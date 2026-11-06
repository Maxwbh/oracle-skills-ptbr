"""
oracle_devops_utils.py — Utilitários compartilhados para scripts DevOps Oracle
M&S do Brasil LTDA — contato@msbrasil.inf.br

Importado por todos os scripts Python do projeto:
    from oracle_devops_utils import conectar, executar_arquivo_sql, log, ...
"""

from __future__ import annotations

import hashlib
import logging
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import oracledb

# ─── Logging ──────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("oracle_devops")

# ─── Cores para terminal ──────────────────────────────────────────────────────

_TTY = sys.stdout.isatty()
GREEN  = "\033[92m" if _TTY else ""
YELLOW = "\033[93m" if _TTY else ""
RED    = "\033[91m" if _TTY else ""
CYAN   = "\033[96m" if _TTY else ""
BOLD   = "\033[1m"  if _TTY else ""
RESET  = "\033[0m"  if _TTY else ""
DIM    = "\033[2m"  if _TTY else ""

SEP    = f"{DIM}{'─' * 55}{RESET}"
SEP2   = f"{BOLD}{'═' * 55}{RESET}"

# ─── Variáveis de ambiente ────────────────────────────────────────────────────

def carregar_dotenv(root: Path) -> None:
    """Carrega .env sem dependência de python-dotenv."""
    env_file = root / ".env"
    if not env_file.exists():
        return
    for linha in env_file.read_text(encoding="utf-8").splitlines():
        linha = linha.strip()
        if not linha or linha.startswith("#") or "=" not in linha:
            continue
        chave, _, valor = linha.partition("=")
        os.environ.setdefault(chave.strip(), valor.strip().strip('"').strip("'"))


def obter_config_db() -> dict:
    """Lê configuração do banco das variáveis de ambiente. Falha com mensagem clara."""
    obrigatorios = ["DB_HOST", "DB_PORT", "DB_SERVICE", "DB_USER", "DB_PASS"]
    ausentes = [v for v in obrigatorios if not os.environ.get(v)]
    if ausentes:
        log.error(f"{RED}Variáveis não definidas: {', '.join(ausentes)}{RESET}")
        log.error("Configure .env ou exporte as variáveis antes de executar.")
        sys.exit(1)
    return {
        "host":     os.environ["DB_HOST"],
        "port":     int(os.environ.get("DB_PORT", "1521")),
        "service":  os.environ["DB_SERVICE"],
        "user":     os.environ["DB_USER"],
        "password": os.environ["DB_PASS"],
    }


# ─── Conexão Oracle ───────────────────────────────────────────────────────────

def conectar(cfg: Optional[dict] = None) -> oracledb.Connection:
    """
    Conecta ao Oracle usando Thin Mode (sem Oracle Client).
    Se cfg for None, lê de obter_config_db().

    Quando DB_SCHEMA != DB_USER (deploy em schema diferente do usuário de conexão),
    executa ALTER SESSION SET CURRENT_SCHEMA automaticamente após conectar.
    Isso garante que USER_* views e objetos sem prefixo de schema apontem
    para o schema correto, sem necessidade de prefixar cada DDL/DML.
    """
    cfg = cfg or obter_config_db()
    dsn = f"{cfg['host']}:{cfg['port']}/{cfg['service']}"
    schema = cfg.get("schema", cfg["user"])

    try:
        conn = oracledb.connect(user=cfg["user"], password=cfg["password"], dsn=dsn)
    except oracledb.DatabaseError as e:
        log.error(f"{RED}Falha na conexão Oracle: {e}{RESET}")
        sys.exit(1)

    # Mudar para o schema alvo se diferente do usuário de conexão
    if schema.upper() != cfg["user"].upper():
        try:
            with conn.cursor() as cur:
                cur.execute(f"ALTER SESSION SET CURRENT_SCHEMA = {schema.upper()}")
            log.info(f"Conectado: {CYAN}{cfg['user']}@{dsn}{RESET}  "
                     f"→ schema alvo: {CYAN}{schema.upper()}{RESET}")
        except oracledb.DatabaseError as e:
            log.error(f"{RED}Falha ao definir CURRENT_SCHEMA={schema.upper()}: {e}{RESET}")
            log.error("Verifique se o usuário tem CREATE SESSION no schema alvo.")
            conn.close()
            sys.exit(1)
    else:
        log.info(f"Conectado: {CYAN}{cfg['user']}@{dsn}{RESET}")

    return conn


def schema_efetivo(conn: oracledb.Connection) -> str:
    """Retorna o CURRENT_SCHEMA efetivo da sessão (após ALTER SESSION, se aplicado)."""
    with conn.cursor() as cur:
        cur.execute("SELECT SYS_CONTEXT('USERENV', 'CURRENT_SCHEMA') FROM dual")
        return cur.fetchone()[0]


# ─── Parser de arquivo SQL Oracle ─────────────────────────────────────────────
#
# Scripts (DDL, PL/SQL, install.sql do APEX) são EXECUTADOS pelo SQLcl
# (ver executar_script_sqlcl). O parser abaixo serve para:
#   - pré-validar o arquivo antes de chamar o SQLcl (literal/comentário não
#     fechado, último comando sem terminador — que o SQLcl ignoraria em
#     silêncio);
#   - dividir em statements quando algum código precisar executar SQL pelo
#     python-oracledb, rejeitando comandos de cliente de forma explícita.
#
# É um tokenizador de verdade (sem regex sobre o texto inteiro): reconhece
# literais '...' (com '' escapado), q'[...]' / nq'[...]', identificadores
# "...", comentários -- e /* */. Nada dentro de literal é alterado.

class ErroParserSQL(ValueError):
    """Arquivo SQL que não pode ser dividido/executado com segurança."""


@dataclass
class ComandoSQL:
    texto: str
    tipo: str          # 'sql' | 'plsql' | 'cliente'
    linha: int         # linha (1-based) onde o comando começa
    terminado: bool    # tinha ';' ou '/' (ou é comando de cliente)


# Primeira palavra de comandos SQL*Plus/SQLcl que não são SQL.
_PALAVRAS_CLIENTE = frozenset("""
    ACCEPT ALIAS APEX BREAK BTITLE CD CLEAR COL COLUMN COMPUTE CONN CONNECT
    COPY CTAS DDL DEF DEFINE DESC DESCRIBE DISC DISCONNECT EDIT EXEC EXECUTE
    EXIT FORMAT GET HISTORY HOST INFO LB LIQUIBASE LOAD OERR PAUSE PRINT PRO
    PROMPT QUIT REM REMARK REPEAT SAVE SCRIPT SET SHO SHOW SODA SPO SPOOL
    START STORE TIMING TTITLE UNDEF UNDEFINE VAR VARIABLE WHENEVER
""".split())

# "SET <x>" que é SQL de verdade, não comando de cliente.
_SET_SQL = frozenset({"TRANSACTION", "ROLE", "CONSTRAINT", "CONSTRAINTS"})

# Comandos que o SQL*Plus/SQLcl trata como bloco PL/SQL (terminam só com '/').
_RE_PLSQL = re.compile(
    r"(BEGIN|DECLARE)\b"
    r"|CREATE\s+(OR\s+REPLACE\s+)?((NON)?EDITIONABLE\s+)?"
    r"(PACKAGE|PROCEDURE|FUNCTION|TRIGGER|TYPE|LIBRARY|JAVA)\b"
    r"|CREATE\s+(OR\s+REPLACE\s+)?AND\s+(COMPILE|RESOLVE)\s+JAVA\b"
    r"|WITH\s+(FUNCTION|PROCEDURE)\b",
    re.IGNORECASE,
)

_Q_FECHA = {"[": "]", "{": "}", "<": ">", "(": ")"}


def _eh_comando_cliente(linha: str) -> bool:
    s = linha.strip()
    if not s:
        return False
    if s[0] in "@!":
        return True
    partes = s.split(None, 2)
    palavra = partes[0].upper().rstrip(";")
    if palavra == "SET":
        return not (len(partes) > 1 and partes[1].upper().rstrip(";") in _SET_SQL)
    return palavra in _PALAVRAS_CLIENTE


def _eh_ident(c: str) -> bool:
    return c.isalnum() or c in "_$#"


def analisar_sql(conteudo: str) -> list[ComandoSQL]:
    """
    Tokeniza um script SQL*Plus/SQLcl e devolve a lista de comandos, na ordem.

    Regras (as mesmas do SQL*Plus/SQLcl):
    - SQL termina em ';' fora de literal/comentário, ou em '/' sozinho na linha;
    - PL/SQL (BEGIN, DECLARE, CREATE PACKAGE/PROCEDURE/FUNCTION/TRIGGER/TYPE...)
      termina só em '/' sozinho na linha; o ';' final (END;) é preservado;
    - comando de cliente (SET, PROMPT, WHENEVER, @, @@, ...) ocupa a linha
      inteira e nunca é anexado ao statement seguinte;
    - comentários dentro de um statement são preservados (vão para o fonte do
      PL/SQL); comentários entre statements são descartados.

    Lança ErroParserSQL para literal, identificador ou comentário não fechado.
    """
    t = conteudo.replace("\r\n", "\n").replace("\r", "\n")
    n = len(t)
    comandos: list[ComandoSQL] = []

    NORMAL, LIT, QLIT, IDENT, BLOCO = range(5)
    estado = NORMAL
    q_fecha = ""
    abertura = 0           # posição onde abriu literal/comentário (para erro)
    ini: Optional[int] = None
    tipo = ""
    linha_ini = 0

    def nlinha(pos: int) -> int:
        return t.count("\n", 0, pos) + 1

    def emitir(fim: int, terminado: bool) -> None:
        nonlocal ini, tipo
        texto = t[ini:fim].rstrip()
        if texto:
            comandos.append(ComandoSQL(texto, tipo, linha_ini, terminado))
        ini, tipo = None, ""

    i = 0
    while i < n:
        # Tratamento por linha: '/' sozinho e comandos de cliente.
        if estado == NORMAL and (i == 0 or t[i - 1] == "\n"):
            fim_linha = t.find("\n", i)
            fim_linha = n if fim_linha == -1 else fim_linha
            linha = t[i:fim_linha]
            if linha.strip() == "/":
                if ini is not None:
                    emitir(i, terminado=True)
                i = fim_linha + 1
                continue
            if ini is None and _eh_comando_cliente(linha):
                comandos.append(ComandoSQL(linha.strip(), "cliente", nlinha(i), True))
                i = fim_linha + 1
                continue

        c = t[i]
        prox = t[i + 1] if i + 1 < n else ""

        if estado == BLOCO:
            if c == "*" and prox == "/":
                estado = NORMAL
                i += 2
            else:
                i += 1
            continue
        if estado == LIT:
            if c == "'":
                if prox == "'":
                    i += 2
                    continue
                estado = NORMAL
            i += 1
            continue
        if estado == QLIT:
            if c == q_fecha and prox == "'":
                estado = NORMAL
                i += 2
            else:
                i += 1
            continue
        if estado == IDENT:
            if c == '"':
                estado = NORMAL
            i += 1
            continue

        # estado NORMAL
        if c == "-" and prox == "-":
            fim_linha = t.find("\n", i)
            i = n if fim_linha == -1 else fim_linha
            continue
        if c == "/" and prox == "*":
            estado, abertura = BLOCO, i
            i += 2
            continue
        if c.isspace():
            i += 1
            continue

        if ini is None:
            ini, linha_ini = i, nlinha(i)
            tipo = "plsql" if _RE_PLSQL.match(t, i) else "sql"

        if c in "qQ" and prox == "'" and i + 2 < n:
            anterior = t[i - 1] if i > 0 else ""
            antes2 = t[i - 2] if i > 1 else ""
            if not _eh_ident(anterior) or (anterior in "nN" and not _eh_ident(antes2)):
                q_fecha = _Q_FECHA.get(t[i + 2], t[i + 2])
                estado, abertura = QLIT, i
                i += 3
                continue
        if c == "'":
            estado, abertura = LIT, i
        elif c == '"':
            estado, abertura = IDENT, i
        elif c == ";" and tipo == "sql":
            emitir(i, terminado=True)
        i += 1

    if estado != NORMAL:
        oque = {LIT: "literal", QLIT: "literal q'...'", IDENT: 'identificador "..."',
                BLOCO: "comentário /* */"}[estado]
        raise ErroParserSQL(f"linha {nlinha(abertura)}: {oque} não fechado")

    if ini is not None:
        emitir(n, terminado=False)

    return comandos


def split_oracle_sql(conteudo: str, *, permitir_cliente: bool = False) -> list[str]:
    """
    Divide um script em statements executáveis pelo python-oracledb.

    - SQL sai sem o ';' final; PL/SQL sai com o 'END;' intacto.
    - Comando de cliente (SET, PROMPT, WHENEVER, @, @@...) lança
      ErroParserSQL, a menos que permitir_cliente=True (aí é descartado).
      Script com comando de cliente deve rodar pelo SQLcl.
    - Último comando sem ';' ou '/' lança ErroParserSQL: o SQLcl não o
      executaria, e executar só no Python mascararia a diferença.
    """
    statements: list[str] = []
    for cmd in analisar_sql(conteudo):
        if cmd.tipo == "cliente":
            if permitir_cliente:
                continue
            raise ErroParserSQL(
                f"linha {cmd.linha}: comando de cliente '{cmd.texto[:40]}' não é SQL — "
                "rode este arquivo pelo SQLcl (executar_script_sqlcl)"
            )
        if not cmd.terminado:
            raise ErroParserSQL(
                f"linha {cmd.linha}: comando sem terminador ("
                + ("'/' em linha própria" if cmd.tipo == "plsql" else "';' ou '/'")
                + ") — o SQLcl não o executaria"
            )
        statements.append(cmd.texto)
    return statements


def validar_arquivo_sql(arquivo: Path) -> list[str]:
    """
    Pré-validação de um script antes de enviá-lo ao SQLcl.
    Retorna lista de problemas (vazia = OK). Comandos de cliente são aceitos.
    """
    try:
        split_oracle_sql(arquivo.read_text(encoding="utf-8"), permitir_cliente=True)
    except ErroParserSQL as e:
        return [f"{arquivo.name}: {e}"]
    return []


# ─── Utilitários ──────────────────────────────────────────────────────────────

def checksum_sha256(arquivo: Path) -> str:
    """Calcula SHA-256 do arquivo."""
    sha = hashlib.sha256()
    sha.update(arquivo.read_bytes())
    return sha.hexdigest()


def confirmar_producao(dry_run: bool = False) -> None:
    """Exige confirmação explícita antes de deploy em produção."""
    if dry_run:
        return
    log.info(f"\n{RED}{BOLD}⚠  DEPLOY EM PRODUÇÃO{RESET}")
    confirmacao = input("  Digite 'CONFIRMO PROD' para continuar: ").strip()
    if confirmacao != "CONFIRMO PROD":
        log.info("Deploy cancelado.")
        sys.exit(0)
    log.info("")


def banner(titulo: str, ambiente: str, dry_run: bool = False) -> None:
    """Exibe banner padronizado no início de cada script."""
    log.info(SEP2)
    log.info(f"{BOLD}  {titulo}{RESET}")
    log.info(f"{BOLD}  M&S do Brasil LTDA — contato@msbrasil.inf.br{RESET}")
    log.info(SEP2)
    log.info(f"  Ambiente : {CYAN}{ambiente}{RESET}")
    if dry_run:
        log.info(f"  {YELLOW}MODO DRY-RUN — sem alterações reais{RESET}")
    log.info("")
