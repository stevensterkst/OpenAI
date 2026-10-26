param(
    [Parameter(Mandatory=$true)]
    [string]$AdbPath,

    [Parameter(Mandatory=$true)]
    [string]$Model
)

$ErrorActionPreference = 'Stop'
$wanted = ($Model -replace '_',' ' -replace '\s+',' ').Trim().ToLowerInvariant()

function Write-Diagnostic([string]$Message) {
    [Console]::Error.WriteLine("[ADB discovery] " + $Message)
}

# Never store or assume a phone IP address or port. Android chooses the
# wireless-debugging TLS port dynamically; query the live mDNS advertisements.
$endpoints = @()
try {
    $services = @(& $AdbPath mdns services 2>$null)
    foreach ($line in $services) {
        $text = [string]$line
        if ($text -notmatch '_adb-tls-connect\._tcp') { continue }
        $match = [regex]::Match($text, '(?<endpoint>(?:\d{1,3}\.){3}\d{1,3}:\d+)')
        if ($match.Success) { $endpoints += $match.Groups['endpoint'].Value }
    }
    $endpoints = @($endpoints | Sort-Object -Unique)
} catch {
    Write-Diagnostic ("Could not query ADB mDNS services: " + $_.Exception.Message)
}

if ($endpoints.Count -eq 0) {
    Write-Diagnostic "No live _adb-tls-connect._tcp endpoint was discovered. Confirm Wireless debugging is ON and both devices are on the same Wi-Fi/LAN."
} else {
    Write-Diagnostic ("Discovered {0} live wireless endpoint(s); trying current advertisements only." -f $endpoints.Count)
    foreach ($endpoint in $endpoints) {
        # The port is deliberately taken from this run's mDNS result.
        $connectOutput = @(& $AdbPath connect $endpoint 2>&1)
        $connectText = ($connectOutput | ForEach-Object { [string]$_ }) -join ' '
        if ($LASTEXITCODE -eq 0 -and $connectText -match 'connected to|already connected to') {
            Write-Diagnostic ("ADB accepted endpoint " + $endpoint)
        } else {
            Write-Diagnostic ("ADB did not connect to " + $endpoint + ". " + $connectText.Trim())
        }
    }
}

# Give ADB a brief moment to finish TLS authentication and enumerate devices.
Start-Sleep -Milliseconds 700
$matches = @()
try {
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
} catch {
    Write-Diagnostic ("Could not enumerate ADB devices: " + $_.Exception.Message)
}

$selected = $matches | Select-Object -First 1
if ($selected) {
    # Standard output is reserved for the serial only: the .bat caller captures it.
    Write-Output $selected
    exit 0
}

Write-Diagnostic ("No authorized connected device reported model '" + $Model + "'.")
Write-Diagnostic "If mDNS endpoints were found but connect failed, check that this PC is listed under the phone's Wireless debugging > Paired devices. The connect port and pairing port are different; do not use the pairing port with adb connect."
exit 1
