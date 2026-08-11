@echo off
setlocal
title SS Provider Setup - one button
echo SS Provider Setup
echo.
echo Opening official credential/setup pages...
start "" "https://openrouter.ai/keys"
start "" "https://huggingface.co/settings/tokens"
start "" "https://venice.ai/settings/api"
start "" "https://platform.openai.com/api-keys"
start "" "https://console.anthropic.com/settings/keys"
start "" "https://aistudio.google.com/app/apikey"
start "" "https://console.x.ai/"
start "" "https://platform.deepseek.com/api_keys"
start "" "https://console.mistral.ai/api-keys/"
start "" "https://platform.moonshot.ai/console/api-keys"
start "" "https://z.ai/manage-apikey/apikey-list"
start "" "https://bailian.console.alibabacloud.com/?tab=model#/api-key"
start "" "https://www.perplexity.ai/settings/api"
start "" "https://brave.com/search/api/"
echo.
echo Jan: Settings ^> Local API Server ^> Start Server, then 127.0.0.1:1337
start "" "https://www.jan.ai/docs/desktop/api-server"
echo LM Studio:
start "" "https://lmstudio.ai/"
echo.
echo After creating keys, enter them once in SS Console. SS stores them in the OS credential store.
echo This script never collects, transmits, or writes API keys.
pause
