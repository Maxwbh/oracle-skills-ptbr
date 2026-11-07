--==============================================================================
-- APEX_ITEM — render manual de items em SQL Report (padrão legado)
--
-- Antes do Interactive Grid (5.1+) existia o padrão "Tabular Form" onde cada
-- coluna do report era renderizada como input editável usando APEX_ITEM.
-- O resultado vinha em arrays g_f01..g_f50 no submit.
--
-- ESCOPO ATUAL:
--   - Interactive Grid (IG) é o padrão moderno para edição em massa
--   - APEX_ITEM ainda é útil em casos onde IG não cabe:
--       * Classic Report customizado com 1-2 colunas editáveis
--       * Páginas legadas em migração gradual
--       * Cenários onde IG não suporta o tipo de item desejado
--       * Reports com lógica condicional complexa por linha
--
-- Documentação: https://docs.oracle.com/en/database/oracle/apex/24.2/aeapi/
--==============================================================================

--==============================================================================
-- 1. Tipos de items disponíveis em APEX_ITEM
--==============================================================================

/*
Função              | Render                  | Submit (array em)
--------------------|-------------------------|------------------
text                | <input type=text>       | g_fNN
textarea            | <textarea>              | g_fNN
password            | <input type=password>   | g_fNN
hidden              | <input type=hidden>     | g_fNN  ← usar para PK!
display_and_save    | label + hidden          | g_fNN
select_list         | <select> com options    | g_fNN
checkbox2           | <input type=checkbox>   | g_fNN  (só MARCADOS)
radiogroup          | <input type=radio>      | g_fNN
date_popup          | input + calendário      | g_fNN
popup_from_query    | popup LOV               | g_fNN
popupkey_from_query | popup LOV com 2 valores | g_fNN (display) + g_fNN+1 (key)
md5_hidden          | hidden + MD5 (checksum) | g_fNN  ← anti-tampering
*/

--==============================================================================
-- 2. Query típica de tabular form
--==============================================================================

-- Page Region: Classic Report
-- Source Type: SQL Query
-- Source:
SELECT APEX_ITEM.hidden       (1, id)                                AS id_h,
       APEX_ITEM.md5_hidden   (2, id, valor, status)                 AS check_h,
       APEX_ITEM.text         (3, descricao, 50, 100)                AS descricao,
       APEX_ITEM.text         (4, valor, 10, 12,
                               'class="apex-item-text right"')       AS valor,
       APEX_ITEM.select_list_from_query(
         5, status,
         'SELECT label, value FROM status_lov ORDER BY ord'
       )                                                              AS status,
       APEX_ITEM.checkbox2    (6, 'Y',
                               DECODE(ativo, 'S', 'CHECKED', NULL))   AS ativo,
       APEX_ITEM.date_popup   (7, NULL, data_vencimento, 'DD-MON-YYYY')
                                                                      AS vencimento
  FROM faturas
 WHERE status_processamento = 'PENDENTE';

-- IMPORTANTE: o primeiro parâmetro de cada função é o ÍNDICE DO ARRAY (1-50).
-- Use índices ÚNICOS e consistentes — o submit usa esses números pra montar
-- g_f01, g_f02, etc.

--==============================================================================
-- 3. Page Process — receber e processar
--==============================================================================

DECLARE
  l_ids       APEX_APPLICATION_GLOBAL.vc_arr2 := APEX_APPLICATION.g_f01;
  l_checks    APEX_APPLICATION_GLOBAL.vc_arr2 := APEX_APPLICATION.g_f02;
  l_descricao APEX_APPLICATION_GLOBAL.vc_arr2 := APEX_APPLICATION.g_f03;
  l_valor     APEX_APPLICATION_GLOBAL.vc_arr2 := APEX_APPLICATION.g_f04;
  l_status    APEX_APPLICATION_GLOBAL.vc_arr2 := APEX_APPLICATION.g_f05;
  -- g_f06 é checkbox (ativo)
  l_vencto    APEX_APPLICATION_GLOBAL.vc_arr2 := APEX_APPLICATION.g_f07;

  l_check_atual VARCHAR2(32);
  l_ativo_flag  VARCHAR2(1);
BEGIN
  FOR i IN 1..l_ids.COUNT LOOP

    -- Optimistic locking (lost update): re-calcular o checksum com os valores
    -- ATUAIS do banco e comparar com o md5_hidden capturado no render. Se
    -- diferente, OUTRA SESSÃO alterou a linha entre o render e o submit.
    -- (md5_value não existe — a função de comparação é APEX_ITEM.md5_checksum)
    SELECT APEX_ITEM.md5_checksum(id, valor, status)
      INTO l_check_atual
      FROM faturas
     WHERE id = TO_NUMBER(l_ids(i));

    IF l_check_atual <> l_checks(i) THEN
      raise_application_error(-20100,
        'Linha ' || i || ' foi alterada por outro usuário — recarregue a página');
    END IF;

    -- Checkbox: só os MARCADOS estão em g_f06 (preciso casar com hidden)
    l_ativo_flag := CASE
                      WHEN APEX_APPLICATION.g_f06.EXISTS(i) THEN 'S'
                      ELSE 'N'
                    END;
    -- ATENÇÃO: EXISTS(i) NÃO funciona como esperado se algumas linhas
    -- foram desmarcadas — index de g_f06 é o ID, não a ordem.
    -- Padrão mais robusto: cruzar como em apex_application_global.sql §2.

    UPDATE faturas
       SET descricao        = l_descricao(i),
           valor            = TO_NUMBER(l_valor(i)),
           status           = l_status(i),
           ativo            = l_ativo_flag,
           data_vencimento  = TO_DATE(l_vencto(i), 'DD-MON-YYYY'),
           atualizado_em    = SYSDATE,
           atualizado_por   = :APP_USER
     WHERE id = TO_NUMBER(l_ids(i));

  END LOOP;

  -- Sem COMMIT: o APEX é o dono da transação do request e a fecha ao final
  -- do processamento da página (convenção "APEX não comita" da suíte).

  APEX_APPLICATION.g_print_success_message :=
    l_ids.COUNT || ' linhas atualizadas';
END;

--==============================================================================
-- 4. md5_hidden — anti-tampering
--==============================================================================

-- O md5_hidden guarda um checksum dos valores da linha NO MOMENTO DO RENDER.
-- No submit, re-calcule com os valores ATUAIS do banco (APEX_ITEM.md5_checksum)
-- e compare. Se diferente, outra sessão alterou a linha (lost update).

-- Render (no SELECT do report):
-- APEX_ITEM.md5_hidden(2, valor, status, data_vencimento)

-- Verifica no submit (no Process):
-- SELECT APEX_ITEM.md5_checksum(valor, status, data_vencimento)
--   INTO l_check_atual FROM faturas WHERE id = ...;
-- IF l_check_atual <> l_checks(i) THEN raise_application_error(...);

-- NOTA: isso protege contra LOST UPDATE, não contra tampering de campos
-- editáveis (que o usuário altera legitimamente). Para hidden que NÃO deve
-- mudar (PK), valide autorização no banco e use Session State Protection.

--==============================================================================
-- 5. Quando MIGRAR para Interactive Grid
--==============================================================================

/*
USE IG QUANDO:
  - 5+ colunas editáveis
  - Quer save automático sem botão (auto-save)
  - Quer add row inline / delete inline
  - Quer copy/paste de planilha
  - Quer agrupamento, sort, filter sem PL/SQL custom

MANTENHA APEX_ITEM QUANDO:
  - 1-2 colunas editáveis em report majoritariamente read-only
  - Lógica de render condicional muito específica por linha
    (ex: tipo de item muda baseado em valor de outra coluna)
  - Migrar tudo agora não cabe — refatore página por página
  - Layout exótico que IG não permite

MAU SINAL:
  - Page com 10+ colunas APEX_ITEM em report = é hora de IG
  - Process com 500 linhas iterando g_f01..g_f30 = é hora de IG
*/

--==============================================================================
-- 6. Anti-patterns
--==============================================================================

/*
ANTI-PATTERN 1: Confiar em hidden input sem verificação
  -- Atacante abre DevTools, muda o ID em hidden input, submit
  -- Resultado: UPDATE em linha que ele não deveria acessar
  → valide autorização por linha no Process (o usuário pode editar ESTE id?)
  → use md5_hidden/md5_checksum para detectar lost update

ANTI-PATTERN 2: Usar índice duplicado de array
  SELECT APEX_ITEM.hidden(1, id),
         APEX_ITEM.text  (1, descricao)  -- ❌ índice 1 colide
  → cada coluna PRECISA de índice único 1-50

ANTI-PATTERN 3: Acessar g_fNN sem checar bounds
  l_valor := APEX_APPLICATION.g_f04(i);  -- ORA-22160 se não existe
  → use l_valor.EXISTS(i) ou g_f04.COUNT

ANTI-PATTERN 4: COMMIT explícito no Page Process
  -- O APEX é o dono da transação do request: o process não comita. COMMIT
  -- no meio quebra o "tudo ou nada" da página (se um process seguinte
  -- falhar, o que veio antes já foi gravado).

ANTI-PATTERN 5: Checkbox sem hidden complementar
  -- g_fNN (checkbox) só traz MARCADOS; sem g_fMM (hidden ID), não dá pra
  -- cruzar com a linha original
  → SEMPRE pareie checkbox com hidden(ID) na mesma linha
*/
