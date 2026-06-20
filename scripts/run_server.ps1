$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $ProjectRoot

New-Item -ItemType Directory -Force -Path "data" | Out-Null

$VenvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
if (Test-Path $VenvPython) {
    $Python = $VenvPython
} else {
    $Python = "python"
}

$HostValue = if ($env:APP_HOST) { $env:APP_HOST } else { "127.0.0.1" }
$PortValue = if ($env:APP_PORT) { $env:APP_PORT } else { "8000" }

& $Python -m uvicorn app.main:app --host $HostValue --port $PortValue *>> data\server.log
