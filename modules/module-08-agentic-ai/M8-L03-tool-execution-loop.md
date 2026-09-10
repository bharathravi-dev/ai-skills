# M8-L03 — The Tool Execution Loop, Written From Scratch

| | |
|---|---|
| **Lesson ID** | M8-L03 |
| **Difficulty** | 2 (Intermediate) |
| **Estimated study time** | 2.5 hours |
| **Prerequisites** | [M8-L02](M8-L02-deterministic-vs-model-selected.md), M5-L08 |

---

## 1. Learning objectives

1. **Implement** a general-purpose tool-execution loop that works for any set of tools, not one hardcoded
   to a single scenario.
2. **Represent** a tool call using M5-L08's own vocabulary — a name plus arguments — and connect that shape
   to the loop's control flow.
3. **Handle** two categories of failure a loop must survive without crashing: an unrecognized tool name and
   a tool call that raises.
4. **Demonstrate** that a single loop implementation genuinely generalizes by running it, unmodified, across
   two unrelated domains.
5. **Enforce** a hard step-count bound as a property of the loop itself, independent of what any decision
   step returns.

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **Tool execution loop** | The code that repeatedly asks what to do next, executes it, and feeds the result back, until told to stop. |
| **Observation** | A tool's result (or its error), fed back into the next decision as new information. |
| **Decision step** | The part of the loop — model or mock — that chooses the next action from what has been observed. |
| **Unrecognized action** | A proposed tool name the loop has no matching implementation for. |
| **Step bound** | A hard limit on loop iterations, enforced regardless of the decision step's own choices (M8-L15). |

---

## 3. Plain-language explanation

### 3.1 M8-L01 and M8-L02 each built a loop; this lesson builds the loop

M8-L01's `run_agent()` and M8-L02's `gated_refund()` each worked, but each was written for one specific
scenario. This lesson extracts what was actually general about them into one reusable function and proves,
by running it against two unrelated domains unchanged, that the generalization is real.

### 3.2 A tool call is a name and some arguments — nothing more

§7.1 restates M5-L08's own definition on purpose: a tool call is a name plus arguments. §7.2–§7.4's entire
`run_tool_loop()` is built around exactly that shape — a decision step returns `(action_name, action_args)`,
and the loop's job is to turn that pair into an actual function call, an observation, or a caught error.

### 3.3 A loop that trusts its own decision step will eventually crash

§7.2 deliberately scripts two realistic mistakes — a hallucinated tool name and a call with a wrong
argument — into one scenario, and shows both handled by the *same* general error-handling code, not two
special cases bolted on for the demo. Neither mistake stops the loop; each becomes an observation the next
decision can act on.

### 3.4 Running the same function on two unrelated problems is the actual proof

§7.3 doesn't just claim `run_tool_loop()` is general — it runs it, completely unmodified, against a
trip-cost calculator that shares no code, no data, and no domain concepts with the refund scenario in §7.2.
That the identical function drives both correctly is the demonstration, not an assertion about the code's
design.

### 3.5 A loop needs a bound it enforces itself, not one it hopes for

§7.4 gives the loop a decision step that never chooses to stop, and shows the loop stopping anyway — because
`max_steps` is checked by the loop's own code, not requested politely of whatever is making the decisions.

---

## 4. Analogy

**A relay race baton, not a play script.** A play script specifies every actor's every line in advance — if
an actor forgets a line, the scene breaks, because nothing in the script's design anticipated deviation. A
relay race, by contrast, has one simple, enforced rule that doesn't care what happens in between: the baton
gets passed at each exchange zone, and if a runner trips, the baton is still there to be picked up and
passed at the next zone — the race's structure survives an individual runner's mistake. `run_tool_loop()` is
built like the relay's baton-passing rule, not like a script: it doesn't need to anticipate every specific
way a decision step might go wrong, only to guarantee that whatever happens, the next observation is handed
back cleanly and the loop keeps running (or stops on its own terms).

### Where the analogy breaks

- **A relay runner who trips loses time but the team's structure isn't otherwise threatened.** §7.2's
  errors are genuinely caught and recovered from *within the same run*, not merely survived at a cost — the
  loop's next step succeeds using the corrected information.
- **A race has a fixed, known number of exchange zones.** §7.4's `max_steps` is a safety bound for the
  *unknown* case — a decision step that never naturally reaches a stopping point at all, which a race's
  fixed structure doesn't need to guard against.

---

## 5. Detailed technical explanation

### 5.1 One general loop, defined once

`[REAL]` §7's `run_tool_loop(tools, decide_next, max_steps)` takes a list of `Tool` objects (name, function,
description — M5-L08's own fields) and a `decide_next(observed) -> (action_name, action_args)` function. It
contains no reference to refunds, trips, or any other domain — every domain-specific behavior lives entirely
in the tools and the decision function passed in, not in the loop.

### 5.2 Both real failure modes are caught by the same general code

`[REAL, measured]` §7.2 scripted a decision step that first proposes `lookup_customer_history` — a tool
that was never registered — and later proposes `get_order` with an order id that doesn't exist,
**genuinely raising a `ValueError`.** Both were caught by the loop's own generic `if action_name not in
tool_by_name` check and `try/except`, respectively — **no scenario-specific handling exists for either
case.** Both errors became entries in `observed`, and the scripted decision step's next call used the
corrected information to complete the refund successfully.

### 5.3 The same function, two unrelated domains, zero changes

`[REAL, measured]` §7.3 ran the identical `run_tool_loop()` against a trip-cost calculator (`get_distance`,
`get_fuel_price`, `compute_trip_cost`) — tools sharing no code, data, or vocabulary with §7.2's support
scenario. **It produced the correct final result (a computed trip cost of $25.31 from real distance and fuel
values) with no modification to the loop itself.** This is the actual test of "general-purpose": not that
the code looks reusable, but that it was reused, unmodified, and worked.

### 5.4 The step bound is the loop's property, not the decision step's

`[REAL, measured]` §7.4 gave the loop a decision step that always proposes another tool call, never
`"respond"`. Run with `max_steps=3`, **the loop made exactly 3 calls and then stopped itself**, printing a
clear "reached max_steps" message rather than continuing indefinitely. The bound is enforced by
`run_tool_loop()`'s own `for` loop, entirely independent of whether the decision step ever intends to stop.

### 5.5 Assumptions and limitations

- `decide_next()` in every scenario is a small, scripted stand-in for a real model's choices — a real system
  replaces this with an actual model call that reads `observed` and the available tools' descriptions
  (M8-L04 covers the plan/act/observe/stop shape of that call in more depth).
- This lesson does not validate a tool's *arguments* against a schema before calling it (M8-L05); it only
  handles an unrecognized tool *name* and an exception the tool itself raises.
- State and memory carried across separate conversations, not just within one loop's single run, is M8-L06's
  topic. Human approval gates before a high-stakes call executes are M8-L10's topic.

---

## 6. Worked example — the loop that only worked in the demo

**The system.** A team hand-writes a tool-execution loop for a single internal use case: an IT-helpdesk
assistant with three tools. It works reliably in every demo and every test the team runs before launch.

**What broke in production.** Within the first week, two things happened that never occurred in testing: the
model proposed a tool name from an *earlier version* of the tool list, one the team had since renamed — and
a tool call failed because a downstream service timed out, raising an exception the loop had never been
written to expect. **The loop crashed outright both times**, ending the conversation with an unhandled error
instead of recovering.

**Why this matches §5.2 exactly.** Both incidents are the same two failure categories §7.2 deliberately
exercised — an unrecognized action name, and a tool call that raises — except this team's loop had no
general handling for either, only success-path code. **Nothing about either failure was exotic**; a renamed
tool and a timeout are two of the most ordinary things that happen to a running system.

**Three defects the incidents revealed:**

| # | Defect | Consequence |
|---|---|---|
| 1 | No `if action_name not in tool_by_name` check existed anywhere in the loop | A single renamed or removed tool silently crashed every conversation that happened to reference the old name |
| 2 | No `try/except` wrapped the tool invocation itself | Any transient failure in any tool (a timeout, a network blip) ended the conversation instead of becoming recoverable information |
| 3 | The loop's error handling had only ever been exercised by demos that never hit either case | The gap was invisible until real, unremarkable production conditions triggered it |

### The fix

**Add the two general checks §5.2 demonstrates**, not as special cases for the specific renamed tool or the
specific timing service, but as loop-level handling that survives *any* unrecognized name or *any* raised
exception, present or future.

**Test the loop against deliberately broken inputs before launch**, per §7.2's own design — a scripted
decider that requests a nonexistent tool and a tool call engineered to fail, exactly as this lesson's lab
does, rather than only against inputs that are known to succeed.

**The general rule.** **A tool-execution loop's error handling is not a feature to add once a specific
failure is observed in production — the two failure categories (unrecognized name, raised exception) are
general and predictable in advance, and a loop that only handles the success path will eventually meet
both, on a schedule it does not control.**

---

## 7. Practical activity

**File:** [`labs/m8/l03_tool_execution_loop.py`](../../labs/m8/l03_tool_execution_loop.py)

**No API key, no network, no third-party dependencies.** Runs in well under a second.

```bash
source .venv/bin/activate
python labs/m8/l03_tool_execution_loop.py
```

### 7.2 Expected output

`[EXECUTED]` — 2026-09-10, Python 3.10.11 (pure standard library).

```text
============================================================================
1. WHAT A TOOL CALL ACTUALLY IS: A NAME PLUS ARGUMENTS
============================================================================
  M5-L08's own definition: 'Tool call: The model's request -- a tool
  name plus arguments.' That's the whole shape decide_next() must
  produce: (action_name, action_args). Everything else in this lab is
  what a loop does with that shape once it has it.

============================================================================
2. SCENARIO A: SUPPORT ASSISTANT -- BOTH ERROR PATHS, DELIBERATELY TRIGGERED
============================================================================
  Running run_tool_loop() against the support-assistant tools:

  [step 1] REQUESTED unknown tool 'lookup_customer_history' -- caught, fed back as an observation, loop continues
  [step 2] search_orders({'customer_name': 'Dana Kim'}) -> 'O-1001'
  [step 3] get_order({'order_id': 'O-9999'}) RAISED ValueError("no such order: 'O-9999'") -- caught, fed back as an observation, loop continues
  [step 4] get_order({'order_id': 'O-1001'}) -> {'item': 'Wireless Mouse', 'amount': 25.0}
  [step 5] issue_refund({'order_id': 'O-1001', 'amount': 25.0}) -> 'refund of $25.00 issued for O-1001'
  [step 6] respond -- loop stops

  Step 1's unknown tool and step 3's invalid order id both reached
  the SAME general except/unknown-name handling in run_tool_loop() --
  no scenario-specific error handling was written for either one.
  The loop recovered and completed the refund anyway, because each
  error became an observation instead of a crash.

============================================================================
3. SCENARIO B: A COMPLETELY DIFFERENT DOMAIN, THE SAME LOOP, UNCHANGED
============================================================================
  Running the IDENTICAL run_tool_loop() function against an unrelated
  trip-cost domain -- zero changes to the loop itself:

  [step 1] get_distance({'origin': 'Springfield', 'destination': 'Capital City'}) -> 187.0
  [step 2] get_fuel_price({}) -> 3.79
  [step 3] compute_trip_cost({'distance': 187.0, 'fuel_price': 3.79}) -> 25.31
  [step 4] respond -- loop stops

  Nothing about run_tool_loop() mentions orders, refunds, distances,
  or fuel -- it only knows about Tool objects and (name, args) pairs.
  That is what 'general-purpose, written from scratch' means here: the
  SAME function, unmodified, correctly drives two domains that share
  no code and no data.

============================================================================
4. THE SAFETY BOUND: A DECIDER THAT NEVER SAYS 'RESPOND'
============================================================================
  A decider that always proposes another tool call, run with a real,
  low max_steps bound:

  [step 1] get_fuel_price({}) -> 3.79
  [step 2] get_fuel_price({}) -> 3.79
  [step 3] get_fuel_price({}) -> 3.79
  [step 3] STOPPED: reached max_steps=3 without a final response

  The loop made exactly 3 calls, then stopped itself -- not because
  the decider ever chose to stop, but because max_steps is enforced by
  run_tool_loop() itself, independent of what any decision function
  returns. This is the same bound M8-L01's run_agent() applied ad hoc;
  here it is a first-class, reusable parameter of the general loop.

============================================================================
5. WHAT THIS LAB IS AND IS NOT
============================================================================
  REAL: run_tool_loop() is genuinely general-purpose -- sections 2 and
  3 run the IDENTICAL function against two unrelated tool sets with no
  changes to the loop. Both error paths in section 2 (unknown tool
  name, a tool call that raises) are genuinely caught by the loop's
  own except/lookup logic, not scripted around. Section 4's step count
  is a real, measured consequence of max_steps.

  ILLUSTRATIVE: decide_next() in every scenario is a small, scripted
  stand-in for a real model's choices -- a real system replaces this
  with an actual model call reading `observed` and the available
  tools' descriptions, then choosing what to do next (M8-L04 covers
  the plan/act/observe/stop shape of that choice in more depth).

  NOT SHOWN: validating a tool's ARGUMENTS against a schema before
  calling it (M8-L05); state and memory carried across separate
  conversations, not just within one loop's run (M8-L06); and human
  approval gates before a high-stakes tool call executes (M8-L10).

Done.
```

### 7.3 Reading the result

**Section 2's trace is the lesson's central evidence.** Two genuinely different mistakes — a name that
doesn't exist, and a call that fails — both get absorbed by the same handful of lines of general code, and
the scripted decision step recovers from both within a single run. Nothing about either error path was
written twice.

**Section 3 is a stronger claim than it looks.** It would be easy to *say* a loop is general-purpose;
running the unmodified function against a domain with no shared vocabulary at all, and getting a correct
answer, is what actually earns that description.

**Section 4's bound matters exactly because sections 2 and 3 look so well-behaved.** A loop that recovers
gracefully from errors and generalizes across domains still needs a hard stop that doesn't depend on the
decision step's cooperation — the two properties are independent, and this lesson demonstrates both rather
than assuming good error handling implies a safe bound.

---

## 8. Common mistakes and troubleshooting

1. **Writing error handling specific to one anticipated failure instead of general handling for a whole
   category.** §5.2, §6 — a renamed tool and a timeout are both instances of "unrecognized name" and "call
   that raises," not two separate problems needing two separate fixes.
2. **Testing a loop only against inputs known to succeed.** §6 — a loop's error paths need to be exercised
   deliberately, with a scripted decider that requests bad input, before trusting them in production.
3. **Assuming a loop is general-purpose because it looks decoupled, without actually running it on a second
   domain.** §5.3 — the proof is in reuse, not in code appearance.
4. **Relying on the decision step to eventually choose to stop.** §5.4 — a step bound enforced by the loop
   itself is what actually guarantees termination, independent of what any decision function returns.
5. **Letting an unhandled exception from one tool call end the entire conversation.** §5.2, §6 — a caught
   exception, fed back as an observation, preserves the chance to recover; an unhandled one does not.

| Symptom | Likely cause | Fix |
|---|---|---|
| The whole conversation ends abruptly after one tool call | An exception from that tool call was never caught by the loop | Wrap the tool invocation in try/except and feed the error back as an observation (§5.2) |
| A tool rename or removal breaks existing conversations | The loop has no check for an unrecognized action name | Add an explicit `if action_name not in tool_by_name` branch, per §5.2 |
| A "general" loop needs code changes for every new use case | Domain-specific logic leaked into the loop itself instead of staying in the tools and decision function | Refactor so the loop only handles (name, args) pairs and Tool objects, per §5.1 |
| A conversation runs far longer than expected, or never ends | No step bound is enforced by the loop itself | Add a max_steps parameter checked by the loop's own control flow, per §5.4 |

---

## 9. Security, privacy, reliability, cost

- **Reliability.** Handle both an unrecognized tool name and a raised exception generally, at the loop
  level — these are the two failure categories any tool-execution loop will eventually meet (§5.2, §6).
- **Reliability.** Enforce a step bound as a property of the loop itself, not as a courtesy the decision
  step is expected to observe (§5.4).
- **Reliability.** Test error paths deliberately, with inputs engineered to fail, before trusting a loop's
  error handling in production (§6).
- **Cost.** An unbounded loop against a decision step that never naturally stops has unbounded cost — a
  step limit caps this regardless of cause (§5.4; M8-L15 covers budget-based bounds in depth).

---

## 10. Exercises

### Exercise 1 — Beginner (~20 min)

1. What two pieces of information does a tool call consist of, per M5-L08's own definition?
2. What two categories of failure does `run_tool_loop()` handle generally, without scenario-specific code?
3. Why is running the loop against a second, unrelated domain a stronger test than reading the code?
4. What enforces `run_tool_loop()`'s step bound — the decision step, or the loop itself?
5. In your own words, what happened at step 3 of §7.2's trace, and how did the loop recover?

### Exercise 2 — Intermediate (~40 min)

1. Run the lab. Confirm §7.2's full six-step trace and §7.3's trip-cost result on your own machine.
2. Add a third, unrelated domain (your own choice of 2-3 tools) with its own scripted decider, and confirm
   `run_tool_loop()` drives it correctly with no changes to the loop itself.
3. Modify `make_support_decider()` to trigger a THIRD kind of mistake (e.g., calling `issue_refund` before
   `get_order` has ever run, so `observed["get_order"]` doesn't exist yet) and observe what actually happens
   — does the loop catch it? Why or why not?
4. Lower `max_steps` in §7.2's scenario to 4 and re-run. What happens, and does the refund still get issued?
5. Add a second tool to the trip-cost domain that deliberately raises (e.g., an unknown city pair) and
   confirm the loop handles it the same way §7.2's `get_order` failure was handled.

### Exercise 3 — Challenge (~50 min)

1. Extend `run_tool_loop()` to record how many times each specific error type (unknown tool vs. raised
   exception) occurred across a run, and print a summary at the end.
2. Design a decision function that deliberately alternates between two different unrecognized tool names
   forever, and confirm the step bound still catches it correctly.
3. Using M8-L02's framework, argue for or against adding a "maximum retries per tool" limit (distinct from
   the overall step bound) to `run_tool_loop()`, and explain what blast-radius consideration would justify
   it.
4. Research (conceptually) how a real agent framework structures its tool-call loop and error handling, and
   compare it to this lesson's `run_tool_loop()`.
5. Using §6's worked example, write a short pre-launch test checklist a team could run against any new
   tool-execution loop before shipping it, based specifically on this lesson's two failure categories.

---

## 11. Quiz

*(Answers: [`answer-keys/module-08-answers.md`](../../answer-keys/module-08-answers.md#m8-l03).)*

**Q1.** Per §7.1, what two pieces of information make up a tool call, per M5-L08's own definition?

- A. A tool name and its arguments.
- B. A conversation ID and a timestamp.
- C. A model name and a temperature setting.
- D. A user ID and a session token.

**Q2.** Per §7.2's measured result, what happened when the scripted decision step proposed
`lookup_customer_history`, a tool that was never registered?

- A. The loop crashed with an unhandled error.
- B. The loop silently ignored the request and moved to the next scripted step without recording anything.
- C. The loop retried the same unknown tool name repeatedly until max_steps was reached.
- D. The loop's general unknown-tool check caught it, recorded an error observation, and continued to the next step.

**Q3.** Per §7.2's measured result, what happened when `get_order` was called with the invalid id
`"O-9999"`?

- A. The function returned `None` silently.
- B. The function genuinely raised a ValueError, which the loop's try/except caught and recorded as an observation before continuing.
- C. The loop crashed and the run ended.
- D. The function returned the wrong order's details instead of raising.

**Q4.** Per §7.2, was separate, scenario-specific error-handling code written for the unknown-tool case and
the raised-exception case?

- A. Yes, each required its own dedicated handling function.
- B. Only the raised-exception case required dedicated handling.
- C. No — both were caught by the same general, non-scenario-specific checks in run_tool_loop().
- D. Only the unknown-tool case required dedicated handling.

**Q5.** Per §7.3's measured result, what changed in `run_tool_loop()`'s own code to make it work correctly
against the trip-cost domain?

- A. Nothing — the identical, unmodified function was run against a completely different tool set and decision function.
- B. The error-handling logic had to be duplicated for the new domain.
- C. The max_steps parameter had to be significantly increased.
- D. A new branch had to be added to recognize trip-related tool names specifically.

**Q6.** Per §7.3, what specifically demonstrates that the loop is genuinely general-purpose rather than
merely well-organized?

- A. The code's structure looks clean and readable.
- B. The tools in both domains happen to share similar names.
- C. The loop was reviewed by a second engineer.
- D. The loop was actually run, unmodified, against a second domain sharing no code, data, or vocabulary with the first, and produced a correct result.

**Q7.** Per §7.4's measured result, how many tool calls did the loop make when run with `max_steps=3`
against a decision step that never proposes "respond"?

- A. It ran indefinitely until manually stopped.
- B. It made exactly 3 calls and then stopped itself.
- C. It made 0 calls and immediately stopped.
- D. It made an unpredictable number of calls depending on system load.

**Q8.** Per §7.4, what specifically enforces the step bound in this lab's loop?

- A. The decision step voluntarily checks a counter and stops itself.
- B. An external monitoring process outside the loop terminates it.
- C. run_tool_loop()'s own control flow enforces max_steps, independent of what the decision step returns.
- D. The individual tools refuse to execute after being called too many times.

**Q9.** Per §6's worked example, what were the two real production incidents that broke the
hand-written, scenario-specific loop?

- A. A tool was renamed (an unrecognized name was proposed) and a downstream service timed out (a tool call raised an exception) — the same two categories §7.2 exercised deliberately.
- B. A user submitted an unusually long message, and the server ran out of memory.
- C. Two different users submitted conflicting requests simultaneously.
- D. The model's API key expired unexpectedly.

**Q10.** Per §6, why did the worked-example team's loop crash on both incidents instead of recovering?

- A. Their loop had general error handling, but it contained a bug.
- B. Their loop had only ever been tested against inputs engineered to fail, never against successful cases.
- C. Their tools were implemented incorrectly, unrelated to the loop's error handling.
- D. Their loop had no general handling for either failure category — only success-path code — because its testing had never exercised either case.

**Q11.** Per §7.5, what does this lesson explicitly NOT cover?

- A. The general run_tool_loop() function demonstrated in sections 2 through 4.
- B. Validating a tool's arguments against a schema, state/memory across separate conversations, and human approval gates — left to M8-L05, M8-L06, and M8-L10 respectively.
- C. The unknown-tool and raised-exception handling shown in section 2.
- D. The step-bound mechanism shown in section 4.

**Q12.** What is the general lesson this lab demonstrates about writing a tool-execution loop?

- A. Every new domain requires its own custom-written loop with domain-specific error handling.
- B. Error handling is optional as long as the demo scenario never triggers a failure.
- C. A tool-execution loop can be genuinely general-purpose when its error handling addresses failure categories (unrecognized names, raised exceptions) rather than anticipated specific cases, and this generality is proven by actually running it, unmodified, across unrelated domains.
- D. A step bound is unnecessary as long as the decision step is well-designed.

**Q13.** *(Written, rubric-graded.)* In under 150 words: your team's tool-execution loop has worked
flawlessly in every test so far. Based on this lesson, what would you specifically test before trusting it
in production, and why?

---

## 12. Revision notes

- **A tool call is a name plus arguments** — M5-L08's own definition, and the entire shape
  `run_tool_loop()`'s decision function must produce.
- **Two failure categories — an unrecognized tool name and a tool call that raises — were both caught by
  the same general code**, with no scenario-specific handling written for either.
- **The identical loop function, unmodified, correctly drove two domains sharing no code, data, or
  vocabulary** — measured directly, not merely asserted from the code's structure.
- **A step bound enforced by the loop itself, not by the decision step's cooperation, stopped a decision
  step that never naturally reaches a stopping condition** — measured directly at exactly 3 calls with
  `max_steps=3`.
- **A loop's error handling needs deliberate testing against inputs engineered to fail**, not only inputs
  known to succeed — the worked example's production incidents were both ordinary, predictable instances of
  categories this lesson's lab exercises on purpose.

---

## 13. Completion checklist

- [ ] I can state the two pieces of information that make up a tool call.
- [ ] I can name the two failure categories a general tool-execution loop must handle.
- [ ] I can explain why running a loop on a second, unrelated domain is a stronger test than code review.
- [ ] I can explain what enforces a step bound and why it must not depend on the decision step.
- [ ] I test a loop's error handling with inputs deliberately engineered to fail, not only successful ones.
- [ ] I write error handling for failure categories, not individually anticipated cases.
- [ ] I scored 10/13 on the quiz.

---

## 14. References

- M5-L08's own tool-call vocabulary ("name plus arguments"), reused directly throughout this lesson.
  `[STABLE]`
- Anthropic, agentic tool-use documentation, for how a real model call fits into this loop shape, where
  available. `[UNVERIFIED]`

---

## 15. Next lesson

→ M8-L04 — Plan, Act, Observe, Stop

This lesson built the loop's mechanics. Next: the shape of the decision itself — how a real system plans
before acting, observes what actually happened, and decides when enough is enough.
