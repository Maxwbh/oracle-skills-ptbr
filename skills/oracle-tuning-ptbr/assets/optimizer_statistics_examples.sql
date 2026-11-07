--==============================================================================
-- Template: Estatísticas do Optimizer — exemplos prontos
--
-- Coleção de comandos DBMS_STATS para o dia a dia de tuning: coleta correta,
-- preferências, histogramas, estatísticas estendidas, SQL Plan Directives,
-- e ciclo de vida (lock/pending/restore/retention/report) + Statistics Advisor.
--
-- Ajuste os nomes de schema/tabela/coluna. Exemplos usam CLIENTES/FATURAS.
--==============================================================================


--==============================================================================
-- 1. COLETA RECOMENDADA
--==============================================================================

-- Tabela: deixe o Oracle decidir amostra, histogramas e paralelismo
BEGIN
  DBMS_STATS.gather_table_stats(
    ownname          => USER,
    tabname          => 'FATURAS',
    estimate_percent => DBMS_STATS.auto_sample_size,   -- NÃO fixe percentual
    method_opt       => 'FOR ALL COLUMNS SIZE AUTO',   -- histograma onde compensa
    cascade          => TRUE,                           -- inclui índices
    degree           => DBMS_STATS.auto_degree
  );
END;
/

-- Schema: só o que está stale ou sem stats (ideal para rotina)
EXEC DBMS_STATS.gather_schema_stats(ownname => USER, options => 'GATHER AUTO');

-- Verificar frescor das stats
SELECT table_name, num_rows, sample_size, last_analyzed, stale_stats
  FROM user_tab_statistics
 WHERE table_name IN ('CLIENTES', 'FATURAS');


--==============================================================================
-- 2. PREFERÊNCIAS (hierarquia: tabela > schema > global)
--==============================================================================

-- Ler as preferências globais mais relevantes de uma vez
SELECT DBMS_STATS.get_prefs('ESTIMATE_PERCENT')       estimate_percent,
       DBMS_STATS.get_prefs('METHOD_OPT')             method_opt,
       DBMS_STATS.get_prefs('DEGREE')                 degree,
       DBMS_STATS.get_prefs('STALE_PERCENT')          stale_percent,
       DBMS_STATS.get_prefs('INCREMENTAL')            incremental,
       DBMS_STATS.get_prefs('PUBLISH')                publish,
       DBMS_STATS.get_prefs('AUTO_STAT_EXTENSIONS')   auto_stat_extensions
  FROM dual;

-- Preferência de uma tabela
SELECT DBMS_STATS.get_prefs('STALE_PERCENT', USER, 'FATURAS') FROM dual;

-- Definir preferência só da tabela (não afeta o resto)
EXEC DBMS_STATS.set_table_prefs(USER, 'FATURAS', 'STALE_PERCENT', '13');

-- Tabelas particionadas: coleta incremental (synopses por partição)
EXEC DBMS_STATS.set_table_prefs(USER, 'FATURAS', 'INCREMENTAL', 'TRUE');
EXEC DBMS_STATS.set_table_prefs(USER, 'FATURAS', 'GRANULARITY', 'AUTO');

-- Listar preferências definidas por tabela
SELECT * FROM user_tab_stat_prefs;


--==============================================================================
-- 3. HISTOGRAMAS — para colunas com distribuição assimétrica (skew)
--==============================================================================

-- Forçar histograma numa coluna específica (até 254 buckets)
BEGIN
  DBMS_STATS.gather_table_stats(
    ownname    => USER,
    tabname    => 'FATURAS',
    method_opt => 'FOR COLUMNS status SIZE 254'
  );
END;
/

-- Ver tipo de histograma e nº de buckets (FREQUENCY/TOP-FREQUENCY/HYBRID/HEIGHT BALANCED)
SELECT column_name, num_distinct, histogram, num_buckets
  FROM user_tab_col_statistics
 WHERE table_name = 'FATURAS';

-- Inspecionar os buckets e quantas linhas há em cada
SELECT endpoint_number, endpoint_value,
       endpoint_number
         - LAG(endpoint_number, 1, 0) OVER (ORDER BY endpoint_number) AS linhas_no_bucket
  FROM user_histograms
 WHERE table_name = 'FATURAS'
   AND column_name = 'STATUS'
 ORDER BY endpoint_number;

-- Remover histograma de uma coluna (volta a densidade plana)
EXEC DBMS_STATS.delete_column_stats(USER, 'FATURAS', 'STATUS', col_stat_type => 'HISTOGRAM');


--==============================================================================
-- 4. ESTATÍSTICAS ESTENDIDAS — colunas correlacionadas (column group)
--==============================================================================

-- Sem o column group, o optimizer multiplica seletividades e subestima.
-- Criar o grupo para (id_municipio, uf) que são correlacionados:
SELECT DBMS_STATS.create_extended_stats(USER, 'CLIENTES', '(id_municipio, uf)') FROM dual;

-- Coletar com histogramas onde houver skew
EXEC DBMS_STATS.gather_table_stats(USER, 'CLIENTES', method_opt => 'FOR ALL COLUMNS SIZE SKEWONLY');

-- Conferir as extensões e suas estatísticas
SELECT e.extension AS col_group, t.num_distinct, t.histogram
  FROM user_stat_extensions e
  JOIN user_tab_col_statistics t ON t.column_name = e.extension_name
                                 AND t.table_name = e.table_name
 WHERE e.table_name = 'CLIENTES';

-- Remover
EXEC DBMS_STATS.drop_extended_stats(USER, 'CLIENTES', '(id_municipio, uf)');


--==============================================================================
-- 5. SQL PLAN DIRECTIVES e dynamic statistics
--==============================================================================

-- 19c: optimizer_adaptive_statistics é FALSE por padrão (estabilidade de plano).
-- Para experimentar directives numa sessão de teste:
ALTER SESSION SET optimizer_adaptive_statistics = TRUE;

-- Após uma query com erro de estimativa, ver se foi marcada para reotimizar
SELECT sql_id, child_number, executions, is_reoptimizable, sql_text
  FROM v$sql
 WHERE sql_text LIKE '%/* minha_query */%'
   AND sql_text NOT LIKE '%v$sql%';

-- Gravar as directives da memória no dicionário
EXEC DBMS_SPD.flush_sql_plan_directive;

-- Consultar directives do schema
SELECT TO_CHAR(d.directive_id) dir_id, o.owner, o.object_name,
       o.subobject_name AS coluna, o.object_type, d.type, d.state, d.reason
  FROM dba_sql_plan_directives d
  JOIN dba_sql_plan_dir_objects o ON o.directive_id = d.directive_id
 WHERE o.owner = USER
 ORDER BY 1;

-- Remover uma directive
-- EXEC DBMS_SPD.drop_sql_plan_directive(directive_id => <dir_id>);


--==============================================================================
-- 6. LOCK — congelar estatísticas (estabilidade de plano)
--==============================================================================

EXEC DBMS_STATS.lock_table_stats(USER, 'FATURAS');
EXEC DBMS_STATS.unlock_table_stats(USER, 'FATURAS');

SELECT table_name, stattype_locked
  FROM user_tab_statistics
 WHERE table_name = 'FATURAS';


--==============================================================================
-- 7. PENDING — testar stats antes de publicar
--==============================================================================

EXEC DBMS_STATS.set_table_prefs(USER, 'FATURAS', 'PUBLISH', 'FALSE');  -- passa a não publicar
EXEC DBMS_STATS.gather_table_stats(USER, 'FATURAS');                    -- vira pending

ALTER SESSION SET optimizer_use_pending_statistics = TRUE;             -- testar nesta sessão
-- ... rode as queries e compare os planos ...

EXEC DBMS_STATS.publish_pending_stats(USER, 'FATURAS');                 -- aprovar
-- EXEC DBMS_STATS.delete_pending_stats(USER, 'FATURAS');               -- ou descartar
EXEC DBMS_STATS.set_table_prefs(USER, 'FATURAS', 'PUBLISH', 'TRUE');   -- voltar ao normal


--==============================================================================
-- 8. RESTORE / RETENTION — histórico de estatísticas
--==============================================================================

-- Quando foram alteradas
SELECT table_name, stats_update_time
  FROM user_tab_stats_history
 WHERE table_name = 'FATURAS'
 ORDER BY stats_update_time DESC;

-- Restaurar para um instante anterior (desfaz um gather ruim)
EXEC DBMS_STATS.restore_table_stats(USER, 'FATURAS', SYSTIMESTAMP - 1);

-- Retenção do histórico
SELECT DBMS_STATS.get_stats_history_availability FROM dual;
SELECT DBMS_STATS.get_stats_history_retention    FROM dual;   -- default 31 dias
EXEC DBMS_STATS.alter_stats_history_retention(45);


--==============================================================================
-- 9. REPORT — relatório de operações de coleta
--==============================================================================

SET LONG 100000
VARIABLE rel CLOB;
BEGIN
  :rel := DBMS_STATS.report_stats_operations(
    since        => SYSDATE - 10,
    until        => SYSDATE,
    detail_level => 'TYPICAL',
    format       => 'TEXT');   -- ou 'HTML'
END;
/
PRINT rel;


--==============================================================================
-- 10. COLETA AUTOMÁTICA — status do job
--==============================================================================

SELECT client_name, status, total_cpu_last_30_days
  FROM dba_autotask_client
 WHERE client_name LIKE '%optimizer stats%';


--==============================================================================
-- 11. OPTIMIZER STATISTICS ADVISOR
--==============================================================================

-- Ler o relatório da task automática diária
SELECT DBMS_STATS.report_advisor_task('AUTO_STATS_ADVISOR_TASK') AS report FROM dual;

-- Executar uma task manual (requer privilégio ADVISOR)
DECLARE
  l_task VARCHAR2(128);
BEGIN
  l_task := DBMS_STATS.create_advisor_task('STATS_ADVISOR_MANUAL');
  l_task := DBMS_STATS.execute_advisor_task('STATS_ADVISOR_MANUAL');
END;
/

SELECT DBMS_STATS.report_advisor_task('STATS_ADVISOR_MANUAL') FROM dual;   -- recomendações
SELECT DBMS_STATS.script_advisor_task('STATS_ADVISOR_MANUAL') FROM dual;   -- script de correção
-- Revise o script ANTES de implementar:
-- SELECT DBMS_STATS.implement_advisor_task('STATS_ADVISOR_MANUAL') FROM dual;


--==============================================================================
-- 12. SQL TUNING ADVISOR + SQL PROFILE (para um SQL_ID específico)
--==============================================================================

DECLARE
  l_task VARCHAR2(64);
BEGIN
  l_task := DBMS_SQLTUNE.create_tuning_task(sql_id => '&sql_id');
  DBMS_SQLTUNE.execute_tuning_task(l_task);
  DBMS_OUTPUT.put_line('Task: ' || l_task);
END;
/

-- Ver recomendações da task
SELECT DBMS_SQLTUNE.report_tuning_task('&task_name') FROM dual;

-- Aceitar o SQL Profile recomendado
EXEC DBMS_SQLTUNE.accept_sql_profile(task_name => '&task_name', replace => TRUE);

-- Listar e remover profiles
SELECT name, status FROM dba_sql_profiles;
-- EXEC DBMS_SQLTUNE.drop_sql_profile(name => '<profile_name>', ignore => TRUE);
