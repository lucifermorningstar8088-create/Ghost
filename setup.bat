@echo off
setlocal EnableExtensions
title Ghost - One Click Setup
cd /d "%~dp0"
echo.
echo  =========================================
echo          GHOST FULL-STACK SETUP
echo  =========================================
echo.

set "PYTHON_CMD="
where py >nul 2>nul
if not errorlevel 1 (
  py -3.12 --version >nul 2>nul
  if not errorlevel 1 set "PYTHON_CMD=py -3.12"
)
if not defined PYTHON_CMD (
  where python >nul 2>nul
  if not errorlevel 1 set "PYTHON_CMD=python"
)
if not defined PYTHON_CMD (
  echo [ERROR] Python 3.12+ not found.
  echo Install from https://www.python.org/downloads/windows/
  echo Enable "Add Python to PATH", then rerun setup.bat.
  pause
  exit /b 1
)
%PYTHON_CMD% --version

where node >nul 2>nul
if errorlevel 1 (
  echo [ERROR] Node.js was not found.
  echo Install Node.js LTS from https://nodejs.org/ then rerun setup.bat.
  pause
  exit /b 1
)
where npm >nul 2>nul
if errorlevel 1 (
  echo [ERROR] npm was not found. Repair your Node.js LTS installation.
  pause
  exit /b 1
)
node --version
npm --version

if not exist "apps\api\requirements.txt" (
  echo [ERROR] apps\api\requirements.txt not found. Use the Ghost repository root.
  pause
  exit /b 1
)
if not exist "apps\web\package.json" (
  echo [ERROR] apps\web\package.json not found.
  pause
  exit /b 1
)

echo.
echo [1/5] Preparing isolated Python environment...
if not exist "apps\api\.venv\Scripts\python.exe" (
  %PYTHON_CMD% -m venv "apps\api\.venv"
  if errorlevel 1 goto failed
)
echo.
echo [2/5] Installing API dependencies...
"apps\api\.venv\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 goto failed
"apps\api\.venv\Scripts\python.exe" -m pip install -r "apps\api\requirements.txt"
if errorlevel 1 goto failed

echo.
echo [3/5] Installing web dependencies...
pushd "apps\web"
call npm install
if errorlevel 1 (
  popd
  goto failed
)
popd

echo.
echo [4/5] Checking API import...
pushd "apps\api"
".venv\Scripts\python.exe" -c "from app.main import app; print('API import OK:', app.title)"
if errorlevel 1 (
  popd
  goto failed
)
popd

echo.
echo [5/5] Checking frontend production build...
pushd "apps\web"
call npm run build
if errorlevel 1 (
  popd
  goto failed
)
popd

echo.
echo =========================================
echo SETUP COMPLETE
echo =========================================
echo Double-click run.bat to launch Ghost UI + API.
echo UI:  http://127.0.0.1:5173
echo API: http://127.0.0.1:8000
echo.
echo This setup does not create credentials or enable external providers.
pause
exit /b 0

:failed
echo.
echo [ERROR] Setup failed. Read the error above, fix it, and rerun setup.bat.
echo The script can be rerun safely.
pause
exit /b 1
