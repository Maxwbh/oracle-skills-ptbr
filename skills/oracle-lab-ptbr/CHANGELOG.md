# Changelog — oracle-lab-ptbr

## [1.2.1] - 2026-11-07
- Docs — passo a passo da VM com APEX 26.2 e ORDS ≥ 26.3.0 (26.1 exigia 26.1.1); requisito de memória da instalação 26.2: a verificar.

## [1.2.0] - 2026-11-07
- Feature — caminho "Docker Compose: 26ai Free + imagem oficial do ORDS" na escolha do caminho e §9.1 do passo a passo: a imagem `database/ords` instala o APEX montado em `/opt/oracle/apex`; variáveis (inclusive `ORACLE_USER_PWD`, obrigatória no ORDS 26.x), troca da senha do ADMIN, scripts `startup` × `setup` e tempos medidos (26ai Free 23.26.3 + ORDS 26.3.1 + APEX 26.2). Aponta para o `ambiente-teste/` do oracle-26ai-helper-ptbr.
- Docs — troubleshooting de container: `ORACLE_USER_PWD` ausente, ORA-20001 na senha do APEX, script de `setup` que não roda (banco pré-criado) e `curl` em loop no `/ords/apex` (cookie).
- Docs — container deixa de ser descrito como "sem APEX/ORDS prontos".
- Docs — roteamento: roteiro do upgrade 19c→26ai também vai para oracle-26ai-helper-ptbr; checklist de código fica na oracle-26ai-ptbr; operação na oracle-dba-ptbr.

## [1.1.0] - 2026-11-06
- Feature — 19c em Oracle Linux 10: Oracle recomenda RU 19.32+ com one-offs; build oraclebase/vagrant `ol10_19` com RU 19.33 (instalação limpa segundo o oracle-base).
- Feature — fim do HCP Vagrant Registry (criação encerrada em 01/10/2026, suporte em 02/11/2026, desligamento em 31/12/2026): guardar a box localmente.
- Docs — Fedora 45 (`f45_*`) como curiosidade ("don't do this for something serious"); VirtualBox 7.2.22 é a mais recente (sem versão mínima exigida); APEX 26.2 na tabela de compatibilidade.
- Docs — roteamento para oracle-26ai-helper-ptbr.

## [1.0.2] - 2026-09-15
- Docs — tabela "Áreas cobertas" no SKILL.md: os 3 references e os 4 assets não eram citados, então future-Claude não sabia que existiam.

## [1.0.1] - 2026-09-15
- Fix — matriz de compatibilidade acrescentada ao SKILL.md: APEX 26.1 exige ORDS >= 26.1.1, banco >= 23.26.0 em 26ai, SGA >= 1200 MB e PGA >= 300 MB; ORDS 26.1 aceita Oracle JDK 17/21 ou GraalVM (GraalVM só é obrigatório para GraphQL, deixou de ser apresentado como componente obrigatório); Tomcat fixado na série 9 com a nota de que Tomcat 10 só entra no ORDS 26.4.
- Fix — "RAM da VM ≠ RAM do banco": a edição Free limita o banco a 2 GB independentemente do tamanho da VM.
- Fix — `ORDS_SOFTWARE` versionado (`ords-26.1.1.zip`) em vez de `ords-latest.zip`, para o lab ser reproduzível.
- Fix — `PATH` do exemplo apontava para `$ORACLE_HOME` em vez de `$ORACLE_HOME/bin`.
- Fix — `verificar_ambiente.ps1` deixou de tratar hipervisor ativo como erro: agora é informativo, com a ressalva de que a questão só afeta o caminho VirtualBox.
- Docs — 5 novas linhas de troubleshooting (memória do APEX, ORDS abaixo de 26.1.1, Java < 17, Tomcat 10).

## [1.0.0] - 2026-09-15
- Criação da skill. Módulo de instalação e ambiente local para desenvolvedor sem experiência de DBA: escolha do caminho (VM Vagrant+VirtualBox como padrão, container Docker/Podman, OVA, RPM nativo), dimensionamento de máquina, 19c e 26ai Free, APEX/ORDS opcionais, acesso pela rede de casa (host-only × bridge × port forwarding, IP fixo, firewall) e troubleshooting por sintoma. Regras de tom próprias para público não-DBA (uma pergunta por vez, comando pronto, sem jargão sem tradução). Ancorada nos builds públicos de github.com/oraclebase/vagrant (Apache 2.0) e na imagem container-registry.oracle.com/database/free.
