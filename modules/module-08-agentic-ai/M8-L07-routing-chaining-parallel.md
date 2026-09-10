# M8-L07 — Routing, Chaining and Parallel Execution

| | |
|---|---|
| **Lesson ID** | M8-L07 |
| **Difficulty** | 2 (Intermediate) |
| **Estimated study time** | 2.0 hours |
| **Prerequisites** | [M8-L04](M8-L04-plan-act-observe-stop.md) |

---

## 1. Learning objectives

1. **Distinguish** routing, chaining, and parallel execution by the relationship between the steps
   involved, not by surface similarity.
2. **Demonstrate** the real cost of skipping routing — either quality loss (always using one generic path)
   or wasted calls (running every path regardless).
3. **Demonstrate** that a chain's step order is a genuine data dependency, not a stylistic choice, by
   breaking it.
4. **Measure** a real wall-clock speedup from running independent steps in parallel rather than in
   sequence.
5. **Apply** a two-question framework to decide which of the three shapes fits a given set of steps.

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **Routing** | Choosing exactly one of several mutually exclusive paths based on a classification. |
| **Chaining** | Running steps in a fixed order because each one's input is the previous one's output. |
| **Parallel execution** | Running independent steps concurrently because none needs another's result. |
| **Mutually exclusive paths** | Alternatives where only one actually applies to a given case. |
| **Data dependency** | A genuine requirement that one step's output exist before another step can run. |

---

## 3. Plain-language explanation

### 3.1 Three shapes for the same underlying question: how do multiple steps relate?

M8-L04 built a loop that took several steps toward one answer. This lesson asks a structural question about
multiple steps: are they *alternatives* (only one applies — routing), a *sequence* (each needs the last
one's result — chaining), or *independent* (none needs another's result — parallel)? Picking the wrong shape
for a given relationship has a real, measurable cost, demonstrated three different ways in §7.1–§7.3.

### 3.2 Routing is not just "answering correctly" — it's avoiding unnecessary work too

§7.1 shows the same three queries handled two wrong ways: always using one generic handler (a real quality
loss — a billing question gets an hours-of-operation answer) and always running every handler regardless of
which applies (a real 3x cost increase, computed directly from actual call counts). Routing is what avoids
both.

### 3.3 A chain's order isn't a preference — it's a requirement

§7.2 doesn't just assert that order matters; it tries running the steps in the wrong order and lets Python's
own exceptions confirm there was no valid way to do so. `check_eligibility()` needs real order data;
`issue_refund()` needs a real eligibility decision. Neither can be skipped or reordered without failing for
a concrete, mechanical reason.

### 3.4 Parallel execution is a timing claim, so it gets a timing measurement

§7.3 doesn't argue that parallel execution "should" be faster — it measures both the sequential and
parallel versions of the identical three calls on the same machine and reports the real wall-clock ratio.

---

## 4. Analogy

**A hospital triage desk, a factory assembly line, and three separate phone calls placed at once.** A triage
desk picks exactly one department for a patient — cardiology or orthopedics, never both, never neither — a
routing decision. An assembly line's stations must run in a fixed order because each one modifies what the
last one produced — welding before painting only works one way. Three separate phone calls to check
insurance, check pharmacy stock, and check appointment availability don't need each other's answers at all,
so a receptionist with three phone lines can make all three at once rather than waiting for each to finish
before starting the next.

### Where the analogy breaks

- **A triage desk's decision can be revisited if the patient's case turns out more complex.** §7.1's routing
  decision, once made, sends the query down exactly one path with no built-in reconsideration — a real
  system might need an escalation path this lesson does not cover.
- **A receptionist's three phone lines have a real, finite limit.** §7.3's `ThreadPoolExecutor` can be given
  more workers than a system can actually sustain — this lesson measures the speedup, not the ceiling on how
  much parallelism is safe or economical.

---

## 5. Detailed technical explanation

### 5.1 Routing avoided both failure modes it was tested against

`[REAL, measured]` §7.1 routed three distinct queries to three distinct handlers, using exactly one call per
query (`CALL_COUNT` confirms `{'billing': 1, 'technical': 1, 'general': 1}`). Contrasted against always using
the general handler, **the billing and technical queries received the identical, unhelpful hours-of-operation
response** — a real quality loss. Contrasted against calling every handler regardless of category, **9 calls
were made where routing needed only 3** — a real, measured 3x cost increase for identical final answers.

### 5.2 A chain's dependency is mechanical, not conventional

`[REAL, measured]` §7.2 ran `get_order()` → `check_eligibility()` → `issue_refund()` in order, then
deliberately tried two ways to break the sequence. **Calling `issue_refund()` with no real eligibility
result raised a genuine `TypeError`** (comparing `None` to a number). **Calling `check_eligibility()` before
any order was fetched raised a genuine `TypeError`** (subscripting `None`). Neither exception was staged —
each function's own logic requires a real value only the step before it can produce.

### 5.3 Parallel execution's speedup is a real, measured ratio

`[REAL, measured]` §7.3 checked stock across three independent warehouses sequentially (474ms) and then
concurrently via a `ThreadPoolExecutor` (159ms) — **a measured 3.0x speedup**, with identical results in
both cases (`{'East': 12, 'Central': 0, 'West': 7}`). The speedup is real precisely because none of the
three calls needed any other one's result — the exact opposite relationship from §7.2's chain.

### 5.4 One framework, three shapes, matching what was measured

`[REAL mechanism]` §7.4's `recommend_shape()` uses two questions — are the candidates mutually exclusive,
and does a dependency exist between them — to recommend routing, chaining, or parallel execution. Applied
to descriptions of §7.1–§7.3's own scenarios, it recommends exactly the shape each section actually used and
measured, confirming the framework isn't offered independently of the evidence — it's derived from it.

### 5.5 Assumptions and limitations

- `classify_query()` is a small, hand-coded stand-in for a real router's judgment — a real system uses an
  actual model call or a trained classifier, not a fixed keyword list.
- §7.3's `time.sleep()` calls stand in for real network requests — genuinely blocking and genuinely timed,
  but not real I/O; a real system's actual speedup depends on real network and service latencies.
- This lesson does not cover combining these three shapes within one larger system (a route that itself
  contains a parallel step), handling a failure in one of several parallel calls without losing the others'
  results (M8-L13), or orchestrating multiple agents rather than multiple steps within one (M8-L08).

---

## 6. Worked example — the assistant that ran every specialist "just to be safe"

**The system.** A customer-support assistant is redesigned to consult three specialist tools for every
incoming request — a billing checker, a technical diagnostic tool, and a general-policy lookup — combining
whichever outputs "seemed relevant," on the theory that this guarantees nothing is missed.

**The incident.** Response latency and API cost both roughly tripled after the redesign shipped, and a
review found that for the overwhelming majority of requests, two of the three specialist calls' outputs
were discarded entirely — the request only ever needed one of them, and the "combining" logic was, in
practice, just picking the one relevant result and ignoring the rest.

**Why this matches §5.1 exactly.** This is precisely §7.1's second contrast, at production scale: calling
every path "just in case" is measurably more expensive than routing to the one path that actually applies,
for **the same final answer**. The redesign didn't improve correctness — the discarded outputs were, by the
team's own account, not needed — it only added cost.

**Three defects the incident revealed:**

| # | Defect | Consequence |
|---|---|---|
| 1 | No classification step decided which specialist actually applied before calling any of them | Every request paid for three calls' worth of latency and cost regardless of which one mattered |
| 2 | "Combining outputs" in practice meant discarding two of three results | The extra calls produced no actual improvement in the final answer for the majority of requests |
| 3 | Cost and latency were not measured before and after the redesign shipped | The 3x regression was discovered only after users and finance both noticed |

### The fix

**Add a routing step that classifies the request before calling any specialist**, per §5.1 — reducing calls
per request from three to one for the common case, with no loss to the final answer, since the discarded
outputs were never used anyway.

**Reserve "call more than one path" for cases where the answer genuinely needs more than one path's
information** — a real chaining or parallel relationship, not a routing one disguised as thoroughness.

**The general rule.** **"Call everything, just to be safe" is not a stronger version of routing — it is the
specific failure mode routing exists to prevent, and its cost is directly measurable: extra calls for
outputs that, in the case that actually matters, are simply thrown away.**

---

## 7. Practical activity

**File:** [`labs/m8/l07_routing_chaining_parallel.py`](../../labs/m8/l07_routing_chaining_parallel.py)

**No API key, no network, no third-party dependencies** (uses only the standard library's
`concurrent.futures` and `time` for section 3's real, measured timing).

```bash
source .venv/bin/activate
python labs/m8/l07_routing_chaining_parallel.py
```

### 7.2 Expected output

`[EXECUTED]` — 2026-09-10, Python 3.10.11 (pure standard library).

```text
============================================================================
1. ROUTING: EXACTLY ONE OF SEVERAL MUTUALLY EXCLUSIVE PATHS
============================================================================
  Routing each query to exactly ONE specialized handler:

  Query: "What's my account balance?"
    -> routed to 'billing': Billing: your current balance is $0.00 and no charges are pending.

  Query: 'My app keeps crashing on startup'
    -> routed to 'technical': Technical: please try reinstalling the app; if it persists, share your device logs.

  Query: 'What are your support hours?'
    -> routed to 'general': General: our support hours are 9am-6pm, Monday through Friday.

  Calls made per handler: {'billing': 1, 'technical': 1, 'general': 1} -- exactly one call, one handler, per query.

  Contrast: a system with NO routing that always uses the general
  handler for every query:
    "What's my account balance?" -> General: our support hours are 9am-6pm, Monday through Friday.
    'My app keeps crashing on startup' -> General: our support hours are 9am-6pm, Monday through Friday.
    'What are your support hours?' -> General: our support hours are 9am-6pm, Monday through Friday.

  The billing and technical queries get the SAME generic response as
  the hours question -- a real quality loss, not a hypothetical one.

  Contrast: a system with NO routing that calls EVERY handler for
  every query, just in case:
    Calls made: 9 (3 queries x 3 handlers each)
    Calls routing actually needed: 3 (1 per query)
    3x more calls than routing required --
    for identical final answers, since only one handler's output is
    ever actually used per query.

============================================================================
2. CHAINING: A FIXED ORDER, BECAUSE EACH STEP NEEDS THE LAST ONE'S OUTPUT
============================================================================
  Running the chain in its required order:
    get_order('O-1001') -> {'customer': 'Dana Kim', 'amount': 40.0, 'days_since_purchase': 10}
    check_eligibility(order) -> {'eligible': True, 'max_refund': 40.0}
    issue_refund('O-1001', 40.0) -> refund of $40.00 issued for O-1001

  Attempting to skip the dependency order -- issue_refund() called
  directly, without ever running check_eligibility() first:
    issue_refund('O-1001', None) RAISED TypeError("'<=' not supported between instances of 'NoneType' and 'int'")

  Attempting to run check_eligibility() BEFORE get_order() -- there is
  no order data yet to check eligibility against:
    check_eligibility(None) RAISED TypeError("'NoneType' object is not subscriptable")

  Both failures are genuine, not staged -- each step's function
  signature requires a real value only the PREVIOUS step produces.
  Unlike routing's alternatives or section 3's independent steps, a
  chain's order is not a style choice: it is a real data dependency.

============================================================================
3. PARALLEL EXECUTION: INDEPENDENT STEPS, RUN AT THE SAME TIME
============================================================================
  Checking stock across 3 independent warehouses -- none of these
  calls needs any other one's result:

  SEQUENTIAL: {'East': 12, 'Central': 0, 'West': 7}  (474ms)
  PARALLEL:   {'East': 12, 'Central': 0, 'West': 7}  (159ms)

  Same 3 calls, same results, 3.0x faster wall-clock time --
  a REAL, measured speedup, because none of these three calls needed
  any other one's output. Chaining these same three calls (as in
  section 2) would have been WRONG here -- there is no dependency to
  respect, only unnecessary waiting.

============================================================================
4. A REUSABLE FRAMEWORK: WHICH SHAPE FITS WHICH RELATIONSHIP
============================================================================
    ROUTING (pick exactly one path)
      -- Classifying a query as billing/technical/general, then answering only that way

    CHAINING (fixed order, each step needs the last one's output)
      -- Fetching an order, then checking its eligibility, then refunding it

    PARALLEL (independent steps, all needed, order doesn't matter)
      -- Checking stock across 3 independent, unrelated warehouses

  This matches exactly what sections 1-3 measured: routing avoided
  6 unnecessary handler calls by picking one path;
  chaining's dependency was real enough to raise a genuine exception
  when broken; and parallel execution turned a real dependency-free
  wait into a measured 3.0x speedup. Using the wrong shape for a
  given relationship either wastes work (routing where you chain or
  parallelize), breaks correctness (chaining treated as parallel), or
  wastes time (parallel-eligible steps run as a chain anyway).

============================================================================
5. WHAT THIS LAB IS AND IS NOT
============================================================================
  REAL: every call count in section 1, every raised exception in
  section 2, and every measured timing in section 3 is genuinely
  produced by running the code -- the parallel speedup is real
  wall-clock time measured on this machine, not a claimed ratio.

  ILLUSTRATIVE: classify_query() is a small, hand-coded stand-in for
  a real router's judgment -- a real system uses an actual model
  call or a trained classifier, not a fixed keyword list. Section 3's
  time.sleep() calls stand in for real network requests -- genuinely
  blocking and genuinely timed, but not real I/O.

  NOT SHOWN: combining these three shapes within one larger system
  (a route that itself contains a parallel step, say); handling a
  failure in ONE of several parallel calls without losing the others'
  results (M8-L13's retry/recovery topic); and orchestrating many
  agents rather than many steps within one (M8-L08's own topic).

Done.
```

### 7.3 Reading the result

**Section 1's two contrasts are two different failure modes, not one.** Always using the general handler
is a *correctness* problem — a wrong or unhelpful answer. Always calling every handler is a *cost* problem —
correct-but-wasteful. Routing is the one shape that avoids both at once, and the lab measures both
separately rather than conflating them.

**Section 2's exceptions are the strongest evidence in this lesson.** It would be easy to assert "chains
must run in order"; catching Python's own `TypeError` twice, from two different broken orderings, shows the
dependency is enforced by the actual data flow, not by a rule this lesson imposes on top of it.

**Section 3's 3.0x is a specific number for a specific case, not a universal constant.** It reflects three
equal-length, fully independent, I/O-bound calls run with three available workers — a different mix of call
count, duration, and independence would produce a different ratio, though the same underlying mechanism.

---

## 8. Common mistakes and troubleshooting

1. **Calling every possible path "just to be safe" instead of routing.** §5.1, §6 — this is measurably more
   expensive for the same final answer whenever only one path's output is actually used.
2. **Using one generic handler for every request instead of routing to a specialized one.** §5.1 — this is
   a real quality loss, not merely a missed optimization.
3. **Assuming chain order is a stylistic preference that could be reordered for convenience.** §5.2 — a
   genuine data dependency will fail mechanically, not just underperform, when broken.
4. **Running independent steps sequentially out of habit.** §5.3 — a real, measurable wall-clock cost is
   paid for no correctness benefit when the steps don't depend on each other.
5. **Choosing a shape by how the code happens to be organized, rather than by the actual relationship
   between the steps.** §5.4 — apply the two-question framework to the relationship itself, not to whatever
   arrangement is easiest to write.

| Symptom | Likely cause | Fix |
|---|---|---|
| Latency or cost increases without a corresponding quality improvement | Every possible path is called regardless of which one actually applies | Add a routing/classification step and call only the path that applies, per §5.1 |
| Two categories of request receive the same generic response | No routing step distinguishes them; one handler serves everything | Add routing so each category reaches its own specialized handler, per §5.1 |
| A pipeline crashes or behaves unpredictably when steps are reordered or parallelized | The steps have a genuine data dependency that was not respected | Confirm the dependency and run the steps in the required order, per §5.2 |
| Several independent lookups take noticeably longer than expected | Independent, non-dependent calls are being run one after another instead of concurrently | Run them in parallel and measure the actual speedup, per §5.3 |

---

## 9. Security, privacy, reliability, cost

- **Cost.** Route to the one path that applies rather than calling every path "just in case" — §7.1's own
  measurement shows this can be a 3x difference in calls for an identical final answer.
- **Reliability.** Respect a chain's genuine data dependency — §7.2 shows breaking it produces a real,
  immediate failure, not a subtly degraded result.
- **Cost.** Run genuinely independent steps in parallel rather than in sequence — §7.3's measured 3.0x
  speedup is real wall-clock time, translating directly to latency and, often, cost.
- **Reliability.** Choose the arrangement (routing, chaining, or parallel) that matches the actual
  relationship between steps, using §5.4's two-question framework, rather than defaulting to whichever
  shape is easiest to code.

---

## 10. Exercises

### Exercise 1 — Beginner (~20 min)

1. What relationship between steps calls for routing, as opposed to chaining or parallel execution?
2. Why did calling every handler for every query cost 3x more than routing, in §7.1's own measurement?
3. Why did breaking the chain's order in §7.2 raise a genuine exception rather than just a wrong answer?
4. What made §7.3's three warehouse checks eligible for parallel execution?
5. In your own words, what are the two questions §7.4's framework uses to recommend a shape?

### Exercise 2 — Intermediate (~40 min)

1. Run the lab. Confirm §7.1's call counts, §7.2's two raised exceptions, and §7.3's measured speedup on
   your own machine.
2. Add a fourth query category and handler to §7.1, and confirm routing correctly reaches the new handler.
3. Add a fourth, independent warehouse to §7.3 and re-measure the sequential-vs-parallel speedup. Does the
   ratio change, and why or why not?
4. Modify §7.2's `check_eligibility()` to accept an order with `days_since_purchase` greater than 30, and
   confirm the chain correctly produces a `max_refund` of 0.0 rather than raising an exception.
5. Using §5.4's framework, classify three real steps from a system you're familiar with as routing,
   chaining, or parallel candidates, and justify each classification.

### Exercise 3 — Challenge (~50 min)

1. Design a scenario that combines all three shapes: a routing decision whose chosen path itself contains
   a chain, one step of which forks into parallel independent calls before continuing.
2. Using §6's worked example, propose a specific metric (cost per request, latency per request, or similar)
   a team could monitor to catch a "call everything just in case" regression before it reaches the scale
   the worked example describes.
3. Investigate (by modifying the lab) what happens to the parallel speedup in §7.3 if one of the three
   warehouse checks takes noticeably longer than the other two — does the parallel version's total time
   equal the sum, the maximum, or something else?
4. Research (conceptually) how a real agent framework represents a routing decision (e.g., as a
   classifier-selected sub-agent or tool group), and compare it to this lesson's `classify_query()`.
5. Design a test that would catch a chain being silently reordered (e.g., during a refactor) without
   raising an exception — a case where the reordered chain runs without error but produces a wrong result.

---

## 11. Quiz

*(Answers: [`answer-keys/module-08-answers.md`](../../answer-keys/module-08-answers.md#m8-l07).)*

**Q1.** Per §7.1's measured result, what relationship between the billing, technical, and general handlers
made routing the appropriate shape?

- A. The three handlers were mutually exclusive alternatives — only one applied to a given query.
- B. The three handlers needed to run in a fixed sequence, each depending on the last one's output.
- C. The three handlers had no relationship to each other at all.
- D. The three handlers needed to run concurrently to save time.

**Q2.** Per §7.1's measured result, what specifically was the cost of calling every handler for every
query instead of routing?

- A. It produced completely incorrect answers for every query.
- B. It caused the loop to exceed max_steps and fail.
- C. It required rewriting the handlers themselves.
- D. It made 9 calls where routing needed only 3, for identical final answers.

**Q3.** Per §7.2's measured result, what happened when `issue_refund()` was called without a real
eligibility result from `check_eligibility()`?

- A. It silently issued an incorrect refund amount.
- B. It genuinely raised a TypeError, because the function's own logic required comparing a real number, not None.
- C. It ran successfully with a default value.
- D. It called check_eligibility() automatically to recover.

**Q4.** Per §7.2, why couldn't `check_eligibility()` be run before `get_order()` in this chain?

- A. Because the two functions have identical signatures.
- B. Because Python enforces function call order alphabetically.
- C. Because check_eligibility() genuinely requires real order data to check against, which only get_order() produces.
- D. There was no actual reason; the order was an arbitrary stylistic choice.

**Q5.** Per §7.3's measured result, what was the measured wall-clock speedup from running the three
warehouse checks in parallel instead of sequentially?

- A. Approximately 3.0x faster.
- B. No measurable speedup occurred.
- C. The parallel version was measurably slower.
- D. Approximately 10x faster.

**Q6.** Per §7.3, what property of the three warehouse checks made them eligible for parallel execution?

- A. They were mutually exclusive alternatives.
- B. They all returned the same value.
- C. They needed to run in a specific fixed order.
- D. None of the three calls needed any other one's result.

**Q7.** Per §5.4's framework, which factor determines whether a set of candidate steps should be routed
rather than chained or parallelized?

- A. Whether the steps take a long time to execute.
- B. Whether the steps are mutually exclusive alternatives where only one applies.
- C. Whether the steps were written by the same engineer.
- D. Whether the steps use the same programming language.

**Q8.** Per §7.4, did the framework's recommendations for sections 1 through 3's own scenarios match what
those sections actually measured?

- A. No, the framework recommended a different shape than what was actually used in each section.
- B. The framework only applies to hypothetical scenarios, not the lab's own sections.
- C. Yes — applied to descriptions of sections 1-3's own scenarios, it recommended exactly the shape each section actually used and measured.
- D. The comparison is not meaningful since the framework was developed independently.

**Q9.** Per §6's worked example, what was the measured consequence of calling all three specialist tools
for every request "just to be safe"?

- A. Response latency and cost roughly tripled, while two of three specialist outputs were discarded for the majority of requests.
- B. Response quality improved significantly for every request.
- C. The system crashed and had to be rolled back immediately.
- D. No measurable change occurred in latency or cost.

**Q10.** Per §6, what is the stated general rule this incident illustrates?

- A. Calling every available path is always the safest and most correct approach regardless of cost.
- B. The incident has no general lesson beyond this one specific system.
- C. Specialist tools should never be combined under any circumstances.
- D. "Call everything, just to be safe" is not a stronger version of routing — it is the specific failure mode routing exists to prevent, with a directly measurable cost.

**Q11.** Per §7.5, what does this lesson explicitly NOT cover?

- A. The routing, chaining, and parallel execution shapes demonstrated in sections 1 through 3.
- B. Combining these three shapes within one larger system, handling a failure in one of several parallel calls, and orchestrating multiple agents — left to further combination, M8-L13, and M8-L08 respectively.
- C. The two-question framework in section 4.
- D. The measured speedup in section 3.

**Q12.** What is the general lesson this lab demonstrates about arranging multiple steps in an agent?

- A. Parallel execution should always be preferred over routing or chaining because it is fastest.
- B. Routing, chaining, and parallel execution are interchangeable and produce identical results regardless of which is chosen.
- C. The relationship between steps (mutually exclusive, dependent, or independent) determines which arrangement is correct, and using the wrong one for a given relationship has a measurable cost — wasted work, broken correctness, or wasted time.
- D. Chaining is always the safest default arrangement for any set of steps.

**Q13.** *(Written, rubric-graded.)* In under 150 words: a colleague proposes always running three
specialist tools in parallel for every request "to save time," regardless of what the request actually
asks. Based on this lesson, what would you point out, and why?

---

## 12. Revision notes

- **Routing picks exactly one of several mutually exclusive paths** — measured directly: one call per
  query, versus a 3x cost increase or a real quality loss when routing is skipped.
- **Chaining's fixed order reflects a genuine data dependency** — measured directly: breaking the order
  raised real exceptions, not just a degraded result, because each step's function genuinely requires the
  previous step's output.
- **Parallel execution is a timing claim, verified by timing it** — measured directly: a 3.0x wall-clock
  speedup for three independent, equal-length calls run concurrently instead of sequentially.
- **A two-question framework (mutually exclusive? dependent?) recommends the correct shape**, and matches
  exactly what each section's own measurement already showed was correct.
- **"Call everything, just to be safe" is the specific failure mode routing exists to prevent** — its cost
  is directly measurable, not merely a theoretical inefficiency.

---

## 13. Completion checklist

- [ ] I can distinguish routing, chaining, and parallel execution by the relationship between steps.
- [ ] I can explain the two distinct costs of skipping routing (quality loss and wasted calls).
- [ ] I can explain why a chain's order is a data dependency, not a stylistic choice.
- [ ] I can measure a real speedup from parallelizing independent steps.
- [ ] I can apply the two-question framework to classify a new set of steps.
- [ ] I choose an arrangement based on the actual relationship between steps, not by default habit.
- [ ] I scored 10/13 on the quiz.

---

## 14. References

- Anthropic, *Building Effective Agents*, on routing, prompt chaining, and parallelization workflow
  patterns, where available. `[UNVERIFIED]`
- Python standard library, `concurrent.futures` documentation, for the `ThreadPoolExecutor` mechanism used
  in §7.3. `[STABLE]`

---

## 15. Next lesson

→ M8-L08 — Orchestrator-Worker and Evaluator-Optimizer Patterns

This lesson arranged multiple steps within a single agent's turn. Next: patterns for arranging multiple
agents — one directing several others, or one agent checking and improving another's work.
