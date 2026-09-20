"""M11-L08 lab -- how a private workload reaches the outside, and what each path costs.
This lab computes:

  1. the four egress paths compared on cost, exposure and whether policy can restrict them,
  2. NAT gateway arithmetic across one, two and three AZs,
  3. what is reachable from a private subnet under four egress designs,
  4. an S3 gateway-endpoint policy that stops data leaving for someone else's bucket,
  5. a reachability check: all four conditions that must hold for inbound traffic.

Deterministic. No AWS account, no network, no third-party dependencies.
Run:  python labs/m11/l08_public_private_nat_endpoints.py
"""

from __future__ import annotations

import sys

sys.stdout.reconfigure(encoding="utf-8")


def rule(title: str) -> None:
    print(f"\n{'=' * 76}\n{title}\n{'=' * 76}")


# ============================================================ 1
rule("1. FOUR WAYS OUT, COMPARED")

PATHS = {
    "public IP + internet gateway": {
        "reaches": "the internet", "inbound_possible": True, "per_gb": 0.00,
        "hourly": 0.00, "leaves_aws": True, "policy": "security group only"},
    "NAT gateway": {
        "reaches": "the internet", "inbound_possible": False, "per_gb": 0.045,
        "hourly": 0.045, "leaves_aws": True, "policy": "security group only"},
    "gateway endpoint (S3, DynamoDB)": {
        "reaches": "that service only", "inbound_possible": False, "per_gb": 0.00,
        "hourly": 0.00, "leaves_aws": False, "policy": "ENDPOINT POLICY (per bucket/table)"},
    "interface endpoint (PrivateLink)": {
        "reaches": "that service only", "inbound_possible": False, "per_gb": 0.01,
        "hourly": 0.011, "leaves_aws": False, "policy": "ENDPOINT POLICY + security group"},
}
print(f"  {'path':<34}{'reaches':<20}{'inbound?':>10}{'$/GB':>8}{'$/hour':>9}   restrictable by")
for name, p in PATHS.items():
    print(f"  {name:<34}{p['reaches']:<20}{('YES' if p['inbound_possible'] else 'no'):>10}"
          f"{p['per_gb']:>8.3f}{p['hourly']:>9.3f}   {p['policy']}")
print("\n  [ILLUSTRATIVE rates.] Two things to notice. A public IP is the only row that")
print("  allows INBOUND connections -- 'it needs internet access' is not a reason to")
print("  give something a public address. And only the endpoint rows can be")
print("  restricted by a POLICY rather than by an address range (section 4).")


# ============================================================ 2
rule("2. WHAT DOES NAT ACTUALLY COST?")

HOURS = 730
GB = 6_000
nat = PATHS["NAT gateway"]
print(f"  {GB:,} GB/month of egress, {HOURS} hours [ILLUSTRATIVE rates]\n")
print(f"  {'design':<40}{'hourly':>11}{'processing':>13}{'total/mo':>12}{'total/yr':>12}")
for azs in (1, 2, 3):
    hourly = nat["hourly"] * HOURS * azs
    proc = nat["per_gb"] * GB
    total = hourly + proc
    label = f"{azs} NAT gateway{'s' if azs > 1 else ''} ({azs} AZ{'s' if azs > 1 else ''})"
    print(f"  {label:<40}{hourly:>11,.0f}{proc:>13,.0f}{total:>12,.0f}{total * 12:>12,.0f}")
s3_share = 0.75
saved = nat["per_gb"] * GB * s3_share
print(f"\n  if {s3_share:.0%} of that traffic is S3 and moves to a GATEWAY endpoint:")
print(f"    processing charges fall by ${saved:,.0f}/month (${saved * 12:,.0f}/year) and the traffic")
print(f"    never leaves the AWS network.")
print("  Multi-AZ NAT is bought for availability, not throughput: one NAT per AZ so")
print("  an AZ failure does not take egress with it -- and so that traffic does not")
print("  cross AZs to reach it, which would be charged again (M11-L02).")


# ============================================================ 3
rule("3. WHAT CAN A COMPROMISED WORKLOAD REACH?")

DESTINATIONS = [
    ("our S3 bucket (intended)",              "s3"),
    ("ANOTHER ACCOUNT'S S3 bucket",           "s3"),
    ("Bedrock / the model API",               "aws"),
    ("an approved partner API",               "partner"),
    ("pastebin.example / attacker endpoint",  "internet"),
    ("a crypto-mining pool",                  "internet"),
]
DESIGNS = {
    "public IP, open egress":       {"s3", "aws", "partner", "internet"},
    "NAT gateway, open egress":     {"s3", "aws", "partner", "internet"},
    "endpoints + NAT for partner":  {"s3", "aws", "partner"},
    "endpoints only, no NAT":       {"s3", "aws"},
}
SHORT = {"public IP, open egress": "public IP", "NAT gateway, open egress": "NAT",
         "endpoints + NAT for partner": "endpts+NAT", "endpoints only, no NAT": "endpts only"}
print(f"  {'destination':<40}" + "".join(f"{SHORT[d]:>13}" for d in DESIGNS))
for label, kind in DESTINATIONS:
    row = "".join(f"{('reach' if kind in allowed else 'BLOCKED'):>13}" for allowed in DESIGNS.values())
    print(f"  {label:<40}{row}")
print()
for label, allowed in DESIGNS.items():
    blocked = sum(1 for _, k in DESTINATIONS if k not in allowed)
    print(f"  {label:<32}blocks {blocked}/{len(DESTINATIONS)} destinations")
print("\n  Note row 2: every design that reaches S3 at all still reaches SOMEONE ELSE'S")
print("  S3 bucket. Network design alone cannot tell your bucket from theirs --")
print("  that needs an endpoint policy (section 4). This is the exfiltration path")
print("  that survives 'we blocked the internet' (M9-L12, M10-L10).")


# ============================================================ 4
rule("4. AN ENDPOINT POLICY THAT KNOWS WHOSE BUCKET IT IS")

ENDPOINT_POLICY = {
    "allowed_buckets": ["arn:aws:s3:::acme-prod-docs", "arn:aws:s3:::acme-prod-docs/*"],
}
ATTEMPTS = [
    ("PutObject to acme-prod-docs/report.pdf",      "arn:aws:s3:::acme-prod-docs/report.pdf"),
    ("GetObject from acme-prod-docs/policy.pdf",    "arn:aws:s3:::acme-prod-docs/policy.pdf"),
    ("PutObject to attacker-exfil-bucket/dump.zip", "arn:aws:s3:::attacker-exfil-bucket/dump.zip"),
    ("PutObject to acme-dev-scratch/dump.zip",      "arn:aws:s3:::acme-dev-scratch/dump.zip"),
]
import fnmatch
print(f"  endpoint policy allows only: {', '.join(ENDPOINT_POLICY['allowed_buckets'])}\n")
print(f"  {'attempt':<50}{'verdict':>10}")
for label, arn in ATTEMPTS:
    ok = any(fnmatch.fnmatchcase(arn, p) for p in ENDPOINT_POLICY["allowed_buckets"])
    print(f"  {label:<50}{('allowed' if ok else 'DENIED'):>10}")
blocked = sum(1 for _, arn in ATTEMPTS
              if not any(fnmatch.fnmatchcase(arn, p) for p in ENDPOINT_POLICY["allowed_buckets"]))
print(f"\n  denied: {blocked}/{len(ATTEMPTS)}")
print("  An endpoint policy is a resource-level control on a NETWORK path. It is the")
print("  only mechanism in this lesson that can distinguish your bucket from an")
print("  attacker's, because both live at the same service endpoint. Pair it with an")
print("  identity policy condition on aws:SourceVpce (M11-L04, M11-L10).")


# ============================================================ 5
rule("5. CAN ANYTHING ACTUALLY REACH THIS INSTANCE?")

CONDITIONS = ["public IP assigned", "route to internet gateway", "security group allows",
              "network ACL allows"]
SCENARIOS = {
    "public subnet, SG open on 443":     [True, True, True, True],
    "public subnet, SG closed":          [True, True, False, True],
    "private subnet, SG open":           [False, False, True, True],
    "public subnet, no public IP":       [False, True, True, True],
    "public subnet, NACL denies inbound": [True, True, True, False],
}
print(f"  {'scenario':<38}" + "".join(f"{c.split(' ')[0][:9]:>12}" for c in CONDITIONS) + "   reachable?")
for name, conds in SCENARIOS.items():
    print(f"  {name:<38}" + "".join(f"{('yes' if c else 'no'):>12}" for c in conds)
          + f"   {'YES' if all(conds) else 'no'}")
print("\n  All four must hold. That is why 'is it exposed?' has four answers, and why")
print("  auditing only security groups misses instances that are unreachable anyway")
print("  -- and, worse, reports as safe an instance whose SG is closed today and")
print("  will be opened by someone next week (M10-L07).")


rule("6. WHAT THIS LAB IS AND IS NOT")
print("  REAL: every cost, block count, policy verdict and reachability result above")
print("  is computed from the values and rules in this script.")
print("\n  ILLUSTRATIVE: all per-GB and hourly rates are invented; check current AWS")
print("  pricing. Traffic volumes and the destination list are invented too.")
print("\n  NOT SHOWN: AWS Network Firewall, egress proxies with domain allowlists,")
print("  Transit Gateway designs, and PrivateLink for your own services (M11-L09).")
print("\nDone.")
