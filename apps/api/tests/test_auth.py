from fastapi import FastAPI, Depends
from fastapi.testclient import TestClient
from jwt import PyJWKClientConnectionError

from app.auth import AuthenticatedUser, get_current_user


app = FastAPI()


@app.get("/protected")
def protected(user: AuthenticatedUser = Depends(get_current_user)):
    return {"user_id": user.user_id, "tenant_id": user.tenant_id}


client = TestClient(app)


def test_missing_bearer_token_is_rejected():
    response = client.get("/protected")
    assert response.status_code == 401


def test_unconfigured_auth_fails_closed(monkeypatch):
    def unconfigured(_token):
        raise RuntimeError("not configured")

    monkeypatch.setattr("app.auth.verify_access_token", unconfigured)
    response = client.get("/protected", headers={"Authorization": "Bearer test-token"})
    assert response.status_code == 503


def test_jwks_provider_outage_returns_503(monkeypatch):
    def provider_unavailable(_token):
        raise PyJWKClientConnectionError("JWKS endpoint unavailable")

    monkeypatch.setattr("app.auth.verify_access_token", provider_unavailable)
    response = client.get("/protected", headers={"Authorization": "Bearer test-token"})
    assert response.status_code == 503
    assert response.json()["detail"] == "Authentication provider is temporarily unavailable"


def test_invalid_token_is_rejected(monkeypatch):
    from jwt import InvalidTokenError

    monkeypatch.setattr(
        "app.auth.verify_access_token",
        lambda _token: (_ for _ in ()).throw(InvalidTokenError("invalid token")),
    )
    response = client.get("/protected", headers={"Authorization": "Bearer test-token"})
    assert response.status_code == 401


def test_verified_claim_without_tenant_is_forbidden(monkeypatch):
    monkeypatch.setattr("app.auth.verify_access_token", lambda _token: {"sub": "user-1"})
    response = client.get("/protected", headers={"Authorization": "Bearer test-token"})
    assert response.status_code == 403


def test_tenant_is_derived_from_verified_app_metadata(monkeypatch):
    monkeypatch.setattr(
        "app.auth.verify_access_token",
        lambda _token: {"sub": "user-1", "app_metadata": {"tenant_id": "tenant-a"}},
    )
    response = client.get("/protected", headers={"Authorization": "Bearer test-token"})
    assert response.status_code == 200
    assert response.json() == {"user_id": "user-1", "tenant_id": "tenant-a"}


def test_client_cannot_choose_tenant_via_query(monkeypatch):
    monkeypatch.setattr(
        "app.auth.verify_access_token",
        lambda _token: {"sub": "user-1", "app_metadata": {"tenant_id": "tenant-a"}},
    )
    response = client.get(
        "/protected?tenant_id=tenant-b",
        headers={"Authorization": "Bearer test-token"},
    )
    assert response.status_code == 200
    assert response.json()["tenant_id"] == "tenant-a"
