# SS GitHub engineering benchmark — v0.8.4

SS remains **v0.8.4**. This document records verified engineering patterns from mature AI applications/frameworks; it does not claim feature parity.

## Benchmarks reviewed

- **Jan**: tagged releases and explicit release identity. SS therefore keeps a fixed VERSION and will not bump it merely because code changed.
- **Open WebUI**: durable migrations, backup-before-schema-change discipline, local/desktop operation, scheduled automations and provider flexibility. SS therefore keeps user data outside code releases and makes update paths non-destructive.
- **AnythingLLM**: dynamic model routing, automatic/user memories, intelligent tool selection, MCP, multimodal support, agents, document pipelines, citations, native tool calling and bounded agent loops. SS adopts capability-based routing, persistent memory, tool boundaries and read-only document intelligence.
- **LangGraph**: durable state, resumability and human-in-the-loop execution. SS's orchestration target uses explicit state transitions, approvals and recovery rather than opaque autonomous mutation.
- **LibreChat / @librechat/agents**: multi-provider agents, MCP, skills, subagents, tool execution, graph orchestration and streaming event handling. SS adopts the separation of provider adapters, agent roles, tools and policy.
- **OpenRouter**: Workspaces provide scoped API keys, routing defaults, guardrails and observability; its Models API exposes standardized pricing/context/capability metadata and model filtering. SS therefore treats provider credentials, model metadata, privacy policy and routing as first-class control-plane data.
- **Hugging Face Inference Providers**: `/v1/models` exposes provider-level pricing, context, latency/throughput and `is_free`; model routing can use `:fastest`, `:cheapest` or a selected provider. SS therefore does not guess that a model is free and preserves provider-level metadata.

## SS-specific non-negotiables

1. Existing chats, memory, files and metadata are never deleted by an application update.
2. No automatic provider fallback across a privacy boundary.
3. No cloud generation or spending without explicit approval.
4. File mutation is disabled in the current workspace layer; scan, extraction and duplicate analysis are read-only.
5. Model/provider provenance is deterministic for identity questions; the model is not trusted to self-identify.
6. A version number does not change merely because code changed. A new version requires a substantial, verified capability leap and explicit approval.
7. CI must test the actual integrated runtime, not a retired parallel implementation.
8. Large optional dependencies are not installed merely to expose a feature; heavy capabilities are isolated and loaded only when needed.
9. API credentials are entered in SS Setup Center and stored in the OS credential store, never in GitHub or chat history.
10. Browser-only services (Meta AI, HuggingChat, DuckDuckGo UI, Tor Browser) must be labelled as browser/privacy layers, not falsely represented as API model providers.

## Target architecture

`UI -> permission/policy layer -> task classifier -> capability/model router -> provider adapter -> response verifier -> persistent archive`

File intelligence follows:

`authorized filesystem -> metadata-preserving scanner -> extraction/index -> evidence/citation context -> model`

No destructive filesystem action is part of this path until a future version has a proposal + explicit approval + audit trail + reversible execution mechanism.

## Current 8765/8766 integration rule

`127.0.0.1:8765` is the canonical SS Second Brain entry point. The former `provider-console/` source and 8766 launcher remain in GitHub as recoverable historical/source material, but the integrated runtime now absorbs their useful provider/setup/history functionality. A second independent Brain must not be allowed to diverge from 8765.
