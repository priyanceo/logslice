"""Tests for logslice.tailer."""
from __future__ import annotations

import pytest
from datetime import datetime, timezone

from logslice.log_parser import LogEntry
from logslice.tailer import Tailer, TailerError


def _entry(msg: str, level: str = "INFO") -> LogEntry:
    return LogEntry(
        timestamp=datetime(2024, 1, 1, tzinfo=timezone.utc),
        level=level,
        service="svc",
        message=msg,
        raw=msg,
    )


@pytest.fixture()
def entries() -> list[LogEntry]:
    return [_entry(f"msg-{i}") for i in range(5)]


def test_negative_backfill_raises() -> None:
    with pytest.raises(TailerError, match="backfill"):
        Tailer(backfill=-1)


def test_zero_backfill_accepted() -> None:
    t = Tailer(backfill=0)
    assert t.backfill == 0


def test_feed_yields_all_entries(entries: list[LogEntry]) -> None:
    t = Tailer()
    result = list(t.feed(entries))
    assert result == entries


def test_backfill_buffer_capped(entries: list[LogEntry]) -> None:
    t = Tailer(backfill=3)
    list(t.feed(entries))
    buf = t.backfill_entries()
    assert len(buf) == 3
    assert buf == entries[-3:]


def test_backfill_zero_stores_all(entries: list[LogEntry]) -> None:
    t = Tailer(backfill=0)
    list(t.feed(entries))
    # With backfill=0 the deque has no maxlen — all entries stored
    assert len(t.backfill_entries()) == len(entries)


def test_on_entry_callback_called(entries: list[LogEntry]) -> None:
    seen: list[LogEntry] = []
    t = Tailer(on_entry=seen.append)
    list(t.feed(entries))
    assert seen == entries


def test_reset_clears_buffer(entries: list[LogEntry]) -> None:
    t = Tailer(backfill=5)
    list(t.feed(entries))
    t.reset()
    assert t.backfill_entries() == []


def test_feed_empty_stream() -> None:
    t = Tailer(backfill=10)
    result = list(t.feed([]))
    assert result == []
    assert t.backfill_entries() == []


def test_feed_is_lazy(entries: list[LogEntry]) -> None:
    """feed() is a generator — no work until iterated."""
    t = Tailer()
    gen = t.feed(entries)
    assert t.backfill_entries() == []
    next(gen)
    assert len(t.backfill_entries()) == 1
