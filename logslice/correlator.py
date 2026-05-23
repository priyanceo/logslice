"""Log correlation: group related entries by trace/request ID or time proximity."""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from logslice.log_parser import LogEntry


class CorrelatorError(ValueError):
    """Raised for invalid correlator configuration."""


@dataclass
class CorrelationGroup:
    key: str
    entries: List[LogEntry] = field(default_factory=list)

    def add(self, entry: LogEntry) -> None:
        self.entries.append(entry)

    @property
    def size(self) -> int:
        return len(self.entries)

    def summary(self) -> Dict:
        levels = defaultdict(int)
        services = set()
        for e in self.entries:
            levels[e.level or "unknown"] += 1
            if e.service:
                services.add(e.service)
        return {
            "key": self.key,
            "count": self.size,
            "levels": dict(levels),
            "services": sorted(services),
        }


@dataclass
class CorrelatorConfig:
    field: str = "trace_id"          # extra field to group by
    window_seconds: float = 5.0       # fallback time-window grouping in seconds
    min_group_size: int = 1           # ignore groups smaller than this

    def __post_init__(self) -> None:
        if self.window_seconds <= 0:
            raise CorrelatorError("window_seconds must be positive")
        if self.min_group_size < 1:
            raise CorrelatorError("min_group_size must be >= 1")


class Correlator:
    """Groups log entries by a shared field value or by time proximity."""

    def __init__(self, config: Optional[CorrelatorConfig] = None) -> None:
        self._cfg = config or CorrelatorConfig()
        self._groups: Dict[str, CorrelationGroup] = {}

    def feed(self, entry: LogEntry) -> str:
        """Add *entry* to a group; return the group key used."""
        key = self._resolve_key(entry)
        if key not in self._groups:
            self._groups[key] = CorrelationGroup(key=key)
        self._groups[key].add(entry)
        return key

    def groups(self) -> List[CorrelationGroup]:
        """Return groups that meet min_group_size."""
        return [
            g for g in self._groups.values()
            if g.size >= self._cfg.min_group_size
        ]

    def reset(self) -> None:
        self._groups.clear()

    # ------------------------------------------------------------------
    def _resolve_key(self, entry: LogEntry) -> str:
        # 1. Try the configured extra field
        if entry.extra and self._cfg.field in entry.extra:
            return str(entry.extra[self._cfg.field])
        # 2. Fall back to time-window bucket
        if entry.timestamp:
            try:
                ts = datetime.fromisoformat(entry.timestamp)
                bucket = int(ts.timestamp() / self._cfg.window_seconds)
                return f"window:{bucket}"
            except ValueError:
                pass
        return "ungrouped"
