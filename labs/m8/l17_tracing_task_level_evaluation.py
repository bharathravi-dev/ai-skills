"""M8-L17 lab -- M5-L18 built an evaluation dataset for a single call's
output. An agent's task spans many calls, and every individual call can
succeed -- no exception, a plausible-looking result -- while the TASK ITSELF
still fails, because the steps collectively did the wrong thing. This lesson
builds a trace (a structured record of every step actually taken) and shows
it revealing exactly this: a refund task where search_orders, get_order, and
issue_refund all "succeed," and the refund still goes to the wrong customer.

Deterministic. No API key, no network, no third-party dependencies.
Run:  python labs/m8/l17_tracing_task_level_evaluation.py
"""

from __future__ import annotations

import sys

sys.stdout.reconfigure(encoding="utf-8")


def rule(title: str) -> None:
    print(f"\n{'=' * 76}\n{title}\n{'=' * 76}")


CUSTOMERS = {"Dana Kim": "O-7001", "Dana Lin": "O-7002"}
ORDERS = {
    "O-7001": {"customer": "Dana Kim", "amount": 40.0},
    "O-7002": {"customer": "Dana Lin", "amount": 55.0},
}
REFUND_LOG: list[tuple[str, float]] = []


def search_orders(name_query: str) -> str:
    """[REAL, deliberately naive] Exact match first; falls back to matching
    on first name ONLY if no exact match exists -- a real, plausible
    simplification, not a contrived bug."""
    if name_query in CUSTOMERS:
        return CUSTOMERS[name_query]
    first_word = name_query.split()[0]
    for full_name, order_id in CUSTOMERS.items():
        if full_name.split()[0] == first_word:
            return order_id
    raise ValueError(f"no matching customer for {name_query!r}")


def get_order(order_id: str) -> dict:
    return dict(ORDERS[order_id])


def issue_refund(order_id: str, amount: float) -> str:
    REFUND_LOG.append((order_id, amount))
    return f"refund of ${amount:.2f} issued for {order_id}"


# ============================================================ 1
rule("1. A TRACE: A STRUCTURED RECORD OF WHAT WAS ACTUALLY DONE")

TRACE: list[dict] = []


def traced_call(step_name: str, func, *args):
    """[REAL] Records every call's name, arguments, and result (or error)
    into TRACE -- not just the final output, the entire sequence."""
    try:
        result = func(*args)
        TRACE.append({"step": step_name, "args": args, "result": result, "error": None})
        return result
    except Exception as exc:
        TRACE.append({"step": step_name, "args": args, "result": None, "error": str(exc)})
        raise


def run_refund_task(name_query: str) -> dict:
    order_id = traced_call("search_orders", search_orders, name_query)
    order = traced_call("get_order", get_order, order_id)
    traced_call("issue_refund", issue_refund, order_id, order["amount"])
    return order


print("  Running a refund task for a request that only gave a first name,")
print("  'Dana' -- tracing every step as it happens:\n")
resulting_order = run_refund_task("Dana")
for entry in TRACE:
    print(f"    [{entry['step']}] args={entry['args']} -> "
          f"result={entry['result']!r} error={entry['error']!r}")

print(f"\n  Task's own final result: refunded order belongs to "
      f"{resulting_order['customer']!r}")
print("  The trace is a genuine record of the actual sequence taken -- not")
print("  a summary, not a guess -- available for inspection independent of")
print("  whether the task's outcome turns out to be right or wrong.")


# ============================================================ 2
rule("2. STEP-LEVEL 'ALL GREEN' CAN COEXIST WITH TASK-LEVEL FAILURE")


def step_level_check(trace: list[dict]) -> bool:
    """[REAL] Checks only whether each individual step completed without
    an error -- exactly what a per-call evaluation (M5-L18's own territory)
    would check, applied to each step in isolation."""
    return all(entry["error"] is None for entry in trace)


def task_level_check(order: dict, intended_customer: str) -> bool:
    """[REAL] Checks whether the TASK's actual goal was achieved -- the
    refund went to the customer who was actually supposed to receive it,
    not merely to SOME customer via a technically successful call chain."""
    return order["customer"] == intended_customer


intended_customer = "Dana Lin"   # the real person who actually submitted this request

step_result = step_level_check(TRACE)
task_result = task_level_check(resulting_order, intended_customer)

print(f"  Step-level check (did every call complete without error?): {step_result}")
print(f"  Task-level check (did the refund reach {intended_customer!r}, "
      f"who actually asked?): {task_result}")
print(f"\n  REFUND_LOG: {REFUND_LOG}")
print(f"  The refund went to {resulting_order['customer']!r} instead of "
      f"{intended_customer!r}.")

print("\n  Every individual step genuinely succeeded -- search_orders found A")
print("  real order, get_order returned real details, issue_refund genuinely")
print("  processed a real refund. A step-level evaluation checking only for")
print("  errors would report this task as fully successful. It was not: the")
print("  wrong customer was refunded, and only a TASK-level check, comparing")
print("  the actual outcome against what was actually intended, catches it.")


# ============================================================ 3
rule("3. USING THE TRACE TO DIAGNOSE WHERE THINGS ACTUALLY WENT WRONG")

print("  With task-level failure confirmed, the trace answers WHERE the")
print("  divergence happened -- not by guessing, but by reading the actual")
print("  recorded step:\n")
search_step = next(e for e in TRACE if e["step"] == "search_orders")
print(f"    [search_orders] called with {search_step['args']} -> "
      f"returned {search_step['result']!r}")
print(f"    Real intended order (for {intended_customer!r}): "
      f"{CUSTOMERS[intended_customer]!r}")
print(f"    Do they match? {search_step['result'] == CUSTOMERS[intended_customer]}")

print("\n  The trace pinpoints search_orders specifically -- get_order and")
print("  issue_refund both correctly and faithfully acted on WHATEVER order")
print("  id search_orders handed them; neither of those steps did anything")
print("  wrong given their own input. The task-level failure traces back to")
print("  exactly one step's decision, visible directly in the trace record,")
print("  not inferred after the fact.")


# ============================================================ 4
rule("4. WHAT THIS LAB IS AND IS NOT")

print("  REAL: every trace entry, every step-level and task-level check")
print("  result above is genuinely computed by running this code -- the")
print("  wrong-customer refund is a real, measured outcome of a real")
print("  ambiguous-name lookup, not a scripted narrative.")
print("\n  ILLUSTRATIVE: search_orders()'s first-name-only fallback is a")
print("  small, deliberately realistic simplification standing in for a")
print("  real fuzzy-matching or search ambiguity -- a real system's own")
print("  retrieval logic could fail in many other specific ways.")
print("\n  NOT SHOWN: tracing across multiple agents or a distributed system")
print("  (M8-L09's own multi-agent territory, now needing correlated")
print("  traces); building a full evaluation DATASET of many traced tasks")
print("  (M5-L18's own topic, applied at the task level); and automated")
print("  tools that surface a likely-culprit step without a human reading")
print("  the trace directly, as this lab's section 3 does by hand.")

print("\nDone.")
