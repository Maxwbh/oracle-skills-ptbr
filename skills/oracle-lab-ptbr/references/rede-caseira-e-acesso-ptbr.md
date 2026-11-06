# Rede de casa — acessar o banco de outros aparelhos

Como sair do "funciona só na minha máquina" sem transformar o lab em porta aberta para a internet.

## Índice

- [1. Os três tipos de rede do VirtualBox](#1-os-três-tipos-de-rede-do-virtualbox)
- [2. Cenário A: só a sua máquina usa](#2-cenário-a-só-a-sua-máquina-usa)
- [3. Cenário B: outros aparelhos da casa usam](#3-cenário-b-outros-aparelhos-da-casa-usam)
- [4. IP que não muda](#4-ip-que-não-muda)
- [5. Firewall](#5-firewall)
- [6. Como conectar de cada ferramenta](#6-como-conectar-de-cada-ferramenta)
- [7. Acesso de fora de casa](#7-acesso-de-fora-de-casa)
- [8. Segurança mínima do lab](#8-segurança-mínima-do-lab)
- [9. Diagnóstico de conectividade em 4 perguntas](#9-diagnóstico-de-conectividade-em-4-perguntas)

---

## 1. Os três tipos de rede do VirtualBox

| Tipo | Quem enxerga a VM | Quando usar |
|---|---|---|
| **Host-only** (`192.168.56.x`) | Só o computador que hospeda a VM | Padrão dos builds; suficiente para trabalhar sozinho |
| **Redirecionamento de portas (NAT)** | Só o host, via `localhost:porta` | Já vem junto nos builds (1521, 8080, 8443, 5500) |
| **Bridge** | Todos os aparelhos da casa; a VM ganha IP do roteador (`192.168.0.x`, `192.168.1.x`…) | Quando o notebook da sala, o celular ou um colega precisa acessar |

Os builds do oracle-base ligam host-only **e** redirecionamento ao mesmo tempo. Então, do seu próprio computador, `192.168.56.140:1521` e `localhost:1521` funcionam igualmente.

## 2. Cenário A: só a sua máquina usa

Nada a fazer. Conecte em `//192.168.56.140:1521/freepdb1` ou `//localhost:1521/freepdb1`.

Um detalhe que confunde: dentro da VM, `localhost` é a própria VM. Comandos rodados por `vagrant ssh` usam `localhost`; ferramentas no seu Windows usam o IP `192.168.56.140`.

## 3. Cenário B: outros aparelhos da casa usam

Adicione um adaptador em bridge. No `Vagrantfile`, descomente/insira:

```ruby
config.vm.network "public_network", bridge: "Intel(R) Wi-Fi 6 AX201"
```

Descobrir o nome exato do adaptador do host:

```bash
VBoxManage list bridgedifs | findstr Name     # Windows
VBoxManage list bridgedifs | grep '^Name'     # Linux/Mac
```

Depois `vagrant reload`. Dentro da VM, `ip a` mostra o novo IP (algo como `192.168.0.57`) — é esse que os outros aparelhos usam.

Cuidados:
- **Wi-Fi e bridge nem sempre se dão bem.** Se o IP não vier ou cair, use cabo, ou fique no cenário A e trabalhe pelo host.
- O IP vem do DHCP do roteador e **muda**. Resolva na seção 4.
- Com bridge, a VM passa a ser um aparelho a mais na sua rede: aplica-se tudo da seção 8.

## 4. IP que não muda

Duas formas, escolha uma:

**Reserva no roteador (recomendada).** Pegue o MAC da VM (`ip a` dentro dela, ou `VBoxManage showvminfo <vm> | grep MAC`) e, na interface do roteador, em DHCP → Reserva/Binding, amarre esse MAC a um IP fora da faixa distribuída (ex.: `192.168.0.50`). Vantagem: a VM continua configurada como DHCP, e o roteador sempre entrega o mesmo número.

**IP fixo dentro da VM.** Funciona, mas se você errar a máscara ou o gateway perde o acesso e precisa arrumar pelo console do VirtualBox.

Para APEX, IP estável importa ainda mais: o endereço entra no link que você compartilha.

## 5. Firewall

**No host Windows.** Na primeira vez que o VirtualBox precisar de rede, aparece a caixa "Permitir acesso". Marque **Redes privadas** e permita. Se alguém clicou em Cancelar, corrija em Firewall do Windows Defender → Permitir um aplicativo, ou:

```powershell
# PowerShell como Administrador
New-NetFirewallRule -DisplayName "VirtualBox" -Direction Inbound -Program "C:\Program Files\Oracle\VirtualBox\VirtualBoxVM.exe" -Action Allow -Profile Private
```

Nunca libere no perfil **Público** — é o perfil usado em Wi-Fi de aeroporto e café.

**Dentro da VM (Oracle Linux).** Os builds já abrem as portas necessárias. Se você criou a VM por outro caminho:

```bash
sudo firewall-cmd --permanent --add-port=1521/tcp
sudo firewall-cmd --permanent --add-port=8080/tcp
sudo firewall-cmd --permanent --add-port=8443/tcp
sudo firewall-cmd --reload
sudo firewall-cmd --list-ports
```

**No roteador.** Nada a fazer para uso doméstico. Se a ideia era "abrir a porta no roteador", leia a seção 7 antes.

## 6. Como conectar de cada ferramenta

Dados que toda ferramenta pede: **host** (`192.168.56.140` ou o IP da bridge), **porta** (`1521`), **service name** (`freepdb1` no 26ai Free, `pdb1` no 19c), usuário e senha.

| Ferramenta | Como |
|---|---|
| SQLcl / SQL*Plus | `sql usuario/senha@//192.168.56.140:1521/freepdb1` |
| SQL Developer / VS Code (extensão Oracle) | Conexão "Basic": hostname, porta, **Service name** (não SID) |
| Python (`oracledb`) | `oracledb.connect(user=…, password=…, dsn="192.168.56.140:1521/freepdb1")` — modo thin, sem Instant Client |
| APEX no navegador | `http://192.168.56.140:8080/ords/` |
| Celular/tablet | Só com bridge (seção 3), usando o IP do roteador |

Erro comum: informar **SID** onde se pede **service name**. No multitenant você conecta ao PDB pelo service name; o SID (`FREE`, `cdb1`) é o container.

## 7. Acesso de fora de casa

**Não abra portas no roteador.** Nem 1521, nem 8080, nem 8443; nem por "DMZ", nem por UPnP. Um banco exposto na internet é encontrado por varredura automática em poucas horas, e o Oracle não foi feito para ficar nu na rede pública.

Se precisar mesmo acessar de fora:

1. **VPN para a sua casa** (WireGuard ou a VPN embutida em roteadores melhores). O aparelho remoto entra na rede doméstica e usa o IP interno normalmente.
2. **Túnel SSH**, se houver um servidor SSH acessível: `ssh -L 1521:192.168.56.140:1521 usuario@servidor` e conecte em `localhost:1521`.
3. **Não use o lab.** Para demonstrar algo a um cliente, use um ambiente na nuvem (Oracle Autonomous Free, por exemplo), não a máquina de casa.

## 8. Segurança mínima do lab

- Trocar as senhas de exemplo (`SysPassword1`, `ApexPassword1`) se a VM ficar em bridge.
- Nenhum dado real de cliente. Massa de teste gerada ou anonimizada — LGPD vale também no notebook de casa.
- Desligar a VM quando não estiver usando: `vagrant halt`. Serviço no ar sem ninguém olhando é o que dá problema.
- Certificado autoassinado em `8443` faz o navegador reclamar — em lab, tudo bem aceitar; em qualquer outro lugar, não.
- Não expor o Enterprise Manager Express (`5500`) além do host.
- Se a casa tem visitas com Wi-Fi, prefira deixar o lab em host-only e acessar pelo próprio computador.

## 9. Diagnóstico de conectividade em 4 perguntas

Quando "não conecta", responda nesta ordem — cada etapa elimina metade das causas:

1. **A VM está ligada?** `vagrant status` no host deve dizer *running*.
2. **A máquina responde?** `ping 192.168.56.140`. Sem resposta → problema de rede/firewall do host, não do Oracle.
3. **A porta responde?**
   ```powershell
   Test-NetConnection 192.168.56.140 -Port 1521      # Windows
   ```
   ```bash
   nc -zv 192.168.56.140 1521                        # Linux/Mac
   ```
   Fechada → listener parado dentro da VM ou firewall da VM (seção 5).
4. **O serviço existe?** Dentro da VM (`vagrant ssh`, `sudo su - oracle`):
   ```bash
   lsnrctl status
   ```
   Procure `freepdb1` na lista de serviços. Não aparece → o PDB está fechado; abra com `alter pluggable database freepdb1 open;` e depois `alter pluggable database freepdb1 save state;` para ele abrir sozinho no próximo boot.

Erros específicos e o que cada um significa: `references/troubleshooting-instalacao-ptbr.md`.
