"""M9-L05 lab -- how an MCP client and server agree on a protocol version and on
what each side can do. Two eras exist side by side in September 2026:

  LEGACY  (2024-11-05 .. 2025-11-25): an `initialize` request, its result, and a
          `notifications/initialized` notification establish a stateful session;
          version and capabilities are negotiated ONCE, per connection.
  MODERN  (2026-07-28): no handshake. Every request carries its protocol version
          and client capabilities in `_meta`; `server/discover` is optional.

This lab implements a legacy server, a modern server and a dual-era server, plus
legacy, modern and dual-era clients, and measures:
  1. legacy version negotiation and its counter-offer rule,
  2. what goes wrong when capabilities live on a CONNECTION that is shared,
  3. per-request validation: -32602, -32022 UnsupportedProtocolVersion,
     -32021 MissingRequiredClientCapability,
  4. a version-selection bug: picking max() of version strings,
  5. the full 3x3 era compatibility matrix, and a fallback rule keyed to one
     error code versus the rule the spec actually requires.

Deterministic (seeded). No API key, no network, no third-party dependencies.
Run:  python labs/m9/l05_initialization_capability_negotiation.py
"""

from __future__ import annotations

import random
import sys

sys.stdout.reconfigure(encoding="utf-8")


def rule(title: str) -> None:
    print(f"\n{'=' * 76}\n{title}\n{'=' * 76}")


MODERN = "2026-07-28"
PV, CAPS, INFO = ("io.modelcontextprotocol/protocolVersion",
                  "io.modelcontextprotocol/clientCapabilities",
                  "io.modelcontextprotocol/clientInfo")
MODERN_ERROR_CODES = {-32020, -32021, -32022}
TIMEOUT = "TIMEOUT"


def err(rid, code, message, data=None):
    e = {"code": code, "message": message}
    if data is not None:
        e["data"] = data
    return {"jsonrpc": "2.0", "id": rid, "error": e}


def ok(rid, result):
    return {"jsonrpc": "2.0", "id": rid, "result": result}


TOOLS = [{"name": "delete_report", "description": "Delete a report after asking the user to confirm.",
          "inputSchema": {"type": "object", "properties": {"report_id": {"type": "string"}},
                          "required": ["report_id"]}}]


# ------------------------------------------------------------------ servers
class LegacyServer:
    """[REAL] A handshake-era server. State lives on the connection object.
    `pre_init` controls how it treats requests that arrive before initialize:
    'method_not_found', 'invalid_params', 'silent', or 'lenient'."""

    def __init__(self, supported=("2025-06-18", "2025-11-25"), pre_init="method_not_found"):
        self.supported, self.pre_init = list(supported), pre_init
        self.version = None
        self.client_caps = None
        self.ready = False

    def handle(self, msg):
        method, rid = msg.get("method"), msg.get("id")
        if method == "initialize":
            requested = msg["params"]["protocolVersion"]
            self.version = requested if requested in self.supported else self.supported[-1]
            self.client_caps = msg["params"]["capabilities"]
            return ok(rid, {"protocolVersion": self.version,
                            "capabilities": {"tools": {"listChanged": False}},
                            "serverInfo": {"name": "legacy-reports", "version": "1.4.0"}})
        if method == "notifications/initialized":
            self.ready = True
            return None
        if not self.ready and self.pre_init != "lenient":
            if self.pre_init == "silent":
                return TIMEOUT
            code = -32601 if self.pre_init == "method_not_found" else -32602
            return err(rid, code, "Server not initialized")
        if method == "tools/list":
            return ok(rid, {"tools": TOOLS})
        return err(rid, -32601, f"Method not found: {method}")


class ModernServer:
    """[REAL] A 2026-07-28 server. It keeps NO per-connection state: every
    decision is taken from the request's own _meta."""

    def __init__(self, supported=(MODERN,)):
        self.supported = list(supported)

    def handle(self, msg):
        method, rid = msg.get("method"), msg.get("id")
        if method == "initialize":
            return err(rid, -32601, f"initialize is not supported; this server speaks {self.supported}")
        meta = (msg.get("params") or {}).get("_meta") or {}
        if PV not in meta or CAPS not in meta:
            missing = [k for k in (PV, CAPS) if k not in meta]
            return err(rid, -32602, f"Invalid params: missing {missing}")
        if meta[PV] not in self.supported:
            return err(rid, -32022, "Unsupported protocol version",
                       {"supported": self.supported, "requested": meta[PV]})
        caps = meta[CAPS]
        if method == "server/discover":
            return ok(rid, {"resultType": "complete", "supportedVersions": self.supported,
                            "capabilities": {"tools": {}},
                            "_meta": {"io.modelcontextprotocol/serverInfo": {"name": "modern-reports", "version": "2.0.0"}},
                            "ttlMs": 3_600_000, "cacheScope": "public"})
        if method == "tools/list":
            return ok(rid, {"resultType": "complete", "tools": TOOLS, "ttlMs": 60_000, "cacheScope": "public"})
        if method == "tools/call":
            if "elicitation" not in caps:
                return err(rid, -32021, "Missing required client capability",
                           {"requiredCapabilities": {"elicitation": {}}})
            return ok(rid, {"resultType": "input_required",
                            "inputRequests": {"confirm": {"method": "elicitation/create",
                                                          "params": {"mode": "form", "message": "Delete report?"}}}})
        return err(rid, -32601, f"Method not found: {method}")


class DualEraServer:
    """[REAL] Serves legacy clients that open with initialize and modern clients
    that send per-request _meta, choosing per message."""

    def __init__(self):
        self.legacy = LegacyServer(supported=("2025-06-18", "2025-11-25"))
        self.modern = ModernServer(supported=(MODERN, "2025-11-25"))

    def handle(self, msg):
        meta = (msg.get("params") or {}).get("_meta") or {}
        if msg.get("method") in ("initialize", "notifications/initialized") or (PV not in meta and self.legacy.version):
            return self.legacy.handle(msg)
        return self.modern.handle(msg)


# ------------------------------------------------------------------ helpers
_next = iter(range(1, 10_000))


def modern_request(method, version=MODERN, caps=None, params=None):
    p = dict(params or {})
    p["_meta"] = {PV: version, CAPS: caps if caps is not None else {},
                  INFO: {"name": "lab-client", "version": "0.1.0"}}
    return {"jsonrpc": "2.0", "id": next(_next), "method": method, "params": p}


def legacy_initialize(version="2025-11-25", caps=None):
    return {"jsonrpc": "2.0", "id": next(_next), "method": "initialize",
            "params": {"protocolVersion": version, "capabilities": caps or {},
                       "clientInfo": {"name": "lab-client", "version": "0.1.0"}}}


# ============================================================ 1
rule("1. LEGACY: THE INITIALIZE HANDSHAKE AND ITS COUNTER-OFFER RULE")

for offered, client_supports in [("2025-11-25", {"2025-11-25"}),
                                 ("2025-06-18", {"2025-06-18", "2025-11-25"}),
                                 ("2024-11-05", {"2024-11-05"})]:
    server = LegacyServer()
    reply = server.handle(legacy_initialize(offered))
    got = reply["result"]["protocolVersion"]
    verdict = "proceed" if got in client_supports else "client MUST disconnect"
    print(f"  client offers {offered} -> server answers {got}  => {verdict}")

server = LegacyServer()
early = server.handle({"jsonrpc": "2.0", "id": 99, "method": "tools/list"})
print(f"\n  tools/list sent BEFORE initialize -> {early['error']}")
server.handle(legacy_initialize())
before_ack = server.handle({"jsonrpc": "2.0", "id": 100, "method": "tools/list"})
server.handle({"jsonrpc": "2.0", "method": "notifications/initialized"})
after_ack = server.handle({"jsonrpc": "2.0", "id": 101, "method": "tools/list"})
print(f"  tools/list after initialize, before initialized -> {before_ack.get('error')}")
print(f"  tools/list after notifications/initialized       -> {len(after_ack['result']['tools'])} tool(s)")
print("\n  Three messages, in order, before any real work -- and every fact they")
print("  establish (version, capabilities) is stored on THIS connection.")


# ============================================================ 2
rule("2. WHY STATE ON A CONNECTION BREAKS: A POOLED CONNECTION")

rng = random.Random(505)
pooled = LegacyServer()
pooled.handle(legacy_initialize(caps={"elicitation": {}}))  # client A opened the pool
pooled.handle({"jsonrpc": "2.0", "method": "notifications/initialized"})
senders = [("A", {"elicitation": {}}) if rng.random() < 0.6 else ("B", {}) for _ in range(100)]

wrong_legacy = sum(1 for who, caps in senders if ("elicitation" in pooled.client_caps) != ("elicitation" in caps))
modern = ModernServer()
wrong_modern = 0
for who, caps in senders:
    reply = modern.handle(modern_request("tools/call", caps=caps,
                                         params={"name": "delete_report", "arguments": {"report_id": "r1"}}))
    asked_to_elicit = reply.get("result", {}).get("resultType") == "input_required"
    wrong_modern += asked_to_elicit != ("elicitation" in caps)
b_count = sum(1 for who, _ in senders if who == "B")
print("  A gateway shares ONE server connection between client A (supports")
print("  elicitation) and client B (does not). A initialized the connection.")
print(f"  100 requests: {100 - b_count} from A, {b_count} from B.")
print(f"    connection-scoped capabilities: {wrong_legacy:>2}/100 requests judged with the WRONG capability set")
print(f"    per-request capabilities      : {wrong_modern:>2}/100")
print("\n  Every one of B's requests inherited A's capabilities. 2026-07-28 removed")
print("  the handshake for exactly this reason: an open connection is not a")
print("  session, and a server MUST NOT infer capabilities from prior requests.")


# ============================================================ 3
rule("3. MODERN: EVERY REQUEST IS VALIDATED ON ITS OWN")

server = ModernServer()
cases = [
    ("no _meta at all", {"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}),
    ("unknown version", modern_request("tools/list", version="1900-01-01")),
    ("valid tools/list", modern_request("tools/list")),
    ("call, no elicitation", modern_request("tools/call", params={"name": "delete_report", "arguments": {"report_id": "r1"}})),
    ("call, with elicitation", modern_request("tools/call", caps={"elicitation": {"form": {}}},
                                              params={"name": "delete_report", "arguments": {"report_id": "r1"}})),
]
for label, req in cases:
    reply = server.handle(req)
    if "error" in reply:
        e = reply["error"]
        detail = f"data={e['data']}" if "data" in e else e["message"]
        print(f"  {label:<24} -> error {e['code']}: {detail}")
    else:
        r = reply["result"]
        shown = r["resultType"] + (f", {len(r['tools'])} tool(s)" if "tools" in r else f", asks: {list(r['inputRequests'])}")
        print(f"  {label:<24} -> result: {shown}")


# ============================================================ 4
rule("4. VERSION SELECTION: max() OF VERSION STRINGS IS A BUG")

client_known = ["2025-06-18", "2025-11-25", MODERN]
server_lists = [
    ["2025-11-25", MODERN],
    ["2025-11-25", MODERN, "DRAFT-2026-v2"],
    [MODERN, "next"],
]
for advertised in server_lists:
    naive = max(advertised)
    mutual = [v for v in client_known if v in advertised]
    safe = mutual[-1] if mutual else None
    flag = "" if naive in client_known else "   <- naive pick is a version the client cannot speak"
    print(f"  server supports {advertised}")
    print(f"    naive max(): {naive!r:<18} intersection-then-newest-known: {safe!r}{flag}")
print("\n  Versions are an enumerated set, not an ordered scalar: 'DRAFT...' and")
print("  'next' sort above every date. Pick from the INTERSECTION with the")
print("  versions the client actually implements, ordered by the client's list.")


# ============================================================ 5
rule("5. THE 3x3 ERA COMPATIBILITY MATRIX, RUN FOR REAL")


def legacy_client(server):
    reply = server.handle(legacy_initialize())
    if reply in (None, TIMEOUT) or "error" in reply:
        return "FAILS (initialize rejected)"
    server.handle({"jsonrpc": "2.0", "method": "notifications/initialized"})
    tools = server.handle({"jsonrpc": "2.0", "id": next(_next), "method": "tools/list"})
    return f"works (legacy {reply['result']['protocolVersion']}, {len(tools['result']['tools'])} tool)"


def probe(server):
    reply = server.handle(modern_request("server/discover"))
    if reply == TIMEOUT or reply is None:
        return "legacy", None
    if "result" in reply:
        return "modern", reply["result"]["supportedVersions"]
    if reply["error"]["code"] in MODERN_ERROR_CODES:
        return "modern", reply["error"].get("data", {}).get("supported")
    return "legacy", None


def modern_client(server):
    era, _ = probe(server)
    if era != "modern":
        return "FAILS (probe says legacy server)"
    tools = server.handle(modern_request("tools/list"))
    return f"works (modern {MODERN}, {len(tools['result']['tools'])} tool)"


def dual_client(server):
    era, _ = probe(server)
    if era == "modern":
        return modern_client(server)
    return legacy_client(server)


servers = {"legacy server": LegacyServer, "modern server": ModernServer, "dual-era server": DualEraServer}
clients = {"legacy client": legacy_client, "modern client": modern_client, "dual-era client": dual_client}
for cname, cfn in clients.items():
    for sname, sfactory in servers.items():
        print(f"  {cname:<16} x {sname:<16} -> {cfn(sfactory())}")


# ------------------------------------------------------------------ 5b
print("\n  Fallback rule check against three kinds of legacy server:")


def dual_keyed_on_code(server):
    reply = server.handle(modern_request("server/discover"))
    if isinstance(reply, dict) and reply.get("error", {}).get("code") == -32601:
        return legacy_client(server)
    if isinstance(reply, dict) and "result" in reply:
        return "modern"
    return "FAILS"


results = {"keyed on -32601 only": [], "spec rule (anything not modern)": []}
for pre in ("method_not_found", "invalid_params", "silent"):
    results["keyed on -32601 only"].append(dual_keyed_on_code(LegacyServer(pre_init=pre)).startswith("works"))
    results["spec rule (anything not modern)"].append(dual_client(LegacyServer(pre_init=pre)).startswith("works"))
for name, oks in results.items():
    print(f"    {name:<34}: connected to {sum(oks)}/3 legacy servers  {oks}")


# ============================================================ 6
rule("6. WHAT THIS LAB IS AND IS NOT")
print("  REAL: every negotiation outcome, error code and matrix cell above is the")
print("  result of running these server and client implementations against each")
print("  other. Section 2's 100 requests use a seeded random mix.")
print("\n  ILLUSTRATIVE: servers and clients run in one process with no transport;")
print("  a 'silent' legacy server is modelled as an immediate TIMEOUT value rather")
print("  than a real wait.")
print("\n  NOT SHOWN: HTTP-specific era detection (inspecting a 400 body, M9-L08),")
print("  extension negotiation beyond the empty 'extensions' map, and the full")
print("  elicitation round trip that section 3's input_required result begins (M9-L06).")
print("\nDone.")
