"""Truthful health and dependency-readiness endpoints for the Ghost API."""
import os

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
    """Check configured database connectivity and report unconfigured integrations honestly."""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        database_status = "not_configured"
    else:
        engine = None
        try:
            engine = build_engine(database_url)
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
