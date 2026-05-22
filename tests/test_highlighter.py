"""Tests for logslice.highlighter."""

from __future__ import annotations

import pytest

from logslice.highlighter import (
    Color,
    colorize,
    format_entry,
    highlight_level,
    highlight_term,
)
from logslice.log_parser import LogEntry


def _entry(
    message: str = "hello world",
    level: str | None = "info",
    timestamp: str | None = "2024-01-01T00:00:00Z",
) -> LogEntry:
    return LogEntry(timestamp=timestamp, level=level, message=message, raw=message)


# ---------------------------------------------------------------------------
# colorize
# ---------------------------------------------------------------------------

def test_colorize_wraps_with_ansi():
    result = colorize("text", Color.RED)
    assert Color.RED.value in result
    assert "text" in result
    assert Color.RESET.value in result


# ---------------------------------------------------------------------------
# highlight_level
# ---------------------------------------------------------------------------

def test_highlight_level_error_uses_red():
    entry = _entry(level="error")
    result = highlight_level(entry)
    assert Color.RED.value in result


def test_highlight_level_info_uses_green():
    entry = _entry(level="info")
    result = highlight_level(entry)
    assert Color.GREEN.value in result


def test_highlight_level_unknown_uses_cyan():
    entry = _entry(level=None)
    result = highlight_level(entry)
    assert Color.CYAN.value in result


# ---------------------------------------------------------------------------
# highlight_term
# ---------------------------------------------------------------------------

def test_highlight_term_marks_occurrence():
    result = highlight_term("hello world", "world")
    assert Color.MAGENTA.value in result
    assert "world" in result


def test_highlight_term_case_insensitive():
    result = highlight_term("Hello World", "hello")
    assert Color.MAGENTA.value in result


def test_highlight_term_empty_term_returns_original():
    text = "unchanged"
    assert highlight_term(text, "") == text


# ---------------------------------------------------------------------------
# format_entry
# ---------------------------------------------------------------------------

def test_format_entry_contains_message():
    entry = _entry(message="something happened")
    result = format_entry(entry, use_color=False)
    assert "something happened" in result


def test_format_entry_contains_timestamp():
    entry = _entry(timestamp="2024-06-01T12:00:00Z")
    result = format_entry(entry, use_color=False)
    assert "2024-06-01T12:00:00Z" in result


def test_format_entry_highlights_search_term():
    entry = _entry(message="error occurred in module")
    result = format_entry(entry, search_term="error", use_color=True)
    assert Color.MAGENTA.value in result


def test_format_entry_no_color_no_ansi():
    entry = _entry()
    result = format_entry(entry, use_color=False)
    assert "\033[" not in result
