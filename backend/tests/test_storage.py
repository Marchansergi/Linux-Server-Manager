from collections import namedtuple
from pathlib import Path

import psutil
import pytest

from app.services import storage
from app.services.storage import (
    MountEntry,
    StorageUnavailableError,
    get_storage_stats,
    mounts_file,
    parse_mounts,
    parse_nodev_fstypes,
    select_storage_mounts,
)

Usage = namedtuple("Usage", "total used free percent")

MOUNTS = """\
/dev/sda1 / ext4 rw,relatime 0 0
proc /proc proc rw 0 0
tmpfs /run tmpfs rw 0 0
/dev/sda1 /var/lib/bind ext4 rw 0 0
/dev/sdb1 /mnt/my\\040disk xfs rw 0 0
/dev/loop0 /snap/core/1 squashfs ro 0 0
tank/data /tank zfs rw 0 0
server:/export /mnt/nfs nfs4 rw 0 0
overlay /var/lib/docker/overlay2/x/merged overlay rw 0 0
short line
"""
FILESYSTEMS = (
    "nodev\tsysfs\nnodev\tproc\nnodev\ttmpfs\n\text4\n"
    "nodev\tnfs4\nnodev\toverlay\nnodev\tzfs\n\txfs\n"
)
NODEV = parse_nodev_fstypes(FILESYSTEMS)


def test_parse_mounts_unescapes_and_skips_malformed_lines() -> None:
    entries = parse_mounts(MOUNTS)
    assert MountEntry("/dev/sdb1", "/mnt/my disk", "xfs") in entries
    assert all(entry.device != "short" for entry in entries)


def test_parse_nodev_fstypes() -> None:
    assert {"sysfs", "proc", "tmpfs", "nfs4", "overlay", "zfs"} == NODEV


def test_select_storage_mounts_filters_and_deduplicates() -> None:
    selected = select_storage_mounts(parse_mounts(MOUNTS), NODEV)
    assert [entry.mountpoint for entry in selected] == ["/", "/mnt/my disk", "/tank"]


def test_mounts_file_location(tmp_path: Path) -> None:
    assert mounts_file(Path("/")) == Path("/proc/self/mounts")
    assert mounts_file(tmp_path) == tmp_path / "proc/1/mounts"


@pytest.fixture
def host_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    (tmp_path / "proc/1").mkdir(parents=True)
    (tmp_path / "proc/1/mounts").write_text(MOUNTS)
    filesystems = tmp_path / "filesystems"
    filesystems.write_text(FILESYSTEMS)
    monkeypatch.setattr(storage, "PROC_FILESYSTEMS", filesystems)
    return tmp_path


def test_get_storage_stats_resolves_paths_under_host_root(
    host_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    queried: list[str] = []

    def disk_usage(path: str) -> Usage:
        queried.append(path)
        return Usage(total=100, used=40, free=60, percent=40.0)

    monkeypatch.setattr(psutil, "disk_usage", disk_usage)
    stats = get_storage_stats(host_root)
    assert queried == [str(host_root), str(host_root / "mnt/my disk"), str(host_root / "tank")]
    assert [p.mountpoint for p in stats.partitions] == ["/", "/mnt/my disk", "/tank"]
    assert stats.partitions[0].model_dump() == {
        "device": "/dev/sda1",
        "mountpoint": "/",
        "fstype": "ext4",
        "total_bytes": 100,
        "used_bytes": 40,
        "free_bytes": 60,
        "percent": 40.0,
    }


def test_unreadable_or_empty_partitions_are_skipped_and_logged(
    host_root: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    def disk_usage(path: str) -> Usage:
        if path.endswith("disk"):
            raise PermissionError("denied")
        if path.endswith("tank"):
            return Usage(total=0, used=0, free=0, percent=0.0)
        return Usage(total=100, used=40, free=60, percent=40.0)

    monkeypatch.setattr(psutil, "disk_usage", disk_usage)
    stats = get_storage_stats(host_root)
    assert [p.mountpoint for p in stats.partitions] == ["/"]
    assert "Skipping /mnt/my disk" in caplog.text


def test_missing_mount_table_raises(tmp_path: Path) -> None:
    with pytest.raises(StorageUnavailableError, match="mount table"):
        get_storage_stats(tmp_path)


def test_missing_proc_filesystems_raises(host_root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(storage, "PROC_FILESYSTEMS", host_root / "missing")
    with pytest.raises(StorageUnavailableError, match="missing"):
        get_storage_stats(host_root)


def test_real_host_has_a_root_filesystem() -> None:
    """Smoke test against the machine running the tests."""
    assert get_storage_stats(Path("/")).partitions
