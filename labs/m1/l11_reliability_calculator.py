"""M1-L11: compound reliability of an AI pipeline.

    python3 labs/m1/l11_reliability_calculator.py

Standard library only.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

DAILY_VOLUME = 500


@dataclass(frozen=True)
class Step:
    name: str
    ai_rate: float          # success rate if done by a model
    code_rate: float | None  # success rate if done deterministically, else None
    can_be_code: bool


PIPELINE: list[Step] = [
    Step("classify ticket",   0.95, None, False),
    Step("retrieve policy",   0.90, None, False),
    Step("extract account id", 0.95, 0.999, True),
    Step("look up account",   0.98, 1.000, True),
    Step("draft reply",       0.90, None, False),
    Step("send",              0.99, 1.000, True),
]


def reliability(rates: list[float]) -> float:
    """Compound success rate: every required step must succeed."""
    return math.prod(rates)


def report(title: str, names: list[str], rates: list[float]) -> float:
    total = reliability(rates)
    failures = DAILY_VOLUME * (1 - total)
    print(f"{title}")
    for name, rate in zip(names, rates):
        print(f"    {name:<22} {rate:.3f}")
    product = "  x  ".join(f"{r:.3f}" for r in rates)
    print(f"    {'':<22} {product}")
    print(f"    -> end-to-end reliability = {total:.4f}  ({total:.1%})")
    print(f"    -> at {DAILY_VOLUME} tickets/day: {failures:.0f} go wrong somewhere")
    print()
    return total


def main() -> None:
    print("=" * 72)
    print("COMPOUND RELIABILITY: why good steps make a poor pipeline")
    print("=" * 72)
    print()

    names = [s.name for s in PIPELINE]

    all_ai = [s.ai_rate for s in PIPELINE]
    r_ai = report("DESIGN A - every step done by a model", names, all_ai)

    hybrid = [s.code_rate if s.can_be_code else s.ai_rate for s in PIPELINE]
    r_hybrid = report(
        "DESIGN B - the three deterministic steps done in code", names, hybrid
    )

    print(f"Hybrid improvement: {r_ai:.1%} -> {r_hybrid:.1%} "
          f"({(r_hybrid - r_ai) * DAILY_VOLUME:.0f} fewer bad tickets per day)")
    print()

    # -----------------------------------------------------------------------
    # Deleting a step vs improving a step
    # -----------------------------------------------------------------------
    print("-" * 72)
    print("DELETE A STEP  vs  IMPROVE A STEP  (starting from Design A)")
    print("-" * 72)
    print(f"{'intervention':<40}{'reliability':>13}{'change':>11}")
    print("-" * 72)
    print(f"{'(baseline, Design A)':<40}{r_ai:>12.1%}{'':>11}")

    for i, step in enumerate(PIPELINE):
        removed = all_ai[:i] + all_ai[i + 1:]
        r_removed = reliability(removed)
        print(f"{'DELETE: ' + step.name:<40}{r_removed:>12.1%}"
              f"{r_removed - r_ai:>+11.1%}")

    print()
    for i, step in enumerate(PIPELINE):
        improved = list(all_ai)
        improved[i] = min(0.999, improved[i] + 0.05)
        r_improved = reliability(improved)
        print(f"{'IMPROVE +5pp: ' + step.name:<40}{r_improved:>12.1%}"
              f"{r_improved - r_ai:>+11.1%}")

    print()
    print("Deleting a step multiplies reliability by 1/p, so removing the")
    print("WEAKEST step helps most. Improving a step by a fixed amount helps")
    print("by roughly (improvement/p) - also biggest for the weakest step.")
    print("Either way: fix the worst step, and prefer deleting it to tuning it.")
    print()

    # -----------------------------------------------------------------------
    # The p^n decay table
    # -----------------------------------------------------------------------
    print("-" * 72)
    print("HOW RELIABILITY DECAYS WITH CHAIN LENGTH  (p^n)")
    print("-" * 72)
    print(f"{'steps':>7}{'p=0.99':>10}{'p=0.95':>10}{'p=0.90':>10}{'p=0.80':>10}")
    print("-" * 72)
    for n in (1, 3, 5, 10, 20, 30):
        row = "".join(f"{p ** n:>10.1%}" for p in (0.99, 0.95, 0.90, 0.80))
        print(f"{n:>7}{row}")
    print("-" * 72)
    print()
    print("The p=0.90 column is the one to remember. A 10-step agent whose")
    print("every step works 9 times out of 10 finishes correctly about a")
    print("THIRD of the time. This is why agents get hard step limits")
    print("(M8-L15) and why 'just add another tool call' is not free.")
    print()
    print("NOTE: this rule is OPTIMISTIC. It assumes step failures are")
    print("independent. In reality a malformed input breaks several steps at")
    print("once, so measured reliability is usually worse than p^n predicts.")
    print("=" * 72)


if __name__ == "__main__":
    main()
