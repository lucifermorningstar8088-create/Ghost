# Durable LLM task intake

Ghost exposes tenant-scoped task-intake endpoints:

- `POST /api/v1/llm/tasks` accepts a validated chat request and returns `202 Accepted` with status `queued`.
- `GET /api/v1/llm/tasks` lists the authenticated tenant's recent tasks.
- `GET /api/v1/llm/tasks/{task_id}` returns one task belonging to that tenant.

Every request requires a verified bearer token and an `Idempotency-Key` header. Repeating the same key with the same request returns the existing task; reusing the key with a different request returns HTTP 409. Retry attempts are bounded to 1-5. Task payloads and state are persisted in the database through migration `0004_llm_tasks`.

## Important current limitation

This is durable **task intake and status storage**, not a completed execution queue. No background worker currently claims tasks, calls the LLM router, retries failures, or updates a task to completed/failed. Newly accepted tasks remain `queued` until a worker is implemented and deployed. The synchronous `POST /api/v1/llm/chat` endpoint remains the only endpoint that currently executes a provider request.

Do not interpret `queued` as GPU/API execution started. The worker should later use atomic claims/leases, bounded retries with backoff, tenant-scoped updates, and safe error codes before this is used for production automation.
