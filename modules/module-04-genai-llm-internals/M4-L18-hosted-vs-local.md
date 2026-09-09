# M4-L18 — Hosted vs Local Models: Quality, Latency, Context, Licensing, Cost

| | |
|---|---|
| **Lesson ID** | M4-L18 |
| **Difficulty** | 2 (Intermediate) |
| **Estimated study time** | 2 hours |
| **Prerequisites** | [M4-L17](M4-L17-serving.md), [M4-L01](M4-L01-foundation-models.md) |

---

## 1. Learning objectives

1. **Compute** the break-even volume at which self-hosting beats per-token pricing.
2. **Evaluate** the seven axes on which the decision actually turns.
3. **Explain** why utilisation, not volume, is what makes self-hosting cheap or expensive.
4. **Read** a model licence well enough to know what you may not do.
5. **Design** a hybrid deployment and say what each route is for.

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **Hosted / API model** | Accessed over an API; the provider runs the hardware. |
| **Local / self-hosted** | You run the weights on hardware you control. |
| **Open weights** | Weights downloadable, often under a restrictive licence. |
| **Open source** (OSI sense) | Freedom to use, study, modify and redistribute. |
| **Utilisation** | The fraction of provisioned capacity actually doing work. |
| **Break-even volume** | The request rate at which two cost models cross. |
| **Data residency** | A legal requirement that data stay in a jurisdiction. |
| **Egress** | The cost of moving data out of a cloud provider. |
| **Cold start** | Time to load a model into memory before serving. |
| **Acceptable use policy** | Provider terms restricting what you may do with a hosted model. |

---

## 3. Plain-language explanation

### 3.1 Seven axes, not one

The argument is usually held as if it were about cost. It rarely is:

| Axis | Hosted | Self-hosted |
|---|---|---|
| **Quality** | Frontier models available | Best open weights, generally behind |
| **Latency** | Network round trip; shared queue | No network hop; you control the queue |
| **Context** | Long windows available | Bounded by your KV-cache memory (M4-L17) |
| **Cost** | Per token; zero when idle | Fixed hardware; **paid when idle** |
| **Privacy** | Data leaves your boundary | Data never leaves |
| **Control** | Versions change under you | You pin exactly what you run |
| **Effort** | An API key | Serving, scaling, monitoring, on-call |

**The last row is the one most often underestimated**, and the one that decides most real projects.

### 3.2 The cost picture is about utilisation, not volume

```
Hosted:      cost = requests × tokens × price_per_token       (zero when idle)
Self-hosted: cost = hours × hourly_rate                       (fixed, always)
```

**Self-hosting is cheap only when the hardware is busy.** An accelerator at 5% utilisation costs the
same as one at 95%, and you are paying for the idle 95%.

**So the real question is not "how many requests do we serve?" but "how evenly are they spread?"** A
million requests in one hour and a million spread over a month have identical hosted cost and wildly
different self-hosted cost. §7.3 measures this.

### 3.3 Open weights is not open source

M4-L01 §5.7 introduced this; here is why it belongs in a deployment decision.

**Most "open" LLMs are open *weights* under a custom licence.** Restrictions commonly seen `[UNVERIFIED
— read the actual licence for any model you use]`:

- No commercial use, or none above a user threshold
- No use to train competing models
- Attribution requirements
- Acceptable-use terms binding on you
- Field-of-use restrictions

**This is a legal question, not a technical one.** Get it reviewed before you build on it. Nothing in
this course is legal advice.

---

## 4. Analogy

**Taxis versus buying a van.** Taxis cost per journey and nothing when you are not travelling. A van
costs the same whether it moves or not. The crossover is not about total distance; it is about **how
much of the time the van is driving**.

### Where the analogy breaks

1. **Any taxi will do. A hosted frontier model may be materially better** than the best van you can buy
   — quality is not equivalent across the two options.
2. **You can drive a van yourself. Running inference well is a specialism** — batching, monitoring,
   failover, upgrades.
3. **A van does not change under you.** A hosted model version can be deprecated or altered, changing
   your system's behaviour without a deploy on your side.
4. **Taxis do not see your cargo.** Sending data to a hosted model is a disclosure, and sometimes that
   alone settles the decision.

---

## 5. Detailed technical explanation

### 5.1 The break-even calculation

**Hosted:**

```
monthly = requests × (in_tokens × in_price + out_tokens × out_price)
```

**Self-hosted:**

```
monthly = instance_hourly × 730 × instances
```

Set equal and solve for requests. §7.3 does this across scenarios — and the crossover is **much higher
than intuition suggests**, because idle capacity is pure loss.

**What the simple version omits, and should not:**

| Omitted | Typical effect |
|---|---|
| Engineering time to build and operate | Often the largest cost |
| On-call and incident response | Ongoing |
| Redundancy (you need ≥2 instances) | ~2× hardware |
| Peak provisioning | Sized for peak, paid at average |
| Model upgrades and re-evaluation | Recurring |
| Egress and storage | Small but real |

**Include at least redundancy and peak provisioning**, or the comparison is not honest. A single
instance is not a production deployment.

### 5.2 Utilisation is the whole story

```
effective_cost_per_request = hourly_rate / (requests_per_hour_at_peak × utilisation)
```

| Utilisation | Effective multiplier on cost |
|---|---|
| 100% | 1× |
| 50% | 2× |
| 20% | 5× |
| 5% | **20×** |

**A workload that is bursty — office hours, weekday-only, seasonal — has low utilisation by
construction**, and self-hosting it is expensive regardless of total volume.

### 5.3 When each wins

**Hosted wins when:**

- Volume is low, bursty or unpredictable
- You need frontier quality
- You have no ML infrastructure team
- Time to market matters
- Very long context is needed

**Self-hosted wins when:**

- Volume is high **and steady**
- Data cannot leave your boundary (this alone can be decisive)
- You need exact version pinning
- The task is narrow and a small model suffices (M4-L11 §5.5)
- Per-request latency is critical and the network hop matters

**The strongest genuine case for self-hosting is usually not cost.** It is **data residency or version
control** — requirements that money cannot buy from a hosted provider.

### 5.4 Hybrid deployments

Most mature systems use both:

| Pattern | Route to local | Route to hosted |
|---|---|---|
| **Tiered by difficulty** | Routine requests | Hard ones |
| **Tiered by sensitivity** | Anything with personal data | Everything else |
| **Small-model-first** | Classification, extraction, routing | Generation |
| **Fallback** | Normal operation | When local is saturated |

**The small-model-first pattern is the most reliably valuable**, and M4-L11 §7.3 measured why: a 110M
encoder is **636×** smaller than a 70B decoder for a narrow classification task, runs locally on a CPU,
and has no prompt-injection surface.

### 5.5 The costs that are not on the invoice

| Cost | Hosted | Self-hosted |
|---|---|---|
| Version deprecation forcing re-evaluation | **Yes** | No |
| Rate limits shaping your architecture | **Yes** | No |
| Provider outage you cannot fix | **Yes** | No |
| Building and running the serving stack | No | **Yes** |
| On-call for inference | No | **Yes** |
| Hardware procurement lead time | No | **Yes** |
| Your data in someone else's systems | **Yes** | No |

### 5.6 Assumptions and limitations

- All prices and hardware rates change constantly. Everything numeric here is **illustrative** and
  marked as such; substitute current figures before deciding anything.
- Open-model quality relative to frontier models changes rapidly.
- Licence terms change between model versions. Re-read on every upgrade.

---

## 6. Worked example — the decision, done properly

**The proposal:** *"We do 500,000 requests a month. Self-hosting will be cheaper."*

**Step 1 — the naive comparison.** 2,000 input and 400 output tokens per request, at illustrative rates
of \$0.50/M input and \$1.50/M output (a small hosted model):

```
Hosted:  500,000 × (2,000 × 0.50 + 400 × 1.50) / 1e6
       = 500,000 × (0.0010 + 0.0006)
       = $800/month
```

Self-hosting on one accelerator at an illustrative \$2/hour:

```
1 × $2 × 730 = $1,460/month
```

**Hosted already wins**, before anything else is counted.

**Step 2 — make the self-hosted figure honest.**

```
Redundancy (2 instances):            $2,920
Peak provisioning (2× average):      $5,840
Engineering: 0.25 FTE at $120k/yr:   $2,500/month
                                    --------
Realistic total:                     $8,340/month
```

**Ten times the hosted cost.**

**Step 3 — find the actual break-even.** Solve `requests × 0.0016 = 8,340`:

```
requests = 5,212,500 per month  ≈ 10.4× the current volume
```

**Step 4 — check whether utilisation even permits it.** 500,000 requests a month is **11.4 per minute
on average**. If they arrive in office hours on weekdays, the real rate during those hours is roughly
5× the average, and utilisation outside them is **near zero**.

**A bursty workload cannot reach the utilisation that makes self-hosting cheap, at any volume**, unless
you scale instances up and down — which is engineering effort you have not costed.

**Step 5 — now ask the question that actually decides it.** Cost said hosted, clearly. So:

> **Is there a requirement that money cannot satisfy?**

| Requirement | Verdict |
|---|---|
| Data must not leave our infrastructure | **Self-host, regardless of cost** |
| We must pin an exact model version indefinitely | **Self-host** |
| We need frontier quality | Hosted |
| We need it working next month | Hosted |

**Step 6 — the honest conclusion.** At this volume, self-hosting is 10× more expensive and would need
**10.4× the traffic** to break even — and even then only if the traffic were evenly spread, which it is
not.

**Unless there is a data-residency or version-pinning requirement, hosted is correct.** And if there
*is* such a requirement, the decision was never about cost and the whole calculation above was
answering the wrong question.

**Step 7 — a caution about every number here.** These are illustrative rates from 2026-09-09, not
quotes. Prices, hardware rates and model quality all change. **The method transfers; the numbers do
not.** Redo it with current figures, and include redundancy, peak provisioning and engineering time or
the comparison is not honest.

---

## 7. Practical activity

**File:** [`labs/m4/l18_hosted_vs_local.py`](../../labs/m4/l18_hosted_vs_local.py)

**No API key, no network, no cloud resources.** Nothing is provisioned and nothing is billable.

```bash
source .venv/bin/activate
python labs/m4/l18_hosted_vs_local.py
```

Reproduces §6's arithmetic, computes break-even across scenarios, models utilisation's effect,
demonstrates why a bursty workload cannot reach break-even, and scores the seven-axis decision.

### 7.2 Expected output

`[EXECUTED]` on Python 3.12.3, NumPy 2.5.3, 2026-09-09. **Nothing was provisioned; cost £0.00.**

```text

============================================================================
1. THE NAIVE COMPARISON  (and why it is wrong)
============================================================================
  500,000 requests/month, 2,000 input + 400 output tokens each
  ILLUSTRATIVE rates: $0.50/M in, $1.50/M out, $2.00/GPU-hour

  option                                           $/month
  hosted                                               800
  self-hosted, 1 instance (the naive figure)         1,460

  Hosted already wins, before anything else is counted.

  making the self-hosted figure honest:
  1 instance                                         1,460   not a production deployment
  + redundancy (2 instances)                         2,920   one instance is a single point of failure
  + peak provisioning (4 total)                      5,840   sized for peak, paid at average
  + 0.25 FTE engineering                             8,340   usually the largest line

  realistic self-hosted : $8,340/month
  hosted                : $800/month
  self-hosting is 10x MORE expensive at this volume.

============================================================================
2. WHERE IS THE ACTUAL BREAK-EVEN?
============================================================================
  hosted cost per request : $0.001600
  self-hosted fixed cost  : $8,340/month
  break-even              : 5,212,500 requests/month
                          = 10.4x the current volume

    monthly requests    hosted $   self-hosted $     cheaper
             100,000         160           8,340      hosted
             500,000         800           8,340      hosted
           2,000,000       3,200           8,340      hosted
           5,000,000       8,000           8,340      hosted
          10,000,000      16,000           8,340 self-hosted
          50,000,000      80,000           8,340 self-hosted

  Note the self-hosted column does not move. That is the whole point:
  it is a FIXED cost, paid whether the hardware is busy or idle.

============================================================================
3. UTILISATION IS THE WHOLE STORY
============================================================================
  A fixed cost divided by actual work done. If the accelerator is idle
  95% of the time, you paid for the idle 95%.

    utilisation  effective multiplier   effective $/request
          100%                  1.0x                0.0033
           70%                  1.4x                0.0048
           50%                  2.0x                0.0067
           30%                  3.3x                0.0111
           20%                  5.0x                0.0167
           10%                 10.0x                0.0334
            5%                 20.0x                0.0667

  A workload that is bursty BY CONSTRUCTION -- office hours, weekdays,
  seasonal -- cannot reach high utilisation at any total volume.

============================================================================
4. A REALISTIC ARRIVAL PATTERN, AND WHY IT CANNOT BREAK EVEN
============================================================================
  500,000 requests/month arriving in weekday office hours

  total hours in month                     730
  hours with any traffic                   199  (27%)
  mean requests/hour (all hours)           685
  peak requests/hour                      3502
  peak / mean                              5.1x

  You must provision for the PEAK (3502/hr) and you
  are paid-for at the MEAN (685/hr).
  -> utilisation = 19.6%, an effective cost multiplier of 5.1x

  break-even at 100% utilisation :    5,212,500 requests/month
  break-even at 20% utilisation  :   26,650,646
                                  = 53x the current volume

  A bursty workload does not reach break-even at ANY volume without
  autoscaling -- which is more engineering effort you have not costed.

============================================================================
5. WHEN DOES SELF-HOSTING ACTUALLY WIN?
============================================================================
  Varying volume AND steadiness. 'steady' means traffic spread evenly;
  'bursty' means the weekday-office-hours pattern above.

    monthly requests   hosted $  steady self $  bursty self $        winner
             500,000        800          5,420          6,880        hosted
           5,000,000      8,000          8,340         22,940        hosted
          20,000,000     32,000         18,560         79,880 self (steady)
         100,000,000    160,000         76,960        377,720 self (steady)

  Self-hosting starts to win at high AND steady volume. The bursty
  column never does, because it must provision for a peak it only
  reaches for a few hours a day.

============================================================================
6. THE DECISION IS RARELY ABOUT COST
============================================================================
  requirement                         points to         why
  quality needed: frontier            hosted            open weights lag frontier models
  volume: low or bursty               hosted            zero cost when idle
  volume: high and steady             self              utilisation makes fixed cost pay
  data cannot leave our boundary      SELF (decisive)   money cannot buy this from a provider
  must pin an exact version forever   SELF (decisive)   hosted versions get deprecated
  no ML infrastructure team           hosted            effort is the underestimated axis
  time to market matters              hosted            an API key vs a serving stack
  narrow task, small model suffices   self              a 110M encoder runs on a CPU (M4-L11)
  very long context needed            hosted            your KV cache bounds it (M4-L17)

  Two rows say DECISIVE. Those are the requirements money cannot
  satisfy -- and when either applies, the cost calculation above was
  answering the wrong question entirely.

  the cost axis, for this scenario, said:
    hosted $800/month vs self-hosted $8,340/month -> hosted, by 10x

  So: unless there is a residency or version-pinning requirement,
  hosted is correct here. And if there IS one, cost was never the
  deciding factor.

============================================================================
7. WHAT THIS LAB DID NOT COST YOU
============================================================================
  This lab provisioned NOTHING. No cloud account, no accelerator, no
  API key, no network call. It is arithmetic, and it cost 0.00.

  Every price in it is ILLUSTRATIVE and dated 2026-09-09:
    input tokens   $   0.50 per million
    output tokens  $   1.50 per million
    accelerator    $   2.00 per hour
    engineer       $120,000 per year fully loaded

  THE METHOD TRANSFERS; THE NUMBERS DO NOT. Substitute current rates,
  include redundancy, peak provisioning and engineering time, and redo
  it. A comparison that omits those three is not an honest comparison.

  And if you do provision an accelerator to test any of this: SHUT IT
  DOWN afterwards. An idle GPU bills exactly like a busy one, and a
  billing alert notifies you rather than capping the spend.

Done.
```

### 7.3 Reading the result

**Section 1 reproduces §6 exactly.** Hosted **\$800/month**; a single self-hosted instance
**\$1,460** — hosted already wins before anything else is counted. Making the self-hosted figure
honest by adding redundancy, peak provisioning and a quarter of an engineer takes it to **\$8,340**,
**10× the hosted cost**.

**Each of those three additions is not optional.** One instance is not a production deployment; you
size for peak and pay at the average; and somebody has to build and run the serving stack.

**Section 2 finds the break-even at 5,212,500 requests/month — 10.4× the current volume.** The
scenario table makes the shape clear: **the self-hosted column does not move.** It is a fixed cost paid
whether the hardware is busy or idle, which is the entire reason utilisation matters more than volume.

**Section 3 prices idleness.** At 20% utilisation the effective cost multiplier is **5×**; at 5% it is
**20×**.

**Section 4 is the section that settles the argument.** Modelling 500,000 requests arriving in weekday
office hours:

| | |
|---|---|
| Hours with any traffic | **199 of 730 (27%)** |
| Peak / mean requests per hour | **5.1×** |
| Resulting utilisation | **19.6%** |
| Break-even at 100% utilisation | 5,212,500/month |
| **Break-even at 19.6% utilisation** | **26,650,646/month — 53× current volume** |

**You must provision for the peak and you are paid-for at the mean.** A bursty workload does not reach
break-even at *any* volume without autoscaling — which is more engineering effort you have not costed.

**Section 5 shows where self-hosting does win:** at 20M+ requests/month **and steady**. The bursty
column never wins at any volume in the table, because it must provision for a peak it reaches for a few
hours a day.

**Section 6 lists the seven axes and marks two as decisive** — data residency and version pinning.
**Those are requirements money cannot satisfy**, and when either applies the cost calculation was
answering the wrong question.

**Section 7 states what the lab cost: nothing.** No cloud account, no accelerator, no API key. Every
price is illustrative and dated. **The method transfers; the numbers do not** — substitute current
rates, include redundancy, peak and engineering, and redo it. And if you provision anything to test it,
**shut it down**: an idle GPU bills exactly like a busy one, and a billing alert notifies rather than
caps.

---

## 8. Common mistakes and troubleshooting

1. **Comparing hosted token cost with one instance's hourly rate.** Add redundancy and peak.
2. **Ignoring engineering time.** Usually the largest self-hosting cost.
3. **Assuming high volume implies self-hosting.** Utilisation decides, not volume.
4. **Not reading the licence.**
5. **Assuming an open model matches a frontier model.** Evaluate on your task.
6. **Forgetting hosted versions get deprecated.** Budget for re-evaluation.
7. **Treating cost as the deciding axis** when a residency requirement exists.

| Symptom | Likely cause | Fix |
|---|---|---|
| Self-hosted costs more than projected | Idle capacity | Measure utilisation; consider hosted |
| Hosted costs grew unexpectedly | Volume or prompt growth | Log token usage; cache; trim prompts |
| Quality dropped after a provider update | Version change | Pin versions; re-run evaluations |
| Legal blocked the launch | Licence or residency | Review before building |
| Local model much worse than expected | Open-model gap | Benchmark on your task before committing |
| Capacity fine on average, fails at peak | Sized for average | Size for peak, or autoscale |

---

## 9. Security, privacy, reliability, cost

- **Privacy.** Sending data to a hosted model is a **disclosure**. Know the provider's retention and
  training-use terms, and whether a zero-retention option exists. For regulated data this is frequently
  the deciding factor and it belongs in your DPIA (M10-L11).
- **Privacy.** Self-hosting keeps data in your boundary — **and makes you responsible for securing it
  there.** It moves the risk; it does not remove it.
- **Cost.** **Never provision an accelerator without a shutdown plan.** An idle GPU bills identically to
  a busy one. Set a budget alert, and remember it **notifies rather than caps**.
- **Reliability.** Hosted means a dependency you cannot fix during an outage. Self-hosted means you are
  on call. Both need a documented degraded mode.
- **Legal.** Open weights ≠ open source. Read the licence, get it reviewed, and re-read on every model
  upgrade. Nothing here is legal advice, and no technical control establishes compliance.
- **This lesson provisions nothing.** The lab is pure arithmetic and costs £0.00.

---

## 10. Exercises

### Exercise 1 — Beginner (~20 min)

1. Name the seven axes and say which is most often underestimated.
2. Compute hosted cost for 200,000 requests at 1,500 in / 300 out tokens at \$0.50/M and \$1.50/M.
3. Why does utilisation matter more than volume?
4. Give two requirements that make self-hosting correct regardless of cost.
5. What is the difference between open weights and open source?

### Exercise 2 — Intermediate (~35 min)

1. Run the lab and reproduce §6's break-even of 5.2M requests.
2. Add redundancy, peak provisioning and engineering time to a comparison and report how the break-even
   moves.
3. Model a weekday-office-hours workload and compute its true utilisation.
4. Compute the effective cost multiplier at 5%, 20%, 50% and 100% utilisation.
5. Design a small-model-first hybrid and estimate the fraction of traffic each route handles.

### Exercise 3 — Challenge (~45 min)

1. Build a decision tool taking volume, burstiness, sensitivity and quality requirements, and returning
   a recommendation with the reasoning.
2. Model autoscaling: given an arrival pattern and a cold-start time, compute the instance-hours needed
   and compare with fixed provisioning.
3. Write the one-page recommendation for a real decision at your organisation, with numbers and stated
   assumptions.
4. Build a cost monitor that alerts when hosted spend would exceed the self-hosted break-even for three
   consecutive months.
5. Read one real open-model licence and write a summary of what you may and may not do with it, listing
   anything you would need legal review for.

---

## 11. Quiz

*(Answers: [`answer-keys/module-04-answers.md`](../../answer-keys/module-04-answers.md#m4-l18).)*

**Q1.** Self-hosting becomes cheaper primarily as a function of:

- A. The total number of requests served each month.
- B. The number of distinct models you need to run.
- C. Hardware utilisation — how busy the accelerator is.
- D. The average number of tokens in each request.

**Q2.** An accelerator at 20% utilisation has an effective cost multiplier of:

- A. 1.2×  B. 2×  C. 5×  D. 0.2×

**Q3.** A fair self-hosted comparison must include:

- A. Redundancy, peak provisioning and engineering time.
- B. The hourly rate plus data egress charges.
- C. Only the instance hourly rate, which is the direct cost.
- D. The hourly rate divided by expected utilisation.

**Q4.** "Open weights" means:

- A. The model may be used freely for any commercial purpose.
- B. Weights are downloadable, often under a restrictive licence.
- C. The training data has been published alongside the model.
- D. The same as open source, under a different label.

**Q5.** The strongest genuine case for self-hosting is usually:

- A. Lower total cost at moderate request volumes.
- B. Access to higher-quality models than hosted providers offer.
- C. Reduced engineering effort compared with API integration.
- D. Data residency or exact version pinning.

**Q6.** A bursty weekday-office-hours workload:

- A. Reaches high utilisation because peaks are concentrated.
- B. Has utilisation independent of the arrival pattern.
- C. Has low utilisation, making self-hosting expensive.
- D. Is unaffected by utilisation, since cost scales with volume.

**Q7.** Which cost applies to hosted but not self-hosted?

- A. Building and operating the serving stack.
- B. Being on call for inference failures.
- C. Version deprecation forcing re-evaluation.
- D. Hardware procurement lead time.

**Q8.** In §6, how much traffic would be needed to reach break-even?

- A. About 2× the current volume.
- B. About the current volume already.
- C. About 100× the current volume.
- D. About 10× the current volume.

**Q9.** The small-model-first hybrid pattern routes to a local model:

- A. Every request, with a hosted fallback on failure only.
- B. Only requests arriving outside normal business hours.
- C. Requests from users who have opted out of hosted processing.
- D. Narrow tasks like classification, extraction and routing.

**Q10.** Before provisioning a cloud accelerator you should:

- A. Set a billing alert, which will cap the spending.
- B. Have a shutdown plan; an idle GPU bills like a busy one.
- C. Reserve capacity for a year to obtain the lowest rate.
- D. Provision for peak plus 50% to avoid any queueing.

**Q11.** *(Written, rubric-graded.)* In under 120 words, respond to a director who says "we do half a
million requests a month, we should obviously host our own model."

---

## 12. Revision notes

- **Seven axes: quality, latency, context, cost, privacy, control, effort.** **Effort is the most
  underestimated**, and it decides most real projects.
- **Hosted: per token, zero when idle. Self-hosted: fixed, paid when idle.**
- **Utilisation, not volume, decides cost.** 20% utilisation is a **5× effective multiplier**. A bursty
  workload cannot reach break-even at any volume without autoscaling you have not costed.
- **A fair comparison includes redundancy (≥2 instances), peak provisioning, and engineering time** —
  which is usually the largest line. A single instance is not a production deployment.
- **§6's result: self-hosting was 10× more expensive and needed 10.4× the traffic to break even** —
  and **53×** once the workload's real 19.6% utilisation is accounted for.
- **The strongest genuine case for self-hosting is not cost — it is data residency or version
  pinning**, requirements money cannot buy from a provider.
- **Open weights ≠ open source.** Restrictive custom licences are the norm. **Read it; get it
  reviewed; re-read on every upgrade.**
- **Small-model-first is the most reliably valuable hybrid**: narrow tasks to a small local model
  (M4-L11 measured **636×** fewer parameters), generation to a hosted one.
- **Never provision an accelerator without a shutdown plan.** A billing alert **notifies; it does not
  cap.**

---

## 13. Completion checklist

- [ ] I can compute a break-even volume including redundancy and engineering.
- [ ] I can explain why utilisation matters more than volume.
- [ ] I can name the seven axes and which is underestimated.
- [ ] I know the two requirements that override the cost argument.
- [ ] I know open weights is not open source, and that it is a legal question.
- [ ] I can design a small-model-first hybrid.
- [ ] I scored 8/11 on the quiz.

---

## 14. References

- Open Source Initiative, *The Open Source AI Definition*. <https://opensource.org/ai> `[UNVERIFIED]`
- vLLM documentation. <https://docs.vllm.ai/> `[UNVERIFIED]`
- Hugging Face, *Model licences*. <https://huggingface.co/docs/hub/repositories-licenses>
  `[UNVERIFIED]`

---

## 15. Next: Project 4

→ [Project 4 — Controlled Model Behaviour Comparison](../../projects/project-04-model-comparison/README.md)

Module 4's lessons are complete. Next: a project that puts the decoding, tokenization and context
material to work in a reproducible comparison harness — and then the module assessment.
