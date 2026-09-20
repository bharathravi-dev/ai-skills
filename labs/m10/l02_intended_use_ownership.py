"""M10-L02 lab -- the first governance artefact: a statement of what a system is
for, what it is not for, and who answers for it. Measures:

  1. completeness of three intended-use statements against a required-field list,
  2. what an explicit out-of-scope list does to 20 realistic user requests,
  3. ownership: controls with no owner, and owners with too much,
  4. limitations that are written down but surfaced nowhere a user would see,
  5. staleness: which statements no longer describe the system after four changes.

Deterministic. No API key, no network, no third-party dependencies.
Run:  python labs/m10/l02_intended_use_ownership.py
"""

from __future__ import annotations

import sys

sys.stdout.reconfigure(encoding="utf-8")


def rule(title: str) -> None:
    print(f"\n{'=' * 76}\n{title}\n{'=' * 76}")


REQUIRED_FIELDS = ["purpose", "users", "inputs", "outputs", "decisions_affected", "out_of_scope",
                   "limitations", "human_oversight", "owner", "reviewed_on"]

STATEMENTS = {
    "marketing one-liner": {
        "purpose": "An AI assistant that helps our support team work faster.",
        "users": "Everyone.",
    },
    "partial, written by the build team": {
        "purpose": "Drafts refund emails for delivery-failure complaints under GBP 100.",
        "users": "Support agents in the UK team.",
        "inputs": "Customer email text, order record, refund policy document.",
        "outputs": "A draft email and a proposed refund amount.",
        "limitations": "Weaker on emails not written in English.",
        "owner": "Support Platform team",
    },
    "complete": {
        "purpose": "Drafts refund emails for delivery-failure complaints under GBP 100.",
        "users": "Support agents in the UK team, during a customer conversation.",
        "inputs": "Customer email text, order record, refund policy document (version pinned).",
        "outputs": "A draft email and a proposed refund amount, with the policy clause quoted.",
        "decisions_affected": "Whether a refund is offered, and how much, subject to agent approval.",
        "out_of_scope": "Goodwill refunds; B2B accounts; disputes; refunds over GBP 100; non-UK entities.",
        "limitations": "Weaker on emails not written in English; cannot see payment-provider status.",
        "human_oversight": "An agent must approve every send; refunds over GBP 100 need a supervisor.",
        "owner": "Director of Support Operations (named individual, reviewed quarterly)",
        "reviewed_on": "2026-08-01",
    },
}


# ============================================================ 1
rule("1. COMPLETENESS OF THE INTENDED-USE STATEMENT")

for name, statement in STATEMENTS.items():
    missing = [f for f in REQUIRED_FIELDS if f not in statement]
    print(f"  {name:<34}: {len(REQUIRED_FIELDS) - len(missing):>2}/{len(REQUIRED_FIELDS)} fields"
          + (f"   missing: {', '.join(missing[:4])}{'...' if len(missing) > 4 else ''}" if missing else "   complete"))
print("\n  'Helps our support team work faster' cannot be reviewed, tested, or")
print("  refused against. Every later artefact in this module refers back to these")
print("  fields: the risk register to decisions_affected, the gates to limitations,")
print("  the incident plan to owner.")


# ============================================================ 2
rule("2. WHAT AN OUT-OF-SCOPE LIST DOES TO REAL REQUESTS")

REQUESTS = [
    ("Customer says parcel never arrived, order GBP 40", True),
    ("Parcel arrived damaged, order GBP 85", True),
    ("Customer wants GBP 300 refunded for a late delivery", False),
    ("Customer is threatening legal action over a delivery", False),
    ("B2B account asks for a credit note", False),
    ("Customer asks for a goodwill refund because they changed their mind", False),
    ("Delivery failed, order GBP 12", True),
    ("Customer asks to close their account and delete their data", False),
    ("Customer asks whether their parcel is insured", False),
    ("Repeat delivery failure, order GBP 60", True),
    ("Customer asks for compensation for missing a job interview", False),
    ("Delivery failed for an order placed in the German store", False),
    ("Customer asks the agent to explain the refund policy", True),
    ("Customer disputes a refund already issued", False),
    ("Delivery failed, order GBP 99.99", True),
    ("Customer asks for a refund on a subscription", False),
    ("Delivery failed but the customer wants store credit instead", False),
    ("Delivery failed, order GBP 25, customer writes in French", True),
    ("Customer asks for the CEO's email address", False),
    ("Delivery failed, order GBP 150", False),
]
OUT_OF_SCOPE_RULES = [
    ("amount above GBP 100", lambda r: any(s in r for s in ("GBP 300", "GBP 150"))),
    ("goodwill or change of mind", lambda r: "goodwill" in r or "changed their mind" in r),
    ("B2B account", lambda r: "B2B" in r),
    ("dispute or legal", lambda r: "legal" in r or "disputes" in r),
    ("not a delivery-failure refund", lambda r: any(s in r for s in ("delete their data", "insured", "interview",
                                                                    "subscription", "store credit", "CEO"))),
    ("non-UK entity", lambda r: "German store" in r),
]


def in_scope(request: str) -> tuple[bool, str]:
    for label, rule_fn in OUT_OF_SCOPE_RULES:
        if rule_fn(request):
            return False, label
    return True, ""


no_check = sum(1 for _, ok in REQUESTS if not ok)          # answered anyway, because nothing refuses
with_check = sum(1 for req, ok in REQUESTS if not ok and in_scope(req)[0])
false_refusals = sum(1 for req, ok in REQUESTS if ok and not in_scope(req)[0])
print(f"  {len(REQUESTS)} requests, of which {no_check} are outside the stated scope.")
print(f"    no scope check         : {no_check} out-of-scope requests handled by the assistant")
print(f"    explicit out-of-scope list: {with_check} handled, {false_refusals} in-scope request(s) wrongly refused")
print("\n  Out-of-scope requests routed to a human:")
for req, ok in REQUESTS:
    allowed, why = in_scope(req)
    if not allowed:
        print(f"    - {req[:58]:<58} ({why})")

HELD_OUT = [   # written after the rules, in the words real customers use
    ("Customer wants GBP 250 back for a late parcel", False),
    ("Order never turned up; this is our company account", False),
    ("Customer says their solicitor will be in touch", False),
    ("Customer would prefer a gift card instead of a refund", False),
    ("Delivery failed, order GBP 30; customer says our CEO would be embarrassed", True),
    ("Parcel lost in transit, order GBP 45", True),
]
missed = [r for r, ok in HELD_OUT if not ok and in_scope(r)[0]]
wrong = [r for r, ok in HELD_OUT if ok and not in_scope(r)[0]]
print(f"\n  The same rules on {len(HELD_OUT)} held-out requests written afterwards:")
print(f"    out-of-scope requests the rules MISSED : {len(missed)}  e.g. {missed[0] if missed else '-'}")
print(f"    in-scope requests wrongly REFUSED      : {len(wrong)}  e.g. {wrong[0] if wrong else '-'}")
print("  Keyword rules encode the examples you thought of. The scope statement is the")
print("  governance artefact; enforcing it needs a classifier that fails safe, or a")
print("  human triage step, and monitoring of both error directions (M10-L12).")


# ============================================================ 3
rule("3. OWNERSHIP: UNOWNED CONTROLS AND OVERLOADED OWNERS")

CONTROLS = {
    "Refund limit enforced in the tool": "Support Platform engineer (A. Okafor)",
    "Prompt version pinned and reviewed": None,
    "Evaluation set refreshed quarterly": "Applied science (R. Mehta)",
    "Subgroup refusal-rate monitoring": None,
    "Access control on the refund tool": "Support Platform engineer (A. Okafor)",
    "Retention of customer email text": "Privacy office (S. Blum)",
    "Incident runbook and kill switch": "Support Platform engineer (A. Okafor)",
    "Supplier terms reviewed on renewal": "Privacy office (S. Blum)",
    "Disclosure that drafts are AI-generated": None,
    "Model version change approval": "Support Platform engineer (A. Okafor)",
}
unowned = [c for c, o in CONTROLS.items() if o is None]
load: dict[str, int] = {}
for owner in CONTROLS.values():
    if owner:
        load[owner] = load.get(owner, 0) + 1
print(f"  controls with no owner: {len(unowned)}/{len(CONTROLS)}")
for c in unowned:
    print(f"    - {c}")
print("\n  owner load:")
for owner, n in sorted(load.items(), key=lambda kv: -kv[1]):
    print(f"    {owner:<40} {n} control(s)")
print("\n  An unowned control is a control nobody will notice failing. One person")
print("  holding half of them is a single point of failure for the same reason.")


# ============================================================ 4
rule("4. LIMITATIONS: WRITTEN DOWN VS ACTUALLY SURFACED")

LIMITATIONS = {
    "Weaker on emails not written in English": {"internal doc", "model card"},
    "Cannot see payment-provider status": {"internal doc"},
    "Policy document may be up to 24 hours out of date": set(),
    "Refunds over GBP 100 are out of scope": {"internal doc", "model card", "agent UI", "refusal message"},
    "Drafts are AI-generated": {"internal doc"},
}
SEEN_BY_USERS = {"agent UI", "refusal message", "customer email footer"}
for text, places in LIMITATIONS.items():
    visible = places & SEEN_BY_USERS
    print(f"  [{'visible' if visible else 'HIDDEN':>7}] {text:<52} in: {', '.join(sorted(places)) or 'nowhere'}")
hidden = sum(1 for p in LIMITATIONS.values() if not (p & SEEN_BY_USERS))
print(f"\n  {hidden}/{len(LIMITATIONS)} limitations are recorded but never reach the person relying on the output.")
print("  A limitation only changes behaviour where it is visible at the moment of use (M10-L09).")


# ============================================================ 5
rule("5. STALENESS: THE SYSTEM CHANGED, THE STATEMENT DID NOT")

CHANGES = [
    ("Model swapped to a cheaper provider", ["limitations", "outputs"]),
    ("German store connected as a data source", ["users", "out_of_scope"]),
    ("Auto-send enabled for refunds under GBP 20", ["human_oversight", "decisions_affected"]),
    ("Retention shortened from 3 years to 90 days", ["limitations"]),
]
statement = dict(STATEMENTS["complete"])
stale_fields: set[str] = set()
for change, affected in CHANGES:
    stale_fields.update(affected)
    print(f"  {change:<44} -> now describes reality wrongly: {', '.join(affected)}")
print(f"\n  after four ordinary changes, {len(stale_fields)}/{len(REQUIRED_FIELDS)} fields of the statement are out of date")
print(f"  last reviewed: {statement['reviewed_on']}  -- a quarterly review would have caught three of these late.")
print("  Tie the review to CHANGES, not only to the calendar: a model swap, a new")
print("  data source, or a new automated action should each require re-approval (M10-L14).")


rule("6. WHAT THIS LAB IS AND IS NOT")
print("  REAL: every count above is computed from the statements, requests, controls,")
print("  limitations and changes encoded in this file.")
print("\n  ILLUSTRATIVE: the scope rules are keyword matches standing in for a real")
print("  classifier or a human triage step; a production system needs a far better")
print("  scope check than string matching, and must fail safe when unsure.")
print("\n  NOT SHOWN: how to decide the scope in the first place (M14-L01, M14-L07) and")
print("  how the statement becomes a public-facing card (M10-L15).")
print("\nDone.")
