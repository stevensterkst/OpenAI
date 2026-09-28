# SS v0.8.4 ↔ AnythingLLM Integration

## Architecture

```
SS Second Brain (8765)
   Orchestrator/Brain
   │
   ├─ Direct providers (OpenAI, Claude, Gemini, etc)
   │
   └─ AnythingLLM Gateway (new in v0.8.4)
        │
        └─ Ollama Local Engine
             │
             └─ phi4-mini:3.8b (configured model)
```

## Verified API Endpoints

All endpoints use AnythingLLM's **documented API v1**:

### Discovery
- `GET /api/v1/system/status` — Verify AnythingLLM is online

### Configuration
- `GET /api/v1/workspaces` — List available workspaces
- `GET /api/v1/workspace/{slug}/settings` — Verify LLM provider config

### Inference
- `POST /api/v1/workspace/{slug}/chat` — Execute documented chat endpoint

## Configuration

### 1. AnythingLLM Installation

AnythingLLM must be running on default port `127.0.0.1:3001` or configured via:

```bash
export ANYTHINGLLM_BASE="http://127.0.0.1:3001"
```

### 2. AnythingLLM API Key

Store in Windows Credential Manager:

```python
import keyring
keyring.set_password("SS-Second-Brain", "anythingllm", "<api-key-from-anythingllm>")
```

### 3. Ollama Configuration in AnythingLLM

In AnythingLLM workspace settings:
- Select **Ollama** as the LLM Provider
- Point to: `http://127.0.0.1:11434` (Ollama default)
- Select model: `phi4-mini:3.8b` (must be pulled: `ollama pull phi4-mini:3.8b`)

## Integration in SS

SS automatically:
1. Discovers AnythingLLM endpoint
2. Authenticates with stored API key
3. Selects first available workspace
4. Verifies Ollama is configured
5. Routes eligible tasks through the chain
6. Falls back to direct providers if AnythingLLM fails

## Testing

```bash
# Run end-to-end tests
pytest tests/test_anythingllm.py -v

# or manually from Python
python tests/test_anythingllm.py
```

Tests verify:
- Endpoint reachability ✓
- API key configuration ✓
- Workspace availability ✓
- Ollama provider ✓
- **Real model inference** ✓

## Inference Chain Flow

```
User (8765 UI)
   ↓
SS Router (classify task → select provider)
   ↓ [if AnythingLLM selected or auto-routed]
SS AnythingLLM Adapter
   ↓
POST /api/v1/workspace/{slug}/chat
   ↓ [at AnythingLLM 3001]
AnythingLLM Orchestrator
   ↓
Ollama API (11434)
   ↓
Phi4-mini Model
   ↓ [inference]
Response → AnythingLLM → SS → User
```

## Fallback Behavior

If AnythingLLM fails at any point:
1. SS logs the boundary error
2. SS does NOT silently substitute another provider
3. SS reports to user with diagnostic
4. User can explicitly enable cloud provider or retry with different config

## Documentation References

- Official AnythingLLM API: https://docs.anythingllm.com/api/overview
- Ollama: https://ollama.ai
- phi4-mini: Model configuration in Ollama
