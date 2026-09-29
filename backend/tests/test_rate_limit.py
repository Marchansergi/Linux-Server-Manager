from app.rate_limit import LoginRateLimiter


class FakeClock:
    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now


def test_blocks_after_max_failures_and_reports_retry_after() -> None:
    clock = FakeClock()
    limiter = LoginRateLimiter(max_attempts=3, window_seconds=60, clock=clock)
    for _ in range(2):
        limiter.record_failure("1.2.3.4")
    assert limiter.retry_after("1.2.3.4") == 0
    limiter.record_failure("1.2.3.4")
    assert limiter.retry_after("1.2.3.4") == 60
    clock.now += 45.5
    assert limiter.retry_after("1.2.3.4") == 15


def test_unblocks_when_window_expires() -> None:
    clock = FakeClock()
    limiter = LoginRateLimiter(max_attempts=1, window_seconds=60, clock=clock)
    limiter.record_failure("client")
    assert limiter.retry_after("client") > 0
    clock.now += 60
    assert limiter.retry_after("client") == 0


def test_clients_are_tracked_independently() -> None:
    limiter = LoginRateLimiter(max_attempts=1, window_seconds=60, clock=FakeClock())
    limiter.record_failure("a")
    assert limiter.retry_after("a") > 0
    assert limiter.retry_after("b") == 0


def test_reset_clears_failures() -> None:
    limiter = LoginRateLimiter(max_attempts=1, window_seconds=60, clock=FakeClock())
    limiter.record_failure("a")
    limiter.reset("a")
    assert limiter.retry_after("a") == 0


def test_expired_clients_are_pruned() -> None:
    clock = FakeClock()
    limiter = LoginRateLimiter(max_attempts=5, window_seconds=60, clock=clock)
    limiter.record_failure("old")
    clock.now += 61
    limiter.record_failure("new")
    assert set(limiter._failures) == {"new"}
