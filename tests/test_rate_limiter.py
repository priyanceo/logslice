"""Tests for logslice.rate_limiter."""
from __future__ import annotations

import pytest

from logslice.log_parser import LogEntry
from logslice.rate_limiter import RateLimiter, RateLimiterError, apply_rate_limit


def _entry(msg: str = "hello") -> LogEntry:
    return LogEntry(timestamp="2024-01-01T00:00:00", level="info",
                    service="svc", message=msg, raw=msg)


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------

def test_zero_rate_raises() -> None:
    with pytest.raises(RateLimiterError):
        RateLimiter(max_per_second=0)


def test_negative_rate_raises() -> None:
    with pytest.raises(RateLimiterError):
        RateLimiter(max_per_second=-5.0)


# ---------------------------------------------------------------------------
# allow()
# ---------------------------------------------------------------------------

def test_allow_within_limit() -> None:
    limiter = RateLimiter(max_per_second=3)
    now = 1_000.0
    assert limiter.allow(now=now) is True
    assert limiter.allow(now=now) is True
    assert limiter.allow(now=now) is True


def test_allow_exceeds_limit() -> None:
    limiter = RateLimiter(max_per_second=2)
    now = 1_000.0
    limiter.allow(now=now)
    limiter.allow(now=now)
    assert limiter.allow(now=now) is False


def test_allow_resets_after_window() -> None:
    limiter = RateLimiter(max_per_second=2)
    t0 = 1_000.0
    limiter.allow(now=t0)
    limiter.allow(now=t0)
    # 1.1 seconds later — old timestamps should be evicted
    assert limiter.allow(now=t0 + 1.1) is True


# ---------------------------------------------------------------------------
# filter()
# ---------------------------------------------------------------------------

def test_filter_passes_entries_within_rate() -> None:
    limiter = RateLimiter(max_per_second=5)
    entries = [_entry(f"msg-{i}") for i in range(5)]
    result = list(limiter.filter(entries))
    assert len(result) == 5


def test_filter_drops_excess_entries() -> None:
    limiter = RateLimiter(max_per_second=2)
    # Monkey-patch allow to use a fixed timestamp so all calls are "simultaneous"
    fixed_now = 2_000.0
    original_allow = limiter.allow

    def _patched_allow(now=None):
        return original_allow(now=fixed_now)

    limiter.allow = _patched_allow  # type: ignore[method-assign]
    entries = [_entry(f"msg-{i}") for i in range(5)]
    result = list(limiter.filter(entries))
    assert len(result) == 2


# ---------------------------------------------------------------------------
# apply_rate_limit convenience wrapper
# ---------------------------------------------------------------------------

def test_apply_rate_limit_convenience() -> None:
    entries = [_entry(f"x-{i}") for i in range(3)]
    result = list(apply_rate_limit(entries, max_per_second=100))
    assert len(result) == 3


def test_apply_rate_limit_bad_rate_raises() -> None:
    with pytest.raises(RateLimiterError):
        list(apply_rate_limit([], max_per_second=0))
