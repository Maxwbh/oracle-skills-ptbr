"""Import do APEX em deploy_full.py (item 1.5) — sem banco, SQLcl falso."""
import json
import stat
import sys
import textwrap

import pytest

import deploy_full as df
import oracle_devops_utils as u


def _export(tmp_path, app_id=100, completo=True):
    pasta = tmp_path / "apex" / f"app_{app_id}" / f"f{app_id}"
    (pasta / "application").mkdir(parents=True)
    (pasta / "install.sql").write_text(
        "PROMPT inicio\n@application/set_environment.sql\n@application/pages/page_00001.sql\n")
    if completo:
        (pasta / "application" / "set_environment.sql").write_text("PROMPT env\n")
    return pasta


class _Cur:
    def __init__(self, respostas):
        self.respostas = list(respostas)

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def execute(self, sql, **binds):
        pass

    def fetchone(self):
        return self.respostas.pop(0)


class _Conn:
    def __init__(self, *respostas):
        self.respostas = respostas

    def cursor(self):
        return _Cur(self.respostas)


def test_sem_export_split_falha_com_mensagem_clara(tmp_path):
    with pytest.raises(df.ErroImportApex, match="export_apex.py --app-id 100"):
        df.localizar_export_apex(tmp_path, 100)


def test_export_incompleto_falha(tmp_path):
    _export(tmp_path, completo=False)
    with pytest.raises(df.ErroImportApex, match="set_environment.sql"):
        df.localizar_export_apex(tmp_path, 100)


def test_workspace_inexistente_falha(tmp_path):
    with pytest.raises(df.ErroImportApex, match="Workspace 'WS_X' não encontrado"):
        df.validar_destino_apex(_Conn(None), "WS_X", 100)


def test_app_de_outro_workspace_falha():
    with pytest.raises(df.ErroImportApex, match="já existe no workspace 'OUTRO'"):
        df.validar_destino_apex(_Conn((1,), ("OUTRO",)), "MEU_WS", 100)


def test_app_novo_ou_do_mesmo_workspace_passa():
    df.validar_destino_apex(_Conn((1,), None), "MEU_WS", 100)
    df.validar_destino_apex(_Conn((1,), ("meu_ws",)), "MEU_WS", 100)


def test_workspace_com_injecao_eh_recusado():
    with pytest.raises(df.ErroImportApex, match="inválido"):
        df.preambulo_import_apex("x'); drop table y; --", 100, None)


def test_sem_sqlcl_falha_antes_de_conectar(tmp_path, monkeypatch):
    _export(tmp_path)
    monkeypatch.delenv("SQLCL_BIN", raising=False)
    monkeypatch.setattr(u.shutil, "which", lambda _: None)
    with pytest.raises(u.ErroSQLcl, match="SQLcl não encontrado"):
        df.importar_apex(None, {}, tmp_path, "WS", 100, None, dry_run=True)


def test_import_roda_install_do_export_a_partir_da_pasta_do_app(tmp_path, monkeypatch):
    pasta = _export(tmp_path)
    registro = tmp_path / "reg.json"
    exe = tmp_path / "sql"
    exe.write_text(textwrap.dedent(f"""\
        #!{sys.executable}
        import json, os, sys
        json.dump({{"stdin": sys.stdin.read(), "cwd": os.getcwd()}}, open({str(registro)!r}, "w"))
    """))
    exe.chmod(exe.stat().st_mode | stat.S_IEXEC)
    monkeypatch.setenv("SQLCL_BIN", str(exe))
    monkeypatch.setattr(df, "validar_destino_apex", lambda *a: None)
    monkeypatch.setattr(u, "data_hora_banco", lambda c: None)
    monkeypatch.setattr(u, "verificar_erros_compilacao", lambda c, d: [])
    cfg = {"host": "h", "port": 1521, "service": "s", "user": "app", "password": "p",
           "schema": "app"}

    df.importar_apex(object(), cfg, tmp_path, "meu_ws", 100, "ms_app", dry_run=False)

    reg = json.loads(registro.read_text())
    assert reg["cwd"] == str(pasta)
    stdin = reg["stdin"].splitlines()
    assert "  apex_application_install.set_workspace(p_workspace => 'MEU_WS');" in stdin
    assert "  apex_application_install.set_application_id(p_application_id => 100);" in stdin
    assert "  apex_application_install.set_schema(p_schema => 'MS_APP');" in stdin
    assert stdin.index("END;") < stdin.index(f'@"{(pasta / "install.sql").resolve()}"')
    assert "SET DEFINE OFF" in stdin
