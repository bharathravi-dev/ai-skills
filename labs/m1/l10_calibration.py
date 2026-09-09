"""M1-L10: non-determinism, calibration, and choosing a threshold.

    python3 labs/m1/l10_calibration.py

Three demonstrations, no API key and no libraries needed.
"""

from __future__ import annotations

import random

SEED = 5
N_PREDICTIONS = 2000
# How miscalibrated the simulated model is:
#     true_accuracy = CAL_INTERCEPT + CAL_SLOPE * stated_confidence
# Perfect calibration would be INTERCEPT=0.0, SLOPE=1.0 (accuracy == stated).
# These values reproduce the table in section 6 of the lesson: a model that
# says 0.95 is right about 0.81 of the time.
CAL_INTERCEPT = 0.2875
CAL_SLOPE = 0.55


# ---------------------------------------------------------------------------
# 1. Sampling non-determinism
# ---------------------------------------------------------------------------
# A toy next-token distribution, of the kind a real model produces at every
# single step of generation.
DISTRIBUTION: dict[str, float] = {
    " Paris": 0.89,
    " located": 0.04,
    " the": 0.03,
    " a": 0.02,
    " home": 0.02,
}


def demo_sampling() -> None:
    print("=" * 70)
    print("1. WHY THE SAME PROMPT GIVES DIFFERENT ANSWERS")
    print("=" * 70)
    print('Prompt: "The capital of France is"')
    print()
    print("The model produces a probability distribution over next tokens:")
    for token, prob in DISTRIBUTION.items():
        bar = "#" * int(prob * 50)
        print(f"    {token!r:<12} {prob:.2f}  {bar}")
    print()

    rng = random.Random(SEED)
    tokens = list(DISTRIBUTION.keys())
    probs = list(DISTRIBUTION.values())

    print("SAMPLING (temperature > 0) - 20 runs of the identical prompt:")
    draws = [rng.choices(tokens, weights=probs, k=1)[0] for _ in range(20)]
    print("   ", " |".join(d.strip() for d in draws))
    unique = sorted(set(draws))
    print(f"    -> {len(unique)} distinct outputs from the SAME input: {unique}")
    print()

    print("GREEDY (temperature = 0) - 20 runs of the identical prompt:")
    greedy = [max(DISTRIBUTION, key=DISTRIBUTION.get) for _ in range(20)]
    print("   ", " |".join(g.strip() for g in greedy))
    print(f"    -> {len(set(greedy))} distinct output. Reproducible.")
    print()
    print("But note: greedy removes SAMPLING variance only. Hosted models can")
    print("still differ run to run because floating-point addition is not")
    print("associative and batching/hardware change the summation order.")
    print("Never assert exact model output in a test.")
    print()


# ---------------------------------------------------------------------------
# 2. Calibration
# ---------------------------------------------------------------------------
def simulate_predictions(rng: random.Random) -> list[tuple[float, bool]]:
    """Return (stated_confidence, was_correct) pairs from an OVERCONFIDENT model.

    The model states confidence `c`, but its true accuracy is a flattened
    version of it: it never gets as good as it claims, and the gap widens as
    the claim gets bolder.
    """
    out: list[tuple[float, bool]] = []
    for _ in range(N_PREDICTIONS):
        stated = rng.uniform(0.5, 1.0)
        true_accuracy = CAL_INTERCEPT + CAL_SLOPE * stated
        correct = rng.random() < true_accuracy
        out.append((stated, correct))
    return out


def reliability_table(preds: list[tuple[float, bool]]) -> None:
    print("=" * 70)
    print("2. CALIBRATION: does stated confidence match actual accuracy?")
    print("=" * 70)
    print(f"{N_PREDICTIONS} predictions from a simulated overconfident model.")
    print()
    print(f"{'bucket':<14}{'n':>6}{'stated':>10}{'actual':>10}{'gap':>9}  reliability")
    print("-" * 70)

    edges = [0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
    ece = 0.0
    for i in range(len(edges) - 1):
        lo, hi = edges[i], edges[i + 1]
        bucket = [(c, ok) for c, ok in preds if lo <= c < hi or (hi == 1.0 and c == 1.0)]
        if not bucket:
            continue
        mean_stated = sum(c for c, _ in bucket) / len(bucket)
        actual = sum(1 for _, ok in bucket if ok) / len(bucket)
        gap = actual - mean_stated
        ece += abs(gap) * len(bucket) / len(preds)

        # A simple visual: where the actual accuracy sits on a 0.5-1.0 scale.
        pos = int((actual - 0.5) / 0.5 * 40)
        expected_pos = int((mean_stated - 0.5) / 0.5 * 40)
        line = [" "] * 42
        line[max(0, min(41, expected_pos))] = "|"      # where it CLAIMS to be
        line[max(0, min(41, pos))] = "*"               # where it ACTUALLY is
        print(f"{lo:.1f}-{hi:.1f}      {len(bucket):>6}{mean_stated:>10.3f}"
              f"{actual:>10.3f}{gap:>+9.3f}  {''.join(line)}")

    print("-" * 70)
    print("                                                  | = stated   * = actual")
    print()
    print(f"Expected Calibration Error (ECE) = {ece:.3f}")
    print("  In plain English: on average the model's stated confidence is")
    print(f"  wrong by about {ece * 100:.1f} percentage points.")
    print()
    print("  Look at the DIRECTION of the gaps, not just their size. At low")
    print("  confidence the model is slightly UNDER-confident (gap positive:")
    print("  it does better than it claims). From about 0.7 upward it flips to")
    print("  OVER-confident, and the gap widens as the claim gets bolder:")
    print("  -0.034, then -0.091, then -0.139.")
    print()
    print("  That pattern is the worst possible shape. The model is most wrong")
    print("  about itself exactly where you were planning to trust it - in the")
    print("  high-confidence bucket you wanted to automate. A single average")
    print("  ECE number would have hidden this. Always look per bucket.")
    print()


# ---------------------------------------------------------------------------
# 3. Threshold analysis
# ---------------------------------------------------------------------------
def threshold_table(preds: list[tuple[float, bool]]) -> None:
    print("=" * 70)
    print("3. CHOOSING AN AUTO-APPROVAL THRESHOLD")
    print("=" * 70)
    print("You want to auto-approve high-confidence predictions and send the")
    print("rest to a human. Which threshold actually delivers what you need?")
    print()
    print(f"{'threshold':>10}{'automated':>11}{'% traffic':>11}"
          f"{'accuracy':>10}{'errors':>9}   vs 95% target")
    print("-" * 70)

    for threshold in (0.60, 0.70, 0.80, 0.85, 0.90, 0.95, 0.99):
        selected = [(c, ok) for c, ok in preds if c >= threshold]
        if not selected:
            continue
        accuracy = sum(1 for _, ok in selected if ok) / len(selected)
        errors = sum(1 for _, ok in selected if not ok)
        share = 100 * len(selected) / len(preds)
        verdict = "MEETS TARGET" if accuracy >= 0.95 else f"short by {(0.95 - accuracy) * 100:.1f}pp"
        print(f"{threshold:>10.2f}{len(selected):>11}{share:>10.1f}%"
              f"{accuracy:>10.3f}{errors:>9}   {verdict}")

    print("-" * 70)
    print()
    print("READ THIS CAREFULLY:")
    print("* No threshold reaches 95% accuracy - not even 0.99.")
    print("* That is a genuinely important finding. It means the 95% target is")
    print("  NOT achievable by thresholding this model at all. You would need a")
    print("  better model, a narrower task, or a different automation target.")
    print("* Discovering this BEFORE launch is the entire value of the exercise.")
    print("* Note the trade-off in the table: raising the threshold improves")
    print("  accuracy but automates less traffic. There is no free setting.")
    print("* And note what you must NOT do: take the model's stated 0.95 at")
    print("  face value. It claims 0.95 and delivers far less.")
    print("=" * 70)


def main() -> None:
    demo_sampling()
    rng = random.Random(SEED)
    preds = simulate_predictions(rng)
    reliability_table(preds)
    threshold_table(preds)


if __name__ == "__main__":
    main()
