"""Execução de scripts pelo SQLcl e checagem de compilação (unitário, sem banco).

Usa um executável 'sql' falso que grava argv/stdin e devolve o código e a
saída pedidos, para verificar o contrato com o SQLcl sem precisar dele.
"""
import json
import stat
import sys
import textwrap
from datetime import datetime

import pytest

import oracle_devops_utils as u

CFG = {"host": "h", "port": 1521, "service": "svc", "user": "deployer",
       "password": "s3nh@/x", "schema": "deployer"}


@pytest.fixture
def sql_falso(tmp_path, monkeypatch):
    registro = tmp_path / "registro.json"
    exe = tmp_path / "sql"
    exe.write_text(textwrap.dedent(f"""\
        #!{sys.executable}
        import json, os, sys
        dados = {{"argv": sys.argv[1:], "stdin": sys.stdin.read(), "cwd": os.getcwd()}}
        open({str(registro)!r}, "w").write(json.dumps(dados))
        sys.stdout.write(os.environ.get("FAKE_OUT", ""))
        sys.exit(int(os.environ.get("FAKE_RC", "0")))
    """))
    exe.chmod(exe.stat().st_mode | stat.S_IEXEC)
    monkeypatch.setenv("SQLCL_BIN", str(exe))
    return lambda: json.loads(registro.read_text())


@pytest.fixture
def script(tmp_path):
    pasta = tmp_path / "app"
    pasta.mkdir()
    arq = pasta / "install.sql"
    arq.write_text("PROMPT ok\n@@outro.sql\nCREATE TABLE t (id NUMBER);\n")
    return arq


def test_sqlcl_recebe_senha_pela_entrada_e_nao_pela_linha_de_comando(sql_falso, script):
    u.executar_script_sqlcl(script, CFG, verbose=False)
    reg = sql_falso()
    assert reg["argv"] == ["-S", "/nolog"]
    assert "s3nh@/x" not in " ".join(reg["argv"])
    assert 'CONNECT deployer/"s3nh@/x"@//h:1521/svc' in reg["stdin"]


def test_sqlcl_usa_whenever_com_rollback_e_exit_com_commit(sql_falso, script):
    u.executar_script_sqlcl(script, CFG, verbose=False)
    linhas = sql_falso()["stdin"].splitlines()
    assert linhas[0] == "WHENEVER SQLERROR EXIT FAILURE ROLLBACK"
    assert linhas[1] == "WHENEVER OSERROR EXIT FAILURE ROLLBACK"
    assert linhas[-1] == "EXIT SUCCESS COMMIT"
    assert linhas[-2] == f'@"{script.resolve()}"'


def test_sqlcl_liga_sqlblanklines_antes_do_script(sql_falso, script):
    # Linha em branco dentro de um comando não pode encerrá-lo (UPDATE sem WHERE)
    u.executar_script_sqlcl(script, CFG, verbose=False)
    linhas = sql_falso()["stdin"].splitlines()
    assert "SET SQLBLANKLINES ON" in linhas
    assert linhas.index("SET SQLBLANKLINES ON") < linhas.index(f'@"{script.resolve()}"')


def test_sqlcl_roda_na_pasta_do_script_para_preservar_arroba_arroba(sql_falso, script):
    u.executar_script_sqlcl(script, CFG, verbose=False)
    assert sql_falso()["cwd"] == str(script.parent)


def test_sqlcl_aplica_current_schema_quando_db_schema_difere(sql_falso, script):
    u.executar_script_sqlcl(script, {**CFG, "schema": "ms_app"}, verbose=False)
    assert "ALTER SESSION SET CURRENT_SCHEMA = MS_APP;" in sql_falso()["stdin"]


def test_sqlcl_preambulo_vem_antes_do_script(sql_falso, script):
    u.executar_script_sqlcl(script, CFG, preambulo=["PROMPT pre"], verbose=False)
    linhas = sql_falso()["stdin"].splitlines()
    assert linhas.index("PROMPT pre") < linhas.index(f'@"{script.resolve()}"')


SAIDA_ERRO = textwrap.dedent("""\

    Table T created.


    Error starting at line : 4 in command -
    insert into tabela_inexistente values (1)
    Error at Command Line : 4 Column : 13
    Error report -
    SQL Error: ORA-00942: table or view "APP"."TABELA_INEXISTENTE" does not exist
    Help: https://docs.oracle.com/error-help/db/ora-00942/
    Rollback
""")


def test_sqlcl_codigo_de_saida_diferente_de_zero_vira_erro_com_statement(
        sql_falso, script, monkeypatch):
    monkeypatch.setenv("FAKE_RC", "2")
    monkeypatch.setenv("FAKE_OUT", SAIDA_ERRO)
    with pytest.raises(u.ErroSQLcl) as exc:
        u.executar_script_sqlcl(script, CFG, verbose=False)
    assert exc.value.codigo == 2
    assert exc.value.statement == "insert into tabela_inexistente values (1)"
    assert "ORA-00942" in exc.value.erro_oracle
    assert "ORA-00942" in str(exc.value)


def test_extrair_erro_formato_de_arquivo():
    # Rodando a partir de '@arquivo', o SQLcl põe "In command -" em linha própria.
    saida = ("Error starting at line : 2 File @ /x/dml.sql\nIn command -\n"
             "INSERT INTO y VALUES (1)\nError report -\nORA-00942: nao existe\n")
    assert u.extrair_erro_sqlcl(saida) == ("INSERT INTO y VALUES (1)", "ORA-00942: nao existe")


def test_extrair_erro_formato_error_at_line():
    # Formato usado pelo SQLcl em erro de CREATE TRIGGER, por exemplo.
    saida = ("Sequence S created.\n\nRollback\nCREATE OR REPLACE TRIGGER tr_x\n*\n"
             "ERROR at line 1:\nORA-32795: cannot insert into a generated always identity column\n"
             "Help: https://docs.oracle.com/error-help/db/ora-32795/\n\n")
    stmt, erro = u.extrair_erro_sqlcl(saida)
    assert stmt == "CREATE OR REPLACE TRIGGER tr_x"
    assert erro.startswith("ORA-32795")
    assert u.resumo_erro("Rollback\nORA-1: x") == "ORA-1: x"


def test_sqlcl_ausente_falha_com_mensagem_clara(script, monkeypatch):
    monkeypatch.delenv("SQLCL_BIN", raising=False)
    monkeypatch.setattr(u.shutil, "which", lambda _: None)
    with pytest.raises(u.ErroSQLcl, match="SQLcl não encontrado"):
        u.executar_script_sqlcl(script, CFG, verbose=False)


def test_sqlcl_pre_valida_arquivo_antes_de_executar(sql_falso, tmp_path):
    arq = tmp_path / "sem_barra.sql"
    arq.write_text("BEGIN\n  NULL;\nEND;\n")
    with pytest.raises(u.ErroSQLcl, match="terminador"):
        u.executar_script_sqlcl(arq, CFG, verbose=False)


def test_senha_com_aspas_duplas_eh_recusada(script):
    with pytest.raises(u.ErroSQLcl, match="aspas"):
        u.montar_script_sqlcl(script, {**CFG, "password": 'a"b'})


# ─── DB_SCHEMA ───────────────────────────────────────────────────────────────

def _env_db(monkeypatch, **extra):
    for k, v in {"DB_HOST": "h", "DB_PORT": "1521", "DB_SERVICE": "s",
                 "DB_USER": "admin_dba", "DB_PASS": "x", **extra}.items():
        monkeypatch.setenv(k, v)


def test_obter_config_db_le_db_schema(monkeypatch):
    _env_db(monkeypatch, DB_SCHEMA="ms_app")
    assert u.obter_config_db()["schema"] == "ms_app"


def test_obter_config_db_schema_padrao_eh_o_usuario(monkeypatch):
    _env_db(monkeypatch)
    monkeypatch.delenv("DB_SCHEMA", raising=False)
    assert u.obter_config_db()["schema"] == "admin_dba"


def test_obter_config_db_recusa_schema_com_injecao(monkeypatch):
    _env_db(monkeypatch, DB_SCHEMA="x; DROP USER y")
    with pytest.raises(SystemExit):
        u.obter_config_db()


# ─── Erros de compilação ─────────────────────────────────────────────────────

class _Cursor:
    def __init__(self, linhas):
        self.linhas, self.sql, self.binds = linhas, None, None

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def execute(self, sql, **binds):
        self.sql, self.binds = sql, binds

    def fetchall(self):
        return self.linhas


class _Conn:
    def __init__(self, linhas):
        self.cur = _Cursor(linhas)

    def cursor(self):
        return self.cur


def test_verificar_erros_compilacao_consulta_all_errors_do_schema_corrente():
    conn = _Conn([("PRC_X", "PROCEDURE", 3, 3, "PLS-00201: identifier 'X' must be declared")])
    desde = datetime(2026, 11, 6, 12, 0)
    erros = u.verificar_erros_compilacao(conn, desde)
    assert erros and erros[0][0] == "PRC_X"
    assert "all_errors" in conn.cur.sql.lower()
    assert "SYS_CONTEXT('USERENV', 'CURRENT_SCHEMA')" in conn.cur.sql
    assert conn.cur.binds == {"desde": desde}


def test_executar_e_verificar_falha_quando_ha_erro_de_compilacao(
        sql_falso, script, monkeypatch):
    conn = _Conn([("PRC_X", "PROCEDURE", 3, 3, "PLS-00201: identifier 'X' must be declared")])
    monkeypatch.setattr(u, "data_hora_banco", lambda c: datetime(2026, 11, 6))
    with pytest.raises(u.ErroSQLcl, match="erro\\(s\\) de compilação"):
        u.executar_e_verificar(conn, script, CFG, verbose=False)
