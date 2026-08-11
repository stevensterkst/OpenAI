# SS — Second Brain v0.8.4

**Single application entry point:** `http://127.0.0.1:8765/`

SS is a local-first intelligent orchestration layer. It selects among local models, privacy-oriented gateways and frontier/reasoning providers according to task capability, privacy and available compute. It is not locked to Ollama or Venice.

## What is live in v0.8.4

- Real Second Brain chat UI at `/`.
- Provider console at `/console` and `/providers`.
- Permanent external chat archive with chat list and reload.
- No automatic chat deletion/pruning/cleanup.
- Optional cloud mirror via `SS_CHAT_CLOUD_ROOT`.
- OS credential-store integration through `keyring`; keys are not committed to GitHub.
- Explicit per-request approval before a cloud chat can be sent.
- OpenRouter ZDR + `data_collection: deny` request mode.
- Resource telemetry: RAM, CPU and swap.
- Routing policy scaffolding for privacy, research, coding and complex reasoning.
- Local backends: Ollama, LM Studio/Bionic, Jan.
- Cloud/gateway backends: OpenRouter, Hugging Face Inference, Venice, OpenAI, Anthropic, Gemini, xAI, DeepSeek, Mistral, Moonshot/Kimi, Z.ai/GLM, Qwen/Alibaba Model Studio, Perplexity.
- Separate connector layer: Brave Search API, Higgsfield MCP, DuckDuckGo browser search, Tor transport/browser, HuggingChat web UI and Meta AI web UI.

## Important distinction

A provider being listed does not mean that its private credential or local server is magically available. SS performs real endpoint/model discovery and reports the actual boundary. It does not invent APIs. For services that currently expose browser/MCP access rather than a normal public API, SS presents the real connector instead.

## Windows

Run `run-SS.bat`. It creates/uses `.venv`, installs the requirements and opens **127.0.0.1:8765**. A GitHub update changes source code only; the already-running Windows process must be restarted after pulling the repository.

## Data safety

Application source is versioned in GitHub. User chats are not stored in the repository. They live under the SS application-data directory outside the code. This separation is deliberate: updating or replacing application code must not overwrite conversation archives.

The previous 8766 provider-console prototype was inspected and found to keep chat messages only in JavaScript memory. That was a real persistence defect. v0.8.4 fixes the architecture by persisting successful chats outside the repository.

**Do not delete or clear the old 8766 application/browser data until the recovery procedure in `docs/RECOVER-8766-CHAT.md` has been attempted.**

## Development state

`docs/SS_PROJECT_STATE.md` is the compact persistent specification recovered from the supplied Second Brain development material. Future SS development should update that state rather than relying on one ChatGPT conversation to remember another conversation.
