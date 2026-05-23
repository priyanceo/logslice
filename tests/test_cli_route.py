"""Tests for logslice.cli_route."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from logslice.cli_route import route_command
from logslice.docker_client import DockerClientError
from logslice.log_parser import LogEntry


def _make_runner() -> CliRunner:
    return CliRunner(mix_stderr=False)


def _fake_entry(message: str, level: str = "info") -> LogEntry:
    return LogEntry(timestamp="2024-01-01T00:00:00Z", level=level, service="svc", message=message, raw=message)


@patch("logslice.cli_route.DockerLogClient")
@patch("logslice.cli_route.parse_line")
def test_route_keyword_rule_matches(mock_parse, mock_client_cls):
    entry = _fake_entry("database connection error")
    mock_parse.return_value = entry
    mock_client_cls.return_value.stream_logs.return_value = ["raw"]

    runner = _make_runner()
    result = runner.invoke(route_command, ["mycontainer", "--route", "db:database", "--no-color"])
    assert result.exit_code == 0
    assert "[db]" in result.output


@patch("logslice.cli_route.DockerLogClient")
@patch("logslice.cli_route.parse_line")
def test_route_keyword_no_match_produces_no_output(mock_parse, mock_client_cls):
    entry = _fake_entry("unrelated message")
    mock_parse.return_value = entry
    mock_client_cls.return_value.stream_logs.return_value = ["raw"]

    runner = _make_runner()
    result = runner.invoke(route_command, ["mycontainer", "--route", "db:database", "--no-color"])
    assert result.exit_code == 0
    assert "[db]" not in result.output


@patch("logslice.cli_route.DockerLogClient")
@patch("logslice.cli_route.parse_line")
def test_route_level_rule_matches(mock_parse, mock_client_cls):
    entry = _fake_entry("boom", level="error")
    mock_parse.return_value = entry
    mock_client_cls.return_value.stream_logs.return_value = ["raw"]

    runner = _make_runner()
    result = runner.invoke(route_command, ["mycontainer", "--level-route", "errors:error", "--no-color"])
    assert result.exit_code == 0
    assert "[errors]" in result.output


@patch("logslice.cli_route.DockerLogClient")
def test_route_exits_on_client_error(mock_client_cls):
    mock_client_cls.return_value.stream_logs.side_effect = DockerClientError("no docker")

    runner = _make_runner()
    result = runner.invoke(route_command, ["mycontainer"])
    assert result.exit_code == 1
    assert "Error" in result.stderr


def test_route_invalid_rule_format():
    runner = _make_runner()
    result = runner.invoke(route_command, ["mycontainer", "--route", "badformat"])
    assert result.exit_code != 0
