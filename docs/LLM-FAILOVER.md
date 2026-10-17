# LLM Fast-First Routing and Automatic Failover

Ghost's authenticated endpoint is `POST /api/v1/llm/chat`. It uses the server-side provider registry and tries the configured fast providers first, then the remaining providers by priority. If a model is rate-limited, times out, returns a server error, or is unreachable, the router attempts the next configured model/provider. A provider with missing credentials is skipped.

## Configuration

Set `GHOST_LLM_PROVIDERS` as a JSON array in the API service's server-side environment. Never put provider keys inside this JSON, browser variables, source code, request payloads, or logs. The JSON contains *names of environment variables*, not their values.

Example (replace provider URLs and model IDs with values supported by your chosen providers):

```json
[
  {
    "name": "fast-primary",
    "base_url": "https://api.provider-one.example/v1",
    "api_key_env": "PROVIDER_ONE_API_KEY",
    "models": ["fast-model-id", "backup-model-id"],
    "fast": true,
    "priority": 10,
    "timeout_seconds": 15
  },
  {
    "name": "reliable-backup",
    "base_url": "https://api.provider-two.example/v1",
    "api_key_env": "PROVIDER_TWO_API_KEY",
    "models": ["supported-model-id"],
    "fast": false,
    "priority": 20,
    "timeout_seconds": 25
  }
]
```

Configure the actual secrets separately as `PROVIDER_ONE_API_KEY` and `PROVIDER_TWO_API_KEY` in Render or the deployment secret manager. Do not use the example hostnames/model IDs as real endpoints.

Provider URLs must use HTTPS. Local HTTP endpoints are rejected unless `GHOST_LLM_ALLOW_INSECURE_HTTP=true` is explicitly set in a trusted development environment only.

## Failover behavior

- Fast-marked providers are attempted first; configured priority orders providers within each class.
- Models listed on a provider are attempted in the configured order.
- HTTP 408/409/425/429, HTTP 5xx, timeouts, network errors, missing credentials, invalid provider responses, and provider authentication/permission failures trigger failover.
- HTTP 4xx errors other than the retryable statuses and 401/403 are treated as request/configuration errors and returned rather than blindly repeating a malformed request.
- Provider failures open a process-local circuit breaker after repeated failures. A successful response resets that provider's breaker.
- If every route fails, the endpoint returns HTTP 503 with a safe status message and `Retry-After`.
- API keys are sent only in server-to-provider Authorization headers. The client cannot choose a provider or override a model.

## Availability limits and honest guarantees

Failover is sequential for a request, not simultaneous duplicated generation. This avoids accidental double billing and conflicting answers. A request may still fail if all providers are down, all keys are invalid, quotas are exhausted, the request is unsupported by every model, or the network is unavailable. No design can guarantee that every external API is always available.

The circuit breaker is currently process-local. With multiple API replicas, each process has separate health state; use a shared Redis/database breaker if cross-replica coordination becomes necessary. Provider availability is learned from actual request outcomes, not a claimed always-live external status API.

The router currently targets the OpenAI-compatible `/chat/completions` protocol. Providers using a different API protocol need an explicit adapter; do not assume a key/model is compatible merely because it is called an LLM API.

## Current integration status

The endpoint and unit tests are included in the code change. Merge only after CI passes. Deployment still requires configuring at least two genuinely independent compatible providers and their server-side secrets. No provider API keys are included in the repository.
