---
name: oracle-plsql-ptbr
description: Módulo PL/SQL da suíte Oracle PT-BR. PL/SQL Oracle 19c — packages, procedures, functions, types, cursores, LOBs e EBR. ATIVE em BULK COLLECT, FORALL, NOCOPY, EXECUTE IMMEDIATE, MERGE INTO, compound trigger, editioning view, cross-edition trigger, CLOB/BLOB, Logger, exception handler, DML alternatives. Frases ambíguas com contexto PL/SQL — "criar package", "refatorar procedure", "processar LOB", "zero downtime deploy", "loop tá lento", "trigger de auditoria". NÃO ATIVE em páginas APEX, endpoints ORDS, DBA operacional (sessões/locks/tablespace), tuning de queries (explain plan/AWR/ASH). Aplica naming Trivadis automaticamente — para revisão explícita do padrão use oracle-trivadis-ptbr. Templates em assets/.
metadata:
  version: "3.0.2"
  release_date: "2026-11-07"
  repository: "https://github.com/maxwbh/oracle-skills-ptbr"
  suite_size: 11
  author: "Maxwell da Silva Oliveira"
  contact: "contato@msbrasil.inf.br"
  organization: "M&S do Brasil LTDA"
  site: "https://msbrasil.inf.br"
  tags:
    - "oracle"
    - "plsql"
    - "database"
    - "packages"
    - "triggers"
    - "lob"
    - "ebr"
    - "logger"
    - "oracle-19c"
  category: "database"
  language: "pt-BR"
  icon: "🗄️"
---

# Suíte Oracle PT-BR — Módulo PL/SQL (oracle-plsql-ptbr)

> **Versão:** 3.0.2 · **Atualizada em:** novembro/2026 · **Repositório:** oracle-skills-ptbr · **Suíte:** 10 skills (11 recursos nesta skill)
> **v3.0.2:** roteamento do roteiro de upgrade 19c→26ai. Histórico em `CHANGELOG.md`.

Suíte completa (10 skills — conjunto único):
- **oracle-core-ptbr** — roteamento central, convenções transversais, cenários multidisciplinares
- **oracle-plsql-ptbr** — PL/SQL 19c: packages, BULK, LOBs, triggers, EBR
- **oracle-trivadis-ptbr** — Trivadis 4.4: naming, prefixos, revisão de código
- **oracle-apex-ptbr** — APEX 24.2–26.2: páginas, DA, IG, APIs APEX_*, metadata
- **oracle-ords-ptbr** — ORDS: REST modules/handlers, OAuth, Network ACL
- **oracle-dba-ptbr** — DBA operacional: sessões, locks, flashback, scripts ad-hoc
- **oracle-tuning-ptbr** — performance: explain plan, índices, stats, result cache
- **oracle-devops-ptbr** — Git/CI-CD: estrutura, Liquibase, pipelines, GMUD
- **oracle-26ai-ptbr** — 23ai/26ai: novidades SQL/PL/SQL, backports 19.28, migração 19c→26ai (só com versão declarada)
- **oracle-lab-ptbr** — instalação e ambiente local (VM/container) para quem não é DBA; rede de casa

> Fora da suíte (repositório separado): **oracle-26ai-helper-ptbr** — Vector Search, JSON Relational Duality, RAFT (replicação do Globally Distributed Database) e roteiro do upgrade 19c→26ai. Roteamento: Vector / Duality / RAFT e roteiro do upgrade (fases, riscos, Vector Pool na janela) → **oracle-26ai-helper-ptbr**; sintaxe nova e checklist de código da migração (o que muda, caminhos, compatibilidade APEX/ORDS/SQLcl) → **oracle-26ai-ptbr**; operação do upgrade (AutoUpgrade, PDB, Data Guard) → **oracle-dba-ptbr**.


PL/SQL Oracle 19c seguindo Trivadis Guidelines 4.4. Foco em código correto, seguro e performático.

**Desenvolvido por:** Maxwell da Silva Oliveira — [M&S do Brasil LTDA](https://msbrasil.inf.br)

## Áreas cobertas

| Área | Reference | Assets |
|---|---|---|
| **EBR (zero downtime)** | `references/ebr-editioning-views.md` | (conceitual) |
| **PL/SQL** | naming/estrutura: **oracle-trivadis-ptbr** | `package_header.sql`, `package_body.sql`, `exception_template.sql`, `bulk_processing_template.sql`, `dml_alternatives_to_plsql.sql`, `nocopy_for_lobs.sql`, `clob_blob_operations.sql`, `logger_integration.sql`, `triggers_canonicos.sql` |

> **Referência cruzada de nomenclatura:** padrão Trivadis 4.4 completo (prefixos, estrutura, naming PT-BR) está em **oracle-trivadis-ptbr**. Esta skill aplica as convenções automaticamente — carregue `oracle-trivadis-ptbr` quando o foco for revisão explícita de padrão.

## Quando ativar

- Criação ou refatoração de packages, procedures, functions, types
- BULK COLLECT + FORALL (loop PL/SQL em volume)
- NOCOPY para BLOB/CLOB > 100KB ou collections grandes em IN OUT
- EXECUTE IMMEDIATE com bind variables (SQL dinâmico)
- MERGE INTO como substituto de loop SELECT/INSERT/UPDATE
- LOBs: leitura em chunks, Base64, SHA-256, DBMS_LOB
- Triggers: simples `FOR EACH ROW` (auditoria de colunas, surrogate key legada), compound (estado entre linha e statement, mutating table, auditoria em lote), cross-edition (EBR)
- EBR: editioning views, cross-edition triggers, deploy zero downtime
- Logger (OraOpenSource): log_error, log_warn, log_info, log_permanent
- Qualquer menção a AUTONOMOUS_TRANSACTION, PRAGMA, DBMS_ERRLOG

**Não usar** para: APEX pages/regions/items, ORDS endpoints/modules, DBA ops (sessão/lock/tablespace), tuning de queries.

> **Fronteira com oracle-tuning-ptbr:** paralelismo *como técnica de escrita de DML* (hints `PARALLEL`/`APPEND` em INSERT SELECT, CTAS, external table) fica aqui. *Diagnóstico de plano de execução* (explain plan, AWR, ASH, escolha de índice) vai para **oracle-tuning-ptbr**.

## Princípios canônicos

0. **SQL puro antes de PL/SQL.** Se MERGE, INSERT SELECT ou UPDATE com CASE resolve — use. PL/SQL só quando há lógica de negócio por linha, chamadas externas ou coordenação complexa.
1. **Bind variables sempre.** Em EXECUTE IMMEDIATE use `USING`. Identificadores dinâmicos → `DBMS_ASSERT.simple_sql_name`.
2. **Bulk em loops.** `BULK COLLECT` + `FORALL`. Com `LIMIT` para volumes > 100k. `DBMS_ERRLOG` quando cabe DML único.
3. **Exception com contexto, sem perder o erro original.** `lc_nome_unidade CONSTANT VARCHAR2(60)` em toda procedure pública. Erro de negócio conhecido → `raise_application_error(-20xxx, msg)` mapeado em exceção nomeada. Erro inesperado → log com backtrace + `RAISE` (nunca trocar por `-20999` com `SQLERRM`: perde código e pilha). Para acrescentar contexto, `raise_application_error(..., TRUE)`.
4. **Transação tem dono.** Rotina reutilizável **não faz COMMIT nem ROLLBACK total**: abre `SAVEPOINT` no início e, no handler, faz `ROLLBACK TO` (desfaz só o próprio trabalho) e propaga a exceção (`RAISE`). `COMMIT`/`ROLLBACK` total só no **ponto de entrada dono da transação** — job do scheduler, handler ORDS, script de carga — e documentado no cabeçalho dele. No APEX, o dono é o próprio APEX (o process não comita). Única exceção: log em `PRAGMA AUTONOMOUS_TRANSACTION` (o commit é da transação autônoma). Ver `exception_template.sql` e `package_body.sql` (`processar_registro` × `processar_pendentes`).
5. **Logger em vez de DBMS_OUTPUT** em produção.
6. **Privilégios mínimos.** Schema owner faz DDL; app user faz DML.
7. **Auditabilidade.** `criado_em`, `criado_por`, `atualizado_em`, `atualizado_por` em tabelas de domínio.
8. **NOCOPY para LOB/collection grande** em IN OUT/OUT.
9. **Triggers não contêm regra de negócio.** Auditoria, surrogate key, cross-edition EBR.
10. **Compound trigger quando há estado entre linha e statement** — evitar mutating table (coletar na linha, consultar no AFTER STATEMENT), auditoria em lote, processamento em bulk. Para o caso só-linha (colunas de auditoria, surrogate key legada), **trigger simples `FOR EACH ROW` continua válida** e é mais legível. Nunca compartilhe estado entre triggers via variável global de package.
11. **EBR para zero downtime.** Editioning views + editions + cross-edition triggers.

## Fluxo de uso

**Criar código:** SQL puro resolve? → `dml_alternatives_to_plsql.sql`. Não → clone template da área → adapte naming Trivadis → use Logger.

**Revisar código:** Princípio #0 primeiro. Depois antipatterns: concatenação em SQL dinâmico, loop linha-a-linha, `WHEN OTHERS THEN NULL`, `DBMS_OUTPUT` em produção, falta NOCOPY em LOB IN OUT. Para naming explícito → **oracle-trivadis-ptbr**.

## Referências cruzadas

| Precisa de | Skill |
|---|---|
| Naming, prefixos, checklist Trivadis | **oracle-trivadis-ptbr** |
| APEX page process, dynamic action, IG | **oracle-apex-ptbr** |
| ORDS handler, módulo REST | **oracle-ords-ptbr** |
| Sessão, lock, flashback, tablespace | **oracle-dba-ptbr** |
| Explain plan, AWR, index, tuning | **oracle-tuning-ptbr** |
| Sintaxe 23ai/26ai (BOOLEAN, RETURNING OLD/NEW, RESETTABLE, transpiler) — só com versão declarada | **oracle-26ai-ptbr** |
