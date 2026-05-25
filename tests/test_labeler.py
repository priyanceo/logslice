"""Tests for logslice.labeler."""

from __future__ import annotations

import pytest

from logslice.labeler import LabelRule, Labeler, LabelerError
from logslice.log_parser import LogEntry


def _entry(
    message: str = "hello",
    level: str = "info",
    service: str = "svc",
    extra: dict | None = None,
) -> LogEntry:
    return LogEntry(timestamp="2024-01-01T00:00:00", level=level, message=message, service=service, extra=extra or {})


# ---------------------------------------------------------------------------
# LabelRule validation
# ---------------------------------------------------------------------------

def test_rule_empty_name_raises():
    with pytest.raises(LabelerError, match="name"):
        LabelRule(name="", match=lambda e: True, labels={"k": "v"})


def test_rule_non_callable_match_raises():
    with pytest.raises(LabelerError, match="callable"):
        LabelRule(name="r", match="not-callable", labels={"k": "v"})  # type: ignore[arg-type]


def test_rule_empty_labels_raises():
    with pytest.raises(LabelerError, match="labels"):
        LabelRule(name="r", match=lambda e: True, labels={})


def test_rule_non_string_label_key_raises():
    with pytest.raises(LabelerError, match="keys"):
        LabelRule(name="r", match=lambda e: True, labels={1: "v"})  # type: ignore[dict-item]


def test_rule_non_string_label_value_raises():
    with pytest.raises(LabelerError, match="values"):
        LabelRule(name="r", match=lambda e: True, labels={"k": 42})  # type: ignore[dict-item]


# ---------------------------------------------------------------------------
# Labeler.apply
# ---------------------------------------------------------------------------

def test_no_rules_returns_entry_unchanged():
    labeler = Labeler()
    entry = _entry()
    result = labeler.apply(entry)
    assert result is entry


def test_matching_rule_adds_labels():
    labeler = Labeler()
    labeler.add_rule(LabelRule(name="env", match=lambda e: True, labels={"env": "prod"}))
    result = labeler.apply(_entry())
    assert result.extra.get("env") == "prod"


def test_non_matching_rule_does_not_add_labels():
    labeler = Labeler()
    labeler.add_rule(LabelRule(name="err", match=lambda e: e.level == "error", labels={"alert": "yes"}))
    result = labeler.apply(_entry(level="info"))
    assert "alert" not in result.extra


def test_multiple_matching_rules_merge_labels():
    labeler = Labeler()
    labeler.add_rule(LabelRule(name="r1", match=lambda e: True, labels={"a": "1"}))
    labeler.add_rule(LabelRule(name="r2", match=lambda e: True, labels={"b": "2"}))
    result = labeler.apply(_entry())
    assert result.extra["a"] == "1"
    assert result.extra["b"] == "2"


def test_later_rule_overwrites_earlier_label():
    labeler = Labeler()
    labeler.add_rule(LabelRule(name="r1", match=lambda e: True, labels={"k": "first"}))
    labeler.add_rule(LabelRule(name="r2", match=lambda e: True, labels={"k": "second"}))
    result = labeler.apply(_entry())
    assert result.extra["k"] == "second"


def test_existing_extra_fields_preserved():
    labeler = Labeler()
    labeler.add_rule(LabelRule(name="r", match=lambda e: True, labels={"new": "val"}))
    entry = _entry(extra={"existing": "keep"})
    result = labeler.apply(entry)
    assert result.extra["existing"] == "keep"
    assert result.extra["new"] == "val"


def test_match_exception_raises_labeler_error():
    def bad_match(e: LogEntry) -> bool:
        raise RuntimeError("boom")

    labeler = Labeler()
    labeler.add_rule(LabelRule(name="bad", match=bad_match, labels={"k": "v"}))
    with pytest.raises(LabelerError, match="boom"):
        labeler.apply(_entry())


def test_apply_all_processes_every_entry():
    labeler = Labeler()
    labeler.add_rule(LabelRule(name="tag", match=lambda e: True, labels={"tagged": "yes"}))
    entries = [_entry(message=f"msg{i}") for i in range(4)]
    results = labeler.apply_all(entries)
    assert len(results) == 4
    assert all(r.extra.get("tagged") == "yes" for r in results)
