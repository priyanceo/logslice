"""Log splitter: fan-out log entries to multiple named output streams based on rules."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, Iterable, List

from logslice.log_parser import LogEntry


class SplitterError(Exception):
    """Raised when splitter configuration is invalid."""


@dataclass
class SplitRule:
    name: str
    match: Callable[[LogEntry], bool]

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise SplitterError("SplitRule name must be a non-empty string")
        if not callable(self.match):
            raise SplitterError("SplitRule match must be callable")


@dataclass
class Splitter:
    """Distributes log entries across named buckets according to ordered rules."""

    rules: List[SplitRule] = field(default_factory=list)
    catch_all: str = "default"

    def add_rule(self, rule: SplitRule) -> None:
        self.rules.append(rule)

    def classify(self, entry: LogEntry) -> str:
        """Return the name of the first matching rule, or the catch-all bucket."""
        for rule in self.rules:
            if rule.match(entry):
                return rule.name
        return self.catch_all

    def split(
        self, entries: Iterable[LogEntry]
    ) -> Dict[str, List[LogEntry]]:
        """Partition *entries* into a dict keyed by bucket name."""
        buckets: Dict[str, List[LogEntry]] = {}
        for entry in entries:
            bucket = self.classify(entry)
            buckets.setdefault(bucket, []).append(entry)
        return buckets
