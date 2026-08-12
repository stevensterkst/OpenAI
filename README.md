# SS — Second Brain v0.8.4

**Single application entry point:** `http://127.0.0.1:8765/`

SS is a local-first intelligent orchestration layer. It chooses a suitable model under privacy, capability, cost and available-compute constraints rather than being locked to one provider.

## v0.8.4 canonical Brain

- Permanent Second Brain chat archive outside the Git repository; no automatic deletion/pruning.
- Explicit approval before cloud chat turns; no silent provider substitution.
- Resource-aware routing telemetry including available RAM/CPU.
- FREE and PAID/OTHER model lists, alphabetically sorted in the provider UI.
- Local engines: Ollama, LM Studio/Bionic, Jan.
- Cloud/gateway providers: OpenRouter, Hugging Face Inference, Venice, OpenAI, Anthropic, Gemini, xAI, DeepSeek, Mistral, Moonshot/Kimi, Z.ai/GLM, Qwen/Alibaba Model Studio, Perplexity.
- Connector layer: Brave Search API, Higgsfield MCP, DuckDuckGo, Tor, HuggingChat and Meta AI.
- **Integrated read-only File / Legal Workspace:** recursive folder inventory, metadata-preserving document extraction (PDF/DOCX/XLSX/text), multi-source context assembly and evidence-oriented analysis through SS.
- **Duplicate-photo intelligence:** exact SHA-256 duplicate detection, oldest-creation-date canonical proposal and recoverable-space calculation. No deletion, rename, move or overwrite is performed.
- All workspace actions default to read-only. Original paths, timestamps and metadata are retained.
- Windows OS credential-store integration for provider keys; credentials are not written to GitHub, source code or chat archives.
- Canonical 8765 composition entry: `ss_entry.py` mounts Brain + Provider Console + read-only Workspace.

## Use

Run `run-SS.bat`. It pulls the current fast-forward GitHub build, creates/updates `.venv`, installs requirements, safely reuses/restarts an existing SS process occupying 8765, and starts the **canonical `ss_entry:APP`** at **127.0.0.1:8765**. It never terminates an unrelated process occupying the port. The integrated workspace is at `127.0.0.1:8765/workspace`.

`ss_entry.py` is the canonical 8765 composition layer. Do not launch `app.py` or `app_integrated.py` directly as competing SS servers.

## Data safety

Application source is versioned in GitHub. User chats are outside the repository under the SS application-data directory. Updates do not reset, prune or overwrite that archive. The workspace is read-only by design.

The old 8766 provider-console prototype had an in-memory chat persistence defect. **Do not delete its browser/application data until the recovery procedure in `docs/RECOVER-8766-CHAT.md` has been attempted.** If the old 8766 tab is still open and visibly contains the missing chats, do not reload or close it; follow that recovery procedure first.

## Important boundary

A provider being listed does not mean its private credential or local server is magically available. SS reports actual endpoint/credential boundaries. It does not invent APIs. Cloud requests remain gated by explicit approval.

## Verification

The repository has GitHub Actions regression tests for the canonical v0.8.4 entry, including release-version, identity/provenance, workspace safety and required-route checks. A green CI result is required before treating a repository change as verified; provider credentials and local runtimes still require machine-side endpoint tests.
