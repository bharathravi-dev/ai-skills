"""Metric formulas, and the undefined cases that get quietly collapsed to 0."""

from __future__ import annotations

import math

import numpy as np
import pytest

from churnclf.metrics import (Confusion, accuracy, confusion_matrix,
                              expected_calibration_error, f1, fbeta, precision,
                              pr_auc, recall, report, roc_auc, specificity)

# The worked example from M3-L14 section 10, exercise 1.
CM = Confusion(tp=40, fp=10, fn=60, tn=890)


def test_worked_example_values():
    assert accuracy(CM) == pytest.approx(0.93)
    assert precision(CM) == pytest.approx(0.80)
    assert recall(CM) == pytest.approx(0.40)
    assert specificity(CM) == pytest.approx(890 / 900)
    assert f1(CM) == pytest.approx(0.5333, abs=1e-4)


def test_fbeta_directions():
    """F2 favours recall, F0.5 favours precision -- here recall is the weaker."""
    assert fbeta(CM, 2.0) < f1(CM) < fbeta(CM, 0.5)


def test_f1_is_the_harmonic_mean_not_the_arithmetic_one():
    cm = Confusion(tp=1, fp=0, fn=99, tn=0)      # precision 1.0, recall 0.01
    assert precision(cm) == pytest.approx(1.0)
    assert recall(cm) == pytest.approx(0.01)
    assert f1(cm) == pytest.approx(0.0198, abs=1e-4)
    assert f1(cm) < 0.5 * (precision(cm) + recall(cm)) / 10


def test_confusion_matrix_counts():
    y = np.array([1, 1, 1, 0, 0, 0, 0])
    p = np.array([1, 1, 0, 1, 0, 0, 0])
    cm = confusion_matrix(y, p)
    assert (cm.tp, cm.fp, cm.fn, cm.tn) == (2, 1, 1, 3)
    assert cm.total == 7
    assert cm.flagged == 3
    assert cm.positives == 3


def test_mismatched_lengths_raise():
    with pytest.raises(ValueError):
        confusion_matrix([1, 0, 1], [1, 0])


def test_precision_is_nan_when_nothing_is_flagged():
    """NaN, not 0. 'We flagged nothing' is not 'we were wrong about everything'."""
    cm = Confusion(tp=0, fp=0, fn=10, tn=90)
    assert math.isnan(precision(cm))
    assert recall(cm) == pytest.approx(0.0)


def test_precision_is_zero_when_every_flag_is_wrong():
    cm = Confusion(tp=0, fp=10, fn=10, tn=80)
    assert precision(cm) == pytest.approx(0.0)


def test_recall_is_nan_when_there_are_no_positives():
    cm = Confusion(tp=0, fp=5, fn=0, tn=95)
    assert math.isnan(recall(cm))


def test_fbeta_is_nan_when_either_component_is():
    assert math.isnan(fbeta(Confusion(tp=0, fp=0, fn=1, tn=9)))


def test_roc_auc_of_a_perfect_ranker_is_one():
    y = np.array([0, 0, 1, 1])
    assert roc_auc(y, np.array([0.1, 0.2, 0.8, 0.9])) == pytest.approx(1.0)


def test_roc_auc_of_a_reversed_ranker_is_zero():
    y = np.array([0, 0, 1, 1])
    assert roc_auc(y, np.array([0.9, 0.8, 0.2, 0.1])) == pytest.approx(0.0)


def test_roc_auc_of_constant_scores_is_one_half():
    y = np.array([0, 1, 0, 1])
    assert roc_auc(y, np.full(4, 0.3)) == pytest.approx(0.5)


def test_roc_auc_is_nan_with_one_class():
    assert math.isnan(roc_auc(np.zeros(5, dtype=int), np.linspace(0, 1, 5)))


def test_roc_auc_is_invariant_to_monotonic_transforms():
    """M3-L14 section 7.3 -- measured identical to six decimal places."""
    rng = np.random.default_rng(0)
    y = (rng.random(500) < 0.1).astype(int)
    p = rng.random(500)
    base = roc_auc(y, p)
    for transform in (lambda q: q ** 2, lambda q: q ** 3, np.sqrt,
                      lambda q: q * 0.5 + 0.25):
        assert roc_auc(y, transform(p)) == pytest.approx(base, abs=1e-12)


def test_pr_auc_of_a_perfect_ranker_is_one():
    y = np.array([0, 0, 1, 1])
    assert pr_auc(y, np.array([0.1, 0.2, 0.8, 0.9])) == pytest.approx(1.0)


def test_pr_auc_of_random_scores_is_near_the_base_rate():
    """A PR curve's random baseline is the base rate, not 0.5."""
    rng = np.random.default_rng(0)
    y = (rng.random(20000) < 0.05).astype(int)
    ap = pr_auc(y, rng.random(20000))
    assert ap == pytest.approx(0.05, abs=0.01)


def test_pr_auc_collapses_on_imbalance_where_roc_auc_does_not():
    rng = np.random.default_rng(1)
    score = rng.normal(size=20000)
    y_bal = (score + rng.normal(0, 1.0, 20000) > 0).astype(int)
    y_rare = (score + rng.normal(0, 1.0, 20000)
              > np.quantile(score, 0.99)).astype(int)
    assert roc_auc(y_rare, score) > 0.7
    assert pr_auc(y_rare, score) < pr_auc(y_bal, score) / 2


def test_ece_is_zero_for_a_perfectly_calibrated_model():
    rng = np.random.default_rng(0)
    p = rng.random(200000)
    y = (rng.random(200000) < p).astype(int)
    assert expected_calibration_error(y, p) < 0.01


def test_ece_grows_when_probabilities_are_shifted():
    rng = np.random.default_rng(0)
    p = rng.random(50000)
    y = (rng.random(50000) < p).astype(int)
    honest = expected_calibration_error(y, p)
    shifted = expected_calibration_error(y, np.clip(p * 0.5 + 0.25, 0, 1))
    assert shifted > honest + 0.05


def test_report_contains_every_key_and_the_base_rate():
    rng = np.random.default_rng(0)
    y = (rng.random(1000) < 0.1).astype(int)
    r = report(y, rng.random(1000), 0.5)
    for key in ("accuracy", "precision", "recall", "f1", "f2", "roc_auc",
                "pr_auc", "ece", "base_rate", "tp", "fp", "fn", "tn"):
        assert key in r
    assert r["base_rate"] == pytest.approx(y.mean())
    assert r["tp"] + r["fp"] + r["fn"] + r["tn"] == 1000
