-- -----------------------------------------------------------------------------------
-- Arquivo     : assets/scripts_dba/lock_tree.sql
-- Origem      : https://oracle-base.com/dba/10g/lock_tree.sql (Tim Hall)
-- Descrição   : Mostra a hierarquia de sessões bloqueadoras/bloqueadas.
--               A coluna username vem indentada conforme o nível da cadeia.
-- Requisitos  : SELECT em v$session (com blocking_session).
-- Como chamar : @lock_tree
-- Útil para   : identificar a sessão "root" responsável por uma cadeia de locks.
-- -----------------------------------------------------------------------------------
SET LINESIZE 500
SET PAGESIZE 1000

COLUMN username   FORMAT A30
COLUMN osuser     FORMAT A10
COLUMN machine    FORMAT A25
COLUMN logon_time FORMAT A20

SELECT LEVEL,
       LPAD(' ', (LEVEL - 1) * 2, ' ') || NVL(s.username, '(oracle)') AS username,
       s.osuser,
       s.sid,
       s.serial#,
       s.lockwait,
       s.status,
       s.module,
       s.machine,
       s.program,
       TO_CHAR(s.logon_time, 'DD-MON-YYYY HH24:MI:SS') AS logon_time
FROM   v$session s
WHERE  LEVEL > 1
       OR EXISTS (SELECT 1
                  FROM   v$session
                  WHERE  blocking_session = s.sid)
CONNECT BY PRIOR s.sid = s.blocking_session
START WITH s.blocking_session IS NULL;

SET PAGESIZE 14
