"""Login, logout and current-user endpoints (cookie-based sessions)."""

from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status

from app.api.deps import (
    SESSION_COOKIE,
    CurrentUserDep,
    DbDep,
    SettingsDep,
    get_rate_limiter,
)
from app.rate_limit import LoginRateLimiter
from app.schemas import CurrentUser, LoginRequest
from app.services.auth import authenticate, create_session, revoke_session

router = APIRouter(prefix="/auth", tags=["auth"])

COOKIE_PATH = "/api"


def _client_key(request: Request) -> str:
    return request.client.host if request.client else "unknown"


@router.post("/login")
def login(
    credentials: LoginRequest,
    request: Request,
    response: Response,
    db: DbDep,
    settings: SettingsDep,
    limiter: Annotated[LoginRateLimiter, Depends(get_rate_limiter)],
) -> CurrentUser:
    client = _client_key(request)
    retry_after = limiter.retry_after(client)
    if retry_after:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many failed login attempts",
            headers={"Retry-After": str(retry_after)},
        )
    user = authenticate(db, credentials.username, credentials.password)
    if user is None:
        limiter.record_failure(client)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password"
        )
    limiter.reset(client)
    ttl = timedelta(minutes=settings.session_ttl_minutes)
    token = create_session(db, user, ttl)
    response.set_cookie(
        SESSION_COOKIE,
        token,
        max_age=int(ttl.total_seconds()),
        path=COOKIE_PATH,
        secure=settings.cookie_secure,
        httponly=True,
        samesite="strict",
    )
    return CurrentUser(username=user.username)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    response: Response,
    db: DbDep,
    settings: SettingsDep,
    session_token: Annotated[str | None, Cookie(alias=SESSION_COOKIE)] = None,
) -> None:
    if session_token:
        revoke_session(db, session_token)
    response.delete_cookie(
        SESSION_COOKIE,
        path=COOKIE_PATH,
        secure=settings.cookie_secure,
        httponly=True,
        samesite="strict",
    )


@router.get("/me")
def me(user: CurrentUserDep) -> CurrentUser:
    return CurrentUser(username=user.username)
