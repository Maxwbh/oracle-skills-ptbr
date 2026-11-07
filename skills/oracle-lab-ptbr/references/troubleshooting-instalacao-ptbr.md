# Troubleshooting — instalação e ambiente local

Organizado por **sintoma**, não por componente: o público desta skill não sabe de qual peça veio o erro.

Antes de tudo, colete: sistema do host, RAM total, caminho escolhido (VM/container), versão (19c/26ai) e a **mensagem de erro completa**. Sem isso, qualquer sugestão é chute.

## Índice

- [1. A VM não sobe](#1-a-vm-não-sobe)
- [2. O vagrant up para no meio](#2-o-vagrant-up-para-no-meio)
- [3. Não consigo conectar no banco](#3-não-consigo-conectar-no-banco)
- [4. Erros de login](#4-erros-de-login)
- [5. APEX e ORDS](#5-apex-e-ords)
- [6. Container](#6-container)
- [7. Lentidão e travamentos](#7-lentidão-e-travamentos)
- [8. Quebrou de vez](#8-quebrou-de-vez)
- [9. Comandos de coleta](#9-comandos-de-coleta)

---

## 1. A VM não sobe

| Mensagem / sintoma | Causa | O que fazer |
|---|---|---|
| `VERR_INTNET_FLT_IF_NOT_FOUND` | Adaptador host-only quebrado, normalmente após atualização do Windows ou instalação do WSL2/Docker | Reinstalar o VirtualBox marcando os componentes de rede; ou recriar: `VBoxManage hostonlyif create`. Verificar conflito Hyper-V (linha abaixo) |
| "Hyper-V is active", VM lentíssima ou travada na tela preta | WSL2/Docker Desktop/Hyper-V tomaram o hipervisor | Escolher um lado: `bcdedit /set hypervisorlaunchtype off` (Admin, reinicia) para usar VirtualBox; `auto` para voltar ao WSL2. Ou migrar para o caminho de container |
| `VT-x is not available` / `AMD-V is disabled` | Virtualização desligada na BIOS | Habilitar VT-x/AMD-V (ou SVM) na BIOS |
| "The IP address configured for the host-only network is not within the allowed ranges" | `public_ip` fora de `192.168.56.0/21` | Usar `192.168.56.x`; ou ampliar a faixa em `/etc/vbox/networks.conf` (Linux/Mac) |
| VM sobe, mas o host fica inutilizável | RAM da VM alta demais | Reduzir `mem_size` em `config/vagrant.yml`; deixe ≥ 4 GB para o host |
| `vagrant: command not found` depois de instalar | Terminal antigo, sem o PATH novo | Fechar e reabrir o terminal |

## 2. O vagrant up para no meio

| Sintoma | Causa | O que fazer |
|---|---|---|
| "No such file or directory" citando um `.zip`/`.rpm` | Instalador ausente em `software/` ou nome diferente do esperado | Conferir o `README.md` da pasta e ajustar o nome na variável correspondente do `install.env` |
| Download da box travado ou muito lento | Rede/VPN corporativa | Desconectar a VPN; ou baixar a box uma vez com `vagrant box add oraclebase/oracle-9` |
| Falha ao descompactar / "No space left on device" | Disco do host cheio (a box + VM passam de 60 GB) | Liberar espaço; VMs antigas ficam em `~/VirtualBox VMs` |
| Erro durante a criação do banco (DBCA) | Falta de RAM na VM | `vagrant destroy`, aumentar `mem_size` para 4096+, `vagrant up` |
| Parou depois de instalar o banco, durante APEX/ORDS | Java/Tomcat/ORDS ausentes ou versão trocada | O banco já está de pé: `vagrant ssh` e rodar só o script que faltou (`/vagrant/scripts/ords_software_installation.sh`) ou refazer com `INSTALL_APEX=false` se APEX não for necessário agora |

Rodar de novo é seguro: os scripts dos builds são feitos para reexecução.

## 3. Não consigo conectar no banco

Siga o diagnóstico em 4 perguntas do reference de rede antes de olhar a tabela.

| Erro | Tradução | O que fazer |
|---|---|---|
| **ORA-12541: TNS:no listener** | Ninguém atende na porta 1521 | VM ligada? Dentro dela: `lsnrctl status`; se parado, `lsnrctl start`. Confirmar IP e porta |
| **ORA-12514: TNS:listener does not currently know of service** | O listener atende, mas aquele nome de serviço não existe | Quase sempre é PDB fechado ou nome errado. `show pdbs`; `alter pluggable database freepdb1 open;` + `alter pluggable database freepdb1 save state;` |
| **ORA-12154: TNS:could not resolve the connect identifier** | Você usou um apelido de `tnsnames.ora` que não existe | Use a forma direta: `//host:1521/servico` |
| **TNS-12535 / timeout** | Pacote não chega | Firewall do host ou da VM; testar `Test-NetConnection`/`nc` |
| **ORA-12505: SID desconhecido** | Informou SID onde se pede service name | No multitenant, use o **service name** do PDB (`freepdb1`, `pdb1`) |
| Conecta pelo host, não conecta do notebook da sala | A VM está só em host-only | Adicionar adaptador em bridge (reference de rede, seção 3) |

## 4. Erros de login

| Erro | Causa | O que fazer |
|---|---|---|
| **ORA-01017: invalid username/password** | Senha errada, ou senha com caractere que o shell comeu | Use aspas: `sql "usuario/Senha@1"@//host:1521/pdb`. Confirme a senha em `config/install.env` |
| **ORA-28000: account is locked** | Usuário bloqueado (comum com `SCOTT`, `HR`) | `alter user hr identified by NovaSenha1 account unlock;` como SYS |
| **ORA-28001: the password has expired** | Perfil com validade (padrão 180 dias) | Trocar a senha quando pedir; em lab, `alter profile default limit password_life_time unlimited;` |
| **ORA-01109: database not open** | Instância de pé, banco/PDB fechado | `alter pluggable database all open;` |
| `as sysdba` falha mesmo com a senha certa | Usuário do SO fora do grupo `dba` | Rodar como o usuário `oracle`: `sudo su - oracle` |

## 5. APEX e ORDS

| Sintoma | Causa | O que fazer |
|---|---|---|
| Página em branco por segundos na primeira vez | ORDS aquecendo | Esperar e recarregar |
| Página em branco sempre, sem CSS, layout quebrado | Imagens do APEX (`/i/`) não publicadas no Tomcat | Conferir `ls $CATALINA_BASE/webapps/i/`; recopiar de `apex/images/` |
| 404 em `/ords/` | `ords.war` não implantado ou Tomcat parado | `sudo systemctl status tomcat`; conferir `webapps/ords.war` |
| 503 / "Service Unavailable" | ORDS sem conseguir falar com o banco | Banco/PDB aberto? Senha do pool (`APEX_PUBLIC_USER`/`ORDS_PUBLIC_USER`) correta? Ver logs em `$ORDS_CONF/logs` |
| Aviso de certificado em `https://…:8443` | Certificado autoassinado do lab | Esperado — aceitar. Nunca em produção |
| Login no `INTERNAL` recusado | Senha do admin do APEX diferente da do `install.env` | Dentro da VM: `@apxchpwd.sql` no diretório do APEX |
| APEX lento com 2 GB de RAM | Banco + Tomcat + JVM não cabem | Subir a VM para 4 GB (lembrando que o Free limita o **banco** a 2 GB) |
| Instalação do APEX reclama de memória | APEX 26.1 exige SGA ≥ 1200 MB e PGA ≥ 300 MB | `show parameter sga_target` / `pga_aggregate_target`; ajustar e reiniciar. No Free, o teto de 2 GB torna isso apertado — não sobra para outros usos |
| APEX instalado, mas ORDS recusa ou o APEX não abre | ORDS abaixo de 26.1.1 com APEX 26.1 | Conferir `ords --version`; baixar 26.1.1 ou superior |
| ORDS não inicia: "requires Java 17 and above" | JDK antigo no `JAVA_HOME` | Java 17 ou 21 (Oracle JDK ou GraalVM) |
| ORDS não sobe no Tomcat 10 | ORDS 26.1 só suporta Tomcat 9.0.x | Usar Tomcat 9; Tomcat 10 só a partir do ORDS 26.4 |

## 6. Container

| Sintoma | Causa | O que fazer |
|---|---|---|
| Container sobe e morre em seguida | Memória insuficiente no Docker Desktop | Aumentar RAM nas configurações do Docker (≥ 4 GB) |
| `unauthorized` ao baixar a imagem | Registry pede login/aceite de licença | `docker login container-registry.oracle.com`; ou usar a imagem `free`, que é pública |
| Perdi tudo ao remover o container | Sem volume | Sempre `-v nome-volume:/opt/oracle/oradata` |
| Conecta de dentro, não de fora | Porta não publicada | `-p 1521:1521` na criação; não dá para adicionar depois — recrie o container |
| "database is not ready" | Ainda inicializando | `docker logs -f` até "DATABASE IS READY TO USE" |
| Não roda no Mac M1/M2/M3 | Imagem x86 | Usar tag `…-lite-arm64` |
| Container do ORDS aborta: "Required variable ORACLE_USER_PWD is missing" | Imagem do ORDS 26.x exige a senha do `ORDS_PUBLIC_USER` | Passar `ORACLE_USER_PWD` no `docker run`/compose |
| ORA-20001 "Password validation failed" ao trocar a senha do ADMIN do APEX | Política de senha do APEX | Incluir caractere de pontuação na senha |
| Script em `/opt/oracle/scripts/setup` nunca roda | A imagem do Free traz o banco pré-criado | Usar `/opt/oracle/scripts/startup` (roda a cada subida; faça-o idempotente) |
| `curl` no `/ords/apex` fica em redirecionamento infinito | O APEX controla sessão por cookie | `curl -c cj -b cj -L …` |

## 7. Lentidão e travamentos

- **Host com pouca RAM sobrando** é a causa nº 1. Regra: RAM do host − RAM da VM ≥ 4 GB.
- **Antivírus varrendo o disco virtual** (`.vdi`): excluir a pasta das VMs da varredura em tempo real.
- **Hyper-V ativo junto com VirtualBox** derruba muito o desempenho, mesmo quando funciona (seção 1).
- **Disco cheio dentro da VM**: `df -h`; arquivos de auditoria e trace crescem (`$ORACLE_BASE/diag`). Limpeza é assunto de `oracle-dba-ptbr`.
- **Notebook hibernou com a VM ligada**: sessões caem e às vezes o banco não volta. `vagrant reload`.

## 8. Quebrou de vez

Ordem de tentativa, do mais barato ao mais caro:

1. `vagrant reload` (reinicia a VM).
2. Restaurar o snapshot: `VBoxManage snapshot <vm> restore "base-ok"`.
3. `vagrant destroy` + `vagrant up` — 30–60 min, mas resolve praticamente tudo. Os instaladores já estão em `software/`, não precisa baixar de novo.
4. Salvou algo dentro da VM que importa? Antes de destruir: `vagrant ssh` e copie para `/vagrant` (essa pasta é compartilhada com o host).

Ambiente de lab é descartável por design. Reinstalar não é derrota.

## 9. Comandos de coleta

Rode e envie a saída ao pedir ajuda:

**No host**
```bash
vagrant status
VBoxManage list runningvms
VBoxManage showvminfo <nome-da-vm> | head -30
```

**Dentro da VM** (`vagrant ssh`)
```bash
free -m
df -h
systemctl status tomcat --no-pager
sudo su - oracle -c 'lsnrctl status'
sudo su - oracle -c 'sqlplus -s / as sysdba <<< "select name, open_mode from v\$pdbs;"'
```

**Container**
```bash
docker ps -a
docker logs --tail 50 <nome>
```
