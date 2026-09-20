"""Helper for the M9-L08 lab: a minimal newline-delimited JSON-RPC server that
speaks over stdin/stdout, in one of four deliberately different behaviours.

  clean           correct: JSON-RPC on stdout, logs on stderr, exits on stdin EOF
  noisy           writes human-readable log lines to STDOUT (the classic bug)
  ignore_eof      correct messages, but keeps running after stdin closes
  ignore_sigterm  ignores stdin EOF *and* SIGTERM

Run by the lab, not directly:  python labs/m9/l08_stdio_server.py clean
"""

from __future__ import annotations

import json
import signal
import sys
import time

MODE = sys.argv[1] if len(sys.argv) > 1 else "clean"


def log(text: str) -> None:
    if MODE == "noisy":
        print(text, flush=True)                       # the bug: logs on stdout
    else:
        print(text, file=sys.stderr, flush=True)      # correct: logs on stderr


def send(message: dict) -> None:
    sys.stdout.write(json.dumps(message, separators=(",", ":")) + "\n")
    sys.stdout.flush()


if MODE == "ignore_sigterm":
    signal.signal(signal.SIGTERM, signal.SIG_IGN)

log("[server] starting up, loading report index")
for line in sys.stdin:
    line = line.strip()
    if not line:
        continue
    try:
        msg = json.loads(line)
    except json.JSONDecodeError:
        send({"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "Parse error"}})
        continue
    if "id" not in msg:
        log(f"[server] notification {msg.get('method')}")
        continue
    log(f"[server] handling {msg.get('method')} id={msg['id']}")
    if msg.get("method") == "tools/call":
        n = msg["params"]["arguments"]["n"]
        send({"jsonrpc": "2.0", "id": msg["id"], "result": {
            "resultType": "complete", "content": [{"type": "text", "text": str(n * n)}], "isError": False}})
    else:
        send({"jsonrpc": "2.0", "id": msg["id"], "error": {"code": -32601, "message": "Method not found"}})

log("[server] stdin closed")
if MODE in ("ignore_eof", "ignore_sigterm"):
    while True:
        time.sleep(0.05)
