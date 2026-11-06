---
name: oracle-core-ptbr
description: "Assistente central da suíte Oracle PT-BR (M&S do Brasil): roteamento entre os 9 módulos técnicos, convenções transversais (naming PT-BR + Trivadis 4.4, SQL antes de PL/SQL, APEX não comita, GMUD e promoção entre ambientes) e cenários multidisciplinares. ATIVE em dúvidas sobre qual skill Oracle usar, visão geral da suíte Oracle, convenções gerais de projeto Oracle, começar projeto Oracle/APEX do zero, 'como vocês organizam o código Oracle', 'qual o padrão do projeto'. Use com oracle-plsql-ptbr, oracle-trivadis-ptbr, oracle-apex-ptbr, oracle-ords-ptbr, oracle-dba-ptbr, oracle-tuning-ptbr, oracle-devops-ptbr , oracle-26ai-ptbr (só quando a versão-alvo for 23ai/26ai) e oracle-lab-ptbr (instalar/montar ambiente local) para cobertura técnica completa. NÃO ATIVE quando a demanda já é claramente de um módulo específico (código PL/SQL, página APEX, endpoint ORDS, sessão travada, query lenta, pipeline) — nesse caso ative o módulo direto."
metadata:
  version: "1.4.1"
  release_date: "2026-11-06"
  repository: "https://github.com/maxwbh/oracle-skills-ptbr"
  suite_size: 2
  author: "Maxwell da Silva Oliveira"
  contact: "contato@msbrasil.inf.br"
  organization: "M&S do Brasil LTDA"
  site: "https://msbrasil.inf.br"
---

# Suíte Oracle PT-BR — Core (oracle-core-ptbr)

> **Versão:** 1.4.1 · **Atualizada em:** novembro/2026 · **Repositório:** oracle-skills-ptbr · **Suíte:** 10 skills (2 recursos nesta skill — `brand/tema-msbrasil.yaml` + CHANGELOG.md)
> **v1.3.1:** convenção de padrão de código registra que Trivadis 4.4 é a versão final (projeto arquivado em fev/2026) e aponta o dbLinter como catálogo vivo. Histórico em `CHANGELOG.md`.

Skill central da suíte Oracle PT-BR. Não contém templates próprios: define **como a suíte funciona como conjunto**, roteia demandas para o módulo certo e concentra as convenções que valem para todos.

Suíte completa (10 skills — conjunto único):
- **oracle-core-ptbr** — esta skill: roteamento, convenções transversais, cenários multidisciplinares
- **oracle-plsql-ptbr** — PL/SQL 19c: packages, BULK, LOBs, triggers, EBR
- **oracle-trivadis-ptbr** — Trivadis 4.4: naming, prefixos, revisão de código
- **oracle-apex-ptbr** — APEX 26.1: páginas, DA, IG, APIs APEX_*, metadata
- **oracle-ords-ptbr** — ORDS: REST modules/handlers, OAuth, Network ACL
- **oracle-dba-ptbr** — DBA operacional: sessões, locks, flashback, scripts ad-hoc
- **oracle-tuning-ptbr** — performance: explain plan, índices, stats, result cache
- **oracle-devops-ptbr** — Git/CI-CD: estrutura, Liquibase, pipelines, GMUD
- **oracle-26ai-ptbr** — 23ai/26ai: novidades SQL/PL/SQL, backports 19.28, migração 19c→26ai (só com versão declarada)
- **oracle-lab-ptbr** — instalação e ambiente local (VM/container) para quem não é DBA; rede de casa

## Contexto da suíte

- **Stack alvo:** Oracle Database **19c** (padrão) · APEX 24.2/26.1 · ORDS · SQLcl. 23ai/26ai só com versão declarada — ver `oracle-26ai-ptbr`; na dúvida, 19c
- **Idioma:** identificadores de domínio e comentários em **PT-BR**; keywords SQL/PL/SQL, pacotes Oracle nativos, funções built-in, hints e prefixos Trivadis em **inglês**
- **Padrão de código:** Trivadis PL/SQL & SQL Guidelines **4.4** (versão final — o projeto foi arquivado em fev/2026; catálogo vivo é o dbLinter, ver `oracle-trivadis-ptbr`)
- **Deploy:** Git → pipeline (Azure DevOps/GitHub Actions) → ambientes dev → hom → prod (branches develop → hom → main); Git **nunca** conecta direto em produção

## Roteamento — sintoma → módulo

| O usuário diz algo como | Módulo |
|---|---|
| "criar procedure/package/function", "loop tá lento, dá pra BULK?", "trigger de auditoria", "processar CLOB", "deploy sem downtime" | **oracle-plsql-ptbr** |
| "qual prefixo usar?", "esse código segue Trivadis?", "revisa esse package", "checklist antes da GMUD" | **oracle-trivadis-ptbr** |
| "página APEX", "IG editável", "Dynamic Action", "process no submit", "auditar paginação", "APEX_COLLECTION", "auth custom", "Universal Theme" | **oracle-apex-ptbr** |
| "endpoint REST", "módulo ORDS", "AutoREST", "autenticar API", "consumir API externa", "ORA-24247/ACL" | **oracle-ords-ptbr** |
| "sessão travada", "quem tá bloqueando", "matar sessão", "recuperar dado deletado", "objetos inválidos", "tablespace cheio", "tenho licença de Diagnostics Pack?", "agendar gather stats" | **oracle-dba-ptbr** |
| "query lenta", "qual índice criar", "explain plan", "hard parse", "stats desatualizadas", "result cache", "analisar AWR/ASH desse SQL" | **oracle-tuning-ptbr** |
| "estruturar projeto no Git", "pipeline", "changelog Liquibase", "export APEX pra Git", "nomenclatura GMUD", "enviar pra homologação" | **oracle-devops-ptbr** |
| "estou no 26ai", "isso existe no 26ai?", "migrar do 19c pro 26", "dá pra usar no 19c?", "IF NOT EXISTS", "BOOLEAN nativo", "QUALIFY", "duality view" | **oracle-26ai-ptbr** |
| "como instalo o Oracle aqui", "vagrant up", "VirtualBox", "preciso de um banco pra testar", "não conecto no meu banco local", "acessar do notebook da sala" | **oracle-lab-ptbr** |

## Cenários multidisciplinares — ordem de carregamento

| Cenário | Módulos (na ordem) |
|---|---|
| Página APEX lenta | oracle-apex-ptbr (capturar SQL via Debug) → oracle-tuning-ptbr (plano/índice) |
| Refatorar process APEX com lógica grande | oracle-apex-ptbr (mover para package) → oracle-plsql-ptbr (Trivadis, BULK) |
| API REST que chama regra de negócio | oracle-ords-ptbr (handler) → oracle-plsql-ptbr (package chamada) |
| Deploy de release com DDL + APEX + ORDS | oracle-devops-ptbr (ordem, GMUD) → oracle-plsql-ptbr (EBR se zero downtime) |
| Lock causado por transação do APEX | oracle-dba-ptbr (lock_tree, module/client_identifier) → oracle-apex-ptbr (origem) |
| Code review completo antes de GMUD | oracle-trivadis-ptbr (naming/estrutura) → módulo da tecnologia revisada |
| Query lenta identificada em job noturno | oracle-dba-ptbr (localizar SQL_ID) → oracle-tuning-ptbr (plano) → oracle-plsql-ptbr (reescrita) |
| Consumir API externa a partir do APEX | oracle-ords-ptbr (Network ACL) → oracle-apex-ptbr (APEX_WEB_SERVICE / JSON Source) |
| Cliente declara 26ai e pede código | oracle-26ai-ptbr (o que muda, backports) → módulo da tecnologia (gera com sintaxe 26ai marcada `-- 26ai`) |
| Planejar upgrade 19c → 26ai | oracle-26ai-ptbr (compatibilidade, checklist) → oracle-dba-ptbr (AutoUpgrade, PDB) → oracle-devops-ptbr (pipeline contra 26ai Free) |
| Dev novo na equipe, sem ambiente | oracle-lab-ptbr (montar VM com banco + APEX) → oracle-core-ptbr (convenções) → módulo da tecnologia |

## Convenções transversais canônicas

Valem em **todos** os módulos; cada um detalha as suas.

1. **SQL puro antes de PL/SQL.** Se a operação cabe em MERGE/INSERT SELECT/UPDATE CASE, não escreva loop. Detalhes: `oracle-plsql-ptbr`.
2. **Bind variables sempre.** Nunca concatenar valores em SQL dinâmico; `EXECUTE IMMEDIATE ... USING`.
3. **Naming Trivadis 4.4 + PT-BR.** Prefixos `g_, gc_, l_, lc_, p_, r_, t_, co_, e_`; identificadores de domínio em PT-BR. Guia completo: `oracle-trivadis-ptbr`.
4. **APEX não comita.** Page Process e server-side code não fazem COMMIT/ROLLBACK explícitos — o engine gerencia a transação. Detalhes: `oracle-apex-ptbr`.
5. **Auditabilidade.** `criado_em/criado_por/atualizado_em/atualizado_por` + soft delete (`ativo`, `excluido_em`).
6. **Privilégio mínimo.** Owner faz DDL, app user faz DML; nunca DBA para usuário de aplicação.
7. **Operações de risco pedem confirmação.** KILL SESSION, REBUILD sem ONLINE, GATHER_STATS em pico, TRUNCATE — sempre alertar antes. Tabela completa: `oracle-dba-ptbr`.
8. **Deploy versionado.** Todo objeto passa por Git + pipeline com GMUD nomeada (`001_projeto_ddl_objeto.sql`); promoção dev → hom → prod com aprovação. Detalhes: `oracle-devops-ptbr`.
9. **19c por padrão.** Sintaxe 23ai/26ai só com versão-alvo declarada, marcada `-- 26ai` no código; módulos 19c apenas citam a alternativa. Detalhes: `oracle-26ai-ptbr`.

## Manutenção da suíte

- Versionamento semântico por skill; `suite_size` = contagem real de recursos (assets + references) de cada skill, recalculada a cada release
- Histórico de versões em `CHANGELOG.md` na raiz de cada skill (não vai no frontmatter, para manter o SKILL.md enxuto no carregamento)
- Ao evoluir um módulo, verificar se a mudança afeta as cláusulas ATIVE/NÃO ATIVE dos irmãos (exclusão mútua)

## Identidade visual dos entregáveis

Peças visuais de projeto (propostas, decks de arquitetura, documentos de GMUD, relatórios de pós-implantação) usam o tema `msbrasil`, publicado em `brand/tema-msbrasil.yaml` e consumido pela skill `theme-factory-ptbr`:

```bash
python3 /mnt/skills/user/theme-factory-ptbr/scripts/aplicar_tema.py --tema msbrasil --arquivo <arquivo> --office
```

O tema é **provisório e declarado como tal**: herda o Tech Innovation do catálogo porque a M&S do Brasil ainda não tem paleta oficial. Não o apresente a cliente como "identidade visual da M&S". Quando a paleta existir, acrescente `colors`/`fonts`/`semantic` ao arquivo — roles, presets e contrastes são re-derivados.

Material de **cliente final** usa o tema do cliente quando existir; na ausência, escolha pelo contexto com `aplicar_tema.py --escolher "<pedido>"`, não o tema da M&S.
