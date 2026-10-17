# Remote Compute and Kaggle GPU Workload Manager

## Purpose

Ghost should accept a compute job from its UI/API, validate workload and budget, select an approved compute pool, submit or dispatch the job, record state and usage, checkpoint long-running work, and collect logs/artifacts. The local PC acts as the control plane; heavy work executes on a configured remote provider.

This document defines the integration contract and rollout plan. The example configuration is proposed, not a working Kaggle adapter or proof that a remote GPU is connected.

## Kaggle quota and account policy

- Kaggle documents a weekly GPU quota commonly around 30 hours, but actual quota and accelerator availability can vary. Verify the current account UI and official documentation before scheduling.
- Ghost's Kaggle integration supports one configured Kaggle account. Do not rotate across accounts, create extra accounts, or combine accounts to evade platform quota.
- The configured weekly GPU-hour budget is an internal safety ceiling, not a live quota measurement. It must not exceed the user's confirmed remaining quota. The scheduler must stop if quota data is unknown or stale.
- Do not claim the Kaggle API exposes an exact remaining GPU-hour balance unless this is verified against current official API documentation. Until then, use operator-entered quota snapshots and tracked Ghost-launched job durations, clearly marked as estimates.
- Follow Kaggle terms, competition rules, notebook limits, and provider rate limits. Do not use GPU sessions as an always-on endpoint unless current provider rules permit it.

## Proposed architecture

1. Compute pool registry: provider, status, capabilities, credential environment-variable names, budget and parallelism limits. Secret values never belong in YAML, Git, or browser state.
2. Job admission: validate task type, estimated duration, required accelerator/RAM, input/output sizes, retry safety and approved budget.
3. Quota ledger: record estimated GPU minutes per provider/account, job, start/end time, status, measurement source, and timestamp of the latest operator/provider quota snapshot.
4. Scheduler: choose an enabled pool that supports the job, has a fresh quota snapshot and budget headroom, and is within parallelism limits. Unknown quota means pause, not assume unlimited capacity.
5. Remote runner adapter: use the official Kaggle CLI/API to publish/update notebooks or scripts and inspect job status where supported. Do not scrape private endpoints or bypass session controls.
6. Checkpoint/artifact store: save periodic checkpoints and logs durably; retrieve final artifacts and verify size/checksum before marking success.
7. UI observability: show queued/running/completed/failed/cancelled state, provider label, elapsed and estimated GPU time, last quota snapshot, retry count, artifact links and truthful degraded/unknown status.
8. Fallback router: if Kaggle quota is exhausted or unknown, queue the job or route only to another explicitly authorized provider with a valid budget. Paid providers require explicit spend authorization.

## Job lifecycle

Normal path: queued -> admitted -> submitted -> running -> checkpointing -> succeeded.

Failure paths: retry_wait, failed, cancelled, quota_blocked, needs_attention. State transitions must be persisted and idempotent; retrying a submission must not accidentally launch duplicate compute.

## Proposed API contracts (not implemented yet)

- POST /api/v1/compute/jobs: create a validated job with tenant authorization and explicit resource/budget bounds.
- GET /api/v1/compute/jobs: list only jobs belonging to the caller's tenant.
- GET /api/v1/compute/jobs/{job_id}: inspect status, redacted log summary, usage estimate and artifact metadata.
- POST /api/v1/compute/jobs/{job_id}/cancel: request supported cancellation and reconcile remote state.
- GET /api/v1/compute/pools: return non-secret pool configuration and health.
- POST /api/v1/compute/pools/{pool_id}/quota-snapshot: record a user-confirmed quota snapshot; never accept a secret in the request body.

## Security and reliability requirements

- Credentials stay in server-side environment or an approved secret manager. Never send Kaggle tokens to React, log them, or commit them.
- Default-deny provider launch; only configured, validated and enabled pools may execute jobs.
- Enforce GPU-hour ceiling, max parallel jobs, max run duration, retry ceiling and per-job estimated-cost ceiling.
- Require explicit budget authorization before any paid call.
- Enforce tenant authorization and audit job creation, cancellation and provider changes.
- Reconcile remote status before releasing quota reservations after cancellation.
- Do not assume Kaggle session disk is permanent; store checkpoints and artifacts durably.
- Treat quota as unknown when snapshots are stale, usage records are incomplete, or provider state cannot be reconciled.
- Add dry-run mode and fake-provider tests before enabling remote execution.

## Implementation phases

1. Contract/config: schema, safe example config, docs, validation and CI.
2. Local queue + dry run: persisted jobs and simulated provider; test admission, budget checks, duplicate submissions, retries and cancellation.
3. Single-account Kaggle adapter: official CLI/API only, notebook template, status reconciliation, artifact retrieval and manually verified quota snapshots.
4. Compute dashboard: live jobs, usage estimates, quota freshness, logs and checkpoint/artifact links.
5. Additional authorized providers: one adapter at a time, with provider-specific billing, terms, tests and budget controls.

## Optional Kaggle API and local-hardware fallback

Kaggle credentials are optional. Ghost must remain usable when no Kaggle API credentials are configured.

Selection policy:

1. If a Kaggle pool is configured, credentials are present, the pool is explicitly enabled, quota is fresh/verified, and budget/concurrency checks pass, prefer Kaggle first for compatible GPU workloads.
2. If Kaggle credentials are absent, use the local hardware adapter for tasks that fit the machine's available CPU/RAM/GPU resources. Do not attempt a Kaggle API call or block local jobs waiting for credentials.
3. If Kaggle is configured but disabled, quota is unknown/stale, the quota/budget gate fails, or the provider is unavailable, do not launch on Kaggle. Route to local hardware only if the task fits local capacity; otherwise queue it and explain the blocker.
4. Never silently switch to a paid provider. Any paid alternative requires explicit authorization.
5. Detect local CPU/RAM and, where supported, local GPU availability at runtime. Do not assume a GPU exists. If local hardware is insufficient, fail admission with a clear resource message rather than starting an impossible job.
6. Every remote Kaggle run must have a maximum runtime and use the documented Kaggle CLI timeout option. Workloads should exit naturally on completion, then Ghost verifies remote status. If remote termination cannot be verified, mark `needs_attention` and retain the budget reservation.

This policy is routing intent only; it does not mean a live Kaggle or local GPU execution adapter is already implemented. Keep provider launch disabled until adapters and acceptance tests are merged.

See [Kaggle Runtime Stop Guard](KAGGLE-RUNTIME-STOP-GUARD.md) for runtime limits, stop verification, and failure handling.

## References

- Kaggle notebooks: https://www.kaggle.com/docs/notebooks
- Kaggle efficient GPU usage: https://www.kaggle.com/docs/efficient-gpu-usage
- Kaggle public API and rate limits: https://www.kaggle.com/docs/api
- Kaggle terms: https://www.kaggle.com/terms
