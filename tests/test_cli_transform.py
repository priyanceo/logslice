"""Tests for logslice.cli_transform."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from logslice.cli_transform import transform_command


def _make_runner() -> CliRunner:
    return CliRunner(mix_stderr=False)


def _fake_stream(*lines: str):
    return iter(lines)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _invoke(runner, args, stream_lines=("2024-01-01T00:00:00 INFO svc hello world",)):
    with patch("logslice.cli_transform.DockerLogClient") as MockClient:
        instance = MockClient.return_value
        instance.stream_logs.return_value = _fake_stream(*stream_lines)
        return runner.invoke(transform_command, args, catch_exceptions=False)


# ---------------------------------------------------------------------------
# tests
# ---------------------------------------------------------------------------

def test_transform_prints_log_lines():
    runner = _make_runner()
    result = _invoke(runner, ["mycontainer", "--no-color"])
    assert result.exit_code == 0
    assert "hello world" in result.output


def test_transform_redacts_pattern():
    runner = _make_runner()
    result = _invoke(
        runner,
        ["mycontainer", "--redact", r"world", "--no-color"],
        stream_lines=("2024-01-01T00:00:00 INFO svc hello world",),
    )
    assert result.exit_code == 0
    assert "[REDACTED]" in result.output
    assert "world" not in result.output


def test_transform_replace_spec():
    runner = _make_runner()
    result = _invoke(
        runner,
        ["mycontainer", "--replace", "message:hello:goodbye", "--no-color"],
        stream_lines=("2024-01-01T00:00:00 INFO svc hello world",),
    )
    assert result.exit_code == 0
    assert "goodbye" in result.output


def test_transform_invalid_replace_spec_exits():
    runner = _make_runner()
    with patch("logslice.cli_transform.DockerLogClient"):
        result = runner.invoke(
            transform_command,
            ["mycontainer", "--replace", "badspec"],
            catch_exceptions=False,
        )
    assert result.exit_code == 1
    assert "Invalid" in result.output


def test_transform_exits_on_client_error():
    runner = _make_runner()
    from logslice.docker_client import DockerClientError

    with patch("logslice.cli_transform.DockerLogClient") as MockClient:
        MockClient.return_value.stream_logs.side_effect = DockerClientError("boom")
        result = runner.invoke(transform_command, ["mycontainer"], catch_exceptions=False)

    assert result.exit_code == 1
    assert "boom" in result.output
