from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import User, UserSession
from app.services import auth
from app.services.auth import (
    UserExistsError,
    UserNotFoundError,
    authenticate,
    create_session,
    create_user,
    get_session_user,
    set_password,
)
from tests.conftest import PASSWORD


def _session_count(db: Session) -> int:
    return db.scalar(select(func.count()).select_from(UserSession)) or 0


def test_password_is_not_stored_in_plaintext(db: Session, user: str) -> None:
    stored = db.scalar(select(User.password_hash).where(User.username == user))
    assert stored is not None
    assert PASSWORD not in stored


def test_create_user_rejects_duplicates_and_invalid_input(db: Session, user: str) -> None:
    with pytest.raises(UserExistsError):
        create_user(db, user, "another good password")
    with pytest.raises(ValueError):
        create_user(db, "bad name", "another good password")
    with pytest.raises(ValueError):
        create_user(db, "newuser", "short")


def test_authenticate(db: Session, user: str) -> None:
    assert authenticate(db, user, PASSWORD) is not None
    assert authenticate(db, user, "wrong") is None
    assert authenticate(db, "ghost", PASSWORD) is None


def test_session_token_is_stored_hashed(db: Session, user: str) -> None:
    account = authenticate(db, user, PASSWORD)
    assert account is not None
    token = create_session(db, account, timedelta(hours=1))
    stored = db.scalar(select(UserSession.token_hash))
    assert stored is not None and stored != token
    found = get_session_user(db, token)
    assert found is not None and found.username == user


def test_expired_session_is_rejected_and_deleted(
    db: Session, user: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    account = authenticate(db, user, PASSWORD)
    assert account is not None
    token = create_session(db, account, timedelta(minutes=5))
    later = datetime.now(UTC) + timedelta(minutes=6)
    monkeypatch.setattr(auth, "_now", lambda: later)
    assert get_session_user(db, token) is None
    assert _session_count(db) == 0


def test_creating_a_session_purges_expired_ones(
    db: Session, user: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    account = authenticate(db, user, PASSWORD)
    assert account is not None
    create_session(db, account, timedelta(minutes=5))
    later = datetime.now(UTC) + timedelta(minutes=6)
    monkeypatch.setattr(auth, "_now", lambda: later)
    create_session(db, account, timedelta(minutes=5))
    assert _session_count(db) == 1


def test_set_password_changes_hash_and_revokes_sessions(db: Session, user: str) -> None:
    account = authenticate(db, user, PASSWORD)
    assert account is not None
    token = create_session(db, account, timedelta(hours=1))
    set_password(db, user, "a brand new password")
    assert get_session_user(db, token) is None
    assert authenticate(db, user, PASSWORD) is None
    assert authenticate(db, user, "a brand new password") is not None


def test_set_password_errors(db: Session, user: str) -> None:
    with pytest.raises(UserNotFoundError):
        set_password(db, "ghost", "a brand new password")
    with pytest.raises(ValueError):
        set_password(db, user, "short")
