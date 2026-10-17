"""Create tenant-scoped dry-run compute jobs.

Revision ID: 0002_compute_jobs
Revises: 0001_channel_profiles
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0002_compute_jobs"
down_revision: Union[str, None] = "0001_channel_profiles"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "compute_jobs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("job_id", sa.String(length=36), nullable=False),
        sa.Column("tenant_id", sa.String(length=128), nullable=False),
        sa.Column("idempotency_key", sa.String(length=128), nullable=False),
        sa.Column("job_type", sa.String(length=32), nullable=False),
        sa.Column("requested_pool", sa.String(length=64), nullable=False),
        sa.Column("estimated_gpu_hours", sa.Float(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("dry_run", sa.Boolean(), nullable=False),
        sa.Column("job_spec", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("job_id"),
        sa.UniqueConstraint("tenant_id", "idempotency_key", name="uq_compute_job_tenant_idempotency"),
    )
    op.create_index("ix_compute_jobs_job_id", "compute_jobs", ["job_id"], unique=True)
    op.create_index("ix_compute_jobs_tenant_id", "compute_jobs", ["tenant_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_compute_jobs_tenant_id", table_name="compute_jobs")
    op.drop_index("ix_compute_jobs_job_id", table_name="compute_jobs")
    op.drop_table("compute_jobs")
