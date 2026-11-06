# Migração 19c → 26ai — caminhos, compatibilidade e checklist de código

Guia para planejar a saída do 19c (long term release atual) para o 26ai (próximo long term). Foco no que um time de desenvolvimento Oracle/APEX/ORDS precisa decidir; o passo a passo operacional do upgrade fica com `oracle-dba-ptbr`.

## Índice

- [1. Posicionamento das versões](#1-posicionamento-das-versões)
- [2. Caminhos de upgrade](#2-caminhos-de-upgrade)
- [3. Matriz de compatibilidade APEX / ORDS / SQLcl](#3-matriz-de-compatibilidade-apex--ords--sqlcl)
- [4. Checklist de código 19c → 26ai](#4-checklist-de-código-19c--26ai)
- [5. Armadilhas conhecidas](#5-armadilhas-conhecidas)
- [6. Estratégia de código dual (19c hoje, 26ai amanhã)](#6-estratégia-de-código-dual-19c-hoje-26ai-amanhã)
- [7. Roteiro sugerido](#7-roteiro-sugerido)

---

## 1. Posicionamento das versões

| Versão | Papel | Observação |
|---|---|---|
| **19c** | Long term release em uso na maioria dos clientes | Recebe RUs trimestrais; features 23ai backportadas em 19.16 (TLS `system:`) e 19.28 (IF NOT EXISTS, Annotations, DBMS_DEVELOPER). Confirme datas de fim de suporte no MOS (Doc 742060.1) — mudaram mais de uma vez |
| 21c | Innovation release | Não é destino; serve só como degrau de upgrade |
| 23ai | Base do 26ai | 23ai → 26ai é **patch** (23.26.x), não upgrade completo. Versão Free existe para laboratório |
| **26ai** | Long term release sucessor do 19c | "Oracle AI Database 26ai"; numeração interna 23.26.x |

## 2. Caminhos de upgrade

- **Direto para 26ai:** apenas de **19c e 21c**. Versões anteriores passam por 19c primeiro (`11.2.0.4 → 19c → 26ai`; `10.2 → 12.2 → 19c → 26ai`).
- **Non-CDB foi desuportado em 21c:** não existe 26ai non-CDB. Todo 19c non-CDB vira PDB dentro de um CDB 26ai — o AutoUpgrade converte automaticamente ao abrir a PDB.
- **Ferramenta:** `autoupgrade.jar` (baixe sempre o mais recente do MOS 2485457.1, substitua o que veio no `$ORACLE_HOME/rdbms/admin`). Modos `-mode analyze` → `fixups` → `deploy`. DBUA existe, mas o padrão da comunidade é AutoUpgrade.
- **Cenários típicos:**
  1. CDB 19c com PDBs → upgrade do CDB inteiro (AutoUpgrade `deploy`).
  2. Unplug de uma PDB 19c → plug em CDB 26ai (AutoUpgrade unplug/plugin) — permite migrar um cliente por vez.
  3. Non-CDB 19c → PDB em CDB 26ai (conversão + upgrade no `OPEN`).
- **Read-only Oracle Home** é o default em 21c+: arquivos de configuração (`sqlnet.ora`, `tnsnames.ora`, `spfile`) saem do `$ORACLE_HOME` para `ORACLE_BASE_HOME`/`ORACLE_BASE_CONFIG` — ajuste scripts e pipelines que assumem caminhos fixos.
- **Antes:** `DBMS_HCHECK.full` no 19c, backup RMAN validado, `AUDIT_TRAIL` tradicional migrado para Unified Audit, objetos inválidos zerados (`oracle-dba-ptbr`).

## 3. Matriz de compatibilidade APEX / ORDS / SQLcl

| Componente | Requisito com banco 26ai | Notas |
|---|---|---|
| APEX 26.1 | Banco ≥ 23.26.0 (out/2025) quando em 26ai; 19c ≥ 19.18 também suportado | Session state BOOLEAN só com banco 26ai; Universal Theme 26.1 |
| APEX 24.2 / 24.1 | Suportados até jul/2027 e dez/2026 | Não exploram BOOLEAN nativo em session state |
| ORDS 26.1.x | Exigido pelo APEX 26.1 (ORDS ≥ versão do APEX); 26.1.1 obrigatório para APEXlang | VecDB REST APIs exigem 23.26.1+; export gera `DROP` de objetos removidos |
| ORDS 26.4 (previsto inverno/2026) | Tomcat 10 / WebLogic 15 obrigatórios | Tomcat 9 deixa de ser suportado — planejar servidor de aplicação junto com o banco |
| SQLcl | Atual (26.x); `lb` Liquibase embutido, `apex export -split`, `ARGUMENT` | Compatível com 19c e 26ai |
| Drivers | `oracledb` (Python) Thin, JDBC 23ai+ para BOOLEAN/JSON/VECTOR nativos | Driver antigo mapeia BOOLEAN como NUMBER — teste `export_db.py`/`deploy_db.py` (`oracle-devops-ptbr`) |
| Instant Client | 23ai+ para TLS sem wallet e novos tipos | 19c client conecta em 26ai, sem os tipos novos |

## 4. Checklist de código 19c → 26ai

Nada obrigatório quebra sintaxe válida de 19c; o checklist é de **oportunidade** e de **comportamento**.

**Comportamento (verificar antes do go-live)**
- [ ] `TXN_PRIORITY` default `HIGH` — só importa se alguém mudar; confirmar que nenhum script de lote setou `LOW` sem tratamento de `ORA-63302`.
- [ ] `JSON_BEHAVIOR` — validar retornos de `JSON_VALUE`/`JSON_QUERY` em código que dependia de `NULL ON ERROR` implícito.
- [ ] Tablespaces novas são **bigfile** por default — scripts que criam tablespaces smallfile por convenção precisam do `SMALLFILE` explícito.
- [ ] Trilha de auditoria tradicional desuportada — jobs que leem `DBA_AUDIT_TRAIL` migram para `UNIFIED_AUDIT_TRAIL`.
- [ ] Packages com estado: avaliar `RESETTABLE` nos que causam `ORA-04068` em deploy.
- [ ] `RESOURCE` role ganhou privilégios (`CREATE PROPERTY GRAPH`, `CREATE ANALYTIC VIEW`, …) — revisar usuários de aplicação que a recebem; preferir grants explícitos ou `DB_DEVELOPER_ROLE` só em dev.
- [ ] ORDS: `OAUTH`/`OAUTH_ADMIN` já removidos desde 25.3 — se o ORDS subir junto com o banco, o código de clientes OAuth precisa estar em `ORDS_SECURITY`.

**Oportunidade (adotar por release, não tudo de uma vez)**
- [ ] Scripts GMUD → `IF [NOT] EXISTS` (já em 19.28).
- [ ] Flags `NUMBER(1)`/`'S'/'N'` → `BOOLEAN` **apenas em tabelas novas**; migrar colunas existentes exige revisar APEX items, ORDS handlers e integrações (`'S'/'N'` não é literal BOOLEAN válido).
- [ ] `MERGE` só-UPDATE → `UPDATE … FROM`.
- [ ] Auditoria de valor anterior → `RETURNING OLD/NEW`.
- [ ] Regras repetidas de formato (e-mail, CPF/CNPJ, CEP) → `DOMAIN`.
- [ ] Grants pós-deploy → schema privileges.
- [ ] Contadores concorrentes → `RESERVABLE`.
- [ ] APIs JSON de leitura/escrita simples → duality view + AutoREST.

## 5. Armadilhas conhecidas

- **Literal BOOLEAN em português não existe.** `'S'`, `'N'`, `'sim'`, `'nao'` lançam erro. Padronize `'Y'/'N'` na fronteira (APEX, ORDS, CSV) e `TRUE/FALSE` no banco.
- **`UPDATE … FROM` com join não único** atualiza com valor indeterminado, sem erro. Garanta unicidade por constraint ou `GROUP BY`.
- **`GROUP BY ALL` em views:** qualquer coluna adicionada ao `SELECT` muda o agrupamento. Use só em consultas ad hoc.
- **Duality view exige integridade referencial declarada** — tabelas legadas sem FK não servem sem antes criar as constraints (pode ser `RELY NOVALIDATE` enquanto se limpa o dado).
- **Assertions são caras** — reavaliadas por transação; não use para regra de linha.
- **SQL Firewall + APEX:** IR/IG geram SQL variável; capture por semanas antes de `BLOCK`.
- **Read-only Oracle Home** muda caminhos de `tnsnames.ora`/`sqlnet.ora` — pipelines e `oracle_devops_utils.py` que apontam para `$ORACLE_HOME/network/admin` devem usar `$ORACLE_BASE_HOME`.

## 6. Estratégia de código dual (19c hoje, 26ai amanhã)

1. **Escreva 19c.** É o denominador comum e o que roda em produção na maioria dos clientes.
2. **Marque oportunidades**, não implemente: comentário `-- 26ai: UPDATE … FROM` acima do `MERGE`, sem código alternativo no repositório.
3. **Não faça branch por versão** (`IF versao >= 23 THEN EXECUTE IMMEDIATE …`) — dobra o teste e esconde bugs. Exceção: scripts GMUD que rodam em bancos mistos podem checar `v$instance.version_full` para escolher entre `IF NOT EXISTS` e o bloco tradicional.
4. **Isolar por EBR**, não por versão: quando um cliente migrar, a edição nova pode adotar sintaxe 26ai sem tocar na edição em uso.
5. **Testes:** utPLSQL roda igual nas duas versões; adicione um job de CI contra o 26ai Free em container para detectar mudanças de comportamento cedo (`oracle-devops-ptbr`).

## 7. Roteiro sugerido

| Fase | O que fazer | Skill de apoio |
|---|---|---|
| 0 — Laboratório | 26ai Free em container/VM; rodar suíte utPLSQL e smoke tests APEX/ORDS | devops |
| 1 — 19c ao dia | Subir para RU ≥ 19.28; adotar `IF NOT EXISTS` e Annotations já em 19c; Unified Audit | dba, devops |
| 2 — Pré-requisitos de plataforma | ORDS 26.1.x + Tomcat 10; APEX 26.1 no 19c (compatível) — separa o risco de app do risco de banco | apex, ords |
| 3 — Upgrade do banco | AutoUpgrade analyze/fixups/deploy; conversão non-CDB → PDB; `DBMS_HCHECK` antes e depois | dba |
| 4 — Adoção gradual | Um item do checklist de oportunidade por release, sempre em tabelas/objetos novos primeiro | plsql, esta skill |
