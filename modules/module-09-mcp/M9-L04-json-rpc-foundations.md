# M9-L04 — JSON-RPC 2.0 Foundations

| | |
|---|---|
| **Lesson ID** | M9-L04 |
| **Difficulty** | 2 (Intermediate) |
| **Estimated study time** | 1.75 hours |
| **Prerequisites** | [M2-L11](../module-02-python-foundations/M2-L11-http-rest.md), [M9-L03](M9-L03-three-primitives-tools-resources-prompts.md) |

---

## 1. Learning objectives

1. **Classify** any JSON value as a JSON-RPC request, notification, result response, error response, or
   invalid message, using MCP's stricter rules on top of base JSON-RPC 2.0.
2. **Return** the correct standard error code (`-32700`, `-32600`, `-32601`, `-32602`, `-32603`) for a given
   malformed or failing input.
3. **Explain and measure** why responses must be correlated by `id` rather than by arrival order, and why an
   `id` must not be reused while a request is in flight.
4. **Recognise** the Python-specific trap in which `1`, `1.0` and `True` collide as dictionary keys, and write
   a validator that rejects boolean ids.
5. **State** MCP's position on batches and on responding to notifications.

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **JSON-RPC 2.0** | A small, transport-independent remote-procedure-call format: a caller names a `method`, passes `params`, and gets back a `result` or an `error`. |
| **Request** | A message with `method` and `id`. The receiver MUST answer it with exactly one response carrying the same `id`. |
| **Notification** | A message with `method` and **no** `id`. The receiver MUST NOT answer it. |
| **Result response** | A message with `id` and `result`. In current MCP, `result` always carries `resultType`. |
| **Error response** | A message with `id` and `error: {code, message, data?}`. |
| **Correlation** | Matching a response to the request that caused it — by `id`, never by timing or order. |
| **In flight** | A request that has been sent and has not yet received its response. |
| **Batch** | A JSON array of several messages in one frame. Allowed by JSON-RPC 2.0; **not** allowed by current MCP. |

---

## 3. Plain-language explanation

### 3.1 Why MCP needed an envelope at all

The first three lessons in this module showed that MCP standardizes *how* a host and a server talk, not
*what* either side decides or does. The layer that makes that possible is **JSON-RPC 2.0**, a message
format old enough (2010) to be boring, which is exactly what you want underneath a protocol. MCP did not
invent a message format; it adopted one and tightened a few of its rules.

### 3.2 Four shapes, one question each

Every JSON-RPC message answers one question:

- **"Please do this, and tell me how it went"** is a **request**: `method` + `id`.
- **"FYI, no reply needed"** is a **notification**: `method`, no `id`.
- **"Here's how request N went — it worked"** is a **result response**: `id` + `result`.
- **"Here's how request N went — it failed"** is an **error response**: `id` + `error`.

A message that fits none of these, or two at once, is invalid. §7.1 runs a strict classifier over ten
candidates and shows exactly which rule each invalid one breaks.

### 3.3 The `id` is the only thread connecting a question to its answer

Over a real connection, many requests are in flight at once and a server may finish them in any order.
**The only thing tying a response to its request is the `id`.** §7.3 measured what happens when a client
ignores that and assumes "the next response belongs to the oldest request": with 20 requests in flight and
a server that finishes them in a shuffled order, **19 of 20 requests received someone else's answer**, and
over 1,000 shuffles the average was **95.3%**. The same client passes every test that sends one request at a
time.

### 3.4 Small rules with large consequences

MCP adds three constraints to base JSON-RPC: an `id` is a string or an integer and **never `null`**; an `id`
**must not be reused** while a request with that `id` is still in flight; and there are **no batches** —
one message per frame. §7.4–§7.6 show each rule's failure mode running.

---

## 4. Analogy

**Numbered tickets at a busy deli counter.** You take ticket 47 and order a sandwich (a request). The staff
make sandwiches in whatever order suits the kitchen, and call out "47!" when yours is ready (a response with
`id` 47). If you shouted "I'll just take the next sandwich that comes out," you would regularly walk off with
someone else's lunch — that is §7.3's arrival-order bug. If two people held ticket 47 at once, one would get
the other's order — §7.4. A sign on the counter saying "we close at 6" is a notification: nobody is expected
to reply to it.

### Where the analogy breaks

- **A deli rarely has the same number twice by accident; software does.** A client that restarts its
  counter, or two components sharing one connection with separate counters, reuses ids easily. The protocol
  therefore makes uniqueness the *sender's* responsibility, per connection, for in-flight requests only.
- **Tickets are just numbers; ids have types.** JSON distinguishes the string `"47"` from the integer `47`,
  and they are different ids. Python blurs other distinctions — `47`, `47.0` and even `True == 1` — which the
  deli analogy has no equivalent for (§5.5).

---

## 5. Detailed technical explanation

### 5.1 The message shapes, precisely

`[VERIFIED 2026-09-15 — MCP specification 2026-07-28, Base Protocol]`

```text
Request        {"jsonrpc": "2.0", "id": <string|integer>, "method": <string>, "params"?: {...}}
Notification   {"jsonrpc": "2.0", "method": <string>, "params"?: {...}}            -- no id
Result         {"jsonrpc": "2.0", "id": <same id>, "result": {"resultType": ..., ...}}
Error          {"jsonrpc": "2.0", "id"?: <same id>, "error": {"code": <int>, "message": <string>, "data"?: any}}
```

Rules MCP adds or emphasises on top of JSON-RPC 2.0:

| Rule | Base JSON-RPC 2.0 | MCP (2026-07-28) |
|---|---|---|
| Request `id` type | String, number, or `null` (null discouraged) | String or integer; **MUST NOT be `null`** |
| `id` reuse | Not addressed | **MUST NOT** match any other request the sender has in flight |
| `result` contents | Any value | An object that **MUST** include `resultType` (`"complete"` or `"input_required"`) |
| Batches | Allowed | Not allowed: each stdio line / HTTP POST body is a single message |
| Answering notifications | Forbidden | Forbidden |

`[REAL, measured]` §7.1 classified ten candidates. The four well-formed shapes classified correctly; the
six malformed ones were each rejected with the specific rule broken: `id: null`, `id: true`, `id: 1.5`,
`jsonrpc: "1.0"`, a message with both `result` and `error`, and a batch array.

**`resultType` is new.** It arrived in protocol version 2026-07-28 so that a result can be either final
(`"complete"`) or an interim request for more input (`"input_required"`, covered in M9-L06). Clients MUST
treat a missing `resultType` — which every older server will send — as `"complete"`.

### 5.2 The five standard error codes

JSON-RPC reserves `-32768` to `-32000`. Five codes are defined by JSON-RPC itself:

| Code | Name | Use it when |
|---|---|---|
| `-32700` | Parse error | The frame is not valid JSON |
| `-32600` | Invalid Request | Valid JSON, but not a valid request object (bad `id`, missing `method`, a batch in MCP) |
| `-32601` | Method not found | The `method` is not one this server implements |
| `-32602` | Invalid params | The method exists but its parameters are wrong — in MCP this includes an **unknown tool name** and, since 2026-07-28, a **resource not found** |
| `-32603` | Internal error | Something broke inside the server |

`[REAL, measured]` §7.2 fed seven raw frames through the dispatcher and got exactly one code per failure:
truncated JSON → `-32700` with `id: null`; `id: null` → `-32600`; `tools/delete` → `-32601`; unknown tool
`sub` → `-32602`; wrong argument names → `-32602`; and the notification produced **no response at all**.

Two details are easy to get wrong:

- **An error may omit or null the `id` only when the server could not read it** (the truncated frame). In
  every other case the error carries the request's `id`, or the client cannot tell which request failed.
- **"Unknown tool" is `-32602`, not `-32601`.** The method (`tools/call`) exists; the *parameter* naming
  the tool is invalid. This is the spec's own example.

MCP partitions the remaining server-error range: `-32000…-32019` is legacy and implementation-defined, and
`-32020…-32099` is reserved for codes the MCP specification defines (for example `-32022`
`UnsupportedProtocolVersion`, used in M9-L05). New application-specific codes should be allocated
**outside** `-32768…-32000` entirely.

### 5.3 Correlation by `id`, and why order is worthless

`[REAL, measured]` §7.3 sent 20 requests and let the "server" complete them in a seeded, shuffled order.
Matching by arrival order misrouted **19/20**; matching by `id` misrouted **0/20**. Over 1,000 shuffles,
arrival-order matching misrouted **95.3%** of responses.

That figure is not a coincidence of this dataset. In a random ordering of N items, the expected number that
land in their original position is exactly **1**, whatever N is, so the expected misrouting rate is
`1 − 1/N` — 95% for N = 20. **The bug gets worse as load rises**, and it is invisible at N = 1, which is how
most unit tests run.

The correct client structure is a **pending table** keyed by `id`:

```python
pending: dict[str | int, Future] = {}

def send(request):
    pending[request["id"]] = future = Future()
    transport.write(request)
    return future

def on_message(msg):
    if "id" in msg and ("result" in msg or "error" in msg):
        fut = pending.pop(msg["id"], None)
        if fut is None:
            log.warning("response for unknown or already-cancelled id %r", msg["id"])
        else:
            fut.set_result(msg)
```

### 5.4 Reusing an in-flight `id`

`[REAL, measured]` §7.4 sent two requests with `id: 5` — `add(1, 1)` then `add(40, 2)`. The second
**overwrote** the first in the pending table; the server answered the first request with `"2"`; and the
client reported **2 as the answer to 40 + 2**. No exception was raised anywhere. The first request can never
be resolved and will eventually time out, which is where the bug is usually noticed — far from its cause.

The rule is scoped: an `id` must not be reused **while a request with that `id` is still in flight**. Reusing
an id after its response arrived is legal, but a monotonically increasing counter per connection makes the
question disappear, and is what the official SDKs do.

### 5.5 The Python trap: `True`, `1` and `1.0`

`[REAL, measured]` §7.5 checked four candidate ids — `1`, `1.0`, `True`, `"1"`:

- A naive `isinstance(v, (str, int))` **accepted `True`**, because in Python `bool` is a subclass of `int`.
- Placed as keys in one dict, the four ids produced **2 entries**, not 4: `1`, `1.0` and `True` hash and
  compare equal, so they are the same key.

JSON itself keeps them apart — `true`, `1`, `1.0` and `"1"` are four different JSON values — so a server
written in another language might legitimately treat them as four different ids while a Python client
merges three of them. A strict validator therefore excludes `bool` explicitly and rejects non-integer
numbers:

```python
def valid_id(value) -> bool:
    return isinstance(value, str) or (isinstance(value, int) and not isinstance(value, bool))
```

### 5.6 Batches, and why notifications never get answers

`[REAL, measured]` §7.6 sent a two-request batch; the dispatcher returned `-32600`. **JSON-RPC 2.0 allows
batches. MCP added support in protocol version 2025-03-26 and removed it in 2025-06-18.** Current transports
make the rule structural: a stdio line holds one message and a Streamable HTTP POST body holds one message
(M9-L08).

A deliberately "chatty" server in §7.6 answered three notifications. Every stray response had `id: None`,
matched nothing in the pending table, and would have been handed to real requests by any client that
resolves "the oldest pending request" on receipt of any response. **A notification is fire-and-forget by
definition**; a receiver that answers one is wrong, and a client that does not ignore unmatched responses is
fragile.

### 5.7 Assumptions and limitations

- The lab runs client and server in one process and simulates concurrency by shuffling completion order.
  Real concurrency adds partial frames and interleaving, which transports handle (M9-L08).
- The dispatcher covers only `tools/call`. The full method set and per-request `_meta` are M9-L05 and M9-L06.
- JSON-RPC's `-32000…-32099` sub-allocation is MCP policy as of 2026-07-28; older servers may still emit
  legacy codes such as `-32002` (resource not found), which clients SHOULD still accept.

---

## 6. Worked example — the dashboard that showed the wrong customer's balance

**The situation.** An internal support dashboard called an MCP server's `get_balance` tool for each
customer row on screen. In development, with one test customer, every balance was right. After launch,
support agents reported that balances "shuffled" when they refreshed a page with many rows, and a
customer was told another customer's balance over the phone.

**Investigation, step by step.**

1. The server's logs showed every `tools/call` request and every response with the correct `id` and the
   correct balance for that customer. The server was not the problem.
2. The client used a small hand-written connection class. It kept a Python `list` of outstanding requests
   and, on each incoming response, popped the **first** element — correlation by arrival order (§5.3).
3. With one row, the list never held more than one request. With 30 rows, the server's balance lookups ran
   concurrently against a database with variable latency, so responses returned in a different order from
   the requests.

**Quantifying it before fixing it.** Applying §5.3's result: with N = 30 concurrent requests and an
effectively random completion order, the expected misrouting rate is `1 − 1/30 ≈ 96.7%`. The observed
"shuffling" was not a rare race; it was the normal case at that page size.

**A second bug found in review.** The fix replaced the list with a dict keyed by `id` — and a reviewer
noticed that the dashboard generated ids as `row_index`, restarting at `0` on every page refresh. If an
agent refreshed while the previous page's requests were still in flight, two requests would share id `3`,
reproducing §5.4's overwrite exactly.

| # | Defect | Mechanism | Fix |
|---|---|---|---|
| 1 | Responses matched by arrival order | Concurrent completion order differs from send order | Pending table keyed by `id` (§5.3) |
| 2 | Ids restarted per refresh | An in-flight id reused, overwriting the pending entry | One monotonically increasing counter per connection (§5.4) |
| 3 | Unmatched responses silently accepted | No log when a response matched no pending id | Log and discard unknown ids (§5.6) |

**The general rule.** **A JSON-RPC client that has only ever been tested with one request in flight has not
been tested at all.** Correlation bugs are invisible at N = 1 and near-certain at N = 30.

---

## 7. Practical activity

**File:** [`labs/m9/l04_json_rpc_foundations.py`](../../labs/m9/l04_json_rpc_foundations.py)

**No API key, no network, no third-party dependencies.**

```bash
source .venv/bin/activate
python labs/m9/l04_json_rpc_foundations.py
```

### 7.2 Expected output

`[EXECUTED]` — 2026-09-15, Python 3.12.3 (pure standard library). Run twice; output identical.

```text

============================================================================
1. THE FOUR MESSAGE SHAPES, CLASSIFIED BY A STRICT VALIDATOR
============================================================================
  request                                              <- {"jsonrpc": "2.0", "id": 1, "method": "tools/list"}
  notification                                         <- {"jsonrpc": "2.0", "method": "notifications/cancelled", "par
  result                                               <- {"jsonrpc": "2.0", "id": 1, "result": {"resultType": "comple
  error                                                <- {"jsonrpc": "2.0", "id": 1, "error": {"code": -32601, "messa
  INVALID(bad request id None)                         <- {"jsonrpc": "2.0", "id": null, "method": "tools/list"}
  INVALID(bad request id True)                         <- {"jsonrpc": "2.0", "id": true, "method": "tools/list"}
  INVALID(bad request id 1.5)                          <- {"jsonrpc": "2.0", "id": 1.5, "method": "tools/list"}
  INVALID(jsonrpc must be exactly '2.0')               <- {"jsonrpc": "1.0", "id": 1, "method": "tools/list"}
  INVALID(has both result and error)                   <- {"jsonrpc": "2.0", "id": 1, "result": {}, "error": {"code": 
  INVALID(batch arrays are not allowed in MCP)         <- [{"jsonrpc": "2.0", "id": 1, "method": "tools/list"}]

============================================================================
2. A DISPATCHER THAT RETURNS THE RIGHT STANDARD ERROR CODE
============================================================================
  valid call       -> result id=7: 5
  truncated JSON   -> error -32700 id=None: Parse error
  null id          -> error -32600 id=None: INVALID(bad request id None)
  unknown method   -> error -32601 id=9: Method not found: tools/delete
  unknown tool     -> error -32602 id=10: Invalid params: 'sub'
  wrong arg names  -> error -32602 id=11: <lambda>() got an unexpected keyword argument 'x'
  notification     -> (no response -- notifications are never answered)

  The truncated frame gets id=None: the server could not read the id, so
  it cannot correlate the error with any request. That is the ONLY case
  in which an error response may omit or null the id.

============================================================================
3. CORRELATION: MATCHING RESPONSES BY ARRIVAL ORDER VS BY ID
============================================================================
  20 in-flight requests, responses arriving in a shuffled order:
    client matching by ARRIVAL ORDER : 19/20 requests got someone else's answer
    client matching by ID            :  0/20 requests got someone else's answer

  Over 1000 shuffles, arrival-order matching misrouted 95.3% of responses on average.
  With only ONE request in flight at a time it would never fail -- which is
  why this bug survives every sequential test and appears under load.

============================================================================
4. REUSING AN ID WHILE THE FIRST REQUEST IS STILL IN FLIGHT
============================================================================
  pending table after sending two requests with id=5: {5: {'a': 40, 'b': 2}}
  request silently overwritten and never resolvable: [{'a': 1, 'b': 1}]
  the server answers the FIRST request (1+1) with id 5 -> '2'
  the client resolves it against {'a': 40, 'b': 2} and reports 2 as the answer to 40+2.

============================================================================
5. THE PYTHON TRAP: NAIVE ID CHECKS ACCEPT IDS THAT COLLIDE
============================================================================
  candidate ids:       [1, 1.0, True, '1']
  naive isinstance    : [True, False, True, True]
  strict valid_id()   : [True, False, False, True]
  a dict keyed by these four ids holds 2 entries: {1: 'request sent with id True', '1': "request sent with id '1'"}

  1, 1.0 and True are ONE dict key in Python (they hash and compare equal),
  so a client keyed on raw ids silently merges three different requests.
  '1' stays separate -- a string id and an integer id are distinct in JSON-RPC.

============================================================================
6. BATCHES AND ANSWERED NOTIFICATIONS
============================================================================
  batch of two requests -> {'code': -32600, 'message': 'INVALID(batch arrays are not allowed in MCP)'}
  JSON-RPC 2.0 permits batches; MCP 2025-03-26 briefly supported them and
  2025-06-18 removed them. A current server rejects the array outright.

  a chatty server answered 3 notifications with: [None, None, None]
  Each stray response has id=None, matches no pending request, and a lenient
  client that resolves 'the oldest pending request' on any response would
  hand these empty results to three real requests.

============================================================================
7. WHAT THIS LAB IS AND IS NOT
============================================================================
  REAL: every classification, error code and correlation count above is the
  output of running the validator and dispatcher in this file. Section 3's
  misrouting rate is measured over 1,000 seeded shuffles.

  ILLUSTRATIVE: a single-process 'server'; concurrency is simulated by
  shuffling completion order rather than by real threads.

  NOT SHOWN: the MCP-specific _meta fields every request now carries
  (M9-L05), transport framing over stdio and HTTP (M9-L08), and the
  protocol-level error codes MCP adds in -32020..-32099 (M9-L05, M9-L14).

Done.
```

### 7.3 Reading the result

**Section 1 is a checklist you can reuse.** Every invalid candidate fails for a different, nameable reason.
When you debug a real MCP integration, classify the offending frame against this list before looking
anywhere else.

**Section 3 is the lesson's headline.** 19/20 and 95.3% are not properties of this dataset — they are what
`1 − 1/N` predicts. Correlating by order is not a bug that "sometimes" bites; it bites almost every response
once more than one is in flight.

**Section 5 is language-specific, and that is the point.** JSON keeps `true`, `1`, `1.0` and `"1"` distinct.
Python does not, for three of them. Protocol code sits exactly on this boundary.

---

## 8. Common mistakes and troubleshooting

1. **Correlating responses by order or timing.** §5.3 — measured 95.3% misrouting at N = 20.
2. **Reusing ids across components or after reconnects while requests are still in flight.** §5.4 — the
   earlier request is silently orphaned and the later one receives the wrong answer.
3. **Validating ids with `isinstance(v, int)` in Python.** §5.5 — accepts `True`, and `1`/`1.0`/`True`
   collide as dict keys.
4. **Returning `-32601` for an unknown tool.** §5.2 — the method exists; the tool name is an invalid param,
   so the code is `-32602`.
5. **Answering notifications, or accepting responses that match no pending id.** §5.6.
6. **Sending batches to an MCP server.** §5.6 — removed from MCP in 2025-06-18.

| Symptom | Likely cause | Fix |
|---|---|---|
| Results "shuffle" only under load | Order-based correlation | Key a pending table by `id` |
| A request times out even though the server logged a response | Its `id` was reused and its pending entry overwritten | Per-connection monotonic counter |
| Server rejects every message with `-32600` | `id: null`, wrong `jsonrpc` string, or a batch array | Check §7.1's list |
| Client crashes on a response with `id: null` | A parse error from the server, which could not read the id | Treat as a connection-level error, not a request result |
| Client throws on a result from an older server | Code assumes `resultType` is present | Default a missing `resultType` to `"complete"` |

---

## 9. Security, privacy, reliability, cost

- **Privacy.** A correlation bug delivers one caller's data to another — §6's balances. That is a data
  disclosure incident, not merely a display glitch.
- **Reliability.** Orphaned requests from id reuse surface as timeouts far from their cause (§5.4). Log
  unknown and duplicate ids.
- **Security.** Parse error responses should not echo large portions of the malformed input back; a
  hostile client can use verbose errors to reflect content or probe internals.
- **Cost.** Each misrouted or orphaned request is usually retried, paying for the underlying tool call
  twice.

---

## 10. Exercises

### Exercise 1 — Beginner (~20 min)

1. Write one example of each of the four valid message shapes for a `resources/read` of `orders://O-1001`.
2. Which error code should a server return for: invalid JSON; `method: "tools/delete"`; `tools/call` naming a
   tool that does not exist? Justify each from §5.2.
3. Why does the truncated frame's error response carry `id: null`?
4. What is MCP's rule about reusing an `id`, precisely?
5. What did §7.5 print for the number of dict entries, and why?

### Exercise 2 — Intermediate (~40 min)

1. Run the lab. Change `N` in section 3 to 2, 5, 50 and 200 and record the misrouting rate. Compare each with
   `1 − 1/N`.
2. Add a `-32603` path to `dispatch_raw` by registering a tool that raises `ZeroDivisionError`, and check the
   response keeps the request's `id`.
3. Extend `classify` to reject a request whose `params` is present but is not an object.
4. Rewrite section 4 so the client detects the id collision at send time and raises instead of overwriting.
5. Add `-32002` handling on the client side: accept it from a legacy server and map it to the same
   "resource not found" outcome as `-32602`.

### Exercise 3 — Challenge (~50 min)

1. Implement a thread-based version of section 3 using `concurrent.futures` and a real pending table with
   `threading.Lock`. Confirm zero misroutes at N = 200.
2. Design a property-based test (in words or with `hypothesis`) that would have caught §6's defect 1 without
   knowing about it in advance.
3. A server written in TypeScript assigns meaning to ids `1` and `1.0` separately. Describe a concrete failure
   when a Python client talks to it, and the smallest client change that prevents it.
4. Write a short argument for or against MCP's removal of batching, considering HTTP/2 multiplexing and
   stdio framing.
5. Specify the logging fields you would emit for every unmatched response so that §6 would have been
   diagnosed from logs alone.

---

## 11. Quiz

*(Answers: [`answer-keys/module-09-answers.md`](../../answer-keys/module-09-answers.md#m9-l04).)*

**Q1.** Which message is a valid MCP notification?

- A. `{"jsonrpc": "2.0", "id": null, "method": "notifications/cancelled"}`
- B. `{"jsonrpc": "2.0", "id": 3, "method": "notifications/cancelled"}`
- C. `{"jsonrpc": "2.0", "method": "notifications/cancelled", "params": {"requestId": 3}}`
- D. `{"jsonrpc": "2.0", "result": {}, "method": "notifications/cancelled"}`

**Q2.** A client sends `tools/call` naming a tool the server does not have. Which error code fits?

- A. `-32602` Invalid params
- B. `-32601` Method not found
- C. `-32700` Parse error
- D. `-32603` Internal error

**Q3.** In §7.3, how many of 20 requests did arrival-order matching misroute on the first shuffle?

- A. 0
- B. 10
- C. 1
- D. 19

**Q4.** Why is the expected misrouting rate for order-based correlation close to `1 − 1/N`?

- A. Servers deliberately randomise their response order
- B. A random ordering leaves on average exactly one item in place
- C. JSON parsing reorders keys inside each response object
- D. Each response has a `1/N` chance of being dropped entirely

**Q5.** Which statement about `id` reuse matches MCP's rule?

- A. An id may never be used twice on a connection
- B. Ids must be globally unique across all clients
- C. An id may repeat only if both requests use the same method
- D. An id must not match any request the sender still has in flight

**Q6.** What did §7.5 show about the ids `1`, `1.0`, `True` and `"1"` in a Python dict?

- A. They produced two entries
- B. They produced four entries
- C. They produced one entry
- D. They raised a `TypeError`

**Q7.** When may an error response omit or null the `id`?

- A. Whenever the error code is below `-32000`
- B. When the request was a notification
- C. When the server could not read the id from a malformed message
- D. When the server wants to hide which request failed

**Q8.** What is MCP's current position on JSON-RPC batches?

- A. Required for all list methods
- B. Allowed only over Streamable HTTP
- C. Allowed only for notifications
- D. Not allowed; one message per frame

**Q9.** A server receives a notification and replies with a result. Per §5.6, what is wrong?

- A. Nothing; replies to notifications are optional
- B. Notifications must never be answered, and the reply matches no request
- C. The reply should have used `-32600` instead of a result
- D. The reply must reuse the notification's method name

**Q10.** A current MCP client receives a result without `resultType` from an older server. What must it do?

- A. Treat it as `"complete"`
- B. Reject it as malformed
- C. Treat it as `"input_required"`
- D. Resend the request with a new id

**Q11.** In §6, what made the dashboard bug invisible during development?

- A. The server returned balances in sorted order
- B. The development database had no latency at all
- C. Only one request was ever in flight at a time
- D. The client used string ids in development

**Q12.** Which range does MCP reserve for error codes defined by its own specification?

- A. `-32768` to `-32700`
- B. `-32020` to `-32099`
- C. `-32000` to `-32019`
- D. `-32600` to `-32603`

**Q13.** *(Written, rubric-graded.)* In under 150 words: a teammate's MCP client passes all unit tests but
occasionally shows one user another user's data in production. Using this lesson, describe how you would
confirm or rule out a JSON-RPC correlation defect, and what the fix looks like.

---

## 12. Revision notes

- **Four shapes:** request (`method` + `id`), notification (`method`, no `id`), result (`id` + `result`),
  error (`id` + `error`). Anything else is invalid.
- **MCP tightens JSON-RPC:** ids are strings or integers, never `null`; no in-flight id reuse; no batches;
  results carry `resultType` (absent → `"complete"`).
- **Error codes:** `-32700` parse, `-32600` invalid request, `-32601` method not found, `-32602` invalid
  params (includes unknown tool and resource not found), `-32603` internal. MCP reserves `-32020…-32099`.
- **Correlate by id.** Order-based matching misroutes about `1 − 1/N` of responses — **95.3%** measured at
  N = 20 — and never fails at N = 1.
- **Python trap:** `bool` is an `int`; `1`, `1.0`, `True` are one dict key.
- **Never answer notifications; log and discard responses that match no pending id.**

---

## 13. Completion checklist

- [ ] I can classify any JSON value into one of the four shapes or name why it is invalid.
- [ ] I can pick the right standard error code for a malformed or failing request.
- [ ] I can explain the `1 − 1/N` result and why it hides at N = 1.
- [ ] I can write a pending table keyed by id with a safe id validator.
- [ ] I know MCP's rules on batches, notifications and `resultType`.
- [ ] I scored at least 10/13 on the quiz.

---

## 14. References

- JSON-RPC 2.0 Specification — <https://www.jsonrpc.org/specification> `[STABLE]`
- Model Context Protocol specification, revision 2026-07-28, *Base Protocol* (messages, error-code
  allocation, `resultType`) — <https://modelcontextprotocol.io/specification/2026-07-28/basic>
  `[VERIFIED 2026-09-15]`
- MCP changelog 2026-07-28 (resource-not-found code change, error-code partition) —
  <https://modelcontextprotocol.io/specification/2026-07-28/changelog> `[VERIFIED 2026-09-15]`
- Python data model: `bool` is a subclass of `int`; equal numbers hash equally —
  <https://docs.python.org/3/reference/datamodel.html> `[STABLE]`

---

## 15. Next lesson

→ [M9-L05 — Initialization and Capability Negotiation](M9-L05-initialization-capability-negotiation.md) puts
the envelope to work: how a client and server agree on a protocol version and on what each side can do —
the legacy `initialize` handshake, and the stateless per-request model that replaced it in 2026-07-28.
