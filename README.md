# oracle-skills-ptbr

**Skills Claude para Oracle — Stack Completa em Português**

10 Skills do Claude cobrindo toda a stack Oracle (roteamento central, PL/SQL, APEX, ORDS, DBA, Performance, Trivadis Guidelines, DevOps/CI-CD, ambiente local e novidades 23ai/26ai), desenvolvidas pela **M&S do Brasil LTDA** para uso profissional em projetos Oracle 19c + APEX 24.2–26.2 + ORDS.

---

## Desenvolvedor

**Maxwell da Silva Oliveira**  
M&S do Brasil LTDA — [msbrasil.inf.br](https://msbrasil.inf.br)  
✉ contato@msbrasil.inf.br · 🐙 [@maxwbh](https://github.com/maxwbh)

---

## Skills disponíveis

| Skill | Versão | Escopo | Recursos |
|---|---|---|---|
| `oracle-core-ptbr` | 1.5.0 | Assistente central — roteamento entre os módulos e convenções transversais | 2 |
| `oracle-plsql-ptbr` | 3.0.1 | PL/SQL 19c, packages, LOBs, EBR, triggers, Logger | 11 |
| `oracle-apex-ptbr` | 2.6.0 | APEX (padrões de 24.2+) development + Data Dictionary completo | 21 |
| `oracle-ords-ptbr` | 2.5.0 | ORDS REST services + Data Dictionary (USER/DBA_ORDS_*) | 6 |
| `oracle-dba-ptbr` | 2.4.0 | DBA operacional + Oracle Data Dictionary (V$, DBA_*, CDB_*) | 15 |
| `oracle-tuning-ptbr` | 2.7.0 | Performance tuning, AWR, ASH, explain plan, indexes, estatísticas | 7 |
| `oracle-trivadis-ptbr` | 2.4.1 | Trivadis Guidelines 4.4 — nomenclatura e revisão de código | 2 |
| `oracle-devops-ptbr` | 4.1.0 | Git, CI/CD, changelog Oracle, Liquibase, deploy Python + oracledb | 31 |
| `oracle-lab-ptbr` | 1.1.0 | Ambiente local (Vagrant/VirtualBox, container) para desenvolvedor | 8 |
| `oracle-26ai-ptbr` | 1.1.0 | Novidades 23ai/26ai e migração 19c → 26ai (só com versão-alvo declarada) | 6 |

---

## Instalação

### Via arquivo `.skill` (Claude.ai)

1. Baixe os arquivos `.skill` da pasta [`dist/`](./dist/)
2. No Claude.ai → **Settings** → **Skills** → arraste ou clique em **Upload**
3. Repita para cada skill desejada

### Stack completa (recomendado)

```bash
# Baixar todos os .skill e instalar um por um
dist/oracle-core-ptbr.skill
dist/oracle-plsql-ptbr.skill
dist/oracle-apex-ptbr.skill
dist/oracle-ords-ptbr.skill
dist/oracle-dba-ptbr.skill
dist/oracle-tuning-ptbr.skill
dist/oracle-trivadis-ptbr.skill
dist/oracle-devops-ptbr.skill
dist/oracle-lab-ptbr.skill
dist/oracle-26ai-ptbr.skill
```

---

## Quando cada skill é ativada

### oracle-core-ptbr
Qual skill Oracle usar · visão geral da suíte · convenções gerais de projeto · começar projeto Oracle/APEX do zero

```
"Qual skill Oracle eu uso pra isso?"
"Qual o padrão do projeto Oracle de vocês?"
```

### oracle-plsql-ptbr
`BULK COLLECT` · `FORALL` · `NOCOPY` · `EXECUTE IMMEDIATE` · `MERGE INTO` · compound trigger · EBR · CLOB/BLOB · Logger · package · procedure · function

```
"Criar um package para processar pagamentos"
"Refatorar esse loop para BULK COLLECT"
"Como usar EBR para deploy sem downtime?"
```

### oracle-apex-ptbr
APEX · Dynamic Action · Interactive Report · Interactive Grid · Page Process · AJAX Callback · `APEX_APPLICATION_*` · `APEX_WORKSPACE_*` · Workflows · AI configs · JSON Sources

```
"Como auditar a paginação dos meus IRs?"
"Diferença entre Page Process e Dynamic Action"
"Como verificar pages sem authorization scheme?"
```

### oracle-ords-ptbr
ORDS · `define_module` · `define_handler` · AutoREST · OAuth · `ORDS_SECURITY` · JWT · PAR · `USER_ORDS_*` · `DBA_ORDS_*`

```
"Criar endpoint REST com autenticação OAuth"
"Inventário de todos os handlers ORDS"
"Como migrar do OAUTH depreciado para ORDS_SECURITY?"
```

### oracle-dba-ptbr
`V$SESSION` · `GV$` · `DBA_*` · `CDB_*` · `DBA_HIST_*` · sessão travada · lock · flashback · recompile · tablespace · SE2 vs EE · Diagnostics Pack

```
"Quem está bloqueando essa sessão?"
"Recuperar linha deletada por engano"
"Qual edição Oracle preciso para usar AWR?"
```

### oracle-tuning-ptbr
explain plan · `V$SQL` · `V$SQLAREA` · AWR em tempo real · ASH · index · hard parse · `DBMS_STATS` · cardinality · hints

```
"Essa query está fazendo full scan, como otimizar?"
"Qual index criar para essa consulta?"
"Hard parse muito alto no V$SQLAREA"
```

### oracle-trivadis-ptbr
Revisão explícita do padrão · prefixos `g_/l_/p_/r_/t_/co_/e_` · naming PT-BR · checklist pré-deploy

```
"Esse package segue o padrão Trivadis?"
"Qual prefixo usar para esse cursor?"
"Checklist Trivadis antes do GMUD"
```

> As demais skills aplicam Trivadis automaticamente — `oracle-trivadis-ptbr` é para consultas e revisões explícitas.

### oracle-devops-ptbr
Estrutura Git · changelog Oracle (`db/changelog.yml` + `db_changelog`) · scripts Python com `oracledb` · GitHub Actions · GMUD naming · export APEX split · versionamento ORDS · `DB_SCHEMA` para deploy via DBA

```
"Como estruturar meu projeto Oracle no Git?"
"Script de deploy com changelog versionado"
"Export do APEX para Git em modo split"
"Deploy via usuário DBA em schema diferente"
```

### oracle-lab-ptbr
Instalar Oracle na própria máquina · Vagrant + VirtualBox · container Free · APEX/ORDS locais · ORA-12541 / ORA-12514 / ORA-01017 de quem está começando

```
"Como instalo um Oracle pra testar?"
"Não consigo conectar no banco da VM"
```

### oracle-26ai-ptbr
Só quando a versão-alvo declarada for 23ai/26ai · migração 19c → 26ai · backports 19.28 · BOOLEAN em SQL · Domains · JSON duality views

```
"Estou no 26ai, isso muda?"
"Dá pra usar isso no 19c?"
```

---

## Skill irmã (repositório separado)

[`oracle-26ai-helper-ptbr`](https://github.com/Maxwbh/oracle-26ai-helper-ptbr) — aprofundamento em Oracle AI Database 26ai: **Vector Search, JSON Relational Duality e RAFT**. Roteamento: Vector / Duality / RAFT → `oracle-26ai-helper-ptbr`; sintaxe nova e migração 19c→26ai → `oracle-26ai-ptbr`.

---

## Referências cruzadas entre skills

```
oracle-plsql-ptbr  ←→  oracle-trivadis-ptbr    (nomenclatura)
oracle-plsql-ptbr  ←→  oracle-apex-ptbr         (page process)
oracle-plsql-ptbr  ←→  oracle-ords-ptbr          (handler logic)
oracle-dba-ptbr    ←→  oracle-tuning-ptbr        (AWR / performance)
oracle-apex-ptbr   ←→  oracle-ords-ptbr          (REST consumption)
oracle-devops-ptbr ←→  oracle-plsql-ptbr         (db/packages/)
oracle-devops-ptbr ←→  oracle-apex-ptbr          (apex/app_N/)
oracle-devops-ptbr ←→  oracle-ords-ptbr          (ords/modules/)
```

---

## Versões suportadas

| Item | Situação em 06/11/2026 | Fonte |
|---|---|---|
| **Oracle Database 19c** | Long Term Support Release · **Premier até 31/12/2029 · Extended até 31/12/2032** · RU mais recente com página de novidades: **19.33** · upgrade **direto 19c → 26ai** (detalhe em `oracle-26ai-ptbr`) | [Lifetime Support Policy](https://www.oracle.com/us/assets/lifetime-support-technology-069183.pdf) (02/10/2026), [26ai Upgrade Guide](https://docs.oracle.com/en/database/oracle/oracle-database/26/upgrd/oracle-database-releases-that-support-direct-upgrade.html), [RU 19.33](https://docs.oracle.com/en/database/oracle/oracle-database/19/newft/ru-19-33.html) |
| Oracle AI Database 26ai | Long Term Support Release · Premier até dez/2031 | Lifetime Support Policy |
| **APEX 26.2** | **atual** — GA 06/10/2026 · exige **ORDS 26.3.0+**, **SQLcl 26.3.0+**, banco **19c RU 19.18+** ou **26ai 23.26.0+** · upgrade direto a partir do 18.1 · patch 26.2.1 | [release notes 26.2](https://docs.oracle.com/en/database/oracle/apex/26.2/htmrn/about-release-notes.html), [downloads](https://www.oracle.com/tools/downloads/apex-downloads) |
| APEX 26.1 | GA 14/05/2026 · ORDS 26.1.1+ · patch 26.1.6 | [downloads 26.1](https://www.oracle.com/tools/downloads/apex-261-downloads) |
| **APEX 24.2** | **baseline suportada da suíte** · patch set mais recente **24.2.22** (04/11/2026) · ⚠ 24.2.0–24.2.20 na faixa da **CVE-2026-101521** (CVSS 9.8) | [downloads 24.2](https://www.oracle.com/tools/downloads/apex-242-downloads), [CPU out/2026](https://www.oracle.com/security-alerts/cpuoct2026.html) |
| ORDS | **26.3.1** (04/11/2026) é a mais recente · 26.4 planejada ("Winter 2026", Tomcat 10/WebLogic 15) | [ORDS changelog](https://www.oracle.com/tools/ords/ords-changelog.html) |
| SQLcl | **26.3.1** (03/11/2026) · CodeScan com regras para APEXlang desde 26.3.0 | [SQLcl changelog](https://www.oracle.com/tools/sqlcl/sqlcl-changelog.html) |

**A verificar:** datas de fim de suporte do APEX (24.2, 26.1, 26.2); data de lançamento do RU 19.33; primeira versão corrigida da CVE-2026-101521.

---

## Stack coberta

| Tecnologia | Versão | Cobertura |
|---|---|---|
| Oracle Database | 19c (padrão) · 23ai/26ai só com versão declarada | PL/SQL, SQL, tipos, EBR, Data Dictionary 11g→26ai |
| Oracle APEX | 24.2 (baseline) → 26.2 | Development + Data Dictionary (APEX_APPLICATION_* etc.) |
| Oracle ORDS | 24.4 → 26.3 | REST services + Data Dictionary (USER/DBA_ORDS_*) |
| Trivadis Guidelines | 4.4 | Nomenclatura PT-BR + checklist |
| Python oracledb | 2.0+ (Thin Mode) | Scripts DevOps sem Oracle Client |
| GitHub Actions | — | CI/CD com deploy por ambiente e aprovação prod |

---

## oracle-devops-ptbr — Scripts Python

A skill DevOps inclui 7 scripts Python + módulo compartilhado:

```
scripts/
├── oracle_devops_utils.py   # shared: connect, run_sql, colors, DB_SCHEMA
├── apply_changelog.py       # migrations (changelog.yml + db_changelog)
├── deploy_full.py           # orquestrador changelog → APEX → ORDS
├── deploy_db.py             # objetos banco em ordem de dependência
├── deploy_ords.py           # módulos ORDS (security→privileges→modules)
├── export_db.py             # DDL via DBMS_METADATA → db/
├── export_ords.py           # schema ORDS via ORDS_EXPORT
├── export_apex.py           # export split APEX via SQLcl
└── requirements-devops.txt  # oracledb>=2.0.0, PyYAML>=6.0.0
```

### Deploy em schema diferente do usuário de conexão

Suporte nativo a cenários DBA:

```bash
# .env
DB_USER=admin_dba      # usuário de conexão
DB_PASS=senha_dba
DB_SCHEMA=ms_app       # schema alvo do deploy

# oracle_devops_utils executa automaticamente:
# ALTER SESSION SET CURRENT_SCHEMA = MS_APP
```

---

## Estrutura do repositório

```
oracle-skills-ptbr/
├── README.md
├── CHANGELOG.md
├── LICENSE
├── .gitignore
├── build.py                   # propaga shared/ e empacota dist/
├── marketplace.yml
├── shared/assets/             # fonte única (ex.: oracle_devops_utils.py)
├── skills/                    # código-fonte (para contribuições)
│   ├── oracle-core-ptbr/
│   ├── oracle-plsql-ptbr/
│   ├── oracle-apex-ptbr/
│   ├── oracle-ords-ptbr/
│   ├── oracle-dba-ptbr/
│   ├── oracle-tuning-ptbr/
│   ├── oracle-trivadis-ptbr/
│   ├── oracle-devops-ptbr/
│   ├── oracle-lab-ptbr/
│   └── oracle-26ai-ptbr/
└── dist/                      # pacotes prontos para instalar
    ├── oracle-core-ptbr.skill
    ├── oracle-plsql-ptbr.skill
    ├── oracle-apex-ptbr.skill
    ├── oracle-ords-ptbr.skill
    ├── oracle-dba-ptbr.skill
    ├── oracle-tuning-ptbr.skill
    ├── oracle-trivadis-ptbr.skill
    ├── oracle-devops-ptbr.skill
    ├── oracle-lab-ptbr.skill
    └── oracle-26ai-ptbr.skill
```

---

## Publicar no GitHub

```bash
# Extrair o ZIP
unzip oracle-skills-ptbr-v3.1.0-git.zip

cd oracle-skills-ptbr
git init
git add .
git commit -m "feat: oracle-skills-ptbr v3.1.0 — 10 skills stack Oracle completa"
git remote add origin https://github.com/maxwbh/oracle-skills-ptbr.git
git push -u origin main

git tag -a v3.1.0 -m "10 skills + devops Python oracledb v3.1.0"
git push origin v3.1.0
```

---

## Licença

MIT — veja [LICENSE](./LICENSE)  
Copyright © 2026 Maxwell da Silva Oliveira — M&S do Brasil LTDA
