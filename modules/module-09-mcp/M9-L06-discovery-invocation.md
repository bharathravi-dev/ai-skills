# M9-L06 — Discovery and Invocation

| | |
|---|---|
| **Lesson ID** | M9-L06 |
| **Difficulty** | 2 (Intermediate) |
| **Estimated study time** | 1.75 hours |
| **Prerequisites** | [M9-L05](M9-L05-initialization-capability-negotiation.md) |

---

## 1. Learning objectives

1. **List** a server's tools, resources, resource templates and prompts correctly across pagination, treating
   cursors as opaque and page size as the server's choice.
2. **Apply** `ttlMs` and `cacheScope` to cache discovery results without serving stale lists or leaking one
   user's list to another.
3. **Explain** why deterministic tool ordering affects LLM prompt-cache hit rates.
4. **Invoke** each primitive — `tools/call`, `resources/read`, `prompts/get` — and interpret its result
   shape, including `-32602` for unknown names, missing arguments and missing resources.
5. **Complete** a multi round-trip request: handle `resultType: "input_required"` by retrying with a new id,
   `inputResponses`, and the echoed `requestState`.

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **Discovery** | Asking a server what it offers: `tools/list`, `resources/list`, `resources/templates/list`, `prompts/list`, and `server/discover`. |
| **Invocation** | Using an offering: `tools/call`, `resources/read`, `prompts/get`. |
| **Cursor** | An opaque string a server returns as `nextCursor`; the client passes it back to get the next page. |
| **`ttlMs`** | A server's hint for how many milliseconds a result may be treated as fresh. |
| **`cacheScope`** | `"public"` (may be shared across callers) or `"private"` (reuse only within the same authorization context). |
| **Resource template** | A URI pattern (RFC 6570), e.g. `orders://{order_id}`, describing a family of resources. |
| **MRTR** | Multi round-trip request: a server returns `resultType: "input_required"` and the client retries with the requested input. |
| **`requestState`** | An opaque string the server includes in an `input_required` result, which the client must echo unchanged on the retry. |

---

## 3. Plain-language explanation

### 3.1 Asking before acting

A host cannot give a model tools it does not know exist, and cannot read a resource whose address it has
never seen. **Discovery** is the host asking a server "what do you offer?"; **invocation** is using one of
those offerings. M9-L03 introduced the three primitives; this lesson is the concrete request-and-response
work of finding and using them.

### 3.2 Lists come in pages, and the server decides the page size

A server with hundreds of tools returns them a page at a time. Each page may include a `nextCursor`; the
client sends it back to get the next page, and **only a missing `nextCursor` means "that's all"**. §7.1
measured four client strategies against a 47-tool server. Only the client that followed `nextCursor` until it
disappeared saw all 47 in both configurations; a client that assumed pages hold 20 tools worked perfectly —
until the server changed its page size to 15, when it silently saw **15 of 47**.

### 3.3 Caching discovery results, and the two ways it goes wrong

Re-listing tools before every model turn wastes round trips, so 2026-07-28 servers attach **`ttlMs`** (how long
the list stays fresh) and **`cacheScope`** (who may share a cached copy). §7.3 showed that a client caching for
the TTL made **3** server fetches instead of **121**, and stayed correct only when it also listened for
change notifications. §7.4 showed the other failure: a per-user tool list mistakenly marked `"public"` let a
shared gateway serve an administrator's tool list to an analyst **3 times** in 5 requests.

### 3.4 Invocation is mostly unsurprising — with one new shape

Calling a tool, reading a resource, or getting a prompt returns a result or a `-32602` error for a bad name or
argument. The new shape in 2026-07-28 is **`input_required`**: a server can answer "I need something first"
(for example, a user's confirmation), and the client retries the same call with the answer. The server keeps
no memory in between — the retry carries everything, including a `requestState` token it must echo back.

---

## 4. Analogy

**A large restaurant menu, a specials board and a waiter who checks with you.** The menu is too long for
one page (pagination); you must turn pages until there are no more, and the number of dishes per page is the
printer's decision, not yours. The specials board says "valid until 3 pm" (`ttlMs`) — you don't re-read it
every minute, but if the waiter announces "the fish is gone" (a list-changed notification) you stop ordering
the fish immediately. A personalised allergy menu printed for one guest (`"private"`) must not be photocopied
for the next table. When you order the steak, the waiter may come back with "how would you like it cooked?"
(`input_required`); you answer, and the order goes through.

### Where the analogy breaks

- **A waiter remembers your table; an MCP server does not.** In the round trip the client must bring back the
  whole order plus the waiter's note (`requestState`) — the server kept nothing between the two requests.
- **Menu page numbers are meaningful; cursors are not.** You may not skip to "page 3" by writing "3"; a cursor
  must be exactly the string the server gave you (§7.1's fabricated cursor was rejected).

---

## 5. Detailed technical explanation

### 5.1 The discovery and invocation methods

`[VERIFIED 2026-09-15 — MCP 2026-07-28 spec pages and mcp-types 2026-07-28 models]`

| Primitive | Discover | Invoke | Paginated | Cacheable |
|---|---|---|---|---|
| Server identity | `server/discover` | — | No | Yes |
| Tools | `tools/list` | `tools/call` | Yes | list only |
| Resources | `resources/list`, `resources/templates/list` | `resources/read` | lists | lists **and** `resources/read` |
| Prompts | `prompts/list` | `prompts/get` | Yes | list only |

A `tools/list` result (2026-07-28):

```json
{"resultType":"complete",
 "tools":[{"name":"get_weather","title":"Weather Information Provider",
           "description":"Get current weather information for a location",
           "inputSchema":{"type":"object","properties":{"location":{"type":"string"}},"required":["location"]}}],
 "nextCursor":"next-page-cursor","ttlMs":300000,"cacheScope":"public"}
```

### 5.2 Pagination rules

- The **cursor is opaque**. Clients MUST NOT parse, modify or construct it, and must not infer anything from
  its value except whether one was provided — an **empty string is a valid cursor**, not the end.
- **Page size is chosen by the server**; clients MUST NOT assume a fixed size.
- Clients SHOULD treat a **missing `nextCursor`** as the end of results.
- An invalid cursor SHOULD produce `-32602`.

`[REAL, measured]` §7.1, 47 tools:

| Client strategy | page size 20 | page size 15 |
|---|---|---|
| Reads the first page only | 20/47 | 15/47 |
| Stops when a page has fewer than 20 items | 47/47 | **15/47** |
| Fabricates cursor `"20"` for the second page | 20/47 (cursor rejected, `-32602`) | 15/47 |
| Follows `nextCursor` until absent | **47/47** | **47/47** |

The second row is the dangerous one: it passes every test written against today's server and breaks on a
server configuration change, with no error — the missing tools simply never appear in the model's context.

### 5.3 Deterministic order and prompt caching

`[REAL, measured]` §7.2: ten `tools/list` calls returning the same 8 tools in arbitrary order produced
**10 distinct serializations**; a stable order produced **1**.

This matters beyond tidiness. Hosts typically place tool definitions at the **start** of the model's context,
and LLM providers' prompt caches (M5-L16) reuse computation only for an **identical prefix**. A server that
reorders tools on each call turns every turn into a full cache miss on the tool block. The 2026-07-28 spec adds
that servers SHOULD return tools in a deterministic order, citing client caching and prompt-cache hit rates.

### 5.4 `ttlMs` and `cacheScope`

`[VERIFIED 2026-09-15 — MCP 2026-07-28, Caching]`

Servers MUST include both fields on `complete` results of `server/discover`, `tools/list`, `prompts/list`,
`resources/list`, `resources/templates/list` and `resources/read`. `input_required` results carry neither, and
results of MRTR retries MUST NOT be cached.

- A result is fresh while `now < t_received + ttlMs`. `ttlMs: 0` means immediately stale; a missing `ttlMs`
  (older servers) SHOULD be treated as `0`.
- TTL is a **freshness hint, not a guarantee**: the server may change the data before it expires. A
  `list_changed` notification (delivered via `subscriptions/listen`, M9-L08) **invalidates** a fresh cache entry.
- Clients SHOULD NOT treat TTL as a polling interval; if they poll anyway they MUST add jitter and backoff.
- The **cache key** is the method plus the parameters that affect the result (e.g. `uri`, `cursor`). Each page
  is cached independently; there is no cross-page consistency guarantee.

`[REAL, measured]` §7.3, 121 moments over 10 minutes, `ttlMs` 300,000, a tool removed at t = 200 s:

| Policy | Server fetches | Uses of a stale list |
|---|---|---|
| Always re-fetch | 121 | 0 |
| TTL + list-changed notifications | **3** | **0** |
| TTL only | 3 | **20** |
| Cache forever | 1 | **81** |

A stale list is not cosmetic: every one of those uses offers the model a tool that no longer exists, and the
resulting `tools/call` fails with `-32602`.

**`cacheScope`.** `"public"` means the result contains no user-specific data and **any** client, gateway or
proxy may serve it to anyone. `"private"` means reuse only within the same authorization context — a different
access token needs a different cache. A `tools/list` MAY vary by the caller's authorization (for example,
filtered by granted scopes), and such a list must be `"private"`.

`[REAL, measured]` §7.4: a per-user tool list marked `"public"` let a shared gateway cache serve the admin's
list (`delete_report`, `export_all_users`) to the analyst **3 times** in 5 requests; marked `"private"`,
**0**. The spec is explicit that servers **MUST NOT rely on `cacheScope` alone** for access control — every
`tools/call` must still be authorised (M9-L13).

### 5.5 Resources, templates and `resources/read`

A `resources/read` result holds a `contents` array; each item has `uri`, optional `mimeType`, and either
`text` or `blob` (base64). Resource **templates** advertise a `uriTemplate` following **RFC 6570**, so clients
can construct addresses for resources that are not enumerated.

`[REAL, measured]` §7.5 expanded `orders://{order_id}` with four values. Plain string replacement produced
`orders://../admin/keys` and `orders://O-1001?export=all` — a value changed the **structure** of the URI.
RFC 6570 simple expansion percent-encodes reserved characters, producing `orders://..%2Fadmin%2Fkeys` and
`orders://O-1001%3Fexport%3Dall`, which remain single, opaque identifiers. Servers must still validate every URI
they receive (M9-L12); correct client expansion prevents accidental structure changes, not attacks.

A resource that does not exist returns **`-32602`** in 2026-07-28 (earlier revisions used `-32002`, which
clients SHOULD still accept).

### 5.6 Prompts and `prompts/get`

`prompts/list` returns each prompt's `name`, optional `title`/`description`, and `arguments`
(`name`, `description`, `required`). `prompts/get` returns `messages`, each with a `role` and a content block.
Prompts are designed to be **user-controlled** — surfaced for a person to pick, like a slash command — rather than
chosen by the model.

`[REAL, measured]` §7.6: `prompts/get` with `ticket_id` returned one user message; without the required
argument it returned `-32602` naming `ticket_id`.

### 5.7 `tools/call` results and the `input_required` round trip

A complete tool result has `content` (text, image, audio, `resource_link`, or embedded `resource` blocks),
optionally `structuredContent` (M9-L07), and `isError` for tool execution failures (M9-L14). An unknown tool
is a protocol error, `-32602`.

**Multi round-trip requests** replace the older pattern in which a server sent its own requests to the client.
`tools/call`, `resources/read` and `prompts/get` may return:

```json
{"resultType":"input_required",
 "inputRequests":{"confirm":{"method":"elicitation/create",
    "params":{"mode":"form","message":"Share report R-12 with maya?","requestedSchema":{...}}}},
 "requestState":"eyJyZXBvcnRfaWQiOiJSLTEyIn0.3f9c..."}
```

The client gathers the input and **retries the original request** with:

- a **new JSON-RPC `id`** (the retry is an independent request; reusing the id is forbidden);
- the original `params`, plus `inputResponses` keyed like `inputRequests`;
- `requestState` echoed **exactly** — clients MUST NOT inspect or modify it, and MUST NOT include one if none
  was given.

`[REAL, measured]` §7.7: the client that echoed `requestState` completed in **2 rounds**; the client that
dropped it was asked again each time and gave up after **3**. The server stored nothing between rounds. Because
`requestState` travels through the client, the server MUST treat it as attacker-controlled and protect its
integrity whenever it affects authorization or business logic — the lab signs it with HMAC, and M9-L13 adds
principal binding and expiry.

### 5.8 Assumptions and limitations

- The lab omits `_meta` validation (M9-L05) and uses simulated time for caching.
- Only level-1 RFC 6570 expansion is shown; real templates may use other operators (`{+path}`, `{?query}`)
  with different encoding rules.
- Subscriptions and change notifications are modelled as an instantaneous invalidation; delivery over a real
  `subscriptions/listen` stream is M9-L08.

---

## 6. Worked example — the assistant that "forgot" half its tools

**The situation.** An internal assistant connected to a company's "ops" MCP server, which exposed about 60 tools
across billing, deployments and incident management. After an ops-server release, users reported that the
assistant "no longer knew how" to roll back deployments. Nobody had touched the assistant.

**Investigation.**

1. `tools/list` called directly from a debugging script returned a first page of **15** tools and a
   `nextCursor`. Before the release, the first page had held 25.
2. The assistant's client code looped `while len(page) == 25`, a condition someone had written after observing
   the server's page size once — §5.2's "assumes a page size" strategy.
3. The rollback tools happened to sort into the second page. From the model's point of view they had simply
   ceased to exist: no error was logged anywhere, because every request had succeeded.

**A second finding.** While fixing pagination, the team noticed the assistant re-listed all 60 tools before
**every** model turn, and the ops server returned them in dictionary-insertion order that changed with each
plugin reload. Latency and model cost had both risen after the assistant launched, and the provider dashboard
showed prompt-cache hits near zero — §5.3's measurement at production scale.

| # | Defect | Mechanism | Fix |
|---|---|---|---|
| 1 | Tools on page 2+ invisible after a server change | Loop condition assumed a fixed page size (§5.2) | Loop until `nextCursor` is absent |
| 2 | Tool list fetched every turn | Ignored `ttlMs` | Cache for `ttlMs`, invalidate on `notifications/tools/list_changed` (§5.4) |
| 3 | Prompt-cache hit rate near zero | Non-deterministic tool order from the server (§5.3) | Server returns tools sorted by name; client also sorts before building context |

**Verification.** After the fix, a test ran the client against a stub server configured with page sizes 1, 7
and 1,000 and asserted the full set of tools was seen each time — the test that would have caught defect 1
before it shipped.

**The general rule.** **Every server-controlled parameter your client silently depends on — page size, order,
freshness — is a future outage.** Follow the protocol's signals (`nextCursor`, `ttlMs`, notifications) rather
than observations of one server on one day.

---

## 7. Practical activity

**File:** [`labs/m9/l06_discovery_invocation.py`](../../labs/m9/l06_discovery_invocation.py)

**No API key, no network, no third-party dependencies.**

```bash
source .venv/bin/activate
python labs/m9/l06_discovery_invocation.py
```

### 7.2 Expected output

`[EXECUTED]` — 2026-09-15, Python 3.12.3 (pure standard library). Run twice; output identical.

```text

============================================================================
1. PAGINATION: CURSORS ARE OPAQUE AND PAGE SIZE IS THE SERVER'S CHOICE
============================================================================
  server page size 20, 47 tools in total:
    client_first_page_only             saw 20/47 tools
    client_assumes_page_size_20        saw 47/47 tools
    client_fabricates_offset_cursor    saw 20/47 tools
    client_follows_next_cursor         saw 47/47 tools
  server page size 15, 47 tools in total:
    client_first_page_only             saw 15/47 tools
    client_assumes_page_size_20        saw 15/47 tools
    client_fabricates_offset_cursor    saw 15/47 tools
    client_follows_next_cursor         saw 47/47 tools

  a fabricated cursor '20' -> {'code': -32602, 'message': 'Invalid params: invalid cursor'}

============================================================================
2. DETERMINISTIC ORDER: WHY THE SAME LIST MUST SERIALIZE THE SAME WAY
============================================================================
  10 tools/list calls, same 8 tools, serialized into the model's context:
    server returning arbitrary order : 10 distinct serializations
    server returning a stable order  : 1 distinct serialization

  Hosts usually place tool definitions at the START of the model's context.
  A provider's prompt cache matches on an identical prefix, so every
  reordering is a cache miss on the entire tool block. The 2026-07-28 spec
  says servers SHOULD return tools in a deterministic order for this reason.

============================================================================
3. ttlMs: FRESHNESS HINTS VS ALWAYS-REFETCH VS CACHE-FOREVER
============================================================================
  121 moments the host needs the list; ttlMs=300000; a tool is removed at t=200s
    always             server fetches: 121   uses of a stale list:  0
    ttl+notifications  server fetches:   3   uses of a stale list:  0
    ttl only           server fetches:   3   uses of a stale list: 20
    forever            server fetches:   1   uses of a stale list: 81

  TTL is a freshness hint, not a guarantee: without the list_changed
  notification the TTL-only client used a stale list until the TTL ran out.

============================================================================
4. cacheScope: A SHARED GATEWAY CACHE AND A PER-USER TOOL LIST
============================================================================
  server marks the per-user list 'public': 3 leak(s) [('analyst', ['delete_report', 'export_all_users'])]
  server marks the per-user list 'private': 0 leak(s) []

  A 'public' result may be served to ANY caller by a shared cache. A list
  that varies by user must be 'private' -- and the server must still check
  authorization on every tools/call, because cacheScope is not a control.

============================================================================
5. RESOURCE TEMPLATES: RFC 6570 EXPANSION VS STRING REPLACE
============================================================================
  value 'O-1001'               naive -> orders://O-1001                RFC 6570 -> orders://O-1001
  value '../admin/keys'        naive -> orders://../admin/keys         RFC 6570 -> orders://..%2Fadmin%2Fkeys
  value 'O-1001?export=all'    naive -> orders://O-1001?export=all     RFC 6570 -> orders://O-1001%3Fexport%3Dall
  value 'O 1001'               naive -> orders://O 1001                RFC 6570 -> orders://O%201001

  resources/read orders://O-1001 -> {"amount": 40.0, "status": "delivered"}
  resources/read orders://O-9999 -> {'code': -32602, 'message': 'Resource not found: orders://O-9999'}
  (2026-07-28 uses -32602 for 'not found'; clients SHOULD still accept a
  legacy server's -32002.)

============================================================================
6. PROMPTS: DECLARED ARGUMENTS ARE CHECKED ON prompts/get
============================================================================
  prompts/get with ticket_id  -> [{'role': 'user', 'content': {'type': 'text', 'text': 'Summarize ticket T-7 in a neutral tone for a manager.'}}]
  prompts/get without it      -> {'code': -32602, 'message': "Invalid params: missing required argument(s) ['ticket_id']"}

============================================================================
7. INVOCATION: AN input_required RESULT AND THE RETRY THAT COMPLETES IT
============================================================================
  client that echoes requestState: rounds [(1, 'input_required'), (2, 'complete')] -> {'report_id': 'R-12', 'shared_with': 'maya'}
  client that drops requestState : rounds [(1, 'input_required'), (2, 'input_required'), (3, 'input_required')] -> gave up

  The server kept no memory between rounds: everything it needed came back
  in the retry. A client that drops requestState is simply asked again.

============================================================================
8. WHAT THIS LAB IS AND IS NOT
============================================================================
  REAL: every count above comes from running the clients against these
  servers: tools seen per pagination strategy, distinct serializations,
  fetches and stale uses per caching policy, gateway leaks, expansions,
  and the input_required round trips.

  ILLUSTRATIVE: time in section 3 is simulated; cursors and requestState are
  signed with a hard-coded lab secret (never do this in a real server).

  NOT SHOWN: per-request _meta (M9-L05), input/output schema validation
  (M9-L07), subscriptions/listen streams over a real transport (M9-L08),
  and requestState replay protection with principal and expiry (M9-L13).

Done.
```

### 7.3 Reading the result

**Section 1's second client is the lesson in miniature.** It is correct at page size 20 and wrong at 15, and
nothing in its output says so.

**Section 3's middle two rows differ only by a notification.** TTL alone controls cost; notifications control
correctness. You usually want both.

**Section 7 shows the protocol's statelessness paying off.** The server needed no session to hold a pending
confirmation, so the retry could have landed on a different server instance.

---

## 8. Common mistakes and troubleshooting

1. **Treating a short page, or an empty-string cursor, as the end of a list.** §5.2 — only an absent
   `nextCursor` ends it.
2. **Constructing, decoding or persisting cursors.** §5.2 — they are opaque and may be signed or version-bound.
3. **Caching without listening for change notifications**, or caching forever. §5.4 — measured 20 and 81 stale
   uses.
4. **Marking per-user results `"public"`.** §5.4 — shared caches may serve them to anyone.
5. **Expanding URI templates with string replacement.** §5.5 — values can change URI structure.
6. **Reusing the JSON-RPC id, or altering `requestState`, on an MRTR retry.** §5.7.
7. **Caching the result of an MRTR retry.** §5.4 — it depends on inputs outside the cache key.

| Symptom | Likely cause | Fix |
|---|---|---|
| Model "loses" tools after a server release | Client stopped paginating early | Follow `nextCursor` until absent |
| `-32602 invalid cursor` on page 2 | Cursor constructed or modified by the client | Pass back the exact `nextCursor` string |
| `-32602` calling a tool the model was just offered | Stale cached list | Honour `ttlMs`, subscribe to `list_changed` |
| Users see tools they cannot use | Per-user list cached as `"public"` | Mark `"private"`; key caches by authorization context |
| A tool call loops on confirmation | `requestState` not echoed or `inputResponses` keys mismatched | Echo exactly; key responses by `inputRequests` keys |

---

## 9. Security, privacy, reliability, cost

- **Privacy.** A mis-scoped cache discloses what another user can do, and for `resources/read`, what they can
  see. Default to `"private"` for anything that depends on the caller (§5.4).
- **Security.** `cacheScope` and filtered lists are conveniences, not controls. Authorise every invocation on the
  server (M9-L13). Treat `requestState` as attacker-controlled (§5.7).
- **Reliability.** Server-controlled page size, order and freshness must never be hard-coded in clients (§6).
- **Cost.** Deterministic ordering plus TTL caching cut both MCP round trips and model prompt cost; §7.3 measured
  121 → 3 fetches.

---

## 10. Exercises

### Exercise 1 — Beginner (~20 min)

1. Name the discovery and invocation method for each of the three primitives.
2. What is the only signal that a paginated list has ended?
3. Which results carry `ttlMs` and `cacheScope`?
4. What must change, and what must stay identical, between an `input_required` response's original request and
   its retry?
5. Why did `orders://../admin/keys` appear in §7.5, and what did RFC 6570 expansion produce instead?

### Exercise 2 — Intermediate (~40 min)

1. Run the lab. Add a page size of 1 and of 100 to section 1 and record each client's count.
2. Make section 3's server remove a tool at t = 590 s and predict each policy's stale-use count before running.
3. Add `resources/templates/list` to the lab, returning `TEMPLATE`, and a client that expands it for three ids.
4. Change `tools_call` in section 7 so that a `"decline"` answer returns a complete result with `isError: true`.
5. Modify section 7's client to reuse `id=1` on the retry. Where would a real server or SDK detect this?

### Exercise 3 — Challenge (~50 min)

1. Implement a client-side cache for `tools/list` keyed by (server, authorization context, cursor) that honours
   `ttlMs`, `cacheScope` and an invalidation callback. Test it against section 4's gateway scenario.
2. Write a property-based test: for any page size from 1 to 50, a correct client sees exactly `ALL_TOOLS`.
3. Design how a host should present a paginated list of 400 tools to a model without exceeding its context
   budget (see M5-L11). Consider server-side search, tool groups, and resources.
4. Tamper with one character of `requestState` in section 7 and confirm rejection; then explain why HMAC alone
   does not prevent another user replaying a captured state.
5. Read the `mcp` 2.2.0 SDK client and find how it paginates `list_tools`. Does it follow §5.2's rules?

---

## 11. Quiz

*(Answers: [`answer-keys/module-09-answers.md`](../../answer-keys/module-09-answers.md#m9-l06).)*

**Q1.** A `tools/list` response has 10 tools and `"nextCursor": ""`. What should the client do?

- A. Stop; an empty cursor marks the end
- B. Stop; ten tools is a full page
- C. Treat the response as malformed
- D. Request the next page with cursor `""`

**Q2.** In §7.1, why did the "stops on a short page" client see 15/47 at page size 15?

- A. The server rejected its cursors
- B. It assumed pages hold 20, so the first page looked like the end
- C. It fabricated an offset cursor
- D. The server returned tools in random order

**Q3.** Why does the 2026-07-28 spec recommend a deterministic tool order?

- A. JSON objects must be sorted
- B. Clients paginate by alphabetical position
- C. Stable order enables caching and prompt-cache hits
- D. Models reject unsorted tool lists

**Q4.** In §7.3, how many stale-list uses did the "TTL only" client make?

- A. 20
- B. 0
- C. 81
- D. 121

**Q5.** A server returns a user-specific `resources/read` result. Which `cacheScope` fits?

- A. `"private"`
- B. `"public"`
- C. Either, since TTL governs sharing
- D. None; `resources/read` is never cacheable

**Q6.** What is the correct role of `cacheScope` in access control?

- A. It replaces per-call authorization
- B. It encrypts cached responses
- C. None; servers must still authorize every call
- D. It limits which tools a model may select

**Q7.** Which expansion of `orders://{order_id}` with `order_id = "a/b"` follows RFC 6570 simple expansion?

- A. `orders://a/b`
- B. `orders://a%2Fb`
- C. `orders://{a/b}`
- D. `orders://a_b`

**Q8.** Under 2026-07-28, what does `resources/read` return for a resource that does not exist?

- A. A result with empty `contents`
- B. `-32601` Method not found
- C. `-32002` Resource not found
- D. `-32602` Invalid params

**Q9.** A `tools/call` returns `resultType: "input_required"`. What must the retry contain?

- A. The same id, with `inputResponses` added to the params
- B. A new id, the original params and a refreshed `requestState`
- C. A new id, original params, `inputResponses`, and the exact `requestState`
- D. Only `requestState`, since the server stored the params

**Q10.** Why did §7.7's server re-ask the client that dropped `requestState`?

- A. It stored nothing between rounds, so the retry lacked context
- B. It rejected the new request id
- C. The elicitation schema was invalid
- D. Its cache had expired

**Q11.** Per M9-L06, who is a prompt primarily designed to be chosen by?

- A. The model, like a tool
- B. The server, on a schedule
- C. The transport layer
- D. The user, like a slash command

**Q12.** In §6, what was the root cause of the assistant losing its rollback tools?

- A. The server removed the rollback tools
- B. The client's loop assumed a fixed page size
- C. The prompt cache had evicted them
- D. The tools had invalid input schemas

**Q13.** *(Written, rubric-graded.)* In under 150 words: design the tool-discovery logic for a host that
connects to several MCP servers and serves many users. Cover pagination, caching and one security concern.

---

## 12. Revision notes

- **Discover** with `tools/list`, `resources/list`, `resources/templates/list`, `prompts/list`
  (and `server/discover`); **invoke** with `tools/call`, `resources/read`, `prompts/get`.
- **Pagination:** cursors are opaque; page size is the server's; only an **absent** `nextCursor` ends a list.
  Measured: only the follow-`nextCursor` client saw 47/47 at both page sizes.
- **Order:** deterministic tool order → stable serialization → prompt-cache hits (10 vs 1 serializations).
- **Caching:** `ttlMs` = freshness hint; notifications invalidate; `"private"` for anything caller-specific.
  Measured 121 → 3 fetches, and 20 stale uses without notifications. `cacheScope` is not access control.
- **Templates:** RFC 6570 expansion percent-encodes values; string replacement can change URI structure.
- **Not found / bad args / unknown names:** `-32602` (accept legacy `-32002` for resources).
- **MRTR:** `input_required` → retry with a **new id**, original params, `inputResponses`, exact `requestState`;
  never cache the retry's result; treat `requestState` as attacker-controlled.

---

## 13. Completion checklist

- [ ] I can list every primitive correctly across pagination.
- [ ] I can cache discovery results with `ttlMs`, notifications and the right `cacheScope`.
- [ ] I can explain deterministic ordering in terms of prompt caching.
- [ ] I can expand a resource template safely and interpret `resources/read` results.
- [ ] I can complete an `input_required` round trip correctly.
- [ ] I scored at least 10/13 on the quiz.

---

## 14. References

- MCP 2026-07-28, *Pagination* — <https://modelcontextprotocol.io/specification/2026-07-28/server/utilities/pagination> `[VERIFIED 2026-09-15]`
- MCP 2026-07-28, *Caching* (`ttlMs`, `cacheScope`, cache keys, pagination interaction) —
  <https://modelcontextprotocol.io/specification/2026-07-28/server/utilities/caching> `[VERIFIED 2026-09-15]`
- MCP 2026-07-28, *Tools* (listing, deterministic order, calling, input-required results) —
  <https://modelcontextprotocol.io/specification/2026-07-28/server/tools> `[VERIFIED 2026-09-15]`
- MCP 2026-07-28, *Multi Round-Trip Requests* — <https://modelcontextprotocol.io/specification/2026-07-28/basic/patterns/mrtr> `[VERIFIED 2026-09-15]`
- `mcp-types` 2026-07-28 models (`Resource`, `ResourceTemplate`, `ReadResourceResult`, `Prompt`, `GetPromptResult`), shipped with `mcp` 2.2.0 `[VERIFIED 2026-09-15]`
- RFC 6570, *URI Template* — <https://www.rfc-editor.org/rfc/rfc6570> `[STABLE]`

---

## 15. Next lesson

→ [M9-L07 — Input and Output Schemas](M9-L07-input-output-schemas.md) looks inside the `inputSchema` and
`outputSchema` every tool definition carries: what they can express, how to validate against them, and what
happens when a server's output quietly drifts from its declared schema.
