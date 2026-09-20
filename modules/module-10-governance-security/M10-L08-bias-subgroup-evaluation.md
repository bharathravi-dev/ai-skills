# M10-L08 — Bias and Subgroup Evaluation

| | |
|---|---|
| **Lesson ID** | M10-L08 |
| **Difficulty** | 3 (Advanced) |
| **Estimated study time** | 2.25 hours |
| **Prerequisites** | [M3-L14](../module-03-math-ml-essentials/M3-L14-metrics.md), [M10-L06](M10-L06-personal-sensitive-data.md) |

> **Scope note.** This lesson teaches the measurement: how to find subgroup gaps, decide whether they are real, and choose
> what to report. Which attributes you may collect, and what the law requires of decisions about people, are
> jurisdiction-specific and out of scope (M10-L16).

---

## 1. Learning objectives

1. **Disaggregate** an aggregate metric and report per-subgroup error rates that matter for the decision being made.
2. **Attach confidence intervals** to subgroup metrics and say when a subgroup is too small to conclude anything.
3. **Recognise** Simpson's paradox and report stratified alongside aggregate results.
4. **Explain** why demographic parity, equal opportunity and predictive parity cannot all hold when base rates differ.
5. **Document** intersectional cells where there is not enough data to measure, rather than publishing a number with no
   power.

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **Subgroup** | A slice of users or cases you evaluate separately (a population group, language, channel, device, region). |
| **Disaggregated evaluation** | Reporting metrics per subgroup rather than only in aggregate. |
| **FNR / miss rate** | Share of genuinely positive cases the system fails to flag. |
| **FPR / false alarm rate** | Share of genuinely negative cases the system wrongly flags. |
| **Selection rate** | Share of a group the system selects, regardless of correctness. |
| **Demographic parity** | Equal selection rates across groups. |
| **Equal opportunity** | Equal true-positive rates across groups. |
| **Predictive parity** | Equal precision across groups. |
| **Wilson interval** | A confidence interval for a proportion that behaves sensibly at small n. |

---

## 3. Plain-language explanation

### 3.1 The number in the release note is an average over people

§7.1 evaluates a synthetic screening model: **80.9% overall accuracy**. Disaggregated, the same model misses **17.1%** of
suitable Group A applicants and **39.8%** of suitable Group B applicants — Group B's suitable applicants are missed
**2.3×** as often. Group C sits in between on a small sample.

Nothing in the aggregate hints at this, because Group A is 72% of the population: their experience *is* the average.

### 3.2 Which gaps are real?

§7.2 attaches 95% Wilson intervals. Group A's miss rate is 17.1% [14.9, 19.5]; Group B's is 39.8% [34.5, 45.4] — the
intervals do not overlap, so the gap is not a sampling artefact. But measure Group C on a 60-applicant sample and you get
15.8% **[5.5, 37.6]** — an interval wide enough to contain both "no gap" and "a very large gap". Reporting the point
estimate alone would be a coin flip presented as a finding.

### 3.3 Aggregates can reverse

§7.3 constructs the classic case: Group B is selected **more** often than Group A in **both** channels (65% vs 60%, 25%
vs 20%) and **less** often overall (29% vs 52%), because B applies mostly through the channel that selects fewer people.
Whether your headline gap is real, an artefact of composition, or both, depends on strata you have to choose and report.

### 3.4 You cannot close every gap at once

§7.4 lowers Group B's threshold and watches three fairness definitions move. At one shared threshold: selection gap
10.3%, TPR gap 22.7%, precision gap 2.0%. Lowering B's threshold to 0.44 nearly closes the selection gap (2.4%) and
halves the TPR gap — and pushes the precision gap to 10.9%. At 0.40, the TPR gap nearly closes (3.3%) while selection and
precision gaps widen to 13.7% and 19.6%.

This is the impossibility result in miniature: when base rates differ, these definitions conflict. **Choosing which gap
matters is a governance decision with a named owner**, not a modelling detail — and per-group thresholds carry legal
constraints in many jurisdictions.

### 3.5 Some cells cannot be measured

§7.5 crosses group with channel. Four cells have enough positive cases to estimate error rates; **two do not**. The
honest output is "not measurable at this sample size", not a number.

---

## 4. Analogy

**A school reporting one average grade.** The school average is fine; the average hides that pupils taught in one
building do markedly worse. Reporting by building is disaggregation. Checking whether a 12-pupil building's average means
anything is the confidence interval. Noticing that the weaker building takes more pupils who arrived mid-year is
stratification — and discovering that, within each arrival cohort, that building does *better* is Simpson's paradox.

### Where the analogy breaks

- **A school can eventually teach every pupil the same way; a classifier's errors trade off against each other.** §7.4's
  three definitions cannot be satisfied together, so someone must choose which to prioritise.
- **Grades are one metric; AI harms differ by direction.** A missed suitable applicant and a wrongly flagged one are not
  equivalent, and which matters more depends on the decision (§5.2).

---

## 5. Detailed technical explanation

### 5.1 Choose the metric that matches the harm

`[REAL, measured]` §7.1:

| Group | n | Accuracy | Miss rate (FNR) | False alarm (FPR) | Selection rate |
|---|---|---|---|---|---|
| A | 2,885 | 82.0% | 17.1% | 18.4% | 41.4% |
| B | 849 | 76.2% | **39.8%** | 14.9% | 31.1% |
| C | 266 | 83.8% | 21.6% | 13.5% | 35.0% |

Accuracy differs by 5.8 points; the **miss rate differs by 22.7 points**. Which one you report decides whether anyone
acts. Pick per direction of harm:

- **Denial of an opportunity** (screening, credit, triage): compare **FNR / TPR** — who is wrongly excluded.
- **Unwanted attention** (fraud flags, moderation): compare **FPR** — who is wrongly burdened.
- **Both, plus selection rate**, when the decision allocates something scarce.

For generative systems the same logic applies to task-specific measures: refusal rate by language, citation accuracy by
document type, escalation rate by customer segment (M7-L19, M5-L18).

### 5.2 Intervals, not point estimates

`[REAL, measured]` §7.2: A 17.1% [14.9, 19.5]; B 39.8% [34.5, 45.4]; C (n=60 sample) 15.8% **[5.5, 37.6]**.

- Use **Wilson intervals** for proportions; normal approximations misbehave at small n and near 0 or 1 (M3-L14).
- Decide a **minimum cell size** in advance for reporting, and publish "insufficient data" for cells below it.
- Remember multiple comparisons: testing twenty subgroups will produce an apparently significant gap by chance. Pre-register
  the subgroups that matter and treat the rest as exploratory.

### 5.3 Stratify

`[REAL, measured, constructed]` §7.3: B is selected more in both channels (65% vs 60%; 25% vs 20%) and less overall (29%
vs 52%).

Practical rules: report aggregate **and** stratified; choose strata that reflect how people arrive at the system
(channel, product, region, tenure); and state which strata you controlled for. A reversal is not proof of fairness — it
relocates the question to "why do the groups arrive through different channels?", which is often the more important
finding.

### 5.4 The impossibility, and the decision it forces

`[REAL, measured]` §7.4:

| Scenario | Selection gap | TPR gap | Precision gap |
|---|---|---|---|
| One threshold (0.50) | 10.3% | 22.7% | 2.0% |
| B threshold 0.44 | 2.4% | 8.9% | 10.9% |
| B threshold 0.40 | 13.7% | 3.3% | 19.6% |

When base rates differ, equal selection rates, equal true-positive rates and equal precision cannot hold simultaneously.
So the governance artefact is a **written decision**: which gap this system optimises, why, who decided, and what is
monitored (L15's card, L04's register).

**Note carefully:** group-specific thresholds are one mechanism among several, and in many jurisdictions treating people
differently by a protected characteristic is constrained regardless of intent. Other mechanisms — better data coverage,
features that work equally well, changing the decision so the model advises rather than decides — may be both more
effective and less fraught (L09).

### 5.5 Intersections and coverage

`[REAL, measured]` §7.5: 2 of 6 cells lacked enough positive cases to estimate error rates.

- Publish the **coverage table** with the results: cell, n, positives, measurable yes/no.
- Plan collection where it matters: oversample small groups in evaluation sets (not in production decisions), or run
  targeted studies.
- Respect the privacy constraint: measuring by subgroup needs the attribute, which you may not be permitted to collect or
  keep (L06). Options include voluntary self-report with a clear purpose, statistical proxies used only in aggregate, or
  third-party assessment — each with its own trade-offs, and each a decision to record.

### 5.6 What to do about a gap

Measurement is the start. In order of usual effectiveness:

1. **Fix the data**: coverage, labelling quality, and label bias (the labels themselves may encode past decisions).
2. **Fix the task**: does the system decide, or advise a human who decides (L09)?
3. **Fix the model**: features, training weighting, calibration per group where lawful.
4. **Fix the threshold or the process**: routing low-confidence cases to humans, with monitoring.
5. **Do not ship** the capability for the affected population until it works.

Re-measure after every change, and keep the gap in the release gates (L12) so it cannot silently regress.

### 5.7 Assumptions and limitations

- The population is synthetic and the groups are neutral labels; the arithmetic is real, the scenario is not.
- Causes are not identified here: a gap tells you *that* the system fails a group, not *why*.
- Fairness definitions beyond the three shown (calibration, counterfactual fairness, individual fairness) exist and
  conflict in their own ways.

---

## 6. Worked example — the assistant that was worse at one job

**The situation.** A support assistant answered customer questions, measured by "answer accepted by the agent" —
**87% overall**, well above the 80% gate. It shipped. Three months later, the complaints team noticed that customers
writing in French were escalating twice as often.

**What the disaggregation showed.**

1. Acceptance was **91%** for English conversations and **61%** for French — a 30-point gap invisible in the 87% aggregate
   (§5.1), because French was 8% of volume.
2. The evaluation set had been sampled from historical conversations, which were **94% English**: the gate had been passed
   on a set that barely contained the failing case (M5-L18).
3. Per-language intervals on the evaluation set were wide — the French cell had 31 examples, interval [43%, 77%] — so even
   the original evaluation could not have concluded anything about French (§5.2).
4. Stratifying by topic showed the gap concentrated in **billing** questions, where the retrieved policy documents existed
   only in English (§5.3). The model was not "worse at French"; the *system* had no French billing content.

| # | Finding | Fix |
|---|---|---|
| 1 | Aggregate gate hid a 30-point gap | Gate per language with minimum cell sizes (L12) |
| 2 | Evaluation set mirrored historical volume | Stratified evaluation set: minimum 150 examples per language |
| 3 | No intervals reported | Wilson intervals on every cell; "insufficient data" where small |
| 4 | Root cause was content coverage, not the model | Translate billing policies; measure retrieval coverage per language (M7-L19) |

**The general rule.** **Aggregate metrics are for dashboards; disaggregated metrics are for decisions.** And when a gap
appears, look at the system — data, retrieval, process — before blaming the model.

---

## 7. Practical activity

**File:** [`labs/m10/l08_bias_subgroup_evaluation.py`](../../labs/m10/l08_bias_subgroup_evaluation.py)

**No API key, no network, no third-party dependencies.** All data is synthetic.

```bash
source .venv/bin/activate
python labs/m10/l08_bias_subgroup_evaluation.py
```

### 7.2 Expected output

`[EXECUTED]` — 2026-09-16, Python 3.12.3 (pure standard library). Run twice; output identical.

```text

============================================================================
1. ONE AGGREGATE SCORE, THREE DIFFERENT EXPERIENCES
============================================================================
  overall accuracy 80.9% on 4000 applicants (the number that would appear in a release note)

  group       n  accuracy   miss rate (FNR)  false alarm (FPR)  selection rate
  A        2885     82.0%             17.1%              18.4%           41.4%
  B         849     76.2%             39.8%              14.9%           31.1%
  C         266     83.8%             21.6%              13.5%           35.0%

  Group B's suitable applicants are missed 2.3x as often as Group A's,
  while overall accuracy looks healthy. Accuracy is an average over people.

============================================================================
2. IS THE GAP REAL? CONFIDENCE INTERVALS BY SUBGROUP SIZE
============================================================================
  group    suitable n   missed      FNR   95% interval
  A              1028      176    17.1%   [14.9%, 19.5%]
  B               304      121    39.8%   [34.5%, 45.4%]
  C                88       19    21.6%   [14.3%, 31.3%]

  the same measurement on a 60-applicant sample of Group C:
    FNR 15.8% with interval [5.5%, 37.6%] -- wide enough to contain
    both 'no gap' and 'a very large gap'. Report intervals, and say when a
    subgroup is too small to conclude anything (M3-L14).

============================================================================
3. SIMPSON'S PARADOX: AN AGGREGATE GAP THAT REVERSES IN EVERY STRATUM
============================================================================
  referral (60-65% selected)    A: 480/800 = 60%  B: 65/100 = 65%   higher: B
  online (20-25% selected)      A: 40/200 = 20%  B: 225/900 = 25%   higher: B
  ALL APPLICANTS                A: 520/1000 = 52%  B: 290/1000 = 29%   higher: A

  Group B is selected more often in BOTH channels and less often overall,
  because B applies mainly through the channel that selects fewer people.
  Aggregates mix 'who applies where' with 'how they are treated', so report
  stratified numbers and say which strata you controlled for.

============================================================================
4. THREE FAIRNESS DEFINITIONS, ONE THRESHOLD
============================================================================
  scenario                                   selection gap               TPR gap         precision gap
  one threshold 0.50 for both                        10.3%                 22.7%                  2.0%
  Group B threshold lowered to 0.44                   2.4%                  8.9%                 10.9%
  Group B threshold lowered to 0.40                  13.7%                  3.3%                 19.6%

  Closing one gap opens another: these definitions cannot all hold at once
  when base rates differ (the standard impossibility result). Choosing WHICH
  gap matters for this decision is a governance choice with a named owner --
  and per-group thresholds carry legal constraints in many jurisdictions.

============================================================================
5. INTERSECTIONS: WHERE THERE IS NOT ENOUGH DATA TO MEASURE
============================================================================
  cell                        n  suitable n   status
  ('A', 'online')          1714         505   measurable
  ('A', 'referral')        1171         523   measurable
  ('B', 'online')           534         168   measurable
  ('B', 'referral')         315         136   measurable
  ('C', 'online')           163          49   too small to measure (need >= 100 suitable)
  ('C', 'referral')         103          39   too small to measure (need >= 100 suitable)

  2/6 cells cannot support a stable error-rate estimate.
  Say so in the card (M10-L15) instead of publishing a number with no power,
  and plan how to collect enough data -- or accept the limitation explicitly.

============================================================================
6. WHAT THIS LAB IS AND IS NOT
============================================================================
  REAL: every rate, interval, paradox and gap above is computed from the
  generated population; the Wilson intervals and the impossibility trade-off
  are genuine arithmetic.

  ILLUSTRATIVE: the population is synthetic, and the 'groups' are neutral
  labels. Real subgroup analysis requires deciding which attributes you may
  collect and hold at all (M10-L06), and the harms differ by context.

  NOT SHOWN: causal analysis of WHY a gap exists, mitigation by reweighting or
  data collection, and the legal treatment of protected characteristics, which
  varies by jurisdiction (M10-L16).

Done.
```

### 7.3 Reading the result

**Section 1's accuracy column is nearly flat; the miss-rate column is not.** Choosing the metric is choosing what you can
see.

**Section 2's third row is the discipline.** A 60-case sample yields an interval that spans "fine" to "very bad".

**Section 4 is the uncomfortable one**: every row closes one gap and opens another. There is no threshold that makes the
table all zeros.

---

## 8. Common mistakes and troubleshooting

1. **Reporting aggregate accuracy only.** §5.1 — a 22.7-point miss-rate gap hid behind 5.8 points of accuracy.
2. **Point estimates with no intervals**, especially on small cells. §5.2.
3. **Testing many subgroups and reporting the significant one.** §5.2 — pre-register what matters.
4. **Comparing aggregates across groups with different compositions.** §5.3.
5. **Claiming a system is "fair" without saying which definition.** §5.4.
6. **Publishing numbers for cells with no statistical power.** §5.5.
7. **Treating a gap as a model problem** when it is a data-coverage or process problem. §6.

| Symptom | Likely cause | Fix |
|---|---|---|
| Gate passed, users of one group complain | Aggregate gate, unrepresentative evaluation set | Per-subgroup gates with minimum cell sizes |
| Subgroup result swings between releases | Cell too small | Report intervals; increase sampling or mark unmeasurable |
| Two teams disagree on whether it is fair | Different definitions | Write down which definition governs and why |
| A gap disappears when stratified | Composition effect | Report both; investigate why arrival differs |
| Fixing one gap creates another | The impossibility trade-off | Make and record the choice, with monitoring |

---

## 9. Security, privacy, reliability, cost

- **Privacy.** Subgroup measurement needs subgroup data, which is often sensitive: minimise, aggregate, restrict access,
  and be explicit about purpose (L06).
- **Security.** Attribute data collected for fairness work is attractive to attackers; treat it as special-category data.
- **Reliability.** Gaps regress like any metric; put them in the release gates and monitor them in production (L12, M12-L13).
- **Cost.** Building representative evaluation sets costs real annotation effort; it is far cheaper than discovering the
  gap through complaints (§6).

---

## 10. Exercises

### Exercise 1 — Beginner (~20 min)

1. Why did overall accuracy hide Group B's miss rate?
2. What does the interval [5.5%, 37.6%] allow you to conclude?
3. In §7.3, which group is selected more often within each channel, and which overall?
4. State the three fairness definitions measured in §7.4 in your own words.
5. Which cells in §7.5 were not measurable, and what should be published for them?

### Exercise 2 — Intermediate (~40 min)

1. Run the lab. Change Group B's share of the population to 40% and re-run; does the aggregate still hide the gap?
2. Add a fourth scenario to §7.4 with Group A's threshold raised instead, and compare the three gaps.
3. Compute the sample size needed for a ±5-point interval on Group C's miss rate.
4. Add "language" as a second attribute and produce the full intersectional coverage table.
5. Write the subgroup section of a model card for this system (L15).

### Exercise 3 — Challenge (~60 min)

1. Implement a bootstrap confidence interval for the *difference* in miss rates between two groups and compare with the
   Wilson approach.
2. Build a release gate that fails when any subgroup with sufficient n regresses by more than 3 points (L12).
3. Construct a dataset where equal precision and equal TPR both hold, and explain what had to be true.
4. Design an evaluation-set sampling plan that meets minimum cell sizes for six subgroups without collecting new
   attributes about individuals.
5. Take a real system you know and write down which fairness definition its decision implies, who owns that choice, and
   what is monitored.

---

## 11. Quiz

*(Answers: [`answer-keys/module-10-answers.md`](../../answer-keys/module-10-answers.md#m10-l08).)*

**Q1.** In §7.1, what was the gap between Group A and Group B?

- A. 5.8 points of accuracy, and nothing else
- B. 22.7 points of miss rate
- C. 22.7 points of false alarm rate
- D. No gap outside the confidence intervals

**Q2.** Why did the aggregate score hide it?

- A. The model was calibrated per group
- B. Accuracy is insensitive to false negatives
- C. The evaluation set was too large
- D. Group A dominated the population

**Q3.** What does an interval of [5.5%, 37.6%] mean for a reported 15.8% miss rate?

- A. The sample is too small to conclude anything
- B. The true rate is 15.8% with 95% certainty
- C. The gap is confirmed at 95% confidence
- D. The interval width does not affect conclusions

**Q4.** Which metric should you compare when the harm is wrongful exclusion?

- A. Precision
- B. Overall accuracy
- C. Miss rate (FNR)
- D. False alarm rate (FPR)

**Q5.** In §7.3, which group had the higher selection rate within each channel?

- A. Group A in both channels
- B. Group A in referral, Group B online
- C. Group B in both channels
- D. Neither; the rates were equal

**Q6.** What explains the reversal in the aggregate?

- A. The classifier threshold differed by group
- B. Group B applied mainly through the lower-selecting channel
- C. The sample sizes were too small
- D. Selection rates were miscalculated

**Q7.** In §7.4, what happened when Group B's threshold was lowered to 0.40?

- A. All three gaps closed
- B. Only the precision gap closed
- C. The selection gap closed and the others held
- D. The TPR gap nearly closed while the others widened

**Q8.** What does the impossibility result imply for governance?

- A. Someone must choose and record which gap matters
- B. Fairness cannot be measured meaningfully
- C. Group-specific thresholds are always required
- D. Only precision parity is achievable in practice

**Q9.** What should be published for a cell with too few positive cases?

- A. The point estimate, clearly labelled as noisy
- B. "Insufficient data to measure"
- C. The aggregate figure in its place
- D. An estimate borrowed from a similar cell

**Q10.** Which check would have caught §6's French gap before release?

- A. A larger overall evaluation set
- B. A higher accuracy gate
- C. A per-language gate with minimum cell sizes
- D. More frequent model retraining

**Q11.** In §6, what was the underlying cause of the gap?

- A. Billing policies existed only in English
- B. The model was weaker at French generally
- C. Agents rejected French answers out of habit
- D. French conversations were longer

**Q12.** Which action addresses a gap without changing the model?

- A. Adjusting the decision threshold per group
- B. Retraining with class weighting
- C. Recalibrating probabilities per group
- D. Routing low-confidence cases to a human

**Q13.** *(Written, rubric-graded.)* In under 150 words: your model's overall accuracy meets the release gate. Describe the
subgroup analysis you would run before shipping, and what you would do if you found a gap.

---

## 12. Revision notes

- **Disaggregate:** 80.9% overall hid a **17.1% vs 39.8%** miss rate (2.3×). Accuracy moved 5.8 points; miss rate moved 22.7.
- **Intervals:** Wilson intervals; A [14.9, 19.5] vs B [34.5, 45.4] — a real gap. A 60-case sample gave **[5.5, 37.6]** —
  no conclusion.
- **Stratify:** constructed case where B is selected more in both channels (65/60, 25/20) and less overall (29% vs 52%).
- **Impossibility:** one threshold → gaps 10.3 / 22.7 / 2.0; B at 0.44 → 2.4 / 8.9 / 10.9; B at 0.40 → 13.7 / 3.3 / 19.6.
  Choose and record which gap governs.
- **Coverage:** 2 of 6 intersectional cells unmeasurable; publish that, don't publish noise.
- **Fix the data, the task and the process before the threshold** — and gate the gap so it cannot regress.

---

## 13. Completion checklist

- [ ] I report per-subgroup metrics matched to the direction of harm.
- [ ] I attach intervals and declare minimum cell sizes.
- [ ] I report stratified as well as aggregate results.
- [ ] I can explain which fairness definition my system optimises and who chose it.
- [ ] I publish coverage gaps instead of underpowered numbers.
- [ ] I scored at least 10/13 on the quiz.

---

## 14. References

- M3-L14 (metrics, baselines, reproducibility) and M3-L13 (splits and imbalance) — the measurement foundation `[STABLE]`
- M5-L18 (building an evaluation dataset you can trust) — why the evaluation set's composition decides what you can see `[STABLE]`
- E. B. Wilson (1927), score interval for a proportion — the interval used in §7.2 `[STABLE]`
- J. Kleinberg, S. Mullainathan, M. Raghavan, *Inherent Trade-Offs in the Fair Determination of Risk Scores* (2016) — the
  impossibility result demonstrated in §7.4 `[UNVERIFIED]`
- NIST AI RMF *Measure* function — disaggregated evaluation as a practice; see M10-L16 `[UNVERIFIED — checked in M10-L16]`

---

## 15. Next lesson

→ [M10-L09 — Transparency, User Communication and Human Oversight](M10-L09-transparency-oversight.md) asks what the people
using and affected by the system are told, and whether the human "in the loop" is really able to intervene.
