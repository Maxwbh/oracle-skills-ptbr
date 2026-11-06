-- -----------------------------------------------------------------------------------
-- Arquivo     : assets/scripts_dba/invalid_objects_quick.sql
-- Origem      : https://oracle-base.com/dba/monitoring/invalid_objects.sql (Tim Hall)
-- Descrição   : Lista objetos inválidos no banco. Versão "quick" para diagnose.
--               Para recompilar em lote, ver assets/recompile_invalid_objects.sql.
-- Requisitos  : SELECT em dba_objects (ou user_objects se sem privilégio).
-- Como chamar : @invalid_objects_quick
-- -----------------------------------------------------------------------------------
COLUMN owner       FORMAT A30
COLUMN object_name FORMAT A40
COLUMN object_type FORMAT A20

SELECT owner,
       object_type,
       object_name,
       status
FROM   dba_objects
WHERE  status = 'INVALID'
ORDER BY owner, object_type, object_name;
