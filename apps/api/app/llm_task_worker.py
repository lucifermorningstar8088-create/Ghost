"""Single-task worker for durable LLM tasks.

Run with: python -m app.llm_task_worker
This worker intentionally processes one task at a time. Multiple workers use
row-level locking where supported. Provider execution is never claimed until this
module is actually deployed and running.
"""
from __future__ import annotations

import logging
import os
import time
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from .database import build_engine, build_session_factory
from .llm_router import LLMFailoverRouter, LLMRoutingError
from .models import LLMTask

logger = logging.getLogger("ghost.llm_task_worker")


def process_one(session_factory, router: LLMFailoverRouter) -> bool:
    """Claim and process one queued task. Returns False when no work is available."""
    with session_factory() as session:
        task = session.scalar(
            select(LLMTask)
            .where(LLMTask.status == "queued")
            .order_by(LLMTask.created_at.asc())
            .with_for_update(skip_locked=True)
            .limit(1)
        )
        if task is None:
            return False
        task.status = "running"
        task.attempts += 1
        task.updated_at = datetime.now(timezone.utc)
        task_id = task.task_id
        payload = dict(task.payload)
        max_attempts = task.max_attempts
        session.commit()

    # The request fingerprint is internal idempotency metadata, not a model input.
    payload.pop("_request_fingerprint", None)
    try:
        result = router.chat(
            payload["messages"],
            temperature=payload.get("temperature", 0.4),
            max_tokens=payload.get("max_tokens", 1024),
        )
        safe_result = {
            "content": result.content,
            "provider": result.provider,
            "model": result.model,
            "provider_attempts": result.attempts,
        }
        status_value = "completed"
        error_code = None
    except (LLMRoutingError, ValueError, KeyError) as exc:
        # Store a bounded category, never raw upstream exception text or credentials.
        safe_result = None
        error_code = "provider_unavailable" if isinstance(exc, LLMRoutingError) else "invalid_task_payload"
        status_value = "queued" if isinstance(exc, LLMRoutingError) and _attempt_count(session_factory, task_id) < max_attempts else "failed"
        logger.warning("LLM task %s ended with safe error code %s", task_id, error_code)
    except Exception:
        safe_result = None
        error_code = "internal_worker_error"
        status_value = "queued" if _attempt_count(session_factory, task_id) < max_attempts else "failed"
        logger.exception("LLM task %s encountered an unexpected worker error", task_id)

    with session_factory() as session:
        task = session.scalar(select(LLMTask).where(LLMTask.task_id == task_id))
        if task is None:
            return True
        task.status = status_value
        task.last_error_code = error_code
        task.result = safe_result
        task.updated_at = datetime.now(timezone.utc)
        session.commit()
    return True


def _attempt_count(session_factory, task_id: str) -> int:
    with session_factory() as session:
        task = session.scalar(select(LLMTask).where(LLMTask.task_id == task_id))
        return task.attempts if task else 999


def main() -> None:
    if os.getenv("GHOST_LLM_WORKER_ENABLED", "false").lower() != "true":
        raise SystemExit("Set GHOST_LLM_WORKER_ENABLED=true to enable provider execution.")
    engine = build_engine()
    session_factory = build_session_factory(engine)
    router = LLMFailoverRouter()
    idle_seconds = max(1, min(int(os.getenv("GHOST_LLM_WORKER_POLL_SECONDS", "3")), 60))
    if not router.providers:
        raise SystemExit("No LLM providers configured; refusing to start execution worker.")
    logger.info("LLM task worker started with %d configured providers", len(router.providers))
    try:
        while True:
            if not process_one(session_factory, router):
                time.sleep(idle_seconds)
    finally:
        engine.dispose()


if __name__ == "__main__":
    logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
    main()
