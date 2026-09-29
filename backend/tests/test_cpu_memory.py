import os
from types import SimpleNamespace

import psutil
import pytest

from app.services import cpu
from app.services.cpu import get_cpu_stats
from app.services.memory import get_memory_stats


@pytest.fixture
def fake_cpu(monkeypatch: pytest.MonkeyPatch) -> None:
    def cpu_percent(interval: float | None = None, percpu: bool = False) -> object:
        return [10.0, 30.0] if percpu else 20.0

    monkeypatch.setattr(psutil, "cpu_percent", cpu_percent)
    monkeypatch.setattr(psutil, "cpu_count", lambda logical=True: 2 if logical else 1)
    monkeypatch.setattr(psutil, "cpu_freq", lambda: SimpleNamespace(current=2400.0))
    monkeypatch.setattr(os, "getloadavg", lambda: (0.5, 0.25, 0.1))


@pytest.mark.usefixtures("fake_cpu")
def test_cpu_stats() -> None:
    stats = get_cpu_stats()
    assert stats.usage_percent == 20.0
    assert stats.per_core_percent == [10.0, 30.0]
    assert (stats.logical_cores, stats.physical_cores) == (2, 1)
    assert stats.load_average == (0.5, 0.25, 0.1)
    assert stats.frequency_mhz == 2400.0


@pytest.mark.usefixtures("fake_cpu")
def test_cpu_stats_with_missing_optional_data(monkeypatch: pytest.MonkeyPatch) -> None:
    def no_loadavg() -> tuple[float, float, float]:
        raise OSError("unavailable")

    monkeypatch.setattr(os, "getloadavg", no_loadavg)
    monkeypatch.setattr(psutil, "cpu_count", lambda logical=True: None)
    monkeypatch.setattr(psutil, "cpu_freq", lambda: None)
    stats = get_cpu_stats()
    assert stats.load_average is None
    assert stats.physical_cores is None
    assert stats.frequency_mhz is None


@pytest.mark.usefixtures("fake_cpu")
@pytest.mark.parametrize("freq", [SimpleNamespace(current=0.0), NotImplementedError, OSError])
def test_cpu_frequency_unavailable(monkeypatch: pytest.MonkeyPatch, freq: object) -> None:
    def cpu_freq() -> object:
        if isinstance(freq, type):
            raise freq
        return freq

    monkeypatch.setattr(psutil, "cpu_freq", cpu_freq)
    assert get_cpu_stats().frequency_mhz is None


def test_prime_cpu_sampling_calls_both_counters(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[bool] = []

    def cpu_percent(interval: float | None = None, percpu: bool = False) -> float:
        assert interval is None
        calls.append(percpu)
        return 0.0

    monkeypatch.setattr(psutil, "cpu_percent", cpu_percent)
    cpu.prime_cpu_sampling()
    assert calls == [False, True]


def test_memory_used_is_total_minus_available(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        psutil,
        "virtual_memory",
        lambda: SimpleNamespace(total=8000, available=6000, used=1500, percent=25.0),
    )
    monkeypatch.setattr(
        psutil, "swap_memory", lambda: SimpleNamespace(total=2000, used=500, percent=25.0)
    )
    stats = get_memory_stats()
    assert stats.used_bytes == 2000
    assert stats.available_bytes == 6000
    assert stats.percent == 25.0
    assert stats.swap.used_bytes == 500


def test_real_host_values_are_sane() -> None:
    """Smoke test against the machine running the tests."""
    stats = get_memory_stats()
    assert 0 < stats.available_bytes <= stats.total_bytes
    assert 0 <= stats.percent <= 100
    assert get_cpu_stats().logical_cores
