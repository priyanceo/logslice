"""Tests for logslice.classifier."""
from __future__ import annotations

import pytest

from logslice.classifier import Classifier, ClassifierError, ClassifyRule
from logslice.log_parser import LogEntry


def _entry(message: str, level: str = "info", service: str = "svc") -> LogEntry:
    return LogEntry(timestamp="2024-01-01T00:00:00", level=level, service=service, message=message)


# ---------------------------------------------------------------------------
# ClassifyRule validation
# ---------------------------------------------------------------------------

def test_rule_empty_name_raises():
    with pytest.raises(ClassifierError, match="name"):
        ClassifyRule(name="", match=lambda e: True, category="cat")


def test_rule_non_callable_match_raises():
    with pytest.raises(ClassifierError, match="callable"):
        ClassifyRule(name="r", match="not_callable", category="cat")  # type: ignore[arg-type]


def test_rule_empty_category_raises():
    with pytest.raises(ClassifierError, match="category"):
        ClassifyRule(name="r", match=lambda e: True, category="")


# ---------------------------------------------------------------------------
# Classifier.add_rule
# ---------------------------------------------------------------------------

def test_add_non_rule_raises():
    clf = Classifier()
    with pytest.raises(ClassifierError, match="ClassifyRule"):
        clf.add_rule("not-a-rule")  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Classifier.classify
# ---------------------------------------------------------------------------

def test_classify_returns_first_matching_category():
    clf = Classifier()
    clf.add_rule(ClassifyRule("error-rule", lambda e: "error" in e.message.lower(), "error"))
    clf.add_rule(ClassifyRule("warn-rule", lambda e: "warn" in e.message.lower(), "warning"))

    entry = _entry("An error occurred")
    assert clf.classify(entry) == "error"


def test_classify_falls_back_to_default():
    clf = Classifier(default_category="misc")
    clf.add_rule(ClassifyRule("error-rule", lambda e: "error" in e.message.lower(), "error"))

    entry = _entry("Everything is fine")
    assert clf.classify(entry) == "misc"


def test_classify_no_rules_returns_default():
    clf = Classifier(default_category="unknown")
    assert clf.classify(_entry("hello")) == "unknown"


def test_classify_skips_raising_match():
    """A rule whose match() raises should be skipped gracefully."""
    clf = Classifier(default_category="safe")

    def bad_match(e: LogEntry) -> bool:
        raise RuntimeError("boom")

    clf.add_rule(ClassifyRule("bad", bad_match, "danger"))
    assert clf.classify(_entry("test")) == "safe"


# ---------------------------------------------------------------------------
# Classifier.classify_all
# ---------------------------------------------------------------------------

def test_classify_all_returns_pairs():
    clf = Classifier(default_category="other")
    clf.add_rule(ClassifyRule("err", lambda e: e.level == "error", "error"))

    entries = [_entry("ok", level="info"), _entry("fail", level="error")]
    result = clf.classify_all(entries)

    assert len(result) == 2
    assert result[0] == (entries[0], "other")
    assert result[1] == (entries[1], "error")
