"""Tests for logslice.correlator."""
from __future__ import annotations

import pytest

from logslice.correlator import CorrelationGroup, Correlator, CorrelatorConfig, CorrelatorError
from logslice.log_parser import LogEntry


def _entry(
    message: str = "hello",
    level: str = "INFO",
    service: str = "svc",
    timestamp: str = "2024-01-01T00:00:00",
    extra: dict | None = None,
) -> LogEntry:
    return LogEntry(
        raw=message,
        message=message,
        level=level,
        service=service,
        timestamp=timestamp,
        extra=extra or {},
    )


# ---------------------------------------------------------------------------
# CorrelatorConfig validation
# ---------------------------------------------------------------------------

def test_config_defaults():
    cfg = CorrelatorConfig()
    assert cfg.field == "trace_id"
    assert cfg.window_seconds == 5.0
    assert cfg.min_group_size == 1


def test_config_negative_window_raises():
    with pytest.raises(CorrelatorError):
        CorrelatorConfig(window_seconds=-1)


def test_config_zero_min_size_raises():
    with pytest.raises(CorrelatorError):
        CorrelatorConfig(min_group_size=0)


# ---------------------------------------------------------------------------
# CorrelationGroup
# ---------------------------------------------------------------------------

def test_group_size_increments():
    g = CorrelationGroup(key="abc")
    g.add(_entry())
    g.add(_entry())
    assert g.size == 2


def test_group_summary_contains_key():
    g = CorrelationGroup(key="xyz")
    g.add(_entry(level="ERROR", service="api"))
    s = g.summary()
    assert s["key"] == "xyz"
    assert s["count"] == 1
    assert "ERROR" in s["levels"]
    assert "api" in s["services"]


# ---------------------------------------------------------------------------
# Correlator.feed — field-based grouping
# ---------------------------------------------------------------------------

def test_feed_groups_by_extra_field():
    c = Correlator(CorrelatorConfig(field="trace_id"))
    c.feed(_entry(extra={"trace_id": "t1"}))
    c.feed(_entry(extra={"trace_id": "t1"}))
    c.feed(_entry(extra={"trace_id": "t2"}))
    groups = {g.key: g for g in c.groups()}
    assert groups["t1"].size == 2
    assert groups["t2"].size == 1


def test_feed_falls_back_to_time_window():
    c = Correlator(CorrelatorConfig(window_seconds=60))
    # same minute → same bucket
    c.feed(_entry(timestamp="2024-01-01T00:00:05"))
    c.feed(_entry(timestamp="2024-01-01T00:00:30"))
    groups = c.groups()
    assert len(groups) == 1
    assert groups[0].size == 2


def test_feed_different_windows_are_separate():
    c = Correlator(CorrelatorConfig(window_seconds=10))
    c.feed(_entry(timestamp="2024-01-01T00:00:00"))
    c.feed(_entry(timestamp="2024-01-01T00:00:11"))
    groups = c.groups()
    assert len(groups) == 2


def test_feed_ungrouped_key_for_no_timestamp():
    c = Correlator()
    c.feed(_entry(timestamp=None))
    keys = [g.key for g in c.groups()]
    assert "ungrouped" in keys


# ---------------------------------------------------------------------------
# min_group_size filtering
# ---------------------------------------------------------------------------

def test_min_group_size_filters_small_groups():
    c = Correlator(CorrelatorConfig(min_group_size=2))
    c.feed(_entry(extra={"trace_id": "lone"}))
    c.feed(_entry(extra={"trace_id": "pair"}))
    c.feed(_entry(extra={"trace_id": "pair"}))
    keys = [g.key for g in c.groups()]
    assert "pair" in keys
    assert "lone" not in keys


def test_reset_clears_all_groups():
    c = Correlator()
    c.feed(_entry(extra={"trace_id": "t1"}))
    c.reset()
    assert c.groups() == []
