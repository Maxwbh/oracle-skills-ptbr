# Changelog — oracle-devops-ptbr

## [4.1.1] - 2026-11-07
- Fix — `export_db.py`: sem `--schema`, usava `DB_USER` mesmo com `DB_SCHEMA` definido; agora `DB_SCHEMA` tem precedência (mesma regra do `oracle_devops_utils`).
- Fix — lint dos `export_*.py` (imports, f-strings, `check=False` explícito no `subprocess.run`) para o ruff do CI.

## [4.1.0] - 2026-11-06
- Feature — `codescan_gate.py`: gate de CI com SQLcl CodeScan (SQL, PL/SQL e APEXlang `.apx`, regras de .apx desde o SQLcl 26.3.0); falha se houver achado (o `codescan` sai com 0 mesmo com violações); exceções em `codescan.json`. Job `validate` do `github-deploy.yml` instala Java 21 + SQLcl e roda o gate. `suite_size` 30 → 31.
- Docs — APEXlang no pipeline: promoção entre ambientes com a aplicação inteira; import por arquivo do APEX 26.2 é só SQLcl/VS Code e só dev.
- Docs — roteamento para oracle-26ai-helper-ptbr; escopo APEX 24.2–26.2.

## [4.0.0] - 2026-11-06
- Breaking — scripts SQL (DDL, PL/SQL, migrations, install.sql do APEX) passam a ser executados pelo SQLcl (`sql -S /nolog`, `WHENEVER SQLERROR/OSERROR EXIT FAILURE ROLLBACK`, código de saída checado); SQLcl vira pré-requisito. `executar_arquivo_sql()` removido. Após cada script, `ALL_ERRORS` (owner = CURRENT_SCHEMA) é consultado e erro de compilação falha o deploy.
- Fix — parser `split_oracle_sql` reescrito como tokenizador: `END;` preservado em PL/SQL, `/* */`/`--`/`;`/`/` dentro de literal (inclusive `q'[...]'`) intactos, comandos de cliente (SET, PROMPT, WHENEVER, @, @@) rejeitados explicitamente, comando sem terminador vira erro. Novos `analisar_sql()` e `validar_arquivo_sql()` (pré-validação, inclusive UTF-8).
- Fix — `DB_SCHEMA` não era lido por `obter_config_db()`: o `ALTER SESSION SET CURRENT_SCHEMA` nunca rodava. Identificadores validados antes de ir para SQL dinâmico.
- Breaking — `db_changelog` ganha `status` (EM_ANDAMENTO/APLICADA/ERRO), `mensagem_erro` e `statement_erro`; tabela antiga atualizada automaticamente (linhas antigas = APLICADA). Migration em ERRO/EM_ANDAMENTO bloqueia novas execuções; novas opções `--retomar <id>`, `--marcar-resolvida <id>` e `--validar` (offline). Reference com migrations pequenas, pré-validação, compensação e retomada segura.
- Breaking — `confirmar_producao()`: em CI (`CI=true`) ou sem TTY nunca chama `input()`; exige `--confirmar-prod` ou `CONFIRMO_PROD=1` (sai com 2). Cancelamento interativo sai com 1.
- Fix — `deploy_full.py`: import do APEX pelo SQLcl a partir de `apex/app_<ID>/f<ID>` (export split), com workspace/app id validados antes e definidos via `APEX_APPLICATION_INSTALL`; mensagem clara sem SQLcl. `export_apex.py`: o `install.sql` gerado não importava a aplicação (só chamava `set_environment.sql`).
- Fix — `github-deploy.yml`: sem `upper()`; GitHub Environments dev/hom/prod com `DB_PASS` por ambiente e aprovação obrigatória em prod; sem segredos em outputs; validação offline real; `scripts/requirements-devops.txt` como caminho único. actionlint limpo.
- Breaking — ambientes unificados em `dev`/`hom`/`prod` também no fluxo Liquibase (Environments, Variable Groups `oracle-dev/hom/prod`, contexts do changelog XML, `gmud_liquibase.py --env`). Changelogs existentes com `context="hml,prd"` precisam ser renomeados. `setup_devops.py` sugeria `apply_changelog.py --env hml`, que não existe.
- Docs — estrutura do projeto não diz mais "triggers sempre compound" (regra 10 da oracle-plsql-ptbr).
- Fix — extrator de erro do SQLcl reconhece também o formato `ERROR at line N:` (ex.: CREATE TRIGGER); o resumo usa a linha ORA-/PLS-.
- Fix — `github-deploy-liquibase.yml` e `azure-pipelines-liquibase.yml`: instalação real do Liquibase (`setup-liquibase@v3` / em cada job do Azure), `validate` só com conexão (dentro dos deploys), credenciais por `LIQUIBASE_COMMAND_*`, sem `|| true`. `gmud_liquibase.py`: senha saía no log; nova ação `verificar` (offline); `aplicar --env prd` sem `input()` em CI.

## [3.6.2] - 2026-09-15
- Docs — suíte com 10 skills; referência cruzada para o lab local como ambiente de teste do pipeline.

## [3.6.1] - 2026-09-15
- Docs — suíte com 9 skills; referência cruzada para IF NOT EXISTS em scripts GMUD.

## [3.6.0] - 2026-09-15
- Docs — stack alvo alinhada à suíte (APEX 24.2/26.1, não só 24.2); branch de homologação padronizada como hml (hom = fluxo legado) no SKILL.md; tabela "Assets disponíveis" completada com os 6 assets Liquibase/CI que só apareciam em "Áreas cobertas" (setup_devops.py, gmud_liquibase.py, changelog-master.xml, changelog-release-exemplo.xml, github-deploy-liquibase.yml, azure-pipelines-liquibase.yml); NÃO ATIVE na description; changelog movido para CHANGELOG.md.

## [3.5.0]
- Feature — integração à suíte unificada: identidade "Módulo da suíte Oracle PT-BR" na description, bloco de versão/suíte no corpo, lista das 8 skills e roteamento central via oracle-core-ptbr (nova).

## [3.4.0]
- Feature — matriz de decisão em 2 eixos (CI/CD: git|azure|manual × Liquibase: sim|não) explicitada no reference, com tabela apontando os assets de cada combo e a estratégia de entrega ao banco como terceiro eixo. Novo asset setup_devops.py: assistente interativo (ou via flags --ci/--liquibase) que gera o esqueleto do combo escolhido (pipeline + estrutura de changelog Liquibase ou fluxo legado + README-deploy.md), sem conectar no banco. Liquibase marcado como recomendado; fluxo YAML antigo (changelog.yml + apply_changelog.py) marcado como legado na seção 11 do git-project-structure-ptbr.md (mantido para projetos existentes). SKILL.md: área, gatilho.

## [3.3.0]
- Feature — pipeline CI-agnóstico (GitHub Actions OU Azure DevOps). Novo asset azure-pipelines-liquibase.yml (stages dev/hml/prd com deployment jobs + Environments e Approvals and checks como approval gates; mesmas 3 estratégias de entrega ao banco; segredos via Variable Group/Key Vault). Reference liquibase-cicd-gmud-ptbr.md ganhou seção de portabilidade GitHub↔Azure (tabela de equivalências: job/stage, needs/dependsOn, Environments+reviewers/Approvals). Miolo (changelog Liquibase, contexts, gmud_liquibase.py) inalterado entre plataformas. SKILL.md: description e gatilhos incluem Azure Pipelines.

## [3.2.0]
- Feature — fluxo Liquibase + code review + deploy GMUD por ambiente. Novo reference liquibase-cicd-gmud-ptbr.md e 4 assets: changelog-master.xml e changelog-release-exemplo.xml (databaseChangeLog/changeSet reais, sqlFile, runOnChange, context, rollback, tagDatabase), github-deploy-liquibase.yml (GitHub Environments protegidos dev/hml/prd como approval gates — aprovar/reprovar/enviar p/ HML/PRD; cobre as 3 estratégias de entrega ao banco), e gmud_liquibase.py (gera o master a partir das releases e invoca liquibase/SQLcl/script). SKILL.md: nova área, gatilhos e description. XSD dbchangelog-latest; context como seletor de ambiente.

## [3.1.2]
- Docs — adicionado Índice (ToC) em references com +100 linhas (git-project-structure-ptbr.md); limpeza de artefatos __pycache__. Sem mudança de comportamento.

## [3.1.1]
- Fix — export_apex.py: SyntaxError (backslash em f-string) impedia o módulo de carregar; export_db.py: CABECALHO_TEMPLATE quebrava em .format() (chave literal {'─' * 60} → KeyError), travando toda escrita de DDL; f-strings de git commit (export_db/ords) compatibilizadas para Python <3.12; split_oracle_sql passa a separar statement seguido de comentário inline na mesma linha (preservando '--' em strings) e documenta limitações; deploy_db.py: ORDEM_DEPLOY/TIPOS incluem constraints/fk/indexes (alinhado ao SKILL.md). Metadados suite_size/release_date/repository adicionados.

## [3.1.0]
- Fix — substituição de USER_* por ALL_* com SYS_CONTEXT(CURRENT_SCHEMA). oracle_devops_utils: DB_SCHEMA + ALTER SESSION SET CURRENT_SCHEMA automático. deploy_ords: DBA_ORDS_MODULES com fallback USER_ORDS_MODULES. Suporte a deploy via usuário DBA em schema alvo diferente.

## [3.0.0]
- Breaking — todos os scripts migrados para Python (oracledb Thin Mode). Novo oracle_devops_utils.py compartilhado. deploy_full/db/ords.py, export_db/ords/apex.py. Shell scripts viram thin wrappers. requirements-devops.txt atualizado.

## [2.3.0]
- Reescrita do apply-changelog em Python (oracledb Thin Mode + PyYAML). apply_changelog.py com argparse, dry-run, status, cores terminal, confirmacao prod. apply-changelog.sh vira wrapper fino. requirements-devops.txt. github-deploy.yml atualizado.

## [2.2.0]
- Sistema de changelog do banco — changelog.yml + db_changelog (Oracle) + apply-changelog.sh (checksum SHA-256, fail-fast, deteccao de drift). Assets: changelog_template.yml, create-changelog-table.sql, apply-changelog.sh.

## [2.1.0]
- Novo asset export-db.sh — extrai DDL completo do schema Oracle (DBMS_METADATA.GET_DDL) para estrutura db/ do Git. Packages separados em .pks e .pkb. Remove clausulas de storage/tablespace. Detecta objetos invalidos.

## [2.0.0]
- Skill criada como parte da família oracle-*-ptbr v2.0.0. Cobre estrutura Git, scripts de deploy (deploy-full/db/ords/apex), export APEX split, versionamento ORDS, GMUD naming, branch strategy, .gitignore Oracle, GitHub Actions CI/CD.
