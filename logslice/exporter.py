"""Export filtered log entries to various output formats."""

from __future__ import annotations

import csv
import io
import json
from enum import Enum
from typing import Iterable

from logslice.log_parser import LogEntry


class ExportFormat(str, Enum):
    JSON = "json"
    CSV = "csv"
    TEXT = "text"


class ExportError(Exception):
    """Raised when an export operation fails."""


def export_json(entries: Iterable[LogEntry]) -> str:
    """Serialize log entries as a JSON array."""
    records = []
    for entry in entries:
        records.append(
            {
                "timestamp": entry.timestamp,
                "level": entry.level,
                "message": entry.message,
                "raw": entry.raw,
            }
        )
    return json.dumps(records, indent=2, default=str)


def export_csv(entries: Iterable[LogEntry]) -> str:
    """Serialize log entries as CSV with headers."""
    output = io.StringIO()
    fieldnames = ["timestamp", "level", "message", "raw"]
    writer = csv.DictWriter(output, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    for entry in entries:
        writer.writerow(
            {
                "timestamp": entry.timestamp or "",
                "level": entry.level or "",
                "message": entry.message,
                "raw": entry.raw,
            }
        )
    return output.getvalue()


def export_text(entries: Iterable[LogEntry]) -> str:
    """Serialize log entries as plain text lines."""
    return "\n".join(str(entry) for entry in entries)


def export_entries(entries: Iterable[LogEntry], fmt: ExportFormat | str) -> str:
    """Dispatch export to the appropriate formatter.

    Args:
        entries: Iterable of LogEntry objects to export.
        fmt: Target format (json, csv, or text).

    Returns:
        Formatted string representation of the entries.

    Raises:
        ExportError: If the format is unsupported.
    """
    fmt = ExportFormat(fmt)
    if fmt == ExportFormat.JSON:
        return export_json(entries)
    if fmt == ExportFormat.CSV:
        return export_csv(entries)
    if fmt == ExportFormat.TEXT:
        return export_text(entries)
    raise ExportError(f"Unsupported export format: {fmt}")
