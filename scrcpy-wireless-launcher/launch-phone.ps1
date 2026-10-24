param(
    [Parameter(Mandatory=$true)]
    [string]$AdbPath,

    [Parameter(Mandatory=$true)]
    [string]$ScrcpyPath,

    [Parameter(Mandatory=$true)]
    [string]$Serial,

    [Parameter(Mandatory=$true)]
    [string]$Title,

    [Parameter(Mandatory=$false)]
    [string]$ExpectedModel = ""
)

$ErrorActionPreference = 'Stop'

$model = (& $AdbPath -s $Serial shell getprop ro.product.model 2>$null | Select-Object -First 1).Trim()
if (-not $model) {
    Write-Host "[ERROR] Could not verify device model for $Serial"
    exit 2
}
if ($ExpectedModel) {
    $normalize = { param($value) (($value -replace '_',' ' -replace '\s+',' ').Trim().ToLowerInvariant()) }
    if ((& $normalize $model) -ne (& $normalize $ExpectedModel)) {
        Write-Host "[ERROR] Model mismatch: serial $Serial reports '$model', expected '$ExpectedModel'. Refusing to open the wrong phone."
        exit 5
    }
}

Write-Host "    Serial: $Serial"
Write-Host "    ADB model: $model"
Write-Host "    Expected window: $Title"

$scrcpyArgs = @(
    '-s',
    $Serial,
    ('--window-title="' + $Title + '"')
)

try {
    $p = Start-Process -FilePath $ScrcpyPath -ArgumentList $scrcpyArgs -PassThru
    Start-Sleep -Milliseconds 700

    if ($p.HasExited) {
        Write-Host "[ERROR] scrcpy exited immediately (PID $($p.Id), exit code $($p.ExitCode))."
        exit 3
    }

    Write-Host "    scrcpy started, PID $($p.Id)"
    exit 0
}
catch {
    Write-Host "[ERROR] Failed to start scrcpy: $($_.Exception.Message)"
    exit 4
}
