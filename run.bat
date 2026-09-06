@echo off
title Insta OSINT Engine - Runner
setlocal enabledelayedexpansion

if not exist venv\Scripts\activate.bat (
    echo [-] Virtual environment missing! Run setup.bat first.
    pause
    exit /b 1
)

call venv\Scripts\activate.bat

:: Agar command line arguments pass kiye gaye hain
if not "%~1"=="" (
    python insta_osint.py %*
    goto end
)

:: Interactive CLI Mode
echo ======================================================
echo              Insta OSINT Engine v2.0
echo ======================================================
echo.
set /p target="Enter target Instagram username: "

if "!target!"=="" (
    echo [-] Username cannot be empty.
    pause
    exit /b 1
)

echo.
echo Select scan mode:
echo   [1] Quick Dossier (Profile + Bio Links + Mentions)
echo   [2] Deep Scan (Download Media + OCR + CSV + JSON Export)
echo   [3] Custom Command Arguments
echo.
set /p mode="Choose an option [1-3] (Default 1): "

if "!mode!"=="2" (
    python insta_osint.py !target! --download --ocr --json --csv
) else if "!mode!"=="3" (
    set /p custom_args="Enter flags (e.g. --max-posts 20 --proxy http://127.0.0.1:8080): "
    python insta_osint.py !target! !custom_args!
) else (
    python insta_osint.py !target!
)

:end
echo.
echo ======================================================
echo Execution complete.
echo ======================================================
pause
