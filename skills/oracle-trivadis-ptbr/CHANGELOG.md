# Changelog — oracle-trivadis-ptbr

## [2.4.0] - 2026-11-06
- Fix — guia: exemplo, "Padrão completo" de exceção e princípios de transação alinhados à regra 4 da oracle-plsql-ptbr (rotina não comita; SAVEPOINT + ROLLBACK TO + RAISE; dono da transação). Antes recomendava ROLLBACK total e -20999 com SQLERRM.

## [2.3.1] - 2026-09-15
- Docs — suíte com 10 skills (oracle-lab-ptbr).

## [2.3.0] - 2026-09-15
- Feature — seção "Sucessão do padrão — dbLinter": Trivadis 4.4 é a versão final (repositório e db* CODECOP arquivados em 02/02/2026); sucessor dbLinter (198 regras, mesma numeração G-xxxx + novas), bloco de naming G-92xx (inclui G-9208 assertions), regras novas recomendadas já em 19c, regras APEX A-xxxx, ferramentas (VS Code/CLI/SonarQube). Description com gatilhos dbLinter/db* CODECOP/IslandSQL/G-92xx.

## [2.2.1] - 2026-09-15
- Docs — suíte com 9 skills (oracle-26ai-ptbr).

## [2.2.0] - 2026-09-15
- changelog movido para CHANGELOG.md; header de versão sincronizado.

## [2.1.0]
- Feature — integração à suíte unificada: identidade "Módulo da suíte Oracle PT-BR" na description, bloco de versão/suíte no corpo, lista das 8 skills e roteamento central via oracle-core-ptbr (nova).

## [2.0.2]
- Docs — adicionado Índice (ToC) em references com +100 linhas (plsql-trivadis-guidelines.md); limpeza de artefatos __pycache__. Sem mudança de comportamento.

## [2.0.1]
- Fix — prefixos alinhados ao validador oficial Trivadis (TrivadisPlsqlNaming, G-9101–9115) com os dois desvios locais marcados explicitamente (gc_/lc_=constante e co_=cursor, vs oficial co_=constante / c_=cursor); removido o prefixo inventado gco_ ("variável de contexto"), que não existe no padrão; adicionadas convenções oficiais faltantes (in_/out_/io_, o_, sufixo _type); corrigida afirmação datada "Oracle não tem BOOLEAN em SQL" (BOOLEAN nativo existe em 23ai/26ai; em 19c emular com NUMBER(1)); exemplos de código convertidos para naming PT-BR coerente com a própria regra; linkagem corrigida (skill não tem assets — aponta skills irmãs); adicionados códigos de regra G-xxxx. Metadados suite_size/release_date/repository adicionados.

## [2.0.0]
- Breaking — divisão de oracle-sql-helper-ptbr v1.6.0 em 6 skills especializadas. Esta skill cobre Trivadis Guidelines 4.4 — nomenclatura, estrutura e revisão de código. Instale as 6 irmãs para cobertura completa da stack Oracle.

## [1.6.0]
- (oracle-sql-helper-ptbr) Novo reference ords-data-dictionary-ptbr.md — USER_ORDS_*/DBA_ORDS_*, depreciacao OAUTH/ORDS_SECURITY, evolucao 18.x-25.x.

## [1.5.0]
- (oracle-sql-helper-ptbr) Novo reference apex-data-dictionary-ptbr.md — hierarquia APEX_APPLICATION_*/APEX_APPL_*/APEX_WORKSPACE_*, versoes 19-26.1.

## [1.4.0]
- (oracle-sql-helper-ptbr) Remocao de clientes reais. Autoria M&S do Brasil LTDA.

## [1.3.0]
- (oracle-sql-helper-ptbr) Novo reference data-dictionary-ptbr.md — hierarquia Oracle, matriz edicao x tecnologia, evolucao 11g-26ai.
