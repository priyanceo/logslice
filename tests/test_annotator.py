"""Tests for logslice.annotator."""
from __future__ import annotations

import pytest

from logslice.annotator import AnnotationRule, Annotator, AnnotatorError
from logslice.log_parser import LogEntry


def _entry(
    message: str = "hello world",
    level: str = "INFO",
    service: str = "svc",
    extra: dict | None = None,
) -> LogEntry:
    return LogEntry(timestamp="2024-01-01T00:00:00", level=level, message=message, service=service, extra=extra or {})


def test_rule_empty_tag_raises() -> None:
    with pytest.raises(ValueError, match="tag must not be empty"):
        AnnotationRule(tag="", match=lambda e: True)


def test_rule_non_callable_match_raises() -> None:
    with pytest.raises(TypeError, match="match must be callable"):
        AnnotationRule(tag="foo", match="not-callable")  # type: ignore[arg-type]


def test_annotate_adds_tag_when_rule_matches() -> None:
    annotator = Annotator()
    annotator.add_rule(AnnotationRule(tag="greet", match=lambda e: "hello" in e.message, value="yes"))
    result = annotator.annotate(_entry(message="hello world"))
    assert result.extra.get("greet") == "yes"


def test_annotate_skips_tag_when_rule_does_not_match() -> None:
    annotator = Annotator()
    annotator.add_rule(AnnotationRule(tag="greet", match=lambda e: "goodbye" in e.message))
    result = annotator.annotate(_entry(message="hello world"))
    assert "greet" not in result.extra


def test_annotate_preserves_existing_extra() -> None:
    annotator = Annotator()
    annotator.add_rule(AnnotationRule(tag="new", match=lambda e: True, value="1"))
    entry = _entry(extra={"existing": "val"})
    result = annotator.annotate(entry)
    assert result.extra["existing"] == "val"
    assert result.extra["new"] == "1"


def test_annotate_does_not_mutate_original_entry() -> None:
    annotator = Annotator()
    annotator.add_rule(AnnotationRule(tag="x", match=lambda e: True))
    entry = _entry(extra={"a": "b"})
    annotator.annotate(entry)
    assert "x" not in entry.extra


def test_multiple_rules_all_applied() -> None:
    annotator = Annotator()
    annotator.add_rule(AnnotationRule(tag="has_hello", match=lambda e: "hello" in e.message))
    annotator.add_rule(AnnotationRule(tag="has_world", match=lambda e: "world" in e.message))
    result = annotator.annotate(_entry(message="hello world"))
    assert "has_hello" in result.extra
    assert "has_world" in result.extra


def test_annotate_all_returns_same_count() -> None:
    annotator = Annotator()
    entries = [_entry(message=f"msg {i}") for i in range(5)]
    results = annotator.annotate_all(entries)
    assert len(results) == 5


def test_add_rule_rejects_non_rule() -> None:
    annotator = Annotator()
    with pytest.raises(AnnotatorError):
        annotator.add_rule("not-a-rule")  # type: ignore[arg-type]


def test_no_rules_returns_entry_unchanged() -> None:
    annotator = Annotator()
    entry = _entry(extra={"k": "v"})
    result = annotator.annotate(entry)
    assert result.extra == {"k": "v"}
    assert result.message == entry.message
