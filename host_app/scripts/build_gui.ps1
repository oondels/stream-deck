$ErrorActionPreference = "Stop"

$HostRoot = Split-Path -Parent $PSScriptRoot
$VenvPython = Join-Path $HostRoot ".venv\Scripts\python.exe"

if (-not (Test-Path $VenvPython)) {
    py -3.12 -m venv (Join-Path $HostRoot ".venv")
}

& $VenvPython -m pip install --upgrade pip
& $VenvPython -m pip install -e "${HostRoot}[gui,build]"
Push-Location $HostRoot
try {
    & $VenvPython -m PyInstaller --clean --noconfirm streamdeck_gui.spec
}
finally {
    Pop-Location
}

Write-Host "Build concluido em: $HostRoot\dist\StreamDeckMini"
