"""M8-L04 lab -- M8-L03 built a general loop and left decide_next() as a
black box. This lesson opens that box into four named phases -- PLAN, ACT,
OBSERVE, STOP -- and shows that getting the loop's mechanics right (M8-L03)
does not guarantee getting the RIGHT ANSWER: a rigid plan that never revises
itself against what it observes fails one way, and a react-style loop with a
sloppy stopping condition fails a completely different way, even while both
reuse the identical, correctly-implemented tool-execution loop underneath.

Deterministic. No API key, no network, no third-party dependencies.
Run:  python labs/m8/l04_plan_act_observe_stop.py
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
    """[REAL, M8-L03's exact general loop, byte-for-byte unmodified] Every
    variant in this lesson reuses this identical function -- what differs
    between them is only the decide_next() passed in, isolating exactly the
    PLAN/STOP quality this lesson is actually about. `observed` still maps
    each tool name to only its MOST RECENT result, exactly as in M8-L03 --
    a decider that needs to remember more than the last call (as sections
    3-4's minimization over several carriers does) keeps that memory in its
    own closure, not by changing this function's contract."""
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


# The task: find the CHEAPEST shipping carrier that arrives within 3 days.
CARRIERS = {
    "Standard": {"days": 5, "cost": 5.0},
    "Overnight": {"days": 1, "cost": 30.0},
    "Express": {"days": 2, "cost": 12.0},
}
CHECK_ORDER = ["Standard", "Overnight", "Express"]   # deliberately NOT cost-sorted
MAX_DAYS = 3


def check_shipping(carrier: str) -> dict:
    return CARRIERS[carrier]


SHIPPING_TOOLS = [Tool("check_shipping", check_shipping, "Days and cost for a named carrier")]


# ============================================================ 1
rule("1. THE TASK: CHEAPEST CARRIER ARRIVING WITHIN 3 DAYS")

print(f"  Carriers on file: {CARRIERS}")
print(f"  Constraint: days <= {MAX_DAYS}. Goal: minimum cost among valid carriers.")
print(f"  Correct answer, computed directly from the table above: "
      f"{min((c for c in CARRIERS if CARRIERS[c]['days'] <= MAX_DAYS), key=lambda c: CARRIERS[c]['cost'])} "
      f"at ${min(CARRIERS[c]['cost'] for c in CARRIERS if CARRIERS[c]['days'] <= MAX_DAYS):.2f}")
print("  Three ways of reaching (or failing to reach) this answer follow.")


# ============================================================ 2
rule("2. PLAN-FIRST: A PLAN MADE BEFORE ANY OBSERVATION, NEVER REVISED")


def plan_first_book(default_carrier: str = "Standard") -> str:
    """[REAL, deliberately rigid] The ENTIRE plan is fixed before any tool
    is ever called -- 'most customers use Standard, so the plan is: check
    Standard, book Standard.' There is no step where an unexpected
    OBSERVATION could change what happens next, because the plan was never
    designed to be revised."""
    plan = [default_carrier]
    print(f"  [PLAN] committed in advance, before any observation: {plan}")
    for carrier in plan:
        result = check_shipping(carrier)
        print(f"  [ACT] check_shipping({carrier!r}) -> [OBSERVE] {result}")
    return f"booked {plan[0]} -- plan contained no other option to try"


outcome = plan_first_book()
print(f"\n  Result: {outcome}")
print(f"\n  Standard genuinely takes {CARRIERS['Standard']['days']} days, "
      f"violating the {MAX_DAYS}-day constraint -- but the plan was never")
print("  designed to check that constraint against an ALTERNATIVE, only to")
print("  execute what it already decided. A valid, cheaper-than-Overnight")
print("  option (Express) exists and is never even considered.")


# ============================================================ 3
rule("3. REACT-STYLE, NAIVE STOP: ADAPTS, BUT STOPS AT THE FIRST VALID ANSWER")


def make_naive_decider() -> tuple[Callable[[dict], tuple[str, dict]], dict]:
    """[ILLUSTRATIVE] Reacts to each observation (unlike section 2) -- but
    STOPS as soon as ANY carrier satisfies the constraint, never asking
    whether a CHEAPER valid one might still be unchecked. `checked` is this
    decider's OWN memory across calls (a real model's equivalent is its
    conversation history), returned alongside decide_next so the actual
    reported answer can be computed from it below -- run_tool_loop()'s
    `observed` still holds only the latest result, unchanged from M8-L03."""
    checked: dict[str, dict] = {}
    pending: list[str] = []

    def decide_next(observed: dict) -> tuple[str, dict]:
        if pending:
            checked[pending.pop()] = observed["check_shipping"]
        for carrier in CHECK_ORDER:
            if carrier not in checked:
                pending.append(carrier)
                return "check_shipping", {"carrier": carrier}
            if checked[carrier]["days"] <= MAX_DAYS:
                return "respond", {}
        return "respond", {}
    return decide_next, checked


print("  Running M8-L03's run_tool_loop() with a NAIVE stop condition:\n")
naive_decide, naive_checked = make_naive_decider()
naive_trace = run_tool_loop(SHIPPING_TOOLS, naive_decide)
for line in naive_trace:
    print(f"  {line}")

naive_valid = {c: r for c, r in naive_checked.items() if r["days"] <= MAX_DAYS}
naive_answer = min(naive_valid, key=lambda c: naive_valid[c]["cost"])
print(f"\n  Reported answer: {naive_answer} at ${naive_checked[naive_answer]['cost']:.2f} "
      f"-- computed from only {sorted(naive_checked)}, never checking Express at all.")

print("\n  This variant DOES react to observations -- it correctly skips past")
print("  Standard once it sees the 5-day observation violates the")
print("  constraint. But it stops the moment it finds ANY valid carrier")
print("  without checking whether a cheaper valid one still unchecked")
print("  (Express, $12) exists. Adapting to observations and stopping")
print("  correctly are two SEPARATE properties -- this variant has the")
print("  first and not the second.")


# ============================================================ 4
rule("4. REACT-STYLE, CORRECT STOP: CHECKS EVERYTHING BEFORE DECIDING")


def make_correct_decider() -> tuple[Callable[[dict], tuple[str, dict]], dict]:
    """[ILLUSTRATIVE] Reacts to each observation AND only stops once every
    carrier in the known, enumerable set has actually been checked -- a
    correct stopping rule specifically BECAUSE this task is a minimization
    over a small, fully-known set. Same closure-based memory pattern as
    make_naive_decider() -- only the STOP condition differs."""
    checked: dict[str, dict] = {}
    pending: list[str] = []

    def decide_next(observed: dict) -> tuple[str, dict]:
        if pending:
            checked[pending.pop()] = observed["check_shipping"]
        for carrier in CHECK_ORDER:
            if carrier not in checked:
                pending.append(carrier)
                return "check_shipping", {"carrier": carrier}
        return "respond", {}
    return decide_next, checked


print("  Running the SAME run_tool_loop() with a CORRECT stop condition:\n")
correct_decide, correct_checked = make_correct_decider()
correct_trace = run_tool_loop(SHIPPING_TOOLS, correct_decide)
for line in correct_trace:
    print(f"  {line}")

correct_valid = {c: r for c, r in correct_checked.items() if r["days"] <= MAX_DAYS}
correct_answer = min(correct_valid, key=lambda c: correct_valid[c]["cost"])
print(f"\n  Reported answer: {correct_answer} at ${correct_checked[correct_answer]['cost']:.2f} "
      f"-- computed from all {sorted(correct_checked)}, the full known set.")

print("\n  This variant checks all three carriers before stopping, so it")
print("  actually knows Express ($12) beats Overnight ($30) among the valid")
print("  options -- the correct, cheapest answer, verified rather than")
print("  assumed. The only difference from section 3's decide_next() is the")
print("  STOP condition; run_tool_loop() itself, and the ACT/OBSERVE")
print("  mechanics, are byte-for-byte identical between the two.")


# ============================================================ 5
rule("5. FOUR NAMED PHASES, AND WHICH ONE EACH VARIANT GOT WRONG")

correct_cost = correct_checked[correct_answer]["cost"]
naive_verdict = "correct" if naive_answer == correct_answer else "WRONG"
print(f"  {'Variant':<31}{'Plan':<10}{'Act/Observe':<14}{'Stop':<10}{'Result'}")
print(f"  {'Plan-first (sec. 2)':<31}{'fixed':<10}{'n/a':<14}{'n/a':<10}"
      f"WRONG (booked Standard, violates {MAX_DAYS}-day limit)")
print(f"  {'React, naive stop (sec. 3)':<31}{'adaptive':<10}{'correct':<14}{'WRONG':<10}"
      f"{naive_verdict} ({naive_answer}, ${naive_checked[naive_answer]['cost']:.2f})")
print(f"  {'React, correct stop (sec. 4)':<31}{'adaptive':<10}{'correct':<14}{'correct':<10}"
      f"RIGHT ({correct_answer}, ${correct_cost:.2f})")

print("\n  PLAN, ACT, OBSERVE, and STOP are four separate places a loop can")
print("  be wrong, even when the underlying tool-execution mechanics")
print("  (M8-L03) are entirely correct in all three variants above. Section")
print("  2 failed at PLAN -- it never revised its committed plan against an")
print("  observation. Section 3 failed at STOP -- it adapted correctly but")
print("  quit checking too soon. Neither failure is a bug in run_tool_loop()")
print("  itself; both are properties of the decision logic wired into it.")


# ============================================================ 6
rule("6. WHAT THIS LAB IS AND IS NOT")

print("  REAL: run_tool_loop() is M8-L03's own function, unmodified. All")
print("  three variants' outcomes (the wrong answer from section 2, the")
print("  wrong answer from section 3, the correct answer from section 4)")
print("  are genuinely computed from the same CARRIERS table, not scripted")
print("  to produce a predetermined narrative.")
print("\n  ILLUSTRATIVE: make_naive_decider() and make_correct_decider() are")
print("  small, hand-coded stopping RULES standing in for a real model's")
print("  judgment about when enough information has been gathered -- a real")
print("  agent reasons about this per task, not via a fixed rule. The")
print("  shipping-carrier domain and its specific numbers are this lesson's")
print("  own illustration, not a claim about real shipping costs.")
print("\n  NOT SHOWN: genuine multi-step re-planning (revising a plan's later")
print("  steps mid-execution, as opposed to this lesson's all-or-nothing")
print("  rigid plan); validating tool arguments against a schema (M8-L05);")
print("  and human approval before an action executes, which would let a")
print("  person catch section 2's or 3's wrong answer before it was acted")
print("  on (M8-L10).")

print("\nDone.")
