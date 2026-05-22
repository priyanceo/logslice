"""Tests for logslice.alerter."""
import time
from unittest.mock import MagicMock

import pytest

from logslice.alerter import AlertEngine, AlertRule
from logslice.log_parser import LogEntry


def _entry(level: str = "ERROR", message: str = "something went wrong") -> LogEntry:
    return LogEntry(timestamp="2024-01-01T00:00:00", level=level, message=message, raw=message)


@pytest.fixture
def engine() -> AlertEngine:
    return AlertEngine()


def test_no_rules_no_callbacks(engine):
    """Processing without rules should not raise."""
    engine.process(_entry())


def test_rule_fires_on_threshold(engine):
    rule = AlertRule(level="ERROR", threshold=1, name="err-rule")
    engine.add_rule(rule)
    callback = MagicMock()
    engine.on_alert(callback)

    engine.process(_entry("ERROR"))

    callback.assert_called_once()
    fired_rule, fired_entry = callback.call_args[0]
    assert fired_rule.name == "err-rule"
    assert fired_entry.level == "ERROR"


def test_rule_does_not_fire_below_threshold(engine):
    rule = AlertRule(level="ERROR", threshold=3, name="high-err")
    engine.add_rule(rule)
    callback = MagicMock()
    engine.on_alert(callback)

    engine.process(_entry("ERROR"))
    engine.process(_entry("ERROR"))

    callback.assert_not_called()


def test_rule_fires_exactly_at_threshold(engine):
    rule = AlertRule(level="WARN", threshold=2, name="warn-rule")
    engine.add_rule(rule)
    callback = MagicMock()
    engine.on_alert(callback)

    engine.process(_entry("WARN", "disk space"))
    engine.process(_entry("WARN", "disk space"))

    assert callback.call_count == 1


def test_rule_resets_after_firing(engine):
    rule = AlertRule(level="ERROR", threshold=1, name="reset-rule")
    engine.add_rule(rule)
    callback = MagicMock()
    engine.on_alert(callback)

    engine.process(_entry("ERROR"))
    engine.process(_entry("ERROR"))

    assert callback.call_count == 2


def test_keyword_filter_skips_non_matching(engine):
    rule = AlertRule(level="ERROR", keyword="timeout", threshold=1)
    engine.add_rule(rule)
    callback = MagicMock()
    engine.on_alert(callback)

    engine.process(_entry("ERROR", "connection refused"))

    callback.assert_not_called()


def test_keyword_filter_matches_case_insensitive(engine):
    rule = AlertRule(level="ERROR", keyword="timeout", threshold=1)
    engine.add_rule(rule)
    callback = MagicMock()
    engine.on_alert(callback)

    engine.process(_entry("ERROR", "Request TIMEOUT exceeded"))

    callback.assert_called_once()


def test_wrong_level_not_counted(engine):
    rule = AlertRule(level="ERROR", threshold=1)
    engine.add_rule(rule)
    callback = MagicMock()
    engine.on_alert(callback)

    engine.process(_entry("INFO", "all good"))

    callback.assert_not_called()
