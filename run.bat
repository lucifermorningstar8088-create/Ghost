@echo off
setlocal EnableExtensions
title Ghost - Full Stack Launcher
cd /d "%~dp0"

if not exist "apps\api\.venv\Scripts\python.exe" (
  echo [ERROR] Run setup.bat first.
  pause
  exit /b 1
)
if not exist "apps\web\node_modules\vite\bin\vite.js" (
  echo [ERROR] Web dependencies are missing. Run setup.bat first.
  pause
  exit /b 1
)

echo.
echo  =========================================
echo         GHOST OPERATIONS CENTER
echo  =========================================
echo.
echo Starting local API and professional web UI...
echo Local database default: SQLite
echo External providers and background workers stay disabled unless configured.
echo Close the API and UI terminal windows to stop Ghost.
echo.

set "DATABASE_URL=sqlite+pysqlite:///./ghost.db"
start "Ghost API" /min cmd /k "cd /d ""%~dp0apps\api"" && .venv\Scripts\python.exe -m alembic upgrade head && .venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000"
timeout /t 3 /nobreak >nul
start "Ghost Web UI" /min cmd /k "cd /d ""%~dp0apps\web"" && npm run dev -- --host 127.0.0.1"
echo Waiting for services to initialize...
timeout /t 3 /nobreak >nul
start "" "http://127.0.0.1:5173"
echo.
echo Ghost launch requested.
echo UI:  http://127.0.0.1:5173
echo API: http://127.0.0.1:8000
echo API docs (developer view): http://127.0.0.1:8000/docs
echo.
echo If a terminal shows an error, keep it open to read the message.
echo Stop Ghost by closing the "Ghost API" and "Ghost Web UI" windows.
pause
