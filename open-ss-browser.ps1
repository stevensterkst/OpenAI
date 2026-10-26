param(
    [string]$Url = "http://127.0.0.1:8765/",
    [int]$Port = 8765,
    [int]$TimeoutSeconds = 60
)
$ErrorActionPreference = "Stop"
$deadline = (Get-Date).AddSeconds($TimeoutSeconds)
$healthUrl = "http://127.0.0.1:$Port/system"
$lastError = "No response received from the health endpoint."

while ((Get-Date) -lt $deadline) {
    try {
        $response = Invoke-RestMethod -Method Get -Uri $healthUrl -TimeoutSec 2
        if ($response.status -eq "online" -and $response.service -eq "SS Second Brain" -and $response.version) {
            Start-Process $Url
            exit 0
        }
        $lastError = "Health endpoint responded, but did not identify a healthy SS Second Brain service."
    } catch {
        $lastError = $_.Exception.Message
    }
    Start-Sleep -Milliseconds 500
}
Write-Error "SS did not become healthy within $TimeoutSeconds seconds. Last result: $lastError"
exit 1
