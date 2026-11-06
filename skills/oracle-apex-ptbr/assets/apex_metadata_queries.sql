--==============================================================================
-- APEX Metadata — queries em views WWV_FLOW_*
--
-- Os apps APEX são armazenados em tabelas do schema APEX_<versão> (ex: APEX_240200
-- em 24.2). As views públicas APEX_APPLICATION_* expõem esse conteúdo de forma
-- estável entre versões. Útil para:
--   - Auditoria de pages, items, processes, dynamic actions
--   - Validação pré-deploy / GMUD
--   - Code review programático (encontrar items sem Value Protected, processes
--     sem error handling, etc.)
--   - Descobrir uso de elementos: "qual page chama a procedure X?"
--
-- Privilégio: views são visíveis por default ao schema parser/owner do app.
-- Workspace SECURITY: app_id filtrado pela autenticação ao workspace.
--==============================================================================

--==============================================================================
-- 1. Visão geral do workspace
--==============================================================================

-- Apps no workspace
SELECT application_id,
       application_name,
       alias,
       version,
       build_status,
       last_updated_on,
       last_updated_by
  FROM apex_applications
 WHERE workspace = 'MEU_WORKSPACE'
 ORDER BY application_id;

-- Pages de um app
SELECT page_id,
       page_name,
       page_alias,
       page_mode,                          -- NORMAL, MODAL, NON_MODAL
       cache_page_yn,
       authentication,
       page_template,
       last_updated_on
  FROM apex_application_pages
 WHERE application_id = :APP_ID
 ORDER BY page_id;

--==============================================================================
-- 2. Items por página
--==============================================================================

SELECT page_id,
       item_name,
       item_label,
       display_as,
       item_source,
       item_default,
       value_protected,                    -- 'Yes' / 'No' — para audit de segurança
       session_state_protection,
       help_text IS NOT NULL AS tem_help
  FROM apex_application_page_items
 WHERE application_id = :APP_ID
   AND page_id        = 49
 ORDER BY display_sequence;

-- Items SEM value_protected (potencial mass-assignment vulnerability)
SELECT page_id,
       item_name,
       display_as
  FROM apex_application_page_items
 WHERE application_id = :APP_ID
   AND value_protected = 'No'
   AND display_as IN ('NATIVE_NUMBER_FIELD',
                      'NATIVE_TEXT_FIELD',
                      'NATIVE_HIDDEN')
 ORDER BY page_id, item_name;

--==============================================================================
-- 3. Interactive Reports — pagination scheme (caso real de auditoria)
--==============================================================================

-- Em deploys, é comum precisar validar se todos os IRs estão usando o
-- pagination scheme correto (ex: Row Ranges X to Y of Z).
-- Os literais do domínio pagination_type variam por versão — confirme antes:
--   SELECT DISTINCT pagination_type FROM apex_application_page_ir;
SELECT page_id,
       region_name,
       pagination_type,
       pagination_display_position,
       maximum_row_count
  FROM apex_application_page_ir
 WHERE application_id = :APP_ID
 ORDER BY page_id;

-- IRs com pagination NÃO esperado (exemplo de auditoria)
SELECT page_id,
       region_name,
       pagination_type
  FROM apex_application_page_ir
 WHERE application_id = :APP_ID
   AND pagination_type NOT IN ('ROW_RANGES_X_TO_Y_OF_Z',
                               'ROW_RANGES_X_TO_Y_WITH_SET_PAGINATION')
 ORDER BY page_id;

--==============================================================================
-- 4. Page Processes — encontrar lógica inline (candidato a refatorar p/ package)
--==============================================================================

-- Processes com PL/SQL grande inline (>50 linhas: cheiro de refatoração)
SELECT page_id,
       process_name,
       process_point,                      -- ON_SUBMIT_BEFORE_COMPUTATION, etc.
       process_type,
       REGEXP_COUNT(process_source, CHR(10)) + 1 AS linhas
  FROM apex_application_page_proc
 WHERE application_id = :APP_ID
   AND process_type   = 'NATIVE_PLSQL'
   AND REGEXP_COUNT(process_source, CHR(10)) > 50
 ORDER BY linhas DESC;

-- Processes que NÃO referenciam algum package (todo o código está inline)
SELECT page_id, process_name,
       LENGTH(process_source) AS tamanho
  FROM apex_application_page_proc
 WHERE application_id = :APP_ID
   AND process_type   = 'NATIVE_PLSQL'
   AND UPPER(process_source) NOT LIKE '%_PKG.%'
   AND UPPER(process_source) NOT LIKE '%PACKAGE%'
   AND LENGTH(process_source) > 500
 ORDER BY tamanho DESC;

--==============================================================================
-- 5. Dynamic Actions
--==============================================================================

SELECT page_id,
       dynamic_action_name,
       event_name,                         -- click, change, ready, etc.
       triggering_element_type,
       triggering_element,
       condition_element_type
  FROM apex_application_page_da
 WHERE application_id = :APP_ID
 ORDER BY page_id, display_sequence;

-- DAs com PL/SQL server-side (potencial gargalo se chamado muito)
SELECT da.page_id,
       da.dynamic_action_name,
       a.action_type,
       a.action_sequence
  FROM apex_application_page_da    da
       JOIN apex_application_page_da_acts a
         ON da.dynamic_action_id = a.dynamic_action_id
 WHERE da.application_id = :APP_ID
   AND a.action_type     IN ('NATIVE_PLSQL', 'NATIVE_EXECUTE_PLSQL_CODE')
 ORDER BY da.page_id;

--==============================================================================
-- 6. Authorization Schemes — quais pages estão protegidas
--==============================================================================

SELECT page_id,
       page_name,
       authorization_scheme,
       authentication
  FROM apex_application_pages
 WHERE application_id = :APP_ID
   AND authorization_scheme IS NULL          -- pages SEM authorization scheme
   AND page_id > 0                           -- ignora global page
 ORDER BY page_id;

-- Definição dos schemes
SELECT authorization_scheme_name,
       scheme_type,                          -- PLSQL_FUNCTION_RETURNING_BOOLEAN, etc.
       attribute_01,                         -- código da função, ou expressão
       error_message
  FROM apex_application_auth_schemes
 WHERE application_id = :APP_ID;

--==============================================================================
-- 7. Buscar referência a um objeto do banco
--==============================================================================

-- "Onde a tabela FATURAS é usada?"
SELECT application_id, page_id, region_name, region_source
  FROM apex_application_page_regions
 WHERE application_id = :APP_ID
   AND UPPER(region_source) LIKE '%FATURAS%'
UNION ALL
SELECT application_id, page_id, process_name, process_source
  FROM apex_application_page_proc
 WHERE application_id = :APP_ID
   AND UPPER(process_source) LIKE '%FATURAS%'
UNION ALL
SELECT application_id, page_id, validation_name, validation_expression1
  FROM apex_application_page_val
 WHERE application_id = :APP_ID
   AND UPPER(validation_expression1) LIKE '%FATURAS%';

-- "Quais pages chamam a procedure PAGAMENTO_PKG.PROCESSAR?"
SELECT page_id, process_name
  FROM apex_application_page_proc
 WHERE application_id = :APP_ID
   AND UPPER(process_source) LIKE '%PAGAMENTO_PKG.PROCESSAR%';

--==============================================================================
-- 8. Auditoria de uso (workspace_activity_log)
--==============================================================================

-- Top 10 páginas mais acessadas no último mês
SELECT application_id, page_id,
       COUNT(*) AS hits,
       COUNT(DISTINCT apex_user) AS usuarios_distintos,
       AVG(elapsed_time)         AS tempo_medio_seg
  FROM apex_workspace_activity_log
 WHERE workspace = 'MEU_WORKSPACE'
   AND view_date > SYSDATE - 30
 GROUP BY application_id, page_id
 ORDER BY hits DESC
 FETCH FIRST 10 ROWS ONLY;

-- Páginas SEM acesso nos últimos 6 meses (candidatas a remoção)
SELECT p.page_id, p.page_name
  FROM apex_application_pages p
 WHERE p.application_id = :APP_ID
   AND NOT EXISTS (
         SELECT 1
           FROM apex_workspace_activity_log a
          WHERE a.application_id = p.application_id
            AND a.page_id        = p.page_id
            AND a.view_date      > SYSDATE - 180
       )
 ORDER BY p.page_id;

--==============================================================================
-- 9. Export de metadata (snapshot para versionamento ou comparação)
--==============================================================================

-- Snapshot completo das views relevantes — útil para tirar uma "foto" antes
-- de deploy e comparar depois.

DECLARE
  l_clob CLOB;
BEGIN
  APEX_JSON.initialize_clob_output;
  APEX_JSON.open_object;

  APEX_JSON.write('app_id', :APP_ID);
  APEX_JSON.write('snapshot_em', SYSTIMESTAMP);

  APEX_JSON.open_array('pages');
  FOR r IN (SELECT page_id, page_name, page_alias, last_updated_on
              FROM apex_application_pages
             WHERE application_id = :APP_ID
             ORDER BY page_id) LOOP
    APEX_JSON.open_object;
    APEX_JSON.write('id',         r.page_id);
    APEX_JSON.write('name',       r.page_name);
    APEX_JSON.write('alias',      r.page_alias);
    APEX_JSON.write('updated_on', r.last_updated_on);
    APEX_JSON.close_object;
  END LOOP;
  APEX_JSON.close_array;

  APEX_JSON.close_object;
  l_clob := APEX_JSON.get_clob_output;
  APEX_JSON.free_output;

  INSERT INTO snapshots_apex (app_id, snapshot_em, conteudo)
  VALUES (:APP_ID, SYSTIMESTAMP, l_clob);
  COMMIT;
END;
/

--==============================================================================
-- 10. Padrões úteis
--==============================================================================

/*
PADRÃO A: Pre-deploy validation
  Antes de deploy de versão nova:
    1. Snapshot da metadata atual (queries acima → tabela)
    2. Deploy
    3. Re-snapshot
    4. Diff: pages alteradas, items adicionados/removidos, processes mudados

PADRÃO B: GMUD documentation
  Para acompanhar deploys:
    SELECT page_id, page_name, last_updated_on, last_updated_by
      FROM apex_application_pages
     WHERE application_id = :APP_ID
       AND last_updated_on > TO_DATE('2026-05-01', 'YYYY-MM-DD');

PADRÃO C: Linter caseiro
  Conjunto de queries que pegam violations comuns:
    - Items sensíveis sem value_protected
    - Pages sem authorization scheme
    - Processes inline > 50 linhas
    - IRs sem maximum_row_count
    - DAs encadeadas profundamente (> 5 ações)
  Salve cada query como view; rode em CI/CD antes de aprovar PR.
*/
