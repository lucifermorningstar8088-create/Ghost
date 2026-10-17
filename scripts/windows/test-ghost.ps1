param(
  [string]$ApiBaseUrl = "http://127.0.0.1:8000",
  [string]$WebDir = "",
  [switch]$SkipBuild
)

$ErrorActionPreference = "Stop"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "../..")).Path
$ApiDir = Join-Path $RepoRoot "apps/api"
if (-not $WebDir) { $WebDir = Join-Path $RepoRoot "apps/web" }
$Python = Join-Path $ApiDir ".venv/Scripts/python.exe"

function Invoke-HealthCheck([string]$Path, [string]$ExpectedStatusCode = "200") {
  $Url = "$($ApiBaseUrl.TrimEnd('/'))$Path"
  Write-Host "Checking $Url ..." -ForegroundColor Cyan
  try {
    $Response = Invoke-WebRequest -Uri $Url -Method Get -TimeoutSec 10
    if ([string]$Response.StatusCode -ne $ExpectedStatusCode) {
      throw "Unexpected HTTP status $($Response.StatusCode) from $Path"
    }
    $Payload = $Response.Content | ConvertFrom-Json
    Write-Host "  HTTP $($Response.StatusCode); status=$($Payload.status)" -ForegroundColor Green
    return $Payload
  } catch {
    throw "Health check failed for $Url. Ensure Ghost API is running and inspect its terminal. Details: $($_.Exception.Message)"
  }
}

Write-Host "== Ghost local test runner ==" -ForegroundColor Cyan
if (-not (Test-Path $Python)) {
  throw "API virtual environment not found. Run scripts/windows/setup-ghost.ps1 first."
}
if (-not (Test-Path (Join-Path $WebDir "node_modules"))) {
  throw "Web dependencies not found. Run scripts/windows/setup-ghost.ps1 first."
}

# The API should be started with scripts/windows/run-ghost.ps1 before this script.
$null = Invoke-HealthCheck "/health/live"
$Readiness = Invoke-HealthCheck "/health/ready"
if ($Readiness.checks.database -ne "ok") {
  throw "API is reachable, but database readiness is not ok. Review DATABASE_URL and the API terminal."
}
$Migrations = Invoke-HealthCheck "/health/migrations"
if ($Migrations.status -ne "up_to_date") {
  Write-Warning "Migration status is '$($Migrations.status)'. This script will not apply migrations. Review the migration graph and back up data before making schema changes."
}

Write-Host "Running API tests..." -ForegroundColor Cyan
Push-Location $ApiDir
try {
  & $Python -m pytest
  if ($LASTEXITCODE -ne 0) { throw "API tests failed with exit code $LASTEXITCODE." }
} finally {
  Pop-Location
}

Push-Location $WebDir
try {
  if (-not $SkipBuild) {
    Write-Host "Running frontend typecheck..." -ForegroundColor Cyan
    npm run typecheck
    if ($LASTEXITCODE -ne 0) { throw "Frontend typecheck failed with exit code $LASTEXITCODE." }
    Write-Host "Building frontend..." -ForegroundColor Cyan
    npm run build
    if ($LASTEXITCODE -ne 0) { throw "Frontend build failed with exit code $LASTEXITCODE." }
  } else {
    Write-Host "Skipping frontend typecheck/build because -SkipBuild was supplied." -ForegroundColor Yellow
  }
} finally {
  Pop-Location
}

Write-Host ""
Write-Host "All requested local checks passed." -ForegroundColor Green
Write-Host "This verifies API tests, configured health endpoints, and frontend checks; it does not prove OAuth, social publishing, provider adapters, or Telegram delivery are live."
