# M8-L12 — Idempotency and Duplicate-Action Prevention

| | |
|---|---|
| **Lesson ID** | M8-L12 |
| **Difficulty** | 3 (Advanced) |
| **Estimated study time** | 2.0 hours |
| **Prerequisites** | [M8-L11](M8-L11-read-only-vs-state-changing.md) |

---

## 1. Learning objectives

1. **Implement** an idempotency key mechanism that makes a retried state-changing action safe by
   construction, not by luck.
2. **Demonstrate** that a genuinely new request, with its own key, still executes normally rather than
   being blocked by the mechanism.
3. **Identify** the specific pitfall of generating a fresh idempotency key on every retry, and explain why
   it defeats the mechanism entirely.
4. **Distinguish** an idempotency key's request-level protection from M8-L06's business-level scoping, and
   explain why a real system typically needs both.
5. **Diagnose**, from a described incident, whether a duplicate action resulted from a missing idempotency
   key or from a key that was generated incorrectly.

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **Idempotency key** | A unique identifier generated once per logical attempt, reused across its retries. |
| **Idempotency store** | A record mapping each seen idempotency key to the result it already produced. |
| **Logical attempt** | One intended action, potentially represented by multiple retried calls sharing one key. |
| **Request-level protection** | Idempotency's own scope: is this specific call a retry of one already handled? |
| **Business-level scoping** | M8-L06's own scope: has this real-world fact already happened, across any past request? |

---

## 3. Plain-language explanation

### 3.1 M8-L11 identified the risk; this lesson removes it deliberately

M8-L11 showed that a state-changing action's safety under retry depends on what the action happens to do
internally — some tolerate a repeat by luck, most don't. This lesson builds the mechanism that makes safety
deliberate: an idempotency key, checked before the underlying action ever runs a second time for the same
logical attempt.

### 3.2 The same key, retried, produces exactly one real effect

§7.1 retries the identical call three times with one key generated up front. **Only the first call actually
executes `issue_refund()`; the second and third return the cached result untouched.** Directly contrasted
with M8-L11's own retry — $75 for a $25 refund with no key at all — this lesson's mechanism produces exactly
$30 for three retries of one $30 refund.

### 3.3 A new key for a new request still does real work

§7.2 doesn't stop at proving the mechanism blocks duplicates — it confirms the mechanism doesn't block
*everything*. A genuinely different request, with its own key, executes normally and adds a real, second
entry to the log.

### 3.4 The mechanism is only as good as how the key is generated

§7.3 demonstrates the single most important, easy-to-miss failure mode: generating a *fresh* key on every
retry, rather than reusing one key across all retries of the same attempt, produces the exact same triple
payout M8-L11 showed for no protection at all — because from the mechanism's point of view, three unique
keys are indistinguishable from three genuinely separate requests.

### 3.5 Idempotency and M8-L06's scoping check answer different questions

§7.4 draws the line explicitly: an idempotency key asks whether *this specific call* is a retry; M8-L06's
own business-level check asks whether *this real-world fact* has already happened, regardless of which
request is asking. Neither one substitutes for the other.

---

## 4. Analogy

**A claim ticket at a dry cleaner, versus the shop's own record of whose clothes are whose.** A claim ticket
given to you at drop-off is the idempotency key: if you hand back the *same* ticket twice, the shop gives you
the *same* garment both times — it doesn't clean and re-tag it again just because you asked twice, and if you
lose the ticket and get issued a brand-new one for the same visit, the shop has no way to know it's really
the same garment, and might process it as a second, separate drop-off. The shop's own internal record — this
customer's coat, dropped off this date — is the business-level check: it answers "has this customer's coat
already been cleaned this week," a different, broader question than "is this specific ticket a duplicate of
one already redeemed."

### Where the analogy breaks

- **A claim ticket is a physical object that can't trivially be reissued at will.** §7.3's fresh-key pitfall
  is exactly what happens when a system makes that mistake anyway — nothing structurally prevents a caller
  from generating a new key per attempt, which is precisely why it's a real, easy-to-make error.
- **A dry cleaner's shop record is usually a single, simple lookup.** M8-L06's own business-level check
  needed a carefully-scoped key (customer AND order together) to avoid a different failure mode entirely —
  the two mechanisms solve different problems and can each be implemented well or badly on their own terms.

---

## 5. Detailed technical explanation

### 5.1 A repeated key returns a cached result, never re-executing the action

`[REAL, measured]` §7.1 called `issue_refund_idempotent()` three times with the identical key, generated
once before the first attempt. **Only the first call's result came from actually running `issue_refund()`;
the second and third calls' results were explicitly labeled as returned from cache, and `REFUND_LOG` shows
exactly one entry.** The underlying action's own repeat behavior — whether it happens to be safe or not,
per M8-L11 — becomes irrelevant, because it is never invoked a second time for that key at all.

### 5.2 The mechanism distinguishes retries from genuinely new requests

`[REAL, measured]` §7.2 issued a second, different refund under a different key. **It executed normally,
adding a real second entry to `REFUND_LOG`.** This confirms the mechanism's actual job: not blocking
refunds in general, only recognizing and short-circuiting a specific key it has already processed.

### 5.3 A fresh key per retry reproduces the exact failure the mechanism exists to prevent

`[REAL, measured]` §7.3 generated a brand-new UUID on every one of three attempts for what was meant to be
a single $20.00 refund. **Three entries appeared in `REFUND_LOG`, totaling $60.00 — the identical failure
mode M8-L11 demonstrated with no idempotency mechanism at all.** The idempotency store itself worked
correctly at every step — it simply never saw the same key twice, because there never was a repeated key
to recognize. **The mechanism's guarantee depends entirely on the caller generating one key per logical
attempt and reusing it across that attempt's own retries — a responsibility the mechanism cannot enforce
from the inside.**

### 5.4 Two different questions, both often necessary

`[REAL reasoning]` §7.4 states the distinction directly: an idempotency key answers "is this specific call
a retry of one already handled," a request-level question the caller's own retry behavior determines.
M8-L06's business-level check answers "has this real-world fact already happened, across any request at
all" — a question about the state of the world, independent of which specific call is asking. **A system
using only idempotency keys remains vulnerable to M8-L06's own scoping risk (a genuinely new request,
correctly using a new key, asking for something that already happened at the business level); a system
using only business-level checks remains vulnerable to this lesson's own retry risk within a single logical
attempt.**

### 5.5 Assumptions and limitations

- `IDEMPOTENCY_STORE` is an in-memory dict in this lab — a real system needs a persistent, durable store
  that survives a crash or restart between retries for the guarantee to hold in practice.
- This lesson does not cover how long a key should remain valid before being safely forgotten, what happens
  if two genuinely concurrent requests race on the same key (M8-L13's own concurrency territory), or how a
  real client library generates and attaches keys automatically rather than requiring each caller to manage
  them explicitly, as this lab's examples do for clarity.

---

## 6. Worked example — the payment retry that generated a fresh key every time

**The system.** A payment-processing client library automatically retries a failed request up to three
times, attaching an idempotency key to each request as a defensive measure, following the provider's own
documented best practice.

**The incident.** The library's retry logic called a helper function that generated a new random idempotency
key inline, once per HTTP request attempt — meaning each of the three retries carried a *different* key.
When a request genuinely timed out after the payment had, in fact, already succeeded, the retries did not
recognize themselves as repeats of the same attempt: each key was new to the payment provider's own
idempotency store, and each was processed as a fully separate, real charge.

**Why this matches §5.3 exactly.** This is §7.3's own pitfall verbatim, at production scale: the mechanism
the team believed protected them was implemented in a way that could never actually trigger, because the
key was regenerated on every attempt instead of once per logical request.

**Three defects the incident revealed:**

| # | Defect | Consequence |
|---|---|---|
| 1 | The idempotency key was generated inside the retry loop, once per HTTP attempt | Every retry looked, to the provider's own idempotency store, like a genuinely new request |
| 2 | No test exercised what happened when a request timed out after actually succeeding | The gap was invisible until a real timeout coincided with a real, already-processed charge |
| 3 | The team believed the mechanism protected them because a key was present on every request | Presence of *a* key was mistaken for correct *reuse* of *the same* key across retries |

### The fix

**Generate the idempotency key once, outside the retry loop, before the first attempt**, per §5.3 — and
pass that identical key to every retry of the same logical request.

**Test the specific case a timeout followed by an already-successful action represents**, per §6 — this is
exactly the scenario idempotency keys exist to make safe, and it needs to be exercised directly, not assumed
to work because a key is present somewhere in the code.

**The general rule.** **An idempotency key's protection comes entirely from being reused correctly across
retries of the same attempt — a key that is present but regenerated on every call provides the appearance
of protection without any of its substance, and this specific mistake is common precisely because the code
still "has" an idempotency key at every step.**

---

## 7. Practical activity

**File:** [`labs/m8/l12_idempotency_duplicate_prevention.py`](../../labs/m8/l12_idempotency_duplicate_prevention.py)

**No API key, no network, no third-party dependencies.** Runs in well under a second.

```bash
source .venv/bin/activate
python labs/m8/l12_idempotency_duplicate_prevention.py
```

### 7.2 Expected output

`[EXECUTED]` — 2026-09-10, Python 3.10.11 (pure standard library).

```text
============================================================================
1. THE SAME KEY, RETRIED THREE TIMES: EXACTLY ONE REAL REFUND
============================================================================
  A caller generates one idempotency key ('req-a1b2c3') before its
  first attempt, and reuses the SAME key across all retries of that
  SAME logical attempt -- exactly as a real client library would:

    attempt 1: issue_refund_idempotent('req-a1b2c3', 'O-4001', 30.0) -> 'refund of $30.00 issued for O-4001'
    attempt 2: issue_refund_idempotent('req-a1b2c3', 'O-4001', 30.0) -> 'refund of $30.00 issued for O-4001 [returned from cache -- issue_refund() was NOT called again]'
    attempt 3: issue_refund_idempotent('req-a1b2c3', 'O-4001', 30.0) -> 'refund of $30.00 issued for O-4001 [returned from cache -- issue_refund() was NOT called again]'

  REFUND_LOG after 3 retries with the SAME key: [('O-4001', 30.0)]
  Total refunded: $30.00 -- exactly one $30.00 refund,
  not three, despite three separate calls. Contrast this directly
  with M8-L11's own retry demonstration, which produced $75.00 for a
  single intended $25.00 refund using the SAME underlying action with
  no idempotency key at all.

============================================================================
2. A GENUINELY NEW REQUEST STILL EXECUTES FOR REAL
============================================================================
  A genuinely different request, its own key ('req-d4e5f6'):
    issue_refund_idempotent('req-d4e5f6', 'O-4002', 55.0) -> 'refund of $55.00 issued for O-4002'

  REFUND_LOG now: [('O-4001', 30.0), ('O-4002', 55.0)]

  The mechanism did not block this refund -- it only recognized and
  short-circuited RETRIES of a request it had already seen under the
  SAME key. A new key for a new request executes normally, exactly as
  it should.

============================================================================
3. THE PITFALL: A FRESH KEY EVERY RETRY DEFEATS THE MECHANISM ENTIRELY
============================================================================
  The SAME retry scenario as section 1, but generating a brand-new
  key on every attempt instead of reusing one:

  REFUND_LOG: [('O-4003', 20.0), ('O-4003', 20.0), ('O-4003', 20.0)]
  IDEMPOTENCY_STORE now has 3 distinct keys.
  Total refunded: $60.00 -- three $20.00 refunds, $60.00 total,
  for what was meant to be a single $20.00 refund.

  The idempotency mechanism itself is not broken -- it correctly
  never saw the same key twice, because there NEVER WAS a repeated
  key to recognize. Idempotency protection depends entirely on the
  CALLER generating one key per logical attempt and reusing it across
  retries -- a fresh key per call is indistinguishable, from the
  mechanism's point of view, from three genuinely different requests.

============================================================================
4. IDEMPOTENCY KEYS VS. M8-L06'S BUSINESS-LEVEL SCOPING: DIFFERENT QUESTIONS
============================================================================
  M8-L06's check_already_refunded(customer, order_id) answers: 'has
  THIS REAL-WORLD ORDER already been refunded, ever, in any past
  conversation?' -- a business-level fact, checked against history.

  This lesson's idempotency key answers a narrower, different
  question: 'is THIS SPECIFIC CALL ATTEMPT a retry of one already in
  flight or already completed?' -- a request-level fact, checked
  against a key the CALLER controls and must reuse correctly.

  A real system typically needs BOTH: idempotency keys protect a
  single logical request from being duplicated by network retries
  within its own attempt; M8-L06's business-level check protects
  against a genuinely NEW request (a new key, a new conversation)
  asking for something that, at the business level, already
  happened. Neither replaces the other.

============================================================================
5. WHAT THIS LAB IS AND IS NOT
============================================================================
  REAL: every REFUND_LOG entry, every IDEMPOTENCY_STORE lookup, and
  the three-way contrast (correct reuse, a new request, the fresh-key
  pitfall) are genuinely computed by calling these functions -- not
  scripted to produce a predetermined narrative.

  ILLUSTRATIVE: this lab's IDEMPOTENCY_STORE is an in-memory dict --
  a real system needs a persistent, durable store (surviving a crash
  or restart between retries) for the guarantee to hold in practice,
  which this lab does not model.

  NOT SHOWN: how long an idempotency key should remain valid before
  being safely forgotten; what happens if two genuinely concurrent
  requests race on the same key (M8-L13's own concurrency territory);
  and how a real client library generates and attaches idempotency
  keys automatically rather than requiring each caller to manage them
  by hand, as this lab's examples do explicitly for clarity.

Done.
```

### 7.3 Reading the result

**Section 1 is the payoff M8-L11 was building toward.** The exact same kind of retry that produced $75 for
a $25 refund in that lesson produces exactly $30 for a $30 refund here — the only difference is a key,
generated once and reused.

**Section 3 is the lesson's most important result, and it's deliberately placed right after section 1's
success.** It would be easy to walk away thinking "just add an idempotency key" solves the problem
completely; section 3 shows the mechanism can be present in the code and still provide zero protection, for
a reason that has nothing to do with the mechanism's own implementation.

**Section 4 prevents a specific, likely misreading.** It would be easy to conclude idempotency keys make
M8-L06's own scoping check unnecessary, or vice versa; the lab states directly that they answer different
questions and a real system generally needs both.

---

## 8. Common mistakes and troubleshooting

1. **Generating a new idempotency key on every retry instead of once per logical attempt.** §5.3, §6 —
   this is the single most damaging mistake this lesson identifies, and it leaves code that "has" a key at
   every step providing no actual protection.
2. **Assuming an idempotency key alone protects against business-level duplicates.** §5.4 — a correctly
   reused key still won't catch a genuinely new request asking for something that already happened; that's
   M8-L06's job.
3. **Assuming M8-L06's business-level scoping alone protects against retry duplication.** §5.4 — that
   check doesn't address a single request's own retries at all; that's this lesson's job.
4. **Treating an in-memory idempotency store as sufficient for production use.** §5.5 — a store that
   doesn't survive a crash between retries can't provide the guarantee it's meant to.
5. **Not testing the specific scenario of a timeout following an already-successful action.** §6 — this is
   exactly the case idempotency keys exist to protect, and it needs to be exercised directly.

| Symptom | Likely cause | Fix |
|---|---|---|
| A state-changing action is duplicated despite an idempotency key being present in the code | The key is being generated fresh on every retry instead of reused from the original attempt | Move key generation outside the retry loop, generating it once per logical attempt, per §5.3, §6 |
| A legitimate, new request is being blocked or merged with an unrelated earlier one | Two genuinely different requests are sharing the same idempotency key by mistake | Confirm each distinct logical request gets its own, uniquely generated key, per §5.2 |
| A duplicate action occurs even though retries correctly reuse one key | The idempotency store may not have survived a crash or restart between retries | Move to a persistent, durable idempotency store, per §5.5 |
| A duplicate is caught within one request's retries but a business-level duplicate still occurs across separate requests | Idempotency keys alone were relied on, without a business-level scoping check | Add M8-L06's own scoped check alongside idempotency keys, per §5.4 |

---

## 9. Security, privacy, reliability, cost

- **Reliability.** Generate an idempotency key once per logical attempt and reuse it across all retries of
  that attempt — this is the entire mechanism's protection, and it fails silently if violated (§5.3, §6).
- **Reliability.** Use a persistent, durable idempotency store in production — an in-memory store cannot
  provide the guarantee across a crash or restart (§5.5).
- **Reliability.** Combine idempotency keys with M8-L06's own business-level scoping — neither mechanism
  covers the failure mode the other is designed for (§5.4).
- **Cost.** A correctly implemented idempotency mechanism converts a real, measurable duplicate-payout risk
  (§7.1's $75-for-$25 case from M8-L11, now $30-for-$30 here) into a bounded, single execution.

---

## 10. Exercises

### Exercise 1 — Beginner (~20 min)

1. What is an idempotency key, and when should it be generated relative to a request's retries?
2. Why did §7.1's three retries produce exactly one real refund?
3. Why did §7.2's new request execute normally instead of being blocked?
4. What specifically went wrong in §7.3, and why did the idempotency mechanism not catch it?
5. What is the difference between the question an idempotency key answers and the question M8-L06's
   business-level check answers?

### Exercise 2 — Intermediate (~40 min)

1. Run the lab. Confirm §7.1's single refund, §7.2's second real refund, and §7.3's triple refund on your
   own machine.
2. Modify `buggy_retry_with_fresh_key()` to correctly reuse one key across all retries, and confirm this
   produces the same correct single-refund outcome as §7.1.
3. Add a second state-changing tool (not a refund) and implement an idempotent version of it, following
   `issue_refund_idempotent()`'s pattern.
4. Simulate an idempotency key colliding accidentally between two genuinely different requests (not a
   retry), and observe what happens to the second request's result. Is this a realistic risk? Why or why
   not?
5. Using §5.4's distinction, design a combined check for a new scenario that needs both an idempotency key
   and a business-level scoping check, and explain what each one specifically protects against.

### Exercise 3 — Challenge (~50 min)

1. Extend `IDEMPOTENCY_STORE` to record a timestamp per key and implement an expiration policy — after
   how long should a key be safely forgotten, and what determines that duration?
2. Design a solution for the race condition this lesson's own §7.5 flags as not shown: two genuinely
   concurrent calls with the identical key, both arriving before either has finished. What could go wrong,
   and how would you prevent it?
3. Using M8-L05's schema-validation approach, design a way to validate that an idempotency key itself is
   well-formed (e.g., a UUID) before accepting it, and explain what risk this addresses.
4. Research (conceptually) how a real payment API's idempotency-key mechanism is documented to work, and
   compare it to this lesson's `issue_refund_idempotent()`.
5. Using §6's worked example, write a specific test case that would have caught the fresh-key-per-retry bug
   before it reached production.

---

## 11. Quiz

*(Answers: [`answer-keys/module-08-answers.md`](../../answer-keys/module-08-answers.md#m8-l12).)*

**Q1.** Per §7.1's measured result, how many real refunds were issued across three retries using the
identical idempotency key?

- A. Exactly one — the second and third calls returned a cached result instead of executing again.
- B. Three, one per retry.
- C. Zero — all three calls failed.
- D. Two — the first call failed and had to be retried once successfully.

**Q2.** Per §7.2's measured result, what happened when a genuinely different request, using its own key,
was made?

- A. It was blocked because the idempotency store already had an entry.
- B. It raised an exception because two keys existed in the store.
- C. It returned the cached result from the first request in section 1.
- D. It executed normally and added a real, second entry to REFUND_LOG.

**Q3.** Per §7.3's measured result, what happened when a fresh idempotency key was generated on every
retry instead of reusing one?

- A. The mechanism correctly recognized all three attempts as retries and issued only one refund.
- B. Three separate refunds were issued, reproducing the exact duplicate-payout risk from M8-L11 with no idempotency protection at all.
- C. The system crashed due to too many keys.
- D. Exactly two refunds were issued.

**Q4.** Per §5.3, was the idempotency store itself the cause of the failure in section 3?

- A. Yes, the store contained a bug that failed to detect duplicate keys.
- B. Yes, the store's capacity was exceeded.
- C. No — the store worked correctly at every step; it simply never saw the same key twice, because the caller never reused one.
- D. The store was never actually used in section 3.

**Q5.** Per §5.4, what question does an idempotency key answer, as distinguished from M8-L06's
business-level check?

- A. Whether this specific call is a retry of one already handled, as opposed to whether this real-world fact has already happened across any past request.
- B. Whether the customer is authorized to make this request.
- C. Whether the requested amount exceeds a policy cap.
- D. Whether the tool's arguments match its declared schema.

**Q6.** Per §5.4, does this lesson recommend using only idempotency keys or only M8-L06's business-level
scoping, rather than both?

- A. Yes, idempotency keys alone are always sufficient.
- B. Yes, business-level scoping alone is always sufficient.
- C. Neither mechanism is recommended under any circumstances.
- D. No — a real system typically needs both, since neither covers the failure mode the other is designed for.

**Q7.** Per §6's worked example, what specifically caused the payment retry incident?

- A. The payment provider's servers were down.
- B. The idempotency key was generated inline within the retry loop, once per HTTP attempt, rather than once per logical request reused across attempts.
- C. No idempotency key was ever attached to any request.
- D. The customer's payment method was declined.

**Q8.** Per §6, why was this mistake described as easy to make and hard to notice?

- A. Because the bug only occurred once in the system's entire history.
- B. Because idempotency keys are rarely documented by payment providers.
- C. Because the code appeared to have an idempotency key present at every step, which was mistaken for correct reuse of the same key across retries.
- D. Because the retry logic itself was never actually executed.

**Q9.** Per §6, what is the stated general rule this incident illustrates?

- A. An idempotency key's protection comes entirely from being reused correctly across retries — a key that is present but regenerated on every call provides the appearance of protection without any of its substance.
- B. Idempotency keys should never be used with payment systems.
- C. Retry logic should always be disabled for payment requests.
- D. The incident has no generalizable lesson beyond this specific system.

**Q10.** Per §7.5, is `IDEMPOTENCY_STORE` in this lab presented as production-ready as implemented?

- A. Yes, an in-memory dict is presented as fully sufficient for production use.
- B. Yes, but only for low-volume systems.
- C. The lesson does not address this question.
- D. No — the lesson explicitly states a real system needs a persistent, durable store that survives a crash or restart, which this lab's in-memory dict does not model.

**Q11.** Per §7.5, what does this lesson explicitly NOT cover?

- A. The correct single-key retry demonstrated in section 1.
- B. Key expiration policy, concurrent requests racing on the same key, and automatic key generation by a real client library — left as natural extensions or to M8-L13.
- C. The fresh-key pitfall demonstrated in section 3.
- D. The distinction from M8-L06's business-level scoping in section 4.

**Q12.** What is the general lesson this lab demonstrates about idempotency and duplicate-action
prevention?

- A. Any idempotency mechanism, however implemented, automatically prevents all duplicate actions.
- B. Idempotency keys make M8-L06's business-level scoping check unnecessary.
- C. An idempotency key makes a retried action safe deliberately, but only if the caller generates one key per logical attempt and reuses it correctly across retries — a responsibility the mechanism itself cannot enforce.
- D. Idempotency is only relevant for payment systems specifically.

**Q13.** *(Written, rubric-graded.)* In under 150 words: your team's retry logic attaches an idempotency
key to every request, but duplicate actions are still occurring. Based on this lesson, what would you check
first, and why?

---

## 12. Revision notes

- **An idempotency key, generated once and reused across retries, makes a repeated call return a cached
  result instead of re-executing** — measured directly: three retries with one key produced exactly one
  real refund, versus M8-L11's $75-for-$25 with no key at all.
- **A genuinely new request, with its own key, still executes normally** — the mechanism blocks only
  recognized retries, not requests in general.
- **Generating a fresh key on every retry defeats the mechanism entirely, and does so silently** —
  measured directly: three fresh keys for one logical attempt produced three real refunds, an outcome
  indistinguishable from having no idempotency key at all.
- **The idempotency store itself was not the point of failure in that case** — it worked correctly; the
  caller simply never gave it a repeated key to recognize.
- **Idempotency keys (retry-level) and M8-L06's business-level scoping answer different questions**, and a
  real system typically needs both, since neither covers the specific failure mode the other addresses.

---

## 13. Completion checklist

- [ ] I can implement an idempotency key mechanism that caches a result and avoids re-executing an action.
- [ ] I can explain why a genuinely new request still executes despite the mechanism being in place.
- [ ] I can identify the fresh-key-per-retry pitfall and explain why it defeats the mechanism.
- [ ] I can distinguish an idempotency key's request-level protection from business-level scoping (M8-L06).
- [ ] I can diagnose, from a described incident, whether a duplicate resulted from a missing key or an
      incorrectly-generated one.
- [ ] I generate an idempotency key once per logical attempt and reuse it across that attempt's retries.
- [ ] I scored 10/13 on the quiz.

---

## 14. References

- Stripe API documentation, *Idempotent Requests*, for a real, widely-referenced idempotency-key design,
  where available. `[UNVERIFIED]`
- M8-L06's own business-level scoping mechanism, distinguished directly from this lesson's request-level
  mechanism. `[STABLE]`

---

## 15. Next lesson

→ M8-L13 — Retries, Timeouts, Cancellation and Recovery

This lesson made a single retry safe. Next: the broader machinery around it — how many times to retry, how
long to wait, and how to recover cleanly when an action truly cannot complete.
