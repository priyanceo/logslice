"""Tests for logslice.cli_replay."""

from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

from logslice.cli_replay import replay_command

PLAIN_LINES = [
    '2024-01-01T00:00:00Z {"level":"INFO","msg":"hello"}',
    '2024-01-01T00:00:01Z {"level":"ERROR","msg":"fail"}',
    '2024-01-01T00:00:02Z {"level":"INFO","msg":"world"}',
]


def _make_runner():
    return CliRunner(mix_stderr=False)


def _log_file(tmp_path: Path) -> Path:
    p = tmp_path / "app.log"
    p.write_text("\n".join(PLAIN_LINES), encoding="utf-8")
    return p


def test_replay_prints_all_lines(tmp_path):
    runner = _make_runner()
    result = runner.invoke(replay_command, [str(_log_file(tmp_path)), "--no-color"])
    assert result.exit_code == 0
    assert "hello" in result.output
    assert "fail" in result.output
    assert "world" in result.output


def test_replay_level_filter(tmp_path):
    runner = _make_runner()
    result = runner.invoke(
        replay_command, [str(_log_file(tmp_path)), "--level", "ERROR", "--no-color"]
    )
    assert result.exit_code == 0
    assert "fail" in result.output
    assert "hello" not in result.output


def test_replay_exact_filter(tmp_path):
    runner = _make_runner()
    result = runner.invoke(
        replay_command, [str(_log_file(tmp_path)), "--exact", "world", "--no-color"]
    )
    assert result.exit_code == 0
    assert "world" in result.output
    assert "hello" not in result.output


def test_replay_missing_file_exits_nonzero(tmp_path):
    runner = _make_runner()
    result = runner.invoke(replay_command, [str(tmp_path / "missing.log")])
    assert result.exit_code == 1
    assert "Error" in result.stderr


def test_replay_reports_match_count(tmp_path):
    runner = _make_runner()
    result = runner.invoke(replay_command, [str(_log_file(tmp_path)), "--no-color"])
    assert "3 line(s) matched" in result.stderr
