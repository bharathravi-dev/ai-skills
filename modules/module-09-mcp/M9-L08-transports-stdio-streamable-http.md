# M9-L08 — Transports: stdio and Streamable HTTP; Local vs Remote

| | |
|---|---|
| **Lesson ID** | M9-L08 |
| **Difficulty** | 2 (Intermediate) |
| **Estimated study time** | 2.0 hours |
| **Prerequisites** | [M9-L05](M9-L05-initialization-capability-negotiation.md), [M2-L11](../module-02-python-foundations/M2-L11-http-rest.md) |

---

## 1. Learning objectives

1. **Implement** a stdio MCP client that frames messages as single lines, reads responses from stdout and
   treats stderr as logs.
2. **Diagnose** the two most common stdio framing bugs — logging to stdout and multi-line JSON — from their
   measured symptoms.
3. **Shut down** a stdio server correctly: close stdin, then escalate to SIGTERM and SIGKILL.
4. **Describe** the 2026-07-28 Streamable HTTP transport: one POST endpoint, JSON or SSE responses, `202` for
   notifications, and the mirrored `MCP-Protocol-Version`, `Mcp-Method` and `Mcp-Name` headers.
5. **Apply** the transport's security rules — header/body consistency (`-32020`), `Origin` validation and
   loopback binding — and choose between local and remote deployment.

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **Transport** | How MCP messages physically move between client and server. The message format (JSON-RPC) is the same on every transport. |
| **stdio** | The client launches the server as a subprocess; messages go over the child's stdin and stdout, one per line. |
| **Streamable HTTP** | The server is an independent HTTP service with one endpoint; each client message is its own POST. |
| **SSE** | Server-Sent Events: an HTTP response of type `text/event-stream` that delivers a sequence of `data:` events. |
| **Framing** | How a receiver knows where one message ends and the next begins. stdio uses newlines. |
| **Mirrored header** | An HTTP header that repeats a value from the JSON body so infrastructure can route without parsing the body. |
| **DNS rebinding** | An attack that lets a web page in the user's browser send requests to services on the user's own machine. |
| **Local vs remote server** | A local server runs on the user's machine (usually stdio); a remote server runs elsewhere and is reached over HTTP. |

---

## 3. Plain-language explanation

### 3.1 The same messages, two kinds of pipe

Everything so far in this module has been about **what** the messages say. A transport is about **how they get
there**. MCP defines two standard transports. **stdio** is for servers that run on your machine: the host starts
the server as a child process and the two talk through its standard input and output, exactly as a shell pipes
programs together. **Streamable HTTP** is for servers that run somewhere else: each message is an HTTP POST to
one URL.

### 3.2 stdio is simple, and unforgiving

On stdio, **each message is one line of JSON** and **stdout carries nothing but messages**. That simplicity has
two sharp edges, both measured in §7. A server that prints a friendly "loading…" line to stdout produced
**11 non-protocol lines among 21**, and a client that matched responses line by line got **0 of 10** right.
A client that sent pretty-printed JSON — one message spread over 11 lines — got **11 parse errors and no
result**. Neither bug is visible when you test the server by hand in a terminal, because a human reads right
past both.

### 3.3 Shutting a child process down

The polite way to stop a stdio server is to close its input; a well-behaved server notices end-of-file and
exits. §7.4 showed what happens when servers don't: one needed **SIGTERM**, another ignored that too and needed
**SIGKILL**, which ends a process without letting it clean up.

### 3.4 Streamable HTTP in the 2026-07-28 shape

For remote servers, the client POSTs each request to one endpoint, such as `https://example.com/mcp`. The server
answers with either a plain JSON response or an **SSE stream** that carries progress notifications and then the
final response. Notifications get `202 Accepted` and no body. Since 2026-07-28 there are **no sessions**, **no
standing GET stream**, and **no resumable streams** — each request stands alone, which is what makes these
servers easy to put behind a load balancer.

### 3.5 HTTP brings HTTP's problems

Putting a server on HTTP invites three attacks the lab demonstrates. A proxy that routes or authorises on a
header can be fooled if the body says something different (§7.6). A web page in a user's browser can try to talk
to a server on that user's laptop (§7.7). And a local server bound to every network interface is reachable by
everyone on the network. The protocol's answers are strict header checks, `Origin` validation, and binding to
`127.0.0.1`.

---

## 4. Analogy

**An intercom inside a house versus the postal service.** stdio is an intercom between two rooms: whatever is
said into it goes straight to the other end, so if someone in the kitchen starts singing into the intercom
(logging to stdout), the other room can no longer tell instructions from noise. Streamable HTTP is the postal
service: every letter travels separately in its own envelope (a POST), addressed to one office, and a reply may
come as one letter or a short series of updates followed by the final answer (SSE). The sorting office reads the
envelope (headers) without opening the letter (body) — so if the envelope says "brochure" and the letter inside
says "cheque", the office must refuse it.

### Where the analogy breaks

- **Intercoms have no natural message boundaries; stdio does — newlines.** That is exactly why a message must not
  contain a raw newline (§7.3). An intercom conversation can pause mid-sentence; a stdio message cannot span lines.
- **Post offices don't care who posted the letter; an MCP HTTP server must.** Browsers attach an `Origin` header,
  and a local server must reject origins it does not recognise (§7.7). Authentication comes on top of that
  (M9-L10, M9-L11).

---

## 5. Detailed technical explanation

### 5.1 stdio: the rules

`[VERIFIED 2026-09-15 — MCP 2026-07-28, Transports: stdio]`

- The client launches the server as a subprocess. The server reads JSON-RPC from **stdin** and writes JSON-RPC to
  **stdout**.
- Messages are **delimited by newlines and MUST NOT contain embedded newlines**.
- The server **MUST NOT** write anything to stdout that is not a valid MCP message; the client MUST NOT write
  anything else to stdin.
- The server MAY write UTF-8 logs to **stderr**; the client MAY capture, forward or ignore them and SHOULD NOT
  treat stderr output as an error signal.
- The server MUST NOT write JSON-RPC *requests* to stdout. Server-to-client needs travel as `input_required`
  results (M9-L06).
- Cancellation on stdio is an explicit `notifications/cancelled` notification (M9-L14).
- The same framing works over Unix sockets or TCP; only launch, stderr and shutdown are subprocess-specific.

`[REAL, measured]` §7.1 ran a real child process: three `tools/call` requests produced three responses on stdout,
a notification produced **0** stdout lines, and all log output (5 lines) appeared on stderr.

### 5.2 The stdout-pollution bug

`[REAL, measured]` §7.2 sent 10 requests to two server variants:

| Server | stdout lines | Not JSON-RPC | Line-per-response client correct |
|---|---|---|---|
| Logs to stderr | 10 | 0 | 10/10 |
| Logs to stdout | 21 | 11 | **0/10** |

In Python, the usual culprits are a stray `print()`, a logging handler configured with `sys.stdout`, a library that
prints a banner or progress bar on import, and warnings emitted by dependencies. A robust client may skip
non-JSON lines rather than crash, but that only hides a server bug that another client will not forgive. The fix is
on the server:

```python
import logging, sys
logging.basicConfig(stream=sys.stderr, level=logging.INFO)   # never stdout on a stdio server
```

### 5.3 The multi-line JSON bug

`[REAL, measured]` §7.3: compact JSON (1 line) produced 1 result; `json.dumps(..., indent=2)` (11 lines) produced
**0 results and 11 parse errors** — the server tried to parse each line as a separate message.

Compact JSON can never contain a raw newline: `json.dumps` escapes a newline inside a string as the two characters
`\n`. So the rule "one message per line" is satisfied automatically by default serialization — and broken the moment
someone adds `indent` for readability.

### 5.4 stdio shutdown

The client SHOULD: **(1)** close the server's stdin; **(2)** wait for it to exit; **(3)** if it does not exit in a
reasonable time, terminate it — on POSIX, `SIGTERM` then `SIGKILL`; on Windows, `TerminateProcess` or Job Objects.
Servers SHOULD exit promptly on stdin EOF, which is the only portable graceful signal. If a server dies unexpectedly
the client SHOULD restart it; because the protocol is stateless, in-flight requests are simply lost and retried.

`[REAL, measured]` §7.4 with a 1-second grace period per step:

| Server behaviour | Outcome | Exit code |
|---|---|---|
| Exits on stdin EOF | exited after closing stdin | 0 |
| Ignores EOF | needed SIGTERM | −15 |
| Ignores EOF and SIGTERM | needed SIGKILL | −9 |

Each escalation costs the grace period, so a host that starts and stops many servers pays for every misbehaving
one. Never skip straight to SIGKILL: a server mid-write to a local file or database gets no chance to finish.

### 5.5 Streamable HTTP (2026-07-28)

`[VERIFIED 2026-09-15 — MCP 2026-07-28, Transports: Streamable HTTP]`

| Rule | Detail |
|---|---|
| Endpoint | One path (the *MCP endpoint*) that accepts POST, e.g. `https://example.com/mcp` |
| Each message | Its own POST; body is a single JSON-RPC request or notification |
| `Accept` | Client MUST list both `application/json` and `text/event-stream` |
| Request response | `Content-Type: application/json` (one object) **or** `text/event-stream` (notifications related to that request, then the response); clients MUST support both |
| Notification response | `202 Accepted`, no body |
| Server → client requests | Not sent on streams; embedded as `input_required` results (MRTR) |
| Change notifications | On a long-lived `subscriptions/listen` POST response stream |
| Cancellation | Closing the SSE response stream *is* the cancellation |
| Proxies | Servers SHOULD send `X-Accel-Buffering: no` on SSE responses |
| Removed in 2026-07-28 | `Mcp-Session-Id` sessions, the GET stream, `Last-Event-ID` resumability — a broken stream loses the request, which the client re-issues with a new id |

`[REAL, measured]` §7.5 against a real `http.server` on 127.0.0.1: `tools/list` → **200 JSON**; `tools/call` for a
long-running tool → **200 SSE with 3 progress notifications and the response**; a notification → **202, empty
body**; a legacy GET → **405**.

A server that supports only 2026-07-28 SHOULD answer legacy GET or DELETE with `405`, and ignore `Mcp-Session-Id`
and `Last-Event-ID` headers.

### 5.6 Mirrored headers and header/body consistency

Every POST MUST carry:

| Header | Mirrors | Required for |
|---|---|---|
| `MCP-Protocol-Version` | `_meta["io.modelcontextprotocol/protocolVersion"]` | All POSTs |
| `Mcp-Method` | `method` | All requests |
| `Mcp-Name` | `params.name` or `params.uri` | `tools/call`, `resources/read`, `prompts/get` |
| `Mcp-Param-{Name}` | A tool argument marked `x-mcp-header` in its `inputSchema` | When the argument is present |

Values that are not plain ASCII use a `=?base64?…?=` sentinel encoding. Servers that process the body MUST reject
any missing required header or any header that disagrees with the body, with **HTTP 400 and `-32020`
HeaderMismatch**.

`[REAL, measured]` §7.6: a request whose `Mcp-Name` header said `build_report` while the body said
`delete_all_reports` was rejected with **400 / `-32020`**, as was a request missing `Mcp-Name`.

The reason is **split-brain authorization**. Headers exist so load balancers, gateways and web application firewalls
can route, rate-limit or authorise without parsing JSON. If a gateway allows "`build_report`" by header and the
server executes the body's `delete_all_reports`, the gateway's policy was bypassed. Consistency checking at the
server closes that gap. Two further rules follow: intermediaries enforcing policy on mirrored headers SHOULD reject
requests whose `MCP-Protocol-Version` predates header validation, and servers SHOULD NOT mark sensitive parameters
(tokens, passwords, personal data) with `x-mcp-header`, because headers are visible to every intermediary and often
logged.

### 5.7 `Origin`, loopback binding, and local servers

Servers **MUST** validate the `Origin` header and respond **403** to an invalid one. When running locally they
**SHOULD bind to 127.0.0.1**, not `0.0.0.0`, and SHOULD require authentication.

`[REAL, measured]` §7.7: no `Origin` (a non-browser client) → 200; `http://localhost:<port>` → 200;
`https://evil.example` → **403**; `http://localhost.evil.example` → **403**. The last one matters: an allowlist
implemented as "starts with `http://localhost`" would have accepted it.

Browsers attach `Origin` to cross-site requests. Without validation, a page on any website the user visits can
script requests to a local MCP server — directly to `localhost`, or via **DNS rebinding**, where an attacker's
domain is made to resolve to `127.0.0.1` after the page loads. A local server with file-system or shell tools is a
high-value target. The MCP security guidance adds: prefer **stdio** for local servers where possible (only the
launching client can talk to it), and if HTTP is necessary, require a token or use a Unix domain socket.

### 5.8 Status codes for protocol errors

`[REAL, measured]` §7.8: an unsupported version → **400** with `-32022` and `data.supported`; an unknown method →
**404** with a `-32601` body. The JSON-RPC body is what lets a dual-era client tell a modern server's 404 ("method
unknown") from a legacy server's 404 ("no such endpoint") before falling back (M9-L05). Missing required `_meta`
fields and missing client capabilities are also 400.

### 5.9 Choosing local or remote

| Consideration | Local (stdio) | Remote (Streamable HTTP) |
|---|---|---|
| Who can connect | Only the launching process | Anyone who can reach the URL — needs auth |
| Credentials | From the environment (spec: stdio SHOULD NOT use the OAuth flow) | OAuth 2.1 resource server (M9-L11) |
| Access to user's machine | Full, with the user's privileges — sandbox it | None, unless you build it |
| Scaling | One process per client | Stateless requests behind a load balancer |
| Distribution | User installs and trusts a binary/package | Operator deploys once; users configure a URL |
| Typical fit | File system, local dev tools, desktop apps | Shared SaaS integrations, multi-user data |

### 5.10 Assumptions and limitations

- The lab's HTTP server implements only this lesson's checks; its `406` for a missing `text/event-stream` in
  `Accept` is a lab choice, not a spec-mandated code.
- No TLS: loopback only. Remote servers must use HTTPS.
- Shutdown results are specific to POSIX signal semantics; Windows uses different mechanisms.

---

## 6. Worked example — the database server that worked in the terminal but not in the IDE

**The situation.** A developer built a stdio MCP server exposing read-only SQL queries against a local analytics
database. Running `python server.py` in a terminal and pasting JSON lines by hand worked perfectly. Configured in
an IDE's MCP client, the server showed as "failed to connect" roughly half the time, and when it did connect, the
first tool call sometimes returned another call's result.

**Investigation.**

1. The IDE's MCP log showed `Unexpected token 'C' in JSON at position 0` — the first stdout line began with
   `Connecting to analytics.db...`. The database driver printed a banner **to stdout** on first connection, and the
   server's own `logging.basicConfig()` call had been copied from a script that logged to stdout. This is §5.2.
2. The "half the time" came from timing: when the IDE's probe arrived before the database connected, the first
   response line was valid; when the banner won the race, the client rejected the stream.
3. The mismatched results appeared in a second IDE that skipped unparseable lines but correlated by position for
   its first request — §7.2's line-per-response client, and M9-L04's correlation lesson.

**A second problem found while fixing it.** To make debugging easier, the developer had added an HTTP mode:
`server.py --http` bound to `0.0.0.0:8765` with no authentication and no `Origin` check. On the office network,
anyone could run SQL against the developer's analytics database, and any website the developer visited could
script requests to it.

| # | Defect | Mechanism | Fix |
|---|---|---|---|
| 1 | Driver banner and app logs on stdout | §5.2 | `logging` to stderr; redirect or silence the driver's banner |
| 2 | Client correlated by position | M9-L04 | Correlate by id; treat non-JSON stdout as a server bug |
| 3 | HTTP mode bound to all interfaces | §5.7 | Bind `127.0.0.1`; require a token |
| 4 | No `Origin` validation | §5.7 | Exact-match allowlist; 403 otherwise |

**Verification.** A test launched the server as a subprocess, sent 50 compact requests, and asserted that every
stdout line parsed as JSON-RPC and matched a request id — the check the terminal session could never perform,
because humans ignore banners.

**The general rule.** **Test a transport the way a program uses it, not the way a person does.** A person reading
a terminal filters noise; a client parsing a stream does not.

---

## 7. Practical activity

**Files:** [`labs/m9/l08_transports_stdio_streamable_http.py`](../../labs/m9/l08_transports_stdio_streamable_http.py)
and its helper server [`labs/m9/l08_stdio_server.py`](../../labs/m9/l08_stdio_server.py)

**No API key, no internet access, no third-party dependencies.** Uses subprocesses and the loopback interface only.
Takes about 6 seconds (it waits out shutdown grace periods).

```bash
source .venv/bin/activate
python labs/m9/l08_transports_stdio_streamable_http.py
```

### 7.2 Expected output

`[EXECUTED]` — 2026-09-16, Python 3.12.3 on Linux (pure standard library). Run twice; output identical.

```text

============================================================================
1. STDIO: A CLEAN ROUND TRIP OVER A REAL SUBPROCESS
============================================================================
  responses on stdout : [(1, '121'), (2, '144'), (3, '169')]
  extra stdout lines after a notification: 0
  stderr lines (logs) : 5 -> first: '[server] starting up, loading report index'

============================================================================
2. STDIO: A SERVER THAT LOGS TO STDOUT
============================================================================
  clean  server: 10 stdout lines for 10 requests,  0 not JSON-RPC; line-per-response client matched 10/10
  noisy  server: 21 stdout lines for 10 requests, 11 not JSON-RPC; line-per-response client matched  0/10

  The noisy server's responses are all present, but every log line
  shifts the stream. A strict client treats a non-JSON line as a fatal
  framing error; a line-counting client mismatches everything after the
  first log line. Only one rule prevents both: stdout carries MCP
  messages and nothing else; logs go to stderr.

============================================================================
3. STDIO: PRETTY-PRINTED JSON BREAKS NEWLINE FRAMING
============================================================================
  compact  :  1 line(s) sent -> 1 result(s), 0 parse error(s)
  indent=2 : 11 line(s) sent -> 0 result(s), 11 parse error(s)

  json.dumps never emits a raw newline inside a string (it writes \n),
  so compact JSON is always exactly one line: "line1\nline2"

============================================================================
4. STDIO SHUTDOWN: CLOSE STDIN, THEN SIGTERM, THEN SIGKILL
============================================================================
  clean           -> exited after closing stdin (code 0)
  ignore_eof      -> needed SIGTERM (code -15)
  ignore_sigterm  -> needed SIGKILL (code -9)

  Negative codes are the signal number that ended the process. Every
  escalation step costs the client its grace period, and SIGKILL gives
  the server no chance to flush or clean up.

============================================================================
5. STREAMABLE HTTP: ONE POST ENDPOINT, JSON OR SSE, 202, 405
============================================================================
  server bound to 127.0.0.1 (loopback only) on an ephemeral port
  tools/list                    -> HTTP 200, JSON result with 1 tool(s)
  tools/call build_report       -> HTTP 200, SSE with 4 events: ['notifications/progress', 'notifications/progress', 'notifications/progress', 'response']
  a notification POST           -> HTTP 202, empty body
  legacy GET for a standing SSE -> HTTP 405 (no GET stream in 2026-07-28)
  Accept without event-stream   -> HTTP 406 (the lab server's choice for a non-conforming client)

============================================================================
6. MIRRORED HEADERS: WHY THE SERVER CHECKS THEM AGAINST THE BODY
============================================================================
  header says build_report, body says delete_all_reports
    -> HTTP 400, Header mismatch: headers (tools/call, build_report) vs body (tools/call, delete_all_reports)
  Mcp-Name header missing
    -> HTTP 400, Header mismatch: required MCP header missing

  A gateway that authorizes on Mcp-Name ('build_report is allowed') while
  the server executes the body ('delete_all_reports') is a split-brain
  authorization bypass. The server MUST reject any mismatch with -32020.

============================================================================
7. ORIGIN VALIDATION: A BROWSER PAGE TALKING TO A LOCAL SERVER
============================================================================
  (no Origin header: non-browser client)     -> HTTP 200
  Origin: http://localhost:<port>            -> HTTP 200
  Origin: https://evil.example               -> HTTP 403
  Origin: http://localhost.evil.example      -> HTTP 403

  Without this check, a web page on any site the user visits can script
  requests to a server listening on the user's machine (via DNS rebinding
  or plain localhost fetches). Servers MUST validate Origin and SHOULD bind
  to 127.0.0.1 rather than 0.0.0.0 when running locally.

============================================================================
8. VERSION AND METHOD ERRORS AS HTTP STATUS CODES
============================================================================
  unsupported version  -> HTTP 400, JSON-RPC -32022, data={'supported': ['2026-07-28'], 'requested': '2025-11-25'}
  unknown method       -> HTTP 404, JSON-RPC -32601, data=None

  A 404 WITH a JSON-RPC -32601 body means 'modern server, unknown method';
  a bare 404 or 400 with no recognized body is how a client detects a legacy
  server and falls back (M9-L05).

============================================================================
9. WHAT THIS LAB IS AND IS NOT
============================================================================
  REAL: real subprocesses, real pipes, real signals, and a real HTTP server
  on the loopback interface; every count, status code and exit code above
  was observed on this machine.

  ILLUSTRATIVE: the HTTP server implements only the checks this lesson
  covers; the 406 for a bad Accept header is this lab's choice; timings are
  reported only as which shutdown step was needed.

  NOT SHOWN: TLS, authorization headers (M9-L10, M9-L11), subscriptions/listen
  streams, cancellation by closing an SSE stream (M9-L14), and the Base64
  sentinel encoding for non-ASCII header values.

Done.
```

### 7.3 Reading the result

**Sections 2 and 3 are the stdio bugs you will actually meet.** Both come from habits that are good everywhere
else — logging progress, pretty-printing JSON — and both are invisible in a terminal.

**Section 6 is about infrastructure you do not own.** The server is fine on its own; the risk appears only when a
gateway makes decisions from headers.

**Section 7's fourth row is a string-matching lesson.** `localhost.evil.example` is a perfectly good attacker domain.

---

## 8. Common mistakes and troubleshooting

1. **Logging, printing banners or progress bars to stdout on a stdio server.** §5.2.
2. **Sending pretty-printed or otherwise multi-line JSON.** §5.3.
3. **Servers that ignore stdin EOF; clients that go straight to SIGKILL or never kill at all.** §5.4.
4. **Omitting mirrored headers, or letting them disagree with the body.** §5.6.
5. **Marking tokens or personal data with `x-mcp-header`.** §5.6.
6. **Binding local HTTP servers to `0.0.0.0`, or skipping `Origin` validation / using prefix matching.** §5.7.
7. **Expecting sessions, a GET stream or resumable streams from a 2026-07-28 server.** §5.5.

| Symptom | Likely cause | Fix |
|---|---|---|
| `Unexpected token` / JSON parse error on the first line | Something printed to stdout | Route all logs to stderr (§5.2) |
| Server returns `-32700` for every request from one client | Client sends multi-line JSON | Compact serialization (§5.3) |
| Host hangs for seconds when closing | Server ignores stdin EOF | Exit on EOF; client escalates SIGTERM → SIGKILL (§5.4) |
| HTTP 400 with `-32020` | Missing or mismatched `MCP-Protocol-Version` / `Mcp-Method` / `Mcp-Name` | Mirror exactly from the body (§5.6) |
| HTTP 403 from a local server in a browser-based client | `Origin` not in the allowlist | Add the exact origin; never prefix-match (§5.7) |
| HTTP 405 on GET | Legacy client expecting a standing SSE stream | Upgrade client or use a dual-era server |
| SSE progress arrives all at once at the end | Reverse proxy buffering | `X-Accel-Buffering: no`; disable proxy buffering |

---

## 9. Security, privacy, reliability, cost

- **Security.** A local server runs with the user's privileges; stdio limits who can talk to it. HTTP servers need
  `Origin` validation, loopback binding when local, TLS when remote, and authentication (M9-L10–L12). Header/body
  consistency prevents gateway bypasses (§5.6).
- **Privacy.** Headers are visible to intermediaries and commonly logged: never mirror sensitive arguments
  (§5.6). stderr logs from stdio servers may be stored by the host — keep secrets out of them too.
- **Reliability.** Stateless Streamable HTTP lets any instance serve any request; the trade-off is that a broken
  stream loses the request, so clients must retry with a new id. stdio hosts must supervise and restart crashed
  servers.
- **Cost.** SSE keeps connections open for the duration of a request; long-running tools on HTTP need timeouts and
  capacity planning (M9-L14, M13-L10).

---

## 10. Exercises

### Exercise 1 — Beginner (~20 min)

1. List three things a stdio server may write to stdout and one place it should write logs.
2. Why did the indented JSON in §7.3 produce 11 parse errors rather than 1?
3. What are the three shutdown steps a stdio client should use, in order?
4. What response does a Streamable HTTP server give to a notification?
5. Name the three mirrored headers and which JSON field each mirrors.

### Exercise 2 — Intermediate (~40 min)

1. Run the lab. Add a fifth stdio server mode that writes its log lines to stdout **as JSON** (e.g.
   `{"log": "..."}`). What does each client in §7.2 do now, and why is it still wrong?
2. Make the §7.2 client robust: skip non-JSON lines with a warning and correlate by id. Re-run against the noisy
   server.
3. Add an `Mcp-Param-Region` header check to the HTTP server for a tool with a `region` argument marked
   `x-mcp-header`, including the mismatch case.
4. Change `ALLOWED_ORIGINS` checking to `origin.startswith("http://localhost")` and show which §7.7 request now
   wrongly succeeds.
5. Measure how long the host waits in §7.4 for each server mode using `time.monotonic()`, and compute the total for a
   host that restarts 20 misbehaving servers.

### Exercise 3 — Challenge (~50 min)

1. Implement cancellation on the HTTP server: detect a closed SSE stream mid-response and stop generating progress.
   Verify with a client that disconnects after the first event.
2. Write a stdio "transport conformance" test that any server can be run through: framing, stderr use, EOF exit,
   parse-error handling, and id correlation under 50 concurrent requests.
3. Implement the `=?base64?…?=` sentinel encoding and decoding for `Mcp-Name`, with tests for non-ASCII names,
   leading spaces, newlines, and literal sentinel-shaped values.
4. Design a threat model for a local HTTP MCP server with file-system tools. Include DNS rebinding, other local
   users, malware, and a malicious browser extension; state which of §5.7's controls addresses each.
5. Compare this lab's stdio client with the `mcp` 2.2.0 SDK's `mcp/client/stdio.py`: how does the SDK handle stderr,
   shutdown escalation and process restarts?

---

## 11. Quiz

*(Answers: [`answer-keys/module-09-answers.md`](../../answer-keys/module-09-answers.md#m9-l08).)*

**Q1.** On a stdio server, where should human-readable log lines go?

- A. stdout, prefixed with `#`
- B. stdout, as JSON log objects
- C. stderr
- D. Nowhere; stdio servers must not log

**Q2.** In §7.2, why did the line-per-response client match 0 of 10 requests with the noisy server?

- A. The noisy server returned errors for every call
- B. The server crashed after the first log line
- C. The responses were missing from stdout
- D. Log lines shifted every response's position in the stream

**Q3.** Why does compact `json.dumps` output satisfy stdio framing?

- A. It escapes newlines inside strings as `\n`
- B. It removes all string values containing newlines
- C. It wraps the message in a length prefix
- D. It encodes the message as base64

**Q4.** What is the correct order of steps to stop a stdio server?

- A. SIGKILL, then close stdin
- B. Close stdin, SIGTERM, then SIGKILL
- C. SIGTERM, close stdin, then SIGKILL
- D. Send an `exit` request, then SIGKILL

**Q5.** How does a 2026-07-28 Streamable HTTP server respond to a notification it accepts?

- A. `200` with an empty JSON object
- B. `204` with a JSON-RPC result
- C. An SSE stream with one event
- D. `202 Accepted` with no body

**Q6.** Which feature was removed from Streamable HTTP in 2026-07-28?

- A. SSE responses to POST requests
- B. `Mcp-Session-Id` protocol sessions
- C. The `MCP-Protocol-Version` header
- D. JSON responses to POST requests

**Q7.** What must a server do when `Mcp-Name` says `build_report` but the body names `delete_all_reports`?

- A. Execute the body, which is authoritative
- B. Execute the header, which the gateway checked
- C. Reject with HTTP 400 and `-32020`
- D. Log a warning and execute both

**Q8.** Why do mirrored headers make header/body validation necessary?

- A. Intermediaries may decide from headers while the server executes the body
- B. HTTP forbids duplicating body values in headers
- C. Headers are encrypted separately from request bodies
- D. JSON bodies cannot carry method names

**Q9.** A local HTTP MCP server receives `Origin: http://localhost.evil.example`. What should it do?

- A. Accept it because it starts with `localhost`
- B. Respond `403 Forbidden`
- C. Redirect to `127.0.0.1`
- D. Accept it if the body is valid

**Q10.** Which binding is recommended for an MCP HTTP server that runs on a user's machine?

- A. `0.0.0.0`, so the host can reach it
- B. The machine's LAN address
- C. Any interface, with a firewall rule
- D. `127.0.0.1`

**Q11.** How should a stdio server obtain credentials, per the spec?

- A. Through the OAuth authorization code flow
- B. From `Mcp-Param` headers
- C. From its environment
- D. From the client's `clientInfo`

**Q12.** In §6, why did the server appear to work when tested manually in a terminal?

- A. A person reading output ignores banner lines a parser rejects
- B. The terminal filtered the banner out automatically
- C. The database was not connected in the terminal
- D. Manual tests used the HTTP mode

**Q13.** *(Written, rubric-graded.)* In under 150 words: your team will expose a document-search MCP server to
employees. Some want it inside a desktop assistant on their laptops; the platform team wants one shared deployment.
Recommend a transport for each case and name the security controls each needs.

---

## 12. Revision notes

- **stdio:** one JSON-RPC message per line; stdout = messages only; stderr = logs; no raw newlines. Measured:
  stdout logging → **0/10** correct matches; indented JSON → **11 parse errors, 0 results**.
- **stdio shutdown:** close stdin → SIGTERM → SIGKILL (measured exit codes 0, −15, −9). Servers exit on EOF.
- **Streamable HTTP (2026-07-28):** one POST endpoint; `Accept` lists JSON and SSE; request → JSON or SSE;
  notification → 202; no sessions, no GET stream, no resumability; closing the SSE stream cancels.
- **Headers:** `MCP-Protocol-Version`, `Mcp-Method`, `Mcp-Name` (and `Mcp-Param-*`) must match the body →
  otherwise **400 / `-32020`**. Never mirror secrets.
- **Local HTTP:** validate `Origin` exactly (403), bind `127.0.0.1`, authenticate; prefer stdio for local servers.
- **Status codes:** `-32022` → 400; unknown method → 404 with `-32601` body; legacy GET → 405.

---

## 13. Completion checklist

- [ ] I can write a stdio client and server that frame, log and shut down correctly.
- [ ] I can recognise stdout pollution and multi-line JSON from their symptoms.
- [ ] I can describe a 2026-07-28 Streamable HTTP exchange, including SSE and 202.
- [ ] I can explain why header/body mismatches must be rejected.
- [ ] I can secure a local HTTP server with `Origin` validation and loopback binding.
- [ ] I scored at least 10/13 on the quiz.

---

## 14. References

- MCP 2026-07-28, *Transports: stdio* — <https://modelcontextprotocol.io/specification/2026-07-28/basic/transports/stdio> `[VERIFIED 2026-09-15]`
- MCP 2026-07-28, *Transports: Streamable HTTP* (headers, validation, `Origin`, backward compatibility) —
  <https://modelcontextprotocol.io/specification/2026-07-28/basic/transports/streamable-http> `[VERIFIED 2026-09-15]`
- MCP *Security Best Practices* (local server compromise, DNS rebinding) —
  <https://modelcontextprotocol.io/specification/2026-07-28/basic/security_best_practices> `[VERIFIED 2026-09-15]`
- WHATWG HTML Living Standard, *Server-sent events* — <https://html.spec.whatwg.org/multipage/server-sent-events.html> `[STABLE]`
- Python `subprocess` and `signal` documentation — <https://docs.python.org/3/library/subprocess.html> `[STABLE]`

---

## 15. Next lesson

→ [M9-L09 — Build Your First MCP Server (stdio, Python)](M9-L09-build-first-mcp-server.md) combines M9-L04 to
M9-L08 into one working server, then proves it interoperates by connecting the official `mcp` Python SDK client
to it.
