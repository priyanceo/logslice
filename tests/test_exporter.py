"""Tests for logslice.exporter module."""

from __future__ import annotations

import csv
import io
import json

import pytest

from logslice.exporter import (
    ExportError,
    ExportFormat,
    export_csv,
    export_entries,
    export_json,
    export_text,
)
from logslice.log_parser import LogEntry


def _entry(message: str, timestamp: str | None = "2024-01-01T00:00:00Z", level: str | None = "INFO") -> LogEntry:
    return LogEntry(timestamp=timestamp, level=level, message=message, raw=message)


@pytest.fixture()
def sample_entries() -> list[LogEntry]:
    return [
        _entry("server started", "2024-01-01T10:00:00Z", "INFO"),
        _entry("disk full", "2024-01-01T10:01:00Z", "ERROR"),
        _entry("no timestamp", None, None),
    ]


def test_export_json_returns_array(sample_entries):
    result = export_json(sample_entries)
    data = json.loads(result)
    assert isinstance(data, list)
    assert len(data) == 3


def test_export_json_contains_fields(sample_entries):
    data = json.loads(export_json(sample_entries))
    first = data[0]
    assert first["message"] == "server started"
    assert first["level"] == "INFO"
    assert first["timestamp"] == "2024-01-01T10:00:00Z"


def test_export_csv_has_header(sample_entries):
    result = export_csv(sample_entries)
    reader = csv.DictReader(io.StringIO(result))
    assert reader.fieldnames == ["timestamp", "level", "message", "raw"]


def test_export_csv_row_count(sample_entries):
    result = export_csv(sample_entries)
    rows = list(csv.DictReader(io.StringIO(result)))
    assert len(rows) == 3


def test_export_csv_handles_none_fields(sample_entries):
    result = export_csv(sample_entries)
    rows = list(csv.DictReader(io.StringIO(result)))
    assert rows[2]["timestamp"] == ""
    assert rows[2]["level"] == ""


def test_export_text_one_line_per_entry(sample_entries):
    result = export_text(sample_entries)
    lines = result.splitlines()
    assert len(lines) == 3


def test_export_entries_dispatches_json(sample_entries):
    result = export_entries(sample_entries, ExportFormat.JSON)
    assert result.startswith("[")


def test_export_entries_dispatches_csv(sample_entries):
    result = export_entries(sample_entries, "csv")
    assert "timestamp" in result


def test_export_entries_dispatches_text(sample_entries):
    result = export_entries(sample_entries, "text")
    assert "server started" in result


def test_export_entries_invalid_format_raises(sample_entries):
    with pytest.raises(ValueError):
        export_entries(sample_entries, "xml")
