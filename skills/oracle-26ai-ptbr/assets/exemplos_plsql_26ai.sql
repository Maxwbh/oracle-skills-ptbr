/*
 * exemplos_plsql_26ai.sql — Suíte Oracle PT-BR / oracle-26ai-ptbr
 * PL/SQL, privilégios e ferramentas 23ai/26ai. Naming Trivadis 4.4 + PT-BR.
 * Requisito: Oracle Database 23ai+; itens "26ai" exigem 26ai; "19.28" existe em 19c.
 * Depende das tabelas criadas em exemplos_sql_26ai.sql (tb_clientes, tb_faturas).
 */

-------------------------------------------------------------------------------
-- 1. RESETTABLE (26ai) — package com estado que não lança ORA-04068 após recompilar
-------------------------------------------------------------------------------
create or replace package pkg_config_app resettable as                          -- 26ai
  gc_nome_pacote constant varchar2(30) := 'PKG_CONFIG_APP';
  g_instanciado_em date := sysdate;
  function obter_instanciado_em return date;
end pkg_config_app;
/
create or replace package body pkg_config_app resettable as                     -- 26ai (spec E body)
  function obter_instanciado_em return date is
  begin
    return g_instanciado_em;
  end obter_instanciado_em;
end pkg_config_app;
/
-- Teste: chame numa sessão, recompile o body em outra, chame de novo — sem ORA-04068.
-- 19c: dbms_session.reset_package; ou packages sem estado (g_ mínimo, padrão Trivadis).

-------------------------------------------------------------------------------
-- 2. Transpiler PL/SQL → SQL (23ai) — função simples vira expressão SQL no plano
-------------------------------------------------------------------------------
create or replace function fnc_valor_com_imposto(p_valor in number, p_aliquota in number default 0.2)
  return number deterministic is
begin
  return round(p_valor * (1 + p_aliquota), 2);                                  -- um único RETURN de expressão: elegível
end fnc_valor_com_imposto;
/
alter session set sql_transpiler = 'ON';                                       -- default OFF
select id_fatura, valor from tb_faturas where fnc_valor_com_imposto(valor) > 100;
select * from dbms_xplan.display_cursor(format => 'BASIC +PREDICATE');
-- Predicado aparece como ROUND("VALOR"*1.2,2)>100, não como chamada FNC_… → sem context switch.
-- Inelegível: SQL interno, loops, exceções, coleções, side effects.

-------------------------------------------------------------------------------
-- 3. Dynamic statistics para funções PL/SQL (23ai)
-------------------------------------------------------------------------------
select dbms_stats.get_plsql_prefs('dynamic_stats') as pref_global from dual;  -- CHOOSE
begin
  dbms_stats.set_plsql_prefs(pname => 'dynamic_stats', pvalue => 'ON',
                             ownname => user, function_name => 'FNC_VALOR_COM_IMPOSTO');
end;
/

-------------------------------------------------------------------------------
-- 4. CASE com predicados e múltiplas escolhas (23ai)
-------------------------------------------------------------------------------
declare
  l_percentual number := 85;
  l_faixa      varchar2(20);
begin
  case l_percentual
    when <= 40     then l_faixa := 'OTIMO';
    when <= 70     then l_faixa := 'SEGURO';
    when 75, 80    then l_faixa := 'ATENCAO';
    when > 90      then l_faixa := 'CRITICO';
    else                l_faixa := 'ALERTA';
  end case;
  dbms_output.put_line(l_percentual || ' -> ' || l_faixa);
end;
/

-------------------------------------------------------------------------------
-- 5. BOOLEAN em SQL dinâmico + RETURNING OLD/NEW em coleções (23ai)
-------------------------------------------------------------------------------
declare
  lc_nome_unidade constant varchar2(60) := 'EXEMPLO_BOOLEAN_BIND';
  l_somente_ativos boolean := true;
  l_qtd            number;
  type t_situacoes is table of tb_faturas.situacao%type;
  l_situacoes_ant  t_situacoes;
  l_situacoes_nova t_situacoes;
begin
  execute immediate 'select count(*) from tb_clientes where ativo = :1 or not :2'
    into l_qtd using l_somente_ativos, l_somente_ativos;                       -- bind BOOLEAN direto
  dbms_output.put_line('clientes: ' || l_qtd);

  update tb_faturas set situacao = 'CANCELADO'
  where  situacao = 'PENDENTE' and valor < 20
  returning old situacao, new situacao bulk collect into l_situacoes_ant, l_situacoes_nova;
  dbms_output.put_line('canceladas: ' || l_situacoes_nova.count);
  rollback;
exception
  when others then
    dbms_output.put_line(lc_nome_unidade || ': ' || sqlerrm);
    raise;
end;
/

-------------------------------------------------------------------------------
-- 6. DBMS_DEVELOPER (19.28) — metadata em JSON para ferramentas
-------------------------------------------------------------------------------
select json_serialize(
         dbms_developer.get_metadata(name => 'TB_FATURAS', object_type => 'TABLE', detail => 'TYPICAL')
         pretty) as metadata_json
from dual;

-------------------------------------------------------------------------------
-- 7. Privilégios: DB_DEVELOPER_ROLE, schema privileges, usuário read-only (23ai) — rodar como DBA
-------------------------------------------------------------------------------
-- create user usr_dev identified by "..." quota unlimited on users;
-- grant db_developer_role to usr_dev;                    -- substitui CONNECT + RESOURCE
-- create user usr_bi identified by "...";
-- grant create session to usr_bi;
-- grant select any table on schema owner_app to usr_bi;  -- cobre objetos futuros
-- alter user usr_bi read only;                           -- DML/DDL → ORA-28194
-- select username, read_only from dba_users where username in ('USR_DEV','USR_BI');

-------------------------------------------------------------------------------
-- 8. Priority transactions (23ai) — sessão de lote com prioridade baixa
-------------------------------------------------------------------------------
-- Instância: priority_txns_mode = TRACK primeiro; ROLLBACK só depois de medir.
-- show parameter txn_priority                            -- default HIGH para todos
-- show parameter priority_txns
alter session set txn_priority = 'LOW';                                        -- job noturno cede para OLTP
-- Se for rollbackado: ORA-63302 → tratar e reexecutar o lote.

-------------------------------------------------------------------------------
-- 9. SQL Firewall (23ai) — esqueleto de captura → allow-list (rodar como SQL_FIREWALL_ADMIN)
-------------------------------------------------------------------------------
-- exec dbms_sql_firewall.enable;
-- exec dbms_sql_firewall.create_capture(username => 'USR_APP', top_level_only => false, start_capture => true);
-- ... uso real por dias/semanas (APEX IR/IG geram SQL variável) ...
-- exec dbms_sql_firewall.stop_capture(username => 'USR_APP');
-- exec dbms_sql_firewall.generate_allow_list(username => 'USR_APP');
-- exec dbms_sql_firewall.enable_allow_list(username => 'USR_APP', enforce => dbms_sql_firewall.enforce_all, block => false); -- LOG primeiro
-- select * from dba_sql_firewall_violations where username = 'USR_APP';

-------------------------------------------------------------------------------
-- 10. SQLcl / SQL*Plus ARGUMENT (SQLcl 22.4+, SQL*Plus 23ai) — scripts GMUD com parâmetro nomeado
-------------------------------------------------------------------------------
-- argument 1 prompt 'Schema alvo:' default 'OWNER_APP'
-- alter session set current_schema = &1;
