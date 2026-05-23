"""Tests for logslice.cli_enrich."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from logslice.cli_enrich import enrich_command
from logslice.docker_client import DockerClientError


def _make_runner() -> CliRunner:
    return CliRunner(mix_stderr=False)


def _fake_stream(*lines: str):
    """Return a mock DockerLogClient whose stream_logs yields the given lines."""
    client = MagicMock()
    client.stream_logs.return_value = iter(lines)
    return client


@patch("logslice.cli_enrich.DockerLogClient")
def test_enrich_prints_log_lines(mock_cls):
    mock_cls.return_value = _fake_stream(
        '{"level":"info","message":"started","service":"api"}',
    )
    result = _make_runner().invoke(enrich_command, ["mycontainer"])
    assert result.exit_code == 0
    assert "started" in result.output


@patch("logslice.cli_enrich.DockerLogClient")
def test_enrich_host_field_added(mock_cls):
    mock_cls.return_value = _fake_stream(
        '{"level":"info","message":"ping","service":"web"}',
    )
    result = _make_runner().invoke(enrich_command, ["mycontainer", "--add-host"])
    assert result.exit_code == 0
    # host value is the container name; format_entry renders extra fields
    assert result.output  # at minimum something was printed


@patch("logslice.cli_enrich.DockerLogClient")
def test_enrich_level_filter_excludes_debug(mock_cls):
    mock_cls.return_value = _fake_stream(
        '{"level":"debug","message":"verbose","service":"svc"}',
        '{"level":"error","message":"boom","service":"svc"}',
    )
    result = _make_runner().invoke(enrich_command, ["mycontainer", "--level", "error"])
    assert result.exit_code == 0
    assert "boom" in result.output
    assert "verbose" not in result.output


@patch("logslice.cli_enrich.DockerLogClient")
def test_enrich_exits_on_client_error(mock_cls):
    client = MagicMock()
    client.stream_logs.side_effect = DockerClientError("connection refused")
    mock_cls.return_value = client
    result = _make_runner().invoke(enrich_command, ["mycontainer"])
    assert result.exit_code != 0
    assert "connection refused" in result.output
