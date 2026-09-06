# Insta OSINT Engine - PowerShell Setup Script
Write-Host "======================================================" -ForegroundColor Cyan
Write-Host "       Insta OSINT Engine - PowerShell Setup" -ForegroundColor Cyan
Write-Host "======================================================" -ForegroundColor Cyan

# Verify Python
try {
    $pyVer = python --version
    Write-Host "[+] $pyVer detected." -ForegroundColor Green
} catch {
    Write-Host "[-] Error: Python is not available in system PATH." -ForegroundColor Red
    Exit 1
}

# Create venv
if (-not (Test-Path -Path "venv")) {
    Write-Host "[+] Generating virtual environment (venv)..." -ForegroundColor Yellow
    python -m venv venv
} else {
    Write-Host "[*] Directory 'venv' already exists." -ForegroundColor Gray
}

# Install dependencies directly via venv python binary
Write-Host "[+] Upgrading pip inside virtual environment..." -ForegroundColor Yellow
& ".\venv\Scripts\python.exe" -m pip install --upgrade pip

Write-Host "[+] Installing requirements..." -ForegroundColor Yellow
& ".\venv\Scripts\pip.exe" install -r requirements.txt

# Verify Tesseract installation
$tessPath = "C:\Program Files\Tesseract-OCR\tesseract.exe"
if (Test-Path $tessPath) {
    Write-Host "[+] Tesseract OCR detected at $tessPath" -ForegroundColor Green
} else {
    Write-Host "[!] Note: Tesseract OCR binary not found at default path." -ForegroundColor DarkYellow
    Write-Host "    Install it if you plan to use image OCR parsing." -ForegroundColor DarkYellow
}

Write-Host "`n[+] Setup complete! Run the tool using .\run.ps1" -ForegroundColor Green
