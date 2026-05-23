"""Unit tests for logslice.splitter."""
from __future__ import annotations

import pytest

from logslice.log_parser import LogEntry
from logslice.splitter import SplitRule, Splitter, SplitterError


def _entry(message: str = "msg", level: str = "info", service: str = "svc") -> LogEntry:
    return LogEntry(timestamp="2024-01-01T00:00:00", level=level, service=service, message=message, raw=message)


# ---------------------------------------------------------------------------
# SplitRule validation
# ---------------------------------------------------------------------------

def test_rule_empty_name_raises() -> None:
    with pytest.raises(SplitterError, match="non-empty"):
        SplitRule(name="", match=lambda e: True)


def test_rule_non_callable_match_raises() -> None:
    with pytest.raises(SplitterError, match="callable"):
        SplitRule(name="errors", match="not_callable")  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Splitter.classify
# ---------------------------------------------------------------------------

def test_classify_returns_first_matching_rule() -> None:
    splitter = Splitter()
    splitter.add_rule(SplitRule(name="errors", match=lambda e: e.level == "error"))
    splitter.add_rule(SplitRule(name="warnings", match=lambda e: e.level == "warn"))

    assert splitter.classify(_entry(level="error")) == "errors"
    assert splitter.classify(_entry(level="warn")) == "warnings"


def test_classify_falls_back_to_catch_all() -> None:
    splitter = Splitter(catch_all="other")
    splitter.add_rule(SplitRule(name="errors", match=lambda e: e.level == "error"))

    assert splitter.classify(_entry(level="info")) == "other"


def test_classify_custom_catch_all_name() -> None:
    splitter = Splitter(catch_all="misc")
    assert splitter.classify(_entry()) == "misc"


# ---------------------------------------------------------------------------
# Splitter.split
# ---------------------------------------------------------------------------

def test_split_partitions_entries() -> None:
    splitter = Splitter(catch_all="default")
    splitter.add_rule(SplitRule(name="errors", match=lambda e: e.level == "error"))

    items = [
        _entry(level="error"),
        _entry(level="info"),
        _entry(level="error"),
    ]
    result = splitter.split(items)

    assert len(result["errors"]) == 2
    assert len(result["default"]) == 1


def test_split_empty_input_returns_empty_dict() -> None:
    splitter = Splitter()
    assert splitter.split([]) == {}


def test_split_all_to_catch_all_when_no_rules() -> None:
    splitter = Splitter(catch_all="everything")
    items = [_entry(), _entry(), _entry()]
    result = splitter.split(items)
    assert result == {"everything": items}


def test_split_keyword_rule() -> None:
    splitter = Splitter()
    splitter.add_rule(SplitRule(name="timeout", match=lambda e: "timeout" in e.message.lower()))

    items = [
        _entry(message="Connection timeout reached"),
        _entry(message="All good"),
    ]
    result = splitter.split(items)
    assert len(result["timeout"]) == 1
    assert len(result["default"]) == 1
