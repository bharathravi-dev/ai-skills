# M2-L13 — Async and Concurrency: when it helps and when it does not

| | |
|---|---|
| **Lesson ID** | M2-L13 |
| **Difficulty** | 3 (Advanced) |
| **Estimated study time** | 2.25 hours |
| **Prerequisites** | [M2-L12](M2-L12-api-clients-httpx.md) |

---

## 1. Learning objectives

1. **Distinguish** I/O-bound from CPU-bound work and **choose** the right concurrency tool.
2. **Write** `async`/`await` code and **run** many requests concurrently.
3. **Explain** why `async` does not speed up CPU-bound work, and what the GIL is.
4. **Bound** concurrency with a semaphore and **explain** why unbounded concurrency fails.
5. **Handle** partial failure across concurrent tasks without losing results or errors.

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **Concurrency** | Managing several tasks with overlapping lifetimes. |
| **Parallelism** | Executing several tasks at literally the same instant, on multiple cores. |
| **I/O-bound** | Time is spent waiting for network, disk or a database. |
| **CPU-bound** | Time is spent computing. |
| **Blocking** | An operation that stops the thread until it completes. |
| **Coroutine** | A function defined with `async def`; calling it returns an awaitable. |
| **`await`** | Suspends the coroutine and yields control until the awaited thing completes. |
| **Event loop** | The scheduler that runs coroutines and resumes them when their I/O is ready. |
| **Task** | A coroutine scheduled on the event loop, running concurrently. |
| **`asyncio.gather`** | Runs awaitables concurrently and collects results. |
| **Semaphore** | A counter limiting how many things may run at once. |
| **GIL** | Global Interpreter Lock — only one thread executes Python bytecode at a time. |
| **Thread pool** | Worker threads; good for blocking I/O in libraries without async support. |
| **Process pool** | Worker processes; the way to get real CPU parallelism in Python. |

---

## 3. Plain-language explanation

The decision is made by one question: **what is your program waiting for?**

| Waiting for | Type | Tool |
|---|---|---|
| Network, disk, database | **I/O-bound** | `asyncio` (or threads) |
| Arithmetic, parsing, model inference on CPU | **CPU-bound** | `multiprocessing` |

**Almost everything in AI application engineering is I/O-bound.** You call an API and wait 3 seconds
for a response. During those 3 seconds your CPU does nothing. If you must make 100 such calls,
sequentially that is 300 seconds; concurrently it can be close to 3.

That is the entire value proposition of async here, and it is enormous.

**What async does not do:** make any single call faster, or help with CPU work. Because of the GIL,
Python executes only one thread of bytecode at a time — so `asyncio` and threads give you *waiting*
concurrency, not *computing* parallelism. For CPU work you need separate processes.

### If you know JavaScript

Almost identical, with two important differences:

| JavaScript | Python |
|---|---|
| `async function` | `async def` |
| `await fetch(...)` | `await client.get(...)` |
| `Promise.all([...])` | `asyncio.gather(*tasks)` |
| `Promise.allSettled` | `asyncio.gather(..., return_exceptions=True)` |
| Event loop always running | **You must start it**: `asyncio.run(main())` |
| Calling an async fn starts it | **Calling a coroutine does nothing until awaited** |

The last row causes a specific bug: `fetch_data()` without `await` in Python creates a coroutine
object and **never runs it**, with only a `RuntimeWarning: coroutine was never awaited` — easily
missed.

---

## 4. Analogy

**A single waiter serving many tables.**

The waiter takes an order, hands it to the kitchen, and — rather than standing still — takes the next
table's order. One waiter, many tables in flight. Nothing cooks faster; the *waiting* overlaps.

### Where the analogy breaks

1. **One waiter cannot chop vegetables for ten tables at once.** That is CPU work, and no amount of
   attentiveness helps. You need more cooks (processes).
2. **A real waiter can be interrupted mid-task. A coroutine only yields at an `await`.** A blocking
   call with no `await` inside a coroutine freezes the *entire* event loop — every other table waits.
   This is the single most common async bug (§5.5).
3. **A restaurant naturally limits tables. Async does not.** `gather` over 10,000 coroutines opens
   10,000 connections and gets you rate-limited or out of file descriptors. You must impose the limit
   (§5.6).
4. **A waiter knows when a table gives up.** A coroutine whose exception nobody retrieves can fail
   silently (§5.7).

---

## 5. Detailed technical explanation

### 5.1 The basics

```python
import asyncio

async def fetch(name: str) -> str:
    await asyncio.sleep(1)          # simulates I/O; yields control
    return f"result-{name}"

async def main() -> None:
    result = await fetch("a")               # sequential
    results = await asyncio.gather(          # concurrent
        fetch("a"), fetch("b"), fetch("c")
    )

asyncio.run(main())
```

Three rules:

1. `await` may only appear inside `async def`.
2. **Calling a coroutine does not run it.** `fetch("a")` creates an object; `await` or a task runs it.
3. `asyncio.run()` starts the loop. Call it **once**, at the top level.

`asyncio.sleep` yields to the loop. `time.sleep` **blocks it** — a critical difference (§5.5).

### 5.2 Concurrency with httpx

```python
import asyncio, httpx

async def fetch_all(urls: list[str]) -> list[dict]:
    async with httpx.AsyncClient(timeout=30.0) as client:
        responses = await asyncio.gather(*(client.get(u) for u in urls))
        return [r.json() for r in responses]
```

Note `AsyncClient` and `async with`. The sync and async APIs are otherwise identical — the reason
this course chose `httpx` (M2-L12).

**Sequential:** 100 calls × 2 s = **200 s**.
**Concurrent:** roughly **2 s**, plus overhead. The lab measures this.

### 5.3 Structured concurrency: `TaskGroup`

Python 3.11+ offers a safer construct:

```python
async def main() -> None:
    async with asyncio.TaskGroup() as tg:
        t1 = tg.create_task(fetch("a"))
        t2 = tg.create_task(fetch("b"))
    print(t1.result(), t2.result())
```

If any task raises, the others are **cancelled** and the errors are raised together as an
`ExceptionGroup`. Compare with `gather`, whose default behaviour on the first exception is to
propagate it while leaving the other tasks running. Prefer `TaskGroup` for work that should succeed
or fail as a unit.

### 5.4 Partial failure

For independent work — 100 documents, some of which may fail — you usually want all the results *and*
all the errors:

```python
results = await asyncio.gather(*tasks, return_exceptions=True)

succeeded = [r for r in results if not isinstance(r, Exception)]
failed = [r for r in results if isinstance(r, Exception)]
```

Without `return_exceptions=True`, the first failure propagates and **you lose the 99 successes**.
With it, exceptions arrive as ordinary values in the results list — which you must then check, or you
will pass an exception object downstream as if it were data.

### 5.5 The blocking-call trap

**This is the bug you will actually write:**

```python
async def bad(url: str):
    time.sleep(1)                    # BLOCKS THE WHOLE EVENT LOOP
    return requests.get(url)          # so does this: sync library in async code
```

`asyncio` is cooperative. A coroutine keeps the loop until it hits an `await`. A blocking call inside
a coroutine stops *every* other task — so a hundred "concurrent" requests run one at a time and async
is now slower than the synchronous version, because you also pay the loop overhead.

**Fixes:**

```python
await asyncio.sleep(1)                                    # async-aware sleep
async with httpx.AsyncClient() as c: await c.get(url)     # async-aware client
result = await asyncio.to_thread(blocking_function, arg)  # offload to a thread
```

`asyncio.to_thread` is the escape hatch for libraries with no async support — many database drivers,
some SDKs, most file I/O.

**How to spot it:** any `async def` whose body contains no `await` is almost certainly wrong.

### 5.6 Bounding concurrency

```python
async def fetch_all(urls: list[str], *, limit: int = 10) -> list[str]:
    semaphore = asyncio.Semaphore(limit)

    async def one(url: str) -> str:
        async with semaphore:                # at most `limit` inside at once
            async with httpx.AsyncClient() as client:
                return (await client.get(url)).text

    return await asyncio.gather(*(one(u) for u in urls))
```

**Unbounded concurrency fails in four distinct ways**, and all four happen in practice:

| Failure | Cause |
|---|---|
| `429` rate limiting | You exceeded the provider's per-minute limit instantly |
| "Too many open files" | Each connection is a file descriptor; the default limit is often 1024 |
| Memory exhaustion | 10,000 in-flight responses buffered at once |
| Overwhelming a downstream service | You became the incident |

**Always bound concurrency.** A sensible default is 5–20 for external APIs; tune against the
provider's documented limits (M2-L14).

### 5.7 Fire-and-forget tasks

```python
asyncio.create_task(background_work())     # no reference kept
```

Two problems: if nothing holds a reference the task may be **garbage-collected mid-execution**, and
if it raises, the exception surfaces only as a warning when the task is destroyed. Keep references:

```python
_background: set[asyncio.Task] = set()

task = asyncio.create_task(background_work())
_background.add(task)
task.add_done_callback(_background.discard)
```

### 5.8 Choosing a tool

| Situation | Tool | Why |
|---|---|---|
| Many API calls | **`asyncio`** | I/O-bound; thousands of tasks are cheap |
| Blocking library, few calls | `ThreadPoolExecutor` or `asyncio.to_thread` | No async support available |
| CPU-heavy work | **`ProcessPoolExecutor`** | Only way past the GIL |
| One call | Plain sync | Async adds complexity for nothing |

**Do not make a codebase async for a single API call.** Async is contagious — an `async def` can only
be awaited from another `async def` — so it spreads through your call stack. Adopt it when
concurrency is genuinely needed, which for AI applications it usually is.

### 5.9 Assumptions and limitations

- The GIL means threads do not give CPU parallelism. (Free-threaded builds are experimental;
  `[UNVERIFIED]` — do not rely on this.)
- `asyncio` performance depends on every library in the path being async-aware.
- Debugging is harder: tracebacks cross `await` boundaries and may omit intermediate frames.
- Async adds real complexity. For a script making ten calls, sequential is fine.

---

## 6. Worked example — 100 documents through an API

Requirement: classify 100 documents. Each call takes ~1 s.

**Version 1 — sequential.** ~100 s. Correct, simple, and too slow. CPU is idle 99.9% of the time.

**Version 2 — unbounded `gather`.**

```python
results = await asyncio.gather(*(classify(d) for d in docs))
```

In theory ~1 s. In practice: 100 simultaneous connections, HTTP `429` on most of them, and now you
have 100 *failed* results in 1 second. **Faster failure is not progress.**

**Version 3 — bounded.**

```python
async def classify_all(docs: list[str], *, limit: int = 10) -> list[dict]:
    semaphore = asyncio.Semaphore(limit)
    async with httpx.AsyncClient(timeout=30.0) as client:
        async def one(doc: str) -> dict:
            async with semaphore:
                response = await client.post("/classify", json={"text": doc})
                response.raise_for_status()
                return response.json()
        return await asyncio.gather(*(one(d) for d in docs))
```

~10 s (100 documents ÷ 10 concurrent × 1 s), within rate limits. **A tenfold speed-up that actually
works** beats a hundredfold one that does not — and as the lab measures, the bounded version is often
genuinely *faster* as well as safer, because the service you are calling saturates.

**Version 4 — bounded, with partial failure handled.**

```python
async def classify_all(docs, *, limit=10):
    semaphore = asyncio.Semaphore(limit)
    async with httpx.AsyncClient(timeout=30.0) as client:
        async def one(index: int, doc: str):
            async with semaphore:
                response = await client.post("/classify", json={"text": doc})
                response.raise_for_status()
                return index, response.json()

        outcomes = await asyncio.gather(
            *(one(i, d) for i, d in enumerate(docs)), return_exceptions=True
        )

    results: dict[int, dict] = {}
    failures: list[tuple[int, Exception]] = []
    for index, outcome in enumerate(outcomes):
        if isinstance(outcome, Exception):
            failures.append((index, outcome))
        else:
            position, payload = outcome
            results[position] = payload
    return results, failures
```

**Three decisions worth noting:**

1. **Each task returns its index.** `gather` preserves input order, but carrying the index explicitly
   makes the mapping robust if the code is later refactored to use `as_completed`.
2. **`return_exceptions=True`** so one bad document does not discard 99 good results.
3. **Failures are returned, not logged and swallowed** — the caller decides whether to retry, skip or
   abort (M2-L10).

This is the exact shape of the ingestion pipeline in M7-L03 and the batch evaluation runner in
M5-L18.

---

## 7. Practical activity

**File:** [`labs/m2/l13_async.py`](../../labs/m2/l13_async.py)

**Requires the venv.** Runs a local server; no key or internet needed:

```bash
source .venv/bin/activate
python labs/m2/l13_async.py
```

Measures sequential versus concurrent versus bounded, demonstrates the blocking-call trap with real
timings, shows CPU-bound work not benefiting from async, and handles partial failure.

### 7.1 Important lines

| Construct | Why |
|---|---|
| `asyncio.gather(*coros)` | Runs concurrently, preserves input order. |
| `asyncio.Semaphore(limit)` | Bounds concurrency. |
| `return_exceptions=True` | Keeps successes when some tasks fail. |
| `time.sleep` inside `async def` | The blocking trap, measured. |
| `asyncio.to_thread(fn)` | Offloads a blocking call so the loop keeps running. |
| `ProcessPoolExecutor` | Real parallelism for CPU work. |

### 7.2 Expected output

`[EXECUTED]` 2026-09-08 with httpx 0.28.1, Python 3.12.3. Timings vary by machine; the **relative
pattern** is what matters:

```
==========================================================================
ASYNC AND CONCURRENCY
==========================================================================
Local server on http://127.0.0.1:33267

--------------------------------------------------------------------------
1. SEQUENTIAL vs CONCURRENT vs BOUNDED
--------------------------------------------------------------------------
  30 requests, each taking 100 ms server-side.
  Theoretical sequential floor: 3.0 s

  Each strategy is run 3 times, because the SPREAD matters as much
  as the average.

  strategy                         best    worst   spread   speed-up
  sequential                      3.21s    3.21s    0.00s       1.0x
  gather (unbounded)              1.20s    1.27s    0.07s       2.7x
  gather + semaphore(10)          0.42s    1.19s    0.77s       7.6x
  gather + semaphore(5)           0.71s    0.73s    0.02s       4.5x

  Nothing got faster. The WAITING overlapped. During the
  sequential run the CPU was idle almost the entire time.

  Now the result people find surprising: compare unbounded gather
  with semaphore(10). More concurrency was SLOWER.

  Firing all 30 requests at once saturates the server. It has a
  finite number of worker threads, so the extra requests do not
  run sooner - they queue, and everything contends for the same
  resources. Ten at a time keeps the server in its efficient range.

  This is the general shape of concurrency tuning: throughput rises
  with concurrency up to the point the downstream service
  saturates, then FLATTENS OR FALLS. The best limit is a property
  of the thing you are calling, not of your code, so it must be
  measured rather than guessed.

  Exact numbers vary between machines and runs. What is stable is
  the shape: sequential is worst, a sensible bound is best, and
  unbounded is neither fastest nor safe. Against a real API,
  unbounded also means HTTP 429s and exhausted file descriptors.

--------------------------------------------------------------------------
2. THE BLOCKING TRAP - async that is not concurrent
--------------------------------------------------------------------------
  version                                           time
  async def + time.sleep (BLOCKING)                3.01s
  async def + await asyncio.to_thread(...)         0.21s

  The first is 15x slower despite being 'async'.

  time.sleep does not yield to the event loop, so all 30 'concurrent'
  coroutines ran one after another. The code LOOKS concurrent, uses
  gather, and is fully sequential.

  DIAGNOSTIC: an 'async def' whose body contains no 'await' is
  almost always this bug. Look for the missing await first.

--------------------------------------------------------------------------
3. CPU-BOUND WORK - async and threads do not help
--------------------------------------------------------------------------
  4 jobs, each summing 3,000,000 squares

  approach                              time   vs sequential
  sequential                           0.66s            1.0x
  asyncio.gather                       0.51s            1.3x
  ThreadPoolExecutor                   1.08s            0.6x
  ProcessPoolExecutor                  0.24s            2.8x

  asyncio and threads give roughly NO improvement: the GIL lets
  only one thread execute Python bytecode at a time, and there is
  no I/O to overlap. Only separate PROCESSES get real parallelism.

--------------------------------------------------------------------------
4. PARTIAL FAILURE - keeping the successes
--------------------------------------------------------------------------
  WITHOUT return_exceptions=True:
    gather raised HTTPStatusError (500) on the first failure.
    Every successful result was discarded.

  WITH return_exceptions=True:
    kept 16 successes, captured 4 failures
    failed indices: [0, 5, 10, 15]
    (the server fails every 5th id, so this is exactly right)

  The exceptions arrive as ORDINARY VALUES in the results list.
  If you do not check for them you will pass an exception object
  downstream as if it were data.

==========================================================================
```

### 7.3 Reading the result

**Section 1 contains a result that surprises most people.** More concurrency was *slower*:

| Strategy | Best | Speed-up |
|---|---|---|
| sequential | 3.18 s | 1.0× |
| gather (unbounded, 30 at once) | 1.21 s | 2.6× |
| **gather + semaphore(10)** | **0.39 s** | **8.1×** |
| gather + semaphore(5) | 0.70 s | 4.6× |

Firing all 30 requests simultaneously was **three times slower** than limiting to 10. The server has
a finite number of worker threads; the extra requests do not run sooner, they queue, and everything
contends.

This is the general shape of concurrency tuning: **throughput rises with concurrency until the
downstream service saturates, then flattens or falls.** The optimum — 10 here — is a property of the
service you are calling, not of your code, which is why it must be measured rather than guessed.

So "bound your concurrency" is not only about avoiding rate limits. Very often the bounded version is
simply **faster**.

**Section 2 is the bug you will actually write:**

```
async def + time.sleep (BLOCKING)                3.01s
async def + await asyncio.to_thread(...)         0.21s
```

Roughly **14× slower**, from code that uses `async def`, uses `gather`, and looks entirely
concurrent. `time.sleep` never yields to the event loop, so all 30 coroutines ran strictly one after
another — and you paid the event-loop overhead on top.

The diagnostic is mechanical and worth internalising: **an `async def` whose body contains no
`await` cannot be concurrent.** Search for that shape before profiling anything.

**Section 3 settles the CPU question with numbers:**

| Approach | vs sequential |
|---|---|
| `asyncio.gather` | ~1.0–1.2× (no real gain) |
| `ThreadPoolExecutor` | **often < 1.0× — slower** |
| `ProcessPoolExecutor` | ~2.8× |

Threads being *slower than sequential* is the striking one: the GIL prevents any parallel bytecode
execution, so you get all of the coordination overhead and none of the benefit. Only separate
processes cross the GIL.

**Section 4 shows what `return_exceptions=True` is worth.** Without it, `gather` raised on the first
`500` and **all 16 successful results were discarded** — the work was done, paid for, and thrown
away. With it: 16 successes kept, 4 failures captured, and the failed indices `[0, 5, 10, 15]` match
the server's every-fifth-id rule exactly.

The closing warning matters: those exceptions arrive as **ordinary values in the results list**.
Nothing forces you to look at them. Skip the `isinstance` check and you will pass an exception object
into downstream code as though it were a successful result.

**Verification:** confirm a bounded run beats the unbounded one, the blocking version takes roughly
the full sequential time, `ProcessPoolExecutor` is the only CPU winner, and the failed indices are
`[0, 5, 10, 15]`.

---

## 8. Common mistakes and troubleshooting

1. **Blocking calls inside `async def`.** `time.sleep`, `requests`, sync DB drivers.
2. **Forgetting `await`.** The coroutine never runs; only a warning.
3. **Unbounded `gather`.** Rate limits, file descriptors, memory.
4. **`gather` without `return_exceptions=True`** for independent work — losing successes.
5. **Not checking for exceptions in the results list** when you do use it.
6. **Fire-and-forget tasks with no reference.**
7. **Using async for CPU-bound work.**
8. **Making a whole codebase async for one call.**
9. **Creating a new `AsyncClient` per request** — same pooling loss as M2-L12.

| Error | Cause | Fix |
|---|---|---|
| `RuntimeWarning: coroutine ... never awaited` | Missing `await` | Add it, or `create_task` |
| `RuntimeError: asyncio.run() cannot be called from a running event loop` | Nested `run()` | Call it once at the top |
| `OSError: [Errno 24] Too many open files` | Unbounded concurrency | Add a semaphore |
| Many `429`s | Too much concurrency | Lower the limit; honour `Retry-After` |
| Async no faster than sync | A blocking call in the loop | Find the `async def` with no `await` |
| One failure loses everything | `gather` without `return_exceptions` | Add it and partition results |
| Task vanishes silently | No reference held | Keep it in a set with a done-callback |

---

## 9. Security, privacy, reliability and cost

- **Reliability.** Unbounded concurrency is a self-inflicted denial of service — against the provider
  and often against your own database. The semaphore is a reliability control, not an optimisation.
- **Cost.** Concurrency multiplies spend *rate*, not total spend — but a runaway loop with retries can
  burn a monthly budget in minutes. Bound concurrency **and** total requests (M8-L15).
- **Security.** Shared mutable state across concurrent tasks is a cross-request data-leak risk — the
  M2-L05 mutable-default and M2-L07 class-attribute bugs become far more dangerous under concurrency.
- **Privacy.** Interleaved logging from concurrent tasks makes traces hard to attribute. Include a
  request or task ID in every log line (M8-L17).

---

## 10. Exercises

### Exercise 1 — Beginner (~15 min)

1. Write an `async def` that sleeps 0.5 s and returns a value. Call it ten times sequentially and
   then with `gather`. Report both durations.
2. Remove one `await` and record the exact warning.
3. Replace `asyncio.sleep` with `time.sleep` and re-run the `gather` version. Report the duration and
   explain it.

### Exercise 2 — Intermediate (~30 min)

Using the lab's server:

1. Fetch 50 URLs sequentially, with unbounded `gather`, and with a semaphore of 5. Report all three.
2. Make 10 of the 50 return `500`. Show that `gather` without `return_exceptions=True` loses the
   successes, and that with it you keep 40 results and 10 errors.
3. Partition the results into successes and failures, preserving the original index of each.
4. Add a per-task timeout with `asyncio.wait_for` and show what happens when it fires.

### Exercise 3 — Challenge (~30 min)

1. Write a CPU-bound function (e.g. summing squares to 10 million). Run it 4 times: sequentially,
   with `asyncio.gather`, with `ThreadPoolExecutor`, and with `ProcessPoolExecutor`. Report all four
   and explain the pattern.
2. Explain why the async and thread versions do not help, referring to the GIL.
3. Take a blocking function and make it non-blocking with `asyncio.to_thread`. Prove the loop stays
   responsive by running a "heartbeat" coroutine that prints every 100 ms alongside it.
4. Implement the §6 version 4 (bounded + partial failure + index preservation) and test it with a
   server where 20% of requests fail.
5. Demonstrate the fire-and-forget bug: create a task without keeping a reference, have it raise, and
   show that the exception does not surface normally. Then fix it.

---

## 11. Quiz

**Q1.** Which work benefits from `asyncio`?

- A. CPU-heavy computation.  B. Waiting on network, disk or database I/O.
- C. Both equally.  D. Neither.

**Q2.** What does `time.sleep(1)` inside an `async def` do?

- A. Sleeps only that coroutine.
- B. Blocks the entire event loop, so every other task stops for one second.
- C. Raises an error.
- D. Is automatically converted to `asyncio.sleep`.

**Q3.** You call `fetch_data()` without `await`. What happens?

- A. It runs normally.
- B. A coroutine object is created and never executed; you get only a `RuntimeWarning`.
- C. `SyntaxError`.
- D. It runs in a thread.

**Q4.** Why must concurrency be bounded?

- A. To reduce memory only.
- B. Unbounded concurrency causes rate limiting, file-descriptor exhaustion, memory pressure, and can
  overwhelm the downstream service.
- C. Python limits it to 100.
- D. It does not need bounding.

**Q5.** What does `return_exceptions=True` change in `asyncio.gather`?

- A. Suppresses all errors.
- B. Exceptions are returned as values in the results list instead of propagating, so one failure does
  not discard the other successes — but you must then check for them.
- C. Retries failed tasks.
- D. Cancels remaining tasks.

**Q6.** Why does `asyncio` not speed up CPU-bound work?

- A. Coroutines are slow.
- B. The GIL allows only one thread to execute Python bytecode at a time, and async provides
  concurrency in *waiting*, not parallelism in *computing*.
- C. CPU work cannot be awaited.
- D. It does speed it up.

**Q7.** Which gives real CPU parallelism in Python?

- A. `asyncio`  B. `ThreadPoolExecutor`  C. `ProcessPoolExecutor`  D. More coroutines

**Q8.** How do `TaskGroup` and `gather` differ on failure?

- A. They are identical.
- B. `TaskGroup` cancels the remaining tasks and raises an `ExceptionGroup`; `gather` by default
  propagates the first exception while leaving other tasks running.
- C. `gather` cancels; `TaskGroup` does not.
- D. Neither handles failure.

**Q9.** An `async def` function contains no `await` anywhere. What does that suggest?

- A. It is correctly written.
- B. It is almost certainly wrong — it never yields control, so it blocks the loop for its whole
  duration and gains nothing from being a coroutine.
- C. It will not compile.
- D. It runs in a thread.

**Q10.** *(Written, rubric-graded.)* In under 80 words, explain to a colleague why their "async"
version of a script is no faster than the synchronous one.

---

## 12. Revision notes

- **The question is what you are waiting for.** I/O-bound → `asyncio`. CPU-bound → processes.
- `async def` defines a coroutine; **calling it does nothing until awaited**. `asyncio.run()` once,
  at the top.
- `gather` runs concurrently and **preserves input order**. `TaskGroup` (3.11+) cancels siblings and
  raises an `ExceptionGroup`.
- **`return_exceptions=True`** for independent work — otherwise one failure discards every success.
  Then *check* for exception values in the list.
- **A blocking call inside a coroutine freezes the whole loop.** `time.sleep`, `requests`, sync DB
  drivers. Diagnostic: **an `async def` with no `await` is almost always wrong.**
  Escape hatch: `asyncio.to_thread`.
- **Always bound concurrency with a `Semaphore`** — 5–20 for external APIs. Unbounded means `429`s,
  file-descriptor exhaustion, memory pressure, and taking down the thing you call.
- **The GIL** means threads give no CPU parallelism. `ProcessPoolExecutor` does.
- Keep references to `create_task` results, or they can be garbage-collected and their exceptions
  lost.
- **Async is contagious.** Adopt it when you need concurrency, not for a single call.

---

## 13. Completion checklist

- [ ] I can state the I/O-bound vs CPU-bound rule and pick the right tool.
- [ ] I measured sequential vs concurrent vs bounded myself.
- [ ] I reproduced the blocking-call trap and can spot it by the missing `await`.
- [ ] I showed CPU work not benefiting from async or threads, but benefiting from processes.
- [ ] I handled partial failure keeping both successes and errors with their indices.
- [ ] I always bound concurrency with a semaphore.
- [ ] I scored 7/10 on the quiz.

---

## 14. References

- Python docs, `asyncio`. <https://docs.python.org/3/library/asyncio.html> `[UNVERIFIED]`
- Python docs, `asyncio.TaskGroup`.
  <https://docs.python.org/3/library/asyncio-task.html#task-groups> `[UNVERIFIED]`
- Python docs, `concurrent.futures`.
  <https://docs.python.org/3/library/concurrent.futures.html> `[UNVERIFIED]`

---

## 15. Next lesson

→ [M2-L14 — Timeouts, Retries, Exponential Backoff and Rate Limits](M2-L14-retries-backoff.md)

You can now issue many requests at once. Next: what to do when they fail — which is often, at scale —
and how to retry without making the problem worse.
