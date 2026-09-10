# M8-L14 — Checkpointing and Durable Execution

| | |
|---|---|
| **Lesson ID** | M8-L14 |
| **Difficulty** | 3 (Advanced) |
| **Estimated study time** | 2.0 hours |
| **Prerequisites** | [M8-L13](M8-L13-retries-timeouts-cancellation-recovery.md) |

---

## 1. Learning objectives

1. **Demonstrate** that a crashed, unrecoverable multi-step task restarted from scratch re-executes every
   step, including state-changing ones already completed.
2. **Implement** a checkpoint that lets a resumed task skip genuinely completed steps rather than
   repeating them.
3. **Demonstrate** that checkpointing a step *before* its action executes can cause that action to be
   silently skipped entirely on resume — the opposite failure from having no checkpoint at all.
4. **Explain** why correct checkpoint ordering and M8-L12's idempotency key are complementary, not
   redundant, mechanisms.
5. **Diagnose**, from a described incident, whether a durable-execution failure came from missing
   checkpoints, wrongly-ordered checkpoints, or a genuinely un-idempotent step.

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **Checkpoint** | A durable record of which steps of a task have genuinely completed. |
| **Durable execution** | The guarantee that a multi-step task eventually completes correctly even across crashes. |
| **Resume** | Continuing a task from its last checkpoint rather than restarting it from the beginning. |
| **Checkpoint ordering** | Whether a step is marked complete before or after its action actually executes. |
| **Silent skip** | A step never executing, with no visible sign it was skipped, because a checkpoint wrongly says it's done. |

---

## 3. Plain-language explanation

### 3.1 M8-L13 made one retry safe; this lesson makes a whole crashed task recoverable

M8-L13's mechanisms operate within one process's lifetime. This lesson asks what happens when the *process
itself* stops mid-task — a crash, a restart, a deploy. §7.1 shows the naive answer: restart from scratch,
and every step, including ones already genuinely completed, runs again.

### 3.2 A checkpoint written after each step lets a resume skip real, finished work

§7.2 adds exactly one thing to the identical crash scenario: a durable record, updated after each step
completes. The resumed run reads that record and skips straight to the one step that never actually
finished, rather than repeating three that already had.

### 3.3 Checkpointing too early is a different, opposite failure

§7.3 doesn't stop at showing checkpointing works — it shows a specific way to implement it *wrong*: marking
a step complete before its action runs, then crashing in the gap. The resumed run trusts the checkpoint,
skips the step, and a refund that was supposed to happen never does — silently, with the checkpoint's own
record looking exactly like a successfully finished task.

### 3.4 Checkpointing and idempotency solve adjacent, not identical, problems

§7.4 states directly what §5.4 argues: correct checkpoint ordering handles the *common* case (skip what's
genuinely done); M8-L12's idempotency key handles the *narrow* remaining case (a crash in the instant
between an action finishing and its checkpoint being written). Durable execution needs both.

---

## 4. Analogy

**A recipe followed from a torn page, versus one followed from a kitchen timer that was started before the
oven preheated.** Restarting a multi-step recipe from page one after being interrupted means re-measuring
flour you already measured and re-cracking eggs you already cracked — wasteful at best, and if a step was
"add the baking soda," doing it twice is a real, ruined result. A checkpoint is like a cook who ties a knot
in a length of string for every step actually finished, so picking the recipe back up means looking at the
knots and starting from the very next unstarted step. But a cook who ties the knot the moment they *decide*
to preheat the oven, before checking the oven is actually on, risks walking away believing a step is done
that never actually happened — the knot says "preheated," the oven says otherwise, and nothing about the
string reveals the discrepancy.

### Where the analogy breaks

- **A cook can visually double-check whether the oven is actually hot.** §7.3's checkpoint has no such
  independent check built in — it is trusted exactly as written, which is precisely why the ordering of
  when it's written matters so much.
- **A recipe's steps rarely need to be safe against being done twice.** M8-L12's idempotency key exists
  specifically because some steps (a refund, an email) are not naturally safe to repeat, unlike most
  cooking steps.

---

## 5. Detailed technical explanation

### 5.1 No checkpoint means a resumed task cannot distinguish "done" from "never started"

`[REAL, measured]` §7.1 crashed a four-step task after its third step (`issue_refund`) genuinely completed.
Restarting the identical function from scratch **re-executed all four steps, producing two entries in
`REFUND_LOG` for the same order** — a real, measured duplicate refund, with no code change between the
crashed run and the "restarted" one; only the absence of any durable memory of what had already happened.

### 5.2 A checkpoint written after each step's completion lets resumption skip exactly the right work

`[REAL, measured]` §7.2 ran the identical crash scenario with one addition: each step's result was recorded
in `CHECKPOINT_STORE` immediately after it completed. **On resume, the function correctly skipped
`search_orders`, `get_order`, and `issue_refund` — all three already present in the checkpoint — and
executed only `send_confirmation_email`, the one step that had never actually finished.** `REFUND_LOG`
shows exactly one entry.

### 5.3 Checkpointing before the action runs reproduces the opposite failure

`[REAL, measured]` §7.3 marked `issue_refund` complete in the checkpoint *before* calling its actual
action, then crashed during that action's execution — genuinely before `issue_refund()` ever ran.
**`REFUND_LOG` was empty after the crash, confirming the refund never happened — yet the checkpoint already
held an entry for it.** On resume, the function trusted that entry and skipped the step entirely.
**`REFUND_LOG` remained empty even after the task "resumed" and reported its remaining step done** — a
real, silent, missed action, indistinguishable from success by looking at the checkpoint alone.

### 5.4 Correct ordering and idempotency address different parts of the same gap

`[REAL reasoning]` §7.4 states the boundary directly: writing a checkpoint only *after* a step's action is
confirmed complete (§5.2's ordering) prevents §5.3's silent-skip failure in the ordinary case. It does not,
by itself, eliminate every risk — a crash occurring in the narrow window between an action finishing and
its checkpoint being durably written would leave that step's completion uncertain, and a resumed run would
correctly choose to retry it. **This is precisely the case M8-L12's idempotency key protects: a retry of a
step whose true completion status was ambiguous stays safe, because repeating it (if it did, in fact,
already succeed) returns the cached result rather than acting again.**

### 5.5 Assumptions and limitations

- `CHECKPOINT_STORE` is an in-memory dict in this lab, standing in for a durable store (a database, a
  persistent queue) that would actually survive a real process crash — this lab simulates a crash with a
  raised exception within the same process, not an actual restart.
- This lesson does not cover how a real system chooses checkpoint granularity (per step versus a larger
  unit of work), how concurrent workers resuming the same task id could race with each other, or the
  cost/storage trade-offs of checkpointing frequently versus rarely.

---

## 6. Worked example — the workflow engine that marked steps done too soon

**The system.** A workflow engine checkpoints each step of a multi-step order-fulfillment process, updating
its status to "complete" as the first action of executing that step, on the theory that this simplifies the
engine's own internal logic (mark, then act, rather than act, then mark).

**The incident.** A worker process crashed during the "charge payment" step, immediately after that step
was marked complete in the workflow's durable state but before the actual charge request was sent. When
the workflow resumed on a new worker, it read the checkpoint, saw "charge payment: complete," and moved
directly to the next step — shipping the order. The customer received a shipped order and was never
charged.

**Why this matches §5.3 exactly.** This is §7.3's own ordering bug, verbatim, at production scale: the
checkpoint was written *before* the action it described had actually happened, and a crash in that specific
window turned an unstarted action into one silently recorded as finished.

**Three defects the incident revealed:**

| # | Defect | Consequence |
|---|---|---|
| 1 | The workflow engine's own convention was to checkpoint before executing a step, not after | A crash during any step's actual execution would silently mark that step as falsely complete |
| 2 | No verification step checked that "charge payment: complete" corresponded to any actual charge record | The mismatch between the checkpoint's claim and reality had no independent check |
| 3 | The gap was invisible until a customer noticed they had received goods without being charged | Detection depended on an external party rather than the system's own consistency checks |

### The fix

**Change the engine's own convention to checkpoint after a step's action is confirmed complete**, per
§5.2 — reversing the specific ordering that caused the incident.

**Add an idempotency key to any step that must remain safe even if its completion status is ever
ambiguous**, per §5.4 — protecting against the narrower race this reordering alone cannot fully close.

**The general rule.** **A checkpoint's value depends entirely on what moment it actually records — a
checkpoint written before an action is a plan, not a fact, and treating a plan as a completed fact on
resume is exactly how a real action gets silently skipped.**

---

## 7. Practical activity

**File:** [`labs/m8/l14_checkpointing_durable_execution.py`](../../labs/m8/l14_checkpointing_durable_execution.py)

**No API key, no network, no third-party dependencies.** Runs in well under a second.

```bash
source .venv/bin/activate
python labs/m8/l14_checkpointing_durable_execution.py
```

### 7.2 Expected output

`[EXECUTED]` — 2026-09-10, Python 3.10.11 (pure standard library).

```text
============================================================================
1. NO CHECKPOINT: A CRASH MEANS STARTING OVER FROM SCRATCH
============================================================================
  First run -- crashes right after issue_refund completes, before
  send_confirmation_email ever runs:
    SIMULATED CRASH after completing step 3 ('issue_refund')

  REFUND_LOG after the crash: ['O-6001']

  'Restarting' the task from scratch, with no memory of the crashed run:
  REFUND_LOG after the restart: ['O-6001', 'O-6001']
  EMAILS_SENT after the restart: ['O-6001']

  issue_refund() ran TWICE for the same order -- once before the
  crash, once again when the task restarted from the very beginning
  with no record of what had already genuinely happened.

============================================================================
2. A CHECKPOINT WRITTEN AFTER EACH STEP LETS A RESUME SKIP REAL WORK
============================================================================
  First run -- crashes right after issue_refund completes, exactly as
  in section 1, but this time each completed step was checkpointed:
    SIMULATED CRASH after completing step 3 ('issue_refund')

  CHECKPOINT_STORE now records: ['search_orders', 'get_order', 'issue_refund']
  REFUND_LOG after the crash: ['O-6002']

  Resuming the SAME task id -- the checkpoint tells the resumed run
  exactly which steps are already genuinely done:
  REFUND_LOG after resuming: ['O-6002']
  EMAILS_SENT after resuming: ['O-6002']

  issue_refund() ran exactly ONCE this time -- the resumed run
  skipped search_orders, get_order, and issue_refund entirely,
  because the checkpoint already recorded them as complete, and
  executed only the one step that had genuinely never finished.

============================================================================
3. WHEN THE CHECKPOINT IS WRITTEN MATTERS AS MUCH AS WHETHER IT EXISTS
============================================================================
  Crashing DURING issue_refund itself -- AFTER it was optimistically
  marked complete, but BEFORE execute_step() for it ever ran:
    SIMULATED CRASH DURING step 2 ('issue_refund') -- AFTER it was marked complete, BEFORE it actually executed

  REFUND_LOG after the crash: [] -- genuinely empty; issue_refund() never ran.
  Checkpoint for 'issue_refund': 'marked complete (BEFORE the action actually ran)'

  Resuming -- the checkpoint (wrongly) already says issue_refund is done:
  REFUND_LOG after 'resuming': []
  EMAILS_SENT after 'resuming': ['O-6003']

  The resumed run skipped issue_refund entirely, because the
  checkpoint said it was complete -- but it never actually ran. A
  customer's order was never refunded, and nothing in the checkpoint
  reveals this: it looks, from the checkpoint's own record, exactly
  like a task that finished correctly. This is the OPPOSITE failure
  from section 1 -- there, a crash caused a real duplicate action;
  here, checkpointing too early caused a real action to be silently
  skipped altogether.

============================================================================
4. THE CORRECT COMBINATION: CHECKPOINT AFTER, AND IDEMPOTENT ANYWAY
============================================================================
  Section 2's ordering (checkpoint written only AFTER a step's action
  genuinely completes) avoids section 3's silent-skip failure. But
  section 2 alone still assumes the checkpoint write itself and the
  action's completion are safely atomic -- a crash occurring in the
  narrow gap between an action finishing and its checkpoint being
  written would leave that step's result uncertain on resume, and
  the resumed run would correctly choose to retry it (since no
  checkpoint entry exists yet).

  This is exactly why M8-L12's idempotency key is not optional here:
  a correctly-ordered checkpoint (write after, never before) tells a
  resumed run what NOT to repeat in the common case; an idempotency
  key protects the specific narrow case where the checkpoint and the
  action's completion could not be made perfectly atomic, so a retry
  of that one step is still safe even though it wasn't skipped.
  Durable execution is this combination, not either mechanism alone.

============================================================================
5. WHAT THIS LAB IS AND IS NOT
============================================================================
  REAL: every REFUND_LOG entry, every CHECKPOINT_STORE record, and
  the specific contrast between section 1's duplicate refund,
  section 2's correct single refund, and section 3's silently
  skipped refund are genuinely produced by running this code -- not
  scripted to fit a predetermined narrative.

  ILLUSTRATIVE: CHECKPOINT_STORE is an in-memory dict standing in
  for a durable store (a database, a persistent queue) that would
  actually survive a real process crash -- this lab simulates a
  crash with a raised exception within the same process, not an
  actual process restart.

  NOT SHOWN: how a real system chooses checkpoint granularity (per
  step, per some larger unit of work); how concurrent workers
  resuming the same task id could race with each other; and cost or
  storage-overhead trade-offs of checkpointing frequently versus
  rarely, a natural extension left to the exercises.

Done.
```

### 7.3 Reading the result

**Sections 1 and 3 are mirror-image failures, and reading them side by side is the fastest way to
internalize this lesson.** No checkpoint at all causes a real duplicate action. A checkpoint written at the
wrong moment causes a real missed action. Both look, from the outside, like the same category of problem
("something went wrong during a crash"), but they need opposite fixes.

**Section 2 is the version that actually works, and it earns that status by being tested against the exact
same crash as section 1.** The identical crash point, the identical steps, and the only difference is
where the checkpoint gets written and read — that controlled comparison is what makes the fix convincing.

**Section 4's honesty about section 2's own residual gap is worth taking seriously.** It would be tempting
to present correct checkpoint ordering as a complete solution; the lesson instead states plainly that a
narrow race still exists, and that idempotency (M8-L12) is what closes it, not a claim that checkpointing
alone is sufficient.

---

## 8. Common mistakes and troubleshooting

1. **Restarting a crashed multi-step task from scratch with no durable record of prior progress.** §5.1 —
   this re-executes every step, including state-changing ones already genuinely completed.
2. **Marking a step complete in a checkpoint before executing its action.** §5.3, §6 — a crash in the gap
   between the mark and the real execution causes that action to be silently skipped on resume.
3. **Treating correct checkpoint ordering as a complete solution on its own.** §5.4 — a narrow race between
   an action's completion and its checkpoint being written still exists; idempotency (M8-L12) closes it.
4. **Assuming a checkpoint's record is automatically accurate.** §5.3, §6 — a checkpoint is only as
   trustworthy as the moment it was actually written relative to the real action.
5. **Not testing what happens when a crash occurs in the middle of a specific step**, rather than only
   between steps. §7.3 — this is exactly the case that reveals ordering bugs.

| Symptom | Likely cause | Fix |
|---|---|---|
| A resumed task re-executes a state-changing step that had already completed before a crash | No durable checkpoint exists to tell the resumed run what already happened | Add a checkpoint, written after each step completes, per §5.2 |
| A resumed task skips a step, and the corresponding real-world action never happened | The checkpoint was written before the step's action executed, and a crash occurred in between | Move the checkpoint write to after the action is confirmed complete, per §5.3, §6 |
| A duplicate action still occurs occasionally despite a correctly-ordered checkpoint | A crash landed in the narrow window between the action completing and its checkpoint being durably written | Add an idempotency key (M8-L12) to make a retry of that step safe regardless, per §5.4 |
| A checkpoint's record doesn't match what actually happened, and this was only discovered externally | No independent verification exists between the checkpoint's claims and the real system of record | Add a verification step or reconciliation check, per §6 |

---

## 9. Security, privacy, reliability, cost

- **Reliability.** Checkpoint each step only after its action is confirmed complete, never before — the
  ordering itself determines whether a crash produces a missed action or a safely-skippable one (§5.2,
  §5.3, §6).
- **Reliability.** Pair correct checkpoint ordering with an idempotency key (M8-L12) for the narrow race a
  checkpoint alone cannot close (§5.4).
- **Cost.** A task that restarts from scratch after every crash pays for every already-completed step
  again — a real, avoidable cost a correctly-ordered checkpoint removes (§5.1, §5.2).
- **Reliability.** Verify a checkpoint's claims against the actual system of record where possible — a
  checkpoint that says a step is done is a claim, not independently guaranteed truth (§5.3, §6).

---

## 10. Exercises

### Exercise 1 — Beginner (~20 min)

1. Why did section 1's restarted task issue a duplicate refund?
2. What single addition in section 2 prevented that duplicate?
3. Why did section 3's checkpoint cause a refund to be silently skipped instead?
4. In your own words, what is the difference between section 1's failure and section 3's failure?
5. Why does correct checkpoint ordering alone not fully eliminate the need for idempotency (M8-L12)?

### Exercise 2 — Intermediate (~40 min)

1. Run the lab. Confirm the duplicate refund in §7.1, the correct single refund in §7.2, and the silently
   skipped refund in §7.3 on your own machine.
2. Modify `run_task_with_checkpoint()` to crash at a different step index and confirm the resumed run still
   correctly skips only the genuinely completed steps.
3. Add a fifth step to `TASK_STEPS` and confirm the checkpoint mechanism from section 2 still correctly
   resumes from the right point after a crash at various positions.
4. Using M8-L12's own idempotency key mechanism, extend `run_task_with_checkpoint()` to also protect
   `issue_refund` with an idempotency key, and explain what additional case this protects against beyond
   the checkpoint alone.
5. Using §5.4's framework, design a test that specifically simulates a crash occurring between a step's
   completion and its checkpoint write, and confirm your idempotency-protected version handles it safely.

### Exercise 3 — Challenge (~50 min)

1. Design a checkpoint schema (beyond a simple "step name" key) that records enough information to verify,
   independently, that a checkpointed step's claimed result actually matches reality.
2. Investigate what could go wrong if two workers, both resuming the same task id, ran concurrently against
   the same checkpoint store, and propose a mechanism to prevent it.
3. Using M8-L13's own timeout mechanism, design a policy for how long a task should wait before considering
   a step "possibly crashed" and eligible for resumption by a different worker.
4. Research (conceptually) how a real durable-execution framework (in any domain) represents checkpoints and
   compare it to this lesson's dict-based `CHECKPOINT_STORE`.
5. Using §6's worked example, design a reconciliation check that could run periodically to catch a
   checkpoint claiming a step is complete when the underlying system of record disagrees.

---

## 11. Quiz

*(Answers: [`answer-keys/module-08-answers.md`](../../answer-keys/module-08-answers.md#m8-l14).)*

**Q1.** Per §7.1's measured result, why did restarting the crashed task from scratch produce two refund
log entries for the same order?

- A. The restarted run had no durable record of which steps had already completed, so it re-executed all four steps, including issue_refund, which had already run before the crash.
- B. issue_refund() itself contains a bug that duplicates its own log entry.
- C. The order amount was defined incorrectly.
- D. The checkpoint store was corrupted.

**Q2.** Per §7.2's measured result, what did the resumed run do differently from section 1's restart?

- A. It also re-executed all four steps from scratch.
- B. It executed only search_orders and stopped.
- C. It refused to resume at all.
- D. It skipped search_orders, get_order, and issue_refund because the checkpoint already recorded them as complete, executing only the one step that had never finished.

**Q3.** Per §7.3's measured result, what happened when the checkpoint marked `issue_refund` complete
before its action actually ran, and a crash occurred in that gap?

- A. The refund was issued twice.
- B. REFUND_LOG remained empty even after resuming, because the resumed run trusted the checkpoint and skipped the step that had never actually executed.
- C. The system correctly detected the discrepancy and re-executed the step.
- D. The checkpoint store was automatically corrected.

**Q4.** Per §5.3, why is section 3's failure described as the opposite of section 1's?

- A. Section 3's failure only affected read-only actions.
- B. Both sections describe the identical failure mode.
- C. Section 1's failure caused a real duplicate action; section 3's failure caused a real action to be silently skipped altogether.
- D. Section 1's failure was intentional, while section 3's was not.

**Q5.** Per §5.4, does correctly ordering a checkpoint (writing it only after a step's action completes)
fully eliminate the need for an idempotency key?

- A. No — a crash occurring in the narrow gap between an action completing and its checkpoint being written still leaves that step's status ambiguous on resume, which an idempotency key protects against.
- B. Yes, correct ordering alone is fully sufficient in every case.
- C. Idempotency keys are only needed when there is no checkpoint at all.
- D. Correct ordering makes idempotency keys actively harmful.

**Q6.** Per §7.4, what specific risk remains even with a correctly-ordered checkpoint (write after, never
before)?

- A. No risk remains; the ordering fix is complete on its own.
- B. Correct ordering introduces a new duplicate-action risk not present before.
- C. The checkpoint store itself always fails regardless of ordering.
- D. A crash in the narrow window between a step's action finishing and its checkpoint being durably written can leave that step's completion status uncertain on resume.

**Q7.** Per §6's worked example, what specific ordering mistake caused the customer to receive a shipped,
unpaid order?

- A. The shipping step was executed before the payment step was ever attempted.
- B. The workflow engine's convention was to checkpoint a step as complete before executing its action, and a crash during the payment step's actual execution left it marked complete despite never having charged the customer.
- C. The customer's payment method was invalid.
- D. No checkpoint existed anywhere in the workflow.

**Q8.** Per §6, how was the incident eventually discovered?

- A. The workflow engine's own internal checks flagged the discrepancy immediately.
- B. A scheduled audit caught the issue within minutes.
- C. A customer noticed they had received goods without being charged.
- D. The incident was never discovered.

**Q9.** Per §6, what is the stated general rule this incident illustrates?

- A. A checkpoint's value depends entirely on what moment it actually records — a checkpoint written before an action is a plan, not a fact, and treating a plan as a completed fact on resume causes a real action to be silently skipped.
- B. Checkpointing should never be used in any production workflow system.
- C. Payment processing should never be part of an automated workflow.
- D. The incident has no generalizable lesson beyond this specific system.

**Q10.** Per §6, what two fixes are proposed together for the kind of gap this incident revealed?

- A. Removing the workflow engine entirely and processing orders manually.
- B. Only increasing the number of retries, with no change to checkpoint ordering.
- C. Disabling checkpointing entirely to avoid the ordering risk.
- D. Reversing the checkpoint ordering to write after action completion, and adding an idempotency key for any step that must remain safe even if completion status is ever ambiguous.

**Q11.** Per §7.5, what does this lesson explicitly NOT cover?

- A. The no-checkpoint duplicate-action demonstration in section 1.
- B. How a real system chooses checkpoint granularity, how concurrent workers resuming the same task could race, and cost/storage trade-offs of checkpoint frequency — left as natural extensions.
- C. The correctly-ordered checkpoint demonstration in section 2.
- D. The wrongly-ordered checkpoint demonstration in section 3.

**Q12.** What is the general lesson this lab demonstrates about checkpointing and durable execution?

- A. Any checkpoint, regardless of when it is written, fully protects against both duplicate and missed actions.
- B. Checkpointing and idempotency solve the identical problem, so only one is ever needed.
- C. A checkpoint written after a step's action completes lets a resumed task skip genuine, finished work, but a checkpoint written before the action runs can cause that action to be silently skipped entirely — durable execution requires correct ordering combined with idempotency for the narrow gap ordering alone cannot close.
- D. Restarting a crashed task from scratch is always safe as long as the steps are executed quickly.

**Q13.** *(Written, rubric-graded.)* In under 150 words: your team's workflow engine checkpoints a step as
complete immediately before executing it, "to keep the code simple." Based on this lesson, what would you
change, and why?

---

## 12. Revision notes

- **A crashed task restarted with no durable record re-executes every step, including state-changing ones
  already completed** — measured directly: a duplicate refund from restarting a crashed four-step task
  from scratch.
- **A checkpoint written after each step's action completes lets a resumed task skip genuinely finished
  work** — measured directly: the identical crash scenario, with checkpointing, produced exactly one
  refund instead of two.
- **A checkpoint written before the action runs can cause that action to be silently skipped entirely on
  resume** — measured directly: a refund marked "complete" before it ran, then never executed, with the
  checkpoint's own record showing no visible sign of the gap.
- **Correct checkpoint ordering and M8-L12's idempotency key solve adjacent, not identical, problems** —
  ordering handles the common case; idempotency protects the narrow race ordering alone cannot close.
- **A checkpoint's value depends entirely on what moment it records** — a checkpoint written before an
  action is a plan, not a fact, and the general worked-example rule follows directly from this.

---

## 13. Completion checklist

- [ ] I can explain why a crashed task restarted from scratch re-executes already-completed steps.
- [ ] I can implement a checkpoint that lets a resumed task skip genuinely finished work.
- [ ] I can explain why checkpointing before an action runs can cause that action to be silently skipped.
- [ ] I can explain why correct checkpoint ordering does not fully eliminate the need for idempotency.
- [ ] I can diagnose, from a described incident, whether the cause was a missing checkpoint, a wrongly-
      ordered one, or a genuinely un-idempotent step.
- [ ] I checkpoint a step only after its action is confirmed complete, never before.
- [ ] I scored 10/13 on the quiz.

---

## 14. References

- M8-L12's own idempotency key mechanism, combined directly with checkpointing in this lesson's §5.4.
  `[STABLE]`
- M8-L13's own retry and recovery discipline, extended here to whole-process crash recovery. `[STABLE]`

---

## 15. Next lesson

→ M8-L15 — Step Limits, Cost Budgets and Runaway Prevention

This lesson made a crashed, multi-step task recoverable. Next: bounding how far an agent's own loop is
allowed to run in the first place, in steps and in cost, before recovery is ever needed.
