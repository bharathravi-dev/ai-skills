# M3-L14 — Metrics: Accuracy, Precision, Recall, F1 and Baselines

| | |
|---|---|
| **Lesson ID** | M3-L14 |
| **Difficulty** | 2 (Intermediate) |
| **Estimated study time** | 2.5 hours |
| **Prerequisites** | [M3-L13](M3-L13-splits-imbalance.md), [M1-L11](../module-01-ai-foundations/M1-L11-capability-vs-reliability.md) |

---

> **This lesson is the one you will use most often, and for the longest.**
> You will stop computing gradients by hand within a month. You will be arguing about precision and
> recall for the rest of your career — including for RAG (M7-L16), agents (M8-L15) and LLM evaluation
> (M5-L15), none of which have a loss function but all of which have exactly these trade-offs.

---

## 1. Learning objectives

1. **Build** a confusion matrix and compute every metric from it.
2. **Choose** a metric from the cost of each error type, and defend the choice.
3. **Explain** why ROC-AUC misleads on imbalanced data and when to use PR-AUC instead.
4. **Select** a decision threshold from a business requirement.
5. **Establish** baselines and refuse to report a score without one.
6. **Assess** calibration, and explain why a good ranker can have bad probabilities.
7. **Compute** regression metrics and multi-class averages correctly.

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **Confusion matrix** | Counts of predictions against truth, by class. |
| **TP / FP / FN / TN** | True/false positives and negatives. |
| **Accuracy** | `(TP+TN) / total`. Fraction correct. |
| **Precision** | `TP / (TP+FP)`. *Of those flagged, how many were right?* |
| **Recall** (sensitivity, TPR) | `TP / (TP+FN)`. *Of those that exist, how many did we find?* |
| **Specificity** (TNR) | `TN / (TN+FP)`. |
| **F1** | Harmonic mean of precision and recall. |
| **Fβ** | Weighted harmonic mean; β>1 favours recall. |
| **ROC curve** | TPR against FPR across thresholds. |
| **PR curve** | Precision against recall across thresholds. |
| **AUC** | Area under a curve. |
| **Calibration** | Whether predicted probabilities match observed frequencies. |
| **Macro / micro / weighted average** | Ways to combine per-class metrics. |
| **MAE / RMSE / R²** | Regression metrics. |
| **Baseline** | A trivial reference every model must beat. |

---

## 3. Plain-language explanation

Every classification decision has **two ways to be wrong**, and they usually cost different amounts.

| | Predicted positive | Predicted negative |
|---|---|---|
| **Actually positive** | ✅ True positive | ❌ **False negative** — you missed it |
| **Actually negative** | ❌ **False positive** — a false alarm | ✅ True negative |

**Precision and recall each measure one of the two failures:**

- **Precision** is about false alarms. *When we said yes, how often were we right?*
- **Recall** is about misses. *Of everything we should have found, how much did we find?*

**They trade off, always.** Flag more things and you catch more of the real ones (recall up) while
raising the false alarm rate (precision down). Flag fewer and the reverse. **You cannot maximise both;
you choose where to sit.** And you choose based on which error costs more:

| Situation | Costlier error | Optimise |
|---|---|---|
| Cancer screening | Missing a case | **Recall** |
| Spam filter | Deleting a real email | **Precision** |
| Fraud alerts to a small review team | Wasting their time | **Precision** |
| Legal document discovery | Missing evidence | **Recall** |
| RAG retrieval | Missing the answer | **Recall** (then rerank for precision) |

**The rule that outranks all of this: never report a metric without a baseline.** "94% accurate" is not
information. "94% accurate, against a majority-class baseline of 91%" is. M3-L13 §7.3 measured a case
where the useless baseline scored **99.00%** and a genuinely bad model scored **99.20%**.

---

## 4. Analogy

**A metal detector on a beach.** Precision is what fraction of your digs found metal. Recall is what
fraction of the buried metal you found. Turn up the sensitivity: you find more metal *and* dig far
more holes for bottle caps.

### Where the analogy breaks

1. **You can count the holes you dug, but not the metal you walked past.** Measuring recall requires
   labelled ground truth for things your model *rejected* — which is why recall is expensive to
   measure in production and precision is cheap.
2. **The detector's sensitivity is one dial. A model's threshold is one dial too — but retraining
   changes the whole curve**, which is a different kind of improvement.
3. **All buried metal is equal. Errors are not**: a missed tumour and a missed bottle cap differ by
   orders of magnitude, which is what Fβ and cost matrices are for.
4. **Beach metal does not change. Your data distribution does** (drift, M13-L13), so today's threshold
   may be wrong next quarter.

---

## 5. Detailed technical explanation

### 5.1 Everything from the confusion matrix

```
                  Predicted
                  Neg     Pos
Actual  Neg  |    TN      FP  |
        Pos  |    FN      TP  |
```

```python
accuracy    = (TP + TN) / (TP + TN + FP + FN)
precision   = TP / (TP + FP)          # undefined if nothing was flagged
recall      = TP / (TP + FN)          # undefined if there are no positives
specificity = TN / (TN + FP)
f1          = 2 * precision * recall / (precision + recall)
```

**Always look at the raw counts, not only the ratios.** "Precision 0.5" means something very
different at TP=1, FP=1 than at TP=5000, FP=5000.

### 5.2 F1 and Fβ

F1 is the **harmonic** mean, which is close to the *smaller* of the two:

| Precision | Recall | Arithmetic mean | **F1** |
|---|---|---|---|
| 0.9 | 0.9 | 0.90 | **0.90** |
| 1.0 | 0.5 | 0.75 | **0.67** |
| 1.0 | 0.1 | 0.55 | **0.18** |
| 1.0 | 0.01 | 0.505 | **0.02** |

**That last row is why F1 exists.** A model with perfect precision and 1% recall gets an arithmetic
mean of 0.505 — which sounds acceptable — and an F1 of 0.02, which correctly says the model is
useless. **F1 punishes imbalance between the two; the arithmetic mean hides it.**

**Fβ** shifts the weighting:

$$F_\\beta = (1+\\beta^2)\\cdot\\frac{P \\cdot R}{\\beta^2 P + R}$$

`β = 2` weights recall 2× (medical screening); `β = 0.5` weights precision 2× (spam).

**F1's real weakness: it ignores true negatives entirely**, and it treats a fixed precision/recall
balance as correct regardless of the actual costs. When you know the costs, use them directly — a
cost matrix beats F1 every time.

### 5.3 ROC-AUC versus PR-AUC

**ROC** plots TPR against FPR across all thresholds; **AUC** is the probability that a random positive
scores above a random negative. 0.5 is random, 1.0 is perfect.

**ROC-AUC is misleading on imbalanced data**, and the reason is a base-rate effect (M3-L04):

```
FPR = FP / (FP + TN)
```

With 99,000 negatives, 990 false positives is an FPR of 0.01 — visually negligible on an ROC curve.
But if you flagged 1,000 things total and 990 were wrong, your **precision is 0.01** and the model is
unusable. **ROC-AUC divides false positives by a huge number; precision divides them by a small one.**

| Use | When |
|---|---|
| **ROC-AUC** | Roughly balanced classes; you care about ranking overall |
| **PR-AUC** | **Imbalanced classes; the positive class is what matters** |

A PR curve's random baseline is the **base rate**, not 0.5. PR-AUC 0.30 on a 1% problem is 30× better
than random; ROC-AUC 0.90 on the same problem may be worthless. **Report the base rate alongside
PR-AUC or the number cannot be interpreted.**

### 5.4 Choosing a threshold

The model outputs a probability; **you** choose the cut point. It is not a modelling decision, it is a
product decision, and it belongs to whoever owns the cost of the errors.

**Method 1 — from a capacity constraint.** "The review team handles 50 cases a day." Set the threshold
so about 50 clear it. This is the most common real answer.

**Method 2 — from a requirement.** "We must catch 95% of fraud." Find the lowest threshold meeting
recall ≥ 0.95 on validation, then report the precision it costs. Frequently this is the moment a
stakeholder revises the requirement.

**Method 3 — maximise Fβ** on validation, with β set from the cost ratio.

**Method 4 — expected cost**, when you can put numbers on it:

```python
cost = n_fp * cost_per_false_alarm + n_fn * cost_per_miss
```

Sweep thresholds, pick the minimum. This is the most defensible method and the least used, because it
forces someone to state what a miss actually costs.

**Choose on validation. Never on test.** A threshold tuned on test means you no longer have a test set
(M3-L13 §5.4).

### 5.5 Calibration

A model can rank perfectly and still have wrong probabilities. **AUC is invariant to any monotonic
transformation of the scores** — squaring every probability leaves AUC identical and calibration
destroyed.

Check with a **reliability diagram**: bin predictions, and compare each bin's mean predicted
probability against its observed frequency. Perfect calibration lies on the diagonal.

**Expected Calibration Error (ECE)** is the weighted mean absolute gap across bins.

**When calibration matters:** expected-cost decisions, ranking across differently-trained models,
showing confidence to users, and any downstream system that multiplies probabilities. **When it does
not:** pure top-k ranking.

**Things that break calibration:** class weighting and resampling (M3-L13 §5.8), softmax over a small
label set, and — importantly — **LLM verbalised confidence**. A model saying "I am 90% confident" is
producing text, not a calibrated probability, and it is typically overconfident. M5-L16 returns to
this. Fixes: Platt scaling, isotonic regression, temperature scaling.

### 5.6 Baselines — non-negotiable

| Baseline | Definition |
|---|---|
| **Majority class** | Always predict the most common class |
| **Random** (stratified) | Predict at the base rate |
| **Simple rule** | One hand-written heuristic |
| **Previous model** | What is in production today |
| **Human** | What a person achieves on the same data |

**Report at least the majority-class baseline every time.** For LLM work the equivalents are: keyword
search before an embedding model (M6), no-retrieval before RAG (M7), and a single prompt before an
agent (M8). Each has repeatedly beaten the sophisticated version on real tasks.

### 5.7 Regression metrics

| Metric | Formula | Character |
|---|---|---|
| **MAE** | `mean(|y − ŷ|)` | In the target's units; robust to outliers |
| **MSE** | `mean((y − ŷ)²)` | Punishes large errors; squared units |
| **RMSE** | `√MSE` | Target's units; still outlier-sensitive |
| **MAPE** | `mean(|y − ŷ| / |y|)` | Percentage; **explodes near zero** |
| **R²** | `1 − SS_res/SS_tot` | Fraction of variance explained |

**MAE or RMSE?** If one 100-unit error is as bad as ten 10-unit errors, use MAE. If it is far worse,
use RMSE. RMSE ≥ MAE always, and the gap indicates how skewed your errors are.

**R² cautions:** it can be negative (worse than predicting the mean); it always rises when you add
features; and on tiny samples it is meaningless — M3-L08 §7.3 measured R² = 1.0000 on five points that
happened to lie on a plane.

### 5.8 Multi-class averaging

| Average | How | Use when |
|---|---|---|
| **Micro** | Pool all TP/FP/FN, then compute | You care about overall correctness |
| **Macro** | Per-class metric, then unweighted mean | **Every class matters equally** |
| **Weighted** | Per-class, weighted by support | You want something accuracy-like |

**Macro and micro can differ enormously.** With one dominant class handled well and several rare
classes handled badly, micro looks excellent and macro exposes the failure. **Report macro when rare
classes matter** — which is nearly always the case when someone asks about fairness across groups.

### 5.9 Reproducibility

```python
import random, numpy as np
SEED = 42
random.seed(SEED)
np.random.seed(SEED)
# torch.manual_seed(SEED); torch.use_deterministic_algorithms(True)
```

Record: seed, data version, split method, package versions, threshold, metric definitions. A metric
you cannot reproduce is an anecdote. **Note that seeding does not make a result true** — it makes one
draw repeatable. Report across several seeds when the difference is small (M3-L13 §7.3).

### 5.10 Assumptions and limitations

- Every metric assumes your labels are correct. Label noise caps the achievable score, and above ~95%
  you are often measuring the labellers.
- Aggregate metrics hide subgroup failures. **Always slice.**
- A single number cannot capture a system's behaviour. Report a small set with the baseline.
- Offline metrics do not always predict online outcomes. A/B test where you can.

---

## 6. Worked example — one model, four decisions

**Fraud detection.** 10,000 synthetic transactions, **87 fraudulent (0.87%)**. One trained model. All
numbers below are measured by the lab in §7.3 — nothing here is illustrative.

| Threshold | Flagged | TP | FP | FN | Precision | Recall | F1 | Accuracy |
|---|---|---|---|---|---|---|---|---|
| 0.60 | 5 | 4 | 1 | 83 | **0.800** | 0.046 | 0.087 | **0.9916** |
| 0.40 | 23 | 11 | 12 | 76 | 0.478 | 0.126 | 0.200 | 0.9912 |
| 0.25 | 59 | 21 | 38 | 66 | 0.356 | 0.241 | **0.288** | 0.9896 |
| 0.15 | 103 | 27 | 76 | 60 | 0.262 | 0.310 | 0.284 | 0.9864 |
| 0.08 | 208 | 40 | 168 | 47 | 0.192 | 0.460 | 0.271 | 0.9785 |
| 0.04 | 429 | 51 | 378 | 36 | 0.119 | 0.586 | 0.198 | 0.9586 |
| 0.02 | 787 | 59 | 728 | 28 | 0.075 | 0.678 | 0.135 | 0.9244 |
| 0.01 | 1,358 | 68 | 1,290 | 19 | 0.050 | **0.782** | 0.094 | 0.8691 |

**And the baseline** — predict "not fraud" always: accuracy **0.9913**, recall **0.000**, fraud caught
**0 of 87**.

**Look at the accuracy column, then at the baseline.** At threshold 0.60 the model's accuracy is
**0.9916 — the highest in the table, and above the baseline** — while catching **4 of 87** fraud cases.
By accuracy, the best threshold is the one that does almost nothing. Accuracy on this problem is not
measuring the task; it is measuring the 99% of transactions that are fine.

**Now watch precision and recall move in opposite directions, monotonically, down the table.** That is
not a defect. That is the dial, and someone has to choose where to set it.

### Four organisations, four right answers, one model

| Organisation | Method | Threshold | Flagged | Precision | Recall | False alarms |
|---|---|---|---|---|---|---|
| **A** — 20-case/day review team | capacity | 0.4172 | 21 | 0.476 | 0.115 | 11 |
| **B** — must catch 95% of fraud | requirement | 0.0006 | 5,597 | 0.015 | **0.977** | **5,512** |
| **C** — no cost data available | maximise F1 | 0.2200 | 71 | 0.338 | 0.276 | 47 |
| **D** — FP costs 5, FN costs 500 | expected cost | 0.0100 | 1,358 | 0.050 | 0.782 | 1,290 |

**A** — the team's capacity is 20 cases a day, so the threshold is set to produce about 20. They see
21 cases, about half of which are real fraud, and catch 11.5% of it. That is the honest ceiling of a
20-case-a-day team. **The binding constraint is staffing, not modelling**, and no amount of model work
changes it.

**B** — the 95% requirement is *technically* met, at a threshold of 0.0006. It requires flagging
**5,597 of 10,000 transactions — 56% of all traffic** — to catch 85 real cases, at **64.8 wasted
investigations per catch**. The correct response is not to deploy this. It is to take these numbers
back to whoever wrote the requirement, because "catch 95% of fraud" has just been priced, and the price
is 5,512 false accusations. **This is the single most valuable thing a threshold sweep does**: it turns
an aspiration into a number someone can decide about.

**C** — with no cost information, maximising F1 gives threshold 0.22: 71 flags, precision 0.338,
recall 0.276. Note this is close to A's operating point, which is reassuring but coincidental.
**Nobody's actual business problem is "maximise F1."** It is a defensible default when you genuinely
have no cost data, and a poor substitute for asking.

**D** — with costs stated (a false alarm costs 5, a miss costs 500), the optimum moves to 0.01: catch
78% of fraud and accept 1,290 false alarms. The maths says the misses dominate at a 100:1 cost ratio.
**This is the most defensible method and the least used**, because it requires someone to say out loud
what a miss costs.

**The model is byte-identical in all four rows.** One trained artefact, four deployments, four
completely different correct answers. This is why the threshold belongs to the product owner, why it
must be logged with the model, and why *"what is the model's accuracy?"* is almost always the wrong
question.

## 7. Practical activity

**File:** [`labs/m3/l14_metrics.py`](../../labs/m3/l14_metrics.py)

```bash
source .venv/bin/activate
python labs/m3/l14_metrics.py
```

Computes every metric from scratch, reproduces §6's threshold table, compares ROC-AUC and PR-AUC on an
imbalanced problem, demonstrates AUC's invariance to monotonic transformation, builds a reliability
diagram and ECE, compares baselines, contrasts macro and micro averaging, and compares MAE/RMSE with
and without an outlier.

### 7.2 Expected output

`[EXECUTED]` on Python 3.12.3, NumPy 2.5.3, 2026-09-08.

```text

==========================================================================
1. EVERY METRIC FROM ONE CONFUSION MATRIX  (TP=40 FP=10 FN=60 TN=890)
==========================================================================
                  Predicted
                  Neg      Pos
  Actual  Neg  |    890       10  |
          Pos  |     60       40  |

  accuracy    = (40 + 890) / 1000        = 0.9300
  precision   = 40 / (40 + 10)            = 0.8000
  recall      = 40 / (40 + 60)            = 0.4000
  specificity = 890 / (890 + 10)          = 0.9889
  F1          = 2PR/(P+R)               = 0.5333
  F2 (recall-weighted)                  = 0.4444
  F0.5 (precision-weighted)             = 0.6667

  majority-class baseline accuracy      = 0.9000
  the model beats it by                 = +0.0300
  ... while missing 60 of 100 positives.

  F1 is the HARMONIC mean -- close to the smaller of P and R:
    precision   recall   arithmetic       F1
         0.90     0.90        0.900   0.9000
         1.00     0.50        0.750   0.6667
         1.00     0.10        0.550   0.1818
         1.00     0.01        0.505   0.0198

==========================================================================
2. ONE MODEL, MANY THRESHOLDS  (10,000 transactions, 1% fraud)
==========================================================================
  base rate = 0.0087  (87 positives of 10000)

    thresh  flagged    TP     FP    FN  precision   recall      F1  accuracy
      0.60        5     4      1    83     0.8000   0.0460  0.0870    0.9916
      0.40       23    11     12    76     0.4783   0.1264  0.2000    0.9912
      0.25       59    21     38    66     0.3559   0.2414  0.2877    0.9896
      0.15      103    27     76    60     0.2621   0.3103  0.2842    0.9864
      0.08      208    40    168    47     0.1923   0.4598  0.2712    0.9785
      0.04      429    51    378    36     0.1189   0.5862  0.1977    0.9586
      0.02      787    59    728    28     0.0750   0.6782  0.1350    0.9244
      0.01     1358    68   1290    19     0.0501   0.7816  0.0941    0.8691

  BASELINE (always negative): accuracy 0.9913, recall 0.0000, fraud caught 0
  Highest-accuracy threshold in the sweep beats the baseline while
  missing most of the fraud. Best-F1 threshold = 0.22.

==========================================================================
2b. FOUR ORGANISATIONS, FOUR THRESHOLDS, ONE MODEL
==========================================================================
  organisation                      method                thresh  flagged    prec  recall     FP
  A: 20-case/day review team        capacity              0.4172       21  0.4762  0.1149     11
  B: must catch 95% of fraud        requirement*          0.0006     5597  0.0152  0.9770   5512
  C: no cost data available         maximise F1           0.2200       71  0.3380  0.2759     47
  D: FP costs 5, FN costs 500       expected cost         0.0100     1358  0.0501  0.7816   1290

  Organisation B's 95% requirement costs 5512 false alarms for
  85 real catches -- 64.8 wasted investigations per catch.
  Same trained model in all four rows. The threshold is a PRODUCT
  decision, not a modelling one.

==========================================================================
3. ROC-AUC vs PR-AUC ON IMBALANCED DATA
==========================================================================
  dataset                   base rate   ROC-AUC   PR-AUC   PR random baseline
  balanced (50% pos)           0.4985    0.8630   0.8608               0.4985
  1% positive                  0.0092    0.9274   0.2605               0.0092

  Same signal, same model, two base rates. ROC-AUC barely moves; PR-AUC
  collapses. ROC-AUC does not tell you whether the model is USABLE.

  On the 1% problem, at the threshold where FPR = 2% (t = 0.0702):
    ROC-AUC   0.9039   -- looks excellent
    FPR       0.0201   -- looks excellent: only 199 false positives
                          out of 9,913 negatives
    precision 0.1777   -- UNUSABLE: the SAME 199 false positives,
                          now measured against 242 total flags
    -> 4.6 false alarms for every real catch, at only 49% recall

  Identical errors. FPR divides them by the huge negative count and they
  vanish; precision divides them by the small flagged count and they
  dominate. That is the whole reason to prefer PR-AUC when positives are
  rare -- and why PR-AUC must be reported next to the base rate.

==========================================================================
4. AUC IS BLIND TO CALIBRATION  (monotonic transforms)
==========================================================================
  transform                      ROC-AUC   PR-AUC      ECE   mean predicted   actual rate
  original                      0.903852 0.231935   0.0011           0.0087        0.0087
  squared  (q^2)                0.903852 0.231935   0.0073           0.0014        0.0087
  cubed    (q^3)                0.903852 0.231935   0.0082           0.0005        0.0087
  sqrt     (q^0.5)              0.903852 0.231935   0.0450           0.0537        0.0087
  x0.5 then +0.25               0.903852 0.231935   0.2457           0.2544        0.0087

  ROC-AUC and PR-AUC are IDENTICAL to six decimal places across all five
  rows: every transform is monotonic, so the RANKING never changed. ECE
  moves a lot. A model can rank perfectly and still tell you nothing
  truthful about probability -- which matters the moment you make an
  expected-cost decision or show a confidence number to a user.

==========================================================================
5. RELIABILITY DIAGRAM  (10 bins, original model)
==========================================================================
  bin                 n   mean predicted   observed rate      gap
  [0.0, 0.1)         9830           0.0048          0.0053  +0.0005
  [0.1, 0.2)           87           0.1326          0.1149  -0.0176
  [0.2, 0.3)           44           0.2474          0.2045  -0.0428
  [0.3, 0.4)           16           0.3443          0.3125  -0.0318
  [0.4, 0.5)           12           0.4434          0.4167  -0.0268
  [0.5, 0.6)            6           0.5555          0.3333  -0.2222
  [0.6, 0.7)            4           0.6302          0.7500  +0.1198
  [0.7, 0.8)            1           0.7030          1.0000  +0.2970
  [0.8, 0.9)            0               --              --       --
  [0.9, 1.0)            0               --              --       --

  ECE = 0.0011   (0 would be perfect; the diagonal is perfect calibration)

==========================================================================
6. MACRO vs MICRO AVERAGING  (5 classes, one dominant, one rare)
==========================================================================
  class     support  precision   recall       F1
  0            8000     0.9114   0.9900   0.9491
  1            1200     0.9231   0.8000   0.8571
  2             500     1.0000   0.4500   0.6207
  3             200     1.0000   0.2000   0.3333
  4             100     1.0000   0.0500   0.0952

  micro-F1 (= accuracy) : 0.9150
  weighted-F1           : 0.9008
  macro-F1              : 0.5711

  micro - macro = 0.3439. The dominant class (80% of the
  data) carries micro and weighted; macro gives the rare classes equal
  weight and exposes that class 4 is at F1 0.0952. Report macro when
  rare classes matter -- which includes every fairness question.

==========================================================================
7. REGRESSION METRICS, WITH AND WITHOUT ONE OUTLIER
==========================================================================
  dataset                                 MAE      RMSE   RMSE/MAE       R2     MAPE
  clean (500 rows)                     2.4025    3.0514     1.2701   0.9073   0.0510
  + one outlier (y=500)                3.2882   20.0926     6.1105   0.2005   0.0527
  + one near-zero target (y=0.01)      2.5119    3.9448     1.5704   0.8522  11.2341

  ONE row in 500 changes RMSE far more than MAE -- the RMSE/MAE ratio is
  a direct read-out of how skewed your errors are. And MAPE explodes on a
  near-zero target, because it divides by it. Choose the metric that
  matches what the errors actually cost you.

Done.
```

### 7.3 Reading the result

**Section 1** confirms every formula and the F1 table from §5.2. Note the bottom row: precision 1.00
with recall 0.01 gives an arithmetic mean of 0.505 and **F1 = 0.0198**. F1 is doing its job.

Note also the baseline line: the model's accuracy is 0.9300 against a majority baseline of 0.9000 — a
3-point gain — **while missing 60 of 100 positives**. Accuracy flatters it.

**Sections 2 and 2b** produce the §6 tables. The result worth dwelling on is that **the
highest-accuracy threshold in the entire sweep (0.60, accuracy 0.9916) catches 4 of 87 fraud cases**,
and still beats the do-nothing baseline of 0.9913.

**Section 3 is the ROC-versus-PR argument, and the lab makes it two ways.**

First, the same signal and the same model at two base rates:

| Dataset | Base rate | ROC-AUC | PR-AUC | PR random baseline |
|---|---|---|---|---|
| Balanced | 0.4985 | 0.8630 | 0.8608 | 0.4985 |
| 1% positive | 0.0092 | **0.9274** | **0.2605** | 0.0092 |

**ROC-AUC went *up* when the problem got harder** (0.863 → 0.927) while PR-AUC collapsed from 0.861 to
0.261. ROC-AUC is not measuring usability.

Second, and more concretely — the same errors, viewed two ways, at the threshold where the false
positive rate is a reassuring 2%:

| Metric | Value | Reads as |
|---|---|---|
| ROC-AUC | 0.9039 | excellent |
| FPR | **0.0201** | excellent — only 199 false positives out of 9,913 negatives |
| **Precision** | **0.1777** | **unusable — the same 199 false positives, against 242 total flags** |

**4.6 false alarms for every real catch, at 49% recall.** Nothing changed between rows 2 and 3 except
the denominator. FPR divides the false positives by the 9,913 negatives and they vanish; precision
divides them by the 242 flags and they dominate. **That is the entire argument for PR-AUC on
imbalanced problems**, and it is why PR-AUC is uninterpretable without the base rate printed next to
it.

**Section 4 demonstrates AUC's blindness to calibration exactly.** Across five monotonic transforms —
squaring, cubing, square-rooting, and a linear rescale — **ROC-AUC and PR-AUC are identical to all six
decimal places** (0.903852 and 0.231935 every time), because the ranking never changed. Meanwhile ECE
goes from **0.0011 to 0.2457**, and the last row's mean predicted probability is **0.2544 against an
actual rate of 0.0087** — a model claiming 25% risk where the truth is under 1%, with a *perfect* AUC.

**If you take one thing from this lesson, take this:** AUC tells you the model can *rank*. It tells you
nothing about whether the numbers it outputs mean anything. The moment you make an expected-cost
decision, set a threshold from a probability, or show a confidence figure to a user, you need
calibration, and AUC will not warn you.

**Section 5** shows the reliability diagram for the original model: ECE **0.0011**, with 9,830 of
10,000 predictions in the lowest bin and gaps under 0.05 wherever there is enough data. The high bins
hold 1, 4 and 6 rows — their large-looking gaps (+0.2970 on a single row) are pure sampling noise, and
this is the normal state of a reliability diagram on imbalanced data. **Only trust bins with enough
support**, exactly as in M3-L13 §7.3.

**Section 6** builds the macro/micro divergence deliberately: **micro-F1 0.9150, weighted-F1 0.9008,
macro-F1 0.5711** — a **0.344 gap**. The dominant class (80% of the data) is at F1 0.9491 while the
rarest class is at **0.0952**. Micro and weighted are both carried by the large class; only macro
exposes the failure. Report macro whenever rare classes matter — and every fairness question is a
question about rare classes.

**Section 7** shows one row in 500 changing the regression metrics:

| Dataset | MAE | RMSE | RMSE/MAE | R² | MAPE |
|---|---|---|---|---|---|
| Clean | 2.40 | 3.05 | 1.27 | 0.907 | 0.051 |
| + one outlier (y=500) | 3.29 | **20.09** | **6.11** | **0.201** | 0.053 |
| + one near-zero target (y=0.01) | 2.51 | 3.94 | 1.57 | 0.852 | **11.23** |

**One row in 500 took RMSE from 3.05 to 20.09 (6.6×) while MAE moved 1.37×, and took R² from 0.907 to
0.201.** The RMSE/MAE ratio is a direct read-out of error skew: 1.27 for clean errors, 6.11 with an
outlier. And MAPE went from 0.051 to **11.23** — an apparent 1,123% error — from a single target near
zero, because it divides by the target. Choose the metric that matches what the errors actually cost.

---

## 8. Common mistakes and troubleshooting

1. **Reporting accuracy on imbalanced data.** Report the majority baseline alongside, always.
2. **No baseline at all.** A score without a reference is not a result.
3. **Using ROC-AUC on a 1% problem** and concluding the model is good.
4. **Tuning the threshold on the test set.**
5. **Treating 0.5 as a law of nature.** It is a default, not a decision.
6. **Optimising F1 by reflex** without asking what the errors cost.
7. **Trusting probabilities from a class-weighted model** without recalibrating.
8. **Reporting micro-average** when rare classes are the point.
9. **Never slicing.** Aggregate metrics hide subgroup failures.
10. **Comparing to a paper's numbers** computed on a different split, threshold or metric definition.

| Symptom | Cause | Fix |
|---|---|---|
| Precision is `nan` | Nothing was flagged | Lower the threshold; check the model learned |
| Recall is `nan` | No positives in the test set | Stratify (M3-L13) |
| ROC-AUC 0.95 but useless in production | Imbalance | Use PR-AUC; report the base rate |
| Great F1, angry users | F1 was not the right trade-off | Use costs; ask what a miss costs |
| Probabilities all near 0 or 1 | Overconfident / miscalibrated | Reliability diagram; temperature scaling |
| Accuracy above the labeller agreement rate | Leakage, or label noise | Audit the split; re-check labels |
| Metric differs from a colleague's | Different definition or averaging | Agree the definition in writing |
| Score changes every run | No seed | Seed everything; report across seeds |

---

## 9. Security, privacy, reliability, cost

- **Governance.** Report metrics **sliced by subgroup** where required. An aggregate number can hide a
  severe failure for a minority group. Note carefully: measuring per-group performance is a
  prerequisite for fairness work, not a demonstration of fairness, and **no metric establishes legal
  compliance.** (M10-L09.)
- **Privacy.** Publishing per-group metrics on small groups can be disclosive. Suppress cells below a
  minimum count.
- **Reliability.** Monitor the same metrics in production, not just at training time. A model whose
  input distribution drifts degrades silently.
- **Cost.** Recall is expensive to measure — it needs labels for things you rejected. Budget for
  ongoing labelling, or you will only ever be able to measure precision.
- **Reliability.** Log the threshold with the model artefact. A model deployed with the wrong threshold
  is a common and entirely avoidable incident.

---

## 10. Exercises

### Exercise 1 — Beginner (~25 min)

Confusion matrix: TP=40, FP=10, FN=60, TN=890.

1. Compute accuracy, precision, recall, specificity and F1.
2. What is the majority-class baseline accuracy? Compare it to the model's.
3. Which error type dominates, and what would you change?
4. For each, name the metric to optimise: (a) tumour screening; (b) a spam filter; (c) RAG retrieval
   feeding a reranker; (d) auto-blocking payments.
5. Precision 1.0, recall 0.02. Compute F1 and explain why it is so much lower than the average.

### Exercise 2 — Intermediate (~40 min)

1. Implement `confusion_matrix`, `precision`, `recall`, `f1` and `fbeta` from scratch. Handle the
   zero-denominator cases explicitly.
2. Reproduce §6's threshold table from a trained model, then choose a threshold by each of the four
   methods in §5.4 and report what each gives.
3. Compute ROC-AUC and PR-AUC on a 1% problem. Explain why they tell different stories.
4. Square every predicted probability. Show ROC-AUC is unchanged and calibration is destroyed.
5. Build a reliability diagram with 10 bins and compute ECE.

### Exercise 3 — Challenge (~45 min)

1. Implement expected-cost threshold selection. Show the optimum moves as the cost ratio changes from
   1:1 to 1:50, and plot the relationship.
2. Implement macro, micro and weighted averaging for a 5-class problem where one class is 80% of the
   data and one is 1%. Construct a case where micro > 0.90 and macro < 0.50.
3. Implement temperature scaling on a validation set and show ECE falling while accuracy is unchanged.
4. Add 5% label noise and measure the ceiling it puts on achievable accuracy.
5. Slice a test set by a synthetic group attribute and find a case where aggregate accuracy is 0.92
   while one group's is below 0.60.
6. Run the same training with 10 seeds. Report mean ± sd and state the smallest difference you could
   defend as real.

---

## 11. Quiz

**Q1.** TP=40, FP=10, FN=60, TN=890. Precision?

- A. 0.40  B. 0.80  C. 0.93  D. 0.04

**Q2.** Same matrix. Recall?

- A. 0.80  B. 0.40  C. 0.93  D. 0.10

**Q3.** Which is `TP / (TP + FN)`?

- A. Precision  B. Recall  C. Specificity  D. Accuracy

**Q4.** Why does ROC-AUC mislead on a 1% positive problem?

- A. It is computed incorrectly.
- B. FPR divides false positives by the large negative count, so a huge number of false alarms barely
  moves the curve — while precision, dividing by the small flagged count, collapses.
- C. It needs balanced classes to compute.
- D. It ignores true positives.

**Q5.** Precision 1.0, recall 0.02. F1?

- A. 0.51  B. 0.04  C. 0.98  D. 1.0

**Q6.** Your model is 94% accurate. What must you report alongside?

- A. Training time.
- B. A baseline — at minimum the majority-class accuracy — because without it the number cannot be
  interpreted.
- C. The learning rate.
- D. The parameter count.

**Q7.** You square every predicted probability. What happens?

- A. Both AUC and calibration worsen.
- B. ROC-AUC is unchanged (it depends only on ranking, and squaring is monotonic) while
  calibration is destroyed.**
- C. AUC improves.
- D. Nothing changes.

**Q8.** Where should a decision threshold be chosen?

- A. On the test set.  B. On validation data.  C. On training data.  D. Always 0.5.

**Q9.** Micro-average F1 is 0.93 and macro is 0.41. What does that tell you?

- A. A calculation error.
- B. The dominant class is handled well and one or more rare classes are handled badly — micro is
  dominated by the large class, macro weights every class equally.
- C. The model is well calibrated.
- D. Macro is always lower and it means nothing.

**Q10.** Your model achieves 99.2% accuracy on 1%-positive data and catches 3 of 15 fraud cases.
The always-negative baseline gets 99.0%. What should you conclude?

- A. The model is excellent — it beat the baseline.
- B. The 0.2-point gain is nearly meaningless and the model misses 80% of the fraud; accuracy is
  measuring the majority class, not the task, and you should report precision and recall against a
  chosen threshold instead.
- C. Lower the learning rate.
- D. The test set is too large.

**Q11.** *(Written, rubric-graded.)* In under 120 words, explain to a product manager why you cannot
give them "the model's accuracy" as a single number for a fraud detector, and what you will give them
instead.

---

## 12. Revision notes

- **Two ways to be wrong. Precision measures false alarms; recall measures misses.** They trade off.
- `precision = TP/(TP+FP)` · `recall = TP/(TP+FN)` · `specificity = TN/(TN+FP)`.
- **F1 is the harmonic mean** — close to the smaller value. P=1.0, R=0.01 → **F1 = 0.02**, not 0.505.
- **Fβ**: β=2 favours recall, β=0.5 favours precision. F1 ignores true negatives.
- **ROC-AUC for balanced; PR-AUC for imbalanced.** FPR hides false positives behind a huge negative
  count. A PR curve's random baseline is the **base rate** — always report it.
- **The threshold is a product decision**, chosen on validation from capacity, a requirement, Fβ, or
  expected cost. 0.5 is a default, not a law.
- **AUC is invariant to monotonic transformations.** Measured: ROC-AUC identical to **six decimal
  places** across squaring, cubing and rescaling, while ECE went 0.0011 → 0.2457. A perfect ranker can
  be badly calibrated, and AUC will not warn you.
- Measured: at **FPR 0.0201** — which reads as excellent — the same errors give **precision 0.1777**
  and 4.6 false alarms per catch. Same errors, different denominator.
- Measured: **the highest-accuracy threshold caught 4 of 87 fraud cases** and still beat the
  do-nothing baseline.
- **Never report a metric without a baseline.** Majority class at minimum.
- Regression: **MAE** (robust, target units) · **RMSE** (punishes large errors) · **R²** (can be
  negative; meaningless on tiny samples).
- **Macro when every class matters; micro when overall correctness matters.** Measured: micro-F1
  0.9150 against macro-F1 0.5711 — the rarest class was at F1 0.0952 and only macro showed it.
- Measured: **one outlier row in 500** took RMSE 3.05 → 20.09 and R² 0.907 → 0.201, while MAE moved
  2.40 → 3.29. **RMSE/MAE is a direct read-out of error skew.**
- **Always slice.** Aggregates hide subgroup failure. Seed everything; a metric you cannot reproduce
  is an anecdote.

---

## 13. Completion checklist

- [ ] I can compute every metric from a confusion matrix without looking them up.
- [ ] I can explain precision vs recall to a non-technical stakeholder.
- [ ] I can say why ROC-AUC misleads on imbalanced data.
- [ ] I reproduced §6's threshold table and chose a threshold by all four methods.
- [ ] I showed AUC unchanged to six decimal places while ECE went 0.0011 → 0.2457.
- [ ] I saw the highest-accuracy threshold catch 4 of 87 fraud cases.
- [ ] I built a reliability diagram and computed ECE.
- [ ] I never report a metric without a baseline.
- [ ] I scored 8/11 on the quiz.

---

## 14. References

- scikit-learn, *Metrics and scoring*.
  <https://scikit-learn.org/stable/modules/model_evaluation.html> `[UNVERIFIED]`
- Saito & Rehmsmeier (2015), *The Precision-Recall Plot Is More Informative than the ROC Plot*.
  <https://doi.org/10.1371/journal.pone.0118432> `[UNVERIFIED]`
- Guo et al. (2017), *On Calibration of Modern Neural Networks*.
  <https://arxiv.org/abs/1706.04599> `[UNVERIFIED]`

---

## 15. Next lesson

→ [Project 3 — Train and Evaluate a Classifier](../../projects/project-03-classifier/README.md)

Module 3's concepts are complete. Next: building one model end to end — split, train, tune, evaluate
and write up — with every decision in this module applied deliberately.
