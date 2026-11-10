"""In-memory rate limiting for sensitive lookup attempts."""

from dataclasses import dataclass
import math
import time
from threading import Lock
from typing import Callable


class RateLimitExceeded(Exception):
    """Raised when a lookup is blocked by a case or IP lockout."""

    def __init__(self, message: str, retry_after: int = 0) -> None:
        super().__init__(message)
        self.retry_after = retry_after


@dataclass
class _FailureWindow:
    failures: int = 0
    last_failure: float = 0.0
    locked_until: float = 0.0


class LookupRateLimiter:
    """Track failed lookups with independent case and IP thresholds.

    Failures older than ``window_seconds`` stop counting. Hitting a limit
    locks that case or IP for ``lockout_seconds`` and resets its counter,
    so a lock does not re-trigger on the first mistake after it expires.
    """

    def __init__(
        self,
        *,
        clock: Callable[[], float] = time.monotonic,
        case_failure_limit: int = 5,
        ip_failure_limit: int = 10,
        lockout_seconds: float = 15 * 60,
        window_seconds: float = 10 * 60,
        max_entries: int = 10_000,
    ) -> None:
        if case_failure_limit < 1 or ip_failure_limit < 1:
            raise ValueError("failure limits must be positive")
        if lockout_seconds <= 0 or window_seconds <= 0:
            raise ValueError("lockout_seconds and window_seconds must be positive")
        self._clock = clock
        self._case_failure_limit = case_failure_limit
        self._ip_failure_limit = ip_failure_limit
        self._lockout_seconds = lockout_seconds
        self._window_seconds = window_seconds
        self._max_entries = max_entries
        self._case_windows: dict[str, _FailureWindow] = {}
        self._ip_windows: dict[str, _FailureWindow] = {}
        self._lock = Lock()

    def check(self, case_id: str, client_ip: str) -> None:
        """Raise ``RateLimitExceeded`` if this lookup is currently blocked."""

        with self._lock:
            now = self._clock()
            case_window = self._case_windows.get(case_id)
            ip_window = self._ip_windows.get(client_ip)
            if case_window and case_window.locked_until > now:
                raise RateLimitExceeded(
                    "case lookup is temporarily locked",
                    math.ceil(case_window.locked_until - now),
                )
            if ip_window and ip_window.locked_until > now:
                raise RateLimitExceeded(
                    "lookup attempts from this IP are temporarily locked",
                    math.ceil(ip_window.locked_until - now),
                )

    def record_failure(self, case_id: str, client_ip: str) -> None:
        """Record one failed lookup and apply thresholds when reached."""

        with self._lock:
            now = self._clock()
            self._register(self._case_windows, case_id, self._case_failure_limit, now)
            self._register(self._ip_windows, client_ip, self._ip_failure_limit, now)
            self._evict(self._case_windows, now)
            self._evict(self._ip_windows, now)

    def record_success(self, case_id: str, client_ip: str) -> None:
        """Clear failures for the case only, never for the IP."""

        with self._lock:
            self._case_windows.pop(case_id, None)

    def _register(self, windows, key, limit, now) -> None:
        w = windows.setdefault(key, _FailureWindow())
        if w.locked_until <= now and now - w.last_failure > self._window_seconds:
            w.failures = 0  # old failures no longer count
        w.failures += 1
        w.last_failure = now
        if w.failures >= limit:
            w.locked_until = now + self._lockout_seconds
            w.failures = 0  # fresh start once the lock expires

    def _evict(self, windows, now) -> None:
        if len(windows) <= self._max_entries:
            return
        stale = [k for k, w in windows.items()
                 if w.locked_until <= now
                 and now - w.last_failure > self._window_seconds]
        for k in stale:
            del windows[k]
        while len(windows) > self._max_entries:
            windows.pop(next(iter(windows)))  # drop the oldest entry