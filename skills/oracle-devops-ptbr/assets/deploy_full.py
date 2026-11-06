#!/usr/bin/env python3
"""
deploy_full.py — Orquestrador de deploy completo: DB → APEX → ORDS
M&S do Brasil LTDA — contato@msbrasil.inf.br

Uso:
    python deploy_full.py [--env dev|hom|prod] [--dry-run] [--skip-apex] [--skip-ords]
    python deploy_full.py --env dev
    python deploy_full.py --env prod --dry-run

Ordem de execução:
    1. apply_changelog.py  (migrations pendentes do banco)
    2. import APEX pelo SQLcl: apex/app_{ID}/f{ID}/install.sql (export split),
       executado a partir dessa pasta, com workspace/app id do destino definidos
       por APEX_APPLICATION_INSTALL; workspace e app id validados antes
    3. deploy_ords.py      (módulos ORDS)
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import oracledb

from oracle_devops_utils import (
    BOLD,
    CYAN,
    GREEN,
    RED,
    RESET,
    SEP,
    SEP2,
    YELLOW,
    ErroSQLcl,
    banner,
    carregar_dotenv,
    conectar,
    confirmar_producao,
    executar_e_verificar,
    localizar_sqlcl,
    log,
    obter_config_db,
)


def rodar_script(
    script: str,
    args_extras: list[str],
    descricao: str,
) -> bool:
    """Executa outro script Python como subprocess. Retorna True se OK."""
    scripts_dir = Path(__file__).parent
    script_path = scripts_dir / script

    if not script_path.exists():
        log.error(f"{RED}{script} não encontrado em {scripts_dir}{RESET}")
        return False

    cmd = [sys.executable, str(script_path)] + args_extras
    log.info(f"  {CYAN}→ {' '.join(cmd[2:])}{RESET}")

    inicio = time.monotonic()
    resultado = subprocess.run(cmd, text=True, check=False)
    duracao = time.monotonic() - inicio

    if resultado.returncode == 0:
        log.info(f"  {GREEN}✓ {descricao} ({duracao:.1f}s){RESET}")
        return True
    else:
        log.error(f"  {RED}✗ {descricao} falhou (exit {resultado.returncode}){RESET}")
        return False


class ErroImportApex(RuntimeError):
    """Pré-condição do import APEX não atendida."""


def localizar_export_apex(root: Path, app_id: int) -> Path:
    """
    Pasta do export split (apex/app_<ID>/f<ID>) com o install.sql gerado pelo
    'apex export -split'. É a partir dela que o SQLcl roda o import: o
    install.sql do export chama os componentes com caminho relativo.
    """
    pasta = root / "apex" / f"app_{app_id}" / f"f{app_id}"
    install = pasta / "install.sql"
    if not install.exists():
        raise ErroImportApex(
            f"{install.relative_to(root)} não encontrado. Gere o export split com "
            f"'python scripts/export_apex.py --app-id {app_id}'."
        )
    if not (pasta / "application" / "set_environment.sql").exists():
        raise ErroImportApex(
            f"{pasta.relative_to(root)}/application/set_environment.sql não encontrado — "
            "o export split parece incompleto."
        )
    return pasta


def validar_destino_apex(conn, workspace: str, app_id: int) -> None:
    """
    Confere no banco de destino, antes do import:
    - o APEX está acessível ao usuário de deploy;
    - o workspace existe (e é visível ao usuário);
    - o app id não pertence a OUTRO workspace.
    """
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT workspace_id FROM apex_workspaces "
                        "WHERE workspace = UPPER(:ws)", ws=workspace)
            if cur.fetchone() is None:
                raise ErroImportApex(
                    f"Workspace '{workspace}' não encontrado no destino (ou o usuário de "
                    "deploy não tem acesso a ele: o schema precisa estar associado ao "
                    "workspace, ou ter APEX_ADMINISTRATOR_ROLE)."
                )
            cur.execute("SELECT workspace FROM apex_applications "
                        "WHERE application_id = :id", id=app_id)
            linha = cur.fetchone()
    except oracledb.DatabaseError as e:
        raise ErroImportApex(f"APEX não acessível no destino: {e}") from e
    if linha and linha[0].upper() != workspace.upper():
        raise ErroImportApex(
            f"App {app_id} já existe no workspace '{linha[0]}', não em '{workspace}'. "
            "Import abortado para não sobrescrever aplicação de outro workspace."
        )


def preambulo_import_apex(workspace: str, app_id: int, schema: str | None) -> list[str]:
    """
    Comandos executados antes do install.sql do export: define workspace, app
    id e (opcional) parsing schema do destino via APEX_APPLICATION_INSTALL.
    Sem isso, o import usa os IDs do ambiente de origem do export.
    """
    if not _RE_WORKSPACE.fullmatch(workspace):
        raise ErroImportApex(f"Nome de workspace inválido: '{workspace}'")
    linhas = [
        "BEGIN",
        f"  apex_application_install.set_workspace(p_workspace => '{workspace.upper()}');",
        f"  apex_application_install.set_application_id(p_application_id => {int(app_id)});",
    ]
    if schema:
        linhas.append(f"  apex_application_install.set_schema(p_schema => '{schema.upper()}');")
    linhas += ["END;", "/"]
    return linhas


_RE_WORKSPACE = re.compile(r"[A-Za-z][A-Za-z0-9_$#]{0,254}")


def importar_apex(conn, cfg: dict, root: Path, workspace: str, app_id: int,
                  schema: str | None, dry_run: bool) -> None:
    """Import do export split pelo SQLcl, a partir da pasta do app. Lança em erro."""
    if app_id <= 0:
        raise ErroImportApex(f"App id inválido: {app_id}")
    if not workspace:
        raise ErroImportApex("APEX_WORKSPACE não definido (--workspace ou variável de ambiente).")
    pasta = localizar_export_apex(root, app_id)
    localizar_sqlcl()  # falha cedo, com mensagem clara, se não houver SQLcl
    preambulo = preambulo_import_apex(workspace, app_id, schema)
    if dry_run:
        log.info(f"  {CYAN}DRY-RUN: importaria {pasta.relative_to(root)}/install.sql "
                 f"no workspace {workspace.upper()} como app {app_id}{RESET}")
        return
    validar_destino_apex(conn, workspace, app_id)
    executar_e_verificar(conn, pasta / "install.sql", cfg, cwd=pasta, preambulo=preambulo)
    log.info(f"  {GREEN}✓ APEX app {app_id} importado no workspace {workspace.upper()}{RESET}")


# ─── Ponto de entrada ─────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Deploy completo Oracle: changelog → APEX → ORDS",
    )
    parser.add_argument("--env", default=os.environ.get("ENVIRONMENT", "dev"),
                        choices=["dev", "hom", "prod"])
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--confirmar-prod", action="store_true",
                        help="Confirma deploy em produção sem prompt (obrigatório fora de TTY/CI)")
    parser.add_argument("--skip-db",   action="store_true", help="Pula changelog do banco")
    parser.add_argument("--skip-apex", action="store_true", help="Pula import APEX")
    parser.add_argument("--skip-ords", action="store_true", help="Pula deploy ORDS")
    parser.add_argument("--app-id", type=int,
                        default=int(os.environ.get("APEX_APP_ID", "100")))
    parser.add_argument("--workspace", default=os.environ.get("APEX_WORKSPACE", ""),
                        help="Workspace APEX de destino (padrão: APEX_WORKSPACE)")
    parser.add_argument("--apex-schema", default=os.environ.get("APEX_SCHEMA") or None,
                        help="Parsing schema no destino (padrão: APEX_SCHEMA; vazio = o do export)")
    parser.add_argument("--project-root", type=Path,
                        default=Path(__file__).parent.parent)
    args = parser.parse_args()

    root = args.project_root.resolve()
    carregar_dotenv(root)

    banner("deploy_full.py — Deploy completo Oracle/APEX/ORDS", args.env, args.dry_run)

    if args.env == "prod":
        confirmar_producao(args.dry_run, confirmado=args.confirmar_prod)

    args_comuns = [
        "--env", args.env,
        "--project-root", str(root),
    ] + (["--dry-run"] if args.dry_run else [])
    if args.env == "prod" and not args.dry_run:
        # Já confirmado acima: repassa aos scripts filhos para não perguntar de novo.
        args_comuns.append("--confirmar-prod")

    inicio_total = time.monotonic()
    etapas_ok: list[tuple[str, bool]] = []

    # ── Etapa 1: Changelog do banco ───────────────────────────────────────────
    log.info(f"\n{SEP}")
    log.info(f"  {BOLD}ETAPA 1/3 — Changelog do banco{RESET}")

    if args.skip_db:
        log.info(f"  {YELLOW}⏭  Pulado (--skip-db){RESET}")
        etapas_ok.append(("Banco (changelog)", True))
    else:
        ok = rodar_script("apply_changelog.py", args_comuns, "apply_changelog")
        etapas_ok.append(("Banco (changelog)", ok))
        if not ok:
            log.error(f"\n{RED}⛔ Etapa 1 falhou — deploy interrompido.{RESET}")
            sys.exit(1)

    # ── Etapa 2: APEX ─────────────────────────────────────────────────────────
    log.info(f"\n{SEP}")
    log.info(f"  {BOLD}ETAPA 2/3 — Import APEX (App {args.app_id}){RESET}")

    if args.skip_apex:
        log.info(f"  {YELLOW}⏭  Pulado (--skip-apex){RESET}")
        etapas_ok.append(("APEX", True))
    else:
        conn = None
        try:
            if not args.dry_run:
                cfg = obter_config_db()
                conn = conectar(cfg)
            else:
                cfg = {}
            importar_apex(conn, cfg, root, args.workspace, args.app_id,
                          args.apex_schema, args.dry_run)
            ok = True
        except (ErroImportApex, ErroSQLcl) as e:
            log.error(f"  {RED}✗ Import APEX: {e}{RESET}")
            if isinstance(e, ErroSQLcl) and e.statement:
                log.error(f"  {RED}  statement: {e.statement[:300]}{RESET}")
            ok = False
        finally:
            if conn is not None:
                conn.close()

        etapas_ok.append(("APEX", ok))
        if not ok:
            log.error(f"\n{RED}⛔ Etapa 2 falhou — deploy interrompido.{RESET}")
            sys.exit(1)

    # ── Etapa 3: ORDS ─────────────────────────────────────────────────────────
    log.info(f"\n{SEP}")
    log.info(f"  {BOLD}ETAPA 3/3 — Deploy ORDS{RESET}")

    if args.skip_ords:
        log.info(f"  {YELLOW}⏭  Pulado (--skip-ords){RESET}")
        etapas_ok.append(("ORDS", True))
    else:
        ok = rodar_script("deploy_ords.py", args_comuns, "deploy_ords")
        etapas_ok.append(("ORDS", ok))
        if not ok:
            log.error(f"\n{RED}⛔ Etapa 3 falhou.{RESET}")
            sys.exit(1)

    # ── Relatório ─────────────────────────────────────────────────────────────
    duracao_total = time.monotonic() - inicio_total

    log.info(f"\n{SEP2}")
    log.info(f"  {BOLD}DEPLOY {args.env.upper()} CONCLUÍDO — {duracao_total:.1f}s{RESET}")
    for etapa, ok in etapas_ok:
        icone = f"{GREEN}✅" if ok else f"{RED}❌"
        log.info(f"  {icone}  {etapa}{RESET}")
    log.info(SEP2)


if __name__ == "__main__":
    main()
