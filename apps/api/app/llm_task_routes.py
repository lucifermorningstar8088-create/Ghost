"""Durable tenant-scoped LLM task intake and status API.

This module persists task requests only. It does not run a background worker.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from .auth import AuthenticatedUser, get_current_user
from .models import LLMTask
from .profile_routes import get_db_session

router = APIRouter(prefix="/api/v1/llm/tasks", tags=["llm-tasks"])


class TaskMessage(BaseModel):
    model_config = ConfigDict(extra="forbid")
    role: str = Field(pattern=r"^(system|user|assistant)$")
    content: str = Field(min_length=1, max_length=12000)


class LLMTaskCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    messages: list[TaskMessage] = Field(min_length=1, max_length=40)
    temperature: float = Field(default=0.4, ge=0.0, le=2.0)
    max_tokens: int = Field(default=1024, ge=1, le=8192)
    max_attempts: int = Field(default=3, ge=1, le=5)


class LLMTaskRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    task_id: str
    idempotency_key: str
    status: str
    attempts: int
    max_attempts: int
    last_error_code: str | None
    result: dict | None
    created_at: datetime
    updated_at: datetime


def _payload_hash(payload: dict) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


@router.post("", response_model=LLMTaskRead, status_code=status.HTTP_202_ACCEPTED)
def enqueue_llm_task(
    payload: LLMTaskCreate,
    idempotency_key: str = Header(min_length=8, max_length=128, alias="Idempotency-Key"),
    user: AuthenticatedUser = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> LLMTask:
    """Persist a task request once; execution is intentionally delegated to a future worker."""
    payload_data = payload.model_dump(mode="json", exclude={"max_attempts"})
    fingerprint = _payload_hash(payload_data)
    stored_payload = {**payload_data, "_request_fingerprint": fingerprint}
    existing = session.scalar(select(LLMTask).where(
        LLMTask.tenant_id == user.tenant_id,
        LLMTask.idempotency_key == idempotency_key,
    ))
    if existing is not None:
        if existing.payload.get("_request_fingerprint") != fingerprint:
            raise HTTPException(status_code=409, detail="Idempotency-Key was already used with a different request")
        return existing

    task = LLMTask(
        task_id=str(uuid4()),
        tenant_id=user.tenant_id,
        idempotency_key=idempotency_key,
        status="queued",
        payload=stored_payload,
        attempts=0,
        max_attempts=payload.max_attempts,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    session.add(task)
    try:
        session.commit()
        session.refresh(task)
        return task
    except IntegrityError as exc:
        session.rollback()
        existing = session.scalar(select(LLMTask).where(
            LLMTask.tenant_id == user.tenant_id,
            LLMTask.idempotency_key == idempotency_key,
        ))
        if existing is not None:
            if existing.payload.get("_request_fingerprint") != fingerprint:
                raise HTTPException(status_code=409, detail="Idempotency-Key was already used with a different request") from exc
            return existing
        raise HTTPException(status_code=409, detail="Could not reserve idempotency key") from exc
    except SQLAlchemyError as exc:
        session.rollback()
        raise HTTPException(status_code=503, detail="LLM task storage is temporarily unavailable") from exc


@router.get("", response_model=list[LLMTaskRead])
def list_llm_tasks(
    limit: int = Query(default=50, ge=1, le=100),
    user: AuthenticatedUser = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> list[LLMTask]:
    try:
        return list(session.scalars(
            select(LLMTask)
            .where(LLMTask.tenant_id == user.tenant_id)
            .order_by(LLMTask.created_at.desc())
            .limit(limit)
        ))
    except SQLAlchemyError as exc:
        session.rollback()
        raise HTTPException(status_code=503, detail="LLM task storage is temporarily unavailable") from exc


@router.get("/{task_id}", response_model=LLMTaskRead)
def get_llm_task(
    task_id: str,
    user: AuthenticatedUser = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> LLMTask:
    task = session.scalar(select(LLMTask).where(
        LLMTask.task_id == task_id,
        LLMTask.tenant_id == user.tenant_id,
    ))
    if task is None:
        raise HTTPException(status_code=404, detail="LLM task not found")
    return task
