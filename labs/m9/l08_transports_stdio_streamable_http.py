"""M9-L08 lab -- the two standard MCP transports, run for real on this machine.

stdio: the client launches labs/m9/l08_stdio_server.py as a subprocess and
exchanges newline-delimited JSON-RPC over its pipes. Measured:
  1. a clean round trip,
  2. a server that logs to STDOUT, and what that does to a client,
  3. a client that sends pretty-printed (multi-line) JSON,
  4. shutdown: close stdin, then SIGTERM, then SIGKILL -- how many steps each
     server variant needed.

Streamable HTTP (2026-07-28 shape): a real http.server bound to 127.0.0.1 on an
ephemeral port, called with urllib. Measured:
  5. JSON vs SSE responses, 202 for notifications, 405 for legacy GET,
  6. mirrored-header validation (-32020 HeaderMismatch) and why it exists,
  7. Origin validation (403) against DNS-rebinding-style requests,
  8. version and method errors mapped to HTTP status codes.

No API key, no internet access, no third-party dependencies. Uses only the
loopback interface. Timings are reported as coarse categories so output is
repeatable.
Run:  python labs/m9/l08_transports_stdio_streamable_http.py
"""

from __future__ import annotations

import json
import os
import queue
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
SERVER = os.path.join(HERE, "l08_stdio_server.py")
MODERN = "2026-07-28"


def rule(title: str) -> None:
    print(f"\n{'=' * 76}\n{title}\n{'=' * 76}")


class StdioConnection:
    """[REAL] Launches the server and reads its stdout/stderr on background threads."""

    def __init__(self, mode: str):
        self.proc = subprocess.Popen([sys.executable, SERVER, mode], stdin=subprocess.PIPE,
                                     stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)
        self.out: queue.Queue[str] = queue.Queue()
        self.err: list[str] = []
        threading.Thread(target=self._pump, args=(self.proc.stdout, self.out.put), daemon=True).start()
        threading.Thread(target=self._pump, args=(self.proc.stderr, self.err.append), daemon=True).start()

    @staticmethod
    def _pump(stream, sink):
        for line in stream:
            sink(line.rstrip("\n"))

    def write(self, text: str) -> None:
        self.proc.stdin.write(text)
        self.proc.stdin.flush()

    def read_line(self, timeout: float = 2.0) -> str | None:
        try:
            return self.out.get(timeout=timeout)
        except queue.Empty:
            return None


def call(n: int, rid: int) -> str:
    return json.dumps({"jsonrpc": "2.0", "id": rid, "method": "tools/call",
                       "params": {"name": "square", "arguments": {"n": n}}}, separators=(",", ":"))


# ============================================================ 1
rule("1. STDIO: A CLEAN ROUND TRIP OVER A REAL SUBPROCESS")

conn = StdioConnection("clean")
for i in range(1, 4):
    conn.write(call(i + 10, i) + "\n")
responses = [json.loads(conn.read_line()) for _ in range(3)]
conn.write(json.dumps({"jsonrpc": "2.0", "method": "notifications/cancelled", "params": {"requestId": 99}}) + "\n")
time.sleep(0.2)
print("  responses on stdout :", [(r["id"], r["result"]["content"][0]["text"]) for r in responses])
print(f"  extra stdout lines after a notification: {conn.out.qsize()}")
print(f"  stderr lines (logs) : {len(conn.err)} -> first: {conn.err[0]!r}")
conn.proc.stdin.close()
conn.proc.wait(timeout=5)


# ============================================================ 2
rule("2. STDIO: A SERVER THAT LOGS TO STDOUT")


def run_ten(mode: str):
    c = StdioConnection(mode)
    for i in range(1, 11):
        c.write(call(i, i) + "\n")
    time.sleep(0.5)
    lines = []
    while not c.out.empty():
        lines.append(c.out.get())
    c.proc.stdin.close()
    c.proc.wait(timeout=5)
    naive_ok = 0                        # "the k-th line is the k-th response"
    for k, line in enumerate(lines[:10], start=1):
        try:
            naive_ok += json.loads(line).get("id") == k
        except json.JSONDecodeError:
            pass
    unparseable = sum(1 for line in lines if not line.startswith("{"))
    return len(lines), unparseable, naive_ok


for mode in ("clean", "noisy"):
    total, junk, ok = run_ten(mode)
    print(f"  {mode:<6} server: {total:>2} stdout lines for 10 requests, {junk:>2} not JSON-RPC; "
          f"line-per-response client matched {ok:>2}/10")
print("\n  The noisy server's responses are all present, but every log line")
print("  shifts the stream. A strict client treats a non-JSON line as a fatal")
print("  framing error; a line-counting client mismatches everything after the")
print("  first log line. Only one rule prevents both: stdout carries MCP")
print("  messages and nothing else; logs go to stderr.")


# ============================================================ 3
rule("3. STDIO: PRETTY-PRINTED JSON BREAKS NEWLINE FRAMING")

for label, text in (("compact", call(7, 1)), ("indent=2", json.dumps(json.loads(call(7, 1)), indent=2))):
    c = StdioConnection("clean")
    c.write(text + "\n")
    time.sleep(0.3)
    replies = []
    while not c.out.empty():
        replies.append(json.loads(c.out.get()))
    c.proc.stdin.close()
    c.proc.wait(timeout=5)
    parse_errors = sum(1 for r in replies if r.get("error", {}).get("code") == -32700)
    results = sum(1 for r in replies if "result" in r)
    print(f"  {label:<9}: {text.count(chr(10)) + 1:>2} line(s) sent -> {results} result(s), {parse_errors} parse error(s)")
print(f"\n  json.dumps never emits a raw newline inside a string (it writes \\n),")
print(f"  so compact JSON is always exactly one line: {json.dumps('line1' + chr(10) + 'line2')}")


# ============================================================ 4
rule("4. STDIO SHUTDOWN: CLOSE STDIN, THEN SIGTERM, THEN SIGKILL")


def shutdown(mode: str, grace: float = 1.0) -> str:
    c = StdioConnection(mode)
    time.sleep(0.2)
    c.proc.stdin.close()
    try:
        c.proc.wait(timeout=grace)
        return f"exited after closing stdin (code {c.proc.returncode})"
    except subprocess.TimeoutExpired:
        pass
    c.proc.terminate()
    try:
        c.proc.wait(timeout=grace)
        return f"needed SIGTERM (code {c.proc.returncode})"
    except subprocess.TimeoutExpired:
        pass
    c.proc.kill()
    c.proc.wait(timeout=grace)
    return f"needed SIGKILL (code {c.proc.returncode})"


for mode in ("clean", "ignore_eof", "ignore_sigterm"):
    print(f"  {mode:<15} -> {shutdown(mode)}")
print("\n  Negative codes are the signal number that ended the process. Every")
print("  escalation step costs the client its grace period, and SIGKILL gives")
print("  the server no chance to flush or clean up.")


# ============================================================ 5-8
rule("5. STREAMABLE HTTP: ONE POST ENDPOINT, JSON OR SSE, 202, 405")

ALLOWED_ORIGINS: set[str] = set()


def rpc_error(code, message, rid=None, data=None):
    e = {"code": code, "message": message}
    if data:
        e["data"] = data
    return {"jsonrpc": "2.0", "id": rid, "error": e}


class MCPHandler(BaseHTTPRequestHandler):
    def log_message(self, *args):                    # keep the lab's output clean
        pass

    def _json(self, status, body):
        raw = json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        self.send_response(405)
        self.send_header("Allow", "POST")
        self.end_headers()

    do_DELETE = do_GET

    def do_POST(self):
        origin = self.headers.get("Origin")
        if origin is not None and origin not in ALLOWED_ORIGINS:
            return self._json(403, rpc_error(-32600, f"Forbidden origin {origin}"))
        accept = self.headers.get("Accept", "")
        if "application/json" not in accept or "text/event-stream" not in accept:
            return self._json(406, rpc_error(-32600, "Accept must list application/json and text/event-stream"))
        body = self.rfile.read(int(self.headers.get("Content-Length", 0)))
        try:
            msg = json.loads(body)
        except json.JSONDecodeError:
            return self._json(400, rpc_error(-32700, "Parse error"))
        if "id" not in msg:
            self.send_response(202)
            self.end_headers()
            return None
        rid, method, params = msg["id"], msg.get("method"), msg.get("params") or {}
        meta = params.get("_meta") or {}
        hv, hm, hn = (self.headers.get("MCP-Protocol-Version"), self.headers.get("Mcp-Method"),
                      self.headers.get("Mcp-Name"))
        body_name = params.get("name") or params.get("uri")
        if hv is None or hm is None or (method in ("tools/call", "resources/read", "prompts/get") and hn is None):
            return self._json(400, rpc_error(-32020, "Header mismatch: required MCP header missing", rid))
        if hv != meta.get("io.modelcontextprotocol/protocolVersion") or hm != method or (hn is not None and hn != body_name):
            return self._json(400, rpc_error(-32020, f"Header mismatch: headers ({hm}, {hn}) vs body ({method}, {body_name})", rid))
        if hv != MODERN:
            return self._json(400, rpc_error(-32022, "Unsupported protocol version", rid, {"supported": [MODERN], "requested": hv}))
        if method == "tools/list":
            return self._json(200, {"jsonrpc": "2.0", "id": rid, "result": {
                "resultType": "complete", "ttlMs": 60000, "cacheScope": "public",
                "tools": [{"name": "build_report", "inputSchema": {"type": "object"}}]}})
        if method == "tools/call" and body_name == "build_report":
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("X-Accel-Buffering", "no")
            self.end_headers()
            token = meta.get("progressToken")
            for step in (1, 2, 3):
                note = {"jsonrpc": "2.0", "method": "notifications/progress",
                        "params": {"progressToken": token, "progress": step, "total": 3}}
                self.wfile.write(f"data: {json.dumps(note)}\n\n".encode())
                self.wfile.flush()
            final = {"jsonrpc": "2.0", "id": rid, "result": {"resultType": "complete", "isError": False,
                     "content": [{"type": "text", "text": "report ready"}]}}
            self.wfile.write(f"data: {json.dumps(final)}\n\n".encode())
            self.wfile.flush()
            return None
        return self._json(404, rpc_error(-32601, f"Method not found: {method}", rid))


httpd = ThreadingHTTPServer(("127.0.0.1", 0), MCPHandler)
PORT = httpd.server_address[1]
ALLOWED_ORIGINS.update({f"http://127.0.0.1:{PORT}", f"http://localhost:{PORT}"})
threading.Thread(target=httpd.serve_forever, daemon=True).start()
URL = f"http://127.0.0.1:{PORT}/mcp"
print(f"  server bound to {httpd.server_address[0]} (loopback only) on an ephemeral port")


def post(body: dict | None, headers: dict | None = None, method: str = "POST"):
    data = json.dumps(body).encode() if body is not None else None
    h = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream"}
    h.update(headers or {})
    h = {k: v for k, v in h.items() if v is not None}
    req = urllib.request.Request(URL, data=data, headers=h, method=method)
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status, resp.headers.get("Content-Type"), resp.read().decode()
    except urllib.error.HTTPError as exc:
        return exc.code, exc.headers.get("Content-Type"), exc.read().decode()


def modern(method: str, params: dict | None = None, version: str = MODERN, extra_meta: dict | None = None) -> dict:
    p = dict(params or {})
    p["_meta"] = {"io.modelcontextprotocol/protocolVersion": version,
                  "io.modelcontextprotocol/clientCapabilities": {}, **(extra_meta or {})}
    return {"jsonrpc": "2.0", "id": 1, "method": method, "params": p}


def headers_for(req: dict) -> dict:
    p = req["params"]
    h = {"MCP-Protocol-Version": p["_meta"]["io.modelcontextprotocol/protocolVersion"], "Mcp-Method": req["method"]}
    if "name" in p:
        h["Mcp-Name"] = p["name"]
    return h


def summarize(status, ctype, text):
    if not text:
        return f"HTTP {status}, empty body"
    if ctype and ctype.startswith("text/event-stream"):
        events = [json.loads(line[6:]) for line in text.splitlines() if line.startswith("data: ")]
        kinds = [e.get("method", "response") for e in events]
        return f"HTTP {status}, SSE with {len(events)} events: {kinds}"
    body = json.loads(text)
    if "error" in body:
        return f"HTTP {status}, JSON-RPC error {body['error']['code']}"
    return f"HTTP {status}, JSON result with {len(body['result'].get('tools', []))} tool(s)"


req = modern("tools/list")
print(f"  tools/list                    -> {summarize(*post(req, headers_for(req)))}")
req = modern("tools/call", {"name": "build_report", "arguments": {}}, extra_meta={"progressToken": "p-1"})
print(f"  tools/call build_report       -> {summarize(*post(req, headers_for(req)))}")
note = {"jsonrpc": "2.0", "method": "notifications/example", "params": {}}
print(f"  a notification POST           -> {summarize(*post(note))}")
print(f"  legacy GET for a standing SSE -> HTTP {post(None, method='GET')[0]} (no GET stream in 2026-07-28)")
status, _, _ = post(req, {**headers_for(req), "Accept": "application/json"})
print(f"  Accept without event-stream   -> HTTP {status} (the lab server's choice for a non-conforming client)")


rule("6. MIRRORED HEADERS: WHY THE SERVER CHECKS THEM AGAINST THE BODY")

req = modern("tools/call", {"name": "delete_all_reports", "arguments": {}})
spoofed = {**headers_for(req), "Mcp-Name": "build_report"}
missing = {k: v for k, v in headers_for(req).items() if k != "Mcp-Name"}
for label, hdrs in (("header says build_report, body says delete_all_reports", spoofed),
                    ("Mcp-Name header missing", missing)):
    status, _, text = post(req, hdrs)
    print(f"  {label}\n    -> HTTP {status}, {json.loads(text)['error']['message']}")
print("\n  A gateway that authorizes on Mcp-Name ('build_report is allowed') while")
print("  the server executes the body ('delete_all_reports') is a split-brain")
print("  authorization bypass. The server MUST reject any mismatch with -32020.")


rule("7. ORIGIN VALIDATION: A BROWSER PAGE TALKING TO A LOCAL SERVER")

req = modern("tools/list")
for origin in (None, f"http://localhost:{PORT}", "https://evil.example", "http://localhost.evil.example"):
    status, _, _ = post(req, {**headers_for(req), "Origin": origin})
    label = "(no Origin header: non-browser client)" if origin is None else "Origin: " + origin.replace(str(PORT), "<port>")
    print(f"  {label:<42} -> HTTP {status}")
print("\n  Without this check, a web page on any site the user visits can script")
print("  requests to a server listening on the user's machine (via DNS rebinding")
print("  or plain localhost fetches). Servers MUST validate Origin and SHOULD bind")
print("  to 127.0.0.1 rather than 0.0.0.0 when running locally.")


rule("8. VERSION AND METHOD ERRORS AS HTTP STATUS CODES")

for label, request in (("unsupported version", modern("tools/list", version="2025-11-25")),
                       ("unknown method", modern("reports/export"))):
    status, _, text = post(request, headers_for(request))
    body = json.loads(text)
    print(f"  {label:<20} -> HTTP {status}, JSON-RPC {body['error']['code']}, data={body['error'].get('data')}")
print("\n  A 404 WITH a JSON-RPC -32601 body means 'modern server, unknown method';")
print("  a bare 404 or 400 with no recognized body is how a client detects a legacy")
print("  server and falls back (M9-L05).")
httpd.shutdown()


rule("9. WHAT THIS LAB IS AND IS NOT")
print("  REAL: real subprocesses, real pipes, real signals, and a real HTTP server")
print("  on the loopback interface; every count, status code and exit code above")
print("  was observed on this machine.")
print("\n  ILLUSTRATIVE: the HTTP server implements only the checks this lesson")
print("  covers; the 406 for a bad Accept header is this lab's choice; timings are")
print("  reported only as which shutdown step was needed.")
print("\n  NOT SHOWN: TLS, authorization headers (M9-L10, M9-L11), subscriptions/listen")
print("  streams, cancellation by closing an SSE stream (M9-L14), and the Base64")
print("  sentinel encoding for non-ASCII header values.")
print("\nDone.")
