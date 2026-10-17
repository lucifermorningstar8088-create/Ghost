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

## Concurrent workers and community management

- [Worker orchestration specification](docs/WORKER-ORCHESTRATION.md) defines parallel jobs, dependency graphs, durable queues, capacity/rate limits, retries, checkpoints, cancellation, dead-letter handling, and worker safety boundaries.
- [Community management specification](docs/COMMUNITY-MANAGEMENT.md) defines authorized multi-platform inboxes, comment classification, context-aware natural replies, factual verification, human escalation, controlled low-risk auto-send, and remote read-back.
- [Worker/community acceptance matrix](tests/WORKER-COMMUNITY-ACCEPTANCE.md) lists required concurrency, recovery, account-isolation, reply-quality, moderation, and duplicate-send tests. These are acceptance requirements, not passed test results.

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

This component is a front-end prototype. Seed jobs, provider health, worker status and comments are demo data. The UI does not claim that accounts are OAuth-connected, providers are live, Telegram alerts are delivered, or settings are persisted. The connection center now has an authenticated backend API and encrypted credential storage foundation. Full OAuth callbacks, account/page discovery, job events and remaining provider adapters are still separate implementation tasks. The repository contains a runnable React/Vite frontend shell and a FastAPI backend scaffold, but many operations-center panels still use demo data and the platform is not production-ready.

## Channel & Pages Connection Center API

The backend connection foundation supports tenant-scoped records for YouTube, Facebook Pages, Instagram, TikTok, X, Telegram and generic integrations. Credentials are encrypted server-side and never returned by the API. Configure `GHOST_SECRET_ENCRYPTION_KEY` using a generated Fernet key before saving credentials. See [Connection Center implementation status](docs/CHANNEL-PAGES-CONNECTION-CENTER.md) for API endpoints and provider limitations. Telegram and X have live verification adapters; other platforms remain explicitly unverified until their OAuth/discovery adapters are implemented. Saving credentials does not mean an account is connected.

See [Connection Center setup, API endpoints, and known limitations](docs/CHANNEL-PAGES-CONNECTION-CENTER.md).

## Run the web UI locally

The React/Vite shell mounts the Ghost Operations Center prototype. From the repository root:

```bash
cd apps/web
npm install
npm run dev
```

Open the local URL printed by Vite (normally `http://localhost:5173`). To validate a production build:

```bash
npm run typecheck
npm run build
npm run preview
```

Copy `apps/web/.env.example` to `.env.local` only if you need to set a public API base URL. Never place provider secrets, Supabase service-role keys, OAuth client secrets, database passwords, or Telegram tokens in `VITE_*` variables.

**Runtime boundary:** this makes the frontend shell runnable, not the platform production-ready. The current operations center uses seeded demo data and local component state. Login/OAuth, durable persistence, real provider health, worker queues/events, actual publishing, and Telegram delivery remain unimplemented until backend services are added and verified.

## Install Ghost on Windows 10/11

Use this path to run the current repository locally on your own PC. This is a developer setup, not a one-click production installer.

### Prerequisites

- Windows 10/11, 64-bit
- Python 3.12 or newer on PATH
- Node.js LTS (npm is included)
- Internet access for the first dependency install
- PowerShell

Git is optional if you download the repository as a ZIP. No cloud API keys, Docker, Supabase, or PostgreSQL server are required for the default local SQLite health-check setup.

### Option A: one-click Windows launchers (recommended)

1. Open the repository page and choose **Code → Download ZIP**.
2. Extract the ZIP to a normal writable folder, for example `C:\\Projects\\Ghost`.
3. Open the extracted `Ghost` folder.
4. Double-click **`setup.bat`** and wait for dependency installation and validation to finish.
5. Double-click **`run.bat`** to start the API and web UI.

The root batch files delegate reusable work to `scripts/windows/`. Keep `setup.bat`, `run.bat`, those PowerShell scripts, this README, and relevant tests synchronized whenever runtime requirements change. If startup fails, read the error in the service terminal before retrying.

The API and frontend run in separate terminal windows. Keep them open while using Ghost. Close the service windows to stop the local development servers.

### Option B: PowerShell scripts

From the repository root, run setup:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\\scripts\\windows\\setup-ghost.ps1
```

Then start the services:

```powershell
.\\scripts\\windows\\run-ghost.ps1
```

### Local addresses

| Purpose | Address |
| --- | --- |
| Web UI | http://127.0.0.1:5173 |
| API interactive docs | http://127.0.0.1:8000/docs |
| Liveness check | http://127.0.0.1:8000/health/live |
| Readiness / database connectivity | http://127.0.0.1:8000/health/ready |
| Migration status (read-only) | http://127.0.0.1:8000/health/migrations |

Use `127.0.0.1` on the same PC. These development servers are not intended to be exposed directly to the public internet.

### Option B: run each service manually

Open two terminals at the repository root.

Terminal 1, API:

```powershell
cd apps/api
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
$env:PYTHONPATH = "."
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Terminal 2, frontend:

```powershell
cd apps/web
npm install
Copy-Item .env.example .env.local -ErrorAction SilentlyContinue
npm run dev -- --host 127.0.0.1
```

### Database behavior and migrations

- If the API process has no `DATABASE_URL`, the current database helper defaults to local SQLite at `apps/api/ghost.db` when started from `apps/api`.
- The setup script does not automatically apply database migrations or reset data.
- Open `/health/migrations` to inspect migration status. This endpoint is read-only; it does not create or upgrade tables.
- Do not paste the PostgreSQL example URL from `apps/api/.env.example` unless you have configured a matching PostgreSQL server and credentials.
- Before running any migration command, review the migration files and back up any database you care about.

### Frontend environment configuration

`apps/web/.env.example` contains public Vite configuration such as `VITE_GHOST_API_URL`. Copy it to `apps/web/.env.local` if needed and set the API base URL to `http://127.0.0.1:8000`.

**Never put a Supabase service-role key, provider API secret, database password, OAuth client secret, or Telegram bot token in a `VITE_*` variable.** Vite variables are shipped to the browser. Server-side secrets must stay in server-side environment/configuration and must not be committed to Git.

## Day-to-day development operations

### Run frontend checks

```powershell
cd apps/web
npm run typecheck
npm run build
```

### Run API tests

```powershell
cd apps/api
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m pytest
```

### Validate repository configuration

From the repository root, install the development requirements if needed, then run:

```powershell
python -m pip install -r requirements-dev.txt
python scripts/validate_configs.py
```

### One-command local test runner (Windows)

After running `scripts/windows/run-ghost.ps1` and confirming the API is running, open a new PowerShell window at the repository root and run:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\scripts\windows\test-ghost.ps1
```

The test runner checks API liveness, database readiness, and migration status, then runs API tests, frontend typecheck, and a production build. It does **not** apply migrations. If the database is not ready, a health endpoint is unavailable, or a test/build fails, it stops and prints an error to investigate.

To run health checks and API tests without frontend typecheck/build:

```powershell
.\scripts\windows\test-ghost.ps1 -SkipBuild
```

### Basic smoke-test checklist

1. Confirm the API liveness endpoint responds.
2. Confirm the readiness endpoint reports database connectivity; if not, inspect the API terminal and effective database configuration.
3. Inspect migration status. A `not_initialized` or `pending` state means database migrations still need deliberate review and setup.
4. Open the UI and test navigation, forms and screen layout.
5. Run frontend typecheck/build and API tests before submitting code changes.
6. Check the API and frontend terminals for errors; do not treat a page rendering as proof that external integrations are connected.

## Troubleshooting

- **`python` not found:** install Python 3.12+ and enable the installer option to add Python to PATH, then reopen PowerShell.
- **`npm` not found:** install Node.js LTS, then reopen PowerShell and verify `node --version` and `npm --version`.
- **PowerShell says scripts are disabled:** run `Set-ExecutionPolicy -Scope Process Bypass` in that terminal only, then retry the setup script.
- **Port 8000 or 5173 is already in use:** stop the other process using that port before starting Ghost. The Vite dev server is configured to require its expected port.
- **Frontend opens but API calls fail:** verify the API terminal is running, check `VITE_GHOST_API_URL` in `.env.local`, then restart Vite after changing environment variables.
- **Readiness fails:** check the API terminal and database URL. With the local default, start the API from `apps/api` so the SQLite file is created in the expected working directory.
- **Migration status is not up to date:** the status endpoint only reports state. Review migrations and back up data before applying any schema change.
- **Profile endpoints return 401/403:** authenticated profile operations require correctly configured Supabase JWT verification and tenant metadata; local startup alone does not bypass authentication.
- **Dependency installation fails:** check internet access and supported Python/Node versions, then rerun the failed install command and keep the full error output for debugging.

## What is operational today, and what is not

**Runnable locally:** the React/Vite shell, FastAPI service, health endpoints, database connectivity check, migration-status inspection, configuration validation, and automated checks that pass in CI.

**Still incomplete or requires external setup:** real login/OAuth connections, durable settings for every screen, live provider health, actual worker queues/events, social publishing, Telegram delivery, and production-grade secret storage. Seeded jobs, worker/provider status, and community comments shown in the operations center are demo data. The profile API is tenant-scoped and requires valid authentication configuration.

Do not use the current UI as proof that a social account is connected or that a post/message was actually published or delivered. Enable external integrations only after their credentials, permissions, failure handling, and tests have been implemented and verified.

## Further implementation references

- [Windows local setup guide](docs/LOCAL-PC-SETUP.md)
- [Implementation backlog](docs/IMPLEMENTATION-BACKLOG.md)
- [Database and integration control-plane specification](docs/CONFIGURABLE-INTEGRATIONS-AND-DATABASE.md)
- [Worker orchestration specification](docs/WORKER-ORCHESTRATION.md)
- [Community management specification](docs/COMMUNITY-MANAGEMENT.md)
