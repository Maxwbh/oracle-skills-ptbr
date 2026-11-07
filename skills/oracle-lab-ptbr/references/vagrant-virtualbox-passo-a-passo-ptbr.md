# Passo a passo — Oracle na sua máquina com Vagrant + VirtualBox

Caminho padrão da suíte. Resultado final: uma máquina virtual Linux com Oracle (19c ou 26ai Free), opcionalmente APEX e ORDS, acessível do seu Windows/Linux/Mac e do resto da casa.

Baseado nos builds públicos de Tim Hall (github.com/oraclebase/vagrant, Apache 2.0), que já resolvem pacotes do SO, kernel parameters, criação do banco, APEX e Tomcat/ORDS.

## Índice

- [0. O que você vai instalar](#0-o-que-você-vai-instalar)
- [1. Preparar o host](#1-preparar-o-host)
- [2. Pegar os builds](#2-pegar-os-builds)
- [3. Escolher a pasta certa](#3-escolher-a-pasta-certa)
- [4. Baixar os instaladores Oracle](#4-baixar-os-instaladores-oracle)
- [5. Ajustar os dois arquivos de configuração](#5-ajustar-os-dois-arquivos-de-configuração)
- [6. vagrant up](#6-vagrant-up)
- [7. Testar](#7-testar)
- [8. Snapshot e rotina do dia a dia](#8-snapshot-e-rotina-do-dia-a-dia)
- [9. Alternativa rápida: container](#9-alternativa-rápida-container)
  - [9.1 Container com APEX e ORDS (Docker Compose)](#91-container-com-apex-e-ords-docker-compose)

---

## 0. O que você vai instalar

| Componente | Para quê | Obrigatório? |
|---|---|---|
| VirtualBox | Cria a máquina virtual | sim |
| Vagrant | Automatiza: cria a VM, instala o Oracle e configura tudo sozinho | sim |
| Git | Baixar os builds | sim (ou baixar o ZIP do GitHub) |
| Banco (19c ou 26ai Free) | O Oracle | sim |
| APEX + ORDS + Tomcat + Java | Telas APEX e REST | só se `INSTALL_APEX=true` |
| SQLcl | Conectar no banco pelo terminal | recomendado |

## 1. Preparar o host

### Windows

1. Baixe e instale **VirtualBox** (Downloads no site virtualbox.org — a mais recente em 06/11/2026 é a **7.2.22**, de 20/10/2026; o oraclebase/vagrant não exige versão mínima) e **Vagrant** (developer.hashicorp.com/vagrant). Aceite tudo como vem. A rede pisca durante a instalação do VirtualBox — é ele criando o adaptador virtual.
2. Feche e reabra o terminal. Confira no **PowerShell**:
   ```powershell
   VBoxManage --version
   vagrant --version
   ```
   Se `VBoxManage` não for reconhecido, use o caminho completo: `& "C:\Program Files\Oracle\VirtualBox\VBoxManage.exe" --version`.
3. **Conflito Hyper-V / WSL2 / Docker Desktop.** Se você usa WSL2 ou Docker Desktop, o Windows liga o Hyper-V, e a VM do VirtualBox fica **lenta ou nem inicia**. Sintomas: `VERR_INTNET_FLT_IF_NOT_FOUND`, aviso "Hyper-V is active", VM travando na tela preta.
   - VirtualBox 7.1+ convive melhor, mas com perda de desempenho.
   - Solução limpa: escolher um lado. Para desligar o Hyper-V (PowerShell como Administrador, reinicia depois):
     ```powershell
     bcdedit /set hypervisorlaunchtype off
     ```
     Para voltar (e ter WSL2/Docker de novo): `bcdedit /set hypervisorlaunchtype auto`.
   - Se você depende do Docker Desktop no dia a dia, vá pelo caminho de container (seção 9) em vez de brigar com isso.
4. Verifique que a **virtualização está ligada na BIOS**: Gerenciador de Tarefas → Desempenho → CPU → "Virtualização: Habilitado". Se estiver desabilitado, ligue VT-x/AMD-V na BIOS.

### Linux

```bash
sudo dnf install -y VirtualBox vagrant      # Oracle Linux / Fedora
sudo apt install -y virtualbox vagrant      # Debian / Ubuntu
vagrant --version && VBoxManage --version
```

Se a VM não iniciar por causa de Secure Boot, é preciso assinar os módulos do VirtualBox ou desligar o Secure Boot.

### Mac

VirtualBox só roda em Mac **Intel**. Em Apple Silicon (M1/M2/M3/M4), pule para a seção 9 (container arm64) ou use outro computador como servidor do lab.

## 2. Pegar os builds

```bash
cd ~            # Windows: cd C:\git  (crie a pasta se não existir)
git clone https://github.com/oraclebase/vagrant.git
```

Sem Git: baixe o ZIP pelo botão "Code" no GitHub e extraia.

## 3. Escolher a pasta certa

Dentro de `vagrant/database/`:

| Pasta | O que é | Quando usar |
|---|---|---|
| `ol9_26_free` | 26ai Free (RPM) em Oracle Linux 9 | **Padrão** — download livre, instalação rápida |
| `ol9_19` | 19c completo em Oracle Linux 9 | Reproduzir ambiente de cliente |
| `ol10_26_free`, `ol8_26_free` | 26ai Free em OL10 / OL8 | Preferência de SO |
| `ol8_19`, `ol8_19_rpm` | 19c em OL8 | Cliente em OL8 |
| `ol10_19` | 19c em **Oracle Linux 10**, com **RU 19.33** aplicado na instalação (`-applyRU`) | Cliente que vai para OL10 |
| `f45_19`, `f45_21`, `f45_26` | Oracle em **Fedora 45** | Só curiosidade — o autor avisa: "Please don't do this for something serious"; a box é gerada localmente com Packer |

Todas seguem a mesma estrutura: `Vagrantfile`, `config/`, `scripts/`, `software/`.

**19c em Oracle Linux 10 (situação em 06/11/2026):**
- A Oracle suporta o 19c em OL10 e **recomenda o RU 19.32 ou superior**, com
  patches one-off adicionais listados na doc
  ([Installing 19c on OL10/RHEL10](https://docs.oracle.com/en/database/oracle/oracle-database/19/rnrdm/installing-oracle-database-19c-oracle-linux-10-and-red-hat-enterprise-linux-10.html)).
- O build `ol10_19` do oraclebase/vagrant usa o **RU 19.33** (commit de
  23/10/2026), que segundo o autor dá **instalação limpa** de single instance e
  RAC; o instalador ainda precisa de `CV_ASSUME_DISTID=OL9` (o build já faz)
  ([oracle-base, 25/09/2026, atualizado](https://oracle-base.com/blog/2026/09/25/oracle-database-19c-supported-on-oracle-linux-10-ol10-but/)).
- O README da pasta ainda cita o patch 19.27 na lista de downloads; vale o que
  está em `config/install.env` (19.33).

**Boxes e o fim do HCP Vagrant Registry (antigo Vagrant Cloud):** a HashiCorp
encerrou a criação de boxes em **01/10/2026**, o suporte em **02/11/2026** e
desliga o serviço em **31/12/2026**
([HCP Vagrant EOL](https://developer.hashicorp.com/hcp/docs/vagrant/hcp-vagrant-eol)).
Boxes publicadas lá (como `oraclebase/oracle-9`) deixam de baixar depois disso.
Enquanto ainda baixam: faça `vagrant box add` uma vez e **guarde o arquivo
`.box`** (fica em `~/.vagrant.d/boxes/`); para reinstalar de um arquivo local,
`vagrant box add --name oraclebase/oracle-9 caminho/da/box.box`. O build
`ol10_19` já usa a box `oraclelinux/10` fornecida pela Oracle.

## 4. Baixar os instaladores Oracle

Abra o `README.md` da pasta escolhida: ele lista exatamente o que baixar. Coloque os arquivos **dentro de `software/`**, sem renomear e sem descompactar.

Para `ol9_26_free`, tipicamente:

| Arquivo | Onde | Precisa de login? |
|---|---|---|
| `oracle-ai-database-free-26ai-…el9.x86_64.rpm` | oracle.com/database/free | não |
| `apex_26.1_en.zip` | oracle.com/tools/downloads/apex-downloads | não |
| `ords-latest.zip` | downloads do ORDS | não |
| `sqlcl-latest.zip` | oracle.com/tools/downloads/sqlcl-downloads | não |
| `graalvm-jdk-21_linux-x64_bin.tar.gz` | graalvm.org/downloads | não |
| `apache-tomcat-9.0.x.tar.gz` | tomcat.apache.org (**série 9**, não 10) | não |

Duas correções úteis sobre essa lista:

- **GraalVM não é obrigatório.** O ORDS 26.1 aceita **Oracle JDK 17 ou 21** e também GraalVM 17/21. O build usa GraalVM porque foi a escolha do autor; se você já tem um JDK 21, aponte `JAVA_SOFTWARE` para ele. GraalVM só vira requisito se você for usar **GraphQL** no ORDS.
- **Tomcat tem que ser da série 9.** O ORDS 26.1 suporta Tomcat 9.0.x; o suporte a Tomcat 10 só chega no ORDS 26.4 (previsto para o inverno de 2026), e a própria Oracle pede para não antecipar a migração. Baixar o Tomcat 10 "porque é mais novo" quebra a instalação.
- **Fixe a versão do ORDS.** O arquivo que a Oracle publica chama-se `ords-latest.zip` — e o conteúdo muda a cada release. Para o lab ser reproduzível, renomeie o download (`ords-26.1.1.zip`) e aponte `ORDS_SOFTWARE` para esse nome. Assim, quem repetir o passo a passo daqui a três meses monta o mesmo ambiente. O APEX 26.1 exige **ORDS ≥ 26.1.1**; versão menor falha.

Para `ol9_19` troque o RPM por `LINUX.X64_193000_db_home.zip` (e-delivery/edelivery.oracle.com — **exige conta Oracle**, ~3 GB). Patches são opcionais (`PATCH_DB` no `install.env`) e exigem My Oracle Support.

Confira os nomes: o `install.env` procura o arquivo **pelo nome exato**. Versão diferente da esperada → ajuste a variável no `install.env`.

## 5. Ajustar os dois arquivos de configuração

### `config/install.env` — o que instalar e com quais senhas

```bash
export DB_PASSWORD=SysPassword1        # senha do SYS/SYSTEM (lab!)
export ORACLE_SID=FREE
export PDB_NAME=freepdb1               # o nome que você usa para conectar
export INSTALL_APEX=true               # false = só o banco, sobe muito mais rápido
export INSTALL_ORDS="true"             # false se não for usar APEX nem REST
export APEX_PASSWORD="ApexPassword1"
export DB_SOFTWARE=oracle-ai-database-free-26ai-23.26.0-1.el9.x86_64.rpm
export APEX_SOFTWARE="apex_26.1_en.zip"
export TOMCAT_SOFTWARE="apache-tomcat-9.0.110.tar.gz"
```

Se você só quer um banco para escrever SQL, ponha `INSTALL_APEX=false` e `INSTALL_ORDS=false`: cai de ~50 para ~15 minutos e economiza 2 GB de RAM.

### `config/vagrant.yml` — tamanho da máquina e endereço

```yaml
box: oraclebase/oracle-9
vm_name: ol9_26_free
mem_size: 4096          # 2048 se for só o banco; 6144 para 19c + APEX
cpus: 2
public_ip: 192.168.56.140
disk_size: 100          # GB, cresce sob demanda
```

`public_ip` **precisa estar na faixa 192.168.56.0/21**. Fora dela o Vagrant recusa com "The IP address configured for the host-only network is not within the allowed ranges" (a faixa permitida vem de `/etc/vbox/networks.conf` no Linux/Mac). Se `…140` já estiver em uso, mude para `…141`.

Nas pastas mais antigas esses valores estão direto no `Vagrantfile` (`var_mem_size`, `var_public_ip`).

## 6. vagrant up

```bash
cd vagrant/database/ol9_26_free
vagrant up
```

O que acontece: baixa a "box" (imagem do Oracle Linux, ~1 GB, só na primeira vez), cria a VM, instala pacotes, instala o banco, cria o PDB, instala APEX e ORDS. **30 a 60 minutos** na primeira execução. É normal parecer travado em alguns pontos — o log continua rolando.

Enquanto roda: não hiberne o notebook, não desligue a VPN corporativa se ela filtra o download da box.

Terminou sem erro fatal? A última linha útil costuma ser o resumo dos serviços. Se parou no meio, guarde a **mensagem inteira**: os erros mais comuns estão no reference de troubleshooting.

## 7. Testar

Do próprio host (Windows/Linux/Mac), com SQLcl instalado:

```bash
sql sys/SysPassword1@//192.168.56.140:1521/freepdb1 as sysdba
```

Rode também o `assets/teste_conexao.sql`: ele confirma versão, PDB aberto, memória e escrita — "conectei" não é o mesmo que "está utilizável".

Deve aparecer `Connected to: Oracle AI Database 26ai Free Release 23.26.0.0.0`. Depois:

```sql
select version_full from v$instance;
select name, open_mode from v$pdbs;
```

APEX no navegador: `http://192.168.56.140:8080/ords/` → workspace `INTERNAL`, usuário `ADMIN`, senha do `install.env`. Primeira abertura demora (ORDS está aquecendo); em branco por alguns segundos é normal, em branco por minutos está no troubleshooting.

Dentro da VM, se precisar:

```bash
vagrant ssh
sudo su - oracle
sqlplus / as sysdba
```

## 8. Snapshot e rotina do dia a dia

**Antes de qualquer experimento**, com tudo funcionando:

```bash
vagrant halt                                     # desligue primeiro
VBoxManage snapshot ol9_26_free take "base-ok"
```

Voltar: `VBoxManage snapshot ol9_26_free restore "base-ok"`.

Rotina, sempre dentro da pasta do build:

| Quero | Comando |
|---|---|
| Ligar | `vagrant up` |
| Desligar (jeito certo) | `vagrant halt` |
| Entrar no Linux | `vagrant ssh` |
| Ver se está de pé | `vagrant status` |
| Recomeçar do zero | `vagrant destroy` e depois `vagrant up` |

Nunca feche a janela da VM no "X" nem force o desligamento do host com a VM ligada: o banco pode não abrir na próxima vez.

## 9. Alternativa rápida: container

Quando só é preciso um banco para rodar SQL, sem APEX:

```bash
docker run -d --name oracle26 -p 1521:1521 \
  -e ORACLE_PWD=SuaSenhaDeLab1 \
  -v oracle26-data:/opt/oracle/oradata \
  container-registry.oracle.com/database/free:23.26.0.0
```

- Vale `podman` no lugar de `docker`. Em Mac Apple Silicon use a tag `…-lite-arm64`.
- `ORACLE_SID` é sempre `FREE`; o PDB é `FREEPDB1`; conecte em `//localhost:1521/FREEPDB1`.
- A tag `-lite` é ~80% menor e sobe mais rápido, sem alguns recursos avançados.
- O `-v` é o que faz seus dados sobreviverem a `docker rm`. Sem ele, apagou o container, apagou o banco.
- Acompanhe a subida com `docker logs -f oracle26` até aparecer "DATABASE IS READY TO USE".
- Trocar a senha depois: `docker exec oracle26 ./setPassword.sh NovaSenha1`.

### 9.1 Container com APEX e ORDS (Docker Compose)

A Oracle publica a imagem **`container-registry.oracle.com/database/ords`** (ex.: tag `26.3.1`). Ao subir apontando para o banco, ela instala o ORDS no banco e, se a pasta do APEX estiver montada em `/opt/oracle/apex`, **instala ou atualiza o APEX** e serve as imagens em `/i/`. Medido em nov/2026 (26ai Free 23.26.3 + ORDS 26.3.1 + APEX 26.2, 4 vCPU/15 GB):

| Situação | Tempo até o APEX responder |
|---|---|
| Primeira subida (instala ORDS + APEX) | ~21 min |
| Restaurar snapshot dos volumes (já com APEX) | ~2 min |
| `docker compose stop` / `start` | ~1 min |
| Zerar o banco para um teste (clonar PDB de um PDB "dourado" READ ONLY) | ~10 s (descartar: ~3 s) |

Pontos que pegam na montagem:

- **Variáveis do container do ORDS:** `DBHOST`, `DBPORT`, `DBSERVICENAME` (ex.: `FREEPDB1`), `ORACLE_PWD` (senha do SYS), `APEX_PWD` (pool do APEX) e **`ORACLE_USER_PWD`** (senha do `ORDS_PUBLIC_USER`) — sem esta última o ORDS 26.x aborta na subida.
- **APEX baixado** de `https://download.oracle.com/otn_software/apex/apex-latest.zip` (ou `apex_26.2.zip`) e descompactado na pasta montada.
- A instalação é silenciosa e usa senhas internas fixas: **troque a senha do ADMIN do INTERNAL** depois. A política de senha do APEX exige pontuação (senão ORA-20001 "Password validation failed").
- A imagem do 26ai Free já traz o **banco pré-criado**: scripts em `/opt/oracle/scripts/setup` não rodam; use `/opt/oracle/scripts/startup` (roda a cada subida).
- Checagem automática do APEX por `curl` precisa de cookie jar (`-c`/`-b`): sem ele o APEX redireciona em loop.

Um ambiente pronto (compose, pós-instalação, snapshot dourado e PDB descartável, com esses tempos) está no repositório **oracle-26ai-helper-ptbr**, pasta `ambiente-teste/`: https://github.com/Maxwbh/oracle-26ai-helper-ptbr

Se o objetivo é **reproduzir o ambiente de um cliente** (19c, Tomcat, caminhos de produção), a VM continua sendo o caminho.
