# Novidades PL/SQL, segurança e plataforma — Oracle Database 23ai/26ai

Complemento do reference de SQL: o que muda em PL/SQL, privilégios, conectividade e recursos de plataforma que impactam desenvolvimento. Exemplos em `assets/exemplos_plsql_26ai.sql`.

## Índice

- [1. PL/SQL](#1-plsql)
  - [1.1 RESETTABLE (26ai) — adeus ORA-04068](#11-resettable-26ai--adeus-ora-04068)
  - [1.2 Transpiler automático PL/SQL → SQL](#12-transpiler-automático-plsql--sql)
  - [1.3 Dynamic statistics para funções PL/SQL](#13-dynamic-statistics-para-funções-plsql)
  - [1.4 CASE com predicados e múltiplas escolhas](#14-case-com-predicados-e-múltiplas-escolhas)
  - [1.5 BOOLEAN em SQL dinâmico e RETURNING em coleções](#15-boolean-em-sql-dinâmico-e-returning-em-coleções)
  - [1.6 Multilingual Engine (MLE) — JavaScript no banco](#16-multilingual-engine-mle--javascript-no-banco)
- [2. Privilégios e segurança](#2-privilégios-e-segurança)
  - [2.1 Schema privileges](#21-schema-privileges)
  - [2.2 DB_DEVELOPER_ROLE](#22-db_developer_role)
  - [2.3 Usuários read-only de PDB](#23-usuários-read-only-de-pdb)
  - [2.4 SQL Firewall](#24-sql-firewall)
  - [2.5 TLS sem wallet no cliente (19.16 variante)](#25-tls-sem-wallet-no-cliente-1916-variante)
  - [2.6 Auditoria e Data Redaction](#26-auditoria-e-data-redaction)
- [3. Ferramentas para desenvolvedor](#3-ferramentas-para-desenvolvedor)
  - [3.1 DBMS_DEVELOPER (19.28)](#31-dbms_developer-1928)
  - [3.2 SQL*Plus/SQLcl ARGUMENT](#32-sqlplussqlcl-argument)
  - [3.3 DBMS_HCHECK](#33-dbms_hcheck)
- [4. Plataforma](#4-plataforma)
  - [4.1 AI Vector Search](#41-ai-vector-search)
  - [4.2 Multitenant: PDB priority (26ai), hybrid read-only, DRCP](#42-multitenant-pdb-priority-26ai-hybrid-read-only-drcp)
  - [4.3 Materialized views, particionamento, blockchain/immutable](#43-materialized-views-particionamento-blockchainimmutable)
  - [4.4 Flashback logs fora da FRA](#44-flashback-logs-fora-da-fra)

---

## 1. PL/SQL

### 1.1 RESETTABLE (26ai) — adeus ORA-04068

Package com estado (variáveis globais) recompilado → próxima chamada na sessão falha com `ORA-04068: existing state of packages has been discarded`. Com `RESETTABLE`, o Oracle reinicializa o estado silenciosamente em vez de lançar erro.

```sql
create or replace package pkg_config resettable as
  g_ultima_carga date;
  function obter_ultima_carga return date;
end pkg_config;
/
create or replace package body pkg_config resettable as
  ...
end pkg_config;
/
```

- Declare em **spec e body**.
- Impacto na suíte: deploy de packages em produção (GMUD) deixa de exigir reconexão do pool ORDS/APEX. Combine com EBR para zero downtime real (`oracle-plsql-ptbr`).
- **19c:** `DBMS_SESSION.reset_package` / `modify_package_state`, reciclagem do pool ou packages sem estado (padrão Trivadis já recomenda `g_` mínimo).

### 1.2 Transpiler automático PL/SQL → SQL

O optimizer converte chamadas de funções PL/SQL simples em expressões SQL, eliminando o *context switch*.

```sql
alter session set sql_transpiler = 'ON';   -- default OFF
select id, valor1, valor2 from tb_valores where fnc_somar(valor1, valor2) = 300;
```

- Elegíveis: funções com um único `RETURN` de expressão, sem SQL interno, loops, exceções, coleções ou side effects. Funções de package simples já são transpiladas.
- Verifique no plano (`DBMS_XPLAN.display_cursor`): o filtro aparece como expressão, não como chamada.
- Não substitui os princípios "SQL puro antes de PL/SQL" e "funções `DETERMINISTIC`/`RESULT_CACHE`" — é um bônus para o que sobrou.

### 1.3 Dynamic statistics para funções PL/SQL

Preferência `DYNAMIC_STATS` em `DBMS_STATS.get/set_plsql_prefs` (níveis por função/package) melhora a estimativa de cardinalidade de queries que chamam funções (inclusive pipelined/PTF).

```sql
select dbms_stats.get_plsql_prefs('dynamic_stats') from dual;   -- CHOOSE
exec dbms_stats.set_plsql_prefs(pname => 'dynamic_stats', pvalue => 'ON', ownname => user, function_name => 'FNC_LISTAR');
```

### 1.4 CASE com predicados e múltiplas escolhas

```sql
case l_pct
  when = 40      then l_faixa := 'OTIMO';
  when <= 70     then l_faixa := 'SEGURO';
  when 80, 90    then l_faixa := 'ALERTA';
  when > 90      then l_faixa := 'CRITICO';
end case;
```

- Alinha o `CASE` simples do PL/SQL ao SQL:2003; vale para statement e expression.

### 1.5 BOOLEAN em SQL dinâmico e RETURNING em coleções

- `EXECUTE IMMEDIATE … USING l_flag` com `BOOLEAN` funciona (antes exigia `sys.diutil.bool_to_int`).
- `RETURNING OLD/NEW … BULK COLLECT INTO` retorna vetores antigo/novo em um único DML — ver SQL 2.2.
- `SELECT … INTO` sem `FROM` funciona em PL/SQL.

### 1.6 Multilingual Engine (MLE) — JavaScript no banco

- Módulos persistentes (`CREATE MLE MODULE … LANGUAGE JAVASCRIPT`), *environments* e *call specifications* que expõem funções JS como PL/SQL. Privilégios: `CREATE MLE`, `EXECUTE ON JAVASCRIPT`.
- ORDS 24.1.1+: handler `mle/javascript`. APEX 24.1+: MLE em processes.
- Uso legítimo: validações/transformações já existentes em JS (ex.: regras compartilhadas com front-end). Não migre regra de negócio PL/SQL para JS por moda — a convenção da suíte continua PL/SQL + Trivadis.

## 2. Privilégios e segurança

### 2.1 Schema privileges

```sql
grant select any table on schema owner_app to usr_leitura;
grant select any sequence, execute any procedure on schema owner_app to rl_app;
revoke select any table on schema owner_app from usr_leitura;
```

- Cobre objetos **futuros** do schema — substitui scripts de grant pós-deploy.
- Dicionário: `DBA_SCHEMA_PRIVS`, `USER_SCHEMA_PRIVS`, `ROLE_SCHEMA_PRIVS`.
- Não se aplica a `SYS`, `SYSTEM` e schemas Oracle-maintained.
- Encaixa no princípio "owner faz DDL, app user faz DML" do `oracle-core-ptbr` — o app user recebe `INSERT/UPDATE/DELETE/SELECT ANY TABLE ON SCHEMA owner`.

### 2.2 DB_DEVELOPER_ROLE

Role pronta com o conjunto que a Oracle considera necessário para desenvolvedor: `CREATE SESSION`, `CREATE TABLE/VIEW/PROCEDURE/SEQUENCE/TRIGGER/TYPE/SYNONYM/MLE/…`, `EXECUTE ON JAVASCRIPT`, `SELECT ON` views de dicionário úteis (`V$SESSION`, `V$SQL`…) e `SODA_APP`.

- Substitui `CONNECT` + `RESOURCE` (este último inclui `CREATE PROPERTY GRAPH`, `CREATE ANALYTIC VIEW`… em 23ai).
- Ainda **não** dá quota: `ALTER USER x QUOTA UNLIMITED ON users` continua necessário.

### 2.3 Usuários read-only de PDB

```sql
alter user usr_relatorio read only;
-- sessão: ORA-28194: Can perform read operations only (DML, FOR UPDATE, DDL falham)
```

- `DBA_USERS.READ_ONLY`. Ideal para usuários de BI/ORDS de consulta sem depender de grants negativos.

### 2.4 SQL Firewall

Allow-list de SQL e contexto de sessão (IP, programa, usuário do SO) por usuário de banco: fase de **captura** (`DBMS_SQL_FIREWALL.create_capture`) → gera allow-list → **enforce** (`enable_allow_list`, modo `BLOCK` ou só `LOG`).

- Caso de uso: usuário do pool ORDS/APEX só pode executar o SQL conhecido; SQL injection que gere statement novo é bloqueado.
- Exige `SQL_FIREWALL_ADMIN`; logs em `DBA_SQL_FIREWALL_VIOLATIONS`.
- Cuidado com APEX: SQL gerado dinamicamente (IR/IG) muda com filtros do usuário — capture com uso real por semanas antes de `BLOCK`.

### 2.5 TLS sem wallet no cliente (19.16 variante)

- 23ai: cliente conecta com TLS usando o certificate store do SO, sem `WALLET_LOCATION` no `sqlnet.ora` (autenticação one-way).
- Backport parcial 19.16: `UTL_HTTP.set_wallet('system:')` usa o store do SO para chamadas HTTPS a partir do banco — resolve `ORA-29024` sem manter wallet (`oracle-ords-ptbr` — Network ACL continua obrigatória).

### 2.6 Auditoria e Data Redaction

- Unified Audit: novas ações auditáveis (23ai), `DBMS_AUDIT_MGMT` com limpeza por PDB; trilha tradicional (`AUDIT_TRAIL`) está **desuportada** — planeje a migração para Unified Audit antes do upgrade.
- `DBMS_REDACT` (23.6): redaction em colunas `JSON`, novas funções de máscara.

## 3. Ferramentas para desenvolvedor

### 3.1 DBMS_DEVELOPER (19.28)

```sql
select dbms_developer.get_metadata(name => 'TB_CLIENTES', object_type => 'TABLE', detail => 'TYPICAL') from dual;
```

- Metadata do objeto em **JSON** (colunas, constraints, índices, annotations). Mais leve que `DBMS_METADATA.get_ddl` para ferramentas — ex.: gerar página APEX ou handler ORDS a partir da tabela.
- Backportado para 19.28.

### 3.2 SQL*Plus/SQLcl ARGUMENT

`ARGUMENT 1 PROMPT 'Schema:' DEFAULT 'APP'` (SQLcl 22.4+ / SQL*Plus 23ai) — parâmetros nomeados com default em scripts GMUD; elimina `&1` sem validação.

### 3.3 DBMS_HCHECK

Health check do dicionário (`DBMS_HCHECK.full`, `critical`) — rode antes de upgrade e após patches; substitui o `hcheck.sql` do MOS.

## 4. Plataforma

### 4.1 AI Vector Search

- Tipo `VECTOR`, funções `VECTOR_EMBEDDING`, `VECTOR_DISTANCE`, índices `INMEMORY NEIGHBOR GRAPH` (HNSW) / `NEIGHBOR PARTITIONS` (IVF); modelos ONNX carregados via `DBMS_VECTOR.load_onnx_model`.
- Base do RAG declarativo do APEX 24.2+ e das VecDB REST APIs do ORDS 26.1 (exige 23.26.1+).
- Licenciamento: incluído no banco; índices HNSW usam In-Memory (área `VECTOR_MEMORY_SIZE`).
- **`VECTOR_MEMORY_SIZE` — restart só para ligar.** Medido no 26ai Free 23.26.3: no CDB com o pool em 0 no startup, aumentar exige `SCOPE=SPFILE` + restart (sem restart → ORA-51950); com o pool já alocado no startup, cresce sem restart e não reduz abaixo do valor inicial (ORA-51953); no PDB é cota dinâmica (`SCOPE=BOTH`), limitada ao pool do CDB (ORA-51955). Em produção, defina o pool já na janela do upgrade.
- Fora do escopo da suíte gerar pipelines de embedding; cobrir só integração (coluna VECTOR + busca por similaridade em APEX/ORDS).

### 4.2 Multitenant: PDB priority (26ai), hybrid read-only, DRCP

- **PDB priority (26ai):** `ALTER PLUGGABLE DATABASE x PRIORITY n` ordena abertura, recuperação e alocação de recursos entre PDBs — prioridade para o PDB de produção sobre o de homologação no mesmo CDB.
- **Hybrid read-only:** PDB read-only para usuários comuns e read-write para usuários locais privilegiados (manutenção sem abrir para a aplicação).
- **DRCP (23ai):** pool multi-PDB, pool por PDB, autenticação por token — relevante para ORDS/APEX em ambientes com muitas conexões curtas.

### 4.3 Materialized views, particionamento, blockchain/immutable

- MV: refresh concorrente, suporte a joins ANSI, Logical Partition Change Tracking (LPCT) para refresh incremental por partição lógica.
- Particionamento: metadata aprimorada (`DBA_TAB_PARTITIONS` com colunas de estado), hybrid partitioned tables com mais operações online.
- Blockchain/immutable tables: novas opções de retenção e assinatura; imutáveis exigem `NO DROP UNTIL n DAYS IDLE`.

### 4.4 Flashback logs fora da FRA

- 23ai/26ai: `DB_FLASHBACK_LOG_DEST` separa os flashback logs da Fast Recovery Area — reduz o risco de a FRA encher e derrubar o banco por causa de Flashback Database usado em pipelines de teste (`oracle-devops-ptbr`).
