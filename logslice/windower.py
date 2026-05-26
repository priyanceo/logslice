"""Sliding and tumbling window grouping for log entries."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Iterator, List

from logslice.log_parser import LogEntry


class WindowerError(Exception):
    """Raised when Windower is misconfigured."""


@dataclass
class Window:
    """A single time window holding a batch of log entries."""

    start: datetime
    end: datetime
    entries: List[LogEntry] = field(default_factory=list)

    def add(self, entry: LogEntry) -> None:
        self.entries.append(entry)

    @property
    def size(self) -> int:
        return len(self.entries)

    def summary(self) -> dict:
        levels: dict[str, int] = {}
        for e in self.entries:
            lvl = (e.level or "unknown").lower()
            levels[lvl] = levels.get(lvl, 0) + 1
        return {
            "start": self.start.isoformat(),
            "end": self.end.isoformat(),
            "total": self.size,
            "levels": levels,
        }


@dataclass
class Windower:
    """Groups log entries into fixed-size tumbling time windows."""

    window_seconds: int = 60
    _windows: List[Window] = field(default_factory=list, init=False)
    _current: Window | None = field(default=None, init=False)

    def __post_init__(self) -> None:
        if self.window_seconds <= 0:
            raise WindowerError("window_seconds must be a positive integer")

    def _make_window(self, start: datetime) -> Window:
        end = start + timedelta(seconds=self.window_seconds)
        return Window(start=start, end=end)

    def push(self, entry: LogEntry) -> None:
        """Add an entry to the appropriate window."""
        ts = entry.timestamp or datetime.utcnow()
        if self._current is None:
            self._current = self._make_window(ts)
        if ts >= self._current.end:
            self._windows.append(self._current)
            self._current = self._make_window(ts)
        self._current.add(entry)

    def flush(self) -> None:
        """Close the current open window and store it."""
        if self._current is not None and self._current.size > 0:
            self._windows.append(self._current)
            self._current = None

    def windows(self) -> Iterator[Window]:
        """Yield all completed windows plus the current one if non-empty."""
        yield from self._windows
        if self._current and self._current.size > 0:
            yield self._current
