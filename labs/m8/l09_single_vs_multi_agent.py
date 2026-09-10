"""M8-L09 lab -- a single agent accumulates everything it observes in one
growing context; splitting into separate agents means a HAND-OFF between
them, usually a summary rather than the full history. This lesson measures
both real costs of that trade-off: single-agent's context genuinely grows
with each step (a real token/cost concern), and multi-agent's hand-off can
genuinely lose a specific detail the summary never captured (a real
correctness concern) -- then shows a case where multi-agent's isolation has
no such cost at all, because there was never anything to hand off.

Deterministic. No API key, no network, no third-party dependencies.
Run:  python labs/m8/l09_single_vs_multi_agent.py
"""

from __future__ import annotations

import re
import sys

sys.stdout.reconfigure(encoding="utf-8")


def rule(title: str) -> None:
    print(f"\n{'=' * 76}\n{title}\n{'=' * 76}")


# ============================================================ 1
rule("1. SINGLE-AGENT CONTEXT: EVERYTHING ACCUMULATES, NOTHING IS LOST")

INVESTIGATION_STEPS = [
    ("check_error_logs",
     "Error code E-4471 at 14:32 UTC: connection timeout after 30s, retried 3x, all failed."),
    ("check_service_status",
     "Regional outage in us-east-2 confirmed, started 14:28 UTC, ongoing."),
    ("check_customer_impact",
     "Customer's account region: us-east-2. Affected by the ongoing outage."),
]

full_context = ""
print("  A single agent investigates, accumulating EVERY observation into")
print("  one growing context:\n")
for step_name, observation in INVESTIGATION_STEPS:
    full_context += f"[{step_name}] {observation}\n"
    print(f"    [{step_name}] {observation}")
    print(f"      -- context size so far: {len(full_context)} characters")

print(f"\n  Full accumulated context ({len(full_context)} characters):")
print(f"    {full_context!r}")


def draft_customer_response(context: str) -> str:
    """[REAL] Extracts whatever specific details are ACTUALLY PRESENT in the
    given context -- an error code (if present) and the outage region (if
    present) -- and drafts a response using only what it can find. This
    function does not know or assume anything beyond its input string."""
    error_code_match = re.search(r"E-\d+", context)
    region_match = re.search(r"us-[a-z]+-\d+", context)
    parts = ["We're sorry for the disruption to your service."]
    if region_match:
        parts.append(f"This was caused by a regional outage in {region_match.group(0)}.")
    if error_code_match:
        parts.append(f"Your specific error was logged as {error_code_match.group(0)}, "
                      f"which our team can use to confirm your case if you contact support.")
    return " ".join(parts)


single_agent_response = draft_customer_response(full_context)
print(f"\n  Single-agent's customer response (drafted from the FULL context):")
print(f"    {single_agent_response!r}")


# ============================================================ 2
rule("2. MULTI-AGENT HAND-OFF: A SMALLER CONTEXT, BUT A REAL RISK OF LOSING A DETAIL")


def summarize_for_handoff(context: str) -> str:
    """[ILLUSTRATIVE] A small, deliberately realistic summarizer -- it
    correctly captures the GENERAL cause (a regional outage) but, like many
    real summaries, drops a granular detail (the specific error code) that
    seemed secondary to whoever or whatever wrote the summary."""
    return "There was a confirmed regional outage affecting this customer's account."


handoff_summary = summarize_for_handoff(full_context)
print(f"  Technical agent hands off a SUMMARY instead of the full context:")
print(f"    {handoff_summary!r}")
print(f"\n  Full context: {len(full_context)} characters")
print(f"  Handoff summary: {len(handoff_summary)} characters")
print(f"  Size reduction: {(1 - len(handoff_summary) / len(full_context)) * 100:.0f}% smaller --")
print("  a real, measurable saving for whatever agent receives it.")

multi_agent_response = draft_customer_response(handoff_summary)
print(f"\n  Communications agent's response (drafted from ONLY the summary):")
print(f"    {multi_agent_response!r}")

print(f"\n  Does the single-agent response mention the specific error code? "
      f"{'E-4471' in single_agent_response}")
print(f"  Does the multi-agent response mention the specific error code? "
      f"{'E-4471' in multi_agent_response}")
print("\n  The error code was never lost by accident or by a bug in")
print("  draft_customer_response() -- it is simply not PRESENT in the")
print("  summary text at all, so there was nothing for the function to")
print("  find. This is the real trade-off: the smaller context measured")
print("  above is smaller because something specific was left out of it.")


# ============================================================ 3
rule("3. WHERE MULTI-AGENT HAS NO SUCH COST: TRULY INDEPENDENT INVESTIGATIONS")

UNRELATED_CASES = {
    "Customer A": "Billing dispute over a duplicate charge.",
    "Customer B": "Password reset request after a failed login.",
    "Customer C": "Question about international shipping rates.",
}

print("  Three genuinely unrelated cases, each handled by its OWN agent with")
print("  its OWN, independently-sized context -- none needs anything from")
print("  the others:\n")
total_isolated_context = 0
for customer, case in UNRELATED_CASES.items():
    agent_context = f"[{customer}'s case] {case}"
    total_isolated_context += len(agent_context)
    print(f"    {customer}'s agent context ({len(agent_context)} chars): {agent_context!r}")

combined_single_context = " | ".join(f"[{c}] {t}" for c, t in UNRELATED_CASES.items())
print(f"\n  Three separate agent contexts, summed: {total_isolated_context} characters")
print(f"  One single agent handling all three in one context: {len(combined_single_context)} characters")
print("\n  Here, splitting into separate agents costs NOTHING beyond the raw")
print("  size of each case's own data -- there is no hand-off between them")
print("  at all, because none of the three cases needs anything from the")
print("  other two. Unlike section 2, no detail is at risk of being lost,")
print("  because nothing needs to cross an agent boundary in the first place.")


# ============================================================ 4
rule("4. A FRAMEWORK: WHEN DOES SPLITTING INTO AGENTS PAY FOR ITSELF")


def recommend_design(relationship: str) -> str:
    """[REAL] One question, three honest answers: is anything shared across
    the boundary at all ("independent"), does a later step need the FULL
    detail an earlier step gathered with no safe way to condense it
    ("needs_full_detail"), or does it need only SOME specific, identifiable
    fields that a carefully-engineered hand-off could preserve
    ("needs_some_detail")?"""
    if relationship == "independent":
        return "MULTI-AGENT (isolation is free -- nothing needs to cross a boundary)"
    if relationship == "needs_full_detail":
        return "SINGLE AGENT (a hand-off risks losing detail a later step needs)"
    return "MULTI-AGENT WITH A CAREFUL, LOSSLESS HAND-OFF (pass specific fields, not free prose)"


CASES = [
    ("Technical investigation feeding a customer response that must cite specific error details",
     "needs_full_detail"),
    ("Three unrelated customer cases with no shared information", "independent"),
    ("A research phase whose key findings (a few named facts, not the whole transcript) must reach a writing phase",
     "needs_some_detail"),
]
for description, relationship in CASES:
    print(f"    {recommend_design(relationship)}")
    print(f"      -- {description}\n")

print("  This matches exactly what sections 1-3 measured: the technical-to-")
print("  communications hand-off in section 2 needed shared detail and lost")
print("  some of it, exactly the risk this framework flags; section 3's")
print("  three unrelated cases needed nothing shared, exactly where")
print("  multi-agent's isolation was free.")


# ============================================================ 5
rule("5. WHAT THIS LAB IS AND IS NOT")

print("  REAL: every character count, every regex match, and both drafted")
print("  responses above are genuinely computed -- the missing error code")
print("  in section 2's multi-agent response is a measured consequence of")
print("  what text the summary actually contains, not an asserted claim.")
print("\n  ILLUSTRATIVE: summarize_for_handoff() is a small, hand-written")
print("  stand-in for a real summarization step -- a real system might use")
print("  a model call to summarize, which could preserve or drop different")
print("  details than this specific example. draft_customer_response()'s")
print("  regex-based extraction stands in for a real generation step.")
print("\n  NOT SHOWN: how agents actually pass messages to each other in a")
print("  real framework (protocols, message formats); a hand-off design")
print("  that explicitly preserves specific fields rather than relying on")
print("  a free-text summary; and cost/latency comparisons between running")
print("  N agents versus one agent making N tool calls, a natural extension")
print("  left to the exercises.")

print("\nDone.")
