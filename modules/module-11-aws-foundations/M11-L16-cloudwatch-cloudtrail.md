# M11-L16 — CloudWatch and CloudTrail

| | |
|---|---|
| **Lesson ID** | M11-L16 |
| **Difficulty** | 2 (Intermediate) |
| **Estimated study time** | 2.0 hours |
| **Prerequisites** | [M11-L13](M11-L13-lambda-api-gateway.md), [M10-L13](../module-10-governance-security/M10-L13-versioning-auditability.md) |

---

## 1. Learning objectives

1. **Assign** each incident question to metrics, logs or traces, and spend accordingly.
2. **Cut log cost** by sampling successes and keeping every error, and emit numbers as metrics.
3. **Alarm on a percentile**, because averages hide user-visible failures.
4. **Distinguish** CloudTrail management events from data events, and enable data events selectively.
5. **Tune alarms** with multiple datapoints and composite conditions, from a measured flap rate.

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **Metric** | A numeric time series, aggregated, cheap, and the only thing an alarm fires on. |
| **Log** | A record of something that happened, searchable, expensive per gigabyte. |
| **Trace** | A single request's path across services, with timing per span. |
| **Embedded metric format** | Emitting structured logs from which CloudWatch extracts metrics automatically. |
| **Management event** | A CloudTrail record of a control-plane action (who changed what); on by default. |
| **Data event** | A CloudTrail record of a data-plane action (who read which object); opt-in and charged. |
| **Datapoints to alarm** | The "M out of N" rule deciding when an alarm changes state. |
| **Composite alarm** | An alarm whose condition combines other alarms. |
| **Flap rate** | How often a healthy system momentarily breaches a threshold. |

---

## 3. Plain-language explanation

### 3.1 Three signals, three jobs

§7.1 maps nine incident questions. Metrics answer **3 of 9** — including the only ones you can alarm on. Logs answer
**4 of 9**; traces **4 of 9**. Metrics tell you *that* something is wrong, cheaply and quickly; logs and traces tell you
*why*, expensively and afterwards.

### 3.2 Sampling successes is the biggest cost lever you have

§7.2: 300 rps at 14 KB of logs per request is **10,382 GB/month** — **$6,125/month** at 90-day retention. Keeping all
errors and **1% of successes** at 14-day retention: **$320**. Structured metrics plus errors only: **$107 — 1.7% of the
original**, saving **$6,019/month**.

You keep every failure you would ever investigate and drop the successful requests nobody reads.

### 3.3 The average hides real failures

§7.3: 3% of requests take about nine seconds. Against a 1,500 ms threshold, the **Average (675 ms), p50, p90 and p95 are
all silent**. Only the **p99 (9,488 ms)** fires.

Three per cent of your users waiting nine seconds is a serious, dependency-shaped failure, and a dashboard of averages
shows green.

### 3.4 CloudTrail records configuration by default, data access only if you ask

§7.4: **4 of 8** example events are management events, recorded by default — who changed a bucket policy, who assumed a
role, who stopped CloudTrail. The other **4 are data events**: who *read* an object, who invoked a function. Those are
off by default and charged per event — **$120/month** for 120 million object reads in the lab.

### 3.5 A noisy alarm is a muted alarm

§7.5: at a 0.4% flap rate, a "1 out of 1" alarm fires **2,102 times a year** — about **58 false alarms for every real
incident**. "3 out of 3" fires **0.01 times a year** but a single healthy minute resets it mid-incident. "3 out of 5"
fires **0.07 times a year** *and* keeps firing through a flapping failure.

---

## 4. Analogy

**A hospital's monitoring.** The bedside monitor (metrics) shows heart rate continuously and sets off an alarm — that is
its job, and it must not cry wolf, because a nurse who mutes it has disabled it. The notes (logs) record what was
administered and when, and you read them only when something has gone wrong. The patient's journey through departments
(traces) explains where the six-hour wait actually happened. And the average temperature on the ward tells you nothing
about the patient with a fever.

### Where the analogy breaks

- **A monitor's alarm threshold is clinically established; yours is invented** and must be tuned against your own measured
  flap rate (§5.5).
- **Notes are written for humans; logs are written by machines at gigabyte scale**, which is why sampling and retention
  are design decisions with a price (§5.2).

---

## 5. Detailed technical explanation

### 5.1 What to record, and where

`[REAL, mapped]` §7.1.

| Signal | Use for | Cost shape |
|---|---|---|
| **Metrics** | Alarms, dashboards, capacity, SLOs | Per metric and per datapoint; cheap |
| **Logs** | Investigating a specific request or change | Per GB ingested and stored; expensive |
| **Traces** | Finding which component is slow across services | Per trace, usually sampled |

For an AI system, the metrics worth emitting from day one:

```text
requests, errors, and latency (p50/p95/p99) -- per route AND per slice (M10-L08)
tokens in / out per request, and per hour       (cost and runaway detection -- M11-L06)
retrieval hit rate, chunks returned, reranker latency
model errors by type: throttling, timeout, refusal, schema-validation failure
abstention rate, citation-validity rate         (quality proxies -- M10-L12)
queue depth and age of oldest message           (M11-L15)
```

Emit them with the **embedded metric format** — structured log lines from which CloudWatch extracts metrics — so you get
both the metric and the searchable record from one emission.

### 5.2 Log volume and cost

`[REAL, computed — ILLUSTRATIVE rates]` §7.2 — $6,125 → $107 per month.

Policy that works:

- **All errors, always**, with full context.
- **A sample of successes** (1–5%), with a consistent sampling key so a sampled request's whole trace is present.
- **Retention by class**: request metadata longer, full text shorter (M10-L13 §5.6).
- **No debug logging in production** by default; make it switchable per request or per tenant.
- **Hash prompts and outputs** in application logs; keep the text in one governed store (M10-L13 §5.4).

### 5.3 Alarming on the right statistic

`[REAL, computed]` §7.3.

Alarm on **p95 or p99**, not the average. Also alarm on:

| Signal | Why |
|---|---|
| Error **rate**, not count | Count scales with traffic and hides a rate change |
| Age of oldest queue message | L15 §5.6 |
| Throttles (Lambda, DynamoDB, provider) | User-visible 429s |
| Tokens per hour | Runaway detection faster than billing (L06 §5.1) |
| Per-slice latency and quality | The aggregate hides the slice (M10-L08, M10-L12) |

### 5.4 CloudTrail

`[REAL, classified]` §7.4 — 4 management, 4 data.

| | Management events | Data events |
|---|---|---|
| Records | Control-plane actions: create, modify, delete, assume role | Data-plane actions: object reads/writes, function invocations, item reads |
| Default | On | **Off** |
| Cost | First copy in the account is generally free | Charged per event |
| Answers | "Who changed the configuration?" | "Who read this object?" |

Configuration that holds up in an investigation:

- An **organisation trail**, all regions, delivering to a **separate log-archive account** (L03 §5.4).
- The destination bucket with **Object Lock** and a deny-delete policy (L10 §5.5).
- **Data events enabled selectively**: on buckets holding sensitive data, not on the image registry.
- **Log file validation** enabled, so tampering is detectable.

CloudTrail is the evidence layer for M10-L13's audit questions and for most security investigations. Its own "logging was
stopped" event is one to alarm on.

### 5.5 Alarm design

`[REAL, computed]` §7.5 — 2,102 / 4.20 / 0.01 / 0.07 false alarms per year.

```text
false alarms per year ≈ (periods per year / N) × P(at least M breaches in N periods)
```

Practical rules:

1. **Measure your flap rate first** on a quiet period (M10-L14 §5.1).
2. Prefer **M out of N with N > M** — nearly as quiet as M out of M, and it survives a flapping failure.
3. **Composite alarms** for paging: "latency high **AND** error rate up" stops one noisy metric waking anyone.
4. **Treat missing data explicitly** — a metric that stops reporting is usually worse news than a breach.
5. Every paging alarm needs a **runbook link** and an owner (M10-L14 §5.7).

### 5.6 Dashboards

Two dashboards, not twenty: one **service health** view (the four or five numbers that decide whether it is working) and
one **investigation** view (per-dependency latency and errors, queue depths, throttles). Put deployment markers on both
(M10-L14 §6).

### 5.7 Assumptions and limitations

- All prices, traffic volumes, latency distributions and flap probabilities are invented.
- CloudTrail's free-tier behaviour and CloudWatch pricing change; verify current terms.
- Logs Insights, X-Ray/OpenTelemetry setup, metric filters and anomaly detection are out of scope (M12-L13, M13-L12).

---

## 6. Worked example — the green dashboard and the angry customer

**The situation.** An assistant's dashboard showed average latency at about 700 ms and an error rate near zero. A large
customer escalated: their team found the assistant "unusably slow, several times a day".

**What was happening.**

1. A downstream document service failed intermittently, and the retry path took about nine seconds. It affected roughly
   **3%** of requests (§7.3).
2. The dashboard showed **Average**. At 675 ms it never approached the 1,500 ms alarm threshold (§7.3).
3. The affected requests clustered in **one tenant's document type**, so the customer's experience was far worse than 3%
   — a slice problem invisible in any aggregate (M10-L08).
4. Logs were sampled at 1% **without a consistent key**, so the slow requests' traces were incomplete (§5.2).
5. There was no trace instrumentation, so nobody could say *which* dependency was slow without adding logging and waiting
   a day (§7.1).

**After:** p99 alarms per route and per tenant slice, consistent trace-based sampling, and one trace per slow request
retained in full.

| # | What went wrong | Fix |
|---|---|---|
| 1 | Alarmed on the average | p95/p99 alarms (§5.3) |
| 2 | No per-slice metrics | Emit latency and errors per slice (M10-L08) |
| 3 | Sampling without a consistent key | Sample by trace id, keep whole traces |
| 4 | No tracing | Instrument dependencies; keep slow traces |
| 5 | Error *count*, not rate | Alarm on rate (§5.3) |

**The general rule.** **If your alarm can be satisfied by a healthy average while users are suffering, it is not an
alarm.**

---

## 7. Practical activity

**File:** [`labs/m11/l16_cloudwatch_cloudtrail.py`](../../labs/m11/l16_cloudwatch_cloudtrail.py)

**No AWS account, no network, no third-party dependencies.** Seeded, so the figures below reproduce exactly.

```bash
source .venv/bin/activate
python labs/m11/l16_cloudwatch_cloudtrail.py
```

### 7.2 Expected output

`[EXECUTED]` — 2026-09-17, Python 3.12.3 (pure standard library). Seeded with `random.Random(1116)`; run twice, output
identical.

```text

============================================================================
1. WHICH SIGNAL ANSWERS WHICH QUESTION?
============================================================================
  question                                          metrics   logs   traces
  is the system broken right now?                       yes      -        -
  how broken, and since when?                           yes      -        -
  which user was affected?                                -    yes      yes
  what exactly did we send the model?                     -    yes        -
  which of the eight services was slow?                   -      -      yes
  did the retrieval step or the model take 4 s?           -      -      yes
  who changed the bucket policy, and when?                -    yes        -
  is the French slice regressing?                       yes      -        -
  why did THIS request fail?                              -    yes      yes

  metrics  answers 3/9
  logs     answers 4/9
  traces   answers 4/9

  Metrics tell you THAT something is wrong, cheaply and fast, and they are
  what an alarm can fire on. Logs and traces tell you WHY, expensively and
  after the fact. You need all three, and you should pay very different
  amounts for each (M10-L13).

============================================================================
2. WHAT DOES LOGGING COST, AND WHAT DOES SAMPLING SAVE?
============================================================================
  300 requests/s, 14 KB of logs each -> 10,382 GB/month

  policy                                          GB/mo   ingest $   store $   total $
  everything, 90-day retention                   10,382      5,191       934     6,125
  everything, 14-day retention                   10,382      5,191       146     5,337
  errors + 5% of successes, 14 days               1,038        519        15       534
  errors + 1% of successes, 14 days                 623        311         9       320
  structured metrics + errors only                  208        104         3       107

  the strictest policy costs 1.7% of the loosest ($6,019/month saved).
  Sampling successes and keeping ALL errors is the highest-value change most
  teams can make: you keep every failure you will investigate and drop the
  99% of successful requests nobody ever reads. Emit the numbers you need as
  METRICS (cheap, aggregated, alarmable) rather than parsing them out of logs
  later (embedded metric format).

============================================================================
3. THE STATISTIC DECIDES WHETHER YOU SEE IT
============================================================================
  3% of requests hit a broken dependency and take about 9 s

  statistic                    value   alarm at 1500 ms?
  Average                     675 ms   silent
  p50                         424 ms   silent
  p90                         552 ms   silent
  p95                         602 ms   silent
  p99                        9488 ms   FIRES
  Maximum                   12051 ms   FIRES

  Read that again: 3% of users are waiting NINE SECONDS, and the Average,
  p50, p90 and p95 are all SILENT. Only the p99 fires. Averaging is how a
  real, user-visible, dependency-shaped failure hides inside a green
  dashboard. Alarm on a high percentile, and keep the average away from any
  dashboard people make decisions from (M13-L11, M10-L08).

============================================================================
4. CLOUDTRAIL: MANAGEMENT EVENTS AND DATA EVENTS
============================================================================
  event                                       type            recorded by default?
  someone changed a bucket policy             management                       yes
  someone assumed a role                      management                       yes
  an instance was launched                    management                       yes
  CloudTrail logging was stopped              management                       yes
  an object was READ from a bucket            data                    NO -- opt in
  an object was WRITTEN to a bucket           data                    NO -- opt in
  a Lambda function was INVOKED               data                    NO -- opt in
  a DynamoDB item was read                    data                    NO -- opt in

  management events: 4/8 (recorded by default)
  data events:       4/8 (opt-in, charged per event)

  at 120,000,000 object reads/month, S3 data events would cost $120/month
  Management events answer 'who changed the configuration' -- the question in
  most security investigations -- and are on by default. Data events answer
  'who read this object', which is what you need for a data-access
  investigation, and are off and expensive. Enable them SELECTIVELY: on the
  buckets holding sensitive data, not on the one holding container images
  (M10-L13, M11-L10).

============================================================================
5. ALARM NOISE: FOUR CONFIGURATIONS
============================================================================
  a healthy system breaches the threshold in 0.4% of 1-minute periods

  configuration                       false alarms/year   detect delay   survives a good blip?           
  1 datapoint out of 1                         2,102.40            1 min   no -- one good minute resets it 
  2 out of 2                                       4.20            2 min   no -- one good minute resets it 
  3 out of 3                                       0.01            3 min   no -- one good minute resets it 
  3 out of 5 (tolerates a blip)                    0.07            5 min   yes                             

  '1 out of 1' produces about 175 false alarms a month against 3 real incidents:
  58 false alarms for every real one. That alarm is muted within a
  fortnight, and then the real incident goes undetected (M10-L14).
  Note the last column. '3 out of 3' is quiet but a single healthy minute in
  the middle of a real incident resets the count; '3 out of 5' is almost as
  quiet and keeps firing through a flapping failure. Combine signals with a
  COMPOSITE alarm -- 'latency high AND error rate up' -- so one noisy metric
  cannot page anyone on its own.

============================================================================
6. WHAT THIS LAB IS AND IS NOT
============================================================================
  REAL: every coverage count, cost figure, statistic, event classification
  and false-alarm rate above is computed from the values in this script.

  DOCUMENTED BEHAVIOUR: CloudTrail records management events by default and
  requires data events to be enabled explicitly and charged; CloudWatch alarms
  evaluate N datapoints out of M periods.

  ILLUSTRATIVE: all prices, traffic volumes, latency distributions and flap
  probabilities are invented. Measure your own flap rate before choosing an
  alarm configuration.

  NOT SHOWN: Logs Insights queries, X-Ray/OpenTelemetry setup, metric filters,
  anomaly detection, and cross-account log aggregation (M12-L13, M13-L12).

Done.
```

### 7.3 Reading the result

**Section 2's last row** is a **$6,019/month** saving from a change that loses nothing you would investigate.

**Section 3 is the most important table in this lesson**: Average, p50, p90 and p95 all silent while 3% of users wait
nine seconds.

**Section 4's split** tells you which questions your current trail can answer.

**Section 5's last column** is why "3 out of 5" beats "3 out of 3".

---

## 8. Common mistakes and troubleshooting

1. **Alarming on averages.** §7.3.
2. **Alarming on error count rather than rate.** §5.3.
3. **Logging everything at full verbosity.** §7.2 — 57× more expensive.
4. **Sampling without a consistent key.** §6 — incomplete traces for the requests that matter.
5. **Full prompts and outputs in application logs.** Personal data everywhere (M10-L13).
6. **Assuming CloudTrail records object reads.** §7.4 — data events are opt-in.
7. **Data events on everything.** §7.4 — enable selectively.
8. **"1 out of 1" alarms.** §7.5 — 58 false alarms per real incident.
9. **No alarm on missing data.** A silent metric looks like a healthy one.
10. **A dashboard nobody uses in an incident.** §5.6 — two dashboards, with deployment markers.

| Symptom | Likely cause | Fix |
|---|---|---|
| Users report slowness, dashboards green | Alarming on averages | p95/p99, and per slice |
| Alarms are muted | Flap rate never measured | M-out-of-N, composite alarms |
| Log bill exceeds compute bill | No sampling, long retention | Errors + sampled successes; retention by class |
| Cannot answer "who read this file" | Data events not enabled | Enable on sensitive buckets |
| Cannot reconstruct an incident timeline | Logs sampled inconsistently, short retention | Consistent sampling; retention from complaint lag (M10-L13) |

---

## 9. Security, privacy, reliability, cost

- **Security.** CloudTrail is the evidence layer; protect the trail (separate account, Object Lock) and alarm on
  "logging stopped" (M10-L13, L03).
- **Privacy.** Logs are a data store with a retention rule; hash prompts and outputs, and make deletion reach them
  (M10-L06).
- **Reliability.** Alarms are the detection half of M10-L14; their measured false-alarm rate is part of the design.
- **Cost.** Observability is routinely 8–15% of a bill (L06 §7.5); sampling and retention are the levers.

---

## 10. Exercises

### Exercise 1 — Beginner (~20 min)

1. Which questions in §7.1 can only logs or traces answer?
2. What did the strictest logging policy cost as a share of the loosest?
3. Which statistics stayed silent while 3% of users waited nine seconds?
4. Which four events in §7.4 are not recorded by default?
5. How many false alarms per year does "1 out of 1" produce?

### Exercise 2 — Intermediate (~40 min)

1. Run the lab. Change the flap rate to 2% and re-choose an alarm configuration.
2. Add your own log volume and retention to §7.2.
3. Change the broken-dependency share to 1% and see which statistics still fire.
4. Add two events from your system to §7.4 and classify them.
5. Write the metric list your service should emit, using §5.1 as a starting point.

### Exercise 3 — Challenge (~60 min)

1. Measure your real flap rate over a quiet week and set alarm configurations from it.
2. Implement embedded-metric-format emission for one service and build a health dashboard.
3. Add per-slice latency and error metrics for your L08 slice list.
4. Design the CloudTrail configuration from §5.4, including the log-archive account.
5. Write composite alarms for your top three paging conditions, each with a runbook link.

---

## 11. Quiz

*(Answers: [`answer-keys/module-11-answers.md`](../../answer-keys/module-11-answers.md#m11-l16).)*

**Q1.** What can an alarm fire on?

- A. Log lines matching a pattern, directly
- B. Metrics
- C. Traces exceeding a duration
- D. CloudTrail events, directly

**Q2.** In §7.2, what did "structured metrics + errors only" cost as a share of full logging at 90-day retention?

- A. 1.7%
- B. 10%
- C. 25%
- D. 50%

**Q3.** What is the highest-value logging change for most teams?

- A. Increasing retention so investigations reach further back
- B. Compressing log lines before ingestion
- C. Keeping all errors and sampling successes
- D. Moving logs to object storage immediately

**Q4.** In §7.3, which statistic fired against the 1,500 ms threshold?

- A. The Average
- B. The p95
- C. The p50
- D. The p99

**Q5.** Why is alarming on the average dangerous?

- A. Averages are computed over longer periods than percentiles
- B. A real failure affecting a minority of users leaves it silent
- C. Averages are unavailable for custom metrics
- D. Averages cannot be combined in composite alarms

**Q6.** Which CloudTrail events are recorded by default?

- A. Data events
- B. Both, in the current default configuration
- C. Management events
- D. Neither; a trail must be created first

**Q7.** What question do data events answer?

- A. Who changed the bucket policy
- B. Who assumed a role
- C. Which instances were launched
- D. Who read a specific object

**Q8.** Why enable data events selectively?

- A. They are charged per event and the volume is very large
- B. They are only available in certain regions
- C. They cannot be delivered to a separate account
- D. They conflict with management-event logging

**Q9.** In §7.5, how many false alarms per year did "1 datapoint out of 1" produce?

- A. 4.20
- B. 0.07
- C. 2,102.40
- D. 0.01

**Q10.** Why prefer "3 out of 5" to "3 out of 3"?

- A. It keeps firing through a flapping failure that a single good datapoint would reset
- B. It produces fewer false alarms
- C. It detects failures faster
- D. It requires fewer metric datapoints to be published

**Q11.** What should a paging alarm always include?

- A. A composite condition across at least three metrics
- B. A one-minute evaluation period
- C. An anomaly-detection band
- D. A runbook link and a named owner

**Q12.** Why should a metric that stops reporting be alarmed on?

- A. Missing data inflates the average
- B. Absent data usually means something worse than a breach
- C. CloudWatch charges for gaps in a metric stream
- D. Alarms cannot evaluate without continuous data

**Q13.** *(Written, rubric-graded.)* In under 150 words: your dashboards are green and a customer says the assistant is
unusably slow several times a day. Describe what you would check and what you would change about your monitoring.

---

## 12. Revision notes

- **Metrics say *that*, logs and traces say *why*.** Only metrics can be alarmed on.
- **Logging cost**: $6,125/month → **$107** (1.7%) by keeping all errors, sampling successes, and shortening retention.
- **Alarm on percentiles**: with 3% of requests at ~9 s, Average (675 ms), p50, p90 and **p95 were all silent**; only
  **p99 (9,488 ms)** fired.
- **CloudTrail**: management events on by default (who changed what); **data events opt-in and charged** (who read what).
  Organisation trail → separate log-archive account, Object Lock, log-file validation.
- **Alarm noise**: "1 out of 1" → **2,102 false alarms/year** (**58 per real incident**); **"3 out of 5"** → 0.07/year and
  survives a blip.
- **Two dashboards**, deployment markers, runbook links on every paging alarm.

---

## 13. Completion checklist

- [ ] My service emits metrics for latency percentiles, error rate, tokens and quality proxies, per slice.
- [ ] Logging keeps all errors and a consistently-sampled fraction of successes, with retention by class.
- [ ] No alarm uses an average; error alarms use rates.
- [ ] An organisation CloudTrail delivers to a separate, protected log-archive account.
- [ ] Data events are enabled on sensitive resources only.
- [ ] Alarm configurations come from a measured flap rate, with composite conditions for paging.
- [ ] I scored at least 10/13 on the quiz.

---

## 14. References

- Amazon CloudWatch — metrics, statistics and percentiles, alarms with datapoints-to-alarm, composite alarms, embedded
  metric format, Logs retention `[STABLE — verify current pricing]`
- AWS CloudTrail — management events (default) and data events (opt-in, charged); organisation trails; log file
  validation `[STABLE]`
- M10-L13 (audit records and retention) and M10-L14 (detection time and false-alarm cost) `[STABLE]`
- M10-L08 (slices) and M10-L12 (quality gates) — what per-slice metrics are for `[STABLE]`
- M13-L11 (latency percentiles) and M13-L12 (online monitoring) `[STABLE]`

---

## 15. Next lesson

→ [M11-L17 — KMS, Secrets Manager, Backups and Disaster Recovery](M11-L17-kms-secrets-backups-dr.md) covers the keys that
decide who can read your data, the secrets that should never be in an image or an environment variable, and the backups
that only count once you have restored from one.
