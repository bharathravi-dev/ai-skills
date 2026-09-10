"""M8-L15 lab -- M8-L03's max_steps is a real bound, but a step COUNT limit
alone says nothing about DOLLAR cost when different steps cost wildly
different amounts (M5-L15's own per-request accounting, now summed across
an entire agent run). This lesson adds two things a step limit alone
misses: a real cost budget, checked before each step, and runaway
detection, which recognizes a loop repeating the same unproductive action
and stops early -- before burning through the full step or cost budget for
no progress at all.

Deterministic. No API key, no network, no third-party dependencies.
Run:  python labs/m8/l15_step_limits_cost_budgets_runaway.py
"""

from __future__ import annotations

import sys

sys.stdout.reconfigure(encoding="utf-8")


def rule(title: str) -> None:
    print(f"\n{'=' * 76}\n{title}\n{'=' * 76}")


TOOL_COSTS = {"cheap_lookup": 0.01, "expensive_generation": 2.00}


# ============================================================ 1
rule("1. A STEP LIMIT ALONE SAYS NOTHING ABOUT DOLLAR COST")


def run_loop_step_limit_only(decide_next, max_steps: int = 10) -> tuple[int, float]:
    """[REAL] Bounds step COUNT only -- exactly M8-L03's max_steps,
    unmodified in spirit. Nothing here looks at what each step actually
    costs."""
    total_cost = 0.0
    steps_taken = 0
    for _ in range(max_steps):
        action = decide_next()
        if action == "stop":
            break
        total_cost += TOOL_COSTS[action]
        steps_taken += 1
    return steps_taken, total_cost


def always_expensive() -> str:
    return "expensive_generation"


def always_cheap() -> str:
    return "cheap_lookup"


cheap_steps, cheap_cost = run_loop_step_limit_only(always_cheap, max_steps=10)
expensive_steps, expensive_cost = run_loop_step_limit_only(always_expensive, max_steps=10)

print(f"  10 steps, always the cheap action:      {cheap_steps} steps, ${cheap_cost:.2f} total")
print(f"  10 steps, always the expensive action:  {expensive_steps} steps, ${expensive_cost:.2f} total")
print(f"\n  Both runs respected the IDENTICAL max_steps=10 limit -- and produced")
print(f"  a {expensive_cost / cheap_cost:.0f}x difference in real dollar cost. A step-count limit alone")
print("  cannot distinguish these two cases; it was never designed to.")


# ============================================================ 2
rule("2. A REAL COST BUDGET, CHECKED BEFORE EACH STEP")


def run_loop_with_cost_budget(decide_next, max_steps: int = 10, max_cost: float = 5.00):
    """[REAL] Checks the NEXT step's cost against the REMAINING budget
    before executing it -- stopping the loop the moment a step would
    exceed what's left, regardless of how few steps have run."""
    total_cost = 0.0
    trace = []
    for i in range(1, max_steps + 1):
        action = decide_next()
        if action == "stop":
            trace.append(f"step {i}: decider chose to stop")
            break
        next_cost = TOOL_COSTS[action]
        if total_cost + next_cost > max_cost:
            trace.append(f"step {i}: BUDGET STOP -- {action!r} would cost ${next_cost:.2f}, "
                         f"only ${max_cost - total_cost:.2f} of the ${max_cost:.2f} budget remains")
            break
        total_cost += next_cost
        trace.append(f"step {i}: {action} -> running cost ${total_cost:.2f}")
    return total_cost, trace


print("  Running the SAME always-expensive decider, this time with a real")
print(f"  ${5.00:.2f} cost budget instead of only a step count:\n")
budget_cost, budget_trace = run_loop_with_cost_budget(always_expensive, max_steps=10, max_cost=5.00)
for line in budget_trace:
    print(f"    {line}")
print(f"\n  Final cost: ${budget_cost:.2f} -- the loop stopped itself after 2 real")
print("  steps, well before reaching max_steps=10, because a third expensive")
print("  step would have exceeded the budget. This is exactly what section 1")
print("  had no mechanism to prevent.")


# ============================================================ 3
rule("3. RUNAWAY DETECTION: STOPPING UNPRODUCTIVE REPETITION EARLY")


def stuck_decider(history: list[str]) -> str:
    """[ILLUSTRATIVE] A decision function that never adapts -- always
    proposes the identical action regardless of what has already happened,
    standing in for a real bug in a decision loop's own logic."""
    return "cheap_lookup"


def is_runaway(history: list[str], repeat_threshold: int = 3) -> bool:
    """[REAL] Detects the SAME action repeated some number of times in a
    row -- a real, checkable pattern distinct from simply running out of
    steps or budget."""
    if len(history) < repeat_threshold:
        return False
    return len(set(history[-repeat_threshold:])) == 1


def run_loop_with_runaway_detection(decide_next, max_steps: int = 10, max_cost: float = 5.00,
                                     repeat_threshold: int = 3, detect: bool = True):
    total_cost = 0.0
    history: list[str] = []
    trace = []
    for i in range(1, max_steps + 1):
        action = decide_next(history)
        history.append(action)
        if detect and is_runaway(history, repeat_threshold):
            trace.append(f"step {i}: RUNAWAY DETECTED -- {action!r} repeated "
                         f"{repeat_threshold}x in a row with no new information -- stopping early")
            break
        next_cost = TOOL_COSTS[action]
        if total_cost + next_cost > max_cost:
            trace.append(f"step {i}: BUDGET STOP")
            break
        total_cost += next_cost
        trace.append(f"step {i}: {action} -> running cost ${total_cost:.2f}")
    return total_cost, trace, i


print("  A decider stuck proposing the identical action every time, WITHOUT")
print("  runaway detection -- it simply runs to the step limit:")
no_detect_cost, no_detect_trace, no_detect_steps = run_loop_with_runaway_detection(
    stuck_decider, max_steps=10, max_cost=5.00, detect=False)
for line in no_detect_trace:
    print(f"    {line}")
print(f"\n  Ran the full {no_detect_steps} steps -- ${no_detect_cost:.2f} spent, with NO actual")
print("  progress at any point (the same action, over and over).")

print("\n  The SAME stuck decider, WITH runaway detection active:")
detect_cost, detect_trace, detect_steps = run_loop_with_runaway_detection(
    stuck_decider, max_steps=10, max_cost=5.00, detect=True)
for line in detect_trace:
    print(f"    {line}")
print(f"\n  Stopped after {detect_steps} steps instead of {no_detect_steps} -- "
      f"{no_detect_steps - detect_steps} wasted steps avoided, by")
print("  recognizing the unproductive pattern rather than waiting for a step")
print("  or cost limit to be exhausted first.")


# ============================================================ 4
rule("4. THREE MECHANISMS, THREE DIFFERENT FAILURE MODES")

print("  Step limit (M8-L03): bounds how many actions run, regardless of")
print("  what each one costs -- section 1 showed this alone misses a real")
print(f"  {expensive_cost / cheap_cost:.0f}x cost difference between two runs of equal length.")
print("\n  Cost budget (section 2): bounds real dollar spend directly,")
print("  stopping BEFORE a step that would exceed it -- catching exactly")
print("  what a step-count limit cannot see.")
print("\n  Runaway detection (section 3): recognizes a loop making no real")
print("  progress and stops EARLY, before either the step limit or the cost")
print(f"  budget would otherwise be exhausted -- {no_detect_steps - detect_steps} steps saved in this")
print("  lab's own measured comparison.")
print("\n  None of the three substitutes for the others: a step limit is a")
print("  hard backstop against literally infinite loops; a cost budget is")
print("  the constraint that actually matters financially; runaway")
print("  detection is what lets a loop stop gracefully, before either hard")
print("  limit is reached, when it recognizes it isn't converging.")


# ============================================================ 5
rule("5. WHAT THIS LAB IS AND IS NOT")

print("  REAL: every cost total, every trace line, and the step-count")
print("  comparison between detected and undetected runaway loops are")
print("  genuinely computed by running this code -- not asserted numbers.")
print("\n  ILLUSTRATIVE: stuck_decider() and is_runaway()'s exact-repeat check")
print("  are small, hand-coded stand-ins -- a real system's decision logic")
print("  and a real runaway pattern could be far more subtle than an")
print("  identical action repeated verbatim. TOOL_COSTS' specific dollar")
print("  values are this lesson's own illustration.")
print("\n  NOT SHOWN: detecting subtler non-convergence patterns (oscillating")
print("  between two or more states, rather than repeating one exactly);")
print("  per-user or per-organization budget pools spanning many separate")
print("  agent runs; and how a stopped-early run should report itself (M8-L13's")
print("  own honest-recovery topic, applied here to a budget or runaway stop).")

print("\nDone.")
