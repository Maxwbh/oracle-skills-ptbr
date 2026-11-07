---
name: oracle-tuning-ptbr
description: Módulo de tuning da suíte Oracle PT-BR. Performance tuning Oracle 19c — explain plan, análise AWR/ASH de SQL, indexes, hints, bind variables, cursor sharing, DBMS_STATS, V$SQL, V$SQLAREA, V$SESSION_WAIT. ATIVE em query lenta, full scan indesejado, hard parse alto, index strategy, plano de execução ruim, estatísticas desatualizadas, cardinality errada, AWR snapshot, ASH amostragem. Frases — "query está lenta", "qual index criar", "melhorar explain plan", "muitos hard parse", "cursor sharing", "optimizer hint", "runstats". NÃO ATIVE em DBA operacional (sessões/locks/tablespace), código PL/SQL novo, APEX, ORDS. Templates em assets/.
metadata:
  version: "2.7.0"
  release_date: "2026-11-06"
  repository: "https://github.com/maxwbh/oracle-skills-ptbr"
  suite_size: 7
  author: "Maxwell da Silva Oliveira"
  contact: "contato@msbrasil.inf.br"
  organization: "M&S do Brasil LTDA"
  site: "https://msbrasil.inf.br"
  tags:
    - "oracle"
    - "tuning"
    - "performance"
    - "explain-plan"
    - "awr"
    - "ash"
    - "indexes"
    - "statistics"
  category: "database"
  language: "pt-BR"
  icon: "🚀"
---

# Suíte Oracle PT-BR — Módulo Tuning (oracle-tuning-ptbr)

> **Versão:** 2.7.0 · **Atualizada em:** novembro/2026 · **Repositório:** oracle-skills-ptbr · **Suíte:** 10 skills (7 recursos nesta skill)
> **v2.7.0:** baseline SPM aceito pode não ser usado (caso 19.32): conferir V$SQL.SQL_PLAN_BASELINE e REPRODUCED. Histórico em `CHANGELOG.md`.

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

> Fora da suíte (repositório separado): **oracle-26ai-helper-ptbr** — Vector Search, JSON Relational Duality e RAFT (replicação do Globally Distributed Database). Roteamento: Vector / Duality / RAFT → **oracle-26ai-helper-ptbr**; sintaxe nova e migração 19c→26ai → **oracle-26ai-ptbr**.


Performance tuning Oracle 19c — análise de planos de execução, índices e leitura de AWR/ASH para diagnosticar SQL.

**Desenvolvido por:** Maxwell da Silva Oliveira — [M&S do Brasil LTDA](https://msbrasil.inf.br)

## Áreas cobertas

| Área | Reference | Assets |
|---|---|---|
| **Performance** | `references/performance-tuning.md` | `explain_plan_workflow.sql`, `index_strategy_examples.sql` |
| **Result Cache** | `references/performance-tuning.md` | `result_cache_pattern.sql` (quando usar, invalidação, anti-patterns) |
| **Estatísticas do optimizer** | `references/optimizer-statistics-ptbr.md` | `optimizer_statistics_examples.sql` |

## Quando ativar

- Query lenta — análise de explain plan, `AUTOTRACE`, `DBMS_XPLAN.DISPLAY_CURSOR`
- Índices: `B-Tree`, `Bitmap` (DW, não OLTP), `Function-Based`, `Composite`, `Unique`, `Reverse Key`, `Invisible`; índice de cobertura; `Invisible` vs `Unusable`
- `V$SQL`, `V$SQLAREA` — top SQL por `ELAPSED_TIME`, `CPU_TIME`, `BUFFER_GETS`
- `V$SESSION_WAIT`, `V$SYSTEM_EVENT` — wait event analysis
- Hard parse alto: bind variables ausentes, cursor sharing
- Cardinality errada: `DBMS_STATS`, `METHOD_OPT`, `HISTOGRAM`
- AWR: `DBA_HIST_SQLSTAT`, `DBA_HIST_SQL_PLAN`, `DBA_HIST_SYSTEM_EVENT` para analisar um SQL ao longo do tempo (requer Diagnostics Pack — licença, retenção e snapshots são assunto de **oracle-dba-ptbr**)
- ASH: `V$ACTIVE_SESSION_HISTORY`, `DBA_HIST_ACTIVE_SESS_HISTORY`
- Hints: `/*+ APPEND */`, `/*+ INDEX */`, `/*+ PARALLEL */`, `/*+ FIRST_ROWS */`
- Paralelismo: statement-level vs object-level, parallel DML (`ENABLE PARALLEL DML`), DOP, `V$PX_SESSION`
- `MERGE` vs loop, `BULK COLLECT` para I/O pesado
- Estatísticas: `GATHER_SCHEMA_STATS`, `GATHER_TABLE_STATS`, lock stats
- Estatísticas do optimizer (aprofundado): histogramas (frequency/top-frequency/height-balanced/hybrid), `METHOD_OPT`, estatísticas estendidas (column groups), preferences (`GET_PREFS`/`SET_TABLE_PREFS`), SQL Plan Directives, pending/restore/retention stats, Optimizer Statistics Advisor, SQL Tuning Advisor/SQL Profile

**Não usar** para: DBA ops (sessão/lock/kill), código PL/SQL novo, APEX, ORDS.

## Princípios canônicos

- **Medir antes de otimizar.** Baseline com `SET TIMING ON` + `AUTOTRACE`. Sem medição, otimização é placebo.
- **Bind variables primeiro.** Hard parse elevado em `V$SQLAREA` resolve antes de qualquer tuning de index.
- **Index ≠ sempre melhor.** Full scan em tabela pequena ou query retornando > 10% das linhas geralmente vence B-Tree.
- **AWR requer licença.** `DBA_HIST_*` e ASH → Diagnostics Pack obrigatório. Cheque o parâmetro `control_management_pack_access` em `V$PARAMETER` (`NONE`/`DIAGNOSTIC`/`DIAGNOSTIC+TUNING`) e o uso real em `DBA_FEATURE_USAGE_STATISTICS`.
- **Histogram nas colunas com skew.** Sem histogram, optimizer usa densidade plana → plano errado em distribuição assimétrica.
- **CREATE INDEX ONLINE** em produção — sem `ONLINE`, bloqueia DML.
- **Paralelismo é para volume, não OLTP.** Ajuda em full scans/joins grandes e ETL; atrapalha em lookups de poucas linhas e tabelas pequenas. Parallel DML está desabilitado por padrão — exige `ALTER SESSION ENABLE PARALLEL DML` (ou hint `ENABLE_PARALLEL_DML`), senão o DML roda serial mesmo com hint `PARALLEL`.

## Referências cruzadas

| Precisa de | Skill |
|---|---|
| PL/SQL com BULK COLLECT, loop otimizado | **oracle-plsql-ptbr** |
| Licença Diagnostics Pack, retenção/snapshots AWR, sessões, DBA operacional | **oracle-dba-ptbr** |
| Query lenta em report APEX | **oracle-apex-ptbr** |
| Naming Trivadis em scripts de tuning | **oracle-trivadis-ptbr** |
