import pytest

from app.security.ratelimit import LookupRateLimiter, RateLimitExceeded


class FakeClock:
    def __init__(self) -> None:
        self.now = 100.0

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


def test_allows_first_lookup() -> None:
    limiter = LookupRateLimiter()
    limiter.check("case-1", "127.0.0.1")


def test_case_locks_after_five_failures() -> None:
    limiter = LookupRateLimiter()
    for _ in range(5):
        limiter.record_failure("case-1", "127.0.0.1")

    with pytest.raises(RateLimitExceeded, match="case"):
        limiter.check("case-1", "127.0.0.1")


def test_case_failures_do_not_lock_another_case() -> None:
    limiter = LookupRateLimiter()
    for _ in range(5):
        limiter.record_failure("case-1", "127.0.0.1")

    limiter.check("case-2", "127.0.0.1")


def test_ip_locks_after_ten_failures() -> None:
    limiter = LookupRateLimiter()
    for index in range(10):
        limiter.record_failure(f"case-{index}", "127.0.0.1")

    with pytest.raises(RateLimitExceeded, match="IP"):
        limiter.check("another-case", "127.0.0.1")


def test_ip_lock_applies_to_other_cases() -> None:
    limiter = LookupRateLimiter()
    for index in range(10):
        limiter.record_failure(f"case-{index}", "127.0.0.1")

    with pytest.raises(RateLimitExceeded):
        limiter.check("case-99", "127.0.0.1")


def test_different_ip_is_not_locked() -> None:
    limiter = LookupRateLimiter()
    for index in range(10):
        limiter.record_failure(f"case-{index}", "127.0.0.1")

    limiter.check("case-99", "127.0.0.2")


def test_case_lock_expires() -> None:
    clock = FakeClock()
    limiter = LookupRateLimiter(clock=clock, lockout_seconds=900)
    for _ in range(5):
        limiter.record_failure("case-1", "127.0.0.1")

    clock.advance(900)
    limiter.check("case-1", "127.0.0.1")


def test_ip_lock_expires() -> None:
    clock = FakeClock()
    limiter = LookupRateLimiter(clock=clock, lockout_seconds=900)
    for index in range(10):
        limiter.record_failure(f"case-{index}", "127.0.0.1")

    clock.advance(900)
    limiter.check("case-99", "127.0.0.1")


def test_success_clears_case_failures() -> None:
    limiter = LookupRateLimiter()
    for _ in range(4):
        limiter.record_failure("case-1", "127.0.0.1")

    limiter.record_success("case-1", "127.0.0.1")
    for _ in range(4):
        limiter.record_failure("case-1", "127.0.0.1")
    limiter.check("case-1", "127.0.0.1")


def test_invalid_limits_are_rejected() -> None:
    with pytest.raises(ValueError):
        LookupRateLimiter(case_failure_limit=0)
    with pytest.raises(ValueError):
        LookupRateLimiter(lockout_seconds=0)


# --- New tests covering the two bugs and the memory cap ---


def test_lock_does_not_retrigger_after_expiry() -> None:
    clock = FakeClock()
    limiter = LookupRateLimiter(clock=clock, lockout_seconds=900)
    for _ in range(5):
        limiter.record_failure("case-1", "127.0.0.1")

    clock.advance(901)
    limiter.record_failure("case-1", "127.0.0.1")  # one typo after the lock
    limiter.check("case-1", "127.0.0.1")


def test_old_failures_expire() -> None:
    clock = FakeClock()
    limiter = LookupRateLimiter(clock=clock, window_seconds=600)
    for _ in range(4):
        limiter.record_failure("case-1", "127.0.0.1")

    clock.advance(601)
    for _ in range(4):
        limiter.record_failure("case-1", "127.0.0.1")
    limiter.check("case-1", "127.0.0.1")


def test_memory_is_bounded() -> None:
    limiter = LookupRateLimiter(max_entries=50)
    for i in range(500):
        limiter.record_failure(f"case-{i}", f"ip-{i}")
    assert len(limiter._case_windows) <= 50
    assert len(limiter._ip_windows) <= 50