# M11-L11 — EC2 and the Compute Baseline

| | |
|---|---|
| **Lesson ID** | M11-L11 |
| **Difficulty** | 2 (Intermediate) |
| **Estimated study time** | 1.75 hours |
| **Prerequisites** | [M11-L07](M11-L07-vpc-subnets-security-groups.md), [M11-L06](M11-L06-billing-budgets-cost-allocation.md) |

---

## 1. Learning objectives

1. **Right-size** from measured p95 plus headroom, accepting that some workloads get *larger*.
2. **Choose** a purchase option from the workload's tolerance for commitment and interruption.
3. **Compute** autoscaling lag and explain why it is not a defence against spikes.
4. **Size AI workloads by concurrency and memory**, because they are not CPU-bound.
5. **Replace instances rather than patch them**, and measure the drift you have today.

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **Instance type** | A family and size, e.g. `m7i.2xlarge` — family, generation, size. |
| **AMI** | The machine image an instance boots from. |
| **EBS** | Network-attached block storage; separate lifecycle from the instance. |
| **Instance store** | Local disk, lost when the instance stops. |
| **Savings Plan** | A commitment to a level of *spend per hour* for one or three years, in exchange for a discount. |
| **Spot** | Spare capacity at a large discount, reclaimable with a short notice. |
| **Auto Scaling group** | A managed set of instances with a size policy and health replacement. |
| **Warm-up** | The time between an instance starting and being able to serve. |
| **Drift** | Divergence between a running instance and the image it came from. |

---

## 3. Plain-language explanation

### 3.1 Right-sizing is "measure, then fit" — not "make it smaller"

§7.1 right-sizes four workloads from measured p95 with 40% headroom. Two shrink. One stays where it is. And **one gets
bigger**: the embedding workers' p95 of 3.8 vCPU needs 5.3 with headroom, which does not fit their current size. The net
saving is **$280/month — 6%**, not the 40% a cost-optimisation slide promises.

### 3.2 Purchase options are a statement about commitment

§7.2: on-demand **$33,638/year** for ten instances; a 1-year Savings Plan **28%** less; a 3-year all-upfront plan
**45%** less; Spot **68%** less. Spot can be reclaimed on short notice — at a 5% hourly interruption rate, an instance
survives a 24-hour job only **29%** of the time, so Spot is for work that checkpoints and resumes (M8-L14).

Savings Plans commit you to **spend**, not to instances. That is safe for a stable baseline and wrong if you may move the
workload to containers or serverless inside the term.

### 3.3 Autoscaling responds in minutes

§7.3: traffic jumps from 160 to 420 rps. Alarm evaluation **120 s**, launch **45 s**, boot **40 s**, **application and
model-client warm-up 95 s**, health checks **30 s** — **330 seconds**, during which **85,800 requests** are queued or
rejected.

Autoscaling is a cost control and a slow-growth mechanism. Spikes are handled by headroom, a queue (L15), or deliberate
load shedding (M7-L13).

### 3.4 AI workloads are not CPU-bound

§7.4 profiles a request: **2,730 ms** total, of which **60 ms — 2.2%** is CPU. The rest is waiting on the model API,
the vector store and storage. A machine can hold roughly **46× more concurrent requests** than CPU utilisation suggests,
if the runtime can wait on many things at once (M2-L13).

So a fleet sized by CPU utilisation looks 2% busy and still falls over — on connection limits, memory, or the provider's
rate limits (M12-L12).

### 3.5 Long-lived instances cannot be reproduced

§7.5: **57%** of a 40-instance fleet is older than 90 days, and **55%** carries manual changes. An instance that has been
patched by hand is one you cannot rebuild — and the next scale-out event launches the *image*, not the instance someone
fixed.

---

## 4. Analogy

**Hiring vans for a delivery business.** You size from your busiest realistic day plus a margin, not from the average —
and sometimes that means a *bigger* van. Renting daily is flexible and dear; a year's contract is cheaper and binds you;
the cut-price van that can be recalled at two minutes' notice is fine for moving stock between depots and not for the
scheduled round. Getting an extra van takes a morning, so it does not help with this afternoon's rush. And the van
somebody has been fixing in the yard for two years is the one nobody else can drive.

### Where the analogy breaks

- **A van's capacity is its volume; a server's is whichever resource runs out first**, and for AI work that is rarely CPU
  (§5.4).
- **Vans are returned; instances quietly persist.** Drift accumulates because nothing forces replacement (§5.5).

---

## 5. Detailed technical explanation

### 5.1 What you are choosing

| Dimension | Question |
|---|---|
| **Family** | General purpose (`m`), compute-optimised (`c`), memory-optimised (`r`), burstable (`t`), accelerated (`g`, `p`) |
| **Generation** | Newer generations are usually cheaper per unit of work — check before assuming |
| **Processor** | x86 or Graviton (`g` suffix): often better price/performance if your stack rebuilds cleanly |
| **Size** | vCPU and memory scale together within a family; network and EBS bandwidth scale with size too |
| **Storage** | EBS (persistent, network) versus instance store (fast, ephemeral) |

For a typical AI application server — waiting on APIs, holding connections, buffering responses — **memory and network**
matter more than vCPU, and a general-purpose or memory-optimised family is usually right.

Burstable (`t`) instances accrue CPU credits; when they run out, performance collapses in a way that looks like an
application bug. Fine for development, dangerous for anything user-facing with a long tail.

### 5.2 Right-sizing

`[REAL, computed — ILLUSTRATIVE prices]` §7.1 — $4,765 → $4,485/month, 6%.

```text
required = p95_measured × headroom_factor
size     = the smallest instance that fits required vCPU AND required memory
```

Three discipline points: use **p95, not the mean**; apply headroom explicitly and write down the factor; and be willing to
**increase** a size — an undersized workload shows up as latency and errors, not as a cost saving.

Measure both vCPU **and** memory. Memory is what actually kills AI application servers, because response buffers, model
clients and retrieved context all live there.

### 5.3 Purchase options

`[REAL, computed — ILLUSTRATIVE discounts]` §7.2.

| Option | Use for | Avoid when |
|---|---|---|
| On-demand | Variable load, new workloads, anything you may change | Stable baseline you will run all year |
| Savings Plan (1yr) | A baseline you are confident about | You may re-platform within the term |
| Savings Plan (3yr, upfront) | Long-lived, stable, well-understood | Anything under a year old |
| Spot | Batch, embedding jobs, evaluation runs, anything checkpointed | Stateful services, anything a user waits on |

`(1 − 0.05)^24 = 29%` — the survival probability of a 24-hour Spot job at a 5% hourly interruption rate. Design for
interruption: checkpoint, make work idempotent (M8-L12), and use a queue so reclaimed work is retried (L15).

### 5.4 Autoscaling

`[REAL, computed]` §7.3 — 330 seconds, 85,800 requests.

```text
lag = alarm evaluation + launch + boot + application warm-up + health checks
```

Reduce each: alarms on shorter periods with a lower threshold (accepting more false scale-outs — L09 §5.5), pre-baked
AMIs so boot is short, warm pools so instances are already started, and a health check that passes as soon as the
application is genuinely ready (L09 §5.5).

Then accept the floor and add: **headroom** (run at 50–60% of capacity, not 90%), a **queue** to absorb bursts (L15), and
**load shedding** that degrades deliberately rather than collapsing (M7-L13, M8-L15).

Scale on a metric that reflects the bottleneck. For AI workloads that is usually **in-flight requests** or **queue
depth**, not CPU (§5.4).

### 5.5 Immutable infrastructure

`[REAL, computed]` §7.5 — 57% older than 90 days, 55% drifted.

The rule: **instances are replaced, never modified**. Bake an AMI in CI, roll the group, and let nothing survive a
deployment. Consequences worth stating:

- No SSH access needed in normal operation — use Systems Manager Session Manager when you must, and log it.
- Configuration lives in the image and in parameters, not in a change someone made at 3am.
- A rebuilt instance is the recovery path for a compromised one (M10-L14).
- The AMI has a **version**, which belongs in the run fingerprint (M10-L13).

### 5.6 When not to use EC2

EC2 is the baseline, not the default. For most AI applications:

| Need | Better fit |
|---|---|
| Stateless HTTP service | Containers on Fargate (L12) — no OS to patch |
| Event-driven, spiky, short tasks | Lambda (L13) |
| Model hosting you do not want to operate | Bedrock (M12-L01) |
| Custom model serving with GPUs | SageMaker endpoints (M12-L07), or EC2 if you need the control |

Choose EC2 when you need specific instance types, long-running processes, GPU control, or software that cannot be
containerised — and know which of those reasons applies.

### 5.7 Assumptions and limitations

- Prices, discounts, interruption rates, boot timings and the request profile are invented.
- The autoscaling model is a single scale-out step; real policies have cooldowns and step adjustments.
- GPU instances, placement groups, EBS volume types and `t`-family credit mechanics are out of scope.

---

## 6. Worked example — the fleet that was 4% busy and kept falling over

**The situation.** An assistant's API ran on eight instances behind a load balancer. CPU utilisation averaged **4%**. A
cost review recommended halving the fleet. The team resisted, without being able to say why.

**What the measurements showed.**

1. Each request spent **~2.4 seconds waiting** on the model API, with the CPU idle (§7.4).
2. The bottleneck was **memory**: each in-flight request held a buffered response and its retrieved context. At 60
   concurrent requests per instance, memory was at 85% while CPU was at 4%.
3. A second bottleneck was the **outbound connection pool**, capped in the HTTP client's default configuration
   (M2-L12).
4. Autoscaling was configured on **CPU at 70%**, a threshold the fleet would never reach, so it had never scaled at all
   (§5.4).
5. Halving the fleet would have halved the memory headroom and doubled the concurrency per instance.

| # | What was wrong | Fix |
|---|---|---|
| 1 | Sizing judged by CPU | Size by memory and concurrency (§5.4) |
| 2 | Autoscaling on the wrong metric | Scale on in-flight requests or queue depth |
| 3 | Connection pool at defaults | Tune and monitor pool saturation (M2-L12) |
| 4 | No headroom policy | Target 50–60% of measured capacity |
| 5 | Capacity never load-tested | Establish real capacity per instance (M13-L11) |

**The general rule.** **Find which resource runs out first, then size for that. For AI workloads it is almost never
CPU.**

---

## 7. Practical activity

**File:** [`labs/m11/l11_ec2_compute_baseline.py`](../../labs/m11/l11_ec2_compute_baseline.py)

**No AWS account, no network, no third-party dependencies.** Seeded, so the figures below reproduce exactly.

```bash
source .venv/bin/activate
python labs/m11/l11_ec2_compute_baseline.py
```

### 7.2 Expected output

`[EXECUTED]` — 2026-09-17, Python 3.12.3 (pure standard library). Seeded with `random.Random(1111)`; run twice, output
identical.

```text

============================================================================
1. RIGHT-SIZING FROM MEASURED UTILISATION
============================================================================
  headroom factor 1.4x over measured p95

  workload            now         p95 vCPU   p95 GiB   right size     $/mo now  $/mo right
  api servers         2xlarge          1.4       5.2   large             1,682         420
  ingestion workers   4xlarge          9.1      28.0   4xlarge           1,682       1,682
  embedding workers   xlarge           3.8      14.8   2xlarge           1,121       2,243
  admin/batch         xlarge           0.3       1.1   large               280         140
  TOTAL                                                                  4,765       4,485

  right-sizing saves $280/month ($3,364/year), 6%
  Two rows are the interesting ones. 'ingestion workers' at p95 9.1 vCPU does
  not fit a 2xlarge once headroom is applied, so it stays where it is. And
  'embedding workers' is UNDERSIZED: 3.8 x 1.4 = 5.3 vCPU needs a 2xlarge, so
  right-sizing makes it more expensive -- which is why the net saving is only
  6% rather than the 40% a slide would promise. Right-sizing is 'measure, then
  fit', not 'make everything smaller'. Size from p95 plus headroom, never from
  the mean (M13-L11).

============================================================================
2. ON-DEMAND, SAVINGS PLAN, OR SPOT?
============================================================================
  10 instances at $0.384/hour on-demand [ILLUSTRATIVE discounts]

  purchase option                        rate     $/year   saving   commitment
  on-demand                              1.00     33,638       0%   stop any time
  1-year Savings Plan (no upfront)       0.72     24,220      28%   committed for 1 year
  3-year Savings Plan (all upfront)      0.55     18,501      45%   committed for 3 years
  Spot                                   0.32     10,764      68%   can be reclaimed

  Spot saves 68% and can be reclaimed with 2-minute notice.
  At a 5% hourly interruption rate, an instance survives a
  24-hour batch job 29% of the time -- so Spot is for work that
  CHECKPOINTS and resumes (M8-L14), not for a stateful service.
  Savings Plans are a commitment to SPEND, not to specific instances: they
  are safe for a stable baseline and wrong for a workload you may re-platform
  within the term (M11-L12).

============================================================================
3. AUTOSCALING LAG AGAINST A SPIKE
============================================================================
  4 instances x 40 rps = 160 rps; traffic jumps to 420 rps

  stage                                         seconds  cumulative
  alarm evaluates (2 periods of 60 s)               120         120
  instance launches                                  45         165
  OS and agent start                                 40         205
  application and model client warm up               95         300
  health checks pass, traffic arrives                30         330

  shortfall during the lag: 260 rps for 330 s = 85,800 requests queued or rejected
  needed instances: 11; scaling from 4 takes 330 s (5.5 minutes)

  Autoscaling responds in MINUTES. It is a cost control and a slow-growth
  mechanism, not a spike defence. Defend spikes with headroom, a queue
  (M11-L15), or a load shedder that degrades deliberately (M7-L13). Note
  which stage is largest: model-client warm-up, which is an AI-specific cost.

============================================================================
4. FOR AN AI WORKLOAD, WHAT IS ACTUALLY THE BOTTLENECK?
============================================================================
  phase                                ms   share   what it is
  waiting on the model API           2400   87.9%   network + provider time; CPU is idle
  waiting on vector search            180    6.6%   mostly the database's problem
  waiting on object storage            90    3.3%   network
  tokenising and assembling            35    1.3%   real CPU, and small
  JSON parsing and validation          18    0.7%   real CPU, and smaller
  logging                               7    0.3%   real CPU, negligible
  TOTAL                              2730    100%

  CPU-bound work: 60 ms of 2730 ms = 2.2%
  a machine could hold roughly 46x more concurrent requests than CPU
  alone suggests -- if the runtime can wait on many things at once (M2-L13).
  So the sizing question is CONCURRENCY and MEMORY, not vCPU. A fleet sized
  by CPU utilisation will look 2% busy and still fall over on connection
  limits, memory, or provider rate limits (M12-L12).

============================================================================
5. FLEET AGE AND DRIFT
============================================================================
  age since last AMI replacement          instances   with manual changes
  under 30 days                                   8                     0
  30-90 days                                      9                     4
  90-180 days                                    16                    11
  over 180 days                                   7                     7

  instances older than 90 days: 23/40 (57%)
  instances with manual changes (drift): 22/40 (55%)
  An instance that has been running long enough to be patched by hand is an
  instance you cannot reproduce. Replace instances rather than updating them:
  bake an AMI, roll the fleet, and let nothing survive a deployment. Drift is
  what makes 'it works on that box' an outage waiting for a scale-out event
  (M11-L18, M10-L13).

============================================================================
6. WHAT THIS LAB IS AND IS NOT
============================================================================
  REAL: every sizing decision, annual cost, lag total, profile share and drift
  count above is computed from the values in this script.

  ILLUSTRATIVE: instance prices, discount multipliers, the Spot interruption
  rate, boot timings and the request profile are invented. Check current AWS
  pricing and measure your own timings.

  NOT SHOWN: instance families and their trade-offs in detail, GPU instances,
  placement groups, EBS volume types and burstable (T-family) credits.

Done.
```

### 7.3 Reading the result

**Section 1's third row** is the honest part: right-sizing made one workload *more* expensive, and the net saving is 6%.

**Section 2's last two lines** are the rule for Spot: 29% survival over 24 hours means checkpointing, not hoping.

**Section 3's largest stage** is model-client warm-up — an AI-specific cost that generic autoscaling advice ignores.

**Section 4** is the single most useful table in this lesson for sizing an AI service.

---

## 8. Common mistakes and troubleshooting

1. **Sizing from the mean.** §5.2 — use p95 plus a stated headroom factor.
2. **Assuming right-sizing always shrinks.** §7.1 — one workload needed to grow.
3. **Committing to a 3-year plan for a workload you may re-platform.** §5.3.
4. **Spot for stateful services.** §5.3 — 29% survival over a day.
5. **Autoscaling as a spike defence.** §5.4 — 330 seconds of lag.
6. **Scaling on CPU for an AI workload.** §5.4 — the threshold is never reached.
7. **Burstable instances in production.** Credit exhaustion looks like an application bug.
8. **Patching instances in place.** §5.5 — 55% drift.
9. **No load test, so no known capacity per instance.** (M13-L11.)

| Symptom | Likely cause | Fix |
|---|---|---|
| Low CPU, high latency, occasional errors | Memory or connection-pool saturation | Measure both; size by the real bottleneck |
| Autoscaling never triggers | Scaling on CPU for an IO-bound workload | Scale on in-flight requests or queue depth |
| Errors during a traffic spike | Scale-out lag | Headroom, queue, load shedding |
| A rebuilt instance behaves differently | Drift on the old instance | Immutable images; no in-place changes |
| Batch jobs never finish | Spot interruptions with no checkpointing | Checkpoint; idempotent work; retry queue |

---

## 9. Security, privacy, reliability, cost

- **Security.** Immutable instances remove persistent footholds and make rebuilding the standard remediation (M10-L14);
  require IMDSv2 on every launch template (L05).
- **Privacy.** Instance store and EBS snapshots hold data — include them in retention and deletion (M10-L06).
- **Reliability.** Spread the group across AZs (L02); health-check replacement is the baseline recovery mechanism.
- **Cost.** Right-sizing, purchase options and shutting non-production instances outside working hours are the three
  levers, in that order of effort (L06).

---

## 10. Exercises

### Exercise 1 — Beginner (~20 min)

1. Which workload in §7.1 needed a *larger* instance, and why?
2. What is the total autoscaling lag in §7.3, and which stage is largest?
3. What percentage of the request in §7.4 is CPU-bound?
4. What is the survival probability of a 24-hour Spot job at 5% hourly interruption?
5. What share of the fleet in §7.5 has drifted?

### Exercise 2 — Intermediate (~40 min)

1. Run the lab. Change the headroom factor to 2.0 and re-read section 1.
2. Add a memory-optimised size to `SIZES` and see which workloads move.
3. Reduce the warm-up stage in §7.3 to 10 s and recompute the lost requests.
4. Change the profile in §7.4 to a local model with 400 ms of GPU time and re-read the conclusion.
5. Decide the purchase option for each workload in §7.1, with a reason.

### Exercise 3 — Challenge (~60 min)

1. Measure a real service's p95 CPU, memory and in-flight concurrency, and right-size it.
2. Load-test to find the actual capacity per instance and the resource that saturates first (M13-L11).
3. Design an autoscaling policy on in-flight requests, with the headroom you can justify.
4. Build an immutable deployment: bake an AMI in CI, roll the group, verify nothing is modified in place (L18).
5. Compute the break-even point between a Savings Plan and moving the workload to Fargate (L12).

---

## 11. Quiz

*(Answers: [`answer-keys/module-11-answers.md`](../../answer-keys/module-11-answers.md#m11-l11).)*

**Q1.** What should an instance be sized from?

- A. Measured p95 utilisation plus a stated headroom factor
- B. The instance type used by a comparable team
- C. The mean utilisation over the last month
- D. The peak utilisation ever observed

**Q2.** In §7.1, what happened to the embedding workers?

- A. They were right-sized to a smaller instance
- B. They were found to be undersized and needed a larger instance
- C. They were unchanged because memory fit exactly
- D. They were removed from the fleet

**Q3.** A Savings Plan commits you to —

- A. specific instance types for the term
- B. a minimum number of running instances
- C. a level of spend per hour for the term
- D. a single Availability Zone

**Q4.** At a 5% hourly interruption rate, roughly how often does a 24-hour Spot job survive?

- A. 95%
- B. 68%
- C. 50%
- D. 29%

**Q5.** What is Spot appropriate for?

- A. Work that checkpoints and can resume
- B. Stateful services with persistent sessions
- C. Any workload, with a longer health-check threshold
- D. Latency-sensitive user-facing requests

**Q6.** In §7.3, how long was the total autoscaling lag?

- A. 120 seconds
- B. 45 seconds
- C. 330 seconds
- D. 95 seconds

**Q7.** Why is autoscaling not a spike defence?

- A. Scaling policies have a maximum instance count
- B. Alarms cannot evaluate faster than five minutes
- C. Health checks reject new instances during high load
- D. It responds in minutes, while a spike arrives in seconds

**Q8.** What should an AI application server usually scale on?

- A. CPU utilisation
- B. In-flight requests or queue depth
- C. Network throughput
- D. Disk I/O

**Q9.** In §7.4, what proportion of the request was CPU-bound?

- A. 87.9%
- B. 2.2%
- C. 6.6%
- D. 46%

**Q10.** Which resource most often saturates first on an AI application server?

- A. vCPU
- B. Local disk
- C. Memory and connections
- D. EBS throughput

**Q11.** Why replace instances rather than patch them?

- A. Patching requires downtime that replacement avoids
- B. AWS does not support in-place package updates
- C. Replacement is cheaper than running a patch tool
- D. A hand-modified instance cannot be reproduced, and scale-out launches the image

**Q12.** What is the risk of burstable (`t`-family) instances in production?

- A. CPU credit exhaustion causes a performance collapse that resembles a bug
- B. They are unavailable in some Availability Zones
- C. They cannot join an Auto Scaling group
- D. They do not support EBS-optimised throughput

**Q13.** *(Written, rubric-graded.)* In under 150 words: a cost review says your AI API fleet averages 5% CPU and
should be halved. Give your response and the measurements you would present.

---

## 12. Revision notes

- **Right-size from p95 × headroom**: in the lab, two shrank, one stayed, **one grew** — net **6%**, not 40%.
- **Purchase options**: on-demand **$33,638/yr** → 1-yr plan **−28%** → 3-yr upfront **−45%** → Spot **−68%**, reclaimable.
  Spot survives 24 h only **29%** of the time at 5%/hour.
- **Autoscaling lag = 330 s** (alarm 120 + launch 45 + boot 40 + **warm-up 95** + health 30) → **85,800** requests lost.
  Use headroom, queues and load shedding for spikes.
- **AI requests are 2.2% CPU**: size by **memory and concurrency**; scale on in-flight requests, not CPU.
- **Immutable instances**: **57%** older than 90 days and **55%** drifted in the lab — replace, never patch.
- **EC2 is the baseline, not the default**: Fargate, Lambda and managed model services are usually the better fit.

---

## 13. Completion checklist

- [ ] I size from measured p95 for both vCPU and memory, with a stated headroom factor.
- [ ] I know which resource saturates first for my workload, from a load test.
- [ ] Purchase options match each workload's commitment and interruption tolerance.
- [ ] Autoscaling uses a metric that reflects the real bottleneck, and I know my lag.
- [ ] Instances are replaced from versioned images, never modified in place.
- [ ] I scored at least 10/13 on the quiz.

---

## 14. References

- Amazon EC2 User Guide — instance families and sizes, Auto Scaling groups, warm pools, launch templates `[STABLE]`
- AWS purchase options — Savings Plans (spend commitment) and Spot (interruption with short notice) `[STABLE — check current discounts]`
- M13-L10 (batching and concurrency) and M13-L11 (latency percentiles and load testing) `[STABLE]`
- M11-L12 (containers — the usual better fit) and M11-L18 (immutable deployment pipelines) `[STABLE]`
- M8-L14 (checkpointing — what makes Spot safe) and M8-L15 (load shedding and limits) `[STABLE]`

---

## 15. Next lesson

→ [M11-L12 — Containers on AWS: ECR, ECS and Fargate](M11-L12-containers-ecr-ecs-fargate.md) takes the same workload and
removes the operating system from your responsibilities — changing what you patch, how you deploy, and what a task role
means for an agent's permissions.
