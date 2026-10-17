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
  echo Install from https://www.python.org/downloads/windows/ and enable Add Python to PATH.
  pause
  exit /b 1
)
%PYTHON_CMD% --version

where node >nul 2>nul
if errorlevel 1 (
  echo [ERROR] Node.js was not found. Install Node.js LTS from https://nodejs.org/
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
call npm --version

if not exist "scripts\windows\setup-ghost.ps1" (
  echo [ERROR] Required setup script is missing: scripts\windows\setup-ghost.ps1
  echo Make sure you are running this from the extracted Ghost repository root.
  pause
  exit /b 1
)

echo.
echo Delegating setup to the maintained project setup script...
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\windows\setup-ghost.ps1"
if errorlevel 1 goto failed

echo.
echo Running frontend production build validation...
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
echo Setup does not apply database migrations or connect external accounts.
pause
exit /b 0

:failed
echo.
echo [ERROR] Setup failed. Read the error above, fix it, and rerun setup.bat.
echo The script can be rerun safely; it does not reset the database.
pause
exit /b 1
