# SS — Second Brain v0.9.0

**Single application entry point:** `http://127.0.0.1:8765/`

SS is a local-first intelligent orchestration layer. It chooses a suitable model under privacy, capability, cost and available-compute constraints rather than being locked to one provider.

## 0.9.0 LEAP

- Permanent Second Brain chat archive outside the Git repository; no automatic deletion/pruning.
- Explicit approval before cloud chat turns; no silent provider substitution.
- Resource-aware routing that considers available RAM before preferring a local model.
- FREE and PAID/OTHER model lists, alphabetically sorted by provider UI.
- Local engines: Ollama, LM Studio/Bionic, Jan.
- Cloud/gateway providers: OpenRouter, Hugging Face Inference, Venice, OpenAI, Anthropic, Gemini, xAI, DeepSeek, Mistral, Moonshot/Kimi, Z.ai/GLM, Qwen/Alibaba Model Studio, Perplexity.
- Connector layer: Brave Search API, Higgsfield MCP, DuckDuckGo, Tor, HuggingChat and Meta AI.
- **Integrated read-only File / Legal Workspace:** recursive folder inventory, metadata-preserving document extraction (PDF/DOCX/XLSX/text), multi-source context assembly and evidence-oriented analysis through SS.
- **Duplicate-photo intelligence:** exact SHA-256 duplicate detection, oldest-creation-date canonical proposal and recoverable-space calculation. No deletion, rename, move or overwrite is performed.
- All workspace actions default to read-only. Original paths, timestamps and metadata are retained.

## Use

Run `run-SS.bat`. It pulls the current fast-forward GitHub build, creates/updates `.venv`, installs requirements, and starts **127.0.0.1:8765**. The integrated workspace is at **127.0.0.1:8765/workspace**.

`ss_server.py` wraps the existing application and adds the workspace before Uvicorn starts. FastAPI/Uvicorn supports this normal import-string application pattern. citeturn2search2turn2search7

## Data safety

Application source is versioned in GitHub. User chats are outside the repository under the SS application-data directory. Updates do not reset, prune or overwrite that archive. The workspace is read-only by design.

The old 8766 provider-console prototype had an in-memory chat persistence defect. Do not delete its browser/application data until the recovery procedure in `docs/RECOVER-8766-CHAT.md` has been attempted.

## Important boundary

A provider being listed does not mean its private credential or local server is magically available. SS reports actual endpoint/credential boundaries. It does not invent APIs. Cloud requests remain gated by explicit approval.
