import socket
import time
from pathlib import Path

import psutil
import pytest

from app.services.system_info import get_system_info, parse_os_release, read_os_name

OS_RELEASE = """\
# comment
NAME="Debian GNU/Linux"
PRETTY_NAME="Debian GNU/Linux 12 (bookworm)"
ID=debian
BROKEN="unbalanced
not a key value line
"""


def _write(root: Path, relative: str, content: str) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def test_parse_os_release() -> None:
    fields = parse_os_release(OS_RELEASE)
    assert fields["PRETTY_NAME"] == "Debian GNU/Linux 12 (bookworm)"
    assert fields["ID"] == "debian"
    assert fields["BROKEN"] == '"unbalanced'
    assert "# comment" not in fields


def test_read_os_name_prefers_pretty_name(tmp_path: Path) -> None:
    _write(tmp_path, "etc/os-release", OS_RELEASE)
    assert read_os_name(tmp_path) == "Debian GNU/Linux 12 (bookworm)"


def test_read_os_name_falls_back_to_usr_lib_and_name(tmp_path: Path) -> None:
    _write(tmp_path, "usr/lib/os-release", 'NAME="Alpine Linux"\n')
    assert read_os_name(tmp_path) == "Alpine Linux"


def test_read_os_name_keeps_absolute_symlinks_inside_host_root(tmp_path: Path) -> None:
    _write(tmp_path, "usr/lib/os-release", 'PRETTY_NAME="Host OS"\n')
    (tmp_path / "etc").mkdir()
    (tmp_path / "etc/os-release").symlink_to("/usr/lib/os-release")
    assert read_os_name(tmp_path) == "Host OS"


def test_read_os_name_follows_relative_symlinks(tmp_path: Path) -> None:
    _write(tmp_path, "usr/lib/os-release", 'PRETTY_NAME="Host OS"\n')
    (tmp_path / "etc").mkdir()
    (tmp_path / "etc/os-release").symlink_to("../usr/lib/os-release")
    assert read_os_name(tmp_path) == "Host OS"


def test_read_os_name_missing_file(tmp_path: Path) -> None:
    assert read_os_name(tmp_path) is None


def test_read_os_name_unreadable_file(tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
    (tmp_path / "etc/os-release").mkdir(parents=True)  # reading a directory raises OSError
    _write(tmp_path, "usr/lib/os-release", "NAME=Fallback\n")
    assert read_os_name(tmp_path) == "Fallback"
    assert "Cannot read" in caplog.text


def test_get_system_info(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _write(tmp_path, "etc/os-release", 'PRETTY_NAME="Test OS"\n')
    monkeypatch.setattr(psutil, "boot_time", lambda: 1_000_000.0)
    monkeypatch.setattr(time, "time", lambda: 1_003_600.5)
    monkeypatch.setattr(socket, "gethostname", lambda: "server01")
    info = get_system_info(tmp_path)
    assert info.hostname == "server01"
    assert info.os_name == "Test OS"
    assert info.uptime_seconds == 3600
    assert info.boot_time.timestamp() == 1_000_000.0
    assert info.kernel and info.architecture
