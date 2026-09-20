# M12-L01 — Amazon Bedrock: concepts, model access, region reality

| | |
|---|---|
| **Lesson ID** | M12-L01 |
| **Difficulty** | 2 (Intermediate) |
| **Estimated study time** | 2.0 hours |
| **Prerequisites** | [M11-L04](../module-11-aws-foundations/M11-L04-iam-policies-roles.md), [M11-L02](../module-11-aws-foundations/M11-L02-regions-availability-zones.md), [M4-L18](../module-04-genai-llm-internals/M4-L18-hosted-vs-local.md) |

> **Bedrock's model catalogue, regional availability and pricing change frequently.** Every model name and price in this
> lesson is invented. What transfers is the *shape* of the decisions and the order to make them in. Check the console and
> the pricing page, and record the date you checked.

---

## 1. Learning objectives

1. **Name** the three conditions that must all hold before an invoke call succeeds, and the distinct error each produces.
2. **Apply region parity as a gate** before a prototype, not after it.
3. **Compute** the break-even between on-demand and provisioned throughput, and say what else provisioned buys.
4. **Restate** the shared responsibility split for a managed model service.
5. **Answer** the nine questions a model choice must settle — only one of which is about quality.

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **Amazon Bedrock** | A managed service exposing several providers' foundation models behind one AWS API. |
| **Model access** | Per-account permission to use a particular model, requested in the console. |
| **Model id / ARN** | The identifier you invoke and the ARN your IAM policy must allow. |
| **On-demand** | Pay per token, shared capacity, subject to account quotas. |
| **Provisioned throughput** | Reserved capacity billed per hour, giving predictable throughput. |
| **Region parity** | Whether a given model exists in a given region — it often does not. |
| **Inference profile** | An identifier that can route inference across regions, where offered. |
| **Quota** | A limit on requests or tokens per minute, per account and per model. |

---

## 3. Plain-language explanation

### 3.1 Three conditions, three different errors

§7.1: a call succeeds only when the model **exists in the region**, the **account has been granted access**, and the
**IAM policy allows invoke on that model's ARN**. Each fails differently, and "access denied" can mean any of the three.
Knowing which to check saves hours.

### 3.2 Parity is a gate, and it closes late

§7.2: with no constraint, 12 model/region pairs are usable. "Data must stay in Europe" leaves **6**. "Europe plus the
model we designed around" leaves **2**. "Europe plus the newest preview model" leaves **zero** — and that last row is
what ends projects, because the prototype was built on it.

### 3.3 Provisioned throughput buys predictability as well as price

§7.3: at a 2,400-in/400-out profile, a request costs **$0.0132** on demand. Against **$17,520/month** for one provisioned
unit, the break-even is about **44,000 requests/day**. Below that, on-demand is cheaper; above it, provisioned.

Two things the table hides: provisioned capacity is not subject to a shared pool's throttling (L12), which can matter more
than the price; and it is a **commitment** — if you halve your context length next month, the on-demand line falls and the
provisioned one does not.

### 3.4 The service removes operations, not engineering

§7.4: the service owns **3 of 12** concerns — running the model, its weights, its regional footprint. You own the other
**9**: which model, what you send it, the prompt, output validation, guardrails, IAM, retries, evaluation and cost.

### 3.5 One question in nine is about quality

§7.5 lists the nine questions a model choice must answer. Exactly **one** is "is it good enough on our tasks". The rest
are availability, access, cost, latency, quotas, version stability, data handling and fallback — and those are what sink
projects.

---

## 4. Analogy

**Hiring a specialist contractor through an agency.** The agency handles recruitment, payroll, cover when someone is ill —
real work you no longer do. It does not decide what you ask them to build, what information you hand over, whether the
work is any good, or what you do when the agency has nobody available on Tuesday. And the specialist you interviewed may
not be available in your city.

### Where the analogy breaks

- **An agency's roster changes slowly; a model catalogue changes monthly**, so parity checks expire (§5.2).
- **A contractor tells you when they cannot do something; a model answers anyway**, which is why output validation stays
  yours (§5.4, M5-L07).

---

## 5. Detailed technical explanation

### 5.1 What Bedrock is

A managed API in front of foundation models from several providers, with a common invocation surface (L02), IAM-based
authorisation, CloudTrail logging, VPC endpoints (M11-L08), KMS integration (M11-L17) and optional features — Knowledge
Bases (L04), Agents (L05), Guardrails (L06).

The engineering value is that a model call becomes an ordinary AWS API call: the same IAM, the same networking, the same
audit trail as every other service in Module 11. The engineering cost is that everything specific to *using* a model well
remains yours.

### 5.2 Access, region and permission

`[REAL, computed]` §7.1, §7.2.

| Condition | How it fails | Where to fix it |
|---|---|---|
| Model exists in this region | The model id is not recognised, or is absent from the list | Change region, or choose an available model |
| Account has access | An access/authorisation error mentioning model access | Request access for the account (per account, per model) |
| IAM allows invoke on the ARN | `AccessDeniedException` on the action | Add `bedrock:InvokeModel` for the model ARN (L08) |

Practical discipline:

- **Check parity first**, before the prototype, with the *exact* model you intend to ship. Record the date.
- **Request access in every account** you will deploy to — it is not inherited from the management account.
- **Pin the model id** in configuration and in the run fingerprint (M10-L13), so a result can be reproduced.
- **Re-check before committing**, because availability expands and a six-month-old answer is not an answer.

Where offered, **cross-region inference profiles** can route requests across regions to improve availability and
throughput. Read what that means for residency before enabling it — it may move data across a boundary you promised it
would not cross (M10-L06, M11-L02).

### 5.3 On-demand and provisioned throughput

`[REAL, computed — ILLUSTRATIVE prices]` §7.3 — break-even around 44,000 requests/day.

```text
on-demand monthly  = (in_tokens × in_rate + out_tokens × out_rate) × requests/day × 30
provisioned monthly = hourly_rate × 730 × units
```

| Choose | When |
|---|---|
| **On-demand** | Variable or unknown traffic, development, anything you may re-shape |
| **Provisioned** | Sustained high volume, or a need for throughput that does not compete with a shared pool |

The second column of the provisioned case is the one to weigh: at high volume on-demand, **throttling** becomes a design
constraint and the mitigation is retries with backoff, request shaping and sometimes a queue (L12, M11-L15). Provisioned
capacity converts that variable into a fixed cost.

### 5.4 The responsibility split

`[REAL, classified]` §7.4 — 3 service, 9 yours.

The nine that stay yours map exactly onto earlier modules: prompt design and versioning (M5-L01, M5-L12), structured
output and repair (M5-L06, M5-L07), retrieval (Module 7), agent loops and limits (Module 8), guardrails and threat model
(M10-L10, L06), evaluation gates (M10-L12), audit records (M10-L13), IAM (L08), and cost (L14).

Restating M11-L01: a managed service removes work, never accountability.

### 5.5 Choosing a model

`[REAL, enumerated]` §7.5 — nine questions, one about quality.

The order to answer them in:

```text
1. gates    region parity, access, residency, data handling  -> eliminates most candidates
2. measure  quality on YOUR evaluation set, per slice        (M10-L11, M10-L12)
3. measure  p95 latency at YOUR context size                 (M13-L11)
4. compute  cost per request at YOUR token profile           (L14)
5. check    quotas, throttling behaviour, version pinning    (L12, M10-L13)
6. design   fallback when unavailable or throttled           (M13-L08)
7. record   the choice, the runner-up, and the re-check date (M10-L11)
```

This is M10-L11's gates-before-scores rule applied to a model. Note that steps 2 and 3 need real calls, which needs steps
1 to be settled — another reason parity comes first.

### 5.6 What this means for the rest of the module

| Lesson | Builds on this by |
|---|---|
| L02 | The invocation surface itself, and streaming |
| L03 | Embeddings, and why their versioning is stricter |
| L04–L06 | Managed retrieval, agents and guardrails — and when to build your own instead |
| L08 | The IAM policies that make the third condition true |
| L12 | Quotas, throttling and the retry policy that makes on-demand usable |
| L14 | The cost model at your real volume |

### 5.7 Assumptions and limitations

- Model names, the availability matrix and all prices in the lab are invented.
- Bedrock's feature set changes; treat any specific capability claim here as needing a check.
- Model customisation, fine-tuning on Bedrock and marketplace models are out of scope (M13-L05 covers fine-tuning
  generally).

---

## 6. Worked example — the prototype that could not ship

**The situation.** A team built a document assistant over six weeks, on a newly released model, in `us-east-1`, because
that is where it was available first. The demo was well received and a launch date was set.

**What happened at the launch review.**

1. The customer's contract required **data to stay in the EU**. The model was not available in any EU region
   (§7.2, row 4).
2. The nearest available model produced measurably different output: prompts tuned to the original model's formatting
   behaviour needed rewriting, and the evaluation results no longer held (M10-L11 §5.6).
3. Access for the replacement model had not been requested in the production account, which was a separate account
   (§5.2).
4. Quotas in the EU region were lower than the development account's, so the load test throttled (L12).
5. The cost profile differed enough to change the business case (§5.3).

**Six weeks of work, and the blocking issue was a table in the documentation.**

| # | What was missing | When it should have been done |
|---|---|---|
| 1 | Region parity check for the exact model | Before the prototype (§5.2) |
| 2 | Residency requirement confirmed | Before the model choice (M10-L06) |
| 3 | Model access requested per account | During environment setup |
| 4 | Quota check and load test in the target region | Before the launch date |
| 5 | Cost per request at the real token profile | With the business case (L14) |

**The general rule.** **Check the gates before you build. The most expensive model decision is the one made by whatever
was available in the region you happened to open.**

---

## 7. Practical activity

**File:** [`labs/m12/l01_bedrock_concepts_model_access.py`](../../labs/m12/l01_bedrock_concepts_model_access.py)

**No AWS account, no network, no third-party dependencies.** Nothing here calls Bedrock; the lab computes the decisions so
you can make them before spending anything.

```bash
source .venv/bin/activate
python labs/m12/l01_bedrock_concepts_model_access.py
```

### 7.2 Expected output

`[EXECUTED]` — 2026-09-17, Python 3.12.3 (pure standard library). Run twice; output identical.

```text

============================================================================
1. THREE THINGS MUST ALL BE TRUE BEFORE A CALL SUCCEEDS
============================================================================
  model                    us-east-1       eu-west-2    eu-central-1  ap-southeast-2   enabled here?
  frontier-large           available       available       available               -   yes
  frontier-small           available       available       available       available   NOT REQUESTED
  embedding-v3             available       available       available       available   yes
  newest-preview           available               -               -               -   NOT REQUESTED

  A call succeeds only when THREE things hold: the model exists in the region,
  your account has been granted access to it, and your IAM policy allows the
  invoke action for that model's ARN (M12-L08). Each fails with a different
  error, and teams lose hours because 'access denied' can mean any of them.

============================================================================
2. REGION PARITY NARROWS THE DESIGN
============================================================================
  no constraint                            12 model/region pairs; regions: ap-southeast-2, eu-central-1, eu-west-2, us-east-1
  data must stay in Europe                  6 model/region pairs; regions: eu-central-1, eu-west-2
  Europe + the model we designed around     2 model/region pairs; regions: eu-central-1, eu-west-2
  Europe + the newest preview model         0 model/region pairs; regions: NONE

  The last row is the one that ends a project: the model the prototype was
  built on does not exist where the data is allowed to be. Check parity
  BEFORE the prototype, record the date, and re-check before committing --
  availability expands over time, which is why a six-month-old answer is not
  an answer (M11-L02 section 5.4).

============================================================================
3. ON-DEMAND OR PROVISIONED THROUGHPUT?
============================================================================
  on-demand: $3.0/M input, $15.0/M output; a request is 2400 in + 400 out = $0.0132
  provisioned: $24.0/hour per model unit, whether you use it or not

    requests/day   on-demand $/mo   provisioned $/mo   cheaper
           1,000              396             17,520   on-demand
          20,000            7,920             17,520   on-demand
         100,000           39,600             17,520   provisioned
         400,000          158,400             17,520   provisioned
       2,000,000          792,000             17,520   provisioned

  break-even: about 44,242 requests/day at this token profile.
  Two things the table hides. Provisioned throughput also buys PREDICTABLE
  capacity -- no throttling from a shared pool (M12-L12) -- which can matter
  more than the price. And it is a COMMITMENT: if you halve your context
  length next month, the on-demand line falls and the provisioned one does
  not (M11-L11 section 5.3).

============================================================================
4. WHAT THE SERVICE TAKES OVER, AND WHAT STAYS YOURS
============================================================================
  concern                                 owner               
  running and scaling the model           service             
  model weights and updates               service             
  regional availability                   service             
  which model you choose                  yours               
  what data you send it                   yours               
  the prompt and its versioning           yours               
  output validation and repair            yours               
  guardrail configuration                 yours (M12-L06)     
  IAM permissions on invoke               yours (M12-L08)     
  retry, timeout and backoff policy       yours (M12-L12)     
  evaluation on your tasks                yours (M10-L12)     
  cost per request                        yours (M12-L14)     

  the service owns 3/12; you own 9/12
  This is M11-L01's table for one service. A managed model removes the
  hardest operational problem in the stack and none of the engineering ones.
  Everything in Modules 5, 7, 8 and 10 still applies, unchanged.

============================================================================
5. THE QUESTIONS A MODEL CHOICE HAS TO ANSWER
============================================================================
  question                                      where it is answered
  Does it exist in our region, today?           section 2; record the date
  Has access been requested and granted?        section 1; per account
  Is it good enough ON OUR TASKS?               your evaluation set, not a benchmark (M10-L11)
  What does a request cost at our token profile?section 3 (M11-L06, M12-L14)
  What is its p95 latency at our context size?  measure it (M13-L11)
  What are the quotas, and what happens at them?throttling behaviour (M12-L12)
  Can we pin a version, and what notice of change?reproducibility (M10-L13)
  Is our data used for training? Retained?      supplier assessment (M10-L11)
  What is the fallback when it is unavailable?  routing and degradation (M13-L08)

  9 questions; exactly ONE of them is about model quality.
  That ratio is the lesson. Choosing a hosted model is mostly a procurement
  and operations decision wearing an ML costume, and the questions that sink
  projects are availability, quota, cost and version stability -- not whether
  the model is clever enough.

============================================================================
6. WHAT THIS LAB IS AND IS NOT
============================================================================
  REAL: every count, filter result, cost projection and break-even figure
  above is computed from the values in this script.

  ILLUSTRATIVE: the model names, the availability matrix and every price are
  INVENTED. Bedrock's model catalogue, regional availability and pricing
  change frequently -- check the console and the pricing page, and record the
  date you checked.

  NOT SHOWN: the API surface itself (M12-L02), model customisation, and
  cross-region inference routing.

Done.
```

### 7.3 Reading the result

**Section 1's three conditions** are the first thing to check when a call fails, in that order.

**Section 2's last row** — zero usable pairs — is a project ending in a table.

**Section 3's break-even** is the number to compute with your own prices before anyone argues about it.

**Section 5's ratio** — one quality question in nine — is the lesson's central claim.

---

## 8. Common mistakes and troubleshooting

1. **Prototyping on a model before checking parity in the target region.** §6.
2. **Assuming model access is account-wide.** §5.2 — request it per account.
3. **Using an unpinned model reference.** M10-L13 — results become unreproducible.
4. **Comparing models on public benchmarks.** M10-L11 §5.6 — measure on your tasks.
5. **Committing to provisioned throughput before the token profile is stable.** §5.3.
6. **Ignoring quota differences between accounts and regions.** L12.
7. **Enabling cross-region inference without checking residency.** §5.2.
8. **Treating the managed service as removing the engineering work.** §7.4 — 9 of 12 concerns stay yours.

| Symptom | Likely cause | Fix |
|---|---|---|
| Model id not recognised | Not available in this region | Check parity; change region or model |
| Access denied mentioning model access | Access not granted in this account | Request access per account |
| `AccessDeniedException` on the action | IAM policy missing the model ARN | Add `bedrock:InvokeModel` (L08) |
| Works in dev, throttles in prod | Different quotas per account/region | Check and request quota increases (L12) |
| Output changed with no deploy | Unpinned model reference | Pin the model id; record it (M10-L13) |

---

## 9. Security, privacy, reliability, cost

- **Security.** Invoke permission is the agent's capability boundary (M9-L13, L08); reach the service over a VPC endpoint
  (M11-L08) and log with CloudTrail (M11-L16).
- **Privacy.** What you send is yours to decide (§5.4); residency and data-handling terms are gates, not preferences
  (M10-L06, M10-L11).
- **Reliability.** Quotas, throttling and regional availability are the reliability variables; design a fallback
  (M13-L08).
- **Cost.** Compute the per-request cost at your own token profile before choosing a purchase model (L14, M11-L06).

---

## 10. Exercises

### Exercise 1 — Beginner (~20 min)

1. Name the three conditions that must hold before an invoke call succeeds.
2. How many model/region pairs survive "data must stay in Europe" in §7.2?
3. What is the break-even between on-demand and provisioned in §7.3?
4. How many of the twelve concerns in §7.4 are the service's?
5. Which of the nine questions in §7.5 is about model quality?

### Exercise 2 — Intermediate (~40 min)

1. Run the lab. Change the token profile to 8,000 in / 1,200 out and recompute the break-even.
2. Add a fifth region and a model that exists only there, then re-run the constraint filters.
3. Write the nine questions out for a model you are actually considering, and answer the ones you can.
4. Add two concerns to §7.4 specific to your system and assign each an owner.
5. Look up the real region-availability table for one model and record the date.

### Exercise 3 — Challenge (~60 min)

1. Produce the model-choice decision record from §5.5, gates first, for one real use case.
2. Compute your real per-request cost from measured token counts and compare purchase options.
3. Write the IAM policy that satisfies the third condition, scoped to one model ARN (L08).
4. Design the fallback path for when the primary model is unavailable or throttled (M13-L08).
5. Set a calendar reminder to re-check parity and pricing, and say what would change your decision.

---

## 11. Quiz

*(Answers: [`answer-keys/module-12-answers.md`](../../answer-keys/module-12-answers.md#m12-l01).)*

**Q1.** Which three conditions must all hold before an invoke call succeeds?

- A. Region availability, account access, and an IAM policy allowing the action
- B. Region availability, a provisioned throughput commitment, and an IAM policy
- C. Account access, a VPC endpoint, and a guardrail configuration
- D. An inference profile, account access, and a KMS key

**Q2.** In §7.2, how many model/region pairs survived "Europe + the newest preview model"?

- A. Six
- B. Two
- C. Twelve
- D. None

**Q3.** When should region parity be checked?

- A. Before the prototype, with the exact model you intend to ship
- B. At the launch review, once requirements are final
- C. Only when a residency requirement is known
- D. After the evaluation results are in

**Q4.** Why does a parity answer expire?

- A. Access grants lapse after 90 days
- B. Model ids are rotated periodically
- C. Availability expands over time, so an old answer may be wrong in both directions
- D. Regional endpoints are re-assigned between accounts

**Q5.** What does provisioned throughput buy beyond a possible price advantage?

- A. Automatic failover to a second region
- B. Access to models not available on demand
- C. Lower per-token prices on all models
- D. Predictable capacity that does not compete with a shared pool

**Q6.** What is the risk of committing to provisioned throughput early?

- A. It cannot be combined with on-demand for the same model
- B. It is a fixed cost that does not fall when you optimise your token profile
- C. It requires a separate account
- D. It disables CloudTrail logging for those invocations

**Q7.** In §7.4, how many of the twelve concerns belong to the service?

- A. Three
- B. Six
- C. Nine
- D. Twelve

**Q8.** Which concern is *not* the service's?

- A. Running and scaling the model
- B. Output validation and repair
- C. Model weights and updates
- D. Regional availability

**Q9.** How many of §7.5's nine questions are about model quality?

- A. Four
- B. Two
- C. One
- D. All nine, indirectly

**Q10.** Model access in Bedrock is granted —

- A. per organisation, inherited by member accounts
- B. per account, and must be requested in each
- C. per IAM role
- D. per region, once, for all models

**Q11.** Why pin the model id in configuration?

- A. To reduce invocation latency
- B. Because unpinned ids are rejected by the API
- C. So results can be reproduced and a change is a deliberate release
- D. To qualify for provisioned throughput pricing

**Q12.** Before enabling cross-region inference routing, what must you check?

- A. Whether it increases the per-token price
- B. Whether your IAM policy lists every region
- C. Whether the second region has a VPC endpoint
- D. Whether it moves data across a residency boundary you committed to

**Q13.** *(Written, rubric-graded.)* In under 150 words: a colleague has prototyped on a newly released model and wants
to set a launch date. What do you check before agreeing, and in what order?

---

## 12. Revision notes

- **Three conditions**: region availability, account access, IAM allow on the model ARN — three different errors.
- **Parity is a gate**: 12 → **6** (Europe) → **2** (Europe + our model) → **0** (Europe + preview model). Check before the
  prototype; record the date; re-check before committing.
- **Break-even** at a 2,400/400 profile: about **44,000 requests/day** between on-demand and one provisioned unit.
  Provisioned also buys predictable capacity and is a commitment.
- **The service owns 3 of 12 concerns**; the other **9** — model choice, what you send, prompts, validation, guardrails,
  IAM, retries, evaluation, cost — are yours.
- **One of nine model-choice questions is about quality.** The rest decide whether you can ship.

---

## 13. Completion checklist

- [ ] I can name the three conditions and the error each produces.
- [ ] Parity is checked for the exact model, in the target region, with a recorded date.
- [ ] Model access is requested in every account I deploy to.
- [ ] Model ids are pinned and appear in the run fingerprint.
- [ ] I have computed the per-request cost and the provisioned break-even at my token profile.
- [ ] I have answered all nine model-choice questions, not just the quality one.
- [ ] I scored at least 10/13 on the quiz.

---

## 14. References

- Amazon Bedrock User Guide — model access, supported models and regions, provisioned throughput, inference profiles.
  The catalogue, availability and pricing change frequently `[UNVERIFIED — check current]`
- M11-L01 (shared responsibility) and M11-L02 (region parity as a placement gate) `[STABLE]`
- M10-L11 (supplier and model assessment, gates before scores) and M10-L13 (pinning and reproducibility) `[STABLE]`
- M4-L18 (hosted versus local models) and M5-L17 (provider portability) `[STABLE]`
- M12-L08 (IAM for AI services), M12-L12 (quotas and throttling), M12-L14 (cost per request) `[STABLE]`

---

## 15. Next lesson

→ [M12-L02 — Invocation, Streaming and the Converse API](M12-L02-invocation-streaming-converse.md) moves from choosing a
model to calling one: the unified request shape, how streaming changes every timeout on the path, and where tool use fits.
