# M8-L10 — Human Approval and Escalation

| | |
|---|---|
| **Lesson ID** | M8-L10 |
| **Difficulty** | 2 (Intermediate) |
| **Estimated study time** | 2.0 hours |
| **Prerequisites** | [M8-L05](M8-L05-tool-schemas-argument-validation.md) |

---

## 1. Learning objectives

1. **Design** a tiered approval policy that routes actions to auto-approval, human approval, or escalation
   based on blast radius, extending M5-L08's own gating principle.
2. **Implement** an approval gate that genuinely pauses an action until a real human decision is recorded,
   not merely logs the request and proceeds anyway.
3. **Distinguish** escalation triggered by high blast radius from escalation triggered by genuine
   classification uncertainty.
4. **Measure** the real cost of requiring approval for every action versus a properly-tiered policy.
5. **Identify**, from a described incident, whether an approval gate was missing, bypassed, or simply
   overwhelmed by volume.

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **Approval gate** | A checkpoint where an action pauses until a human explicitly approves it. |
| **Tiered policy** | A rule that routes different cases to different levels of review based on risk. |
| **Escalation** | Routing a case to a human specifically because the system cannot confidently decide it itself. |
| **Approval fatigue** | The degraded scrutiny that results from routing too many low-stakes cases through the same review process. |
| **Pending state** | A genuine, unresolved status an action holds while awaiting a human decision. |

---

## 3. Plain-language explanation

### 3.1 M5-L08 and M8-L02 gated with code; this lesson gates with a person

M5-L08 established that code, not a prompt, should decide whether an action is allowed. M8-L02 showed a
deterministic gate applied to a computed value. This lesson adds a third kind of gate: one where the
decision-maker is a human, reserved for cases where blast radius or uncertainty makes an automatic decision
the wrong choice.

### 3.2 A tiered policy decides who decides, not just what's allowed

§7.1 sorts 20 real requests into three tiers by amount — most auto-approve, a few need a human's judgment,
a few need a more senior one. This mirrors M5-L08's blast-radius principle exactly, but the "control" at the
top of the range isn't a hard-coded rejection — it's a person.

### 3.3 A gate that doesn't actually wait isn't a gate

§7.2 doesn't just check whether an amount exceeds a threshold — it demonstrates that the action genuinely
does not happen until a real decision is recorded. A pending request stays pending; nothing about the code
resolves it on its own.

### 3.4 Not every escalation is about the number

§7.3 shows a second, distinct reason to escalate: not because an amount is large, but because the
classifier cannot confidently place a request into any tier at all — a missing amount, an unsupported
currency. Guessing here would be a real, silent risk; escalating is the same abstention principle M7-L13
built for answers, applied here to a decision.

### 3.5 "Approve everything" has a real, computed cost

§7.4 doesn't argue abstractly that requiring approval for everything causes "fatigue" — it counts. The same
20 requests need 20 approvals under a blanket policy and 6 under a properly tiered one, a 70% reduction with
no loss of scrutiny on the cases that actually warrant it.

---

## 4. Analogy

**An emergency room's triage nurse, not a receptionist who refers every patient to the same specialist.** A
triage nurse looks at each arriving patient and routes them: a minor scrape gets basic first aid on the
spot; a broken bone goes to a doctor; a suspected heart attack goes straight to the most senior physician
available. A receptionist who instead referred every single patient — scrapes included — to the most senior
cardiologist would not be "extra safe"; they would bury genuinely urgent cases in a queue full of routine
ones, and the cardiologist's attention on any specific patient would be worth less because of how much of it
had to be spread across cases that never needed a cardiologist at all.

### Where the analogy breaks

- **A triage nurse can look a patient in the eye and ask follow-up questions in real time.** §7.2's approval
  queue is a one-shot request-and-wait; this lesson does not model a back-and-forth clarification exchange
  between the agent and the approver.
- **A hospital's severity levels are broadly agreed upon across the field.** §7.1's specific dollar
  thresholds are this lesson's own illustration, not a claim about where a real policy's lines should sit.

---

## 5. Detailed technical explanation

### 5.1 A tiered policy applies blast radius to the question of who decides

`[REAL, measured]` §7.1 ran `decide_tier()` against 20 real amounts: **14 auto-approved, 1 needed human
approval, 5 escalated to senior review** — only 6 of 20 requests needed any human involvement at all. This
directly extends M5-L08's blast-radius principle: a $12 refund and a $999 refund are not equally risky, and
the tiering reflects that difference in exactly where M5-L08's own gate would have drawn a hard line, except
here the top tier's decision-maker is a person, not a rejection.

### 5.2 The gate is real because the wait is real

`[REAL, measured]` §7.2's `process_request()` returned a `"WAITING"` state for both above-threshold
requests, **genuinely recording each in `PENDING_APPROVALS` with `decision: None`** rather than issuing a
refund. Contrasted directly against calling `issue_refund()` without the gate — which succeeds immediately,
labeled explicitly as the wrong behavior — **only after `apply_human_decision()` records a real approval
does a refund for that specific request get issued.** The second request, `O-2002`, remained genuinely
pending and unresolved, confirmed by inspecting `PENDING_APPROVALS` directly.

### 5.3 Escalation for amount and escalation for uncertainty are different triggers

`[REAL, measured]` §7.3 ran `decide_tier_with_uncertainty()` against three cases: a normal auto-approve
amount, a missing amount, and an amount in an unsupported currency. **The second and third cases escalated
for a reason entirely separate from §7.1's tiers** — not because the value was large, but because the
classifier had no confident way to place the request into any tier at all. Guessing (defaulting to
auto-approve for an unrecognized currency, say) would silently apply a USD-denominated policy to a non-USD
amount; escalating instead makes the uncertainty visible rather than resolving it by assumption.

### 5.4 "Approve everything" is measurably worse, not just theoretically worse

`[REAL, measured]` §7.4 counted **20 required approvals under a blanket policy against 6 under §7.1's
tiered one — a 70% reduction** for the identical set of requests. This reframes "approval fatigue" from a
vague warning into a specific, computed consequence: a reviewer facing 20 requests, most of them genuinely
routine, has measurably less basis for distinguishing which ones deserve real scrutiny than a reviewer
facing only the 6 that actually crossed a real threshold.

### 5.5 Assumptions and limitations

- `apply_human_decision()` stands in for a real reviewer's actual judgment — this lab scripts one specific
  decision rather than modeling a real review interface or a real person's reasoning.
- The specific dollar thresholds (`$50`, `$200`) are this lesson's own illustration, not a claim about
  where a real policy's tiers should sit for any particular business.
- This lesson does not cover what information a real approval interface should show a reviewer, a real
  audit trail of who approved what and when, or what happens if a pending approval is never resolved at
  all (bordering on M8-L13's timeout/recovery topic).

---

## 6. Worked example — the approval queue nobody could keep up with

**The system.** A team adds a human-approval requirement to every action an internal agent proposes, after
a single high-profile incident involving one large, mistaken action. The policy makes no distinction by
amount or risk — every action, regardless of size, waits in the same review queue.

**The incident.** Within two weeks, the approval queue's average wait time grew past a full business day,
and reviewers, facing dozens of routine, low-stakes requests for every genuinely risky one, began
approving requests in batches without individually reading each one — the review had become, in practice,
what the policy was meant to prevent: unexamined approval.

**Why this matches §5.4 exactly.** This is §7.4's measured trade-off at production scale: a policy that
routes everything through the same gate does not multiply scrutiny by the number of gates crossed — it
divides the reviewer's attention across a queue where the genuinely risky cases are indistinguishable from
routine ones by the time they're reached.

**Three defects the incident revealed:**

| # | Defect | Consequence |
|---|---|---|
| 1 | No tiering existed to distinguish low-blast-radius actions from high-blast-radius ones | Every action, regardless of risk, consumed the same limited reviewer attention |
| 2 | The queue gave reviewers no signal about which pending items were actually high-stakes | Batch-approving became the practical coping strategy, defeating the policy's own purpose |
| 3 | The original incident that motivated the blanket policy was never analyzed for what SPECIFIC threshold would have caught it | The fix (approve everything) was broader than the problem (one specific kind of large, risky action) |

### The fix

**Analyze what specifically made the original incident risky**, per §5.1 — likely the action's blast
radius, not its mere existence — and set a tier threshold that catches that specific risk without routing
every unrelated, low-stakes action through the same gate.

**Reserve human approval for the tier that actually needs it**, per §5.4's measured reduction — restoring
the reviewer's ability to give real attention to the smaller number of requests that genuinely warrant it.

**The general rule.** **A human approval gate's value comes from a human actually looking closely at what
reaches them — routing too much through it, regardless of individual risk, doesn't add scrutiny, it dilutes
whatever scrutiny the reviewer has left to give the cases that need it most.**

---

## 7. Practical activity

**File:** [`labs/m8/l10_human_approval_escalation.py`](../../labs/m8/l10_human_approval_escalation.py)

**No API key, no network, no third-party dependencies.** Runs in well under a second.

```bash
source .venv/bin/activate
python labs/m8/l10_human_approval_escalation.py
```

### 7.2 Expected output

`[EXECUTED]` — 2026-09-10, Python 3.10.11 (pure standard library).

```text
============================================================================
1. A TIERED POLICY: AMOUNT DECIDES WHO DECIDES
============================================================================
  20 real refund requests, amounts: [12, 8, 45, 300, 15, 22, 500, 9, 60, 18, 250, 7, 33, 400, 11, 19, 27, 999, 14, 21]

  Auto-approve (< $50):            14
  Needs human approval ($50-$200):    1
  Escalate to senior review (> $200): 5

  Only 6 of 20 requests need ANY human involvement at all --
  the rest are low enough blast radius to auto-approve safely.

============================================================================
2. THE AGENT GENUINELY WAITS: NO REFUND BEFORE A HUMAN DECIDES
============================================================================
  Two requests, both above the auto-approve limit:

    process_request('O-2001', 120.0) -> 'WAITING: APPR-O-2001 queued for needs approval, no refund issued yet'
    process_request('O-2002', 80.0) -> 'WAITING: APPR-O-2002 queued for needs approval, no refund issued yet'

  PENDING_APPROVALS: {'APPR-O-2001': {'order_id': 'O-2001', 'amount': 120.0, 'decision': None}, 'APPR-O-2002': {'order_id': 'O-2002', 'amount': 80.0, 'decision': None}}

  Neither refund was issued -- the function returned a WAITING state,
  not a refund confirmation, because a human decision genuinely does
  not exist yet. Contrast this with an ungated version that would
  call issue_refund() immediately regardless of tier:
    issue_refund('O-2001', 120.0) -> 'refund of $120.00 issued for O-2001'  (WRONG -- skipped the gate entirely)

  A human decision now arrives for one of the two pending requests:
    apply_human_decision('APPR-O-2001', approved=True) -> 'refund of $120.00 issued for O-2001'

  The refund for O-2001 was issued only once a real approval was
  recorded -- 'APPR-O-2002' remains pending, genuinely unresolved,
  in PENDING_APPROVALS: {'order_id': 'O-2002', 'amount': 80.0, 'decision': None}

============================================================================
3. ESCALATION FROM UNCERTAINTY, NOT JUST FROM AMOUNT
============================================================================
    decide_tier_with_uncertainty(30.0, 'USD') -> 'auto-approve'
    decide_tier_with_uncertainty(None, 'USD') -> 'escalate: amount could not be determined'
    decide_tier_with_uncertainty(75.0, 'EUR') -> "escalate: unsupported currency 'EUR', cannot apply USD-denominated policy"

  The second and third cases escalate for a DIFFERENT reason than
  section 1's amount-based tiers -- not because the amount is large,
  but because the classifier cannot confidently determine a tier at
  all. Guessing (e.g., defaulting to auto-approve for a currency the
  policy was never designed to handle) would be a real, silent risk;
  escalating is the honest alternative, matching M7-L13's abstention
  principle applied here to a decision instead of an answer.

============================================================================
4. THE REAL COST OF 'JUST APPROVE EVERYTHING'
============================================================================
  A policy requiring human approval for EVERY request: 20 approvals needed for 20 requests.
  This lesson's tiered policy: 6 approvals needed for the same 20 requests.
  Reduction: 70% fewer human decisions,
  for the SAME set of real requests, with the smallest, lowest-blast-
  radius ones handled automatically instead of consuming a human
  reviewer's attention on every single one.

  This is a real, measurable version of 'approval fatigue': a
  reviewer facing 20 approval requests for 20 low-stakes refunds has
  no way to tell which of the 20 actually deserves scrutiny --
  a reviewer facing only 6, each one genuinely above the
  auto-approve threshold, can give each one real attention instead of
  rubber-stamping a long queue of routine requests.

============================================================================
5. WHAT THIS LAB IS AND IS NOT
============================================================================
  REAL: every tier count, every WAITING state, and the escalation
  triggers in section 3 are genuinely computed -- process_request()
  genuinely returns before issuing a refund for any non-auto-approve
  tier, and apply_human_decision() is the only path that can issue
  one afterward.

  ILLUSTRATIVE: apply_human_decision() stands in for a real human
  reviewer's actual decision -- this lab scripts one specific
  decision (approved=True) rather than modeling a real review
  interface or a real reviewer's judgment. The specific dollar
  thresholds are this lesson's own illustration, not a universal
  policy recommendation.

  NOT SHOWN: what information a real approval interface should show
  a reviewer to let them decide quickly and correctly; a real audit
  trail of who approved what and when; and what happens if a pending
  approval is never resolved at all, a case bordering on M8-L13's
  own timeout/recovery topic.

Done.
```

### 7.3 Reading the result

**Section 2's contrast is the load-bearing evidence in this lesson.** It would be easy to write an approval
*check* that logs a warning and proceeds anyway; showing the ungated call succeed immediately, right next to
the gated calls genuinely returning a pending state, is what proves the gate actually gates.

**Section 3 is easy to conflate with section 1, and the lab deliberately keeps them separate.** A large
amount and an unrecognized currency both result in escalation, but for structurally different reasons — one
because the stakes are high, the other because the system cannot tell what the stakes even are.

**Section 4's 70% is not a rhetorical flourish.** It's the same 20 requests, run through two different
policies, counted. The worked example in §6 shows what happens when that reduction is skipped.

---

## 8. Common mistakes and troubleshooting

1. **Building an approval check that logs a request and proceeds anyway.** §5.2 — a gate that doesn't
   genuinely block the action until a decision exists isn't a gate.
2. **Treating every escalation as if it means the same thing.** §5.3 — a high-blast-radius escalation and
   an uncertainty-driven escalation call for different follow-up (senior review versus fixing a
   classification gap).
3. **Guessing a tier when a request doesn't cleanly classify, rather than escalating.** §5.3 — a silent
   default (e.g., treating an unrecognized currency as USD) can produce a wrong decision with no visible
   sign anything went wrong.
4. **Requiring approval for everything "to be safe."** §5.4, §6 — this measurably dilutes the scrutiny
   available for the cases that actually need it, rather than adding safety uniformly.
5. **Adopting a blanket approval policy in reaction to one incident without analyzing what specific
   threshold would have caught it.** §6 — the fix should match the actual risk, not over-correct broadly.

| Symptom | Likely cause | Fix |
|---|---|---|
| An agent takes an action immediately despite an approval requirement existing "on paper" | The approval check logs or warns but doesn't actually block the action from proceeding | Confirm the action genuinely waits for a recorded decision, per §5.2 |
| A reviewer is approving a large volume of requests quickly, without apparent scrutiny | Too many low-stakes requests are routed through the same approval queue as high-stakes ones | Add a tiered policy so only genuinely high-blast-radius or uncertain cases require approval, per §5.1, §5.4 |
| A request with unusual or malformed input was auto-approved or auto-rejected without anyone noticing | The classifier guessed a tier for a case it could not confidently classify | Escalate on classification uncertainty specifically, per §5.3, rather than defaulting silently |
| An approval policy was recently made much stricter after one incident, and the team is now overwhelmed | The response was broader than the specific risk that caused the incident | Analyze the specific blast-radius threshold the incident crossed and tier accordingly, per §6 |

---

## 9. Security, privacy, reliability, cost

- **Security.** Confirm an approval gate genuinely blocks the action until a decision is recorded — a gate
  that only logs a request is not a control (§5.2).
- **Reliability.** Escalate when a request cannot be confidently classified, rather than defaulting to a
  guessed tier — an unrecognized case is exactly where a silent default is most dangerous (§5.3).
- **Cost.** Reserve human approval for tiers that genuinely need it — §7.4's measured 70% reduction is real
  reviewer time returned to the cases that actually warrant scrutiny (§5.4).
- **Reliability.** Set approval thresholds based on the specific blast radius a real incident revealed,
  not as a broad overcorrection applied to every action regardless of risk (§6).

---

## 10. Exercises

### Exercise 1 — Beginner (~20 min)

1. What are the three tiers this lesson's policy routes requests into, and what decides which tier a
   request falls into?
2. Why does §7.2 count as evidence that the approval gate genuinely blocks the action, not just logs it?
3. What are the two different reasons a request might escalate in this lesson?
4. Why is defaulting to a guessed tier for an unrecognized case described as dangerous?
5. What was the measured reduction in required approvals between a blanket policy and this lesson's tiered
   one?

### Exercise 2 — Intermediate (~40 min)

1. Run the lab. Confirm §7.1's tier counts, §7.2's pending/resolved states, and §7.4's 70% reduction on
   your own machine.
2. Add a fourth tier (e.g., amounts over $1000 require two separate approvals) and implement it.
3. Add a rejection case to §7.2 (`apply_human_decision` with `approved=False`) and confirm no refund is
   issued for that request.
4. Add a third uncertainty case to §7.3 (your own choice — a negative amount, an unrecognized order id
   format) and confirm it escalates rather than being guessed into a tier.
5. Using §5.1's blast-radius principle, propose your own dollar thresholds for a hypothetical system you're
   familiar with, and justify each tier boundary.

### Exercise 3 — Challenge (~50 min)

1. Design a real approval-request payload (the specific fields a reviewer would need to see) for this
   lesson's refund scenario, and explain why each field is necessary for a fast, correct decision.
2. Extend `PENDING_APPROVALS` to track how long each request has been pending, and design a policy for what
   should happen if a request remains unresolved past a time limit.
3. Using M8-L02's framework, argue whether the auto-approve tier in this lesson should also have a
   deterministic cap on the total number of auto-approvals per day, and why.
4. Research (conceptually) how a real production system implements a human-in-the-loop approval queue, and
   compare it to this lesson's `PENDING_APPROVALS` dict.
5. Using §6's worked example, design a monitoring metric a team could track (e.g., median approval queue
   wait time, percentage of requests batch-approved) that would have surfaced the incident before reviewers
   started batch-approving.

---

## 11. Quiz

*(Answers: [`answer-keys/module-08-answers.md`](../../answer-keys/module-08-answers.md#m8-l10).)*

**Q1.** Per §7.1's measured result, how many of the 20 real requests needed any human involvement at all?

- A. 6 of the 20 requests needed human involvement (1 for approval, 5 for escalation).
- B. All 20 requests needed human involvement.
- C. None of the 20 requests needed human involvement.
- D. Exactly half of the 20 requests needed human involvement.

**Q2.** Per §7.2's measured result, what happened when `process_request()` was called for an amount above
the auto-approve limit?

- A. It immediately issued the refund without any further check.
- B. It crashed with an error.
- C. It automatically rejected the request without human input.
- D. It returned a WAITING state and recorded the request in PENDING_APPROVALS with no decision yet, without issuing any refund.

**Q3.** Per §7.2's measured result, what was the contrast drawn between the gated call and the ungated
`issue_refund()` call?

- A. Both calls behaved identically in every respect.
- B. The ungated call issued a refund immediately, labeled explicitly as wrong behavior, while the gated call genuinely waited for a decision.
- C. The gated call issued the refund immediately; the ungated call waited.
- D. Neither call issued any refund under any circumstances.

**Q4.** Per §7.3's measured result, why did the case with a missing amount and the case with an
unsupported currency both escalate?

- A. Both amounts happened to exceed the senior-escalation threshold.
- B. Both requests were flagged as fraudulent.
- C. The classifier could not confidently place either request into any tier at all, a different reason than an amount being large.
- D. The system encountered a runtime error while processing both.

**Q5.** Per §5.3, why is escalating on classification uncertainty described as preferable to guessing a
tier?

- A. A silent default (e.g., treating an unrecognized currency as USD) could apply a wrong policy with no visible sign anything went wrong.
- B. Guessing is always faster and therefore preferable in every case.
- C. Escalating is described as strictly worse than guessing in every case.
- D. There is no meaningful difference between escalating and guessing.

**Q6.** Per §7.4's measured result, what was the reduction in required approvals between a blanket
"approve everything" policy and this lesson's tiered policy, for the same 20 requests?

- A. There was no measurable reduction.
- B. Exactly a 10% reduction.
- C. The tiered policy required more approvals than the blanket policy.
- D. Approximately 70% fewer required approvals.

**Q7.** Per §5.4, what is the stated consequence of routing too many low-stakes requests through the same
approval queue as high-stakes ones?

- A. It has no effect on reviewer attention or scrutiny.
- B. It dilutes the scrutiny available for genuinely high-stakes cases, rather than adding uniform safety.
- C. It always improves the quality of every decision made.
- D. It eliminates the need for any tiering at all.

**Q8.** Per §6's worked example, what happened to the review process after the blanket approval policy
was adopted?

- A. No requests were ever submitted for approval.
- B. The system automatically resolved all pending requests without human input.
- C. Reviewers began approving requests in batches without individually reading each one, defeating the policy's own purpose.
- D. Reviewer attention and scrutiny improved significantly for every request.

**Q9.** Per §6, what is the stated general rule this incident illustrates about a human approval gate's
value?

- A. A human approval gate's value comes from a human actually looking closely at what reaches them — routing too much through it dilutes scrutiny rather than adding it.
- B. Approval gates should always be applied to every action without exception.
- C. Approval gates have no measurable value under any circumstances.
- D. The specific incident that caused the policy change was never relevant to the fix.

**Q10.** Per §6, what should have been analyzed before adopting the blanket approval policy?

- A. Nothing needed to be analyzed; the blanket policy was the correct response.
- B. Only the average time it takes to review a single request.
- C. Only the total number of reviewers available.
- D. The specific blast-radius threshold the original incident actually crossed, so the fix could match the actual risk rather than over-correcting broadly.

**Q11.** Per §7.5, what does this lesson explicitly NOT cover?

- A. The tiered policy demonstrated in section 1.
- B. What information a real approval interface should show a reviewer, a real audit trail, and what happens if a pending approval is never resolved — left as a natural extension or bordering on M8-L13.
- C. The genuine wait for a human decision demonstrated in section 2.
- D. The escalation-from-uncertainty distinction demonstrated in section 3.

**Q12.** What is the general lesson this lab demonstrates about human approval and escalation?

- A. Every action should always require human approval, with no exceptions, to maximize safety.
- B. Human approval gates provide no measurable benefit over fully automated decisions.
- C. A tiered approval policy — reserving human review for genuinely high-blast-radius or uncertain cases — provides real scrutiny where it matters, while a blanket policy measurably dilutes that scrutiny across too many routine cases.
- D. Escalation should never be used, since automated classification is always sufficient.

**Q13.** *(Written, rubric-graded.)* In under 150 words: your team's agent currently requires human
approval for every action it takes, and reviewers are falling behind. Based on this lesson, what would you
propose, and why?

---

## 12. Revision notes

- **A tiered policy applies M5-L08's blast-radius principle to deciding WHO decides** — measured directly:
  20 requests sorted into auto-approve, human approval, and senior escalation tiers, with only 6 needing
  any human involvement.
- **A genuine approval gate blocks the action until a real decision is recorded** — measured directly: a
  gated request returned a pending state with no refund issued, contrasted against an ungated call
  succeeding immediately.
- **Escalation from classification uncertainty is a different trigger than escalation from high blast
  radius** — measured directly: a missing amount and an unsupported currency both escalated for a reason
  unrelated to the size of any number.
- **"Approve everything" has a real, computed cost, not just a vague fatigue risk** — measured directly:
  20 required approvals under a blanket policy versus 6 under a tiered one, a 70% reduction.
- **A human approval gate's value depends on a human actually scrutinizing what reaches them** — routing
  too much through it dilutes that scrutiny rather than adding safety uniformly.

---

## 13. Completion checklist

- [ ] I can design a tiered approval policy based on blast radius.
- [ ] I can implement an approval gate that genuinely blocks an action until a decision is recorded.
- [ ] I can distinguish escalation from high blast radius from escalation from classification uncertainty.
- [ ] I can measure the real cost of a blanket approval policy versus a tiered one.
- [ ] I can identify, from a described incident, whether an approval gate was missing, bypassed, or
      overwhelmed by volume.
- [ ] I reserve human approval for genuinely high-stakes or uncertain cases, not every action by default.
- [ ] I scored 10/13 on the quiz.

---

## 14. References

- M5-L08's own blast-radius and gating principle, extended directly to human-decision gates in this
  lesson. `[STABLE]`
- M7-L13's abstention principle, applied here to escalation from classification uncertainty. `[STABLE]`

---

## 15. Next lesson

→ M8-L11 — Read-Only vs State-Changing Actions

This lesson decided when a human should decide. Next: a more fundamental distinction underneath it — which
actions can be undone by simply not repeating them, and which permanently change something the moment they
run.
