"""M1-L05: parameter vs hyperparameter drill, plus an optimistic-bias demo.

    python3 labs/m1/l05_hyperparameter_sort.py          # drill
    python3 labs/m1/l05_hyperparameter_sort.py --show   # reference table
    python3 labs/m1/l05_hyperparameter_sort.py --demo   # the important one

Standard library only.
"""

from __future__ import annotations

import random
import statistics
import sys
from dataclasses import dataclass

# ---------------------------------------------------------------------------
# Part 1: the sorting drill
# ---------------------------------------------------------------------------
ITEMS: list[tuple[str, str, str]] = [
    ("Number of trees in a random forest", "hyper",
     "You choose it before training. The trees themselves are parameters."),
    ("Coefficient on 'age' in a logistic regression", "param",
     "Computed by the fitting procedure from data."),
    ("Temperature passed to an LLM API", "hyper",
     "A setting you choose per request. Nothing learned it."),
    ("Values in an LLM's embedding table", "param",
     "Learned during pretraining. Billions of them."),
    ("Number of clusters k in k-means", "hyper",
     "You must pick k before running. The algorithm cannot choose it."),
    ("Coordinates of a cluster centre", "param",
     "Computed by the algorithm as it iterates."),
    ("Your system prompt", "hyper",
     "Set before running, changes behaviour materially, invalidates previous "
     "measurements when changed. Version it (M5-L12)."),
    ("Smoothing constant in Naive Bayes", "hyper",
     "In M1-L02 you added 1 to every count. That 1 was a human choice."),
    ("Max depth of a decision tree", "hyper",
     "A shape constraint you impose before training."),
    ("Split threshold chosen at a tree node", "param",
     "The algorithm searched the data to find it."),
    ("Number of retrieved chunks k in RAG", "hyper",
     "Your application's setting, tuned on a validation set like any other."),
    ("Learned word frequencies in a spam model", "param",
     "Counted from the training corpus."),
]


def show_table() -> None:
    print("PARAMETER vs HYPERPARAMETER REFERENCE")
    print("=" * 78)
    print(f"{'Item':<48} {'Category'}")
    print("-" * 78)
    for text, kind, _ in ITEMS:
        label = "parameter" if kind == "param" else "HYPERparameter"
        print(f"{text[:47]:<48} {label}")
    print("=" * 78)
    n_hyper = sum(1 for _, k, _ in ITEMS if k == "hyper")
    print(f"Total: {len(ITEMS)}  hyperparameters={n_hyper}  parameters={len(ITEMS) - n_hyper}")


def run_drill() -> None:
    print("M1-L05 drill: type 'p' for parameter, 'h' for hyperparameter.\n")
    score = 0
    for i, (text, kind, why) in enumerate(ITEMS, 1):
        print(f"[{i}/{len(ITEMS)}] {text}")
        answer = input("    p / h: ").strip().lower()
        got = "param" if answer.startswith("p") else "hyper"
        if got == kind:
            score += 1
            print("    CORRECT.")
        else:
            correct = "parameter" if kind == "param" else "hyperparameter"
            print(f"    WRONG - it is a {correct}.")
        print(f"    {why}\n")
    print("=" * 60)
    print(f"Score: {score}/{len(ITEMS)}")


# ---------------------------------------------------------------------------
# Part 2: the optimistic-bias demo. This is the point of the lesson.
# ---------------------------------------------------------------------------
@dataclass
class Candidate:
    """One hyperparameter setting. All candidates here are equally good."""

    name: str
    true_rate: float
    val_score: float


def simulate_selection(
    n_trials: int, eval_size: int, true_rate: float, rng: random.Random
) -> tuple[float, float]:
    """Try n_trials equally-good candidates; return (winner's observed score,
    winner's true score).

    Every candidate has the SAME true success rate. Any difference in observed
    score is pure sampling noise.
    """
    candidates: list[Candidate] = []
    for i in range(n_trials):
        # Score this candidate on `eval_size` items. `True` counts as 1.
        successes = sum(rng.random() < true_rate for _ in range(eval_size))
        candidates.append(
            Candidate(f"cand{i}", true_rate, successes / eval_size)
        )

    # A human tuner picks the best-looking one.
    winner = max(candidates, key=lambda c: c.val_score)
    return winner.val_score, winner.true_rate


def run_demo(true_rate: float = 0.70, eval_size: int = 100, repeats: int = 2000) -> None:
    print("=" * 64)
    print("OPTIMISTIC BIAS: why you must not tune on the test set")
    print("=" * 64)
    print(f"Setup: every candidate is EQUALLY GOOD - true success rate {true_rate:.2f}.")
    print("       Any difference we observe is pure luck.")
    print(f"       Eval set = {eval_size} items. Repeated {repeats} times.")
    print()
    print(" trials   best score on the set   true score of winner   optimism")
    print("-" * 68)

    rng = random.Random(42)
    for n_trials in (1, 3, 5, 10, 20, 50, 100):
        observed: list[float] = []
        actual: list[float] = []
        for _ in range(repeats):
            val, true = simulate_selection(n_trials, eval_size, true_rate, rng)
            observed.append(val)
            actual.append(true)
        mean_obs = statistics.mean(observed)
        mean_true = statistics.mean(actual)
        print(
            f"{n_trials:>7}   {mean_obs:>21.4f}   {mean_true:>20.4f}   "
            f"{mean_obs - mean_true:>+8.4f}"
        )

    print()
    print("Reading this table:")
    print(f"  Every candidate is identical - true rate {true_rate:.2f} for all of them.")
    print("  Yet after trying 50, the winner APPEARS to score noticeably higher.")
    print("  That gap is entirely selection luck. There is no real gain.")
    print("  Report it and you have overstated your system by that much.")
    print()
    print("  The fix: pick the winner on a VALIDATION set, then measure it")
    print("  ONCE on a test set that played no part in the choice.")
    print("=" * 64)


def main() -> None:
    if "--show" in sys.argv:
        show_table()
    elif "--demo" in sys.argv:
        run_demo()
    else:
        try:
            run_drill()
        except (EOFError, KeyboardInterrupt):
            print("\nStopped. Try --show or --demo.")


if __name__ == "__main__":
    main()
