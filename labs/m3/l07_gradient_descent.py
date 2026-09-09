"""M3-L07: losses, gradient descent, training curves and feature scaling.

Requires numpy:
    source .venv/bin/activate
    python labs/m3/l07_gradient_descent.py
"""

from __future__ import annotations

import time

import numpy as np

LINE = "-" * 74
X = np.array([1.0, 2.0, 3.0])
Y = np.array([3.0, 5.0, 7.0])          # y = 2x + 1 exactly


def section(title: str) -> None:
    print()
    print(LINE)
    print(title)
    print(LINE)


def mse(w: float, b: float, x=X, y=Y) -> float:
    return float(((w * x + b - y) ** 2).mean())


def mse_grads(w: float, b: float, x=X, y=Y) -> tuple[float, float]:
    error = w * x + b - y
    n = len(x)
    return float(2 / n * (error * x).sum()), float(2 / n * error.sum())


def by_hand() -> None:
    section("1. THE SECTION 6 CALCULATION, VERIFIED")
    w, b = 0.0, 0.0
    print(f"  data: {list(zip(X.astype(int), Y.astype(int)))}   (true: y = 2x + 1)")
    print(f"  start: w = {w}, b = {b}")
    print()
    print(f"  {'x':>4}{'y':>6}{'y_hat':>10}{'error':>10}{'error^2':>10}")
    pred = w * X + b
    for xi, yi, pi in zip(X, Y, pred):
        err = pi - yi
        print(f"  {xi:>4.0f}{yi:>6.0f}{pi:>10.4f}{err:>10.4f}{err ** 2:>10.4f}")
    print(f"  MSE = {((pred - Y) ** 2).sum():.3f} / 3 = {mse(w, b):.3f}")
    print()
    gw, gb = mse_grads(w, b)
    print(f"  dL/dw = (2/3)[(-3)(1) + (-5)(2) + (-7)(3)] = {gw:.4f}")
    print(f"  dL/db = (2/3)[(-3) + (-5) + (-7)]          = {gb:.4f}")
    print("  Both negative, so both parameters should INCREASE. Correct:")
    print("  they start at 0 and should reach w=2, b=1.")
    print()
    lr = 0.01
    w2, b2 = w - lr * gw, b - lr * gb
    print(f"  One step at alpha={lr}:")
    print(f"    w = 0 - {lr} x ({gw:.4f}) = {w2:.4f}")
    print(f"    b = 0 - {lr} x ({gb:.4f}) = {b2:.4f}")
    print(f"    new MSE = {mse(w2, b2):.3f}   (was {mse(w, b):.3f})   fell OK")
    print()
    print(f"  NOTE the asymmetry: |dL/dw| = {abs(gw):.2f} but |dL/db| = {abs(gb):.2f}.")
    print("  w is multiplied by x (values 1-3); b is not. The parameter")
    print("  attached to the larger input gets the larger gradient. That is")
    print("  the feature-scaling problem, visible in two parameters.")


def ascii_curve(losses: list[float], width: int = 58, height: int = 12) -> None:
    lo, hi = min(losses), max(losses)
    span = hi - lo if hi > lo else 1.0
    step = max(1, len(losses) // width)
    sampled = losses[::step][:width]
    print(f"  loss")
    for row in range(height, 0, -1):
        threshold = lo + span * row / height
        line = f"  {threshold:>8.3f} |"
        for value in sampled:
            line += "*" if value >= threshold else " "
        print(line)
    print(f"  {'':>8} +" + "-" * len(sampled))
    print(f"  {'':>10}0{' ' * (len(sampled) - 6)}step {len(losses)}")


def converge() -> None:
    section("2. DESCENT TO CONVERGENCE")
    w, b, lr = 0.0, 0.0, 0.05
    losses = []
    for _ in range(400):
        losses.append(mse(w, b))
        gw, gb = mse_grads(w, b)
        w -= lr * gw
        b -= lr * gb
    print(f"  alpha = {lr}, 400 steps")
    print(f"  final: w = {w:.6f}, b = {b:.6f}, loss = {mse(w, b):.3e}")
    print(f"  target: w = 2, b = 1, loss = 0")
    print()
    ascii_curve(losses)
    print()
    print("  Smooth fall then flat: the healthy shape. It reaches zero loss")
    print("  because these three points lie EXACTLY on a line. Real data")
    print("  never does, and the loss converges to a non-zero floor that")
    print("  represents the noise you cannot fit.")


def mse_vs_mae() -> None:
    section("3. MSE OPTIMISES THE MEAN, MAE THE MEDIAN")
    values = np.array([10.0, 12.0, 11.0, 500.0])
    print(f"  Predicting a single constant for {values.tolist()}")
    print()
    candidates = np.linspace(5, 200, 40_000)
    mse_losses = ((candidates[:, None] - values) ** 2).mean(axis=1)
    mae_losses = np.abs(candidates[:, None] - values).mean(axis=1)
    best_mse = candidates[int(np.argmin(mse_losses))]
    best_mae = candidates[int(np.argmin(mae_losses))]

    print(f"  value minimising MSE : {best_mse:>8.2f}   (the mean is "
          f"{values.mean():.2f})")
    print(f"  value minimising MAE : {best_mae:>8.2f}   (the median is "
          f"{np.median(values):.2f})")
    print()
    print("  One outlier moved the MSE-optimal prediction to 133 - a value")
    print("  no observation is anywhere near. MAE stayed at the median.")
    print()
    print("  This is not a rounding difference. On right-skewed targets")
    print("  (latency, price, document length - M3-L03) MSE and MAE give")
    print("  genuinely different models.")


def sigmoid(z: np.ndarray) -> np.ndarray:
    return 1 / (1 + np.exp(-z))


def why_not_mse_for_classification() -> None:
    section("4. WHY MSE FAILS FOR CLASSIFICATION")
    print("  Binary classifier, sigmoid output, TRUE LABEL = 1.")
    print("  Comparing the gradient with respect to the pre-sigmoid value z.")
    print()
    print(f"  {'prediction':>12}{'error':>10}{'cross-entropy':>16}{'MSE':>14}"
          f"{'ratio':>10}")
    for p in (0.99, 0.90, 0.50, 0.10, 0.01):
        z = np.log(p / (1 - p))
        s = sigmoid(np.array([z]))[0]
        error = s - 1.0
        ce_grad = error                      # d/dz of cross-entropy = sigma(z) - y
        mse_grad = error * s * (1 - s)       # extra sigma'(z) factor
        print(f"  {p:>12.2f}{error:>10.2f}{ce_grad:>16.4f}{mse_grad:>14.6f}"
              f"{abs(ce_grad / mse_grad):>10.0f}x")
    print()
    print("  Compare the two columns as the prediction gets WORSE:")
    print("    cross-entropy  0.0100 -> 0.1000 -> 0.5000 -> 0.9000 -> 0.9900")
    print("      rises steadily. The worse the prediction, the bigger the push.")
    print("    MSE            0.0001 -> 0.0090 -> 0.1250 -> 0.0810 -> 0.0098")
    print("      rises then FALLS AWAY again. It peaks at p=0.5 and collapses")
    print("      at BOTH extremes.")
    print()
    print("  So under MSE, a prediction of 0.01 when the truth is 1 (as wrong")
    print("  as possible) receives a gradient of 0.0098 - essentially the same")
    print("  as a nearly-correct 0.90 (0.0090), and 13x SMALLER than an")
    print("  unsure 0.50 (0.125).")
    print()
    print("  MSE cannot tell 'almost right' from 'completely wrong'.")
    print("  Cross-entropy separates them by a factor of 10.")
    print()
    print("  The culprit is the sigma'(z) factor, which goes to zero as the")
    print("  sigmoid saturates at either end.")

    print()
    print("  DOES IT MATTER IN PRACTICE? It depends on where you start.")
    rng = np.random.default_rng(42)
    n = 600
    x = rng.normal(size=(n, 2))
    y = (x[:, 0] + x[:, 1] > 0).astype(float)

    def train(loss_name: str, w0: np.ndarray, b0: float,
              steps: int = 400, lr: float = 0.5) -> tuple[float, float]:
        w, b = w0.copy(), b0
        for _ in range(steps):
            p = sigmoid(x @ w + b)
            if loss_name == "cross-entropy":
                dz = (p - y) / n
            else:
                dz = (p - y) * p * (1 - p) / n
            w -= lr * (x.T @ dz)
            b -= lr * dz.sum()
        acc = float((((x @ w + b) > 0) == y).mean())
        start_acc = float((((x @ w0 + b0) > 0) == y).mean())
        return start_acc, acc

    print()
    print(f"  {'starting point':<34}{'loss':<16}{'start acc':>11}{'final acc':>11}")
    starts = [
        ("zeros (neutral)", np.zeros(2), 0.0),
        ("CONFIDENTLY WRONG (-8, -8)", np.array([-8.0, -8.0]), 0.0),
    ]
    for label, w0, b0 in starts:
        for loss_name in ("cross-entropy", "MSE"):
            start_acc, acc = train(loss_name, w0, b0)
            print(f"  {label:<34}{loss_name:<16}{start_acc:>11.3f}{acc:>11.3f}")

    print()
    print("  From a NEUTRAL start both losses work; this problem is easy and")
    print("  MSE may even edge ahead. The difference only bites once the")
    print("  model is deep in saturation.")
    print()
    print("  From a CONFIDENTLY WRONG start, cross-entropy recovers and MSE")
    print("  does not - it is stuck exactly where its gradient has vanished.")
    print("  In a deep network some units are always saturated, which is why")
    print("  cross-entropy is the standard choice rather than merely a")
    print("  preference.")


def curve_pathologies() -> None:
    section("5. THE FIVE TRAINING-CURVE PATHOLOGIES")
    settings = [
        ("healthy", 0.05, 60),
        ("alpha too small (flat)", 0.00005, 60),
        ("alpha too high (oscillating)", 0.22, 60),
        ("diverging", 0.30, 20),
    ]
    for label, lr, steps in settings:
        w, b = 0.0, 0.0
        losses = []
        for _ in range(steps):
            losses.append(mse(w, b))
            gw, gb = mse_grads(w, b)
            w -= lr * gw
            b -= lr * gb
            if not np.isfinite(mse(w, b)) or mse(w, b) > 1e12:
                losses.append(float("inf"))
                break
        first, last = losses[0], losses[-1]
        trend = ("diverged" if not np.isfinite(last) or last > first
                 else "converging" if last < first * 0.1
                 else "barely moved")
        shown = [f"{v:.1f}" if np.isfinite(v) else "inf" for v in losses[:6]]
        print(f"  {label:<30} alpha={lr:<9} {trend}")
        print(f"  {'':<30} first losses: {', '.join(shown)}")
    print()
    print("  A curve that is flat and a curve that is diverging need OPPOSITE")
    print("  fixes. Reading which one you have is the whole diagnostic skill.")


def feature_scaling() -> None:
    section("6. FEATURE SCALING - the ravine, measured")
    rng = np.random.default_rng(42)
    n = 200
    # Two features on wildly different scales.
    f1 = rng.normal(0, 1, n)
    f2 = rng.normal(0, 1000, n)
    y = 3 * f1 + 0.005 * f2 + rng.normal(0, 0.1, n)

    def train(features: np.ndarray, lr: float, steps: int = 3000) -> tuple[int, float]:
        w = np.zeros(features.shape[1])
        for step in range(steps):
            pred = features @ w
            loss = float(((pred - y) ** 2).mean())
            if not np.isfinite(loss) or loss > 1e15:
                return step, float("inf")
            if loss < 0.02:
                return step, loss
            w -= lr * (2 / n) * (features.T @ (pred - y))
        return steps, float(((features @ w - y) ** 2).mean())

    raw = np.column_stack([f1, f2])
    scaled = (raw - raw.mean(axis=0)) / raw.std(axis=0)

    print(f"  Feature 1 std: {f1.std():.2f}   Feature 2 std: {f2.std():.2f}")
    print(f"  Ratio: {f2.std() / f1.std():.0f}x")
    print()
    print(f"  {'features':<14}{'alpha':>10}{'steps to converge':>20}{'final loss':>14}")
    for lr in (1e-2, 1e-4, 1e-6):
        steps, loss = train(raw, lr)
        result = "DIVERGED" if not np.isfinite(loss) else (
            f"{steps}" if steps < 3000 else "did not converge")
        print(f"  {'raw':<14}{lr:>10.0e}{result:>20}"
              f"{loss if np.isfinite(loss) else float('inf'):>14.4f}")
    for lr in (1e-2,):
        steps, loss = train(scaled, lr)
        result = f"{steps}" if steps < 3000 else "did not converge"
        print(f"  {'standardised':<14}{lr:>10.0e}{result:>20}{loss:>14.4f}")
    print()
    print("  With raw features there is NO learning rate that works well:")
    print("  large enough for feature 1 diverges on feature 2, and small")
    print("  enough for feature 2 crawls on feature 1. That is the ravine.")
    print()
    print("  Standardising makes both gradients comparable, the surface")
    print("  round, and an ordinary learning rate converge quickly.")
    print("  This is usually the single biggest practical fix in training.")


def main() -> None:
    print("=" * 74)
    print("LOSS FUNCTIONS AND GRADIENT DESCENT")
    print("=" * 74)
    by_hand()
    converge()
    mse_vs_mae()
    why_not_mse_for_classification()
    curve_pathologies()
    feature_scaling()
    print()
    print("=" * 74)


if __name__ == "__main__":
    main()
