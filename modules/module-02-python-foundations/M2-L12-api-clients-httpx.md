# M2-L12 — Calling APIs from Python with httpx (and what an SDK adds)

| | |
|---|---|
| **Lesson ID** | M2-L12 |
| **Difficulty** | 2 (Core) |
| **Estimated study time** | 1.75 hours |
| **Prerequisites** | [M2-L11](M2-L11-http-rest.md), [M2-L08](M2-L08-type-hints-pydantic.md) |

---

## 1. Learning objectives

1. **Make** GET and POST requests with `httpx`, with explicit timeouts and error handling.
2. **Reuse** a client for connection pooling and **explain** the performance difference.
3. **Consume** a streamed response correctly.
4. **Wrap** a raw HTTP call in a typed client with validated responses.
5. **Decide** between a raw HTTP client and a provider SDK, with reasons.

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **`httpx`** | A modern Python HTTP client supporting sync and async with the same API. |
| **`requests`** | The long-standing sync-only HTTP library. Still common. |
| **Client / session** | A reusable object holding connection pools and default settings. |
| **Connection pooling** | Reusing TCP/TLS connections across requests. |
| **Connect timeout** | Maximum time to establish a connection. |
| **Read timeout** | Maximum time waiting for data **between chunks**. |
| **`raise_for_status()`** | Raises an exception for a 4xx/5xx response. |
| **SDK** | A provider-supplied client library wrapping their API. |
| **Base URL** | A prefix applied to every request from a client. |
| **Transport** | The layer that actually sends bytes; replaceable in tests. |
| **`MockTransport`** | An httpx transport that returns canned responses — no network. |

---

## 3. Plain-language explanation

`httpx` is the HTTP client this course uses. It looks like `requests` and adds two things that matter
here: **async support with an identical API** (M2-L13) and **first-class streaming**.

```python
import httpx

response = httpx.get("https://example.com/api/items", timeout=10.0)
response.raise_for_status()
data = response.json()
```

Three habits separate working code from production code:

1. **Always set a timeout.** `httpx` defaults to 5 seconds, which is far too short for an LLM call
   and will silently truncate your work. (`requests` defaults to *no timeout*, which hangs forever —
   worse.)
2. **Reuse a `Client`.** Creating one per request re-does DNS and the TLS handshake every time.
3. **Validate the response body.** A `200` does not mean the JSON has the shape you expect (M2-L11
   §7.3, M2-L08).

### Comparison

| | `requests` | `httpx` |
|---|---|---|
| Sync | ✅ | ✅ |
| Async | ❌ | ✅ same API |
| Default timeout | **None** (hangs forever) | 5 seconds |
| Streaming | Awkward | First-class |
| HTTP/2 | ❌ | Optional |
| Test injection | Needs a library | Built-in `MockTransport` |

This course uses `httpx` throughout. `[VERIFIED 2026-09-08]` — version **0.28.1**, installed and
executed in this environment.

---

## 4. Analogy

**A `Client` is an open phone line; a bare `httpx.get()` is dialling from scratch each time.**

Dialling — DNS lookup, TCP handshake, TLS negotiation — costs real time. Keeping the line open makes
the second call much cheaper.

### Where the analogy breaks

1. **Phone lines are one conversation at a time.** An `httpx.Client` holds a *pool* and can serve
   many concurrent requests.
2. **A line is either up or down. Pooled connections expire silently**, and the client transparently
   redials — so a "reused" connection may not be.
3. **The analogy suggests a client is stateful about your conversation.** It is not. HTTP is
   stateless; the client holds only transport state and defaults (headers, base URL, timeouts).
4. **Phone calls do not have timeouts on each syllable.** HTTP reads do — and for streaming, the
   per-chunk read timeout is the one that matters (M2-L11 §5.5).

---

## 5. Detailed technical explanation

### 5.1 Requests and clients

```python
import httpx

# One-off: opens and closes a connection
response = httpx.get(url, timeout=10.0)

# Reused: pooled connections, shared defaults
with httpx.Client(
    base_url="https://api.example.com",
    headers={"Authorization": f"Bearer {api_key}"},
    timeout=httpx.Timeout(connect=5.0, read=60.0, write=10.0, pool=5.0),
) as client:
    r1 = client.get("/items")
    r2 = client.post("/messages", json=payload)
```

`with` closes the client and releases connections. In a long-running server, create **one client at
startup** and reuse it for the process's lifetime (M2-L15).

### 5.2 Timeouts — four of them

```python
httpx.Timeout(connect=5.0, read=60.0, write=10.0, pool=5.0)
```

| Timeout | Meaning | Typical for an LLM call |
|---|---|---|
| `connect` | Establishing the connection | 5–10 s |
| `read` | Waiting **between chunks** of the response | 60–120 s |
| `write` | Sending the request body | 10 s |
| `pool` | Waiting for a free pooled connection | 5 s |

**`read` is per-chunk, not total.** For streaming that is exactly what you want: it detects a stalled
stream without killing a legitimately long answer (M2-L11 §5.5). If you need an overall cap, enforce
it yourself around the call.

A single number sets all four: `timeout=30.0`.

### 5.3 Errors

```python
try:
    response = client.post("/messages", json=payload)
    response.raise_for_status()
    data = response.json()
except httpx.TimeoutException as exc:        # ambiguous: may have been processed
    ...
except httpx.ConnectError as exc:            # never reached the server
    ...
except httpx.HTTPStatusError as exc:         # 4xx/5xx; exc.response has details
    status = exc.response.status_code
    ...
except httpx.HTTPError as exc:               # base class for all of the above
    ...
```

**`raise_for_status()` is opt-in.** Without it, `httpx` returns the response object for a `500` and
your code carries on with an error page as if it were data.

The exception hierarchy matters for M2-L11's retry rule:

| Exception | Reached the server? | Retryable |
|---|---|---|
| `ConnectError` | **No** | Yes — safe, nothing happened |
| `TimeoutException` | **Unknown** | Yes, but only with an idempotency key for writes |
| `HTTPStatusError` | Yes | Depends on the status code |

That middle row is the M2-L11 §6 case-5 problem, surfaced as a Python type.

### 5.4 Streaming

```python
with client.stream("POST", "/messages", json=payload) as response:
    response.raise_for_status()
    for line in response.iter_lines():
        if line.startswith("data: "):
            event = json.loads(line[6:])
            ...
```

`client.stream(...)` returns a context manager and **does not download the body**. Use
`iter_lines()` for SSE, `iter_bytes()` for binary, `iter_text()` for text.

**Do not call `response.json()` on a streamed response** — the body has not been read, and the
attempt either fails or blocks.

### 5.5 A typed client

Combining M2-L08 with everything above — the pattern used for the rest of this course:

```python
from pydantic import BaseModel

class Message(BaseModel):
    id: str
    text: str
    tokens: int

class ApiError(Exception):
    def __init__(self, status: int, message: str, request_id: str | None) -> None:
        super().__init__(f"{status}: {message} (request_id={request_id})")
        self.status = status
        self.message = message
        self.request_id = request_id
        self.retryable = status in {408, 425, 429, 500, 502, 503, 504, 529}

class MessagesClient:
    def __init__(self, base_url: str, api_key: str, *, timeout: float = 60.0) -> None:
        self._client = httpx.Client(
            base_url=base_url,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=httpx.Timeout(connect=5.0, read=timeout, write=10.0, pool=5.0),
        )

    def create(self, text: str) -> Message:
        response = self._client.post("/messages", json={"text": text})
        request_id = response.headers.get("request-id")
        if response.status_code >= 400:
            body = response.json() if response.content else {}
            raise ApiError(response.status_code,
                           body.get("error", {}).get("message", "unknown"),
                           request_id)
        return Message.model_validate(response.json())

    def close(self) -> None:
        self._client.close()
```

**Five decisions worth noting:**

1. **One `Client`, created once**, reused for every call.
2. **Explicit timeouts**, not defaults.
3. **A domain exception** carrying status, message, request ID **and a `retryable` flag** — so the
   caller decides policy without re-deriving the rule.
4. **The request ID is captured on every path**, success or failure.
5. **The response is validated**, so callers get a typed `Message` rather than a raw dict.

Callers now handle `ApiError`, not `httpx` internals. If you switch HTTP libraries, nothing outside
this class changes.

### 5.6 Testing without a network

```python
def handler(request: httpx.Request) -> httpx.Response:
    return httpx.Response(200, json={"id": "m1", "text": "hi", "tokens": 3})

transport = httpx.MockTransport(handler)
client = httpx.Client(transport=transport, base_url="https://example.test")
```

`MockTransport` intercepts at the transport layer, so **your real client code runs unchanged** —
headers, timeouts, error handling and validation all execute. No network, no keys, no flakiness, and
you can simulate a `429` or a malformed body trivially.

**This is how every API-dependent test in this course works**, and it is why the labs need no
credentials.

### 5.7 Raw client versus SDK

| | Raw `httpx` | Provider SDK |
|---|---|---|
| Learning value | **High** — you see the protocol | Low — it is hidden |
| Retries, backoff | You write them | Usually built in |
| Streaming helpers | Manual SSE parsing | Typed event objects |
| Typed responses | You define them | Provided |
| API changes | You track them | Handled by upgrades |
| Portability | You control it | Locked to that provider |
| Debugging | Everything is visible | Extra layers to read through |

**This course's approach, and the reason for it:** build the raw version first so you understand what
the SDK does, then use the SDK in production. An engineer who has only ever used an SDK cannot debug
a 429 storm, cannot reason about timeout semantics, and cannot port to another provider (M5-L17).

**Use an SDK in production.** It handles retries, protocol versioning and streaming edge cases you
would otherwise reimplement — but keep it behind your own interface (§5.5) so a provider change is a
one-file change.

### 5.8 Assumptions and limitations

- `httpx` 0.28.1 `[VERIFIED 2026-09-08]`. The API is stable but check release notes on upgrade.
- HTTP/2 requires the `http2` extra and is off by default.
- `MockTransport` does not exercise real TLS, DNS or proxies — integration tests still have value.
- Connection pools are per-client; a client per request destroys the benefit.

---

## 6. Worked example — measuring the client-reuse difference

**Version 1 — a new connection every time:**

```python
for i in range(20):
    httpx.get(f"{base}/items/{i}", timeout=10.0)
```

Each iteration: DNS, TCP handshake, TLS handshake, request, response, close. On a real HTTPS endpoint
the TLS handshake alone is typically 50–200 ms.

**Version 2 — one pooled client:**

```python
with httpx.Client(base_url=base, timeout=10.0) as client:
    for i in range(20):
        client.get(f"/items/{i}")
```

One connection setup, twenty requests.

The lab measures this against a local server and finds a **27.9× difference** — 2,053 ms versus
73.6 ms for 50 requests.

Read that number carefully, because it is *not* mostly about the network. On loopback there is no
DNS lookup, no network latency and no TLS handshake. What you are measuring is the raw cost of
opening and tearing down a TCP connection, fifty times instead of once.

Against a real HTTPS provider the gap is **larger**, because each new connection additionally pays
for DNS resolution, a network round trip, and a TLS handshake — typically 50–200 ms on its own.

One caveat on the lab, which is itself instructive: the test server sets `disable_nagle_algorithm`.
Without it, Nagle's algorithm interacting with delayed ACKs adds roughly 40 ms to *every* request on
loopback, which is larger than everything being measured and hides the result entirely. Benchmarks
frequently measure an artefact rather than the thing you care about.

**The production form:**

```python
# module scope or app startup - ONE client for the process
client = httpx.Client(
    base_url=settings.api_base,
    headers={"Authorization": f"Bearer {settings.api_key}"},
    timeout=httpx.Timeout(connect=5.0, read=90.0, write=10.0, pool=5.0),
    limits=httpx.Limits(max_connections=100, max_keepalive_connections=20),
)
```

`limits` caps concurrency so you cannot accidentally open a thousand sockets — which matters once
M2-L13 introduces concurrency.

---

## 7. Practical activity

**File:** [`labs/m2/l12_httpx.py`](../../labs/m2/l12_httpx.py)

**Requires the venv** (`httpx==0.28.1`). Runs a local server, so **no API key and no internet
access** are needed:

```bash
source .venv/bin/activate
python labs/m2/l12_httpx.py
```

Measures pooled versus unpooled requests, demonstrates each timeout, shows the exception hierarchy,
consumes a stream, exercises the typed client from §5.5, and tests it with `MockTransport`.

### 7.1 Important lines

| Construct | Why |
|---|---|
| `httpx.Timeout(connect=..., read=...)` | Separate timeouts; `read` is per-chunk. |
| `client.stream("GET", ...)` | Does not download the body; iterate it. |
| `response.raise_for_status()` | Opt-in; without it a 500 flows on as data. |
| `httpx.MockTransport(handler)` | Tests the real client code with no network. |
| `httpx.Limits(max_connections=...)` | Caps concurrency. |

### 7.2 Expected output

`[EXECUTED]` 2026-09-08 with httpx 0.28.1, Python 3.12.3. Ports and timings vary:

```
==========================================================================
HTTP CLIENTS WITH httpx
==========================================================================
httpx version 0.28.1; local server on http://127.0.0.1:44819

--------------------------------------------------------------------------
1. CONNECTION POOLING - reuse one client
--------------------------------------------------------------------------
  50 requests, new connection each time :  1999.2 ms
  50 requests, one pooled client        :    74.0 ms
  speed-up                               : 27.0x

  What you are seeing is the cost of CONNECTION SETUP, repeated 50
  times versus paid once. Even on loopback - no DNS, no network
  latency, no TLS - it dominates.

  Against a real HTTPS provider the gap is LARGER still, because
  each new connection also pays for a DNS lookup, a network
  round trip, and a TLS handshake (typically 50-200 ms on its own).
  None of those appear in this local measurement.

--------------------------------------------------------------------------
2. TIMEOUTS AND THE EXCEPTION HIERARCHY
--------------------------------------------------------------------------
  scenario                          exception               reached server?
  read timeout (server too slow)    ReadTimeout             unknown
  connect error (port closed)       ConnectError            NO - safe to retry
  500 without raise_for_status      (no exception)          yes
    -> status_code=500, body flows on as data: {'error': {'message': 'internal error'}}
  500 with raise_for_status         HTTPStatusError         yes
    -> retryable? True

  The exception TYPE answers the retry question:
    ConnectError      -> never reached the server. Always safe.
    TimeoutException  -> UNKNOWN. May have been processed. For a
                         write, retry only with an idempotency key.
    HTTPStatusError   -> reached it; decide from the status code.

--------------------------------------------------------------------------
3. STREAMING
--------------------------------------------------------------------------
  status 200 received after 10 ms (before ANY text was generated)
  chunks              : 5
  text                : 'Refunds take five business days.'
  time to first chunk : 11 ms
  total time          : 263 ms
  perceived wait is the FIRST number, not the second.

--------------------------------------------------------------------------
4. A TYPED CLIENT
--------------------------------------------------------------------------
  create() -> Message(id='msg_1', text='Refund my order please', tokens=4)
    type    : Message (validated, not a raw dict)
    tokens  : 4 (int)

  A malformed response is caught at the boundary:
    ('text',): Field required
    ('tokens',): Field required
    The server returned HTTP 200. Only validation caught it.

--------------------------------------------------------------------------
5. MockTransport - testing the real client with no network
--------------------------------------------------------------------------
  success path -> Message(id='msg_mock', text='mocked', tokens=1)
  429 path     -> ApiError status=429 retryable=True request_id=req_mock_429

  requests actually made: 2
    POST /messages  Authorization=***REDACTED***
    POST /other  Authorization=***REDACTED***

  The real client ran unchanged: same headers, same timeouts, same
  error handling, same Pydantic validation. No network, no key, no
  flakiness - and a 429 was trivial to simulate.

==========================================================================
```

### 7.3 Reading the result

**Section 2 is the table to memorise**, because it maps a Python exception type onto a retry
decision:

| Scenario | Exception | Reached the server? | Safe to retry? |
|---|---|---|---|
| Server too slow | `ReadTimeout` | **Unknown** | Only with an idempotency key, for writes |
| Port closed | `ConnectError` | **No** | Always |
| 500, no `raise_for_status()` | *none* | Yes | — but you never noticed |
| 500, with `raise_for_status()` | `HTTPStatusError` | Yes | Check the code — here, `True` |

The third row is the one that costs people time. `httpx` returned an ordinary response object with
`status_code=500`, and the lab's next line shows the error body **flowing on as data**:
`{'error': {'message': 'internal error'}}`. Nothing raised. Nothing warned. Downstream code receives
a dict and carries on.

**Section 3 shows why streaming is a UX decision.** The status arrived in 10 ms, the first chunk in
11 ms, and the complete answer in 263 ms. The user perceives **11 ms**, not 263 ms. Scale those
proportions to a real model — first token in ~400 ms, full answer in 15 seconds — and streaming
removes roughly 97% of the perceived wait without making anything faster.

Note also that the status arrived **before any text was generated**, which is M2-L11 §5.5 restated:
`200` on a stream means only that the stream started.

**Section 4 catches a failure that HTTP could not.** The server returned `200` with
`{"id": "msg_2"}` — valid HTTP, valid JSON, missing two required fields:

```
('text',): Field required
('tokens',): Field required
```

`raise_for_status()` would have passed this. `response.json()` would have passed it. Only the
Pydantic model caught it, at the boundary, naming both missing fields. This is the M2-L08 argument
arriving in real client code.

**Section 5 is how every API-dependent test in this course works.** The same `MessagesClient` ran
against `MockTransport` — real headers, real timeouts, real error handling, real validation — and a
`429` with a `Retry-After` was simulated in three lines. No network, no key, no flakiness, and the
`ApiError` correctly reported `retryable=True` and carried the request ID.

The redaction line is worth noting too: the recorded requests show
`Authorization=***REDACTED***`, because even test output is somewhere a credential can leak.

**Verification:** confirm the pooling speed-up is large (order of 20×+), that `ConnectError` is
labelled safe to retry while `ReadTimeout` is `unknown`, and that the malformed-response test reports
two missing fields.

---

## 8. Common mistakes and troubleshooting

1. **No explicit timeout.** `httpx` defaults to 5s (too short for LLMs); `requests` defaults to
   forever.
2. **A new `Client` per request.** Destroys pooling.
3. **Forgetting `raise_for_status()`.**
4. **Calling `.json()` on a streamed response.**
5. **Not closing the client** — leaks connections.
6. **Catching `Exception` instead of the `httpx` hierarchy.**
7. **Retrying a timed-out `POST` without an idempotency key.**
8. **Not validating the response body.**
9. **Logging the whole request, including `Authorization`.**

| Error | Cause | Fix |
|---|---|---|
| `httpx.ReadTimeout` | Response slower than `read` | Raise `read`; check for a stalled stream |
| `httpx.ConnectTimeout` | Cannot reach the host | Check DNS, network, base URL |
| `httpx.ConnectError` | Refused / unreachable | Server down or wrong port |
| `httpx.HTTPStatusError` | 4xx/5xx after `raise_for_status()` | Inspect `exc.response` |
| `json.JSONDecodeError` on `.json()` | Body is not JSON (HTML error page) | Check `Content-Type` first |
| `RuntimeError: Attempted to read...` | `.json()` on a stream | Use `iter_lines()` |
| Slow under load | New client per request | Reuse one client |
| `PoolTimeout` | All pooled connections busy | Raise `limits` or reduce concurrency |

---

## 9. Security, privacy, reliability and cost

- **Security.** Put credentials in client `headers` once, never in URLs. Never log the client's
  header dict without redaction (M2-L11 §7.3). Verify TLS — never set `verify=False` outside a
  controlled test.
- **Privacy.** `httpx` event hooks can log every request and response. Convenient and dangerous:
  bodies contain user data. Log status, request ID, duration and token counts, not bodies.
- **Reliability.** The exception type tells you whether the request reached the server, which
  determines whether a retry is safe. `ConnectError` is always safe to retry; `TimeoutException` is
  not, for writes.
- **Cost.** Connection reuse reduces latency, not spend. But a retried `POST` that already succeeded
  is billed twice — the reliability and cost arguments point the same way.

---

## 10. Exercises

### Exercise 1 — Beginner (~15 min)

1. Make a GET to the lab's server with a 0.001 s timeout and record the exception type.
2. Make a request to a closed port and record the exception type. How does it differ from #1, and
   why does that difference matter for retries?
3. Call an endpoint returning `500` with and without `raise_for_status()`. Show what your code does
   in each case.

### Exercise 2 — Intermediate (~30 min)

Build a `TicketApiClient` with:

- One reusable `httpx.Client` with explicit four-part timeouts.
- `get_ticket(ticket_id) -> Ticket` returning a validated Pydantic model.
- `create_ticket(text) -> Ticket` sending JSON.
- A domain `ApiError` carrying status, message, request ID and a `retryable` flag.
- A `close()` method, and support for use as a context manager.

Then write five tests using `MockTransport` covering: success, `404`, `429` with `Retry-After`, a
malformed body that fails validation, and a connection error. **No network.**

### Exercise 3 — Challenge (~30 min)

1. Measure pooled versus unpooled for 50 requests against the lab server. Report both and the ratio.
2. Explain why this local measurement *understates* the real-world benefit. Name the three costs a
   local test does not include.
3. Consume the lab's streaming endpoint and print the time of each chunk's arrival. Compute time to
   first chunk and total time, and explain what a user perceives.
4. Set `read=0.05` against the streaming endpoint (which sleeps 0.05 s between chunks) and observe
   what happens. Explain why a per-chunk read timeout is the right semantics for streaming.
5. Write an event hook logging method, URL, status and duration for every request — with headers
   redacted. Show it working.

---

## 11. Quiz

**Q1.** What is `httpx`'s default timeout, and why must you override it for LLM calls?

- A. No timeout; override to avoid hangs.
- B. 5 seconds — far shorter than an LLM response often takes, so requests are cut off mid-generation.
- C. 60 seconds; no override needed.
- D. 30 seconds.

**Q2.** Why reuse a single `httpx.Client`?

- A. It uses less memory.
- B. It pools connections, so DNS resolution and the TCP/TLS handshake are not repeated for every
  request.
- C. It is required by the API.
- D. It enables retries.

**Q3.** What does `read` timeout mean for a streaming response?

- A. Total time for the whole response.
- B. Maximum time to wait between chunks, which detects a stalled stream without killing a
  legitimately long answer.
- C. Time to read the headers.
- D. Time to establish the connection.

**Q4.** Which exception means the request definitely never reached the server?

- A. `httpx.TimeoutException`  B. `httpx.ConnectError`  C. `httpx.HTTPStatusError`
- D. `httpx.ReadTimeout`

**Q5.** Why is `httpx.TimeoutException` dangerous to retry blindly on a `POST`?

- A. It is slow.
- B. The server may have processed the request before the response was lost, so a retry can duplicate
  the effect — unless an idempotency key is used.
- C. It always means failure.
- D. Timeouts cannot be retried.

**Q6.** What happens if you omit `raise_for_status()`?

- A. The library raises anyway.
- B. A 4xx/5xx response is returned as an ordinary response object, and your code proceeds using an
  error body as if it were data.
- C. The request is retried.
- D. The response is empty.

**Q7.** What does `httpx.MockTransport` give you?

- A. A fake server process.
- B. Interception at the transport layer, so your real client code — headers, timeouts, error
  handling, validation — runs unchanged with no network.
- C. Automatic retries.
- D. Response caching.

**Q8.** Why does this course teach raw `httpx` before provider SDKs?

- A. SDKs are unreliable.
- B. So you understand the protocol underneath — retries, timeouts, streaming and status semantics —
  which you need to debug and to port between providers.
- C. SDKs cost money.
- D. `httpx` is faster.

**Q9.** Why keep an SDK behind your own client interface?

- A. It is faster.
- B. So a provider change, or a switch back to raw HTTP, is a one-file change rather than a
  refactor across the codebase.
- C. SDKs require it.
- D. To avoid installing dependencies.

**Q10.** *(Written, rubric-graded.)* In under 80 words, explain why a local benchmark understates the
benefit of connection pooling.

---

## 12. Revision notes

- **Always set explicit timeouts.** `httpx` defaults to 5 s; `requests` to none. Four parts:
  `connect`, **`read` (per-chunk)**, `write`, `pool`.
- **One `Client` per process**, not per request. Add `limits` to cap concurrency.
- **`raise_for_status()` is opt-in.** Without it a 500 flows on as data.
- Exception hierarchy tells you retry safety: **`ConnectError`** never reached the server (safe);
  **`TimeoutException`** is ambiguous (needs an idempotency key for writes); **`HTTPStatusError`**
  depends on the code.
- **`client.stream(...)`** does not download the body — iterate `iter_lines()`. Never `.json()` a
  stream.
- **Wrap the API in a typed client**: one client, explicit timeouts, a domain exception carrying
  status + message + request ID + `retryable`, and a validated Pydantic response.
- **`MockTransport`** tests real client code with no network, no keys, no flakiness.
- **Learn raw HTTP, ship the SDK — behind your own interface.**

---

## 13. Completion checklist

- [ ] I always set explicit four-part timeouts.
- [ ] I reuse one client and measured the difference.
- [ ] I can name which exception means "never reached the server".
- [ ] I built a typed client with a domain exception carrying a request ID.
- [ ] I tested it with `MockTransport` and no network.
- [ ] I consumed a stream with `iter_lines()`.
- [ ] I can argue for raw HTTP as a learning step and an SDK in production.
- [ ] I scored 7/10 on the quiz.

---

## 14. References

- httpx documentation. <https://www.python-httpx.org/> `[UNVERIFIED]` link not re-checked;
  version 0.28.1 `[VERIFIED 2026-09-08]` by installation and execution here.
- httpx advanced usage — clients, timeouts, transports.
  <https://www.python-httpx.org/advanced/> `[UNVERIFIED]`

---

## 15. Next lesson

→ [M2-L13 — Async and Concurrency](M2-L13-async-concurrency.md)

You can make one call correctly. Next: making a hundred at once — when that helps, when it does not,
and the mistakes that make async slower than the synchronous version.
