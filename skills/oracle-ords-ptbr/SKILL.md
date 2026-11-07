---
name: oracle-ords-ptbr
description: Módulo ORDS da suíte Oracle PT-BR. Oracle ORDS — REST services e dicionário USER_ORDS_*/DBA_ORDS_*. ATIVE em define_module, define_template, define_handler, AutoREST, OAuth, ORDS_SECURITY, ORDS_SECURITY_ADMIN, JWT, PAR via ORDS_PAR, ORDS_EXPORT_ADMIN, delete_module/drop_rest_for_schema, privilege, role ORDS, ORDS_EXPORT, USER_ORDS_MODULES, USER_ORDS_HANDLERS, USER_ORDS_SCHEMAS, DBA_ORDS_*, source_type_collection_feed, source_type_collection_item, CORS, versionamento de API, depreciação OAUTH package. Frases — "criar endpoint REST", "módulo ORDS", "autenticar API", "inventário de handlers ORDS", "OAUTH deprecated". NÃO ATIVE em APEX pages, PL/SQL puro, DBA operacional. Templates em assets/.
metadata:
  version: "2.5.2"
  release_date: "2026-11-07"
  repository: "https://github.com/maxwbh/oracle-skills-ptbr"
  suite_size: 6
  author: "Maxwell da Silva Oliveira"
  contact: "contato@msbrasil.inf.br"
  organization: "M&S do Brasil LTDA"
  site: "https://msbrasil.inf.br"
  tags:
    - "oracle"
    - "ords"
    - "rest-api"
    - "oauth"
    - "autorest"
    - "jwt"
    - "openapi"
  category: "development"
  language: "pt-BR"
  icon: "🌐"
---

# Suíte Oracle PT-BR — Módulo ORDS (oracle-ords-ptbr)

> **Versão:** 2.5.2 · **Atualizada em:** novembro/2026 · **Repositório:** oracle-skills-ptbr · **Suíte:** 10 skills (6 recursos nesta skill)
> **v2.5.2:** APEX 26.2 como padrão; Network ACL do APEX 26.2 no schema APEX_260200. Histórico em `CHANGELOG.md`.

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


Oracle REST Data Services — padrões de desenvolvimento e dicionário completo de views de metadados.

**Desenvolvido por:** Maxwell da Silva Oliveira — [M&S do Brasil LTDA](https://msbrasil.inf.br)

## Áreas cobertas

| Área | Reference | Assets |
|---|---|---|
| **REST services** | `references/ords-rest-services.md` | `ords_module.sql`, `ords_handler.sql` |
| **Network ACL** | — | `network_acl_setup.sql` (DBMS_NETWORK_ACL_ADMIN — pré-requisito para UTL_HTTP/APEX_WEB_SERVICE; sem ACL: ORA-24247. E-mail/REST/LDAP do próprio APEX 26.2: conceder ao schema `APEX_260200`) |
| **ORDS Data Dictionary** | `references/ords-data-dictionary-ptbr.md` | (queries embutidas no reference) |

## Quando ativar

- `ORDS.define_module`, `ORDS.define_template`, `ORDS.define_handler`
- `ORDS.enable_schema`, `ORDS.enable_object` (AutoREST)
- `ORDS_SECURITY.create_client`, `ORDS_SECURITY_ADMIN.*` (24.3+)
- `OAUTH.*` ou `OAUTH_ADMIN.*` → alertar depreciação (removidos em ORDS 25.3)
- `ORDS_PAR` — Pre-Authenticated Requests (24.4+)
- `ORDS_EXPORT_ADMIN` — exportar configuração de outro schema (25.1+, requer `ORDS_ADMINISTRATOR_ROLE`)
- `ORDS.delete_module`, `ORDS.delete_template`, `ORDS.delete_handler` (25.3+), `ORDS.drop_rest_for_object`, `ORDS.drop_rest_for_schema` — limpeza de metadata
- `ORDS_EXPORT.export_schema` — backup/deploy de configuração
- `USER_ORDS_MODULES`, `USER_ORDS_HANDLERS`, `USER_ORDS_SCHEMAS`
- `DBA_ORDS_*` (requer `ORDS_ADMINISTRATOR`) — ORDS 24.4+
- Source types: `collection/query`, `collection/item`, `plsql/block`, `mle/javascript`
- CORS, códigos HTTP REST, versionamento de API, OAuth 2.0
- JWT Profiles, `USER_ORDS_JWT_PROFILE`

**Não usar** para: APEX pages/regions, PL/SQL puro sem REST, DBA ops.

## Princípios canônicos

- **Hierarquia ORDS:** Schema → Module → Template → Handler → Parameter.
- **Bind variables sempre:** path params (`:id`), query string (`:status`) são bind automático. SQL dinâmico → `DBMS_ASSERT`.
- **Source type correto:** lista paginada → `source_type_collection_feed` (`collection/query`). Um item → `source_type_collection_item` (`collection/item`). Lógica complexa → `source_type_plsql` (`plsql/block`). BLOB → `source_type_media` (`media/blob`).
- **Autenticação obrigatória** em qualquer endpoint que acesse dado sensível — `ORDS.define_privilege` + role.
- **OAUTH depreciado em 24.3:** migrar para `ORDS_SECURITY` / `ORDS_SECURITY_ADMIN`. Removido em ORDS 25.3.
- **Versionamento no path:** `/recurso/v1/` e `/recurso/v2/` — não via query string.
- **DBA_ORDS_*:** visão cross-schema (ORDS 24.4+). Requer role `ORDS_ADMINISTRATOR`.
- **ORDS_EXPORT:** use para CI/CD e backup de configuração. A partir do **ORDS 26.1** o export também gera `DROP` para módulos, privilégios e roles apagados na origem — o arquivo passa a ser idempotente de verdade, e um deploy do export remove o que foi removido. Confira isso antes de aplicar em ambiente com configuração feita à mão.
- **Limpar é diferente de desabilitar:** `ORDS.drop_rest_for_object` apenas **desabilita** o objeto; `ORDS.delete_module` apaga um módulo; `ORDS.drop_rest_for_schema` apaga toda a configuração REST do schema. Sempre `commit` depois.

## Linha do tempo das versões (o que vale hoje)

| Versão | O que mudou | Impacto na suíte |
|---|---|---|
| 24.3 | `ORDS_SECURITY` / `ORDS_SECURITY_ADMIN`; `OAUTH`/`OAUTH_ADMIN` **depreciados** | Código novo já nasce em `ORDS_SECURITY` |
| 24.4 | `ORDS_PAR` (pre-authenticated requests); `DBA_ORDS_*`; bind `:body_json` | Inventário cross-schema e links temporários |
| 25.1 | `ORDS_EXPORT_ADMIN` (exportar outro schema); JWT com claims/roles | Export centralizado no pipeline |
| **25.3** (out/2025) | `OAUTH`/`OAUTH_ADMIN` **removidos** — chamadas passam a dar erro; `ORDS.DELETE_TEMPLATE`/`DELETE_HANDLER` | Cliente que ainda usa OAuth antigo **quebra** ao subir o ORDS |
| **26.1** | Export gera `DROP` de objetos removidos; VecDB REST APIs (exigem banco 23.26.1+) | Muda o comportamento do `export_ords.py` (`oracle-devops-ptbr`) |
| **26.1.1** | Exigido pelo **APEX 26.1** e pelo suporte a APEXlang | APEX 26.1 com ORDS menor que isso não é suportado |
| **26.3.0** (out/2026) | Exigido pelo **APEX 26.2** (e pelo APEXlang com ele) | APEX 26.2 com ORDS menor que 26.3.0 não é suportado |
| **26.3.1** (04/11/2026) | Versão mais recente em 06/11/2026 | Alvo de atualização (ver segurança abaixo) |
| **26.4** (planejado "Winter 2026", ainda não lançado) | Passa a suportar **Tomcat 10 / WebLogic 15** e deixa de rodar em Tomcat 9 e WebLogic 14 | Planejar o servidor de aplicação junto; **standalone (Jetty embutido) não é afetado** |

Fontes (06/11/2026): [ORDS changelog](https://www.oracle.com/tools/ords/ords-changelog.html), [página de download](https://www.oracle.com/database/sqldeveloper/technologies/db-actions/download/), [release notes APEX 26.2](https://docs.oracle.com/en/database/oracle/apex/26.2/htmrn/about-release-notes.html).

**Par APEX × ORDS (mínimo exigido pela doc do APEX):** APEX 26.1 → ORDS **26.1.1+**; APEX 26.2 → ORDS **26.3.0+**. Ao subir o APEX, confira primeiro o ORDS; em instalação nova a Oracle recomenda instalar o ORDS antes do APEX.

Enquanto o ORDS for 26.1–26.3, **Tomcat 9.0.x** (ou WebLogic 14.1.2) continua sendo o correto — a doc do 26.3 lista exatamente esses — e a Oracle pede para não migrar antes do 26.4 sair. Java suportado: **17 ou 21** (Oracle JDK ou GraalVM; GraalVM só é obrigatório para GraphQL).

### Segurança — CPU de outubro/2026

O [CPU de out/2026](https://www.oracle.com/security-alerts/cpuoct2026.html) traz **35 CVEs do ORDS** (11 exploráveis sem autenticação), faixa geral **24.2.0–26.2.2**. As mais graves: **CVE-2026-91610** (CVSS 8.8, "takeover of Oracle REST Data Services", usuário com privilégio baixo, 24.2.0–26.2.2), CVE-2026-33941 (8.2, Database Actions), CVE-2026-9753 (8.1) e CVE-2026-101494 (7.7). O advisory não nomeia a versão que corrige: atualize para o **ORDS mais recente** (26.3.1 em 06/11/2026) e confira o documento de patches do CPU na Oracle Support.

### O que é do APEX e o que é do ORDS

| Recurso | Dono | Situação (06/11/2026) |
|---|---|---|
| *RESTful Services* do SQL Workshop (REST Workshop) | **APEX** (tela dentro do App Builder) | Deprecated no APEX 26.1, **removido no 26.2**. Import/export legado e serviços de exemplo saíram; `APEX_REST_RESOURCE_*` ficam sem dados do Workshop |
| Módulos, templates e handlers REST | **ORDS** (metadados no banco, API `ORDS.*`) | **Continuam funcionando** — nada muda para quem já tem serviços |
| Definir APIs REST por tela | **SQL Developer Web / Database Actions** (vem com o ORDS) | Caminho recomendado; o APEX 26.2 abre o REST Designer a partir do App Builder |
| Definir APIs REST por código / CI | **ORDS** — `ORDS.define_*`, `ORDS_EXPORT` / `ORDS_EXPORT_ADMIN` | Caminho da suíte (assets desta skill + `oracle-devops-ptbr`) |
| `APEX_LISTENER` | APEX | Instalação nova do 26.2 não cria mais |
| Swagger UI URL (configuração de instância) | APEX | Removida no 26.2 |

A depreciação da tela do APEX já vinha anunciada nas [release notes do ORDS 25.1](https://www.oracle.com/tools/ords/ords-relnotes-25.1.html), que indicam o SQL Developer Web como interface recomendada.

## Referências cruzadas

| Precisa de | Skill |
|---|---|
| PL/SQL dentro de handler (packages, lógica) | **oracle-plsql-ptbr** |
| Naming e prefixos Trivadis no código | **oracle-trivadis-ptbr** |
| APEX consumindo endpoints ORDS | **oracle-apex-ptbr** |
| V$SESSION, locks, DBA operacional | **oracle-dba-ptbr** |
| Query lenta no handler | **oracle-tuning-ptbr** |
| Instalar ORDS/Tomcat no ambiente local | **oracle-lab-ptbr** |
| Pipeline que aplica o export ORDS entre ambientes | **oracle-devops-ptbr** |
