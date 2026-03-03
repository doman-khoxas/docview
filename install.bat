@echo off
REM ============================================================
REM  DocView — Register as Default PDF Application
REM  Double-click this file to register DocView as a PDF handler.
REM  Then set it as default via: Settings > Default Apps > .pdf
REM ============================================================

title DocView Installer

REM Check for Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Install Python 3.10+ from https://python.org
    pause
    exit /b 1
)

REM Navigate to script directory
cd /d "%~dp0"

echo.
echo ============================================================
echo   DocView - File Association Installer
echo ============================================================
echo.
echo   This will register DocView as a PDF file handler so you
echo   can set it as your default PDF application.
echo.

REM Check if we should install for all users
set SYSTEM_FLAG=
if "%1"=="--system" (
    set SYSTEM_FLAG=--system
    echo   Mode: System-wide (all users)
) else (
    echo   Mode: Current user only
)

echo.
python install.py %SYSTEM_FLAG%

echo.
echo ============================================================
echo   Next steps:
echo     1. Open Windows Settings
echo     2. Go to Default Apps
echo     3. Search for ".pdf"
echo     4. Select "DocView" from the list
echo.
echo   Or: Right-click any PDF file ^> Open With ^> DocView
echo ============================================================
echo.

pause
