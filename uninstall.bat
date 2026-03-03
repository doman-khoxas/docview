@echo off
REM ============================================================
REM  DocView — Remove File Associations
REM  Double-click to unregister DocView as a PDF handler.
REM ============================================================

title DocView Uninstaller

python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found.
    pause
    exit /b 1
)

cd /d "%~dp0"

echo.
echo ============================================================
echo   DocView - File Association Uninstaller
echo ============================================================
echo.

python install.py --uninstall

echo.
pause
