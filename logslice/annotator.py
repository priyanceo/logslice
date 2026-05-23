"""Annotator: attach custom tags and metadata to log entries."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

from logslice.log_parser import LogEntry


@dataclass
class AnnotationRule:
    """A rule that adds a tag to matching log entries."""

    tag: str
    match: Callable[[LogEntry], bool]
    value: str = "true"

    def __post_init__(self) -> None:
        if not self.tag:
            raise ValueError("tag must not be empty")
        if not callable(self.match):
            raise TypeError("match must be callable")


class AnnotatorError(Exception):
    """Raised when annotation configuration is invalid."""


class Annotator:
    """Applies a list of AnnotationRules to log entries."""

    def __init__(self, rules: Optional[List[AnnotationRule]] = None) -> None:
        self._rules: List[AnnotationRule] = rules or []

    def add_rule(self, rule: AnnotationRule) -> None:
        if not isinstance(rule, AnnotationRule):
            raise AnnotatorError("Expected an AnnotationRule instance")
        self._rules.append(rule)

    def annotate(self, entry: LogEntry) -> LogEntry:
        """Return a copy of *entry* with matching tags merged into its extra dict."""
        extra: Dict[str, str] = dict(entry.extra or {})
        for rule in self._rules:
            try:
                if rule.match(entry):
                    extra[rule.tag] = rule.value
            except Exception as exc:  # pragma: no cover
                raise AnnotatorError(f"Rule '{rule.tag}' raised: {exc}") from exc
        return LogEntry(
            timestamp=entry.timestamp,
            level=entry.level,
            message=entry.message,
            service=entry.service,
            extra=extra,
        )

    def annotate_all(self, entries: List[LogEntry]) -> List[LogEntry]:
        """Annotate every entry in *entries* and return a new list."""
        return [self.annotate(e) for e in entries]
