"""M11-L06 lab -- an alert is a notification, not a brake.
This lab computes:

  1. what a runaway costs before the budget alert fires and before anyone acts,
  2. which mechanisms are actual CAPS, and what each one costs you when it bites,
  3. how much of the bill is attributable at different tag-coverage levels,
  4. unit economics: cost per request, and what 10x traffic does to it,
  5. where the money actually goes in an AI workload.

Deterministic. No AWS account, no network, no third-party dependencies.
Run:  python labs/m11/l06_billing_budgets_cost.py
"""

from __future__ import annotations

import sys

sys.stdout.reconfigure(encoding="utf-8")


def rule(title: str) -> None:
    print(f"\n{'=' * 76}\n{title}\n{'=' * 76}")


# ============================================================ 1
rule("1. WHAT A RUNAWAY COSTS BEFORE THE ALERT FIRES")

BURN_PER_HOUR = 640.0     # USD/h once the retry loop starts [ILLUSTRATIVE]
STAGES = [
    ("usage is metered and reaches billing data", 6),
    ("the budget evaluates and the alert is sent", 4),
    ("someone reads the alert (out of hours)", 8),
    ("someone works out what is spending", 2),
    ("the change is made and takes effect", 1),
]
print(f"  a retry loop starts burning ${BURN_PER_HOUR:,.0f}/hour at 23:00 on a Friday\n")
print(f"  {'stage':<46}{'hours':>7}{'cumulative':>12}{'spent':>12}")
cum = 0.0
for label, hrs in STAGES:
    cum += hrs
    print(f"  {label:<46}{hrs:>7}{cum:>11.0f} h{BURN_PER_HOUR * cum:>12,.0f}")
print(f"\n  total before it stops: {cum:.0f} hours, ${BURN_PER_HOUR * cum:,.0f}")
print(f"  the alert itself accounted for {STAGES[0][1] + STAGES[1][1]} of those hours -- billing data lags,")
print("  and budgets evaluate periodically. A budget alert tells you about money you")
print("  have ALREADY spent. It is a smoke detector, not a sprinkler.")


# ============================================================ 2
rule("2. WHAT ACTUALLY CAPS SPEND?")

MECHANISMS = [
    # name,                                  caps?, latency,      what it costs you when it bites
    ("budget alert (email/SNS)",             False, "hours",      "nothing -- it only notifies"),
    ("cost anomaly detection",               False, "hours",      "nothing -- it only notifies"),
    ("service quotas / account limits",      True,  "immediate",  "requests fail; legitimate load fails too"),
    ("Lambda reserved concurrency",          True,  "immediate",  "throttling; queue backs up"),
    ("provisioned capacity instead of on-demand", True, "immediate", "queuing or rejection at the cap"),
    ("max_tokens and step limits in the app", True, "immediate",  "truncated or abandoned work (M8-L15)"),
    ("SCP denying expensive instance types", True,  "immediate",  "deploys fail until reviewed (M11-L03)"),
    ("automated shutdown on a budget action", True, "hours",      "the environment stops; data may be lost"),
    ("a rate limiter in front of the model",  True, "immediate",  "users are queued or rejected"),
]
caps = [m for m in MECHANISMS if m[1]]
print(f"  {'mechanism':<44}{'caps?':>7}{'latency':>12}   what it costs when it bites")
for name, cap, lat, cost in MECHANISMS:
    print(f"  {name:<44}{('CAP' if cap else 'alert'):>7}{lat:>12}   {cost}")
print(f"\n  real caps: {len(caps)}/{len(MECHANISMS)}")
print("  Every genuine cap breaks something on purpose. That is what makes it a cap.")
print("  Choose which failure you prefer BEFORE the Friday night, and put the cheap")
print("  ones (max_tokens, step limits, concurrency) in from day one (M8-L15).")


# ============================================================ 3
rule("3. CAN YOU EVEN TELL WHOSE SPEND IT IS?")

MONTHLY = 84_000
for coverage in (0.30, 0.60, 0.85, 0.97, 1.00):
    attributable = MONTHLY * coverage
    print(f"  tag coverage {coverage:>5.0%} -> ${attributable:>9,.0f} attributable, "
          f"${MONTHLY - attributable:>8,.0f} unattributable "
          f"({'usable for chargeback' if coverage >= 0.95 else 'arguments at the review'})")
print("\n  Untagged spend is not a reporting inconvenience: it is the part of the bill")
print("  nobody will reduce, because nobody owns it. Enforce tags at creation with")
print("  a tag policy and an SCP, not with a spreadsheet afterwards.")
print("  Minimum useful tag set: owner, environment, service, cost-centre, data-class.")


# ============================================================ 4
rule("4. UNIT ECONOMICS OF ONE AI FEATURE  [ILLUSTRATIVE RATES]")

PER_REQUEST = {
    "model input tokens (2,400 @ $3/M)":   0.0072,
    "model output tokens (400 @ $15/M)":   0.0060,
    "embedding of the query":              0.0001,
    "vector search":                       0.0004,
    "reranking":                           0.0011,
    "compute (app, 300 ms)":               0.0002,
    "logging and storage":                 0.0003,
    "data transfer":                       0.0001,
}
unit = sum(PER_REQUEST.values())
print(f"  {'component':<38}{'USD/request':>14}{'share':>9}")
for name, cost in sorted(PER_REQUEST.items(), key=lambda kv: -kv[1]):
    print(f"  {name:<38}{cost:>14.4f}{cost / unit:>9.0%}")
print(f"  {'TOTAL':<38}{unit:>14.4f}{1:>9.0%}")
print()
for rpd in (1_000, 10_000, 100_000, 1_000_000):
    print(f"  {rpd:>9,} requests/day -> ${unit * rpd:>10,.0f}/day   ${unit * rpd * 30:>12,.0f}/month")
model_share = (PER_REQUEST["model input tokens (2,400 @ $3/M)"]
               + PER_REQUEST["model output tokens (400 @ $15/M)"]) / unit
print(f"\n  the model is {model_share:.0%} of the unit cost, so that is where optimisation pays:")
print("  shorter context, fewer retrieved chunks, caching, a smaller model for easy")
print("  cases (M5-L15, M5-L16, M13-L08). Halving retrieved context here saves more")
print("  than every infrastructure line added together.")


# ============================================================ 5
rule("5. WHERE THE MONEY ACTUALLY GOES  [ILLUSTRATIVE MONTHLY BILL]")

BILL = {
    "model inference":            38_400,
    "vector store / database":     9_200,
    "compute (containers)":        7_800,
    "NAT gateway + data transfer": 4_100,
    "object storage":              2_600,
    "logging and observability":   6_900,
    "non-production environments": 9_800,
    "idle / forgotten resources":  5_200,
}
total = sum(BILL.values())
print(f"  {'line':<34}{'USD/month':>12}{'share':>9}   note")
NOTES = {
    "NAT gateway + data transfer": "often replaceable by VPC endpoints (M11-L08)",
    "logging and observability":   "sampling and retention are levers (M11-L16)",
    "non-production environments": "schedule them off outside working hours",
    "idle / forgotten resources":  "nobody's, because nothing is tagged (section 3)",
    "model inference":             "the unit-economics lever (section 4)",
}
for name, amount in sorted(BILL.items(), key=lambda kv: -kv[1]):
    print(f"  {name:<34}{amount:>12,}{amount / total:>9.0%}   {NOTES.get(name, '')}")
print(f"  {'TOTAL':<34}{total:>12,}{1:>9.0%}")
waste = BILL["idle / forgotten resources"] + BILL["non-production environments"] * 0.6
print(f"\n  plausibly recoverable without touching the product: ${waste:,.0f}/month "
      f"({waste / total:.0%})")
nonprod_share = (BILL["non-production environments"] + BILL["idle / forgotten resources"]) / total
print(f"  non-production and idle resources alone are {nonprod_share:.0%} of the bill and serve no")
print("  user. Look at the bill itemised at least monthly; the surprises are never in")
print("  the line you expect.")


rule("6. WHAT THIS LAB IS AND IS NOT")
print("  REAL: every total, share, cap classification and projection above is")
print("  computed from the values in this script.")
print("\n  ILLUSTRATIVE: every rate, burn figure, lag and bill line is invented, though")
print("  the SHAPE (model dominates unit cost; NAT and logging are quietly large;")
print("  non-production and idle resources are recoverable) is the common one.")
print("\n  NOT SHOWN: Reserved Instances and Savings Plans, Cost Explorer itself,")
print("  consolidated billing mechanics, and negotiated pricing (M12-L14).")
print("\nDone.")
