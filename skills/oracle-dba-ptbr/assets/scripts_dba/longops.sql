-- -----------------------------------------------------------------------------------
-- Arquivo     : assets/scripts_dba/longops.sql
-- Origem      : https://oracle-base.com/dba/monitoring/longops.sql (Tim Hall)
-- Descrição   : Mostra operações longas em andamento (ETA, % completo).
--               Operações como CREATE INDEX, gather_stats, table scan grande
--               aparecem aqui se passarem de ~6s e o servidor estimar duração.
-- Requisitos  : SELECT em v$session_longops.
-- Como chamar : @longops
-- -----------------------------------------------------------------------------------
SET LINESIZE 500
SET PAGESIZE 1000

COLUMN opname      FORMAT A40
COLUMN target      FORMAT A30
COLUMN message     FORMAT A60
COLUMN start_time  FORMAT A20
COLUMN time_remain FORMAT A12

SELECT sid,
       serial#,
       opname,
       target,
       sofar,
       totalwork,
       ROUND(sofar / NULLIF(totalwork, 0) * 100, 1) AS pct_done,
       TO_CHAR(start_time, 'DD-MON HH24:MI:SS')     AS start_time,
       elapsed_seconds                              AS elapsed_sec,
       time_remaining                               AS time_remain,
       message
FROM   v$session_longops
WHERE  sofar < totalwork
ORDER BY start_time DESC;

SET PAGESIZE 14
