#!/usr/bin/env python3
"""
deploy_ords.py — Deploy de módulos ORDS via oracledb
M&S do Brasil LTDA — contato@msbrasil.inf.br

Uso:
    python deploy_ords.py [--env dev|hom|prod] [--modulo nome_modulo]
    python deploy_ords.py --env dev
    python deploy_ords.py --env hom --modulo clientes_v2

Ordem de execução:
    1. ords/security/roles.sql
    2. ords/security/oauth_clients.sql
    3. ords/privileges/global_privileges.sql
    4. ords/modules/**/module.sql → templates.sql → handlers.sql → privileges.sql
    5. Verificação pós-deploy via DBA_ORDS_MODULES (24.4+) ou USER_ORDS_MODULES

Execução pelo SQLcl (pré-validação de todos os arquivos, WHENEVER SQLERROR
EXIT FAILURE ROLLBACK, ALL_ERRORS ao final de cada etapa).
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import oracledb

sys.path.insert(0, str(Path(__file__).parent))
from oracle_devops_utils import (
    BOLD,
    CYAN,
    DIM,
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
    executar_lote_sqlcl,
    log,
    obter_config_db,
    schema_efetivo,
    validar_arquivo_sql,
)

# Ordem canônica de execução dentro de cada módulo
PARTES_MODULO = ["module", "templates", "handlers", "privileges"]


def montar_plano(ords_dir: Path, modulo: str | None) -> list[tuple[str, list[Path]]]:
    """
    Etapas (rótulo, arquivos) na ordem canônica:
    segurança global → privileges globais → cada módulo (module → templates →
    handlers → privileges). Arquivos ausentes são simplesmente omitidos.
    """
    plano: list[tuple[str, list[Path]]] = []
    seguranca = [ords_dir / r for r in ("security/roles.sql", "security/oauth_clients.sql")]
    plano.append(("segurança global", [a for a in seguranca if a.exists()]))
    priv_dir = ords_dir / "privileges"
    plano.append(("privileges globais",
                  sorted(priv_dir.glob("*.sql")) if priv_dir.exists() else []))
    modules_dir = ords_dir / "modules"
    if modules_dir.exists():
        for d in sorted(x for x in modules_dir.iterdir() if x.is_dir()):
            if modulo is None or d.name == modulo:
                arquivos = [d / f"{parte}.sql" for parte in PARTES_MODULO]
                plano.append((f"módulo {d.name}", [a for a in arquivos if a.exists()]))
    return plano


def verificar_modulos(conn: oracledb.Connection) -> None:
    """
    Exibe os módulos ORDS publicados no schema alvo após o deploy.

    Usa USER_ORDS_MODULES que, após ALTER SESSION SET CURRENT_SCHEMA executado
    por conectar(), aponta para o schema alvo (não o usuário de conexão).

    Fallback para DBA_ORDS_MODULES (ORDS 24.4+) se disponível e o schema
    efetivo diferir do usuário conectado — garante visibilidade em qualquer
    configuração.
    """
    schema = schema_efetivo(conn)
    log.info(f"\n{SEP}")
    log.info(f"  {CYAN}Módulos ORDS publicados — schema: {schema}{RESET}")

    with conn.cursor() as cur:
        # Tenta DBA_ORDS_MODULES primeiro (ORDS 24.4+ — visão cross-schema)
        # Fallback para USER_ORDS_MODULES (funciona após ALTER SESSION SET CURRENT_SCHEMA)
        try:
            cur.execute("""
                SELECT name, uri_prefix, status, items_per_page
                  FROM dba_ords_modules
                 WHERE schema = :1
                 ORDER BY name
            """, [schema])
            fonte = "DBA_ORDS_MODULES"
        except oracledb.DatabaseError:
            cur.execute("""
                SELECT name, uri_prefix, status, items_per_page
                  FROM user_ords_modules
                 ORDER BY name
            """)
            fonte = "USER_ORDS_MODULES (CURRENT_SCHEMA)"

        rows = cur.fetchall()

    log.info(f"  {DIM}Fonte: {fonte}{RESET}")

    if not rows:
        log.info(f"  {YELLOW}Nenhum módulo encontrado no schema {schema}.{RESET}")
        return

    for nome, prefixo, status, _items in rows:
        cor = GREEN if status == "PUBLISHED" else YELLOW
        log.info(
            f"  {cor}{'●' if status == 'PUBLISHED' else '○'}{RESET} "
            f"{nome:<30} {prefixo:<25} {cor}{status}{RESET}"
        )


# ─── Ponto de entrada ─────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Deploy de módulos ORDS (security → privileges → modules)",
    )
    parser.add_argument("--env", default=os.environ.get("ENVIRONMENT", "dev"),
                        choices=["dev", "hom", "prod"])
    parser.add_argument("--modulo", default=None,
                        help="Deploya apenas este módulo (nome do diretório)")
    parser.add_argument("--project-root", type=Path,
                        default=Path(__file__).parent.parent)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--confirmar-prod", action="store_true",
                        help="Confirma deploy em produção sem prompt (obrigatório fora de TTY/CI)")
    args = parser.parse_args()

    root = args.project_root.resolve()
    ords_dir = root / "ords"

    carregar_dotenv(root)
    banner("deploy_ords.py — Deploy de módulos ORDS", args.env, args.dry_run)

    if args.env == "prod":
        confirmar_producao(args.dry_run, confirmado=args.confirmar_prod)

    plano = montar_plano(ords_dir, args.modulo)
    if args.modulo and not any(r == f"módulo {args.modulo}" for r, _ in plano):
        log.error(f"{RED}Módulo não encontrado: {args.modulo}{RESET}")
        sys.exit(1)

    todos = [a for _, arquivos in plano for a in arquivos]
    problemas = [p for a in todos for p in validar_arquivo_sql(a)]
    for rotulo, arquivos in plano:
        if arquivos:
            log.info(f"  {CYAN}{rotulo}{RESET}: {', '.join(a.name for a in arquivos)}")
    if problemas:
        for p in problemas:
            log.error(f"  {RED}✗ {p}{RESET}")
        sys.exit(1)

    if args.dry_run:
        log.info(f"\n{CYAN}DRY-RUN: {len(todos)} arquivo(s) validados, nada executado.{RESET}")
        return

    cfg = obter_config_db()
    conn = conectar(cfg)
    try:
        for rotulo, arquivos in plano:
            if not arquivos:
                continue
            log.info(f"\n{SEP}")
            log.info(f"  {BOLD}→ {rotulo}{RESET}")
            try:
                executar_lote_sqlcl(conn, arquivos, cfg, base=ords_dir)
            except ErroSQLcl as e:
                log.error(f"  {RED}✗ {e}{RESET}")
                if e.statement:
                    log.error(f"  {RED}  statement: {e.statement[:300]}{RESET}")
                log.error(f"\n{RED}⛔ Deploy ORDS interrompido em '{rotulo}'.{RESET}")
                sys.exit(1)
            log.info(f"  {GREEN}✓ {len(arquivos)} arquivo(s){RESET}")

        # Verificação pós-deploy
        verificar_modulos(conn)
    finally:
        conn.close()

    log.info(f"\n{SEP2}")
    log.info(f"  {GREEN}✅ Deploy ORDS concluído{RESET}")
    log.info(SEP2)


if __name__ == "__main__":
    main()
