---
name: oracle-apex-ptbr
description: Módulo APEX da suíte Oracle PT-BR. Oracle APEX 26.1 (padrões válidos de 24.2+) — desenvolvimento e dicionário de metadados. ATIVE em Dynamic Actions, Interactive Report, Interactive Grid, Classic Report, Page Process, AJAX Callback, Validations, Authorization Schemes, pagination, LOV, APEX_APPLICATION_*, APEX_APPLICATION_PAGE_*, APEX_WORKSPACE_*, APEX_APPL_*, Workflows, Tasks, AI configs, ACL, JSON Sources, APEX_ACTIVITY_LOG. Frases — "página APEX", "region IR", "IG editável", "process no submit", "qual view APEX usar", "auditar paginação APEX". NÃO ATIVE em PL/SQL puro, ORDS endpoints, DBA operacional. Para naming use oracle-trivadis-ptbr. Templates em assets/.
metadata:
  version: "2.5.0"
  release_date: "2026-11-06"
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

> **Versão:** 2.5.0 · **Atualizada em:** novembro/2026 · **Repositório:** oracle-skills-ptbr · **Suíte:** 10 skills (20 recursos nesta skill)
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

> Fora da suíte (repositório separado): **oracle-26ai-helper-ptbr** — Vector Search, JSON Relational Duality e RAFT (replicação do Globally Distributed Database). Roteamento: Vector / Duality / RAFT → **oracle-26ai-helper-ptbr**; sintaxe nova e migração 19c→26ai → **oracle-26ai-ptbr**.


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
| **Segurança — patch level (CPU out/2026)** | `references/apex-version-matrix-ptbr.md` (seção Segurança) | `apex_verificar_patch_seguranca.sql` (classifica a versão instalada contra CVE-2026-101521 e CVE-2026-66010) |
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
- **Patch level antes de orientar uma instância:** ao gerar código ou orientação para uma instância APEX **existente**, pergunte (ou peça para rodar `apex_verificar_patch_seguranca.sql`) a versão completa com patch set — ex.: 24.2.**22**. Se estiver em **24.1.0–24.1.21, 24.2.0–24.2.20 ou 26.1.0–26.1.4**, alerte primeiro: **CVE-2026-101521**, CVSS 9.8, tomada do APEX **sem autenticação via HTTPS** (Oracle CPU out/2026). O advisory não nomeia a versão que corrige: oriente aplicar o Patch Set Bundle mais recente da versão e conferir o documento CPU359 da Oracle Support.
- **APEX_DICTIONARY:** ponto de entrada para descoberta de qualquer view de metadados APEX.
- **Consciência de versão:** features divergem entre 24.1, 24.2, 26.1 e 26.2. Antes de gerar código que dependa de versão (IA no app, APEXlang, Select One/Many, Slots, Workflow/Working Copy, session state BOOLEAN, Universal Theme Iris), confirme a versão-alvo — ver regra abaixo. Consulte `references/apex-version-matrix-ptbr.md` para o que é exclusivo de cada release.

## Distinção de versão (24 vs 26)

A versão atual é o **APEX 26.2** (GA em 06/10/2026; exige **ORDS 26.3.0+** e
**SQLcl 26.3.0+**; banco 19c com RU 19.18+ ou 26ai 23.26.0+). A **26.1**
(14/05/2026) segue suportada e a **24.2** é a **baseline suportada** da suíte —
sempre no patch set mais recente (24.2.22 em 04/11/2026; ver alerta de
segurança acima). Datas de fim de suporte: a verificar. Resumo do que é
exclusivo (detalhe, fontes e 26.2 em `references/apex-version-matrix-ptbr.md`):

**Novo no 26.2:** APEXlang com import por arquivo (SQLcl/VS Code, só dev),
traduções e subscription mapping no APEXlang, APIs `APEX_APPLICATION_ADMIN`
de lock e Working Copy, IA com reasoning effort, colunas por linguagem natural
no IR e navigation targets, Deep Data Security (banco 23.26.3+). **Removido no
26.2:** REST Workshop do SQL Workshop — APIs REST pelo SQL Developer Web; os
serviços REST existentes continuam funcionando.

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
curta ("Para qual versão do APEX — 24.2, 26.1 ou 26.2, com patch set — e, se for o caso, qual
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
