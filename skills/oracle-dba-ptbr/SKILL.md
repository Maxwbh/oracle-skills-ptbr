---
name: oracle-dba-ptbr
description: Módulo DBA da suíte Oracle PT-BR. DBA operacional Oracle 19c e dicionário (V$, GV$, DBA_*, CDB_*, DBA_HIST_*). ATIVE em sessão travada, bloqueio, kill session, RAC (GV$SESSION, INST_ID), flashback query/table, recompile objetos inválidos, tablespace cheio, espaço em disco, DBMS_STATS (coleta, agendamento, lock), AWR/ASH (licença, retenção, snapshots — a análise do SQL é oracle-tuning-ptbr), Diagnostics Pack, SE2 vs EE, Data Guard, CDB/PDB, V$PDBS. Frases — "quem tá bloqueando", "recuperar dado deletado", "objetos inválidos", "qual view DBA usar", "tablespace cheio", "edição do banco", "Diagnostics Pack licença". NÃO ATIVE em código PL/SQL novo, APEX, ORDS, explain plan/tuning.
metadata:
  version: "2.3.2"
  release_date: "2026-09-15"
  repository: "https://github.com/maxwbh/oracle-skills-ptbr"
  suite_size: 15
  author: "Maxwell da Silva Oliveira"
  contact: "contato@msbrasil.inf.br"
  organization: "M&S do Brasil LTDA"
  site: "https://msbrasil.inf.br"
  tags:
    - "oracle"
    - "dba"
    - "performance"
    - "awr"
    - "ash"
    - "rac"
    - "flashback"
    - "data-dictionary"
  category: "database"
  language: "pt-BR"
  icon: "🛡️"
---

# Suíte Oracle PT-BR — Módulo DBA (oracle-dba-ptbr)

> **Versão:** 2.3.2 · **Atualizada em:** setembro/2026 · **Repositório:** oracle-skills-ptbr · **Suíte:** 10 skills (15 recursos nesta skill)
> **v2.3.2:** suíte com 10 skills; fronteira com oracle-lab-ptbr (máquina local do dev) explicitada. Histórico em `CHANGELOG.md`.

Suíte completa (10 skills — conjunto único):
- **oracle-core-ptbr** — roteamento central, convenções transversais, cenários multidisciplinares
- **oracle-plsql-ptbr** — PL/SQL 19c: packages, BULK, LOBs, triggers, EBR
- **oracle-trivadis-ptbr** — Trivadis 4.4: naming, prefixos, revisão de código
- **oracle-apex-ptbr** — APEX 26.1: páginas, DA, IG, APIs APEX_*, metadata
- **oracle-ords-ptbr** — ORDS: REST modules/handlers, OAuth, Network ACL
- **oracle-dba-ptbr** — DBA operacional: sessões, locks, flashback, scripts ad-hoc
- **oracle-tuning-ptbr** — performance: explain plan, índices, stats, result cache
- **oracle-devops-ptbr** — Git/CI-CD: estrutura, Liquibase, pipelines, GMUD
- **oracle-26ai-ptbr** — 23ai/26ai: novidades SQL/PL/SQL, backports 19.28, migração 19c→26ai (só com versão declarada)
- **oracle-lab-ptbr** — instalação e ambiente local (VM/container) para quem não é DBA; rede de casa


DBA operacional Oracle 19c e dicionário completo de views (estáticas e dinâmicas).

**Desenvolvido por:** Maxwell da Silva Oliveira — [M&S do Brasil LTDA](https://msbrasil.inf.br)

## Áreas cobertas

| Área | Reference | Assets |
|---|---|---|
| **DBA operacional** | `references/dba-operations.md` | `session_management.sql`, `flashback_query.sql`, `recompile_invalid_objects.sql` |
| **Diagnose ad-hoc (Tim Hall style)** | — | `assets/scripts_dba/` — 8 scripts prontos para `@nome` em SQLcl: `locked_objects`, `lock_tree` (quem bloqueia quem), `top_sessions` (CPU/IO agora), `longops` (progresso de operações longas), `invalid_objects_quick`, `redo_by_hour`, `index_usage`, `session_pga` |
| **Oracle Data Dictionary** | `references/data-dictionary-ptbr.md` | (queries embutidas no reference) |

## Quando ativar

- Sessões travadas, bloqueios, `blocking_session`, kill session
- RAC: `GV$SESSION`, `GV$LOCK`, `INST_ID`, kill cross-instance
- Flashback query (`AS OF TIMESTAMP`, `AS OF SCN`) e `FLASHBACK TABLE`
- Objetos inválidos: listar, recompilar, dependências
- Tablespace: uso, datafiles, free space, autoextend
- Estatísticas: `DBMS_STATS`, `last_analyzed`, locked stats
- AWR: licença Diagnostics Pack, retenção e snapshots (`DBMS_WORKLOAD_REPOSITORY`), relatório `awrrpt` — **verifica a licença primeiro**; a análise de um SQL específico fica em **oracle-tuning-ptbr**
- ASH: `V$ACTIVE_SESSION_HISTORY`, `DBA_HIST_ACTIVE_SESS_HISTORY`
- Dúvidas sobre edição: SE2 vs EE, `V$OPTION`
- CDB/PDB: `V$PDBS`, `V$CONTAINERS`, `CDB_*`, `CON_ID`
- Data Guard: `V$DATAGUARD_STATUS`, `V$MANAGED_STANDBY`
- Hierarquia de views: `X$`, `V$`, `GV$`, `DBA_*`, `ALL_*`, `USER_*`

**Não usar** para: código PL/SQL novo, APEX, ORDS, explain plan/index tuning.

## Princípios canônicos

- **Privilégio mínimo:** app user faz DML; schema owner faz DDL; DBA só quando necessário.
- **KILL com cautela:** verifica transação ativa antes — rollback pode demorar horas.
- **Confirme o Diagnostics Pack antes de `DBA_HIST_*`/ASH:** o parâmetro `control_management_pack_access` (em `V$PARAMETER`, valores `NONE` | `DIAGNOSTIC` | `DIAGNOSTIC+TUNING`) indica se o pack está habilitado; `V$OPTION` lista opções instaladas (Partitioning, RAC). Uso sem licença é infração contratual — auditável via `DBA_FEATURE_USAGE_STATISTICS`.
- **RAC:** `V$SESSION` = instância local; `GV$SESSION` = todas. Sempre inclui `INST_ID` no kill em RAC.
- **Flashback:** respeita `undo_retention`. Para períodos longos: Flashback Database (configuração prévia).
- **CDB:** `CDB_*` + `CON_ID` para visão cross-container. `DBA_*` = container corrente.

## Referências cruzadas

| Precisa de | Skill |
|---|---|
| Código PL/SQL, packages, procedures | **oracle-plsql-ptbr** |
| Explain plan, análise AWR/ASH de um SQL, indexes | **oracle-tuning-ptbr** |
| APEX views (APEX_WORKSPACE_ACTIVITY_LOG) | **oracle-apex-ptbr** |
| ORDS views (USER_ORDS_*, DBA_ORDS_*) | **oracle-ords-ptbr** |
| Naming Trivadis em scripts DBA | **oracle-trivadis-ptbr** |
| Planejar upgrade 19c → 26ai (compatibilidade, checklist de código) | **oracle-26ai-ptbr** |
| Instalar ou consertar o banco local do próprio dev (VM, container) | **oracle-lab-ptbr** |
