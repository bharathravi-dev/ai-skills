# M8-L06 — State and Memory in Agents

| | |
|---|---|
| **Lesson ID** | M8-L06 |
| **Difficulty** | 3 (Advanced) |
| **Estimated study time** | 2.0 hours |
| **Prerequisites** | M5-L10 |

---

## 1. Learning objectives

1. **Distinguish** working memory (state within one tool-execution loop run) from persistent memory (state
   that must survive across separate runs).
2. **Demonstrate** that the absence of persistent memory can cause a real, duplicated action.
3. **Explain** why persistent memory scoped by the wrong key can be worse than no persistent memory at all.
4. **Apply** correct scoping — keying a stored fact by every identity that makes it meaningful — to a
   concrete persistent-memory design.
5. **Identify**, from a described incident, whether it reflects missing memory or wrongly-scoped memory.

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **Working memory** | State that exists only for the duration of one tool-execution loop run (M8-L03's `observed`). |
| **Persistent memory** | State that must survive across separate runs, conversations, or sessions. |
| **Scoping** | Choosing which identities a stored fact is keyed by. |
| **Scoping collision** | Two distinct real-world records sharing a key because the key omits an identity that distinguishes them. |
| **Duplicate action** | An action repeated because no memory recorded that it had already happened. |

---

## 3. Plain-language explanation

### 3.1 M8-L03's loop never claimed to remember anything

M8-L03's `observed` dict is created fresh every time `run_tool_loop()` is called and discarded when it
returns — a correct, deliberate design for *working* memory. §7.1 shows what happens when a fact that
*should* survive across separate conversations has nowhere else to live: it doesn't, and a real, measurable
duplicate action results.

### 3.2 The fix isn't inside the loop

§7.2 adds exactly one thing — a persistent record, checked before acting — and the identical loop, called
the same way, now produces the correct outcome. The loop itself never had to change; M8-L03's contract was
never the problem.

### 3.3 Scoped wrong is a different, and sometimes worse, failure

§7.3 reproduces M5-L10's own "remembered the wrong customer" risk in a new shape: a persistent record keyed
by *order id alone* — omitting which customer the order belongs to — correctly protects against one
customer's duplicate refund and, at the exact same time, wrongly blocks a completely different customer's
first, legitimate one.

### 3.4 Three memories, one lesson

§7.4 names all three states that appeared across the lab — correctly-scoped-away working memory, correctly
persistent memory, and wrongly-scoped persistent memory — and states plainly that the third is not merely
*less useful* than the second, but actively produces a wrong outcome the first (no memory at all) would not
have.

---

## 4. Analogy

**A hotel's guest register, kept per-hotel versus kept by room number alone across a whole chain.** A
receptionist who keeps no register at all cannot tell a genuine returning guest from a first-time one — a
real, working inconvenience, but not actively harmful. A receptionist who keeps a register *correctly*, by
guest name and hotel together, remembers exactly the right thing. A chain-wide system that logs bookings by
*room number alone*, across every property, will see "Room 204" used by a guest in one city and refuse to
let a completely different guest book "Room 204" in another city — not because anything is actually
double-booked, but because the record never captured which property the room number belonged to.

### Where the analogy breaks

- **A receptionist can usually tell two different guests apart by looking at them.** §7.3's
  `check_already_refunded_unscoped()` has no such fallback — it consults exactly the key it was given, and
  nothing else, which is what makes the scoping choice itself the entire determinant of correctness.
- **A hotel chain's room numbers are a known, bounded set an administrator could audit for collisions in
  advance.** A real system's identifiers (order ids across merged systems, session ids, user ids) may
  collide in ways nobody anticipated until the collision actually occurs.

---

## 5. Detailed technical explanation

### 5.1 No persistent memory produced a real duplicate

`[REAL, measured]` §7.1 called `run_tool_loop()` twice for the same customer and order, each call getting a
genuinely fresh `observed` dict. **With no persistent record anywhere, both calls issued a refund — a
measured $80.00 paid out against a $40.00 order.** Nothing in this result required a bug in the loop itself;
M8-L03's working-memory contract behaved exactly as designed. The defect was the absence of anything else.

### 5.2 A correctly-scoped record, external to the loop, fixed it

`[REAL, measured]` §7.2 added `REFUND_LOG`, a list living outside any single `run_tool_loop()` call, and
`check_already_refunded()`, keyed by **both** `customer` and `order_id` together. Run against the identical
two-conversation scenario, **the second conversation's check correctly returned `True`, and no second
refund was issued — a measured $40.00 total, matching the order.** The loop function itself was not
modified between §7.1 and §7.2; the fix lived entirely in what the decider could consult.

### 5.3 Scoped wrong produced a different, real failure

`[REAL, measured]` §7.3 used the identical pattern with one change: `check_already_refunded_unscoped()`
checks `order_id` alone. Run against Dana Kim's `O-1001` and then, in a separate conversation, Priya Shah's
*unrelated* `O-1001` (from a different, hypothetical legacy system), **the check for Priya's order returned
`True` — a genuine, never-before-refunded order was wrongly blocked**, because the key it was checked
against carried no information about whose order it actually was. This is M5-L10's own scoping risk,
reproduced with the opposite visible symptom: that lesson's worked example showed wrongly *granted* access
to the wrong customer's data; this lesson shows wrongly *denied* action for a legitimate one — **the same
root cause (a key missing a distinguishing identity) producing different-looking failures depending on what
the check happens to be used for.**

### 5.4 Three memories, three different needs

`[REAL, measured]` §7.4 restates the three states demonstrated: working memory (correctly scoped to nothing
surviving, by M8-L03's own design), correctly-scoped persistent memory (§7.2), and wrongly-scoped persistent
memory (§7.3). **The third is explicitly not framed as merely inferior to the second — §7.3's own measured
result shows it actively causing a wrong outcome that the complete absence of persistent memory (§7.1) would
not have caused**, because §7.1's failure mode (a duplicate refund) and §7.3's failure mode (a wrongly
blocked one) are different, and neither is strictly worse than the other in general — each depends on what
the specific incorrect memory is used to decide.

### 5.5 Assumptions and limitations

- This lesson treats persistent memory as an in-memory Python structure for illustration — a real system's
  persistent memory should physically live in a database, cache, or session store appropriate to how long
  and how reliably it needs to survive.
- Preventing a duplicate action from a *correctly-scoped* check that is itself checked twice in a race
  (two conversations checking simultaneously, both seeing "not yet refunded" before either commits) is
  M8-L12's topic (idempotency), not this lesson's.
- The `LEGACY_ORDERS` id collision is a constructed example illustrating the scoping risk, not a claim about
  how frequently real systems actually reuse identifiers across unrelated systems.

---

## 6. Worked example — the assistant that remembered a decision for the wrong ticket

**The system.** A support agent remembers whether a customer has already been offered a retention discount,
to avoid offering it twice in the same billing dispute. The check is keyed by `discount_type` alone.

**The incident.** A different customer, with a completely unrelated billing dispute, happened to be offered
the *same* `discount_type` ("loyalty-10") as part of a standard, unrelated retention flow. When the first
customer's *actual* repeat contact came in later, the system's check — keyed only by `discount_type` — saw
that "loyalty-10" had already been offered (to the unrelated customer) and refused to offer it again, even
though this customer had never actually received it.

**Why this matches §5.3 exactly.** The check's key (`discount_type` alone) carried no information about
*which customer* the prior offer applied to — structurally identical to §7.3's `order_id`-only key missing
which customer the order belonged to. **The failure is not that memory was missing; it is that the memory
that existed was scoped to the wrong thing.**

**Three defects the incident revealed:**

| # | Defect | Consequence |
|---|---|---|
| 1 | The persistence key (`discount_type`) did not include the customer's identity | Two unrelated customers' unrelated offers collided in the same record |
| 2 | No test exercised two different customers receiving the same discount type | The scoping gap was invisible until two real customers happened to overlap |
| 3 | The failure looked like a policy enforcement working correctly (blocking a "repeat" offer) | The wrongness was not obviously a bug — it looked like the system doing its job |

### The fix

**Key the persistent record by every identity that makes the fact meaningful**, per §5.2 — here, both
`customer_id` and `discount_type` together, exactly as §7.2's `(customer, order_id)` pairing fixed the
original refund scenario.

**Test the scoping specifically with two different identities sharing one otherwise-common value**, per §6
— the same technique §7.3 used deliberately (two different customers, one shared order-id string) to
surface the gap before it reached production.

**The general rule.** **A persistence key is a claim about what makes a stored fact unique — leaving out any
identity that actually distinguishes two real records is not a smaller version of correct scoping, it is a
different, specific bug, and it can fail in either direction: granting what should be denied, or denying
what should be granted.**

---

## 7. Practical activity

**File:** [`labs/m8/l06_state_and_memory.py`](../../labs/m8/l06_state_and_memory.py)

**No API key, no network, no third-party dependencies.** Runs in well under a second.

```bash
source .venv/bin/activate
python labs/m8/l06_state_and_memory.py
```

### 7.2 Expected output

`[EXECUTED]` — 2026-09-10, Python 3.10.11 (pure standard library).

```text
============================================================================
1. NO PERSISTENT MEMORY: TWO SEPARATE CONVERSATIONS, TWO REFUNDS
============================================================================
  Conversation 1 -- Dana Kim asks for a refund on O-1001:
    [step 1] [ACT] issue_refund({'customer': 'Dana Kim', 'order_id': 'O-1001', 'amount': 40.0}) -> [OBSERVE] "refund of $40.00 issued for Dana Kim's order O-1001"
    [step 2] [STOP] respond -- loop stops

  Conversation 2 -- Dana Kim contacts support again about the SAME order:
    [step 1] [ACT] issue_refund({'customer': 'Dana Kim', 'order_id': 'O-1001', 'amount': 40.0}) -> [OBSERVE] "refund of $40.00 issued for Dana Kim's order O-1001"
    [step 2] [STOP] respond -- loop stops

  REFUND_LOG: [('Dana Kim', 'O-1001', 40.0), ('Dana Kim', 'O-1001', 40.0)]
  Total refunded to Dana Kim for O-1001 (a $40.00 order): $80.00

  Each run_tool_loop() call got a genuinely FRESH `observed` dict --
  working memory, by design, does not survive between calls. With
  nothing ELSE remembering that a refund already happened, the second
  conversation had no way to know, and a real double refund resulted.

============================================================================
2. A PERSISTENT, CORRECTLY-SCOPED CHECK FIXES IT
============================================================================
  Conversation 1 -- Dana Kim asks for a refund on O-1001:
    [step 1] [ACT] check_already_refunded({'customer': 'Dana Kim', 'order_id': 'O-1001'}) -> [OBSERVE] False
    [step 2] [ACT] issue_refund({'customer': 'Dana Kim', 'order_id': 'O-1001', 'amount': 40.0}) -> [OBSERVE] "refund of $40.00 issued for Dana Kim's order O-1001"
    [step 3] [STOP] respond -- loop stops

  Conversation 2 -- Dana Kim contacts support again about the SAME order:
    [step 1] [ACT] check_already_refunded({'customer': 'Dana Kim', 'order_id': 'O-1001'}) -> [OBSERVE] True
    [step 2] [STOP] respond -- loop stops

  REFUND_LOG: [('Dana Kim', 'O-1001', 40.0)]
  Total refunded to Dana Kim for O-1001: $40.00 -- correct.

  The SAME two working-memory-only conversations as section 1 now
  produce the correct outcome, because check_already_refunded() reads
  state that persisted across both calls -- the fix was never inside
  run_tool_loop() itself (unchanged from M8-L03), only in what the
  decider could consult before acting.

============================================================================
3. SCOPED WRONG: A DIFFERENT CUSTOMER'S IDENTICAL ORDER ID GETS BLOCKED
============================================================================
  Conversation 1 -- Dana Kim's O-1001 ($40.00, the main system):
    [step 1] [ACT] check_already_refunded({'order_id': 'O-1001'}) -> [OBSERVE] False
    [step 2] [ACT] issue_refund({'customer': 'Dana Kim', 'order_id': 'O-1001', 'amount': 40.0}) -> [OBSERVE] "refund of $40.00 issued for Dana Kim's order O-1001"
    [step 3] [STOP] respond -- loop stops

  Conversation 2 -- Priya Shah's O-1001 ($55.00, an UNRELATED legacy
  system that happens to reuse the same order id string):
    [step 1] [ACT] check_already_refunded({'order_id': 'O-1001'}) -> [OBSERVE] True
    [step 2] [STOP] respond -- loop stops

  BAD_LOG: {'O-1001'}

  Priya Shah's legitimate, never-before-refunded order was BLOCKED --
  check_already_refunded_unscoped() cannot tell her O-1001 apart from
  Dana's, because the key it checks (order_id alone) does not include
  who the order belongs to. This is M5-L10's own worked example ('the
  assistant that remembered the wrong customer'), reproduced here as
  a wrongly BLOCKED action instead of a wrongly GRANTED one -- the
  same root cause, a scoping key missing the identity that actually
  distinguishes two records, produces different-looking symptoms.

============================================================================
4. WORKING MEMORY VS. PERSISTENT MEMORY, SCOPED CORRECTLY
============================================================================
  Three distinct kinds of memory appeared in this lesson:

  WORKING memory (observed, inside one run_tool_loop() call): exists
  only for that call's duration -- section 1 showed this is correctly
  scoped to nothing surviving, by design (M8-L03's own contract).

  PERSISTENT memory, scoped correctly (REFUND_LOG, keyed by BOTH
  customer and order_id together): section 2 showed this is what a
  fact like 'was this specific customer's specific order already
  refunded' actually needs -- surviving across conversations, keyed
  by the full identity that makes the fact meaningful.

  PERSISTENT memory, scoped WRONG (BAD_LOG, keyed by order_id alone):
  section 3 showed this is worse than no persistent memory at all in
  this specific case -- it didn't just fail to help, it actively
  produced an incorrect block for an unrelated customer.

  The general rule this lesson leaves for later ones: deciding WHICH
  facts need persistent memory, and preventing an action from being
  repeated even with a correctly-scoped check racing itself, is
  M8-L12's own topic (idempotency) -- this lesson is about WHERE the
  memory lives and how it must be KEYED, not yet about race conditions
  in checking it.

============================================================================
5. WHAT THIS LAB IS AND IS NOT
============================================================================
  REAL: every REFUND_LOG and BAD_LOG entry above is genuinely
  produced by running run_tool_loop() multiple times against real,
  executed tool functions -- the double refund in section 1 and the
  wrongly-blocked refund in section 3 are measured outcomes of the
  actual code, not asserted claims.

  ILLUSTRATIVE: the deciders in every section are small, scripted
  stand-ins for a real model's choices, and LEGACY_ORDERS' id
  collision is a constructed example, not a claim about how often
  real systems reuse order ids across unrelated systems.

  NOT SHOWN: preventing a duplicate action from a correctly-scoped
  check that is itself checked twice in a race (M8-L12); where
  persistent memory should physically live -- a database, a cache, a
  session store -- which this lesson treats as an in-memory
  illustration only; and human approval as a check independent of
  any stored memory at all (M8-L10).

Done.
```

### 7.3 Reading the result

**Section 1's bug is the easy one to accept, and section 3's is the one worth sitting with.** Missing
memory feels like an obvious gap. Memory that *exists*, is genuinely consulted, and still produces the wrong
answer because of how it's keyed is a subtler, arguably more dangerous failure — nothing about the system
looks broken from the outside; it looks like a check doing exactly its job.

**The loop's own code never changed between any of the three sections.** `run_tool_loop()` in §7.1, §7.2,
and §7.3 is the identical function from M8-L03. Every difference in outcome came from what the decider could
see and how the persistent record it consulted was keyed — confirmation that the defect (and the fix) live
outside the loop's own mechanics entirely.

**Section 3's failure direction is the instructive twist on M5-L10.** That lesson's own worked example
showed a scoping gap *leaking* the wrong customer's data in. This lesson's version shows the same kind of
gap *blocking* the right customer's action out — a reminder that a scoping bug's visible symptom depends
entirely on what the wrongly-shared record is used to decide.

---

## 8. Common mistakes and troubleshooting

1. **Assuming working memory (M8-L03's `observed`) is a substitute for persistent memory.** §5.1 — a fact
   that needs to survive across separate conversations needs somewhere else to live entirely.
2. **Keying a persistent record by only the field that happens to be convenient**, rather than every
   identity that actually distinguishes two real records. §5.3, §6 — the omitted identity is exactly where
   a collision becomes possible.
3. **Assuming persistent memory is strictly better than no persistent memory.** §5.4 — wrongly-scoped memory
   can actively cause a wrong outcome (a false block or a false grant) that no memory at all would not have
   caused.
4. **Testing a persistence key only with distinct values, never with two different real-world records that
   happen to share one field.** §6 — the collision case is exactly what ordinary testing tends to miss.
5. **Treating a system that blocks a repeat-looking action as automatically correct.** §5.3 — a block can be
   the visible symptom of a scoping bug just as easily as an incorrect grant can.

| Symptom | Likely cause | Fix |
|---|---|---|
| The same action is performed more than once across separate conversations for what should be a one-time request | No persistent memory records that the action already happened | Add a persistent, correctly-scoped record checked before acting, per §5.2 |
| A legitimate action is refused, and the system reports it as "already done" when it was not | A persistent check is scoped by a key that omits an identity distinguishing two real records | Re-scope the key to include every identity the fact actually depends on, per §5.3 |
| A bug is hard to reproduce because it only appears when two specific, unrelated records happen to share a field value | The persistence key was never tested against a genuine collision case | Test deliberately with two different identities sharing one common field, per §6 |
| Memory-related bugs keep appearing in different tools with different symptoms | No shared discipline exists for how persistence keys are chosen across the system | Establish and apply one scoping principle (every distinguishing identity, always) project-wide |

---

## 9. Security, privacy, reliability, cost

- **Reliability.** Persist a fact when a working-memory-only loop cannot know it was already established in
  a separate conversation — verified directly by measuring a duplicate action's occurrence without it
  (§5.1).
- **Reliability.** Key every persistent record by every identity that distinguishes one real-world record
  from another, not only the field that happens to be convenient (§5.2, §5.3).
- **Privacy.** A wrongly-scoped record can leak one customer's information or decision into another's
  context (M5-L10's own finding) — correct scoping is a privacy control, not only a correctness one.
- **Cost.** A duplicate action from missing persistent memory has a direct, measurable cost — §7.1's $40
  order became an $80 payout from a single, avoidable gap.

---

## 10. Exercises

### Exercise 1 — Beginner (~20 min)

1. What is the difference between working memory and persistent memory, using this lesson's own terms?
2. Why did section 1's two conversations produce a double refund?
3. What single change fixed section 1's bug in section 2, and where did that change live?
4. Why did section 3's correctly-functioning check still produce a wrong outcome?
5. In your own words, why can wrongly-scoped memory be worse than no memory at all?

### Exercise 2 — Intermediate (~40 min)

1. Run the lab. Confirm the $80 total in §7.1, the $40 total in §7.2, and the wrongly-blocked refund in
   §7.3 on your own machine.
2. Add a third conversation to §7.2's scenario for a different customer and a different order, and confirm
   the correctly-scoped check still behaves correctly for them.
3. Modify §7.3's scenario so the two customers have genuinely different order ids, and confirm the
   incorrect block disappears even with the unscoped check — explain why the bug specifically needs a
   collision to manifest.
4. Design a persistent record for a NEW fact this lesson's domain doesn't yet track (e.g., "has this
   customer been offered a loyalty discount this year") and specify exactly what identities its key needs.
5. Using §5.4's three-memory framework, classify three pieces of state from a system you're familiar with
   as working memory, correctly-scoped persistent memory, or (if you can find one) a real scoping risk.

### Exercise 3 — Challenge (~50 min)

1. Extend REFUND_LOG's check to also account for a time window (e.g., "already refunded in the last 30
   days" rather than "ever"), and explain what new scoping consideration this introduces.
2. Design a test suite entry specifically intended to catch a scoping collision like §7.3's, generalizable
   to any persistent record keyed by more than one field.
3. Using M8-L12's forthcoming topic (idempotency) as motivation, describe a race condition that could still
   cause a duplicate refund even with §7.2's correctly-scoped check in place, and explain why this lesson's
   fix does not address it.
4. Research (conceptually) how a real agent framework or memory system represents scoped, persistent facts
   (e.g., per-user, per-session, per-organization), and compare it to this lesson's tuple-keyed approach.
5. Using §6's worked example, write a one-paragraph design-review comment flagging the discount-type-only
   key before it ships, based specifically on this lesson's scoping principle.

---

## 11. Quiz

*(Answers: [`answer-keys/module-08-answers.md`](../../answer-keys/module-08-answers.md#m8-l06).)*

**Q1.** Per §7.1's measured result, why did two separate conversations both issue a refund for the same
order?

- A. No persistent memory recorded that a refund had already been issued, and each conversation's working memory started fresh.
- B. run_tool_loop() itself contains a bug that duplicates tool calls.
- C. The order amount was defined incorrectly.
- D. The second conversation used a different order id by mistake.

**Q2.** Per §7.2's measured result, what specifically changed between section 1 and section 2 that fixed
the duplicate-refund bug?

- A. run_tool_loop() was modified to remember previous calls.
- B. The order amount was reduced.
- C. The customer was asked to confirm before each refund.
- D. A persistent, correctly-scoped check (by both customer and order_id) was added and consulted before acting; the loop itself was unmodified.

**Q3.** Per §7.3's measured result, why was Priya Shah's legitimate refund request wrongly blocked?

- A. Priya Shah had actually already received a refund for that order.
- B. The check was scoped by order_id alone, so it could not distinguish her order from Dana Kim's unrelated order sharing the same id string.
- C. The loop reached max_steps before her refund could be processed.
- D. Priya Shah's order amount exceeded a policy cap.

**Q4.** Per §5.3, how does section 3's failure relate to M5-L10's own worked example ("the assistant that
remembered the wrong customer")?

- A. It is unrelated — a completely different class of bug.
- B. It only applies to conversations that never use persistent memory at all.
- C. It is the identical root cause (a scoping key missing a distinguishing identity), but producing the opposite visible symptom: a wrongly blocked action instead of a wrongly granted one.
- D. It shows that persistent memory should never be used for refunds specifically.

**Q5.** Per §5.4, is wrongly-scoped persistent memory (section 3) framed as simply "less useful" than
correctly-scoped persistent memory (section 2)?

- A. No — the lesson states it can actively produce a wrong outcome that no persistent memory at all would not have caused.
- B. Yes — it is described as strictly better than no memory, just less optimal.
- C. Yes — the two are described as functionally equivalent in every case.
- D. The lesson does not compare the two directly.

**Q6.** Per §7.4, what distinguishes working memory (M8-L03's `observed`) from persistent memory in this
lesson's own terms?

- A. Working memory is always stored in a database; persistent memory never is.
- B. Persistent memory is always scoped correctly by definition.
- C. There is no meaningful distinction between the two.
- D. Working memory exists only for one run_tool_loop() call's duration; persistent memory must survive across separate calls.

**Q7.** Per §6's worked example, what was structurally identical between the discount-type incident and
section 3's order-id collision?

- A. Both incidents involved the same specific customers.
- B. Both keys omitted the customer identity that would have distinguished two unrelated records, causing a false match.
- C. Neither incident involved any persistent memory at all.
- D. Both incidents were caused by a bug inside run_tool_loop() itself.

**Q8.** Per §6, what specific testing technique is proposed to catch a scoping bug like this before it
reaches production?

- A. Testing only with values that are guaranteed to be unique across the whole system.
- B. Removing all persistent memory checks to avoid the risk entirely.
- C. Deliberately testing with two different real-world identities that happen to share one common field value.
- D. Testing only with a single customer's data repeated many times.

**Q9.** Per §5.5, what does this lesson explicitly leave to M8-L12 (idempotency)?

- A. Preventing a duplicate action from a correctly-scoped check that is itself checked twice in a race condition.
- B. Everything about persistent memory, which this lesson does not address at all.
- C. The difference between working and persistent memory.
- D. How to choose which fields belong in a persistence key.

**Q10.** Per §7.5, is `LEGACY_ORDERS`'s order-id collision presented as a claim about how often real
systems actually reuse identifiers?

- A. Yes, it is presented as a statistically common occurrence.
- B. The lesson does not address this question.
- C. Yes, it is based on real, measured industry data.
- D. No — it is explicitly described as a constructed example illustrating the scoping risk, not a frequency claim.

**Q11.** Per §7.5, what does this lesson explicitly NOT cover?

- A. The distinction between working and persistent memory demonstrated in sections 1 and 4.
- B. Preventing duplicate actions from race conditions in a correctly-scoped check, and where persistent memory should physically live — left to M8-L12 and treated as illustration-only here, respectively.
- C. The correctly-scoped fix demonstrated in section 2.
- D. The wrongly-scoped failure demonstrated in section 3.

**Q12.** What is the general lesson this lab demonstrates about state and memory in agents?

- A. Persistent memory should always be preferred over working memory in every situation.
- B. Working memory (M8-L03's observed dict) should be made to survive across separate conversations by default.
- C. An agent needs persistent, correctly-scoped memory for facts that must survive across separate conversations — and a memory record scoped by the wrong key can be as harmful as, or more harmful than, having no persistent memory at all.
- D. Scoping a persistent record correctly is only a performance concern, not a correctness one.

**Q13.** *(Written, rubric-graded.)* In under 150 words: your team is adding a persistent record so an
agent remembers which support tickets it has already escalated, to avoid escalating the same ticket twice.
Based on this lesson, what would you check about how this record is keyed, and why?

---

## 12. Revision notes

- **Working memory (M8-L03's `observed`) correctly does not survive across separate loop runs** — the
  absence of persistent memory to fill that gap produced a real, measured duplicate refund ($80 for a $40
  order).
- **A persistent record, checked before acting and scoped by every identity a fact depends on, fixes a
  duplicate-action bug without any change to the loop itself.**
- **A persistent record scoped by only one identity can wrongly treat two distinct real-world records as
  the same one** — measured directly: an order-id-only key wrongly blocked a different customer's
  legitimate, never-before-refunded order.
- **Wrongly-scoped memory is not simply "less good" than correctly-scoped memory** — it can actively cause
  a wrong outcome (a false block or a false grant) that no persistent memory at all would not have caused.
- **The same root cause — a key omitting a distinguishing identity — can produce opposite-looking symptoms**
  depending on what the record is used to decide: M5-L10's own example leaked data in; this lesson's example
  blocked a legitimate action out.

---

## 13. Completion checklist

- [ ] I can distinguish working memory from persistent memory using this lesson's own terms.
- [ ] I can explain why missing persistent memory caused a real duplicate action.
- [ ] I can explain why a persistent record scoped by the wrong key can be worse than no persistent memory.
- [ ] I can design a persistence key that includes every identity a stored fact actually depends on.
- [ ] I can identify, from a described incident, whether it reflects missing memory or wrongly-scoped
      memory.
- [ ] I test a persistence key deliberately against two different real-world identities sharing one field.
- [ ] I scored 10/13 on the quiz.

---

## 14. References

- M5-L10's own "the assistant that remembered the wrong customer" worked example, extended directly in this
  lesson's §6 and §7.3. `[STABLE]`
- Anthropic, agent memory and context management documentation, where available. `[UNVERIFIED]`

---

## 15. Next lesson

→ M8-L07 — Routing, Chaining and Parallel Execution

This lesson covered what an agent remembers across separate runs. Next: how multiple steps within a single
run can be arranged — routed to different paths, chained together, or run in parallel — and what each
arrangement actually buys.
