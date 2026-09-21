param(
    [Parameter(Mandatory=$true)]
    [string]$AdbPath,

    [Parameter(Mandatory=$true)]
    [string]$Model
)

$ErrorActionPreference = 'SilentlyContinue'

$lines = & $AdbPath devices -l 2>$null
$candidates = @()

foreach ($line in $lines) {
    if ($line -match '^(S+)s+devices') {
        $candidates += $Matches[1]
    }
}

# Prefer the stable ADB TLS/mDNS transport over a raw IP:port transport.
$ranked = $candidates | Sort-Object @{
    Expression = { if ($_ -like '*._adb-tls-connect._tcp') { 0 } else { 1 } }
}, @{
    Expression = { if ($_ -like '*:*') { 1 } else { 0 } }
}

foreach ($serial in $ranked) {
    $reportedModel = (& $AdbPath -s $serial shell getprop ro.product.model 2>$null | Out-String).Trim()
    if ($reportedModel -eq $Model) {
        Write-Output $serial
        exit 0
    }
}

exit 1
