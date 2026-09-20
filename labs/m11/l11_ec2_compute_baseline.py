"""M11-L11 lab -- sizing, buying and scaling compute, with the arithmetic shown.
This lab computes:

  1. right-sizing a fleet from measured utilisation, and what the headroom costs,
  2. on-demand vs Savings Plan vs Spot over one year, including interruption risk,
  3. autoscaling lag against a traffic spike: how many requests are lost,
  4. why an AI workload's bottleneck is usually not CPU,
  5. instance age and configuration drift across a fleet.

Deterministic (seeded). No AWS account, no network, no third-party dependencies.
Run:  python labs/m11/l11_ec2_compute_baseline.py
"""

from __future__ import annotations

import random
import sys

sys.stdout.reconfigure(encoding="utf-8")


def rule(title: str) -> None:
    print(f"\n{'=' * 76}\n{title}\n{'=' * 76}")


rng = random.Random(1111)

# ============================================================ 1
rule("1. RIGHT-SIZING FROM MEASURED UTILISATION")

SIZES = {"large": (2, 8, 0.096), "xlarge": (4, 16, 0.192), "2xlarge": (8, 32, 0.384),
         "4xlarge": (16, 64, 0.768)}     # vCPU, GiB, $/hour [ILLUSTRATIVE]
FLEET = [
    # name,               current size, p95 vCPU used, p95 GiB used, count
    ("api servers",       "2xlarge", 1.4,  5.2, 6),
    ("ingestion workers", "4xlarge", 9.1, 28.0, 3),
    ("embedding workers", "xlarge",  3.8, 14.8, 8),
    ("admin/batch",       "xlarge",  0.3,  1.1, 2),
]
HEADROOM = 1.4      # keep 40% above measured p95
HOURS = 730


def smallest_fitting(vcpu: float, gib: float) -> str:
    for name, (c, g, _) in SIZES.items():
        if c >= vcpu and g >= gib:
            return name
    return "4xlarge"


print(f"  headroom factor {HEADROOM:.1f}x over measured p95\n")
print(f"  {'workload':<20}{'now':<10}{'p95 vCPU':>10}{'p95 GiB':>10}   {'right size':<12}"
      f"{'$/mo now':>11}{'$/mo right':>12}")
now_total = right_total = 0.0
for name, size, vcpu, gib, count in FLEET:
    want = smallest_fitting(vcpu * HEADROOM, gib * HEADROOM)
    now_cost = SIZES[size][2] * HOURS * count
    right_cost = SIZES[want][2] * HOURS * count
    now_total += now_cost
    right_total += right_cost
    print(f"  {name:<20}{size:<10}{vcpu:>10.1f}{gib:>10.1f}   {want:<12}"
          f"{now_cost:>11,.0f}{right_cost:>12,.0f}")
print(f"  {'TOTAL':<20}{'':<10}{'':>10}{'':>10}   {'':<12}{now_total:>11,.0f}{right_total:>12,.0f}")
print(f"\n  right-sizing saves ${now_total - right_total:,.0f}/month "
      f"(${(now_total - right_total) * 12:,.0f}/year), {1 - right_total / now_total:.0%}")
print("  Two rows are the interesting ones. 'ingestion workers' at p95 9.1 vCPU does")
print("  not fit a 2xlarge once headroom is applied, so it stays where it is. And")
print("  'embedding workers' is UNDERSIZED: 3.8 x 1.4 = 5.3 vCPU needs a 2xlarge, so")
print("  right-sizing makes it more expensive -- which is why the net saving is only")
print("  6% rather than the 40% a slide would promise. Right-sizing is 'measure, then")
print("  fit', not 'make everything smaller'. Size from p95 plus headroom, never from")
print("  the mean (M13-L11).")


# ============================================================ 2
rule("2. ON-DEMAND, SAVINGS PLAN, OR SPOT?")

BASE_HOURLY = 0.384
INSTANCES = 10
PLANS = {
    "on-demand":                  (1.00, 0.00, "none", "stop any time"),
    "1-year Savings Plan (no upfront)": (0.72, 0.00, "none", "committed for 1 year"),
    "3-year Savings Plan (all upfront)": (0.55, 0.00, "none", "committed for 3 years"),
    "Spot":                       (0.32, 0.05, "2-minute notice", "can be reclaimed"),
}
print(f"  {INSTANCES} instances at ${BASE_HOURLY}/hour on-demand [ILLUSTRATIVE discounts]\n")
print(f"  {'purchase option':<36}{'rate':>7}{'$/year':>11}{'saving':>9}   commitment")
od = BASE_HOURLY * 8760 * INSTANCES
for name, (mult, interrupt, notice, commit) in PLANS.items():
    annual = od * mult
    print(f"  {name:<36}{mult:>7.2f}{annual:>11,.0f}{1 - mult:>9.0%}   {commit}")
spot_mult, spot_interrupt = PLANS["Spot"][0], PLANS["Spot"][1]
print(f"\n  Spot saves {1 - spot_mult:.0%} and can be reclaimed with {PLANS['Spot'][2]}.")
print(f"  At a {spot_interrupt:.0%} hourly interruption rate, an instance survives a")
print(f"  24-hour batch job {(1 - spot_interrupt) ** 24:.0%} of the time -- so Spot is for work that")
print("  CHECKPOINTS and resumes (M8-L14), not for a stateful service.")
print("  Savings Plans are a commitment to SPEND, not to specific instances: they")
print("  are safe for a stable baseline and wrong for a workload you may re-platform")
print("  within the term (M11-L12).")


# ============================================================ 3
rule("3. AUTOSCALING LAG AGAINST A SPIKE")

CAPACITY_PER_INSTANCE = 40      # requests/second
START_INSTANCES = 4
SPIKE_RPS = 420
BOOT_STAGES = [("alarm evaluates (2 periods of 60 s)", 120), ("instance launches", 45),
               ("OS and agent start", 40), ("application and model client warm up", 95),
               ("health checks pass, traffic arrives", 30)]
total_lag = sum(s for _, s in BOOT_STAGES)
print(f"  {START_INSTANCES} instances x {CAPACITY_PER_INSTANCE} rps = {START_INSTANCES * CAPACITY_PER_INSTANCE} rps"
      f"; traffic jumps to {SPIKE_RPS} rps\n")
print(f"  {'stage':<44}{'seconds':>9}{'cumulative':>12}")
cum = 0
for label, secs in BOOT_STAGES:
    cum += secs
    print(f"  {label:<44}{secs:>9}{cum:>12}")
shortfall = SPIKE_RPS - START_INSTANCES * CAPACITY_PER_INSTANCE
print(f"\n  shortfall during the lag: {shortfall} rps for {total_lag} s = "
      f"{shortfall * total_lag:,} requests queued or rejected")
print(f"  needed instances: {-(-SPIKE_RPS // CAPACITY_PER_INSTANCE)}; scaling from {START_INSTANCES} takes "
      f"{total_lag} s ({total_lag / 60:.1f} minutes)")
print("\n  Autoscaling responds in MINUTES. It is a cost control and a slow-growth")
print("  mechanism, not a spike defence. Defend spikes with headroom, a queue")
print("  (M11-L15), or a load shedder that degrades deliberately (M7-L13). Note")
print("  which stage is largest: model-client warm-up, which is an AI-specific cost.")


# ============================================================ 4
rule("4. FOR AN AI WORKLOAD, WHAT IS ACTUALLY THE BOTTLENECK?")

PROFILE = [
    ("waiting on the model API",   2400, "network + provider time; CPU is idle"),
    ("waiting on vector search",    180, "mostly the database's problem"),
    ("waiting on object storage",    90, "network"),
    ("tokenising and assembling",    35, "real CPU, and small"),
    ("JSON parsing and validation",  18, "real CPU, and smaller"),
    ("logging",                       7, "real CPU, negligible"),
]
total_ms = sum(ms for _, ms, _ in PROFILE)
cpu_ms = sum(ms for name, ms, _ in PROFILE if "waiting" not in name)
print(f"  {'phase':<32}{'ms':>7}{'share':>8}   what it is")
for name, ms, note in PROFILE:
    print(f"  {name:<32}{ms:>7}{ms / total_ms:>8.1%}   {note}")
print(f"  {'TOTAL':<32}{total_ms:>7}{1:>8.0%}")
print(f"\n  CPU-bound work: {cpu_ms} ms of {total_ms} ms = {cpu_ms / total_ms:.1%}")
print(f"  a machine could hold roughly {total_ms / cpu_ms:.0f}x more concurrent requests than CPU")
print("  alone suggests -- if the runtime can wait on many things at once (M2-L13).")
print("  So the sizing question is CONCURRENCY and MEMORY, not vCPU. A fleet sized")
print("  by CPU utilisation will look 2% busy and still fall over on connection")
print("  limits, memory, or provider rate limits (M12-L12).")


# ============================================================ 5
rule("5. FLEET AGE AND DRIFT")

N = 40
ages = [int(abs(rng.gauss(0, 150))) for _ in range(N)]
manual_changes = [rng.random() < min(0.9, a / 200) for a in ages]
print(f"  {'age since last AMI replacement':<38}{'instances':>11}{'with manual changes':>22}")
for lo, hi, label in [(0, 30, "under 30 days"), (30, 90, "30-90 days"),
                      (90, 180, "90-180 days"), (180, 10_000, "over 180 days")]:
    idx = [i for i, a in enumerate(ages) if lo <= a < hi]
    drifted = sum(1 for i in idx if manual_changes[i])
    print(f"  {label:<38}{len(idx):>11}{drifted:>22}")
old = sum(1 for a in ages if a >= 90)
drifted_total = sum(manual_changes)
print(f"\n  instances older than 90 days: {old}/{N} ({old / N:.0%})")
print(f"  instances with manual changes (drift): {drifted_total}/{N} ({drifted_total / N:.0%})")
print("  An instance that has been running long enough to be patched by hand is an")
print("  instance you cannot reproduce. Replace instances rather than updating them:")
print("  bake an AMI, roll the fleet, and let nothing survive a deployment. Drift is")
print("  what makes 'it works on that box' an outage waiting for a scale-out event")
print("  (M11-L18, M10-L13).")


rule("6. WHAT THIS LAB IS AND IS NOT")
print("  REAL: every sizing decision, annual cost, lag total, profile share and drift")
print("  count above is computed from the values in this script.")
print("\n  ILLUSTRATIVE: instance prices, discount multipliers, the Spot interruption")
print("  rate, boot timings and the request profile are invented. Check current AWS")
print("  pricing and measure your own timings.")
print("\n  NOT SHOWN: instance families and their trade-offs in detail, GPU instances,")
print("  placement groups, EBS volume types and burstable (T-family) credits.")
print("\nDone.")
