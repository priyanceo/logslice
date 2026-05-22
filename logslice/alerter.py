"""Alert engine: trigger callbacks when log entries match threshold rules."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, List, Optional

from logslice.log_parser import LogEntry


@dataclass
class AlertRule:
    """A single alert rule based on log level and optional keyword."""

    level: str
    keyword: Optional[str] = None
    threshold: int = 1
    window: int = 60  # seconds; 0 means no time window
    name: str = "unnamed"


@dataclass
class AlertState:
    """Tracks hit count for a single rule."""

    rule: AlertRule
    hits: List[float] = field(default_factory=list)  # timestamps of hits

    def record(self, timestamp: float) -> None:
        if self.rule.window > 0:
            cutoff = timestamp - self.rule.window
            self.hits = [t for t in self.hits if t >= cutoff]
        self.hits.append(timestamp)

    @property
    def count(self) -> int:
        return len(self.hits)

    def triggered(self) -> bool:
        return self.count >= self.rule.threshold


AlertCallback = Callable[[AlertRule, LogEntry], None]


class AlertEngine:
    """Evaluates log entries against registered rules and fires callbacks."""

    def __init__(self) -> None:
        self._states: List[AlertState] = []
        self._callbacks: List[AlertCallback] = []

    def add_rule(self, rule: AlertRule) -> None:
        self._states.append(AlertState(rule=rule))

    def on_alert(self, callback: AlertCallback) -> None:
        self._callbacks.append(callback)

    def process(self, entry: LogEntry) -> None:
        import time

        ts = time.time()
        for state in self._states:
            rule = state.rule
            if entry.level.upper() != rule.level.upper():
                continue
            if rule.keyword and rule.keyword.lower() not in entry.message.lower():
                continue
            state.record(ts)
            if state.triggered():
                for cb in self._callbacks:
                    cb(rule, entry)
                state.hits.clear()  # reset after firing
