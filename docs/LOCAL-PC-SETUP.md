# Run Ghost on a Windows PC

This guide runs the current Ghost web app and API locally so you can test backend endpoints on your own PC. It does **not** turn every Operations Center panel into a production integration: worker jobs, provider health, social OAuth/publishing, Telegram delivery, and several settings remain demo/preview behavior.

## Requirements

- Windows 10/11, 64-bit
- Python 3.12 or newer, with Python added to PATH
- Node.js LTS (npm included)
- Internet for the first dependency installation
- Git if cloning the repository

No Docker, Supabase project, API provider key, or PostgreSQL server is required for the local SQLite default.

## One-time setup

1. Download/clone the repository and open PowerShell in its root folder.
2. If Windows blocks local scripts, run this for the current PowerShell process only:

   ~~~powershell
   Set-ExecutionPolicy -Scope Process Bypass
   ~~~

3. Install the dependencies:

   ~~~powershell
   .\scripts\windows\setup-ghost.ps1
   ~~~

The setup creates apps/api/.venv, installs the API requirements, applies Alembic migrations to the local SQLite database when `DATABASE_URL` is unset, installs web packages, and creates apps/web/.env.local from the example if missing. It does not overwrite an existing local env file or add cloud credentials. If `DATABASE_URL` is set, setup deliberately skips migrations for that configured database; back it up and apply migrations explicitly after reviewing the target.

## Start the app

From the repository root:

~~~powershell
.\scripts\windows\run-ghost.ps1
~~~

It opens separate PowerShell windows for the API and web dev server.

- Web UI: http://127.0.0.1:5173
- API docs: http://127.0.0.1:8000/docs
- Liveness: http://127.0.0.1:8000/health/live
- Readiness: http://127.0.0.1:8000/health/ready
- Migration status: http://127.0.0.1:8000/health/migrations

## What to test first

1. Open liveness. Expected: JSON with status "ok".
2. Open readiness. With local SQLite available, checks.database should be "ok". Overall readiness can be "degraded" because external integrations are not configured.
3. Open migration status. It reports the current Alembic revision and head without applying any migration.
4. Open Swagger docs. Profile routes require a valid Supabase access token and tenant metadata, so they will not accept anonymous requests. Configure Supabase Auth only if you want to test authenticated profile CRUD.
5. Explore the UI, but treat seeded jobs, worker health, comments, provider statuses and preview-only settings as sample data, not live integrations.

## Database and data

- Without DATABASE_URL, the API defaults to sqlite+pysqlite:///./ghost.db. The runner sets the working directory to apps/api, so the database file is apps/api/ghost.db.
- Back up apps/api/ghost.db if you create local data there.
- Migration status is read-only. This setup script intentionally does not run alembic upgrade head automatically.
- Never put database passwords, Supabase service-role keys, OAuth secrets, or Telegram bot tokens into frontend VITE_* variables or commit them to Git.

## Stop and troubleshoot

- Stop each service with Ctrl+C in its PowerShell window.
- If port 8000 or 5173 is already in use, stop the other process or change the port consistently in the script/config.
- If Python/Node is not recognized, install it and reopen PowerShell.
- If npm install fails, check internet access and Node.js LTS.
- If API imports fail, rerun setup and check that the API terminal's current directory is apps/api.

## Validation commands

~~~powershell
cd apps/api
.\.venv\Scripts\python.exe -m pytest
~~~

~~~powershell
cd apps/web
npm run typecheck
npm run build
~~~

Passing these local checks verifies the tested code/build only. It does not prove that external providers, OAuth, publishing, Telegram, or production deployment are connected.
