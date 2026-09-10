# M8-L05 — Tool Schemas and Argument Validation

| | |
|---|---|
| **Lesson ID** | M8-L05 |
| **Difficulty** | 2 (Intermediate) |
| **Estimated study time** | 2.0 hours |
| **Prerequisites** | M5-L06, [M8-L03](M8-L03-tool-execution-loop.md) |

---

## 1. Learning objectives

1. **Apply** M5-L06's schema-validation principle to tool-call arguments specifically, not only to
   structured output text.
2. **Extend** M8-L03's tool-execution loop with a third general failure category: recognized tool,
   invalid arguments.
3. **Demonstrate** that a schema catches wrong types, out-of-bounds values, and undeclared fields before a
   tool function ever runs.
4. **Apply** M5-L08's absent-parameter defense to a tool's argument schema, not just to its own internal
   logic.
5. **Explain** why gating arguments before a tool call is a different, earlier checkpoint than gating a
   value computed inside the tool (M8-L02).

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **Tool schema** | A declared shape (types, bounds, allowed fields) that a tool's arguments must satisfy. |
| **Argument validation** | Checking proposed tool-call arguments against a schema before invoking the tool. |
| **Absent-parameter defense** | Designing a schema so a dangerous field does not exist, rather than validating its value (M5-L08). |
| **Undeclared field** | An argument present in a proposed call but not defined anywhere in the tool's schema. |
| **Validation gate** | The point in a loop where arguments are checked before the corresponding action executes. |

---

## 3. Plain-language explanation

### 3.1 M5-L06 validated output text; this lesson validates tool arguments

M5-L06 built a schema to catch a model's structured JSON output going wrong in ways no instruction could
prevent. A tool call's arguments are exactly that same kind of output, arriving through a different channel
— M8-L03's `(action_name, action_args)` pair instead of a JSON blob. §7.2–§7.3 apply the identical principle
there.

### 3.2 A schema catches three things instructions can't

§7.2 runs three malformed argument proposals directly through a schema: a wrong type, an out-of-bounds
value, and a field the schema never declared. All three are rejected — not because any of them "look"
dangerous in isolation, but because each fails a specific, checkable property the schema encodes.

### 3.3 The loop needed a real extension, not just a new scenario

Unlike M8-L04, which reused M8-L03's loop completely unmodified, §7.3 genuinely adds a new branch to
`run_tool_loop()` — a validation step, positioned before the tool call. This is an honest extension: the
original loop had no concept of "arguments can be wrong independent of the tool name being right," and this
lesson's capability didn't exist without adding it.

### 3.4 Where the gate sits changes what it protects

§7.4 draws the contrast with M8-L02 directly: M8-L02 gated a *computed* value from inside a tool's own logic,
after deciding what to do. This lesson gates the *proposed arguments* before the tool function is invoked at
all — a step earlier, and one that means the tool's own code never has to defend against malformed input
reaching it in the first place.

---

## 4. Analogy

**A bouncer checking IDs at the door, not a manager checking receipts after last call.** A venue could, in
principle, let everyone in and have staff periodically walk the floor checking IDs, ejecting anyone found to
be underage after the fact — enforcement happens, but only after the person is already inside, possibly
having already ordered a drink. A bouncer at the door checks the ID *before* anyone crosses the threshold —
the same rule, enforced at an earlier point, meaning nothing downstream (bartenders, the register, the
dance floor) ever has to handle a case that should never have gotten that far. A tool schema is the bouncer;
a value check written inside the tool's own logic is the manager doing rounds.

### Where the analogy breaks

- **A bouncer's ID check is binary — old enough or not.** A schema check has more shapes (type, bounds,
  field presence), each catching a genuinely different kind of malformed input, not one uniform check.
- **A person turned away at the door can argue their case.** §7.3's rejected calls get no negotiation — an
  `ArgValidationError` is unconditional; only a retry with genuinely corrected arguments succeeds.

---

## 5. Detailed technical explanation

### 5.1 Three catches, demonstrated directly

`[REAL, measured]` §7.2 ran `validate_args()` against three proposals for `issue_refund`: `amount="forty
dollars"` (wrong type), `amount=50000.0` (exceeds the schema's `le=500.0` bound), and a call including
`approved_by="admin"` (a field the schema never declared). **All three were genuinely rejected, each with a
distinct, specific error message naming exactly what failed** — not a single generic "invalid input"
response.

### 5.2 A new, general failure category, not a special case

`[REAL, measured]` §7.3 wired `REFUND_SCHEMA` into an extended `run_tool_loop()` and ran a scripted decider
proposing the same three malformed calls, followed by a valid one. **All three rejections used the identical
`[VALIDATE]` branch** — no scenario-specific handling exists for "wrong type" versus "out of bounds" versus
"undeclared field"; all three are instances of one general check. The loop recovered and completed the
refund on the fourth, valid attempt, exactly matching M8-L03's own "error becomes an observation, not a
crash" pattern, now extended to a third failure type.

### 5.3 The undeclared-field rejection is the absent-parameter defense, applied to arguments

`[REAL, measured]` The `approved_by="admin"` proposal was rejected **not because its value was inspected and
judged suspicious, but because the schema never declared such a field could exist at all.** This is M5-L08's
"no prompt, however persuasive, can set a field that does not exist" principle, applied here to a tool's
argument schema rather than to a structured-output model — the mechanism is identical, only the channel
differs.

### 5.4 An earlier gate changes what downstream code has to assume

`[REAL reasoning]` §7.4 contrasts this lesson's checkpoint with M8-L02's: M8-L02's `gated_refund()` computed
and bounded a dollar amount *inside* the tool's own logic, after the tool had already been invoked. This
lesson's schema validation happens *before* `issue_refund()` is ever called — **a wrong-type or
out-of-bounds argument never reaches a single line of the tool's own code.** This means a tool's internal
logic can be written assuming its arguments are already well-formed, rather than re-implementing type and
bounds checks itself.

### 5.5 Assumptions and limitations

- `validate_args()` is a small, hand-written reimplementation of M5-L06's Pydantic-based approach, built to
  stay dependency-free — a real system should prefer a maintained schema library, not a hand-rolled
  validator.
- This lesson does not cover nested or cross-field validation (a rule spanning two arguments together),
  M5-L06's lax-versus-strict coercion distinction (fully applicable to tool arguments too, just not
  re-demonstrated here), or how many correction attempts a model gets before a loop gives up (M8-L13).
- `make_scripted_decider()` stands in for a real model receiving each rejection's error message as its next
  observation and retrying — a real system would show the model the actual validation error, not follow a
  fixed script.

---

## 6. Worked example — the tool that trusted its caller

**The system.** A team builds an internal `update_user_role` tool for an agent that handles account
administration requests. The tool's own code reads `new_role` and applies it directly to the user record,
trusting that anything reaching the function is already a valid role.

**The incident.** A conversation that involved retrieved, untrusted text (a support ticket quoting a user's
own message) led the model to propose `update_user_role(user_id="u-2210", new_role="superadmin")` —
`"superadmin"` was not one of the three roles the system actually supported (`"member"`, `"admin"`,
`"owner"`), but the tool's own code did no validation, assumed the string was one of the valid three, and
stored it as-is. The account now had a role string the rest of the system had never been designed to
handle.

**Why this matches §5.2 exactly.** No schema was ever wired into this tool's call path — there was no
`[VALIDATE]` gate at all, only whatever the tool's own code happened to check (in this case, nothing). Per
§5.1, a `new_role` value outside the three legitimate options is exactly the kind of thing an `Enum`-style
schema constraint rejects immediately, the same way §7.2's out-of-bounds refund amount was rejected before
`issue_refund()` ever ran.

**Three defects the incident revealed:**

| # | Defect | Consequence |
|---|---|---|
| 1 | No schema validated `new_role` against the three legitimate values | An arbitrary string was accepted and stored as a user's role |
| 2 | The tool's own code assumed well-formed input rather than checking it | The invalid role reached storage with no rejection anywhere in the path |
| 3 | The dangerous value arrived via a channel (retrieved ticket text) the team hadn't specifically tested | The gap was invisible until a real conversation happened to trigger it |

### The fix

**Add an enum-style schema constraint on `new_role`**, per §5.1 — restricting it to exactly the three
legitimate values, rejecting anything else before the tool function runs.

**Move the check to the loop's validation gate, not the tool's own code**, per §5.4 — so every tool sharing
this pattern benefits from the same general `[VALIDATE]` branch, rather than each tool needing to
reimplement its own ad hoc checks.

**The general rule.** **A tool that trusts its own caller's arguments to already be well-formed is only as
safe as every possible path that could produce those arguments — a schema gate makes that assumption
unnecessary, checking the arguments themselves rather than trying to anticipate every route they might
arrive by.**

---

## 7. Practical activity

**File:** [`labs/m8/l05_tool_schemas_argument_validation.py`](../../labs/m8/l05_tool_schemas_argument_validation.py)

**No API key, no network, no third-party dependencies.** Runs in well under a second.

```bash
source .venv/bin/activate
python labs/m8/l05_tool_schemas_argument_validation.py
```

### 7.2 Expected output

`[EXECUTED]` — 2026-09-10, Python 3.10.11 (pure standard library).

```text
============================================================================
1. THREE THINGS NO AMOUNT OF PROMPTING CAN GUARANTEE
============================================================================
  M5-L06's own finding, restated for tool arguments specifically: an
  instruction can ASK a model to pass a valid order id, a reasonable
  amount, and nothing extra -- a schema REFUSES anything that
  doesn't comply, regardless of how the model was asked. Section 2
  runs this loop's schema against three malformed proposals directly.

============================================================================
2. THREE MALFORMED PROPOSALS, VALIDATED DIRECTLY
============================================================================
  wrong type         {'order_id': 'O-1001', 'amount': 'forty dollars', 'reason': 'damaged'}
    -> REJECTED: 'amount' must be float, got str ('forty dollars')
  out of bounds      {'order_id': 'O-1001', 'amount': 50000.0, 'reason': 'damaged'}
    -> REJECTED: 'amount'=50000.0 exceeds maximum 500.0
  undeclared field   {'order_id': 'O-1001', 'amount': 40.0, 'reason': 'damaged', 'approved_by': 'admin'}
    -> REJECTED: unexpected argument(s) not in schema: ['approved_by']

  Each rejection happened before issue_refund() was ever called --
  the wrong-type amount never reached a float comparison inside the
  function (which would have crashed or misbehaved); the out-of-
  bounds amount never reached the business logic at all; and
  'approved_by' was rejected NOT because its value looked suspicious,
  but because the schema never declared such a field could exist --
  M5-L08's exact absent-parameter defense, applied here to args.

============================================================================
3. THE SAME THREE CATCHES, NOW INSIDE THE LOOP
============================================================================
  Running the loop with REFUND_SCHEMA wired in:

  [step 1] [VALIDATE] issue_refund({'order_id': 'O-1001', 'amount': 'forty dollars', 'reason': 'damaged'}) REJECTED: 'amount' must be float, got str ('forty dollars')
  [step 2] [VALIDATE] issue_refund({'order_id': 'O-1001', 'amount': 50000.0, 'reason': 'damaged'}) REJECTED: 'amount'=50000.0 exceeds maximum 500.0
  [step 3] [VALIDATE] issue_refund({'order_id': 'O-1001', 'amount': 40.0, 'reason': 'damaged', 'approved_by': 'admin'}) REJECTED: unexpected argument(s) not in schema: ['approved_by']
  [step 4] [ACT] issue_refund({'order_id': 'O-1001', 'amount': 40.0, 'reason': 'damaged'}) -> [OBSERVE] 'refund of $40.00 issued for O-1001 (damaged)'
  [step 5] [STOP] respond -- loop stops

  Three rejections, one success, zero crashes -- every rejection
  used the SAME general [VALIDATE] branch in run_tool_loop(), not
  three separate special cases. This is the loop's THIRD failure
  category, alongside M8-L03's unknown-tool and raised-exception
  handling: recognized tool, invalid arguments.

============================================================================
4. WHERE THE GATE SITS MATTERS: BEFORE THE CALL, NOT INSIDE IT
============================================================================
  M8-L02's gated_refund() validated a COMPUTED amount from inside the
  tool's own logic, after deciding what to charge. This lesson's
  schema validates the PROPOSED arguments before the tool function
  is invoked AT ALL -- a step earlier. For issue_refund() specifically,
  that means a wrong-type amount never reaches a single line of the
  function's own code, including any bounds-checking that function
  might otherwise need to duplicate. The schema is where the
  well-formedness check belongs; the tool's own logic is free to
  assume its arguments are already valid by the time it runs.

============================================================================
5. WHAT THIS LAB IS AND IS NOT
============================================================================
  REAL: validate_args() is a genuine, executed type/bounds/field
  checker -- every rejection in sections 2 and 3 is a real raised
  ArgValidationError, caught by real except blocks, not a scripted
  narrative. The final successful refund in section 3 is a real
  call to issue_refund() with validated arguments.

  ILLUSTRATIVE: make_scripted_decider() stands in for a real model
  across several attempts or turns -- a real system would show each
  rejection's error message to the model as its next observation and
  let it try again, not follow a fixed script. validate_args() is a
  small, hand-written reimplementation of M5-L06's Pydantic-based
  approach, built here to stay dependency-free -- a real system
  should prefer a maintained schema library over a hand-rolled one.

  NOT SHOWN: nested or cross-field validation (e.g., a rule spanning
  two arguments together); coercion policy (M5-L06's lax-vs-strict
  distinction, fully applicable here too); and retry/backoff
  strategies for how many correction attempts a model gets before
  the loop gives up (M8-L13's own topic).

Done.
```

### 7.3 Reading the result

**Section 2 and section 3 show the same three rejections at two different levels.** Section 2 proves the
validator itself works correctly, in isolation. Section 3 proves it works identically once wired into the
actual loop a real system would run — the same three error messages, produced the same way, inside a
realistic multi-step conversation.

**The absence of `approved_by` from `REFUND_SCHEMA` is doing real work, not just filling in a table.**
Nothing in `validate_args()` specifically watches for that field name — it's rejected by the same generic
"is this key in the schema" check that would reject any other undeclared field, which is exactly the point:
the defense is structural, not a special case written to catch that one attack.

**Section 4's contrast with M8-L02 is worth sitting with.** Two different lessons gated two different kinds
of value — a *computed* result, and *proposed* arguments — at two different points in a call's lifecycle.
Neither replaces the other; a real system typically needs both.

---

## 8. Common mistakes and troubleshooting

1. **Writing type or bounds checks inside a tool's own function body instead of in a schema.** §5.4 — this
   duplicates logic across every tool that needs similar checks, and the tool still has to handle malformed
   input reaching it in the first place.
2. **Validating a field's value without asking whether the field should exist at all.** §5.3 — an absent
   field is a stronger defense than a validated one, per M5-L08.
3. **Treating argument validation as a special case for "dangerous" tools only.** §5.2 — the same general
   `[VALIDATE]` mechanism benefits any tool with a schema, not just high-stakes ones.
4. **Assuming a schema check that happens somewhere in the system is enough**, without confirming it happens
   *before* the tool function runs. §5.4 — a check performed after the fact protects less than one performed
   before.
5. **Writing a bespoke rejection message or handling path for each specific malformed-argument case.** §5.2
   — a schema-driven approach handles new malformed cases (a different wrong type, a different undeclared
   field) without new code.

| Symptom | Likely cause | Fix |
|---|---|---|
| A tool call crashes with a TypeError or similar inside the tool's own code | No schema validates argument types before the call | Add a type-checked schema and a validation gate before invocation, per §5.2 |
| An unexpected field ends up influencing behavior downstream of a tool call | The tool's schema (or the tool itself) accepts fields it never explicitly declared | Reject undeclared fields explicitly, per §5.3's absent-parameter defense |
| A tool receives a value technically the right type but nonsensical (too large, empty, wrong format) | The schema checks type but not bounds, length, or pattern | Add ge/le, min/max length, or prefix/pattern constraints, per §7.2 |
| Similar validation logic is duplicated across several tools' own code | No shared, general validation gate exists in the loop itself | Move validation into the loop as a general step, per §5.2, rather than per-tool code |

---

## 9. Security, privacy, reliability, cost

- **Security.** Prefer an absent-parameter defense over a validated one wherever possible — a field that
  does not exist in the schema cannot be set by anything, however persuasively argued for (§5.3, M5-L08).
- **Security.** Validate tool arguments before the tool function runs, not inside it — an earlier gate means
  the tool's own code never has to defend against malformed input reaching it (§5.4).
- **Reliability.** Use one general validation mechanism for all tools with schemas, not bespoke handling per
  tool — new malformed-argument cases are caught automatically, without new code (§5.2).
- **Cost.** A rejected, malformed tool call costs a validation check; an unvalidated one that reaches a real
  side-effecting tool (a refund, a role change) can cost far more to undo, if it can be undone at all (§6).

---

## 10. Exercises

### Exercise 1 — Beginner (~20 min)

1. What three kinds of malformed arguments does `validate_args()` catch in this lesson?
2. Why was the `approved_by` field rejected, specifically?
3. What new branch did `run_tool_loop()` need, compared to M8-L03's original version?
4. In your own words, how does this lesson's validation gate differ from M8-L02's gated amount check?
5. Why is an absent field considered a stronger defense than a validated one?

### Exercise 2 — Intermediate (~40 min)

1. Run the lab. Confirm all three rejections and the final successful refund in §7.3 on your own machine.
2. Add a fourth malformed proposal (your own choice: an empty `reason`, an `order_id` missing the `"O-"`
   prefix, or a `reason` exceeding the max length) and confirm the loop catches it via the same `[VALIDATE]`
   branch.
3. Add a second tool with its own schema to `REFUND_TOOLS` and confirm the validation gate works correctly
   for both tools using the same `schemas` dict.
4. Remove `REFUND_SCHEMA` from the `run_tool_loop()` call entirely and re-run §7.3's scripted decider. What
   happens to the wrong-type `amount` proposal now, and why?
5. Using M5-L06's lax-vs-strict distinction, decide whether `validate_args()` in its current form behaves
   more like lax or strict mode, and explain your reasoning with a specific example from the code.

### Exercise 3 — Challenge (~50 min)

1. Extend `ArgSpec` and `validate_args()` to support a cross-field rule (e.g., a `discount_amount` argument
   that must not exceed a separately-provided `order_total` argument), and test it against a case that
   should fail.
2. Using §6's worked example, design the schema constraint that would have caught the `new_role="superadmin"`
   incident, and write the corresponding `ArgSpec` for it.
3. Research (conceptually) how a real tool-calling API (from any major provider) represents argument schemas
   for the model, and compare its structure to this lesson's hand-written `ArgSpec`.
4. Design a policy for how many validation rejections a single tool call gets before the loop gives up
   entirely (rather than retrying indefinitely), and explain how it should interact with M8-L03's
   `max_steps` bound.
5. Using M5-L06's coercion-visibility principle ("a validator that converts *and records that it
   converted*"), extend `validate_args()` to log a warning when it silently accepts a borderline value,
   rather than rejecting or accepting it silently.

---

## 11. Quiz

*(Answers: [`answer-keys/module-08-answers.md`](../../answer-keys/module-08-answers.md#m8-l05).)*

**Q1.** Per §7.2's measured result, why was `amount="forty dollars"` rejected?

- A. Because the schema requires `amount` to be a float, and a string was provided instead.
- B. Because "forty dollars" exceeded the maximum allowed length for a string.
- C. Because the order_id in that proposal was invalid.
- D. Because the reason field was empty.

**Q2.** Per §7.2's measured result, why was `amount=50000.0` rejected even though it is a valid float?

- A. It is not a valid float type.
- B. The order_id was missing the required prefix.
- C. It contains an undeclared field.
- D. It exceeds the schema's declared maximum of 500.0.

**Q3.** Per §7.2 and §5.3, why specifically was the `approved_by="admin"` proposal rejected?

- A. Because the value "admin" failed a bounds check.
- B. Because the schema never declared an `approved_by` field at all, regardless of what value it held.
- C. Because "admin" is not a valid string type.
- D. Because the order_id in that proposal was invalid.

**Q4.** Per §7.3's measured result, how many distinct code branches in `run_tool_loop()` were used to
handle the three different kinds of rejected proposals?

- A. Three separate branches, one per malformed-argument type.
- B. Zero — the rejections were handled outside run_tool_loop() entirely.
- C. One shared `[VALIDATE]` branch, used identically for all three rejection types.
- D. Four branches, one per proposal plus one for the final success.

**Q5.** Per §7.3's measured result, what happened after the three rejections in the scripted sequence?

- A. A fourth, valid proposal was accepted, and issue_refund() was genuinely called and returned a result.
- B. The loop terminated after the third rejection without ever completing the refund.
- C. The loop reached max_steps before any valid proposal was attempted.
- D. The same invalid proposal was retried automatically without any change.

**Q6.** Per §5.4, how does this lesson's validation gate differ from M8-L02's `gated_refund()` amount
check?

- A. They are functionally identical mechanisms applied to the same checkpoint.
- B. Neither mechanism actually prevents any specific failure.
- C. M8-L02's gate ran before the tool call; this lesson's gate runs only after.
- D. This lesson's gate validates proposed arguments before the tool function runs; M8-L02's gate validated a computed value from inside the tool's own logic, after the fact.

**Q7.** Per §5.4, what is a consequence of validating arguments before the tool function runs, rather than
inside it?

- A. The tool's own code must still perform all the same checks redundantly.
- B. The tool's own code can assume its arguments are already well-formed, rather than needing to re-implement type and bounds checks itself.
- C. It has no effect on what the tool's own code needs to assume.
- D. It makes the tool function itself unnecessary.

**Q8.** Per §6's worked example, what was the root defect that allowed `new_role="superadmin"` to be
stored?

- A. The tool's own code explicitly permitted the value "superadmin".
- B. The user_id argument was invalid.
- C. No schema validated new_role against the legitimate set of values, and the tool's own code assumed well-formed input with no check of its own.
- D. The tool crashed and stored a default value instead.

**Q9.** Per §6, what is the stated general fix for the kind of gap the `new_role` incident revealed?

- A. Add an enum-style schema constraint restricting new_role to its legitimate values, checked before the tool function runs.
- B. Remove the update_user_role tool entirely.
- C. Add logging so the bad value can be found after the fact.
- D. Ask the model more firmly to only use valid role names.

**Q10.** Per §7.5, why is `validate_args()` described as a reimplementation rather than a recommendation
for production use?

- A. Because it does not actually work correctly.
- B. Because it cannot catch any of the three failure categories this lesson demonstrates.
- C. Because it is slower than checking arguments manually inside each tool.
- D. Because a real system should prefer a maintained schema library (such as M5-L06's pydantic) over a small, hand-rolled validator built here to stay dependency-free.

**Q11.** Per §7.5, what does this lesson explicitly NOT cover?

- A. The three malformed-argument catches demonstrated in section 2.
- B. Cross-field validation, coercion policy, and retry/backoff strategy for correction attempts — left to a later exercise or to M8-L13.
- C. The validation gate integrated into the loop in section 3.
- D. The contrast with M8-L02's gating approach in section 4.

**Q12.** What is the general lesson this lab demonstrates about tool-call arguments?

- A. Tool arguments never need validation as long as the tool's own code is carefully written.
- B. Only high-stakes tools need argument validation; low-stakes tools can trust their input.
- C. Validating tool-call arguments against a schema — including rejecting undeclared fields — is a general, reusable gate that catches malformed input before it reaches a tool's own logic, extending both M5-L06's schema principle and M8-L03's general error-handling categories.
- D. Argument validation and computed-value gating (M8-L02) serve the identical purpose and only one is ever needed.

**Q13.** *(Written, rubric-graded.)* In under 150 words: a new tool is being added to your team's agent
that deletes a file given a file path argument. Based on this lesson, what would you check the schema for
specifically, and why?

---

## 12. Revision notes

- **A schema catches wrong types, out-of-bounds values, and undeclared fields in tool-call arguments**,
  extending M5-L06's structured-output principle to a different channel — measured directly across three
  distinct rejection types.
- **An undeclared field is rejected because the schema never defined it, not because its value was
  inspected and judged suspicious** — M5-L08's absent-parameter defense, applied to tool arguments.
- **M8-L03's loop needed a genuine third branch — `[VALIDATE]` — to add this capability**, unlike M8-L04's
  variants, which reused the loop unmodified; validation is a capability the original loop did not have.
- **Gating arguments before a tool call is an earlier checkpoint than gating a computed value inside the
  tool (M8-L02)** — a wrong-type or out-of-bounds argument never reaches a single line of the tool's own
  code when validated first.
- **A tool that trusts its arguments to already be well-formed is only as safe as every path that could
  produce them** — a schema gate removes the need to anticipate every such path.

---

## 13. Completion checklist

- [ ] I can name the three kinds of malformed arguments this lesson's schema catches.
- [ ] I can explain why an absent field is a stronger defense than a validated one.
- [ ] I can explain what new capability `run_tool_loop()` needed to add for this lesson, compared to
      M8-L03.
- [ ] I can distinguish this lesson's argument-validation gate from M8-L02's computed-value gate.
- [ ] I can identify a tool argument that should be schema-validated, and design the specific constraint
      for it.
- [ ] I design tool schemas to omit dangerous fields entirely, not just validate their values.
- [ ] I scored 10/13 on the quiz.

---

## 14. References

- M5-L06's own schema-validation principle ("an instruction asks, a schema refuses"), applied directly
  throughout this lesson. `[STABLE]`
- M5-L08's absent-parameter defense, applied directly to tool argument schemas. `[STABLE]`
- Anthropic, tool-use / function-calling schema documentation, where available. `[UNVERIFIED]`

---

## 15. Next lesson

→ M8-L06 — State and Memory in Agents

This lesson validated a single tool call's arguments in isolation. Next: what an agent needs to remember
across many calls and many turns, and where that memory actually lives.
