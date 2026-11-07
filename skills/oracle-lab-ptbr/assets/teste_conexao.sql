/*
 * teste_conexao.sql — Suíte Oracle PT-BR / oracle-lab-ptbr
 * Confere, em um minuto, se o lab está realmente utilizável.
 * Uso (do seu Windows/Linux/Mac, com SQLcl instalado):
 *   sql sys/SysPassword1@//192.168.56.140:1521/freepdb1 as sysdba @teste_conexao.sql
 * Em container: troque o host por localhost e o serviço por FREEPDB1.
 */

set echo off
set feedback off
set linesize 200
set pagesize 100

prompt
prompt ===== 1. Onde eu me conectei =====
select sys_context('USERENV','DB_NAME')      as banco,
       sys_context('USERENV','CON_NAME')     as container,
       sys_context('USERENV','SERVICE_NAME') as servico,
       user                                  as usuario
from   dual;

prompt
prompt ===== 2. Versao =====
select banner_full from v$version where rownum = 1;
-- 19.x  -> ambiente igual ao dos clientes
-- 23.26 -> 26ai (ver skill oracle-26ai-ptbr antes de usar sintaxe nova)

prompt
prompt ===== 3. PDBs abertos =====
-- Se o seu PDB nao estiver em READ WRITE, a conexao da aplicacao falha com ORA-12514.
-- Correcao: alter pluggable database <nome> open;
--           alter pluggable database <nome> save state;
select name, open_mode, restricted from v$pdbs order by name;

prompt
prompt ===== 4. Memoria e limites =====
select name, display_value
from   v$parameter
where  name in ('sga_target','pga_aggregate_target','cpu_count','processes','db_block_size')
order  by name;

prompt
prompt ===== 5. Espaco nas tablespaces =====
select tablespace_name,
       round(sum(bytes)/1024/1024) as mb_livres
from   dba_free_space
group  by tablespace_name
order  by 1;

prompt
prompt ===== 6. APEX e ORDS instalados? =====
select comp_name, version, status
from   dba_registry
where  comp_name like '%APEX%' or comp_name like '%XDB%';

select username, account_status
from   dba_users
where  username in ('APEX_PUBLIC_USER','ORDS_PUBLIC_USER','ORDS_METADATA')
order  by username;
-- Nenhuma linha = instalado sem APEX/ORDS (INSTALL_APEX=false), o que pode ser o esperado.

prompt
prompt ===== 7. Teste de escrita (cria, grava e apaga) =====
declare
  lc_nome_tabela constant varchar2(30) := 'TB_TESTE_LAB';
begin
  execute immediate 'create table ' || lc_nome_tabela || ' (id number, criado_em date)';
  execute immediate 'insert into ' || lc_nome_tabela || ' values (1, sysdate)';
  commit;
  execute immediate 'drop table ' || lc_nome_tabela || ' purge';
  dbms_output.put_line('Escrita OK — o lab esta utilizavel.');
exception
  when others then
    dbms_output.put_line('Falhou na escrita: ' || sqlerrm);
    raise;
end;
/

prompt
prompt ===== Fim. Tudo respondeu? Tire um snapshot antes de mexer em qualquer coisa. =====
