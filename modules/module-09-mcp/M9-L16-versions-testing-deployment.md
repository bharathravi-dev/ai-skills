# M9-L16 — Protocol Versions, Compatibility, Server Testing and Deployment

| | |
|---|---|
| **Lesson ID** | M9-L16 |
| **Difficulty** | 3 (Advanced) |
| **Estimated study time** | 2.25 hours |
| **Prerequisites** | [M9-L14](M9-L14-errors-timeouts-cancellation-logging.md), [M2-L20](../module-02-python-foundations/M2-L20-docker.md) |

---

## 1. Learning objectives

1. **Place** any MCP revision on the version timeline, and apply the feature lifecycle and deprecation policy.
2. **Write** a conformance suite that catches the bugs a tolerant client hides, and **fuzz** a server without crashing it.
3. **Use** golden transcripts to turn "the release looks fine" into a diff.
4. **Classify** a change to your own tool definitions as compatible or breaking.
5. **Ship** a server: packaging for stdio, a hardened container, and the extra requirements of an HTTP deployment.

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **Protocol revision** | A dated version of the MCP specification, e.g. `2026-07-28`. |
| **Feature lifecycle** | The Active → Deprecated → Removed states a specification feature moves through. |
| **Deprecation window** | The minimum time a deprecated feature remains available (twelve months). |
| **Extension** | Optional functionality outside the core protocol, negotiated via the `extensions` capability. |
| **Conformance suite** | Tests asserting a server obeys the protocol, independent of its domain logic. |
| **Golden transcript** | A recorded, normalised request/response script compared on every release. |
| **Breaking change** | A change that invalidates a caller written against the previous definition. |

---

## 3. Plain-language explanation

### 3.1 Versions are a list, not a number

MCP revisions are dates, and there are five so far: `2024-11-05`, `2025-03-26`, `2025-06-18`, `2025-11-25`, `2026-07-28`.
The first four negotiate with the `initialize` handshake; the last is stateless with per-request metadata (M9-L05).
Treat the set as an enumeration you support explicitly — never as something to compare with `<` (M9-L05 measured a
client picking `"DRAFT-2026-v2"` because it sorts above every date).

### 3.2 Features now have a published lifecycle

Since 2026-07-28 the specification defines states — Active, Deprecated, Removed — a **minimum twelve-month** deprecation
window, and a registry of deprecated features. That matters for planning: Roots, Sampling and Logging are deprecated,
along with the old HTTP+SSE transport and Dynamic Client Registration. They still work; new code should not adopt them.

### 3.3 Testing a server means testing the protocol, not just the tools

M9-L09 showed an SDK client tolerating three real bugs: a stdout banner, a string-typed id, and a missing
`server/discover` (silently falling back to the legacy era). §7.2 turns those into explicit checks: a **24-check
conformance suite** that the M9-L09 server passes 24/24. §7.3 then throws **300 malformed or hostile frames** at it —
truncated JSON, injected punctuation, a 5,000-character argument, random method names, two messages on one line — and
measures what matters: **nothing invalid came back, the process stayed alive, and it still answered correctly
afterwards**.

### 3.4 Releases need a diff, not an opinion

§7.4 records a **golden transcript** of five calls, then replays it against three mutated releases. Each mutation
showed up as exactly one differing step: a reworded description in `tools/list`, a shortened `ttlMs` in
`resources/read`, an extra field in a `tools/call` result. §7.5 classifies changes to tool definitions: adding an
optional argument or an enum value is compatible; making an argument required, removing an enum value, changing a type,
or dropping an output guarantee is **breaking**.

### 3.5 Shipping

A stdio server is a command a host runs; a container makes its filesystem and network boundary explicit. §7.6 builds the
M9-L09 server into an image and runs the conformance checks through `docker run -i` with **no network, a read-only
filesystem, dropped capabilities and a non-root user** — 8/8 checks.

---

## 4. Analogy

**Type approval for an electrical appliance.** The plug must fit the socket standard of the year it was made, and the
standard publishes when old fittings stop being supported. Before sale the appliance goes through a test rig: not "does
it boil water" but "does it behave under a shorted line, a brown-out, the wrong frequency" — that is the conformance
suite and the fuzzer. Each production batch is compared against the approved sample (the golden transcript). And the
appliance ships in a housing that keeps the user away from the live parts: the container.

### Where the analogy breaks

- **Appliances are approved once; MCP servers publish new tool definitions on every listing.** Compatibility is
  continuous, which is why §7.5's classification runs in CI rather than at a certification lab.
- **A shorted mains line is rare; malformed input is the normal case.** An MCP server is exposed to a model's output and
  possibly the public internet, so fuzzing is a routine test, not an edge case.

---

## 5. Detailed technical explanation

### 5.1 The version timeline

`[VERIFIED 2026-09-16 — `mcp_types.version` registry shipped in `mcp` 2.2.0, and the 2026-07-28 changelog]`

| Revision | Era | Notable for |
|---|---|---|
| `2024-11-05` | legacy | First public revision; HTTP+SSE transport |
| `2025-03-26` | legacy | Streamable HTTP; JSON-RPC batching added; OAuth-based authorization |
| `2025-06-18` | legacy | Batching removed; `MCP-Protocol-Version` header; structured tool output; elicitation |
| `2025-11-25` | legacy | Tasks (experimental), URL-mode elicitation, sampling with tools |
| `2026-07-28` | **modern** | Handshake and sessions removed; per-request `_meta`; `server/discover`; MRTR; `subscriptions/listen`; caching hints; error-code partition |

The SDK's own registry keeps these as an ordered tuple with helper functions, and its source note is worth repeating:
"versions are an enumerated set, not an ordered scalar… unrecognized peer strings must compare conservatively".

### 5.2 Feature lifecycle and what is deprecated

`[VERIFIED 2026-09-15 — MCP changelog 2026-07-28 and the feature lifecycle policy]`

- States: **Active**, **Deprecated** (works, documented in a registry, do not adopt), **Removed**.
- Minimum **twelve-month** deprecation window before removal.
- Currently deprecated: **Roots**, **Sampling**, **Logging** (SEP-2577); the **HTTP+SSE** transport; **Dynamic Client
  Registration** in favour of Client ID Metadata Documents; `includeContext` values `"thisServer"` / `"allServers"`.
- Suggested replacements: pass directories or files as tool parameters or resource URIs instead of Roots; call an LLM
  provider directly instead of Sampling; log to stderr or use OpenTelemetry instead of Logging.

**Extensions** are the growth path for the rest: optional, opt-in, negotiated through the `extensions` capability map
(for example `io.modelcontextprotocol/tasks` for long-running work). A party that does not support an extension reverts
to core behaviour or rejects the request.

### 5.3 A conformance suite

`[REAL, measured]` §7.2: **24/24** checks against the M9-L09 server, covering discovery and version handling, listing
shape and determinism, tool-name rules, result shape (`resultType`, caching hints, `serverInfo`, `structuredContent`),
both error channels, **id echo including its JSON type**, `_meta` validation, notifications getting no reply, **stdout
cleanliness**, stderr logging, and a clean exit on EOF.

Three of those exist specifically because an SDK client tolerated the corresponding bug (M9-L09 §5.7): stdout purity, id
typing, and `server/discover`. Add one more assertion that no suite can infer for you: **the negotiated protocol version
is the one you intend**, so a silent fallback to a legacy era fails the build.

Run the suite in CI against every supported era, and — where a second implementation exists — against another SDK's
client too (M9-L09).

### 5.4 Fuzzing

`[REAL, measured]` §7.3: 300 mutated frames produced **274 replies, 0 invalid JSON, 0 malformed envelopes**, left the
process **alive**, and the connection still worked. Not every frame deserves a reply — a notification gets none, and an
unreadable fragment may be dropped — so the assertions are about **invalid output and survival**, not reply counts.

Useful mutations: truncation, punctuation injection, oversized values, random method names, wrong parameter names, two
messages on one line, deeply nested JSON, and (for HTTP) header/body mismatches (M9-L08). Add a schema-directed fuzzer
for tool arguments — a tool's own `inputSchema` tells you what to violate (M9-L07).

### 5.5 Golden transcripts

`[REAL, measured]` §7.4: three mutated releases each produced exactly one differing step; the unmodified control produced
none.

Rules that keep them useful:

- **Normalise volatile fields** — `_meta`, timestamps, generated ids — or every run is a false alarm.
- **Keep them small and legible**; a diff a reviewer cannot read gets approved blindly.
- **Store them next to the code**, so a deliberate change updates the golden file in the same commit as the code change.
- Complement, don't replace, assertions: a transcript tells you *something* changed, the conformance suite tells you it
  is *wrong*.

### 5.6 Versioning your own tools

`[REAL, measured]` §7.5 classified six candidate releases:

| Change | Verdict |
|---|---|
| Add an optional argument | compatible |
| Add an enum value | compatible |
| Make an existing argument required | **breaking** |
| Remove an enum value | **breaking** |
| Change an argument's type | **breaking** |
| Stop guaranteeing an output field | **breaking** |

Your callers are models and hosts that **cache** definitions (M9-L06) and may have **approved** them (M9-L15). So:

- ship breaking changes as a **new tool name** (`search_courses_v2`) or a clearly versioned server, and keep the old tool
  for a stated period;
- prefer additive changes, with `additionalProperties: false` preserved;
- use `listChanged` plus short `ttlMs` around a change so caches refresh promptly;
- record the change in a changelog the host can show a user re-approving.

### 5.7 Deployment: stdio

- **Package it as a command.** A console entry point (`pyproject.toml` `[project.scripts]`) installable with `pipx` or
  runnable with `uvx` beats "python /some/absolute/path.py" in a user's configuration `[UNVERIFIED — tool-specific]`.
- **Absolute paths and an explicit interpreter** in host configuration; the host's working directory is not yours.
- **Pass only the environment the server needs** (M9-L12): the official SDK's default allowlist is `HOME`, `LOGNAME`,
  `PATH`, `SHELL`, `TERM`, `USER` plus what you name.
- **stdout is the transport.** Ban prints; route logging and any dependency's banner to stderr (M9-L08).
- **Exit on EOF**, and expect SIGTERM then SIGKILL after a grace period (the SDK allows 2 s, then 2 s more).
- **Pin your dependencies**, including the MCP SDK's major version — `mcp` 2.x renamed `FastMCP` to `MCPServer`
  (M9-L09).

`[REAL, measured]` §7.6 built the M9-L09 server into a container and ran conformance checks through
`docker run -i --rm --network none --read-only --cap-drop ALL --memory 256m`: **8/8 passed**, with logs on stderr and a
clean exit. A container is a boundary, not an authorization mechanism — the credentials you pass in still decide reach.

### 5.8 Deployment: Streamable HTTP

Everything from M9-L08 and the authorization lessons becomes operational work:

| Concern | Requirement |
|---|---|
| Transport | One POST endpoint; JSON or SSE; `202` for notifications; `405` for legacy GET/DELETE |
| Security | TLS; `Origin` validation; bind loopback when local; header/body consistency (`-32020`) |
| Authorization | Protected Resource Metadata; token audience validation; scope challenges (M9-L11) |
| Scaling | Statelessness means any instance can serve any request — no sticky sessions; a broken stream simply loses one request |
| Limits | Per-principal rate limits, request size caps, tool timeouts (M9-L14) |
| Observability | Structured logs with request ids, trace context from `_meta`, metrics per tool: calls, errors by channel, duration percentiles |
| Health | A non-MCP health endpoint for your platform, separate from the MCP endpoint |
| Release | Canary or blue/green, with the conformance suite run against the new version before traffic moves (M13-L14) |

### 5.9 A release checklist

1. Conformance suite passes, in every era you claim to support.
2. Interop check against at least one independent client (M9-L09).
3. Fuzz run: no crashes, no invalid output.
4. Golden transcripts reviewed; any diff is intentional.
5. Tool-definition diff classified; breaking changes renamed or versioned, changelog written.
6. Authorization tests: the caller × operation × object matrix (M9-L10), including denials.
7. Secrets: none in code, logs or images; least-privilege credentials (M9-L12).
8. Operational: timeouts, limits, health checks, dashboards, rollback plan.
9. Documentation: what the server does, what each tool costs and changes, and how to report a problem.

### 5.10 Assumptions and limitations

- Version facts are correct as of 2026-09-16; revisions are added over time, and the deprecation registry is the place to
  check what has since been removed.
- 300 fuzz frames is a smoke test. Real campaigns run continuously with coverage feedback.
- §7.6's container demonstrates isolation flags on one machine; production adds image scanning, signing and a registry.
- Public listing (the MCP registry and host marketplaces) is out of scope and changes fast `[UNVERIFIED]`.

---

## 6. Worked example — the server that broke every host on the same afternoon

**The situation.** A team maintained a popular internal MCP server. A routine release tightened validation: `level`,
previously optional on `search_courses`, became required, and two enum values were renamed (`intermediate` → `mid`).
Tests passed — they were written against the new schema. Within an hour, assistants across the company were failing on
course searches.

**What happened, mapped to this lesson.**

1. **Both changes were breaking** by §7.5's classification: an argument became required, and enum values disappeared.
2. **Hosts had cached the old definitions** (`ttlMs` 300,000, M9-L06), so for up to five minutes models were still being
   offered the *old* schema and sending `level: "intermediate"` — which the new server rejected.
3. The rejection arrived as a **protocol error**, so models could not self-correct (M9-L14) and simply retried.
4. Hosts that had **pinned definitions** (M9-L15) showed users a re-approval prompt instead — noisy, but safe.

| # | Defect | Fix |
|---|---|---|
| 1 | Breaking change shipped silently | CI check comparing tool definitions across releases; breaking → new tool name |
| 2 | No transition period | Keep `search_courses` accepting both enum sets for a deprecation window; add `search_courses_v2` |
| 3 | Validation failure as a protocol error | `isError` result naming the accepted values (M9-L14) |
| 4 | Cache and change notification not considered | Shorten `ttlMs` before a change; emit `listChanged` at rollout |

**The general rule.** **Your tool definitions are a public API whose clients cache and approve them.** Treat a schema
edit with the same care as changing an HTTP endpoint's contract.

---

## 7. Practical activity

**Files:** [`labs/m9/l16_conformance_and_release.py`](../../labs/m9/l16_conformance_and_release.py) and
[`labs/m9/l16_container_check.py`](../../labs/m9/l16_container_check.py) (needs Docker; skips cleanly without it),
against the server from M9-L09 and its [`Dockerfile`](../../labs/m9/l09_catalog_server/Dockerfile).

```bash
source .venv/bin/activate
python labs/m9/l16_conformance_and_release.py     # about 11 seconds
python labs/m9/l16_container_check.py             # builds and removes a container image
```

### 7.2 Expected output — conformance, fuzzing, transcripts, compatibility

`[EXECUTED]` — 2026-09-16, Python 3.12.3 (pure standard library). Run twice; output identical.

```text

============================================================================
1. CONFORMANCE SUITE
============================================================================
  [PASS] server/discover implemented                          ['2026-07-28']
  [PASS] discover advertises a version we speak               
  [PASS] discover carries caching hints                       
  [PASS] results carry resultType 'complete'                  
  [PASS] results identify the server                          
  [PASS] tools/list returns an array                          2 tools
  [PASS] tool list is deterministically ordered               
  [PASS] every tool has an object inputSchema                 
  [PASS] tool names match the allowed character set           
  [PASS] tools/list is stable across calls                    
  [PASS] tool result has content and structuredContent        
  [PASS] structured result matches outputSchema shape         
  [PASS] text content mirrors the structured result           
  [PASS] bad arguments -> isError result, not a protocol error Invalid arguments: missing required argument 'qu
  [PASS] unknown tool -> protocol error -32602                
  [PASS] id echoed unchanged and typed (str)                  
  [PASS] id echoed unchanged and typed (int)                  
  [PASS] no _meta -> -32602                                   
  [PASS] unknown version -> -32022 listing supported versions 
  [PASS] unknown method -> -32601                             
  [PASS] notification gets no reply                           
  [PASS] all stdout was JSON-RPC                              
  [PASS] logs went to stderr                                  2 line(s)
  [PASS] exits 0 when stdin closes                            

  24/24 conformance checks passed

============================================================================
2. FUZZING: 300 MALFORMED OR HOSTILE FRAMES
============================================================================
  frames sent                         : 300
  replies received                    : 274
  replies that were not valid JSON    : 0
  replies with a malformed envelope   : 0
  server still alive at the end       : True
  still answering correctly afterwards: True

  Not every frame deserves a reply -- notifications and unreadable junk do not.
  What matters is that nothing crashed the process, nothing produced invalid
  output, and the connection still worked afterwards.

============================================================================
3. GOLDEN TRANSCRIPT: DETECTING A REGRESSION IN A RELEASE
============================================================================
  description reworded               differing steps: 1  (tools/list)
  ttlMs shortened                    differing steps: 1  (resources/read)
  extra field in structured output   differing steps: 1  (tools/call)
  no change (control)                differing steps: 0  (none)

  A golden transcript turns 'the release looks fine' into a diff. Normalise
  volatile fields (_meta, timestamps, ids) or every run is a false alarm.

============================================================================
4. BREAKING-CHANGE DETECTOR FOR TOOL DEFINITIONS
============================================================================
  add an optional argument       -> COMPATIBLE
  add an enum value              -> COMPATIBLE
  make 'level' required          -> BREAKING: argument became required: level
  drop an enum value             -> BREAKING: enum values removed from level: ['intermediate']
  query becomes an array         -> BREAKING: type changed: query
  stop guaranteeing 'results'    -> BREAKING: output field no longer guaranteed: results

  Callers here are models and their hosts, and they cache tool definitions
  (M9-L06). Breaking changes need a new tool name or a version bump the host
  can see -- not a silent edit.

============================================================================
5. WHAT THIS LAB IS AND IS NOT
============================================================================
  REAL: a real subprocess under a real conformance suite and fuzzer; the
  transcripts, diffs and compatibility verdicts are computed by this code.

  ILLUSTRATIVE: 300 frames is a smoke test, not a fuzzing campaign; the
  breaking-change rules cover common cases, not all of JSON Schema.

  NOT SHOWN: HTTP deployment, load and soak testing, multi-SDK interop
  (M9-L09 does one SDK), and registry publication.

Done.
```

### 7.3 Expected output — the container check

`[EXECUTED]` — 2026-09-16, Docker 29.2.1, image `python:3.12-slim`.

```text

============================================================================
A STDIO MCP SERVER IN A CONTAINER
============================================================================
  built mcp-catalog:lab from m9/l09_catalog_server/Dockerfile
  [PASS] container answered every request             3/3
  [PASS] stdout carried only JSON-RPC                 3 line(s)
  [PASS] ids echoed in order                          [1, 2, 3]
  [PASS] discover advertises the modern version       
  [PASS] tools listed                                 2 tools
  [PASS] tool call returned structured content        
  [PASS] server logs reached stderr, not stdout       2 line(s)
  [PASS] exited cleanly when stdin closed             exit 0

  8/8 checks passed with --network none, --read-only,
  --cap-drop ALL and a 256 MB limit, running as a non-root user.
  image removed.

  A container gives a local server a filesystem and network boundary the host
  can state explicitly. It does not authorise anything: the credentials you pass
  in still decide what the server may reach (M9-L12).

Done.
```

### 7.4 Reading the result

**The conformance suite is the deliverable, not the 24/24.** Copy it to your own server and watch which checks fail.

**The fuzz section asserts the right things**: survival and output validity, not a reply for every frame.

**The golden transcript's value is the "differing steps" column.** One line tells a reviewer where to look.

---

## 8. Common mistakes and troubleshooting

1. **Comparing version strings with `<` or `max()`.** §5.1.
2. **Adopting deprecated features in new code** (Roots, Sampling, Logging, HTTP+SSE, DCR). §5.2.
3. **Testing only the happy path of your own tools.** §5.3 — the protocol layer is where interop breaks.
4. **Asserting a reply for every fuzz frame.** §5.4.
5. **Golden transcripts with unnormalised `_meta` or timestamps.** §5.5.
6. **Shipping breaking schema changes under the same tool name.** §5.6, §6.
7. **Printing to stdout, or shipping without pinning the SDK major version.** §5.7.
8. **Assuming a container authorises anything.** §5.7.

| Symptom | Likely cause | Fix |
|---|---|---|
| Works with one host, fails with another | Untested tolerance (ids, stdout, discover) | Run the conformance suite plus an interop check |
| Server dies on strange input | No fuzzing; one bad request kills the loop | Catch per-request exceptions (M9-L09); fuzz in CI |
| Every release produces transcript diffs | Volatile fields not normalised | Strip `_meta`, ids, timestamps |
| Clients break minutes after a deploy | Breaking change plus cached definitions | Rename or version; shorten TTL; emit `listChanged` |
| Host shows the server on an old protocol version | `server/discover` failing, silent legacy fallback | Assert the negotiated version in CI |
| Container works locally, fails in the host | Stdout buffering or wrong entrypoint | `python -u`; `docker run -i`; logs to stderr |

---

## 9. Security, privacy, reliability, cost

- **Security.** Fuzzing finds crashes and information leaks in error paths; containers bound filesystem and network reach;
  releases change what users approved (M9-L15), so diffs matter.
- **Privacy.** Golden transcripts and fuzz corpora are test data — never record real user data into them.
- **Reliability.** Statelessness makes horizontal scaling and restarts safe; conformance in CI keeps compatibility from
  drifting.
- **Cost.** A breaking change costs every connected host a burst of failed calls and retries (§6); an image rebuilt and
  scanned per release costs minutes.

---

## 10. Exercises

### Exercise 1 — Beginner (~25 min)

1. List the five MCP revisions and say which era each belongs to.
2. Name three deprecated features and their suggested replacements.
3. Which three conformance checks exist because an SDK client tolerated the bug?
4. Why is "every fuzz frame gets a reply" the wrong assertion?
5. Classify: adding an optional argument; removing an enum value; renaming a tool.

### Exercise 2 — Intermediate (~45 min)

1. Run both labs. Add a conformance check asserting the negotiated version is 2026-07-28 and make it fail by removing
   `server/discover`.
2. Add three new mutation kinds to the fuzzer, including one that sends 1 MB in a single frame. What happens?
3. Extend the golden transcript with an error case and a paginated listing.
4. Extend `compare()` to handle `minimum`/`maximum` tightening and `additionalProperties` flipping to `true`.
5. Add a `HEALTHCHECK` to the Dockerfile that exercises `server/discover` over stdio. Is that sensible for a stdio server?

### Exercise 3 — Challenge (~60 min)

1. Wire both labs into a GitHub Actions workflow that runs on every push, across Python 3.11–3.13, and fails on any
   conformance or breaking-change finding.
2. Write a schema-directed fuzzer that reads each tool's `inputSchema` and generates violating arguments automatically.
3. Build a dual-era test: run your server against a modern client and a legacy client in the same CI job and assert both
   negotiate correctly (M9-L05).
4. Design the deprecation plan for renaming `search_courses` to `find_courses`: timeline, what both tools return during
   the window, and what users see.
5. Take the M9-L09 server to an HTTP deployment: add the transport (M9-L08), token validation (M9-L10), and the
   operational items in §5.8, then run the conformance suite over HTTP.

---

## 11. Quiz

*(Answers: [`answer-keys/module-09-answers.md`](../../answer-keys/module-09-answers.md#m9-l16).)*

**Q1.** How many MCP protocol revisions exist as of September 2026, and which is modern?

- A. Four, with `2025-11-25` modern
- B. Five, with `2026-07-28` modern
- C. Three, with `2025-06-18` modern
- D. Five, with all of them modern

**Q2.** What is the minimum deprecation window in the feature lifecycle policy?

- A. Three months
- B. Six months
- C. Twelve months
- D. Until the next revision

**Q3.** Which feature is deprecated as of 2026-07-28?

- A. Sampling
- B. Tools
- C. Resources
- D. Elicitation

**Q4.** Why should version strings never be compared with `max()`?

- A. Dates sort incorrectly in JSON
- B. Servers may advertise them in random order
- C. The newest version is always listed first
- D. Versions are an enumerated set, not an ordered scalar

**Q5.** In §7.2, how many conformance checks did the M9-L09 server pass?

- A. 18 of 24 checks
- B. 24 of 30 checks
- C. 24 of 24 checks
- D. 8 of 8 checks

**Q6.** Which assertion is appropriate after a fuzz run?

- A. Every frame received exactly one reply
- B. No invalid output, and the process survived
- C. All replies had `resultType: "complete"`
- D. The reply count equals the frame count

**Q7.** What must you normalise in a golden transcript?

- A. Tool names and argument names
- B. Error codes returned by the server
- C. The order of tools in listings
- D. Volatile fields such as `_meta` and ids

**Q8.** Which change to a tool definition is compatible?

- A. Adding an optional argument
- B. Making an argument required
- C. Removing an enum value
- D. Changing an argument's type

**Q9.** Why are breaking tool changes especially disruptive in MCP?

- A. Servers cannot version their tools
- B. The protocol forbids schema changes
- C. Hosts cache and may have approved definitions
- D. Models re-read schemas on every call

**Q10.** Which environment variables does the official Python SDK pass to a stdio server by default on Linux?

- A. The full environment of the parent process
- B. None at all
- C. Only the variables prefixed with `MCP_`
- D. `HOME`, `LOGNAME`, `PATH`, `SHELL`, `TERM`, `USER`

**Q11.** What did the container run in §7.3 demonstrate?

- A. That containers authorise tool calls
- B. Conformance with no network and a read-only filesystem
- C. That stdio cannot work in containers
- D. That images must run as root to bind stdio

**Q12.** Why can a Streamable HTTP MCP server scale horizontally without sticky sessions?

- A. Each request carries everything needed to process it
- B. Clients always reconnect to the same instance
- C. The protocol replicates sessions between instances
- D. SSE streams are resumable across instances

**Q13.** *(Written, rubric-graded.)* In under 150 words: describe the checks you would run in CI before releasing a new
version of an MCP server, and what each one catches.

---

## 12. Revision notes

- **Five revisions**; `2026-07-28` is modern, the rest negotiate with `initialize`. Support an explicit set; never sort.
- **Lifecycle:** Active → Deprecated (≥12 months) → Removed. Deprecated now: Roots, Sampling, Logging, HTTP+SSE, DCR.
- **Conformance suite** (24/24 measured) including the three bugs tolerant clients hide: stdout purity, id type, discover
  and the negotiated version.
- **Fuzz** (300 frames): assert no invalid output and survival — 274 replies, 0 invalid, still alive.
- **Golden transcripts**: normalise `_meta`/ids; each mutation showed as one differing step.
- **Breaking vs compatible**: required arguments, removed enum values, type changes and dropped output guarantees break;
  additive changes do not. Rename or version, and mind cached definitions.
- **Ship:** package as a command, environment allowlist, stdout clean, exit on EOF; container with `--network none`,
  `--read-only`, `--cap-drop ALL`, non-root (8/8 measured); HTTP adds TLS, Origin, auth, limits and health.

---

## 13. Completion checklist

- [ ] I can place any revision on the timeline and know what is deprecated.
- [ ] I have a conformance suite that runs in CI, including the negotiated version.
- [ ] I fuzz my server and assert survival and output validity.
- [ ] I keep golden transcripts and classify tool-definition changes.
- [ ] I can package and containerise a stdio server, and list what an HTTP deployment adds.
- [ ] I scored at least 10/13 on the quiz.

---

## 14. References

- MCP changelog 2026-07-28 (feature lifecycle, deprecations, removals) —
  <https://modelcontextprotocol.io/specification/2026-07-28/changelog> `[VERIFIED 2026-09-15]`
- MCP 2026-07-28, *Versioning and Compatibility* — <https://modelcontextprotocol.io/specification/2026-07-28/basic/versioning> `[VERIFIED 2026-09-15]`
- Feature lifecycle policy and deprecated features registry — <https://modelcontextprotocol.io/community/feature-lifecycle>
  and `/specification/2026-07-28/deprecated` `[VERIFIED 2026-09-15 via the changelog's links]`
- `mcp` 2.2.0: `mcp_types.version` registry; `mcp/client/stdio.py` (environment allowlist, shutdown timeouts) `[VERIFIED 2026-09-16]`
- Docker documentation: `--read-only`, `--cap-drop`, `--network none` — <https://docs.docker.com/engine/reference/run/> `[STABLE]`

---

## 15. Next lesson

→ Module 9 ends here. **Project 9** applies it: an MCP server for the course catalogue with permissioned learner progress,
built on the server from M9-L09, tested with the suite from this lesson. Module 10 turns from one protocol to the
governance and security practices that decide whether any of this is fit to put in front of users:
[M10-L01 — Governance, Safety, Security and Compliance are Four Different Things](../module-10-governance-security/M10-L01-governance-safety-security-compliance.md).
