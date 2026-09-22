param(
    [string]$Source
)

$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot

$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) {
    throw 'Python was not found on PATH.'
}

$app = Join-Path $PSScriptRoot 'app.py'
if (-not (Test-Path -LiteralPath $app -PathType Leaf)) {
    throw 'Transcribe-Translate app.py is missing.'
}

Write-Host 'SS Transcribe-Translate - 100% local runtime' -ForegroundColor Cyan
Write-Host 'faster-whisper + CTranslate2 -> Ollama; no OpenAI API calls.'
Write-Host ''

if ($Source) {
    if (-not (Test-Path -LiteralPath $Source -PathType Leaf)) {
        throw ('Source media does not exist: ' + $Source)
    }
    Write-Host ('Source supplied: ' + $Source)
    $env:SS_TRANSCRIBE_SOURCE = (Resolve-Path -LiteralPath $Source).Path
}

& $python.Source $app
$exitCode = $LASTEXITCODE
if ($exitCode -ne 0) {
    throw ('Transcribe-Translate exited with code ' + $exitCode + '.')
}
