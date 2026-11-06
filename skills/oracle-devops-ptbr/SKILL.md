---
name: oracle-devops-ptbr
description: Módulo DevOps da suíte Oracle PT-BR. Estrutura Git e CI/CD para projetos Oracle/APEX/ORDS. ATIVE em estrutura de projeto Oracle no Git, commit de objetos do banco, script de deploy, GitHub Actions ou Azure Pipelines para Oracle, export APEX split via SQLcl, versionamento de módulos ORDS, GMUD naming (001_projeto_ddl_objeto.sql), deploy-db/deploy-apex/deploy-ords, branch strategy, .gitignore Oracle, rollback, ordem de dependências, changelog Liquibase XML (databaseChangeLog/changeSet), code review e promoção entre ambientes via GitHub/Azure. Frases — "estruturar projeto no Git", "script de deploy Oracle", "export do APEX para Git", "deploy ordenado do banco", "nomenclatura GMUD", "changelog Liquibase", "pipeline Azure DevOps", "deploy com aprovação por ambiente", "enviar para homologação/produção". NÃO ATIVE em código PL/SQL (oracle-plsql-ptbr), APEX pages (oracle-apex-ptbr), ORDS handlers (oracle-ords-ptbr), DBA operacional (oracle-dba-ptbr), tuning (oracle-tuning-ptbr). Templates em assets/.
metadata:
  version: "3.6.2"
  release_date: "2026-09-15"
  repository: "https://github.com/maxwbh/oracle-skills-ptbr"
  suite_size: 30
  author: "Maxwell da Silva Oliveira"
  contact: "contato@msbrasil.inf.br"
  organization: "M&S do Brasil LTDA"
  site: "https://msbrasil.inf.br"
  tags:
    - "oracle"
    - "devops"
    - "cicd"
    - "git"
    - "github-actions"
    - "changelog"
    - "oracledb"
    - "python"
    - "deployment"
  category: "devops"
  language: "pt-BR"
  icon: "⚙️"
---

# Suíte Oracle PT-BR — Módulo DevOps (oracle-devops-ptbr)

> **Versão:** 3.6.2 · **Atualizada em:** setembro/2026 · **Repositório:** oracle-skills-ptbr · **Suíte:** 10 skills (30 recursos nesta skill)
> **v3.6.2:** suíte com 10 skills; referência cruzada para o lab local como ambiente de teste do pipeline. Histórico em `CHANGELOG.md`.

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


Estrutura Git, scripts de deploy e CI/CD para projetos Oracle 19c + APEX 24.2/26.1 + ORDS.

**Desenvolvido por:** Maxwell da Silva Oliveira — [M&S do Brasil LTDA](https://msbrasil.inf.br)

## Áreas cobertas

| Área | Reference | Assets |
|---|---|---|
| **Estrutura Git e Changelog** | `references/git-project-structure-ptbr.md` | `oracle_devops_utils.py`, `apply_changelog.py`, `deploy_full.py`, `deploy_db.py`, `deploy_ords.py`, `export_db.py`, `export_ords.py`, `export_apex.py` |
| **Liquibase, code review e deploy GMUD por ambiente** | `references/liquibase-cicd-gmud-ptbr.md` | `setup_devops.py`, `changelog-master.xml`, `changelog-release-exemplo.xml`, `github-deploy-liquibase.yml`, `azure-pipelines-liquibase.yml`, `gmud_liquibase.py` |
| **Templates e configuração** | — | `module_template.sql`, `changelog_template.yml`, `github-deploy.yml`, `gitignore-oracle.txt`, `requirements-devops.txt` |

## Quando ativar

- Estrutura de diretórios para projeto Oracle/APEX/ORDS no Git
- Nomenclatura de arquivos de deploy (padrão GMUD: `001_projeto_ddl_objeto.sql`)
- Scripts de deploy Python: `deploy_full.py` (orquestrador), `deploy_db.py`, `deploy_ords.py`
- Export APEX split via SQLcl (`apex export -split`)
- Export de módulos ORDS via `ORDS_EXPORT.export_schema()`
- Versionamento de módulos ORDS (`clientes_v1/`, `clientes_v2/`)
- Branch strategy (`main` / `hml` / `develop` / `feature/*`) — `hml` é o nome canônico da suíte para homologação; o fluxo legado (changelog.yml, `github-deploy.yml`, scripts `deploy_*.py`) usa `hom`
- GitHub Actions ou Azure DevOps Pipelines para Oracle/APEX/ORDS (CI-agnóstico)
- Escolha do combo CI/CD (Git/Azure/Manual) × Liquibase (sim/não) — assistente `setup_devops.py`
- Deploy GMUD via Liquibase (changelog XML real, `databaseChangeLog`/`changeSet`)
- Code review e promoção entre ambientes (Aprovar/Reprovar/Enviar p/ HML/Enviar p/ PRD) com GitHub Environments protegidos
- Ordem de execução por changelog (estilo Liquibase) e rollback por tag de release
- `.gitignore` para projetos Oracle
- `.gitattributes` (encoding UTF-8, LF)
- Ordem de deploy de objetos do banco (sequences → tables → packages → triggers)
- Gestão de environments (dev / hom / prod) sem credenciais em código
- Exportar DDL atual do banco para Git (baseline de projeto legado, sync após alteração direta)
- Changelog de banco: migrations ordenadas (changelog.yml + db_changelog), apply_changelog.py com --dry-run/--status, checksum SHA-256, detecção de drift entre ambientes

**Não usar** para: código PL/SQL (→ oracle-plsql-ptbr), APEX pages (→ oracle-apex-ptbr), ORDS handlers (→ oracle-ords-ptbr), DBA ops (→ oracle-dba-ptbr), tuning (→ oracle-tuning-ptbr).

## Estrutura canônica de projeto

```
meu-projeto-apex/
├── .gitignore            ← assets/gitignore-oracle.txt
├── db/
│   ├── tables/           ← DDL de tabelas
│   ├── views/
│   ├── packages/         ← .pks (spec) e .pkb (body) separados
│   ├── procedures/       ← .prc
│   ├── functions/        ← .fnc
│   ├── triggers/         ← .trg (sempre compound)
│   └── scripts/          ← 001_projeto_tipo_objeto.sql (GMUD)
├── apex/
│   └── app_100/
│       ├── install.sql   ← import manual (CI roda f100/install.sql)
│       └── f100/         ← export split (SQLcl)
├── ords/
│   ├── modules/
│   │   ├── clientes_v1/  ← module.sql + templates.sql +
│   │   └── clientes_v2/     handlers.sql + privileges.sql
│   ├── security/
│   └── scripts/          ← (wrappers shell — chamam os .py)
├── scripts/
│   ├── deploy_full.py    ← orquestrador (changelog → apex → ords)
│   ├── deploy_db.py      ← deploy objetos banco em ordem
│   ├── deploy_ords.py    ← deploy módulos ORDS
│   ├── apply_changelog.py← migrations do changelog.yml
│   ├── export_db.py      ← extrai DDL do banco → db/
│   ├── export_apex.py    ← export split APEX via SQLcl
│   ├── export_ords.py    ← export schema ORDS
│   ├── oracle_devops_utils.py  ← módulo compartilhado
│   └── requirements-devops.txt
└── .github/workflows/
    └── deploy.yml        ← assets/github-deploy.yml
```

## Padrão GMUD — nomenclatura de scripts

```
{sequencia}_{projeto}_{tipo}_{objeto}.sql

001_msbrasil_ddl_tb_clientes.sql
002_msbrasil_ddl_pk_clientes.sql
003_msbrasil_pkg_clientes.sql
004_msbrasil_page_54_cadastro_v1.sql
```

Tipos: `ddl` `dml` `pkg` `prc` `fnc` `trg` `vw` `page` `fix`

## Ordem de deploy de objetos do banco

```
sequences → types → tables → constraints → FK → indexes →
grants → synonyms → views → package specs (.pks) →
package bodies (.pkb) → procedures → functions → triggers →
APEX → ORDS
```

Implementado em `assets/deploy_db.py` (subdiretórios `db/constraints/`, `db/fk/`, `db/indexes/` são opcionais — se ausentes, são pulados).

## Assets disponíveis

| Arquivo | Tipo | Descrição |
|---|---|---|
| **Módulo compartilhado** | | |
| `oracle_devops_utils.py` | Python | `conectar()` (DB_SCHEMA), `executar_script_sqlcl()` / `executar_e_verificar()` (SQLcl + `ALL_ERRORS`), `validar_arquivo_sql()` / `split_oracle_sql()` (tokenizador), `confirmar_producao()`, `checksum_sha256()` |
| **Scripts Python — uso direto** | | |
| `apply_changelog.py` | Python | Lê `db/changelog.yml`, aplica migrations pelo SQLcl com status `EM_ANDAMENTO`/`APLICADA`/`ERRO`. CLI: `--env`, `--dry-run`, `--status`, `--retomar`, `--marcar-resolvida`, `--confirmar-prod` |
| `deploy_full.py` | Python | Orquestrador: changelog → APEX (export split pelo SQLcl, workspace/app id validados) → ORDS. Suporta `--skip-db/apex/ords` |
| `deploy_db.py` | Python | Deploy ordenado: sequences → types → tables → package specs → bodies → triggers |
| `deploy_ords.py` | Python | Deploy ORDS: security → privileges → módulos. Verifica `USER_ORDS_MODULES` pós-deploy |
| `export_db.py` | Python | Extrai DDL via `DBMS_METADATA.GET_DDL()` → `db/` (.pks/.pkb/.vw/.trg...) |
| `export_ords.py` | Python | Export via `ORDS_EXPORT.export_schema()` — lê CLOB nativo via oracledb |
| `export_apex.py` | Python | Export split APEX via SQLcl subprocess — backup automático, gera `install.sql` para import manual |
| **Wrappers shell (compatibilidade CI/CD)** | | |
| `apply-changelog.sh` | Shell | `exec python3 apply_changelog.py "$@"` |
| `deploy-full.sh` | Shell | `exec python3 deploy_full.py "$@"` |
| `deploy-db.sh` | Shell | `exec python3 deploy_db.py "$@"` |
| `deploy-ords.sh` | Shell | `exec python3 deploy_ords.py "$@"` |
| `export-db.sh` | Shell | `exec python3 export_db.py "$@"` |
| `export-apex.sh` | Shell | `exec python3 export_apex.py "$@"` |
| `export-ords.sh` | Shell | `exec python3 export_ords.py "$@"` |
| **Configuração e templates** | | |
| `requirements-devops.txt` | Config | `oracledb>=2.0.0`, `PyYAML>=6.0.0` |
| `changelog_template.yml` | Template | Copiar para `db/changelog.yml` do projeto |
| `create-changelog-table.sql` | SQL | DDL idempotente da tabela `db_changelog` |
| `module_template.sql` | SQL | Template completo de módulo ORDS (module + templates + handlers + privileges) |
| `gitignore-oracle.txt` | Config | Copiar como `.gitignore` na raiz do projeto |
| `github-deploy.yml` | CI/CD | GitHub Actions (fluxo Python) — Environments `dev`/`hom`/`prod`, `DB_PASS` por ambiente, aprovação obrigatória em prod, validação offline, deploy pelo SQLcl |
| **Liquibase e CI-agnóstico (recomendado)** | | |
| `setup_devops.py` | Python | Assistente interativo (ou `--ci git|azure|manual --liquibase sim|não`) que gera o esqueleto do combo escolhido, sem conectar no banco |
| `gmud_liquibase.py` | Python | Gera `changelog-master.xml` a partir das releases e invoca liquibase/SQLcl/script |
| `changelog-master.xml` | Liquibase | `databaseChangeLog` mestre — inclui os changelogs de release |
| `changelog-release-exemplo.xml` | Liquibase | Exemplo de release com `changeSet`, `sqlFile`, `runOnChange`, `context`, `rollback`, `tagDatabase` |
| `github-deploy-liquibase.yml` | CI/CD | GitHub Actions com Environments protegidos dev/hml/prd como approval gates; credenciais via `LIQUIBASE_COMMAND_*` |
| `azure-pipelines-liquibase.yml` | CI/CD | Azure DevOps — stages dev/hml/prd com deployment jobs + Approvals and checks |

## Referências cruzadas

| Precisa de | Skill |
|---|---|
| Código PL/SQL nos packages de `db/packages/` | **oracle-plsql-ptbr** |
| Nomenclatura Trivadis no código | **oracle-trivadis-ptbr** |
| Handlers e módulos em `ords/modules/` | **oracle-ords-ptbr** |
| Pages e components em `apex/` | **oracle-apex-ptbr** |
| DBA ops durante deploy | **oracle-dba-ptbr** |
| Query lenta pós-deploy | **oracle-tuning-ptbr** |
| Scripts GMUD com `IF NOT EXISTS` (19.28+/26ai) | **oracle-26ai-ptbr** |
| Montar o ambiente local usado como alvo de teste do pipeline | **oracle-lab-ptbr** |
