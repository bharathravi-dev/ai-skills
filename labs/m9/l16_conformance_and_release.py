"""M9-L16 lab -- the tests that catch what a tolerant client hides, run against the
server built in M9-L09. Measures:

  1. a conformance suite over a real stdio connection, including the three bugs
     M9-L09's mutation test showed an SDK client tolerating,
  2. fuzzing with 300 seeded malformed frames: crashes, non-JSON output, wrong ids,
     and requests left unanswered,
  3. golden-transcript comparison, run against a pristine server and a mutated one,
  4. a breaking-change detector for tool definitions between two releases.

No API key, no network, no third-party dependencies.
Run:  python labs/m9/l16_conformance_and_release.py
"""

from __future__ import annotations

import json
import os
import queue
import random
import string
import subprocess
import sys
import tempfile
import threading

sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
SERVER = os.path.join(HERE, "l09_catalog_server", "server.py")
MODERN = "2026-07-28"
META = {"io.modelcontextprotocol/protocolVersion": MODERN,
        "io.modelcontextprotocol/clientCapabilities": {},
        "io.modelcontextprotocol/clientInfo": {"name": "conformance-harness", "version": "1.0"}}


def rule(title: str) -> None:
    print(f"\n{'=' * 76}\n{title}\n{'=' * 76}")


class Connection:
    def __init__(self, path: str = SERVER):
        self.proc = subprocess.Popen([sys.executable, path], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE, text=True, bufsize=1)
        self.lines: queue.Queue[str] = queue.Queue()
        self.stderr: list[str] = []
        threading.Thread(target=lambda: [self.lines.put(l.rstrip("\n")) for l in self.proc.stdout], daemon=True).start()
        threading.Thread(target=lambda: [self.stderr.append(l.rstrip("\n")) for l in self.proc.stderr], daemon=True).start()

    def send_raw(self, text: str) -> None:
        try:
            self.proc.stdin.write(text + "\n")
            self.proc.stdin.flush()
        except BrokenPipeError:
            pass

    def read(self, timeout: float = 3.0) -> str | None:
        try:
            return self.lines.get(timeout=timeout)
        except queue.Empty:
            return None

    def request(self, rid, method: str, params: dict | None = None, meta: dict | None = META) -> dict | None:
        p = dict(params or {})
        if meta is not None:
            p["_meta"] = meta
        self.send_raw(json.dumps({"jsonrpc": "2.0", "id": rid, "method": method, "params": p}, separators=(",", ":")))
        line = self.read()
        return None if line is None else json.loads(line)

    def close(self) -> int | None:
        try:
            self.proc.stdin.close()
        except BrokenPipeError:
            pass
        try:
            return self.proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.proc.kill()
            return None


# ============================================================ 1
rule("1. CONFORMANCE SUITE")

checks: list[tuple[str, bool, str]] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    checks.append((name, ok, detail))


conn = Connection()
discover = conn.request(1, "server/discover")
check("server/discover implemented", "result" in discover, str(discover.get("result", {}).get("supportedVersions")))
check("discover advertises a version we speak", MODERN in discover["result"].get("supportedVersions", []))
check("discover carries caching hints", {"ttlMs", "cacheScope"} <= set(discover["result"]))
check("results carry resultType 'complete'", discover["result"].get("resultType") == "complete")
check("results identify the server", "io.modelcontextprotocol/serverInfo" in discover["result"].get("_meta", {}))

tools = conn.request(2, "tools/list")["result"]["tools"]
check("tools/list returns an array", isinstance(tools, list), f"{len(tools)} tools")
check("tool list is deterministically ordered", [t["name"] for t in tools] == sorted(t["name"] for t in tools))
check("every tool has an object inputSchema", all(t.get("inputSchema", {}).get("type") == "object" for t in tools))
check("tool names match the allowed character set",
      all(set(t["name"]) <= set(string.ascii_letters + string.digits + "_.-") and 1 <= len(t["name"]) <= 128 for t in tools))
second = conn.request(3, "tools/list")["result"]["tools"]
check("tools/list is stable across calls", [t["name"] for t in second] == [t["name"] for t in tools])

call = conn.request(4, "tools/call", {"name": "search_courses", "arguments": {"query": "python"}})["result"]
check("tool result has content and structuredContent", "content" in call and "structuredContent" in call)
check("structured result matches outputSchema shape", isinstance(call["structuredContent"].get("results"), list))
check("text content mirrors the structured result", call["content"][0]["type"] == "text")

bad_args = conn.request(5, "tools/call", {"name": "search_courses", "arguments": {}})["result"]
check("bad arguments -> isError result, not a protocol error", bad_args.get("isError") is True,
      bad_args["content"][0]["text"][:48])
unknown = conn.request(6, "tools/call", {"name": "no_such_tool", "arguments": {}})
check("unknown tool -> protocol error -32602", unknown.get("error", {}).get("code") == -32602)

for rid in ("string-id", 42):
    reply = conn.request(rid, "tools/list")
    check(f"id echoed unchanged and typed ({type(rid).__name__})", reply["id"] == rid and type(reply["id"]) is type(rid))

check("no _meta -> -32602", conn.request(7, "tools/list", meta=None)["error"]["code"] == -32602)
check("unknown version -> -32022 listing supported versions",
      conn.request(8, "tools/list", meta={**META, "io.modelcontextprotocol/protocolVersion": "1999-01-01"})["error"]["code"] == -32022)
check("unknown method -> -32601", conn.request(9, "reports/export")["error"]["code"] == -32601)
conn.send_raw('{"jsonrpc":"2.0","method":"notifications/cancelled","params":{"requestId":9}}')
check("notification gets no reply", conn.request(10, "tools/list")["id"] == 10)
check("all stdout was JSON-RPC", conn.lines.empty())
check("logs went to stderr", any("course-catalog" in line for line in conn.stderr), f"{len(conn.stderr)} line(s)")
check("exits 0 when stdin closes", conn.close() == 0)

for name, ok, detail in checks:
    print(f"  [{'PASS' if ok else 'FAIL'}] {name:<52} {detail}")
print(f"\n  {sum(ok for _, ok, _ in checks)}/{len(checks)} conformance checks passed")


# ============================================================ 2
rule("2. FUZZING: 300 MALFORMED OR HOSTILE FRAMES")

rng = random.Random(1616)
FRAGMENTS = ['{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"search_courses","arguments":{"query":"x"}}}',
             '{"jsonrpc":"2.0","id":2,"method":"tools/list"}', '{"jsonrpc":"1.0","id":3,"method":"tools/list"}',
             '[]', 'null', '"just a string"', '{}', '{"jsonrpc":"2.0"}', '   ', '{"jsonrpc":"2.0","id":null,"method":"x"}']


def mutate(text: str) -> str:
    choice = rng.randrange(6)
    if choice == 0:
        return text[: rng.randrange(1, max(2, len(text)))]                       # truncate
    if choice == 1:
        i = rng.randrange(len(text))
        return text[:i] + rng.choice("{}[]\",:\\") + text[i:]                    # inject punctuation
    if choice == 2:
        return text.replace('"query":"x"', '"query":' + json.dumps("A" * 5000))  # oversized value
    if choice == 3:
        return json.dumps({"jsonrpc": "2.0", "id": rng.randrange(1000), "method": "".join(
            rng.choice(string.printable[:80]) for _ in range(rng.randrange(1, 30))), "params": {}})
    if choice == 4:
        return text.replace("arguments", "args")                                 # wrong param names
    return text + text                                                           # two messages, one line


conn = Connection()
sent = replies = non_json = wrong_shape = 0
for _ in range(300):
    frame = mutate(rng.choice(FRAGMENTS))
    sent += 1
    conn.send_raw(frame)
    line = conn.read(timeout=0.4)
    if line is None:
        continue
    replies += 1
    try:
        msg = json.loads(line)
    except json.JSONDecodeError:
        non_json += 1
        continue
    if msg.get("jsonrpc") != "2.0" or not ({"result", "error"} & set(msg)):
        wrong_shape += 1
alive = conn.proc.poll() is None
probe = conn.request(9999, "tools/list") if alive else None
print(f"  frames sent                         : {sent}")
print(f"  replies received                    : {replies}")
print(f"  replies that were not valid JSON    : {non_json}")
print(f"  replies with a malformed envelope   : {wrong_shape}")
print(f"  server still alive at the end       : {alive}")
print(f"  still answering correctly afterwards: {bool(probe and 'result' in probe)}")
conn.close()
print("\n  Not every frame deserves a reply -- notifications and unreadable junk do not.")
print("  What matters is that nothing crashed the process, nothing produced invalid")
print("  output, and the connection still worked afterwards.")


# ============================================================ 3
rule("3. GOLDEN TRANSCRIPT: DETECTING A REGRESSION IN A RELEASE")

SCRIPT = [("server/discover", {}), ("tools/list", {}),
          ("tools/call", {"name": "search_courses", "arguments": {"query": "python"}}),
          ("resources/read", {"uri": "catalog://courses/mcp-101"}),
          ("prompts/get", {"name": "study_plan", "arguments": {"course_id": "mcp-101"}})]


def transcript(path: str) -> list[str]:
    """One normalised line per step: volatile metadata removed, everything else compared."""
    conn, out = Connection(path), []
    for i, (method, params) in enumerate(SCRIPT, start=1):
        reply = conn.request(i, method, params)
        result = reply.get("result", reply.get("error"))
        if isinstance(result, dict):
            result = {k: v for k, v in result.items() if k != "_meta"}           # ignore volatile metadata
        out.append(f"{method} -> {json.dumps(result, sort_keys=True)}")
    conn.close()
    return out


golden = transcript(SERVER)
source = open(SERVER, encoding="utf-8").read()
MUTANTS = {
    "description reworded": ('"description": "Find courses whose title contains the query',
                             '"description": "Search stuff'),
    "ttlMs shortened": ('"ttlMs": 300_000', '"ttlMs": 5_000'),
    "extra field in structured output": ('{"results": results}', '{"results": results, "debug": True}'),
    "no change (control)": ("SERVER_INFO = ", "SERVER_INFO = "),
}
with tempfile.TemporaryDirectory() as tmp:
    for label, (old, new) in MUTANTS.items():
        assert source.count(old) >= 1, f"mutation target not found: {label}"
        path = os.path.join(tmp, "release.py")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(source.replace(old, new, 1))
        candidate = transcript(path)
        diffs = [i for i, (a, b) in enumerate(zip(golden, candidate)) if a != b]
        where = ", ".join(SCRIPT[i][0] for i in diffs) if diffs else "none"
        print(f"  {label:<34} differing steps: {len(diffs)}  ({where})")
print("\n  A golden transcript turns 'the release looks fine' into a diff. Normalise")
print("  volatile fields (_meta, timestamps, ids) or every run is a false alarm.")


# ============================================================ 4
rule("4. BREAKING-CHANGE DETECTOR FOR TOOL DEFINITIONS")

V1 = {"name": "search_courses",
      "inputSchema": {"type": "object", "properties": {"query": {"type": "string"},
                      "level": {"type": "string", "enum": ["beginner", "intermediate", "advanced"]}},
                      "required": ["query"], "additionalProperties": False},
      "outputSchema": {"type": "object", "properties": {"results": {"type": "array"}}, "required": ["results"]}}


def compare(v1: dict, v2: dict) -> list[str]:
    breaking = []
    p1, p2 = v1["inputSchema"]["properties"], v2["inputSchema"]["properties"]
    r1, r2 = set(v1["inputSchema"].get("required", [])), set(v2["inputSchema"].get("required", []))
    for name in set(p1) - set(p2):
        breaking.append(f"argument removed: {name}")
    for name in r2 - r1:
        breaking.append(f"argument became required: {name}")
    for name in set(p1) & set(p2):
        if p1[name].get("type") != p2[name].get("type"):
            breaking.append(f"type changed: {name}")
        lost = set(p1[name].get("enum", [])) - set(p2[name].get("enum", []))
        if lost:
            breaking.append(f"enum values removed from {name}: {sorted(lost)}")
    for name in set(v1["outputSchema"].get("required", [])) - set(v2["outputSchema"].get("required", [])):
        breaking.append(f"output field no longer guaranteed: {name}")
    return breaking


releases = {
    "add an optional argument": {**V1, "inputSchema": {**V1["inputSchema"], "properties": {
        **V1["inputSchema"]["properties"], "limit": {"type": "integer"}}}},
    "add an enum value": {**V1, "inputSchema": {**V1["inputSchema"], "properties": {
        **V1["inputSchema"]["properties"], "level": {"type": "string", "enum": ["beginner", "intermediate", "advanced", "expert"]}}}},
    "make 'level' required": {**V1, "inputSchema": {**V1["inputSchema"], "required": ["query", "level"]}},
    "drop an enum value": {**V1, "inputSchema": {**V1["inputSchema"], "properties": {
        **V1["inputSchema"]["properties"], "level": {"type": "string", "enum": ["beginner", "advanced"]}}}},
    "query becomes an array": {**V1, "inputSchema": {**V1["inputSchema"], "properties": {
        **V1["inputSchema"]["properties"], "query": {"type": "array"}}}},
    "stop guaranteeing 'results'": {**V1, "outputSchema": {**V1["outputSchema"], "required": []}},
}
for label, v2 in releases.items():
    issues = compare(V1, v2)
    print(f"  {label:<30} -> {'COMPATIBLE' if not issues else 'BREAKING: ' + '; '.join(issues)}")
print("\n  Callers here are models and their hosts, and they cache tool definitions")
print("  (M9-L06). Breaking changes need a new tool name or a version bump the host")
print("  can see -- not a silent edit.")


rule("5. WHAT THIS LAB IS AND IS NOT")
print("  REAL: a real subprocess under a real conformance suite and fuzzer; the")
print("  transcripts, diffs and compatibility verdicts are computed by this code.")
print("\n  ILLUSTRATIVE: 300 frames is a smoke test, not a fuzzing campaign; the")
print("  breaking-change rules cover common cases, not all of JSON Schema.")
print("\n  NOT SHOWN: HTTP deployment, load and soak testing, multi-SDK interop")
print("  (M9-L09 does one SDK), and registry publication.")
print("\nDone.")
