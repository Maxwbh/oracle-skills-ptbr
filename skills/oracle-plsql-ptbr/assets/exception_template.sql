--==============================================================================
-- Template: tratamento de exceção e controle de transação
--
-- Uso: copie o esqueleto adequado e substitua os marcadores <...>.
--
-- QUEM É O DONO DA TRANSAÇÃO (regra 4 da skill)
--   A. Rotina REUTILIZÁVEL (procedure/function de package chamada por outras):
--      - NÃO faz COMMIT nem ROLLBACK total;
--      - SAVEPOINT no início + ROLLBACK TO no handler desfaz só o trabalho
--        DELA, preservando o que o chamador já fez;
--      - propaga a exceção (RAISE) — o chamador precisa saber que falhou.
--   B. PONTO DE ENTRADA (job do scheduler, handler ORDS, process de página,
--      script de carga): é o DONO DA TRANSAÇÃO — só ele decide COMMIT e
--      ROLLBACK total. Documente no cabeçalho que ele é o dono.
--      No APEX, quem fecha a transação do request é o próprio APEX: o
--      process de página não comita (convenção da suíte; ver oracle-apex-ptbr).
--
-- POR QUE NÃO "ROLLBACK + raise" EM TODA ROTINA
--   Um ROLLBACK total dentro de uma rotina reutilizável desfaz também o que
--   o CHAMADOR fez antes de chamá-la, sem que ele saiba. E trocar o erro
--   original por raise_application_error(-20999, SQLERRM) perde o código
--   Oracle e a pilha (o chamador não consegue mais tratar ORA-00001, por ex.).
--
-- Padrões aplicados:
--   - lc_nome_unidade CONSTANT compondo nome do package + procedure
--   - Validação de pré-condições (parâmetros)
--   - Erro de NEGÓCIO conhecido: raise_application_error(-20xxx, msg) com
--     contexto; mapeie para exceção nomeada (PRAGMA EXCEPTION_INIT) na spec
--   - Erro INESPERADO: log com backtrace + RAISE (preserva código e pilha).
--     Se precisar acrescentar contexto, raise_application_error(-20xxx, msg,
--     TRUE) — o TRUE mantém a pilha de erros original.
--
-- DEPENDÊNCIAS DE CONTEXTO (este é um esqueleto, não compila isolado):
--   - gc_nome_pacote: constante declarada no PACKAGE BODY
--     (ex.: gc_nome_pacote CONSTANT VARCHAR2(30) := 'MEU_PKG';)
--   - Logger (OraOpenSource) instalado — ou troque por sua rotina de log
--   Exemplo completo e testado: package_body.sql (processar_registro e
--   processar_pendentes).
--==============================================================================


--==============================================================================
-- A. Rotina reutilizável — NÃO comita, desfaz só o próprio trabalho
--==============================================================================

PROCEDURE <nome_procedure> (
  p_param1 IN <tipo>,
  p_param2 IN <tipo> DEFAULT <valor_default>
) IS
  -- Identificador da unidade para logging (composição package + procedure)
  lc_nome_unidade CONSTANT VARCHAR2(60) := gc_nome_pacote || '.<nome_procedure>';

  -- Variáveis locais
  l_qtd NUMBER;
BEGIN
  -- Primeiro comando: marca o início do trabalho desta unidade
  SAVEPOINT sp_<nome_procedure>;

  --==========================================================================
  -- 1. Validação de pré-condições
  --==========================================================================

  IF p_param1 IS NULL THEN
    raise_application_error(-20102,
      'Parâmetro p_param1 é obrigatório em ' || lc_nome_unidade);
  END IF;

  --==========================================================================
  -- 2. Validações de negócio (estado do banco)
  --==========================================================================

  SELECT COUNT(*) INTO l_qtd
    FROM tabela_relacionada
   WHERE id = p_param1;

  IF l_qtd = 0 THEN
    raise_application_error(-20101,
      'Registro relacionado não existe em ' || lc_nome_unidade || ' para ID ' || p_param1);
  END IF;

  --==========================================================================
  -- 3. Lógica principal (pode ter vários DML — o SAVEPOINT cobre todos)
  --==========================================================================

  UPDATE tabela_destino
     SET status         = 'PROCESSADO',
         atualizado_em  = SYSDATE,
         atualizado_por = USER
   WHERE id = p_param1;

  IF SQL%ROWCOUNT = 0 THEN
    raise_application_error(-20104,
      'Nenhuma linha afetada em ' || lc_nome_unidade);
  END IF;

  -- SEM COMMIT: o dono da transação decide.

EXCEPTION
  WHEN DUP_VAL_ON_INDEX THEN
    -- Erro conhecido com significado de negócio: acrescenta contexto e
    -- MANTÉM a pilha original (3º parâmetro TRUE).
    ROLLBACK TO sp_<nome_procedure>;
    raise_application_error(-20106,
      'Violação de unicidade em ' || lc_nome_unidade, TRUE);

  WHEN OTHERS THEN
    -- Desfaz só o trabalho desta unidade; o do chamador fica intacto.
    ROLLBACK TO sp_<nome_procedure>;
    logger.log_error('Erro em ' || lc_nome_unidade, lc_nome_unidade);
    RAISE;  -- preserva código e pilha do erro original
END <nome_procedure>;


--==============================================================================
-- B. Ponto de entrada — DONO DA TRANSAÇÃO
--
-- Ex.: procedure chamada por job do DBMS_SCHEDULER ou script de carga.
-- Só aqui há COMMIT e ROLLBACK total. Documente a política escolhida
-- (tudo-ou-nada, ou commit por item como abaixo).
--==============================================================================

PROCEDURE <nome_job> IS
  lc_nome_unidade CONSTANT VARCHAR2(60) := gc_nome_pacote || '.<nome_job>';

  TYPE t_lista_ids IS TABLE OF NUMBER INDEX BY PLS_INTEGER;
  l_ids t_lista_ids;
BEGIN
  -- Lê os IDs antes de processar: sem fetch através de COMMIT (ORA-01555).
  SELECT id BULK COLLECT INTO l_ids
    FROM tabela_destino
   WHERE status = 'PENDENTE';

  FOR i IN 1 .. l_ids.COUNT LOOP
    BEGIN
      <nome_procedure>(p_param1 => l_ids(i));
      COMMIT;                      -- política: commit por item
    EXCEPTION
      WHEN OTHERS THEN
        ROLLBACK;                  -- o dono decide desfazer o item
        logger.log_error('Item ' || l_ids(i) || ' falhou em ' || lc_nome_unidade,
                         lc_nome_unidade);
        -- segue para o próximo item (decisão do dono, documentada acima)
    END;
  END LOOP;
EXCEPTION
  WHEN OTHERS THEN
    ROLLBACK;
    logger.log_error('Erro em ' || lc_nome_unidade, lc_nome_unidade);
    RAISE;
END <nome_job>;
