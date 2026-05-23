"""Tests for logslice.truncator."""
from __future__ import annotations

import pytest

from logslice.log_parser import LogEntry
from logslice.truncator import Truncator, TruncatorError


def _entry(
    message: str = "hello world",
    extra: dict | None = None,
) -> LogEntry:
    return LogEntry(
        timestamp="2024-01-01T00:00:00Z",
        level="INFO",
        service="svc",
        message=message,
        extra=extra or {},
    )


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------

def test_zero_max_length_raises():
    with pytest.raises(TruncatorError):
        Truncator(max_length=0)


def test_negative_max_length_raises():
    with pytest.raises(TruncatorError):
        Truncator(max_length=-5)


def test_ellipsis_too_long_raises():
    with pytest.raises(TruncatorError):
        Truncator(max_length=3, ellipsis_str="...")


# ---------------------------------------------------------------------------
# truncate_text
# ---------------------------------------------------------------------------

def test_short_text_unchanged():
    t = Truncator(max_length=50)
    assert t.truncate_text("hi") == "hi"


def test_exact_length_unchanged():
    t = Truncator(max_length=5)
    assert t.truncate_text("hello") == "hello"


def test_long_text_is_truncated():
    t = Truncator(max_length=10, ellipsis_str="...")
    result = t.truncate_text("A" * 20)
    assert result == "A" * 7 + "..."
    assert len(result) == 10


def test_custom_ellipsis():
    t = Truncator(max_length=8, ellipsis_str=">")
    result = t.truncate_text("123456789")
    assert result.endswith(">")
    assert len(result) == 8


# ---------------------------------------------------------------------------
# apply
# ---------------------------------------------------------------------------

def test_apply_truncates_message():
    t = Truncator(max_length=5, ellipsis_str=".")
    entry = _entry(message="hello world")
    result = t.apply(entry)
    assert len(result.message) == 5
    assert result.message.endswith(".")


def test_apply_preserves_metadata():
    t = Truncator(max_length=100)
    entry = _entry(message="short")
    result = t.apply(entry)
    assert result.timestamp == entry.timestamp
    assert result.level == entry.level
    assert result.service == entry.service


def test_apply_truncates_extra_field():
    t = Truncator(max_length=10, ellipsis_str="...", fields=["detail"])
    entry = _entry(extra={"detail": "x" * 30})
    result = t.apply(entry)
    assert len(result.extra["detail"]) == 10


def test_apply_skips_missing_extra_field():
    t = Truncator(max_length=10, fields=["body"])
    entry = _entry(extra={"other": "value"})
    result = t.apply(entry)  # should not raise
    assert "body" not in result.extra


def test_apply_does_not_mutate_original():
    t = Truncator(max_length=5, ellipsis_str=".")
    entry = _entry(message="hello world")
    t.apply(entry)
    assert entry.message == "hello world"


# ---------------------------------------------------------------------------
# run
# ---------------------------------------------------------------------------

def test_run_yields_all_entries():
    t = Truncator(max_length=100)
    entries = [_entry("short"), _entry("also short")]
    results = list(t.run(entries))
    assert len(results) == 2


def test_run_truncates_long_entries():
    t = Truncator(max_length=6, ellipsis_str="...")
    entries = [_entry("a" * 20), _entry("b" * 20)]
    results = list(t.run(entries))
    assert all(len(r.message) == 6 for r in results)
