"""Parse raw Docker log lines into structured log entries."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Optional

_TIMESTAMP_RE = re.compile(
    r"^(?P<timestamp>\d{4}-\d{2}-\d{2}T[\d:.]+Z)\s+(?P<message>.+)$"
)


@dataclass
class LogEntry:
    raw: str
    timestamp: Optional[str] = None
    message: str = ""
    structured: dict = field(default_factory=dict)
    is_json: bool = False

    def __str__(self) -> str:
        ts = f"[{self.timestamp}] " if self.timestamp else ""
        return f"{ts}{self.message}"


def parse_line(raw_line: str) -> LogEntry:
    """Parse a single raw Docker log line into a LogEntry."""
    entry = LogEntry(raw=raw_line)

    match = _TIMESTAMP_RE.match(raw_line)
    if match:
        entry.timestamp = match.group("timestamp")
        body = match.group("message")
    else:
        body = raw_line

    entry.message = body

    # Attempt JSON parsing for structured logs
    stripped = body.strip()
    if stripped.startswith("{") and stripped.endswith("}"):
        try:
            entry.structured = json.loads(stripped)
            entry.is_json = True
            # Prefer 'msg' or 'message' field as the display message
            entry.message = entry.structured.get(
                "msg", entry.structured.get("message", body)
            )
        except json.JSONDecodeError:
            pass

    return entry


def parse_lines(raw_lines: list[str]) -> list[LogEntry]:
    """Parse multiple raw log lines."""
    return [parse_line(line) for line in raw_lines if line.strip()]
