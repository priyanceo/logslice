"""Tests for logslice.scorer."""
import pytest

from logslice.log_parser import LogEntry
from logslice.scorer import ScoreRule, Scorer, ScorerError


def _entry(message: str = "hello", level: str = "INFO", service: str = "svc") -> LogEntry:
    return LogEntry(timestamp="2024-01-01T00:00:00", level=level, service=service, message=message)


# ---------------------------------------------------------------------------
# ScoreRule validation
# ---------------------------------------------------------------------------

def test_rule_empty_name_raises():
    with pytest.raises(ScorerError, match="name"):
        ScoreRule(name="", match=lambda e: True, points=1)


def test_rule_non_callable_match_raises():
    with pytest.raises(ScorerError, match="callable"):
        ScoreRule(name="r", match="not_callable", points=1)  # type: ignore[arg-type]


def test_rule_zero_points_raises():
    with pytest.raises(ScorerError, match="non-zero"):
        ScoreRule(name="r", match=lambda e: True, points=0)


# ---------------------------------------------------------------------------
# Scorer.add_rule
# ---------------------------------------------------------------------------

def test_add_non_rule_raises():
    scorer = Scorer()
    with pytest.raises(ScorerError, match="ScoreRule"):
        scorer.add_rule("not_a_rule")  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Scorer.score
# ---------------------------------------------------------------------------

def test_score_no_rules_returns_zero():
    scorer = Scorer()
    assert scorer.score(_entry()) == 0.0


def test_score_matching_rule_adds_points():
    scorer = Scorer()
    scorer.add_rule(ScoreRule("error-boost", lambda e: e.level == "ERROR", points=10))
    assert scorer.score(_entry(level="ERROR")) == 10.0


def test_score_non_matching_rule_adds_nothing():
    scorer = Scorer()
    scorer.add_rule(ScoreRule("error-boost", lambda e: e.level == "ERROR", points=10))
    assert scorer.score(_entry(level="INFO")) == 0.0


def test_score_multiple_rules_accumulate():
    scorer = Scorer()
    scorer.add_rule(ScoreRule("error-boost", lambda e: e.level == "ERROR", points=10))
    scorer.add_rule(ScoreRule("keyword", lambda e: "crash" in e.message, points=5))
    entry = _entry(message="crash detected", level="ERROR")
    assert scorer.score(entry) == 15.0


def test_score_negative_points_reduce_score():
    scorer = Scorer()
    scorer.add_rule(ScoreRule("debug-penalty", lambda e: e.level == "DEBUG", points=-3))
    assert scorer.score(_entry(level="DEBUG")) == -3.0


def test_score_rule_raises_wraps_error():
    def bad_match(e: LogEntry) -> bool:
        raise ValueError("oops")

    scorer = Scorer()
    scorer.add_rule(ScoreRule("bad", bad_match, points=1))
    with pytest.raises(ScorerError, match="bad"):
        scorer.score(_entry())


# ---------------------------------------------------------------------------
# Scorer.rank
# ---------------------------------------------------------------------------

def test_rank_orders_by_score_descending():
    scorer = Scorer()
    scorer.add_rule(ScoreRule("error-boost", lambda e: e.level == "ERROR", points=10))
    entries = [_entry(level="INFO"), _entry(level="ERROR"), _entry(level="DEBUG")]
    ranked = scorer.rank(entries)
    scores = [s for _, s in ranked]
    assert scores == sorted(scores, reverse=True)
    assert ranked[0][0].level == "ERROR"


def test_rank_empty_list_returns_empty():
    scorer = Scorer()
    assert scorer.rank([]) == []
