# SS v0.8 architecture

SS is the application and orchestrator. The provider console is an integrated UI/API layer, not a replacement application.

## Ports

- SS: `127.0.0.1:8765`
- There is no separate provider server in this release.
- Provider UI: `http://127.0.0.1:8765/providers`

## Providers

The adapter boundary normalizes model discovery and chat across Ollama, LM Studio/Bionic, Jan, OpenRouter and Venice. Local providers require their own local server. Cloud providers require a browser-supplied API key.

OpenRouter requests can request ZDR with `provider.zdr=true` and `data_collection=deny`.

## Security

No API keys are committed to GitHub and the server does not write them to disk. Do not put secrets into repository files.
