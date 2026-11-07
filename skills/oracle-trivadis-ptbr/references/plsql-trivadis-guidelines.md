# PL/SQL — Trivadis Guidelines 4.4

Detalhes dos padrões Trivadis para Oracle PL/SQL. Use esta referência quando precisar revisar código alheio, justificar uma escolha em code review, ou aplicar padrão consistente em código novo.

## Índice

- [Por que Trivadis 4.4](#por-que-trivadis-44)
- [Naming conventions completas](#naming-conventions-completas)
- [Estrutura de package](#estrutura-de-package)
- [Exception handling](#exception-handling)
- [Cursores](#cursores)
- [Bulk processing](#bulk-processing)
- [Transações](#transações)
- [Comentários](#comentários)
- [Antipatterns Trivadis-explicit](#antipatterns-trivadis-explicit)
- [Linkagem com outros recursos](#linkagem-com-outros-recursos)

## Por que Trivadis 4.4

Trivadis Guidelines é um padrão amplamente adotado para Oracle PL/SQL
profissional, originado na Trivadis (consultoria suíça) e hoje mantido como
projeto aberto. Característica: convenções rígidas mas justificadas, foco em
manutenibilidade. Cada regra tem um código no formato **G-xxxx** (ex.: G-2310
"Avoid using CHAR data type", G-5040 "Avoid WHEN OTHERS sem handlers
específicos") e as convenções de naming são verificáveis pelo **PL/SQL Cop**
(validador `TrivadisPlsqlNaming`, regras G-9101 a G-9115).

Documento original (v4.4): https://trivadis.github.io/plsql-and-sql-coding-guidelines/v4.4/
Repositório/validador: https://github.com/Trivadis/plsql-cop-validators

## Naming conventions completas

### Importante: dialeto local desta base de código

O padrão Trivadis oficial é definido pelo validador `TrivadisPlsqlNaming`
(PL/SQL Cop), capítulo 2.2 das guidelines. **Esta base de código (M&S do Brasil)
adota um dialeto local** que diverge do oficial em dois prefixos, por decisão
deliberada de consistência com o código já existente. As duas colunas abaixo
deixam a diferença explícita — ao revisar código DESTA base, use a coluna
"Local"; ao revisar código de terceiros ou validar com PL/SQL Cop, use a
"Oficial".

### Variáveis, constantes e afins

| Elemento | Prefixo LOCAL (esta base) | Prefixo OFICIAL Trivadis | Regra | Exemplo (local) |
|---|---|---|---|---|
| Variável global de pacote | `g_` | `g_` | G-9101 | `g_id_usuario NUMBER;` |
| Variável local | `l_` | `l_` | G-9102 | `l_qtd NUMBER;` |
| **Constante global de pacote** | **`gc_`** | `co_` (sem distinção de escopo) | G-9114 | `gc_max_tentativas CONSTANT NUMBER := 3;` |
| **Constante local** | **`lc_`** | `co_` (sem distinção de escopo) | G-9114 | `lc_idioma_default CONSTANT VARCHAR2(2) := 'PT';` |
| **Cursor** | **`co_`** | `c_` | G-9103 | `CURSOR co_ativos IS SELECT ...` |
| Record (instância) | `r_` | `r_` | G-9104 | `r_funcionario funcionarios%ROWTYPE;` |
| Collection/array (instância) | `t_` | `t_` | G-9105 | `l_ids t_lista_ids;` |
| Exception | `e_` | `e_` | G-9113 | `e_estado_invalido EXCEPTION;` |
| Parâmetro (genérico) | `p_` | `p_` (parâmetro de cursor) | G-9107 | `p_id_funcionario IN NUMBER` |

> **Os dois desvios locais conscientes:**
> 1. **Constantes** — o oficial usa `co_` para qualquer constante (sem indicar
>    escopo). Esta base usa `gc_` (global/package) e `lc_` (local), porque o
>    escopo da constante é informação útil em review. Consequência: `co_` fica
>    livre e é reaproveitado para cursor.
> 2. **Cursor** — o oficial usa `c_`. Esta base usa `co_`. (Não há colisão com
>    constante porque constantes usam `gc_`/`lc_` aqui.)
>
> **NÃO existe o prefixo `gco_`** ("variável de contexto") — isso não faz parte
> do Trivadis nem deste dialeto; se aparecer em código legado, é desvio a corrigir.

### Convenções oficiais que esta base também segue (sem divergência)

O padrão Trivadis distingue parâmetros por direção e tem sufixo `_type` para
**definições** de tipo. Aplique quando o código exigir clareza de direção/tipo:

| Elemento | Prefixo/Sufixo oficial | Regra | Exemplo |
|---|---|---|---|
| Parâmetro IN | `in_` (ou `p_` na convenção simples) | G-9108 | `in_id_funcionario IN NUMBER` |
| Parâmetro OUT | `out_` | G-9109 | `out_total OUT NUMBER` |
| Parâmetro IN OUT | `io_` | G-9110 | `io_buffer IN OUT CLOB` |
| Object (instância de object type) | `o_` | G-9106 | `o_endereco endereco_typ;` |
| **Definição** de record type | sufixo `_type` (`r_..._type`) | G-9111 | `TYPE r_funcionario_type IS RECORD (...);` |
| **Definição** de collection type | sufixo `_type` (`t_..._type`) | G-9112 | `TYPE t_id_type IS TABLE OF NUMBER;` |
| Subtype | sufixo `_type` | G-9115 | `SUBTYPE id_type IS NUMBER(10);` |

> Distinção importante: `r_`/`t_` (sem `_type`) nomeiam **instâncias**; o sufixo
> `_type` nomeia a **definição** do tipo. Ex.: `TYPE t_ids_type IS TABLE OF NUMBER;`
> (definição) e `l_ids t_ids_type;` — na convenção simples desta base, costuma-se
> usar `t_lista_ids` direto para a definição quando não há ambiguidade; em código
> validado por PL/SQL Cop, prefira o sufixo `_type` na definição.

> **Idioma dos prefixos:** os prefixos (`g_`, `gc_`, `l_`, `lc_`, `co_`, `r_`,
> `t_`, `e_`, `p_`) são parte do padrão e **mantêm-se em inglês**. Apenas o nome
> após o prefixo é em PT-BR.

### Procedures e Functions

- **Verbo no infinitivo:** `processar_fatura`, `validar_cpf`, `enviar_notificacao`
- **Sem prefixos redundantes:** evite `executar_processo`, `rodar_limpeza`
- **Function vs Procedure:**
  - Function: retorna valor único, nome geralmente é substantivo do retorno (`obter_valor_total`)
  - Procedure: ação que pode ter side effects, nome é verbo (`processar_pagamento`)

### Packages

- **Sufixo `_pkg`:** recomendado mas não obrigatório
- **Singular:** `pagamento_pkg`, não `pagamentos_pkg`
- **Domínio bem definido:** package de pagamento não cuida de NFSe; cada package tem responsabilidade única

### Tabelas e colunas

Trivadis foca em PL/SQL, mas aplicar consistência ajuda:

- **Tabelas em minúsculas, plural:** `funcionarios`, `faturas`, `clientes`
- **PK simples como `id`:** `funcionarios.id`, `faturas.id` (padrão moderno) ou `id_funcionario`, `id_fatura` (padrão tradicional)
- **FK com nome explícito:** `id_cliente`, `id_funcionario` (deixa o relacionamento óbvio)
- **Booleanos:** em banco **23ai/26ai**, use o tipo `BOOLEAN` nativo de SQL
  (`ativo BOOLEAN`) — aceita `TRUE`/`FALSE`/`NULL`, porém **não é indexável**.
  Em **19c** (sem BOOLEAN em SQL), emule com `NUMBER(1)` + CHECK
  (`ativo NUMBER(1) CHECK (ativo IN (0,1))`); a guideline G-2310 desaconselha
  `CHAR`, então prefira `NUMBER(1)` a `CHAR(1)` para a flag em 19c. Confirme a
  versão de banco antes de assumir BOOLEAN nativo.

## Estrutura de package

### Header (SPEC)

```sql
CREATE OR REPLACE PACKAGE exemplo_pkg AS
  /**
   * Package responsável por processar exemplos.
   *
   * Convenção: uma frase descrevendo a responsabilidade do package.
   * Linhas adicionais para detalhes importantes (regras de negócio,
   * dependências externas, observações de uso).
   */

  -- ============================================================
  -- Tipos públicos
  -- ============================================================
  TYPE t_lista_ids IS TABLE OF NUMBER INDEX BY PLS_INTEGER;

  -- ============================================================
  -- Constantes públicas (raras — geralmente private)
  -- ============================================================
  gc_max_registros CONSTANT NUMBER := 1000;

  -- ============================================================
  -- Exceptions públicas (uso por callers)
  -- ============================================================
  e_estado_invalido EXCEPTION;
  PRAGMA EXCEPTION_INIT(e_estado_invalido, -20100);

  -- ============================================================
  -- Procedures e Functions públicas
  -- ============================================================

  /**
   * Processa um exemplo.
   *
   * @param p_id              ID do exemplo a processar
   * @param p_forcar_update   Se 'S', força atualização mesmo se já processado
   *
   * @raises e_estado_invalido Se o exemplo está em estado inválido
   */
  PROCEDURE processar_exemplo(
    p_id            IN NUMBER,
    p_forcar_update IN VARCHAR2 DEFAULT 'N'
  );

  FUNCTION obter_status(
    p_id IN NUMBER
  ) RETURN VARCHAR2;

END exemplo_pkg;
/
```

### Body (BODY)

```sql
CREATE OR REPLACE PACKAGE BODY exemplo_pkg AS
  -- ============================================================
  -- Constantes privadas
  -- ============================================================
  gc_nome_pacote CONSTANT VARCHAR2(30) := 'EXEMPLO_PKG';

  -- ============================================================
  -- Variáveis globais (cuidado: persistem entre chamadas na sessão)
  -- ============================================================
  g_cache_inicializado BOOLEAN := FALSE;

  -- ============================================================
  -- Forward declarations (para procedures privadas usadas antes de declaradas)
  -- ============================================================
  PROCEDURE validar_estado(p_id IN NUMBER);

  -- ============================================================
  -- Procedures e Functions
  -- ============================================================

  PROCEDURE processar_exemplo(
    p_id            IN NUMBER,
    p_forcar_update IN VARCHAR2 DEFAULT 'N'
  ) IS
    lc_nome_unidade CONSTANT VARCHAR2(60) := gc_nome_pacote || '.processar_exemplo';
    l_status        VARCHAR2(20);
  BEGIN
    -- Rotina reutilizável: não comita; desfaz só o próprio trabalho em erro
    SAVEPOINT sp_processar_exemplo;

    -- Valida estado antes de processar
    validar_estado(p_id);

    -- Lógica principal
    SELECT status INTO l_status FROM exemplos WHERE id = p_id;

    IF l_status = 'PROCESSADO' AND p_forcar_update = 'N' THEN
      RETURN;  -- já processado, no-op
    END IF;

    UPDATE exemplos SET status = 'PROCESSADO', processado_em = SYSDATE
     WHERE id = p_id;
    -- SEM COMMIT: o dono da transação (job, endpoint, process) decide

  EXCEPTION
    WHEN e_estado_invalido THEN
      ROLLBACK TO sp_processar_exemplo;
      raise_application_error(-20100,
        'Estado inválido em ' || lc_nome_unidade || ' para ID ' || p_id);
    WHEN OTHERS THEN
      ROLLBACK TO sp_processar_exemplo;
      logger.log_error('Erro inesperado em ' || lc_nome_unidade, lc_nome_unidade);
      RAISE;  -- preserva código e pilha originais
  END processar_exemplo;


  FUNCTION obter_status(
    p_id IN NUMBER
  ) RETURN VARCHAR2 IS
    l_status VARCHAR2(20);
  BEGIN
    SELECT status INTO l_status FROM exemplos WHERE id = p_id;
    RETURN l_status;
  EXCEPTION
    WHEN NO_DATA_FOUND THEN
      RETURN NULL;
  END obter_status;


  PROCEDURE validar_estado(p_id IN NUMBER) IS
    l_estado VARCHAR2(20);
  BEGIN
    SELECT estado INTO l_estado FROM exemplos WHERE id = p_id;
    IF l_estado NOT IN ('VALIDO', 'PENDENTE') THEN
      RAISE e_estado_invalido;
    END IF;
  END validar_estado;

END exemplo_pkg;
/
```

## Exception handling

### Padrão completo

Todo procedure tem três blocos de exception (rotina reutilizável com DML
abre `SAVEPOINT sp_<nome>` como primeiro comando):

```sql
EXCEPTION
  WHEN e_specific_known THEN
    -- Erro de negócio conhecido: contexto + código próprio
    ROLLBACK TO sp_<nome>;
    raise_application_error(-20001,
      'Contexto específico em ' || lc_nome_unidade || ': ' || ..., TRUE);  -- TRUE mantém a pilha

  WHEN NO_DATA_FOUND THEN
    -- Tratamento esperado (pode ser RETURN NULL, default value, etc.)
    NULL;

  WHEN OTHERS THEN
    -- Captura último: desfaz só o trabalho desta unidade e propaga o ORIGINAL
    ROLLBACK TO sp_<nome>;
    logger.log_error('Erro inesperado em ' || lc_nome_unidade, lc_nome_unidade);
    RAISE;
END;
```

Não troque o erro inesperado por `raise_application_error(-20999, SQLERRM)`:
perde o código Oracle e a pilha, e o chamador não consegue mais tratá-lo.

### Constante `lc_nome_unidade`

Cada procedure tem uma constante local com nome canônico para logging:

```sql
PROCEDURE processar_pagamento IS
  lc_nome_unidade CONSTANT VARCHAR2(60) := gc_nome_pacote || '.processar_pagamento';
BEGIN
  ...
EXCEPTION
  WHEN OTHERS THEN
    log_error(lc_nome_unidade, SQLERRM);
    RAISE;
END;
```

Permite rastrear exatamente onde o erro ocorreu sem depender de stack trace.

### Quando NÃO capturar exceptions

- Não suprima erros que indiquem bug (NO_DATA_FOUND inesperado, ZERO_DIVIDE)
- Não engula `WHEN OTHERS THEN NULL` (anti-pattern absoluto)
- Não capture exception só para re-raise sem adicionar contexto

```sql
-- ANTIPATTERN
EXCEPTION
  WHEN OTHERS THEN NULL;

-- ANTIPATTERN
EXCEPTION
  WHEN OTHERS THEN RAISE;  -- não adicionou nada

-- BOM
EXCEPTION
  WHEN OTHERS THEN
    raise_application_error(-20999, 'Erro em ' || lc_nome_unidade || ': ' || SQLERRM);
```

## Cursores

### Implícito (preferencial para casos simples)

```sql
SELECT col1, col2 INTO l_var1, l_var2 FROM tab WHERE id = p_id;
```

Usa `NO_DATA_FOUND` / `TOO_MANY_ROWS` automaticamente.

### Explícito (para múltiplas linhas com lógica)

```sql
DECLARE
  CURSOR co_usuarios_ativos IS
    SELECT id_usuario, ultimo_login FROM usuarios WHERE status = 'ATIVO';
  r_usuario co_usuarios_ativos%ROWTYPE;
BEGIN
  OPEN co_usuarios_ativos;
  LOOP
    FETCH co_usuarios_ativos INTO r_usuario;
    EXIT WHEN co_usuarios_ativos%NOTFOUND;

    -- Lógica
  END LOOP;
  CLOSE co_usuarios_ativos;
END;
```

### Cursor FOR loop (sintaxe limpa, evita BULK)

```sql
FOR r_usuario IN (SELECT id_usuario, ultimo_login FROM usuarios WHERE status = 'ATIVO') LOOP
  -- Lógica
END LOOP;
```

**Apenas para lógica leve.** Para operações em volume, use BULK.

## Bulk processing

Quando processar muitas linhas, **sempre** use bulk:

```sql
DECLARE
  TYPE t_lista_ids IS TABLE OF usuarios.id_usuario%TYPE;
  l_ids_usuarios t_lista_ids;
BEGIN
  -- BULK COLLECT
  SELECT id_usuario BULK COLLECT INTO l_ids_usuarios
    FROM usuarios
   WHERE status = 'ATIVO';

  -- FORALL para DML
  FORALL i IN l_ids_usuarios.FIRST..l_ids_usuarios.LAST
    UPDATE usuarios SET ultimo_processamento = SYSDATE
     WHERE id_usuario = l_ids_usuarios(i);

  COMMIT;
END;
```

### LIMIT em BULK COLLECT

Para tabelas grandes, processe em chunks:

```sql
DECLARE
  CURSOR co_usuarios IS SELECT id_usuario FROM usuarios WHERE status = 'ATIVO';
  TYPE t_lista_ids IS TABLE OF NUMBER;
  l_ids t_id_tab;
  lc_limit CONSTANT PLS_INTEGER := 1000;
BEGIN
  OPEN co_usuarios;
  LOOP
    FETCH co_usuarios BULK COLLECT INTO l_ids LIMIT lc_limit;
    EXIT WHEN l_ids.COUNT = 0;

    FORALL i IN l_ids.FIRST..l_ids.LAST
      UPDATE outra_tabela SET ... WHERE id = l_ids(i);

    COMMIT;
  END LOOP;
  CLOSE co_usuarios;
END;
```

## Transações

### Princípios

- **Uma unidade lógica = uma transação.** Não commit dentro de loop sem razão.
- **Procedures não comitam.** Rotina reutilizável não faz `COMMIT` nem `ROLLBACK` total (autonomous transaction de log é a exceção).
- **Desfaça só a sua unidade:** `SAVEPOINT` no início e `ROLLBACK TO` no handler, seguido de `RAISE`. Um `ROLLBACK` total desfaria também o trabalho do chamador.
- **Dono da transação:** `COMMIT`/`ROLLBACK` total só no ponto de entrada (job, endpoint, script de carga), documentado no cabeçalho. No APEX, o dono é o próprio APEX. Detalhes: regra 4 da `oracle-plsql-ptbr`.

### Autonomous transaction

Use **apenas** para logging/auditoria que precisa persistir mesmo se transação principal falhar:

```sql
PROCEDURE registrar_evento(p_msg IN VARCHAR2) IS
  PRAGMA AUTONOMOUS_TRANSACTION;
BEGIN
  INSERT INTO log_eventos(msg, criado_em) VALUES (p_msg, SYSDATE);
  COMMIT;  -- obrigatório em autonomous
EXCEPTION
  WHEN OTHERS THEN
    ROLLBACK;
    NULL;  -- log de log não deve quebrar fluxo principal
END;
```

## Comentários

### Comentário de package/procedure (Javadoc-like)

```sql
/**
 * Processa pagamento de uma fatura.
 *
 * Aplica regras de multa e juros conforme tabela de configuração.
 * Atualiza status para PAGO e cria registro em historico_pagamentos.
 *
 * @param p_id_fatura  ID da fatura
 * @param p_data_pagamento  Data do pagamento (default SYSDATE)
 *
 * @raises e_fatura_nao_encontrada  Fatura não existe
 * @raises e_fatura_ja_paga          Fatura já foi paga
 */
PROCEDURE processar_pagamento(
  p_id_fatura IN NUMBER,
  p_data_pagamento IN DATE DEFAULT SYSDATE
);
```

### Comentário inline

Explica **por quê**, nunca **o quê**:

```sql
-- RUIM
l_total := l_total + r.valor;  -- soma o valor

-- BOM
l_total := l_total + r.valor;  -- soma apenas se categoria = "operacional" (regra fiscal IRPJ)
```

### Comentário de bloco

```sql
-- ============================================================
-- Validação de elegibilidade
--
-- Regras conforme NORMA-2024-15:
--   1. Cliente deve estar ativo há > 12 meses
--   2. Não pode ter pendência fiscal aberta
--   3. Volume mensal > limite mínimo (parametrizável)
-- ============================================================
```

## Antipatterns Trivadis-explicit

| Antipattern | Por quê é ruim |
|---|---|
| SQL dinâmico com concatenação | SQL injection + hard parse |
| Loop linha-a-linha em grandes volumes | Performance terrível |
| `WHEN OTHERS THEN NULL` | Mascara bugs |
| Variáveis globais sem necessidade | Side effects difíceis de rastrear |
| Comentário que repete o código | Ruído visual |
| Nomes em português abreviados | `proc_p_p` ilegível 1 mês depois |
| `GOTO` | Sempre há alternativa estruturada |
| Triggers com lógica complexa | Vire procedure, chame do trigger |

## Linkagem com outros recursos

Esta skill documenta o padrão (sem assets próprios). Os templates de código que
aplicam Trivadis vivem nas skills irmãs:

- Templates PL/SQL (package header/body, exception, bulk) → skill **oracle-plsql-ptbr** (`assets/`)
- Padrões APEX → skill **oracle-apex-ptbr** (`references/apex-patterns.md`)
- Padrões ORDS → skill **oracle-ords-ptbr**
- Operação/diagnóstico (lock, sessão, objetos inválidos) → skill **oracle-dba-ptbr**
- Análise de performance → skill **oracle-tuning-ptbr**
