"""Authenticated, tenant-scoped channel profile API."""
from __future__ import annotations

import os
from functools import lru_cache
from typing import Any
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import delete
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from .auth import AuthenticatedUser, get_current_user
from .database import build_engine
from .models import ChannelProfile
from .profiles import create_profile, get_profile, list_profiles

router = APIRouter(prefix="/api/v1/profiles", tags=["profiles"])


@lru_cache(maxsize=4)
def _session_factory(database_url: str) -> sessionmaker[Session]:
    return sessionmaker(bind=build_engine(database_url), autoflush=False, expire_on_commit=False)


def get_db_session():
    """Open a request-scoped DB session from server-side DATABASE_URL."""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise HTTPException(status_code=503, detail="Database is not configured")
    session = _session_factory(database_url)()
    try:
        yield session
    finally:
        session.close()


class ProfileCreate(BaseModel):
    profile_id: str = Field(min_length=1, max_length=64)
    connected_account_id: str = Field(min_length=1, max_length=128)
    platform: str = Field(pattern=r"^(youtube|facebook|instagram)$")
    display_name: str = Field(min_length=1, max_length=120)
    profile_version: int = Field(default=1, ge=1)
    profile_data: dict[str, Any] = Field(default_factory=dict)


class ProfileUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    connected_account_id: str | None = Field(default=None, min_length=1, max_length=128)
    platform: str | None = Field(default=None, pattern=r"^(youtube|facebook|instagram)$")
    display_name: str | None = Field(default=None, min_length=1, max_length=120)
    profile_version: int | None = Field(default=None, ge=1)
    profile_data: dict[str, Any] | None = None


class ProfileRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    profile_id: str
    connected_account_id: str
    platform: str
    display_name: str
    profile_version: int
    profile_data: dict[str, Any]
    created_at: datetime
    updated_at: datetime


@router.post("", response_model=ProfileRead, status_code=status.HTTP_201_CREATED)
def create_channel_profile(
    payload: ProfileCreate,
    user: AuthenticatedUser = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> ChannelProfile:
    data = payload.model_dump()
    data["tenant_id"] = user.tenant_id
    try:
        return create_profile(session, data)
    except IntegrityError as exc:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Profile ID already exists for this tenant",
        ) from exc
    except SQLAlchemyError as exc:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Profile storage is temporarily unavailable",
        ) from exc


@router.get("", response_model=list[ProfileRead])
def get_channel_profiles(
    user: AuthenticatedUser = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> list[ChannelProfile]:
    return list_profiles(session, user.tenant_id)


@router.get("/{profile_id}", response_model=ProfileRead)
def get_channel_profile(
    profile_id: str,
    user: AuthenticatedUser = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> ChannelProfile:
    profile = get_profile(session, user.tenant_id, profile_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile


@router.patch("/{profile_id}", response_model=ProfileRead)
def update_channel_profile(
    profile_id: str,
    payload: ProfileUpdate,
    user: AuthenticatedUser = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> ChannelProfile:
    profile = get_profile(session, user.tenant_id, profile_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Profile not found")
    changes = payload.model_dump(exclude_unset=True)
    if not changes:
        raise HTTPException(status_code=422, detail="At least one field must be provided")
    for field, value in changes.items():
        if value is not None:
            setattr(profile, field, value)
    try:
        session.commit()
        session.refresh(profile)
    except SQLAlchemyError as exc:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Profile storage is temporarily unavailable",
        ) from exc
    return profile


@router.delete("/{profile_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_channel_profile(
    profile_id: str,
    user: AuthenticatedUser = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> Response:
    result = session.execute(
        delete(ChannelProfile).where(
            ChannelProfile.tenant_id == user.tenant_id,
            ChannelProfile.profile_id == profile_id,
        )
    )
    if result.rowcount == 0:
        session.rollback()
        raise HTTPException(status_code=404, detail="Profile not found")
    try:
        session.commit()
    except SQLAlchemyError as exc:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Profile storage is temporarily unavailable",
        ) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)
