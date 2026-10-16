from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_liveness_reports_running_api() -> None:
    response = client.get("/health/live")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "ghost-api"}


def test_readiness_does_not_claim_unconfigured_integrations_are_live() -> None:
    response = client.get("/health/ready")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "degraded"
    assert payload["checks"]["api"] == "ok"
    assert payload["checks"]["database"] == "not_configured"
    assert payload["checks"]["social_platforms"] == "not_configured"
    assert payload["checks"]["provider_adapters"] == "not_configured"
    assert payload["checks"]["telegram"] == "not_configured"
