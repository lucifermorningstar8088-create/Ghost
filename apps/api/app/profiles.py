"""Persistence operations for channel profiles.

These functions are internal building blocks. Callers must derive tenant_id from
an authenticated identity before invoking them.
"""
from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import ChannelProfile


def create_profile(session: Session, data: dict[str, Any]) -> ChannelProfile:
    """Create a profile; tenant/profile uniqueness is enforced by the database."""
    profile = ChannelProfile(
        tenant_id=data["tenant_id"],
        profile_id=data["profile_id"],
        connected_account_id=data["connected_account_id"],
        platform=data["platform"],
        display_name=data["display_name"],
        profile_version=data.get("profile_version", 1),
        profile_data=data.get("profile_data", data),
    )
    session.add(profile)
    session.commit()
    session.refresh(profile)
    return profile


def list_profiles(session: Session, tenant_id: str) -> list[ChannelProfile]:
    """List profiles only for the supplied tenant; auth must establish this value."""
    statement = (
        select(ChannelProfile)
        .where(ChannelProfile.tenant_id == tenant_id)
        .order_by(ChannelProfile.display_name, ChannelProfile.profile_id)
    )
    return list(session.scalars(statement).all())


def get_profile(
    session: Session, tenant_id: str, profile_id: str
) -> ChannelProfile | None:
    """Fetch one profile using both tenant and profile identifiers."""
    statement = select(ChannelProfile).where(
        ChannelProfile.tenant_id == tenant_id,
        ChannelProfile.profile_id == profile_id,
    )
    return session.scalars(statement).first()
