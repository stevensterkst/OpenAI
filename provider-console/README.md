# SS Provider Console v0.8

This is the provider-console application surface extracted from the integrated SS v0.8 architecture. The canonical runnable console is served by the SS application at `http://127.0.0.1:8765/providers`.

It is deliberately not another server competing for port 8765. SS owns the application and provider routing.

## Direct engines

- Ollama — `127.0.0.1:11434`
- LM Studio/Bionic — OpenAI-compatible local API
- Jan — OpenAI-compatible local API
- OpenRouter — cloud, with ZDR/data-collection-deny request mode
- Venice — cloud/private-oriented provider

## Integration contract

The UI calls the SS provider API. SS remains responsible for routing, context, memory and future resource-aware model selection.
