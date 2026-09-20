# M10-L09 — Transparency, User Communication and Human Oversight

| | |
|---|---|
| **Lesson ID** | M10-L09 |
| **Difficulty** | 2 (Intermediate) |
| **Estimated study time** | 1.75 hours |
| **Prerequisites** | [M10-L02](M10-L02-intended-use-limitations-ownership.md), [M8-L10](../module-08-agentic-ai/M8-L10-human-approval-escalation.md) |

---

## 1. Learning objectives

1. **Distinguish** oversight that changes outcomes from oversight that only changes who is blamed.
2. **Measure** the effect of review design on how many model errors reach users.
3. **Explain** why a confidence display is only a control when the confidence is calibrated.
4. **Check** whether the throughput target leaves time for the review the design assumes.
5. **Choose** what to disclose, to whom, and where — including how to reach a human and contest a decision.

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **Human in the loop** | A person decides, with the system advising, before the action takes effect. |
| **Human on the loop** | The system acts; a person monitors and can intervene. |
| **Automation bias** | The tendency to accept an automated recommendation without independent checking. |
| **Rubber-stamping** | Nominal review that accepts nearly everything — oversight in name only. |
| **Calibration** | Whether a stated confidence matches the observed frequency of being right (M1-L10). |
| **Disclosure** | What users and affected people are told about the system, at the moment it matters. |
| **Contestability** | A usable route to challenge an outcome and reach a person with authority to change it. |

---

## 3. Plain-language explanation

### 3.1 "A human reviews it" is a design, not a fact

§7.1 runs the same model (85% accurate) past the same reviewers (80% accurate when they genuinely work a case) under three
review designs. **Rubber-stamping** — accepting nearly everything — catches **1.2%** of model errors and lets **12.7%** of
all decisions go out wrong, barely better than the 15% the model would produce alone. A **confidence-led** design that works
any case scoring below 0.80 catches **77.3%** of errors and cuts errors reaching users to **2.9%**.

The organisation with rubber-stamping has not added a control. It has added a person whose name is on the outcome.

### 3.2 An honest result about forced sampling

The third design adds a 20% random sample on top. With **well-calibrated** confidence it costs **306 more worked cases**
and catches **no more errors**, because nearly every model error already scores low. Its value appears in §7.2: when
confidence is inflated by 0.18, confidence-led review collapses to **36.3%** catch rate and **8.2%** errors out, and the
same forced sample pulls it back to **44.5%** and **7.1%**.

**Sampling is insurance against your confidence being wrong**, not a general improvement.

### 3.3 Confidence only helps if it means something

Under the inflated score, **136 of 256 model errors** arrive labelled "high confidence" and are never examined. A number
on the screen changes reviewer behaviour whether or not it deserves to (M1-L10).

### 3.4 Time decides what review can be

§7.3: at 20 cases/hour there are 180 seconds per case and a proper review (90 seconds here) is possible; at **90
cases/hour** there are 40 seconds and proper review is possible for **44%** of them. A throughput target that implies less
time than the review needs is a decision to rubber-stamp, taken by whoever set the target.

### 3.5 Sampling QA is slow

§7.4: sampling **1%** of outputs against a fault present in **2%** of cases gives an even chance of seeing one instance
within **3,465 cases**, and 95% confidence only after **14,977**. Raising the sample to 5% brings the even chance down to
693 cases. Sampling finds systematic faults slowly; targeted review and user reports find them faster.

### 3.6 Disclosure is per audience

§7.5 scores three interfaces against eight disclosures. The internal agent console scores 4/8 and is missing exactly the
two that matter to the customer: **how to reach a human** and **how to contest a decision** — because its user is the
agent, not the person affected.

---

## 4. Analogy

**An autopilot and its pilots.** Autopilot is safe because pilots are trained, rostered with time to monitor, given
instruments they can read, and required to intervene at defined points — not because someone is in the seat. Aviation
learned that a warning nobody has time to act on is not a warning, and that instruments which lie (or which crews cannot
interpret) are worse than none. Passengers, meanwhile, are told something different from what the crew is told, and told
it at the right moment.

### Where the analogy breaks

- **Pilots are trained for months and fly a handful of sectors a day; a reviewer may see 90 cases an hour with no
  training.** The gap in §7.3 is a staffing and design decision, not a human failing.
- **An aircraft's instruments are calibrated to physical quantities; a model's confidence is a learned artefact** that can
  drift with every release (§7.2, M12-L13).

---

## 5. Detailed technical explanation

### 5.1 Three questions before claiming oversight

1. **Can the reviewer form an independent view?** Do they see the evidence — the retrieved documents, the record, the
   reason — or only the recommendation? An interface that shows the answer alone produces agreement, not review.
2. **Do they have time?** §5.4.
3. **Can they act?** Is there a real override path, does using it cost them anything, and is the override recorded?

If any answer is no, the honest design is either to remove the human (and own the automation) or to change the design
until the answers are yes.

### 5.2 Review designs, measured

`[REAL, measured]` §7.1, 2,000 cases, model 85% accurate, reviewer 80% accurate when working a case:

| Design | Cases worked | Model errors caught | Errors reaching users |
|---|---|---|---|
| Rubber-stamping | 30 | 1.2% | 12.7% |
| Review when confidence < 0.80 | 539 | 77.3% | 2.9% |
| Low confidence + 20% forced sample | 845 | 77.3% | 2.9% |

Two lessons: the confidence-led design is where the gain is, and the forced sample buys nothing **while the confidence is
honest**.

### 5.3 Calibration is a precondition

`[REAL, measured]` §7.2, same design, confidence inflated by 0.18:

| Confidence | Cases worked | Caught | Errors out |
|---|---|---|---|
| Calibrated | 539 | 77.3% | 2.9% |
| Overconfident | 120 | 36.3% | 8.2% |
| Overconfident + 20% sample | 492 | 44.5% | 7.1% |

So: measure calibration (reliability diagrams, M1-L10), re-measure after every model or prompt change, and **explain what
the number means** in the interface ("in the last 10,000 cases, answers shown at this level were right about 8 times in
10") rather than showing a bare percentage.

Where confidence is unavailable or untrustworthy — most generative outputs — use proxies you can defend: retrieval
coverage, agreement across samples, presence of a citation that verifies (M7-L12, M7-L13).

### 5.4 Time budgets

`[REAL, measured]` §7.3: 20/hour → 180 s → full review; 40/hour → 90 s → just enough; **90/hour → 40 s → 44%**.

Before claiming review as a control, write down the seconds a real review takes, multiply by the volume, and compare with
the staffing. Publish the number. If the plan does not survive that arithmetic, either fund it, narrow what is reviewed
(risk-based: review the consequential 10%), or state that the system is automated with sampling QA.

### 5.5 Sampling QA

`[REAL, measured]` §7.4, cases needed for a 50% / 95% chance of catching one instance:

| Sample rate | Fault rate | 50% | 95% |
|---|---|---|---|
| 1% | 2% | 3,465 | 14,977 |
| 5% | 2% | 693 | 2,994 |
| 5% | 10% | 138 | 598 |
| 20% | 2% | 173 | 747 |

Design implications: sample **more** when the fault rate you care about is low; stratify the sample towards high-risk
cases; and treat user complaints as a detection channel with its own latency and bias (people who complain are not a
random sample). Pair sampling with automated checks that run on 100% of outputs (schema validation, citation checks,
policy checks) — those catch classes of fault immediately (M7-L12, M9-L07).

### 5.6 Disclosure: what, to whom, where

`[REAL, measured]` §7.5: 1/8, 6/8 and 4/8 across three interfaces.

| Audience | Needs to know | Where |
|---|---|---|
| End user in the conversation | That it is AI, what it is for, its limits, how to reach a human | In the interface, at first contact and at refusal |
| Person affected by a decision | That a decision was made, the main reasons, how to contest it, who decides | With the decision, in plain language |
| Internal reviewer | Evidence, confidence and its meaning, what they are accountable for | In the review interface |
| Buyer or partner | Intended use, limitations, evaluation results, data handling | System/model card (L15) |

Two rules that prevent most bad disclosures: put it **where the decision is**, not in a policy page nobody opens; and make
it **actionable** — "how to contest" is only a disclosure if the route exists and is answered by someone with authority
(L14).

### 5.7 Assumptions and limitations

- Reviewer behaviour is a scripted probability, not a study. Published work on automation bias reports substantial
  effects; the specific numbers here are the lab's assumptions.
- Disclosure requirements differ by jurisdiction and sector, and are out of scope (L16).
- Accessibility of disclosures — language, reading level, assistive technology — matters and is not modelled here.

---

## 6. Worked example — the "human-reviewed" credit decisions

**The situation.** A lender introduced a model to pre-assess loan applications. Policy said every declined application was
reviewed by an analyst before the decision was sent. The compliance pack described "human oversight of all adverse
decisions".

**What an internal audit found.**

1. Analysts handled **110 cases an hour**. A proper review — open the file, check income evidence, form a view — took about
   two minutes. §7.3's arithmetic: proper review was possible for roughly a quarter of cases.
2. The interface showed the model's recommendation and a score, **not** the evidence. Analysts could open the file, which
   cost 30 seconds, so most did not.
3. Override rate was **0.6%**, and analysts who overrode were asked to write a justification; those who agreed were not.
   The path of least resistance was agreement.
4. The score was uncalibrated after a model update: cases at "high confidence" had an error rate three times higher than
   six months earlier (§7.2).

| # | Finding | Fix |
|---|---|---|
| 1 | Throughput made review impossible | Review only high-impact declines, with a time budget; automate the rest openly |
| 2 | Evidence not in the interface | Show the evidence inline, with the reasons and the retrieval sources |
| 3 | Asymmetric friction | Equal effort to agree or override; record both with reasons |
| 4 | Uncalibrated confidence | Re-measure calibration each release; gate on it (L12) |
| 5 | "Human oversight" claimed in the pack | Restate honestly: automated with targeted review and sampling QA |

**The general rule.** **If overriding costs more than agreeing, you have measured your reviewers' patience, not their
judgement.**

---

## 7. Practical activity

**File:** [`labs/m10/l09_transparency_oversight.py`](../../labs/m10/l09_transparency_oversight.py)

**No API key, no network, no third-party dependencies.**

```bash
source .venv/bin/activate
python labs/m10/l09_transparency_oversight.py
```

### 7.2 Expected output

`[EXECUTED]` — 2026-09-16, Python 3.12.3 (pure standard library). Run twice; output identical.

```text

============================================================================
1. THREE REVIEW DESIGNS, SAME MODEL, SAME REVIEWERS
============================================================================
  rubber-stamping (accepts almost everything)  cases worked:   30/2000  model errors caught:  1.2%  errors reaching the user: 12.7%
  reviews only when confidence < 0.80          cases worked:  539/2000  model errors caught: 77.3%  errors reaching the user: 2.9%
  low confidence + 20% forced sample           cases worked:  845/2000  model errors caught: 77.3%  errors reaching the user: 2.9%

  the model alone would send 15% of decisions out wrong.
  Rubber-stamping changes that number very little, at the cost of implying
  to everyone -- users, auditors, the people affected -- that a human decided.

  Note the third row: when confidence is WELL CALIBRATED, nearly every model
  error already carries a low score, so the extra 20% sample costs 306 more worked
  cases and catches no more errors. Its value shows up in section 2.

============================================================================
2. WHEN CONFIDENCE IS MISCALIBRATED, CONFIDENCE-LED REVIEW MISFIRES
============================================================================
  well-calibrated confidence : cases worked  539, caught 77.3%, errors out 2.9%
  overconfident by 0.18      : cases worked  120, caught 36.3%, errors out 8.2%
  overconfident + 20% sample : cases worked  492, caught 44.5%, errors out 7.1%

  under the inflated score, 136/256 model errors arrive labelled
  'high confidence' and are never worked. A confidence display is a control
  only if the number is calibrated and its meaning is explained (M1-L10).

============================================================================
3. THE TIME BUDGET DECIDES HOW MUCH REVIEW IS POSSIBLE
============================================================================
  target  20 cases/hour ->   180s per case -> a proper review is possible for about 100% of them
  target  40 cases/hour ->    90s per case -> a proper review is possible for about 100% of them
  target  90 cases/hour ->    40s per case -> a proper review is possible for about  44% of them

  A proper review here means 90s: read the case, check the evidence,
  form an independent view. If the throughput target implies less, the
  organisation has chosen rubber-stamping without writing it down.

============================================================================
4. SAMPLING QA: HOW LONG UNTIL A SYSTEMATIC FAULT IS NOTICED?
============================================================================
  sampling   1% of outputs, fault in   2% of cases: 50% chance of seeing one within   3,465 cases
  sampling   1% of outputs, fault in   2% of cases: 95% chance of seeing one within  14,977 cases
  sampling   1% of outputs, fault in  10% of cases: 50% chance of seeing one within     693 cases
  sampling   1% of outputs, fault in  10% of cases: 95% chance of seeing one within   2,994 cases
  sampling   5% of outputs, fault in   2% of cases: 50% chance of seeing one within     693 cases
  sampling   5% of outputs, fault in   2% of cases: 95% chance of seeing one within   2,994 cases
  sampling   5% of outputs, fault in  10% of cases: 50% chance of seeing one within     138 cases
  sampling   5% of outputs, fault in  10% of cases: 95% chance of seeing one within     598 cases
  sampling  20% of outputs, fault in   2% of cases: 50% chance of seeing one within     173 cases
  sampling  20% of outputs, fault in   2% of cases: 95% chance of seeing one within     747 cases
  sampling  20% of outputs, fault in  10% of cases: 50% chance of seeing one within      34 cases
  sampling  20% of outputs, fault in  10% of cases: 95% chance of seeing one within     148 cases

  At 1,000 cases a day, a 1% sample of a 2% fault has an even chance of
  surfacing it in about a month and a half. Sampling finds systematic faults
  slowly; targeted review of high-risk cases and user reports find them faster.

============================================================================
5. WHAT USERS ARE TOLD
============================================================================
  chat widget, first version   1/8 present   missing: what it is for / not for; known limitations; confidence or uncertainty shown...
  chat widget, after review    6/8 present   missing: confidence or uncertainty shown; how to contest a decision
  internal agent console       4/8 present   missing: what it is for / not for; how to reach a human; how to contest a decision...

  The internal console is missing the two disclosures that matter to the person
  affected -- how to reach a human and how to contest -- because the agent, not
  the customer, is its user. Somebody has to own the end-to-end story (M10-L02).

============================================================================
6. WHAT THIS LAB IS AND IS NOT
============================================================================
  REAL: every catch rate, error rate, time budget and detection figure above is
  computed from the simulation or from binomial arithmetic.

  ILLUSTRATIVE: reviewer behaviour is a scripted probability, not a study of
  real reviewers. Published work on automation bias reports large effects, but
  the numbers here are this lab's assumptions, not findings.

  NOT SHOWN: what any jurisdiction requires to be disclosed, and accessibility
  of disclosures, both of which matter and are out of scope (M10-L16).

Done.
```

### 7.3 Reading the result

**Section 1's first row is the honest description of most "human in the loop" claims**: 1.2% of errors caught.

**Section 2 is why calibration is a governance property**, not a modelling nicety: the same design loses half its value
when the number is inflated.

**Section 4 sets expectations for sampling.** If your QA plan is "we review 1%", know how long it takes to notice a 2%
fault.

---

## 8. Common mistakes and troubleshooting

1. **Claiming oversight without checking time, evidence and authority.** §5.1, §6.
2. **Showing a confidence number without calibrating or explaining it.** §5.3.
3. **Assuming a forced sample always helps.** §5.2 — it earns its cost when confidence is unreliable.
4. **Sampling 1% and expecting to notice rare faults quickly.** §5.5.
5. **Making override cost more than agreement.** §6.
6. **Disclosures in a policy page rather than at the decision.** §5.6.
7. **"How to contest" with no route, or a route with no authority.** §5.6, L14.

| Symptom | Likely cause | Fix |
|---|---|---|
| Override rate near zero | Rubber-stamping, or asymmetric friction | Equalise effort; measure and target a realistic rate |
| Reviewers agree with wrong answers confidently | Uncalibrated confidence display | Recalibrate; explain the number; re-gate |
| Faults discovered by customers first | Sampling too thin, no automated checks | Raise sampling on risky slices; add 100% automated checks |
| Reviewers cannot explain a decision | Evidence not shown in the interface | Put the evidence next to the recommendation |
| Complaints about "no way to reach a human" | Disclosure missing at the point of refusal | Add the route where the refusal happens |

---

## 9. Security, privacy, reliability, cost

- **Security.** Oversight is a control against injected instructions and tool misuse only if reviewers see what changed
  and can refuse (M9-L13); otherwise it is a formality attackers can rely on.
- **Privacy.** Review interfaces expose records to staff: apply the same minimisation and access rules as anywhere else
  (L06, L07).
- **Reliability.** Calibration drifts with model and prompt changes; treat it as a monitored metric (M12-L13).
- **Cost.** Review time is the dominant cost in most of these designs; risk-based review keeps the cost proportional to the
  consequence.

---

## 10. Exercises

### Exercise 1 — Beginner (~20 min)

1. What three conditions make oversight real, per §5.1?
2. Why did rubber-stamping catch only 1.2% of errors?
3. When does a forced random sample earn its cost?
4. How many cases does a 5% sample need to have an even chance of catching a 2% fault?
5. Which two disclosures were missing from the internal console, and why does that matter?

### Exercise 2 — Intermediate (~40 min)

1. Run the lab. Change the reviewer accuracy to 0.6 and re-run; which design is most affected?
2. Add a design that reviews the 10% of cases with the largest financial impact regardless of confidence, and compare.
3. Compute the staffing needed for §7.3's 90 cases/hour scenario to allow a 90-second review.
4. Add "explanation quality" to §7.5's disclosure list and score the three interfaces again.
5. Write the disclosure text you would show at the moment an AI assistant refuses a request.

### Exercise 3 — Challenge (~60 min)

1. Design an experiment to measure automation bias in your own reviewers, with a control condition and consent.
2. Build a calibration monitor: bucket confidence, compare with observed accuracy, and alert when the gap exceeds a
   threshold (M1-L10).
3. Design a risk-based review policy for a system you know: what is reviewed, by whom, in how long, and what is sampled.
4. Write the contest process end to end: intake, evidence, who decides, timescales, and what the person is told.
5. Argue whether your system should say "AI-generated" on every output or only some, and what changes with that choice.

---

## 11. Quiz

*(Answers: [`answer-keys/module-10-answers.md`](../../answer-keys/module-10-answers.md#m10-l09).)*

**Q1.** In §7.1, what share of model errors did rubber-stamping catch?

- A. 77.3% of errors
- B. 44.5% of errors
- C. 1.2% of errors
- D. 36.3% of errors

**Q2.** What does a rubber-stamping review add, if not error reduction?

- A. A person whose name is on the outcome
- B. A calibrated confidence signal
- C. Faster throughput per case
- D. A record of the evidence considered

**Q3.** When did the 20% forced sample add no value?

- A. When reviewers were inaccurate
- B. When the sample was drawn randomly
- C. When the volume was high
- D. When confidence was well calibrated

**Q4.** In §7.2, what happened to the confidence-led design when scores were inflated?

- A. It worked more cases and caught more
- B. Catch rate fell from 77.3% to 36.3%
- C. Errors reaching users stayed at 2.9%
- D. It became equivalent to forced review

**Q5.** Why does an inflated confidence score break confidence-led review?

- A. Reviewers stop trusting the interface
- B. Errors arrive labelled high confidence and are never worked
- C. The model refuses more cases
- D. The sample size becomes too small

**Q6.** At 90 cases per hour, what share of cases allowed a 90-second review?

- A. 100% of cases
- B. 90% of cases
- C. 67% of cases
- D. 44% of cases

**Q7.** What does a throughput target below the review time mean?

- A. Rubber-stamping has been chosen implicitly
- B. Reviewers will work faster over time
- C. The model must be more accurate
- D. Sampling QA becomes unnecessary

**Q8.** Sampling 1% of outputs against a 2% fault rate: how many cases for an even chance of catching one?

- A. About 138 cases
- B. About 693 cases
- C. About 3,465 cases
- D. About 14,977 cases

**Q9.** What complements sampling for faults you can define?

- A. Increasing reviewer headcount
- B. Reducing the model's confidence threshold
- C. Publishing the sampling rate
- D. Automated checks on 100% of outputs

**Q10.** Which disclosures were missing from the internal agent console?

- A. AI involvement and citations
- B. How to reach a human and how to contest
- C. Limitations and confidence
- D. Data use and retention

**Q11.** Per §5.6, where should a disclosure appear?

- A. In the terms of service
- B. In the model card only
- C. Where the decision or refusal happens
- D. In the release notes

**Q12.** In §6, what made agreement the path of least resistance?

- A. Only overrides required a written justification
- B. The model was usually right
- C. Analysts were not trained on the product
- D. Declines were rare in the case mix

**Q13.** *(Written, rubric-graded.)* In under 150 words: your product claims "every AI decision is reviewed by a human".
Describe how you would test whether that claim is true, and what you would change if it is not.

---

## 12. Revision notes

- **Oversight needs evidence, time and authority.** Measured: rubber-stamping caught **1.2%** of errors (12.7% out);
  confidence-led caught **77.3%** (2.9% out).
- **Forced sampling** costs 306 extra worked cases and caught nothing extra with calibrated confidence; it recovered
  36.3% → **44.5%** when confidence was inflated.
- **Calibration is a precondition**: 136/256 errors arrived labelled high confidence when the score was inflated.
- **Time budget:** 90 cases/hour leaves 40 s, enough for **44%** of a 90-second review.
- **Sampling QA:** 1% sample, 2% fault → even chance at **3,465** cases; 5% → 693. Add automated checks on 100%.
- **Disclosure per audience, at the point of decision**, including a real route to a human and to contest.

---

## 13. Completion checklist

- [ ] I can state whether my reviewers have evidence, time and authority.
- [ ] I measure catch rate and override rate, not just "review completed".
- [ ] My confidence displays are calibrated and explained.
- [ ] My QA plan states its detection latency for the faults I care about.
- [ ] Users are told what they need, where the decision happens, with a real route to a human.
- [ ] I scored at least 10/13 on the quiz.

---

## 14. References

- M1-L10 (probabilistic behaviour, calibration) — what a confidence number must satisfy to be useful `[STABLE]`
- M8-L10 (human approval and escalation) — approval design in agent systems `[STABLE]`
- M7-L12 / M7-L13 (citations and abstention) — the evidence a reviewer needs and the system's own uncertainty `[STABLE]`
- Research on automation bias in decision support (e.g. Parasuraman & Riley, 1997) — the effect this lab models `[UNVERIFIED]`
- NIST AI RMF *Govern* and *Manage* — transparency and oversight as practices; see M10-L16 `[UNVERIFIED — checked in M10-L16]`

---

## 15. Next lesson

→ [M10-L10 — Security: Prompt Injection, Exfiltration and Tool Misuse](M10-L10-security-threat-model.md) builds the threat
model for an AI system: who attacks it, through which inputs, and what they can reach.
