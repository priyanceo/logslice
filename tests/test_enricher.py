"""Tests for logslice.enricher."""

from __future__ import annotations

import pytest

from logslice.enricher import EnrichRule, Enricher, EnricherError
from logslice.log_parser import LogEntry


def _entry(**kwargs) -> LogEntry:
    defaults = dict(timestamp="2024-01-01T00:00:00", level="info",
                    message="hello", service="svc", raw="hello", extra={})
    defaults.update(kwargs)
    return LogEntry(**defaults)


# --- EnrichRule validation ---

def test_rule_empty_key_raises():
    with pytest.raises(EnricherError, match="key"):
        EnrichRule(key="", derive=lambda e: None)


def test_rule_non_callable_derive_raises():
    with pytest.raises(EnricherError, match="callable"):
        EnrichRule(key="env", derive="production")  # type: ignore[arg-type]


# --- Enricher.enrich ---

def test_enrich_adds_field():
    enricher = Enricher()
    enricher.add_rule(EnrichRule(key="env", derive=lambda e: "prod"))
    entry = _entry()
    result = enricher.enrich(entry)
    assert result.extra["env"] == "prod"


def test_enrich_multiple_rules():
    enricher = Enricher()
    enricher.add_rule(EnrichRule(key="host", derive=lambda e: "box1"))
    enricher.add_rule(EnrichRule(key="region", derive=lambda e: "eu-west"))
    entry = _entry()
    enricher.enrich(entry)
    assert entry.extra["host"] == "box1"
    assert entry.extra["region"] == "eu-west"


def test_enrich_derives_from_entry():
    enricher = Enricher()
    enricher.add_rule(EnrichRule(key="upper_msg", derive=lambda e: e.message.upper()))
    entry = _entry(message="hello world")
    enricher.enrich(entry)
    assert entry.extra["upper_msg"] == "HELLO WORLD"


def test_enrich_all_processes_every_entry():
    enricher = Enricher()
    enricher.add_rule(EnrichRule(key="tagged", derive=lambda e: True))
    entries = [_entry(message=f"msg {i}") for i in range(5)]
    results = enricher.enrich_all(entries)
    assert len(results) == 5
    assert all(e.extra.get("tagged") is True for e in results)


def test_enrich_no_rules_leaves_extra_unchanged():
    enricher = Enricher()
    entry = _entry(extra={"existing": "value"})
    enricher.enrich(entry)
    assert entry.extra == {"existing": "value"}


def test_add_rule_rejects_non_rule():
    enricher = Enricher()
    with pytest.raises(EnricherError):
        enricher.add_rule("not a rule")  # type: ignore[arg-type]


def test_enrich_overwrites_existing_key():
    enricher = Enricher()
    enricher.add_rule(EnrichRule(key="env", derive=lambda e: "staging"))
    entry = _entry(extra={"env": "prod"})
    enricher.enrich(entry)
    assert entry.extra["env"] == "staging"
