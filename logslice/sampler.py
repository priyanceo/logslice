"""Log sampling: keep every Nth entry or a random percentage of entries."""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Iterable, Iterator

from logslice.log_parser import LogEntry


class SamplerError(Exception):
    """Raised when sampler configuration is invalid."""


@dataclass
class Sampler:
    """Configurable log entry sampler.

    Attributes:
        every_nth: Keep every Nth entry; 1 means keep all entries.
        rate: Probability in (0.0, 1.0] that a candidate entry is kept
              after the ``every_nth`` filter has passed it.
    """

    every_nth: int = 1          # keep every Nth entry (1 = keep all)
    rate: float = 1.0           # random keep probability in [0.0, 1.0]
    _counter: int = field(default=0, init=False, repr=False)

    def __post_init__(self) -> None:
        if self.every_nth < 1:
            raise SamplerError("every_nth must be >= 1")
        if not (0.0 < self.rate <= 1.0):
            raise SamplerError("rate must be in range (0.0, 1.0]")

    def reset(self) -> None:
        """Reset the internal counter, allowing the sampler to be reused."""
        self._counter = 0

    def should_keep(self, entry: LogEntry) -> bool:  # noqa: ARG002
        """Return True if this entry should be kept."""
        self._counter += 1
        if self._counter % self.every_nth != 0:
            return False
        if self.rate < 1.0 and random.random() > self.rate:
            return False
        return True

    def sample(self, entries: Iterable[LogEntry]) -> Iterator[LogEntry]:
        """Yield entries that pass the sampling criteria."""
        for entry in entries:
            if self.should_keep(entry):
                yield entry


def nth_sample(entries: Iterable[LogEntry], n: int) -> Iterator[LogEntry]:
    """Convenience: yield every Nth entry from *entries*."""
    return Sampler(every_nth=n).sample(entries)


def rate_sample(entries: Iterable[LogEntry], rate: float) -> Iterator[LogEntry]:
    """Convenience: yield entries with probability *rate*."""
    return Sampler(rate=rate).sample(entries)
