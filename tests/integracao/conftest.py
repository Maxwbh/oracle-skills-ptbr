"""Fixtures de integração: SÓ em banco descartável (container Oracle Free).

Variáveis:
    ORACLE_TESTE_DSN         ex.: localhost:1521/FREEPDB1
    ORACLE_TESTE_ADMIN_USER  ex.: system
    ORACLE_TESTE_ADMIN_PASS  senha definida no 'docker run -e ORACLE_PWD=...'

Cada sessão de testes cria um usuário temporário e o remove no final.
Nunca aponte estas variáveis para um banco real.
"""
import os
import secrets
import shutil

import oracledb
import pytest

DSN = os.environ.get("ORACLE_TESTE_DSN")


def pytest_collection_modifyitems(config, items):
    motivo = None
    if not DSN:
        motivo = "ORACLE_TESTE_DSN não definido (sem container de teste)"
    elif not (os.environ.get("SQLCL_BIN") or shutil.which("sql")):
        motivo = "SQLcl ('sql') não encontrado"
    for item in items:
        if "integracao" in str(item.fspath):
            item.add_marker(pytest.mark.integracao)
            if motivo:
                item.add_marker(pytest.mark.skip(reason=motivo))


@pytest.fixture(scope="session")
def admin():
    conn = oracledb.connect(user=os.environ["ORACLE_TESTE_ADMIN_USER"],
                            password=os.environ["ORACLE_TESTE_ADMIN_PASS"], dsn=DSN)
    yield conn
    conn.close()


@pytest.fixture
def schema_teste(admin, monkeypatch):
    """Usuário descartável com privilégios de deploy; exporta DB_* para os scripts."""
    nome = f"T_DEVOPS_{secrets.token_hex(3).upper()}"
    senha = f"Tst_{secrets.token_hex(6)}"
    with admin.cursor() as cur:
        cur.execute(f'CREATE USER {nome} IDENTIFIED BY "{senha}" QUOTA UNLIMITED ON SYSTEM')
        cur.execute(f"GRANT CREATE SESSION, CREATE TABLE, CREATE PROCEDURE, CREATE TRIGGER, "
                    f"CREATE SEQUENCE, CREATE TYPE, CREATE VIEW TO {nome}")
    host_porta, servico = DSN.split("/", 1)
    host, _, porta = host_porta.partition(":")
    env = {"DB_HOST": host, "DB_PORT": porta or "1521", "DB_SERVICE": servico,
           "DB_USER": nome, "DB_PASS": senha}
    for k, v in env.items():
        monkeypatch.setenv(k, v)
    monkeypatch.delenv("DB_SCHEMA", raising=False)
    yield {"user": nome, "password": senha, "dsn": DSN, "env": env}
    with admin.cursor() as cur:
        cur.execute(f"DROP USER {nome} CASCADE")


@pytest.fixture
def conn_teste(schema_teste):
    conn = oracledb.connect(user=schema_teste["user"], password=schema_teste["password"],
                            dsn=schema_teste["dsn"])
    yield conn
    conn.close()
