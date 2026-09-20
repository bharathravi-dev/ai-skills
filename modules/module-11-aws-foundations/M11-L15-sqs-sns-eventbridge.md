# M11-L15 — SQS, SNS and EventBridge

| | |
|---|---|
| **Lesson ID** | M11-L15 |
| **Difficulty** | 2 (Intermediate) |
| **Estimated study time** | 2.0 hours |
| **Prerequisites** | [M11-L13](M11-L13-lambda-api-gateway.md), [M8-L12](../module-08-agentic-ai/M8-L12-idempotency-duplicate-prevention.md) |

---

## 1. Learning objectives

1. **Show** how a queue converts an availability problem into a latency problem, with numbers.
2. **Set** the visibility timeout from p99 processing time, and explain the duplicates a short one creates.
3. **Treat at-least-once delivery as a requirement on your handler**, not a caveat in the documentation.
4. **Configure** `maxReceiveCount` and a dead-letter queue, and understand FIFO head-of-line blocking.
5. **Choose** between SQS, SNS and EventBridge from the requirement, and combine them correctly.

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **SQS** | A queue: producers send, consumers poll, messages are deleted when processed. |
| **SNS** | Publish/subscribe fan-out: one message pushed to many subscribers. |
| **EventBridge** | An event bus that routes by event *content* to targets, with schemas, archive and replay. |
| **Visibility timeout** | How long a received message is hidden from other consumers before redelivery. |
| **At-least-once** | A message may be delivered more than once; the handler must tolerate it. |
| **FIFO queue** | Ordered delivery within a *message group*, with deduplication. |
| **`maxReceiveCount`** | How many times a message is delivered before moving to the dead-letter queue. |
| **DLQ** | Dead-letter queue: where messages go after repeated failures. |
| **Head-of-line blocking** | In FIFO, a stuck message blocks every later message in its group. |
| **Backlog** | Messages waiting; its depth over time is your primary health signal. |

---

## 3. Plain-language explanation

### 3.1 A queue turns rejections into waiting

§7.1: workers handle 60/s, traffic peaks at 260/s for 20 seconds. **Without** a queue, **4,000 of 7,200 requests —
55.6% — are rejected** with errors. **With** a queue, **nothing is rejected**: the backlog peaks at 4,000, the worst wait
is **66.7 s**, and it drains **40 s** after the spike ends.

That is a good trade for ingestion, embedding, indexing and notifications, and a bad one for a user waiting for an
answer — so use it where the work can be asynchronous, and tell the user it is queued (M10-L09).

### 3.2 A short visibility timeout manufactures duplicates

§7.2: with a 30-second timeout, a **95-second model call is redelivered every single time**. The first worker eventually
finishes and deletes the message; the second copy has already done the work again.

### 3.3 At-least-once is a requirement on your handler

§7.3: at a 2.09% duplication rate over 200,000 messages, **4,173 duplicates** arrive. **3 of 6** example handlers
misbehave — charging twice, emailing twice, double-counting — roughly **2,086 times**. The three that are fine are fine
because they key on something stable.

### 3.4 A poison message wastes a worker, or blocks a group

§7.4: with `maxReceiveCount` at 100, a permanently failing message consumes **3,000 worker-seconds** before giving up.
Without a DLQ it is retried until retention expires — up to **11,520 attempts** at a four-day default. In a **FIFO**
queue it is worse: it blocks every later message in its group.

### 3.5 Three services, three jobs

§7.5: SQS is a **buffer**; SNS is a **fan-out**; EventBridge is a **router** with schemas, archive and replay. The
production pattern combines them: fan out with SNS or EventBridge, and put an SQS queue **in front of each consumer** so a
slow or broken consumer buffers its own backlog rather than losing messages.

---

## 4. Analogy

**A restaurant kitchen's order rail.** Without the rail, when twelve tables order at once the waiter turns people away.
With it, every order is accepted and the wait grows — better, provided the diners are told. The chef takes a ticket off
the rail and it is hidden from the others; if she takes too long and it reappears, two chefs cook the same dish. A ticket
nobody can cook — an ingredient that does not exist — goes back on the rail forever unless someone moves it to the "ask
the manager" spike. And the pass calls out one order to several stations (fan-out) while each station keeps its own rail.

### Where the analogy breaks

- **A rail is visible; a backlog is a metric** you must choose to watch, and a queue that quietly grows for a week looks
  healthy from the producer's side (§5.6).
- **A chef notices she is cooking a duplicate; your handler will not** unless you gave it an idempotency key (§5.4).

---

## 5. Detailed technical explanation

### 5.1 Why a queue

`[REAL, simulated]` §7.1 — 55.6% rejected versus 0%, at the cost of a 66.7-second worst wait.

The queue gives you four things at once: **spike absorption**, **bounded concurrency downstream** (the consumer decides
its own rate, protecting a database — L14 §5.3), **retries with a defined failure destination**, and **decoupling** so the
producer does not fail when the consumer does.

For an AI system the natural asynchronous boundaries are: document ingestion and chunking (M7-L03), embedding and
indexing (M6-L10), evaluation runs (M10-L12), notifications and webhooks, and any agent action that is allowed to take
minutes (M8-L04).

### 5.2 Standard and FIFO

| | Standard | FIFO |
|---|---|---|
| Ordering | Best-effort | Strict, **within a message group** |
| Delivery | At-least-once | Exactly-once processing within the deduplication window |
| Throughput | Very high | Lower, and bounded per message group |
| Poison message | Wastes a worker | **Blocks its whole group** |

Use FIFO only when order genuinely matters, and choose the **message group id** carefully: one group per tenant or per
conversation gives ordering where it matters and parallelism everywhere else. A single group id serialises your entire
system.

### 5.3 Visibility timeout

`[REAL, computed]` §7.2.

```text
visibility_timeout > p99 processing time, with margin
```

Two better techniques than a large fixed value: **extend the timeout from the worker** as it makes progress (a heartbeat),
and keep handlers short by splitting long work into stages with their own queues. A very large blanket timeout delays
legitimate redelivery after a worker crash, so it is a trade-off, not a free setting.

Watch for a related trap: with Lambda consuming SQS, the **function timeout** and the **visibility timeout** must agree,
or you get duplicates or stuck messages (L13 §5.5).

### 5.4 Idempotency

`[REAL, computed]` §7.3 — 4,173 duplicates, 3 of 6 handlers affected.

```python
# the standard shape: a conditional write on a natural key
key = f"{message['type']}:{message['id']}:{message['version']}"
try:
    table.put_item(Item={"pk": key, "ts": now, "ttl": now + 7 * 86400},
                   ConditionExpression="attribute_not_exists(pk)")
except ConditionalCheckFailedException:
    return                      # already processed; a no-op, not an error
do_the_work(message)
```

Three details that matter: the key comes from the **message content**, not the delivery; the marker has a **TTL** longer
than the queue's retention; and the marker is written **before** the side effect if the side effect is not itself
idempotent (M8-L12).

### 5.5 Dead-letter queues

`[REAL, computed]` §7.4 — 3,000 worker-seconds at `maxReceiveCount` 100; up to 11,520 attempts with no DLQ.

- Set `maxReceiveCount` to a **small** number — 3 to 5 for most handlers.
- **Alarm on DLQ depth > 0.** Anything in the DLQ is an incident with a cause (M10-L14).
- Keep a **redrive** path so fixed messages can be replayed once the bug is fixed.
- Distinguish **transient** failures (retry helps) from **permanent** ones (malformed message — send it to the DLQ
  immediately rather than burning retries).

### 5.6 Monitoring a queue

The three signals, in order of usefulness:

| Signal | Tells you |
|---|---|
| **Age of the oldest message** | Whether consumers are keeping up — better than depth, which hides a slow drain |
| Queue depth and its trend | Backlog size; alarm on sustained growth |
| DLQ depth | Something is broken and being dropped |

Plus consumer-side: processing duration p99 (feeds §5.3) and error rate by cause.

### 5.7 Choosing between the three

`[REAL, matched]` §7.5.

| Requirement | Service |
|---|---|
| Buffer work; one logical consumer; do not lose it | **SQS** |
| One event, many independent consumers | **SNS** or **EventBridge** |
| Route by event content to different targets | **EventBridge** |
| Ordering per entity | **SQS FIFO** |
| React to AWS service events | **EventBridge** |
| Replay past events after a fix | **EventBridge** (archive and replay) |

The combination to default to: **EventBridge (or SNS) → SQS per consumer → consumer**. Fan-out decouples producers from
consumers; the per-consumer queue means one broken consumer does not lose messages or slow the others.

### 5.8 Assumptions and limitations

- Traffic figures, capacity, duplication rates and processing times are invented.
- Default retention, visibility and quota values change; check current documentation.
- Long polling, batching, message attributes, Step Functions and streaming (Kinesis) are out of scope (M12-L09).

---

## 6. Worked example — the ingestion queue that was "fine" for a week

**The situation.** A document ingestion pipeline used SQS with a Lambda consumer. A dashboard showed queue depth, and it
was near zero. Then a customer reported that documents uploaded the previous Tuesday still were not searchable.

**What was happening.**

1. A subset of documents — a specific PDF variant — failed to parse and threw. `maxReceiveCount` was **1000** and there
   was **no DLQ** (§7.4).
2. Those messages were redelivered continuously, consuming consumer capacity, and being counted as "in flight" rather
   than "available" — so **queue depth looked low** (§5.6).
3. The right signal was **age of the oldest message**, which was **six days** and not on any dashboard.
4. The Lambda's function timeout was 300 s while the visibility timeout was 30 s, so long-running messages were also
   being processed in duplicate (§5.3, L13 §5.5).
5. The handler was not idempotent, so duplicates produced duplicate chunks in the index, quietly degrading retrieval
   (M7-L05).

| # | What went wrong | Fix |
|---|---|---|
| 1 | No DLQ, huge `maxReceiveCount` | `maxReceiveCount` 5, DLQ, alarm on depth > 0 |
| 2 | Monitored depth, not age | Alarm on age of oldest message |
| 3 | Visibility timeout below function timeout | Align them; extend from the worker |
| 4 | Non-idempotent handler | Conditional write on a content key (§5.4) |
| 5 | Parse failure treated as transient | Classify permanent failures; DLQ immediately |

**The general rule.** **Alarm on the age of the oldest message. Queue depth can be zero while nothing is getting
done.**

---

## 7. Practical activity

**File:** [`labs/m11/l15_sqs_sns_eventbridge.py`](../../labs/m11/l15_sqs_sns_eventbridge.py)

**No AWS account, no network, no third-party dependencies.** Seeded, so the figures below reproduce exactly.

```bash
source .venv/bin/activate
python labs/m11/l15_sqs_sns_eventbridge.py
```

### 7.2 Expected output

`[EXECUTED]` — 2026-09-17, Python 3.12.3 (pure standard library). Seeded with `random.Random(1115)`; run twice, output
identical.

```text

============================================================================
1. A SPIKE, WITH AND WITHOUT A QUEUE
============================================================================
  worker capacity 60/s; arrivals peak at 260/s for 20 s

  WITHOUT a queue (synchronous):
    offered 7,200 requests, rejected 4,000 (55.6%) with errors
    users affected immediately; the spike is lost work

  WITH a queue:
    rejected 0; peak backlog 4,000 messages
    worst wait 66.7 s; back to normal 40 s after the spike ended
    total work done: 7,200 -- nothing was lost

  The queue converts an AVAILABILITY problem into a LATENCY problem. That is
  a good trade for ingestion, embedding, indexing and notifications, and a
  bad one for a user waiting for an answer. Use it where the work can be
  asynchronous, and tell the user it is queued (M10-L09).

============================================================================
2. VISIBILITY TIMEOUT VS PROCESSING TIME
============================================================================
  a message is redelivered if not deleted within the visibility timeout

  processing time                       30 s        60 s       300 s       900 s
  fast path (4 s)                         ok          ok          ok          ok
  typical (22 s)                          ok          ok          ok          ok
  slow: long model call (95 s)   REDELIVERED REDELIVERED          ok          ok
  stuck: downstream hang (400 s) REDELIVERED REDELIVERED REDELIVERED          ok

  A message redelivered while still being processed is now being processed
  TWICE -- and the first worker will finish and delete it, so the second copy
  does the work again. With a 30 s timeout, any model call over 30 s
  duplicates every single time. Set the timeout above your p99 processing
  time, or extend it from the worker as it goes (M13-L11).

============================================================================
3. AT-LEAST-ONCE: HOW OFTEN DOES A DUPLICATE ARRIVE?
============================================================================
  200,000 messages processed

  duplicates delivered: 4,173 (2.09%)

  what the handler does                 effect of a duplicate     needs a key?
  append a row to an audit log          harmless duplicate row    no
  index a chunk (same id)               idempotent by key         no
  charge a customer                     CHARGED TWICE             YES
  send a notification email             EMAILED TWICE             YES
  increment a counter                   COUNT IS WRONG            YES
  call the model and store by hash      idempotent by content     no

  handlers that must be made idempotent: 3/6
  at 2.09% duplication, 3 of 6 handlers would misbehave ~2,086 times
  'At-least-once' is not a caveat in the documentation; it is a requirement
  on your handler. Store an idempotency key, conditionally write it, and
  make the second delivery a no-op (M8-L12).

============================================================================
4. A POISON MESSAGE, AND WHAT A DLQ SAVES
============================================================================
  one message always fails, taking 30 s of a worker each time

    maxReceiveCount   attempts   worker-seconds wasted   then                            
                  1          1                      30   moved to the DLQ                
                  3          3                      90   moved to the DLQ                
                  5          5                     150   moved to the DLQ                
                100        100                    3000   retried until it expires (days) 

  without a DLQ, the message is retried until the retention period expires:
    at a 4-day default retention, that is up to 11,520 attempts of 30 s each
  In a STANDARD queue the poison message only wastes a worker. In a FIFO
  queue it BLOCKS its message group entirely: every later message for that
  group waits behind it. Set maxReceiveCount to a small number, alarm on
  DLQ depth, and treat anything in the DLQ as an incident with a cause
  (M10-L14).

============================================================================
5. SQS, SNS OR EVENTBRIDGE?
============================================================================
  requirement                                             fits                    
  absorb a spike; one consumer; work must not be lost     SQS                     
  one event, five unrelated consumers, fan out            SNS or EventBridge      
  route events by their CONTENT to different targets      EventBridge             
  strict ordering per customer                            SQS FIFO                
  react to an AWS service event (S3 object created)       EventBridge             
  replay last week's events after fixing a bug            EventBridge (archive + replay)

  The short version: SQS is a BUFFER between a producer and a consumer that
  may be slower. SNS is a FAN-OUT: one message, many subscribers, push
  delivery. EventBridge is a ROUTER: rules match event content and send it
  to targets, with schemas, archive and replay.
  The common production pattern combines them: EventBridge or SNS for fan-out,
  with an SQS queue in front of EACH consumer so that a slow or broken
  consumer buffers its own backlog instead of losing messages.

============================================================================
6. WHAT THIS LAB IS AND IS NOT
============================================================================
  REAL: every backlog figure, redelivery verdict, duplicate count, wasted
  worker-second and routing match above is computed by this script.

  DOCUMENTED BEHAVIOUR: standard SQS is at-least-once with best-effort
  ordering; a message not deleted within the visibility timeout is
  redelivered; maxReceiveCount moves a message to a dead-letter queue; FIFO
  queues preserve order within a message group.

  ILLUSTRATIVE: traffic figures, capacity, duplication rates and processing
  times are invented. Default retention and visibility values change --
  check current documentation.

  NOT SHOWN: long polling, batching, message attributes, Step Functions, and
  Kinesis/streaming (M12-L09).

Done.
```

### 7.3 Reading the result

**Section 1's two blocks** are the same spike with two architectures: 4,000 errors, or a 67-second wait.

**Section 2's third row** is the AI-specific trap: any model call longer than the visibility timeout duplicates every
time.

**Section 3's "needs a key?" column** is the design checklist for every handler you write.

**Section 4's last row** is what happens without a DLQ: 11,520 attempts.

---

## 8. Common mistakes and troubleshooting

1. **Putting a user-facing request behind a queue without telling the user.** §7.1 — latency instead of an error is only
   better if it is communicated (M10-L09).
2. **Visibility timeout below p99 processing time.** §7.2.
3. **Lambda function timeout and visibility timeout disagreeing.** §5.3.
4. **Assuming exactly-once on a standard queue.** §7.3.
5. **Non-idempotent handlers.** §5.4 — 3 of 6 in the lab.
6. **No DLQ, or a huge `maxReceiveCount`.** §7.4.
7. **Monitoring depth instead of age of oldest message.** §6.
8. **One FIFO message group for everything.** §5.2 — it serialises the system.
9. **Fan-out without a queue per consumer.** §5.7 — one slow consumer loses messages.

| Symptom | Likely cause | Fix |
|---|---|---|
| Work is processed twice | Visibility timeout too short, or no idempotency | Raise/extend the timeout; add an idempotency key |
| Queue depth is zero but nothing completes | Messages in flight, failing repeatedly | Alarm on age of oldest; add a DLQ |
| One tenant's messages block everything | Single FIFO message group | Group per tenant or conversation |
| Consumers overwhelm the database | Unbounded consumer concurrency | Cap concurrency; that is the queue's job |
| Messages disappear silently | DLQ exists but is unmonitored | Alarm on DLQ depth > 0 |

---

## 9. Security, privacy, reliability, cost

- **Security.** Queue policies control who may send and receive; encrypt with a customer-managed key and restrict by
  `aws:SourceVpce` where appropriate (L08, L17).
- **Privacy.** Message bodies often contain user text — apply the hash-and-store pattern and set retention deliberately
  (M10-L06, M10-L13).
- **Reliability.** The queue is what makes retries safe and bounds downstream load; the DLQ is what makes failure visible.
- **Cost.** Per-request pricing is small, but a poison-message retry loop and a fan-out with many subscribers are both
  real spend; alarm on them (L06).

---

## 10. Exercises

### Exercise 1 — Beginner (~20 min)

1. What proportion of requests was rejected without a queue in §7.1?
2. Which processing times are redelivered at a 60-second visibility timeout?
3. Which three handlers in §7.3 need an idempotency key, and why?
4. How many attempts does a poison message get with no DLQ at four-day retention?
5. Which service routes by event content?

### Exercise 2 — Intermediate (~40 min)

1. Run the lab. Double the worker capacity and re-read section 1.
2. Add a 150-second processing time to §7.2 and choose a visibility timeout.
3. Add two handlers from your own system to §7.3 and classify them.
4. Compute the worker-seconds wasted at `maxReceiveCount` 5 with a 95-second handler.
5. Draw the fan-out design for an event with three consumers, one of which is slow.

### Exercise 3 — Challenge (~60 min)

1. Write an idempotent handler with a conditional write and a TTL, and test it with a deliberate duplicate.
2. Implement visibility-timeout extension from a long-running worker.
3. Set up DLQ alarms and a redrive procedure, and document it in the runbook (M10-L14).
4. Model your own spike: arrival profile, consumer capacity, resulting backlog and worst wait.
5. Choose the message group id for a FIFO use case in your system, and justify the parallelism it allows.

---

## 11. Quiz

*(Answers: [`answer-keys/module-11-answers.md`](../../answer-keys/module-11-answers.md#m11-l15).)*

**Q1.** What does a queue convert an availability problem into?

- A. A consistency problem
- B. A latency problem
- C. A cost problem
- D. A durability problem

**Q2.** In §7.1, what share of requests was rejected without a queue?

- A. 0%
- B. 20.0%
- C. 55.6%
- D. 100%

**Q3.** What happens when processing takes longer than the visibility timeout?

- A. The message is deleted automatically
- B. The consumer receives an error
- C. The message moves straight to the dead-letter queue
- D. The message is redelivered and processed a second time

**Q4.** How should the visibility timeout be chosen?

- A. Above p99 processing time, or extended from the worker
- B. Equal to the average processing time
- C. At the default of 30 seconds
- D. Below the function timeout, to force retries

**Q5.** What does "at-least-once delivery" require of you?

- A. Enabling FIFO queues
- B. Deleting messages before processing them
- C. Idempotent handlers
- D. Setting `maxReceiveCount` to 1

**Q6.** Which handler in §7.3 does *not* need an idempotency key?

- A. Indexing a chunk by a stable id
- B. Incrementing a counter
- C. Charging a customer
- D. Sending a notification email

**Q7.** What does a poison message do in a FIFO queue?

- A. It is skipped after the first failure
- B. It blocks every later message in its group
- C. It is duplicated across all groups
- D. It is delivered to the DLQ immediately

**Q8.** What is the best primary alarm for a queue's health?

- A. Number of messages sent per minute
- B. Consumer error rate
- C. Queue depth
- D. Age of the oldest message

**Q9.** Why can queue depth be near zero while nothing completes?

- A. Depth excludes messages that are in flight and failing repeatedly
- B. Depth is sampled once an hour
- C. Failed messages are counted in the DLQ instead
- D. Standard queues do not report depth accurately

**Q10.** Which service provides archive and replay of past events?

- A. SQS
- B. SNS
- C. SQS FIFO
- D. EventBridge

**Q11.** Why put an SQS queue in front of each consumer in a fan-out design?

- A. To reduce the cost of the fan-out service
- B. So a slow or broken consumer buffers its own backlog rather than losing messages
- C. To guarantee ordering across consumers
- D. To allow consumers to share a single processing pool

**Q12.** What is the risk of a single FIFO message group id?

- A. Deduplication stops working
- B. Messages are delivered out of order
- C. It serialises the entire system
- D. The DLQ cannot be used

**Q13.** *(Written, rubric-graded.)* In under 150 words: your document-ingestion consumer sometimes processes the same
file twice, creating duplicate chunks. Describe the causes you would check and the fix you would implement.

---

## 12. Revision notes

- **A queue trades availability for latency**: **55.6%** rejected without one; **0** rejected with one, at a **66.7 s**
  worst wait and a **40 s** drain.
- **Visibility timeout > p99**: a 95-second model call under a 30-second timeout duplicates **every time**; align it with
  the Lambda function timeout.
- **At-least-once is your problem**: **2.09%** duplicates, **3 of 6** handlers broken without an idempotency key.
- **DLQ with a small `maxReceiveCount`**: without one, up to **11,520** attempts at four-day retention. In FIFO, a poison
  message blocks its group.
- **Alarm on age of the oldest message**, not depth — depth can be zero while nothing completes.
- **SQS buffers, SNS fans out, EventBridge routes.** Default pattern: fan-out → a queue per consumer → consumer.

---

## 13. Completion checklist

- [ ] Asynchronous work is behind a queue, and users are told when something is queued.
- [ ] Visibility timeout is set from p99 and agrees with the consumer's own timeout.
- [ ] Every handler is idempotent on a content-derived key.
- [ ] Every queue has a DLQ, a small `maxReceiveCount`, an alarm and a redrive procedure.
- [ ] Alarms watch the age of the oldest message.
- [ ] Fan-out designs give each consumer its own queue.
- [ ] I scored at least 10/13 on the quiz.

---

## 14. References

- Amazon SQS Developer Guide — visibility timeout, at-least-once delivery, dead-letter queues and `maxReceiveCount`, FIFO
  queues and message groups `[STABLE — verify current defaults]`
- Amazon SNS — fan-out to queues, functions and endpoints `[STABLE]`
- Amazon EventBridge — content-based routing rules, schema registry, archive and replay `[STABLE]`
- M8-L12 (idempotency and duplicate prevention) and M8-L13 (retries, timeouts, cancellation) `[STABLE]`
- M11-L13 (Lambda consumers and timeouts) and M11-L14 (bounding downstream database load) `[STABLE]`

---

## 15. Next lesson

→ [M11-L16 — CloudWatch and CloudTrail](M11-L16-cloudwatch-cloudtrail.md) covers the signals every lesson so far has
told you to alarm on: what to record, what it costs, and the difference between a metric that tells you the system is
broken and one that tells you why.
