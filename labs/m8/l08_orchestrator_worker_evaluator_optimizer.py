"""M8-L08 lab -- two patterns beyond M8-L07's fixed routing/chaining/
parallel shapes. ORCHESTRATOR-WORKER decomposes a task into a NUMBER OF
SUBTASKS THAT VARIES WITH THE REQUEST, dispatches each to a worker, and
combines the results -- unlike M8-L07's parallel section, which always ran
the same fixed three calls regardless of input. EVALUATOR-OPTIMIZER
generates a candidate, checks it against explicit criteria, and revises
based on what specifically failed, looping until it passes or a bound is
reached -- and this lab shows both a genuine, feedback-driven improvement
and a genuine, honest give-up when the requirement cannot be met at all.

Deterministic. No API key, no network, no third-party dependencies.
Run:  python labs/m8/l08_orchestrator_worker_evaluator_optimizer.py
"""

from __future__ import annotations

import sys
from concurrent.futures import ThreadPoolExecutor

sys.stdout.reconfigure(encoding="utf-8")


def rule(title: str) -> None:
    print(f"\n{'=' * 76}\n{title}\n{'=' * 76}")


# ============================================================ 1
rule("1. ORCHESTRATOR-WORKER: DECOMPOSITION THAT VARIES WITH THE REQUEST")


def get_price_info(request: str) -> str:
    return "Price: $49.99."


def get_shipping_info(request: str) -> str:
    return "Ships in 2-3 business days."


def get_returns_info(request: str) -> str:
    return "Returns accepted within 30 days."


WORKERS = {"price": get_price_info, "shipping": get_shipping_info, "returns": get_returns_info}


def decompose_task(request: str) -> list[str]:
    """[ILLUSTRATIVE] A small stand-in for a real orchestrator's judgment
    about which subtasks a compound request actually needs -- a real
    system uses an actual model call to decide this, not a keyword check.
    The key property this lab measures is real: the RESULT genuinely
    varies with the request's content."""
    text = request.lower()
    subtasks = []
    if "price" in text or "cost" in text:
        subtasks.append("price")
    if "shipping" in text or "ship" in text:
        subtasks.append("shipping")
    if "return" in text:
        subtasks.append("returns")
    return subtasks


def orchestrate(request: str) -> tuple[str, list[str]]:
    """[REAL] The orchestrator decomposes, then dispatches each subtask to
    its worker IN PARALLEL (M8-L07's own mechanism, reused here because
    once decomposed, the subtasks are genuinely independent of each other)
    before combining the results into one response."""
    subtasks = decompose_task(request)
    with ThreadPoolExecutor(max_workers=max(len(subtasks), 1)) as pool:
        results = list(pool.map(lambda s: WORKERS[s](request), subtasks))
    return " ".join(results), subtasks


REQUESTS = [
    "Tell me about the price and shipping for this item.",
    "Tell me about the price, shipping, and return policy for this item.",
]

for request in REQUESTS:
    combined, subtasks = orchestrate(request)
    print(f"  Request: {request!r}")
    print(f"    Decomposed into {len(subtasks)} subtask(s): {subtasks}")
    print(f"    Combined response: {combined!r}\n")

print("  The SECOND request decomposed into one more subtask than the")
print("  FIRST -- the number of workers dispatched genuinely varies with")
print("  what the request actually asks for. Contrast this with M8-L07's")
print("  parallel section, which always ran the SAME fixed three warehouse")
print("  checks regardless of input: there, the set of independent calls")
print("  was known in advance; here, the orchestrator decides it per request.")


# ============================================================ 2
rule("2. EVALUATOR-OPTIMIZER: GENERATE, CHECK, REVISE BASED ON WHAT FAILED")

TOPIC_KEYWORDS = {"price": ["price", "$"], "shipping": ["ship"], "returns": ["return"], "warranty": ["warranty"]}


def generate_draft(feedback_ever_seen: set[str]) -> str:
    """[ILLUSTRATIVE] A draft generator whose output genuinely depends on
    every piece of feedback it has EVER received, not just the last round's
    -- a real system's generator revises cumulatively, incorporating each
    fix permanently, rather than forgetting an earlier correction the
    moment a later round's feedback focuses on something else."""
    parts = ["Price: $49.99.", "Ships in 2-3 business days."]
    if "returns" in feedback_ever_seen:
        parts.append("Returns accepted within 30 days.")
    return " ".join(parts)


def evaluate(draft: str, required_topics: list[str]) -> tuple[bool, list[str]]:
    """[REAL] Checks the draft against explicit, named criteria -- exactly
    the kind of evaluator this pattern needs: specific enough to tell the
    generator WHAT was missing, not just THAT something was missing."""
    draft_lower = draft.lower()
    missing = [t for t in required_topics if not any(kw in draft_lower for kw in TOPIC_KEYWORDS[t])]
    return (len(missing) == 0, missing)


def evaluator_optimizer(required_topics: list[str], max_attempts: int = 3) -> tuple[str | None, list[str]]:
    feedback_ever_seen: set[str] = set()
    trace = []
    for attempt in range(1, max_attempts + 1):
        draft = generate_draft(feedback_ever_seen)
        passed, missing = evaluate(draft, required_topics)
        trace.append(f"  attempt {attempt}: {draft!r}")
        trace.append(f"    evaluator: missing={missing}")
        if passed:
            trace.append(f"    PASSED on attempt {attempt}")
            return draft, trace
        feedback_ever_seen |= set(missing)
    trace.append(f"  GAVE UP after {max_attempts} attempts -- still missing {missing}")
    return None, trace


print("  Case A -- a requirement the generator CAN satisfy once told what's missing:")
draft, trace = evaluator_optimizer(["price", "shipping", "returns"])
for line in trace:
    print(f"  {line}")
print(f"  Final result: {draft!r}\n")

print("  Case B -- a requirement (warranty info) this generator can NEVER")
print("  produce, regardless of feedback:")
draft, trace = evaluator_optimizer(["price", "shipping", "returns", "warranty"], max_attempts=3)
for line in trace:
    print(f"  {line}")
print(f"  Final result: {draft!r}")

print("\n  Case A shows genuine improvement: the second attempt's draft is")
print("  DIFFERENT from the first, specifically because the evaluator's")
print("  feedback named what was missing. Case B shows the loop honestly")
print("  giving up after a real, enforced attempt limit, rather than either")
print("  looping forever or falsely reporting success -- the same bounded-")
print("  loop discipline M8-L03's max_steps established, applied here to")
print("  revision attempts instead of tool calls.")


# ============================================================ 3
rule("3. A FRAMEWORK: WHICH PATTERN FITS WHICH NEED")


def recommend_pattern(decomposes_dynamically: bool, needs_quality_check: bool) -> str:
    """[REAL] Two questions: does the number/shape of subtasks genuinely
    depend on the specific request (not fixed in advance), and does the
    output need to be checked against explicit criteria and possibly
    revised?"""
    if decomposes_dynamically:
        return "ORCHESTRATOR-WORKER (subtask count/shape varies with the request)"
    if needs_quality_check:
        return "EVALUATOR-OPTIMIZER (generate, check against criteria, revise)"
    return "A FIXED SHAPE FROM M8-L07 IS LIKELY SUFFICIENT (routing/chaining/parallel)"


CASES = [
    ("A compound request whose number of sub-topics varies per customer", True, False),
    ("A single generated answer that must satisfy several explicit, checkable criteria", False, True),
    ("Three always-present, independent warehouse stock checks (M8-L07)", False, False),
]
for description, dynamic, quality_check in CASES:
    print(f"    {recommend_pattern(dynamic, quality_check)}")
    print(f"      -- {description}\n")

print("  This matches exactly what sections 1-2 measured: the orchestrator's")
print("  subtask count genuinely changed between two real requests (2 vs 3")
print("  workers), and the optimizer's second draft genuinely differed from")
print("  its first because of specific, named evaluator feedback -- neither")
print("  property appears in M8-L07's fixed-shape patterns.")


# ============================================================ 4
rule("4. WHAT THIS LAB IS AND IS NOT")

print("  REAL: decompose_task() genuinely produces a different subtask list")
print("  for the two requests in section 1; the ThreadPoolExecutor dispatch")
print("  is real, reused from M8-L07; and evaluate() in section 2 performs a")
print("  real, executed keyword check whose result genuinely determines")
print("  whether the loop stops or continues.")
print("\n  ILLUSTRATIVE: decompose_task() and generate_draft() are small,")
print("  hand-coded stand-ins for a real model's judgment and generation --")
print("  a real system uses actual model calls for both, not keyword rules.")
print("  The specific product-description domain is this lesson's own")
print("  illustration, not a claim about real e-commerce systems.")
print("\n  NOT SHOWN: an orchestrator that itself decides HOW to combine")
print("  worker results beyond simple concatenation; an evaluator whose")
print("  criteria are themselves generated or learned rather than fixed in")
print("  advance; and running orchestrator-worker and evaluator-optimizer")
print("  together in one system (a worker's own output being evaluated and")
print("  revised, say) -- a natural extension left to the exercises.")

print("\nDone.")
