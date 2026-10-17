"""Truthful health and dependency-readiness endpoints for the Ghost API."""
import os
from pathlib import Path

from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from .database import build_engine
from .profile_routes import router as profile_router

app = FastAPI(
    title="Ghost API",
    description="Backend foundation for Ghost social media operations.",
    version="0.1.0",
)
app.include_router(profile_router)

# Keep browser access explicit and configurable. Add the deployed web origin to GHOST_CORS_ORIGINS.
_allowed_origins = [origin.strip() for origin in os.getenv("GHOST_CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",") if origin.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Accept", "Authorization", "Content-Type"],
)


@app.get("/health/live", tags=["health"])
def liveness() -> dict[str, str]:
    """Report that the API process is running without checking dependencies."""
    return {"status": "ok", "service": "ghost-api"}


@app.get("/health/ready", tags=["health"])
def readiness() -> JSONResponse:
    """Check the effective database connection, including the local SQLite default."""
    engine = None
    try:
        # build_engine() applies DATABASE_URL when set and otherwise uses local SQLite.
        engine = build_engine(os.getenv("DATABASE_URL"))
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        database_status = "ok"
    except (SQLAlchemyError, RuntimeError):
        database_status = "unavailable"
    finally:
        if engine is not None:
            engine.dispose()

    checks = {
        "api": "ok",
        "database": database_status,
        "social_platforms": "not_configured",
        "provider_adapters": "not_configured",
        "telegram": "not_configured",
    }
    database_failed = database_status == "unavailable"
    all_integrations_configured = all(
        value == "ok" for key, value in checks.items() if key != "api"
    )
    overall_status = (
        "unavailable" if database_failed
        else "ok" if all_integrations_configured
        else "degraded"
    )
    return JSONResponse(
        status_code=503 if database_failed else 200,
        content={
            "status": overall_status,
            "service": "ghost-api",
            "checks": checks,
            "message": (
                "Database connectivity failed."
                if database_failed
                else "API is available; readiness reflects the configured dependencies."
            ),
        },
    )


@app.get("/health/migrations", tags=["health"])
def migration_status() -> JSONResponse:
    """Report database and Alembic revision status without applying migrations."""
    engine = None
    try:
        engine = build_engine(os.getenv("DATABASE_URL"))
        api_root = Path(__file__).resolve().parent.parent
        alembic_config = Config(str(api_root / "alembic.ini"))
        alembic_config.set_main_option("script_location", str(api_root / "migrations"))
        scripts = ScriptDirectory.from_config(alembic_config)
        heads = scripts.get_heads()
        with engine.connect() as connection:
            current = MigrationContext.configure(connection).get_current_revision()
        if current is None:
            status = "not_initialized"
        elif len(heads) != 1:
            status = "multiple_heads"
        elif current != heads[0]:
            status = "pending"
        else:
            status = "up_to_date"
        return JSONResponse(
            status_code=200,
            content={
                "status": status,
                "current_revision": current,
                "head_revisions": heads,
                "migration_required": status in {"not_initialized", "pending", "multiple_heads"},
                "message": {
                    "not_initialized": "No Alembic revision is recorded for this database.",
                    "pending": "The database revision differs from the latest migration head.",
                    "up_to_date": "The database matches the current migration head.",
                    "multiple_heads": "Multiple migration heads exist; review the migration graph.",
                }[status],
            },
        )
    except (SQLAlchemyError, RuntimeError, OSError, ValueError) as exc:
        # Do not include exception details: database driver errors can contain connection data.
        return JSONResponse(
            status_code=503,
            content={
                "status": "unavailable",
                "current_revision": None,
                "head_revisions": [],
                "migration_required": None,
                "message": "Could not read migration status. Check database connectivity and migration configuration.",
            },
        )
    finally:
        if engine is not None:
            engine.dispose()
