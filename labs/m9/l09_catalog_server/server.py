"""A complete, dependency-free MCP server over stdio -- the M9-L09 build.

Domain: a small course catalog (the seed of Project 9).
  tools      search_courses, plan_study_time          (read-only)
  resources  catalog://courses, catalog://courses/{course_id}
  prompts    study_plan

Dual-era, as taught in M9-L05:
  * modern 2026-07-28 requests carry _meta and are served statelessly;
  * a legacy client that opens with `initialize` is served under 2025-11-25.

Every rule below maps to a lesson: framing and stderr logging (M9-L08), message
shapes and error codes (M9-L04), per-request _meta and discover (M9-L05),
pagination and caching hints (M9-L06), schemas and structuredContent (M9-L07).

Run by a client, not by hand:  python labs/m9/l09_catalog_server/server.py
"""

from __future__ import annotations

import json
import sys
from urllib.parse import unquote

SERVER_INFO = {"name": "course-catalog", "version": "0.9.0"}
MODERN_VERSIONS = ["2026-07-28"]
LEGACY_VERSIONS = ["2025-06-18", "2025-11-25"]
PV = "io.modelcontextprotocol/protocolVersion"
CAPS = "io.modelcontextprotocol/clientCapabilities"
CAPABILITIES = {"tools": {"listChanged": False}, "resources": {"listChanged": False, "subscribe": False},
                "prompts": {"listChanged": False}}
INSTRUCTIONS = "Read-only catalog of AI engineering courses. Use search_courses before planning."

COURSES = {
    "mcp-101": {"title": "Model Context Protocol Fundamentals", "level": "intermediate", "hours": 24},
    "rag-201": {"title": "Retrieval-Augmented Generation", "level": "advanced", "hours": 34},
    "py-100": {"title": "Python for AI Engineers", "level": "beginner", "hours": 34},
    "gov-150": {"title": "AI Governance and Security", "level": "intermediate", "hours": 24},
    "aws-110": {"title": "AWS Foundations", "level": "beginner", "hours": 28},
}

TOOLS = [
    {
        "name": "plan_study_time",
        "title": "Plan study time",
        "description": "Estimate how many weeks a set of courses takes at a given number of study hours per week.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "course_ids": {"type": "array", "items": {"type": "string"}, "minItems": 1,
                               "description": "Course ids from search_courses, e.g. 'mcp-101'."},
                "hours_per_week": {"type": "number", "minimum": 1, "maximum": 60},
            },
            "required": ["course_ids", "hours_per_week"],
            "additionalProperties": False,
        },
        "outputSchema": {
            "type": "object",
            "properties": {"total_hours": {"type": "number"}, "weeks": {"type": "integer"}},
            "required": ["total_hours", "weeks"],
        },
        "annotations": {"readOnlyHint": True, "openWorldHint": False},
    },
    {
        "name": "search_courses",
        "title": "Search courses",
        "description": "Find courses whose title contains the query, optionally filtered by level.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "minLength": 1},
                "level": {"type": "string", "enum": ["beginner", "intermediate", "advanced"]},
            },
            "required": ["query"],
            "additionalProperties": False,
        },
        "outputSchema": {
            "type": "object",
            "properties": {"results": {"type": "array", "items": {"type": "object", "properties": {
                "id": {"type": "string"}, "title": {"type": "string"}, "level": {"type": "string"},
                "hours": {"type": "number"}}, "required": ["id", "title", "level", "hours"]}}},
            "required": ["results"],
        },
        "annotations": {"readOnlyHint": True, "openWorldHint": False},
    },
]  # already in deterministic (name) order

PROMPTS = [{"name": "study_plan", "title": "Study plan",
            "description": "Draft a weekly study plan for one course.",
            "arguments": [{"name": "course_id", "description": "A course id", "required": True},
                          {"name": "hours_per_week", "description": "Hours available each week", "required": False}]}]


def log(text: str) -> None:
    print(f"[course-catalog] {text}", file=sys.stderr, flush=True)


def send(message: dict) -> None:
    sys.stdout.write(json.dumps(message, separators=(",", ":")) + "\n")
    sys.stdout.flush()


class RpcError(Exception):
    def __init__(self, code: int, message: str, data=None):
        super().__init__(message)
        self.code, self.message, self.data = code, message, data


# ----------------------------------------------------------------- validation
def argument_problems(schema: dict, args: dict) -> list[str]:
    """Just enough of JSON Schema for these two tools (see M9-L07 for more)."""
    problems = []
    props = schema["properties"]
    for name in schema.get("required", []):
        if name not in args:
            problems.append(f"missing required argument '{name}'")
    for name, value in args.items():
        spec = props.get(name)
        if spec is None:
            problems.append(f"unexpected argument '{name}'")
            continue
        t = spec["type"]
        ok = {"string": isinstance(value, str), "array": isinstance(value, list),
              "number": isinstance(value, (int, float)) and not isinstance(value, bool)}[t]
        if not ok:
            problems.append(f"'{name}' must be a {t}")
            continue
        if "enum" in spec and value not in spec["enum"]:
            problems.append(f"'{name}' must be one of {spec['enum']}")
        if "minimum" in spec and value < spec["minimum"] or "maximum" in spec and value > spec["maximum"]:
            problems.append(f"'{name}' must be between {spec.get('minimum')} and {spec.get('maximum')}")
        if "minLength" in spec and len(value) < spec["minLength"]:
            problems.append(f"'{name}' must not be empty")
        if "minItems" in spec and len(value) < spec["minItems"]:
            problems.append(f"'{name}' needs at least {spec['minItems']} item(s)")
    return problems


def tool_result(structured: dict, text: str) -> dict:
    return {"resultType": "complete", "isError": False, "structuredContent": structured,
            "content": [{"type": "text", "text": text}]}


def tool_error(text: str) -> dict:
    return {"resultType": "complete", "isError": True, "content": [{"type": "text", "text": text}]}


# ----------------------------------------------------------------- handlers
def handle_tools_call(params: dict) -> dict:
    name, args = params.get("name"), params.get("arguments") or {}
    tool = next((t for t in TOOLS if t["name"] == name), None)
    if tool is None:
        raise RpcError(-32602, f"Unknown tool: {name}")
    problems = argument_problems(tool["inputSchema"], args)
    if problems:  # input validation failures are tool EXECUTION errors, so the model can self-correct
        return tool_error("Invalid arguments: " + "; ".join(problems))
    if name == "search_courses":
        q, level = args["query"].lower(), args.get("level")
        results = [{"id": cid, **c} for cid, c in sorted(COURSES.items())
                   if q in c["title"].lower() and (level is None or c["level"] == level)]
        text = f"{len(results)} course(s): " + ", ".join(f"{r['id']} ({r['title']})" for r in results)
        return tool_result({"results": results}, text)
    unknown = [cid for cid in args["course_ids"] if cid not in COURSES]
    if unknown:
        return tool_error(f"Unknown course id(s): {unknown}. Call search_courses to find valid ids.")
    total = sum(COURSES[cid]["hours"] for cid in args["course_ids"])
    weeks = -(-total // args["hours_per_week"])  # ceiling division
    return tool_result({"total_hours": total, "weeks": int(weeks)},
                       f"{total} hours at {args['hours_per_week']} h/week is {int(weeks)} week(s).")


def handle_resources_read(params: dict) -> dict:
    uri = params.get("uri", "")
    if uri == "catalog://courses":
        body = [{"id": cid, "title": c["title"]} for cid, c in sorted(COURSES.items())]
    elif uri.startswith("catalog://courses/") and unquote(uri.rsplit("/", 1)[1]) in COURSES:
        cid = unquote(uri.rsplit("/", 1)[1])
        body = {"id": cid, **COURSES[cid]}
    else:
        raise RpcError(-32602, f"Resource not found: {uri}")
    return {"resultType": "complete", "ttlMs": 300_000, "cacheScope": "public",
            "contents": [{"uri": uri, "mimeType": "application/json", "text": json.dumps(body)}]}


def handle_prompts_get(params: dict) -> dict:
    args = params.get("arguments") or {}
    if params.get("name") != "study_plan":
        raise RpcError(-32602, f"Unknown prompt: {params.get('name')}")
    if "course_id" not in args:
        raise RpcError(-32602, "Missing required prompt argument 'course_id'")
    course = COURSES.get(args["course_id"])
    if course is None:
        raise RpcError(-32602, f"Unknown course id: {args['course_id']}")
    hours = args.get("hours_per_week", "5")
    text = (f"Create a week-by-week study plan for '{course['title']}' ({course['hours']} hours, "
            f"{course['level']} level) for a learner with {hours} hours per week. "
            f"Include a checkpoint at the end of each week.")
    return {"resultType": "complete", "description": "Weekly study plan",
            "messages": [{"role": "user", "content": {"type": "text", "text": text}}]}


def listing(key: str, items: list) -> dict:
    return {"resultType": "complete", key: items, "ttlMs": 300_000, "cacheScope": "public"}


METHODS = {
    "server/discover": lambda p: {"resultType": "complete", "supportedVersions": MODERN_VERSIONS,
                                  "capabilities": CAPABILITIES, "instructions": INSTRUCTIONS,
                                  "ttlMs": 3_600_000, "cacheScope": "public"},
    "tools/list": lambda p: listing("tools", TOOLS),
    "tools/call": handle_tools_call,
    "resources/list": lambda p: listing("resources", [
        {"uri": "catalog://courses", "name": "courses", "title": "All courses", "mimeType": "application/json"}]),
    "resources/templates/list": lambda p: listing("resourceTemplates", [
        {"uriTemplate": "catalog://courses/{course_id}", "name": "course", "title": "One course",
         "mimeType": "application/json"}]),
    "resources/read": handle_resources_read,
    "prompts/list": lambda p: listing("prompts", PROMPTS),
    "prompts/get": handle_prompts_get,
}


# ----------------------------------------------------------------- dispatch
legacy_session = {"version": None}


def dispatch(msg: dict):
    method, params = msg.get("method"), msg.get("params") or {}
    if method == "initialize":
        requested = params.get("protocolVersion")
        version = requested if requested in LEGACY_VERSIONS else LEGACY_VERSIONS[-1]
        legacy_session["version"] = version
        log(f"legacy initialize: client asked {requested}, using {version}")
        return {"protocolVersion": version, "capabilities": CAPABILITIES,
                "serverInfo": SERVER_INFO, "instructions": INSTRUCTIONS}
    meta = params.get("_meta") or {}
    modern = PV in meta
    if not modern and legacy_session["version"] is None:
        raise RpcError(-32602, "Missing _meta protocol fields; this server speaks "
                               f"{MODERN_VERSIONS + LEGACY_VERSIONS}")
    if modern:
        if CAPS not in meta:
            raise RpcError(-32602, f"Invalid params: missing {CAPS}")
        if meta[PV] not in MODERN_VERSIONS:
            raise RpcError(-32022, "Unsupported protocol version",
                           {"supported": MODERN_VERSIONS, "requested": meta[PV]})
    if method not in METHODS:
        raise RpcError(-32601, f"Method not found: {method}")
    result = METHODS[method](params)
    if modern:
        result.setdefault("_meta", {})["io.modelcontextprotocol/serverInfo"] = SERVER_INFO
    else:  # legacy results have no resultType or caching hints
        for key in ("resultType", "ttlMs", "cacheScope"):
            result.pop(key, None)
    return result


def main() -> None:
    log("ready on stdio")
    for line in sys.stdin:
        if not line.strip():
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            send({"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "Parse error"}})
            continue
        if not isinstance(msg, dict) or msg.get("jsonrpc") != "2.0":
            send({"jsonrpc": "2.0", "id": None, "error": {"code": -32600, "message": "Invalid Request"}})
            continue
        if "id" not in msg:
            log(f"notification {msg.get('method')}")
            continue
        if "method" not in msg:  # a response from the client; this server never sends requests
            continue
        try:
            send({"jsonrpc": "2.0", "id": msg["id"], "result": dispatch(msg)})
        except RpcError as exc:
            error = {"code": exc.code, "message": exc.message}
            if exc.data is not None:
                error["data"] = exc.data
            send({"jsonrpc": "2.0", "id": msg["id"], "error": error})
        except Exception as exc:  # never let one bad request kill the process
            log(f"internal error on {msg.get('method')}: {exc!r}")
            send({"jsonrpc": "2.0", "id": msg["id"], "error": {"code": -32603, "message": "Internal error"}})
    log("stdin closed, exiting")


if __name__ == "__main__":
    main()
