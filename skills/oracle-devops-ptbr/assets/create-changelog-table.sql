-- create-changelog-table.sql
-- Cria a tabela de controle do changelog de banco de dados — ou atualiza uma
-- tabela de versão anterior para o modelo com status (idempotente).
-- M&S do Brasil LTDA — contato@msbrasil.inf.br
--
-- O apply_changelog.py executa este mesmo bloco automaticamente (constante
-- DDL_CHANGELOG_TABLE); este arquivo serve para o DBA rodar à mão pelo SQLcl:
--   sql -S usuario@//host:1521/servico @create-changelog-table.sql
--
-- Status de cada migration:
--   EM_ANDAMENTO  gravado (e comitado) ANTES de executar a migration
--   APLICADA      terminou sem erro e sem erro de compilação
--   ERRO          falhou; mensagem_erro e statement_erro dizem onde
-- Enquanto houver ERRO/EM_ANDAMENTO, o apply_changelog.py bloqueia novas
-- execuções (ver --retomar e --marcar-resolvida).
--
-- Atualização de tabela antiga: as colunas status, mensagem_erro e
-- statement_erro são acrescentadas; linhas existentes ficam como APLICADA.
--
-- Usa ALL_TABLES + SYS_CONTEXT('USERENV','CURRENT_SCHEMA') (e não USER_TABLES)
-- para funcionar quando o usuário de conexão é diferente do schema alvo
-- (ALTER SESSION SET CURRENT_SCHEMA = <DB_SCHEMA> antes de rodar).
-- ─────────────────────────────────────────────────────────────────────────────

SET SERVEROUTPUT ON

DECLARE
  l_schema VARCHAR2(128) := SYS_CONTEXT('USERENV', 'CURRENT_SCHEMA');
  l_qtd    PLS_INTEGER;

  FUNCTION existe_coluna(p_coluna IN VARCHAR2) RETURN BOOLEAN IS
    l_qtd_coluna PLS_INTEGER;
  BEGIN
    SELECT COUNT(*)
      INTO l_qtd_coluna
      FROM all_tab_columns
     WHERE owner       = l_schema
       AND table_name  = 'DB_CHANGELOG'
       AND column_name = p_coluna;
    RETURN l_qtd_coluna > 0;
  END existe_coluna;
BEGIN
  -- ALL_TABLES + CURRENT_SCHEMA: funciona quando o usuário de conexão é
  -- diferente do schema alvo (DB_SCHEMA != DB_USER).
  SELECT COUNT(*)
    INTO l_qtd
    FROM all_tables
   WHERE owner      = l_schema
     AND table_name = 'DB_CHANGELOG';

  IF l_qtd = 0 THEN
    EXECUTE IMMEDIATE q'[
      CREATE TABLE db_changelog (
        id             VARCHAR2(20)   NOT NULL,
        descricao      VARCHAR2(500)  NOT NULL,
        arquivo        VARCHAR2(500)  NOT NULL,
        tipo           VARCHAR2(10)   NOT NULL,
        checksum       VARCHAR2(64)   NOT NULL,
        status         VARCHAR2(20)   NOT NULL,
        aplicado_em    DATE           DEFAULT SYSDATE NOT NULL,
        aplicado_por   VARCHAR2(128)  DEFAULT USER    NOT NULL,
        duracao_ms     NUMBER,
        ambiente       VARCHAR2(10),
        mensagem_erro  VARCHAR2(4000),
        statement_erro VARCHAR2(4000),
        CONSTRAINT pk_db_changelog PRIMARY KEY (id),
        CONSTRAINT ck_db_changelog_status
          CHECK (status IN ('EM_ANDAMENTO', 'APLICADA', 'ERRO'))
      )]';
    EXECUTE IMMEDIATE q'[COMMENT ON TABLE db_changelog IS 'Controle de migrations — gerenciado por apply_changelog.py']';
  ELSE
    IF NOT existe_coluna('STATUS') THEN
      -- Linhas existentes foram aplicadas pela versão anterior do script.
      EXECUTE IMMEDIATE q'[ALTER TABLE db_changelog ADD (status VARCHAR2(20) DEFAULT 'APLICADA' NOT NULL)]';
      -- Sem default daqui em diante: o script sempre informa o status.
      EXECUTE IMMEDIATE q'[ALTER TABLE db_changelog MODIFY (status DEFAULT NULL)]';
    END IF;
    IF NOT existe_coluna('MENSAGEM_ERRO') THEN
      EXECUTE IMMEDIATE q'[ALTER TABLE db_changelog ADD (mensagem_erro VARCHAR2(4000))]';
    END IF;
    IF NOT existe_coluna('STATEMENT_ERRO') THEN
      EXECUTE IMMEDIATE q'[ALTER TABLE db_changelog ADD (statement_erro VARCHAR2(4000))]';
    END IF;
    SELECT COUNT(*)
      INTO l_qtd
      FROM all_constraints
     WHERE owner           = l_schema
       AND table_name      = 'DB_CHANGELOG'
       AND constraint_name = 'CK_DB_CHANGELOG_STATUS';
    IF l_qtd = 0 THEN
      EXECUTE IMMEDIATE q'[ALTER TABLE db_changelog ADD CONSTRAINT ck_db_changelog_status CHECK (status IN ('EM_ANDAMENTO', 'APLICADA', 'ERRO'))]';
    END IF;
  END IF;
END;
/

-- Conferir estrutura
SELECT column_name, data_type, data_length, nullable
  FROM all_tab_columns
 WHERE table_name = 'DB_CHANGELOG'
   AND owner      = SYS_CONTEXT('USERENV', 'CURRENT_SCHEMA')
 ORDER BY column_id;
