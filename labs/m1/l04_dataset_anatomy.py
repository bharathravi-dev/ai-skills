"""M1-L04: build a dataset by hand and see the X/y alignment bug.

    python3 labs/m1/l04_dataset_anatomy.py

Standard library only. No NumPy yet - that is M3-L01.
"""

from __future__ import annotations

import random

# ---------------------------------------------------------------------------
# Raw dataset from the lesson: support tickets, predicting SLA breach.
# Synthetic data written for this course.
# (channel, tier, body_len, hour, prior_tickets, breached)
# ---------------------------------------------------------------------------
RAW: list[tuple[str, str, int, int, int, int]] = [
    ("email", "free",       850, 22, 0, 1),
    ("chat",  "enterprise", 120, 10, 5, 0),
    ("email", "pro",        430, 14, 2, 0),
    ("phone", "free",       210,  3, 1, 1),
    ("chat",  "pro",       1500, 16, 0, 1),
]


def one_hot(value: str, categories: list[str]) -> list[float]:
    """Return a list with 1.0 in the position of `value`, 0.0 elsewhere."""
    return [1.0 if value == category else 0.0 for category in categories]


def build_matrix() -> tuple[list[list[float]], list[int], list[str]]:
    """Turn RAW into a numeric feature matrix X, label vector y, and names."""
    # sorted() gives a STABLE category order. If this order changed between
    # training and inference, column 3 would silently change meaning.
    channels = sorted({row[0] for row in RAW})
    tiers = sorted({row[1] for row in RAW})

    names = (
        [f"ch_{c}" for c in channels]
        + [f"tier_{t}" for t in tiers]
        + ["body_len", "hour", "prior"]
    )

    X: list[list[float]] = []
    y: list[int] = []
    for channel, tier, body_len, hour, prior, breached in RAW:
        features = (
            one_hot(channel, channels)
            + one_hot(tier, tiers)
            + [float(body_len), float(hour), float(prior)]
        )
        X.append(features)
        y.append(breached)

    return X, y, names


def main() -> None:
    print("=" * 60)
    print("DATASET ANATOMY - support ticket SLA breach")
    print("=" * 60)
    print()

    print("Raw dataset (5 examples, 5 features + 1 label)")
    print(f"  {'#':<3}{'channel':<9}{'tier':<12}{'body_len':>8}{'hour':>6}{'prior':>7}  | y")
    for i, (channel, tier, body_len, hour, prior, breached) in enumerate(RAW, 1):
        print(f"  {i:<3}{channel:<9}{tier:<12}{body_len:>8}{hour:>6}{prior:>7}  | {breached}")
    print()

    channels = sorted({row[0] for row in RAW})
    tiers = sorted({row[1] for row in RAW})
    print("Categories discovered (sorted for stability):")
    print(f"  channel -> {channels}")
    print(f"  tier    -> {tiers}")
    print()

    X, y, names = build_matrix()
    print("After one-hot encoding:")
    print(f"  X shape = ({len(X)}, {len(X[0])})   n={len(X)} examples, d={len(X[0])} features")
    print(f"  y shape = ({len(y)},)")
    print(f"  column names: {names[:6]},")
    print(f"                {names[6:]}")
    print()
    for i in range(2):
        print(f"  X[{i}] = {X[i]}   y[{i}] = {y[i]}")
    print()

    # -----------------------------------------------------------------------
    # The alignment bug: shuffle X but not y. Nothing complains.
    # -----------------------------------------------------------------------
    print("-" * 60)
    print("THE ALIGNMENT BUG")
    print("-" * 60)

    body_len_index = names.index("body_len")

    print("Correct pairing:")
    for i in range(3):
        print(f"  example {i + 1}: body_len={int(X[i][body_len_index]):<4} -> y={y[i]}")
    print()

    X_only = [row[:] for row in X]        # copy the rows
    random.Random(0).shuffle(X_only)      # shuffle X, leave y untouched

    print("After shuffling X but NOT y:")
    for i in range(3):
        mark = "   <-- wrong label" if X_only[i] != X[i] else ""
        print(f"  example {i + 1}: body_len={int(X_only[i][body_len_index]):<4} -> y={y[i]}{mark}")
    print()

    print("Nothing raised an exception. No type error. No warning.")
    print("The code runs perfectly and the model learns noise.")
    print("This is why X and y must always be shuffled together.")
    print("=" * 60)


if __name__ == "__main__":
    main()
