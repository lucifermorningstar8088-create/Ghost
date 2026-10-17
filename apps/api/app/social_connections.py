"""Tenant-scoped social account connection records with encrypted credentials.

This module deliberately distinguishes stored credentials from a verified live connection.
Only provider adapters with a real verification implementation may return connected=true.
"""
from __future__ import annotations

import base64
import json
import os
import uuid
from datetime import datetime, timezone
from typing import Any

import httpx
from cryptography.fernet import Fernet, InvalidToken
from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from .auth import AuthenticatedUser, get_current_user
from .database import build_engine
from .models import SocialConnection

router = APIRouter(prefix="/api/v1/connections", tags=["social-connections"])
PLATFORMS = {"youtube", "facebook", "instagram", "tiktok", "x", "telegram", "other"}
_SECRET_FIELDS = {"access_token", "refresh_token", "bearer_token", "bot_token", "api_key", "client_secret", "client_secret_key", "private_key", "password", "token", "secret", "signing_secret", "webhook_secret"}


def _fernet() -> Fernet:
    key = os.getenv("GHOST_SECRET_ENCRYPTION_KEY", "").strip()
    if not key:
        raise HTTPException(status_code=503, detail="Server secret encryption is not configured")
    try:
        return Fernet(key.encode("ascii"))
    except (ValueError, UnicodeEncodeError) as exc:
        raise HTTPException(status_code=503, detail="Server secret encryption key is invalid") from exc


def _session():
    url = os.getenv("DATABASE_URL") or "sqlite+pysqlite:///./ghost.db"
    factory = sessionmaker(bind=build_engine(url), autoflush=False, expire_on_commit=False)
    session = factory()
    try:
        yield session
    finally:
        session.close()


def _clean_metadata(value: dict[str, Any]) -> dict[str, Any]:
    """Reject credential-like keys at every nesting level to prevent plaintext secret leaks."""
    def contains_secret(item: Any) -> bool:
        if isinstance(item, dict):
            return any(
                str(key).strip().lower() in _SECRET_FIELDS or contains_secret(child)
                for key, child in item.items()
            )
        if isinstance(item, list):
            return any(contains_secret(child) for child in item)
        return False

    if contains_secret(value):
        raise HTTPException(
            status_code=422,
            detail="Put credentials in the credentials field, not metadata",
        )
    return value


class ConnectionCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    platform: str = Field(pattern=r"^(youtube|facebook|instagram|tiktok|x|telegram|other)$")
    label: str = Field(min_length=1, max_length=120)
    method: str = Field(default="manual", pattern=r"^(manual|oauth)$")
    credentials: dict[str, str] = Field(min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)
    permissions: list[str] = Field(default_factory=list, max_length=100)


class ConnectionRead(BaseModel):
    connection_id: str
    platform: str
    label: str
    method: str
    status: str
    metadata: dict[str, Any]
    permissions: list[str]
    last_checked_at: datetime | None
    created_at: datetime
    updated_at: datetime
    has_credentials: bool = True


def _read(row: SocialConnection) -> ConnectionRead:
    return ConnectionRead(
        connection_id=row.connection_id, platform=row.platform, label=row.label,
        method=row.method, status=row.status, metadata=row.metadata_json,
        permissions=row.permissions_json, last_checked_at=row.last_checked_at,
        created_at=row.created_at, updated_at=row.updated_at,
    )


@router.get("", response_model=list[ConnectionRead])
def list_connections(user: AuthenticatedUser = Depends(get_current_user), db: Session = Depends(_session)):
    try:
        rows = db.scalars(select(SocialConnection).where(SocialConnection.tenant_id == user.tenant_id).order_by(SocialConnection.created_at.desc())).all()
        return [_read(row) for row in rows]
    except SQLAlchemyError as exc:
        raise HTTPException(status_code=503, detail="Connection storage is unavailable") from exc


@router.post("", response_model=ConnectionRead, status_code=status.HTTP_201_CREATED)
def create_connection(payload: ConnectionCreate, user: AuthenticatedUser = Depends(get_current_user), db: Session = Depends(_session)):
    if not payload.credentials or any(not k.strip() or not v.strip() for k, v in payload.credentials.items()):
        raise HTTPException(status_code=422, detail="Credential names and values must be non-empty")
    metadata = _clean_metadata(payload.metadata)
    try:
        secret_blob = _fernet().encrypt(json.dumps(payload.credentials, separators=(",", ":")).encode()).decode()
        row = SocialConnection(
            connection_id=str(uuid.uuid4()), tenant_id=user.tenant_id,
            platform=payload.platform, label=payload.label.strip(), method=payload.method,
            status="needs_verification", encrypted_credentials=secret_blob,
            metadata_json=metadata, permissions_json=payload.permissions,
            created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc),
        )
        db.add(row)
        db.commit()
        db.refresh(row)
        return _read(row)
    except HTTPException:
        raise
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Connection already exists") from exc
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=503, detail="Connection storage is unavailable") from exc


def _decrypt(row: SocialConnection) -> dict[str, str]:
    try:
        return json.loads(_fernet().decrypt(row.encrypted_credentials.encode()).decode())
    except (InvalidToken, ValueError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=503, detail="Stored credentials could not be decrypted; check the server encryption key") from exc


async def _verify(row: SocialConnection) -> tuple[str, dict[str, Any]]:
    credentials = _decrypt(row)
    # Only claim live verification for adapters that actually contact the official service.
    if row.platform == "telegram":
        token = credentials.get("bot_token") or credentials.get("token")
        if not token:
            raise HTTPException(status_code=422, detail="Telegram requires bot_token")
        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                response = await client.get(f"https://api.telegram.org/bot{token}/getMe")
            data = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise HTTPException(status_code=502, detail="Telegram verification request failed") from exc
        if response.status_code != 200 or not data.get("ok"):
            raise HTTPException(status_code=422, detail="Telegram rejected the bot token")
        bot = data.get("result", {})
        return "connected", {"account_id": str(bot.get("id", "")), "username": bot.get("username", ""), "display_name": bot.get("first_name", "")}
    if row.platform == "x":
        token = credentials.get("access_token") or credentials.get("bearer_token")
        if not token:
            raise HTTPException(status_code=422, detail="X requires an access_token or bearer_token")
        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                response = await client.get("https://api.x.com/2/users/me", headers={"Authorization": f"Bearer {token}"})
            data = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise HTTPException(status_code=502, detail="X verification request failed") from exc
        if response.status_code != 200 or not isinstance(data.get("data"), dict):
            raise HTTPException(status_code=422, detail="X rejected the token or required API access is unavailable")
        account = data["data"]
        return "connected", {"account_id": str(account.get("id", "")), "username": account.get("username", ""), "display_name": account.get("name", "")}
    # These providers require app registration/OAuth callback configuration and provider-specific
    # discovery adapters. Do not misrepresent merely stored credentials as a successful connection.
    raise HTTPException(status_code=501, detail=f"Live verification adapter is not implemented for {row.platform}; credentials remain unverified")


@router.post("/{connection_id}/test", response_model=ConnectionRead)
async def test_connection(connection_id: str, user: AuthenticatedUser = Depends(get_current_user), db: Session = Depends(_session)):
    row = db.scalar(select(SocialConnection).where(SocialConnection.tenant_id == user.tenant_id, SocialConnection.connection_id == connection_id))
    if row is None:
        raise HTTPException(status_code=404, detail="Connection not found")
    try:
        new_status, discovered = await _verify(row)
        row.status = new_status
        row.metadata_json = {**row.metadata_json, **discovered}
        row.last_checked_at = datetime.now(timezone.utc)
        row.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(row)
        return _read(row)
    except HTTPException as exc:
        if exc.status_code in {422, 501, 502}:
            row.status = "verification_failed" if exc.status_code != 501 else "needs_adapter"
            row.last_checked_at = datetime.now(timezone.utc)
            row.updated_at = datetime.now(timezone.utc)
            db.commit()
        raise
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=503, detail="Connection storage is unavailable") from exc


@router.delete("/{connection_id}", status_code=status.HTTP_204_NO_CONTENT)
def disconnect_connection(connection_id: str, user: AuthenticatedUser = Depends(get_current_user), db: Session = Depends(_session)):
    row = db.scalar(select(SocialConnection).where(SocialConnection.tenant_id == user.tenant_id, SocialConnection.connection_id == connection_id))
    if row is None:
        raise HTTPException(status_code=404, detail="Connection not found")
    db.delete(row)
    db.commit()
    return Response(status_code=204)
