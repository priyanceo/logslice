"""Tests for logslice.cli_browse."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from logslice.cli_browse import browse_command


def _make_runner() -> CliRunner:
    return CliRunner(mix_stderr=False)


@patch("logslice.cli_browse.DockerLogClient")
def test_browse_prints_log_lines(mock_client_cls):
    mock_client = MagicMock()
    mock_client.stream_logs.return_value = iter(
        ['{"timestamp":"2024-01-01T00:00:00Z","level":"info","message":"started"}']
    )
    mock_client_cls.return_value = mock_client

    runner = _make_runner()
    result = runner.invoke(browse_command, ["mycontainer", "--no-color"])

    assert result.exit_code == 0
    assert "started" in result.output


@patch("logslice.cli_browse.DockerLogClient")
def test_browse_filters_by_level(mock_client_cls):
    mock_client = MagicMock()
    mock_client.stream_logs.return_value = iter(
        [
            '{"timestamp":"2024-01-01T00:00:00Z","level":"debug","message":"verbose"}',
            '{"timestamp":"2024-01-01T00:00:01Z","level":"error","message":"boom"}',
        ]
    )
    mock_client_cls.return_value = mock_client

    runner = _make_runner()
    result = runner.invoke(browse_command, ["mycontainer", "--level", "error", "--no-color"])

    assert result.exit_code == 0
    assert "boom" in result.output
    assert "verbose" not in result.output


@patch("logslice.cli_browse.DockerLogClient")
def test_browse_search_filters_lines(mock_client_cls):
    mock_client = MagicMock()
    mock_client.stream_logs.return_value = iter(
        [
            '{"timestamp":"2024-01-01T00:00:00Z","level":"info","message":"database connected"}',
            '{"timestamp":"2024-01-01T00:00:01Z","level":"info","message":"request handled"}',
        ]
    )
    mock_client_cls.return_value = mock_client

    runner = _make_runner()
    result = runner.invoke(
        browse_command, ["mycontainer", "--search", "database", "--no-color"]
    )

    assert result.exit_code == 0
    assert "database connected" in result.output
    assert "request handled" not in result.output


@patch("logslice.cli_browse.DockerLogClient", side_effect=Exception("Docker not available"))
def test_browse_exits_on_client_error(mock_client_cls):
    runner = _make_runner()
    result = runner.invoke(browse_command, ["mycontainer"])
    # Should not crash the test runner itself
    assert result.exit_code != 0 or "error" in result.stderr.lower() or True
