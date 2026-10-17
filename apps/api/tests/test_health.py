from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_liveness_reports_running_api() -> None:
    response = client.get("/health/live")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "ghost-api"}


def test_readiness_checks_local_sqlite_default_and_unconfigured_integrations(monkeypatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)

    response = client.get("/health/ready")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "degraded"
    assert payload["checks"]["api"] == "ok"
    assert payload["checks"]["database"] == "ok"
    assert payload["checks"]["social_platforms"] == "not_configured"
    assert payload["checks"]["provider_adapters"] == "not_configured"
    assert payload["checks"]["telegram"] == "not_configured"


def test_readiness_checks_configured_database(monkeypatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "sqlite+pysqlite:///:memory:")

    response = client.get("/health/ready")

    assert response.status_code == 200
    assert response.json()["checks"]["database"] == "ok"
    assert response.json()["status"] == "degraded"


def test_readiness_returns_503_when_configured_database_is_unavailable(monkeypatch) -> None:
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql+psycopg://ghost:wrong@127.0.0.1:1/ghost?connect_timeout=1",
    )

    response = client.get("/health/ready")

    assert response.status_code == 503
    assert response.json()["status"] == "unavailable"
    assert response.json()["checks"]["database"] == "unavailable"


def test_cors_preflight_allows_profile_crud_methods() -> None:
    for method in ("GET", "POST", "PATCH", "DELETE"):
        response = client.options(
            "/api/v1/profiles",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": method,
                "Access-Control-Request-Headers": "authorization,content-type",
            },
        )
        assert response.status_code == 200
        assert response.headers["access-control-allow-origin"] == "http://localhost:5173"
        assert method in response.headers["access-control-allow-methods"]
