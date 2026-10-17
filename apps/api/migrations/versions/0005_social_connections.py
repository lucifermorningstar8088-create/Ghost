"""Add encrypted tenant-scoped social connection records.

Revision ID: 0005_social_connections
Revises: 0004_llm_tasks
"""
from alembic import op
import sqlalchemy as sa

revision = "0005_social_connections"
down_revision = "0004_llm_tasks"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "social_connections",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("connection_id", sa.String(length=36), nullable=False),
        sa.Column("tenant_id", sa.String(length=128), nullable=False),
        sa.Column("platform", sa.String(length=32), nullable=False),
        sa.Column("label", sa.String(length=120), nullable=False),
        sa.Column("method", sa.String(length=16), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="needs_verification"),
        sa.Column("encrypted_credentials", sa.Text(), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("permissions_json", sa.JSON(), nullable=False),
        sa.Column("last_checked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("connection_id", name="uq_social_connection_id"),
    )
    op.create_index("ix_social_connections_connection_id", "social_connections", ["connection_id"], unique=True)
    op.create_index("ix_social_connections_tenant_id", "social_connections", ["tenant_id"])
    op.create_index("ix_social_connections_platform", "social_connections", ["platform"])


def downgrade() -> None:
    op.drop_index("ix_social_connections_platform", table_name="social_connections")
    op.drop_index("ix_social_connections_tenant_id", table_name="social_connections")
    op.drop_index("ix_social_connections_connection_id", table_name="social_connections")
    op.drop_table("social_connections")
