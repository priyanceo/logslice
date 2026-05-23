"""Rate limiter for log entry throughput control."""
from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass, field
from typing import Iterable, Iterator

from logslice.log_parser import LogEntry


class RateLimiterError(ValueError):
    """Raised when RateLimiter is misconfigured."""


@dataclass
class RateLimiter:
    """Allow at most *max_per_second* entries through per sliding window."""

    max_per_second: float
    _timestamps: deque = field(default_factory=deque, init=False, repr=False)

    def __post_init__(self) -> None:
        if self.max_per_second <= 0:
            raise RateLimiterError(
                f"max_per_second must be positive, got {self.max_per_second}"
            )

    def _evict_old(self, now: float) -> None:
        cutoff = now - 1.0
        while self._timestamps and self._timestamps[0] < cutoff:
            self._timestamps.popleft()

    def allow(self, now: float | None = None) -> bool:
        """Return True if the entry should be passed through."""
        if now is None:
            now = time.monotonic()
        self._evict_old(now)
        if len(self._timestamps) < self.max_per_second:
            self._timestamps.append(now)
            return True
        return False

    def filter(self, entries: Iterable[LogEntry]) -> Iterator[LogEntry]:
        """Yield entries that fall within the allowed rate."""
        for entry in entries:
            if self.allow():
                yield entry


def apply_rate_limit(
    entries: Iterable[LogEntry], max_per_second: float
) -> Iterator[LogEntry]:
    """Convenience wrapper: create a RateLimiter and apply it."""
    limiter = RateLimiter(max_per_second=max_per_second)
    yield from limiter.filter(entries)
