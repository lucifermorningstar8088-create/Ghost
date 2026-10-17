# Kaggle Runtime Stop Guard

## Goal

Do not leave a Kaggle GPU workload running after its task is complete. Every submitted run must have a hard maximum runtime, a workload-level completion path, and a status reconciliation step before Ghost finalizes the job.

## Important provider limitation

The documented Kaggle CLI supports `kaggle kernels push --timeout <SECONDS>` and `kaggle kernels status <KERNEL>`. The documented command list does not include a supported `kernels stop` command. Do not treat deleting a kernel as a safe stop mechanism, and do not call undocumented endpoints unless Kaggle documents and supports them for this integration.

Therefore, this guard is built around:
1. A hard run timeout passed when submitting the kernel.
2. The workload returning/exiting as soon as its work is complete.
3. A watchdog that polls the kernel status and records the terminal state.
4. A fail-safe `needs_attention` state when status cannot be confirmed; never report a runtime as stopped based only on a local job flag.

## Required launch contract

- Require a positive `max_runtime_seconds` for every remote run.
- Pass the configured maximum as the Kaggle CLI `--timeout` option.
- Include a completion sentinel/artifact written only after outputs and checkpoints are flushed.
- On completion, stop producing work, flush/close files, write the completion sentinel, and exit the notebook/script naturally.
- On timeout, persist the timeout reason and try only a provider-supported termination mechanism if one becomes available and is explicitly enabled.
- Poll `kaggle kernels status` with bounded intervals and an overall verification deadline.
- Do not release a GPU budget reservation until the remote status is terminal or an operator has reconciled it. If status is unknown, keep the reservation held and mark `needs_attention`.
- Do not automatically rerun a timed-out job unless it is checkpointed, retry-safe, within budget, and the prior run is known to have terminated.
- Redact tokens and private environment values from logs.

## State transitions

`running -> completion_detected -> verifying_stop -> succeeded`

`running -> timeout_requested -> verifying_stop -> timed_out`

`verifying_stop -> needs_attention` when remote status is unknown or remains active beyond the verification deadline.

A successful local process exit is not sufficient evidence that a remote session is stopped. The provider adapter must confirm the remote kernel status before finalizing the job.

## Suggested defaults

- `stop_on_completion: true`
- `max_runtime_seconds: 3600` (one hour; operators may lower it for short tasks)
- `stop_verification_timeout_seconds: 300`
- `status_poll_interval_seconds: 15`

These are Ghost safety defaults, not claims about Kaggle's maximum runtime or quota policy.

## Acceptance tests before enabling live GPU execution

1. The submit command always includes the configured timeout.
2. Successful workload completion flushes outputs and exits without waiting for an unrelated long-running loop.
3. The watchdog observes terminal status and finalizes once, idempotently.
4. An active/unknown status does not mark the job successful or release its reservation.
5. Timeout and status-check failures lead to `timed_out` or `needs_attention`, not infinite polling.
6. Repeated completion/status events do not double-release reserved GPU hours.
7. Dry-run tests never invoke Kaggle or any remote provider.

## References

- Official Kaggle kernel command reference: https://github.com/Kaggle/kaggle-cli/blob/main/docs/kernels.md
- Kaggle efficient GPU usage: https://www.kaggle.com/docs/efficient-gpu-usage
