"""M9-L16, deployment half -- builds the catalog server into a container and runs
the same conformance checks against it over `docker run -i`, with no network and a
read-only filesystem.

Requires Docker. If Docker is unavailable the script says so and exits 0, so the
rest of the module still runs.
Run:  python labs/m9/l16_container_check.py
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
CONTEXT = os.path.join(HERE, "l09_catalog_server")
IMAGE = "mcp-catalog:lab"
MODERN = "2026-07-28"
META = {"io.modelcontextprotocol/protocolVersion": MODERN,
        "io.modelcontextprotocol/clientCapabilities": {}}


def rule(title: str) -> None:
    print(f"\n{'=' * 76}\n{title}\n{'=' * 76}")


rule("A STDIO MCP SERVER IN A CONTAINER")

if shutil.which("docker") is None:
    print("  docker not found on PATH -- skipping (the rest of M9-L16 does not need it)")
    raise SystemExit(0)

build = subprocess.run(["docker", "build", "-q", "-t", IMAGE, CONTEXT], capture_output=True, text=True, timeout=600)
if build.returncode != 0:
    print("  docker build failed:", build.stderr.strip().splitlines()[-1:])
    raise SystemExit(0)
print(f"  built {IMAGE} from {os.path.relpath(CONTEXT, os.path.dirname(HERE))}/Dockerfile")

# The host's server command becomes `docker run -i ...`; stdin/stdout are the transport.
command = ["docker", "run", "-i", "--rm", "--network", "none", "--read-only",
           "--cap-drop", "ALL", "--memory", "256m", IMAGE]
requests = [
    {"jsonrpc": "2.0", "id": 1, "method": "server/discover", "params": {"_meta": META}},
    {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {"_meta": META}},
    {"jsonrpc": "2.0", "id": 3, "method": "tools/call",
     "params": {"name": "search_courses", "arguments": {"query": "python"}, "_meta": META}},
]
stdin = "\n".join(json.dumps(r, separators=(",", ":")) for r in requests) + "\n"
run = subprocess.run(command, input=stdin, capture_output=True, text=True, timeout=120)

lines = [line for line in run.stdout.splitlines() if line.strip()]
replies = [json.loads(line) for line in lines]
checks = [
    ("container answered every request", len(replies) == len(requests), f"{len(replies)}/{len(requests)}"),
    ("stdout carried only JSON-RPC", all(line.startswith("{") for line in lines), f"{len(lines)} line(s)"),
    ("ids echoed in order", [r.get("id") for r in replies] == [1, 2, 3], str([r.get("id") for r in replies])),
    ("discover advertises the modern version", MODERN in replies[0]["result"]["supportedVersions"], ""),
    ("tools listed", len(replies[1]["result"]["tools"]) == 2, f"{len(replies[1]['result']['tools'])} tools"),
    ("tool call returned structured content", "structuredContent" in replies[2]["result"], ""),
    ("server logs reached stderr, not stdout", "course-catalog" in run.stderr, f"{len(run.stderr.splitlines())} line(s)"),
    ("exited cleanly when stdin closed", run.returncode == 0, f"exit {run.returncode}"),
]
for name, ok, detail in checks:
    print(f"  [{'PASS' if ok else 'FAIL'}] {name:<44} {detail}")
print(f"\n  {sum(ok for _, ok, _ in checks)}/{len(checks)} checks passed with --network none, --read-only,")
print("  --cap-drop ALL and a 256 MB limit, running as a non-root user.")
subprocess.run(["docker", "image", "rm", "-f", IMAGE], capture_output=True)
print("  image removed.")
print("\n  A container gives a local server a filesystem and network boundary the host")
print("  can state explicitly. It does not authorise anything: the credentials you pass")
print("  in still decide what the server may reach (M9-L12).")
print("\nDone.")
