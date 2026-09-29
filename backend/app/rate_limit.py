"""In-memory limiter for failed login attempts.

State lives in the process: it resets on restart and is not shared between
workers. That is enough for a single-process, self-hosted deployment.
"""

import math
import threading
import time
from collections import deque
from collections.abc import Callable


class LoginRateLimiter:
    def __init__(
        self,
        max_attempts: int,
        window_seconds: float,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._max_attempts = max_attempts
        self._window = window_seconds
        self._clock = clock
        self._failures: dict[str, deque[float]] = {}
        self._lock = threading.Lock()

    def retry_after(self, key: str) -> int:
        """Seconds until ``key`` may try again; 0 when it is not blocked."""
        with self._lock:
            now = self._clock()
            failures = self._prune(key, now)
            if len(failures) < self._max_attempts:
                return 0
            return max(1, math.ceil(failures[0] + self._window - now))

    def record_failure(self, key: str) -> None:
        with self._lock:
            now = self._clock()
            self._prune_all(now)
            self._failures.setdefault(key, deque()).append(now)

    def reset(self, key: str) -> None:
        with self._lock:
            self._failures.pop(key, None)

    def _prune(self, key: str, now: float) -> deque[float]:
        failures = self._failures.get(key, deque())
        while failures and failures[0] <= now - self._window:
            failures.popleft()
        if not failures:
            self._failures.pop(key, None)
        return failures

    def _prune_all(self, now: float) -> None:
        # Keeps memory bounded by the number of clients seen within one window.
        for key in list(self._failures):
            self._prune(key, now)
