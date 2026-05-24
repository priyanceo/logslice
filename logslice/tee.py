"""Tee — broadcast each log entry to multiple sinks simultaneously."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Iterable, List

from logslice.log_parser import LogEntry


class TeeError(Exception):
    """Raised when a Tee is misconfigured."""


@dataclass
class TeeSink:
    """A named output channel for the tee."""

    name: str
    sink: Callable[[LogEntry], None]

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise TeeError("TeeSink name must not be empty.")
        if not callable(self.sink):
            raise TeeError(f"TeeSink '{self.name}' sink must be callable.")


@dataclass
class Tee:
    """Broadcasts each entry to all registered sinks.

    If *fail_fast* is True any exception raised by a sink propagates
    immediately.  When False, all sinks are called and a summary
    TeeError is raised at the end if any failed.
    """

    fail_fast: bool = True
    _sinks: List[TeeSink] = field(default_factory=list, init=False, repr=False)

    def add_sink(self, name: str, sink: Callable[[LogEntry], None]) -> None:
        """Register a new sink."""
        self._sinks.append(TeeSink(name=name, sink=sink))

    def dispatch(self, entry: LogEntry) -> None:
        """Send *entry* to every registered sink."""
        errors: list[str] = []
        for ts in self._sinks:
            try:
                ts.sink(entry)
            except Exception as exc:  # noqa: BLE001
                if self.fail_fast:
                    raise TeeError(
                        f"Sink '{ts.name}' raised an error: {exc}"
                    ) from exc
                errors.append(f"'{ts.name}': {exc}")
        if errors:
            raise TeeError("One or more sinks failed: " + "; ".join(errors))

    def run(self, entries: Iterable[LogEntry]) -> None:
        """Dispatch every entry in *entries* to all sinks."""
        for entry in entries:
            self.dispatch(entry)
