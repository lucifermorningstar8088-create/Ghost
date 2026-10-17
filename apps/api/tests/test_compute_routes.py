from collections.abc import Generator

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.auth import AuthenticatedUser, get_current_user
from app.database import Base
from app.main import app
from app.profile_routes import get_db_session


def test_client() -> Generator[TestClient, None, None]:
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
        with TestClient(app) as client:
            yield client
    finally:
        app.dependency_overrides.clear()
        engine.dispose()


def payload(**overrides) -> dict:
    return {
        "job_type": "training",
        "requested_pool": "kaggle-primary",
        "estimated_gpu_hours": 2.0,
        "job_spec": {"purpose": "test", "epochs": 1},
        **overrides,
    }


def test_compute_job_persists_as_dry_run() -> None:
    client = next(test_client())
    try:
        response = client.post(
            "/api/v1/compute/jobs",
            headers={"Idempotency-Key": "training-test-001"},
            json=payload(),
        )
        assert response.status_code == 201
        body = response.json()
        assert body["status"] == "dry_run"
        assert body["dry_run"] is True
        assert body["estimated_gpu_hours"] == 2.0
        assert "tenant_id" not in body
        assert client.get("/api/v1/compute/jobs").json()[0]["job_id"] == body["job_id"]
    finally:
        client.close()


def test_compute_job_idempotency_prevents_duplicate_rows() -> None:
    client = next(test_client())
    try:
        headers = {"Idempotency-Key": "same-request-key"}
        first = client.post("/api/v1/compute/jobs", headers=headers, json=payload())
        second = client.post("/api/v1/compute/jobs", headers=headers, json=payload(job_type="inference"))
        assert first.status_code == second.status_code == 201
        assert second.json()["job_id"] == first.json()["job_id"]
        assert len(client.get("/api/v1/compute/jobs").json()) == 1
    finally:
        client.close()


def test_compute_job_validates_type_and_gpu_hour_bound() -> None:
    client = next(test_client())
    try:
        assert client.post(
            "/api/v1/compute/jobs",
            headers={"Idempotency-Key": "invalid-job-type"},
            json=payload(job_type="shell"),
        ).status_code == 422
        assert client.post(
            "/api/v1/compute/jobs",
            headers={"Idempotency-Key": "too-many-hours"},
            json=payload(estimated_gpu_hours=31),
        ).status_code == 422
    finally:
        client.close()


def test_compute_jobs_are_tenant_scoped() -> None:
    client = next(test_client())
    try:
        created = client.post(
            "/api/v1/compute/jobs",
            headers={"Idempotency-Key": "tenant-a-job"},
            json=payload(),
        )
        assert created.status_code == 201
        app.dependency_overrides[get_current_user] = lambda: AuthenticatedUser(
            user_id="test-user-b", tenant_id="tenant-b", claims={}
        )
        assert client.get("/api/v1/compute/jobs").json() == []
    finally:
        client.close()
