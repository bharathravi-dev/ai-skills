"""M1-L01 self-check: classify systems as AI / ML / DL / Generative.

Run interactively:
    python3 labs/m1/l01_taxonomy_quiz.py

Show the answer table without playing:
    python3 labs/m1/l01_taxonomy_quiz.py --show-answers

No third-party dependencies. Standard library only. Python 3.9+.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass


@dataclass
class System:
    """One system to classify, with the correct answers and the reason."""

    name: str
    ai: bool
    ml: bool
    dl: bool
    generative: bool
    reason: str


SYSTEMS: list[System] = [
    System(
        name="Fixed-threshold thermostat",
        ai=False, ml=False, dl=False, generative=False,
        reason="A human wrote `if temp < 18`. The task is also not one we call "
               "intelligent. This is ordinary software.",
    ),
    System(
        name="Learning thermostat (occupancy)",
        ai=True, ml=True, dl=False, generative=False,
        reason="Fits your schedule from observed behaviour, so the logic came from "
               "data (ML). Small tabular problem, no deep stack. Output is a time or "
               "probability, not constructed content.",
    ),
    System(
        name="Keyword spam filter",
        ai=True, ml=False, dl=False, generative=False,
        reason="AI by historical convention, but the keyword list was written by a "
               "human, so nothing was learned.",
    ),
    System(
        name="Naive Bayes spam filter",
        ai=True, ml=True, dl=False, generative=False,
        reason="Same task, but the word weights are estimated from labelled emails. "
               "One layer of learned parameters, so not deep. Output is a label.",
    ),
    System(
        name="Face detection in a phone camera",
        ai=True, ml=True, dl=True, generative=False,
        reason="A many-layer convolutional network trained on labelled images. Output "
               "is boxes plus face/not-face: a fixed shape, not open-ended content. "
               "The key example that deep learning does not imply generative.",
    ),
    System(
        name="Chess engine using search + handcrafted evaluation",
        ai=True, ml=False, dl=False, generative=False,
        reason="Classic symbolic AI: minimax search plus a human-written evaluation "
               "function. Strong play, zero learning.",
    ),
    System(
        name="AlphaZero-style chess engine",
        ai=True, ml=True, dl=True, generative=False,
        reason="Same task as above but the evaluation is a deep network trained by "
               "self-play. Output is a move choice and a value: a selection, not "
               "constructed content.",
    ),
    System(
        name="Customer-churn model on tabular data",
        ai=True, ml=True, dl=False, generative=False,
        reason="Typically gradient-boosted trees or logistic regression on rows and "
               "columns. Learned, but not a deep stack. Output is a probability.",
    ),
    System(
        name="LLM chat assistant",
        ai=True, ml=True, dl=True, generative=True,
        reason="A deep transformer trained on text, producing a token sequence built "
               "one step at a time from a huge vocabulary. All four apply.",
    ),
    System(
        name="Image generator from a text prompt",
        ai=True, ml=True, dl=True, generative=True,
        reason="A deep diffusion model constructing pixels that never existed. All "
               "four apply.",
    ),
]

QUESTIONS = ("AI", "ML", "DL", "Generative")


def ask_bool(prompt: str) -> bool:
    """Ask a yes/no question, accepting y/yes/n/no in any case."""
    while True:
        answer = input(f"    {prompt} (y/n): ").strip().lower()
        if answer.startswith("y"):
            return True
        if answer.startswith("n"):
            return False
        print("    Please answer y or n.")


def show_answers() -> None:
    """Print the full answer table. Deterministic, safe to compare exactly."""
    print("CLASSIFICATION ANSWER TABLE")
    print("=" * 80)
    print(f"{'System':<40} {'AI':<5} {'ML':<5} {'DL':<5} {'Gen'}")
    print("-" * 80)
    for s in SYSTEMS:
        flags = [("yes" if v else "no") for v in (s.ai, s.ml, s.dl, s.generative)]
        # Truncate to keep the columns aligned for long names.
        print(f"{s.name[:39]:<40} {flags[0]:<5} {flags[1]:<5} {flags[2]:<5} {flags[3]}")
    print("=" * 80)
    print(f"Total systems: {len(SYSTEMS)}")


def run_quiz() -> int:
    """Run the interactive quiz. Returns the score out of len(SYSTEMS) * 4."""
    print("M1-L01 taxonomy self-check")
    print("For each system, answer 4 yes/no questions.\n")

    score = 0
    for index, system in enumerate(SYSTEMS, start=1):
        print(f"[{index}/{len(SYSTEMS)}] {system.name}")
        got = [ask_bool(q + "?") for q in QUESTIONS]
        expected = [system.ai, system.ml, system.dl, system.generative]

        wrong = [label for label, g, e in zip(QUESTIONS, got, expected) if g != e]
        score += sum(1 for g, e in zip(got, expected) if g == e)

        if wrong:
            print(f"    MISSED: {', '.join(wrong)}")
        else:
            print("    All four correct.")
        print(f"    Why: {system.reason}\n")

    total = len(SYSTEMS) * len(QUESTIONS)
    print("=" * 60)
    print(f"Score: {score}/{total}")
    if score >= total * 0.8:
        print("Good. Move on to M1-L02.")
    else:
        print("Re-read section 5.2 (the deciding property for each term), then retry.")
    return score


def main() -> None:
    if "--show-answers" in sys.argv:
        show_answers()
        return
    try:
        run_quiz()
    except (EOFError, KeyboardInterrupt):
        print("\nStopped. Run with --show-answers to see the table.")


if __name__ == "__main__":
    main()
