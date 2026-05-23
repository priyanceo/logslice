"""Enricher: attach extra fields to log entries based on configurable rules."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List

from logslice.log_parser import LogEntry


class EnricherError(Exception):
    """Raised when enricher configuration is invalid."""


@dataclass
class EnrichRule:
    """A single enrichment rule.

    Attributes:
        key:    The extra-field key to set on the log entry.
        derive: Callable that receives a LogEntry and returns the value to set.
    """

    key: str
    derive: Callable[[LogEntry], Any]

    def __post_init__(self) -> None:
        if not self.key:
            raise EnricherError("EnrichRule.key must not be empty")
        if not callable(self.derive):
            raise EnricherError("EnrichRule.derive must be callable")


@dataclass
class Enricher:
    """Applies a list of EnrichRules to log entries."""

    rules: List[EnrichRule] = field(default_factory=list)

    def add_rule(self, rule: EnrichRule) -> None:
        if not isinstance(rule, EnrichRule):
            raise EnricherError("Expected an EnrichRule instance")
        self.rules.append(rule)

    def enrich(self, entry: LogEntry) -> LogEntry:
        """Return the entry with extra fields populated by all rules."""
        for rule in self.rules:
            value = rule.derive(entry)
            entry.extra[rule.key] = value
        return entry

    def enrich_all(self, entries: List[LogEntry]) -> List[LogEntry]:
        """Enrich a sequence of entries in place and return them."""
        return [self.enrich(e) for e in entries]
