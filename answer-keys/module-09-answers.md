# Module 9 — Answer Key

**Do not read this before attempting the questions.** Every answer carries a reason, and for multiple
choice, a reason each distractor fails.

> Module 9 quiz options are uniform in length with a balanced answer distribution, and carry no inline
> explanation of the correct choice. All rationale lives here.

| Lesson | Jump to |
|---|---|
| M9-L01 What MCP Standardizes — and Explicitly What It Does Not | [↓](#m9-l01) |
| M9-L02 Hosts, Clients and Servers | [↓](#m9-l02) |
| M9-L03 The Three Primitives: Tools, Resources, Prompts | [↓](#m9-l03) |
| M9-L04 JSON-RPC 2.0 Foundations | [↓](#m9-l04) |
| M9-L05 Initialization and Capability Negotiation | [↓](#m9-l05) |
| M9-L06 Discovery and Invocation | [↓](#m9-l06) |
| M9-L07 Input and Output Schemas | [↓](#m9-l07) |
| M9-L08 Transports: stdio and Streamable HTTP | [↓](#m9-l08) |
| M9-L09 Build Your First MCP Server | [↓](#m9-l09) |
| M9-L10 Authentication vs Authorization in MCP | [↓](#m9-l10) |
| M9-L11 OAuth Concepts and MCP's Authorization Requirements | [↓](#m9-l11) |
| M9-L12 Credentials, Token Handling and Trust Boundaries | [↓](#m9-l12) |
| M9-L13 Permission Enforcement Outside the Model | [↓](#m9-l13) |
| M9-L14 Errors, Timeouts, Cancellation, Logging and Debugging | [↓](#m9-l14) |
| M9-L15 Tool Descriptions, Discoverability and Untrusted Tool Results | [↓](#m9-l15) |
| M9-L16 Protocol Versions, Compatibility, Testing and Deployment | [↓](#m9-l16) |

> **Answer-pattern note.** The M9-L01–L03 quizzes cycle A · D · B · C. From M9-L04 onward every quiz has
> a balanced but *unpatterned* distribution, so the position of one answer tells you nothing about the next.

---

<a id="m9-l01"></a>
## M9-L01 — What MCP Standardizes — and Explicitly What It Does Not

**Answers: A · D · B · C · A · D · B · C · A · D · B · C**

| Q | Ans | Why, and why the distractors fail |
|---|---|---|
| 1 | **A** | The lab's own measured result: both servers' tools/list responses shared the identical `jsonrpc`/`id`/`result.tools` envelope. **B**, **C** and **D** contradict the lab's own printed output. |
| 2 | **D** | The lab's own measured result: the identical `dispatch()` correctly handled both the refund and weather requests with no domain-specific branch. **A**, **B** and **C** contradict this measured, printed result. |
| 3 | **B** | The lab's own measured result: `decide_next_for_refund_request()`, a plain host-side function, determined the call order. **A**, **C** and **D** contradict the lab's own printed trace and code. |
| 4 | **C** | This is the lesson's own stated conclusion: MCP has no opinion on the host's choice of decision logic. **A**, **B** and **D** contradict this stated conclusion. |
| 5 | **A** | The lab's own measured result: the identical request produced $999.00 from v1 and $40.00 (capped) from v2. **B**, **C** and **D** contradict this measured, printed result. |
| 6 | **D** | The lesson states this directly: the schema describes the calling interface, not the tool's internal behavior. **A**, **B** and **C** contradict this stated distinction. |
| 7 | **B** | The worked example states this directly as the resolution of the compliance dispute. **A**, **C** and **D** contradict the worked example's own stated facts. |
| 8 | **C** | The worked example states this directly as the actual, valid concern once compliance was confirmed. **A**, **B** and **D** contradict the worked example's own stated facts. |
| 9 | **A** | This is the worked example's own stated general rule. **B**, **C** and **D** contradict this stated rule or overstate an absolute the lesson does not support. |
| 10 | **D** | Section 7.5 names these specifically as not shown, deferring to later lessons in this module. **A**, **B** and **C** name things this lesson does cover directly. |
| 11 | **B** | This is the lesson's own stated point in §5.1: the two servers' differing subject matter is content, not part of the shared envelope shape. **A**, **C** and **D** name parts of the shared shape itself. |
| 12 | **C** | This is the lesson's own stated general conclusion, tying together every section's specific measured finding. **A**, **B** and **D** contradict this conclusion or the evidence presented throughout the lesson. |

**Q13 rubric (5 marks).** One mark each for: **naming what MCP actually standardizes**, per §5.1-§5.2 — the
calling convention (message shape for listing and invoking tools), not the logic that decides which tool to
call; **naming the decision step as the host's own responsibility**, per §5.3 and §7.3 — M8-L03's own
`run_tool_loop()` worked unmodified against MCP-style calls specifically because the decision of which tool
to call, and when, was never part of the protocol layer; **giving a concrete consequence of the
misconception**, per §5.3 — a team that skips reviewing its own tool-selection logic because "MCP handles
it" would ship an agent whose actual behavior (what it decides to call, and in what order) was never actually
checked by anyone; **connecting this to tool behavior as a second, separate gap**, per §5.4 — even a
correctly-selected tool call can produce different real outcomes depending on the server's own
implementation, a second area MCP does not cover; and **stating the corrected expectation**, per §5.1 — MCP
reduces integration friction (one calling convention for any compliant server) but does not remove the need
to design, write, and review the host's own decision logic. An answer that only says "that's wrong" without
naming the specific layer (decision logic) MCP leaves to the host scores 2.

---

<a id="m9-l02"></a>
## M9-L02 — Hosts, Clients and Servers

**Answers: A · D · B · C · A · D · B · C · A · D · B · C**

| Q | Ans | Why, and why the distractors fail |
|---|---|---|
| 1 | **A** | The lesson states this directly: two independently-developed servers sharing a tool name is ordinary, not a bug. **B**, **C** and **D** contradict the lab's own printed setup. |
| 2 | **D** | The lab's own measured result: `refund_client` is structurally bound to `refund_server` alone. **A**, **B** and **C** contradict the lab's own code and printed output. |
| 3 | **B** | The lab's own measured result: `refund_server`'s `get_status` entry vanished, silently overwritten by `shipping_server`'s. **A**, **C** and **D** contradict this measured, printed result. |
| 4 | **C** | The lesson states this directly: each server's own tests passed, since the collision existed only at the aggregation layer neither server's team owned. **A**, **B** and **D** contradict this stated reasoning. |
| 5 | **A** | The lab's own measured result: `NamespacedHost` keys its catalog by `"{server_name}.{tool_name}"`. **B**, **C** and **D** contradict the lab's own printed code and output. |
| 6 | **D** | The lesson states this directly, per M9-L01's own finding that MCP does not mandate host-side design choices. **A**, **B** and **C** contradict this stated conclusion. |
| 7 | **B** | The worked example states this directly as the root cause, mirroring §7.3's own demonstrated collision. **A**, **C** and **D** contradict the worked example's own stated facts. |
| 8 | **C** | The worked example states this directly: no test exercised the host with two servers sharing a tool name. **A**, **B** and **D** contradict the worked example's own stated facts. |
| 9 | **A** | This is the worked example's own stated general rule. **B**, **C** and **D** contradict this stated rule or invent an unsupported absolute. |
| 10 | **D** | This is the lesson's own stated distinction in §3.4. **A**, **B** and **C** contradict this stated distinction. |
| 11 | **B** | Section 5.5 names these specifically as not covered, left to later lessons in this module. **A**, **C** and **D** name things this lesson does cover directly. |
| 12 | **C** | This is the lesson's own stated general conclusion, tying together every section's specific measured finding. **A**, **B** and **D** contradict this conclusion or the evidence presented throughout the lesson. |

**Q13 rubric (5 marks).** One mark each for: **checking for tool-name collisions across the two servers
before deployment**, per §5.3-§5.4 and §6 — listing every tool each server exposes and comparing the two
lists directly, since MCP guarantees uniqueness only within one server's own catalog; **checking how the
host currently aggregates tools**, per §5.3 — specifically whether it keys by bare tool name (vulnerable, per
`NaiveHost`) or already namespaces by server (safe, per `NamespacedHost`); **testing the host with both
servers connected simultaneously, not just each individually**, per §6 — since this class of bug is invisible
to any test using only a single connected server; **proposing namespacing as the fix if bare-name aggregation
is found**, per §5.4 — qualifying every tool by its owning server before the change ships; and **explaining
why this matters even if no collision is found today**, per §5.3 — a future third server could still
introduce one, so the aggregation scheme itself, not just today's specific tool names, is what should be
made safe. An answer that only says "check for naming conflicts" without addressing the aggregation
mechanism itself scores 2.

---

<a id="m9-l03"></a>
## M9-L03 — The Three Primitives: Tools, Resources, Prompts

**Answers: A · D · B · C · A · D · B · C · A · D · B · C**

| Q | Ans | Why, and why the distractors fail |
|---|---|---|
| 1 | **A** | `issue_refund` takes an order id *and* an amount chosen at call time — a decision with consequences. **B** describes a resource read; **C** contradicts the explicit call in §7.1; **D** describes a prompt. |
| 2 | **D** | §7.2 read `orders://O-1001` with nothing but the URI. **A** and **B** describe a tool call's argument choice; **C** describes rendering a prompt. |
| 3 | **B** | §7.3 printed a filled-in sentence whose wording the server owns. **A** is a tool's effect; **C** is the §7.4 lookup; **D** is a resource read. |
| 4 | **C** | The printed trace shows exactly one step, `['get_customer_orders']`. **A** is the resource path's count; **B** has no basis in the trace; **D** is wrong because the lab is deterministic. |
| 5 | **A** | §7.4 read the identical list through `read_resource` with no decision function involved. **B** and **C** invent steps; **D** is contradicted by the two identical printed results. |
| 6 | **D** | Same data, 1 step versus 0 — the extra step bought nothing. **A** inverts the finding; **B** contradicts the measured 1-versus-0; **C** is exactly what the measurement disproves. |
| 7 | **B** | Applying a discount changes an order and needs a real choice of order and code. **A** and **C** are pure lookups (§6 finding 1); **D** ignores that finding. |
| 8 | **C** | §6 says the issue surfaced only when step counts were compared across integrations. **A**, **B** and **D** are plausible review methods the worked example does not describe; every individual call "worked correctly", so none of them would have flagged it. |
| 9 | **A** | This is §6's general rule verbatim in substance. **B**, **C** and **D** are properties unrelated to whether a decision exists — a resource can be long, frequently read, or large. |
| 10 | **D** | §5.5 lists subscriptions, prompt argument schemas and the handshake as not shown. **A**, **B** and **C** are the lesson's main demonstrations. |
| 11 | **B** | §3.2 defines the test by what *using* the primitive requires. **A**, **C** and **D** are surface properties that say nothing about decisions or side effects. |
| 12 | **C** | The measured 1-versus-0 step difference is the lesson's whole argument. **A** is the §6 mistake; **B** is false — resources and prompts are core primitives; **D** is what §7.4 disproves. |

**Q13 rubric (5 marks).** One mark each for: **recommending a resource** (e.g. `accounts://{id}/balance`)
rather than a tool; **applying the §3.2 test** — reading a balance needs only an identifier, not a choice
between arguments or outcomes; **naming the cost** of the tool design — an unnecessary planning step on every
run that needs the balance (§5.4, measured 1 versus 0); **noting reliability** — a tool invites a
decision step to supply a wrong or hallucinated argument, a fixed address does not (§9); and **stating the
condition that would change the answer** — if retrieving the balance had a side effect or needed a genuine
choice (for example "balance as of a chosen date with currency conversion"), a tool becomes defensible.
An answer that says "resource" without the test or the cost scores 2.

---

<a id="m9-l04"></a>
## M9-L04 — JSON-RPC 2.0 Foundations

**Answers: C · A · D · B · D · A · C · D · B · A · C · B**

| Q | Ans | Why, and why the distractors fail |
|---|---|---|
| 1 | **C** | A notification has `method` and no `id` at all. **A** has an `id` member (and `null` is forbidden in MCP); **B** has an id, so it is a request; **D** mixes `method` and `result`, which is invalid. |
| 2 | **A** | `tools/call` exists; the tool name is a parameter, so the params are invalid — the spec's own example uses `-32602`. **B** would mean `tools/call` itself is unknown; **C** is for unparseable JSON; **D** is for failures inside the server. |
| 3 | **D** | The lab printed `19/20`. **A** is the id-based result; **B** is a guess at "half"; **C** is the number of *correct* matches, not misroutes. |
| 4 | **B** | The expected number of fixed points of a random permutation is 1 for any N, so about `N − 1` of N are misrouted. **A** is not required — any completion order that differs from send order causes it; **C** is irrelevant to correlation; **D** describes loss, not misrouting. |
| 5 | **D** | The rule is scoped to requests still in flight. **A** is stricter than the spec (reuse after completion is legal); **B** is not required — ids are per sender; **C** invents a method-based exception. |
| 6 | **A** | `1`, `1.0` and `True` merged into one key and `"1"` stayed separate: 2 entries. **B** would require JSON-like distinctness; **C** ignores that `"1"` is a string; **D** — Python accepts all four as keys. |
| 7 | **C** | Only when the id could not be read (e.g. a parse error). **A** is not a rule; **B** — notifications get no response at all; **D** would make the error impossible to correlate and is never permitted. |
| 8 | **D** | Batching was added in 2025-03-26 and removed in 2025-06-18; current transports carry one message per frame. **A**, **B** and **C** describe rules MCP never had. |
| 9 | **B** | Notifications MUST NOT be answered, and the stray reply has no id to correlate. **A** contradicts the spec; **C** — the fault is replying at all, not the reply's shape; **D** is meaningless for a response. |
| 10 | **A** | Clients MUST treat an absent `resultType` as `"complete"` for backward compatibility. **B** would break every pre-2026-07-28 server; **C** inverts the default; **D** repeats a request that already succeeded. |
| 11 | **C** | With one customer, only one request was ever in flight, so order-based matching could not fail. **A**, **B** and **D** are not described and would not by themselves hide the bug. |
| 12 | **B** | `-32020…-32099` is reserved for MCP-defined codes; `-32000…-32019` is legacy. **A** straddles JSON-RPC's own reserved codes; **C** is the legacy sub-range; **D** is JSON-RPC's standard codes. |

**Q13 rubric (5 marks).** One mark each for: **reproducing with concurrency** — driving many simultaneous
requests (N ≫ 1) against a server whose latency varies, since the defect is invisible at N = 1 (§5.3);
**inspecting the correlation mechanism** — checking whether responses are matched by `id` in a pending table
or by order/timing (§5.3, §6); **checking id generation** — whether ids can repeat while requests are in
flight, e.g. counters that reset per page, per component or on reconnect (§5.4); **checking id validation and
typing** — Python `bool`/`int`/`float` key collisions (§5.5); and **stating the fix** — a per-connection
monotonic id, a dict of pending futures keyed by id, and logging plus discarding responses that match nothing
(§5.3, §5.6). Naming "race condition" without a mechanism scores 1.

---

<a id="m9-l05"></a>
## M9-L05 — Initialization and Capability Negotiation

**Answers: B · D · A · C · C · A · D · B · A · C · B · D**

| Q | Ans | Why, and why the distractors fail |
|---|---|---|
| 1 | **B** | The handshake is request → result → `notifications/initialized`; the client's notification ends it. **A** is only the second message; **C** is ordinary work after initialization; **D** — `ping` is allowed early but completes nothing. |
| 2 | **D** | The counter-offer rule: answer with a supported version, normally the latest; the client then proceeds or disconnects. **A** — `-32022` is a modern-era error; **B** inverts the rule; **C** — the server must answer. |
| 3 | **A** | All 46 wrong decisions were B's requests judged with A's stored capabilities. **B** — the requests were valid; **C** — nothing was rejected as malformed; **D** — A's requests were judged correctly. |
| 4 | **C** | Both are marked required in the 2026-07-28 `_meta` table. **A** — both optional; **B** — `serverInfo` belongs in results; **D** — `traceparent` is optional tracing context. |
| 5 | **C** | The spec requires `MissingRequiredClientCapabilityError` (`-32021`) with `data.requiredCapabilities`. **A** is for malformed params; **B** is for tool execution failures, not protocol conditions; **D** is about the version. |
| 6 | **A** | Uppercase `D` (0x44) sorts after `2` (0x32), so `max()` picks it. **B** — it was listed last; **C** — the client did not support it at all; **D** — the client had no such preference. |
| 7 | **D** | A recognised modern error proves the server is modern; retry with a supported version and do not fall back. **A** is exactly the prohibited reaction; **B** abandons a working server; **C** produces `-32602`. |
| 8 | **B** | Legacy servers answer unknown pre-initialize methods with implementation-defined errors, commonly `-32601` or `-32602`, or not at all — measured 1/3 vs 3/3. **A** overstates; **C** is false (`-32022` exists); **D** is invented. |
| 9 | **A** | Legacy clients have no way forward; the modern server rejects `initialize`. **B**, **C** and **D** describe behaviour neither party implements. |
| 10 | **C** | `clientInfo` is self-reported and intended for display, logging and debugging; servers SHOULD NOT use it for security decisions. **A**, **B** and **D** are behaviour or security decisions. |
| 11 | **B** | The probe converts a lenient legacy server's silent misprocessing into an early, clear failure. **A** overstates — probing is recommended, not required per call; **C** — `tools/list` lists tools; **D** — modern servers keep no such state. |
| 12 | **D** | Per-request capabilities forwarded in `_meta` remove the shared-connection assumption. **A** removes a safety feature; **B** does not touch the cause; **C** avoids rather than fixes. |

**Q13 rubric (5 marks).** One mark each for: **probing first with `server/discover`** at the client's preferred
modern version, with a short timeout (§5.6); **modern outcome** — on a `DiscoverResult`, choose a version from the
intersection with the client's own list and send `protocolVersion` + `clientCapabilities` in `_meta` on every
request (§5.3, §5.5); **recognised modern error** — on `-32022`, retry with a version from `data.supported` rather
than falling back (§5.6); **legacy outcome** — on any other error *or* no reply, run `initialize` →
`notifications/initialized`, accepting or disconnecting on the counter-offer (§5.1); and **naming a naive bug** —
falling back only on `-32601`, picking `max()` of version strings, not bounding the probe timeout, or caching
capabilities per connection (§5.2, §5.5, §5.6). Also accept caching the detected era per server process.

---

<a id="m9-l06"></a>
## M9-L06 — Discovery and Invocation

**Answers: D · B · C · A · A · C · B · D · C · A · D · B**

| Q | Ans | Why, and why the distractors fail |
|---|---|---|
| 1 | **D** | An empty string is a valid cursor and MUST NOT be treated as the end; only an absent `nextCursor` ends the list. **A** is the exact mistake the spec names; **B** assumes a page size; **C** — the response is valid. |
| 2 | **B** | Its loop ended when a page held fewer than 20 items, so a full 15-item page looked final. **A** — its cursors were genuine; **C** is a different client; **D** — order does not affect count. |
| 3 | **C** | The spec cites client-side caching and LLM prompt-cache hit rates; §7.2 measured 10 vs 1 serializations. **A** — JSON has no such rule; **B** — pagination uses opaque cursors; **D** is false. |
| 4 | **A** | Uses at t = 200…295 s, 20 moments, before the TTL expired at 300 s. **B** is the TTL + notifications row; **C** is cache-forever; **D** is the number of fetches for always-refetch. |
| 5 | **A** | `"private"` is for results that depend on the caller; they may be reused only within the same authorization context. **B** allows sharing across users; **C** — TTL governs freshness, not sharing; **D** — `resources/read` is explicitly cacheable. |
| 6 | **C** | The spec says servers MUST NOT rely on `cacheScope` alone; every invocation must be authorised. **A** is the error it warns against; **B** — it encrypts nothing; **D** — it says nothing about model selection. |
| 7 | **B** | Simple expansion percent-encodes `/` as `%2F`, keeping the value a single identifier. **A** is string replacement; **C** and **D** are not RFC 6570 behaviours. |
| 8 | **D** | 2026-07-28 moved "resource not found" to `-32602`. **A** hides the failure; **B** means the method is unknown; **C** is the legacy code, which clients should still *accept* but current servers must not emit. |
| 9 | **C** | The retry is a new request with a new id, the original params, `inputResponses`, and `requestState` echoed exactly. **A** reuses the id; **B** modifies the state; **D** — the server stored nothing. |
| 10 | **A** | Statelessness: the server's only memory of round 1 was the `requestState` the client failed to return. **B** — new ids are required; **C** — the schema was fine for the other client; **D** — no cache was involved. |
| 11 | **D** | Prompts are designed to be user-controlled, surfaced for a person to choose. **A** describes tools; **B** and **C** describe no MCP primitive. |
| 12 | **B** | The loop condition `len(page) == 25` broke when the server's first page shrank to 15. **A** — the tools still existed; **C** — the cache issue was separate and cost-related; **D** — no schema error was involved. |

**Q13 rubric (5 marks).** One mark each for: **pagination** — loop on `nextCursor` until absent, never assume page
size or build cursors, restart from the beginning if a cursor becomes invalid (§5.2); **freshness** — cache per
server for `ttlMs`, invalidate on `list_changed` via `subscriptions/listen`, and do not poll on the TTL without
jitter (§5.4); **cache partitioning** — key caches by server, authorization context and cursor, and share only
`"public"` results across users (§5.4); **ordering and aggregation** — keep a deterministic order and namespace
tools per server to avoid collisions (§5.3, M9-L02); and **one security concern with a mitigation** — for example,
cached per-user lists leaking across users, relying on filtered lists instead of per-call authorization, or tool
descriptions as untrusted input (M9-L15). A design that re-lists on every turn with no caching scores at most 2.

---

<a id="m9-l07"></a>
## M9-L07 — Input and Output Schemas

**Answers: A · C · B · D · B · A · D · C · C · B · A · D**

| Q | Ans | Why, and why the distractors fail |
|---|---|---|
| 1 | **A** | Schemas without `$schema` default to 2020-12. **B** must be declared explicitly via `$schema`; **C** is not MCP's vocabulary; **D** — the dialect is defined by the schema, not the client. |
| 2 | **C** | Types caught the four string/null cases plus the two missing-key cases: 6. **A** is required-keys only; **B** is the full schema; **D** ignores the type failures. |
| 3 | **B** | The spec recommends it because it accepts only an empty object. **A** — `inputSchema` MUST NOT be `null`; **C** is legal but accepts any object (5/5 in §7.2); **D** lacks the required root `type: "object"`. |
| 4 | **D** | Type checks only inspect declared properties; without `additionalProperties: false`, an extra key is ignored. **A** is false; **B** — it was not declared at all; **C** — no enum applied to it. |
| 5 | **B** | `.get("status")` returned `None`, every order looked ineligible, and no exception occurred. **A** would have required `result["status"]`; **C** — only the validating client detected it; **D** inverts the outcome. |
| 6 | **A** | "Servers MUST provide structured results that conform to this schema." **B** contradicts the backward-compatibility guidance; **C** confuses output with input; **D** — the schema is in the tool definition. |
| 7 | **D** | Older clients only understand `content`; the text copy keeps them working. **A** — it is any JSON value; **B** — models read either form via the host; **C** overstates a SHOULD. |
| 8 | **C** | Implementations MUST NOT automatically dereference network `$ref`s. **A** is automatic dereferencing; **B** is the permissive treatment the spec says to avoid; **D** silently weakens the schema. |
| 9 | **C** | About 1.6 kB of schema demanded 32,762 evaluations at depth 12. **A** is false; **B** — the schemas were valid; **D** — a budget rejects expensive schemas rather than validating them loosely. |
| 10 | **B** | The result was well-formed; the failure was on the input side. **A**, **C** and **D** would each have rejected the call. |
| 11 | **A** | `structuredContent` is server-produced result data. **B** is the specific confusion the spec warns against; **C** and **D** are unrelated concepts. |
| 12 | **D** | Don't guess; report a precise, attributable failure. **A** passes corrupted data to decisions; **B** fabricates data; **C** — a drifted server will keep returning the same shape. |

**Q13 rubric (5 marks).** One mark each for: **`required`** — at least `when`, `attendees` and `duration` should be
required, with a reason (§5.2); **format and ranges** — `when` needs a constraint such as `format: "date-time"` plus
server-side parsing, and `duration` should be an `integer` (minutes) with `minimum`/`maximum` (§5.2); **array items** —
`attendees` needs `items` (e.g. string with an email pattern), `minItems`/`maxItems` (§5.2); **`additionalProperties:
false`** with the §5.3/§6 reasoning; and **one of**: descriptions and units for the model's benefit, an
`outputSchema` for the created meeting with conformance checks (§5.4–§5.5), or server-side validation regardless of
client checks. Listing fixes without reasons scores at most 3.

---

<a id="m9-l08"></a>
## M9-L08 — Transports: stdio and Streamable HTTP

**Answers: C · D · A · B · D · B · C · A · B · D · C · A**

| Q | Ans | Why, and why the distractors fail |
|---|---|---|
| 1 | **C** | The server MAY log to stderr and MUST NOT write non-messages to stdout. **A** and **B** still put non-messages on stdout; **D** is false — stderr logging is explicitly allowed. |
| 2 | **D** | Every log line pushed later responses down, so position no longer matched id. **A** — every response was a valid result; **B** — it handled all ten; **C** — all ten responses were present. |
| 3 | **A** | Newlines inside strings become the two characters `\n`, so a compact message is one physical line. **B**, **C** and **D** describe behaviours `json.dumps` does not have. |
| 4 | **B** | Close stdin, wait, then SIGTERM, then SIGKILL. **A** kills first; **C** skips the graceful signal; **D** — there is no standard exit request on stdio. |
| 5 | **D** | Accepted notifications get 202 with no body. **A**, **B** and **C** all send a body — and notifications never get JSON-RPC responses. |
| 6 | **B** | 2026-07-28 removed protocol-level sessions (and the GET stream and resumability). **A**, **C** and **D** remain part of the transport. |
| 7 | **C** | Any header/body mismatch MUST be rejected with 400 and `HeaderMismatch` (`-32020`). **A** and **B** each let one component's decision diverge from another's; **D** is dangerous and meaningless. |
| 8 | **A** | Split-brain decisions — routing or authorising on headers while executing the body — are the risk the rule closes. **B** is false; **C** — TLS covers both equally; **D** — the body carries `method`. |
| 9 | **B** | It is not an allowed origin; servers MUST respond 403. **A** is the prefix-matching bug §7.7 demonstrates; **C** does not stop the request; **D** ignores where it came from. |
| 10 | **D** | Local servers SHOULD bind only to loopback. **A**, **B** and **C** expose the server to the network. |
| 11 | **C** | stdio implementations SHOULD NOT follow the HTTP authorization flow and should retrieve credentials from the environment. **A** is for HTTP transports; **B** — headers do not exist on stdio; **D** — `clientInfo` is self-reported metadata. |
| 12 | **A** | A human skims past `Connecting to analytics.db...`; a JSON parser rejects it. **B** — terminals don't filter; **C** — the database did connect; **D** — manual tests used stdio. |

**Q13 rubric (5 marks).** One mark each for: **desktop → stdio**, because only the launching host can talk to it and
credentials come from the environment (§5.1, §5.9); **stdio controls** — trusted distribution or pinned package,
sandboxing/least privilege for a process running with the user's rights, logs to stderr with no secrets (§5.2, §5.9);
**shared → Streamable HTTP**, stateless behind a load balancer (§5.5, §5.9); **HTTP controls** — TLS, OAuth-based
authentication and authorization (M9-L10/L11), header/body validation (§5.6), no sensitive `x-mcp-header` params;
and **an explicit rule against a local HTTP shortcut**, or, if one is needed, `127.0.0.1` binding, exact `Origin`
allowlist and a token (§5.7). Recommending HTTP for both with no local-server controls scores at most 3.

---

<a id="m9-l09"></a>
## M9-L09 — Build Your First MCP Server (stdio, Python)

**Answers: B · A · D · C · A · D · C · B · D · B · C · A**

| Q | Ans | Why, and why the distractors fail |
|---|---|---|
| 1 | **B** | Details go to stderr; the client gets a bare `-32603`, so no stack trace or data leaks. **A** leaks internals; **C** breaks stdio framing; **D** — the loop catches exceptions precisely so one request cannot kill the process. |
| 2 | **A** | Input validation failures are tool execution errors, returned with `isError` so the model can correct itself. **B** is the protocol channel; **C** claims a server fault; **D** silently changes the user's request. |
| 3 | **D** | Unknown tools are listed under protocol errors. **A**, **B** and **C** are the spec's examples of tool execution errors. |
| 4 | **C** | Section 2 of the interop output reports 9/9 in legacy mode. **A** and **B** do not match the output; **D** — the server is dual-era. |
| 5 | **A** | The probe failed with a non-modern error, so the client fell back to `initialize` and negotiated 2025-11-25 — silently. **B**, **C** and **D** are what happened to *other* mutations, or nothing at all. |
| 6 | **D** | `coerce_request_id` converts numeric strings back to integers "so a peer-echoed id still correlates". **A** is false — JSON-RPC ids of different types are distinct; **B** — requests used integer ids; **C** — nothing timed out. |
| 7 | **C** | No complete JSON line ever arrived, so the client waited until the 12-second watchdog. **A** worked; **B** and **D** raised `ValidationError`. |
| 8 | **B** | Three real bugs passed silently; only your own tests would catch them. **A** overstates — it caught five; **C** — the hand-written server passed 9/9 twice; **D** — framing and version bugs mattered too. |
| 9 | **D** | `ToolError` is the anticipated-failure exception whose message reaches the model. **A** is a success result; **B** is treated as a crash and masked; **C** kills the server. |
| 10 | **B** | Observed: `isError` result with `Unknown tool: drop_tables`. **A** and **C** are protocol errors (our hand-written server used **C**); **D** did not occur. |
| 11 | **C** | The original host fell back to the legacy handshake when discover failed, so everything appeared to work. **A** and **B** are unrelated; **D** hid a *different* defect (string ids). |
| 12 | **A** | They were introduced in 2026-07-28 and are not part of the legacy schema the client negotiated. **B** overstates — clients generally ignore unknown fields; **C** is unrelated; **D** is false. |

**Q13 rubric (5 marks).** One mark each for: **an independent-client interop test**, ideally more than one SDK or host,
in both protocol eras (§5.6); **tests for bugs tolerant clients hide** — clean stdout, id type preserved, discover
implemented and negotiated version asserted (§5.7, §6); **error-channel tests** — bad arguments give actionable
`isError` results, unknown tools/resources give protocol errors, exceptions never leak text (§5.2, §5.4); **robustness
tests** — malformed JSON, batches, missing `_meta`, unsupported versions, notifications, EOF shutdown (§5.5); and **a
reason grounded in evidence** — e.g. the mutation test's three tolerated bugs, or §6's second client failing on ids.
"Add more unit tests" without naming what they check scores 1.

---

<a id="m9-l10"></a>
## M9-L10 — Authentication vs Authorization in MCP

**Answers: D · B · A · C · C · A · B · D · A · D · B · C**

| Q | Ans | Why, and why the distractors fail |
|---|---|---|
| 1 | **D** | Audience validation establishes that the token is genuinely for this server — part of accepting the credential. **A** and **B** decide what the caller may do; **C** is a usability feature. |
| 2 | **B** | Design A allowed 5 of 32. **A** is design C; **C** is designs B and D; **D** is design E's count of wrong codes, not leaks. |
| 3 | **A** | Both leaks were `li` reading `raj`'s progress: operation allowed, object not checked (BOLA). **B**, **C** — authentication was identical across designs; **D** — B's codes were right, its decisions were wrong. |
| 4 | **C** | `clientInfo.name == "admin-console"` bypassed checks, and anyone can send it. **A** — `li` had `catalog:read progress:self`; **B** — the token was valid; **D** is unrelated to the bypass. |
| 5 | **C** | Filtering lists helps models and users but cannot stop a client that sends the name anyway (§7.3: 200). **A**, **B** and **D** all mistake it for enforcement. |
| 6 | **A** | Invalid or expired tokens MUST receive 401, with `WWW-Authenticate` so the client can re-authenticate. **B** is for insufficient scope; **C** is for malformed authorization requests; **D** is for tool execution failures. |
| 7 | **B** | Insufficient scope or permission → 403, with `error="insufficient_scope"` and `scope` when more scope would help. **A** would trigger re-authentication; **C** and **D** misreport the problem. |
| 8 | **D** | E made C's decisions (0 leaks) but mislabelled 16 authentication failures as 403. **A** is exactly the misconception; **B** — clients act on codes; **C** — E still used C's object checks. |
| 9 | **A** | stdio implementations SHOULD NOT follow the HTTP authorization flow and should use environment credentials. **B** is for HTTP; **C** is unverified self-description; **D** is meaningless. |
| 10 | **D** | Arguments such as `student_id` are chosen by the model, so any id can appear. **A**, **B** and **C** are false. |
| 11 | **B** | SSO provided authentication only; record-level rules were missing. **A** and **D** were exactly what failed; **C** — SSO does not prevent token theft. |
| 12 | **C** | The spec allows the set to vary by the authorization presented, since credentials are per-request input. **A** is too strict; **B** — per-user lists must be `private`; **D** — lists never replace per-call checks. |

**Q13 rubric (5 marks).** One mark each for: **distinguishing authentication from authorization** in plain terms (§3.1);
**naming operation-level authorization** — scopes or roles for the tool (§5.2); **naming object-level authorization** with a
concrete example on the chosen tool, noting that a model chooses the ids (§5.2, §6); **naming at least one false control** to
avoid — `clientInfo`/header bypasses, filtered lists, or instructions to the model (§5.3–§5.4); and **a concrete test** — a
caller × operation × object matrix with expected 200/401/403 per cell, including wrong-audience and expired tokens (§7.2,
§6 verification). Also accept correct 401/403 semantics as the fourth or fifth point.

---

<a id="m9-l11"></a>
## M9-L11 — OAuth Concepts and MCP's Authorization Requirements

**Answers: A · C · D · B · D · A · C · B · B · C · A · D**

| Q | Ans | Why, and why the distractors fail |
|---|---|---|
| 1 | **A** | A protected MCP server accepts and validates access tokens — a resource server. **B** issues tokens; **C** is the MCP client; **D** is the user. |
| 2 | **C** | MCP servers MUST implement Protected Resource Metadata; clients use the 401's `resource_metadata` or well-known URLs. **A** and **B** are protocol messages unrelated to authorization; **D** — the spec names no authorization servers. |
| 3 | **D** | For issuers with a path, OAuth metadata with path insertion comes first. **A** is third; **B** is second; **C** ignores the tenant path. |
| 4 | **B** | DCR (RFC 7591) is deprecated in favour of Client ID Metadata Documents. **A**, **C** and **D** remain supported options. |
| 5 | **D** | With `plain`, the challenge sent via the browser equals the verifier. **A** — codes were single-use; **B** — client_id matched; **C** — `resource` was present and irrelevant here. |
| 6 | **A** | An absent field means the AS does not support PKCE, and clients MUST refuse. **B** and **C** weaken or remove PKCE; **D** does not change the metadata's meaning. |
| 7 | **C** | Same AS and same key: only the audience claim, set from `resource`, differed. **A** and **B** were identical; **D** protects code redemption, not token use. |
| 8 | **B** | The check must happen before the code is sent to any token endpoint, or a mix-up has already succeeded. **A** is too late; **C** and **D** invent conditions. |
| 9 | **B** | The union of previously requested and challenged scopes preserves read access. **A** is the "replace" mistake; **C** over-requests; **D** will fail again. |
| 10 | **C** | Without a challenge scope, clients fall back to requesting everything in `scopes_supported`. **A**, **B** and **D** are false. |
| 11 | **A** | stdio implementations SHOULD NOT use this flow and take credentials from the environment. **B** and **C** are HTTP-based; **D** is irrelevant to the rule. |
| 12 | **D** | Replacing scopes dropped `docs:read` after each step-up. **A**, **B** and **C** were not observed. |

**Q13 rubric (5 marks).** One mark each for a correct ordered sequence covering: **401 + discovery** — `WWW-Authenticate`
`resource_metadata` or well-known PRM → `authorization_servers` → AS metadata (§5.2); **registration and authorization
request** — client id via pre-registration/CIMD/DCR, then browser authorization with `code_challenge` (S256), `resource`,
`scope`, `state` (§5.3–§5.4); **callback and token exchange** — verify `state` and `iss`, then redeem code with
`code_verifier` and `resource` (§5.4, §5.6); **authenticated request** — Bearer token in the header on every request, server
validates signature, expiry and audience (§5.5, M9-L10); and **at least three named checks with their attacks** (PKCE →
code interception; audience → token reuse at other servers; `iss` → mix-up; redirect URI/state → open redirect/CSRF). Fewer
than three correctly paired checks caps the score at 3.

---

<a id="m9-l12"></a>
## M9-L12 — Credentials, Token Handling and Trust Boundaries

**Answers: C · A · B · D · B · C · D · A · C · D · A · B**

| Q | Ans | Why, and why the distractors fail |
|---|---|---|
| 1 | **C** | PRM URLs are chosen by the server and can point at internal addresses (SSRF). **A**, **B** and **D** originate inside the client's own trust domain. |
| 2 | **A** | With no audience check and forwarding, the calendar token read li's files. **B** is the correct server's behaviour; **C** is a different row; **D** did not happen. |
| 3 | **B** | The spec says the upstream token is separate, issued by the upstream authorization server. **A** is passthrough; **C** violates least privilege; **D** — refresh tokens are never sent to resource servers. |
| 4 | **D** | Upstream logs showed only the user, hiding the MCP server's involvement. **A**, **B** and **C** were not involved. |
| 5 | **B** | All five planted credentials were visible. **A** is the allowlist result; **C** and **D** do not match the output. |
| 6 | **C** | stdio servers SHOULD retrieve credentials from the environment, so it defines what they can reach. **A** is false; **B** — environment variables are plain text; **D** — HTTP servers use Bearer headers. |
| 7 | **D** | It leaked 40/40 held-out lines in unseen formats — overfitting. **A** — benign lines altered: 0; **B** was not measured; **C** — it caught every JWT in the original corpus. |
| 8 | **A** | Fields not on the allowlist are never written. **B** leaked 200/240; **C** still writes secrets; **D** is reversible encoding, not protection. |
| 9 | **C** | `2852039166` is the 32-bit integer form of 169.254.169.254; the naive check compared strings. **A** and **D** are irrelevant; **B** — it was plain HTTP. |
| 10 | **D** | The guidance warns against manual IP validation because of octal, hex and IPv4-mapped tricks. **A** and **B** are exactly the fragile approaches; **C** — TLS does not stop requests to internal hosts. |
| 11 | **A** | Mode 0644 made the file world-readable. **B** — no encryption was involved; **C** and **D** did not occur. |
| 12 | **B** | The wiki saw the user's token and logged only the user. **A** — it did log; **C** was not the case; **D** is the fix, not the defect. |

**Q13 rubric (5 marks).** One mark each for a check **and** what it prevents, drawn from: **audience validation / no passthrough** —
separate upstream token (stolen tokens from other services; lost accountability) (§5.2); **per-client consent and exact
redirect matching if it is a proxy with a static client id** (confused deputy) (§5.2); **allowlisted logging, no tokens in URLs or
`x-mcp-header`** (credential leakage via logs and intermediaries) (§5.4); **secure token storage, short-lived tokens, refresh
rotation** (theft from caches/files) (§5.6); **SSRF controls on any URL the server or its dependencies fetch** (internal access,
metadata credentials) (§5.5); **least-privilege upstream credential** (blast radius) (§5.3, M9-L11). Checks without a stated
threat earn half credit.

---

<a id="m9-l13"></a>
## M9-L13 — Permission Enforcement Outside the Model

**Answers: C · B · A · B · D · C · D · A · C · B · A · D**

| Q | Ans | Why, and why the distractors fail |
|---|---|---|
| 1 | **C** | Injected text competes with the description, and a client can send any request regardless of the model. **A** and **B** are false — descriptions are sent to models; **D** invents a limit. |
| 2 | **B** | The measured count was 11 of 200 tasks (50 poisoned documents). **A** is the enforced run; **C** is the number of poisoned documents; **D** assumes every task was attacked. |
| 3 | **A** | Authorization must compare the requested object with the authenticated principal. **C** is the value under attacker influence; **B** is self-reported; **D** is attacker-supplied content. |
| 4 | **B** | `random` is not cryptographic, and seeds 0–199 regenerated the stream. **A** — they were 128-bit; **C** and **D** are not how the lab generated them. |
| 5 | **D** | Binding means possession alone is not authority. **A** and **C** are unrelated; **B** — expiry still limits exposure. |
| 6 | **C** | HMAC stops edits, not reuse: replay as another user (and later, and on another tool) was accepted. **A** was rejected; **B** did not occur — the key was not available; **D** contradicts the table. |
| 7 | **D** | The spec lists the authenticated principal, a short TTL and an identifier for the originating request. **A** is unverified metadata; **B** is pointless and large; **C** would leak credentials through the client. |
| 8 | **A** | The answer is produced by the client, so a compromised host can auto-accept — and over-asking causes fatigue. **B** and **C** are false; **D** is unrelated. |
| 9 | **C** | The per-handler design allowed it (no check written); the central table denied it for having no policy entry. **A**, **B** and **D** contradict the output. |
| 10 | **B** | It fails closed, so omissions surface as broken features. **A** — authentication is still required; **C** is irrelevant; **D** — decisions are not delegated to clients. |
| 11 | **A** | Authority supplied as an argument is authority the caller grants itself. **B**, **C** and **D** were not the defect. |
| 12 | **D** | Prompt-level defences lower the frequency of successful injection but do not bound consequences. **A** is what server enforcement does; **B** and **C** overstate them. |

**Q13 rubric (5 marks).** One mark each for: **server-side authorization on the authenticated principal**, including
object-level checks, as the primary bound (§5.1); **narrowing the tool surface** — remove dangerous arguments, prefer
`*_my_*` tools, read-only where possible (§5.1); **bound handles and bound `requestState`** — CSPRNG, principal binding,
expiry, request digest, one-time redemption (§5.2–§5.3); **human confirmation for a small set of high-consequence actions**,
with the caveat that it is defence in depth, not authorization (§5.4); and **containment and detection** — deny by default,
least-privilege downstream credentials, rate limits, logging denials, and prompt-level defences as frequency reduction
(§5.5–§5.6). An answer that relies on better prompting or model instructions scores at most 2.

---

<a id="m9-l14"></a>
## M9-L14 — Errors, Timeouts, Cancellation, Logging and Debugging

**Answers: B · D · A · C · C · A · D · B · A · C · B · D**

| Q | Ans | Why, and why the distractors fail |
|---|---|---|
| 1 | **B** | stdio has one shared channel, so cancellation is an explicit notification naming the request id. **A** shuts the whole server down; **C** and **D** are not MCP methods or behaviours. |
| 2 | **D** | Each request has its own response stream, so closing it is unambiguous; no notification is expected. **A** contradicts the transport rules; **B** gets 405; **C** is invented. |
| 3 | **A** | The server reported 4 work units before stopping. **B** is the stubborn server; **C** and **D** do not match the output. |
| 4 | **C** | It MUST NOT send any further messages for the cancelled request. **A** and **B** are encouraged; **D** — the connection stays usable. |
| 5 | **C** | The server reported progress indefinitely and each notification reset the deadline. **A** — a token was sent; **B** and **D** did not happen. |
| 6 | **A** | Resetting is allowed, but implementations SHOULD always enforce a maximum timeout. **B**, **C** and **D** contradict the spec's guidance. |
| 7 | **D** | Input-validation failures are execution errors the model can correct. **A**, **B** and **C** are the spec's protocol-error examples. |
| 8 | **B** | The protocol error carried nothing actionable, so 0 of 10 tasks completed. **A** is the execution-error result; **C** and **D** do not match. |
| 9 | **A** | Servers MUST NOT emit `notifications/message` for requests that did not set `io.modelcontextprotocol/logLevel`. **B** inverts the opt-in; **C** — `logging/setLevel` was removed; **D** — request-scoped notifications flow on the request's own stream. |
| 10 | **C** | These three keys are reserved for W3C Trace Context and Baggage. **A**, **B** and **D** are other reserved keys with different purposes. |
| 11 | **B** | Clients SHOULD ignore responses to cancelled requests; the id is no longer pending. **A** is the correlation bug from M9-L04; **C** alarms the user about work they cancelled; **D** is pointless. |
| 12 | **D** | The worker ran to completion after the stream closed, billing the warehouse. **A** is not how billing worked; **B** — retries were a separate defect on malformed filters; **C** was not the case. |

**Q13 rubric (5 marks).** One mark each for: **cancellation** — check a cancelled set between units of work (or treat an
HTTP disconnect as cancellation) and send nothing further (§5.1); **timeouts** — a per-tool deadline, optional reset on
progress, and an absolute maximum cap, or an async handle pattern for genuinely long work (§5.2); **error channels** —
actionable `isError` results for input and business failures, JSON-RPC errors for invalid requests, `-32603` with details
logged rather than returned (§5.3); **observability** — stderr logs with request ids and cancellation reasons, progress
notifications for liveness, trace context propagation, no payload logging (§5.4–§5.5); and **what to measure** — work
units or cost avoided after cancellation, p50/p99 duration versus the cap, retry counts per failure type, and the rate of
late responses. Naming controls without any measurement caps the score at 4.

---

<a id="m9-l15"></a>
## M9-L15 — Tool Descriptions, Discoverability and Untrusted Tool Results

**Answers: C · A · D · B · B · D · A · C · D · B · C · A**

| Q | Ans | Why, and why the distractors fail |
|---|---|---|
| 1 | **C** | Adding "use when / not for" phrasing and users' vocabulary took the selector from 4/12 to 11/12. **A** scored 1/12; **B** scored 4/12; **D** was not tested and carries even less signal. |
| 2 | **A** | The template covers what it does, what it returns, when to use it and when not to. **B** belongs in `serverInfo`; **C** is the host's decision logic; **D** is authorization metadata, not selection guidance. |
| 3 | **D** | Poisoning targets the model through metadata it reads. **A** is malformed input; **B** is denial of service; **C** is shadowing by name collision. |
| 4 | **B** | Both paraphrases were missed. **A** and **C** contradict the output; **D** — they were not flagged at all, which is the same as being treated as benign, but the measured statement is that both were missed. |
| 5 | **B** | You cannot know what a motivated author will write next; catches are a lower bound. **A** is false; **C** — scanning text is cheap; **D** — either side can scan. |
| 6 | **D** | Clients MUST consider annotations untrusted unless from a trusted server. **A**, **B** and **C** describe verification the protocol does not perform. |
| 7 | **A** | The lying `archive_learner` was auto-approved: 1 writing tool. **B** and **C** contradict the measurement; **D** is the opposite policy. |
| 8 | **C** | A definition changing after approval means the approved thing is not what runs. **A**, **B** and **D** describe other problems. |
| 9 | **D** | It flags cosmetic edits such as a capitalised title, training users to click through. **A** — hashes are computed locally; **B** is false; **C** inverts the behaviour. |
| 10 | **B** | A wiki server's content named a file server's tool, trying to influence another server's use. **A**, **C** and **D** are unrelated properties. |
| 11 | **C** | Enforcement outside the model decides whether anything actually happens. **A** and **D** are partial mitigations; **B** is a request, not a control. |
| 12 | **A** | Every tool claimed read-only, the host auto-approved on that basis, and no pinning flagged the new sentence. **B**, **C** and **D** were not involved. |

**Q13 rubric (5 marks).** One mark each for: **install-time review** — read full descriptions and schemas (including
parameter descriptions), check names and namespacing, record who publishes the server (§5.1–§5.2); **definition pinning
with material-change re-approval**, showing a diff and classifying cosmetic changes (§5.4); **approval policy that does
not rest on annotations** — explicit allowlists, confirmation for anything that writes or publishes, per-server trust
(§5.3, §6); **runtime handling of results as data** — provenance labels, isolation from instructions, awareness of
cross-server shadowing (§5.5); and **the control that bounds damage** — authorization and least-privilege credentials, with
scanning and logging as tripwires (§5.2, §5.5, M9-L12, M9-L13). An answer relying only on review-at-install scores at
most 2.

---

<a id="m9-l16"></a>
## M9-L16 — Protocol Versions, Compatibility, Server Testing and Deployment

**Answers: B · C · A · D · C · B · D · A · C · D · B · A**

| Q | Ans | Why, and why the distractors fail |
|---|---|---|
| 1 | **B** | `2024-11-05`, `2025-03-26`, `2025-06-18`, `2025-11-25`, `2026-07-28`; only the last uses per-request metadata. **A** and **C** miscount; **D** — the first four are handshake-era. |
| 2 | **C** | The policy sets a minimum twelve-month window. **A** and **B** are shorter than the published minimum; **D** ties removal to a release rather than a duration. |
| 3 | **A** | Roots, Sampling and Logging were deprecated by SEP-2577. **B**, **C** and **D** are active features. |
| 4 | **D** | Future identifiers need not be date-shaped, and unknown strings must compare conservatively — M9-L05 measured `max()` choosing an unsupported version. **A** is false for these strings; **B** and **C** are not guaranteed and do not matter if you intersect. |
| 5 | **C** | The suite reported 24/24. **A** and **B** do not match; **D** is the container check's count. |
| 6 | **B** | Some frames legitimately get no reply; what matters is invalid output and survival. **A**, **C** and **D** would fail on notifications and unreadable fragments. |
| 7 | **D** | Volatile fields cause false alarms on every run. **A**, **B** and **C** are exactly the things you want a diff to reveal. |
| 8 | **A** | Additive and optional changes keep old callers valid. **B**, **C** and **D** each invalidate previously valid calls or results. |
| 9 | **C** | Definitions are cached (`ttlMs`) and may have been approved, so old schemas stay in use after a deploy. **A** is false — versioned names are the recommended route; **B** is false; **D** inverts caching. |
| 10 | **D** | That is `DEFAULT_INHERITED_ENV_VARS` on POSIX, plus anything named explicitly. **A** is a plain `subprocess` default; **B** would break `PATH`; **C** is invented. |
| 11 | **B** | 8/8 checks passed with `--network none`, `--read-only`, `--cap-drop ALL`, non-root. **A** is explicitly denied in the lesson; **C** is disproved by the run; **D** is the opposite of the Dockerfile. |
| 12 | **A** | Statelessness: every request carries its version, capabilities and any handle it needs. **B** is what sticky sessions do; **C** and **D** describe mechanisms 2026-07-28 removed. |

**Q13 rubric (5 marks).** One mark each for: **conformance suite in CI**, run for every supported era and asserting the
negotiated version — catches interop bugs tolerant clients hide (§5.3); **interop against an independent client/SDK** —
catches assumptions your own client shares (§5.3, M9-L09); **fuzzing with survival and output-validity assertions** —
catches crashes and invalid frames from malformed input (§5.4); **golden transcripts with normalised volatile fields** —
catches unintended behaviour changes in a release (§5.5); and **tool-definition compatibility check** — catches breaking
schema changes before cached or approved definitions break hosts (§5.6, §6). Also credit authorization matrix tests,
secret scanning, or image hardening checks in place of one of the above when paired with what it catches.

---

*Module 9 is complete: 16 lessons, each with an executed lab.*