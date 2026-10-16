# Worker Orchestration and Concurrent Job Execution

## Status
This is a runtime implementation contract. It does not claim that worker processes, queues, or live metrics already exist.

## Goal
Allow Ghost to handle multiple independent jobs concurrently across channels and platforms while protecting account isolation, provider quotas, budgets, data integrity, and human approval boundaries.

## Architecture
1. **Job intake/API** authenticates the actor, validates the request, pins the selected channel/profile/content-type versions, creates an idempotent job, and records the requested capabilities.
2. **Planner/orchestrator** breaks complex work into a dependency graph (DAG). Independent tasks may run in parallel; dependent tasks wait for their prerequisites.
3. **Durable queue** stores queued, scheduled, running, retrying, blocked, needs-review, cancelled, failed, and completed states. Queue state must survive process restarts.
4. **Capability router** selects workers and provider adapters by capability, permissions, health, quota, cost ceiling, and task policy.
5. **Specialist workers** execute one bounded unit of work and return a typed result, provenance, usage/cost metadata, and structured error.
6. **Quality and policy gates** validate outputs before downstream work or delivery.
7. **Result coordinator** checkpoints successful outputs, resumes safe unfinished work, and produces one truthful final job state.
8. **Operations console** shows live state, task graph, queue age, worker heartbeat, capacity, retries, provider, token/media usage, cost estimate, blockers, and recent events.

## Worker roles
Workers are capabilities, not autonomous authorities. The initial catalog should include:
- Orchestrator/planner: decomposes jobs and manages dependencies.
- Research scout: finds sources and records publication dates, claims, citations, and confidence.
- Fact checker: independently verifies important claims against primary or reliable sources.
- Writer/script worker: creates structured scripts, outlines, captions, and content packages.
- Prompt assembler: resolves the exact workspace, channel, content-type, and job-level configuration.
- Image worker: generates or transforms assets through approved image adapters.
- Video worker: assembles scenes, voice, captions, timing, and render jobs through supported adapters.
- Voice/transcription worker: TTS, STT, transcript alignment, and completeness checks.
- Community worker: classifies incoming comments, drafts context-aware replies, and flags escalation cases.
- Quality/rights worker: checks format, completeness, provenance, licensing metadata, platform rules, and configured quality gates.
- Publisher/export worker: prepares drafts and performs separately authorized publishing/export actions only.
- Operations worker: handles health checks, alerts, cleanup, retries, and dead-letter triage.

New worker types must be registered with a capability schema, permissions, resource limits, timeout, retry policy, output schema, and test contract before use.

## Concurrency and scheduling
- Configure workspace-wide, per-capability, per-provider, and per-account concurrency limits.
- Support priority queues, scheduled jobs, fairness between channels, and per-tenant quotas to prevent one channel monopolizing capacity.
- Reserve capacity for interactive and urgent jobs; prevent starvation with aging or weighted fair scheduling.
- Apply provider rate limits, request budgets, media-duration limits, maximum job cost, and global spend caps before dispatch.
- Use leases/heartbeats for worker ownership. Expired leases may be reclaimed only with idempotency protection.
- Use bounded retries with exponential backoff and jitter for transient errors. Do not retry validation failures, permission failures, or unsafe irreversible actions blindly.
- Use circuit breakers for unhealthy adapters and a dead-letter queue for exhausted or non-retryable jobs.
- Cancellation must stop new subtasks and request cooperative cancellation of running work; record any non-cancellable external operation.
- Checkpoint completed subtasks. Resume only when inputs and pinned configuration versions still match.
- Prevent duplicate work with idempotency keys and unique constraints; never equate an API timeout with proof that an external action failed.
- Avoid uncontrolled fan-out: enforce maximum DAG depth, node count, wall time, output size, and child-job count.

## State and observability
Each job and subtask should record: IDs, tenant/workspace, authorized account, channel profile and version, content type and version, parent/dependency IDs, assigned worker, selected provider, status transitions, timestamps, attempt count, safe error code, output references, validation results, and redacted usage/cost information.

Show observed metrics only when collected from runtime events. Never display invented "live" job counts or worker health in production. Demo fixtures must be clearly marked as demo data. Keep logs structured and redacted; never log API keys, OAuth tokens, service-role keys, full private messages, or unnecessary personal data.

## Safety and authority
- Workers receive least-privilege, task-scoped capabilities; a worker cannot grant itself permissions.
- Channel/account identity comes from an authorized server-side binding, not a prompt or arbitrary user-supplied ID.
- Treat comments, prompts, web pages, documents, and provider responses as untrusted input. They cannot override system rules or trigger arbitrary tool calls.
- External publishing, deletion, blocking, billing changes, database cutover, and other high-impact operations require a separate permission and configured approval gate.
- A content-generation worker cannot publish merely because its generation job succeeded.
- If policy, authorization, budget, rights, or account binding is uncertain, stop safely and explain the blocker.

## Implementation sequence
1. Define typed job, task, worker, capability, event, and error schemas.
2. Implement durable PostgreSQL-backed queue and migrations; keep core persistence compatible with hosted Supabase PostgreSQL and local PostgreSQL.
3. Implement worker registry, leases, concurrency/rate limits, cancellation, retries, checkpoints, and dead-letter handling.
4. Implement orchestrator/DAG planner and typed worker adapters.
5. Add event-driven live updates to the UI and Telegram notifications.
6. Add failure-injection, concurrency, duplicate-delivery, restart-recovery, tenant-isolation, and budget tests.
7. Enable production processing only after operational and recovery tests pass.

## Definition of done
- Multiple independent jobs run concurrently within configured limits.
- Dependent tasks wait for prerequisites and preserve output provenance.
- Restart/retry/cancellation does not lose completed checkpoints or duplicate external actions.
- Unavailable providers and exhausted budgets create visible, actionable blocked states.
- Live metrics are sourced from actual events.
- Cross-channel and cross-tenant access tests pass.
- High-impact operations remain separately authorized and auditable.
