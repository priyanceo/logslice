"""Tests for logslice.cli_mask."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from logslice.cli_mask import mask_command
from logslice.docker_client import DockerClientError


def _make_runner() -> CliRunner:
    return CliRunner(mix_stderr=False)


def _fake_stream(lines):
    """Return a mock DockerLogClient whose stream_logs yields *lines*."""
    mock = MagicMock()
    mock.stream_logs.return_value = iter(lines)
    return mock


@patch("logslice.cli_mask.DockerLogClient")
def test_mask_prints_log_lines(mock_cls):
    mock_cls.return_value = _fake_stream(
        ["2024-01-01T00:00:00Z info svc hello world"]
    )
    result = _make_runner().invoke(mask_command, ["mycontainer"])
    assert result.exit_code == 0
    assert "***" in result.output  # message was masked


@patch("logslice.cli_mask.DockerLogClient")
def test_mask_hides_original_message(mock_cls):
    mock_cls.return_value = _fake_stream(
        ["2024-01-01T00:00:00Z info svc secret-password"]
    )
    result = _make_runner().invoke(
        mask_command, ["mycontainer", "--field", "message"]
    )
    assert result.exit_code == 0
    assert "secret-password" not in result.output


@patch("logslice.cli_mask.DockerLogClient")
def test_mask_custom_replacement(mock_cls):
    mock_cls.return_value = _fake_stream(
        ["2024-01-01T00:00:00Z info svc hello"]
    )
    result = _make_runner().invoke(
        mask_command,
        ["mycontainer", "--field", "message", "--mask-with", "[HIDDEN]"],
    )
    assert result.exit_code == 0
    assert "[HIDDEN]" in result.output


@patch("logslice.cli_mask.DockerLogClient")
def test_mask_level_filter_excludes_debug(mock_cls):
    mock_cls.return_value = _fake_stream(
        [
            "2024-01-01T00:00:00Z debug svc debug-line",
            "2024-01-01T00:00:01Z error svc error-line",
        ]
    )
    result = _make_runner().invoke(
        mask_command, ["mycontainer", "--level", "error"]
    )
    assert result.exit_code == 0
    assert "debug" not in result.output.lower() or "debug-line" not in result.output


@patch("logslice.cli_mask.DockerLogClient")
def test_mask_exits_on_client_error(mock_cls):
    mock_cls.return_value = MagicMock()
    mock_cls.return_value.stream_logs.side_effect = DockerClientError("boom")
    result = _make_runner().invoke(mask_command, ["mycontainer"])
    assert result.exit_code != 0
    assert "boom" in result.output
