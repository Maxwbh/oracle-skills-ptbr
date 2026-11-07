# Changelog — oracle-26ai-ptbr

## [1.1.2] - 2026-11-07
- Fix — matriz de migração: APEX 26.2 (padrão) com ORDS/SQLcl 26.3.0+ e Deep Data Security 23.26.3+; "24.2/24.1 suportados até jul/2027 e dez/2026" não tinha fonte → a verificar; fase 2 do roteiro com ORDS 26.3+ (Tomcat 10 só no ORDS 26.4).

## [1.1.1] - 2026-11-07
- Docs — `VECTOR_MEMORY_SIZE` medido no 26ai Free 23.26.3: no CDB com pool 0, aumentar exige `SCOPE=SPFILE` + restart (ORA-51950); com pool alocado, cresce sem restart e não reduz abaixo do inicial (ORA-51953); no PDB a cota é dinâmica e limitada ao CDB (ORA-51955). Nova armadilha na migração: definir o pool na janela do upgrade.
- Docs — fronteira: roteiro do upgrade 19c→26ai (fases, riscos, Vector Pool na janela) → oracle-26ai-helper-ptbr; checklist de código, caminhos e compatibilidade ficam aqui; operação → oracle-dba-ptbr.

## [1.1.0] - 2026-11-06
- Feature — fronteira com oracle-26ai-helper-ptbr: Vector Search, JSON Relational Duality e RAFT vão para a skill irmã; saem do ATIVE e entram no NÃO ATIVE da description. Sintaxe nova e migração 19c→26ai ficam aqui.
- Docs — migração: datas de suporte do 19c (31/12/2029 / 31/12/2032) e upgrade direto 19c/21c → 26ai com fonte.

## [1.0.2] - 2026-09-15
- Docs — suíte com 10 skills; referência cruzada para subir um 26ai Free local e testar a sintaxe nova.

## [1.0.1] - 2026-09-15
- Docs — princípio 8 cita o encerramento do Trivadis na 4.4 e o dbLinter (G-92xx, G-9208 assertions) como referência de naming para objetos 26ai.

## [1.0.0] - 2026-09-15
- Criação da skill. Isola as novidades de Oracle Database 23ai/26ai (SQL, PL/SQL, segurança, plataforma) e o guia de migração 19c → 26ai, para que os módulos 19c da suíte continuem gerando código 19c por padrão. Regra da suíte: só ativa com versão-alvo declarada; na dúvida, 19c. Cobre backports para 19c (19.16 TLS `system:`; 19.28 IF NOT EXISTS, Annotations, DBMS_DEVELOPER), tabela 19c×26ai "como escrever hoje", 3 references (SQL, PL/SQL+plataforma, migração) e 2 assets executáveis com naming Trivadis PT-BR. Fontes: artigos 23ai/26ai de oracle-base.com (Tim Hall) e release notes oficiais APEX 26.1 / ORDS 26.1.x.
