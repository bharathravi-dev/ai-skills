# M1-L11 — AI Capability vs Application Reliability, and When Plain Code Wins

| | |
|---|---|
| **Lesson ID** | M1-L11 |
| **Difficulty** | 2 (Core) |
| **Estimated study time** | 1.25 hours |
| **Prerequisites** | [M1-L10](M1-L10-probability-uncertainty-hallucination.md) |

---

## 1. Learning objectives

1. **Distinguish** model capability from application reliability, and **explain** why a demo proves
   the first and says nothing about the second.
2. **Compute** the compound success rate of a multi-step AI pipeline and **explain** why long chains
   degrade fast.
3. **Apply** a decision checklist to determine whether AI, plain code, or a hybrid is appropriate.
4. **Identify** at least five categories of task where ordinary code is strictly better.
5. **Articulate** the reliability argument to a non-technical stakeholder without being dismissive.

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **Capability** | What a model *can* do, at least sometimes, under favourable conditions. |
| **Reliability** | How often a complete system produces an acceptable result under real conditions. |
| **Demo gap** | The distance between an impressive demonstration and a dependable product. |
| **Compound error** | The multiplication of per-step success rates across a pipeline. |
| **Happy path** | The input and conditions the system was designed and demonstrated on. |
| **Long tail** | The large set of rare, varied inputs that collectively make up much of real traffic. |
| **Determinism requirement** | A requirement that the same input must always produce the same output. |
| **Acceptance criteria** | Testable conditions defining "working". |
| **Baseline** | The simplest reasonable alternative, used for comparison. |
| **Cost per request** | Total marginal cost of serving one request. |
| **Failure budget** | The rate of failure the business will tolerate. |

---

## 3. Plain-language explanation

There is a gap that swallows AI projects, and it has a precise shape.

**Capability** is "the model did it once, and I have the screenshot." **Reliability** is "the system
does it 99.5% of the time, on inputs nobody anticipated, at 2am, without a human watching."

Those are separated by most of the engineering work. A demo is evidence of capability. It is not
weak evidence of reliability — it is *no* evidence, because a demo is run on inputs chosen by the
person demonstrating.

You already know this from web development. Making a feature work on your machine with your test
data is a small fraction of shipping it. Error handling, edge cases, concurrency, monitoring and
rollback are the rest. **AI has the same ratio, with two aggravating factors:**

1. The failure mode is silent and confident (M1-L10), so bugs do not announce themselves.
2. The behaviour is probabilistic, so "it works" is a statistical claim rather than a binary one.

The second point deserves stating plainly: **you cannot make an AI feature work "correctly" the way
you make a function correct.** You can only make it work *often enough*, and you must decide what
often enough means before you start.

### Connecting to what you already know

| Web engineering | AI engineering equivalent |
|---|---|
| Works on my machine | Worked in the demo |
| Handles the happy path | Handles the prompts you tried |
| Error handling and retries | Validation, repair, fallback (M5-L07, M5-L14) |
| Input validation | Prompt injection defence (M5-L13) |
| Integration tests | Evaluation dataset (M5-L18) |
| Monitoring and alerting | Online quality monitoring (M13-L12) |
| Load testing | Latency percentiles (M13-L11) |
| Feature flags and rollback | Prompt/model versioning, canary release (M13-L14) |

Everything in the right column is a module in this course. That mapping *is* the curriculum: your
existing instincts transfer, they just need new tools.

---

## 4. Analogy

**A self-driving demo versus a self-driving product.**

Driving one pre-scouted route in good weather demonstrates capability. Driving any route, in any
weather, with a child running out, is reliability. The second is not the first "plus polish"; it is
a different and much larger problem, and the last few percent costs more than everything before it.

### Where the analogy breaks

1. **Driving has an unambiguous success criterion.** "Summarise this ticket well" does not, which
   makes AI reliability harder to *measure*, not just harder to achieve.
2. **The stakes differ enormously by application.** A wrong ticket category costs a re-route. Do not
   import safety-critical rhetoric into a low-stakes feature — it makes you sound unserious and
   blocks useful work.
3. **Cars fail visibly. Text systems fail invisibly.** A plausible wrong summary can go unnoticed for
   months.
4. **You can add non-AI guardrails cheaply.** Validation, permissions and deterministic checks around
   a model are inexpensive compared to the equivalent in a physical system. **This is the good
   news** and it is what most of this course teaches.

---

## 5. Detailed technical explanation

### 5.1 Compound error — the arithmetic that kills pipelines

An AI pipeline is a chain of steps. If every step must succeed, success rates multiply.

Consider a five-step support automation, with generous per-step rates:

| Step | Success rate |
|---|---|
| 1. Classify the ticket | 0.95 |
| 2. Retrieve the right policy | 0.90 |
| 3. Extract the account ID | 0.95 |
| 4. Call the API correctly | 0.98 |
| 5. Draft an acceptable reply | 0.90 |

Every step looks strong. End-to-end:

```
0.95 × 0.90 × 0.95 × 0.98 × 0.90 = 0.7166
```

**71.7%.** Roughly **1 in 3.5 tickets** goes wrong somewhere. No individual step looks like the
problem, and every engineer can defend their own component.

The general rule for `n` steps at rate `p`: success = `p^n`.

| Steps | p=0.99 | p=0.95 | p=0.90 |
|---|---|---|---|
| 3 | 97.0% | 85.7% | 72.9% |
| 5 | 95.1% | 77.4% | 59.0% |
| 10 | 90.4% | 59.9% | 34.9% |
| 20 | 81.8% | 35.8% | 12.2% |

**Read the 0.90 column.** A 10-step agent whose every step works 90% of the time succeeds
**35%** of the time. This single table explains most disappointing agent demos, and it is why M8-L15
puts hard limits on step counts.

**The engineering responses:**

| Response | Effect |
|---|---|
| **Fewer steps** | The highest-leverage fix. Removing a step multiplies your rate by `1/p`. |
| **Deterministic steps** | Replace a model step with code where possible: p becomes ~1.0 and drops out of the product entirely. |
| **Validation and repair at each step** | Raises individual `p` (M5-L07). |
| **Checkpointing** | A failure costs one step, not the whole chain (M8-L14). |
| **Human checkpoint at the risky step** | Converts a silent failure into a caught one (M8-L10). |
| **Independent steps** | If steps are not all required, the product rule does not apply. Design for this. |

The second row is the most important and the most overlooked. **Every step you can make
deterministic disappears from the multiplication.** If step 3 (extract account ID) can be done with a
regular expression at ~100%, your pipeline goes from 71.7% to 75.4% for free — and becomes testable,
debuggable and auditable at that step.

### 5.2 The decision checklist

Ask these before choosing AI. Any "yes" in the left column is a strong signal for plain code.

| Question | If YES → plain code | If NO → AI may fit |
|---|---|---|
| Is the rule written down somewhere authoritative? | Implement the rule | — |
| Must the same input always give the same output? | Determinism required | — |
| Must you explain every decision precisely? | Auditability required | — |
| Is this a security or authorization decision? | **Never delegate to a model** | — |
| Does a wrong answer cause irreversible harm? | Code, or human, or both | — |
| Can a regex, lookup table, or SQL query do it? | Do that | — |
| Is the input structured and the mapping fixed? | Code | — |
| Does the task need judgement over unstructured input? | — | AI fits |
| Are there too many cases to enumerate? | — | AI fits |
| Is "usually right, sometimes wrong" acceptable? | — | AI fits |
| Would a human doing this rely on reading and judgement? | — | AI fits |

**The single best question:** *could a competent person write down the rule in an afternoon?* If yes,
have them write it down. You will get a faster, cheaper, testable, auditable system, and you will
avoid an evaluation problem you did not need.

### 5.3 Tasks where plain code is strictly better

1. **Arithmetic and aggregation.** Totals, tax, percentages. A model *may* get these right; SQL
   *does*. Never compute money with a language model.
2. **Exact lookup.** "What is the price of SKU 4471?" is a database query. Using an LLM introduces
   the possibility of a wrong price and no possibility of a better one.
3. **Format validation.** Email, postcode, IBAN, ISO date. Regex and libraries are exact.
4. **Authorization.** Never. Not "usually correct" — provably correct. This principle recurs in
   M7-L15, M8-L16, M9-L13.
5. **Deterministic transformation.** CSV→JSON, unit conversion, date formatting.
6. **Sorting, filtering, joining.** Ordinary data operations.
7. **Anything with a published specification.** Tax bands, statutory rules, business policy.

A useful diagnostic when someone proposes AI: **"what would we do if the model were unavailable?"**
If the honest answer is "write the obvious code", consider writing it first and using the model only
where that code cannot reach.

### 5.4 Where AI genuinely wins

Be equally clear about this, or you will become the person who blocks good work:

1. **Unstructured input.** Free text, images, audio — where writing rules is hopeless.
2. **Open-ended output.** Summaries, drafts, explanations.
3. **Long-tail variation.** Thousands of phrasings for the same intent.
4. **Fuzzy matching.** Semantic similarity where exact matching fails (Module 6).
5. **Tasks humans do by reading.** Triage, extraction, classification of prose.
6. **Rapid prototyping.** Working system this week without a labelling project.
7. **Tasks with an acceptable failure mode.** Drafting for human review is the archetype: a wrong
   draft costs an edit, not an incident.

Point 7 is the design principle worth internalising: **shape the task so that being wrong is cheap.**
"Draft a reply for the agent to approve" and "send a reply" are the same capability with entirely
different reliability requirements. Choosing the first is often the whole difference between a
project that ships and one that does not.

### 5.5 Setting a reliability target before you build

Define acceptance criteria before writing code:

| Question | Example answer |
|---|---|
| What does success mean, per request? | Correct category, or correctly abstained |
| What rate is acceptable? | ≥ 92% on the held-out eval set |
| What happens on failure? | Route to human queue; log with trace ID |
| What is the failure budget? | ≤ 8% mis-routed, ≤ 2% silently wrong |
| What is the fallback if the provider is down? | Rule-based routing on keywords |
| Cost ceiling per request? | £0.01 |
| Latency ceiling? | p95 < 3s |
| How will we know in production? | Sampled human review of 50/day + reassignment-rate monitor |

If you cannot fill this table, you are not ready to build — and filling it in is often what reveals
that the project as scoped is impossible (as happened in the M1-L10 threshold analysis). M14-L04
develops this into a full method.

### 5.6 Assumptions and limitations

- Per-step success rates are rarely independent; failures correlate (a garbled input breaks several
  steps). The product rule is therefore an *optimistic* approximation.
- Capability moves. A task infeasible today may be routine in a year. Re-test rather than
  re-remembering — but do not architect around capabilities you do not have.
- "Plain code is better" assumes the rules are knowable. If nobody can articulate them, that option
  does not exist.

---

## 6. Worked example — the ticket automation proposal

> "Let's use AI to fully automate our tier-1 support. 500 tickets/day."

**Step 1 — decompose** (M1-L03). Classify, retrieve policy, extract account ID, look up account,
draft reply, send.

**Step 2 — apply the checklist per step.**

| Step | Structured? | Rule exists? | Verdict |
|---|---|---|---|
| Classify | No — free text | No | **AI** |
| Retrieve policy | No — semantic match | No | **AI (retrieval)** |
| Extract account ID | Semi — a pattern like `ACC-12345` | Yes | **Regex** ✅ |
| Look up account | Yes | Yes | **Database query** ✅ |
| Draft reply | No | No | **AI** |
| Send | Yes | Yes | **Code** ✅ |

Three of six steps are plain code. That is typical, and identifying it early is most of the value of
this lesson.

**Step 3 — compute reliability.**

Naive all-AI version:
`0.95 × 0.90 × 0.95 × 0.98 × 0.90 × 0.99 = 0.709` → **70.9%**, or ~146 wrong tickets/day.

Hybrid version, with the three deterministic steps at ~1.0 (the lab uses 0.999 for the regex, since
no parser is truly perfect):
`0.95 × 0.90 × 0.999 × 1.0 × 0.90 × 1.0 = 0.769` → **76.9%**, ~116 wrong/day.

Better, and still nowhere near "automate tier 1".

**Step 4 — reshape the task instead of chasing the number.** The requirement "send" is what forces
near-perfection. Change it to "draft for agent approval":

- Failure now costs an edit, not a customer incident.
- The agent is a verification step with very high reliability.
- Value shifts from *elimination* of work to *acceleration* of it.

**Step 5 — restate the business case honestly.**

| | Full automation | Assisted drafting |
|---|---|---|
| Reliability needed | ~99%+ | ~80% is genuinely useful |
| Achievable now? | No | Yes |
| Failure cost | Customer harm, escalation | An agent edits a draft |
| Value | Remove agent time | Reduce handling time ~40% |
| Risk | High | Low |

**The recommendation:** build assisted drafting. Measure the handling-time reduction. Revisit
automation for the *narrow* ticket categories where measured accuracy exceeds 98%, if any.

This is the single most valuable conversation pattern in this course, and Module 14 is largely about
having it well. Note what it is *not*: it is not "no". It is a smaller, achievable yes, with a
measurable path to the larger one.

---

## 7. Practical activity

**File:** [`labs/m1/l11_reliability_calculator.py`](../../labs/m1/l11_reliability_calculator.py)

```bash
python3 labs/m1/l11_reliability_calculator.py
```

Models the §6 pipeline: computes compound reliability for the all-AI and hybrid designs, prints the
`p^n` decay table, shows the effect of removing one step versus improving one step by 5 points, and
converts everything into tickets-per-day so the numbers are concrete.

### 7.1 Important lines

| Construct | Why |
|---|---|
| `math.prod(...)` | Multiplies a list — the compound-error rule in one call. |
| `steps_without(i)` | Removes a step to show the leverage of *deletion* versus improvement. |
| `daily_failures = volume * (1 - reliability)` | Converts a percentage into the number a manager reacts to. |

### 7.2 Expected output

`[EXECUTED]` 2026-09-07, Python 3.12.3. Deterministic:

```
========================================================================
COMPOUND RELIABILITY: why good steps make a poor pipeline
========================================================================

DESIGN A - every step done by a model
    classify ticket        0.950
    retrieve policy        0.900
    extract account id     0.950
    look up account        0.980
    draft reply            0.900
    send                   0.990
                           0.950  x  0.900  x  0.950  x  0.980  x  0.900  x  0.990
    -> end-to-end reliability = 0.7092  (70.9%)
    -> at 500 tickets/day: 145 go wrong somewhere

DESIGN B - the three deterministic steps done in code
    classify ticket        0.950
    retrieve policy        0.900
    extract account id     0.999
    look up account        1.000
    draft reply            0.900
    send                   1.000
                           0.950  x  0.900  x  0.999  x  1.000  x  0.900  x  1.000
    -> end-to-end reliability = 0.7687  (76.9%)
    -> at 500 tickets/day: 116 go wrong somewhere

Hybrid improvement: 70.9% -> 76.9% (30 fewer bad tickets per day)

------------------------------------------------------------------------
DELETE A STEP  vs  IMPROVE A STEP  (starting from Design A)
------------------------------------------------------------------------
intervention                              reliability     change
------------------------------------------------------------------------
(baseline, Design A)                           70.9%           
DELETE: classify ticket                        74.7%      +3.7%
DELETE: retrieve policy                        78.8%      +7.9%
DELETE: extract account id                     74.7%      +3.7%
DELETE: look up account                        72.4%      +1.4%
DELETE: draft reply                            78.8%      +7.9%
DELETE: send                                   71.6%      +0.7%

IMPROVE +5pp: classify ticket                  74.6%      +3.7%
IMPROVE +5pp: retrieve policy                  74.9%      +3.9%
IMPROVE +5pp: extract account id               74.6%      +3.7%
IMPROVE +5pp: look up account                  72.3%      +1.4%
IMPROVE +5pp: draft reply                      74.9%      +3.9%
IMPROVE +5pp: send                             71.6%      +0.6%

Deleting a step multiplies reliability by 1/p, so removing the
WEAKEST step helps most. Improving a step by a fixed amount helps
by roughly (improvement/p) - also biggest for the weakest step.
Either way: fix the worst step, and prefer deleting it to tuning it.

------------------------------------------------------------------------
HOW RELIABILITY DECAYS WITH CHAIN LENGTH  (p^n)
------------------------------------------------------------------------
  steps    p=0.99    p=0.95    p=0.90    p=0.80
------------------------------------------------------------------------
      1     99.0%     95.0%     90.0%     80.0%
      3     97.0%     85.7%     72.9%     51.2%
      5     95.1%     77.4%     59.0%     32.8%
     10     90.4%     59.9%     34.9%     10.7%
     20     81.8%     35.8%     12.2%      1.2%
     30     74.0%     21.5%      4.2%      0.1%
------------------------------------------------------------------------

The p=0.90 column is the one to remember. A 10-step agent whose
every step works 9 times out of 10 finishes correctly about a
THIRD of the time. This is why agents get hard step limits
(M8-L15) and why 'just add another tool call' is not free.

NOTE: this rule is OPTIMISTIC. It assumes step failures are
independent. In reality a malformed input breaks several steps at
once, so measured reliability is usually worse than p^n predicts.
========================================================================
```

### 7.3 Reading the result

**Three things in this output change how you design pipelines.**

**1. Moving three steps to code bought 30 tickets a day.** 70.9% → 76.9%, with no change to any
model, any prompt, or any budget. The three steps that became deterministic simply left the
multiplication. This is the cheapest reliability improvement available in most AI systems and it is
routinely skipped in favour of prompt tuning.

**2. Deleting a step beats improving it — by roughly double.**

| Intervention on `retrieve policy` | Result | Change |
|---|---|---|
| Improve it by 5 percentage points (0.90 → 0.95) | 74.9% | +3.9% |
| **Delete it entirely** | **78.8%** | **+7.9%** |

Deleting multiplies your reliability by `1/p`; improving adds roughly `improvement/p`. For a weak
step, deletion wins decisively. So the first design question is not *"how do I make this step
better?"* but **"do I need this step at all?"** — and the second is *"can it be code?"*

Both tables also agree on *where* to intervene: the weakest steps (`retrieve policy` and
`draft reply`, both at 0.90) dominate, and the strongest (`send`, 0.99) is nearly irrelevant. Effort
spent on a step that already works 99% of the time is effort wasted.

**3. The `p^n` table is the one to memorise.**

```
  steps    p=0.99    p=0.95    p=0.90    p=0.80
     10     90.4%     59.9%     34.9%     10.7%
     20     81.8%     35.8%     12.2%      1.2%
```

A 10-step agent whose every step works 9 times in 10 completes correctly **about a third of the
time**. A 20-step agent at the same per-step rate succeeds **12%** of the time. When you read about
agents that "sometimes go off the rails", this table is usually the whole explanation — and it is why
M8-L15 imposes hard step limits rather than trusting the loop to behave.

**And note the caveat the lab prints.** The product rule assumes step failures are *independent*.
They are not: a malformed input, an ambiguous ticket or a truncated document breaks several steps at
once. So every number above is an **optimistic** bound. Measured reliability is typically worse.

**Verification:** confirm Design A = `0.7092 (70.9%)`, Design B = `0.7687 (76.9%)`, and that
`DELETE: retrieve policy` shows `+7.9%` against `IMPROVE +5pp: retrieve policy` at `+3.9%`.

---

## 8. Common mistakes and troubleshooting

1. **Treating a demo as evidence of reliability.** Ask what inputs it was tried on and who chose
   them.
2. **Ignoring compound error.** Every additional model step multiplies your failure rate.
3. **Using a model where a regex would do.** Slower, dearer, less reliable, untestable.
4. **Delegating authorization to a model.** Non-negotiable.
5. **Not defining acceptance criteria before building.**
6. **Assuming reliability improves with a better prompt.** Sometimes; often the ceiling is
   structural.
7. **Being the person who says AI is unreliable and stops there.** Bring the reshaped version.
8. **Chasing the last few points instead of changing the task shape.**

| Symptom | Diagnosis | Fix |
|---|---|---|
| Demos well, fails in production | Happy-path only | Build a diverse eval set from real inputs |
| Each component fine, system poor | Compound error | Reduce steps; make steps deterministic |
| "Sometimes wrong" is unacceptable | Determinism requirement | Move that decision to code or a human |
| Costs more than expected | Per-request model cost across many steps | Route cheap steps to code or smaller models |
| Cannot explain a decision to a customer | Auditability requirement | Rule-based for that decision |

---

## 9. Security, privacy, reliability and cost

- **Security.** Every model step is an injection surface (M5-L13). Fewer model steps is a smaller
  attack surface as well as a higher success rate. Authorization stays in code, always.
- **Reliability.** Publish reliability as a *measured distribution*, never as a claim. "92% on our
  eval set of 300 examples, measured 2026-09-01" is a statement someone can check.
- **Cost.** Six model calls at ~£0.002 each is £0.012/ticket → £6/day at 500 tickets → ~£2,200/year,
  before retries and evaluation runs. Replacing three steps with code cuts it roughly in half. Do
  this arithmetic in the proposal, not after (M5-L15).
- **Governance.** The decision *not* to use AI for a step is itself worth recording — it is evidence
  of deliberate design in an audit (M10-L15).

---

## 10. Exercises

### Exercise 1 — Beginner (~10 min)

For each, say AI, plain code, or hybrid — with the deciding question from §5.2:

1. Calculate VAT on an invoice.
2. Decide whether a support email is angry.
3. Check whether a password meets the complexity policy.
4. Summarise a 40-message conversation thread.
5. Determine whether user X may view document Y.
6. Extract an order number matching `ORD-\d{6}` from an email.
7. Decide which of 5,000 help articles best answers a question.

### Exercise 2 — Intermediate (~20 min)

A pipeline has six steps at 0.97, 0.93, 0.99, 0.88, 0.95 and 0.99.

1. Compute end-to-end reliability. Show your working.
2. At 2,000 requests/day, how many fail?
3. Which single step should you improve first, and why? Compute the new end-to-end figure if you
   raise it to 0.95.
4. Which single step should you try to make deterministic? Compute the effect of removing it from
   the product entirely.
5. Compare your answers to 3 and 4. Which intervention is worth more, and what general principle
   does that illustrate?

### Exercise 3 — Challenge (~30 min)

Your CTO asks for "an AI agent that manages our AWS infrastructure — it should be able to scale
services, restart failed tasks, and fix configuration drift."

1. Decompose into steps and mark each as AI or code.
2. Identify every **irreversible** action and state what must be true before one is taken.
3. Compute a realistic end-to-end reliability with your assumed per-step rates, stated explicitly.
4. Redesign so the failure mode is acceptable. What does the agent do, and what does it never do?
5. Write a 150-word response to the CTO. Take the idea seriously, be specific about what you will
   build first, and state your reliability assumption openly.
6. Name the one thing in your design most likely to be wrong, and how you would find out early.

The rubric weights parts 4 and 5 most heavily. A response that only lists risks scores poorly; a
response that proposes a smaller, achievable, measurable version scores well.

---

## 11. Quiz

**Q1.** What is the essential difference between capability and reliability?

- A. Capability is about speed; reliability is about accuracy.
- B. Capability is what a model can do at least sometimes under favourable conditions; reliability is
  how often a whole system succeeds under real conditions.
- C. They are the same thing measured differently.
- D. Capability applies to models; reliability applies only to hardware.

**Q2.** Five steps at 0.95, 0.90, 0.95, 0.98 and 0.90. End-to-end reliability?

- A. 90.0%  B. 82.5%  C. 71.7%  D. 95.0%

**Q3.** A 10-step agent whose every step succeeds 90% of the time succeeds end-to-end about:

- A. 90%  B. 65%  C. 35%  D. 10%

**Q4.** Which intervention removes a step's failure rate from the product entirely?

- A. Improving the prompt for that step.
- B. Replacing that step with deterministic code, so its success rate becomes ~1.0.
- C. Adding a retry.
- D. Using a larger model.

**Q5.** Which task should **never** be delegated to a model?

- A. Summarising a document  B. Classifying ticket sentiment
- C. Deciding whether user X may access document Y  D. Drafting a reply

**Q6.** "Could a competent person write down the rule in an afternoon?" — if the answer is yes, you
should:

- A. Use an LLM, since the task is simple.
- B. Have them write it down: you get a faster, cheaper, testable and auditable system and avoid an
  evaluation problem you did not need.
- C. Use a hybrid.
- D. Use a smaller model.

**Q7.** In the §6 example, why does changing "send the reply" to "draft for agent approval" matter so
much?

- A. It reduces API cost.
- B. It changes the failure cost from a customer incident to an edit, so a reliability level that is
  unacceptable for sending is genuinely useful for drafting.
- C. It makes the model more accurate.
- D. It removes the need for evaluation.

**Q8.** Why is the compound-error product rule described as *optimistic*?

- A. It overstates the number of steps.
- B. It assumes step failures are independent, but in practice failures correlate — a garbled input
  breaks several steps at once — so real reliability is usually worse.
- C. It ignores latency.
- D. It assumes all steps use the same model.

**Q9.** A stakeholder shows you a demo where the assistant answered five questions perfectly. What is
the most useful next question?

- A. "Which model is it?"
- B. "Who chose those five questions, and what happens on inputs nobody picked in advance?"
- C. "How fast was it?"
- D. "Can we add more features?"

**Q10.** *(Written, rubric-graded.)* In under 100 words, respond to "the demo worked perfectly, why
do you need six more weeks?" — without being dismissive, and with at least one concrete number.

---

## 12. Revision notes

- **Capability** = it worked once, on inputs someone chose. **Reliability** = it works often enough,
  on inputs nobody chose. A demo is evidence of the first and none of the second.
- **Compound error:** required steps multiply. `p^n`. Ten steps at 0.90 → **35%**.
- Highest-leverage fixes, in order: **remove steps** · **make steps deterministic** (they leave the
  product entirely) · validate and repair · checkpoint · human checkpoint at the risky step.
- **Never** delegate: authorization, arithmetic on money, exact lookup, format validation, published
  specifications.
- Best single question: *could a competent person write down the rule in an afternoon?*
- AI wins on: unstructured input, open-ended output, long-tail variation, fuzzy matching, tasks
  humans do by reading, prototyping, **and tasks where being wrong is cheap**.
- **Reshape the task so failure is cheap.** "Draft for approval" ≠ "send".
- Define acceptance criteria, failure budget, fallback, cost and latency ceilings **before** building.
- Do not just say "unreliable" — bring the smaller, achievable version.

---

## 13. Completion checklist

- [ ] I can define capability vs reliability in one sentence each.
- [ ] I can compute compound reliability and explain the `p^n` table.
- [ ] I ran the lab and can explain why deleting a step beats improving one.
- [ ] I can list five tasks where plain code is strictly better.
- [ ] I can list five where AI genuinely wins.
- [ ] I completed the §5.5 acceptance-criteria table for a hypothetical project.
- [ ] I attempted Exercise 3 and wrote the response to the CTO.
- [ ] I scored 7/10 on the quiz.

---

## 14. References

- Sculley et al., "Hidden Technical Debt in Machine Learning Systems" (NeurIPS 2015). `[UNVERIFIED]`
- Google, *People + AI Guidebook* — on designing for graceful failure and appropriate trust.
  <https://pair.withgoogle.com/guidebook/> `[UNVERIFIED]`

---

## 15. Next steps — end of Module 1

You have finished the eleven lessons of Module 1. Before moving on:

1. Work the **revision guide**: [`assessments/module-01-revision.md`](../../assessments/module-01-revision.md)
2. Sit the **module assessment** (18 questions + practical):
   [`assessments/module-01-assessment.md`](../../assessments/module-01-assessment.md)
3. Check your answers: [`answer-keys/module-01-answers.md`](../../answer-keys/module-01-answers.md)

Then begin → [M2-L01 — Terminal, Python Install, Virtual Environments and pip](../module-02-python-foundations/M2-L01-setup-terminal-venv-pip.md)

Module 2 is where you stop reasoning about AI and start building. It is the longest module in the
course, and every later module depends on it.
