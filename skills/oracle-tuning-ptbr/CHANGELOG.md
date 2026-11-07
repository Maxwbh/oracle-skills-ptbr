# Changelog — oracle-tuning-ptbr

## [2.7.0] - 2026-11-06
- Feature — baseline SPM aceito pode ser ignorado (caso relatado no 19c RU 19.32, oracle-base 29/09/2026): etapa 9 do `explain_plan_workflow.sql` confere `V$SQL.SQL_PLAN_BASELINE`, `DBA_SQL_PLAN_BASELINES.REPRODUCED` e o trace `[SQL_Compiler.*]`. Bug/nota MOS: a verificar.
- Docs — roteamento para oracle-26ai-helper-ptbr.

## [2.6.2] - 2026-09-15
- Docs — suíte com 10 skills (oracle-lab-ptbr).

## [2.6.1] - 2026-09-15
- Docs — suíte com 9 skills (oracle-26ai-ptbr).

## [2.6.0] - 2026-09-15
- Fix — "AWR em tempo real" (contradição: DBA_HIST_* é histórico) trocado por "análise AWR/ASH de SQL" na description e no corpo; fronteira com oracle-dba-ptbr explicitada; CRLF→LF em result_cache_pattern.sql; changelog movido para CHANGELOG.md.

## [2.5.0]
- Feature — integração à suíte unificada: identidade "Módulo da suíte Oracle PT-BR" na description, bloco de versão/suíte no corpo, lista das 8 skills e roteamento central via oracle-core-ptbr (nova).

## [2.4.0]
- Feature — novo asset result_cache_pattern.sql: quando usar RESULT_CACHE (dado quase-estático, função cara chamada com poucos valores distintos), anti-patterns (SYSDATE/USER no corpo, side effects, tabela transacional), invalidação e monitoramento. Migrado da geração v1.0.0 (aposentada). suite_size 5→6.

## [2.3.1]
- Docs — adicionado Índice (ToC) em references com +100 linhas (performance-tuning.md); limpeza de artefatos __pycache__. Sem mudança de comportamento.

## [2.3.0]
- Feature — novo reference optimizer-statistics-ptbr.md e asset optimizer_statistics_examples.sql cobrindo em profundidade as estatísticas do optimizer: coleta com DBMS_STATS (auto_sample_size, GATHER AUTO), preferences (GET_PREFS/SET_TABLE_PREFS, hierarquia), histogramas (frequency/top-frequency/height-balanced/hybrid + cálculo de cardinalidade), estatísticas estendidas (column groups), SQL Plan Directives e dynamic statistics, ciclo de vida (lock/pending/restore/retention/report), coleta automática, Optimizer Statistics Advisor e SQL Tuning Advisor/SQL Profile; notas de versão 19c verificadas (optimizer_adaptive_statistics FALSE, AUTO_STAT_EXTENSIONS OFF, high-frequency stats); seção Statistics do performance-tuning.md passou a apontar para o novo material; SKILL.md atualizado (áreas, gatilhos).

## [2.2.0]
- Feature/Fix (tipos de índice) — adicionados Reverse Key e Invisible index (este último o SKILL.md anunciava mas nenhum arquivo cobria), com distinção Invisible (mantido por DML, ignorado pelo optimizer; OPTIMIZER_USE_INVISIBLE_INDEXES) vs Unusable (não mantido, sem segmento); precisado que "covering index" não é um tipo no Oracle (é técnica — índice com todas as colunas da query, sem TABLE ACCESS BY ROWID); alerta de bitmap detalhado (lock de fragmento de rowids → enq: TX/deadlock, só EE); decisão rápida e SKILL.md atualizados.

## [2.1.0]
- Feature — nova seção de Paralelismo (Parallel Execution) no reference: statement-level vs object-level (11.2+), parallel DML desabilitado por padrão (ALTER SESSION ENABLE PARALLEL DML / hint ENABLE_PARALLEL_DML 12.1+), ORA-12841, quando ajuda x atrapalha, conferência via V$PX_SESSION e anti-patterns; entrada do hint PARALLEL na tabela desmembrada em statement/object/NO_PARALLEL; corrigida descrição imprecisa do INDEX FAST FULL SCAN (I/O multibloco, não "em paralelo"); princípio canônico e "quando ativar" do SKILL.md atualizados.

## [2.0.1]
- Fix — v$object_usage (deprecada desde 12.1) trocada por user_object_usage no reference e no asset; status 'ATIVO'→'ACTIVE' em V$SESSION (query de wait events retornava vazio); alinhados nomes de tabela/coluna nos diagnósticos de stats (CUSTOMERS/INVOICES→CLIENTES/FATURAS, CUSTOMER_ID/INVOICE_DATE→ID_CLIENTE/DATA_EMISSAO) que não correspondiam às queries analisadas; corrigida sugestão de "índice parcial WHERE coluna IS NOT NULL" (não existe em Oracle — substituída por function-based index/composite); exemplos do reference padronizados em PT-BR; control_management_pack_access precisado como V$PARAMETER. Metadados suite_size/release_date/repository adicionados.

## [2.0.0]
- Breaking — divisão de oracle-sql-helper-ptbr v1.6.0 em 6 skills especializadas. Esta skill cobre Performance tuning — explain plan, AWR, ASH, indexes. Instale as 6 irmãs para cobertura completa da stack Oracle.

## [1.6.0]
- (oracle-sql-helper-ptbr) Novo reference ords-data-dictionary-ptbr.md — USER_ORDS_*/DBA_ORDS_*, depreciacao OAUTH/ORDS_SECURITY, evolucao 18.x-25.x.

## [1.5.0]
- (oracle-sql-helper-ptbr) Novo reference apex-data-dictionary-ptbr.md — hierarquia APEX_APPLICATION_*/APEX_APPL_*/APEX_WORKSPACE_*, versoes 19-26.1.

## [1.4.0]
- (oracle-sql-helper-ptbr) Remocao de clientes reais. Autoria M&S do Brasil LTDA.

## [1.3.0]
- (oracle-sql-helper-ptbr) Novo reference data-dictionary-ptbr.md — hierarquia Oracle, matriz edicao x tecnologia, evolucao 11g-26ai.
