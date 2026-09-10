"""M8-L14 lab -- M8-L13 made a single retry within one process's lifetime
safe. This lesson asks what happens when the PROCESS ITSELF is interrupted
mid-task: without a durable checkpoint, resuming means starting over from
scratch, re-running every step including ones already completed -- for a
state-changing step, a real duplicate action. A checkpoint that records
completed steps lets a resumed run skip real, finished work -- but ONLY if
it is written at the right point: after a step's action is confirmed to
have actually happened, never before.

Deterministic. No API key, no network, no third-party dependencies.
Run:  python labs/m8/l14_checkpointing_durable_execution.py
"""

from __future__ import annotations

import sys

sys.stdout.reconfigure(encoding="utf-8")


def rule(title: str) -> None:
    print(f"\n{'=' * 76}\n{title}\n{'=' * 76}")


REFUND_LOG: list[str] = []
EMAILS_SENT: list[str] = []


def search_orders(order_id: str) -> str:
    return f"found order {order_id}"


def get_order(order_id: str) -> dict:
    return {"order_id": order_id, "amount": 40.0}


def issue_refund(order: dict) -> str:
    REFUND_LOG.append(order["order_id"])
    return f"refund of ${order['amount']:.2f} issued for {order['order_id']}"


def send_confirmation_email(order_id: str) -> str:
    EMAILS_SENT.append(order_id)
    return f"confirmation email sent for {order_id}"


TASK_STEPS = ["search_orders", "get_order", "issue_refund", "send_confirmation_email"]


def execute_step(step: str, order_id: str, context: dict):
    if step == "search_orders":
        return search_orders(order_id)
    if step == "get_order":
        return get_order(order_id)
    if step == "issue_refund":
        return issue_refund(context["get_order"])
    if step == "send_confirmation_email":
        return send_confirmation_email(order_id)
    raise ValueError(f"unknown step {step!r}")


# ============================================================ 1
rule("1. NO CHECKPOINT: A CRASH MEANS STARTING OVER FROM SCRATCH")


def run_task_no_checkpoint(order_id: str, crash_after_step: int | None = None) -> dict:
    """[REAL] Every call starts with a completely empty context -- there is
    no durable record of what a PREVIOUS, crashed run already completed."""
    context: dict = {}
    for i, step in enumerate(TASK_STEPS):
        if crash_after_step is not None and i == crash_after_step:
            raise RuntimeError(f"SIMULATED CRASH after completing step {i} ({TASK_STEPS[i - 1]!r})")
        context[step] = execute_step(step, order_id, context)
    return context


print("  First run -- crashes right after issue_refund completes, before")
print("  send_confirmation_email ever runs:")
try:
    run_task_no_checkpoint("O-6001", crash_after_step=3)
except RuntimeError as exc:
    print(f"    {exc}")

print(f"\n  REFUND_LOG after the crash: {REFUND_LOG}")
print("\n  'Restarting' the task from scratch, with no memory of the crashed run:")
run_task_no_checkpoint("O-6001")
print(f"  REFUND_LOG after the restart: {REFUND_LOG}")
print(f"  EMAILS_SENT after the restart: {EMAILS_SENT}")
print("\n  issue_refund() ran TWICE for the same order -- once before the")
print("  crash, once again when the task restarted from the very beginning")
print("  with no record of what had already genuinely happened.")


# ============================================================ 2
rule("2. A CHECKPOINT WRITTEN AFTER EACH STEP LETS A RESUME SKIP REAL WORK")

REFUND_LOG.clear()
EMAILS_SENT.clear()
CHECKPOINT_STORE: dict[str, dict] = {}


def run_task_with_checkpoint(task_id: str, order_id: str, crash_after_step: int | None = None) -> dict:
    """[REAL] Persists each step's result to CHECKPOINT_STORE -- standing in
    for a durable store that would survive a real process crash -- ONLY
    AFTER that step's action has genuinely completed."""
    checkpoint = CHECKPOINT_STORE.setdefault(task_id, {})
    for i, step in enumerate(TASK_STEPS):
        if step in checkpoint:
            continue
        if crash_after_step is not None and i == crash_after_step:
            raise RuntimeError(f"SIMULATED CRASH after completing step {i} ({TASK_STEPS[i - 1]!r})")
        checkpoint[step] = execute_step(step, order_id, checkpoint)
    return checkpoint


print("  First run -- crashes right after issue_refund completes, exactly as")
print("  in section 1, but this time each completed step was checkpointed:")
try:
    run_task_with_checkpoint("task-6002", "O-6002", crash_after_step=3)
except RuntimeError as exc:
    print(f"    {exc}")

print(f"\n  CHECKPOINT_STORE now records: {list(CHECKPOINT_STORE['task-6002'].keys())}")
print(f"  REFUND_LOG after the crash: {REFUND_LOG}")

print("\n  Resuming the SAME task id -- the checkpoint tells the resumed run")
print("  exactly which steps are already genuinely done:")
run_task_with_checkpoint("task-6002", "O-6002")
print(f"  REFUND_LOG after resuming: {REFUND_LOG}")
print(f"  EMAILS_SENT after resuming: {EMAILS_SENT}")
print("\n  issue_refund() ran exactly ONCE this time -- the resumed run")
print("  skipped search_orders, get_order, and issue_refund entirely,")
print("  because the checkpoint already recorded them as complete, and")
print("  executed only the one step that had genuinely never finished.")


# ============================================================ 3
rule("3. WHEN THE CHECKPOINT IS WRITTEN MATTERS AS MUCH AS WHETHER IT EXISTS")

REFUND_LOG.clear()
EMAILS_SENT.clear()
BEFORE_CHECKPOINT_STORE: dict[str, dict] = {}


def run_task_checkpoint_before_action(task_id: str, order_id: str, crash_during_step: int | None = None) -> dict:
    """[REAL, deliberately wrong ordering] Marks a step complete BEFORE
    executing its action, not after -- a real, demonstrated ordering bug,
    not a hypothetical one."""
    checkpoint = BEFORE_CHECKPOINT_STORE.setdefault(task_id, {})
    for i, step in enumerate(TASK_STEPS):
        if step in checkpoint:
            continue
        checkpoint[step] = "marked complete (BEFORE the action actually ran)"
        if crash_during_step is not None and i == crash_during_step:
            raise RuntimeError(f"SIMULATED CRASH DURING step {i} ({step!r}) -- "
                                f"AFTER it was marked complete, BEFORE it actually executed")
        checkpoint[step] = execute_step(step, order_id, checkpoint)
    return checkpoint


print("  Crashing DURING issue_refund itself -- AFTER it was optimistically")
print("  marked complete, but BEFORE execute_step() for it ever ran:")
try:
    run_task_checkpoint_before_action("task-6003", "O-6003", crash_during_step=2)
except RuntimeError as exc:
    print(f"    {exc}")

print(f"\n  REFUND_LOG after the crash: {REFUND_LOG} -- genuinely empty; issue_refund() never ran.")
print(f"  Checkpoint for 'issue_refund': {BEFORE_CHECKPOINT_STORE['task-6003']['issue_refund']!r}")

print("\n  Resuming -- the checkpoint (wrongly) already says issue_refund is done:")
run_task_checkpoint_before_action("task-6003", "O-6003")
print(f"  REFUND_LOG after 'resuming': {REFUND_LOG}")
print(f"  EMAILS_SENT after 'resuming': {EMAILS_SENT}")
print("\n  The resumed run skipped issue_refund entirely, because the")
print("  checkpoint said it was complete -- but it never actually ran. A")
print("  customer's order was never refunded, and nothing in the checkpoint")
print("  reveals this: it looks, from the checkpoint's own record, exactly")
print("  like a task that finished correctly. This is the OPPOSITE failure")
print("  from section 1 -- there, a crash caused a real duplicate action;")
print("  here, checkpointing too early caused a real action to be silently")
print("  skipped altogether.")


# ============================================================ 4
rule("4. THE CORRECT COMBINATION: CHECKPOINT AFTER, AND IDEMPOTENT ANYWAY")

print("  Section 2's ordering (checkpoint written only AFTER a step's action")
print("  genuinely completes) avoids section 3's silent-skip failure. But")
print("  section 2 alone still assumes the checkpoint write itself and the")
print("  action's completion are safely atomic -- a crash occurring in the")
print("  narrow gap between an action finishing and its checkpoint being")
print("  written would leave that step's result uncertain on resume, and")
print("  the resumed run would correctly choose to retry it (since no")
print("  checkpoint entry exists yet).")
print("\n  This is exactly why M8-L12's idempotency key is not optional here:")
print("  a correctly-ordered checkpoint (write after, never before) tells a")
print("  resumed run what NOT to repeat in the common case; an idempotency")
print("  key protects the specific narrow case where the checkpoint and the")
print("  action's completion could not be made perfectly atomic, so a retry")
print("  of that one step is still safe even though it wasn't skipped.")
print("  Durable execution is this combination, not either mechanism alone.")


# ============================================================ 5
rule("5. WHAT THIS LAB IS AND IS NOT")

print("  REAL: every REFUND_LOG entry, every CHECKPOINT_STORE record, and")
print("  the specific contrast between section 1's duplicate refund,")
print("  section 2's correct single refund, and section 3's silently")
print("  skipped refund are genuinely produced by running this code -- not")
print("  scripted to fit a predetermined narrative.")
print("\n  ILLUSTRATIVE: CHECKPOINT_STORE is an in-memory dict standing in")
print("  for a durable store (a database, a persistent queue) that would")
print("  actually survive a real process crash -- this lab simulates a")
print("  crash with a raised exception within the same process, not an")
print("  actual process restart.")
print("\n  NOT SHOWN: how a real system chooses checkpoint granularity (per")
print("  step, per some larger unit of work); how concurrent workers")
print("  resuming the same task id could race with each other; and cost or")
print("  storage-overhead trade-offs of checkpointing frequently versus")
print("  rarely, a natural extension left to the exercises.")

print("\nDone.")
