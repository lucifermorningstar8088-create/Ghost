"""Authenticated, tenant-scoped dry-run compute job API.

Records job intent only. It does not contact Kaggle or any provider.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from .auth import AuthenticatedUser, get_current_user
from .models import ComputeJob, ComputeQuotaState
from .compute_quota import QuotaAdmissionError, reserve_gpu_budget
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



quota_router = APIRouter(prefix="/api/v1/compute", tags=["compute-quota"])


class QuotaSnapshotWrite(BaseModel):
    model_config = ConfigDict(extra="forbid")
    weekly_budget_hours: float = Field(ge=0.0, le=30.0)
    remaining_quota_hours: float = Field(ge=0.0, le=30.0)
    observed_at: datetime | None = None


class QuotaSnapshotRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    pool_id: str
    weekly_budget_hours: float
    remaining_quota_hours: float
    reserved_hours: float
    observed_at: datetime
    source: str


class ReservationRead(BaseModel):
    job_id: str
    pool_id: str
    reserved_hours: float
    status: str


@quota_router.put("/pools/{pool_id}/quota-snapshot", response_model=QuotaSnapshotRead)
def write_quota_snapshot(
    pool_id: str,
    payload: QuotaSnapshotWrite,
    user: AuthenticatedUser = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> ComputeQuotaState:
    """Record an operator-confirmed quota snapshot; credentials are never accepted."""
    if not pool_id or len(pool_id) > 64:
        raise HTTPException(status_code=422, detail="Invalid pool_id")
    observed_at = payload.observed_at or datetime.now(timezone.utc)
    if observed_at.tzinfo is None:
        observed_at = observed_at.replace(tzinfo=timezone.utc)
    now = datetime.now(timezone.utc)
    if observed_at > now + timedelta(minutes=5):
        raise HTTPException(status_code=422, detail="Quota snapshot cannot be from the future")
    state = session.scalar(select(ComputeQuotaState).where(
        ComputeQuotaState.tenant_id == user.tenant_id,
        ComputeQuotaState.pool_id == pool_id,
    ))
    if state is None:
        state = ComputeQuotaState(
            tenant_id=user.tenant_id,
            pool_id=pool_id,
            weekly_budget_hours=payload.weekly_budget_hours,
            remaining_quota_hours=payload.remaining_quota_hours,
            reserved_hours=0.0,
            observed_at=observed_at,
            source="operator_confirmed",
        )
        session.add(state)
    else:
        state.weekly_budget_hours = payload.weekly_budget_hours
        state.remaining_quota_hours = payload.remaining_quota_hours
        state.observed_at = observed_at
        state.source = "operator_confirmed"
    try:
        session.commit()
        session.refresh(state)
        return state
    except SQLAlchemyError as exc:
        session.rollback()
        raise HTTPException(status_code=503, detail="Quota snapshot storage is temporarily unavailable") from exc


@quota_router.post("/jobs/{job_id}/reserve", response_model=ReservationRead, status_code=status.HTTP_201_CREATED)
def reserve_job_budget(
    job_id: str,
    user: AuthenticatedUser = Depends(get_current_user),
    session: Session = Depends(get_db_session),
):
    """Reserve budget for a persisted job; this endpoint does not launch a provider."""
    job = session.scalar(select(ComputeJob).where(
        ComputeJob.tenant_id == user.tenant_id,
        ComputeJob.job_id == job_id,
    ))
    if job is None:
        raise HTTPException(status_code=404, detail="Compute job not found")
    if job.dry_run:
        raise HTTPException(status_code=409, detail="Dry-run jobs cannot reserve live compute budget")
    try:
        reservation = reserve_gpu_budget(
            session,
            tenant_id=user.tenant_id,
            pool_id=job.requested_pool,
            job_id=job.job_id,
            requested_hours=job.estimated_gpu_hours,
        )
        session.commit()
        session.refresh(reservation)
        return reservation
    except QuotaAdmissionError as exc:
        session.rollback()
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except SQLAlchemyError as exc:
        session.rollback()
        raise HTTPException(status_code=503, detail="Quota reservation storage is temporarily unavailable") from exc
