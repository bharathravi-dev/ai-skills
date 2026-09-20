"""M10-L12 lab -- a release gate is a decision rule applied to noisy measurements.
This lab simulates releases and measures:

  1. gating on a point estimate vs on a confidence bound, when NOTHING changed,
  2. a slice regression hidden by an aggregate improvement,
  3. how small an effect an evaluation set of a given size can detect,
  4. a gate suite: hard gates, quality gates and budget gates over six candidates,
  5. best-of-k selection: how much apparent gain comes from choosing the winner.

Deterministic (seeded). No API key, no network, no third-party dependencies.
Run:  python labs/m10/l12_release_gates.py
"""

from __future__ import annotations

import math
import random
import sys

sys.stdout.reconfigure(encoding="utf-8")


def rule(title: str) -> None:
    print(f"\n{'=' * 76}\n{title}\n{'=' * 76}")


rng = random.Random(1012)


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (0.0, 1.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


# ============================================================ 1
rule("1. GATING ON A POINT ESTIMATE VS A CONFIDENCE BOUND")

TRUE_QUALITY = 0.82
THRESHOLD = 0.80
TRIALS = 1000
for n in (100, 400):
    point_pass = bound_pass = 0
    for _ in range(TRIALS):
        k = sum(1 for _ in range(n) if rng.random() < TRUE_QUALITY)
        point_pass += (k / n) >= THRESHOLD
        bound_pass += wilson(k, n)[0] >= THRESHOLD
    print(f"  n={n:<5} true quality {TRUE_QUALITY:.0%}, gate at {THRESHOLD:.0%}:"
          f"   point estimate passes {point_pass / TRIALS:.0%} of runs,"
          f"   lower bound passes {bound_pass / TRIALS:.0%}")
BAD_QUALITY = 0.78
for n in (100, 400):
    point_pass = bound_pass = 0
    for _ in range(TRIALS):
        k = sum(1 for _ in range(n) if rng.random() < BAD_QUALITY)
        point_pass += (k / n) >= THRESHOLD
        bound_pass += wilson(k, n)[0] >= THRESHOLD
    print(f"  n={n:<5} true quality {BAD_QUALITY:.0%} (BELOW the gate):"
          f"   point estimate passes {point_pass / TRIALS:.0%} of runs,"
          f"   lower bound passes {bound_pass / TRIALS:.0%}")
print("\n  A point estimate against a threshold is a coin flip when the true value is")
print("  near it, and lets a genuinely worse system through in a third of runs at")
print("  n=100. A lower confidence bound is strict: it asks the release to PROVE the")
print("  quality, and needs a larger evaluation set to pass at all.")


# ============================================================ 2
rule("2. AN AGGREGATE IMPROVEMENT HIDING A SLICE REGRESSION")

SLICES = {"english / billing": 2400, "english / delivery": 1500, "french / billing": 260,
          "french / delivery": 140, "screen-reader users": 120}
BASELINE = {"english / billing": 0.86, "english / delivery": 0.84, "french / billing": 0.79,
            "french / delivery": 0.80, "screen-reader users": 0.81}
CANDIDATE = {"english / billing": 0.89, "english / delivery": 0.87, "french / billing": 0.71,
             "french / delivery": 0.78, "screen-reader users": 0.74}
total = sum(SLICES.values())
base_overall = sum(BASELINE[s] * n for s, n in SLICES.items()) / total
cand_overall = sum(CANDIDATE[s] * n for s, n in SLICES.items()) / total
print(f"  aggregate: baseline {base_overall:.1%} -> candidate {cand_overall:.1%} "
      f"({cand_overall - base_overall:+.1%})   an aggregate gate at -0.0% PASSES\n")
print(f"  {'slice':<22}{'n':>7}{'baseline':>11}{'candidate':>11}{'change':>10}   per-slice gate (-2 points)")
for s, n in SLICES.items():
    delta = CANDIDATE[s] - BASELINE[s]
    verdict = "FAIL" if delta < -0.02 else "pass"
    print(f"  {s:<22}{n:>7}{BASELINE[s]:>11.1%}{CANDIDATE[s]:>11.1%}{delta:>+10.1%}   {verdict}")
failing = [s for s in SLICES if CANDIDATE[s] - BASELINE[s] < -0.02]
print(f"\n  slices failing a -2 point rule: {len(failing)} ({', '.join(failing)})")
print(f"  those slices are {sum(SLICES[s] for s in failing) / total:.0%} of volume -- small enough for the")
print("  aggregate to improve while the people in them get a materially worse system.")


# ============================================================ 3
rule("3. WHAT CAN AN EVALUATION SET OF THIS SIZE EVEN DETECT?")

def detectable(n: int, p: float = 0.82, z: float = 1.96) -> float:
    """Roughly the smallest difference distinguishable from noise with this n."""
    return z * math.sqrt(2 * p * (1 - p) / n)


for n in (50, 100, 300, 1000, 3000):
    print(f"  n={n:<5} smallest detectable difference ~= {detectable(n):>5.1%}"
          f"   (so a '{detectable(n) / 2:.0%} improvement' claim at this size is noise)")
print("\n  Set the gate's tolerance from the evaluation set you actually have, and size")
print("  the set from the difference you need to detect -- especially per slice, where")
print("  n is a fraction of the total (M3-L14, M5-L18).")


# ============================================================ 4
rule("4. A GATE SUITE OVER SIX CANDIDATE RELEASES")

CANDIDATES = {
    #                     quality  worst slice   unsafe   p95 ms   cost/1k
    "A: prompt tweak":      (0.845, -0.005, 0.002, 1900, 0.9),
    "B: new model":         (0.869, -0.031, 0.003, 2400, 1.4),
    "C: cheaper model":     (0.828, -0.012, 0.004, 1500, 0.4),
    "D: retrieval change":  (0.851, +0.004, 0.002, 2100, 1.0),
    "E: aggressive prompt": (0.872, -0.002, 0.019, 2000, 1.0),
    "F: bigger context":    (0.858, +0.002, 0.002, 3400, 2.6),
}
GATES = {
    "quality >= 84%": lambda c: c[0] >= 0.84,
    "no slice worse than -2 points": lambda c: c[1] >= -0.02,
    "unsafe outputs <= 0.5%": lambda c: c[2] <= 0.005,
    "p95 latency <= 2500 ms": lambda c: c[3] <= 2500,
    "cost <= GBP 1.50 / 1k requests": lambda c: c[4] <= 1.5,
}
HARD = ["no slice worse than -2 points", "unsafe outputs <= 0.5%"]
SHORT = {"quality >= 84%": "quality", "no slice worse than -2 points": "slices",
         "unsafe outputs <= 0.5%": "unsafe", "p95 latency <= 2500 ms": "p95",
         "cost <= GBP 1.50 / 1k requests": "cost"}
print(f"  {'candidate':<22}" + "".join(f"{SHORT[g]:>12}" for g in GATES) + "   verdict")
for name, c in CANDIDATES.items():
    results = {g: fn(c) for g, fn in GATES.items()}
    hard_fail = [g for g in HARD if not results[g]]
    soft_fail = [g for g, ok in results.items() if not ok and g not in HARD]
    verdict = "BLOCKED" if hard_fail else ("review" if soft_fail else "ship")
    print(f"  {name:<22}" + "".join(f"{('pass' if results[g] else 'FAIL'):>12}" for g in GATES)
          + f"   {verdict}")
print("\n  Hard gates (a slice regression, unsafe output rate) block regardless of the")
print("  headline number; budget gates are trade-offs a named owner can accept with a")
print("  recorded reason. 'E: aggressive prompt' has the best quality in the table.")


# ============================================================ 5
rule("5. BEST-OF-K: HOW MUCH OF AN IMPROVEMENT IS JUST CHOOSING THE WINNER?")

TRUE = 0.82
for k in (1, 5, 20):
    for n in (200, 1000):
        inflation = []
        for _ in range(400):
            best = max(sum(1 for _ in range(n) if rng.random() < TRUE) / n for _ in range(k))
            inflation.append(best - TRUE)
        mean_inflation = sum(inflation) / len(inflation)
        print(f"  k={k:<3} candidates, n={n:<5}: best observed score exceeds the true value by "
              f"{mean_inflation:+.2%} on average")
print("\n  Every candidate here is identical. Picking the best of twenty on one")
print("  evaluation set manufactures 2 to 5 points of 'improvement', and a smaller")
print("  set manufactures more. Hold out a confirmation set for the chosen")
print("  candidate, and report THAT number (M5-L18).")


rule("6. WHAT THIS LAB IS AND IS NOT")
print("  REAL: every pass rate, slice figure, detectable difference and inflation")
print("  number above is computed by simulation or by the stated formula.")
print("\n  ILLUSTRATIVE: quality, safety, latency and cost figures for the six")
print("  candidates are invented; real gates use your measured results.")
print("\n  NOT SHOWN: online evaluation and canaries (M13-L14), human evaluation")
print("  (M13-L13), and the content of the evaluation set itself (M5-L18).")
print("\nDone.")
