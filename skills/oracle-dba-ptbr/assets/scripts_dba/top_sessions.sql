-- -----------------------------------------------------------------------------------
-- Arquivo     : assets/scripts_dba/top_sessions.sql
-- Origem      : https://oracle-base.com/dba/monitoring/top_sessions.sql (Tim Hall)
-- Descrição   : Top sessões consumindo mais CPU/IO no banco (ordenado por value DESC).
-- Requisitos  : SELECT em v$sesstat, v$statname, v$session, v$process.
-- Como chamar : @top_sessions
-- Útil para   : encontrar quem está pesando no banco AGORA (1-shot snapshot).
--               Para análise histórica, prefira AWR/ASH.
-- -----------------------------------------------------------------------------------
SET LINESIZE 500
SET PAGESIZE 1000

COLUMN username     FORMAT A20
COLUMN sid_serial   FORMAT A12
COLUMN spid         FORMAT A10
COLUMN program      FORMAT A40
COLUMN statistic    FORMAT A30

SELECT *
FROM (
  SELECT NVL(s.username, '(oracle)')    AS username,
         s.sid || ',' || s.serial#      AS sid_serial,
         p.spid,
         SUBSTR(s.program, 1, 40)       AS program,
         sn.name                        AS statistic,
         ss.value
  FROM   v$sesstat   ss
         JOIN v$statname sn ON ss.statistic# = sn.statistic#
         JOIN v$session  s  ON ss.sid        = s.sid
         JOIN v$process  p  ON s.paddr       = p.addr
  WHERE  sn.name IN (
           'CPU used by this session',
           'physical reads',
           'physical writes',
           'logical reads',          -- session logical reads em algumas versões
           'session logical reads',
           'user commits',
           'redo size'
         )
    AND  ss.value > 0
  ORDER BY ss.value DESC
)
WHERE ROWNUM <= 30;

SET PAGESIZE 14
