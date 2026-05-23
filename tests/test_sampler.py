"""Tests for logslice.sampler."""

from __future__ import annotations

import pytest

from logslice.log_parser import LogEntry
from logslice.sampler import Sampler, SamplerError, nth_sample, rate_sample


def _entry(msg: str = "hello") -> LogEntry:
    return LogEntry(timestamp=None, level="INFO", message=msg, raw=msg, extra={})


@pytest.fixture()
def entries() -> list[LogEntry]:
    return [_entry(f"msg-{i}") for i in range(10)]


# ---------------------------------------------------------------------------
# Sampler validation
# ---------------------------------------------------------------------------

def test_every_nth_zero_raises() -> None:
    with pytest.raises(SamplerError, match="every_nth"):
        Sampler(every_nth=0)


def test_rate_zero_raises() -> None:
    with pytest.raises(SamplerError, match="rate"):
        Sampler(rate=0.0)


def test_rate_above_one_raises() -> None:
    with pytest.raises(SamplerError, match="rate"):
        Sampler(rate=1.1)


# ---------------------------------------------------------------------------
# nth sampling
# ---------------------------------------------------------------------------

def test_every_nth_one_keeps_all(entries: list[LogEntry]) -> None:
    result = list(Sampler(every_nth=1).sample(entries))
    assert len(result) == 10


def test_every_nth_two_keeps_half(entries: list[LogEntry]) -> None:
    result = list(nth_sample(entries, n=2))
    assert len(result) == 5


def test_every_nth_five_keeps_two(entries: list[LogEntry]) -> None:
    result = list(nth_sample(entries, n=5))
    assert len(result) == 2


def test_nth_sample_correct_entries(entries: list[LogEntry]) -> None:
    result = list(nth_sample(entries, n=3))
    # counter starts at 0, increments before check: keeps indices 2, 5, 8
    assert result[0].message == "msg-2"
    assert result[1].message == "msg-5"


# ---------------------------------------------------------------------------
# rate sampling (deterministic via seed)
# ---------------------------------------------------------------------------

def test_rate_one_keeps_all(entries: list[LogEntry]) -> None:
    result = list(rate_sample(entries, rate=1.0))
    assert len(result) == 10


def test_rate_reduces_entries(entries: list[LogEntry]) -> None:
    import random
    random.seed(42)
    result = list(rate_sample(entries, rate=0.3))
    # With seed 42 some entries are dropped; just verify < 10
    assert len(result) < 10


# ---------------------------------------------------------------------------
# Combined nth + rate
# ---------------------------------------------------------------------------

def test_combined_nth_and_rate(entries: list[LogEntry]) -> None:
    import random
    random.seed(0)
    sampler = Sampler(every_nth=2, rate=1.0)
    result = list(sampler.sample(entries))
    assert len(result) == 5  # every 2nd, rate=1 keeps all of those
