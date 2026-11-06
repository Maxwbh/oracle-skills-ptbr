"""apply_changelog.py — estados EM_ANDAMENTO/APLICADA/ERRO e bloqueio (sem banco)."""
from pathlib import Path

import pytest

import apply_changelog as ac
import oracle_devops_utils as u

ASSET_SQL = (Path(__file__).resolve().parents[1] / "skills" / "oracle-devops-ptbr"
             / "assets" / "create-changelog-table.sql")


def test_create_changelog_table_sql_igual_ao_bloco_do_script():
    cmds = [c for c in u.analisar_sql(ASSET_SQL.read_text(encoding="utf-8"))
            if c.tipo == "plsql"]
    assert len(cmds) == 1
    assert cmds[0].texto == ac.DDL_CHANGELOG_TABLE.strip()


def test_bloco_da_tabela_eh_plsql_bem_formado():
    # Parser tem de enxergar um único bloco PL/SQL terminado (com o '/').
    assert u.split_oracle_sql(ac.DDL_CHANGELOG_TABLE + "\n/\n") == [ac.DDL_CHANGELOG_TABLE]


# ─── Ordem dos registros (sem banco) ─────────────────────────────────────────

@pytest.fixture
def projeto(tmp_path):
    db = tmp_path / "db"
    db.mkdir()
    (db / "001.sql").write_text("CREATE TABLE t (id NUMBER);\n")
    (db / "changelog.yml").write_text(
        "migrations:\n  - {id: '001', arquivo: 001.sql, tipo: ddl, descricao: tabela t}\n")
    return tmp_path


@pytest.fixture
def eventos(monkeypatch):
    log: list = []
    monkeypatch.setattr(ac, "marcar_em_andamento", lambda *a, **k: log.append("EM_ANDAMENTO"))
    monkeypatch.setattr(ac, "marcar_aplicada", lambda *a, **k: log.append("APLICADA"))
    monkeypatch.setattr(ac, "marcar_erro", lambda c, i, d, msg, stmt: log.append(("ERRO", msg, stmt)))
    return log


MIG = ac.Migration("001", "001.sql", "ddl", "tabela t")


def test_grava_em_andamento_antes_de_executar_e_aplicada_depois(projeto, eventos, monkeypatch):
    monkeypatch.setattr(ac, "executar_e_verificar", lambda *a, **k: eventos.append("EXEC"))
    r = ac.processar_migration(None, {}, MIG, projeto / "db", "dev", False, None)
    assert r.status == ac.APLICADA
    assert eventos == ["EM_ANDAMENTO", "EXEC", "APLICADA"]


def test_falha_grava_erro_com_mensagem_e_statement(projeto, eventos, monkeypatch):
    def falha(*a, **k):
        eventos.append("EXEC")
        raise u.ErroSQLcl("falhou", statement="CREATE TABLE t (id NUMBER)",
                          erro_oracle="ORA-00955: name is already used")
    monkeypatch.setattr(ac, "executar_e_verificar", falha)
    r = ac.processar_migration(None, {}, MIG, projeto / "db", "dev", False, None)
    assert r.status == ac.ERRO
    assert eventos == ["EM_ANDAMENTO", "EXEC",
                       ("ERRO", "ORA-00955: name is already used", "CREATE TABLE t (id NUMBER)")]


def test_aplicada_com_mesmo_checksum_eh_pulada(projeto, eventos):
    chk = u.checksum_sha256(projeto / "db" / "001.sql")
    reg = ac.Registro("001", ac.APLICADA, chk)
    r = ac.processar_migration(None, {}, MIG, projeto / "db", "dev", False, reg)
    assert r.status == "PULADA" and eventos == []


def test_aplicada_com_checksum_diferente_eh_erro_de_integridade(projeto, eventos):
    reg = ac.Registro("001", ac.APLICADA, "0" * 64)
    r = ac.processar_migration(None, {}, MIG, projeto / "db", "dev", False, reg)
    assert r.status == ac.ERRO and "INTEGRIDADE" in r.erro and eventos == []


class _ConnFalsa:
    def close(self):
        pass


@pytest.mark.parametrize("status", [ac.ERRO, ac.EM_ANDAMENTO])
def test_pendencia_bloqueia_nova_execucao(projeto, monkeypatch, status):
    monkeypatch.setattr(ac, "obter_config_db", lambda: {"schema": "X"})
    monkeypatch.setattr(ac, "conectar", lambda cfg: _ConnFalsa())
    monkeypatch.setattr(ac, "garantir_tabela_changelog", lambda conn: None)
    monkeypatch.setattr(ac, "ler_registros",
                        lambda conn: {"001": ac.Registro("001", status, "x", mensagem_erro="ORA-1")})
    monkeypatch.setattr(ac, "processar_migration",
                        lambda *a, **k: pytest.fail("não pode executar com pendência"))
    assert ac.main(["--env", "dev", "--project-root", str(projeto)]) == 1


def test_retomar_id_sem_pendencia_eh_recusado(projeto, monkeypatch):
    monkeypatch.setattr(ac, "obter_config_db", lambda: {"schema": "X"})
    monkeypatch.setattr(ac, "conectar", lambda cfg: _ConnFalsa())
    monkeypatch.setattr(ac, "garantir_tabela_changelog", lambda conn: None)
    monkeypatch.setattr(ac, "ler_registros", lambda conn: {})
    assert ac.main(["--retomar", "001", "--project-root", str(projeto)]) == 1


def test_mensagem_longa_eh_cortada_para_caber_em_varchar2_4000():
    assert len(ac._cortar("é" * 5000).encode("utf-8")) <= 4000


def test_validar_offline_nao_conecta_e_aponta_problemas(projeto, monkeypatch):
    (projeto / "db" / "002.sql").write_bytes("INSERT INTO t VALUES ('ação');\n".encode("latin-1"))
    with (projeto / "db" / "changelog.yml").open("a") as f:
        f.write("  - {id: '002', arquivo: 002.sql, tipo: dml, descricao: latin1}\n")
        f.write("  - {id: '003', arquivo: nao_existe.sql, tipo: dml, descricao: sumiu}\n")
    monkeypatch.setattr(ac, "conectar", lambda cfg: pytest.fail("não pode conectar"))
    monkeypatch.setattr(ac, "obter_config_db", lambda: pytest.fail("não pode ler DB_*"))
    assert ac.main(["--validar", "--env", "prod", "--project-root", str(projeto)]) == 1


def test_validar_offline_ok(projeto, monkeypatch):
    monkeypatch.setattr(ac, "conectar", lambda cfg: pytest.fail("não pode conectar"))
    assert ac.main(["--validar", "--project-root", str(projeto)]) == 0
