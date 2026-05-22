"""Fuzzy and exact filtering of log entries."""

from __future__ import annotations

from typing import Callable, Optional

from thefuzz import fuzz

from logslice.log_parser import LogEntry

DEFAULT_FUZZY_THRESHOLD = 60


def exact_filter(entries: list[LogEntry], keyword: str) -> list[LogEntry]:
    """Return entries whose message contains *keyword* (case-insensitive)."""
    kw = keyword.lower()
    return [e for e in entries if kw in e.message.lower()]


def fuzzy_filter(
    entries: list[LogEntry],
    keyword: str,
    threshold: int = DEFAULT_FUZZY_THRESHOLD,
) -> list[LogEntry]:
    """Return entries that fuzzy-match *keyword* above the given threshold."""
    results: list[LogEntry] = []
    for entry in entries:
        score = fuzz.partial_ratio(keyword.lower(), entry.message.lower())
        if score >= threshold:
            results.append(entry)
    return results


def level_filter(entries: list[LogEntry], level: str) -> list[LogEntry]:
    """Filter structured log entries by log level field."""
    target = level.lower()
    filtered = []
    for entry in entries:
        if entry.is_json:
            entry_level = str(
                entry.structured.get("level", entry.structured.get("severity", ""))
            ).lower()
            if entry_level == target:
                filtered.append(entry)
    return filtered


def build_filter_chain(
    keyword: Optional[str] = None,
    fuzzy: bool = False,
    level: Optional[str] = None,
    threshold: int = DEFAULT_FUZZY_THRESHOLD,
) -> Callable[[list[LogEntry]], list[LogEntry]]:
    """Compose a filter pipeline and return it as a single callable."""

    def apply(entries: list[LogEntry]) -> list[LogEntry]:
        result = entries
        if keyword:
            result = fuzzy_filter(result, keyword, threshold) if fuzzy else exact_filter(result, keyword)
        if level:
            result = level_filter(result, level)
        return result

    return apply
