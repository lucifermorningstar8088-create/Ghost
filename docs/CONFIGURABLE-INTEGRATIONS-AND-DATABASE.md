# Configurable Database, Providers, Accounts, and Telegram Control Plane

## Status and scope

This document is an implementation contract, not evidence that the runtime/UI already exists. All connections must be created, tested, edited, disabled, and removed through an authenticated UI. Secrets are stored server-side in an encrypted secret store and are never returned to the browser after save.

## 1. Database modes

The setup UI must offer two supported deployment modes:

- **Hosted Supabase:** project URL, public/anon key where required by the client, and server-only service-role key stored as a secret. Server operations must use least privilege and Row Level Security (RLS) where applicable.
- **Local PostgreSQL:** host, port, database, username, password, TLS mode, and optional SSL CA settings. Support localhost/private-network deployment and Docker compose instructions. Never expose the database port to the public internet by default.

### Database requirements

- Use PostgreSQL as the common persistence contract; Supabase is a managed PostgreSQL option, not a separate data model.
- Select the active backend in a first-run setup wizard. Support a connection test, schema/migration status, backup status, and clear error details with secrets redacted.
- Provide versioned SQL migrations, migration locking, rollback/forward-fix guidance, and a pre-migration backup recommendation.
- Switching database targets is an explicit migration workflow: preview row counts, run export/import, validate checksums/counts, verify foreign keys, then require confirmation to cut over. Never silently switch or dual-write.
- Keep a database provider interface so the application does not depend on Supabase-only APIs for core data operations.
- Store connection metadata separately from credentials. Encrypt secrets at rest; use environment/KMS-backed encryption keys, rotate credentials, and redact logs.
- Provide health checks and a backup/restore runbook. A successful connection test does not mean migrations or restore have passed.

## 2. UI-first integration manager

Build an Integrations page with categories, cards, and a common lifecycle:

1. Add provider / connector.
2. Choose provider type and enter required fields.
3. Save credentials securely.
4. Test connection / validate permissions.
5. Show explicit state: `draft`, `configured`, `validated`, `enabled`, `degraded`, or `disabled`.
6. Set priority, allowed use cases, timeout, rate limit, cost ceiling, and fallback behavior.
7. Enable only after validation; show last test, last error (redacted), quota/usage if available, and disable/delete controls.

Support multiple providers per capability. Each provider instance has a unique ID and label, for example "LLM - primary", "LLM - backup", "Image - low cost", "Video - quality". Never assume all providers share the same API format or endpoint. Implement typed adapters and provider-specific validation.

### Required integration categories

- LLM/text generation: OpenAI-compatible and provider-specific APIs; configurable base URL only when explicitly supported.
- Web search/research: search APIs and optional fetch/crawl adapters.
- Image generation/editing.
- Video generation/rendering.
- Text-to-speech, speech-to-text, captions and transcription.
- Storage/assets: local filesystem, S3-compatible object storage, and supported hosted storage.
- Social/platform accounts: YouTube, Facebook, Instagram and future platforms through official OAuth/API scopes.
- Notifications: Telegram bot, with other notification channels optional.
- Developer/infrastructure: GitHub, database, queue, and observability integrations.

A provider's presence in the UI/catalog is not evidence it works. Each adapter must have contract tests for auth, request/response schema, timeout, rate limits, quota exhaustion, malformed output, and provider outage.

## 3. Multi-provider routing and fallback

- Allow one or more configured provider instances per capability.
- Configure per-instance priority, allowed tasks, model/quality settings, timeout, max retries, rate limits, and daily/monthly budget.
- Provide manual selection and optional policy-based routing (availability, quality target, cost ceiling, task type).
- Fallback must be explicit, bounded, observable, and compatible with data/privacy constraints.
- Do not silently make paid calls, exceed configured budgets, or switch to a provider with incompatible retention/data terms.
- Add circuit breakers, idempotency keys, backoff with jitter, and dead-letter/manual-review handling.
- UI must show which provider actually handled each job, including fallback reason and estimated/actual cost when available.

## 4. Channel, page, and account connections

- Connect accounts through an authenticated UI flow. Use OAuth for platforms that support it; never request platform passwords.
- Show connected account identity, platform, scopes/permissions, connection status, expiry/re-auth state, and last successful sync.
- Allow many channels/pages/accounts and bind each content profile to an explicit account/page ID.
- A profile must never inherit another profile's credentials or silently use another account when its binding is missing.
- Separate profile editing permissions from publishing permissions. Publishing requires explicit authorization, an approval gate, idempotency, and remote read-back.
- Include a connection test and a read-only metadata test before enabling write/publish operations.
- Support disconnect/revoke and deletion flows with a clear impact summary.

## 5. Telegram setup and system notifications

Provide a Telegram section in Settings:

- Enter a bot token in a secret field, or use a guided setup that explains how to create a bot with BotFather.
- Save the token server-side only, test bot identity, and allow selecting a destination chat/group after the bot is added and authorized there.
- Verify chat access before enabling notifications. Do not ask the user to publish the token in chat or logs.
- Add configurable event toggles: job queued/started/completed/failed, retries exhausted, provider degraded, quota/budget threshold, approval required, publishing outcome, connection expiry, backup/migration failures, and security alerts.
- Let the user configure quiet hours, severity, digest frequency, and per-channel/project filters.
- Provide a "Send test notification" action and show delivery status. Do not claim delivery until Telegram returns a successful result.
- Notifications contain job IDs, safe summaries, links, and redacted error messages only. Never send API keys, access tokens, private prompts, or sensitive user data by default.
- Add retry with bounded backoff and a dead-letter view for failed notifications. Avoid duplicate alerts through event IDs/idempotency.

## 6. Jobs and operational dashboard

A single UI dashboard must show jobs across all channels/pages and providers: queue state, current stage, selected profile, provider used, progress when known, timestamps, retry count, cost/quota where available, artifacts, and redacted failure reason. Users can filter by account, channel/page, capability, provider, status, and date. Support cancel/retry/resume only when the job type safely supports it.

Telegram is a notification/control surface, not a substitute for authentication and authorization in the web UI. Any Telegram-triggered action must be authenticated, allow-listed, permission-checked, idempotent, and require confirmation for destructive or publishing actions.

## 7. Security and acceptance criteria

- Secrets are encrypted at rest, never returned after save, and redacted from logs/errors.
- All provider, database, Telegram, channel, and page configuration APIs enforce server-side authorization.
- API keys are never stored in localStorage, source control, client bundles, or example fixtures.
- Test mode never publishes content.
- Missing or invalid profile/account/provider bindings fail closed; they never fall back to another channel/account.
- Budget, safety, rights, and platform policies cannot be overridden by prompts or provider settings.
- Integration health is evidence-based: `configured` is not `validated`, and `validated` is not `enabled`.
- Automated tests cover wrong credentials, expired OAuth, timeout, 429/quota, provider outage, fallback, duplicate event delivery, Telegram permission failure, DB unavailable, migration failure, and tenant/profile isolation.

## 8. Delivery order

1. Secrets abstraction and database selection/setup wizard.
2. PostgreSQL migrations and repository/data-access abstraction.
3. Integrations catalog + provider connection CRUD/test endpoints.
4. Multi-provider routing, budgets, retries and audit events.
5. Channel/page account connection UI and explicit profile binding.
6. Telegram setup, test notification, event subscriptions and delivery queue.
7. Unified job/health/usage dashboard.
8. Security, failure-injection, migration, restore and end-to-end tests.

Do not mark a phase complete until executable tests and observed evidence exist.
