"""M1-L09: build a 100%-accurate useless model, then catch it with an audit.

    python3 labs/m1/l09_leakage.py

Standard library only. The classifier is a tiny decision stump / Naive Bayes
hybrid kept deliberately simple so the leakage, not the model, is the subject.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, replace

SEED = 11
N = 600


@dataclass(frozen=True)
class Ticket:
    channel: str
    body_len: int
    priority: str          # set at creation, but agents RAISE it when escalating
    assigned_team: str     # 'tier2' IS how escalation is recorded  -> leaky
    escalation_note: str   # only ever populated when escalated     -> leaky
    escalated: int         # the label


def make_data() -> list[Ticket]:
    """Synthetic tickets. Escalation genuinely depends (weakly) on channel,
    body length and creation priority - and is PERFECTLY recorded by the two
    leaky fields."""
    rng = random.Random(SEED)
    rows: list[Ticket] = []
    for _ in range(N):
        channel = rng.choice(["email", "chat", "phone"])
        body_len = rng.randint(50, 2000)
        creation_priority = rng.choices(
            ["low", "medium", "high"], weights=[5, 3, 2]
        )[0]

        # The REAL (moderate) signal available at creation time. Kept
        # deliberately imperfect: real escalation depends on things no field
        # captures. Base rate is near 40% so that plain accuracy stays a
        # meaningful metric for this lesson (M3-L14 covers imbalance).
        score = 0.12
        score += 0.30 if creation_priority == "high" else 0.0
        score += 0.20 if channel == "phone" else 0.0
        score += 0.22 if body_len > 1200 else 0.0
        escalated = 1 if rng.random() < score else 0

        # Fields that only get their values AFTER the outcome.
        if escalated:
            assigned_team = "tier2"
            note = rng.choice(["customer VIP", "SLA risk", "repeat issue"])
            # Agents also bump priority as part of escalating.
            priority = "high"
        else:
            assigned_team = "tier1"
            note = ""
            priority = creation_priority

        rows.append(Ticket(channel, body_len, priority, assigned_team, note, escalated))
    return rows


def production_row(t: Ticket) -> Ticket:
    """Rebuild a ticket AS IT LOOKS AT PREDICTION TIME.

    At creation there is no escalation note, no tier2 assignment, and priority
    has not yet been bumped. Almost nobody runs this check, and it is the one
    that exposes target leakage immediately.
    """
    return replace(t, assigned_team="tier1", escalation_note="", priority="unknown")


# ---------------------------------------------------------------------------
# Feature extraction: two variants
# ---------------------------------------------------------------------------
def features_leaky(t: Ticket) -> dict[str, float]:
    return {
        "ch_phone": 1.0 if t.channel == "phone" else 0.0,
        "long_body": 1.0 if t.body_len > 1200 else 0.0,
        "prio_high": 1.0 if t.priority == "high" else 0.0,
        "team_tier2": 1.0 if t.assigned_team == "tier2" else 0.0,   # LEAK
        "has_note": 1.0 if t.escalation_note else 0.0,              # LEAK
    }


def features_honest(t: Ticket) -> dict[str, float]:
    return {
        "ch_phone": 1.0 if t.channel == "phone" else 0.0,
        "long_body": 1.0 if t.body_len > 1200 else 0.0,
    }


# ---------------------------------------------------------------------------
# A minimal classifier: score = sum of per-feature log-odds. Enough to expose
# leakage without introducing a library.
# ---------------------------------------------------------------------------
class SimpleModel:
    """Bernoulli Naive Bayes over binary features.

    Compares log P(y=1) + sum log P(f_i | y=1) against the same for y=0,
    accounting for features that are ABSENT as well as present. Kept small and
    explicit so the leakage, not the model, is the subject of the lesson.
    """

    def __init__(self) -> None:
        self.p_present: dict[str, tuple[float, float]] = {}   # name -> (P(f|1), P(f|0))
        self.log_prior_pos: float = 0.0
        self.log_prior_neg: float = 0.0

    def train(self, rows: list[Ticket], featurizer) -> None:
        pos = [r for r in rows if r.escalated == 1]
        neg = [r for r in rows if r.escalated == 0]
        self.log_prior_pos = math.log(len(pos) / len(rows))
        self.log_prior_neg = math.log(len(neg) / len(rows))

        for name in featurizer(rows[0]):
            # Laplace smoothing, exactly as in M1-L02.
            p1 = (sum(featurizer(r)[name] for r in pos) + 1) / (len(pos) + 2)
            p0 = (sum(featurizer(r)[name] for r in neg) + 1) / (len(neg) + 2)
            self.p_present[name] = (p1, p0)

    def predict(self, t: Ticket, featurizer) -> int:
        f = featurizer(t)
        score_pos, score_neg = self.log_prior_pos, self.log_prior_neg
        for name, (p1, p0) in self.p_present.items():
            if f[name] > 0.5:
                score_pos += math.log(p1)
                score_neg += math.log(p0)
            else:
                score_pos += math.log(1 - p1)
                score_neg += math.log(1 - p0)
        return 1 if score_pos > score_neg else 0


def accuracy(model: SimpleModel, rows: list[Ticket], featurizer) -> float:
    correct = sum(1 for r in rows if model.predict(r, featurizer) == r.escalated)
    return correct / len(rows)


def single_feature_accuracy(rows: list[Ticket], featurizer, name: str) -> float:
    """AUDIT STEP 2: how well does this ONE feature predict the label alone?"""
    correct = 0
    for r in rows:
        guess = 1 if featurizer(r)[name] > 0.5 else 0
        if guess == r.escalated:
            correct += 1
    direct = correct / len(rows)
    return max(direct, 1 - direct)     # allow for an inverted relationship


def main() -> None:
    rows = make_data()
    rng = random.Random(SEED)
    shuffled = list(rows)
    rng.shuffle(shuffled)
    cut1, cut2 = int(0.6 * N), int(0.8 * N)
    train, val, test = shuffled[:cut1], shuffled[cut1:cut2], shuffled[cut2:]

    base_rate = sum(r.escalated for r in rows) / len(rows)

    print("=" * 72)
    print("DATA LEAKAGE: a model with perfect scores and no value")
    print("=" * 72)
    print(f"{N} synthetic tickets. Escalation base rate: {base_rate:.1%}")
    print(f"Splits: train={len(train)} val={len(val)} test={len(test)}")
    print()

    # --- The leaky model -----------------------------------------------------
    leaky = SimpleModel()
    leaky.train(train, features_leaky)
    print("MODEL A - includes 'assigned_team' and 'escalation_note'")
    print(f"  train accuracy      : {accuracy(leaky, train, features_leaky):.1%}")
    print(f"  validation accuracy : {accuracy(leaky, val, features_leaky):.1%}")
    print(f"  test accuracy       : {accuracy(leaky, test, features_leaky):.1%}")
    print()
    print("  Every split looks perfect. The M1-L08 diagnostic says 'good fit':")
    print("  training and validation agree, so there is no generalization gap.")
    print("  Nothing here looks wrong.")
    print()

    # --- The same model on production-shaped rows ---------------------------
    prod_test = [production_row(t) for t in test]
    prod_acc = accuracy(leaky, prod_test, features_leaky)
    always_no = sum(1 for r in test if r.escalated == 0) / len(test)
    print("  NOW: the same test rows, as they actually look at prediction time")
    print("  (no note yet, no tier2 assignment yet, priority not yet raised):")
    print(f"  production accuracy : {prod_acc:.1%}")
    print(f"  'always predict no' : {always_no:.1%}   <- the do-nothing baseline")
    print()
    print("  The model has collapsed to the baseline. It learned to read a")
    print("  field that records the answer, and that field is empty when the")
    print("  prediction is actually needed.")
    print()

    # --- The honest model ----------------------------------------------------
    honest = SimpleModel()
    honest.train(train, features_honest)
    print("MODEL B - only features available at ticket creation")
    print(f"  train accuracy      : {accuracy(honest, train, features_honest):.1%}")
    print(f"  test accuracy       : {accuracy(honest, test, features_honest):.1%}")
    print(f"  'always predict no' : {always_no:.1%}")
    print()

    # --- The audit -----------------------------------------------------------
    print("-" * 72)
    print("LEAKAGE AUDIT")
    print("-" * 72)

    print("Step 2 - single-feature predictive power (an alarm above ~0.90):")
    for name in features_leaky(rows[0]):
        acc = single_feature_accuracy(rows, features_leaky, name)
        flag = "   <-- ALARM: investigate this field" if acc > 0.90 else ""
        print(f"    {name:<12} {acc:.1%}{flag}")
    print()

    print("Step 3 - split integrity (identical rows appearing in two splits):")
    def keys(rs): return {hash((r.channel, r.body_len, r.priority, r.escalated)) for r in rs}
    overlap = keys(train) & keys(test)
    print(f"    train/test overlapping rows: {len(overlap)}")
    print()

    print("Step 8 - sanity check:")
    print(f"    reported test accuracy = {accuracy(leaky, test, features_leaky):.1%}")
    print("    Is near-perfect accuracy plausible for predicting human")
    print("    escalation decisions from a ticket at creation time? No.")
    print("    Treat it as a bug report until explained.")
    print()

    print("-" * 72)
    print("THE LESSON")
    print("-" * 72)
    print("* Model A scored perfectly on train, validation AND test. Every")
    print("  standard check passed. The generalization gap was zero.")
    print()
    print("* Model A is worthless. Model B, which looks much worse, is the")
    print("  one that works.")
    print()
    print("* No split strategy would have caught this. Leakage is a DATA")
    print("  problem, and it is found by auditing where each field comes")
    print("  from and when it is populated - not by better validation.")
    print()
    print("* The decisive check was rebuilding test rows as they look at")
    print("  prediction time. Run it on every project.")
    print("=" * 72)


if __name__ == "__main__":
    main()
