"""Replay saved log files through the filter/highlight pipeline."""

from __future__ import annotations

import gzip
import os
from pathlib import Path
from typing import Iterator

from logslice.log_parser import LogEntry, parse_line


class ReplayError(Exception):
    """Raised when a log file cannot be opened or read."""


def _open_file(path: Path):
    """Open a regular or gzip-compressed log file."""
    if path.suffix == ".gz":
        return gzip.open(path, "rt", encoding="utf-8", errors="replace")
    return path.open("r", encoding="utf-8", errors="replace")


def iter_entries(path: Path) -> Iterator[LogEntry]:
    """Yield parsed LogEntry objects from a log file.

    Supports plain text and gzip-compressed files.
    Empty lines are skipped.

    Raises:
        ReplayError: if the file does not exist or cannot be read.
    """
    if not path.exists():
        raise ReplayError(f"File not found: {path}")

    try:
        with _open_file(path) as fh:
            for raw in fh:
                line = raw.rstrip("\n")
                if line.strip():
                    yield parse_line(line)
    except (OSError, EOFError) as exc:
        raise ReplayError(f"Cannot read {path}: {exc}") from exc


def replay(path: Path, filters=None) -> Iterator[LogEntry]:
    """Iterate entries from *path*, applying an optional filter chain.

    Args:
        path: Path to the log file.
        filters: callable ``(LogEntry) -> bool`` or None.

    Yields:
        LogEntry objects that pass the filter.
    """
    for entry in iter_entries(path):
        if filters is None or filters(entry):
            yield entry
