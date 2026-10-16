from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import Session, sessionmaker

from app.auth import AuthenticatedUser, get_current_user
from app.database import Base
from app.main import app
from app.profile_routes import get_db_session


@pytest.fixture()
def client() -> Generator[TestClient, None, None]:
    engine = create_engine("sqlite+pysqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    def override_db():
        with factory() as session:
            yield session

    app.dependency_overrides[get_db_session] = override_db
    app.dependency_overrides[get_current_user] = lambda: AuthenticatedUser(
        user_id="test-user-a", tenant_id="tenant-a", claims={}
    )
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    engine.dispose()


def payload(profile_id: str = "channel-1") -> dict:
    return {
        "profile_id": profile_id,
        "connected_account_id": "account-1",
        "platform": "youtube",
        "display_name": "History Hindi",
        "profile_version": 1,
        "profile_data": {"language": "Hindi", "format": "shorts"},
    }


def test_profile_crud_is_authenticated_and_tenant_scoped(client: TestClient) -> None:
    created = client.post("/api/v1/profiles", json=payload())
    assert created.status_code == 201
    assert created.json()["profile_data"] == {"language": "Hindi", "format": "shorts"}
    assert "tenant_id" not in created.json()["profile_data"]

    assert client.get("/api/v1/profiles").json()[0]["profile_id"] == "channel-1"
    assert client.get("/api/v1/profiles/channel-1").status_code == 200

    updated = client.patch("/api/v1/profiles/channel-1", json={"display_name": "Updated Name"})
    assert updated.status_code == 200
    assert updated.json()["display_name"] == "Updated Name"

    assert client.delete("/api/v1/profiles/channel-1").status_code == 204
    assert client.get("/api/v1/profiles/channel-1").status_code == 404


def test_client_cannot_choose_tenant_or_read_another_tenant(client: TestClient) -> None:
    forged_tenant = client.post(
        "/api/v1/profiles", json={**payload("forged-channel"), "tenant_id": "tenant-b"}
    )
    assert forged_tenant.status_code == 422
    assert client.get("/api/v1/profiles/forged-channel").status_code == 404

    created = client.post("/api/v1/profiles", json=payload())
    assert created.status_code == 201

    app.dependency_overrides[get_current_user] = lambda: AuthenticatedUser(
        user_id="test-user-b", tenant_id="tenant-b", claims={}
    )
    assert client.get("/api/v1/profiles").json() == []
    assert client.get("/api/v1/profiles/channel-1").status_code == 404
    assert client.patch("/api/v1/profiles/channel-1", json={"display_name": "Nope"}).status_code == 404
    assert client.delete("/api/v1/profiles/channel-1").status_code == 404


def test_profile_requires_supported_platform_and_valid_version(client: TestClient) -> None:
    assert client.post("/api/v1/profiles", json={**payload(), "platform": "unsupported"}).status_code == 422
    assert client.post("/api/v1/profiles", json={**payload(), "profile_version": 0}).status_code == 422


def test_profile_endpoints_require_authentication_when_not_overridden(client: TestClient) -> None:
    app.dependency_overrides.pop(get_current_user)
    response = client.get("/api/v1/profiles")
    assert response.status_code == 401
