"""Tests for logslice.cli_correlate."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from logslice.cli_correlate import correlate_command
from logslice.docker_client import DockerClientError
from logslice.log_parser import LogEntry


def _make_runner() -> CliRunner:
    return CliRunner(mix_stderr=False)


def _fake_entry(trace_id: str, level: str = "INFO") -> str:
    import json
    return json.dumps({"message": "msg", "level": level, "trace_id": trace_id})


@patch("logslice.cli_correlate.DockerLogClient")
def test_correlate_groups_by_trace_id(mock_cls):
    mock_client = MagicMock()
    mock_cls.return_value = mock_client
    mock_client.stream_logs.return_value = [
        _fake_entry("t1"),
        _fake_entry("t1"),
        _fake_entry("t2"),
    ]
    runner = _make_runner()
    result = runner.invoke(correlate_command, ["mycontainer", "--min-size", "1"])
    assert result.exit_code == 0
    assert "t1" in result.output
    assert "t2" in result.output


@patch("logslice.cli_correlate.DockerLogClient")
def test_correlate_json_output(mock_cls):
    import json
    mock_client = MagicMock()
    mock_cls.return_value = mock_client
    mock_client.stream_logs.return_value = [
        _fake_entry("abc"),
        _fake_entry("abc"),
    ]
    runner = _make_runner()
    result = runner.invoke(
        correlate_command,
        ["mycontainer", "--min-size", "1", "--json-out"],
    )
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert isinstance(data, list)
    assert data[0]["key"] == "abc"
    assert data[0]["count"] == 2


@patch("logslice.cli_correlate.DockerLogClient")
def test_correlate_min_size_hides_small_groups(mock_cls):
    mock_client = MagicMock()
    mock_cls.return_value = mock_client
    mock_client.stream_logs.return_value = [
        _fake_entry("solo"),
        _fake_entry("duo"),
        _fake_entry("duo"),
    ]
    runner = _make_runner()
    result = runner.invoke(correlate_command, ["mycontainer", "--min-size", "2"])
    assert result.exit_code == 0
    assert "duo" in result.output
    assert "solo" not in result.output


@patch("logslice.cli_correlate.DockerLogClient")
def test_correlate_exits_on_client_error(mock_cls):
    mock_client = MagicMock()
    mock_cls.return_value = mock_client
    mock_client.stream_logs.side_effect = DockerClientError("boom")
    runner = _make_runner()
    result = runner.invoke(correlate_command, ["mycontainer"])
    assert result.exit_code == 1
    assert "Docker error" in result.stderr


@patch("logslice.cli_correlate.DockerLogClient")
def test_correlate_no_groups_message(mock_cls):
    mock_client = MagicMock()
    mock_cls.return_value = mock_client
    mock_client.stream_logs.return_value = []
    runner = _make_runner()
    result = runner.invoke(correlate_command, ["mycontainer", "--min-size", "1"])
    assert result.exit_code == 0
    assert "No groups" in result.output
