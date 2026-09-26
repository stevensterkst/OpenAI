# Safe resource profile for Ollama on Windows.
# No models are installed/deleted. Restart Ollama after setting variables.
[Environment]::SetEnvironmentVariable("OLLAMA_MAX_LOADED_MODELS","1","User")
[Environment]::SetEnvironmentVariable("OLLAMA_NUM_PARALLEL","1","User")
[Environment]::SetEnvironmentVariable("OLLAMA_KEEP_ALIVE","5m","User")
[Environment]::SetEnvironmentVariable("OLLAMA_FLASH_ATTENTION","1","User")
[Environment]::SetEnvironmentVariable("OLLAMA_KV_CACHE_TYPE","q8_0","User")
Write-Host "Ollama safe profile saved for the current Windows user." -ForegroundColor Green
Write-Host "Quit Ollama completely from the taskbar, then start it again." -ForegroundColor Yellow
Write-Host "After restart run: ollama ps" -ForegroundColor Cyan
Write-Host "GPU-only operation must be verified with ollama ps." -ForegroundColor Yellow