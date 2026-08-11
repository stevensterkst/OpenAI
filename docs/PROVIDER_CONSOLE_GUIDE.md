# SS Provider Console — how to use it

Open `http://127.0.0.1:8765/` and click **Open integrated AI Provider Console**. The console is part of SS; it is not a second server.

## 1. Select an engine

Click one of the five provider cards on the left:

- **Ollama** — local, default endpoint `http://127.0.0.1:11434`
- **LM Studio / Bionic** — local OpenAI-compatible server, default `http://127.0.0.1:1234/v1`
- **Jan** — local OpenAI-compatible server, default `http://127.0.0.1:1337/v1`
- **OpenRouter** — cloud; requires an API key. ZDR is enabled by default in the UI.
- **Venice AI** — cloud; requires an API key.

## 2. Click Models

`Models` calls the selected provider's model-list endpoint and fills the model selector. If the provider is unavailable, SS reports the boundary instead of pretending it worked.

## 3. Click Test

`Test` repeats model discovery and reports `READY`, model count, and latency. This is the first diagnostic to use when a provider does not work.

## 4. Choose a model and Send

Select a discovered model, type a prompt, and press `SEND`. The conversation is maintained in the browser for the selected provider during the session.

## 5. SS Router

The **Analyse routing** tool accepts a task description and displays the current transparent routing priority. It is deliberately not yet a black-box autonomous router: v0.8.1 exposes the policy so it can be inspected and improved safely while the Second Brain work is being integrated.

Current intent classes:

- private/local/offline → local engines first
- current/web/research → cloud-capable engines first
- unrestricted/creative/roleplay → Venice/local engines first
- otherwise → local-first baseline

Availability and model suitability still need to be checked before actual execution.

## 6. Privacy

Cloud keys are kept in browser `localStorage` and passed to the selected provider. The SS server does not write them to its own filesystem. For OpenRouter, the request explicitly asks for ZDR and `data_collection: deny` when the ZDR checkbox is enabled.

## Important distinction

The console is integrated at `/providers` under the SS Second Brain application on port **8765**. Do not start a separate provider server on 8765. The old standalone 8766 experiments are not part of the current architecture.
