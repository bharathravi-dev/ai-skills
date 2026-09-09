"""Threshold selection, baselines and slicing (M3-L13, M3-L14).

Every function that chooses something takes VALIDATION data. None of them
accepts a test set -- the pipeline never passes one, and that is enforced by
naming rather than by hope: read `train.py` and the test set appears exactly
once, in the final report.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from .metrics import confusion_matrix, f1, fbeta, precision, recall


@dataclass(frozen=True)
class ThresholdChoice:
    threshold: float
    method: str
    rationale: str
    achieved: dict


THRESHOLD_GRID = np.linspace(0.005, 0.995, 199)


def _stats(y, proba, t):
    cm = confusion_matrix(y, (proba >= t).astype(int))
    return cm, precision(cm), recall(cm)


def choose_threshold_by_cost(y_val, proba_val, cost_fp: float,
                             cost_fn: float) -> ThresholdChoice:
    """Minimise expected cost. The most defensible method (M3-L14 section 5.4).

    Requires someone to state what a miss actually costs, which is usually the
    most useful conversation the project produces.
    """
    if cost_fp <= 0 or cost_fn <= 0:
        raise ValueError("costs must be positive")
    best_t, best_cost = 0.5, math.inf
    for t in THRESHOLD_GRID:
        cm, _, _ = _stats(y_val, proba_val, t)
        cost = cm.fp * cost_fp + cm.fn * cost_fn
        if cost < best_cost:
            best_cost, best_t = cost, float(t)
    cm, p, r = _stats(y_val, proba_val, best_t)
    return ThresholdChoice(
        threshold=best_t,
        method="expected cost",
        rationale=(f"minimises {cost_fp:g}*FP + {cost_fn:g}*FN on validation; "
                   f"expected cost {best_cost:,.0f}"),
        achieved={"precision": p, "recall": r, "fp": cm.fp, "fn": cm.fn},
    )


def choose_threshold_by_capacity(proba_val, capacity_frac: float
                                 ) -> ThresholdChoice:
    """Flag roughly `capacity_frac` of rows -- a real constraint, often binding."""
    if not 0 < capacity_frac < 1:
        raise ValueError("capacity_frac must be in (0, 1)")
    t = float(np.quantile(proba_val, 1 - capacity_frac))
    return ThresholdChoice(
        threshold=t, method="capacity",
        rationale=f"flags about {capacity_frac:.1%} of rows for review",
        achieved={},
    )


def choose_threshold_by_recall(y_val, proba_val, target_recall: float
                               ) -> ThresholdChoice | None:
    """Lowest threshold meeting a recall requirement, or None if unreachable.

    Returning None matters: M3-L14 section 7.3 shows that discovering a
    requirement is unachievable -- and what it would cost to approach it -- is
    a more useful deliverable than a threshold that quietly misses it.
    """
    for t in sorted(THRESHOLD_GRID, reverse=True):
        cm, p, r = _stats(y_val, proba_val, t)
        if not math.isnan(r) and r >= target_recall:
            return ThresholdChoice(
                threshold=float(t), method="recall requirement",
                rationale=f"lowest threshold reaching recall >= {target_recall:.0%}",
                achieved={"precision": p, "recall": r, "fp": cm.fp},
            )
    return None


def choose_threshold_by_fbeta(y_val, proba_val, beta: float = 1.0
                              ) -> ThresholdChoice:
    best_t, best_score = 0.5, -1.0
    for t in THRESHOLD_GRID:
        cm, _, _ = _stats(y_val, proba_val, t)
        score = fbeta(cm, beta)
        if not math.isnan(score) and score > best_score:
            best_score, best_t = score, float(t)
    cm, p, r = _stats(y_val, proba_val, best_t)
    return ThresholdChoice(
        threshold=best_t, method=f"maximise F{beta:g}",
        rationale=f"best F{beta:g} on validation = {best_score:.4f}",
        achieved={"precision": p, "recall": r},
    )


def baselines(y_true, base_rate: float, seed: int = 0) -> dict[str, dict]:
    """The references every model must be reported against (M3-L14 section 5.6)."""
    y_true = np.asarray(y_true).astype(int)
    rng = np.random.default_rng(seed)
    out = {}

    cm = confusion_matrix(y_true, np.zeros(len(y_true), dtype=int))
    out["always negative"] = {
        "accuracy": (cm.tp + cm.tn) / cm.total, "recall": recall(cm),
        "precision": precision(cm), "f1": f1(cm), "flagged": cm.flagged}

    cm = confusion_matrix(y_true, np.ones(len(y_true), dtype=int))
    out["always positive"] = {
        "accuracy": (cm.tp + cm.tn) / cm.total, "recall": recall(cm),
        "precision": precision(cm), "f1": f1(cm), "flagged": cm.flagged}

    guess = (rng.random(len(y_true)) < base_rate).astype(int)
    cm = confusion_matrix(y_true, guess)
    out[f"random at base rate ({base_rate:.1%})"] = {
        "accuracy": (cm.tp + cm.tn) / cm.total, "recall": recall(cm),
        "precision": precision(cm), "f1": f1(cm), "flagged": cm.flagged}
    return out


def slice_report(y_true, proba, threshold: float, slicer: np.ndarray,
                 min_support: int = 30) -> list[dict]:
    """Per-slice metrics. Slices below `min_support` are reported, not hidden.

    Suppressing small slices entirely lets a failure disappear; reporting them
    with their support lets the reader discount them appropriately. Small
    slices in a PUBLISHED artefact are a disclosure risk (M3-L14 section 9) --
    that is a separate decision from whether you look at them yourself.
    """
    y_true = np.asarray(y_true).astype(int)
    pred = (np.asarray(proba) >= threshold).astype(int)
    rows = []
    for value in np.unique(slicer):
        mask = slicer == value
        cm = confusion_matrix(y_true[mask], pred[mask])
        rows.append({
            "slice": value, "n": int(mask.sum()),
            "positives": cm.positives,
            "accuracy": (cm.tp + cm.tn) / cm.total if cm.total else float("nan"),
            "precision": precision(cm), "recall": recall(cm),
            "reliable": bool(mask.sum() >= min_support and cm.positives >= 10),
        })
    return rows
