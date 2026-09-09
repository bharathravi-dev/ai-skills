# M1-L08 — Generalization, Overfitting and Underfitting

| | |
|---|---|
| **Lesson ID** | M1-L08 |
| **Difficulty** | 2 (Core) |
| **Estimated study time** | 1.25 hours |
| **Prerequisites** | [M1-L06](M1-L06-training-validation-testing-inference.md) |

---

## 1. Learning objectives

1. **Define** generalization, overfitting and underfitting, and **state** the diagnostic signature of
   each in terms of training and validation error.
2. **Diagnose** which problem a model has from two numbers, and **choose** an appropriate remedy.
3. **Explain** the capacity/complexity trade-off and locate the sweet spot on a curve.
4. **Recognise** overfitting in LLM applications, where you never train a model.
5. **Apply** at least four concrete remedies and state the cost of each.

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **Generalization** | Performing well on data not seen during training. The actual goal of all machine learning. |
| **Generalization gap** | Training performance minus validation performance. A large gap indicates overfitting. |
| **Overfitting** | Learning patterns specific to the training data — including its noise — that do not hold generally. |
| **Underfitting** | Failing to learn patterns that *are* present, usually because the model is too simple or trained too little. |
| **Capacity** | How complex a relationship a model can represent. More parameters generally means more capacity. |
| **Bias** (error sense) | Error from a model being too simple to capture the real pattern. A third meaning of "bias" — see §5.6. |
| **Variance** (error sense) | Error from a model being overly sensitive to the particular training sample. |
| **Regularization** | Any technique that constrains a model to reduce overfitting. |
| **Early stopping** | Halting training when validation error stops improving. |
| **Dropout** | Randomly disabling units during training so the model cannot rely on any single one. |
| **Data augmentation** | Creating extra training examples by transforming existing ones. |
| **Memorization** | The extreme of overfitting: storing training examples rather than learning a rule. |
| **Noise** | Variation in data that carries no generalisable signal. |

---

## 3. Plain-language explanation

The point of training a model is **not** to do well on the training data. You already know the
answers for the training data. The point is to do well on data you have never seen.

Three things can happen:

1. **Underfitting** — the model is too simple, or you stopped too early. It does badly on the
   training data *and* on new data. It has not learned the pattern that is there.
2. **Good fit** — it does well on both, with a small gap between them.
3. **Overfitting** — it does brilliantly on training data and badly on new data. It memorised the
   specific examples, including their noise, instead of learning the underlying rule.

The diagnostic is two numbers, and it is remarkably reliable:

| Training error | Validation error | Diagnosis | What to do |
|---|---|---|---|
| High | High (similar) | **Underfitting** | More capacity, better features, train longer |
| Low | Low (similar) | **Good fit** | Ship it |
| **Low** | **High** | **Overfitting** | More data, less capacity, regularisation, early stopping |
| High | Low | Something is wrong | Bug, leakage in reverse, or mismatched splits |

That last row is not a real state. If validation beats training substantially, you have a bug —
commonly a training set that includes harder examples, dropout still active at evaluation, or
mismatched preprocessing. Investigate rather than celebrate.

### Connecting to what you already know

You have seen overfitting in software, though not by that name:

| Software situation | Equivalent |
|---|---|
| Code that passes tests because it special-cases each test input | Overfitting — memorising, not solving |
| A regex tuned to your 20 sample URLs that breaks on the 21st | Overfitting |
| A cache keyed too specifically, so it never hits | Overfitting |
| A validator so loose it accepts everything | Underfitting |
| Hard-coding `if input == "test1": return 42` | Pure memorization |

The special-cased-tests analogy is exact. A model that overfits is doing the machine-learning
equivalent of `if input == known_example: return known_answer`, just smoothly and unintentionally.

---

## 4. Analogy

**Studying for an exam.**

- **Underfitting** = you skimmed the chapter titles. You fail the practice papers and the real exam.
- **Good fit** = you understood the principles. You do well on both.
- **Overfitting** = you memorised the answers to last year's paper word-for-word. You score 100% on
  last year's paper and fail this year's, because the questions changed but the principles did not.

### Where the analogy breaks

1. **The student knows they are memorising.** A model has no such awareness — it cannot tell you it
   is memorising. Only held-out data reveals it, which is why M1-L06 is a prerequisite.
2. **Exam questions are deliberately varied; real data drifts on its own.** A model can generalise
   well today and poorly next quarter with no change to the model.
3. **Memorisation is sometimes correct.** If a fact genuinely never changes, memorising it is fine.
   Overfitting is memorising things that *do* change or that are pure noise. The distinction is
   whether the memorised pattern holds outside the sample — which you cannot know without testing.
4. **A student has one brain of fixed capacity.** You can *choose* your model's capacity, and that
   choice is the main lever you have.

---

## 5. Detailed technical explanation

### 5.1 What overfitting actually is

All real data contains **signal** (patterns that hold generally) and **noise** (variation specific to
this sample). A model with enough capacity cannot tell them apart. It will fit both, because fitting
the noise reduces training error further.

Concretely: suppose ticket resolution time genuinely depends on ticket complexity, plus random
variation from which agent happened to pick it up. A high-capacity model will learn "tickets
submitted at 14:37 on Tuesdays take 3.2 hours" — a pattern that exists in your 800 training rows by
coincidence and will not hold next month.

**More capacity always reduces training error and eventually increases validation error.** That
turning point is the sweet spot, and finding it is what the validation set is for.

### 5.2 The capacity curve

```
error
  ^
  |  \                                              /
  |   \                                          /
  |    \        validation error              /
  |     \                                  /
  |      \                             /
  |       \_____                  ___/
  |             \____________ ___/
  |                          X   <-- sweet spot (lowest validation error)
  |                     ____/
  |                ___/
  |           ___/    training error (keeps falling)
  |      ____/
  |  ___/
  +-------------------------------------------------> model capacity
     UNDERFITTING        GOOD          OVERFITTING
   (both errors high)              (train low, val high)
```

Read this carefully:

- **Training error falls monotonically** with capacity. It essentially always does. This is why
  training error alone tells you nothing useful.
- **Validation error is U-shaped.** It falls while the model learns real signal, then rises as the
  model starts fitting noise.
- **The sweet spot is the minimum of the validation curve**, not the minimum of the training curve.

The same curve applies to *training duration*: train too few epochs and you underfit; too many and
you overfit. **Early stopping** simply means halting at the minimum of the validation curve.

### 5.3 Remedies, and their costs

| Remedy | How it works | Cost / risk |
|---|---|---|
| **More training data** | Noise averages out; harder to memorise a large set | Often the most effective and the most expensive |
| **Reduce capacity** | Fewer parameters/layers/depth; the model cannot represent noise | Too far and you underfit |
| **Regularization (L1/L2)** | Penalises large weights, pushing toward simpler functions | Adds a hyperparameter to tune |
| **Early stopping** | Stop at the validation minimum | Nearly free; needs a validation set |
| **Dropout** | Randomly disable units so no single one is relied on | Neural networks only; slows convergence |
| **Data augmentation** | Generate variants (rotate images, paraphrase text) | Must preserve the label; a rotated "6" is not a "9"-safe transform |
| **Feature reduction** | Remove features that carry mostly noise | May remove real signal |
| **Cross-validation** | Better estimate so you tune more reliably | k× compute |
| **Simpler model class** | Linear instead of deep | May underfit |

**If you can get more real data, do that first.** Every other remedy is a way of coping with not
having enough.

### 5.4 Diagnosing underfitting

Underfitting is under-diagnosed because the numbers look uniformly mediocre rather than dramatic.
Signatures:

- Training error is high and barely improves with more epochs.
- Training and validation errors are close together and both poor.
- The model predicts near the average for everything.

Causes and fixes:

| Cause | Fix |
|---|---|
| Model too simple | More capacity |
| Trained too briefly | More epochs |
| Learning rate too high (never converges) or too low (crawls) | Tune it — M3-L12 |
| Features do not contain the signal | Better features. **No model can predict from information that is not there.** |
| Over-regularised | Reduce the penalty |

The fourth row is the most important and the most often missed. If your features genuinely do not
contain the answer, no amount of model sophistication helps. Establish a **baseline** first (M3-L14):
if a trivial model does as well as your fancy one, the features may be the problem, not the model.

### 5.5 Overfitting in LLM applications — you *will* meet this

You do not train the model, so it is easy to assume this lesson does not apply. It applies, in three
distinct ways, and all three are common.

**1. Prompt overfitting.** You iterate on your prompt against 30 examples until it handles all 30.
You have fitted the prompt to those 30 cases. New inputs fail. Signature: excellent on your dev
examples, mediocre in production. This is exactly the optimistic bias you measured in M1-L05.
*Remedy:* a larger and more diverse eval set, and a held-out test set touched once.

**2. Few-shot example overfitting.** Your examples are all from one customer or one format, so the
model imitates that format rather than learning the task. *Remedy:* diversify examples deliberately;
check performance on formats absent from your examples.

**3. Retrieval overfitting.** You tune chunk size, `k` and thresholds against your 40 test questions
until retrieval is perfect for them. Real user questions are phrased differently and retrieval
collapses. *Remedy:* build eval questions from *real* user language, not from the documents you
indexed (M7-L19).

A fourth, subtler case belongs to the model rather than you: **benchmark contamination**. If the
model memorised a public benchmark during pretraining, its score on it is memorisation, not
capability. This is why your own private eval set is worth more than any leaderboard (M5-L18).

### 5.6 Bias and variance — and the third meaning of "bias"

The classical decomposition:

- **Bias (error sense)** = error from wrong assumptions; the model is too simple. → underfitting.
- **Variance (error sense)** = error from sensitivity to the particular sample. → overfitting.

Traditionally you trade one against the other. Note that this is now the **third** distinct meaning
of "bias" in this course:

| Meaning | Context | Lesson |
|---|---|---|
| The learned constant `b` in `wx + b` | Model internals | M1-L05 |
| Error from an over-simple model | Bias–variance | This lesson |
| Unfair treatment of groups | Fairness | M10-L08 |

Always say which you mean. Confusing the second and third in a stakeholder conversation is a real
and avoidable embarrassment.

### 5.7 Assumptions and limitations

- The tidy U-curve assumes classical models. Very large neural networks can show **double descent**,
  where validation error falls, rises, then falls *again* as capacity grows past the interpolation
  point. This is why "just make it smaller" is not universal advice for large models. `[UNVERIFIED]`
  — an active research area; the classical picture is what you should reason with day to day.
- Diagnosis assumes your validation set is representative. If it is not, all four rows of the
  diagnostic table are unreliable.
- A small generalization gap does not mean the model is good — both numbers can be uniformly bad.
  **Always compare against a baseline** (M3-L14).

---

## 6. Worked example

Predicting ticket resolution hours from ticket length. 12 training points that follow a genuine
gentle upward trend plus noise.

**Model A — a horizontal line (capacity 1: predict the mean).**

| | Training error | Validation error |
|---|---|---|
| Model A | 4.2 | 4.4 |

Both high, gap tiny (0.2). → **Underfitting.** It ignores length entirely.

**Model B — a straight line (capacity 2: slope + intercept).**

| | Training error | Validation error |
|---|---|---|
| Model B | 2.1 | 2.3 |

Both improved, gap still small. → **Good fit.**

**Model C — an 11th-degree polynomial (capacity 12: enough to pass through every point).**

| | Training error | Validation error |
|---|---|---|
| Model C | **0.0** | **9.8** |

Training error is *perfect*. Validation error is worse than the horizontal line. → **Severe
overfitting.** The curve passes exactly through all 12 training points and oscillates wildly
between them.

**The lesson in one line:** Model C has the best training error and is the worst model. **A training
score is not evidence of anything.**

Note the shape of the gaps: 0.2, 0.2, then **9.8**. The generalization gap is the diagnostic, not
the training number.

---

## 7. Practical activity

**File:** [`labs/m1/l08_overfitting.py`](../../labs/m1/l08_overfitting.py)

```bash
python3 labs/m1/l08_overfitting.py
```

Fits polynomials of increasing degree to noisy synthetic data and prints training and validation
error for each, plus an ASCII plot of both curves. It reproduces the U-shape from §5.2 with real
numbers, using only the standard library (least squares solved by hand with Gaussian elimination —
no NumPy, so nothing is hidden).

### 7.1 Important lines

| Construct | Why |
|---|---|
| `[[x ** p for p in range(degree + 1)] for x in xs]` | Builds the design matrix: each column is `x` to a power. Degree 1 gives a line; degree 11 gives a curve that can pass through 12 points. |
| `solve(ata, atb)` | Solves the normal equations by Gaussian elimination — the closed-form least-squares fit. The maths is M3-L08. |
| `ridge` parameter | Adds a small penalty to the diagonal — **L2 regularization**, and also what keeps the high-degree fit numerically solvable. |
| `mean((pred - actual) ** 2)` | Mean squared error. M3-L07. |

### 7.2 Expected output

`[EXECUTED]` 2026-09-07, Python 3.12.3. Deterministic:

```
======================================================================
OVERFITTING: training error vs validation error as capacity grows
======================================================================
True pattern: y = 2.0 + 1.5x - 0.15x^2   (a degree-2 curve)
Training points: 12   Validation points: 40
Noise std dev: 1.2   Ridge: 1e-08

A degree-d polynomial has d+1 parameters. With 12 training points,
degree 11 has exactly enough capacity to pass through every one.

 degree  params   train err    val err       gap  verdict
----------------------------------------------------------------------
      0       1       2.356      3.352     0.996  underfit (predicts the mean)
      1       2       1.341      2.142     0.801  good
      2       3       0.582      2.282     1.699  good
      3       4       0.286      2.561     2.275  OVERFIT
      4       5       0.189      2.071     1.882  OVERFIT
      5       6       0.181      2.063     1.882  OVERFIT
      6       7       0.131      2.313     2.182  OVERFIT
      7       8       0.128      2.140     2.012  OVERFIT
      8       9       0.100     46.343    46.243  OVERFIT
      9      10       0.063   1448.503  1448.440  OVERFIT
     10      11       0.075     36.774    36.699  OVERFIT
     11      12       0.054  15714.965 15714.911  OVERFIT
----------------------------------------------------------------------
Lowest validation error at degree 5 (val=2.063, train=0.181, gap=1.882)
Lowest TRAINING error at degree 11 (train=0.054, val=15714.965)


  error (log scale)
    15714.96 |                       V
     7496.67 |                        
     3576.21 |                        
     1706.00 |                        
      813.83 |                   V    
      388.23 |                        
      185.20 |                        
       88.35 |                        
       42.15 |                 V      
       20.11 |                     V  
        9.59 |                        
        4.58 |                        
        2.18 | B   V V     V          
        1.04 |   B     V V   V        
        0.50 |     T                  
        0.24 |       T                
        0.11 |         T T T T        
        0.05 |                 T T T T
             +------------------------
               0 1 2 3 4 5 6 7 8 91011
              model capacity (polynomial degree)
              T = training error   V = validation error   B = both

----------------------------------------------------------------------
WHAT TO SEE HERE
----------------------------------------------------------------------
1. Training error (T) falls essentially monotonically. It NEVER
   tells you to stop. This is why training error is not evidence.

2. Validation error (V) is U-shaped: it drops while the model
   learns real signal, then climbs as it starts fitting noise.

3. The best model is at the BOTTOM OF THE V CURVE, not the T curve.
   Choosing by training error picks the worst model available.

4. Look at degrees 1-7: validation error barely moves (about 2.0-2.6)
   while training error falls 10x. That flat region is the model
   buying nothing real. Then from degree 8 it does not just stop
   helping, it detonates - 2.1 -> 46 -> 1448 -> 15715.

5. HONEST NOTE: the true function is degree 2, but the validation
   minimum lands at degree 5. With only 12 noisy training points,
   the validation curve is too flat in that region to identify the
   true complexity. Do not expect model selection to recover the
   'real' answer - it recovers what your data can support. With
   N_TRAIN=60 (Exercise 2) the catastrophe disappears entirely:
   worst-case validation error falls from 15715 to about 1.7.
======================================================================
```

### 7.3 Reading the result

**The single most important pair of rows:**

| | degree 5 | degree 11 |
|---|---|---|
| training error | 0.181 | **0.054** (best) |
| validation error | **2.063** (best) | 15714.965 |

The model with the **best training error is the worst model by a factor of about 7,600**. If you
selected on training error — which is exactly what "our model fits the data well" means — you would
choose the catastrophic one. This is why §5.2 insists that training error never tells you to stop.

**The explosion is worth dwelling on.** Validation error does not degrade gracefully as capacity
grows past the useful point:

```
degree:  7      8       9        10      11
val:     2.14   46.3    1448.5   36.8    15715.0
```

Once the polynomial has enough freedom to thread exactly through all 12 training points, it does so —
and between those points it swings violently. Overfitting is not always a gentle decline. It can be a
cliff, and you only see the cliff if you are measuring on held-out data.

**Look at the flat region, degrees 1–7.** Validation error hovers around 2.0–2.6 while training error
falls tenfold, from 1.34 to 0.13. Every bit of that tenfold improvement is the model absorbing noise.
It bought nothing. This flat region is what "more capacity is not helping" looks like in practice, and
it is far more common than the dramatic explosion.

**An honest caveat about model selection.** The true function is degree 2, but the validation minimum
lands at degree 5. With only 12 noisy training points the validation curve is too flat between
degrees 1 and 7 to distinguish them. Do not expect model selection to recover the "real" complexity —
it recovers what your data can support. Reporting degree 5 as "the discovered complexity of the
system" would be overclaiming.

**What Exercise 2 will show you** (both verified in this environment):

| Change | Best degree | Worst-case validation error |
|---|---|---|
| Baseline (12 points, ridge 1e-8) | 5 | **15,715** |
| `N_TRAIN = 60` | 4 | **1.71** |
| `RIDGE = 1.0` (12 points) | 5 | **1,925** |

More data does not merely reduce overfitting — it **eliminates the catastrophe**. With 60 points, even
a degree-11 polynomial cannot thread through them all, so the worst case falls from 15,715 to 1.71.
Regularization helps substantially too (15,715 → 1,925) but is nowhere near as effective as having
enough data. That ordering — data first, regularization second — is exactly the guidance in §5.3, and
you can now see the magnitude of the difference rather than taking it on trust.

**Verification:** confirm `Lowest validation error at degree 5` and `train=0.054, val=15714.965` at
degree 11.

---

## 8. Common mistakes and troubleshooting

1. **Reporting training accuracy.** It is not evidence. Always report held-out performance.
2. **Concluding "overfitting" from a low score alone.** Low training *and* low validation is
   underfitting; the remedies are opposite. Adding regularization to an underfit model makes it
   worse.
3. **Fixing overfitting only by shrinking the model** when more data was available.
4. **Not noticing prompt overfitting**, because there is no training loop to watch.
5. **Augmenting data in a way that breaks the label.** Flipping an image of the digit 2 does not
   produce a valid 2.
6. **Celebrating validation > training.** That is a bug signature.
7. **Assuming a small gap means a good model.** Compare to a baseline.

| Symptom | Diagnosis | Fix |
|---|---|---|
| Train 99%, val 71% | Overfitting | More data, regularise, early stop, reduce capacity |
| Train 68%, val 67% | Underfitting | More capacity, longer training, better features |
| Train 68%, val 82% | Bug | Check dropout at eval, preprocessing consistency, split composition |
| Val error rises after epoch 12 | Overfitting begins there | Early stopping at epoch 12 |
| Great on dev prompts, poor in production | Prompt overfitting | Bigger, more diverse eval set; held-out test |

---

## 9. Security, privacy, reliability and cost

- **Privacy.** Extreme overfitting *is* memorization, and memorised training data can be extracted
  from a model. If you fine-tune on personal data, you may have built a system that can be induced
  to reveal it. This is a documented attack class (M10-L06, M13-L02).
- **Reliability.** An overfit model degrades sharply on any input distribution change — it has no
  margin. Monitor the gap between offline and online performance (M13-L12).
- **Cost.** More data is the best remedy and the most expensive. Regularization and early stopping
  are nearly free. Try the free ones first, but do not mistake them for a substitute when the real
  problem is 200 training examples.
- **Governance.** "Model achieves 94%" must always specify *on what data*. A claim without a split
  description is not auditable (M10-L13).

---

## 10. Exercises

### Exercise 1 — Beginner (~10 min)

Diagnose each and name one remedy:

1. Train 98%, validation 62%.
2. Train 64%, validation 63%.
3. Train 88%, validation 86%.
4. Train 55%, validation 79%.
5. Validation error falls until epoch 20, then rises steadily to epoch 100.

### Exercise 2 — Intermediate (~20 min)

Run the lab, then:

1. At which degree is validation error lowest? What is the generalization gap there?
2. What is the training error at the highest degree, and the validation error? Explain the
   relationship in your own words.
3. Increase `N_TRAIN` from 12 to 60 and re-run. Report how the best degree and the worst-case
   validation error change, and explain why more data changes the picture.
4. Set `RIDGE` to 1.0 and re-run with `N_TRAIN = 12`. Report what happens at high degree and explain
   the mechanism.

### Exercise 3 — Challenge (~25 min)

Your RAG assistant answers 38 of 40 evaluation questions correctly. In production, users report it is
"often wrong".

1. List five distinct hypotheses for the discrepancy, at least two involving overfitting as described
   in §5.5.
2. For each, state the specific diagnostic you would run and what result would confirm it.
3. Design a better evaluation set: where would the questions come from, how many, and what would you
   deliberately include that your current 40 probably lack?
4. You cannot get more evaluation questions this month. What would you do instead, and what would you
   tell stakeholders about your confidence level?

---

## 11. Quiz

**Q1.** A model scores 97% on training data and 68% on validation data. This is:

- A. Underfitting  B. Overfitting  C. A good fit  D. Data leakage

**Q2.** What is the defining signature of underfitting?

- A. Training error much lower than validation error.
- B. Training and validation error both high and close together.
- C. Validation error lower than training error.
- D. Perfect training error.

**Q3.** Why does training error alone tell you nothing useful about model quality?

- A. It is usually computed incorrectly.
- B. It falls monotonically as capacity increases, so a model can achieve zero training error purely
  by memorising, including the noise.
- C. It is always equal to validation error.
- D. It cannot be measured for neural networks.

**Q4.** Which single remedy is generally most effective against overfitting, and also most expensive?

- A. Dropout  B. Early stopping  C. More real training data  D. Reducing the learning rate

**Q5.** You add L2 regularization to a model with training 64% / validation 63%. What will most
likely happen?

- A. Validation improves substantially.
- B. Both get worse, because the model is underfitting and regularization further constrains an
  already-too-simple model.
- C. Training improves, validation unchanged.
- D. Nothing changes.

**Q6.** In an LLM application where you train nothing, "prompt overfitting" means:

- A. The prompt is too long for the context window.
- B. You iterated the prompt against a small set of examples until it handled them, fitting the
  prompt to those specific cases rather than the general task.
- C. The model memorised your prompt.
- D. Temperature is set too high.

**Q7.** Validation accuracy is consistently *higher* than training accuracy by 14 points. The best
first action is:

- A. Ship it — the model generalises unusually well.
- B. Investigate for a bug: check whether regularisation such as dropout is still active during
  training-set evaluation, whether preprocessing differs between splits, or whether the splits
  contain systematically different difficulty.
- C. Increase model capacity.
- D. Add more training data.

**Q8.** In the §6 example, Model C achieved 0.0 training error. What does this tell you?

- A. It is the best model.
- B. It has enough capacity to pass exactly through every training point, which is evidence of
  memorisation rather than of learning — confirmed by its validation error of 9.8.
- C. The data has no noise.
- D. Training was successful.

**Q9.** Which pair correctly matches the classical bias–variance terms?

- A. High bias → overfitting; high variance → underfitting.
- B. High bias → underfitting; high variance → overfitting.
- C. Both refer to unfair treatment of groups.
- D. Both increase with more training data.

**Q10.** *(Written, rubric-graded.)* Your colleague reports "99% accuracy" on a fraud model. In under
80 words, list the three questions you would ask before believing it, and say why each matters.

---

## 12. Revision notes

- The goal is **generalization**, never training performance.
- Diagnostic from two numbers: **both high** = underfitting · **train low, val high** = overfitting ·
  **both low** = good · **val ≫ train** = bug.
- Training error falls monotonically with capacity; validation error is **U-shaped**. The sweet spot
  is the validation minimum, which is also what early stopping finds.
- Overfitting = fitting noise. Underfitting = missing signal. Opposite remedies — diagnose before
  treating.
- Remedies: more data (best, dearest) · reduce capacity · L1/L2 · early stopping · dropout ·
  augmentation · feature reduction.
- **In LLM apps:** prompt overfitting, few-shot overfitting, retrieval overfitting, plus benchmark
  contamination in the model itself.
- "Bias" now has three meanings: the intercept · error from oversimplicity · unfairness. Disambiguate.
- No model can predict from information the features do not contain. Baseline first.

---

## 13. Completion checklist

- [ ] I can state the diagnostic signature of each condition.
- [ ] I can draw the capacity curve and mark the sweet spot.
- [ ] I ran the lab and identified the best degree from its output.
- [ ] I completed Exercise 2 including the more-data and ridge variations.
- [ ] I can name three ways overfitting appears in LLM applications.
- [ ] I can distinguish the three meanings of "bias".
- [ ] I scored 7/10 on the quiz.

---

## 14. References

- Hastie, Tibshirani & Friedman, *ESL*, Ch. 7 — model assessment and the bias–variance
  decomposition. `[UNVERIFIED]`
- Belkin et al., "Reconciling modern machine-learning practice and the classical bias–variance
  trade-off" (PNAS 2019) — double descent, referenced in §5.7. `[UNVERIFIED]`
- Carlini et al., "Extracting Training Data from Large Language Models" (2021) — the memorisation
  privacy risk in §9. `[UNVERIFIED]`

---

## 15. Next lesson

→ [M1-L09 — Data Leakage and Evaluation Contamination](M1-L09-data-leakage.md)

Overfitting is visible in the gap between training and validation. Leakage is worse: it makes both
numbers look excellent while the system is broken. Next you will build a model with 100% accuracy
that is completely useless.
