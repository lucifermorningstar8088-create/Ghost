# Compute Adapters: Current Contract

## Implemented in this phase

- `KaggleCliAdapter` detects whether the Kaggle CLI and server-side `KAGGLE_USERNAME`/`KAGGLE_KEY` are present.
- It builds a Kaggle `kernels push` command with a bounded `--timeout` and validates that the local kernel directory exists.
- It polls `kaggle kernels status` with a subprocess timeout and reports `unknown` when status cannot be reliably read.
- `LocalHardwareAdapter` always permits CPU-side capability checks and optionally detects an NVIDIA GPU through `nvidia-smi`; GPU-required jobs are not assumed to fit CPU-only hardware.
- `ComputeRouter` prefers Kaggle only when the pool is enabled, credentials/CLI are available, quota freshness is affirmed by its caller, and budget headroom is affirmed by its caller. Otherwise it selects local hardware only if the task fits, or returns no provider with a reason.
- Live launch remains fail-closed unless `GHOST_COMPUTE_EXECUTION_ENABLED=true`.

## Not yet implemented

These adapters are not yet wired to the authenticated job API or a durable quota ledger. The API still persists dry-run jobs only. There is no live remote workload submission, automatic remote cancellation, durable reservation accounting, or verified end-to-end GPU run in this phase. Do not set the live execution flag in production until the quota ledger, authenticated admission endpoint, actual workload packaging, cancellation/reconciliation, and integration tests are implemented.

## Runtime stop behavior

The CLI adapter uses the supported `--timeout` option when building a push command and can query remote status. The current documented command interface does not provide a dedicated stop command. The workload must exit naturally on completion; Ghost must verify the terminal remote status. Unknown status must never be interpreted as stopped and must not release a future quota reservation.

## Required next steps

1. Add database-backed quota snapshots and budget reservations with atomic admission.
2. Wire the router into an authenticated admission service and preserve tenant isolation.
3. Define a safe, versioned workload package contract; do not execute arbitrary request-provided shell commands.
4. Implement a local worker with explicit resource limits and hard timeout.
5. Implement Kaggle submit/status/artifact reconciliation using only documented CLI/API behavior.
6. Test timeout, duplicate submissions, stale quota, concurrency races, cancellation uncertainty, and secret redaction against fake providers before any live run.
