param(
    [Parameter(Mandatory=$true)]
    [string]$AdbPath,

    [Parameter(Mandatory=$true)]
    [string]$Model
)

$ErrorActionPreference = 'Stop'

$wanted = ($Model -replace '_',' ' -replace '\s+',' ').Trim().ToLowerInvariant()
$matches = @()

$lines = & $AdbPath devices -l 2>$null

foreach ($line in $lines) {
    $parts = ($line -split '\s+') | Where-Object { $_ -ne '' }

    if ($parts.Count -lt 2) { continue }
    if ($parts[1] -ne 'device') { continue }

    $serial = $parts[0]
    $modelToken = $parts | Where-Object { $_ -like 'model:*' } | Select-Object -First 1

    if (-not $modelToken) { continue }

    $reported = ($modelToken.Substring(6) -replace '_',' ' -replace '\s+',' ').Trim().ToLowerInvariant()

    if ($reported -eq $wanted) {
        $matches += $serial
    }
}

$selected = $matches |
    Sort-Object @{Expression={if ($_ -like '*._adb-tls-connect._tcp') {0} else {1}}} |
    Select-Object -First 1

if ($selected) {
    Write-Output $selected
    exit 0
}

exit 1
