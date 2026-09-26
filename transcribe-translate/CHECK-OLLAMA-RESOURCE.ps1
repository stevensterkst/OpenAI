Write-Host "=== OLLAMA RESOURCE CHECK ===" -ForegroundColor Cyan
$ollama = Get-Command ollama -ErrorAction SilentlyContinue
if(-not $ollama){ throw "ollama.exe not found on PATH." }
Write-Host ""
Write-Host "Configured user variables:"
foreach($n in "OLLAMA_MAX_LOADED_MODELS","OLLAMA_NUM_PARALLEL","OLLAMA_KEEP_ALIVE","OLLAMA_FLASH_ATTENTION","OLLAMA_KV_CACHE_TYPE"){
  Write-Host ("{0}={1}" -f $n,[Environment]::GetEnvironmentVariable($n,"User"))
}
Write-Host ""
Write-Host "Currently loaded models:"
& $ollama.Source ps
Write-Host ""
Write-Host "GPU adapters:"
Get-CimInstance Win32_VideoController | Select-Object Name,AdapterRAM,DriverVersion | Format-Table -AutoSize
Write-Host "Interpretation: ollama ps is authoritative for CPU/GPU model placement."Write-Host ""
Write-Host "llama-server.exe processes (if any):"
Get-CimInstance Win32_Process -Filter "Name = 'llama-server.exe'" | Select-Object ProcessId,ExecutablePath,CommandLine | Format-List
