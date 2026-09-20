"""M9-L06 lab -- discovery (tools/list, resources/list, resources/templates/list,
prompts/list) and invocation (tools/call, resources/read, prompts/get) against a
2026-07-28-shaped server, measuring the client mistakes each rule prevents:

  1. pagination: reading one page, assuming a page size, fabricating cursors,
  2. deterministic ordering, and why it matters for LLM prompt caching,
  3. ttlMs freshness vs always-refetch vs cache-forever, with a list change,
  4. cacheScope: a shared gateway cache that leaks a per-user tool list,
  5. resource templates: naive string replacement vs RFC 6570 encoding,
  6. prompts/get argument checking,
  7. a tools/call that returns resultType "input_required" and the retry that
     completes it (multi round-trip requests).

Per-request _meta validation was M9-L05's subject and is omitted here for brevity.
Deterministic (seeded). No API key, no network, no third-party dependencies.
Run:  python labs/m9/l06_discovery_invocation.py
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import random
import sys
from urllib.parse import quote

sys.stdout.reconfigure(encoding="utf-8")


def rule(title: str) -> None:
    print(f"\n{'=' * 76}\n{title}\n{'=' * 76}")


SECRET = b"lab-only-server-secret"


def error(code: int, message: str) -> dict:
    return {"error": {"code": code, "message": message}}


# ============================================================ 1
rule("1. PAGINATION: CURSORS ARE OPAQUE AND PAGE SIZE IS THE SERVER'S CHOICE")

ALL_TOOLS = [{"name": f"report_{i:02d}", "description": f"Report number {i}.",
              "inputSchema": {"type": "object", "additionalProperties": False}} for i in range(47)]


class ListingServer:
    def __init__(self, page_size: int):
        self.page_size = page_size

    def _cursor(self, offset: int) -> str:
        body = base64.urlsafe_b64encode(json.dumps({"o": offset}).encode()).decode()
        sig = hmac.new(SECRET, body.encode(), hashlib.sha256).hexdigest()[:12]
        return f"{body}.{sig}"

    def _offset(self, cursor: str) -> int | None:
        body, _, sig = cursor.partition(".")
        good = hmac.new(SECRET, body.encode(), hashlib.sha256).hexdigest()[:12]
        if not hmac.compare_digest(sig, good):
            return None
        return json.loads(base64.urlsafe_b64decode(body))["o"]

    def tools_list(self, cursor: str | None = None) -> dict:
        offset = 0 if cursor is None else self._offset(cursor)
        if offset is None:
            return error(-32602, "Invalid params: invalid cursor")
        page = ALL_TOOLS[offset: offset + self.page_size]
        result = {"resultType": "complete", "tools": page, "ttlMs": 300_000, "cacheScope": "public"}
        if offset + self.page_size < len(ALL_TOOLS):
            result["nextCursor"] = self._cursor(offset + self.page_size)
        return {"result": result}


def client_first_page_only(server):
    return len(server.tools_list()["result"]["tools"])


def client_assumes_page_size_20(server):
    seen, cursor = 0, None
    while True:
        r = server.tools_list(cursor)["result"]
        seen += len(r["tools"])
        if len(r["tools"]) < 20:          # the bug: "a short page means the end"
            return seen
        cursor = r.get("nextCursor")
        if cursor is None:
            return seen


def client_fabricates_offset_cursor(server):
    first = server.tools_list()["result"]
    second = server.tools_list(cursor=str(len(first["tools"])))
    return len(first["tools"]) if "error" in second else len(first["tools"]) + len(second["result"]["tools"])


def client_follows_next_cursor(server):
    seen, cursor = 0, None
    while True:
        r = server.tools_list(cursor)["result"]
        seen += len(r["tools"])
        cursor = r.get("nextCursor")
        if cursor is None:            # only an ABSENT nextCursor ends the list
            return seen


for size in (20, 15):
    server = ListingServer(page_size=size)
    print(f"  server page size {size}, {len(ALL_TOOLS)} tools in total:")
    for fn in (client_first_page_only, client_assumes_page_size_20,
               client_fabricates_offset_cursor, client_follows_next_cursor):
        print(f"    {fn.__name__:<34} saw {fn(server):>2}/{len(ALL_TOOLS)} tools")
bad = ListingServer(20).tools_list(cursor="20")
print(f"\n  a fabricated cursor '20' -> {bad['error']}")


# ============================================================ 2
rule("2. DETERMINISTIC ORDER: WHY THE SAME LIST MUST SERIALIZE THE SAME WAY")

rng = random.Random(606)
small = ALL_TOOLS[:8]
unordered, ordered = set(), set()
for _ in range(10):
    shuffled = small[:]
    rng.shuffle(shuffled)                      # e.g. tools collected from a dict of plugins
    unordered.add(hashlib.sha256(json.dumps(shuffled).encode()).hexdigest()[:10])
    ordered.add(hashlib.sha256(json.dumps(sorted(small, key=lambda t: t["name"])).encode()).hexdigest()[:10])
print(f"  10 tools/list calls, same 8 tools, serialized into the model's context:")
print(f"    server returning arbitrary order : {len(unordered)} distinct serializations")
print(f"    server returning a stable order  : {len(ordered)} distinct serialization")
print("\n  Hosts usually place tool definitions at the START of the model's context.")
print("  A provider's prompt cache matches on an identical prefix, so every")
print("  reordering is a cache miss on the entire tool block. The 2026-07-28 spec")
print("  says servers SHOULD return tools in a deterministic order for this reason.")


# ============================================================ 3
rule("3. ttlMs: FRESHNESS HINTS VS ALWAYS-REFETCH VS CACHE-FOREVER")

TTL_S = 300
CHANGE_AT = 200                     # report_03 is removed at t=200s; server notifies subscribers
needs = list(range(0, 601, 5))      # the host needs the tool list every 5 s for 10 minutes


def tools_at(t):
    return {t_["name"] for t_ in small if not (t >= CHANGE_AT and t_["name"] == "report_03")}


def simulate(policy: str):
    fetches, stale_uses, cached, received = 0, 0, None, None
    for t in needs:
        invalidated = policy == "ttl+notifications" and received is not None and received < CHANGE_AT <= t
        fresh = cached is not None and not invalidated and (
            policy == "forever" or (policy != "always" and t < received + TTL_S))
        if not fresh:
            cached, received = tools_at(t), t
            fetches += 1
        if cached != tools_at(t):
            stale_uses += 1
    return fetches, stale_uses


print(f"  {len(needs)} moments the host needs the list; ttlMs={TTL_S * 1000}; a tool is removed at t={CHANGE_AT}s")
for policy in ("always", "ttl+notifications", "ttl only", "forever"):
    f, s = simulate(policy)
    print(f"    {policy:<18} server fetches: {f:>3}   uses of a stale list: {s:>2}")
print("\n  TTL is a freshness hint, not a guarantee: without the list_changed")
print("  notification the TTL-only client used a stale list until the TTL ran out.")


# ============================================================ 4
rule("4. cacheScope: A SHARED GATEWAY CACHE AND A PER-USER TOOL LIST")

USER_TOOLS = {"admin": ["read_report", "delete_report", "export_all_users"], "analyst": ["read_report"]}


def per_user_tools_list(user: str, declared_scope: str) -> dict:
    return {"tools": USER_TOOLS[user], "cacheScope": declared_scope}


def gateway(requests_in_order, declared_scope):
    cache, leaks = {}, []
    for user in requests_in_order:
        key = ("tools/list",) if declared_scope == "public" else ("tools/list", user)
        if key not in cache:
            cache[key] = per_user_tools_list(user, declared_scope)
        served = cache[key]["tools"]
        leaked = sorted(set(served) - set(USER_TOOLS[user]))
        if leaked:
            leaks.append((user, leaked))
    return leaks


order = ["admin", "analyst", "analyst", "admin", "analyst"]
for scope in ("public", "private"):
    leaks = gateway(order, scope)
    print(f"  server marks the per-user list '{scope}': {len(leaks)} leak(s) {leaks[:1]}")
print("\n  A 'public' result may be served to ANY caller by a shared cache. A list")
print("  that varies by user must be 'private' -- and the server must still check")
print("  authorization on every tools/call, because cacheScope is not a control.")


# ============================================================ 5
rule("5. RESOURCE TEMPLATES: RFC 6570 EXPANSION VS STRING REPLACE")

TEMPLATE = {"uriTemplate": "orders://{order_id}", "name": "order", "mimeType": "application/json"}
ORDERS = {"O-1001": {"amount": 40.0, "status": "delivered"}}


def naive_expand(template: str, **values) -> str:
    return template.replace("{order_id}", values["order_id"])


def rfc6570_simple_expand(template: str, **values) -> str:
    return template.replace("{order_id}", quote(values["order_id"], safe=""))


def resources_read(uri: str) -> dict:
    key = uri.removeprefix("orders://")
    if key not in ORDERS:
        return error(-32602, f"Resource not found: {uri}")
    return {"result": {"resultType": "complete", "ttlMs": 0, "cacheScope": "private",
                       "contents": [{"uri": uri, "mimeType": "application/json", "text": json.dumps(ORDERS[key])}]}}


for value in ("O-1001", "../admin/keys", "O-1001?export=all", "O 1001"):
    n, s = naive_expand(TEMPLATE["uriTemplate"], order_id=value), rfc6570_simple_expand(TEMPLATE["uriTemplate"], order_id=value)
    print(f"  value {value!r:<22} naive -> {n:<30} RFC 6570 -> {s}")
print(f"\n  resources/read orders://O-1001 -> {resources_read('orders://O-1001')['result']['contents'][0]['text']}")
print(f"  resources/read orders://O-9999 -> {resources_read('orders://O-9999')['error']}")
print("  (2026-07-28 uses -32602 for 'not found'; clients SHOULD still accept a")
print("  legacy server's -32002.)")


# ============================================================ 6
rule("6. PROMPTS: DECLARED ARGUMENTS ARE CHECKED ON prompts/get")

PROMPT = {"name": "summarize_ticket", "description": "Summarize a support ticket for a manager.",
          "arguments": [{"name": "ticket_id", "required": True}, {"name": "tone", "required": False}]}


def prompts_get(name: str, arguments: dict) -> dict:
    missing = [a["name"] for a in PROMPT["arguments"] if a.get("required") and a["name"] not in arguments]
    if name != PROMPT["name"] or missing:
        return error(-32602, f"Invalid params: missing required argument(s) {missing}")
    tone = arguments.get("tone", "neutral")
    return {"result": {"resultType": "complete", "messages": [
        {"role": "user", "content": {"type": "text",
                                     "text": f"Summarize ticket {arguments['ticket_id']} in a {tone} tone for a manager."}}]}}


print(f"  prompts/get with ticket_id  -> {prompts_get('summarize_ticket', {'ticket_id': 'T-7'})['result']['messages']}")
print(f"  prompts/get without it      -> {prompts_get('summarize_ticket', {'tone': 'formal'})['error']}")


# ============================================================ 7
rule("7. INVOCATION: AN input_required RESULT AND THE RETRY THAT COMPLETES IT")


def sign(payload: dict) -> str:
    body = base64.urlsafe_b64encode(json.dumps(payload, sort_keys=True).encode()).decode()
    return body + "." + hmac.new(SECRET, body.encode(), hashlib.sha256).hexdigest()[:16]


def verify(state: str) -> dict | None:
    body, _, sig = state.partition(".")
    if not hmac.compare_digest(sig, hmac.new(SECRET, body.encode(), hashlib.sha256).hexdigest()[:16]):
        return None
    return json.loads(base64.urlsafe_b64decode(body))


def tools_call(params: dict) -> dict:
    args = params["arguments"]
    state = verify(params["requestState"]) if "requestState" in params else None
    answer = (params.get("inputResponses") or {}).get("confirm")
    if state and state.get("report_id") == args["report_id"] and answer and answer.get("action") == "accept":
        return {"resultType": "complete", "isError": False,
                "content": [{"type": "text", "text": f"Report {args['report_id']} shared with {args['to_user']}."}],
                "structuredContent": {"report_id": args["report_id"], "shared_with": args["to_user"]}}
    return {"resultType": "input_required",
            "inputRequests": {"confirm": {"method": "elicitation/create", "params": {
                "mode": "form", "message": f"Share report {args['report_id']} with {args['to_user']}?",
                "requestedSchema": {"type": "object", "properties": {"ok": {"type": "boolean"}}}}}},
            "requestState": sign({"report_id": args["report_id"], "tool": "share_report"})}


def run_client(echo_state: bool, max_rounds: int = 3):
    rid, params, log = 1, {"name": "share_report", "arguments": {"report_id": "R-12", "to_user": "maya"}}, []
    for _ in range(max_rounds):
        result = tools_call(params)
        log.append((rid, result["resultType"]))
        if result["resultType"] == "complete":
            return log, result
        retry = dict(params, inputResponses={"confirm": {"action": "accept", "content": {"ok": True}}})
        if echo_state:
            retry["requestState"] = result["requestState"]
        rid, params = rid + 1, retry          # a retry is a NEW request with a NEW id
    return log, None


for echo in (True, False):
    log, final = run_client(echo_state=echo)
    label = "echoes requestState" if echo else "drops requestState "
    outcome = final["structuredContent"] if final else "gave up"
    print(f"  client that {label}: rounds {log} -> {outcome}")
print("\n  The server kept no memory between rounds: everything it needed came back")
print("  in the retry. A client that drops requestState is simply asked again.")


# ============================================================ 8
rule("8. WHAT THIS LAB IS AND IS NOT")
print("  REAL: every count above comes from running the clients against these")
print("  servers: tools seen per pagination strategy, distinct serializations,")
print("  fetches and stale uses per caching policy, gateway leaks, expansions,")
print("  and the input_required round trips.")
print("\n  ILLUSTRATIVE: time in section 3 is simulated; cursors and requestState are")
print("  signed with a hard-coded lab secret (never do this in a real server).")
print("\n  NOT SHOWN: per-request _meta (M9-L05), input/output schema validation")
print("  (M9-L07), subscriptions/listen streams over a real transport (M9-L08),")
print("  and requestState replay protection with principal and expiry (M9-L13).")
print("\nDone.")
