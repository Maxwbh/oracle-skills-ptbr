# Changelog — oracle-26ai-ptbr

## [1.0.2] - 2026-09-15
- Docs — suíte com 10 skills; referência cruzada para subir um 26ai Free local e testar a sintaxe nova.

## [1.0.1] - 2026-09-15
- Docs — princípio 8 cita o encerramento do Trivadis na 4.4 e o dbLinter (G-92xx, G-9208 assertions) como referência de naming para objetos 26ai.

## [1.0.0] - 2026-09-15
- Criação da skill. Isola as novidades de Oracle Database 23ai/26ai (SQL, PL/SQL, segurança, plataforma) e o guia de migração 19c → 26ai, para que os módulos 19c da suíte continuem gerando código 19c por padrão. Regra da suíte: só ativa com versão-alvo declarada; na dúvida, 19c. Cobre backports para 19c (19.16 TLS `system:`; 19.28 IF NOT EXISTS, Annotations, DBMS_DEVELOPER), tabela 19c×26ai "como escrever hoje", 3 references (SQL, PL/SQL+plataforma, migração) e 2 assets executáveis com naming Trivadis PT-BR. Fontes: artigos 23ai/26ai de oracle-base.com (Tim Hall) e release notes oficiais APEX 26.1 / ORDS 26.1.x.
