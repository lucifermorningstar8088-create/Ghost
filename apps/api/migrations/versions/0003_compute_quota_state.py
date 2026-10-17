"""Add compute quota snapshots and atomic reservation counters.

Revision ID: 0003_compute_quota_state
Revises: 0002_compute_jobs
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0003_compute_quota_state"
down_revision: Union[str, None] = "0002_compute_jobs"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "compute_quota_states",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("tenant_id", sa.String(length=128), nullable=False),
        sa.Column("pool_id", sa.String(length=64), nullable=False),
        sa.Column("weekly_budget_hours", sa.Float(), nullable=False),
        sa.Column("remaining_quota_hours", sa.Float(), nullable=False),
        sa.Column("reserved_hours", sa.Float(), nullable=False, server_default="0"),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source", sa.String(length=32), nullable=False, server_default="operator_confirmed"),
        sa.CheckConstraint("weekly_budget_hours >= 0", name="ck_compute_quota_budget_nonnegative"),
        sa.CheckConstraint("remaining_quota_hours >= 0", name="ck_compute_quota_remaining_nonnegative"),
        sa.CheckConstraint("reserved_hours >= 0", name="ck_compute_quota_reserved_nonnegative"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "pool_id", name="uq_compute_quota_tenant_pool"),
    )
    op.create_index("ix_compute_quota_states_tenant_id", "compute_quota_states", ["tenant_id"], unique=False)
    op.create_table(
        "compute_budget_reservations",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("tenant_id", sa.String(length=128), nullable=False),
        sa.Column("pool_id", sa.String(length=64), nullable=False),
        sa.Column("job_id", sa.String(length=36), nullable=False),
        sa.Column("reserved_hours", sa.Float(), nullable=False),
        sa.Column("status", sa.String(length=24), nullable=False, server_default="reserved"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("reserved_hours > 0", name="ck_compute_reservation_hours_positive"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "job_id", name="uq_compute_reservation_tenant_job"),
    )
    op.create_index("ix_compute_budget_reservations_tenant_id", "compute_budget_reservations", ["tenant_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_compute_budget_reservations_tenant_id", table_name="compute_budget_reservations")
    op.drop_table("compute_budget_reservations")
    op.drop_index("ix_compute_quota_states_tenant_id", table_name="compute_quota_states")
    op.drop_table("compute_quota_states")
