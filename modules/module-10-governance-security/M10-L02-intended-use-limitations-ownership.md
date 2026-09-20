# M10-L02 — Intended Use, Limitations and System Ownership

| | |
|---|---|
| **Lesson ID** | M10-L02 |
| **Difficulty** | 2 (Intermediate) |
| **Estimated study time** | 1.5 hours |
| **Prerequisites** | [M10-L01](M10-L01-governance-safety-security-compliance.md) |

---

## 1. Learning objectives

1. **Write** an intended-use statement with the ten fields every later governance artefact refers back to.
2. **Derive** an out-of-scope list from it, and **measure** what happens to real requests with and without one.
3. **Explain** why enforcing scope needs more than keyword rules, in both error directions.
4. **Assign** an owner to every control, and spot unowned controls and overloaded owners.
5. **Keep** the statement true: surface limitations where they are used, and re-review on change, not only on a calendar.

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **Intended use** | What the system is for: purpose, users, inputs, outputs, and the decisions it affects. |
| **Out-of-scope list** | Uses the owner has decided the system must not serve, written down before launch. |
| **Limitation** | A known way the system is worse, or blind, that a user relying on it should know. |
| **Accountable owner** | The named individual answerable for the system's behaviour and for accepting its residual risk. |
| **Control owner** | The named individual responsible for one specific control working. |
| **Staleness** | The gap between what the statement says and what the system now does. |
| **Fail safe** | When unsure, take the cautious branch — here, route to a human rather than answer. |

---

## 3. Plain-language explanation

### 3.1 "Helps the team work faster" cannot be governed

§7.1 scores three intended-use statements against ten required fields. A marketing one-liner scores **2/10**; a
statement written by the build team scores **6/10**, missing exactly the fields governance needs later — which decisions
it affects, what is out of scope, what human oversight exists, when it was last reviewed. The complete version scores
**10/10** and reads like an engineering document, because it is one.

Every later artefact in this module refers back to these fields: the risk register to *decisions affected*, the
evaluation gates to *limitations*, the incident plan to *owner*, the card to all of them.

### 3.2 An out-of-scope list is a design input, not a disclaimer

§7.2 takes 20 realistic requests for a refund-drafting assistant. **13 are outside the stated scope** — legal threats,
B2B accounts, goodwill requests, data-deletion requests, amounts over the limit. With no scope check, the assistant
handles all 13. With the out-of-scope list turned into rules, it routes all 13 to a human and refuses none of the valid
seven.

### 3.3 …and the enforcement is harder than the list

The same rules meet **six held-out requests written afterwards**, in the words customers actually use. They **miss 4**
("GBP 250 back", "our company account", "solicitor will be in touch", "gift card instead") and **wrongly refuse 1** (an
in-scope refund whose text happens to mention the CEO). The statement is the governance artefact; enforcing it needs a
classifier that fails safe or a human triage step — and monitoring of both error directions (M10-L12).

### 3.4 Owners, and what happens without them

§7.3 lists ten controls for the same system. **Three have no owner** — prompt versioning, subgroup monitoring and the
AI-disclosure — and one engineer owns **four**. An unowned control is one nobody will notice failing; a single owner
holding half of them is the same problem wearing a name badge.

### 3.5 Limitations nobody sees, statements nobody updates

§7.4: of five recorded limitations, **four are visible only in internal documents** — including "drafts are
AI-generated". §7.5: after four ordinary changes (a model swap, a new data source, auto-send for small refunds, a
retention change), **6 of 10 fields** of a complete statement no longer describe the system.

---

## 4. Analogy

**A ladder's rating label.** It states the maximum load, the surfaces it may stand on, and that it is not for
electrical work. That label is the intended-use statement, and it is written before the ladder is sold, not after
someone falls. The out-of-scope list is "not for electrical work" — a decision, not a disclaimer. The limitations
matter where they are visible: a label inside a box in a warehouse protects nobody. And when the manufacturer changes
the alloy, the rating has to be re-checked, not carried over.

### Where the analogy breaks

- **A ladder's capability is fixed; an AI system's changes with every model, prompt and data update.** That is why §7.5
  ties review to change events rather than an annual cycle.
- **Nobody expects a ladder to decide whether it should be used.** An assistant *can* be asked to judge whether a request
  is in scope — and §7.2 shows why that judgement must fail safe rather than guess.

---

## 5. Detailed technical explanation

### 5.1 The ten fields

| Field | Why it exists | Used later by |
|---|---|---|
| `purpose` | The narrow thing it does | Everything |
| `users` | Who uses it, in what setting | L09 transparency, L08 subgroups |
| `inputs` | What it reads, and from where | L05 provenance, L06 personal data |
| `outputs` | What it produces, in what form | L12 gates, L15 card |
| `decisions_affected` | What changes in the world as a result | L04 risk register |
| `out_of_scope` | Uses it must not serve | This lesson, L12 |
| `limitations` | Known weaknesses and blind spots | L09, L12, L15 |
| `human_oversight` | Who checks what, and when | L09, M8-L10 |
| `owner` | The named accountable individual | L14 incidents, L16 residual risk |
| `reviewed_on` | When this was last true | L13, L14 |

`[REAL, measured]` §7.1: 2/10, 6/10 and 10/10 for the three statements. The build team's version is the common case: it
describes the system accurately but omits the fields that make it **reviewable**.

Two properties make a statement useful rather than decorative:

- **Falsifiable.** "Drafts refund emails for delivery-failure complaints under £100" can be tested; "helps agents work
  faster" cannot.
- **Bounded.** The out-of-scope list is as important as the purpose, because models will attempt anything asked of them.

### 5.2 Scope enforcement, and both error directions

`[REAL, measured]` §7.2, 20 in-sample requests: no check → **13 out-of-scope handled**; explicit rules → **0** handled,
**0** valid requests refused. On **6 held-out** requests: **4 missed**, **1 wrongly refused**.

The two error directions have different costs and different owners:

| Error | Example | Cost | Mitigation |
|---|---|---|---|
| Out-of-scope handled | Assistant drafts a reply to a legal threat | The harm the scope existed to prevent | Fail safe: route to human when unsure; enforce hard limits in tools (M9-L13) |
| In-scope refused | Valid refund routed to a queue | Slower service, user frustration, shadow workarounds | Monitor refusal rate; review refusals weekly |

Practical enforcement, in increasing strength:

1. **Hard constraints in code** — the £100 limit lives in the refund tool, not the prompt (M9-L13).
2. **A scope classifier** with a "not sure" band that routes to a human, measured on a labelled set like any other
   classifier (M3-L14) and monitored for drift.
3. **The model's own refusal**, prompted with the out-of-scope list — helpful, but the weakest layer, since the same
   channel carries the user's text (M5-L13).

### 5.3 Ownership

`[REAL, measured]` §7.3: 3/10 controls unowned; one engineer owns 4.

- **Accountable owner** (one per system): answers for behaviour, accepts residual risk (L16), is called in an incident
  (L14). A named individual, with a named deputy.
- **Control owners** (one per control): keep that control working and evidenced (L13).
- Review the ownership list when people change roles. "The team" is not an owner; a rota is not an owner; a Slack
  channel is definitely not an owner.

A useful test: for each control, ask **"who gets paged when this fails, and how would they know?"** If the answer is
nobody or "we'd notice", it is unowned.

### 5.4 Limitations must be visible where they are used

`[REAL, measured]` §7.4: 4/5 limitations appear only in internal documents.

Match each limitation to the moment it matters:

| Limitation | Where it must appear |
|---|---|
| Weaker on non-English emails | Agent UI, at draft time, with a prompt to check |
| Policy may be 24 hours stale | Next to the quoted clause, with its timestamp |
| Drafts are AI-generated | The agent UI, and — if the organisation decides so — the customer-facing footer (L09) |
| Refunds over £100 out of scope | The refusal message, in the words a user needs |

A limitation recorded only in a model card changes nobody's behaviour at the moment of use.

### 5.5 Keeping the statement true

`[REAL, measured]` §7.5: four ordinary changes made **6/10 fields** wrong. Tie re-review to **change events**:

- a model or provider change (limitations, outputs);
- a new data source or new user population (inputs, users, out-of-scope);
- any new automated action, or a widened one (human oversight, decisions affected);
- a retention, contract or policy change (limitations, compliance sign-off).

Put the statement under version control next to the code, require the owner's approval on change (L13), and record the
review date. A quarterly calendar review is a backstop, not the mechanism.

### 5.6 Assumptions and limitations

- The scope rules in §7.2 are keyword matches, deliberately weak, to make the held-out failure visible. Production scope
  checks need a measured classifier and a human path.
- The ten fields are a practical superset drawn from common documentation practice; specific frameworks and regulators
  ask for more (L15, L16).
- Ownership modelling here ignores organisational reality — holidays, reorganisations, contractors — which is exactly
  what deputies and review cycles are for.

---

## 6. Worked example — the assistant that grew three new jobs

**The situation.** A logistics company shipped an assistant to answer "where is my parcel?" questions. Its intended-use
statement said: *"Answers parcel-status questions for consumer customers in the UK."* It worked well, and over nine
months it acquired three new jobs by accretion: a colleague added the returns policy to its retrieval index; a sales
team pointed it at the B2B customer portal; and someone enabled a tool that could re-book a delivery.

**What went wrong.** A B2B customer asked to re-book a pallet delivery. The assistant re-booked it — into a consumer
courier slot that could not carry pallets. The pallet was returned to the depot, the customer's production line stopped,
and the contract's service credits were triggered.

**Reading it through the artefact.**

1. **The statement was never updated** (§5.5). Every one of the three additions changed `users`, `inputs` or
   `decisions_affected`, and none triggered a re-review.
2. **There was no out-of-scope list** (§5.2). "Consumer customers in the UK" implies B2B is out, but nothing said so, so
   nothing enforced it.
3. **The new action had no owner** (§5.3). The re-booking tool was added by a team that did not own the assistant; the
   assistant's owner learned of it during the incident.
4. **A limitation existed but was invisible** (§5.4): the courier integration could not handle pallets, which was known
   to the integration team and stated nowhere the assistant or its users could see.

| # | Fix | Artefact |
|---|---|---|
| 1 | Re-review the statement on every data-source, user-population or action change | This lesson, L14 |
| 2 | Write an explicit out-of-scope list, enforced in the tool, not the prompt | §5.2, M9-L13 |
| 3 | One accountable owner for the assistant; no new tools without their approval | §5.3 |
| 4 | Surface capability limits at the point of action, and refuse unsupported combinations | §5.4 |

**The general rule.** **Systems acquire new jobs quietly; statements have to be re-approved loudly.**

---

## 7. Practical activity

**File:** [`labs/m10/l02_intended_use_ownership.py`](../../labs/m10/l02_intended_use_ownership.py)

**No API key, no network, no third-party dependencies.**

```bash
source .venv/bin/activate
python labs/m10/l02_intended_use_ownership.py
```

### 7.2 Expected output

`[EXECUTED]` — 2026-09-16, Python 3.12.3 (pure standard library). Run twice; output identical.

```text

============================================================================
1. COMPLETENESS OF THE INTENDED-USE STATEMENT
============================================================================
  marketing one-liner               :  2/10 fields   missing: inputs, outputs, decisions_affected, out_of_scope...
  partial, written by the build team:  6/10 fields   missing: decisions_affected, out_of_scope, human_oversight, reviewed_on
  complete                          : 10/10 fields   complete

  'Helps our support team work faster' cannot be reviewed, tested, or
  refused against. Every later artefact in this module refers back to these
  fields: the risk register to decisions_affected, the gates to limitations,
  the incident plan to owner.

============================================================================
2. WHAT AN OUT-OF-SCOPE LIST DOES TO REAL REQUESTS
============================================================================
  20 requests, of which 13 are outside the stated scope.
    no scope check         : 13 out-of-scope requests handled by the assistant
    explicit out-of-scope list: 0 handled, 0 in-scope request(s) wrongly refused

  Out-of-scope requests routed to a human:
    - Customer wants GBP 300 refunded for a late delivery        (amount above GBP 100)
    - Customer is threatening legal action over a delivery       (dispute or legal)
    - B2B account asks for a credit note                         (B2B account)
    - Customer asks for a goodwill refund because they changed t (goodwill or change of mind)
    - Customer asks to close their account and delete their data (not a delivery-failure refund)
    - Customer asks whether their parcel is insured              (not a delivery-failure refund)
    - Customer asks for compensation for missing a job interview (not a delivery-failure refund)
    - Delivery failed for an order placed in the German store    (non-UK entity)
    - Customer disputes a refund already issued                  (dispute or legal)
    - Customer asks for a refund on a subscription               (not a delivery-failure refund)
    - Delivery failed but the customer wants store credit instea (not a delivery-failure refund)
    - Customer asks for the CEO's email address                  (not a delivery-failure refund)
    - Delivery failed, order GBP 150                             (amount above GBP 100)

  The same rules on 6 held-out requests written afterwards:
    out-of-scope requests the rules MISSED : 4  e.g. Customer wants GBP 250 back for a late parcel
    in-scope requests wrongly REFUSED      : 1  e.g. Delivery failed, order GBP 30; customer says our CEO would be embarrassed
  Keyword rules encode the examples you thought of. The scope statement is the
  governance artefact; enforcing it needs a classifier that fails safe, or a
  human triage step, and monitoring of both error directions (M10-L12).

============================================================================
3. OWNERSHIP: UNOWNED CONTROLS AND OVERLOADED OWNERS
============================================================================
  controls with no owner: 3/10
    - Prompt version pinned and reviewed
    - Subgroup refusal-rate monitoring
    - Disclosure that drafts are AI-generated

  owner load:
    Support Platform engineer (A. Okafor)    4 control(s)
    Privacy office (S. Blum)                 2 control(s)
    Applied science (R. Mehta)               1 control(s)

  An unowned control is a control nobody will notice failing. One person
  holding half of them is a single point of failure for the same reason.

============================================================================
4. LIMITATIONS: WRITTEN DOWN VS ACTUALLY SURFACED
============================================================================
  [ HIDDEN] Weaker on emails not written in English              in: internal doc, model card
  [ HIDDEN] Cannot see payment-provider status                   in: internal doc
  [ HIDDEN] Policy document may be up to 24 hours out of date    in: nowhere
  [visible] Refunds over GBP 100 are out of scope                in: agent UI, internal doc, model card, refusal message
  [ HIDDEN] Drafts are AI-generated                              in: internal doc

  4/5 limitations are recorded but never reach the person relying on the output.
  A limitation only changes behaviour where it is visible at the moment of use (M10-L09).

============================================================================
5. STALENESS: THE SYSTEM CHANGED, THE STATEMENT DID NOT
============================================================================
  Model swapped to a cheaper provider          -> now describes reality wrongly: limitations, outputs
  German store connected as a data source      -> now describes reality wrongly: users, out_of_scope
  Auto-send enabled for refunds under GBP 20   -> now describes reality wrongly: human_oversight, decisions_affected
  Retention shortened from 3 years to 90 days  -> now describes reality wrongly: limitations

  after four ordinary changes, 6/10 fields of the statement are out of date
  last reviewed: 2026-08-01  -- a quarterly review would have caught three of these late.
  Tie the review to CHANGES, not only to the calendar: a model swap, a new
  data source, or a new automated action should each require re-approval (M10-L14).

============================================================================
6. WHAT THIS LAB IS AND IS NOT
============================================================================
  REAL: every count above is computed from the statements, requests, controls,
  limitations and changes encoded in this file.

  ILLUSTRATIVE: the scope rules are keyword matches standing in for a real
  classifier or a human triage step; a production system needs a far better
  scope check than string matching, and must fail safe when unsure.

  NOT SHOWN: how to decide the scope in the first place (M14-L01, M14-L07) and
  how the statement becomes a public-facing card (M10-L15).

Done.
```

### 7.3 Reading the result

**Section 1's middle row is the one to recognise.** The build team's statement is accurate and still unusable for
governance, because the missing fields are exactly the ones others need.

**Section 2's held-out block is the honest half.** Rules written against examples you have seen will fail on the ones you
have not.

**Section 5 quantifies drift.** Nothing unusual happened — a model swap, a new market, an automation, a retention change —
and most of the statement stopped being true.

---

## 8. Common mistakes and troubleshooting

1. **A purpose statement that cannot be falsified.** §5.1.
2. **No out-of-scope list**, or one written as a disclaimer rather than enforced. §5.2.
3. **Enforcing scope with keywords and calling it done.** §5.2 — 4/6 held-out misses.
4. **Monitoring only one error direction** (usually the embarrassing one). §5.2.
5. **Controls with no named owner**, or one owner holding most of them. §5.3.
6. **Limitations recorded only in a card or wiki.** §5.4.
7. **Re-reviewing on a calendar while the system changes weekly.** §5.5, §6.

| Symptom | Likely cause | Fix |
|---|---|---|
| The system is used for things nobody planned | No out-of-scope list; no re-review on change | Write and enforce it; tie review to change events |
| Users complain it "refuses normal requests" | Scope enforcement too crude in the other direction | Measure both error rates; add a human path |
| A control quietly stopped working | No owner, no evidence | Assign an owner and a check (L13) |
| Users are surprised by a known weakness | Limitation not surfaced at the point of use | Put it in the UI and the refusal message |
| Documentation contradicts the system | Statement not updated after changes | Version it with the code; approve on change |

---

## 9. Security, privacy, reliability, cost

- **Security.** The out-of-scope list is a security input: it bounds what tools the system needs at all, which bounds what
  an attacker can reach (M9-L13).
- **Privacy.** `inputs` and `limitations` are where personal-data questions start (L06); a new data source is a privacy
  change, not just an engineering one.
- **Reliability.** Scope creep is the most common cause of "it used to work" — the system did not change, its job did.
- **Cost.** Routing out-of-scope requests to humans has a real cost; measuring both error directions is how you tune it
  rather than guess.

---

## 10. Exercises

### Exercise 1 — Beginner (~20 min)

1. List the ten fields and say which artefact later in this module uses each.
2. Rewrite "an AI assistant that helps our support team work faster" as a falsifiable purpose.
3. Give two examples of out-of-scope uses for a system you know, and say how each would be enforced.
4. Why is "the platform team" not an owner?
5. Which of §7.4's limitations would you surface in a UI, and where exactly?

### Exercise 2 — Intermediate (~40 min)

1. Run the lab. Add four held-out requests of your own and re-measure both error directions.
2. Add a "not sure" band to `in_scope()` that routes to a human, and report three-way counts.
3. Assign owners to the three unowned controls and justify each choice.
4. Extend §7.5 with two more change events and recompute how much of the statement is stale.
5. Write the full ten-field statement for a system you have worked on.

### Exercise 3 — Challenge (~50 min)

1. Replace the keyword rules with a small trained classifier (M3-L09) on a labelled set you write, and report precision
   and recall for both directions, with confidence intervals (M3-L14).
2. Design the approval workflow for adding a new tool to an existing assistant: who approves, what evidence, what
   re-review.
3. Write the monitoring plan for scope: what you count, what threshold triggers a review, and who sees it.
4. Draft a one-page template your team would fill in for every AI feature, and test it on two real features.
5. Propose how an intended-use statement should be published to users versus kept internal, and what differs.

---

## 11. Quiz

*(Answers: [`answer-keys/module-10-answers.md`](../../answer-keys/module-10-answers.md#m10-l02).)*

**Q1.** Which field does a build-team statement most often omit, per §7.1?

- A. The purpose of the system
- B. Which decisions the system affects
- C. The inputs the system reads
- D. The outputs the system produces

**Q2.** What is an out-of-scope list for?

- A. Limiting the model provider's liability
- B. Listing features planned for later
- C. Recording user complaints about refusals
- D. Recording uses the system must not serve

**Q3.** In §7.2, how many of the 20 in-sample requests were outside the stated scope?

- A. 13 of 20 requests
- B. 7 of 20 requests
- C. 4 of 20 requests
- D. 20 of 20 requests

**Q4.** What did the held-out requests show about keyword scope rules?

- A. They refused every new request
- B. They matched the classifier exactly
- C. They missed 4 and wrongly refused 1
- D. They handled all six correctly

**Q5.** Which enforcement layer is strongest for "refunds over £100 are out of scope"?

- A. A sentence in the system prompt
- B. A line in the model card
- C. A note in the agent's UI
- D. A limit enforced in the refund tool

**Q6.** What makes an intended-use statement reviewable?

- A. It is approved by a legal team
- B. It is falsifiable and bounded
- C. It is short enough to fit on a slide
- D. It is written before any code exists

**Q7.** Per §5.3, what is a good test for whether a control has an owner?

- A. Who gets paged when it fails, and how would they know?
- B. Which team's repository contains the code?
- C. Who wrote the original design document?
- D. Which budget pays for the service?

**Q8.** In §7.4, where were most limitations recorded?

- A. In the refusal messages
- B. In the customer-facing footer
- C. Only in internal documents
- D. In the agent UI at draft time

**Q9.** Why does that matter?

- A. Cards must list every limitation by law
- B. A limitation changes behaviour only where it is visible in use
- C. Internal documents cannot be version-controlled
- D. Users will otherwise request the limitation be removed

**Q10.** In §7.5, how much of the complete statement was stale after four ordinary changes?

- A. 1 of 10 fields
- B. 3 of 10 fields
- C. 10 of 10 fields
- D. 6 of 10 fields

**Q11.** Which event should trigger re-review of the statement?

- A. The quarterly calendar reminder only
- B. A change to the user interface styling
- C. Connecting a new data source
- D. A change in the on-call rota

**Q12.** In §6, what allowed the assistant to re-book a pallet delivery?

- A. No out-of-scope list, and a tool added without the owner's approval
- B. A model upgrade that changed its behaviour
- C. A customer bypassing authentication
- D. An evaluation set that was too small

**Q13.** *(Written, rubric-graded.)* In under 150 words: write the intended-use statement for an AI feature you know,
covering at least six of the ten fields, and name one limitation and where you would surface it.

---

## 12. Revision notes

- **Ten fields:** purpose, users, inputs, outputs, decisions affected, out of scope, limitations, human oversight, owner,
  reviewed on. Measured completeness: **2/10**, **6/10**, **10/10**.
- **Out-of-scope list:** 13/20 requests were out of scope; rules routed all of them — then **missed 4/6** held-out cases and
  **wrongly refused 1**. Enforce hard limits in code; classify with a fail-safe band; monitor both directions.
- **Ownership:** 3/10 controls unowned, one person owning 4. Test: who gets paged, and how would they know?
- **Limitations:** 4/5 visible only internally. Surface each where it is used.
- **Staleness:** four ordinary changes made **6/10** fields wrong. Re-review on change events, not only the calendar.

---

## 13. Completion checklist

- [ ] I can write a falsifiable, bounded intended-use statement with all ten fields.
- [ ] I derive an out-of-scope list and enforce it in code where it matters.
- [ ] I measure both scope error directions on held-out examples.
- [ ] Every control I rely on has a named owner.
- [ ] My limitations are visible at the point of use, and my statement is re-reviewed on change.
- [ ] I scored at least 10/13 on the quiz.

---

## 14. References

- M9-L13 (enforcement outside the model) — why scope belongs in code, not prompts `[STABLE]`
- M3-L14 (metrics, both error directions) — how to measure a scope classifier `[STABLE]`
- Model card practice for intended use and limitations — see M10-L15, which builds the document `[STABLE]`
- NIST AI RMF "Map" function (context, purpose and boundaries) — see M10-L16 `[UNVERIFIED — checked in M10-L16]`

---

## 15. Next lesson

→ [M10-L03 — AI Inventories](M10-L03-ai-inventories.md) asks the question that precedes all of this at organisation
scale: which AI systems do we actually have, and which ones is nobody looking at?
