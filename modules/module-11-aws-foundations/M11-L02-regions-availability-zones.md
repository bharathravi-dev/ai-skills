# M11-L02 — Regions, Availability Zones and Placement Decisions

| | |
|---|---|
| **Lesson ID** | M11-L02 |
| **Difficulty** | 1 (Beginner) |
| **Estimated study time** | 1.25 hours |
| **Prerequisites** | [M11-L01](M11-L01-cloud-shared-responsibility.md) |

---

## 1. Learning objectives

1. **Compute** the latency floor distance imposes, and multiply it by the number of sequential round trips a design makes.
2. **Calculate** availability for single-AZ, multi-AZ and multi-region designs, and identify the dominant failure term.
3. **Apply** data residency as a filter before any other criterion.
4. **Price** traffic that crosses an AZ, a region or the internet boundary.
5. **Make** a placement decision as gates first, then a stated trade-off.

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **Region** | A geographic area containing multiple isolated data-centre groups; resources and most service APIs are region-scoped. |
| **Availability Zone (AZ)** | One or more discrete data centres within a region, with independent power, cooling and networking, connected to the other AZs by low-latency links. |
| **Multi-AZ** | A design that keeps working when one AZ is unavailable. |
| **Data residency** | A requirement that data be stored and processed in a stated geography. |
| **Data transfer charge** | The per-GB price of moving data across an AZ, region or internet boundary. |
| **Latency floor** | The minimum round-trip time set by distance and the speed of light in fibre. |
| **Global service** | A service whose control plane is not region-scoped (for example IAM). |
| **Region parity** | Whether a given service, model or feature exists in a given region — it often does not. |

---

## 3. Plain-language explanation

### 3.1 Distance is a cost you cannot engineer away

§7.1 computes the round-trip floor from London: **0.3 ms** to London, **7.0 ms** to Ireland, **9.6 ms** to Frankfurt,
**88.5 ms** to Virginia, **254.8 ms** to Sydney. A RAG request making six sequential round trips pays it six times:
**1.8 ms** versus **531 ms**. No amount of tuning gets under it — you move closer, or you make fewer round trips.

### 3.2 The second AZ is the big win; the second region usually is not

§7.2: infrastructure unavailability falls from **1,199.8 ppm** (single AZ) to **201.0 ppm** with two AZs — and only to
**200.0** with three, because whole-region failure now dominates. Two regions reach **0.04 ppm**.

Then the honest column: your own software contributes **2,000 ppm** by itself. End to end, two AZs give **99.7799%** and
two regions **99.8000%**. The multi-region project buys **0.02 percentage points** while the application is the dominant
term.

### 3.3 Residency filters first

§7.3: "data stays in Europe" leaves **3 of 5** regions. "Data stays in the UK" leaves **1**. And the filter teams forget —
"Europe *and* the AI service exists here" — is the one that breaks plans late, because service and model availability
varies by region.

### 3.4 Boundaries have a price per gigabyte

§7.4: 8,000 GB/month costs **$0** within an AZ, **$960/year** across AZs, **$1,920/year** across regions and
**$8,640/year** out to the internet — for identical traffic, decided only by placement.

### 3.5 The decision is gates, then a trade-off

§7.5: one of four candidates fails the residency gate. Among the eligible three, the lowest-latency region and the
lowest-cost region differ by **6.8 ms per round trip — 40.8 ms per request** at six round trips. That is a trade-off two
people can discuss. "Everyone uses us-east-1" is not.

---

## 4. Analogy

**Choosing where to put a warehouse.** Distance to customers sets a delivery time you cannot beat with better vans. Two
warehouses in one city survive a fire; two cities survive a flood, at a cost. Some goods legally cannot leave the country,
which rules out sites before you compare rents. And moving stock between sites costs money every time, forever.

### Where the analogy breaks

- **A warehouse's inventory is where you put it; cloud data replicates by default in some services and not others.**
  "Where is it?" is a per-service question (§5.4).
- **You can build a warehouse anywhere; you cannot conjure a service into a region.** Region parity is a hard constraint
  set by the provider (§5.3).

---

## 5. Detailed technical explanation

### 5.1 What a region and an AZ actually are

- A **region** is a named geographic area (`eu-west-2`, `us-east-1`) containing multiple **Availability Zones**.
- An **AZ** is one or more discrete data centres with independent power, cooling and physical security, meaningfully
  separated from the other AZs in the region, and connected to them by high-bandwidth, low-latency links `[STABLE]`.
- Most services are **region-scoped**: a bucket, a VPC, a queue belongs to one region. Some are **global**: IAM identities,
  Route 53 hosted zones, CloudFront distributions `[STABLE]`.
- AZ names are **per-account aliases**: your `eu-west-2a` is not necessarily another account's `eu-west-2a`. Use AZ IDs
  when the physical identity matters `[STABLE]`.

Two independent failure domains follow: **AZ failure** (power, network, a data centre event) and **region failure** (rare,
and usually a control-plane or dependency event rather than a physical one).

### 5.2 Latency arithmetic

`[REAL, computed]` §7.1. Light travels roughly **200 km per millisecond** in glass, and real routes run about **1.5×** the
great-circle distance. So:

```text
RTT_floor_ms ≈ 2 × distance_km × 1.5 / 200
```

The multiplier that matters is **your design's sequential round trips**. A RAG request typically makes several: embed the
query, search the index, rerank, call the model, call a tool, write a log. Six sequential trips to a region 5,900 km away
cost **531 ms** before any work is done.

Two consequences: **co-locate the chatty components** (model, index, application) in one region; and reduce sequential
trips by batching and parallelising (M13-L10). Cross-region calls belong on paths that happen once, not per request.

### 5.3 Availability arithmetic

`[REAL, computed — ILLUSTRATIVE probabilities]` §7.2.

```text
single AZ          : 1 − (1 − p_az)(1 − p_region)
two AZs, one region: 1 − (1 − p_az²)(1 − p_region)
two regions        : (p_az² + p_region)²
end to end         : combine with your own application failure rate
```

| Design | Infra ppm | With app (2,000 ppm) | Availability |
|---|---|---|---|
| Single AZ | 1,199.80 | 3,197.40 | 99.6803% |
| Two AZs | 201.00 | 2,200.60 | 99.7799% |
| Three AZs | 200.00 | 2,199.60 | 99.7800% |
| Two regions | 0.04 | 2,000.04 | 99.8000% |

Read the third column, not the second. **The dominant term wins**, and for most teams the dominant term is their own
software — deploys, dependency failures, bad configuration, unhandled errors. Multi-region is a large, expensive project
that changes the end-to-end number by a rounding error until the application term is smaller than the infrastructure one.

The order of investment that follows: multi-AZ (cheap, large gain) → application reliability (large gain, ongoing work) →
multi-region (expensive, only when the application is already the smaller term, or when residency or regulation demands
it).

### 5.4 Residency and region parity

`[REAL, filtered]` §7.3 — 5 → 3 → 1 regions under successive constraints.

Residency is an **L06 data question**, answered before architecture: which data classes, stored where, processed where,
with what transfers. Two practical traps:

- **Replication you did not ask for.** Some services replicate or store metadata outside the region by default; check per
  service rather than assuming.
- **Region parity.** Not every service, instance type, model or feature exists in every region, and new capabilities often
  arrive in a handful of regions first. For AI work this is the common blocker: the model you designed around may not be
  available in the region your data must stay in (M12-L01).

Check parity **before** the design is committed, and record the check with a date — it changes.

### 5.5 Data transfer costs

`[REAL, computed — ILLUSTRATIVE rates]` §7.4 — $0 / $960 / $1,920 / $8,640 per year for the same 8,000 GB/month.

The general shape `[STABLE]`: traffic within an AZ over private addressing is free or cheapest; crossing AZs costs;
crossing regions costs more; leaving for the internet costs most. Exact rates change and vary by direction and service —
check current pricing.

Design consequences: keep chatty pairs in one AZ *within* a multi-AZ deployment (replicate per AZ rather than calling
across); prefer VPC endpoints to NAT gateways for AWS-service traffic (L08); and be aware that a multi-AZ database's
synchronous replication is cross-AZ traffic by design — that is the price of the availability you bought.

### 5.6 Making the decision

`[REAL, scored]` §7.5.

```text
1. GATES  (yes/no, evidenced)
   [ ] residency permits this region for these data classes
   [ ] every service, model and feature we need exists here
   [ ] our compliance and contractual commitments allow it
2. COMPARE (only among regions that pass every gate)
   latency to users (RTT floor × sequential trips)
   cost index (compute, storage, transfer at our volume)
   operational familiarity and support coverage
3. RECORD the choice, the runner-up, and what would change it.
```

This is M10-L11's gates-before-scores rule applied to geography. The decision is also **hard to reverse**: moving a
production system between regions is a migration, not a configuration change (M10-L14 §5.4).

### 5.7 Assumptions and limitations

- Distances are approximate; failure probabilities and per-GB rates are invented.
- The availability model assumes independent failures. Correlated failures — a shared control plane, a global dependency,
  one deployment pipeline pushing the same bug everywhere — are the ones that actually cause multi-AZ outages.
- Edge caching, Local Zones and Outposts change the latency picture and are out of scope.

---

## 6. Worked example — the multi-region project that bought nothing

**The situation.** After a four-hour outage, a team committed to multi-region active-active for an assistant product. The
project was scoped at two quarters.

**What the numbers said, once someone computed them.**

1. The outage had been caused by **a bad deploy**, not an AZ or region failure. It would have been replicated to both
   regions in minutes (§5.3 — correlated failure).
2. Measured application unavailability was about **2,000 ppm**; infrastructure contributed about **200 ppm** in the
   existing two-AZ design (§7.2).
3. The proposed design would have taken end-to-end availability from **99.78%** to **99.80%** — **0.02 points** (§7.2).
4. The AI model they depended on was **not available** in the second region at the time (§5.4).
5. Cross-region synchronous replication would have added latency to every write, and cross-region transfer to the monthly
   bill (§5.5).

**What they did instead.** Canary deploys and automated rollback (M10-L14), a second AZ for the one component that lacked
it, and a quality monitor with a measured false-alarm rate. Measured application unavailability fell by more than the
multi-region project would have delivered, in three weeks.

| # | Assumption | What the arithmetic said |
|---|---|---|
| 1 | The outage was an infrastructure failure | It was a deploy, which replicates |
| 2 | Multi-region improves availability | +0.02 points against a 2,000 ppm app term |
| 3 | Regions are interchangeable | The model was not available in region two |
| 4 | Replication is free | Latency on every write, plus transfer charges |
| 5 | Big project, big gain | The cheap fixes were bigger |

**The general rule.** **Compute the dominant failure term before you buy redundancy for a different one.**

---

## 7. Practical activity

**File:** [`labs/m11/l02_regions_availability_zones.py`](../../labs/m11/l02_regions_availability_zones.py)

**No AWS account, no network, no third-party dependencies.** Fully deterministic.

```bash
source .venv/bin/activate
python labs/m11/l02_regions_availability_zones.py
```

### 7.2 Expected output

`[EXECUTED]` — 2026-09-16, Python 3.12.3 (pure standard library). Run twice; output identical.

```text

============================================================================
1. THE LATENCY FLOOR IS PHYSICS, NOT ENGINEERING
============================================================================
  user in London; round-trip floor = 2 x distance x 1.5 / 200 km per ms

  region                            km   RTT floor    1 call   6 sequential calls
  eu-west-2 (London)                20       0.3 ms     0.3 ms               1.8 ms
  eu-west-1 (Ireland)              470       7.0 ms     7.0 ms              42.3 ms
  eu-central-1 (Frankfurt)         640       9.6 ms     9.6 ms              57.6 ms
  us-east-1 (N. Virginia)        5,900      88.5 ms    88.5 ms             531.0 ms
  ap-southeast-2 (Sydney)       16,990     254.8 ms   254.8 ms            1529.1 ms

  a RAG request that makes 6 sequential round trips (embed, search, rerank,
  generate, tool call, log) pays the floor SIX times: 1.8 ms in London vs 531 ms from Virginia.
  This is before any processing. You cannot optimise your way under it; you
  can only move closer or make fewer round trips (M13-L10).

============================================================================
2. AVAILABILITY: ONE AZ, TWO AZs, TWO REGIONS
============================================================================
  unavailability shown in ppm (parts per million of the period)

  design                           infra ppm   your app ppm   total ppm   availability
  single AZ                         1,199.80          2,000    3,197.40      99.6803%
  two AZs, one region                 201.00          2,000    2,200.60      99.7799%
  three AZs, one region               200.00          2,000    2,199.60      99.7800%
  two regions, active-active            0.04          2,000    2,000.04      99.8000%

  Two lessons. First, the second AZ is the biggest single improvement and the
  cheapest: infra unavailability falls from 1,200 ppm to 201 ppm.
  Second, your own software contributes 2,000 ppm on its own, so going from two
  AZs to two regions moves the end-to-end number by almost nothing. Spend the
  effort on the dominant term (M13-L11).

============================================================================
3. WHICH REGIONS SURVIVE THE CONSTRAINT?
============================================================================
  none                            5/5 regions: eu-west-2, eu-west-1, eu-central-1, us-east-1, ap-southeast-2
  data stays in Europe            3/5 regions: eu-west-2, eu-west-1, eu-central-1
  data stays in the UK            1/5 regions: eu-west-2
  Europe + the AI service exists  3/5 regions: eu-west-2, eu-west-1, eu-central-1

  Residency is a filter applied BEFORE latency and cost, not a tie-breaker
  after them (M10-L06). And the filter that surprises teams is the last one:
  not every service, model or feature exists in every region (M12-L01).

============================================================================
4. WHAT DOES CROSSING A BOUNDARY COST?
============================================================================
  8,000 GB/month of traffic between two components

  placement                          USD/GB    USD/month    USD/year
  within one AZ (private IP)           0.00            0           0
  between AZs in a region              0.01           80         960
  between regions                      0.02          160       1,920
  out to the internet                  0.09          720       8,640

  the same traffic costs $0 or $8,640/year depending only on where the two ends sit.
  Chatty services split across AZs for no reason are a recurring line item;
  so is a NAT gateway carrying traffic that could use a VPC endpoint (M11-L08).

============================================================================
5. A PLACEMENT DECISION, SCORED
============================================================================
  hard requirements: data must stay in Europe; the AI service must exist in region

  region                         gates       RTT   cost idx   ops   verdict
  eu-west-2 (London)              pass     0.3 ms       1.08     4   eligible
  eu-west-1 (Ireland)             pass     7.1 ms       1.00     5   eligible
  eu-central-1 (Frankfurt)        pass     9.6 ms       1.04     3   eligible
  us-east-1 (N. Virginia)         FAIL    88.5 ms       0.95     5   excluded by residency

  eligible: 3/4
  lowest latency among eligible : eu-west-2 (London) (0.3 ms)
  lowest cost among eligible    : eu-west-1 (Ireland) (index 1.00)
  latency difference between them: 6.8 ms per round trip, x6 round trips = 40.8 ms per request

  The honest form of this decision: gates first (residency, service
  availability), then a trade-off between two numbers you can both state.
  'Everyone uses us-east-1' is not one of the inputs (M10-L11).

============================================================================
6. WHAT THIS LAB IS AND IS NOT
============================================================================
  REAL: every latency floor, availability figure, filter result, transfer
  cost and comparison above is computed from the values in this script.

  ILLUSTRATIVE: distances are approximate, failure probabilities are invented,
  and the per-GB rates are made up. Check current AWS pricing and the region
  table for the services you use -- both change.

  NOT SHOWN: edge caching and CDNs, Local Zones and Outposts, cross-region
  replication mechanics, and legal analysis of residency (M10-L16).

Done.

```

### 7.3 Reading the result

**Section 1's last column is the one to quote in design reviews.** One round trip to Virginia is tolerable; six is not.

**Section 2's "total ppm" column** is why most multi-region proposals do not survive arithmetic.

**Section 3's last filter** — service availability within the permitted geography — is the constraint that arrives late and
hurts most (M12-L01).

**Section 5 is M10-L11's gates-before-scores rule** applied to a map.

---

## 8. Common mistakes and troubleshooting

1. **Choosing a region by convention.** §5.6 — gates, then a stated trade-off.
2. **Ignoring sequential round trips.** §5.2 — the floor multiplies by the number of hops.
3. **Buying multi-region while the application dominates.** §5.3 — compute the terms first.
4. **Assuming independent failures.** A shared deploy pipeline is a correlated failure across every region.
5. **Checking service availability after the design.** §5.4 — check parity first, with a date.
6. **Forgetting cross-AZ transfer charges.** §5.5 — chatty pairs split across AZs cost money forever.
7. **Treating region choice as reversible.** It is a migration (M10-L14).
8. **Assuming data stays where you put it.** Per-service replication and metadata behaviour vary.

| Symptom | Likely cause | Fix |
|---|---|---|
| p95 latency has a large irreducible floor | Users far from the region, or too many sequential hops | Move closer; batch and parallelise (M13-L10) |
| Availability unchanged after a redundancy project | Wrong dominant term | Measure app vs infra unavailability separately |
| Unexplained monthly data-transfer line item | Cross-AZ or NAT traffic | Co-locate chatty components; use VPC endpoints (L08) |
| A service is missing in the chosen region | Parity not checked | Verify per service and per model before committing (M12-L01) |
| Compliance blocks a launch late | Residency treated as a tie-breaker | Apply residency as a gate first (M10-L06) |

---

## 9. Security, privacy, reliability, cost

- **Security.** Region choice determines which regulatory regime and which AZ-level blast radius apply; it is an input to
  the threat model (M10-L10).
- **Privacy.** Residency and transfer are data-protection questions with engineering consequences — answer them before
  the design (M10-L06).
- **Reliability.** Multi-AZ is the cheapest large gain available; buy it first, then fix your own software.
- **Cost.** Placement decides a recurring transfer bill that never appears in a design document unless someone computes it.

---

## 10. Exercises

### Exercise 1 — Beginner (~20 min)

1. What is the RTT floor from London to Frankfurt, and what does it cost over six sequential calls?
2. What is the infrastructure unavailability of a single-AZ design in §7.2, in ppm?
3. Which term dominates end-to-end availability there?
4. How many regions survive "data stays in the UK"?
5. What does 8,000 GB/month cost across AZs versus out to the internet?

### Exercise 2 — Intermediate (~40 min)

1. Run the lab. Change `APP_FAIL` to 0.0001 and see when multi-region starts to matter.
2. Add your own users' city and compute the floor to three candidate regions.
3. Add a fourth constraint — "the model we need exists" — and see how the eligible set changes.
4. Recompute §7.4 at your real monthly transfer volume.
5. Write the placement decision record for a system you work on, gates first.

### Exercise 3 — Challenge (~60 min)

1. Measure your application's actual unavailability over the last quarter and compare it with the infrastructure term.
2. Count the sequential round trips in one real request path and estimate the floor you are paying.
3. Model the cost of moving one chatty component into the same AZ as its peer.
4. Check region parity for every service and model your design depends on, and record the date.
5. Write the conditions under which multi-region would become the right investment for you, with numbers.

---

## 11. Quiz

*(Answers: [`answer-keys/module-11-answers.md`](../../answer-keys/module-11-answers.md#m11-l02).)*

**Q1.** What is an Availability Zone?

- A. A physical building within a data centre campus
- B. A logical grouping of accounts within an organisation
- C. One or more discrete data centres with independent power, cooling and networking
- D. A replicated copy of a region used for disaster recovery

**Q2.** In §7.1, what is the round-trip floor from London to us-east-1?

- A. 88.5 ms
- B. 9.6 ms
- C. 254.8 ms
- D. 7.0 ms

**Q3.** Why does a six-hop design suffer disproportionately from distance?

- A. Each hop adds processing time proportional to distance
- B. Packet loss compounds across sequential requests
- C. Bandwidth falls with distance, slowing each transfer
- D. The latency floor is paid once per sequential round trip

**Q4.** In §7.2, what did moving from two AZs to three achieve?

- A. It halved infrastructure unavailability
- B. Almost nothing, because region failure now dominates
- C. It eliminated the application failure term
- D. It reduced cross-AZ transfer costs

**Q5.** Why did two regions barely change end-to-end availability?

- A. Regions fail together more often than expected
- B. Cross-region replication introduces its own failures
- C. The AI service was unavailable in the second region
- D. The application's own failure rate dominated the total

**Q6.** When should data residency be applied in a placement decision?

- A. As a tie-breaker between similarly priced regions
- B. After latency, since users notice latency first
- C. As a gate, before latency or cost are considered
- D. Only when a regulator has explicitly asked

**Q7.** Which constraint most often surprises teams late in a design?

- A. That the service or model does not exist in the required region
- B. That AZ names differ between accounts
- C. That IAM is a global service
- D. That regions have different numbers of AZs

**Q8.** In §7.4, how much did 8,000 GB/month cost per year across AZs?

- A. $0
- B. $960
- C. $1,920
- D. $8,640

**Q9.** Which pair of components should ideally sit in the same AZ?

- A. Two components exchanging large volumes of traffic per request
- B. A database and its synchronous standby replica
- C. A load balancer and its health-check target group
- D. An application and its off-site backup store

**Q10.** What is the recommended order of investment for availability?

- A. Multi-region, then multi-AZ, then application reliability
- B. Application reliability, then multi-region, then multi-AZ
- C. Multi-AZ and multi-region together, then the application
- D. Multi-AZ, then application reliability, then multi-region

**Q11.** Why is a bad deploy a poor argument for multi-region?

- A. Deploys are not covered by availability commitments
- B. The same bug replicates to every region
- C. Multi-region deployments take longer to roll out
- D. Regional isolation only protects against network faults

**Q12.** Why should a region choice be recorded with its runner-up?

- A. To satisfy the inventory's required fields
- B. Because providers require a documented region strategy
- C. Because moving later is a migration, and the reasoning must be reviewable
- D. To allow automatic failover to the runner-up

**Q13.** *(Written, rubric-graded.)* In under 150 words: your team wants to deploy an AI assistant for UK customers and
proposes us-east-1 "because everything is there". Give your response, with the questions you would answer first.

---

## 12. Revision notes

- **Latency floor** ≈ `2 × km × 1.5 / 200` ms: **0.3 / 7.0 / 9.6 / 88.5 / 254.8 ms** from London — and it multiplies by
  sequential round trips (**531 ms** to Virginia at six hops).
- **Availability**: single AZ **1,199.8 ppm** infra → two AZs **201.0** → three AZs **200.0** → two regions **0.04**.
- **The dominant term wins**: with a 2,000 ppm application, two AZs give **99.7799%** and two regions **99.8000%**.
- **Residency is a gate**: Europe → **3/5** regions, UK → **1/5**; and check **region parity** for every service and model.
- **Transfer costs** for the same 8,000 GB/month: **$0 / $960 / $1,920 / $8,640** per year by placement alone.
- **Decide with gates, then a stated trade-off**; record the runner-up, because the choice is a migration to reverse.

---

## 13. Completion checklist

- [ ] I can compute the latency floor for my users and multiply it by my design's sequential round trips.
- [ ] I know which failure term dominates my system's availability.
- [ ] I apply residency and region parity as gates, with a dated check.
- [ ] I know what my cross-boundary traffic costs per year.
- [ ] My region choice is recorded with its runner-up and the conditions that would change it.
- [ ] I scored at least 10/13 on the quiz.

---

## 14. References

- AWS Global Infrastructure — regions, Availability Zones, AZ IDs — <https://aws.amazon.com/about-aws/global-infrastructure/> `[STABLE]`
- AWS service and Region availability table; AWS data transfer pricing — both change; check at design time `[UNVERIFIED — check current]`
- M10-L06 (residency as a data question) and M10-L14 (region choice as a one-way door) `[STABLE]`
- M13-L10 (batching and concurrency — reducing sequential round trips) and M13-L11 (latency percentiles) `[STABLE]`
- M12-L01 (Bedrock model availability by region — the parity constraint in practice) `[STABLE]`

---

## 15. Next lesson

→ [M11-L03 — Account Setup, Root User Protection and MFA](M11-L03-account-root-mfa.md) moves from where things run to who
can create them: the account boundary, the root user, and the handful of settings that prevent the most expensive
beginner mistakes.
