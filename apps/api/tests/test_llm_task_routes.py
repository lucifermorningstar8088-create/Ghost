from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.auth import AuthenticatedUser, get_current_user
from app.database import Base
from app.main import app
from app.profile_routes import get_db_session


@pytest.fixture()
def client() -> Generator[TestClient, None, None]:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    def override_db():
        with factory() as session:
            yield session

    app.dependency_overrides[get_db_session] = override_db
    app.dependency_overrides[get_current_user] = lambda: AuthenticatedUser(
        user_id="test-user-a", tenant_id="tenant-a", claims={}
    )
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()
        engine.dispose()


def task_payload(**overrides):
    return {
        "messages": [{"role": "user", "content": "Explain the water cycle."}],
        "temperature": 0.4,
        "max_tokens": 300,
        "max_attempts": 3,
        **overrides,
    }


def test_task_is_durably_accepted_as_queued_not_running(client: TestClient):
    response = client.post(
        "/api/v1/llm/tasks",
        headers={"Idempotency-Key": "llm-task-0001"},
        json=task_payload(),
    )
    assert response.status_code == 202
    body = response.json()
    assert body["status"] == "queued"
    assert body["attempts"] == 0
    assert body["max_attempts"] == 3
    assert body["result"] is None
    assert client.get("/api/v1/llm/tasks/" + body["task_id"]).json()["task_id"] == body["task_id"]


def test_same_idempotency_key_and_payload_returns_same_task(client: TestClient):
    headers = {"Idempotency-Key": "llm-task-repeat"}
    first = client.post("/api/v1/llm/tasks", headers=headers, json=task_payload())
    second = client.post("/api/v1/llm/tasks", headers=headers, json=task_payload())
    assert first.status_code == second.status_code == 202
    assert first.json()["task_id"] == second.json()["task_id"]
    assert len(client.get("/api/v1/llm/tasks").json()) == 1


def test_idempotency_key_reuse_with_different_payload_conflicts(client: TestClient):
    headers = {"Idempotency-Key": "llm-task-conflict"}
    first = client.post("/api/v1/llm/tasks", headers=headers, json=task_payload())
    second = client.post(
        "/api/v1/llm/tasks",
        headers=headers,
        json=task_payload(messages=[{"role": "user", "content": "Different task"}]),
    )
    assert first.status_code == 202
    assert second.status_code == 409


def test_invalid_retry_count_is_rejected(client: TestClient):
    response = client.post(
        "/api/v1/llm/tasks",
        headers={"Idempotency-Key": "llm-task-invalid"},
        json=task_payload(max_attempts=6),
    )
    assert response.status_code == 422


def test_task_records_are_tenant_scoped(client: TestClient):
    created = client.post(
        "/api/v1/llm/tasks",
        headers={"Idempotency-Key": "llm-task-tenant-a"},
        json=task_payload(),
    )
    app.dependency_overrides[get_current_user] = lambda: AuthenticatedUser(
        user_id="test-user-b", tenant_id="tenant-b", claims={}
    )
    assert client.get("/api/v1/llm/tasks").json() == []
    assert client.get("/api/v1/llm/tasks/" + created.json()["task_id"]).status_code == 404
