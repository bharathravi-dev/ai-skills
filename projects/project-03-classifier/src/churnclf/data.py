"""Synthetic churn data.

SYNTHETIC ONLY. No real customer data is used, required or shipped anywhere in
this course. The generator is deterministic given a seed, so every number in
the report is reproducible.

The data is built with three properties that make honest evaluation hard, all
of which appear in real churn datasets:

1. GROUPED   -- each customer contributes several monthly snapshots, and a
                customer has a persistent latent "churn propensity". A random
                split lets the model memorise individuals (M3-L13 section 5.3).
2. IMBALANCED-- about 6% of snapshots churn, so accuracy is nearly useless
                (M3-L14 section 6).
3. TEMPORAL  -- churn propensity drifts upward over the observed months, so a
                random split trains on the future (M3-L13 section 5.6).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

FEATURE_NAMES = (
    "tenure_months",
    "monthly_spend",
    "support_tickets",
    "logins_last_30d",
    "days_since_last_login",
    "has_annual_contract",
)


@dataclass(frozen=True)
class Dataset:
    """A generated dataset. Frozen so callers cannot mutate it by accident."""

    X: np.ndarray            # (n, n_features) standardised features
    y: np.ndarray            # (n,) int 0/1
    groups: np.ndarray       # (n,) customer id
    month: np.ndarray        # (n,) 0-based month index
    feature_names: tuple[str, ...]
    raw: np.ndarray          # (n, n_features) unstandardised, for slicing
    means: np.ndarray
    stds: np.ndarray

    def __len__(self) -> int:
        return len(self.y)

    @property
    def base_rate(self) -> float:
        return float(self.y.mean())


def make_churn_data(
    n_customers: int = 3000,
    months: int = 12,
    seed: int = 20260908,
    target_base_rate: float = 0.06,
    add_leaky_feature: bool = False,
) -> Dataset:
    """Generate a grouped, imbalanced, time-ordered churn dataset.

    `add_leaky_feature=True` appends `customer_churn_rate_alltime`: each
    customer's mean label computed over EVERY month, including the months used
    for evaluation. This is target encoding without a fold-safe scheme -- the
    single most common leakage bug in tabular machine learning, and it is
    included here so the pipeline can measure what it does rather than assert
    it. Never compute a feature this way for real.
    """
    rng = np.random.default_rng(seed)

    # Each customer has a latent propensity that no feature reveals directly.
    # This is what a random split lets the model memorise.
    propensity = rng.normal(0.0, 0.9, size=n_customers)

    rows, groups, month_idx = [], [], []
    for m in range(months):
        tenure = rng.integers(1, 72, size=n_customers).astype(float) + m
        spend = np.clip(rng.gamma(shape=4.0, scale=18.0, size=n_customers), 5, 400)
        tickets = rng.poisson(lam=np.clip(0.4 + propensity * 0.35, 0.05, None))
        logins = np.clip(
            rng.poisson(lam=np.clip(14 - propensity * 4.0, 0.5, None)), 0, None
        ).astype(float)
        scale = np.clip(3.0 + propensity * 2.5, 0.3, None)
        days_since = np.clip(rng.exponential(scale=scale), 0, 60)
        annual = (rng.random(n_customers) < 0.35).astype(float)

        rows.append(np.column_stack([tenure, spend, tickets, logins,
                                     days_since, annual]))
        groups.append(np.arange(n_customers))
        month_idx.append(np.full(n_customers, m))

    raw = np.vstack(rows)
    groups_arr = np.concatenate(groups)
    month_arr = np.concatenate(month_idx)

    # The true log-odds: observable drivers, plus the latent customer effect,
    # plus a mild upward trend over months.
    tenure, spend, tickets, logins, days_since, annual = raw.T
    logit = (
        0.55 * tickets
        + 0.085 * days_since
        - 0.075 * logins
        - 0.010 * tenure
        - 0.0016 * spend
        - 0.80 * annual
        + 0.85 * propensity[groups_arr]
        + 0.045 * month_arr
    )
    logit = logit - logit.mean()
    logit = logit + _intercept_for(logit, target_base_rate)
    y = (rng.random(len(logit)) < _sigmoid(logit)).astype(int)

    names = FEATURE_NAMES
    if add_leaky_feature:
        # LEAKY BY CONSTRUCTION -- see the docstring. Uses the labels of every
        # month, so a row's feature already contains its own answer.
        rate = np.zeros(n_customers)
        for g in range(n_customers):
            rate[g] = y[groups_arr == g].mean()
        raw = np.column_stack([raw, rate[groups_arr]])
        names = FEATURE_NAMES + ("customer_churn_rate_alltime",)

    means = raw.mean(axis=0)
    stds = raw.std(axis=0)
    stds[stds == 0] = 1.0
    X = (raw - means) / stds

    return Dataset(X=X, y=y, groups=groups_arr, month=month_arr,
                   feature_names=names, raw=raw, means=means, stds=stds)


def _sigmoid(z: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-np.clip(z, -500, 500)))


def _intercept_for(logit: np.ndarray, target: float) -> float:
    """Bisect for the intercept giving the requested mean event probability."""
    lo, hi = -50.0, 50.0
    for _ in range(200):
        mid = (lo + hi) / 2
        if _sigmoid(logit + mid).mean() > target:
            hi = mid
        else:
            lo = mid
    return (lo + hi) / 2
