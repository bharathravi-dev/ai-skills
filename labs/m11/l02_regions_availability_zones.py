"""M11-L02 lab -- where you put things has four consequences you can compute.
This lab computes:

  1. the latency floor set by distance, and what it does to a chatty design,
  2. availability arithmetic: one AZ, two AZs, two regions,
  3. which regions survive a data-residency constraint,
  4. what crossing an AZ or a region boundary costs per month,
  5. a placement decision scored over four candidate regions.

Deterministic. No AWS account, no network, no third-party dependencies.
Run:  python labs/m11/l02_regions_availability_zones.py
"""

from __future__ import annotations

import sys

sys.stdout.reconfigure(encoding="utf-8")


def rule(title: str) -> None:
    print(f"\n{'=' * 76}\n{title}\n{'=' * 76}")


# ============================================================ 1
rule("1. THE LATENCY FLOOR IS PHYSICS, NOT ENGINEERING")

C_FIBRE_KM_PER_MS = 200.0     # light in glass, ~200 km per millisecond
ROUTE_FACTOR = 1.5            # cables are not straight lines
USER = "London"
DISTANCES_KM = {              # great-circle distance from London [ILLUSTRATIVE]
    "eu-west-2 (London)": 20,
    "eu-west-1 (Ireland)": 470,
    "eu-central-1 (Frankfurt)": 640,
    "us-east-1 (N. Virginia)": 5900,
    "ap-southeast-2 (Sydney)": 16990,
}
print(f"  user in {USER}; round-trip floor = 2 x distance x {ROUTE_FACTOR} / {C_FIBRE_KM_PER_MS:.0f} km per ms\n")
print(f"  {'region':<28}{'km':>8}{'RTT floor':>12}{'1 call':>10}{'6 sequential calls':>21}")
rtts = {}
for region, km in DISTANCES_KM.items():
    rtt = 2 * km * ROUTE_FACTOR / C_FIBRE_KM_PER_MS
    rtts[region] = rtt
    print(f"  {region:<28}{km:>8,}{rtt:>10.1f} ms{rtt:>8.1f} ms{rtt * 6:>18.1f} ms")
print(f"\n  a RAG request that makes 6 sequential round trips (embed, search, rerank,")
print(f"  generate, tool call, log) pays the floor SIX times: "
      f"{rtts['eu-west-2 (London)'] * 6:.1f} ms in London vs "
      f"{rtts['us-east-1 (N. Virginia)'] * 6:.0f} ms from Virginia.")
print("  This is before any processing. You cannot optimise your way under it; you")
print("  can only move closer or make fewer round trips (M13-L10).")


# ============================================================ 2
rule("2. AVAILABILITY: ONE AZ, TWO AZs, TWO REGIONS")

AZ_FAIL = 0.001          # probability an AZ is unavailable in a given period [ILLUSTRATIVE]
REGION_FAIL = 0.0002     # probability the whole region is unavailable
APP_FAIL = 0.002         # your own software failing, independent of infrastructure

designs = {
    "single AZ":                 1 - (1 - AZ_FAIL) * (1 - REGION_FAIL),
    "two AZs, one region":       1 - (1 - AZ_FAIL ** 2) * (1 - REGION_FAIL),
    "three AZs, one region":     1 - (1 - AZ_FAIL ** 3) * (1 - REGION_FAIL),
    "two regions, active-active": 1 - (1 - (AZ_FAIL ** 2 + REGION_FAIL) ** 2),
}
print("  unavailability shown in ppm (parts per million of the period)\n")
print(f"  {'design':<30}{'infra ppm':>12}{'your app ppm':>15}{'total ppm':>12}{'availability':>15}")
for name, unavail in designs.items():
    total = 1 - (1 - unavail) * (1 - APP_FAIL)
    print(f"  {name:<30}{unavail * 1e6:>12,.2f}{APP_FAIL * 1e6:>15,.0f}{total * 1e6:>12,.2f}"
          f"{1 - total:>14.4%}")
print("\n  Two lessons. First, the second AZ is the biggest single improvement and the")
print(f"  cheapest: infra unavailability falls from {designs['single AZ'] * 1e6:,.0f} ppm to "
      f"{designs['two AZs, one region'] * 1e6:,.0f} ppm.")
print(f"  Second, your own software contributes {APP_FAIL * 1e6:,.0f} ppm on its own, so going from two")
print("  AZs to two regions moves the end-to-end number by almost nothing. Spend the")
print("  effort on the dominant term (M13-L11).")


# ============================================================ 3
rule("3. WHICH REGIONS SURVIVE THE CONSTRAINT?")

REGIONS = {
    "eu-west-2 (London)":       {"continent": "europe", "uk": True,  "service_available": True},
    "eu-west-1 (Ireland)":      {"continent": "europe", "uk": False, "service_available": True},
    "eu-central-1 (Frankfurt)": {"continent": "europe", "uk": False, "service_available": True},
    "us-east-1 (N. Virginia)":  {"continent": "americas", "uk": False, "service_available": True},
    "ap-southeast-2 (Sydney)":  {"continent": "apac", "uk": False, "service_available": False},
}
CONSTRAINTS = {
    "none":                         lambda r: True,
    "data stays in Europe":         lambda r: r["continent"] == "europe",
    "data stays in the UK":         lambda r: r["uk"],
    "Europe + the AI service exists": lambda r: r["continent"] == "europe" and r["service_available"],
}
for label, fn in CONSTRAINTS.items():
    ok = [n for n, r in REGIONS.items() if fn(r)]
    print(f"  {label:<32}{len(ok)}/{len(REGIONS)} regions: {', '.join(n.split(' ')[0] for n in ok)}")
print("\n  Residency is a filter applied BEFORE latency and cost, not a tie-breaker")
print("  after them (M10-L06). And the filter that surprises teams is the last one:")
print("  not every service, model or feature exists in every region (M12-L01).")


# ============================================================ 4
rule("4. WHAT DOES CROSSING A BOUNDARY COST?")

GB_PER_MONTH = 8000
RATES = {                         # USD per GB [ILLUSTRATIVE -- check current pricing]
    "within one AZ (private IP)": 0.00,
    "between AZs in a region":    0.01,
    "between regions":            0.02,
    "out to the internet":        0.09,
}
print(f"  {GB_PER_MONTH:,} GB/month of traffic between two components\n")
print(f"  {'placement':<32}{'USD/GB':>9}{'USD/month':>13}{'USD/year':>12}")
for name, rate in RATES.items():
    print(f"  {name:<32}{rate:>9.2f}{rate * GB_PER_MONTH:>13,.0f}{rate * GB_PER_MONTH * 12:>12,.0f}")
print(f"\n  the same traffic costs $0 or ${RATES['out to the internet'] * GB_PER_MONTH * 12:,.0f}/year "
      f"depending only on where the two ends sit.")
print("  Chatty services split across AZs for no reason are a recurring line item;")
print("  so is a NAT gateway carrying traffic that could use a VPC endpoint (M11-L08).")


# ============================================================ 5
rule("5. A PLACEMENT DECISION, SCORED")

CANDIDATES = {
    #                             residency  service   RTT ms  rel. cost  ops familiarity
    "eu-west-2 (London)":        (True,  True,  0.3,  1.08, 4),
    "eu-west-1 (Ireland)":       (True,  True,  7.1,  1.00, 5),
    "eu-central-1 (Frankfurt)":  (True,  True,  9.6,  1.04, 3),
    "us-east-1 (N. Virginia)":   (False, True, 88.5, 0.95, 5),
}
RULE = "data must stay in Europe; the AI service must exist in region"
print(f"  hard requirements: {RULE}\n")
print(f"  {'region':<28}{'gates':>8}{'RTT':>10}{'cost idx':>11}{'ops':>6}   verdict")
eligible = []
for name, (res, svc, rtt, cost, ops) in CANDIDATES.items():
    gates = res and svc
    if gates:
        eligible.append((name, rtt, cost, ops))
    print(f"  {name:<28}{('pass' if gates else 'FAIL'):>8}{rtt:>8.1f} ms{cost:>11.2f}{ops:>6}"
          f"   {'eligible' if gates else 'excluded by residency'}")
print(f"\n  eligible: {len(eligible)}/{len(CANDIDATES)}")
best_latency = min(eligible, key=lambda e: e[1])
best_cost = min(eligible, key=lambda e: e[2])
print(f"  lowest latency among eligible : {best_latency[0]} ({best_latency[1]:.1f} ms)")
print(f"  lowest cost among eligible    : {best_cost[0]} (index {best_cost[2]:.2f})")
print(f"  latency difference between them: {abs(best_latency[1] - best_cost[1]):.1f} ms "
      f"per round trip, x6 round trips = {abs(best_latency[1] - best_cost[1]) * 6:.1f} ms per request")
print("\n  The honest form of this decision: gates first (residency, service")
print("  availability), then a trade-off between two numbers you can both state.")
print("  'Everyone uses us-east-1' is not one of the inputs (M10-L11).")


rule("6. WHAT THIS LAB IS AND IS NOT")
print("  REAL: every latency floor, availability figure, filter result, transfer")
print("  cost and comparison above is computed from the values in this script.")
print("\n  ILLUSTRATIVE: distances are approximate, failure probabilities are invented,")
print("  and the per-GB rates are made up. Check current AWS pricing and the region")
print("  table for the services you use -- both change.")
print("\n  NOT SHOWN: edge caching and CDNs, Local Zones and Outposts, cross-region")
print("  replication mechanics, and legal analysis of residency (M10-L16).")
print("\nDone.")
