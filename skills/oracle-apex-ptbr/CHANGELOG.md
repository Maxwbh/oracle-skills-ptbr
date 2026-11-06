# Changelog — oracle-apex-ptbr

## [2.5.0] - 2026-11-06
- Fix — COMMIT/ROLLBACK alinhados à regra 4 da oracle-plsql-ptbr e ao "APEX não comita": autenticação customizada com contador de tentativas e log de acesso em AUTONOMOUS_TRANSACTION; page processes sem COMMIT; AJAX callbacks que capturam o erro usam SAVEPOINT + ROLLBACK TO; apex_item_legacy.sql afirmava que o page process precisava de COMMIT explícito.
- Fix — IG: FORALL ... INDICES OF (lista vazia não quebra).
- Fix — removido nome de cliente real da matriz de versões (vindo da versão instalada).

## [2.4.2] - 2026-09-15
- Docs — suíte com 10 skills; referência cruzada para montar APEX+ORDS local.

## [2.4.1] - 2026-09-15
- Docs — suíte com 9 skills; referência cruzada para banco 26ai (session state BOOLEAN, duality views).

## [2.4.0] - 2026-09-15
- CRLF→LF em apex_interactive_grid.sql; NÃO ATIVE na description; changelog movido para CHANGELOG.md. Datas 26.1 (GA mai/2026) e suporte 24.1/24.2 reverificadas contra oracle.com/apex.

## [2.3.0]
- Feature — integração à suíte unificada: identidade "Módulo da suíte Oracle PT-BR" na description, bloco de versão/suíte no corpo, lista das 8 skills e roteamento central via oracle-core-ptbr (nova).

## [2.2.0]
- Feature — consolidação da geração oracle-apex-24-ptbr v1.0.0 (aposentada). +10 assets de aprofundamento, todos revisados/corrigidos antes do merge: apex_util_reference (session state, prepare_url, count_click com p_company, reset_pw p_user), apex_collection_reference (carrinho/wizard/working set, overload BLOB correto), apex_application_global (g_x01..g_x20, g_f01..g_f50, upload/download, payload grande via p_clob_01; g_error_message removido — usar APEX_ERROR), apex_authentication_custom (custom scheme, post-auth/sentry SEM parâmetros, OIDC, HTTP Header), apex_debug_patterns (níveis corrigidos 5=APP_ENTER/6=APP_TRACE, APEX_DEBUG.enter, g_debug), apex_json_reference (p_cache, get_boolean via CASE, validação IS JSON), apex_metadata_queries (auditoria/linter via views de metadados), apex_item_legacy (md5_checksum p/ lost update — md5_value não existe), universal_theme_patterns (tokens --ut-*, dark mode sem seletor inventado), apex_json_source (JSON Sources 24.2+). suite_size 9→19.

## [2.1.2]
- Fix — revisão profunda de especialista APEX (10 correções). IG custom save reescrito: G_F01..G_Fnn era padrão de Tabular Form legado (IG não submete via G_Fnn); agora Page Process com Editable Region, binds :NOME_COLUNA e :APEX$ROW_STATUS ('C'/'U'/'D'); removida referência a g_request_data (inexistente); "IG desde APEX 22"→5.1/2017; validation de IG com TO_DATE (binds chegam VARCHAR2). DA Variante 3: G_X01 não existe em "Execute Server-side Code" (só em apex.server.process) — trocado por item via Items to Submit; removidos COMMIT/ROLLBACK explícitos. apex-patterns: authorization function com bind :APP_USER (não compila) → SYS_CONTEXT('APEX$SESSION','APP_USER'); G_X01..G_X10→G_X20. BLOB upload: JS agora fatia Base64 em chunks de 30k (elemento de f01 limita 32767 bytes). Long job: adicionado spec de heavy_job_pkg (body sozinho não compilava, PLS-00313). Process: alerta NEXTVAL em Before Header (queima sequência por render). Data dictionary: headers de versão corrigidos (26.1 GA mai/2026; removido "24.2 LTS atual"/"26.1 preview"); auditoria value_protected IN ('N','No') com nota de domínio por versão.

## [2.1.1]
- Docs — adicionado Índice (ToC) em references com +100 linhas (apex-data-dictionary-ptbr.md, apex-patterns.md); limpeza de artefatos __pycache__. Sem mudança de comportamento.

## [2.1.0]
- Feature — novo reference apex-version-matrix-ptbr.md com matriz detalhada do que é exclusivo de 24.1/24.2/26.1 (verificada nas release notes oficiais), requisitos por versão e dependências de versão de banco (ex.: session state BOOLEAN exige 26ai). SKILL.md ganhou princípio de consciência de versão, tabela-resumo 24 vs 26 e a regra "perguntar a versão-alvo antes de gerar código version-dependente". Notas de compatibilidade adicionadas aos assets base.

## [2.0.1]
- Fix — APEX_ERROR.add_error: parâmetro p_mensagem→p_message (inexistente, quebrava compilação) em 4 assets; APEX_APPLICATION_TEMP_FILES: colunas tipo_mime→mime_type e nome→name (ORA-00904); DBMS_SCHEDULER.create_job: nome_job→job_name e views user_scheduler_* coluna job_name; corrigido disparo de background — APEX_BACKGROUND_PROCESS.execute() não existe, substituído por Execution Chain declarativo (23.1+) com set_progress; alerta no custom save do IG (l_acao_linha nunca populado); versão de referência atualizada para APEX 26.1 (atual; padrões válidos de 24.2+). Metadados suite_size/release_date/repository adicionados.

## [2.0.0]
- Breaking — divisão de oracle-sql-helper-ptbr v1.6.0 em 6 skills especializadas. Esta skill cobre APEX development e APEX Data Dictionary. Instale as 6 irmãs para cobertura completa da stack Oracle.

## [1.6.0]
- (oracle-sql-helper-ptbr) Novo reference ords-data-dictionary-ptbr.md — USER_ORDS_*/DBA_ORDS_*, depreciacao OAUTH/ORDS_SECURITY, evolucao 18.x-25.x.

## [1.5.0]
- (oracle-sql-helper-ptbr) Novo reference apex-data-dictionary-ptbr.md — hierarquia APEX_APPLICATION_*/APEX_APPL_*/APEX_WORKSPACE_*, versoes 19-26.1.

## [1.4.0]
- (oracle-sql-helper-ptbr) Remocao de clientes reais. Autoria M&S do Brasil LTDA.

## [1.3.0]
- (oracle-sql-helper-ptbr) Novo reference data-dictionary-ptbr.md — hierarquia Oracle, matriz edicao x tecnologia, evolucao 11g-26ai.
