"""Application settings loaded from environment variables.

All variables use the ``LSM_`` prefix. See ``.env.example`` at the repository
root for the full list and their defaults.
"""

import os
from collections.abc import Mapping
from functools import lru_cache
from pathlib import Path

from pydantic import BaseModel, Field, ValidationError

ENV_PREFIX = "LSM_"


class SettingsError(RuntimeError):
    """Raised when the environment contains an invalid configuration."""


class Settings(BaseModel):
    database_url: str = "sqlite:///./data/lsm.db"
    # Root of the monitored host's filesystem. "/" when running directly on the
    # host; "/host" when running in Docker with the host root mounted read-only.
    host_root: Path = Path("/")
    session_ttl_minutes: int = Field(default=12 * 60, ge=5, le=30 * 24 * 60)
    cookie_secure: bool = True
    login_max_attempts: int = Field(default=5, ge=1)
    login_window_seconds: int = Field(default=300, ge=1)
    # Directory with the built frontend. When set, the backend serves it.
    frontend_dist: Path | None = None
    log_level: str = "INFO"


def load_settings(environ: Mapping[str, str] | None = None) -> Settings:
    """Build settings from ``LSM_*`` variables, rejecting invalid values."""
    env = os.environ if environ is None else environ
    values = {
        name: env[ENV_PREFIX + name.upper()]
        for name in Settings.model_fields
        if ENV_PREFIX + name.upper() in env
    }
    try:
        return Settings.model_validate(values)
    except ValidationError as exc:
        raise SettingsError(f"Invalid configuration: {exc}") from exc


@lru_cache
def get_settings() -> Settings:
    return load_settings()
