$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot\..
if (-not (Get-Command git -ErrorAction SilentlyContinue)) { throw "Git is not installed or not on PATH." }
git pull --ff-only
if ($LASTEXITCODE -ne 0) { throw "git pull --ff-only failed. Inspect git status before retrying." }
if (Test-Path ".venv\Scripts\python.exe") {
    & .venv\Scripts\python.exe -m pip install -r requirements.txt
}
Write-Host "Update complete."
