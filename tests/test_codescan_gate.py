"""codescan_gate.py — gate de CI sobre o SQLcl CodeScan."""
import json
import os
import stat
import sys
import textwrap

import pytest

import codescan_gate as g

SQLCL_REAL = os.environ.get("SQLCL_BIN")


@pytest.fixture
def sql_falso(tmp_path, monkeypatch):
    """SQLcl falso: grava no -output o JSON definido em FAKE_JSON."""
    exe = tmp_path / "sql"
    exe.write_text(textwrap.dedent(f"""\
        #!{sys.executable}
        import os, re, sys
        cmd = sys.stdin.read()
        saida = re.search(r"-output '([^']+)'", cmd).group(1)
        open(saida, "w").write(os.environ.get("FAKE_JSON", "[]"))
    """))
    exe.chmod(exe.stat().st_mode | stat.S_IEXEC)
    monkeypatch.setenv("SQLCL_BIN", str(exe))
    (tmp_path / "db").mkdir()
    return tmp_path


def test_sem_achados_sai_zero(sql_falso, monkeypatch):
    monkeypatch.setenv("FAKE_JSON", "[]")
    assert g.main([str(sql_falso / "db")]) == 0


def test_com_achados_sai_um_mesmo_com_sqlcl_saindo_zero(sql_falso, monkeypatch):
    monkeypatch.setenv("FAKE_JSON", json.dumps([{"file": "p.sql", "issues": [
        {"line": 0, "col": 18, "ruleNo": "G-7310", "msg": "Avoid standalone procedures"}]}]))
    assert g.main([str(sql_falso / "db")]) == 1


def test_pasta_inexistente_eh_pulada(sql_falso, monkeypatch):
    monkeypatch.setenv("FAKE_JSON", "[]")
    assert g.main([str(sql_falso / "db"), str(sql_falso / "apex")]) == 0


def test_relatorio_ausente_sai_dois(tmp_path, monkeypatch):
    exe = tmp_path / "sql"
    exe.write_text(f"#!{sys.executable}\nimport sys; sys.stdin.read()\n")
    exe.chmod(exe.stat().st_mode | stat.S_IEXEC)
    monkeypatch.setenv("SQLCL_BIN", str(exe))
    (tmp_path / "db").mkdir()
    assert g.main([str(tmp_path / "db")]) == 2


@pytest.mark.skipif(not SQLCL_REAL, reason="SQLCL_BIN não definido (SQLcl real)")
def test_sqlcl_real_acha_violacao_e_settings_ignora(tmp_path, monkeypatch):
    monkeypatch.setenv("SQLCL_BIN", SQLCL_REAL)
    db = tmp_path / "db"
    db.mkdir()
    (db / "p.sql").write_text("CREATE OR REPLACE PROCEDURE p IS\nBEGIN\n  NULL;\nEND;\n/\n")
    assert g.main([str(db)]) == 1
    achados = []
    with pytest.MonkeyPatch.context():
        rel = tmp_path / "r.json"
        g.executar_codescan(db, saida=rel)
        achados = g.ler_achados(rel)
    regras = [{"ruleNo": a["ruleNo"]} for a in achados]
    cfg = tmp_path / "codescan.json"
    cfg.write_text(json.dumps({"ignore": regras}))
    assert g.main([str(db), "--settings", str(cfg)]) == 0
