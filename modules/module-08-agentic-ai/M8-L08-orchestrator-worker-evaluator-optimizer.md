# M8-L08 — Orchestrator-Worker and Evaluator-Optimizer Patterns

| | |
|---|---|
| **Lesson ID** | M8-L08 |
| **Difficulty** | 3 (Advanced) |
| **Estimated study time** | 2.0 hours |
| **Prerequisites** | [M8-L07](M8-L07-routing-chaining-parallel.md) |

---

## 1. Learning objectives

1. **Distinguish** orchestrator-worker's dynamic decomposition from M8-L07's fixed-shape routing, chaining,
   and parallel execution.
2. **Demonstrate** that an orchestrator's subtask count and composition can genuinely vary with the
   request, not just its output content.
3. **Implement** an evaluator-optimizer loop that revises a draft based on specific, named feedback rather
   than a generic pass/fail signal.
4. **Demonstrate** the difference between a generator that genuinely improves with feedback and one that
   cannot satisfy a requirement regardless of how many attempts it gets.
5. **Apply** a two-question framework to decide whether a task needs orchestrator-worker,
   evaluator-optimizer, or one of M8-L07's fixed shapes.

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **Orchestrator-worker** | A pattern where one component decomposes a task into subtasks and dispatches each to a worker. |
| **Dynamic decomposition** | Subtask count and composition that genuinely varies per request, rather than being fixed in advance. |
| **Evaluator-optimizer** | A pattern where a generated candidate is checked against explicit criteria and revised if it fails. |
| **Specific feedback** | An evaluation result that names exactly what failed, not just whether something failed. |
| **Cumulative revision** | A generator that retains every previously-satisfied criterion across attempts, rather than forgetting one while fixing another. |

---

## 3. Plain-language explanation

### 3.1 M8-L07's shapes were all fixed in advance; these two aren't

Routing, chaining, and parallel execution (M8-L07) all have a set of steps that's known before the request
arrives — three warehouses, a fixed sequence, three mutually exclusive categories. §7.1 and §7.2 both
involve a decision that genuinely depends on the specific request or the specific output, not a
pre-determined shape.

### 3.2 An orchestrator's job is to decide how many workers, not just which one

§7.1 runs two different compound requests through the same orchestrator and gets two different subtask
counts — two workers for one request, three for the other. This is the property that separates
orchestrator-worker from M8-L07's parallel execution: parallel execution ran the same fixed three calls
regardless of input; here, the *number* of calls is itself part of what gets decided.

### 3.3 An evaluator's value is in naming what's wrong, not just that something is

§7.2's evaluator doesn't return a single pass/fail bit — it names exactly which required topics are still
missing. The generator's second attempt genuinely differs from its first specifically because of that named
feedback, and a second, harder case shows the same loop honestly giving up, rather than either looping
forever or pretending to succeed, when a requirement truly can't be met.

### 3.4 One framework, matching what was actually measured

§7.3's two-question framework — does the decomposition vary with the request, does the output need
checking against explicit criteria — recommends exactly the pattern each earlier section demonstrated,
because it was derived from what those sections measured, not proposed independently of it.

---

## 4. Analogy

**A project manager assigning subcontractors, versus an editor sending a manuscript back for specific
revisions.** A project manager surveying a renovation job doesn't call the same fixed three subcontractors
for every job — a small repair might need only a plumber; a full renovation might need a plumber,
electrician, and carpenter. The number and mix of subcontractors is decided *from the job itself*. An editor
reviewing a manuscript doesn't just say "this isn't ready" — they mark exactly which sections are unclear,
which claims are unsupported, which format rules were missed, and the writer's next draft addresses those
specific notes, not a vague sense that something needed fixing.

### Where the analogy breaks

- **A project manager can always find a subcontractor for any trade needed.** §7.2's Case B shows a
  generator that genuinely cannot produce a specific kind of content (warranty information) no matter how
  many revision rounds it gets — a limit an editor's writer usually doesn't have in the same absolute way.
- **An editor's notes are read and applied by a human who remembers all of them at once.** §7.2's fix
  specifically had to make the generator accumulate *every* piece of feedback it had ever received, not just
  the most recent round's — a real risk this lesson's own first draft of the code actually hit.

---

## 5. Detailed technical explanation

### 5.1 Subtask count is a real, measured variable, not a fixed constant

`[REAL, measured]` §7.1 ran `decompose_task()` against two requests: one mentioning price and shipping
(decomposing into 2 subtasks) and one also mentioning returns (decomposing into 3). **The number of workers
`orchestrate()` dispatched genuinely differed — 2 versus 3 — driven entirely by the request's own content.**
Once decomposed, the subtasks were run in parallel via the identical `ThreadPoolExecutor` mechanism M8-L07
used, because at that point they are genuinely independent of each other — orchestrator-worker's
distinguishing property is entirely in the *decomposition* step, not in how the resulting subtasks execute.

### 5.2 Specific feedback produced a genuinely different second draft

`[REAL, measured]` §7.2's Case A ran `evaluator_optimizer()` against a three-topic requirement. Attempt 1's
draft was missing "returns"; the evaluator named this specifically; **attempt 2's draft genuinely included a
returns clause the first did not, and passed.** The revision was driven by the evaluator's specific,
named output, not a generic retry.

### 5.3 A real fix was needed to make revision genuinely cumulative

`[REAL, measured]` The lab's first working version tracked only the *most recent* round's feedback, and Case
B's third attempt lost the "returns" clause it had already correctly added on attempt 2, because attempt
3's own feedback happened to focus on "warranty" alone. **The fix — accumulating every piece of feedback
ever received into `feedback_ever_seen`, rather than only the last round's — is itself evidence for this
lesson's point**: a generator revising based on feedback needs to retain every previously-satisfied
criterion, not just react to whatever the most recent evaluation happened to flag.

### 5.4 A genuinely unsatisfiable requirement produces an honest give-up

`[REAL, measured]` With the fix in place, §7.2's Case B correctly retained the returns clause from attempt
2 onward, while "warranty" — content this generator has no mechanism to produce at all — remained missing
through all 3 attempts. **The loop reported `None` and an honest "gave up" message, rather than looping
indefinitely or fabricating a passing result.** This is the same bounded-loop discipline M8-L03's
`max_steps` established, applied here to revision attempts rather than tool calls.

### 5.5 Assumptions and limitations

- `decompose_task()` and `generate_draft()` are small, hand-coded stand-ins for a real model's judgment and
  generation — a real system uses actual model calls for both, not keyword rules.
- This lesson does not cover an orchestrator that decides *how* to combine worker results beyond simple
  concatenation, an evaluator whose criteria are themselves generated or learned rather than fixed in
  advance, or running both patterns together in one system (a worker's own output being evaluated and
  revised, for instance).

---

## 6. Worked example — the report generator that "revised" itself in circles

**The system.** An internal report generator produces a weekly summary, checked by an automated reviewer
against a list of required sections. When a section is missing, the reviewer's feedback is passed back to
the generator for a new attempt.

**The incident.** The generator's revision logic considered only the *most recent* reviewer note, discarding
which sections earlier rounds had already fixed. A report missing both a "risks" section and a "budget"
section went through several rounds where each fix "undid" a previous one — the generator would add the
risks section (because that round's note flagged it), lose the budget section on the next round (because
that round's note focused elsewhere), and the report never converged to something satisfying all
requirements within the attempt limit.

**Why this matches §5.3 exactly.** This is the identical bug this lesson's own first implementation had,
before the fix: **feedback was tracked per-round instead of cumulatively**, so a criterion satisfied in one
round could be silently lost in the next, purely because that round's feedback happened to be about
something else.

**Three defects the incident revealed:**

| # | Defect | Consequence |
|---|---|---|
| 1 | The generator's revision state considered only the latest feedback, not the accumulated history | A previously-fixed requirement could regress without any new feedback ever flagging it as broken |
| 2 | The evaluator's pass/fail check did not track which requirements had been separately verified in earlier rounds | There was no record showing a requirement had already been satisfied once |
| 3 | The attempt limit was reached without the report ever converging, despite each individual round's fix being locally correct | The system consumed its full retry budget for a report that should have succeeded well before the limit |

### The fix

**Accumulate feedback across every round, not just the most recent one**, per §5.3 — this lesson's own
lab required exactly this change to produce Case B's correct, non-regressing behavior.

**Design the generator to treat every previously-satisfied criterion as a standing requirement**, not
something to be re-derived from the latest note alone.

**The general rule.** **An evaluator-optimizer loop's generator needs memory of every requirement it has
ever been told to satisfy, not just the current round's complaint — otherwise, fixing one problem can
silently reintroduce another, and the loop may never converge even when every individual round's revision
was, in isolation, a correct response to that round's feedback.**

---

## 7. Practical activity

**File:** [`labs/m8/l08_orchestrator_worker_evaluator_optimizer.py`](../../labs/m8/l08_orchestrator_worker_evaluator_optimizer.py)

**No API key, no network, no third-party dependencies.** Runs in well under a second.

```bash
source .venv/bin/activate
python labs/m8/l08_orchestrator_worker_evaluator_optimizer.py
```

### 7.2 Expected output

`[EXECUTED]` — 2026-09-10, Python 3.10.11 (pure standard library).

```text
============================================================================
1. ORCHESTRATOR-WORKER: DECOMPOSITION THAT VARIES WITH THE REQUEST
============================================================================
  Request: 'Tell me about the price and shipping for this item.'
    Decomposed into 2 subtask(s): ['price', 'shipping']
    Combined response: 'Price: $49.99. Ships in 2-3 business days.'

  Request: 'Tell me about the price, shipping, and return policy for this item.'
    Decomposed into 3 subtask(s): ['price', 'shipping', 'returns']
    Combined response: 'Price: $49.99. Ships in 2-3 business days. Returns accepted within 30 days.'

  The SECOND request decomposed into one more subtask than the
  FIRST -- the number of workers dispatched genuinely varies with
  what the request actually asks for. Contrast this with M8-L07's
  parallel section, which always ran the SAME fixed three warehouse
  checks regardless of input: there, the set of independent calls
  was known in advance; here, the orchestrator decides it per request.

============================================================================
2. EVALUATOR-OPTIMIZER: GENERATE, CHECK, REVISE BASED ON WHAT FAILED
============================================================================
  Case A -- a requirement the generator CAN satisfy once told what's missing:
    attempt 1: 'Price: $49.99. Ships in 2-3 business days.'
      evaluator: missing=['returns']
    attempt 2: 'Price: $49.99. Ships in 2-3 business days. Returns accepted within 30 days.'
      evaluator: missing=[]
      PASSED on attempt 2
  Final result: 'Price: $49.99. Ships in 2-3 business days. Returns accepted within 30 days.'

  Case B -- a requirement (warranty info) this generator can NEVER
  produce, regardless of feedback:
    attempt 1: 'Price: $49.99. Ships in 2-3 business days.'
      evaluator: missing=['returns', 'warranty']
    attempt 2: 'Price: $49.99. Ships in 2-3 business days. Returns accepted within 30 days.'
      evaluator: missing=['warranty']
    attempt 3: 'Price: $49.99. Ships in 2-3 business days. Returns accepted within 30 days.'
      evaluator: missing=['warranty']
    GAVE UP after 3 attempts -- still missing ['warranty']
  Final result: None

  Case A shows genuine improvement: the second attempt's draft is
  DIFFERENT from the first, specifically because the evaluator's
  feedback named what was missing. Case B shows the loop honestly
  giving up after a real, enforced attempt limit, rather than either
  looping forever or falsely reporting success -- the same bounded-
  loop discipline M8-L03's max_steps established, applied here to
  revision attempts instead of tool calls.

============================================================================
3. A FRAMEWORK: WHICH PATTERN FITS WHICH NEED
============================================================================
    ORCHESTRATOR-WORKER (subtask count/shape varies with the request)
      -- A compound request whose number of sub-topics varies per customer

    EVALUATOR-OPTIMIZER (generate, check against criteria, revise)
      -- A single generated answer that must satisfy several explicit, checkable criteria

    A FIXED SHAPE FROM M8-L07 IS LIKELY SUFFICIENT (routing/chaining/parallel)
      -- Three always-present, independent warehouse stock checks (M8-L07)

  This matches exactly what sections 1-2 measured: the orchestrator's
  subtask count genuinely changed between two real requests (2 vs 3
  workers), and the optimizer's second draft genuinely differed from
  its first because of specific, named evaluator feedback -- neither
  property appears in M8-L07's fixed-shape patterns.

============================================================================
4. WHAT THIS LAB IS AND IS NOT
============================================================================
  REAL: decompose_task() genuinely produces a different subtask list
  for the two requests in section 1; the ThreadPoolExecutor dispatch
  is real, reused from M8-L07; and evaluate() in section 2 performs a
  real, executed keyword check whose result genuinely determines
  whether the loop stops or continues.

  ILLUSTRATIVE: decompose_task() and generate_draft() are small,
  hand-coded stand-ins for a real model's judgment and generation --
  a real system uses actual model calls for both, not keyword rules.
  The specific product-description domain is this lesson's own
  illustration, not a claim about real e-commerce systems.

  NOT SHOWN: an orchestrator that itself decides HOW to combine
  worker results beyond simple concatenation; an evaluator whose
  criteria are themselves generated or learned rather than fixed in
  advance; and running orchestrator-worker and evaluator-optimizer
  together in one system (a worker's own output being evaluated and
  revised, say) -- a natural extension left to the exercises.

Done.
```

### 7.3 Reading the result

**Section 1's "2 vs 3" is a small number carrying a large point.** It would be easy to build an
orchestrator that always dispatches the same fixed set of workers and call it "orchestrator-worker" anyway;
measuring that the count genuinely changes with the request is what actually distinguishes this pattern from
M8-L07's parallel execution.

**Section 2's honest bug-and-fix, documented directly in §5.3, is the most valuable single result in this
lesson.** It would have been easy to write a generator that happened to work for the two demonstrated cases
without ever noticing the per-round-only feedback flaw; the flaw surfaced specifically because Case B pushed
the loop through three full rounds, and §6 shows the identical failure at production scale.

**Case A and Case B are not two random examples — they are a deliberate pair.** One shows the pattern
working exactly as intended; the other shows what an honest limit looks like when the pattern's assumption
(the generator *can* eventually satisfy the requirement) doesn't hold.

---

## 8. Common mistakes and troubleshooting

1. **Calling a fixed, pre-determined set of parallel calls "orchestrator-worker."** §5.1 — the distinguishing
   property is that the decomposition itself varies with the request, not merely that multiple workers run.
2. **Giving an evaluator only a pass/fail signal instead of specific, named feedback.** §5.2 — a generator
   revising from "no" alone has nothing concrete to change; naming what's missing is what makes revision
   possible.
3. **Tracking only the most recent round's feedback in a revision loop.** §5.3, §6 — this lesson's own bug:
   a fix satisfied in one round can be silently lost in the next if the generator doesn't retain it.
4. **Looping indefinitely, or falsely reporting success, when a requirement genuinely cannot be met.** §5.4
   — an evaluator-optimizer loop needs the same honest, bounded give-up M8-L03's `max_steps` established.
5. **Assuming an evaluator-optimizer loop will always converge given enough attempts.** §5.4 — some
   requirements are outside what a given generator can ever produce, regardless of attempt count.

| Symptom | Likely cause | Fix |
|---|---|---|
| A "multi-worker" system always dispatches the same fixed set of calls regardless of input | It is actually a parallel-execution pattern (M8-L07), not genuine orchestrator-worker | Confirm decomposition itself varies with the request, per §5.1, before calling it orchestrator-worker |
| A revision loop's drafts don't clearly improve across attempts | The evaluator returns only pass/fail, with no specific detail about what's wrong | Have the evaluator name exactly which criteria failed, per §5.2 |
| A previously-fixed issue reappears in a later revision attempt | Only the most recent round's feedback is tracked, not the full accumulated history | Accumulate feedback across all rounds, per §5.3 and §6 |
| A revision loop runs to its attempt limit without ever succeeding | The requirement may be genuinely outside what the generator can produce | Confirm the loop gives up honestly rather than looping forever, per §5.4, and investigate the generator's actual limitation |

---

## 9. Security, privacy, reliability, cost

- **Reliability.** Confirm a "multi-worker" pattern's decomposition genuinely varies with the request before
  calling it orchestrator-worker — a fixed decomposition is M8-L07's parallel pattern, not this one (§5.1).
- **Reliability.** Design evaluators to name specific failures, not just report pass/fail — this is what
  makes a subsequent revision attempt meaningfully different rather than a repeated guess (§5.2).
- **Reliability.** Accumulate feedback across all revision rounds — §5.3 and §6 both show a real regression
  that results from tracking only the most recent round.
- **Cost.** Bound revision attempts and give up honestly when a requirement cannot be met, rather than
  consuming unlimited retries on an unsatisfiable criterion (§5.4).

---

## 10. Exercises

### Exercise 1 — Beginner (~20 min)

1. What property distinguishes orchestrator-worker from M8-L07's parallel execution pattern?
2. Why did the two requests in §7.1 produce different numbers of subtasks?
3. Why does an evaluator's specific, named feedback matter more than a plain pass/fail result?
4. What bug did this lesson's own lab have to fix, and why did it matter?
5. What happened when Case B's requirement genuinely could not be satisfied, and why was that the correct
   outcome?

### Exercise 2 — Intermediate (~40 min)

1. Run the lab. Confirm §7.1's 2-vs-3 subtask counts and §7.2's Case A pass and Case B give-up on your own
   machine.
2. Add a third, different compound request to §7.1 and predict its subtask count before running it.
3. Add a fourth required topic to Case A (one the generator CAN satisfy) and confirm the loop still
   converges, tracking how many attempts it now takes.
4. Deliberately revert §7.2's fix (track only the most recent round's feedback instead of the accumulated
   set) and re-run Case B. Confirm you reproduce the regression described in §5.3, then restore the fix.
5. Using §5.5's framework, classify three real multi-step tasks from a system you're familiar with as
   orchestrator-worker, evaluator-optimizer, or one of M8-L07's fixed shapes.

### Exercise 3 — Challenge (~50 min)

1. Extend the orchestrator so it decides not just which workers to call but how to weight or prioritize
   their combined output, and explain what new decision this introduces beyond decomposition alone.
2. Design an evaluator whose criteria are more than simple keyword presence (e.g., checking a numeric value
   falls within a range, or that two fields are mutually consistent), and integrate it into the
   evaluator-optimizer loop.
3. Combine both patterns: build an orchestrator that dispatches a subtask to a worker, then runs that
   worker's own output through an evaluator-optimizer loop before combining results.
4. Research (conceptually) how a real multi-agent framework represents an orchestrator's dynamic task
   decomposition, and compare it to this lesson's `decompose_task()`.
5. Using §6's worked example, design a specific test case that would have caught the cumulative-feedback
   bug before it reached production.

---

## 11. Quiz

*(Answers: [`answer-keys/module-08-answers.md`](../../answer-keys/module-08-answers.md#m8-l08).)*

**Q1.** Per §7.1's measured result, what specifically distinguished the two requests' outcomes?

- A. The second request decomposed into one more subtask than the first, because it mentioned an additional topic the first did not.
- B. Both requests decomposed into the identical number of subtasks.
- C. The first request failed to decompose at all.
- D. The number of subtasks was fixed at three regardless of the request.

**Q2.** Per §5.1, what property distinguishes orchestrator-worker from M8-L07's parallel execution
pattern?

- A. Orchestrator-worker never uses concurrent execution at all.
- B. Parallel execution always uses more workers than orchestrator-worker.
- C. There is no meaningful distinction between the two patterns.
- D. In orchestrator-worker, the decomposition itself (the number and composition of subtasks) genuinely varies with the request; in M8-L07's parallel pattern, the set of independent calls was fixed in advance.

**Q3.** Per §7.2's measured result, why did Case A's second attempt succeed where the first failed?

- A. The second attempt used a completely different generator function.
- B. The evaluator's specific feedback named "returns" as missing, and the generator's second draft genuinely included a returns clause the first did not.
- C. The evaluator's criteria were relaxed between attempts.
- D. The max_attempts limit was increased between the two attempts.

**Q4.** Per §5.3, what bug did this lesson's own lab implementation have to fix?

- A. The evaluator never checked for the "returns" topic at all.
- B. The loop had no attempt limit and ran indefinitely.
- C. The generator tracked only the most recent round's feedback, causing a previously-fixed requirement to regress in a later attempt.
- D. The ThreadPoolExecutor caused a race condition in the orchestrator.

**Q5.** Per §7.2's measured result, what happened in Case B after the fix was applied?

- A. The returns requirement, once satisfied, stayed satisfied in later attempts, while the warranty requirement remained missing through all 3 attempts, and the loop honestly gave up.
- B. The loop falsely reported success despite the warranty requirement never being satisfied.
- C. The loop looped indefinitely without ever stopping.
- D. Both the returns and warranty requirements were satisfied by attempt 2.

**Q6.** Per §5.4, why is Case B's "gave up" outcome described as correct rather than a failure of the
lesson's design?

- A. Because giving up is always the correct outcome for any evaluator-optimizer loop.
- B. Because Case B was not actually run to completion.
- C. Because the evaluator was broken and could not correctly check anything.
- D. Because the requirement (warranty information) was genuinely outside what this generator could ever produce, and honestly reporting this is preferable to looping forever or fabricating success.

**Q7.** Per §6's worked example, what specific bug caused the report generator to "revise in circles"?

- A. The evaluator never provided any feedback to the generator.
- B. The generator's revision logic considered only the most recent reviewer note, so a previously-fixed section could be lost when a later round's feedback focused elsewhere.
- C. The report had no required sections defined at all.
- D. The attempt limit was set to zero.

**Q8.** Per §6, what is the stated general fix for the kind of regression the report generator exhibited?

- A. Remove the automated reviewer and rely on manual review only.
- B. Increase the attempt limit indefinitely.
- C. Accumulate feedback across every round, and design the generator to treat every previously-satisfied criterion as a standing requirement, not something to be re-derived from the latest note alone.
- D. Ignore all reviewer feedback and generate a single, unrevised report.

**Q9.** Per §7.3's framework, which factor determines whether a task needs orchestrator-worker rather than
evaluator-optimizer?

- A. Whether the task's decomposition into subtasks genuinely varies with the specific request.
- B. Whether the output needs to be checked against explicit criteria and possibly revised.
- C. Whether the task involves any tool calls at all.
- D. Whether the task can be completed in a single step.

**Q10.** Per §7.3, did the framework's recommendations match what sections 1 and 2 actually measured?

- A. No, the framework contradicted what was measured in both sections.
- B. The framework was not applied to sections 1 and 2's own scenarios.
- C. The framework only applies to hypothetical future scenarios.
- D. Yes — the framework recommended exactly the pattern each section actually demonstrated, because it was derived from what was measured, not proposed independently.

**Q11.** Per §7.4, what does this lesson explicitly NOT cover?

- A. The orchestrator-worker pattern demonstrated in section 1.
- B. An orchestrator that decides HOW to combine worker results beyond simple concatenation, an evaluator with learned criteria, and running both patterns together in one system — left as natural extensions.
- C. The evaluator-optimizer pattern demonstrated in section 2.
- D. The two-question framework in section 3.

**Q12.** What is the general lesson this lab demonstrates about orchestrator-worker and
evaluator-optimizer?

- A. Both patterns are identical to M8-L07's fixed shapes and offer no additional capability.
- B. Evaluator-optimizer loops always converge given enough attempts, regardless of the requirement.
- C. Orchestrator-worker's decomposition and evaluator-optimizer's revision both genuinely depend on the specific request or output, rather than following a shape fixed in advance — and evaluator-optimizer additionally requires the generator to retain feedback cumulatively, not just from the most recent round.
- D. Orchestrator-worker never needs any form of concurrent execution.

**Q13.** *(Written, rubric-graded.)* In under 150 words: your team's evaluator-optimizer loop keeps
producing drafts that satisfy the most recent piece of feedback but fail a requirement that was satisfied
two rounds earlier. Based on this lesson, what is the likely cause, and what would you check?

---

## 12. Revision notes

- **Orchestrator-worker's decomposition genuinely varies with the request** — measured directly: two
  different requests produced 2 and 3 subtasks respectively, distinguishing this pattern from M8-L07's
  fixed-shape parallel execution.
- **An evaluator's specific, named feedback is what makes a generator's revision meaningfully different**,
  not a generic pass/fail signal — measured directly in Case A's genuinely improved second draft.
- **A revision loop must accumulate feedback across all rounds, not just the most recent one** — this
  lesson's own lab needed exactly this fix after discovering a real regression, mirrored directly in §6's
  worked example.
- **An evaluator-optimizer loop needs an honest, bounded give-up for genuinely unsatisfiable requirements**
  — measured directly: Case B correctly retained its fixed requirement while honestly reporting failure on
  the one requirement it could never satisfy.
- **A two-question framework (does decomposition vary? does output need checking against criteria?)
  recommends the correct pattern**, matching exactly what each section's own measurement already showed.

---

## 13. Completion checklist

- [ ] I can distinguish orchestrator-worker from M8-L07's fixed-shape parallel execution.
- [ ] I can explain why an evaluator's specific feedback matters more than a plain pass/fail signal.
- [ ] I can explain why a revision loop must accumulate feedback across all rounds, not just the most
      recent one.
- [ ] I can design an evaluator-optimizer loop that gives up honestly when a requirement cannot be met.
- [ ] I can apply the two-question framework to classify a new task as orchestrator-worker,
      evaluator-optimizer, or a fixed shape.
- [ ] I check that a "multi-worker" system's decomposition genuinely varies with the request before calling
      it orchestrator-worker.
- [ ] I scored 10/13 on the quiz.

---

## 14. References

- Anthropic, *Building Effective Agents*, on orchestrator-worker and evaluator-optimizer workflow patterns,
  where available. `[UNVERIFIED]`
- Python standard library, `concurrent.futures` documentation, reused from M8-L07 for worker dispatch.
  `[STABLE]`

---

## 15. Next lesson

→ M8-L09 — Single-Agent vs Multi-Agent Designs

This lesson arranged workers and revision loops around a single point of control. Next: when splitting
work across genuinely separate agents is worth its added coordination cost, and when it isn't.
