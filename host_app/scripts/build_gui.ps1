$ErrorActionPreference = "Stop"

$HostRoot = Split-Path -Parent $PSScriptRoot
$VenvPython = Join-Path $HostRoot ".venv\Scripts\python.exe"
$WorkPath = Join-Path $HostRoot "build"
$DistPath = Join-Path $HostRoot "dist"
$IconPath = Join-Path $WorkPath "app_icon.ico"

function Invoke-CheckedPython {
    & $VenvPython @args
    if ($LASTEXITCODE -ne 0) {
        throw "O comando Python falhou com o codigo de saida $LASTEXITCODE."
    }
}

if (-not (Test-Path $VenvPython)) {
    py -3.12 -m venv (Join-Path $HostRoot ".venv")
    if ($LASTEXITCODE -ne 0) {
        throw "Nao foi possivel criar o ambiente virtual (codigo $LASTEXITCODE)."
    }
}

Invoke-CheckedPython -m pip install --upgrade pip
Invoke-CheckedPython -m pip install -e "${HostRoot}[gui,build]"
Invoke-CheckedPython (Join-Path $PSScriptRoot "generate_windows_icon.py") `
    (Join-Path $HostRoot "streamdeck_monitor\gui\assets\app_icon.svg") `
    $IconPath
Invoke-CheckedPython -m PyInstaller --clean --noconfirm `
    --workpath $WorkPath `
    --distpath $DistPath `
    (Join-Path $HostRoot "streamdeck_gui.spec")

$Executable = Join-Path $DistPath "StreamDeckMini\StreamDeckMini.exe"
if (-not (Test-Path $Executable)) {
    throw "O PyInstaller terminou sem gerar o executavel esperado: $Executable"
}

Write-Host "Build concluido em: $Executable"
