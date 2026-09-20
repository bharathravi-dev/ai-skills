"""M9-L09 lab -- drives the dependency-free MCP server in
labs/m9/l09_catalog_server/server.py over a real stdio pipe and prints the wire
transcript, then runs a set of robustness checks against it.

  1. modern era: server/discover, then each method with per-request _meta,
  2. legacy era: initialize -> notifications/initialized -> tools/list,
  3. a tool execution error vs a protocol error,
  4. robustness: parse errors, invalid requests, missing _meta, unsupported
     versions, unknown methods, stdout cleanliness, exit on EOF.

The companion script labs/m9/l09_sdk_interop.py checks the same server with the
official `mcp` SDK client (requires `pip install mcp==2.2.0`).

No API key, no network, no third-party dependencies.
Run:  python labs/m9/l09_build_first_server.py
"""

from __future__ import annotations

import json
import os
import queue
import subprocess
import sys
import threading

sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
SERVER = os.path.join(HERE, "l09_catalog_server", "server.py")
META = {"io.modelcontextprotocol/protocolVersion": "2026-07-28",
        "io.modelcontextprotocol/clientCapabilities": {},
        "io.modelcontextprotocol/clientInfo": {"name": "lab-raw-client", "version": "0.1.0"}}


def rule(title: str) -> None:
    print(f"\n{'=' * 76}\n{title}\n{'=' * 76}")


class Server:
    def __init__(self):
        self.proc = subprocess.Popen([sys.executable, SERVER], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE, text=True, bufsize=1)
        self.lines: queue.Queue[str] = queue.Queue()
        self.stderr: list[str] = []
        self.next_id = 0
        threading.Thread(target=lambda: [self.lines.put(l.rstrip("\n")) for l in self.proc.stdout], daemon=True).start()
        threading.Thread(target=lambda: [self.stderr.append(l.rstrip("\n")) for l in self.proc.stderr], daemon=True).start()

    def raw(self, text: str) -> dict:
        self.proc.stdin.write(text + "\n")
        self.proc.stdin.flush()
        return json.loads(self.lines.get(timeout=5))

    def request(self, method: str, params: dict | None = None, meta: dict | None = META) -> dict:
        self.next_id += 1
        p = dict(params or {})
        if meta is not None:
            p["_meta"] = meta
        msg = {"jsonrpc": "2.0", "id": self.next_id, "method": method}
        if p:
            msg["params"] = p
        reply = self.raw(json.dumps(msg, separators=(",", ":")))
        assert reply.get("id") == self.next_id, reply
        return reply

    def notify(self, method: str) -> None:
        self.proc.stdin.write(json.dumps({"jsonrpc": "2.0", "method": method}) + "\n")
        self.proc.stdin.flush()

    def close(self) -> int | None:
        self.proc.stdin.close()
        try:
            return self.proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            self.proc.kill()
            return None


def short(obj, limit: int = 150) -> str:
    text = json.dumps(obj, separators=(",", ":"))
    return text if len(text) <= limit else text[:limit - 3] + "..."


# ============================================================ 1
rule("1. MODERN ERA (2026-07-28): EVERY METHOD, WITH PER-REQUEST _meta")

srv = Server()
steps = [
    ("server/discover", {}),
    ("tools/list", {}),
    ("tools/call", {"name": "search_courses", "arguments": {"query": "a", "level": "beginner"}}),
    ("tools/call", {"name": "plan_study_time", "arguments": {"course_ids": ["mcp-101", "gov-150"], "hours_per_week": 10}}),
    ("resources/list", {}),
    ("resources/templates/list", {}),
    ("resources/read", {"uri": "catalog://courses/rag-201"}),
    ("prompts/list", {}),
    ("prompts/get", {"name": "study_plan", "arguments": {"course_id": "py-100", "hours_per_week": "6"}}),
]
for method, params in steps:
    reply = srv.request(method, params)
    result = dict(reply["result"])
    result.pop("_meta", None)
    if method == "tools/list":
        result["tools"] = [f"{t['name']} (inputSchema, outputSchema, annotations)" for t in result["tools"]]
    print(f"  -> {method:<25} {short(params, 60) if params else ''}")
    print(f"  <- {short(result)}")
print(f"\n  every modern result carried _meta.serverInfo: "
      f"{srv.request('tools/list')['result']['_meta']['io.modelcontextprotocol/serverInfo']}")


# ============================================================ 2
rule("2. LEGACY ERA (2025-11-25): THE HANDSHAKE, THEN NO _meta")

legacy = Server()
init = legacy.request("initialize", {"protocolVersion": "2025-11-25", "capabilities": {},
                                     "clientInfo": {"name": "old-client", "version": "1.0"}}, meta=None)
legacy.notify("notifications/initialized")
tools = legacy.request("tools/list", meta=None)
print(f"  initialize        <- protocolVersion={init['result']['protocolVersion']}, "
      f"serverInfo={init['result']['serverInfo']}")
print(f"  tools/list        <- {len(tools['result']['tools'])} tools; keys in result: {sorted(tools['result'])}")
print("  (no resultType / ttlMs / cacheScope: those fields do not exist in 2025-11-25)")
legacy.close()


# ============================================================ 3
rule("3. TOOL EXECUTION ERRORS VS PROTOCOL ERRORS")

cases = [
    ("bad argument value", "tools/call", {"name": "plan_study_time", "arguments": {"course_ids": ["mcp-101"], "hours_per_week": 500}}),
    ("unknown course id", "tools/call", {"name": "plan_study_time", "arguments": {"course_ids": ["mcp-999"], "hours_per_week": 5}}),
    ("unknown tool", "tools/call", {"name": "drop_tables", "arguments": {}}),
    ("missing resource", "resources/read", {"uri": "catalog://courses/nope"}),
]
for label, method, params in cases:
    reply = srv.request(method, params)
    if "error" in reply:
        print(f"  {label:<20} -> PROTOCOL error {reply['error']['code']}: {reply['error']['message']}")
    else:
        print(f"  {label:<20} -> result isError={reply['result']['isError']}: {reply['result']['content'][0]['text']}")
print("\n  Bad arguments and unknown ids are returned as tool results with isError,")
print("  so a model can read the message and correct itself. An unknown tool or")
print("  resource is a protocol error: the request itself was wrong.")


# ============================================================ 4
rule("4. ROBUSTNESS CHECKS")

checks = []


def check(name: str, ok: bool, detail: str) -> None:
    checks.append(ok)
    print(f"  [{'PASS' if ok else 'FAIL'}] {name:<40} {detail}")


r = srv.raw('{"jsonrpc":"2.0","id":50,"method":"tools/li')
check("truncated JSON -> -32700, id null", r["error"]["code"] == -32700 and r["id"] is None, short(r["error"]))
r = srv.raw('[{"jsonrpc":"2.0","id":51,"method":"tools/list"}]')
check("batch array -> -32600", r["error"]["code"] == -32600, short(r["error"]))
r = srv.request("tools/list", meta=None)
check("no _meta on a fresh process -> -32602", r["error"]["code"] == -32602, r["error"]["message"][:64])
r = srv.request("tools/list", meta={**META, "io.modelcontextprotocol/protocolVersion": "2031-01-01"})
check("unknown version -> -32022 with supported", r["error"]["code"] == -32022, short(r["error"]["data"]))
r = srv.request("tools/list", meta={"io.modelcontextprotocol/protocolVersion": "2026-07-28"})
check("missing clientCapabilities -> -32602", r["error"]["code"] == -32602, r["error"]["message"][:64])
r = srv.request("reports/export")
check("unknown method -> -32601", r["error"]["code"] == -32601, r["error"]["message"])
r = srv.request("tools/call", {"name": "search_courses", "arguments": {"query": "x", "debug": True}})
check("undeclared argument -> isError result", r["result"]["isError"] is True, r["result"]["content"][0]["text"])
srv.notify("notifications/cancelled")
r = srv.request("tools/list")
check("notification produced no reply", r["id"] == srv.next_id, "next reply matched the next request id")
code = srv.close()
check("exits on stdin EOF", code == 0, f"exit code {code}")
check("stdout carried only JSON-RPC", srv.lines.empty(), "no stray lines; logs went to stderr")
print(f"\n  {sum(checks)}/{len(checks)} robustness checks passed")


# ============================================================ 5
rule("5. WHAT THIS LAB IS AND IS NOT")
print("  REAL: a real subprocess speaking newline-delimited JSON-RPC; every message")
print("  and verdict above is what the server actually returned.")
print("\n  ILLUSTRATIVE: the catalog data is five hard-coded courses, and argument")
print("  validation implements only the JSON Schema keywords these tools use.")
print("\n  NOT SHOWN: Streamable HTTP hosting, authorization (M9-L10..L13), progress")
print("  and cancellation (M9-L14), subscriptions, and packaging (M9-L16).")
print("\nDone.")
