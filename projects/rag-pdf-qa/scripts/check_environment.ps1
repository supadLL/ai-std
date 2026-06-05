param(
    [int]$Port = 8000
)

$ErrorActionPreference = "Stop"

$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $ProjectRoot

$hasError = $false

function Write-CheckOk {
    param([string]$Message)
    Write-Host "[OK] $Message" -ForegroundColor Green
}

function Write-CheckWarn {
    param([string]$Message)
    Write-Host "[WARN] $Message" -ForegroundColor Yellow
}

function Write-CheckFail {
    param([string]$Message)
    Write-Host "[FAIL] $Message" -ForegroundColor Red
    $script:hasError = $true
}

Write-Host "Checking Local Knowledge RAG Agent environment..." -ForegroundColor Cyan
Write-Host "Project root: $ProjectRoot"

if (Test-Path ".venv\Scripts\python.exe") {
    Write-CheckOk "Virtual environment found: .venv"
} else {
    Write-CheckFail "Missing .venv. Run: python -m venv .venv"
}

if (Test-Path ".env") {
    Write-CheckOk ".env found"
} elseif (Test-Path ".env.example") {
    Write-CheckFail "Missing .env. Run: Copy-Item .env.example .env, then set DEEPSEEK_API_KEY."
} else {
    Write-CheckFail "Missing .env and .env.example"
}

if (Test-Path "requirements.txt") {
    Write-CheckOk "requirements.txt found"
} else {
    Write-CheckFail "Missing requirements.txt"
}

try {
    $pythonCommand = Get-Command python -ErrorAction Stop
    Write-CheckOk "System python found: $($pythonCommand.Source)"
} catch {
    Write-CheckWarn "System python was not found in PATH. The .venv python can still be used if it exists."
}

if (Test-Path ".venv\Scripts\python.exe") {
    $missingModules = @()
    foreach ($module in @("fastapi", "uvicorn", "pdfplumber", "fastembed", "qdrant_client")) {
        & ".\.venv\Scripts\python.exe" -c "import $module" 2>$null
        if ($LASTEXITCODE -ne 0) {
            $missingModules += $module
        }
    }

    if ($missingModules.Count -eq 0) {
        Write-CheckOk "Core Python dependencies are importable"
    } else {
        Write-CheckFail "Missing Python modules in .venv: $($missingModules -join ', '). Run: .\.venv\Scripts\python.exe -m pip install -r requirements.txt"
    }

    $missingOcrModules = @()
    foreach ($module in @("fitz", "pytesseract", "PIL")) {
        & ".\.venv\Scripts\python.exe" -c "import $module" 2>$null
        if ($LASTEXITCODE -ne 0) {
            $missingOcrModules += $module
        }
    }

    if ($missingOcrModules.Count -eq 0) {
        Write-CheckOk "OCR Python dependencies are importable"
    } else {
        Write-CheckWarn "Optional OCR Python modules are missing: $($missingOcrModules -join ', '). OCR needs: .\.venv\Scripts\python.exe -m pip install -r requirements.txt"
    }
}

$listeners = @(Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue)
if ($listeners.Count -gt 0) {
    $pids = ($listeners | Select-Object -ExpandProperty OwningProcess -Unique) -join ", "
    Write-CheckWarn "Port $Port is already in use by PID(s): $pids. Stop the old service before starting a new one."
} else {
    Write-CheckOk "Port $Port is available"
}

if ($hasError) {
    Write-Host "Environment check failed. Fix the items above and retry." -ForegroundColor Red
    exit 1
}

Write-Host "Environment check passed." -ForegroundColor Green
