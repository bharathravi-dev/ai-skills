# Module 3 — Revision Guide

Read this before the assessment. It condenses fourteen lessons into what recurs for the rest of the
course — and much of it recurs sooner than you expect, because Modules 6, 7 and 8 are full of vectors,
similarity, thresholds and precision/recall arguments even where no model is being trained.

If a line here reads as unfamiliar rather than merely terse, return to the lesson.

---

## 1. One line per lesson

| Lesson | The thing to retain |
|---|---|
| L01 | A vector is a list of numbers with an **agreed meaning per position**. Shapes must line up. |
| L02 | **Cosine similarity compares direction, not magnitude.** `(a·b)/(‖a‖‖b‖)`. Range −1…1. |
| L03 | Mean hides the tail. **Report percentiles.** `SE = σ/√n` — averages of few things wobble. |
| L04 | `P(A\|B) ≠ P(B\|A)`. **Base rates dominate** — a 99% test on a 1-in-10,000 disease is mostly wrong. |
| L05 | Logs turn multiplication into addition. **Cross-entropy = −log(p assigned to the truth)**. |
| L06 | A derivative is a local slope. **Chain rule: rates multiply.** Central difference, `h ≈ 1e-5`. |
| L07 | Loss measures wrongness; gradient descent walks downhill. **α is the whole game.** |
| L08 | Linear regression = fitting a plane. **R² on a tiny sample means nothing** (measured: 1.0000 on 5 points). |
| L09 | Logistic regression = linear score → sigmoid → probability. **Softmax temperature is the same knob as LLM temperature.** |
| L10 | Without a non-linearity, **any depth collapses to one matrix** (measured: 1,579 params → 21). |
| L11 | Backprop = the chain rule in reverse. One pass, every gradient. **Training ≈ a small constant × inference.** |
| L12 | Learning rate first, optimizer second. **Adam gives each parameter its own effective rate.** |
| L13 | **Split by the thing that repeats.** Split first, resample second. A test score is an estimate. |
| L14 | **Two ways to be wrong.** Never report a metric without a baseline. The threshold is a product decision. |

---

## 2. The formulas worth memorising

| | |
|---|---|
| Cosine similarity | `(a·b) / (‖a‖ ‖b‖)` |
| Standard error of a mean | `σ / √n` |
| Standard error of a proportion | `√(p(1−p)/n)` |
| Bayes | `P(A\|B) = P(B\|A)·P(A) / P(B)` |
| Cross-entropy (one example) | `−log(p_true_class)` |
| Perplexity | `exp(cross-entropy)` |
| Sigmoid | `1 / (1 + e^−z)` |
| Gradient descent step | `θ ← θ − α·∇L` |
| Softmax with temperature | `exp(z_i/T) / Σ exp(z_j/T)` |
| Precision / recall | `TP/(TP+FP)` · `TP/(TP+FN)` |
| F1 | `2PR/(P+R)` — the **harmonic** mean |
| Matrix backward pass | `dW = Xᵀδ` · `db = δ.sum(0)` · `dX = δWᵀ` |

---

## 3. Numbers this module actually measured

These are not rules of thumb. Every one was produced by a lab in this module.

| Measurement | Value | Lesson |
|---|---|---|
| A 5-layer linear network collapsed to one matrix | 1,579 params → **21 numbers**, max diff 9.33e-15 | L10 |
| Sigmoid gradient product over 50 layers | **7.89e-31** (ReLU stays 1.0) | L10 |
| Per-layer gradient spread over 12 layers | sigmoid **31,035,255×**, ReLU **0.4×** | L11 |
| Cost of forward+backward vs forward alone | **1.46×** for 1M params | L11 |
| One-parameter-at-a-time gradient, 1M params | **7.1 hours** per step vs 35.6 ms | L11 |
| Missing ReLU mask, gradient-checked on one input | **passed at 4.94e-11** | L11 |
| Adam vs stable SGD on a 1000:1 bowl | **125 vs 3,450 steps**; SGD diverges 10% above the limit | L12 |
| Adam without bias correction, first step | **3.16× too large** | L12 |
| One poisoned row in 512, unclipped | weights **±2e+221**, loss `nan` | L12 |
| Same model on 50-row test sets | scored **0.56 to 0.92** | L13 |
| Test rows needed to resolve a 2-point difference | **~5,000** | L13 |
| Random split on customer-grouped data with an ID feature | **+16.7 points** of fake accuracy | L13 |
| Resample-before-split | precision **0.96 vs 0.21**; 50% of test rows seen in training | L13 |
| Highest-accuracy threshold on 1% fraud | caught **4 of 87**, still beat the baseline | L14 |
| ROC-AUC under monotonic transforms | identical to **6 decimal places**; ECE 0.0011 → 0.2457 | L14 |
| At FPR 0.0201 (reads as excellent) | precision **0.1777**, 4.6 false alarms per catch | L14 |
| Micro-F1 vs macro-F1 with a rare class | **0.9150 vs 0.5711** | L14 |
| One outlier in 500 | RMSE 3.05 → **20.09**; R² 0.907 → **0.201** | L14 |

**If you remember nothing else from this module, remember the third-from-last row.** A model can have
a flawless AUC and tell you nothing truthful about probability.

---

## 4. Decision tables

### Which split?

| Rows are related by | Use |
|---|---|
| Nothing | Random |
| Class, one class rare | **Stratified** (the classification default) |
| An entity that repeats | **Grouped** |
| Time | **Temporal**, with a gap |
| Entity *and* time | Grouped temporal |

### Which metric?

| Situation | Report |
|---|---|
| Balanced classes | Accuracy — with a baseline |
| **Imbalanced** | **Precision, recall, PR-AUC + the base rate** |
| Missing is costly | Recall, F2 |
| False alarms are costly | Precision, F0.5 |
| You know the costs | **Expected cost** — the most defensible, the least used |
| Rare classes matter | **Macro** average |
| Regression, outliers matter | RMSE |
| Regression, outliers are noise | MAE |

### Diagnosing a loss curve

| Shape | Cause |
|---|---|
| `nan` in a few steps | LR far too high; no clipping |
| Sawtooth | LR too high |
| Falls then flat and high | LR slightly high, or underfitting |
| Smooth but still falling at the end | LR too low |
| Train falls, validation rises | Overfitting |

---

## 5. The five mistakes to actively guard against

1. **Reporting accuracy on imbalanced data.** Always print the majority baseline beside it.
2. **Resampling before splitting.** Split first, always, and resample the training side only.
3. **Choosing a threshold on the test set.** It is now a validation set and you have no test set.
4. **Comparing models on a small test set.** 0.90 vs 0.85 on 100 rows is noise.
5. **Trusting a gradient you never checked**, or checking it on one convenient input.

---

## 6. What carries forward

| From Module 3 | Where it returns |
|---|---|
| Cosine similarity | M6 embeddings, M7 retrieval — the core operation of both |
| Softmax temperature | M4-L14, M5 — the same formula, the same effect |
| Cross-entropy / perplexity | M4 model evaluation, M13 fine-tuning |
| Precision / recall / thresholds | M7-L16 RAG evaluation, M8-L15 agent evaluation, M5-L18 LLM evaluation |
| Grouped splits | M7-L16 — chunks of one document must not span the split |
| Calibration | M5-L18 — an LLM's stated confidence is not a probability |
| Baselines | M6 (keyword search), M7 (no retrieval), M8 (a single prompt) |
| Optimizer settings | M13 fine-tuning and LoRA |

**The single most transferable idea in this module:** most systems have two ways to be wrong, they
cost different amounts, and somebody has to choose where to sit. That is true of a classifier, a
retriever, a guardrail and an agent's escalation policy alike.

---

→ [Module 3 assessment](module-03-assessment.md)
