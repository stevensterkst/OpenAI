# SS Second Brain v0.8.1
Real Windows runtime. Lovable is not required.
Implements SmartOrchestrator, 8 agent contracts/execution paths, provider registry,
resource-aware model selection, persistent memory, read-only drive discovery/inventory,
verification, approval gates and explicit boundary/recovery explanations.

Install: double-click INSTALL_SS_V081.cmd
Run: double-click START_SS_V081.cmd
Open: http://127.0.0.1:8765/

Ollama local is used when a model fits the conservative RAM budget.
OpenRouter is available only when OPENROUTER_API_KEY is explicitly configured.
GPU shared memory is never counted as extra RAM; acceleration is reported only when verified.
No destructive filesystem operation is exposed in this release.
