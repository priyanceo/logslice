"""Live tail module: follow log entries from a stream with optional backfill."""
from __future__ import annotations

from dataclasses import dataclass, field
from collections import deque
from typing import Callable, Iterable, Iterator

from logslice.log_parser import LogEntry


class TailerError(Exception):
    """Raised when Tailer is misconfigured."""


@dataclass
class Tailer:
    """Buffers the last *backfill* entries then yields new ones as they arrive."""

    backfill: int = 0
    on_entry: Callable[[LogEntry], None] | None = None
    _buffer: deque[LogEntry] = field(default_factory=deque, init=False, repr=False)

    def __post_init__(self) -> None:
        if self.backfill < 0:
            raise TailerError("backfill must be >= 0")
        self._buffer = deque(maxlen=self.backfill if self.backfill > 0 else None)

    def feed(self, entries: Iterable[LogEntry]) -> Iterator[LogEntry]:
        """Consume *entries*, yielding each one (and calling on_entry if set)."""
        for entry in entries:
            self._buffer.append(entry)
            if self.on_entry is not None:
                self.on_entry(entry)
            yield entry

    def backfill_entries(self) -> list[LogEntry]:
        """Return the buffered backfill entries collected so far."""
        return list(self._buffer)

    def reset(self) -> None:
        """Clear the internal buffer."""
        self._buffer.clear()
