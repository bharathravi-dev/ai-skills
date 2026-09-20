"""M11-L18 lab -- infrastructure as code, and what a pipeline actually buys you.
This lab computes:

  1. configuration drift when console changes are allowed,
  2. reading a plan: which changes REPLACE a resource rather than update it,
  3. where a defect is caught, and what catching it later costs,
  4. what infrastructure code can and cannot roll back,
  5. pipeline credentials: stored keys against OIDC federation.

Deterministic (seeded). No AWS account, no network, no third-party dependencies.
Run:  python labs/m11/l18_iac_cicd_rollback.py
"""

from __future__ import annotations

import random
import sys

sys.stdout.reconfigure(encoding="utf-8")


def rule(title: str) -> None:
    print(f"\n{'=' * 76}\n{title}\n{'=' * 76}")


rng = random.Random(1118)

# ============================================================ 1
rule("1. DRIFT: WHAT HAPPENS WHEN THE CONSOLE IS ALLOWED")

RESOURCES = 180
WEEKS = 52
POLICIES = [
    ("console changes normal, no detection",   0.010, None),
    ("console changes discouraged, no detection", 0.004, None),
    ("drift detection monthly, fixed by hand", 0.010, 4),
    ("read-only console; changes only via code", 0.0002, 4),
]
print(f"  {RESOURCES} resources, {WEEKS} weeks\n")
print(f"  {'policy':<44}{'drifted at year end':>21}{'share':>8}")
for label, weekly_rate, repair_weeks in POLICIES:
    drifted = 0
    for week in range(WEEKS):
        drifted += sum(1 for _ in range(RESOURCES - drifted) if rng.random() < weekly_rate)
        if repair_weeks and week % repair_weeks == repair_weeks - 1:
            drifted -= int(drifted * 0.7)        # detection finds and fixes most, not all
    print(f"  {label:<44}{drifted:>21}{drifted / RESOURCES:>8.0%}")
print("\n  Every drifted resource is one where the code no longer describes reality,")
print("  so the next apply either reverts someone's fix or fails outright.")
print("  Detection plus repair keeps the number small but never reaches zero, and it")
print("  costs someone a recurring afternoon. Removing WRITE access to the console")
print("  removes the source. The console stays useful for reading, which is most of")
print("  what it is good for -- and a break-glass role covers the rest (M11-L03).")


# ============================================================ 2
rule("2. READING A PLAN: WHICH CHANGES DESTROY SOMETHING?")

CHANGES = [
    ("security group rule added",              "update in place", False, ""),
    ("instance type changed",                  "update in place", False, "brief restart"),
    ("subnet CIDR changed",                    "REPLACE",         True,  "new subnet; anything in it is orphaned"),
    ("RDS instance identifier renamed",        "REPLACE",         True,  "NEW EMPTY DATABASE; the old one is deleted"),
    ("S3 bucket name changed",                 "REPLACE",         True,  "new empty bucket; data not migrated"),
    ("Lambda memory increased",                "update in place", False, ""),
    ("DynamoDB partition key changed",         "REPLACE",         True,  "new empty table"),
    ("tags changed",                           "update in place", False, ""),
    ("availability zone of a subnet changed",  "REPLACE",         True,  "everything in it is recreated"),
]
print(f"  {'change':<42}{'effect':<18}{'data loss?':>11}   note")
for name, effect, destructive, note in CHANGES:
    print(f"  {name:<42}{effect:<18}{('YES' if destructive else 'no'):>11}   {note}")
bad = sum(1 for _, _, d, _ in CHANGES if d)
print(f"\n  changes that REPLACE a resource: {bad}/{len(CHANGES)}")
print("  A plan is not a formality; it is the only place the difference between")
print("  'update' and 'destroy and create' is visible before it happens. Require the")
print("  plan output in the pull request, make a reviewer acknowledge every")
print("  replacement, and put deletion protection on stateful resources so that an")
print("  unreviewed plan cannot execute (M10-L14 -- these are one-way doors).")


# ============================================================ 3
rule("3. WHERE IS THE DEFECT CAUGHT, AND WHAT DOES THAT COST?")

STAGES = [
    ("editor / pre-commit hook",        1,    0.55),
    ("CI: lint, validate, policy check", 4,   0.25),
    ("CI: plan reviewed by a human",     30,  0.10),
    ("deploy to staging",                90,  0.06),
    ("canary in production",             240, 0.03),
    ("full production incident",         5400, 0.01),
]
print(f"  {'caught at':<36}{'cost (minutes)':>16}{'share of defects':>19}{'weighted':>11}")
total = 0.0
for label, minutes, share in STAGES:
    total += minutes * share
    print(f"  {label:<36}{minutes:>16,}{share:>19.0%}{minutes * share:>11.1f}")
print(f"  {'EXPECTED COST PER DEFECT':<36}{'':>16}{'':>19}{total:>11.1f} min")

# counterfactual: policy-as-code catches the class of defect that currently
# escapes to canary and production (public buckets, open security groups,
# missing encryption) -- moving those 4% up to the CI check stage
ALT = [0.55, 0.25 + 0.04, 0.10, 0.06, 0.0, 0.0]
alt_total = sum(m * s for (_, m, _), s in zip(STAGES, ALT))
print(f"\n  counterfactual: a policy check that catches the 3% reaching canary and the")
print(f"  1% reaching production -- open security groups, public buckets, missing")
print(f"  encryption -- moves them to the 4-minute stage:")
print(f"    expected cost per defect {total:.1f} min -> {alt_total:.1f} min "
      f"({1 - alt_total / total:.0%} lower)")
print("  Each stage is roughly an order of magnitude more expensive than the one")
print("  before, so moving ONE class of defect one stage earlier pays for a lot of")
print("  automation -- and the 1% that reaches production dominates the average.")
print("  Policy-as-code checks (no public buckets, no 0.0.0.0/0, tags required,")
print("  encryption required) are the cheapest stage to add (M10-L12, M11-L10).")


rule("4. WHAT CAN THE PIPELINE ACTUALLY ROLL BACK?")

ROLLBACK = [
    ("application container image",     True,  "redeploy the previous tag"),
    ("Lambda function code",            True,  "alias points to the previous version"),
    ("security group rules",            True,  "re-apply the previous code"),
    ("IAM policy change",               True,  "re-apply, but sessions already issued persist"),
    ("a database schema migration",     False, "needs the reverse migration, written in advance"),
    ("a deleted S3 bucket",             False, "the name may be gone; the data certainly is"),
    ("a deleted RDS instance",          False, "restore from snapshot, if one exists and is current"),
    ("a re-indexed vector store",       False, "rebuild, if you kept the previous index (M10-L14)"),
    ("emails the deployed agent sent",  False, "cannot be unsent"),
]
rev = sum(1 for _, r, _ in ROLLBACK if r)
print(f"  {'change':<36}{'revertible by re-apply?':>25}   how")
for name, r, how in ROLLBACK:
    print(f"  {name:<36}{('yes' if r else 'NO'):>25}   {how}")
print(f"\n  revertible: {rev}/{len(ROLLBACK)}")
print("  'Infrastructure as code means we can always roll back' is true of")
print("  CONFIGURATION and false of STATE and EFFECTS -- the same split as M10-L14.")
print("  So: deletion protection on stateful resources, reverse migrations written")
print("  with the forward one, previous artefacts kept through a soak period, and a")
print("  pipeline that can deploy the previous commit without a rebuild.")


# ============================================================ 5
rule("5. PIPELINE CREDENTIALS")

OPTIONS = [
    ("long-lived IAM user keys in CI secrets", "until someone rotates them", "any job, any branch, forever",
     "a leaked log line is a permanent breach"),
    ("OIDC federation, role per repository",   "the job's duration (minutes)", "that repo, that workflow",
     "a leaked token expires in minutes"),
    ("OIDC + branch condition + environment approval", "the job's duration", "that repo, that BRANCH, after approval",
     "a fork's pull request cannot deploy"),
]
print(f"  {'option':<44}{'credential lifetime':<30}")
for name, lifetime, scope, risk in OPTIONS:
    print(f"  {name:<44}{lifetime:<30}")
    print(f"      scope: {scope}")
    print(f"      if it leaks: {risk}")
print("\n  This is M11-L05's arithmetic applied to CI. The subtlety specific to")
print("  pipelines is the CONDITION: an OIDC trust policy that checks only the")
print("  repository lets any branch -- including one from a fork's pull request --")
print("  assume the deployment role. Condition on the repo AND the branch or")
print("  environment, and require an approval for production (M11-L04 section 5.7).")


rule("6. WHAT THIS LAB IS AND IS NOT")
print("  REAL: every drift count, replacement classification, weighted cost and")
print("  rollback verdict above is computed from the values in this script.")
print("\n  ILLUSTRATIVE: drift rates, defect distribution, stage costs and repair")
print("  effectiveness are invented. The ORDERING of stage costs -- each roughly an")
print("  order of magnitude above the last -- is the durable part.")
print("\n  TOOL-AGNOSTIC: 'plan', 'apply' and 'replace' describe CloudFormation,")
print("  Terraform and CDK alike, with different names.")
print("\n  NOT SHOWN: state-file management and locking, module design, multi-account")
print("  pipeline topologies, and progressive delivery tooling (M13-L14).")
print("\nDone.")
