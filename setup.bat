@echo off
title Insta OSINT Engine - Windows Setup
echo ======================================================
echo        Insta OSINT Engine - Windows Installer
echo ======================================================
echo.

:: Check Python installation
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [-] Error: Python is not installed or not in PATH!
    echo [*] Download Python from https://www.python.org and check "Add Python to PATH".
    pause
    exit /b 1
)

echo [+] Python detected.
echo [+] Initializing virtual environment (venv)...

if not exist venv (
    python -m venv venv
    echo [+] Created 'venv' directory.
) else (
    echo [*] Existing 'venv' found. Skipping creation.
)

echo [+] Activating virtual environment...
call venv\Scripts\activate.bat

echo [+] Updating pip...
python -m pip install --upgrade pip

echo [+] Installing packages from requirements.txt...
pip install -r requirements.txt

echo.
echo [*] Checking Tesseract OCR for Windows...
if exist "C:\Program Files\Tesseract-OCR\tesseract.exe" (
    echo [+] Tesseract OCR found at C:\Program Files\Tesseract-OCR\tesseract.exe
) else (
    echo [!] WARNING: Tesseract OCR was not found in default path.
    echo [!] If you need --ocr support, install from:
    echo     https://github.com/UB-Mannheim/tesseract/wiki
)

echo.
echo ======================================================
echo [+] Windows installation complete!
echo [*] Use run.bat to launch the tool anytime.
echo ======================================================
pause
