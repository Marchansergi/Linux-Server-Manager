"""FastAPI dependencies shared by the routes."""

from collections.abc import Iterator
from typing import Annotated

from fastapi import Cookie, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.config import Settings
from app.db import User
from app.rate_limit import LoginRateLimiter
from app.services.auth import get_session_user

SESSION_COOKIE = "lsm_session"


def get_settings(request: Request) -> Settings:
    settings: Settings = request.app.state.settings
    return settings


def get_db(request: Request) -> Iterator[Session]:
    with request.app.state.session_factory() as db:
        yield db


def get_rate_limiter(request: Request) -> LoginRateLimiter:
    limiter: LoginRateLimiter = request.app.state.login_rate_limiter
    return limiter


def get_current_user(
    db: Annotated[Session, Depends(get_db)],
    session_token: Annotated[str | None, Cookie(alias=SESSION_COOKIE)] = None,
) -> User:
    user = get_session_user(db, session_token) if session_token else None
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return user


SettingsDep = Annotated[Settings, Depends(get_settings)]
DbDep = Annotated[Session, Depends(get_db)]
CurrentUserDep = Annotated[User, Depends(get_current_user)]
