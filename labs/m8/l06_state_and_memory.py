"""M8-L06 lab -- M8-L03's `observed` dict is WORKING memory: it exists only
for the duration of one run_tool_loop() call and is gone the moment that
call returns. This lesson asks what an agent needs to remember ACROSS
separate runs -- separate conversations, separate days -- and shows two
real failure modes: no persistent memory at all (a duplicate action), and
persistent memory scoped wrong (M5-L10's own "remembered the wrong
customer" risk, now causing a wrongly BLOCKED action rather than a wrongly
GRANTED one).

Deterministic. No API key, no network, no third-party dependencies.
Run:  python labs/m8/l06_state_and_memory.py
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from typing import Any, Callable

sys.stdout.reconfigure(encoding="utf-8")


def rule(title: str) -> None:
    print(f"\n{'=' * 76}\n{title}\n{'=' * 76}")


@dataclass
class Tool:
    name: str
    func: Callable[..., Any]
    description: str


def run_tool_loop(
    tools: list[Tool],
    decide_next: Callable[[dict], tuple[str, dict]],
    max_steps: int = 6,
) -> list[str]:
    """[REAL, M8-L03's exact loop, unmodified] One call to this function is
    one conversation's WORKING memory -- `observed` is created fresh here
    and discarded when the function returns. Nothing in this signature
    persists anything across separate calls; that is the entire point this
    lesson is built around."""
    tool_by_name = {t.name: t for t in tools}
    trace: list[str] = []
    observed: dict[str, Any] = {}
    for step in range(1, max_steps + 1):
        action_name, action_args = decide_next(observed)
        if action_name == "respond":
            trace.append(f"[step {step}] [STOP] respond -- loop stops")
            return trace
        if action_name not in tool_by_name:
            observed["last_error"] = f"unknown tool {action_name!r}"
            trace.append(f"[step {step}] unknown tool {action_name!r}")
            continue
        try:
            result = tool_by_name[action_name].func(**action_args)
            observed[action_name] = result
            trace.append(f"[step {step}] [ACT] {action_name}({action_args}) "
                         f"-> [OBSERVE] {result!r}")
        except Exception as exc:
            observed["last_error"] = str(exc)
            trace.append(f"[step {step}] {action_name}({action_args}) RAISED {exc!r}")
    trace.append(f"[step {max_steps}] [STOP] max_steps reached")
    return trace


ORDERS = {"O-1001": {"customer": "Dana Kim", "amount": 40.0}}

# A separate, real-world-plausible legacy system whose order ids were never
# coordinated with the main one -- "O-1001" exists there too, for a
# DIFFERENT customer. This is section 4's deliberate collision.
LEGACY_ORDERS = {"O-1001": {"customer": "Priya Shah", "amount": 55.0}}


# ============================================================ 1
rule("1. NO PERSISTENT MEMORY: TWO SEPARATE CONVERSATIONS, TWO REFUNDS")

REFUND_LOG: list[tuple[str, str, float]] = []   # (customer, order_id, amount) -- OUTSIDE any single loop call


def issue_refund(customer: str, order_id: str, amount: float) -> str:
    REFUND_LOG.append((customer, order_id, amount))
    return f"refund of ${amount:.2f} issued for {customer}'s order {order_id}"


REFUND_TOOLS = [Tool("issue_refund", issue_refund, "Issue a refund")]


def make_no_memory_decider(customer: str, order_id: str) -> Callable[[dict], tuple[str, dict]]:
    """[ILLUSTRATIVE] Always proposes a refund -- there is no tool available
    to check whether one was already issued, because no such memory exists
    anywhere in this section."""
    def decide_next(observed: dict) -> tuple[str, dict]:
        if "issue_refund" in observed:
            return "respond", {}
        amount = ORDERS[order_id]["amount"]
        return "issue_refund", {"customer": customer, "order_id": order_id, "amount": amount}
    return decide_next


print("  Conversation 1 -- Dana Kim asks for a refund on O-1001:")
for line in run_tool_loop(REFUND_TOOLS, make_no_memory_decider("Dana Kim", "O-1001")):
    print(f"    {line}")

print("\n  Conversation 2 -- Dana Kim contacts support again about the SAME order:")
for line in run_tool_loop(REFUND_TOOLS, make_no_memory_decider("Dana Kim", "O-1001")):
    print(f"    {line}")

total_dana = sum(a for c, o, a in REFUND_LOG if c == "Dana Kim" and o == "O-1001")
print(f"\n  REFUND_LOG: {REFUND_LOG}")
print(f"  Total refunded to Dana Kim for O-1001 (a ${ORDERS['O-1001']['amount']:.2f} order): "
      f"${total_dana:.2f}")
print("\n  Each run_tool_loop() call got a genuinely FRESH `observed` dict --")
print("  working memory, by design, does not survive between calls. With")
print("  nothing ELSE remembering that a refund already happened, the second")
print("  conversation had no way to know, and a real double refund resulted.")


# ============================================================ 2
rule("2. A PERSISTENT, CORRECTLY-SCOPED CHECK FIXES IT")

REFUND_LOG.clear()


def check_already_refunded(customer: str, order_id: str) -> bool:
    """[REAL] Reads REFUND_LOG -- state that lives OUTSIDE any single
    run_tool_loop() call, and is scoped by BOTH customer and order_id
    together."""
    return any(c == customer and o == order_id for c, o, _ in REFUND_LOG)


SCOPED_TOOLS = [
    Tool("issue_refund", issue_refund, "Issue a refund"),
    Tool("check_already_refunded", check_already_refunded, "Check refund history for this customer's order"),
]


def make_scoped_decider(customer: str, order_id: str) -> Callable[[dict], tuple[str, dict]]:
    def decide_next(observed: dict) -> tuple[str, dict]:
        if "check_already_refunded" not in observed:
            return "check_already_refunded", {"customer": customer, "order_id": order_id}
        if observed["check_already_refunded"]:
            return "respond", {}
        if "issue_refund" not in observed:
            amount = ORDERS[order_id]["amount"]
            return "issue_refund", {"customer": customer, "order_id": order_id, "amount": amount}
        return "respond", {}
    return decide_next


print("  Conversation 1 -- Dana Kim asks for a refund on O-1001:")
for line in run_tool_loop(SCOPED_TOOLS, make_scoped_decider("Dana Kim", "O-1001")):
    print(f"    {line}")

print("\n  Conversation 2 -- Dana Kim contacts support again about the SAME order:")
for line in run_tool_loop(SCOPED_TOOLS, make_scoped_decider("Dana Kim", "O-1001")):
    print(f"    {line}")

total_dana_2 = sum(a for c, o, a in REFUND_LOG if c == "Dana Kim" and o == "O-1001")
print(f"\n  REFUND_LOG: {REFUND_LOG}")
print(f"  Total refunded to Dana Kim for O-1001: ${total_dana_2:.2f} -- correct.")
print("\n  The SAME two working-memory-only conversations as section 1 now")
print("  produce the correct outcome, because check_already_refunded() reads")
print("  state that persisted across both calls -- the fix was never inside")
print("  run_tool_loop() itself (unchanged from M8-L03), only in what the")
print("  decider could consult before acting.")


# ============================================================ 3
rule("3. SCOPED WRONG: A DIFFERENT CUSTOMER'S IDENTICAL ORDER ID GETS BLOCKED")

BAD_LOG: set[str] = set()   # keyed by order_id ALONE -- no customer in the key


def issue_refund_unscoped(customer: str, order_id: str, amount: float) -> str:
    BAD_LOG.add(order_id)
    return f"refund of ${amount:.2f} issued for {customer}'s order {order_id}"


def check_already_refunded_unscoped(order_id: str) -> bool:
    """[REAL, deliberately mis-scoped] Checks order_id ALONE -- exactly the
    scoping bug M5-L10's own worked example warned about, reproduced here
    causing the OPPOSITE symptom: a wrongly BLOCKED action instead of a
    wrongly granted one."""
    return order_id in BAD_LOG


UNSCOPED_TOOLS = [
    Tool("issue_refund", issue_refund_unscoped, "Issue a refund"),
    Tool("check_already_refunded", check_already_refunded_unscoped, "Check refund history by order id"),
]


def make_unscoped_decider(customer: str, order_id: str, amount: float) -> Callable[[dict], tuple[str, dict]]:
    def decide_next(observed: dict) -> tuple[str, dict]:
        if "check_already_refunded" not in observed:
            return "check_already_refunded", {"order_id": order_id}
        if observed["check_already_refunded"]:
            return "respond", {}
        if "issue_refund" not in observed:
            return "issue_refund", {"customer": customer, "order_id": order_id, "amount": amount}
        return "respond", {}
    return decide_next


print("  Conversation 1 -- Dana Kim's O-1001 ($40.00, the main system):")
for line in run_tool_loop(UNSCOPED_TOOLS, make_unscoped_decider("Dana Kim", "O-1001", ORDERS["O-1001"]["amount"])):
    print(f"    {line}")

print("\n  Conversation 2 -- Priya Shah's O-1001 ($55.00, an UNRELATED legacy")
print("  system that happens to reuse the same order id string):")
for line in run_tool_loop(UNSCOPED_TOOLS, make_unscoped_decider("Priya Shah", "O-1001", LEGACY_ORDERS["O-1001"]["amount"])):
    print(f"    {line}")

print(f"\n  BAD_LOG: {BAD_LOG}")
print("\n  Priya Shah's legitimate, never-before-refunded order was BLOCKED --")
print("  check_already_refunded_unscoped() cannot tell her O-1001 apart from")
print("  Dana's, because the key it checks (order_id alone) does not include")
print("  who the order belongs to. This is M5-L10's own worked example ('the")
print("  assistant that remembered the wrong customer'), reproduced here as")
print("  a wrongly BLOCKED action instead of a wrongly GRANTED one -- the")
print("  same root cause, a scoping key missing the identity that actually")
print("  distinguishes two records, produces different-looking symptoms.")


# ============================================================ 4
rule("4. WORKING MEMORY VS. PERSISTENT MEMORY, SCOPED CORRECTLY")

print("  Three distinct kinds of memory appeared in this lesson:\n")
print("  WORKING memory (observed, inside one run_tool_loop() call): exists")
print("  only for that call's duration -- section 1 showed this is correctly")
print("  scoped to nothing surviving, by design (M8-L03's own contract).")
print("\n  PERSISTENT memory, scoped correctly (REFUND_LOG, keyed by BOTH")
print("  customer and order_id together): section 2 showed this is what a")
print("  fact like 'was this specific customer's specific order already")
print("  refunded' actually needs -- surviving across conversations, keyed")
print("  by the full identity that makes the fact meaningful.")
print("\n  PERSISTENT memory, scoped WRONG (BAD_LOG, keyed by order_id alone):")
print("  section 3 showed this is worse than no persistent memory at all in")
print("  this specific case -- it didn't just fail to help, it actively")
print("  produced an incorrect block for an unrelated customer.")
print("\n  The general rule this lesson leaves for later ones: deciding WHICH")
print("  facts need persistent memory, and preventing an action from being")
print("  repeated even with a correctly-scoped check racing itself, is")
print("  M8-L12's own topic (idempotency) -- this lesson is about WHERE the")
print("  memory lives and how it must be KEYED, not yet about race conditions")
print("  in checking it.")


# ============================================================ 5
rule("5. WHAT THIS LAB IS AND IS NOT")

print("  REAL: every REFUND_LOG and BAD_LOG entry above is genuinely")
print("  produced by running run_tool_loop() multiple times against real,")
print("  executed tool functions -- the double refund in section 1 and the")
print("  wrongly-blocked refund in section 3 are measured outcomes of the")
print("  actual code, not asserted claims.")
print("\n  ILLUSTRATIVE: the deciders in every section are small, scripted")
print("  stand-ins for a real model's choices, and LEGACY_ORDERS' id")
print("  collision is a constructed example, not a claim about how often")
print("  real systems reuse order ids across unrelated systems.")
print("\n  NOT SHOWN: preventing a duplicate action from a correctly-scoped")
print("  check that is itself checked twice in a race (M8-L12); where")
print("  persistent memory should physically live -- a database, a cache, a")
print("  session store -- which this lesson treats as an in-memory")
print("  illustration only; and human approval as a check independent of")
print("  any stored memory at all (M8-L10).")

print("\nDone.")
