"""CPU usage, core counts, load average and frequency."""

import logging
import os

import psutil

from app.schemas import CpuStats

logger = logging.getLogger(__name__)


def prime_cpu_sampling() -> None:
    """Start psutil's CPU counters.

    ``cpu_percent(interval=None)`` reports usage since the previous call, and the
    very first call always returns 0.0. Calling it at startup makes the first
    API response meaningful without blocking the request.
    """
    psutil.cpu_percent(interval=None)
    psutil.cpu_percent(interval=None, percpu=True)


def _load_average() -> tuple[float, float, float] | None:
    try:
        return os.getloadavg()
    except OSError:
        logger.warning("Load average is not available")
        return None


def _frequency_mhz() -> float | None:
    try:
        freq = psutil.cpu_freq()
    except (OSError, NotImplementedError):
        return None
    # Some virtual machines report no frequency or 0 MHz.
    return freq.current if freq is not None and freq.current > 0 else None


def get_cpu_stats() -> CpuStats:
    return CpuStats(
        usage_percent=psutil.cpu_percent(interval=None),
        per_core_percent=psutil.cpu_percent(interval=None, percpu=True),
        logical_cores=psutil.cpu_count(logical=True),
        physical_cores=psutil.cpu_count(logical=False),
        load_average=_load_average(),
        frequency_mhz=_frequency_mhz(),
    )
