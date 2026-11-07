/*
 * exemplos_sql_26ai.sql — Suíte Oracle PT-BR / oracle-26ai-ptbr
 * Exemplos executáveis das novidades SQL 23ai/26ai, com naming Trivadis 4.4 + PT-BR.
 * Requisito: Oracle Database 23ai+ (itens marcados "26ai" exigem 26ai; "19.28" existe em 19c).
 * Cada bloco é independente: rode no SQLcl ou no SQL Developer Web.
 * Convenção: -- 26ai  → exclusivo do 26ai
 *            -- 19.28 → backportado para 19c
 */

-------------------------------------------------------------------------------
-- 0. Descobrir a versão
-------------------------------------------------------------------------------
select version_full from v$instance;
-- 19.28.0.0.0 → IF NOT EXISTS / Annotations / DBMS_DEVELOPER disponíveis
-- 23.26.x     → 26ai

-------------------------------------------------------------------------------
-- 1. DDL idempotente (19.28) + BOOLEAN + DEFAULT ON NULL FOR INSERT AND UPDATE
-------------------------------------------------------------------------------
drop table if exists tb_faturas purge;                                          -- 19.28
drop table if exists tb_clientes purge;                                         -- 19.28

create table if not exists tb_clientes (                                        -- 19.28
  id_cliente     number generated always as identity primary key,
  nome           varchar2(200) not null,
  email          varchar2(200),
  ativo          boolean default true not null,                                 -- 23ai
  criado_em      timestamp default systimestamp not null,
  criado_por     varchar2(60) default coalesce(sys_context('APEX$SESSION','APP_USER'), user) not null
) annotations (Dominio 'Cadastro', Owner_Negocio 'Comercial');                 -- 19.28

create table if not exists tb_faturas (
  id_fatura      number generated always as identity primary key,
  id_cliente     number not null references tb_clientes,
  situacao       varchar2(20) default on null for insert and update 'PENDENTE'  -- 23ai (UPDATE)
                 check (situacao in ('PENDENTE','PAGO','CANCELADO')),
  valor          number(14,2) not null,
  valor_imposto  number(14,2) generated always as (round(valor * 0.2, 2)) materialized, -- 23ai
  emitida_em     date default sysdate not null,
  atualizado_em  timestamp
);

insert into tb_clientes (nome, email, ativo)
values ('Maria', 'maria@exemplo.com.br', true),
       ('João',  'joao@exemplo.com.br',  'N'),      -- 'Y'/'N' aceitos; 'S'/'N' NÃO
       ('Ana',   null,                    1);       -- table values constructor (23ai)
commit;

select id_cliente, nome, ativo from tb_clientes where not ativo;               -- BOOLEAN direto no WHERE

update tb_faturas set situacao = null where id_fatura = -1;                    -- viraria 'PENDENTE', não NULL

-------------------------------------------------------------------------------
-- 2. Domain reutilizável (23ai)
-------------------------------------------------------------------------------
drop domain if exists dom_email;
create domain dom_email as varchar2(200)
  constraint chk_dom_email check (regexp_like(dom_email, '^(\S+)@(\S+)\.(\S+)$'))
  display lower(dom_email)
  order   lower(dom_email)
  annotations (Descricao 'E-mail validado por regexp');

alter table tb_clientes modify (email dom_email);
select nome, domain_display(email) as email_exibicao from tb_clientes order by domain_order(email);

-------------------------------------------------------------------------------
-- 3. DML: VALUES multi-linha, UPDATE/DELETE com JOIN, RETURNING OLD/NEW, INSERT BY NAME (23.9)
-------------------------------------------------------------------------------
insert into tb_faturas (id_cliente, valor)
values (1, 100), (1, 250.50), (2, 80);
commit;

-- reajuste → UPDATE direto por JOIN (equivalente 19c: MERGE)
with reajustes (id_cliente, fator) as (values (1, 1.10), (2, 1.05))
update tb_faturas f
set    f.valor = round(f.valor * r.fator, 2), f.atualizado_em = systimestamp
from   reajustes r
where  f.id_cliente = r.id_cliente
and    f.situacao   = 'PENDENTE';

-- DELETE por JOIN
delete from tb_faturas f
from   tb_clientes c
where  f.id_cliente = c.id_cliente
and    not c.ativo
and    f.situacao = 'CANCELADO';

-- RETURNING OLD/NEW em bloco PL/SQL
declare
  l_situacao_ant  tb_faturas.situacao%type;
  l_situacao_nova tb_faturas.situacao%type;
begin
  update tb_faturas
  set    situacao = 'PAGO', atualizado_em = systimestamp
  where  id_fatura = 1
  returning old situacao, new situacao into l_situacao_ant, l_situacao_nova;
  dbms_output.put_line('Fatura 1: ' || l_situacao_ant || ' -> ' || l_situacao_nova);
end;
/

-- INSERT BY NAME (23.9): casa por alias, não por posição
insert into tb_faturas by name
select 2 as id_cliente, 999 as valor, 'PENDENTE' as situacao from dual;
insert into tb_faturas set id_cliente = 2, valor = 12.5;                        -- 23.9
commit;

-------------------------------------------------------------------------------
-- 4. Consulta: SELECT sem FROM, GROUP BY ALL (23.9), QUALIFY (26ai), FILTER (26ai), calendar (26ai)
-------------------------------------------------------------------------------
select sysdate, user, uuid();                                                  -- sem FROM; uuid() 23.9

select c.nome, f.situacao, count(*) qtd, sum(f.valor) total
from   tb_faturas f join tb_clientes c on c.id_cliente = f.id_cliente
group by all                                                                   -- 23.9
order by total desc;

select id_fatura, id_cliente, valor,
       rank() over (partition by id_cliente order by valor desc) as posicao
from   tb_faturas
qualify posicao <= 2;                                                          -- 26ai (equiv. 19c: subquery inline)

select count(*)   filter (where situacao = 'PAGO')     as qtd_pagas,           -- 26ai
       sum(valor) filter (where situacao = 'PENDENTE') as valor_pendente,      -- 19c: SUM(CASE WHEN … END)
       sum(valor) filter (where emitida_em >= calendar_month_start_date(sysdate)) as valor_mes
from   tb_faturas;

select calendar_month(sysdate)             as mes,                              -- 26ai
       calendar_week(sysdate)              as semana,
       calendar_quarter_end_date(sysdate)  as fim_trimestre,
       calendar_add_months(sysdate, 3)     as daqui_3_meses,
       ceil(sysdate, 'MM')                 as primeiro_dia_prox_mes;            -- 23ai: CEIL/FLOOR em datas

-------------------------------------------------------------------------------
-- 5. Lock-free reservations (23ai) — contador sem bloqueio
-------------------------------------------------------------------------------
drop table if exists tb_estoque purge;
create table tb_estoque (
  id_produto   number primary key,
  qtd_vendida  number reservable check (qtd_vendida >= 0)
);
insert into tb_estoque values (1, 0);
commit;
update tb_estoque set qtd_vendida = qtd_vendida + 5 where id_produto = 1;      -- outra sessão faz o mesmo sem esperar
-- commit aplica a reserva; SET qtd_vendida = 100 (absoluto) NÃO usa a reserva
commit;

-------------------------------------------------------------------------------
-- 6. Assertion (26ai) — regra multi-linha verificada no commit
-------------------------------------------------------------------------------
drop assertion if exists asr_limite_pendente_cliente;
create assertion asr_limite_pendente_cliente check (
  not exists (
    select 1 from tb_faturas where situacao = 'PENDENTE'
    group by id_cliente having sum(valor) > 100000
  )
);
-- violação → ORA-08601. Custo: reavaliada por transação — não usar para regra de linha.

-------------------------------------------------------------------------------
-- 7. JSON-Relational Duality View (23ai) — API JSON de leitura/escrita
-------------------------------------------------------------------------------
create or replace json relational duality view dv_clientes as
select json {'_id'     : c.id_cliente,
             'nome'    : c.nome,
             'email'   : c.email,
             'ativo'   : c.ativo,
             'faturas' : [ select json {'id' : f.id_fatura, 'situacao' : f.situacao, 'valor' : f.valor}
                           from   tb_faturas f with insert update delete
                           where  f.id_cliente = c.id_cliente ]}
from tb_clientes c with insert update delete;

select json_serialize(data pretty) from dv_clientes where json_value(data, '$._id') = 1;
-- ORDS: ords.enable_object(p_object => 'DV_CLIENTES') → GET/POST/PUT/DELETE sem handler

-------------------------------------------------------------------------------
-- 8. Schema privileges (23ai) — app user sem grant objeto a objeto (rodar como owner/DBA)
-------------------------------------------------------------------------------
-- grant select any table, insert any table, update any table, delete any table on schema owner_app to usr_app;
-- grant execute any procedure, select any sequence on schema owner_app to usr_app;
-- select * from dba_schema_privs where grantee = 'USR_APP';

-------------------------------------------------------------------------------
-- 9. Limpeza
-------------------------------------------------------------------------------
-- drop view dv_clientes; drop assertion if exists asr_limite_pendente_cliente;
-- drop table if exists tb_estoque purge; drop table if exists tb_faturas purge;
-- drop table if exists tb_clientes purge; drop domain if exists dom_email;
