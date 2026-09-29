"""Static host information: hostname, OS, kernel and uptime."""

import logging
import platform
import shlex
import socket
import time
from datetime import UTC, datetime
from pathlib import Path

import psutil

from app.schemas import SystemInfo

logger = logging.getLogger(__name__)

OS_RELEASE_PATHS = ("etc/os-release", "usr/lib/os-release")


def _unquote(value: str) -> str:
    try:
        return " ".join(shlex.split(value))
    except ValueError:
        return value.strip()


def parse_os_release(content: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        fields[key.strip()] = _unquote(value)
    return fields


def read_os_name(host_root: Path) -> str | None:
    for relative in OS_RELEASE_PATHS:
        path = host_root / relative
        try:
            fields = parse_os_release(path.read_text(encoding="utf-8", errors="replace"))
        except FileNotFoundError:
            continue
        except OSError as exc:
            logger.warning("Cannot read %s: %s", path, exc)
            continue
        return fields.get("PRETTY_NAME") or fields.get("NAME")
    return None


def get_system_info(host_root: Path) -> SystemInfo:
    boot_timestamp = psutil.boot_time()
    return SystemInfo(
        hostname=socket.gethostname(),
        os_name=read_os_name(host_root),
        kernel=platform.release(),
        architecture=platform.machine(),
        boot_time=datetime.fromtimestamp(boot_timestamp, tz=UTC),
        uptime_seconds=max(0, int(time.time() - boot_timestamp)),
    )
