@echo off
setlocal EnableExtensions
title Ghost - Local API
cd /d "%~dp0"

if not exist "apps\api\.venv\Scripts\python.exe" (
  echo [ERROR] Ghost is not set up yet.
  echo First double-click setup.bat.
  echo.
  pause
  exit /b 1
)

echo.
echo  ========================================
echo        GHOST - LOCAL START
echo  ========================================
echo.
echo This launcher uses a local SQLite database by default.
echo It will not apply migrations to a hosted database.
echo Press Ctrl+C in this window to stop the API.
echo.

pushd "apps\api"

rem Keep local runs safe by default. Opt into a preconfigured DB only
rem when the operator explicitly sets GHOST_USE_CONFIGURED_DATABASE=true.
if /i not "%GHOST_USE_CONFIGURED_DATABASE%"=="true" (
  set "DATABASE_URL=sqlite+pysqlite:///./ghost.db"
)

echo [1/2] Applying local database migrations...
".venv\Scripts\python.exe" -m alembic upgrade head
if errorlevel 1 (
  echo.
  echo [ERROR] Database migration failed. The API was not started.
  popd
  pause
  exit /b 1
)

echo.
echo [2/2] Starting Ghost API...
echo API:      http://127.0.0.1:8000
echo API docs: http://127.0.0.1:8000/docs
echo Health:   http://127.0.0.1:8000/health/ready
echo.
start "" http://127.0.0.1:8000/docs
".venv\Scripts\python.exe" -m uvicorn app.main:app --host 127.0.0.1 --port 8000
set "GHOST_EXIT_CODE=%errorlevel%"
popd

echo.
echo Ghost API stopped with exit code %GHOST_EXIT_CODE%.
pause
exit /b %GHOST_EXIT_CODE%
