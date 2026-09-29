from fastapi.testclient import TestClient

from app.api.deps import SESSION_COOKIE
from tests.conftest import PASSWORD


def _login(client: TestClient, username: str, password: str) -> int:
    response = client.post("/api/auth/login", json={"username": username, "password": password})
    return response.status_code


def test_login_sets_hardened_session_cookie(client: TestClient, user: str) -> None:
    response = client.post("/api/auth/login", json={"username": user, "password": PASSWORD})
    assert response.status_code == 200
    assert response.json() == {"username": user}
    cookie = response.headers["set-cookie"]
    assert cookie.startswith(f"{SESSION_COOKIE}=")
    assert "HttpOnly" in cookie
    assert "SameSite=strict" in cookie
    assert "Path=/api" in cookie
    assert "Max-Age=43200" in cookie


def test_cookie_is_secure_when_configured(client: TestClient, user: str) -> None:
    client.app.state.settings.cookie_secure = True  # type: ignore[attr-defined]
    response = client.post("/api/auth/login", json={"username": user, "password": PASSWORD})
    assert "Secure" in response.headers["set-cookie"]


def test_me_requires_session(client: TestClient) -> None:
    response = client.get("/api/auth/me")
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


def test_me_returns_logged_in_user(auth_client: TestClient, user: str) -> None:
    assert auth_client.get("/api/auth/me").json() == {"username": user}


def test_wrong_password_and_unknown_user_get_same_error(client: TestClient, user: str) -> None:
    wrong = client.post("/api/auth/login", json={"username": user, "password": "nope"})
    unknown = client.post("/api/auth/login", json={"username": "ghost", "password": "nope"})
    assert wrong.status_code == unknown.status_code == 401
    assert wrong.json() == unknown.json() == {"detail": "Invalid username or password"}
    assert "set-cookie" not in wrong.headers


def test_invalid_cookie_is_rejected(client: TestClient) -> None:
    client.cookies.set(SESSION_COOKIE, "forged-token", path="/api")
    assert client.get("/api/auth/me").status_code == 401


def test_logout_revokes_session_server_side(auth_client: TestClient) -> None:
    token = auth_client.cookies.get(SESSION_COOKIE)
    assert token
    response = auth_client.post("/api/auth/logout")
    assert response.status_code == 204
    assert auth_client.get("/api/auth/me").status_code == 401
    # Replaying the old token must not work either.
    auth_client.cookies.set(SESSION_COOKIE, token, path="/api")
    assert auth_client.get("/api/auth/me").status_code == 401


def test_logout_without_session_is_harmless(client: TestClient) -> None:
    assert client.post("/api/auth/logout").status_code == 204


def test_login_rate_limit_blocks_after_failures(client: TestClient, user: str) -> None:
    for _ in range(3):
        assert _login(client, user, "wrong password") == 401
    response = client.post("/api/auth/login", json={"username": user, "password": PASSWORD})
    assert response.status_code == 429
    assert int(response.headers["retry-after"]) > 0


def test_successful_login_resets_failure_count(client: TestClient, user: str) -> None:
    for _ in range(2):
        _login(client, user, "wrong password")
    assert _login(client, user, PASSWORD) == 200
    for _ in range(2):
        assert _login(client, user, "wrong password") == 401


def test_login_validates_payload(client: TestClient) -> None:
    assert client.post("/api/auth/login", json={}).status_code == 422
    assert client.post("/api/auth/login", json={"username": "", "password": "x"}).status_code == 422
    too_long = {"username": "a" * 65, "password": "x"}
    assert client.post("/api/auth/login", json=too_long).status_code == 422
    huge_password = {"username": "admin", "password": "x" * 1025}
    assert client.post("/api/auth/login", json=huge_password).status_code == 422
