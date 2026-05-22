"""Tests for logslice.replay."""

from __future__ import annotations

import gzip
from pathlib import Path

import pytest

from logslice.replay import ReplayError, iter_entries, replay


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

PLAIN_LINES = [
    '2024-01-01T00:00:00Z {"level":"INFO","msg":"started"}',
    '2024-01-01T00:00:01Z {"level":"ERROR","msg":"boom"}',
    "",
    '2024-01-01T00:00:02Z plain text line',
]


def _write_plain(tmp_path: Path, lines=None) -> Path:
    p = tmp_path / "test.log"
    p.write_text("\n".join(lines or PLAIN_LINES), encoding="utf-8")
    return p


def _write_gz(tmp_path: Path) -> Path:
    p = tmp_path / "test.log.gz"
    with gzip.open(p, "wt", encoding="utf-8") as fh:
        fh.write("\n".join(PLAIN_LINES))
    return p


# ---------------------------------------------------------------------------
# iter_entries
# ---------------------------------------------------------------------------


def test_iter_entries_plain(tmp_path):
    path = _write_plain(tmp_path)
    entries = list(iter_entries(path))
    # empty line is skipped
    assert len(entries) == 3


def test_iter_entries_gz(tmp_path):
    path = _write_gz(tmp_path)
    entries = list(iter_entries(path))
    assert len(entries) == 3


def test_iter_entries_missing_file(tmp_path):
    with pytest.raises(ReplayError, match="File not found"):
        list(iter_entries(tmp_path / "missing.log"))


def test_iter_entries_parses_json(tmp_path):
    path = _write_plain(tmp_path)
    entries = list(iter_entries(path))
    info = entries[0]
    assert info.level == "INFO"
    assert info.message == "started"


# ---------------------------------------------------------------------------
# replay (with filter)
# ---------------------------------------------------------------------------


def test_replay_no_filter_returns_all(tmp_path):
    path = _write_plain(tmp_path)
    entries = list(replay(path))
    assert len(entries) == 3


def test_replay_with_filter_reduces(tmp_path):
    path = _write_plain(tmp_path)
    only_errors = list(replay(path, filters=lambda e: e.level == "ERROR"))
    assert len(only_errors) == 1
    assert only_errors[0].message == "boom"


def test_replay_propagates_replay_error(tmp_path):
    with pytest.raises(ReplayError):
        list(replay(tmp_path / "nope.log"))
