-- -----------------------------------------------------------------------------------
-- Arquivo     : assets/scripts_dba/locked_objects.sql
-- Origem      : https://oracle-base.com/dba/monitoring/locked_objects.sql (Tim Hall)
-- Descrição   : Lista todos os objetos bloqueados (locks) no banco.
-- Requisitos  : SELECT em v$locked_object, v$session, dba_objects.
-- Como chamar : @locked_objects
-- Adaptação   : header e legendas em PT-BR; nomes de coluna preservados (V$).
-- -----------------------------------------------------------------------------------
SET LINESIZE 500
SET PAGESIZE 1000
SET VERIFY OFF

COLUMN username     FORMAT A20
COLUMN object_owner FORMAT A20
COLUMN object_name  FORMAT A30
COLUMN locked_mode  FORMAT A15
COLUMN os_user_name FORMAT A20

SELECT lo.session_id AS sid,
       s.serial#,
       NVL(lo.oracle_username, '(oracle)') AS username,
       o.owner                              AS object_owner,
       o.object_name,
       DECODE(lo.locked_mode, 0, 'None',
                              1, 'Null (NULL)',
                              2, 'Row-S (SS)',
                              3, 'Row-X (SX)',
                              4, 'Share (S)',
                              5, 'S/Row-X (SSX)',
                              6, 'Exclusive (X)',
                              lo.locked_mode) AS locked_mode,
       lo.os_user_name
FROM   v$locked_object lo
       JOIN dba_objects o ON o.object_id = lo.object_id
       JOIN v$session   s ON lo.session_id = s.sid
ORDER BY 1, 2, 3, 4;

SET PAGESIZE 14
SET VERIFY ON
