"""M8-L11 lab -- not all tools carry the same retry risk. A read-only
lookup can be called any number of times with no effect on the world beyond
its own return value; a state-changing action does something to the world
each time it runs, and calling it again is not automatically safe (M8-L06's
own double-refund finding, revisited here as a property of the ACTION
rather than of missing memory). This lesson tags each tool with a declared
`read_only` flag and then VERIFIES that declaration empirically, by calling
each tool twice and checking whether the second call changed anything the
first call didn't already establish.

Deterministic. No API key, no network, no third-party dependencies.
Run:  python labs/m8/l11_read_only_vs_state_changing.py
"""

from __future__ import annotations

import copy
import sys
from dataclasses import dataclass
from typing import Any, Callable

sys.stdout.reconfigure(encoding="utf-8")


def rule(title: str) -> None:
    print(f"\n{'=' * 76}\n{title}\n{'=' * 76}")


ORDERS = {"O-3001": {"item": "Desk Lamp", "amount": 40.0, "address": "12 Main St"}}
REFUND_LOG: list[tuple[str, float]] = []


def get_order(order_id: str) -> dict:
    return dict(ORDERS[order_id])


def check_inventory(item: str) -> int:
    return {"Desk Lamp": 7, "Wireless Mouse": 0}.get(item, 0)


def issue_refund(order_id: str, amount: float) -> str:
    REFUND_LOG.append((order_id, amount))
    return f"refund of ${amount:.2f} issued for {order_id}"


def update_shipping_address(order_id: str, new_address: str) -> str:
    ORDERS[order_id]["address"] = new_address
    return f"address for {order_id} updated to {new_address!r}"


@dataclass
class Tool:
    name: str
    func: Callable[..., Any]
    declared_read_only: bool


TOOLS = [
    Tool("get_order", get_order, declared_read_only=True),
    Tool("check_inventory", check_inventory, declared_read_only=True),
    Tool("issue_refund", issue_refund, declared_read_only=False),
    Tool("update_shipping_address", update_shipping_address, declared_read_only=False),
]


# ============================================================ 1
rule("1. A DECLARED FLAG, VERIFIED BY ACTUALLY CALLING EACH TOOL TWICE")


def world_snapshot() -> tuple:
    """[REAL] Captures everything this lab's tools could possibly mutate --
    used to check, empirically, whether even ONE call has any side effect
    on the world beyond returning a value. Uses a DEEP copy deliberately:
    ORDERS' values are themselves dicts, and a shallow copy would alias
    those inner dicts, making a real mutation (like an address update)
    invisible to a before/after comparison."""
    return (copy.deepcopy(ORDERS), list(REFUND_LOG))


CALL_ARGS = {
    "get_order": {"order_id": "O-3001"},
    "check_inventory": {"item": "Desk Lamp"},
    "issue_refund": {"order_id": "O-3001", "amount": 10.0},
    "update_shipping_address": {"order_id": "O-3001", "new_address": "99 Oak Ave"},
}

print(f"  {'Tool':<26}{'Declared':<16}{'Has ANY side effect?':<24}{'Verified'}")
for tool in TOOLS:
    args = CALL_ARGS[tool.name]
    before = world_snapshot()
    tool.func(**args)
    after = world_snapshot()
    has_side_effect = after != before
    verified = has_side_effect != tool.declared_read_only
    print(f"  {tool.name:<26}{'read-only' if tool.declared_read_only else 'state-changing':<16}"
          f"{str(has_side_effect):<24}{'yes' if verified else 'NO -- MISMATCH'}")

print(f"\n  ORDERS after all calls: {ORDERS}")
print(f"  REFUND_LOG after all calls: {REFUND_LOG}")
print("\n  get_order and check_inventory left the world UNCHANGED -- neither")
print("  ORDERS nor REFUND_LOG differ before versus after either call.")
print("  issue_refund and update_shipping_address each genuinely changed the")
print("  world the moment they ran, confirming their declared tags")
print("  empirically, not just by the label attached to them.")

print("\n  A further, more subtle check: call update_shipping_address a SECOND")
print("  time with the IDENTICAL address already on file:")
before_repeat = world_snapshot()
update_shipping_address("O-3001", "99 Oak Ave")
after_repeat = world_snapshot()
print(f"    World changed by this second, identical call? {after_repeat != before_repeat}")
print("  This tool is genuinely state-changing (it writes to ORDERS) -- but")
print("  writing the SAME value twice happens to look unchanged, because a")
print("  SET overwritten with an identical value is indistinguishable from")
print("  never having been called again. issue_refund's retry in section 2")
print("  shows the opposite: an APPEND-style action that adds a new entry")
print("  EVERY time, identical arguments or not. Both are state-changing;")
print("  only one of them is also naturally safe to repeat -- exactly the")
print("  distinction M8-L12 (idempotency) builds on directly.")


# ============================================================ 2
rule("2. RETRYING AFTER A SUSPECTED FAILURE: SAFE FOR ONE KIND, NOT THE OTHER")

REFUND_LOG.clear()


def call_with_simulated_retry(tool: Tool, args: dict, retries: int) -> None:
    """[REAL] Simulates a caller that isn't sure whether an earlier attempt
    actually went through (a timeout, a dropped connection) and retries
    defensively -- a real, common pattern, not a contrived one."""
    for _ in range(retries):
        tool.func(**args)


print("  A caller unsure whether its first attempt succeeded retries 3 times:\n")

before = world_snapshot()
call_with_simulated_retry(next(t for t in TOOLS if t.name == "check_inventory"),
                          {"item": "Desk Lamp"}, retries=3)
after = world_snapshot()
print(f"  check_inventory retried 3x -- world changed? {before != after}")

call_with_simulated_retry(next(t for t in TOOLS if t.name == "issue_refund"),
                          {"order_id": "O-3001", "amount": 25.0}, retries=3)
print(f"  issue_refund retried 3x -- REFUND_LOG now: {REFUND_LOG}")
total_refunded = sum(a for _, a in REFUND_LOG)
print(f"  Total refunded for a SINGLE $25.00 refund request: ${total_refunded:.2f}")

print("\n  Retrying the read-only lookup 3 times cost nothing beyond 3 function")
print("  calls -- the world was identical before and after. Retrying the")
print("  state-changing action 3 times, with no other safeguard, issued the")
print("  refund 3 TIMES -- the exact double/triple-execution risk M8-L06's")
print("  own lab demonstrated, now identified as a property of THIS KIND of")
print("  action specifically, not of missing memory alone.")


# ============================================================ 3
rule("3. SPECULATIVE CALLS: CHEAP AND SAFE FOR ONE KIND, NEVER FOR THE OTHER")

print("  An agent uncertain which of several lookups it needs can call ALL")
print("  of them speculatively, at no risk, since none of them changes")
print("  anything:\n")
for item in ["Desk Lamp", "Wireless Mouse", "Standing Desk"]:
    stock = check_inventory(item)
    print(f"    check_inventory({item!r}) -> {stock} (speculative -- no cost beyond the call itself)")

print("\n  The equivalent for a state-changing action would be calling")
print("  issue_refund() 'just to see if it's the right order' -- there is no")
print("  version of this that is safe, because every call has a real effect")
print("  the moment it runs, whether or not it turns out to have been the")
print("  right decision.")


# ============================================================ 4
rule("4. WHAT THIS LAB IS AND IS NOT")

print("  REAL: every world-state comparison above is a genuine before/after")
print("  check against ORDERS and REFUND_LOG -- the empirical verification")
print("  in section 1 and the triple refund in section 2 are measured")
print("  outcomes of actually calling these functions, not asserted claims.")
print("\n  ILLUSTRATIVE: declared_read_only is a flag this lab's own author")
print("  assigned by hand -- a real system needs a real process (code review,")
print("  a convention enforced in how tools are registered) to keep this tag")
print("  accurate as tools change, which section 1's verification step is")
print("  designed to catch when it drifts.")
print("\n  NOT SHOWN: idempotency keys that make a state-changing action safe")
print("  to retry despite not being read-only (M8-L12's own topic); how a")
print("  real system enforces the read-only tag automatically rather than")
print("  trusting a hand-set flag; and combining this classification with")
print("  M8-L10's approval tiers for a complete action-safety policy.")

print("\nDone.")
