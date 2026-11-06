--==============================================================================
-- APEX_APPLICATION — globals para AJAX callback e mensagens
--
-- O pacote APEX_APPLICATION (não confundir com APEX_APP) expõe variáveis
-- globais do request HTTP atual: g_x01..g_x20 (VARCHAR2), g_f01..g_f50
-- (arrays de checkbox/multi-select), g_print_success_message, etc.
--
-- Uso central: passar parâmetros para AJAX Callback (On-Demand Process) via
-- apex.server.process do JS, e receber arrays de checkbox marcados.
--==============================================================================

--==============================================================================
-- 1. AJAX Callback: ler g_x01..g_x20 vindo do JavaScript
--==============================================================================

-- No JavaScript da página (Dynamic Action ou inline):
/*
apex.server.process(
  'CALCULAR_DESCONTO',                        -- On-Demand Process name
  {
    x01: $v('P10_ID_CLIENTE'),                -- → APEX_APPLICATION.g_x01
    x02: $v('P10_VALOR_BRUTO'),               -- → g_x02
    x03: 'FIDELIDADE_2025'                    -- → g_x03
  },
  {
    dataType: 'text',
    success: function(pResultado) {
      $s('P10_VALOR_LIQUIDO', pResultado);
    }
  }
);
*/

-- No PL/SQL do On-Demand Process "CALCULAR_DESCONTO":
DECLARE
  l_id_cliente   NUMBER  := TO_NUMBER(APEX_APPLICATION.g_x01);
  l_valor_bruto  NUMBER  := TO_NUMBER(APEX_APPLICATION.g_x02);
  l_codigo_promo VARCHAR2(30) := APEX_APPLICATION.g_x03;
  l_desconto     NUMBER;
  l_liquido      NUMBER;
BEGIN
  -- Lógica de cálculo (idealmente em package, chamada daqui)
  desconto_pkg.calcular(
    p_id_cliente    => l_id_cliente,
    p_valor_bruto   => l_valor_bruto,
    p_codigo_promo  => l_codigo_promo,
    p_valor_liquido => l_liquido
  );

  -- Resposta vai como texto plano via HTP.prn
  HTP.prn(TO_CHAR(l_liquido, 'FM999G990D00', 'NLS_NUMERIC_CHARACTERS='',.'''));
END;

-- Para resposta JSON estruturada (mais comum):
DECLARE
  l_id_cliente NUMBER := TO_NUMBER(APEX_APPLICATION.g_x01);
BEGIN
  APEX_JSON.open_object;
  APEX_JSON.write('id_cliente', l_id_cliente);
  APEX_JSON.write('desconto',   l_desconto);
  APEX_JSON.write('liquido',    l_liquido);
  APEX_JSON.close_object;
END;

--==============================================================================
-- 2. Receber arrays de checkbox (g_f01..g_f50)
--==============================================================================

-- Em Classic Report com APEX_ITEM.checkbox2, cada coluna vira um array
-- com índice numérico. Submit popula g_f01, g_f02, etc.

-- Query do region:
-- SELECT APEX_ITEM.checkbox2(1, id, 'CHECKED') AS marcar,  -- g_f01
--        APEX_ITEM.hidden(2, id)              AS id_hidden, -- g_f02
--        nome
--   FROM clientes;

-- Page Process "Salvar selecionados":
DECLARE
  l_ids_marcados APEX_APPLICATION_GLOBAL.vc_arr2 := APEX_APPLICATION.g_f01;
  l_ids_hidden   APEX_APPLICATION_GLOBAL.vc_arr2 := APEX_APPLICATION.g_f02;
  -- vc_arr2 é o tipo: TABLE OF VARCHAR2(32767) INDEX BY BINARY_INTEGER
BEGIN
  -- ATENÇÃO: g_f01 só contém os MARCADOS. Para iterar todos, use g_f02 (hidden).
  -- Padrão "marcados ∩ todos" não funciona direto — precisa cruzar manualmente.

  FOR i IN 1..l_ids_hidden.COUNT LOOP
    -- ID está em hidden array
    DECLARE
      l_id           NUMBER := TO_NUMBER(l_ids_hidden(i));
      l_foi_marcado  BOOLEAN := FALSE;
    BEGIN
      -- Checa se o ID está no array de marcados
      FOR j IN 1..l_ids_marcados.COUNT LOOP
        IF l_ids_marcados(j) = l_ids_hidden(i) THEN
          l_foi_marcado := TRUE;
          EXIT;
        END IF;
      END LOOP;

      IF l_foi_marcado THEN
        UPDATE clientes SET ativo = 'S' WHERE id = l_id;
      END IF;
    END;
  END LOOP;
END;

-- ALTERNATIVA mais limpa: usar APEX_COLLECTION antes do submit
-- (DA "checkbox change" popula collection 'SELECAO', Submit lê dela)

--==============================================================================
-- 3. Mensagem de sucesso/erro na próxima página
--==============================================================================

-- Success message (verde, no topo da página após redirect/branch)
BEGIN
  APEX_APPLICATION.g_print_success_message :=
    '<span class="t-Icon icon-check"></span> Fatura ' || :P10_NUMERO || ' salva.';
END;

-- Notification de erro (vermelho): NÃO existe g_error_message documentado.
-- Use APEX_ERROR.add_error — funciona em Process/Validation/Error Handling:
BEGIN
  APEX_ERROR.add_error(
    p_message          => 'Falha na integração externa.',
    p_display_location => APEX_ERROR.c_inline_in_notification
  );
END;

-- HTML é permitido (sanitize input antes!) — para mensagem simples, prefira
-- texto puro para não criar XSS vector.

--==============================================================================
-- 4. Trabalhar com upload single (APEX_APPLICATION_TEMP_FILES)
--==============================================================================

-- Em File Browse item P10_ARQUIVO, o conteúdo fica em
-- APEX_APPLICATION_TEMP_FILES (uma row por upload da sessão).

DECLARE
  l_blob       BLOB;
  l_filename   VARCHAR2(400);
  l_mime_type  VARCHAR2(100);
BEGIN
  SELECT blob_content, filename, mime_type
    INTO l_blob, l_filename, l_mime_type
    FROM APEX_APPLICATION_TEMP_FILES
   WHERE name = :P10_ARQUIVO;

  INSERT INTO documentos (id, conteudo, nome, mime_type)
  VALUES (documentos_seq.NEXTVAL, l_blob, l_filename, l_mime_type);

  -- Limpa o temp file (boa prática)
  DELETE FROM APEX_APPLICATION_TEMP_FILES WHERE name = :P10_ARQUIVO;
EXCEPTION
  WHEN NO_DATA_FOUND THEN
    APEX_ERROR.add_error(
      p_message          => 'Nenhum arquivo foi enviado',
      p_display_location => APEX_ERROR.c_inline_with_field_and_notif,
      p_page_item_name   => 'P10_ARQUIVO'
    );
END;

--==============================================================================
-- 5. Saída de download direto (sem region)
--==============================================================================

-- Em On-Demand Process chamado por window.location.href = '?process=DOWNLOAD':
DECLARE
  l_blob       BLOB;
  l_filename   VARCHAR2(400);
  l_mime_type  VARCHAR2(100);
  l_length     NUMBER;
BEGIN
  SELECT conteudo, nome, mime_type, DBMS_LOB.getlength(conteudo)
    INTO l_blob, l_filename, l_mime_type, l_length
    FROM documentos
   WHERE id = :P10_ID;

  OWA_UTIL.mime_header(l_mime_type, FALSE);
  HTP.p('Content-Length: ' || l_length);
  HTP.p('Content-Disposition: attachment; filename="' || l_filename || '"');
  OWA_UTIL.http_header_close;
  WPG_DOCLOAD.download_file(l_blob);
  APEX_APPLICATION.stop_apex_engine;            -- para o engine não renderizar página depois
END;

--==============================================================================
-- 6. Anti-patterns
--==============================================================================

/*
ANTI-PATTERN 1: Lógica grande em On-Demand Process inline
  -- RUIM: difícil manutenção, sem reuso, sem teste isolado
  DECLARE ... BEGIN
    [200 linhas de regras de negócio inline]
  END;

  -- BOM: package chamada do callback
  BEGIN
    desconto_pkg.calcular(...);
  END;

ANTI-PATTERN 2: Passar JSON cru em g_x01
  -- LIMITADO: g_x01 é VARCHAR2(32767) — JSON > 32k não cabe
  -- BOM: para payload grande, use p_clob_01:
  --   JS:     apex.server.process('PROC', { p_clob_01: jsonGrande })
  --   PL/SQL: l_clob := APEX_APPLICATION.g_clob_01;
  -- Alternativa: chunking em f01 (ver apex_blob_upload_download.sql)

ANTI-PATTERN 3: stop_apex_engine sem set header antes
  -- ERRADO: browser recebe response sem mime correto
  WPG_DOCLOAD.download_file(l_blob);
  APEX_APPLICATION.stop_apex_engine;

  -- BOM: SEMPRE OWA_UTIL.mime_header → HTP.p (extras) → http_header_close → download_file

ANTI-PATTERN 4: Confundir g_f01 (checkbox) com g_x01 (request param)
  - g_x01..g_x20: parâmetros nomeados de AJAX callback
  - g_f01..g_f50: arrays vindos de submit de form (checkbox, multi-select)
*/
