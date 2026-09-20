"""M10-L11 lab -- choosing a model provider or vendor. Measures:

  1. weighted scoring vs must-pass gates: the supplier that wins on points and
     fails a requirement,
  2. how much the ranking depends on the weights you happened to choose,
  3. list price vs total cost once volume and the obvious extras are included,
  4. lock-in: how much provider-specific surface a design uses,
  5. staleness: which assessments no longer describe the supplier.

All prices and scores are ILLUSTRATIVE and invented for this lab.
Deterministic. No API key, no network, no third-party dependencies.
Run:  python labs/m10/l11_supplier_assessment.py
"""

from __future__ import annotations

import itertools
import sys

sys.stdout.reconfigure(encoding="utf-8")


def rule(title: str) -> None:
    print(f"\n{'=' * 76}\n{title}\n{'=' * 76}")


# scores are 0-5 on each criterion; gates are pass/fail facts, not scores
SUPPLIERS = {
    "Provider A (frontier, US)": {"quality": 5, "latency": 4, "support": 4, "roadmap": 5,
                                  "gates": {"data_not_used_for_training": True, "eu_region_available": False,
                                            "sub_processor_list": True, "deletion_sla_30d": False}},
    "Provider B (frontier, EU region)": {"quality": 4, "latency": 4, "support": 3, "roadmap": 4,
                                         "gates": {"data_not_used_for_training": True, "eu_region_available": True,
                                                   "sub_processor_list": True, "deletion_sla_30d": True}},
    "Provider C (cheap, new)": {"quality": 3, "latency": 5, "support": 2, "roadmap": 2,
                                "gates": {"data_not_used_for_training": False, "eu_region_available": True,
                                          "sub_processor_list": False, "deletion_sla_30d": False}},
    "Provider D (self-hosted open weights)": {"quality": 3, "latency": 3, "support": 1, "roadmap": 3,
                                              "gates": {"data_not_used_for_training": True, "eu_region_available": True,
                                                        "sub_processor_list": True, "deletion_sla_30d": True}},
    "Provider E (incumbent vendor add-on)": {"quality": 3, "latency": 3, "support": 5, "roadmap": 3,
                                             "gates": {"data_not_used_for_training": True, "eu_region_available": True,
                                                       "sub_processor_list": True, "deletion_sla_30d": False}},
}
WEIGHTS = {"quality": 0.45, "latency": 0.20, "support": 0.20, "roadmap": 0.15}
MUST_PASS = ["data_not_used_for_training", "eu_region_available", "deletion_sla_30d"]


def score(name: str, weights=WEIGHTS) -> float:
    s = SUPPLIERS[name]
    return sum(s[c] * w for c, w in weights.items())


def gate_failures(name: str) -> list[str]:
    return [g for g in MUST_PASS if not SUPPLIERS[name]["gates"].get(g)]


# ============================================================ 1
rule("1. WEIGHTED SCORE VS MUST-PASS REQUIREMENTS")

ranked = sorted(SUPPLIERS, key=lambda n: -score(n))
print(f"  {'rank':<5}{'supplier':<40}{'weighted score':>15}   must-pass failures")
for i, name in enumerate(ranked, start=1):
    fails = gate_failures(name)
    print(f"  {i:<5}{name:<40}{score(name):>15.2f}   {', '.join(fails) if fails else 'none'}")
eligible = [n for n in ranked if not gate_failures(n)]
print(f"\n  ranking by score alone puts '{ranked[0]}' first; it fails "
      f"{len(gate_failures(ranked[0]))} must-pass requirement(s).")
print(f"  eligible suppliers after gates: {len(eligible)}/{len(SUPPLIERS)} -> best eligible: '{eligible[0]}'")
print("  A weighted average lets a strong score on quality pay for a failed requirement")
print("  about data handling. Gates are answered yes/no BEFORE any scoring.")


# ============================================================ 2
rule("2. HOW MUCH DOES THE RANKING DEPEND ON THE WEIGHTS?")

variants = {
    "as chosen": WEIGHTS,
    "quality-led": {"quality": 0.60, "latency": 0.15, "support": 0.15, "roadmap": 0.10},
    "operations-led": {"quality": 0.30, "latency": 0.25, "support": 0.35, "roadmap": 0.10},
    "equal weights": {c: 0.25 for c in WEIGHTS},
}
orders = {}
for label, w in variants.items():
    order = sorted(SUPPLIERS, key=lambda n: -score(n, w))
    orders[label] = order
    print(f"  {label:<16} {' > '.join(n.split(' (')[0] for n in order)}")
first_places = {orders[l][0] for l in orders}
base = orders["as chosen"]
moved = {l: sum(1 for a, b in zip(base, o) if a != b) for l, o in orders.items() if l != "as chosen"}
print(f"\n  distinct suppliers ranked first across four weightings: {len(first_places)}")
print(f"  positions that move relative to the chosen weighting: "
      f"{', '.join(f'{l}: {n}' for l, n in moved.items())}")
print("  Here the top choice is stable and only places 2-3 swap, which is a useful")
print("  thing to have checked rather than assumed. When a plausible reweighting DOES")
print("  change the winner, the weights are deciding rather than the evidence -- and a")
print("  short-list plus an explicit trade-off conversation is the honest alternative.")


# ============================================================ 3
rule("3. LIST PRICE VS TOTAL COST  [ILLUSTRATIVE FIGURES]")

MONTHLY_TOKENS_M = 40        # millions of tokens per month
COSTS = {   # GBP; invented for this lab
    "Provider A (frontier, US)": {"per_m_tokens": 7.0, "support_tier": 1500, "egress": 0, "engineering": 0},
    "Provider B (frontier, EU region)": {"per_m_tokens": 8.0, "support_tier": 0, "egress": 0, "engineering": 0},
    "Provider C (cheap, new)": {"per_m_tokens": 2.0, "support_tier": 0, "egress": 0, "engineering": 2500},
    "Provider D (self-hosted open weights)": {"per_m_tokens": 0.0, "support_tier": 0, "egress": 400,
                                              "engineering": 9000},
    "Provider E (incumbent vendor add-on)": {"per_m_tokens": 11.0, "support_tier": 0, "egress": 0, "engineering": 0},
}
print(f"  at {MONTHLY_TOKENS_M}M tokens/month\n")
print(f"  {'supplier':<40}{'tokens':>10}{'other':>10}{'total/mo':>12}")
totals = {}
for name, c in COSTS.items():
    tokens = c["per_m_tokens"] * MONTHLY_TOKENS_M
    other = c["support_tier"] + c["egress"] + c["engineering"]
    totals[name] = tokens + other
    print(f"  {name:<40}{tokens:>10,.0f}{other:>10,.0f}{totals[name]:>12,.0f}")
by_list = sorted(COSTS, key=lambda n: COSTS[n]["per_m_tokens"])
by_total = sorted(totals, key=lambda n: totals[n])
print(f"\n  cheapest by list price : {by_list[0].split(' (')[0]}")
print(f"  cheapest by total cost : {by_total[0].split(' (')[0]}")
print(f"  positions that differ between the two orderings: "
      f"{sum(1 for a, b in zip(by_list, by_total) if a != b)}/{len(COSTS)}")
print("  Self-hosting trades price per token for engineering time; a cheap provider")
print("  that needs its own integration is not cheap at this volume (M4-L18, M12-L14).")


# ============================================================ 4
rule("4. LOCK-IN: HOW MUCH PROVIDER-SPECIFIC SURFACE DOES THE DESIGN USE?")

FEATURES = {
    "chat completion with system prompt": False,
    "tool calling (JSON schema)": False,
    "structured output constrained decoding": True,
    "provider-hosted vector store": True,
    "provider-specific caching header": True,
    "fine-tuned model on provider": True,
    "batch API with provider queue": True,
    "provider-specific safety filters config": True,
}
DESIGNS = {
    "portable design": ["chat completion with system prompt", "tool calling (JSON schema)"],
    "convenient design": ["chat completion with system prompt", "tool calling (JSON schema)",
                          "structured output constrained decoding", "provider-hosted vector store",
                          "provider-specific caching header"],
    "all-in design": list(FEATURES),
}
for label, used in DESIGNS.items():
    specific = [f for f in used if FEATURES[f]]
    print(f"  {label:<20} uses {len(used)} features, {len(specific)} provider-specific: "
          f"{', '.join(f.split(' (')[0] for f in specific) or 'none'}")
print("\n  Switching cost is not a number in a contract; it is the count of things you")
print("  would have to rebuild. Decide deliberately which provider-specific features")
print("  are worth the lock-in, and keep an abstraction at the call site (M5-L17).")


# ============================================================ 5
rule("5. IS THE ASSESSMENT STILL TRUE?")

ASSESSMENTS = {
    "Provider A (frontier, US)": {"assessed": "2026-01-10", "events": ["terms updated 2026-06", "model deprecated 2026-08"]},
    "Provider B (frontier, EU region)": {"assessed": "2026-08-20", "events": []},
    "Provider C (cheap, new)": {"assessed": "2025-11-02", "events": ["security incident 2026-03", "acquired 2026-07"]},
    "Provider D (self-hosted open weights)": {"assessed": "2026-07-01", "events": ["licence change 2026-09"]},
    "Provider E (incumbent vendor add-on)": {"assessed": "2026-02-14", "events": ["sub-processor added 2026-05"]},
}
STALE_BEFORE = "2026-06-01"
for name, a in ASSESSMENTS.items():
    reasons = []
    if a["assessed"] < STALE_BEFORE:
        reasons.append(f"assessed {a['assessed']}")
    reasons += a["events"]
    print(f"  {name:<40} {'RE-ASSESS: ' + '; '.join(reasons) if reasons else 'current'}")
due = sum(1 for a in ASSESSMENTS.values() if a["assessed"] < STALE_BEFORE or a["events"])
print(f"\n  {due}/{len(ASSESSMENTS)} suppliers need re-assessment.")
print("  Supplier assessment is not a purchase-time activity: terms change, models are")
print("  deprecated, companies are acquired, and licences are revised (M10-L14).")


rule("6. WHAT THIS LAB IS AND IS NOT")
print("  REAL: every ranking, sensitivity count, total and lock-in count above is")
print("  computed from the encoded scores, prices and feature lists.")
print("\n  ILLUSTRATIVE: the suppliers are fictional and every price and score is")
print("  invented. Real assessments use the supplier's own documentation, contracts,")
print("  security reports and your measured results (M5-L18, M10-L12).")
print("\n  NOT SHOWN: contract negotiation, procurement process, and jurisdiction-specific")
print("  obligations for processors and sub-processors (M10-L16).")
print("\nDone.")
