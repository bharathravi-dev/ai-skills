"""M9-L03 lab -- M9-L01 and M9-L02 used only TOOLS as their running example.
MCP actually defines three distinct primitives a server can expose: TOOLS
(model-invoked actions with side effects or computation), RESOURCES
(host-readable data, addressed by a URI, that the model does not decide to
"call"), and PROMPTS (reusable, server-defined templates a user can invoke
explicitly). This lab builds all three literally against a single server and
finds a real design mistake: modeling something that should be a resource
(a customer's own order history, pure lookup data) as a tool instead --
working, but pointlessly forcing a model decision on data the host could have
simply read.

Deterministic. No API key, no network, no third-party dependencies.
Run:  python labs/m9/l03_three_primitives.py
"""

from __future__ import annotations

import sys

sys.stdout.reconfigure(encoding="utf-8")


def rule(title: str) -> None:
    print(f"\n{'=' * 76}\n{title}\n{'=' * 76}")


ORDERS = {
    "O-1001": {"customer": "Priya Nair", "amount": 40.0, "status": "delivered"},
    "O-1002": {"customer": "Priya Nair", "amount": 15.0, "status": "shipped"},
}


# ============================================================ 1
rule("1. A TOOL: A MODEL-INVOKED ACTION, EXPLICITLY DECIDED AND CALLED")


def issue_refund(order_id: str, amount: float) -> dict:
    """[REAL] A genuine tool -- it performs an action with a real effect,
    and something (a model or a decision function) must explicitly decide
    to invoke it, with specific arguments, at a specific moment."""
    return {"order_id": order_id, "refunded": amount}


TOOLS = {
    "issue_refund": {
        "description": "Issue a refund for a specific order and amount.",
        "handler": issue_refund,
    }
}

result = TOOLS["issue_refund"]["handler"]("O-1001", 40.0)
print(f"  Calling the 'issue_refund' TOOL: issue_refund('O-1001', 40.0) -> {result}")
print("\n  A tool requires an explicit call, with explicit arguments, at an")
print("  explicit moment -- exactly M8-L03's own tool-call definition,")
print("  unchanged. Nothing about a tool is passive; it always represents a")
print("  decision to DO something.")


# ============================================================ 2
rule("2. A RESOURCE: HOST-READABLE DATA, ADDRESSED BY A URI, NOT 'CALLED'")

RESOURCES = {
    "orders://O-1001": lambda: dict(ORDERS["O-1001"]),
    "orders://O-1002": lambda: dict(ORDERS["O-1002"]),
}


def read_resource(uri: str) -> dict:
    """[REAL] Reading a resource is a lookup by a fixed identifier (a URI),
    not a decision with arguments to reason about -- there is no 'amount'
    or 'order_id' parameter to choose, only an address to read."""
    return RESOURCES[uri]()


order_1001_data = read_resource("orders://O-1001")
order_1002_data = read_resource("orders://O-1002")
print(f"  Reading the RESOURCE 'orders://O-1001': {order_1001_data}")
print(f"  Reading the RESOURCE 'orders://O-1002': {order_1002_data}")

print("\n  Reading a resource never required deciding what arguments to")
print("  pass -- only which URI to read. A host can read every resource it")
print("  has access to and place the content directly into context, with")
print("  no model decision step involved at all.")


# ============================================================ 3
rule("3. A PROMPT: A REUSABLE, SERVER-DEFINED TEMPLATE, EXPLICITLY INVOKED")

PROMPTS = {
    "refund_explanation": (
        "Explain, in plain language a customer would understand, why "
        "order {order_id} (status: {status}) is or is not eligible for "
        "a refund of ${amount:.2f}."
    ),
}


def render_prompt(name: str, **kwargs) -> str:
    """[REAL] A prompt is a server-defined TEMPLATE -- the server owns and
    maintains its wording; a client fills in named fields and gets back
    text meant to be used as-is (e.g., sent to a model), not executed."""
    return PROMPTS[name].format(**kwargs)


rendered = render_prompt("refund_explanation", order_id="O-1001", status="delivered", amount=40.0)
print(f"  Rendering the PROMPT 'refund_explanation':\n    {rendered!r}")

print("\n  A prompt is neither an action (a tool) nor raw data to read (a")
print("  resource) -- it is reusable TEXT the server maintains, so that")
print("  many different clients invoking the same prompt name get the")
print("  same well-crafted wording, rather than each re-inventing it.")


# ============================================================ 4
rule("4. A REAL DESIGN MISTAKE: MODELING A RESOURCE AS A TOOL")


def get_customer_orders_as_tool(customer_name: str) -> list[dict]:
    """[REAL, deliberately mis-designed] A pure lookup with no arguments to
    reason about beyond an identifier -- built as a TOOL anyway, forcing a
    model or decision step to explicitly choose to call it before this
    already-available data can be used at all."""
    return [dict(o, order_id=oid) for oid, o in ORDERS.items() if o["customer"] == customer_name]


def decide_next_naive(observations: list[dict]):
    """[REAL] A decision function that must explicitly plan a tool call
    just to retrieve data that never needed a decision in the first
    place -- an extra planning step purely because of how it was modeled."""
    if not observations:
        return "get_customer_orders", {"customer_name": "Priya Nair"}
    return "stop", {}


steps_taken = []
observations: list[dict] = []
while True:
    action, args = decide_next_naive(observations)
    if action == "stop":
        break
    steps_taken.append(action)
    observations.append({"action": action, "result": get_customer_orders_as_tool(**args)})

print(f"  Modeled as a TOOL: retrieving Priya Nair's orders required")
print(f"  {len(steps_taken)} explicit decision step(s): {steps_taken}")
print(f"    result: {observations[0]['result']}")

as_resource = read_resource  # reuse section 2's mechanism directly
RESOURCES["orders://by_customer/Priya Nair"] = lambda: [
    dict(o, order_id=oid) for oid, o in ORDERS.items() if o["customer"] == "Priya Nair"
]
resource_result = as_resource("orders://by_customer/Priya Nair")
print(f"\n  Modeled as a RESOURCE: retrieving the identical data required")
print(f"  0 decision steps -- a host can read it directly:")
print(f"    result: {resource_result}")

print("\n  Both paths returned the SAME underlying data. The tool-based path")
print("  forced something to explicitly plan and decide to call a function")
print("  before the data was available at all -- for information that was")
print("  never actually a decision, only a lookup. Modeling it as a")
print("  resource instead removes that pointless planning step entirely.")


# ============================================================ 5
rule("5. WHAT THIS LAB IS AND IS NOT")

print("  REAL: every tool call, resource read, and prompt render above is")
print("  genuinely executed; section 4's step-count comparison (1 decision")
print("  step for the tool-based design versus 0 for the resource-based")
print("  one) is a measured result of actually running both paths against")
print("  the identical underlying data.")
print("\n  ILLUSTRATIVE: this lab's URI scheme ('orders://...') is a small,")
print("  hand-chosen convention for this lesson -- real MCP resource URIs")
print("  follow the server's own scheme design.")
print("\n  NOT SHOWN: resource subscriptions and update notifications, prompt")
print("  arguments with their own schemas, and the full initialization/")
print("  capability-negotiation handshake that tells a client which of the")
print("  three primitives a specific server actually supports (M9-L05).")

print("\nDone.")
