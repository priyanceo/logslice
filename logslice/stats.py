"""Log statistics aggregation for logslice."""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import Iterable, Dict, List

from logslice.log_parser import LogEntry


@dataclass
class LogStats:
    """Aggregated statistics over a collection of log entries."""

    total: int = 0
    by_level: Dict[str, int] = field(default_factory=dict)
    by_service: Dict[str, int] = field(default_factory=dict)
    top_messages: List[tuple] = field(default_factory=list)

    def summary(self) -> str:
        lines = [
            f"Total entries : {self.total}",
            "By level      : "
            + ", ".join(f"{k}={v}" for k, v in sorted(self.by_level.items())),
            "By service    : "
            + ", ".join(f"{k}={v}" for k, v in sorted(self.by_service.items())),
        ]
        if self.top_messages:
            lines.append("Top messages  :")
            for msg, count in self.top_messages:
                lines.append(f"  [{count:>4}] {msg}")
        return "\n".join(lines)


def compute_stats(entries: Iterable[LogEntry], top_n: int = 5) -> LogStats:
    """Compute statistics from an iterable of LogEntry objects."""
    level_counter: Counter = Counter()
    service_counter: Counter = Counter()
    message_counter: Counter = Counter()
    total = 0

    for entry in entries:
        total += 1
        level = (entry.level or "unknown").lower()
        level_counter[level] += 1

        service = entry.extra.get("service") or entry.extra.get("container") or "unknown"
        service_counter[str(service)] += 1

        if entry.message:
            # Truncate long messages for grouping
            key = entry.message[:120]
            message_counter[key] += 1

    return LogStats(
        total=total,
        by_level=dict(level_counter),
        by_service=dict(service_counter),
        top_messages=message_counter.most_common(top_n),
    )
