@echo off
REM ============================================================
REM  DocView v2.0.0 — Build Executable
REM  Packages DocView into a single .exe using PyInstaller.
REM ============================================================

title DocView Build

REM Check for Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Install Python 3.10+ from https://python.org
    pause
    exit /b 1
)

REM Navigate to script directory
cd /d "%~dp0"

REM Display version info
echo.
echo ============================================================
echo  DocView Build System
echo ============================================================
python -c "from app.version import version_string; print(f'  {version_string()}')" 2>nul
echo.

REM Activate venv if it exists
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
) else (
    echo [DocView] Creating virtual environment...
    python -m venv .venv
    call .venv\Scripts\activate.bat
)

REM Install build dependencies
echo [DocView] Installing build dependencies...
pip install -q -r requirements.txt
pip install -q pyinstaller

REM Generate icon if missing
if not exist "assets\docview.ico" (
    echo [DocView] Generating application icon...
    python assets\generate_icon.py
)

REM Clean previous builds
echo [DocView] Cleaning previous builds...
python build.py --clean

REM Build single executable
echo [DocView] Building executable...
echo.
python build.py

echo.
echo ============================================================
if exist "dist\DocView.exe" (
    echo   BUILD COMPLETE: dist\DocView.exe
    echo   You can move this file anywhere and run it standalone.
    echo.
    echo   Features included:
    echo     - PDF viewing, annotation, and editing
    echo     - Multi-document tabs with continuous viewport
    echo     - Page management: extract, insert, delete, rotate, reorder
    echo     - PDF compression with image downscaling
    echo     - Digital signatures (PFX/P12 + visible stamp)
    echo     - Metadata stripping (OPSEC)
    echo     - Redaction with preview and batch apply
    echo     - Image insertion, shape fill, freehand draw
    echo     - Search, print, undo/redo, keyboard navigation
    echo     - Crash logging to crashlog.txt
) else if exist "dist\DocView" (
    echo   BUILD COMPLETE: dist\DocView\
    echo   Distribute the entire folder.
) else (
    echo   BUILD FAILED — check the output above for errors.
)
echo ============================================================
echo.

deactivate
pause
