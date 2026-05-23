"""Tests for logslice.router."""
from __future__ import annotations

from typing import List

import pytest

from logslice.log_parser import LogEntry
from logslice.router import Route, Router, RouterError


def _entry(message: str = "hello", level: str = "info", service: str = "svc") -> LogEntry:
    return LogEntry(timestamp="2024-01-01T00:00:00Z", level=level, service=service, message=message, raw=message)


# ---------------------------------------------------------------------------
# Route validation
# ---------------------------------------------------------------------------

def test_route_empty_name_raises():
    with pytest.raises(RouterError):
        Route(name="", match=lambda e: True, sink=lambda e: None)


def test_route_non_callable_match_raises():
    with pytest.raises(RouterError):
        Route(name="r", match="not_callable", sink=lambda e: None)  # type: ignore


def test_route_non_callable_sink_raises():
    with pytest.raises(RouterError):
        Route(name="r", match=lambda e: True, sink="not_callable")  # type: ignore


# ---------------------------------------------------------------------------
# Router dispatch
# ---------------------------------------------------------------------------

def test_dispatch_calls_matching_sink():
    received: List[LogEntry] = []
    router = Router()
    router.add_route(Route(name="all", match=lambda e: True, sink=received.append))
    entry = _entry()
    router.dispatch(entry)
    assert received == [entry]


def test_dispatch_skips_non_matching_sink():
    received: List[LogEntry] = []
    router = Router()
    router.add_route(Route(name="errors", match=lambda e: e.level == "error", sink=received.append))
    router.dispatch(_entry(level="info"))
    assert received == []


def test_dispatch_returns_matched_names():
    router = Router()
    router.add_route(Route(name="a", match=lambda e: True, sink=lambda e: None))
    router.add_route(Route(name="b", match=lambda e: e.level == "error", sink=lambda e: None))
    matched = router.dispatch(_entry(level="info"))
    assert matched == ["a"]


def test_dispatch_stop_halts_after_first_match():
    counts = {"a": 0, "b": 0}
    router = Router()
    router.add_route(Route(name="a", match=lambda e: True, sink=lambda e: counts.__setitem__("a", counts["a"] + 1), stop=True))
    router.add_route(Route(name="b", match=lambda e: True, sink=lambda e: counts.__setitem__("b", counts["b"] + 1)))
    router.dispatch(_entry())
    assert counts["a"] == 1
    assert counts["b"] == 0


def test_dispatch_all_iterates_entries():
    received: List[LogEntry] = []
    router = Router()
    router.add_route(Route(name="all", match=lambda e: True, sink=received.append))
    entries = [_entry(message=f"msg{i}") for i in range(5)]
    router.dispatch_all(entries)
    assert received == entries


def test_multiple_routes_can_both_match():
    a_received: List[LogEntry] = []
    b_received: List[LogEntry] = []
    router = Router()
    router.add_route(Route(name="a", match=lambda e: True, sink=a_received.append))
    router.add_route(Route(name="b", match=lambda e: True, sink=b_received.append))
    entry = _entry()
    router.dispatch(entry)
    assert entry in a_received
    assert entry in b_received
