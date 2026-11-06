-- -----------------------------------------------------------------------------------
-- Arquivo     : assets/scripts_dba/index_usage.sql
-- Origem      : https://oracle-base.com/dba/monitoring/index_usage.sql (Tim Hall)
-- Descrição   : Lista índices monitorados e indica se foram USADOS desde o monitoring
--               foi ligado. Em 12.2+ prefira v$index_usage_info / dba_index_usage.
-- Requisitos  : SELECT em v$object_usage; ALTER INDEX ... MONITORING USAGE antes.
-- Como chamar : @index_usage
-- Workflow    :
--   1. ALTER INDEX <esquema>.<idx> MONITORING USAGE;
--   2. Aguardar 1-2 semanas de uso típico.
--   3. @index_usage para ver quais NÃO tiveram USED='YES'.
--   4. Avaliar drop dos não-usados (impacto de manutenção em DML).
-- -----------------------------------------------------------------------------------
SET LINESIZE 500
SET PAGESIZE 1000

COLUMN index_name FORMAT A40
COLUMN table_name FORMAT A40

SELECT index_name,
       table_name,
       monitoring,
       used,
       start_monitoring,
       end_monitoring
FROM   v$object_usage
ORDER BY used, index_name;

SET PAGESIZE 14
