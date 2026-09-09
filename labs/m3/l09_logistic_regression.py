"""M3-L09: sigmoid, softmax, logits and odds - and the LLM temperature knob.

Requires numpy:
    source .venv/bin/activate
    python labs/m3/l09_logistic_regression.py
"""

from __future__ import annotations

import warnings

import numpy as np

LINE = "-" * 74


def section(title: str) -> None:
    print()
    print(LINE)
    print(title)
    print(LINE)


def sigmoid(z):
    """Numerically stable: exp(-|z|) never overflows."""
    z = np.asarray(z, dtype=float)
    positive = z >= 0
    result = np.empty_like(z)
    result[positive] = 1 / (1 + np.exp(-z[positive]))
    exp_z = np.exp(z[~positive])
    result[~positive] = exp_z / (1 + exp_z)
    return result


def softmax(z, temperature: float = 1.0):
    z = np.asarray(z, dtype=float) / temperature
    z = z - z.max()                       # a no-op mathematically, essential numerically
    e = np.exp(z)
    return e / e.sum()


def sigmoid_shape() -> None:
    section("1. THE SIGMOID AND ITS DERIVATIVE")
    print(f"  {'z':>7}{'sigma(z)':>12}{'sigma_prime(z)':>17}   shape")
    for z in (-6, -4, -2, -1, 0, 1, 2, 4, 6):
        s = float(sigmoid(z))
        d = s * (1 - s)
        bar = "#" * int(s * 40)
        print(f"  {z:>7}{s:>12.4f}{d:>17.4f}   {bar}")
    print()
    peak = 0.25
    edge = float(sigmoid(6)) * (1 - float(sigmoid(6)))
    print(f"  sigma' peaks at z=0 with {peak}, and falls to {edge:.4f} at z=6")
    print(f"  a ratio of {peak / edge:.0f}x")
    print()
    print("  THAT COLLAPSE IS SATURATION. It is the sigma'(z) factor that")
    print("  made MSE fail for classification in M3-L07: at z=+-6 the")
    print("  gradient is a hundredth of its peak. Cross-entropy's gradient")
    print("  is simply (p - y), with no sigma' factor at all.")


def logits_odds() -> None:
    section("2. PROBABILITY, ODDS AND LOG-ODDS - the same thing three ways")
    print(f"  {'probability':>13}{'odds':>14}{'log-odds (logit)':>20}"
          f"{'sigmoid(logit)':>17}")
    for p in (0.01, 0.1, 0.25, 0.5, 0.75, 0.9, 0.99):
        odds = p / (1 - p)
        logit = np.log(odds)
        back = float(sigmoid(logit))
        print(f"  {p:>13.2f}{odds:>14.3f}{logit:>20.4f}{back:>17.4f}")
    print()
    print("  The last column recovers the first exactly: the sigmoid IS the")
    print("  inverse of the log-odds. That is why z is called a 'logit' -")
    print("  the linear part of the model predicts log-odds.")


def section6() -> None:
    section("3. THE SECTION 6 MODEL, VERIFIED")
    w = np.array([1.2, 0.8])
    b = -0.5
    print(f"  w = {w.tolist()}, b = {b}")
    print()
    print(f"  {'ticket':<12}{'body_std':>10}{'priority':>10}{'z':>9}{'p':>9}{'odds':>9}")
    for name, x in (("A", np.array([1.5, 1.0])), ("B", np.array([-0.5, 0.0]))):
        z = float(x @ w + b)
        p = float(sigmoid(z))
        odds = p / (1 - p)
        print(f"  ticket {name:<5}{x[0]:>10.1f}{x[1]:>10.0f}{z:>9.3f}{p:>9.4f}"
              f"{odds:>9.3f}")
    print()
    z_a = float(np.array([1.5, 1.0]) @ w + b)
    p_a = float(sigmoid(z_a))
    print(f"  Check: log(odds) for ticket A = {np.log(p_a / (1 - p_a)):.4f}, "
          f"which is z = {z_a:.4f}")
    print()
    print("  Coefficients as ODDS RATIOS:")
    for name, coef in zip(("body_length_std", "is_priority"), w):
        print(f"    {name:<20} e^{coef} = {np.exp(coef):.3f}x the odds")


def odds_ratio_trap() -> None:
    section("4. THE ODDS-RATIO TRAP - why 'adds X% probability' is always wrong")
    coefficient = 1.2
    ratio = float(np.exp(coefficient))
    print(f"  Coefficient {coefficient} -> odds ratio {ratio:.3f}")
    print("  Applying the SAME +1 standard deviation at different starting")
    print("  probabilities:")
    print()
    print(f"  {'start p':>10}{'start odds':>13}{'new odds':>12}{'new p':>10}"
          f"{'change':>12}")
    for p in (0.05, 0.25, 0.50, 0.75, 0.89, 0.98):
        odds = p / (1 - p)
        new_odds = odds * ratio
        new_p = new_odds / (1 + new_odds)
        print(f"  {p:>10.2f}{odds:>13.3f}{new_odds:>12.3f}{new_p:>10.4f}"
              f"{new_p - p:>+11.1%}")
    print()
    print("  The SAME coefficient and the SAME feature change produce a")
    print("  27-point probability rise starting from 0.25 and under a")
    print("  2-point rise starting from 0.98.")
    print()
    print("  'Each unit adds X% probability' is therefore never a correct")
    print("  statement about a logistic model. The odds ratio is constant;")
    print("  the probability effect is not.")


def softmax_demo() -> None:
    section("5. SOFTMAX")
    logits = np.array([2.0, 1.0, 0.1])
    print(f"  logits = {logits.tolist()}")
    exps = np.exp(logits)
    print(f"  exponentiate : {np.array2string(exps, precision=3)}")
    print(f"  sum          : {exps.sum():.3f}")
    result = softmax(logits)
    print(f"  divide       : {np.array2string(result, precision=3)}")
    print(f"  sums to      : {result.sum():.6f}")
    print()
    print("  ONLY DIFFERENCES MATTER - add 100 to every logit:")
    shifted = softmax(logits + 100)
    print(f"    {np.array2string(shifted, precision=3)}   identical? "
          f"{np.allclose(result, shifted)}")
    print()
    print("  OUTPUTS COMPETE - raise the first logit by 1:")
    raised = softmax(logits + np.array([1.0, 0.0, 0.0]))
    print(f"    before {np.array2string(result, precision=3)}")
    print(f"    after  {np.array2string(raised, precision=3)}")
    print("    The first rose; BOTH others fell. Softmax suits mutually")
    print("    exclusive classes. Independent per-label sigmoids suit")
    print("    multi-label problems (M1-L03).")


def overflow_demo() -> None:
    section("6. NUMERICAL OVERFLOW - and the one-line fix")
    big = np.array([1000.0, 999.0, 998.0])
    print(f"  logits = {big.tolist()}")
    print()
    print("  NAIVE softmax (no max subtraction):")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        e = np.exp(big)
        naive = e / e.sum()
    print(f"    np.exp(1000) = {e[0]}")
    print(f"    result       = {naive}   <- nan, the distribution is destroyed")
    print()
    print("  STABLE softmax (subtract the max first):")
    stable = softmax(big)
    print(f"    result       = {np.array2string(stable, precision=6)}")
    print(f"    sums to      = {stable.sum():.6f}")
    print()
    print("  Mathematically the two are identical - softmax is invariant to")
    print("  adding a constant. Numerically one produces nan and the other")
    print("  the right answer. This is why you use the library's version.")


def temperature_demo() -> None:
    section("7. TEMPERATURE - the same knob an LLM exposes")
    logits = np.array([3.0, 1.0, 0.5])
    tokens = ["Paris", "London", "Berlin"]
    print(f"  Next-token logits: {dict(zip(tokens, logits.tolist()))}")
    print()
    print(f"  {'temperature':>13}" + "".join(f"{t:>11}" for t in tokens) + "   character")
    for temp in (0.1, 0.5, 1.0, 2.0, 5.0, 20.0):
        probs = softmax(logits, temperature=temp)
        if temp < 0.5:
            note = "nearly deterministic"
        elif temp < 1.0:
            note = "sharpened"
        elif temp == 1.0:
            note = "the model's own distribution"
        elif temp < 5.0:
            note = "flattened, more variety"
        else:
            note = "approaching uniform"
        print(f"  {temp:>13.1f}" + "".join(f"{p:>11.4f}" for p in probs)
              + f"   {note}")
    print()
    print("  At T=0.1 the model picks 'Paris' essentially always. At T=20 it")
    print("  is close to choosing at random between all three.")
    print()
    print("  This IS the temperature parameter on an LLM API. 'temperature=0'")
    print("  is the limit of this table: always take the highest logit,")
    print("  which is greedy decoding (M1-L07, M4-L14).")


def train_from_scratch() -> None:
    section("8. LOGISTIC REGRESSION FROM SCRATCH")
    rng = np.random.default_rng(42)
    n = 400
    x = rng.normal(size=(n, 2))
    true_w, true_b = np.array([1.5, -2.0]), 0.3
    p_true = sigmoid(x @ true_w + true_b)
    y = (rng.random(n) < p_true).astype(float)

    w, b = np.zeros(2), 0.0
    lr = 0.5
    print(f"  {n} samples, true w = {true_w.tolist()}, true b = {true_b}")
    print()
    print(f"  {'step':>7}{'loss':>12}{'w[0]':>10}{'w[1]':>10}{'b':>10}{'accuracy':>11}")
    for step in range(2001):
        p = sigmoid(x @ w + b)
        if step % 400 == 0:
            eps = 1e-12
            loss = float(-(y * np.log(p + eps) + (1 - y) * np.log(1 - p + eps)).mean())
            acc = float(((p > 0.5) == y).mean())
            print(f"  {step:>7}{loss:>12.4f}{w[0]:>10.4f}{w[1]:>10.4f}{b:>10.4f}"
                  f"{acc:>11.3f}")
        grad = p - y
        w -= lr * (x.T @ grad) / n
        b -= lr * grad.mean()
    print()
    print(f"  recovered w = [{w[0]:.3f}, {w[1]:.3f}], b = {b:.3f}")
    print(f"  true      w = {true_w.tolist()}, b = {true_b}")
    print()
    print("  The gradient used was (1/n) X^T (p - y) - the SAME FORM as")
    print("  linear regression's, because the sigmoid's derivative and")
    print("  cross-entropy's derivative cancel exactly.")


def threshold_sweep() -> None:
    section("9. THE THRESHOLD IS A DECISION, NOT A DEFAULT")
    rng = np.random.default_rng(7)
    n = 2000
    # An imbalanced problem: 8% positives.
    y = (rng.random(n) < 0.08).astype(float)
    p = np.clip(sigmoid(rng.normal(loc=np.where(y == 1, 1.2, -1.2), scale=1.1)),
                1e-6, 1 - 1e-6)

    print(f"  {n} predictions, {y.mean():.1%} genuinely positive")
    print()
    print(f"  {'threshold':>11}{'predicted +':>13}{'precision':>12}{'recall':>10}"
          f"{'F1':>9}")
    for t in (0.1, 0.2, 0.3, 0.5, 0.7, 0.9):
        pred = p >= t
        tp = float((pred & (y == 1)).sum())
        fp = float((pred & (y == 0)).sum())
        fn = float((~pred & (y == 1)).sum())
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        print(f"  {t:>11.1f}{int(pred.sum()):>13}{precision:>12.3f}{recall:>10.3f}"
              f"{f1:>9.3f}")
    print()
    print("  Nothing about the MODEL changed across those rows - only the")
    print("  decision rule bolted on top of it.")
    print()
    print("  Screening for something serious? Take a low threshold: catch")
    print("  more real cases, accept more false alarms.")
    print("  Auto-blocking user content? Take a high one: silencing a real")
    print("  user costs more than missing one bad post.")
    print("  0.5 is a default, not an answer.")


def main() -> None:
    print("=" * 74)
    print("LOGISTIC REGRESSION, THE SIGMOID AND SOFTMAX")
    print("=" * 74)
    sigmoid_shape()
    logits_odds()
    section6()
    odds_ratio_trap()
    softmax_demo()
    overflow_demo()
    temperature_demo()
    train_from_scratch()
    threshold_sweep()
    print()
    print("=" * 74)


if __name__ == "__main__":
    main()
