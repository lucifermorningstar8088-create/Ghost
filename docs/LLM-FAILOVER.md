# Ghost LLM provider failover

Ghost can route requests through multiple OpenAI-compatible chat-completions providers. Providers are tried in ascending numeric priority; assign the fast, dependable primary a lower number and configure backup providers with higher numbers.

## Environment configuration

Example server-side environment variables (replace example URLs/model IDs with providers you actually have access to):

```dotenv
GHOST_LLM_PROVIDERS=fast,backup
GHOST_LLM_FAST_BASE_URL=https://provider-a.example/v1
GHOST_LLM_FAST_API_KEY_ENV=PROVIDER_A_API_KEY
GHOST_LLM_FAST_MODEL=provider-fast-model
GHOST_LLM_FAST_PRIORITY=1
GHOST_LLM_FAST_TIMEOUT_SECONDS=15
GHOST_LLM_FAST_MAX_CONCURRENCY=8
GHOST_LLM_BACKUP_BASE_URL=https://provider-b.example/v1
GHOST_LLM_BACKUP_API_KEY_ENV=PROVIDER_B_API_KEY
GHOST_LLM_BACKUP_MODEL=provider-backup-model
GHOST_LLM_BACKUP_PRIORITY=2
GHOST_LLM_BACKUP_TIMEOUT_SECONDS=25
GHOST_LLM_BACKUP_MAX_CONCURRENCY=4
PROVIDER_A_API_KEY=configure-in-secret-manager
PROVIDER_B_API_KEY=configure-in-secret-manager
```

The values for `*_API_KEY_ENV` are names of environment variables, not the secret values. Set actual secrets only in the server's secret manager/environment. Never put provider keys in the browser, repository, logs, or user prompts.

## Request behavior

- Authenticated endpoint: `POST /api/v1/llm/chat`.
- Authenticated provider health: `GET /api/v1/llm/health`; output contains provider/model/priority/capacity only, never credentials.
- Provider health is cached briefly. Missing credentials, unsuccessful health probes, HTTP 429, server errors, transport errors, malformed responses and empty responses do not produce a successful answer. The router moves to the next eligible provider.
- Per-provider in-flight limits avoid sending unlimited concurrent requests to one provider. If one provider reaches its limit, the router can try the next.
- Failed providers enter a short cooldown, so repeated requests can bypass a temporarily failing primary.
- If all providers are unavailable, the API returns HTTP 503 rather than pretending the task succeeded. Callers can safely retry with bounded backoff.
- Requests use a provider-agnostic chat-completions payload. This initial adapter does not support provider-specific tools, image inputs, streaming, or non-OpenAI-compatible APIs.
- Priority is configured by the operator. The router does not yet run a benchmark to automatically discover the objectively fastest model, and no provider can be guaranteed to be always available. Keep at least two independently hosted providers configured.

## Current limitations

This is an initial in-process router, not a distributed queue. Health/cooldown/concurrency state is per API process and resets on restart. There is not yet tenant-level token/cost accounting, streaming failover, provider-specific retry semantics, circuit-breaker metrics, or durable job handoff. Do not promise seamless continuation of a generation that already streamed partial output; the current endpoint is non-streaming, so it can switch providers before returning a response.
