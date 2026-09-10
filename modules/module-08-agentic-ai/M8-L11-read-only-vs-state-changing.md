# M8-L11 — Read-Only vs State-Changing Actions

| | |
|---|---|
| **Lesson ID** | M8-L11 |
| **Difficulty** | 2 (Intermediate) |
| **Estimated study time** | 1.5 hours |
| **Prerequisites** | [M8-L10](M8-L10-human-approval-escalation.md) |

---

## 1. Learning objectives

1. **Distinguish** a read-only action (no side effect on the world) from a state-changing one (a real
   effect every time it runs), and verify the distinction empirically rather than by label alone.
2. **Demonstrate** that retrying a read-only action after a suspected failure is free, while retrying a
   state-changing action without a safeguard repeats its real effect.
3. **Explain** why speculative, exploratory calls are safe for read-only actions and never safe for
   state-changing ones.
4. **Distinguish** two different kinds of state-changing action — one that happens to look unchanged when
   repeated with identical arguments, and one that accumulates a new effect every time.
5. **Identify**, from a tool's declared classification, whether that classification has actually been
   verified against its real behavior.

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **Read-only action** | An action with no side effect on the world beyond returning a value. |
| **State-changing action** | An action that has a real effect on the world every time it runs. |
| **Declared classification** | A tag assigned to a tool by whoever registers it, not automatically verified. |
| **Speculative call** | Calling an action just to see its result, without committing to act on it. |
| **Side effect** | Any change to the world beyond a function's return value. |

---

## 3. Plain-language explanation

### 3.1 M8-L10 decided who approves; this lesson decides what needs approval at all

M8-L10 built a tiered policy for routing actions to a human. Underneath that policy sits a more basic
question this lesson answers: what makes an action risky in the first place? §7.1 answers it directly by
calling each tool and checking, empirically, whether the world looks any different afterward.

### 3.2 A label is a claim; a before/after check is evidence

§7.1 doesn't just trust that `get_order` is read-only and `issue_refund` is state-changing because someone
tagged them that way — it captures the world's state before and after each call and confirms the tag
matches what actually happened. Getting this check right took two real fixes along the way, both of which
turned out to matter for the lesson itself.

### 3.3 Retrying is free for one kind and repeats a real effect for the other

§7.2 doesn't argue abstractly that retries are risky — it retries a read-only lookup three times (nothing
changes) and a state-changing action three times (three refunds are issued for what was meant to be one).

### 3.4 Not all state-changing actions repeat the same way

§7.1's own verification uncovered a real nuance: a SET-style action (overwriting a field) can look
unchanged when repeated with the identical value, while an APPEND-style action (like issuing a refund) adds
a new effect every single time, regardless of whether the arguments repeat. Both are genuinely
state-changing; only one of them happens to be safe to repeat by coincidence of what it does.

---

## 4. Analogy

**Checking a mailbox versus mailing a letter.** Checking a mailbox has no effect on the world beyond telling
you what's inside — check it once, check it ten times, nothing about the mailbox or its contents changes
because you looked. Mailing a letter is different: the moment you drop it in, something in the world has
changed, and dropping a second, identical letter in doesn't undo or merge with the first — it's a second
letter, sent. Setting your own mailbox's forwarding address to the same address twice looks like nothing
happened the second time; mailing two copies of the same letter is unmistakably two letters, no matter how
identical their contents are.

### Where the analogy breaks

- **A mailbox check has zero cost regardless of how many times you do it.** §7.3's speculative calls carry
  a real, if small, computational cost per call — the lesson's claim is that they carry no *side-effect*
  risk, not that they are literally free.
- **Real mail systems sometimes do deduplicate identical letters.** §5.4's SET-versus-APPEND distinction is
  about what a *specific* action's own logic happens to do, not a guarantee that any particular
  state-changing action behaves one way or the other without checking.

---

## 5. Detailed technical explanation

### 5.1 The correct test compares before-any-call to after-one-call

`[REAL, measured]` §7.1 initially compared the world *after* a first call to the world *after* a second
call — the wrong test, since it actually measures whether repeating the action has an *additional* visible
effect, not whether the action has any effect at all. The corrected test compares the world before any call
to the world after exactly one call: **`get_order` and `check_inventory` left `ORDERS` and `REFUND_LOG`
completely unchanged; `issue_refund` and `update_shipping_address` both genuinely changed the world the
moment they ran.**

### 5.2 A shallow copy can hide a real mutation

`[REAL, measured]` The verification's first working version used `dict(ORDERS)` to snapshot the world —
a *shallow* copy. Because `ORDERS`' values are themselves dicts, a shallow copy shares those inner
dictionaries by reference: mutating `ORDERS["O-3001"]["address"]` also mutated what the "before" snapshot
was pointing at, making a real, executed address change invisible to the comparison. **Switching to
`copy.deepcopy()` fixed this** — and the fact that this specific bug had to be found and fixed is itself
evidence for a general point: verifying a "no side effect" claim requires genuinely independent snapshots,
not merely distinct-looking variable names.

### 5.3 A retry is free for one kind and costly for the other, measured directly

`[REAL, measured]` §7.2 retried `check_inventory` three times — **the world was identical before and after
all three calls.** It retried `issue_refund` three times for what was meant to be one $25.00 refund — **the
log shows three separate entries, a real $75.00 total paid out for a single request.** This is M8-L06's own
double-refund finding, now identified as a structural property of *this kind* of action, independent of
whether persistent memory exists to catch it.

### 5.4 SET and APPEND are both state-changing, but repeat differently

`[REAL, measured]` §7.1's bonus check called `update_shipping_address` a second time with the *identical*
address already on file: **the world showed no further change**, because overwriting a field with the value
it already holds is indistinguishable from not calling the function again. `issue_refund`, by contrast, adds
a new log entry on every call regardless of whether the arguments repeat. **Both are genuinely
state-changing by this lesson's own read-only test — the difference is a separate property (whether
repeating the identical call is safe), which is exactly what M8-L12's idempotency mechanisms are built to
guarantee deliberately, rather than leaving to an action's own incidental behavior.**

### 5.5 Assumptions and limitations

- `declared_read_only` is a flag this lab's own author assigned by hand — a real system needs an actual
  process (code review, a convention enforced at tool registration) to keep this tag accurate as tools
  change over time.
- This lesson does not cover idempotency keys that make a state-changing action safe to retry despite not
  being read-only (M8-L12), how a real system could enforce the read-only tag automatically rather than
  trusting a hand-set flag, or combining this classification with M8-L10's approval tiers into one complete
  policy.

---

## 6. Worked example — the "safe" retry that wasn't

**The system.** An agent's tool-execution loop, following a general best practice, automatically retries
any tool call that times out, up to twice, on the theory that a timeout usually means the request never
went through.

**The incident.** A `send_notification` tool — which genuinely sends an email, a real state-changing action
— timed out due to a slow network response, even though the email had, in fact, already been sent
successfully before the response reached the caller. The automatic retry policy, applied uniformly to every
tool regardless of its classification, sent the notification a second time. A customer received the same
email twice.

**Why this matches §5.3 exactly.** This is §7.2's own measured finding at production scale: a retry policy
that doesn't distinguish read-only from state-changing actions treats every timeout the same way, and for a
state-changing action, "the same way" means repeating a real effect that may have already happened.

**Three defects the incident revealed:**

| # | Defect | Consequence |
|---|---|---|
| 1 | No classification distinguished which tools were safe to retry blindly | A retry policy meant for safe, read-only cases was applied uniformly to a state-changing one |
| 2 | `send_notification` had no idempotency mechanism (M8-L12) to make a repeat safe | A timeout with no way to confirm prior success left retrying and not retrying both risky |
| 3 | The retry policy was adopted as a general best practice without auditing which specific tools it would apply to | The gap was invisible until a real timeout coincided with a real, already-successful send |

### The fix

**Classify every tool as read-only or state-changing before deciding a retry policy**, per §5.1 —
read-only tools can retry freely; state-changing ones need a different mechanism.

**Add an idempotency safeguard to state-changing tools that must support retries**, per §5.4 — M8-L12
covers this directly; a blind retry policy is not a substitute for it.

**The general rule.** **A retry policy that doesn't distinguish read-only actions from state-changing ones
is applying a safe idea (retrying costs nothing) to cases where it's actually not true (retrying repeats a
real effect) — the safety of retrying was never a property of retries in general, only of the specific
actions that have no side effect to repeat.**

---

## 7. Practical activity

**File:** [`labs/m8/l11_read_only_vs_state_changing.py`](../../labs/m8/l11_read_only_vs_state_changing.py)

**No API key, no network, no third-party dependencies.** Runs in well under a second.

```bash
source .venv/bin/activate
python labs/m8/l11_read_only_vs_state_changing.py
```

### 7.2 Expected output

`[EXECUTED]` — 2026-09-10, Python 3.10.11 (pure standard library).

```text
============================================================================
1. A DECLARED FLAG, VERIFIED BY ACTUALLY CALLING EACH TOOL TWICE
============================================================================
  Tool                      Declared        Has ANY side effect?    Verified
  get_order                 read-only       False                   yes
  check_inventory           read-only       False                   yes
  issue_refund              state-changing  True                    yes
  update_shipping_address   state-changing  True                    yes

  ORDERS after all calls: {'O-3001': {'item': 'Desk Lamp', 'amount': 40.0, 'address': '99 Oak Ave'}}
  REFUND_LOG after all calls: [('O-3001', 10.0)]

  get_order and check_inventory left the world UNCHANGED -- neither
  ORDERS nor REFUND_LOG differ before versus after either call.
  issue_refund and update_shipping_address each genuinely changed the
  world the moment they ran, confirming their declared tags
  empirically, not just by the label attached to them.

  A further, more subtle check: call update_shipping_address a SECOND
  time with the IDENTICAL address already on file:
    World changed by this second, identical call? False
  This tool is genuinely state-changing (it writes to ORDERS) -- but
  writing the SAME value twice happens to look unchanged, because a
  SET overwritten with an identical value is indistinguishable from
  never having been called again. issue_refund's retry in section 2
  shows the opposite: an APPEND-style action that adds a new entry
  EVERY time, identical arguments or not. Both are state-changing;
  only one of them is also naturally safe to repeat -- exactly the
  distinction M8-L12 (idempotency) builds on directly.

============================================================================
2. RETRYING AFTER A SUSPECTED FAILURE: SAFE FOR ONE KIND, NOT THE OTHER
============================================================================
  A caller unsure whether its first attempt succeeded retries 3 times:

  check_inventory retried 3x -- world changed? False
  issue_refund retried 3x -- REFUND_LOG now: [('O-3001', 25.0), ('O-3001', 25.0), ('O-3001', 25.0)]
  Total refunded for a SINGLE $25.00 refund request: $75.00

  Retrying the read-only lookup 3 times cost nothing beyond 3 function
  calls -- the world was identical before and after. Retrying the
  state-changing action 3 times, with no other safeguard, issued the
  refund 3 TIMES -- the exact double/triple-execution risk M8-L06's
  own lab demonstrated, now identified as a property of THIS KIND of
  action specifically, not of missing memory alone.

============================================================================
3. SPECULATIVE CALLS: CHEAP AND SAFE FOR ONE KIND, NEVER FOR THE OTHER
============================================================================
  An agent uncertain which of several lookups it needs can call ALL
  of them speculatively, at no risk, since none of them changes
  anything:

    check_inventory('Desk Lamp') -> 7 (speculative -- no cost beyond the call itself)
    check_inventory('Wireless Mouse') -> 0 (speculative -- no cost beyond the call itself)
    check_inventory('Standing Desk') -> 0 (speculative -- no cost beyond the call itself)

  The equivalent for a state-changing action would be calling
  issue_refund() 'just to see if it's the right order' -- there is no
  version of this that is safe, because every call has a real effect
  the moment it runs, whether or not it turns out to have been the
  right decision.

============================================================================
4. WHAT THIS LAB IS AND IS NOT
============================================================================
  REAL: every world-state comparison above is a genuine before/after
  check against ORDERS and REFUND_LOG -- the empirical verification
  in section 1 and the triple refund in section 2 are measured
  outcomes of actually calling these functions, not asserted claims.

  ILLUSTRATIVE: declared_read_only is a flag this lab's own author
  assigned by hand -- a real system needs a real process (code review,
  a convention enforced in how tools are registered) to keep this tag
  accurate as tools change, which section 1's verification step is
  designed to catch when it drifts.

  NOT SHOWN: idempotency keys that make a state-changing action safe
  to retry despite not being read-only (M8-L12's own topic); how a
  real system enforces the read-only tag automatically rather than
  trusting a hand-set flag; and combining this classification with
  M8-L10's approval tiers for a complete action-safety policy.

Done.
```

### 7.3 Reading the result

**Section 1's own debugging history, told honestly in §5.1 and §5.2, is more instructive than a clean
result would have been.** Two real mistakes — comparing the wrong pair of snapshots, then snapshotting with
a shallow copy that hid a real mutation — both had to be found and fixed before the verification actually
verified anything. A lesson about checking claims empirically is more convincing when its own check needed
correcting.

**The SET-versus-APPEND distinction in §5.4 is easy to miss and important not to.** It would be natural to
assume "state-changing" is a single category with uniform retry risk; the bonus check shows two
state-changing actions can behave completely differently under a repeat, for reasons specific to what each
one actually does internally.

**Section 2's $75.00 for a single $25.00 request is the concrete stakes.** It is the same category of harm
M8-L06 demonstrated from a different cause (missing memory) — here, the cause is retrying an action whose
classification alone should have signaled the risk.

---

## 8. Common mistakes and troubleshooting

1. **Trusting a tool's declared read-only/state-changing tag without verifying it against actual
   behavior.** §5.1, §5.2 — a tag can be wrong, and this lesson's own verification needed two real fixes
   before it worked correctly.
2. **Applying a uniform retry policy to every tool regardless of classification.** §5.3, §6 — read-only
   tools can retry freely; state-changing ones need a specific safeguard, not a blanket policy.
3. **Assuming all state-changing actions carry identical retry risk.** §5.4 — a SET-style action may
   happen to look safe to repeat; an APPEND-style action generally will not, and neither should be assumed
   without checking.
4. **Making a state-changing call "just to see" during exploration.** §7.3 — this has no read-only
   equivalent; every state-changing call has a real effect the moment it runs.
5. **Testing a "no side effect" claim by comparing the wrong before/after pair, or with a shallow copy that
   can alias nested mutable state.** §5.1, §5.2 — both are genuine, specific pitfalls this lesson's own
   verification ran into.

| Symptom | Likely cause | Fix |
|---|---|---|
| A retried action produces a duplicated real-world effect (an extra charge, a duplicate message) | The action was retried without checking whether it is read-only or state-changing | Classify the action first, per §5.1, and add an idempotency safeguard for state-changing retries (M8-L12) |
| A verification test reports no side effect for an action that clearly should have one | The snapshot comparison used a shallow copy, aliasing nested mutable state | Use a deep copy for any snapshot involving nested structures, per §5.2 |
| Two actions both called "state-changing" behave very differently when repeated with the same arguments | One is a SET-style action (naturally idempotent for identical values) and the other is APPEND-style (never idempotent) | Test each action's actual repeat behavior directly, per §5.4, rather than assuming uniform risk |
| An agent explores multiple options by calling a state-changing tool speculatively | No read-only alternative was available, or the distinction wasn't enforced in tool design | Restrict speculative/exploratory calls to genuinely read-only tools, per §7.3 |

---

## 9. Security, privacy, reliability, cost

- **Reliability.** Verify a tool's read-only/state-changing classification against its actual behavior, not
  just its declared tag — this lesson's own verification needed two real fixes to do this correctly (§5.1,
  §5.2).
- **Reliability.** Apply retry policies based on classification, not uniformly — a blind retry policy is
  safe for read-only tools and directly risky for state-changing ones (§5.3, §6).
- **Cost.** A repeated state-changing action has a real, direct cost (§7.2's $75.00 for a single $25.00
  refund; §6's duplicated customer notification).
- **Reliability.** Never call a state-changing action speculatively "just to see" — restrict exploratory,
  low-commitment calling to genuinely read-only tools (§7.3).

---

## 10. Exercises

### Exercise 1 — Beginner (~20 min)

1. What is the difference between a read-only action and a state-changing action, in this lesson's own
   terms?
2. Why was comparing "after the first call" to "after the second call" the wrong test for classifying a
   tool as read-only or state-changing?
3. Why did a shallow copy fail to detect a real mutation in this lesson's own lab?
4. Why is it safe to retry a read-only lookup any number of times?
5. What is the difference between a SET-style state-changing action and an APPEND-style one?

### Exercise 2 — Intermediate (~40 min)

1. Run the lab. Confirm the verification table in §7.1, the retry outcomes in §7.2, and the speculative
   calls in §7.3 on your own machine.
2. Add a new tool of your own design, declare its classification, and verify it using this lesson's
   before/after snapshot technique.
3. Deliberately reintroduce the shallow-copy bug from §5.2 (change `copy.deepcopy(ORDERS)` back to
   `dict(ORDERS)`) and confirm you reproduce the same false "no side effect" result for
   `update_shipping_address`.
4. Design a second APPEND-style state-changing tool (distinct from `issue_refund`) and confirm it is
   NOT idempotent under a repeated identical call, the same way `issue_refund` is not.
5. Using §5.4's distinction, classify three tools from a system you're familiar with as read-only,
   SET-style state-changing, or APPEND-style state-changing.

### Exercise 3 — Challenge (~50 min)

1. Design an automatic classifier that could, in principle, detect whether a Python function is read-only
   by inspecting its side effects (without running it) — and explain why this is fundamentally harder than
   the empirical, run-it-and-check approach this lesson uses.
2. Extend this lesson's verification into a reusable test utility that could be run against any tool
   registered in a real system, flagging any mismatch between declared and observed behavior automatically.
3. Using M8-L10's tiered-approval framework, propose how read-only versus state-changing classification
   should interact with approval tiers — should read-only actions ever require approval?
4. Research (conceptually) how HTTP's own method semantics (GET versus POST/PUT/DELETE) encode a similar
   read-only/state-changing distinction, and compare it to this lesson's classification.
5. Using §6's worked example, design a retry policy that explicitly checks a tool's classification before
   deciding whether to retry, and specify what it should do differently for each case.

---

## 11. Quiz

*(Answers: [`answer-keys/module-08-answers.md`](../../answer-keys/module-08-answers.md#m8-l11).)*

**Q1.** Per §7.1's measured result, what did comparing the world before any call to the world after one
call reveal about `get_order` and `check_inventory`?

- A. Neither tool changed ORDERS or REFUND_LOG at all — the world was identical before and after.
- B. Both tools genuinely changed ORDERS and REFUND_LOG.
- C. Only get_order changed the world; check_inventory did not.
- D. The comparison could not be performed for either tool.

**Q2.** Per §5.2, why did the lab's first snapshot implementation fail to detect a real mutation to
`update_shipping_address`'s address field?

- A. ORDERS was never initialized in the first place.
- B. The address field was never actually written to.
- C. The snapshot function had a syntax error.
- D. The snapshot used a shallow copy, so the inner dict holding the address was shared by reference between the "before" and "after" snapshots, making the mutation invisible to the comparison.

**Q3.** Per §5.2, what was the fix for the shallow-copy bug?

- A. Removing the snapshot comparison entirely.
- B. Using copy.deepcopy() instead of a shallow dict copy, so nested mutable state is genuinely independent between snapshots.
- C. Changing update_shipping_address to no longer write to ORDERS.
- D. Comparing string representations instead of the actual data structures.

**Q4.** Per §7.2's measured result, what happened when `issue_refund` was retried three times for what
was meant to be a single $25.00 refund?

- A. The retries had no effect; only one refund was recorded.
- B. The loop crashed on the second retry.
- C. Three separate refund entries were recorded, totaling $75.00 for a single intended refund.
- D. The retries were automatically detected and merged into one.

**Q5.** Per §5.3, why is retrying a read-only action after a suspected failure described as safe?

- A. A read-only action has no side effect on the world, so calling it any number of times produces no additional real-world consequence beyond returning a value.
- B. Read-only actions are always faster to execute than state-changing ones.
- C. Read-only actions never fail, so retries are never actually needed.
- D. Retrying is only safe if the action has already succeeded once.

**Q6.** Per §5.4's measured result, what did the bonus check on `update_shipping_address` reveal about
calling it twice with the identical address?

- A. It raised an exception on the second call.
- B. It caused ORDERS to be deleted entirely.
- C. It proved update_shipping_address is actually read-only.
- D. The second call left the world looking unchanged, because overwriting a field with the value it already holds produces no observable difference, even though the action is genuinely state-changing.

**Q7.** Per §5.4, how does `issue_refund`'s repeat behavior differ from `update_shipping_address`'s?

- A. Both behave identically when called twice with identical arguments.
- B. issue_refund adds a new log entry every time it is called, regardless of whether the arguments repeat, unlike update_shipping_address's SET-style behavior.
- C. issue_refund is read-only, while update_shipping_address is state-changing.
- D. Neither tool has any observable repeat behavior.

**Q8.** Per §6's worked example, what caused the customer to receive the same notification email twice?

- A. The customer explicitly requested two copies of the email.
- B. The email server was configured incorrectly.
- C. A retry policy was applied uniformly to send_notification, a state-changing action, without a classification-based distinction or an idempotency safeguard.
- D. The customer's email address was duplicated in the database.

**Q9.** Per §6, what is the stated general rule this incident illustrates?

- A. A retry policy that doesn't distinguish read-only from state-changing actions applies a safe idea to cases where it isn't actually safe, since retrying only costs nothing when there's no side effect to repeat.
- B. Retry policies should never be used under any circumstances.
- C. State-changing actions should never support retries under any circumstances.
- D. The incident has no generalizable lesson beyond this specific system.

**Q10.** Per §6, what is proposed as the fix for the kind of gap this incident revealed?

- A. Remove all state-changing tools from the system.
- B. Only allow read-only tools to exist in any agent system.
- C. Disable all retry logic permanently across the entire system.
- D. Classify every tool as read-only or state-changing before deciding a retry policy, and add an idempotency safeguard (M8-L12) for state-changing tools that must support retries.

**Q11.** Per §7.4, what does this lesson explicitly NOT cover?

- A. The empirical verification of read-only versus state-changing behavior in section 1.
- B. Idempotency keys that make a state-changing action safe to retry, automatic enforcement of the read-only tag, and combining this classification with M8-L10's approval tiers — left to M8-L12 or as natural extensions.
- C. The retry demonstration in section 2.
- D. The speculative-calling demonstration in section 3.

**Q12.** What is the general lesson this lab demonstrates about read-only versus state-changing actions?

- A. All actions carry identical retry and exploration risk regardless of classification.
- B. State-changing actions are always safe to retry as long as the arguments are identical.
- C. Read-only actions can be retried and called speculatively with no real-world risk, while state-changing actions repeat a real effect every time they run — and even among state-changing actions, repeat behavior varies by what the action specifically does (SET versus APPEND).
- D. Classification of tools as read-only or state-changing has no practical consequence for system design.

**Q13.** *(Written, rubric-graded.)* In under 150 words: your team is designing a general retry policy for
an agent's tool-execution loop. Based on this lesson, what would you check before applying it, and why?

---

## 12. Revision notes

- **A read-only action has no side effect on the world; a state-changing action has a real effect every
  time it runs** — verified empirically by comparing world state before and after a single call, not by
  trusting a declared tag alone.
- **Two real bugs had to be fixed to make this lesson's own verification correct** — comparing the wrong
  snapshot pair, and a shallow copy that aliased nested mutable state — both genuine pitfalls in testing a
  "no side effect" claim.
- **Retrying a read-only action after a suspected failure is free; retrying a state-changing action without
  a safeguard repeats its real effect** — measured directly: a single intended $25.00 refund became $75.00
  across three retries.
- **Speculative, exploratory calling is safe only for read-only actions** — a state-changing action has no
  "just to see" version, since every call has a real effect the moment it runs.
- **Not all state-changing actions repeat the same way** — a SET-style action can look unchanged when
  repeated with an identical value; an APPEND-style action adds a new effect every time, regardless of
  argument repetition — the exact distinction M8-L12's idempotency mechanisms are built to handle
  deliberately.

---

## 13. Completion checklist

- [ ] I can distinguish a read-only action from a state-changing one and verify the distinction
      empirically.
- [ ] I can explain why comparing the wrong snapshot pair, or using a shallow copy, can hide a real
      mutation.
- [ ] I can explain why retrying is safe for read-only actions and risky for state-changing ones.
- [ ] I can explain why speculative calling has no safe equivalent for state-changing actions.
- [ ] I can distinguish a SET-style state-changing action from an APPEND-style one by its repeat behavior.
- [ ] I classify tools before applying a retry policy, rather than applying one uniformly.
- [ ] I scored 10/13 on the quiz.

---

## 14. References

- M8-L06's own double-refund finding, revisited here as a property of action type rather than missing
  memory. `[STABLE]`
- HTTP method semantics (GET as read-only/safe, POST/PUT/DELETE as state-changing), for a widely-used
  parallel to this lesson's distinction, where available. `[UNVERIFIED]`

---

## 15. Next lesson

→ M8-L12 — Idempotency and Duplicate-Action Prevention

This lesson identified which actions carry retry risk. Next: the actual mechanism — an idempotency key —
that makes a state-changing action safe to retry deliberately, rather than leaving safety to chance.
