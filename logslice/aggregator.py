"""Time-window aggregation of log entries."""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, Iterable, List, Optional

from logslice.log_parser import LogEntry


@dataclass
class WindowBucket:
    """Aggregated counts for a single time window."""
    window_start: datetime
    window_end: datetime
    total: int = 0
    by_level: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    by_service: Dict[str, int] = field(default_factory=lambda: defaultdict(int))

    def record(self, entry: LogEntry) -> None:
        self.total += 1
        level = (entry.level or "unknown").lower()
        self.by_level[level] += 1
        service = entry.service or "unknown"
        self.by_service[service] += 1

    def summary(self) -> str:
        start = self.window_start.strftime("%H:%M:%S")
        end = self.window_end.strftime("%H:%M:%S")
        levels = ", ".join(f"{k}={v}" for k, v in sorted(self.by_level.items()))
        return f"[{start}-{end}] total={self.total} levels=({levels})"


class AggregatorError(Exception):
    """Raised when aggregation configuration is invalid."""


@dataclass
class Aggregator:
    """Aggregate log entries into fixed-size time windows."""
    window_seconds: int = 60
    _buckets: List[WindowBucket] = field(default_factory=list, init=False)

    def __post_init__(self) -> None:
        if self.window_seconds <= 0:
            raise AggregatorError("window_seconds must be a positive integer")

    def _bucket_for(self, ts: datetime) -> WindowBucket:
        epoch = datetime(1970, 1, 1)
        slot = int((ts - epoch).total_seconds() // self.window_seconds)
        window_start = epoch + timedelta(seconds=slot * self.window_seconds)
        window_end = window_start + timedelta(seconds=self.window_seconds)
        for bucket in self._buckets:
            if bucket.window_start == window_start:
                return bucket
        bucket = WindowBucket(window_start=window_start, window_end=window_end)
        self._buckets.append(bucket)
        self._buckets.sort(key=lambda b: b.window_start)
        return bucket

    def feed(self, entries: Iterable[LogEntry]) -> None:
        for entry in entries:
            ts = entry.timestamp or datetime.utcnow()
            self._bucket_for(ts).record(entry)

    def buckets(self) -> List[WindowBucket]:
        return list(self._buckets)

    def reset(self) -> None:
        self._buckets.clear()
