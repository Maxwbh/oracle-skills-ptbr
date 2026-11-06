"""Integração: templates do oracle-plsql-ptbr compilam e seguem as regras.

Regra 4 (transação): rotina reutilizável não comita nem faz ROLLBACK total,
desfaz só a própria unidade (SAVEPOINT) e propaga o erro original; só o
ponto de entrada é dono da transação.
Regra 10 (triggers): trigger simples para auditoria de colunas; compound
quando há estado entre linha e statement.
"""
from pathlib import Path

import oracledb
import pytest

import oracle_devops_utils as u

ASSETS = Path(__file__).resolve().parents[2] / "skills" / "oracle-plsql-ptbr" / "assets"


def _instalar(tmp_path, conn, nome, sql):
    arq = tmp_path / nome
    arq.write_text(sql, encoding="utf-8")
    u.executar_e_verificar(conn, arq, u.obter_config_db(), verbose=False)


def _template(nome):
    return ((ASSETS / nome).read_text(encoding="utf-8")
            .replace("<nome_pacote>", "teste").replace("<NOME_PACOTE>", "TESTE"))


@pytest.fixture
def pacote(tmp_path, conn_teste):
    with conn_teste.cursor() as cur:
        cur.execute("""CREATE TABLE registros (
                         id NUMBER PRIMARY KEY, status VARCHAR2(1), valor NUMBER,
                         processado_em DATE, processado_por VARCHAR2(128))""")
        cur.execute("""CREATE TABLE log_eventos (
                         criado_em TIMESTAMP, nome_pacote VARCHAR2(30), mensagem VARCHAR2(4000))""")
        cur.execute("CREATE TABLE marcador (id NUMBER)")
        cur.executemany("INSERT INTO registros (id, status, valor) VALUES (:1, :2, 10)",
                        [(1, "P"), (2, "C"), (3, "X"), (4, "A")])
    conn_teste.commit()
    _instalar(tmp_path, conn_teste, "spec.pks", _template("package_header.sql"))
    _instalar(tmp_path, conn_teste, "body.pkb", _template("package_body.sql"))
    return conn_teste


def _status(conn, id_):
    with conn.cursor() as cur:
        cur.execute("SELECT status FROM registros WHERE id = :1", [id_])
        return cur.fetchone()[0]


def _marcadores(conn):
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM marcador")
        return cur.fetchone()[0]


def test_rotina_reutilizavel_nao_comita(pacote):
    with pacote.cursor() as cur:
        cur.callproc("teste_pkg.processar_registro", [1])
    pacote.rollback()                       # o chamador desiste
    assert _status(pacote, 1) == "P"        # nada foi gravado pela rotina


def test_erro_na_rotina_nao_desfaz_trabalho_do_chamador(pacote):
    with pacote.cursor() as cur:
        cur.execute("INSERT INTO marcador VALUES (1)")   # trabalho do chamador
        with pytest.raises(oracledb.DatabaseError):
            cur.callproc("teste_pkg.processar_registro", [3])   # estado inválido
    assert _marcadores(pacote) == 1         # a rotina não fez ROLLBACK total


def test_erro_original_eh_preservado(pacote):
    with pacote.cursor() as cur:
        cur.execute("""CREATE OR REPLACE TRIGGER trg_teste_falha
                         BEFORE UPDATE ON registros FOR EACH ROW
                       BEGIN
                         raise_application_error(-20777, 'falha simulada');
                       END;""")
        with pytest.raises(oracledb.DatabaseError) as exc:
            cur.callproc("teste_pkg.processar_registro", [1])
    assert exc.value.args[0].code == 20777  # não virou -20999


def test_estado_invalido_levanta_e_estado_invalido(pacote):
    with pacote.cursor() as cur, pytest.raises(oracledb.DatabaseError) as exc:
        cur.callproc("teste_pkg.processar_registro", [3])
    assert exc.value.args[0].code == 20100


def test_ja_processado_sem_forcar_nao_falha(pacote):
    with pacote.cursor() as cur:
        cur.callproc("teste_pkg.processar_registro", [2])   # status C
    assert _status(pacote, 2) == "C"


def test_ponto_de_entrada_eh_dono_da_transacao(pacote, schema_teste):
    with pacote.cursor() as cur:
        cur.callproc("teste_pkg.processar_pendentes")
    # Outra sessão enxerga o resultado: o ponto de entrada comitou.
    outra = oracledb.connect(user=schema_teste["user"], password=schema_teste["password"],
                             dsn=schema_teste["dsn"])
    try:
        assert [_status(outra, i) for i in (1, 2, 3, 4)] == ["C", "C", "X", "C"]
    finally:
        outra.close()


# ─── Triggers (regra 10) ─────────────────────────────────────────────────────

@pytest.fixture
def triggers(tmp_path, conn_teste):
    with conn_teste.cursor() as cur:
        cur.execute("""CREATE TABLE faturas (
                         id_fatura NUMBER PRIMARY KEY, valor NUMBER,
                         criado_em TIMESTAMP, criado_por VARCHAR2(128),
                         atualizado_em TIMESTAMP, atualizado_por VARCHAR2(128))""")
    # Executa o template até a seção de EBR (cross-edition exige editions).
    texto = (ASSETS / "triggers_canonicos.sql").read_text(encoding="utf-8")
    corte = texto.index("EBR — cross-edition trigger")
    corte = texto.rindex("--====", 0, corte)
    texto = texto[:texto.rindex("\n", 0, corte)] + "\n"
    _instalar(tmp_path, conn_teste, "triggers.sql", texto)
    return conn_teste


def test_triggers_do_template_compilam_sem_erro(triggers):
    with triggers.cursor() as cur:
        cur.execute("SELECT object_name FROM user_objects WHERE status <> 'VALID'")
        assert cur.fetchall() == []


def test_auditoria_de_colunas_e_em_lote(triggers):
    with triggers.cursor() as cur:
        cur.execute("""INSERT INTO faturas (id_fatura, valor)
                       SELECT LEVEL, LEVEL * 10 FROM dual CONNECT BY LEVEL <= 3""")
        cur.execute("SELECT COUNT(*) FROM faturas WHERE criado_em IS NOT NULL "
                    "AND criado_por IS NOT NULL AND atualizado_em = criado_em")
        assert cur.fetchone()[0] == 3
        cur.execute("UPDATE faturas SET valor = valor + 1")
        cur.execute("SELECT operacao, COUNT(*) FROM auditoria_alteracao "
                    "WHERE tabela = 'FATURAS' GROUP BY operacao ORDER BY 1")
        assert cur.fetchall() == [("INSERT", 3), ("UPDATE", 3)]


def test_surrogate_key_legada(triggers):
    with triggers.cursor() as cur:
        cur.execute("INSERT INTO pagamentos_legado (id_fatura, valor) VALUES (1, 5)")
        cur.execute("SELECT id_pagamento FROM pagamentos_legado")
        assert cur.fetchone()[0] is not None


# ─── logger_integration.sql (rotina reutilizável com Logger) ─────────────────
# Stub mínimo do Logger (OraOpenSource): só as assinaturas usadas no template.
LOGGER_STUB = """
CREATE OR REPLACE PACKAGE logger AS
  TYPE rec_param IS RECORD (name VARCHAR2(255), val VARCHAR2(4000));
  TYPE tab_param IS TABLE OF rec_param INDEX BY BINARY_INTEGER;
  PROCEDURE log(p_text IN VARCHAR2, p_scope IN VARCHAR2 DEFAULT NULL,
                p_extra IN CLOB DEFAULT NULL, p_params IN tab_param DEFAULT CAST(NULL AS tab_param));
  PROCEDURE log_information(p_text IN VARCHAR2, p_scope IN VARCHAR2 DEFAULT NULL,
                p_extra IN CLOB DEFAULT NULL, p_params IN tab_param DEFAULT CAST(NULL AS tab_param));
  PROCEDURE log_warn(p_text IN VARCHAR2, p_scope IN VARCHAR2 DEFAULT NULL,
                p_extra IN CLOB DEFAULT NULL, p_params IN tab_param DEFAULT CAST(NULL AS tab_param));
  PROCEDURE log_error(p_text IN VARCHAR2, p_scope IN VARCHAR2 DEFAULT NULL,
                p_extra IN CLOB DEFAULT NULL, p_params IN tab_param DEFAULT CAST(NULL AS tab_param));
  PROCEDURE append_param(p_params IN OUT NOCOPY tab_param, p_name IN VARCHAR2, p_val IN VARCHAR2);
END logger;
/
CREATE OR REPLACE PACKAGE BODY logger AS
  PROCEDURE log(p_text IN VARCHAR2, p_scope IN VARCHAR2 DEFAULT NULL,
                p_extra IN CLOB DEFAULT NULL, p_params IN tab_param DEFAULT CAST(NULL AS tab_param)) IS
  BEGIN NULL; END;
  PROCEDURE log_information(p_text IN VARCHAR2, p_scope IN VARCHAR2 DEFAULT NULL,
                p_extra IN CLOB DEFAULT NULL, p_params IN tab_param DEFAULT CAST(NULL AS tab_param)) IS
  BEGIN NULL; END;
  PROCEDURE log_warn(p_text IN VARCHAR2, p_scope IN VARCHAR2 DEFAULT NULL,
                p_extra IN CLOB DEFAULT NULL, p_params IN tab_param DEFAULT CAST(NULL AS tab_param)) IS
  BEGIN NULL; END;
  PROCEDURE log_error(p_text IN VARCHAR2, p_scope IN VARCHAR2 DEFAULT NULL,
                p_extra IN CLOB DEFAULT NULL, p_params IN tab_param DEFAULT CAST(NULL AS tab_param)) IS
  BEGIN NULL; END;
  PROCEDURE append_param(p_params IN OUT NOCOPY tab_param, p_name IN VARCHAR2, p_val IN VARCHAR2) IS
  BEGIN NULL; END;
END logger;
/
CREATE OR REPLACE PACKAGE pagamento_pkg AS
  PROCEDURE processar_pagamento(p_id_fatura IN NUMBER, p_valor IN NUMBER);
END pagamento_pkg;
/
"""


@pytest.fixture
def pagamento(tmp_path, conn_teste):
    with conn_teste.cursor() as cur:
        cur.execute("CREATE TABLE faturas (id NUMBER PRIMARY KEY, status VARCHAR2(10), "
                    "pago_em DATE, valor_pago NUMBER)")
        cur.execute("CREATE TABLE marcador (id NUMBER)")
        cur.executemany("INSERT INTO faturas (id, status) VALUES (:1, :2)",
                        [(1, "ABERTA"), (2, "PAGO")])
    conn_teste.commit()
    texto = (ASSETS / "logger_integration.sql").read_text(encoding="utf-8")
    corpo = next(c.texto for c in u.analisar_sql(texto)
                 if c.texto.upper().startswith("CREATE OR REPLACE PACKAGE BODY PAGAMENTO_PKG"))
    _instalar(tmp_path, conn_teste, "logger_pagamento.sql", LOGGER_STUB + corpo + "\n/\n")
    return conn_teste


def test_logger_integration_rotina_nao_comita(pagamento):
    with pagamento.cursor() as cur:
        cur.callproc("pagamento_pkg.processar_pagamento", [1, 100])
        pagamento.rollback()
        cur.execute("SELECT status FROM faturas WHERE id = 1")
        assert cur.fetchone()[0] == "ABERTA"


def test_logger_integration_preserva_erro_e_trabalho_do_chamador(pagamento):
    with pagamento.cursor() as cur:
        cur.execute("INSERT INTO marcador VALUES (1)")
        with pytest.raises(oracledb.DatabaseError) as exc:
            cur.callproc("pagamento_pkg.processar_pagamento", [2, 100])   # já paga
        assert exc.value.args[0].code == 20100      # não virou -20999
        cur.execute("SELECT COUNT(*) FROM marcador")
        assert cur.fetchone()[0] == 1               # sem ROLLBACK total
