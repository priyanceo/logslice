"""Tests for logslice.windower."""
from datetime import datetime, timedelta

import pytest

from logslice.log_parser import LogEntry
from logslice.windower import Window, Windower, WindowerError


def _entry(message: str, ts: datetime, level: str = "info") -> LogEntry:
    return LogEntry(timestamp=ts, level=level, service="svc", message=message, raw=message)


BASE = datetime(2024, 1, 1, 12, 0, 0)


# --- configuration validation ---

def test_zero_window_raises():
    with pytest.raises(WindowerError):
        Windower(window_seconds=0)


def test_negative_window_raises():
    with pytest.raises(WindowerError):
        Windower(window_seconds=-10)


def test_valid_window_accepted():
    w = Windower(window_seconds=30)
    assert w.window_seconds == 30


# --- Window dataclass ---

def test_window_size_increments():
    win = Window(start=BASE, end=BASE + timedelta(seconds=60))
    win.add(_entry("a", BASE))
    win.add(_entry("b", BASE))
    assert win.size == 2


def test_window_summary_contains_total():
    win = Window(start=BASE, end=BASE + timedelta(seconds=60))
    win.add(_entry("a", BASE, level="error"))
    s = win.summary()
    assert s["total"] == 1
    assert s["levels"]["error"] == 1


def test_window_summary_iso_dates():
    win = Window(start=BASE, end=BASE + timedelta(seconds=60))
    s = win.summary()
    assert s["start"] == BASE.isoformat()


# --- Windower.push ---

def test_push_single_entry_creates_one_window():
    w = Windower(window_seconds=60)
    w.push(_entry("msg", BASE))
    wins = list(w.windows())
    assert len(wins) == 1
    assert wins[0].size == 1


def test_push_entries_within_same_window():
    w = Windower(window_seconds=60)
    w.push(_entry("a", BASE))
    w.push(_entry("b", BASE + timedelta(seconds=30)))
    wins = list(w.windows())
    assert len(wins) == 1
    assert wins[0].size == 2


def test_push_entry_past_boundary_creates_new_window():
    w = Windower(window_seconds=60)
    w.push(_entry("a", BASE))
    w.push(_entry("b", BASE + timedelta(seconds=61)))
    wins = list(w.windows())
    assert len(wins) == 2


def test_push_multiple_windows_correct_counts():
    w = Windower(window_seconds=10)
    for i in range(5):
        w.push(_entry(f"msg{i}", BASE + timedelta(seconds=i * 11)))
    wins = list(w.windows())
    assert len(wins) == 5


# --- Windower.flush ---

def test_flush_closes_open_window():
    w = Windower(window_seconds=60)
    w.push(_entry("x", BASE))
    w.flush()
    # After flush, _current is None; windows() still yields the stored window
    wins = list(w.windows())
    assert len(wins) == 1


def test_flush_empty_windower_is_noop():
    w = Windower(window_seconds=60)
    w.flush()  # should not raise
    assert list(w.windows()) == []
