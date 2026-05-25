"""Sequencer: reorder log entries by timestamp within a sliding buffer window."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterator, List

from logslice.log_parser import LogEntry


class SequencerError(Exception):
    """Raised for invalid sequencer configuration."""


@dataclass
class Sequencer:
    """Buffer log entries and emit them in timestamp order.

    Args:
        buffer_size: Maximum number of entries to hold before flushing the
                     oldest entry.  Must be >= 1.
    """

    buffer_size: int = 50
    _buffer: List[LogEntry] = field(default_factory=list, init=False, repr=False)

    def __post_init__(self) -> None:
        if self.buffer_size < 1:
            raise SequencerError("buffer_size must be >= 1")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def push(self, entry: LogEntry) -> Iterator[LogEntry]:
        """Add *entry* to the buffer and yield any entries that are ready.

        An entry is considered ready when the buffer exceeds *buffer_size*;
        the oldest entry (by timestamp, falling back to insertion order) is
        evicted and yielded.
        """
        self._buffer.append(entry)
        self._buffer.sort(key=_sort_key)

        while len(self._buffer) > self.buffer_size:
            yield self._buffer.pop(0)

    def flush(self) -> Iterator[LogEntry]:
        """Drain all remaining buffered entries in order."""
        self._buffer.sort(key=_sort_key)
        while self._buffer:
            yield self._buffer.pop(0)

    @property
    def pending(self) -> int:
        """Number of entries currently held in the buffer."""
        return len(self._buffer)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _sort_key(entry: LogEntry):
    """Primary sort key: timestamp string (lexicographic ISO-8601 is fine)."""
    return entry.timestamp or ""
