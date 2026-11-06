--==============================================================================
-- APEX_UTIL — manipulação de session state e utilidades do runtime
--
-- Pacote PL/SQL oficial APEX para ler/escrever items, manipular cache de
-- sessão, gerar URLs com checksum, e operações administrativas básicas.
--
-- Referência completa: https://docs.oracle.com/en/database/oracle/apex/24.2/aeapi/
--==============================================================================

--==============================================================================
-- 1. Ler / escrever session state
--==============================================================================

-- Ler value de um item (equivalente a :P10_ITEM em contexto APEX)
DECLARE
  l_id_cliente NUMBER;
BEGIN
  l_id_cliente := APEX_UTIL.get_session_state('P10_ID_CLIENTE');
  -- Diferença vs :P10_ID_CLIENTE: get_session_state funciona em contexto
  -- onde a sintaxe bind não está disponível (jobs, background, ORDS).
END;
/

-- Escrever value (raramente necessário fora de Page Process)
BEGIN
  APEX_UTIL.set_session_state(
    p_name  => 'P10_STATUS',
    p_value => 'PROCESSADO'
  );
END;
/

-- Diferença essencial:
--   :P10_STATUS := 'X';                          -- PL/SQL inline em APEX Process
--   APEX_UTIL.set_session_state('P10_STATUS','X') -- chamável de QUALQUER contexto
-- A primeira só funciona em runtime de Page; a segunda também em job/background.

--==============================================================================
-- 2. Limpar / purgar session state
--==============================================================================

-- Limpar cache de uma página inteira (Application > Utilities > Session State)
BEGIN
  APEX_UTIL.clear_page_cache(p_page => 10);
END;
/

-- Limpar cache do aplicativo inteiro (uso raro, geralmente em logout)
BEGIN
  APEX_UTIL.clear_app_cache(p_app => :APP_ID);
END;
/

-- Purgar session state de TODAS as sessões — só em deploy/admin
BEGIN
  APEX_UTIL.purge_session_state(p_app => :APP_ID);
END;
/

--==============================================================================
-- 3. Geração de URLs com checksum (link bookmarkable seguro)
--==============================================================================

-- URLs APEX precisam de checksum quando passam valores de items que tem
-- Session State Protection. Sem checksum: redireciona para "Invalid URL".

DECLARE
  l_url VARCHAR2(4000);
BEGIN
  l_url := APEX_UTIL.prepare_url(
    p_url            => 'f?p=' || :APP_ID || ':20:' || :APP_SESSION
                         || '::NO::P20_ID_FATURA:12345',
    p_checksum_type  => 'SESSION'    -- ou 'PRIVATE_BOOKMARK' / 'PUBLIC_BOOKMARK'
  );

  -- Tipos de checksum:
  --   SESSION           — só vale na sessão atual
  --   PRIVATE_BOOKMARK  — vale para o usuário logado (multi-sessão)
  --   PUBLIC_BOOKMARK   — vale para qualquer usuário (link público)
END;
/

--==============================================================================
-- 4. Contar cliques (URL tracking)
--==============================================================================

-- Para links externos onde se quer medir clique-trough:
DECLARE
  l_url VARCHAR2(4000);
BEGIN
  l_url := APEX_UTIL.count_click(
    p_url  => 'https://parceiro.com/produto/42',
    p_cat  => 'BANNER_HOME',               -- categoria do clique
    p_id   => :P1_BANNER_ID,
    p_user => :APP_USER
  );
  -- Parâmetro opcional p_company (NUMBER) recebe o workspace ID quando se
  -- quer segregar cliques por workspace. Não existe p_workspace.
  -- l_url é a URL "envelopada" que registra o clique antes de redirecionar.
  -- Renderize ela no HREF do link.
END;
/

-- Consulta dos cliques registrados:
SELECT category, url, click_date, application_user, workspace
  FROM apex_workspace_clicks
 WHERE category = 'BANNER_HOME'
 ORDER BY click_date DESC;

--==============================================================================
-- 5. Manipular usuários APEX (workspace users — auth Application Express)
--
-- Use APENAS se a Authentication Scheme é "Application Express Accounts".
-- Para Custom/SSO/OAuth, ver apex_authentication_custom.sql.
--==============================================================================

-- Criar usuário
BEGIN
  APEX_UTIL.create_user(
    p_user_name        => 'joao.silva',
    p_first_name       => 'João',
    p_last_name        => 'Silva',
    p_description      => 'Analista de TI',
    p_email_address    => 'joao.silva@exemplo.com.br',
    p_web_password     => 'TempPass123!',
    p_change_password_on_first_use => 'Y',
    p_allow_access_to_schemas      => 'MEU_APP'
  );
END;
/

-- Resetar senha (admin)
BEGIN
  APEX_UTIL.set_workspace(p_workspace => 'MEU_WORKSPACE');
  APEX_UTIL.reset_pw(
    p_user => 'joao.silva',
    p_msg  => 'Sua senha foi resetada. Faça login com a temporária.'
  );
END;
/

-- Travar / destravar conta
BEGIN
  APEX_UTIL.lock_account(p_user_name => 'joao.silva');
  -- APEX_UTIL.unlock_account(p_user_name => 'joao.silva');
END;
/

--==============================================================================
-- 6. APEX_UTIL.get_username_by_userid e variações
--==============================================================================

-- Quando se tem o ID interno mas precisa do nome:
DECLARE
  l_nome VARCHAR2(100);
BEGIN
  l_nome := APEX_UTIL.get_username(p_userid => 12345);
  -- Mais usado em apps multi-workspace ou com auditoria histórica
END;
/

--==============================================================================
-- 7. Padrões de uso
--==============================================================================

/*
PADRÃO A: Background process precisa do usuário APEX que disparou

  -- Job de scheduler não tem :APP_USER (rodando como schema owner)
  PROCEDURE processar_assincrono(p_id_job NUMBER, p_app_user VARCHAR2) IS
    l_scope VARCHAR2(60) := 'BG.PROC_ASYNC';
  BEGIN
    -- Setar contexto para auditoria via APEX_UTIL
    APEX_UTIL.set_session_state('CLIENT_INFO', p_app_user);
    DBMS_SESSION.set_identifier(p_app_user);  -- USERENV.CLIENT_IDENTIFIER
    -- ... lógica
  END;

PADRÃO B: Mensagem de sucesso após Process (já no SKILL.md APEX, lembrando)

  APEX_APPLICATION.g_print_success_message :=
    '<span class="t-Icon icon-check"></span> Fatura salva com sucesso';

PADRÃO C: URL absoluta para envio por e-mail (precisa checksum)

  l_url := APEX_UTIL.prepare_url(
    p_url           => 'f?p=' || :APP_ID || ':30:0::NO::P30_TOKEN:' || l_token,
    p_checksum_type => 'PUBLIC_BOOKMARK'
  );
  -- Anexar APEX_INSTANCE_ADMIN.get_parameter('IMAGE_PREFIX') ou setting do app
*/

--==============================================================================
-- 8. Anti-patterns
--==============================================================================

/*
ANTI-PATTERN 1: Usar :ITEM em job de scheduler
  -- RUIM: :ITEM só funciona em contexto APEX runtime
  BEGIN
    UPDATE faturas SET status = 'X' WHERE id = :P10_ID;  -- ❌ no job
  END;

  -- BOM: passar como parâmetro de procedure, ou usar APEX_UTIL no setup
  PROCEDURE atualizar(p_id NUMBER) IS BEGIN UPDATE...; END;

ANTI-PATTERN 2: Loop set_session_state em report grande
  -- RUIM: cada chamada é roundtrip e flush de cache
  FOR r IN (SELECT id FROM ...) LOOP
    APEX_UTIL.set_session_state('P10_TEMP', r.id);
    -- algum processamento
  END LOOP;

  -- BOM: use APEX_COLLECTION ou bulk processing

ANTI-PATTERN 3: URL sem checksum em link customizado
  -- RUIM: vai dar "Invalid URL" para items protegidos
  HTF.anchor('f?p='||:APP_ID||':20:'||:APP_SESSION||'::NO::P20_ID:'||l_id, l_label)

  -- BOM: APEX_UTIL.prepare_url envolvendo
*/
