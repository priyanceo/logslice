"""Tests for logslice.cli_tail."""
from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from logslice.cli_tail import tail_command
from logslice.log_parser import LogEntry


def _make_runner() -> CliRunner:
    return CliRunner(mix_stderr=False)


def _fake_entry(msg: str, level: str = "INFO") -> LogEntry:
    return LogEntry(
        timestamp=datetime(2024, 1, 1, tzinfo=timezone.utc),
        level=level,
        service="web",
        message=msg,
        raw=msg,
    )


def _make_mock_client(lines: list[str]):
    mock_client = MagicMock()
    mock_client.stream_logs.return_value = iter(lines)
    return mock_client


def test_tail_prints_log_lines() -> None:
    runner = _make_runner()
    with patch("logslice.cli_tail.DockerLogClient") as MockClient:
        MockClient.return_value = _make_mock_client(["hello world", "second line"])
        result = runner.invoke(tail_command, ["mycontainer", "--no-color"])
    assert result.exit_code == 0
    assert "hello world" in result.output
    assert "second line" in result.output


def test_tail_level_filter_excludes_non_matching() -> None:
    runner = _make_runner()
    lines = ['{"level":"ERROR","message":"boom"}', '{"level":"INFO","message":"ok"}']
    with patch("logslice.cli_tail.DockerLogClient") as MockClient:
        MockClient.return_value = _make_mock_client(lines)
        result = runner.invoke(tail_command, ["mycontainer", "--level", "ERROR", "--no-color"])
    assert "boom" in result.output
    assert "ok" not in result.output


def test_tail_exits_on_client_error() -> None:
    runner = _make_runner()
    from logslice.docker_client import DockerClientError
    with patch("logslice.cli_tail.DockerLogClient") as MockClient:
        MockClient.return_value.stream_logs.side_effect = DockerClientError("no daemon")
        result = runner.invoke(tail_command, ["mycontainer"])
    assert result.exit_code != 0
    assert "no daemon" in result.output


def test_tail_backfill_option_accepted() -> None:
    runner = _make_runner()
    with patch("logslice.cli_tail.DockerLogClient") as MockClient:
        MockClient.return_value = _make_mock_client(["line1"])
        result = runner.invoke(tail_command, ["mycontainer", "--backfill", "10", "--no-color"])
    assert result.exit_code == 0
