"""Application factory and ASGI entry point (``uvicorn app.main:app``)."""

import logging
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import sessionmaker

from app.api.routes import auth, health, system
from app.config import Settings, get_settings
from app.db import create_db_engine, init_db
from app.rate_limit import LoginRateLimiter
from app.services.cpu import prime_cpu_sampling

logger = logging.getLogger(__name__)

API_PREFIX = "/api"
SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Content-Security-Policy": (
        "default-src 'self'; img-src 'self' data:; object-src 'none'; "
        "base-uri 'none'; frame-ancestors 'none'; form-action 'self'"
    ),
}


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        engine = create_db_engine(settings.database_url)
        init_db(engine)
        app.state.session_factory = sessionmaker(engine)
        prime_cpu_sampling()
        if settings.cookie_secure is False:
            logger.warning("LSM_COOKIE_SECURE=false: session cookies are sent over plain HTTP")
        yield
        engine.dispose()

    app = FastAPI(
        title="Linux Server Manager",
        lifespan=lifespan,
        docs_url=None,
        redoc_url=None,
        openapi_url=f"{API_PREFIX}/openapi.json",
    )
    app.state.settings = settings
    app.state.login_rate_limiter = LoginRateLimiter(
        settings.login_max_attempts, settings.login_window_seconds
    )

    @app.middleware("http")
    async def add_security_headers(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        response = await call_next(request)
        for header, value in SECURITY_HEADERS.items():
            response.headers.setdefault(header, value)
        if request.url.path.startswith(API_PREFIX):
            response.headers.setdefault("Cache-Control", "no-store")
        return response

    for router in (health.router, auth.router, system.router):
        app.include_router(router, prefix=API_PREFIX)

    if settings.frontend_dist is not None:
        # Mounted last so it never shadows API routes.
        app.mount("/", StaticFiles(directory=settings.frontend_dist, html=True), name="frontend")

    return app


def _configure_logging() -> None:
    logging.basicConfig(
        level=get_settings().log_level.upper(),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


def build_app() -> FastAPI:
    _configure_logging()
    return create_app()
