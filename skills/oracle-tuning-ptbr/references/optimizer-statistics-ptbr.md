# Estatísticas do Optimizer — DBMS_STATS, Histogramas, Directives e Advisor

Aprofundamento sobre estatísticas do optimizer no Oracle 19c. O CBO (Cost-Based
Optimizer) escolhe planos a partir das estatísticas; estatísticas erradas ou
ausentes são a causa nº 1 de cardinalidade mal estimada e, por consequência, de
plano ruim. Este reference cobre coleta, preferências, histogramas, estatísticas
estendidas, SQL Plan Directives, e o gerenciamento do ciclo de vida das stats
(lock, pending, restore, retention, report) além do Optimizer Statistics Advisor.

> Notas de versão 19c verificadas: `optimizer_adaptive_statistics` tem default
> **FALSE** (prioriza estabilidade de plano); a criação automática de column
> group é **OFF** por padrão, controlada pela preferência `AUTO_STAT_EXTENSIONS`;
> o 19c adiciona coleta automática de alta frequência (high-frequency, a cada
> ~15 min para objetos stale) e real-time statistics em INSERT/UPDATE/MERGE.

## Índice

- [Conceitos: o que o optimizer usa](#conceitos-o-que-o-optimizer-usa)
- [Coleta com DBMS_STATS](#coleta-com-dbms_stats)
- [Preferências (preferences)](#preferências-preferences)
- [Histogramas](#histogramas)
- [Estatísticas estendidas (column groups)](#estatísticas-estendidas-column-groups)
- [SQL Plan Directives e dynamic statistics](#sql-plan-directives-e-dynamic-statistics)
- [Ciclo de vida: lock, pending, restore, retention, report](#ciclo-de-vida-lock-pending-restore-retention-report)
- [Coleta automática](#coleta-automática)
- [Optimizer Statistics Advisor](#optimizer-statistics-advisor)
- [SQL Tuning Advisor e SQL Profiles](#sql-tuning-advisor-e-sql-profiles)
- [Checklist de diagnóstico de estatísticas](#checklist-de-diagnóstico-de-estatísticas)

## Conceitos: o que o optimizer usa

Para cada tabela/coluna/índice, o optimizer consulta estatísticas no dicionário:

- **Tabela:** `num_rows`, `blocks`, `avg_row_len` (`dba_tab_statistics`).
- **Coluna:** `num_distinct` (NDV), `num_nulls`, `density`, presença de
  `histogram`, `low_value`/`high_value` (`dba_tab_col_statistics`).
- **Índice:** `distinct_keys`, `clustering_factor`, `leaf_blocks`, `blevel`
  (`dba_indexes`).

A estimativa básica de cardinalidade para um predicado de igualdade sem
histograma é `num_rows * density`, onde `density ≈ 1/num_distinct`. Para um range
(`coluna BETWEEN v1 AND v2`) sem histograma, o optimizer usa interpolação linear
sobre `low_value`/`high_value`:

```
cardinalidade ≈ ( (v2 - v1) / (high_value - low_value) + 2*density ) * num_rows
```

Quando os dados são **assimétricos** (skew) — poucos valores concentram muitas
linhas — a densidade plana erra feio. É aí que entram os histogramas.

## Coleta com DBMS_STATS

```sql
-- Tabela (forma recomendada: deixar o Oracle decidir amostra e histogramas)
BEGIN
  DBMS_STATS.gather_table_stats(
    ownname          => USER,
    tabname          => 'FATURAS',
    estimate_percent => DBMS_STATS.auto_sample_size,  -- não fixe percentual
    method_opt       => 'FOR ALL COLUMNS SIZE AUTO',  -- histograma onde compensa
    cascade          => TRUE,                          -- inclui índices
    degree           => DBMS_STATS.auto_degree
  );
END;
/

-- Schema inteiro, só o que está stale/sem stats
EXEC DBMS_STATS.gather_schema_stats(ownname => USER, options => 'GATHER AUTO');

-- Coletar só índice
EXEC DBMS_STATS.gather_index_stats(ownname => USER, indname => 'IDX_FAT_CLI_DATA');
```

Princípios de coleta:
- **Use `auto_sample_size`** em vez de fixar `estimate_percent`. O algoritmo de
  NDV do `auto_sample_size` é preciso e rápido (hash-based), diferente da
  amostragem fixa que pode errar a contagem de distintos.
- **`method_opt => 'FOR ALL COLUMNS SIZE AUTO'`** deixa o Oracle decidir em quais
  colunas criar histograma (com base no uso em predicados + skew). Evite
  `SIZE 254` cego em todas as colunas.
- **`options => 'GATHER AUTO'`** coleta apenas objetos com stats stale ou
  ausentes — ideal para rotina.
- Uma tabela é considerada **stale** quando ~10% das linhas mudaram desde a
  última coleta (preferência `STALE_PERCENT`, default 10). Verifique em
  `dba_tab_statistics.stale_stats` (`YES`/`NO`).

## Preferências (preferences)

As preferências controlam o comportamento padrão do `DBMS_STATS`. Há hierarquia:
**tabela → schema → global**. A mais específica vence.

```sql
-- Ler preferências globais (todas relevantes de uma vez)
SELECT DBMS_STATS.get_prefs('ESTIMATE_PERCENT') estimate_percent,
       DBMS_STATS.get_prefs('METHOD_OPT')       method_opt,
       DBMS_STATS.get_prefs('DEGREE')           degree,
       DBMS_STATS.get_prefs('CASCADE')          cascade,
       DBMS_STATS.get_prefs('STALE_PERCENT')    stale_percent,
       DBMS_STATS.get_prefs('INCREMENTAL')      incremental,
       DBMS_STATS.get_prefs('PUBLISH')          publish,
       DBMS_STATS.get_prefs('AUTO_STAT_EXTENSIONS') auto_stat_ext
  FROM dual;

-- Preferência só de uma tabela
SELECT DBMS_STATS.get_prefs('STALE_PERCENT', USER, 'FATURAS') FROM dual;

-- Definir preferência de tabela (não afeta as demais)
EXEC DBMS_STATS.set_table_prefs(USER, 'FATURAS', 'STALE_PERCENT', '13');

-- Definir preferência global (afeta o banco todo)
EXEC DBMS_STATS.set_global_prefs('AUTO_TASK_MAX_RUN_TIME', '3600');

-- Listar preferências definidas por tabela
SELECT * FROM user_tab_stat_prefs;
```

Preferências que mais importam em tuning:
- **`INCREMENTAL`** (`TRUE`/`FALSE`): em tabelas particionadas, mantém synopses
  por partição e deriva a stat global sem reescanear tudo. Liga junto com
  `GRANULARITY => 'AUTO'`.
- **`STALE_PERCENT`**: limiar de quanto a tabela muda antes de virar stale.
- **`PUBLISH`** (`TRUE`/`FALSE`): com `FALSE`, a coleta gera **pending stats**
  (ver adiante), que não entram em vigor até serem publicadas.
- **`AUTO_STAT_EXTENSIONS`** (`ON`/`OFF`, default OFF): se `ON`, o banco cria
  column groups automaticamente a partir de SQL Plan Directives.

## Histogramas

Histograma descreve a **distribuição** dos valores de uma coluna, permitindo ao
optimizer estimar bem mesmo com skew. O Oracle 19c tem quatro tipos, escolhidos
automaticamente conforme NDV e o número de buckets (`SIZE`):

| Tipo | Quando o Oracle escolhe | Característica |
|---|---|---|
| **Frequency** | NDV ≤ nº de buckets | Um bucket por valor distinto. Exato. |
| **Top-Frequency** | NDV > buckets, mas os N valores mais comuns cobrem ≥ p% das linhas (p = (1 - 1/buckets)*100) | Frequency só dos top-N; ignora a "cauda" rara. |
| **Height-Balanced** | Modo legado (pré-12c) ou amostra não permite hybrid | Cada bucket com ~mesmo nº de linhas. Menos preciso. |
| **Hybrid** | NDV > buckets e não atende ao critério de top-frequency | Combina height-balanced com frequência por endpoint. Default moderno. |

```sql
-- Forçar histograma numa coluna com até 130 buckets
BEGIN
  DBMS_STATS.gather_table_stats(
    ownname    => USER,
    tabname    => 'FATURAS',
    method_opt => 'FOR COLUMNS status SIZE 130'
  );
END;
/

-- Ver o tipo de histograma e nº de buckets
SELECT column_name, num_distinct, histogram, num_buckets
  FROM user_tab_col_statistics
 WHERE table_name = 'FATURAS';

-- Inspecionar os buckets (endpoints)
SELECT endpoint_number, endpoint_value,
       endpoint_number
         - LAG(endpoint_number, 1, 0) OVER (ORDER BY endpoint_number) AS linhas_no_bucket
  FROM user_histograms
 WHERE table_name = 'FATURAS'
   AND column_name = 'STATUS'
 ORDER BY endpoint_number;
```

Regra de decisão Top-Frequency vs Hybrid: calcule o **fator p** = `(1 - 1/buckets)*100`.
Some a frequência dos `buckets` valores mais comuns; se essa soma cobre ≥ p% do
total de linhas, o Oracle usa **top-frequency**, senão **hybrid**.

Quando criar histograma: colunas usadas em predicados (`WHERE`, `JOIN`) **e** com
distribuição assimétrica. Não crie em colunas uniformes ou nunca filtradas — só
adiciona custo de coleta e risco de bind peeking ruim.

## Estatísticas estendidas (column groups)

Quando duas colunas são **correlacionadas** (ex.: `id_municipio` e `uf` — a UF é
determinada pelo município), o optimizer assume independência e multiplica as
seletividades, subestimando a cardinalidade. Estatísticas estendidas de **column
group** corrigem isso.

```sql
-- Criar o grupo de colunas e coletar com histogramas onde houver skew
SELECT DBMS_STATS.create_extended_stats(USER, 'CLIENTES',
         '(id_municipio, uf)') FROM dual;

EXEC DBMS_STATS.gather_table_stats(USER, 'CLIENTES', -
       method_opt => 'FOR ALL COLUMNS SIZE SKEWONLY');

-- Conferir as extensões criadas e suas stats
SELECT e.extension AS col_group, t.num_distinct, t.histogram
  FROM user_stat_extensions e
  JOIN user_tab_col_statistics t ON t.column_name = e.extension_name
                                 AND t.table_name = e.table_name
 WHERE e.table_name = 'CLIENTES';

-- Remover
EXEC DBMS_STATS.drop_extended_stats(USER, 'CLIENTES', '(id_municipio, uf)');
```

Também há extended stats de **expressão** (ex.: `(UPPER(nome))`), que ajudam o
optimizer a estimar predicados com função sem precisar de FBI dedicado para a
cardinalidade.

## SQL Plan Directives e dynamic statistics

Uma **SQL Plan Directive** é uma instrução que o optimizer cria automaticamente
quando detecta erro de cardinalidade (geralmente por colunas correlacionadas).
Na próxima vez, ela faz o optimizer usar **dynamic sampling** e pode levar à
criação de um column group.

```sql
-- Pré-requisito para directives entrarem em ação (default 19c é FALSE)
ALTER SESSION SET optimizer_adaptive_statistics = TRUE;

-- Após uma query com erro de estimativa, verificar se foi marcada p/ reotimizar
SELECT sql_id, child_number, executions, is_reoptimizable, sql_text
  FROM v$sql
 WHERE sql_text LIKE '%trecho_distinto%'
   AND sql_text NOT LIKE '%v$sql%';

-- Forçar a gravação das directives em memória para o dicionário
EXEC DBMS_SPD.flush_sql_plan_directive;

-- Consultar directives de um schema
SELECT TO_CHAR(d.directive_id) dir_id,
       o.owner, o.object_name, o.subobject_name AS coluna,
       o.object_type, d.type, d.state, d.reason
  FROM dba_sql_plan_directives d
  JOIN dba_sql_plan_dir_objects o ON o.directive_id = d.directive_id
 WHERE o.owner = USER
 ORDER BY 1;

-- Remover uma directive específica
EXEC DBMS_SPD.drop_sql_plan_directive(directive_id => &dir_id);
```

`is_reoptimizable = Y` indica que o cursor será re-otimizado na próxima execução
porque o optimizer viu divergência entre estimado (E-Rows) e real (A-Rows).

Cuidado de versão: como `optimizer_adaptive_statistics` é FALSE por padrão no
19c, directives existentes ainda são mantidas, mas o uso agressivo de dynamic
sampling guiado por elas fica restrito — decisão deliberada da Oracle para
priorizar estabilidade. A correção definitiva para correlação é criar o column
group (estatística estendida), não depender de directive.

## Ciclo de vida: lock, pending, restore, retention, report

### Lock — congelar estatísticas

Útil para **estabilidade de plano**: travar stats boas conhecidas, ou travar
stats de uma tabela volátil/temporária para evitar coletas ruins.

```sql
EXEC DBMS_STATS.lock_table_stats(USER, 'FATURAS');
EXEC DBMS_STATS.unlock_table_stats(USER, 'FATURAS');
-- Conferir
SELECT table_name, stattype_locked FROM user_tab_statistics
 WHERE table_name = 'FATURAS';
```

Com stats travadas, um `gather` comum é ignorado (a menos de `force => TRUE`).

### Pending — testar antes de publicar

Permite coletar stats, validar o efeito nos planos, e só então publicar.

```sql
-- Passar a tabela para modo "não publicar"
EXEC DBMS_STATS.set_table_prefs(USER, 'FATURAS', 'PUBLISH', 'FALSE');
-- Coletar (vira pending, não entra em vigor)
EXEC DBMS_STATS.gather_table_stats(USER, 'FATURAS');
-- Testar usando as pending nesta sessão
ALTER SESSION SET optimizer_use_pending_statistics = TRUE;
-- ... rodar as queries e comparar planos ...
-- Publicar se aprovado, ou descartar
EXEC DBMS_STATS.publish_pending_stats(USER, 'FATURAS');
EXEC DBMS_STATS.delete_pending_stats(USER, 'FATURAS');
-- Voltar ao normal
EXEC DBMS_STATS.set_table_prefs(USER, 'FATURAS', 'PUBLISH', 'TRUE');
```

### Restore — voltar stats anteriores

Toda coleta arquiva a versão anterior. Se um gather piorou os planos, restaure.

```sql
-- Quando foram alteradas pela última vez?
SELECT table_name, stats_update_time
  FROM user_tab_stats_history
 WHERE table_name = 'FATURAS'
 ORDER BY stats_update_time DESC;

-- Restaurar para um instante anterior
EXEC DBMS_STATS.restore_table_stats(USER, 'FATURAS', SYSTIMESTAMP - 1);
```

### Retention — quanto tempo o histórico é mantido

```sql
SELECT DBMS_STATS.get_stats_history_availability FROM dual;  -- desde quando há histórico
SELECT DBMS_STATS.get_stats_history_retention FROM dual;     -- dias retidos (default 31)
EXEC DBMS_STATS.alter_stats_history_retention(45);           -- alterar
EXEC DBMS_STATS.purge_stats(SYSTIMESTAMP - 60);              -- expurgar antigas
```

### Report — relatório de operações de coleta

```sql
VARIABLE rel CLOB;
BEGIN
  :rel := DBMS_STATS.report_stats_operations(
    since        => SYSDATE - 10,
    until        => SYSDATE,
    detail_level => 'TYPICAL',
    format       => 'HTML');   -- ou 'TEXT'
END;
/
PRINT rel;
```

## Coleta automática

O Oracle roda um job de coleta na janela de manutenção, além do high-frequency.

```sql
-- Status do job automático de stats
SELECT client_name, status, total_cpu_last_30_days
  FROM dba_autotask_client
 WHERE client_name LIKE '%optimizer stats%';

-- Histórico de execuções
SELECT * FROM dba_autotask_client_history
 WHERE client_name LIKE '%optimizer stats%';

-- Desabilitar / reabilitar (use com critério)
BEGIN
  DBMS_AUTO_TASK_ADMIN.disable(
    client_name => 'auto optimizer stats collection',
    operation => NULL, window_name => NULL);
END;
/
BEGIN
  DBMS_AUTO_TASK_ADMIN.enable(
    client_name => 'auto optimizer stats collection',
    operation => NULL, window_name => NULL);
END;
/
```

## Optimizer Statistics Advisor

Recurso (12.2+) que avalia se as estatísticas seguem boas práticas e gera
recomendações + script de correção. A task `AUTO_STATS_ADVISOR_TASK` roda
diariamente na janela de manutenção; o fluxo normal começa lendo o relatório.

```sql
-- Ler o relatório da task automática
SELECT DBMS_STATS.report_advisor_task('AUTO_STATS_ADVISOR_TASK') AS report FROM dual;

-- Executar manualmente uma task própria (requer privilégio ADVISOR)
DECLARE
  l_task VARCHAR2(128);
BEGIN
  l_task := DBMS_STATS.create_advisor_task('STATS_ADVISOR_MANUAL');
  l_task := DBMS_STATS.execute_advisor_task('STATS_ADVISOR_MANUAL');
END;
/

-- Relatório da task manual
SELECT DBMS_STATS.report_advisor_task('STATS_ADVISOR_MANUAL') FROM dual;

-- Gerar o script SQL com as correções recomendadas
SELECT DBMS_STATS.script_advisor_task('STATS_ADVISOR_MANUAL') FROM dual;

-- Implementar as recomendações (revise o script antes!)
SELECT DBMS_STATS.implement_advisor_task('STATS_ADVISOR_MANUAL') FROM dual;
```

O advisor **não coleta** stats por conta própria — gera findings e
recomendações; a aplicação é explícita via `implement_advisor_task` ou rodando o
script de `script_advisor_task`. Prefira revisar o script a implementar cego.

## SQL Tuning Advisor e SQL Profiles

Para uma query específica, o SQL Tuning Advisor analisa e pode recomendar um
**SQL Profile** — um conjunto de ajustes de estimativa que corrige o plano sem
alterar o SQL nem criar baseline.

```sql
-- Criar e executar uma tuning task para um SQL_ID em cache
DECLARE
  l_task VARCHAR2(64);
BEGIN
  l_task := DBMS_SQLTUNE.create_tuning_task(sql_id => '&sql_id');
  DBMS_SQLTUNE.execute_tuning_task(l_task);
END;
/

-- Ver recomendações
SELECT DBMS_SQLTUNE.report_tuning_task('&task_name') FROM dual;

-- Aceitar o SQL Profile recomendado
EXEC DBMS_SQLTUNE.accept_sql_profile(task_name => '&task_name', replace => TRUE);

-- Listar SQL Profiles e remover
SELECT name, status, sql_text FROM dba_sql_profiles;
EXEC DBMS_SQLTUNE.drop_sql_profile(name => '&profile_name', ignore => TRUE);
```

Hierarquia de "fixação" de plano, do mais leve ao mais forte: **estatísticas
corretas** → **SQL Profile** (ajusta estimativas) → **SQL Plan Baseline** (fixa o
plano). Prefira sempre resolver via stats antes de recorrer a profile/baseline.

**Baseline aceito não garante uso.** Num caso relatado no 19c RU 19.32
([oracle-base, 29/09/2026](https://oracle-base.com/blog/2026/09/29/sql-plan-management-spm-baseline-issue/)),
o baseline existia e estava aceito, mas era ignorado porque o plano não podia
ser reproduzido. Depois de criar ou transportar um baseline, confira
`V$SQL.SQL_PLAN_BASELINE` e `DBA_SQL_PLAN_BASELINES.REPRODUCED`; o motivo
aparece no trace `[SQL_Compiler.*]` (seção "SPM Plan Dump"). Ver
`assets/explain_plan_workflow.sql`, etapa 9. Bug/nota MOS: a verificar.

## Checklist de diagnóstico de estatísticas

1. As tabelas envolvidas têm stats? (`last_analyzed` não nulo)
2. As stats estão stale? (`dba_tab_statistics.stale_stats = 'YES'`)
3. E-Rows diverge de A-Rows (>10x) em `DBMS_XPLAN.display_cursor` com
   `ALLSTATS LAST`? → cardinalidade mal estimada.
4. A coluna do predicado tem skew sem histograma? → `method_opt FOR COLUMNS ...`.
5. Há colunas correlacionadas no WHERE? → estatística estendida (column group).
6. Stats foram travadas por engano? (`stattype_locked`)
7. Um gather recente piorou tudo? → `restore_table_stats`.
8. Quer validar antes de publicar? → pending stats.
9. Boas práticas no geral? → rode/leia o Optimizer Statistics Advisor.
