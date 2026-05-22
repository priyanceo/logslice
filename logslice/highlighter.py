"""ANSI color highlighting for log output in the terminal."""

from __future__ import annotations

import re
from enum import Enum
from typing import Optional

from logslice.log_parser import LogEntry


class Color(str, Enum):
    RESET = "\033[0m"
    BOLD = "\033[1m"
    RED = "\033[31m"
    YELLOW = "\033[33m"
    GREEN = "\033[32m"
    CYAN = "\033[36m"
    MAGENTA = "\033[35m"
    DIM = "\033[2m"


LEVEL_COLORS: dict[str, Color] = {
    "error": Color.RED,
    "fatal": Color.RED,
    "warn": Color.YELLOW,
    "warning": Color.YELLOW,
    "info": Color.GREEN,
    "debug": Color.DIM,
    "trace": Color.DIM,
}


def colorize(text: str, color: Color) -> str:
    """Wrap *text* with the given ANSI *color* code."""
    return f"{color.value}{text}{Color.RESET.value}"


def highlight_level(entry: LogEntry) -> str:
    """Return the log level string with an appropriate ANSI color."""
    level = (entry.level or "").lower()
    color = LEVEL_COLORS.get(level, Color.CYAN)
    label = (entry.level or "UNKNOWN").upper().ljust(7)
    return colorize(label, color)


def highlight_term(text: str, term: str, color: Color = Color.MAGENTA) -> str:
    """Case-insensitively highlight all occurrences of *term* in *text*."""
    if not term:
        return text
    pattern = re.compile(re.escape(term), re.IGNORECASE)
    return pattern.sub(lambda m: colorize(m.group(), color), text)


def format_entry(
    entry: LogEntry,
    search_term: Optional[str] = None,
    use_color: bool = True,
) -> str:
    """Format a LogEntry as a single terminal line with optional highlighting."""
    ts = entry.timestamp or ""
    level = highlight_level(entry) if use_color else (entry.level or "UNKNOWN").upper().ljust(7)
    message = entry.message

    if use_color and search_term:
        message = highlight_term(message, search_term)

    ts_part = colorize(ts, Color.DIM) if use_color and ts else ts
    return f"{ts_part}  {level}  {message}"
