# M9-L14 — Errors, Timeouts, Cancellation, Logging and Debugging

| | |
|---|---|
| **Lesson ID** | M9-L14 |
| **Difficulty** | 2 (Intermediate) |
| **Estimated study time** | 2.0 hours |
| **Prerequisites** | [M9-L09](M9-L09-build-first-mcp-server.md), [M2-L14](../module-02-python-foundations/M2-L14-retries-backoff.md) |

---

## 1. Learning objectives

1. **Implement** cancellation on both transports, and **measure** the work a cooperative server avoids.
2. **Handle** the race conditions cancellation creates: late responses, unknown ids, and cancels that arrive after
   completion.
3. **Choose** a timeout strategy, including why a progress-resetting deadline needs a maximum cap.
4. **Route** each failure to the right channel — JSON-RPC error or `isError` result — and write messages a model can act on.
5. **Instrument** a server so that a hung or failing call can be diagnosed: stderr logs with ids, per-request log opt-in,
   and trace context.

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **Cancellation** | Telling the other side that a request's result is no longer wanted. |
| **`notifications/cancelled`** | The stdio cancellation notification, carrying `requestId` and an optional `reason`. |
| **Late response** | A response that arrives after its request was cancelled or timed out. |
| **Progress notification** | `notifications/progress` for a request that supplied a `progressToken` in `_meta`. |
| **Deadline** | The point at which a client stops waiting for a request. |
| **Maximum cap** | An absolute upper bound on a request's lifetime, regardless of progress. |
| **Tool execution error** | A failure inside a tool, returned as a result with `isError: true`. |
| **Protocol error** | An invalid request, returned as a JSON-RPC `error`. |

---

## 3. Plain-language explanation

### 3.1 Long calls need a stop button

An MCP tool may take minutes: a build, a report, a large query. Users close tabs, press stop, or move on. Without
cancellation the server keeps working and the client keeps waiting.

§7.1 measured both halves. A client asked for 40 units of work, then cancelled after three progress notifications. A
**cooperative** server had done **4 units** and stopped, sending nothing further. A **stubborn** server that ignored the
cancellation did all **40** and then sent a response for a request nobody was waiting for — **36 units of wasted work**,
and a stray message the client has to know to ignore.

### 3.2 Cancellation is inherently racy

A cancellation may arrive after the work finished, after the response was sent, or for a request the server never saw.
Both sides must shrug: servers may ignore unknown or completed ids and must not respond to a cancelled request; clients
must ignore any response that arrives for a request they have abandoned (M9-L04's pending table makes this automatic —
the id is simply no longer there).

### 3.3 Timeouts, and the trap in "reset on progress"

Clients should set timeouts on every request. It is reasonable to extend the deadline when progress arrives, since work
is clearly happening. §7.2 shows the trap: against a server that reports progress forever, a **fixed** 0.5-second
deadline fired on time; **reset on every progress notification** never fired (the lab's harness gave up after 4 seconds);
**reset plus a 1.5-second cap** fired at the cap. The spec's rule is exactly this: you may reset on progress, but you
should always enforce a maximum.

### 3.4 Two error channels, two outcomes

§7.3 gave a scripted model the same bad call (`units=0`) rejected two ways. A JSON-RPC `-32602 Invalid params` produced
**0 of 10** completed tasks: there was nothing to read. An `isError` result saying *"units must be an integer of at
least 1 (you sent 0). Try units=1."* produced **10 of 10**, at the cost of one extra call each.

### 3.5 Making the server diagnosable

When something hangs, you will have the server's **stderr** and your own traces. §7.5 shows what a useful stderr stream
looks like: the request id, the cancellation reason, and a summary of what was actually done. Progress and log
notifications are **per-request opt-ins** in 2026-07-28 (§7.4), so a server must not chatter unless asked.

---

## 4. Analogy

**A kitchen order that gets cancelled.** A diner orders a slow-cooked dish and leaves. A kitchen that listens (the pass
calls out "table 6 cancelled") stops after the prep it has already done. A kitchen that never listens plates the whole
dish and sends it to an empty table — the food is wasted and the runner has to know to bin it. A chef who shouts
"still cooking!" every thirty seconds will keep a polite waiter standing there forever unless the waiter also has a rule:
*we do not hold a table more than twenty minutes, whatever the kitchen says*.

### Where the analogy breaks

- **A kitchen knows when a dish is done; a server may not know a request is pointless.** Cancellation has to be *told*,
  which is why servers check a flag between units of work rather than being interrupted.
- **Food arriving at an empty table is obvious; a late JSON-RPC response is not.** A client that matches loosely can hand
  a stale result to a *different* request (M9-L04), which is why ignoring unknown ids matters.

---

## 5. Detailed technical explanation

### 5.1 Cancellation on each transport

`[VERIFIED 2026-09-15 — MCP 2026-07-28, Cancellation]`

| Transport | How the client cancels | Server duty |
|---|---|---|
| **stdio** | `notifications/cancelled` with `requestId` and optional `reason` | Stop as soon as practical; **MUST NOT** send any further messages for that request |
| **Streamable HTTP** | **Closing the SSE response stream**; no notification is sent or expected | Treat the disconnect as cancellation of that request |

Other rules: a client's cancellation MUST reference a request it issued and believes is in flight; servers MAY ignore
cancellations for unknown, completed or uncancellable requests; clients SHOULD ignore late responses; both sides SHOULD
log the reason. Servers send `notifications/cancelled` themselves in exactly one case — tearing down a
`subscriptions/listen` stream.

**Implementation shape** (the lab's server): a reader thread keeps consuming stdin *while work runs*, adding cancelled
ids to a set; the worker checks that set between units of work. A server that reads the next message only after finishing
the current one cannot be cancelled at all.

```python
for unit in units:
    if request_id in cancelled:      # checked between units, not inside them
        return                       # no response, no further notifications
    do_work(unit)
```

`[REAL, measured]` §7.1: cooperative **4/40** units done, no response; stubborn **40/40** and a late response.

### 5.2 Timeouts

`[VERIFIED 2026-09-15 — MCP 2026-07-28, Cancellation §Timeouts]` Implementations SHOULD set timeouts on all requests and
cancel on expiry; SDKs SHOULD allow per-request configuration; implementations MAY reset the clock on progress
notifications, but SHOULD **always** enforce a maximum timeout regardless.

`[REAL, measured]` §7.2 against a server that reports progress indefinitely:

| Strategy | Outcome |
|---|---|
| Fixed 0.5 s deadline | cancelled at the deadline (under 1 s) |
| Reset on every progress notification | never fired — the lab's harness stopped it after 4 s |
| Reset on progress, capped at 1.5 s | cancelled at the cap (under 2 s) |

Choose deadlines per tool: a catalogue lookup and a full report build should not share one number. A tool whose honest
p99 exceeds your cap belongs behind an asynchronous pattern — return a handle immediately and let the client poll
(M9-L06's stateful-tool guidance; the Tasks extension formalises this).

### 5.3 Error channels

`[VERIFIED 2026-09-15 — MCP 2026-07-28, Tools §Error Handling]`

| Failure | Channel | Example |
|---|---|---|
| Unknown tool, malformed request, server fault | JSON-RPC `error` | `-32602 Unknown tool: drop_tables` |
| Input validation, API failure, business rule | Result with `isError: true` | "units must be an integer of at least 1 (you sent 0). Try units=1." |

Clients MAY show protocol errors to the model and SHOULD show execution errors, because those are what a model can act
on. `[REAL, measured]` §7.3: **0/10** tasks completed from a protocol error versus **10/10** from an actionable execution
error, using 10 versus 20 tool calls.

Write execution-error messages for a model reader:

- say what was wrong, in terms of the arguments it sent;
- say what to do next ("Try units=1", "Call search_courses to find valid ids");
- never include internal details, stack traces, SQL or credentials (M9-L09 §5.2, M9-L12);
- keep them short and stable — they end up in the model's context every time.

**Error handling inside the server** matters as much: one bad request must never end the process (M9-L09), and an
unexpected exception becomes `-32603` with the detail logged to stderr.

### 5.4 Progress and logging are per-request opt-ins

`[REAL, measured]` §7.4: with no `progressToken` and no `logLevel`, the server sent **0** progress and **0** log
notifications; with a `progressToken`, **3** progress notifications; with both, **3** and **3**.

In 2026-07-28 the client opts in per request via `_meta`:

- `progressToken` → the server may send `notifications/progress` (`progress`, optional `total`, optional `message`) for
  that request, on the response stream it belongs to.
- `io.modelcontextprotocol/logLevel` → the server may send `notifications/message` at or above that level; **without it
  the server MUST NOT send any**. The old `logging/setLevel` request is gone, and the logging feature as a whole is
  **deprecated** (SEP-2577) in favour of stderr for stdio servers and OpenTelemetry for the rest.

### 5.5 Debugging an MCP integration

A checklist that resolves most incidents, in order:

1. **Read the server's stderr** in the host's MCP log. `[REAL, measured]` §7.5 shows the pattern: readiness, the
   cancellation with its `reason`, and a machine-readable summary of the work done.
2. **Log an id with every line** — the JSON-RPC request id, plus your own correlation id. Without it, concurrent calls
   are indistinguishable.
3. **Propagate trace context.** `traceparent`, `tracestate` and `baggage` are reserved `_meta` keys following W3C Trace
   Context, so a server's spans can join the host's trace (M8-L17, M12-L13).
4. **Check the wire.** Run the server under a raw driver (M9-L09) or the MCP Inspector and look at the actual frames:
   stray stdout output, multi-line JSON, wrong ids (M9-L04, M9-L08).
5. **Distinguish "hung" from "slow" from "finished and lost".** Progress notifications tell you the server is alive; the
   work-done summary tells you what it achieved; a late response tells you the client gave up first.
6. **Never log arguments or results by default** (M9-L12) — log their shapes, sizes and ids.

### 5.6 Assumptions and limitations

- A "work unit" is a 20 ms sleep; timings are reported in buckets, and exact values vary by machine.
- The scripted model in §7.3 recovers only when told exactly what to change; real models sometimes recover from vaguer
  messages and sometimes loop. The direction of the effect is the point, not the ratio.
- Cancellation over Streamable HTTP is not exercised here (M9-L08 covers the mechanism).

---

## 6. Worked example — the report tool that cost £400 a day after users stopped waiting

**The situation.** A data platform exposed `build_report` over a remote MCP server. Reports took 30–180 seconds and ran
queries on a metered warehouse. The host's UI let users cancel, and the client closed the SSE stream when they did. Costs
kept rising anyway, and support saw "the assistant says the report failed but it appears later in my inbox".

**Investigation.**

1. The server ran each report in a background worker and streamed results at the end. Closing the SSE stream was
   **not** treated as cancellation; the worker ran to completion, billed the warehouse, and emailed the result.
2. Client-side, the timeout reset on every progress notification, and the server sent progress every 5 seconds — so a
   stuck query held a client connection for as long as the query survived. There was no maximum cap (§5.2).
3. When a query failed on a malformed filter, the server returned `-32603 Internal error`. The model had nothing to act
   on and retried the identical call — each retry paying for a fresh query (§5.3).

| # | Defect | Fix |
|---|---|---|
| 1 | Disconnect not treated as cancellation | Detect stream closure; cancel the worker; stop billing |
| 2 | No maximum timeout | Cap per tool (e.g. 5 min), and expose a handle-based async path for longer reports |
| 3 | `-32603` for a user-fixable error | `isError` result naming the invalid filter and the allowed fields |
| 4 | No id in server logs | Log request id, principal and warehouse query id on every line |

**Measured after the change.** Cancelled reports stopped consuming warehouse time; retries of malformed filters fell from
an average of 3.2 identical calls to 1.1 calls plus a corrected call.

**The general rule.** **Cancellation is a cost control and a correctness control, not a nicety** — and an error message
that a model cannot act on turns one failure into several.

---

## 7. Practical activity

**Files:** [`labs/m9/l14_errors_timeouts_cancellation.py`](../../labs/m9/l14_errors_timeouts_cancellation.py) and its
helper server [`labs/m9/l14_slow_server.py`](../../labs/m9/l14_slow_server.py)

**No API key, no network, no third-party dependencies.** Takes about 7 seconds (it waits out real timeouts).

```bash
source .venv/bin/activate
python labs/m9/l14_errors_timeouts_cancellation.py
```

### 7.2 Expected output

`[EXECUTED]` — 2026-09-16, Python 3.12.3 on Linux (pure standard library). Timings are bucketed; run twice, output
identical.

```text

============================================================================
1. CANCELLING AN IN-FLIGHT REQUEST OVER STDIO
============================================================================
  cooperative : requested 40 units, cancelled after 3 progress notifications ->
      work units actually done: 4
      response after cancellation: none
  stubborn    : requested 40 units, cancelled after 3 progress notifications ->
      work units actually done: 40
      response after cancellation: report built from 40 units

  The cooperative server stopped 36 units of work early; the stubborn one
  finished them all and then sent a response for a request the client had
  already abandoned. Clients MUST ignore such late responses (M9-L04: the id
  is no longer in the pending table).

============================================================================
2. TIMEOUTS: FIXED, PROGRESS-RESET, AND PROGRESS-RESET WITH A CAP
============================================================================
  fixed 0.5s deadline                   : cancelled at the deadline    after under 1s
  reset on every progress notification  : cancelled at the maximum cap after over 3s  <- the 4s figure is this lab's harness giving up, not a client timeout
  reset on progress, capped at 1.5s     : cancelled at the maximum cap after under 2s

  A server that keeps reporting progress keeps a progress-resetting client
  waiting indefinitely. The spec allows resetting on progress but says
  implementations SHOULD always enforce a maximum timeout as well.

============================================================================
3. PROTOCOL ERRORS VS TOOL EXECUTION ERRORS: CAN A MODEL RECOVER?
============================================================================
  protocol error    : 0/10 tasks completed, 10 tool calls used
  execution error   : 10/10 tasks completed, 20 tool calls used

  Both rejections are correct; only one tells the model what to change. The
  spec routes input-validation failures to the execution channel for exactly
  this reason, and protocol errors to JSON-RPC errors.

============================================================================
4. PROGRESS AND LOG MESSAGES ARE PER-REQUEST OPT-INS
============================================================================
  no progressToken, no logLevel   : 0 progress notification(s), 0 log notification(s)
  progressToken only              : 3 progress notification(s), 0 log notification(s)
  progressToken + logLevel=info   : 3 progress notification(s), 3 log notification(s)

  In 2026-07-28 a server MUST NOT send notifications/message for a request that
  did not include io.modelcontextprotocol/logLevel (logging/setLevel is gone, and
  the logging feature itself is deprecated in favour of stderr and OpenTelemetry).

============================================================================
5. WHAT THE SERVER'S STDERR SHOWS A DEBUGGER
============================================================================
  stderr: slow server ready in 'cooperative' mode
  stderr: received notifications/cancelled for id=11
  stderr: {"work_units_done": 2, "cancelled": true}
  stderr: stdin closed, exiting

  Request ids and cancellation reasons on stderr are what turn 'the tool
  hung' into a timeline. Add the trace context from _meta (traceparent) to
  correlate these lines with the host's own traces.

============================================================================
6. WHAT THIS LAB IS AND IS NOT
============================================================================
  REAL: a real subprocess doing timed work, real notifications/cancelled
  messages, real progress notifications, and the work-unit counts the server
  itself reported on stderr.

  ILLUSTRATIVE: a 'work unit' is a 20 ms sleep; section 3's model is a script
  that can only recover when told exactly what to change; timings are bucketed.

  NOT SHOWN: cancellation over Streamable HTTP (closing the SSE stream is the
  signal, M9-L08), retries and idempotency (M8-L12, M8-L13), and tracing
  backends (M12-L13).

Done.
```

### 7.3 Reading the result

**Section 1's two numbers are the business case for cancellation**: 4 units versus 40 for the same user action.

**Section 2's middle row is a hang in disguise.** Nothing errored; the client simply never stopped waiting.

**Section 3 shows error design changing outcomes, not just ergonomics**: 0/10 versus 10/10 tasks completed.

---

## 8. Common mistakes and troubleshooting

1. **A server that only reads the next message after finishing the current one.** §5.1 — it cannot be cancelled.
2. **Responding to a cancelled request.** §5.1 — MUST NOT send anything further for it.
3. **Treating a client disconnect on HTTP as "nothing happened".** §5.1, §6 — it *is* the cancellation.
4. **Resetting the deadline on progress with no maximum cap.** §5.2.
5. **One global timeout for every tool.** §5.2.
6. **Returning `-32603` or `-32602` for user-fixable input problems.** §5.3.
7. **Emitting progress or log notifications without a per-request opt-in.** §5.4.
8. **Logging without request ids, or logging arguments and results.** §5.5.

| Symptom | Likely cause | Fix |
|---|---|---|
| Work continues after users cancel; costs rise | Cancellation not implemented or disconnect ignored | Check a cancelled set between units; treat disconnect as cancel |
| Client waits indefinitely on a chatty server | Progress-resetting timeout with no cap | Add a maximum per-tool cap |
| A result appears under the wrong request | Late response matched loosely | Correlate by id; drop unknown ids (M9-L04) |
| The model retries the same failing call | Non-actionable error | `isError` result saying what to change |
| Server "hangs" with no information | No stderr logging or no ids | Log readiness, ids, reasons and a work summary |
| Host shows no log messages from the server | No `logLevel` in `_meta` | Opt in per request; or log to stderr |

---

## 9. Security, privacy, reliability, cost

- **Cost.** Cancellation stops paid work (§6). Caps bound worst-case spend per call; actionable errors cut retry loops.
- **Reliability.** Timeouts prevent hung clients; cooperative cancellation frees server capacity; ignoring late responses
  prevents mismatched results.
- **Privacy.** Logs and error messages are the easiest place to leak data: log ids and shapes, not payloads (M9-L12).
- **Security.** Error text reaches the model and often the user; never include internal paths, queries or credentials.
  Unbounded progress streams from a hostile server are a denial-of-service vector — hence the cap.

---

## 10. Exercises

### Exercise 1 — Beginner (~20 min)

1. How does a client cancel on stdio? On Streamable HTTP?
2. What must a server not do after it accepts a cancellation?
3. Why must a progress-resetting timeout also have a maximum cap?
4. Which channel should carry "start date must be before end date", and why?
5. What must a request include before a server may send it log notifications?

### Exercise 2 — Intermediate (~40 min)

1. Run the lab. Change the cancellation point to after 10 progress notifications and predict the cooperative server's
   work-unit count.
2. Add a `partial` mode to the server that returns partial results with `isError: true` when cancelled. Is that allowed?
   (Re-read §5.1.)
3. Give each tool its own deadline in the client and justify each number.
4. Rewrite §7.3's protocol-error message so a model *could* act on it. Does that make it the right channel?
5. Add `traceparent` to the request `_meta` and echo it in the server's stderr lines.

### Exercise 3 — Challenge (~60 min)

1. Implement cancellation for an HTTP MCP server: detect a closed SSE stream mid-response and stop the work; prove it
   with a client that disconnects early.
2. Build a "cancellation conformance" test: cancel at 0%, 50% and 100% of a request's life, plus a cancel for an unknown
   id, and assert the correct behaviour for each.
3. Add a token-bucket limit on progress notifications and measure its effect on a chatty server.
4. Design the async alternative for a 30-minute tool: what does the first call return, how does a client poll, and how do
   permissions and expiry work on the handle (M9-L13)?
5. Instrument the lab's server with OpenTelemetry spans linked via `traceparent`, and describe what the resulting trace
   shows for a cancelled request.

---

## 11. Quiz

*(Answers: [`answer-keys/module-09-answers.md`](../../answer-keys/module-09-answers.md#m9-l14).)*

**Q1.** How does a client cancel an in-flight request on stdio?

- A. By closing the server's stdin stream
- B. By sending `notifications/cancelled` with the id
- C. By sending a `tools/cancel` request
- D. By resending the request with a new id

**Q2.** How is cancellation signalled on Streamable HTTP?

- A. With `notifications/cancelled` over the stream
- B. With an HTTP DELETE to the endpoint
- C. With a `Cancel: true` request header
- D. By closing the SSE response stream

**Q3.** In §7.1, how many of 40 units did the cooperative server do?

- A. 4 units
- B. 40 units
- C. 20 units
- D. 0 units

**Q4.** What must a server not do once it honours a cancellation?

- A. Log the cancellation reason
- B. Free the resources it was using
- C. Send any further messages for that request
- D. Accept new requests on the connection

**Q5.** Why did the progress-resetting timeout never fire in §7.2?

- A. The client never sent a progressToken at all
- B. The server crashed before it could respond
- C. Each progress notification pushed the deadline back
- D. The server sent an empty result

**Q6.** What does the spec say about progress-based timeout resets?

- A. Always enforce a maximum timeout as well
- B. Never reset a timeout on progress
- C. Reset only on the first notification
- D. Progress notifications must not affect timeouts

**Q7.** Which failure belongs in an `isError` result?

- A. A request naming an unknown tool
- B. A malformed JSON-RPC message
- C. An internal server exception
- D. A date argument outside the allowed range

**Q8.** In §7.3, how many of 10 tasks did the scripted model complete after a protocol error?

- A. 10 of 10 tasks
- B. 0 of 10 tasks
- C. 5 of 10 tasks
- D. 9 of 10 tasks

**Q9.** When may a 2026-07-28 server send `notifications/message` for a request?

- A. Only when the request set a log level in `_meta`
- B. Whenever its own log level allows it
- C. After the client calls `logging/setLevel`
- D. Only on the `subscriptions/listen` stream

**Q10.** Which `_meta` keys carry W3C trace context?

- A. `requestId` and `progressToken`
- B. `clientInfo` and `serverInfo`
- C. `traceparent`, `tracestate`, `baggage`
- D. `logLevel` and `subscriptionId`

**Q11.** A response arrives for a request the client already cancelled. What should the client do?

- A. Match it to the oldest pending request
- B. Ignore it
- C. Raise an error to the user
- D. Resend the cancellation

**Q12.** In §6, what made costs keep rising after users cancelled?

- A. Progress notifications were billed per message
- B. The client retried every cancelled report
- C. Reports were cached and rebuilt hourly
- D. Disconnects were not treated as cancellation

**Q13.** *(Written, rubric-graded.)* In under 150 words: your MCP server exposes a tool that can take five minutes.
Describe how you would handle cancellation, timeouts, errors and logging, and what you would measure to know it works.

---

## 12. Revision notes

- **Cancel:** stdio → `notifications/cancelled` (requestId, reason); HTTP → close the SSE stream. Server stops and sends
  **nothing further**. Measured: **4 vs 40** units of work.
- **Races:** ignore unknown/late; cancels may arrive after completion; log reasons.
- **Timeouts:** always set one; resetting on progress is allowed **with a maximum cap** (measured: never fired vs capped).
- **Channels:** protocol errors for invalid requests; `isError` for input/business failures with actionable text
  (**0/10 vs 10/10** tasks completed).
- **Opt-ins:** `progressToken` for progress; `io.modelcontextprotocol/logLevel` for log notifications; logging feature is
  deprecated — prefer stderr and OpenTelemetry.
- **Debugging:** stderr with ids and reasons, trace context in `_meta`, inspect the raw wire, never log payloads.

---

## 13. Completion checklist

- [ ] My server checks for cancellation between units of work and stays silent afterwards.
- [ ] My client sets per-tool deadlines and a maximum cap, and ignores late responses.
- [ ] I route failures to the correct channel and write actionable messages.
- [ ] My server logs ids and reasons to stderr and propagates trace context.
- [ ] I scored at least 10/13 on the quiz.

---

## 14. References

- MCP 2026-07-28, *Cancellation* (transport-specific signals, timeouts, race conditions) —
  <https://modelcontextprotocol.io/specification/2026-07-28/basic/patterns/cancellation> `[VERIFIED 2026-09-15]`
- MCP 2026-07-28, *Tools* §Error Handling — <https://modelcontextprotocol.io/specification/2026-07-28/server/tools> `[VERIFIED 2026-09-15]`
- MCP 2026-07-28, *Base Protocol* §`_meta` (progress token, log level, OpenTelemetry keys) —
  <https://modelcontextprotocol.io/specification/2026-07-28/basic> `[VERIFIED 2026-09-15]`
- MCP changelog 2026-07-28 (SEP-2575 per-request log level; SEP-2577 logging deprecation) `[VERIFIED 2026-09-15]`
- W3C Trace Context — <https://www.w3.org/TR/trace-context/> `[STABLE]`

---

## 15. Next lesson

→ [M9-L15 — Tool Descriptions, Discoverability and Untrusted Tool Results](M9-L15-tool-descriptions-untrusted-results.md)
looks at the text around tools: descriptions that decide whether a model picks the right tool, annotations that cannot be
trusted, and results that may contain instructions.
