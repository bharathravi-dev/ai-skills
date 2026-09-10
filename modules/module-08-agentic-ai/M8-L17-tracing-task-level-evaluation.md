# M8-L17 — Tracing and Task-Level Evaluation

| | |
|---|---|
| **Lesson ID** | M8-L17 |
| **Difficulty** | 3 (Advanced) |
| **Estimated study time** | 2.25 hours |
| **Prerequisites** | M8-L04, M5-L18 |

---

## 1. Learning objectives

1. **Implement** a trace that records the full sequence of steps an agent actually took, not just its
   final output.
2. **Demonstrate** that every individual step in a task can succeed while the task itself fails to achieve
   its actual goal.
3. **Distinguish** step-level evaluation (did each call complete without error?) from task-level evaluation
   (did the outcome match what was actually intended?).
4. **Use** a trace to identify exactly which step caused a task-level failure, without guessing.
5. **Diagnose**, from a described incident, whether a monitoring gap came from missing tracing or from
   evaluating only at the step level.

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **Trace** | A structured record of every step an agent actually took during a task. |
| **Step-level evaluation** | Checking whether each individual call completed without error. |
| **Task-level evaluation** | Checking whether the task's actual, intended outcome was achieved. |
| **Divergence point** | The specific step in a trace where the actual outcome first departed from the intended one. |

---

## 3. Plain-language explanation

### 3.1 M5-L18 evaluated one call; this lesson evaluates a whole task

M5-L18 built an evaluation dataset for a single call's output. An agent's task, per M8-L04, can span many
calls — and this lesson's central finding is that every one of those calls can succeed individually while
the task, taken as a whole, still fails. §7.2 makes this a measured fact, not a cautionary generality.

### 3.2 A trace is what makes "why did this fail" answerable at all

§7.1 doesn't summarize a task's outcome — it records every step's name, arguments, and result as the task
runs. This is the only reason §7.3 can later point to one specific step as the cause of a failure, instead
of guessing.

### 3.3 Step-level "all green" is real, and it is not the same claim as task success

§7.2 runs a genuine refund task where `search_orders`, `get_order`, and `issue_refund` each complete without
error, and a customer genuinely gets refunded — and the wrong customer. A check that only looks for errors
across the trace reports full success. A check that compares the actual outcome to what was actually
intended reports failure. Both checks are correctly computed; they are answering different questions.

### 3.4 The trace, not a guess, identifies where things went wrong

§7.3 doesn't argue in the abstract that `search_orders` was the problem — it reads the trace's own recorded
call and compares its result directly against the order that should have been found, confirming the
mismatch from the trace's own data.

---

## 4. Analogy

**A relay race's official timing log, versus just announcing who crossed the finish line.** Announcing only
the finishing time tells you the race is over and roughly how it went; it tells you nothing about which leg
of the race was actually fastest or slowest, or where a baton exchange went wrong. An official timing log
that records each runner's individual split time lets you look back and see exactly which leg underperformed
— not by guessing from the final time alone, but by reading the actual recorded splits. And a team can
finish the race with every individual runner recording a personal best split, and still lose, if the baton
was passed to the wrong runner at some exchange.

### Where the analogy breaks

- **A relay race has an unambiguous, single correct order of runners.** §7.2's task-level check needs an
  externally-known "correct" outcome (the actual intended customer) to compare against — a real system must
  have some independent source of truth, which a trace alone does not provide.
- **A timing log is purely passive — it doesn't affect the race.** Tracing an agent's steps is also purely
  observational in this lesson; it records what happened without influencing the task's outcome, unlike a
  human official who might intervene mid-race.

---

## 5. Detailed technical explanation

### 5.1 A trace is a genuine record, not a summary

`[REAL, measured]` §7.1's `traced_call()` recorded each of three real steps — `search_orders`, `get_order`,
`issue_refund` — with their actual arguments and actual results, as the task executed. **The trace shows
`search_orders('Dana')` genuinely returned `'O-7001'`**, available for inspection independent of whether the
task's overall outcome turns out to be correct.

### 5.2 Step-level success and task-level success are measurably different claims

`[REAL, measured]` §7.2's `step_level_check()` — checking only whether each recorded step completed without
an error — returned `True`. **`task_level_check()` — checking whether the refund actually reached the
customer who submitted the request — returned `False`.** Both checks ran against the identical trace and
outcome; they disagree because they are computing genuinely different things. The refund itself was real
(`REFUND_LOG` shows a genuine entry), just directed at the wrong customer.

### 5.3 The trace pinpoints the specific divergence, not just that one exists

`[REAL, measured]` §7.3 compared `search_orders`'s actual recorded result (`'O-7001'`) against the order id
that should have been found for the actual intended customer (`'O-7002'`) — **a direct mismatch, read from
the trace's own data.** `get_order` and `issue_refund` are explicitly confirmed to have acted correctly
*given their own input* — the failure traces to one specific step's decision, not to a general sense that
"something went wrong somewhere."

### 5.4 Assumptions and limitations

- `search_orders()`'s first-name-only fallback is a small, deliberately realistic simplification standing
  in for a real search-ambiguity failure mode — a real system's retrieval logic could fail in many other
  specific ways.
- This lesson does not cover tracing across multiple agents or a distributed system (M8-L09's own
  multi-agent territory, which would need correlated traces across agent boundaries), building a full
  evaluation dataset of many traced tasks (M5-L18's own topic, applied at the task level), or automated
  tools that surface a likely-culprit step without a person reading the trace directly, as this lab's
  section 3 does by hand.

---

## 6. Worked example — the dashboard that only ever showed green

**The system.** A team's agent-monitoring dashboard reports the percentage of tool calls that complete
without error, displayed prominently as the system's primary health metric.

**The incident.** The dashboard stayed at 99%+ "success" for months while a specific class of customer
complaints about incorrect account actions slowly grew. Every tool call involved — account lookups, balance
checks, the action itself — was individually completing without any error at any point; the actual accounts
being affected were, in a meaningful fraction of cases, simply the wrong ones, for reasons resembling this
lesson's own ambiguous-name lookup.

**Why this matches §5.2 exactly.** The dashboard's single metric was a purely step-level check — did each
call error out? — with **no task-level check anywhere in the system verifying that the actual outcome
matched what was actually intended.** The dashboard was not lying; it was answering a real, correctly
computed question that simply was not the question that mattered for catching this specific class of
failure.

**Three defects the incident revealed:**

| # | Defect | Consequence |
|---|---|---|
| 1 | The only tracked metric was step-level completion, with no task-level outcome check | A meaningful failure rate was structurally invisible to the dashboard's own primary metric |
| 2 | No trace was retained per task, only aggregate step-completion statistics | Even after complaints arrived, there was no structured record to inspect for the specific cause |
| 3 | The growing complaint rate was the only signal available, discovered slowly and indirectly | Detection depended on customers reporting individual incidents rather than the system's own monitoring |

### The fix

**Add a task-level metric alongside the step-level one**, per §5.2 — comparing actual outcomes against
known-correct ones for at least a sample of tasks, not just checking for errors.

**Retain a trace per task**, per §5.1 and §5.3 — so that once a task-level failure is identified (by any
means), the specific divergence point can be found directly, rather than reconstructed from memory or
guesswork.

**The general rule.** **A dashboard reporting near-perfect step-level success is answering a real question
correctly, and it is a different question from "did the system do what it was actually supposed to do" —
mistaking one for the other is exactly how a real, growing failure rate stays invisible for months.**

---

## 7. Practical activity

**File:** [`labs/m8/l17_tracing_task_level_evaluation.py`](../../labs/m8/l17_tracing_task_level_evaluation.py)

**No API key, no network, no third-party dependencies.** Runs in well under a second.

```bash
source .venv/bin/activate
python labs/m8/l17_tracing_task_level_evaluation.py
```

### 7.2 Expected output

`[EXECUTED]` — 2026-09-10, Python 3.10.11 (pure standard library).

```text
============================================================================
1. A TRACE: A STRUCTURED RECORD OF WHAT WAS ACTUALLY DONE
============================================================================
  Running a refund task for a request that only gave a first name,
  'Dana' -- tracing every step as it happens:

    [search_orders] args=('Dana',) -> result='O-7001' error=None
    [get_order] args=('O-7001',) -> result={'customer': 'Dana Kim', 'amount': 40.0} error=None
    [issue_refund] args=('O-7001', 40.0) -> result='refund of $40.00 issued for O-7001' error=None

  Task's own final result: refunded order belongs to 'Dana Kim'
  The trace is a genuine record of the actual sequence taken -- not
  a summary, not a guess -- available for inspection independent of
  whether the task's outcome turns out to be right or wrong.

============================================================================
2. STEP-LEVEL 'ALL GREEN' CAN COEXIST WITH TASK-LEVEL FAILURE
============================================================================
  Step-level check (did every call complete without error?): True
  Task-level check (did the refund reach 'Dana Lin', who actually asked?): False

  REFUND_LOG: [('O-7001', 40.0)]
  The refund went to 'Dana Kim' instead of 'Dana Lin'.

  Every individual step genuinely succeeded -- search_orders found A
  real order, get_order returned real details, issue_refund genuinely
  processed a real refund. A step-level evaluation checking only for
  errors would report this task as fully successful. It was not: the
  wrong customer was refunded, and only a TASK-level check, comparing
  the actual outcome against what was actually intended, catches it.

============================================================================
3. USING THE TRACE TO DIAGNOSE WHERE THINGS ACTUALLY WENT WRONG
============================================================================
  With task-level failure confirmed, the trace answers WHERE the
  divergence happened -- not by guessing, but by reading the actual
  recorded step:

    [search_orders] called with ('Dana',) -> returned 'O-7001'
    Real intended order (for 'Dana Lin'): 'O-7002'
    Do they match? False

  The trace pinpoints search_orders specifically -- get_order and
  issue_refund both correctly and faithfully acted on WHATEVER order
  id search_orders handed them; neither of those steps did anything
  wrong given their own input. The task-level failure traces back to
  exactly one step's decision, visible directly in the trace record,
  not inferred after the fact.

============================================================================
4. WHAT THIS LAB IS AND IS NOT
============================================================================
  REAL: every trace entry, every step-level and task-level check
  result above is genuinely computed by running this code -- the
  wrong-customer refund is a real, measured outcome of a real
  ambiguous-name lookup, not a scripted narrative.

  ILLUSTRATIVE: search_orders()'s first-name-only fallback is a
  small, deliberately realistic simplification standing in for a
  real fuzzy-matching or search ambiguity -- a real system's own
  retrieval logic could fail in many other specific ways.

  NOT SHOWN: tracing across multiple agents or a distributed system
  (M8-L09's own multi-agent territory, now needing correlated
  traces); building a full evaluation DATASET of many traced tasks
  (M5-L18's own topic, applied at the task level); and automated
  tools that surface a likely-culprit step without a human reading
  the trace directly, as this lab's section 3 does by hand.

Done.
```

### 7.3 Reading the result

**Section 2's `True` and `False`, computed against the identical trace, is the whole lesson in two lines.**
Neither check is wrong; they simply measure different things, and a system that only ever computes the
first one has a real, structural blind spot toward the second.

**Section 3 is what makes tracing worth the overhead of recording it.** Knowing a task failed is one thing;
knowing precisely which step's decision caused it, confirmed against the trace's own recorded data rather
than inferred from context, is the actual payoff of having traced the task in the first place.

**Section 1's trace format — step, arguments, result, error — is deliberately minimal.** It's the smallest
structure that still supports both section 2's step-level check and section 3's divergence-finding, which is
itself a small, useful design lesson: a trace only needs to record enough to answer the questions actually
asked of it.

---

## 8. Common mistakes and troubleshooting

1. **Treating "no errors across all steps" as equivalent to "the task succeeded."** §5.2, §6 — these are
   different, both computable, and often disagree in exactly the cases that matter most.
2. **Monitoring only aggregate step-completion rates, with no task-level outcome check.** §6 — this is
   precisely the gap that let a real incident grow invisibly for months.
3. **Not retaining a trace per task, only summary statistics.** §5.1, §6 — without a trace, even a
   correctly-identified task-level failure has no structured record to diagnose.
4. **Guessing which step caused a task-level failure instead of reading the trace directly.** §5.3 — the
   trace's own recorded arguments and results settle this without inference.
5. **Assuming a task-level check needs no independent source of truth.** §5.2 — comparing an outcome
   against "what was intended" requires knowing what was actually intended, from somewhere outside the
   trace itself.

| Symptom | Likely cause | Fix |
|---|---|---|
| A monitoring dashboard shows near-perfect success while user complaints about wrong outcomes persist | Only step-level (error-free) completion is tracked, with no task-level outcome check | Add a task-level check comparing actual outcomes to known-correct ones, per §5.2, §6 |
| A task-level failure is identified, but the cause is unclear | No trace was recorded, or the trace wasn't consulted directly | Record a structured trace per task and read it directly to find the divergence, per §5.1, §5.3 |
| A team assumes a specific step caused a failure without checking | The assumption was never verified against the trace's actual recorded data | Compare the step's actual recorded result against what it should have been, per §5.3 |
| Task-level evaluation seems impossible to implement | No independent source of the "correct" or "intended" outcome exists to compare against | Identify or construct a ground-truth source (an authenticated identity, a known-correct answer set) per task, per §5.2 |

---

## 9. Security, privacy, reliability, cost

- **Reliability.** Evaluate agent tasks at both the step level (did each call error?) and the task level
  (did the outcome match what was intended?) — measured directly to be different, disagreeing claims (§5.2).
- **Reliability.** Retain a structured trace per task, not just aggregate statistics — this is what makes a
  task-level failure diagnosable rather than merely detectable (§5.1, §5.3).
- **Privacy.** A task-level failure that sends an action (a refund, a data disclosure) to the wrong party is
  a privacy incident, not merely a quality one — task-level evaluation is what catches this class of error
  (§5.2, §6).
- **Cost.** A monitoring system relying only on step-level success can let a real, costly failure mode grow
  invisibly for an extended period, as §6's worked example shows directly.

---

## 10. Exercises

### Exercise 1 — Beginner (~20 min)

1. What does a trace record that a simple pass/fail summary does not?
2. Why did every individual step in §7.1's task succeed, yet the task itself failed?
3. What is the difference between step-level and task-level evaluation, in your own words?
4. How did §7.3 identify exactly which step caused the task-level failure?
5. Why couldn't the worked example's dashboard detect the real failure it was missing?

### Exercise 2 — Intermediate (~40 min)

1. Run the lab. Confirm §7.1's trace, §7.2's step-level/task-level disagreement, and §7.3's diagnosis on
   your own machine.
2. Modify `search_orders()`'s fallback to fix the first-name-only ambiguity (e.g., requiring a full name
   match), and confirm the task now succeeds at both the step and task level for the same request.
3. Construct a second scenario where a step genuinely FAILS (raises an exception) but the task still
   achieves its correct overall goal through a fallback path, and implement both checks against it.
4. Extend `TRACE` to also record a timestamp per step, and use it to compute how long each step took.
5. Using §5.2's distinction, design a task-level check for a domain of your choosing (not refunds), and
   specify what independent source of truth it would need.

### Exercise 3 — Challenge (~50 min)

1. Design an automated "likely culprit" finder that inspects a trace and a task-level failure, and proposes
   which step most likely caused the divergence, without a human reading the trace directly.
2. Using M8-L09's own multi-agent territory, design a trace format that could correlate steps taken by
   several different agents collaborating on one task.
3. Using M5-L18's own evaluation-dataset discipline, design a process for building a dataset of many traced
   tasks, each with a known-correct outcome, suitable for measuring task-level success rate at scale.
4. Research (conceptually) how a real observability or tracing system (in any domain) structures its trace
   format, and compare it to this lesson's simple step/args/result/error record.
5. Using §6's worked example, design a specific dashboard metric (beyond raw step-completion percentage)
   that would have surfaced the growing incident rate earlier.

---

## 11. Quiz

*(Answers: [`answer-keys/module-08-answers.md`](../../answer-keys/module-08-answers.md#m8-l17).)*

**Q1.** Per §7.1's measured result, what did the trace record for each step of the refund task?

- A. Each step's name, its actual arguments, and its actual result or error.
- B. Only the final output of the entire task, with no per-step detail.
- C. Only whether the task as a whole succeeded or failed.
- D. A summary count of how many steps were taken, with no other detail.

**Q2.** Per §7.2's measured result, what did the step-level check report for this task?

- A. It reported that two of three steps failed.
- B. It reported that the task failed.
- C. It could not be computed at all.
- D. It reported that every step completed without error.

**Q3.** Per §7.2's measured result, what did the task-level check report for the same task, and why?

- A. It reported success, agreeing with the step-level check.
- B. It reported failure, because the refund reached a different customer than the one who actually submitted the request.
- C. It could not be computed without a live model call.
- D. It reported the same result as the step-level check for a different reason.

**Q4.** Per §5.2, why do the step-level and task-level checks disagree in this lesson's own example?

- A. One of the two checks contains a bug.
- B. The task-level check is simply a renamed copy of the step-level check.
- C. They are computing genuinely different things — whether calls completed without error, versus whether the actual outcome matched what was actually intended.
- D. The disagreement is a random artifact with no underlying cause.

**Q5.** Per §7.3's measured result, how was the specific step causing the task-level failure identified?

- A. By comparing search_orders's actual recorded result in the trace against the order that should have been found for the actual intended customer.
- B. By guessing which step was most likely to blame.
- C. By re-running the entire task from scratch with different inputs.
- D. By assuming get_order or issue_refund must be at fault, since they run later in the sequence.

**Q6.** Per §5.3, were get_order and issue_refund found to have done anything wrong in this lesson's
example?

- A. Yes, both steps contained bugs unrelated to search_orders.
- B. The lesson does not address whether these steps behaved correctly.
- C. Only issue_refund was found to be at fault.
- D. No — both acted correctly given the input they were actually given; the failure traced to search_orders's own decision specifically.

**Q7.** Per §6's worked example, what was the actual gap in the team's monitoring dashboard?

- A. The dashboard had no monitoring of any kind.
- B. The dashboard tracked only step-level (error-free) completion, with no task-level check verifying actual outcomes matched what was intended.
- C. The dashboard only tracked task-level outcomes, with no step-level detail.
- D. The dashboard was tracking the correct metric, and the incident was unrelated to monitoring.

**Q8.** Per §6, why did the incident grow for months before being noticed through other means?

- A. The incident was immediately visible but ignored.
- B. The dashboard was never actually checked by anyone.
- C. The dashboard's step-level success metric stayed high because individual calls were genuinely completing without error, giving no signal that outcomes were sometimes wrong.
- D. No customers were ever affected by the incident.

**Q9.** Per §6, what is the stated general rule this incident illustrates?

- A. A dashboard reporting near-perfect step-level success is answering a real but different question from "did the system do what it was actually supposed to do," and conflating the two lets a real failure mode stay invisible.
- B. Step-level monitoring should never be used in any system.
- C. Task-level evaluation makes step-level monitoring entirely unnecessary.
- D. The incident has no generalizable lesson beyond this specific system.

**Q10.** Per §6, what two fixes are proposed together for the kind of gap this incident revealed?

- A. Removing all monitoring dashboards entirely.
- B. Disabling the affected feature permanently rather than adding any new check.
- C. Only increasing the frequency of dashboard updates, with no new metric.
- D. Adding a task-level metric alongside the step-level one, and retaining a trace per task so a divergence point can be found directly once a failure is identified.

**Q11.** Per §7.4, what does this lesson explicitly NOT cover?

- A. The trace-recording mechanism demonstrated in section 1.
- B. Tracing across multiple agents, building a full evaluation dataset of traced tasks, and automated culprit-finding tools — left to M8-L09's territory, M5-L18's own topic, or as natural extensions.
- C. The step-level versus task-level distinction demonstrated in section 2.
- D. The divergence-finding demonstrated in section 3.

**Q12.** What is the general lesson this lab demonstrates about tracing and task-level evaluation?

- A. Step-level and task-level evaluation always produce identical results, so only one is ever needed.
- B. Tracing is only useful for tasks that have already failed; it provides no value for successful tasks.
- C. A trace makes an agent task's actual sequence of steps inspectable, and evaluating a task requires checking whether its actual outcome matched what was intended — a claim distinct from, and not guaranteed by, every individual step completing without error.
- D. Task-level evaluation is impossible without a live model call.

**Q13.** *(Written, rubric-graded.)* In under 150 words: your team's agent-monitoring dashboard shows 99%
step-level success, but a slowly growing number of customer complaints suggests something is wrong. Based
on this lesson, what would you add, and why?

---

## 12. Revision notes

- **A trace records the actual sequence of steps taken — name, arguments, result or error — not a summary**
  — this is what makes later diagnosis possible at all.
- **Every individual step in a task can succeed while the task itself fails** — measured directly: three
  error-free steps, and a refund sent to the wrong customer.
- **Step-level evaluation and task-level evaluation are genuinely different, both correctly-computed
  claims** — measured directly: `True` and `False` against the identical trace and outcome.
- **A trace identifies the specific divergence point directly, without guessing** — measured directly:
  comparing one step's actual recorded result against what should have been found settled the question.
- **A monitoring system relying only on step-level success has a real, structural blind spot** — the
  general rule §6's worked example illustrates directly, at production scale.

---

## 13. Completion checklist

- [ ] I can implement a trace that records a task's actual sequence of steps.
- [ ] I can demonstrate that step-level success does not guarantee task-level success.
- [ ] I can distinguish step-level from task-level evaluation and explain why they can disagree.
- [ ] I can use a trace to identify the specific step causing a task-level failure.
- [ ] I can diagnose, from a described incident, whether a monitoring gap came from missing tracing or
      step-only evaluation.
- [ ] I evaluate agent tasks at both the step level and the task level, not just one.
- [ ] I scored 10/13 on the quiz.

---

## 14. References

- M5-L18's own evaluation-dataset discipline, extended here from a single call to a whole traced task.
  `[STABLE]`
- OpenTelemetry and similar tracing standards, for how real systems structure distributed traces, where
  available. `[UNVERIFIED]`

---

## 15. Next lesson

→ M8-L18 — Tool Failures, Adversarial Inputs, Framework Choice, and When Not to Use an Agent

This lesson evaluated whether a task succeeded. Next, closing this module: what to do when tools
themselves fail or are attacked, how to choose a framework, and when an agent is the wrong tool for the job
entirely.
