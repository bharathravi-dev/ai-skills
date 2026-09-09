"""Splitting strategies (M3-L13).

Every function here returns index arrays, never copies of the data, so that a
caller can always trace a prediction back to the row it came from. Splits are
deterministic given a seed.

The one rule this module exists to enforce: NO CUSTOMER APPEARS ON BOTH SIDES.
`grouped_temporal_split` is the only splitter the pipeline uses; the simpler
ones are provided so the tests can demonstrate what they get wrong.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class Split:
    train: np.ndarray
    val: np.ndarray
    test: np.ndarray

    def sizes(self) -> tuple[int, int, int]:
        return len(self.train), len(self.val), len(self.test)


def random_split(n: int, val_frac: float, test_frac: float, seed: int) -> Split:
    """A plain random split. WRONG for grouped data -- kept for comparison."""
    rng = np.random.default_rng(seed)
    idx = rng.permutation(n)
    n_test = int(round(test_frac * n))
    n_val = int(round(val_frac * n))
    return Split(train=idx[n_test + n_val:], val=idx[n_test:n_test + n_val],
                 test=idx[:n_test])


def stratified_split(y: np.ndarray, val_frac: float, test_frac: float,
                     seed: int) -> Split:
    """Preserve class proportions in every part (M3-L13 section 5.2)."""
    rng = np.random.default_rng(seed)
    train, val, test = [], [], []
    for cls in np.unique(y):
        cls_idx = rng.permutation(np.where(y == cls)[0])
        n_test = int(round(test_frac * len(cls_idx)))
        n_val = int(round(val_frac * len(cls_idx)))
        test.extend(cls_idx[:n_test])
        val.extend(cls_idx[n_test:n_test + n_val])
        train.extend(cls_idx[n_test + n_val:])
    return Split(train=np.array(sorted(train)), val=np.array(sorted(val)),
                 test=np.array(sorted(test)))


def grouped_temporal_split(
    groups: np.ndarray,
    month: np.ndarray,
    val_frac: float = 0.15,
    test_frac: float = 0.20,
    seed: int = 20260908,
    gap_months: int = 1,
    eval_months: int = 2,
) -> Split:
    """The splitter the pipeline uses. Grouped by customer AND ordered by time.

    Customers are partitioned first, so no customer spans two parts. Within
    that, evaluation keeps only the last `eval_months` months and training only
    the earliest, with `gap_months` discarded between them so that a rolling
    feature cannot straddle the boundary (M3-L13 section 5.6).

    `eval_months` trades evaluation-set size against how far into the future
    you are claiming to predict. One month gives the cleanest claim and the
    noisiest estimate; the default of two is a compromise, and M3-L13 section
    5.4 is the reason it is not one.

    Returns index arrays into the full dataset.
    """
    if not 0 < val_frac < 1 or not 0 < test_frac < 1:
        raise ValueError("val_frac and test_frac must be in (0, 1)")
    if val_frac + test_frac >= 1:
        raise ValueError("val_frac + test_frac must leave room for training")
    if gap_months < 0:
        raise ValueError("gap_months must be >= 0")

    rng = np.random.default_rng(seed)
    unique_groups = rng.permutation(np.unique(groups))
    n_test_g = int(round(test_frac * len(unique_groups)))
    n_val_g = int(round(val_frac * len(unique_groups)))
    if n_test_g == 0 or n_val_g == 0:
        raise ValueError("too few groups for the requested fractions")

    test_g = set(unique_groups[:n_test_g].tolist())
    val_g = set(unique_groups[n_test_g:n_test_g + n_val_g].tolist())

    max_month = int(month.max())
    eval_start = max_month - eval_months + 1       # evaluation months
    train_end = eval_start - gap_months            # training months < this
    if train_end <= int(month.min()):
        raise ValueError(
            f"no training months left: eval_months={eval_months} and "
            f"gap_months={gap_months} consume the whole {max_month + 1}-month span"
        )

    train, val, test = [], [], []
    for i, (g, m) in enumerate(zip(groups, month)):
        if g in test_g:
            if m >= eval_start:
                test.append(i)
        elif g in val_g:
            if m >= eval_start:
                val.append(i)
        elif m < train_end:
            train.append(i)

    split = Split(train=np.array(train), val=np.array(val), test=np.array(test))
    assert_no_group_leak(groups, split)
    return split


def assert_no_group_leak(groups: np.ndarray, split: Split) -> None:
    """Raise if any group appears in more than one part. Called on every split."""
    g_train = set(groups[split.train].tolist())
    g_val = set(groups[split.val].tolist())
    g_test = set(groups[split.test].tolist())
    for a, b, name in ((g_train, g_val, "train/val"),
                       (g_train, g_test, "train/test"),
                       (g_val, g_test, "val/test")):
        overlap = a & b
        if overlap:
            raise AssertionError(
                f"group leak between {name}: {len(overlap)} shared groups, "
                f"e.g. {sorted(overlap)[:5]}"
            )


def stratified_kfold(y: np.ndarray, k: int, seed: int) -> list[np.ndarray]:
    """Stratified k-fold indices. Every row appears in exactly one fold."""
    if k < 2:
        raise ValueError("k must be at least 2")
    rng = np.random.default_rng(seed)
    folds: list[list[int]] = [[] for _ in range(k)]
    for cls in np.unique(y):
        cls_idx = rng.permutation(np.where(y == cls)[0])
        for i, row in enumerate(cls_idx):
            folds[i % k].append(int(row))
    return [np.array(sorted(f)) for f in folds]
