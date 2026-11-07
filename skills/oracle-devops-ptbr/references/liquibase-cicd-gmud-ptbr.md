# Liquibase, Code Review e Deploy GMUD por Ambiente

Fluxo de deploy de banco Oracle versionado com **Liquibase** (changelog XML
real), promovido entre ambientes (dev → hom → prod) por **GitHub Actions com
environments protegidos**, mantendo a regra de governança de que **o Git nunca
conecta direto no banco de produção** quando o projeto assim exigir.

Liquibase rastreia o que já foi aplicado na tabela `DATABASECHANGELOG`; a ordem
de execução é a ordem dos changesets no changelog. Isso substitui o controle
manual por nome de arquivo: o XML é a fonte da verdade da ordem e do estado.

## Índice

- [Visão geral do fluxo](#visão-geral-do-fluxo)
- [Eixos de decisão e matriz](#eixos-de-decisão-e-matriz)
- [Estados e gatilhos no Git](#estados-e-gatilhos-no-git)
- [Estrutura de pastas](#estrutura-de-pastas)
- [Anatomia do changelog](#anatomia-do-changelog)
- [Mapeando GMUD em changesets](#mapeando-gmud-em-changesets)
- [Ambientes via context](#ambientes-via-context)
- [Três estratégias de entrega ao banco](#três-estratégias-de-entrega-ao-banco)
- [Rollback](#rollback)
- [Executor auxiliar (gmud_liquibase.py)](#executor-auxiliar-gmud_liquibasepy)
- [Portabilidade: GitHub Actions ou Azure Pipelines](#portabilidade-github-actions-ou-azure-pipelines)
- [Checklist de adoção](#checklist-de-adoção)

## Visão geral do fluxo

```
PR aberto ─► review do CÓDIGO (required approvals na branch protection)
   │ merge em develop
   ▼
[dev]  deploy automático (sem gate)
   │ workflow_dispatch ambiente=hom
   ▼
[hom]  GATE: required reviewer aprova/reprova  ◄── "Enviar p/ HOM"
   │ workflow_dispatch ambiente=prod
   ▼
[prod]  GATE: required reviewer aprova/reprova  ◄── "Enviar p/ PROD"
       (aplica direto, via runner interno, ou só gera SQL para o DBA)
```

Há **dois** pontos de aprovação distintos, que costumam ser confundidos:
- **Code review** = aprovação do *código* no Pull Request (branch protection).
- **Approval gate de ambiente** = aprovação da *promoção/deploy* num ambiente
  (GitHub Environment com required reviewers). É aqui que "Aprovar / Reprovar /
  Enviar p/ HOM / Enviar p/ PROD" se materializam.

## Eixos de decisão e matriz

Esta skill cobre uma matriz de combinações em **dois eixos independentes**:

- **CI/CD (onde roda):** `git` (GitHub Actions) · `azure` (Azure Pipelines) · `manual` (sem pipeline; o DBA executa).
- **Liquibase (como versiona/aplica o banco):** `sim` (changelog XML + `DATABASECHANGELOG` — **recomendado**) · `não` (fluxo **legado** por ordem de nome de arquivo + checksum YAML, via `apply_changelog.py`).

Os dois eixos se cruzam livremente. A tabela aponta os assets de cada combo:

| CI ↓ \ Liquibase → | **Sim (recomendado)** | **Não (legado)** |
|---|---|---|
| **git** | `github-deploy-liquibase.yml` + `changelog-master.xml` + `gmud_liquibase.py` | `github-deploy.yml` + `changelog_template.yml` + `apply_changelog.py` |
| **azure** | `azure-pipelines-liquibase.yml` + `changelog-master.xml` + `gmud_liquibase.py` | sem template Azure legado — use `apply_changelog.py` chamado por um pipeline Azure próprio |
| **manual** | `gmud_liquibase.py prever/aplicar` ou SQLcl `lb update` | `apply_changelog.py --env ...` rodado pelo DBA |

A escolha de **entrega ao banco** (runner direto / self-hosted / DBA aplica o SQL) é um terceiro eixo que se aplica a qualquer combo com CI — detalhado em [Três estratégias de entrega ao banco](#três-estratégias-de-entrega-ao-banco).

> **Liquibase é o caminho recomendado** (estado em `DATABASECHANGELOG`, rollback por tag, contexts por ambiente, suporte nativo no SQLcl). O fluxo YAML legado permanece para projetos que já o adotaram, mas novos projetos devem usar Liquibase.

### Gerar o setup automaticamente

`assets/setup_devops.py` monta o esqueleto do combo escolhido (pipeline +
estrutura de changelog + README-deploy.md):

```bash
python setup_devops.py                                   # interativo: pergunta CI e Liquibase
python setup_devops.py --ci git   --liquibase sim --dest .
python setup_devops.py --ci azure --liquibase sim
python setup_devops.py --ci manual --liquibase nao       # fluxo legado, sem pipeline
```

O script só copia o template certo e cria as pastas — não conecta no banco.

## Estados e gatilhos no Git

| Ação desejada | Mecanismo GitHub | Efeito |
|---|---|---|
| Aprovar (código) | Pull Request approval (branch protection) | Permite merge |
| Reprovar (código) | PR "Request changes" | Bloqueia merge |
| Deploy em dev | `push` em `develop` | Job `deploy-dev` roda sem gate |
| Enviar p/ HOM | `workflow_dispatch` ambiente=hom | Job `deploy-hom` aguarda reviewer do environment `hom` |
| Aprovar HOM | Reviewer aprova o deployment pendente | Job prossegue e aplica em HOM |
| Reprovar HOM | Reviewer rejeita | Job falha; nada é aplicado |
| Enviar p/ PROD | `workflow_dispatch` ambiente=prod | Job `deploy-prod` aguarda reviewer do environment `prod` |
| Aprovar/Reprovar PROD | Reviewer do environment `prod` | Aplica em PROD ou cancela |

Configuração no GitHub (uma vez por repositório):
1. Settings → Environments → crie `dev`, `hom`, `prod`.
2. Em `hom` e `prod`: marque **Required reviewers** (as pessoas que aprovam o
   deploy). Opcional: **Wait timer** e **Deployment branches** (ex.: só `main`
   pode deployar em prod).
3. Em cada environment, cadastre os **Secrets** de conexão (`DB_URL`,
   `DB_USER`, `DB_PASSWORD`) — assim cada ambiente tem credencial isolada e o
   segredo de produção nunca fica acessível ao job de dev.
   Secrets de Environment só existem nos jobs que declaram `environment:` —
   por isso o job `validar` (sem environment) faz só a verificação offline, e
   o `liquibase validate` (que **exige conexão**) roda dentro de cada deploy.
4. As credenciais chegam ao Liquibase por `LIQUIBASE_COMMAND_URL`,
   `LIQUIBASE_COMMAND_USERNAME` e `LIQUIBASE_COMMAND_PASSWORD` — nunca em
   `--password=` na linha de comando (fica em `ps` e no log).
5. O Liquibase é instalado com `liquibase/setup-liquibase@v3`
   (`liquibase/liquibase-github-action` executa uma operação e exige o input
   `operation`; não instala o CLI no PATH). O 4.33.0 Community já traz o
   driver Oracle (ojdbc8); do 5.0 em diante a Community não traz drivers
   (instalar com `liquibase lpm add ...`).

Workflow pronto: `assets/github-deploy-liquibase.yml`.

## Estrutura de pastas

```
db/
├── changelog-master.xml            # ponto de entrada (gerado/mantido)
└── releases/
    ├── 2026.01-gmud-001/
    │   ├── changelog.xml           # changesets desta GMUD
    │   ├── 001_projeto_ddl_tb_cliente.sql
    │   ├── 002_projeto_ddl_constraints.sql
    │   ├── 003_projeto_plsql_pkg_cliente.sql
    │   ├── 004_projeto_dml_dominios.sql
    │   └── rollback/
    │       ├── 001_drop_tb_cliente.sql
    │       └── ...
    └── 2026.02-gmud-002/
        └── ...
```

O prefixo numérico/cronológico das releases define a ordem quando se usa
`includeAll`; com `include` explícito, a ordem é a do XML.

## Anatomia do changelog

O `changelog-master.xml` só inclui releases em ordem. Cada release tem seu
`changelog.xml` com os changesets. Identidade única de um changeset =
`id` + `author` + caminho do arquivo — nunca reaproveite um `id` já aplicado;
para mudar algo já aplicado, crie um changeset novo (ou use `runOnChange`).

Atributos de changeset mais usados aqui:
- `sqlFile` — referencia o `.sql` GMUD (com `relativeToChangelogFile="true"`).
- `endDelimiter="/"` — necessário para blocos PL/SQL (packages, triggers).
- `runOnChange="true"` — reaplica quando o checksum do arquivo muda; ideal para
  objetos `CREATE OR REPLACE` (packages, views, procedures).
- `context` — restringe o ambiente (ver adiante).
- `labels` — etiqueta lógica (ex.: `gmud-001`) para filtrar deploys.
- `<rollback>` — script de desfazimento explícito do changeset.
- `<tagDatabase>` — marca um ponto nomeado para rollback de release.

Modelos prontos: `assets/changelog-master.xml` e
`assets/changelog-release-exemplo.xml`.

## Mapeando GMUD em changesets

A skill nomeia os scripts no padrão GMUD `001_projeto_ddl_objeto.sql`. No
Liquibase, cada um vira um `<changeSet>` com `<sqlFile>`, na ordem de
dependências:

1. `sequences`, `types`
2. `tables`
3. `constraints`, `fk`, `indexes`
4. `views`, `grants`, `synonyms`
5. `packages` / `procedures` / `functions` / `triggers` (use `runOnChange`)
6. `dml` (cargas, seeds)
7. `tagDatabase` ao fim da release

A ordem dos `<changeSet>` no XML é a ordem de execução — respeite as
dependências entre objetos.

## Ambientes via context

`context` é o seletor de ambiente. Um changeset sem `context` roda em todos; com
`context="hom,prod"` roda só nesses. No deploy, passa-se o context do ambiente:

```bash
liquibase changelog-file=db/changelog-master.xml contexts=dev update
liquibase changelog-file=db/changelog-master.xml contexts=hom update
```

Padrão recomendado: DDL estrutural sem context (vai a todos os ambientes);
cargas de dados de homologação/produção com `context="hom,prod"`; massa de teste
só de dev com `context="dev"`.

## Três estratégias de entrega ao banco

Cada projeto escolhe **uma**, conforme a rede e a política de segurança. A regra
"o Git não conecta direto no banco" é mais crítica em produção.

**A) Runner hospedado conecta direto.** O job do GitHub Actions (runner
ubuntu-latest) abre conexão Oracle e roda `update`. Simples, mas exige que o
banco aceite conexão a partir da rede do runner — geralmente aceitável em
dev/hom, raramente em prod. Mais simples de manter.

**B) Runner self-hosted dentro da rede do banco.** Um runner próprio, instalado
em servidor da rede interna, executa o `update`. O GitHub orquestra e aprova,
mas a conexão nunca sai da rede segura. É a opção recomendada para prod quando se
quer automação completa sem expor o banco à internet.

**C) Pipeline só gera o script; DBA aplica.** O workflow roda `updateSQL`
(dry-run) e publica o `.sql` resultante como artefato/anexo da GMUD. Nenhuma
conexão de produção parte do Git — o DBA revisa e aplica manualmente via SQLcl.
É a opção mais conservadora e a que melhor honra "o Git não toca o banco".

O workflow `github-deploy-liquibase.yml` traz os três caminhos: dev/hom na
estratégia A (ajustável para B trocando `runs-on`), e prod já na C (gera
`gmud-prod.sql`), com o bloco de `update` direto comentado para quem optar por A/B.

## Rollback

Com `<rollback>` em cada changeset e um `<tagDatabase>` ao fim da release, dá
para voltar uma release inteira:

```bash
liquibase changelog-file=db/changelog-master.xml rollback 2026.01-gmud-001
```

Sem rollback declarado, alguns change types têm rollback automático (DDL
simples), mas para PL/SQL e DML sempre escreva o script de rollback explícito.

## Executor auxiliar (gmud_liquibase.py)

Para quem prefere um wrapper único em Python (consistente com os demais assets
da skill), `assets/gmud_liquibase.py` gera o master a partir das releases e
dispara o Liquibase ou o SQLcl:

```bash
python gmud_liquibase.py gerar    --root db                 # monta o master.xml
python gmud_liquibase.py verificar --root db                # XML e arquivos (sem banco)
python gmud_liquibase.py validar  --root db                 # liquibase validate (exige conexão)
python gmud_liquibase.py prever   --root db --env hom        # updateSQL (dry-run)
python gmud_liquibase.py aplicar  --root db --env hom        # update
python gmud_liquibase.py rollback --root db --env hom --tag 2026.01-gmud-001
```

Conexão por variáveis de ambiente (`DB_URL`/`DB_USER`/`DB_PASSWORD`), nunca no
código; repassadas ao Liquibase como `LIQUIBASE_COMMAND_*`. `aplicar --env prod`
pede confirmação só em terminal interativo; em CI exige `--yes` (dado após a
aprovação do Environment). `--runner` escolhe `liquibase` (binário), `sqlcl` (Liquibase embutido no
SQLcl da Oracle) ou `script` (só gera o SQL para o DBA — estratégia C).

## Portabilidade: GitHub Actions ou Azure Pipelines

O **miolo do deploy é agnóstico de plataforma**: o changelog Liquibase, a ordem
dos changesets, os contexts por ambiente e o `gmud_liquibase.py` são idênticos
em qualquer CI. Só muda a **camada de orquestração** (quem dispara, onde ficam
os approval gates e os segredos). A skill traz os dois pipelines lado a lado:

- GitHub: `assets/github-deploy-liquibase.yml`
- Azure: `assets/azure-pipelines-liquibase.yml`

Equivalência de conceitos:

| Conceito | GitHub Actions | Azure Pipelines |
|---|---|---|
| Unidade de execução | `job` | `stage` com `deployment` job |
| Ordem entre etapas | `needs:` | `dependsOn:` |
| Approval gate por ambiente | Environment + Required reviewers | Environment + Approvals and checks |
| Mirar o ambiente | `environment: hom` no job | `environment: hom` no deployment job |
| Disparo manual com escolha | `workflow_dispatch` + `inputs` | `parameters` + execução manual |
| Disparo por push | `on: push: branches:` | `trigger: branches:` |
| Segredos por ambiente | Environment Secrets | Variable Group / Key Vault por ambiente |
| Aprovar / Reprovar | Reviewer no deployment pendente | Aprovador em Approvals and checks |

O que **não** muda entre as duas plataformas: os comandos `liquibase ... update`
/ `updateSQL` / `rollback`, o `contexts=<ambiente>`, a tabela `DATABASECHANGELOG`
e as três estratégias de entrega ao banco. Trocar de GitHub para Azure (ou
manter os dois) é só escolher o arquivo de pipeline correspondente — nenhum
changelog ou script GMUD precisa ser alterado.

Setup mínimo no Azure (uma vez): Pipelines → Environments → criar `dev`, `hom`,
`prod`; em `hom`/`prod` abrir Approvals and checks → Approvals e cadastrar os
aprovadores; criar Variable Groups `oracle-dev`/`oracle-hom`/`oracle-prod` com
`DB_URL`/`DB_USER`/`DB_PASSWORD` (de preferência ligados ao Key Vault).

## Checklist de adoção

1. Liquibase instalado (CLI próprio ou via SQLcl `lb`).
2. `db/changelog-master.xml` apontando para as releases em ordem.
3. Cada GMUD é uma pasta em `releases/` com `changelog.xml` + `.sql` + `rollback/`.
4. Changesets de PL/SQL com `runOnChange` e `endDelimiter="/"`.
5. Cargas por ambiente com `context` apropriado.
6. GitHub Environments `dev`/`hom`/`prod` criados; reviewers em hom/prod.
7. Secrets de conexão por environment (isolados).
8. Estratégia de entrega ao banco definida (A, B ou C) e refletida no workflow.
9. `validate` + `updateSQL` rodando no CI antes de qualquer `update`.
10. Tag de release ao fim de cada changelog para rollback nomeado.
