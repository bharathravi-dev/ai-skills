"""The gradient is derived by hand, so it is verified numerically here.

M3-L11 section 7.3 measured a real bug passing a gradient check on one
convenient input, so every check below runs on several different subsets.
"""

from __future__ import annotations

import numpy as np
import pytest

from churnclf.model import LogisticRegression, class_weights, sigmoid


def test_sigmoid_basics():
    assert sigmoid(np.array([0.0]))[0] == pytest.approx(0.5)
    assert sigmoid(np.array([-1000.0]))[0] == pytest.approx(0.0, abs=1e-12)
    assert sigmoid(np.array([1000.0]))[0] == pytest.approx(1.0, abs=1e-12)


def test_sigmoid_does_not_overflow():
    with np.errstate(over="raise"):
        sigmoid(np.array([-1e9, 1e9]))


def test_class_weights_balance_the_classes():
    y = np.array([0] * 95 + [1] * 5)
    w = class_weights(y)
    assert w[y == 1].sum() == pytest.approx(w[y == 0].sum())
    assert w[y == 1][0] > w[y == 0][0]


def test_class_weights_degrade_gracefully_on_one_class():
    assert np.all(class_weights(np.zeros(10, dtype=int)) == 1.0)


@pytest.mark.parametrize("check_seed", [0, 1, 2, 3, 4])
def test_gradient_matches_numerical_on_several_subsets(data, split, check_seed):
    rng = np.random.default_rng(check_seed)
    sub = rng.choice(split.train, size=300, replace=False)
    worst = LogisticRegression().gradient_check(
        data.X[sub], data.y[sub],
        sample_weight=class_weights(data.y[sub]), seed=check_seed)
    assert worst < 1e-7, f"worst relative error {worst:.2e}"


def test_gradient_check_also_passes_unweighted(data, split):
    worst = LogisticRegression().gradient_check(
        data.X[split.train[:300]], data.y[split.train[:300]], seed=0)
    assert worst < 1e-7


def test_a_broken_gradient_is_caught():
    """A deliberately wrong gradient must FAIL the check, or the check is
    decorative. This guards the guard."""

    class Broken(LogisticRegression):
        def loss_and_grad(self, X, y, w, b, sample_weight):
            loss, gw, gb = super().loss_and_grad(X, y, w, b, sample_weight)
            return loss, gw * 0.5, gb          # half the true weight gradient

    rng = np.random.default_rng(0)
    X = rng.normal(size=(200, 6))
    y = (rng.random(200) < 0.2).astype(float)
    assert Broken().gradient_check(X, y, seed=0) > 1e-4


def test_training_reduces_the_loss(data, split):
    m = LogisticRegression(steps=400).fit(
        data.X[split.train], data.y[split.train],
        sample_weight=class_weights(data.y[split.train]))
    assert m.history[-1] < m.history[0]
    assert all(np.isfinite(m.history))


def test_loss_decreases_monotonically_enough(data, split):
    """Gradient descent with a fixed rate should not oscillate here."""
    m = LogisticRegression(steps=300).fit(
        data.X[split.train], data.y[split.train])
    increases = sum(1 for a, b in zip(m.history, m.history[1:]) if b > a + 1e-12)
    assert increases == 0, f"{increases} steps increased the loss"


def test_predictions_are_probabilities(data, split):
    m = LogisticRegression(steps=300).fit(
        data.X[split.train], data.y[split.train])
    p = m.predict_proba(data.X[split.test])
    assert p.shape == (len(split.test),)
    assert np.all((p >= 0.0) & (p <= 1.0))


def test_model_beats_a_coin_flip(data, split):
    from churnclf.metrics import roc_auc
    m = LogisticRegression().fit(
        data.X[split.train], data.y[split.train],
        sample_weight=class_weights(data.y[split.train]))
    auc = roc_auc(data.y[split.test], m.predict_proba(data.X[split.test]))
    assert auc > 0.65, f"ROC-AUC {auc:.4f} -- the model learned nothing"


def test_l2_shrinks_the_weights(data, split):
    weak = LogisticRegression(l2=0.0, steps=500).fit(
        data.X[split.train], data.y[split.train])
    strong = LogisticRegression(l2=1.0, steps=500).fit(
        data.X[split.train], data.y[split.train])
    assert np.linalg.norm(strong.w) < np.linalg.norm(weak.w)


def test_l2_does_not_penalise_the_bias(data, split):
    """A heavily regularised model must still track the base rate, not 0.5.

    Note the learning rate: gradient descent on an L2 term is stable only while
    `lr < 2 / l2` (M3-L12 section 7.3 measured this limit directly). At lr=0.5
    the largest usable l2 is just under 4, so a strong-regularisation test has
    to lower the rate as well -- which is itself the lesson.
    """
    m = LogisticRegression(l2=20.0, lr=0.05, steps=4000).fit(
        data.X[split.train], data.y[split.train])
    assert np.linalg.norm(m.w) < 0.05, "weights should be crushed"
    mean_pred = float(m.predict_proba(data.X[split.train]).mean())
    assert mean_pred == pytest.approx(data.y[split.train].mean(), abs=0.02)


def test_high_l2_with_a_high_learning_rate_oscillates(data, split):
    """The stability limit is real: lr * l2 > 2 makes the loss oscillate.

    The model does not produce nan -- gradient clipping catches that -- so the
    only symptom is a loss that never settles. This test exists so that the
    failure mode is documented rather than discovered later.
    """
    m = LogisticRegression(l2=50.0, lr=0.5, steps=400).fit(
        data.X[split.train], data.y[split.train])
    tail = m.history[-20:]
    assert max(tail) - min(tail) > 1.0, "expected an oscillating loss"
    assert all(np.isfinite(m.history)), "clipping should still prevent nan"


def test_predict_before_fit_raises():
    with pytest.raises(RuntimeError, match="fit"):
        LogisticRegression().predict_proba(np.zeros((3, 4)))


def test_mismatched_feature_count_raises(data, split):
    m = LogisticRegression(steps=50).fit(data.X[split.train],
                                         data.y[split.train])
    with pytest.raises(ValueError, match="features"):
        m.predict_proba(np.zeros((5, 99)))


def test_mismatched_row_counts_raise():
    with pytest.raises(ValueError, match="rows"):
        LogisticRegression().fit(np.zeros((10, 3)), np.zeros(9))


def test_one_dimensional_x_is_rejected():
    with pytest.raises(ValueError, match="2-D"):
        LogisticRegression().fit(np.zeros(10), np.zeros(10))


def test_training_is_reproducible(data, split):
    a = LogisticRegression(steps=200).fit(data.X[split.train],
                                          data.y[split.train])
    b = LogisticRegression(steps=200).fit(data.X[split.train],
                                          data.y[split.train])
    assert np.array_equal(a.w, b.w)
    assert a.b == b.b


def test_gradient_clipping_survives_an_extreme_row(data, split):
    """One poisoned row must not produce nan (M3-L12 section 7.3)."""
    X = data.X[split.train].copy()
    y = data.y[split.train].copy()
    X[0] = 1e6
    m = LogisticRegression(steps=200, clip_norm=1.0).fit(X, y)
    assert np.all(np.isfinite(m.w))
    assert np.isfinite(m.b)
    assert all(np.isfinite(m.history))
