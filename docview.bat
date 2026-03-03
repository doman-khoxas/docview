@echo off
REM ============================================================
REM  DocView — Launch Script
REM  Installs dependencies if needed, then launches the app.
REM ============================================================

title DocView

REM Check for Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Install Python 3.9+ from https://python.org
    echo         Make sure to check "Add Python to PATH" during install.
    pause
    exit /b 1
)

REM Navigate to script directory
cd /d "%~dp0"

REM Create virtual environment if it doesn't exist
if not exist ".venv" (
    echo [DocView] Creating virtual environment...
    python -m venv .venv
)

REM Activate virtual environment
call .venv\Scripts\activate.bat

REM Install/update dependencies
echo [DocView] Checking dependencies...
pip install -q -r requirements.txt 2>nul
if errorlevel 1 (
    echo [DocView] Installing dependencies...
    pip install PyMuPDF>=1.23 customtkinter>=5.2.0 Pillow>=10.0
)

REM Launch DocView
echo [DocView] Starting...
python main.py %*

REM Deactivate on exit
deactivate
