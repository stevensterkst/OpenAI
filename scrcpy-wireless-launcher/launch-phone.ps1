param(
    [Parameter(Mandatory=$true)]
    [string]$AdbPath,

    [Parameter(Mandatory=$true)]
    [string]$ScrcpyPath,

    [Parameter(Mandatory=$true)]
    [string]$Serial,

    [Parameter(Mandatory=$true)]
    [string]$Title
)

$ErrorActionPreference = 'Stop'

$model = (& $AdbPath -s $Serial shell getprop ro.product.model 2>$null | Select-Object -First 1).Trim()
if (-not $model) {
    Write-Host "[ERROR] Could not verify device model for $Serial"
    exit 2
}

Write-Host "    Serial: $Serial"
Write-Host "    ADB model: $model"
Write-Host "    Expected window: $Title"

$args = @(
    '-s',
    $Serial,
    ('--window-title="' + $Title + '"')
)

try {
    $p = Start-Process -FilePath $ScrcpyPath -ArgumentList $args -PassThru
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
