# Changelog — oracle-dba-ptbr

## [2.3.2] - 2026-09-15
- Docs — suíte com 10 skills; fronteira com oracle-lab-ptbr (máquina local do dev) explicitada.

## [2.3.1] - 2026-09-15
- Docs — suíte com 9 skills; referência cruzada para planejamento de upgrade 19c → 26ai.

## [2.3.0] - 2026-09-15
- Fronteira com oracle-tuning-ptbr explicitada: aqui fica licença/retenção/snapshots de AWR-ASH e coleta/agendamento de DBMS_STATS; análise de SQL vai para tuning. Description e referência cruzada ajustadas; changelog movido para CHANGELOG.md.

## [2.2.0]
- Feature — integração à suíte unificada: identidade "Módulo da suíte Oracle PT-BR" na description, bloco de versão/suíte no corpo, lista das 8 skills e roteamento central via oracle-core-ptbr (nova).

## [2.1.0]
- Feature — nova pasta assets/scripts_dba/ com 8 scripts ad-hoc estilo Tim Hall/oracle-base.com (locked_objects, lock_tree, top_sessions, longops, invalid_objects_quick, redo_by_hour, index_usage, session_pga) + README de uso. Migrados da geração v1.0.0 (aposentada). suite_size 5→14.

## [2.0.2]
- Docs — adicionado Índice (ToC) em references com +100 linhas (data-dictionary-ptbr.md, dba-operations.md); limpeza de artefatos __pycache__. Sem mudança de comportamento.

## [2.0.1]
- Fix — valores literais do dicionário Oracle corrigidos (status 'ATIVO'→'ACTIVE', 'INATIVO'→'INACTIVE', 'INVALIDO'→'INVALID') que faziam as queries de sessão e objetos inválidos retornarem vazio; coluna 'nome'→'name' em v$statname, user_errors/dba_errors, dependencies (ORA-00904); rownum antes de ORDER BY em v$undostat corrigido (subquery ordenada); control_management_pack_access reclassificado de V$OPTION para V$PARAMETER no SKILL.md; diagnóstico de privilégio inclui DBA_TAB_PRIVS; verificação pré-KILL reforçada (v$transaction, type='USER'). Metadados suite_size/release_date/repository adicionados.

## [2.0.0]
- Breaking — divisão de oracle-sql-helper-ptbr v1.6.0 em 6 skills especializadas. Esta skill cobre DBA operacional e Oracle Data Dictionary (V$, GV$, DBA_*, CDB_*). Instale as 6 irmãs para cobertura completa da stack Oracle.

## [1.6.0]
- (oracle-sql-helper-ptbr) Novo reference ords-data-dictionary-ptbr.md — USER_ORDS_*/DBA_ORDS_*, depreciacao OAUTH/ORDS_SECURITY, evolucao 18.x-25.x.

## [1.5.0]
- (oracle-sql-helper-ptbr) Novo reference apex-data-dictionary-ptbr.md — hierarquia APEX_APPLICATION_*/APEX_APPL_*/APEX_WORKSPACE_*, versoes 19-26.1.

## [1.4.0]
- (oracle-sql-helper-ptbr) Remocao de clientes reais. Autoria M&S do Brasil LTDA.

## [1.3.0]
- (oracle-sql-helper-ptbr) Novo reference data-dictionary-ptbr.md — hierarquia Oracle, matriz edicao x tecnologia, evolucao 11g-26ai.
