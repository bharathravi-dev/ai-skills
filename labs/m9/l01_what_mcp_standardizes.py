"""M9-L01 lab -- opening Module 9. MCP (Model Context Protocol) standardizes the
CALLING CONVENTION between a host application and a tool/data server: how tools
are listed, how they are invoked, and the shape of what comes back -- the same
shape regardless of what domain a server actually implements. This lab builds
two completely unrelated "MCP-style" servers (refunds, weather) and shows their
tools/list and tools/call messages are IDENTICALLY shaped. It then reuses
M8-L03's own run_tool_loop() UNMODIFIED to show what MCP explicitly does NOT
standardize: which tool to call and when (the host's own decision step) and
what a tool actually does internally (its business logic) -- both left
entirely outside the protocol.

Deterministic. No API key, no network, no third-party dependencies. The
JSON-RPC 2.0 envelope shown here is simplified for illustration; its full
structure is this module's own M9-L04 topic.
Run:  python labs/m9/l01_what_mcp_standardizes.py
"""

from __future__ import annotations

import sys

sys.stdout.reconfigure(encoding="utf-8")


def rule(title: str) -> None:
    print(f"\n{'=' * 76}\n{title}\n{'=' * 76}")


# ============================================================ 1
rule("1. THE STANDARDIZED SHAPE: A 'tools/list' RESPONSE")


def make_tools_list_response(request_id: int, tools: list[dict]) -> dict:
    """[REAL] The standardized envelope MCP defines for listing a server's
    available tools -- a JSON-RPC 2.0 result carrying a fixed 'tools' array,
    each entry with a fixed shape (name, description, inputSchema)."""
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "result": {"tools": tools},
    }


REFUND_TOOLS = [
    {
        "name": "search_orders",
        "description": "Find an order id by customer name.",
        "inputSchema": {"type": "object", "properties": {"name": {"type": "string"}}, "required": ["name"]},
    },
    {
        "name": "issue_refund",
        "description": "Issue a refund for an order.",
        "inputSchema": {"type": "object", "properties": {"order_id": {"type": "string"}, "amount": {"type": "number"}}, "required": ["order_id", "amount"]},
    },
]

WEATHER_TOOLS = [
    {
        "name": "get_forecast",
        "description": "Get a weather forecast for a city.",
        "inputSchema": {"type": "object", "properties": {"city": {"type": "string"}}, "required": ["city"]},
    },
]

refund_list_response = make_tools_list_response(1, REFUND_TOOLS)
weather_list_response = make_tools_list_response(1, WEATHER_TOOLS)

print("  A refund server's tools/list response:")
print(f"    {refund_list_response}\n")
print("  A completely unrelated weather server's tools/list response:")
print(f"    {weather_list_response}")

print("\n  Both responses share the IDENTICAL envelope shape -- 'jsonrpc',")
print("  'id', and a 'result.tools' array of {name, description, inputSchema}")
print("  entries -- despite the two servers having nothing in common beyond")
print("  both speaking MCP. This shared shape is exactly what the protocol")
print("  standardizes: not what a tool does, but how any tool is DESCRIBED.")


# ============================================================ 2
rule("2. THE STANDARDIZED SHAPE: A 'tools/call' REQUEST AND RESPONSE")

CUSTOMERS = {"Priya Nair": "O-1001"}
ORDERS = {"O-1001": {"amount": 40.0}}
FORECASTS = {"Austin": "72F, clear"}


def refund_server_call(name: str, arguments: dict) -> dict:
    """[REAL] The refund server's own tool implementations, called only
    through the standardized dispatch below -- their internals are entirely
    the server's own business, invisible to the calling convention itself."""
    if name == "search_orders":
        return {"order_id": CUSTOMERS.get(arguments["name"], "NOT_FOUND")}
    if name == "issue_refund":
        return {"status": "refunded", "order_id": arguments["order_id"], "amount": arguments["amount"]}
    raise ValueError(f"unknown tool {name!r}")


def weather_server_call(name: str, arguments: dict) -> dict:
    """[REAL] A completely unrelated server's own implementation."""
    if name == "get_forecast":
        return {"forecast": FORECASTS.get(arguments["city"], "unknown")}
    raise ValueError(f"unknown tool {name!r}")


def make_tools_call_request(request_id: int, name: str, arguments: dict) -> dict:
    """[REAL] The standardized envelope for INVOKING a tool -- identical
    shape regardless of which server or tool it targets."""
    return {"jsonrpc": "2.0", "id": request_id, "method": "tools/call",
            "params": {"name": name, "arguments": arguments}}


def make_tools_call_response(request_id: int, content: dict) -> dict:
    """[REAL] The standardized envelope for a tool's RESULT."""
    return {"jsonrpc": "2.0", "id": request_id, "result": {"content": content}}


def dispatch(server_call, request: dict) -> dict:
    """[REAL] A minimal, generic dispatcher -- unpacks the standardized
    request shape, calls the server's own function, wraps the result in the
    standardized response shape. The SAME dispatcher works for either
    server, because the envelope, not the tool, is what it depends on."""
    params = request["params"]
    result = server_call(params["name"], params["arguments"])
    return make_tools_call_response(request["id"], result)


refund_request = make_tools_call_request(2, "issue_refund", {"order_id": "O-1001", "amount": 40.0})
weather_request = make_tools_call_request(2, "get_forecast", {"city": "Austin"})

refund_response = dispatch(refund_server_call, refund_request)
weather_response = dispatch(weather_server_call, weather_request)

print("  A refund tools/call request and response:")
print(f"    request:  {refund_request}")
print(f"    response: {refund_response}\n")
print("  A weather tools/call request and response, through the SAME dispatch():")
print(f"    request:  {weather_request}")
print(f"    response: {weather_response}")

print("\n  The identical dispatch() function handled both -- it never once")
print("  needed to know anything about refunds or weather. This is the")
print("  concrete meaning of 'MCP standardizes the calling convention': one")
print("  generic caller works against any server that speaks the same shape.")


# ============================================================ 3
rule("3. WHAT MCP DOES NOT STANDARDIZE: WHICH TOOL TO CALL, AND WHEN")


def run_tool_loop(decide_next, execute_tool, max_steps: int = 10) -> list[dict]:
    """[REAL, M8-L03's own function, unchanged] The general tool-execution
    loop this course built from scratch -- reused here completely as-is."""
    observations: list[dict] = []
    for _ in range(max_steps):
        action, args = decide_next(observations)
        if action == "stop":
            break
        try:
            result = execute_tool(action, args)
            observations.append({"action": action, "args": args, "result": result, "error": None})
        except Exception as exc:
            observations.append({"action": action, "args": args, "result": None, "error": str(exc)})
    return observations


def mcp_style_execute(action: str, args: dict) -> dict:
    """[REAL] Every tool call, regardless of which tool, goes through the
    same standardized request/response envelope built in section 2."""
    request = make_tools_call_request(len(TRACE_IDS) + 1, action, args)
    TRACE_IDS.append(request["id"])
    response = dispatch(refund_server_call, request)
    return response["result"]["content"]


TRACE_IDS: list[int] = []


def decide_next_for_refund_request(observations: list[dict]):
    """[REAL] This decision function is the HOST's own logic -- nothing
    about it is defined or constrained by MCP itself. MCP has no opinion on
    whether this looks up the order first, skips straight to a refund, or
    never calls issue_refund at all."""
    if not observations:
        return "search_orders", {"name": "Priya Nair"}
    if len(observations) == 1:
        order_id = observations[0]["result"]["order_id"]
        return "issue_refund", {"order_id": order_id, "amount": 40.0}
    return "stop", {}


trace = run_tool_loop(decide_next_for_refund_request, mcp_style_execute)
print("  Running M8-L03's own run_tool_loop(), completely unmodified, against")
print("  tools reached only through the standardized MCP-style envelope:\n")
for entry in trace:
    print(f"    [{entry['action']}] args={entry['args']} -> result={entry['result']!r}")

print("\n  Every call above passed through the identical standardized")
print("  envelope from section 2 -- but WHICH tool to call, and in what")
print("  order, came entirely from decide_next_for_refund_request(), a")
print("  function MCP's own specification says nothing about. A host could")
print("  have used a hand-written decision function like this one, a full")
print("  model-driven agent loop, or a fixed workflow -- MCP standardizes")
print("  none of that choice.")


# ============================================================ 4
rule("4. WHAT MCP DOES NOT STANDARDIZE: A TOOL'S OWN BUSINESS LOGIC")


def issue_refund_v1(order_id: str, amount: float) -> dict:
    """[REAL] One possible implementation behind the 'issue_refund' name --
    unconditionally accepts any amount."""
    return {"status": "refunded", "order_id": order_id, "amount": amount}


def issue_refund_v2(order_id: str, amount: float) -> dict:
    """[REAL] A different, more careful implementation behind the SAME
    tool name and the SAME inputSchema -- caps the amount to the order's own
    real total, something section 1's schema says nothing about."""
    real_amount = ORDERS.get(order_id, {}).get("amount", 0.0)
    capped = min(amount, real_amount)
    return {"status": "refunded", "order_id": order_id, "amount": capped}


requested = {"order_id": "O-1001", "amount": 999.0}
result_v1 = issue_refund_v1(**requested)
result_v2 = issue_refund_v2(**requested)

print(f"  A single request, {requested!r}, sent to two different servers")
print(f"  both exposing a tool literally named 'issue_refund' with the")
print(f"  identical inputSchema from section 1:\n")
print(f"    server using issue_refund_v1 -> {result_v1!r}")
print(f"    server using issue_refund_v2 -> {result_v2!r}")

print("\n  Both servers are equally valid MCP servers -- the protocol")
print("  standardizes the NAME, the DESCRIPTION, and the INPUT SCHEMA a")
print("  client sees, and the envelope a call travels in. It says nothing")
print("  about what the tool actually DOES with a validated request, which")
print("  is why the identical request produced two entirely different real")
print("  outcomes here.")


# ============================================================ 5
rule("5. WHAT THIS LAB IS AND IS NOT")

print("  REAL: every tools/list and tools/call message above is a genuinely")
print("  constructed dict matching the envelope MCP defines; dispatch() and")
print("  run_tool_loop() are genuinely, identically reused across both")
print("  domains and both refund implementations; every printed trace is a")
print("  measured result of actually running this code.")
print("\n  ILLUSTRATIVE: this lab's JSON-RPC envelope is simplified for this")
print("  lesson's purpose -- the real JSON-RPC 2.0 structure MCP actually")
print("  uses (including error objects and notification messages) is this")
print("  module's own M9-L04 topic.")
print("\n  NOT SHOWN: real network transport (M9-L08), capability negotiation")
print("  during initialization (M9-L05), resources and prompts -- the other")
print("  two MCP primitives beyond tools (M9-L03) -- and authorization over")
print("  who may call a tool at all (M9-L10 through M9-L13).")

print("\nDone.")
