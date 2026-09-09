"""Shared fixtures. A small dataset so the suite stays fast."""

from __future__ import annotations

import numpy as np
import pytest

from churnclf.data import make_churn_data
from churnclf.split import grouped_temporal_split

SEED = 20260908


@pytest.fixture(scope="session")
def data():
    return make_churn_data(n_customers=400, months=10, seed=SEED)


@pytest.fixture(scope="session")
def split(data):
    return grouped_temporal_split(data.groups, data.month, seed=SEED)


@pytest.fixture(scope="session")
def rng():
    return np.random.default_rng(SEED)
