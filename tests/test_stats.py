"""Tests for logslice.stats module."""
from __future__ import annotations

import pytest

from logslice.log_parser import LogEntry
from logslice.stats import compute_stats, LogStats


def _entry(
    message: str = "hello",
    level: str | None = "info",
    service: str | None = None,
) -> LogEntry:
    extra = {}
    if service:
        extra["service"] = service
    return LogEntry(timestamp="2024-01-01T00:00:00Z", level=level, message=message, raw=message, extra=extra)


@pytest.fixture
def entries():
    return [
        _entry("started", "info", "api"),
        _entry("started", "info", "api"),
        _entry("error occurred", "error", "api"),
        _entry("connected", "debug", "db"),
        _entry("timeout", "warning", "db"),
        _entry("timeout", "warning", "db"),
    ]


def test_compute_stats_total(entries):
    stats = compute_stats(entries)
    assert stats.total == 6


def test_compute_stats_by_level(entries):
    stats = compute_stats(entries)
    assert stats.by_level["info"] == 2
    assert stats.by_level["error"] == 1
    assert stats.by_level["debug"] == 1
    assert stats.by_level["warning"] == 2


def test_compute_stats_by_service(entries):
    stats = compute_stats(entries)
    assert stats.by_service["api"] == 3
    assert stats.by_service["db"] == 3


def test_compute_stats_top_messages(entries):
    stats = compute_stats(entries, top_n=2)
    messages = [msg for msg, _ in stats.top_messages]
    # "started" and "timeout" both appear twice
    assert len(stats.top_messages) == 2
    assert "started" in messages
    assert "timeout" in messages


def test_compute_stats_empty():
    stats = compute_stats([])
    assert stats.total == 0
    assert stats.by_level == {}
    assert stats.by_service == {}
    assert stats.top_messages == []


def test_compute_stats_unknown_level():
    entries = [_entry(level=None)]
    stats = compute_stats(entries)
    assert stats.by_level.get("unknown") == 1


def test_summary_contains_total(entries):
    stats = compute_stats(entries)
    summary = stats.summary()
    assert "Total entries" in summary
    assert "6" in summary


def test_summary_contains_level_info(entries):
    stats = compute_stats(entries)
    summary = stats.summary()
    assert "info=2" in summary or "info" in summary
