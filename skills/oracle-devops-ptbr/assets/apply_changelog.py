#!/usr/bin/env python3
"""
apply_changelog.py — Aplica migrations pendentes do db/changelog.yml
M&S do Brasil LTDA — contato@msbrasil.inf.br

Uso:
    python apply_changelog.py [--env dev|hom|prod] [--dry-run] [--status]
    python apply_changelog.py --retomar <id>            # reexecuta a migration em ERRO/EM_ANDAMENTO
    python apply_changelog.py --marcar-resolvida <id>   # DBA corrigiu à mão; registra como APLICADA

Exemplos:
    python apply_changelog.py --env dev
    python apply_changelog.py --env prod --dry-run    # simula sem aplicar
    python apply_changelog.py --status                 # mostra estado atual

Atomicidade — o que este script garante e o que NÃO garante:
    DDL no Oracle comita implicitamente: uma migration que falha no meio
    deixa aplicado tudo o que veio antes do erro. Não existe rollback de DDL.
    Por isso cada migration é registrada em db_changelog ANTES de executar
    (status EM_ANDAMENTO) e atualizada DEPOIS (APLICADA ou ERRO, com a
    mensagem e o statement que falhou). Enquanto houver migration em ERRO ou
    EM_ANDAMENTO, novas execuções são bloqueadas até alguém decidir:
      --retomar <id>           o arquivo foi corrigido/tornado idempotente;
                               reexecuta essa migration e segue com as demais;
      --marcar-resolvida <id>  o ajuste foi feito à mão; registra como APLICADA
                               (com o checksum atual do arquivo) e para.
    DML dentro de uma migration que falha é desfeito (WHENEVER SQLERROR EXIT
    FAILURE ROLLBACK); o DDL anterior ao erro, não.
    Boas práticas no reference git-project-structure-ptbr.md (seção
    "Migrations: falha no meio e retomada").
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import yaml

# Importar utilitários compartilhados
sys.path.insert(0, str(Path(__file__).parent))
import oracledb  # noqa: E402

from oracle_devops_utils import (  # noqa: E402
    BOLD,
    CYAN,
    GREEN,
    RED,
    RESET,
    SEP2,
    YELLOW,
    ErroSQLcl,
    banner,
    carregar_dotenv,
    checksum_sha256,
    conectar,
    confirmar_producao,
    executar_e_verificar,
    log,
    obter_config_db,
)

# ─── Estados ──────────────────────────────────────────────────────────────────

EM_ANDAMENTO = "EM_ANDAMENTO"
APLICADA = "APLICADA"
ERRO = "ERRO"
PENDENCIAS = (ERRO, EM_ANDAMENTO)

# Limite seguro para VARCHAR2(4000 BYTE) com texto multibyte (UTF-8).
_MAX_TEXTO = 1300


# ─── Estruturas de dados ──────────────────────────────────────────────────────

@dataclass
class Migration:
    id: str
    arquivo: str
    tipo: str
    descricao: str


@dataclass
class Registro:
    """Linha de db_changelog."""
    id: str
    status: str
    checksum: str
    aplicado_em: object = None
    ambiente: str | None = None
    duracao_ms: int | None = None
    mensagem_erro: str | None = None
    statement_erro: str | None = None


@dataclass
class ResultadoMigration:
    migration: Migration
    status: str          # APLICADA | PULADA | ERRO | DRY_RUN
    checksum: str = ""
    duracao_ms: int = 0
    erro: str = ""


# ─── Tabela de controle ───────────────────────────────────────────────────────
#
# Bloco idempotente: cria db_changelog ou acrescenta as colunas de status a
# uma tabela de versão anterior (linhas antigas ficam como APLICADA).
# O mesmo bloco está em create-changelog-table.sql (o teste
# tests/test_apply_changelog.py garante que os dois não divergem).

DDL_CHANGELOG_TABLE = """\
DECLARE
  l_schema VARCHAR2(128) := SYS_CONTEXT('USERENV', 'CURRENT_SCHEMA');
  l_qtd    PLS_INTEGER;

  FUNCTION existe_coluna(p_coluna IN VARCHAR2) RETURN BOOLEAN IS
    l_qtd_coluna PLS_INTEGER;
  BEGIN
    SELECT COUNT(*)
      INTO l_qtd_coluna
      FROM all_tab_columns
     WHERE owner       = l_schema
       AND table_name  = 'DB_CHANGELOG'
       AND column_name = p_coluna;
    RETURN l_qtd_coluna > 0;
  END existe_coluna;
BEGIN
  -- ALL_TABLES + CURRENT_SCHEMA: funciona quando o usuário de conexão é
  -- diferente do schema alvo (DB_SCHEMA != DB_USER).
  SELECT COUNT(*)
    INTO l_qtd
    FROM all_tables
   WHERE owner      = l_schema
     AND table_name = 'DB_CHANGELOG';

  IF l_qtd = 0 THEN
    EXECUTE IMMEDIATE q'[
      CREATE TABLE db_changelog (
        id             VARCHAR2(20)   NOT NULL,
        descricao      VARCHAR2(500)  NOT NULL,
        arquivo        VARCHAR2(500)  NOT NULL,
        tipo           VARCHAR2(10)   NOT NULL,
        checksum       VARCHAR2(64)   NOT NULL,
        status         VARCHAR2(20)   NOT NULL,
        aplicado_em    DATE           DEFAULT SYSDATE NOT NULL,
        aplicado_por   VARCHAR2(128)  DEFAULT USER    NOT NULL,
        duracao_ms     NUMBER,
        ambiente       VARCHAR2(10),
        mensagem_erro  VARCHAR2(4000),
        statement_erro VARCHAR2(4000),
        CONSTRAINT pk_db_changelog PRIMARY KEY (id),
        CONSTRAINT ck_db_changelog_status
          CHECK (status IN ('EM_ANDAMENTO', 'APLICADA', 'ERRO'))
      )]';
    EXECUTE IMMEDIATE q'[COMMENT ON TABLE db_changelog IS 'Controle de migrations — gerenciado por apply_changelog.py']';
  ELSE
    IF NOT existe_coluna('STATUS') THEN
      -- Linhas existentes foram aplicadas pela versão anterior do script.
      EXECUTE IMMEDIATE q'[ALTER TABLE db_changelog ADD (status VARCHAR2(20) DEFAULT 'APLICADA' NOT NULL)]';
      -- Sem default daqui em diante: o script sempre informa o status.
      EXECUTE IMMEDIATE q'[ALTER TABLE db_changelog MODIFY (status DEFAULT NULL)]';
    END IF;
    IF NOT existe_coluna('MENSAGEM_ERRO') THEN
      EXECUTE IMMEDIATE q'[ALTER TABLE db_changelog ADD (mensagem_erro VARCHAR2(4000))]';
    END IF;
    IF NOT existe_coluna('STATEMENT_ERRO') THEN
      EXECUTE IMMEDIATE q'[ALTER TABLE db_changelog ADD (statement_erro VARCHAR2(4000))]';
    END IF;
    SELECT COUNT(*)
      INTO l_qtd
      FROM all_constraints
     WHERE owner           = l_schema
       AND table_name      = 'DB_CHANGELOG'
       AND constraint_name = 'CK_DB_CHANGELOG_STATUS';
    IF l_qtd = 0 THEN
      EXECUTE IMMEDIATE q'[ALTER TABLE db_changelog ADD CONSTRAINT ck_db_changelog_status CHECK (status IN ('EM_ANDAMENTO', 'APLICADA', 'ERRO'))]';
    END IF;
  END IF;
END;"""


def garantir_tabela_changelog(conn: oracledb.Connection) -> None:
    """Cria db_changelog ou a atualiza para o modelo com status. Idempotente."""
    with conn.cursor() as cur:
        cur.execute(DDL_CHANGELOG_TABLE)
    conn.commit()


# ─── Parser do changelog.yml ──────────────────────────────────────────────────

def ler_changelog(changelog_path: Path) -> list[Migration]:
    """Lê e valida o changelog.yml, retornando lista ordenada de migrations."""
    if not changelog_path.exists():
        log.error(f"{RED}Não encontrado: {changelog_path}{RESET}")
        log.error("Copie assets/changelog_template.yml para db/changelog.yml")
        sys.exit(1)

    with changelog_path.open(encoding="utf-8") as f:
        dados = yaml.safe_load(f)

    if not dados or "migrations" not in dados:
        log.error(f"{RED}changelog.yml não contém a chave 'migrations'{RESET}")
        sys.exit(1)

    migrations: list[Migration] = []
    ids_vistos: set[str] = set()

    for i, entry in enumerate(dados["migrations"], start=1):
        for campo in ("id", "arquivo", "tipo", "descricao"):
            if campo not in entry:
                log.error(f"{RED}Migration #{i} sem campo obrigatório: '{campo}'{RESET}")
                sys.exit(1)

        mid = str(entry["id"]).strip()
        if mid in ids_vistos:
            log.error(f"{RED}ID duplicado no changelog.yml: '{mid}'{RESET}")
            sys.exit(1)
        if len(mid) > 20:
            log.error(f"{RED}ID '{mid}' excede 20 caracteres (coluna db_changelog.id){RESET}")
            sys.exit(1)
        ids_vistos.add(mid)

        tipo = str(entry["tipo"]).lower().strip()
        if tipo not in ("ddl", "dml", "fix"):
            log.error(f"{RED}Migration {mid}: tipo '{tipo}' inválido. Use: ddl | dml | fix{RESET}")
            sys.exit(1)

        migrations.append(Migration(
            id=mid,
            arquivo=str(entry["arquivo"]).strip(),
            tipo=tipo,
            descricao=str(entry["descricao"]).strip(),
        ))

    return migrations


# ─── Operações no db_changelog ────────────────────────────────────────────────

def ler_registros(conn: oracledb.Connection) -> dict[str, Registro]:
    """Estado atual de db_changelog, por id."""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT id, status, checksum, aplicado_em, ambiente, duracao_ms,
                   mensagem_erro, statement_erro
              FROM db_changelog""")
        return {row[0]: Registro(*row) for row in cur.fetchall()}


def _cortar(texto: str | None) -> str | None:
    if not texto:
        return None
    return texto if len(texto) <= _MAX_TEXTO else texto[:_MAX_TEXTO - 3] + "..."


def marcar_em_andamento(conn: oracledb.Connection, migration: Migration,
                        checksum: str, ambiente: str, existente: bool) -> None:
    """Grava EM_ANDAMENTO e comita ANTES de executar a migration."""
    with conn.cursor() as cur:
        if existente:
            cur.execute("""
                UPDATE db_changelog
                   SET status = :status, checksum = :checksum, descricao = :descricao,
                       arquivo = :arquivo, tipo = :tipo, ambiente = :ambiente,
                       aplicado_em = SYSDATE, aplicado_por = USER, duracao_ms = NULL,
                       mensagem_erro = NULL, statement_erro = NULL
                 WHERE id = :id""",
                status=EM_ANDAMENTO, checksum=checksum, descricao=migration.descricao,
                arquivo=migration.arquivo, tipo=migration.tipo, ambiente=ambiente,
                id=migration.id)
        else:
            cur.execute("""
                INSERT INTO db_changelog
                       (id, descricao, arquivo, tipo, checksum, status,
                        aplicado_em, aplicado_por, ambiente)
                VALUES (:id, :descricao, :arquivo, :tipo, :checksum, :status,
                        SYSDATE, USER, :ambiente)""",
                id=migration.id, descricao=migration.descricao, arquivo=migration.arquivo,
                tipo=migration.tipo, checksum=checksum, status=EM_ANDAMENTO,
                ambiente=ambiente)
    conn.commit()


def marcar_aplicada(conn: oracledb.Connection, migration_id: str, duracao_ms: int) -> None:
    with conn.cursor() as cur:
        cur.execute("""
            UPDATE db_changelog
               SET status = :status, duracao_ms = :duracao, aplicado_em = SYSDATE
             WHERE id = :id""",
            status=APLICADA, duracao=duracao_ms, id=migration_id)
    conn.commit()


def marcar_erro(conn: oracledb.Connection, migration_id: str, duracao_ms: int,
                mensagem: str, statement: str) -> None:
    with conn.cursor() as cur:
        cur.execute("""
            UPDATE db_changelog
               SET status = :status, duracao_ms = :duracao,
                   mensagem_erro = :msg_erro, statement_erro = :stmt_erro
             WHERE id = :id""",
            status=ERRO, duracao=duracao_ms, msg_erro=_cortar(mensagem),
            stmt_erro=_cortar(statement), id=migration_id)
    conn.commit()


def marcar_resolvida(conn: oracledb.Connection, migration_id: str, checksum: str) -> None:
    """Registra como APLICADA uma migration corrigida manualmente, mantendo o histórico do erro."""
    with conn.cursor() as cur:
        cur.execute("""
            UPDATE db_changelog
               SET status = :status, checksum = :checksum,
                   mensagem_erro = SUBSTR('[resolvida manualmente por ' || USER || ' em '
                                   || TO_CHAR(SYSDATE, 'DD/MM/YYYY HH24:MI') || '] '
                                   || mensagem_erro, 1, 4000)
             WHERE id = :id
               AND status IN ('ERRO', 'EM_ANDAMENTO')""",
            status=APLICADA, checksum=checksum, id=migration_id)
        if cur.rowcount != 1:
            raise RuntimeError(f"Migration {migration_id} não está em ERRO/EM_ANDAMENTO")
    conn.commit()


# ─── Processamento de migration ───────────────────────────────────────────────

def processar_migration(
    conn: oracledb.Connection,
    cfg: dict,
    migration: Migration,
    db_dir: Path,
    ambiente: str,
    dry_run: bool,
    registro: Registro | None,
) -> ResultadoMigration:
    """Processa uma migration individual. Retorna o resultado."""
    arquivo = db_dir / migration.arquivo

    if not arquivo.exists():
        return ResultadoMigration(
            migration=migration, status=ERRO,
            erro=f"Arquivo não encontrado: db/{migration.arquivo}",
        )

    checksum_atual = checksum_sha256(arquivo)

    if registro is not None and registro.status == APLICADA:
        if registro.checksum == checksum_atual:
            return ResultadoMigration(migration=migration, status="PULADA",
                                      checksum=checksum_atual)
        return ResultadoMigration(
            migration=migration, status=ERRO, checksum=checksum_atual,
            erro=(f"INTEGRIDADE: arquivo alterado após aplicação.\n"
                  f"  Banco   : {registro.checksum[:16]}...\n"
                  f"  Arquivo : {checksum_atual[:16]}...\n"
                  f"  Crie uma nova migration para corrigir."),
        )

    if dry_run:
        return ResultadoMigration(migration=migration, status="DRY_RUN",
                                  checksum=checksum_atual)

    marcar_em_andamento(conn, migration, checksum_atual, ambiente,
                        existente=registro is not None)
    inicio = time.monotonic()
    try:
        executar_e_verificar(conn, arquivo, cfg, cwd=db_dir, verbose=True)
    except ErroSQLcl as e:
        duracao_ms = int((time.monotonic() - inicio) * 1000)
        marcar_erro(conn, migration.id, duracao_ms,
                    e.erro_oracle or str(e), e.statement)
        detalhe = str(e) + (f"\n  Statement: {e.statement[:300]}" if e.statement else "")
        return ResultadoMigration(migration=migration, status=ERRO,
                                  checksum=checksum_atual, erro=detalhe)

    duracao_ms = int((time.monotonic() - inicio) * 1000)
    marcar_aplicada(conn, migration.id, duracao_ms)
    return ResultadoMigration(migration=migration, status=APLICADA,
                              checksum=checksum_atual, duracao_ms=duracao_ms)


# ─── Exibição ─────────────────────────────────────────────────────────────────

def exibir_status(registros: dict[str, Registro], migrations: list[Migration]) -> None:
    """Exibe tabela de estado de todas as migrations."""
    log.info(f"\n{BOLD}Status das migrations:{RESET}")
    log.info("─" * 72)

    pendentes = 0
    for m in migrations:
        r = registros.get(m.id)
        if r is None:
            log.info(f"  {YELLOW}⏳ {m.id:<10}{RESET} {m.descricao[:45]:<45} PENDENTE")
            pendentes += 1
            continue
        quando = r.aplicado_em.strftime("%d/%m/%Y %H:%M") if r.aplicado_em else "—"
        if r.status == APLICADA:
            log.info(f"  {GREEN}✅ {m.id:<10}{RESET} {m.descricao[:45]:<45} "
                     f"{quando}  [{r.ambiente or '—'}]  {r.duracao_ms or 0}ms")
        else:
            log.info(f"  {RED}⛔ {m.id:<10}{RESET} {m.descricao[:45]:<45} "
                     f"{r.status}  {quando}")
            if r.mensagem_erro:
                log.info(f"     {RED}{r.mensagem_erro.splitlines()[0][:100]}{RESET}")

    aplicadas = sum(1 for r in registros.values() if r.status == APLICADA)
    log.info("─" * 72)
    log.info(f"  Total: {len(migrations)} | Aplicadas: {aplicadas} | "
             f"{YELLOW}Pendentes: {pendentes}{RESET}\n")


def exibir_bloqueio(pendencias: list[Registro]) -> None:
    log.error(f"\n{RED}{BOLD}⛔ Execução bloqueada: há migration em ERRO/EM_ANDAMENTO.{RESET}")
    for r in pendencias:
        log.error(f"  {RED}{r.id}: {r.status}{RESET}")
        if r.mensagem_erro:
            log.error(f"    erro      : {r.mensagem_erro.splitlines()[0][:200]}")
        if r.statement_erro:
            log.error(f"    statement : {r.statement_erro.splitlines()[0][:200]}")
    log.error("\n  DDL já executado antes do erro NÃO foi desfeito. Verifique o banco e escolha:")
    log.error("    --retomar <id>           depois de corrigir o arquivo / torná-lo idempotente")
    log.error("    --marcar-resolvida <id>  se o ajuste foi concluído manualmente\n")


# ─── Ponto de entrada ─────────────────────────────────────────────────────────

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Aplica migrations Oracle do db/changelog.yml (execução pelo SQLcl)",
    )
    parser.add_argument("--env", default=os.environ.get("ENVIRONMENT", "dev"),
                        choices=["dev", "hom", "prod"])
    parser.add_argument("--dry-run", action="store_true",
                        help="Simula sem aplicar migrations")
    parser.add_argument("--status", action="store_true",
                        help="Exibe estado atual das migrations e sai")
    acao = parser.add_mutually_exclusive_group()
    acao.add_argument("--retomar", metavar="ID",
                      help="Reexecuta a migration em ERRO/EM_ANDAMENTO e segue com as demais")
    acao.add_argument("--marcar-resolvida", metavar="ID",
                      help="Registra como APLICADA uma migration corrigida manualmente")
    parser.add_argument("--confirmar-prod", action="store_true",
                        help="Confirma deploy em produção sem prompt (obrigatório fora de TTY/CI)")
    parser.add_argument("--project-root", type=Path,
                        default=Path(__file__).parent.parent)
    args = parser.parse_args(argv)

    root = args.project_root.resolve()
    db_dir = root / "db"
    changelog_path = db_dir / "changelog.yml"

    carregar_dotenv(root)

    banner("apply_changelog.py — Migrations do banco", args.env, args.dry_run)

    if args.env == "prod" and not args.status:
        confirmar_producao(args.dry_run, confirmado=args.confirmar_prod)

    migrations = ler_changelog(changelog_path)
    por_id = {m.id: m for m in migrations}
    log.info(f"  {len(migrations)} migrations em changelog.yml")

    cfg = obter_config_db()
    conn = conectar(cfg)

    try:
        garantir_tabela_changelog(conn)
        registros = ler_registros(conn)

        if args.status:
            exibir_status(registros, migrations)
            return 0

        pendencias = [r for r in registros.values() if r.status in PENDENCIAS]
        alvo = args.retomar or args.marcar_resolvida
        if alvo:
            if alvo not in {r.id for r in pendencias}:
                log.error(f"{RED}Migration '{alvo}' não está em ERRO/EM_ANDAMENTO.{RESET}")
                return 1
            if alvo not in por_id:
                log.error(f"{RED}Migration '{alvo}' não existe mais no changelog.yml.{RESET}")
                return 1
            if args.retomar and len(pendencias) > 1:
                exibir_bloqueio(pendencias)
                log.error(f"{RED}Resolva uma pendência por vez.{RESET}")
                return 1

        if args.marcar_resolvida:
            if args.dry_run:
                log.info(f"  {CYAN}DRY-RUN: marcaria {alvo} como APLICADA{RESET}")
                return 0
            checksum = checksum_sha256(db_dir / por_id[alvo].arquivo)
            marcar_resolvida(conn, alvo, checksum)
            log.info(f"  {GREEN}✅ {alvo} registrada como APLICADA (resolvida manualmente).{RESET}")
            return 0

        if pendencias and not args.retomar:
            exibir_bloqueio(pendencias)
            return 1

        log.info(f"\n{'─' * 55}")

        resultados: list[ResultadoMigration] = []
        falhou = False

        for migration in migrations:
            log.info(f"  {migration.id} — {migration.descricao}")
            resultado = processar_migration(
                conn, cfg, migration, db_dir, args.env, args.dry_run,
                registros.get(migration.id))
            resultados.append(resultado)

            if resultado.status == APLICADA:
                log.info(f"  {GREEN}✅ Aplicada{RESET} em {resultado.duracao_ms}ms  "
                         f"[{resultado.checksum[:12]}...]")
            elif resultado.status == "PULADA":
                log.info(f"  {YELLOW}⏭  Já aplicada — pulando{RESET}")
            elif resultado.status == "DRY_RUN":
                log.info(f"  {CYAN}🔍 DRY-RUN — seria aplicada{RESET}  "
                         f"[{resultado.checksum[:12]}...]")
            elif resultado.status == ERRO:
                log.error(f"  {RED}❌ ERRO: {resultado.erro}{RESET}")
                log.error(f"  {RED}⛔ Deploy interrompido. Migration registrada como ERRO "
                          f"em db_changelog (ver --status).{RESET}")
                falhou = True
                break

            log.info("")

        # Relatório final
        aplicadas = sum(1 for r in resultados if r.status == APLICADA)
        puladas = sum(1 for r in resultados if r.status == "PULADA")
        dry_runs = sum(1 for r in resultados if r.status == "DRY_RUN")
        erros = sum(1 for r in resultados if r.status == ERRO)

        log.info(SEP2)
        log.info(f"  {GREEN}✅ Aplicadas : {aplicadas}{RESET}")
        log.info(f"  {YELLOW}⏭  Puladas   : {puladas}{RESET}")
        if dry_runs:
            log.info(f"  {CYAN}🔍 Dry-run  : {dry_runs}{RESET}")
        if erros:
            log.info(f"  {RED}❌ Erros    : {erros}{RESET}")
        log.info(SEP2)

        if aplicadas > 0 and not args.dry_run:
            log.info("\nPróximo passo: sincronizar DDL no Git:")
            log.info(f"  python scripts/export_db.py --schema {cfg['schema']}")

        return 1 if falhou else 0

    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())
