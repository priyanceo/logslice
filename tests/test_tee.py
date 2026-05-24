"""Tests for logslice.tee."""

from __future__ import annotations

import pytest

from logslice.log_parser import LogEntry
from logslice.tee import Tee, TeeError, TeeSink


def _entry(msg: str = "hello", level: str = "INFO") -> LogEntry:
    return LogEntry(timestamp="2024-01-01T00:00:00", level=level, message=msg)


# ---------------------------------------------------------------------------
# TeeSink validation
# ---------------------------------------------------------------------------

def test_sink_empty_name_raises() -> None:
    with pytest.raises(TeeError, match="name must not be empty"):
        TeeSink(name="", sink=lambda e: None)


def test_sink_non_callable_raises() -> None:
    with pytest.raises(TeeError, match="must be callable"):
        TeeSink(name="out", sink="not-callable")  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Tee.add_sink / dispatch
# ---------------------------------------------------------------------------

def test_dispatch_calls_all_sinks() -> None:
    received: dict[str, list[LogEntry]] = {"a": [], "b": []}
    tee = Tee()
    tee.add_sink("a", received["a"].append)
    tee.add_sink("b", received["b"].append)

    entry = _entry()
    tee.dispatch(entry)

    assert received["a"] == [entry]
    assert received["b"] == [entry]


def test_dispatch_no_sinks_is_noop() -> None:
    tee = Tee()
    tee.dispatch(_entry())  # should not raise


def test_fail_fast_stops_on_first_error() -> None:
    called: list[str] = []

    def bad_sink(e: LogEntry) -> None:
        raise RuntimeError("boom")

    def good_sink(e: LogEntry) -> None:
        called.append("good")

    tee = Tee(fail_fast=True)
    tee.add_sink("bad", bad_sink)
    tee.add_sink("good", good_sink)

    with pytest.raises(TeeError, match="boom"):
        tee.dispatch(_entry())

    assert "good" not in called


def test_no_fail_fast_calls_all_sinks_then_raises() -> None:
    called: list[str] = []

    def bad_sink(e: LogEntry) -> None:
        raise RuntimeError("oops")

    tee = Tee(fail_fast=False)
    tee.add_sink("bad", bad_sink)
    tee.add_sink("good", lambda e: called.append("good"))

    with pytest.raises(TeeError, match="One or more sinks failed"):
        tee.dispatch(_entry())

    assert "good" in called


# ---------------------------------------------------------------------------
# Tee.run
# ---------------------------------------------------------------------------

def test_run_dispatches_all_entries() -> None:
    received: list[LogEntry] = []
    tee = Tee()
    tee.add_sink("collector", received.append)

    entries = [_entry(f"msg-{i}") for i in range(5)]
    tee.run(entries)

    assert received == entries
