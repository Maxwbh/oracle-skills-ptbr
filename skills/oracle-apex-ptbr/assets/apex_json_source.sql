--==============================================================================
-- Template: JSON Sources em APEX 24.2 (Shared Component)
--
-- JSON Sources são um novo tipo de Shared Component introduzido em APEX 24.2.
-- Permitem criar Forms, Reports, Faceted Search, etc. diretamente sobre:
--   - Tabelas com coluna do tipo JSON (suportado em 19c+)
--   - Duality Views (apenas 23ai)
--   - JSON Collection Tables/Views (apenas 23ai)
--
-- Vantagem sobre REST Data Source: sem rede, transação ACID, single source of
-- truth. Vantagem sobre tabela relacional clássica: schema flexível por linha.
--
-- Este template cobre o caminho 19c (tabela + coluna JSON). Para 23ai com
-- Duality View, ver doc oficial 24.2 §"Managing JSON Sources".
--==============================================================================

--==============================================================================
-- 1. Tabela de exemplo: documentos com payload JSON
--==============================================================================

CREATE TABLE documentos_json (
  id              NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  tipo_documento  VARCHAR2(30)  NOT NULL,
  payload         JSON          NOT NULL,
  -- Coluna virtual indexável (path conhecido) — útil para WHERE/ORDER BY
  numero_processo VARCHAR2(50)  GENERATED ALWAYS AS (JSON_VALUE(payload, '$.numero_processo')),
  criado_em       TIMESTAMP DEFAULT SYSTIMESTAMP,
  criado_por      VARCHAR2(50)  DEFAULT USER,
  -- Garante que o payload é JSON válido (em 19c usa IS JSON; 21c+ tem tipo JSON nativo)
  CONSTRAINT ck_documentos_json CHECK (payload IS JSON)
);

-- Índice JSON Search Index (multivalue) — acelera JSON_EXISTS / JSON_VALUE
CREATE SEARCH INDEX idx_documentos_json_search ON documentos_json (payload)
  FOR JSON;

--==============================================================================
-- 2. Popular com dados de exemplo
--==============================================================================

INSERT INTO documentos_json (tipo_documento, payload) VALUES (
  'FATURA',
  JSON_OBJECT(
    'numero_processo' VALUE 'PROC-2026-0042',
    'cliente'         VALUE JSON_OBJECT('id' VALUE 1001, 'nome' VALUE 'Empresa Alfa'),
    'itens'           VALUE JSON_ARRAY(
                              JSON_OBJECT('desc' VALUE 'Servico A', 'valor' VALUE 1500),
                              JSON_OBJECT('desc' VALUE 'Servico B', 'valor' VALUE 800)
                            ),
    'total'           VALUE 2300
  )
);

COMMIT;

--==============================================================================
-- 3. Configurar como JSON Source no App Builder (passo declarativo)
--
-- No Page Designer:
--   1. Shared Components > JSON Sources > Create
--   2. Source Type: Local Database Table with JSON Column
--   3. Table: DOCUMENTOS_JSON
--   4. JSON Column: PAYLOAD
--   5. APEX "infere" o data profile da coluna JSON automaticamente
--      (lê uma amostra das linhas e detecta os campos)
--   6. Edite o data profile se necessário: ajustar tipos, renomear, esconder.
--
-- Depois de criada, a JSON Source aparece como "Source" disponível em:
--   - Classic Report
--   - Interactive Report
--   - Faceted Search
--   - Form region
--   - Cards region
--==============================================================================

--==============================================================================
-- 4. Quando preferir JSON Source vs tabela relacional clássica
--==============================================================================

/*
USE JSON SOURCE QUANDO:
  - Schema do payload muda com frequência (não vale alterar tabela)
  - Documentos vêm de fora (NFe, integração com sistema externo)
  - Cada linha tem campos opcionais distintos
  - Precisa de array aninhado sem normalizar em tabela filha
  - Vai integrar com 23ai Duality Views no futuro

USE TABELA RELACIONAL QUANDO:
  - Schema é estável e bem conhecido
  - Queries fazem muitos JOINs com outras tabelas
  - Volume é alto e queries dependem de índices em colunas específicas
  - Equipe tem mais familiaridade com SQL clássico que JSON path
*/

--==============================================================================
-- 5. Queries úteis para JSON em PL/SQL
--==============================================================================

-- Extrair campo escalar
SELECT id,
       JSON_VALUE(payload, '$.total' RETURNING NUMBER) AS total
  FROM documentos_json;

-- Extrair sub-objeto
SELECT id,
       JSON_QUERY(payload, '$.cliente') AS cliente_json
  FROM documentos_json;

-- Iterar array (JSON_TABLE)
SELECT d.id,
       jt.desc,
       jt.valor
  FROM documentos_json d,
       JSON_TABLE(d.payload, '$.itens[*]'
         COLUMNS (
           desc   VARCHAR2(100) PATH '$.desc',
           valor  NUMBER        PATH '$.valor'
         )
       ) jt
 WHERE d.id = 1;

-- Filtro por existência de path
SELECT id
  FROM documentos_json
 WHERE JSON_EXISTS(payload, '$.cliente.nome');

--==============================================================================
-- 6. Anti-patterns
--==============================================================================

/*
ANTI-PATTERN 1: Coluna VARCHAR2 com JSON em string
  -- RUIM: sem validação, sem search index, sem JSON_VALUE direto
  payload VARCHAR2(4000)

  -- BOM: tipo JSON nativo (21c+) ou VARCHAR2/CLOB + CHECK IS JSON
  payload JSON                                       -- 21c+
  payload CLOB CHECK (payload IS JSON)               -- 19c

ANTI-PATTERN 2: APEX Form direto sobre coluna JSON sem JSON Source
  -- RUIM: usuário edita JSON cru em textarea, valida só no submit
  -- BOM: declarar JSON Source — APEX gera form com itens por campo

ANTI-PATTERN 3: Loop PL/SQL para parsear array
  -- RUIM
  FOR i IN 0 .. JSON_VALUE(payload, '$.itens.size()') LOOP
    l_valor := JSON_VALUE(payload, '$.itens[' || i || '].valor');
  END LOOP;

  -- BOM: JSON_TABLE com FOR loop em cursor (single query)
  FOR r IN (SELECT * FROM JSON_TABLE(payload, '$.itens[*]'
              COLUMNS (valor NUMBER PATH '$.valor'))) LOOP
    -- r.valor disponível
  END LOOP;
*/
