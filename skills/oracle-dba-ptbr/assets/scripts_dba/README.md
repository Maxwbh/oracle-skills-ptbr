# Scripts DBA ad-hoc

Utilitários SQL curtos para **diagnose pontual** em `sqlplus` / `SQLcl`. Estilo Tim Hall: cabeçalho padrão, formatação configurada, prontos para `@<nome>`.

## Crédito

Todos os scripts são **adaptações em PT-BR** dos scripts originais publicados por **Tim Hall** em [oracle-base.com/dba/scripts](https://oracle-base.com/dba/scripts). O cabeçalho de cada arquivo preserva o link para a fonte original.

## Diferença vs `assets/*.sql`

| `assets/<template>.sql` | `assets/scripts_dba/<script>.sql` |
|---|---|
| Esqueleto para clonar e adaptar em pacotes | Comando pronto para rodar |
| Foco em construção (PL/SQL completo) | Foco em diagnose (1 query) |
| Naming Trivadis, exception handler, lc_nome_unidade | Estilo Tim Hall: SET LINESIZE, COLUMN FORMAT |

## Índice

| Arquivo | Para que serve |
|---|---|
| `locked_objects.sql` | Lista locks ativos (sessão, owner, objeto, modo) |
| `lock_tree.sql` | Hierarquia de bloqueios — identifica a sessão "root" |
| `top_sessions.sql` | Top 30 sessões por CPU/IO/redo no momento |
| `longops.sql` | Operações longas em andamento (% completo, ETA) |
| `invalid_objects_quick.sql` | Lista rápida de objetos inválidos por schema |
| `redo_by_hour.sql` | Volume de redo por hora nos últimos 7 dias |
| `index_usage.sql` | Índices monitorados + se foram usados (ALTER INDEX MONITORING USAGE) |
| `session_pga.sql` | Uso de PGA por sessão — investiga OOM, BULK COLLECT sem LIMIT, NOCOPY ausente |

## Como usar

Em `sqlplus` ou `SQLcl`, conectado como usuário com privilégios DBA ou em V$ views:

```sql
SQL> @assets/scripts_dba/locked_objects
SQL> @assets/scripts_dba/lock_tree
SQL> @assets/scripts_dba/top_sessions
```

Para `dba_objects` em vez de `user_objects`, o usuário precisa do papel `SELECT_CATALOG_ROLE` ou privilégio direto.
