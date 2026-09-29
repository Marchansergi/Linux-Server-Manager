from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.config import Settings
from app.main import create_app
from app.services.auth import create_user

USERNAME = "admin"
PASSWORD = "correct horse battery"


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    return Settings(
        database_url=f"sqlite:///{tmp_path / 'test.db'}",
        cookie_secure=False,
        login_max_attempts=3,
        login_window_seconds=60,
    )


@pytest.fixture
def client(settings: Settings) -> Iterator[TestClient]:
    with TestClient(create_app(settings)) as test_client:
        yield test_client


@pytest.fixture
def db(client: TestClient) -> Iterator[Session]:
    with client.app.state.session_factory() as session:  # type: ignore[attr-defined]
        yield session


@pytest.fixture
def user(db: Session) -> str:
    create_user(db, USERNAME, PASSWORD)
    return USERNAME


@pytest.fixture
def auth_client(client: TestClient, user: str) -> TestClient:
    response = client.post("/api/auth/login", json={"username": user, "password": PASSWORD})
    assert response.status_code == 200
    return client
