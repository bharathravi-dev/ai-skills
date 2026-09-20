# M10-L16 — NIST AI RMF, Legal Requirements vs Voluntary Frameworks, Residual Risk

| | |
|---|---|
| **Lesson ID** | M10-L16 |
| **Difficulty** | 3 (Advanced) |
| **Estimated study time** | 2.25 hours |
| **Prerequisites** | [M10-L04](M10-L04-risk-registers.md), [M10-L14](M10-L14-incident-response-rollback.md), [M10-L15](M10-L15-model-cards-documentation.md) |

> **Not legal advice.** This lesson is about the *engineering* consequences of obligations and frameworks. Which
> obligations apply to you depends on your jurisdiction, your sector and your system, and that question belongs with the
> people who own it — early enough that the answer can change the design.

---

## 1. Learning objectives

1. **Place** the module's controls against a framework's functions, and find the thin column.
2. **Separate** legal obligations from framework expectations from engineering choices, and say which is which.
3. **Compute** residual risk from partial, stacking controls, and show why no control carries a stack alone.
4. **Decide** what happens to residual risk above appetite: reduce, accept in writing, or do not ship.
5. **Explain** why a complete compliance checklist is not evidence that a system is safe.

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **NIST AI RMF** | A voluntary US framework organising AI risk practice into four functions: GOVERN, MAP, MEASURE, MANAGE. |
| **ISO/IEC 42001** | A certifiable management-system standard for AI — a structure for running the practice, not a set of controls. |
| **Legal obligation** | Something you must do, enforceable, jurisdiction- and sector-specific. |
| **Framework expectation** | Something a voluntary framework asks for; strong evidence of good practice, not enforceable in itself. |
| **Engineering choice** | A practice you adopt because it works; no framework prescribes it. |
| **Inherent risk** | Likelihood and impact before controls. |
| **Residual risk** | What remains after controls, because no control is perfect. |
| **Risk appetite** | The residual level the organisation has decided it will tolerate, per risk tier. |
| **Risk acceptance** | A named person recording, in writing, that they accept a residual risk, with a review date. |

---

## 3. Plain-language explanation

### 3.1 A framework is a list of questions; the controls are yours

§7.1 maps this module's 16 lessons onto the four AI RMF functions. GOVERN is covered by **8** lessons, MAP by **7**,
MANAGE by **7**, and **MEASURE by 3**. That shape is the usual one: writing a policy is easier than measuring whether it
works. The framework's value is that it makes the thin column visible.

### 3.2 Three different kinds of "must"

§7.2 classifies twelve statements: **4 legal obligations**, **4 framework expectations**, **4 engineering choices**.
Deletion on request is an obligation. Keeping an AI inventory is an expectation. Pinning model versions is a choice
nobody requires and everybody should make.

Two failure modes are equally common: treating a choice as an obligation ("the framework says we must"), which wastes
effort and credibility; and treating an obligation as a choice ("we'll do deletion later"), which is how systems get
switched off.

### 3.3 Residual risk is never zero, and controls multiply

§7.3 stacks five partial controls against a 40%-per-year inherent likelihood: 40% → 26% → 7.8% → 3.9% → 1.56% →
**1.09%**. Removing just the strongest control raises the residual to **3.64% — 3.3× higher**. Stacking works *because*
independent partial controls multiply; the same arithmetic says one strong control cannot carry the stack.

### 3.4 What is left has to be owned

§7.4 compares residual risk to appetite across six register rows: **3 of 6 exceed it**. Each has three honest endings —
reduce it, accept it in writing with a named person and a review date, or do not ship. "We are aware of it" is not one.

### 3.5 Compliant and unsafe at the same time

§7.5 shows a system scoring **8/8** on a governance checklist while **0 of 4** of its actual controls work: gates on a
90-question set that cannot detect what they gate, no slice gate, an agent that emails customers without approval, and a
7-day audit log against a 36-day complaint lag. The checklist asks whether an artefact **exists**; only a measurement asks
whether the control **works**.

---

## 4. Analogy

**Building regulations and a survey.** Regulations set a floor: fire doors, insulation values, wiring standards. A
completion certificate says the boxes were ticked on the day. It does not say the house is dry, warm or well built — for
that you pay a surveyor to *measure*, and you still accept residual risk when you buy, knowingly, in writing, at a price.

### Where the analogy breaks

- **Building regulations are specific and settled; AI obligations are being written while you deploy.** Designs must
  survive the rules changing, which is why L02's scope statement and L13's records matter more than any checklist (§5.2).
- **A house is inspected once; your system changes weekly.** Compliance is a continuous property here, and the only
  practical form of it is the automated gate (L12) and the CI check (L15).

---

## 5. Detailed technical explanation

### 5.1 Frameworks, and how to use one

`[REAL, mapped]` §7.1 — GOVERN 8, MAP 7, MEASURE 3, MANAGE 7 across sixteen lessons.

**NIST AI RMF 1.0** (January 2023) organises practice into four functions `[STABLE]`:

| Function | Asks | Lessons here |
|---|---|---|
| **GOVERN** | Who is accountable, what are the policies, how is this overseen? | L01, L02, L03, L09, L11, L13, L15, L16 |
| **MAP** | What is this system, in what context, with what risks? | L02, L03, L04, L05, L06, L10, L11 |
| **MEASURE** | How do we know it works, for whom, and how would we notice it stopped? | L08, L12, L13 |
| **MANAGE** | What do we do about what we found, and when it goes wrong? | L04, L06, L07, L09, L10, L12, L14 |

`[VERIFIED 2026-09-16 at nist.gov/itl/ai-risk-management-framework]`: AI RMF 1.0 is accompanied by an **AI RMF Playbook**,
a **Generative AI Profile** (NIST-AI-600-1), and is **currently being revised** as part of the US AI Action Plan — so
check the current version rather than citing 1.0 from memory.

**ISO/IEC 42001** is a different shape: a management-system standard, certifiable, concerned with whether you run the
practice consistently — policies, roles, competence, internal audit, continual improvement. A framework tells you what
questions to answer; a management-system standard tells you how to keep answering them.

The practical use of either is **gap analysis**: map what you already do (L01–L15), find the thin column, fix the gap that
matters. Not: adopt the framework's vocabulary and produce documents.

### 5.2 Obligation, expectation, choice

`[REAL, classified — ILLUSTRATIVE and jurisdiction-dependent]` §7.2 — 4 / 4 / 4.

| Kind | Test | Consequence of getting it wrong |
|---|---|---|
| **Legal obligation** | Enforceable against your organisation, in your jurisdiction, for this system | Enforcement, liability, being switched off |
| **Framework expectation** | A voluntary framework or standard asks for it | Weak evidence in a review; a customer may require it contractually |
| **Engineering choice** | It works; nobody requires it | Incidents you could have avoided |

Three engineering habits follow:

1. **Ask early.** "Is this system in scope for X?" is a design input, not a launch-week form. The answer can change the
   architecture (where data lives, whether a human must decide, what you must be able to delete).
2. **Build the capability, not the paperwork.** Deletion on request needs a deletion path that reaches indexes, caches and
   logs (L06, L13) — that is engineering work with a lead time.
3. **Record which is which.** In the risk register (L04) and the system card (L15), say whether a control exists because of
   an obligation, an expectation or a choice. It makes the next trade-off conversation honest.

Contractual obligations behave like legal ones for engineering purposes: a customer's DPA or security schedule can bind
you more tightly than any statute (L11).

### 5.3 Residual risk arithmetic

`[REAL, computed — ILLUSTRATIVE figures]` §7.3.

```text
residual = inherent × Π (1 − effectiveness_i)      for independent controls
```

40% → **1.09%** across five controls; remove the strongest and it is **3.64%**, 3.3× higher.

Three cautions the arithmetic hides:

- **Independence is an assumption.** Controls that share a failure mode do not multiply. If four of your five controls
  depend on the same identity service, they are closer to one control (M9-L13).
- **Effectiveness figures are estimates.** Take them from your own incident history and testing, not from a vendor's
  claim, and mark them as estimates.
- **Impact does not shrink with likelihood.** Controls usually reduce likelihood; reducing *impact* needs a different kind
  of control — blast-radius limits, approval gates, tenant isolation (L07, L14).

### 5.4 Appetite, and the three honest endings

`[REAL, computed]` §7.4 — 3 of 6 rows above appetite.

Risk appetite is a decision, made in advance, per tier, by people accountable for the system. It is what stops "is this
acceptable?" being argued afresh under launch pressure.

```text
Residual above appetite  ->  exactly three endings:
  1. REDUCE      add or strengthen a control; re-measure the residual
  2. ACCEPT      a named person, in writing, with a reason and a review date
  3. DO NOT SHIP  or ship a reduced scope that removes the risk (L02)
```

The acceptance record is a governance artefact with teeth: it names someone, it expires, and it appears in the register
(L04) and the card (L15). The seniority of the accepter scales with the tier — a cross-tenant exposure risk is not
accepted by whoever wrote the code.

### 5.5 Compliance is a floor, not a goal

`[REAL, counted]` §7.5 — 8/8 checklist items, 0/4 effective controls.

| The checklist asks | The measurement asks |
|---|---|
| Is there a risk assessment? | Does the register contain the risks that actually occurred? (L04, L14) |
| Are release gates defined? | Can the evaluation set detect the difference the gate claims? (L12) |
| Is there an incident process? | What was the last measured time-to-detect? (L14) |
| Is a system card published? | Does it match the deployed configuration? (L15) |
| Is access controlled? | Did the isolation test suite pass this week? (L07) |

Both matter. The checklist gives you shared vocabulary, a floor and an audit trail. It is a poor proxy for safety because
it is cheap to satisfy without changing anything — which is exactly why the measurement column exists.

### 5.6 What to do on Monday

1. Map your current practice to a framework's functions; find the thin column (§5.1).
2. Ask which statements in your context are obligations; write the list down with a date (§5.2).
3. For your top five register rows, estimate residual risk explicitly and compare it with appetite (§5.3, §5.4).
4. For every row above appetite, produce one of the three endings, with a name and a date (§5.4).
5. For every checklist item you already pass, write the measurement that would show it works (§5.5).

### 5.7 Assumptions and limitations

- Every likelihood, effectiveness figure and appetite threshold in the lab is invented.
- The obligation/expectation/choice classification in §7.2 is illustrative and jurisdiction-dependent — it is a *method*,
  not a legal reference.
- Framework contents change; AI RMF 1.0 is under revision, and sector rules evolve faster than course material.

---

## 6. Worked example — the review that passed and the system that failed

**The situation.** A regulated-adjacent business ran a governance review before launching an assistant. Every artefact
existed: inventory entry, intended-use statement, impact assessment, system card, supplier assessment, gate definitions,
incident runbook, training records. The review passed with no findings.

**Ten weeks later**, a customer complaint escalated into an investigation.

1. The release gates existed and ran — on **90 questions**, with a minimum detectable effect of about **11 points**
   (L12 §5.5). They had never failed, and could not have.
2. No slice gate existed. The complained-about population was **4%** of the evaluation set (L08).
3. The agent could email customers without approval. The runbook covered rollback; the emails were a one-way door
   (L14 §5.4).
4. The audit log retained **7 days**. The complaint arrived at **36** (L13 §5.6). The team could not say what had been
   retrieved or sent.
5. The review's checklist had asked whether each artefact existed. All four answers were yes.

| # | Checklist said | Measurement would have said |
|---|---|---|
| 1 | Gates defined | Gate cannot detect the effect it gates on |
| 2 | Evaluation performed | No slice gate; 4% population invisible |
| 3 | Incident process documented | No mitigation exists for the irreversible action |
| 4 | Logging enabled | Retention shorter than the complaint lag |
| 5 | Risks assessed | Register had no row for this failure mode |

**The general rule.** **Ask of every control: what measurement would show this is working? If there is no answer, you have
an artefact, not a control.**

---

## 7. Practical activity

**File:** [`labs/m10/l16_frameworks_residual_risk.py`](../../labs/m10/l16_frameworks_residual_risk.py)

**No API key, no network, no third-party dependencies.** Fully deterministic (no randomness at all).

```bash
source .venv/bin/activate
python labs/m10/l16_frameworks_residual_risk.py
```

### 7.2 Expected output

`[EXECUTED]` — 2026-09-16, Python 3.12.3 (pure standard library). Run twice; output identical.

```text

============================================================================
1. THIS MODULE AGAINST THE FOUR AI RMF FUNCTIONS
============================================================================
  lesson                             GOVERN      MAP  MEASURE   MANAGE
  L01 four disciplines                    x        .        .        .
  L02 intended use, ownership             x        x        .        .
  L03 AI inventories                      x        x        .        .
  L04 risk registers                      .        x        .        x
  L05 provenance, licensing               .        x        .        .
  L06 personal data                       .        x        .        x
  L07 access control                      .        .        .        x
  L08 bias, subgroups                     .        .        x        .
  L09 transparency, oversight             x        .        .        x
  L10 security threat model               .        x        .        x
  L11 supplier assessment                 x        x        .        .
  L12 release gates                       .        .        x        x
  L13 versioning, audit                   x        .        x        .
  L14 incident response                   .        .        .        x
  L15 model and system cards              x        .        .        .
  L16 frameworks, residual                x        .        .        .

  GOVERN    covered by  8/16 lessons
  MAP       covered by  7/16 lessons
  MEASURE   covered by  3/16 lessons
  MANAGE    covered by  7/16 lessons

  MEASURE is the thinnest column, and that is the usual shape: teams find it
  easier to write policies than to measure whether they work (L08, L12).
  A framework is a checklist of QUESTIONS, not a set of controls -- the
  controls are the lessons.

============================================================================
2. OBLIGATION, EXPECTATION, OR CHOICE?
============================================================================
  statement                                                    kind                    basis
  Personal data needs a lawful basis and a retention period    LEGAL OBLIGATION        data-protection law where you operate; the
  Keep an inventory of AI systems                              framework expectation   ISO/IEC 42001 and AI RMF GOVERN; sometimes
  Gate releases on a per-slice quality threshold               your choice             no framework prescribes your thresholds; y
  Tell users they are interacting with an AI system            LEGAL OBLIGATION        required in several jurisdictions and cont
  Run a risk assessment before deploying a high-impact system  framework expectation   AI RMF MAP, ISO/IEC 42001; obligation in s
  Pin model versions in production                             your choice             pure engineering discipline; no framework 
  Be able to delete a person's data on request                 LEGAL OBLIGATION        data-protection law; drives your deletion 
  Publish a model card                                         your choice             widely expected, rarely required; you deci
  Report a personal-data breach within a defined window        LEGAL OBLIGATION        jurisdiction-specific timing; drives the L
  Evaluate subgroup performance                                framework expectation   AI RMF MEASURE; an obligation where anti-d
  Keep a human in the loop for consequential decisions         framework expectation   obligation in specific regulated decisions
  Use a canary rollout                                         your choice             engineering practice; nothing requires it,

  4 obligations, 4 framework expectations, 4 engineering choices (out of 12)
  Two failure modes, equally common: treating a choice as an obligation ('we
  must, the framework says so') and treating an obligation as a choice ('we
  will do deletion later'). Only the first column is not negotiable -- and
  which statements sit in it depends on YOUR jurisdiction and sector.
  NOTHING HERE IS LEGAL ADVICE: the engineering job is to build the capability
  and to ask the question early enough that the answer can change the design.

============================================================================
3. RESIDUAL RISK: CONTROLS ARE PARTIAL, AND THEY MULTIPLY
============================================================================
  inherent likelihood: 40% per year

  control                                                   reduces by   residual
  input delimiting and provenance marking (M5-L13)                35%     26.00%
  authorization enforced outside the model (L07, M9-L13)          70%      7.80%
  egress allowlist (M9-L12)                                       50%      3.90%
  human approval for state-changing actions (M8-L10)              60%      1.56%
  monitoring and canary rollout (L14)                             30%      1.09%

  five controls, none of them perfect  ->  residual 1.09% per year
  removing the single best control (authorization enforced outside the model):
    residual becomes 3.64%  -- 3.3x higher

  No control is 100%, so residual risk is never zero. Stacking independent
  partial controls works BECAUSE they multiply -- and the same arithmetic
  says one strong control cannot carry the whole stack (L10).

============================================================================
4. WHAT IS LEFT, AND WHO ACCEPTS IT?
============================================================================
  register row                                inherent  controls  residual  appetite   verdict
  R01 cross-tenant data exposure                   30%       97%      0.9%        1%   within appetite
  R02 unsafe advice reaches a user                 45%       88%      5.4%        1%   OVER -> accept or reduce
  R03 agent takes a wrong billing action           35%       90%      3.5%        5%   within appetite
  R04 quality regression on a slice                60%       75%     15.0%        5%   OVER -> accept or reduce
  R05 provider outage, feature down                80%       40%     48.0%       15%   OVER -> accept or reduce
  R06 cost overrun from a retry loop               50%       85%      7.5%       15%   within appetite

  rows above appetite: 3/6
    R02 unsafe advice reaches a user           needs: executive owner + written acceptance
    R04 quality regression on a slice          needs: system owner
    R05 provider outage, feature down          needs: team lead

  Residual risk above appetite has exactly three honest endings: reduce it,
  accept it in writing with a named person and a review date, or do not ship.
  'We are aware of it' is not one of them (L04).

============================================================================
5. COMPLIANT AND STILL UNSAFE
============================================================================
  checklist items complete: 8/8  -> the governance review passes

  what is actually true                               effective?   why it matters
  gates run on a 90-question set (MDE ~11 points)             NO   cannot detect the regressions it gates on
  no per-slice gate; French is 4% of the set                  NO   L08/L12 gap the checklist does not see
  agent can email customers without approval                  NO   one-way door, no approval gate (M8-L10)
  audit log keeps 7 days; complaints arrive at 36             NO   cannot investigate (L13)

  effective controls among the four checked: 0/4
  A checklist asks whether an artefact EXISTS. Only a measurement asks whether
  the control WORKS. Compliance is a floor and a vocabulary; it is not
  evidence of safety, and passing it is not the goal (L01).

============================================================================
6. WHAT THIS LAB IS AND IS NOT
============================================================================
  REAL: every coverage count, residual-risk figure, appetite comparison and
  checklist count above is computed by this script from the encoded values.

  ILLUSTRATIVE: the likelihoods, control effectiveness figures and appetite
  thresholds are invented. Real ones come from your own incident history and
  a decision by the people accountable for the system.

  NOT LEGAL ADVICE: which statements in section 2 are obligations depends on
  your jurisdiction, sector and the system itself. Ask early; the answer
  changes the design, not just the paperwork.

Done.
```

### 7.3 Reading the result

**Section 1's MEASURE column** is the finding, and it is the finding in most real gap analyses too.

**Section 2's three columns** are the conversation teams keep failing to have. Only the first is non-negotiable, and it is
usually the shortest.

**Section 3's last line** — 3.3× from removing one control — is the argument for defence in depth, stated as arithmetic.

**Section 5 is the whole module in one table**: eight artefacts, zero working controls.

---

## 8. Common mistakes and troubleshooting

1. **Adopting a framework's vocabulary instead of doing a gap analysis.** §5.1.
2. **Claiming a choice is an obligation.** §5.2 — it wastes effort and erodes trust when discovered.
3. **Deferring an actual obligation.** §5.2 — deletion paths have long lead times.
4. **Asking the legal question in launch week.** The answer changes the design, not the paperwork.
5. **Treating residual risk as zero once controls are listed.** §5.3 — 1.09%, not 0%.
6. **Assuming controls are independent.** §5.3 — shared dependencies do not multiply.
7. **Reducing likelihood and calling it impact reduction.** §5.3 — blast-radius controls are different controls.
8. **"We are aware of it" as a risk response.** §5.4 — reduce, accept in writing, or do not ship.
9. **Treating a passed checklist as evidence of safety.** §5.5 — 8/8 and 0/4.

| Symptom | Likely cause | Fix |
|---|---|---|
| Lots of documents, recurring incidents | GOVERN-heavy, MEASURE-thin | Gap analysis by function; invest in measurement (L08, L12) |
| Arguments about whether something is required | Obligation/expectation/choice never separated | Write the three-column list with a date and an owner |
| Residual risk "eliminated" | Controls assumed perfect | Estimate effectiveness; compute and publish the residual |
| Risks linger unresolved for months | No appetite and no acceptance path | Set appetite per tier; require named written acceptance |
| A review passes, then an incident follows | Checklist without measurements | For each item, define the measurement that proves it works |

---

## 9. Security, privacy, reliability, cost

- **Security.** Frameworks will not find your exfiltration path; the threat model does (L10). Use the framework to check
  you *have* a threat model, then do the work.
- **Privacy.** This is where obligations bite hardest and lead times are longest: lawful basis, minimisation, retention,
  deletion, transfer (L06). Ask first; build second.
- **Reliability.** Availability risks (R05 in §7.4) are usually the largest residual and the most accepted — deliberately,
  with a named accepter, or by accident.
- **Cost.** Governance effort is finite. Spend it on the thin column and the rows above appetite, not on producing
  documents that already exist in another form (L15 §5.6).

---

## 10. Exercises

### Exercise 1 — Beginner (~20 min)

1. Which AI RMF function is thinnest in §7.1, and why is that typical?
2. Classify three practices from your own team as obligation, expectation or choice.
3. Why is residual risk in §7.3 not zero?
4. How many register rows in §7.4 exceeded appetite, and what are their three endings?
5. Give one measurement for each of two checklist items you currently pass.

### Exercise 2 — Intermediate (~40 min)

1. Run the lab. Add a control at 20% effectiveness and observe how little it moves the residual.
2. Make two controls dependent (a shared identity service) and recompute honestly.
3. Change the appetite tiers and see which rows change verdict.
4. Map your own team's practice to the four functions and find your thin column.
5. Write a risk-acceptance record for one row above appetite, with accepter, reason and review date.

### Exercise 3 — Challenge (~60 min)

1. Run a gap analysis of your organisation against the four functions, with evidence per claim.
2. Produce the three-column obligation/expectation/choice list for one system, and get it reviewed by whoever owns the
   legal question.
3. Estimate control effectiveness from your own incident history rather than assumption, and publish the residuals.
4. Define the risk appetite per tier and the acceptance authority, and get it agreed.
5. For every item on your governance checklist, write the measurement that shows it works — then run them and report
   which controls are artefacts.

---

## 11. Quiz

*(Answers: [`answer-keys/module-10-answers.md`](../../answer-keys/module-10-answers.md#m10-l16).)*

**Q1.** What are the four functions of the NIST AI RMF?

- A. Identify, Protect, Detect, Respond
- B. Plan, Do, Check, Act
- C. Govern, Map, Measure, Manage
- D. Assess, Mitigate, Monitor, Report

**Q2.** In §7.1, which function was covered by the fewest lessons?

- A. GOVERN
- B. MEASURE
- C. MANAGE
- D. MAP

**Q3.** What is the practical use of a framework?

- A. To certify the organisation against an external standard
- B. To provide the controls a system needs
- C. To supply vocabulary for governance documents
- D. Gap analysis — finding which questions you cannot answer

**Q4.** Which of these is an engineering choice rather than an obligation or expectation?

- A. Being able to delete a person's data on request
- B. Reporting a personal-data breach within a defined window
- C. Keeping an inventory of AI systems
- D. Pinning model versions in production

**Q5.** Why does treating a choice as an obligation cause harm?

- A. It wastes effort and erodes trust when discovered
- B. Frameworks prohibit over-implementation
- C. It exposes the organisation to enforcement action
- D. It invalidates the risk register's likelihood estimates

**Q6.** In §7.3, what was the residual likelihood after five controls?

- A. 1.09% per year
- B. 3.64% per year
- C. 0% — the controls were sufficient
- D. 7.80% per year

**Q7.** Why do stacked controls multiply rather than add?

- A. Because impact scales with likelihood
- B. Because the residual after each control is the input to the next
- C. Because frameworks require defence in depth
- D. Because effectiveness is measured as a percentage

**Q8.** When does the multiplication assumption break?

- A. When more than three controls are applied
- B. When controls are applied in a different order
- C. When effectiveness figures come from vendors
- D. When controls share a dependency and fail together

**Q9.** Residual risk exceeds appetite. What are the honest options?

- A. Reduce it, accept it in writing with a named person, or do not ship
- B. Document awareness and proceed
- C. Lower the appetite threshold to match
- D. Re-estimate the likelihood using a different method

**Q10.** Why should the accepter's seniority scale with the risk tier?

- A. Senior approvers estimate likelihood more accurately
- B. Frameworks assign acceptance authority by role
- C. The person accountable for the consequence should be the one accepting it
- D. It shortens the review cycle for low-tier risks

**Q11.** In §7.5, the system scored 8/8 on the checklist. How many of the four examined controls were effective?

- A. Four
- B. None
- C. One
- D. Two

**Q12.** What question distinguishes a control from an artefact?

- A. Is it referenced in the system card?
- B. Which framework function does it satisfy?
- C. What measurement would show it is working?
- D. Who approved it, and when?

**Q13.** *(Written, rubric-graded.)* In under 150 words: your governance review passed with no findings. Describe three
measurements you would run anyway, and what each would tell you that the review did not.

---

## 12. Revision notes

- **A framework is questions, not controls**: GOVERN **8**, MAP **7**, MEASURE **3**, MANAGE **7** across this module —
  MEASURE is the usual thin column.
- **Three kinds of "must"**: **4** obligations, **4** expectations, **4** choices in the lab. Only the first is
  non-negotiable, and it is jurisdiction-specific.
- **Ask the legal question early**: the answer changes the design, and deletion paths have long lead times.
- **Residual is never zero**: 40% → **1.09%** across five partial controls; removing the strongest gives **3.64%**,
  **3.3×** higher.
- **Independence is an assumption**: controls sharing a dependency do not multiply.
- **Above appetite → three endings**: reduce, accept in writing with a name and a review date, or do not ship.
- **Compliance is a floor**: **8/8** checklist items, **0/4** working controls. Ask what measurement proves each control.

---

## 13. Completion checklist

- [ ] I have mapped my practice to a framework's functions and know my thin column.
- [ ] I can say which of my practices are obligations, which expectations, which choices — and ask the question early.
- [ ] I estimate residual risk explicitly, and I state where independence is assumed.
- [ ] Every residual above appetite has been reduced, accepted in writing, or has stopped a launch.
- [ ] For each control I claim, I can name the measurement that shows it works.
- [ ] I scored at least 10/13 on the quiz.

---

## 14. References

- NIST AI Risk Management Framework (AI RMF 1.0, January 2023): GOVERN, MAP, MEASURE, MANAGE; AI RMF Playbook; Generative
  AI Profile (NIST-AI-600-1). AI RMF 1.0 is under revision as part of the US AI Action Plan —
  <https://www.nist.gov/itl/ai-risk-management-framework> `[VERIFIED 2026-09-16]`
- ISO/IEC 42001 — AI management systems; certifiable, process-focused, complementary to the AI RMF `[UNVERIFIED]`
- ISO/IEC 23894 — AI risk-management guidance, aligned with ISO 31000 `[UNVERIFIED]`
- M10-L04 (risk registers, appetite, acceptance) and M10-L01 (why compliance ≠ safety) `[STABLE]`
- M10-L12 (gates), M10-L14 (incidents) and M10-L15 (cards) — the measurements behind the checklist items `[STABLE]`

---

## 15. Next lesson

→ Module 10 ends here. **Project 10** applies it end to end: a risk register, a system card, a release gate and an incident
drill for one system, with residual risk stated and accepted by name.

Module 11 changes register completely — from the practices that decide whether a system *should* run to the infrastructure
that decides whether it *can*:
[M11-L01 — Cloud Computing and the Shared Responsibility Model](../module-11-aws-foundations/M11-L01-cloud-shared-responsibility.md).
Everything in Module 10 reappears there as a concrete control: IAM for access (L07), KMS and S3 policies for data handling
(L06), CloudTrail for auditability (L13), and deployment pipelines for release gates and rollback (L12, L14).
