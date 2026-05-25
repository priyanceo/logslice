"""Labeler: attach arbitrary key-value labels to log entries based on match rules."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List

from logslice.log_parser import LogEntry


class LabelerError(Exception):
    """Raised when a labeling rule is misconfigured."""


@dataclass
class LabelRule:
    name: str
    match: Callable[[LogEntry], bool]
    labels: Dict[str, str]

    def __post_init__(self) -> None:
        if not self.name:
            raise LabelerError("LabelRule.name must not be empty")
        if not callable(self.match):
            raise LabelerError("LabelRule.match must be callable")
        if not isinstance(self.labels, dict) or not self.labels:
            raise LabelerError("LabelRule.labels must be a non-empty dict")
        for k, v in self.labels.items():
            if not isinstance(k, str) or not k:
                raise LabelerError("All label keys must be non-empty strings")
            if not isinstance(v, str):
                raise LabelerError("All label values must be strings")


@dataclass
class Labeler:
    _rules: List[LabelRule] = field(default_factory=list, init=False)

    def add_rule(self, rule: LabelRule) -> None:
        """Register a labeling rule."""
        self._rules.append(rule)

    def apply(self, entry: LogEntry) -> LogEntry:
        """Apply all matching rules and merge labels into entry.extra."""
        merged: Dict[str, str] = {}
        for rule in self._rules:
            try:
                if rule.match(entry):
                    merged.update(rule.labels)
            except Exception as exc:  # noqa: BLE001
                raise LabelerError(f"Rule '{rule.name}' raised during match: {exc}") from exc

        if merged:
            extra = dict(entry.extra or {})
            extra.update(merged)
            return LogEntry(
                timestamp=entry.timestamp,
                level=entry.level,
                message=entry.message,
                service=entry.service,
                extra=extra,
            )
        return entry

    def apply_all(self, entries: List[LogEntry]) -> List[LogEntry]:
        """Apply labeling to every entry in *entries*."""
        return [self.apply(e) for e in entries]
