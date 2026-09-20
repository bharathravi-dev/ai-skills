# M11-L06 — Billing, Budgets and Cost Allocation — and why alerts are not caps

| | |
|---|---|
| **Lesson ID** | M11-L06 |
| **Difficulty** | 2 (Intermediate) |
| **Estimated study time** | 1.75 hours |
| **Prerequisites** | [M11-L03](M11-L03-account-root-mfa.md), [M8-L15](../module-08-agentic-ai/M8-L15-step-limits-cost-budgets-runaway.md) |

---

## 1. Learning objectives

1. **Explain** why a budget alert cannot stop a runaway, using the lag arithmetic.
2. **Distinguish** alerts from genuine caps, and choose which failure each cap causes.
3. **Enforce** tagging at creation, because unattributable spend is spend nobody reduces.
4. **Compute** unit cost per request and project it across traffic levels.
5. **Read** an itemised bill and identify the lines that are not the product.

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **Budget** | A threshold on forecast or actual spend that triggers a notification or an action. |
| **Cost anomaly detection** | Alerting on a spend pattern that deviates from the learned baseline. |
| **Cap** | A mechanism that makes spending physically impossible, by failing something. |
| **Service quota** | A per-account, per-region limit on a resource or a request rate. |
| **Cost allocation tag** | A tag activated for billing, so spend can be grouped by owner, environment or service. |
| **Unit economics** | Cost per request, per user or per transaction. |
| **Chargeback / showback** | Attributing cost to the team that incurred it, with or without an internal transfer. |
| **Runaway** | Spend caused by a defect — a retry loop, an agent loop, an unbounded scan. |

---

## 3. Plain-language explanation

### 3.1 The alert arrives after the money is gone

§7.1 traces a retry loop burning **$640/hour** from 23:00 on a Friday. Metering reaches billing data after **6 hours**;
the budget evaluates and sends after **4 more**; someone reads it after **8**; diagnosis **2**; the fix **1**. Total:
**21 hours and $13,440**, of which **10 hours** were the alerting pipeline itself.

A budget alert tells you about money you have **already spent**. It is a smoke detector, not a sprinkler.

### 3.2 A cap is something that breaks on purpose

§7.2 classifies nine mechanisms: **7 are genuine caps**, 2 are alerts. Every genuine cap has a cost when it bites —
requests fail, queues back up, deploys are rejected, work is truncated. That is precisely what makes it a cap. The
decision is *which failure you prefer*, taken calmly in advance rather than at 2am.

### 3.3 Untagged spend is unowned spend

§7.3: on an $84,000 monthly bill, 30% tag coverage leaves **$58,800** unattributable; 85% still leaves **$12,600**. Below
about 95% coverage, the monthly review is an argument rather than a decision — and the unattributable part is the part
nobody reduces.

### 3.4 Unit economics are dominated by the model

§7.4 itemises one AI request at **$0.0154**. The model's input and output tokens are **86%** of it. At 100,000
requests/day that is **$46,200/month**; at a million, **$462,000**. Halving retrieved context saves more than every
infrastructure line added together.

### 3.5 Two of the biggest lines are not the product

§7.5: on the same bill, **non-production environments (12%)** and **idle or forgotten resources (6%)** are **18%** of
spend and serve no user. NAT gateway and data transfer (5%) and observability (8%) are both commonly reducible without
touching the product.

---

## 4. Analogy

**A mobile phone bill abroad.** The warning text arrives after the data has been used, often hours later, sometimes after
you are already over. The only things that actually stop the spend are switching data roaming off, or a hard cap the
network enforces — and both of those break something you might have wanted. "Bill shock" is not an information problem; it
is a control problem.

### Where the analogy breaks

- **Your phone has one meter; a cloud account has hundreds**, and a runaway can start in a service you have not looked at
  for a year (§5.5).
- **Roaming stops when you land; a retry loop does not get bored.** Software failure modes sustain maximum spend
  indefinitely (M8-L15).

---

## 5. Detailed technical explanation

### 5.1 Why alerts lag

`[REAL, computed — ILLUSTRATIVE figures]` §7.1 — 21 hours, $13,440.

Three lags compound:

| Lag | Cause | Typical scale |
|---|---|---|
| Metering to billing data | Usage records are aggregated and delivered periodically | Hours |
| Budget evaluation | Budgets evaluate on a schedule, not continuously | Hours |
| Human response | Notification, attention, diagnosis, action | Hours, worse out of hours |

Reduce each where you can — CloudWatch metrics on *your own* usage counters (tokens, invocations, queue depth) are
near-real-time and are a far better runaway signal than billing data (L16, M13-L12). But do not expect any of it to
*stop* anything.

### 5.2 Real caps, and what each one breaks

`[REAL, classified]` §7.2 — 7 of 9 are caps.

| Cap | Where it lives | What breaks |
|---|---|---|
| `max_tokens`, step limits, loop limits | Your code | Truncated or abandoned work (M8-L15) |
| Rate limiter in front of the model | Your code / gateway | Users queued or rejected |
| Reserved concurrency (Lambda) | Platform | Throttling; backlog |
| Service quotas | Platform | Requests fail account-wide |
| Provisioned rather than on-demand capacity | Architecture | Queuing at the ceiling |
| SCP denying expensive resource types | Organizations | Deploys rejected until reviewed (L03) |
| Budget action: stop/detach | Automation | The environment stops; in-flight work may be lost |

The order to adopt them: **in-application limits first** (cheap, precise, no collateral damage), then concurrency and rate
limits, then account guardrails, then automated shutdown for non-production only. Automated shutdown in production is a
self-inflicted outage with a budget trigger; use it in dev and test, where it is a feature.

### 5.3 Tagging that works

`[REAL, computed]` §7.3.

```text
Minimum useful tag set:
  owner          a team or person, resolvable to someone on call
  environment    dev | test | staging | prod
  service        the system this belongs to (matches the L03 inventory id)
  cost-centre    for chargeback
  data-class     for L06 retention and residency decisions
```

Enforce at **creation**: tag policies in Organizations, required tags in infrastructure code (L18), and an SCP that denies
resource creation without the required tags where the service supports it. Retrospective tagging never reaches 95%,
because the untagged resources are the ones whose owner has left.

Activate the tags as **cost allocation tags** in billing, or they will not appear in cost reports at all.

### 5.4 Unit economics

`[REAL, computed — ILLUSTRATIVE rates]` §7.4 — $0.0154 per request, 86% model.

```text
unit_cost = model_in + model_out + embedding + search + rerank + compute + logs + transfer
monthly   = unit_cost × requests_per_day × 30
```

Compute this **before** launch and re-compute when anything changes. It converts design decisions into money: retrieving
12 chunks instead of 6, or a 4,000-token system prompt instead of 800, is now a line item rather than a preference
(M5-L15).

The optimisation order follows the shares: context length and retrieved-chunk count, caching (M5-L16), a smaller model
for easy cases with routing (M13-L08), output length, and only then infrastructure.

### 5.5 Reading the bill

`[REAL, computed — ILLUSTRATIVE bill]` §7.5.

The lines that surprise teams, in rough order of frequency:

- **Non-production environments** running 24/7 for a team that works 40 hours a week.
- **Idle and forgotten resources**: unattached volumes, old snapshots, idle endpoints, a load balancer for a decommissioned
  service.
- **NAT gateway** data-processing charges for traffic that could use a VPC endpoint (L08).
- **Observability**: log ingestion and retention, often larger than the compute it observes (L16).
- **Cross-AZ data transfer** from a chatty design (L02).

Do the review **itemised and monthly**, with the tag dimensions from §5.3, and give each of the top five lines an owner.

### 5.6 A practical baseline

```text
Day 1 of any account:
  [ ] budget with alerts at 50 / 80 / 100% of forecast and actual
  [ ] cost anomaly detection enabled
  [ ] required tags enforced at creation; cost allocation tags activated
  [ ] in-app caps: max_tokens, step limits, per-run cost ceiling (M8-L15)
  [ ] service quotas reviewed for the services you use
  [ ] non-production: scheduled shutdown, and a budget action that stops it
  [ ] a CloudWatch alarm on YOUR usage counter (tokens/hour), not on billing
  [ ] monthly itemised review with an owner per top-five line
```

### 5.7 Assumptions and limitations

- Every rate, lag and bill line in the lab is invented; the shape is representative, the numbers are not.
- Budget evaluation frequency, metering lag and pricing all change — check current documentation and your own data.
- Savings Plans, Reserved Instances and negotiated pricing are out of scope here and revisited in M12-L14.

---

## 6. Worked example — the £9,000 weekend

**The situation.** A team shipped an agent that retried failed tool calls. A downstream API began returning a transient
error on Friday evening. The retry had no backoff, no attempt limit and no cost ceiling (M8-L13, M8-L15).

**What happened.**

1. The loop ran at full rate all weekend. Each attempt was a model call with a long context.
2. A budget alert existed at 100% of the monthly forecast. It fired **Sunday afternoon** — the lag in §7.1, plus a monthly
   threshold that a weekend's burn took time to cross.
3. The alert went to a shared mailbox nobody watched at weekends.
4. Monday's diagnosis took two hours because spend was untagged; the bill showed "model inference" with no service
   dimension (§7.3).
5. The fix was four lines: a maximum attempt count, exponential backoff, a per-run token ceiling, and a CloudWatch alarm
   on tokens per hour.

| # | What was missing | Fix |
|---|---|---|
| 1 | Attempt limit and backoff | Bounded retries (M8-L13) |
| 2 | Per-run cost ceiling | A hard cap in the agent loop (M8-L15) |
| 3 | Near-real-time signal | Alarm on your own token counter, not on billing (§5.1) |
| 4 | Alert routing | Page a rota, not a mailbox (M10-L14) |
| 5 | Tags | Enforced at creation; spend attributable to the service (§5.3) |

**The general rule.** **The cheapest cap is the one in your own code, and it is the only one that can stop the spend in the
first minute.**

---

## 7. Practical activity

**File:** [`labs/m11/l06_billing_budgets_cost.py`](../../labs/m11/l06_billing_budgets_cost.py)

**No AWS account, no network, no third-party dependencies.** Fully deterministic.

```bash
source .venv/bin/activate
python labs/m11/l06_billing_budgets_cost.py
```

### 7.2 Expected output

`[EXECUTED]` — 2026-09-17, Python 3.12.3 (pure standard library). Run twice; output identical.

```text

============================================================================
1. WHAT A RUNAWAY COSTS BEFORE THE ALERT FIRES
============================================================================
  a retry loop starts burning $640/hour at 23:00 on a Friday

  stage                                           hours  cumulative       spent
  usage is metered and reaches billing data           6          6 h       3,840
  the budget evaluates and the alert is sent          4         10 h       6,400
  someone reads the alert (out of hours)              8         18 h      11,520
  someone works out what is spending                  2         20 h      12,800
  the change is made and takes effect                 1         21 h      13,440

  total before it stops: 21 hours, $13,440
  the alert itself accounted for 10 of those hours -- billing data lags,
  and budgets evaluate periodically. A budget alert tells you about money you
  have ALREADY spent. It is a smoke detector, not a sprinkler.

============================================================================
2. WHAT ACTUALLY CAPS SPEND?
============================================================================
  mechanism                                     caps?     latency   what it costs when it bites
  budget alert (email/SNS)                      alert       hours   nothing -- it only notifies
  cost anomaly detection                        alert       hours   nothing -- it only notifies
  service quotas / account limits                 CAP   immediate   requests fail; legitimate load fails too
  Lambda reserved concurrency                     CAP   immediate   throttling; queue backs up
  provisioned capacity instead of on-demand       CAP   immediate   queuing or rejection at the cap
  max_tokens and step limits in the app           CAP   immediate   truncated or abandoned work (M8-L15)
  SCP denying expensive instance types            CAP   immediate   deploys fail until reviewed (M11-L03)
  automated shutdown on a budget action           CAP       hours   the environment stops; data may be lost
  a rate limiter in front of the model            CAP   immediate   users are queued or rejected

  real caps: 7/9
  Every genuine cap breaks something on purpose. That is what makes it a cap.
  Choose which failure you prefer BEFORE the Friday night, and put the cheap
  ones (max_tokens, step limits, concurrency) in from day one (M8-L15).

============================================================================
3. CAN YOU EVEN TELL WHOSE SPEND IT IS?
============================================================================
  tag coverage   30% -> $   25,200 attributable, $  58,800 unattributable (arguments at the review)
  tag coverage   60% -> $   50,400 attributable, $  33,600 unattributable (arguments at the review)
  tag coverage   85% -> $   71,400 attributable, $  12,600 unattributable (arguments at the review)
  tag coverage   97% -> $   81,480 attributable, $   2,520 unattributable (usable for chargeback)
  tag coverage  100% -> $   84,000 attributable, $       0 unattributable (usable for chargeback)

  Untagged spend is not a reporting inconvenience: it is the part of the bill
  nobody will reduce, because nobody owns it. Enforce tags at creation with
  a tag policy and an SCP, not with a spreadsheet afterwards.
  Minimum useful tag set: owner, environment, service, cost-centre, data-class.

============================================================================
4. UNIT ECONOMICS OF ONE AI FEATURE  [ILLUSTRATIVE RATES]
============================================================================
  component                                USD/request    share
  model input tokens (2,400 @ $3/M)             0.0072      47%
  model output tokens (400 @ $15/M)             0.0060      39%
  reranking                                     0.0011       7%
  vector search                                 0.0004       3%
  logging and storage                           0.0003       2%
  compute (app, 300 ms)                         0.0002       1%
  embedding of the query                        0.0001       1%
  data transfer                                 0.0001       1%
  TOTAL                                         0.0154     100%

      1,000 requests/day -> $        15/day   $         462/month
     10,000 requests/day -> $       154/day   $       4,620/month
    100,000 requests/day -> $     1,540/day   $      46,200/month
  1,000,000 requests/day -> $    15,400/day   $     462,000/month

  the model is 86% of the unit cost, so that is where optimisation pays:
  shorter context, fewer retrieved chunks, caching, a smaller model for easy
  cases (M5-L15, M5-L16, M13-L08). Halving retrieved context here saves more
  than every infrastructure line added together.

============================================================================
5. WHERE THE MONEY ACTUALLY GOES  [ILLUSTRATIVE MONTHLY BILL]
============================================================================
  line                                 USD/month    share   note
  model inference                         38,400      46%   the unit-economics lever (section 4)
  non-production environments              9,800      12%   schedule them off outside working hours
  vector store / database                  9,200      11%   
  compute (containers)                     7,800       9%   
  logging and observability                6,900       8%   sampling and retention are levers (M11-L16)
  idle / forgotten resources               5,200       6%   nobody's, because nothing is tagged (section 3)
  NAT gateway + data transfer              4,100       5%   often replaceable by VPC endpoints (M11-L08)
  object storage                           2,600       3%   
  TOTAL                                   84,000     100%

  plausibly recoverable without touching the product: $11,080/month (13%)
  non-production and idle resources alone are 18% of the bill and serve no
  user. Look at the bill itemised at least monthly; the surprises are never in
  the line you expect.

============================================================================
6. WHAT THIS LAB IS AND IS NOT
============================================================================
  REAL: every total, share, cap classification and projection above is
  computed from the values in this script.

  ILLUSTRATIVE: every rate, burn figure, lag and bill line is invented, though
  the SHAPE (model dominates unit cost; NAT and logging are quietly large;
  non-production and idle resources are recoverable) is the common one.

  NOT SHOWN: Reserved Instances and Savings Plans, Cost Explorer itself,
  consolidated billing mechanics, and negotiated pricing (M12-L14).

Done.
```

### 7.3 Reading the result

**Section 1's fourth column** is the argument: $13,440 spent before anything stopped it, and the alert pipeline owned
10 of the 21 hours.

**Section 2's right-hand column** is the part usually skipped. Every cap costs something; pick which.

**Section 4's last line** says where engineering effort pays: the model is 86% of unit cost.

**Section 5** shows 18% of the bill serving nobody.

---

## 8. Common mistakes and troubleshooting

1. **Believing a budget alert will stop a runaway.** §5.1 — it reports history.
2. **Having no cap at all because every cap breaks something.** §5.2 — choose the failure deliberately.
3. **Alerting on billing data instead of your own counters.** §5.1 — tokens/hour is near-real-time.
4. **Retrospective tagging.** §5.3 — enforce at creation, or never reach 95%.
5. **Forgetting to activate cost allocation tags.** Tagged resources still show up untagged in reports.
6. **No unit-cost figure.** §5.4 — design decisions stay opinions without it.
7. **Reviewing the total, not the itemised bill.** §5.5 — the surprises are in lines nobody owns.
8. **Automated shutdown in production.** A self-inflicted outage with a budget trigger.
9. **Non-production running 24/7.** §7.5 — 12% of the bill in the lab.

| Symptom | Likely cause | Fix |
|---|---|---|
| Large unexplained spend increase | Runaway or forgotten resource, untagged | Tags at creation; itemised review with owners |
| The alert fired after the money was spent | Billing-data lag | Alarm on your own usage metric (L16) |
| Nobody can say whose spend it is | Tag coverage below 95% | Tag policies, SCP, infrastructure-as-code defaults |
| Cost grows faster than traffic | Context or retrieval growth | Recompute unit cost; check tokens per request (M5-L15) |
| Observability costs more than compute | Log volume and retention | Sample, set retention, drop debug logs in prod (L16) |

---

## 9. Security, privacy, reliability, cost

- **Security.** Spend anomalies are often the first visible sign of compromised credentials (L03, L05) — treat them as
  security signals, not only finance ones.
- **Privacy.** The `data-class` tag connects cost allocation to retention and residency decisions (M10-L06).
- **Reliability.** Caps cause failures by design; decide which and make them graceful — queue, degrade, abstain (M7-L13).
- **Cost.** Unit economics belong in the design document alongside latency, and are re-measured when traffic changes by an
  order of magnitude (M12-L14).

---

## 10. Exercises

### Exercise 1 — Beginner (~20 min)

1. How many of the 21 hours in §7.1 were alerting lag?
2. Name three genuine caps and what each breaks.
3. Why is retrospective tagging ineffective?
4. What share of unit cost was the model in §7.4?
5. Which two bill lines in §7.5 serve no user?

### Exercise 2 — Intermediate (~40 min)

1. Run the lab. Change the burn rate to $50/hour and decide whether the same controls are justified.
2. Add a mechanism to §7.2 that your team uses, and classify it.
3. Recompute §7.4 with your own model prices and context sizes.
4. Add a "GPU inference endpoints" line to §7.5 and see how the recoverable share changes.
5. Write the day-1 cost baseline (§5.6) for a new account and assign owners.

### Exercise 3 — Challenge (~60 min)

1. Compute the real unit cost of a feature you run, from measured token counts.
2. Implement a per-run cost ceiling in an agent loop and test that it triggers.
3. Build a CloudWatch-style alarm design on tokens per hour with a measured false-alarm rate (M10-L14).
4. Audit tag coverage in one account and write the enforcement plan.
5. Produce an itemised monthly review with an owner per top-five line, and one action each.

---

## 11. Quiz

*(Answers: [`answer-keys/module-11-answers.md`](../../answer-keys/module-11-answers.md#m11-l06).)*

**Q1.** Why can a budget alert not stop a runaway?

- A. Budgets only evaluate monthly
- B. Alerts are delivered without priority
- C. Budgets apply per region, not per account
- D. It reports spend that has already happened, after a metering and evaluation lag

**Q2.** In §7.1, how much was spent before the loop was stopped?

- A. $6,400
- B. $13,440
- C. $3,840
- D. $11,520

**Q3.** What distinguishes a cap from an alert?

- A. A cap makes spending impossible by failing something
- B. A cap is evaluated continuously rather than on a schedule
- C. A cap requires an SCP to be effective
- D. A cap notifies a rota rather than a mailbox

**Q4.** Which cap should be adopted first?

- A. Automated shutdown on a budget action
- B. A service quota reduction
- C. In-application limits such as `max_tokens` and step limits
- D. An SCP denying expensive instance types

**Q5.** Why is automated shutdown inappropriate in production?

- A. Budget actions cannot target production accounts
- B. It is a self-inflicted outage triggered by a spend threshold
- C. It cannot be reversed without root access
- D. Production spend is rarely the cause of overruns

**Q6.** In §7.3, what remained unattributable at 85% tag coverage?

- A. $2,520
- B. $33,600
- C. $58,800
- D. $12,600

**Q7.** Why does retrospective tagging fail?

- A. Tags cannot be applied to existing resources
- B. Cost allocation tags apply only from activation onwards
- C. The untagged resources are the ones whose owner has left
- D. Tag keys are case-sensitive and drift over time

**Q8.** In §7.4, what proportion of unit cost was model tokens?

- A. 86%
- B. 47%
- C. 39%
- D. 14%

**Q9.** Where should optimisation effort go first, given that split?

- A. Compute instance sizing
- B. Logging and storage volume
- C. Data transfer and NAT charges
- D. Context length, retrieved chunks, caching and model routing

**Q10.** Which signal detects a runaway fastest?

- A. The cost anomaly detector
- B. An alarm on your own usage counter, such as tokens per hour
- C. A daily budget threshold
- D. The itemised monthly bill

**Q11.** What are cost allocation tags for?

- A. Enforcing which resources may be created
- B. Applying retention policies to logs
- C. Grouping spend by owner, environment and service in cost reports
- D. Restricting access by team

**Q12.** Why treat a spend anomaly as a security signal?

- A. It is often the first visible sign of compromised credentials
- B. Billing data is protected by the same controls as audit logs
- C. Anomaly detection is part of the security services suite
- D. Spend thresholds are required by most compliance frameworks

**Q13.** *(Written, rubric-graded.)* In under 150 words: your team is launching an AI feature and has set a monthly budget
alert at 80% and 100%. Explain what that does and does not protect you from, and the three controls you would add.

---

## 12. Revision notes

- **Alerts lag**: metering **6 h** + evaluation **4 h** + human **11 h** = **21 h**, **$13,440** at $640/h.
- **7 of 9 mechanisms are real caps**, and every one of them breaks something on purpose. Choose the failure in advance.
- **Adoption order**: in-app limits → concurrency/rate limits → quotas and SCPs → automated shutdown (non-production only).
- **Tag at creation**: 85% coverage still leaves **$12,600** unattributable on an $84,000 bill; aim above 95%.
- **Unit cost $0.0154/request**, **86% model** → **$46,200/month** at 100k/day. Optimise context, retrieval, caching,
  routing.
- **18% of the lab's bill** is non-production and idle resources; NAT and observability are commonly reducible too.

---

## 13. Completion checklist

- [ ] I can explain why a budget alert is not a brake.
- [ ] My system has in-application caps on tokens, steps and per-run cost.
- [ ] Alarms watch my own usage counters, not just billing data.
- [ ] Required tags are enforced at creation and activated for cost allocation.
- [ ] I know my unit cost per request and what dominates it.
- [ ] The bill is reviewed itemised and monthly, with an owner per top line.
- [ ] I scored at least 10/13 on the quiz.

---

## 14. References

- AWS Budgets, budget actions, and Cost Anomaly Detection; AWS Cost Explorer and cost allocation tags — check current
  evaluation frequencies and pricing `[UNVERIFIED — check current]`
- M8-L15 (step limits, cost budgets and runaway prevention) — the in-application caps `[STABLE]`
- M5-L15 (token accounting) and M5-L16 (caching and routing) — the unit-cost levers `[STABLE]`
- M11-L08 (VPC endpoints vs NAT) and M11-L16 (log volume and retention) — the infrastructure lines `[STABLE]`
- M12-L14 (cost per request and workload estimates on AWS) `[STABLE]`

---

## 15. Next lesson

→ [M11-L07 — VPCs, Subnets, Route Tables and Security Groups](M11-L07-vpc-subnets-security-groups.md) starts the network:
the address plan you cannot change later, and the difference between a stateful security group and a stateless network
ACL.
