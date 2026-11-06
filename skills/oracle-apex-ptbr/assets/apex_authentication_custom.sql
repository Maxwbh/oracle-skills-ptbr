--==============================================================================
-- APEX Authentication — schemes customizados
--
-- APEX oferece schemes prontos (Application Express Accounts, Database Account,
-- LDAP, Social, SAML, Open ID Connect, HTTP Header Variable). Para integração
-- corporativa específica, use "Custom" scheme com função PL/SQL própria.
--
-- Este template cobre os pontos canônicos: authentication function, post-auth
-- callback, sentinel logout, session sharing entre apps.
--==============================================================================

--==============================================================================
-- 1. Custom Authentication Scheme — função de validação
--==============================================================================

-- Settings da Authentication Scheme (no APEX):
--   Type: Custom
--   Authentication Function Name: AUTH_PKG.validar_credenciais
--
-- Assinatura obrigatória: retorna BOOLEAN (TRUE=ok), p_username e p_password IN.

CREATE OR REPLACE PACKAGE auth_pkg AS

  FUNCTION validar_credenciais (
    p_username IN VARCHAR2,
    p_password IN VARCHAR2
  ) RETURN BOOLEAN;

  -- Post-Authentication Procedure do scheme: assinatura SEM parâmetros.
  -- O usuário autenticado está em apex_application.g_user.
  PROCEDURE post_authenticate;

  -- Chamar de um processo de logout customizado (também sem parâmetros).
  PROCEDURE pre_logout;

  FUNCTION sentinel_check RETURN BOOLEAN;
  -- Chamada em CADA request — use com cuidado (perf)

END auth_pkg;
/

CREATE OR REPLACE PACKAGE BODY auth_pkg AS

  gc_nome_pacote CONSTANT VARCHAR2(30) := 'AUTH_PKG';

  ----------------------------------------------------------------------------
  FUNCTION validar_credenciais (
    p_username IN VARCHAR2,
    p_password IN VARCHAR2
  ) RETURN BOOLEAN IS
    lc_nome_unidade CONSTANT VARCHAR2(60) := gc_nome_pacote || '.validar_credenciais';
    l_hash_armazenado VARCHAR2(64);
    l_hash_recebido   VARCHAR2(64);
    l_ativo           VARCHAR2(1);
    l_tentativas      NUMBER;
  BEGIN
    SELECT senha_hash, ativo, tentativas_falhas
      INTO l_hash_armazenado, l_ativo, l_tentativas
      FROM usuarios
     WHERE UPPER(login) = UPPER(p_username);

    -- Conta bloqueada por tentativas
    IF l_tentativas >= 5 THEN
      apex_debug.error(lc_nome_unidade || ': conta bloqueada para ' || p_username);
      RETURN FALSE;
    END IF;

    -- Conta inativa
    IF l_ativo <> 'S' THEN
      apex_debug.warn(lc_nome_unidade || ': conta inativa para ' || p_username);
      RETURN FALSE;
    END IF;

    -- Hash da senha recebida (SHA-256 + salt seria ideal; exemplo simples)
    l_hash_recebido := LOWER(RAWTOHEX(
      DBMS_CRYPTO.hash(UTL_RAW.cast_to_raw(p_password || ':SALT_FIXO_PARA_EXEMPLO'),
                       DBMS_CRYPTO.hash_sh256)
    ));

    IF l_hash_recebido = l_hash_armazenado THEN
      -- Sucesso: zera tentativas, registra último login
      UPDATE usuarios
         SET tentativas_falhas = 0,
             ultimo_login = SYSTIMESTAMP
       WHERE UPPER(login) = UPPER(p_username);
      COMMIT;
      RETURN TRUE;
    ELSE
      -- Falha: incrementa contador
      UPDATE usuarios
         SET tentativas_falhas = tentativas_falhas + 1
       WHERE UPPER(login) = UPPER(p_username);
      COMMIT;
      RETURN FALSE;
    END IF;

  EXCEPTION
    WHEN NO_DATA_FOUND THEN
      -- Não revele "usuário não existe" — mesma mensagem para "senha errada"
      apex_debug.info(lc_nome_unidade || ': usuário não encontrado ' || p_username);
      RETURN FALSE;
    WHEN OTHERS THEN
      apex_debug.error(lc_nome_unidade || ': erro inesperado - ' || SQLERRM);
      RETURN FALSE;
  END validar_credenciais;

  ----------------------------------------------------------------------------
  -- Post-Authentication Procedure (no scheme: Post-Authentication Procedure)
  --
  -- Roda DEPOIS de validar_credenciais retornar TRUE. Use para:
  --   - Carregar perfil, permissões em Application Items
  --   - Setar CLIENT_IDENTIFIER (importante para audit e VPD)
  --   - Log de auditoria de login
  ----------------------------------------------------------------------------
  PROCEDURE post_authenticate IS
    lc_nome_unidade CONSTANT VARCHAR2(60) := gc_nome_pacote || '.post_authenticate';
    l_username    VARCHAR2(255) := apex_application.g_user;
    l_id_usuario  NUMBER;
    l_perfil      VARCHAR2(50);
  BEGIN
    SELECT id, perfil
      INTO l_id_usuario, l_perfil
      FROM usuarios
     WHERE UPPER(login) = UPPER(l_username);

    -- Application Items setadas (visíveis em todas as páginas)
    APEX_UTIL.set_session_state('G_ID_USUARIO',  l_id_usuario);
    APEX_UTIL.set_session_state('G_PERFIL',      l_perfil);

    -- CLIENT_IDENTIFIER para audit em V$SESSION, VPD policy, Logger context
    DBMS_SESSION.set_identifier(l_username);

    -- Auditoria de login
    INSERT INTO log_acessos (id_usuario, evento, ip, ts)
    VALUES (l_id_usuario, 'LOGIN',
            OWA_UTIL.get_cgi_env('REMOTE_ADDR'),
            SYSTIMESTAMP);
    COMMIT;
  END post_authenticate;

  ----------------------------------------------------------------------------
  -- Pre-Logout (no scheme: Logout URL → Procedure)
  ----------------------------------------------------------------------------
  PROCEDURE pre_logout IS
  BEGIN
    INSERT INTO log_acessos (
      id_usuario, evento, ts
    ) VALUES (
      APEX_UTIL.get_session_state('G_ID_USUARIO'),
      'LOGOUT', SYSTIMESTAMP
    );
    COMMIT;
  END pre_logout;

  ----------------------------------------------------------------------------
  -- Session Sentinel (no scheme: Session Cookie Attributes / Sentry Function)
  --
  -- Chamada A CADA REQUEST. Bloqueia acesso se condição não bate.
  -- Performance crítica — query simples e indexada. Sem isso, app inteiro lento.
  --
  -- Casos típicos: conta foi bloqueada DURANTE a sessão; sessão excedeu
  -- inatividade customizada; usuário foi removido.
  ----------------------------------------------------------------------------
  FUNCTION sentinel_check RETURN BOOLEAN IS
    l_ativo VARCHAR2(1);
  BEGIN
    -- Cache em Application Item para evitar query por request? Cuidado: precisa
    -- invalidar quando o usuário é desativado por outro caminho.
    SELECT ativo INTO l_ativo
      FROM usuarios
     WHERE id = APEX_UTIL.get_session_state('G_ID_USUARIO');

    RETURN l_ativo = 'S';
  EXCEPTION
    WHEN NO_DATA_FOUND THEN
      RETURN FALSE;  -- usuário sumiu da base → invalidar sessão
  END sentinel_check;

END auth_pkg;
/

--==============================================================================
-- 2. Schema HTTP Header (SSO com proxy fazendo a autenticação)
--==============================================================================

-- Setting no Authentication Scheme:
--   Type: HTTP Header Variable
--   HTTP Header: REMOTE_USER (ou X-Authenticated-User, conforme proxy)
--
-- Útil quando há SSO corporativo (CAS, Shibboleth, ADFS) com reverse proxy
-- adicionando o header no request. O APEX confia no header e usa como :APP_USER.
-- ATENÇÃO: só funciona se o proxy IMPEDIR cliente direto. Sem isso, bypass total.

-- No nginx (exemplo):
--   location /ords/ {
--     auth_request /auth/validate;
--     proxy_set_header X-Authenticated-User $upstream_http_x_user;
--     proxy_pass http://ords-backend;
--   }

--==============================================================================
-- 3. Schema Open ID Connect (OIDC) — APEX nativo
--==============================================================================

-- 22.1+ tem suporte nativo a OIDC. Setting:
--   Type: Open ID Connect Provider
--   Discovery URL: https://login.microsoftonline.com/<tenant>/v2.0/.well-known/openid-configuration
--   Client ID / Secret: do app registrado no IdP
--
-- Sem código PL/SQL. APEX faz o flow, mapeia claims, e :APP_USER recebe o
-- email/upn do ID Token.

--==============================================================================
-- 4. Workspace SSO entre apps (mesmo workspace)
--==============================================================================

-- Apps no MESMO workspace e MESMA Authentication Scheme compartilham sessão.
-- Usuário loga em App 100, abre App 114 → não precisa re-logar.
--
-- Para forçar isolamento: criar Authentication Schemes separados ou
-- workspaces separados.

--==============================================================================
-- 5. Anti-patterns
--==============================================================================

/*
ANTI-PATTERN 1: Senha em VARCHAR2 plana
  -- ERRADO: pode vazar em backup, log, dump
  CREATE TABLE usuarios (senha VARCHAR2(50));  -- ❌

  -- BOM: hash com salt único por usuário
  CREATE TABLE usuarios (senha_hash VARCHAR2(64), salt VARCHAR2(32));

ANTI-PATTERN 2: Mensagem de erro "usuário não existe"
  -- VAZA INFO: atacante descobre quais usuários existem
  IF NOT existe(p_user) THEN
    apex_error.add_error('Usuário não cadastrado');
  ELSIF senha_errada THEN
    apex_error.add_error('Senha inválida');
  END IF;

  -- BOM: mesma mensagem para os dois casos
  apex_error.add_error('Credenciais inválidas');

ANTI-PATTERN 3: Sentry function fazendo query pesada
  -- IMPACTO: roda a CADA request. SELECT com JOIN de 5 tabelas mata o app.
  FUNCTION sentry RETURN BOOLEAN IS ...

  -- BOM: query simples, indexada, em coluna única; ou cache em Application Item

ANTI-PATTERN 4: Confiar em :APP_USER de HTTP_HEADER sem garantir o proxy
  -- VULNERÁVEL: cliente pode injetar o header
  -- BOM: proxy deve ser o ÚNICO caminho de entrada, com firewall bloqueando direto

ANTI-PATTERN 5: Esquecer DBMS_SESSION.set_identifier no post-auth
  -- IMPACTO: audit em V$SESSION mostra null; Logger sem contexto
  -- BOM: SEMPRE set_identifier(p_username) no post_authenticate
*/
