"""Tests for logslice.masker."""
from __future__ import annotations

import pytest

from logslice.log_parser import LogEntry
from logslice.masker import MaskRule, Masker, MaskerError


def _entry(**kwargs) -> LogEntry:
    defaults = dict(
        timestamp="2024-01-01T00:00:00Z",
        level="info",
        service="svc",
        message="hello world",
        extra={},
    )
    defaults.update(kwargs)
    return LogEntry(**defaults)


# --- MaskRule validation ---

def test_rule_empty_name_raises():
    with pytest.raises(MaskerError, match="name"):
        MaskRule(name="", fields=["message"])


def test_rule_empty_fields_raises():
    with pytest.raises(MaskerError, match="fields"):
        MaskRule(name="r", fields=[])


def test_rule_non_callable_condition_raises():
    with pytest.raises(MaskerError, match="callable"):
        MaskRule(name="r", fields=["message"], condition="not-callable")  # type: ignore


# --- Masker.add_rule ---

def test_add_non_rule_raises():
    m = Masker()
    with pytest.raises(MaskerError):
        m.add_rule("bad")  # type: ignore


# --- apply: message field ---

def test_mask_message_field():
    m = Masker()
    m.add_rule(MaskRule(name="r", fields=["message"]))
    result = m.apply(_entry(message="secret"))
    assert result.message == "***"


def test_mask_custom_replacement():
    m = Masker()
    m.add_rule(MaskRule(name="r", fields=["message"], mask_with="[REDACTED]"))
    result = m.apply(_entry(message="secret"))
    assert result.message == "[REDACTED]"


# --- apply: extra fields ---

def test_mask_extra_field():
    m = Masker()
    m.add_rule(MaskRule(name="r", fields=["token"]))
    entry = _entry(extra={"token": "abc123", "user": "alice"})
    result = m.apply(entry)
    assert result.extra["token"] == "***"
    assert result.extra["user"] == "alice"


def test_missing_extra_field_is_ignored():
    m = Masker()
    m.add_rule(MaskRule(name="r", fields=["missing_field"]))
    entry = _entry(extra={"other": "val"})
    result = m.apply(entry)
    assert result.extra == {"other": "val"}


# --- condition ---

def test_condition_skips_non_matching_entry():
    m = Masker()
    m.add_rule(
        MaskRule(name="r", fields=["message"],
                 condition=lambda e: e.level == "error")
    )
    entry = _entry(level="info", message="keep me")
    result = m.apply(entry)
    assert result.message == "keep me"


def test_condition_masks_matching_entry():
    m = Masker()
    m.add_rule(
        MaskRule(name="r", fields=["message"],
                 condition=lambda e: e.level == "error")
    )
    entry = _entry(level="error", message="secret")
    result = m.apply(entry)
    assert result.message == "***"


# --- apply_all ---

def test_apply_all_processes_every_entry():
    m = Masker()
    m.add_rule(MaskRule(name="r", fields=["message"]))
    entries = [_entry(message="a"), _entry(message="b")]
    results = m.apply_all(entries)
    assert all(r.message == "***" for r in results)
    assert len(results) == 2


# --- original entry is not mutated ---

def test_original_entry_not_mutated():
    m = Masker()
    m.add_rule(MaskRule(name="r", fields=["message"]))
    entry = _entry(message="original")
    m.apply(entry)
    assert entry.message == "original"
