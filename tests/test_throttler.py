"""Tests for logslice.throttler."""

from __future__ import annotations

import pytest

from logslice.log_parser import LogEntry
from logslice.throttler import Throttler, ThrottlerError


def _entry(message: str = "hello", level: str = "info", service: str = "svc") -> LogEntry:
    return LogEntry(timestamp="2024-01-01T00:00:00Z", level=level, service=service, message=message)


# ---------------------------------------------------------------------------
# Configuration validation
# ---------------------------------------------------------------------------

def test_zero_window_raises():
    with pytest.raises(ThrottlerError, match="window_seconds"):
        Throttler(window_seconds=0)


def test_negative_window_raises():
    with pytest.raises(ThrottlerError, match="window_seconds"):
        Throttler(window_seconds=-5)


def test_zero_max_allowed_raises():
    with pytest.raises(ThrottlerError, match="max_allowed"):
        Throttler(window_seconds=1, max_allowed=0)


def test_negative_max_allowed_raises():
    with pytest.raises(ThrottlerError, match="max_allowed"):
        Throttler(window_seconds=1, max_allowed=-1)


# ---------------------------------------------------------------------------
# Core allow logic
# ---------------------------------------------------------------------------

def test_first_occurrence_is_allowed():
    t = Throttler(window_seconds=10)
    assert t.allow(_entry("msg"), now=100.0) is True


def test_second_occurrence_within_window_is_throttled():
    t = Throttler(window_seconds=10)
    t.allow(_entry("msg"), now=100.0)
    assert t.allow(_entry("msg"), now=105.0) is False


def test_occurrence_after_window_expires_is_allowed():
    t = Throttler(window_seconds=10)
    t.allow(_entry("msg"), now=100.0)
    # 15 seconds later — outside the window
    assert t.allow(_entry("msg"), now=115.0) is True


def test_occurrence_exactly_at_window_boundary_is_throttled():
    """An event at exactly window_seconds after the first should still be throttled."""
    t = Throttler(window_seconds=10)
    t.allow(_entry("msg"), now=100.0)
    assert t.allow(_entry("msg"), now=110.0) is False


def test_different_messages_are_independent():
    t = Throttler(window_seconds=10)
    t.allow(_entry("msg-a"), now=100.0)
    assert t.allow(_entry("msg-b"), now=101.0) is True


def test_max_allowed_greater_than_one():
    t = Throttler(window_seconds=10, max_allowed=3)
    now = 100.0
    assert t.allow(_entry("msg"), now=now) is True
    assert t.allow(_entry("msg"), now=now + 1) is True
    assert t.allow(_entry("msg"), now=now + 2) is True
    assert t.allow(_entry("msg"), now=now + 3) is False


def test_reset_clears_state():
    t = Throttler(window_seconds=10)
    t.allow(_entry("msg"), now=100.0)
    t.reset()
    assert t.allow(_entry("msg"), now=101.0) is True


def test_custom_key_fn_uses_level():
    t = Throttler(window_seconds=10, key_fn=lambda e: e.level)
    t.allow(_entry("msg1", level="error"), now=100.0)
    # same level, different message — still throttled
    assert t.allow(_entry("msg2", level="error"), now=101.0) is False
    # different level — allowed
    assert t.allow(_entry("msg3", level="info"), now=101.0) is True
