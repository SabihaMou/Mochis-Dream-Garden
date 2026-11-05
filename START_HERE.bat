@echo off
setlocal
cd /d "%~dp0"
title Mochi's Dream Garden - Launcher
set "PYTHON_CMD="
py -3.10 --version >nul 2>&1
if not errorlevel 1 set "PYTHON_CMD=py -3.10"
if not defined PYTHON_CMD (
    py -3.11 --version >nul 2>&1
    if not errorlevel 1 set "PYTHON_CMD=py -3.11"
)
if not defined PYTHON_CMD (
    echo Python 3.10 or 3.11 was not found.
    echo Install Python 3.10 from https://www.python.org/downloads/
    pause
    exit /b 1
)
if not exist ".venv\Scripts\python.exe" (
    echo Creating game environment...
    %PYTHON_CMD% -m venv .venv
    if errorlevel 1 goto :error
)
echo Installing/checking Pygame...
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto :error
echo Starting Mochi's Dream Garden...
".venv\Scripts\python.exe" main.py
if errorlevel 1 goto :error
exit /b 0
:error
echo.
echo Something went wrong. Please screenshot this window if you need help.
pause
exit /b 1
