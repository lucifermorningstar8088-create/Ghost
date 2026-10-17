# Ghost local setup for Windows PowerShell
$ErrorActionPreference = "Stop"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "../..")).Path
$ApiDir = Join-Path $RepoRoot "apps/api"
$WebDir = Join-Path $RepoRoot "apps/web"

function Require-Command([string]$Name, [string]$Hint) {
  if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
    throw "$Name was not found. $Hint"
  }
}

Require-Command "python" "Install Python 3.12+ and enable Add Python to PATH."
Require-Command "node" "Install Node.js LTS and reopen PowerShell."
Require-Command "npm" "Install Node.js LTS (npm is included) and reopen PowerShell."

Write-Host "== Ghost local setup ==" -ForegroundColor Cyan
python --version
node --version
npm --version

$Venv = Join-Path $ApiDir ".venv"
if (-not (Test-Path $Venv)) { python -m venv $Venv }
$Python = Join-Path $Venv "Scripts/python.exe"
$Pip = Join-Path $Venv "Scripts/pip.exe"

Write-Host "Installing API dependencies..." -ForegroundColor Cyan
& $Python -m pip install --upgrade pip
& $Pip install -r (Join-Path $ApiDir "requirements.txt")

Write-Host "Installing web dependencies..." -ForegroundColor Cyan
Push-Location $WebDir
try { npm install } finally { Pop-Location }

$WebEnv = Join-Path $WebDir ".env.local"
if (-not (Test-Path $WebEnv)) {
  Copy-Item (Join-Path $WebDir ".env.example") $WebEnv
  Write-Host "Created apps/web/.env.local from example." -ForegroundColor Green
}

Write-Host ""
Write-Host "Setup finished. No cloud credentials are required for the local SQLite default." -ForegroundColor Green
Write-Host "Next: run .\scripts\windows\run-ghost.ps1"
Write-Host "Note: dependency setup only; no database migrations or social account connections are performed."
