# Changelog — oracle-plsql-ptbr

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
