"""M10-L01 lab -- governance, safety, security and compliance are four different
things, and treating them as one leaves gaps. This lab encodes 24 real-shaped
failures from AI systems, gives each of the four disciplines a review "lens", and
measures:

  1. how many of the 24 each lens catches on its own,
  2. which failures are caught by exactly one lens (the gaps if you skip it),
  3. cross-tabs: systems that are secure but unsafe, compliant but ungoverned,
  4. ownership: who signs off, and how many failures have no owner if a role is
     missing from the organisation.

The 24 failures and the lenses are hand-built teaching material, not a survey.
Deterministic. No API key, no network, no third-party dependencies.
Run:  python labs/m10/l01_four_disciplines.py
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field

sys.stdout.reconfigure(encoding="utf-8")


def rule(title: str) -> None:
    print(f"\n{'=' * 76}\n{title}\n{'=' * 76}")


@dataclass(frozen=True)
class Failure:
    name: str
    adversary: bool          # someone is deliberately attacking the system
    user_harm: bool          # a user or third party is harmed by normal operation
    legal_duty: bool         # a specific legal or contractual obligation is engaged
    process_gap: bool        # nobody decided, recorded or reviewed something
    tags: tuple = field(default=())


FAILURES = [
    Failure("Prompt injection in a retrieved document triggers a refund", True, True, False, False),
    Failure("Stolen access token replayed against the MCP server", True, False, False, False),
    Failure("Support agent exfiltrates data via a markdown image URL", True, True, False, False),
    Failure("Tenant A's cached answer served to tenant B", True, True, True, False),
    Failure("Dependency in the server image has a critical CVE", True, False, False, False),
    Failure("Model invents a refund policy that does not exist", False, True, False, False),
    Failure("Assistant gives confident medical dosage advice", False, True, True, False),
    Failure("Summariser drops the word 'not' in safety instructions", False, True, False, False),
    Failure("Chatbot responds abusively when provoked", False, True, False, False),
    Failure("Model refuses valid requests from speakers of one dialect", False, True, True, False),
    Failure("Personal data retained for three years with no policy", False, False, True, True),
    Failure("Training data licence forbids commercial use", False, False, True, True),
    Failure("No record of which prompt version produced an output", False, False, True, True),
    Failure("Users are not told they are talking to an AI", False, False, True, True),
    Failure("Deletion request not propagated to the vector index", False, False, True, True),
    Failure("No named owner for the classifier in production", False, False, False, True),
    Failure("Nobody decided what accuracy is good enough to ship", False, True, False, True),
    Failure("Evaluation set was never refreshed after launch", False, True, False, True),
    Failure("Three teams run near-identical LLM features, unknown to each other", False, False, False, True),
    Failure("A model was swapped for a cheaper one with no re-evaluation", False, True, False, True),
    Failure("Incident had no runbook; response took nine hours", True, True, False, True),
    Failure("Subgroup accuracy never measured before release", False, True, True, True),
    Failure("Vendor changed data-retention terms; nobody noticed", False, False, True, True),
    Failure("Kill switch existed but no one had permission to use it", True, True, False, True),
]

LENSES = {
    # A failure can belong to more than one lens: an injected instruction that causes a
    # wrong refund is both an attack (security) and a harm in normal use (safety).
    "security": lambda f: f.adversary,
    "safety": lambda f: f.user_harm,
    "compliance": lambda f: f.legal_duty,
    "governance": lambda f: f.process_gap,
}
OWNERS = {"security": "Security engineering", "safety": "Product + applied science",
          "compliance": "Legal / privacy office", "governance": "Accountable system owner"}


# ============================================================ 1
rule("1. WHAT EACH LENS CATCHES ON ITS OWN")

caught = {name: {f.name for f in FAILURES if fn(f)} for name, fn in LENSES.items()}
for name, found in caught.items():
    print(f"  {name:<11} review catches {len(found):>2}/{len(FAILURES)}   (owner: {OWNERS[name]})")
union = set().union(*caught.values())
print(f"\n  all four together catch {len(union)}/{len(FAILURES)}")
print(f"  caught by no lens: {sorted(f.name for f in FAILURES if f.name not in union) or 'none'}")


# ============================================================ 2
rule("2. WHAT YOU LOSE BY SKIPPING ONE DISCIPLINE")

for name in LENSES:
    others = set().union(*(v for k, v in caught.items() if k != name))
    only_here = caught[name] - others
    print(f"  without {name:<11}: {len(only_here):>2} failure(s) would be caught by nobody")
    for item in sorted(only_here)[:2]:
        print(f"      e.g. {item}")


# ============================================================ 3
rule("3. SECURE BUT UNSAFE, COMPLIANT BUT UNGOVERNED")

pairs = [("security", "safety"), ("compliance", "governance"), ("security", "compliance")]
for a, b in pairs:
    only_a = caught[a] - caught[b]
    only_b = caught[b] - caught[a]
    both = caught[a] & caught[b]
    print(f"  {a:<11} only: {len(only_a):>2}   {b:<11} only: {len(only_b):>2}   both: {len(both):>2}")
def first(include: str, exclude: str | None = None, also: str | None = None) -> str:
    return next(f.name for f in FAILURES
                if f.name in caught[include]
                and (exclude is None or f.name not in caught[exclude])
                and (also is None or f.name in caught[also]))


print("\n  One example of each combination:")
print(f"    nothing to attack, but users are harmed  : {first('safety', 'security')}")
print(f"    an attack that also harms users          : {first('security', also='safety')}")
print(f"    a legal duty with no adversary           : {first('compliance', 'security')}")
print(f"    a process gap with no legal duty         : {first('governance', 'compliance')}")


# ============================================================ 4
rule("4. OWNERSHIP: WHAT HAPPENS WHEN A ROLE IS MISSING")

for missing in LENSES:
    present = {k: v for k, v in caught.items() if k != missing}
    unowned = [f.name for f in FAILURES if not any(f.name in v for v in present.values())]
    print(f"  no {OWNERS[missing]:<28}: {len(unowned):>2} failure(s) have no owner")
print("\n  'Someone will notice' is not an owner. Each failure above needs a named")
print("  role that reviews for it before release and is called when it happens.")


# ============================================================ 5
rule("5. THE FOUR QUESTIONS, APPLIED TO ONE FEATURE")

feature = "an assistant that drafts and sends customer refund emails"
questions = [
    ("governance", "Who owns this, what is it for, what is out of scope, and what evidence do we keep?"),
    ("safety", "What happens when it is wrong, confidently wrong, or wrong for one group of users?"),
    ("security", "Who might attack it, through which input, and what could they reach?"),
    ("compliance", "Which obligations apply to this data and this decision, and who signs that off?"),
]
print(f"  Feature: {feature}\n")
for name, q in questions:
    print(f"  {name:<11}: {q}")
print("\n  The same feature, four different reviews, four different owners, four")
print("  different artefacts (inventory entry and risk register, evaluation and")
print("  abstention rules, threat model and controls, records and disclosures).")


rule("6. WHAT THIS LAB IS AND IS NOT")
print("  REAL: every count above is computed from the 24 encoded failures and the")
print("  four lens definitions in this file.")
print("\n  ILLUSTRATIVE: the failures are hand-written composites of common incidents,")
print("  and the lenses are simplified: real reviews use judgement, and disciplines")
print("  overlap more than four boolean predicates suggest.")
print("\n  NOT SHOWN: any jurisdiction's legal requirements (this course gives no legal")
print("  advice, M10-L16), and the artefacts themselves (M10-L02 onward).")
print("\nDone.")
