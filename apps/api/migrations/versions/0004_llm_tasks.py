"""Create durable tenant-scoped LLM task records.

Revision ID: 0004_llm_tasks
Revises: 0003_compute_quota_state
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0004_llm_tasks"
down_revision: Union[str, None] = "0003_compute_quota_state"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "llm_tasks",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("task_id", sa.String(length=36), nullable=False),
        sa.Column("tenant_id", sa.String(length=128), nullable=False),
        sa.Column("idempotency_key", sa.String(length=128), nullable=False),
        sa.Column("status", sa.String(length=24), nullable=False, server_default="queued"),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_attempts", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("last_error_code", sa.String(length=64), nullable=True),
        sa.Column("result", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("attempts >= 0", name="ck_llm_task_attempts_nonnegative"),
        sa.CheckConstraint("max_attempts >= 1 AND max_attempts <= 5", name="ck_llm_task_max_attempts_range"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("task_id"),
        sa.UniqueConstraint("tenant_id", "idempotency_key", name="uq_llm_task_tenant_idempotency"),
    )
    op.create_index("ix_llm_tasks_task_id", "llm_tasks", ["task_id"], unique=True)
    op.create_index("ix_llm_tasks_tenant_id", "llm_tasks", ["tenant_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_llm_tasks_tenant_id", table_name="llm_tasks")
    op.drop_index("ix_llm_tasks_task_id", table_name="llm_tasks")
    op.drop_table("llm_tasks")
