# M9-L09 — Build Your First MCP Server (stdio, Python)

| | |
|---|---|
| **Lesson ID** | M9-L09 |
| **Difficulty** | 2 (Intermediate) |
| **Estimated study time** | 2.5 hours |
| **Prerequisites** | [M9-L07](M9-L07-input-output-schemas.md), [M9-L08](M9-L08-transports-stdio-streamable-http.md) |

---

## 1. Learning objectives

1. **Build** a complete stdio MCP server in plain Python — tools, resources, a resource template and a prompt —
   that serves both 2026-07-28 and legacy clients.
2. **Distinguish** in code between tool execution errors (`isError: true`) and protocol errors, and choose
   correctly for each failure.
3. **Verify** a server with an independent client: the official `mcp` Python SDK, in both protocol eras.
4. **Interpret** a mutation test: which planted server bugs an independent client detects, which it tolerates,
   and what that implies for your own test suite.
5. **Rebuild** the same server with the SDK's `MCPServer` and explain what the SDK does for you — and the
   behaviour differences you must know about.

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **Handler** | The function that serves one method, e.g. `handle_tools_call`. |
| **Dispatch** | Routing an incoming message to the right handler after protocol checks. |
| **Tool execution error** | A tool ran but could not do what was asked; returned as a normal result with `isError: true` so the model can adjust. |
| **Protocol error** | The request itself was invalid (unknown method, unknown tool, malformed params); returned as a JSON-RPC `error`. |
| **Interop test** | Checking your implementation against an independently written counterpart. |
| **Mutation test** | Deliberately introducing a known bug and checking whether a test (here: an independent client) notices. |
| **`MCPServer`** | The Python SDK's high-level server class (named `FastMCP` in `mcp` 1.x). |
| **`ToolError`** | The SDK exception for an *anticipated* tool failure whose message should reach the model. |

---

## 3. Plain-language explanation

### 3.1 Everything from the last five lessons, in one file

The server in this lesson is about 300 lines of standard-library Python. It frames messages as single lines and
logs to stderr (M9-L08), returns the right JSON-RPC shapes and error codes (M9-L04), reads the protocol version
and capabilities from each request's `_meta` and answers `server/discover` (M9-L05), attaches caching hints to
lists (M9-L06), and declares input and output schemas with conforming `structuredContent` (M9-L07). Its subject
is a small course catalog, which grows into Project 9.

### 3.2 Write it by hand once, then let a library do it

You would rarely ship a hand-written protocol server; the official SDK exists for that. Writing one once is how
you learn what the SDK is doing, which is what you need when something goes wrong between a host and a server
and the logs show raw JSON. At the end of the lesson you rebuild the same server with the SDK in about 70 lines.

### 3.3 "It works with my client" is weak evidence

A server tested only by the person who wrote it tends to agree with that person's misunderstandings. §7.4
connects the **official SDK client** to our server: all 9 checks passed in the modern era and all 9 in the legacy
era. Then it asks the harder question. It planted nine known bugs one at a time and measured how the SDK client
reacted: it **raised errors for five**, **hung on one**, and **silently worked with three** — including a server
with no `server/discover` at all, which the client handled by quietly falling back to the older protocol.
**Those three are bugs only your own tests will catch.**

---

## 4. Analogy

**Building a flat-pack wardrobe without the instructions, then comparing it with the showroom model.** Assembling
it from first principles teaches you what every bracket is for (the hand-written server). Standing it next to the
manufacturer's display model tells you whether it fits the same doors and shelves (the SDK interop test). Then a
careful inspector deliberately loosens one screw at a time and pulls on each door: some faults are obvious
immediately, one makes a drawer jam, and a few don't show at all until someone loads the wardrobe differently
(the mutation test).

### Where the analogy breaks

- **The showroom model is not the standard.** The SDK is one implementation. Where it tolerates something (a
  string id, a stdout banner), another client may reject it; where it rejects something (a missing `cacheScope`),
  it is enforcing the spec. You check against the spec, and use clients as evidence.
- **Wardrobes don't have two eras.** Our server must behave correctly for clients that open with `initialize` and
  for clients that never will — two sets of fittings on one frame.

---

## 5. Detailed technical explanation

### 5.1 Layout and capabilities

**Files:** [`labs/m9/l09_catalog_server/server.py`](../../labs/m9/l09_catalog_server/server.py) (stdlib server) ·
[`labs/m9/l09_catalog_server/sdk_server.py`](../../labs/m9/l09_catalog_server/sdk_server.py) (SDK version) ·
[`labs/m9/l09_build_first_server.py`](../../labs/m9/l09_build_first_server.py) (raw wire driver) ·
[`labs/m9/l09_sdk_interop.py`](../../labs/m9/l09_sdk_interop.py) (SDK interop and mutation test)

| Primitive | What the server offers | Why this primitive (M9-L03) |
|---|---|---|
| Tool | `search_courses(query, level?)` | Needs a query and a filter chosen at call time |
| Tool | `plan_study_time(course_ids, hours_per_week)` | A computation over chosen inputs |
| Resource | `catalog://courses` | A fixed list; no decision needed |
| Resource template | `catalog://courses/{course_id}` | One course by identifier |
| Prompt | `study_plan(course_id, hours_per_week?)` | User-chosen, server-maintained wording |

Both tools declare `readOnlyHint: true`. That is honest here, but remember that clients must treat annotations from
untrusted servers as unverified claims (M9-L15).

### 5.2 The main loop: framing, logging, and never dying on one request

```python
def main() -> None:
    log("ready on stdio")                                   # stderr, never stdout
    for line in sys.stdin:                                  # one message per line
        ...
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            send({"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "Parse error"}})
            continue
        if not isinstance(msg, dict) or msg.get("jsonrpc") != "2.0":
            send({... "code": -32600 ...}); continue         # includes batch arrays
        if "id" not in msg:                                  # notification: never reply
            continue
        try:
            send({"jsonrpc": "2.0", "id": msg["id"], "result": dispatch(msg)})
        except RpcError as exc:                              # deliberate protocol errors
            send({... "id": msg["id"], "error": {"code": exc.code, "message": exc.message, ...}})
        except Exception:                                    # bugs: log details, reveal nothing
            log(...); send({... "code": -32603, "message": "Internal error"})
    log("stdin closed, exiting")                             # exit on EOF
```

Three design decisions are worth copying. `send()` always uses compact `json.dumps`, so a message is always one
line. An unexpected exception is logged with detail to **stderr** but returned as a bare `-32603 Internal error`,
so a stack trace containing file paths or data never reaches a client. And the loop ends when stdin closes, so the
host's polite shutdown works (M9-L08).

### 5.3 Dispatch: two eras, one process

```python
def dispatch(msg):
    if method == "initialize":                          # legacy client
        legacy_session["version"] = negotiate(...)      # counter-offer rule (M9-L05)
        return {"protocolVersion": ..., "capabilities": ..., "serverInfo": ..., "instructions": ...}
    meta = params.get("_meta") or {}
    modern = PV in meta
    if not modern and legacy_session["version"] is None:
        raise RpcError(-32602, "Missing _meta protocol fields ...")
    if modern:
        require CAPS in meta                     -> else -32602
        require meta[PV] in MODERN_VERSIONS      -> else -32022 {"supported", "requested"}
    result = METHODS[method](params)             # unknown method -> -32601
    if modern:  result["_meta"]["io.modelcontextprotocol/serverInfo"] = SERVER_INFO
    else:       strip resultType / ttlMs / cacheScope (not part of 2025-11-25)
```

A request with modern `_meta` is served statelessly; an `initialize` switches that **stdio process** into legacy
semantics, which is exactly the dual-era behaviour the 2026-07-28 versioning page describes.

### 5.4 Handlers, and choosing the right kind of error

`[REAL, measured]` §7.1 exercised every method with per-request `_meta` and printed each result: lists carry
`ttlMs`/`cacheScope`, `tools/call` results carry `structuredContent` plus a `TextContent` copy, and every modern
result carries `_meta.serverInfo`.

`[REAL, measured]` §7.3 separated the two error channels:

| Failure | Channel | Returned |
|---|---|---|
| `hours_per_week: 500` (out of range) | Tool execution error | `isError: true`, "'hours_per_week' must be between 1 and 60" |
| `course_ids: ["mcp-999"]` | Tool execution error | `isError: true`, "Unknown course id(s)… Call search_courses to find valid ids." |
| Tool `drop_tables` | Protocol error | `-32602 Unknown tool: drop_tables` |
| Resource `catalog://courses/nope` | Protocol error | `-32602 Resource not found` |

The 2026-07-28 tools page puts **input validation failures, API failures and business-logic errors** on the
execution-error channel, because a model can read "must be between 1 and 60" and try again. It puts **unknown
tools, malformed requests and server errors** on the protocol channel. Write execution-error messages for a model
reader: say what was wrong and what to do next ("Call search_courses to find valid ids").

### 5.5 Robustness checks

`[REAL, measured]` §7.4 of the raw driver: **10/10** checks passed — truncated JSON → `-32700` with `id: null`;
a batch → `-32600`; no `_meta` on a fresh process → `-32602`; unknown version → `-32022` with `supported`; missing
`clientCapabilities` → `-32602`; unknown method → `-32601`; an undeclared argument → `isError`; a notification
produced no reply; the process exited with code 0 on stdin EOF; and stdout carried nothing but JSON-RPC.

### 5.6 Interop with the official SDK client

`[REAL, measured]` The companion script launched our server with `mcp` 2.2.0's `Client`:

| Mode | Negotiated | Checks passed |
|---|---|---|
| `mode="auto"` (probe `server/discover`) | 2026-07-28 | **9/9** |
| `mode="legacy"` (`initialize`) | 2025-11-25 | **9/9** |

The checks covered identity, `tools/list`, both tools including structured output, an `isError` result, resource
listing and templates, `resources/read`, `prompts/get`, and an unknown tool.

### 5.7 The mutation test: what an independent client does and does not catch

`[REAL, measured]` Nine single-bug copies of the server, each driven by the SDK client in `auto` mode with a
12-second watchdog:

| Planted bug | SDK client outcome | Interpretation |
|---|---|---|
| Banner printed to stdout | **worked** | The SDK skips unparseable lines; stricter clients reject the stream (M9-L08) |
| Responses pretty-printed | **hung** (watchdog fired) | No complete line ever parsed; framing broken |
| Response `id` echoed as `"1"` | **worked** | The SDK deliberately coerces numeric-string ids back to integers ("matches the TS SDK"); other clients may not |
| `tools` as an object, not an array | ERROR `ValidationError` | Caught |
| No `cacheScope` on lists | ERROR `ValidationError` | Caught — required in 2026-07-28 |
| No `resultType` | ERROR `ValidationError` | Caught — "absent means complete" is for *earlier-version* servers |
| `structuredContent` violates `outputSchema` | ERROR `RuntimeError` | Caught — the client validates structured output |
| `isError` omitted on tool errors | ERROR `RuntimeError` | Caught indirectly: a "successful" result had no `structuredContent` despite an `outputSchema` |
| No `server/discover` | **worked, at 2025-11-25** | The probe failed, so the client silently fell back to the legacy handshake |

The last row deserves attention. Nothing failed — the server simply got used in the **older protocol era**, without
per-request capabilities or caching hints, and nobody was told. A server that means to be modern needs a test that
asserts the negotiated version.

**The practical conclusion:** an independent client's acceptance is necessary, not sufficient. Your own test suite
must assert at least: stdout is clean, ids are echoed with their original type, `server/discover` succeeds, and the
negotiated version is the one you intend (M9-L16 builds that suite).

### 5.8 The same server with the SDK

```python
from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

server = MCPServer("course-catalog-sdk", version="0.9.0", instructions="...")

@server.tool(title="Search courses")
def search_courses(query: str, level: Literal["beginner", "intermediate", "advanced"] | None = None) -> SearchResult:
    """Find courses whose title contains the query, optionally filtered by level."""
    ...

@server.tool(title="Plan study time")
def plan_study_time(course_ids: list[str], hours_per_week: float) -> StudyPlan:
    if unknown:
        raise ToolError(f"Unknown course id(s): {unknown}. Call search_courses to find valid ids.")
    ...

@server.resource("catalog://courses/{course_id}", mime_type="application/json")
def one_course(course_id: str) -> str: ...

@server.prompt(title="Study plan")
def study_plan(course_id: str, hours_per_week: str = "5") -> str: ...

if __name__ == "__main__":
    server.run()          # stdio
```

`[REAL, measured]` The SDK client passed **9/9** checks against it. The SDK generated both schemas from the type
hints and Pydantic models, and handled framing, both eras, discovery and caching fields. Two behaviours differ from
our hand-written server and are worth knowing:

1. **Unknown tools come back as an `isError` result** (`Unknown tool: drop_tables`), not a JSON-RPC protocol error.
   The spec's tools page lists unknown tools under protocol errors; clients therefore need to handle both forms.
2. **Exception type decides what the model sees.** A `ToolError` passes its message to the model. **Any other
   exception is treated as a crash**, and the model sees only `Error executing tool <name>` — the SDK hides the text
   so that internal details do not leak. The first draft of `sdk_server.py` raised `ValueError`, and the model would
   have lost the actionable hint; it now raises `ToolError`.

`mcp` 2.x renamed `FastMCP` to `MCPServer`; importing `mcp.server.fastmcp` raises an error pointing at the migration
guide. Tutorials using `FastMCP` target `mcp` 1.x.

### 5.9 Connecting it to a host

Most MCP hosts launch stdio servers from a JSON configuration naming a command and arguments. The common shape is:

```json
{"mcpServers": {"course-catalog": {"command": "python",
                                   "args": ["/absolute/path/to/labs/m9/l09_catalog_server/server.py"]}}}
```

`[UNVERIFIED]` File names, locations and extra fields (environment variables, working directory) differ between hosts
and change between releases — check your host's current documentation. Use absolute paths, point `command` at the
virtual environment's interpreter if the server has dependencies, and remember that a host shows stderr in its MCP
log, which is where your `log()` lines will appear. For interactive debugging, the MCP Inspector
(`npx @modelcontextprotocol/inspector <command> <args>`) lets you call each method by hand `[UNVERIFIED]`.

### 5.10 Assumptions and limitations

- The hand-written validator supports only the schema keywords these tools use; the SDK uses Pydantic.
- The mutation results describe `mcp` 2.2.0's client. Other SDKs and hosts may be stricter or more lenient.
- No Streamable HTTP, authorization, cancellation, progress or subscriptions yet — M9-L10 to M9-L16.

---

## 6. Worked example — the internal server that "worked" for six months

**The situation.** A platform team wrote a stdio MCP server for their deployment system in early 2026 and tested it
with one desktop host, where it worked. In September 2026 a second team adopted it from a new agent built on a
different SDK, and every session failed at startup with "invalid response id".

**Investigation with this lesson's tools.**

1. The team ran the raw driver approach from §7.1 against the server and printed the wire transcript. Responses to
   `id: 1` came back as `"id": "1"`: the server read ids with a helper that returned strings.
2. The original host's SDK coerced numeric strings back to integers — exactly the tolerance measured in §5.7's third
   row — so the bug had never surfaced. The new client matched ids exactly, as its authors were entitled to.
3. A mutation-style review of the rest of the server found two more latent issues: a third-party library printed a
   deprecation warning to stdout on first import (tolerated by the original host, fatal to the new one), and the
   server did not implement `server/discover`, so the original host had silently used the legacy protocol all along
   (§5.7 last row) — which also meant nobody had noticed the server ignored per-request capabilities.

| # | Defect | Hidden by | Fix |
|---|---|---|---|
| 1 | Ids echoed as strings | Id coercion in one client | Echo the id value unchanged; test `type(reply["id"]) is type(request["id"])` |
| 2 | Library warning on stdout | Client skipping non-JSON lines | Route warnings/logging to stderr; test that every stdout line parses |
| 3 | No `server/discover` | Automatic legacy fallback | Implement discover; test the negotiated version is 2026-07-28 |

**The general rule.** **A client's tolerance is not your server's correctness.** Build the tests that a strict,
independent client would imply, and run them in CI.

---

## 7. Practical activity

**Files:** see §5.1. The raw driver needs only the standard library; the interop script needs `mcp==2.2.0`.

```bash
source .venv/bin/activate
python labs/m9/l09_build_first_server.py          # stdlib only
pip install "mcp==2.2.0"
python labs/m9/l09_sdk_interop.py                  # about 15 seconds
```

### 7.2 Expected output — the raw wire driver

`[EXECUTED]` — 2026-09-16, Python 3.12.3 (pure standard library). Run twice; output identical.

```text

============================================================================
1. MODERN ERA (2026-07-28): EVERY METHOD, WITH PER-REQUEST _meta
============================================================================
  -> server/discover           
  <- {"resultType":"complete","supportedVersions":["2026-07-28"],"capabilities":{"tools":{"listChanged":false},"resources":{"listChanged":false,"subscri...
  -> tools/list                
  <- {"resultType":"complete","tools":["plan_study_time (inputSchema, outputSchema, annotations)","search_courses (inputSchema, outputSchema, annotation...
  -> tools/call                {"name":"search_courses","arguments":{"query":"a","level"...
  <- {"resultType":"complete","isError":false,"structuredContent":{"results":[{"id":"aws-110","title":"AWS Foundations","level":"beginner","hours":28},{...
  -> tools/call                {"name":"plan_study_time","arguments":{"course_ids":["mcp...
  <- {"resultType":"complete","isError":false,"structuredContent":{"total_hours":48,"weeks":5},"content":[{"type":"text","text":"48 hours at 10 h/week i...
  -> resources/list            
  <- {"resultType":"complete","resources":[{"uri":"catalog://courses","name":"courses","title":"All courses","mimeType":"application/json"}],"ttlMs":300...
  -> resources/templates/list  
  <- {"resultType":"complete","resourceTemplates":[{"uriTemplate":"catalog://courses/{course_id}","name":"course","title":"One course","mimeType":"appli...
  -> resources/read            {"uri":"catalog://courses/rag-201"}
  <- {"resultType":"complete","ttlMs":300000,"cacheScope":"public","contents":[{"uri":"catalog://courses/rag-201","mimeType":"application/json","text":"...
  -> prompts/list              
  <- {"resultType":"complete","prompts":[{"name":"study_plan","title":"Study plan","description":"Draft a weekly study plan for one course.","arguments"...
  -> prompts/get               {"name":"study_plan","arguments":{"course_id":"py-100","h...
  <- {"resultType":"complete","description":"Weekly study plan","messages":[{"role":"user","content":{"type":"text","text":"Create a week-by-week study ...

  every modern result carried _meta.serverInfo: {'name': 'course-catalog', 'version': '0.9.0'}

============================================================================
2. LEGACY ERA (2025-11-25): THE HANDSHAKE, THEN NO _meta
============================================================================
  initialize        <- protocolVersion=2025-11-25, serverInfo={'name': 'course-catalog', 'version': '0.9.0'}
  tools/list        <- 2 tools; keys in result: ['tools']
  (no resultType / ttlMs / cacheScope: those fields do not exist in 2025-11-25)

============================================================================
3. TOOL EXECUTION ERRORS VS PROTOCOL ERRORS
============================================================================
  bad argument value   -> result isError=True: Invalid arguments: 'hours_per_week' must be between 1 and 60
  unknown course id    -> result isError=True: Unknown course id(s): ['mcp-999']. Call search_courses to find valid ids.
  unknown tool         -> PROTOCOL error -32602: Unknown tool: drop_tables
  missing resource     -> PROTOCOL error -32602: Resource not found: catalog://courses/nope

  Bad arguments and unknown ids are returned as tool results with isError,
  so a model can read the message and correct itself. An unknown tool or
  resource is a protocol error: the request itself was wrong.

============================================================================
4. ROBUSTNESS CHECKS
============================================================================
  [PASS] truncated JSON -> -32700, id null        {"code":-32700,"message":"Parse error"}
  [PASS] batch array -> -32600                    {"code":-32600,"message":"Invalid Request"}
  [PASS] no _meta on a fresh process -> -32602    Missing _meta protocol fields; this server speaks ['2026-07-28',
  [PASS] unknown version -> -32022 with supported {"supported":["2026-07-28"],"requested":"2031-01-01"}
  [PASS] missing clientCapabilities -> -32602     Invalid params: missing io.modelcontextprotocol/clientCapabiliti
  [PASS] unknown method -> -32601                 Method not found: reports/export
  [PASS] undeclared argument -> isError result    Invalid arguments: unexpected argument 'debug'
  [PASS] notification produced no reply           next reply matched the next request id
  [PASS] exits on stdin EOF                       exit code 0
  [PASS] stdout carried only JSON-RPC             no stray lines; logs went to stderr

  10/10 robustness checks passed

============================================================================
5. WHAT THIS LAB IS AND IS NOT
============================================================================
  REAL: a real subprocess speaking newline-delimited JSON-RPC; every message
  and verdict above is what the server actually returned.

  ILLUSTRATIVE: the catalog data is five hard-coded courses, and argument
  validation implements only the JSON Schema keywords these tools use.

  NOT SHOWN: Streamable HTTP hosting, authorization (M9-L10..L13), progress
  and cancellation (M9-L14), subscriptions, and packaging (M9-L16).

Done.
```

### 7.3 Reading the result

**Section 1 is worth reading line by line.** Every field discussed in M9-L04 to M9-L07 appears on the wire:
`resultType`, `ttlMs`, `cacheScope`, `structuredContent`, `_meta.serverInfo`.

**Section 2 shows the same server in the other era**: after `initialize`, results contain only `tools` — no
`resultType`, no caching fields.

### 7.4 Expected output — SDK interop and mutation test

`[EXECUTED]` — 2026-09-16, Python 3.12.3, `mcp` 2.2.0 in a virtual environment. Run twice; output identical.

```text
  official SDK version: mcp 2.2.0

============================================================================
1. SDK CLIENT (mode='auto') -> OUR STDLIB SERVER
============================================================================
  [PASS] negotiated version / server identity     2026-07-28 / course-catalog
  [PASS] tools/list                               ['plan_study_time', 'search_courses']
  [PASS] tools/call search_courses (structured)   ['aws-110', 'py-100']
  [PASS] tools/call plan_study_time               {"total_hours": 48, "weeks": 5}
  [PASS] tool execution error -> isError          Unknown course id(s): ['mcp-999']. Call search_courses to 
  [PASS] resources/list + templates/list          catalog://courses/{course_id}
  [PASS] resources/read                           {"id": "rag-201", "title": "Retrieval-Augmented Generation
  [PASS] prompts/get                              Create a week-by-week study plan for 'Python for AI Engine...
  [PASS] unknown tool rejected                    as a PROTOCOL error: Unknown tool: drop_tables

  9/9 checks passed

============================================================================
2. SDK CLIENT (mode='legacy') -> OUR STDLIB SERVER
============================================================================
  [PASS] negotiated version / server identity     2025-11-25 / course-catalog
  [PASS] tools/list                               ['plan_study_time', 'search_courses']
  [PASS] tools/call search_courses (structured)   ['aws-110', 'py-100']
  [PASS] tools/call plan_study_time               {"total_hours": 48, "weeks": 5}
  [PASS] tool execution error -> isError          Unknown course id(s): ['mcp-999']. Call search_courses to 
  [PASS] resources/list + templates/list          catalog://courses/{course_id}
  [PASS] resources/read                           {"id": "rag-201", "title": "Retrieval-Augmented Generation
  [PASS] prompts/get                              Create a week-by-week study plan for 'Python for AI Engine...
  [PASS] unknown tool rejected                    as a PROTOCOL error: Unknown tool: drop_tables

  9/9 checks passed

============================================================================
3. MUTATION TEST: WHICH PLANTED BUGS DOES THE SDK CLIENT NOTICE?
============================================================================
  banner printed to stdout                  
      -> worked: 2026-07-28, 2 tools, structured keys=['results'], bad call isError=True
  responses pretty-printed                  
      -> HUNG (timed out)
  response id echoed as a string            
      -> worked: 2026-07-28, 2 tools, structured keys=['results'], bad call isError=True
  tools/list returns an object, not an array
      -> ERROR ValidationError: 1 validation error for ListToolsResult
  no cacheScope on list results             
      -> ERROR ValidationError: 1 validation error for ListToolsResult
  no resultType on any result               
      -> ERROR ValidationError: 1 validation error for ListToolsResult
  structuredContent violates outputSchema   
      -> ERROR RuntimeError: Invalid structured content returned by tool search_courses: 'results' is a required property
  isError missing on tool errors            
      -> ERROR RuntimeError: Tool plan_study_time has an output schema but did not return structured content
  server/discover not implemented           
      -> worked: 2025-11-25, 2 tools, structured keys=['results'], bad call isError=True

  Read each line as: did an independent client catch this bug? Anything
  that 'worked' is a bug your own tests must catch, because a tolerant
  client will not -- and a stricter client elsewhere may break on it.

============================================================================
4. SDK CLIENT (mode='auto') -> THE SAME SERVER WRITTEN WITH THE SDK
============================================================================
  [PASS] negotiated version / server identity     2026-07-28 / course-catalog-sdk
  [PASS] tools/list                               ['plan_study_time', 'search_courses']
  [PASS] tools/call search_courses (structured)   ['aws-110', 'py-100']
  [PASS] tools/call plan_study_time               {"total_hours": 48, "weeks": 5}
  [PASS] tool execution error -> isError          Error executing tool plan_study_time: Unknown course id(s)
  [PASS] resources/list + templates/list          catalog://courses/{course_id}
  [PASS] resources/read                           {"id": "rag-201", "title": "Retrieval-Augmented Generation
  [PASS] prompts/get                              Create a week-by-week study plan for 'Python for AI Engine...
  [PASS] unknown tool rejected                    as an isError RESULT: Unknown tool: drop_tables

  9/9 checks passed

============================================================================
5. WHAT THIS CHECK IS AND IS NOT
============================================================================
  REAL: the official SDK client launched each server as a subprocess over
  stdio; every PASS, ERROR and 'worked' above is its actual behaviour.

  NOT SHOWN: other SDKs (TypeScript, Java...) may be stricter or more
  tolerant; Streamable HTTP; authorization. Passing one client's checks is
  necessary for interoperability, not proof of conformance.

Done.
```

### 7.5 Reading the result

**Sections 1, 2 and 4 are the good news**: an independent implementation accepts both servers in both eras.

**Section 3 is the lesson.** Five mutations raised errors, one hung, and three worked. For each "worked" row, write
the test that would catch it before you read §6.

---

## 8. Common mistakes and troubleshooting

1. **Letting any library or `print()` write to stdout.** §5.2, §5.7 row 1.
2. **Returning argument-validation failures as protocol errors.** §5.4 — the model cannot self-correct from a
   JSON-RPC error as easily.
3. **Echoing request ids with a different type.** §5.7 row 3, §6.
4. **Skipping `server/discover`** and not noticing the client fell back to legacy. §5.7 row 9.
5. **Leaking exception text to clients.** §5.2 — log details to stderr, return a generic `-32603`.
6. **Raising plain exceptions from `MCPServer` tools** when the model should see the message. §5.8 — use `ToolError`.
7. **Following `FastMCP` tutorials with `mcp` 2.x installed.** §5.8.

| Symptom | Likely cause | Fix |
|---|---|---|
| Host log: "invalid response id" | Id echoed as a string or reformatted | Echo `msg["id"]` unchanged |
| Host shows the server as connected, but on an old protocol version | `server/discover` missing or failing | Implement discover; assert negotiated version in tests |
| Client hangs at startup | Multi-line JSON or no output flush | Compact JSON, `flush()` after every message |
| Model keeps repeating a bad call | Execution error message not actionable, or hidden by the SDK | Say what to change; raise `ToolError` |
| `ModuleNotFoundError: mcp.server.fastmcp` | `mcp` 2.x | `from mcp.server.mcpserver import MCPServer` |
| Client `ValidationError` on list results | Missing `resultType`, `ttlMs` or `cacheScope` | Include all three on modern results |

---

## 9. Security, privacy, reliability, cost

- **Security.** Never return exception text or stack traces to clients (§5.2); the SDK's crash masking exists for
  the same reason (§5.8). Read-only annotations are claims, not controls. Validate every argument server-side.
- **Privacy.** stderr logs are collected by hosts; log method names and ids, not argument values containing personal
  data.
- **Reliability.** One bad request must never kill the process (§5.2). Interop and mutation tests catch the bugs
  that tolerant clients hide (§5.7).
- **Cost.** Actionable execution-error messages reduce repeated model calls; caching hints on lists reduce round
  trips (M9-L06).

---

## 10. Exercises

### Exercise 1 — Beginner (~25 min)

1. Run both labs. Which checks in §7.2 section 4 map to which earlier lesson?
2. For each failure in §5.4's table, explain why it belongs on its channel.
3. List the three mutations the SDK client tolerated and the risk each poses with a stricter client.
4. Why does the server strip `resultType`, `ttlMs` and `cacheScope` in legacy mode?
5. What does the model see when an `MCPServer` tool raises `ValueError`, and why did the SDK authors choose that?

### Exercise 2 — Intermediate (~50 min)

1. Add a tool `get_prerequisites(course_id)` to both servers. Decide whether it should really be a resource template
   (M9-L03), and justify the choice.
2. Add three assertions to `l09_build_first_server.py` that would catch the three "worked" mutations.
3. Add a fourth mutation of your own design to `MUTATIONS` and record the SDK's response.
4. Make `plan_study_time` reject duplicate course ids with an actionable execution error, in both servers.
5. Register the stdlib server in an MCP host you use, call `search_courses` from a conversation, and find your stderr
   log lines in the host's MCP log.

### Exercise 3 — Challenge (~60 min)

1. Add pagination to `tools/list` with an opaque cursor and a page size of 1, and confirm the SDK client still lists
   both tools (M9-L06).
2. Implement `notifications/cancelled` handling for a deliberately slow tool (preview of M9-L14).
3. Write a property-based test that generates random argument objects for `plan_study_time` and asserts the server
   never returns `-32603` and never writes a non-JSON line.
4. Port the stdlib server's dispatch to `asyncio` so that one slow tool does not block other requests; demonstrate
   interleaved responses matched by id.
5. Compare the tool definitions the SDK generated from type hints with the hand-written ones. Where do they differ,
   and which differences change what a model is likely to send?

---

## 11. Quiz

*(Answers: [`answer-keys/module-09-answers.md`](../../answer-keys/module-09-answers.md#m9-l09).)*

**Q1.** Where does the hand-written server send details of an unexpected exception?

- A. To the client, in `error.data`
- B. To stderr, with a generic `-32603` to the client
- C. To stdout, before the response
- D. Nowhere; exceptions stop the process

**Q2.** A model calls `plan_study_time` with `hours_per_week: 500`. How should the server respond?

- A. A result with `isError: true` and an actionable message
- B. JSON-RPC error `-32602`, Invalid params
- C. JSON-RPC error `-32603`, Internal error
- D. A result with the value clamped silently to 60

**Q3.** Which failure belongs on the protocol-error channel per the 2026-07-28 tools page?

- A. An upstream API timeout
- B. A date in the wrong format
- C. A business rule rejecting a refund
- D. A call naming a tool that does not exist

**Q4.** In §7.4, how many checks did the SDK client pass against the stdlib server in legacy mode?

- A. 5 of 9
- B. 8 of 9
- C. 9 of 9
- D. 0 of 9, because legacy is unsupported

**Q5.** What happened when the mutated server did not implement `server/discover`?

- A. The client fell back to 2025-11-25 and worked
- B. The client raised a `ValidationError`
- C. The client hung until the watchdog fired
- D. The client refused to connect

**Q6.** Why did the "id echoed as a string" mutation go unnoticed by the SDK client?

- A. JSON-RPC treats `"1"` and `1` as the same id
- B. The server only ever used string ids
- C. The watchdog timeout was too short
- D. The SDK coerces numeric-string ids for correlation

**Q7.** Which mutation made the SDK client hang?

- A. A banner printed to stdout
- B. No `cacheScope` on list results
- C. Pretty-printed responses
- D. `tools` returned as an object

**Q8.** What is the main conclusion of the mutation test?

- A. The SDK client is far too lenient to be of any use
- B. Client acceptance is necessary, but your own tests must catch tolerated bugs
- C. Hand-written servers cannot interoperate reliably at all
- D. Only protocol errors matter for interoperability

**Q9.** In an `MCPServer` tool, how do you make an anticipated failure's message reach the model?

- A. Return a string starting with `Error:`
- B. Raise `ValueError` with the message
- C. Call `sys.exit` with the message
- D. Raise `ToolError` with the message

**Q10.** How did the SDK-built server report a call to an unknown tool?

- A. As JSON-RPC error `-32601`
- B. As a result with `isError: true`
- C. As JSON-RPC error `-32602`
- D. It returned an empty successful result

**Q11.** In §6, what hid the missing `server/discover` for six months?

- A. The server's stderr logging
- B. A resource template misconfiguration
- C. The host's silent fallback to the legacy handshake
- D. Id coercion inside the newly adopted client

**Q12.** Why does the server strip `resultType`, `ttlMs` and `cacheScope` from legacy-era results?

- A. Those fields are not part of the 2025-11-25 schema
- B. Legacy clients reject any unknown field
- C. They would leak cache contents
- D. JSON-RPC forbids them in results

**Q13.** *(Written, rubric-graded.)* In under 150 words: your team's MCP server passes all tests using one popular
host. Before offering it to other teams, what additional testing would you add, and why? Use evidence from this
lesson.

---

## 12. Revision notes

- **One file, five lessons:** line framing + stderr logs; JSON-RPC shapes and codes; per-request `_meta` +
  `server/discover` + legacy `initialize`; caching hints; schemas + `structuredContent`.
- **Errors:** bad arguments / business failures → `isError: true` with actionable text; unknown tool/resource,
  malformed request → JSON-RPC error; unexpected exceptions → log to stderr, return `-32603`.
- **Interop (mcp 2.2.0 client):** 9/9 modern, 9/9 legacy.
- **Mutation test:** 5 caught (errors), 1 hung (pretty-printed JSON), 3 **tolerated** — stdout banner, string ids,
  missing `server/discover` (silent legacy fallback). Test those yourself.
- **SDK server:** `MCPServer` (formerly `FastMCP`); raise `ToolError` for messages the model should see; unknown tools
  come back as `isError` results.

---

## 13. Completion checklist

- [ ] I built and ran a stdio server with tools, resources, a template and a prompt.
- [ ] I can place any failure on the correct error channel.
- [ ] I ran the official SDK client against my server in both eras.
- [ ] I can explain each row of the mutation-test table.
- [ ] I can build the same server with `MCPServer` and know its two behaviour differences.
- [ ] I scored at least 10/13 on the quiz.

---

## 14. References

- MCP 2026-07-28, *Tools* (error handling channels, structured content) —
  <https://modelcontextprotocol.io/specification/2026-07-28/server/tools> `[VERIFIED 2026-09-15]`
- MCP 2026-07-28, *Versioning and Compatibility* (dual-era servers) —
  <https://modelcontextprotocol.io/specification/2026-07-28/basic/versioning> `[VERIFIED 2026-09-15]`
- MCP Python SDK `mcp` 2.2.0 — `mcp.Client`, `mcp.server.mcpserver.MCPServer`, `ToolError`/`UnexpectedToolError`
  docstrings, `coerce_request_id` in `mcp/shared/dispatcher.py` — <https://pypi.org/project/mcp/> `[VERIFIED 2026-09-16, source read and executed]`
- MCP Python SDK v2 migration guide (FastMCP → MCPServer) — <https://py.sdk.modelcontextprotocol.io/v2/migration/> `[UNVERIFIED — URL taken from the SDK's error message]`
- MCP Inspector — <https://github.com/modelcontextprotocol/inspector> `[UNVERIFIED]`

---

## 15. Next lesson

→ [M9-L10 — Authentication vs Authorization in MCP](M9-L10-authentication-vs-authorization.md) asks the question this
server has ignored so far: who is calling, and what are they allowed to do?
