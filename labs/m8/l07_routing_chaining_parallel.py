"""M8-L07 lab -- three different ways to arrange more than one step inside a
single agent turn, each suited to a different relationship between the
steps: ROUTING picks exactly ONE of several mutually exclusive paths;
CHAINING runs steps in a fixed order because each one's input is the
previous one's output; PARALLEL EXECUTION runs steps that don't depend on
each other at the same time, saving real wall-clock time. Each shape is
demonstrated against what happens when it's used incorrectly for the wrong
relationship.

Deterministic. No API key, no network, no third-party dependencies (uses
only the standard library's `concurrent.futures` and `time` for section 3's
real, measured timing).
Run:  python labs/m8/l07_routing_chaining_parallel.py
"""

from __future__ import annotations

import sys
import time
from concurrent.futures import ThreadPoolExecutor

sys.stdout.reconfigure(encoding="utf-8")


def rule(title: str) -> None:
    print(f"\n{'=' * 76}\n{title}\n{'=' * 76}")


# ============================================================ 1
rule("1. ROUTING: EXACTLY ONE OF SEVERAL MUTUALLY EXCLUSIVE PATHS")

QUERIES = [
    ("What's my account balance?", "billing"),
    ("My app keeps crashing on startup", "technical"),
    ("What are your support hours?", "general"),
]


def classify_query(query: str) -> str:
    """[ILLUSTRATIVE] A small keyword rule standing in for a real router's
    judgment -- a real system uses an actual model call to classify intent,
    not this fixed list."""
    text = query.lower()
    if "balance" in text or "account" in text or "charge" in text:
        return "billing"
    if "crash" in text or "error" in text or "bug" in text:
        return "technical"
    return "general"


def handle_billing(query: str) -> str:
    return "Billing: your current balance is $0.00 and no charges are pending."


def handle_technical(query: str) -> str:
    return "Technical: please try reinstalling the app; if it persists, share your device logs."


def handle_general(query: str) -> str:
    return "General: our support hours are 9am-6pm, Monday through Friday."


ROUTES = {"billing": handle_billing, "technical": handle_technical, "general": handle_general}
CALL_COUNT = {"billing": 0, "technical": 0, "general": 0}


def route(query: str) -> str:
    category = classify_query(query)
    CALL_COUNT[category] += 1
    return ROUTES[category](query)


print("  Routing each query to exactly ONE specialized handler:\n")
for query, expected in QUERIES:
    result = route(query)
    print(f"  Query: {query!r}")
    print(f"    -> routed to {classify_query(query)!r}: {result}\n")

print(f"  Calls made per handler: {CALL_COUNT} -- exactly one call, one handler, per query.")

print("\n  Contrast: a system with NO routing that always uses the general")
print("  handler for every query:")
for query, expected in QUERIES:
    print(f"    {query!r} -> {handle_general(query)}")
print("\n  The billing and technical queries get the SAME generic response as")
print("  the hours question -- a real quality loss, not a hypothetical one.")

print("\n  Contrast: a system with NO routing that calls EVERY handler for")
print("  every query, just in case:")
total_calls_no_routing = len(QUERIES) * len(ROUTES)
total_calls_with_routing = sum(CALL_COUNT.values())
print(f"    Calls made: {total_calls_no_routing} (3 queries x 3 handlers each)")
print(f"    Calls routing actually needed: {total_calls_with_routing} (1 per query)")
print(f"    {total_calls_no_routing / total_calls_with_routing:.0f}x more calls than routing required --")
print("    for identical final answers, since only one handler's output is")
print("    ever actually used per query.")


# ============================================================ 2
rule("2. CHAINING: A FIXED ORDER, BECAUSE EACH STEP NEEDS THE LAST ONE'S OUTPUT")

ORDERS = {"O-1001": {"customer": "Dana Kim", "amount": 40.0, "days_since_purchase": 10}}


def get_order(order_id: str) -> dict:
    return ORDERS[order_id]


def check_eligibility(order: dict) -> dict:
    """[REAL] Genuinely needs the ORDER's data as input -- there is no
    version of this function that could run before get_order()."""
    eligible = order["days_since_purchase"] <= 30
    return {"eligible": eligible, "max_refund": order["amount"] if eligible else 0.0}


def issue_refund(order_id: str, amount: float) -> str:
    """[REAL] Genuinely needs the ELIGIBILITY decision's output -- there is
    no version of this function that could run before check_eligibility()."""
    if amount <= 0:
        raise ValueError("cannot issue a non-positive refund")
    return f"refund of ${amount:.2f} issued for {order_id}"


print("  Running the chain in its required order:")
order = get_order("O-1001")
print(f"    get_order('O-1001') -> {order}")
eligibility = check_eligibility(order)
print(f"    check_eligibility(order) -> {eligibility}")
if eligibility["eligible"]:
    result = issue_refund("O-1001", eligibility["max_refund"])
    print(f"    issue_refund('O-1001', {eligibility['max_refund']}) -> {result}")

print("\n  Attempting to skip the dependency order -- issue_refund() called")
print("  directly, without ever running check_eligibility() first:")
try:
    bad_amount = None
    issue_refund("O-1001", bad_amount)
except TypeError as exc:
    print(f"    issue_refund('O-1001', None) RAISED {exc!r}")

print("\n  Attempting to run check_eligibility() BEFORE get_order() -- there is")
print("  no order data yet to check eligibility against:")
try:
    check_eligibility(None)
except TypeError as exc:
    print(f"    check_eligibility(None) RAISED {exc!r}")

print("\n  Both failures are genuine, not staged -- each step's function")
print("  signature requires a real value only the PREVIOUS step produces.")
print("  Unlike routing's alternatives or section 3's independent steps, a")
print("  chain's order is not a style choice: it is a real data dependency.")


# ============================================================ 3
rule("3. PARALLEL EXECUTION: INDEPENDENT STEPS, RUN AT THE SAME TIME")


def check_warehouse_stock(warehouse: str) -> int:
    """[REAL delay, ILLUSTRATIVE call] time.sleep() stands in for a real
    network call to a warehouse inventory system -- genuinely blocking,
    genuinely timed, but not an actual network request."""
    time.sleep(0.15)
    return {"East": 12, "Central": 0, "West": 7}[warehouse]


WAREHOUSES = ["East", "Central", "West"]

print("  Checking stock across 3 independent warehouses -- none of these")
print("  calls needs any other one's result:\n")

t0 = time.perf_counter()
sequential_results = {w: check_warehouse_stock(w) for w in WAREHOUSES}
sequential_time = time.perf_counter() - t0
print(f"  SEQUENTIAL: {sequential_results}  ({sequential_time * 1000:.0f}ms)")

t0 = time.perf_counter()
with ThreadPoolExecutor(max_workers=3) as pool:
    parallel_results = dict(zip(WAREHOUSES, pool.map(check_warehouse_stock, WAREHOUSES)))
parallel_time = time.perf_counter() - t0
print(f"  PARALLEL:   {parallel_results}  ({parallel_time * 1000:.0f}ms)")

print(f"\n  Same 3 calls, same results, {sequential_time / parallel_time:.1f}x faster wall-clock time --")
print("  a REAL, measured speedup, because none of these three calls needed")
print("  any other one's output. Chaining these same three calls (as in")
print("  section 2) would have been WRONG here -- there is no dependency to")
print("  respect, only unnecessary waiting.")


# ============================================================ 4
rule("4. A REUSABLE FRAMEWORK: WHICH SHAPE FITS WHICH RELATIONSHIP")


def recommend_shape(mutually_exclusive: bool, has_dependency: bool) -> str:
    """[REAL] Two questions settle it: are the candidate steps alternatives
    where only one applies, or a fixed sequence where each needs the last
    one's output, or neither (independent, all needed)?"""
    if mutually_exclusive:
        return "ROUTING (pick exactly one path)"
    if has_dependency:
        return "CHAINING (fixed order, each step needs the last one's output)"
    return "PARALLEL (independent steps, all needed, order doesn't matter)"


CASES = [
    ("Classifying a query as billing/technical/general, then answering only that way", True, False),
    ("Fetching an order, then checking its eligibility, then refunding it", False, True),
    ("Checking stock across 3 independent, unrelated warehouses", False, False),
]
for description, mutually_exclusive, has_dependency in CASES:
    print(f"    {recommend_shape(mutually_exclusive, has_dependency)}")
    print(f"      -- {description}\n")

print("  This matches exactly what sections 1-3 measured: routing avoided")
print(f"  {total_calls_no_routing - total_calls_with_routing} unnecessary handler calls by picking one path;")
print("  chaining's dependency was real enough to raise a genuine exception")
print("  when broken; and parallel execution turned a real dependency-free")
print(f"  wait into a measured {sequential_time / parallel_time:.1f}x speedup. Using the wrong shape for a")
print("  given relationship either wastes work (routing where you chain or")
print("  parallelize), breaks correctness (chaining treated as parallel), or")
print("  wastes time (parallel-eligible steps run as a chain anyway).")


# ============================================================ 5
rule("5. WHAT THIS LAB IS AND IS NOT")

print("  REAL: every call count in section 1, every raised exception in")
print("  section 2, and every measured timing in section 3 is genuinely")
print("  produced by running the code -- the parallel speedup is real")
print("  wall-clock time measured on this machine, not a claimed ratio.")
print("\n  ILLUSTRATIVE: classify_query() is a small, hand-coded stand-in for")
print("  a real router's judgment -- a real system uses an actual model")
print("  call or a trained classifier, not a fixed keyword list. Section 3's")
print("  time.sleep() calls stand in for real network requests -- genuinely")
print("  blocking and genuinely timed, but not real I/O.")
print("\n  NOT SHOWN: combining these three shapes within one larger system")
print("  (a route that itself contains a parallel step, say); handling a")
print("  failure in ONE of several parallel calls without losing the others'")
print("  results (M8-L13's retry/recovery topic); and orchestrating many")
print("  agents rather than many steps within one (M8-L08's own topic).")

print("\nDone.")
