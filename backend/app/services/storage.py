"""Disk usage of the host's mounted block-device filesystems.

Mounts are read from the kernel instead of ``psutil.disk_partitions`` so the
host's mounts can be listed from inside a container: with the host root
mounted at ``host_root``, ``<host_root>/proc/1/mounts`` is the mount table of
the host's init process.
"""

import logging
import re
from dataclasses import dataclass
from pathlib import Path

import psutil

from app.schemas import Partition, StorageStats

logger = logging.getLogger(__name__)

HOST_ROOT = Path("/")
PROC_FILESYSTEMS = Path("/proc/filesystems")
# Block-device filesystem that is not real storage (snap images, etc.).
EXCLUDED_FSTYPES = frozenset({"squashfs"})
# Flagged "nodev" by the kernel but backed by real storage.
EXTRA_STORAGE_FSTYPES = frozenset({"zfs"})
_OCTAL_ESCAPE = re.compile(r"\\([0-7]{3})")


class StorageUnavailableError(RuntimeError):
    """The mount table could not be read."""


@dataclass(frozen=True)
class MountEntry:
    device: str
    mountpoint: str
    fstype: str


def _unescape(field: str) -> str:
    # The kernel escapes spaces, tabs, newlines and backslashes as \ooo.
    return _OCTAL_ESCAPE.sub(lambda match: chr(int(match.group(1), 8)), field)


def parse_mounts(content: str) -> list[MountEntry]:
    entries = []
    for line in content.splitlines():
        fields = line.split()
        if len(fields) < 3:
            continue
        device, mountpoint, fstype = (_unescape(field) for field in fields[:3])
        entries.append(MountEntry(device=device, mountpoint=mountpoint, fstype=fstype))
    return entries


def parse_block_fstypes(content: str) -> frozenset[str]:
    """Filesystem types the kernel registers as backed by a block device."""
    return frozenset(
        fields[0]
        for line in content.splitlines()
        if (fields := line.split()) and not line.startswith("nodev")
    )


def mounts_file(host_root: Path) -> Path:
    if host_root == HOST_ROOT:
        return Path("/proc/self/mounts")
    return host_root / "proc/1/mounts"


def _is_storage(entry: MountEntry, block_fstypes: frozenset[str]) -> bool:
    # An allowlist: pseudo filesystems (some, like nsfs, are not even listed in
    # /proc/filesystems) and network filesystems are excluded. statvfs on a dead
    # network mount can hang, so skipping them also keeps this endpoint responsive.
    if entry.fstype in EXCLUDED_FSTYPES:
        return False
    return entry.fstype in block_fstypes or entry.fstype in EXTRA_STORAGE_FSTYPES


def select_storage_mounts(
    entries: list[MountEntry], block_fstypes: frozenset[str]
) -> list[MountEntry]:
    """Keep real storage, one entry per device (bind mounts repeat devices)."""
    seen_devices: set[str] = set()
    selected = []
    for entry in entries:
        if not _is_storage(entry, block_fstypes) or entry.device in seen_devices:
            continue
        seen_devices.add(entry.device)
        selected.append(entry)
    return selected


def _read_block_fstypes() -> frozenset[str]:
    try:
        return parse_block_fstypes(PROC_FILESYSTEMS.read_text(encoding="utf-8"))
    except OSError as exc:
        raise StorageUnavailableError(f"Cannot read {PROC_FILESYSTEMS}: {exc}") from exc


def _read_mounts(host_root: Path) -> list[MountEntry]:
    path = mounts_file(host_root)
    try:
        return parse_mounts(path.read_text(encoding="utf-8", errors="replace"))
    except OSError as exc:
        raise StorageUnavailableError(f"Cannot read mount table {path}: {exc}") from exc


def _usage(entry: MountEntry, host_root: Path) -> Partition | None:
    path = host_root / entry.mountpoint.lstrip("/")
    try:
        usage = psutil.disk_usage(str(path))
    except OSError as exc:
        logger.warning("Skipping %s: cannot read usage (%s)", entry.mountpoint, exc)
        return None
    if usage.total == 0:
        return None
    return Partition(
        device=entry.device,
        mountpoint=entry.mountpoint,
        fstype=entry.fstype,
        total_bytes=usage.total,
        used_bytes=usage.used,
        free_bytes=usage.free,
        percent=usage.percent,
    )


def get_storage_stats(host_root: Path) -> StorageStats:
    mounts = select_storage_mounts(_read_mounts(host_root), _read_block_fstypes())
    partitions = [p for entry in mounts if (p := _usage(entry, host_root)) is not None]
    return StorageStats(partitions=partitions)
