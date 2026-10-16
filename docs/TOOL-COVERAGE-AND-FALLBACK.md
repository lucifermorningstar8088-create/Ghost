# Ghost Tool Coverage and Fallback Standard

## Objective

Prevent avoidable workflow stoppages caused by missing integrations, provider outages, quota exhaustion, schema drift, or unavailable local capabilities. Coverage means every critical capability has a tested route or a safe stop; it does **not** mean connecting every available service.

## Operating rules

1. **Capability-first registry.** Register capabilities and contracts, not just vendor names. A provider can change without rewriting the workflow.
2. **Primary plus fallback.** Every critical capability must have a preferred implementation and at least one viable fallback path. The fallback may be another provider, a local tool, cached data, a queue, or a human approval step.
3. **Evidence-based states.** `proposed`, `configured`, `validated`, `enabled`, `degraded`, `disabled`. Never label a tool validated based on documentation or file presence alone.
4. **Progressive discovery.** Search the registry and load only the tool schemas needed for the current task. Do not inject every tool definition into every model call.
5. **Bounded recovery.** Use timeouts, bounded retries with jitter, circuit breakers, idempotency keys, and dead-letter/manual review paths. Never retry irreversible publishing or account changes blindly.
6. **Security by default.** Deny by default; least-privilege scopes; secret manager/environment injection; account/tenant isolation; redacted logs; allowlisted destinations; human approval for consequential external actions.
7. **Cost controls.** Free-first where practical, but never assume a free tier exists or is permanent. Track provider costs, quotas, latency, reliability, and quality. Never silently invoke paid services.
8. **Graceful degradation.** If both primary and fallback fail, preserve the job and evidence, report the exact blocker, and queue or request human intervention. Never fabricate success.
9. **Contract testing.** Verify auth, schema, representative request/response, rate-limit behavior, timeouts, retries, permissions, and recovery before enabling a connector.
10. **No universal fallback fiction.** Different providers are not automatically interchangeable. Check platform policies, data rights, freshness, output formats, and quality before failover.

## Critical capability matrix

| Capability | Primary route (proposed) | Fallback / recovery route | Safe failure behavior |
|---|---|---|---|
| Tool discovery | Registry search + MCP `tools/list` | Cached catalogue with TTL and freshness marker | Use last known schema only if still approved; otherwise stop |
| Model reasoning | Configured model adapter | Second approved model adapter; deterministic rules for simple tasks | Persist task and request retry/approval |
| Web research | Approved search adapter | Second search provider or previously verified cache | Mark evidence unavailable/stale; do not invent citations |
| Documentation lookup | Context7 or official vendor docs | Version-pinned local docs/cache | Flag version uncertainty |
| Source control | GitHub API/connector | Local Git checkout and queued sync | Keep changes on branch; never claim remote push succeeded |
| API/backend | FastAPI + typed schemas | Local health/restart path; queue work if dependency unavailable | Return explicit degraded status |
| Persistent data | PostgreSQL/Supabase adapter | Durable local queue/export where configured | No silent data loss; halt writes if consistency is uncertain |
| Background jobs | Durable queue/worker | Retry queue + dead-letter queue | Preserve job ID and failure reason |
| Browser automation | Playwright | Official API if supported, otherwise manual workflow | Do not bypass MFA/CAPTCHA or access controls |
| Platform analytics | Official platform API/authorized export | Cached last successful snapshot with timestamp | Label stale data; avoid decisions on stale metrics |
| Publishing | Official platform API with scoped OAuth | Draft/export package for manual publication | Never repeat publish without idempotency/read-back |
| Asset sourcing | Rights-checked licensed/user-owned assets | Original asset generation or approved stock alternative | Block unverified assets |
| Image processing | Pillow/ImageMagick adapter | Alternate supported local library | Keep originals and report conversion failure |
| Video/audio processing | FFmpeg | Preserve source and queue conversion; approved alternate codec path | No partial file presented as final |
| Captions/transcription | Approved speech-to-text adapter | Second approved model or manual transcript | Flag low confidence for review |
| Text quality | Deterministic lint + model review | Alternate reviewer or human review | Block high-risk/low-confidence output |
| Copyright/rights review | Asset provenance ledger + policy checks | Manual legal/editorial review | Do not claim a definitive legal clearance |
| Security scanning | Pinned scanners in CI | Alternate scanner plus manual review | Critical unresolved finding blocks release |
| Test execution | pytest/CI pipeline | Local reproducible test command | No release on missing required test evidence |
| Observability | Structured logs + metrics/traces | Local append-only diagnostic logs | Surface degraded observability; redact secrets |
| Secrets | Environment/secret manager | Rotation and operator reconfiguration | Never hardcode or print credentials |
| Scheduling | Durable scheduler/queue | Reconcile missed jobs at startup | Deduplicate before replay |
| Documents/export | Format-specific converter | Alternate converter or source-format handoff | Validate output opens and content is complete |
| Cost/quota | Provider usage meters + budget policy | Cheaper approved model/local route; queue | Pause paid calls at budget ceiling |
| Notifications | Configured notification adapter | Secondary channel or in-app queue | Persist notification and expose pending state |
| Backups/recovery | Scheduled DB/export backups | Secondary storage destination | Alert on failed backup; test restoration |
| UI workflow | Automated browser tests | API contract tests + manual smoke test | Mark release blocked if critical path fails |

## Minimum tool contract

Each registered implementation should define:

- Stable `tool_id`, capability, provider, adapter version, and documentation URL.
- Input/output JSON schemas and timeout.
- Auth scopes and data classification.
- Required secrets by **name only**, never their values.
- Rate-limit and budget policy.
- Retry safety, idempotency support, and circuit-breaker behavior.
- Health check and representative contract test.
- Primary/fallback relationship and compatibility constraints.
- Status, last validation time, evidence link, owner, and known limitations.

## Required health and validation gates

- [ ] Credentials present without printing them; scope is least-privilege.
- [ ] Provider health check succeeds.
- [ ] Input and output validate against schemas.
- [ ] Representative task passes with a saved, redacted test receipt.
- [ ] Timeout, 429/rate-limit, 5xx, malformed response, and auth failure are handled.
- [ ] Fallback is tested and cannot duplicate irreversible actions.
- [ ] Budget/rate limits and tenant/account boundaries are enforced.
- [ ] Logs are redacted and include correlation/job IDs.
- [ ] Recovery path is documented and tested.
- [ ] Status reflects observed evidence, not intended configuration.

## Rollout order

1. Registry schema, adapters, policy enforcement, secret handling, and structured logs.
2. CI, tests, durable jobs, retries, idempotency, and dead-letter handling.
3. Model and research adapters with explicit fallback policies.
4. Platform read-only analytics and account isolation.
5. Draft generation and human review.
6. Publishing only after OAuth scopes, platform limits, preflight, idempotency, read-back, and recovery pass.
7. Monitoring, quota/cost dashboards, disaster recovery, and regular connector re-validation.

## Definition of done

A workflow is not "covered" merely because a provider is listed. It is covered only when its primary route, fallback or safe-stop route, permission boundaries, representative tests, observability, and recovery behavior have evidence. A workflow can be marked production-ready only after end-to-end tests pass in the target environment.
