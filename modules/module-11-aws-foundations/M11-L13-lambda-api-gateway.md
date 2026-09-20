# M11-L13 — Lambda and API Gateway

| | |
|---|---|
| **Lesson ID** | M11-L13 |
| **Difficulty** | 2 (Intermediate) |
| **Estimated study time** | 2.25 hours |
| **Prerequisites** | [M11-L04](M11-L04-iam-policies-roles.md), [M11-L12](M11-L12-containers-ecr-ecs-fargate.md) |

---

## 1. Learning objectives

1. **Predict** what share of requests pays a cold start, from the invocation rate.
2. **Decide** when provisioned concurrency is right, and recognise when it means you wanted a container.
3. **Use reserved concurrency** for both guarantee and cap, and compute throttling under a spike.
4. **Check every timeout on the path**, because an AI request exceeds several defaults.
5. **Choose** between Lambda and a container by duty cycle, then by the limits.

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **Cold start** | The extra latency when a request runs in a new execution environment. |
| **Warm environment** | A reused environment; subsequent requests skip initialisation. |
| **Provisioned concurrency** | Pre-initialised environments kept warm, billed whether used or not. |
| **Reserved concurrency** | A guaranteed **and maximum** slice of the account's concurrency for one function. |
| **Account concurrency limit** | The total concurrent executions allowed, across functions (a soft quota). |
| **Integration timeout** | How long API Gateway waits for the backend before giving up. |
| **Response streaming** | Returning a response incrementally rather than in one payload. |
| **Duty cycle** | The fraction of time a workload is actually doing work. |

---

## 3. Plain-language explanation

### 3.1 Cold starts matter at low rates and vanish at high ones

§7.1: a function called every ~30 minutes pays the full **2.4 s on 100% of requests**, because nothing stays warm between
calls. At one call per minute it is **2.78%**; at one per second, **0.06%**.

The dangerous case is neither extreme: a function busy in the day and idle overnight has a fine p99 at 2pm and a terrible
one at 6am — when nobody is looking.

### 3.2 Provisioned concurrency is a server with a different name

§7.2 prices keeping environments warm. It removes cold starts up to the provisioned level and charges for them whether
used or not. If you need a lot of it, you have discovered your workload is a **service**, and a container (L12) is usually
cheaper and simpler.

### 3.3 Reserved concurrency guarantees and caps

§7.3: with 500 of 1,000 reserved, the assistant API's 200 gives it **80 rps** at 2.5-second requests, isolated from
everything else. A spike of **140 rps** needs **350** concurrent executions and is **throttled**, rejecting the equivalent
of 150.

Both jobs matter: the reservation protects this function from others, **and** protects others from this one (L06 §5.2).

### 3.4 An AI request exceeds several defaults

§7.4: a request totalling **46.9 seconds** — almost all of it streamed generation — exceeds **2 of 4** ceilings at their
defaults, including API Gateway's integration timeout and a typical Lambda default. The model is fine, the function is
fine, and the API layer cuts the connection.

### 3.5 Choose by duty cycle

§7.5: Lambda wins for the webhook (5k/day) and the rare admin job; a container wins for the assistant API (200k/day) and
the batch embedder. The crossover is where the function is effectively always running — which is also where cold starts,
concurrency limits and the 15-minute ceiling stop being theoretical.

---

## 4. Analogy

**A taxi versus a leased car with a driver.** For an occasional trip the taxi is obviously cheaper, but you wait for it to
arrive (cold start). Keeping a taxi idling outside costs you whether or not you go anywhere (provisioned concurrency) —
at which point you have leased a car with a driver and should admit it. Booking a fleet in advance guarantees you cars and
stops your department taking all of them (reserved concurrency). And no taxi will wait outside the restaurant for an hour
if its meter caps at thirty minutes.

### Where the analogy breaks

- **A taxi's wait is visible; a cold start appears only in the p99** of a metric nobody is watching at 6am (§5.2).
- **Taxis scale one at a time; Lambda scales to hundreds instantly** — which is a genuine advantage, and also how a bug
  becomes a bill in ninety seconds (§5.4, L06).

---

## 5. Detailed technical explanation

### 5.1 The execution model

A request arrives; if a warm environment is free it is reused, otherwise a new one is created: download the code, start
the runtime, run module-level initialisation, then the handler. Only the last part happens on subsequent requests.

Consequences worth designing around:

- **Module-level initialisation is amortised.** Create SDK clients, load configuration and open connection pools at module
  scope, not inside the handler.
- **There is no "between requests".** Background threads, in-process caches and buffered writes may not run again.
- **The environment may be reused**, so leaking state between invocations is a real bug class — and a real privacy bug if
  the state is another user's data.
- **Scaling is per request**, so a downstream database can be overwhelmed by a burst your architecture invited (L14, L15).

### 5.2 Cold starts

`[REAL, modelled — ILLUSTRATIVE durations]` §7.1 — 100% / 2.78% / 0.28% / 0.06% / 0.07% / 0.07%.

Reduce the cost rather than chase the count: import only what you need, avoid heavyweight frameworks in the handler path,
keep the package small (L12 §5.3 applies to zip and image packages alike), and consider a runtime with a fast start.

Then decide whether it matters: for an asynchronous ingestion function, 2.4 seconds is irrelevant; for a synchronous
user-facing call it is most of the latency budget.

### 5.3 Provisioned concurrency

`[REAL, computed — ILLUSTRATIVE rate]` §7.2.

Use it when: the workload is user-facing, the traffic pattern is known, and the warm floor is small and bounded. Avoid it
when: it would cover most of your traffic (buy a container instead), or the pattern is unpredictable (you will pay for
idle and still get cold starts at the edges).

Autoscale provisioned concurrency on a schedule where the pattern is daily — that is genuinely cheaper than a container
for a workload with a sharp business-hours shape.

### 5.4 Concurrency and throttling

`[REAL, computed]` §7.3.

```text
concurrent executions ≈ requests_per_second × average_duration_seconds
```

That formula is the whole model. A 2.5-second AI request at 140 rps needs 350 concurrent executions — a number that
surprises teams used to 100-millisecond functions.

Set **reserved concurrency on every function that matters**: it guarantees capacity and caps runaway spend and downstream
load. Leave headroom unreserved for everything else. Alarm on throttles (`Throttles` metric) — they are user-visible 429s,
not a tuning detail.

### 5.5 Timeouts on the path

`[REAL, compared]` §7.4 — 46.9 s against four ceilings.

Check every layer, in order: client, CDN, load balancer or API Gateway, function, and any downstream SDK timeout. The
smallest one wins, and the failure is usually reported by the wrong layer.

`[UNVERIFIED — quotas change; check current values for your API type]` As a rule of thumb: **Lambda's maximum is 15
minutes** (stable); **API Gateway's integration timeout defaults to about 29 seconds**, raiseable on REST APIs by quota
request; HTTP APIs have their own, lower ceiling; load balancer idle timeouts are configurable into minutes.

For streamed AI answers, prefer a path that supports **response streaming** — a Lambda function URL, or a load balancer in
front of a container (L12) — and set the client's timeout above your p99 (M13-L11).

### 5.6 API Gateway, and whether you need it

API Gateway gives you authorisers, request validation, throttling and usage plans, and WAF integration. A load balancer
gives you fewer features, higher limits and simpler streaming. Choose by what you actually need:

| Need | API Gateway | Load balancer |
|---|---|---|
| Per-client rate limits and API keys | Yes | No |
| Request validation and transformation | Yes | No |
| Long or streamed responses | Constrained by the integration timeout | Configurable into minutes |
| Cost at high volume | Per request | Per hour plus capacity units |

### 5.7 Permissions and packaging

The function's **execution role** is its identity for every AWS call — the same boundary argument as L12 §5.4 and the
same significance for an agent's reach (M9-L13). Grant it per function, never a shared "lambda-role".

Package as a zip for small functions, or as a **container image** for large dependencies — which also lets you reuse the
L12 build discipline. Keep secrets out of environment variables where you can and fetch them at initialisation (L17).

### 5.8 Assumptions and limitations

- Cold-start durations, environment recycling, all prices and the request profile are invented; the recycling model is a
  simplification of platform behaviour you do not control.
- Account concurrency defaults and API Gateway timeouts change — verify current quotas.
- Response streaming setup, SnapStart, and VPC-attached Lambda networking are out of scope.

---

## 6. Worked example — the assistant that worked in testing and timed out in production

**The situation.** A team built an assistant endpoint as a Lambda behind API Gateway. It passed testing with short
questions and was deployed.

**What happened.**

1. Real questions produced longer answers. Requests taking more than ~29 seconds returned a gateway timeout, while the
   function **kept running and kept billing** (§7.4).
2. The error surfaced as a 504 from the gateway, so the investigation started at the network layer. The function's own
   logs showed successful completions — at 40 seconds (§5.5, "reported by the wrong layer").
3. The team raised the **function** timeout, which changed nothing, because the ceiling was the gateway's.
4. Streaming was the obvious fix, and API Gateway's integration path did not support it in the form they needed (§5.6).
5. Concurrency was also wrong: at 2.5 s average and a 60 rps peak, the function needed 150 concurrent executions and had
   no reservation, so it was throttled whenever the ingestion function was busy (§7.3).

**After:** the endpoint moved to a container behind a load balancer with a 300-second idle timeout and response streaming;
the ingestion path stayed on Lambda with reserved concurrency.

| # | What went wrong | Fix |
|---|---|---|
| 1 | Only the function timeout was checked | Enumerate every ceiling on the path (§5.5) |
| 2 | Timeout at the wrong layer reported first | Correlate function duration with gateway 504s (L16) |
| 3 | Streaming not supported on that path | Function URL or load balancer + container |
| 4 | No reserved concurrency | Reserve for user-facing functions (§5.4) |
| 5 | Synchronous long request on a serverless path | Long work belongs behind a queue (L15) |

**The general rule.** **The shortest timeout on the path is your real timeout, and it is rarely the one you configured.**

---

## 7. Practical activity

**File:** [`labs/m11/l13_lambda_api_gateway.py`](../../labs/m11/l13_lambda_api_gateway.py)

**No AWS account, no network, no third-party dependencies.** Seeded, so the figures below reproduce exactly.

```bash
source .venv/bin/activate
python labs/m11/l13_lambda_api_gateway.py
```

### 7.2 Expected output

`[EXECUTED]` — 2026-09-17, Python 3.12.3 (pure standard library). Seeded with `random.Random(1113)`; run twice, output
identical.

```text

============================================================================
1. WHAT SHARE OF REQUESTS PAYS A COLD START?
============================================================================
  cold start 2400 ms (SDK + model client import), warm start 40 ms, request 2.5 s

   requests/second  concurrency   cold starts/hour  % of requests cold
            0.0005            1                1.8             100.00%
            0.0100            1                1.0               2.78%
            0.1000            1                1.0               0.28%
            1.0000            2                2.0               0.06%
           10.0000           25               25.0               0.07%
          100.0000          250              250.0               0.07%

  The shape is what matters. A function called once every 30 minutes pays the
  full 2.4 s on EVERY request, because nothing stays warm between calls. From
  about one call per minute the cost amortises away entirely. The dangerous
  case is a function busy in the day and idle at night: your p99 is fine at
  2pm and terrible at 6am, which is exactly when nobody is looking.

============================================================================
2. WHAT DOES PROVISIONED CONCURRENCY BUY?
============================================================================
  provisioned concurrency   0 -> $       0/month   cold starts: every request when idle
  provisioned concurrency   5 -> $      82/month   cold starts: only above 5 concurrent
  provisioned concurrency  20 -> $     329/month   cold starts: only above 20 concurrent
  provisioned concurrency  50 -> $     821/month   cold starts: only above 50 concurrent

  [ILLUSTRATIVE rate.] Provisioned concurrency keeps environments warm and
  charges for them whether or not they are used -- which is a server, billed
  by another name. If you need a lot of it, you have discovered that your
  workload is a service, and a container (M11-L12) is usually cheaper and
  simpler. Provisioned concurrency is for a known, bounded warm floor.

============================================================================
3. CONCURRENCY LIMITS AND THROTTLING
============================================================================
  account concurrency limit: 1000 [default, soft]

  function                            reserved  duration   max rps   note
  assistant API (reserved 200)             200      2.5s        80   isolated from the others
  ingestion worker (reserved 300)          300      8.0s        38   isolated from the others
  webhook handler (unreserved)               -      0.3s      1667   shares the remaining 500

  reserved in total: 500; left for everything unreserved: 500
  a spike of 140 rps on the assistant API needs 350 concurrent executions,
  against a reservation of 200 -> THROTTLED, 150 executions' worth rejected (429)

  Reserved concurrency does two jobs: it GUARANTEES a function its share, and
  it CAPS that function so a runaway cannot starve everything else (M11-L06).
  Both matter. An unreserved function competing for the remainder is the one
  that gets throttled first during someone else's incident.

============================================================================
4. TIMEOUTS: AN AI REQUEST AGAINST EACH CEILING
============================================================================
  phase                               seconds
  retrieval                               0.4
  rerank                                  0.3
  model generation (streamed)            46.0
  post-processing and logging             0.2
  TOTAL                                  46.9

  ceiling                                         seconds   fits?   note
  API Gateway integration timeout (default)            29      NO   raiseable on REST APIs by quota request
  Load balancer idle timeout (typical default)         60     yes   configurable, up to minutes
  Lambda function timeout (maximum)                   900     yes   15 minutes, hard
  Lambda function timeout (typical default)             3      NO   set it deliberately

  a 47-second streamed answer exceeds two of the four ceilings at their
  defaults. This is the single most common serverless surprise in AI work:
  the model is fine, the function is fine, and the API layer cuts the
  connection at its default. Check every ceiling on the path, and prefer
  streaming-capable paths (function URLs, ALB) for long answers (M5-L09).
  [Quotas change -- verify the current numbers for your API type.]

============================================================================
5. LAMBDA OR A CONTAINER?
============================================================================
  workload                                    Lambda $/mo  Fargate $/mo   cheaper
  webhook: 5k/day, 200 ms, 0.5 GB                       0             9   Lambda
  assistant API: 200k/day, 2.5 s, 1.5 GB              376           270   Fargate
  batch embed: 2M/day, 0.8 s, 2 GB                  1,612         1,117   Fargate
  rare admin job: 30/day, 60 s, 1 GB                    1            18   Lambda

  [ILLUSTRATIVE rates; the crossover point is what matters, not the numbers.]
  Lambda wins on spiky, low-duty-cycle and rare work, where a container would
  idle. A container wins once the function is effectively always running --
  and that is also the point where cold starts, concurrency limits and the
  15-minute ceiling stop being theoretical. Choose by duty cycle first, then
  by the timeout table in section 4.

============================================================================
6. WHAT THIS LAB IS AND IS NOT
============================================================================
  REAL: every share, cost, throttling figure and comparison above is computed
  from the values in this script.

  ILLUSTRATIVE: cold-start durations, idle-environment behaviour, all prices,
  and the request profile are invented. The cold-start model is a
  simplification: real recycling depends on traffic shape and platform
  behaviour you do not control.

  VERIFY BEFORE RELYING ON: Lambda's 15-minute maximum is stable, but account
  concurrency defaults and API Gateway integration timeouts change -- check
  the current quotas for your account and API type.

  NOT SHOWN: Lambda response streaming setup, SnapStart, VPC-attached Lambda
  networking, and API Gateway authorisers (M12-L11).

Done.
```

### 7.3 Reading the result

**Section 1's first and last rows** are the whole cold-start argument: 100% versus 0.07%.

**Section 3's spike line** shows how quickly a 2.5-second request exhausts a concurrency reservation.

**Section 4** is the table to copy into your own design review, with your own numbers.

**Section 5's middle two rows** are where teams get this wrong: the always-busy function that should have been a
container.

---

## 8. Common mistakes and troubleshooting

1. **Creating SDK clients inside the handler.** §5.1 — initialise at module scope.
2. **Assuming cold starts are always negligible.** §7.1 — 100% at low rates.
3. **Provisioned concurrency covering most traffic.** §5.3 — that is a container.
4. **No reserved concurrency on user-facing functions.** §5.4.
5. **Forgetting `concurrency ≈ rps × duration`.** §5.4 — AI durations make the number large.
6. **Checking only the function timeout.** §5.5 — the gateway's is usually smaller.
7. **Synchronous long requests through API Gateway.** §6 — stream, or use a queue (L15).
8. **A shared execution role across functions.** §5.7 — per function, least privilege.
9. **State left in a reused environment.** A correctness and privacy bug.

| Symptom | Likely cause | Fix |
|---|---|---|
| 504 from the gateway, success in function logs | Integration timeout below function duration | Stream, raise the quota, or change the path |
| Occasional multi-second latency spikes | Cold starts at low rates | Provisioned concurrency, or a container |
| 429s during someone else's incident | No reserved concurrency | Reserve per function (§5.4) |
| Downstream database overwhelmed | Lambda scaled faster than the database can take | Reserved concurrency; a queue (L15) |
| One user's data appears in another's response | State reused across invocations | Never cache per-request data at module scope |

---

## 9. Security, privacy, reliability, cost

- **Security.** The execution role is the function's whole capability set; per-function least privilege (L04, M9-L13).
- **Privacy.** Reused environments make module-scope caches a cross-user leak; keep per-request data in the handler.
- **Reliability.** Reserved concurrency and throttle alarms are what stop one function's incident becoming everyone's.
- **Cost.** Lambda's per-millisecond billing makes a runaway loop expensive quickly; concurrency caps are a cost control
  as much as a capacity one (L06, M8-L15).

---

## 10. Exercises

### Exercise 1 — Beginner (~20 min)

1. What share of requests pays a cold start at one invocation per 30 minutes? At 100 rps?
2. Compute the concurrency needed for 50 rps with 3-second requests.
3. Which two ceilings does the 46.9-second request exceed?
4. Which workloads in §7.5 are cheaper on Lambda?
5. What two jobs does reserved concurrency do?

### Exercise 2 — Intermediate (~40 min)

1. Run the lab. Change the request duration to 0.2 s and re-read section 3.
2. Add a fifth workload shape to §7.5 matching something you run.
3. Add your own client and CDN timeouts to §7.4.
4. Compute the provisioned concurrency you would need for a 9am-to-6pm traffic shape.
5. Write the reserved-concurrency plan for three functions sharing one account limit.

### Exercise 3 — Challenge (~60 min)

1. Enumerate every timeout on one real request path, end to end, with its current value.
2. Measure a real function's cold-start and warm latency, and compute the p99 impact at your traffic rate.
3. Design the queue-based alternative for a long synchronous request (L15).
4. Write the per-function execution roles for a three-function application (L04).
5. Add throttle and duration alarms with thresholds derived from your concurrency maths (L16).

---

## 11. Quiz

*(Answers: [`answer-keys/module-11-answers.md`](../../answer-keys/module-11-answers.md#m11-l13).)*

**Q1.** Where should SDK clients be created in a Lambda function?

- A. At module scope, so initialisation is amortised across invocations
- B. Inside the handler, so each request gets a fresh client
- C. In a background thread started at first invocation
- D. In an initialisation hook that runs before every request

**Q2.** In §7.1, what share of requests paid a cold start at one invocation every 30 minutes?

- A. 2.78%
- B. 0.06%
- C. 100%
- D. 0.28%

**Q3.** When is provisioned concurrency the wrong answer?

- A. When traffic has a predictable daily shape
- B. When the warm floor needed covers most of your traffic
- C. When the function is user-facing
- D. When cold starts exceed one second

**Q4.** What does reserved concurrency do?

- A. Guarantees a function's share and caps it
- B. Keeps environments warm to remove cold starts
- C. Raises the account's total concurrency limit
- D. Reserves capacity in a specific Availability Zone

**Q5.** How many concurrent executions does 140 rps with 2.5-second requests need?

- A. 56
- B. 140
- C. 200
- D. 350

**Q6.** In §7.4, which ceilings did the 46.9-second request exceed?

- A. Only the Lambda maximum
- B. Only the load balancer idle timeout
- C. The API Gateway integration timeout and a typical Lambda default
- D. All four ceilings

**Q7.** What is Lambda's maximum function timeout?

- A. 29 seconds
- B. 5 minutes
- C. 15 minutes
- D. 60 minutes

**Q8.** A gateway returns 504 while the function logs success. What is happening?

- A. The function is retrying internally
- B. The integration timeout is shorter than the function's duration
- C. The load balancer is draining the target
- D. The function's execution role lacks logging permission

**Q9.** What should be the first criterion when choosing Lambda or a container?

- A. Whether the language runtime is supported
- B. Whether the team prefers infrastructure as code
- C. Whether the workload needs a VPC
- D. The workload's duty cycle

**Q10.** Why can Lambda's scaling overwhelm a downstream database?

- A. Lambda opens a new connection per module load only
- B. It scales per request, far faster than the database can accept connections
- C. Databases reject requests from ephemeral addresses
- D. Connection pooling is unavailable in serverless runtimes

**Q11.** Why is caching per-request data at module scope a bug?

- A. Environments are reused, so one user's data can reach another
- B. It increases the cold-start duration
- C. Module scope is read-only after initialisation
- D. Module scope is not persisted between requests at all

**Q12.** What is the practical approach to long, streamed AI responses?

- A. Increase the function timeout and retry on failure
- B. Split the answer into multiple short synchronous requests
- C. Return a redirect and let the client poll the model provider
- D. Use a streaming-capable path, such as a function URL or load balancer plus container

**Q13.** *(Written, rubric-graded.)* In under 150 words: a colleague proposes running the whole assistant API on Lambda
behind API Gateway, at about 200,000 requests a day with 2.5-second responses. Give your assessment.

---

## 12. Revision notes

- **Cold starts**: **100%** of requests at one call per 30 minutes; **2.78%** at one per minute; **~0.06%** above one per
  second. The trap is a daily-cycle function.
- **Provisioned concurrency** removes cold starts and bills for idle — a lot of it means you wanted a container.
- **`concurrency ≈ rps × duration`**: 140 rps × 2.5 s = **350**, against a 200 reservation → **throttled**.
- **Reserved concurrency guarantees *and* caps**; alarm on throttles.
- **Check every ceiling**: a 46.9 s request exceeded **2 of 4** defaults; Lambda's maximum is **15 minutes**, API
  Gateway's integration timeout defaults to about **29 s**.
- **Choose by duty cycle**: Lambda for spiky and rare work; containers once the function is effectively always running.

---

## 13. Completion checklist

- [ ] Clients and configuration are initialised at module scope; no per-request state leaks there.
- [ ] I know my cold-start share at my actual invocation rate.
- [ ] User-facing functions have reserved concurrency, and throttles are alarmed.
- [ ] Every timeout on the request path is enumerated and deliberately set.
- [ ] Long or streamed responses use a streaming-capable path.
- [ ] Each function has its own least-privilege execution role.
- [ ] I scored at least 10/13 on the quiz.

---

## 14. References

- AWS Lambda Developer Guide — execution environments and reuse, cold starts, reserved and provisioned concurrency,
  function timeout (15-minute maximum), response streaming `[STABLE for the 15-minute maximum; verify quotas]`
- Amazon API Gateway — integration timeouts and quotas; these change, and differ between REST and HTTP APIs
  `[UNVERIFIED — check current quotas]`
- M11-L12 (containers — the usual alternative) and M11-L15 (queues for long work) `[STABLE]`
- M5-L09 (streaming) and M13-L11 (latency percentiles — where your timeouts come from) `[STABLE]`
- M8-L15 (runaway prevention) and M11-L06 (concurrency caps as cost control) `[STABLE]`

---

## 15. Next lesson

→ [M11-L14 — RDS and DynamoDB](M11-L14-rds-dynamodb.md) covers the state behind all of this: when a relational database
is right, when a key-value store is, and the connection-limit problem that serverless compute creates for both.
