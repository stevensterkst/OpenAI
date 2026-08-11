@echo off
setlocal
title SS - Official Provider API Setup

echo.
echo Opening official provider/API credential pages...
echo.
echo SECURITY: never put an API key into this BAT, GitHub, or ChatGPT.
echo If a key has been exposed, revoke/rotate it immediately.
echo.

start "" "https://platform.openai.com/api-keys"
start "" "https://platform.claude.com/settings/keys"
start "" "https://aistudio.google.com/apikey"
start "" "https://console.x.ai/home"
start "" "https://platform.deepseek.com/api_keys"
start "" "https://console.mistral.ai/api-keys"
start "" "https://platform.kimi.ai/console/api-keys"
start "" "https://open.bigmodel.cn/usercenter/apikeys"
start "" "https://bailian.console.aliyun.com/?tab=model"
start "" "https://www.perplexity.ai/account/details"
start "" "https://venice.ai/settings/api"
start "" "https://openrouter.ai/settings/keys"
start "" "https://huggingface.co/settings/tokens"
start "" "https://api.search.brave.com/app/keys"

echo.
echo Opened official pages for:
echo OpenAI, Claude, Gemini, Grok, DeepSeek, Mistral, Kimi,
echo Z.ai, Qwen, Perplexity, Venice, OpenRouter, Hugging Face,
echo and Brave Search.
echo.
echo After obtaining/locating a credential:
echo   8765 -^> Setup Center -^> paste -^> Save securely -^> Test
echo.
echo Local engines need no cloud API key:
echo   Ollama / Jan / LM Studio
echo.
pause
endlocal
