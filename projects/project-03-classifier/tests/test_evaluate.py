"""Threshold selection, baselines and slicing."""

from __future__ import annotations

import math

import numpy as np
import pytest

from churnclf.evaluate import (baselines, choose_threshold_by_capacity,
                               choose_threshold_by_cost,
                               choose_threshold_by_fbeta,
                               choose_threshold_by_recall, slice_report)


@pytest.fixture(scope="module")
def scored():
    """A model with real but imperfect skill on a 10% positive problem."""
    rng = np.random.default_rng(0)
    y = (rng.random(4000) < 0.10).astype(int)
    proba = np.clip(rng.normal(np.where(y == 1, 0.55, 0.25), 0.15), 0.001, 0.999)
    return y, proba


def test_cost_choice_moves_toward_recall_as_misses_get_expensive(scored):
    y, proba = scored
    cheap = choose_threshold_by_cost(y, proba, cost_fp=1, cost_fn=1)
    dear = choose_threshold_by_cost(y, proba, cost_fp=1, cost_fn=100)
    assert dear.threshold < cheap.threshold
    assert dear.achieved["recall"] > cheap.achieved["recall"]


def test_cost_choice_actually_minimises_the_stated_cost(scored):
    y, proba = scored
    choice = choose_threshold_by_cost(y, proba, cost_fp=5, cost_fn=200)
    from churnclf.metrics import confusion_matrix

    def cost_at(t):
        cm = confusion_matrix(y, (proba >= t).astype(int))
        return cm.fp * 5 + cm.fn * 200

    best = cost_at(choice.threshold)
    for t in np.linspace(0.01, 0.99, 99):
        assert cost_at(t) >= best - 1e-9


def test_negative_costs_are_rejected(scored):
    y, proba = scored
    with pytest.raises(ValueError):
        choose_threshold_by_cost(y, proba, cost_fp=0, cost_fn=1)


def test_capacity_choice_flags_about_the_requested_fraction(scored):
    _, proba = scored
    choice = choose_threshold_by_capacity(proba, 0.05)
    flagged = float((proba >= choice.threshold).mean())
    assert flagged == pytest.approx(0.05, abs=0.01)


def test_capacity_fraction_must_be_a_fraction(scored):
    _, proba = scored
    for bad in (0.0, 1.0, 1.5, -0.2):
        with pytest.raises(ValueError):
            choose_threshold_by_capacity(proba, bad)


def test_recall_requirement_is_met_when_reachable(scored):
    y, proba = scored
    choice = choose_threshold_by_recall(y, proba, 0.80)
    assert choice is not None
    assert choice.achieved["recall"] >= 0.80


def test_unreachable_recall_returns_none_rather_than_a_wrong_threshold():
    """Reporting 'impossible' beats quietly returning something that misses."""
    # Every positive scores BELOW the lowest threshold on the grid, so no
    # threshold the chooser can offer will ever flag one.
    y = np.array([1] * 10 + [0] * 90)
    proba = np.concatenate([np.full(10, 0.001), np.full(90, 0.9)])
    assert choose_threshold_by_recall(y, proba, 0.99) is None
    # ... and a target of 0 recall IS reachable for the same model.
    assert choose_threshold_by_recall(y, proba, 0.0) is not None


def test_fbeta_choice_prefers_recall_at_higher_beta(scored):
    y, proba = scored
    f1_choice = choose_threshold_by_fbeta(y, proba, 1.0)
    f2_choice = choose_threshold_by_fbeta(y, proba, 2.0)
    assert f2_choice.threshold <= f1_choice.threshold


def test_baselines_include_the_always_negative_case(scored):
    y, _ = scored
    base = baselines(y, float(y.mean()))
    neg = base["always negative"]
    assert neg["recall"] == pytest.approx(0.0)
    assert neg["flagged"] == 0
    assert math.isnan(neg["precision"])
    assert neg["accuracy"] == pytest.approx(1 - y.mean())


def test_always_positive_baseline_has_precision_equal_to_the_base_rate(scored):
    y, _ = scored
    base = baselines(y, float(y.mean()))
    assert base["always positive"]["precision"] == pytest.approx(y.mean())
    assert base["always positive"]["recall"] == pytest.approx(1.0)


def test_slice_report_marks_small_slices_unreliable():
    y = np.array([1] * 5 + [0] * 15 + [1] * 60 + [0] * 400)
    proba = np.linspace(0, 1, len(y))
    slicer = np.array(["tiny"] * 20 + ["big"] * 460)
    rows = {r["slice"]: r for r in slice_report(y, proba, 0.5, slicer)}
    assert rows["tiny"]["reliable"] is False
    assert rows["big"]["reliable"] is True
    assert rows["tiny"]["n"] == 20


def test_slice_report_covers_every_row():
    rng = np.random.default_rng(0)
    y = (rng.random(500) < 0.2).astype(int)
    slicer = rng.choice(["a", "b", "c"], size=500)
    rows = slice_report(y, rng.random(500), 0.5, slicer)
    assert sum(r["n"] for r in rows) == 500
