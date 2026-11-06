---
name: oracle-26ai-ptbr
description: "Módulo 26ai da suíte Oracle PT-BR. Novidades de Oracle Database 23ai/26ai (SQL, PL/SQL, segurança, JSON, migração) isoladas do restante da suíte, que é 19c. ATIVE quando a versão-alvo declarada for 23ai ou 26ai, ou em perguntas sobre migrar de 19c para 26ai, o que muda no código, backports 19.28 (IF NOT EXISTS, Annotations, DBMS_DEVELOPER), BOOLEAN em SQL, SELECT sem FROM, UPDATE/DELETE com JOIN, RETURNING OLD/NEW, GROUP BY ALL, INSERT BY NAME, QUALIFY, FILTER, calendar functions, UUID(), Domains, Assertions, RESETTABLE, transpiler PL/SQL→SQL, lock-free reservations, priority transactions, JSON duality views, schema privileges, SQL Firewall, MLE JavaScript, Vector Search, AutoUpgrade. Frases — 'estou no 26ai', 'quando migrarmos pro 26', 'isso existe no 26ai?', 'dá pra usar no 19c?'. NÃO ATIVE quando a versão for 19c ou não estiver declarada — o módulo específico responde em 19c e só cita esta skill se houver alternativa 26ai relevante."
metadata:
  version: "1.0.2"
  release_date: "2026-09-15"
  repository: "https://github.com/maxwbh/oracle-skills-ptbr"
  suite_size: 6
  author: "Maxwell da Silva Oliveira"
  contact: "contato@msbrasil.inf.br"
  organization: "M&S do Brasil LTDA"
  site: "https://msbrasil.inf.br"
  tags:
    - "oracle"
    - "26ai"
    - "23ai"
    - "migration"
    - "sql"
    - "plsql"
    - "json"
  category: "database"
  language: "pt-BR"
  icon: "🧭"
---

# Suíte Oracle PT-BR — Módulo 26ai (oracle-26ai-ptbr)

> **Versão:** 1.0.2 · **Atualizada em:** setembro/2026 · **Repositório:** oracle-skills-ptbr · **Suíte:** 10 skills (6 recursos nesta skill)
> **v1.0.2:** suíte com 10 skills; referência cruzada para subir um 26ai Free local e testar a sintaxe nova. Histórico em `CHANGELOG.md`.

Suíte completa (10 skills — conjunto único): ver `oracle-core-ptbr`.

Novidades de **Oracle Database 23ai/26ai** organizadas pelo que muda na prática para quem escreve SQL/PL/SQL e mantém sistemas hoje em **19c**. 26ai é o *long term release* sucessor do 19c; 23ai → 26ai é patch, não upgrade.

**Desenvolvido por:** Maxwell da Silva Oliveira — [M&S do Brasil LTDA](https://msbrasil.inf.br)

## Por que uma skill separada

Cerca de 90% do trabalho da suíte roda em 19c. Se as sintaxes novas ficassem espalhadas nos módulos, o Claude passaria a sugerir `IF NOT EXISTS`, `BOOLEAN` em coluna ou `UPDATE … FROM` para bancos que não aceitam. Esta skill concentra o material 26ai e os outros módulos **só a citam** quando a versão-alvo for declarada. Regra da suíte: **na dúvida, 19c**.

## Áreas cobertas

| Área | Reference | Assets |
|---|---|---|
| **SQL novo** (DDL, DML, consulta, JSON) | `references/novidades-sql-26ai-ptbr.md` | `exemplos_sql_26ai.sql` |
| **PL/SQL, segurança e plataforma** | `references/novidades-plsql-plataforma-26ai-ptbr.md` | `exemplos_plsql_26ai.sql` |
| **Migração 19c → 26ai** (caminhos, compatibilidade, checklist de código) | `references/migracao-19c-para-26ai-ptbr.md` | (checklist embutido no reference) |

## Quando ativar

- Usuário declara versão 23ai/26ai ("estou no 26ai", "banco Free 26ai", "ADB")
- Planejamento ou execução de upgrade 19c/21c → 26ai (AutoUpgrade, non-CDB → PDB)
- "Isso existe no 26ai?" / "dá pra fazer mais simples na versão nova?"
- Confirmar se uma feature foi **backportada para 19c** (19.16, 19.28)
- Código que depende de versão em APEX 26.1 (session state BOOLEAN exige banco 26ai) ou ORDS 26.1 (VecDB REST APIs)

**Não usar** quando a versão é 19c ou não foi informada: o módulo técnico responde em 19c. Se houver uma alternativa 26ai claramente melhor, ele acrescenta **uma linha** "no 26ai: …" apontando para cá — não gera o código 26ai por conta própria.

## Regra — confirmar a versão-alvo

Antes de gerar código com sintaxe 23ai/26ai, a versão precisa estar explícita na conversa. Se não estiver, faça UMA pergunta curta ("Qual a versão do banco — 19c ou 26ai?"). Se já foi informada, não pergunte de novo; apenas marque no código o que é exclusivo (`-- 26ai`).

## O que já existe em 19c (backports) — use sem medo

| Feature | 19c a partir de | Nota |
|---|---|---|
| `IF [NOT] EXISTS` em DDL | **19.28** | Elimina blocos `BEGIN EXECUTE IMMEDIATE … EXCEPTION WHEN OTHERS` em scripts GMUD |
| Annotations (`ANNOTATIONS (…)`) | **19.28** | Metadados chave/valor em tabelas, colunas, views, domains |
| `DBMS_DEVELOPER.get_metadata` (JSON) | **19.28** | Metadata de objeto em JSON — útil em ferramentas/skills |
| `UTL_HTTP.set_wallet('system:')` | 19.16 | Usa o certificate store do SO (TLS sem wallet, variante) |

Cheque o RU: `SELECT version_full FROM v$instance;`.

## Resumo — 19c vs 26ai, como escrever hoje

| Você quer | Em 19c | Em 26ai |
|---|---|---|
| Flag sim/não em coluna | `NUMBER(1)` + `CHECK (x IN (0,1))` | `BOOLEAN` nativo (aceita `true`, `'Y'`, `1`…) |
| Criar objeto só se não existir | bloco PL/SQL com tratamento de erro (ou `IF NOT EXISTS` em 19.28+) | `CREATE TABLE IF NOT EXISTS` |
| Constante/expressão sem tabela | `SELECT … FROM dual` | `SELECT …` (sem FROM) |
| UPDATE a partir de outra tabela | `MERGE` ou subquery correlacionada | `UPDATE t1 a SET … FROM t2 b WHERE a.id = b.id` |
| Valor antigo e novo após DML | `SELECT` antes + `RETURNING` | `RETURNING OLD col, NEW col INTO …` |
| Múltiplas linhas literais | `INSERT ALL` / `UNION ALL` de `dual` | `VALUES (…), (…), (…)` (table values constructor) |
| Filtrar por função analítica | subquery inline | `QUALIFY` (26ai) |
| Contagem condicional | `COUNT(CASE WHEN … THEN 1 END)` | `COUNT(*) FILTER (WHERE …)` (26ai) |
| Início/fim de mês, semana, trimestre | `TRUNC`/`LAST_DAY`/`NEXT_DAY` | `CALENDAR_MONTH_START_DATE` etc. (26ai) |
| ID único não previsível | `SYS_GUID()` | `UUID()` (23.9+) |
| Regra de domínio reutilizável (e-mail, CPF) | `CHECK` repetido por tabela | `CREATE DOMAIN` + `annotations` |
| Contador concorrente sem lock | fila/tabela auxiliar | coluna `RESERVABLE` (lock-free reservations) |
| Evitar `ORA-04068` após recompilar package | `DBMS_SESSION.reset_package` / nova sessão | `PACKAGE … RESETTABLE` (26ai) |
| Grant em todos os objetos de um schema | grants objeto a objeto (ou script) | `GRANT SELECT ANY TABLE ON SCHEMA x TO y` |
| Documento JSON sobre tabelas relacionais | `JSON_OBJECT` em view | `JSON RELATIONAL DUALITY VIEW` (leitura e escrita) |

Detalhes, restrições e exemplos completos nos references.

## Princípios canônicos

1. **19c é o padrão da suíte.** Sintaxe 26ai só com versão declarada; marque `-- 26ai` no código.
2. **Backport primeiro.** Se a feature existe em 19.28 (IF NOT EXISTS, Annotations), prefira-a à emulação — mas confirme o RU do cliente.
3. **BOOLEAN nativo ≠ BOOLEAN do APEX.** Colunas `BOOLEAN` funcionam em qualquer 23ai+; *session state* BOOLEAN no APEX 26.1 exige banco 26ai e ORDS 26.1.1+. Em items APEX de bancos 19c, continue com `'Y'/'N'`.
4. **Priority transactions: o default é `TXN_PRIORITY = HIGH`** para todas as sessões — nada é rollbackado até você baixar a prioridade de sessões de lote. Não ative `PRIORITY_TXNS_MODE = ROLLBACK` em produção sem período em `TRACK`.
5. **Duality views são API, não atalho.** Exigem PK/FK íntegras e definem quais tabelas aceitam `INSERT/UPDATE/DELETE`; não substituem package de negócio.
6. **Transpiler PL/SQL→SQL é automático, mas limitado.** Só funções simples (sem SQL interno, loops, exceções) são transpiladas; `SQL_TRANSPILER = ON` na sessão para testar. Continue aplicando "SQL puro antes de PL/SQL".
7. **Non-CDB acabou.** 26ai só existe como CDB/PDB; todo plano de upgrade 19c non-CDB inclui conversão para PDB (AutoUpgrade faz).
8. **Naming Trivadis 4.4 + PT-BR continua valendo.** O Trivadis foi encerrado na 4.4 (fev/2026); para objetos novos a referência de naming é o bloco G-92xx do **dbLinter** (sucessor oficial) — ex.: G-9208 assertions. Domains, assertions e annotations recebem nomes PT-BR como qualquer objeto (`dom_email`, `asr_salario_presidente`). Detalhes em `oracle-trivadis-ptbr`.

## Referências cruzadas

| Precisa de | Skill |
|---|---|
| Gerar packages/procedures (19c ou 26ai com versão declarada) | **oracle-plsql-ptbr** |
| Naming e revisão Trivadis | **oracle-trivadis-ptbr** |
| APEX 26.1 e dependências de versão de banco | **oracle-apex-ptbr** |
| ORDS 26.1 (VecDB, export com DROP, APEXlang) | **oracle-ords-ptbr** |
| Upgrade operacional: AutoUpgrade, PDB, Data Guard | **oracle-dba-ptbr** |
| Plano de execução, stats, transpiler na prática | **oracle-tuning-ptbr** |
| Scripts GMUD idempotentes com `IF NOT EXISTS` | **oracle-devops-ptbr** |
| Subir um 26ai Free local para testar a sintaxe nova | **oracle-lab-ptbr** |
