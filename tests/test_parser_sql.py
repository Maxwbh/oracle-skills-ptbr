"""Testes do parser de scripts Oracle (split_oracle_sql / analisar_sql).

Cobrem os defeitos apontados na revisão 2026-11:
- terminador '/' removia o ';' final de blocos PL/SQL (END; virava END);
- comentário /* */ era removido também dentro de literal (dado corrompido);
- comandos de cliente (SET, PROMPT, WHENEVER, @, @@) grudavam no SQL seguinte.
"""
import textwrap

import pytest

import oracle_devops_utils as u


def split(sql: str, **kw) -> list[str]:
    return u.split_oracle_sql(textwrap.dedent(sql), **kw)


# ─── PL/SQL: o ';' final faz parte do código ─────────────────────────────────

def test_package_spec_e_body_preservam_end_com_ponto_e_virgula():
    stmts = split("""
        CREATE OR REPLACE PACKAGE pkg_cliente AS
          PROCEDURE p_gravar(p_id IN NUMBER);
        END pkg_cliente;
        /
        CREATE OR REPLACE PACKAGE BODY pkg_cliente AS
          PROCEDURE p_gravar(p_id IN NUMBER) IS
          BEGIN
            NULL;
          END p_gravar;
        END pkg_cliente;
        /
    """)
    assert len(stmts) == 2
    assert stmts[0].startswith("CREATE OR REPLACE PACKAGE pkg_cliente")
    assert stmts[0].endswith("END pkg_cliente;")
    assert stmts[1].startswith("CREATE OR REPLACE PACKAGE BODY")
    assert stmts[1].endswith("END pkg_cliente;")


def test_procedure_preserva_end():
    stmts = split("""
        CREATE OR REPLACE PROCEDURE prc_teste IS
          l_total NUMBER := 10 / 2;
        BEGIN
          NULL;
        END;
        /
    """)
    assert len(stmts) == 1
    assert stmts[0].endswith("END;")
    assert "10 / 2" in stmts[0]


def test_trigger_preserva_end():
    stmts = split("""
        CREATE OR REPLACE EDITIONABLE TRIGGER trg_cliente_bi
          BEFORE INSERT ON cliente
          FOR EACH ROW
        BEGIN
          :new.dt_criacao := SYSDATE;
        END trg_cliente_bi;
        /
    """)
    assert stmts == [stmts[0]]
    assert stmts[0].endswith("END trg_cliente_bi;")


def test_bloco_anonimo_preserva_end():
    stmts = split("""
        DECLARE
          l_n NUMBER;
        BEGIN
          SELECT COUNT(*) INTO l_n FROM dual;
        END;
        /
    """)
    assert len(stmts) == 1
    assert stmts[0].startswith("DECLARE")
    assert stmts[0].endswith("END;")


def test_create_type_eh_plsql():
    stmts = split("""
        CREATE OR REPLACE TYPE t_item AS OBJECT (
          id   NUMBER,
          nome VARCHAR2(100)
        );
        /
    """)
    assert len(stmts) == 1
    assert stmts[0].endswith(");")


# ─── Literais e comentários ──────────────────────────────────────────────────

def test_literal_com_ponto_e_virgula():
    assert split("INSERT INTO t (c) VALUES ('a;b');\n") == [
        "INSERT INTO t (c) VALUES ('a;b')"
    ]


def test_literal_com_barra_em_linha_propria():
    stmts = split("INSERT INTO t (c) VALUES ('linha1\n/\nlinha3');\n")
    assert stmts == ["INSERT INTO t (c) VALUES ('linha1\n/\nlinha3')"]


def test_comentario_de_bloco_dentro_de_literal_nao_eh_removido():
    stmts = split("INSERT INTO t (c) VALUES ('/* x */');\n")
    assert stmts == ["INSERT INTO t (c) VALUES ('/* x */')"]


def test_traco_traco_dentro_de_literal_nao_eh_comentario():
    stmts = split("UPDATE t SET c = 'a -- b' WHERE id = 1;\n")
    assert stmts == ["UPDATE t SET c = 'a -- b' WHERE id = 1"]


def test_aspas_escapadas_no_literal():
    stmts = split("INSERT INTO t (c) VALUES ('it''s; ok');\n")
    assert stmts == ["INSERT INTO t (c) VALUES ('it''s; ok')"]


def test_q_quote():
    stmts = split("SELECT q'[it's; /* não é comentário */ -- nem isto]' FROM dual;\n")
    assert stmts == ["SELECT q'[it's; /* não é comentário */ -- nem isto]' FROM dual"]


def test_q_quote_outros_delimitadores_e_nq():
    stmts = split("SELECT q'{a;b}', nq'!c;d!', Q'<e;f>' FROM dual;\n")
    assert stmts == ["SELECT q'{a;b}', nq'!c;d!', Q'<e;f>' FROM dual"]


def test_comentario_com_aspas_nao_abre_literal():
    stmts = split("""
        -- comentário com aspa ' solta
        SELECT 1 FROM dual; /* outro ' */
        SELECT 2 FROM dual;
    """)
    assert stmts == ["SELECT 1 FROM dual", "SELECT 2 FROM dual"]


def test_comentario_dentro_do_plsql_eh_preservado():
    stmts = split("""
        CREATE OR REPLACE PROCEDURE prc_x IS
        BEGIN
          /* regra de negócio: não remover */
          NULL; -- comentário de linha
        END;
        /
    """)
    assert "/* regra de negócio: não remover */" in stmts[0]
    assert "-- comentário de linha" in stmts[0]


def test_dois_statements_na_mesma_linha():
    assert split("SELECT 1 FROM dual; SELECT 2 FROM dual;\n") == [
        "SELECT 1 FROM dual",
        "SELECT 2 FROM dual",
    ]


def test_sql_terminado_por_barra():
    assert split("CREATE TABLE t (id NUMBER)\n/\n") == ["CREATE TABLE t (id NUMBER)"]


def test_literal_nao_fechado_eh_erro():
    with pytest.raises(u.ErroParserSQL):
        split("INSERT INTO t VALUES ('aberto);\n")


def test_comentario_nao_fechado_eh_erro():
    with pytest.raises(u.ErroParserSQL):
        split("SELECT 1 FROM dual; /* sem fim\n")


# ─── Comandos de cliente (SQL*Plus / SQLcl) ──────────────────────────────────

SCRIPT_COM_CLIENTE = """
    SET DEFINE OFF
    PROMPT criando tabela
    WHENEVER SQLERROR EXIT FAILURE
    @@outro_script.sql
    @ ../comum/grants.sql
    CREATE TABLE t (id NUMBER);
"""


def test_comando_de_cliente_eh_rejeitado_explicitamente():
    with pytest.raises(u.ErroParserSQL, match="cliente"):
        split(SCRIPT_COM_CLIENTE)


def test_comando_de_cliente_nao_gruda_no_sql_seguinte():
    stmts = split(SCRIPT_COM_CLIENTE, permitir_cliente=True)
    assert stmts == ["CREATE TABLE t (id NUMBER)"]


def test_analisar_classifica_comandos():
    cmds = u.analisar_sql(textwrap.dedent(SCRIPT_COM_CLIENTE))
    assert [c.tipo for c in cmds] == ["cliente"] * 5 + ["sql"]
    assert cmds[3].texto == "@@outro_script.sql"
    assert cmds[-1].linha == 7


def test_set_transaction_eh_sql_e_nao_cliente():
    assert split("SET TRANSACTION READ ONLY;\n") == ["SET TRANSACTION READ ONLY"]


# ─── Arquivo sem terminador ──────────────────────────────────────────────────

def test_sql_sem_terminador_eh_erro():
    # O SQLcl/SQL*Plus não executa o buffer final sem ';' ou '/':
    # o statement seria ignorado em silêncio.
    with pytest.raises(u.ErroParserSQL, match="terminador"):
        split("CREATE TABLE t (id NUMBER)")


def test_plsql_sem_barra_final_eh_erro():
    with pytest.raises(u.ErroParserSQL, match="terminador"):
        split("BEGIN\n  NULL;\nEND;\n")


def test_validar_arquivo_aponta_problemas(tmp_path):
    arq = tmp_path / "001_x.sql"
    arq.write_text("SET DEFINE OFF\nBEGIN\n  NULL;\nEND;\n", encoding="utf-8")
    problemas = u.validar_arquivo_sql(arq)
    assert len(problemas) == 1
    assert "terminador" in problemas[0]


def test_validar_arquivo_ok(tmp_path):
    arq = tmp_path / "001_x.sql"
    arq.write_text("SET DEFINE OFF\nBEGIN\n  NULL;\nEND;\n/\n", encoding="utf-8")
    assert u.validar_arquivo_sql(arq) == []


def test_crlf():
    assert split("SELECT 1 FROM dual;\r\nSELECT 2 FROM dual;\r\n") == [
        "SELECT 1 FROM dual",
        "SELECT 2 FROM dual",
    ]
