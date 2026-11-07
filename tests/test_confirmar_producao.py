"""confirmar_producao(): nunca input() em CI/sem TTY (revisão 2026-11, item 1.4)."""
import io

import pytest

import oracle_devops_utils as u


class _Stdin(io.StringIO):
    def __init__(self, texto="", tty=False):
        super().__init__(texto)
        self._tty = tty

    def isatty(self):
        return self._tty


@pytest.fixture(autouse=True)
def _limpa_env(monkeypatch):
    monkeypatch.delenv("CI", raising=False)
    monkeypatch.delenv("CONFIRMO_PROD", raising=False)


def _proibe_input(monkeypatch):
    def falha(*_):
        raise AssertionError("input() não pode ser chamado aqui")
    monkeypatch.setattr("builtins.input", falha)


def test_ci_sem_confirmacao_aborta_sem_chamar_input(monkeypatch):
    monkeypatch.setenv("CI", "true")
    monkeypatch.setattr("sys.stdin", _Stdin(tty=True))
    _proibe_input(monkeypatch)
    with pytest.raises(SystemExit) as exc:
        u.confirmar_producao()
    assert exc.value.code == 2


def test_sem_tty_sem_confirmacao_aborta_sem_chamar_input(monkeypatch):
    monkeypatch.setattr("sys.stdin", _Stdin(tty=False))
    _proibe_input(monkeypatch)
    with pytest.raises(SystemExit) as exc:
        u.confirmar_producao()
    assert exc.value.code == 2


def test_flag_confirmar_prod_segue_em_ci(monkeypatch):
    monkeypatch.setenv("CI", "true")
    _proibe_input(monkeypatch)
    u.confirmar_producao(confirmado=True)


def test_variavel_confirmo_prod_segue_sem_tty(monkeypatch):
    monkeypatch.setenv("CONFIRMO_PROD", "1")
    monkeypatch.setattr("sys.stdin", _Stdin(tty=False))
    _proibe_input(monkeypatch)
    u.confirmar_producao()


def test_terminal_interativo_pede_frase(monkeypatch):
    monkeypatch.setattr("sys.stdin", _Stdin(tty=True))
    monkeypatch.setattr("builtins.input", lambda *_: "CONFIRMO PROD")
    u.confirmar_producao()


def test_terminal_interativo_frase_errada_cancela(monkeypatch):
    monkeypatch.setattr("sys.stdin", _Stdin(tty=True))
    monkeypatch.setattr("builtins.input", lambda *_: "sim")
    with pytest.raises(SystemExit) as exc:
        u.confirmar_producao()
    assert exc.value.code == 1


def test_dry_run_nao_pede_nada(monkeypatch):
    monkeypatch.setenv("CI", "true")
    _proibe_input(monkeypatch)
    u.confirmar_producao(dry_run=True)
