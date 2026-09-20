"""M9-L14 lab -- what happens when calls fail, hang, or are abandoned. Runs a real
subprocess server (labs/m9/l14_slow_server.py) and measures:

  1. cancellation on stdio: work units a cooperative server stops doing, versus a
     server that ignores notifications/cancelled,
  2. the late response a cancelled request produces, and why clients must ignore it,
  3. timeouts: a fixed deadline, a deadline reset by progress notifications, and
     the maximum cap that saves the latter from hanging forever,
  4. protocol errors vs tool execution errors, and how many tasks a scripted model
     recovers from each,
  5. per-request opt-ins: progress notifications and log messages are only sent
     when the request asks for them.

Timings are printed in coarse buckets so the output is repeatable.
No API key, no network, no third-party dependencies.
Run:  python labs/m9/l14_errors_timeouts_cancellation.py
"""

from __future__ import annotations

import json
import os
import queue
import subprocess
import sys
import threading
import time

sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
SERVER = os.path.join(HERE, "l14_slow_server.py")


def rule(title: str) -> None:
    print(f"\n{'=' * 76}\n{title}\n{'=' * 76}")


def bucket(seconds: float) -> str:
    for edge in (0.5, 1.0, 1.5, 2.0, 3.0):
        if seconds < edge:
            return f"under {edge:g}s"
    return "over 3s"


class SlowServer:
    def __init__(self, mode: str):
        self.proc = subprocess.Popen([sys.executable, SERVER, mode], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE, text=True, bufsize=1)
        self.messages: queue.Queue[dict] = queue.Queue()
        self.stderr: list[str] = []
        threading.Thread(target=self._read_stdout, daemon=True).start()
        threading.Thread(target=lambda: [self.stderr.append(l.rstrip()) for l in self.proc.stderr], daemon=True).start()

    def _read_stdout(self):
        for line in self.proc.stdout:
            self.messages.put(json.loads(line))

    def send(self, message: dict):
        self.proc.stdin.write(json.dumps(message, separators=(",", ":")) + "\n")
        self.proc.stdin.flush()

    def call(self, rid, units, progress_token=None, log_level=None):
        meta = {"io.modelcontextprotocol/protocolVersion": "2026-07-28",
                "io.modelcontextprotocol/clientCapabilities": {}}
        if progress_token is not None:
            meta["progressToken"] = progress_token
        if log_level is not None:
            meta["io.modelcontextprotocol/logLevel"] = log_level
        self.send({"jsonrpc": "2.0", "id": rid, "method": "tools/call",
                   "params": {"name": "build_report", "arguments": {"units": units}, "_meta": meta}})

    def cancel(self, rid, reason="user cancelled"):
        self.send({"jsonrpc": "2.0", "method": "notifications/cancelled",
                   "params": {"requestId": rid, "reason": reason}})

    def next_message(self, timeout=2.0):
        try:
            return self.messages.get(timeout=timeout)
        except queue.Empty:
            return None

    def summary(self) -> dict:
        self.proc.stdin.close()
        self.proc.wait(timeout=5)
        time.sleep(0.1)
        for line in reversed(self.stderr):
            if line.startswith("{"):
                return json.loads(line)
        return {}


# ============================================================ 1
rule("1. CANCELLING AN IN-FLIGHT REQUEST OVER STDIO")

results = {}
for mode in ("cooperative", "stubborn"):
    srv = SlowServer(mode)
    srv.call(rid=1, units=40, progress_token="p1")
    seen_progress = 0
    while seen_progress < 3:                       # let it get going, then cancel
        msg = srv.next_message()
        seen_progress += msg is not None and msg.get("method") == "notifications/progress"
    srv.cancel(1)
    late = None
    deadline = time.monotonic() + 2.0
    while time.monotonic() < deadline:             # collect anything that arrives after the cancel
        msg = srv.next_message(timeout=0.3)
        if msg is None:
            continue
        if "id" in msg and msg["id"] == 1:
            late = msg
    summary = srv.summary()
    results[mode] = (summary, late)
    print(f"  {mode:<12}: requested 40 units, cancelled after 3 progress notifications ->")
    print(f"      work units actually done: {summary.get('work_units_done')}")
    print(f"      response after cancellation: {'none' if late is None else late['result']['content'][0]['text']}")
saved = results['stubborn'][0]['work_units_done'] - results['cooperative'][0]['work_units_done']
print(f"\n  The cooperative server stopped {saved} units of work early; the stubborn one")
print("  finished them all and then sent a response for a request the client had")
print("  already abandoned. Clients MUST ignore such late responses (M9-L04: the id")
print("  is no longer in the pending table).")


# ============================================================ 2
rule("2. TIMEOUTS: FIXED, PROGRESS-RESET, AND PROGRESS-RESET WITH A CAP")


def wait_with_timeout(srv, rid, deadline_s, reset_on_progress, max_total_s=None):
    start = time.monotonic()
    deadline = start + deadline_s
    while True:
        now = time.monotonic()
        if max_total_s is not None and now - start >= max_total_s:
            return "cancelled at the maximum cap", now - start
        if now >= deadline:
            return "cancelled at the deadline", now - start
        msg = srv.next_message(timeout=0.05)
        if msg is None:
            continue
        if msg.get("method") == "notifications/progress" and reset_on_progress:
            deadline = time.monotonic() + deadline_s
        elif "id" in msg and msg["id"] == rid:
            return "completed", time.monotonic() - start


strategies = [("fixed 0.5s deadline", 0.5, False, None),
              ("reset on every progress notification", 0.5, True, 4.0),
              ("reset on progress, capped at 1.5s", 0.5, True, 1.5)]
for label, deadline_s, reset, cap in strategies:
    srv = SlowServer("progress_forever")
    srv.call(rid=7, units=3, progress_token="p7")
    outcome, elapsed = wait_with_timeout(srv, 7, deadline_s, reset, cap)
    srv.cancel(7)
    srv.summary()
    note = "  <- the 4s figure is this lab's harness giving up, not a client timeout" if cap == 4.0 else ""
    print(f"  {label:<38}: {outcome:<28} after {bucket(elapsed)}{note}")
print("\n  A server that keeps reporting progress keeps a progress-resetting client")
print("  waiting indefinitely. The spec allows resetting on progress but says")
print("  implementations SHOULD always enforce a maximum timeout as well.")


# ============================================================ 3
rule("3. PROTOCOL ERRORS VS TOOL EXECUTION ERRORS: CAN A MODEL RECOVER?")


def server_reply(kind: str, units):
    """Two ways of rejecting units=0 (the tool needs at least 1)."""
    if isinstance(units, int) and units >= 1:
        return {"result": {"isError": False, "content": [{"type": "text", "text": f"built from {units} units"}]}}
    if kind == "protocol":
        return {"error": {"code": -32602, "message": "Invalid params"}}
    return {"result": {"isError": True, "content": [{"type": "text",
            "text": "units must be an integer of at least 1 (you sent 0). Try units=1."}]}}


def scripted_model(first_args, kind):
    """A stand-in model: it can only self-correct from a message that says what to change."""
    reply = server_reply(kind, first_args)
    if "result" in reply and not reply["result"]["isError"]:
        return True, 1
    if "error" in reply:
        return False, 1                                   # nothing actionable to read
    text = reply["result"]["content"][0]["text"]
    if "Try units=" in text:
        fixed = int(text.split("Try units=")[1].split(".")[0])
        return "isError" in str(server_reply(kind, fixed)) and not server_reply(kind, fixed)["result"]["isError"], 2
    return False, 1


for kind in ("protocol", "execution"):
    outcomes = [scripted_model(0, kind) for _ in range(10)]
    solved = sum(ok for ok, _ in outcomes)
    calls = sum(n for _, n in outcomes)
    print(f"  {kind + ' error':<18}: {solved}/10 tasks completed, {calls} tool calls used")
print("\n  Both rejections are correct; only one tells the model what to change. The")
print("  spec routes input-validation failures to the execution channel for exactly")
print("  this reason, and protocol errors to JSON-RPC errors.")


# ============================================================ 4
rule("4. PROGRESS AND LOG MESSAGES ARE PER-REQUEST OPT-INS")

for label, token, level in (("no progressToken, no logLevel", None, None),
                            ("progressToken only", "p9", None),
                            ("progressToken + logLevel=info", "p9", "info")):
    srv = SlowServer("cooperative")
    srv.call(rid=9, units=3, progress_token=token, log_level=level)
    progress = logs = 0
    while True:
        msg = srv.next_message(timeout=1.0)
        if msg is None or ("id" in msg and msg["id"] == 9):
            break
        progress += msg.get("method") == "notifications/progress"
        logs += msg.get("method") == "notifications/message"
    srv.summary()
    print(f"  {label:<32}: {progress} progress notification(s), {logs} log notification(s)")
print("\n  In 2026-07-28 a server MUST NOT send notifications/message for a request that")
print("  did not include io.modelcontextprotocol/logLevel (logging/setLevel is gone, and")
print("  the logging feature itself is deprecated in favour of stderr and OpenTelemetry).")


# ============================================================ 5
rule("5. WHAT THE SERVER'S STDERR SHOWS A DEBUGGER")

srv = SlowServer("cooperative")
srv.call(rid=11, units=5, progress_token="p11")
srv.next_message()
srv.cancel(11, reason="user pressed stop")
time.sleep(0.4)
srv.summary()
for line in srv.stderr[:4]:
    print(f"  stderr: {line}")
print("\n  Request ids and cancellation reasons on stderr are what turn 'the tool")
print("  hung' into a timeline. Add the trace context from _meta (traceparent) to")
print("  correlate these lines with the host's own traces.")


rule("6. WHAT THIS LAB IS AND IS NOT")
print("  REAL: a real subprocess doing timed work, real notifications/cancelled")
print("  messages, real progress notifications, and the work-unit counts the server")
print("  itself reported on stderr.")
print("\n  ILLUSTRATIVE: a 'work unit' is a 20 ms sleep; section 3's model is a script")
print("  that can only recover when told exactly what to change; timings are bucketed.")
print("\n  NOT SHOWN: cancellation over Streamable HTTP (closing the SSE stream is the")
print("  signal, M9-L08), retries and idempotency (M8-L12, M8-L13), and tracing")
print("  backends (M12-L13).")
print("\nDone.")
