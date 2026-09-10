"""M8-L03 lab -- M8-L01 and M8-L02 each hand-rolled a loop specific to one
scenario. This lesson builds the general machinery underneath both: a `Tool`
wrapper (name, function, description -- M5-L08's own vocabulary) and one
`run_tool_loop()` that works for ANY set of tools and ANY decision function,
handling two things a scenario-specific loop can get away with ignoring: a
proposed tool name that doesn't exist, and a tool call that raises. The same
loop, unmodified, drives two unrelated domains -- proof it is actually
general, not just refactored.

Deterministic. No API key, no network, no third-party dependencies.
Run:  python labs/m8/l03_tool_execution_loop.py
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
    """[REAL] M5-L08's own vocabulary, made concrete: a name the decision
    step can refer to, the actual function invoked, and a description (not
    used by this mock loop, but present because a real model needs it to
    know the tool exists at all)."""
    name: str
    func: Callable[..., Any]
    description: str


def run_tool_loop(
    tools: list[Tool],
    decide_next: Callable[[dict], tuple[str, dict]],
    max_steps: int = 6,
) -> list[str]:
    """[REAL, general-purpose] Works for ANY tools list and ANY decide_next
    function -- nothing here is specific to refunds, trips, or any other
    domain. decide_next(observed) returns (action_name, action_args);
    "respond" stops the loop. An unrecognized action_name, or a tool call
    that raises, is CAUGHT and fed back into `observed` as an error --
    never crashes the loop -- because a real model, shown that error as its
    next observation, could choose to recover from it (M8-L01's decision-
    point pattern, now applied to failures specifically)."""
    tool_by_name = {t.name: t for t in tools}
    trace: list[str] = []
    observed: dict[str, Any] = {}

    for step in range(1, max_steps + 1):
        action_name, action_args = decide_next(observed)

        if action_name == "respond":
            trace.append(f"[step {step}] respond -- loop stops")
            return trace

        if action_name not in tool_by_name:
            observed["last_error"] = f"unknown tool {action_name!r}"
            trace.append(f"[step {step}] REQUESTED unknown tool {action_name!r} "
                         f"-- caught, fed back as an observation, loop continues")
            continue

        tool = tool_by_name[action_name]
        try:
            result = tool.func(**action_args)
            observed[action_name] = result
            trace.append(f"[step {step}] {action_name}({action_args}) -> {result!r}")
        except Exception as exc:
            observed["last_error"] = f"{action_name} raised {exc}"
            trace.append(f"[step {step}] {action_name}({action_args}) RAISED "
                         f"{exc!r} -- caught, fed back as an observation, loop continues")

    trace.append(f"[step {max_steps}] STOPPED: reached max_steps={max_steps} "
                  f"without a final response")
    return trace


# ============================================================ 1
rule("1. WHAT A TOOL CALL ACTUALLY IS: A NAME PLUS ARGUMENTS")

print("  M5-L08's own definition: 'Tool call: The model's request -- a tool")
print("  name plus arguments.' That's the whole shape decide_next() must")
print("  produce: (action_name, action_args). Everything else in this lab is")
print("  what a loop does with that shape once it has it.")


# ============================================================ 2
rule("2. SCENARIO A: SUPPORT ASSISTANT -- BOTH ERROR PATHS, DELIBERATELY TRIGGERED")

CUSTOMER_ORDERS = {"Dana Kim": "O-1001"}
ORDERS = {"O-1001": {"item": "Wireless Mouse", "amount": 25.0}}


def search_orders(customer_name: str) -> str:
    return CUSTOMER_ORDERS[customer_name]


def get_order(order_id: str) -> dict:
    """[REAL] Raises on an unknown id, rather than returning None -- so this
    lab can demonstrate the loop's real exception handling, not a special
    case bolted on for the demo."""
    if order_id not in ORDERS:
        raise ValueError(f"no such order: {order_id!r}")
    return ORDERS[order_id]


def issue_refund(order_id: str, amount: float) -> str:
    return f"refund of ${amount:.2f} issued for {order_id}"


SUPPORT_TOOLS = [
    Tool("search_orders", search_orders, "Find a customer's order id by name"),
    Tool("get_order", get_order, "Fetch order details by order id"),
    Tool("issue_refund", issue_refund, "Issue a refund for an order id"),
]


def make_support_decider() -> Callable[[dict], tuple[str, dict]]:
    """[ILLUSTRATIVE, scripted] A stand-in for a real model's choices,
    deliberately scripted to hit both error paths: step 1 requests a tool
    that was never registered (a plausible-sounding hallucinated name);
    step 3 requests a real tool with a wrong id (a plausible mistake, like
    acting on a stale or misremembered value). A real model, shown each
    error as its next observation, could choose how to recover -- this
    script simply IS the recovery, standing in for that same capability."""
    calls = {"n": 0}

    def decide_next(observed: dict) -> tuple[str, dict]:
        calls["n"] += 1
        n = calls["n"]
        if n == 1:
            return "lookup_customer_history", {"customer_name": "Dana Kim"}
        if n == 2:
            return "search_orders", {"customer_name": "Dana Kim"}
        if n == 3:
            return "get_order", {"order_id": "O-9999"}
        if n == 4:
            return "get_order", {"order_id": observed["search_orders"]}
        if n == 5:
            return "issue_refund", {"order_id": observed["search_orders"],
                                     "amount": observed["get_order"]["amount"]}
        return "respond", {}

    return decide_next


print("  Running run_tool_loop() against the support-assistant tools:\n")
support_trace = run_tool_loop(SUPPORT_TOOLS, make_support_decider())
for line in support_trace:
    print(f"  {line}")

print("\n  Step 1's unknown tool and step 3's invalid order id both reached")
print("  the SAME general except/unknown-name handling in run_tool_loop() --")
print("  no scenario-specific error handling was written for either one.")
print("  The loop recovered and completed the refund anyway, because each")
print("  error became an observation instead of a crash.")


# ============================================================ 3
rule("3. SCENARIO B: A COMPLETELY DIFFERENT DOMAIN, THE SAME LOOP, UNCHANGED")


def get_distance(origin: str, destination: str) -> float:
    DISTANCES = {("Springfield", "Capital City"): 187.0}
    return DISTANCES[(origin, destination)]


def get_fuel_price() -> float:
    return 3.79


def compute_trip_cost(distance: float, fuel_price: float, mpg: float = 28.0) -> float:
    return round(distance / mpg * fuel_price, 2)


TRIP_TOOLS = [
    Tool("get_distance", get_distance, "Distance in miles between two cities"),
    Tool("get_fuel_price", get_fuel_price, "Current fuel price per gallon"),
    Tool("compute_trip_cost", compute_trip_cost, "Estimated fuel cost for a trip"),
]


def make_trip_decider() -> Callable[[dict], tuple[str, dict]]:
    calls = {"n": 0}

    def decide_next(observed: dict) -> tuple[str, dict]:
        calls["n"] += 1
        n = calls["n"]
        if n == 1:
            return "get_distance", {"origin": "Springfield", "destination": "Capital City"}
        if n == 2:
            return "get_fuel_price", {}
        if n == 3:
            return "compute_trip_cost", {"distance": observed["get_distance"],
                                          "fuel_price": observed["get_fuel_price"]}
        return "respond", {}

    return decide_next


print("  Running the IDENTICAL run_tool_loop() function against an unrelated")
print("  trip-cost domain -- zero changes to the loop itself:\n")
trip_trace = run_tool_loop(TRIP_TOOLS, make_trip_decider())
for line in trip_trace:
    print(f"  {line}")

print("\n  Nothing about run_tool_loop() mentions orders, refunds, distances,")
print("  or fuel -- it only knows about Tool objects and (name, args) pairs.")
print("  That is what 'general-purpose, written from scratch' means here: the")
print("  SAME function, unmodified, correctly drives two domains that share")
print("  no code and no data.")


# ============================================================ 4
rule("4. THE SAFETY BOUND: A DECIDER THAT NEVER SAYS 'RESPOND'")


def make_runaway_decider() -> Callable[[dict], tuple[str, dict]]:
    """[ILLUSTRATIVE] Always proposes another get_fuel_price() call -- a
    stand-in for a model stuck in a loop, never reaching a stopping
    condition (M8-L15's own topic, previewed here at the mechanism level)."""
    def decide_next(observed: dict) -> tuple[str, dict]:
        return "get_fuel_price", {}
    return decide_next


print("  A decider that always proposes another tool call, run with a real,")
print("  low max_steps bound:\n")
runaway_trace = run_tool_loop(TRIP_TOOLS, make_runaway_decider(), max_steps=3)
for line in runaway_trace:
    print(f"  {line}")

print("\n  The loop made exactly 3 calls, then stopped itself -- not because")
print("  the decider ever chose to stop, but because max_steps is enforced by")
print("  run_tool_loop() itself, independent of what any decision function")
print("  returns. This is the same bound M8-L01's run_agent() applied ad hoc;")
print("  here it is a first-class, reusable parameter of the general loop.")


# ============================================================ 5
rule("5. WHAT THIS LAB IS AND IS NOT")

print("  REAL: run_tool_loop() is genuinely general-purpose -- sections 2 and")
print("  3 run the IDENTICAL function against two unrelated tool sets with no")
print("  changes to the loop. Both error paths in section 2 (unknown tool")
print("  name, a tool call that raises) are genuinely caught by the loop's")
print("  own except/lookup logic, not scripted around. Section 4's step count")
print("  is a real, measured consequence of max_steps.")
print("\n  ILLUSTRATIVE: decide_next() in every scenario is a small, scripted")
print("  stand-in for a real model's choices -- a real system replaces this")
print("  with an actual model call reading `observed` and the available")
print("  tools' descriptions, then choosing what to do next (M8-L04 covers")
print("  the plan/act/observe/stop shape of that choice in more depth).")
print("\n  NOT SHOWN: validating a tool's ARGUMENTS against a schema before")
print("  calling it (M8-L05); state and memory carried across separate")
print("  conversations, not just within one loop's run (M8-L06); and human")
print("  approval gates before a high-stakes tool call executes (M8-L10).")

print("\nDone.")
