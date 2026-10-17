"""Authenticated, tenant-scoped dry-run compute job API.

Records job intent only. It does not contact Kaggle or any provider.
"""
from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from .auth import AuthenticatedUser, get_current_user
from .models import ComputeJob
from .profile_routes import get_db_session

router = APIRouter(prefix="/api/v1/compute/jobs", tags=["compute"])


class ComputeJobCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    job_type: str = Field(pattern=r"^(training|inference|image_processing|video_processing|evaluation)$")
    requested_pool: str = Field(default="unassigned", min_length=1, max_length=64)
    estimated_gpu_hours: float = Field(default=0.0, ge=0.0, le=30.0)
    job_spec: dict = Field(default_factory=dict)


class ComputeJobRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    job_id: str
    idempotency_key: str
    job_type: str
    requested_pool: str
    estimated_gpu_hours: float
    status: str
    dry_run: bool
    job_spec: dict
    created_at: datetime


@router.post("", response_model=ComputeJobRead, status_code=status.HTTP_201_CREATED)
def create_dry_run_job(
    payload: ComputeJobCreate,
    idempotency_key: str = Header(min_length=8, max_length=128, alias="Idempotency-Key"),
    user: AuthenticatedUser = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> ComputeJob:
    """Persist a dry-run intent; external execution is intentionally not implemented."""
    existing = session.scalar(select(ComputeJob).where(
        ComputeJob.tenant_id == user.tenant_id,
        ComputeJob.idempotency_key == idempotency_key,
    ))
    if existing is not None:
        return existing

    job = ComputeJob(
        job_id=str(uuid4()),
        tenant_id=user.tenant_id,
        idempotency_key=idempotency_key,
        job_type=payload.job_type,
        requested_pool=payload.requested_pool,
        estimated_gpu_hours=payload.estimated_gpu_hours,
        status="dry_run",
        dry_run=True,
        job_spec=payload.job_spec,
    )
    session.add(job)
    try:
        session.commit()
        session.refresh(job)
        return job
    except IntegrityError as exc:
        session.rollback()
        existing = session.scalar(select(ComputeJob).where(
            ComputeJob.tenant_id == user.tenant_id,
            ComputeJob.idempotency_key == idempotency_key,
        ))
        if existing is not None:
            return existing
        raise HTTPException(status_code=409, detail="Could not reserve idempotency key") from exc
    except SQLAlchemyError as exc:
        session.rollback()
        raise HTTPException(status_code=503, detail="Compute job storage is temporarily unavailable") from exc


@router.get("", response_model=list[ComputeJobRead])
def list_dry_run_jobs(
    limit: int = Query(default=50, ge=1, le=100),
    user: AuthenticatedUser = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> list[ComputeJob]:
    """List only jobs belonging to the authenticated tenant."""
    try:
        return list(session.scalars(
            select(ComputeJob)
            .where(ComputeJob.tenant_id == user.tenant_id)
            .order_by(ComputeJob.created_at.desc())
            .limit(limit)
        ))
    except SQLAlchemyError as exc:
        session.rollback()
        raise HTTPException(status_code=503, detail="Compute job storage is temporarily unavailable") from exc
