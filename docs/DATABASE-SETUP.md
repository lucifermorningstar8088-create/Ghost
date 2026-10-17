# Database setup: Supabase or PostgreSQL

Ghost supports PostgreSQL through SQLAlchemy. Supabase is a hosted PostgreSQL option; its Auth/JWT configuration is separate from the database connection.

## 1. Choose a database

### Supabase
1. Create a project in Supabase.
2. Open the project's **Connect** panel and copy the PostgreSQL connection URI appropriate for your runtime. A pooler URI is usually the easiest choice for hosted/serverless environments; use the URI and port recommended by Supabase for your selected mode.
3. Ensure the database password is set and URL-encode special characters in URI credentials when necessary.

### Your own PostgreSQL
1. Create a database and a dedicated application role.
2. Grant only the permissions the app needs, including migration permissions during deployment if migrations run with this role.
3. Ensure the API host can reach the database and configure TLS for remote connections.

## 2. Add backend environment variables

Set these in the backend runtime's secret/environment settings, not in the frontend, source control, or chat:

- `DATABASE_URL`: SQLAlchemy URI, for example `postgresql+psycopg://USER:PASSWORD@HOST:5432/DATABASE`
- `SUPABASE_URL`: only required for Supabase Auth JWT verification.
- `SUPABASE_JWT_AUDIENCE`: normally `authenticated`.
- `GHOST_CORS_ORIGINS`: comma-separated exact origins of the web app, for example `https://your-ghost-web.example`.

Do not put database credentials, Supabase service-role keys, or other secrets into `VITE_*` variables. The browser must never connect directly to PostgreSQL.

## 3. Frontend API URL

Set `VITE_GHOST_API_URL` in the web app build environment to the API origin, without a trailing path, for example `https://your-ghost-api.example`. When developing locally, the UI defaults to `http://localhost:8000`.

## 4. Deploy and migrate

1. Deploy/restart the API after setting environment variables.
2. Run database migrations from the API project directory using the project's Alembic configuration, following the repository's migration workflow. Review migrations before applying them to a database containing important data.
3. Open the Ghost **Database** screen and press **Check live backend status**.
4. A response of `checks.database: "ok"` confirms the API could execute `SELECT 1` against the configured database. `not_configured` means `DATABASE_URL` is missing. `unavailable` means the API could not connect or execute the check.
5. Other integrations can still show `not_configured`; database health does not imply social accounts, AI providers, or Telegram are connected.

## Important boundaries

- The UI deliberately does not accept or persist database passwords. The first connection is configured by the operator in the backend host's environment.
- Supabase project URL / anon key are not PostgreSQL credentials. The PostgreSQL URI is used by the backend.
- Switching database targets does not automatically copy data. Back up and perform an explicit migration/cutover.
- The health endpoint reports status, not credentials or connection strings.


## 5. Verify authenticated profile API

Before connecting the Channels & Profiles screen to the live API, verify the API independently:

1. Configure and verify the database as above, then apply Alembic migrations.
2. Configure the backend-only Supabase Auth settings described in [API authentication](../apps/api/docs/AUTHENTICATION.md).
3. Ensure the authenticated test user has a trusted server-assigned `app_metadata.tenant_id`. Do not assign tenant membership from browser-provided metadata.
4. Obtain a valid access token through your configured Supabase sign-in flow and send it as `Authorization: Bearer <access-token>` to `/api/v1/profiles`.
5. Test create/list/read/update/delete with a non-production test profile. Verify that a second tenant cannot read or mutate it.
6. Keep access tokens in memory or an approved secure auth flow. Never commit tokens, database URIs, or service-role keys.

The current web canvas still uses local preview state for channel profiles; the backend API is implemented separately and the live OAuth/account authorization flow is not yet connected. A successful database readiness check alone does not mean profile UI persistence or social-platform publishing is live.
