@echo off
setlocal EnableExtensions
title Ghost - Full Stack Launcher
cd /d "%~dp0"

if not exist "scripts\windows\run-ghost.ps1" (
  echo [ERROR] Required runner missing: scripts\windows\run-ghost.ps1
  pause
  exit /b 1
)
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
echo Starting local API and web UI...
echo Database migrations are NOT applied automatically.
echo External providers are not assumed connected.
echo.

powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\windows\run-ghost.ps1"
if errorlevel 1 (
  echo.
  echo [ERROR] Startup failed. Review the diagnostic message above.
  pause
  exit /b 1
)
exit /b 0
