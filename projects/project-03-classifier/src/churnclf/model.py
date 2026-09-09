"""Logistic regression, implemented directly (M3-L09, M3-L11, M3-L12).

No scikit-learn. The gradient is derived by hand and verified numerically by
`gradient_check`, which the test suite runs -- the same discipline M3-L11
section 5.5 argues for, including checking on more than one input.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np


def sigmoid(z: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-np.clip(z, -500, 500)))


def class_weights(y: np.ndarray) -> np.ndarray:
    """Per-row weights that balance the classes (M3-L13 section 5.7)."""
    n = len(y)
    n_pos = int(y.sum())
    n_neg = n - n_pos
    if n_pos == 0 or n_neg == 0:
        return np.ones(n)
    w_pos = n / (2.0 * n_pos)
    w_neg = n / (2.0 * n_neg)
    return np.where(y == 1, w_pos, w_neg)


@dataclass
class LogisticRegression:
    """Binary logistic regression trained by gradient descent with L2 decay."""

    lr: float = 0.5
    steps: int = 3000
    l2: float = 1e-3
    clip_norm: float | None = 5.0
    seed: int = 20260908
    w: np.ndarray | None = field(default=None, init=False)
    b: float = field(default=0.0, init=False)
    history: list[float] = field(default_factory=list, init=False)

    # -- core -------------------------------------------------------------
    def loss_and_grad(self, X, y, w, b, sample_weight):
        """Weighted binary cross-entropy plus L2, and its exact gradient.

        The L2 term deliberately excludes the bias: penalising the intercept
        would bias predictions toward 0.5 rather than toward the base rate.
        """
        n = len(y)
        sw = sample_weight / sample_weight.mean()
        p = sigmoid(X @ w + b)
        pc = np.clip(p, 1e-12, 1 - 1e-12)
        nll = -(sw * (y * np.log(pc) + (1 - y) * np.log(1 - pc))).sum() / n
        loss = nll + 0.5 * self.l2 * float(w @ w)
        err = sw * (p - y) / n
        return loss, (X.T @ err + self.l2 * w), float(err.sum())

    def fit(self, X, y, sample_weight=None):
        X = np.asarray(X, dtype=float)
        y = np.asarray(y, dtype=float)
        if X.ndim != 2:
            raise ValueError(f"X must be 2-D, got shape {X.shape}")
        if len(X) != len(y):
            raise ValueError(f"X has {len(X)} rows but y has {len(y)}")
        sw = np.ones(len(y)) if sample_weight is None else np.asarray(
            sample_weight, dtype=float)

        self.w = np.zeros(X.shape[1])
        self.b = 0.0
        self.history = []
        for _ in range(self.steps):
            loss, gw, gb = self.loss_and_grad(X, y, self.w, self.b, sw)
            self.history.append(loss)
            if self.clip_norm is not None:
                norm = float(np.sqrt((gw ** 2).sum() + gb ** 2))
                if norm > self.clip_norm:
                    scale = self.clip_norm / norm
                    gw, gb = gw * scale, gb * scale
            self.w -= self.lr * gw
            self.b -= self.lr * gb
        return self

    def predict_proba(self, X) -> np.ndarray:
        if self.w is None:
            raise RuntimeError("call fit() before predict_proba()")
        X = np.asarray(X, dtype=float)
        if X.shape[1] != len(self.w):
            raise ValueError(
                f"X has {X.shape[1]} features, model expects {len(self.w)}")
        return sigmoid(X @ self.w + self.b)

    def predict(self, X, threshold: float = 0.5) -> np.ndarray:
        return (self.predict_proba(X) >= threshold).astype(int)

    # -- verification ------------------------------------------------------
    def gradient_check(self, X, y, sample_weight=None, h: float = 1e-5,
                       seed: int = 0, n_checks: int = 12) -> float:
        """Worst relative error between analytic and numerical gradients.

        M3-L11 section 7.3 measured that a real bug can pass a check run on one
        convenient input, so the caller is expected to run this on several
        different subsets -- which `tests/test_model.py` does.
        """
        X = np.asarray(X, dtype=float)
        y = np.asarray(y, dtype=float)
        sw = np.ones(len(y)) if sample_weight is None else np.asarray(
            sample_weight, dtype=float)
        rng = np.random.default_rng(seed)
        w = rng.normal(0, 0.4, size=X.shape[1])
        b = float(rng.normal(0, 0.4))

        _, gw, gb = self.loss_and_grad(X, y, w, b, sw)
        worst = 0.0
        picks = rng.choice(len(w), size=min(n_checks, len(w)), replace=False)
        for j in list(picks) + ["bias"]:
            if j == "bias":
                up = self.loss_and_grad(X, y, w, b + h, sw)[0]
                dn = self.loss_and_grad(X, y, w, b - h, sw)[0]
                analytic = gb
            else:
                wp, wm = w.copy(), w.copy()
                wp[j] += h
                wm[j] -= h
                up = self.loss_and_grad(X, y, wp, b, sw)[0]
                dn = self.loss_and_grad(X, y, wm, b, sw)[0]
                analytic = gw[j]
            numeric = (up - dn) / (2 * h)
            rel = abs(analytic - numeric) / (max(abs(analytic), abs(numeric)) + 1e-12)
            worst = max(worst, rel)
        return worst
