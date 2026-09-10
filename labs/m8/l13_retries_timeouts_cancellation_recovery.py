"""M8-L13 lab -- M2-L14 already built real backoff/jitter/circuit-breaker
discipline for retrying an HTTP client call; M8-L12 built the idempotency
key that makes a retry of a state-changing action safe. This lesson wires
both into an agent's own tool-execution step and adds three things neither
earlier lesson covered: a TIMEOUT that gives up waiting on a hung call
rather than blocking forever, a CANCELLATION check that only some actions
can actually honor once started, and a RECOVERY path that reports an honest
failure instead of silently pretending a step succeeded.

Deterministic. No API key, no network, no third-party dependencies (uses
only the standard library's `concurrent.futures` and `time`).
Run:  python labs/m8/l13_retries_timeouts_cancellation_recovery.py
"""

from __future__ import annotations

import sys
import time
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeoutError

sys.stdout.reconfigure(encoding="utf-8")


def rule(title: str) -> None:
    print(f"\n{'=' * 76}\n{title}\n{'=' * 76}")


# ============================================================ 1
rule("1. A REAL TIMEOUT: GIVING UP ON A HUNG CALL, MEASURED")


def slow_check_inventory(item: str) -> int:
    time.sleep(0.6)   # stands in for a call that has genuinely hung
    return 5


def call_with_timeout(func, args: tuple, timeout_seconds: float):
    """[REAL] Genuinely bounds how long a single call is waited on --
    using a real thread and a real timeout, not a simulated delay. Uses the
    pool directly, WITHOUT a `with` block: exiting a `with ThreadPoolExecutor`
    block calls shutdown(wait=True) by default, which would block until the
    hung background thread actually finishes -- silently erasing the very
    timeout this function exists to enforce. shutdown(wait=False) lets the
    caller return immediately at the real timeout, leaving the orphaned
    thread to finish (or not) on its own."""
    pool = ThreadPoolExecutor(max_workers=1)
    future = pool.submit(func, *args)
    try:
        result = future.result(timeout=timeout_seconds)
        pool.shutdown(wait=False)
        return result, None
    except FutureTimeoutError:
        pool.shutdown(wait=False)
        return None, "TIMED OUT"


t0 = time.perf_counter()
result, error = call_with_timeout(slow_check_inventory, ("Desk Lamp",), timeout_seconds=0.2)
elapsed = time.perf_counter() - t0
print(f"  call_with_timeout(slow_check_inventory, timeout=0.2s) -> "
      f"result={result!r}, error={error!r}")
print(f"  Actually waited: {elapsed * 1000:.0f}ms (the call itself takes 600ms to finish)")
print("\n  The caller gave up at the timeout, not at whenever the underlying")
print("  call eventually finishes -- a real, measured bound, not a claim.")
print("  The underlying thread is still running in the background; the")
print("  TIMEOUT decision is about how long the CALLER waits, not about")
print("  stopping the work itself (that is section 3's separate topic).")


# ============================================================ 2
rule("2. RETRY WITH REAL BACKOFF, PROTECTED BY AN IDEMPOTENCY KEY")

REFUND_LOG: list[tuple[str, float]] = []
IDEMPOTENCY_STORE: dict[str, str] = {}
FLAKY_ATTEMPTS = {"n": 0}


def flaky_issue_refund(order_id: str, amount: float) -> str:
    """[REAL] Genuinely fails (raises) on its first two calls, succeeding
    only on the third -- a real, deterministic stand-in for a transient
    failure (M2-L14's own territory), not a claim about real network
    behavior."""
    FLAKY_ATTEMPTS["n"] += 1
    if FLAKY_ATTEMPTS["n"] < 3:
        raise ConnectionError(f"simulated transient failure (attempt {FLAKY_ATTEMPTS['n']})")
    REFUND_LOG.append((order_id, amount))
    return f"refund of ${amount:.2f} issued for {order_id}"


def retry_with_backoff(idempotency_key: str, order_id: str, amount: float,
                        max_retries: int = 5, base_delay: float = 0.05) -> str:
    """[REAL] M2-L14's own exponential-backoff shape, applied here, combined
    with M8-L12's idempotency key so a SUCCESSFUL prior attempt is never
    re-executed, and a retry only ever re-attempts a call that has not yet
    succeeded."""
    if idempotency_key in IDEMPOTENCY_STORE:
        return f"{IDEMPOTENCY_STORE[idempotency_key]} [cached, no retry needed]"
    delay = base_delay
    for attempt in range(1, max_retries + 1):
        try:
            result = flaky_issue_refund(order_id, amount)
            IDEMPOTENCY_STORE[idempotency_key] = result
            return result
        except ConnectionError as exc:
            print(f"    attempt {attempt} failed ({exc}) -- waiting {delay * 1000:.0f}ms before retry")
            if attempt == max_retries:
                raise
            time.sleep(delay)
            delay *= 2
    raise RuntimeError("unreachable")


print("  Retrying a flaky refund call with real, measured backoff:\n")
t0 = time.perf_counter()
final_result = retry_with_backoff("req-retry-1", "O-5001", 40.0)
total_elapsed = time.perf_counter() - t0
print(f"\n  Final result: {final_result!r}")
print(f"  Total wall-clock time across all attempts and waits: {total_elapsed * 1000:.0f}ms")
print(f"  REFUND_LOG: {REFUND_LOG} -- exactly one entry, from the one attempt that succeeded.")

print("\n  Retrying the SAME logical request again (same idempotency key):")
repeat_result = retry_with_backoff("req-retry-1", "O-5001", 40.0)
print(f"    retry_with_backoff('req-retry-1', ...) -> {repeat_result!r}")
print(f"  REFUND_LOG unchanged: {REFUND_LOG}")


# ============================================================ 3
rule("3. CANCELLATION: SOME ACTIONS CAN STOP MID-WAY; SOME CANNOT")


def cancellable_bulk_check(cancel_flag: dict, items: list[str]) -> list[str]:
    """[REAL] A genuinely cancellable action -- it checks an EXTERNAL flag
    between steps and can stop early, returning real partial progress. The
    flag is set by the caller, not this function -- exactly how a real
    cancellation request would arrive, from outside the running action."""
    checked = []
    for item in items:
        if cancel_flag.get("cancelled"):
            return checked
        checked.append(item)
    return checked


cancel_flag = {"cancelled": False}
items_to_check = ["Desk Lamp", "Wireless Mouse", "Standing Desk", "Monitor", "Keyboard"]
CANCEL_AFTER_ITEMS = 2


def items_with_cancellation_arriving_at(items: list[str], cancel_flag: dict, cancel_after: int):
    """[REAL] Sets the SAME external cancel_flag cancellable_bulk_check()
    checks, as a side effect during iteration, deterministically timed to
    the item index rather than to wall-clock delay -- so this demonstration
    reproduces exactly on every run. A real cancellation request arriving
    from another thread or process mid-execution would flip the identical
    flag; only how the flag gets set differs, not how it is checked."""
    for i, item in enumerate(items):
        if i == cancel_after:
            cancel_flag["cancelled"] = True
        yield item


checked_before_cancel = cancellable_bulk_check(
    cancel_flag, items_with_cancellation_arriving_at(items_to_check, cancel_flag, CANCEL_AFTER_ITEMS))

print(f"  cancellable_bulk_check() cancelled mid-way -- items actually checked: "
      f"{checked_before_cancel} (of {len(items_to_check)} requested)")

print("\n  Contrast: issue_refund() and flaky_issue_refund() have NO cancellation")
print("  point at all -- each is a single, atomic operation. Once called,")
print("  there is no partial state to stop at; it either has not started")
print("  (safe to simply not call) or has already completed (too late to")
print("  cancel). Treating a state-changing action as if it could be safely")
print("  interrupted mid-way, when its own logic has no such checkpoint, is")
print("  a real design error, not a matter of adding a flag after the fact.")


# ============================================================ 4
rule("4. RECOVERY: AN HONEST FAILURE, NOT A SILENT ONE")

ALWAYS_FAILS_ATTEMPTS = {"n": 0}


def always_fails_refund(order_id: str, amount: float) -> str:
    ALWAYS_FAILS_ATTEMPTS["n"] += 1
    raise ConnectionError("simulated permanent failure")


def honest_recovery(order_id: str, amount: float, max_retries: int = 3) -> str:
    """[REAL] Exhausts retries, then reports an HONEST, specific failure --
    the caller can see exactly what happened and route it (to M8-L10's
    human escalation, for instance), rather than being told nothing went
    wrong."""
    delay = 0.02
    for attempt in range(1, max_retries + 1):
        try:
            return always_fails_refund(order_id, amount)
        except ConnectionError:
            if attempt == max_retries:
                return f"FAILED after {max_retries} attempts -- no refund was issued for {order_id}"
            time.sleep(delay)
            delay *= 2


def dishonest_recovery(order_id: str, amount: float, max_retries: int = 3) -> str:
    """[REAL, deliberately wrong] Exhausts retries and then returns a
    success-shaped message anyway -- a real, demonstrated version of
    silently masking a failure instead of surfacing it."""
    delay = 0.02
    for attempt in range(1, max_retries + 1):
        try:
            return always_fails_refund(order_id, amount)
        except ConnectionError:
            if attempt == max_retries:
                return f"refund of ${amount:.2f} issued for {order_id}"
            time.sleep(delay)
            delay *= 2


honest_result = honest_recovery("O-5002", 60.0)
print(f"  Honest recovery:    {honest_result!r}")
print(f"  REFUND_LOG contains an entry for O-5002? {'O-5002' in [o for o, _ in REFUND_LOG]}")

dishonest_result = dishonest_recovery("O-5003", 60.0)
print(f"\n  Dishonest recovery: {dishonest_result!r}")
print(f"  REFUND_LOG contains an entry for O-5003? {'O-5003' in [o for o, _ in REFUND_LOG]}")

print("\n  Both functions retried the identical, permanently-failing action")
print("  the identical number of times. The dishonest version's final")
print("  message is INDISTINGUISHABLE, in its own text, from a real success")
print("  -- but no refund was ever recorded. A caller (or a human) reading")
print("  only that string has no way to tell the two apart without checking")
print("  the underlying system of record directly.")


# ============================================================ 5
rule("5. WHAT THIS LAB IS AND IS NOT")

print("  REAL: the timeout in section 1 is a genuine, measured wall-clock")
print("  bound; the backoff delays in section 2 genuinely double and are")
print("  genuinely waited; the cancellation in section 3 genuinely stops a")
print("  real loop mid-way based on a real, externally-set flag;")
print("  and both recovery paths in section 4 genuinely exhaust real")
print("  retries against a function that genuinely always raises.")
print("\n  ILLUSTRATIVE: flaky_issue_refund() and always_fails_refund() are")
print("  small, deterministic stand-ins for real transient and permanent")
print("  failures -- a real system's actual failure modes and timing would")
print("  differ. The specific delay values are this lesson's own")
print("  illustration, not a tuned recommendation for any real system.")
print("\n  NOT SHOWN: M2-L14's own jitter and circuit-breaker mechanisms in")
print("  full (referenced, not rebuilt here); how a real system decides")
print("  which errors are worth retrying at all versus failing immediately;")
print("  and durable checkpointing across a process restart mid-retry")
print("  (M8-L14's own topic).")

print("\nDone.")
