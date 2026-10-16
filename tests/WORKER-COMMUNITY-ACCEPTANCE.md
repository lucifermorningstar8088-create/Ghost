# Worker Orchestration and Community Acceptance Matrix

These are required tests, not claims that they already pass.

## Worker and parallel-job tests
- [ ] Two independent jobs execute concurrently when capacity permits.
- [ ] A dependent task cannot start before its prerequisite succeeds.
- [ ] Per-workspace, per-account, per-provider, and per-capability limits are enforced.
- [ ] One busy channel cannot starve other channels indefinitely.
- [ ] A worker crash or expired lease recovers without losing completed checkpoints.
- [ ] A transient provider error retries with bounded backoff and jitter.
- [ ] Permission, schema, budget, and rights failures do not retry blindly.
- [ ] Circuit breaker routes away from an unhealthy provider only to an explicitly approved fallback.
- [ ] Exhausted tasks enter a visible dead-letter/manual-review state.
- [ ] Cancellation prevents new subtasks and records non-cancellable external work.
- [ ] Duplicate queue delivery does not duplicate external side effects.
- [ ] Restarting the service preserves queued/running job recovery state.
- [ ] Budget and quota caps block dispatch before an over-budget paid call.
- [ ] Live dashboard values come from runtime events; fixtures are marked demo.
- [ ] Tenant/account isolation is enforced even if a caller tampers with IDs.
- [ ] Publishing, deletion, and other high-impact actions require separate authorization and approval.

## Community inbox and reply tests
- [ ] Sync deduplicates repeated webhooks and paginated records by stable remote IDs.
- [ ] An account with missing/expired scopes is shown disconnected and cannot send.
- [ ] Channel switching never leaks comments, profile voice, or destination account.
- [ ] Reply draft references the actual comment and uses the selected channel profile.
- [ ] Factual question/correction requires evidence or is escalated.
- [ ] Unverified location, price, date, result, or promise is not stated as fact.
- [ ] Reply is checked for repetition against recent channel replies.
- [ ] Threats, personal data, harassment, and high-stakes topics always require human review.
- [ ] Low confidence or ambiguous sarcasm does not auto-send.
- [ ] Auto-send is disabled by default and can be paused immediately.
- [ ] Auto-send only accepts explicitly allow-listed low-risk categories.
- [ ] Approve/edit/reject/escalate actions are permission-checked and audited.
- [ ] Bulk approval cannot bypass per-item safety gates.
- [ ] Send timeout triggers remote read-back before retry.
- [ ] Failed or unknown sends are not falsely labeled sent.
- [ ] Rate limits and provider outages use bounded backoff and visible failure states.
- [ ] Telegram notifications omit credentials and unnecessary personal data.
- [ ] Metrics distinguish draft, edited, rejected, escalated, sent, and failed outcomes.
