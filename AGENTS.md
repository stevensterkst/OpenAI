# AGENTS.md - SS-Brain-Base (v0.8.4) — AI Coordination Hand-off

## 1. Project Identity & Architecture
*   **Project Name:** SS-Brain-Base — Local-first intelligent orchestration layer
*   **Core Objective:** Route to the strongest suitable model for each task under privacy/censorship/compute/cost policy. Single entry point at 127.0.0.1:8765.
*   **Tech Stack:** Python 3, FastAPI, Ollama/LM Studio/Jan (local), OpenRouter/Cloud (gateway), keyring (OS credential store), SQLite (data archive)
*   **Key Directories:**
    *   `/app.py` — Main FastAPI application (single entry point)
    *   `/ss_core.py` — Stable runtime: providers, connectors, data archive, read-only policy
    *   `/ss_brain_084.py` — Brain logic: model selection, resource-aware routing
    *   `/ss_server.py` — Server startup & lifecycle
    *   `/ss_entry.py` — Entry point & CLI
    *   `/ss_hardening.py` — Security hardening: credential isolation, audit logging
    *   `/ss_policy.py` — Policy engine: privacy, cost, compute, censorship rules
    *   `/agent_bridge.py` — Multi-agent bridge: coordinates OpenAI, DeepSeek, Claude
    *   `/anythingllm_adapter.py` — AnythingLLM integration adapter
    *   `/workspace_min.py` — Minimal workspace router
    *   `/provider-console/` — Legacy 8766 companion UI (integrated, not competing)
    *   `/web/` — Static HTML/JS frontend
    *   `/docs/` — Architecture, data safety, project state
    *   `/tests/` — Regression tests

## 2. Shared Development Workflow (The Multi-AI Rule)
This project utilizes a dual-engine AI strategy (OpenAI & DeepSeek). To maintain sync:
1. **GitHub is the absolute Source of Truth.** Never trust a previous chat window's assumption over the actual state of the code on GitHub.
2. Before writing code, you must read the latest commit changes or request a file export.
3. **OpenAI Focus:** Architectural design, system prompt engineering, feature planning, and structured layouts.
4. **DeepSeek Focus:** Math, performance optimization, heavy logical debugging, and deep algorithmic thinking.

## 3. Current Sprint & State of Play
*   **Active Branch:** `main`
*   **Last Successfully Merged Feature:** Integration modules cherry-picked from SS-Brain-Evolved (agent_bridge, anythingllm_adapter, ss_entry, ss_hardening, ss_policy)
*   **Current Bottleneck / Active Task:** None — all integration modules present
*   **Immediate Next Action Item:** Verify app.py runs correctly; enable branch protection on GitHub

## 4. Code Style & Technical Constraints
*   **Formatting:** PEP 8, 4-space indent, snake_case functions, UPPER_CASE constants
*   **Testing Protocol:** Run `python -m pytest tests/` before declaring code "complete". All business logic must have unit tests.
*   **Explicit Boundaries:** Do not alter configuration files without explicit permission.
*   **Security:** No API keys committed to GitHub. Keys stored in OS credential store (keyring) or environment variables.
*   **Data Policy:** Chats never auto-deleted, pruned, rotated, or overwritten by an application update. User data is outside the repository.

## 5. Provider Layer (v0.8.4)

### Direct model providers
Ollama, LM Studio/Bionic, Jan, OpenRouter, Hugging Face Inference Providers, Venice, OpenAI, Anthropic, Google Gemini, xAI/Grok, DeepSeek, Mistral, Moonshot/Kimi, Z.ai/GLM, Qwen/Alibaba Model Studio, Perplexity.

### Tool/privacy connectors
Brave Search API; Higgsfield MCP; DuckDuckGo browser search; Tor transport/browser; HuggingChat web UI; Meta AI web UI.

SS deliberately does not fabricate APIs. Services without a verified public consumer API are exposed as browser/MCP connectors with their actual status.

## 6. Hardware/RAM policy
The user's Windows laptop has limited RAM and an AMD integrated GPU. SS therefore needs resource-aware routing and model loading/unloading. It should prefer the smallest model that can satisfy the task and refuse a model load when available memory cannot safely support it, rather than repeatedly crashing Ollama/llama.cpp.

## 7. Permanent data architecture
Application code is replaceable. User data is not.

```text
SS/data/
  chats/       permanent conversation archives
  memory/      explicitly saved long-term memory/context
  backups/     migration/recovery copies
```

Optional cloud mirroring is controlled by `SS_CHAT_CLOUD_ROOT`. The application has no automatic deletion endpoint.

## 8. Integration modules (cherry-picked from Evolved)
- `agent_bridge.py` — Multi-agent bridge: coordinates OpenAI, DeepSeek, Claude
- `anythingllm_adapter.py` — AnythingLLM integration adapter
- `ss_entry.py` — Entry point & CLI
- `ss_hardening.py` — Security hardening: credential isolation, audit logging
- `ss_policy.py` — Policy engine: privacy, cost, compute, censorship rules
- `workspace_min.py` — Minimal workspace router
- `app_integrated.py` — Integrated runtime (single 8765 app)