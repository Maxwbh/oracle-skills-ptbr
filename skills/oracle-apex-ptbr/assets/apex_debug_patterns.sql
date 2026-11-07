--==============================================================================
-- APEX_DEBUG — logging instrumentado para apex_debug_messages
--
-- APEX_DEBUG grava mensagens estruturadas na tabela WWV_FLOW_DEBUG_MESSAGES
-- (acessível via view apex_debug_messages). Diferente de DBMS_OUTPUT (volátil)
-- e Logger (genérico), APEX_DEBUG está integrado ao Debug View do builder.
--
-- Níveis (1=mais crítico, 9=mais verboso):
--   1 = ERROR
--   2 = WARN
--   4 = INFO     (default)
--   5 = APP_ENTER (entrada de procedure — use APEX_DEBUG.enter)
--   6 = APP_TRACE
--   9 = APP_DEBUG / TRACE
--==============================================================================

--==============================================================================
-- 1. Logs básicos por nível
--==============================================================================

BEGIN
  APEX_DEBUG.error('Erro crítico em ' || lc_nome_unidade);
  APEX_DEBUG.warn('Situação anômala mas continuável');
  APEX_DEBUG.info('Marco de processo — começou X, terminou Y');
  APEX_DEBUG.trace('Detalhe verboso — só liga em troubleshoot');
END;
/

-- Equivalente verboso com nível explícito:
BEGIN
  APEX_DEBUG.message(
    p_message => 'Mensagem com nível custom',
    p_level   => APEX_DEBUG.c_log_level_info  -- ou 1/2/4/5/6/9
  );
END;
/

--==============================================================================
-- 2. Logs com parâmetros estruturados (debug context)
--==============================================================================

DECLARE
  lc_nome_unidade CONSTANT VARCHAR2(60) := 'PAGAMENTO_PKG.processar';
BEGIN
  -- Estilo printf — APEX_DEBUG substitui %s pelos parâmetros
  APEX_DEBUG.info(
    p_message => 'Processando fatura %s, valor %s, cliente %s',
    p0 => :P10_ID_FATURA,
    p1 => :P10_VALOR,
    p2 => :P10_ID_CLIENTE
  );

  -- Com nome explícito da unidade (boa prática)
  APEX_DEBUG.message(
    p_message => 'Em ' || lc_nome_unidade || ': fatura %s atualizada',
    p0        => :P10_ID_FATURA,
    p_level   => APEX_DEBUG.c_log_level_info
  );
END;
/

--==============================================================================
-- 3. Ativar / desativar debug em runtime
--==============================================================================

-- Via URL: adicionar &DEBUG=YES ao link.
-- Via PL/SQL: forçar debug mesmo sem URL parameter
BEGIN
  APEX_DEBUG.enable;
END;
/

-- Em On-Demand Process para liberar debug condicionalmente:
BEGIN
  IF v('G_PERFIL') = 'DEV' THEN
    APEX_DEBUG.enable(p_level => APEX_DEBUG.c_log_level_app_trace);
  END IF;
END;
/

-- Desligar
BEGIN
  APEX_DEBUG.disable;
END;
/

--==============================================================================
-- 4. Consultar apex_debug_messages
--==============================================================================

-- Debug da sessão atual:
SELECT message_timestamp,
       page_id,
       message_level,
       SUBSTR(message, 1, 200) AS msg
  FROM apex_debug_messages
 WHERE application_id = :APP_ID
   AND session_id     = :APP_SESSION
 ORDER BY message_timestamp;

-- Debug de uma página específica nas últimas N horas:
SELECT message_timestamp,
       page_id,
       application_user,
       message_level,
       message
  FROM apex_debug_messages
 WHERE application_id = :APP_ID
   AND page_id        = 49
   AND message_timestamp > SYSTIMESTAMP - INTERVAL '2' HOUR
 ORDER BY message_timestamp DESC;

-- Filtrar só erros das últimas 24h:
SELECT application_user,
       page_id,
       MAX(message_timestamp) AS ultimo,
       COUNT(*) AS qtd,
       SUBSTR(MAX(message), 1, 100) AS amostra
  FROM apex_debug_messages
 WHERE message_level = 1  -- ERROR
   AND application_id = :APP_ID
   AND message_timestamp > SYSDATE - 1
 GROUP BY application_user, page_id
 ORDER BY qtd DESC;

--==============================================================================
-- 5. Limpar debug messages (manutenção)
--==============================================================================

-- Cuidado: pode apagar debug útil de outras sessões. Use com data filter:
BEGIN
  APEX_DEBUG.remove_debug_by_age(p_application_id => :APP_ID, p_older_than_days => 7);
END;
/

-- DELETE manual (precisa de privilégio adequado):
-- DELETE FROM wwv_flow_debug_messages
--  WHERE application_id = :APP_ID
--    AND message_timestamp < SYSDATE - 7;

--==============================================================================
-- 6. Padrões de uso
--==============================================================================

/*
PADRÃO A: Entry de procedure (API dedicada)
  PROCEDURE processar_x (p_id NUMBER) IS
  BEGIN
    APEX_DEBUG.enter('PAGAMENTO_PKG.processar_x', 'p_id', p_id);
    -- ... lógica ... (não há "exit" dedicado; logue um info final se precisar)
  END;

PADRÃO B: Log condicional para performance
  -- Não monte mensagem cara se debug está desligado
  IF apex_application.g_debug THEN
    APEX_DEBUG.trace(
      'Estado complexo: ' || construir_dump_caro_de_estado
    );
  END IF;

PADRÃO C: Capturar SQLERRM com contexto
  EXCEPTION
    WHEN OTHERS THEN
      APEX_DEBUG.error(
        'Exception em %s: %s',
        p0 => lc_nome_unidade,
        p1 => SQLERRM
      );
      RAISE;

PADRÃO D: Audit de quem viu o quê
  -- Não usar APEX_DEBUG para audit de negócio — use tabela própria.
  -- APEX_DEBUG é debug-only; pode ser purgado.
*/

--==============================================================================
-- 7. APEX_DEBUG vs Logger framework
--==============================================================================

/*
USE APEX_DEBUG QUANDO:
  - Logging vinculado a contexto APEX (app, page, session, user)
  - Quer ver no Debug View do Builder
  - Vai purgar em alguns dias (debug volátil mesmo)

USE LOGGER (OraOpenSource) QUANDO:
  - Logging em jobs/background sem contexto APEX
  - Audit que tem que sobreviver (use log_permanent)
  - Captura automática de call stack / error backtrace
  - Logging em packages "neutros" reaproveitáveis fora do APEX

PADRÃO MISTO RAZOÁVEL:
  - APEX_DEBUG em On-Demand Process, Page Process, Dynamic Action server-side
  - Logger em packages de negócio chamadas tanto de APEX quanto de jobs
*/

--==============================================================================
-- 8. Anti-patterns
--==============================================================================

/*
ANTI-PATTERN 1: APEX_DEBUG.info dentro de FOR LOOP grande
  -- POLUI tabela
  FOR i IN 1..1000 LOOP
    APEX_DEBUG.info('Processando linha ' || i);
  END LOOP;

  -- BOM: marcos a cada N iterações + sumário
  IF MOD(i, 100) = 0 THEN APEX_DEBUG.info('100 linhas processadas'); END IF;

ANTI-PATTERN 2: Concatenar SQLERRM sem nível ERROR
  -- DIFÍCIL filtrar depois
  APEX_DEBUG.info('Erro: ' || SQLERRM);

  -- BOM: use o nível certo
  APEX_DEBUG.error('Erro em %s: %s', p0=>lc_unit, p1=>SQLERRM);

ANTI-PATTERN 3: Logar dados sensíveis
  APEX_DEBUG.info('Senha recebida: ' || p_senha);  -- ❌
  APEX_DEBUG.info('CPF: ' || p_cpf);               -- ❌ (LGPD)

  -- BOM: ofuscar ou omitir
  APEX_DEBUG.info('CPF últimos 4: ' || SUBSTR(p_cpf, -4));

ANTI-PATTERN 4: APEX_DEBUG como audit log persistente
  -- ERRADO: apex_debug_messages é purgada pela retention do workspace
  APEX_DEBUG.info('Usuário aprovou pagamento de R$ 50.000');  -- audit ❌

  -- BOM: tabela de audit própria
  INSERT INTO log_acoes (id_usuario, acao, detalhe, ts) VALUES (...);
*/
