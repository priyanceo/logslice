"""Log entry classifier: assigns a category to each entry based on configurable rules."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, List, Optional

from logslice.log_parser import LogEntry


class ClassifierError(Exception):
    """Raised when classifier configuration is invalid."""


@dataclass
class ClassifyRule:
    name: str
    match: Callable[[LogEntry], bool]
    category: str

    def __post_init__(self) -> None:
        if not self.name:
            raise ClassifierError("Rule name must not be empty.")
        if not callable(self.match):
            raise ClassifierError("Rule 'match' must be callable.")
        if not self.category:
            raise ClassifierError("Rule 'category' must not be empty.")


@dataclass
class Classifier:
    default_category: str = "uncategorized"
    _rules: List[ClassifyRule] = field(default_factory=list, init=False, repr=False)

    def add_rule(self, rule: ClassifyRule) -> None:
        if not isinstance(rule, ClassifyRule):
            raise ClassifierError("Expected a ClassifyRule instance.")
        self._rules.append(rule)

    def classify(self, entry: LogEntry) -> str:
        """Return the category of the first matching rule, or the default."""
        for rule in self._rules:
            try:
                if rule.match(entry):
                    return rule.category
            except Exception:
                continue
        return self.default_category

    def classify_all(self, entries: List[LogEntry]) -> List[tuple[LogEntry, str]]:
        """Return (entry, category) pairs for every entry."""
        return [(e, self.classify(e)) for e in entries]
