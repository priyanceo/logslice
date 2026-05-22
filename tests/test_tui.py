"""Tests for the TUI application logic (non-curses parts)."""

import pytest
from unittest.mock import MagicMock, patch
from logslice.log_parser import LogEntry
from logslice.tui import TUIApp, launch_tui


def _make_entry(msg: str, level: str = "info", ts: str = "2024-01-01T00:00:00Z") -> LogEntry:
    return LogEntry(timestamp=ts, level=level, message=msg, raw=msg)


@pytest.fixture
def entries():
    return [
        _make_entry("server started", "info"),
        _make_entry("disk full", "error"),
        _make_entry("cache miss", "warn"),
        _make_entry("user login", "debug"),
    ]


def test_initial_state_shows_all_entries(entries):
    app = TUIApp(entries)
    assert len(app.filtered) == len(entries)
    assert app.query == ""
    assert app.selected == 0


def test_filter_reduces_results(entries):
    app = TUIApp(entries)
    app.query = "disk"
    app._filter()
    assert len(app.filtered) == 1
    assert "disk" in app.filtered[0].message.lower()


def test_filter_resets_selection(entries):
    app = TUIApp(entries)
    app.selected = 2
    app.offset = 1
    app.query = "login"
    app._filter()
    assert app.selected == 0
    assert app.offset == 0


def test_filter_empty_query_shows_all(entries):
    app = TUIApp(entries)
    app.query = "error"
    app._filter()
    app.query = ""
    app._filter()
    assert len(app.filtered) == len(entries)


def test_filter_no_match_returns_empty(entries):
    app = TUIApp(entries)
    app.query = "xyzzy_not_found"
    app._filter()
    assert app.filtered == []


def test_launch_tui_returns_selected_entry(entries):
    expected = entries[1]
    with patch("logslice.tui.curses.wrapper", return_value=expected):
        result = launch_tui(entries)
    assert result is expected


def test_launch_tui_returns_none_on_quit(entries):
    with patch("logslice.tui.curses.wrapper", return_value=None):
        result = launch_tui(entries)
    assert result is None
