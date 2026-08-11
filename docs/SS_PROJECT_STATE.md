# SS project state — authoritative integration notes

## Purpose
SS is intended to be a local-first intelligent orchestration layer, not merely a chat frontend. The target is: choose the strongest suitable model for the task subject to dynamically selected privacy, compute, capability and cost policy.

## Decisions recovered from the supplied SS development material

- Do not optimize for a single "smart uncensored AI". Optimize for the best model for the actual task under privacy/censorship/compute policy.
- Preferred architecture: SS intelligent router → local engines (Ollama / LM Studio / Jan), ZDR cloud gateway (especially OpenRouter), direct frontier/reasoning providers when justified, and web/search tools as a separate layer.
- Sensitive/private documents should prefer local inference. If local compute is insufficient, SS must explain the privacy boundary before crossing it.
- OpenRouter is a routing layer, not a model. SS can request ZDR and deny data collection; provider/model compatibility still has to be checked at request time.
- LM Studio is an important local option because its OpenAI-compatible server runs on localhost and its current APIs support model management and MCP/tool use.
- Jan is a privacy-first local frontend/backend with an OpenAI-compatible local API. The normal server endpoint is 127.0.0.1:1337/v1; Jan also has a newer CLI/server path and can connect to custom remote endpoints.
- Ollama remains a model-serving engine, not the SS intelligence layer.
- Venice remains a valid privacy/low-guardrail provider, but SS should not be architecturally locked to Venice.
- Cloud requests must never be silently charged or silently substituted. The application now requires explicit cloud approval for each cloud chat turn.
- API keys must not be committed to GitHub. SS uses the OS credential store through `keyring` where available.
- Chats must never be automatically cleaned, deleted, pruned, rotated or overwritten by an application update. User data is outside the repository.
- 127.0.0.1:8765 is the single SS application entry point. 8766 was a separate provider-console prototype and must not remain a competing Second Brain entry point.

## Provider layer in v0.8.4

### Direct model providers
Ollama, LM Studio/Bionic, Jan, OpenRouter, Hugging Face Inference Providers, Venice, OpenAI, Anthropic, Google Gemini, xAI/Grok, DeepSeek, Mistral, Moonshot/Kimi, Z.ai/GLM, Qwen/Alibaba Model Studio, Perplexity.

### Tool/privacy connectors
Brave Search API; Higgsfield MCP; DuckDuckGo browser search; Tor transport/browser; HuggingChat web UI; Meta AI web UI.

SS deliberately does not fabricate APIs. Services without a verified public consumer API are exposed as browser/MCP connectors with their actual status.

## Hardware/RAM policy

The user's Windows laptop has limited RAM and an AMD integrated GPU. SS therefore needs resource-aware routing and model loading/unloading. It should prefer the smallest model that can satisfy the task and refuse a model load when available memory cannot safely support it, rather than repeatedly crashing Ollama/llama.cpp.

## Permanent data architecture

Application code is replaceable. User data is not.

```text
SS/data/
  chats/       permanent conversation archives
  memory/      explicitly saved long-term memory/context
  backups/     migration/recovery copies
```

Optional cloud mirroring is controlled by `SS_CHAT_CLOUD_ROOT`. The application has no automatic deletion endpoint.

## 8766 recovery finding

The supplied `SS-MultiProvider-Console-v1.2-WORKING-8766.zip` was inspected. Its README explicitly said that it was a standalone provider console and that API keys were kept in browser localStorage. More importantly, its `public/app.js` kept chat messages only in an in-memory JavaScript object (`state.chats`) and did not persist those chats to disk/server storage. Therefore a browser reload/restart could lose those chat messages. This is an implementation defect, not an acceptable SS data policy.

The v0.8.4 architecture fixes this class of failure by saving every chat to the external SS data archive after each successful assistant response.

If an old 8766 browser tab containing the lost chat state is still open, its messages may be exportable from that live page. If the tab was reloaded/closed and the in-memory state was destroyed, the old v1.2 package alone does not contain those messages; SS must not claim recovery unless the actual data is found in the browser profile, a backup, or an exported conversation.

## Supplied development material

This state file was derived from the user-supplied historic SS development captures and the standalone 8766 package supplied in the conversation. The full source captures remain in the ChatGPT conversation files; this document is the compact, persistent project-state record that future development chats can use.
