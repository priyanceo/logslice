"""Tests for the stats CLI command."""

import json
from unittest.mock import MagicMock, patch
from click.testing import CliRunner
from logslice.cli_stats import stats_command
from logslice.docker_client import DockerClientError


def _make_runner():
    return CliRunner()


SAMPLE_LINES = [
    '{"timestamp": "2024-01-01T10:00:00Z", "level": "INFO", "service": "api", "message": "started"}',
    '{"timestamp": "2024-01-01T10:00:01Z", "level": "ERROR", "service": "api", "message": "failed"}',
    '{"timestamp": "2024-01-01T10:00:02Z", "level": "INFO", "service": "worker", "message": "done"}',
    '{"timestamp": "2024-01-01T10:00:03Z", "level": "WARN", "service": "worker", "message": "slow"}',
]


@patch("logslice.cli_stats.DockerLogClient")
def test_stats_shows_total(mock_client_cls):
    mock_client = MagicMock()
    mock_client.stream_logs.return_value = iter(SAMPLE_LINES)
    mock_client_cls.return_value = mock_client

    runner = _make_runner()
    result = runner.invoke(stats_command, ["my_container"])

    assert result.exit_code == 0
    assert "Total logs: 4" in result.output
    assert "my_container" in result.output


@patch("logslice.cli_stats.DockerLogClient")
def test_stats_level_breakdown(mock_client_cls):
    mock_client = MagicMock()
    mock_client.stream_logs.return_value = iter(SAMPLE_LINES)
    mock_client_cls.return_value = mock_client

    runner = _make_runner()
    result = runner.invoke(stats_command, ["my_container", "--level"])

    assert result.exit_code == 0
    assert "By level" in result.output
    assert "INFO" in result.output
    assert "ERROR" in result.output


@patch("logslice.cli_stats.DockerLogClient")
def test_stats_service_breakdown(mock_client_cls):
    mock_client = MagicMock()
    mock_client.stream_logs.return_value = iter(SAMPLE_LINES)
    mock_client_cls.return_value = mock_client

    runner = _make_runner()
    result = runner.invoke(stats_command, ["my_container", "--service"])

    assert result.exit_code == 0
    assert "By service" in result.output
    assert "api" in result.output
    assert "worker" in result.output


@patch("logslice.cli_stats.DockerLogClient")
def test_stats_exits_on_client_error(mock_client_cls):
    mock_client = MagicMock()
    mock_client.stream_logs.side_effect = DockerClientError("container not found")
    mock_client_cls.return_value = mock_client

    runner = _make_runner()
    result = runner.invoke(stats_command, ["bad_container"])

    assert result.exit_code != 0
    assert "container not found" in result.output


@patch("logslice.cli_stats.DockerLogClient")
def test_stats_no_entries(mock_client_cls):
    mock_client = MagicMock()
    mock_client.stream_logs.return_value = iter([])
    mock_client_cls.return_value = mock_client

    runner = _make_runner()
    result = runner.invoke(stats_command, ["empty_container"])

    assert result.exit_code == 0
    assert "No log entries found" in result.output
