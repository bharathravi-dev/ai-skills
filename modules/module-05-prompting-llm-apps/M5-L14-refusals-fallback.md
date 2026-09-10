# M5-L14 — Refusals, Errors and Fallback Behaviour

| | |
|---|---|
| **Lesson ID** | M5-L14 |
| **Difficulty** | 2 (Intermediate) |
| **Estimated study time** | 1.5 hours |
| **Prerequisites** | [M5-L07](M5-L07-validation-repair.md) |

---

## 1. Learning objectives

1. **Distinguish** a refusal, an infrastructure error and an empty or malformed response as three
   separate failure classes, each needing its own detection.
2. **Explain** why a keyword-based refusal detector misfires in both directions, and what that costs.
3. **Decide** whether a given failure is worth retrying, and justify it with the failure's actual
   recovery rate rather than habit.
4. **Design** a circuit breaker and compute the cost it saves during a sustained outage.
5. **Choose** a fallback response matched to the failure class, instead of one generic error path.

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **Refusal** | The model declining an otherwise well-formed request. |
| **Policy refusal** | A refusal grounded in the model's safety or usage-policy training. |
| **Capability limit** | A decline because a genuine capability (browsing, real-time data) does not exist — distinct from policy. |
| **Infrastructure error** | A transport or service failure — timeout, 5xx, rate limit — unrelated to what the model would have said. |
| **Retry-worthy** | A failure whose success probability improves meaningfully on an identical repeated attempt. |
| **Circuit breaker** | A control that stops sending requests to a failing dependency for a period, bounding cost during an outage. |
| **Half-open (breaker state)** | A breaker's periodic, limited probe of a tripped dependency to test recovery. |
| **Retry storm** | Many clients retrying simultaneously against a failing dependency, amplifying the outage. |
| **Silent failure** | Returning no clear signal that something went wrong, leaving the user or caller to guess. |

---

## 3. Plain-language explanation

### 3.1 Three failures that look alike and are not

M5-L07 taught you to classify a **validation** failure as transient or systematic before deciding
whether to retry. This lesson adds the failures that arrive *before* validation ever runs: the model
**refuses**, the **infrastructure** fails, or the response is **empty** or malformed for reasons that
have nothing to do with policy. All three can show up as "the request didn't work." **Treating them as
one problem is the mistake this lesson exists to prevent.**

### 3.2 A refusal usually looks like a normal, successful response

This is the detail that catches people out: a refusal typically arrives as **HTTP 200 with ordinary
text** — "I'm sorry, I can't help with that." Nothing at the transport layer tells you it happened. Your
code has to recognise it from the content, and §7.1 shows that recognising it reliably is harder than it
looks.

### 3.3 Retrying is the right answer to exactly one of these

An infrastructure error is usually noise: ask again and the odds of success rise fast (M2-L14). A policy
refusal is usually closer to the model's **stable, repeatable answer** — asking the identical question
again mostly does not change it. §7.2 puts numbers on the gap. **Applying M2-L14's retry machinery to a
refusal is not a safety issue; it is a budget one.**

### 3.4 A system-wide failure needs a system-wide response

When the failure is not one bad request but a dependency that is entirely down, retrying *every* request
individually multiplies the damage — thousands of doomed attempts hammering something that cannot
answer any of them. §7.3 prices what a circuit breaker saves by stopping that.

---

## 4. Analogy

**A receptionist fielding three different kinds of "no."** A visitor is turned away because the policy
says no visitors without an appointment (a **policy refusal** — asking the same way again gets the same
no). A visitor is turned away because the person they want genuinely isn't in the building today (a
**capability limit** — true, and a different kind of no). And the phone line to the back office is down,
so the receptionist can't even check whether anyone is in (an **infrastructure error** — try again in a
few minutes and it will likely work).

A receptionist who treats all three the same — a flat "no, come back later" — wastes the visitor's time
twice: once by not saying *why*, and once by not knowing that only one of the three is worth a second
attempt at all.

### Where the analogy breaks

- **A receptionist recognises which "no" they're giving without effort.** Your code has to infer it from
  text with no reliable marker, which is exactly §7.1's problem.
- **A human visitor understands nuance in a spoken "no."** A downstream system consuming your API often
  only sees text and a status code, and needs the distinction made explicit, not implied.
- **One receptionist, one visitor at a time.** A circuit breaker exists because your system faces
  thousands of "phone line is down" moments at once, not one.

---

## 5. Detailed technical explanation

### 5.1 A detector that misfires in both directions

`[REAL]` §7.1 ran a keyword-based refusal detector against nine constructed samples:

| Class | Detector's error |
|---|---|
| Genuine refusals (4 samples) | **1 missed** — a capability-limit statement with no marker phrase |
| Legitimate domain content (3 samples) | **2 wrongly flagged** — text about what "cannot" be done that isn't a refusal at all |
| Empty response / infra error (2 samples) | Correctly not flagged as refusals — but that's the wrong question for them entirely |

**A false negative lets a refusal through as if it were a real answer** — worse than the false positive,
because downstream code may act on refusal text as content. **A false positive treats a legitimate
answer as a failure**, triggering an unnecessary retry or escalation. Both directions cost something,
and — echoing M5-L13's filter result — **no keyword list closes the gap completely.**

### 5.2 Retry-worthiness has a number, not a habit

`[REAL arithmetic on stated rates]` §7.2 compared cumulative success after repeated identical attempts:

| Attempts | Infra error (transient) | Policy refusal (identical re-ask) |
|---|---|---|
| 1 | 60% | 3% |
| 3 | 94% | 9% |
| 5 | **99%** | **14%** |
| 8 | 100% | 22% |

**By 5 attempts an infra error is all but resolved. A refusal, re-asked identically, is still wrong 86%
of the time — for the same five attempts of cost.** The reason is not that refusals are unlucky; it is
that a refusal is closer to the model's *actual, repeatable* decision than to random noise around a
right answer. **Retry the first kind. For the second, change something — the prompt, the context, the
capability offered — or stop and escalate (M5-L07's degrade/escalate/fail choice, applied here).**

### 5.3 The circuit breaker

`[REAL arithmetic on stated parameters]` §7.3 modelled a 120-second outage at 50 requests/second
(6,000 total requests):

| Strategy | Wasted upstream attempts |
|---|---|
| No breaker — every request retries 3× | **18,000** |
| Breaker — trips after 5 failures, probes every 30s | **8** |

**A 99.96% reduction in wasted attempts against a dependency that could not have answered any of
them.** Every one of the 6,000 users still gets *a* response in both scenarios — the difference is
whether it comes instantly from a local fallback or only after a doomed multi-second retry cycle. A
breaker has three states: **closed** (normal traffic), **open** (short-circuit locally after the trip
threshold), and **half-open** (a periodic, limited probe to test recovery before resuming full traffic).

### 5.4 Matching the fallback to the failure

| Failure class | Retry the identical request? | What the user should see |
|---|---|---|
| Infrastructure error | **Yes** — bounded, with backoff (M2-L14) | Brief "retrying" state, then success or an honest failure |
| Policy refusal | **No** — retrying wastes budget (§5.2) | A clear reason, and an alternative path if one exists |
| Capability limit | No — the answer will not change | What the system *can* do instead, not a bare "no" |
| Sustained outage | No — the breaker is open | An immediate, honest fallback, not a hung request |

**A generic "something went wrong, try again" answer is wrong for at least three of these four rows.**
It wastes the user's time on a policy refusal, misleads them on a capability limit, and — worst — invites
them to retry manually into an open breaker, recreating the retry storm the breaker exists to prevent.

### 5.5 Silent failure is its own, separate defect

An empty or truncated response with no error signal is not any of the above — it is a fourth failure
mode. The fix is not classification; it is making sure your pipeline never returns "nothing, with no
explanation" as if it were a valid empty answer. Check `finish_reason` (M4-L15) before treating a short
response as complete.

### 5.6 Assumptions and limitations

- §7.1's sample set is small and hand-built; it demonstrates the failure mode, not a production-scale
  false-positive/false-negative rate. Measure your own on real traffic.
- §7.2's per-attempt success rates are stated, illustrative parameters. Real refusal stability and real
  transient-error recovery both vary by provider, cause and model version.
- §7.3's traffic and timing figures are chosen to make the arithmetic legible. Recompute with your own
  request rate, outage duration and retry policy.
- A production refusal classifier typically needs more than a keyword list — the same lesson M5-L13
  drew about injection filters applies here in reverse.

---

## 6. Worked example — the support bot that apologised for nothing

**The system.** A support assistant answers billing questions. On any failure, it returns: *"Sorry,
something went wrong. Please try again."* — one message, for every cause.

**What actually happened, three ways in one week:**

| Incident | True cause | What the generic message did |
|---|---|---|
| A | The billing API timed out under load (infra error) | User retried manually — fine, coincidentally, since this *was* retry-worthy |
| B | The user asked for a competitor's pricing, and the model declined on policy grounds | User retried the identical question five times, got the same decline five times, then filed a complaint about a "broken bot" |
| C | The billing API was down for 4 minutes (sustained outage) | Thousands of users each triggered a full retry cycle against a dead dependency, extending the outage's visible impact well past the 4 minutes it actually lasted |

**Why one message failed twice out of three.** Incident A's generic message happened to produce the
right *behaviour* (retry) for the wrong *reason* (the message gave no indication retrying would help —
it was luck that the user tried again). Incident B's message actively encouraged five wasted attempts at
something §7.2 shows barely moves. Incident C turned a 4-minute outage into a much longer visible one,
because nothing in the pipeline stopped new requests from individually retrying against a dependency that
could not answer any of them.

**Three defects:**

| # | Defect | Consequence |
|---|---|---|
| 1 | No classification of failure type before choosing a response | The same message served three situations with three different correct actions |
| 2 | No distinction between "retry helps" and "retry wastes budget" | Incident B burned five attempts for a 14%-ish chance of a different answer that was never coming |
| 3 | No circuit breaker | Incident C's blast radius was the traffic volume during the outage, not just the outage itself |

### The fix

**Classify before responding**, per §5.4's table: infra error → bounded retry with backoff, honest
failure if exhausted; policy refusal → a clear reason and an alternative, not a repeat of the same
request; capability limit → say what the system *can* do; sustained outage → an open breaker and an
immediate fallback, not a hung retry.

**Bound refusal retries separately from infra retries** — if you retry at all on a suspected refusal, do
it once, with a materially different prompt, not the identical text five times.

**Add the breaker** so a real outage's visible impact is close to its actual duration, not multiplied by
every individual client's retry cycle.

**The general rule.** **A single generic error message is a decision to be wrong for at least two out of
every three failure classes you actually have.** Classify first; respond second.

---

## 7. Practical activity

**File:** [`labs/m5/l14_refusals_fallback.py`](../../labs/m5/l14_refusals_fallback.py)

**No API key, no network.**

```bash
source .venv/bin/activate
python labs/m5/l14_refusals_fallback.py
```

Pure Python, no dependencies. Section 1's detector and sections 2–3's arithmetic are all real and exact
given the stated inputs — no model call anywhere in this lab.

### 7.2 Expected output

`[EXECUTED]` — 2026-09-09, Python 3.10.11.

```text
============================================================================
1. REFUSAL DETECTION: A HEURISTIC THAT MISFIRES BOTH WAYS
============================================================================
  Nine sample outputs. Ground truth: is this actually a model
  REFUSING, or something else entirely?

  sample              true class    detector says   correct?
  genuine_refusal_1   refusal       refusal         yes
  genuine_refusal_2   refusal       refusal         yes
  genuine_refusal_3   refusal       refusal         yes
  capability_limit    refusal       not-refusal     NO
  legit_domain_1      legitimate    refusal         NO
  legit_domain_2      legitimate    not-refusal     yes
  legit_domain_3      legitimate    refusal         NO
  empty_response      empty         not-refusal     n/a (wrong tool)
  error_shaped        infra_error   not-refusal     n/a (wrong tool)

  False negatives: 1/4 genuine refusals missed.
  False positives: 2/3 legitimate answers wrongly flagged as refusals.

  Read the two 'legit_domain' rows the detector got wrong: they
  contain the exact words a refusal detector looks for, because the
  DOMAIN CONTENT is about things that can't or cannot be done. And
  read the last two rows: an empty response and an infrastructure
  error are not refusals at all -- they are two entirely separate
  failure classes a real system must detect with DIFFERENT checks,
  not folded into 'the model said no.'

============================================================================
2. RETRYING AN INFRA ERROR VS RETRYING A REFUSAL
============================================================================
  Per-attempt success probability, cumulative over repeated retries
  of the SAME request. Infra error (transient, per M2-L14): 60%/attempt.
  Safety/policy refusal, identical re-ask: 3%/attempt.

   attempts  infra: cumulative success  refusal: cumulative success
          1                        60%                           3%
          2                        84%                           6%
          3                        94%                           9%
          5                        99%                          14%
          8                       100%                          22%

  By 5 attempts, retrying a transient infra error succeeds nearly
  99% of the time -- exactly why M2-L14's retry-with-backoff exists.
  Retrying an identical prompt after a policy refusal barely moves: just 14% after those same 5
  attempts, for the same cost. The refusal is not noise around a
  right answer the way a timeout is -- it is closer to the model's
  actual, repeatable answer. Retrying it blindly with M2-L14's
  machinery burns budget for almost nothing; the right response is a
  DIFFERENT strategy -- rephrase with more context, offer an
  alternative capability, or escalate to a person (M5-L07's
  degrade/escalate/fail choice, applied to a different failure class).

============================================================================
3. THE CIRCUIT BREAKER: BOUNDING COST DURING AN OUTAGE
============================================================================
  An upstream dependency is down for 120s. Traffic: 50 req/s -> 6,000 requests arrive during the outage.

  WITHOUT a circuit breaker: every request retries up to 3x (M2-L14's backoff, applied blindly).
    wasted upstream attempts: 6,000 x 3 = 18,000

  WITH a circuit breaker: opens after 5 consecutive failures, then short-circuits new requests locally
  (an instant fallback response, no upstream call) and probes upstream once every 30s to test recovery.
    trip cost:   5 attempts
    probe cost:  115s remaining / 30s = 3 probe attempts
    total wasted upstream attempts: 5 + 3 = 8

  Reduction in wasted upstream attempts: 99.96% (18,000 -> 8).

  Every one of the 6,000 users still gets a response
  in both cases -- the difference is WHERE it comes from. Without a
  breaker, each of them waits through a full retry cycle against a
  dependency that cannot answer. With a breaker, everyone after the
  trip gets an immediate, honest fallback, and the dead dependency
  is bothered only a handful of times instead of tens of thousands.

============================================================================
4. WHAT THIS LAB IS AND IS NOT
============================================================================
  REAL: section 1's detector and its results on the stated samples,
  and sections 2-3's arithmetic, given the stated rates and
  parameters -- all exact and reproducible.

  ILLUSTRATIVE: the specific per-attempt success rates in section 2
  and the traffic/timing parameters in section 3. The SHAPE is the
  point -- transient failures respond to retrying, refusals mostly
  don't, and a breaker's saving grows with outage length and
  traffic. Measure your own rates before setting real thresholds.

  NOT SHOWN: a real model's actual refusal phrasing, which varies by
  provider, version and system prompt, and a production-grade
  refusal classifier, which typically needs more than a keyword list
  -- see M5-L13's same lesson about pattern-matching's limits,
  applied here to refusals instead of injected instructions.

Done.
```

### 7.3 Reading the result

**Section 1 misfires in both directions, on purpose, to make the point concretely.** The detector missed
a real refusal phrased without a marker word, and flagged two legitimate answers whose domain content
happens to use "unable to" and "cannot." Neither error is exotic — both are exactly the kind of text a
real support or legal or HR assistant produces routinely.

**Section 2 is the number that should change how you retry.** Five attempts turn a 60%-per-try infra
error into 99% cumulative success. The same five attempts, spent on an identical re-ask after a refusal,
buy only 14%. **The cost is identical; the return is not.** That gap is the entire argument for
classifying before retrying.

**Section 3's reduction — 18,000 wasted attempts down to 8 — is not a rounding trick.** It is what
happens when you stop asking a dead dependency the same question thousands of times in parallel. Every
user still gets an answer either way; only the breaker version gets it without extending the outage's
visible impact past its real duration.

---

## 8. Common mistakes and troubleshooting

1. **Treating a 200-status response as automatically successful.** A refusal usually arrives with a
   normal status code (§3.2).
2. **Using one generic error message for every failure class.** §6 — wrong for at least two out of three.
3. **Retrying an identical prompt after a policy refusal, repeatedly.** §5.2 — a materially different
   prompt, or escalation, not five identical tries.
4. **Applying infra-error retry policy (M2-L14) to refusals without checking whether it helps.**
5. **No circuit breaker on a dependency that can go down.** §5.3 — the blast radius becomes traffic
   volume, not just outage duration.
6. **Trusting a keyword-based refusal detector without measuring its error rate on your own content.**
7. **Silently returning an empty response instead of an explicit failure.** §5.5 — a fourth, separate
   failure mode.
8. **Not checking `finish_reason` before treating a short response as complete** (M4-L15).
9. **Letting users retry manually into an open circuit breaker**, recreating the retry storm the breaker
   exists to prevent.
10. **Never revisiting refusal/error classification as the model or provider changes.** Phrasing and
    behaviour drift; retest.

| Symptom | Likely cause | Fix |
|---|---|---|
| Legitimate answers treated as failures | Refusal detector false-positiving on domain vocabulary | Tighten detection; test against real domain content |
| Users report "the bot just repeats itself" | Identical retries after a policy refusal | Change the prompt materially, or escalate, instead of repeating it |
| An outage lasts far longer than the actual incident | No circuit breaker; retry storm | Add a breaker; short-circuit locally when open |
| Support tickets about "broken bot" after a decline | Generic error message masking a policy refusal | Give a clear reason and an alternative path |
| A response looks complete but is missing content | Silent failure / truncation, not checked | Check `finish_reason`; never treat empty as valid without cause |

---

## 9. Security, privacy, reliability, cost

- **Reliability.** A circuit breaker bounds the visible impact of an outage to close to its real
  duration, instead of amplifying it through thousands of individual retry cycles (§5.3).
- **Reliability.** Refusal and infra-error detection must be separate checks. Conflating them means a
  refusal gets treated as retry-worthy (wasting budget) or an infra error gets treated as final (denying
  a user something that would have worked on retry).
- **Cost.** Retrying an identical prompt after a policy refusal spends budget for a return measured in
  single-digit percentage points per attempt (§5.2). Bound it separately from infra-error retries.
- **Cost.** An open circuit breaker turns thousands of doomed upstream calls into a handful of probes —
  §7.3 measured a 99.96% reduction for one stated scenario.
- **Security.** Do not attempt to route around a policy refusal by automatically rephrasing until it
  succeeds — that pattern is functionally an injection attempt against your own system's safety training,
  not a legitimate retry.
- **Privacy.** Log the failure *class* (refusal, infra error, empty) alongside the incident, not just
  "failed" — without it, you cannot later tell whether a spike was an outage or a policy issue.

---

## 10. Exercises

### Exercise 1 — Beginner (~20 min)

1. Name the three failure classes this lesson distinguishes from a validation failure (M5-L07).
2. Why does a refusal usually arrive with a normal HTTP status code?
3. Which failure class is generally worth retrying with backoff, and which is not?
4. What does a circuit breaker's "half-open" state do?
5. Give one reason a single generic error message is a poor design choice.

### Exercise 2 — Intermediate (~40 min)

1. Run the lab. Report the false-positive and false-negative counts from section 1 and name which
   specific samples were misclassified.
2. Add three new samples of your own (a genuine refusal, legitimate content with refusal-shaped words, and
   a capability limit) and report how the detector handles each.
3. Using section 2's model, compute how many attempts it would take for cumulative refusal-retry success
   to exceed 50%, and comment on whether that budget is realistic.
4. Change section 3's traffic rate and outage duration to a scenario from your own experience (or a
   plausible one) and recompute the breaker's savings.
5. Design the fallback message for each of the four rows in §5.4's table for a system of your choice.

### Exercise 3 — Challenge (~50 min)

1. Build a `classify_failure(response, status_code)` function that returns one of `refusal`,
   `capability_limit`, `infra_error`, `empty`, or `ok`, and test it against a set of at least 15 samples
   you construct, including adversarial edge cases.
2. Implement a real circuit breaker (closed/open/half-open) as a small class with a configurable trip
   threshold and probe interval, and write a test simulating an outage that exercises all three states.
3. Design a retry policy that treats refusals and infra errors differently in the same code path — bound
   each independently, and justify the bounds with arithmetic like §5.2's.
4. Extend the lab's section 1 detector into a small scored heuristic (multiple weighted signals instead of
   one keyword list) and measure whether it improves the false-positive/false-negative counts on your own
   test set.
5. Write the incident postmortem for §6, covering all three incidents in one document, with the specific
   fix that would have prevented each.

---

## 11. Quiz

*(Answers: [`answer-keys/module-05-answers.md`](../../answer-keys/module-05-answers.md#m5-l14).)*

**Q1.** In §7.1, two legitimate answers were wrongly flagged as refusals. The reason was:

- A. The detector had a bug in its string comparison.
- B. The model actually refused, but the detector reported it as legitimate.
- C. The domain content itself used words like "unable to" that are also refusal markers, unrelated to the model actually refusing.
- D. The samples were malformed JSON.

**Q2.** Per this lesson, an empty response and an infrastructure error should be treated as:

- A. Two separate failure classes requiring their own detection, not instances of "the model refused."
- B. The same thing, since both result in no usable answer.
- C. Refusals, since the model did not provide the requested content.
- D. Validation failures, per M5-L07.

**Q3.** After 5 identical retry attempts, cumulative success reached about 99% for an infra error and
about 14% for a policy refusal. This gap exists because:

- A. The refusal detector was miscalibrated.
- B. Providers rate-limit refusal retries more aggressively.
- C. Five attempts is too few to draw any conclusion in either case.
- D. A refusal is closer to the model's stable, repeatable answer than to noise around a right answer, unlike a transient infra failure.

**Q4.** The generally correct response to a genuine policy refusal is:

- A. Retry the identical prompt with exponential backoff, per M2-L14.
- B. Do not repeat the identical request — instead rephrase with more context, offer an alternative, or escalate.
- C. Increase the retry budget until the refusal succeeds.
- D. Treat it as a transient failure and wait before retrying.

**Q5.** A circuit breaker reduces wasted upstream attempts during an outage mainly by:

- A. Short-circuiting new requests locally once it trips, instead of letting every request retry against a dependency that cannot answer.
- B. Increasing the number of retries per request to improve the odds of success.
- C. Caching every possible response in advance.
- D. Blocking all users from making any request during the outage.

**Q6.** In §7.3's scenario, wasted upstream attempts fell from 18,000 to 8 with a breaker. What happened
to the 6,000 users during the outage?

- A. Most of them received no response of any kind.
- B. They were queued until the outage ended.
- C. Every one of them still received a response in both scenarios; only where that response came from, and how quickly, changed.
- D. Only the first 8 users received a response.

**Q7.** Echoing M5-L13's finding about filters, a keyword-based refusal detector is an imperfect tool
because:

- A. It requires a live model to run.
- B. It only works on English text.
- C. It is too slow for production use.
- D. It misfires in both directions — missing real refusals phrased without common markers, and flagging legitimate content that happens to share the same words.

**Q8.** M5-L07 distinguished transient from systematic validation failures. This lesson's refusal/error
distinction is best understood as:

- A. A replacement for M5-L07's classification.
- B. A parallel classification for a different failure surface — what the model or infrastructure returned, rather than whether output validated a schema.
- C. Identical to M5-L07's transient/systematic split, just renamed.
- D. Only relevant once M5-L07's repair loop has already failed.

**Q9.** The "capability_limit" sample in §7.1 was missed by the detector because:

- A. It was not actually a refusal at all.
- B. Capability limits cannot be detected by any method.
- C. It contained none of the detector's specific marker phrases, despite functioning as a refusal.
- D. The sample was empty.

**Q10.** The purpose of a circuit breaker's half-open state is to:

- A. Periodically send a limited probe to test whether the dependency has recovered, without resuming full traffic immediately.
- B. Resume full traffic immediately after any single successful probe.
- C. Never test the dependency again until manually reset.
- D. Reject all requests permanently once tripped, with no recovery path.

**Q11.** Retrying a safety refusal is usually a worse use of budget than retrying a timeout because:

- A. Refusals are more expensive per attempt than timeouts.
- B. The refusal is close to a repeatable decision, so most of the retry budget buys almost no additional chance of success.
- C. Timeouts never actually recover on retry.
- D. Refusals count against a different, unrelated budget.

**Q12.** The general principle this lesson establishes is:

- A. All failures should be retried with the same backoff policy for consistency.
- B. Refusals should always be escalated to a human immediately, with no exceptions.
- C. Circuit breakers are unnecessary if retries are bounded per request.
- D. Match the response to the failure class: retry transient errors, use a different strategy for refusals, and short-circuit during sustained outages.

**Q13.** *(Written, rubric-graded.)* In under 150 words: your team's support bot currently returns "Sorry,
something went wrong. Please try again." for every failure. State the three failure classes this conflates,
the concrete harm of merging them, and what you would change first.

---

## 12. Revision notes

- **A refusal, an infrastructure error, and an empty/malformed response are three separate failure
  classes**, each needing its own detection — none of them is the same problem as a validation failure
  (M5-L07).
- **A refusal usually arrives as a normal, successful-looking response.** Nothing at the transport layer
  flags it; your code must recognise it from content.
- **A keyword-based refusal detector misfires in both directions.** Measured: 1 of 4 genuine refusals
  missed, 2 of 3 legitimate answers wrongly flagged, in a small hand-built test set.
- **Retry-worthiness has a number.** Measured: 5 identical retries take an infra error to ~99% cumulative
  success and a policy refusal to only ~14%. Same cost, very different return.
- **A circuit breaker bounds cost during a sustained outage.** Measured: 18,000 wasted upstream attempts
  down to 8 — a 99.96% reduction — with every user still served, just from a faster, honest fallback.
- **Never retry an identical prompt repeatedly after a policy refusal.** Change something material, or
  escalate.
- **Match the fallback message to the failure class.** A single generic error message is wrong for at
  least two of the four classes in §5.4's table.
- **Silent failure is its own defect**, distinct from all of the above — check `finish_reason` (M4-L15)
  before treating a short or empty response as valid.

---

## 13. Completion checklist

- [ ] I classify failures as refusal, infra error, or empty/malformed before deciding how to respond.
- [ ] My refusal detection has been tested against legitimate content that shares refusal-shaped words.
- [ ] I do not retry an identical prompt repeatedly after a policy refusal.
- [ ] I have a circuit breaker on any dependency that can go down, with a stated trip threshold and probe interval.
- [ ] My fallback messages differ by failure class, not one generic message for all of them.
- [ ] I check `finish_reason` before treating a short response as complete.
- [ ] I log failure class alongside every incident, not just "failed."
- [ ] I scored 10/13 on the quiz.

---

## 14. References

- Nygard, M. T., *Release It!* — the circuit breaker pattern.
  <https://pragprog.com/titles/mnee2/release-it-second-edition/> `[UNVERIFIED]`
- Fowler, M., *CircuitBreaker*. <https://martinfowler.com/bliki/CircuitBreaker.html> `[UNVERIFIED]`
- Anthropic — usage policies and refusal behaviour.
  <https://docs.anthropic.com/en/docs/resources/glossary> `[UNVERIFIED]`

---

## 15. Next lesson

→ [M5-L15 — Token Accounting and Cost Calculation](M5-L15-token-accounting.md)

You can now classify a failure and respond to it correctly. Next: putting an exact number on what every
request costs — including the retries, refusals and fallback calls this lesson just gave you a policy
for.
