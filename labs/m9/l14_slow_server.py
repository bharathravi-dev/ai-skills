"""Helper for the M9-L14 lab: an MCP-style stdio server with a slow tool, in one
of three behaviours.

  cooperative       checks for cancellation between work units and stops
  stubborn          ignores notifications/cancelled and finishes the work
  progress_forever  emits progress notifications indefinitely and never finishes

It emits notifications/progress only when the request carries a progressToken,
and notifications/message only when the request carries
io.modelcontextprotocol/logLevel -- both per-request opt-ins in 2026-07-28.
When a run ends it prints a JSON summary line to stderr:
    {"work_units_done": N, "cancelled": bool}

Run by the lab, not directly:  python labs/m9/l14_slow_server.py cooperative
"""

from __future__ import annotations

import json
import queue
import sys
import threading
import time

MODE = sys.argv[1] if len(sys.argv) > 1 else "cooperative"
UNIT_SECONDS = 0.02
cancelled: set = set()
inbox: queue.Queue = queue.Queue()


def send(message: dict) -> None:
    sys.stdout.write(json.dumps(message, separators=(",", ":")) + "\n")
    sys.stdout.flush()


def log(text: str) -> None:
    print(text, file=sys.stderr, flush=True)


def reader() -> None:
    """Keeps reading while work is in progress -- that is what makes cancellation possible."""
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        msg = json.loads(line)
        if msg.get("method") == "notifications/cancelled":
            rid = msg["params"]["requestId"]
            cancelled.add(rid)
            log(f"received notifications/cancelled for id={rid}")
        elif "id" in msg:
            inbox.put(msg)
    inbox.put(None)


def run_tool(msg: dict) -> None:
    rid = msg["id"]
    params = msg.get("params") or {}
    meta = params.get("_meta") or {}
    token, level = meta.get("progressToken"), meta.get("io.modelcontextprotocol/logLevel")
    units = params["arguments"]["units"]
    done = 0
    while True:
        if MODE != "stubborn" and rid in cancelled:
            log(json.dumps({"work_units_done": done, "cancelled": True}))
            return                                  # MUST NOT send any further messages for it
        time.sleep(UNIT_SECONDS)
        done += 1
        if token is not None:
            send({"jsonrpc": "2.0", "method": "notifications/progress",
                  "params": {"progressToken": token, "progress": done,
                             "total": None if MODE == "progress_forever" else units}})
        if level is not None:
            send({"jsonrpc": "2.0", "method": "notifications/message",
                  "params": {"level": "info", "data": f"unit {done} of {units}"}})
        if MODE != "progress_forever" and done >= units:
            break                                   # progress_forever never leaves this loop
    log(json.dumps({"work_units_done": done, "cancelled": rid in cancelled}))
    send({"jsonrpc": "2.0", "id": rid, "result": {"resultType": "complete", "isError": False,
          "content": [{"type": "text", "text": f"report built from {done} units"}]}})


threading.Thread(target=reader, daemon=True).start()
log(f"slow server ready in '{MODE}' mode")
while True:
    request = inbox.get()
    if request is None:
        break
    if request.get("method") == "tools/call":
        run_tool(request)
    else:
        send({"jsonrpc": "2.0", "id": request["id"], "error": {"code": -32601, "message": "Method not found"}})
log("stdin closed, exiting")
