from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import inspect

from app.config import Settings
from app.db import UTCDateTime, create_db_engine
from app.main import build_app, create_app


def test_health_is_public(client: TestClient) -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_security_headers(client: TestClient) -> None:
    headers = client.get("/api/health").headers
    assert headers["x-content-type-options"] == "nosniff"
    assert headers["x-frame-options"] == "DENY"
    assert "frame-ancestors 'none'" in headers["content-security-policy"]


def test_interactive_docs_are_disabled(client: TestClient) -> None:
    assert client.get("/docs").status_code == 404
    assert client.get("/api/openapi.json").status_code == 200


def test_database_file_and_tables_are_created(tmp_path: Path) -> None:
    db_path = tmp_path / "nested" / "dir" / "lsm.db"
    with TestClient(create_app(Settings(database_url=f"sqlite:///{db_path}"))):
        pass
    tables = inspect(create_db_engine(f"sqlite:///{db_path}")).get_table_names()
    assert set(tables) == {"users", "sessions"}


def test_utc_datetime_rejects_naive_values() -> None:
    from datetime import datetime

    with pytest.raises(ValueError, match="Naive"):
        UTCDateTime().process_bind_param(datetime(2024, 1, 1), dialect=None)  # type: ignore[arg-type]


def test_serves_frontend_without_shadowing_api(tmp_path: Path) -> None:
    (tmp_path / "index.html").write_text("<html>dashboard</html>")
    settings = Settings(database_url=f"sqlite:///{tmp_path / 'db.sqlite'}", frontend_dist=tmp_path)
    with TestClient(create_app(settings)) as client:
        assert "dashboard" in client.get("/").text
        assert client.get("/api/health").json() == {"status": "ok"}
        assert client.get("/api/auth/me").status_code == 401


def test_build_app_reads_environment(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from app.config import get_settings

    monkeypatch.setenv("LSM_DATABASE_URL", f"sqlite:///{tmp_path / 'env.db'}")
    monkeypatch.setenv("LSM_COOKIE_SECURE", "true")
    get_settings.cache_clear()
    try:
        app = build_app()
    finally:
        get_settings.cache_clear()
    assert app.state.settings.database_url.endswith("env.db")
