"""Minimal, truthful health surface for the Ghost API.

This service intentionally does not claim that external integrations or a database
are connected. Those capabilities will be reported only after real adapters exist.
"""
from fastapi import FastAPI
from fastapi.responses import JSONResponse

from .profile_routes import router as profile_router

app = FastAPI(
    title="Ghost API",
    description="Backend foundation for Ghost social media operations.",
    version="0.1.0",
)
app.include_router(profile_router)


@app.get("/health/live", tags=["health"])
def liveness() -> dict[str, str]:
    """Report that the API process is running."""
    return {"status": "ok", "service": "ghost-api"}


@app.get("/health/ready", tags=["health"])
def readiness() -> JSONResponse:
    """Report current readiness without pretending unconfigured services are live."""
    return JSONResponse(
        status_code=200,
        content={
            "status": "degraded",
            "service": "ghost-api",
            "checks": {
                "api": "ok",
                "database": "not_configured",
                "social_platforms": "not_configured",
                "provider_adapters": "not_configured",
                "telegram": "not_configured",
            },
            "message": "API process is available; external services are not configured.",
        },
    )
