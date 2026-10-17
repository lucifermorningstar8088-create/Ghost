from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.compute_quota import (
    QuotaAdmissionError,
    release_reservation_after_reconciliation,
    reserve_gpu_budget,
)
from app.database import Base
from app.models import ComputeBudgetReservation, ComputeQuotaState


@pytest.fixture()
def session():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    with Session(engine, expire_on_commit=False) as db:
        yield db
    engine.dispose()


def add_state(session, *, observed_at=None, budget=4.0, remaining=3.0, reserved=0.0):
    state = ComputeQuotaState(
        tenant_id="tenant-a",
        pool_id="kaggle-primary",
        weekly_budget_hours=budget,
        remaining_quota_hours=remaining,
        reserved_hours=reserved,
        observed_at=observed_at or datetime.now(timezone.utc),
        source="operator_confirmed",
    )
    session.add(state)
    session.flush()
    return state


def test_reservation_checks_fresh_snapshot_and_budget(session):
    state = add_state(session, budget=2.0, remaining=2.0)
    reservation = reserve_gpu_budget(
        session, tenant_id="tenant-a", pool_id="kaggle-primary",
        job_id="job-001", requested_hours=1.5,
    )
    assert reservation.status == "reserved"
    session.flush()
    session.refresh(state)
    assert state.reserved_hours == 1.5


def test_unknown_quota_blocks_admission(session):
    with pytest.raises(QuotaAdmissionError, match="missing"):
        reserve_gpu_budget(
            session, tenant_id="tenant-a", pool_id="kaggle-primary",
            job_id="job-001", requested_hours=1.0,
        )


def test_stale_snapshot_blocks_admission(session):
    add_state(session, observed_at=datetime.now(timezone.utc) - timedelta(days=2))
    with pytest.raises(QuotaAdmissionError, match="stale"):
        reserve_gpu_budget(
            session, tenant_id="tenant-a", pool_id="kaggle-primary",
            job_id="job-001", requested_hours=1.0,
        )


def test_budget_oversubscription_is_rejected(session):
    state = add_state(session, budget=1.0, remaining=2.0)
    with pytest.raises(QuotaAdmissionError, match="Insufficient"):
        reserve_gpu_budget(
            session, tenant_id="tenant-a", pool_id="kaggle-primary",
            job_id="job-001", requested_hours=1.5,
        )
    session.refresh(state)
    assert state.reserved_hours == 0.0


def test_duplicate_reservation_is_idempotent(session):
    add_state(session)
    first = reserve_gpu_budget(
        session, tenant_id="tenant-a", pool_id="kaggle-primary",
        job_id="job-001", requested_hours=1.0,
    )
    second = reserve_gpu_budget(
        session, tenant_id="tenant-a", pool_id="kaggle-primary",
        job_id="job-001", requested_hours=1.0,
    )
    assert first.id == second.id
    assert session.scalar(select(ComputeBudgetReservation).where(
        ComputeBudgetReservation.job_id == "job-001"
    )).id == first.id


def test_reservation_cannot_be_released_without_remote_confirmation(session):
    add_state(session)
    reserve_gpu_budget(
        session, tenant_id="tenant-a", pool_id="kaggle-primary",
        job_id="job-001", requested_hours=1.0,
    )
    with pytest.raises(QuotaAdmissionError, match="not confirmed"):
        release_reservation_after_reconciliation(
            session, tenant_id="tenant-a", job_id="job-001",
            remote_terminal_confirmed=False,
        )


def test_confirmed_release_is_exactly_once(session):
    state = add_state(session)
    reserve_gpu_budget(
        session, tenant_id="tenant-a", pool_id="kaggle-primary",
        job_id="job-001", requested_hours=1.0,
    )
    session.flush()
    assert release_reservation_after_reconciliation(
        session, tenant_id="tenant-a", job_id="job-001",
        remote_terminal_confirmed=True,
    ) is True
    assert release_reservation_after_reconciliation(
        session, tenant_id="tenant-a", job_id="job-001",
        remote_terminal_confirmed=True,
    ) is False
    session.refresh(state)
    assert state.reserved_hours == 0.0
