"""gmud_liquibase.py — credenciais fora da linha de comando e prd sem input() em CI."""
import io
import json
import stat
import sys
import textwrap

import pytest

import gmud_liquibase as g

SENHA = "S3nh@_Secreta"


@pytest.fixture
def liquibase_falso(tmp_path, monkeypatch):
    registro = tmp_path / "reg.json"
    exe = tmp_path / "liquibase"
    exe.write_text(textwrap.dedent(f"""\
        #!{sys.executable}
        import json, os, sys
        env = {{k: v for k, v in os.environ.items() if k.startswith("LIQUIBASE_COMMAND_")}}
        json.dump({{"argv": sys.argv[1:], "env": env}}, open({str(registro)!r}, "w"))
    """))
    exe.chmod(exe.stat().st_mode | stat.S_IEXEC)
    monkeypatch.setenv("PATH", f"{tmp_path}:{__import__('os').environ['PATH']}")
    monkeypatch.setenv("DB_URL", "jdbc:oracle:thin:@//h:1521/s")
    monkeypatch.setenv("DB_USER", "deployer")
    monkeypatch.setenv("DB_PASSWORD", SENHA)
    master = tmp_path / "changelog-master.xml"
    master.write_text("<databaseChangeLog/>")
    return master, lambda: json.loads(registro.read_text())


@pytest.mark.parametrize("comando", ["update", "updateSQL", "validate"])
def test_senha_vai_por_variavel_e_nao_pela_linha_de_comando(liquibase_falso, capsys, comando):
    master, reg = liquibase_falso
    assert g.run_liquibase(master, comando, "hml", "liquibase") == 0
    dados = reg()
    assert SENHA not in " ".join(dados["argv"])
    assert dados["env"]["LIQUIBASE_COMMAND_PASSWORD"] == SENHA
    assert dados["env"]["LIQUIBASE_COMMAND_URL"] == "jdbc:oracle:thin:@//h:1521/s"
    assert SENHA not in capsys.readouterr().out   # nem no log


def test_runner_script_tambem_nao_expoe_senha(liquibase_falso, tmp_path, monkeypatch):
    master, reg = liquibase_falso
    monkeypatch.chdir(tmp_path)
    assert g.run_liquibase(master, "updateSQL", "prd", "script") == 0
    assert SENHA not in " ".join(reg()["argv"])


class _Stdin(io.StringIO):
    def isatty(self):
        return False


def test_prd_em_ci_sem_yes_recusa_sem_chamar_input(monkeypatch):
    monkeypatch.setenv("CI", "true")
    monkeypatch.delenv("CONFIRMO_PROD", raising=False)
    monkeypatch.setattr("builtins.input", lambda *_: pytest.fail("input() em CI"))
    assert g.confirmar_prd(False) is False


def test_prd_sem_tty_sem_yes_recusa(monkeypatch):
    monkeypatch.delenv("CI", raising=False)
    monkeypatch.delenv("CONFIRMO_PROD", raising=False)
    monkeypatch.setattr("sys.stdin", _Stdin())
    monkeypatch.setattr("builtins.input", lambda *_: pytest.fail("input() sem TTY"))
    assert g.confirmar_prd(False) is False


def test_prd_com_yes_segue(monkeypatch):
    monkeypatch.setenv("CI", "true")
    assert g.confirmar_prd(True) is True


def _changelog(tmp_path):
    ns = 'xmlns="http://www.liquibase.org/xml/ns/dbchangelog"'
    rel = tmp_path / "releases" / "r1"
    rel.mkdir(parents=True)
    (rel / "001.sql").write_text("SELECT 1 FROM dual;\n")
    (rel / "changelog.xml").write_text(
        f'<databaseChangeLog {ns}><changeSet id="1" author="a">'
        '<sqlFile path="001.sql" relativeToChangelogFile="true"/>'
        '<rollback><sqlFile path="rollback/001.sql" relativeToChangelogFile="true"/></rollback>'
        '</changeSet></databaseChangeLog>')
    master = tmp_path / "changelog-master.xml"
    master.write_text(f'<databaseChangeLog {ns}>'
                      '<include file="releases/r1/changelog.xml" relativeToChangelogFile="true"/>'
                      '</databaseChangeLog>')
    return master, rel


def test_verificar_offline_aponta_arquivo_inexistente(tmp_path):
    master, _ = _changelog(tmp_path)
    erros = g.verificar_offline(master)
    assert erros == ["changelog.xml: referência inexistente: rollback/001.sql"]


def test_verificar_offline_ok(tmp_path):
    master, rel = _changelog(tmp_path)
    (rel / "rollback").mkdir()
    (rel / "rollback" / "001.sql").write_text("SELECT 1 FROM dual;\n")
    assert g.verificar_offline(master) == []


def test_verificar_offline_xml_invalido(tmp_path):
    master = tmp_path / "changelog-master.xml"
    master.write_text("<databaseChangeLog>")
    assert "XML inválido" in g.verificar_offline(master)[0]
