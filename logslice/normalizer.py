"""Normalize log entry fields to consistent formats."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Callable, Optional

from logslice.log_parser import LogEntry


class NormalizerError(ValueError):
    """Raised when a normalization rule is misconfigured."""


@dataclass
class NormalizeRule:
    """A single field-normalization rule."""

    field: str  # 'level', 'service', or 'message'
    transform: Callable[[str], str]

    def __post_init__(self) -> None:
        if not self.field:
            raise NormalizerError("field must not be empty")
        if self.field not in ("level", "service", "message"):
            raise NormalizerError(
                f"field must be 'level', 'service', or 'message', got {self.field!r}"
            )
        if not callable(self.transform):
            raise NormalizerError("transform must be callable")


@dataclass
class Normalizer:
    """Apply a sequence of NormalizeRules to LogEntry objects."""

    rules: list[NormalizeRule] = field(default_factory=list)

    def add_rule(self, rule: NormalizeRule) -> None:
        if not isinstance(rule, NormalizeRule):
            raise NormalizerError("rule must be a NormalizeRule instance")
        self.rules.append(rule)

    def apply(self, entry: LogEntry) -> LogEntry:
        """Return a new LogEntry with all rules applied."""
        level = entry.level
        service = entry.service
        message = entry.message
        extra = dict(entry.extra) if entry.extra else {}

        for rule in self.rules:
            if rule.field == "level":
                level = rule.transform(level) if level else level
            elif rule.field == "service":
                service = rule.transform(service) if service else service
            elif rule.field == "message":
                message = rule.transform(message)

        return LogEntry(
            timestamp=entry.timestamp,
            level=level,
            service=service,
            message=message,
            raw=entry.raw,
            extra=extra,
        )


# ---------- convenience factories ----------

def uppercase_level_rule() -> NormalizeRule:
    """Return a rule that uppercases the level field."""
    return NormalizeRule(field="level", transform=str.upper)


def lowercase_service_rule() -> NormalizeRule:
    """Return a rule that lowercases the service field."""
    return NormalizeRule(field="service", transform=str.lower)


def strip_ansi_rule() -> NormalizeRule:
    """Return a rule that strips ANSI escape codes from the message."""
    _ansi_re = re.compile(r"\x1b\[[0-9;]*m")
    return NormalizeRule(field="message", transform=lambda m: _ansi_re.sub("", m))
