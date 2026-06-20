param(
    [string]$EnvFile = ".env.production",
    [string]$Python = ""
)

$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $ProjectRoot

New-Item -ItemType Directory -Force -Path "data" | Out-Null
New-Item -ItemType Directory -Force -Path "data\logs" | Out-Null

if ($EnvFile -and (Test-Path $EnvFile)) {
    Get-Content $EnvFile | ForEach-Object {
        $line = $_.Trim()
        if (-not $line -or $line.StartsWith("#") -or -not $line.Contains("=")) {
            return
        }
        $name, $value = $line.Split("=", 2)
        [Environment]::SetEnvironmentVariable($name.Trim(), $value.Trim(), "Process")
    }
}

if (-not $Python) {
    $VenvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
    if (Test-Path $VenvPython) {
        $Python = $VenvPython
    } else {
        $Python = "python"
    }
}

$HostValue = if ($env:APP_HOST) { $env:APP_HOST } else { "127.0.0.1" }
$PortValue = if ($env:APP_PORT) { $env:APP_PORT } else { "8000" }

& $Python -m uvicorn app.main:app --host $HostValue --port $PortValue --proxy-headers *>> data\logs\server.log
