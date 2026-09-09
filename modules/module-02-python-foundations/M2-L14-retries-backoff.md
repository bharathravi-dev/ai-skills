# M2-L14 — Timeouts, Retries, Exponential Backoff and Rate Limits

| | |
|---|---|
| **Lesson ID** | M2-L14 |
| **Difficulty** | 2 (Core) |
| **Estimated study time** | 2.0 hours |
| **Prerequisites** | [M2-L13](M2-L13-async-concurrency.md), [M2-L11](M2-L11-http-rest.md) |

---

## 1. Learning objectives

1. **Decide** whether a failure is retryable, using the exception type and status code.
2. **Implement** exponential backoff **with jitter**, and explain why jitter is not optional.
3. **Explain** the thundering-herd problem and how retries can cause an outage.
4. **Bound** retries by attempts, total time and cost.
5. **Choose** between retrying, failing fast, and circuit-breaking.

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **Retry** | Re-issuing a failed request. |
| **Backoff** | Waiting between attempts. |
| **Exponential backoff** | Doubling the wait each attempt: 1s, 2s, 4s, 8s. |
| **Jitter** | Random variation added to the wait, so clients do not synchronise. |
| **Thundering herd** | Many clients retrying simultaneously, amplifying an outage. |
| **Retry budget** | A cap on retries — by attempts, total time, or cost. |
| **Circuit breaker** | A component that stops calling a failing service for a period. |
| **Rate limit** | A cap on requests per unit time, enforced by the server. |
| **Token bucket** | A rate-limiting algorithm allowing bursts up to a capacity. |
| **`Retry-After`** | A response header telling you how long to wait. |
| **Idempotency key** | Lets a server de-duplicate retried writes (M2-L11). |
| **Deadline** | An absolute time by which the whole operation must finish. |

---

## 3. Plain-language explanation

At scale, requests fail. A system that works only when nothing fails does not work.

But **retrying is not free and is not always safe**. Three questions decide it:

1. **Is this failure transient?** A `500` might succeed on retry. A `400` never will.
2. **Is the operation safe to repeat?** A read always is. A write may create a duplicate.
3. **Will retrying make things worse?** If a service is overloaded, retries add load.

The naive version is the one most people write first:

```python
for attempt in range(3):
    try:
        return call()
    except Exception:
        time.sleep(1)
```

It is wrong in five ways: it retries non-retryable errors, waits a fixed interval, has no jitter, has
no total deadline, and swallows the final exception. This lesson fixes each.

---

## 4. Analogy

**Calling a busy phone line.** Engaged: you wait and try again. If you redial instantly and
repeatedly you never get through and you keep the line busy. So you wait a bit, then longer.

Now imagine ten thousand people redialling at *exactly* the same interval. Every retry arrives in a
synchronised wave. That is the **thundering herd**, and jitter is the fix.

### Where the analogy breaks

1. **A phone tells you it is engaged. A timeout tells you nothing** — the request may have been
   processed and the answer lost. That ambiguity is why writes need idempotency keys.
2. **Redialling does not cost money.** Each LLM retry does, and a retried request that already
   succeeded is billed twice.
3. **A person gives up.** Code does not, unless you make it. Unbounded retry loops burn budget
   silently.
4. **Phone lines do not have `Retry-After`.** When a server tells you how long to wait, that beats
   any algorithm you invent.

---

## 5. Detailed technical explanation

### 5.1 Deciding what to retry

Combining M2-L11 and M2-L12:

| Signal | Retry? | Why |
|---|---|---|
| `httpx.ConnectError` | **Yes** | Never reached the server; nothing happened |
| `httpx.ConnectTimeout` | **Yes** | Same |
| `httpx.ReadTimeout` | **Careful** | May have been processed. Reads yes; writes only with an idempotency key |
| `429` | **Yes, after `Retry-After`** | Transient quota state |
| `500`, `502`, `503`, `504`, `529` | **Yes** | Server-side, usually transient |
| `408`, `425` | Yes | Timeout / too-early |
| `400`, `401`, `403`, `404`, `422` | **No** | Retrying changes nothing |
| `409` | No | Needs a decision, not a repeat |

```python
NON_RETRYABLE = {400, 401, 403, 404, 409, 413, 422}
RETRYABLE = {408, 425, 429, 500, 502, 503, 504, 529}
```

**Retrying a `401` in a loop is a real production incident pattern.** It never succeeds, it burns
your rate limit, and the logs fill with identical errors that hide the real problem.

### 5.2 Backoff strategies

| Strategy | Waits | Problem |
|---|---|---|
| Immediate | 0, 0, 0 | Hammers a struggling service |
| Fixed | 1, 1, 1 | All clients retry in lockstep |
| Linear | 1, 2, 3 | Grows too slowly under real overload |
| **Exponential** | 1, 2, 4, 8 | Correct shape, but still synchronised |
| **Exponential + jitter** | 0.7, 1.9, 3.2, 7.1 | **Correct** |

```python
delay = min(base * (2 ** attempt), max_delay)
```

`max_delay` (typically 30–60 s) stops the fourth retry waiting eight minutes.

### 5.3 Jitter — and why it is mandatory

Without jitter, every client that failed at the same moment retries at the same moment. An outage
recovers, ten thousand synchronised retries arrive, and the service falls over again. Backoff spreads
retries *in time per client*; only jitter spreads them *across clients*.

Three common forms:

```python
# Full jitter (recommended default)
delay = random.uniform(0, min(cap, base * 2 ** attempt))

# Equal jitter
temp = min(cap, base * 2 ** attempt)
delay = temp / 2 + random.uniform(0, temp / 2)

# Decorrelated jitter
delay = min(cap, random.uniform(base, previous_delay * 3))
```

**Full jitter is the usual recommendation** and is what this course uses. The lab measures the
clustering difference directly.

### 5.4 Respect `Retry-After`

```python
def wait_seconds(response, attempt: int) -> float:
    retry_after = response.headers.get("Retry-After")
    if retry_after:
        try:
            return float(retry_after)          # seconds form
        except ValueError:
            pass                                # HTTP-date form; parse if you need it
    return random.uniform(0, min(60.0, 1.0 * 2 ** attempt))
```

**A server-supplied `Retry-After` always beats your algorithm** — it knows when capacity returns and
you do not. Ignoring it can extend a rate-limit block.

### 5.5 Bounding retries three ways

Attempt count alone is not enough.

```python
MAX_ATTEMPTS = 4          # 1 initial + 3 retries
DEADLINE_SECONDS = 90     # total wall-clock for the whole operation
MAX_COST = Decimal("0.50")
```

**Why a deadline matters:** with a 60 s timeout and 4 attempts plus backoff, worst case is over four
minutes. If the caller is an HTTP request that times out at 30 s, every retry after that point is
pure waste — burning money on a response nobody will receive. **Pass a deadline down and check it
before each attempt.**

**Why a cost bound matters:** M8-L15 makes this a first-class agent concern. A retry loop inside a
loop inside an agent step is how a £5 task becomes £500.

### 5.6 Retries interact badly with layers

If your HTTP client retries 3 times, your service wrapper retries 3 times, and the caller retries 3
times, one user request can become **27** upstream calls. This is retry amplification, and it turns a
small degradation into an outage.

**Rule: retry at exactly one layer.** Usually the lowest one that can classify the error correctly.
Disable retries in the layers above, and say so in the code.

### 5.7 Circuit breakers

When a service is down, retrying every request wastes time and adds load. A circuit breaker tracks
failures and, past a threshold, **fails immediately** without calling:

| State | Behaviour |
|---|---|
| **Closed** | Normal; count failures |
| **Open** | Fail fast; do not call. After a cooldown → half-open |
| **Half-open** | Allow one trial. Success → closed. Failure → open |

Retries handle *transient* failures; circuit breakers handle *sustained* ones. Retries alone against
a hard-down dependency turn every request into a slow failure — and your own latency collapses even
though the fault is elsewhere.

### 5.8 Client-side rate limiting

Better than reacting to `429` is not causing it. A **token bucket** allows bursts up to a capacity
while enforcing an average rate:

```python
class TokenBucket:
    def __init__(self, rate: float, capacity: float) -> None:
        self.rate = rate              # tokens added per second
        self.capacity = capacity      # burst size
        self.tokens = capacity
        self.updated = time.monotonic()

    def acquire(self) -> float:
        """Return how long to wait before proceeding."""
        now = time.monotonic()
        self.tokens = min(self.capacity, self.tokens + (now - self.updated) * self.rate)
        self.updated = now
        if self.tokens >= 1:
            self.tokens -= 1
            return 0.0
        return (1 - self.tokens) / self.rate
```

Combine with the semaphore from M2-L13: the semaphore bounds *concurrency*, the bucket bounds *rate*.
They are different limits and providers usually impose both.

### 5.9 Assumptions and limitations

- Retries assume failures are independent. If the cause is your malformed request, every retry fails
  identically.
- Backoff assumes recovery is likely. For a hard outage, a circuit breaker is correct.
- Timeouts must be shorter than the caller's deadline, or retries are wasted work.
- `Retry-After` may be an HTTP date rather than seconds.
- Libraries such as `tenacity` implement all of this; write it once yourself to understand it.

---

## 6. Worked example — retry policy, refined five times

**v1 — naive.**

```python
for _ in range(3):
    try:
        return call()
    except Exception:
        time.sleep(1)
```
Retries a `400` forever-ish, fixed delay, no jitter, no deadline, and returns `None` after the loop —
so failure looks like success with no data.

**v2 — classify errors.**

```python
for attempt in range(3):
    try:
        return call()
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code not in RETRYABLE:
            raise
        time.sleep(1)
```
Better. Still fixed delay, no jitter, no deadline.

**v3 — exponential backoff.** `time.sleep(1 * 2 ** attempt)` → 1, 2, 4. Now synchronised across
clients.

**v4 — full jitter.** `time.sleep(random.uniform(0, min(30, 1 * 2 ** attempt)))`. Herd fixed.

**v5 — production.**

```python
def call_with_retry(fn, *, max_attempts=4, base=1.0, cap=30.0,
                    deadline: float | None = None):
    started = time.monotonic()
    last_exc: Exception | None = None

    for attempt in range(max_attempts):
        if deadline is not None and time.monotonic() - started > deadline:
            raise TimeoutError(
                f"deadline of {deadline}s exceeded after {attempt} attempts"
            ) from last_exc
        try:
            return fn()
        except httpx.HTTPStatusError as exc:
            last_exc = exc
            status = exc.response.status_code
            if status not in RETRYABLE:
                raise                                  # fail fast, do not waste attempts
            server_wait = exc.response.headers.get("Retry-After")
            delay = (float(server_wait) if server_wait and server_wait.isdigit()
                     else random.uniform(0, min(cap, base * 2 ** attempt)))
        except (httpx.ConnectError, httpx.ConnectTimeout) as exc:
            last_exc = exc                              # never reached the server: safe
            delay = random.uniform(0, min(cap, base * 2 ** attempt))
        except httpx.ReadTimeout as exc:
            last_exc = exc                              # ambiguous: caller must opt in
            raise
        if attempt == max_attempts - 1:
            break
        time.sleep(delay)

    raise RuntimeError(f"failed after {max_attempts} attempts") from last_exc
```

**Six decisions, each earning its place:**

1. **Non-retryable errors re-raise immediately** rather than consuming attempts.
2. **`Retry-After` overrides** the computed delay.
3. **Full jitter** on every computed delay.
4. **A deadline** checked before each attempt, so retries stop being useful work.
5. **`ReadTimeout` re-raises by default** — it is ambiguous, and blindly retrying a write duplicates
   it. A caller with an idempotency key can opt in.
6. **The final failure raises with `from last_exc`**, preserving the cause. It never returns `None`.

---

## 7. Practical activity

**File:** [`labs/m2/l14_retries.py`](../../labs/m2/l14_retries.py)

**Requires the venv.** Local server; no key or internet needed:

```bash
source .venv/bin/activate
python labs/m2/l14_retries.py
```

Simulates 200 clients retrying an outage with and without jitter and shows the clustering; compares
retry strategies against a flaky endpoint; demonstrates non-retryable errors failing fast; shows the
deadline stopping useless work; and runs a token bucket.

### 7.1 Important lines

| Construct | Why |
|---|---|
| `random.uniform(0, min(cap, base * 2 ** attempt))` | Full jitter. |
| `time.monotonic()` | Never goes backwards; correct for measuring elapsed time. |
| `response.headers.get("Retry-After")` | Server instruction beats your algorithm. |
| Histogram of retry arrival times | Makes the thundering herd visible. |
| `raise ... from last_exc` | Preserves the cause after exhausting attempts. |

### 7.2 Expected output

`[EXECUTED]` 2026-09-08 with httpx 0.28.1, Python 3.12.3. Seeded, so the jitter values reproduce:

```
==========================================================================
TIMEOUTS, RETRIES, BACKOFF AND RATE LIMITS
==========================================================================
Local server on http://127.0.0.1:46485

--------------------------------------------------------------------------
1. RETRY CLASSIFICATION IN ACTION
--------------------------------------------------------------------------
  /flaky  (503, 503, then 200)
      attempt 1: 503 -> retryable, waiting 0.032s (full jitter)
      attempt 2: 503 -> retryable, waiting 0.003s (full jitter)
      attempt 3: 200 OK
      -> succeeded: {'ok': True, 'attempts': 3}, total calls: 3

  /bad-request  (400 - not retryable)
      attempt 1: 400 -> NOT retryable, failing immediately
      -> raised 400 after 1 call
      Four attempts were allowed. Only ONE was used, because
      retrying a 400 cannot possibly succeed.

  /rate-limited  (429 with Retry-After: 3)
      attempt 1: 429 -> retryable, waiting 3.000s (Retry-After: 3s)
      would need 3.000s more, but only 0.498s of deadline remains -> stopping now
      -> TimeoutError: deadline of 0.5s would be exceeded by waiting 3.000s after 1 attempts
      The server asked for 3s; our deadline was 0.5s. Stopping
      is correct - the caller will have given up long before.

  /always-500 with deadline=0.3s
      attempt 1: 500 -> retryable, waiting 0.028s (full jitter)
      attempt 2: 500 -> retryable, waiting 0.045s (full jitter)
      attempt 3: 500 -> retryable, waiting 0.295s (full jitter)
      would need 0.295s more, but only 0.222s of deadline remains -> stopping now
      -> TimeoutError: deadline of 0.3s would be exceeded by waiting 0.295s after 3 attempts

--------------------------------------------------------------------------
2. THE THUNDERING HERD - why jitter is mandatory
--------------------------------------------------------------------------
  FIXED exponential backoff (no jitter)
    t+ 0.0s |                                                            |    0
    t+ 0.5s |                                                            |    0
    t+ 1.0s |                                                            |    0
    t+ 1.5s |                                                            |    0
    t+ 2.0s |                                                            |    0
    t+ 2.5s |                                                            |    0
    t+ 3.0s |                                                            |    0
    t+ 3.5s |                                                            |    0
    t+ 4.0s |                                                            |    0
    t+ 4.5s |                                                            |    0
    t+ 5.0s |                                                            |    0
    t+ 5.5s |                                                            |    0
    t+ 6.0s |                                                            |    0
    t+ 6.5s |                                                            |    0
    t+ 7.0s |                                                            |    0
    t+ 7.5s |                                                            |    0
    t+ 8.0s |############################################################|  500
    peak in any 500ms window: 500 of 500 clients

  FULL JITTER
    t+ 0.0s |###                                                         |   27
    t+ 0.5s |####                                                        |   34
    t+ 1.0s |##                                                          |   23
    t+ 1.5s |#####                                                       |   46
    t+ 2.0s |####                                                        |   37
    t+ 2.5s |##                                                          |   21
    t+ 3.0s |####                                                        |   38
    t+ 3.5s |##                                                          |   22
    t+ 4.0s |####                                                        |   35
    t+ 4.5s |###                                                         |   29
    t+ 5.0s |####                                                        |   34
    t+ 5.5s |###                                                         |   26
    t+ 6.0s |###                                                         |   29
    t+ 6.5s |###                                                         |   32
    t+ 7.0s |####                                                        |   34
    t+ 7.5s |###                                                         |   33
    t+ 8.0s |                                                            |    0
    peak in any 500ms window: 46 of 500 clients

  Peak load reduced from 500 to 46 (11x lower)

  Without jitter every client waits EXACTLY 8s, so all 500 retries
  land in the same instant. The service has just come back up and
  is immediately hit by its entire client base at once - which is
  how a recovering service falls over again.

  Backoff spreads retries in time PER CLIENT. Only jitter spreads
  them ACROSS clients. You need both.

--------------------------------------------------------------------------
3. TOKEN BUCKET - bounding RATE, not concurrency
--------------------------------------------------------------------------
  rate=2/s, capacity=5 (so a burst of 5 is allowed immediately)

  request         wait   note
  1              0.00s   burst allowed
  2              0.00s   burst allowed
  3              0.00s   burst allowed
  4              0.00s   burst allowed
  5              0.00s   burst allowed
  6              0.50s   throttled
  7              0.00s   token refilled
  8              0.50s   throttled

  8 requests took 1.00s
  The first 5 went straight through (the burst capacity), then the
  bucket enforced roughly 2 per second.

  A SEMAPHORE would not have helped here: 8 sequential requests are
  never concurrent. Rate limits and concurrency limits are
  different constraints and providers usually impose both.

--------------------------------------------------------------------------
4. RETRY AMPLIFICATION - why you retry at ONE layer only
--------------------------------------------------------------------------
  layers retrying       attempts each   upstream calls
  1                     3               3
  2                     3               9
  3                     3               27

  One user request becomes 27 upstream calls when the client, the
  service and the gateway each retry three times. During a partial
  degradation that multiplies load by 27 at exactly the moment the
  dependency can least afford it.

  Rule: retry at exactly ONE layer - normally the lowest one that
  can classify the error correctly - and disable it everywhere else.

==========================================================================
```

### 7.3 Reading the result

**Section 1 shows each policy decision paying off:**

| Endpoint | Attempts used (of 4 allowed) | Why |
|---|---|---|
| `/flaky` (503, 503, 200) | 3 | Retried correctly, succeeded |
| `/bad-request` (400) | **1** | Not retryable — three attempts saved |
| `/rate-limited` (429, `Retry-After: 3`) | 1 | Server asked for 3 s; deadline was 0.5 s |
| `/always-500` with 0.3 s deadline | 3 of 8 | Deadline stopped it, not the attempt count |

The `400` row is the one that matters most in practice. Four attempts were permitted; **one** was
used. A policy that retries blindly would have made four identical failing calls, burned rate limit,
and written four identical errors into the log — hiding the actual problem in noise.

Note also the deadline messages:

```
would need 3.000s more, but only 0.498s of deadline remains -> stopping now
```

The check happens **before** sleeping. Sleeping three seconds only to discover the deadline expired
2.5 seconds ago wastes exactly the resource the deadline exists to protect. This is a small
refinement that separates a working retry policy from a correct one.

**Section 2 makes the thundering herd visible.** Without jitter, every one of 500 clients waits
exactly 8 seconds, so all 500 retries land in **one 500 ms window**:

```
FIXED backoff:  peak in any 500ms window: 500 of 500 clients
FULL JITTER:    peak in any 500ms window:  46 of 500 clients
```

**An 11× reduction in peak load**, from one line of code. And look at the shape of the jittered
histogram — a broadly flat spread across the full 8-second window, exactly what a recovering service
needs.

The failure mode this prevents is worth stating plainly: a service comes back up after an outage and
is instantly hit by its **entire client base simultaneously**. It falls over again. The clients back
off, wait 16 seconds, and hit it again in unison. Without jitter, backoff can produce a *self-
sustaining* outage.

**Section 3 shows why a semaphore is not a rate limiter.** The token bucket let the first 5 requests
through immediately (the burst capacity) then throttled to roughly 2 per second. A semaphore would
have done nothing at all here — these 8 requests were never concurrent. **Concurrency limits and rate
limits are different constraints**, and providers typically impose both.

**Section 4** is arithmetic rather than measurement, but it is the arithmetic people forget:
3 layers × 3 attempts = **27 upstream calls for one user request**. During a partial degradation that
multiplies load 27-fold at precisely the moment the dependency can least absorb it.

**Verification:** confirm `/bad-request` uses exactly 1 call, the deadline messages appear *before*
the sleep, and the herd peak drops from 500 to roughly 40–60.

---

## 8. Common mistakes and troubleshooting

1. **Retrying non-retryable errors.** Especially `401` and `400`.
2. **No jitter.** Works in testing, causes outages at scale.
3. **No deadline.** Retries continue after the caller has given up.
4. **Retrying at several layers.** 3 × 3 × 3 = 27 calls.
5. **Blindly retrying writes** on a timeout. Duplicates.
6. **Ignoring `Retry-After`.**
7. **Swallowing the final exception** and returning `None`.
8. **Using `time.time()`** for elapsed time — it can jump. Use `time.monotonic()`.
9. **No cost bound** in an agent loop.

| Symptom | Cause | Fix |
|---|---|---|
| Endless identical errors in logs | Retrying a non-retryable status | Classify before retrying |
| Service recovers then falls over again | Thundering herd | Add full jitter |
| Costs far above estimate | Unbounded retries | Attempt, deadline and cost caps |
| Duplicate records | Retried a write after a timeout | Idempotency keys |
| One user request → many upstream calls | Retry amplification | Retry at exactly one layer |
| Latency collapses when a dependency is down | Retrying a hard outage | Add a circuit breaker |
| `429` despite backoff | Rate, not concurrency, is the limit | Add a token bucket |

---

## 9. Security, privacy, reliability and cost

- **Reliability.** Retries are the highest-value reliability control for API-backed systems — and the
  easiest to turn into a self-inflicted outage. Jitter and bounds are what separate the two.
- **Cost.** Every retry of an LLM call costs money. A retried request that already succeeded is
  billed twice. Bound retries by cost as well as attempts (M5-L15, M8-L15).
- **Security.** A retry loop against an authentication endpoint can look like a brute-force attempt
  and get you blocked. Never retry `401`.
- **Privacy.** Retry logs multiply. If you log request bodies on failure, one failed request writes
  the payload four times.

---

## 10. Exercises

### Exercise 1 — Beginner (~15 min)

For each, state retry or not, and the wait:

1. `401 Unauthorized`.
2. `429` with `Retry-After: 20`.
3. `httpx.ConnectError`.
4. `httpx.ReadTimeout` on a `POST` that creates an order.
5. `503` on attempt 3, base 1 s, cap 30 s, full jitter.
6. `400 Bad Request`.

### Exercise 2 — Intermediate (~30 min)

Implement `call_with_retry` from §6 v5, then:

1. Test it against the lab's flaky endpoint (fails twice, then succeeds). Log each attempt's delay.
2. Test against an endpoint returning `400`. Confirm it fails after **one** call, not four.
3. Test with `deadline=2.0` against an always-failing endpoint. Confirm it stops on the deadline
   rather than after all attempts, and that the error names the deadline.
4. Add `Retry-After: 3` to the 429 response and confirm your code waits 3 s rather than the jittered
   delay.
5. Count total calls made in each case and explain each number.

### Exercise 3 — Challenge (~35 min)

1. Simulate 500 clients hitting an outage that ends at t=5 s. Plot (as an ASCII histogram) the
   arrival times of their first retry with fixed backoff and with full jitter. Report the peak
   requests-per-100 ms in each case.
2. Implement a circuit breaker with the three states from §5.7. Show it opening after 5 failures,
   failing fast for 10 s, then half-opening.
3. Implement the token bucket from §5.8. Show it allowing a burst of 10 then throttling to 2/s.
4. Combine semaphore (concurrency) + token bucket (rate) + retry with jitter, and explain what each
   protects against and why one cannot substitute for another.
5. Demonstrate retry amplification: three nested layers each retrying 3 times. Count the upstream
   calls for one user request.

---

## 11. Quiz

**Q1.** Which should **never** be retried?

- A. `503`  B. `429`  C. `401`  D. `httpx.ConnectError`

**Q2.** Why is jitter mandatory rather than optional?

- A. It makes retries faster.
- B. Backoff spreads retries in time *per client* but leaves clients synchronised with each other;
  jitter spreads them *across* clients, preventing a thundering herd when an outage ends.
- C. It reduces cost.
- D. It is required by HTTP.

**Q3.** `Retry-After: 20` on a `429`. What do you do?

- A. Retry immediately.  B. Use your computed backoff.  C. Wait at least 20 s — the server's
  instruction beats your algorithm.  D. Fail permanently.

**Q4.** Why bound retries by a deadline as well as attempt count?

- A. Deadlines are easier to configure.
- B. Timeout × attempts plus backoff can far exceed the caller's own timeout, so retries after that
  point burn money on a response nobody will receive.
- C. Attempt counts are unreliable.
- D. It is not necessary.

**Q5.** Client retries 3×, service retries 3×, gateway retries 3×. How many upstream calls can one
user request cause?

- A. 3  B. 9  C. 27  D. 1

**Q6.** Why is `httpx.ReadTimeout` handled differently from `ConnectError`?

- A. It is more common.
- B. `ConnectError` proves the request never reached the server, so a retry is safe;
  `ReadTimeout` leaves it unknown whether the request was processed, so retrying a write may
  duplicate it.
- C. `ReadTimeout` is not retryable at all.
- D. They are the same.

**Q7.** When is a circuit breaker the right tool rather than retries?

- A. Never; retries always suffice.
- B. When failures are sustained rather than transient — retrying a hard-down dependency turns every
  request into a slow failure and collapses your own latency.
- C. Only for databases.
- D. When the error is `400`.

**Q8.** What does a semaphore bound, and what does a token bucket bound?

- A. Both bound concurrency.
- B. The semaphore bounds concurrency (how many at once); the token bucket bounds rate (how
  many per second). Providers usually impose both.
- C. Both bound rate.
- D. The semaphore bounds cost.

**Q9.** Why use `time.monotonic()` rather than `time.time()` for elapsed time?

- A. It is more precise.
- B. It never goes backwards, whereas the wall clock can jump when the system clock is adjusted,
  making an elapsed-time calculation negative or wildly wrong.
- C. It is faster.
- D. `time.time()` does not exist.

**Q10.** *(Written, rubric-graded.)* In under 80 words, explain how a well-intentioned retry policy
can turn a brief degradation into a full outage.

---

## 12. Revision notes

- **Classify before retrying.** `ConnectError`/`ConnectTimeout` → always safe. `429`/`5xx`/`408`/`425`
  → yes. **`4xx` (400, 401, 403, 404, 409, 422) → never.** `ReadTimeout` → ambiguous; writes need an
  idempotency key.
- **Exponential backoff with FULL JITTER:** `random.uniform(0, min(cap, base * 2 ** attempt))`.
  Backoff alone leaves clients synchronised; **jitter is what prevents the thundering herd**.
- **`Retry-After` overrides your algorithm.**
- **Bound three ways: attempts, deadline, cost.** Without a deadline you keep paying after the caller
  has gone.
- **Retry at exactly one layer.** 3 × 3 × 3 = 27.
- **Circuit breaker for sustained failure**; retries for transient. Closed → open → half-open.
- **Semaphore bounds concurrency; token bucket bounds rate.** Different limits, both usually needed.
- **`time.monotonic()`** for elapsed time, never `time.time()`.
- Never swallow the final exception — raise with `from last_exc`.

---

## 13. Completion checklist

- [ ] I can classify any failure as retryable or not.
- [ ] I implemented exponential backoff with full jitter.
- [ ] I saw the thundering-herd histogram with and without jitter.
- [ ] My retry stops on a deadline, not only on attempt count.
- [ ] I confirmed a `400` fails after one call.
- [ ] I can explain why `ReadTimeout` differs from `ConnectError`.
- [ ] I implemented a token bucket and know how it differs from a semaphore.
- [ ] I scored 7/10 on the quiz.

---

## 14. References

- AWS Architecture Blog, "Exponential Backoff And Jitter" — the source of the full/equal/decorrelated
  jitter comparison. <https://aws.amazon.com/builders-library/timeouts-retries-and-backoff-with-jitter/>
  `[UNVERIFIED]`
- Google SRE Book, "Handling Overload" and "Addressing Cascading Failures".
  <https://sre.google/books/> `[UNVERIFIED]`
- `tenacity` — a production retry library implementing these patterns.
  <https://tenacity.readthedocs.io/> `[UNVERIFIED]`

---

## 15. Next lesson

→ [M2-L15 — FastAPI: Routes, Request/Response Schemas, Dependencies](M2-L15-fastapi.md)

You can call APIs reliably. Next: serving one — with validated requests, proper status codes and the
dependency injection that makes it testable.
