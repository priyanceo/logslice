"""Field-level masking for sensitive log data."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, List

from logslice.log_parser import LogEntry


class MaskerError(Exception):
    """Raised when a MaskRule is misconfigured."""


@dataclass
class MaskRule:
    name: str
    fields: List[str]
    mask_with: str = "***"
    condition: Callable[[LogEntry], bool] = field(default=lambda _: True)

    def __post_init__(self) -> None:
        if not self.name:
            raise MaskerError("MaskRule name must not be empty")
        if not self.fields:
            raise MaskerError("MaskRule fields must not be empty")
        if not callable(self.condition):
            raise MaskerError("MaskRule condition must be callable")


@dataclass
class Masker:
    _rules: List[MaskRule] = field(default_factory=list, init=False)

    def add_rule(self, rule: MaskRule) -> None:
        if not isinstance(rule, MaskRule):
            raise MaskerError("Expected a MaskRule instance")
        self._rules.append(rule)

    def apply(self, entry: LogEntry) -> LogEntry:
        """Return a new LogEntry with matching fields masked."""
        extra = dict(entry.extra)
        message = entry.message

        for rule in self._rules:
            if not rule.condition(entry):
                continue
            for f in rule.fields:
                if f == "message":
                    message = rule.mask_with
                elif f in extra:
                    extra[f] = rule.mask_with

        return LogEntry(
            timestamp=entry.timestamp,
            level=entry.level,
            service=entry.service,
            message=message,
            extra=extra,
        )

    def apply_all(self, entries: List[LogEntry]) -> List[LogEntry]:
        return [self.apply(e) for e in entries]
