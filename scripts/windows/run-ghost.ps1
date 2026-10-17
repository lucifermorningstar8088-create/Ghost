# Start Ghost API and web UI in separate PowerShell windows.
$ErrorActionPreference = "Stop"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "../..")).Path
$ApiDir = Join-Path $RepoRoot "apps/api"
$WebDir = Join-Path $RepoRoot "apps/web"
$Python = Join-Path $ApiDir ".venv/Scripts/python.exe"

if (-not (Test-Path $Python)) { throw "API virtual environment missing. Run setup-ghost.ps1 first." }
if (-not (Test-Path (Join-Path $WebDir "node_modules"))) { throw "Web dependencies missing. Run setup-ghost.ps1 first." }

$ApiCommand = "Set-Location '$ApiDir'; `$env:PYTHONPATH='.'; & '$Python' -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000"
$WebCommand = "Set-Location '$WebDir'; npm run dev -- --host 127.0.0.1"

Start-Process powershell -ArgumentList @("-NoExit", "-ExecutionPolicy", "Bypass", "-Command", $ApiCommand)
Start-Sleep -Seconds 2
Start-Process powershell -ArgumentList @("-NoExit", "-ExecutionPolicy", "Bypass", "-Command", $WebCommand)

Write-Host ""
Write-Host "Ghost API:  http://127.0.0.1:8000/health/live" -ForegroundColor Cyan
Write-Host "Readiness:  http://127.0.0.1:8000/health/ready" -ForegroundColor Cyan
Write-Host "Migrations: http://127.0.0.1:8000/health/migrations" -ForegroundColor Cyan
Write-Host "Web UI:     http://127.0.0.1:5173" -ForegroundColor Green
Write-Host "Swagger:    http://127.0.0.1:8000/docs" -ForegroundColor Cyan
Write-Host "Use Ctrl+C in the two opened windows to stop each service."
