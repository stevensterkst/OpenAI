param(
    [string]$Url = "http://127.0.0.1:8765/",
    [int]$Port = 8765,
    [int]$TimeoutSeconds = 60
)
$ErrorActionPreference = "SilentlyContinue"
$deadline = (Get-Date).AddSeconds($TimeoutSeconds)
$healthUrl = "http://127.0.0.1:$Port/system"
while ((Get-Date) -lt $deadline) {
    try {
        $response = Invoke-WebRequest -UseBasicParsing -Uri $healthUrl -TimeoutSec 2
        if ($response.StatusCode -ge 200 -and $response.StatusCode -lt 500) {
            Start-Process $Url
            exit 0
        }
    } catch {}
    Start-Sleep -Milliseconds 500
}
Write-Error "SS Brain did not become ready within $TimeoutSeconds seconds. Server console/logs contain the startup error."
exit 1
