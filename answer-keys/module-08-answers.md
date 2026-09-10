# Module 8 — Answer Key

**Do not read this before attempting the questions.** Every answer carries a reason, and for multiple
choice, a reason each distractor fails.

> Module 8 quiz options are uniform in length with a balanced answer distribution, and carry no inline
> explanation of the correct choice. All rationale lives here.

| Lesson | Jump to |
|---|---|
| M8-L01 Chatbots, Workflows and Agents: a Precise Distinction | [↓](#m8-l01) |
| M8-L02 Deterministic Execution vs Model-Selected Actions | [↓](#m8-l02) |
| M8-L03 The Tool Execution Loop, Written From Scratch | [↓](#m8-l03) |
| M8-L04 Plan, Act, Observe, Stop | [↓](#m8-l04) |
| M8-L05 Tool Schemas and Argument Validation | [↓](#m8-l05) |
| M8-L06 State and Memory in Agents | [↓](#m8-l06) |
| M8-L07 Routing, Chaining and Parallel Execution | [↓](#m8-l07) |
| M8-L08 Orchestrator-Worker and Evaluator-Optimizer Patterns | [↓](#m8-l08) |
| M8-L09 Single-Agent vs Multi-Agent Designs | [↓](#m8-l09) |
| M8-L10 Human Approval and Escalation | [↓](#m8-l10) |
| M8-L11 Read-Only vs State-Changing Actions | [↓](#m8-l11) |
| M8-L12 Idempotency and Duplicate-Action Prevention | [↓](#m8-l12) |
| M8-L13 Retries, Timeouts, Cancellation and Recovery | [↓](#m8-l13) |
| M8-L14 Checkpointing and Durable Execution | [↓](#m8-l14) |
| M8-L15 Step Limits, Cost Budgets and Runaway Prevention | [↓](#m8-l15) |
| M8-L16 Sandboxing and Least Privilege for Tools | [↓](#m8-l16) |
| M8-L17 Tracing and Task-Level Evaluation | [↓](#m8-l17) |
| M8-L18 Tool Failures, Adversarial Inputs, Framework Choice, and When Not to Use an Agent | [↓](#m8-l18) |

---

<a id="m8-l01"></a>
## M8-L01 — Chatbots, Workflows and Agents: a Precise Distinction

**Answers: B · C · A · D · B · C · A · D · B · C · A · D**

| Q | Ans | Why, and why the distractors fail |
|---|---|---|
| 1 | **B** | This is the lesson's own stated, checkable definition: whether the system takes actions at all, and if so, who chooses the next one. **A**, **C** and **D** name properties the lesson explicitly does not use for classification. |
| 2 | **C** | A chatbot has no code path that reaches a tool at all, a structural property of the shape confirmed by the lab's own printed output. **A**, **B** and **D** invent unrelated or false causes. |
| 3 | **A** | The lab's own measured result: the workflow always executes the same fixed three-call sequence regardless of the request's actual content. **B**, **C** and **D** contradict the lab's own printed trace and code. |
| 4 | **D** | The lab's own measured result: the agent's decision step chose "respond" once order details showed no refund was requested, taking a genuinely shorter path. **A**, **B** and **C** contradict the lab's own printed trace and code. |
| 5 | **B** | This is the lesson's own stated distinction: a workflow can call a model inside a step, but the next step is still fixed by code, not by that call's output. **A**, **C** and **D** misstate or invent false constraints on workflows. |
| 6 | **C** | The lab's own measured result: classify() produced the same three labels for both the described and the actually-executed systems. **A**, **B** and **D** contradict the lab's own printed output. |
| 7 | **A** | The lab's own measured result: the workflow stayed at a constant 3 steps; the agent varied between 3 and 4 depending on the scenario. **B**, **C** and **D** contradict this measured, printed result directly. |
| 8 | **D** | This is the lesson's own stated reasoning, drawn directly from section 5's measured step-count comparison. **A**, **B** and **C** contradict this stated reasoning or invent false claims about workflow cost. |
| 9 | **B** | This is the lesson's own stated reasoning: a workflow's next step was never the model's decision, so there is no such decision for injected content to hijack. **A**, **C** and **D** contradict this stated reasoning. |
| 10 | **C** | This is exactly the test the worked example describes applying, drawn directly from §5.4's two-question definition. **A**, **B** and **D** name checks the worked example does not describe as the decisive one. |
| 11 | **A** | Section 7.6 names these specifically as left to later lessons, not built here. **B**, **C** and **D** name things this lesson does build and demonstrate directly. |
| 12 | **D** | This is the lesson's own stated general conclusion, tying together every section's specific measured finding. **A**, **B** and **C** contradict this conclusion or the evidence presented throughout the lesson. |

**Q13 rubric (5 marks).** One mark each for: **asking the decisive question** — whether the choice of which
action to take next (e.g., approve, reject, escalate) is made by a model at runtime, or by fixed code
branches, per §5.4's two-question test; **asking for a concrete counter-example** — specifically, whether
the system has ever been tested on an expense report type its designer didn't anticipate, and what happened,
per §6's worked example; **explaining why this matters for reliability** — a mislabeled workflow's fixed
branches will silently fail to act (or act wrongly) on inputs outside what its branches anticipated, per §5.2
and §6; **explaining why this matters for cost/predictability** — a genuine agent's step count and cost are
data-dependent and must be measured, not assumed constant, per §5.5; and **explaining why this matters for
security** — only a genuinely model-selected next action carries the loop-hijack risk M5-L08 foreshadowed,
so mislabeling changes what security review is actually needed, per §5.5. An answer that only asks "is it
really an agent?" without proposing the specific, checkable test scores 2.

---

<a id="m8-l02"></a>
## M8-L02 — Deterministic Execution vs Model-Selected Actions

**Answers: B · C · A · D · B · C · A · D · B · C · A · D**

| Q | Ans | Why, and why the distractors fail |
|---|---|---|
| 1 | **B** | The lab's own measured result: none of "damaged," "never arrived," or "late" appeared in the novel complaint's wording, so it fell through to "unrecognized." **A**, **C** and **D** contradict the lab's own printed setup and output. |
| 2 | **C** | The lab's own measured result: the gated variant correctly resolved the same complaint to "damaged" and returned $40.00. **A**, **B** and **D** contradict the lab's own printed output. |
| 3 | **A** | This is the lesson's own stated mechanism: the gated amount is computed only from the real order_amount and capped, never from any number in the complaint text. **B**, **C** and **D** invent causes unrelated to the actual, demonstrated mechanism. |
| 4 | **D** | The lab's own measured result: the ungated path extracted the largest dollar figure in the text and paid it directly, with no check against the order amount or cap. **A**, **B** and **C** contradict the lab's own printed output. |
| 5 | **B** | The lab's own measured result: variant 2 differed from variant 1 only on the novel-phrasing case and from variant 3 only on the adversarial case. **A**, **C** and **D** contradict the lab's own printed comparison table. |
| 6 | **C** | This is the lesson's own stated interpretation, explicitly ruling out a tuning explanation. **A**, **B** and **D** contradict this stated interpretation or the lab's own printed results. |
| 7 | **A** | The lesson states this explicitly: blast radius is checked first, and a high-blast-radius decision gets a gate regardless of enumerability. **B**, **C** and **D** contradict this stated priority order. |
| 8 | **D** | This is the lesson's own stated application of the framework to its own running example. **A**, **B** and **C** contradict or invert this stated application. |
| 9 | **B** | The worked example states this directly: the category was correct; the amount field was trusted from model output with no independent check. **A**, **C** and **D** contradict the worked example's own stated facts. |
| 10 | **C** | This is the worked example's own stated general fix. **A**, **B** and **D** contradict this stated fix or propose approaches the lesson explicitly argues against. |
| 11 | **A** | Section 7.7 names these specifically as left to M8-L05 and M8-L10. **B**, **C** and **D** name things this lesson does cover directly. |
| 12 | **D** | This is the lesson's own stated general conclusion, tying together every section's specific measured finding. **A**, **B** and **C** contradict this conclusion or the evidence presented throughout the lesson. |

**Q13 rubric (5 marks).** One mark each for: **identifying the actual risk**, per §5.3 and §6 — that a
price field authored directly by the model is exactly as untrusted as a number appearing in free-form
customer text, regardless of how well the model understands the requirements; **proposing the split**, per
§5.2 — let the model classify or describe what the order requires (open-ended, low blast radius), while code
computes the final price from a fixed pricing table or formula driven by that classification; **explaining
why "it understands the requirements better" does not address the actual concern** — understanding the
requirements is a classification-quality question, not a safety question, and the two are independent per
§5.2's own finding that a correct classification and an unsafe amount can coexist; **connecting this to blast
radius**, per §5.5 — a price is exactly the kind of high-blast-radius field that needs a deterministic gate
regardless of how it was derived; and **naming the concrete risk of not doing this**, per §6 — a
custom-order request could itself be worded to influence the proposed price, the same mechanism that
produced the $5000 overpayment and the expense-approval incident. An answer that only says "that seems risky"
without proposing the specific classify/compute split scores 2.

---

<a id="m8-l03"></a>
## M8-L03 — The Tool Execution Loop, Written From Scratch

**Answers: A · D · B · C · A · D · B · C · A · D · B · C**

| Q | Ans | Why, and why the distractors fail |
|---|---|---|
| 1 | **A** | This is M5-L08's own stated definition, restated directly in §7.1. **B**, **C** and **D** name unrelated fields not part of a tool call's definition. |
| 2 | **D** | The lab's own measured result: the general unknown-tool check caught the request, recorded an error observation, and the loop continued. **A**, **B** and **C** contradict the lab's own printed trace. |
| 3 | **B** | The lab's own measured result: get_order genuinely raised a ValueError, caught by the loop's try/except and recorded before continuing. **A**, **C** and **D** contradict the lab's own printed trace. |
| 4 | **C** | The lesson states this directly: both failures were caught by the same general checks, with no scenario-specific handling for either. **A**, **B** and **D** contradict this stated design. |
| 5 | **A** | The lesson states this directly, and the lab's own trace confirms it: the identical, unmodified function ran against a completely different tool set and decider. **B**, **C** and **D** contradict this stated and measured result. |
| 6 | **D** | This is the lesson's own stated criterion for "genuinely general-purpose" — actual reuse against an unrelated domain, not code appearance. **A**, **B** and **C** name properties the lesson explicitly does not treat as sufficient evidence. |
| 7 | **B** | The lab's own measured result: exactly 3 calls, then the loop stopped itself. **A**, **C** and **D** contradict this measured, printed result. |
| 8 | **C** | The lesson states this directly: max_steps is enforced by run_tool_loop()'s own control flow, independent of the decision step. **A**, **B** and **D** contradict this stated mechanism. |
| 9 | **A** | The worked example states this directly, and ties both incidents explicitly to §7.2's two deliberately-exercised categories. **B**, **C** and **D** name incidents the worked example does not describe. |
| 10 | **D** | The worked example states this directly: only success-path code existed, because testing had never exercised either failure category. **A**, **B** and **C** contradict the worked example's own stated facts. |
| 11 | **B** | Section 7.5 names these specifically as left to M8-L05, M8-L06, and M8-L10. **A**, **C** and **D** name things this lesson does cover directly. |
| 12 | **C** | This is the lesson's own stated general conclusion, tying together every section's specific measured finding. **A**, **B** and **D** contradict this conclusion or the evidence presented throughout the lesson. |

**Q13 rubric (5 marks).** One mark each for: **proposing a test for the unrecognized-name category**, per
§5.2 — deliberately scripting a decision step that requests a tool name that doesn't exist (e.g., a renamed
or removed tool) and confirming the loop recovers rather than crashing; **proposing a test for the
raised-exception category**, per §5.2 — deliberately triggering a real exception from within a tool call
(e.g., invalid input, a simulated downstream failure) and confirming it becomes an observation, not a crash;
**proposing a test for the step bound**, per §5.4 — running a decision step that never chooses to stop and
confirming max_steps actually terminates the loop; **explaining why passing tests so far is not sufficient
evidence**, per §6 — a loop that has only been exercised by successful demo scenarios has never actually
tested its error handling, which is exactly the gap that broke the worked example's team in production; and
**connecting this to a general principle** — that a loop's error-handling code needs to be exercised by
inputs engineered to fail, not inferred to work from inputs that happen to succeed. An answer that proposes
only "more testing" without naming the specific failure categories from this lesson scores 2.

---

<a id="m8-l04"></a>
## M8-L04 — Plan, Act, Observe, Stop

**Answers: A · D · B · C · A · D · B · C · A · D · B · C**

| Q | Ans | Why, and why the distractors fail |
|---|---|---|
| 1 | **A** | The lab's own measured result: the plan contained only "Standard," so once observed to be invalid, there was no alternative for the plan to fall back on. **B**, **C** and **D** contradict the lab's own printed setup and output. |
| 2 | **D** | The lab's own measured result: the decider stopped at the first carrier satisfying the constraint, never checking Express. **A**, **B** and **C** contradict the lab's own printed setup and output. |
| 3 | **B** | The lab's own measured trace: Standard was checked, observed to be invalid, and correctly skipped — the failure was purely in the later stop decision. **A**, **C** and **D** contradict the lab's own printed trace. |
| 4 | **C** | The lesson states this directly: only the stop condition changed, from "first valid" to "check every known carrier." **A**, **B** and **D** contradict this stated and measured change. |
| 5 | **A** | The lesson states this directly, and both variants reuse the identical run_tool_loop() from M8-L03. **B**, **C** and **D** contradict this stated design. |
| 6 | **D** | Section 7.5's table names PLAN specifically for the plan-first variant. **A**, **B** and **C** name phases the table does not attribute this failure to. |
| 7 | **B** | Section 7.5's table names STOP specifically for the naive-stop variant. **A**, **C** and **D** name phases the table does not attribute this failure to. |
| 8 | **C** | The lesson states this directly: ACT and OBSERVE were identical across all three variants; only PLAN and STOP logic differed. **A**, **B** and **D** contradict this stated and measured result. |
| 9 | **A** | The worked example states this directly, tying the bot's genuine adaptation and stop-only failure to §5.2's exact pattern. **B**, **C** and **D** contradict the worked example's own stated facts. |
| 10 | **D** | The worked example states this directly: adaptive-looking behavior combined with an order-dependent bug made it invisible until a specific case surfaced it. **A**, **B** and **C** contradict the worked example's own stated facts. |
| 11 | **B** | Section 7.6 names these specifically as not covered here, deferring to M8-L05 and M8-L10 or later coverage. **A**, **C** and **D** name things this lesson does cover directly. |
| 12 | **C** | This is the lesson's own stated general conclusion, tying together every section's specific measured finding. **A**, **B** and **D** contradict this conclusion or the evidence presented throughout the lesson. |

**Q13 rubric (5 marks).** One mark each for: **naming PLAN and STOP as the first places to look**, per §5.4
— since ACT and OBSERVE being logged correctly (as stated in the premise) is exactly the pattern §7.5's
table shows is consistent with a PLAN or STOP defect, not an ACT/OBSERVE one; **proposing a check for
premature stopping specifically**, per §5.2-§5.3 — verifying whether the agent's stop condition confirms it
has checked every relevant option (for a bounded task) or only that some option satisfying a constraint was
found; **proposing a check for a rigid, unrevised plan**, per §5.1 — verifying whether the agent's decision
logic can actually act differently based on what it observes, or whether it follows a fixed sequence
regardless of results; **connecting this to a concrete diagnostic step**, per §6 — comparing the agent's
logged tool calls against the full set of options that existed for a specific suboptimal-answer case, to see
whether a better option was ever queried at all; and **explaining why "tools and results look correct in
logs" does not rule this out**, per §5.4 — because both known failure modes (rigid plan, premature stop) are
fully compatible with every individual tool call and observation being entirely correct. An answer that
proposes only "add more logging" without naming PLAN/STOP as the specific suspect scores 2.

---

<a id="m8-l05"></a>
## M8-L05 — Tool Schemas and Argument Validation

**Answers: A · D · B · C · A · D · B · C · A · D · B · C**

| Q | Ans | Why, and why the distractors fail |
|---|---|---|
| 1 | **A** | The lab's own measured result: the schema requires `amount` to be a float, and the proposal supplied a string. **B**, **C** and **D** contradict the lab's own printed setup and error message. |
| 2 | **D** | The lab's own measured result: 50000.0 is a valid float but exceeds the schema's `le=500.0` bound. **A**, **B** and **C** contradict the lab's own printed error message. |
| 3 | **B** | This is the lesson's own stated mechanism, and the lab's own printed error message: the field was never declared, independent of its value. **A**, **C** and **D** contradict this stated mechanism and the lab's own output. |
| 4 | **C** | The lesson states this directly, and the lab's trace confirms it: one shared [VALIDATE] branch handled all three rejection types. **A**, **B** and **D** contradict this stated design and the lab's own printed trace. |
| 5 | **A** | The lab's own measured trace: a fourth, valid proposal was accepted and issue_refund() genuinely executed. **B**, **C** and **D** contradict the lab's own printed trace. |
| 6 | **D** | This is the lesson's own stated contrast, tying directly to M8-L02's own gating mechanism. **A**, **B** and **C** contradict or invert this stated contrast. |
| 7 | **B** | The lesson states this directly as the consequence of an earlier gate. **A**, **C** and **D** contradict this stated consequence. |
| 8 | **C** | The worked example states this directly: no schema existed, and the tool's own code assumed well-formed input. **A**, **B** and **D** contradict the worked example's own stated facts. |
| 9 | **A** | The worked example states this directly as its own stated fix. **B**, **C** and **D** propose approaches the worked example does not recommend or explicitly argues against. |
| 10 | **D** | Section 7.5 states this directly: a real system should prefer a maintained schema library over this lesson's dependency-free reimplementation. **A**, **B** and **C** contradict this stated reasoning or the lab's own demonstrated, working catches. |
| 11 | **B** | Section 7.5 names these specifically as not covered, deferring to a later exercise or to M8-L13. **A**, **C** and **D** name things this lesson does cover directly. |
| 12 | **C** | This is the lesson's own stated general conclusion, tying together every section's specific measured finding. **A**, **B** and **D** contradict this conclusion or the evidence presented throughout the lesson. |

**Q13 rubric (5 marks).** One mark each for: **checking the path itself, not just its type**, per §5.1 and
§7.2 — a string type check alone does not prevent a path like `"../../etc/passwd"` or an absolute path
outside an intended directory, the same class of gap a bounds check closes for a numeric argument;
**considering an allow-list or absent-parameter approach**, per §5.3 — if the tool only ever needs to
operate within a specific known directory, a schema that accepts a filename within that directory (not a
full arbitrary path) removes the dangerous case entirely rather than trying to validate it away;
**connecting this to blast radius**, per M8-L02 — a delete action is irreversible, making this exactly the
kind of high-stakes argument that needs a gate regardless of how the value was derived; **proposing the gate
be checked before the tool function runs**, per §5.4 — so the delete logic itself never has to defend
against a malformed or dangerous path reaching it; and **naming the general principle**, per §6 — a tool
that trusts its arguments to already be safe is only as safe as every path that could produce them. An
answer that proposes only "validate the file path" without naming a specific technique (path containment,
allow-list, or similar) scores 2.

---

<a id="m8-l06"></a>
## M8-L06 — State and Memory in Agents

**Answers: A · D · B · C · A · D · B · C · A · D · B · C**

| Q | Ans | Why, and why the distractors fail |
|---|---|---|
| 1 | **A** | The lab's own measured result: no persistent record existed, and each conversation's working memory started fresh, per M8-L03's own design. **B**, **C** and **D** contradict the lab's own printed setup and output. |
| 2 | **D** | The lab's own measured result: a persistent, correctly-scoped check was added and consulted, with run_tool_loop() itself unmodified. **A**, **B** and **C** contradict this stated and measured change. |
| 3 | **B** | The lab's own measured result: the check's key (order_id alone) could not distinguish Priya's order from Dana's unrelated one sharing the id string. **A**, **C** and **D** contradict the lab's own printed setup and output. |
| 4 | **C** | The lesson states this directly: the identical root cause as M5-L10's own example, producing the opposite visible symptom. **A**, **B** and **D** contradict this stated relationship. |
| 5 | **A** | The lesson states this directly: wrongly-scoped memory can actively cause a wrong outcome no memory at all would not have caused. **B**, **C** and **D** contradict this stated framing. |
| 6 | **D** | This is the lesson's own stated definition of the two kinds of memory. **A**, **B** and **C** contradict this stated definition. |
| 7 | **B** | The worked example states this directly, drawing the parallel to section 3's exact mechanism. **A**, **C** and **D** contradict the worked example's own stated facts. |
| 8 | **C** | The worked example states this directly as its proposed testing technique. **A**, **B** and **D** contradict or propose approaches the worked example does not recommend. |
| 9 | **A** | The lesson states this directly as left to M8-L12, distinct from this lesson's own scoping-and-location focus. **B**, **C** and **D** contradict this stated scope or misstate what this lesson does cover. |
| 10 | **D** | Section 7.5 states this directly: the collision is a constructed illustration, not a frequency claim. **A**, **B** and **C** contradict this stated framing. |
| 11 | **B** | Section 7.5 names these specifically as not covered, deferring to M8-L12 or treating them as illustration-only. **A**, **C** and **D** name things this lesson does cover directly. |
| 12 | **C** | This is the lesson's own stated general conclusion, tying together every section's specific measured finding. **A**, **B** and **D** contradict this conclusion or the evidence presented throughout the lesson. |

**Q13 rubric (5 marks).** One mark each for: **naming the exact identities the key must include**, per
§5.2-§5.3 — the ticket's own unique identifier together with whatever distinguishes it from a different
ticket that might coincidentally share a field (e.g., a ticket number reused across different support queues
or systems); **proposing a deliberate collision test**, per §6 and §7.3 — checking whether two different,
unrelated tickets that happen to share one field value (a ticket number, a subject line) are wrongly treated
as the same record; **explaining why this matters even though the check "already works" in normal testing**,
per §5.3 — a scoping gap is invisible until two real records actually collide, exactly as it was in this
lesson's own example; **distinguishing this from a race-condition concern**, per §5.5 — correct scoping is
about which key a fact is stored under, a different question from whether two simultaneous checks could
still both slip through (M8-L12); and **connecting this to the two possible failure directions**, per §5.3
— a scoping gap here could either cause a ticket to be escalated twice (if under-scoped in one direction) or
wrongly prevent a legitimate second escalation of an unrelated ticket (if under-scoped in the collision
direction), so both symptoms are worth checking for. An answer that only says "make sure the key is unique"
without naming a specific identity or a collision test scores 2.

---

<a id="m8-l07"></a>
## M8-L07 — Routing, Chaining and Parallel Execution

**Answers: A · D · B · C · A · D · B · C · A · D · B · C**

| Q | Ans | Why, and why the distractors fail |
|---|---|---|
| 1 | **A** | The lab's own measured result: exactly one handler applied per query, confirmed by the 1-call-per-handler count. **B**, **C** and **D** contradict the lab's own printed setup and output. |
| 2 | **D** | The lab's own measured result: 9 calls were made where routing needed only 3, for identical final answers. **A**, **B** and **C** contradict the lab's own printed setup and output. |
| 3 | **B** | The lab's own measured result: a genuine TypeError was raised comparing None to a number. **A**, **C** and **D** contradict the lab's own printed output. |
| 4 | **C** | The lesson states this directly: check_eligibility() genuinely requires real order data only get_order() produces. **A**, **B** and **D** contradict this stated and measured dependency. |
| 5 | **A** | The lab's own measured result: 474ms sequential versus 159ms parallel, a 3.0x speedup. **B**, **C** and **D** contradict this measured, printed result. |
| 6 | **D** | The lesson states this directly as the property that made parallel execution valid and correct here. **A**, **B** and **C** contradict this stated property. |
| 7 | **B** | This is the lesson's own stated first question in the framework. **A**, **C** and **D** name factors the framework does not use. |
| 8 | **C** | The lesson states this directly: the framework's recommendations matched exactly what each section measured. **A**, **B** and **D** contradict this stated result. |
| 9 | **A** | The worked example states this directly: latency and cost roughly tripled while most outputs were discarded. **B**, **C** and **D** contradict the worked example's own stated facts. |
| 10 | **D** | This is the worked example's own stated general rule. **A**, **B** and **C** contradict this stated rule or the evidence the worked example presents. |
| 11 | **B** | Section 7.5 names these specifically as not covered, deferring to further combination, M8-L13, and M8-L08. **A**, **C** and **D** name things this lesson does cover directly. |
| 12 | **C** | This is the lesson's own stated general conclusion, tying together every section's specific measured finding. **A**, **B** and **D** contradict this conclusion or the evidence presented throughout the lesson. |

**Q13 rubric (5 marks).** One mark each for: **naming the actual question to ask first**, per §5.4 — whether
each request's three specialist calls are genuinely independent (parallel-eligible) or whether, in practice,
only one specialist's output is ever used per request (a routing relationship, not a parallel one);
**explaining why "parallel" doesn't fix a routing problem**, per §5.1 and §6 — running three calls
concurrently instead of sequentially still pays for three calls' worth of cost when only one was ever needed,
saving latency but not the underlying wasted work; **citing the measured precedent**, per §6 — the worked
example's own incident, where "call everything" (there, sequentially; the same point applies if made
parallel) tripled cost while discarding most outputs, unchanged; **proposing the actual fix**, per §5.1 — a
routing step that classifies the request and calls only the one specialist that applies; and **conceding
where parallel genuinely would help**, per §5.3 — if the request truly needs all three specialists'
information together, running them concurrently is the right optimization, just not a substitute for
figuring out whether that's actually the case. An answer that only says "parallel isn't always faster"
without identifying the routing-vs-parallel distinction scores 2.

---

<a id="m8-l08"></a>
## M8-L08 — Orchestrator-Worker and Evaluator-Optimizer Patterns

**Answers: A · D · B · C · A · D · B · C · A · D · B · C**

| Q | Ans | Why, and why the distractors fail |
|---|---|---|
| 1 | **A** | The lab's own measured result: the second request mentioned returns, an additional topic, and decomposed into one more subtask. **B**, **C** and **D** contradict the lab's own printed output. |
| 2 | **D** | This is the lesson's own stated distinction, directly contrasting dynamic decomposition with M8-L07's fixed set of calls. **A**, **B** and **C** contradict or deny this stated distinction. |
| 3 | **B** | The lab's own measured result: the evaluator named "returns" as missing, and the second draft genuinely included it. **A**, **C** and **D** contradict the lab's own printed trace. |
| 4 | **C** | The lesson states this directly as the bug its own first implementation had, fixed via cumulative feedback tracking. **A**, **B** and **D** contradict this stated bug and fix. |
| 5 | **A** | The lab's own measured result, after the fix: returns stayed satisfied, warranty remained missing through all 3 attempts, and the loop gave up honestly. **B**, **C** and **D** contradict this measured, printed result. |
| 6 | **D** | The lesson states this directly as the reasoning for why giving up was the correct outcome here. **A**, **B** and **C** contradict this stated reasoning. |
| 7 | **B** | The worked example states this directly, tying it explicitly to the lab's own bug in §5.3. **A**, **C** and **D** contradict the worked example's own stated facts. |
| 8 | **C** | This is the worked example's own stated general fix. **A**, **B** and **D** propose approaches the worked example does not recommend or explicitly argues against. |
| 9 | **A** | This is the lesson's own stated first question in the framework, distinguishing orchestrator-worker specifically. **B**, **C** and **D** name unrelated or evaluator-optimizer-specific factors. |
| 10 | **D** | The lesson states this directly: the framework's recommendations matched exactly what each section measured. **A**, **B** and **C** contradict this stated result. |
| 11 | **B** | Section 7.4 names these specifically as left to natural extensions, not covered here. **A**, **C** and **D** name things this lesson does cover directly. |
| 12 | **C** | This is the lesson's own stated general conclusion, tying together every section's specific measured finding. **A**, **B** and **D** contradict this conclusion or the evidence presented throughout the lesson. |

**Q13 rubric (5 marks).** One mark each for: **naming the likely cause directly**, per §5.3 — the generator
most likely tracks only the most recent round's feedback rather than accumulating every requirement ever
flagged as missing across all rounds; **connecting this to the lesson's own documented bug**, per §5.3 and
§6 — this is the identical failure this lesson's own lab implementation had, and the identical failure §6's
worked example describes at production scale; **proposing the specific check**, per §5.3 — inspecting
whether the generator's revision state is built from cumulative feedback (a set or list that only grows) or
from only the latest evaluation's result (which can lose information between rounds); **proposing the
fix**, per §6 — treating every previously-satisfied requirement as a standing constraint the generator must
continue to honor, not something to be re-derived from the current round's note alone; and **noting that
individually correct fixes can still fail to converge as a system**, per §6 — each round's fix can be a
locally correct response to that round's feedback while the loop as a whole never converges, which is
exactly why this class of bug is easy to miss in isolated testing. An answer that only says "the generator
has a bug" without naming the cumulative-feedback mechanism specifically scores 2.

---

<a id="m8-l09"></a>
## M8-L09 — Single-Agent vs Multi-Agent Designs

**Answers: A · D · B · C · A · D · B · C · A · D · B · C**

| Q | Ans | Why, and why the distractors fail |
|---|---|---|
| 1 | **A** | The lab's own measured result: the full context still contained the error code, so the drafting step found and included it. **B**, **C** and **D** contradict the lab's own printed code and output. |
| 2 | **D** | The lab's own measured result: the summary text never contained the error code at all, so there was nothing to find. **A**, **B** and **C** contradict the lab's own printed setup and output. |
| 3 | **B** | The lab's own measured result: 290 characters to 72 characters, a 75% reduction. **A**, **C** and **D** contradict this measured, printed result. |
| 4 | **C** | The lab's own measured result: 188 characters summed versus 173 for one shared context, a near match. **A**, **B** and **D** contradict this measured, printed result. |
| 5 | **A** | This is the lesson's own stated third framework outcome. **B**, **C** and **D** misstate or invert this stated outcome. |
| 6 | **D** | The lesson states this directly as the framework's recommendation for exactly this case. **A**, **B** and **C** contradict this stated recommendation. |
| 7 | **B** | The worked example states this directly: the split was useful; the defect was the unstructured hand-off specifically. **A**, **C** and **D** contradict the worked example's own stated facts. |
| 8 | **C** | This is the worked example's own stated general rule. **A**, **B** and **D** contradict this stated rule or overstate an absolute the lesson does not support. |
| 9 | **A** | Section 7.5 names these specifically as left to natural extensions. **B**, **C** and **D** name things this lesson does cover directly. |
| 10 | **D** | Section 7.5 states this directly: a hand-written stand-in, not a general claim about all summarization systems. **A**, **B** and **C** contradict this stated framing. |
| 11 | **B** | Section 7.5 states this directly: a specific, measured comparison, not a universal zero-cost guarantee. **A**, **C** and **D** contradict this stated framing. |
| 12 | **C** | This is the lesson's own stated general conclusion, tying together every section's specific measured finding. **A**, **B** and **D** contradict this conclusion or the evidence presented throughout the lesson. |

**Q13 rubric (5 marks).** One mark each for: **naming the actual question to ask first**, per §5.4 — whether
the report-writing agent will need any specific, granular detail from the data-analysis phase that a
free-text summary might not reliably carry; **proposing a concrete test**, per §5.2 and §6 — identifying a
specific data point (a number, a named finding, a data source) the report must cite, and checking whether a
hand-off built the same way as §7.2's summary would actually preserve it; **distinguishing this from
whether to split at all**, per §5.4 and §6 — the two agents may genuinely do different jobs well suited to
separation, so the check is about hand-off DESIGN, not about reversing the decision to split; **proposing
the concrete fix if needed**, per §5.4 and §6 — passing specific, named fields (key figures, data source
citations) explicitly, rather than relying on a prose summary to happen to include them; and **connecting
this to cost**, per §5.2-§5.3 — noting that if the two phases turn out to need almost everything shared
between them, the case for splitting weakens, while if they're more independent than assumed, isolation may
come at little or no cost. An answer that only asks "will information be lost?" without proposing a
concrete way to check scores 2.

---

<a id="m8-l10"></a>
## M8-L10 — Human Approval and Escalation

**Answers: A · D · B · C · A · D · B · C · A · D · B · C**

| Q | Ans | Why, and why the distractors fail |
|---|---|---|
| 1 | **A** | The lab's own measured result: 14 auto-approved, 1 needed approval, 5 escalated — 6 of 20 needed a human. **B**, **C** and **D** contradict the lab's own printed counts. |
| 2 | **D** | The lab's own measured result: a WAITING state was returned and the request recorded pending, with no refund issued. **A**, **B** and **C** contradict the lab's own printed output. |
| 3 | **B** | The lesson states this directly, and the lab's own output labels the ungated call's immediate success as wrong behavior. **A**, **C** and **D** contradict this stated and measured contrast. |
| 4 | **C** | The lab's own measured result: both escalated because the classifier had no confident tier for either, unrelated to amount. **A**, **B** and **D** contradict the lab's own printed output. |
| 5 | **A** | The lesson states this directly as the specific risk a silent default introduces. **B**, **C** and **D** contradict this stated reasoning. |
| 6 | **D** | The lab's own measured result: 20 approvals under the blanket policy versus 6 under the tiered one, a 70% reduction. **A**, **B** and **C** contradict this measured, printed result. |
| 7 | **B** | This is the lesson's own stated consequence, distinguishing dilution from added safety. **A**, **C** and **D** contradict this stated consequence. |
| 8 | **C** | The worked example states this directly as what actually happened after the blanket policy shipped. **A**, **B** and **D** contradict the worked example's own stated facts. |
| 9 | **A** | This is the worked example's own stated general rule. **B**, **C** and **D** contradict this stated rule or the evidence the worked example presents. |
| 10 | **D** | The worked example states this directly as what the team should have analyzed first. **A**, **B** and **C** name factors the worked example does not identify as the key analysis. |
| 11 | **B** | Section 7.5 names these specifically as not covered, left to a natural extension or bordering on M8-L13. **A**, **C** and **D** name things this lesson does cover directly. |
| 12 | **C** | This is the lesson's own stated general conclusion, tying together every section's specific measured finding. **A**, **B** and **D** contradict this conclusion or the evidence presented throughout the lesson. |

**Q13 rubric (5 marks).** One mark each for: **naming the actual fix**, per §5.1 and §5.4 — introducing a
tiered policy that reserves human approval for genuinely high-blast-radius or uncertain actions, rather than
requiring it for every action; **connecting this to a measured consequence, not just an assertion**, per
§7.4 — a properly-tiered policy can reduce required approvals substantially (this lesson's own example
measured a 70% reduction) without reducing scrutiny on the cases that actually matter; **explaining why the
blanket policy is actively counterproductive, not just inefficient**, per §5.4 and §6 — routing everything
through the same queue dilutes reviewer attention, risking exactly the kind of unexamined batch-approval §6's
worked example describes; **proposing how to set the tier thresholds**, per §5.1 — based on the actual blast
radius of each action type, not an arbitrary cutoff; and **addressing what NOT to do**, per §6 — avoiding an
overcorrection that swings back to requiring no approval at all, since some genuinely high-stakes or
uncertain actions still need a human. An answer that only says "add tiers" without connecting it to the
measured scrutiny-dilution problem scores 2.

---

<a id="m8-l11"></a>
## M8-L11 — Read-Only vs State-Changing Actions

**Answers: A · D · B · C · A · D · B · C · A · D · B · C**

| Q | Ans | Why, and why the distractors fail |
|---|---|---|
| 1 | **A** | The lab's own measured result: neither tool's call changed ORDERS or REFUND_LOG at all. **B**, **C** and **D** contradict the lab's own printed output. |
| 2 | **D** | The lesson states this directly: a shallow copy shared the inner dict by reference, hiding a real mutation from the comparison. **A**, **B** and **C** contradict this stated cause. |
| 3 | **B** | The lesson states this directly as the actual fix applied. **A**, **C** and **D** propose changes the lesson does not describe as the fix. |
| 4 | **C** | The lab's own measured result: three refund entries, $75.00 total for one intended $25.00 refund. **A**, **B** and **D** contradict this measured, printed result. |
| 5 | **A** | This is the lesson's own stated reasoning, directly tied to the read-only definition. **B**, **C** and **D** state false or unrelated claims about read-only actions. |
| 6 | **D** | The lab's own measured result: the second, identical call left the world looking unchanged despite the action being genuinely state-changing. **A**, **B** and **C** contradict this measured, printed result. |
| 7 | **B** | The lesson states this directly, contrasting APPEND-style accumulation with SET-style overwriting. **A**, **C** and **D** contradict this stated and measured distinction. |
| 8 | **C** | The worked example states this directly as the root cause. **A**, **B** and **D** contradict the worked example's own stated facts. |
| 9 | **A** | This is the worked example's own stated general rule. **B**, **C** and **D** contradict this stated rule or overstate an absolute the lesson does not support. |
| 10 | **D** | This is the worked example's own stated proposed fix. **A**, **B** and **C** propose overcorrections the lesson does not recommend. |
| 11 | **B** | Section 7.4 names these specifically as left to M8-L12 or as natural extensions. **A**, **C** and **D** name things this lesson does cover directly. |
| 12 | **C** | This is the lesson's own stated general conclusion, tying together every section's specific measured finding. **A**, **B** and **D** contradict this conclusion or the evidence presented throughout the lesson. |

**Q13 rubric (5 marks).** One mark each for: **naming the actual check**, per §5.1 — classifying every tool
the retry policy could apply to as read-only or state-changing before deciding how retries should behave for
it; **explaining why a uniform policy is risky**, per §5.3 and §6 — a retry that costs nothing for a
read-only lookup repeats a real, possibly-already-successful effect for a state-changing action, exactly the
mechanism behind §6's duplicated notification; **proposing the specific fix for state-changing tools**, per
§5.4 and §6 — pairing any retryable state-changing action with an idempotency safeguard (M8-L12) rather than
relying on the retry policy alone; **noting that not all state-changing actions carry equal risk**, per
§5.4 — a SET-style action may happen to tolerate a blind retry better than an APPEND-style one, but this
should be verified per action, not assumed; and **connecting this to verification, not just labeling**, per
§5.1-§5.2 — confirming each tool's actual behavior empirically, since this lesson's own classification
needed two real bug fixes before its own verification was trustworthy. An answer that proposes only "add
retries carefully" without naming the read-only/state-changing check specifically scores 2.

---

<a id="m8-l12"></a>
## M8-L12 — Idempotency and Duplicate-Action Prevention

**Answers: A · D · B · C · A · D · B · C · A · D · B · C**

| Q | Ans | Why, and why the distractors fail |
|---|---|---|
| 1 | **A** | The lab's own measured result: exactly one real refund, with the second and third calls returning a cached result. **B**, **C** and **D** contradict the lab's own printed output. |
| 2 | **D** | The lab's own measured result: the new request executed normally, adding a genuine second entry to REFUND_LOG. **A**, **B** and **C** contradict the lab's own printed output. |
| 3 | **B** | The lab's own measured result: three separate refunds, reproducing M8-L11's own unprotected-retry finding exactly. **A**, **C** and **D** contradict this measured, printed result. |
| 4 | **C** | The lesson states this directly: the store worked correctly; it simply never received a repeated key. **A**, **B** and **D** contradict this stated and measured cause. |
| 5 | **A** | This is the lesson's own stated distinction between the two mechanisms' scopes. **B**, **C** and **D** name unrelated concerns not addressed by either mechanism this lesson discusses. |
| 6 | **D** | The lesson states this directly: a real system typically needs both mechanisms. **A**, **B** and **C** contradict this stated recommendation. |
| 7 | **B** | The worked example states this directly as the root cause. **A**, **C** and **D** contradict the worked example's own stated facts. |
| 8 | **C** | The worked example states this directly as the reason the mistake was easy to miss. **A**, **B** and **D** contradict the worked example's own stated facts. |
| 9 | **A** | This is the worked example's own stated general rule. **B**, **C** and **D** contradict this stated rule or overstate an absolute the lesson does not support. |
| 10 | **D** | Section 7.5 states this directly: a persistent, durable store is needed for the guarantee to hold, unlike this lab's in-memory dict. **A**, **B** and **C** contradict this stated limitation. |
| 11 | **B** | Section 7.5 names these specifically as left to natural extensions or to M8-L13. **A**, **C** and **D** name things this lesson does cover directly. |
| 12 | **C** | This is the lesson's own stated general conclusion, tying together every section's specific measured finding. **A**, **B** and **D** contradict this conclusion or the evidence presented throughout the lesson. |

**Q13 rubric (5 marks).** One mark each for: **naming the first, most likely cause to check**, per §5.3 and
§6 — whether the idempotency key is actually being generated ONCE per logical attempt and reused across
retries, or regenerated fresh on every attempt, since the latter is indistinguishable from having no
protection at all; **proposing a concrete way to verify this**, per §6 — inspecting where in the retry logic
the key is generated (outside the retry loop versus inside it) and logging the actual key value used across
a sequence of retries for the same logical request; **naming a second possible cause**, per §5.5 — the
idempotency store itself failing to persist across a crash or restart between retries, if the first cause is
ruled out; **naming a third possible cause**, per §5.4 — a business-level duplicate (a genuinely new request,
correctly using a new key, asking for something that already happened), which an idempotency key alone
cannot catch; and **connecting this to the general principle**, per §5.3 — that a key merely being present
in the code does not guarantee it is being reused correctly, which is exactly why this specific check should
come first. An answer that jumps straight to "the store must be broken" without first checking key reuse
scores 2.

---

<a id="m8-l13"></a>
## M8-L13 — Retries, Timeouts, Cancellation and Recovery

**Answers: A · D · B · C · A · D · B · C · A · D · B · C**

| Q | Ans | Why, and why the distractors fail |
|---|---|---|
| 1 | **A** | The lesson states this directly as the actual, diagnosed cause of the first implementation's bug. **B**, **C** and **D** contradict this stated cause. |
| 2 | **D** | The lab's own measured result: roughly 200ms, matching the requested bound, after the fix. **A**, **B** and **C** contradict this measured, printed result. |
| 3 | **B** | The lab's own measured result: exactly one entry in REFUND_LOG, from the successful third attempt. **A**, **C** and **D** contradict the lab's own printed output. |
| 4 | **C** | The lesson states this directly: the two mechanisms address different questions and neither needed awareness of the other. **A**, **B** and **D** contradict this stated independence. |
| 5 | **A** | The lab's own measured result: cancellable_bulk_check() stopped early with real partial progress; issue_refund() has no such checkpoint. **B**, **C** and **D** contradict the lab's own printed setup and output. |
| 6 | **D** | The lab's own measured result: no entry existed despite the message's success-shaped text. **A**, **B** and **C** contradict this measured, printed result. |
| 7 | **B** | This is the lesson's own stated reasoning for why the two results are indistinguishable from their text alone. **A**, **C** and **D** contradict this stated reasoning. |
| 8 | **C** | The worked example states this directly as the incident's actual outcome. **A**, **B** and **D** contradict the worked example's own stated facts. |
| 9 | **A** | The worked example states this directly as how the incident was found. **B**, **C** and **D** contradict the worked example's own stated facts. |
| 10 | **D** | This is the worked example's own stated general rule. **A**, **B** and **C** contradict this stated rule or overstate an absolute the lesson does not support. |
| 11 | **B** | Section 7.5 names these specifically as left to M2-L14's own coverage or to M8-L14. **A**, **C** and **D** name things this lesson does cover directly. |
| 12 | **C** | This is the lesson's own stated general conclusion, tying together every section's specific measured finding. **A**, **B** and **D** contradict this conclusion or the evidence presented throughout the lesson. |

**Q13 rubric (5 marks).** One mark each for: **naming the actual defect**, per §5.4 and §6 — the recovery
path reports "task completed" regardless of whether the underlying action actually succeeded after retries,
exactly the dishonest-recovery pattern this lesson demonstrates and §6's worked example shows at production
scale; **proposing the concrete fix**, per §5.4 — distinguishing "succeeded" from "retries exhausted, no
effect occurred" as two different, explicitly different reported outcomes, never collapsing them into one
success-shaped message; **connecting this to a measurable consequence**, per §7.4 — a caller (or a human)
reading only the reported status has no way to tell a real success from a masked failure without
independently checking the underlying system of record, exactly as this lesson's own lab demonstrated;
**proposing where the honest failure should route to**, per M8-L10 — an explicit failure signal can be
escalated to a human or a monitoring system, whereas a masked one cannot be, since nothing marks it as
needing attention; and **naming why this matters at scale**, per §6 — the worked example's incident was
discovered two days later, by a downstream consumer, specifically because the job's own reporting gave no
earlier signal. An answer that only says "add better logging" without addressing the reported status itself
scores 2.

---

<a id="m8-l14"></a>
## M8-L14 — Checkpointing and Durable Execution

**Answers: A · D · B · C · A · D · B · C · A · D · B · C**

| Q | Ans | Why, and why the distractors fail |
|---|---|---|
| 1 | **A** | The lab's own measured result: no durable record existed, so the restart re-executed all four steps including the already-completed refund. **B**, **C** and **D** contradict the lab's own printed setup and output. |
| 2 | **D** | The lab's own measured result: the resumed run skipped the three already-checkpointed steps, executing only the remaining one. **A**, **B** and **C** contradict the lab's own printed output. |
| 3 | **B** | The lab's own measured result: REFUND_LOG stayed empty because the resumed run trusted the checkpoint and skipped the never-executed step. **A**, **C** and **D** contradict this measured, printed result. |
| 4 | **C** | This is the lesson's own stated contrast between the two failure directions. **A**, **B** and **D** contradict this stated contrast. |
| 5 | **A** | The lesson states this directly: a narrow crash window still leaves ambiguity that idempotency protects against. **B**, **C** and **D** contradict this stated limitation. |
| 6 | **D** | The lesson states this directly as the residual risk correct ordering alone does not close. **A**, **B** and **C** contradict this stated risk. |
| 7 | **B** | The worked example states this directly as the root cause. **A**, **C** and **D** contradict the worked example's own stated facts. |
| 8 | **C** | The worked example states this directly as how the incident was found. **A**, **B** and **D** contradict the worked example's own stated facts. |
| 9 | **A** | This is the worked example's own stated general rule. **B**, **C** and **D** contradict this stated rule or overstate an absolute the lesson does not support. |
| 10 | **D** | This is the worked example's own stated pair of fixes. **A**, **B** and **C** propose approaches the worked example does not recommend. |
| 11 | **B** | Section 7.5 names these specifically as left to natural extensions. **A**, **C** and **D** name things this lesson does cover directly. |
| 12 | **C** | This is the lesson's own stated general conclusion, tying together every section's specific measured finding. **A**, **B** and **D** contradict this conclusion or the evidence presented throughout the lesson. |

**Q13 rubric (5 marks).** One mark each for: **naming the actual defect**, per §5.3 and §6 — checkpointing a
step as complete before executing it means a crash during that step's real execution leaves it marked done
when it never actually happened, exactly the ordering bug this lesson's own lab and worked example both
demonstrate; **proposing the concrete fix**, per §5.2 — reverse the ordering so the checkpoint is written
only after the step's action is confirmed to have genuinely completed; **explaining why "simplicity" is not
a valid justification here**, per §6 — the simpler-looking ordering trades a rare-but-real silent failure
(a missed action indistinguishable from success) for marginally simpler code, a bad trade for any
state-changing step; **noting that reordering alone is not a complete fix**, per §5.4 — a narrow race
between an action completing and its checkpoint being durably written still exists, so any step that must
remain fully safe should also carry an idempotency key (M8-L12); and **connecting this to detection**, per
§6 — proposing a way to verify a checkpoint's claims against the real system of record, since this class of
bug is otherwise invisible until an external party (a customer, a downstream report) notices the mismatch.
An answer that only says "checkpoint after, not before" without addressing the residual gap or detection
scores 3.

---

<a id="m8-l15"></a>
## M8-L15 — Step Limits, Cost Budgets and Runaway Prevention

**Answers: A · D · B · C · A · D · B · C · A · D · B · C**

| Q | Ans | Why, and why the distractors fail |
|---|---|---|
| 1 | **A** | The lab's own measured result: $0.10 versus $20.00, a 200x gap, for two runs respecting the identical step limit. **B**, **C** and **D** contradict this measured, printed result. |
| 2 | **D** | The lab's own measured result: exactly 2 real steps, stopping before a third would exceed the $5.00 budget. **A**, **B** and **C** contradict this measured, printed result. |
| 3 | **B** | The lab's own measured result: 3 steps with detection active versus the full 10 without it. **A**, **C** and **D** contradict this measured, printed result. |
| 4 | **C** | The lesson states this directly: the repeated action stayed cheap enough to remain under budget despite no progress. **A**, **B** and **D** contradict this stated and measured cause. |
| 5 | **A** | This is the lesson's own stated conclusion, drawn from all three sections' measured findings. **B**, **C** and **D** contradict this stated conclusion. |
| 6 | **D** | The lesson states this directly as the implicit assumption a step limit relies on to also bound cost. **A**, **B** and **C** name unrelated assumptions the lesson does not discuss. |
| 7 | **B** | The worked example states this directly as the root cause. **A**, **C** and **D** contradict the worked example's own stated facts. |
| 8 | **C** | The worked example states this directly as how the incident was found. **A**, **B** and **D** contradict the worked example's own stated facts. |
| 9 | **A** | This is the worked example's own stated general rule. **B**, **C** and **D** contradict this stated rule or overstate an absolute the lesson does not support. |
| 10 | **D** | This is the worked example's own stated pair of fixes. **A**, **B** and **C** propose approaches the worked example does not recommend. |
| 11 | **B** | Section 7.5 names these specifically as left to natural extensions or to M8-L13. **A**, **C** and **D** name things this lesson does cover directly. |
| 12 | **C** | This is the lesson's own stated general conclusion, tying together every section's specific measured finding. **A**, **B** and **D** contradict this conclusion or the evidence presented throughout the lesson. |

**Q13 rubric (5 marks).** One mark each for: **asking whether cost is bounded separately from step count**,
per §5.1 and §6 — a 30-call limit says nothing about total dollar exposure if different calls cost wildly
different amounts, exactly this lesson's own measured 200x gap; **asking whether the limit's calibration
assumed uniform per-step cost**, per §6 — the worked example's incident happened precisely because a
generous-looking step limit implicitly assumed this, an assumption that broke for one specific task
category; **asking whether unproductive repetition is separately detected**, per §5.3 — 30 calls of
identical, non-progressing action would stay fully within the step limit while accomplishing nothing;
**proposing a concrete cost-per-action-type audit**, per §6 — checking what the actual mix of cheap versus
expensive actions looks like across real runs, not just assuming it is representative; and **naming the
general principle**, per §5.4 — that a step-count limit, however carefully chosen, answers a different
question from a cost budget, and "generous and safe" describes only the step-count dimension unless cost is
checked too. An answer that only asks "is 30 the right number" without questioning what the limit actually
bounds scores 2.

---

<a id="m8-l16"></a>
## M8-L16 — Sandboxing and Least Privilege for Tools

**Answers: A · D · B · C · A · D · B · C · A · D · B · C**

| Q | Ans | Why, and why the distractors fail |
|---|---|---|
| 1 | **A** | The lab's own measured result: the SSN field was never part of the narrow tool's own data, structurally. **B**, **C** and **D** contradict the lab's own printed output. |
| 2 | **D** | The lab's own measured result: a genuine NameError, since __import__ was never in the sandboxed namespace. **A**, **B** and **C** contradict this measured, printed result. |
| 3 | **B** | The lab's own measured result: a genuine OS call executed, returning the real working directory. **A**, **C** and **D** contradict this measured, printed result. |
| 4 | **C** | The lesson states this directly as the structural reason removal beats checking. **A**, **B** and **D** contradict this stated reasoning. |
| 5 | **A** | This is the lesson's own stated definition of the framework's two inputs. **B**, **C** and **D** name unrelated inputs the framework does not use. |
| 6 | **D** | The lab's own measured result: exactly these four excess capabilities were named. **A**, **B** and **C** contradict this measured, printed result. |
| 7 | **B** | The worked example states this directly as the actual gap between intent and capability. **A**, **C** and **D** contradict the worked example's own stated facts. |
| 8 | **C** | The worked example states this directly as why the temporary plan failed. **A**, **B** and **D** contradict the worked example's own stated facts. |
| 9 | **A** | This is the worked example's own stated general rule. **B**, **C** and **D** contradict this stated rule or overstate an absolute the lesson does not support. |
| 10 | **D** | This is the worked example's own stated pair of fixes. **A**, **B** and **C** propose approaches the worked example does not recommend. |
| 11 | **B** | Section 7.4 names these specifically as substantial engineering efforts left beyond this lesson's scope. **A**, **C** and **D** name things this lesson does cover directly. |
| 12 | **C** | This is the lesson's own stated general conclusion, tying together every section's specific measured finding. **A**, **B** and **D** contradict this conclusion or the evidence presented throughout the lesson. |

**Q13 rubric (5 marks).** One mark each for: **naming the minimal capability actually needed**, per
§5.1-§5.4 — the ability to send an email to one specific, already-validated customer address and message
content, nothing broader; **naming what to deliberately withhold**, per §5.1 — access to the full customer
database, the ability to send to arbitrary or attacker-influenced addresses, and any capability to modify
records rather than only send a message; **connecting this to the removal-over-checking principle**, per
§5.3 — a tool that structurally cannot email an arbitrary address (because it only accepts a pre-validated
recipient, say) is safer than one that can email anyone but is expected to be checked at call time;
**applying the needed-versus-granted framework explicitly**, per §5.4 — stating what the tool needs versus
what it would be granted, and confirming no excess capability remains; and **connecting this to blast
radius**, per M5-L08 — an email-sending tool with broader-than-necessary reach (arbitrary recipients, bulk
sending) has a correspondingly larger worst-case outcome if manipulated. An answer that only says "give it
the minimum it needs" without naming a specific capability to withhold scores 2.

---

<a id="m8-l17"></a>
## M8-L17 — Tracing and Task-Level Evaluation

**Answers: A · D · B · C · A · D · B · C · A · D · B · C**

| Q | Ans | Why, and why the distractors fail |
|---|---|---|
| 1 | **A** | The lab's own measured result: each step's name, arguments, and result or error were recorded. **B**, **C** and **D** contradict the lab's own printed trace. |
| 2 | **D** | The lab's own measured result: step_level_check() returned True, since every call completed without error. **A**, **B** and **C** contradict this measured, printed result. |
| 3 | **B** | The lab's own measured result: task_level_check() returned False, because the refund reached the wrong customer. **A**, **C** and **D** contradict this measured, printed result. |
| 4 | **C** | The lesson states this directly as the reason the two checks disagree. **A**, **B** and **D** contradict this stated reasoning. |
| 5 | **A** | The lab's own measured result: the trace's recorded search_orders result was compared directly against the correct order. **B**, **C** and **D** contradict the lab's own printed diagnosis. |
| 6 | **D** | The lesson states this directly: both steps acted correctly given their own input. **A**, **B** and **C** contradict this stated and measured finding. |
| 7 | **B** | The worked example states this directly as the actual gap. **A**, **C** and **D** contradict the worked example's own stated facts. |
| 8 | **C** | The worked example states this directly as why the incident stayed invisible. **A**, **B** and **D** contradict the worked example's own stated facts. |
| 9 | **A** | This is the worked example's own stated general rule. **B**, **C** and **D** contradict this stated rule or overstate an absolute the lesson does not support. |
| 10 | **D** | This is the worked example's own stated pair of fixes. **A**, **B** and **C** propose approaches the worked example does not recommend. |
| 11 | **B** | Section 7.4 names these specifically as left to other lessons or as natural extensions. **A**, **C** and **D** name things this lesson does cover directly. |
| 12 | **C** | This is the lesson's own stated general conclusion, tying together every section's specific measured finding. **A**, **B** and **D** contradict this conclusion or the evidence presented throughout the lesson. |

**Q13 rubric (5 marks).** One mark each for: **naming the actual gap**, per §5.2 and §6 — a 99% step-level
success rate only measures whether individual calls completed without error, and says nothing about whether
the resulting outcomes were actually correct; **proposing a task-level metric**, per §5.2 — sampling a
subset of completed tasks and comparing their actual outcomes against a known-correct answer, independent of
whether every step technically succeeded; **proposing trace retention**, per §5.1 and §5.3 — recording a
structured trace per task so that once a task-level failure is found (by this new metric or by continued
complaints), the specific divergence point can be identified directly rather than guessed at; **connecting
this to the worked example's own precedent**, per §6 — this is the identical gap that let a real incident
grow for months while the existing dashboard reported near-perfect health; and **explaining why the two
metrics need to coexist**, per §5.2 — task-level evaluation does not make step-level monitoring obsolete,
since a genuine error is still worth catching separately from a wrong-but-error-free outcome. An answer that
only says "add better logging" without proposing a genuine task-level outcome check scores 2.

---

<a id="m8-l18"></a>
## M8-L18 — Tool Failures, Adversarial Inputs, Framework Choice, and When Not to Use an Agent

**Answers: A · D · B · C · A · D · B · C · A · D · B · C**

| Q | Ans | Why, and why the distractors fail |
|---|---|---|
| 1 | **A** | The lab's own measured result: the naive function returned 0.85 with no exception at all, despite the 500s-old cache. **B**, **C** and **D** contradict the lab's own printed output. |
| 2 | **D** | The lesson states this directly: nothing about the naive call is an error from the tool's own point of view, so there is no exception for M8-L03's handling to catch. **A**, **B** and **C** contradict this stated reasoning. |
| 3 | **B** | The lab's own measured result: naive_decide_next() chose issue_refund with the amount read directly out of the poisoned tool result's own text. **A**, **C** and **D** contradict the lab's own printed output. |
| 4 | **C** | The lesson states this directly: safe_decide_next() never reads tool result text as a source of instructions at all, regardless of content. **A**, **B** and **D** contradict this stated design. |
| 5 | **A** | This is the lesson's own stated framework, asking exactly these two questions. **B**, **C** and **D** name factors the framework does not use. |
| 6 | **D** | The lab's own measured result: this course's own situation (teaching why each mechanism works) recommended building from scratch specifically because a framework's abstractions would fight that requirement. **A**, **B** and **C** contradict this measured, printed result. |
| 7 | **B** | The lab's own measured result: classify_shape(True, False), M8-L01's own unmodified function, returned "WORKFLOW." **A**, **C** and **D** contradict this measured, printed result. |
| 8 | **C** | The lesson states this directly: all eight of Module 8's own safety mechanisms become relevant considerations if the workflow-shaped task were built as an agent anyway. **A**, **B** and **D** contradict this stated conclusion. |
| 9 | **A** | The worked example states this directly as the incident's actual root cause. **B**, **C** and **D** contradict the worked example's own stated facts. |
| 10 | **D** | This is the worked example's own stated general rule. **A**, **B** and **C** contradict this stated rule or the evidence the worked example presents. |
| 11 | **B** | Section 7.5 names these specifically as not shown here, deferring to M5-L13's own catalogue or to Project 8. **A**, **C** and **D** name things this lesson does cover directly. |
| 12 | **C** | This is the lesson's own stated general conclusion, tying together every section's specific measured finding. **A**, **B** and **D** contradict this conclusion or the evidence presented throughout the lesson. |

**Q13 rubric (5 marks).** One mark each for: **checking whether the task's control flow genuinely varies**,
per §5.4 and M8-L01 — applying the module's own classifier first, since a task with no branching or
model-selected decision is a workflow, not an agent, regardless of how it is currently built or marketed;
**checking for a concrete example of needed variability**, per §5.4 — asking for a specific case where the
next action could not have been determined by fixed code alone, not a hypothetical one; **explaining why this
matters for cost**, per §5.4 — building the feature as an agent when it is actually a workflow means paying
for some or all of this module's own safety apparatus (approval tiers, checkpointing, tracing, and the rest)
as pure overhead for a control flow that was never going to vary; **explaining why this matters for
security**, per §5.2 and M5-L08 — only a genuinely model-selected next action carries the tool-result
redirection risk this lesson demonstrates, so correctly classifying the task determines what actually needs
defending; and **naming the general principle**, per §5.4 — that "should we build this as an agent" has a
checkable, two-question answer, not a default answer either way. An answer that only asks "do we need an
agent?" without naming M8-L01's own classifier as the specific test scores 2.

---

*Module 8 is complete: all 18 lessons (M8-L01 through M8-L18) are answered above.*
