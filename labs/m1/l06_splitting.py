"""M1-L06: four splitting strategies compared on synthetic ticket data.

    python3 labs/m1/l06_splitting.py

Shows why random splitting flatters a time-dependent model, and how grouping
and stratification change what you measure. Standard library only.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

SEED = 42
N_TICKETS = 3000
N_CUSTOMERS = 60


@dataclass(frozen=True)
class Ticket:
    ticket_id: int
    customer: str
    month: int          # 1..12
    body_len: int
    breached: int       # the label


def make_data() -> list[Ticket]:
    """Synthetic tickets with (a) a rising breach trend over the year and
    (b) repeated customers, so grouping matters."""
    rng = random.Random(SEED)
    tickets: list[Ticket] = []
    for i in range(N_TICKETS):
        # Customers are reused, so the same entity appears many times.
        customer = f"C{rng.randint(1, N_CUSTOMERS)}"
        month = rng.randint(1, 12)
        # DELIBERATE TIME TREND: breaches get much more likely later in the
        # year (a growing product outpacing its support team). A model that
        # trains on late months has an unfair edge when tested on early ones.
        breach_rate = 0.02 + 0.02 * month      # 0.04 in Jan -> 0.26 in Dec
        breached = 1 if rng.random() < breach_rate else 0
        tickets.append(Ticket(i, customer, month, rng.randint(50, 2000), breached))
    return tickets


# ---------------------------------------------------------------------------
# Splitting strategies
# ---------------------------------------------------------------------------
def split_random(rows: list[Ticket]) -> tuple[list[Ticket], list[Ticket]]:
    shuffled = list(rows)
    random.Random(SEED).shuffle(shuffled)
    cut = int(0.8 * len(shuffled))
    return shuffled[:cut], shuffled[cut:]


def split_stratified(rows: list[Ticket]) -> tuple[list[Ticket], list[Ticket]]:
    """Preserve the class ratio in both parts by splitting each class."""
    by_class: dict[int, list[Ticket]] = {}
    for row in rows:
        by_class.setdefault(row.breached, []).append(row)

    train: list[Ticket] = []
    test: list[Ticket] = []
    for label, group in sorted(by_class.items()):
        shuffled = list(group)
        random.Random(SEED + label).shuffle(shuffled)
        cut = int(0.8 * len(shuffled))
        train.extend(shuffled[:cut])
        test.extend(shuffled[cut:])
    return train, test


def split_grouped(rows: list[Ticket]) -> tuple[list[Ticket], list[Ticket]]:
    """Keep every ticket from one customer entirely on one side."""
    customers = sorted({row.customer for row in rows})
    random.Random(SEED).shuffle(customers)
    cut = int(0.8 * len(customers))
    train_customers = set(customers[:cut])
    train = [r for r in rows if r.customer in train_customers]
    test = [r for r in rows if r.customer not in train_customers]
    return train, test


def split_temporal(rows: list[Ticket]) -> tuple[list[Ticket], list[Ticket]]:
    """Train on the past, test on the future. Never shuffle first.

    Cut on a MONTH BOUNDARY, not at an arbitrary row index. Cutting mid-month
    puts the same month on both sides, which quietly reintroduces exactly the
    leakage a temporal split exists to prevent.
    """
    cutoff_month = 10          # train = months 1-9, test = months 10-12
    train = [r for r in rows if r.month < cutoff_month]
    test = [r for r in rows if r.month >= cutoff_month]
    return train, test


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------
def describe(name: str, train: list[Ticket], test: list[Ticket]) -> None:
    train_rate = sum(t.breached for t in train) / len(train)
    test_rate = sum(t.breached for t in test) / len(test)
    test_positives = sum(t.breached for t in test)

    train_customers = {t.customer for t in train}
    test_customers = {t.customer for t in test}
    overlap = train_customers & test_customers
    overlap_pct = 100 * len(overlap) / len(test_customers) if test_customers else 0.0

    train_months = sorted({t.month for t in train})
    test_months = sorted({t.month for t in test})

    print(f"{name}")
    print(f"  train n={len(train):<4} breach rate={train_rate:.3f}")
    print(f"  test  n={len(test):<4} breach rate={test_rate:.3f}  positives={test_positives}")
    print(f"  rate gap (test - train)        = {test_rate - train_rate:+.3f}")
    print(f"  test customers also in train   = {len(overlap)}/{len(test_customers)}"
          f" ({overlap_pct:.0f}%)")
    print(f"  train months={train_months}")
    print(f"  test  months={test_months}")
    print()


def main() -> None:
    rows = make_data()
    overall = sum(t.breached for t in rows) / len(rows)

    print("=" * 70)
    print("SPLITTING STRATEGIES COMPARED")
    print("=" * 70)
    print(f"Synthetic dataset: {len(rows)} tickets, {N_CUSTOMERS} customers, 12 months.")
    print(f"Overall breach rate: {overall:.3f}")
    print("Breach probability RISES sharply through the year (0.04 Jan -> 0.26 Dec).")
    print()

    describe("1. RANDOM (naive)", *split_random(rows))
    describe("2. STRATIFIED (preserves class ratio)", *split_stratified(rows))
    describe("3. GROUPED by customer", *split_grouped(rows))
    describe("4. TEMPORAL (past -> future)", *split_temporal(rows))

    # A trivial "model": predict the breach rate seen in training. This is the
    # baseline every project should have (M3-L14). Compare it to reality.
    print("-" * 70)
    print("WHAT A TRIVIAL MODEL WOULD PREDICT")
    print("-" * 70)
    print("Model: 'predict the training-set breach rate'. Compare to the truth.")
    print()
    print(f"{'strategy':<24}{'predicts':>10}{'actual':>10}{'error':>10}")
    for name, splitter in (
        ("random", split_random),
        ("stratified", split_stratified),
        ("grouped", split_grouped),
        ("temporal", split_temporal),
    ):
        tr, te = splitter(rows)
        predicted = sum(t.breached for t in tr) / len(tr)
        actual = sum(t.breached for t in te) / len(te)
        print(f"{name:<24}{predicted:>10.3f}{actual:>10.3f}{actual - predicted:>+10.3f}")
    print()

    print("-" * 70)
    print("HOW TO READ THIS")
    print("-" * 70)
    print("* Random and stratified splits mix months, so the test set looks")
    print("  like the training set. Their error is small and everything seems")
    print("  fine - but the model was allowed to learn from December while")
    print("  being tested on January. Production never works that way.")
    print()
    print("* The TEMPORAL split is the only one that reproduces the real")
    print("  problem. Breaches rise through the year, so a model fitted on")
    print("  months 1-9 systematically UNDER-predicts months 10-12. The error")
    print("  is several times larger than the random split suggested. That is")
    print("  the honest, uncomfortable number, and it is the one to trust.")
    print()
    print("* Note the temporal split is also UNBALANCED in size: months 1-9")
    print("  hold far more rows than 10-12. A time split gives you whatever")
    print("  proportion the calendar gives you, not a tidy 80/20.")
    print()
    print("* Customer overlap is ~100% for random/stratified/temporal: nearly")
    print("  every test customer was also seen in training, so those scores")
    print("  partly measure memorisation. Only the GROUPED split reports 0%")
    print("  overlap, and it is the only one answering 'how well will this")
    print("  work for a customer we have never seen?'")
    print()
    print("* Note also how FEW test customers the grouped split leaves (12).")
    print("  Grouping buys honesty and pays for it in statistical power.")
    print()
    print("* No single split is correct. The split must match the question")
    print("  you are actually asking. State which question you answered.")
    print("=" * 70)


if __name__ == "__main__":
    main()
