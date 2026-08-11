# SS — Second Brain v0.8

Local-first AI orchestrator with an integrated multi-provider console.

**Status:** v0.8 foundation / provider integration.

## Components

- SS Second Brain: local FastAPI application on `127.0.0.1:8765`
- Integrated provider console: `/providers`
- Providers: Ollama, LM Studio/Bionic, Jan, OpenRouter (ZDR), Venice
- No Docker or WSL required
- Cloud API keys are entered locally in the browser and sent only to the selected provider; they are not written to the SS server filesystem.

## Run on Windows

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m uvicorn app:app --host 127.0.0.1 --port 8765
```

Open `http://127.0.0.1:8765/`.

See `docs/ARCHITECTURE.md` and `docs/RELEASE.md`.
