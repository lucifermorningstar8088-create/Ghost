"""Fail-closed quota snapshot and idempotent budget reservation service."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .models import ComputeBudgetReservation, ComputeQuotaState


class QuotaAdmissionError(RuntimeError):
    """Quota/budget data cannot safely admit a compute job."""


def reserve_gpu_budget(
    session: Session,
    *,
    tenant_id: str,
    pool_id: str,
    job_id: str,
    requested_hours: float,
    max_snapshot_age: timedelta = timedelta(hours=6),
    now: datetime | None = None,
) -> ComputeBudgetReservation:
    """Atomically reserve hours only against a fresh, explicitly recorded snapshot.

    The caller owns the transaction boundary. On any failure, the caller must roll
    back. This function never contacts a provider and never starts a workload.
    """
    if requested_hours <= 0 or requested_hours > 30:
        raise QuotaAdmissionError("Requested GPU hours must be greater than zero and at most 30")

    now = now or datetime.now(timezone.utc)
    existing = session.scalar(select(ComputeBudgetReservation).where(
        ComputeBudgetReservation.tenant_id == tenant_id,
        ComputeBudgetReservation.job_id == job_id,
    ))
    if existing is not None:
        if existing.pool_id != pool_id or abs(existing.reserved_hours - requested_hours) > 1e-9:
            raise QuotaAdmissionError("Job already has a different budget reservation")
        if existing.status != "reserved":
            raise QuotaAdmissionError("Existing reservation is not active")
        return existing

    state = session.scalar(select(ComputeQuotaState).where(
        ComputeQuotaState.tenant_id == tenant_id,
        ComputeQuotaState.pool_id == pool_id,
    ))
    if state is None:
        raise QuotaAdmissionError("Quota snapshot is missing")
    observed_at = state.observed_at
    if observed_at.tzinfo is None:
        observed_at = observed_at.replace(tzinfo=timezone.utc)
    if observed_at > now + timedelta(minutes=5):
        raise QuotaAdmissionError("Quota snapshot timestamp is in the future")
    if now - observed_at > max_snapshot_age:
        raise QuotaAdmissionError("Quota snapshot is stale")

    # One conditional UPDATE prevents two concurrent admissions from both
    # consuming the same remaining budget, including on SQLite.
    changed = session.execute(
        update(ComputeQuotaState)
        .where(
            ComputeQuotaState.id == state.id,
            ComputeQuotaState.reserved_hours + requested_hours <= ComputeQuotaState.weekly_budget_hours,
            ComputeQuotaState.reserved_hours + requested_hours <= ComputeQuotaState.remaining_quota_hours,
        )
        .values(reserved_hours=ComputeQuotaState.reserved_hours + requested_hours)
    ).rowcount
    if changed != 1:
        raise QuotaAdmissionError("Insufficient quota or weekly budget headroom")

    reservation = ComputeBudgetReservation(
        tenant_id=tenant_id,
        pool_id=pool_id,
        job_id=job_id,
        reserved_hours=requested_hours,
        status="reserved",
    )
    session.add(reservation)
    try:
        session.flush()
    except IntegrityError as exc:
        session.rollback()
        raise QuotaAdmissionError("Reservation already exists; retry with the existing job state") from exc
    return reservation


def release_reservation_after_reconciliation(
    session: Session,
    *,
    tenant_id: str,
    job_id: str,
    remote_terminal_confirmed: bool,
) -> bool:
    """Release an active reservation only after the provider's terminal state is confirmed."""
    if not remote_terminal_confirmed:
        raise QuotaAdmissionError("Remote terminal state is not confirmed; reservation remains held")
    reservation = session.scalar(select(ComputeBudgetReservation).where(
        ComputeBudgetReservation.tenant_id == tenant_id,
        ComputeBudgetReservation.job_id == job_id,
    ))
    if reservation is None:
        return False
    if reservation.status == "released":
        return False
    state = session.scalar(select(ComputeQuotaState).where(
        ComputeQuotaState.tenant_id == tenant_id,
        ComputeQuotaState.pool_id == reservation.pool_id,
    ))
    if state is None:
        raise QuotaAdmissionError("Quota state is missing; cannot reconcile reservation")
    changed = session.execute(
        update(ComputeQuotaState)
        .where(
            ComputeQuotaState.id == state.id,
            ComputeQuotaState.reserved_hours >= reservation.reserved_hours,
        )
        .values(reserved_hours=ComputeQuotaState.reserved_hours - reservation.reserved_hours)
    ).rowcount
    if changed != 1:
        raise QuotaAdmissionError("Reservation ledger counter is inconsistent")
    reservation.status = "released"
    session.flush()
    return True
