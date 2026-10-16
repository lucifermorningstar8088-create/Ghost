# Ghost Consolidated Implementation Backlog

## Current truth

Ghost contains specialist-skill specifications, a proposed tool coverage registry, and design contracts for channel/page customization and configurable integrations. These documents and schemas are not a working web UI, persistence layer, or generation runtime. Tool registry entries marked `proposed` are not live integrations. Do not describe these as shipped runtime capabilities until implementation and evidence exist.

## Workstreams

### A. Repository and configuration foundation
- [x] 200 specialist skill specifications across 25 packs.
- [x] Proposed tool capability inventory and fallback policy.
- [x] Channel/page customization product contract.
- [x] JSON Schemas for channel profiles and content-type profiles.
- [x] Example profiles and content-type fixtures.
- [x] Acceptance matrix for customization/isolation.
- [x] Configuration validation workflow and CI evidence previously observed.
- [x] Configurable database, integrations, multi-provider, account-connection, and Telegram design contract.
- [x] Non-secret integration profile schema.
- [ ] Add versioned SQL migrations and data-access/repository interfaces.
- [ ] Implement secret storage/encryption abstraction and rotation.

### B. Database setup and portability
- [ ] First-run UI supports hosted Supabase and local PostgreSQL.
- [ ] Connection test, migration status, health state, and redacted errors.
- [ ] PostgreSQL-first data access layer that avoids Supabase-only assumptions for core persistence.
- [ ] Versioned migrations, migration lock, safe forward-fix/rollback guidance.
- [ ] Explicit export/import/cutover workflow for changing database target; no silent switching or unverified dual writes.
- [ ] Backup and restore procedures with a successful restore test.
- [ ] Tests for unavailable database, invalid credentials, migration failure, and data integrity.

### C. Channel Customization Studio and account connections
- [x] Specify searchable account selector, independent channel/page profiles, custom prompts, content types, version history, restore, and test generation.
- [ ] Implement authenticated UI and tenant-scoped persistence.
- [ ] Implement channel/page/account OAuth connection flows and connection status/expiry.
- [ ] Bind every profile to an explicit platform account/page ID.
- [ ] Implement profile/content-type CRUD, version/restore, prompt assembly, and output validation.
- [ ] Prove cross-account and cross-tenant isolation with executable tests.
- [ ] Keep publishing disabled until explicit authorization, approval, idempotency, and remote read-back pass.

### D. Integrations and multi-provider routing
- [x] Define UI-first integration manager and integration profile schema.
- [ ] Implement add/edit/test/enable/disable/delete provider flows.
- [ ] Support multiple configured providers for LLM, web search, image generation, video generation, TTS, STT, storage, social platforms, Telegram, GitHub, database, and observability.
- [ ] Implement typed provider adapters; do not assume all APIs are interchangeable.
- [ ] Implement primary/fallback selection, per-provider task allowlists, health checks, quotas, rate limits, timeouts, bounded retries, circuit breakers, and idempotency.
- [ ] Store credentials server-side in an encrypted secret store; never expose saved secrets to the browser or logs.
- [ ] Add contract tests for auth, request/response schemas, timeout, rate limits, quota exhaustion, malformed responses, and outages.
- [ ] Add cost/quota tracking and a tested budget stop; never make silent paid calls.
- [ ] Record which provider actually handled each job and why fallback occurred.

### E. Telegram notifications and operations UI
- [ ] Implement Telegram bot setup and secure token storage in Settings.
- [ ] Validate bot identity and destination chat/group permissions before enabling.
- [ ] Add UI event toggles, severity filters, quiet hours, digests, and per-channel filters.
- [ ] Send test notification and report actual delivery result.
- [ ] Add durable notification queue, bounded retries, event idempotency, and dead-letter view.
- [ ] Notify on job lifecycle, exhausted retries, provider degradation, budget/quota thresholds, approval requests, connection expiry, migration/backup failures, and security alerts.
- [ ] Redact credentials and sensitive data from Telegram messages.
- [ ] Implement unified jobs, integration health, cost/quota, and audit dashboard.
- [ ] Telegram-triggered actions must be authenticated, allow-listed, permission-checked, and confirmed for destructive/publishing operations.

### F. Runtime and content production
- [ ] Implement a runtime tool registry with provider contracts and evidence-based health states.
- [ ] Implement planning/execution workflow, durable queue, checkpoints, cancellation, retry/resume where safe, and dead-letter/manual review.
- [ ] Research/evidence ledger with freshness and source attribution.
- [ ] Rights and asset provenance tracking; block unverified assets.
- [ ] Script/scene/storyboard output contracts and duration checks.
- [ ] Voiceover completeness and scene/narration alignment checks.
- [ ] Captions/transcription confidence gates and media integrity checks.
- [ ] Human review queue and exportable draft package.

### G. Security, testing, and deployment
- [ ] Server-side authorization on every profile, content type, asset, job, integration, account, secret, and history operation.
- [ ] Secret scanning and dependency/security scanning in CI.
- [ ] Schema, unit, integration, UI, end-to-end, and failure-injection tests.
- [ ] Redacted structured logs, correlation IDs, metrics, and alerts.
- [ ] Data retention/deletion policy and audit-log review.
- [ ] Backup restore verification and incident recovery runbook.
- [ ] Release gate blocks deploys when critical tests fail.

## Release gates

1. **Configuration-ready:** schemas and fixtures validate in CI.
2. **Database-ready:** both selected database modes pass connection, migration, persistence, and recovery tests.
3. **API-ready:** authenticated, tenant-scoped endpoints pass authorization tests.
4. **UI-ready:** channel switching, prompt editing, integrations setup, provider testing, Telegram settings, and error states pass browser tests.
5. **Generation-ready:** provider routing, output contracts, quality gates, budgets, and failure recovery pass tests.
6. **Operations-ready:** Telegram delivery, jobs dashboard, observability, and alert retry/dead-letter behavior are verified.
7. **Publishing-ready:** explicit authorization, approval, official API contract, idempotency, remote read-back, and recovery pass in a test environment.
8. **Production-ready:** monitoring, cost limits, backup restore, security review, and rollout/rollback are demonstrated.

Passing an earlier gate does not imply that later gates have passed.
