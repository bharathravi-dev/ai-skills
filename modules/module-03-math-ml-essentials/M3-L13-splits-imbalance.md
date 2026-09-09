# M3-L13 — Splits, Class Imbalance and Stratification

| | |
|---|---|
| **Lesson ID** | M3-L13 |
| **Difficulty** | 2 (Intermediate) |
| **Estimated study time** | 2 hours |
| **Prerequisites** | [M1-L06](../module-01-ai-foundations/M1-L06-training-validation-testing-inference.md), [M1-L09](../module-01-ai-foundations/M1-L09-data-leakage.md), [M3-L03](M3-L03-statistics.md) |

---

## 1. Learning objectives

1. **Choose** the right split strategy — random, stratified, grouped or temporal — for a given dataset.
2. **Explain** why a random split silently breaks when rows are correlated.
3. **Quantify** the sampling variability of a small test set and state when a score difference is
   meaningless.
4. **Handle** class imbalance with class weights, resampling and threshold tuning, and explain the
   trade-offs of each.
5. **Implement** stratified k-fold cross-validation and interpret its variance.

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **Stratified split** | A split preserving each class's proportion in every part. |
| **Grouped split** | A split keeping all rows sharing an entity in the same part. |
| **Temporal split** | A split by time — train on the past, test on the future. |
| **k-fold cross-validation** | Rotating the validation set over `k` disjoint folds. |
| **Class imbalance** | One class dominating the dataset. |
| **Majority / minority class** | The most / least frequent class. |
| **Oversampling** | Duplicating or synthesising minority examples. |
| **Undersampling** | Discarding majority examples. |
| **Class weight** | Multiplying the loss on a class to raise its influence. |
| **Decision threshold** | The probability above which you predict the positive class. |
| **Base rate** | The positive class's natural frequency (M3-L04). |
| **SMOTE** | Synthetic Minority Over-sampling Technique. |

---

## 3. Plain-language explanation

M1-L06 established *why* you split: to measure how well a model does on data it has not seen. This
lesson is about *how*, because the obvious method — shuffle and slice — is wrong more often than it
is right.

**The single question that determines your split strategy:**

> **Are any two rows in my dataset related in a way that would let a model cheat?**

If yes, a random split will scatter related rows across train and test, the model will effectively see
the test data, and your score will be an overestimate. This is the leakage of M1-L09, arriving through
the split itself.

| If rows are related by… | Use |
|---|---|
| Nothing; rows are independent | **Random split** |
| Class, and one class is rare | **Stratified split** |
| An entity — user, patient, document, customer | **Grouped split** |
| Time — the future is what you predict | **Temporal split** |
| Both an entity *and* time | **Grouped temporal split** |

**The second problem is imbalance.** If 1% of transactions are fraudulent, a model that predicts "not
fraud" every single time is 99% accurate and completely worthless. Imbalance breaks your metric, your
split and your training, and it needs handling in all three places.

---

## 4. Analogy

**Setting an exam.** Random splitting is drawing questions from a hat. It works if the questions are
independent — but if the hat contains four questions from the same past paper and the students have
seen that paper, the exam measures recall of that paper, not understanding. **Grouped splitting is
making sure all four go on the same side.**

### Where the analogy breaks

1. **A student who saw the paper knows it. A model's "cheating" is silent** — nothing in the training
   logs indicates it happened. You only find out in production.
2. **Exams are graded once. Splits are re-used dozens of times**, and every re-use erodes the test
   set's honesty (M1-L06 §5.6).
3. **Students improve between exams. A test set does not** — reusing it makes it progressively more
   optimistic, not more accurate.
4. **Exam marks have known uncertainty conventions.** Model scores usually do not, which is why §5.4
   matters so much.

---

## 5. Detailed technical explanation

### 5.1 Random split

```python
rng = np.random.default_rng(42)
idx = rng.permutation(len(X))
n_test = int(0.2 * len(X))
test_idx, train_idx = idx[:n_test], idx[n_test:]
```

**Valid only when rows are genuinely independent.** Always seed it, and record the seed — an unseeded
split is unreproducible and any comparison against it is worthless.

### 5.2 Stratified split

With a 2% positive class and a 200-row test set, a random split gives you about 4 positives — and
sometimes 0, at which point the recall is undefined and the run is wasted.

Stratification splits **within each class** and concatenates:

```python
for cls in np.unique(y):
    cls_idx = rng.permutation(np.where(y == cls)[0])
    k = int(round(test_frac * len(cls_idx)))
    test_idx.extend(cls_idx[:k])
    train_idx.extend(cls_idx[k:])
```

Every part now has the same class proportions, and the variance of your score drops. **Stratify by
default for classification** — it costs nothing and removes a whole class of accident.

Stratify on other things too when they matter: language, region, source system, document length band.

### 5.3 Grouped split

The rule: **if a model could identify the entity, split by the entity.**

```python
groups = df["user_id"].to_numpy()
unique = rng.permutation(np.unique(groups))
test_groups = set(unique[:int(0.2 * len(unique))])
test_mask = np.isin(groups, list(test_groups))
```

Examples where a random split is wrong:

| Data | The group | What leaks otherwise |
|---|---|---|
| Multiple support tickets per customer | `customer_id` | Customer-specific phrasing |
| Several scans per patient | `patient_id` | Patient anatomy |
| Chunks of the same document (RAG!) | `document_id` | Document wording |
| Repeated sessions per user | `user_id` | Individual habits |
| Near-duplicate scraped pages | Content hash | The duplicate itself |

**The RAG row is the one that will bite you in Module 7.** Chunking a document produces many highly
similar rows; a random split puts near-identical chunks on both sides and your retrieval evaluation
becomes meaningless. M7-L16 returns to this.

Note that group sizes vary, so a grouped split will not give you exactly 20% of rows. Accept the
approximation, or use a greedy assignment to get closer.

### 5.4 How much does a test score even mean?

A test score is an **estimate from a sample**, so it has a standard error (M3-L03 §5.5):

$$SE = \\sqrt{\\frac{p(1-p)}{n}}$$

| Test size | Accuracy | SE | Rough 95% interval |
|---|---|---|---|
| 100 | 0.90 | 0.030 | 0.84 – 0.96 |
| 1,000 | 0.90 | 0.0095 | 0.88 – 0.92 |
| 10,000 | 0.90 | 0.0030 | 0.894 – 0.906 |

**With 100 test rows, 90% and 85% are not distinguishable.** Deciding between two models on that
evidence is coin-flipping with extra steps. This is the single most common quiet error in applied ML,
and the lab measures it by re-splitting the same data 200 times.

A practical floor: **you need roughly 100 examples of the rarest class** in your test set before the
per-class numbers mean much. With a 1% positive rate that implies a 10,000-row test set.

### 5.5 Cross-validation

When data is scarce, rotate the validation set:

```
Fold 1: [VAL][   train   ]
Fold 2: [ tr ][VAL][ tr  ]
...
Fold 5: [    train   ][VAL]
```

Every row is validated exactly once. Report **mean ± standard deviation** across folds — the standard
deviation is the point, because it tells you how much of your score is luck.

- **Stratified k-fold** for classification — the default.
- **Grouped k-fold** when entities repeat.
- `k = 5` or `10`. Higher `k` means more training data per fold and `k×` the compute.
- **Never cross-validate across a temporal boundary.** Use forward-chaining instead.

**Cross-validation replaces the validation set, not the test set.** Keep a final held-out test set
that no fold ever touched.

### 5.6 Temporal splits and forward chaining

If your model predicts the future, your test set must be the future.

```
|--- train ---|-- val --|-- test --|
      past      recent    newest
```

For repeated evaluation, use **forward chaining**:

```
Fold 1: train [1..3]  test [4]
Fold 2: train [1..4]  test [5]
Fold 3: train [1..5]  test [6]
```

Training data only ever precedes test data. M1-L06 §7.3 measured this: a random split understated the
error by 30× on data with a genuine trend.

**Add a gap** between train and test when your features use recent history. If a feature is a 7-day
rolling average, a test row one day after the cut still contains six days of training data.

### 5.7 Class imbalance — four tools

**Tool 1: Class weights.** Multiply each class's loss contribution:

```python
weight_for_class_c = n_total / (n_classes * count_of_class_c)
```

For 99% / 1%, the minority gets ~50× the weight. **Preferred**: no data is duplicated or discarded,
and it works with any loss.

**Tool 2: Oversampling.** Duplicate minority rows until balanced. Simple, but duplicates increase
overfitting risk — the model can memorise a duplicated row.

**Tool 3: Undersampling.** Discard majority rows. Fast and sometimes surprisingly effective, but you
are throwing away real data.

**Tool 4: Threshold tuning.** Train normally, then *move the decision threshold* away from 0.5:

```python
threshold = 0.23              # chosen on VALIDATION, never on test
pred = (proba >= threshold)
```

**This is the most underrated of the four.** It requires no retraining, is fully reversible, and lets
you set the precision/recall balance from the business requirement rather than from an arbitrary
default. M3-L14 covers how to pick it.

**A critical rule for tools 2 and 3: resample the training set only.** Resampling before splitting
puts duplicates of the same row on both sides — instant leakage, and an accuracy score that looks
wonderful. The lab demonstrates exactly how wonderful, and exactly how false.

**SMOTE** synthesises new minority points by interpolating between neighbours instead of copying.
It helps on some tabular problems and hurts on others; it is not a default. `[UNVERIFIED — results
vary widely by dataset]`

### 5.8 Assumptions and limitations

- All of this assumes train and production data come from the same distribution. When that fails
  (drift, M13-L13), every split strategy is optimistic.
- Stratification on many variables at once quickly becomes infeasible.
- Class weights change the model's calibration: predicted probabilities no longer match observed
  frequencies. If you need calibrated probabilities, recalibrate afterwards.
- Cross-validation gives a better *estimate*; it does not make a small dataset large.

---

## 6. Worked example — a fraud dataset done wrong, then right

**Data:** 10,000 transactions, 100 fraudulent (1%). Customers appear on average 5 times.

### Attempt 1 — random split, accuracy metric

```
Test set: 2,000 rows, ~20 fraud
Model: predict "not fraud" always
Accuracy: 1,980 / 2,000 = 99.0%
```

**99% accuracy, zero fraud caught.** The accuracy metric is dominated by the majority class. Compare
against the **majority-class baseline** (M1-L11) and this "model" is worth exactly nothing.

### Attempt 2 — oversample first, then split

The lab runs exactly this on a 1%-positive dataset (§7.3):

| Procedure | Accuracy | Precision | Test rows already seen in training |
|---|---|---|---|
| Oversample **then** split | **0.9788** | **0.9596** | **1,496 / 2,970 (50%)** |
| Split **then** oversample | 0.9633 | 0.2143 | 0 / 1,500 (0%) |

**The first row is fake, and it is fake by a lot.** Precision 0.96 against 0.21 — a 4.5× difference
produced entirely by the ordering of two operations. Half of the test rows have an identical twin in
the training set, so the model is being scored on data it memorised. Production performance will
collapse and the post-mortem will be painful.

**Split first, resample the training side only.**

### Attempt 3 — random split, but customers repeat

```
Split randomly. Customer 4471 has 5 transactions: 4 in train, 1 in test.
```

The model learns customer 4471's spending pattern from the 4 and is tested on the 5th. It looks
excellent on known customers and fails on new ones — which is the case that actually matters, since
you are trying to catch fraud on accounts you have not seen behaving fraudulently before.

### Attempt 4 — correct

```
1. GROUP split on customer_id: no customer spans train and test.
2. STRATIFY within that, so both sides carry ~1% fraud.
3. TRAIN with class_weight, on the training set only.
4. TUNE the decision threshold on VALIDATION.
5. REPORT precision, recall and PR-AUC (M3-L14) — never accuracy alone.
6. COMPARE against the majority-class baseline.
```

Measured outcome on the lab's 1% dataset (§7.3), all on an honest stratified split:

| Approach | Accuracy | Precision | Recall | Fraud caught |
|---|---|---|---|---|
| Majority baseline (predict "not fraud") | **0.9900** | — | 0.00 | **0 of 15** |
| No imbalance handling | **0.9920** | 1.00 | 0.20 | 3 of 15 |
| Class weights | 0.9513 | 0.17 | **1.00** | 15 of 15 |
| **Threshold tuned to 0.18** | **0.9967** | **0.75** | **1.00** | **15 of 15** |

**Read the first two rows carefully.** The useless model that catches zero fraud scores 99.00%. The
barely-useful model that catches 3 of 15 scores **99.20% — the highest accuracy of any approach that
is not the tuned one**. If accuracy were your metric, you would ship the model that misses 80% of the
fraud.

**And note which approach won.** Threshold tuning used the *same trained model* as "no handling" — no
retraining, no resampling, just a different cut point chosen on validation data. It caught every fraud
case at 0.75 precision. That is why §5.7 calls it the most underrated of the four tools.

**The inversion is the lesson.** Class weights *lowered* accuracy from 0.9920 to 0.9513 while taking
recall from 0.20 to 1.00. Fixing an evaluation usually makes the headline number look worse. **A score
that drops when you fix the split or the metric was never real.**

---

## 7. Practical activity

**File:** [`labs/m3/l13_splits_imbalance.py`](../../labs/m3/l13_splits_imbalance.py)

```bash
source .venv/bin/activate
python labs/m3/l13_splits_imbalance.py
```

Measures test-set variability over 200 re-splits, compares random vs stratified class proportions,
shows a grouped split changing the score, reproduces the resample-before-split leak, compares the four
imbalance tools, and runs stratified k-fold.

### 7.2 Expected output

`[EXECUTED]` on Python 3.12.3, NumPy 2.5.3, 2026-09-08.

```text

========================================================================
1. HOW MUCH DOES A TEST SCORE DEPEND ON THE SPLIT?  (200 re-splits each)
========================================================================
    test size   mean acc       sd      min      max   predicted SE    range
           50     0.7464   0.0622   0.5600   0.9200         0.0615   0.3600
          100     0.7454   0.0460   0.6000   0.8600         0.0436   0.2600
          250     0.7444   0.0264   0.6840   0.8120         0.0276   0.1280
         1000     0.7437   0.0115   0.7130   0.7730         0.0138   0.0600
         5000     0.7431   0.0045   0.7314   0.7560         0.0062   0.0246
        10000     0.7429   0.0000   0.7429   0.7429         0.0044   0.0000

  (n=10000 shows sd exactly 0 because the pool IS 10000 rows: sampling all
   of them without replacement gives the same test set every time. With no
   sampling there is no sampling variability -- the formula's SE is the
   uncertainty about the wider population, which does not vanish.)

  The 'sd' column tracks the predicted SE closely -- the formula works.
  At n=50 the SAME model scores anywhere in a range of ~0.2 accuracy
  depending only on which rows you happened to test it on.

  A 2-point accuracy gap needs about n >= 5,000 test rows
  to be distinguishable (2 * SE * sqrt(2) = 0.0173 < 0.02).

========================================================================
2. RANDOM vs STRATIFIED  (2% positive class, 200-row test set)
========================================================================
  method           mean % pos       sd    min    max   runs with 0 pos
  random                 3.93     2.02      0     12                13
  stratified             4.00     0.00      4      4                 0

  Counts are positives in a 200-row test set; 2% means 4 are expected.
  Random splitting sometimes yields ZERO positives -- recall is then
  undefined and the run is wasted. Stratifying gives exactly 4, always.

========================================================================
3. GROUPED SPLIT  (300 customers, 8 transactions each, customer-id feature)
========================================================================
  split                       test acc   customers in both   test rows from seen custs
  random (WRONG here)           0.7450                 266                   600 / 600
  grouped by customer           0.5783                   0                     0 / 600

  The random split overstates accuracy by 0.1667 (16.7 percentage points).
  Both numbers are computed on held-out ROWS, so both look legitimate.
  But in the random split every test customer was also a TRAINING customer,
  so the model had already learned their individual risk. The grouped
  number is what you will actually see on customers you have never
  observed -- which is the deployment case for fraud detection.

========================================================================
4. THE RESAMPLE-BEFORE-SPLIT LEAK  (1% positive)
========================================================================
  dataset: 6000 rows, 60 positive (1.0%)

  procedure                           test acc  precision   recall   test rows seen in train
  oversample THEN split (WRONG)         0.9862     0.9731   1.0000        1482 / 2970  (50%)
  split THEN oversample (right)         0.9687     0.2419   1.0000            0 / 1500  (0%)

  The wrong procedure reports a better-looking model. It is not a better
  model; it is the same model scored on rows it was trained on.

========================================================================
5. FOUR IMBALANCE TOOLS ON THE SAME DATA  (1% positive, honest split)
========================================================================
  train 4500 rows (45 pos)   test 1500 rows (15 pos)

  approach                           acc  precision   recall   TP   FP   FN
  majority baseline (all neg)     0.9900        nan   0.0000    0    0   15
  no handling                     0.9907     1.0000   0.0667    1    0   14
  class weights                   0.9680     0.2381   1.0000   15   48    0
  oversample train only           0.9680     0.2381   1.0000   15   48    0
  undersample majority            0.9700     0.2500   1.0000   15   45    0
  threshold tuned (0.13)          0.9933     0.6000   1.0000   15   10    0

  The majority baseline scores 0.9900 accuracy while catching ZERO
  positives. Every approach that actually finds positives has LOWER
  accuracy. Reporting accuracy alone would rank the useless model first.
  Threshold tuning used the SAME trained model as 'no handling' -- no
  retraining, just a different cut point chosen on validation data.

========================================================================
6. STRATIFIED 5-FOLD CROSS-VALIDATION
========================================================================
  every row validated exactly once: True
  fold sizes: [1200, 1200, 1200, 1200, 1200]
  positives per fold: [12, 12, 12, 12, 12]  (whole dataset: 60)

  fold       val n   accuracy   precision    recall
  1           1200     0.9667      0.2308    1.0000
  2           1200     0.9633      0.2143    1.0000
  3           1200     0.9675      0.2353    1.0000
  4           1200     0.9675      0.2353    1.0000
  5           1200     0.9667      0.2308    1.0000

  accuracy : 0.9663 +/- 0.0015
  precision: 0.2293 +/- 0.0078
  recall   : 1.0000 +/- 0.0000

  Report the spread, not just the mean. A single split would have handed
  you ONE of these folds -- precision anywhere from 0.2143 to 0.2353,
  a 0.0210 range -- with nothing to tell you how much of it was luck.
  Recall is 1.0000 in every fold: class weighting has pushed the threshold
  low enough to catch everything, at a precision cost. That is a choice,
  not a result -- M3-L14 covers how to make it deliberately.

Done.
```

### 7.3 Reading the result

**Section 1 is the one to internalise.** A *single fixed model* — trained once, never changed — is
scored on 200 different test sets of each size:

| Test size | Measured sd | Predicted SE | Worst-to-best range |
|---|---|---|---|
| 50 | 0.0622 | 0.0615 | **0.5600 → 0.9200** |
| 100 | 0.0460 | 0.0436 | 0.6000 → 0.8600 |
| 1,000 | 0.0115 | 0.0138 | 0.7130 → 0.7730 |
| 5,000 | 0.0045 | 0.0062 | 0.7314 → 0.7560 |

**On 50 test rows the same model scored anywhere from 0.56 to 0.92.** Not a better model, not a worse
one — the same weights, scored on different rows. If you have ever compared two models on a small test
set and picked the winner, this is what you were actually measuring.

The measured sd tracks the `√(p(1−p)/n)` prediction closely, which means §5.4's formula is usable for
planning: the lab computes that distinguishing a **2-percentage-point** difference needs about
**5,000 test rows**. Most people's test sets are far smaller than that, and most reported 2-point
improvements are therefore unfalsifiable.

**Section 2** shows why to stratify. Over 500 random 200-row test sets drawn from 2%-positive data,
the positive count varied from **0 to 12** (sd 2.02), and **13 of 500 runs contained zero positives** —
recall undefined, run wasted. Stratification gave exactly 4 every time, sd **0.00**.

**Section 3 is the grouped-split result, and the gap is large.** The model has a customer-identity
feature and each customer has a latent risk level:

| Split | Test accuracy | Test rows from customers seen in training |
|---|---|---|
| Random | **0.7450** | **600 / 600 (100%)** |
| Grouped by customer | **0.5783** | 0 / 600 |

**A 16.7-percentage-point overstatement.** Both numbers were computed on held-out rows, so both look
legitimate in a notebook. But every customer in the random test set was also a training customer, so
the model had already memorised their individual risk. 0.578 is what you would actually get on a new
customer — and 0.578 against a 0.5 baseline says the observable features carry very little signal,
which is a finding you would never have reached from the 0.745.

**Section 4** quantifies the leak in the §6 worked example. **Section 5** produces the imbalance table
in §6, including the result that the useless majority baseline (0.9900) beats every honest approach on
accuracy except the tuned one.

**Section 6** shows stratified 5-fold working correctly — every row validated exactly once, exactly 12
positives in each of 5 folds — and reports **precision 0.2293 ± 0.0078**. A single split would have
handed you one number between 0.2143 and 0.2353 with nothing to indicate the spread. Note that recall
is 1.0000 in **every** fold with zero variance: class weighting has pushed the effective threshold low
enough to catch everything. That is a *choice about the precision/recall trade-off*, not a result, and
M3-L14 is about making it deliberately rather than by accident.

---

## 8. Common mistakes and troubleshooting

1. **Random splitting correlated rows.** Ask what a row belongs to before you shuffle.
2. **Resampling before splitting.** The single most common way to fabricate a great score.
3. **Reporting accuracy on imbalanced data** without the majority-class baseline.
4. **Comparing models on a 100-row test set.** The difference is noise.
5. **Not stratifying**, then getting a fold with zero positives.
6. **Tuning the threshold on the test set.** That is now a validation set; you no longer have a test.
7. **Cross-validating across time.**
8. **Not recording the split seed.**
9. **No gap between train and test** when features use rolling windows.

| Symptom | Likely cause | Fix |
|---|---|---|
| Test accuracy suspiciously high | Leakage via the split | Check for repeated entities and duplicates |
| Score drops hugely in production | Random split on grouped data | Grouped split |
| Recall is `nan` | Zero positives in a fold | Stratify |
| Score varies wildly between seeds | Test set too small | Enlarge it; cross-validate; report ± |
| 99% accuracy, 0 recall | Imbalance | Class weights; threshold; PR metrics |
| Great CV, bad test | CV set-up leaks | Group and stratify inside the folds |
| Probabilities look wrong after weighting | Weighting changes calibration | Recalibrate |

---

## 9. Security, privacy, reliability, cost

- **Privacy.** Grouped splits usually key on a person identifier. Hash or pseudonymise it — you need
  the *grouping*, not the identity. Never let a raw customer ID into an artefact you share.
- **Privacy.** Duplicated minority rows from oversampling raise memorisation risk, which matters if
  the data is personal. Prefer class weights.
- **Reliability.** Store split indices (or the seed and method) with the model. "Which rows were in
  the test set?" is a question you will be asked during an incident.
- **Governance.** Stratify by protected attributes when you are required to report per-group
  performance — you cannot measure a subgroup you have no examples of. (M10-L09.) Note that measuring
  fairness is not the same as achieving it, and neither establishes legal compliance.
- **Cost.** 5-fold CV is 5× the training cost. On anything large, use a single held-out validation set
  and spend the budget on data instead.

---

## 10. Exercises

### Exercise 1 — Beginner (~20 min)

For each dataset, name the split strategy and the reason:

1. 50,000 independent product reviews, balanced sentiment.
2. 3,000 chest X-rays from 800 patients, 4% positive.
3. Daily electricity demand, 2019–2025.
4. 200,000 chunks from 4,000 policy documents, for a RAG evaluation.
5. 1M transactions from 60,000 customers over 3 years, 0.3% fraud.
6. Compute the SE of a 0.88 accuracy on 250 test rows. Is a 0.91 model better?

### Exercise 2 — Intermediate (~35 min)

1. Implement `stratified_split(X, y, test_frac, seed)` and verify class proportions match within 1%.
2. Split a 2%-positive dataset 200 times randomly and 200 times stratified. Report the sd of the
   positive rate in the test set for each.
3. Implement `grouped_split(X, y, groups, test_frac, seed)` and assert no group spans both sides.
4. Build a dataset where each group has a strong group-specific signal. Report test accuracy under a
   random split and under a grouped split, and explain the gap.
5. Reproduce the oversample-before-split leak: report both the leaked score and the honest one.

### Exercise 3 — Challenge (~40 min)

1. Implement stratified k-fold from scratch. Verify every row is validated exactly once and each
   fold's class proportions match the whole.
2. On a 1% dataset, compare: no handling · class weights · oversampling · undersampling · threshold
   tuning. Report accuracy, precision and recall for each, plus the majority baseline.
3. Implement forward-chaining CV for time series and show that a standard k-fold gives a materially
   better — and wrong — score on trending data.
4. Add a rolling-average feature and show that a temporal split with no gap still leaks. Find the gap
   size that removes it.
5. Take a dataset with 5% near-duplicates. Show the accuracy inflation a random split produces, then
   deduplicate by content hash and re-measure.
6. For test sizes 50 → 20,000, plot the sd of measured accuracy over 200 re-splits. Mark the size at
   which a 2-point difference becomes distinguishable.

---

## 11. Quiz

**Q1.** 3,000 X-rays from 800 patients. Which split?

- A. Random.
- B. Grouped by `patient_id` — otherwise scans of the same patient appear on both sides and the
  model is scored on patients it has already learned.
- C. Temporal.
- D. No split needed.

**Q2.** Your data is 1% positive. Why stratify?

- A. It improves accuracy.
- B. Without it a small test set may contain very few positives — or none — making per-class metrics
  unstable or undefined.
- C. It is faster.
- D. It removes the imbalance.

**Q3.** You oversample the minority class and then split randomly. What happens?

- A. Nothing; this is standard practice.
- B. Duplicates of the same row land in both train and test, so the model is tested on rows it
  memorised and the score is fabricated.
- C. The model underfits.
- D. Training gets slower.

**Q4.** A model is 90% accurate on 100 test rows. The approximate standard error is:

- A. 0.001  B. 0.03  C. 0.3  D. 0

**Q5.** Model A scores 0.90 and model B 0.85, on a 100-row test set. What can you conclude?

- A. A is clearly better.
- B. Very little — the difference is within about one standard error, so the ranking could easily
  reverse on a different split.
- C. B is better.
- D. Both are overfitting.

**Q6.** Which imbalance tool requires no retraining and is fully reversible?

- A. Oversampling  B. Undersampling  C. Threshold tuning  D. SMOTE

**Q7.** Why must you never cross-validate across time on a time series?

- A. It is slower.
- B. Folds would train on data from after the validation period, so the model uses information that
  would not exist at prediction time.
- C. It needs more memory.
- D. You may.

**Q8.** Fixing a leaky split makes your reported accuracy drop from 99% to 96%. This means:

- A. You broke the model.
- B. The 99% was never real — the honest number is 96%, and the model is now measurable.
- C. You should revert.
- D. The test set is too small.

**Q9.** In a RAG evaluation, chunks from the same document are split randomly across train and test.
What is the consequence?

- A. Nothing.
- B. Near-identical chunks appear on both sides, so retrieval quality is measured against text the
  system has effectively already been given — the score is inflated.
- C. Retrieval gets slower.
- D. Embeddings become invalid.

**Q10.** *(Written, rubric-graded.)* In under 100 words, describe the split strategy you would use for
1M transactions from 60,000 customers over 3 years with 0.3% fraud, and justify each element.

---

## 12. Revision notes

- **One question decides the split:** *are any two rows related in a way that would let the model
  cheat?*
- Random (independent rows) · **Stratified** (rare classes — the classification default) ·
  **Grouped** (repeated entities) · **Temporal** (predicting the future) · combine as needed.
- **Split first, resample second, training side only.** Measured: resampling first put **50% of test
  rows in the training set** and lifted precision from 0.21 to 0.96 — entirely fabricated.
- Measured: a random split on customer-grouped data **overstated accuracy by 16.7 points** (0.745 vs
  0.578) with 100% of test rows coming from customers seen in training.
- **A test score is an estimate.** `SE = √(p(1−p)/n)`. Measured: on **50 test rows the same model
  scored 0.56 to 0.92**; distinguishing a 2-point difference needs about **5,000 test rows**.
- Rule of thumb: **~100 examples of the rarest class** in the test set before per-class numbers mean
  much.
- CV replaces the **validation** set, not the test set. Report **mean ± sd** across folds.
- Time series: **forward chaining**, and **add a gap** if features use rolling windows.
- Imbalance tools: **class weights** (preferred) · oversampling (memorisation risk) · undersampling
  (throws data away) · **threshold tuning** (no retraining, reversible, underrated).
- **Never report accuracy alone on imbalanced data.** Always show the majority-class baseline.
- **A score that drops when you fix the split was never real.**

---

## 13. Completion checklist

- [ ] I can name the right split for each of the six exercise-1 datasets.
- [ ] I implemented stratified and grouped splits and asserted their properties.
- [ ] I reproduced the resample-before-split leak and saw the 0.96 → 0.21 precision drop.
- [ ] I saw the same model score 0.56–0.92 on 50-row test sets.
- [ ] I can compute the SE of a test score and say when a difference is meaningless.
- [ ] I compared all four imbalance tools on the same data.
- [ ] I implemented stratified k-fold and reported mean ± sd.
- [ ] I scored 7/10 on the quiz.

---

## 14. References

- scikit-learn, *Cross-validation*.
  <https://scikit-learn.org/stable/modules/cross_validation.html> `[UNVERIFIED]`
- scikit-learn, `StratifiedGroupKFold`.
  <https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.StratifiedGroupKFold.html>
  `[UNVERIFIED]`
- Chawla et al. (2002), *SMOTE*. <https://arxiv.org/abs/1106.1813> `[UNVERIFIED]`

---

## 15. Next lesson

→ [M3-L14 — Metrics: Accuracy, Precision, Recall, F1 and Baselines](M3-L14-metrics.md)

Your split is honest. Next: making sure the number you compute on it is the right number.
