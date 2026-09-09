"""The splitter's job is to make one specific kind of cheating impossible."""

from __future__ import annotations

import numpy as np
import pytest

from churnclf.split import (Split, assert_no_group_leak, grouped_temporal_split,
                            random_split, stratified_kfold, stratified_split)


def test_no_customer_spans_two_parts(data, split):
    g_train = set(data.groups[split.train].tolist())
    g_val = set(data.groups[split.val].tolist())
    g_test = set(data.groups[split.test].tolist())
    assert not (g_train & g_val)
    assert not (g_train & g_test)
    assert not (g_val & g_test)


def test_training_months_strictly_precede_evaluation_months(data, split):
    train_max = int(data.month[split.train].max())
    val_min = int(data.month[split.val].min())
    test_min = int(data.month[split.test].min())
    assert train_max < val_min
    assert train_max < test_min


def test_gap_month_is_actually_discarded(data, split):
    """A row exists in the gap month, and no part contains it."""
    train_max = int(data.month[split.train].max())
    eval_min = int(data.month[split.test].min())
    assert eval_min - train_max >= 2, "there must be a discarded month between"
    gap_months = set(range(train_max + 1, eval_min))
    assigned = np.concatenate([split.train, split.val, split.test])
    assert not (set(data.month[assigned].tolist()) & gap_months)


def test_parts_are_disjoint_and_non_empty(split):
    all_idx = np.concatenate([split.train, split.val, split.test])
    assert len(set(all_idx.tolist())) == len(all_idx)
    for part in (split.train, split.val, split.test):
        assert len(part) > 0


def test_split_is_deterministic(data):
    a = grouped_temporal_split(data.groups, data.month, seed=1)
    b = grouped_temporal_split(data.groups, data.month, seed=1)
    assert np.array_equal(a.test, b.test)
    c = grouped_temporal_split(data.groups, data.month, seed=2)
    assert not np.array_equal(a.test, c.test)


def test_random_split_does_leak_groups(data):
    """The comparison case. Kept so the test suite documents what is wrong."""
    bad = random_split(len(data), 0.15, 0.20, seed=1)
    overlap = (set(data.groups[bad.train].tolist())
               & set(data.groups[bad.test].tolist()))
    assert len(overlap) > 0, "a random split on grouped data must overlap"


def test_assert_no_group_leak_raises_on_a_leak(data):
    bad = random_split(len(data), 0.15, 0.20, seed=1)
    with pytest.raises(AssertionError, match="group leak"):
        assert_no_group_leak(data.groups, bad)


def test_stratified_split_preserves_class_proportions(data):
    s = stratified_split(data.y, 0.15, 0.20, seed=1)
    overall = data.y.mean()
    for part in (s.train, s.val, s.test):
        assert abs(data.y[part].mean() - overall) < 0.01


def test_stratified_kfold_covers_every_row_exactly_once(data):
    folds = stratified_kfold(data.y, k=5, seed=1)
    assert len(folds) == 5
    combined = np.concatenate(folds)
    assert len(combined) == len(data)
    assert len(set(combined.tolist())) == len(data)


def test_stratified_kfold_balances_positives(data):
    folds = stratified_kfold(data.y, k=5, seed=1)
    counts = [int(data.y[f].sum()) for f in folds]
    assert max(counts) - min(counts) <= 1


@pytest.mark.parametrize("kwargs", [
    {"val_frac": 0.0}, {"test_frac": 1.0}, {"val_frac": 0.6, "test_frac": 0.5},
    {"gap_months": -1},
])
def test_invalid_fractions_are_rejected(data, kwargs):
    with pytest.raises(ValueError):
        grouped_temporal_split(data.groups, data.month, **kwargs)


def test_impossible_time_budget_is_rejected(data):
    with pytest.raises(ValueError, match="no training months"):
        grouped_temporal_split(data.groups, data.month, eval_months=9,
                               gap_months=1)
