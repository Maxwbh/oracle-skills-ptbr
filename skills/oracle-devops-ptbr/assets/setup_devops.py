#!/usr/bin/env python3
"""
setup_devops.py — Assistente que monta o esqueleto de CI/CD do projeto a partir
de duas escolhas: onde roda o CI/CD e se usa Liquibase.
M&S do Brasil LTDA — contato@msbrasil.inf.br

Dois eixos de decisão:
    CI/CD     -> git | azure | manual
    Liquibase -> sim | nao   (sim é o recomendado; "nao" usa o fluxo YAML legado)

Gera, na pasta do projeto:
    - Pipeline da plataforma escolhida (GitHub Actions ou Azure Pipelines), exceto manual
    - Estrutura de changelog (Liquibase XML) ou aponta o fluxo YAML legado
    - Um README-deploy.md explicando o combo e os próximos passos

Uso:
    python setup_devops.py                      # modo interativo (pergunta tudo)
    python setup_devops.py --ci git --liquibase sim --dest .
    python setup_devops.py --ci azure --liquibase sim --entrega script
    python setup_devops.py --ci manual --liquibase nao

Os arquivos-fonte (templates) ficam ao lado deste script, em assets/. Este
gerador apenas COPIA o template certo e cria a estrutura — não conecta no banco.
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

ASSETS = Path(__file__).resolve().parent

# Eixo 1: CI/CD  → arquivo de pipeline de origem e destino
CI_PIPELINE = {
    "git":   ("github-deploy-liquibase.yml", ".github/workflows/deploy-liquibase.yml"),
    "azure": ("azure-pipelines-liquibase.yml", "azure-pipelines.yml"),
    "manual": (None, None),  # sem pipeline; DBA executa
}

# Eixo 1 (legado, sem Liquibase): pipeline que chama apply_changelog.py
CI_PIPELINE_LEGADO = {
    "git":   ("github-deploy.yml", ".github/workflows/deploy.yml"),
    "azure": (None, None),   # não há template Azure legado; orientar no README
    "manual": (None, None),
}

_TTY = sys.stdout.isatty()
G = "\033[32m" if _TTY else ""
Y = "\033[33m" if _TTY else ""
R = "\033[31m" if _TTY else ""
C = "\033[36m" if _TTY else ""
B = "\033[1m" if _TTY else ""
Z = "\033[0m" if _TTY else ""


def log(msg: str, cor: str = "") -> None:
    print(f"{cor}{msg}{Z}")


def perguntar(rotulo: str, opcoes: list[str], default: str) -> str:
    op = "/".join(o if o != default else o.upper() for o in opcoes)
    while True:
        resp = input(f"{B}{rotulo}{Z} [{op}]: ").strip().lower()
        if not resp:
            return default
        if resp in opcoes:
            return resp
        log(f"  opção inválida; escolha entre {opcoes}", R)


def copiar(origem_rel: str, destino: Path) -> None:
    src = ASSETS / origem_rel
    if not src.is_file():
        log(f"  ! template ausente: {src.name} (pulei)", Y)
        return
    destino.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, destino)
    log(f"  + {destino}", G)


def estrutura_liquibase(dest: Path) -> None:
    """Cria db/changelog-master.xml e uma release de exemplo."""
    rel = dest / "db" / "releases" / "2026.01-gmud-001"
    (rel / "rollback").mkdir(parents=True, exist_ok=True)
    copiar("changelog-master.xml", dest / "db" / "changelog-master.xml")
    copiar("changelog-release-exemplo.xml", rel / "changelog.xml")
    copiar("gmud_liquibase.py", dest / "db" / "gmud_liquibase.py")
    log(f"  + {rel}/ (coloque aqui os .sql GMUD e os rollback/)", C)


def estrutura_legado(dest: Path) -> None:
    """Aponta o fluxo YAML legado (apply_changelog.py + changelog.yml)."""
    copiar("changelog_template.yml", dest / "db" / "changelog.yml")
    copiar("apply_changelog.py", dest / "db" / "apply_changelog.py")
    copiar("create-changelog-table.sql", dest / "db" / "create-changelog-table.sql")
    log("  (fluxo LEGADO: deploy por ordem de nome + checksum YAML)", Y)


README = """# Deploy — {ci} {lqb}

Setup gerado por setup_devops.py.

- CI/CD: **{ci}**
- Liquibase: **{lqb}**
- Entrega ao banco: **{entrega}**

## Próximos passos
{passos}

## Entrega ao banco (estratégias)
- A) runner/agent hospedado conecta direto (dev/hom).
- B) runner/agent self-hosted na rede do banco (recomendado p/ prod).
- C) pipeline só gera o SQL (updateSQL/dry-run); DBA aplica (Git não toca o banco).

Detalhes em references/liquibase-cicd-gmud-ptbr.md.
"""


def gerar_readme(dest: Path, ci: str, liquibase: bool, entrega: str) -> None:
    if liquibase:
        if ci == "git":
            passos = ("1. Crie os Environments dev/hom/prod no GitHub (reviewers em hom/prod).\n"
                      "2. Cadastre DB_URL/DB_USER/DB_PASSWORD como Environment Secrets.\n"
                      "3. Edite db/releases/.../changelog.xml e adicione seus .sql GMUD.\n"
                      "4. Rode o workflow (Actions) escolhendo o ambiente.")
        elif ci == "azure":
            passos = ("1. Crie os Environments dev/hom/prod em Pipelines > Environments.\n"
                      "2. Approvals and checks > Approvals em hom/prod.\n"
                      "3. Variable Groups oracle-dev/hom/prod com DB_URL/DB_USER/DB_PASSWORD.\n"
                      "4. Crie o pipeline a partir de azure-pipelines.yml.")
        else:  # manual
            passos = ("1. Edite db/releases/.../changelog.xml com seus .sql GMUD.\n"
                      "2. Gere o script: python db/gmud_liquibase.py prever --root db --env hom\n"
                      "3. DBA aplica via SQLcl: lb update -changelog db/changelog-master.xml -context hom")
    else:
        passos = ("1. Ajuste db/changelog.yml com os scripts na ordem.\n"
                  "2. Crie a tabela de controle: db/create-changelog-table.sql\n"
                  "3. Aplique: python db/apply_changelog.py --env hom\n"
                  "   (fluxo LEGADO; considere migrar para Liquibase)")
    txt = README.format(
        ci={"git": "GitHub Actions", "azure": "Azure Pipelines", "manual": "Manual (DBA)"}[ci],
        lqb="Sim (recomendado)" if liquibase else "Não (legado YAML)",
        entrega=entrega, passos=passos)
    (dest / "README-deploy.md").write_text(txt, encoding="utf-8")
    log(f"  + {dest/'README-deploy.md'}", G)


def main() -> int:
    ap = argparse.ArgumentParser(description="Assistente de setup CI/CD Oracle")
    ap.add_argument("--ci", choices=["git", "azure", "manual"])
    ap.add_argument("--liquibase", choices=["sim", "nao"])
    ap.add_argument("--entrega", choices=["A", "B", "C", "script"], default="C",
                    help="Estratégia de entrega ao banco (default C: DBA aplica)")
    ap.add_argument("--dest", default=".", help="Pasta do projeto")
    args = ap.parse_args()

    log(f"{B}Assistente de setup CI/CD — Oracle/APEX/ORDS{Z}", C)
    ci = args.ci or perguntar("Onde roda o CI/CD?", ["git", "azure", "manual"], "git")
    lqb_in = args.liquibase or perguntar("Usar Liquibase? (recomendado)", ["sim", "nao"], "sim")
    liquibase = (lqb_in == "sim")
    dest = Path(args.dest).resolve()
    log(f"\nCombo: CI={ci} | Liquibase={'sim' if liquibase else 'nao'} | dest={dest}\n", C)

    # Pipeline
    if ci != "manual":
        tabela = CI_PIPELINE if liquibase else CI_PIPELINE_LEGADO
        origem, destino_rel = tabela.get(ci, (None, None))
        if origem:
            copiar(origem, dest / destino_rel)
        else:
            log(f"  ! sem template de pipeline para {ci} (Liquibase={'sim' if liquibase else 'nao'});"
                f" configure manualmente (ver matriz no reference).", Y)
    else:
        log("  CI manual: nenhum pipeline gerado; o DBA executa os comandos.", Y)

    # Estrutura de deploy
    if liquibase:
        estrutura_liquibase(dest)
    else:
        estrutura_legado(dest)

    gerar_readme(dest, ci, liquibase, args.entrega)
    log(f"\n{G}Setup concluído.{Z} Veja README-deploy.md para os próximos passos.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
