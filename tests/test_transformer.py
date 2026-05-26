"""Tests for logslice.transformer."""
from __future__ import annotations

import pytest

from logslice.log_parser import LogEntry
from logslice.transformer import (
    TransformRule,
    Transformer,
    TransformerError,
    redact_pattern,
)


def _entry(
    message: str = "hello world",
    level: str = "INFO",
    service: str = "svc",
) -> LogEntry:
    return LogEntry(timestamp=None, level=level, message=message, service=service, raw=message)


# ---------------------------------------------------------------------------
# TransformRule
# ---------------------------------------------------------------------------

def test_rule_replaces_message():
    rule = TransformRule(field="message", pattern=r"world", replacement="earth")
    result = rule.apply(_entry(message="hello world"))
    assert result.message == "hello earth"


def test_rule_is_case_insensitive_by_default():
    rule = TransformRule(field="message", pattern=r"HELLO", replacement="hi")
    result = rule.apply(_entry(message="hello world"))
    assert result.message == "hi world"


def test_rule_replaces_level():
    rule = TransformRule(field="level", pattern=r"INFO", replacement="DEBUG")
    result = rule.apply(_entry(level="INFO"))
    assert result.level == "DEBUG"


def test_rule_replaces_service():
    rule = TransformRule(field="service", pattern=r"svc", replacement="api")
    result = rule.apply(_entry(service="svc"))
    assert result.service == "api"


def test_rule_none_field_returns_entry_unchanged():
    rule = TransformRule(field="service", pattern=r"x", replacement="y")
    entry = LogEntry(timestamp=None, level="INFO", message="msg", service=None, raw="msg")
    result = rule.apply(entry)
    assert result.service is None


# ---------------------------------------------------------------------------
# Transformer
# ---------------------------------------------------------------------------

def test_transformer_applies_rules_in_order():
    t = Transformer()
    t.add_rule(TransformRule(field="message", pattern=r"hello", replacement="hi"))
    t.add_rule(TransformRule(field="message", pattern=r"hi", replacement="hey"))
    result = t.transform(_entry(message="hello world"))
    assert result.message == "hey world"


def test_transformer_no_rules_returns_same_content():
    t = Transformer()
    entry = _entry(message="unchanged")
    result = t.transform(entry)
    assert result.message == "unchanged"


def test_transform_all_applies_to_every_entry():
    t = Transformer()
    t.add_rule(redact_pattern(r"\d+"))
    entries = [_entry(message="order 123"), _entry(message="ref 456")]
    results = t.transform_all(entries)
    assert results[0].message == "order [REDACTED]"
    assert results[1].message == "ref [REDACTED]"


def test_transform_all_empty_list_returns_empty():
    """transform_all should handle an empty entry list gracefully."""
    t = Transformer()
    t.add_rule(redact_pattern(r"\d+"))
    assert t.transform_all([]) == []


# ---------------------------------------------------------------------------
# redact_pattern helper
# ---------------------------------------------------------------------------

def test_redact_pattern_creates_message_rule():
    rule = redact_pattern(r"\d+")
    assert rule.field == "message"
    assert rule.replacement == "[REDACTED]"


def test_redact_pattern_replaces_matched_text():
    rule = redact_pattern(r"\d+")
    result = rule.apply(_entry(message="user id 42 logged in"))
    assert result.message == "user id [REDACTED] logged in"


def test_redact_pattern_no_match_leaves_message_unchanged():
    rule = redact_pattern(r"\d+")
    result = rule.apply(_entry(message="no numbers here"))
    assert result.message == "no numbers here"
