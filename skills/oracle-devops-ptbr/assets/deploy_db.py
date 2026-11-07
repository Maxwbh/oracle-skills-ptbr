#!/usr/bin/env python3
"""
deploy_db.py — Deploy ordenado de objetos Oracle via oracledb
M&S do Brasil LTDA — contato@msbrasil.inf.br

Uso:
    python deploy_db.py [--env dev|hom|prod] [--tipo tables|packages|...]
    python deploy_db.py --env dev
    python deploy_db.py --env hom --tipo packages

Executa os objetos do banco pelo SQLcl, na ordem correta de dependências:
    sequences → types → tables → views → grants → synonyms →
    package specs (.pks) → package bodies (.pkb) →
    procedures → functions → triggers → scripts pontuais (db/scripts/)

Todos os arquivos são pré-validados antes de qualquer execução. Cada etapa
roda numa sessão do SQLcl (WHENEVER SQLERROR EXIT FAILURE ROLLBACK) e, ao
final, ALL_ERRORS é consultado: objeto com erro de compilação falha o deploy.
Requer SQLcl ('sql' no PATH ou SQLCL_BIN).
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from oracle_devops_utils import (
    CYAN,
    GREEN,
    RED,
    RESET,
    SEP,
    SEP2,
    ErroSQLcl,
    banner,
    carregar_dotenv,
    conectar,
    confirmar_producao,
    executar_lote_sqlcl,
    log,
    obter_config_db,
    validar_arquivo_sql,
)

# ─── Mapeamento: tipo → (subdir, extensões) ───────────────────────────────────

TIPOS = {
    "sequences":   ("sequences",   [".sql"]),
    "types":       ("types",       [".typ", ".sql"]),
    "tables":      ("tables",      [".sql"]),
    "constraints": ("constraints", [".sql"]),
    "fk":          ("fk",          [".sql"]),
    "indexes":     ("indexes",     [".sql"]),
    "views":       ("views",       [".vw", ".sql"]),
    "grants":      ("grants",      [".sql"]),
    "synonyms":    ("synonyms",    [".sql"]),
    "procedures":  ("procedures",  [".prc", ".sql"]),
    "functions":   ("functions",   [".fnc", ".sql"]),
    "triggers":    ("triggers",    [".trg", ".sql"]),
}

# Ordem canônica de deploy (respeita dependências entre objetos)
# Alinhada à seção "Ordem de deploy" do SKILL.md.
ORDEM_DEPLOY = [
    "sequences", "types", "tables",
    "constraints", "fk", "indexes",
    "grants", "synonyms", "views",
    # packages tratados à parte (spec antes do body)
    "procedures", "functions", "triggers",
]


def arquivos_do_tipo(db_dir: Path, tipo: str) -> list[Path]:
    """Arquivos de um subdiretório de db/, em ordem alfabética."""
    subdir, extensoes = TIPOS[tipo]
    diretorio = db_dir / subdir
    if not diretorio.exists():
        return []
    return sorted(f for f in diretorio.iterdir()
                  if f.is_file() and f.suffix.lower() in extensoes)


def arquivos_packages(db_dir: Path) -> list[Path]:
    """Specs (.pks) antes dos bodies (.pkb): body depende da spec."""
    pkg_dir = db_dir / "packages"
    if not pkg_dir.exists():
        return []
    return sorted(pkg_dir.glob("*.pks")) + sorted(pkg_dir.glob("*.pkb"))


def arquivos_scripts_pontuais(db_dir: Path) -> list[Path]:
    """Scripts pontuais db/scripts/NNN_*.sql em ordem numérica (padrão GMUD)."""
    scripts_dir = db_dir / "scripts"
    if not scripts_dir.exists():
        return []
    return sorted(f for f in scripts_dir.iterdir()
                  if f.is_file() and f.suffix == ".sql" and re.match(r"^\d{3}_", f.name))


def montar_plano(db_dir: Path, tipo: str) -> list[tuple[str, list[Path]]]:
    """Etapas (rótulo, arquivos) na ordem canônica de dependências."""
    if tipo == "all":
        plano = [(t, arquivos_do_tipo(db_dir, t)) for t in ORDEM_DEPLOY]
        plano.append(("packages (spec → body)", arquivos_packages(db_dir)))
        plano.append(("scripts pontuais", arquivos_scripts_pontuais(db_dir)))
        return plano
    if tipo == "packages":
        return [("packages (spec → body)", arquivos_packages(db_dir))]
    if tipo == "scripts":
        return [("scripts pontuais", arquivos_scripts_pontuais(db_dir))]
    return [(tipo, arquivos_do_tipo(db_dir, tipo))]


# ─── Ponto de entrada ─────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Deploy ordenado de objetos Oracle (sequences→tables→packages→triggers)",
    )
    parser.add_argument("--env", default=os.environ.get("ENVIRONMENT", "dev"),
                        choices=["dev", "hom", "prod"])
    parser.add_argument("--tipo", default="all",
                        choices=["all"] + list(TIPOS.keys()) + ["packages", "scripts"])
    parser.add_argument("--project-root", type=Path,
                        default=Path(__file__).parent.parent)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--confirmar-prod", action="store_true",
                        help="Confirma deploy em produção sem prompt (obrigatório fora de TTY/CI)")
    args = parser.parse_args()

    root = args.project_root.resolve()
    db_dir = root / "db"

    carregar_dotenv(root)

    banner("deploy_db.py — Deploy de objetos do banco", args.env, args.dry_run)

    if args.env == "prod":
        confirmar_producao(args.dry_run, confirmado=args.confirmar_prod)

    plano = montar_plano(db_dir, args.tipo)
    todos = [a for _, arquivos in plano for a in arquivos]

    # Pré-validação de TODOS os arquivos antes de tocar no banco.
    problemas = [p for a in todos for p in validar_arquivo_sql(a)]
    for rotulo, arquivos in plano:
        if arquivos:
            log.info(f"  {CYAN}{rotulo}{RESET}: {len(arquivos)} arquivo(s)")
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
            log.info(f"  {CYAN}{rotulo.upper()}{RESET}")
            try:
                executar_lote_sqlcl(conn, arquivos, cfg, base=db_dir)
            except ErroSQLcl as e:
                log.error(f"  {RED}✗ {e}{RESET}")
                if e.statement:
                    log.error(f"  {RED}  statement: {e.statement[:300]}{RESET}")
                log.error(f"\n{RED}⛔ Deploy interrompido em '{rotulo}'.{RESET}")
                sys.exit(1)
            log.info(f"  {GREEN}✓ {len(arquivos)} arquivo(s){RESET}")
    finally:
        conn.close()

    log.info(f"\n{SEP2}")
    log.info(f"  {GREEN}✅ Sucesso : {len(todos)} arquivo(s){RESET}")
    log.info(SEP2)


if __name__ == "__main__":
    main()
