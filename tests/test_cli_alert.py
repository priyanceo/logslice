"""Tests for logslice.cli_alert."""
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from logslice.cli_alert import alert_command
from logslice.docker_client import DockerClientError


def _make_runner() -> CliRunner:
    return CliRunner(mix_stderr=False)


def _make_mock_client(log_lines: list[str]) -> MagicMock:
    """Create a mock DockerLogClient that streams the given log lines."""
    mock_client = MagicMock()
    mock_client.stream_logs.return_value = iter(log_lines)
    return mock_client


@patch("logslice.cli_alert.DockerLogClient")
def test_alert_streams_lines(mock_client_cls):
    mock_client_cls.return_value = _make_mock_client(
        [
            '{"level": "INFO", "message": "started"}',
            '{"level": "ERROR", "message": "crash"}',
        ]
    )

    runner = _make_runner()
    result = runner.invoke(alert_command, ["my_container", "--level", "ERROR", "--threshold", "1"])

    assert result.exit_code == 0
    assert "crash" in result.output


@patch("logslice.cli_alert.DockerLogClient")
def test_alert_fires_on_threshold(mock_client_cls):
    mock_client_cls.return_value = _make_mock_client(
        [
            '{"level": "ERROR", "message": "bad thing"}',
        ]
    )

    runner = _make_runner()
    result = runner.invoke(
        alert_command,
        ["my_container", "--level", "ERROR", "--threshold", "1", "--rule-name", "test-rule"],
    )

    assert result.exit_code == 0
    assert "ALERT" in result.output
    assert "test-rule" in result.output


@patch("logslice.cli_alert.DockerLogClient")
def test_alert_no_fire_below_threshold(mock_client_cls):
    mock_client_cls.return_value = _make_mock_client(
        [
            '{"level": "ERROR", "message": "one error"}',
        ]
    )

    runner = _make_runner()
    result = runner.invoke(
        alert_command,
        ["my_container", "--level", "ERROR", "--threshold", "5"],
    )

    assert result.exit_code == 0
    assert "ALERT" not in result.output


@patch("logslice.cli_alert.DockerLogClient")
def test_alert_exits_on_client_error(mock_client_cls):
    mock_client_cls.side_effect = DockerClientError("daemon not running")

    runner = _make_runner()
    result = runner.invoke(alert_command, ["missing_container"])

    assert result.exit_code != 0
    assert "daemon not running" in result.output
