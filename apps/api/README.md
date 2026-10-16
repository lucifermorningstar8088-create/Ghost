# Ghost API

Minimal FastAPI foundation for the Ghost platform.

## Local development

Python 3.12 is recommended.

```bash
cd apps/api
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate
python -m pip install -r requirements.txt
uvicorn app.main:app --reload
```

Endpoints:

- `GET /health/live`: confirms the API process responds.
- `GET /health/ready`: reports API and integration configuration status.
- `GET /docs`: interactive OpenAPI documentation for local development.

Run tests and validate the schema migration without a database:

```bash
python -m pytest -q
alembic upgrade head --sql
```

Apply migrations to a configured development or production database only after reviewing the SQL:

```bash
# Set DATABASE_URL in the backend environment; do not commit credentials.
alembic upgrade head
```

See [migrations/README.md](migrations/README.md) for migration workflow.

## Honest status boundary

This is an API foundation, not a production-ready backend. The readiness response explicitly marks the database, social platforms, provider adapters, and Telegram as `not_configured` until configured. No social action is performed. Alembic now tracks the channel-profile schema, but migrations do not provision a database or verify a live PostgreSQL/Supabase connection. Authentication, authorization, tenant identity enforcement, secret management, rate limiting, and real adapters must be implemented and tested before deployment for real users.
