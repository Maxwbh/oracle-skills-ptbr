# Novidades SQL — Oracle Database 23ai/26ai

Referência das mudanças de SQL que afetam código do dia a dia. Cada item traz: desde quando, sintaxe, equivalente 19c e armadilhas. Exemplos executáveis em `assets/exemplos_sql_26ai.sql`.

Convenção de versão: **23ai** = disponível desde 23ai (portanto também em 26ai); **23.x** = release update específico; **26ai** = novo no 26ai; **19.28** = backportado para 19c.

## Índice

- [1. DDL](#1-ddl)
  - [1.1 IF [NOT] EXISTS (19.28)](#11-if-not-exists-1928)
  - [1.2 BOOLEAN](#12-boolean)
  - [1.3 Domains](#13-domains)
  - [1.4 Annotations (19.28)](#14-annotations-1928)
  - [1.5 Assertions (26ai)](#15-assertions-26ai)
  - [1.6 DEFAULT ON NULL FOR INSERT AND UPDATE](#16-default-on-null-for-insert-and-update)
  - [1.7 Colunas virtuais materializadas](#17-colunas-virtuais-materializadas)
  - [1.8 Staging tables, MAX_COLUMNS, bigfile default](#18-staging-tables-max_columns-bigfile-default)
- [2. DML](#2-dml)
  - [2.1 UPDATE/DELETE com JOIN direto](#21-updatedelete-com-join-direto)
  - [2.2 RETURNING OLD/NEW](#22-returning-oldnew)
  - [2.3 Table values constructor](#23-table-values-constructor)
  - [2.4 INSERT BY NAME / INSERT SET (23.9)](#24-insert-by-name--insert-set-239)
  - [2.5 Lock-free reservations](#25-lock-free-reservations)
  - [2.6 Priority transactions](#26-priority-transactions)
- [3. Consulta](#3-consulta)
  - [3.1 SELECT sem FROM](#31-select-sem-from)
  - [3.2 GROUP BY ALL (23.9) e alias em GROUP BY/HAVING](#32-group-by-all-239-e-alias-em-group-byhaving)
  - [3.3 QUALIFY (26ai)](#33-qualify-26ai)
  - [3.4 FILTER em agregações (26ai)](#34-filter-em-agregações-26ai)
  - [3.5 Calendar functions (26ai)](#35-calendar-functions-26ai)
  - [3.6 CEIL/FLOOR para datas, UUID() (23.9), FUZZY_MATCH](#36-ceilfloor-para-datas-uuid-239-fuzzy_match)
- [4. JSON](#4-json)
  - [4.1 Tipo JSON e JSON_BEHAVIOR](#41-tipo-json-e-json_behavior)
  - [4.2 JSON-Relational Duality Views](#42-json-relational-duality-views)
  - [4.3 JSON Collections, JSON Schema, precheck](#43-json-collections-json-schema-precheck)
- [5. Tabela-resumo por versão](#5-tabela-resumo-por-versão)

---

## 1. DDL

### 1.1 IF [NOT] EXISTS (19.28)

```sql
create table if not exists tb_clientes (id_cliente number primary key);
create sequence if not exists sq_clientes;
drop table if exists tb_temporaria purge;
drop procedure if exists prc_antiga;
alter table if exists tb_clientes add (email varchar2(200));
```

- Vale para tabelas, views, sequences, índices, procedures, packages, users, roles, etc.
- **Backport 19c: RU 19.28.** Em 19c mais antigo, mantenha o padrão GMUD com `EXECUTE IMMEDIATE` + `EXCEPTION WHEN e_ja_existe` (ver `oracle-devops-ptbr`).
- `CREATE OR REPLACE … IF NOT EXISTS` não existe: para código (packages/views) use `CREATE OR REPLACE`; `IF NOT EXISTS` é para objetos não substituíveis.
- Liquibase: changesets com `IF NOT EXISTS` ficam idempotentes, mas continue usando `runOnChange="true"` só para código.

### 1.2 BOOLEAN

```sql
create table tb_usuarios (
  id_usuario number generated always as identity,
  ativo      boolean default true not null,
  bloqueado  bool                              -- sinônimo
);
insert into tb_usuarios (ativo, bloqueado) values (true, false), ('Y', 'N'), (1, 0), ('sim', 'nao'); -- 'sim'/'nao' NÃO são aceitos
```

- Literais aceitos: `TRUE/FALSE`, `'true'/'false'`, `'yes'/'no'`, `'on'/'off'`, `1/0`, `'t'/'f'`, `'y'/'n'` (case-insensitive). **Português não é aceito** — `'S'/'N'` falha.
- Em `WHERE`, use direto: `where ativo` / `where not ativo`; funções: `to_boolean()`, `is true`.
- PL/SQL: bind `BOOLEAN` em SQL dinâmico passa a funcionar (`EXECUTE IMMEDIATE … USING l_flag`).
- **Equivalente 19c:** `NUMBER(1) CHECK (col IN (0,1))` ou `VARCHAR2(1) CHECK (col IN ('S','N'))`. A convenção de status PT-BR da suíte (`'ATIVO'/'INATIVO'`) continua válida onde há mais de dois estados.
- APEX: coluna BOOLEAN aparece como switch em IG/forms (26.1). Session state BOOLEAN exige banco 26ai.

### 1.3 Domains

Tipo de dado com regra, formatação e ordenação reutilizáveis.

```sql
create domain dom_email as varchar2(200)
  constraint chk_dom_email check (regexp_like(dom_email, '^(\S+)@(\S+)\.(\S+)$'))
  display lower(dom_email)
  order   lower(dom_email)
  annotations (Descricao 'E-mail validado');

create table tb_contatos (
  id_contato number primary key,
  email      dom_email
);
select domain_display(email), domain_order(email) from tb_contatos;
```

- Domains **single-column**, **multi-column** (CPF + dígito, latitude/longitude) e **flexible** (regra escolhida por discriminador).
- Não muda o tipo físico: a coluna continua `VARCHAR2(200)` para drivers e APEX.
- Dicionário: `USER_DOMAINS`, `USER_DOMAIN_CONSTRAINTS`, `USER_DOMAIN_COLS`.
- **19c:** repita o `CHECK` em cada tabela ou centralize em package de validação.

### 1.4 Annotations (19.28)

Metadados chave/valor em tabelas, colunas, views, índices, domains — sucessor estruturado dos `COMMENT`.

```sql
create table tb_faturas (
  id_fatura   number primary key annotations (Sensibilidade 'Baixa'),
  valor_total number(14,2)       annotations (Sensibilidade 'Alta', Mascara 'Moeda')
) annotations (Dominio 'Financeiro', Owner_Negocio 'Faturamento');

alter table tb_faturas annotations (add Retencao '5 anos');
alter table tb_faturas modify (valor_total annotations (drop Mascara));
select * from user_annotations_usage where object_name = 'TB_FATURAS';
```

- Sem validação de chave/valor — combine com um catálogo (package) para padronizar nomes.
- APEX 24.2+ lê annotations para sugerir labels/formatos; ORDS expõe via metadata.

### 1.5 Assertions (26ai)

Naming: prefixo `asr_` (regra dbLinter G-9208 — o Trivadis 4.4 não cobre assertions).

Constraint declarativa de escopo amplo (multi-linha, multi-tabela), verificada no commit.

```sql
create assertion asr_salario_presidente check (
  exists (select 1 from tb_funcionarios where cargo = 'PRESIDENTE' and salario between 4000 and 10000)
);
-- violação: ORA-08601: SQL assertion (…) violated
```

- Custo: reavaliada a cada transação que toque as tabelas envolvidas — não substitua `CHECK`/`FK` simples por assertion.
- **19c:** trigger `AFTER STATEMENT` (compound trigger) ou validação no package.

### 1.6 DEFAULT ON NULL FOR INSERT AND UPDATE

```sql
create table tb_pedidos (
  id_pedido number primary key,
  situacao  varchar2(20) default on null for insert and update 'PENDENTE'
);
update tb_pedidos set situacao = null;  -- vira 'PENDENTE'
```

- 12c: `DEFAULT ON NULL` só no INSERT. 23ai: também no UPDATE.

### 1.7 Colunas virtuais materializadas

```sql
valor_com_imposto number(12,2) generated always as (round(valor * 1.2, 2)) materialized
```

- Armazena o resultado (custo em disco, ganho em leitura); `virtual` continua sendo o default.

### 1.8 Staging tables, MAX_COLUMNS, bigfile default

- `CREATE TABLE … FOR STAGING` / `ALTER TABLE … FOR STAGING`: tabela volátil de carga, otimizada para direct path; `USER_TABLES.STAGING`.
- `MAX_COLUMNS = EXTENDED` permite até 4096 colunas (default 1000). Wide tables têm custo em parse e em ferramentas — evite salvo caso legítimo (IoT, ML features).
- Tablespaces criadas em 23ai+ são **bigfile por default**; `ALTER TABLESPACE … SHRINK SPACE` funciona em bigfile (23ai) e smallfile (23.7).

## 2. DML

### 2.1 UPDATE/DELETE com JOIN direto

```sql
update tb_produtos a
set    a.preco = b.preco_novo
from   tb_reajustes b
where  a.id_produto = b.id_produto;

delete from tb_itens a
from   tb_pedidos b
where  a.id_pedido = b.id_pedido and b.situacao = 'CANCELADO';
```

- Substitui `MERGE` quando só há UPDATE, e subqueries correlacionadas em DELETE.
- Se o join retornar mais de uma linha por alvo, o resultado é indeterminado (mesma regra do `MERGE` — `ORA-30926` não é lançado aqui). Garanta unicidade.
- **19c:** `MERGE INTO … USING … WHEN MATCHED THEN UPDATE` ou `DELETE WHERE id IN (SELECT …)`.

### 2.2 RETURNING OLD/NEW

```sql
update tb_faturas
set    situacao = 'PAGO'
where  id_fatura = :id
returning old situacao, new situacao, old atualizado_em into l_situacao_ant, l_situacao_nova, l_data_ant;
```

- Funciona com `BULK COLLECT INTO` em coleções.
- Elimina o `SELECT … FOR UPDATE` prévio apenas para auditar valor anterior.
- **19c:** `RETURNING` retorna só o valor novo; o antigo exige leitura antes do DML.

### 2.3 Table values constructor

```sql
insert into tb_situacoes (codigo, descricao)
values ('PEN', 'Pendente'), ('PAG', 'Pago'), ('CAN', 'Cancelado');

with tmp (id, nome) as (values (1, 'a'), (2, 'b'))
select * from tmp;

merge into tb_alvo a
using (values (1, 'x'), (2, 'y')) b (id, valor) on (a.id = b.id)
when matched then update set a.valor = b.valor
when not matched then insert values (b.id, b.valor);
```

- A instrução é atômica: uma linha inválida falha o `INSERT` inteiro.
- **19c:** `INSERT ALL … SELECT 1 FROM dual` ou `UNION ALL` de `dual`.

### 2.4 INSERT BY NAME / INSERT SET (23.9)

```sql
insert into tb_funcionarios by name
select 9999 as id_funcionario, 'MARIA' as nome, 'DBA' as cargo from dual; -- casa por alias

insert into tb_funcionarios set id_funcionario = 9998, nome = 'JOAO', cargo = 'DEV';
```

- Elimina erros de posição em tabelas largas; colunas ausentes recebem default/NULL.

### 2.5 Lock-free reservations

Coluna numérica `RESERVABLE`: incrementos/decrementos vão para um *reservation journal* e só são aplicados no commit, sem bloquear outras sessões.

```sql
create table tb_estoque (
  id_produto   number primary key,
  qtd_vendida  number reservable check (qtd_vendida >= 0)
);
update tb_estoque set qtd_vendida = qtd_vendida + 10 where id_produto = 1; -- não bloqueia
```

- Só `+=`/`-=` relativos; `SET col = 100` absoluto não usa reserva.
- Não se pode `DELETE` a linha com reserva pendente nem `DROP` a tabela com coluna reservable (remova `NOT RESERVABLE` antes).
- Caso de uso: contadores de venda/saldo com alta concorrência (APEX + ORDS).

### 2.6 Priority transactions

Sessão de menor prioridade que bloqueia uma de maior prioridade é **rollbackada automaticamente** (`ORA-63302`).

- Parâmetros: `TXN_PRIORITY` (**default HIGH** — por isso nada muda até você baixar a prioridade de lotes com `ALTER SESSION SET txn_priority = 'LOW'`), `PRIORITY_TXNS_MODE` (`ROLLBACK` | `TRACK`), `PRIORITY_TXNS_HIGH_WAIT_TARGET`, `PRIORITY_TXNS_MEDIUM_WAIT_TARGET` (segundos).
- Comece em `TRACK` e leia `V$TXN_PRIORITY_STATS`… antes de ligar `ROLLBACK` em produção.
- Aplicação precisa tratar `ORA-63302`/`ORA-63300` e reexecutar.

## 3. Consulta

### 3.1 SELECT sem FROM

```sql
select sysdate;
select sq_clientes.nextval;
```

- Também em PL/SQL (`SELECT … INTO`). `DUAL` continua existindo; não é obrigatório trocar.

### 3.2 GROUP BY ALL (23.9) e alias em GROUP BY/HAVING

```sql
select uf, cidade, count(*) from tb_clientes group by all;
select uf as estado, count(*) qtd from tb_clientes group by estado having qtd > 10;
```

- `ALL` agrupa por todas as colunas não agregadas do `SELECT` — evite em views de produção (mudança no `SELECT` muda o agrupamento silenciosamente).

### 3.3 QUALIFY (26ai)

```sql
select id_funcionario, id_depto, salario,
       rank() over (partition by id_depto order by salario desc) as posicao
from   tb_funcionarios
qualify posicao <= 3;
```

- É o `HAVING` das funções analíticas; substitui subquery inline.

### 3.4 FILTER em agregações (26ai)

```sql
select count(*) filter (where situacao = 'PAGO')      as pagas,
       sum(valor) filter (where situacao = 'PENDENTE') as valor_pendente
from   tb_faturas;
```

- **19c:** `COUNT(CASE WHEN … THEN 1 END)` / `SUM(CASE WHEN … THEN valor END)`.

### 3.5 Calendar functions (26ai)

`CALENDAR_YEAR`, `_QUARTER`, `_MONTH`, `_WEEK`, `_DAY`; `_START_DATE`/`_END_DATE` para cada granularidade; `CALENDAR_ADD_DAYS/WEEKS/MONTHS/QUARTERS/YEARS`; `CALENDAR_DAY_OF_WEEK/MONTH/QUARTER/YEAR`; `CALENDAR_FISCAL_YEAR_START`; `CALENDAR_SINCE`.

```sql
select calendar_month_start_date(sysdate), calendar_month_end_date(sysdate),
       calendar_week(sysdate), calendar_add_months(sysdate, 3);
```

- **19c:** `TRUNC(d,'MM')`, `LAST_DAY(d)`, `TO_CHAR(d,'IW')`, `ADD_MONTHS`.

### 3.6 CEIL/FLOOR para datas, UUID() (23.9), FUZZY_MATCH

- `CEIL(sysdate, 'MM')` / `FLOOR(ts, 'HH')` aceitam formato como `TRUNC`/`ROUND`.
- `UUID()` retorna 128 bits não previsíveis (v4); `SYS_GUID()` é sequencial/previsível. Para PK, `RAW(16) DEFAULT uuid()`.
- `FUZZY_MATCH(LEVENSHTEIN, a, b)` e `PHONIC_ENCODE(METAPHONE, s)` para deduplicação de cadastros (nomes, endereços).

## 4. JSON

### 4.1 Tipo JSON e JSON_BEHAVIOR

- Tipo nativo `JSON` (binário OSON) desde 21c; 23ai melhora construtores (`json {…}`), `JSON_TRANSFORM`, predicados em `JSON_VALUE`/`JSON_QUERY`.
- Parâmetro `JSON_BEHAVIOR` controla defaults de retorno (`ON ERROR`, `RETURNING`); leia antes de migrar JSON textual (`VARCHAR2/CLOB IS JSON`) para tipo `JSON` — há artigo/pre-check específico.
- **19c:** JSON em `VARCHAR2/CLOB IS JSON` + `APEX_JSON`/`JSON_TABLE`.

### 4.2 JSON-Relational Duality Views

```sql
create or replace json relational duality view dv_departamentos as
select json {'_id'          : d.id_depto,
             'nome'         : d.nome,
             'funcionarios' : [ select json {'id' : f.id_funcionario, 'nome' : f.nome, 'salario' : f.salario}
                                from   tb_funcionarios f with insert update delete
                                where  f.id_depto = d.id_depto ]}
from tb_departamentos d with insert update delete;
```

- Leitura e escrita (INSERT/UPDATE/DELETE via JSON) com `etag` para lock otimista.
- ORDS faz AutoREST de duality views → API JSON sem handler.
- Exige PK/FK íntegras; anotações `with insert update delete` definem o que cada tabela aceita.

### 4.3 JSON Collections, JSON Schema, precheck

- `CREATE JSON COLLECTION TABLE` (23ai) — coleção estilo MongoDB (ORDS MongoDB API).
- `JSON SCHEMA` em `CHECK` valida estrutura; `DBMS_JSON_SCHEMA.validate_report`.
- Precheck constraints: `ALTER TABLE … PRECHECK` expõe as regras em JSON Schema para validar no cliente antes do INSERT.

## 5. Tabela-resumo por versão

| Feature | Versão | 19c? |
|---|---|---|
| IF [NOT] EXISTS | 23ai | **19.28** |
| Annotations | 23ai | **19.28** |
| DBMS_DEVELOPER | 23ai | **19.28** |
| BOOLEAN, Domains, SELECT sem FROM, UPDATE/DELETE JOIN, RETURNING OLD/NEW, VALUES constructor, DEFAULT ON NULL UPDATE, lock-free reservations, duality views, JSON collections, schema privileges | 23ai | não |
| GROUP BY ALL, UUID(), INSERT BY NAME/SET | 23.9 | não |
| Smallfile shrink | 23.7 | não |
| QUALIFY, FILTER, calendar functions, Assertions, RESETTABLE, PDB priority | 26ai | não |
| Priority transactions | 23ai (doc cita 23c) | não |
