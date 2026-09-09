# M1-L09 — Data Leakage and Evaluation Contamination

| | |
|---|---|
| **Lesson ID** | M1-L09 |
| **Difficulty** | 2 (Core) |
| **Estimated study time** | 1.25 hours |
| **Prerequisites** | [M1-L08](M1-L08-generalization-overfitting.md) |

---

## 1. Learning objectives

1. **Define** data leakage and **explain** why it is more dangerous than overfitting.
2. **Identify** the five common leakage types and **name** the diagnostic for each.
3. **Audit** a feature list for target leakage using the availability-at-prediction-time test.
4. **Explain** evaluation contamination in LLM applications, including benchmark contamination.
5. **Design** a leakage check you can run before trusting any evaluation result.

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **Data leakage** | Information reaching the model during training that will not be available at prediction time, or that comes from the evaluation data. |
| **Target leakage** | A feature that is a consequence of the label, or contains it. |
| **Train–test contamination** | Test examples, or information derived from them, present in training. |
| **Temporal leakage** | Using future information to predict the past. |
| **Group leakage** | Related examples split across train and test, so the model recognises the entity. |
| **Preprocessing leakage** | Computing statistics (mean, vocabulary, scaler) over the whole dataset before splitting. |
| **Duplicate leakage** | Near-identical examples in both splits. |
| **Benchmark contamination** | A pretrained model having seen the evaluation data during pretraining. |
| **Proxy variable** | A feature that indirectly encodes something else, including the label. |
| **Availability test** | Asking whether a value would be known at the moment of prediction. |
| **Provenance** | A record of where each piece of data came from. |

---

## 3. Plain-language explanation

Overfitting shows a warning sign: training performance far exceeds validation performance, and you
can see the gap. **Leakage removes the warning sign.** With leakage, training *and* validation *and*
test all look excellent — and the system fails in production.

Leakage means the model got information it will not have in real use. There are two flavours:

1. **The answer was in the input.** You accidentally included a feature that is caused by, or
   contains, the thing you are predicting. Example: predicting whether a customer will cancel, using
   the field `cancellation_reason`. That field is only populated *after* cancelling. Accuracy: 100%.
   Usefulness: zero.

2. **The test data influenced training.** The evaluation set, or information derived from it, reached
   the model. Then your evaluation measures memory, not skill.

The reason leakage is the most feared problem in applied machine learning is simple: **every number
you would normally use to detect a problem looks fine.** You do not find out until deployment, and by
then you have made promises.

### Connecting to what you already know

| Software situation | Leakage equivalent |
|---|---|
| A test asserting against a value the code just computed | Target leakage — circular |
| A test that passes because of leftover state from a previous test | Train–test contamination |
| Benchmarking a cache with the same query repeatedly | Duplicate leakage |
| A load test against warmed-up data you will not have in production | Temporal leakage |
| Mocking the thing you are trying to test | The general shape of the problem |

Every one of these makes a green test suite that proves nothing. Leakage is the same failure with
higher stakes, because the output is a percentage that sounds like evidence.

---

## 4. Analogy

**An exam where the answers are printed on the back of the paper.**

Everyone scores 100%. The scores are real, the marking is correct, and the results tell you nothing
about who can do the work. Worse: nobody notices, because 100% is not an error condition.

### Where the analogy breaks

1. **A student knows they saw the answers; a model cannot report it.** Leakage is found by auditing
   the data pipeline, never by asking the model.
2. **The exam leak is obvious once found; feature leakage is often subtle.** `n_replies` looks like a
   perfectly reasonable feature. So does `assigned_specialist_team` — until you learn it is only set
   after triage, which is the thing you are predicting.
3. **Exams have one leak channel; pipelines have many.** Features, splits, preprocessing, duplicates,
   time ordering and the pretrained model's own history are six separate channels.
4. **The exam analogy suggests deliberate cheating. Leakage is almost always accidental**, and
   frequently introduced by a well-meaning "helpful" feature or an innocuous line of preprocessing.

---

## 5. Detailed technical explanation

### 5.1 The five types

#### Type 1 — Target leakage

A feature that is a consequence of the label.

| Predicting | Leaky feature | Why |
|---|---|---|
| Will the customer cancel? | `cancellation_reason` | Only exists after cancelling |
| Will this ticket breach SLA? | `resolution_time_hours` | It *is* the label |
| Will the patient be diagnosed with X? | `x_medication_prescribed` | Prescribed because of diagnosis |
| Will this loan default? | `collections_agency_assigned` | Follows default |
| Will this ticket be escalated? | `senior_engineer_assigned` | Assignment happens *at* escalation |

**Diagnostic:** for each feature, ask *"would this value be present, with this value, at the moment I
need the prediction?"* If it is only populated afterwards, or its value changes as a result of the
outcome, it leaks.

**Second diagnostic:** a single feature with implausibly high predictive power is a leakage alarm, not
a success. If one column gives you 97% accuracy on a hard problem, investigate before celebrating.

#### Type 2 — Train–test contamination

Test rows appear in training. Causes: splitting after augmentation; duplicated source records;
re-splitting a dataset that already contains a previous split; concatenating datasets that overlap.

**Diagnostic:** hash every example and check for intersection between splits. Do this literally —
it takes five lines and finds real bugs.

#### Type 3 — Temporal leakage

Training on the future to predict the past. Covered with numbers in M1-L06 — the split lab showed a
30× error difference between random and temporal splits.

Subtler forms:
- A feature computed from a **full-history aggregate**, such as `customer_lifetime_ticket_count`
  computed today and joined onto rows from a year ago.
- A **label defined using a future window** while features come from an overlapping window.

**Diagnostic:** for every feature, ask what timestamp its value was computed at. If a feature's
"as-of" time is later than the prediction time, it leaks.

#### Type 4 — Group leakage

The same entity in both splits. If customer C7 has 40 tickets split across train and test, the model
learns "C7 breaches" rather than a general rule. Also applies to: multiple sentences from one
document, multiple images of one patient, multiple sessions from one user.

**Diagnostic:** measure entity overlap between train and test — the lab in M1-L06 prints exactly
this. 100% overlap is not automatically wrong, but it must be a decision, not an accident.

#### Type 5 — Preprocessing leakage

The quiet one.

```python
# WRONG - the scaler has seen the test set's distribution
X_scaled = scaler.fit_transform(X_all)
X_train, X_test = split(X_scaled)

# RIGHT - fit on train only, then apply
X_train, X_test = split(X_all)
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled  = scaler.transform(X_test)      # transform, NOT fit_transform
```

The same applies to: vocabulary building, imputation of missing values with a mean, feature
selection, PCA, target encoding, and outlier removal thresholds. Anything that computes a statistic
over the data must compute it on **training data only**.

The effect is usually small, which is what makes it insidious — it inflates your number by a few
points and never gets caught.

**Diagnostic:** every `fit` call must occur after the split and see only training data.

### 5.2 Leakage in LLM applications

You train nothing, so types 1–5 seem inapplicable. Three of them apply anyway, plus one that is
unique to pretrained models.

**A. Benchmark contamination.** The model may have memorised your evaluation data during pretraining.
If you evaluate on a public benchmark, a well-known dataset, or public documents, a high score may
measure recall of training data rather than capability.
*Mitigation:* build a **private, synthetic evaluation set** (M5-L18). This is the main reason this
course uses synthetic data throughout.

**B. Few-shot contamination.** An example used in your prompt also appears in your eval set.
Guaranteed correct, measures nothing.
*Mitigation:* keep prompt examples in a separate file from eval data, and assert no overlap in CI.

**C. Retrieval contamination.** Your eval questions were written *by reading the documents you
indexed*, often copying their phrasing. Retrieval succeeds because the question shares rare words
with the chunk. Real users phrase things differently and retrieval collapses.
*Mitigation:* write eval questions from real user language — support tickets, search logs,
interviews — not from the corpus. This is one of the most common and most damaging mistakes in RAG
projects and M7-L19 returns to it.

**D. Answer-in-the-prompt leakage.** Your evaluation harness includes the ground-truth answer
somewhere in the context — in metadata, a filename, or a debugging field. Test it: run the harness
with the retrieved context replaced by empty text. If accuracy stays high, the answer is leaking from
somewhere else.

That last check is cheap, takes ten minutes, and I recommend making it a standing part of any RAG
evaluation.

### 5.3 The general audit procedure

Run this before trusting any evaluation:

1. **Feature availability.** For every feature, state the timestamp it is computed at and confirm it
   precedes prediction time.
2. **Feature power.** Any single feature giving implausible accuracy is a suspect. Drop it and
   re-measure; if accuracy collapses, investigate that feature specifically.
3. **Split integrity.** Hash examples; assert zero intersection between splits.
4. **Entity overlap.** Measure and report it. Decide whether it is acceptable.
5. **Temporal ordering.** Confirm max(train time) ≤ min(test time) where relevant.
6. **Preprocessing order.** Confirm every `fit` happens after the split.
7. **Duplicates.** Check for near-duplicates, not just exact ones.
8. **Sanity check the score.** If it is far better than a domain expert would expect, assume leakage
   until proven otherwise.

Point 8 is the meta-principle: **an unexpectedly good result is a bug report until you have explained
it.** Experienced practitioners are suspicious of their own good news, and this instinct is most of
what separates them from beginners.

### 5.4 Assumptions and limitations

- Some leakage is unfixable without changing the product. If the only strong features arrive after
  the decision point, the task may not be solvable as specified — a legitimate finding to report
  (M14-L03).
- The availability test needs domain knowledge. You cannot audit features for a business you do not
  understand; ask the people who populate the fields.
- Not all overlap is leakage. If your product only ever serves existing customers, entity overlap
  matches reality. **The question is always whether your evaluation matches deployment**, not whether
  it obeys a rule.

---

## 6. Worked example — a 100% accurate useless model

Predict whether a support ticket will be **escalated**.

**The dataset as handed to you:**

| ticket_id | channel | body_len | priority | assigned_team | escalation_note | escalated |
|---|---|---|---|---|---|---|
| 1 | email | 850 | high | tier2 | "customer VIP" | 1 |
| 2 | chat | 120 | low | tier1 | *(empty)* | 0 |
| 3 | email | 430 | medium | tier1 | *(empty)* | 0 |
| 4 | phone | 210 | high | tier2 | "SLA risk" | 1 |

**Step 1 — apply the availability test to every column.**

| Feature | Populated when? | Verdict |
|---|---|---|
| `channel` | At creation | ✅ Safe |
| `body_len` | At creation | ✅ Safe |
| `priority` | At creation (usually) | ⚠️ Check — if agents raise priority *during* escalation, it leaks |
| `assigned_team` | **At escalation** — tier2 *is* the escalation target | ❌ **Target leakage** |
| `escalation_note` | **Only when escalated** | ❌ **Target leakage** — non-empty ⇔ label is 1 |

**Step 2 — see the damage.** `escalation_note` is non-empty exactly when `escalated = 1`. A model
using it achieves **100% accuracy** on train, validation and test. Every diagnostic from M1-L08 looks
perfect: the generalization gap is zero.

In production, the field is empty for every new ticket, because escalation has not happened yet. The
model predicts "not escalated" for everything. **Accuracy in production: equal to the base rate.
Value: none.**

**Step 3 — note that `assigned_team` is subtler and just as fatal.** It looks like a legitimate
operational field. It is only leaky because of a business fact — tier2 assignment *is* how escalation
is recorded. You cannot discover this from the data alone. **You have to ask someone.** This is the
single strongest argument for the discovery work in Module 14.

**Step 4 — `priority` is the interesting case.** It is safe if set at creation and never changed;
leaky if agents raise it as part of escalating. The data may contain both behaviours. Resolution:
check whether an audit log records *when* priority was last modified, and use the value **as of ticket
creation**, not the current value. This is a real pattern — **point-in-time feature reconstruction** —
and it is a large part of why production ML pipelines are harder than notebooks.

**Step 5 — the honest model.**

| Model | Features | Test accuracy | Production accuracy |
|---|---|---|---|
| Leaky | + `escalation_note`, `assigned_team` | **100%** | ~base rate (useless) |
| Honest | `channel`, `body_len`, `priority_at_creation` | **~68%** | ~68% |

**68% is the better model.** It is also the one that will be harder to get approved, because someone
saw 100% first. Managing that conversation is a real professional skill (M14-L10, M14-L12).

---

## 7. Practical activity

**File:** [`labs/m1/l09_leakage.py`](../../labs/m1/l09_leakage.py)

```bash
python3 labs/m1/l09_leakage.py
```

Builds the escalation dataset above, trains the same simple classifier twice — once with the leaky
features, once without — and shows: perfect scores for the leaky model on every split, then what
happens when it meets production data where the leaky fields are empty. It also runs the §5.3 audit
checks and reports which ones fire.

### 7.1 Important lines

| Construct | Why |
|---|---|
| `note_present = 1.0 if row.escalation_note else 0.0` | The leak, made explicit as a feature. |
| `production_row(...)` | Rebuilds each test row **as it would look at prediction time** — leaky fields blanked. This is the check almost nobody runs. |
| `single_feature_accuracy(...)` | Audit step 2: measures each feature alone. Implausible single-feature power is the alarm. |
| `hash(tuple(...))` | Audit step 3: detects identical rows across splits. |

### 7.2 Expected output

`[EXECUTED]` 2026-09-07, Python 3.12.3. Deterministic:

```
========================================================================
DATA LEAKAGE: a model with perfect scores and no value
========================================================================
600 synthetic tickets. Escalation base rate: 31.0%
Splits: train=360 val=120 test=120

MODEL A - includes 'assigned_team' and 'escalation_note'
  train accuracy      : 100.0%
  validation accuracy : 100.0%
  test accuracy       : 100.0%

  Every split looks perfect. The M1-L08 diagnostic says 'good fit':
  training and validation agree, so there is no generalization gap.
  Nothing here looks wrong.

  NOW: the same test rows, as they actually look at prediction time
  (no note yet, no tier2 assignment yet, priority not yet raised):
  production accuracy : 75.0%
  'always predict no' : 75.0%   <- the do-nothing baseline

  The model has collapsed to the baseline. It learned to read a
  field that records the answer, and that field is empty when the
  prediction is actually needed.

MODEL B - only features available at ticket creation
  train accuracy      : 72.8%
  test accuracy       : 78.3%
  'always predict no' : 75.0%

------------------------------------------------------------------------
LEAKAGE AUDIT
------------------------------------------------------------------------
Step 2 - single-feature predictive power (an alarm above ~0.90):
    ch_phone     69.5%
    long_body    65.2%
    prio_high    93.2%   <-- ALARM: investigate this field
    team_tier2   100.0%   <-- ALARM: investigate this field
    has_note     100.0%   <-- ALARM: investigate this field

Step 3 - split integrity (identical rows appearing in two splits):
    train/test overlapping rows: 2

Step 8 - sanity check:
    reported test accuracy = 100.0%
    Is near-perfect accuracy plausible for predicting human
    escalation decisions from a ticket at creation time? No.
    Treat it as a bug report until explained.

------------------------------------------------------------------------
THE LESSON
------------------------------------------------------------------------
* Model A scored perfectly on train, validation AND test. Every
  standard check passed. The generalization gap was zero.

* Model A is worthless. Model B, which looks much worse, is the
  one that works.

* No split strategy would have caught this. Leakage is a DATA
  problem, and it is found by auditing where each field comes
  from and when it is populated - not by better validation.

* The decisive check was rebuilding test rows as they look at
  prediction time. Run it on every project.
========================================================================
```

### 7.3 Reading the result

**Model A's scoreboard is the whole point:**

| | Model A (leaky) |
|---|---|
| train | 100.0% |
| validation | 100.0% |
| test | 100.0% |
| **production-shaped rows** | **75.0%** |
| "always predict no" baseline | **75.0%** |

Every check you learned in M1-L08 passes. Training and validation agree exactly, so the
generalization gap is zero — the diagnostic table says *good fit*. A code reviewer sees three
matching numbers and approves. There is no visible defect anywhere.

Then the model meets rows shaped as they actually arrive, and lands on **exactly the do-nothing
baseline**. Not "somewhat worse" — precisely equal to predicting "no" for everything. That is the
signature of a model whose entire skill was reading a field that records the answer.

**Model B, the honest one, scores 78.3% on test.** Lower than 100%, and genuinely better than the
75% baseline — a modest, real 3.3-point improvement. This is what an honest result on a hard problem
looks like: unimpressive, and worth something. Getting Model B approved after someone has seen
Model A's 100% is a communication problem, not a technical one (M14-L10, M14-L12).

**The audit found the subtle leak too, which is the best part of this run:**

```
prio_high    93.2%   <-- ALARM: investigate this field
team_tier2   100.0%  <-- ALARM: investigate this field
has_note     100.0%  <-- ALARM: investigate this field
```

`team_tier2` and `has_note` are the obvious leaks. But look at **`prio_high` at 93.2%**. Priority
looks like a perfectly legitimate field set when a ticket is created — and in the data generator,
agents *raise priority to high as part of escalating*. The current value of the field is therefore
partly an outcome, not an input.

This is the case from §6 step 4, and it is the realistic one. You would not spot it by reading the
schema, and no split strategy detects it. It surfaces only because the single-feature audit flagged
an implausible 93.2% for a field that ought to be weakly predictive at best. The fix is
**point-in-time reconstruction**: use priority *as of ticket creation* from the audit log, not the
current value.

**Note also step 3 found 2 duplicate rows across train and test.** Small, but real, and found in five
lines of code. Run these checks.

**Verification:** confirm Model A shows `100.0%` on all three splits and `75.0%` on production-shaped
rows, matching the baseline exactly; and that three fields raise alarms in step 2.

---

## 8. Common mistakes and troubleshooting

1. **Celebrating a high score.** Treat unexpectedly good results as bug reports.
2. **Auditing only obvious features.** `escalation_note` is obvious; `assigned_team` is not.
3. **`fit_transform` on the full dataset** before splitting.
4. **Splitting after augmentation or deduplication.** Split first.
5. **Using current field values as historical ones.** Reconstruct point-in-time values.
6. **Evaluating a RAG system on questions written from the indexed documents.**
7. **Assuming a public benchmark score reflects capability** on your data.
8. **Not asking domain experts what each field means and when it is populated.**

| Symptom | Likely leakage type | Diagnostic |
|---|---|---|
| 99%+ on a genuinely hard problem | Target leakage | Per-feature accuracy; drop suspects |
| Excellent offline, base-rate in production | Target leakage | Re-score with leaky fields blanked |
| Great on known entities, poor on new ones | Group leakage | Entity overlap between splits |
| Score drops after re-splitting by time | Temporal leakage | Check feature as-of timestamps |
| Small unexplained boost vs a clean rebuild | Preprocessing leakage | Confirm every `fit` follows the split |
| RAG retrieval perfect on eval, poor live | Retrieval contamination | Rewrite eval questions in user language |

---

## 9. Security, privacy, reliability and cost

- **Reliability.** Leakage is the leading cause of AI projects that pass every internal gate and fail
  on launch. The cost is rarely the compute; it is credibility and rework.
- **Governance.** Release gates (M10-L12) should include an explicit leakage audit with recorded
  results. "We checked for leakage" must be a signed artefact, not a memory.
- **Privacy.** Leakage audits require inspecting raw data, so the audit itself needs access controls
  and logging. Do not solve leakage by giving everyone production data.
- **Cost.** The audit is cheap — hours. Discovering leakage after launch costs a rebuild plus the
  trust of whoever you showed 100% to. This is the highest return-on-effort check in this course.

---

## 10. Exercises

### Exercise 1 — Beginner (~10 min)

For each, name the leakage type and the fix:

1. Predicting fraud using `chargeback_filed`.
2. Scaling all features before splitting.
3. Predicting churn with a random split on 3 years of monthly data.
4. Sentence classification where sentences from one document appear in both splits.
5. Evaluating an LLM on a well-known public benchmark and reporting 94%.

### Exercise 2 — Intermediate (~20 min)

Run the lab, then:

1. What accuracy does the leaky model achieve on the test set, and what does it achieve on the same
   rows presented as they would appear in production?
2. Which audit check fired first, and what did it report?
3. The audit flags `prio_high` at 93.2%. Read `make_data()` and explain exactly why priority is
   partly an outcome rather than an input. Then state how you would fix it in a real system without
   discarding the field.
4. Add a *new* subtle leaky feature of your own — one that is not obviously post-outcome — and
   confirm the audit catches it. Describe what you added and why it is subtle.
5. Model B scores 78.3% against a 75.0% baseline. Write three sentences you would say to a manager
   who has already seen Model A's 100% figure.

### Exercise 3 — Challenge (~25 min)

You join a team whose RAG assistant scores 95% on their 50-question evaluation set. Users say it is
unreliable.

1. List every contamination channel from §5.2 that could produce this, and rank by likelihood.
2. Design the "empty context" test described in §5.2(D). State exactly what you would run and what
   result would prove leakage.
3. The eval questions were written by an engineer who read the documentation. Explain precisely what
   is wrong with this and propose a replacement process.
4. Write the acceptance criteria you would require before you would trust *any* future number from
   this system. Be specific and testable.

---

## 11. Quiz

**Q1.** Why is leakage considered more dangerous than overfitting?

- A. It is harder to fix.
- B. Overfitting shows a visible train/validation gap, whereas leakage makes training, validation and
  test all look excellent, removing every warning sign until production.
- C. It only affects neural networks.
- D. It cannot be detected at all.

**Q2.** Predicting loan default using `collections_agency_assigned` is which type?

- A. Temporal leakage  B. Target leakage  C. Group leakage  D. Preprocessing leakage

**Q3.** Which is the correct order?

- A. Scale the full dataset, then split.
- B. Split, then fit the scaler on training data only, then `transform` validation and test.
- C. Split, then fit a separate scaler on each split.
- D. Order does not matter.

**Q4.** A single feature gives 97% accuracy on a problem experts consider hard. The correct response
is:

- A. Ship it immediately.
- B. Treat it as a leakage alarm: check when the field is populated and whether its value is a
  consequence of the label; drop it and re-measure.
- C. Add more features.
- D. Increase the test set size.

**Q5.** In the §6 example, why is `assigned_team` leaky even though it looks like an ordinary
operational field?

- A. It contains text.
- B. Because tier2 assignment *is* how escalation is recorded, so the field is populated as part of
  the outcome being predicted — a fact discoverable only by asking the business.
- C. Because it has too many categories.
- D. It is not leaky.

**Q6.** Your RAG eval questions were written by an engineer reading the indexed documents. What is
the specific risk?

- A. The questions are too difficult.
- B. Questions inherit the documents' rare wording, so retrieval succeeds on lexical overlap that
  real users' phrasing will not reproduce.
- C. There will be too few questions.
- D. The model will refuse to answer.

**Q7.** What is the "empty context" test?

- A. Running the system with no system prompt.
- B. Replacing retrieved context with empty text and re-running the evaluation; if accuracy stays
  high, the answer is reaching the model from somewhere other than retrieval.
- C. Testing with an empty database.
- D. Removing all few-shot examples.

**Q8.** Your model achieves 100% on train, validation and test. What does the M1-L08 diagnostic table
say, and what should you actually conclude?

- A. It says "good fit", and that conclusion is correct.
- B. It says "good fit" — but a zero generalization gap with a perfect score is the signature of
  leakage, because the M1-L08 diagnostic assumes no leakage.
- C. It says "overfitting"; reduce capacity.
- D. It says "underfitting"; add capacity.

**Q9.** A team splits their data, then removes duplicates from each split independently. What is the
problem?

- A. Nothing.
- B. Duplicates that existed across splits are preserved, so the same example can appear in both
  training and test; deduplication must happen before splitting.
- C. It slows down training.
- D. It causes underfitting.

**Q10.** *(Written, rubric-graded.)* In under 90 words, explain to a product owner why you want to
delay a launch to re-run an evaluation, when the current numbers look excellent.

---

## 12. Revision notes

- **Leakage = information the model will not have at prediction time, or information from the
  evaluation set.** It removes every warning sign; overfitting at least shows a gap.
- Five types: **target** (feature caused by the label) · **train–test contamination** ·
  **temporal** · **group** · **preprocessing**.
- Master diagnostic: *would this value be present, with this value, at the moment I predict?*
- Second diagnostic: **an implausibly strong single feature is an alarm, not a win.**
- Preprocessing rule: **split first, then `fit` on train only, `transform` the rest.**
- LLM-specific: benchmark contamination · few-shot contamination · **retrieval contamination**
  (eval questions written from the corpus) · answer-in-the-prompt. Use private synthetic eval data.
- The **empty-context test** is cheap and catches a lot.
- 8-step audit: availability · feature power · split integrity · entity overlap · temporal order ·
  preprocessing order · duplicates · sanity.
- **Treat unexpectedly good results as bug reports.**

---

## 13. Completion checklist

- [ ] I can name all five leakage types and a diagnostic for each.
- [ ] I can apply the availability test to a feature list.
- [ ] I ran the lab and saw the leaky model collapse on production-shaped rows.
- [ ] I added my own subtle leaky feature and the audit caught it.
- [ ] I can describe the empty-context test.
- [ ] I can explain why 100% on all three splits is alarming, not reassuring.
- [ ] I scored 7/10 on the quiz.

---

## 14. References

- Kaufman et al., "Leakage in Data Mining: Formulation, Detection, and Avoidance" (2011) — the
  standard reference and the source of the type taxonomy. `[UNVERIFIED]`
- Kapoor & Narayanan, "Leakage and the Reproducibility Crisis in ML-based Science" (2023) — surveys
  hundreds of papers invalidated by leakage. `[UNVERIFIED]`

---

## 15. Next lesson

→ [M1-L10 — Probabilistic Behaviour, Uncertainty and Hallucination](M1-L10-probability-uncertainty-hallucination.md)

You have seen how evaluation can lie. Next: how the *model itself* behaves — why the same input can
give different outputs, why fluency is not evidence, and where hallucination actually comes from.
