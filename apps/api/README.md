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

Run tests:

```bash
python -m pytest -q
```

## Honest status boundary

This is an initial API foundation, not a production-ready backend. The readiness response explicitly marks the database, social platforms, provider adapters, and Telegram as `not_configured`. No credentials are accepted or stored here, and no social action is performed. Authentication, authorization, persistence, migrations, secret management, rate limiting, and real adapters must be implemented and tested before deployment for real users.
