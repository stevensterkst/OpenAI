# SS — Second Brain v0.8.3

A local-first AI orchestrator with one integrated multi-provider console.

## Current architecture

- **Single user entry point:** `http://127.0.0.1:8765/`
- Integrated console: `/console` (also `/providers`)
- Local backends: Ollama, Jan, LM Studio/Bionic
- Cloud/gateway backends: OpenRouter, Hugging Face Inference Providers, Venice, OpenAI, Anthropic/Claude, Google Gemini, xAI/Grok, DeepSeek, Mistral, Moonshot/Kimi, Z.ai/GLM, Qwen/Alibaba Model Studio, Perplexity
- Search layer: Brave Search adapter
- Resource telemetry: RAM/CPU/swap exposed to SS routing
- Credential storage: Windows/OS credential store through `keyring`; secrets are not committed to GitHub
- Permanent chat archive outside the repository; optional cloud mirror via `SS_CHAT_CLOUD_ROOT`
- **Deletion policy: NEVER automatically delete chats or generated conversation archives.**
- No Docker or WSL required.

## Windows

Run `run-SS.bat`. It creates/uses `.venv`, installs the pinned application dependencies, opens `http://127.0.0.1:8765/`, and starts FastAPI.

## Provider setup

Open **SS AI Console → select provider → enter key → Save key securely & test**. Cloud credentials are stored in the OS credential store when available. The console includes official setup links for the supported services.

For local providers, SS only connects to an API that is actually running; it does not silently install or download large models. Model loading/unloading and RAM-aware selection are part of the resource-aware provider layer.

## Data safety

Application source is versioned in GitHub; user chats are not. Conversation archives live outside the repository under the SS application-data directory and can optionally be mirrored to a synchronized cloud folder. Code updates must not overwrite those directories.

## Important limitation

A GitHub commit updates the source repository, not an already-running Windows process. After pulling the current branch, restart `run-SS.bat` so the local `127.0.0.1:8765` server uses the new version.
