"""The generator must produce the three properties the project is about."""

from __future__ import annotations

import numpy as np

from churnclf.data import FEATURE_NAMES, make_churn_data


def test_shapes_are_consistent(data):
    assert data.X.shape == (len(data), len(FEATURE_NAMES))
    assert data.y.shape == (len(data),)
    assert data.groups.shape == (len(data),)
    assert data.month.shape == (len(data),)
    assert data.feature_names == FEATURE_NAMES


def test_labels_are_binary(data):
    assert set(np.unique(data.y).tolist()) <= {0, 1}


def test_data_is_imbalanced(data):
    assert 0.02 < data.base_rate < 0.15, f"base rate {data.base_rate}"


def test_every_customer_appears_in_every_month(data):
    counts = np.bincount(data.groups)
    assert counts.min() == counts.max(), "customers must have equal history"


def test_features_are_standardised(data):
    assert np.allclose(data.X.mean(axis=0), 0.0, atol=1e-9)
    assert np.allclose(data.X.std(axis=0), 1.0, atol=1e-9)


def test_generation_is_deterministic():
    a = make_churn_data(n_customers=200, months=6, seed=7)
    b = make_churn_data(n_customers=200, months=6, seed=7)
    assert np.array_equal(a.y, b.y)
    assert np.allclose(a.X, b.X)


def test_different_seeds_give_different_data():
    a = make_churn_data(n_customers=200, months=6, seed=7)
    b = make_churn_data(n_customers=200, months=6, seed=8)
    assert not np.array_equal(a.y, b.y)


def test_churn_rate_trends_upward_over_months(data):
    """The temporal trend must be real, or the temporal split proves nothing."""
    rates = [data.y[data.month == m].mean() for m in range(int(data.month.max()) + 1)]
    first_half = float(np.mean(rates[: len(rates) // 2]))
    second_half = float(np.mean(rates[len(rates) // 2:]))
    assert second_half > first_half, (first_half, second_half)


def test_leaky_feature_is_opt_in_and_adds_a_column():
    honest = make_churn_data(n_customers=200, months=6, seed=7)
    leaky = make_churn_data(n_customers=200, months=6, seed=7,
                            add_leaky_feature=True)
    assert len(honest.feature_names) == len(FEATURE_NAMES)
    assert leaky.feature_names[-1] == "customer_churn_rate_alltime"
    assert leaky.X.shape[1] == honest.X.shape[1] + 1
    # The labels must be identical -- only the feature set changed.
    assert np.array_equal(honest.y, leaky.y)


def test_leaky_feature_really_does_contain_the_answer():
    leaky = make_churn_data(n_customers=200, months=6, seed=7,
                            add_leaky_feature=True)
    rate = leaky.raw[:, -1]
    # Rows whose customer churned more often carry a higher value, by
    # construction -- that is exactly why it must never be built this way.
    assert np.corrcoef(rate, leaky.y)[0, 1] > 0.2
