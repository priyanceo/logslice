"""Redactor: mask sensitive patterns in log entry messages and extra fields."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Callable, List, Optional

from logslice.log_parser import LogEntry


class RedactorError(ValueError):
    """Raised when a redaction rule is misconfigured."""


@dataclass
class RedactRule:
    name: str
    pattern: str
    replacement: str = "[REDACTED]"
    fields: List[str] = field(default_factory=lambda: ["message"])
    _compiled: re.Pattern = field(init=False, repr=False)

    def __post_init__(self) -> None:
        if not self.name:
            raise RedactorError("RedactRule.name must not be empty")
        if not self.pattern:
            raise RedactorError("RedactRule.pattern must not be empty")
        try:
            self._compiled = re.compile(self.pattern, re.IGNORECASE)
        except re.error as exc:
            raise RedactorError(f"Invalid regex pattern '{self.pattern}': {exc}") from exc

    def apply(self, text: str) -> str:
        return self._compiled.sub(self.replacement, text)


class Redactor:
    """Apply a chain of RedactRules to LogEntry objects."""

    def __init__(self) -> None:
        self._rules: List[RedactRule] = []

    def add_rule(self, rule: RedactRule) -> None:
        self._rules.append(rule)

    def apply(self, entry: LogEntry) -> LogEntry:
        """Return a new LogEntry with sensitive data masked."""
        message = entry.message
        extra = dict(entry.extra)

        for rule in self._rules:
            if "message" in rule.fields:
                message = rule.apply(message)
            for key in rule.fields:
                if key != "message" and key in extra:
                    extra[key] = rule.apply(str(extra[key]))

        return LogEntry(
            timestamp=entry.timestamp,
            level=entry.level,
            service=entry.service,
            message=message,
            extra=extra,
        )
