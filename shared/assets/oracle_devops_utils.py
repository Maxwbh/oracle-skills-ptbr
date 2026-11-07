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
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from datetime import datetime
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


# Identificador Oracle sem aspas (usuário, schema). Aceita proxy: usuario[alvo].
_RE_IDENT = re.compile(r"[A-Za-z][A-Za-z0-9_$#]{0,127}(\[[A-Za-z][A-Za-z0-9_$#]{0,127}\])?")


def obter_config_db() -> dict:
    """
    Lê configuração do banco das variáveis de ambiente. Falha com mensagem clara.

    DB_SCHEMA (opcional) é o schema alvo do deploy; padrão = DB_USER.
    """
    obrigatorios = ["DB_HOST", "DB_PORT", "DB_SERVICE", "DB_USER", "DB_PASS"]
    ausentes = [v for v in obrigatorios if not os.environ.get(v)]
    if ausentes:
        log.error(f"{RED}Variáveis não definidas: {', '.join(ausentes)}{RESET}")
        log.error("Configure .env ou exporte as variáveis antes de executar.")
        sys.exit(1)
    usuario = os.environ["DB_USER"]
    schema = os.environ.get("DB_SCHEMA") or usuario
    for nome, valor in (("DB_USER", usuario), ("DB_SCHEMA", schema)):
        if not _RE_IDENT.fullmatch(valor):
            log.error(f"{RED}{nome}='{valor}' não é um identificador Oracle simples.{RESET}")
            sys.exit(1)
    return {
        "host":     os.environ["DB_HOST"],
        "port":     int(os.environ.get("DB_PORT", "1521")),
        "service":  os.environ["DB_SERVICE"],
        "user":     usuario,
        "password": os.environ["DB_PASS"],
        "schema":   schema,
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
    if schema.upper() != cfg["user"].split("[")[0].upper():
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
        conteudo = arquivo.read_text(encoding="utf-8")
    except UnicodeDecodeError as e:
        return [f"{arquivo.name}: não é UTF-8 (byte {e.start})"]
    try:
        split_oracle_sql(conteudo, permitir_cliente=True)
    except ErroParserSQL as e:
        return [f"{arquivo.name}: {e}"]
    return []


# ─── Execução de scripts pelo SQLcl ───────────────────────────────────────────
#
# Scripts de deploy (DDL, PL/SQL, migrations, install.sql do APEX) rodam pelo
# SQLcl, que entende SET, PROMPT, @, @@ e as regras de terminador. O
# python-oracledb fica para controle (db_changelog, verificações, ALL_ERRORS).
#
# Comportamentos verificados em container (Oracle Free + SQLcl 26.3):
# - credencial inválida no CONNECT dispara WHENEVER SQLERROR (exit != 0);
# - 'WHENEVER SQLERROR EXIT FAILURE' sem ROLLBACK COMITA o DML parcial
#   (o padrão do EXIT é COMMIT) — por isso usamos EXIT FAILURE ROLLBACK;
# - CREATE de PL/SQL com erro de compilação NÃO dispara WHENEVER SQLERROR
#   (sai com 0) — por isso verificar_erros_compilacao() após o script;
# - no python-oracledb, o mesmo CREATE também não lança exceção: só
#   preenche cursor.warning (DPY-7000).

class ErroSQLcl(RuntimeError):
    """Falha ao executar script pelo SQLcl (ou erro de compilação após ele)."""

    def __init__(self, mensagem: str, *, statement: str = "", erro_oracle: str = "",
                 saida: str = "", codigo: Optional[int] = None) -> None:
        super().__init__(mensagem)
        self.statement = statement
        self.erro_oracle = erro_oracle
        self.saida = saida
        self.codigo = codigo


def localizar_sqlcl() -> str:
    """Caminho do executável do SQLcl (SQLCL_BIN ou 'sql' no PATH)."""
    caminho = os.environ.get("SQLCL_BIN") or shutil.which("sql")
    if not caminho:
        raise ErroSQLcl(
            "SQLcl não encontrado: instale o SQLcl e coloque 'sql' no PATH "
            "(ou defina SQLCL_BIN). Download: "
            "https://www.oracle.com/database/sqldeveloper/technologies/sqlcl/download/"
        )
    return caminho


def montar_script_sqlcl(arquivo: Path, cfg: dict,
                        preambulo: Optional[list[str]] = None) -> str:
    """
    Script enviado ao SQLcl pela entrada padrão (a senha nunca vai na linha
    de comando, onde ficaria visível em 'ps').
    """
    if '"' in cfg["password"]:
        raise ErroSQLcl('DB_PASS não pode conter aspas duplas (") para uso no SQLcl.')
    usuario = cfg["user"]
    schema = cfg.get("schema") or usuario
    if not _RE_IDENT.fullmatch(usuario) or not _RE_IDENT.fullmatch(schema):
        raise ErroSQLcl("DB_USER/DB_SCHEMA inválido.")
    dsn = f"//{cfg['host']}:{cfg['port']}/{cfg['service']}"
    linhas = [
        "WHENEVER SQLERROR EXIT FAILURE ROLLBACK",
        "WHENEVER OSERROR EXIT FAILURE ROLLBACK",
        "SET DEFINE OFF",
        "SET VERIFY OFF",
        "SET FEEDBACK ON",
        "SET SERVEROUTPUT ON SIZE UNLIMITED",
        f'CONNECT {usuario}/"{cfg["password"]}"@{dsn}',
    ]
    if schema.upper() != usuario.split("[")[0].upper():
        linhas.append(f"ALTER SESSION SET CURRENT_SCHEMA = {schema.upper()};")
    linhas += list(preambulo or [])
    linhas.append(f'@"{arquivo}"')
    linhas.append("EXIT SUCCESS COMMIT")
    return "\n".join(linhas) + "\n"


_RE_ERRO_SQLCL = re.compile(
    r"Error starting at line : \d+[^\n]*\n(?:In command -\n)?(?P<stmt>.*?)\n"
    r"(?:Error at Command Line[^\n]*\n)?Error report -\n(?P<erro>.*?)(?:\n\n|\Z)",
    re.DOTALL,
)


_RE_LINHA_ERRO = re.compile(r"^(ORA|PLS|SP2|SQL Error: ORA)-?\d*", re.MULTILINE)


def extrair_erro_sqlcl(saida: str) -> tuple[str, str]:
    """
    (statement, erro) do último erro na saída do SQLcl. Reconhece os dois
    formatos que o SQLcl usa:
      "Error starting at line : N ... Error report -\nORA-..."   e
      "<statement>\n*\nERROR at line N:\nORA-..."   (ex.: CREATE TRIGGER)
    """
    achados = list(_RE_ERRO_SQLCL.finditer(saida))
    pos_formato2 = saida.rfind("\nERROR at line ")
    if achados and achados[-1].start() > pos_formato2:
        m = achados[-1]
        return m.group("stmt").strip(), m.group("erro").strip()
    if pos_formato2 != -1:
        antes = saida[:pos_formato2].splitlines()
        if antes and antes[-1].strip() == "*":
            antes = antes[:-1]
        stmt: list[str] = []
        for linha in reversed(antes):
            if not linha.strip() or linha.strip() == "Rollback":
                break
            stmt.insert(0, linha)
        depois = saida[pos_formato2 + 1:].splitlines()[1:]
        erro: list[str] = []
        for linha in depois:
            if not linha.strip():
                break
            erro.append(linha)
        return "\n".join(stmt).strip(), "\n".join(erro).strip()
    return "", "\n".join(saida.strip().splitlines()[-8:])


def resumo_erro(erro: str) -> str:
    """Primeira linha com código de erro (ORA-/PLS-/SP2-), ou a primeira linha."""
    m = _RE_LINHA_ERRO.search(erro)
    if m:
        return erro[m.start():].splitlines()[0]
    return erro.splitlines()[0] if erro else "sem mensagem"


def executar_script_sqlcl(
    arquivo: Path,
    cfg: Optional[dict] = None,
    *,
    cwd: Optional[Path] = None,
    preambulo: Optional[list[str]] = None,
    timeout: Optional[int] = None,
    verbose: bool = True,
) -> str:
    """
    Executa um script pelo SQLcl (sql -S /nolog) com
    WHENEVER SQLERROR/OSERROR EXIT FAILURE ROLLBACK e checa o código de saída.

    - cwd: pasta de trabalho (para '@@' relativo; no APEX, a pasta do app).
    - preambulo: comandos extras antes do '@arquivo' (ex.: apex_application_install).
    Retorna a saída. Lança ErroSQLcl com statement e erro Oracle se falhar.
    Erro de compilação de PL/SQL NÃO é detectado aqui: use
    executar_e_verificar() ou verificar_erros_compilacao().
    """
    if not arquivo.exists():
        raise ErroSQLcl(f"Arquivo SQL não encontrado: {arquivo}")
    problemas = validar_arquivo_sql(arquivo)
    if problemas:
        raise ErroSQLcl("Pré-validação falhou: " + "; ".join(problemas))

    cfg = cfg or obter_config_db()
    sqlcl = localizar_sqlcl()
    script = montar_script_sqlcl(arquivo.resolve(), cfg, preambulo)

    try:
        proc = subprocess.run(
            [sqlcl, "-S", "/nolog"],
            input=script, text=True, capture_output=True, check=False,
            cwd=str(cwd or arquivo.parent), timeout=timeout,
            env={**os.environ, "TERM": "dumb"},
        )
    except subprocess.TimeoutExpired as e:
        raise ErroSQLcl(f"SQLcl excedeu {timeout}s em {arquivo.name}") from e

    saida = (proc.stdout or "") + (proc.stderr or "")
    if verbose and saida.strip():
        for linha in saida.rstrip().splitlines():
            if not linha.startswith("Picked up JAVA_TOOL_OPTIONS"):
                log.info(f"    {DIM}│{RESET} {linha}")
    if proc.returncode != 0:
        stmt, erro = extrair_erro_sqlcl(saida)
        primeira = resumo_erro(erro)
        raise ErroSQLcl(
            f"SQLcl terminou com código {proc.returncode} em {arquivo.name}: {primeira}",
            statement=stmt, erro_oracle=erro, saida=saida, codigo=proc.returncode,
        )
    return saida


# ─── Erros de compilação de PL/SQL ────────────────────────────────────────────

def data_hora_banco(conn: oracledb.Connection) -> datetime:
    """SYSDATE do banco — marco para achar objetos compilados neste deploy."""
    with conn.cursor() as cur:
        cur.execute("SELECT SYSDATE FROM dual")
        return cur.fetchone()[0]


SQL_ERROS_COMPILACAO = """
SELECT e.name, e.type, e.line, e.position, e.text
  FROM all_errors e
  JOIN all_objects o
    ON o.owner       = e.owner
   AND o.object_name = e.name
   AND o.object_type = e.type
 WHERE e.owner = SYS_CONTEXT('USERENV', 'CURRENT_SCHEMA')
   AND e.attribute = 'ERROR'
   AND o.last_ddl_time >= :desde
 ORDER BY e.name, e.type, e.sequence
"""


def verificar_erros_compilacao(conn: oracledb.Connection, desde: datetime) -> list[tuple]:
    """
    Erros de compilação (ALL_ERRORS, owner = CURRENT_SCHEMA) dos objetos
    criados/recompilados a partir de 'desde'. Lista vazia = OK.

    Filtrar por LAST_DDL_TIME evita que objetos inválidos pré-existentes, que
    não foram tocados pelo deploy, bloqueiem a entrega.
    """
    with conn.cursor() as cur:
        cur.execute(SQL_ERROS_COMPILACAO, desde=desde)
        return cur.fetchall()


def formatar_erros_compilacao(erros: list[tuple]) -> str:
    return "\n".join(f"  {tipo} {nome} [{lin}/{col}]: {texto.strip()}"
                     for nome, tipo, lin, col, texto in erros)


def executar_e_verificar(
    conn: oracledb.Connection,
    arquivo: Path,
    cfg: Optional[dict] = None,
    **kwargs,
) -> str:
    """
    executar_script_sqlcl + verificar_erros_compilacao. Lança ErroSQLcl se o
    script falhar ou se algum objeto ficar com erro de compilação.
    'conn' deve estar no mesmo schema alvo (conectar() já faz o ALTER SESSION).
    """
    desde = data_hora_banco(conn)
    saida = executar_script_sqlcl(arquivo, cfg, **kwargs)
    erros = verificar_erros_compilacao(conn, desde)
    if erros:
        detalhe = formatar_erros_compilacao(erros)
        raise ErroSQLcl(
            f"{arquivo.name}: {len(erros)} erro(s) de compilação em ALL_ERRORS:\n{detalhe}",
            statement=f"{erros[0][1]} {erros[0][0]}", erro_oracle=detalhe, saida=saida,
        )
    return saida


def executar_lote_sqlcl(
    conn: oracledb.Connection,
    arquivos: list[Path],
    cfg: dict | None = None,
    *,
    base: Path | None = None,
    **kwargs,
) -> None:
    """
    Executa vários scripts numa única sessão do SQLcl (um script mestre com
    PROMPT + @arquivo para cada um, na ordem dada) e depois verifica ALL_ERRORS.

    Todos os arquivos são pré-validados ANTES de qualquer execução: um arquivo
    malformado no fim da lista não deixa metade do lote aplicado.
    Para no primeiro erro (WHENEVER SQLERROR EXIT FAILURE ROLLBACK).
    """
    if not arquivos:
        return
    problemas = [p for a in arquivos for p in validar_arquivo_sql(a)]
    if problemas:
        raise ErroSQLcl("Pré-validação falhou:\n  " + "\n  ".join(problemas))
    with tempfile.TemporaryDirectory(prefix="deploy_") as tmp:
        mestre = Path(tmp) / "lote.sql"
        linhas = []
        for a in arquivos:
            nome = a.relative_to(base) if base else a.name
            linhas.append(f"PROMPT >> {nome}")
            linhas.append(f'@"{a.resolve()}"')
        mestre.write_text("\n".join(linhas) + "\n", encoding="utf-8")
        executar_e_verificar(conn, mestre, cfg, cwd=kwargs.pop("cwd", base), **kwargs)


# ─── Utilitários ──────────────────────────────────────────────────────────────

def checksum_sha256(arquivo: Path) -> str:
    """Calcula SHA-256 do arquivo."""
    sha = hashlib.sha256()
    sha.update(arquivo.read_bytes())
    return sha.hexdigest()


def _em_ci() -> bool:
    return os.environ.get("CI", "").strip().lower() in ("1", "true", "yes")


def confirmar_producao(dry_run: bool = False, *, confirmado: bool = False) -> None:
    """
    Exige confirmação explícita antes de deploy em produção.

    - Com --confirmar-prod (confirmado=True) ou CONFIRMO_PROD=1: segue.
    - Fora de TTY ou com CI=true: NUNCA chama input() — sem confirmação
      explícita, aborta com código 2. No pipeline, a aprovação humana vem do
      GitHub Environment 'prod' (required reviewers), e o job passa
      --confirmar-prod.
    - Em terminal interativo: pede 'CONFIRMO PROD'.
    """
    if dry_run:
        return
    log.info(f"\n{RED}{BOLD}⚠  DEPLOY EM PRODUÇÃO{RESET}")
    if confirmado or os.environ.get("CONFIRMO_PROD") == "1":
        origem = "--confirmar-prod" if confirmado else "CONFIRMO_PROD=1"
        log.info(f"  Confirmado por {origem}.\n")
        return
    if _em_ci() or not sys.stdin.isatty():
        log.error(f"{RED}Deploy em produção sem confirmação explícita em modo "
                  f"não interativo (CI ou sem TTY).{RESET}")
        log.error("Use --confirmar-prod ou CONFIRMO_PROD=1 (no pipeline, após a "
                  "aprovação do Environment 'prod').")
        sys.exit(2)
    confirmacao = input("  Digite 'CONFIRMO PROD' para continuar: ").strip()
    if confirmacao != "CONFIRMO PROD":
        log.info("Deploy cancelado.")
        sys.exit(1)
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
