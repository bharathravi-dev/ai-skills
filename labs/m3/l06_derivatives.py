"""M3-L06: derivatives numerically and analytically, the chain rule, descent.

Requires numpy:
    source .venv/bin/activate
    python labs/m3/l06_derivatives.py
"""

from __future__ import annotations

import math

import numpy as np

LINE = "-" * 74


def section(title: str) -> None:
    print()
    print(LINE)
    print(title)
    print(LINE)


def forward_diff(f, x: float, h: float = 1e-5) -> float:
    return (f(x + h) - f(x)) / h


def central_diff(f, x: float, h: float = 1e-5) -> float:
    """More accurate than the forward form for the same h."""
    return (f(x + h) - f(x - h)) / (2 * h)


def nudge_intuition() -> None:
    section("1. A DERIVATIVE IS JUST A NUDGE RATIO")
    f = lambda x: x ** 2
    x = 3.0
    print(f"  f(x) = x^2, at x = {x}")
    print()
    print(f"  {'nudge h':>12}{'f(x)':>12}{'f(x+h)':>14}{'change':>12}{'rate':>10}")
    for h in (1.0, 0.1, 0.01, 0.001, 0.0001):
        change = f(x + h) - f(x)
        print(f"  {h:>12}{f(x):>12.4f}{f(x + h):>14.6f}{change:>12.6f}"
              f"{change / h:>10.4f}")
    print()
    print("  As the nudge shrinks, the rate converges on 6. The analytic")
    print(f"  derivative of x^2 is 2x, and 2 x 3 = 6. That is all a")
    print("  derivative is: the limit of that last column.")


def rules_check() -> None:
    section("2. THE RULES, CHECKED NUMERICALLY")
    cases = [
        ("f(x) = 7        (constant)", lambda x: 7.0, lambda x: 0.0, 3.0),
        ("f(x) = x", lambda x: x, lambda x: 1.0, 3.0),
        ("f(x) = x^2", lambda x: x ** 2, lambda x: 2 * x, 3.0),
        ("f(x) = x^3", lambda x: x ** 3, lambda x: 3 * x ** 2, 2.0),
        ("f(x) = 5x + 3", lambda x: 5 * x + 3, lambda x: 5.0, 3.0),
        ("f(x) = e^x", math.exp, math.exp, 1.0),
        ("f(x) = ln(x)", math.log, lambda x: 1 / x, 4.0),
    ]
    print(f"  {'function':<28}{'x':>5}{'analytic':>12}{'numerical':>13}{'error':>12}")
    for label, f, df, x in cases:
        analytic = df(x)
        numerical = central_diff(f, x)
        print(f"  {label:<28}{x:>5.0f}{analytic:>12.6f}{numerical:>13.6f}"
              f"{abs(analytic - numerical):>12.2e}")
    print()
    print("  Every rule verified against a numerical estimate. You can always")
    print("  check a derivative this way - it is how you catch sign errors.")


def h_sweep() -> None:
    section("3. HOW SMALL SHOULD h BE? (smaller is NOT better)")

    # NOTE: we deliberately do NOT use x^2 here. The central-difference error
    # term is proportional to the THIRD derivative, which is zero for any
    # quadratic - so the formula is exact for x^2 at every h, and the sweep
    # would show nothing. e^x has non-zero derivatives of every order.
    f, df = math.exp, math.exp
    x = 1.0
    true = df(x)
    print(f"  f(x) = e^x at x = {x}, true derivative = {true:.10f}")
    print()
    print("  (Using e^x rather than x^2: the central difference is EXACT for")
    print("   quadratics, because its error depends on the third derivative.")
    print("   A nice fact, and useless for showing the trade-off.)")
    print()
    print(f"  {'h':>10}{'forward error':>17}{'central error':>17}")
    best_h, best_err = None, float("inf")
    for exponent in range(-1, -14, -1):
        h = 10.0 ** exponent
        fwd_err = abs(forward_diff(f, x, h) - true)
        cen_err = abs(central_diff(f, x, h) - true)
        if cen_err < best_err:
            best_err, best_h = cen_err, h
        marker = ""
        print(f"  {h:>10.0e}{fwd_err:>17.3e}{cen_err:>17.3e}{marker}")
    print()
    print(f"  Best central-difference accuracy at h = {best_h:.0e} "
          f"(error {best_err:.2e})")
    print()
    print("  TWO competing effects pull in opposite directions:")
    print("    large h -> the nudge is too coarse; you measure a chord across")
    print("               a curve, not the tangent. Error SHRINKS as h shrinks.")
    print("    tiny h  -> f(x+h) and f(x-h) agree in their leading digits, so")
    print("               subtracting them destroys precision. Error GROWS as")
    print("               h shrinks further.")
    print()
    print("  The minimum sits between them. Note the central difference beats")
    print("  the forward difference by several orders of magnitude in the")
    print("  useful range - which is why gradient checking uses it.")


def chain_rule() -> None:
    section("4. THE CHAIN RULE - rates multiply")
    x = 2.0
    print(f"  y = (3x + 1)^2  at x = {x}")
    print()
    u = 3 * x + 1
    y = u ** 2
    print(f"  Step 1: u = 3x + 1 = {u}")
    print(f"  Step 2: y = u^2    = {y}")
    print()
    du_dx = 3.0
    dy_du = 2 * u
    dy_dx = dy_du * du_dx
    print(f"  du/dx = 3           = {du_dx}")
    print(f"  dy/du = 2u = 2 x {u} = {dy_du}")
    print(f"  dy/dx = {dy_du} x {du_dx}    = {dy_dx}   <- rates multiply")
    print()
    numeric = central_diff(lambda v: (3 * v + 1) ** 2, x)
    print(f"  numerical check: {numeric:.6f}   error {abs(numeric - dy_dx):.2e}")
    print()
    print("  A neural network is this same chain, thousands of links long.")
    print("  Backpropagation walks it backwards from the loss, multiplying")
    print("  local derivatives - which is why every parameter's gradient")
    print("  costs about one extra forward pass, not one pass each.")


def gradient_demo() -> None:
    section("5. GRADIENTS - all the partial derivatives at once")
    f = lambda x, y: x ** 2 + 3 * y
    point = (2.0, 5.0)

    df_dx = 2 * point[0]
    df_dy = 3.0
    grad = np.array([df_dx, df_dy])

    num_dx = central_diff(lambda v: f(v, point[1]), point[0])
    num_dy = central_diff(lambda v: f(point[0], v), point[1])

    print(f"  f(x, y) = x^2 + 3y   at (x, y) = {point}")
    print(f"    df/dx = 2x = {df_dx}     (numerical {num_dx:.6f})")
    print(f"    df/dy = 3    = {df_dy}     (numerical {num_dy:.6f})")
    print(f"    gradient = {grad}, magnitude {np.linalg.norm(grad):.4f}")
    print()
    print("  The gradient points UPHILL. Proof - move a small step each way:")
    step = 0.01
    base = f(*point)
    uphill = f(point[0] + step * grad[0], point[1] + step * grad[1])
    downhill = f(point[0] - step * grad[0], point[1] - step * grad[1])
    print(f"    f at the point              = {base:.6f}")
    print(f"    f after step ALONG gradient = {uphill:.6f}   (higher)")
    print(f"    f after step AGAINST it     = {downhill:.6f}   (lower)")
    print()
    print("  To minimise, always step AGAINST the gradient. That is the")
    print("  minus sign in  w <- w - alpha * grad.")


def descent() -> None:
    section("6. THE SECTION 6 DESCENT, STEP BY STEP")
    x_data, y_true = 2.0, 10.0

    def loss(w: float) -> float:
        return (w * x_data - y_true) ** 2

    def grad(w: float) -> float:
        return 2 * (w * x_data - y_true) * x_data

    w = 1.0
    print(f"  model: y_hat = w * x   with x = {x_data}, true y = {y_true}")
    print(f"  ideal w = {y_true / x_data}")
    print()
    print(f"  Hand-derived gradient at w=1: {grad(1.0)}")
    numeric = central_diff(loss, 1.0, h=1e-4)
    print(f"  numerical check             : {numeric:.4f}   "
          f"error {abs(numeric - grad(1.0)):.2e}")
    print()
    lr = 0.01
    print(f"  Descending with learning rate {lr}:")
    print(f"  {'step':>6}{'w':>12}{'loss':>14}{'gradient':>12}")
    for step in range(9):
        print(f"  {step:>6}{w:>12.6f}{loss(w):>14.6f}{grad(w):>12.4f}")
        w -= lr * grad(w)
    print(f"  {'...':>6}")
    for _ in range(300):
        w -= lr * grad(w)
    print(f"  {'final':>6}{w:>12.6f}{loss(w):>14.9f}")
    print()
    print("  Converged to w = 5, which is exactly y/x. The loss went to zero.")


def learning_rates() -> None:
    section("7. THE LEARNING RATE DECIDES HOW FAR TO TRUST THE GRADIENT")
    x_data, y_true = 2.0, 10.0
    loss = lambda w: (w * x_data - y_true) ** 2
    grad = lambda w: 2 * (w * x_data - y_true) * x_data

    print(f"  Starting at w = 1 (loss {loss(1.0):.1f}). ONE step at each rate:")
    print()
    print(f"  {'learning rate':>15}{'new w':>12}{'new loss':>14}   outcome")
    for lr in (0.001, 0.01, 0.1, 0.125, 0.2, 0.5):
        w = 1.0 - lr * grad(1.0)
        new_loss = loss(w)
        # Order matters: check the extremes first, then slow, then overshoot.
        optimum = y_true / x_data
        if new_loss == 0:
            outcome = "EXACTLY optimal here"
        elif new_loss > loss(1.0):
            outcome = "DIVERGING - worse than we started"
        elif new_loss > 0.9 * loss(1.0):
            outcome = "correct direction, but very slow"
        elif w > optimum:
            outcome = "overshot past the minimum, still improving"
        else:
            outcome = "good progress"
        print(f"  {lr:>15}{w:>12.4f}{new_loss:>14.4f}   {outcome}")

    print()
    print("  Finding the divergence threshold empirically:")
    lo, hi = 0.1, 1.0
    for _ in range(40):
        mid = (lo + hi) / 2
        w = 1.0 - mid * grad(1.0)
        if loss(w) < loss(1.0):
            lo = mid
        else:
            hi = mid
    print(f"    diverges above a learning rate of about {hi:.4f}")
    print()
    print("  For this quadratic the threshold is 2/(2*x^2) = "
          f"{2 / (2 * x_data ** 2):.4f}. Above it, each step")
    print("  overshoots further than it corrects, and the loss grows without")
    print("  bound. The gradient gave the direction; the rate was wrong.")


def vanishing_exploding() -> None:
    section("8. VANISHING AND EXPLODING GRADIENTS")
    print("  A deep network multiplies one local derivative per layer.")
    print("  Same compounding arithmetic as M1-L11's p^n and M3-L05's underflow.")
    print()
    print(f"  {'per-layer derivative':>22}{'10 layers':>14}{'50 layers':>16}"
          f"{'100 layers':>16}")
    for d in (0.5, 0.9, 1.0, 1.1, 1.5):
        row = "".join(f"{d ** n:>16.3e}" if n > 10 else f"{d ** n:>14.3e}"
                      for n in (10, 50, 100))
        print(f"  {d:>22}{row}")
    print()
    print("  d = 0.5 over 100 layers -> 7.9e-31. The gradient reaching the")
    print("    first layer is effectively zero: it stops learning entirely.")
    print("    VANISHING GRADIENT.")
    print()
    print("  d = 1.5 over 100 layers -> 4.1e+17. The update is astronomically")
    print("    large, weights blow up, and the loss becomes nan.")
    print("    EXPLODING GRADIENT.")
    print()
    print("  Only d = 1.0 is stable at depth. ReLU activations, residual")
    print("  connections, normalisation layers and gradient clipping all")
    print("  exist to keep that product near 1 (M4-L10).")


def main() -> None:
    print("=" * 74)
    print("DERIVATIVES, GRADIENTS AND THE CHAIN RULE")
    print("=" * 74)
    nudge_intuition()
    rules_check()
    h_sweep()
    chain_rule()
    gradient_demo()
    descent()
    learning_rates()
    vanishing_exploding()
    print()
    print("=" * 74)


if __name__ == "__main__":
    main()
