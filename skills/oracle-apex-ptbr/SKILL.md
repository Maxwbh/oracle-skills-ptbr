---
name: oracle-apex-ptbr
description: Módulo APEX da suíte Oracle PT-BR. Oracle APEX 26.1 (padrões válidos de 24.2+) — desenvolvimento e dicionário de metadados. ATIVE em Dynamic Actions, Interactive Report, Interactive Grid, Classic Report, Page Process, AJAX Callback, Validations, Authorization Schemes, pagination, LOV, APEX_APPLICATION_*, APEX_APPLICATION_PAGE_*, APEX_WORKSPACE_*, APEX_APPL_*, Workflows, Tasks, AI configs, ACL, JSON Sources, APEX_ACTIVITY_LOG. Frases — "página APEX", "region IR", "IG editável", "process no submit", "qual view APEX usar", "auditar paginação APEX". NÃO ATIVE em PL/SQL puro, ORDS endpoints, DBA operacional. Para naming use oracle-trivadis-ptbr. Templates em assets/.
metadata:
  version: "2.4.2"
  release_date: "2026-09-15"
  repository: "https://github.com/maxwbh/oracle-skills-ptbr"
  suite_size: 20
  author: "Maxwell da Silva Oliveira"
  contact: "contato@msbrasil.inf.br"
  organization: "M&S do Brasil LTDA"
  site: "https://msbrasil.inf.br"
  tags:
    - "oracle"
    - "apex"
    - "apex-26"
    - "interactive-report"
    - "interactive-grid"
    - "workflow"
    - "javascript"
  category: "development"
  language: "pt-BR"
  icon: "⚡"
---

# Suíte Oracle PT-BR — Módulo APEX (oracle-apex-ptbr)

> **Versão:** 2.4.2 · **Atualizada em:** setembro/2026 · **Repositório:** oracle-skills-ptbr · **Suíte:** 10 skills (20 recursos nesta skill)
> **v2.4.2:** suíte com 10 skills; referência cruzada para montar APEX+ORDS local. Histórico em `CHANGELOG.md`.

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


Oracle APEX 26.1 (padrões válidos de 24.2+) — padrões de desenvolvimento e dicionário completo de views de metadados.

**Desenvolvido por:** Maxwell da Silva Oliveira — [M&S do Brasil LTDA](https://msbrasil.inf.br)

## Áreas cobertas

| Área | Reference | Assets |
|---|---|---|
| **Padrões APEX 26.1** | `references/apex-patterns.md` | `apex_dynamic_action.sql`, `apex_pagination_pattern.sql`, `apex_pl_sql_process.sql`, `apex_long_running_job.sql`, `apex_interactive_grid.sql`, `apex_blob_upload_download.sql`, `apex_json_source.sql` |
| **APIs PL/SQL APEX (aprofundamento)** | — | `apex_util_reference.sql`, `apex_collection_reference.sql`, `apex_application_global.sql`, `apex_json_reference.sql`, `apex_debug_patterns.sql`, `apex_item_legacy.sql` |
| **Autenticação custom** | — | `apex_authentication_custom.sql` (custom scheme, sentry, OIDC, HTTP Header) |
| **Universal Theme** | — | `universal_theme_patterns.sql` (classes t-/u-, tokens --ut-*, dark mode) |
| **Auditoria via metadata** | `references/apex-data-dictionary-ptbr.md` | `apex_metadata_queries.sql` (linter caseiro, pre-deploy validation) |
| **Matriz de versões (24 vs 26)** | `references/apex-version-matrix-ptbr.md` | (tabela embutida no reference) |

## Quando ativar

- Qualquer menção a APEX, App Builder, página, região, item, process, validation
- Dynamic Actions (event, true/false action, affected elements)
- Interactive Report: pagination, colunas, filtros, `APEX_APPLICATION_PAGE_IR`
- Interactive Grid: edição, save process, `APEX_APPLICATION_PAGE_IG`
- Page Process e AJAX Callback (apex.server.process)
- Authorization Scheme e Authentication Scheme
- Paginação de reports (Row Ranges, "of Z", cache de região)
- APEX_APPLICATION_*, APEX_WORKSPACE_*, APEX_APPL_*, APEX_ACTIVITY_LOG
- Workflows, Tasks, AI configs (24.1+), JSON Sources (24.2+)
- `APEX_BACKGROUND_PROCESS`, jobs longos (> 30s)
- BLOB upload/download via APEX (html2pdf, armazenamento)

**Não usar** para: PL/SQL puro sem APEX, ORDS endpoints, DBA operacional.

## Princípios canônicos

- **Page Process vs Dynamic Action:** lógica server-side com transação → Page Process. Reação client-side leve → Dynamic Action.
- **Pagination correta:** `Row Ranges X to Y of Z` em IR. Classic Report: `Rows X to Y`.
- **Items sensíveis:** `Value Protected: Yes` sempre em Hidden PKs.
- **Exception em process APEX:** use `APEX_ERROR.add_error` — nunca `raise_application_error` direto sem handler.
- **APEX não comita:** processos PL/SQL dentro de APEX não fazem COMMIT — o framework gerencia.
- **APEX_DICTIONARY:** ponto de entrada para descoberta de qualquer view de metadados APEX.
- **Consciência de versão:** features divergem entre 24.1, 24.2 e 26.1. Antes de gerar código que dependa de versão (IA no app, APEXlang, Select One/Many, Slots, Workflow/Working Copy, session state BOOLEAN, Universal Theme Iris), confirme a versão-alvo — ver regra abaixo. Consulte `references/apex-version-matrix-ptbr.md` para o que é exclusivo de cada release.

## Distinção de versão (24 vs 26)

A versão atual é o **APEX 26.1** (lançado em mai/2026); **24.2** segue suportado
até jul/2027 e **24.1** até dez/2026. Resumo do que é exclusivo (detalhe e
verificação em `references/apex-version-matrix-ptbr.md`):

| Exclusivo de 26.1 | Introduzido em 24.2 | Introduzido em 24.1 |
|---|---|---|
| APEXlang (`.apx`), AI Interactive Reports, AI Agents, Data Reporter | JSON Sources Shared Component, RAG declarativo, vector search, DA "gerar texto" | `APEX_AI` (chat/generate), APEX Assistant, Select One/Many |
| Universal Theme "Iris" + Font APEX 2.5 | Grouping em Template Components, dependency reporting | Slots (Template Components), Component Groups |
| Template Components client-side partials; Workflow Parallel Flow | Criar modelo de dados por linguagem natural; Font APEX 2.4 | REST Data Source Profiles hierárquicos + array columns |
| Session state BOOLEAN (**requer banco 26ai**); ORDS 26.1.1+ | melhorias Workflows/REST/Fusion | Working Copies aprimoradas; Workflow dashboard/diagram |

Base comum desde 23.x: Workflow + Working Copy (23.2), Background Page
Processing/Execution Chain (23.1). IR, IG, Classic Report, Dynamic Actions,
`APEX_ERROR`/`APEX_JSON`/`APEX_COLLECTION` valem em todas as versões.

**Regra — perguntar a versão-alvo:** se o pedido envolver uma feature
versão-dependente e a versão **não estiver clara na conversa**, faça UMA pergunta
curta ("Para qual versão do APEX — 24.1, 24.2 ou 26.1 — e, se for o caso, qual
banco?") antes de gerar o código. Se a versão já foi informada (ex.: "estou no
26.1"), não pergunte de novo — apenas sinalize a dependência de versão quando
relevante.

## Referências cruzadas

| Precisa de | Skill |
|---|---|
| PL/SQL dentro de processes (packages, bulk) | **oracle-plsql-ptbr** |
| Naming e prefixos Trivadis no código | **oracle-trivadis-ptbr** |
| Endpoints REST consumidos pelo APEX | **oracle-ords-ptbr** |
| Sessão APEX no banco, locks | **oracle-dba-ptbr** |
| Query lenta em report APEX | **oracle-tuning-ptbr** |
| Banco 26ai (session state BOOLEAN, duality views via AutoREST) | **oracle-26ai-ptbr** |
| Instalar APEX + ORDS na própria máquina | **oracle-lab-ptbr** |
