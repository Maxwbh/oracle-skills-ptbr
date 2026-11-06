<#
    verificar_ambiente.ps1 — Suíte Oracle PT-BR / oracle-lab-ptbr
    Confere, no Windows, se a máquina está pronta para montar o lab Oracle
    (VM Vagrant + VirtualBox) e aponta os problemas mais comuns.
    Uso: abra o PowerShell (não precisa ser Administrador) e rode:
         powershell -ExecutionPolicy Bypass -File .\verificar_ambiente.ps1
#>

function Resultado($nome, $ok, $detalhe, $dica) {
    $marca = if ($ok) { "[ OK ]" } else { "[ !! ]" }
    $cor   = if ($ok) { "Green" } else { "Yellow" }
    Write-Host ("{0} {1,-28} {2}" -f $marca, $nome, $detalhe) -ForegroundColor $cor
    if (-not $ok -and $dica) { Write-Host ("        -> " + $dica) -ForegroundColor Gray }
}

Write-Host "`n=== Verificacao de ambiente — lab Oracle (Windows) ===`n"

# 1. Memoria
$memGb = [math]::Round((Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory / 1GB, 1)
Resultado "Memoria RAM total" ($memGb -ge 8) "$memGb GB" `
    "Com menos de 8 GB, use o caminho de container (26ai Free lite) em vez da VM."

# 2. Disco livre
$discoGb = [math]::Round((Get-PSDrive C).Free / 1GB, 1)
Resultado "Espaco livre em C:" ($discoGb -ge 80) "$discoGb GB livres" `
    "A box + a VM passam de 60 GB. Libere espaco ou mude a pasta das VMs para outro disco."

# 3. Virtualizacao na BIOS
$virt = (Get-CimInstance Win32_ComputerSystem).HypervisorPresent
$virtOk = (Get-CimInstance Win32_Processor).VirtualizationFirmwareEnabled -ne $false
Resultado "Virtualizacao (VT-x/AMD-V)" $virtOk $(if ($virtOk) { "habilitada" } else { "desabilitada" }) `
    "Habilite VT-x / AMD-V (SVM) na BIOS."

# 4. Hipervisor do Windows — informativo, NAO e erro
# HypervisorPresent indica apenas que um hipervisor esta ativo (Hyper-V, WSL2, Docker Desktop,
# Credential Guard). Hyper-V e uma plataforma de virtualizacao valida para o Oracle;
# o ponto de atencao vale so para quem escolheu o caminho VirtualBox.
if ($virt) {
    Write-Host ("[info] {0,-28} {1}" -f "Hipervisor do Windows", "ATIVO (Hyper-V / WSL2 / Docker Desktop)") -ForegroundColor Cyan
    Write-Host "        -> VirtualBox ate funciona junto (7.1+), mas costuma perder desempenho." -ForegroundColor Gray
    Write-Host "        -> Se a VM travar ou ficar lenta, as opcoes sao: usar o caminho de container," -ForegroundColor Gray
    Write-Host "           ou desligar o hipervisor (Admin, reinicia): bcdedit /set hypervisorlaunchtype off" -ForegroundColor Gray
    Write-Host "        -> Voltar depois: bcdedit /set hypervisorlaunchtype auto" -ForegroundColor Gray
} else {
    Write-Host ("[ OK ] {0,-28} {1}" -f "Hipervisor do Windows", "inativo — caminho livre para o VirtualBox") -ForegroundColor Green
}

# 5. VirtualBox
$vbox = Get-Command VBoxManage.exe -ErrorAction SilentlyContinue
if (-not $vbox -and (Test-Path "C:\Program Files\Oracle\VirtualBox\VBoxManage.exe")) {
    $vbox = Get-Item "C:\Program Files\Oracle\VirtualBox\VBoxManage.exe"
}
if ($vbox) { $vboxVer = (& $vbox.Path --version) } else { $vboxVer = "nao encontrado" }
Resultado "VirtualBox" ([bool]$vbox) $vboxVer "Instale em https://www.virtualbox.org/wiki/Downloads"

# 6. Vagrant
$vag = Get-Command vagrant -ErrorAction SilentlyContinue
$vagVer = if ($vag) { (& vagrant --version) } else { "nao encontrado" }
Resultado "Vagrant" ([bool]$vag) $vagVer "Instale em https://developer.hashicorp.com/vagrant/downloads e reabra o terminal."

# 7. Git
$git = Get-Command git -ErrorAction SilentlyContinue
Resultado "Git" ([bool]$git) $(if ($git) { (git --version) } else { "nao encontrado" }) `
    "Opcional: da para baixar o ZIP do GitHub em vez de usar Git."

# 8. Java (para SQLcl no host)
$java = Get-Command java -ErrorAction SilentlyContinue
Resultado "Java (para SQLcl)" ([bool]$java) $(if ($java) { "presente" } else { "nao encontrado" }) `
    "So e necessario se voce for rodar SQLcl no Windows. JDK 17+ ou GraalVM."

# 9. Faixa host-only e IP do lab
$ipLab = "192.168.56.140"
$ping = Test-Connection -ComputerName $ipLab -Count 1 -Quiet -ErrorAction SilentlyContinue
if ($ping) {
    Write-Host ("[info] {0,-28} ja responde — VM ligada ou IP em uso por outra maquina." -f $ipLab) -ForegroundColor Cyan
} else {
    Write-Host ("[info] {0,-28} livre (esperado antes do primeiro 'vagrant up')." -f $ipLab) -ForegroundColor Cyan
}

Write-Host "`nResumo: itens com [ !! ] precisam de atencao antes do 'vagrant up'."
Write-Host "Detalhes em references/vagrant-virtualbox-passo-a-passo-ptbr.md`n"
