# Changelog — oracle-ords-ptbr

## [2.5.1] - 2026-11-07
- Docs — roteamento: roteiro do upgrade 19c→26ai também vai para oracle-26ai-helper-ptbr; checklist de código fica na oracle-26ai-ptbr; operação na oracle-dba-ptbr.

## [2.5.0] - 2026-11-06
- Feature — linha do tempo com ORDS 26.3.0 (exigido pelo APEX 26.2) e 26.3.1 (mais recente em 06/11/2026); 26.4 continua planejada (Tomcat 10/WebLogic 15; standalone não afetado). Par mínimo APEX × ORDS documentado.
- Feature — segurança: 35 CVEs do ORDS no CPU out/2026 (faixa 24.2.0–26.2.2), CVE-2026-91610 (8.8) e demais.
- Feature — tabela "O que é do APEX e o que é do ORDS": REST Workshop (APEX, removido no 26.2) × módulos/handlers ORDS (continuam) × SQL Developer Web.
- Docs — roteamento para oracle-26ai-helper-ptbr.

## [2.4.1] - 2026-11-06
- Docs — ords_handler.sql: handler PL/SQL é o ponto de entrada e dono da transação; packages chamados não comitam (regra 4 da oracle-plsql-ptbr).

## [2.4.0] - 2026-09-15
- Feature — seção "Linha do tempo das versões": a skill parava em 24.4 enquanto lab/apex/26ai já afirmavam ORDS 26.1.1. Agora cobre 25.1 (ORDS_EXPORT_ADMIN), 25.3 (remoção do OAUTH, DELETE_TEMPLATE/HANDLER), 26.1 (export com DROP, VecDB), 26.1.1 (exigido pelo APEX 26.1) e 26.4 (Tomcat 10/WebLogic 15), mais Java 17/21 e a regra de não antecipar o Tomcat 10.
- Feature — limpeza de metadata: delete_module/delete_template/delete_handler e a diferença entre drop_rest_for_object (desabilita) e drop_rest_for_schema (apaga).
- Docs — gatilhos novos na description; referência cruzada para o pipeline de export.

## [2.3.2] - 2026-09-15
- Docs — suíte com 10 skills; referência cruzada para instalar ORDS no ambiente local.

## [2.3.1] - 2026-09-15
- Docs — suíte com 9 skills (oracle-26ai-ptbr).

## [2.3.0] - 2026-09-15
- Fix — ORDS_SECURITY/ORDS_SECURITY_ADMIN marcados como 24.3+ no SKILL.md (estava 24.4+; o reference já dizia 24.3 e as release notes oficiais confirmam); PAR e DBA_ORDS_* mantidos em 24.4+ (verificado). NÃO ATIVE na description; changelog movido para CHANGELOG.md.

## [2.2.0]
- Feature — integração à suíte unificada: identidade "Módulo da suíte Oracle PT-BR" na description, bloco de versão/suíte no corpo, lista das 8 skills e roteamento central via oracle-core-ptbr (nova).

## [2.1.0]
- Feature — novo asset network_acl_setup.sql (DBMS_NETWORK_ACL_ADMIN): ACL para UTL_HTTP/APEX_WEB_SERVICE consumir APIs externas, diagnose de ORA-24247, privilégios mínimos por host/porta. Migrado da geração oracle-apex-24-ptbr (aposentada). suite_size 4→5.

## [2.0.2]
- Docs — adicionado Índice (ToC) em references com +100 linhas (ords-data-dictionary-ptbr.md, ords-rest-services.md); limpeza de artefatos __pycache__. Sem mudança de comportamento.

## [2.0.1]
- Fix — constantes de source type corrigidas (source_type_query_one_row → source_type_collection_item; source_type_collection_query → source_type_collection_feed) em ambos os assets e no reference (as anteriores não existem no package ORDS e faziam define_handler falhar); migração OAUTH → ORDS_SECURITY nos templates (OAUTH/OAUTH_ADMIN depreciados em 24.3, removidos em 25.3); correção da versão de depreciação 24.4 → 24.3 em SKILL.md e data dictionary, com nova seção 24.3; handler GET de exemplo no reference reescrito (SELECT INTO :bind → variáveis locais). Metadados suite_size/release_date/repository adicionados.

## [2.0.0]
- Breaking — divisão de oracle-sql-helper-ptbr v1.6.0 em 6 skills especializadas. Esta skill cobre ORDS REST services e ORDS Data Dictionary (USER_ORDS_*/DBA_ORDS_*). Instale as 6 irmãs para cobertura completa da stack Oracle.

## [1.6.0]
- (oracle-sql-helper-ptbr) Novo reference ords-data-dictionary-ptbr.md — USER_ORDS_*/DBA_ORDS_*, depreciacao OAUTH/ORDS_SECURITY, evolucao 18.x-25.x.

## [1.5.0]
- (oracle-sql-helper-ptbr) Novo reference apex-data-dictionary-ptbr.md — hierarquia APEX_APPLICATION_*/APEX_APPL_*/APEX_WORKSPACE_*, versoes 19-26.1.

## [1.4.0]
- (oracle-sql-helper-ptbr) Remocao de clientes reais. Autoria M&S do Brasil LTDA.

## [1.3.0]
- (oracle-sql-helper-ptbr) Novo reference data-dictionary-ptbr.md — hierarquia Oracle, matriz edicao x tecnologia, evolucao 11g-26ai.
