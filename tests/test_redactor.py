"""Tests for logslice.redactor."""
from __future__ import annotations

import pytest

from logslice.log_parser import LogEntry
from logslice.redactor import RedactRule, Redactor, RedactorError


def _entry(
    message: str = "hello world",
    level: str = "INFO",
    service: str = "svc",
    extra: dict | None = None,
) -> LogEntry:
    return LogEntry(
        timestamp="2024-01-01T00:00:00Z",
        level=level,
        service=service,
        message=message,
        extra=extra or {},
    )


# --- RedactRule validation ---

def test_rule_empty_name_raises():
    with pytest.raises(RedactorError, match="name"):
        RedactRule(name="", pattern=r"\d+")


def test_rule_empty_pattern_raises():
    with pytest.raises(RedactorError, match="pattern"):
        RedactRule(name="digits", pattern="")


def test_rule_invalid_regex_raises():
    with pytest.raises(RedactorError, match="Invalid regex"):
        RedactRule(name="bad", pattern="[unclosed")


# --- RedactRule.apply ---

def test_rule_replaces_match():
    rule = RedactRule(name="email", pattern=r"[\w.+-]+@[\w-]+\.[\w.]+")
    assert rule.apply("contact user@example.com now") == "contact [REDACTED] now"


def test_rule_custom_replacement():
    rule = RedactRule(name="token", pattern=r"token-\w+", replacement="***")
    assert rule.apply("auth token-abc123 ok") == "auth *** ok"


def test_rule_case_insensitive():
    rule = RedactRule(name="secret", pattern=r"password")
    assert rule.apply("PASSWORD=hunter2") == "[REDACTED]=hunter2"


# --- Redactor ---

def test_redactor_masks_message():
    r = Redactor()
    r.add_rule(RedactRule(name="ip", pattern=r"\d{1,3}(\.\d{1,3}){3}"))
    result = r.apply(_entry(message="request from 192.168.1.1 received"))
    assert "[REDACTED]" in result.message
    assert "192.168.1.1" not in result.message


def test_redactor_leaves_unmatched_message_intact():
    r = Redactor()
    r.add_rule(RedactRule(name="cc", pattern=r"\d{16}"))
    result = r.apply(_entry(message="no card here"))
    assert result.message == "no card here"


def test_redactor_masks_extra_field():
    r = Redactor()
    r.add_rule(RedactRule(name="token", pattern=r"tok_\w+", fields=["auth_token"]))
    entry = _entry(extra={"auth_token": "tok_secret123"})
    result = r.apply(entry)
    assert result.extra["auth_token"] == "[REDACTED]"


def test_redactor_does_not_mutate_original():
    r = Redactor()
    r.add_rule(RedactRule(name="num", pattern=r"\d+"))
    original = _entry(message="error 404 occurred")
    result = r.apply(original)
    assert original.message == "error 404 occurred"
    assert "404" not in result.message


def test_redactor_multiple_rules_applied_in_order():
    r = Redactor()
    r.add_rule(RedactRule(name="email", pattern=r"[\w.+-]+@[\w-]+\.[\w.]+", replacement="[EMAIL]"))
    r.add_rule(RedactRule(name="bracket", pattern=r"\[EMAIL\]", replacement="[MASKED]"))
    result = r.apply(_entry(message="send to user@example.com"))
    assert result.message == "send to [MASKED]"
