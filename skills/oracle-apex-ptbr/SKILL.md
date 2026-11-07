---
name: oracle-apex-ptbr
description: Módulo APEX da suíte Oracle PT-BR. Oracle APEX 26.2 como versão padrão (compatível com 24.2+) — desenvolvimento e dicionário de metadados. ATIVE em Dynamic Actions, Interactive Report, Interactive Grid, Classic Report, Page Process, AJAX Callback, Validations, Authorization Schemes, pagination, LOV, APEX_APPLICATION_*, APEX_APPLICATION_PAGE_*, APEX_WORKSPACE_*, APEX_APPL_*, Workflows, Tasks, AI configs, ACL, JSON Sources, APEX_ACTIVITY_LOG. Frases — "página APEX", "region IR", "IG editável", "process no submit", "qual view APEX usar", "auditar paginação APEX". NÃO ATIVE em PL/SQL puro, ORDS endpoints, DBA operacional. Para naming use oracle-trivadis-ptbr. Templates em assets/.
metadata:
  version: "2.7.0"
  release_date: "2026-11-07"
  repository: "https://github.com/maxwbh/oracle-skills-ptbr"
  suite_size: 21
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

> **Versão:** 2.7.0 · **Atualizada em:** novembro/2026 · **Repositório:** oracle-skills-ptbr · **Suíte:** 10 skills (21 recursos nesta skill)
> **v2.7.0:** APEX 26.2 como versão padrão (código sai para 26.2 salvo versão declarada; 24.2 é a mínima); mudanças de comportamento, deprecated e desupported do 26.2. Histórico em `CHANGELOG.md`.

Suíte completa (10 skills — conjunto único):
- **oracle-core-ptbr** — roteamento central, convenções transversais, cenários multidisciplinares
- **oracle-plsql-ptbr** — PL/SQL 19c: packages, BULK, LOBs, triggers, EBR
- **oracle-trivadis-ptbr** — Trivadis 4.4: naming, prefixos, revisão de código
- **oracle-apex-ptbr** — APEX 26.2 (padrão; compatível com 24.2+): páginas, DA, IG, APIs APEX_*, metadata
- **oracle-ords-ptbr** — ORDS: REST modules/handlers, OAuth, Network ACL
- **oracle-dba-ptbr** — DBA operacional: sessões, locks, flashback, scripts ad-hoc
- **oracle-tuning-ptbr** — performance: explain plan, índices, stats, result cache
- **oracle-devops-ptbr** — Git/CI-CD: estrutura, Liquibase, pipelines, GMUD
- **oracle-26ai-ptbr** — 23ai/26ai: novidades SQL/PL/SQL, backports 19.28, migração 19c→26ai (só com versão declarada)
- **oracle-lab-ptbr** — instalação e ambiente local (VM/container) para quem não é DBA; rede de casa

> Fora da suíte (repositório separado): **oracle-26ai-helper-ptbr** — Vector Search, JSON Relational Duality, RAFT (replicação do Globally Distributed Database) e roteiro do upgrade 19c→26ai. Roteamento: Vector / Duality / RAFT e roteiro do upgrade (fases, riscos, Vector Pool na janela) → **oracle-26ai-helper-ptbr**; sintaxe nova e checklist de código da migração (o que muda, caminhos, compatibilidade APEX/ORDS/SQLcl) → **oracle-26ai-ptbr**; operação do upgrade (AutoUpgrade, PDB, Data Guard) → **oracle-dba-ptbr**.


Oracle APEX **26.2 é a versão padrão** — todo código e orientação saem para 26.2, salvo versão declarada; a skill continua cobrindo 26.1 e 24.2 (versão mínima). Padrões de desenvolvimento e dicionário completo de views de metadados.

**Desenvolvido por:** Maxwell da Silva Oliveira — [M&S do Brasil LTDA](https://msbrasil.inf.br)

## Áreas cobertas

| Área | Reference | Assets |
|---|---|---|
| **Padrões APEX (26.2; compatível com 24.2+)** | `references/apex-patterns.md` | `apex_dynamic_action.sql`, `apex_pagination_pattern.sql`, `apex_pl_sql_process.sql`, `apex_long_running_job.sql`, `apex_interactive_grid.sql`, `apex_blob_upload_download.sql`, `apex_json_source.sql` |
| **APIs PL/SQL APEX (aprofundamento)** | — | `apex_util_reference.sql`, `apex_collection_reference.sql`, `apex_application_global.sql`, `apex_json_reference.sql`, `apex_debug_patterns.sql`, `apex_item_legacy.sql` |
| **Autenticação custom** | — | `apex_authentication_custom.sql` (custom scheme, sentry, OIDC, HTTP Header) |
| **Universal Theme** | — | `universal_theme_patterns.sql` (classes t-/u-, tokens --ut-*, dark mode) |
| **Auditoria via metadata** | `references/apex-data-dictionary-ptbr.md` | `apex_metadata_queries.sql` (linter caseiro, pre-deploy validation) |
| **Segurança — patch level (CPU out/2026)** | `references/apex-version-matrix-ptbr.md` (seção Segurança) | `apex_verificar_patch_seguranca.sql` (classifica a versão instalada contra CVE-2026-101521 e CVE-2026-66010) |
| **Matriz de versões (24.2, 26.1, 26.2)** | `references/apex-version-matrix-ptbr.md` | (tabela embutida no reference) |

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
- **Versão padrão 26.2:** sem versão declarada, gere para **APEX 26.2** (banco 19c, na dúvida) e diga a suposição em uma linha. Se o recurso não existir em 24.2/26.1, aponte a alternativa — ver regra abaixo e `references/apex-version-matrix-ptbr.md`.

## Versão padrão: APEX 26.2

A suíte gera para o **APEX 26.2** (GA em 06/10/2026, patch set 26.2.1). Requisitos:
**ORDS 26.3.0+**, **SQLcl 26.3.0+** e banco **19c com RU 19.18+** ou **26ai
23.26.0+**; schema `APEX_260200`; instalação nova com ORDS antes do APEX. A
**26.1** (14/05/2026) e a **24.2** (versão mínima coberta, sempre no patch set
mais recente — 24.2.22 em 04/11/2026) continuam atendidas quando declaradas.
Datas de fim de suporte: a verificar. Detalhe e fontes em
`references/apex-version-matrix-ptbr.md`.

**Regra — versão-alvo:**
1. **Versão declarada** (ex.: "estou no 24.2") → use-a e não pergunte de novo.
2. **Nada declarado** → gere para **26.2** e diga em uma linha: "Considerei APEX
   26.2; em 24.2/26.1 troque X por Y" quando o recurso for 26.x.
3. **Instância existente** (app de cliente, upgrade, incidente) → pergunte a
   versão completa com patch set antes de orientar — o patch level importa
   (alerta de segurança acima).
4. **Recurso que depende do banco** — session state BOOLEAN (26ai) e Deep Data
   Security (26ai 23.26.3+) — **não entra no padrão**: o banco padrão é 19c.
   Só gere com o banco 26ai declarado.

**O que o padrão 26.2 muda na prática:**
- APIs REST: o REST Workshop do SQL Workshop foi **removido** — defina APIs pelo
  SQL Developer Web/ORDS (`oracle-ords-ptbr`); serviços existentes continuam.
- Source control: **APEXlang** (`.apx`) é o formato preferido; o import por
  arquivo (`apex import -files`) existe só no SQLcl/VS Code e só em
  desenvolvimento — produção importa a aplicação inteira (`oracle-devops-ptbr`).
- Lock e Working Copy por API: `APEX_APPLICATION_ADMIN.LOCK_APPLICATION`,
  `UNLOCK_APPLICATION`, `CREATE_WORKING_COPY`.
- IA: `p_reasoning_effort` em `APEX_AI.CHAT`/`GENERATE`, colunas calculadas
  por linguagem natural no IR, navigation targets no AI Request Handler.

| Recurso | 24.2 | 26.1 | 26.2 (padrão) |
|---|:---:|:---:|:---:|
| IR, IG, Classic Report, DA, `APEX_ERROR`/`APEX_JSON`/`APEX_COLLECTION` | ✅ | ✅ | ✅ |
| Workflow + Working Copy (23.2), Execution Chain em background (23.1) | ✅ | ✅ | ✅ |
| `APEX_AI` chat/generate, Select One/Many, Slots (24.1) | ✅ | ✅ | ✅ |
| JSON Sources, RAG declarativo, vector search (24.2; vetor exige 23ai+) | ✅ | ✅ | ✅ |
| APEXlang (`.apx`) export/import da aplicação inteira | — | ✅ | ✅ |
| AI Interactive Reports, AI Agents, Data Reporter | — | ✅ | ✅ |
| Universal Theme "Iris", Font APEX 2.5, partials client-side, Workflow Parallel Flow | — | ✅ | ✅ |
| Session state BOOLEAN (**banco 26ai**) | — | ✅ | ✅ |
| APEXlang: import por arquivo, traduções, subscription mapping | — | — | ✅ |
| APIs de lock/Working Copy em `APEX_APPLICATION_ADMIN` | — | — | ✅ |
| IA: reasoning effort, colunas por linguagem natural no IR, navigation targets | — | — | ✅ |
| Deep Data Security (**banco 26ai 23.26.3+**) | — | — | ✅ |
| REST Workshop (*RESTful Services* do SQL Workshop) | ✅ | deprecated | **removido** |

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
