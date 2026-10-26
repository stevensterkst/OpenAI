param(
    [Parameter(Mandatory=$true)]
    [string]$AdbPath,

    [Parameter(Mandatory=$true)]
    [string]$Model
)

$ErrorActionPreference = 'Stop'
$wanted = ($Model -replace '_',' ' -replace '\s+',' ').Trim().ToLowerInvariant()

# Never hard-code IP addresses or ports. ADB mDNS advertises the current
# TLS connection endpoint; the endpoint may change whenever Wireless Debugging
# restarts or the phone reconnects to Wi-Fi.
$endpoints = @()
try {
    $services = @(& $AdbPath mdns services 2>$null)
    foreach ($line in $services) {
        $text = [string]$line
        if ($text -notmatch '_adb-tls-connect\._tcp') { continue }
        $match = [regex]::Match($text, '(?<endpoint>(?:\d{1,3}\.){3}\d{1,3}:\d+)')
        if ($match.Success) { $endpoints += $match.Groups['endpoint'].Value }
    }
} catch {
    [Console]::Error.WriteLine("WARN: Could not query ADB mDNS services: $($_.Exception.Message)")
}
$endpoints = @($endpoints | Sort-Object -Unique)

foreach ($endpoint in $endpoints) {
    # Keep connection output out of stdout: the .bat caller captures stdout
    # and expects exactly one device serial from this script.
    $connectOutput = @(& $AdbPath connect $endpoint 2>&1)
    $connectText = ($connectOutput | ForEach-Object { [string]$_ }) -join ' '
    if ($connectText -match 'failed to connect|cannot connect|unable to connect|error:') {
        [Console]::Error.WriteLine("WARN: ADB could not connect to discovered endpoint $endpoint. $connectText")
    }
}

# Read the connected-device list after attempting every currently advertised
# endpoint. Select by model, never by IP, port, or mDNS GUID.
$matches = @()
$lines = @(& $AdbPath devices -l 2>$null)
foreach ($line in $lines) {
    $parts = ([string]$line -split '\s+') | Where-Object { $_ -ne '' }
    if ($parts.Count -lt 2 -or $parts[1] -ne 'device') { continue }

    $serial = $parts[0]
    $modelToken = $parts | Where-Object { $_ -like 'model:*' } | Select-Object -First 1
    if (-not $modelToken) { continue }

    $reported = ($modelToken.Substring(6) -replace '_',' ' -replace '\s+',' ').Trim().ToLowerInvariant()
    if ($reported -eq $wanted) { $matches += $serial }
}

$selected = $matches | Select-Object -First 1
if ($selected) {
    Write-Output $selected
    exit 0
}

if ($endpoints.Count -eq 0) {
    [Console]::Error.WriteLine("NOT FOUND: No current _adb-tls-connect._tcp mDNS endpoints were advertised. On the phone, enable Wireless debugging and keep it on the same Wi-Fi network.")
} else {
    [Console]::Error.WriteLine("NOT FOUND: ADB did not report an authorized connected device matching '$Model'. If the phone's Wireless debugging screen lists this PC under Paired devices, toggle Wireless debugging off/on and rerun. If it is not paired, pair once using the phone's separate pairing port and code; do not use the connection port as the pairing port.")
}
exit 1
