"""M8-L01 lab -- "agent" is used loosely in industry writing for three
genuinely different system shapes. This lab builds all three from the SAME
underlying tool set (search_orders/get_order/issue_refund, M5-L08's own
running scenario) to make the difference an objective, executable property
rather than a matter of vibes: a CHATBOT never touches a tool at all; a
WORKFLOW calls tools in a sequence FIXED by code, regardless of what the
request actually needs; an AGENT calls tools in a sequence CHOSEN, step by
step, by the model's own judgment about what it has observed so far.

Deterministic. No API key, no network, no third-party dependencies.
Run:  python labs/m8/l01_chatbots_workflows_agents.py
"""

from __future__ import annotations

import sys

sys.stdout.reconfigure(encoding="utf-8")


def rule(title: str) -> None:
    print(f"\n{'=' * 76}\n{title}\n{'=' * 76}")


# A small mock backend, M5-L08's own support-assistant scenario continued.
CUSTOMER_ORDERS = {"Dana Kim": "O-1001", "Priya Shah": "O-1002"}
ORDERS = {
    "O-1001": {"item": "Wireless Mouse", "amount": 25.00, "status": "delayed in transit"},
    "O-1002": {"item": "Desk Lamp", "amount": 40.00, "status": "delivered"},
}
REFUNDS_ISSUED: list[tuple[str, float]] = []


def search_orders(customer_name: str) -> str | None:
    return CUSTOMER_ORDERS.get(customer_name)


def get_order(order_id: str) -> dict | None:
    return ORDERS.get(order_id)


def issue_refund(order_id: str, amount: float) -> str:
    REFUNDS_ISSUED.append((order_id, amount))
    return f"Refund of ${amount:.2f} issued for {order_id}."


SCENARIO_STATUS = {"customer": "Priya Shah", "request": "What is the status of my order?"}
SCENARIO_REFUND = {"customer": "Dana Kim", "request": "My order hasn't arrived, I'd like a refund."}


# ============================================================ 1
rule("1. CHATBOT: TEXT IN, TEXT OUT, NO TOOLS AT ALL")


def chatbot_respond(request: str) -> str:
    """[ILLUSTRATIVE mechanism] A chatbot has no tool access by definition --
    it can only produce text from what it already has (its training and the
    conversation itself). Asked something that needs real, current data, it
    has no mechanism to go check -- the honest response is to say so
    (M7-L13's abstention principle, in a non-RAG setting)."""
    if "status" in request.lower() or "refund" in request.lower():
        return ("I don't have access to your order records, so I can't check "
                "that or take any action on it -- I can only discuss general "
                "policy questions.")
    return "I can help with general questions about our policies."


for scenario in (SCENARIO_STATUS, SCENARIO_REFUND):
    print(f"  Request: {scenario['request']!r}")
    print(f"  Chatbot response: {chatbot_respond(scenario['request'])!r}\n")

print("  Neither call above touched search_orders, get_order, or issue_refund")
print("  -- structurally, a chatbot CANNOT look anything up or change any real")
print("  state, no matter how the request is worded. That is not a missing")
print("  feature in this mock; it is the definition of the shape.")


# ============================================================ 2
rule("2. WORKFLOW: TOOLS CALLED IN A SEQUENCE FIXED BY CODE")


def refund_workflow(customer_name: str) -> list[str]:
    """[REAL] The code decides the NEXT step, always -- never the request's
    actual content. This function calls exactly these three tools, in this
    order, for every customer, every time."""
    trace = []
    order_id = search_orders(customer_name)
    trace.append(f"search_orders({customer_name!r}) -> {order_id!r}")
    order = get_order(order_id)
    trace.append(f"get_order({order_id!r}) -> {order!r}")
    result = issue_refund(order_id, order["amount"])
    trace.append(f"issue_refund({order_id!r}, {order['amount']}) -> {result!r}")
    return trace


print("  Running the SAME fixed workflow for BOTH scenarios:\n")
for scenario in (SCENARIO_STATUS, SCENARIO_REFUND):
    print(f"  Request: {scenario['request']!r}")
    for line in refund_workflow(scenario["customer"]):
        print(f"    {line}")
    print()

print(f"  REFUNDS_ISSUED so far: {REFUNDS_ISSUED}")
print("\n  The workflow issued a refund to Priya Shah, who only asked about")
print("  STATUS and never requested one -- a real, demonstrated consequence")
print("  of a FIXED path: the code always executes all three steps, because")
print("  nothing in the workflow's control flow branches on what the request")
print("  actually needs. A workflow can still call a model INSIDE a step (to")
print("  draft the reply text, say) -- what makes it a workflow is that the")
print("  NEXT STEP is never that model's decision.")

REFUNDS_ISSUED.clear()   # reset for section 3's independent comparison


# ============================================================ 3
rule("3. AGENT: TOOLS CALLED IN A SEQUENCE THE MODEL CHOOSES, STEP BY STEP")


def decide_next_action(request: str, observed: dict) -> str:
    """[ILLUSTRATIVE mechanism, REAL control-flow effect] A small rule-based
    stand-in for a real model's judgment (a real system would use an actual
    model call here, M8-L03's own topic) -- but the KEY property is real and
    not scripted: the returned action genuinely depends on both the request
    AND what has been observed so far, so different inputs can produce
    different NUMBERS of steps, not just different final words."""
    if "order_id" not in observed:
        return "search_orders"
    if "order" not in observed:
        return "get_order"
    wants_refund = "refund" in request.lower()
    if wants_refund and "refund_issued" not in observed:
        return "issue_refund"
    return "respond"


def run_agent(customer_name: str, request: str) -> list[str]:
    trace = []
    observed: dict = {}
    for _ in range(6):   # a real bound -- M8-L15's own topic, previewed here
        action = decide_next_action(request, observed)
        if action == "search_orders":
            observed["order_id"] = search_orders(customer_name)
            trace.append(f"[model chose] search_orders({customer_name!r}) -> {observed['order_id']!r}")
        elif action == "get_order":
            observed["order"] = get_order(observed["order_id"])
            trace.append(f"[model chose] get_order({observed['order_id']!r}) -> {observed['order']!r}")
        elif action == "issue_refund":
            result = issue_refund(observed["order_id"], observed["order"]["amount"])
            observed["refund_issued"] = True
            trace.append(f"[model chose] issue_refund(...) -> {result!r}")
        else:
            trace.append("[model chose] respond -- stop, enough information gathered")
            break
    return trace


print("  Running the SAME tool set through an AGENT loop for BOTH scenarios:\n")
agent_traces = {}
for scenario in (SCENARIO_STATUS, SCENARIO_REFUND):
    print(f"  Request: {scenario['request']!r}")
    trace = run_agent(scenario["customer"], scenario["request"])
    agent_traces[scenario["customer"]] = trace
    for line in trace:
        print(f"    {line}")
    print()

print(f"  REFUNDS_ISSUED this time: {REFUNDS_ISSUED}")
print("\n  This time, Priya Shah's status question genuinely takes a DIFFERENT,")
print("  SHORTER path than Dana Kim's refund request -- no issue_refund call")
print("  for Priya at all, decided step by step from what was actually")
print("  observed. Same tools as section 2; genuinely different, request-")
print("  dependent behavior, because the NEXT action is chosen at runtime")
print("  instead of fixed in advance.")


# ============================================================ 4
rule("4. A CHECKABLE DEFINITION, APPLIED TO REAL AND DESCRIBED SYSTEMS")


def classify(takes_actions: bool, model_selects_next_action: bool) -> str:
    """[REAL] Two yes/no properties are enough: does the system call tools
    that touch real data or state at all, and if so, is the CHOICE of which
    tool to call next made by the model at runtime, or fixed by code ahead
    of time?"""
    if not takes_actions:
        return "CHATBOT"
    if not model_selects_next_action:
        return "WORKFLOW"
    return "AGENT"


DESCRIBED_SYSTEMS = [
    ("A pure Q&A bot with no tool access, answering from general knowledge only", False, False),
    ("A pipeline that always fetches an order, then always emails a confirmation", True, False),
    ("A system that decides whether to search, check inventory, or refund, based on what it finds", True, True),
]
print("  Applying the same two-question test to described systems:\n")
for description, takes_actions, model_selects in DESCRIBED_SYSTEMS:
    print(f"    {classify(takes_actions, model_selects):<8} -- {description}")

print("\n  And applying it to what sections 1-3 actually ran, not just described:")
print(f"    {classify(False, False):<8} -- section 1's chatbot_respond()")
print(f"    {classify(True, False):<8} -- section 2's refund_workflow()")
print(f"    {classify(True, True):<8} -- section 3's run_agent()")
print("\n  Same two questions, same answers, whether applied to a one-line")
print("  description or to the actual functions just executed above --")
print("  classification does not require reading the whole implementation,")
print("  only these two properties of its control flow.")


# ============================================================ 5
rule("5. WHY THE DISTINCTION IS NOT JUST TERMINOLOGY")

workflow_steps = 3          # section 2: identical, every time, by construction
agent_steps = {name: len(trace) for name, trace in agent_traces.items()}

print(f"  Section 2's workflow: ALWAYS {workflow_steps} steps -- constant, by")
print("  construction, regardless of input.")
print(f"  Section 3's agent, measured from its own real traces: "
      f"{agent_steps} steps.")
print(f"  Range across these two real scenarios: "
      f"{min(agent_steps.values())}-{max(agent_steps.values())} steps.")

print("\n  A workflow's step count -- and so its cost and latency -- is knowable")
print("  in advance and identical on every run: it can be tested exhaustively,")
print("  because there is only one path. An agent's step count is genuinely")
print("  DATA-DEPENDENT, as just measured -- its cost, latency, and the exact")
print("  sequence of actions taken cannot be fully enumerated in advance the")
print("  same way, only bounded (the loop above stops after 6 iterations no")
print("  matter what, M8-L15's own topic previewed here).")

print("\n  This is also exactly the expanded surface M5-L08 flagged and left")
print("  for this module: 'the model calls a tool, the result contains an")
print("  instruction, the model calls another tool' is only a LOOP risk for")
print("  the AGENT shape -- a workflow's next step was never the model's to")
print("  decide, so there is no such decision for injected content to hijack.")
print("  This is the real reason Module 8 spends whole lessons on approval")
print("  gates (M8-L10), idempotency (M8-L12), step limits (M8-L15), and")
print("  sandboxing (M8-L16): they matter specifically BECAUSE an agent's")
print("  next action is chosen at runtime, not because tools exist at all.")


# ============================================================ 6
rule("6. WHAT THIS LAB IS AND IS NOT")

print("  REAL: every tool call, trace, and step count in sections 1-3 is")
print("  genuinely executed against the shared mock backend -- the workflow's")
print("  wrong refund and the agent's differing step counts are measured")
print("  outcomes of running the code, not asserted claims. Section 4's")
print("  classify() function is real and applied identically to both")
print("  described and actually-executed systems.")
print("\n  ILLUSTRATIVE: decide_next_action() is a small, hand-coded rule")
print("  standing in for a real model's judgment -- a real agent (M8-L03)")
print("  uses an actual model call to choose its next action, not a keyword")
print("  check. The specific tool set is this course's own running example,")
print("  not a claim about what a real support system's tools look like.")
print("\n  NOT SHOWN: a general-purpose, reusable tool-execution loop (M8-L03")
print("  builds one from scratch); planning across multiple steps before")
print("  acting (M8-L04); and any of the safety mechanisms named in section 5")
print("  (M8-L10, M8-L12, M8-L15, M8-L16 each build one in depth).")

print("\nDone.")
