"""Log entry field transformation and redaction utilities."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Callable, List, Optional

from logslice.log_parser import LogEntry


@dataclass
class TransformRule:
    """A single transformation rule applied to a LogEntry field."""

    field: str  # 'message', 'service', 'level', or 'raw'
    pattern: str
    replacement: str
    flags: int = re.IGNORECASE

    def __post_init__(self) -> None:
        self._regex = re.compile(self.pattern, self.flags)

    def apply(self, entry: LogEntry) -> LogEntry:
        original = getattr(entry, self.field, None)
        if original is None:
            return entry
        transformed = self._regex.sub(self.replacement, str(original))
        return LogEntry(
            timestamp=entry.timestamp,
            level=entry.level if self.field != "level" else transformed,
            message=entry.message if self.field != "message" else transformed,
            service=entry.service if self.field != "service" else transformed,
            raw=entry.raw if self.field != "raw" else transformed,
            extra=entry.extra,
        )


class TransformerError(Exception):
    """Raised when a transformation cannot be applied."""


@dataclass
class Transformer:
    """Applies an ordered chain of TransformRules to log entries."""

    rules: List[TransformRule] = field(default_factory=list)

    def add_rule(self, rule: TransformRule) -> None:
        self.rules.append(rule)

    def transform(self, entry: LogEntry) -> LogEntry:
        for rule in self.rules:
            try:
                entry = rule.apply(entry)
            except Exception as exc:  # pragma: no cover
                raise TransformerError(f"Rule failed on field '{rule.field}': {exc}") from exc
        return entry

    def transform_all(self, entries: List[LogEntry]) -> List[LogEntry]:
        return [self.transform(e) for e in entries]


def redact_pattern(pattern: str, replacement: str = "[REDACTED]") -> TransformRule:
    """Convenience factory: redact a regex pattern from the message field."""
    return TransformRule(field="message", pattern=pattern, replacement=replacement)
