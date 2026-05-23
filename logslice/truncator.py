"""Truncate log entry messages that exceed a configured length."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Iterator

from logslice.log_parser import LogEntry


class TruncatorError(ValueError):
    """Raised when Truncator is misconfigured."""


@dataclass
class Truncator:
    """Shorten log messages that exceed *max_length* characters.

    Parameters
    ----------
    max_length:
        Maximum number of characters to keep from each message.
    ellipsis_str:
        Suffix appended to truncated messages (default ``"..."``).
    fields:
        Additional ``LogEntry.extra`` keys whose values should also be
        truncated.  Useful when structured logs carry a long ``body`` or
        ``detail`` field.
    """

    max_length: int
    ellipsis_str: str = "..."
    fields: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.max_length <= 0:
            raise TruncatorError(
                f"max_length must be a positive integer, got {self.max_length}"
            )
        if len(self.ellipsis_str) >= self.max_length:
            raise TruncatorError(
                "ellipsis_str length must be shorter than max_length"
            )

    def truncate_text(self, text: str) -> str:
        """Return *text* truncated to *max_length*, with ellipsis appended."""
        if len(text) <= self.max_length:
            return text
        keep = self.max_length - len(self.ellipsis_str)
        return text[:keep] + self.ellipsis_str

    def apply(self, entry: LogEntry) -> LogEntry:
        """Return a new :class:`LogEntry` with long fields truncated."""
        new_message = self.truncate_text(entry.message)
        new_extra = dict(entry.extra)
        for key in self.fields:
            if key in new_extra and isinstance(new_extra[key], str):
                new_extra[key] = self.truncate_text(new_extra[key])
        return LogEntry(
            timestamp=entry.timestamp,
            level=entry.level,
            service=entry.service,
            message=new_message,
            extra=new_extra,
        )

    def run(self, entries: Iterable[LogEntry]) -> Iterator[LogEntry]:
        """Yield truncated versions of every entry in *entries*."""
        for entry in entries:
            yield self.apply(entry)
