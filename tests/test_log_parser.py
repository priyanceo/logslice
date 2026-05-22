"""Tests for logslice.log_parser."""

import json
import pytest

from logslice.log_parser import parse_line, parse_lines, LogEntry


RAW_PLAIN = "2024-01-15T12:00:00.000000000Z Hello world"
RAW_JSON = '2024-01-15T12:00:01.000000000Z {"level":"info","msg":"server started","port":8080}'
RAW_NO_TS = "Just a plain message without timestamp"


def test_parse_plain_line_extracts_timestamp():
    entry = parse_line(RAW_PLAIN)
    assert entry.timestamp == "2024-01-15T12:00:00.000000000Z"
    assert entry.message == "Hello world"
    assert not entry.is_json


def test_parse_json_line_is_structured():
    entry = parse_line(RAW_JSON)
    assert entry.is_json is True
    assert entry.structured["port"] == 8080
    assert entry.message == "server started"


def test_parse_line_without_timestamp():
    entry = parse_line(RAW_NO_TS)
    assert entry.timestamp is None
    assert entry.message == RAW_NO_TS


def test_str_representation_includes_timestamp():
    entry = parse_line(RAW_PLAIN)
    assert "2024-01-15T12:00:00.000000000Z" in str(entry)
    assert "Hello world" in str(entry)


def test_parse_lines_skips_empty():
    lines = [RAW_PLAIN, "", "   ", RAW_NO_TS]
    entries = parse_lines(lines)
    assert len(entries) == 2


def test_parse_invalid_json_falls_back_to_plain():
    raw = "2024-01-15T12:00:00.000000000Z {not valid json}"
    entry = parse_line(raw)
    assert not entry.is_json
    assert "{not valid json}" in entry.message
