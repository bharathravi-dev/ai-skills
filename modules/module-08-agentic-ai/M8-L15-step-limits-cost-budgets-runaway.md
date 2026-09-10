# M8-L15 — Step Limits, Cost Budgets and Runaway Prevention

| | |
|---|---|
| **Lesson ID** | M8-L15 |
| **Difficulty** | 2 (Intermediate) |
| **Estimated study time** | 1.5 hours |
| **Prerequisites** | M5-L15, [M8-L04](M8-L04-plan-act-observe-stop.md) |

---

## 1. Learning objectives

1. **Demonstrate** that a step-count limit alone cannot distinguish a cheap run from a wildly more
   expensive one of equal length.
2. **Implement** a real cost budget, checked before each step, that stops a loop before it overspends
   regardless of step count.
3. **Implement** runaway detection that recognizes unproductive repetition and stops a loop early, before
   either a step or cost limit is exhausted.
4. **Explain** why step limits, cost budgets, and runaway detection are three distinct mechanisms
   addressing three distinct failure modes.
5. **Diagnose**, from a described incident, which of these three protections was missing or
   insufficiently specific.

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **Step limit** | A hard bound on the number of actions a loop may take (M8-L03's `max_steps`). |
| **Cost budget** | A hard bound on total dollar spend across a loop's run, checked before each step. |
| **Runaway** | A loop repeating an unproductive pattern with no real progress. |
| **Runaway detection** | A check that recognizes a runaway pattern and stops the loop before a hard limit is reached. |
| **Wasted steps** | Steps that ran without contributing to progress, avoidable by stopping earlier. |

---

## 3. Plain-language explanation

### 3.1 M8-L03's step limit was never a cost control

M8-L03 gave every tool-execution loop a hard stop on step count — a real, necessary backstop against a
loop that never naturally terminates. §7.1 shows directly what that bound was never designed to catch: two
runs of the identical length, one twenty times more expensive than the other, because a step limit counts
actions, not what each action costs (M5-L15's own territory, now summed across a whole run).

### 3.2 A cost budget catches what a step limit cannot see

§7.2 doesn't add a second, separate step-count check — it adds a check of a genuinely different kind,
comparing the *next* step's real cost against what's actually left of a dollar budget, and stopping before
that step runs if it would overspend.

### 3.3 Runaway detection catches a third, different problem: no progress at all

§7.3 shows a loop that is neither expensive per step nor anywhere near its step limit, and still needs to
stop — because it is repeating the identical action with no new information, making no real progress. This
is invisible to both a step limit (it hasn't been reached) and a cost budget (cheap repetition doesn't
overspend); it needs its own, different check.

### 3.4 Three mechanisms, three failure modes, none substituting for the others

§7.4 states plainly what the three sections together demonstrate: a step limit is a backstop against
literal infinite loops; a cost budget is the constraint that actually matters financially; runaway detection
is what lets a loop recognize it isn't converging and stop gracefully, before either hard limit forces it
to.

---

## 4. Analogy

**A taxi meter with a distance cap, a fare cap, and a driver who notices they've circled the same block
three times.** A distance cap (drive no more than 50 miles) says nothing about whether those miles were
driven through a cheap, direct route or an expensive, congested one — that's what a fare cap (spend no more
than $80) actually bounds. But neither cap catches a driver who, confused, circles the same city block
repeatedly without making any progress toward the destination at all — cheap per loop, well under both caps,
and still a real problem a good driver would notice and correct without needing to hit either limit first.

### Where the analogy breaks

- **A taxi passenger can watch the meter and the route directly.** §7.3's runaway detection has to infer
  non-progress from the pattern of actions taken, since nothing in this lab's simple loop directly observes
  whether "progress" toward a goal is actually happening — repetition is used as a proxy, not a perfect
  signal.
- **A fare cap is usually known and fixed by the passenger in advance.** A real cost budget might need to
  vary by task, user, or organization — this lesson uses one fixed illustrative budget throughout.

---

## 5. Detailed technical explanation

### 5.1 A step limit measures actions, not their cost

`[REAL, measured]` §7.1 ran two loops, each respecting an identical `max_steps=10` bound: one always
choosing a $0.01 action, one always choosing a $2.00 action. **Both completed exactly 10 steps; their
total costs were $0.10 and $20.00 respectively — a measured 200x difference the step limit itself never
detected or prevented,** because nothing in a step-count check examines what any given step actually costs.

### 5.2 A cost budget stops a step before it overspends, independent of step count

`[REAL, measured]` §7.2 ran the identical always-expensive decider against a $5.00 budget. **The loop
executed exactly 2 real steps ($4.00 total) and stopped itself before a third, which would have brought the
total to $6.00 — over budget — ever ran.** This happened well short of the 10-step limit; the cost budget is
a genuinely separate check, not a rephrasing of the step count.

### 5.3 Runaway detection stops unproductive repetition before either hard limit is reached

`[REAL, measured]` §7.3 ran a decider that always proposes the identical cheap action, regardless of what
has already happened. **Without runaway detection, the loop ran its full 10 steps, spending $0.10 with no
progress at any point. With runaway detection active, the identical decider triggered a stop after exactly
3 steps** — the same action, repeated `repeat_threshold` times in a row — **saving 7 steps that would have
run for no benefit.** Neither the step limit (far from reached) nor a cost budget (spending stayed trivial)
would have caught this on their own.

### 5.4 The three mechanisms compose without overlapping

`[REAL reasoning]` §7.4 states the boundary explicitly, matching what each section measured: a step limit
is the correct backstop against a loop with no natural termination at all; a cost budget is the correct
control on financial exposure, since step count and dollar cost are independent quantities (§5.1); runaway
detection is the correct mechanism for recognizing non-progress specifically, catching a failure mode
neither of the other two is designed to see (§5.3).

### 5.5 Assumptions and limitations

- `stuck_decider()` and `is_runaway()`'s exact-repeat check are small, hand-coded stand-ins — a real
  system's decision logic and a real runaway pattern could be far more subtle than an identical action
  repeated verbatim (an oscillation between two or more states, for instance).
- This lesson does not cover detecting subtler non-convergence patterns, per-user or per-organization
  budget pools spanning many separate agent runs, or how a stopped-early run should report its own outcome
  (M8-L13's honest-recovery discipline, applied here to a budget or runaway stop specifically).

---

## 6. Worked example — the agent that stayed under budget and still cost a fortune

**The system.** An internal research agent is given a step limit of 50 tool calls per task, considered a
generous but safe bound based on typical task complexity, with no separate cost tracking — the team's
reasoning was that 50 calls "couldn't possibly" become expensive.

**The incident.** A specific class of research task caused the agent to repeatedly invoke its most
expensive tool — a long-form generation call, not a cheap lookup — for nearly all 50 of its allotted steps,
on tasks where a well-behaved run typically used only a handful of that tool's calls. The step limit was
respected on every single run; the monthly bill for that task category was nonetheless many times higher
than projected, discovered only when finance flagged the anomaly.

**Why this matches §5.1 exactly.** The team's step limit was calibrated against *typical* task complexity,
implicitly assuming a roughly uniform cost per step — exactly the assumption §7.1's measured 200x gap shows
is unsafe whenever different actions cost meaningfully different amounts. **A step limit alone was never
capable of catching this, regardless of how carefully its numeric value was chosen.**

**Three defects the incident revealed:**

| # | Defect | Consequence |
|---|---|---|
| 1 | Only step count was bounded; no separate dollar-cost budget existed at all | A run using expensive actions almost exclusively stayed fully compliant with the only limit in place |
| 2 | The step limit's calibration assumed roughly uniform per-step cost | The assumption held for typical tasks and broke silently for the specific class that triggered the incident |
| 3 | No runaway or repetition check existed to catch the pattern independently of cost | Even if the expensive tool's cost had been capped, repeated unproductive calls to it would not have been separately flagged |

### The fix

**Add an explicit dollar-cost budget, checked before each step**, per §5.2 — independent of, and in
addition to, the existing step limit.

**Track cost per action type in monitoring**, so a shift toward expensive actions is visible before it
becomes a billing surprise, rather than only being caught by finance after the fact.

**The general rule.** **A step-count limit and a cost budget answer different questions, and calibrating
one carefully does not substitute for having the other — a "safe-looking" step limit can coexist with an
arbitrarily large real-dollar exposure, if nothing separately bounds what each step is allowed to cost.**

---

## 7. Practical activity

**File:** [`labs/m8/l15_step_limits_cost_budgets_runaway.py`](../../labs/m8/l15_step_limits_cost_budgets_runaway.py)

**No API key, no network, no third-party dependencies.** Runs in well under a second.

```bash
source .venv/bin/activate
python labs/m8/l15_step_limits_cost_budgets_runaway.py
```

### 7.2 Expected output

`[EXECUTED]` — 2026-09-10, Python 3.10.11 (pure standard library).

```text
============================================================================
1. A STEP LIMIT ALONE SAYS NOTHING ABOUT DOLLAR COST
============================================================================
  10 steps, always the cheap action:      10 steps, $0.10 total
  10 steps, always the expensive action:  10 steps, $20.00 total

  Both runs respected the IDENTICAL max_steps=10 limit -- and produced
  a 200x difference in real dollar cost. A step-count limit alone
  cannot distinguish these two cases; it was never designed to.

============================================================================
2. A REAL COST BUDGET, CHECKED BEFORE EACH STEP
============================================================================
  Running the SAME always-expensive decider, this time with a real
  $5.00 cost budget instead of only a step count:

    step 1: expensive_generation -> running cost $2.00
    step 2: expensive_generation -> running cost $4.00
    step 3: BUDGET STOP -- 'expensive_generation' would cost $2.00, only $1.00 of the $5.00 budget remains

  Final cost: $4.00 -- the loop stopped itself after 2 real
  steps, well before reaching max_steps=10, because a third expensive
  step would have exceeded the budget. This is exactly what section 1
  had no mechanism to prevent.

============================================================================
3. RUNAWAY DETECTION: STOPPING UNPRODUCTIVE REPETITION EARLY
============================================================================
  A decider stuck proposing the identical action every time, WITHOUT
  runaway detection -- it simply runs to the step limit:
    step 1: cheap_lookup -> running cost $0.01
    step 2: cheap_lookup -> running cost $0.02
    step 3: cheap_lookup -> running cost $0.03
    step 4: cheap_lookup -> running cost $0.04
    step 5: cheap_lookup -> running cost $0.05
    step 6: cheap_lookup -> running cost $0.06
    step 7: cheap_lookup -> running cost $0.07
    step 8: cheap_lookup -> running cost $0.08
    step 9: cheap_lookup -> running cost $0.09
    step 10: cheap_lookup -> running cost $0.10

  Ran the full 10 steps -- $0.10 spent, with NO actual
  progress at any point (the same action, over and over).

  The SAME stuck decider, WITH runaway detection active:
    step 1: cheap_lookup -> running cost $0.01
    step 2: cheap_lookup -> running cost $0.02
    step 3: RUNAWAY DETECTED -- 'cheap_lookup' repeated 3x in a row with no new information -- stopping early

  Stopped after 3 steps instead of 10 -- 7 wasted steps avoided, by
  recognizing the unproductive pattern rather than waiting for a step
  or cost limit to be exhausted first.

============================================================================
4. THREE MECHANISMS, THREE DIFFERENT FAILURE MODES
============================================================================
  Step limit (M8-L03): bounds how many actions run, regardless of
  what each one costs -- section 1 showed this alone misses a real
  200x cost difference between two runs of equal length.

  Cost budget (section 2): bounds real dollar spend directly,
  stopping BEFORE a step that would exceed it -- catching exactly
  what a step-count limit cannot see.

  Runaway detection (section 3): recognizes a loop making no real
  progress and stops EARLY, before either the step limit or the cost
  budget would otherwise be exhausted -- 7 steps saved in this
  lab's own measured comparison.

  None of the three substitutes for the others: a step limit is a
  hard backstop against literally infinite loops; a cost budget is
  the constraint that actually matters financially; runaway
  detection is what lets a loop stop gracefully, before either hard
  limit is reached, when it recognizes it isn't converging.

============================================================================
5. WHAT THIS LAB IS AND IS NOT
============================================================================
  REAL: every cost total, every trace line, and the step-count
  comparison between detected and undetected runaway loops are
  genuinely computed by running this code -- not asserted numbers.

  ILLUSTRATIVE: stuck_decider() and is_runaway()'s exact-repeat check
  are small, hand-coded stand-ins -- a real system's decision logic
  and a real runaway pattern could be far more subtle than an
  identical action repeated verbatim. TOOL_COSTS' specific dollar
  values are this lesson's own illustration.

  NOT SHOWN: detecting subtler non-convergence patterns (oscillating
  between two or more states, rather than repeating one exactly);
  per-user or per-organization budget pools spanning many separate
  agent runs; and how a stopped-early run should report itself (M8-L13's
  own honest-recovery topic, applied here to a budget or runaway stop).

Done.
```

### 7.3 Reading the result

**Section 1's 200x is the number that should change how a step limit is thought about.** It's easy to treat
`max_steps` as "the" safety control for an agent loop; this measurement shows directly that it protects
against only one specific failure mode (unbounded step count), leaving a completely different one
(unbounded cost concentration) entirely open.

**Section 3's "7 wasted steps avoided" is a concrete, not rhetorical, number.** It would be easy to assume a
step limit alone eventually catches a stuck loop — technically true, but only after burning the entire
budget for nothing. Runaway detection's value is specifically in the gap between "eventually stops" and
"stops as soon as it's clear nothing productive is happening."

**Section 4 is worth reading as a checklist, not a summary.** Each of the three mechanisms answers "is
this covered?" for a genuinely different question, and the worked example in §6 shows a real cost of
assuming one mechanism's coverage extends to a risk it was never designed to catch.

---

## 8. Common mistakes and troubleshooting

1. **Treating a step-count limit as sufficient protection against runaway cost.** §5.1, §6 — step count and
   dollar cost are independent quantities, and a step limit says nothing about the latter.
2. **Calibrating a step limit assuming roughly uniform per-step cost.** §6 — this assumption holds for
   typical cases and can fail silently and expensively for an atypical one.
3. **Assuming a cost budget alone catches unproductive repetition.** §5.3 — cheap, repeated, unproductive
   steps can stay well under any reasonable cost budget while making no real progress.
4. **Waiting for a hard limit to catch a stuck loop instead of detecting the pattern directly.** §5.3 —
   this wastes the entire remaining budget on a loop that was never going to converge.
5. **Adding only one of these three mechanisms and assuming the others are unnecessary.** §5.4 — each
   addresses a distinct failure mode; none is a superset of the others.

| Symptom | Likely cause | Fix |
|---|---|---|
| A system's real dollar cost is far higher than expected despite step limits being respected | No separate cost budget exists; different actions cost wildly different amounts | Add an explicit cost budget, checked before each step, per §5.2 |
| A step limit was carefully calibrated but a specific task category still overspends dramatically | The calibration assumed roughly uniform per-step cost, which doesn't hold for that task category | Track and bound cost per action type directly, per §6 |
| A loop runs to its full step or cost limit without producing anything useful | No runaway or repetition detection exists to catch unproductive patterns early | Add a check for repeated identical actions with no new information, per §5.3 |
| Only one of step limits, cost budgets, or runaway detection is implemented, and gaps keep appearing | Each mechanism only covers its own specific failure mode | Implement all three together, per §5.4 |

---

## 9. Security, privacy, reliability, cost

- **Cost.** Add an explicit dollar-cost budget alongside any step-count limit — §7.1's measured 200x gap
  shows a step limit alone provides no real financial bound (§5.1, §6).
- **Cost.** Track cost per action type, not just total steps, so a shift toward expensive actions is
  visible in monitoring before it becomes a billing surprise (§6).
- **Reliability.** Detect unproductive repetition directly rather than relying on a step or cost limit to
  eventually catch it — this saves real, measured waste (§5.3).
- **Reliability.** Implement step limits, cost budgets, and runaway detection together — each is
  necessary, none is sufficient alone (§5.4).

---

## 10. Exercises

### Exercise 1 — Beginner (~20 min)

1. Why did two runs respecting the identical step limit produce a 200x difference in cost in §7.1?
2. What specifically does a cost budget check that a step limit does not?
3. Why did the stuck decider in §7.3 need its own detection mechanism, rather than relying on the cost
   budget?
4. In your own words, what are the three distinct failure modes this lesson addresses?
5. Why was the worked example's team's step limit not sufficient protection, even though it was carefully
   chosen?

### Exercise 2 — Intermediate (~40 min)

1. Run the lab. Confirm §7.1's 200x cost difference, §7.2's budget stop after 2 steps, and §7.3's 7
   wasted-steps comparison on your own machine.
2. Add a third action type with its own cost to `TOOL_COSTS`, and confirm the cost-budget mechanism in
   section 2 correctly accounts for it.
3. Modify `is_runaway()` to detect an oscillating pattern (alternating between two specific actions)
   rather than only an identical repeated action, and test it against a decider that oscillates.
4. Lower `max_cost` in section 2 and confirm the loop stops after fewer real steps, tracing exactly which
   step triggers the stop.
5. Using §5.4's framework, design a combined loop that enforces all three mechanisms (step limit, cost
   budget, runaway detection) together, and test it against both a well-behaved and a stuck decider.

### Exercise 3 — Challenge (~50 min)

1. Design a runaway detector that catches a genuinely subtler pattern than exact repetition (e.g., a loop
   that keeps calling different but semantically equivalent actions with no progress), and explain what
   additional information it would need beyond a simple action-history list.
2. Using M8-L13's honest-recovery principle, design what a budget-stopped or runaway-stopped loop should
   report to its caller, distinguishing this outcome clearly from both success and a genuine step-limit
   exhaustion.
3. Propose a design for a cost budget that varies by task type or user tier rather than being a single
   fixed value, and explain what information would be needed to set it appropriately.
4. Research (conceptually) how a real agent framework or API provider implements spend limits or rate
   limits, and compare it to this lesson's `run_loop_with_cost_budget()`.
5. Using §6's worked example, design a specific monitoring dashboard metric that would have caught the
   shift toward expensive actions before the monthly bill revealed it.

---

## 11. Quiz

*(Answers: [`answer-keys/module-08-answers.md`](../../answer-keys/module-08-answers.md#m8-l15).)*

**Q1.** Per §7.1's measured result, what was the cost difference between two loops both respecting the
identical max_steps=10 limit?

- A. A 200x difference — $0.10 versus $20.00 — because the step limit does not account for what each step costs.
- B. There was no measurable difference.
- C. The cheaper run actually cost more overall.
- D. Exactly a 10% difference.

**Q2.** Per §7.2's measured result, how many real steps did the cost-budget-protected loop execute before
stopping, given a $5.00 budget and $2.00-per-step actions?

- A. All 10 steps ran to completion.
- B. Zero steps ran at all.
- C. Exactly 5 steps.
- D. Exactly 2 steps, stopping before a third would have exceeded the budget.

**Q3.** Per §7.3's measured result, how many steps did the stuck decider's loop run with runaway detection
active, compared to without it?

- A. Both ran the full 10 steps regardless of detection.
- B. 3 steps with detection active, versus the full 10 without it.
- C. Detection caused the loop to run more steps, not fewer.
- D. Neither version of the loop ever executed a single step.

**Q4.** Per §5.3, why didn't the cost budget alone catch the stuck decider's unproductive repetition?

- A. The cost budget was set too high to ever trigger.
- B. The cost budget mechanism contained a bug.
- C. The repeated action was cheap enough that its total cost stayed well under the budget, despite making no real progress.
- D. The stuck decider never actually executed any actions.

**Q5.** Per §5.4, do step limits, cost budgets, and runaway detection substitute for one another?

- A. No — each addresses a distinct failure mode, and none is a superset of what the others catch.
- B. Yes, any single one of the three is sufficient on its own.
- C. Only cost budgets are ever necessary; the other two are redundant.
- D. Only step limits are ever necessary; the other two are redundant.

**Q6.** Per §5.1, what assumption does a step limit implicitly rely on if it is meant to also bound cost?

- A. That the underlying tools never raise exceptions.
- B. That all actions are read-only.
- C. That the loop will never be retried.
- D. That every step costs roughly the same amount, an assumption this lesson's own measurement shows is unsafe in general.

**Q7.** Per §6's worked example, why did the team's carefully-chosen step limit fail to prevent the cost
incident?

- A. The step limit was set far too low.
- B. The step limit's calibration assumed roughly uniform per-step cost, an assumption that broke for a specific task category that used mostly expensive actions.
- C. The team never actually implemented any step limit at all.
- D. The incident was unrelated to step limits or cost in any way.

**Q8.** Per §6, how was the incident eventually discovered?

- A. The agent's own step-limit logging flagged it immediately.
- B. A customer complained about the cost directly.
- C. Finance flagged the anomaly in the monthly bill.
- D. The incident was never discovered.

**Q9.** Per §6, what is the stated general rule this incident illustrates?

- A. A step-count limit and a cost budget answer different questions, and calibrating one carefully does not substitute for having the other.
- B. Step limits should never be used in any agent system.
- C. Cost budgets are unnecessary as long as step limits are set conservatively.
- D. The incident has no generalizable lesson beyond this specific system.

**Q10.** Per §6, what two fixes are proposed for the kind of gap this incident revealed?

- A. Removing all step limits entirely.
- B. Disabling the expensive action entirely rather than tracking its cost.
- C. Only increasing the existing step limit's numeric value.
- D. An explicit dollar-cost budget checked before each step, and tracking cost per action type in monitoring.

**Q11.** Per §7.5, what does this lesson explicitly NOT cover?

- A. The step-limit cost gap demonstrated in section 1.
- B. Detecting subtler non-convergence patterns, per-organization budget pools across many runs, and how a stopped-early run should report itself — left as natural extensions or to M8-L13.
- C. The cost-budget mechanism demonstrated in section 2.
- D. The runaway-detection mechanism demonstrated in section 3.

**Q12.** What is the general lesson this lab demonstrates about step limits, cost budgets, and runaway
prevention?

- A. A single step-count limit is sufficient protection for any agent loop, regardless of cost variation between actions.
- B. Runaway detection alone makes step limits and cost budgets unnecessary.
- C. Step limits, cost budgets, and runaway detection are three distinct mechanisms addressing three distinct failure modes — unbounded step count, unbounded dollar cost, and unproductive non-progress — and each is necessary because none of them covers what the others are designed to catch.
- D. Cost budgets alone make step limits and runaway detection unnecessary.

**Q13.** *(Written, rubric-graded.)* In under 150 words: your team's agent has a step limit of 30 calls,
considered generous and safe. Based on this lesson, what would you ask before trusting that this limit
actually bounds risk, and why?

---

## 12. Revision notes

- **A step-count limit says nothing about dollar cost** — measured directly: two runs of identical length
  produced a 200x cost difference, because the limit counts actions, not what each one costs.
- **A cost budget, checked before each step, stops a loop before it overspends, independent of step
  count** — measured directly: a loop stopped after 2 steps under a $5.00 budget, well short of a 10-step
  limit.
- **Runaway detection catches unproductive repetition that neither a step limit nor a cost budget is
  designed to see** — measured directly: 7 steps of wasted, unproductive repetition avoided by detecting
  the pattern rather than waiting for a hard limit.
- **The three mechanisms address three distinct failure modes and do not substitute for one another** —
  each was shown, directly, to miss what the others catch.
- **A carefully-calibrated step limit is not the same as a cost bound** — the general rule §6's worked
  example illustrates directly, at production scale.

---

## 13. Completion checklist

- [ ] I can explain why a step-count limit alone does not bound dollar cost.
- [ ] I can implement a cost budget that stops a loop before a step would exceed it.
- [ ] I can implement runaway detection that recognizes unproductive repetition and stops early.
- [ ] I can explain why these three mechanisms are each necessary and none is sufficient alone.
- [ ] I can diagnose, from a described incident, which of the three protections was missing.
- [ ] I implement step limits, cost budgets, and runaway detection together, not just one.
- [ ] I scored 10/13 on the quiz.

---

## 14. References

- M5-L15's own per-request token and cost accounting, summed here across an entire agent run. `[STABLE]`
- M8-L03's own `max_steps` bound, extended directly by this lesson's cost budget and runaway detection.
  `[STABLE]`

---

## 15. Next lesson

→ M8-L16 — Sandboxing and Least Privilege for Tools

This lesson bounded how far and how expensively a loop can run. Next: bounding what a tool is actually
capable of doing in the first place, regardless of how many times it's called.
