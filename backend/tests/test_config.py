from pathlib import Path

import pytest

from app.config import Settings, SettingsError, load_settings


def test_defaults_when_environment_is_empty() -> None:
    assert load_settings({}) == Settings()
    assert Settings().cookie_secure is True
    assert Settings().host_root == Path("/")


def test_reads_prefixed_variables_and_ignores_others() -> None:
    settings = load_settings(
        {
            "LSM_HOST_ROOT": "/host",
            "LSM_COOKIE_SECURE": "false",
            "LSM_SESSION_TTL_MINUTES": "60",
            "HOST_ROOT": "/ignored",
        }
    )
    assert settings.host_root == Path("/host")
    assert settings.cookie_secure is False
    assert settings.session_ttl_minutes == 60


@pytest.mark.parametrize(
    "env",
    [
        {"LSM_COOKIE_SECURE": "maybe"},
        {"LSM_SESSION_TTL_MINUTES": "1"},
        {"LSM_SESSION_TTL_MINUTES": "abc"},
        {"LSM_LOGIN_MAX_ATTEMPTS": "0"},
    ],
)
def test_invalid_values_raise_settings_error(env: dict[str, str]) -> None:
    with pytest.raises(SettingsError):
        load_settings(env)
