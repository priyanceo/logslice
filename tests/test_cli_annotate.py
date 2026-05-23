"""Tests for logslice.cli_annotate."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from logslice.cli_annotate import annotate_command
from logslice.docker_client import DockerClientError


def _make_runner() -> CliRunner:
    return CliRunner(mix_stderr=False)


def _fake_stream(*lines: str):
    return iter(lines)


def test_annotate_prints_log_lines() -> None:
    runner = _make_runner()
    with patch("logslice.cli_annotate.DockerLogClient") as MockClient:
        MockClient.return_value.stream_logs.return_value = _fake_stream(
            "2024-01-01T00:00:00 INFO hello world"
        )
        result = runner.invoke(annotate_command, ["mycontainer"])
    assert result.exit_code == 0
    assert "hello world" in result.output


def test_annotate_tag_appears_in_output() -> None:
    runner = _make_runner()
    with patch("logslice.cli_annotate.DockerLogClient") as MockClient:
        MockClient.return_value.stream_logs.return_value = _fake_stream(
            "2024-01-01T00:00:00 ERROR database connection failed"
        )
        result = runner.invoke(
            annotate_command, ["mycontainer", "--tag", "db_issue:database"]
        )
    assert result.exit_code == 0
    assert "db_issue" in result.output


def test_annotate_tag_not_added_when_no_match() -> None:
    runner = _make_runner()
    with patch("logslice.cli_annotate.DockerLogClient") as MockClient:
        MockClient.return_value.stream_logs.return_value = _fake_stream(
            "2024-01-01T00:00:00 INFO all good"
        )
        result = runner.invoke(
            annotate_command, ["mycontainer", "--tag", "db_issue:database"]
        )
    assert result.exit_code == 0
    assert "db_issue" not in result.output


def test_annotate_level_filter_excludes_non_matching() -> None:
    runner = _make_runner()
    with patch("logslice.cli_annotate.DockerLogClient") as MockClient:
        MockClient.return_value.stream_logs.return_value = _fake_stream(
            "2024-01-01T00:00:00 DEBUG verbose stuff",
            "2024-01-01T00:00:01 ERROR boom",
        )
        result = runner.invoke(
            annotate_command, ["mycontainer", "--level", "error"]
        )
    assert result.exit_code == 0
    assert "boom" in result.output
    assert "verbose" not in result.output


def test_annotate_exits_on_client_error() -> None:
    runner = _make_runner()
    with patch("logslice.cli_annotate.DockerLogClient") as MockClient:
        MockClient.return_value.stream_logs.side_effect = DockerClientError("no docker")
        result = runner.invoke(annotate_command, ["mycontainer"])
    assert result.exit_code != 0
    assert "no docker" in result.output


def test_annotate_bad_tag_spec_raises() -> None:
    runner = _make_runner()
    with patch("logslice.cli_annotate.DockerLogClient"):
        result = runner.invoke(annotate_command, ["mycontainer", "--tag", "badspec"])
    assert result.exit_code != 0
