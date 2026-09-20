"""M9-L09 interop check -- uses the OFFICIAL MCP Python SDK (mcp 2.2.0) to test
the dependency-free server in labs/m9/l09_catalog_server/server.py.

  1. SDK client -> our server, mode 'auto' (probe server/discover, 2026-07-28)
  2. SDK client -> our server, mode 'legacy' (initialize handshake)
  3. MUTATION TEST: plant one known bug at a time in a copy of the server and
     record whether the SDK client notices -- what does "the SDK accepted it"
     actually prove?
  4. SDK client -> the same server written with the SDK (sdk_server.py)

Requires:  pip install "mcp==2.2.0"
Run:       python labs/m9/l09_sdk_interop.py
No API key, no network. Takes about a minute (section 3 waits out timeouts).
"""

from __future__ import annotations

import asyncio
import importlib.metadata
import json
import os
import sys
import tempfile
import warnings

from mcp import Client
from mcp.client.stdio import StdioServerParameters

sys.stdout.reconfigure(encoding="utf-8")
warnings.simplefilter("ignore")
HERE = os.path.dirname(os.path.abspath(__file__))
SERVER = os.path.join(HERE, "l09_catalog_server", "server.py")
SDK_SERVER = os.path.join(HERE, "l09_catalog_server", "sdk_server.py")


def rule(title: str) -> None:
    print(f"\n{'=' * 76}\n{title}\n{'=' * 76}")


def launch(path: str) -> StdioServerParameters:
    # the SDK forwards the server's stderr; send it nowhere so the report stays readable
    return StdioServerParameters(command="/bin/sh", args=["-c", f'exec "{sys.executable}" "{path}" 2>/dev/null'])


async def full_exercise(path: str, mode: str) -> list[tuple[str, bool, str]]:
    checks: list[tuple[str, bool, str]] = []
    async with Client(launch(path), mode=mode) as client:
        info = client.server_info
        checks.append(("negotiated version / server identity", True,
                       f"{client.protocol_version} / {info.name if info else '-'}"))
        names = [t.name for t in (await client.list_tools()).tools]
        checks.append(("tools/list", sorted(names) == ["plan_study_time", "search_courses"], str(sorted(names))))
        found = await client.call_tool("search_courses", {"query": "a", "level": "beginner"})
        ids = [r["id"] for r in (found.structured_content or {}).get("results", [])]
        checks.append(("tools/call search_courses (structured)", ids == ["aws-110", "py-100"], str(ids)))
        plan = await client.call_tool("plan_study_time", {"course_ids": ["mcp-101", "gov-150"], "hours_per_week": 10})
        checks.append(("tools/call plan_study_time", (plan.structured_content or {}).get("weeks") == 5,
                       json.dumps(plan.structured_content)))
        bad = await client.call_tool("plan_study_time", {"course_ids": ["mcp-999"], "hours_per_week": 10})
        checks.append(("tool execution error -> isError", bad.is_error is True, bad.content[0].text[:58]))
        resources = await client.list_resources()
        templates = await client.list_resource_templates()
        checks.append(("resources/list + templates/list",
                       resources.resources[0].uri == "catalog://courses"
                       and templates.resource_templates[0].uri_template == "catalog://courses/{course_id}",
                       templates.resource_templates[0].uri_template))
        read = await client.read_resource("catalog://courses/rag-201")
        checks.append(("resources/read", json.loads(read.contents[0].text)["hours"] == 34, read.contents[0].text[:58]))
        got = await client.get_prompt("study_plan", {"course_id": "py-100", "hours_per_week": "6"})
        text = got.messages[0].content.text
        checks.append(("prompts/get", "6 hours per week" in text, text[:58] + "..."))
        try:
            unknown = await client.call_tool("drop_tables", {})
            checks.append(("unknown tool rejected", unknown.is_error is True,
                           f"as an isError RESULT: {unknown.content[0].text}"[:58]))
        except Exception as exc:
            checks.append(("unknown tool rejected", True, f"as a PROTOCOL error: {exc}"[:58]))
    return checks


def report(title: str, path: str, mode: str) -> None:
    rule(title)
    checks = asyncio.run(full_exercise(path, mode))
    for name, ok, detail in checks:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name:<40} {detail}")
    print(f"\n  {sum(ok for _, ok, _ in checks)}/{len(checks)} checks passed")


print(f"  official SDK version: mcp {importlib.metadata.version('mcp')}")
report("1. SDK CLIENT (mode='auto') -> OUR STDLIB SERVER", SERVER, "auto")
report("2. SDK CLIENT (mode='legacy') -> OUR STDLIB SERVER", SERVER, "legacy")


# ============================================================ 3
rule("3. MUTATION TEST: WHICH PLANTED BUGS DOES THE SDK CLIENT NOTICE?")

SOURCE = open(SERVER, encoding="utf-8").read()
MUTATIONS = [
    ("banner printed to stdout", 'log("ready on stdio")', 'print("course-catalog ready"); log("ready on stdio")'),
    ("responses pretty-printed", 'json.dumps(message, separators=(",", ":"))', 'json.dumps(message, indent=1)'),
    ("response id echoed as a string", '"id": msg["id"], "result": dispatch(msg)', '"id": str(msg["id"]), "result": dispatch(msg)'),
    ("tools/list returns an object, not an array", 'listing("tools", TOOLS)', 'listing("tools", {t["name"]: t for t in TOOLS})'),
    ("no cacheScope on list results", '"ttlMs": 300_000, "cacheScope": "public"}', '"ttlMs": 300_000}'),
    ("no resultType on any result", '= SERVER_INFO\n', '= SERVER_INFO\n        result.pop("resultType", None)\n'),
    ("structuredContent violates outputSchema", 'tool_result({"results": results}, text)', 'tool_result({"items": results}, text)'),
    ("isError missing on tool errors", '"isError": True, "content"', '"content"'),
    ("server/discover not implemented", '"server/discover": lambda p:', '"server/discovered": lambda p:'),
]


async def probe_mutant(path: str) -> str:
    async def run():
        async with Client(launch(path), mode="auto", read_timeout_seconds=4) as client:
            tools = await client.list_tools()
            found = await client.call_tool("search_courses", {"query": "a"})
            bad = await client.call_tool("plan_study_time", {"course_ids": ["x"], "hours_per_week": 5})
            sc = found.structured_content
            return (f"worked: {client.protocol_version}, {len(tools.tools)} tools, "
                    f"structured keys={sorted(sc) if isinstance(sc, dict) else sc}, bad call isError={bad.is_error}")
    try:
        return await asyncio.wait_for(run(), timeout=12)
    except asyncio.TimeoutError:
        return "HUNG (timed out)"
    except BaseException as exc:  # noqa: BLE001 -- record whatever the SDK raised
        inner = exc
        while isinstance(inner, BaseExceptionGroup) and inner.exceptions:
            inner = inner.exceptions[0]
        return f"ERROR {type(inner).__name__}: {str(inner).splitlines()[0][:110] if str(inner) else ''}"


with tempfile.TemporaryDirectory() as tmp:
    for label, old, new in MUTATIONS:
        assert SOURCE.count(old) >= 1, label
        path = os.path.join(tmp, "mutant.py")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(SOURCE.replace(old, new))
        outcome = asyncio.run(probe_mutant(path))
        print(f"  {label:<42}\n      -> {outcome}")

print("\n  Read each line as: did an independent client catch this bug? Anything")
print("  that 'worked' is a bug your own tests must catch, because a tolerant")
print("  client will not -- and a stricter client elsewhere may break on it.")


report("4. SDK CLIENT (mode='auto') -> THE SAME SERVER WRITTEN WITH THE SDK", SDK_SERVER, "auto")

rule("5. WHAT THIS CHECK IS AND IS NOT")
print("  REAL: the official SDK client launched each server as a subprocess over")
print("  stdio; every PASS, ERROR and 'worked' above is its actual behaviour.")
print("\n  NOT SHOWN: other SDKs (TypeScript, Java...) may be stricter or more")
print("  tolerant; Streamable HTTP; authorization. Passing one client's checks is")
print("  necessary for interoperability, not proof of conformance.")
print("\nDone.")
