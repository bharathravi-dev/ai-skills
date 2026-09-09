"""M4-L18 lab -- hosted vs local: the arithmetic behind the decision.

Reproduces the lesson's break-even calculation, models utilisation's effect,
demonstrates why a bursty workload cannot reach break-even, and scores the
seven-axis decision.

Pure arithmetic. NOTHING IS PROVISIONED. No API key, no network, no cloud
resources, no cost. All prices are ILLUSTRATIVE, dated 2026-09-09, and must be
replaced with current figures before any real decision.

Run:  python labs/m4/l18_hosted_vs_local.py
"""

from __future__ import annotations

import numpy as np

RNG = np.random.default_rng(18)
HOURS_PER_MONTH = 730


def rule(title: str) -> None:
    print(f"\n{'=' * 76}\n{title}\n{'=' * 76}")


# ---- ILLUSTRATIVE RATES. Not quotes. Replace before deciding anything. ----
IN_PRICE = 0.50 / 1_000_000        # $/input token
OUT_PRICE = 1.50 / 1_000_000       # $/output token
GPU_HOURLY = 2.00                  # $/accelerator-hour
FTE_MONTHLY = 120_000 / 12         # fully-loaded engineer cost


def hosted_cost(requests, in_tok=2000, out_tok=400):
    return requests * (in_tok * IN_PRICE + out_tok * OUT_PRICE)


def selfhost_cost(instances=1, fte=0.0, hourly=GPU_HOURLY):
    return instances * hourly * HOURS_PER_MONTH + fte * FTE_MONTHLY


rule("1. THE NAIVE COMPARISON  (and why it is wrong)")

REQ = 500_000
print(f"  {REQ:,} requests/month, 2,000 input + 400 output tokens each")
print(f"  ILLUSTRATIVE rates: ${IN_PRICE * 1e6:.2f}/M in, "
      f"${OUT_PRICE * 1e6:.2f}/M out, ${GPU_HOURLY:.2f}/GPU-hour\n")

h = hosted_cost(REQ)
print(f"  {'option':<44}{'$/month':>12}")
print(f"  {'hosted':<44}{h:>12,.0f}")
print(f"  {'self-hosted, 1 instance (the naive figure)':<44}"
      f"{selfhost_cost(1):>12,.0f}")
print(f"\n  Hosted already wins, before anything else is counted.")

print(f"\n  making the self-hosted figure honest:")
rows = [
    ("1 instance", selfhost_cost(1), "not a production deployment"),
    ("+ redundancy (2 instances)", selfhost_cost(2), "one instance is a single point of failure"),
    ("+ peak provisioning (4 total)", selfhost_cost(4), "sized for peak, paid at average"),
    ("+ 0.25 FTE engineering", selfhost_cost(4, 0.25), "usually the largest line"),
]
for label, cost, note in rows:
    print(f"  {label:<44}{cost:>12,.0f}   {note}")

realistic = selfhost_cost(4, 0.25)
print(f"\n  realistic self-hosted : ${realistic:,.0f}/month")
print(f"  hosted                : ${h:,.0f}/month")
print(f"  self-hosting is {realistic / h:.0f}x MORE expensive at this volume.")


rule("2. WHERE IS THE ACTUAL BREAK-EVEN?")

per_req = hosted_cost(1)
breakeven = realistic / per_req
print(f"  hosted cost per request : ${per_req:.6f}")
print(f"  self-hosted fixed cost  : ${realistic:,.0f}/month")
print(f"  break-even              : {breakeven:,.0f} requests/month")
print(f"                          = {breakeven / REQ:.1f}x the current volume")

print(f"\n  {'monthly requests':>18}{'hosted $':>12}{'self-hosted $':>16}"
       f"{'cheaper':>12}")
for r in (100_000, 500_000, 2_000_000, 5_000_000, 10_000_000, 50_000_000):
    hc = hosted_cost(r)
    cheaper = "hosted" if hc < realistic else "self-hosted"
    print(f"  {r:>18,}{hc:>12,.0f}{realistic:>16,.0f}{cheaper:>12}")

print("\n  Note the self-hosted column does not move. That is the whole point:")
print("  it is a FIXED cost, paid whether the hardware is busy or idle.")


rule("3. UTILISATION IS THE WHOLE STORY")

print("  A fixed cost divided by actual work done. If the accelerator is idle")
print("  95% of the time, you paid for the idle 95%.\n")
print(f"  {'utilisation':>13}{'effective multiplier':>22}{'effective $/request':>22}")
for util in (1.0, 0.7, 0.5, 0.3, 0.2, 0.1, 0.05):
    served = REQ * util / 0.2          # capacity normalised so 20% util = REQ
    mult = 1 / util
    eff = realistic / max(served, 1)
    print(f"  {util:>12.0%}{mult:>21.1f}x{eff:>22.4f}")

print("\n  A workload that is bursty BY CONSTRUCTION -- office hours, weekdays,")
print("  seasonal -- cannot reach high utilisation at any total volume.")


rule("4. A REALISTIC ARRIVAL PATTERN, AND WHY IT CANNOT BREAK EVEN")

# Weekday office hours: 9-18, Mon-Fri.
hours = np.arange(HOURS_PER_MONTH)
hour_of_day = hours % 24
day_of_week = (hours // 24) % 7
active = ((hour_of_day >= 9) & (hour_of_day < 18) &
          (day_of_week < 5)).astype(float)
shape = active * (1.0 + 0.4 * np.sin(hour_of_day / 24 * 2 * np.pi))
shape = np.maximum(shape, 0)
demand = shape / shape.sum() * REQ

active_hours = int(active.sum())
peak = float(demand.max())
mean = float(demand.mean())

print(f"  {REQ:,} requests/month arriving in weekday office hours\n")
print(f"  {'total hours in month':<34}{HOURS_PER_MONTH:>10}")
print(f"  {'hours with any traffic':<34}{active_hours:>10}"
      f"  ({active_hours / HOURS_PER_MONTH:.0%})")
print(f"  {'mean requests/hour (all hours)':<34}{mean:>10.0f}")
print(f"  {'peak requests/hour':<34}{peak:>10.0f}")
print(f"  {'peak / mean':<34}{peak / mean:>10.1f}x")

capacity_needed = peak
util = mean / capacity_needed
print(f"\n  You must provision for the PEAK ({capacity_needed:.0f}/hr) and you")
print(f"  are paid-for at the MEAN ({mean:.0f}/hr).")
print(f"  -> utilisation = {util:.1%}, an effective cost multiplier of "
      f"{1 / util:.1f}x")

adjusted_breakeven = breakeven / util
print(f"\n  break-even at 100% utilisation : {breakeven:>12,.0f} requests/month")
print(f"  break-even at {util:.0%} utilisation  : {adjusted_breakeven:>12,.0f}")
print(f"                                  = {adjusted_breakeven / REQ:,.0f}x "
      f"the current volume")
print("\n  A bursty workload does not reach break-even at ANY volume without")
print("  autoscaling -- which is more engineering effort you have not costed.")


rule("5. WHEN DOES SELF-HOSTING ACTUALLY WIN?")

print(f"  Varying volume AND steadiness. 'steady' means traffic spread evenly;")
print(f"  'bursty' means the weekday-office-hours pattern above.\n")
print(f"  {'monthly requests':>18}{'hosted $':>11}{'steady self $':>15}"
      f"{'bursty self $':>15}{'winner':>14}")
for r in (500_000, 5_000_000, 20_000_000, 100_000_000):
    hc = hosted_cost(r)
    # instances scale with peak throughput; assume one instance serves 2M/month
    steady_inst = max(2, int(np.ceil(r / 2_000_000)) + 1)
    bursty_inst = max(2, int(np.ceil(r / 2_000_000 / util)) + 1)
    sc = selfhost_cost(steady_inst, 0.25)
    bc = selfhost_cost(bursty_inst, 0.25)
    win = "hosted" if hc < min(sc, bc) else "self (steady)" if sc < hc else "?"
    print(f"  {r:>18,}{hc:>11,.0f}{sc:>15,.0f}{bc:>15,.0f}{win:>14}")

print("\n  Self-hosting starts to win at high AND steady volume. The bursty")
print("  column never does, because it must provision for a peak it only")
print("  reaches for a few hours a day.")


rule("6. THE DECISION IS RARELY ABOUT COST")

AXES = [
    ("quality needed: frontier", "hosted", "open weights lag frontier models"),
    ("volume: low or bursty", "hosted", "zero cost when idle"),
    ("volume: high and steady", "self", "utilisation makes fixed cost pay"),
    ("data cannot leave our boundary", "SELF (decisive)", "money cannot buy this from a provider"),
    ("must pin an exact version forever", "SELF (decisive)", "hosted versions get deprecated"),
    ("no ML infrastructure team", "hosted", "effort is the underestimated axis"),
    ("time to market matters", "hosted", "an API key vs a serving stack"),
    ("narrow task, small model suffices", "self", "a 110M encoder runs on a CPU (M4-L11)"),
    ("very long context needed", "hosted", "your KV cache bounds it (M4-L17)"),
]
print(f"  {'requirement':<36}{'points to':<18}why")
for req, verdict, why in AXES:
    print(f"  {req:<36}{verdict:<18}{why}")

print("\n  Two rows say DECISIVE. Those are the requirements money cannot")
print("  satisfy -- and when either applies, the cost calculation above was")
print("  answering the wrong question entirely.")

print(f"\n  the cost axis, for this scenario, said:")
print(f"    hosted ${h:,.0f}/month vs self-hosted ${realistic:,.0f}/month "
      f"-> hosted, by {realistic / h:.0f}x")
print("\n  So: unless there is a residency or version-pinning requirement,")
print("  hosted is correct here. And if there IS one, cost was never the")
print("  deciding factor.")


rule("7. WHAT THIS LAB DID NOT COST YOU")

print("  This lab provisioned NOTHING. No cloud account, no accelerator, no")
print("  API key, no network call. It is arithmetic, and it cost 0.00.")
print("\n  Every price in it is ILLUSTRATIVE and dated 2026-09-09:")
print(f"    input tokens   ${IN_PRICE * 1e6:>7.2f} per million")
print(f"    output tokens  ${OUT_PRICE * 1e6:>7.2f} per million")
print(f"    accelerator    ${GPU_HOURLY:>7.2f} per hour")
print(f"    engineer       ${FTE_MONTHLY * 12:>7,.0f} per year fully loaded")
print("\n  THE METHOD TRANSFERS; THE NUMBERS DO NOT. Substitute current rates,")
print("  include redundancy, peak provisioning and engineering time, and redo")
print("  it. A comparison that omits those three is not an honest comparison.")
print("\n  And if you do provision an accelerator to test any of this: SHUT IT")
print("  DOWN afterwards. An idle GPU bills exactly like a busy one, and a")
print("  billing alert notifies you rather than capping the spend.")

print("\nDone.")
