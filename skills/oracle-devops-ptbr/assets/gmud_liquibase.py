#!/usr/bin/env python3
"""
gmud_liquibase.py — Gera o changelog mestre Liquibase a partir dos .sql GMUD e
invoca o Liquibase (ou o Liquibase embutido no SQLcl) no ambiente certo.
M&S do Brasil LTDA — contato@msbrasil.inf.br

Por que existe: a skill já nomeia os scripts no padrão GMUD
(001_projeto_ddl_objeto.sql). Este utilitário monta um changelog-master.xml
Liquibase REAL incluindo cada release na ordem correta e dispara o update/
updateSQL/rollback. Assim o controle do que já foi aplicado fica em
DATABASECHANGELOG (Liquibase), e a ordem é explícita no XML.

Uso:
    # Gerar/atualizar o master.xml a partir de db/releases/*/changelog.xml
    python gmud_liquibase.py gerar --root db

    # Verificar sem banco: XML bem-formado e arquivos referenciados existem
    python gmud_liquibase.py verificar --root db

    # Validar o changelog (sintaxe, ids duplicados) — o Liquibase exige conexão
    python gmud_liquibase.py validar --root db

    # Prever o SQL (dry-run) para um ambiente — não aplica
    python gmud_liquibase.py prever --root db --env hom

    # Aplicar no ambiente (context = env). Pede confirmação se env=prod
    python gmud_liquibase.py aplicar --root db --env hom

    # Rollback até uma tag de release
    python gmud_liquibase.py rollback --root db --env hom --tag 2026.01-gmud-001

Estratégia de entrega ao banco (defina por projeto):
    --runner liquibase   usa o binário 'liquibase' (default)
    --runner sqlcl       usa 'sql' (SQLcl) com 'lb' embutido
    --runner script      só gera o SQL (updateSQL) p/ o DBA aplicar (Git não toca o banco)

Conexão: lida de variáveis de ambiente por ambiente, nunca hard-coded:
    DB_URL, DB_USER, DB_PASSWORD   (ex.: definidas no GitHub Environment)
    Repassadas ao Liquibase como LIQUIBASE_COMMAND_URL/USERNAME/PASSWORD — a
    senha não vai na linha de comando nem no log.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

# ─── Cores de terminal (degradam para vazio se não for TTY) ───────────────────
_TTY = sys.stdout.isatty()
GREEN = "\033[32m" if _TTY else ""
YELLOW = "\033[33m" if _TTY else ""
RED = "\033[31m" if _TTY else ""
CYAN = "\033[36m" if _TTY else ""
BOLD = "\033[1m" if _TTY else ""
RESET = "\033[0m" if _TTY else ""


def log(msg: str, cor: str = "") -> None:
    print(f"{cor}{msg}{RESET}")


# ─── Geração do master.xml a partir das releases ─────────────────────────────

MASTER_HEADER = '''<?xml version="1.0" encoding="UTF-8"?>
<!-- GERADO por gmud_liquibase.py — edite as releases, não este arquivo. -->
<databaseChangeLog
    xmlns="http://www.liquibase.org/xml/ns/dbchangelog"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xsi:schemaLocation="http://www.liquibase.org/xml/ns/dbchangelog
        http://www.liquibase.org/xml/ns/dbchangelog/dbchangelog-latest.xsd">

    <preConditions onFail="HALT" onError="HALT">
        <dbms type="oracle"/>
    </preConditions>

'''

MASTER_FOOTER = "\n</databaseChangeLog>\n"


def gerar_master(root: Path) -> Path:
    """Monta changelog-master.xml incluindo releases/*/changelog.xml em ordem."""
    releases_dir = root / "releases"
    if not releases_dir.is_dir():
        log(f"Pasta de releases não encontrada: {releases_dir}", RED)
        sys.exit(1)

    # Ordem = ordem alfabética do nome da release (por isso o prefixo numérico:
    # 2026.01-gmud-001, 2026.02-gmud-002, ...). A ordem importa.
    releases = sorted(
        d for d in releases_dir.iterdir()
        if d.is_dir() and (d / "changelog.xml").is_file()
    )
    if not releases:
        log("Nenhuma release com changelog.xml encontrada.", YELLOW)

    linhas = []
    for rel in releases:
        # caminho relativo ao master (que fica em root/)
        rel_path = (rel / "changelog.xml").relative_to(root).as_posix()
        linhas.append(
            f'    <include file="{rel_path}" relativeToChangelogFile="true"/>'
        )
        log(f"  + {rel_path}", CYAN)

    master = root / "changelog-master.xml"
    master.write_text(MASTER_HEADER + "\n".join(linhas) + MASTER_FOOTER,
                      encoding="utf-8")
    log(f"Master gerado: {master}  ({len(releases)} release(s))", GREEN)
    return master


# ─── Verificação offline (sem banco) ─────────────────────────────────────────

_NS = "{http://www.liquibase.org/xml/ns/dbchangelog}"


def verificar_offline(master: Path) -> list[str]:
    """
    Checagem que NÃO precisa de banco (o 'liquibase validate' precisa):
    XML bem-formado e todo <include file> / <sqlFile path> existente,
    seguindo os includes recursivamente. Retorna a lista de problemas.
    """
    erros: list[str] = []
    vistos: set[Path] = set()

    def visitar(arq: Path) -> None:
        arq = arq.resolve()
        if arq in vistos:
            return
        vistos.add(arq)
        try:
            raiz = ET.parse(arq).getroot()
        except (ET.ParseError, OSError) as e:
            erros.append(f"{arq.name}: XML inválido ou ilegível: {e}")
            return
        for el in raiz.iter():
            if el.tag == _NS + "include":
                ref = el.get("file")
            elif el.tag == _NS + "sqlFile":
                ref = el.get("path")
            else:
                continue
            if not ref:
                continue
            relativo = el.get("relativeToChangelogFile") == "true"
            alvo = (arq.parent / ref) if relativo else Path(ref)
            if not alvo.exists():
                erros.append(f"{arq.name}: referência inexistente: {ref}")
            elif el.tag == _NS + "include":
                visitar(alvo)

    visitar(master)
    return erros


# ─── Invocação do Liquibase / SQLcl ──────────────────────────────────────────

def _conexao_env() -> dict[str, str]:
    """
    Credenciais para o Liquibase via variáveis LIQUIBASE_COMMAND_* — nunca na
    linha de comando (visível em 'ps' e no log do pipeline).
    """
    url = os.environ.get("DB_URL")
    user = os.environ.get("DB_USER")
    pwd = os.environ.get("DB_PASSWORD")
    faltando = [n for n, v in (("DB_URL", url), ("DB_USER", user),
                               ("DB_PASSWORD", pwd)) if not v]
    if faltando:
        log(f"Variáveis de conexão ausentes: {', '.join(faltando)}", RED)
        sys.exit(2)
    return {**os.environ,
            "LIQUIBASE_COMMAND_URL": url,
            "LIQUIBASE_COMMAND_USERNAME": user,
            "LIQUIBASE_COMMAND_PASSWORD": pwd}


def confirmar_prod(confirmado: bool) -> bool:
    """
    Confirmação de produção. Com --yes ou CONFIRMO_PROD=1: segue. Em CI
    (CI=true) ou sem TTY: nunca chama input() — sem confirmação explícita,
    recusa. No pipeline, a aprovação vem do Environment 'prod'.
    """
    if confirmado or os.environ.get("CONFIRMO_PROD") == "1":
        return True
    em_ci = os.environ.get("CI", "").strip().lower() in ("1", "true", "yes")
    if em_ci or not sys.stdin.isatty():
        log("Aplicar em prod sem confirmação em modo não interativo: use --yes "
            "(após a aprovação do Environment) ou CONFIRMO_PROD=1.", RED)
        return False
    resp = input(f"{BOLD}{RED}Aplicar em PRODUÇÃO. Digite 'prod' para confirmar: {RESET}")
    return resp.strip() == "prod"


def run_liquibase(master: Path, comando: str, env: str | None,
                  runner: str, tag: str | None = None) -> int:
    """Executa o comando Liquibase via 'liquibase', 'sqlcl' ou 'script'."""
    changelog = str(master)
    ctx = f"--contexts={env}" if env else ""

    if runner == "liquibase":
        base = ["liquibase", f"--changelog-file={changelog}"]
        if comando in ("update", "updateSQL", "validate", "rollback"):
            # Até o 'validate' do Liquibase exige conexão (--url).
            env_proc = _conexao_env()
            args = list(base)
            if ctx and comando != "validate":
                args.append(ctx)
            if comando == "rollback":
                if not tag:
                    log("rollback exige --tag", RED)
                    sys.exit(2)
                args += ["rollback", tag]
            else:
                args.append(comando)
        else:
            log(f"Comando não suportado: {comando}", RED)
            sys.exit(2)

    elif runner == "sqlcl":
        # SQLcl: 'sql' executa um script com comandos 'lb ...'
        lb = {
            "update":   f"lb update -changelog {changelog}"
                        + (f" -context {env}" if env else ""),
            "updateSQL": f"lb updatesql -changelog {changelog}"
                         + (f" -context {env}" if env else ""),
            "rollback": f"lb rollback -changelog {changelog} -tag {tag}"
                        if tag else None,
            "validate": f"lb validate -changelog {changelog}",
        }.get(comando)
        if not lb:
            log(f"Comando não suportado no SQLcl: {comando}", RED)
            sys.exit(2)
        # 'sql /nolog' + connect string da env var; aqui assumimos DB_URL no
        # formato aceito pelo SQLcl (user/pwd@host:port/service).
        conn = os.environ.get("SQLCL_CONNECT", "/nolog")
        args = ["sql", "-S", conn]
        return _run_stdin(args, lb + "\nexit\n")

    elif runner == "script":
        # Só gera o SQL previsto para o DBA aplicar (Git não toca o banco).
        base = ["liquibase", f"--changelog-file={changelog}"]
        if ctx:
            base.append(ctx)
        base.append("updateSQL")
        out = Path(f"gmud-{env or 'all'}.sql")
        log(f"Gerando script para o DBA: {out}", YELLOW)
        with out.open("w", encoding="utf-8") as fh:
            return subprocess.call(base, stdout=fh, env=_conexao_env())

    else:
        log(f"Runner desconhecido: {runner}", RED)
        sys.exit(2)

    log(f"$ {' '.join(args)}", CYAN)   # sem credenciais: vão por variável de ambiente
    return subprocess.call(args, env=env_proc)


def _run_stdin(args: list[str], stdin_text: str) -> int:
    log(f"$ {' '.join(args)}  (via stdin)", CYAN)
    p = subprocess.run(args, input=stdin_text, text=True, check=False)
    return p.returncode


# ─── CLI ─────────────────────────────────────────────────────────────────────

def main() -> int:
    ap = argparse.ArgumentParser(description="GMUD + Liquibase para Oracle")
    ap.add_argument("acao",
                    choices=["gerar", "verificar", "validar", "prever", "aplicar", "rollback"])
    ap.add_argument("--root", default="db",
                    help="Pasta raiz do changelog (contém releases/)")
    ap.add_argument("--env", choices=["dev", "hom", "prod"],
                    help="Ambiente alvo (vira o context do Liquibase)")
    ap.add_argument("--runner", choices=["liquibase", "sqlcl", "script"],
                    default="liquibase")
    ap.add_argument("--tag", help="Tag de release para rollback")
    ap.add_argument("--yes", action="store_true",
                    help="Não pedir confirmação em prod")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    master = root / "changelog-master.xml"

    if args.acao == "gerar":
        gerar_master(root)
        return 0

    if args.acao == "verificar":
        if not master.is_file():
            log(f"{master} não existe (rode 'gerar').", RED)
            return 1
        erros = verificar_offline(master)
        for e in erros:
            log(f"  ✗ {e}", RED)
        if not erros:
            log("✓ changelog consistente (verificação offline)", GREEN)
        return 1 if erros else 0

    # As demais ações precisam do master; gera se não existir.
    if not master.is_file():
        log("master.xml não existe; gerando...", YELLOW)
        master = gerar_master(root)

    if args.acao == "validar":
        return run_liquibase(master, "validate", None, args.runner)

    if args.acao == "prever":
        return run_liquibase(master, "updateSQL", args.env, args.runner)

    if args.acao == "aplicar":
        if args.env == "prod" and not confirmar_prod(args.yes):
            log("Cancelado.", YELLOW)
            return 1
        return run_liquibase(master, "update", args.env, args.runner)

    if args.acao == "rollback":
        return run_liquibase(master, "rollback", args.env, args.runner, args.tag)

    return 0


if __name__ == "__main__":
    sys.exit(main())
