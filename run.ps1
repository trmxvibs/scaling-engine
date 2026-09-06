# Insta OSINT Engine - PowerShell Runner
param (
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$ScriptArgs
)

if (-not (Test-Path ".\venv\Scripts\python.exe")) {
    Write-Host "[-] Virtual environment not found. Please run .\setup.ps1 first!" -ForegroundColor Red
    Exit 1
}

# Pass-through mode agar terminal se flags diye gaye hain
if ($ScriptArgs.Count -gt 0) {
    & ".\venv\Scripts\python.exe" insta_osint.py @ScriptArgs
    Exit 0
}

# Interactive CLI prompt
Write-Host "======================================================" -ForegroundColor Cyan
Write-Host "              Insta OSINT Engine v2.0" -ForegroundColor Cyan
Write-Host "======================================================" -ForegroundColor Cyan

$target = Read-Host "Enter target Instagram handle"
if ([string]::IsNullOrWhiteSpace($target)) {
    Write-Host "[-] Target cannot be empty." -ForegroundColor Red
    Exit 1
}

Write-Host "`nSelect scan mode:"
Write-Host "  [1] Quick Profile Scan"
Write-Host "  [2] Deep Scan (Download + OCR + JSON + CSV)"
$choice = Read-Host "Choose option [1/2] (Default: 1)"

if ($choice -eq "2") {
    & ".\venv\Scripts\python.exe" insta_osint.py $target --download --ocr --json --csv
} else {
    & ".\venv\Scripts\python.exe" insta_osint.py $target
}
