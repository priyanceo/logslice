"""Tests for logslice.sequencer."""
from __future__ import annotations

import pytest

from logslice.log_parser import LogEntry
from logslice.sequencer import Sequencer, SequencerError


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _entry(ts: str, msg: str = "msg") -> LogEntry:
    return LogEntry(timestamp=ts, level="info", message=msg, service="svc", raw=msg)


# ---------------------------------------------------------------------------
# Configuration validation
# ---------------------------------------------------------------------------

def test_zero_buffer_raises():
    with pytest.raises(SequencerError):
        Sequencer(buffer_size=0)


def test_negative_buffer_raises():
    with pytest.raises(SequencerError):
        Sequencer(buffer_size=-1)


def test_valid_buffer_size_accepted():
    s = Sequencer(buffer_size=1)
    assert s.buffer_size == 1


# ---------------------------------------------------------------------------
# push() behaviour
# ---------------------------------------------------------------------------

def test_push_below_capacity_yields_nothing():
    s = Sequencer(buffer_size=3)
    results = list(s.push(_entry("2024-01-01T00:00:01")))
    assert results == []
    assert s.pending == 1


def test_push_at_capacity_evicts_oldest():
    s = Sequencer(buffer_size=2)
    s.push(_entry("2024-01-01T00:00:02", "b"))
    s.push(_entry("2024-01-01T00:00:01", "a"))
    evicted = list(s.push(_entry("2024-01-01T00:00:03", "c")))
    assert len(evicted) == 1
    assert evicted[0].message == "a"  # earliest timestamp evicted first


def test_push_reorders_out_of_order_entries():
    s = Sequencer(buffer_size=3)
    s.push(_entry("2024-01-01T00:00:03", "c"))
    s.push(_entry("2024-01-01T00:00:01", "a"))
    s.push(_entry("2024-01-01T00:00:02", "b"))
    # Buffer is full; adding one more triggers eviction of earliest
    evicted = list(s.push(_entry("2024-01-01T00:00:04", "d")))
    assert evicted[0].message == "a"


# ---------------------------------------------------------------------------
# flush() behaviour
# ---------------------------------------------------------------------------

def test_flush_drains_all_entries():
    s = Sequencer(buffer_size=10)
    s.push(_entry("2024-01-01T00:00:02", "b"))
    s.push(_entry("2024-01-01T00:00:01", "a"))
    flushed = list(s.flush())
    assert [e.message for e in flushed] == ["a", "b"]
    assert s.pending == 0


def test_flush_empty_buffer_yields_nothing():
    s = Sequencer(buffer_size=5)
    assert list(s.flush()) == []


# ---------------------------------------------------------------------------
# Entries without timestamps
# ---------------------------------------------------------------------------

def test_entries_without_timestamp_sort_to_front():
    s = Sequencer(buffer_size=10)
    s.push(LogEntry(timestamp=None, level="info", message="no-ts", service="s", raw="no-ts"))
    s.push(_entry("2024-01-01T00:00:01", "ts"))
    flushed = list(s.flush())
    assert flushed[0].message == "no-ts"
