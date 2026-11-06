--==============================================================================
-- APEX_COLLECTION — tabela temporária por sessão (scratchpad)
--
-- COLLECTION é uma estrutura tabular vinculada à sessão APEX, com até 50
-- colunas tipadas (C001..C050 VARCHAR2, N001..N005 NUMBER, D001..D005 DATE,
-- BLOB001, CLOB001, XMLTYPE001). Ideal para:
--   - Carrinho de compras antes do checkout
--   - Multi-step wizard com rascunho
--   - Resultado de query externa (REST) que se quer paginar/filtrar localmente
--   - Working set de IDs selecionados em IR com checkbox em massa
--
-- COLLECTION NÃO substitui tabela permanente. Não é segura para dado crítico:
-- some quando sessão expira ou usuário desloga.
--==============================================================================

--==============================================================================
-- 1. Criar/recarregar collection a partir de query
--==============================================================================

BEGIN
  -- Cria se não existe; substitui se já existe (truncate + reload)
  APEX_COLLECTION.create_or_truncate_collection(
    p_collection_name => 'CARRINHO'
  );

  -- Popular a partir de query
  APEX_COLLECTION.create_collection_from_query(
    p_collection_name => 'CARRINHO',
    p_query           => 'SELECT id, descricao, preco, quantidade '
                      || '  FROM itens_carrinho_temp '
                      || ' WHERE id_sessao = ''' || :APP_SESSION || ''''
  );
END;
/

-- ATENÇÃO: query é VARCHAR2; concatenar :APP_SESSION acima é OK porque é
-- numérico controlado. Para valores de usuário, use a versão com binds:
BEGIN
  APEX_COLLECTION.create_collection_from_query_b (
    p_collection_name => 'CARRINHO',
    p_query           => 'SELECT id, descricao, preco, quantidade '
                      || '  FROM itens_carrinho_temp '
                      || ' WHERE id_sessao = :b1',
    p_names           => APEX_T_VARCHAR2('b1'),
    p_values          => APEX_T_VARCHAR2(:APP_SESSION)
  );
END;
/

--==============================================================================
-- 2. Adicionar member individual
--==============================================================================

DECLARE
  l_seq NUMBER;
BEGIN
  l_seq := APEX_COLLECTION.add_member(
    p_collection_name => 'CARRINHO',
    p_c001 => '12345',                        -- id do produto
    p_c002 => 'Notebook Acer Aspire 5',       -- descrição
    p_n001 => 3499.90,                        -- preço
    p_n002 => 1,                              -- quantidade
    p_d001 => SYSDATE                         -- adicionado em
  );
  -- l_seq é o seq_id atribuído (auto-incremento dentro da collection)
END;
/

-- Adicionar em massa (mais rápido que loop de add_member)
BEGIN
  APEX_COLLECTION.add_members(
    p_collection_name => 'CARRINHO',
    p_c001 => APEX_T_VARCHAR2('99', '100', '101'),
    p_c002 => APEX_T_VARCHAR2('Mouse', 'Teclado', 'Headset'),
    p_n001 => APEX_T_NUMBER(150, 250, 400)
  );
END;
/

--==============================================================================
-- 3. Consultar collection
--==============================================================================

-- Como tabela SQL (uso normal em region source)
SELECT seq_id,
       c001  AS id_produto,
       c002  AS descricao,
       n001  AS preco,
       n002  AS quantidade,
       n001 * n002 AS subtotal
  FROM apex_collections
 WHERE collection_name = 'CARRINHO'
 ORDER BY seq_id;

-- Em region APEX: Source = SQL Query com a query acima.
-- O usuário edita via IG; cada save chama update_member.

-- Total da collection (útil em validation/computation)
DECLARE
  l_total NUMBER;
BEGIN
  SELECT NVL(SUM(n001 * n002), 0)
    INTO l_total
    FROM apex_collections
   WHERE collection_name = 'CARRINHO';
END;
/

--==============================================================================
-- 4. Atualizar / remover member
--==============================================================================

-- Update (geralmente vindo de IG save process — APEX gera automaticamente)
BEGIN
  APEX_COLLECTION.update_member (
    p_collection_name => 'CARRINHO',
    p_seq             => 3,
    p_c001            => '12345',
    p_c002            => 'Notebook Acer Aspire 5',
    p_n001            => 3499.90,
    p_n002            => 2                     -- mudou quantidade
  );

  -- Update parcial — só uma coluna:
  APEX_COLLECTION.update_member_attribute (
    p_collection_name => 'CARRINHO',
    p_seq             => 3,
    p_attr_number     => 2,                    -- N002 = quantidade
    p_number_value    => 2
  );
END;
/

-- Remover
BEGIN
  APEX_COLLECTION.delete_member (
    p_collection_name => 'CARRINHO',
    p_seq             => 3
  );
END;
/

-- Limpar tudo
BEGIN
  APEX_COLLECTION.truncate_collection(p_collection_name => 'CARRINHO');
END;
/

-- Apagar a collection inteira (não volta com create_or_truncate)
BEGIN
  APEX_COLLECTION.delete_collection(p_collection_name => 'CARRINHO');
END;
/

--==============================================================================
-- 5. Checagem de existência
--==============================================================================

DECLARE
  l_existe BOOLEAN;
BEGIN
  l_existe := APEX_COLLECTION.collection_exists(p_collection_name => 'CARRINHO');
  IF NOT l_existe THEN
    APEX_COLLECTION.create_collection(p_collection_name => 'CARRINHO');
  END IF;
END;
/

--==============================================================================
-- 6. BLOB / CLOB em collection
--==============================================================================

-- Coluna BLOB001, CLOB001, XMLTYPE001 disponíveis (1 de cada):
DECLARE
  l_seq  NUMBER;
  l_blob BLOB;
BEGIN
  -- BLOB vem do upload (File Browse) via APEX_APPLICATION_TEMP_FILES
  SELECT blob_content
    INTO l_blob
    FROM apex_application_temp_files
   WHERE name = :P10_ARQUIVO;

  -- Setar BLOB no add (não disponível direto, usar 2-step)
  l_seq := APEX_COLLECTION.add_member(
    p_collection_name => 'UPLOADS',
    p_c001            => 'fatura_2026.pdf'
  );

  -- Overload dedicado para BLOB (sem p_attr_number — só existe BLOB001)
  APEX_COLLECTION.update_member_attribute (
    p_collection_name => 'UPLOADS',
    p_seq             => l_seq,
    p_blob_value      => l_blob
  );
END;
/

--==============================================================================
-- 7. Casos de uso típicos
--==============================================================================

/*
CASO 1: Carrinho antes do checkout
  - Página de catálogo adiciona items na collection 'CARRINHO'
  - Página de revisão mostra collection com totais
  - Page Process do botão "Finalizar" lê collection e insere em pedidos/itens_pedido

CASO 2: Multi-step wizard
  - Página 1: items C001..C010 da collection 'WIZARD' = dados pessoais
  - Página 2: items C011..C020 = endereço
  - Página 3: revisão lendo da collection
  - Submit final: persiste tabelas reais

CASO 3: Working set de IDs em IG/IR
  - Usuário marca checkbox em report (Apex_Item.checkbox2)
  - Submit popula collection 'SELECAO' com IDs marcados
  - Próxima página opera sobre a collection (gerar relatório, exportar, etc.)

CASO 4: Cache de chamada REST cara
  - Page Load chama API externa via APEX_WEB_SERVICE.make_rest_request
  - Resultado JSON parseado em collection 'API_CACHE'
  - Region exibe via SQL Query sobre apex_collections
  - Refresh manual via botão que re-chama API

CASO 5: Comparação antes/depois (audit visual)
  - Collection 'ORIGINAL' tem snapshot inicial
  - Usuário edita IG conectada a tabela real
  - Página de revisão mostra diff calculado em SQL
*/

--==============================================================================
-- 8. Anti-patterns
--==============================================================================

/*
ANTI-PATTERN 1: Collection como tabela permanente
  -- ERRADO: dado some quando sessão expira / usuário desloga
  APEX_COLLECTION.add_member('PEDIDOS_DO_DIA', ...)  -- ❌

  -- BOM: collection como rascunho, tabela real para persistir

ANTI-PATTERN 2: Loop FOR LOOP de add_member com >1000 items
  -- LENTO: cada add é roundtrip
  FOR r IN (SELECT ...) LOOP
    APEX_COLLECTION.add_member(...);
  END LOOP;

  -- BOM: create_collection_from_query (single statement)

ANTI-PATTERN 3: Compartilhar collection entre apps
  -- IMPOSSÍVEL: collection é por (sessão_id, app_id)
  -- Para compartilhar: use tabela permanente com (app_session, app_id) na PK

ANTI-PATTERN 4: Collection com 100+ colunas C001..C0NN
  -- Indica que deveria ser tabela real ou JSON em CLOB001
  -- Limite arquitetural: max 50 chars + 5 num + 5 date + 1 blob + 1 clob + 1 xml

ANTI-PATTERN 5: Não validar collection_exists antes de operar
  -- Erro silencioso se collection não existe ainda
  APEX_COLLECTION.add_member('NAO_EXISTE', ...);  -- ORA-20104

  -- BOM: collection_exists + create_collection se preciso
*/
