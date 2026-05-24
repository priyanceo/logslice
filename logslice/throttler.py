"""Throttler: suppress repeated identical log messages within a time window."""

from __future__ import annotations

import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

from logslice.log_parser import LogEntry


class ThrottlerError(ValueError):
    """Raised when Throttler is misconfigured."""


@dataclass
class Throttler:
    """Suppress log entries whose message repeats within *window_seconds*.

    After *max_allowed* occurrences inside the window the entry is dropped.
    A *key_fn* extracts the deduplication key from an entry (default: message).
    """

    window_seconds: float
    max_allowed: int = 1
    key_fn: Callable[[LogEntry], str] = field(default=lambda e: e.message)

    # internal state
    _buckets: Dict[str, List[float]] = field(default_factory=dict, init=False, repr=False)

    def __post_init__(self) -> None:
        if self.window_seconds <= 0:
            raise ThrottlerError("window_seconds must be positive")
        if self.max_allowed < 1:
            raise ThrottlerError("max_allowed must be >= 1")
        self._buckets: Dict[str, List[float]] = defaultdict(list)

    def _evict(self, key: str, now: float) -> None:
        """Remove timestamps older than the window."""
        cutoff = now - self.window_seconds
        self._buckets[key] = [t for t in self._buckets[key] if t >= cutoff]

    def allow(self, entry: LogEntry, now: Optional[float] = None) -> bool:
        """Return True if the entry should be forwarded, False if throttled."""
        if now is None:
            now = time.monotonic()
        key = self.key_fn(entry)
        self._evict(key, now)
        if len(self._buckets[key]) < self.max_allowed:
            self._buckets[key].append(now)
            return True
        return False

    def reset(self) -> None:
        """Clear all internal state."""
        self._buckets.clear()
