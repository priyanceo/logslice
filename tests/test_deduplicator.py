"""Tests for logslice.deduplicator."""
from __future__ import annotations

import pytest

from logslice.deduplicator import Deduplicator, DeduplicatorConfig
from logslice.log_parser import LogEntry


def _entry(msg: str, level: str = "INFO") -> LogEntry:
    return LogEntry(timestamp="2024-01-01T00:00:00", level=level, message=msg, raw=msg)


# ---------------------------------------------------------------------------
# should_keep
# ---------------------------------------------------------------------------

def test_first_occurrence_is_kept():
    d = Deduplicator()
    assert d.should_keep(_entry("hello")) is True


def test_second_occurrence_is_suppressed_by_default():
    d = Deduplicator()
    d.should_keep(_entry("hello"))
    assert d.should_keep(_entry("hello")) is False


def test_different_messages_both_kept():
    d = Deduplicator()
    assert d.should_keep(_entry("alpha")) is True
    assert d.should_keep(_entry("beta")) is True


def test_max_repeats_allows_multiple():
    cfg = DeduplicatorConfig(max_repeats=3)
    d = Deduplicator(cfg)
    results = [d.should_keep(_entry("msg")) for _ in range(5)]
    assert results == [True, True, True, False, False]


def test_on_suppressed_callback_fires():
    fired: list[tuple] = []
    cfg = DeduplicatorConfig(
        max_repeats=1,
        on_suppressed=lambda e, n: fired.append((e.message, n)),
    )
    d = Deduplicator(cfg)
    d.should_keep(_entry("dup"))
    d.should_keep(_entry("dup"))  # suppressed
    assert len(fired) == 1
    assert fired[0][0] == "dup"
    assert fired[0][1] == 2


# ---------------------------------------------------------------------------
# filter()
# ---------------------------------------------------------------------------

def test_filter_removes_duplicates():
    d = Deduplicator()
    entries = [_entry("x"), _entry("x"), _entry("y"), _entry("x")]
    result = list(d.filter(entries))
    assert len(result) == 2
    assert result[0].message == "x"
    assert result[1].message == "y"


def test_filter_empty_input_yields_nothing():
    d = Deduplicator()
    assert list(d.filter([])) == []


# ---------------------------------------------------------------------------
# reset()
# ---------------------------------------------------------------------------

def test_reset_clears_state():
    d = Deduplicator()
    d.should_keep(_entry("hello"))
    d.reset()
    assert d.should_keep(_entry("hello")) is True


# ---------------------------------------------------------------------------
# window eviction
# ---------------------------------------------------------------------------

def test_window_evicts_old_hashes():
    cfg = DeduplicatorConfig(window_size=3)
    d = Deduplicator(cfg)
    for i in range(4):
        d.should_keep(_entry(f"msg-{i}"))
    # window holds only 3; first entry was evicted, so it's treated as new
    assert d.should_keep(_entry("msg-0")) is True
