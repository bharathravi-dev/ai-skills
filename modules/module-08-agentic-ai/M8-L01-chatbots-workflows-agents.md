# M8-L01 — Chatbots, Workflows and Agents: a Precise Distinction

| | |
|---|---|
| **Lesson ID** | M8-L01 |
| **Difficulty** | 2 (Intermediate) |
| **Estimated study time** | 1.5 hours |
| **Prerequisites** | M5-L08 |

---

## 1. Learning objectives

1. **Define** a chatbot, a workflow, and an agent using two objective, checkable properties rather than
   marketing language.
2. **Classify** any given system as one of these three shapes from a description of its control flow alone.
3. **Demonstrate** that the same underlying tools, wired up three different ways, produce genuinely
   different behavior — not just different names for the same thing.
4. **Explain** why a workflow's fixed control flow can execute a wrong action a model-driven agent would
   have avoided.
5. **Connect** the agent shape's dynamically-chosen actions to the expanded safety surface Module 8 spends
   the rest of its lessons addressing.

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **Chatbot** | A system that only produces text from conversation and training — no tool calls, no side effects. |
| **Workflow** | A system that calls tools in a sequence fixed by code, regardless of what a specific request needs. |
| **Agent** | A system in which the model itself chooses, at runtime, which tool to call next based on what it has observed. |
| **Control flow** | The rule that decides what a system does next at each step. |
| **Model-selected action** | A next step chosen by the model's own output rather than hardcoded in advance (M8-L02). |

---

## 3. Plain-language explanation

### 3.1 "Agent" gets used for three different things

Industry writing calls chatbots, fixed pipelines, and genuinely autonomous systems all "agents"
interchangeably. This lesson exists to stop that: it gives two objective questions that classify any system
correctly, and this module builds on that classification for the next seventeen lessons.

### 3.2 The same tools, three different wirings

§7.1–§7.3 build the identical support-assistant tool set from M5-L08 three separate ways. §7.1's chatbot
never touches a tool at all. §7.2's workflow calls all three tools in a fixed order, every time — and gets
one of two test scenarios visibly wrong as a direct result. §7.3's agent calls the same tools, but lets a
decision step choose which one comes next, and correctly takes a shorter path when a refund was never
actually requested.

### 3.3 Two questions are enough to classify anything

§7.4 reduces the whole distinction to two yes/no questions: does the system take actions at all, and if so,
is the next action chosen by the model at runtime or fixed by code in advance? Applied to hand-written
descriptions and to the actual functions just executed, both give the same answer — classification doesn't
require reading an entire implementation.

### 3.4 The distinction has real engineering consequences, not just naming ones

§7.5 measures it directly: the workflow's step count is constant and knowable in advance; the agent's step
count genuinely varies with input, measured at 3 and 4 steps across the two test scenarios. That variability
is also exactly the surface M5-L08 flagged and left for this module — a workflow's fixed next step cannot be
hijacked by injected content, because there was never a model decision there to hijack in the first place.

---

## 4. Analogy

**A vending machine, an assembly line, and a chef.** A vending machine only ever does one thing per input —
press B4, get the item in B4 — with no judgment involved at all; if it doesn't dispense anything for a
request it can't fulfill, that's the whole of its behavior (a chatbot: bounded, textual, no real-world
action). An assembly line runs the same fixed sequence of stations on every unit that enters it, whether or
not that particular unit actually needs every station — a car destined for a market that doesn't require a
certain part still passes the station that would install it, because the line's sequence was fixed at design
time, not decided per-unit (a workflow). A chef, given the same ingredients and a request, decides what to
do next based on what's actually in front of them — taste the sauce, decide it needs more salt, taste again,
decide it's done — genuinely choosing each next step from what the last one revealed (an agent).

### Where the analogy breaks

- **A chef's decisions are famously hard to fully specify or predict in advance**, which is true of a real
  agent too — but a real agent's decision step is a model call that can, at least, be logged, traced, and
  bounded (M8-L15, M8-L17), unlike a chef's intuition.
- **An assembly line's fixed stations are usually a deliberate efficiency choice**, not a limitation — the
  same is often true of workflows: §7.2's wrong refund is a demonstration of the *risk*, not a claim that
  workflows are always the wrong choice. M8-L02 covers when each shape is actually the better engineering
  decision.

---

## 5. Detailed technical explanation

### 5.1 A chatbot structurally cannot check real data

`[REAL, measured]` §7.1 ran the same `chatbot_respond()` function against both a status question and a
refund request. **Neither call touched `search_orders`, `get_order`, or `issue_refund` — there is no code
path in a chatbot that reaches them.** The honest response it gives (declining to check real data) is not a
design choice about tone; it reflects an actual architectural limit: a chatbot has no mechanism to act on or
look up anything outside the conversation itself.

### 5.2 A workflow's fixed path produced a real, wrong outcome

`[REAL, measured]` §7.2's `refund_workflow()` always executes `search_orders` → `get_order` →
`issue_refund`, in that order, for every customer. Run against a customer who only asked about order status,
**it issued her a refund she never requested** — a genuine bug, not a hypothetical one, produced entirely by
the fact that the code's next step never depended on what the request actually said. **A workflow can still
call a model inside one of its steps (to draft text, say) — what makes it a workflow is that the next
*step* is never that model's decision.**

### 5.3 An agent's next action is chosen from what it has observed

`[REAL, measured]` §7.3's `run_agent()` used the identical tool set, but chose each next action from a
`decide_next_action()` step examining both the request and what had been observed so far. **The status-only
scenario genuinely stopped after 3 steps with no refund call; the refund scenario genuinely took 4 steps,
including one.** This is the load-bearing difference from §5.2: the same tools, wired so that the sequence
of calls is decided at runtime, correctly diverge based on what each request actually needs.

### 5.4 Two properties classify any system

`[REAL mechanism]` §7.4's `classify()` function needs only two facts: does the system take actions at all
(`takes_actions`), and if so, is the next one chosen by the model at runtime (`model_selects_next_action`)?
**Applied identically to three one-line system descriptions and to the three functions §7.1–§7.3 actually
ran, it produces the same three labels both times.** Classification is a property of control flow, checkable
from a description, not something that requires reading an entire codebase.

### 5.5 The variability is real, measurable, and has a name

`[REAL, measured]` §7.5 counted real steps from §7.2 and §7.3's own traces: the workflow took exactly 3
steps on both runs; the agent took 3 and 4 steps respectively across the two scenarios. **A workflow's cost
and latency are knowable in advance and constant; an agent's are genuinely data-dependent, only boundable
(the loop caps at 6 iterations), not fully predictable in advance.** This is stated as a direct, practical
engineering consequence of §5.3's finding, not a separate claim.

### 5.6 Assumptions and limitations

- `decide_next_action()` is a small, hand-coded rule standing in for a real model's judgment — a real agent
  (M8-L03) uses an actual model call to choose its next action, not a keyword check.
- The support-assistant tool set is this course's own running example (from M5-L08), not a claim about what
  a real support system's tools should look like.
- This lesson does not build a general-purpose, reusable tool-execution loop (M8-L03), planning across
  multiple steps before acting (M8-L04), or any of the safety mechanisms it names (M8-L10, M8-L12, M8-L15,
  M8-L16 each build one in depth).

---

## 6. Worked example — the "agent" that was actually a workflow with extra steps

**The pitch.** A team announces they've built an "autonomous customer support agent" and demonstrates it
successfully handling three sample tickets end to end: looking up an order, checking a policy, and issuing a
refund.

**The question that mattered.** A reviewer, applying §5.4's two-question test, asks: for a ticket that
*doesn't* need a refund, does the system skip that step — and is that skip decided by the model, or is the
refund step simply guarded by a fixed `if "refund" in ticket_text` check written by the engineering team?

**What the investigation found.** Every one of the three demo tickets happened to need every step the system
performed. The "decision" to skip the refund step for a non-refund ticket was, in fact, a single hardcoded
keyword check — not a model call, not a judgment about context, just a fixed branch. **By §5.4's test, this
system is a workflow: `takes_actions=True`, `model_selects_next_action=False`.** It had been marketed, and
budgeted, as an agent.

**Why this distinction was not pedantic.** Per §5.5, the team's cost and reliability projections assumed
agent-level flexibility — the ability to handle novel ticket types the fixed keyword checks had never
anticipated. A genuinely new ticket type (a partial refund combined with a shipping address change) fell
straight through every branch and produced no action at all, silently, because no keyword check matched it.
An actual agent, choosing its next action from what it observed, would at least have had a chance to
recognize the combination; the workflow's fixed branches structurally could not.

**Three defects the mislabeling produced:**

| # | Defect | Consequence |
|---|---|---|
| 1 | The system was classified as an agent without applying §5.4's two-question test | Budget and reliability expectations were set for a shape the system did not actually have |
| 2 | "Decision" logic was a fixed keyword branch, not a model-selected action | Any ticket type not anticipated by the keyword list fell through silently, per §5.2's own demonstrated failure mode |
| 3 | The demo set covered only ticket types every branch already handled | The gap was invisible until a genuinely novel ticket arrived in production |

### The fix

**Apply §5.4's two-question test before naming or budgeting for a system**, rather than after — "does it
call tools" is not sufficient; "is the next tool chosen by the model" is the second, decisive question.

**Test with inputs the fixed branches don't anticipate**, not only inputs every branch already handles — per
§5.2, a workflow's failure mode is specifically inputs its designer didn't foresee.

**The general rule.** **Whether a system is a workflow or an agent is a property of its control flow, not
of how it is marketed or what its demo covers — and the two questions in §5.4 settle it in about thirty
seconds, before any budget or reliability claim is made on top of the label.**

---

## 7. Practical activity

**File:** [`labs/m8/l01_chatbots_workflows_agents.py`](../../labs/m8/l01_chatbots_workflows_agents.py)

**No API key, no network, no third-party dependencies.** Runs in well under a second.

```bash
source .venv/bin/activate
python labs/m8/l01_chatbots_workflows_agents.py
```

### 7.2 Expected output

`[EXECUTED]` — 2026-09-10, Python 3.10.11 (pure standard library).

```text
============================================================================
1. CHATBOT: TEXT IN, TEXT OUT, NO TOOLS AT ALL
============================================================================
  Request: 'What is the status of my order?'
  Chatbot response: "I don't have access to your order records, so I can't check that or take any action on it -- I can only discuss general policy questions."

  Request: "My order hasn't arrived, I'd like a refund."
  Chatbot response: "I don't have access to your order records, so I can't check that or take any action on it -- I can only discuss general policy questions."

  Neither call above touched search_orders, get_order, or issue_refund
  -- structurally, a chatbot CANNOT look anything up or change any real
  state, no matter how the request is worded. That is not a missing
  feature in this mock; it is the definition of the shape.

============================================================================
2. WORKFLOW: TOOLS CALLED IN A SEQUENCE FIXED BY CODE
============================================================================
  Running the SAME fixed workflow for BOTH scenarios:

  Request: 'What is the status of my order?'
    search_orders('Priya Shah') -> 'O-1002'
    get_order('O-1002') -> {'item': 'Desk Lamp', 'amount': 40.0, 'status': 'delivered'}
    issue_refund('O-1002', 40.0) -> 'Refund of $40.00 issued for O-1002.'

  Request: "My order hasn't arrived, I'd like a refund."
    search_orders('Dana Kim') -> 'O-1001'
    get_order('O-1001') -> {'item': 'Wireless Mouse', 'amount': 25.0, 'status': 'delayed in transit'}
    issue_refund('O-1001', 25.0) -> 'Refund of $25.00 issued for O-1001.'

  REFUNDS_ISSUED so far: [('O-1002', 40.0), ('O-1001', 25.0)]

  The workflow issued a refund to Priya Shah, who only asked about
  STATUS and never requested one -- a real, demonstrated consequence
  of a FIXED path: the code always executes all three steps, because
  nothing in the workflow's control flow branches on what the request
  actually needs. A workflow can still call a model INSIDE a step (to
  draft the reply text, say) -- what makes it a workflow is that the
  NEXT STEP is never that model's decision.

============================================================================
3. AGENT: TOOLS CALLED IN A SEQUENCE THE MODEL CHOOSES, STEP BY STEP
============================================================================
  Running the SAME tool set through an AGENT loop for BOTH scenarios:

  Request: 'What is the status of my order?'
    [model chose] search_orders('Priya Shah') -> 'O-1002'
    [model chose] get_order('O-1002') -> {'item': 'Desk Lamp', 'amount': 40.0, 'status': 'delivered'}
    [model chose] respond -- stop, enough information gathered

  Request: "My order hasn't arrived, I'd like a refund."
    [model chose] search_orders('Dana Kim') -> 'O-1001'
    [model chose] get_order('O-1001') -> {'item': 'Wireless Mouse', 'amount': 25.0, 'status': 'delayed in transit'}
    [model chose] issue_refund(...) -> 'Refund of $25.00 issued for O-1001.'
    [model chose] respond -- stop, enough information gathered

  REFUNDS_ISSUED this time: [('O-1001', 25.0)]

  This time, Priya Shah's status question genuinely takes a DIFFERENT,
  SHORTER path than Dana Kim's refund request -- no issue_refund call
  for Priya at all, decided step by step from what was actually
  observed. Same tools as section 2; genuinely different, request-
  dependent behavior, because the NEXT action is chosen at runtime
  instead of fixed in advance.

============================================================================
4. A CHECKABLE DEFINITION, APPLIED TO REAL AND DESCRIBED SYSTEMS
============================================================================
  Applying the same two-question test to described systems:

    CHATBOT  -- A pure Q&A bot with no tool access, answering from general knowledge only
    WORKFLOW -- A pipeline that always fetches an order, then always emails a confirmation
    AGENT    -- A system that decides whether to search, check inventory, or refund, based on what it finds

  And applying it to what sections 1-3 actually ran, not just described:
    CHATBOT  -- section 1's chatbot_respond()
    WORKFLOW -- section 2's refund_workflow()
    AGENT    -- section 3's run_agent()

  Same two questions, same answers, whether applied to a one-line
  description or to the actual functions just executed above --
  classification does not require reading the whole implementation,
  only these two properties of its control flow.

============================================================================
5. WHY THE DISTINCTION IS NOT JUST TERMINOLOGY
============================================================================
  Section 2's workflow: ALWAYS 3 steps -- constant, by
  construction, regardless of input.
  Section 3's agent, measured from its own real traces: {'Priya Shah': 3, 'Dana Kim': 4} steps.
  Range across these two real scenarios: 3-4 steps.

  A workflow's step count -- and so its cost and latency -- is knowable
  in advance and identical on every run: it can be tested exhaustively,
  because there is only one path. An agent's step count is genuinely
  DATA-DEPENDENT, as just measured -- its cost, latency, and the exact
  sequence of actions taken cannot be fully enumerated in advance the
  same way, only bounded (the loop above stops after 6 iterations no
  matter what, M8-L15's own topic previewed here).

  This is also exactly the expanded surface M5-L08 flagged and left
  for this module: 'the model calls a tool, the result contains an
  instruction, the model calls another tool' is only a LOOP risk for
  the AGENT shape -- a workflow's next step was never the model's to
  decide, so there is no such decision for injected content to hijack.
  This is the real reason Module 8 spends whole lessons on approval
  gates (M8-L10), idempotency (M8-L12), step limits (M8-L15), and
  sandboxing (M8-L16): they matter specifically BECAUSE an agent's
  next action is chosen at runtime, not because tools exist at all.

============================================================================
6. WHAT THIS LAB IS AND IS NOT
============================================================================
  REAL: every tool call, trace, and step count in sections 1-3 is
  genuinely executed against the shared mock backend -- the workflow's
  wrong refund and the agent's differing step counts are measured
  outcomes of running the code, not asserted claims. Section 4's
  classify() function is real and applied identically to both
  described and actually-executed systems.

  ILLUSTRATIVE: decide_next_action() is a small, hand-coded rule
  standing in for a real model's judgment -- a real agent (M8-L03)
  uses an actual model call to choose its next action, not a keyword
  check. The specific tool set is this course's own running example,
  not a claim about what a real support system's tools look like.

  NOT SHOWN: a general-purpose, reusable tool-execution loop (M8-L03
  builds one from scratch); planning across multiple steps before
  acting (M8-L04); and any of the safety mechanisms named in section 5
  (M8-L10, M8-L12, M8-L15, M8-L16 each build one in depth).

Done.
```

### 7.3 Reading the result

**Sections 2 and 3 are the same test, twice, on purpose.** Running identical scenarios through both shapes
and comparing the actual outcome — a wrong refund from the workflow, a correct divergence from the agent —
is more convincing than any definition, because the difference in behavior is directly observable, not
asserted.

**Section 4's self-check is the important detail.** Applying the classifier to the actual functions just
executed, and getting the same labels as the hand-written descriptions, confirms the two-question test isn't
just a plausible-sounding heuristic — it agrees with what the code demonstrably does.

**Section 5 turns "agents are less predictable" from a vibe into a number.** 3 steps versus 3–4 steps looks
small in this toy example; the same variability, in a system with a dozen possible tools, is the real reason
the rest of this module exists.

---

## 8. Common mistakes and troubleshooting

1. **Calling any system that uses tools "an agent."** §5.4 — tool use alone is not sufficient; the second
   question (who chooses the next tool) is what actually separates a workflow from an agent.
2. **Assuming a workflow is simply a worse or more primitive agent.** §6 — a workflow is often the *correct*
   choice when the set of needed steps genuinely never varies; the risk is mislabeling one as the other, not
   workflows existing at all.
3. **Testing a system labeled "agent" only with inputs every branch already handles.** §6 — the gap between
   a workflow and a real agent only shows up on inputs the designer didn't anticipate.
4. **Assuming a fixed-order pipeline can't call a model at all.** §5.2 — a workflow can call a model inside
   a step; what makes it a workflow is that the *next step* is still fixed by code, not by that call's
   output.
5. **Treating "agent" as a spectrum rather than checking the two properties directly.** §5.4 — the
   classification is binary per property and checkable from a description, not a matter of degree.

| Symptom | Likely cause | Fix |
|---|---|---|
| A system performs an action nobody wanted for a specific request | A fixed workflow path executed a step that didn't apply to that request | Check whether the step's execution should have been conditional on the model's judgment, not fixed (§5.2, §6) |
| A system marketed as "autonomous" fails silently on a novel input type | It is actually a workflow with hardcoded branches, not a real agent | Apply §5.4's two-question test before trusting the label; add a genuinely model-selected fallback path |
| Cost or latency projections for an "agent" turn out wildly wrong in production | The system was actually a workflow (constant, predictable cost) or its variability was never measured | Measure real step-count range across representative scenarios, per §5.5, before projecting cost |
| Uncertainty about whether a proposed design needs agent-level flexibility at all | The actual set of required steps was never checked for whether it ever varies | Apply §5.4: if the needed actions are always the same regardless of input, a workflow is simpler and more predictable |

---

## 9. Security, privacy, reliability, cost

- **Reliability.** Classify a system with §5.4's two objective questions before trusting how it is marketed
  or demoed — a workflow mislabeled as an agent inherits reliability assumptions it cannot actually meet
  (§6).
- **Reliability.** Test a system for novel inputs its fixed branches (if any) do not anticipate, not only
  inputs every branch already handles (§6).
- **Security.** Only the agent shape has a model-selected next action for injected content to potentially
  redirect (M5-L08's own foreshadowing) — this is why Module 8's safety lessons (M8-L10, M8-L12, M8-L15,
  M8-L16) matter specifically for agents, not workflows or chatbots (§5.5).
- **Cost.** A workflow's cost and latency are constant and predictable in advance; an agent's are
  data-dependent and must be measured across representative scenarios, not assumed (§5.5).

---

## 10. Exercises

### Exercise 1 — Beginner (~20 min)

1. What are the two objective questions this lesson uses to classify a system?
2. Why did the workflow in §7.2 issue a refund nobody asked for?
3. Why did the agent in §7.3 correctly avoid that same mistake?
4. Can a workflow call a model at all? If so, what specifically makes it a workflow rather than an agent?
5. Why is an agent's step count harder to predict in advance than a workflow's?

### Exercise 2 — Intermediate (~40 min)

1. Run the lab. Confirm the workflow's wrong refund and the agent's differing step counts in §7.2 and §7.3
   on your own machine.
2. Design a third test scenario (a new customer/request pair) and predict, before running it, whether the
   workflow and the agent will produce the same or different outcomes. Add it to the lab and check your
   prediction.
3. Using §5.4's classify() function, write three new one-line system descriptions of your own (one of each
   shape) and confirm they classify correctly.
4. Extend `decide_next_action()` with a new possible action (e.g., checking a shipping carrier) and confirm
   the agent's step count changes only for scenarios that actually need it.
5. Using §5.5's measurement approach, add a third scenario to the agent loop and report the new min/max step
   range across all three.

### Exercise 3 — Challenge (~50 min)

1. Design (on paper) a fourth system shape — a workflow with exactly one conditional branch chosen by a
   model, for a single specific decision point — and classify it using §5.4's test. Does it fit cleanly
   into "workflow" or "agent," or does it reveal a gap in the two-question test?
2. Using M5-L08's own foreshadowed "agent-loop attack," describe concretely how injected content in a tool
   result could change an agent's next chosen action in this lab's own `decide_next_action()`, and why the
   same content could not do anything analogous to the workflow in §7.2.
3. Research (conceptually) how a real orchestration framework distinguishes a workflow step from an agent
   step in its own terminology, and compare it to this lesson's two-question test.
4. Propose a monitoring signal that would detect, in production, whether a system labeled "agent" is
   actually behaving like a workflow (i.e., its step sequence never actually varies across real traffic).
5. Using §6's worked example, write a short pre-launch checklist a team could apply to avoid mislabeling a
   workflow as an agent before it ships.

---

## 11. Quiz

*(Answers: [`answer-keys/module-08-answers.md`](../../answer-keys/module-08-answers.md#m8-l01).)*

**Q1.** Per §7.4, what two properties does this lesson use to classify a system as a chatbot, workflow, or
agent?

- A. Whether the system uses Python, and how many lines of code it has.
- B. Whether the system takes actions at all, and if so, whether the model chooses the next action at runtime or it is fixed by code in advance.
- C. Whether the system is described as an "agent" in its own documentation.
- D. Whether the system responds in under one second.

**Q2.** Per §7.1's measured result, why did neither chatbot call ever reach `search_orders`, `get_order`,
or `issue_refund`?

- A. The mock backend was offline during that section.
- B. The chatbot's request-matching logic had a bug.
- C. A chatbot has no code path that reaches a tool at all — this is a structural property of the shape, not a missing feature.
- D. Both requests were phrased in a way no chatbot could parse.

**Q3.** Per §7.2's measured result, why did the workflow issue a refund to a customer who only asked about
order status?

- A. The workflow always executes the same fixed sequence of three tool calls regardless of what the request actually says.
- B. A random error caused the wrong tool to be called.
- C. The customer's request was misread as a refund request due to a parsing bug.
- D. The workflow correctly identified this as an edge case requiring a refund.

**Q4.** Per §7.3's measured result, what specifically allowed the agent to avoid the workflow's mistake for
the same status-only scenario?

- A. The agent used a larger, more capable underlying tool set than the workflow.
- B. The agent always skips the issue_refund tool regardless of the request.
- C. The agent was manually configured in advance to skip Priya Shah specifically.
- D. The agent's decision step chose "respond" once order details were observed, since the request never asked for a refund — a genuinely different, shorter path than the refund scenario took.

**Q5.** Per §7.4, can a workflow call a model inside one of its steps?

- A. No — a workflow by definition never calls a model at all.
- B. Yes — what makes it a workflow is that the next step is still fixed by code, not chosen by that model call's output.
- C. Yes, but only if the model call happens before the first tool call.
- D. Yes, but only for the final response, never for an intermediate step.

**Q6.** Per §7.4's measured result, what happened when the classify() function was applied to the three
functions sections 1-3 actually executed, compared to the three hand-written descriptions?

- A. It could not classify the actual functions, only the written descriptions.
- B. It produced different labels, revealing an error in the hand-written descriptions.
- C. It produced the same three labels both times, confirming the test agrees with what the code demonstrably does.
- D. It classified all three actual functions as agents regardless of their real behavior.

**Q7.** Per §7.5's measured result, how did the workflow's step count compare to the agent's across the two
test scenarios?

- A. The workflow was always 3 steps; the agent varied between 3 and 4 steps depending on the scenario.
- B. Both were identical and constant across both scenarios.
- C. The workflow's step count varied more than the agent's.
- D. The agent's step count could not be measured from its own trace.

**Q8.** Per §7.5, why is a workflow's cost and latency easier to predict in advance than an agent's?

- A. Workflow and agent cost predictability are actually identical, per this section.
- B. Because a workflow never calls any tools, so it has no cost at all.
- C. Because an agent's step count is always larger than a workflow's.
- D. Because a workflow's step count is constant and knowable in advance, while an agent's is genuinely data-dependent, only boundable rather than fully predictable.

**Q9.** Per §7.5, why does M5-L08's "agent-loop attack" apply specifically to the agent shape and not to
the workflow shape?

- A. Because workflows never call tools that could be affected by injected content.
- B. Because a workflow's next step was never the model's decision in the first place, so there is no such decision for injected content in a tool result to hijack.
- C. Because agents are immune to injected content by design.
- D. Because the attack applies equally to all three shapes covered in this lesson.

**Q10.** Per §6's worked example, what specific test revealed that the "autonomous agent" was actually a
workflow?

- A. Checking whether its demo tickets were handled correctly.
- B. Checking its total development budget.
- C. Checking whether the skip of a non-applicable step was a model decision or a fixed keyword check — applying §5.4's two-question test.
- D. Checking how many tools it had access to.

**Q11.** Per §7.6, what does this lesson explicitly NOT build?

- A. A general-purpose, reusable tool-execution loop, planning across multiple steps, and the safety mechanisms named in section 5 — each left to later lessons (M8-L03, M8-L04, M8-L10, M8-L12, M8-L15, M8-L16).
- B. The classify() function used in section 4.
- C. The mock support-assistant backend used throughout the lab.
- D. The workflow and agent functions demonstrated in sections 2 and 3.

**Q12.** What is the general lesson this lab demonstrates about the chatbot/workflow/agent distinction?

- A. The distinction is purely a matter of marketing terminology with no real engineering consequence.
- B. Only the number of tools a system has access to determines which of the three shapes it is.
- C. All three shapes always produce identical behavior when given the same tools.
- D. Whether a system is a workflow or an agent is a checkable property of its control flow, with measurable consequences for correctness, predictability, cost, and security surface — not a label assigned by how the system is described or demoed.

**Q13.** *(Written, rubric-graded.)* In under 150 words: a colleague describes a new internal tool as "an
AI agent that handles expense report approvals." Using this lesson's two-question test, what would you ask
them to find out whether it's actually a workflow, and why does the answer matter?

---

## 12. Revision notes

- **Two objective questions classify any system**: does it take actions at all, and if so, does the model
  choose the next action at runtime or is it fixed by code? — chatbot, workflow, and agent respectively.
- **The same tools, wired three different ways, produced measurably different, real outcomes** — the
  workflow issued an unwanted refund; the agent correctly avoided it, using the identical tool set.
- **A workflow can call a model inside a step** — what defines the shape is that the *next step* is still
  fixed by code, never by that call's output.
- **Classification agrees whether applied to a description or to actually-executed code** — it is a
  property of control flow, not a matter of reading an entire implementation.
- **A workflow's cost is constant and predictable; an agent's is genuinely data-dependent** — measured
  directly as 3 steps (constant) versus 3–4 steps (scenario-dependent) across two real test cases.
- **The agent shape's dynamically-chosen next action is specifically what creates the loop-hijack risk
  M5-L08 foreshadowed** — a workflow's fixed next step has no equivalent decision point to redirect.

---

## 13. Completion checklist

- [ ] I can state the two objective questions that classify a chatbot, a workflow, and an agent.
- [ ] I can classify a system from a one-line description of its control flow.
- [ ] I can explain why the same tools produced different outcomes when wired as a workflow versus an
      agent.
- [ ] I can explain why a workflow can call a model and still not be an agent.
- [ ] I can connect an agent's dynamically-chosen actions to the expanded safety surface this module covers.
- [ ] I apply the two-question test before trusting how a system is marketed or demoed.
- [ ] I scored 10/13 on the quiz.

---

## 14. References

- Anthropic, *Building Effective Agents* (workflows vs. agents framing), where available. `[UNVERIFIED]`
- M5-L08's own foreshadowing of "the agent-loop attack," referenced directly throughout this lesson.
  `[STABLE]`

---

## 15. Next lesson

→ M8-L02 — Deterministic Execution vs Model-Selected Actions

This lesson classified systems from the outside. Next: a closer look at exactly where, inside a single
step, control passes from your code's own logic to the model's choice — and how to decide, deliberately,
which parts of a real system should be which.
