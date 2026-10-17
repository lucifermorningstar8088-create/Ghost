# Ghost

Ghost is an AI-powered social media operations platform for YouTube, Facebook, and Instagram. The repository is under active development and is **not production-ready**.

## Run locally on Windows

**Requirements:** Windows 10/11, Python 3.12+, Node.js LTS, and internet access for installation.

1. Download the repository ZIP and extract it.
2. Run `setup.bat` and wait for it to finish.
3. Run `run.bat`.
4. Open the local UI at `http://127.0.0.1:5173`.

API docs: `http://127.0.0.1:8000/docs`

Keep the API and frontend terminal windows open while using Ghost. If startup fails, read the terminal error before retrying.

## Database and secrets

- Without `DATABASE_URL`, the API defaults to local SQLite when started from `apps/api`.
- When `DATABASE_URL` is unset, `setup.bat` applies versioned migrations to local SQLite. If `DATABASE_URL` is set, setup skips remote migrations; back up the target and apply Alembic migrations explicitly after review.
- Never put provider tokens, database passwords, OAuth secrets, or Supabase service-role keys in `VITE_*` variables or commit them to Git.
- The Connection Center credential-storage foundation requires `GHOST_SECRET_ENCRYPTION_KEY`. See the connection guide before configuring it.

## Checks

Frontend:

```powershell
cd apps/web
npm install
npm run typecheck
npm run build
```

API tests:

```powershell
cd apps/api
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m pytest
```

Repository configuration:

```powershell
python -m pip install -r requirements-dev.txt
python scripts/validate_configs.py
```

## Current status

The React/Vite UI and FastAPI backend provide a development foundation. Some screens still use demo data. Full OAuth flows, account/page discovery, several provider adapters, durable settings, worker queues, publishing, and Telegram delivery are not yet fully implemented or verified. A saved credential does not necessarily mean an account is connected.

## Key references

- [Implementation backlog](docs/IMPLEMENTATION-BACKLOG.md)
- [Local PC setup](docs/LOCAL-PC-SETUP.md)
- [Connection Center status and limitations](docs/CHANNEL-PAGES-CONNECTION-CENTER.md)
- [Database and integrations design](docs/CONFIGURABLE-INTEGRATIONS-AND-DATABASE.md)
- [Channel Customization Studio](docs/CHANNEL-CUSTOMIZATION-STUDIO.md)
- [Worker orchestration](docs/WORKER-ORCHESTRATION.md)
- [Community management](docs/COMMUNITY-MANAGEMENT.md)

## Engineering rules

- Verify tests and integrations before claiming they work.
- Protect credentials and isolate tenant data.
- Do not trigger paid services silently.
- Do not promise monetization, virality, or guaranteed revenue.
