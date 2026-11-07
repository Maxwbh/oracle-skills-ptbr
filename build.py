#!/usr/bin/env python3
"""
build.py — Build, propagação e empacotamento das oracle-skills-ptbr
M&S do Brasil LTDA — contato@msbrasil.inf.br

Uso:
    python build.py                    # empacota todas as skills
    python build.py --skill oracle-dba-ptbr   # empacota só uma
    python build.py --check            # verifica consistência sem empacotar
    python build.py --checksums        # gera checksums dos .skill em dist/

O que este script faz:
    1. Propaga shared/ → cada skill que declara dependência
    2. Valida frontmatter (validação própria: YAML, name = pasta, description
       ≤ 1024, version, suite_size = contagem real, CHANGELOG, clientes reais)
    3. Empacota cada skill → dist/*.skill
    4. Gera dist/checksums.sha256

Estrutura esperada:
    oracle-skills-ptbr/
    ├── build.py              (este arquivo)
    ├── marketplace.yml
    ├── shared/               (fontes únicas da verdade)
    │   ├── references/
    │   └── assets/
    ├── skills/
    │   ├── oracle-dba-ptbr/
    │   │   ├── SKILL.md
    │   │   ├── manifest.yml  (declara dependências de shared/)
    │   │   ├── assets/
    │   │   └── references/
    │   └── ...
    └── dist/                 (gerado por este script)
"""

from __future__ import annotations

import argparse
import hashlib
import os
import re
import shutil
import sys
import unicodedata
import zipfile
from pathlib import Path

import yaml

ROOT      = Path(__file__).parent.resolve()
SKILLS    = ROOT / "skills"
SHARED    = ROOT / "shared"
DIST      = ROOT / "dist"
BUILD_TMP = ROOT / ".build_tmp"

# Cores
_TTY = sys.stdout.isatty()
G = "\033[92m" if _TTY else ""
Y = "\033[93m" if _TTY else ""
R = "\033[91m" if _TTY else ""
C = "\033[96m" if _TTY else ""
B = "\033[1m"  if _TTY else ""
Z = "\033[0m"  if _TTY else ""

def log(msg: str)  -> None: print(msg)
def ok(msg: str)   -> None: print(f"  {G}✅ {msg}{Z}")
def warn(msg: str) -> None: print(f"  {Y}⚠  {msg}{Z}")
def err(msg: str)  -> None: print(f"  {R}❌ {msg}{Z}")
def sep()          -> None: print(f"  {'─'*52}")


# ─── Manifest de cada skill ───────────────────────────────────────────────────

def ler_manifest(skill_dir: Path) -> dict:
    """
    Lê manifest.yml da skill para saber o que importar de shared/.
    Se não existir, retorna manifest vazio (sem dependências shared/).

    Formato do manifest.yml:
        shared:
          references:
            - data-dictionary-ptbr.md
            - plsql-trivadis-guidelines.md
          assets:
            - oracle_devops_utils.py
    """
    manifest_path = skill_dir / "manifest.yml"
    if not manifest_path.exists():
        return {"shared": {"references": [], "assets": []}}
    with open(manifest_path) as f:
        return yaml.safe_load(f) or {}


# ─── Propagação de shared/ ────────────────────────────────────────────────────

def propagar_shared(skill_dir: Path, build_dir: Path) -> list[str]:
    """
    Copia arquivos de shared/ para a skill no diretório de build.
    Retorna lista de arquivos propagados.
    """
    manifest  = ler_manifest(skill_dir)
    shared_cfg = manifest.get("shared", {})
    propagados: list[str] = []

    for ref in shared_cfg.get("references", []):
        src = SHARED / "references" / ref
        dst = build_dir / "references" / ref
        if src.exists():
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            propagados.append(f"shared/references/{ref}")
        else:
            warn(f"shared/references/{ref} — não encontrado")

    for asset in shared_cfg.get("assets", []):
        src = SHARED / "assets" / asset
        dst = build_dir / "assets" / asset
        if src.exists():
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            propagados.append(f"shared/assets/{asset}")
        else:
            warn(f"shared/assets/{asset} — não encontrado")

    return propagados


# ─── Validação do SKILL.md (própria — não depende de /mnt/skills) ───────────

LIMITE_DESCRIPTION = 1024

# Ignorados no pacote e na contagem de recursos (suite_size).
IGNORAR = ("manifest.yml", "__pycache__", "*.pyc")


def ler_frontmatter(skill_dir: Path) -> tuple[dict | None, str | None]:
    """(frontmatter, erro). Frontmatter = bloco YAML entre os '---' iniciais."""
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        return None, "SKILL.md não encontrado"
    texto = skill_md.read_text(encoding="utf-8")
    if not texto.startswith("---\n"):
        return None, "SKILL.md sem frontmatter (deve começar com '---')"
    fim = texto.find("\n---", 4)
    if fim == -1:
        return None, "frontmatter sem '---' de fechamento"
    try:
        dados = yaml.safe_load(texto[4:fim])
    except yaml.YAMLError as e:
        return None, f"frontmatter: YAML inválido ({str(e).splitlines()[0]})"
    if not isinstance(dados, dict):
        return None, "frontmatter: YAML não é um mapa"
    return dados, None


def validar_skill(skill_dir: Path) -> bool:
    """Frontmatter mínimo para empacotar (YAML, name = pasta, description, version)."""
    dados, erro = ler_frontmatter(skill_dir)
    return erro is None and not _problemas_frontmatter(skill_dir, dados)


def _problemas_frontmatter(skill_dir: Path, dados: dict) -> list[str]:
    problemas: list[str] = []
    if dados.get("name") != skill_dir.name:
        problemas.append(f"name '{dados.get('name')}' diferente da pasta '{skill_dir.name}'")
    descricao = dados.get("description")
    if not isinstance(descricao, str) or not descricao.strip():
        problemas.append("description ausente")
    elif len(descricao) > LIMITE_DESCRIPTION:
        problemas.append(f"description com {len(descricao)} caracteres (máx. {LIMITE_DESCRIPTION})")
    meta = dados.get("metadata") or {}
    if not str(meta.get("version", "")).strip():
        problemas.append("metadata.version ausente")
    return problemas


def _ignorado(rel: Path) -> bool:
    return any(rel.match(padrao) or padrao in rel.parts for padrao in IGNORAR)


def arquivos_do_pacote(skill_dir: Path) -> list[str]:
    """Caminhos relativos que vão para o .skill: a pasta + shared/ propagado."""
    rels = {str(f.relative_to(skill_dir)) for f in skill_dir.rglob("*")
            if f.is_file() and not _ignorado(f.relative_to(skill_dir))}
    shared_cfg = ler_manifest(skill_dir).get("shared", {}) or {}
    for tipo in ("references", "assets"):
        for nome in shared_cfg.get(tipo, []) or []:
            if (SHARED / tipo / nome).exists():
                rels.add(f"{tipo}/{nome}")
    return sorted(rels)


def contar_recursos(skill_dir: Path) -> int:
    """suite_size real: arquivos do pacote, exceto SKILL.md (CHANGELOG.md conta)."""
    return sum(1 for r in arquivos_do_pacote(skill_dir) if r != "SKILL.md")


# Nomes de clientes reais que nunca podem ir para o repositório público.
# Nomes adicionais sem publicá-los: variável CLIENTES_PROIBIDOS (separados por
# vírgula; no CI, um secret) ou arquivo .clientes-proibidos.txt na raiz
# (um por linha; está no .gitignore).
CLIENTES_PROIBIDOS = ["IMESC", "Zitrus", "Memora", "Hapvida", "Nexdom"]


def clientes_proibidos() -> list[str]:
    termos = list(CLIENTES_PROIBIDOS)
    termos += [t.strip() for t in os.environ.get("CLIENTES_PROIBIDOS", "").split(",") if t.strip()]
    extra = ROOT / ".clientes-proibidos.txt"
    if extra.exists():
        termos += [linha.strip() for linha in extra.read_text(encoding="utf-8").splitlines()
                   if linha.strip() and not linha.startswith("#")]
    return termos


def _sem_acento(texto: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", texto)
                   if not unicodedata.combining(c)).lower()


def procurar_clientes(skill_dir: Path) -> list[str]:
    """Varre TODOS os arquivos de texto da skill (não só .md)."""
    termos = [(t, re.compile(rf"\b{re.escape(_sem_acento(t))}\b")) for t in clientes_proibidos()]
    achados: list[str] = []
    for arquivo in sorted(skill_dir.rglob("*")):
        if not arquivo.is_file() or _ignorado(arquivo.relative_to(skill_dir)):
            continue
        try:
            conteudo = _sem_acento(arquivo.read_text(encoding="utf-8"))
        except (UnicodeDecodeError, OSError):
            continue  # binário
        for termo, padrao in termos:
            if padrao.search(conteudo):
                achados.append(f"cliente real '{termo}' em {arquivo.relative_to(skill_dir)}")
    return achados


def versao_changelog(skill_dir: Path) -> str | None:
    changelog = skill_dir / "CHANGELOG.md"
    if not changelog.exists():
        return None
    m = re.search(r"^## \[([^\]]+)\]", changelog.read_text(encoding="utf-8"), re.MULTILINE)
    return m.group(1) if m else None


# ─── Empacotamento ────────────────────────────────────────────────────────────

def empacotar_skill(skill_dir: Path) -> Path:
    """
    Monta a skill em BUILD_TMP (com propagação de shared/),
    valida e gera dist/{name}.skill.
    Retorna Path do .skill gerado.
    """
    name     = skill_dir.name
    build_dir = BUILD_TMP / name

    # Limpar e recriar diretório de build
    if build_dir.exists():
        shutil.rmtree(build_dir)
    # manifest.yml é metadado de build, não recurso da skill; caches do Python
    # (gerados ao rodar os testes) também ficam fora do pacote.
    shutil.copytree(skill_dir, build_dir, ignore=shutil.ignore_patterns(*IGNORAR))

    # Propagar shared/
    propagados = propagar_shared(skill_dir, build_dir)
    if propagados:
        for p in propagados:
            log(f"    {C}↓ propagado:{Z} {p}")

    # Validar
    if not validar_skill(build_dir):
        err(f"Frontmatter inválido em {name}")
        return None

    # Empacotar como .zip renomeado para .skill
    DIST.mkdir(exist_ok=True)
    skill_file = DIST / f"{name}.skill"

    with zipfile.ZipFile(skill_file, "w", zipfile.ZIP_DEFLATED) as zf:
        for arquivo in sorted(build_dir.rglob("*")):
            if arquivo.is_file():
                arcname = name + "/" + str(arquivo.relative_to(build_dir))
                zf.write(arquivo, arcname)

    return skill_file


# ─── Checksums ────────────────────────────────────────────────────────────────

def gerar_checksums() -> Path:
    """Gera dist/checksums.sha256 com SHA-256 de cada .skill."""
    checksums_file = DIST / "checksums.sha256"
    linhas: list[str] = []

    for skill_file in sorted(DIST.glob("*.skill")):
        sha = hashlib.sha256(skill_file.read_bytes()).hexdigest()
        linhas.append(f"{sha}  {skill_file.name}")
        log(f"    {sha[:16]}...  {skill_file.name}")

    checksums_file.write_text("\n".join(linhas) + "\n", encoding="utf-8")
    return checksums_file


# ─── Verificação de consistência ─────────────────────────────────────────────

def verificar(skill_dir: Path) -> list[str]:
    """Verifica consistência da skill sem empacotar. Retorna lista de problemas."""
    dados, erro = ler_frontmatter(skill_dir)
    if erro:
        return [erro]
    problemas = _problemas_frontmatter(skill_dir, dados)
    meta = dados.get("metadata") or {}

    # Manifesto: shared/ referenciados existem?
    manifest = ler_manifest(skill_dir)
    for tipo in ("references", "assets"):
        for nome in (manifest.get("shared", {}) or {}).get(tipo, []) or []:
            if not (SHARED / tipo / nome).exists():
                problemas.append(f"shared/{tipo}/{nome} — não existe")

    # suite_size = contagem real (arquivos do pacote, SKILL.md fora)
    real = contar_recursos(skill_dir)
    if meta.get("suite_size") != real:
        problemas.append(f"metadata.suite_size = {meta.get('suite_size')}, contagem real = {real}")

    # CHANGELOG.md da skill acompanha a versão
    topo = versao_changelog(skill_dir)
    versao = str(meta.get("version", "")).strip()
    if versao and topo != versao:
        problemas.append(f"CHANGELOG.md: última entrada [{topo}] ≠ metadata.version {versao}")

    problemas += procurar_clientes(skill_dir)
    return problemas


def verificar_marketplace(marketplace: Path) -> list[str]:
    """marketplace.yml lista todas as skills com a mesma versão do SKILL.md."""
    if not marketplace.exists():
        return [f"{marketplace.name} não encontrado"]
    try:
        dados = yaml.safe_load(marketplace.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as e:
        return [f"{marketplace.name}: YAML inválido ({str(e).splitlines()[0]})"]
    no_marketplace = {s.get("name"): str(s.get("version")) for s in dados.get("skills", []) or []}
    problemas: list[str] = []
    for skill_dir in sorted(d for d in SKILLS.iterdir() if d.is_dir()):
        fm, erro = ler_frontmatter(skill_dir)
        if erro:
            continue
        versao = str((fm.get("metadata") or {}).get("version"))
        if skill_dir.name not in no_marketplace:
            problemas.append(f"{skill_dir.name} ausente do {marketplace.name}")
        elif no_marketplace[skill_dir.name] != versao:
            problemas.append(f"{marketplace.name}: {skill_dir.name} {no_marketplace[skill_dir.name]} "
                             f"≠ SKILL.md {versao}")
    return problemas


# ─── Ponto de entrada ─────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build e empacotamento das oracle-skills-ptbr"
    )
    parser.add_argument("--skill", default=None,
                        help="Empacotar apenas esta skill (ex: oracle-dba-ptbr)")
    parser.add_argument("--check", action="store_true",
                        help="Verificar consistência sem empacotar")
    parser.add_argument("--checksums", action="store_true",
                        help="Gerar dist/checksums.sha256")
    args = parser.parse_args()

    log(f"\n{B}{'═'*55}{Z}")
    log(f"{B}  oracle-skills-ptbr — build.py{Z}")
    log(f"{B}  M&S do Brasil LTDA — contato@msbrasil.inf.br{Z}")
    log(f"{B}{'═'*55}{Z}\n")

    # Descobrir skills
    if args.skill:
        skill_dirs = [SKILLS / args.skill]
        if not skill_dirs[0].exists():
            err(f"Skill não encontrada: {args.skill}")
            sys.exit(1)
    else:
        skill_dirs = sorted(d for d in SKILLS.iterdir() if d.is_dir())

    # ── Modo verificação ──────────────────────────────────────────────────────
    if args.check:
        log("  Verificando consistência...\n")
        total_ok = total_err = 0
        for skill_dir in skill_dirs:
            problemas = verificar(skill_dir)
            if problemas:
                err(skill_dir.name)
                for p in problemas:
                    log(f"    → {p}")
                total_err += 1
            else:
                ok(skill_dir.name)
                total_ok += 1
        if not args.skill:
            problemas_mk = verificar_marketplace(ROOT / "marketplace.yml")
            if problemas_mk:
                err("marketplace.yml")
                for p in problemas_mk:
                    log(f"    → {p}")
                total_err += 1
            else:
                ok("marketplace.yml")
        sep()
        log(f"  {G}OK: {total_ok}{Z}  |  {R}Erros: {total_err}{Z}\n")
        sys.exit(1 if total_err else 0)

    # ── Modo checksums ────────────────────────────────────────────────────────
    if args.checksums:
        log("  Gerando checksums...\n")
        f = gerar_checksums()
        ok(f"Checksums → {f}")
        return

    # ── Modo build ────────────────────────────────────────────────────────────
    log("  Empacotando skills...\n")
    if BUILD_TMP.exists():
        shutil.rmtree(BUILD_TMP)

    total_ok = total_err = 0
    for skill_dir in skill_dirs:
        log(f"  {C}{skill_dir.name}{Z}")
        skill_file = empacotar_skill(skill_dir)
        if skill_file:
            size_kb = skill_file.stat().st_size / 1024
            ok(f"{skill_file.name} ({size_kb:.1f} KB)")
            total_ok += 1
        else:
            total_err += 1
        log("")

    # Limpar tmp
    if BUILD_TMP.exists():
        shutil.rmtree(BUILD_TMP)

    # Checksums automáticos após build
    sep()
    log("  Gerando checksums...\n")
    gerar_checksums()

    sep()
    log(f"\n{B}  Build concluído:{Z} {G}{total_ok} skills{Z}", )
    if total_err:
        log(f"  {R}{total_err} com erro{Z}")
        sys.exit(1)
    log("\n  dist/ pronto para GitHub Release.\n")


if __name__ == "__main__":
    main()
