from uuid import uuid4

import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import Base
from app.models import ChannelProfile
from app.profiles import create_profile, get_profile, list_profiles


@pytest.fixture()
def session():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        yield db
    engine.dispose()


def sample_profile(tenant_id: str, profile_id: str | None = None) -> dict:
    return {
        "tenant_id": tenant_id,
        "profile_id": profile_id or str(uuid4()),
        "connected_account_id": "account-1",
        "platform": "youtube",
        "display_name": "History Channel",
        "profile_version": 1,
        "language": "Hindi",
        "default_output": {"format": "short_video", "aspect_ratio": "9:16"},
    }


def test_create_and_get_profile_is_scoped_to_tenant(session: Session) -> None:
    data = sample_profile("tenant-a")
    created = create_profile(session, data)

    assert created.profile_id == data["profile_id"]
    assert get_profile(session, "tenant-a", data["profile_id"]) is not None
    assert get_profile(session, "tenant-b", data["profile_id"]) is None


def test_list_profiles_does_not_mix_tenants(session: Session) -> None:
    create_profile(session, sample_profile("tenant-a"))
    create_profile(session, sample_profile("tenant-b"))

    assert len(list_profiles(session, "tenant-a")) == 1
    assert len(list_profiles(session, "tenant-b")) == 1
    assert list_profiles(session, "unknown-tenant") == []


def test_duplicate_profile_id_within_tenant_is_rejected(session: Session) -> None:
    data = sample_profile("tenant-a")
    create_profile(session, data)
    with pytest.raises(IntegrityError):
        create_profile(session, data)
    session.rollback()


def test_database_url_is_required_for_engine_factory(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.database import build_engine

    monkeypatch.delenv("DATABASE_URL", raising=False)
    with pytest.raises(RuntimeError, match="DATABASE_URL is not configured"):
        build_engine()
