"""M1-L08: watch overfitting happen as model capacity increases.

Fits polynomials of increasing degree to noisy data and reports training and
validation error for each, with an ASCII plot of both curves.

    python3 labs/m1/l08_overfitting.py

Standard library only - least squares is solved here by hand so that nothing
is hidden behind a library call.
"""

from __future__ import annotations

import math
import random

SEED = 3
N_TRAIN = 12
N_VAL = 40
NOISE = 1.2
RIDGE = 1e-8       # tiny value keeps high-degree fits numerically solvable
MAX_DEGREE = 11


def true_function(x: float) -> float:
    """The real underlying pattern: a gentle curve. This is the SIGNAL."""
    return 2.0 + 1.5 * x - 0.15 * x * x


def make_data(n: int, rng: random.Random) -> tuple[list[float], list[float]]:
    """Sample the true function and add NOISE - variation with no signal."""
    xs = [rng.uniform(0.0, 8.0) for _ in range(n)]
    ys = [true_function(x) + rng.gauss(0.0, NOISE) for x in xs]
    return xs, ys


def design_matrix(xs: list[float], degree: int) -> list[list[float]]:
    """Column p holds x**p. Degree d gives d+1 columns (capacity d+1)."""
    return [[x ** p for p in range(degree + 1)] for x in xs]


def solve(a: list[list[float]], b: list[float]) -> list[float]:
    """Gaussian elimination with partial pivoting. Solves a @ w = b."""
    n = len(b)
    m = [row[:] + [b[i]] for i, row in enumerate(a)]

    for col in range(n):
        # Pivot: pick the row with the largest absolute value in this column.
        pivot = max(range(col, n), key=lambda r: abs(m[r][col]))
        m[col], m[pivot] = m[pivot], m[col]
        if abs(m[col][col]) < 1e-14:
            continue
        for row in range(col + 1, n):
            factor = m[row][col] / m[col][col]
            for k in range(col, n + 1):
                m[row][k] -= factor * m[col][k]

    w = [0.0] * n
    for row in range(n - 1, -1, -1):
        if abs(m[row][row]) < 1e-14:
            continue
        total = m[row][n] - sum(m[row][k] * w[k] for k in range(row + 1, n))
        w[row] = total / m[row][row]
    return w


def fit(xs: list[float], ys: list[float], degree: int, ridge: float) -> list[float]:
    """Least squares via the normal equations (X^T X + ridge*I) w = X^T y.

    `ridge` is L2 regularization: it penalises large weights, pulling the fit
    toward simpler functions. Set it to 0 and high degrees blow up.
    """
    X = design_matrix(xs, degree)
    cols = degree + 1

    ata = [[sum(X[r][i] * X[r][j] for r in range(len(X))) for j in range(cols)]
           for i in range(cols)]
    for i in range(cols):
        ata[i][i] += ridge

    atb = [sum(X[r][i] * ys[r] for r in range(len(X))) for i in range(cols)]
    return solve(ata, atb)


def predict(w: list[float], x: float) -> float:
    return sum(coef * (x ** p) for p, coef in enumerate(w))


def mse(w: list[float], xs: list[float], ys: list[float]) -> float:
    return sum((predict(w, x) - y) ** 2 for x, y in zip(xs, ys)) / len(xs)


def ascii_plot(degrees: list[int], train: list[float], val: list[float]) -> None:
    """Plot both error curves on a LOG scale.

    The errors here span from 0.05 to over 15000. On a linear axis the
    training curve would be invisible. A log axis is the honest way to show
    quantities spanning several orders of magnitude.
    """
    height = 18
    floor = 1e-2
    lo = math.log10(max(min(min(train), min(val)), floor))
    hi = math.log10(max(max(train), max(val)))
    span = hi - lo if hi > lo else 1.0

    def row_of(value: float) -> int:
        """Which row (0 = bottom) this value belongs on."""
        v = math.log10(max(value, floor))
        return min(height - 1, max(0, int((v - lo) / span * (height - 1))))

    train_rows = [row_of(v) for v in train]
    val_rows = [row_of(v) for v in val]

    print()
    print("  error (log scale)")
    for level in range(height - 1, -1, -1):
        tick = 10 ** (lo + span * level / (height - 1))
        line = f"  {tick:>10.2f} |"
        for t_row, v_row in zip(train_rows, val_rows):
            if t_row == level and v_row == level:
                line += " B"
            elif v_row == level:
                line += " V"
            elif t_row == level:
                line += " T"
            else:
                line += "  "
        print(line)
    print("             +" + "--" * len(degrees))
    print("              " + "".join(f"{d:>2}" for d in degrees))
    print("              model capacity (polynomial degree)")
    print("              T = training error   V = validation error   B = both")


def main() -> None:
    rng = random.Random(SEED)
    train_x, train_y = make_data(N_TRAIN, rng)
    val_x, val_y = make_data(N_VAL, rng)

    print("=" * 70)
    print("OVERFITTING: training error vs validation error as capacity grows")
    print("=" * 70)
    print(f"True pattern: y = 2.0 + 1.5x - 0.15x^2   (a degree-2 curve)")
    print(f"Training points: {N_TRAIN}   Validation points: {N_VAL}")
    print(f"Noise std dev: {NOISE}   Ridge: {RIDGE}")
    print()
    print("A degree-d polynomial has d+1 parameters. With 12 training points,")
    print("degree 11 has exactly enough capacity to pass through every one.")
    print()

    print(f"{'degree':>7}{'params':>8}{'train err':>12}{'val err':>11}{'gap':>10}  verdict")
    print("-" * 70)

    degrees = list(range(0, MAX_DEGREE + 1))
    train_errors: list[float] = []
    val_errors: list[float] = []

    for degree in degrees:
        w = fit(train_x, train_y, degree, RIDGE)
        tr = mse(w, train_x, train_y)
        va = mse(w, val_x, val_y)
        train_errors.append(tr)
        val_errors.append(va)

        gap = va - tr
        if degree == 0:
            verdict = "underfit (predicts the mean)"
        elif gap > 5 * max(tr, 0.01):
            verdict = "OVERFIT"
        elif tr > 2.5:
            verdict = "underfit"
        else:
            verdict = "good"
        print(f"{degree:>7}{degree + 1:>8}{tr:>12.3f}{va:>11.3f}{gap:>10.3f}  {verdict}")

    best = min(range(len(degrees)), key=lambda i: val_errors[i])
    print("-" * 70)
    print(f"Lowest validation error at degree {degrees[best]} "
          f"(val={val_errors[best]:.3f}, train={train_errors[best]:.3f}, "
          f"gap={val_errors[best] - train_errors[best]:.3f})")
    print(f"Lowest TRAINING error at degree {degrees[-1]} "
          f"(train={train_errors[-1]:.3f}, val={val_errors[-1]:.3f})")
    print()

    ascii_plot(degrees, train_errors, val_errors)

    print()
    print("-" * 70)
    print("WHAT TO SEE HERE")
    print("-" * 70)
    print("1. Training error (T) falls essentially monotonically. It NEVER")
    print("   tells you to stop. This is why training error is not evidence.")
    print()
    print("2. Validation error (V) is U-shaped: it drops while the model")
    print("   learns real signal, then climbs as it starts fitting noise.")
    print()
    print("3. The best model is at the BOTTOM OF THE V CURVE, not the T curve.")
    print("   Choosing by training error picks the worst model available.")
    print()
    print("4. Look at degrees 1-7: validation error barely moves (about 2.0-2.6)")
    print("   while training error falls 10x. That flat region is the model")
    print("   buying nothing real. Then from degree 8 it does not just stop")
    print("   helping, it detonates - 2.1 -> 46 -> 1448 -> 15715.")
    print()
    print("5. HONEST NOTE: the true function is degree 2, but the validation")
    print("   minimum lands at degree 5. With only 12 noisy training points,")
    print("   the validation curve is too flat in that region to identify the")
    print("   true complexity. Do not expect model selection to recover the")
    print("   'real' answer - it recovers what your data can support. With")
    print("   N_TRAIN=60 (Exercise 2) the catastrophe disappears entirely:")
    print("   worst-case validation error falls from 15715 to about 1.7.")
    print("=" * 70)


if __name__ == "__main__":
    main()
