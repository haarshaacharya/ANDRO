@echo off
setlocal EnableDelayedExpansion
title ANDRO — Debug Launcher

echo ======================================================================
echo  🤖 ANDRO — Diagnostic & Debug Mode Launcher
echo ======================================================================
echo.

:: 1. Change to project directory
cd /d "%~dp0"
echo [DEBUG] Current Directory : %CD%
echo [DEBUG] Batch Script Path : %~dp0
echo.

:: 2. Check if .venv exists
if not exist "%~dp0.venv\" (
    echo [ERROR] Virtual environment directory not found!
    echo         Expected: "%~dp0.venv"
    echo.
    goto :END_DEBUG
)

:: 3. Check if python.exe exists
if not exist "%~dp0.venv\Scripts\python.exe" (
    echo [ERROR] Python executable not found in .venv!
    echo         Expected: "%~dp0.venv\Scripts\python.exe"
    echo.
    goto :END_DEBUG
)

:: 4. Check if gui.py exists
if not exist "%~dp0gui.py" (
    echo [ERROR] gui.py not found in project directory!
    echo         Expected: "%~dp0gui.py"
    echo.
    goto :END_DEBUG
)

echo [DEBUG] Python Executable : "%~dp0.venv\Scripts\python.exe"
echo [DEBUG] Python Version    :
"%~dp0.venv\Scripts\python.exe" --version
echo.
echo [DEBUG] Starting ANDRO GUI with full console output...
echo ======================================================================
echo.

"%~dp0.venv\Scripts\python.exe" "%~dp0gui.py"

echo.
echo ======================================================================
echo [DEBUG] ANDRO process ended with exit code: %ERRORLEVEL%
echo ======================================================================

:END_DEBUG
echo.
pause
