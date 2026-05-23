"""Integration tests for logslice.cli_split."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from logslice.cli_split import split_command
from logslice.docker_client import DockerClientError


def _make_runner() -> CliRunner:
    return CliRunner(mix_stderr=False)


def _fake_logs(lines):
    return lines


def test_split_shows_bucket_counts() -> None:
    runner = _make_runner()
    fake_lines = [
        '{"level": "error", "message": "boom"}',
        '{"level": "info", "message": "ok"}',
        '{"level": "error", "message": "crash"}',
    ]
    with patch("logslice.cli_split.DockerLogClient") as MockClient:
        MockClient.return_value.stream_logs.return_value = fake_lines
        result = runner.invoke(split_command, ["mycontainer", "--level", "error"])

    assert result.exit_code == 0
    assert "[error] 2 entries" in result.output
    assert "[default] 1 entries" in result.output


def test_split_keyword_rule_buckets() -> None:
    runner = _make_runner()
    fake_lines = [
        '{"level": "warn", "message": "timeout occurred"}',
        '{"level": "info", "message": "request complete"}',
    ]
    with patch("logslice.cli_split.DockerLogClient") as MockClient:
        MockClient.return_value.stream_logs.return_value = fake_lines
        result = runner.invoke(split_command, ["mycontainer", "--keyword", "timeout"])

    assert result.exit_code == 0
    assert "[timeout] 1 entries" in result.output
    assert "[default] 1 entries" in result.output


def test_split_exits_on_client_error() -> None:
    runner = _make_runner()
    with patch("logslice.cli_split.DockerLogClient") as MockClient:
        MockClient.return_value.stream_logs.side_effect = DockerClientError("no daemon")
        result = runner.invoke(split_command, ["mycontainer"])

    assert result.exit_code == 1
    assert "no daemon" in result.stderr


def test_split_custom_catch_all_label() -> None:
    runner = _make_runner()
    fake_lines = ['{"level": "debug", "message": "verbose"}']
    with patch("logslice.cli_split.DockerLogClient") as MockClient:
        MockClient.return_value.stream_logs.return_value = fake_lines
        result = runner.invoke(
            split_command, ["mycontainer", "--catch-all", "misc"]
        )

    assert result.exit_code == 0
    assert "[misc]" in result.output


def test_split_no_rules_all_to_default() -> None:
    runner = _make_runner()
    fake_lines = [
        '{"level": "info", "message": "a"}',
        '{"level": "info", "message": "b"}',
    ]
    with patch("logslice.cli_split.DockerLogClient") as MockClient:
        MockClient.return_value.stream_logs.return_value = fake_lines
        result = runner.invoke(split_command, ["mycontainer"])

    assert result.exit_code == 0
    assert "[default] 2 entries" in result.output
