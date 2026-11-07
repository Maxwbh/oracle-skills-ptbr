-- -----------------------------------------------------------------------------------
-- Arquivo     : assets/scripts_dba/redo_by_hour.sql
-- Origem      : https://oracle-base.com/dba/monitoring/redo_by_hour.sql (Tim Hall)
-- Descrição   : Volume de redo gerado por hora nos últimos N dias.
--               Útil para dimensionar archivelog/undo e identificar horários de pico.
-- Requisitos  : SELECT em v$log_history.
-- Como chamar : @redo_by_hour
-- -----------------------------------------------------------------------------------
SET LINESIZE 500
SET PAGESIZE 1000

COLUMN day FORMAT A12

SELECT TO_CHAR(first_time, 'YYYY-MM-DD')           AS day,
       SUM(DECODE(TO_CHAR(first_time, 'HH24'), '00', 1, 0)) AS "00",
       SUM(DECODE(TO_CHAR(first_time, 'HH24'), '01', 1, 0)) AS "01",
       SUM(DECODE(TO_CHAR(first_time, 'HH24'), '02', 1, 0)) AS "02",
       SUM(DECODE(TO_CHAR(first_time, 'HH24'), '03', 1, 0)) AS "03",
       SUM(DECODE(TO_CHAR(first_time, 'HH24'), '04', 1, 0)) AS "04",
       SUM(DECODE(TO_CHAR(first_time, 'HH24'), '05', 1, 0)) AS "05",
       SUM(DECODE(TO_CHAR(first_time, 'HH24'), '06', 1, 0)) AS "06",
       SUM(DECODE(TO_CHAR(first_time, 'HH24'), '07', 1, 0)) AS "07",
       SUM(DECODE(TO_CHAR(first_time, 'HH24'), '08', 1, 0)) AS "08",
       SUM(DECODE(TO_CHAR(first_time, 'HH24'), '09', 1, 0)) AS "09",
       SUM(DECODE(TO_CHAR(first_time, 'HH24'), '10', 1, 0)) AS "10",
       SUM(DECODE(TO_CHAR(first_time, 'HH24'), '11', 1, 0)) AS "11",
       SUM(DECODE(TO_CHAR(first_time, 'HH24'), '12', 1, 0)) AS "12",
       SUM(DECODE(TO_CHAR(first_time, 'HH24'), '13', 1, 0)) AS "13",
       SUM(DECODE(TO_CHAR(first_time, 'HH24'), '14', 1, 0)) AS "14",
       SUM(DECODE(TO_CHAR(first_time, 'HH24'), '15', 1, 0)) AS "15",
       SUM(DECODE(TO_CHAR(first_time, 'HH24'), '16', 1, 0)) AS "16",
       SUM(DECODE(TO_CHAR(first_time, 'HH24'), '17', 1, 0)) AS "17",
       SUM(DECODE(TO_CHAR(first_time, 'HH24'), '18', 1, 0)) AS "18",
       SUM(DECODE(TO_CHAR(first_time, 'HH24'), '19', 1, 0)) AS "19",
       SUM(DECODE(TO_CHAR(first_time, 'HH24'), '20', 1, 0)) AS "20",
       SUM(DECODE(TO_CHAR(first_time, 'HH24'), '21', 1, 0)) AS "21",
       SUM(DECODE(TO_CHAR(first_time, 'HH24'), '22', 1, 0)) AS "22",
       SUM(DECODE(TO_CHAR(first_time, 'HH24'), '23', 1, 0)) AS "23"
FROM   v$log_history
WHERE  first_time > SYSDATE - 7
GROUP BY TO_CHAR(first_time, 'YYYY-MM-DD')
ORDER BY 1 DESC;

SET PAGESIZE 14
