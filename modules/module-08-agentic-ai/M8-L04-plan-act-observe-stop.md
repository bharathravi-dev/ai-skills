# M8-L04 — Plan, Act, Observe, Stop

| | |
|---|---|
| **Lesson ID** | M8-L04 |
| **Difficulty** | 2 (Intermediate) |
| **Estimated study time** | 2.0 hours |
| **Prerequisites** | [M8-L03](M8-L03-tool-execution-loop.md) |

---

## 1. Learning objectives

1. **Distinguish** a rigid, pre-committed plan from an adaptive, observation-driven decision process, and
   identify which failure mode each one is prone to.
2. **Explain** why "adapts correctly to observations" and "stops at the right time" are two independent
   properties a loop can each have or lack separately.
3. **Implement** a correct stopping condition for a minimization task over a small, enumerable option set.
4. **Demonstrate** that a correctly-implemented tool-execution loop (M8-L03) can still produce a wrong
   answer, and locate exactly which of four phases caused it.
5. **Identify**, from a described incident, which of PLAN, ACT, OBSERVE, or STOP actually failed.

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **Plan** | A decision, made in advance, about what steps to take. |
| **Act** | Executing one step — here, one tool call. |
| **Observe** | Reading back a step's result and treating it as new information. |
| **Stop condition** | The rule that decides whether enough has been observed to give a final answer. |
| **Premature stop** | Stopping before the stop condition is actually satisfied for the task at hand. |
| **Rigid plan** | A plan that is executed regardless of what later observations reveal. |

---

## 3. Plain-language explanation

### 3.1 M8-L03 built the engine; this lesson asks what drives it well or badly

M8-L03's `run_tool_loop()` correctly handles any tools and any decision function — but "correctly handles"
only means the mechanics work. §7.2–§7.4 run the *identical*, unmodified loop three times, varying only the
decision logic, and get three different answers: one wrong, one wrong for a different reason, one right.
The loop was never the problem in any of the three.

### 3.2 A plan made before looking is a plan that can't react to what it finds

§7.2 commits to checking exactly one shipping carrier before any tool has been called, based on a
plausible-sounding default. When that carrier turns out to violate the actual requirement, the plan has
nothing else to try — not because the code is broken, but because reacting to what it observes was never
part of its design.

### 3.3 Reacting correctly and stopping correctly are different skills

§7.3 reacts properly to its very first observation — it correctly moves past an invalid carrier. It still
gets the wrong answer, because it stops as soon as it finds *any* valid option, without asking whether a
cheaper valid one remains unchecked. §7.4 changes nothing except the stopping rule and gets the right
answer, using the exact same loop and the exact same reactive behavior otherwise.

### 3.4 Four phases, four independent places to go wrong

§7.5 names the phases explicitly and locates each variant's specific failure: §7.2 failed at PLAN, §7.3
failed at STOP, and neither failure touched the loop's ACT/OBSERVE mechanics at all — both variants called
their tools correctly and read the results correctly.

---

## 4. Analogy

**A detective who commits to a suspect before the evidence is in, versus one who stops investigating the
moment they find *a* plausible suspect.** The first detective decides, before visiting the scene, who is
guilty, and interprets nothing that follows as grounds to reconsider — a rigid plan, immune to observation.
The second detective genuinely follows each clue where it leads, but arrests the first person with *any*
plausible motive, without checking whether a second suspect with a *stronger* motive is still unquestioned —
adaptive, but stopping on the wrong condition. Only a detective who both follows the evidence *and* keeps
investigating until the question actually asked ("who did it, of everyone with a plausible motive") is fully
answered reaches a reliably correct conclusion.

### Where the analogy breaks

- **A detective's investigation rarely has a fully enumerable suspect list known in advance.** §7.4's
  correct stopping rule (check every known carrier) works specifically *because* this lesson's task has a
  small, fully-known option set — a genuinely open-ended investigation needs a different kind of stopping
  judgment, which this lesson does not cover.
- **A detective operates alone.** M8-L10 covers a further check this analogy has no equivalent for: a
  second party (a human) reviewing the conclusion before it is acted on.

---

## 5. Detailed technical explanation

### 5.1 A rigid plan fails by never revising itself

`[REAL, measured]` §7.2's `plan_first_book()` commits to `["Standard"]` before any tool call, checks it
(genuinely observing 5 days, violating the 3-day requirement), and **books it anyway — the plan contained no
other option to try.** Nothing in this variant is architecturally capable of responding to what it just
observed; the loop that calls the tool and the logic that decides what to do next were never connected.

### 5.2 Reacting to observations does not, by itself, guarantee correctness

`[REAL, measured]` §7.3's decision function genuinely reacts to its first observation — it moves past
Standard once it sees the 5-day figure. **It then stops at the very next valid carrier (Overnight, $30),
reporting it as the answer — without ever checking Express ($12), which remained unchecked.** The final
reported answer is measurably wrong (§7.5: "WRONG (Overnight, $30.00)"), despite every individual
observation being read and acted on correctly.

### 5.3 The only change needed was the stop condition

`[REAL, measured]` §7.4 uses `run_tool_loop()` **unmodified**, and a decision function differing from
§7.3's *only* in when it decides to stop — checking every carrier in the known set before responding, rather
than the first valid one. **This alone changes the reported answer from Overnight ($30) to Express
($12), the genuinely correct minimum.** The ACT and OBSERVE mechanics are, per the lesson's own claim,
byte-for-byte identical between the two variants — confirmed by both reusing the same closure-based
decision-function structure and the same unmodified loop.

### 5.4 Four phases, cleanly separable in the result

`[REAL, measured]` §7.5's table locates each variant's failure at a specific phase: §7.2 (fixed plan, no
adaptation) fails at PLAN; §7.3 (adaptive, wrong stop condition) fails at STOP; §7.4 (adaptive, correct stop
condition) succeeds at both. **None of the three variants differs in how ACT or OBSERVE behave** — every
tool call and every reading of its result is handled identically across all three, by the same
`run_tool_loop()`. The differences are entirely in the decision logic wrapped around it.

### 5.5 Assumptions and limitations

- `make_naive_decider()` and `make_correct_decider()` are small, hand-coded stopping *rules* standing in for
  a real model's judgment about when enough information has been gathered — a real agent reasons about this
  per task, not via a fixed rule.
- §7.4's "check everything" stopping rule is correct specifically because this lesson's task is a
  minimization over a small, fully-known set of three carriers — it does not generalize automatically to an
  open-ended search space, which this lesson does not cover.
- This lesson does not cover genuine multi-step re-planning (revising a plan's *later* steps mid-execution,
  as opposed to §7.2's all-or-nothing rigid plan), validating tool arguments against a schema (M8-L05), or
  human approval before a high-stakes action executes (M8-L10).

---

## 6. Worked example — the itinerary bot that booked the first flight it found

**The system.** A travel-booking assistant is asked to "find and book the cheapest flight that arrives
before 6pm." It searches airlines one at a time and, per its design, books the first flight it finds that
satisfies the arrival-time constraint.

**The incident.** The first airline checked had a flight arriving at 5:45pm for $420. The assistant booked
it immediately. A cheaper flight — $310, arriving at 4:30pm, satisfying the constraint just as well — existed
on an airline checked later in the search order and was never even queried, because the loop had already
stopped.

**Why this matches §5.2 exactly, not §5.1.** The assistant *did* adapt correctly to each observation as it
came in — it wasn't running a rigid, pre-committed plan (§7.2's failure mode). Its failure was purely in the
STOP condition: **it treated "found one option that satisfies the constraint" as equivalent to "found the
best option that satisfies the constraint,"** exactly the gap §7.3 demonstrates for a $12 shipping option
missed in favor of a $30 one.

**Three defects the incident revealed:**

| # | Defect | Consequence |
|---|---|---|
| 1 | The stop condition checked only constraint satisfaction, not optimality among all valid options | A cheaper, equally valid flight was never even queried |
| 2 | The search order (which airline was checked first) silently determined the outcome | The same request could produce a different price depending on an arbitrary implementation detail |
| 3 | Nothing distinguished "adapts to observations" from "stops at the right time" in the system's own design or testing | The bug was invisible until a specific search order happened to surface it |

### The fix

**Separate "does this satisfy the constraint" from "should the search stop now," per §5.3** — the first is a
per-option check; the second is a decision about whether *better* options might remain among what's still
unchecked.

**For a bounded, enumerable option set (a fixed list of airlines queried), check all of them before
deciding**, per §7.4's exact stopping rule, rather than stopping at the first valid one.

**The general rule.** **"Reacts correctly to what it observes" and "stops at the right time" are two
separate properties of a loop's decision logic, and a system can have the first without the second — the
result looks adaptive and well-behaved right up until the specific case where stopping early actually costs
something.**

---

## 7. Practical activity

**File:** [`labs/m8/l04_plan_act_observe_stop.py`](../../labs/m8/l04_plan_act_observe_stop.py)

**No API key, no network, no third-party dependencies.** Runs in well under a second.

```bash
source .venv/bin/activate
python labs/m8/l04_plan_act_observe_stop.py
```

### 7.2 Expected output

`[EXECUTED]` — 2026-09-10, Python 3.10.11 (pure standard library).

```text
============================================================================
1. THE TASK: CHEAPEST CARRIER ARRIVING WITHIN 3 DAYS
============================================================================
  Carriers on file: {'Standard': {'days': 5, 'cost': 5.0}, 'Overnight': {'days': 1, 'cost': 30.0}, 'Express': {'days': 2, 'cost': 12.0}}
  Constraint: days <= 3. Goal: minimum cost among valid carriers.
  Correct answer, computed directly from the table above: Express at $12.00
  Three ways of reaching (or failing to reach) this answer follow.

============================================================================
2. PLAN-FIRST: A PLAN MADE BEFORE ANY OBSERVATION, NEVER REVISED
============================================================================
  [PLAN] committed in advance, before any observation: ['Standard']
  [ACT] check_shipping('Standard') -> [OBSERVE] {'days': 5, 'cost': 5.0}

  Result: booked Standard -- plan contained no other option to try

  Standard genuinely takes 5 days, violating the 3-day constraint -- but the plan was never
  designed to check that constraint against an ALTERNATIVE, only to
  execute what it already decided. A valid, cheaper-than-Overnight
  option (Express) exists and is never even considered.

============================================================================
3. REACT-STYLE, NAIVE STOP: ADAPTS, BUT STOPS AT THE FIRST VALID ANSWER
============================================================================
  Running M8-L03's run_tool_loop() with a NAIVE stop condition:

  [step 1] [ACT] check_shipping({'carrier': 'Standard'}) -> [OBSERVE] {'days': 5, 'cost': 5.0}
  [step 2] [ACT] check_shipping({'carrier': 'Overnight'}) -> [OBSERVE] {'days': 1, 'cost': 30.0}
  [step 3] [STOP] respond -- loop stops

  Reported answer: Overnight at $30.00 -- computed from only ['Overnight', 'Standard'], never checking Express at all.

  This variant DOES react to observations -- it correctly skips past
  Standard once it sees the 5-day observation violates the
  constraint. But it stops the moment it finds ANY valid carrier
  without checking whether a cheaper valid one still unchecked
  (Express, $12) exists. Adapting to observations and stopping
  correctly are two SEPARATE properties -- this variant has the
  first and not the second.

============================================================================
4. REACT-STYLE, CORRECT STOP: CHECKS EVERYTHING BEFORE DECIDING
============================================================================
  Running the SAME run_tool_loop() with a CORRECT stop condition:

  [step 1] [ACT] check_shipping({'carrier': 'Standard'}) -> [OBSERVE] {'days': 5, 'cost': 5.0}
  [step 2] [ACT] check_shipping({'carrier': 'Overnight'}) -> [OBSERVE] {'days': 1, 'cost': 30.0}
  [step 3] [ACT] check_shipping({'carrier': 'Express'}) -> [OBSERVE] {'days': 2, 'cost': 12.0}
  [step 4] [STOP] respond -- loop stops

  Reported answer: Express at $12.00 -- computed from all ['Express', 'Overnight', 'Standard'], the full known set.

  This variant checks all three carriers before stopping, so it
  actually knows Express ($12) beats Overnight ($30) among the valid
  options -- the correct, cheapest answer, verified rather than
  assumed. The only difference from section 3's decide_next() is the
  STOP condition; run_tool_loop() itself, and the ACT/OBSERVE
  mechanics, are byte-for-byte identical between the two.

============================================================================
5. FOUR NAMED PHASES, AND WHICH ONE EACH VARIANT GOT WRONG
============================================================================
  Variant                        Plan      Act/Observe   Stop      Result
  Plan-first (sec. 2)            fixed     n/a           n/a       WRONG (booked Standard, violates 3-day limit)
  React, naive stop (sec. 3)     adaptive  correct       WRONG     WRONG (Overnight, $30.00)
  React, correct stop (sec. 4)   adaptive  correct       correct   RIGHT (Express, $12.00)

  PLAN, ACT, OBSERVE, and STOP are four separate places a loop can
  be wrong, even when the underlying tool-execution mechanics
  (M8-L03) are entirely correct in all three variants above. Section
  2 failed at PLAN -- it never revised its committed plan against an
  observation. Section 3 failed at STOP -- it adapted correctly but
  quit checking too soon. Neither failure is a bug in run_tool_loop()
  itself; both are properties of the decision logic wired into it.

============================================================================
6. WHAT THIS LAB IS AND IS NOT
============================================================================
  REAL: run_tool_loop() is M8-L03's own function, unmodified. All
  three variants' outcomes (the wrong answer from section 2, the
  wrong answer from section 3, the correct answer from section 4)
  are genuinely computed from the same CARRIERS table, not scripted
  to produce a predetermined narrative.

  ILLUSTRATIVE: make_naive_decider() and make_correct_decider() are
  small, hand-coded stopping RULES standing in for a real model's
  judgment about when enough information has been gathered -- a real
  agent reasons about this per task, not via a fixed rule. The
  shipping-carrier domain and its specific numbers are this lesson's
  own illustration, not a claim about real shipping costs.

  NOT SHOWN: genuine multi-step re-planning (revising a plan's later
  steps mid-execution, as opposed to this lesson's all-or-nothing
  rigid plan); validating tool arguments against a schema (M8-L05);
  and human approval before an action executes, which would let a
  person catch section 2's or 3's wrong answer before it was acted
  on (M8-L10).

Done.
```

### 7.3 Reading the result

**Section 3 is this lesson's most important result, precisely because it looks well-behaved.** It reacts
correctly. It doesn't crash. It doesn't hit a step limit. It produces a plausible-looking, confidently
reported final answer — and that answer is wrong, for a reason invisible unless you specifically check
whether cheaper unchecked options existed at the moment it stopped.

**Section 5's table is the payoff of running all three variants side by side.** Reading straight across the
"Result" column shows two different WRONGs with two different causes and one RIGHT, from a Plan/Act-Observe/
Stop breakdown that makes clear neither wrong answer came from the same place.

**The identical `run_tool_loop()` running correctly in all three variants is what makes this convincing.**
If the loop itself had changed between variants, a skeptical reader could attribute the different outcomes
to loop differences. It didn't, so they can't.

---

## 8. Common mistakes and troubleshooting

1. **Committing to a plan before any observation and never revising it.** §5.1 — a plan that can't react to
   what it finds will act on stale assumptions whenever reality diverges from them.
2. **Treating "found a valid answer" as equivalent to "found the best answer."** §5.2, §6 — for a
   minimization or maximization task, satisfying a constraint and being optimal are different conditions.
3. **Assuming a loop that reacts well to observations must also stop at the right time.** §5.2 — these are
   independent properties; verify each separately.
4. **Debugging a wrong answer by inspecting the loop's mechanics first.** §5.4 — if ACT and OBSERVE are
   identical across correct and incorrect variants (as they are here), the defect is in the decision logic,
   not the loop.
5. **Letting an arbitrary iteration order silently determine the final answer.** §6 — a stop condition that
   depends on which option happens to be checked first is not a reliable stop condition.

| Symptom | Likely cause | Fix |
|---|---|---|
| An agent acts on information that later observations contradicted | The plan was committed before observation and never revised | Move the decision logic to react to each observation, per §5.1 |
| An agent reports a valid-looking but suboptimal answer | The stop condition triggers on "any valid option found," not "best option confirmed" | Check every option in a bounded set before stopping, per §5.3 |
| The same request produces different results depending on unrelated implementation details (like ordering) | The stop condition depends on discovery order rather than exhaustive comparison | Make the stop condition independent of order for a bounded, enumerable task, per §5.3 |
| A wrong answer appears even though tool calls and their results all look correct in logs | The defect is in PLAN or STOP, not ACT or OBSERVE | Isolate which phase differs between a correct and incorrect run, per §5.4 |

---

## 9. Security, privacy, reliability, cost

- **Reliability.** Treat "reacts to observations" and "stops correctly" as two properties to verify
  separately — a loop can have one without the other, as §7.3 demonstrates directly (§5.2).
- **Reliability.** For a bounded, enumerable decision, check the full set before stopping rather than the
  first option satisfying a constraint (§5.3, §6).
- **Reliability.** Test a plan-based system specifically against cases where its default assumption is
  wrong — a rigid plan's failure mode only appears when reality diverges from what was assumed (§5.1).
- **Cost.** A premature stop is not only a correctness risk — a valid but non-optimal answer, chosen
  because a cheaper option was never checked, is a direct, measurable cost (§6's flight-booking example).

---

## 10. Exercises

### Exercise 1 — Beginner (~20 min)

1. What are the four phases this lesson names, and which one did §7.2's variant fail at?
2. Why did §7.3's variant get the wrong answer despite correctly reacting to its first observation?
3. What was the only difference between §7.3's decision function and §7.4's?
4. Why is "check everything before stopping" a correct rule specifically for this lesson's task?
5. In your own words, what does it mean for ACT and OBSERVE to be "identical" across all three variants?

### Exercise 2 — Intermediate (~40 min)

1. Run the lab. Confirm all three variants' reported answers in §7.2–§7.4 on your own machine.
2. Add a fourth carrier to `CARRIERS` that is both valid (≤3 days) and cheaper than Express, and re-run all
   three variants. Predict each variant's new reported answer before running it.
3. Modify `CHECK_ORDER` so Express is checked before Overnight, and re-run §7.3's naive-stop variant. Does
   the reported answer change? Why or why not?
4. Design a stop condition that is correct but checks fewer than all three carriers in some cases (a "early
   exit when no cheaper option could possibly remain" optimization), and explain what property of the task
   makes this safe.
5. Using §7.5's table format, add a fourth variant to the lab that combines a rigid plan with a correct stop
   condition, and explain what its outcome will be before running it.

### Exercise 3 — Challenge (~50 min)

1. Design a decision function implementing genuine re-planning: it commits to an initial plan, but revises
   its remaining steps if an observation contradicts the plan's assumption, rather than either executing
   blindly (§7.2) or having no plan structure at all (§7.3–§7.4).
2. Using M8-L02's blast-radius framework, argue for or against adding a human-approval step specifically
   between STOP and the final action, for this lesson's shipping-carrier task, versus a higher-stakes task.
3. Design a task where "check everything before stopping" (§7.4's rule) is NOT feasible (the option space is
   too large or open-ended), and propose an alternative stop condition appropriate for it.
4. Research (conceptually) how a real agent framework's "ReAct" pattern differs from a "plan-and-execute"
   pattern, and compare both to this lesson's three variants.
5. Using §6's worked example, write a test case (inputs and expected outcome) that would have caught the
   itinerary bot's bug before it reached production.

---

## 11. Quiz

*(Answers: [`answer-keys/module-08-answers.md`](../../answer-keys/module-08-answers.md#m8-l04).)*

**Q1.** Per §7.2's measured result, why did the plan-first variant book an invalid shipping option?

- A. The plan was committed to a single carrier before any observation, and contained no alternative to try once that carrier was observed to violate the constraint.
- B. The check_shipping tool returned incorrect data.
- C. The loop crashed before the constraint could be checked.
- D. The constraint itself was defined incorrectly in the code.

**Q2.** Per §7.3's measured result, what specifically caused the naive-stop variant to report Overnight
($30) instead of Express ($12)?

- A. Express was not actually a valid option under the stated constraint.
- B. The tool call for Express raised an exception.
- C. run_tool_loop() itself contains a bug specific to this scenario.
- D. The decision function stopped as soon as it found any carrier satisfying the constraint, without checking whether a cheaper valid one remained unchecked.

**Q3.** Per §7.3, did the naive-stop variant correctly react to its observation that Standard violated the
constraint?

- A. No — it never checked Standard at all.
- B. Yes — it correctly moved past Standard once it observed the 5-day figure; its failure was specifically in the stop condition, not in reacting to observations.
- C. No — it booked Standard despite observing that it was invalid.
- D. The question does not apply, since this variant made no observations.

**Q4.** Per §7.4's measured result, what was the only change from §7.3's decision function that produced
the correct answer?

- A. A completely different tool set was used.
- B. max_steps was increased significantly.
- C. The stop condition changed to check every known carrier before responding, rather than stopping at the first valid one.
- D. run_tool_loop() itself was modified to compute the minimum directly.

**Q5.** Per §7.4, were run_tool_loop()'s ACT and OBSERVE mechanics different between the naive-stop and
correct-stop variants?

- A. No — both variants reuse the identical, unmodified loop; only the stop condition in the decision function differs.
- B. Yes — the correct-stop variant used a modified version of run_tool_loop().
- C. Yes — the correct-stop variant used entirely different tools.
- D. The comparison is not meaningful because the two variants ran on different data.

**Q6.** Per §7.5's table, which phase did the plan-first variant (section 2) fail at?

- A. STOP.
- B. OBSERVE.
- C. ACT.
- D. PLAN.

**Q7.** Per §7.5's table, which phase did the naive-stop variant (section 3) fail at?

- A. ACT.
- B. STOP.
- C. PLAN.
- D. OBSERVE.

**Q8.** Per §7.5, did ACT or OBSERVE differ between any of the three variants in this lab?

- A. Yes, ACT differed significantly across all three variants.
- B. Yes, OBSERVE differed significantly across all three variants.
- C. No — all three variants used identical ACT/OBSERVE mechanics from the same unmodified run_tool_loop(); the differences were entirely in PLAN and STOP logic.
- D. The lesson does not address this question.

**Q9.** Per §6's worked example, why did the itinerary bot's failure match §5.2 (the naive-stop pattern)
rather than §5.1 (the rigid-plan pattern)?

- A. Because the bot genuinely adapted to each observation as it searched, and its failure was specifically in stopping at the first valid flight rather than checking for a cheaper valid one.
- B. Because the bot crashed when it encountered the second airline.
- C. Because the bot never made any tool calls at all.
- D. Because the bot's plan was fixed before any airline was checked, identical to section 2's pattern.

**Q10.** Per §6, what specifically made the itinerary bot's bug hard to notice before it caused a real
cost?

- A. The bug only affected the loop's ACT mechanics, which were rarely logged.
- B. The system had no tools at all, so no logs existed.
- C. The bug caused an immediate, visible crash on every request.
- D. The bot's behavior looked adaptive and well-behaved, and the bug depended on a specific search order that happened to surface a cheaper unchecked option.

**Q11.** Per §7.6, what does this lesson explicitly NOT cover?

- A. The four named phases (plan, act, observe, stop) demonstrated in sections 2 through 5.
- B. Genuine multi-step re-planning, validating tool arguments against a schema, and human approval before a high-stakes action — left to later coverage or to M8-L05 and M8-L10 respectively.
- C. The comparison table in section 5.
- D. The three decision-function variants in sections 2 through 4.

**Q12.** What is the general lesson this lab demonstrates about a tool-execution loop's correctness?

- A. A correctly-implemented tool-execution loop (M8-L03) guarantees a correct final answer regardless of the decision logic wrapped around it.
- B. Only the STOP phase can ever cause an incorrect final answer.
- C. Reacting correctly to observations and stopping at the right time are independent properties, and a loop with entirely correct ACT/OBSERVE mechanics can still produce a wrong final answer through a flawed PLAN or STOP decision.
- D. A rigid, pre-committed plan is always superior to an adaptive, observation-driven approach.

**Q13.** *(Written, rubric-graded.)* In under 150 words: your team's agent correctly calls its tools and
correctly reads their results in every logged run, but sometimes reports a suboptimal answer. Based on this
lesson, where would you look first, and what specifically would you check?

---

## 12. Revision notes

- **A plan committed before any observation, with no mechanism to revise it, fails when its founding
  assumption turns out wrong** — measured directly: a rigid plan booked an invalid shipping option because
  it had no alternative to try.
- **Reacting correctly to observations and stopping at the right time are independent properties** —
  measured directly: an adaptive decision function still produced a wrong (suboptimal) answer purely
  because of its stop condition.
- **For a minimization or maximization task over a bounded, enumerable set, a correct stop condition
  checks every option, not just the first one satisfying a constraint** — measured directly: this single
  change was the only difference between a wrong and a correct final answer.
- **PLAN, ACT, OBSERVE, and STOP are four separable phases, each independently capable of causing an
  incorrect result** — even while the underlying tool-execution loop (M8-L03) performs ACT and OBSERVE
  identically and correctly across every variant.
- **A loop that looks well-behaved (no crashes, no runaway steps, plausible-looking output) can still be
  wrong** — the defect is only visible by checking whether a better, unchecked option existed at the moment
  the loop decided to stop.

---

## 13. Completion checklist

- [ ] I can name the four phases this lesson identifies and give an example failure at each of PLAN and
      STOP.
- [ ] I can explain why reacting to observations does not guarantee a correct stopping decision.
- [ ] I can implement a correct stop condition for a minimization task over a bounded, enumerable set.
- [ ] I can identify, from a wrong-answer incident, which of the four phases most likely failed.
- [ ] I can explain why ACT and OBSERVE being correct does not guarantee a correct final answer.
- [ ] I check whether a loop's stop condition verifies optimality, not just constraint satisfaction, for
      tasks that need it.
- [ ] I scored 10/13 on the quiz.

---

## 14. References

- Yao et al., *ReAct: Synergizing Reasoning and Acting in Language Models*, 2022, for the react-style
  pattern this lesson's adaptive variants illustrate. `[UNVERIFIED]`
- Anthropic, *Building Effective Agents*, on planning versus reactive execution patterns, where available.
  `[UNVERIFIED]`

---

## 15. Next lesson

→ M8-L05 — Tool Schemas and Argument Validation

This lesson assumed each tool call's arguments were already well-formed. Next: what happens when they
aren't, and how a schema catches a malformed or dangerous argument before it ever reaches a tool.
