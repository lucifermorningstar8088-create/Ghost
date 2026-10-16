"""Initial persistence models for isolated channel profile configuration."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import DateTime, Integer, JSON, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ChannelProfile(Base):
    """Versioned channel/page profile data; authorization is enforced by API layer later."""

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
