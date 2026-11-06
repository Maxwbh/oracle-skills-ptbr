---
name: oracle-lab-ptbr
description: "Módulo de instalação e ambiente local da suíte Oracle PT-BR, para desenvolvedor sem experiência de DBA. Montar Oracle 19c ou 26ai na própria máquina (Windows, Linux, Mac) via VM Vagrant+VirtualBox (padrão), container Docker/Podman, OVA ou RPM, com APEX e ORDS opcionais, e acessar esse banco de outros aparelhos da rede de casa. ATIVE em instalar Oracle na minha máquina, montar ambiente de desenvolvimento, subir banco local, vagrant up, VirtualBox, Oracle Free, XE, APEX local, ORDS local, quanto de RAM preciso, liberar porta 1521, e nos erros de quem está começando — ORA-12541, ORA-12514, ORA-01017, VM não sobe, conflito Hyper-V/WSL2, host-only fora da faixa, APEX em branco. Frases — 'como instalo isso aqui', 'não consigo conectar no banco', 'preciso de um banco pra testar'. NÃO ATIVE em banco de cliente ou produção (é oracle-dba-ptbr), nem em código, página APEX, endpoint ORDS ou pipeline."
metadata:
  version: "1.0.2"
  release_date: "2026-09-15"
  repository: "https://github.com/maxwbh/oracle-skills-ptbr"
  suite_size: 8
  author: "Maxwell da Silva Oliveira"
  contact: "contato@msbrasil.inf.br"
  organization: "M&S do Brasil LTDA"
  site: "https://msbrasil.inf.br"
  tags:
    - "oracle"
    - "instalacao"
    - "vagrant"
    - "virtualbox"
    - "docker"
    - "apex"
    - "ords"
    - "lab"
  category: "database"
  language: "pt-BR"
  icon: "🧰"
---

# Suíte Oracle PT-BR — Módulo Lab/Instalação (oracle-lab-ptbr)

> **Versão:** 1.0.2 · **Atualizada em:** setembro/2026 · **Repositório:** oracle-skills-ptbr · **Suíte:** 10 skills (8 recursos nesta skill)
> **v1.0.2:** tabela "Áreas cobertas" no SKILL.md: os 3 references e os 4 assets não eram citados, então future-Claude não sabia que existiam. Histórico em `CHANGELOG.md`.

Suíte completa (10 skills — conjunto único): ver `oracle-core-ptbr`.

Ajuda um **desenvolvedor sem experiência de DBA** a ter um Oracle rodando na própria máquina e a usá-lo de outros aparelhos da rede de casa. As demais skills assumem um banco existente; esta é a que o coloca de pé.

**Desenvolvido por:** Maxwell da Silva Oliveira — [M&S do Brasil LTDA](https://msbrasil.inf.br)

## Áreas cobertas

| Área | Reference | Assets |
|---|---|---|
| **Instalar** (VM Vagrant+VirtualBox, container, OVA, RPM) | `references/vagrant-virtualbox-passo-a-passo-ptbr.md` | `verificar_ambiente.ps1` (Windows) e `verificar_ambiente.sh` (Linux/Mac) — conferem RAM, disco, VT-x, hipervisor, VirtualBox, Vagrant **antes** do `vagrant up`; `install_env_exemplo.env` — modelo comentado do `config/install.env` |
| **Acessar** (rede de casa, firewall, IP fixo, segurança) | `references/rede-caseira-e-acesso-ptbr.md` | `teste_conexao.sql` — prova que o lab está utilizável (versão, PDB aberto, memória, escrita), não só "conectei" |
| **Consertar** (erros por sintoma: VM, instalação, conexão, login, APEX/ORDS, container, lentidão) | `references/troubleshooting-instalacao-ptbr.md` | seção 9 do reference: comandos de coleta para pedir ajuda |

## Como esta skill conversa

O público não é DBA. Regras de tom, valem para toda a interação:

1. **Uma pergunta por vez, no máximo três no total** antes de indicar o caminho: sistema da máquina, RAM disponível, precisa de APEX?
2. **Comando pronto para copiar**, com o diretório onde executar e o que deve aparecer na tela quando der certo.
3. **Sem jargão sem tradução.** "Listener" = o porteiro que atende conexões na porta 1521. "PDB" = o banco de verdade dentro do container. "SID/service name" = o nome que você informa ao conectar.
4. **Nunca mandar rodar comando como `root`/Administrador sem dizer por quê** e o que ele muda.
5. **Errar é esperado.** Se travar, pedir a mensagem **inteira** e os dados de contexto (SO, quanto de RAM, qual caminho) antes de sugerir qualquer coisa; nada de chutar.
6. **Não transformar em aula de DBA.** Resolver e seguir. Aprofundamento fica nas skills técnicas.

## Escolha do caminho (faça isso primeiro)

| Situação | Caminho | Por quê |
|---|---|---|
| **Padrão da casa** — máquina com 8 GB+ livres, quer algo parecido com o cliente | **VM Vagrant + VirtualBox** | Linux de verdade, mesmas versões e caminhos da produção; APEX e ORDS incluídos; dá para destruir e refazer com um comando |
| Só precisa de um banco para testar SQL/PL/SQL, hoje | **Container Docker/Podman (26ai Free)** | Sobe em minutos, banco pré-criado, ~1–2 GB de RAM; não tem APEX/ORDS prontos |
| Máquina fraca ou sem permissão para instalar | **OVA pronta do Oracle** (VirtualBox) ou banco compartilhado da equipe | Zero comando: importar e ligar |
| Já usa Oracle Linux na máquina ou num mini-PC | **RPM nativo** | Sem camada de virtualização |
| Mac com Apple Silicon | **Container imagem arm64** ou VM em outro host | VirtualBox x86 não roda ali |

Se a pessoa não sabe responder, o padrão é **VM Vagrant + VirtualBox com 26ai Free**: é o mais simples dos caminhos completos e não exige conta no Oracle Container Registry.

## Versão: 19c ou 26ai?

| Use | Quando |
|---|---|
| **19c** | Vai reproduzir o ambiente de um cliente (IMESC, Nexdom, SC Saúde). É o que roda em produção. Exige download do e-delivery (arquivo grande, login Oracle) |
| **26ai Free** | Laboratório, estudo, testar sintaxe nova. Download livre, instalação por RPM, sem custo de licença. Limites da edição Free: 2 CPU, 2 GB de RAM, 12 GB de dados |

Regra da suíte: **código nasce 19c**. O 26ai Free serve para experimentar o que vem depois — ver `oracle-26ai-ptbr`.

## Quanto de máquina

| Combinação | RAM para a VM | Disco | Host precisa ter |
|---|---|---|---|
| Banco 26ai Free só | 2 GB | ~20 GB | 8 GB |
| Banco 26ai Free + APEX + ORDS | 4 GB | ~40 GB | 8 GB (16 confortável) |
| Banco 19c + APEX + ORDS | 4–6 GB | ~100 GB | 16 GB |
| Container 26ai Free (lite) | ~1 GB | ~6 GB | 8 GB |

Sempre deixar **pelo menos 4 GB livres para o host**. VM sem RAM não dá erro claro: ela fica lenta, o banco derruba sessões e a pessoa acha que "o Oracle é ruim".

**RAM da VM ≠ RAM do banco.** Os 4 GB da linha "26ai Free + APEX + ORDS" são da máquina virtual, repartidos entre Linux, banco, JVM do Tomcat e ORDS. A edição **Free limita o banco a 2 GB**, independentemente do que a VM tenha — dar 8 GB à VM não faz o Free usar mais que isso. E o APEX 26.1 exige **SGA ≥ 1200 MB e PGA ≥ 300 MB**: cabe nos 2 GB do Free, mas sem folga. Se a instalação do APEX reclamar de memória, é isso.

## Compatibilidade — a corrente que precisa fechar

| Peça | Exigência | Observação |
|---|---|---|
| APEX 26.1 | **ORDS ≥ 26.1.1** | Regra da doc de instalação do APEX 26.1 |
| APEX 26.1 em 26ai | banco **≥ 23.26.0** (out/2025) | Em 19c, ≥ 19.18 |
| APEX 26.1 | SGA ≥ 1200 MB, PGA ≥ 300 MB, `WORKAREA_SIZE_POLICY=AUTO` na sessão de instalação | |
| ORDS 26.1.x | **Java 17 ou 21** (Oracle JDK **ou** GraalVM) | GraalVM só é obrigatório para GraphQL |
| ORDS 26.1.x | **Tomcat 9.0.x** ou WebLogic 14.1.2 | Tomcat 10 só a partir do ORDS 26.4 (inverno/2026) — **não antecipe a migração** |

Ordem recomendada pela Oracle a partir do APEX 26.1 em instalação nova: **ORDS primeiro, APEX depois**. Os builds do oracle-base ainda fazem APEX → ORDS (ordem clássica, que continua funcionando); é diferença de recomendação, não de funcionamento.

## Caminho padrão em 8 passos (VM Vagrant + VirtualBox)

Detalhe de cada passo, com comandos e telas esperadas, em `references/vagrant-virtualbox-passo-a-passo-ptbr.md`.

1. Instalar **VirtualBox** e **Vagrant** no host (Windows: verificar conflito Hyper-V/WSL2 antes — passo 1 do reference).
2. Clonar os builds prontos: `git clone https://github.com/oraclebase/vagrant.git`.
3. Escolher a pasta: `vagrant/database/ol9_26_free` (26ai Free) ou `vagrant/database/ol9_19` (19c).
4. Baixar os instaladores e colocar em `software/` — a lista exata está no `README.md` da pasta.
5. Ajustar `config/install.env` (senhas, `INSTALL_APEX`, `INSTALL_ORDS`) e `config/vagrant.yml` (RAM, CPU, IP).
6. `vagrant up` e esperar (30–60 min na primeira vez, é normal).
7. Testar a conexão do próprio host com SQLcl ou SQL Developer.
8. Tirar um **snapshot** do VirtualBox com tudo funcionando, antes de mexer em qualquer coisa.

Comandos do dia a dia: `vagrant up` (ligar), `vagrant halt` (desligar), `vagrant ssh` (entrar), `vagrant destroy` (apagar tudo). Sempre a partir da pasta do build.

## Endereços e senhas do build padrão

Valores de fábrica dos builds do oracle-base — servem de referência ao ajudar alguém:

| O quê | Valor |
|---|---|
| IP da VM (host-only) | `192.168.56.140` |
| Banco | porta `1521`, serviço `freepdb1` (26ai Free) ou `pdb1` (19c) |
| SYS | senha de `install.env` (`SysPassword1` no exemplo) |
| APEX | `http://192.168.56.140:8080/ords/` — workspace `INTERNAL`, `ADMIN` |
| ORDS/Tomcat | `8080` (HTTP) e `8443` (HTTPS, certificado autoassinado — o aviso do navegador é esperado) |
| Enterprise Manager Express (19c) | `https://192.168.56.140:5500/em` |

**Essas senhas são de laboratório.** Nunca reaproveitar em nada que saia da máquina; se o ambiente for compartilhado em casa, troque antes.

## Rede de casa

O detalhamento (host-only × bridge × redirecionamento de portas, IP fixo no roteador, firewall do Windows, acessar do celular/notebook) está em `references/rede-caseira-e-acesso-ptbr.md`. Os três pontos que não se negociam:

- **Nunca abrir 1521, 8080 ou 8443 na internet** — nem "só para testar", nem por DMZ ou UPnP do roteador. Banco exposto é varrido em horas. Se precisar de acesso de fora, é VPN ou túnel SSH.
- **Um IP que não muda.** Reserva de DHCP no roteador pelo MAC, ou IP fixo na VM. Sem isso, o endereço muda e "o banco sumiu".
- **Firewall do Windows pergunta uma vez.** Se clicarem em "Cancelar" naquela caixa, nada mais conecta e o sintoma não tem relação óbvia com a causa.

## Princípios canônicos

1. **Snapshot antes de qualquer experimento.** É a diferença entre desfazer em 30 segundos e reinstalar em 3 horas.
2. **Ambiente descartável.** Se quebrou e não é óbvio, `vagrant destroy` + `vagrant up` é resposta legítima — não é fracasso.
3. **Nada de dado real de cliente no lab.** Dados de IMESC, Nexdom e afins não saem do ambiente do cliente; para testar, usar massa gerada ou anonimizada (LGPD).
4. **Um caminho por vez.** Não misturar container e VM na mesma explicação; a pessoa se perde e as portas colidem.
5. **Desligar direito:** `vagrant halt` (ou `shutdown immediate` antes). Fechar a janela da VM no tacape corrompe o banco.
6. **O lab não é produção.** Nada que se aprende aqui sobre senha, firewall ou `chmod 777` vale para o cliente.
7. **Quando chamar quem entende de DBA:** dado perdido que importa, ambiente de cliente, qualquer coisa fora da própria máquina.

## Referências cruzadas

| Depois que o ambiente está de pé | Skill |
|---|---|
| Escrever PL/SQL | **oracle-plsql-ptbr** |
| Criar páginas APEX | **oracle-apex-ptbr** |
| Publicar REST | **oracle-ords-ptbr** |
| Entender sessões, tablespace, objetos inválidos | **oracle-dba-ptbr** |
| Versionar e montar pipeline com esse lab | **oracle-devops-ptbr** |
| Testar sintaxe 23ai/26ai | **oracle-26ai-ptbr** |
| Convenções do projeto antes do primeiro código | **oracle-core-ptbr** |
