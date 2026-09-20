"""M11-L01 lab -- the shared responsibility model, counted rather than recited.
This lab computes:

  1. who is responsible for 18 controls across five deployment models,
  2. how the customer's share changes as you move up the stack,
  3. the controls that are ALWAYS yours, whatever you buy,
  4. the assumption gap: controls teams believe are handled and are not,
  5. what "the provider is compliant" does and does not transfer to you.

Deterministic. No AWS account, no network, no third-party dependencies.
Run:  python labs/m11/l01_shared_responsibility.py
"""

from __future__ import annotations

import sys

sys.stdout.reconfigure(encoding="utf-8")


def rule(title: str) -> None:
    print(f"\n{'=' * 76}\n{title}\n{'=' * 76}")


# P = provider, C = customer, S = shared (both have a distinct job)
MODELS = ["on-prem", "EC2/IaaS", "containers", "Lambda", "managed AI"]
CONTROLS = {
    "physical data-centre security":      ["C", "P", "P", "P", "P"],
    "hardware and network fabric":        ["C", "P", "P", "P", "P"],
    "hypervisor / isolation":             ["C", "P", "P", "P", "P"],
    "host OS patching":                   ["C", "C", "P", "P", "P"],
    "container base image patching":      ["C", "C", "C", "P", "P"],
    "runtime / language patching":        ["C", "C", "C", "S", "P"],
    "application code":                   ["C", "C", "C", "C", "C"],
    "application dependencies":           ["C", "C", "C", "C", "C"],
    "network segmentation (VPC, SGs)":    ["C", "C", "C", "C", "S"],
    "encryption in transit":              ["C", "S", "S", "S", "P"],
    "encryption at rest (key policy)":    ["C", "S", "S", "S", "S"],
    "identity and access policy (IAM)":   ["C", "C", "C", "C", "C"],
    "data classification":                ["C", "C", "C", "C", "C"],
    "what data you send the service":     ["C", "C", "C", "C", "C"],
    "retention and deletion":             ["C", "C", "C", "C", "S"],
    "backup and restore testing":         ["C", "C", "C", "C", "S"],
    "availability design (multi-AZ)":     ["C", "C", "C", "S", "S"],
    "monitoring your own failures":       ["C", "C", "C", "C", "C"],
}

# ============================================================ 1
rule("1. WHO IS RESPONSIBLE FOR WHAT?")

print(f"  {'control':<36}" + "".join(f"{m:>13}" for m in MODELS))
for name, row in CONTROLS.items():
    print(f"  {name:<36}" + "".join(f"{v:>13}" for v in row))
print("\n  P = provider   C = customer   S = shared (each has a distinct part)")


# ============================================================ 2
rule("2. HOW MUCH IS STILL YOURS?")

print(f"  {'model':<14}{'provider':>10}{'shared':>9}{'customer':>10}{'your share':>13}")
for i, m in enumerate(MODELS):
    col = [row[i] for row in CONTROLS.values()]
    p, s, c = col.count("P"), col.count("S"), col.count("C")
    share = (c + 0.5 * s) / len(col)
    print(f"  {m:<14}{p:>10}{s:>9}{c:>10}{share:>12.0%}")
first = [row[0] for row in CONTROLS.values()]
last = [row[-1] for row in CONTROLS.values()]
drop = ((first.count("C") + 0.5 * first.count("S")) - (last.count("C") + 0.5 * last.count("S"))) / len(CONTROLS)
print(f"\n  moving from on-prem to a managed AI service removes {drop:.0%} of the controls from")
print("  your plate. It does not remove the rest, and the rest is where the incidents")
print("  in Module 10 came from.")


# ============================================================ 3
rule("3. WHAT IS ALWAYS YOURS?")

always = [n for n, row in CONTROLS.items() if all(v == "C" for v in row)]
never = [n for n, row in CONTROLS.items() if all(v == "P" for v in row[1:])]
print(f"  yours in EVERY model ({len(always)}):")
for n in always:
    print(f"    - {n}")
print(f"\n  the provider's in every cloud model ({len(never)}):")
for n in never:
    print(f"    - {n}")
print("\n  The first list is the one to memorise. Access policy, data classification,")
print("  what you send, your own code and whether you noticed it break are yours at")
print("  every level of abstraction you will ever buy (M10-L07, M10-L14).")


# ============================================================ 4
rule("4. THE ASSUMPTION GAP")

BELIEFS = [
    ("'S3 is durable, so our data is backed up'", "no",
     "durability is not versioning; a delete or overwrite still destroys it"),
    ("'The provider encrypts at rest, so we are covered'", "partly",
     "who holds the key, and who can decrypt, is your key policy (M11-L17)"),
    ("'Managed service, so patching is handled'", "partly",
     "the runtime is; your dependencies are not (M2-L17)"),
    ("'The provider is certified, so we are compliant'", "no",
     "their certification covers their layer only (section 5)"),
    ("'Multi-AZ by default'", "no",
     "for some services; for most it is a choice you make and pay for"),
    ("'The provider monitors our application'", "no",
     "they monitor their platform; your errors are yours (M11-L16)"),
    ("'Deleting the resource deletes the data'", "no",
     "backups, snapshots, logs and replicas may survive (M10-L06)"),
    ("'Private subnet means unreachable'", "partly",
     "egress, peering, endpoints and misconfigured SGs all exist (M11-L08)"),
]
print(f"  {'common belief':<52}{'true?':>8}   what is actually the case")
for text, verdict, why in BELIEFS:
    print(f"  {text:<52}{verdict:>8}   {why}")
wrong = sum(1 for _, v, _ in BELIEFS if v == "no")
print(f"\n  flatly wrong: {wrong}/{len(BELIEFS)}   partly wrong: {sum(1 for _, v, _ in BELIEFS if v == 'partly')}/{len(BELIEFS)}")
print("  Every one of these is a sentence somebody has said in a design review. The")
print("  test is not 'is it managed?' but 'which specific failure does the provider")
print("  prevent, and which do I?'")


# ============================================================ 5
rule("5. WHAT A PROVIDER'S CERTIFICATION TRANSFERS")

TRANSFERS = [
    ("the data centre's physical controls", True),
    ("the hypervisor's tenant isolation", True),
    ("the service's own availability commitments", True),
    ("your IAM policies being least-privilege", False),
    ("your bucket not being public", False),
    ("your data classification being correct", False),
    ("your retention actually deleting things", False),
    ("your application's authorization logic", False),
    ("your evidence that any of the above works", False),
]
yes = sum(1 for _, t in TRANSFERS if t)
print(f"  {'claim':<46}{'transfers to you?':>19}")
for text, t in TRANSFERS:
    print(f"  {text:<46}{('yes' if t else 'NO'):>19}")
print(f"\n  transfers: {yes}/{len(TRANSFERS)}")
print("  A provider's audit report is an input to YOUR evidence, not a substitute for")
print("  it (M10-L11, M10-L16). You inherit their controls at their layer and you")
print("  still have to demonstrate yours.")


rule("6. WHAT THIS LAB IS AND IS NOT")
print("  REAL: every share, count and classification above is computed from the")
print("  responsibility table encoded in this script.")
print("\n  ILLUSTRATIVE: the table is a teaching simplification. Real boundaries are")
print("  per service and are stated in the provider's own shared-responsibility")
print("  documentation -- read it for the services you actually use.")
print("\n  NOT SHOWN: contractual terms, audit report scopes, and the specific")
print("  responsibility boundaries of individual AWS services (M11-L10 onwards).")
print("\nDone.")
