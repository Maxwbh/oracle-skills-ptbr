"""Integração: classificação de patch level do apex_verificar_patch_seguranca.sql.

A imagem de teste não traz APEX: o teste cria uma view APEX_RELEASE simulada
(só a coluna VERSION_NO, usada pela query) e confere as fronteiras das faixas
afetadas do CPU out/2026.
"""
from pathlib import Path

import pytest

import oracle_devops_utils as u

ARQ = (Path(__file__).resolve().parents[2] / "skills" / "oracle-apex-ptbr" / "assets"
       / "apex_verificar_patch_seguranca.sql")
QUERY = next(c.texto for c in u.analisar_sql(ARQ.read_text(encoding="utf-8")) if c.tipo == "sql")


@pytest.mark.parametrize("versao, critica, media", [
    ("24.1.0", "VULNERÁVEL", "VULNERÁVEL"),
    ("24.1.19", "VULNERÁVEL", "VULNERÁVEL"),
    ("24.1.20", "VULNERÁVEL", "Fora"),
    ("24.1.21", "VULNERÁVEL", "Fora"),
    ("24.1.22", "Fora", "Fora"),
    ("24.2.18", "VULNERÁVEL", "VULNERÁVEL"),
    ("24.2.20", "VULNERÁVEL", "Fora"),
    ("24.2.21", "Fora", "Fora"),
    ("24.2.22", "Fora", "Fora"),
    ("26.1.2", "VULNERÁVEL", "VULNERÁVEL"),
    ("26.1.4", "VULNERÁVEL", "Fora"),
    ("26.1.5", "Fora", "Fora"),
    ("26.2.1", "Fora", "Fora"),
    ("23.2.0", "NÃO AVALIADA", "NÃO AVALIADA"),
])
def test_classificacao_por_versao(conn_teste, versao, critica, media):
    with conn_teste.cursor() as cur:
        cur.execute(f"CREATE OR REPLACE VIEW apex_release AS SELECT '{versao}' AS version_no FROM dual")
        cur.execute(QUERY)
        version_no, c1, c2 = cur.fetchone()
    assert version_no == versao
    assert c1.startswith(critica)
    assert c2.startswith(media)
