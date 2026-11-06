-- -----------------------------------------------------------------------------------
-- Arquivo     : assets/scripts_dba/session_pga.sql
-- Origem      : https://oracle-base.com/dba/monitoring/session_pga.sql (Tim Hall)
-- Descrição   : Uso de PGA por sessão (alocado, usado, máximo histórico).
--               Útil para investigar OOM, BULK COLLECT sem LIMIT, ou NOCOPY missing.
-- Requisitos  : SELECT em v$session, v$process.
-- Como chamar : @session_pga
-- -----------------------------------------------------------------------------------
SET LINESIZE 500
SET PAGESIZE 1000

COLUMN username    FORMAT A20
COLUMN program     FORMAT A40
COLUMN module      FORMAT A30

SELECT NVL(s.username, '(oracle)')                  AS username,
       s.sid,
       s.serial#,
       p.spid,
       s.module,
       SUBSTR(s.program, 1, 40)                     AS program,
       ROUND(p.pga_used_mem  / 1024 / 1024, 2)      AS pga_usado_mb,
       ROUND(p.pga_alloc_mem / 1024 / 1024, 2)      AS pga_alocado_mb,
       ROUND(p.pga_max_mem   / 1024 / 1024, 2)      AS pga_max_mb
FROM   v$session s
       JOIN v$process p ON s.paddr = p.addr
WHERE  s.type = 'USER'
ORDER BY p.pga_alloc_mem DESC;

SET PAGESIZE 14
