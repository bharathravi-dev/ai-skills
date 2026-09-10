"""M8-L10 lab -- extending M5-L08's blast-radius gate and M8-L02's
deterministic cap into a THIRD kind of gate: a human decision point. A
tiered policy routes small refunds to auto-approval, mid-size ones to a
human approval queue, and large ones to escalation -- and the agent
genuinely WAITS for a human decision on the queued ones rather than
proceeding regardless. A separate case shows escalation triggered by
genuine UNCERTAINTY, not just amount. A final measurement shows the real
cost of routing everything through approval instead of a properly-tiered
policy: real numbers, not a vague "approval fatigue" claim.

Deterministic. No API key, no network, no third-party dependencies.
Run:  python labs/m8/l10_human_approval_escalation.py
"""

from __future__ import annotations

import sys

sys.stdout.reconfigure(encoding="utf-8")


def rule(title: str) -> None:
    print(f"\n{'=' * 76}\n{title}\n{'=' * 76}")


# ============================================================ 1
rule("1. A TIERED POLICY: AMOUNT DECIDES WHO DECIDES")

AUTO_APPROVE_LIMIT = 50.0
SENIOR_ESCALATION_THRESHOLD = 200.0


def decide_tier(amount: float) -> str:
    """[REAL] M5-L08's own blast-radius principle, applied to WHO decides
    rather than whether code allows it at all: small amounts are low
    enough blast radius to auto-approve; mid-size amounts need a human's
    judgment; large amounts need a MORE senior human's judgment."""
    if amount < AUTO_APPROVE_LIMIT:
        return "auto-approve"
    if amount <= SENIOR_ESCALATION_THRESHOLD:
        return "needs approval"
    return "escalate to senior review"


REQUEST_AMOUNTS = [12, 8, 45, 300, 15, 22, 500, 9, 60, 18, 250, 7, 33, 400, 11, 19, 27, 999, 14, 21]

tier_counts = {"auto-approve": 0, "needs approval": 0, "escalate to senior review": 0}
for amount in REQUEST_AMOUNTS:
    tier_counts[decide_tier(amount)] += 1

print(f"  {len(REQUEST_AMOUNTS)} real refund requests, amounts: {REQUEST_AMOUNTS}\n")
print(f"  Auto-approve (< ${AUTO_APPROVE_LIMIT:.0f}):            {tier_counts['auto-approve']}")
print(f"  Needs human approval (${AUTO_APPROVE_LIMIT:.0f}-${SENIOR_ESCALATION_THRESHOLD:.0f}):    {tier_counts['needs approval']}")
print(f"  Escalate to senior review (> ${SENIOR_ESCALATION_THRESHOLD:.0f}): {tier_counts['escalate to senior review']}")
print(f"\n  Only {tier_counts['needs approval'] + tier_counts['escalate to senior review']} of "
      f"{len(REQUEST_AMOUNTS)} requests need ANY human involvement at all --")
print("  the rest are low enough blast radius to auto-approve safely.")


# ============================================================ 2
rule("2. THE AGENT GENUINELY WAITS: NO REFUND BEFORE A HUMAN DECIDES")

ORDERS = {"O-2001": 120.0, "O-2002": 80.0}


def issue_refund(order_id: str, amount: float) -> str:
    return f"refund of ${amount:.2f} issued for {order_id}"


def request_human_approval(order_id: str, amount: float) -> str:
    """[REAL] Adds a request to a pending queue and returns its id --
    genuinely does NOT return a decision, because none exists yet."""
    request_id = f"APPR-{order_id}"
    PENDING_APPROVALS[request_id] = {"order_id": order_id, "amount": amount, "decision": None}
    return request_id


PENDING_APPROVALS: dict[str, dict] = {}


def process_request(order_id: str, amount: float) -> str:
    tier = decide_tier(amount)
    if tier == "auto-approve":
        return issue_refund(order_id, amount)
    request_id = request_human_approval(order_id, amount)
    return f"WAITING: {request_id} queued for {tier}, no refund issued yet"


print("  Two requests, both above the auto-approve limit:\n")
for order_id, amount in ORDERS.items():
    result = process_request(order_id, amount)
    print(f"    process_request({order_id!r}, {amount}) -> {result!r}")

print(f"\n  PENDING_APPROVALS: {PENDING_APPROVALS}")
print("\n  Neither refund was issued -- the function returned a WAITING state,")
print("  not a refund confirmation, because a human decision genuinely does")
print("  not exist yet. Contrast this with an ungated version that would")
print("  call issue_refund() immediately regardless of tier:")
ungated_result = issue_refund("O-2001", 120.0)
print(f"    issue_refund('O-2001', 120.0) -> {ungated_result!r}  (WRONG -- skipped the gate entirely)")

print("\n  A human decision now arrives for one of the two pending requests:")


def apply_human_decision(request_id: str, approved: bool) -> str:
    """[REAL] Only NOW, after a real decision is recorded, can a refund
    actually be issued -- the wait in process_request() was not cosmetic."""
    record = PENDING_APPROVALS[request_id]
    record["decision"] = approved
    if approved:
        return issue_refund(record["order_id"], record["amount"])
    return f"REJECTED: no refund issued for {record['order_id']}"


decision_result = apply_human_decision("APPR-O-2001", approved=True)
print(f"    apply_human_decision('APPR-O-2001', approved=True) -> {decision_result!r}")
print("\n  The refund for O-2001 was issued only once a real approval was")
print("  recorded -- 'APPR-O-2002' remains pending, genuinely unresolved,")
print(f"  in PENDING_APPROVALS: {PENDING_APPROVALS['APPR-O-2002']}")


# ============================================================ 3
rule("3. ESCALATION FROM UNCERTAINTY, NOT JUST FROM AMOUNT")


def decide_tier_with_uncertainty(amount: float | None, currency: str) -> str:
    """[REAL] Escalates when the classifier genuinely cannot place the
    request into a tier at all -- a missing amount or an unrecognized
    currency -- rather than guessing a tier and proceeding."""
    if amount is None:
        return "escalate: amount could not be determined"
    if currency != "USD":
        return f"escalate: unsupported currency {currency!r}, cannot apply USD-denominated policy"
    return decide_tier(amount)


AMBIGUOUS_CASES = [
    (30.0, "USD"),
    (None, "USD"),
    (75.0, "EUR"),
]
for amount, currency in AMBIGUOUS_CASES:
    print(f"    decide_tier_with_uncertainty({amount!r}, {currency!r}) -> "
          f"{decide_tier_with_uncertainty(amount, currency)!r}")

print("\n  The second and third cases escalate for a DIFFERENT reason than")
print("  section 1's amount-based tiers -- not because the amount is large,")
print("  but because the classifier cannot confidently determine a tier at")
print("  all. Guessing (e.g., defaulting to auto-approve for a currency the")
print("  policy was never designed to handle) would be a real, silent risk;")
print("  escalating is the honest alternative, matching M7-L13's abstention")
print("  principle applied here to a decision instead of an answer.")


# ============================================================ 4
rule("4. THE REAL COST OF 'JUST APPROVE EVERYTHING'")

always_approve_count = len(REQUEST_AMOUNTS)
smart_policy_count = tier_counts["needs approval"] + tier_counts["escalate to senior review"]

print(f"  A policy requiring human approval for EVERY request: "
      f"{always_approve_count} approvals needed for {len(REQUEST_AMOUNTS)} requests.")
print(f"  This lesson's tiered policy: {smart_policy_count} approvals needed for "
      f"the same {len(REQUEST_AMOUNTS)} requests.")
print(f"  Reduction: {(1 - smart_policy_count / always_approve_count) * 100:.0f}% fewer human decisions,")
print("  for the SAME set of real requests, with the smallest, lowest-blast-")
print("  radius ones handled automatically instead of consuming a human")
print("  reviewer's attention on every single one.")

print("\n  This is a real, measurable version of 'approval fatigue': a")
print("  reviewer facing 20 approval requests for 20 low-stakes refunds has")
print(f"  no way to tell which of the {always_approve_count} actually deserves scrutiny --")
print(f"  a reviewer facing only {smart_policy_count}, each one genuinely above the")
print("  auto-approve threshold, can give each one real attention instead of")
print("  rubber-stamping a long queue of routine requests.")


# ============================================================ 5
rule("5. WHAT THIS LAB IS AND IS NOT")

print("  REAL: every tier count, every WAITING state, and the escalation")
print("  triggers in section 3 are genuinely computed -- process_request()")
print("  genuinely returns before issuing a refund for any non-auto-approve")
print("  tier, and apply_human_decision() is the only path that can issue")
print("  one afterward.")
print("\n  ILLUSTRATIVE: apply_human_decision() stands in for a real human")
print("  reviewer's actual decision -- this lab scripts one specific")
print("  decision (approved=True) rather than modeling a real review")
print("  interface or a real reviewer's judgment. The specific dollar")
print("  thresholds are this lesson's own illustration, not a universal")
print("  policy recommendation.")
print("\n  NOT SHOWN: what information a real approval interface should show")
print("  a reviewer to let them decide quickly and correctly; a real audit")
print("  trail of who approved what and when; and what happens if a pending")
print("  approval is never resolved at all, a case bordering on M8-L13's")
print("  own timeout/recovery topic.")

print("\nDone.")
