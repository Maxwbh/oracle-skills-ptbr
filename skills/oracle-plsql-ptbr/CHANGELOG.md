# Changelog — oracle-plsql-ptbr

## [3.0.3] - 2026-11-07
- Docs — lista da suíte: APEX 26.2 (padrão; compatível com 24.2+).

## [3.0.2] - 2026-11-07
- Docs — roteamento: roteiro do upgrade 19c→26ai também vai para oracle-26ai-helper-ptbr; checklist de código fica na oracle-26ai-ptbr; operação na oracle-dba-ptbr.

## [3.0.1] - 2026-11-06
- Docs — roteamento para a skill irmã oracle-26ai-helper-ptbr; lista da suíte com APEX 24.2–26.2.

## [3.0.0] - 2026-11-06
- Breaking — regra 4 reescrita: transação tem dono. Rotina reutilizável não faz COMMIT nem ROLLBACK total; usa SAVEPOINT + ROLLBACK TO e propaga o erro (RAISE). COMMIT/ROLLBACK total só no ponto de entrada (job, endpoint, script), documentado; no APEX o dono é o APEX. A regra antiga ("ROLLBACK antes do re-raise") desfazia o trabalho do chamador.
- Breaking — regra 3: erro inesperado não vira mais -20999 com SQLERRM (perdia código e pilha); log + RAISE, ou raise_application_error(..., TRUE).
- Breaking — regra 10: compound trigger quando há estado entre linha e statement (mutating table, auditoria em lote, bulk); trigger simples FOR EACH ROW continua válida.
- Fix — package_body.sql: processar_registro sem COMMIT/ROLLBACK total; novo processar_pendentes (ponto de entrada); ramo "já processado" era inalcançável. package_header.sql com processar_pendentes. exception_template.sql com esqueletos A (reutilizável) e B (ponto de entrada).
- Fix — triggers_canonicos.sql: auditoria_pkg não compilava (tipo usado antes de declarado; sem body); trigger de surrogate key sobre coluna IDENTITY falhava com ORA-32795; reorganizado em trigger simples × compound.
- Fix — logger_integration.sql: processar_pagamento comitava e trocava o erro por -20999.
- Testes de integração em container (tests/integracao/test_plsql_templates_oracle.py).

## [2.2.2] - 2026-09-15
- Docs — suíte com 10 skills (oracle-lab-ptbr).

## [2.2.1] - 2026-09-15
- Docs — suíte com 9 skills (oracle-26ai-ptbr); referência cruzada para sintaxe 23ai/26ai.

## [2.2.0] - 2026-09-15
- tabela "Áreas cobertas" corrigida (coluna Reference apontava para references/ inexistente — agora aponta naming para oracle-trivadis-ptbr); NÃO ATIVE com acento na description; changelog movido para CHANGELOG.md.

## [2.1.0]
- Feature — integração à suíte unificada: identidade "Módulo da suíte Oracle PT-BR" na description, bloco de versão/suíte no corpo, lista das 8 skills e roteamento central via oracle-core-ptbr (nova).

## [2.0.1]
- Fix — sintaxe PARALLEL em external table (nível CREATE TABLE, não ACCESS PARAMETERS); coluna status/estado unificada em package_body; WHEN OTHERS em obter_resumo preserva backtrace; avisos de truncamento DBMS_LOB.substr (32767) e critério de PGA por tamanho de linha; esqueleto exception_template documenta dependências; tom de incerteza em 26ai e citações EBR parafraseadas. Metadados suite_size/release_date/repository adicionados.

## [2.0.0]
- Breaking — divisão de oracle-sql-helper-ptbr v1.6.0 em 6 skills especializadas. Esta skill cobre PL/SQL, packages, procedures, functions, LOBs, EBR, triggers. Instale as 6 irmãs para cobertura completa da stack Oracle.

## [1.6.0]
- (oracle-sql-helper-ptbr) Novo reference ords-data-dictionary-ptbr.md — USER_ORDS_*/DBA_ORDS_*, depreciacao OAUTH/ORDS_SECURITY, evolucao 18.x-25.x.

## [1.5.0]
- (oracle-sql-helper-ptbr) Novo reference apex-data-dictionary-ptbr.md — hierarquia APEX_APPLICATION_*/APEX_APPL_*/APEX_WORKSPACE_*, versoes 19-26.1.

## [1.4.0]
- (oracle-sql-helper-ptbr) Remocao de clientes reais. Autoria M&S do Brasil LTDA.

## [1.3.0]
- (oracle-sql-helper-ptbr) Novo reference data-dictionary-ptbr.md — hierarquia Oracle, matriz edicao x tecnologia, evolucao 11g-26ai.
