--==============================================================================
-- Template: Network ACL Setup (DBMS_NETWORK_ACL_ADMIN)
--
-- A partir de Oracle 11gR1, qualquer chamada de UTL_HTTP, UTL_SMTP, UTL_TCP,
-- UTL_INADDR, UTL_MAIL ou APEX_WEB_SERVICE.make_rest_request_* exige uma ACL
-- (Access Control List) configurada para o host de destino. Sem isso:
--
--   ORA-24247: network access denied by access control list (ACL)
--
-- Este template cobre o caminho 12c+ (Real Application Security / Unified ACL).
-- Em 11g a sintaxe é diferente (xdb-based) — ver doc Oracle 11g se aplicável.
--
-- Princípio: privilégio mínimo
--   - Criar UMA ACL por finalidade (não compartilhar entre apps diferentes)
--   - Conceder apenas o privilégio necessário (connect / resolve)
--   - Limitar por host e por porta sempre que possível
--==============================================================================

--==============================================================================
-- 1. Criar ACL + privilégios em um único passo (12c+)
--==============================================================================

-- ATENÇÃO: executar como SYS, SYSTEM, ou usuário com:
--   GRANT EXECUTE ON dbms_network_acl_admin TO <admin>;

BEGIN
  -- Append cria a ACL se não existe, ou anexa o privilégio se já existe.
  -- Idempotente: rodar duas vezes não duplica.
  DBMS_NETWORK_ACL_ADMIN.append_host_ace (
    host       => 'api.banco.com.br',           -- host exato (ou wildcard, ver §3)
    lower_port => 443,                          -- HTTPS típico
    upper_port => 443,
    ace        => xs$ace_type(
                    privilege_list => xs$name_list('connect', 'resolve'),
                    principal_name => 'MEU_APP',     -- schema da aplicação
                    principal_type => xs_acl.ptype_db
                  )
  );
END;
/

COMMIT;

--==============================================================================
-- 2. Verificar ACL aplicada para um host
--==============================================================================

-- Quem tem privilégio para qual host:
SELECT host,
       lower_port,
       upper_port,
       acl,
       acl_owner,
       acltype
  FROM dba_host_acls
 WHERE host = 'api.banco.com.br';

-- Detalhe dos privilégios concedidos:
SELECT acl,
       principal,
       privilege,
       is_grant,
       invert
  FROM dba_host_aces
 WHERE host = 'api.banco.com.br';

-- Teste prático — se retornar erro, ACL ainda não permitiu
DECLARE
  l_resp UTL_HTTP.resp;
  l_req  UTL_HTTP.req;
BEGIN
  l_req  := UTL_HTTP.begin_request('https://api.banco.com.br/healthcheck', 'GET');
  l_resp := UTL_HTTP.get_response(l_req);
  DBMS_OUTPUT.put_line('Status: ' || l_resp.status_code);
  UTL_HTTP.end_response(l_resp);
END;
/

--==============================================================================
-- 3. Patterns úteis
--==============================================================================

-- Padrão A: wildcard de host (CUIDADO — afrouxa segurança)
-- Use só quando precisa de subdomínios variáveis (ex: CDN, S3 com bucket dinâmico)
BEGIN
  DBMS_NETWORK_ACL_ADMIN.append_host_ace (
    host       => '*.amazonaws.com',
    lower_port => 443,
    upper_port => 443,
    ace        => xs$ace_type(
                    privilege_list => xs$name_list('connect', 'resolve'),
                    principal_name => 'MEU_APP',
                    principal_type => xs_acl.ptype_db
                  )
  );
END;
/

-- Padrão B: múltiplos schemas usando o mesmo host
-- Executar o bloco do §1 uma vez para cada schema (MEU_APP, MEU_APP_API, etc).

-- Padrão C: HTTP + HTTPS para o mesmo host
BEGIN
  -- HTTPS
  DBMS_NETWORK_ACL_ADMIN.append_host_ace (
    host       => 'api.parceiro.com',
    lower_port => 443, upper_port => 443,
    ace        => xs$ace_type(
                    privilege_list => xs$name_list('connect', 'resolve'),
                    principal_name => 'MEU_APP', principal_type => xs_acl.ptype_db
                  )
  );
  -- HTTP (para callback dev/legacy)
  DBMS_NETWORK_ACL_ADMIN.append_host_ace (
    host       => 'api.parceiro.com',
    lower_port => 80, upper_port => 80,
    ace        => xs$ace_type(
                    privilege_list => xs$name_list('connect', 'resolve'),
                    principal_name => 'MEU_APP', principal_type => xs_acl.ptype_db
                  )
  );
END;
/

--==============================================================================
-- 4. Wallet TLS — necessário para HTTPS
--==============================================================================

-- HTTPS requer wallet com certificado da CA confiável. Sem wallet:
--   ORA-29024: Certificate validation failure
--
-- Setup (uma vez por banco, executar no SO):
--   $ orapki wallet create -wallet /u01/app/oracle/wallets/ssl -auto_login -pwd <senha>
--   $ orapki wallet add -wallet /u01/app/oracle/wallets/ssl \
--       -trusted_cert -cert /caminho/para/ca.pem -pwd <senha>
--
-- No PL/SQL, antes de UTL_HTTP.begin_request:
DECLARE
  l_resp UTL_HTTP.resp;
  l_req  UTL_HTTP.req;
BEGIN
  UTL_HTTP.set_wallet('file:/u01/app/oracle/wallets/ssl', NULL);
  l_req  := UTL_HTTP.begin_request('https://api.banco.com.br/ping', 'GET');
  l_resp := UTL_HTTP.get_response(l_req);
  UTL_HTTP.end_response(l_resp);
END;
/

--==============================================================================
-- 5. Remover ACL (rollback ou limpeza)
--==============================================================================

-- Remove privilégio específico de um principal:
BEGIN
  DBMS_NETWORK_ACL_ADMIN.remove_host_ace (
    host           => 'api.banco.com.br',
    lower_port     => 443,
    upper_port     => 443,
    ace            => xs$ace_type(
                        privilege_list => xs$name_list('connect', 'resolve'),
                        principal_name => 'MEU_APP',
                        principal_type => xs_acl.ptype_db
                      ),
    remove_empty_acl => TRUE     -- remove a ACL inteira se não sobrar privilégio
  );
END;
/

--==============================================================================
-- 6. Troubleshooting
--==============================================================================

/*
ERRO: ORA-24247 (network access denied by ACL)
  → ACL não criada, ou criada para outro host/porta/principal.
  → Verificar com a query do §2.
  → Em 11gR2 a sintaxe é DIFERENTE (XDB ACL). Não use este template em <12c.

ERRO: ORA-29024 (certificate validation failure)
  → Wallet TLS ausente ou sem o certificado da CA.
  → Ver §4.

ERRO: ORA-12545 (Connect failed because target host not reachable)
  → DNS do banco não resolve o host. Verificar nslookup/tnsping NO SERVIDOR DO BANCO.
  → Em ambientes restritos, pode haver proxy: usar UTL_HTTP.set_proxy().

ERRO: ORA-29273 (HTTP request failed)
  → Pode ser timeout. Configurar antes do begin_request:
    UTL_HTTP.set_transfer_timeout(60);  -- segundos
*/
