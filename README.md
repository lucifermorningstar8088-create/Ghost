# Ghost

AI-assisted social media operations platform. **Development prototype; not production-ready.**

## Features and status

- React/Vite operations-center UI and FastAPI backend.
- Windows setup/run scripts: `setup.bat` and `run.bat`.
- Configuration schemas, validation, and implementation specifications.
- Channel connection API foundation with server-side encrypted credential storage.
- Telegram and X credential verification adapters; other platform integrations are not yet fully implemented.

The UI still contains demo data. Full OAuth flows, account/page discovery, publishing, worker queues, Telegram delivery, and persistent settings across all screens remain incomplete. Saving credentials does not mean an account is connected.

## Run on Windows 10/11

Requirements: Python 3.12+, Node.js LTS, and internet for initial dependency installation.

1. Download the repository ZIP and extract it to a writable folder.
2. Run `setup.bat`.
3. Run `run.bat`.
4. Open:
   - UI: http://127.0.0.1:5173
   - API docs: http://127.0.0.1:8000/docs
   - API health: http://127.0.0.1:8000/health/ready

Keep both service terminals open while using the app. For manual setup or troubleshooting, see [Local PC Setup](docs/LOCAL-PC-SETUP.md).

## Database and secrets

- Default database: SQLite when `DATABASE_URL` is unset.
- PostgreSQL requires a configured server and a valid server-side `DATABASE_URL`.
- A UI-based SQLite/Supabase/PostgreSQL selector and database migration workflow are **not yet implemented**.
- Connection credential encryption requires server-side `GHOST_SECRET_ENCRYPTION_KEY` (Fernet key).
- Never commit secrets or put provider tokens, database passwords, or service-role keys in `VITE_*` variables.

Check migration status at `/health/migrations`. This endpoint is read-only; it does not apply migrations. Back up data and review migrations before applying schema changes.

## Development checks

Frontend:

```powershell
cd apps/web
npm install
npm run typecheck
npm run build
```

API:

```powershell
cd apps/api
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m pytest
```

Repository configuration:

```powershell
python -m pip install -r requirements-dev.txt
python scripts/validate_configs.py
```

Run checks before claiming a change passes. A running page alone does not verify external integrations.

## Key references

- [Implementation backlog](docs/IMPLEMENTATION-BACKLOG.md)
- [Connection Center status and API](docs/CHANNEL-PAGES-CONNECTION-CENTER.md)
- [Database and integrations design](docs/CONFIGURABLE-INTEGRATIONS-AND-DATABASE.md)
- [Windows setup guide](docs/LOCAL-PC-SETUP.md)

## Engineering rules

Secure secrets, isolate accounts, use least privilege, respect platform terms and consent, and never silently trigger paid services. No guarantee of virality, monetization approval, or revenue.
