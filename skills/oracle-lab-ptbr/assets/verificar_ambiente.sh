#!/usr/bin/env bash
# verificar_ambiente.sh — Suíte Oracle PT-BR / oracle-lab-ptbr
# Confere, em Linux/Mac, se a máquina está pronta para montar o lab Oracle.
# Uso: bash verificar_ambiente.sh

ok(){ printf '[ OK ] %-28s %s\n' "$1" "$2"; }
nok(){ printf '[ !! ] %-28s %s\n        -> %s\n' "$1" "$2" "$3"; }
info(){ printf '[info] %-28s %s\n' "$1" "$2"; }

echo
echo "=== Verificacao de ambiente — lab Oracle (Linux/Mac) ==="
echo

# Memoria
if [ "$(uname)" = "Darwin" ]; then
  mem_gb=$(( $(sysctl -n hw.memsize) / 1073741824 ))
else
  mem_gb=$(( $(grep MemTotal /proc/meminfo | awk '{print $2}') / 1048576 ))
fi
[ "$mem_gb" -ge 8 ] && ok "Memoria RAM total" "${mem_gb} GB" \
  || nok "Memoria RAM total" "${mem_gb} GB" "Com menos de 8 GB, prefira o caminho de container (26ai Free lite)."

# Disco
disco_gb=$(df -Pk "$HOME" | awk 'NR==2{print int($4/1048576)}')
[ "$disco_gb" -ge 80 ] && ok "Espaco livre em \$HOME" "${disco_gb} GB" \
  || nok "Espaco livre em \$HOME" "${disco_gb} GB" "A box + a VM passam de 60 GB."

# CPU: virtualizacao
if [ "$(uname)" = "Darwin" ]; then
  arch=$(uname -m)
  [ "$arch" = "arm64" ] && nok "Arquitetura" "$arch (Apple Silicon)" \
      "VirtualBox nao roda aqui. Use container com imagem lite-arm64." \
    || ok "Arquitetura" "$arch"
else
  grep -qE 'vmx|svm' /proc/cpuinfo && ok "Virtualizacao (VT-x/AMD-V)" "habilitada" \
    || nok "Virtualizacao (VT-x/AMD-V)" "nao detectada" "Habilite VT-x / AMD-V (SVM) na BIOS."
fi

# Ferramentas
for par in "VBoxManage:VirtualBox:https://www.virtualbox.org/wiki/Downloads" \
           "vagrant:Vagrant:https://developer.hashicorp.com/vagrant/downloads" \
           "git:Git:gerenciador de pacotes da distro"; do
  cmd=${par%%:*}; resto=${par#*:}; nome=${resto%%:*}; dica=${resto#*:}
  if command -v "$cmd" >/dev/null 2>&1; then
    ok "$nome" "$($cmd --version 2>&1 | head -1)"
  else
    nok "$nome" "nao encontrado" "Instale: $dica"
  fi
done

# Faixa host-only permitida (Linux/Mac)
if [ -f /etc/vbox/networks.conf ]; then
  info "Faixas host-only" "$(grep -v '^#' /etc/vbox/networks.conf | tr '\n' ' ')"
else
  info "Faixas host-only" "padrao 192.168.56.0/21 (crie /etc/vbox/networks.conf para ampliar)"
fi

# IP do lab
if ping -c1 -W1 192.168.56.140 >/dev/null 2>&1; then
  info "192.168.56.140" "ja responde — VM ligada ou IP em uso"
else
  info "192.168.56.140" "livre (esperado antes do primeiro vagrant up)"
fi

echo
echo "Resumo: itens com [ !! ] precisam de atencao antes do 'vagrant up'."
echo "Detalhes em references/vagrant-virtualbox-passo-a-passo-ptbr.md"
echo
