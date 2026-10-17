from collections.abc import Generator
import os

import pytest
from fastapi.testclient import TestClient
from cryptography.fernet import Fernet
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.auth import AuthenticatedUser, get_current_user
from app.database import Base
from app.main import app
from app.models import SocialConnection
from app.social_connections import _session


@pytest.fixture()
def client(monkeypatch) -> Generator[TestClient, None, None]:
    monkeypatch.setenv("GHOST_SECRET_ENCRYPTION_KEY", Fernet.generate_key().decode())
    engine = create_engine("sqlite+pysqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    def override_session():
        with factory() as session:
            yield session

    app.dependency_overrides[_session] = override_session
    app.dependency_overrides[get_current_user] = lambda: AuthenticatedUser(user_id="test-user", tenant_id="tenant-a", claims={})
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    engine.dispose()


def test_credentials_are_encrypted_and_never_returned(client: TestClient):
    secret = "telegram-secret-test-value"
    response = client.post("/api/v1/connections", json={
        "platform": "telegram", "label": "Alerts bot", "method": "manual",
        "credentials": {"bot_token": secret}, "metadata": {"purpose": "alerts"},
        "permissions": ["read_profile"],
    })
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "needs_verification"
    assert secret not in response.text
    assert "credentials" not in body
    with next(app.dependency_overrides[_session]()) as db:
        row = db.scalar(select(SocialConnection).where(SocialConnection.connection_id == body["connection_id"]))
        assert row is not None
        assert secret not in row.encrypted_credentials
        assert secret not in str(row.metadata_json)


def test_metadata_rejects_secret_fields(client: TestClient):
    response = client.post("/api/v1/connections", json={
        "platform": "x", "label": "X account", "credentials": {"bearer_token": "hidden"},
        "metadata": {"access_token": "should-not-be-here"},
    })
    assert response.status_code == 422


def test_connection_list_is_tenant_scoped(client: TestClient):
    created = client.post("/api/v1/connections", json={
        "platform": "other", "label": "Other", "credentials": {"api_key": "secret"},
    })
    assert created.status_code == 201
    listed = client.get("/api/v1/connections")
    assert listed.status_code == 200
    assert [item["connection_id"] for item in listed.json()] == [created.json()["connection_id"]]


def test_unimplemented_provider_is_not_marked_connected(client: TestClient):
    created = client.post("/api/v1/connections", json={
        "platform": "youtube", "label": "YouTube", "method": "oauth",
        "credentials": {"access_token": "token"},
    }).json()
    tested = client.post(f"/api/v1/connections/{created['connection_id']}/test")
    assert tested.status_code == 501
    assert tested.json()["detail"].startswith("Live verification adapter is not implemented")
