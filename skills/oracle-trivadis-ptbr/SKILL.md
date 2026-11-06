---
name: oracle-trivadis-ptbr
description: Módulo de padrões Trivadis da suíte Oracle PT-BR. Trivadis PL/SQL Guidelines 4.4 — nomenclatura, estrutura de código e revisão. ATIVE em revisar código Oracle com padrão Trivadis, validar prefixos (g_, gc_, l_, lc_, p_, r_, t_, co_, e_), naming PT-BR em variáveis/tabelas/colunas, checklist antes de deploy/GMUD, "esse código segue Trivadis?", "qual prefixo usar?", "como nomear essa variável?", "revisa esse package", dbLinter, db* CODECOP, IslandSQL, regras G-92xx (naming de tabelas/constraints/assertions), "Trivadis ainda existe?". NÃO ATIVE em geração de código (use oracle-plsql-ptbr), APEX development, ORDS endpoints, DBA operacional, tuning. As demais oracle-*-ptbr aplicam Trivadis automaticamente — esta skill foca em consultas e revisões explícitas do padrão.
metadata:
  version: "2.4.0"
  release_date: "2026-11-06"
  repository: "https://github.com/maxwbh/oracle-skills-ptbr"
  suite_size: 2
  author: "Maxwell da Silva Oliveira"
  contact: "contato@msbrasil.inf.br"
  organization: "M&S do Brasil LTDA"
  site: "https://msbrasil.inf.br"
  tags:
    - "oracle"
    - "trivadis"
    - "coding-standards"
    - "naming-conventions"
    - "plsql"
    - "code-review"
  category: "development"
  language: "pt-BR"
  icon: "📐"
---

# Suíte Oracle PT-BR — Módulo Padrões Trivadis (oracle-trivadis-ptbr)

> **Versão:** 2.4.0 · **Atualizada em:** novembro/2026 · **Repositório:** oracle-skills-ptbr · **Suíte:** 10 skills (2 recursos nesta skill)
> **v2.3.1:** suíte com 10 skills (oracle-lab-ptbr). Histórico em `CHANGELOG.md`.

Suíte completa (10 skills — conjunto único):
- **oracle-core-ptbr** — roteamento central, convenções transversais, cenários multidisciplinares
- **oracle-plsql-ptbr** — PL/SQL 19c: packages, BULK, LOBs, triggers, EBR
- **oracle-trivadis-ptbr** — Trivadis 4.4: naming, prefixos, revisão de código
- **oracle-apex-ptbr** — APEX 26.1: páginas, DA, IG, APIs APEX_*, metadata
- **oracle-ords-ptbr** — ORDS: REST modules/handlers, OAuth, Network ACL
- **oracle-dba-ptbr** — DBA operacional: sessões, locks, flashback, scripts ad-hoc
- **oracle-tuning-ptbr** — performance: explain plan, índices, stats, result cache
- **oracle-devops-ptbr** — Git/CI-CD: estrutura, Liquibase, pipelines, GMUD
- **oracle-26ai-ptbr** — 23ai/26ai: novidades SQL/PL/SQL, backports 19.28, migração 19c→26ai (só com versão declarada)
- **oracle-lab-ptbr** — instalação e ambiente local (VM/container) para quem não é DBA; rede de casa


Trivadis PL/SQL Guidelines 4.4 — padrão de nomenclatura, estrutura de código e checklist de revisão.

**Desenvolvido por:** Maxwell da Silva Oliveira — [M&S do Brasil LTDA](https://msbrasil.inf.br)

## Áreas cobertas

| Área | Reference |
|---|---|
| **Trivadis Guidelines 4.4** | `references/plsql-trivadis-guidelines.md` |

> **Referência cruzada:** Esta skill documenta o padrão. As skills `oracle-plsql-ptbr`, `oracle-apex-ptbr`, `oracle-ords-ptbr`, `oracle-dba-ptbr` e `oracle-tuning-ptbr` aplicam Trivadis automaticamente em todo código gerado.

## Quando ativar

- "Esse código segue Trivadis?" — revisão explícita de padrão
- "Qual prefixo usar para essa variável/cursor/constante?"
- "Como nomear essa tabela/coluna/package em PT-BR?"
- Checklist pré-deploy / pré-GMUD: validar naming antes de subir para produção
- Auditoria de código legado: identificar desvios do padrão
- Dúvidas sobre convenções: exceções locais vs globais, packages nativos Oracle em inglês, status values em PT-BR

**Não usar** para: geração de código PL/SQL (→ oracle-plsql-ptbr), APEX, ORDS, DBA ops, tuning.

## Prefixos canônicos (dialeto local desta base)

Esta base usa um **dialeto local** do Trivadis. Os dois desvios conscientes do
padrão oficial estão marcados; detalhe e tabela oficial completa (regras
G-9101–9115) em `references/plsql-trivadis-guidelines.md`.

| Prefixo | Uso | Oficial Trivadis | Exemplo |
|---|---|---|---|
| `g_` | Variável global (package) | igual | `g_ultima_execucao` |
| `gc_` | Constante global (package) | ⚠ oficial: `co_` | `gc_nome_pacote` |
| `l_` | Variável local | igual | `l_total_pago` |
| `lc_` | Constante local | ⚠ oficial: `co_` | `lc_nome_unidade` |
| `p_` | Parâmetro | igual (`in_`/`out_`/`io_` p/ direção) | `p_id_fatura` |
| `r_` | Record (instância) | igual | `r_fatura` |
| `t_` | Collection/type (instância) | igual | `t_lista_ids` |
| `co_` | Cursor | ⚠ oficial: `c_` (`co_`=constante) | `co_faturas_pendentes` |
| `e_` | Exception user-defined | igual | `e_estado_invalido` |

> **Desvios locais:** o oficial usa `co_` para constante e `c_` para cursor.
> Esta base usa `gc_`/`lc_` para constantes (indicando escopo) e libera `co_`
> para cursor. **Não existe `gco_`** — se aparecer, é desvio a corrigir.
> Convenções oficiais sem divergência também aplicáveis: `in_`/`out_`/`io_`
> (parâmetros por direção), `o_` (object), sufixo `_type` em definições de tipo.

## Checklist de revisão — o que verificar

1. **Naming:** variáveis, procedures, functions, tabelas e colunas em PT-BR (exceto keywords Oracle, pacotes nativos, prefixos Trivadis)
2. **Prefixos Trivadis:** `g_`, `gc_`, `l_`, `lc_`, `p_`, `r_`, `t_`, `co_`, `e_` aplicados corretamente
3. **Keywords em inglês:** `BEGIN`, `END`, `EXCEPTION`, `BULK COLLECT`, `FORALL`, `MERGE INTO` nunca traduzidos
4. **Pacotes nativos em inglês:** `DBMS_LOB`, `APEX_JSON`, `UTL_HTTP`, `DBMS_STATS` nunca traduzidos
5. **`lc_nome_unidade`** declarado em toda procedure pública
6. **`gc_nome_pacote`** declarado no package body
7. **Comentários em PT-BR** — explicam o PORQUÊ, não o QUÊ
8. **Status values em PT-BR:** `'PENDENTE'`, `'PAGO'`, `'CANCELADO'`, `'ATIVO'`, `'PROCESSADO'`
9. **`WHEN OTHERS THEN NULL`** ausente — sempre propagar com contexto
10. **`DBMS_OUTPUT`** ausente em produção — substituído por Logger

## O que fica em inglês obrigatoriamente

| Categoria | Exemplos |
|---|---|
| Keywords SQL/PL/SQL | `BEGIN`, `END`, `EXCEPTION`, `BULK COLLECT`, `FORALL`, `RETURN`, `IS`, `AS` |
| Pacotes Oracle nativos | `DBMS_LOB`, `DBMS_OUTPUT`, `DBMS_STATS`, `APEX_JSON`, `UTL_HTTP` |
| Funções built-in | `SYSDATE`, `NVL`, `COALESCE`, `TO_DATE`, `INSTR`, `SUBSTR` |
| Variáveis sistema APEX | `:APP_USER`, `:APP_SESSION`, `:APP_ID` |
| Hints | `/*+ APPEND */`, `/*+ PARALLEL */`, `/*+ INDEX */` |
| Prefixos Trivadis | `g_`, `gc_`, `l_`, `lc_`, `p_`, `r_`, `t_`, `co_`, `e_` |

## Sucessão do padrão — dbLinter (2026)

O repositório Trivadis e a suíte db* CODECOP foram **arquivados em 02/02/2026**; a **4.4 (mar/2024) é a versão final** — não existe "Trivadis para 26ai". O sucessor mantido pelo mesmo autor (Philipp Salvisberg, com Grisselbav/United Codes) é o **dbLinter**: 198 regras que incluem todas as G-xxxx do 4.4 com a mesma numeração, mais regras novas; parser IslandSQL atualizado a cada RU do banco (hoje SQL/PL/SQL 26ai 23.26.x, SQLcl 26.2). Catálogo público: grisselbav.github.io/dbLinter e dblinter.app.

Como a suíte usa isso:
- O nome do padrão continua **"Trivadis 4.4"** — nada foi revogado, só houve adições.
- Para objetos e sintaxes que o 4.4 não cobre (assertions, domains, hints, APEX), a referência de naming passa a ser o bloco **G-92xx** do dbLinter: G-9201/9202 tabelas/colunas · G-9203 índices · G-9204–9207 PK/UK/FK/CHECK · **G-9208 assertions** · G-9209 GTT · G-9210–9213 views/sequences/synonyms/triggers · G-9214–9216 packages/functions/procedures · G-9217–9219 object/collection types · G-9116 campos de record. Os prefixos são configuráveis por tenant — o dialeto PT-BR desta base (`tb_`, `vw_`, `sq_`, `syn_`, `trg_`, `pkg_`, `prc_`, `fnc_`, `tp_`, `dom_`, `asr_`) é registrável como configuração.
- Regras novas que valem adotar já em 19c: G-3145 (`SELECT *` direto de tabela), G-3185 (ROWNUM no mesmo nível de ORDER BY), G-3194 (INNER/OUTER explícito), G-7127 (`CREATE VIEW … FORCE`), G-7515 (prefixar tipos Oracle com owner, ex.: `sys.dbms_lob`), G-9501 (parâmetro nunca direto em string de SQL dinâmico — copiar para variável local via `DBMS_ASSERT`), G-96xx (hints válidos, com alias, um só comentário).
- Ferramenta: extensão VS Code (grátis nos planos Anonymous/Starter), CLI e plugin SonarQube — candidatos a *quality gate* no pipeline (`oracle-devops-ptbr`). Marcador de exceção: `-- @dbLinter ignore(G-xxxx): motivo`.
- Regras APEX `A-0700…A-1410` (session state protection, page access protection, alias de página, iframe, naming de items, authorization scheme, session lifetime) — checklist pré-deploy em `oracle-apex-ptbr`.

## Referências cruzadas

| Precisa de | Skill |
|---|---|
| Geração de código PL/SQL, packages | **oracle-plsql-ptbr** |
| Código dentro de APEX processes | **oracle-apex-ptbr** |
| Código dentro de ORDS handlers | **oracle-ords-ptbr** |
| Scripts DBA com padrão Trivadis | **oracle-dba-ptbr** |
