"""Persistence models for Ghost profiles and compute jobs."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import Boolean, DateTime, Float, Integer, JSON, String, UniqueConstraint, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ChannelProfile(Base):
    """Versioned channel/page profile data; access is enforced by authenticated API routes."""

    __tablename__ = "channel_profiles"
    __table_args__ = (
        UniqueConstraint("tenant_id", "profile_id", name="uq_profile_tenant_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    profile_id: Mapped[str] = mapped_column(String(64), nullable=False)
    connected_account_id: Mapped[str] = mapped_column(String(128), nullable=False)
    platform: Mapped[str] = mapped_column(String(32), nullable=False)
    display_name: Mapped[str] = mapped_column(String(120), nullable=False)
    profile_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    profile_data: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)


class ComputeJob(Base):
    """Persisted job intent; this record never launches an external workload."""

    __tablename__ = "compute_jobs"
    __table_args__ = (
        UniqueConstraint("tenant_id", "idempotency_key", name="uq_compute_job_tenant_idempotency"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    job_id: Mapped[str] = mapped_column(String(36), nullable=False, unique=True, index=True)
    tenant_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    idempotency_key: Mapped[str] = mapped_column(String(128), nullable=False)
    job_type: Mapped[str] = mapped_column(String(32), nullable=False)
    requested_pool: Mapped[str] = mapped_column(String(64), nullable=False, default="unassigned")
    estimated_gpu_hours: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="dry_run")
    dry_run: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    job_spec: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)



class ComputeQuotaState(Base):
    """Operator/provider-confirmed quota and atomic budget reservation counters."""

    __tablename__ = "compute_quota_states"
    __table_args__ = (
        UniqueConstraint("tenant_id", "pool_id", name="uq_compute_quota_tenant_pool"),
        CheckConstraint("weekly_budget_hours >= 0", name="ck_compute_quota_budget_nonnegative"),
        CheckConstraint("remaining_quota_hours >= 0", name="ck_compute_quota_remaining_nonnegative"),
        CheckConstraint("reserved_hours >= 0", name="ck_compute_quota_reserved_nonnegative"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    pool_id: Mapped[str] = mapped_column(String(64), nullable=False)
    weekly_budget_hours: Mapped[float] = mapped_column(Float, nullable=False)
    remaining_quota_hours: Mapped[float] = mapped_column(Float, nullable=False)
    reserved_hours: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    source: Mapped[str] = mapped_column(String(32), nullable=False, default="operator_confirmed")
