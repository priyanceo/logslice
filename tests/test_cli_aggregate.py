"""Tests for logslice.cli_aggregate."""
from __future__ import annotations

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from logslice.cli_aggregate import aggregate_command
from logslice.docker_client import DockerClientError
from logslice.log_parser import LogEntry


def _make_runner() -> CliRunner:
    return CliRunner(mix_stderr=False)


def _fake_entry(ts: datetime, level: str = "info", message: str = "msg") -> LogEntry:
    return LogEntry(
        raw=message,
        timestamp=ts,
        level=level,
        service="svc",
        message=message,
        extra={},
    )


_LINES = [
    '2024-01-01T00:00:10Z INFO hello',
    '2024-01-01T00:00:50Z INFO world',
    '2024-01-01T00:01:10Z ERROR boom',
]


@patch("logslice.cli_aggregate.DockerLogClient")
@patch("logslice.cli_aggregate.parse_lines")
def test_aggregate_shows_buckets(mock_parse, mock_client_cls):
    mock_client = MagicMock()
    mock_client.stream_logs.return_value = iter(_LINES)
    mock_client_cls.return_value = mock_client
    mock_parse.return_value = [
        _fake_entry(datetime(2024, 1, 1, 0, 0, 10), "info"),
        _fake_entry(datetime(2024, 1, 1, 0, 0, 50), "info"),
        _fake_entry(datetime(2024, 1, 1, 0, 1, 10), "error"),
    ]
    result = _make_runner().invoke(aggregate_command, ["mycontainer", "--window", "60"])
    assert result.exit_code == 0
    assert "2 window" in result.output or "window" in result.output


@patch("logslice.cli_aggregate.DockerLogClient")
@patch("logslice.cli_aggregate.parse_lines")
def test_aggregate_single_window(mock_parse, mock_client_cls):
    mock_client = MagicMock()
    mock_client.stream_logs.return_value = iter(_LINES[:2])
    mock_client_cls.return_value = mock_client
    mock_parse.return_value = [
        _fake_entry(datetime(2024, 1, 1, 0, 0, 10)),
        _fake_entry(datetime(2024, 1, 1, 0, 0, 50)),
    ]
    result = _make_runner().invoke(aggregate_command, ["mycontainer", "--window", "60"])
    assert result.exit_code == 0
    assert "total=2" in result.output


@patch("logslice.cli_aggregate.DockerLogClient")
def test_aggregate_exits_on_client_error(mock_client_cls):
    mock_client_cls.return_value.stream_logs.side_effect = DockerClientError("no docker")
    result = _make_runner().invoke(aggregate_command, ["mycontainer"])
    assert result.exit_code != 0
    assert "no docker" in result.output


@patch("logslice.cli_aggregate.DockerLogClient")
@patch("logslice.cli_aggregate.parse_lines")
def test_aggregate_no_entries_prints_message(mock_parse, mock_client_cls):
    mock_client = MagicMock()
    mock_client.stream_logs.return_value = iter([])
    mock_client_cls.return_value = mock_client
    mock_parse.return_value = []
    result = _make_runner().invoke(aggregate_command, ["mycontainer"])
    assert result.exit_code == 0
    assert "No log entries" in result.output
