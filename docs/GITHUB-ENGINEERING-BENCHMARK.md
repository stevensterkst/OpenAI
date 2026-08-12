# SS GitHub engineering benchmark

SS remains **v0.8.4**. This document records engineering patterns adopted from mature AI applications/frameworks rather than copying their code.

## Benchmarks reviewed

- **Jan**: tagged releases, release assets/checksums, model/context management, validation and CI. SS therefore keeps an explicit version file, release policy and regression gates.
- **Open WebUI**: durable migrations, backups, provider flexibility, file/message robustness and warnings around schema changes. SS therefore treats user data as external to application code and keeps updates non-destructive.
- **AnythingLLM**: workspaces, persistent memories, agents/skills, filesystem access, citations, provider/model switching and model-aware context. SS therefore separates workspace context from the core chat route and keeps file intelligence read-only until permission exists.
- **LangGraph**: durable state, resumability and human-in-the-loop execution. SS's next orchestration layer is designed around explicit state transitions and approval gates rather than opaque autonomous mutation.
- **Agno**: memory, context providers, human approval, tracing/auditability and production APIs. SS adopts these as architectural targets for the next major capability leap.
- **LibreChat**: agent skills, subagents, MCP hardening, explicit memory controls and provider/model configuration. SS adopts the same separation of capabilities, permissions and model routing.

## SS-specific non-negotiables

1. Existing chats, memory, files and metadata are never deleted by an application update.
2. No automatic provider fallback across a privacy boundary.
3. No cloud generation or spending without explicit approval.
4. File mutation is disabled in the current workspace layer; scan, extraction and duplicate analysis are read-only.
5. Model/provider provenance is deterministic for identity questions; the model is not trusted to self-identify.
6. A version number does not change merely because code changed. A new version requires a substantial, verified capability leap and explicit approval.
7. CI must test the actual integrated runtime, not a retired parallel implementation.
8. Large optional dependencies are not installed merely to expose a feature; heavy capabilities are isolated and loaded only when needed.

## Target architecture

`UI -> permission/policy layer -> task classifier -> capability/model router -> provider adapter -> response verifier -> persistent archive`

File intelligence follows:

`filesystem -> metadata-preserving scanner -> extraction/index -> evidence/citation context -> model`

No destructive filesystem action is part of this path until a future version has a proposal + explicit approval + audit trail + reversible execution mechanism.
