"""Tests for logslice.normalizer."""
import pytest

from logslice.log_parser import LogEntry
from logslice.normalizer import (
    NormalizeRule,
    Normalizer,
    NormalizerError,
    lowercase_service_rule,
    strip_ansi_rule,
    uppercase_level_rule,
)


def _entry(
    message: str = "hello world",
    level: str = "info",
    service: str = "MyService",
) -> LogEntry:
    return LogEntry(
        timestamp="2024-01-01T00:00:00Z",
        level=level,
        service=service,
        message=message,
        raw=message,
        extra={},
    )


# ---- NormalizeRule validation ----

def test_rule_empty_field_raises():
    with pytest.raises(NormalizerError, match="field must not be empty"):
        NormalizeRule(field="", transform=str.upper)


def test_rule_invalid_field_raises():
    with pytest.raises(NormalizerError, match="field must be"):
        NormalizeRule(field="timestamp", transform=str.upper)


def test_rule_non_callable_transform_raises():
    with pytest.raises(NormalizerError, match="transform must be callable"):
        NormalizeRule(field="level", transform="upper")  # type: ignore


# ---- Normalizer.apply ----

def test_apply_uppercase_level():
    normalizer = Normalizer(rules=[uppercase_level_rule()])
    result = normalizer.apply(_entry(level="info"))
    assert result.level == "INFO"


def test_apply_lowercase_service():
    normalizer = Normalizer(rules=[lowercase_service_rule()])
    result = normalizer.apply(_entry(service="MyService"))
    assert result.service == "myservice"


def test_apply_strip_ansi_from_message():
    ansi_msg = "\x1b[31mERROR\x1b[0m occurred"
    normalizer = Normalizer(rules=[strip_ansi_rule()])
    result = normalizer.apply(_entry(message=ansi_msg))
    assert result.message == "ERROR occurred"


def test_apply_multiple_rules_in_order():
    normalizer = Normalizer(rules=[uppercase_level_rule(), lowercase_service_rule()])
    result = normalizer.apply(_entry(level="warn", service="BackendAPI"))
    assert result.level == "WARN"
    assert result.service == "backendapi"


def test_apply_preserves_other_fields():
    entry = _entry(message="keep me", level="debug")
    normalizer = Normalizer(rules=[uppercase_level_rule()])
    result = normalizer.apply(entry)
    assert result.message == "keep me"
    assert result.timestamp == entry.timestamp
    assert result.raw == entry.raw


def test_apply_no_rules_returns_equivalent_entry():
    entry = _entry()
    normalizer = Normalizer()
    result = normalizer.apply(entry)
    assert result.level == entry.level
    assert result.service == entry.service
    assert result.message == entry.message


def test_add_rule_rejects_non_rule():
    normalizer = Normalizer()
    with pytest.raises(NormalizerError, match="NormalizeRule instance"):
        normalizer.add_rule("not-a-rule")  # type: ignore


def test_add_rule_appends_and_applies():
    normalizer = Normalizer()
    normalizer.add_rule(uppercase_level_rule())
    result = normalizer.apply(_entry(level="error"))
    assert result.level == "ERROR"
