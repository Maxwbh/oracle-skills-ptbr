--==============================================================================
-- APEX_JSON — construção e parsing de JSON em PL/SQL
--
-- Pacote padrão APEX para trabalhar com JSON sem depender de PL/JSON externo.
-- Funciona em qualquer schema com EXECUTE em APEX_JSON (default no workspace
-- schema; conceder grant para outros: GRANT EXECUTE ON apex_json TO meu_app).
--
-- Comparação com alternativas:
--   APEX_JSON          — streaming + parse hierárquico; ótimo para construir e ler
--   JSON_OBJECT/ARRAY  — SQL nativo (12c+); ótimo dentro de SELECT
--   JSON_TABLE         — projeção tabular de JSON; ótimo para "transformar em tabela"
--   PL/JSON externo    — legado; evitar em código novo
--==============================================================================

--==============================================================================
-- 1. Construir JSON — abordagem streaming
--==============================================================================

-- Sem parâmetros: imprime via HTP.prn (saída direta para HTTP response).
-- Em On-Demand Process / ORDS handler, isso é o caminho default.

DECLARE
  l_total NUMBER := 1500.50;
BEGIN
  APEX_JSON.open_object;                          -- {
    APEX_JSON.write('id',        12345);          --   "id": 12345,
    APEX_JSON.write('descricao', 'Fatura #42');   --   "descricao": "Fatura #42",
    APEX_JSON.write('total',     l_total);        --   "total": 1500.5,
    APEX_JSON.write('paga',      TRUE);           --   "paga": true,
    APEX_JSON.write('vencimento', DATE '2026-08-15');  -- ISO 8601

    APEX_JSON.open_array('itens');                --   "itens": [
      APEX_JSON.open_object;
        APEX_JSON.write('desc',  'Serviço A');
        APEX_JSON.write('valor', 800);
      APEX_JSON.close_object;
      APEX_JSON.open_object;
        APEX_JSON.write('desc',  'Serviço B');
        APEX_JSON.write('valor', 700.50);
      APEX_JSON.close_object;
    APEX_JSON.close_array;                        --   ],

    APEX_JSON.write_null('observacao');           --   "observacao": null
  APEX_JSON.close_object;                         -- }
END;
/

-- Resultado típico (formatado):
-- {
--   "id": 12345,
--   "descricao": "Fatura #42",
--   "total": 1500.5,
--   "paga": true,
--   "vencimento": "2026-08-15T00:00:00Z",
--   "itens": [
--     {"desc": "Serviço A", "valor": 800},
--     {"desc": "Serviço B", "valor": 700.5}
--   ],
--   "observacao": null
-- }

--==============================================================================
-- 2. Construir JSON em CLOB (para insert, retorno de function, etc.)
--==============================================================================

DECLARE
  l_clob CLOB;
BEGIN
  APEX_JSON.initialize_clob_output(p_cache => TRUE);  -- bufferiza em CLOB

  APEX_JSON.open_object;
    APEX_JSON.write('mensagem', 'OK');
    APEX_JSON.write('timestamp', SYSTIMESTAMP);
  APEX_JSON.close_object;

  l_clob := APEX_JSON.get_clob_output;
  APEX_JSON.free_output;

  -- Agora l_clob tem o JSON completo
  INSERT INTO log_eventos_json (payload) VALUES (l_clob);
  COMMIT;
END;
/

--==============================================================================
-- 3. JSON a partir de cursor (mais limpo que loop manual)
--==============================================================================

DECLARE
  l_cur SYS_REFCURSOR;
BEGIN
  OPEN l_cur FOR
    SELECT id, descricao, valor, data_vencimento
      FROM faturas
     WHERE status = 'PENDENTE';

  APEX_JSON.write(l_cur);
  -- Imprime: [{"ID":1,"DESCRICAO":"...","VALOR":100,"DATA_VENCIMENTO":"..."},...]
  -- Atenção: por default os nomes ficam MAIÚSCULOS (nome da coluna SQL).
  -- Para nomes camelCase, faça alias na query: SELECT id AS "id", ...
END;
/

--==============================================================================
-- 4. Parsing de JSON recebido
--==============================================================================

DECLARE
  l_json   CLOB := q'#{
    "cliente": {
      "id": 1001,
      "nome": "Empresa Alfa",
      "ativo": true
    },
    "itens": [
      {"desc": "A", "valor": 100},
      {"desc": "B", "valor": 200},
      {"desc": "C", "valor": 50}
    ],
    "data_emissao": "2026-05-10"
  }#';
  l_count NUMBER;
BEGIN
  APEX_JSON.parse(l_json);

  -- Escalar simples
  DBMS_OUTPUT.put_line('Cliente ID: ' || APEX_JSON.get_number('cliente.id'));
  DBMS_OUTPUT.put_line('Nome: '       || APEX_JSON.get_varchar2('cliente.nome'));
  DBMS_OUTPUT.put_line('Ativo: ' ||    -- BOOLEAN não concatena direto
    CASE WHEN APEX_JSON.get_boolean('cliente.ativo') THEN 'sim' ELSE 'não' END);
  DBMS_OUTPUT.put_line('Emissão: '    || APEX_JSON.get_date('data_emissao'));

  -- Verificar existência sem falhar
  IF APEX_JSON.does_exist('cliente.email') THEN
    DBMS_OUTPUT.put_line('Email: ' || APEX_JSON.get_varchar2('cliente.email'));
  END IF;

  -- Iterar array
  l_count := APEX_JSON.get_count('itens');
  DBMS_OUTPUT.put_line('Total de itens: ' || l_count);

  FOR i IN 1..l_count LOOP
    DBMS_OUTPUT.put_line(
      'Item ' || i || ': ' ||
      APEX_JSON.get_varchar2(p_path => 'itens[%d].desc', p0 => i) ||
      ' = ' ||
      APEX_JSON.get_number  (p_path => 'itens[%d].valor', p0 => i)
    );
  END LOOP;
END;
/

--==============================================================================
-- 5. Tipos disponíveis em get_*
--==============================================================================

/*
  APEX_JSON.get_varchar2 (p_path, p0..p9)  → VARCHAR2
  APEX_JSON.get_number   (p_path, ...)     → NUMBER
  APEX_JSON.get_date     (p_path, ...)     → DATE      (ISO 8601 input)
  APEX_JSON.get_timestamp(p_path, ...)     → TIMESTAMP
  APEX_JSON.get_boolean  (p_path, ...)     → BOOLEAN
  APEX_JSON.get_clob     (p_path, ...)     → CLOB      (extrai sub-árvore como JSON string)
  APEX_JSON.get_count    (p_path, ...)     → NUMBER    (elementos de array)
  APEX_JSON.does_exist   (p_path, ...)     → BOOLEAN

  Path syntax:
    - "cliente.id"                  → caminhada de objetos
    - "itens[3].valor"              → índice de array (1-based!)
    - "itens[%d].valor" + p0 => i   → índice dinâmico

  IMPORTANTE: array index em APEX_JSON é 1-based (SQL style), não 0-based (JS style).
*/

--==============================================================================
-- 6. JSON inválido — tratamento
--==============================================================================

DECLARE
  l_json_invalido CLOB := '{"erro": faltando aspas}';
BEGIN
  APEX_JSON.parse(l_json_invalido);
EXCEPTION
  WHEN OTHERS THEN
    -- ORA-20987 (APEX) ou erro de parse JSON
    APEX_DEBUG.error('JSON inválido: ' || SQLERRM);
    -- Trate o caso: response 400, default value, ou re-raise
END;
/

-- Validar sem exception no fluxo principal: use a condição SQL nativa IS JSON
DECLARE
  l_clob   CLOB := '{"ok": true}';
  l_valido VARCHAR2(1);
BEGIN
  SELECT CASE WHEN l_clob IS JSON THEN 'S' ELSE 'N' END
    INTO l_valido
    FROM dual;
END;
/

--==============================================================================
-- 7. Boas práticas
--==============================================================================

/*
RECOMENDAÇÃO 1: Em ORDS handler, prefira APEX_JSON em vez de concatenar string
  -- RUIM: vulnerável a injection se l_nome tem aspas
  HTP.prn('{"nome":"' || l_nome || '"}');

  -- BOM: APEX_JSON escapa automaticamente
  APEX_JSON.open_object;
  APEX_JSON.write('nome', l_nome);
  APEX_JSON.close_object;

RECOMENDAÇÃO 2: Para query SQL retornando JSON, prefira JSON_OBJECT/JSON_ARRAYAGG
  SELECT JSON_OBJECT(
           'id' VALUE id,
           'desc' VALUE descricao,
           'itens' VALUE (SELECT JSON_ARRAYAGG(...) FROM ...)
         )
    FROM faturas;
  -- Single statement, otimizável, sem PL/SQL no caminho

RECOMENDAÇÃO 3: Iniciar output explicitamente em batches grandes
  APEX_JSON.initialize_output(
    p_http_header => FALSE,         -- evita Content-Type automático em job
    p_indent      => 0              -- minified — economiza bytes
  );
*/

--==============================================================================
-- 8. Anti-patterns
--==============================================================================

/*
ANTI-PATTERN 1: Concatenar JSON em string
  l_json := '{"nome":"' || p_nome || '"}';     -- ❌ injection, escape errado
  → use APEX_JSON.open_object/write

ANTI-PATTERN 2: Parsear array com índice 0
  APEX_JSON.get_varchar2('itens[0].desc')      -- ❌ 1-based em APEX_JSON
  → use itens[1]..itens[N]

ANTI-PATTERN 3: Ler scalar sem checar existência
  l_email := APEX_JSON.get_varchar2('email');  -- retorna NULL se não existe;
                                                 -- silencioso, pode mascarar bug
  → use does_exist antes em paths opcionais

ANTI-PATTERN 4: Não liberar buffer CLOB
  APEX_JSON.initialize_clob_output(...);
  ... lógica ...
  l_clob := APEX_JSON.get_clob_output;
  -- esqueceu free_output → vaza PGA
  → SEMPRE APEX_JSON.free_output após uso
*/
