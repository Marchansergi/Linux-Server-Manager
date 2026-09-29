from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.api.routes import system
from app.services.storage import StorageUnavailableError

ENDPOINTS = ["/api/system/info", "/api/system/cpu", "/api/system/memory", "/api/system/storage"]


@pytest.mark.parametrize("path", ENDPOINTS)
def test_system_endpoints_require_authentication(client: TestClient, path: str) -> None:
    assert client.get(path).status_code == 401


@pytest.mark.parametrize("path", ENDPOINTS)
def test_system_endpoints_return_data(auth_client: TestClient, path: str) -> None:
    response = auth_client.get(path)
    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"


def test_cpu_payload_shape(auth_client: TestClient) -> None:
    data = auth_client.get("/api/system/cpu").json()
    assert set(data) == {
        "usage_percent",
        "per_core_percent",
        "logical_cores",
        "physical_cores",
        "load_average",
        "frequency_mhz",
    }
    assert 0 <= data["usage_percent"] <= 100


def test_storage_unavailable_returns_503(
    auth_client: TestClient, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    def fail(_root: Path) -> None:
        raise StorageUnavailableError("Cannot read mount table /proc/self/mounts: denied")

    monkeypatch.setattr(system, "get_storage_stats", fail)
    response = auth_client.get("/api/system/storage")
    assert response.status_code == 503
    # Internal paths and OS errors are logged, not leaked to the client.
    assert response.json() == {"detail": "Storage data unavailable"}
    assert "denied" in caplog.text


def test_info_uses_configured_host_root(
    auth_client: TestClient, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    (tmp_path / "etc").mkdir()
    (tmp_path / "etc/os-release").write_text('PRETTY_NAME="Host OS"\n')
    auth_client.app.state.settings.host_root = tmp_path  # type: ignore[attr-defined]
    assert auth_client.get("/api/system/info").json()["os_name"] == "Host OS"
