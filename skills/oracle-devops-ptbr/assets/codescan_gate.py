#!/usr/bin/env python3
"""
codescan_gate.py — Gate de CI com o SQLcl CodeScan (SQL, PL/SQL e APEXlang .apx)
M&S do Brasil LTDA — contato@msbrasil.inf.br

Uso:
    python codescan_gate.py db apex                      # falha se houver achado
    python codescan_gate.py db --settings codescan.json  # ignora o que o JSON listar
    python codescan_gate.py apex --relatorio codescan.md --formato markdown

Por que um script em volta do SQLcl:
    'codescan' devolve código de saída 0 mesmo quando encontra violações
    (verificado no SQLcl 26.3.1). Este gate lê o relatório JSON e sai com:
        0 = nenhum achado (fora os ignorados pelo --settings)
        1 = há achados
        2 = erro ao executar o SQLcl / relatório ausente

Requisitos:
    - SQLcl 26.3.0+ para as regras de APEXlang (.apx); antes disso o codescan
      já analisava .sql/.pks/.pkb/... (regras G-*, Trivadis).
      Fonte: SQLcl changelog, "26.3.0 - Sep 2026 ... Codescan now offers 30+
      rules to check code quality for APEXLang (.apx) files".
    - Arquivos analisados (help do SQLcl 26.3.1): .sql, .pks, .pkb, .pkh, .pls,
      .plb, .pck, .tps, .tpb, .apx.
    - Não precisa de conexão com banco.

Para ignorar regras ou achados específicos, use um JSON de settings do
próprio codescan, por exemplo:
    {"ignore":[{"ruleNo":"G-7310"},
               {"ruleNo":"G-1010","file":"pages/p00005-sales.apx"}]}
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from oracle_devops_utils import (  # noqa: E402
    GREEN,
    RED,
    RESET,
    YELLOW,
    ErroSQLcl,
    localizar_sqlcl,
    log,
)


def _citar(caminho: Path) -> str:
    """Caminho entre aspas simples para o SQLcl (aspas internas recusadas)."""
    texto = str(caminho)
    if "'" in texto:
        raise ErroSQLcl(f"Caminho com aspas simples não é suportado: {texto}")
    return f"'{texto}'"


def executar_codescan(pasta: Path, *, settings: Path | None = None,
                      formato: str = "json", saida: Path) -> str:
    """Roda 'codescan -path' numa pasta e grava o relatório em 'saida'."""
    sqlcl = localizar_sqlcl()
    comando = f"codescan -path {_citar(pasta.resolve())} -format {formato} -output {_citar(saida)}"
    if settings:
        comando += f" -settings {_citar(settings.resolve())}"
    proc = subprocess.run(
        [sqlcl, "-S", "/nolog"], input=comando + "\nexit\n", text=True,
        capture_output=True, check=False, env={**os.environ, "TERM": "dumb"},
    )
    texto = (proc.stdout or "") + (proc.stderr or "")
    if proc.returncode != 0 or not saida.exists():
        raise ErroSQLcl(f"codescan falhou em {pasta} (código {proc.returncode}): "
                        + "\n".join(texto.strip().splitlines()[-5:]))
    return texto


def ler_achados(relatorio: Path) -> list[dict]:
    """Achados do relatório JSON do codescan: [{file, line, col, ruleNo, msg}]."""
    dados = json.loads(relatorio.read_text(encoding="utf-8") or "[]")
    achados: list[dict] = []
    for arquivo in dados:
        for issue in arquivo.get("issues", []):
            achados.append({"file": arquivo.get("file", "?"), **issue})
    return achados


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Gate de CI com SQLcl CodeScan")
    parser.add_argument("pastas", nargs="+", type=Path,
                        help="Pastas a analisar (ex.: db apex ords)")
    parser.add_argument("--settings", type=Path,
                        help="JSON de settings do codescan (lista 'ignore')")
    parser.add_argument("--relatorio", type=Path,
                        help="Grava também um relatório legível (markdown/text)")
    parser.add_argument("--formato", choices=["markdown", "text"], default="markdown")
    args = parser.parse_args(argv)

    total: list[dict] = []
    try:
        with tempfile.TemporaryDirectory(prefix="codescan_") as tmp:
            for i, pasta in enumerate(args.pastas):
                if not pasta.is_dir():
                    log.info(f"  {YELLOW}{pasta}/ não existe — pulando{RESET}")
                    continue
                relatorio = Path(tmp) / f"codescan_{i}.json"
                executar_codescan(pasta, settings=args.settings, saida=relatorio)
                achados = ler_achados(relatorio)
                for a in achados:
                    a["file"] = str(pasta / a["file"]) if not a["file"].startswith(str(pasta)) else a["file"]
                total += achados
                if args.relatorio:
                    legivel = Path(tmp) / f"codescan_{i}.{args.formato}"
                    executar_codescan(pasta, settings=args.settings,
                                      formato=args.formato, saida=legivel)
                    with args.relatorio.open("a", encoding="utf-8") as f:
                        f.write(legivel.read_text(encoding="utf-8"))
    except (ErroSQLcl, json.JSONDecodeError) as e:
        log.error(f"{RED}✗ {e}{RESET}")
        return 2

    for a in total:
        log.info(f"  {a['file']}:{a.get('line', '?')}:{a.get('col', '?')} "
                 f"{a.get('ruleNo', '?')} {a.get('msg', '')}")
    if total:
        regras = sorted({a.get("ruleNo", "?") for a in total})
        log.error(f"{RED}✗ CodeScan: {len(total)} achado(s) — regras: {', '.join(regras)}{RESET}")
        log.error("  Corrija, ou registre a exceção no JSON de --settings (com 'reason').")
        return 1
    log.info(f"{GREEN}✓ CodeScan sem achados{RESET}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
