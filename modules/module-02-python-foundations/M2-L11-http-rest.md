# M2-L11 — HTTP and REST: Methods, Headers, Status Codes, Auth

| | |
|---|---|
| **Lesson ID** | M2-L11 |
| **Difficulty** | 1 (Intro) |
| **Estimated study time** | 1.75 hours |
| **Prerequisites** | [M2-L01](M2-L01-setup-terminal-venv-pip.md) |

---

> You already know HTTP from web development. This lesson makes precise the parts that matter for
> **AI provider APIs specifically**: streaming responses, long-running requests, rate-limit headers,
> idempotency, and the difference between retryable and non-retryable failures. Skim §3–§5.2, read
> §5.3 onward carefully.

---

## 1. Learning objectives

1. **Choose** the correct method and status code for an operation, and **explain** idempotency.
2. **Read** an HTTP response and decide whether a failure is retryable.
3. **Distinguish** authentication from authorization, and **name** the header each uses.
4. **Explain** how streaming responses work and why AI APIs use them.
5. **Interpret** rate-limit headers and the difference between 429 and 503.

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **HTTP** | The request/response protocol of the web. |
| **Method / verb** | `GET`, `POST`, `PUT`, `PATCH`, `DELETE`. |
| **Idempotent** | Repeating the request has the same effect as making it once. |
| **Safe method** | Does not change server state. `GET`, `HEAD`. |
| **Status code** | A three-digit result code. |
| **Header** | A key–value pair carrying metadata. |
| **Body / payload** | The data sent or returned. |
| **Content-Type** | The body's media type, e.g. `application/json`. |
| **Authentication** | Proving *who* you are. |
| **Authorization** | Deciding *what you may do*. |
| **Bearer token** | A credential sent as `Authorization: Bearer <token>`. |
| **REST** | An architectural style using URLs as resources and methods as operations. |
| **SSE** | Server-Sent Events — a streaming response format used by most LLM APIs. |
| **Idempotency key** | A client-supplied ID letting a server de-duplicate retried requests. |
| **TTFB** | Time To First Byte. Critical for streaming UX. |

---

## 3. Plain-language explanation

A request has: a **method**, a **URL**, **headers**, and optionally a **body**. A response has: a
**status code**, **headers**, and a **body**.

```
POST /v1/messages HTTP/1.1
Host: api.example.com
Content-Type: application/json
Authorization: Bearer sk-...
x-api-version: 2026-01-01

{"model": "claude-sonnet-5", "messages": [{"role": "user", "content": "Hi"}]}
```

```
HTTP/1.1 200 OK
Content-Type: application/json
request-id: req_01H8X...
anthropic-ratelimit-requests-remaining: 49

{"content": [{"type": "text", "text": "Hello!"}], "usage": {...}}
```

Two things that differ from typical web APIs and matter enormously here:

1. **Requests are slow.** A CRUD API responds in tens of milliseconds. An LLM request can take
   30–120 seconds. Every default timeout you have ever used is wrong for this.
2. **Responses are often streamed.** Instead of waiting for the whole answer, tokens arrive as they
   are generated. This changes error handling fundamentally — a stream can fail *after* you have
   already shown the user half an answer.

---

## 4. Analogy

**HTTP is the postal system.** The method is the kind of item (letter, parcel, collection request),
the URL is the address, headers are what is written on the envelope, and the body is inside.

### Where the analogy breaks

1. **Post is one-way; HTTP is a round trip** with a status code, which is the part you must actually
   act on.
2. **Post is not idempotent.** Sending two identical parcels delivers two parcels. HTTP `PUT` and
   `DELETE` are *defined* to be idempotent, and this is what makes safe retries possible (§5.2).
3. **A letter arrives whole. A streamed response arrives in pieces**, and may fail halfway — a
   situation with no postal equivalent and real consequences (§5.5).
4. **Stateless.** Every request carries everything the server needs. There is no memory between
   requests — which is exactly why you resend the whole conversation to an LLM every turn (M4-L16).

---

## 5. Detailed technical explanation

### 5.1 Methods

| Method | Purpose | Safe | Idempotent | Body |
|---|---|---|---|---|
| `GET` | Retrieve | ✅ | ✅ | No |
| `HEAD` | Headers only | ✅ | ✅ | No |
| `POST` | Create / invoke | ❌ | **❌** | Yes |
| `PUT` | Replace at a known ID | ❌ | ✅ | Yes |
| `PATCH` | Partial update | ❌ | ❌ (usually) | Yes |
| `DELETE` | Remove | ❌ | ✅ | No |

**`POST` is not idempotent, and this is the crux of retry safety.** If a `POST` times out you do not
know whether the server processed it. Retrying may create a duplicate. This is why LLM APIs — which
use `POST` and frequently time out — need care, and why M8-L12 devotes a whole lesson to idempotency
for agent actions.

### 5.2 Status codes

| Range | Meaning | Retry? |
|---|---|---|
| `2xx` | Success | — |
| `3xx` | Redirect | Follow |
| `4xx` | **Your** mistake | **No** — except `408`, `425`, `429` |
| `5xx` | **Server's** problem | **Usually yes** |

The ones you will actually handle:

| Code | Meaning | Retryable | Action |
|---|---|---|---|
| `200` | OK | — | — |
| `201` | Created | — | — |
| `400` | Bad request — malformed | **No** | Fix the request |
| `401` | Unauthenticated — bad/missing credential | **No** | Fix the key |
| `403` | Authenticated but **not permitted** | **No** | Fix permissions |
| `404` | Not found | No | Check the URL/ID |
| `409` | Conflict | No | Resolve and retry deliberately |
| `413` | Payload too large | No | Send less — often a too-long prompt |
| `422` | Semantically invalid | No | Fix the fields |
| `429` | **Rate limited** | **Yes, after waiting** | Honour `Retry-After` |
| `500` | Server error | Yes | Backoff |
| `502` / `504` | Gateway / timeout | Yes | Backoff |
| `503` | Service unavailable / overloaded | **Yes** | Backoff |

**The `401` vs `403` distinction is worth internalising:** `401` means *"I do not know who you are"*;
`403` means *"I know who you are and you may not do this"*. Retrying `401` with the same key is
pointless. This is the authentication/authorization split, made visible in the protocol — and it
recurs as a design principle in M9-L10 and M9-L13.

**The rule to remember: `4xx` means stop and fix; `5xx` and `429` mean wait and retry.** Retrying a
`400` forever is a real and common bug, and it burns quota while achieving nothing.

### 5.3 Headers that matter for AI APIs

**Request:**

| Header | Purpose |
|---|---|
| `Authorization: Bearer <token>` | The credential. Never log it. |
| `Content-Type: application/json` | Body format |
| `Accept: text/event-stream` | Request a streamed response |
| `Idempotency-Key: <uuid>` | Lets the server de-duplicate retries |
| `User-Agent` | Identify your client; helps providers help you |

**Response:**

| Header | Purpose |
|---|---|
| `request-id` | **Log this always.** It is what support will ask for |
| `Retry-After` | Seconds (or a date) to wait before retrying |
| `*-ratelimit-limit` / `-remaining` / `-reset` | Your current quota position |
| `Content-Type` | `application/json` or `text/event-stream` |

**Logging the request ID on every call is the single highest-value operational habit** in this
lesson. When a provider behaves oddly, a request ID turns a week of speculation into a support ticket
they can answer.

Header names are **case-insensitive**. Values are strings, always.

### 5.4 Authentication versus authorization

| | Authentication | Authorization |
|---|---|---|
| Question | Who are you? | What may you do? |
| Failure | `401` | `403` |
| Carried by | `Authorization` header, cookie, mTLS | Server-side policy |

Note the historical wart: the header is called `Authorization` but carries **authentication**. Do not
let the name confuse the concepts.

**Common schemes:** API key (`Bearer sk-...`) — simple, long-lived, high blast radius if leaked.
OAuth 2.0 access token — short-lived, scoped, refreshable (M9-L11). mTLS — both sides present
certificates.

**The principle that carries through this whole course:** authorization is decided **server-side**,
never by the client and never by a model. A client can be modified; a model can be talked into
anything. M2-L02 §9, M7-L15, M8-L16 and M9-L13 all restate this.

### 5.5 Streaming

A normal response arrives once, complete. A streamed response arrives in chunks as they are produced.

**Server-Sent Events (SSE)** is the format most LLM APIs use:

```
Content-Type: text/event-stream

event: message_start
data: {"type":"message_start","message":{"id":"msg_01..."}}

event: content_block_delta
data: {"type":"content_block_delta","delta":{"type":"text_delta","text":"Hel"}}

event: content_block_delta
data: {"type":"content_block_delta","delta":{"type":"text_delta","text":"lo"}}

event: message_stop
data: {"type":"message_stop"}
```

Lines beginning `data:` carry JSON; a blank line ends an event.

**Why AI APIs stream:** a 500-token answer might take 15 seconds to complete but produce its first
token in 400 ms. Streaming reduces *perceived* latency by roughly 97% without making anything faster.
That is a UX decision with real product consequences (M5-L09).

**Three consequences that catch people:**

1. **You get `200 OK` immediately, before the work succeeds.** The status code no longer tells you
   the request worked. A stream can carry an error event, or simply stop, after a successful status.
2. **Partial output is a real state.** The user has seen half an answer when the connection drops.
   You must decide: show it, discard it, or retry — and retrying produces a *different* answer
   (M1-L10).
3. **Timeouts must be per-chunk, not per-request.** A total-duration timeout either kills long
   legitimate answers or fails to detect a stalled stream. You want "no data for N seconds"
   (M2-L14).

### 5.6 Idempotency keys

Because `POST` is not idempotent and retries are unavoidable:

```
POST /v1/orders
Idempotency-Key: 7f3c1e88-...
```

The server records the key with its result. A retry with the same key returns the original result
rather than acting twice. **The client generates the key once, before the first attempt, and reuses
it for every retry** — generating a new key per attempt defeats the entire mechanism.

Not every API supports this. When one does not, you need your own de-duplication (M8-L12).

### 5.7 Assumptions and limitations

- REST conventions are conventions. Real APIs deviate; read the provider's documentation.
- Status codes are advisory: some APIs return `200` with an error in the body. Check the body too.
- `Retry-After` may be seconds or an HTTP date. Handle both.
- Rate-limit header names are **not standardised** across providers.

---

## 6. Worked example — classifying failures

You call an LLM API 1,000 times and see six distinct failures. For each, decide: retry or not, and
what to do.

| # | Response | Retry? | Why | Action |
|---|---|---|---|---|
| 1 | `401` `{"error":{"type":"authentication_error"}}` | **No** | Bad credential. Retrying cannot change it | Fail fast at startup; check the env var |
| 2 | `429` + `Retry-After: 12` | **Yes** | Rate limited — a temporary quota state | Sleep 12s, retry. Consider client-side throttling |
| 3 | `400` `{"error":{"message":"max_tokens: must be <= 8192"}}` | **No** | Your request is malformed | Fix the code. Log at ERROR |
| 4 | `529` / `503` overloaded | **Yes** | Provider capacity, transient | Exponential backoff with jitter (M2-L14) |
| 5 | Connection reset after 45s, no status | **Yes, carefully** | Unknown whether the server processed it | Retry with the same idempotency key if supported |
| 6 | `200` then the stream stops mid-sentence | **Judgement** | Partial output already shown to the user | See below |

**Case 5 is the interesting one.** A timeout is ambiguous: the request may have been fully processed
and the response lost. For a read this is harmless. For anything that charges money or changes state,
a blind retry is a duplicate. This is precisely why idempotency keys exist and why M8-L12 treats
duplicate-action prevention as a first-class agent concern.

**Case 6 has no universally right answer**, and the reasoning matters more than the choice:

- *Discard and retry:* the user sees the answer restart, and the second answer differs from the first
  (sampling, M1-L10). Confusing, but complete.
- *Keep the partial:* fast, but you have shown a truncated answer that may be misleading — a
  half-sentence can invert a meaning.
- *Keep it and mark it incomplete:* usually best. Show what arrived, label it clearly, offer a retry.

The professional move is to **decide this deliberately and write it down**, because the default —
whatever your HTTP library happens to do — is almost certainly not what you want.

**And the classification rule that falls out:**

```python
RETRYABLE_STATUS = {408, 425, 429, 500, 502, 503, 504, 529}

def is_retryable(status: int | None) -> bool:
    if status is None:          # connection error, no response
        return True
    return status in RETRYABLE_STATUS
```

You will implement exactly this in M2-L14.

---

## 7. Practical activity

**File:** [`labs/m2/l11_http.py`](../../labs/m2/l11_http.py)

```bash
python3 labs/m2/l11_http.py
```

Standard library only, and **no network access required** — it runs a tiny local HTTP server on a
random port that deliberately returns 200, 401, 403, 429 with `Retry-After`, 500 and a streamed SSE
response, then a client that classifies each. You see real requests and real responses without
needing an API key.

### 7.1 Important lines

| Construct | Why |
|---|---|
| `http.server.ThreadingHTTPServer` | A real server, so the requests are genuine. |
| `urllib.request.urlopen` | Standard-library client. `httpx` comes in M2-L12. |
| `HTTPError.code` / `.headers` | Reading the status and headers from a failure. |
| `response.readline()` in a loop | Consuming a stream chunk by chunk rather than all at once. |
| `is_retryable(status)` | The §6 rule, applied. |

### 7.2 Expected output

`[EXECUTED]` 2026-09-08, Python 3.12.3. The port and timings vary; everything else is deterministic:

```
==========================================================================
HTTP: STATUS CODES, HEADERS, STREAMING AND IDEMPOTENCY
==========================================================================
Local test server running on http://127.0.0.1:41893

--------------------------------------------------------------------------
1. STATUS CODES AND RETRY CLASSIFICATION
--------------------------------------------------------------------------
  route               status  retry?   Retry-After  detail
  /ok                 200     no       -            
  /bad-request        400     no       -            max_tokens: must be <= 8192
  /unauthenticated    401     no       -            invalid api key
  /forbidden          403     no       -            your account cannot access this 
  /ratelimited        429     RETRY    12           rate_limit_error
  /server-error       500     RETRY    -            internal_error
  /ok-but-failed      200     no       -            quota exceeded

  Note /ok-but-failed: status 200, classified 'no retry', but the
  BODY says 'quota exceeded'. Status-only classification misses it.
  Always inspect the body as well as the code.

--------------------------------------------------------------------------
2. HEADERS - what to log and what never to log
--------------------------------------------------------------------------
  response status : 200
  request-id      : req_200_5893   <- ALWAYS log this
  ratelimit-left  : 49

  Request headers we sent, as they must appear in a log:
    Authorization     ***REDACTED***
    User-Agent        m2l11/1.0
    X-Api-Key         ***REDACTED***
    Content-Type      application/json

  A bearer token IS your identity. Anyone who reads it from a log
  can act as you until it is rotated.

--------------------------------------------------------------------------
3. STREAMING - 200 arrives before the work is done
--------------------------------------------------------------------------
  complete stream
    HTTP status         : 200   <- said OK before anything was generated
    chunks received     : 5
    assembled text      : 'Hello, Bharath!'
    time to first chunk : 1 ms
    total time          : 254 ms
    saw message_stop    : True

  TRUNCATED stream
    HTTP status         : 200   <- said OK before anything was generated
    chunks received     : 2
    assembled text      : 'The refund policy is '
    time to first chunk : 2 ms
    total time          : 103 ms
    saw message_stop    : False   <-- INCOMPLETE, yet status was 200

  The truncated stream returned 200 and then simply stopped. The
  only way to know it was cut off is the ABSENCE of the terminal
  event. If you trust the status code you will show the user half
  a sentence and call it an answer.

--------------------------------------------------------------------------
4. IDEMPOTENCY KEYS - making a POST retry safe
--------------------------------------------------------------------------
  Without a key - simulating a timeout then a retry:
    attempt 1 -> {'order_id': 'ord-001', 'duplicate': False}
    attempt 2 -> {'order_id': 'ord-002', 'duplicate': False}   <-- TWO orders created

  With the SAME key reused across the retry:
    attempt 1 -> {'order_id': 'ord-003', 'duplicate': False}
    attempt 2 -> {'order_id': 'ord-003', 'duplicate': True}   <-- same order, duplicate flagged

  With a NEW key per attempt (the common mistake):
    attempt 1 -> {'order_id': 'ord-004', 'duplicate': False}
    attempt 2 -> {'order_id': 'ord-005', 'duplicate': False}   <-- duplicate again

  Generate the key ONCE, before the first attempt, and reuse it.

==========================================================================
```

### 7.3 Reading the result

**Section 1's last row is the one to remember:**

```
/ok-but-failed      200     no       -            quota exceeded
```

HTTP status `200`. Classified "no retry". And the body says **quota exceeded**. A client that
branches only on the status code treats this as a successful response and hands an empty result to
the rest of your program. Real APIs do this — status codes describe the *HTTP transaction*, not
necessarily the *operation*. **Always inspect the body as well.**

**Section 3 is the most important part of the lab.** Look at the truncated stream:

```
HTTP status         : 200
chunks received     : 2
assembled text      : 'The refund policy is '
saw message_stop    : False   <-- INCOMPLETE, yet status was 200
```

Read that assembled text aloud. *"The refund policy is "* — and then nothing. The next words could
have been *"30 days"* or *"not applicable to sale items"*. The truncation happened at precisely the
point where the meaning is determined, and **every signal your HTTP client offers says the request
succeeded.**

The only evidence of failure is the **absence** of the terminal `message_stop` event. Nothing raises.
No status changes. If your code trusts the status code, you will render a half-sentence to a user as
a complete answer to a question about refunds.

This is why §5.5 insists that `200` on a stream means only *"the stream started"*, and why detecting
completion requires checking for the protocol's terminal event rather than for the absence of an
error.

**Section 4 proves the idempotency argument with three runs:**

| Strategy | Attempt 1 | Attempt 2 | Outcome |
|---|---|---|---|
| No key | `ord-001` | `ord-002` | **Two orders** |
| Same key reused | `ord-003` | `ord-003` (`duplicate: True`) | **One order** ✅ |
| New key per attempt | `ord-004` | `ord-005` | **Two orders** |

The third row is the mistake people actually make. Adding idempotency keys *feels* like it solves the
problem, and generating a fresh UUID inside the retry loop is the natural place to put it — which
defeats the mechanism completely while leaving the code looking correct. **The key identifies the
intent, not the attempt.**

**Section 2** shows `redact_headers` catching both the explicit `Authorization` header and
`X-Api-Key` via the substring rule, while leaving `User-Agent` and `Content-Type` readable. And it
shows `request-id` — the value to log on every single call.

**Verification:** confirm `/ratelimited` shows `RETRY` with `Retry-After: 12`, the truncated stream
reports `saw message_stop: False` with status 200, and the same-key idempotency run returns the same
`order_id` twice.

---

## 8. Common mistakes and troubleshooting

1. **Retrying `4xx`.** Burns quota, never succeeds. Retry only `408`, `425`, `429` and `5xx`.
2. **Ignoring `Retry-After`.** Hammering a rate-limited endpoint extends the block.
3. **Default timeouts.** Most libraries default to something far too short for LLM calls — or to no
   timeout at all, which is worse. Always set one explicitly (M2-L14).
4. **Not logging the request ID.**
5. **Logging the `Authorization` header.** Redact it (M2-L19).
6. **Treating `200` on a stream as success.**
7. **Assuming `POST` is safe to retry.**
8. **Generating a new idempotency key per attempt.**
9. **Ignoring the response body on error** — the useful detail is usually there, not in the status.

| Symptom | Cause | Fix |
|---|---|---|
| `401` on every call | Missing/wrong key, or wrong header format | Check the env var; confirm `Bearer ` prefix |
| `403` with a valid key | Authenticated but lacking permission for that model/region | Check account permissions |
| Frequent `429` | Exceeding rate limits | Honour `Retry-After`; throttle client-side; request a quota increase |
| Requests hang forever | No timeout set | Set explicit connect and read timeouts |
| Stream stops silently | No per-chunk timeout | Add a read timeout between chunks |
| Duplicate side effects | Retried a non-idempotent `POST` | Use an idempotency key |
| `413` | Prompt too long | Truncate or summarise (M5-L11) |

---

## 9. Security, privacy, reliability and cost

- **Security.** The `Authorization` header is a bearer credential: anyone holding it *is* you. Never
  log it, never put it in a URL (URLs appear in logs, proxies and browser history), never commit it.
  Use HTTPS always — HTTP sends it in clear text.
- **Security.** Authorization decisions belong on the server. A `403` your client "decides" not to
  show is not access control.
- **Privacy.** Request and response bodies contain user data. Logging full bodies is the most common
  accidental exfiltration route in AI applications (M10-L06). Log metadata, request IDs and token
  counts; sample bodies only with a redaction step.
- **Reliability.** Explicit timeouts and correct retry classification are the two highest-value
  reliability controls for API-backed systems.
- **Cost.** A `429` retry storm costs nothing per rejected request, but a retried `POST` that
  *succeeded* the first time is billed twice. Idempotency keys have a direct cost impact.

---

## 10. Exercises

### Exercise 1 — Beginner (~15 min)

For each, give the status code you would expect and whether to retry:

1. Your API key was revoked.
2. You sent `max_tokens: 999999`.
3. The provider is overloaded.
4. You requested a model your account cannot access.
5. You made 200 requests in a minute against a 50/minute limit.
6. Your prompt is 500,000 tokens.

### Exercise 2 — Intermediate (~25 min)

Run the lab, then:

1. Record the status, retry decision and any `Retry-After` for each endpoint.
2. Modify `is_retryable` to also treat `409` as retryable. Explain why that is usually wrong, and
   name one case where it might be right.
3. Add an endpoint returning `200` with `{"error": "quota exceeded"}` in the body. Show that
   status-only classification misses it, and write a check that catches it.
4. For the streaming endpoint, count how many chunks arrive and print the time of the first. Explain
   what TTFB means for perceived latency.

### Exercise 3 — Challenge (~25 min)

1. Add an endpoint that streams three chunks then closes the connection abruptly. Make your client
   detect the truncation. What distinguishes "finished" from "cut off"? (Hint: the protocol has a
   terminal event.)
2. Implement all three case-6 policies from §6 (discard, keep, keep-and-mark). Write the user-facing
   text for each.
3. Write `redact_headers(headers)` returning a loggable copy with `Authorization`, `Cookie` and any
   header containing `key`, `token` or `secret` replaced by `***`. Test it against six header sets.
4. Implement idempotency: have the server record `Idempotency-Key` values and return the original
   result for repeats. Prove that retrying with the same key does not act twice, and that a new key
   does.

---

## 11. Quiz

**Q1.** Which is the correct retry rule?

- A. Retry everything three times.
- B. Retry `5xx`, plus `429`, `408` and `425`; never retry other `4xx`.
- C. Retry only `500`.
- D. Never retry `POST`.

**Q2.** What is the difference between `401` and `403`?

- A. They are the same.
- B. `401` means the server does not know who you are (authentication); `403` means it does and you
  are not permitted (authorization).
- C. `401` is a server error.
- D. `403` means the resource does not exist.

**Q3.** Why is `POST` retry-unsafe?

- A. It is slower.
- B. It is not idempotent: after a timeout you cannot tell whether the server processed it, so a
  retry may duplicate the effect.
- C. It cannot carry a body.
- D. It is safe to retry.

**Q4.** What does an idempotency key do, and when must it be generated?

- A. Encrypts the request; generated per attempt.
- B. Lets the server de-duplicate retries by returning the original result — generated once before
  the first attempt** and reused for every retry.
- C. Authenticates the client.
- D. Sets the retry delay.

**Q5.** With a streamed response, what does `200 OK` tell you?

- A. The request succeeded completely.
- B. Only that the stream started; it can still carry an error or stop mid-answer afterwards.
- C. The response is cached.
- D. Nothing at all.

**Q6.** Why do LLM APIs stream?

- A. It reduces total generation time.
- B. It reduces *perceived* latency — the first token can arrive in a fraction of a second while the
  full answer takes many seconds.
- C. It reduces cost.
- D. It improves accuracy.

**Q7.** Why must a streaming timeout be per-chunk rather than total?

- A. Per-chunk is easier to implement.
- B. A total timeout either kills legitimate long answers or fails to detect a stalled stream; the
  useful signal is "no data received for N seconds".
- C. Totals are not supported.
- D. It reduces cost.

**Q8.** Which header should you log on every AI API call?

- A. `Authorization`  B. `request-id`  C. `Content-Type`  D. `User-Agent`

**Q9.** You get `429` with `Retry-After: 30`. What do you do?

- A. Retry immediately.  B. Wait at least 30 seconds, then retry — and consider throttling
  client-side.  C. Give up permanently.  D. Switch to `GET`.

**Q10.** *(Written, rubric-graded.)* In under 80 words, explain why a request that times out after 45
seconds is more dangerous than one that returns `500`.

---

## 12. Revision notes

- Request = method + URL + headers + body. Response = status + headers + body.
- **`4xx` = stop and fix. `5xx` + `429`/`408`/`425` = wait and retry.**
- **`401`** = who are you (authentication). **`403`** = you may not (authorization). The
  `Authorization` header carries *authentication* — a historical wart.
- **`POST` is not idempotent.** After a timeout you cannot know whether it applied. Use an
  **idempotency key**, generated **once** and reused across retries.
- **Log `request-id` on every call.** Never log `Authorization`. Never put a key in a URL.
- **Streaming:** SSE `data:` lines; `200` arrives before success is known; partial output is a real
  state; **timeouts must be per-chunk**.
- Honour `Retry-After`. Rate-limit header names are not standardised.
- **Authorization is decided server-side**, never by the client and never by a model.
- Check the response **body** on errors — some APIs return `200` with an error inside.

---

## 13. Completion checklist

- [ ] I can classify any status code as retryable or not.
- [ ] I can explain `401` vs `403` and why the header name is misleading.
- [ ] I ran the lab and saw all six endpoint behaviours.
- [ ] I understand why `POST` retries need idempotency keys.
- [ ] I can explain what `200` does and does not mean for a stream.
- [ ] I wrote `redact_headers` and tested it.
- [ ] I scored 7/10 on the quiz.

---

## 14. References

- MDN, HTTP overview. <https://developer.mozilla.org/en-US/docs/Web/HTTP> `[UNVERIFIED]`
- RFC 9110 — HTTP Semantics (methods, status codes, idempotency).
  <https://www.rfc-editor.org/rfc/rfc9110.html> `[UNVERIFIED]`
- MDN, Server-Sent Events.
  <https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events> `[UNVERIFIED]`
- Provider-specific rate-limit and error documentation changes frequently — always check the current
  page for the API you are using. `[UNVERIFIED]`

---

## 15. Next lesson

→ [M2-L12 — Calling APIs from Python with httpx](M2-L12-api-clients-httpx.md)

You know the protocol. Next: making the calls from Python, with correct timeouts, error handling and
the difference between a raw HTTP client and a provider SDK.
