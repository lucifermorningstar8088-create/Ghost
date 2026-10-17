from collections.abc import Generator
from types import SimpleNamespace

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.llm_task_worker import process_one
from app.models import LLMTask


@pytest.fixture()
def session_factory() -> Generator[sessionmaker, None, None]:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    try:
        yield factory
    finally:
        engine.dispose()


def add_task(factory, *, max_attempts=3):
    with factory() as session:
        task = LLMTask(
            task_id="task-test-001",
            tenant_id="tenant-test",
            idempotency_key="worker-test-001",
            status="queued",
            payload={
                "messages": [{"role": "user", "content": "test"}],
                "temperature": 0.2,
                "max_tokens": 100,
                "_request_fingerprint": "internal-only",
            },
            attempts=0,
            max_attempts=max_attempts,
        )
        session.add(task)
        session.commit()


def test_worker_marks_successful_task_completed(session_factory):
    add_task(session_factory)

    class Router:
        def chat(self, messages, *, temperature, max_tokens):
            assert messages == [{"role": "user", "content": "test"}]
            assert temperature == 0.2
            assert max_tokens == 100
            return SimpleNamespace(content="done", provider="test-provider", model="test-model", attempts=1)

    assert process_one(session_factory, Router()) is True
    with session_factory() as session:
        task = session.scalar(select(LLMTask))
        assert task.status == "completed"
        assert task.attempts == 1
        assert task.result["content"] == "done"
        assert task.result["provider"] == "test-provider"
        assert "_request_fingerprint" not in task.result


def test_worker_requeues_transient_failure_until_attempt_limit(session_factory, monkeypatch):
    add_task(session_factory, max_attempts=2)
    monkeypatch.setattr("app.llm_task_worker.time.sleep", lambda _seconds: None)

    class Router:
        def chat(self, *_args, **_kwargs):
            from app.llm_router import LLMRoutingError
            raise LLMRoutingError("do not persist this message", attempts=2)

    assert process_one(session_factory, Router()) is True
    with session_factory() as session:
        task = session.scalar(select(LLMTask))
        assert task.status == "queued"
        assert task.attempts == 1
        assert task.last_error_code == "provider_unavailable"
        assert task.result is None

    assert process_one(session_factory, Router()) is True
    with session_factory() as session:
        task = session.scalar(select(LLMTask))
        assert task.status == "failed"
        assert task.attempts == 2
        assert task.last_error_code == "provider_unavailable"


def test_worker_does_not_claim_when_queue_is_empty(session_factory):
    class Router:
        def chat(self, *_args, **_kwargs):
            raise AssertionError("must not call provider")

    assert process_one(session_factory, Router()) is False
