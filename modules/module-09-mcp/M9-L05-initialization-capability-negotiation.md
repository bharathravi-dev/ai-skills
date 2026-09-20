# M9-L05 — Initialization and Capability Negotiation

| | |
|---|---|
| **Lesson ID** | M9-L05 |
| **Difficulty** | 2 (Intermediate) |
| **Estimated study time** | 1.75 hours |
| **Prerequisites** | [M9-L04](M9-L04-json-rpc-foundations.md) |

> **Why this lesson looks different from older MCP tutorials.** Most MCP material written before August 2026
> teaches a three-message `initialize` handshake. Protocol revision **2026-07-28** removed that handshake and
> made every request self-describing. Both eras are in production at the time of writing, so this lesson
> teaches both and — more usefully — how software that must talk to either one decides which it is facing.

---

## 1. Learning objectives

1. **Trace** the legacy `initialize` → result → `notifications/initialized` handshake and apply its
   version counter-offer rule.
2. **Explain and measure** why connection-scoped capabilities fail when a connection is shared, which is the
   reason 2026-07-28 made MCP stateless.
3. **Construct** a modern request with the required `_meta` fields, and predict the server's response when a
   field is missing, the version is unsupported (`-32022`), or a required client capability is absent
   (`-32021`).
4. **Select** a protocol version safely from a server's advertised list, avoiding string ordering.
5. **Implement** the dual-era probe with `server/discover`, including the fallback rule that must not be keyed
   to a single error code.

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **Protocol version** | A string naming a specification revision, e.g. `"2025-11-25"` or `"2026-07-28"`. |
| **Capability** | A declared feature one side supports, e.g. a server's `tools`, a client's `elicitation`. Absent means unsupported. |
| **Legacy era** | Revisions `2024-11-05` through `2025-11-25`, which negotiate version and capabilities once via `initialize`. |
| **Modern era** | Revision `2026-07-28` and later, in which every request carries version and capabilities in `_meta`. |
| **Dual-era** | An implementation that supports both, choosing behaviour per server (client) or per request (server). |
| **`_meta`** | A reserved object in `params` (requests) or `result` for protocol metadata. Keys under `io.modelcontextprotocol/` are reserved. |
| **`server/discover`** | A modern RPC every server MUST implement, returning supported versions, capabilities and identity. |
| **Probe** | Sending `server/discover` first to learn which era a server belongs to. |

---

## 3. Plain-language explanation

### 3.1 Two questions before any real work

Before a client can usefully call a tool, both sides need answers to two questions: **"which version of the
rules are we using?"** and **"what can each of us actually do?"** A server that wants to ask the user for
confirmation mid-call needs to know the client can show a form; a client needs to know the server has tools
at all.

### 3.2 The old answer: agree once, per connection

Until mid-2026, MCP answered both questions with a **handshake**. The client sent `initialize` with the
version it preferred and its capabilities; the server replied with the version it would use and its own
capabilities; the client confirmed with a `notifications/initialized` notification. After that, both sides
remembered the agreement **for the life of the connection**. §7.1 runs it and shows the counter-offer rule:
if the server does not support the client's preferred version, it names one it does, and the client must
accept that or disconnect.

### 3.3 Why "once per connection" stopped being good enough

Remembering the agreement on the connection assumes **one connection = one client**. Real deployments break
that: gateways pool connections, load balancers spread requests over server instances, and one host process
serves several conversations over one stdio pipe. §7.2 put two clients with different capabilities behind one
pooled connection: **46 of 100 requests were judged using the other client's capabilities.** The protocol
cannot fix that from inside a handshake, because the handshake is the thing assuming a connection has a
single owner.

### 3.4 The new answer: every request says it again

Revision 2026-07-28 deleted the handshake. **Every request carries its protocol version and the client's
capabilities in `_meta`**, and a server MUST NOT infer either from earlier requests. A server that cannot
honour the request says so precisely: `-32022` for an unsupported version (with the list it does support),
`-32021` for a missing capability (with the list it needs). An optional `server/discover` call returns the
server's versions and capabilities up front.

### 3.5 Living with both

Clients that must reach old and new servers **probe**: send `server/discover`; a result or a recognised
modern error means "modern"; anything else — including silence — means "legacy, fall back to `initialize`."
§7.5 ran all nine client/server era combinations and then showed that a probe which falls back only on one
specific error code reaches **1 of 3** kinds of legacy server, while the rule the spec actually states
reaches **3 of 3**.

---

## 4. Analogy

**A hotel registration desk versus a membership card shown at every door.** In the old model you check in
once at reception (initialize), get a key card encoded with your room and privileges, and every door trusts
the card. That works until a family shares one card: the pool attendant sees "adult, spa access" and lets the
eleven-year-old into the sauna, because the card was registered by the parent (§7.2). In the new model there
is no check-in; each person shows a card at each door stating who they are and what they may use, and every
door decides on the spot.

### Where the analogy breaks

- **A membership card is usually verified; `_meta` is not.** The capabilities and `clientInfo` a client sends
  are *self-reported*. They tell the server what the client can technically handle, not what the caller is
  allowed to do. Authorization is a separate mechanism (M9-L10 to M9-L13), and the spec says servers SHOULD
  NOT use `clientInfo` for security decisions.
- **Hotels do not run two check-in systems at once.** MCP does, for years: a dual-era server keeps the old
  desk open for legacy clients while modern clients walk straight past it (§7.5).

---

## 5. Detailed technical explanation

### 5.1 The legacy handshake (2024-11-05 to 2025-11-25)

`[VERIFIED 2026-09-15 — MCP 2025-11-25 schema as shipped in mcp-types / mcp 2.2.0]`

```json
→ {"jsonrpc":"2.0","id":1,"method":"initialize",
   "params":{"protocolVersion":"2025-11-25",
             "capabilities":{"elicitation":{}},
             "clientInfo":{"name":"example-client","version":"1.0.0"}}}
← {"jsonrpc":"2.0","id":1,"result":{"protocolVersion":"2025-11-25",
             "capabilities":{"tools":{"listChanged":true}},
             "serverInfo":{"name":"example-server","version":"1.4.0"},
             "instructions":"Optional guidance for the model."}}
→ {"jsonrpc":"2.0","method":"notifications/initialized"}
```

**Version negotiation.** The client sends the latest version it supports. If the server supports it, the
server answers with the same version; otherwise it answers with another version it supports (normally its
latest). If the client does not support the version in the reply, it MUST disconnect.

`[REAL, measured]` §7.1: offering `2025-11-25` or `2025-06-18` to a server supporting both returned the same
version; offering `2024-11-05` returned `2025-11-25`, and a client that only speaks `2024-11-05` must
disconnect. A `tools/list` sent before `initialize`, or after `initialize` but before
`notifications/initialized`, was rejected by the lab's server. The legacy spec says a client SHOULD NOT send
requests (other than pings) before initialization completes; how a server reacts if one arrives anyway is
implementation-defined, which matters in §5.6.

**Legacy capabilities** (abridged): server `tools`, `resources` (`subscribe`, `listChanged`), `prompts`
(`listChanged`), `logging`, `completions`; client `roots` (`listChanged`), `sampling`, `elicitation`.

### 5.2 The flaw: capabilities bound to a connection

`[REAL, measured]` §7.2 opened one connection as client A (declares `elicitation`) and routed a seeded mix of
100 requests from A and from client B (declares nothing) through it. The server consulted the connection's
stored capabilities: **46/100 requests — every one of B's — were judged with the wrong capability set.** A
per-request server judged **0/100** wrongly.

In practice "judged wrongly" means the server sends B a confirmation form B cannot render, and the call hangs
or fails; or, in the opposite arrangement, it silently skips a confirmation step A could have shown. Neither
side's code has a bug in isolation. The bug is the assumption that a connection has one owner.

The 2026-07-28 specification states the replacement principle directly: **servers MUST NOT rely on prior
requests over the same connection to establish context**, and an open connection — a stdio process included —
is not a conversation or session.

### 5.3 The modern request: `_meta` on every call

`[VERIFIED 2026-09-15 — MCP specification 2026-07-28, Base Protocol §_meta and Versioning]`

```json
{"jsonrpc":"2.0","id":7,"method":"tools/call",
 "params":{"name":"delete_report","arguments":{"report_id":"r1"},
   "_meta":{
     "io.modelcontextprotocol/protocolVersion":"2026-07-28",
     "io.modelcontextprotocol/clientCapabilities":{"elicitation":{"form":{}}},
     "io.modelcontextprotocol/clientInfo":{"name":"example-client","version":"1.0.0"}}}}
```

| `_meta` key | Required | Meaning |
|---|---|---|
| `io.modelcontextprotocol/protocolVersion` | **Yes** | Version for *this* request |
| `io.modelcontextprotocol/clientCapabilities` | **Yes** | Capabilities relevant to *this* request; `{}` means none |
| `io.modelcontextprotocol/clientInfo` | SHOULD | Name and version; self-reported, for display and logs only |
| `io.modelcontextprotocol/logLevel` | No | Opt in to log notifications for this request |

Servers SHOULD return `io.modelcontextprotocol/serverInfo` in each result's `_meta`.

The server's three possible refusals, all of which §7.3 produced:

| Condition | JSON-RPC error | HTTP status (Streamable HTTP) | `data` |
|---|---|---|---|
| Required `_meta` field missing | `-32602` Invalid params | 400 | — |
| Version not supported | `-32022` UnsupportedProtocolVersion | 400 | `{"supported": [...], "requested": "..."}` |
| Needs a capability the client did not declare | `-32021` MissingRequiredClientCapability | 400 | `{"requiredCapabilities": {...}}` |

`[REAL, measured]` §7.3: no `_meta` → `-32602`; version `1900-01-01` → `-32022` listing `["2026-07-28"]`;
`delete_report` called without `elicitation` → `-32021` naming `elicitation`; the same call **with**
`elicitation` → a `resultType: "input_required"` result asking for confirmation (the elicitation round trip is
M9-L06).

**Modern capabilities** add an `extensions` map to both sides (e.g. `io.modelcontextprotocol/tasks`). Client
`roots` and `sampling`, and server `logging`, still exist but are **deprecated** as of 2026-07-28; new
implementations should not adopt them.

### 5.4 `server/discover`

```json
← {"jsonrpc":"2.0","id":"discover-1","result":{
     "resultType":"complete",
     "supportedVersions":["2026-07-28"],
     "capabilities":{"tools":{},"resources":{}},
     "_meta":{"io.modelcontextprotocol/serverInfo":{"name":"ExampleServer","version":"1.0.0"}},
     "instructions":"This server provides weather and resource utilities.",
     "ttlMs":3600000,"cacheScope":"public"}}
```

Servers MUST implement it; clients MAY call it. It is useful to show a server's identity and capabilities in
one round trip, and it is the recommended **era probe on stdio**, where there is no HTTP status to inspect.
The `ttlMs` and `cacheScope` fields let clients cache the answer (M9-L06).

### 5.5 Choosing a version: intersect, don't sort

`[REAL, measured]` §7.4: given a server advertising `["2025-11-25", "2026-07-28", "DRAFT-2026-v2"]`, a client
that picked `max()` chose **`"DRAFT-2026-v2"`**, a version it cannot speak; the same happened with `"next"`.
Picking the newest entry of the **intersection** with the client's own ordered list chose `"2026-07-28"` every
time.

Date-shaped version strings happen to sort correctly today, which is exactly why this bug is tempting. The
official Python SDK's own version registry carries a comment making the same point: versions are an
enumerated set, not an ordered scalar, and unrecognised strings must compare conservatively.

### 5.6 The compatibility matrix and the probe rule

`[REAL, measured]` §7.5 ran every pairing:

| Client ↓ / Server → | Legacy | Modern | Dual-era |
|---|---|---|---|
| **Legacy** | works | **fails** — `initialize` rejected | works (legacy) |
| **Modern** | **fails** — probe identifies a legacy server | works | works (modern) |
| **Dual-era** | works (falls back to legacy) | works | works (modern) |

This matches the matrix in the 2026-07-28 versioning page. The two failures are unavoidable: legacy clients
have no way to move forward, and a modern-only client has no handshake to fall back to. A modern-only client
still SHOULD probe, because some legacy servers do not check that `initialize` came first and would process an
era-ambiguous call such as `tools/call` under legacy rules; the probe turns that into a clear, early failure.

**The fallback rule.** On stdio, a dual-era client that receives:

- a `DiscoverResult` → modern; pick a mutual version;
- a **recognised modern error** (e.g. `-32022`) → modern; retry with a version from `data.supported`; **do not**
  fall back;
- **any other error, or no reply within a timeout** → legacy; fall back to `initialize`.

The spec says the fallback **MUST NOT be keyed to one specific error code**, because legacy servers answer
unknown pre-initialize methods with implementation-defined errors (commonly `-32601` or `-32602`) or not at
all. `[REAL, measured]` §7.5b: a client that fell back only on `-32601` connected to **1/3** legacy-server
variants; the spec rule connected to **3/3**.

On Streamable HTTP the same decision is made by sending a modern request and inspecting a `400` response body:
a recognised modern JSON-RPC error means modern; an empty or unrecognised body means legacy (M9-L08).

### 5.7 Assumptions and limitations

- The lab's servers, clients and "silent" server run in one process; a real silent server costs a real timeout,
  so pick a short probe timeout and cache the era per server process (stdio) or origin (HTTP), as the spec
  recommends.
- Only `elicitation` is exercised as a client capability. Extensions negotiate the same way via the
  `extensions` map, and a party that sees an unsupported extension must fall back to core behaviour or reject.
- Section 5's version facts are as of revision 2026-07-28 and the `mcp` 2.2.0 SDK. A future revision may add
  versions; the selection rule in §5.5 is designed to survive that.

---

## 6. Worked example — the gateway that asked the wrong users to confirm

**The situation.** A company ran an internal "MCP gateway": one service that held long-lived connections to a
dozen legacy-era MCP servers and forwarded requests from many desktop and web clients through them. The
document-management server's `archive_folder` tool asked the user to confirm through elicitation *if the client
supported it*, and otherwise refused, with a message telling the user to use the desktop app.

**Symptoms.** Web users — whose client did not support elicitation — reported that archiving sometimes
"spins forever". Desktop users reported that archiving occasionally happened **with no confirmation dialog**.

**Diagnosis.**

1. Both symptoms appeared only after the gateway was introduced; direct connections behaved correctly.
2. The gateway opened each upstream connection lazily, using the **capabilities of whichever end-user client
   happened to trigger it** for the `initialize` request.
3. When a desktop client opened the connection, web users' requests inherited `elicitation` — the server sent
   them a confirmation form their client could not display, and the request hung (the "spins forever"
   reports). When a web client opened it, desktop users' requests inherited *no* elicitation — and a bug in
   the server's fallback path archived without confirming.

This is §7.2's measurement in production: every request from the minority client type was judged with the
majority type's capabilities, or the reverse, depending on who connected first.

| # | Finding | Mechanism | Fix |
|---|---|---|---|
| 1 | Capabilities judged per connection, not per caller | Legacy handshake state on a pooled connection (§5.2) | Short term: separate upstream connection pools per client capability profile |
| 2 | Silent archive with no confirmation | Server's "no elicitation" path did not refuse as designed | Test both capability paths explicitly |
| 3 | Gateway could not express per-request capabilities to legacy servers | The legacy protocol has no field for it | Long term: upgrade servers to 2026-07-28, forward each caller's own `clientCapabilities` in `_meta` |

**The general rule.** **Anything that multiplexes callers over one connection must not rely on facts negotiated
once for that connection.** In the modern protocol that rule is built in; for legacy servers behind a gateway,
you must enforce it yourself by partitioning connections.

---

## 7. Practical activity

**File:** [`labs/m9/l05_initialization_capability_negotiation.py`](../../labs/m9/l05_initialization_capability_negotiation.py)

**No API key, no network, no third-party dependencies.**

```bash
source .venv/bin/activate
python labs/m9/l05_initialization_capability_negotiation.py
```

### 7.2 Expected output

`[EXECUTED]` — 2026-09-15, Python 3.12.3 (pure standard library). Run twice; output identical.

```text

============================================================================
1. LEGACY: THE INITIALIZE HANDSHAKE AND ITS COUNTER-OFFER RULE
============================================================================
  client offers 2025-11-25 -> server answers 2025-11-25  => proceed
  client offers 2025-06-18 -> server answers 2025-06-18  => proceed
  client offers 2024-11-05 -> server answers 2025-11-25  => client MUST disconnect

  tools/list sent BEFORE initialize -> {'code': -32601, 'message': 'Server not initialized'}
  tools/list after initialize, before initialized -> {'code': -32601, 'message': 'Server not initialized'}
  tools/list after notifications/initialized       -> 1 tool(s)

  Three messages, in order, before any real work -- and every fact they
  establish (version, capabilities) is stored on THIS connection.

============================================================================
2. WHY STATE ON A CONNECTION BREAKS: A POOLED CONNECTION
============================================================================
  A gateway shares ONE server connection between client A (supports
  elicitation) and client B (does not). A initialized the connection.
  100 requests: 54 from A, 46 from B.
    connection-scoped capabilities: 46/100 requests judged with the WRONG capability set
    per-request capabilities      :  0/100

  Every one of B's requests inherited A's capabilities. 2026-07-28 removed
  the handshake for exactly this reason: an open connection is not a
  session, and a server MUST NOT infer capabilities from prior requests.

============================================================================
3. MODERN: EVERY REQUEST IS VALIDATED ON ITS OWN
============================================================================
  no _meta at all          -> error -32602: Invalid params: missing ['io.modelcontextprotocol/protocolVersion', 'io.modelcontextprotocol/clientCapabilities']
  unknown version          -> error -32022: data={'supported': ['2026-07-28'], 'requested': '1900-01-01'}
  valid tools/list         -> result: complete, 1 tool(s)
  call, no elicitation     -> error -32021: data={'requiredCapabilities': {'elicitation': {}}}
  call, with elicitation   -> result: input_required, asks: ['confirm']

============================================================================
4. VERSION SELECTION: max() OF VERSION STRINGS IS A BUG
============================================================================
  server supports ['2025-11-25', '2026-07-28']
    naive max(): '2026-07-28'       intersection-then-newest-known: '2026-07-28'
  server supports ['2025-11-25', '2026-07-28', 'DRAFT-2026-v2']
    naive max(): 'DRAFT-2026-v2'    intersection-then-newest-known: '2026-07-28'   <- naive pick is a version the client cannot speak
  server supports ['2026-07-28', 'next']
    naive max(): 'next'             intersection-then-newest-known: '2026-07-28'   <- naive pick is a version the client cannot speak

  Versions are an enumerated set, not an ordered scalar: 'DRAFT...' and
  'next' sort above every date. Pick from the INTERSECTION with the
  versions the client actually implements, ordered by the client's list.

============================================================================
5. THE 3x3 ERA COMPATIBILITY MATRIX, RUN FOR REAL
============================================================================
  legacy client    x legacy server    -> works (legacy 2025-11-25, 1 tool)
  legacy client    x modern server    -> FAILS (initialize rejected)
  legacy client    x dual-era server  -> works (legacy 2025-11-25, 1 tool)
  modern client    x legacy server    -> FAILS (probe says legacy server)
  modern client    x modern server    -> works (modern 2026-07-28, 1 tool)
  modern client    x dual-era server  -> works (modern 2026-07-28, 1 tool)
  dual-era client  x legacy server    -> works (legacy 2025-11-25, 1 tool)
  dual-era client  x modern server    -> works (modern 2026-07-28, 1 tool)
  dual-era client  x dual-era server  -> works (modern 2026-07-28, 1 tool)

  Fallback rule check against three kinds of legacy server:
    keyed on -32601 only              : connected to 1/3 legacy servers  [True, False, False]
    spec rule (anything not modern)   : connected to 3/3 legacy servers  [True, True, True]

============================================================================
6. WHAT THIS LAB IS AND IS NOT
============================================================================
  REAL: every negotiation outcome, error code and matrix cell above is the
  result of running these server and client implementations against each
  other. Section 2's 100 requests use a seeded random mix.

  ILLUSTRATIVE: servers and clients run in one process with no transport;
  a 'silent' legacy server is modelled as an immediate TIMEOUT value rather
  than a real wait.

  NOT SHOWN: HTTP-specific era detection (inspecting a 400 body, M9-L08),
  extension negotiation beyond the empty 'extensions' map, and the full
  elicitation round trip that section 3's input_required result begins (M9-L06).

Done.
```

### 7.3 Reading the result

**Section 2 is the reason the protocol changed.** 46 wrong out of 100 is not a tuning problem; it is exactly
the share of requests that did not come from the client that opened the connection.

**Section 4 is small and easy to get wrong in any language.** Sorting version strings works on today's data
and fails on the first non-date string.

**Section 5b is the most transferable result.** "Fall back on this specific error code" is a natural way to
write compatibility code, and it quietly fails against servers that answer differently or not at all.

---

## 8. Common mistakes and troubleshooting

1. **Caching client capabilities per connection on a modern server.** §5.2 — MUST NOT; read `_meta` every time.
2. **Omitting `clientCapabilities` because the client "has none".** §5.3 — the field is required; send `{}`.
3. **Picking a version with `max()` or string comparison.** §5.5 — intersect with your own list.
4. **Falling back to `initialize` on one specific error code.** §5.6 — fall back on anything that is not a
   recognised modern error, and on timeout.
5. **Falling back to `initialize` after `-32022`.** §5.6 — that server is modern; retry with a supported version.
6. **Using `clientInfo` to grant or deny features.** §4, §5.3 — it is self-reported and not verified.
7. **Adopting deprecated capabilities (`sampling`, `roots`, `logging`) in new code.** §5.3.

| Symptom | Likely cause | Fix |
|---|---|---|
| Every request fails with `-32602` on a new server | Missing `protocolVersion` or `clientCapabilities` in `_meta` | Add both to every request |
| `-32022` with `data.supported` listed | Client prefers a version the server does not implement | Choose from the intersection (§5.5) |
| `-32021` on one tool only | That tool needs a capability, e.g. `elicitation`, the client did not declare | Declare it if supported; otherwise surface the error |
| Client hangs connecting to an old server | Waiting for a probe reply that never comes | Short probe timeout, then fall back (§5.6) |
| Behaviour differs depending on which user connected first | Connection-scoped state behind a gateway (§6) | Per-request capabilities, or partition connections |

---

## 9. Security, privacy, reliability, cost

- **Security.** Capabilities and `clientInfo` are self-reported. Never treat "client declares X" as "caller is
  authorised to do X" (M9-L10).
- **Reliability.** Stateless requests can be retried against any server instance and survive process restarts,
  because nothing depends on a handshake having happened on this connection.
- **Reliability.** A probe with no timeout turns every legacy server into a hang. Bound it, and cache the result
  per server process or origin.
- **Cost.** Modern requests carry a few hundred extra bytes of `_meta` each; the saving is the removed round trips
  and the ability to load-balance freely. `server/discover` responses are cacheable via `ttlMs`.

---

## 10. Exercises

### Exercise 1 — Beginner (~20 min)

1. Write the three legacy handshake messages for a client offering `2025-06-18` with `elicitation`.
2. Name the two required `_meta` keys on every modern request.
3. What should a dual-era client do when its probe receives `-32022`? When it receives `-32601`? When it receives
   nothing?
4. Why did §7.2 measure 46 wrong decisions, and not some other number?
5. Which three client/server capabilities are deprecated in 2026-07-28?

### Exercise 2 — Intermediate (~40 min)

1. Run the lab. Change the 0.6 in section 2 to 0.9 and to 0.1. Predict the wrong-decision count before running.
2. Add a `resources` capability to `ModernServer`'s discover result and a `resources/list` handler; confirm the
   dual-era client can call it.
3. Make `DualEraServer` answer a legacy `initialize` offering `2024-11-05` and check the counter-offer.
4. Write `choose_version(client_ordered, server_supported)` and test it with at least five server lists,
   including an empty intersection.
5. Add a fourth legacy-server variant that answers `server/discover` with a *result* of `{}`. What should a
   dual-era client conclude, and does the lab's probe handle it?

### Exercise 3 — Challenge (~50 min)

1. Implement §6's short-term fix: a gateway that keeps one upstream legacy connection per distinct capability
   profile. Re-run section 2 through it and show 0 wrong decisions.
2. Design a cache for the era probe result with an invalidation rule that handles a server upgraded from legacy
   to modern between runs.
3. Argue whether a modern server should ever return `-32021` rather than degrading gracefully (for example,
   skipping confirmation). Use a destructive and a read-only tool as your examples.
4. Using the official `mcp` 2.2.0 SDK, find where the client implements the probe and state which of §5.6's
   three outcomes it handles and how.
5. Write a checklist for migrating a legacy server to dual-era without breaking existing clients.

---

## 11. Quiz

*(Answers: [`answer-keys/module-09-answers.md`](../../answer-keys/module-09-answers.md#m9-l05).)*

**Q1.** In the legacy handshake, which message completes initialization?

- A. The server's `initialize` result
- B. The client's `notifications/initialized` notification
- C. The server's first `tools/list` result
- D. A `ping` request from the client

**Q2.** A legacy server supporting only `2025-06-18` and `2025-11-25` receives `initialize` offering
`2024-11-05`. What does it reply?

- A. An error with code `-32022`
- B. `2024-11-05`, since clients choose
- C. No reply until the client retries
- D. A version it supports, such as `2025-11-25`

**Q3.** In §7.2, why were 46 of 100 decisions wrong on the pooled connection?

- A. Every request from client B inherited client A's capabilities
- B. The seeded random generator produced invalid requests
- C. The server rejected half of all requests as malformed
- D. Client A's elicitation requests timed out

**Q4.** Which `_meta` keys are required on every 2026-07-28 request?

- A. `clientInfo` and `logLevel`
- B. `serverInfo` and `protocolVersion`
- C. `protocolVersion` and `clientCapabilities`
- D. `clientCapabilities` and `traceparent`

**Q5.** A modern server needs elicitation to process a call, but the request's capabilities omit it. What
must it return?

- A. `-32602` Invalid params
- B. A result with `isError: true`
- C. `-32021` MissingRequiredClientCapability
- D. `-32022` UnsupportedProtocolVersion

**Q6.** Why did §7.4's naive client choose `"DRAFT-2026-v2"`?

- A. It sorts above every date string
- B. The server listed it first
- C. It was the only version both sides shared
- D. The client preferred draft versions

**Q7.** A dual-era client's stdio probe receives `-32022` listing supported versions. What should it do?

- A. Fall back to `initialize`
- B. Close the connection permanently
- C. Resend the probe with no `_meta`
- D. Retry with a version from the supported list

**Q8.** Why must the fallback not be keyed to a single error code?

- A. Error codes are random in legacy servers
- B. Legacy servers reply with differing errors or none at all
- C. Modern servers never return errors to probes
- D. JSON-RPC forbids comparing error codes

**Q9.** What happens when a legacy-only client connects to a modern-only server?

- A. It fails; the server rejects `initialize`
- B. It works after one retry
- C. The server downgrades itself to legacy
- D. It works but without capabilities

**Q10.** What may a server use `clientInfo` for?

- A. Granting admin-only tools
- B. Choosing the protocol version
- C. Display, logging and debugging
- D. Enforcing per-tenant rate limits

**Q11.** Why should even a modern-only client probe with `server/discover` on stdio?

- A. The spec requires it before every call
- B. Some legacy servers would run `tools/call` without `initialize`
- C. It is the only way to list tools
- D. It lets the server store the client's capabilities

**Q12.** In §6, what was the long-term fix?

- A. Disable elicitation for all clients
- B. Increase the gateway's connection timeout
- C. Move all users to the desktop app
- D. Upgrade servers and forward each caller's capabilities

**Q13.** *(Written, rubric-graded.)* In under 150 words: your team maintains a Python MCP client used against
both old and new servers over stdio. Describe how it should decide which protocol era to use and what it should
do in each case, and name one bug the naive approach would have.

---

## 12. Revision notes

- **Legacy (≤ 2025-11-25):** `initialize` → result (server may counter-offer the version) →
  `notifications/initialized`. Agreement lives on the connection.
- **Why it changed:** connection-scoped capabilities misjudge shared connections — **46/100** measured, i.e.
  every request not from the connection's opener.
- **Modern (2026-07-28):** every request carries `protocolVersion` + `clientCapabilities` in `_meta`; servers
  MUST NOT infer them from earlier requests. Refusals: `-32602` missing field, `-32022` unsupported version
  (`data.supported`), `-32021` missing capability (`data.requiredCapabilities`).
- **`server/discover`:** mandatory for servers, optional for clients, the stdio era probe, cacheable.
- **Version choice:** intersect with the client's ordered list; never `max()` of strings.
- **Probe rule:** result or recognised modern error → modern; anything else or timeout → legacy. Not keyed to one
  code (measured **1/3 vs 3/3**).

---

## 13. Completion checklist

- [ ] I can write the legacy handshake and apply its counter-offer rule.
- [ ] I can explain §7.2's 46/100 result and why it motivated statelessness.
- [ ] I can build a valid modern request and predict `-32602`, `-32021` and `-32022`.
- [ ] I can choose a version safely from an advertised list.
- [ ] I can implement the dual-era probe and its fallback rule.
- [ ] I scored at least 10/13 on the quiz.

---

## 14. References

- MCP specification 2026-07-28, *Versioning and Compatibility* (era model, compatibility matrix, `-32022`) —
  <https://modelcontextprotocol.io/specification/2026-07-28/basic/versioning> `[VERIFIED 2026-09-15]`
- MCP specification 2026-07-28, *Base Protocol* (`_meta` reserved keys, statelessness, `-32021`) —
  <https://modelcontextprotocol.io/specification/2026-07-28/basic> `[VERIFIED 2026-09-15]`
- MCP specification 2026-07-28, *Discovery* (`server/discover`) —
  <https://modelcontextprotocol.io/specification/2026-07-28/server/discover> `[VERIFIED 2026-09-15]`
- MCP specification 2026-07-28, *stdio: Backward Compatibility* (probe outcomes, not keyed to one code) —
  <https://modelcontextprotocol.io/specification/2026-07-28/basic/transports/stdio> `[VERIFIED 2026-09-15]`
- MCP changelog 2026-07-28 (SEP-2575: handshake removal; SEP-2577: deprecations) —
  <https://modelcontextprotocol.io/specification/2026-07-28/changelog> `[VERIFIED 2026-09-15]`
- Legacy handshake and capability shapes: `mcp-types` 2025-11-25 models shipped with the `mcp` 2.2.0 Python SDK
  (`InitializeRequestParams`, `InitializeResult`, `ClientCapabilities`, `ServerCapabilities`) `[VERIFIED 2026-09-15]`

---

## 15. Next lesson

→ [M9-L06 — Discovery and Invocation](M9-L06-discovery-invocation.md) uses the negotiated version to list and
call a server's tools, resources and prompts — including pagination, caching hints, and the `input_required`
round trip §7.3 started.
