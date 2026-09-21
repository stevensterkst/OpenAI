param(
    [Parameter(Mandatory=$true)]
    [string]$AdbPath,

    [Parameter(Mandatory=$true)]
    [string]$Model
)

$ErrorActionPreference = 'SilentlyContinue'

# ADB devices -l already reports the Android model. Use that directly;
# do not make an extra shell/getprop call just to identify the phone.
# Motorola reports e.g. model:moto_g85_5G while the friendly model is
# "moto g85 5G". Normalize underscores/spaces for comparison.

$wanted = ($Model -replace '_',' ' -replace '\s+',' ').Trim().ToLowerInvariant()
$matches = @()

$lines = & $AdbPath devices -l 2>$null

foreach ($line in $lines) {
    if ($line -match '^(S+)\s+device\s+.*?\smodel:(\S+)') {
        $serial = $Matches[1]
        $reported = ($Matches[2] -replace '_',' ' -replace '\s+',' ').Trim().ToLowerInvariant()

        if ($reported -eq $wanted) {
            $matches += $serial
        }
    }
}

# Prefer the stable ADB TLS/mDNS serial when both mDNS and raw IP:port
# transports for the same phone are present.
$selected = $matches |
    Sort-Object @{Expression={if ($_ -like '*._adb-tls-connect._tcp') {0} else {1}}} |
    Select-Object -First 1

if ($selected) {
    Write-Output $selected
    exit 0
}

exit 1
