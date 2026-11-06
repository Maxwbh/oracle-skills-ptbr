---
name: oracle-ords-ptbr
description: Módulo ORDS da suíte Oracle PT-BR. Oracle ORDS — REST services e dicionário USER_ORDS_*/DBA_ORDS_*. ATIVE em define_module, define_template, define_handler, AutoREST, OAuth, ORDS_SECURITY, ORDS_SECURITY_ADMIN, JWT, PAR via ORDS_PAR, ORDS_EXPORT_ADMIN, delete_module/drop_rest_for_schema, privilege, role ORDS, ORDS_EXPORT, USER_ORDS_MODULES, USER_ORDS_HANDLERS, USER_ORDS_SCHEMAS, DBA_ORDS_*, source_type_collection_feed, source_type_collection_item, CORS, versionamento de API, depreciação OAUTH package. Frases — "criar endpoint REST", "módulo ORDS", "autenticar API", "inventário de handlers ORDS", "OAUTH deprecated". NÃO ATIVE em APEX pages, PL/SQL puro, DBA operacional. Templates em assets/.
metadata:
  version: "2.4.0"
  release_date: "2026-09-15"
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

> **Versão:** 2.4.0 · **Atualizada em:** setembro/2026 · **Repositório:** oracle-skills-ptbr · **Suíte:** 10 skills (6 recursos nesta skill)
> **v2.4.0:** linha do tempo ORDS 24.3→26.4 (25.1 ORDS_EXPORT_ADMIN, 25.3 remoção do OAUTH, 26.1 export com DROP, 26.1.1 para APEX 26.1, 26.4 Tomcat 10) e limpeza de metadata. Histórico em `CHANGELOG.md`.

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


Oracle REST Data Services — padrões de desenvolvimento e dicionário completo de views de metadados.

**Desenvolvido por:** Maxwell da Silva Oliveira — [M&S do Brasil LTDA](https://msbrasil.inf.br)

## Áreas cobertas

| Área | Reference | Assets |
|---|---|---|
| **REST services** | `references/ords-rest-services.md` | `ords_module.sql`, `ords_handler.sql` |
| **Network ACL** | — | `network_acl_setup.sql` (DBMS_NETWORK_ACL_ADMIN — pré-requisito para UTL_HTTP/APEX_WEB_SERVICE; sem ACL: ORA-24247) |
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
| **26.4** (previsto inverno/2026) | Passa a exigir **Tomcat 10 / WebLogic 15** | Tomcat 9 deixa de servir — planejar o servidor de aplicação junto |

Enquanto o ORDS for 26.1–26.3, **Tomcat 9.0.x** continua sendo o correto: a Oracle pede explicitamente para não antecipar a migração para o Tomcat 10. Java suportado: **17 ou 21** (Oracle JDK ou GraalVM; GraalVM só é obrigatório para GraphQL).

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
