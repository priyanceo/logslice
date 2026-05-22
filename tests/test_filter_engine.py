"""Tests for logslice.filter_engine."""

import pytest

from logslice.log_parser import parse_line
from logslice.filter_engine import (
    exact_filter,
    fuzzy_filter,
    level_filter,
    build_filter_chain,
)


def _make_entries(raw_lines: list[str]):
    return [parse_line(line) for line in raw_lines]


LINES = [
    "2024-01-15T12:00:00Z Connection established to database",
    '2024-01-15T12:00:01Z {"level":"error","msg":"disk full"}',
    "2024-01-15T12:00:02Z User login successful",
    '2024-01-15T12:00:03Z {"level":"info","msg":"cache warmed up"}',
    "2024-01-15T12:00:04Z Disconnected from database",
]


@pytest.fixture
def entries():
    return _make_entries(LINES)


def test_exact_filter_matches(entries):
    result = exact_filter(entries, "database")
    assert len(result) == 2


def test_exact_filter_case_insensitive(entries):
    result = exact_filter(entries, "DATABASE")
    assert len(result) == 2


def test_exact_filter_no_match(entries):
    result = exact_filter(entries, "kubernetes")
    assert result == []


def test_fuzzy_filter_finds_close_match(entries):
    result = fuzzy_filter(entries, "databse", threshold=60)  # typo
    assert any("database" in e.raw.lower() for e in result)


def test_level_filter_returns_errors_only(entries):
    result = level_filter(entries, "error")
    assert len(result) == 1
    assert result[0].structured["msg"] == "disk full"


def test_build_filter_chain_combined(entries):
    chain = build_filter_chain(keyword="cache", level=None)
    result = chain(entries)
    assert len(result) == 1


def test_build_filter_chain_no_filters(entries):
    chain = build_filter_chain()
    assert chain(entries) == entries
