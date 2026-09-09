"""M1-L03 drill: name the task shape for each real-world request.

    python3 labs/m1/l03_task_shapes.py          # interactive drill
    python3 labs/m1/l03_task_shapes.py --show   # answer table

Standard library only. Python 3.9+.
"""

from __future__ import annotations

import sys
import textwrap
from collections import Counter
from dataclasses import dataclass
from typing import Literal

# A Literal restricts a value to an exact set of strings. It is the type-system
# equivalent of a "label space" - fitting, given what this lesson is about.
Shape = Literal["classification", "regression", "clustering", "ranking", "generation"]

SHAPES: tuple[Shape, ...] = (
    "classification",
    "regression",
    "clustering",
    "ranking",
    "generation",
)


@dataclass(frozen=True)
class Request:
    """One business request, its correct shape, and why."""

    text: str
    shape: Shape
    note: str
    why: str


REQUESTS: list[Request] = [
    Request(
        "Is this email spam?",
        "classification", "binary",
        "Exactly two labels, fixed in advance. The simplest shape.",
    ),
    Request(
        "Route ticket to one of 4 teams",
        "classification", "multi-class",
        "One label from a fixed set of 4. Check that the teams really are "
        "mutually exclusive before committing to multi-class.",
    ),
    Request(
        "Tag article with any of 20 topics",
        "classification", "multi-label",
        "Several tags can be true at once. Modelling this as multi-class "
        "forces a false single choice - a very common and costly error.",
    ),
    Request(
        "Severity: low/medium/high/critical",
        "classification", "ordinal - watch",
        "Ordered categories. Multi-class ignores the ordering; regression "
        "assumes equal spacing. Start with a confusion matrix (M3-L14).",
    ),
    Request(
        "What will this house sell for?",
        "regression", "continuous",
        "A number on a continuous scale. Any value in range is allowed.",
    ),
    Request(
        "Minutes until food delivery arrives",
        "regression", "continuous",
        "Continuous and bounded below by zero.",
    ),
    Request(
        "How many support tickets tomorrow?",
        "regression", "count - awkward",
        "A count cannot be 43.7 or negative. Ordinary regression is fine at "
        "large values and behaves badly near zero.",
    ),
    Request(
        "Probability the customer churns",
        "regression", "bounded 0-1",
        "A bounded range is still regression. Note this is NOT the same as "
        "classifying churn yes/no - the output type differs.",
    ),
    Request(
        "Find natural customer groups (undefined)",
        "clustering", "no label space",
        "Nobody defined the groups in advance, so there is nothing to label "
        "against and no objective notion of correct.",
    ),
    Request(
        "Group log lines to discover error types",
        "clustering", "needs human read",
        "The algorithm proposes groups; a human must interpret them before "
        "they mean anything. It will always return groups.",
    ),
    Request(
        "Order search results by relevance",
        "ranking", "NOT classification",
        "The output is an ordering, not a label. Its metrics differ too: "
        "MRR and nDCG, not accuracy (M6-L13).",
    ),
    Request(
        "Which known issue does this match?",
        "ranking", "label space changes",
        "Looks like multi-class until you notice the issue list has thousands "
        "of entries and changes weekly. No fixed label space -> retrieval.",
    ),
    Request(
        "Write a reply to this ticket",
        "generation", "unbounded output",
        "Constructed content from a space too large to enumerate. Weakest "
        "evaluation story of any shape.",
    ),
    Request(
        "Summarise and categorise and reply",
        "generation", "3 TASKS - split it",
        "This is generation + classification + generation. Bundle for "
        "execution if you like, but SPLIT FOR EVALUATION or you cannot tell "
        "which part is broken.",
    ),
]


def show_table() -> None:
    print("TASK SHAPE REFERENCE TABLE")
    print("=" * 82)
    print(f"{'Request':<50} {'Shape':<15} {'Note'}")
    print("-" * 82)
    for r in REQUESTS:
        print(f"{r.text[:49]:<50} {r.shape:<15} {r.note}")
    print("=" * 82)
    counts = Counter(r.shape for r in REQUESTS)
    summary = "  ".join(f"{shape}={counts[shape]}" for shape in SHAPES)
    print(f"Counts: {summary}")


def run_drill() -> None:
    print("M1-L03 task shape drill")
    print("For each request, type the shape.\n")
    menu = "  ".join(f"[{i}] {s}" for i, s in enumerate(SHAPES, start=1))
    print(menu, "\n")

    score = 0
    for index, request in enumerate(REQUESTS, start=1):
        print(f"[{index}/{len(REQUESTS)}] {request.text}")
        raw = input("    shape (1-5 or name): ").strip().lower()

        if raw.isdigit() and 1 <= int(raw) <= len(SHAPES):
            answer = SHAPES[int(raw) - 1]
        else:
            answer = raw

        if answer == request.shape:
            score += 1
            print(f"    CORRECT ({request.note})")
        else:
            print(f"    WRONG - answer: {request.shape} ({request.note})")
        print(textwrap.fill(request.why, width=72,
                            initial_indent="    ", subsequent_indent="    "))
        print()

    print("=" * 60)
    print(f"Score: {score}/{len(REQUESTS)}")
    if score >= 12:
        print("Good. Move on to M1-L04.")
    else:
        print("Re-read section 5.1 (the four shapes side by side), then retry.")


def main() -> None:
    if "--show" in sys.argv:
        show_table()
        return
    try:
        run_drill()
    except (EOFError, KeyboardInterrupt):
        print("\nStopped. Run with --show to see the table.")


if __name__ == "__main__":
    main()
