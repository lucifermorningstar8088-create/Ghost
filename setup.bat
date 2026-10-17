@echo off
setlocal EnableExtensions
title Ghost - First Time Setup
cd /d "%~dp0"

echo.
echo  ========================================
echo        GHOST - ONE CLICK SETUP
echo  ========================================
echo.

where py >nul 2>nul
if %errorlevel%==0 (
  py -3.12 --version >nul 2>nul
  if not errorlevel 1 (
    set "PYTHON_CMD=py -3.12"
    goto python_found
  )
  py -3 --version >nul 2>nul
  if not errorlevel 1 (
    set "PYTHON_CMD=py -3"
    goto python_found
  )
)

where python >nul 2>nul
if not errorlevel 1 (
  python --version
  set "PYTHON_CMD=python"
  goto python_found
)

echo [ERROR] Python was not found.
echo Install Python 3.12 from https://www.python.org/downloads/windows/
echo During setup, enable "Add python.exe to PATH", then run setup.bat again.
echo.
pause
exit /b 1

:python_found
echo [1/4] Python found.
%PYTHON_CMD% --version
if not exist "apps\api\requirements.txt" (
  echo [ERROR] apps\api\requirements.txt not found. Run this from the Ghost repository.
  pause
  exit /b 1
)

echo.
echo [2/4] Creating the isolated API environment...
if not exist "apps\api\.venv\Scripts\python.exe" (
  %PYTHON_CMD% -m venv "apps\api\.venv"
  if errorlevel 1 goto setup_failed
) else (
  echo Existing virtual environment found. Reusing it.
)

echo.
echo [3/4] Installing/updating Ghost API dependencies...
"apps\api\.venv\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 goto setup_failed
"apps\api\.venv\Scripts\python.exe" -m pip install -r "apps\api\requirements.txt"
if errorlevel 1 goto setup_failed

echo.
echo [4/4] Checking that the API imports successfully...
pushd "apps\api"
".venv\Scripts\python.exe" -c "from app.main import app; print('Ghost API import OK:', app.title)"
if errorlevel 1 (
  popd
  goto setup_failed
)
popd

echo.
echo ========================================
echo SETUP COMPLETE
echo ========================================
echo Double-click run.bat to start Ghost API.
echo Local API docs: http://127.0.0.1:8000/docs
echo Local health:   http://127.0.0.1:8000/health/ready
echo.
echo Note: this repository currently provides the API foundation.
echo Social platforms, provider adapters, Telegram, and a full web UI
echo are not automatically configured by these launcher scripts.
echo.
pause
exit /b 0

:setup_failed
echo.
echo [ERROR] Setup did not complete. Check the error shown above.
echo Fix the issue and run setup.bat again. It is safe to rerun.
echo.
pause
exit /b 1
