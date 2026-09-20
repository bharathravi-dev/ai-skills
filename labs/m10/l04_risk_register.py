"""M10-L04 lab -- a risk register is a ranking tool, and the ranking depends on
choices most registers never state. This lab scores ten AI risks and measures:

  1. likelihood x impact (the 5x5 matrix) against expected loss in money,
  2. how the ranking changes when the impact scale is linear rather than log,
  3. ties: how many genuinely different risks share one matrix score,
  4. inherent vs residual risk, and what happens when controls WITHOUT EVIDENCE
     are discounted,
  5. register completeness: which fields are missing from each entry.

Deterministic. No API key, no network, no third-party dependencies.
Run:  python labs/m10/l04_risk_register.py
"""

from __future__ import annotations

import sys
from dataclasses import dataclass

sys.stdout.reconfigure(encoding="utf-8")


def rule(title: str) -> None:
    print(f"\n{'=' * 76}\n{title}\n{'=' * 76}")


@dataclass
class Risk:
    id: str
    description: str
    likelihood: int          # 1..5 ordinal band
    impact: int              # 1..5 ordinal band
    annual_probability: float
    cost_if_it_happens: float   # GBP
    controls: tuple           # (name, claimed_reduction, evidenced)
    owner: str | None
    review_date: str | None
    acceptance: str | None


RISKS = [
    Risk("R1", "Assistant issues a refund above policy after prompt injection", 3, 4, 0.30, 25_000,
         (("Server-side limit in the refund tool", 0.9, True), ("Prompt says not to", 0.3, False)),
         "Support Platform", "2026-09-01", None),
    Risk("R2", "Personal data retained beyond the stated period", 4, 3, 0.60, 8_000,
         (("Retention job", 0.7, True),), "Privacy office", "2026-07-15", None),
    Risk("R3", "CV screening rejects one group at a higher rate", 2, 5, 0.20, 400_000,
         (("Subgroup evaluation before release", 0.5, False),), None, None, None),
    Risk("R4", "Provider deprecates the model with 30 days' notice", 4, 2, 0.50, 15_000,
         (("Provider abstraction layer", 0.6, True), ("Second provider tested quarterly", 0.5, False)),
         "Platform", "2026-08-20", "accepted by CTO"),
    Risk("R5", "Answer cites a policy clause that does not exist", 5, 2, 0.90, 3_000,
         (("Citation verification", 0.8, True),), "Applied science", "2026-08-30", None),
    Risk("R6", "Cross-tenant data leak through a shared cache", 1, 5, 0.05, 900_000,
         (("Tenant in cache key", 0.95, True), ("Isolation tests in CI", 0.8, True)),
         "Platform", "2026-09-05", None),
    Risk("R7", "Vendor changes data-retention terms unnoticed", 3, 3, 0.35, 20_000,
         (("Contract review on renewal", 0.4, False),), "Procurement", "2025-12-01", None),
    Risk("R8", "Agent loops and spends the monthly budget in a day", 3, 2, 0.40, 6_000,
         (("Step and cost limits", 0.9, True),), "Platform", "2026-09-01", "accepted by owner"),
    Risk("R9", "Evaluation set leaks into the prompt library", 2, 3, 0.15, 30_000,
         (("Separate repositories", 0.5, True),), None, "2026-06-10", None),
    Risk("R10", "Support agent pastes customer data into a public chatbot", 4, 4, 0.55, 120_000,
         (("Policy and training", 0.3, False), ("Egress monitoring", 0.6, True)),
         "Security", "2026-08-11", None),
]


def matrix(r: Risk) -> int:
    return r.likelihood * r.impact


def expected_loss(r: Risk) -> float:
    return r.annual_probability * r.cost_if_it_happens


def residual(r: Risk, require_evidence: bool) -> float:
    remaining = expected_loss(r)
    for _, reduction, evidenced in r.controls:
        if require_evidence and not evidenced:
            continue
        remaining *= (1 - reduction)
    return remaining


# ============================================================ 1
rule("1. MATRIX SCORE VS EXPECTED LOSS")

by_matrix = sorted(RISKS, key=lambda r: -matrix(r))
by_loss = sorted(RISKS, key=lambda r: -expected_loss(r))
print(f"  {'rank':<5}{'by 5x5 matrix':<34}{'by expected annual loss':<34}")
for i, (a, b) in enumerate(zip(by_matrix, by_loss), start=1):
    print(f"  {i:<5}{a.id + ' (' + str(matrix(a)) + ')':<34}{b.id + ' (GBP ' + format(round(expected_loss(b)), ',') + ')':<34}")
moved = sum(1 for i, (a, b) in enumerate(zip(by_matrix, by_loss)) if a.id != b.id)
print(f"\n  {moved}/{len(RISKS)} positions differ between the two rankings.")
top_matrix, top_loss = {r.id for r in by_matrix[:3]}, {r.id for r in by_loss[:3]}
print(f"  top 3 by matrix: {sorted(top_matrix)}   top 3 by expected loss: {sorted(top_loss)}")
print(f"  in one top 3 but not the other: {sorted(top_matrix ^ top_loss)}")


# ============================================================ 2
rule("2. THE SCALE CHANGES THE ANSWER")

LOG_IMPACT = {1: 1, 2: 10, 3: 100, 4: 1_000, 5: 10_000}      # each band ~10x the last
by_log = sorted(RISKS, key=lambda r: -(r.likelihood * LOG_IMPACT[r.impact]))
print("  rank   linear impact (1-5)      log impact (1,10,100,1k,10k)")
for i, (a, b) in enumerate(zip(by_matrix, by_log), start=1):
    print(f"  {i:<6} {a.id:<24} {b.id}")
changed = sum(1 for a, b in zip(by_matrix, by_log) if a.id != b.id)
print(f"\n  {changed}/{len(RISKS)} positions change when only the impact SCALE changes.")
print("  A 5x5 matrix multiplies two ordinal bands as if they were numbers. Whether")
print("  'catastrophic' is 5x 'minor' or 10,000x decides the order -- and registers")
print("  rarely say which they mean.")


# ============================================================ 3
rule("3. TIES: DIFFERENT RISKS, IDENTICAL SCORES")

buckets: dict[int, list[Risk]] = {}
for r in RISKS:
    buckets.setdefault(matrix(r), []).append(r)
print(f"  {len(RISKS)} risks occupy {len(buckets)} distinct matrix scores")
for score, group in sorted(buckets.items(), reverse=True):
    if len(group) > 1:
        print(f"    score {score:>2}: {', '.join(r.id for r in group)}")
        for r in group:
            print(f"        {r.id}  expected loss GBP {round(expected_loss(r)):>7,}   {r.description[:52]}")
print("\n  Two risks sharing a cell are not equally urgent: the matrix has thrown away")
print("  the information that would separate them.")


# ============================================================ 4
rule("4. INHERENT VS RESIDUAL -- AND CONTROLS WITHOUT EVIDENCE")

APPETITE = 5_000.0        # the most expected annual loss the owner accepts per risk
rows = []
for r in RISKS:
    rows.append((r, expected_loss(r), residual(r, require_evidence=False), residual(r, require_evidence=True)))
print(f"  appetite: GBP {APPETITE:,.0f} expected annual loss per risk\n")
print(f"  {'risk':<5}{'inherent':>12}{'residual (claimed)':>22}{'residual (evidenced only)':>28}")
for r, inherent, claimed, evidenced in rows:
    flag = "" if evidenced <= APPETITE else "   OVER APPETITE"
    print(f"  {r.id:<5}{round(inherent):>12,}{round(claimed):>22,}{round(evidenced):>28,}{flag}")
over_claimed = sum(1 for _, _, c, _ in rows if c > APPETITE)
over_evidenced = sum(1 for _, _, _, e in rows if e > APPETITE)
rose = [r.id for r, _, c, e in rows if e > c]
print(f"\n  over appetite counting every claimed control : {over_claimed}/{len(RISKS)}")
print(f"  over appetite counting only EVIDENCED controls: {over_evidenced}/{len(RISKS)}")
print(f"  residual rose for {len(rose)} risk(s) when unevidenced controls were discounted: {', '.join(rose)}")
print(f"  and that pushed {over_evidenced - over_claimed} of them back over the appetite line.")
print("\n  'Policy and training' and 'prompt says not to' are the usual unevidenced")
print("  controls. Until a test, log or record shows a control working, a register")
print("  that counts it is reporting an intention as a reduction (M10-L01).")


# ============================================================ 5
rule("5. REGISTER COMPLETENESS")

for r in RISKS:
    gaps = []
    if r.owner is None:
        gaps.append("no owner")
    if r.review_date is None:
        gaps.append("no review date")
    elif r.review_date < "2026-06-01":
        gaps.append(f"last reviewed {r.review_date}")
    if not any(evidenced for _, _, evidenced in r.controls):
        gaps.append("no evidenced control")
    if residual(r, True) > APPETITE and r.acceptance is None:
        gaps.append("over appetite with no recorded acceptance")
    print(f"  {r.id:<5}{'OK' if not gaps else '; '.join(gaps)}")
print("\n  A register entry that is over appetite with nobody accepting it is not a")
print("  decision -- it is an unanswered question sitting in a spreadsheet.")


rule("6. WHAT THIS LAB IS AND IS NOT")
print("  REAL: every ranking, tie, residual figure and count above is computed from")
print("  the ten encoded risks.")
print("\n  ILLUSTRATIVE: the probabilities, costs and control effectiveness figures are")
print("  invented. Real registers face the harder problem that these numbers are")
print("  estimates -- which is why the lesson argues for stating ranges and assumptions")
print("  rather than pretending a single score is precise.")
print("\n  NOT SHOWN: correlated risks (one incident triggering several), risks to")
print("  people rather than to the organisation, and the frameworks that prescribe")
print("  particular scales (M10-L16).")
print("\nDone.")
