"""Database engine factory for local SQLite and PostgreSQL/Supabase URLs.

No connection is made at import time. Production callers must supply DATABASE_URL
through server-side environment configuration, never through a browser bundle.
"""
from __future__ import annotations

import os
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


class Base(DeclarativeBase):
    """Base class for Ghost persistence models."""


def build_engine(database_url: str | None = None) -> Engine:
    """Create an engine for an explicit URL or server-side DATABASE_URL."""
    url = database_url or os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError(
            "DATABASE_URL is not configured. Set it in the backend environment."
        )

    connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    return create_engine(url, pool_pre_ping=True, connect_args=connect_args)


def build_session_factory(engine: Engine) -> sessionmaker[Session]:
    """Create a session factory bound to the provided engine."""
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_session(factory: sessionmaker[Session]) -> Generator[Session, None, None]:
    """Yield and reliably close one database session."""
    session = factory()
    try:
        yield session
    finally:
        session.close()
