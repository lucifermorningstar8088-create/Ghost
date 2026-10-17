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

Require-Command "node" "Install Node.js LTS and reopen PowerShell."
Require-Command "npm" "Install Node.js LTS (npm is included) and reopen PowerShell."

# Select the same Python interpreter for both version validation and venv creation.
# Prefer the Windows Python launcher so an installed Python 3.12 is not bypassed
# by a different older interpreter earlier on PATH.
$PythonCommand = $null
$PythonPrefixArgs = @()
if (Get-Command "py" -ErrorAction SilentlyContinue) {
  & py -3.12 --version *> $null
  if ($LASTEXITCODE -eq 0) {
    $PythonCommand = "py"
    $PythonPrefixArgs = @("-3.12")
  }
}
if (-not $PythonCommand) {
  Require-Command "python" "Install Python 3.12+ and enable Add Python to PATH."
  $VersionOutput = & python --version 2>&1
  if ($LASTEXITCODE -ne 0 -or $VersionOutput -notmatch "Python\s+(\d+)\.(\d+)") {
    throw "Could not determine the Python version. Install Python 3.12+ and reopen PowerShell."
  }
  $Major = [int]$Matches[1]
  $Minor = [int]$Matches[2]
  if (($Major -lt 3) -or (($Major -eq 3) -and ($Minor -lt 12))) {
    throw "Python 3.12+ is required; found '$VersionOutput'. Install Python 3.12 or newer."
  }
  $PythonCommand = "python"
}

Write-Host "== Ghost local setup ==" -ForegroundColor Cyan
if ($PythonCommand -eq "py") {
  & py @PythonPrefixArgs --version
} else {
  & python --version
}
node --version
npm --version

$Venv = Join-Path $ApiDir ".venv"
if (-not (Test-Path $Venv)) {
  if ($PythonCommand -eq "py") {
    & py @PythonPrefixArgs -m venv $Venv
  } else {
    & python -m venv $Venv
  }
  if ($LASTEXITCODE -ne 0) { throw "Python virtual environment creation failed with exit code $LASTEXITCODE." }
}
$Python = Join-Path $Venv "Scripts/python.exe"
$Pip = Join-Path $Venv "Scripts/pip.exe"

Write-Host "Installing API dependencies..." -ForegroundColor Cyan
& $Python -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) { throw "pip upgrade failed with exit code $LASTEXITCODE." }
& $Pip install -r (Join-Path $ApiDir "requirements.txt")
if ($LASTEXITCODE -ne 0) { throw "API dependency installation failed with exit code $LASTEXITCODE." }

Write-Host "Installing web dependencies..." -ForegroundColor Cyan
Push-Location $WebDir
try {
  npm install
  if ($LASTEXITCODE -ne 0) { throw "Web dependency installation failed with exit code $LASTEXITCODE." }
} finally { Pop-Location }

$WebEnv = Join-Path $WebDir ".env.local"
if (-not (Test-Path $WebEnv)) {
  Copy-Item (Join-Path $WebDir ".env.example") $WebEnv
  Write-Host "Created apps/web/.env.local from example." -ForegroundColor Green
}

Write-Host ""
Write-Host "Setup finished. No cloud credentials are required for the local SQLite default." -ForegroundColor Green
Write-Host "Next: run .\scripts\windows\run-ghost.ps1"
Write-Host "Note: dependency setup only; no database migrations or social account connections are performed."
