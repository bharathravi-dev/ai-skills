# M8-L09 — Single-Agent vs Multi-Agent Designs

| | |
|---|---|
| **Lesson ID** | M8-L09 |
| **Difficulty** | 3 (Advanced) |
| **Estimated study time** | 1.75 hours |
| **Prerequisites** | [M8-L08](M8-L08-orchestrator-worker-evaluator-optimizer.md) |

---

## 1. Learning objectives

1. **Explain** why a single agent's context grows with every step while a multi-agent design's hand-off
   stays small.
2. **Demonstrate** that a hand-off summary can lose a specific, identifiable detail a later agent then
   cannot produce.
3. **Identify** the case where splitting into separate agents costs nothing, because no information needs
   to cross a boundary at all.
4. **Apply** a three-way framework to decide between a single agent, free multi-agent isolation, and
   multi-agent with a carefully engineered hand-off.
5. **Distinguish**, from a described incident, whether a multi-agent design's cost came from unnecessary
   coordination or from a genuine information-loss risk.

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **Single-agent design** | One agent, one growing context, handling every step of a task. |
| **Multi-agent design** | Separate agents, each with its own context, coordinating through explicit hand-offs. |
| **Hand-off** | Information passed from one agent to another — often a summary rather than the full context. |
| **Information-loss risk** | The chance that a hand-off's summary omits a detail a later step actually needs. |
| **Free isolation** | A multi-agent split with no hand-off cost, because the agents share no needed information. |

---

## 3. Plain-language explanation

### 3.1 M8-L08 stayed inside one context; this lesson asks when to leave it

Orchestrator-worker and evaluator-optimizer (M8-L08) both operate within one unified point of control —
the orchestrator sees every worker's result; the optimizer sees every attempt. This lesson asks the
structural question underneath that choice: when does splitting work across genuinely separate agents, each
with its own context, actually pay for the coordination it costs?

### 3.2 A single agent's context is complete and growing; a hand-off is smaller and risky

§7.1 and §7.2 measure the same investigation two ways. Kept in one agent's context, every detail — down to
a specific error code — remains available to the step that drafts the final response. Handed off as a
summary to a separate agent, the context shrinks by a measured 75%, and the specific error code, never
present in the summary text at all, cannot appear in the second agent's response either.

### 3.3 Sometimes there's nothing to hand off, and isolation is free

§7.3 shows the other side: three genuinely unrelated cases split across three agents costs nothing beyond
each case's own data, because none of them needs anything the others know. This is the case multi-agent
designs are built for — not a consolation prize next to single-agent's completeness, but the situation
where isolation carries no real cost at all.

### 3.4 Three real situations, three different recommendations

§7.4 doesn't collapse this into two categories. Alongside "keep it in one agent" and "split with no cost,"
it names a third: split, but engineer the hand-off to carry specific, named fields rather than relying on
free-text summarization — the situation where information does need to cross a boundary, but a careful
hand-off design still makes the split worthwhile.

---

## 4. Analogy

**A single detective working a case alone, versus a specialist handing a case file to a second specialist,
versus three detectives each assigned their own unrelated case.** A lone detective who investigates a
crime and then writes the final report has, by definition, lost nothing between finding a clue and writing
about it — the same person holds it all. A forensics specialist who hands a case to a detective with only a
one-paragraph summary of the lab results has genuinely reduced what the detective has to read, but a
specific, minor-seeming detail from the full lab report might never make it into that paragraph — and the
detective has no way to know it existed at all. Three detectives, each independently assigned a completely
unrelated case, lose nothing by working separately, because nothing about one case ever depended on the
others.

### Where the analogy breaks

- **A human forensics specialist can be asked follow-up questions if the detective realizes something is
  missing.** §7.2's hand-off is one-directional and final in this lab — a real multi-agent system might
  support the second agent requesting more detail, which this lesson does not model.
- **Three detectives working unrelated cases still work in the same building, on the same clock.** This
  lesson measures information content, not real-world cost or latency differences between running agents
  concurrently versus sequentially (that comparison is M8-L07's own territory, applied at the tool-call
  level, not the agent level).

---

## 5. Detailed technical explanation

### 5.1 A single agent's context has no boundary for information to fail to cross

`[REAL, measured]` §7.1 accumulated three investigation observations into one growing context (290
characters by the end) and drafted a customer response directly from it. **The response correctly included
both the outage region and the specific error code**, because both were still present in what the drafting
step could see — there was no point at which anything needed to be summarized or dropped.

### 5.2 A hand-off's size reduction is exactly its information-loss risk, measured

`[REAL, measured]` §7.2 handed the same investigation to a second agent as a 72-character summary — a
**measured 75% size reduction**. The summary genuinely, correctly captured the general cause (a regional
outage) but did not include the specific error code anywhere in its text. **The second agent's response
could not mention the error code not because of any bug, but because the code was never present in what it
was given to work with.** The size reduction and the information loss are the same fact, measured from two
angles.

### 5.3 True independence makes the split free

`[REAL, measured]` §7.3 split three unrelated cases across three agents. The combined size of the three
separate contexts (188 characters) was close to what one agent handling all three in a single context would
need (173 characters) — **the small difference is entirely per-case labeling overhead, not any lost
information**, because none of the three cases ever needed anything the other two knew. This is the
structural opposite of §7.2: no hand-off occurred because none was needed.

### 5.4 A third option exists between "keep it together" and "split for free"

`[REAL mechanism]` §7.4's `recommend_design()` names three outcomes, not two: single agent (when full,
unabridged detail must survive to a later step), free multi-agent (when nothing needs to cross a boundary
at all), and **multi-agent with a carefully engineered hand-off** (when some specific, identifiable
information must cross, but a structured hand-off — passing named fields rather than free prose — could
preserve it deliberately, unlike §7.2's lossy summary). This third case is what a research-to-writing split
represents: information must cross, but *designing* the hand-off to preserve what's needed is a real,
separate decision from whether to split at all.

### 5.5 Assumptions and limitations

- `summarize_for_handoff()` is a small, hand-written stand-in for a real summarization step — a real
  system might use a model call to summarize, which could preserve or drop different specific details than
  this lesson's own example.
- This lesson does not cover how agents actually pass messages to each other in a real framework (message
  protocols, formats), a hand-off design that explicitly preserves specific fields rather than relying on
  free-text summarization, or cost/latency comparisons between running several agents and one agent making
  several tool calls (a natural extension of M8-L07's own measurements).

---

## 6. Worked example — the support system that lost the account number twice

**The system.** A support platform splits ticket handling into two agents: an "intake" agent that gathers
customer details and produces a summary, and a "resolution" agent that reads the summary and takes action.

**The incident.** A customer's ticket included their account number, mentioned once during intake. The
intake agent's summary described the customer's issue accurately but — like §7.2's summary omitting a
specific error code — never included the account number itself, since it wasn't judged central to
describing the *problem*. The resolution agent, unable to identify which account to act on from the summary
alone, had to ask the customer to repeat information they had already provided.

**Why this matches §5.2 exactly, and not §5.4's third case.** The intake-to-resolution split was a
genuinely useful design — the two agents do different jobs, and nothing here suggests they should be
merged into one. **The defect was that the hand-off relied on free-text summarization instead of an
explicit, structured field** for the account number specifically — exactly the distinction §5.4 draws
between "any hand-off" and a hand-off engineered to preserve what a later step actually needs.

**Three defects the incident revealed:**

| # | Defect | Consequence |
|---|---|---|
| 1 | The hand-off was a free-text summary with no guaranteed fields | Any detail not judged "central" to the summary could be silently dropped, unpredictably |
| 2 | The account number specifically was never treated as a required field | The resolution agent had no way to detect that something it needed was missing, only that it wasn't present |
| 3 | No test exercised what the resolution agent could do with a summary lacking the account number | The gap was invisible until a real customer experienced the repeated-information friction |

### The fix

**Keep the split** — per §5.4, intake and resolution genuinely do different jobs, and this is not a case
for merging into one agent.

**Engineer the hand-off to include explicit, named fields for anything a later agent will definitely need**
(account number, ticket ID, customer contact method), separate from the free-text summary of the issue
itself — exactly §5.4's third recommendation, applied concretely.

**The general rule.** **A multi-agent split is not itself the defect when information goes missing at a
hand-off — the defect is relying on an unstructured summary for details a later agent will definitely need,
when a structured, explicit field could have preserved them deliberately instead of hoping a prose summary
happens to mention them.**

---

## 7. Practical activity

**File:** [`labs/m8/l09_single_vs_multi_agent.py`](../../labs/m8/l09_single_vs_multi_agent.py)

**No API key, no network, no third-party dependencies.** Runs in well under a second.

```bash
source .venv/bin/activate
python labs/m8/l09_single_vs_multi_agent.py
```

### 7.2 Expected output

`[EXECUTED]` — 2026-09-10, Python 3.10.11 (pure standard library).

```text
============================================================================
1. SINGLE-AGENT CONTEXT: EVERYTHING ACCUMULATES, NOTHING IS LOST
============================================================================
  A single agent investigates, accumulating EVERY observation into
  one growing context:

    [check_error_logs] Error code E-4471 at 14:32 UTC: connection timeout after 30s, retried 3x, all failed.
      -- context size so far: 105 characters
    [check_service_status] Regional outage in us-east-2 confirmed, started 14:28 UTC, ongoing.
      -- context size so far: 196 characters
    [check_customer_impact] Customer's account region: us-east-2. Affected by the ongoing outage.
      -- context size so far: 290 characters

  Full accumulated context (290 characters):
    "[check_error_logs] Error code E-4471 at 14:32 UTC: connection timeout after 30s, retried 3x, all failed.\n[check_service_status] Regional outage in us-east-2 confirmed, started 14:28 UTC, ongoing.\n[check_customer_impact] Customer's account region: us-east-2. Affected by the ongoing outage.\n"

  Single-agent's customer response (drafted from the FULL context):
    "We're sorry for the disruption to your service. This was caused by a regional outage in us-east-2. Your specific error was logged as E-4471, which our team can use to confirm your case if you contact support."

============================================================================
2. MULTI-AGENT HAND-OFF: A SMALLER CONTEXT, BUT A REAL RISK OF LOSING A DETAIL
============================================================================
  Technical agent hands off a SUMMARY instead of the full context:
    "There was a confirmed regional outage affecting this customer's account."

  Full context: 290 characters
  Handoff summary: 72 characters
  Size reduction: 75% smaller --
  a real, measurable saving for whatever agent receives it.

  Communications agent's response (drafted from ONLY the summary):
    "We're sorry for the disruption to your service."

  Does the single-agent response mention the specific error code? True
  Does the multi-agent response mention the specific error code? False

  The error code was never lost by accident or by a bug in
  draft_customer_response() -- it is simply not PRESENT in the
  summary text at all, so there was nothing for the function to
  find. This is the real trade-off: the smaller context measured
  above is smaller because something specific was left out of it.

============================================================================
3. WHERE MULTI-AGENT HAS NO SUCH COST: TRULY INDEPENDENT INVESTIGATIONS
============================================================================
  Three genuinely unrelated cases, each handled by its OWN agent with
  its OWN, independently-sized context -- none needs anything from
  the others:

    Customer A's agent context (60 chars): "[Customer A's case] Billing dispute over a duplicate charge."
    Customer B's agent context (64 chars): "[Customer B's case] Password reset request after a failed login."
    Customer C's agent context (64 chars): "[Customer C's case] Question about international shipping rates."

  Three separate agent contexts, summed: 188 characters
  One single agent handling all three in one context: 173 characters

  Here, splitting into separate agents costs NOTHING beyond the raw
  size of each case's own data -- there is no hand-off between them
  at all, because none of the three cases needs anything from the
  other two. Unlike section 2, no detail is at risk of being lost,
  because nothing needs to cross an agent boundary in the first place.

============================================================================
4. A FRAMEWORK: WHEN DOES SPLITTING INTO AGENTS PAY FOR ITSELF
============================================================================
    SINGLE AGENT (a hand-off risks losing detail a later step needs)
      -- Technical investigation feeding a customer response that must cite specific error details

    MULTI-AGENT (isolation is free -- nothing needs to cross a boundary)
      -- Three unrelated customer cases with no shared information

    MULTI-AGENT WITH A CAREFUL, LOSSLESS HAND-OFF (pass specific fields, not free prose)
      -- A research phase whose key findings (a few named facts, not the whole transcript) must reach a writing phase

  This matches exactly what sections 1-3 measured: the technical-to-
  communications hand-off in section 2 needed shared detail and lost
  some of it, exactly the risk this framework flags; section 3's
  three unrelated cases needed nothing shared, exactly where
  multi-agent's isolation was free.

============================================================================
5. WHAT THIS LAB IS AND IS NOT
============================================================================
  REAL: every character count, every regex match, and both drafted
  responses above are genuinely computed -- the missing error code
  in section 2's multi-agent response is a measured consequence of
  what text the summary actually contains, not an asserted claim.

  ILLUSTRATIVE: summarize_for_handoff() is a small, hand-written
  stand-in for a real summarization step -- a real system might use
  a model call to summarize, which could preserve or drop different
  details than this specific example. draft_customer_response()'s
  regex-based extraction stands in for a real generation step.

  NOT SHOWN: how agents actually pass messages to each other in a
  real framework (protocols, message formats); a hand-off design
  that explicitly preserves specific fields rather than relying on
  a free-text summary; and cost/latency comparisons between running
  N agents versus one agent making N tool calls, a natural extension
  left to the exercises.

Done.
```

### 7.3 Reading the result

**Sections 1 and 2 are the same investigation measured twice, and that's what makes the comparison
convincing.** It isn't two different scenarios being compared abstractly; it's identical underlying facts,
handled two different ways, with the size reduction and the information loss shown to be the same
underlying phenomenon viewed from two angles.

**Section 3 is not a weaker version of section 2's split — it's a genuinely different situation.** The
close match between the summed isolated contexts (188) and the combined single context (173) is the tell:
almost nothing was saved or lost by splitting, because there was nothing shared to begin with.

**Section 4's third answer is the one most tempting to skip.** It would be easy to reduce this lesson to "if
information needs to cross a boundary, don't split" — but the research-to-writing case shows that's too
strong a rule. The real distinguishing factor is whether the hand-off is engineered to carry what's needed,
not whether a hand-off exists at all.

---

## 8. Common mistakes and troubleshooting

1. **Treating "smaller context" as a benefit without asking what made it smaller.** §5.2 — a hand-off's
   size reduction is often exactly the information that didn't survive.
2. **Assuming any information crossing an agent boundary rules out splitting.** §5.4, §6 — the fix is
   often a better-engineered hand-off, not abandoning the split.
3. **Relying on free-text summarization for details a later step will definitely need.** §5.4, §6 — a
   specific, structured field is a deliberate design choice a prose summary does not guarantee.
4. **Splitting genuinely independent tasks into one agent out of habit.** §5.3 — this can add unnecessary
   context bloat for cases where isolation would have been free.
5. **Not testing what a downstream agent can actually do with a hand-off missing a specific detail.** §6 —
   the gap is often invisible until a real case surfaces it, exactly as in the worked example.

| Symptom | Likely cause | Fix |
|---|---|---|
| A downstream agent's output is missing a specific detail an upstream agent clearly had | The hand-off between them is a free-text summary that didn't happen to include it | Add an explicit, structured field for that detail rather than relying on summarization, per §5.4, §6 |
| A multi-agent design feels unnecessarily complex for tasks that don't interact | The tasks may be independent enough that a hand-off was never actually needed | Confirm whether any information genuinely needs to cross the boundary, per §5.3 |
| A single agent's context grows uncomfortably large over a long task | Every step's detail is being retained even where a later step doesn't need all of it | Consider whether a specific phase could be split off, with a deliberately-engineered hand-off, per §5.4 |
| Users have to repeat information they already provided earlier in a multi-agent flow | A specific field was dropped by a free-text hand-off between agents | Identify the specific field and pass it explicitly, not through prose summarization, per §6 |

---

## 9. Security, privacy, reliability, cost

- **Reliability.** Identify which specific details a downstream agent will definitely need, and pass them
  as explicit fields rather than trusting a free-text summary to include them (§5.4, §6).
- **Reliability.** Confirm whether tasks are genuinely independent before splitting them into separate
  agents out of habit — unnecessary splitting adds coordination without benefit (§5.3).
- **Cost.** A single agent's context grows with every step, which has a real, measured cost — splitting
  where tasks are genuinely independent avoids this without any hand-off cost at all (§5.3).
- **Reliability.** Test what a downstream agent can actually produce from a hand-off missing a specific
  detail before relying on it in production (§6).

---

## 10. Exercises

### Exercise 1 — Beginner (~20 min)

1. Why did the single-agent response in §7.1 include the specific error code, while the multi-agent
   response in §7.2 did not?
2. What made §7.3's three-way split cost nothing beyond each case's own data size?
3. What are the three outcomes §7.4's framework can recommend, and what distinguishes them?
4. In your own words, why is "smaller context" not automatically a benefit?
5. What was the actual defect in §6's worked example — the split itself, or something else?

### Exercise 2 — Intermediate (~40 min)

1. Run the lab. Confirm §7.1's full response, §7.2's missing error code, and §7.3's near-equal context
   sizes on your own machine.
2. Modify `summarize_for_handoff()` to include the specific error code, and confirm the multi-agent
   response in §7.2 now matches the single-agent response's coverage.
3. Add a fourth, genuinely unrelated case to §7.3 and confirm the isolated-vs-combined size comparison
   still shows no meaningful loss.
4. Using §5.4's framework, design a hand-off for the research-to-writing case that passes 2-3 specific,
   named fields rather than a free-text summary, and explain what each field preserves.
5. Using §6's worked example, identify what specific field(s) the intake-to-resolution hand-off was
   missing, and write the structured hand-off format that would have prevented the incident.

### Exercise 3 — Challenge (~50 min)

1. Design a hand-off format (a small schema, in the style of M8-L05) that explicitly separates "required
   fields a later agent needs" from "free-text summary for context," and apply it to this lesson's
   technical-investigation scenario.
2. Measure the actual token/cost trade-off between running the three-agent split in §7.3 versus one agent
   handling all three cases sequentially, using M8-L07's own timing-measurement approach.
3. Design a test that would have caught §6's missing-account-number bug before it reached production,
   generalizable to any structured field a hand-off is expected to carry.
4. Research (conceptually) how a real multi-agent framework represents message-passing between agents, and
   compare it to this lesson's plain-string hand-offs.
5. Combine this lesson with M8-L08: design a system where an orchestrator dispatches to workers that are
   themselves separate agents (not just functions), and identify what new hand-off risk this introduces at
   the orchestrator-to-worker boundary specifically.

---

## 11. Quiz

*(Answers: [`answer-keys/module-08-answers.md`](../../answer-keys/module-08-answers.md#m8-l09).)*

**Q1.** Per §7.1's measured result, why did the single-agent response include the specific error code?

- A. The full accumulated context still contained the error code, so the drafting step could find and include it.
- B. The error code was hardcoded into draft_customer_response() directly.
- C. The single agent made an additional tool call specifically to look up the error code.
- D. The error code was guessed rather than extracted from context.

**Q2.** Per §7.2's measured result, why did the multi-agent response NOT include the specific error code?

- A. The regex used to extract it was broken.
- B. The communications agent deliberately chose to omit it for brevity.
- C. The communications agent lacked permission to mention error codes.
- D. The error code was never present anywhere in the handoff summary text, so there was nothing for the drafting function to find.

**Q3.** Per §7.2's measured result, what was the size reduction from the full context to the handoff
summary?

- A. There was no measurable size reduction.
- B. Approximately 75% smaller.
- C. The summary was larger than the full context.
- D. Approximately 10% smaller.

**Q4.** Per §7.3's measured result, what did splitting three unrelated cases into three separate agent
contexts cost, compared to one agent handling all three?

- A. It cost significantly more, with major information loss.
- B. It was impossible to measure any difference.
- C. Nothing beyond each case's own raw data size — the combined isolated contexts were close to the size of one shared context.
- D. It cost exactly double the single-agent context size.

**Q5.** Per §5.4's framework, what is the THIRD recommended design, distinct from "single agent" and
"free multi-agent isolation"?

- A. Multi-agent with a carefully engineered hand-off that passes specific, named fields rather than relying on free-text summarization.
- B. Never split tasks under any circumstances.
- C. Always default to a single agent regardless of the situation.
- D. Always default to multi-agent regardless of the situation.

**Q6.** Per §5.4, which framework outcome applies to a research phase whose key findings must reach a
writing phase?

- A. Free multi-agent isolation, since no information needs to cross the boundary.
- B. Single agent only, since any hand-off is too risky to ever use.
- C. No design is possible for this scenario.
- D. Multi-agent with a carefully engineered hand-off, since some specific information must cross but a structured hand-off could preserve it deliberately.

**Q7.** Per §6's worked example, was the intake-to-resolution split itself identified as the defect?

- A. Yes, the two agents should have been merged into one.
- B. No — the split was described as genuinely useful; the defect was relying on free-text summarization instead of a structured field for the account number specifically.
- C. Yes, splitting tasks into multiple agents is always the wrong choice.
- D. The worked example does not address whether the split itself was appropriate.

**Q8.** Per §6, what is the stated general rule this incident illustrates?

- A. Only single-agent designs can ever be reliable.
- B. Multi-agent systems should never pass any information between agents.
- C. A multi-agent split is not itself the defect when information goes missing — the defect is relying on an unstructured summary for details a later agent will definitely need.
- D. The incident has no generalizable lesson beyond this one specific system.

**Q9.** Per §7.5, what does this lesson explicitly NOT cover?

- A. Message-passing protocols between real agents, structured hand-off design, and cost/latency comparisons between N agents and one agent's N tool calls — left as natural extensions.
- B. The single-agent context accumulation demonstrated in section 1.
- C. The multi-agent hand-off demonstrated in section 2.
- D. The three-way framework in section 4.

**Q10.** Per §7.5, is `summarize_for_handoff()` presented as a claim about how all real summarization
systems behave?

- A. Yes, it is presented as universally representative.
- B. The lesson does not address this question.
- C. Yes, it is based on measured data from real summarization systems.
- D. No — it is explicitly described as a small, hand-written stand-in whose specific omissions are this lesson's own illustration, not a general claim.

**Q11.** Per §7.5, is section 3's independent-cases scenario claimed to always produce zero cost
difference in every real system?

- A. Yes, always exactly zero in every case.
- B. No — the lesson measures a specific, near-equal comparison for this example, attributing the small remaining difference to per-case labeling overhead, not claiming a universal zero-cost guarantee.
- C. The lesson does not measure section 3 at all.
- D. Yes, but only for exactly three cases.

**Q12.** What is the general lesson this lab demonstrates about single-agent versus multi-agent designs?

- A. Multi-agent designs are always superior because they reduce context size.
- B. Single-agent designs are always superior because they never lose information.
- C. A single agent's growing context and a multi-agent hand-off's information-loss risk are two real, measurable costs of two different designs, and the right choice depends on whether information must cross a boundary and how carefully that boundary is engineered.
- D. The choice between single-agent and multi-agent designs has no measurable consequences.

**Q13.** *(Written, rubric-graded.)* In under 150 words: your team is deciding whether to split a
data-analysis agent and a report-writing agent into two separate agents. Based on this lesson, what would
you check first, and why?

---

## 12. Revision notes

- **A single agent's context retains everything, because nothing has to cross a boundary** — measured
  directly: a response drafted from full context correctly included a specific error code.
- **A multi-agent hand-off's size reduction is the same fact as its information-loss risk, viewed from two
  angles** — measured directly: a 75% smaller summary, and a response that could not include a detail the
  summary never contained.
- **Genuinely independent tasks make a multi-agent split free** — measured directly: three unrelated
  cases' combined isolated contexts nearly matched one shared context's size, with no information lost.
- **A three-way framework — single agent, free isolation, or a carefully engineered hand-off — fits real
  situations better than a simple "split or don't" binary.**
- **A multi-agent split is not itself the defect when a hand-off loses information** — the defect is
  relying on unstructured summarization for details a later agent will definitely need, when a structured,
  explicit field could have preserved them deliberately.

---

## 13. Completion checklist

- [ ] I can explain why a single agent's context retains detail a multi-agent hand-off might lose.
- [ ] I can identify when splitting tasks into separate agents costs nothing.
- [ ] I can apply the three-way framework (single agent, free isolation, engineered hand-off) to a new
      scenario.
- [ ] I can distinguish a genuine information-loss defect from an unnecessary-split defect in a described
      incident.
- [ ] I design hand-offs with explicit, named fields for details a later agent will definitely need.
- [ ] I check whether tasks are genuinely independent before splitting them into separate agents.
- [ ] I scored 10/13 on the quiz.

---

## 14. References

- Anthropic, *Building Effective Agents* and multi-agent research system engineering posts, on when
  splitting into separate agents is worth its coordination cost, where available. `[UNVERIFIED]`

---

## 15. Next lesson

→ M8-L10 — Human Approval and Escalation

This lesson decided when to split work across agents. Next: when to bring a human into the loop at all,
and how to design the handoff between an agent and a person.
