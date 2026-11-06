--==============================================================================
-- Template: Triggers Canônicos
--
-- Cobre: trigger simples de auditoria de colunas, compound trigger (estado
-- entre linha e statement), package de auditoria, surrogate key legada,
-- cross-edition (EBR) e anti-patterns.
--
-- Princípios canônicos aplicados:
--   #4: Trigger e package de auditoria NÃO comitam (fazem parte da
--       transação de quem disparou o DML)
--   #9: Triggers não contêm regra de negócio
--   #10: Compound trigger quando há estado entre linha e statement
--        (mutating table, auditoria em lote, bulk); trigger simples
--        FOR EACH ROW continua válida para o caso só-linha
--
-- Pré-requisito dos exemplos (ajuste ao seu modelo):
--   CREATE TABLE faturas (
--     id_fatura      NUMBER PRIMARY KEY,
--     valor          NUMBER,
--     criado_em      TIMESTAMP,     criado_por     VARCHAR2(128),
--     atualizado_em  TIMESTAMP,     atualizado_por VARCHAR2(128));
--
-- Referência: padrão Trivadis 4.4 + adoções de Insum (G-7720, G-7730).
--==============================================================================


--==============================================================================
-- 1. Trigger simples — auditoria de colunas (só linha)
--
-- Não há estado a levar da linha para o statement: trigger FOR EACH ROW é
-- suficiente, mais curta e mais fácil de ler que um compound.
--==============================================================================

CREATE OR REPLACE TRIGGER tr_faturas_biu_auditoria
BEFORE INSERT OR UPDATE ON faturas
FOR EACH ROW
BEGIN
  IF INSERTING THEN
    :NEW.criado_em      := SYSTIMESTAMP;
    :NEW.criado_por     := NVL(SYS_CONTEXT('USERENV', 'CLIENT_IDENTIFIER'), USER);
    :NEW.atualizado_em  := :NEW.criado_em;
    :NEW.atualizado_por := :NEW.criado_por;
  ELSE
    :NEW.atualizado_em  := SYSTIMESTAMP;
    :NEW.atualizado_por := NVL(SYS_CONTEXT('USERENV', 'CLIENT_IDENTIFIER'), USER);
    -- Preserva campos imutáveis (trilha de criação)
    :NEW.criado_em      := :OLD.criado_em;
    :NEW.criado_por     := :OLD.criado_por;
  END IF;
END tr_faturas_biu_auditoria;
/


--==============================================================================
-- 2. Package de auditoria — a lógica fica aqui; triggers só notificam
--
-- Sem COMMIT: o registro de auditoria faz parte da mesma transação do DML
-- auditado (se o DML for desfeito, a auditoria também é).
--==============================================================================

CREATE TABLE auditoria_alteracao (
  id_auditoria  NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  tabela        VARCHAR2(128) NOT NULL,
  id_registro   NUMBER        NOT NULL,
  operacao      VARCHAR2(6)   NOT NULL,
  dados_old     VARCHAR2(4000),
  dados_new     VARCHAR2(4000),
  alterado_em   TIMESTAMP     DEFAULT SYSTIMESTAMP NOT NULL,
  alterado_por  VARCHAR2(128) DEFAULT NVL(SYS_CONTEXT('USERENV', 'CLIENT_IDENTIFIER'), USER) NOT NULL
);

CREATE OR REPLACE PACKAGE auditoria_pkg AS

  -- O tipo vem ANTES dos subprogramas que o usam como parâmetro.
  TYPE t_lista_ids IS TABLE OF NUMBER INDEX BY PLS_INTEGER;

  PROCEDURE registrar_alteracao_faturas (
    p_ids       IN t_lista_ids,
    p_operacao  IN VARCHAR2
  );

  PROCEDURE registrar_alteracao_clientes (
    p_id_cliente  IN NUMBER,
    p_operacao    IN VARCHAR2,
    p_dados_old   IN VARCHAR2,
    p_dados_new   IN VARCHAR2
  );

END auditoria_pkg;
/

CREATE OR REPLACE PACKAGE BODY auditoria_pkg AS

  PROCEDURE registrar_alteracao_faturas (
    p_ids       IN t_lista_ids,
    p_operacao  IN VARCHAR2
  ) IS
  BEGIN
    -- Um INSERT em lote para todas as linhas do statement (sem COMMIT)
    FORALL i IN INDICES OF p_ids
      INSERT INTO auditoria_alteracao (tabela, id_registro, operacao)
      VALUES ('FATURAS', p_ids(i), p_operacao);
  END registrar_alteracao_faturas;

  PROCEDURE registrar_alteracao_clientes (
    p_id_cliente  IN NUMBER,
    p_operacao    IN VARCHAR2,
    p_dados_old   IN VARCHAR2,
    p_dados_new   IN VARCHAR2
  ) IS
  BEGIN
    INSERT INTO auditoria_alteracao (tabela, id_registro, operacao, dados_old, dados_new)
    VALUES ('CLIENTES', p_id_cliente, p_operacao, p_dados_old, p_dados_new);
  END registrar_alteracao_clientes;

END auditoria_pkg;
/


--==============================================================================
-- 3. Compound trigger — estado entre linha e statement (auditoria em lote)
--
-- Use compound quando é preciso LEVAR estado da linha para o statement:
--   - auditoria/processamento em lote (1 chamada por statement, não por linha);
--   - evitar mutating table: coletar IDs em AFTER EACH ROW e consultar a
--     própria tabela só em AFTER STATEMENT (ORA-04091 na linha);
--   - DML em volume (bulk), descarregando a cada N linhas para limitar memória.
-- O estado declarado no compound é criado no início de cada statement
-- disparador e descartado ao final — não há o que "resetar" manualmente,
-- e não se usa variável global de package para isso.
--==============================================================================

CREATE OR REPLACE TRIGGER tr_faturas_auditoria_lote
FOR INSERT OR UPDATE ON faturas
COMPOUND TRIGGER

  -- Descarrega a cada N linhas: limita a memória em DML muito grande
  lc_limite CONSTANT PLS_INTEGER := 1000;

  l_ids      auditoria_pkg.t_lista_ids;
  l_operacao VARCHAR2(6);

  PROCEDURE descarregar IS
  BEGIN
    IF l_ids.COUNT > 0 THEN
      auditoria_pkg.registrar_alteracao_faturas(p_ids => l_ids, p_operacao => l_operacao);
      l_ids.DELETE;
    END IF;
  END descarregar;

  --------------------------------------------------------------------
  AFTER EACH ROW IS
  --------------------------------------------------------------------
  BEGIN
    -- Só coleta; não consulta faturas aqui (evita mutating table)
    l_operacao := CASE WHEN INSERTING THEN 'INSERT' ELSE 'UPDATE' END;
    l_ids(l_ids.COUNT + 1) := :NEW.id_fatura;
    IF l_ids.COUNT >= lc_limite THEN
      descarregar;
    END IF;
  END AFTER EACH ROW;

  --------------------------------------------------------------------
  AFTER STATEMENT IS
  --------------------------------------------------------------------
  BEGIN
    descarregar;
  END AFTER STATEMENT;

END tr_faturas_auditoria_lote;
/


--==============================================================================
-- 4. Surrogate key trigger (legado pré-12c)
--
-- Em 12c+, prefira GENERATED ... AS IDENTITY na coluna (sem trigger).
-- O trigger abaixo é para tabela LEGADA sem IDENTITY. Nunca combine os
-- dois: atribuir valor a coluna GENERATED ALWAYS AS IDENTITY gera erro.
--==============================================================================

-- Forma moderna (preferir):
CREATE TABLE pagamentos (
  id_pagamento  NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  id_fatura     NUMBER NOT NULL,
  valor         NUMBER(10,2),
  pago_em       TIMESTAMP DEFAULT SYSTIMESTAMP,
  criado_por    VARCHAR2(128)
);

-- Forma legada (tabela sem IDENTITY) — sequence + trigger simples:
CREATE TABLE pagamentos_legado (
  id_pagamento  NUMBER PRIMARY KEY,
  id_fatura     NUMBER NOT NULL,
  valor         NUMBER(10,2)
);

CREATE SEQUENCE seq_pagamentos_legado START WITH 1 NOCACHE NOORDER;

CREATE OR REPLACE TRIGGER tr_pagamentos_legado_pk
BEFORE INSERT ON pagamentos_legado
FOR EACH ROW
BEGIN
  IF :NEW.id_pagamento IS NULL THEN
    :NEW.id_pagamento := seq_pagamentos_legado.NEXTVAL;
  END IF;
END tr_pagamentos_legado_pk;
/


--==============================================================================
-- 5. EBR — cross-edition trigger (template conceitual)
--
-- Cross-edition triggers são o ÚNICO caso onde lógica de transformação
-- de dados em trigger é justificável (princípio #9 abre exceção para EBR).
--
-- São usados durante migração de schema entre editions, mantendo
-- compatibilidade entre versão antiga e nova da aplicação.
--==============================================================================

-- Cenário: coluna `nome` está sendo dividida em `primeiro_nome` + `sobrenome`.
-- Edition antiga vê `nome`; edition nova vê os dois campos separados.
-- Forward cross-edition trigger mantém os campos novos sincronizados quando
-- a edition antiga grava em `nome`.

CREATE OR REPLACE TRIGGER tr_clientes_fwd_xed
BEFORE INSERT OR UPDATE OF nome ON clientes
FOR EACH ROW
FORWARD CROSSEDITION
DISABLE  -- habilitada apenas durante migração
DECLARE
  l_pos PLS_INTEGER;
BEGIN
  -- Só atua quando a edition antiga grava em :NEW.nome
  l_pos := INSTR(:NEW.nome, ' ');
  IF l_pos > 0 THEN
    :NEW.primeiro_nome := SUBSTR(:NEW.nome, 1, l_pos - 1);
    :NEW.sobrenome     := SUBSTR(:NEW.nome, l_pos + 1);
  ELSE
    :NEW.primeiro_nome := :NEW.nome;
    :NEW.sobrenome     := NULL;
  END IF;
END tr_clientes_fwd_xed;
/

-- Reverse cross-edition trigger faz o inverso: edition nova grava em
-- primeiro_nome + sobrenome, trigger reconstrói `nome` para edition antiga.

CREATE OR REPLACE TRIGGER tr_clientes_rev_xed
BEFORE INSERT OR UPDATE OF primeiro_nome, sobrenome ON clientes
FOR EACH ROW
REVERSE CROSSEDITION
DISABLE
BEGIN
  :NEW.nome := TRIM(:NEW.primeiro_nome || ' ' || :NEW.sobrenome);
END tr_clientes_rev_xed;
/

-- Detalhes completos do uso de cross-edition triggers em
-- references/ebr-editioning-views.md


--==============================================================================
-- 6. Anti-patterns
--==============================================================================

/*
ANTI-PATTERN 1: Business logic em trigger (CRÍTICO)

  -- ERRADO: regra de negócio escondida em trigger
  CREATE OR REPLACE TRIGGER tr_faturas_calcular
  BEFORE INSERT OR UPDATE ON faturas
  FOR EACH ROW
  DECLARE
    l_taxa NUMBER;
    l_desconto NUMBER;
  BEGIN
    -- Cálculo complexo de imposto
    SELECT taxa INTO l_taxa
      FROM regras_fiscais WHERE estado = :NEW.estado_uf;

    -- Aplicação de desconto baseado em histórico
    SELECT NVL(SUM(valor), 0) INTO l_desconto
      FROM pagamentos
     WHERE id_cliente = :NEW.id_cliente
       AND pago_em >= ADD_MONTHS(SYSDATE, -12);

    IF l_desconto > 100000 THEN
      :NEW.valor := :NEW.valor * 0.95;  -- desconto fidelidade
    END IF;

    :NEW.valor_imposto := :NEW.valor * l_taxa / 100;
  END;
  /

  Problemas:
  - Lógica fica escondida; quem lê faturas_pkg não vê
  - Quebra em bulk INSERT (FORALL não pode ser revertido facilmente)
  - Mutating table se quiser ler outras linhas de faturas
  - Performance: 1 query por linha em vez de DML único
  - Difícil de testar isoladamente

  -- CORRETO: lógica em package, chamada explícita
  CREATE OR REPLACE PACKAGE faturas_pkg AS
    PROCEDURE criar_fatura (
      p_id_cliente  IN NUMBER,
      p_valor       IN NUMBER,
      p_estado_uf   IN VARCHAR2,
      p_id_fatura   OUT NUMBER
    );
  END faturas_pkg;
  /

  -- O caller chama faturas_pkg.criar_fatura, que aplica regras claramente.


ANTI-PATTERN 2: Estado entre linha e statement via variável global de package

  -- ERRADO: triggers de statement e de linha conversando por package global
  CREATE TRIGGER tr_faturas_bs ... BEFORE STATEMENT   -- limpa pkg.g_ids
  CREATE TRIGGER tr_faturas_ar ... AFTER EACH ROW     -- acumula em pkg.g_ids
  CREATE TRIGGER tr_faturas_as ... AFTER STATEMENT    -- processa pkg.g_ids
  -- Estado vaza entre statements se um deles falhar no meio.

  -- CORRETO: COMPOUND TRIGGER único, estado local (seção 3).
  -- Sem estado entre linha e statement? Trigger simples basta (seção 1).


ANTI-PATTERN 3: Trigger encadeado / cascading

  -- ERRADO: trigger A insere em B; trigger B insere em C; trigger C atualiza A
  -- Resultado: loop infinito, dificílimo de debugar

  -- CORRETO: chamada explícita via package, controle de fluxo claro


ANTI-PATTERN 4: SELECT na própria tabela do trigger (mutating table)

  -- ERRADO em FOR EACH ROW
  CREATE TRIGGER tr_faturas_check
  BEFORE INSERT ON faturas
  FOR EACH ROW
  DECLARE
    l_total NUMBER;
  BEGIN
    SELECT SUM(valor) INTO l_total FROM faturas WHERE ...;  -- ORA-04091
  END;

  -- CORRETO: COMPOUND TRIGGER coleta IDs em AFTER EACH ROW,
  -- consulta agregada em AFTER STATEMENT


ANTI-PATTERN 5: Trigger fazendo COMMIT ou ROLLBACK

  -- ERRADO: rompe transação do caller
  CREATE TRIGGER tr_log_audit
  AFTER INSERT ON faturas
  FOR EACH ROW
  DECLARE
    PRAGMA AUTONOMOUS_TRANSACTION;
  BEGIN
    INSERT INTO log_audit ...;
    COMMIT;  -- caller não controla mais a transação
  END;

  -- AUTONOMOUS_TRANSACTION em trigger é code smell. Prefira:
  -- - Logger framework (que já gerencia autonomous internally)
  -- - Package que processa o evento de forma síncrona
  -- - DBMS_AQ para fila assíncrona


ANTI-PATTERN 6: Validação de regra de domínio em trigger

  -- ERRADO
  CREATE TRIGGER tr_faturas_valid
  BEFORE INSERT OR UPDATE ON faturas
  FOR EACH ROW
  BEGIN
    IF :NEW.valor < 0 THEN
      raise_application_error(-20100, 'Valor não pode ser negativo');
    END IF;
    IF :NEW.data_vencimento < SYSDATE THEN
      raise_application_error(-20101, 'Vencimento no passado');
    END IF;
  END;

  -- CORRETO:
  -- 1. CHECK constraint na tabela:
  --    ALTER TABLE faturas ADD CONSTRAINT ck_faturas_valor_pos CHECK (valor >= 0);
  -- 2. Validação de regra complexa em package: faturas_pkg.validar_fatura()
  --    chamado pelo caller ANTES do INSERT.


ANTI-PATTERN 7: Trigger lendo SYS_CONTEXT mal documentado

  -- Cuidado com USER vs CLIENT_IDENTIFIER vs OS_USER
  -- USER: schema atual do banco (ex: APP_OWNER); igual para todos os usuários da app
  -- CLIENT_IDENTIFIER: setado pela aplicação via DBMS_SESSION.SET_IDENTIFIER
  --                    (ex: usuário APEX, identidade do consumidor REST)
  -- OS_USER: sistema operacional (raramente útil em apps web)

  -- BOM (com fallback explícito):
  :NEW.criado_por := NVL(SYS_CONTEXT('USERENV', 'CLIENT_IDENTIFIER'), USER);
*/


--==============================================================================
-- 7. Decisão rápida
--==============================================================================

/*
PRECISA TRIGGER?

  Auditoria de colunas (criado_em/criado_por)?        → BEFORE INSERT OR UPDATE FOR EACH ROW
  Auditoria em lote / ler a própria tabela / bulk?    → COMPOUND TRIGGER
  Surrogate key em tabela legada sem IDENTITY?        → BEFORE INSERT FOR EACH ROW
  Migração de schema com EBR (cross-edition)?         → CROSSEDITION TRIGGER
  Validação de regra de domínio?                      → CHECK CONSTRAINT ou package
  Cálculo de campo derivado?                          → VIRTUAL COLUMN ou package
  Cascade de operações em outra tabela?               → Package, NÃO trigger
  Processamento assíncrono?                           → DBMS_AQ + scheduler job
  Logging?                                            → Logger framework

REGRA GERAL:
  - Trigger faz NO MÁXIMO: setar campos de auditoria, gerar ID, notificar package
  - Trigger NUNCA faz: lógica de domínio, COMMIT, SELECT na própria tabela,
    decisões de negócio, transformações complexas (exceto cross-edition em EBR)
*/
