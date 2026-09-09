"""Metrics must distinguish 'no samples' from 'zero', and state uncertainty."""

import math

import pytest

from modelcmp.metrics import (distinguishable, proportion_stderr, summarise,
                              token_cost)
from modelcmp.provider import Completion


def comp(text, reason="stop", out=10):
    return Completion(text, reason, 20, out, "abc123")


def test_identical_outputs_give_determinism_one():
    m = summarise([comp("same")] * 5)
    assert m.determinism == 1.0
    assert m.distinct_outputs == 1


def test_all_different_gives_determinism_one_over_n():
    m = summarise([comp(f"x{i}") for i in range(5)])
    assert m.determinism == pytest.approx(0.2)
    assert m.distinct_ratio == 1.0


def test_truncation_rate():
    m = summarise([comp("a"), comp("b", "length"), comp("c", "length")])
    assert m.truncation_rate == pytest.approx(2 / 3)


def test_json_valid_rate():
    m = summarise([comp('{"a": 1}'), comp("not json"), comp('{"b": 2}')])
    assert m.json_valid_rate == pytest.approx(2 / 3)


def test_empty_input_raises():
    with pytest.raises(ValueError):
        summarise([])


def test_stderr_matches_the_formula():
    assert proportion_stderr(0.5, 100) == pytest.approx(0.05)
    assert proportion_stderr(0.9, 100) == pytest.approx(0.03)


def test_stderr_is_nan_for_no_samples():
    """No samples is not zero uncertainty (M3-L14)."""
    assert math.isnan(proportion_stderr(0.5, 0))


def test_small_samples_cannot_distinguish_a_small_difference():
    """0.90 vs 0.85 on 100 rows is noise (M3-L14 section 7.3)."""
    assert not distinguishable(0.90, 0.85, 100, 100)


def test_large_samples_can_distinguish_the_same_difference():
    assert distinguishable(0.90, 0.85, 5000, 5000)


def test_identical_rates_are_never_distinguishable():
    assert not distinguishable(0.7, 0.7, 1000, 1000)


def test_token_cost_arithmetic():
    # 1000 in + 500 out at $0.50/M and $1.50/M
    assert token_cost(1000, 500, 0.50, 1.50) == pytest.approx(
        (1000 * 0.50 + 500 * 1.50) / 1e6)
