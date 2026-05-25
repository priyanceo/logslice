"""Relevance scorer: assigns a numeric score to log entries based on configurable rules."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, List

from logslice.log_parser import LogEntry


class ScorerError(Exception):
    """Raised when scorer configuration is invalid."""


@dataclass
class ScoreRule:
    """A single scoring rule: if *match* returns True, add *points* to the entry score."""

    name: str
    match: Callable[[LogEntry], bool]
    points: float

    def __post_init__(self) -> None:
        if not self.name:
            raise ScorerError("ScoreRule name must not be empty")
        if not callable(self.match):
            raise ScorerError("ScoreRule match must be callable")
        if self.points == 0:
            raise ScorerError("ScoreRule points must be non-zero")


@dataclass
class Scorer:
    """Applies a list of ScoreRules to a LogEntry and returns the total score."""

    rules: List[ScoreRule] = field(default_factory=list)

    def add_rule(self, rule: ScoreRule) -> None:
        if not isinstance(rule, ScoreRule):
            raise ScorerError(f"Expected ScoreRule, got {type(rule).__name__}")
        self.rules.append(rule)

    def score(self, entry: LogEntry) -> float:
        """Return the cumulative score for *entry*."""
        total = 0.0
        for rule in self.rules:
            try:
                if rule.match(entry):
                    total += rule.points
            except Exception as exc:  # noqa: BLE001
                raise ScorerError(f"Rule '{rule.name}' raised an error: {exc}") from exc
        return total

    def rank(self, entries: List[LogEntry]) -> List[tuple[LogEntry, float]]:
        """Return entries paired with their scores, sorted descending."""
        scored = [(e, self.score(e)) for e in entries]
        scored.sort(key=lambda t: t[1], reverse=True)
        return scored
