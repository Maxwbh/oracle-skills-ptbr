# Performance Tuning — Análise e Otimização

Performance tuning para desenvolvedor Oracle. Foco no que dá retorno mais rápido: bind variables, indexes, plan análise, e bulk processing. Não cobre AWR/ASH (escopo DBA) nem otimização de hardware.

## Índice

- [Princípio fundamental: medir antes, depois](#princípio-fundamental-medir-antes-depois)
- [Bind Variables — a otimização #1](#bind-variables-a-otimização-1)
- [EXPLAIN PLAN](#explain-plan)
- [Indexes](#indexes)
- [Hints — uso parcimonioso](#hints-uso-parcimonioso)
- [Paralelismo (Parallel Execution)](#paralelismo-parallel-execution)
- [Cursor sharing e bind peeking](#cursor-sharing-e-bind-peeking)
- [Bulk Processing como otimização](#bulk-processing-como-otimização)
- [Identificar queries problemáticas](#identificar-queries-problemáticas)
- [Statistics — manter atualizadas](#statistics-manter-atualizadas)
- [Anti-patterns Performance](#anti-patterns-performance)
- [Checklist rápido para query lenta](#checklist-rápido-para-query-lenta)
- [Linkagem](#linkagem)

## Princípio fundamental: medir antes, depois

Não otimize por intuição. Sempre:
1. **Antes:** mede tempo de execução (SET TIMING ON, SQL trace)
2. **Hipótese:** identifica o gargalo via plan, V$SQL, V$SESSION_WAIT
3. **Depois:** aplica mudança, mede de novo
4. **Compara:** ganho real ou só placebo?

Sem medição, "essa query agora tá mais rápida" é alucinação.

## Bind Variables — a otimização #1

### Por que bind variables importam

Cada query nova passa por:
1. **Parse:** valida sintaxe, semântica, gera AST
2. **Bind:** substitui variáveis
3. **Execute:** roda
4. **Fetch:** retorna linhas

**Hard parse** (passo 1+2) é caro. Cache compartilhado (`shared_pool`) cacheia plan já parseado para reuse.

Sem bind:
```sql
-- Cada execução é query diferente para Oracle
SELECT * FROM emp WHERE id = 100;  -- hard parse
SELECT * FROM emp WHERE id = 200;  -- hard parse
SELECT * FROM emp WHERE id = 300;  -- hard parse
```

Com bind:
```sql
-- Uma query, plan reusado
SELECT * FROM emp WHERE id = :id;  -- 1 hard parse
-- Execuções subsequentes só re-bindam
```

### Verificar uso

```sql
-- Top SQL por hard parses (queries sem bind)
SELECT sql_text, parse_calls, executions,
       parse_calls / NULLIF(executions, 0) * 100 AS parse_pct
  FROM v$sqlarea
 WHERE parse_calls > 1
   AND executions > 0
 ORDER BY parse_pct DESC
 FETCH FIRST 20 ROWS ONLY;
```

### Sintomas de falta de bind

```sql
-- Queries quase idênticas (literais diferentes) — sintoma claro
SELECT sql_id, sql_text FROM v$sqlarea
 WHERE sql_text LIKE 'SELECT % FROM emp WHERE id = %';
```

Se vê 50 entradas iguais com IDs diferentes literais → falta bind.

### Em PL/SQL: nativamente bindado

```sql
-- Em PL/SQL, isto USA bind automaticamente
SELECT * INTO l_rec FROM emp WHERE id = p_id;

-- E EXECUTE IMMEDIATE também, com USING
EXECUTE IMMEDIATE 'SELECT * FROM emp WHERE id = :1' INTO l_rec USING p_id;

-- MAS concatenação NÃO usa bind
EXECUTE IMMEDIATE 'SELECT * FROM emp WHERE id = ' || p_id;  -- ❌
```

### Em ORDS/APEX

Bind é automático com:
- `:P1_NOME` (APEX item references)
- `:id` (ORDS path parameters)
- Bind variables em PL/SQL

## EXPLAIN PLAN

### Capturar plan

```sql
-- Forma 1: gerar plan antes de executar
EXPLAIN PLAN FOR
SELECT c.nome, COUNT(i.id)
  FROM clientes c
  LEFT JOIN faturas i ON c.id = i.id_cliente
 WHERE c.status = 'A'
 GROUP BY c.nome;

SELECT * FROM TABLE(DBMS_XPLAN.display);
```

### Plan da query mais recente

```sql
SELECT * FROM TABLE(DBMS_XPLAN.display_cursor);
```

### Plan de uma query específica em cache

```sql
-- Encontra SQL_ID
SELECT sql_id, sql_text FROM v$sqlarea
 WHERE sql_text LIKE '%trecho_distinto%';

-- Mostra plan
SELECT * FROM TABLE(DBMS_XPLAN.display_cursor(sql_id => 'abcd1234efgh5'));
```

### Lendo o plan

Saída típica:
```
| Id | Operation              | Name      | Rows | Bytes | Cost | Time     |
|  0 | SELECT STATEMENT       |           |  100 | 5000  |  120 | 00:00:01 |
|  1 |  HASH GROUP BY         |           |  100 | 5000  |  120 | 00:00:01 |
|* 2 |   HASH JOIN OUTER      |           | 1000 | 50000 |  118 | 00:00:01 |
|* 3 |    TABLE ACCESS FULL   | CUSTOMERS |  500 | 15000 |   45 | 00:00:01 |
|  4 |    TABLE ACCESS FULL   | INVOICES  | 5000 | 200000|   72 | 00:00:01 |
```

**Ler de dentro pra fora, de baixo pra cima:**
1. Linha 4: full scan em INVOICES
2. Linha 3: full scan em CUSTOMERS, filtrando status='A'
3. Linha 2: HASH JOIN das duas tabelas
4. Linha 1: agrupa
5. Linha 0: retorna

**Sinais de alerta:**
- `TABLE ACCESS FULL` em tabelas grandes (>10k linhas) → falta index?
- `NESTED LOOPS` com tabelas grandes → cardinalidade subestimada?
- Cost muito desbalanceado entre etapas → algum step domina

### Tipos de acesso a índice — a diferença que importa

Quando a query usa um índice, o plan mostra um destes tipos. **Não são equivalentes** — cada um indica eficiência diferente:

| Tipo | Custo típico | Significado |
|---|---|---|
| `INDEX UNIQUE SCAN` | 1-3 LIO | Acesso por valor único (PK ou unique constraint). Best case absoluto. |
| `INDEX RANGE SCAN` | 1-N LIO | Range de valores; pode retornar 1 linha ou milhares |
| `INDEX FULL SCAN` | mais que TABLE FULL geralmente | Lê o índice inteiro (geralmente ruim) |
| `INDEX FAST FULL SCAN` | similar a TABLE FULL SCAN | Lê o índice inteiro com I/O multibloco, sem ordenação (pode ser paralelizado). Útil quando todas as colunas da query estão no índice |
| `INDEX SKIP SCAN` | variável | "Pula" prefixos do composite index quando primeira coluna não é filtrada |

#### `INDEX UNIQUE SCAN` — query por chave única

```
| 1 | TABLE ACCESS BY INDEX ROWID | CUSTOMERS    |   1 |  100 |   2 |
| 2 |  INDEX UNIQUE SCAN          | PK_CUSTOMERS |   1 |      |   1 |
```

A query `WHERE id_cliente = 100` em PK retorna garantidamente 1 linha. Optimizer faz lookup direto: 2-3 LIO.

#### `INDEX RANGE SCAN` — query por chave não-única ou range

```
| 1 | TABLE ACCESS BY INDEX ROWID BATCHED | INVOICES         | 200 | 10000 |  15 |
| 2 |  INDEX RANGE SCAN                   | IDX_INV_CUST_DT  | 200 |       |   3 |
```

`WHERE id_cliente = 100 AND data_emissao > SYSDATE - 30`: pode retornar 0 linhas, 1, ou 1000.

**Diferença prática:**
- `RANGE SCAN` retornando 1 linha: ótimo
- `RANGE SCAN` retornando 100k linhas: pode ser pior que `TABLE ACCESS FULL`
  - Cada linha gerada pelo index → 1 LIO no índice + 1 LIO na tabela (via ROWID)
  - Se 30%+ da tabela é retornada, full scan é mais eficiente

#### `INDEX FULL SCAN` — geralmente é problema

```
| 1 | INDEX FULL SCAN | IDX_INVOICES_DATE | 100k | ... | 250 |
```

Aparece quando:
- `ORDER BY` em coluna indexada **sem WHERE filtrante**
- `MIN/MAX` em coluna indexada (otimização legítima — caso raro de FULL SCAN bom)
- Optimizer estimou que ler o índice é mais barato que tabela inteira (raro)

#### `INDEX SKIP SCAN` — caso especial em composite index

Composite index em `(status, criado_em)`. Query `WHERE criado_em > SYSDATE - 7` (sem filtrar `status`).

```
| 2 |  INDEX SKIP SCAN | IDX_INV_STATUS_DT | ... |
```

Optimizer "pula" cada valor distinto de `status` e faz range scan dentro de cada. Funciona bem se `status` tem **poucos** valores distintos (3-10). Com 10000 valores distintos, é mais lento que `TABLE ACCESS FULL`.

### O que checar em revisão de plan

1. **Operação principal usa índice?** Se `TABLE ACCESS FULL` em tabela grande, falta index.
2. **Tipo de scan no índice é apropriado?**
   - PK/unique → `UNIQUE SCAN`
   - Range com seletividade alta → `RANGE SCAN` retornando poucas linhas
   - `FULL SCAN` em índice raramente é desejado
3. **Cardinalidade estimada bate com real?**
   - `Rows` no plan vs realidade (use `DBMS_XPLAN.display_cursor` com `format => 'ALLSTATS LAST'` para ver real)
   - Diferença >10x indica stats ruins
4. **Joins usam o método certo?**
   - Tabelas pequenas + índice no join key → `NESTED LOOPS`
   - Tabelas grandes sem filtro seletivo → `HASH JOIN`
   - Ambas ordenadas → `MERGE JOIN`

### Verificando estatísticas reais (vs estimativas do optimizer)

```sql
-- Roda a query (ou já rodou recentemente)
SELECT /*+ GATHER_PLAN_STATISTICS */ ... FROM ...;

-- Mostra plan com runtime stats
SELECT * FROM TABLE(DBMS_XPLAN.display_cursor(
  format => 'ALLSTATS LAST'
));
```

Output mostra colunas adicionais:
- `E-Rows`: estimativa do optimizer
- `A-Rows`: realidade
- `A-Time`: tempo real gasto
- `Buffers`: LIOs reais

Se `E-Rows` e `A-Rows` divergem muito, optimizer escolheu plan errado. Atualize stats com `DBMS_STATS.gather_table_stats`.

## Indexes

### Quando criar index

| Cenário | Ajuda? |
|---|---|
| WHERE coluna = valor (alta seletividade) | Sim |
| WHERE coluna IN (lista) | Sim, se seletivo |
| WHERE LIKE 'inicio%' (pattern com início fixo) | Sim |
| WHERE LIKE '%meio%' (wildcard prefix) | Não ajuda B-tree |
| ORDER BY coluna | Sim, evita sort |
| JOIN ON coluna = outra | Sim, na coluna lookup |
| WHERE função(coluna) = valor | Não — precisa **function-based index** |

### Tipos de index

```sql
-- B-tree (default) — alta seletividade, OLTP
CREATE INDEX idx_clientes_status ON clientes(status);

-- Composite — múltiplas colunas em sequência (ordem importa, ver abaixo)
CREATE INDEX idx_faturas_cli_data ON faturas(id_cliente, data_emissao);

-- Function-based — quando WHERE usa função (predicado e índice com a MESMA função)
CREATE INDEX idx_func_upper_nome ON funcionarios(UPPER(nome));
SELECT * FROM funcionarios WHERE UPPER(nome) = 'JOÃO SILVA';  -- agora usa o índice

-- Bitmap — baixa cardinalidade, em DATA WAREHOUSE (NÃO em OLTP — ver alerta)
CREATE BITMAP INDEX idx_func_sexo ON funcionarios(sexo);

-- Unique — força unicidade + agiliza lookup (INDEX UNIQUE SCAN)
CREATE UNIQUE INDEX uk_clientes_cpf ON clientes(cpf);

-- Reverse Key — inverte os bytes da chave para espalhar inserts sequenciais
-- (evita "hot block"/contenção no lado direito do índice quando a PK vem de
--  sequence em ambiente de alta concorrência). Custo: range scan deixa de
--  funcionar (só igualdade).
CREATE INDEX idx_fat_id_rev ON faturas(id) REVERSE;

-- Invisible — mantido por DML, mas IGNORADO pelo optimizer por padrão.
-- Use para testar a remoção de um índice sem droppar, ou introduzir um índice
-- novo sem afetar planos até validar.
CREATE INDEX idx_fat_teste ON faturas(total) INVISIBLE;
ALTER INDEX idx_fat_teste VISIBLE;     -- promove a visível quando validado
ALTER INDEX idx_fat_teste INVISIBLE;   -- volta a esconder
-- Para o optimizer enxergar invisíveis só nesta sessão (teste):
ALTER SESSION SET optimizer_use_invisible_indexes = TRUE;
```

> **Bitmap — por que NÃO em OLTP:** numa entrada de bitmap, uma única chave
> cobre um range de rowids. Quando um DML altera a coluna indexada, o Oracle
> trava **todas as linhas do fragmento de bitmap** afetado (não a linha única),
> gerando contenção `enq: TX` e até deadlocks sob concorrência. Bitmap é para
> data warehouse (carga em lote, leitura intensa), não para tabelas
> transacionais. Disponível só em Enterprise Edition.

> **"Covering index" não é um tipo no Oracle.** O termo (vindo do SQL Server)
> descreve a situação em que **todas as colunas da query estão no índice**, então
> o optimizer não precisa ler a tabela. No Oracle isso é apenas um índice
> (composite) cujo plano resultante NÃO tem `TABLE ACCESS BY INDEX ROWID` —
> aparece como `INDEX RANGE SCAN`/`INDEX FAST FULL SCAN` puro. É uma técnica,
> não um `CREATE ... <tipo>`.

> **Invisible × Unusable** (não confundir): *invisible* é mantido por DML e
> ignorado pelo optimizer (a menos do parâmetro acima) — reversível e barato
> para testes. *Unusable* não é mantido por DML e não tem segmento — usado para
> acelerar cargas em lote (depois `ALTER INDEX ... REBUILD`).

### Composite index — ordem importa

```sql
CREATE INDEX idx_inv_cust_date ON faturas(id_cliente, data_emissao);

-- USA o index
SELECT * FROM faturas WHERE id_cliente = 100;
SELECT * FROM faturas WHERE id_cliente = 100 AND data_emissao > SYSDATE - 30;

-- NÃO USA o index (não tem prefixo id_cliente)
SELECT * FROM faturas WHERE data_emissao > SYSDATE - 30;
```

**Regra:** coluna mais seletiva e mais usada em WHERE primeiro.

### Verificar uso de indexes

```sql
-- Indexes não utilizados (precisa MONITORING USAGE primeiro)
ALTER INDEX idx_clientes_status MONITORING USAGE;

-- Depois de período de uso (USER_OBJECT_USAGE substituiu V$OBJECT_USAGE,
-- deprecada desde 12.1; em 19c use USER_OBJECT_USAGE / DBA_OBJECT_USAGE)
SELECT index_name, used FROM user_object_usage
 WHERE table_name = 'CLIENTES';

-- Para parar
ALTER INDEX idx_clientes_status NOMONITORING USAGE;
```

### Quando index pode atrapalhar

- DML pesado em tabela com muitos indexes (cada INSERT/UPDATE atualiza todos)
- Index muito grande comparado à tabela (rare scan + table access)
- Estatísticas obsoletas levando optimizer a escolher mal

## Hints — uso parcimonioso

Hints forçam optimizer a escolher caminho específico. **Quase sempre é melhor melhorar stats e indexes do que usar hints.** Mas há casos onde compensa.

### Sintaxe

```sql
SELECT /*+ INDEX(c idx_clientes_status) */
       c.id, c.nome
  FROM clientes c
 WHERE c.status = 'A';
```

### Hints úteis

| Hint | Uso |
|---|---|
| `INDEX(tabela index_name)` | Força uso de index específico |
| `NO_INDEX(tabela index_name)` | Proíbe index específico |
| `FULL(tabela)` | Força full scan |
| `USE_NL(tab1 tab2)` | Força nested loops |
| `USE_HASH(tab1 tab2)` | Força hash join |
| `LEADING(tabela)` | Define primeira tabela no join order |
| `PARALLEL(N)` | Paralelismo no nível do statement (DOP N) — autoriza PX em todos os acessos elegíveis |
| `PARALLEL(tabela, N)` | Paralelismo no nível do objeto (sobrepõe o DOP da tabela) |
| `NO_PARALLEL(tabela)` | Desabilita paralelismo para a tabela/operação |
| `RESULT_CACHE` | Cacheia resultado da query |
| `MATERIALIZE` em WITH | Força materialização de subquery |

### Quando hints fazem sentido

- Stats desatualizadas e impossível atualizar agora
- Optimizer consistentemente erra em caso conhecido
- Forçar plan estável em SQL crítico (use SQL Plan Baselines em vez quando possível)

### Quando NÃO usar hints

- "Vi um cara na internet usar" — sem entender o porquê
- Para "garantir" comportamento — frágil quando dados mudam
- Em vez de criar index — quase sempre o index resolveria melhor

## Paralelismo (Parallel Execution)

Paralelismo divide o trabalho de uma operação entre vários processos (PX
servers). Ajuda em **operações grandes** (full scans de tabelas grandes, joins
volumosos, criação de índice, ETL). **Não ajuda — e atrapalha — em OLTP de
linhas isoladas e tabelas pequenas.**

### Quando paralelismo ajuda x atrapalha

| Cenário | Paralelismo |
|---|---|
| Full scan de tabela grande (milhões de linhas) | Ajuda |
| Join volumoso (HASH JOIN sobre tabelas grandes) | Ajuda |
| CREATE INDEX / ALTER INDEX REBUILD em tabela grande | Ajuda |
| CTAS / INSERT ... SELECT em massa (ETL) | Ajuda (com parallel DML) |
| Lookup por PK / poucas linhas (OLTP) | Atrapalha (overhead de coordenacao) |
| Tabela pequena (ate milhares de linhas, dezenas de blocos) | Nunca habilitar |
| Sistema ja saturado de CPU | Atrapalha (cada query consome mais cores) |

Regra pratica: paralelismo troca **mais CPU/processos** por **menos tempo de
parede**. So vale quando ha trabalho grande a dividir e recursos ociosos.

### Sintaxe do hint - statement-level vs object-level (11.2+)

A partir do 11.2 ha duas formas (nao confundir):

```sql
-- STATEMENT-LEVEL: DOP para todo o statement (forma recomendada hoje).
-- Sem objeto no hint -> escopo e o statement inteiro.
SELECT /*+ PARALLEL(4) */ c.id, c.nome
  FROM clientes c
  JOIN faturas f ON f.id_cliente = c.id;

-- DOP omitido -> Oracle calcula (Auto DOP); minimo e 2.
SELECT /*+ PARALLEL */ ... ;

-- OBJECT-LEVEL: DOP so para a tabela/alias indicado.
SELECT /*+ PARALLEL(f, 4) */ ... FROM faturas f;
```

Detalhes que importam:
- Hints **statement-level tem precedencia** sobre object-level.
- Um hint `PARALLEL` no nivel de statement **habilita Auto DOP**
  independentemente de `PARALLEL_DEGREE_POLICY`.
- `NO_PARALLEL(tabela)` desliga paralelismo para um objeto.

### Parallel DML exige habilitacao explicita (pegadinha classica)

Diferente de query e DDL (paralelos por padrao quando ha hint/atributo), **o
parallel DML esta DESABILITADO por padrao na sessao**. Sem habilitar, um
`INSERT`/`UPDATE`/`DELETE`/`MERGE` **nao roda em paralelo nem com o hint
PARALLEL** - apenas a parte de SELECT/scan pode paralelizar.

```sql
-- Forma classica (sessao): habilite ANTES, fora de transacao aberta
ALTER SESSION ENABLE PARALLEL DML;

INSERT /*+ PARALLEL(4) */ INTO arquivo_faturas
SELECT /*+ PARALLEL(4) */ * FROM faturas WHERE data_emissao < ADD_MONTHS(SYSDATE, -12);
COMMIT;

-- Forma por statement (12.1+): hint ENABLE_PARALLEL_DML, sem ALTER SESSION
INSERT /*+ ENABLE_PARALLEL_DML PARALLEL(4) */ INTO arquivo_faturas
SELECT * FROM faturas WHERE data_emissao < ADD_MONTHS(SYSDATE, -12);
COMMIT;
```

Cuidados:
- **ORA-12841:** nao da para `ALTER SESSION ENABLE/DISABLE PARALLEL DML` dentro
  de uma transacao aberta - faca COMMIT/ROLLBACK antes.
- Apos parallel DML em uma tabela, a sessao **nao pode ler a mesma tabela** sem
  antes commitar (restricao transacional do PDML).
- Parallel DML/DDL **nao e suportado com object types** - executa serial.

### Conferir paralelismo

```sql
-- DOP solicitado vs efetivo das sessoes PX ativas
SELECT req_degree AS dop_solicitado, degree AS dop_efetivo
  FROM v$px_session
 WHERE req_degree IS NOT NULL;

-- Atributo PARALLEL definido em tabelas (DEGREE 1 = serial)
SELECT table_name, degree
  FROM user_tables
 WHERE TRIM(degree) NOT IN ('1');

-- No plano: procure PX COORDINATOR, PX SEND, PX BLOCK ITERATOR.
-- Em DML, se a operacao LOAD aparece ACIMA do PX COORDINATOR, o parallel DML
-- NAO foi habilitado; o bloco "Note" do DBMS_XPLAN tambem sinaliza isso.
```

### Anti-patterns de paralelismo

- Hint `PARALLEL` em query OLTP de poucas linhas -> overhead de coordenacao > ganho.
- Definir `ALTER TABLE ... PARALLEL N` permanente em tabela OLTP -> todo full scan
  vira paralelo, drena PX servers do sistema. Prefira o hint pontual.
- Esperar parallel DML sem `ENABLE PARALLEL DML` -> roda serial silenciosamente.
- DOP altissimo "para ir mais rapido" -> satura CPU; o ganho satura e depois piora.

## Cursor sharing e bind peeking

### Cursor sharing modes

```sql
-- Verifica modo
SHOW PARAMETER cursor_sharing;

-- EXACT (default 19c+): hard parse a cada literal
-- FORCE: substitui literais por bind automaticamente
-- SIMILAR: deprecated
```

`EXACT` é correto, força disciplina de bind no código.

### Bind peeking — efeito de "primeira execução"

Optimizer "espia" valor da bind na primeira execução para escolher plan. Se primeira execução tem valor incomum, plan pode ficar ruim para usos típicos.

**Sintoma:** query rápida normalmente, lenta em horários específicos.

**Mitigação:**
- Adaptive Cursor Sharing (default 11g+): Oracle gera múltiplos plans para diferentes "perfis" de bind
- SQL Plan Baselines: força plan específico

## Bulk Processing como otimização

Loops linha-a-linha em PL/SQL são MUITO mais lentos que bulk. Diferença de 10x-100x em volumes médios.

### Antes (linha-a-linha)

```sql
FOR r IN (SELECT id, valor FROM faturas) LOOP
  INSERT INTO arquivo_faturas VALUES (r.id, r.valor, SYSDATE);
END LOOP;
```

### Depois (bulk)

```sql
DECLARE
  TYPE t_faturas IS TABLE OF faturas%ROWTYPE;
  l_faturas t_faturas;
BEGIN
  SELECT * BULK COLLECT INTO l_faturas FROM faturas;

  FORALL i IN l_faturas.FIRST..l_faturas.LAST
    INSERT INTO arquivo_faturas(id, valor, arquivado_em)
    VALUES (l_faturas(i).id, l_faturas(i).valor, SYSDATE);

  COMMIT;
END;
```

### Para volumes muito grandes — chunking

```sql
DECLARE
  CURSOR co_faturas IS SELECT * FROM faturas;
  TYPE t_faturas IS TABLE OF faturas%ROWTYPE;
  l_faturas t_faturas;
  lc_limit CONSTANT PLS_INTEGER := 10000;
BEGIN
  OPEN co_faturas;
  LOOP
    FETCH co_faturas BULK COLLECT INTO l_faturas LIMIT lc_limit;
    EXIT WHEN l_faturas.COUNT = 0;

    FORALL i IN l_faturas.FIRST..l_faturas.LAST
      INSERT INTO arquivo_faturas(id, valor, arquivado_em)
      VALUES (l_faturas(i).id, l_faturas(i).valor, SYSDATE);

    COMMIT;  -- commit por chunk
  END LOOP;
  CLOSE co_faturas;
END;
```

## Identificar queries problemáticas

### Top SQL por tempo total

```sql
SELECT sql_id, sql_text, executions,
       ROUND(elapsed_time/1000000, 2)  AS elapsed_sec,
       ROUND(elapsed_time/NULLIF(executions,0)/1000, 2) AS avg_ms,
       buffer_gets, disk_reads
  FROM v$sqlarea
 WHERE executions > 0
 ORDER BY elapsed_time DESC
 FETCH FIRST 20 ROWS ONLY;
```

### Top SQL por buffer gets (uso de memória)

```sql
SELECT sql_id, sql_text, executions,
       buffer_gets,
       ROUND(buffer_gets/NULLIF(executions,0), 0) AS avg_buffer_gets
  FROM v$sqlarea
 WHERE executions > 0
 ORDER BY buffer_gets DESC
 FETCH FIRST 20 ROWS ONLY;
```

### Wait events em sessão problemática

```sql
SELECT s.sid, s.serial#, s.username, s.event, s.wait_class,
       s.seconds_in_wait, s.sql_id
  FROM v$session s
 WHERE s.username IS NOT NULL
   AND s.status = 'ACTIVE'
   AND s.event NOT LIKE 'SQL*Net%idle%'
 ORDER BY s.seconds_in_wait DESC;
```

## Statistics — manter atualizadas

Optimizer **depende** de stats precisas. Sem stats:
- Estima cardinalidade errada
- Escolhe plan errado
- Performance imprevisível

```sql
-- Última coleta de stats
SELECT table_name, last_analyzed, num_rows, blocks
  FROM user_tables
 ORDER BY last_analyzed NULLS FIRST;

-- Coletar para tabela
EXEC DBMS_STATS.gather_table_stats(USER, 'FATURAS', cascade => TRUE);

-- Schema inteiro
EXEC DBMS_STATS.gather_schema_stats(USER, cascade => TRUE);
```

**Frequência:** geralmente Oracle Auto Task roda diariamente. Mas após cargas pesadas, force coleta manual.

> Para aprofundamento — histogramas (frequency/top-frequency/height-balanced/hybrid),
> estatísticas estendidas (column groups), preferences, SQL Plan Directives,
> lock/pending/restore/retention/report e o Optimizer Statistics Advisor — veja
> `references/optimizer-statistics-ptbr.md` e o asset
> `assets/optimizer_statistics_examples.sql`.

## Anti-patterns Performance

| Anti-pattern | Sintoma | Correção |
|---|---|---|
| Concatenação de SQL com literais | Hard parses, shared_pool fragmentado | Bind variables |
| Loop linha-a-linha em volume | PL/SQL muito lento | BULK COLLECT + FORALL |
| `SELECT *` em vez de colunas | I/O extra, network extra | Selecione colunas necessárias |
| `COUNT(*)` para checar existência | Lê tudo | `WHERE EXISTS (SELECT 1 ...)` |
| Função em coluna do WHERE | Não usa index | Function-based index |
| OR sem indexes apropriados | Full scan | UNION ALL com index em cada |
| NOT IN com subquery | Estranhamento de NULL | NOT EXISTS |
| Subquery correlacionada | N execuções | JOIN ou WITH |
| Cursor implícito quando 0 ou 1 linha | Overhead de cursor | Single-row SELECT INTO |
| Stats desatualizadas | Plans subitamente ruins | DBMS_STATS regular |

## Checklist rápido para query lenta

1. ✅ Tem bind variables? (não literais)
2. ✅ EXPLAIN PLAN mostra full scan em tabela grande?
3. ✅ Stats da tabela atualizadas?
4. ✅ Index no WHERE/JOIN existe e está sendo usado?
5. ✅ Predicado usa função em coluna? (precisa FBI)
6. ✅ Volume da query é razoável? (não está retornando MB sem necessidade)
7. ✅ É loop em PL/SQL? (use BULK)
8. ✅ Tem subquery correlacionada? (refatore com JOIN)

## Linkagem

- Templates → `assets/` (não há templates específicos de performance — use os de PL/SQL com princípios aplicados)
- Para PL/SQL bulk → `plsql-trivadis-guidelines.md`
- Para troubleshoot operacional → `dba-operations.md`
