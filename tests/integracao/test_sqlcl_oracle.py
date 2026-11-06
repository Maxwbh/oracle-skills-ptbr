"""Integração: comportamento real do SQLcl e do python-oracledb.

Comprova as premissas do executor (ver oracle_devops_utils):
- erro de compilação não dispara WHENEVER SQLERROR → precisa de ALL_ERRORS;
- WHENEVER ... EXIT FAILURE ROLLBACK desfaz o DML parcial;
- python-oracledb não lança exceção em compilação com erro (cursor.warning).
"""
import textwrap

import pytest

import oracle_devops_utils as u


def _arq(tmp_path, nome, conteudo):
    arq = tmp_path / nome
    arq.write_text(textwrap.dedent(conteudo), encoding="utf-8")
    return arq


def test_package_com_set_prompt_e_arroba_arroba_compila_valido(tmp_path, conn_teste):
    _arq(tmp_path, "spec.pks", """\
        CREATE OR REPLACE PACKAGE pkg_teste AS
          FUNCTION f_texto RETURN VARCHAR2;
        END pkg_teste;
        /
    """)
    principal = _arq(tmp_path, "install.sql", """\
        SET DEFINE OFF
        PROMPT instalando pkg_teste
        @@spec.pks
        CREATE OR REPLACE PACKAGE BODY pkg_teste AS
          FUNCTION f_texto RETURN VARCHAR2 IS
          BEGIN
            RETURN '/* não é comentário */; &nem_substituicao';
          END f_texto;
        END pkg_teste;
        /
    """)
    u.executar_e_verificar(conn_teste, principal, u.obter_config_db(), verbose=False)
    with conn_teste.cursor() as cur:
        cur.execute("SELECT pkg_teste.f_texto FROM dual")
        assert cur.fetchone()[0] == "/* não é comentário */; &nem_substituicao"
        cur.execute("SELECT status FROM user_objects WHERE object_name = 'PKG_TESTE'")
        assert {r[0] for r in cur.fetchall()} == {"VALID"}


def test_erro_de_compilacao_sai_com_zero_no_sqlcl_e_eh_pego_em_all_errors(tmp_path, conn_teste):
    arq = _arq(tmp_path, "quebrada.sql", """\
        CREATE OR REPLACE PROCEDURE prc_quebrada IS
        BEGIN
          x := 1;
        END;
        /
    """)
    cfg = u.obter_config_db()
    u.executar_script_sqlcl(arq, cfg, verbose=False)        # não lança: SQLcl sai com 0
    with pytest.raises(u.ErroSQLcl, match="PLS-00201"):
        u.executar_e_verificar(conn_teste, arq, cfg, verbose=False)


def test_falha_no_meio_desfaz_dml_parcial(tmp_path, conn_teste):
    with conn_teste.cursor() as cur:
        cur.execute("CREATE TABLE t_dado (id NUMBER PRIMARY KEY)")
    arq = _arq(tmp_path, "dml.sql", """\
        INSERT INTO t_dado VALUES (1);
        INSERT INTO tabela_inexistente VALUES (1);
    """)
    with pytest.raises(u.ErroSQLcl) as exc:
        u.executar_script_sqlcl(arq, u.obter_config_db(), verbose=False)
    assert "ORA-00942" in exc.value.erro_oracle
    assert exc.value.statement.lower().startswith("insert into tabela_inexistente")
    with conn_teste.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM t_dado")
        assert cur.fetchone()[0] == 0


def test_senha_errada_falha(tmp_path, schema_teste):
    arq = _arq(tmp_path, "x.sql", "SELECT 1 FROM dual;\n")
    cfg = {**u.obter_config_db(), "password": "errada"}
    with pytest.raises(u.ErroSQLcl):
        u.executar_script_sqlcl(arq, cfg, verbose=False)


def test_python_oracledb_nao_lanca_excecao_em_compilacao_com_erro(conn_teste):
    with conn_teste.cursor() as cur:
        cur.execute("CREATE OR REPLACE PROCEDURE prc_q2 IS BEGIN y := 1; END;")
        assert cur.warning is not None
        assert cur.warning.full_code == "DPY-7000"
