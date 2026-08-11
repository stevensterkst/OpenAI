# SS Second Brain v0.8.0

## Release intent

This release establishes the real SS application boundary: Second Brain/orchestrator on port 8765 with the provider console integrated into the same application.

## Included

- FastAPI application
- `/system` health endpoint
- provider registry
- model discovery
- chat adapters for five providers
- integrated provider UI at `/providers`
- OpenRouter ZDR/data-collection deny request controls
- Windows-friendly local run instructions

## Verification

Before considering a deployment complete, run the application locally and verify `/system`, `/api/providers`, `/providers`, model discovery for each installed local provider, and at least one successful chat for each configured provider. Cloud providers require the user's own credentials.

This release does not claim that unavailable provider servers are online; their availability is runtime-dependent.
