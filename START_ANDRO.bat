@echo off
cd /d "%~dp0"

:: Fast direct launch with error guard
"%~dp0.venv\Scripts\python.exe" "%~dp0gui.py"

if %ERRORLEVEL% neq 0 (
    echo.
    echo ======================================================================
    echo  [ERROR] ANDRO GUI encountered an issue (Exit code: %ERRORLEVEL%).
    echo  Path: "%~dp0.venv\Scripts\python.exe"
    echo ======================================================================
    echo.
    pause
)
