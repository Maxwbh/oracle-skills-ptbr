--==============================================================================
-- Template: APEX Dynamic Action
--
-- Compatibilidade: versão padrão APEX 26.2; padrões base de Dynamic Actions
--   valem em 24.2/26.1/26.2. Itens Select One/Select Many existem desde 24.1;
--   partials client-side de Template Components desde o 26.1.
--   Matriz: references/apex-version-matrix-ptbr.md
--
-- Uso: copie estes blocos no APEX Builder para configurar Dynamic Actions
--      comuns. Substitua marcadores <P1_ITEM> pelos items reais da página.
--
-- Estrutura típica de DA:
--   When (Event):           Change of P1_CUSTOMER_ID
--   Affected Elements:      P1_CUSTOMER_NAME, P1_TOTAL_DUE
--   True Action 1:          Execute PL/SQL Code
--   True Action 2:          Execute JavaScript Code
--==============================================================================


--==============================================================================
-- VARIANTE 1: PL/SQL que retorna valores para items
-- 
-- Configuração no APEX:
--   Event:              Change
--   Selection Type:     Item(s)
--   Item(s):            P10_ID_CLIENTE
--   True Action:        Execute PL/SQL Code
--   Items to Submit:    P10_ID_CLIENTE
--   Items to Return:    P10_NOME_CLIENTE, P10_TOTAL_DEVIDO
--==============================================================================

DECLARE
  l_nome_unidade CONSTANT VARCHAR2(60) := 'PAGE_10_DA_CUSTOMER_CHANGED';
  
  l_nome_cliente VARCHAR2(200);
  l_total_devido     NUMBER;
BEGIN
  -- Busca dados do cliente selecionado
  SELECT nome,
         NVL((SELECT SUM(valor)
                FROM faturas
               WHERE id_cliente = c.id
                 AND status = 'PENDENTE'), 0)
    INTO l_nome_cliente,
         l_total_devido
    FROM clientes c
   WHERE c.id = :P10_ID_CLIENTE;

  -- Atribui aos items que serão devolvidos ao client
  :P10_NOME_CLIENTE := l_nome_cliente;
  :P10_TOTAL_DEVIDO     := l_total_devido;
EXCEPTION
  WHEN NO_DATA_FOUND THEN
    -- Customer não existe (improvável vindo de LOV, mas defensive)
    :P10_NOME_CLIENTE := NULL;
    :P10_TOTAL_DEVIDO     := 0;
  WHEN OTHERS THEN
    -- DA não deve quebrar UI silenciosamente — log + raise
    APEX_DEBUG.error('Erro em ' || l_nome_unidade || ': ' || SQLERRM);
    raise_application_error(-20999,
      'Erro ao buscar dados do cliente: ' || SQLERRM);
END;


--==============================================================================
-- VARIANTE 2: JavaScript de reação após PL/SQL
--
-- Configuração:
--   True Action 2 (após Variante 1): Execute JavaScript Code
--==============================================================================

/*
// Acessa items que foram preenchidos pelo PL/SQL anterior
var customerName = apex.item('P10_NOME_CLIENTE').getValue();
var totalDue     = parseFloat(apex.item('P10_TOTAL_DEVIDO').getValue() || 0);

// Atualiza display formatado
$('#display-cliente-nome').text(customerName);
$('#display-total-due').text(
  totalDue.toLocaleString('pt-BR', { 
    style: 'currency', 
    currency: 'BRL' 
  })
);

// Habilita ou desabilita botão de pagamento conforme valor
if (totalDue > 0) {
  apex.item('P10_BTN_PAGAR').enable();
  $('#total-due').addClass('has-debt');
} else {
  apex.item('P10_BTN_PAGAR').disable();
  $('#total-due').removeClass('has-debt');
}
*/


--==============================================================================
-- VARIANTE 3: Confirmação antes de DELETE (DA com condição)
--
-- Configuração:
--   Event:                 Click
--   Selection Type:        jQuery Selector
--   jQuery Selector:       .delete-row
--   True Action 1:         Confirm
--     Text:                Tem certeza que deseja excluir este registro?
--   True Action 2:         Execute PL/SQL Code (com Stop Execution on Error)
--==============================================================================

-- ATENÇÃO: em Dynamic Action "Execute Server-side Code" NÃO existe x01/G_X01 —
-- esses parâmetros são exclusivos de apex.server.process (AJAX Callback).
-- Em DA, o valor chega via item listado em "Items to Submit" (ex.: hidden
-- P10_ID_REGISTRO populado por uma action "Set Value" anterior ou pelo JS
-- que leu o data-id do botão clicado).
DECLARE
  l_id NUMBER := TO_NUMBER(:P10_ID_REGISTRO);  -- Items to Submit: P10_ID_REGISTRO
BEGIN
  -- Soft delete (recomendado para auditoria)
  UPDATE registros
     SET excluido_em  = SYSDATE,
         excluido_por = :APP_USER,
         ativo        = 'N'
   WHERE id = l_id;

  IF SQL%ROWCOUNT = 0 THEN
    raise_application_error(-20101,
      'Registro não encontrado para exclusão: ID ' || l_id);
  END IF;

  -- Sem COMMIT explícito: o APEX gerencia a transação do server-side code.
EXCEPTION
  WHEN OTHERS THEN
    raise_application_error(-20999,
      'Erro ao excluir: ' || SQLERRM);
END;


--==============================================================================
-- VARIANTE 4: Refresh de Region após operação
--
-- Configuração:
--   True Action (após PL/SQL):  Refresh
--   Selection Type:             Region
--   Region:                     Lista de Registros
--==============================================================================

-- Não há código PL/SQL — basta configurar a action "Refresh" no DA Builder.
-- Mas o report precisa ter "Page Items to Submit" configurado para que filtros
-- de pesquisa sejam respeitados no refresh.
