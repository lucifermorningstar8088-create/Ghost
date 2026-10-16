# Ghost

Ghost is an AI-powered social media growth and revenue operations platform in planning for YouTube, Facebook, and Instagram.

## Skill library

The repository contains a planned library of **200 specialist skill specifications**, organized as 25 domain packs under [skills/packs](skills/packs/) and indexed in [CATALOG.md](CATALOG.md).

## Channel Customization Studio

- [Studio specification](docs/CHANNEL-CUSTOMIZATION-STUDIO.md) defines channel/page selection, independent profiles, custom prompts, content-type builder, prompt preview, version history, test generation, job lifecycle, access control, and delivery phases.
- [Channel profile JSON Schema](config/channel-profile.schema.json) and [content-type JSON Schema](config/content-type.schema.json) define configuration contracts.
- [Example profiles](config/channel-profiles.example.yaml) and [content types](config/content-types.example.yaml) are fixtures, not connected accounts or active production settings.
- [Acceptance matrix](tests/CHANNEL-CUSTOMIZATION-ACCEPTANCE.md) defines isolation, authorization, versioning, prompt precedence, failure, and publishing-boundary tests.

## Configurable database, APIs, providers, and Telegram

- [Database and integration control-plane specification](docs/CONFIGURABLE-INTEGRATIONS-AND-DATABASE.md) defines the UI-first setup for **hosted Supabase or local PostgreSQL**, provider connections, multiple providers per capability, account/page binding, and Telegram job notifications.
- [Integration profile schema](config/integration-profile.schema.json) defines non-secret provider metadata. Actual credentials must live in server-side encrypted secret storage, never in source control or browser storage.
- Planned provider categories include LLM/text, web search, image generation, video generation, TTS, STT, storage, social platforms, Telegram, GitHub, database, and observability. Multiple instances per category are required, with explicit health, budget, priority, and fallback controls.
- Telegram is intended for configurable notifications and a limited secure control surface; it is not a replacement for web-app authorization.
- These are design contracts and schemas, **not proof that the UI, database adapters, provider integrations, or Telegram bot are implemented or connected**.

## Configuration validation and implementation backlog

- [Consolidated implementation backlog](docs/IMPLEMENTATION-BACKLOG.md) separates completed specifications from remaining API, UI, runtime, integration, testing, and publishing work.
- [Configuration validation script](scripts/validate_configs.py) checks JSON Schemas, example YAML fixtures, cross-references, and the proposed tool registry.
- [Development validation dependencies](requirements-dev.txt) and [GitHub Actions workflow](.github/workflows/validate-configs.yml) run checks on pull requests and pushes.

## Tool coverage and reliability

- [Tool coverage and fallback standard](docs/TOOL-COVERAGE-AND-FALLBACK.md) defines critical capabilities, primary/fallback/safe-stop routes, security, and readiness gates.
- [Machine-readable tool inventory](config/tools.yaml) lists proposed capability routes. A proposed record is not proof of a live integration.

## Engineering standards

- Evidence before claims; distinguish measured results from estimates.
- Account isolation, least privilege, secure secrets, platform terms, and user consent.
- Free-first resource policy; never silently trigger paid services.
- Independent quality gates, bounded retries, auditable changes, and human escalation for unresolved high-risk actions.
- No promises of virality, monetization approval, or guaranteed revenue.
- Progressive tool discovery: load only the tools needed for a task rather than flooding every model call with every schema.

**Important:** skill, tool, and customization files currently define specifications and examples, not a fully implemented runtime or UI. Database migrations, runtime adapters, platform permissions, executable automated tests, fallback drills, and benchmarks must be implemented and verified before production claims.


## Ghost Operations Center UI

The MagicPath-generated React/TypeScript UI is stored in `apps/web/src/components/ghost-operations-center/`. It includes nine screens for overview, live jobs, workers, community moderation/reply drafts, channel/profile setup, integrations, database selection, Telegram notifications and settings. The onboarding wizard supports YouTube, Facebook and Instagram profile drafts with independent niche, audience, language, format, brand voice, schedule, timezone and custom prompt settings.

### UI integration status

This component is a front-end prototype. Seed jobs, provider health, worker status and comments are demo data. The UI does not claim that accounts are OAuth-connected, providers are live, Telegram alerts are delivered, or settings are persisted. Backend API, secure secret storage, database migrations, OAuth callbacks, job events and real provider adapters remain separate implementation tasks. The current repository is specification-first and does not yet contain a complete web application scaffold.
