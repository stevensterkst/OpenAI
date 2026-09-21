$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")

function Require-Command([string]$Name, [string]$Message) {
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw $Message
    }
}

Require-Command "python" "Python 3.10-3.13 is required. Install Python from python.org and ensure 'python' works in a new terminal."

$py = (Get-Command python).Source
$versionText = & $py --version
Write-Host "Python: $versionText"

if (-not (Test-Path ".venv\Scripts\python.exe")) {
    Write-Host "Creating virtual environment..."
    & $py -m venv .venv
    if ($LASTEXITCODE -ne 0) { throw "Python virtual-environment creation failed." }
}

$venvPython = Join-Path (Get-Location) ".venv\Scripts\python.exe"
& $venvPython -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) { throw "pip upgrade failed." }

Write-Host "Installing Python dependencies..."
& $venvPython -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) { throw "Python dependency installation failed." }

if (-not (Get-Command ffmpeg -ErrorAction SilentlyContinue)) {
    Write-Warning "FFmpeg is not currently on PATH."
    Write-Warning "The Python application has been installed, but media processing cannot start until FFmpeg is installed."
    Write-Host ""
    Write-Host "Recommended: install FFmpeg with winget:"
    Write-Host "  winget install --id Gyan.FFmpeg.Shared -e"
    Write-Host "Then CLOSE this terminal, open a NEW terminal, and run setup.bat again."
} else {
    Write-Host "FFmpeg: found"
}

if (-not (Test-Path "config.json")) {
    Copy-Item "config.example.json" "config.json"
    Write-Host "Created config.json"
}

if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "Created .env"
}

Write-Host ""
Write-Host "SETUP COMPLETE"
Write-Host "Run run.bat to start the application."
