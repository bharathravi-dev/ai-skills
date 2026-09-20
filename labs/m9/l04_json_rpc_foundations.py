"""M9-L04 lab -- M9-L01 to M9-L03 used a simplified JSON-RPC envelope. This lab
builds the real thing: a JSON-RPC 2.0 message classifier and dispatcher that
applies MCP's stricter rules on top of base JSON-RPC (ids are strings or
integers and never null; one message per frame, no batches), then measures
the failure modes that the envelope rules exist to prevent:

  * a client that matches responses by ARRIVAL ORDER instead of by id,
  * a client that REUSES an id while an earlier request is still in flight,
  * a server that answers NOTIFICATIONS,
  * a Python-specific trap: isinstance(True, int) is True, and 1 == 1.0 == True
    as dict keys -- so a naive validator accepts ids that collide.

Deterministic (seeded). No API key, no network, no third-party dependencies.
Run:  python labs/m9/l04_json_rpc_foundations.py
"""

from __future__ import annotations

import json
import random
import sys

sys.stdout.reconfigure(encoding="utf-8")


def rule(title: str) -> None:
    print(f"\n{'=' * 76}\n{title}\n{'=' * 76}")


PARSE_ERROR, INVALID_REQUEST, METHOD_NOT_FOUND, INVALID_PARAMS, INTERNAL_ERROR = (
    -32700, -32600, -32601, -32602, -32603,
)


# ============================================================ 1
rule("1. THE FOUR MESSAGE SHAPES, CLASSIFIED BY A STRICT VALIDATOR")


def valid_id(value) -> bool:
    """[REAL] MCP: an id is a string or an integer, and MUST NOT be null.
    bool is excluded explicitly because in Python isinstance(True, int) is True."""
    return isinstance(value, str) or (isinstance(value, int) and not isinstance(value, bool))


def classify(msg) -> str:
    """[REAL] Returns request / notification / result / error / INVALID(reason)."""
    if not isinstance(msg, dict):
        return "INVALID(batch arrays are not allowed in MCP)" if isinstance(msg, list) else "INVALID(not an object)"
    if msg.get("jsonrpc") != "2.0":
        return "INVALID(jsonrpc must be exactly '2.0')"
    has_id = "id" in msg
    if "method" in msg:
        if not isinstance(msg["method"], str):
            return "INVALID(method must be a string)"
        if "result" in msg or "error" in msg:
            return "INVALID(has both method and result/error)"
        if not has_id:
            return "notification"
        return "request" if valid_id(msg["id"]) else f"INVALID(bad request id {msg['id']!r})"
    if "result" in msg and "error" in msg:
        return "INVALID(has both result and error)"
    if "result" in msg:
        return "result" if has_id and valid_id(msg["id"]) else "INVALID(result needs a valid id)"
    if "error" in msg:
        err = msg["error"]
        if not (isinstance(err, dict) and isinstance(err.get("code"), int) and isinstance(err.get("message"), str)):
            return "INVALID(error needs integer code and string message)"
        return "error"
    return "INVALID(no method, result or error)"


CANDIDATES = [
    {"jsonrpc": "2.0", "id": 1, "method": "tools/list"},
    {"jsonrpc": "2.0", "method": "notifications/cancelled", "params": {"requestId": 1}},
    {"jsonrpc": "2.0", "id": 1, "result": {"resultType": "complete", "tools": []}},
    {"jsonrpc": "2.0", "id": 1, "error": {"code": -32601, "message": "Method not found"}},
    {"jsonrpc": "2.0", "id": None, "method": "tools/list"},
    {"jsonrpc": "2.0", "id": True, "method": "tools/list"},
    {"jsonrpc": "2.0", "id": 1.5, "method": "tools/list"},
    {"jsonrpc": "1.0", "id": 1, "method": "tools/list"},
    {"jsonrpc": "2.0", "id": 1, "result": {}, "error": {"code": 1, "message": "x"}},
    [{"jsonrpc": "2.0", "id": 1, "method": "tools/list"}],
]
for c in CANDIDATES:
    print(f"  {classify(c):<52} <- {json.dumps(c)[:60]}")


# ============================================================ 2
rule("2. A DISPATCHER THAT RETURNS THE RIGHT STANDARD ERROR CODE")

TOOLS = {"add": lambda a, b: a + b}


def dispatch_raw(raw: str):
    """[REAL] One frame in, at most one frame out. Returns None for notifications."""
    try:
        msg = json.loads(raw)
    except json.JSONDecodeError:
        return {"jsonrpc": "2.0", "id": None, "error": {"code": PARSE_ERROR, "message": "Parse error"}}
    kind = classify(msg)
    if kind == "notification":
        return None
    if kind != "request":
        rid = msg.get("id") if isinstance(msg, dict) and valid_id(msg.get("id")) else None
        return {"jsonrpc": "2.0", "id": rid, "error": {"code": INVALID_REQUEST, "message": kind}}
    rid, method, params = msg["id"], msg["method"], msg.get("params", {})
    if method != "tools/call":
        return {"jsonrpc": "2.0", "id": rid, "error": {"code": METHOD_NOT_FOUND, "message": f"Method not found: {method}"}}
    name, arguments = params.get("name"), params.get("arguments")
    if name not in TOOLS or not isinstance(arguments, dict):
        return {"jsonrpc": "2.0", "id": rid, "error": {"code": INVALID_PARAMS, "message": f"Invalid params: {name!r}"}}
    try:
        value = TOOLS[name](**arguments)
    except TypeError as exc:
        return {"jsonrpc": "2.0", "id": rid, "error": {"code": INVALID_PARAMS, "message": str(exc)}}
    except Exception as exc:  # pragma: no cover - defensive
        return {"jsonrpc": "2.0", "id": rid, "error": {"code": INTERNAL_ERROR, "message": str(exc)}}
    return {"jsonrpc": "2.0", "id": rid, "result": {"resultType": "complete",
            "content": [{"type": "text", "text": str(value)}], "isError": False}}


RAW_INPUTS = [
    ('valid call', '{"jsonrpc":"2.0","id":7,"method":"tools/call","params":{"name":"add","arguments":{"a":2,"b":3}}}'),
    ('truncated JSON', '{"jsonrpc":"2.0","id":8,"method":"tools/ca'),
    ('null id', '{"jsonrpc":"2.0","id":null,"method":"tools/call"}'),
    ('unknown method', '{"jsonrpc":"2.0","id":9,"method":"tools/delete"}'),
    ('unknown tool', '{"jsonrpc":"2.0","id":10,"method":"tools/call","params":{"name":"sub","arguments":{}}}'),
    ('wrong arg names', '{"jsonrpc":"2.0","id":11,"method":"tools/call","params":{"name":"add","arguments":{"x":1}}}'),
    ('notification', '{"jsonrpc":"2.0","method":"notifications/cancelled","params":{"requestId":7}}'),
]
for label, raw in RAW_INPUTS:
    out = dispatch_raw(raw)
    if out is None:
        shown = "(no response -- notifications are never answered)"
    elif "error" in out:
        shown = f"error {out['error']['code']} id={out['id']!r}: {out['error']['message'][:62]}"
    else:
        shown = f"result id={out['id']!r}: {out['result']['content'][0]['text']}"
    print(f"  {label:<16} -> {shown}")

print("\n  The truncated frame gets id=None: the server could not read the id, so")
print("  it cannot correlate the error with any request. That is the ONLY case")
print("  in which an error response may omit or null the id.")


# ============================================================ 3
rule("3. CORRELATION: MATCHING RESPONSES BY ARRIVAL ORDER VS BY ID")

rng = random.Random(404)
N = 20
requests = [{"jsonrpc": "2.0", "id": i, "method": "tools/call",
             "params": {"name": "add", "arguments": {"a": i, "b": 100}}} for i in range(1, N + 1)]
responses = [dispatch_raw(json.dumps(r)) for r in requests]
completion_order = responses[:]
rng.shuffle(completion_order)  # a concurrent server finishes in any order

by_order = {req["id"]: resp for req, resp in zip(requests, completion_order)}
by_id = {resp["id"]: resp for resp in completion_order}


def expected(i: int) -> str:
    return str(i + 100)


wrong_order = sum(by_order[i]["result"]["content"][0]["text"] != expected(i) for i in range(1, N + 1))
wrong_id = sum(by_id[i]["result"]["content"][0]["text"] != expected(i) for i in range(1, N + 1))
print(f"  {N} in-flight requests, responses arriving in a shuffled order:")
print(f"    client matching by ARRIVAL ORDER : {wrong_order:>2}/{N} requests got someone else's answer")
print(f"    client matching by ID            : {wrong_id:>2}/{N} requests got someone else's answer")

trials, total_wrong = 1000, 0
for _ in range(trials):
    rng.shuffle(completion_order)
    total_wrong += sum(
        req["id"] != resp["id"] for req, resp in zip(requests, completion_order))
print(f"\n  Over {trials} shuffles, arrival-order matching misrouted "
      f"{total_wrong / (trials * N):.1%} of responses on average.")
print("  With only ONE request in flight at a time it would never fail -- which is")
print("  why this bug survives every sequential test and appears under load.")


# ============================================================ 4
rule("4. REUSING AN ID WHILE THE FIRST REQUEST IS STILL IN FLIGHT")

pending: dict = {}
lost = []
for rid, (a, b) in [(5, (1, 1)), (5, (40, 2))]:  # the bug: the same id twice
    if rid in pending:
        lost.append(pending[rid])
    pending[rid] = {"a": a, "b": b}
print(f"  pending table after sending two requests with id=5: {pending}")
print(f"  request silently overwritten and never resolvable: {lost}")
resp = dispatch_raw(json.dumps({"jsonrpc": "2.0", "id": 5, "method": "tools/call",
                                 "params": {"name": "add", "arguments": {"a": 1, "b": 1}}}))
print(f"  the server answers the FIRST request (1+1) with id 5 -> "
      f"{resp['result']['content'][0]['text']!r}")
print(f"  the client resolves it against {pending[5]} and reports 2 as the answer to 40+2.")


# ============================================================ 5
rule("5. THE PYTHON TRAP: NAIVE ID CHECKS ACCEPT IDS THAT COLLIDE")


def naive_valid_id(value) -> bool:
    return isinstance(value, (str, int))


ids = [1, 1.0, True, "1"]
print("  candidate ids:      ", ids)
print("  naive isinstance    :", [naive_valid_id(v) for v in ids])
print("  strict valid_id()   :", [valid_id(v) for v in ids])
table = {}
for v in ids:
    table[v] = f"request sent with id {v!r}"
print(f"  a dict keyed by these four ids holds {len(table)} entries: {table}")
print("\n  1, 1.0 and True are ONE dict key in Python (they hash and compare equal),")
print("  so a client keyed on raw ids silently merges three different requests.")
print("  '1' stays separate -- a string id and an integer id are distinct in JSON-RPC.")


# ============================================================ 6
rule("6. BATCHES AND ANSWERED NOTIFICATIONS")

batch = json.dumps([requests[0], requests[1]])
print(f"  batch of two requests -> {dispatch_raw(batch)['error']}")
print("  JSON-RPC 2.0 permits batches; MCP 2025-03-26 briefly supported them and")
print("  2025-06-18 removed them. A current server rejects the array outright.")


def chatty_server(raw: str):
    """[REAL, deliberately wrong] answers notifications as if they were requests."""
    msg = json.loads(raw)
    return {"jsonrpc": "2.0", "id": msg.get("id"), "result": {"resultType": "complete"}}


notes = [json.dumps({"jsonrpc": "2.0", "method": "notifications/cancelled",
                     "params": {"requestId": i}}) for i in range(3)]
strays = [chatty_server(n) for n in notes]
print(f"\n  a chatty server answered 3 notifications with: {[s['id'] for s in strays]}")
print("  Each stray response has id=None, matches no pending request, and a lenient")
print("  client that resolves 'the oldest pending request' on any response would")
print("  hand these empty results to three real requests.")


# ============================================================ 7
rule("7. WHAT THIS LAB IS AND IS NOT")
print("  REAL: every classification, error code and correlation count above is the")
print("  output of running the validator and dispatcher in this file. Section 3's")
print("  misrouting rate is measured over 1,000 seeded shuffles.")
print("\n  ILLUSTRATIVE: a single-process 'server'; concurrency is simulated by")
print("  shuffling completion order rather than by real threads.")
print("\n  NOT SHOWN: the MCP-specific _meta fields every request now carries")
print("  (M9-L05), transport framing over stdio and HTTP (M9-L08), and the")
print("  protocol-level error codes MCP adds in -32020..-32099 (M9-L05, M9-L14).")
print("\nDone.")
