"""Tests for logslice.aggregator."""
from __future__ import annotations

from datetime import datetime

import pytest

from logslice.aggregator import Aggregator, AggregatorError, WindowBucket
from logslice.log_parser import LogEntry


def _entry(
    message: str = "hello",
    level: str = "info",
    service: str = "svc",
    ts: datetime | None = None,
) -> LogEntry:
    return LogEntry(
        raw=message,
        timestamp=ts or datetime(2024, 1, 1, 0, 0, 0),
        level=level,
        service=service,
        message=message,
        extra={},
    )


# --- WindowBucket ---

def test_bucket_record_increments_total():
    b = WindowBucket(window_start=datetime(2024, 1, 1), window_end=datetime(2024, 1, 1, 0, 1))
    b.record(_entry())
    assert b.total == 1


def test_bucket_record_tracks_level():
    b = WindowBucket(window_start=datetime(2024, 1, 1), window_end=datetime(2024, 1, 1, 0, 1))
    b.record(_entry(level="error"))
    b.record(_entry(level="info"))
    assert b.by_level["error"] == 1
    assert b.by_level["info"] == 1


def test_bucket_record_tracks_service():
    b = WindowBucket(window_start=datetime(2024, 1, 1), window_end=datetime(2024, 1, 1, 0, 1))
    b.record(_entry(service="api"))
    b.record(_entry(service="api"))
    assert b.by_service["api"] == 2


def test_bucket_summary_contains_total():
    b = WindowBucket(window_start=datetime(2024, 1, 1, 0, 0), window_end=datetime(2024, 1, 1, 0, 1))
    b.record(_entry())
    assert "total=1" in b.summary()


# --- Aggregator ---

def test_zero_window_raises():
    with pytest.raises(AggregatorError):
        Aggregator(window_seconds=0)


def test_negative_window_raises():
    with pytest.raises(AggregatorError):
        Aggregator(window_seconds=-5)


def test_single_entry_creates_one_bucket():
    agg = Aggregator(window_seconds=60)
    agg.feed([_entry(ts=datetime(2024, 1, 1, 0, 0, 30))])
    assert len(agg.buckets()) == 1


def test_entries_in_same_window_merge():
    agg = Aggregator(window_seconds=60)
    agg.feed([
        _entry(ts=datetime(2024, 1, 1, 0, 0, 10)),
        _entry(ts=datetime(2024, 1, 1, 0, 0, 50)),
    ])
    assert len(agg.buckets()) == 1
    assert agg.buckets()[0].total == 2


def test_entries_in_different_windows_create_multiple_buckets():
    agg = Aggregator(window_seconds=60)
    agg.feed([
        _entry(ts=datetime(2024, 1, 1, 0, 0, 10)),
        _entry(ts=datetime(2024, 1, 1, 0, 1, 10)),
    ])
    assert len(agg.buckets()) == 2


def test_buckets_sorted_by_window_start():
    agg = Aggregator(window_seconds=60)
    agg.feed([
        _entry(ts=datetime(2024, 1, 1, 0, 2, 0)),
        _entry(ts=datetime(2024, 1, 1, 0, 0, 0)),
    ])
    starts = [b.window_start for b in agg.buckets()]
    assert starts == sorted(starts)


def test_reset_clears_buckets():
    agg = Aggregator(window_seconds=60)
    agg.feed([_entry()])
    agg.reset()
    assert agg.buckets() == []
