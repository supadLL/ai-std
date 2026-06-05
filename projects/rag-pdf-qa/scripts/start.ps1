param(
    [switch]$Reload,
    [int]$Port = 8000
)

$ErrorActionPreference = "Stop"

$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $ProjectRoot

& "$PSScriptRoot\check_environment.ps1" -Port $Port

$listeners = @(Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue)
if ($listeners.Count -gt 0) {
    $pids = ($listeners | Select-Object -ExpandProperty OwningProcess -Unique) -join ", "
    Write-Host "Port $Port is already in use by PID(s): $pids. Close the old uvicorn process and retry." -ForegroundColor Red
    exit 1
}

$arguments = @(
    "-m", "uvicorn",
    "app.main:app",
    "--host", "127.0.0.1",
    "--port", "$Port"
)

if ($Reload) {
    $arguments += "--reload"
}

Write-Host "Starting Local Knowledge RAG Agent on http://127.0.0.1:$Port/app" -ForegroundColor Cyan
& ".\.venv\Scripts\python.exe" @arguments
