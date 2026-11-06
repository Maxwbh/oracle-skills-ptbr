"""Integração: deploy_db.py ponta a ponta pelo SQLcl no container."""
import subprocess
import sys
import textwrap
from pathlib import Path

ASSETS = Path(__file__).resolve().parents[2] / "skills" / "oracle-devops-ptbr" / "assets"
SHARED = Path(__file__).resolve().parents[2] / "shared" / "assets"


def _projeto(tmp_path, arquivos: dict[str, str]) -> Path:
    for rel, conteudo in arquivos.items():
        arq = tmp_path / "db" / rel
        arq.parent.mkdir(parents=True, exist_ok=True)
        arq.write_text(textwrap.dedent(conteudo), encoding="utf-8")
    return tmp_path


def _rodar(raiz: Path, *args) -> subprocess.CompletedProcess:
    import os
    env = {**os.environ, "PYTHONPATH": f"{SHARED}{os.pathsep}{ASSETS}"}
    return subprocess.run([sys.executable, str(ASSETS / "deploy_db.py"), "--env", "dev",
                           "--project-root", str(raiz), *args],
                          capture_output=True, text=True, env=env, check=False)


SPEC = """\
    CREATE OR REPLACE PACKAGE pkg_cliente AS
      FUNCTION f_total RETURN NUMBER;
    END pkg_cliente;
    /
"""


def test_deploy_db_aplica_tabela_e_package_validos(tmp_path, conn_teste):
    raiz = _projeto(tmp_path, {
        "tables/cliente.sql": "CREATE TABLE cliente (id NUMBER PRIMARY KEY);\n",
        "packages/pkg_cliente.pks": SPEC,
        "packages/pkg_cliente.pkb": """\
            CREATE OR REPLACE PACKAGE BODY pkg_cliente AS
              FUNCTION f_total RETURN NUMBER IS
                l_n NUMBER;
              BEGIN
                SELECT COUNT(*) INTO l_n FROM cliente;
                RETURN l_n;
              END f_total;
            END pkg_cliente;
            /
        """,
    })
    r = _rodar(raiz)
    assert r.returncode == 0, r.stdout + r.stderr
    with conn_teste.cursor() as cur:
        cur.execute("SELECT object_type, status FROM user_objects "
                    "WHERE object_name IN ('CLIENTE', 'PKG_CLIENTE') ORDER BY 1")
        assert cur.fetchall() == [("PACKAGE", "VALID"), ("PACKAGE BODY", "VALID"),
                                  ("TABLE", "VALID")]


def test_deploy_db_falha_com_body_que_nao_compila(tmp_path, conn_teste):
    raiz = _projeto(tmp_path, {
        "packages/pkg_cliente.pks": SPEC,
        "packages/pkg_cliente.pkb": """\
            CREATE OR REPLACE PACKAGE BODY pkg_cliente AS
              FUNCTION f_total RETURN NUMBER IS
              BEGIN
                RETURN tabela_que_nao_existe.coluna;
              END f_total;
            END pkg_cliente;
            /
        """,
    })
    r = _rodar(raiz)
    assert r.returncode == 1
    assert "erro(s) de compilação" in r.stdout + r.stderr


def test_deploy_db_nao_executa_nada_se_algum_arquivo_for_invalido(tmp_path, conn_teste):
    raiz = _projeto(tmp_path, {
        "tables/a_ok.sql": "CREATE TABLE t_a (id NUMBER);\n",
        "packages/pkg_sem_barra.pks": "CREATE OR REPLACE PACKAGE p AS\nEND p;\n",
    })
    r = _rodar(raiz)
    assert r.returncode == 1
    assert "terminador" in r.stdout + r.stderr
    with conn_teste.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM user_tables WHERE table_name = 'T_A'")
        assert cur.fetchone()[0] == 0
