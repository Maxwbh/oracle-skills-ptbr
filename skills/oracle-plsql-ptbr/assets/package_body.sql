--==============================================================================
-- Package BODY: <NOME_PACOTE>_PKG
-- Implementação dos métodos declarados na SPEC.
-- 
-- Padrões:
--   - gc_nome_pacote CONSTANT como identificador para logging/exceptions
--   - lc_nome_unidade por procedure (escopo local) compondo gc_nome_pacote + nome
--   - Exception handler padrão em todo procedure público
--   - Transação: rotinas reutilizáveis não comitam nem fazem ROLLBACK total;
--     usam SAVEPOINT / ROLLBACK TO para desfazer só a própria unidade e
--     propagam o erro original (RAISE). Só o ponto de entrada (job, endpoint,
--     process de página) é dono da transação — ver processar_pendentes.
--   - Forward declarations para procedures privadas usadas antes de declaradas
--==============================================================================

CREATE OR REPLACE PACKAGE BODY <nome_pacote>_pkg AS

  --============================================================================
  -- Constantes privadas
  --============================================================================
  
  -- Identificador do package para logging/exceptions
  gc_nome_pacote CONSTANT VARCHAR2(30) := '<NOME_PACOTE>_PKG';

  -- Status válidos do domínio
  gc_status_pendente  CONSTANT VARCHAR2(1) := 'P';
  gc_status_ativo     CONSTANT VARCHAR2(1) := 'A';
  gc_status_concluido CONSTANT VARCHAR2(1) := 'C';

  --============================================================================
  -- Variáveis globais (use com parcimônia — persistem na sessão)
  --============================================================================
  
  g_cache_inicializado BOOLEAN := FALSE;

  --============================================================================
  -- Forward declarations (procedures privadas usadas antes de declaradas)
  --============================================================================
  
  PROCEDURE validar_estado_registro (p_id IN NUMBER, p_status IN VARCHAR2);
  PROCEDURE registrar_evento (p_mensagem IN VARCHAR2);

  --============================================================================
  -- Procedures e Functions públicas
  --============================================================================

  -----------------------------------------------------------------------------
  -- processar_registro
  --
  -- Rotina REUTILIZÁVEL: não comita e não faz ROLLBACK total — quem decide é
  -- o dono da transação (job, endpoint, process de página). Em caso de erro,
  -- desfaz só o próprio trabalho (ROLLBACK TO SAVEPOINT) e propaga a exceção
  -- original (RAISE), sem trocar o código do erro.
  -----------------------------------------------------------------------------
  PROCEDURE processar_registro (
    p_id            IN NUMBER,
    p_forcar_update IN VARCHAR2 DEFAULT 'N'
  ) IS
    -- Identificador único da unidade para logging
    lc_nome_unidade CONSTANT VARCHAR2(60) := gc_nome_pacote || '.processar_registro';

    l_status_atual VARCHAR2(1);
  BEGIN
    -- Primeiro comando: marca o início do trabalho desta unidade
    SAVEPOINT sp_processar_registro;

    -- Validação de pré-condições
    IF p_id IS NULL THEN
      raise_application_error(-20102,
        'Parâmetro p_id é obrigatório em ' || lc_nome_unidade);
    END IF;

    IF p_forcar_update NOT IN ('Y', 'N') THEN
      raise_application_error(-20103,
        'p_forcar_update deve ser Y ou N em ' || lc_nome_unidade);
    END IF;

    -- Verifica existência (NO_DATA_FOUND tratado embaixo)
    SELECT status INTO l_status_atual
      FROM registros
     WHERE id = p_id;

    IF l_status_atual = gc_status_concluido THEN
      -- No-op se já processado e não está forçando
      IF p_forcar_update = 'N' THEN
        registrar_evento(lc_nome_unidade || ': registro ' || p_id || ' já processado, sem ação');
        RETURN;
      END IF;
    ELSE
      -- Pendente/ativo seguem; qualquer outro estado levanta e_estado_invalido
      validar_estado_registro(p_id, l_status_atual);
    END IF;

    -- Operação principal (usa bind variable implícito em PL/SQL)
    UPDATE registros
       SET status         = gc_status_concluido,
           processado_em  = SYSDATE,
           processado_por = USER
     WHERE id = p_id;

    -- Confirma atualização
    IF SQL%ROWCOUNT = 0 THEN
      raise_application_error(-20104,
        'Nenhuma linha atualizada em ' || lc_nome_unidade || ' para ID ' || p_id);
    END IF;

    registrar_evento(lc_nome_unidade || ': registro ' || p_id || ' processado com sucesso');
    -- SEM COMMIT: o dono da transação decide (ver processar_pendentes).

  EXCEPTION
    WHEN NO_DATA_FOUND THEN
      ROLLBACK TO sp_processar_registro;
      -- Erro de negócio conhecido: código próprio (mapeado em e_nao_encontrado)
      raise_application_error(-20101,
        'Registro não encontrado em ' || lc_nome_unidade || ': ID = ' || p_id);

    WHEN OTHERS THEN
      -- Desfaz só o trabalho desta unidade; o do chamador fica intacto
      ROLLBACK TO sp_processar_registro;
      registrar_evento(lc_nome_unidade || ': ' || SQLERRM
        || ' | ' || DBMS_UTILITY.format_error_backtrace);
      RAISE;  -- preserva o código e a pilha do erro original
  END processar_registro;


  -----------------------------------------------------------------------------
  -- processar_pendentes
  --
  -- PONTO DE ENTRADA (ex.: job do DBMS_SCHEDULER): é o DONO DA TRANSAÇÃO.
  -- Só aqui há COMMIT e ROLLBACK total. Política escolhida: um registro com
  -- erro não impede os demais (commit por item); o erro fica registrado.
  -----------------------------------------------------------------------------
  PROCEDURE processar_pendentes IS
    lc_nome_unidade CONSTANT VARCHAR2(60) := gc_nome_pacote || '.processar_pendentes';

    l_ids t_lista_ids;
  BEGIN
    -- Lê os IDs antes de processar: não há fetch através de COMMIT
    -- (evita ORA-01555). Para volumes grandes, use BULK COLLECT ... LIMIT.
    SELECT id
      BULK COLLECT INTO l_ids
      FROM registros
     WHERE status IN (gc_status_pendente, gc_status_ativo)
     ORDER BY id
     FETCH FIRST gc_max_registros ROWS ONLY;

    FOR i IN 1 .. l_ids.COUNT LOOP
      BEGIN
        processar_registro(l_ids(i));
        COMMIT;
      EXCEPTION
        WHEN OTHERS THEN
          -- processar_registro já desfez a própria unidade e registrou o erro;
          -- o dono da transação decide seguir para o próximo item.
          ROLLBACK;
      END;
    END LOOP;
  EXCEPTION
    WHEN OTHERS THEN
      ROLLBACK;
      registrar_evento(lc_nome_unidade || ': ' || SQLERRM
        || ' | ' || DBMS_UTILITY.format_error_backtrace);
      RAISE;
  END processar_pendentes;


  -----------------------------------------------------------------------------
  -- obter_status
  -----------------------------------------------------------------------------
  FUNCTION obter_status (
    p_id IN NUMBER
  ) RETURN VARCHAR2 IS
    l_status VARCHAR2(1);
  BEGIN
    SELECT status INTO l_status
      FROM registros
     WHERE id = p_id;
    
    RETURN l_status;
  EXCEPTION
    WHEN NO_DATA_FOUND THEN
      -- Função obter_* retorna NULL para não-encontrado (vs. procedure que faz raise)
      RETURN NULL;
  END obter_status;


  -----------------------------------------------------------------------------
  -- obter_resumo
  -----------------------------------------------------------------------------
  FUNCTION obter_resumo (
    p_data_inicio IN DATE,
    p_data_fim    IN DATE
  ) RETURN r_resumo IS
    lc_nome_unidade CONSTANT VARCHAR2(60) := gc_nome_pacote || '.obter_resumo';
    r_resultado r_resumo;
  BEGIN
    -- Valida intervalo
    IF p_data_inicio IS NULL OR p_data_fim IS NULL THEN
      raise_application_error(-20102,
        'Datas são obrigatórias em ' || lc_nome_unidade);
    END IF;

    IF p_data_inicio > p_data_fim THEN
      raise_application_error(-20105,
        'Data inicial não pode ser maior que final em ' || lc_nome_unidade);
    END IF;

    -- Coleta agregados em uma única query (eficiente)
    SELECT COUNT(*),
           NVL(SUM(valor), 0),
           MAX(processado_em)
      INTO r_resultado.qtd_total,
           r_resultado.valor_total,
           r_resultado.ultimo_processado
      FROM registros
     WHERE processado_em BETWEEN p_data_inicio AND p_data_fim
       AND status = gc_status_concluido;

    RETURN r_resultado;
  EXCEPTION
    WHEN OTHERS THEN
      -- Função de leitura pura: agregados não lançam NO_DATA_FOUND.
      -- Preserva o backtrace original para não perder a origem do erro.
      raise_application_error(-20999,
        'Erro inesperado em ' || lc_nome_unidade || ': ' || SQLERRM
        || CHR(10) || DBMS_UTILITY.format_error_backtrace);
  END obter_resumo;


  --============================================================================
  -- Procedures e Functions privadas
  --============================================================================

  -----------------------------------------------------------------------------
  -- validar_estado_registro
  -- Verifica se o status lido permite processamento (pendente ou ativo).
  -----------------------------------------------------------------------------
  PROCEDURE validar_estado_registro (p_id IN NUMBER, p_status IN VARCHAR2) IS
    lc_nome_unidade CONSTANT VARCHAR2(60) := gc_nome_pacote || '.validar_estado_registro';
  BEGIN
    IF p_status IS NULL OR p_status NOT IN (gc_status_pendente, gc_status_ativo) THEN
      -- -20100 = e_estado_invalido (PRAGMA EXCEPTION_INIT na spec)
      raise_application_error(-20100,
        'Estado inválido (' || p_status || ') em ' || lc_nome_unidade || ' para ID ' || p_id);
    END IF;
  END validar_estado_registro;


  -----------------------------------------------------------------------------
  -- registrar_evento
  -- Registra evento em tabela de log (autonomous transaction para
  -- persistir mesmo se transação principal sofrer rollback). É a ÚNICA
  -- exceção legítima a "rotina não comita": o COMMIT é da transação
  -- autônoma, não da do chamador. Em produção, prefira o Logger.
  -----------------------------------------------------------------------------
  PROCEDURE registrar_evento (p_mensagem IN VARCHAR2) IS
    PRAGMA AUTONOMOUS_TRANSACTION;
  BEGIN
    INSERT INTO log_eventos (criado_em, nome_pacote, mensagem)
    VALUES (SYSTIMESTAMP, gc_nome_pacote, p_mensagem);
    COMMIT;
  EXCEPTION
    WHEN OTHERS THEN
      -- Log de log não deve quebrar fluxo principal
      ROLLBACK;
  END registrar_evento;


END <nome_pacote>_pkg;
/
