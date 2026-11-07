"""Integração: migration que falha no meio → ERRO, bloqueio e retomada."""
import textwrap

import apply_changelog as ac


def _projeto(tmp_path, migrations: dict[str, str]):
    db = tmp_path / "db"
    db.mkdir(exist_ok=True)
    linhas = ["migrations:"]
    for mid, sql in migrations.items():
        (db / f"{mid}.sql").write_text(textwrap.dedent(sql), encoding="utf-8")
        linhas.append(f"  - {{id: '{mid}', arquivo: {mid}.sql, tipo: ddl, descricao: m{mid}}}")
    (db / "changelog.yml").write_text("\n".join(linhas) + "\n", encoding="utf-8")
    return tmp_path


def _rodar(raiz, *args):
    return ac.main(["--env", "dev", "--project-root", str(raiz), *args])


def _estado(conn):
    with conn.cursor() as cur:
        cur.execute("SELECT id, status, mensagem_erro, statement_erro FROM db_changelog ORDER BY id")
        return {r[0]: r[1:] for r in cur.fetchall()}


def _existe(conn, tabela):
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM user_tables WHERE table_name = :t", t=tabela)
        return cur.fetchone()[0] == 1


MIGRATION_QUE_FALHA = """\
    CREATE TABLE t_parcial (id NUMBER);
    ALTER TABLE tabela_inexistente ADD (x NUMBER);
"""


def test_falha_no_meio_registra_erro_bloqueia_e_retoma(tmp_path, conn_teste):
    raiz = _projeto(tmp_path, {
        "001": "CREATE TABLE t_um (id NUMBER);\n",
        "002": MIGRATION_QUE_FALHA,
        "003": "CREATE TABLE t_tres (id NUMBER);\n",
    })

    assert _rodar(raiz) == 1
    estado = _estado(conn_teste)
    assert estado["001"][0] == "APLICADA"
    status, mensagem, statement = estado["002"]
    assert status == "ERRO"
    assert "ORA-00942" in mensagem
    assert statement.upper().startswith("ALTER TABLE TABELA_INEXISTENTE")
    assert "003" not in estado
    # DDL anterior ao erro NÃO é desfeito: é por isso que existe o status.
    assert _existe(conn_teste, "T_PARCIAL")

    # Nova execução sem decisão: bloqueada, nada muda.
    assert _rodar(raiz) == 1
    assert "003" not in _estado(conn_teste)

    # Corrige a migration tornando-a idempotente e retoma.
    (raiz / "db" / "002.sql").write_text(textwrap.dedent("""\
        BEGIN
          EXECUTE IMMEDIATE 'CREATE TABLE t_parcial (id NUMBER)';
        EXCEPTION
          WHEN OTHERS THEN
            IF SQLCODE != -955 THEN  -- ORA-00955: nome já usado
              RAISE;
            END IF;
        END;
        /
    """), encoding="utf-8")
    assert _rodar(raiz, "--retomar", "002") == 0
    estado = _estado(conn_teste)
    assert estado["002"] == ("APLICADA", None, None)
    assert estado["003"][0] == "APLICADA"


def test_marcar_resolvida(tmp_path, conn_teste):
    raiz = _projeto(tmp_path, {"001": MIGRATION_QUE_FALHA})
    assert _rodar(raiz) == 1
    assert _rodar(raiz, "--marcar-resolvida", "001") == 0
    status, mensagem, _ = _estado(conn_teste)["001"]
    assert status == "APLICADA"
    assert mensagem.startswith("[resolvida manualmente por")
    assert _rodar(raiz) == 0  # desbloqueado; nada pendente


def test_erro_de_compilacao_vira_status_erro(tmp_path, conn_teste):
    raiz = _projeto(tmp_path, {"001": """\
        CREATE OR REPLACE PROCEDURE prc_quebrada IS
        BEGIN
          x := 1;
        END;
        /
    """})
    assert _rodar(raiz) == 1
    status, mensagem, statement = _estado(conn_teste)["001"]
    assert status == "ERRO"
    assert "PLS-00201" in mensagem
    assert statement == "PROCEDURE PRC_QUEBRADA"


def test_tabela_da_versao_anterior_eh_atualizada_sem_perder_historico(conn_teste):
    with conn_teste.cursor() as cur:
        cur.execute("""
            CREATE TABLE db_changelog (
              id VARCHAR2(20) NOT NULL, descricao VARCHAR2(500) NOT NULL,
              arquivo VARCHAR2(500) NOT NULL, tipo VARCHAR2(10) NOT NULL,
              checksum VARCHAR2(64) NOT NULL,
              aplicado_em DATE DEFAULT SYSDATE NOT NULL,
              aplicado_por VARCHAR2(100) DEFAULT USER NOT NULL,
              duracao_ms NUMBER, ambiente VARCHAR2(10),
              CONSTRAINT pk_db_changelog PRIMARY KEY (id))""")
        cur.execute("INSERT INTO db_changelog (id, descricao, arquivo, tipo, checksum) "
                    "VALUES ('001', 'antiga', '001.sql', 'ddl', 'abc')")
    conn_teste.commit()
    ac.garantir_tabela_changelog(conn_teste)
    ac.garantir_tabela_changelog(conn_teste)  # idempotente
    assert _estado(conn_teste)["001"] == ("APLICADA", None, None)
    with conn_teste.cursor() as cur:
        cur.execute("SELECT data_default FROM user_tab_columns "
                    "WHERE table_name = 'DB_CHANGELOG' AND column_name = 'STATUS'")
        default = cur.fetchone()[0]
        assert default is None or default.strip().upper() == "NULL"
