"""Log deduplication: suppress repeated identical log lines within a window."""
from __future__ import annotations

import hashlib
from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Callable, Iterable, Iterator, Optional

from logslice.log_parser import LogEntry


@dataclass
class DeduplicatorConfig:
    window_size: int = 256  # max unique hashes to track
    max_repeats: int = 1    # how many times a line may appear before suppression
    on_suppressed: Optional[Callable[[LogEntry, int], None]] = None


class Deduplicator:
    """Suppress duplicate LogEntry lines within a sliding hash window."""

    def __init__(self, config: Optional[DeduplicatorConfig] = None) -> None:
        self._cfg = config or DeduplicatorConfig()
        # OrderedDict used as an ordered set with counts
        self._seen: OrderedDict[str, int] = OrderedDict()

    # ------------------------------------------------------------------
    def _hash(self, entry: LogEntry) -> str:
        raw = (entry.message or "").strip()
        return hashlib.md5(raw.encode(), usedforsecurity=False).hexdigest()

    def should_keep(self, entry: LogEntry) -> bool:
        """Return True if the entry should be forwarded, False if suppressed."""
        key = self._hash(entry)
        count = self._seen.get(key, 0)

        if count < self._cfg.max_repeats:
            self._seen[key] = count + 1
            self._evict()
            return True

        # suppress — still bump count so caller can inspect
        self._seen[key] = count + 1
        if self._cfg.on_suppressed:
            self._cfg.on_suppressed(entry, self._seen[key])
        return False

    def filter(self, entries: Iterable[LogEntry]) -> Iterator[LogEntry]:
        """Yield only non-duplicate entries."""
        for entry in entries:
            if self.should_keep(entry):
                yield entry

    def reset(self) -> None:
        self._seen.clear()

    # ------------------------------------------------------------------
    def _evict(self) -> None:
        """Keep window bounded by removing oldest entries."""
        while len(self._seen) > self._cfg.window_size:
            self._seen.popitem(last=False)
