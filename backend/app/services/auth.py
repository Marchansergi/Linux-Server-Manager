"""User accounts and login sessions."""

from datetime import UTC, datetime, timedelta

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.db import User, UserSession
from app.security import (
    burn_verification_time,
    generate_session_token,
    hash_password,
    hash_session_token,
    validate_new_password,
    validate_username,
    verify_password,
)


class UserExistsError(ValueError):
    pass


class UserNotFoundError(LookupError):
    pass


def _now() -> datetime:
    return datetime.now(UTC)


def _get_user(db: Session, username: str) -> User | None:
    return db.scalar(select(User).where(User.username == username))


def create_user(db: Session, username: str, password: str) -> User:
    validate_username(username)
    validate_new_password(password)
    if _get_user(db, username) is not None:
        raise UserExistsError(f"User '{username}' already exists")
    user = User(username=username, password_hash=hash_password(password), created_at=_now())
    db.add(user)
    db.commit()
    return user


def set_password(db: Session, username: str, password: str) -> None:
    """Change a password and revoke all of the user's sessions."""
    validate_new_password(password)
    user = _get_user(db, username)
    if user is None:
        raise UserNotFoundError(f"User '{username}' does not exist")
    user.password_hash = hash_password(password)
    db.execute(delete(UserSession).where(UserSession.user_id == user.id))
    db.commit()


def authenticate(db: Session, username: str, password: str) -> User | None:
    user = _get_user(db, username)
    if user is None:
        burn_verification_time(password)
        return None
    return user if verify_password(password, user.password_hash) else None


def create_session(db: Session, user: User, ttl: timedelta) -> str:
    """Store a new session and return its token. Only the token hash is persisted."""
    now = _now()
    db.execute(delete(UserSession).where(UserSession.expires_at <= now))
    token = generate_session_token()
    db.add(
        UserSession(
            token_hash=hash_session_token(token),
            user_id=user.id,
            created_at=now,
            expires_at=now + ttl,
        )
    )
    db.commit()
    return token


def get_session_user(db: Session, token: str) -> User | None:
    session = db.scalar(
        select(UserSession).where(UserSession.token_hash == hash_session_token(token))
    )
    if session is None:
        return None
    if session.expires_at <= _now():
        db.delete(session)
        db.commit()
        return None
    return db.get(User, session.user_id)


def revoke_session(db: Session, token: str) -> None:
    db.execute(delete(UserSession).where(UserSession.token_hash == hash_session_token(token)))
    db.commit()
