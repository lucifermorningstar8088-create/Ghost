# Database setup: local SQL, PostgreSQL, or hosted Supabase

Ghost must support three database modes without forcing a hosted database:

- **Local mode:** on a PC, generate and use a local SQLite database by default for easy first-run/offline development.
- **Self-managed PostgreSQL:** connect to a PostgreSQL instance the operator controls, local or remote.
- **Hosted mode:** connect to Supabase PostgreSQL when Ghost runs in an online/hosted environment.

Supabase is optional, not a requirement for the local PC installation. Supabase Auth/JWT verification is a separate concern from the database engine. A local installation may use its configured authentication mode; never bypass authentication for a remotely exposed API.

## 1. Local PC mode

1. Install Ghost's API dependencies from `apps/api/requirements.txt`.
2. If `DATABASE_URL` is unset, local development may use a SQLite file such as `sqlite+pysqlite:///./ghost.db` stored under the API data directory.
3. Generate schema changes as reviewed, version-controlled Alembic migration files. Do not generate or apply arbitrary SQL from an untrusted prompt.
4. Start the API and verify `/health/ready` before using persistent features.
5. Back up the local database file before upgrades or migration experiments.

SQLite is suitable for a single-PC setup and lightweight development. Choose PostgreSQL when concurrent writes, multiple workers, remote access, or production operations require it.

## 2. Connect self-managed PostgreSQL

1. Install PostgreSQL locally or provision a server the operator controls.
2. Create a dedicated database and least-privilege application role.
3. Configure the API's server-side `DATABASE_URL`, for example:

   `postgresql+psycopg://USER:PASSWORD@HOST:5432/DATABASE`

4. URL-encode reserved characters in credentials. For remote connections, require TLS and restrict network access.
5. Run reviewed Alembic migrations, then verify database readiness and a non-production CRUD test.
6. Keep the URI in the OS environment or secret manager, never in frontend variables, source control, logs, or chat.

## 3. Hosted Supabase mode

1. Create/select a Supabase project and copy the PostgreSQL URI from its Connect panel for the chosen runtime/networking mode.
2. Set `DATABASE_URL` only in the backend host's secret/environment settings.
3. Set `SUPABASE_URL` and the appropriate JWT settings only when using Supabase Auth for API authentication.
4. Apply reviewed Alembic migrations and verify the backend's live database readiness check.

Supabase is an online deployment option, not a prerequisite for running Ghost locally. Do not place a Supabase service-role key or database password in `VITE_*` variables. The browser talks to Ghost's API, not directly to PostgreSQL.

## 4. Database selection and SQL generation

The Database settings UI should expose an explicit mode selector: **Local SQLite**, **Self-managed PostgreSQL**, or **Hosted Supabase PostgreSQL**. Show safe status, migration version, and redacted connection errors.

For local mode, Ghost may create its local database file and run the application's reviewed migrations automatically on first startup. For PostgreSQL/Supabase mode, require an explicit connection test and migration confirmation before schema changes. Never silently switch databases or perform dual writes.

If Ghost includes a "Generate SQL" helper, it must create a proposed, versioned migration file for review, not execute arbitrary generated SQL directly. Validate migration syntax, target database dialect, destructive operations, and expected schema diff; show the diff and require confirmation before applying. Keep rollback/forward-fix instructions and a backup step for existing data.

## 5. API environment and health checks

Backend environment variables:

- `DATABASE_URL`: selected database connection URI.
- `SUPABASE_URL`: only when Supabase Auth JWT verification is used.
- `SUPABASE_JWT_AUDIENCE`: normally `authenticated` for Supabase Auth.
- `GHOST_CORS_ORIGINS`: exact web-app origins, comma-separated.

Set `VITE_GHOST_API_URL` in the web app build environment to the API origin. For local development, it can point to `http://localhost:8000`.

The Ghost Database screen's live backend check should report:

- `ok`: API can execute a simple database query.
- `not_configured`: no database URL or local mode is configured.
- `unavailable`: the connection/query failed.

A successful health check does not prove OAuth, AI providers, Telegram, or publishing are connected.

## 6. Migration and data safety

- Use Alembic as the source of truth for versioned schema changes.
- Test migrations against disposable SQLite and PostgreSQL databases in CI where supported.
- Back up before production migrations and verify restore procedures.
- Changing the database target does not copy existing data; use an explicit export/import/cutover workflow.
- Do not log credentials or expose connection strings in health responses.
- A local PC can operate without Supabase; cloud deployments can use Supabase or self-managed PostgreSQL.

## 7. Verify the authenticated profile API

1. Configure the chosen database and apply migrations.
2. Configure the appropriate server-side auth mode.
3. Ensure tenant identity is assigned by trusted server-side claims, never browser-provided tenant IDs.
4. Test profile create/list/read/update/delete with a non-production profile.
5. Verify a second tenant cannot read or mutate the first tenant's profile.

The profile API is implemented separately from remaining channel OAuth/publishing work. Database connectivity alone does not imply social account authorization or publishing is live.
