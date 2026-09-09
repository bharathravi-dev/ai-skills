"""M3-L08: linear regression from scratch, evaluated honestly.

Requires numpy:
    source .venv/bin/activate
    python labs/m3/l08_linear_regression.py
"""

from __future__ import annotations

import numpy as np

LINE = "-" * 74

X_RAW = np.array([[100.0, 0.0],
                  [500.0, 0.0],
                  [200.0, 1.0],
                  [800.0, 1.0],
                  [300.0, 0.0]])
Y = np.array([2.0, 4.0, 5.0, 8.0, 3.0])
FEATURES = ["body_length", "is_high_priority"]


def section(title: str) -> None:
    print()
    print(LINE)
    print(title)
    print(LINE)


def standardise(x: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    mean, std = x.mean(axis=0), x.std(axis=0)
    std = np.where(std == 0, 1.0, std)         # never divide by zero
    return (x - mean) / std, mean, std


def fit_descent(x: np.ndarray, y: np.ndarray, *, lr: float = 0.1,
                steps: int = 5000) -> tuple[np.ndarray, float, list[float]]:
    n, d = x.shape
    w, b = np.zeros(d), 0.0
    history = []
    for _ in range(steps):
        pred = x @ w + b
        error = pred - y
        history.append(float((error ** 2).mean()))
        w -= lr * (2 / n) * (x.T @ error)
        b -= lr * (2 / n) * error.sum()
    return w, b, history


def fit_closed_form(x: np.ndarray, y: np.ndarray) -> tuple[np.ndarray, float]:
    """Add a column of ones for the intercept, then solve exactly."""
    augmented = np.column_stack([x, np.ones(len(x))])
    solution = np.linalg.solve(augmented.T @ augmented, augmented.T @ y)
    return solution[:-1], float(solution[-1])


def metrics(y: np.ndarray, pred: np.ndarray) -> dict[str, float]:
    residual = y - pred
    ss_res = float((residual ** 2).sum())
    ss_tot = float(((y - y.mean()) ** 2).sum())
    return {
        "sse": ss_res,
        "mae": float(np.abs(residual).mean()),
        "rmse": float(np.sqrt((residual ** 2).mean())),
        "r2": 1 - ss_res / ss_tot if ss_tot else float("nan"),
    }


def baseline() -> None:
    section("1. THE BASELINE - what any model must beat")
    mean = Y.mean()
    print(f"  hours = {Y.tolist()}")
    print(f"  mean  = {Y.sum():.0f} / {len(Y)} = {mean}")
    print()
    print(f"  {'actual':>8}{'baseline':>12}{'residual':>12}{'squared':>12}")
    for actual in Y:
        r = actual - mean
        print(f"  {actual:>8.1f}{mean:>12.1f}{r:>12.2f}{r ** 2:>12.4f}")
    ss_tot = float(((Y - mean) ** 2).sum())
    print(f"  {'':>8}{'':>12}{'SS_tot':>12}{ss_tot:>12.2f}")
    print()
    print(f"  Baseline SSE = {ss_tot:.2f}. Any model must beat this to be")
    print("  worth anything. It is also the DENOMINATOR of R2, which is why")
    print("  R2 = 0 means exactly 'no better than the mean'.")
    base_metrics = metrics(Y, np.full_like(Y, mean))
    print(f"  Baseline R2  = {base_metrics['r2']:.6f}   (exactly zero, by construction)")


def scaling_matters() -> None:
    section("2. WHY YOU MUST STANDARDISE")
    print(f"  {'feature':<20}{'min':>8}{'max':>8}{'mean':>10}{'std':>10}")
    for i, name in enumerate(FEATURES):
        col = X_RAW[:, i]
        print(f"  {name:<20}{col.min():>8.0f}{col.max():>8.0f}"
              f"{col.mean():>10.1f}{col.std():>10.1f}")
    print()
    print(f"  Scale ratio: {X_RAW[:, 0].std() / max(X_RAW[:, 1].std(), 1e-9):.0f}x")
    print()

    x_std, mean, std = standardise(X_RAW)
    print("  body_length standardised by hand:")
    for raw, scaled in zip(X_RAW[:, 0], x_std[:, 0]):
        print(f"    ({raw:.0f} - {mean[0]:.0f}) / {std[0]:.1f} = {scaled:+.3f}")
    print(f"  standardised mean = {x_std[:, 0].mean():.10f}, "
          f"std = {x_std[:, 0].std():.4f}")
    print()

    print("  Fitting on RAW features at several learning rates:")
    for lr in (1e-2, 1e-5, 1e-7):
        w, b, hist = fit_descent(X_RAW, Y, lr=lr, steps=2000)
        final = hist[-1]
        state = "DIVERGED" if not np.isfinite(final) or final > 1e6 else f"{final:.4f}"
        print(f"    alpha={lr:<8.0e} final MSE = {state}")
    w, b, hist = fit_descent(x_std, Y, lr=0.1, steps=2000)
    print(f"  Fitting on STANDARDISED features at alpha=1e-01: "
          f"final MSE = {hist[-1]:.6f}")
    print()
    print("  On raw features no learning rate works well. On standardised")
    print("  features an ordinary one converges immediately.")


def fit_and_check() -> None:
    section("3. GRADIENT DESCENT vs THE CLOSED FORM")
    x_std, mean, std = standardise(X_RAW)

    w_gd, b_gd, hist = fit_descent(x_std, Y, lr=0.1, steps=20_000)
    w_cf, b_cf = fit_closed_form(x_std, Y)

    print(f"  {'':<22}{'w[body_len]':>14}{'w[priority]':>14}{'intercept':>12}")
    print(f"  {'gradient descent':<22}{w_gd[0]:>14.6f}{w_gd[1]:>14.6f}{b_gd:>12.6f}")
    print(f"  {'closed form (exact)':<22}{w_cf[0]:>14.6f}{w_cf[1]:>14.6f}{b_cf:>12.6f}")
    print(f"  {'difference':<22}{abs(w_gd[0] - w_cf[0]):>14.2e}"
          f"{abs(w_gd[1] - w_cf[1]):>14.2e}{abs(b_gd - b_cf):>12.2e}")
    print()
    print("  Descent converged to the exact solution. Always check a from-")
    print("  scratch implementation against a known-correct one where you can.")

    pred = x_std @ w_cf + b_cf
    m = metrics(Y, pred)
    print()
    print(f"  {'metric':<12}{'value':>12}   reading")
    print(f"  {'SSE':<12}{m['sse']:>12.4f}   down from the baseline's 21.20")
    print(f"  {'R2':<12}{m['r2']:>12.4f}   explains {m['r2']:.1%} of the variance")
    print(f"  {'RMSE':<12}{m['rmse']:>12.4f}   typically wrong by "
          f"{m['rmse'] * 60:.0f} minutes")
    print(f"  {'MAE':<12}{m['mae']:>12.4f}   hours")
    print()
    print("  A PERFECT fit. And that is precisely why it is worthless as")
    print("  evidence: these five points were constructed to lie exactly on")
    print("  a plane, and 3 parameters can always fit them. R2 = 1.000 here")
    print("  tells you about the data, not about the model (M1-L08).")
    print("  Section 5 fits 200 noisy samples with a held-out test set.")


def coefficients() -> None:
    section("4. INTERPRETING COEFFICIENTS - raw vs standardised")
    w_raw, b_raw = fit_closed_form(X_RAW, Y)
    x_std, mean, std = standardise(X_RAW)
    w_std, b_std = fit_closed_form(x_std, Y)

    print(f"  {'feature':<20}{'raw coefficient':>18}{'standardised':>16}")
    for i, name in enumerate(FEATURES):
        print(f"  {name:<20}{w_raw[i]:>18.6f}{w_std[i]:>16.4f}")
    print(f"  {'intercept':<20}{b_raw:>18.6f}{b_std:>16.4f}")
    print()
    print(f"  The RAW coefficients cannot be compared: {w_raw[0]:.4f} per")
    print(f"  character versus {w_raw[1]:.2f} per 0/1 flag says nothing about")
    print("  relative importance - the features are on wildly different scales.")
    print()
    print("  The STANDARDISED coefficients CAN be compared - both now mean")
    print("  'hours per one standard deviation of this feature':")
    order = np.argsort(-np.abs(w_std))
    for rank, i in enumerate(order, 1):
        print(f"    {rank}. {FEATURES[i]:<20}{abs(w_std[i]):>8.3f}")
    print()
    print("  Both models make IDENTICAL predictions. Standardisation changes")
    print("  the coefficients' units, not the fit.")
    pred_raw = X_RAW @ w_raw + b_raw
    pred_std = x_std @ w_std + b_std
    print(f"  predictions identical? {np.allclose(pred_raw, pred_std)}")


def realistic_fit() -> None:
    section("5. A REALISTIC FIT - 200 noisy samples")
    rng = np.random.default_rng(42)
    n = 200
    body = rng.uniform(50, 2000, n)
    priority = (rng.random(n) < 0.3).astype(float)
    true_w = np.array([0.003, 2.0])
    noise = rng.normal(0, 0.8, n)
    y = body * true_w[0] + priority * true_w[1] + 1.5 + noise
    x = np.column_stack([body, priority])

    # Honest evaluation: split before fitting (M1-L06).
    idx = rng.permutation(n)
    train_idx, test_idx = idx[:150], idx[150:]
    x_train, y_train = x[train_idx], y[train_idx]
    x_test, y_test = x[test_idx], y[test_idx]

    mean, std = x_train.mean(axis=0), x_train.std(axis=0)
    w, b = fit_closed_form((x_train - mean) / std, y_train)

    train_pred = ((x_train - mean) / std) @ w + b
    test_pred = ((x_test - mean) / std) @ w + b
    m_train, m_test = metrics(y_train, train_pred), metrics(y_test, test_pred)

    print(f"  {n} samples, true relationship: hours = 0.003*body + 2.0*priority "
          f"+ 1.5 + noise")
    print(f"  split: {len(train_idx)} train / {len(test_idx)} test")
    print()
    print(f"  {'':<12}{'R2':>10}{'RMSE':>10}{'MAE':>10}")
    print(f"  {'train':<12}{m_train['r2']:>10.4f}{m_train['rmse']:>10.4f}"
          f"{m_train['mae']:>10.4f}")
    print(f"  {'test':<12}{m_test['r2']:>10.4f}{m_test['rmse']:>10.4f}"
          f"{m_test['mae']:>10.4f}")
    print()
    print("  Train and test agree closely: a healthy fit, not overfitting")
    print("  (M1-L08). Compare with the 5-sample R2 of ~0.97 in section 3.")
    print()
    # Recover the original-scale coefficients to compare with the truth.
    recovered = w / std
    print(f"  {'coefficient':<20}{'true':>10}{'recovered':>12}")
    for i, name in enumerate(FEATURES):
        print(f"  {name:<20}{true_w[i]:>10.4f}{recovered[i]:>12.4f}")
    print(f"  RMSE {m_test['rmse']:.3f} vs the noise we injected (0.8) - the")
    print("  model has essentially recovered the truth and cannot do better")
    print("  than the noise floor.")


def collinearity() -> None:
    section("6. MULTICOLLINEARITY - unstable coefficients, fine predictions")
    rng = np.random.default_rng(7)
    n = 120
    f1 = rng.normal(0, 1, n)
    f2 = f1 * 1.001 + rng.normal(0, 0.001, n)      # nearly identical to f1
    f3 = rng.normal(0, 1, n)
    y = 3 * f1 + 2 * f3 + rng.normal(0, 0.1, n)
    x = np.column_stack([f1, f2, f3])

    print(f"  correlation between feature 1 and feature 2: "
          f"{np.corrcoef(f1, f2)[0, 1]:.6f}")
    print()
    print(f"  {'fit on':<26}{'w1':>12}{'w2':>12}{'w3':>10}{'test R2':>10}")
    for label, sample in (("full data", np.arange(n)),
                          ("bootstrap resample A", rng.integers(0, n, n)),
                          ("bootstrap resample B", rng.integers(0, n, n)),
                          ("bootstrap resample C", rng.integers(0, n, n))):
        w, b = fit_closed_form(x[sample], y[sample])
        r2 = metrics(y, x @ w + b)["r2"]
        print(f"  {label:<26}{w[0]:>12.2f}{w[1]:>12.2f}{w[2]:>10.2f}{r2:>10.4f}")
    print()
    print("  w1 and w2 swing wildly between resamples - often large and of")
    print("  OPPOSITE sign - while R2 stays high and stable throughout.")
    print()
    print("  The model's PREDICTIONS are reliable. Its individual")
    print("  COEFFICIENTS are meaningless. Anyone reading 'feature 1 has a")
    print("  coefficient of +47' as an insight would be badly misled.")
    print()
    print("  Ridge regression (adding lambda*I to X'X) stabilises this:")
    for lam in (0.0, 0.1, 1.0, 10.0):
        aug = np.column_stack([x, np.ones(n)])
        penalty = lam * np.eye(aug.shape[1])
        penalty[-1, -1] = 0.0                        # never penalise the intercept
        sol = np.linalg.solve(aug.T @ aug + penalty, aug.T @ y)
        r2 = metrics(y, x @ sol[:-1] + sol[-1])["r2"]
        print(f"    lambda={lam:<6} w1={sol[0]:>8.2f}  w2={sol[1]:>8.2f}  "
              f"w3={sol[2]:>6.2f}  R2={r2:.4f}")
    print("    As lambda grows the two collinear coefficients converge to a")
    print("    sensible shared value, at a small cost in training R2.")


def extrapolation() -> None:
    section("7. EXTRAPOLATION - confident and absurd")
    x_std, mean, std = standardise(X_RAW)
    w, b = fit_closed_form(x_std, Y)
    lo, hi = X_RAW[:, 0].min(), X_RAW[:, 0].max()

    print(f"  Training body_length range: {lo:.0f} to {hi:.0f} characters")
    print()
    print(f"  {'body_length':>14}{'standardised':>14}{'predicted hours':>18}   status")
    for length in (150, 400, 800, 5_000, 50_000):
        scaled = (np.array([length, 0.0]) - mean) / std
        pred = float(scaled @ w + b)
        status = "in range" if lo <= length <= hi else "EXTRAPOLATING"
        print(f"  {length:>14,}{scaled[0]:>14.2f}{pred:>18.1f}   {status}")
    far = (np.array([50_000.0, 0.0]) - mean) / std
    far_pred = float(far @ w + b)
    print()
    print(f"  A 50,000-character ticket gets a confident prediction of")
    print(f"  {far_pred:.0f} hours - over {far_pred / 40:.0f} working weeks. Nothing in the")
    print(f"  arithmetic knows that no training ticket exceeded {hi:.0f} characters.")
    print()
    print("  Record the training range and flag inputs outside it. This is")
    print("  the same 'know when you do not know' problem as M1-L10, in a")
    print("  model simple enough to see it clearly.")


def main() -> None:
    print("=" * 74)
    print("LINEAR REGRESSION FROM SCRATCH")
    print("=" * 74)
    baseline()
    scaling_matters()
    fit_and_check()
    coefficients()
    realistic_fit()
    collinearity()
    extrapolation()
    print()
    print("=" * 74)


if __name__ == "__main__":
    main()
