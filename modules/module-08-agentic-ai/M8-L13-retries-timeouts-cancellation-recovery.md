# M8-L13 — Retries, Timeouts, Cancellation and Recovery

| | |
|---|---|
| **Lesson ID** | M8-L13 |
| **Difficulty** | 3 (Advanced) |
| **Estimated study time** | 2.0 hours |
| **Prerequisites** | M2-L14, [M8-L12](M8-L12-idempotency-duplicate-prevention.md) |

---

## 1. Learning objectives

1. **Implement** a real timeout that bounds how long a caller waits on a hung call, without waiting for
   the underlying work to finish.
2. **Combine** M2-L14's backoff discipline with M8-L12's idempotency key into a single retry mechanism for
   a state-changing action.
3. **Distinguish** an action that can honor a cancellation request mid-execution from one that is atomic
   and cannot be safely interrupted once started.
4. **Implement** an honest recovery path that reports a specific failure, and contrast it with a recovery
   path that silently produces a success-shaped message despite no real effect occurring.
5. **Diagnose**, from a described incident, whether a duplicated or masked failure came from a missing
   timeout, a missing idempotency key, an incorrectly-assumed cancellation point, or a dishonest recovery
   path.

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **Timeout** | A bound on how long a caller waits for a call to complete before giving up. |
| **Backoff** | Waiting progressively longer between retries (M2-L14). |
| **Cancellation** | A request to stop an in-progress action before it completes. |
| **Cancellation point** | A place in an action's own logic where it checks for and can honor a cancellation request. |
| **Recovery path** | What a caller does after an action has definitively failed. |

---

## 3. Plain-language explanation

### 3.1 M2-L14 and M8-L12 each built half of what an agent's tool step needs

M2-L14 built real backoff discipline for retrying a client call. M8-L12 built the idempotency key that
makes retrying a state-changing action safe. §7.2 wires both together into one mechanism, and this lesson
adds three things neither earlier lesson covered on its own: a real timeout, a real cancellation check, and
an honest recovery path.

### 3.2 A timeout bounds the caller's wait, not the work itself

§7.1 doesn't just claim a timeout is enforced — it measures the actual elapsed time and confirms it matches
the requested bound, not the full duration of the underlying call. Getting this measurement right required
a real fix: the first version of the timeout wrapper accidentally waited for the hung call to finish anyway,
because closing its thread pool the ordinary way blocks until every submitted task completes.

### 3.3 Backoff and idempotency solve different halves of the same retry

§7.2 retries a call that genuinely fails twice before succeeding, with real, doubling delays between
attempts — and a real idempotency key that, when the same logical request is retried again afterward,
returns the cached result without a third execution.

### 3.4 Not every action has somewhere to stop

§7.3 shows a genuinely cancellable action — one that checks an external signal between steps and can return
real partial progress — directly beside a genuinely uncancellable one: a refund, called once, either hasn't
happened yet or already has. There is no middle state to interrupt.

### 3.5 A recovery path can lie, and the lie is measurable

§7.4 doesn't just warn that masking a failure is bad practice — it runs two recovery functions against the
identical, permanently-failing action and shows their final messages are text-identical in shape to a real
success, while only one of them actually corresponds to anything having happened.

---

## 4. Analogy

**A doorbell you give up waiting at, a delivery you retry with the same tracking number, and a cake that
can't be half-baked.** Ringing a doorbell and waiting thirty seconds before leaving a note is a timeout — you
decide how long you'll wait, independent of whether someone eventually does answer. Attempting a delivery
three times using the identical tracking number, so the recipient's system recognizes all three attempts as
the same package rather than three separate orders, is retry-plus-idempotency. Checking in on a road trip's
progress and being able to turn back at any rest stop is cancellation with real checkpoints; a cake already
in the oven cannot be "half-un-baked" if you change your mind partway — it either hasn't started or it's
going to finish as a cake, edible or not.

### Where the analogy breaks

- **A doorbell's timeout has no cost to the person who rang it beyond their own waiting.** §7.1's timeout
  leaves the underlying call still running in the background, consuming real resources even after the
  caller has moved on — a cost this analogy doesn't carry.
- **A delivery's tracking number is issued by the shipper, not chosen freshly by the sender each time.** A
  real idempotency key has exactly this property (M8-L12) — generated once, reused by the same sender across
  attempts — which the analogy states but doesn't structurally enforce the way M8-L12's own pitfall did.

---

## 5. Detailed technical explanation

### 5.1 A correct timeout measurement required fixing how the pool was closed

`[REAL, measured]` §7.1's first implementation wrapped the timed call in `with ThreadPoolExecutor(...) as
pool:` — and measured an elapsed time of roughly 600ms against a requested 200ms timeout, because exiting a
`with`-managed executor calls `shutdown(wait=True)` by default, blocking until the hung background task
actually finishes. **Switching to an explicit `pool.shutdown(wait=False)` after catching the timeout fixed
this — the corrected measurement shows the caller waiting almost exactly the requested 200ms**, with the
underlying 600ms call left running independently in the background, exactly as a real timeout should behave.

### 5.2 Backoff and idempotency compose without either mechanism needing to know about the other

`[REAL, measured]` §7.2 ran a call that fails on its first two attempts, retrying with real, measured,
doubling delays (roughly 50ms, then 100ms) before succeeding on the third. **Only one entry appeared in
`REFUND_LOG`.** Retrying the identical logical request afterward, using the same idempotency key, returned
the cached result explicitly marked as needing no further retry. Neither mechanism had to be aware of the
other's existence — backoff governs *when* to try again; the idempotency key governs *whether* trying again
does anything.

### 5.3 A cancellation point is a property of an action's own logic, not something added from outside

`[REAL, measured]` §7.3's `cancellable_bulk_check()` genuinely checked an external flag between each item
and stopped after processing exactly two of five requested items once that flag was set. **This is
contrasted directly against `issue_refund()` and `flaky_issue_refund()`, which have no such checkpoint at
all** — each is a single atomic operation with no partial state a "cancel" request could safely interrupt.
Whether an action can be cancelled is not a policy decision made by whoever calls it; it depends on whether
the action's own implementation has somewhere to check.

### 5.4 A dishonest recovery path is measurably indistinguishable from success in its own text

`[REAL, measured]` §7.4 ran two functions against the identical, permanently-failing action, retried the
identical number of times. **The honest version's final message explicitly states failure and that no
refund was issued; the dishonest version's final message reads exactly like a real success — `'refund of
$60.00 issued for O-5003'` — despite `REFUND_LOG` confirming no such entry exists.** A caller (or a human)
reading only the returned string has no way to distinguish the two without independently checking the
underlying system of record.

### 5.5 Assumptions and limitations

- `flaky_issue_refund()` and `always_fails_refund()` are small, deterministic stand-ins for real transient
  and permanent failures — a real system's actual failure modes and timing would differ.
- This lesson does not rebuild M2-L14's jitter and circuit-breaker mechanisms in full (they are referenced,
  not reimplemented), does not cover how a real system decides which errors are worth retrying at all versus
  failing immediately, and does not cover durable checkpointing across a process restart mid-retry (M8-L14).

---

## 6. Worked example — the "successful" batch job that processed nothing

**The system.** A nightly batch job retries a set of failed record-update calls up to five times each, and
reports "batch completed successfully" at the end regardless of outcome, on the theory that individual
record failures are logged elsewhere and shouldn't block the overall job status.

**The incident.** A downstream service was down for several hours, causing every retry of every record in
that night's batch to fail. The job's own recovery logic, after exhausting retries for each record,
returned a generic "processed" status for it anyway — matching the exact shape of a real success — and the
job's final summary reported 100% completion. No record was actually updated. The outage was discovered two
days later, when a report depending on the supposedly-updated data was visibly wrong.

**Why this matches §5.4 exactly.** This is §7.4's own dishonest-recovery pattern at production scale: a
recovery path that, after real retries genuinely exhausted, returned a result indistinguishable in shape
from success, with no separate signal anywhere indicating that nothing had actually happened.

**Three defects the incident revealed:**

| # | Defect | Consequence |
|---|---|---|
| 1 | The recovery path reported the same "processed" status regardless of whether the underlying update actually succeeded | A total outage produced a report identical in shape to a fully successful run |
| 2 | No monitoring distinguished "processed because it succeeded" from "processed because retries were exhausted and the code moved on anyway" | The two very different outcomes were invisible to anyone reading only the job's own summary |
| 3 | The gap was only found when a downstream consumer of the data noticed something was visibly wrong | Detection depended on a secondary system rather than the job's own reporting |

### The fix

**Report failed records as failed, explicitly, per §5.4** — a recovery path's job is to surface what
actually happened, not to produce a summary shaped like success regardless of outcome.

**Route genuinely exhausted retries to an escalation path** (M8-L10's own territory) rather than treating
"retries exhausted" as equivalent to "task complete."

**The general rule.** **A recovery path that reports success regardless of whether anything real happened
is not more resilient than one that reports failure honestly — it is less informative, and the resulting
silence about a real problem tends to be discovered later, and more expensively, than the original failure
would have been.**

---

## 7. Practical activity

**File:** [`labs/m8/l13_retries_timeouts_cancellation_recovery.py`](../../labs/m8/l13_retries_timeouts_cancellation_recovery.py)

**No API key, no network, no third-party dependencies** (uses only the standard library's
`concurrent.futures` and `time`).

```bash
source .venv/bin/activate
python labs/m8/l13_retries_timeouts_cancellation_recovery.py
```

### 7.2 Expected output

`[EXECUTED]` — 2026-09-10, Python 3.10.11 (pure standard library). Millisecond timings vary slightly by
machine; the logical outcomes (which items are checked, which refunds are recorded) are deterministic.

```text
============================================================================
1. A REAL TIMEOUT: GIVING UP ON A HUNG CALL, MEASURED
============================================================================
  call_with_timeout(slow_check_inventory, timeout=0.2s) -> result=None, error='TIMED OUT'
  Actually waited: 208ms (the call itself takes 600ms to finish)

  The caller gave up at the timeout, not at whenever the underlying
  call eventually finishes -- a real, measured bound, not a claim.
  The underlying thread is still running in the background; the
  TIMEOUT decision is about how long the CALLER waits, not about
  stopping the work itself (that is section 3's separate topic).

============================================================================
2. RETRY WITH REAL BACKOFF, PROTECTED BY AN IDEMPOTENCY KEY
============================================================================
  Retrying a flaky refund call with real, measured backoff:

    attempt 1 failed (simulated transient failure (attempt 1)) -- waiting 50ms before retry
    attempt 2 failed (simulated transient failure (attempt 2)) -- waiting 100ms before retry

  Final result: 'refund of $40.00 issued for O-5001'
  Total wall-clock time across all attempts and waits: 172ms
  REFUND_LOG: [('O-5001', 40.0)] -- exactly one entry, from the one attempt that succeeded.

  Retrying the SAME logical request again (same idempotency key):
    retry_with_backoff('req-retry-1', ...) -> 'refund of $40.00 issued for O-5001 [cached, no retry needed]'
  REFUND_LOG unchanged: [('O-5001', 40.0)]

============================================================================
3. CANCELLATION: SOME ACTIONS CAN STOP MID-WAY; SOME CANNOT
============================================================================
  cancellable_bulk_check() cancelled mid-way -- items actually checked: ['Desk Lamp', 'Wireless Mouse'] (of 5 requested)

  Contrast: issue_refund() and flaky_issue_refund() have NO cancellation
  point at all -- each is a single, atomic operation. Once called,
  there is no partial state to stop at; it either has not started
  (safe to simply not call) or has already completed (too late to
  cancel). Treating a state-changing action as if it could be safely
  interrupted mid-way, when its own logic has no such checkpoint, is
  a real design error, not a matter of adding a flag after the fact.

============================================================================
4. RECOVERY: AN HONEST FAILURE, NOT A SILENT ONE
============================================================================
  Honest recovery:    'FAILED after 3 attempts -- no refund was issued for O-5002'
  REFUND_LOG contains an entry for O-5002? False

  Dishonest recovery: 'refund of $60.00 issued for O-5003'
  REFUND_LOG contains an entry for O-5003? False

  Both functions retried the identical, permanently-failing action
  the identical number of times. The dishonest version's final
  message is INDISTINGUISHABLE, in its own text, from a real success
  -- but no refund was ever recorded. A caller (or a human) reading
  only that string has no way to tell the two apart without checking
  the underlying system of record directly.

============================================================================
5. WHAT THIS LAB IS AND IS NOT
============================================================================
  REAL: the timeout in section 1 is a genuine, measured wall-clock
  bound; the backoff delays in section 2 genuinely double and are
  genuinely waited; the cancellation in section 3 genuinely stops a
  real loop mid-way based on a real, externally-set flag;
  and both recovery paths in section 4 genuinely exhaust real
  retries against a function that genuinely always raises.

  ILLUSTRATIVE: flaky_issue_refund() and always_fails_refund() are
  small, deterministic stand-ins for real transient and permanent
  failures -- a real system's actual failure modes and timing would
  differ. The specific delay values are this lesson's own
  illustration, not a tuned recommendation for any real system.

  NOT SHOWN: M2-L14's own jitter and circuit-breaker mechanisms in
  full (referenced, not rebuilt here); how a real system decides
  which errors are worth retrying at all versus failing immediately;
  and durable checkpointing across a process restart mid-retry
  (M8-L14's own topic).

Done.
```

### 7.3 Reading the result

**Section 1's own bug-and-fix, documented honestly in §5.1, is more convincing than a clean result would
have been.** A timeout that quietly waits for the hung call anyway is a subtle, easy mistake — closing a
thread pool the ordinary way is exactly the kind of code that looks correct until measured.

**Section 4's dishonest message is the sharpest single result in this lesson.** It isn't a vague warning
about "silent failures" — it's a specific string, produced by real code, that reads exactly like a real
success while corresponding to nothing having happened. That specificity is what makes §6's worked example
land.

**Sections 2 and 3 show two mechanisms that don't need to coordinate to compose correctly.** Backoff timing
and idempotency protection operate on completely different questions (when to try again, whether trying
again does anything), and neither needed to be aware of the other to work together correctly.

---

## 8. Common mistakes and troubleshooting

1. **Wrapping a timed call in a context-managed thread pool without checking how it closes.** §5.1 — the
   ordinary `with`-block exit can silently wait for a hung task to finish, defeating the timeout it appears
   to enforce.
2. **Adding retries without an idempotency key, or an idempotency key without retries.** §5.2 — the two
   mechanisms solve different halves of the same problem and neither substitutes for the other.
3. **Assuming any action can be safely cancelled if you just add a check somewhere.** §5.3 — a cancellation
   point has to exist in the action's own logic; an atomic operation has nowhere to check.
4. **Returning a success-shaped message after retries are exhausted, "to keep things simple."** §5.4, §6 —
   this is measurably indistinguishable from a real success in its own text, which is exactly the danger.
5. **Reporting a task as "complete" without distinguishing whether it succeeded or merely finished
   attempting.** §6 — completion and success are different claims, and conflating them hides real failures.

| Symptom | Likely cause | Fix |
|---|---|---|
| A timeout is set, but the caller still waits far longer than the configured value | The thread pool's default shutdown behavior is waiting for the hung task to finish anyway | Use shutdown(wait=False) after a timeout, per §5.1 |
| A state-changing action is duplicated despite retry logic including a delay between attempts | Backoff alone was implemented, with no idempotency key protecting the underlying action | Add an idempotency key (M8-L12) alongside the backoff delay, per §5.2 |
| An attempt to "cancel" a state-changing action has no effect, or worse, leaves inconsistent state | The action has no real cancellation point — it is atomic, and was already committed or never started | Confirm whether the action can genuinely honor cancellation before assuming it can, per §5.3 |
| A batch or task reports success even though the underlying work clearly did not happen | The recovery path returns a success-shaped result regardless of whether retries actually succeeded | Report failures explicitly and distinguish "succeeded" from "exhausted retries," per §5.4, §6 |

---

## 9. Security, privacy, reliability, cost

- **Reliability.** Verify that a timeout mechanism actually returns at the configured bound, not at
  whenever the underlying call happens to finish (§5.1).
- **Reliability.** Pair retries with an idempotency key for any state-changing action — backoff alone does
  not prevent duplication (§5.2).
- **Reliability.** Confirm an action has a genuine cancellation point before assuming a cancellation
  request can be honored safely (§5.3).
- **Reliability.** Report exhausted retries as an honest failure, distinguishable from success — a
  recovery path that masks failure is discovered later and at greater cost (§5.4, §6).

---

## 10. Exercises

### Exercise 1 — Beginner (~20 min)

1. What was the bug in this lesson's first timeout implementation, and what caused it?
2. Why does backoff alone not prevent a state-changing action from being duplicated?
3. What distinguishes a cancellable action from one that cannot be safely cancelled?
4. Why is the dishonest recovery function's output described as dangerous specifically?
5. What is the difference between "the task completed" and "the task succeeded"?

### Exercise 2 — Intermediate (~40 min)

1. Run the lab. Confirm the timeout measurement in §7.1, the backoff-plus-idempotency result in §7.2, and
   the two recovery paths in §7.4 on your own machine.
2. Modify `call_with_timeout()` to use the buggy `with`-block version and confirm you reproduce the
   original ~600ms measurement described in §5.1.
3. Add a third recovery function that retries honestly but returns a partial-success message distinct from
   both `honest_recovery()` and `dishonest_recovery()`, and explain what new information it should convey.
4. Change `CANCEL_AFTER_ITEMS` and confirm `cancellable_bulk_check()`'s reported partial progress changes
   correspondingly and deterministically.
5. Using §5.3's distinction, classify three actions from a system you're familiar with as genuinely
   cancellable or atomic, and justify each classification.

### Exercise 3 — Challenge (~50 min)

1. Design a combined function that applies a timeout, backoff-with-idempotency, and honest recovery to a
   single state-changing action, integrating all three mechanisms from this lesson into one call.
2. Using M2-L14's own circuit-breaker concept, propose how a circuit breaker should interact with this
   lesson's idempotency-protected retry — should it prevent even the first attempt in some circumstances?
3. Design a recovery path that distinguishes at least three outcomes (success, transient failure worth
   retrying later, permanent failure) with three genuinely different return values, not just two.
4. Research (conceptually) how a real workflow orchestration system represents cancellation for long-running
   tasks, and compare it to this lesson's flag-checking mechanism.
5. Using §6's worked example, design a monitoring check that would have caught the batch job's 100%
   "completion" rate masking a total outage, before the downstream report surfaced the problem.

---

## 11. Quiz

*(Answers: [`answer-keys/module-08-answers.md`](../../answer-keys/module-08-answers.md#m8-l13).)*

**Q1.** Per §5.1, what caused the lesson's first timeout implementation to measure roughly 600ms against a
requested 200ms timeout?

- A. Exiting a `with`-managed ThreadPoolExecutor calls shutdown(wait=True) by default, blocking until the hung background task actually finishes.
- B. The timeout value itself was set incorrectly in the code.
- C. The underlying call was modified to run faster than expected.
- D. Python's timeout mechanism does not work at all.

**Q2.** Per §7.1's measured result after the fix, how did the actual elapsed time compare to the requested
timeout?

- A. The elapsed time could not be measured after the fix.
- B. The elapsed time still matched the full 600ms duration.
- C. The elapsed time was reduced to nearly zero.
- D. The elapsed time was close to the requested 200ms bound, not the full 600ms the underlying call takes.

**Q3.** Per §7.2's measured result, how many real refund entries were recorded across the retried, flaky
call's three attempts?

- A. Three, one per attempt.
- B. Exactly one, from the attempt that succeeded.
- C. Zero — all attempts failed.
- D. Two, from the two failed attempts.

**Q4.** Per §5.2, did the backoff mechanism or the idempotency key need to be aware of the other's
existence to work correctly together?

- A. Yes, the two mechanisms had to be tightly integrated and aware of each other's internal state.
- B. Only the idempotency key needed to know about the backoff mechanism.
- C. No — backoff governs when to try again, and the idempotency key governs whether trying again does anything, and neither needed to know about the other.
- D. Only the backoff mechanism needed to know about the idempotency key.

**Q5.** Per §5.3, what distinguishes `cancellable_bulk_check()` from `issue_refund()` regarding
cancellation?

- A. cancellable_bulk_check() checks an external flag between steps and can stop early with real partial progress; issue_refund() is a single atomic operation with no such checkpoint.
- B. issue_refund() is cancellable, but cancellable_bulk_check() is not.
- C. Both functions are equally cancellable.
- D. Neither function can ever be cancelled under any circumstances.

**Q6.** Per §7.4's measured result, what happened to `REFUND_LOG` after the dishonest recovery function
returned its final message?

- A. It contained a new entry corresponding to the message's claimed refund.
- B. It could not be checked after the dishonest recovery ran.
- C. It was cleared entirely.
- D. It contained no entry corresponding to the message's claimed refund, despite the message reading like a real success.

**Q7.** Per §5.4, why is a caller unable to distinguish the honest and dishonest recovery results by
reading their returned strings alone?

- A. Both strings are identical character-for-character.
- B. The dishonest version's message is shaped exactly like a real success message, with no textual signal distinguishing it from an actual completed refund.
- C. Neither string contains any information at all.
- D. The honest version's message is also misleading.

**Q8.** Per §6's worked example, what happened to the batch job's reported outcome during the outage?

- A. The job correctly reported a failure for every affected record.
- B. The job crashed and reported no outcome at all.
- C. The job reported 100% completion despite no record actually being updated, because its recovery path returned a "processed" status regardless of actual outcome.
- D. The job paused itself automatically until the outage resolved.

**Q9.** Per §6, how was the incident eventually discovered?

- A. A downstream report depending on the supposedly-updated data was visibly wrong, discovered two days later.
- B. The job's own monitoring immediately flagged the failure.
- C. A customer complained directly to engineering within minutes.
- D. The incident was never actually discovered.

**Q10.** Per §6, what is the stated general rule this incident illustrates?

- A. Batch jobs should never use retries under any circumstances.
- B. The incident has no generalizable lesson beyond this specific system.
- C. Monitoring is unnecessary as long as retries are configured correctly.
- D. A recovery path that reports success regardless of whether anything real happened is less informative than one that reports failure honestly, and the resulting silence tends to be discovered later and more expensively.

**Q11.** Per §7.5, what does this lesson explicitly NOT cover?

- A. The timeout mechanism demonstrated in section 1.
- B. M2-L14's own jitter and circuit-breaker mechanisms in full, how a system decides which errors are worth retrying, and durable checkpointing across a process restart — left to M2-L14's own coverage or to M8-L14.
- C. The backoff-and-idempotency combination in section 2.
- D. The honest-versus-dishonest recovery contrast in section 4.

**Q12.** What is the general lesson this lab demonstrates about retries, timeouts, cancellation, and
recovery?

- A. All four mechanisms are interchangeable and any one of them alone is sufficient for a reliable agent.
- B. Cancellation should always be assumed possible for any action, state-changing or not.
- C. Timeouts, backoff-plus-idempotency, genuine cancellation points, and honest recovery paths are four distinct mechanisms addressing four distinct failure risks, and each has a specific, demonstrated way of silently failing if implemented carelessly.
- D. Recovery paths should always report success to avoid alarming users, regardless of actual outcome.

**Q13.** *(Written, rubric-graded.)* In under 150 words: your team's agent reports "task completed" for
every tool call, whether or not the underlying action actually succeeded after retries. Based on this
lesson, what would you change, and why?

---

## 12. Revision notes

- **A timeout must be measured, not assumed** — this lesson's own first implementation appeared correct
  but actually waited for a hung call to finish anyway, because of how its thread pool was closed; the fix
  was verified by measuring the corrected elapsed time directly.
- **Backoff and idempotency solve different halves of the retry problem and compose without needing to
  know about each other** — measured directly: real doubling delays between failed attempts, and exactly
  one real execution despite three total calls.
- **A cancellation point is a property of an action's own implementation, not a policy applied from
  outside** — measured directly: a genuinely cancellable action stopped with real partial progress; two
  atomic actions had no such checkpoint at all.
- **A dishonest recovery path's output is measurably indistinguishable from success in its own text** —
  measured directly: an identical retried, permanently-failing action produced one message stating failure
  and one message reading exactly like a real success, despite neither actually issuing a refund.
- **A recovery path that reports success regardless of outcome hides real failures until they are
  discovered elsewhere, later, and more expensively** — the general rule §6's worked example illustrates
  directly.

---

## 13. Completion checklist

- [ ] I can implement a timeout that measurably bounds a caller's wait, independent of the underlying
      call's actual duration.
- [ ] I can combine backoff and an idempotency key into one retry mechanism for a state-changing action.
- [ ] I can distinguish a genuinely cancellable action from an atomic one with no cancellation point.
- [ ] I can implement an honest recovery path and explain why a dishonest one is dangerous.
- [ ] I can diagnose, from a described incident, which of these four mechanisms was missing or
      incorrectly implemented.
- [ ] I report exhausted retries as an explicit failure, never as a success-shaped message.
- [ ] I scored 10/13 on the quiz.

---

## 14. References

- M2-L14's own backoff, jitter, and circuit-breaker discipline, extended directly in this lesson's §7.2.
  `[STABLE]`
- M8-L12's own idempotency key mechanism, combined directly with backoff in this lesson. `[STABLE]`
- Python standard library, `concurrent.futures` documentation, for the `ThreadPoolExecutor` timeout and
  shutdown behavior this lesson's own bug fix depended on. `[STABLE]`

---

## 15. Next lesson

→ M8-L14 — Checkpointing and Durable Execution

This lesson made a single retry safe within one process's lifetime. Next: what happens when the process
itself is interrupted mid-task, and how a durable checkpoint lets execution resume without repeating work
already done.
