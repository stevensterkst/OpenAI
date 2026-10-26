param(
    [Parameter(Mandatory=$true)]
    [string]$AdbPath,

    [Parameter(Mandatory=$true)]
    [string]$Model
)

$ErrorActionPreference = 'Stop'

$wanted = ($Model -replace '_',' ' -replace '\s+',' ').Trim().ToLowerInvariant()

# Wireless debugging advertises connect endpoints via mDNS, but "adb devices"
# does not list those phones until ADB connects to the advertised endpoint.
# Connect only services explicitly advertised as _adb-tls-connect._tcp.
try {
    $services = & $AdbPath mdns services 2>$null
    foreach ($line in $services) {
        if ($line -notmatch '_adb-tls-connect\._tcp') { continue }
        $endpoint = [regex]::Match($line, '(?<endpoint>(?:\d{1,3}\.){3}\d{1,3}:\d+)')
        if (-not $endpoint.Success) { continue }
        $address = $endpoint.Groups['endpoint'].Value
        # Ignore stale/offline advertisements; model verification below is authoritative.
        & $AdbPath connect $address 2>$null | Out-Null
    }
} catch {
    # Continue to check already-connected USB/Wi-Fi devices if mDNS is unavailable.
}

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

$selected = $matches | Select-Object -First 1

if ($selected) {
    Write-Output $selected
    exit 0
}

exit 1
