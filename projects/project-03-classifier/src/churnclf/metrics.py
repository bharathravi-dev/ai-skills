"""Every classification metric, from the confusion matrix (M3-L14).

Undefined cases return NaN rather than 0. A precision of 0.0 means "we flagged
things and were wrong about all of them"; a precision of NaN means "we flagged
nothing". Collapsing those to the same number has ended real projects, so this
module keeps them distinct and the tests assert it.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class Confusion:
    tp: int
    fp: int
    fn: int
    tn: int

    @property
    def total(self) -> int:
        return self.tp + self.fp + self.fn + self.tn

    @property
    def flagged(self) -> int:
        return self.tp + self.fp

    @property
    def positives(self) -> int:
        return self.tp + self.fn


def confusion_matrix(y_true, y_pred) -> Confusion:
    y_true = np.asarray(y_true).astype(int)
    y_pred = np.asarray(y_pred).astype(int)
    if len(y_true) != len(y_pred):
        raise ValueError("y_true and y_pred must be the same length")
    return Confusion(
        tp=int(((y_pred == 1) & (y_true == 1)).sum()),
        fp=int(((y_pred == 1) & (y_true == 0)).sum()),
        fn=int(((y_pred == 0) & (y_true == 1)).sum()),
        tn=int(((y_pred == 0) & (y_true == 0)).sum()),
    )


def accuracy(cm: Confusion) -> float:
    return (cm.tp + cm.tn) / cm.total if cm.total else float("nan")


def precision(cm: Confusion) -> float:
    """NaN when nothing was flagged -- not 0. See the module docstring."""
    return cm.tp / cm.flagged if cm.flagged else float("nan")


def recall(cm: Confusion) -> float:
    """NaN when there are no positives to find."""
    return cm.tp / cm.positives if cm.positives else float("nan")


def specificity(cm: Confusion) -> float:
    neg = cm.tn + cm.fp
    return cm.tn / neg if neg else float("nan")


def fbeta(cm: Confusion, beta: float = 1.0) -> float:
    p, r = precision(cm), recall(cm)
    if math.isnan(p) or math.isnan(r):
        return float("nan")
    denom = beta**2 * p + r
    return (1 + beta**2) * p * r / denom if denom else 0.0


def f1(cm: Confusion) -> float:
    return fbeta(cm, 1.0)


def roc_auc(y_true, score) -> float:
    """P(random positive ranks above random negative), ties counted as 0.5."""
    y_true = np.asarray(y_true).astype(int)
    score = np.asarray(score, dtype=float)
    n_pos = int(y_true.sum())
    n_neg = len(y_true) - n_pos
    if n_pos == 0 or n_neg == 0:
        return float("nan")
    order = np.argsort(score, kind="mergesort")
    s = score[order]
    ranks = np.empty(len(s), dtype=float)
    i = 0
    while i < len(s):
        j = i
        while j + 1 < len(s) and s[j + 1] == s[i]:
            j += 1
        ranks[order[i:j + 1]] = (i + j) / 2 + 1      # mean rank within ties
        i = j + 1
    return float(
        (ranks[y_true == 1].sum() - n_pos * (n_pos + 1) / 2) / (n_pos * n_neg))


def pr_auc(y_true, score) -> float:
    """Average precision. Its random baseline is the BASE RATE, not 0.5."""
    y_true = np.asarray(y_true).astype(int)
    score = np.asarray(score, dtype=float)
    n_pos = int(y_true.sum())
    if n_pos == 0:
        return float("nan")
    order = np.argsort(-score, kind="mergesort")
    y = y_true[order]
    tp = np.cumsum(y)
    fp = np.cumsum(1 - y)
    prec = tp / np.maximum(tp + fp, 1)
    rec = tp / n_pos
    ap, prev = 0.0, 0.0
    for p_v, r_v in zip(prec, rec):
        ap += p_v * (r_v - prev)
        prev = r_v
    return float(ap)


def expected_calibration_error(y_true, proba, bins: int = 10) -> float:
    y_true = np.asarray(y_true, dtype=float)
    proba = np.asarray(proba, dtype=float)
    edges = np.linspace(0.0, 1.0, bins + 1)
    total = 0.0
    for lo, hi in zip(edges[:-1], edges[1:]):
        mask = (proba >= lo) & (proba < hi if hi < 1.0 else proba <= hi)
        if not mask.any():
            continue
        total += mask.mean() * abs(proba[mask].mean() - y_true[mask].mean())
    return float(total)


def report(y_true, proba, threshold: float) -> dict:
    """Every metric at one threshold, plus the threshold-free ranking scores."""
    y_true = np.asarray(y_true).astype(int)
    proba = np.asarray(proba, dtype=float)
    cm = confusion_matrix(y_true, (proba >= threshold).astype(int))
    return {
        "threshold": float(threshold),
        "tp": cm.tp, "fp": cm.fp, "fn": cm.fn, "tn": cm.tn,
        "flagged": cm.flagged,
        "accuracy": accuracy(cm),
        "precision": precision(cm),
        "recall": recall(cm),
        "specificity": specificity(cm),
        "f1": f1(cm),
        "f2": fbeta(cm, 2.0),
        "roc_auc": roc_auc(y_true, proba),
        "pr_auc": pr_auc(y_true, proba),
        "ece": expected_calibration_error(y_true, proba),
        "base_rate": float(y_true.mean()),
    }
