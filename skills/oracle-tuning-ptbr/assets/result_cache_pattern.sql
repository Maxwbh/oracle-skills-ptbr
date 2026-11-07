--==============================================================================
-- Template: RESULT_CACHE em PL/SQL e SQL
--
-- Server-side result cache (11gR2+) armazena o RESULTADO de uma function ou
-- query SQL em memória SGA compartilhada entre sessões. A segunda chamada com
-- os mesmos parâmetros retorna em microssegundos, sem executar o corpo.
--
-- EDIÇÃO: Query Results Cache e PL/SQL Function Result Cache são só
-- Enterprise Edition (Database Licensing Information 19c, consultado em
-- 07/11/2026). Em SE2, cache de resultado fica na aplicação ou em coleção
-- de package (por sessão).
--
-- Trade-off central: invalidação. O cache é DESCARTADO automaticamente quando:
--   - Qualquer DML é feita em tabela "Result Cache dependente"
--   - Estatísticas mudam (DBMS_STATS.gather_*)
--   - DDL em qualquer objeto referenciado
--
-- Implicação: ideal para dados "quase-estáticos" (configuração, dimensões,
-- tabelas pequenas com poucas atualizações). Péssimo para tabela transacional.
--==============================================================================

--==============================================================================
-- 1. Pré-requisito: result_cache_max_size > 0
--==============================================================================

-- Verificar configuração da instância:
SHOW PARAMETER result_cache;

-- Setar (DBA, requer scope=spfile + bounce em alguns casos):
-- ALTER SYSTEM SET result_cache_max_size = 256M SCOPE=BOTH;
-- ALTER SYSTEM SET result_cache_mode = MANUAL;  -- só funções/SQL marcadas explicitamente

--==============================================================================
-- 2. PL/SQL function com RESULT_CACHE
--==============================================================================

CREATE OR REPLACE FUNCTION obter_taxa_imposto (
  p_uf       IN VARCHAR2,
  p_tipo     IN VARCHAR2
) RETURN NUMBER
  RESULT_CACHE                       -- ← marca a function como cacheável
IS
  l_taxa NUMBER;
BEGIN
  SELECT taxa INTO l_taxa
    FROM regras_fiscais
   WHERE uf   = p_uf
     AND tipo = p_tipo;

  RETURN l_taxa;
EXCEPTION
  WHEN NO_DATA_FOUND THEN
    RETURN 0;
END;
/

-- A partir da 2ª chamada com os mesmos (p_uf, p_tipo), Oracle retorna do cache.
-- Cache é INVALIDADO automaticamente quando há DML em REGRAS_FISCAIS.

--==============================================================================
-- 3. SQL com /*+ RESULT_CACHE */ hint
--==============================================================================

-- Útil para queries SQL que são executadas frequentemente com mesmos binds:
SELECT /*+ RESULT_CACHE */
       uf,
       tipo,
       taxa
  FROM regras_fiscais
 WHERE uf = 'MG';

-- Em 11g+ o resultado fica cacheado e a próxima execução com mesmo bind é instantânea.

--==============================================================================
-- 4. Quando USAR result cache
--==============================================================================

/*
USE RESULT_CACHE QUANDO:

  - Dado é "quase estático" (configuração, dimensões, parâmetros, FX rates)
  - Função é chamada MUITAS vezes com poucos valores distintos de parâmetro
  - Custo de calcular é alto (JOIN pesado, agregação, function call)
  - Invalidação por DML é OK (não há mudança no meio de uma operação crítica)

EXEMPLOS DE BOM USO:
  - obter_taxa_imposto(UF, tipo)       — 27 UFs × ~5 tipos = 135 combinações
  - obter_descricao_status(status)     — meia dúzia de status
  - calcular_dia_util(data, calendario) — caching por (data, calendário)
  - obter_config_aplicacao(chave)      — dezenas de chaves

NÃO USE QUANDO:

  - Tabela tem alta taxa de DML (cache é descartado a toda hora; pior que nada)
  - Parâmetros têm muita cardinalidade (cache não cabe na SGA)
  - Função tem side effects (logging, DML) — RESULT_CACHE não chama o corpo!
  - Resultado depende de SYSDATE, USER, ou contexto de sessão (cache "vaza" valores)

EXEMPLOS DE MAU USO:
  - obter_saldo_cliente(id)            — saldo muda toda hora
  - obter_estoque_produto(id)          — DML constante invalida
  - logar_e_calcular_x(...)            — side effect: log não acontece em hit
*/

--==============================================================================
-- 5. Monitorar uso do cache
--==============================================================================

-- Estatísticas globais:
SELECT * FROM v$result_cache_statistics;

-- Objetos no cache + hits/invalidações:
SELECT cache_id,
       name,
       type,
       status,
       creation_timestamp,
       block_count,
       column_count,
       row_count,
       scan_count
  FROM v$result_cache_objects
 WHERE type = 'Result'
 ORDER BY scan_count DESC NULLS LAST;

-- Dependências (que tabelas invalidam o quê):
SELECT *
  FROM v$result_cache_dependency;

-- Flush manual (raramente necessário; útil em testes):
-- EXEC DBMS_RESULT_CACHE.flush;

--==============================================================================
-- 6. RELIES_ON — controle manual de dependências (CUIDADO)
--==============================================================================

-- Em alguns casos a function não depende de tabela (ex: cálculo determinístico
-- caro). Pode-se forçar comportamento via PRAGMA:

CREATE OR REPLACE FUNCTION fibonacci (
  p_n IN PLS_INTEGER
) RETURN NUMBER
  RESULT_CACHE
IS
BEGIN
  IF p_n <= 1 THEN RETURN p_n; END IF;
  RETURN fibonacci(p_n - 1) + fibonacci(p_n - 2);
END;
/

-- Mas se a função USA tabela e você quer customizar a invalidação,
-- há a cláusula RELIES_ON (deprecada desde 12c, NÃO usar em código novo).
-- Em vez disso, deixe o auto-detect funcionar.

--==============================================================================
-- 7. Anti-patterns
--==============================================================================

/*
ANTI-PATTERN 1: RESULT_CACHE em function com side effect
  -- ERRADO: a function logger não roda no segundo hit; perde-se a auditoria
  FUNCTION obter_x RESULT_CACHE IS
  BEGIN
    logger.log('chamada');  -- ❌ só roda na 1ª vez
    RETURN ...;
  END;

ANTI-PATTERN 2: RESULT_CACHE em function que lê SYSDATE/SYS_CONTEXT
  -- ERRADO: cache memoriza o valor da 1ª chamada
  FUNCTION saudacao RETURN VARCHAR2 RESULT_CACHE IS
  BEGIN
    IF TO_CHAR(SYSDATE, 'HH24') < 12 THEN RETURN 'Bom dia';
    ELSE RETURN 'Boa tarde';
    END IF;
  END;
  -- Resultado: "Bom dia" pode persistir até a tarde.

ANTI-PATTERN 3: RESULT_CACHE em function determinística pura
  -- DESPERDÍCIO: marque como DETERMINISTIC, não RESULT_CACHE.
  -- DETERMINISTIC é mais leve (caching só dentro de uma query, sem SGA).
  FUNCTION pi RETURN NUMBER DETERMINISTIC IS BEGIN RETURN 3.14159; END;

ANTI-PATTERN 4: Result cache em tabela transacional
  -- INEFICAZ: cada commit invalida o cache; resultado é sempre "calculado".
  FUNCTION saldo_cliente(p_id NUMBER) RETURN NUMBER RESULT_CACHE IS
  BEGIN
    SELECT SUM(valor) INTO l FROM movimentacoes WHERE id_cliente = p_id;
    RETURN l;
  END;
  -- Toda inserção em movimentacoes detona o cache. Em sistema OLTP, cache vive < 1s.
*/
