# Ghost Consolidated Implementation Backlog

## Current truth

Ghost currently contains a detailed specialist-skill catalogue, a proposed tool coverage registry, and a design contract for channel/page customization. The channel customizer documents and config examples are not a working web UI, persistence layer, or generation runtime. Tool registry entries marked `proposed` are not live integrations. Do not describe these as shipped runtime capabilities until implementation and evidence exist.

## Workstreams

### A. Repository and configuration foundation
- [x] 200 specialist skill specifications across 25 packs.
- [x] Proposed tool capability inventory and fallback policy.
- [x] Channel/page customization product contract.
- [x] JSON Schemas for channel profiles and content-type profiles.
- [x] Example profiles and content-type fixtures.
- [x] Acceptance matrix for customization/isolation.
- [ ] Execute configuration validation in CI and retain a successful run as evidence.
- [ ] Add versioned migration strategy once the actual persistence technology is selected.

### B. Channel Customization Studio
- [x] Specify searchable account selector for authorized connected accounts.
- [x] Specify per-channel profile and per-channel custom content types.
- [x] Specify prompt editor, preview, one-time override, immutable version history, and test generation.
- [x] Specify safety/permission/budget precedence and failure states.
- [ ] Implement authenticated API and tenant-scoped persistence.
- [ ] Implement UI states: loading, empty, disconnected, validation error, unsaved changes, and success/failure.
- [ ] Implement profile CRUD/version/restore and content-type CRUD/duplicate.
- [ ] Implement deterministic prompt package assembly and output schema validation.
- [ ] Implement generation job lifecycle, retries, idempotency, and audit events.
- [ ] Prove cross-account and cross-tenant isolation with executable tests.
- [ ] Integrate model, voice, media, asset, and platform adapters using contracts.
- [ ] Keep publishing disabled until separate authorization, approval, idempotency, and read-back tests pass.

### C. Tool coverage and fallback reliability
- [x] Define proposed primary/fallback/safe-stop routes for critical capabilities.
- [x] Define progressive tool discovery and no-silent-paid-call policy.
- [x] Define secret redaction, least privilege, bounded retries, and idempotency requirements.
- [ ] Implement a runtime tool registry with provider contracts and health states.
- [ ] Add contract tests for authentication, schemas, quotas, timeout, rate-limit, and provider failures.
- [ ] Execute primary/fallback drills and store redacted evidence.
- [ ] Add cost/quota metrics and a tested budget stop.
- [ ] Add durable queue, dead-letter handling, backup restore drills, and observability.
- [ ] Mark each integration status only from observed evidence.

### D. Content production workflow
- [ ] Research/evidence ledger with freshness and source attribution.
- [ ] Rights and asset provenance tracking; block unverified assets.
- [ ] Script/scene/storyboard output contracts and duration checks.
- [ ] Voiceover completeness and scene/narration alignment checks.
- [ ] Captions/transcription confidence gates.
- [ ] Media processing adapter contracts and final-file integrity checks.
- [ ] Human review queue for low-confidence or high-impact output.
- [ ] Exportable draft package for manual publication if official publishing APIs are unavailable.

### E. Platform integration and publishing
- [ ] Connect accounts via OAuth with least-privilege scopes.
- [ ] Read-only account metadata/analytics first; validate freshness and scope.
- [ ] Per-platform capability matrix so unsupported format/settings cannot be silently ignored.
- [ ] Draft generation and explicit approval.
- [ ] Publishing adapter only after official API permissions, platform limits, duplicate prevention, remote read-back, and recovery are tested.
- [ ] Reconciliation for uncertain publish outcomes and expired authorization.

### F. Security, testing, and operations
- [ ] Server-side authorization on every profile, content type, asset, job, and history operation.
- [ ] Secret scanning and dependency/security scanning in CI.
- [ ] Schema, unit, integration, UI, and failure-injection tests.
- [ ] Redacted structured logs, correlation IDs, metrics, and alerting.
- [ ] Data retention/deletion policy and audit log review.
- [ ] Backup restore verification and documented incident recovery.
- [ ] Release gate that blocks deploys when critical tests fail.

## Release gates

1. **Configuration-ready:** schemas and fixtures validate in CI.
2. **API-ready:** authenticated, tenant-scoped endpoints pass authorization tests.
3. **UI-ready:** channel switching, prompt editing, preview, versioning, and error states pass browser tests.
4. **Generation-ready:** prompt precedence, output contract, quality gates, budgets, and failure recovery pass tests.
5. **Publishing-ready:** explicit authorization, approval, official API contract, idempotency, remote read-back, and recovery all pass in a test environment.
6. **Production-ready:** monitoring, cost limits, backup restore, security review, and rollout/rollback are demonstrated.

Passing an earlier gate does not imply that later gates have passed.
