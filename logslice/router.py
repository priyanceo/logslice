"""Route log entries to different outputs based on matching rules."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, List, Optional

from logslice.log_parser import LogEntry


class RouterError(Exception):
    """Raised when a routing rule is misconfigured."""


@dataclass
class Route:
    """A single routing rule: if *match* returns True, call *sink* with the entry."""

    name: str
    match: Callable[[LogEntry], bool]
    sink: Callable[[LogEntry], None]
    stop: bool = False  # if True, do not evaluate further routes after a match

    def __post_init__(self) -> None:
        if not self.name:
            raise RouterError("Route name must not be empty.")
        if not callable(self.match):
            raise RouterError("Route 'match' must be callable.")
        if not callable(self.sink):
            raise RouterError("Route 'sink' must be callable.")


@dataclass
class Router:
    """Evaluate a list of routes against each log entry."""

    routes: List[Route] = field(default_factory=list)

    def add_route(self, route: Route) -> None:
        self.routes.append(route)

    def dispatch(self, entry: LogEntry) -> List[str]:
        """Send *entry* to every matching sink. Return names of matched routes."""
        matched: List[str] = []
        for route in self.routes:
            if route.match(entry):
                route.sink(entry)
                matched.append(route.name)
                if route.stop:
                    break
        return matched

    def dispatch_all(self, entries: List[LogEntry]) -> None:
        for entry in entries:
            self.dispatch(entry)
