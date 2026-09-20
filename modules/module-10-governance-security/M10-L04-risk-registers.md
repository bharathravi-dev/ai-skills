# M10-L04 — Risk Registers and Risk Assessment

| | |
|---|---|
| **Lesson ID** | M10-L04 |
| **Difficulty** | 2 (Intermediate) |
| **Estimated study time** | 2.0 hours |
| **Prerequisites** | [M10-L03](M10-L03-ai-inventories.md), [M3-L04](../module-03-math-ml-essentials/M3-L04-probability.md) |

---

## 1. Learning objectives

1. **Write** a risk-register entry with cause, consequence, controls, evidence, owner and residual risk.
2. **Compare** a 5×5 likelihood × impact matrix with an expected-loss ranking, and **explain** why they disagree.
3. **Show** that the impact *scale* — not just the estimates — determines the ranking.
4. **Distinguish** inherent from residual risk, and **discount** controls with no evidence.
5. **Decide** what to do with a risk that remains over appetite: treat, transfer, avoid, or explicitly accept.

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **Risk** | A specific bad outcome, with a cause and a consequence — not a topic ("bias") but an event ("CV screening rejects one group at a higher rate"). |
| **Likelihood** | How often it is expected to happen, as a band or a probability per period. |
| **Impact** | How bad it is if it happens, as a band or a cost. |
| **Inherent risk** | The risk before controls. |
| **Residual risk** | The risk remaining after controls that actually work. |
| **Risk appetite** | The level of residual risk the owner accepts without further action. |
| **Treatment** | Reduce, transfer (insurance/contract), avoid (don't build it), or accept — with a name and a date. |
| **Expected loss** | Probability × cost; a rough single number for comparing unlike risks. |

---

## 3. Plain-language explanation

### 3.1 The register is a ranking tool

A risk register exists to answer one question: *what do we work on first?* Everything else — the columns, the colours —
serves that. Which means the way you score risks decides what gets fixed.

### 3.2 Two scorings, two different answers

§7.1 scores ten AI risks both ways. The 5×5 matrix puts `R10` (staff pasting customer data into a public chatbot) first
and `R3` (CV screening rejecting one group more often) **fourth**. Expected annual loss puts `R3` **first** at £80,000
and `R6` (cross-tenant leak) third, though the matrix ranks `R6` **last**. **9 of 10 positions differ** between the two
rankings.

Neither ranking is "true": the matrix compresses everything into bands, and the expected-loss numbers are estimates. The
point is that a register that shows only one of them is hiding a choice.

### 3.3 The scale is a hidden assumption

§7.2 changes nothing but the meaning of the impact bands — from linear (1–5) to roughly ten-fold steps (1, 10, 100,
1,000, 10,000). **9 of 10 positions change.** Most registers never state whether "catastrophic" is five times "minor" or
ten thousand times, yet multiplying the bands assumes an answer.

### 3.4 Ties hide the work

§7.3: the ten risks occupy just **7 distinct matrix scores**. `R3` (CV screening bias, £80,000 expected loss) and `R5`
(a fabricated policy citation, £2,700) share the same score of 10 — a 30× difference the matrix has discarded.

### 3.5 Controls only count if they can be shown to work

§7.4 computes residual risk twice: crediting every claimed control, and crediting **only controls with evidence** — a
test, a log, a record. Residual rose for **5 of 10** risks, and **1** crossed back over the appetite line. The controls
that vanish are the familiar ones: "policy and training", "the prompt says not to", "contract review on renewal".

---

## 4. Analogy

**Triage in an emergency department.** Patients are not treated in arrival order; they are ranked by how bad it is and
how fast it will get worse. A crude triage score groups very different patients into the same category — and a
department that only records the category, never the underlying observations, cannot explain why one patient waited.
Treatments count only when administered, not when written on the chart. And a patient nobody has accepted responsibility
for is the one who deteriorates in the corridor.

### Where the analogy breaks

- **Triage categories are calibrated against outcomes over millions of patients; AI risk bands are usually invented in a
  workshop.** That is why §7.2's scale sensitivity matters so much here and so little there.
- **A patient's condition is observable; an AI risk's likelihood often is not.** You are estimating with little data,
  which is an argument for ranges, stated assumptions and frequent review — not for more decimal places.

---

## 5. Detailed technical explanation

### 5.1 What an entry contains

| Field | Example |
|---|---|
| Risk (event) | "Assistant issues a refund above policy after prompt injection" |
| Cause | Untrusted customer text reaches the model; limit enforced only in the prompt |
| Consequence | Money lost; customer trust; audit finding |
| Likelihood | 0.30 per year (band 3), with the assumption stated |
| Impact | £25,000 (band 4) |
| Controls + evidence | Server-side limit in the tool (CI test T-114 ✔); "prompt says not to" (no evidence ✘) |
| Inherent / residual | £7,500 → £750 counting evidenced controls only |
| Owner | Named individual |
| Treatment and decision | Reduce; re-test quarterly; accepted by owner on 2026-09-01 |
| Review date | Next review, and the change events that force one early (L02) |

Write the risk as an **event with a cause and a consequence**. "Bias" is not a risk; "CV screening rejects one group at a
higher rate, because the training data reflects past hiring, causing unlawful discrimination and a tribunal claim" is.

### 5.2 Matrix versus expected loss

`[REAL, measured]` §7.1: 9/10 positions differ. Top 3 by matrix: `R1`, `R2`, `R10`. Top 3 by expected loss: `R3`, `R6`,
`R10`.

| Method | Strengths | Weaknesses |
|---|---|---|
| 5×5 matrix | Fast; anyone can fill it in; good for triage | Multiplies ordinal bands; hides scale assumptions; many ties; poor at rare-but-severe risks |
| Expected loss (p × cost) | Comparable across unlike risks; forces explicit assumptions; supports cost-of-control comparisons | Invites false precision; bad at tail risks and at harms that are not money |

Practical approach: use the matrix to **triage**, then compute expected loss (with ranges) for anything in the top band
or with severe consequences, and record the assumptions next to the number. Where the two disagree — `R3` and `R6` here —
that disagreement is the interesting part of the review.

**Rare but catastrophic risks need special handling.** `R6` (cross-tenant leak, 5% × £900,000) ranks last on the matrix
and third on expected loss. Expected value alone under-weights outcomes you cannot survive; treat "unacceptable
regardless of probability" as a separate flag, not a score.

### 5.3 Scale sensitivity

`[REAL, measured]` §7.2: 9/10 positions change when the impact bands are read as ten-fold steps rather than linear ones.

If your register multiplies bands, state what the bands mean in units (money, people affected, hours of downtime, legal
exposure) and check whether the ordering survives a different reasonable scale. If it does not, the ranking is a property
of your scale choice, not of your risks.

### 5.4 Ties, and what they cost

`[REAL, measured]` §7.3: 10 risks, **7 distinct scores**; `R3` and `R5` share a score despite a 30× difference in expected
loss.

Ties matter because registers are used to allocate scarce attention. Break them with the underlying numbers, with
severity flags, or with reversibility — never by row order in a spreadsheet.

### 5.5 Inherent, residual, and the evidence rule

`[REAL, measured]` §7.4, appetite £5,000 expected annual loss per risk:

| Counting | Over appetite |
|---|---|
| Every claimed control | 2/10 |
| Only controls with evidence | **3/10** |

Residual rose for **R1, R3, R4, R7 and R10** when unevidenced controls were discounted.

The rule from M10-L01 applies directly: **a control without evidence is an intention**. For each control record what the
evidence *is* — a CI test id, a monitoring dashboard, an access-review record, an incident drill date — and re-check it
on a schedule. Controls degrade: people leave, tests get skipped, a refactor removes an enforcement point.

Two failure modes to watch:

- **Double counting.** Three controls that all depend on the same mechanism (the same prompt, the same reviewer) are one
  control for risk purposes.
- **Control drift.** The control stays in the register while the system changes around it — the L02 staleness problem,
  applied to controls.

### 5.6 What to do with the risks that remain

Four treatments, and every one needs a name and a date:

1. **Reduce** — add or strengthen a control; re-score with evidence.
2. **Transfer** — insurance, or contractual allocation. Note that reputational and regulatory consequences rarely
   transfer.
3. **Avoid** — change the design or don't ship the feature. Often the right answer for high-tier systems with no
   effective control (L03).
4. **Accept** — record who accepted it, on what date, with what review interval, and what would change the decision.

`[REAL, measured]` §7.5 flags entries where these are missing: `R3` has no owner, no review date, no evidenced control and
no acceptance; `R7` was last reviewed in December 2025; `R10` is over appetite with no recorded acceptance. An
over-appetite risk with no acceptance is not a decision, it is an unanswered question.

### 5.7 Keeping the register honest

- **Re-score on change events** (L02): new model, new data source, new automated action, new user population.
- **Feed incidents back**: an incident is evidence about likelihood, and often reveals a control that did not work (L14).
- **Track near misses**, which are cheaper evidence than incidents.
- **Show the register to the people who would be harmed**, or at least think in their terms — many AI risks are harms to
  users, not costs to you (L08, L09).
- **Keep it short.** A 200-row register nobody reads ranks nothing.

### 5.8 Assumptions and limitations

- Probabilities, costs and control effectiveness in the lab are invented; the arithmetic is real, the inputs are not
  measurements.
- Risks are treated as independent. In reality one incident triggers several (a breach is also a compliance and
  reputational event), and correlated risks need joint treatment.
- Expected loss in money does not capture harm to people. For those, record the harm in its own terms and use severity
  flags rather than converting to currency.

---

## 6. Worked example — the register that ranked the wrong thing first

**The situation.** A recruitment platform kept a 40-row AI risk register scored on a 5×5 matrix. The top three rows for
two quarters were: an outage of the summarisation API, an over-spend on tokens, and a supplier contract lapse. All were
fixed. A candidate then complained that the screening model had rejected them, and an internal review found the model's
recommendation rate for one group was materially lower.

**Reading the register afterwards.**

1. The bias risk was on the register, scored **likelihood 2 (rare) × impact 5 (severe) = 10**, below three operational
   risks scored 12 and 16. On expected loss it was the **largest** risk on the register — §7.1's `R3` pattern exactly.
2. The scoring workshop had used a **linear** impact scale, so "severe" counted as 2.5× "moderate". With a ten-fold
   scale, bias ranked first — §7.2.
3. Its controls were "hiring policy" and "annual fairness review" — **neither evidenced**, and the annual review had not
   run — §7.4.
4. Nobody owned the row: it had been added by a consultant during an assessment and never assigned — §7.5.

| # | Finding | Fix |
|---|---|---|
| 1 | Matrix ranking buried a rare-but-severe risk | Expected-loss ranking for severe rows; separate "unacceptable regardless of probability" flag |
| 2 | Scale assumption unstated | Define bands in units; test the ranking under a second scale |
| 3 | Controls unevidenced and undone | Require an evidence reference per control; discount those without one |
| 4 | No owner, no acceptance | Every row has an owner; over-appetite rows need recorded acceptance or treatment |

**The general rule.** **A register ranks what its scoring method can see.** Check what your method hides before trusting
the order.

---

## 7. Practical activity

**File:** [`labs/m10/l04_risk_register.py`](../../labs/m10/l04_risk_register.py)

**No API key, no network, no third-party dependencies.**

```bash
source .venv/bin/activate
python labs/m10/l04_risk_register.py
```

### 7.2 Expected output

`[EXECUTED]` — 2026-09-16, Python 3.12.3 (pure standard library). Run twice; output identical.

```text

============================================================================
1. MATRIX SCORE VS EXPECTED LOSS
============================================================================
  rank by 5x5 matrix                     by expected annual loss           
  1    R10 (16)                          R3 (GBP 80,000)                   
  2    R1 (12)                           R10 (GBP 66,000)                  
  3    R2 (12)                           R6 (GBP 45,000)                   
  4    R3 (10)                           R1 (GBP 7,500)                    
  5    R5 (10)                           R4 (GBP 7,500)                    
  6    R7 (9)                            R7 (GBP 7,000)                    
  7    R4 (8)                            R2 (GBP 4,800)                    
  8    R8 (6)                            R9 (GBP 4,500)                    
  9    R9 (6)                            R5 (GBP 2,700)                    
  10   R6 (5)                            R8 (GBP 2,400)                    

  9/10 positions differ between the two rankings.
  top 3 by matrix: ['R1', 'R10', 'R2']   top 3 by expected loss: ['R10', 'R3', 'R6']
  in one top 3 but not the other: ['R1', 'R2', 'R3', 'R6']

============================================================================
2. THE SCALE CHANGES THE ANSWER
============================================================================
  rank   linear impact (1-5)      log impact (1,10,100,1k,10k)
  1      R10                      R3
  2      R1                       R6
  3      R2                       R10
  4      R3                       R1
  5      R5                       R2
  6      R7                       R7
  7      R4                       R9
  8      R8                       R5
  9      R9                       R4
  10     R6                       R8

  9/10 positions change when only the impact SCALE changes.
  A 5x5 matrix multiplies two ordinal bands as if they were numbers. Whether
  'catastrophic' is 5x 'minor' or 10,000x decides the order -- and registers
  rarely say which they mean.

============================================================================
3. TIES: DIFFERENT RISKS, IDENTICAL SCORES
============================================================================
  10 risks occupy 7 distinct matrix scores
    score 12: R1, R2
        R1  expected loss GBP   7,500   Assistant issues a refund above policy after prompt 
        R2  expected loss GBP   4,800   Personal data retained beyond the stated period
    score 10: R3, R5
        R3  expected loss GBP  80,000   CV screening rejects one group at a higher rate
        R5  expected loss GBP   2,700   Answer cites a policy clause that does not exist
    score  6: R8, R9
        R8  expected loss GBP   2,400   Agent loops and spends the monthly budget in a day
        R9  expected loss GBP   4,500   Evaluation set leaks into the prompt library

  Two risks sharing a cell are not equally urgent: the matrix has thrown away
  the information that would separate them.

============================================================================
4. INHERENT VS RESIDUAL -- AND CONTROLS WITHOUT EVIDENCE
============================================================================
  appetite: GBP 5,000 expected annual loss per risk

  risk     inherent    residual (claimed)   residual (evidenced only)
  R1          7,500                   525                         750
  R2          4,800                 1,440                       1,440
  R3         80,000                40,000                      80,000   OVER APPETITE
  R4          7,500                 1,500                       3,000
  R5          2,700                   540                         540
  R6         45,000                   450                         450
  R7          7,000                 4,200                       7,000   OVER APPETITE
  R8          2,400                   240                         240
  R9          4,500                 2,250                       2,250
  R10        66,000                18,480                      26,400   OVER APPETITE

  over appetite counting every claimed control : 2/10
  over appetite counting only EVIDENCED controls: 3/10
  residual rose for 5 risk(s) when unevidenced controls were discounted: R1, R3, R4, R7, R10
  and that pushed 1 of them back over the appetite line.

  'Policy and training' and 'prompt says not to' are the usual unevidenced
  controls. Until a test, log or record shows a control working, a register
  that counts it is reporting an intention as a reduction (M10-L01).

============================================================================
5. REGISTER COMPLETENESS
============================================================================
  R1   OK
  R2   OK
  R3   no owner; no review date; no evidenced control; over appetite with no recorded acceptance
  R4   OK
  R5   OK
  R6   OK
  R7   last reviewed 2025-12-01; no evidenced control; over appetite with no recorded acceptance
  R8   OK
  R9   no owner
  R10  over appetite with no recorded acceptance

  A register entry that is over appetite with nobody accepting it is not a
  decision -- it is an unanswered question sitting in a spreadsheet.

============================================================================
6. WHAT THIS LAB IS AND IS NOT
============================================================================
  REAL: every ranking, tie, residual figure and count above is computed from
  the ten encoded risks.

  ILLUSTRATIVE: the probabilities, costs and control effectiveness figures are
  invented. Real registers face the harder problem that these numbers are
  estimates -- which is why the lesson argues for stating ranges and assumptions
  rather than pretending a single score is precise.

  NOT SHOWN: correlated risks (one incident triggering several), risks to
  people rather than to the organisation, and the frameworks that prescribe
  particular scales (M10-L16).

Done.
```

### 7.3 Reading the result

**Section 1's two columns are the same ten risks.** If your register produces only the left column, you are making the
choice the right column would have shown you.

**Section 2 changes nothing about the world** — only the meaning of the bands — and reorders nearly everything.

**Section 4's last two lines are the practical takeaway**: discounting controls you cannot evidence is not pedantry, it
changes which risks are over the line.

---

## 8. Common mistakes and troubleshooting

1. **Recording topics instead of events.** §5.1 — "bias" cannot be scored, caused or controlled.
2. **Multiplying ordinal bands without stating the scale.** §5.3.
3. **Letting ties stand.** §5.4 — 7 scores for 10 risks.
4. **Counting controls that have no evidence.** §5.5 — 5 of 10 residuals rose without them.
5. **Double-counting controls that share a mechanism.** §5.5.
6. **Leaving over-appetite risks with no acceptance or owner.** §5.6.
7. **Registers that only capture costs to the organisation**, not harms to people. §5.7.

| Symptom | Likely cause | Fix |
|---|---|---|
| The same operational risks top the register every quarter | Matrix compresses severe-but-rare risks | Rank severe rows by expected loss; add a severity flag |
| Two very different risks are "equal priority" | Tie in the matrix | Break ties with underlying numbers or reversibility |
| Residual risk looks comfortable, incidents keep happening | Unevidenced or drifted controls | Require evidence references; re-check on a schedule |
| Rows persist for years unchanged | No re-score on change events, no incident feedback | Tie review to changes and incidents |
| Nobody acts on a red row | No owner, no treatment decision | Assign owner; choose reduce/transfer/avoid/accept with a date |

---

## 9. Security, privacy, reliability, cost

- **Security.** Adversarial risks are typically low-likelihood, high-impact — exactly where matrices perform worst (§5.2).
- **Privacy.** Harms to individuals do not convert neatly into expected loss; record them in their own units (people
  affected, sensitivity) and flag severity (L06, L08).
- **Reliability.** Incidents and near misses are the best evidence you will get about likelihood; feed them back (L14).
- **Cost.** Comparing a control's cost with the reduction in expected loss is the one place the money numbers earn their
  keep — provided you state the assumptions.

---

## 10. Exercises

### Exercise 1 — Beginner (~20 min)

1. Rewrite "hallucination" as a risk with a cause and a consequence.
2. Compute expected loss for a risk with p = 0.2 and cost £50,000; where would it sit in §7.1's ranking?
3. Why did `R6` rank last on the matrix and third on expected loss?
4. Which controls in the lab are unevidenced, and what evidence would you require for each?
5. What must accompany an over-appetite risk in the register?

### Exercise 2 — Intermediate (~40 min)

1. Run the lab. Change the appetite to £2,000 and report how many risks are over the line under each counting rule.
2. Add a "reversibility" field (1–3) and produce a third ranking; compare it with the other two.
3. Add two correlated risks (one triggers the other) and describe how you would score them.
4. Change one unevidenced control to evidenced and identify which decisions change.
5. Write full register entries, with evidence references, for two risks in a system you work on.

### Exercise 3 — Challenge (~60 min)

1. Replace point estimates with ranges (e.g. 10th–90th percentile) and produce a ranking by expected loss with
   uncertainty; which risks change order across the range?
2. Design the "unacceptable regardless of probability" flag: criteria, who can set it, and what it forces.
3. Build a control-evidence tracker: control, evidence type, last verified, verification owner — and report staleness.
4. Take three incidents from the news in your sector and add them as register rows with your own estimates and controls.
5. Argue whether harms to users should sit in the same register as costs to the organisation, or a separate one.

---

## 11. Quiz

*(Answers: [`answer-keys/module-10-answers.md`](../../answer-keys/module-10-answers.md#m10-l04).)*

**Q1.** Which is written as a risk rather than a topic?

- A. Model bias in the hiring process
- B. Prompt injection as an industry concern
- C. Screening rejects one group more often, causing a claim
- D. Data quality across the organisation

**Q2.** In §7.1, how many of the ten positions differed between the two rankings?

- A. 9 of 10 positions
- B. 3 of 10 positions
- C. 0 of 10 positions
- D. 5 of 10 positions

**Q3.** Why did the matrix rank `R6` (cross-tenant leak) last?

- A. Its consequence was judged minor
- B. It had no owner assigned
- C. Its controls were unevidenced
- D. Low likelihood compresses a severe impact

**Q4.** What changed between the two rankings in §7.2?

- A. The estimates of likelihood
- B. Only the meaning of the impact bands
- C. The set of controls credited
- D. The risk appetite threshold

**Q5.** What does a tie in the matrix mean, per §7.3?

- A. Information that would separate the risks has been discarded
- B. The two risks share a common cause
- C. The register has duplicate entries
- D. Both risks are within appetite

**Q6.** What is residual risk?

- A. Risk transferred to an insurer
- B. Risk that only appears after launch
- C. Risk remaining after controls that work
- D. The gap between two scoring methods

**Q7.** In §7.4, what happened when unevidenced controls were discounted?

- A. Every risk moved over appetite
- B. Residual rose for 5 risks; 1 crossed the line
- C. Nothing changed; evidence was already required
- D. The ranking by expected loss reversed

**Q8.** Which is an unevidenced control as the lab defines it?

- A. A CI test that fails the build on violation
- B. An access review with a signed record
- C. A dashboard alert with a runbook
- D. "Policy and training" with no record

**Q9.** What must accompany a risk that stays over appetite?

- A. A higher appetite threshold for that system
- B. Removal from the register at the next review
- C. A recorded acceptance with owner and date
- D. An automatic escalation to the regulator

**Q10.** Which treatment is usually unavailable for reputational harm?

- A. Reduce
- B. Transfer
- C. Avoid
- D. Accept

**Q11.** What should trigger re-scoring a risk?

- A. A model swap or a new data source
- B. The end of the financial year only
- C. A change in the register's template
- D. A new member joining the team

**Q12.** In §6, why did the bias risk sit below three operational risks?

- A. Its owner had accepted it formally
- B. Its expected loss was genuinely lower
- C. It had been moved to a separate register
- D. The matrix scored it 10 against 12 and 16

**Q13.** *(Written, rubric-graded.)* In under 150 words: write a register entry for the risk that an AI assistant sends a
customer an incorrect refund amount — cause, consequence, controls with evidence, residual and treatment.

---

## 12. Revision notes

- **A risk is an event with a cause and a consequence**, not a topic.
- **Matrix vs expected loss:** 9/10 positions differed; CV-screening bias ranked 4th on the matrix and 1st by expected
  loss; a rare cross-tenant leak ranked last on the matrix and 3rd by loss.
- **Scale:** changing only the meaning of the impact bands moved 9/10 positions.
- **Ties:** 10 risks, 7 scores; two risks with a 30× difference in expected loss shared a cell.
- **Evidence rule:** discounting unevidenced controls raised residual for 5/10 risks and pushed 1 over appetite.
- **Every row:** owner, evidence reference, residual, treatment (reduce/transfer/avoid/accept) with a name and date, and a
  review tied to change events.

---

## 13. Completion checklist

- [ ] My register rows are events with causes and consequences.
- [ ] I know what my scoring method hides, and I check severe rows by expected loss.
- [ ] I state what my impact bands mean in units.
- [ ] I credit only controls with an evidence reference, and re-check them.
- [ ] Every over-appetite row has an owner, a treatment and a recorded decision.
- [ ] I scored at least 10/13 on the quiz.

---

## 14. References

- M3-L04 (probability) and M1-L11 (compound error) — the arithmetic behind expected loss `[STABLE]`
- M10-L01 — "a control without evidence is an intention" `[STABLE]`
- NIST AI RMF *Map* and *Manage* functions — risk identification and treatment; see M10-L16 `[UNVERIFIED — checked in M10-L16]`
- D. Hubbard and R. Seiersen, *How to Measure Anything in Cybersecurity Risk* — the standard critique of ordinal risk
  matrices and the case for quantified ranges `[UNVERIFIED]`

---

## 15. Next lesson

→ [M10-L05 — Data Provenance, Licensing and Permitted Use](M10-L05-data-provenance-licensing.md) moves from risks in the
abstract to the material the system is built on: where the data came from, what you are permitted to do with it, and what
that means once it is inside an index.
