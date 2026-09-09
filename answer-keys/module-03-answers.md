# Module 3 — Answer Key

**Do not read this before attempting the questions.** Every answer below carries a reason, and for
multiple choice, a reason each distractor is wrong. The explanations are the point; the letters are
not.

| Section | Jump to |
|---|---|
| Lesson quizzes | [L01](#m3-l01) · [L02](#m3-l02) · [L03](#m3-l03) · [L04](#m3-l04) · [L05](#m3-l05) · [L06](#m3-l06) · [L07](#m3-l07) · [L08](#m3-l08) · [L09](#m3-l09) · [L10](#m3-l10) · [L11](#m3-l11) · [L12](#m3-l12) · [L13](#m3-l13) · [L14](#m3-l14) |
| Module assessment | [Section A](#module-assessment) · [B](#section-b) · [C](#section-c) · [D](#section-d) |
| Remediation | [Where to go if you scored low](#remediation) |

> **A note on the lesson quizzes.** They are **formative self-checks**, written so that reading the
> correct option teaches you something. As a side effect their options are uneven in length and the
> answer sits at position B more often than chance. Treat them as revision prompts, not as a test of
> whether you can discriminate between plausible options. **The module assessment is the graded
> instrument**, and its options are uniform in length with a balanced answer distribution.

---

<a id="m3-l01"></a>
## M3-L01 — Vectors, Matrices and Shapes

| Q | Answer | Why |
|---|---|---|
| 1 | **B** | Shape reads outermost-first: 1,000 rows of 1,536 numbers. A reverses it; C confuses a matrix with a vector; D misreads which axis is the item count. |
| 2 | **B** | `*` is element-wise; `@` is matrix multiplication. This is the single most common NumPy error for people arriving from maths notation. |
| 3 | **C** | Indexing removes an axis: `(2,3)[0]` → `(3,)`. It does **not** give `(1,3)` — that requires `m[0:1]`, and the difference breaks broadcasting downstream. |
| 4 | **B** | `axis=0` collapses rows, leaving one value per column. The mnemonic: the axis you name is the one that disappears. |
| 5 | **B** | Broadcasting aligns from the right. `(3,)` matches 3 columns; `(2,)` is compared against 3 and fails. A and D are simply false — broadcasting works between arrays. |
| 6 | **B** | It keeps the collapsed axis at length 1 so the result still broadcasts against the original — essential for row-wise normalisation. |
| 7 | **B** | `(n_samples, n_features)`. Universal across scikit-learn, PyTorch and every embedding API. D is wrong and believing it will cost you an afternoon. |
| 8 | **B** | Slices are views sharing memory. `.copy()` gives independence. This is not a bug — it is what makes NumPy fast. |
| 9 | **B** | `1e6 × 1536 × 4 bytes = 6.144e9` ≈ **6.1 GB**. C forgets the 4 bytes per float; D assumes float64 *and* doubles it. |
| 10 | Written | See rubric below. |

**Q10 rubric (3 marks).** Full marks require both meanings distinguished: (1) the **length of one
vector** — 1,536 numbers per embedding, a property of the model; (2) the **number of items** — 1,000
embeddings, a property of your data. Award 1 mark for naming both, 1 for a correct example of each,
1 for noting that confusing them produces a shape error rather than a silent bug — which is fortunate.

---

<a id="m3-l02"></a>
## M3-L02 — Dot Product, Norms and Cosine Similarity

| Q | Answer | Why |
|---|---|---|
| 1 | **B** | `3·2 + 4·1 = 10`. A is element-wise multiplication, not the dot product; C is the norm of `[3,4]`. |
| 2 | **C** | `√(9+16) = 5`. D is the squared norm — forgetting the square root. |
| 3 | **B** | Dividing by both magnitudes measures direction alone, so a long document is not scored higher merely for being long. A is false (it is marginally slower); C is false (cosine can be negative). |
| 4 | **C** | `c = 2a`, so the angle is zero and cosine is 1.0. The magnitude difference is exactly what cosine removes. |
| 5 | **B** | With `‖a‖ = ‖b‖ = 1` the denominator is 1, so cosine reduces to the dot product. This is why vector databases normalise at index time. |
| 6 | **B** | Query-time scoring becomes one dot product instead of a dot product plus two norms plus a division — across millions of vectors, that matters. |
| 7 | **B** | Rankings bias toward larger-magnitude vectors, typically longer documents. **No error is raised** — this is a silent quality failure, which is why it is worth knowing. |
| 8 | **C** | In high dimensions, random vectors are nearly orthogonal. This is why a cosine of 0.3 can be meaningful where it would be noise in 2-D. |
| 9 | **B** | Score distributions differ substantially between embedding models, so 0.8 means different things in different models. Measure the distribution on **your** data. |
| 10 | Written | See rubric. |

**Q10 rubric (3 marks).** Must explain that a raw dot product rewards magnitude, that document length
inflates magnitude for many embedding models, and therefore that long documents win regardless of
relevance. 1 mark each. A full-mark answer names the fix (normalise, or use cosine).

---

<a id="m3-l03"></a>
## M3-L03 — Statistics You Actually Need

| Q | Answer | Why |
|---|---|---|
| 1 | **B** | Mean `510/5 = 102`; median `3`. The gap is the entire lesson: one outlier moved the mean by 34× and the median not at all. |
| 2 | **B** | Squaring makes deviations positive so they do not cancel, and weights large deviations more heavily. C is false; absolute deviation is a perfectly valid alternative (it gives MAE). |
| 3 | **B** | Mean above median means right skew — a few large values pulling the average up. This is the normal shape of latency data. |
| 4 | **B** | Latency is right-skewed, so the mean describes almost no real request. p95 describes what your slowest users actually experience. |
| 5 | **B** | 3 points against an SE of 3.8 is inside the noise. Shipping on this evidence is a coin flip you have dressed up as a decision. |
| 6 | **B** | `SE ∝ 1/√n`, so halving the SE needs **4×** the data. This is why "just collect more data" gets expensive quickly. |
| 7 | **B** | NumPy defaults to `ddof=0` (population), pandas to `ddof=1` (sample). Neither is buggy; they answer different questions. |
| 8 | **B** | With 50 points, p99 is effectively the single maximum — unstable between runs and not an estimate of anything. |
| 9 | **B** | Centre, spread and sample size. A centre alone is not a summary; it is a number. |
| 10 | Written | See rubric. |

**Q10 rubric (3 marks).** Must convey: the measured difference is smaller than the uncertainty in the
measurement; more data would shrink that uncertainty (by `√n`); and the honest statement is
"indistinguishable so far", not "no difference". Deduct a mark for language implying the prompts are
*proven* equivalent.

---

<a id="m3-l04"></a>
## M3-L04 — Probability, Bayes and Base Rates

| Q | Answer | Why |
|---|---|---|
| 1 | **B** | "The probability of A given B has occurred." C is `P(B|A)`, the confusion the whole lesson is about. |
| 2 | **B** | Same numerator cell, different denominator — you are restricting attention to a different population. |
| 3 | **C** | ≈ 9%. `(0.001×0.99) / (0.001×0.99 + 0.999×0.01) = 0.00099/0.01098 = 0.090`. |
| 4 | **B** | The condition is so rare that 1% of the huge negative population outnumbers 99% of the tiny positive one. |
| 5 | **C** | `P(A)` — the base rate before evidence. Getting this wrong is how the base-rate fallacy happens. |
| 6 | **B** | It assumes conditional independence of features, which is almost always false for text. |
| 7 | **B** | The class *ranking* survives even when the probabilities are badly miscalibrated, and ranking is often all you need. |
| 8 | **B** | It means the model produced 0.87. Whether 87% of such cases are actually positive is an **empirical question about calibration** (M3-L14 §5.5), not something the number asserts. |
| 9 | **B** | Compute expected precision from the base rate and a realistic FPR *first*. If it is unusable, no architecture choice will save it. Doing this before collecting data has saved entire projects. |
| 10 | Written | See rubric. |

**Q10 rubric (3 marks).** Must include: what "99% accurate" leaves unspecified (accurate at what — the
FPR matters most here); a worked base-rate calculation; and the practical consequence (most alerts are
false, so the review process is the bottleneck).

---

<a id="m3-l05"></a>
## M3-L05 — Logarithms, Entropy and Cross-Entropy

| Q | Answer | Why |
|---|---|---|
| 1 | **B** | `2³ = 8`. |
| 2 | **B** | Multiplying many probabilities underflows to exactly `0.0`; adding their logs does not. This is why every real implementation works in log space. |
| 3 | **B** | `−log(p)` of the probability assigned to the **correct** class. All other terms are multiplied by zero. |
| 4 | **A** | The true class is billing, which received 0.90, so the loss is `−ln(0.90) = 0.105`. C (`3.912`) is `−ln(0.02)` — the loss if the model had been confidently wrong. |
| 5 | **B** | `−log(p)` is unbounded as `p → 0`, so near-zero probability on the truth costs enormously. This is deliberate, not a flaw. |
| 6 | **B** | `exp(1.386) = 4.0` — as uncertain as choosing uniformly among 4 options. Perplexity's units are "effective number of choices". |
| 7 | **B** | Only with the same tokenizer and the same evaluation data. Perplexity across different tokenizers is not a comparison. |
| 8 | **B** | Maximise the probability of the token that actually followed. Everything else a language model appears to do is downstream of that. |
| 9 | **B** | Right answers, low confidence. `argmax` is correct but the assigned probability is small. This is exactly the case where accuracy and loss disagree, and both are telling the truth. |
| 10 | Written | See rubric. |

**Q10 rubric (3 marks).** Must separate *being right* (argmax) from *being confident* (probability
mass), give a numeric illustration, and note when each matters — accuracy for a decision, loss for
training signal and for anything downstream that consumes probabilities.

---

<a id="m3-l06"></a>
## M3-L06 — Derivatives, Gradients and the Chain Rule

| Q | Answer | Why |
|---|---|---|
| 1 | **B** | How much the output changes for a tiny change in the input — a local slope. |
| 2 | **B** | `f'(x) = 2x`, so `f'(3) = 6`. C is `f(3)`, the value rather than the slope. |
| 3 | **B** | Increase it. A negative gradient means increasing the parameter *decreases* the loss — which is why the update rule subtracts. |
| 4 | **B** | Steepest **increase** — hence the minus sign in `θ ← θ − α∇L`. Answering "the minimum" is the most common misconception here. |
| 5 | **C** | `dy/dx = 2(3x+1)·3 = 6(3x+1)`; at `x=2` that is `6·7 = 42`. D (49) is `y` itself; B (14) forgets the outer factor of 3. |
| 6 | **B** | One backward pass gives every parameter's gradient, for roughly the cost of one forward pass — M3-L11 §7.3 measured **1.46×**, against 7.1 hours for the naive alternative. |
| 7 | **B** | Exploding gradients or a `log(0)`. In practice: lower the learning rate, then add clipping. |
| 8 | **B** | Below ~`1e-8`, floating-point cancellation in the subtraction dominates. M3-L06 §7.3 measured the optimum at `h ≈ 1e-5` with a central difference. |
| 9 | **B** | `argmax` and hard thresholds have zero gradient almost everywhere, so nothing could learn through them. |
| 10 | Written | See rubric. |

**Q10 rubric (3 marks).** Must state that a gradient is a vector of per-parameter sensitivities, that
it points uphill, and that training therefore steps against it. A full-mark answer notes that it is
**local** — it describes an infinitesimal nudge, not the effect of a large change.

---

<a id="m3-l07"></a>
## M3-L07 — Loss Functions and Gradient Descent

| Q | Answer | Why |
|---|---|---|
| 1 | **B** | One number measuring wrongness, which training minimises. |
| 2 | **B** | With a sigmoid, MSE's gradient carries a `σ'(z)` factor that vanishes when the model is confidently wrong — exactly when you most need a large gradient. M3-L07 §7.3 measured CE reaching 0.998 where MSE reached 0.010 from a confidently-wrong start. |
| 3 | **B** | MSE → mean, MAE → median. This is why MAE is robust to outliers and MSE is not. |
| 4 | **B** | `w` is multiplied by `x` (1–3) while `b` is multiplied by 1, so the input magnitude scales the gradient. |
| 5 | **B** | Learning rate too high. M3-L12 §7.3 shows the full set of loss-curve shapes. |
| 6 | **B** | Overfitting. The model is fitting the training set's noise (M1-L08). |
| 7 | **B** | Good-enough gradient estimate, fits in memory, maps onto GPU computation, and its noise is mildly regularising. |
| 8 | **B** | Accuracy is a step function with zero gradient almost everywhere. You optimise a differentiable surrogate and *report* accuracy. |
| 9 | **B** | Every unit computes the same output and receives the same gradient, so they never differentiate. M3-L10 §7.3 measured all four units remaining at `[0,0,0]`. |
| 10 | Written | See rubric. |

**Q10 rubric (3 marks).** Must name at least three distinct diagnoses tied to observable curve shapes
(`nan` → LR far too high; oscillation → LR too high; flat → LR too low or underfitting; train down /
validation up → overfitting), and state what you would change first. Full marks require "check the
learning rate before reaching for a different optimizer".

---

<a id="m3-l08"></a>
## M3-L08 — Linear Regression End to End

| Q | Answer | Why |
|---|---|---|
| 1 | **B** | `X (n,d)`, `w (d,)`, `ŷ (n,)`. One prediction per row. |
| 2 | **B** | Exactly as good as always predicting the mean. |
| 3 | **B** | Yes — on held-out data a model can be worse than the mean, which is an unambiguous signal that something is wrong. A negative R² is information, not an error. |
| 4 | **B** | A coefficient's size depends on its feature's scale, so unstandardised coefficients cannot be compared. |
| 5 | **B** | Multicollinearity: coefficients become unstable and can take large opposite values while predictions remain fine. The *predictions* are trustworthy; the *interpretation* is not. |
| 6 | **B** | `solve` is faster and numerically more stable than forming an explicit inverse, and it raises informatively on a singular matrix. |
| 7 | **B** | Extrapolation. The model applies its fitted slope confidently far outside the range it has seen, and nothing in the output warns you. |
| 8 | **B** | Fast, explainable, and it establishes the baseline a complex model must beat by enough to justify itself. |
| 9 | **B** | An **association** in this data, holding other features constant. A ("causes") is the error worth guarding against — no regression coefficient establishes causation. |
| 10 | Written | See rubric. |

**Q10 rubric (3 marks).** Must explain that with 5 points and several features there is almost no room
for error, that R² will approach 1 by construction, and that the honest response is to hold out data
or gather more. Full marks reference M3-L08 §7.3, where five invented rows gave **R² = 1.0000** by
lying exactly on a plane.

---

<a id="m3-l09"></a>
## M3-L09 — Logistic Regression, Sigmoid and Softmax

| Q | Answer | Why |
|---|---|---|
| 1 | **B** | `w·x + b` is unbounded; probabilities must lie in [0,1]. The sigmoid is the squashing step. |
| 2 | **B** | `σ(0) = 1/(1+1) = 0.5`. |
| 3 | **B** | +1.2 to the **log-odds**, multiplying the odds by `e^1.2 ≈ 3.32`. A and D are the two most common misreadings. |
| 4 | **B** | The sigmoid is non-linear: a fixed log-odds change moves the probability a lot near 0.5 and barely at all near 0 or 1. |
| 5 | **B** | Nothing mathematically — softmax is shift-invariant — but it prevents `exp` overflow. Every real implementation does it. |
| 6 | **B** | `exp([2,1,0.1]) = [7.389, 2.718, 1.105]`, sum `11.212` → `[0.659, 0.242, 0.099]`. |
| 7 | **B** | The two derivatives cancel, leaving a gradient of simply `p − y` — the same result M3-L11 §5.1 relies on. |
| 8 | **B** | Flattens the distribution toward lower-scoring options. Identical mechanism to LLM sampling temperature (M4-L14). |
| 9 | **B** | Perfect separation: loss can always be reduced by scaling weights up, so the unregularised optimum is at infinity. Regularisation is the fix. |
| 10 | Written | See rubric. |

**Q10 rubric (3 marks).** Must state that the coefficient is constant in **log-odds** but not in
probability, give the sigmoid's non-linearity as the reason, and give a numeric example showing a
larger probability change near 0.5 than near 0.95.

---

<a id="m3-l10"></a>
## M3-L10 — Neural Networks: Weights, Biases, Activations

| Q | Answer | Why |
|---|---|---|
| 1 | **B** | It collapses to a single linear layer. M3-L10 §7.3 measured a 5-layer, 1,579-parameter network reproduced exactly by **21 numbers**, max difference 9.33e-15. |
| 2 | **B** | ReLU's derivative is exactly 1 for positive inputs, so gradients survive depth. Measured: sigmoid's gradient product over 50 layers is **7.89e-31**; ReLU's stays 1.0. |
| 3 | **B** | That unit contributes nothing **and receives no gradient** from that example. The second half is the part people miss. |
| 4 | **B** | Negative input for every example → always outputs 0 → always zero gradient → weights never change. Self-sustaining, and measured in M3-L11 §7.3 as bit-identical weights after 2,000 steps. |
| 5 | **B** | `784·128+128 + 128·64+64 + 64·10+10 = 100,480 + 8,256 + 650 = 109,386`. C forgets the biases and the later layers. |
| 6 | **B** | Framework cross-entropy losses expect **logits** and apply softmax internally for numerical stability. Applying softmax yourself and then using such a loss applies it twice. |
| 7 | **C** | `8e9 × 4 bytes = 32 GB`. And M3-L12 §7.3 measured that training with Adam needs roughly **4×** that. |
| 8 | **B** | Symmetry: identical outputs, identical gradients, permanent identity. |
| 9 | **B** | Very little in practice. It guarantees existence, not learnability, width, or that gradient descent will find it. |
| 10 | Written | See rubric. |

**Q10 rubric (3 marks).** Must identify that without activations the depth is wasted, state the
collapse result, and give the fix. Full marks cite the measured collapse (1,579 → 21).

---

<a id="m3-l11"></a>
## M3-L11 — Backpropagation

| Q | Answer | Why |
|---|---|---|
| 1 | **B** | Backwards reuses shared intermediates so one pass yields every gradient; forwards would need one pass per parameter. Measured: **35.6 ms vs 7.1 hours** for 1M parameters. |
| 2 | **B** | `p − y`. The messy softmax and cross-entropy derivatives cancel, which is why frameworks fuse them. |
| 3 | **B** | The same shape as `W`. This is the most useful debugging invariant in backpropagation — a shape mismatch finds a transpose error without any understanding of the maths. |
| 4 | **B** | A weight's gradient is proportional to the activation it multiplies, and `h1[0] = 2.2` is twice `h1[1] = 1.1`. |
| 5 | **B** | Blocks it entirely — multiplies by zero. Measured in §7.3: column 0 of `dL/dW1` was **exactly** zero, not merely small. |
| 6 | **B** | The loop closes on itself: zero output → zero gradient → unchanged weights → zero output. |
| 7 | **B** | Wrong. Anything above 1e-4 indicates a genuine bug; below 1e-7 is correct. |
| 8 | **B** | The backward pass needs them — ReLU needs `z` to know what to block — which is why activation memory grows with depth and batch size. |
| 9 | **B** | Summed. This is exactly why residual connections help: they add a second gradient path with local derivative 1. |
| 10 | **B** | Correct *on that input only*. §7.3 measured a real missing-mask bug passing at **4.94e-11** on an input where every unit happened to be active. Check several inputs, chosen to exercise the branches. |
| 11 | **B** | Sigmoid's derivative peaks at 0.25, so 12 layers multiply by at most `0.25¹² ≈ 6e-08`. Measured spread: sigmoid **31,035,255×**, ReLU **0.4×**. |
| 12 | Written | See rubric. |

**Q12 rubric (3 marks).** Must state that one backward pass produces all gradients by reusing
intermediates, that its cost is proportional to the forward pass rather than to the parameter count,
and give the contrast with the naive approach. Full marks quote a measured figure.

---

<a id="m3-l12"></a>
## M3-L12 — Learning Rate, Epochs, Batches and Optimizers

| Q | Answer | Why |
|---|---|---|
| 1 | **C** | `10,000/100 = 100` steps per epoch × 5 = **500**. |
| 2 | **A** | Learning rate far too high. Fix that before anything else. |
| 3 | **B** | Divides each parameter's step by a running estimate of its gradient magnitude, giving every parameter its own effective rate. Measured: **125 steps vs 3,450** for the fastest stable SGD on a 1000:1 bowl. |
| 4 | **B** | Early gradients are large and uninformative and Adam's variance estimate is unreliable at step 1. |
| 5 | **C** | **1e-5 to 5e-5.** Using a pretraining rate (1e-3) to fine-tune destroys the pretrained behaviour, and it is the most common fine-tuning mistake. |
| 6 | **B** | Halves it — noise falls as `1/√batch`. Measured: 8× the batch gave 2.80× less noise against a predicted 2.83×. |
| 7 | **B** | Two extra copies (first and second moments). Measured: a 7B model needs ~26 GB to serve and **~104 GB** to train with Adam, before activations. |
| 8 | **B** | Scaling all gradients by one factor preserves the update's **direction** and changes only its magnitude. |
| 9 | **B** | On step 1, `m̂/√v̂ = g/|g| = ±1`, so the step size is set by the learning rate rather than the gradient. This is precisely why Adam is less LR-sensitive than SGD. |
| 10 | Written | See rubric. |

**Q10 rubric (3 marks).** Must state that the learning rate has the largest effect of any
hyperparameter and that a wrong one cannot be rescued by a better optimizer; map at least three curve
shapes to diagnoses; and describe a sweep. Full marks note that the usable range typically spans two
orders of magnitude, so a six-value sweep is cheap and reliable.

---

<a id="m3-l13"></a>
## M3-L13 — Splits, Class Imbalance and Stratification

| Q | Answer | Why |
|---|---|---|
| 1 | **B** | Grouped by `patient_id`. Otherwise scans of the same patient sit on both sides and you score the model on patients it has already learned. |
| 2 | **B** | A small test set may contain very few positives, or none. Measured: over 500 random 200-row test sets from 2%-positive data, **13 contained zero positives** and recall was undefined. |
| 3 | **B** | Duplicates of the same row land on both sides. Measured: **50% of test rows** had an identical twin in training, lifting precision from 0.21 to **0.96** — entirely fabricated. |
| 4 | **B** | `√(0.9×0.1/100) = 0.03`. |
| 5 | **B** | Very little. Measured: on 50-row test sets the *same model* scored between **0.56 and 0.92**. |
| 6 | **C** | Threshold tuning. No retraining, fully reversible, and it lets the business set the precision/recall balance. Measured in M3-L14 §7.3 as the best-performing of the four. |
| 7 | **B** | Folds would train on data from after the validation period — information that would not exist at prediction time. |
| 8 | **B** | The 99% was never real. The honest number is 96%, and the model is now measurable. |
| 9 | **B** | Near-identical chunks appear on both sides, so retrieval is measured against text the system effectively already has. M7-L16 returns to this. |
| 10 | Written | See rubric. |

**Q10 rubric (4 marks).** One mark each for: **grouped** by `customer_id` (customers repeat);
**temporal** with the test set latest (you predict the future); **stratified** within that (0.3%
positive); and a sizing note — 0.3% of a test set needs to be large enough to contain enough positives
to measure, so roughly 33,000 test rows for ~100 positives. Deduct for any answer that reports
accuracy as the headline metric.

---

<a id="m3-l14"></a>
## M3-L14 — Metrics, Baselines and Thresholds

| Q | Answer | Why |
|---|---|---|
| 1 | **B** | `40/(40+10) = 0.80`. |
| 2 | **B** | `40/(40+60) = 0.40`. |
| 3 | **B** | Recall. A is precision — the pair most often swapped under pressure. |
| 4 | **B** | FPR divides false positives by the large negative count so they barely register, while precision divides them by the small flagged count. Measured: at **FPR 0.0201** — which reads as excellent — precision was **0.1777**, 4.6 false alarms per catch. |
| 5 | **B** | `2(1.0)(0.02)/1.02 = 0.039 ≈ 0.04`. A (0.51) is the arithmetic mean, which is exactly the error F1 exists to prevent. |
| 6 | **B** | A baseline — at minimum the majority-class accuracy. Measured: a model catching **4 of 87** fraud cases had the highest accuracy in a whole threshold sweep and beat the do-nothing baseline. |
| 7 | **B** | ROC-AUC unchanged, calibration destroyed. Measured: AUC identical to **six decimal places** across squaring, cubing and rescaling while ECE went 0.0011 → 0.2457. |
| 8 | **B** | On validation. A threshold tuned on test means you no longer have a test set. |
| 9 | **B** | The dominant class is handled well and rare classes badly. Measured: micro 0.9150 against macro 0.5711, with the rarest class at F1 **0.0952**. |
| 10 | **B** | The 0.2-point gain is nearly meaningless, the model misses 80% of the fraud, and accuracy is measuring the majority class rather than the task. |
| 11 | Written | See rubric. |

**Q11 rubric (4 marks).** One mark each for: accuracy is dominated by the 99% of non-fraud;
precision and recall trade off and cannot both be maximised; the threshold is a business decision
requiring their input on costs; and a concrete offer of what you *will* give them (a threshold table,
or a precision/recall pair against a stated capacity or cost). Deduct for any answer that supplies a
single number without a baseline.

---

<a id="module-assessment"></a>
# Module 3 Assessment — Answer Key

## Section A — Recall (13 marks)

| Q | Answer | Reason, and why the distractors fail |
|---|---|---|
| A1 | **D** | `b = 10a` — identical direction, so cosine is 1.0. C (10.0) is impossible: cosine is bounded by [−1, 1], and any answer outside that range is a check you can apply instantly. |
| A2 | **C** | `(0.0001×0.99)/(0.0001×0.99 + 0.9999×0.01) = 0.000099/0.010098 ≈ **0.0098**`. A (99%) is the classic base-rate fallacy — it reports `P(positive\|disease)` instead of `P(disease\|positive)`. |
| A3 | **A** | `−ln(0.02) = 3.912`. C returns the probability itself; B is negative and a loss cannot be. |
| A4 | **B** | A composition of linear maps is a linear map, so any depth collapses to one layer. A is the intuitive but wrong answer — it is not slower, it is *less expressive*. |
| A5 | **D** | `p − y`. A is the sigmoid's own derivative; C is the loss, not its gradient. |
| A6 | **A** | The learning rate. `nan` within a few steps is almost always a rate far above the stability limit. |
| A7 | **A** | Two — the first and second moments. This is why training memory is roughly 4× parameter memory. |
| A8 | **D** | Grouped by patient. B (stratified only) is a real trap: stratification is also desirable at 4% positive, but it does **not** prevent a patient's scans spanning the split. |
| A9 | **A** | `TP/(TP+FP)`. B is recall. |
| A10 | **D** | `2(1.0)(0.01)/1.01 = 0.0198 ≈ 0.02`. A (0.505) is the arithmetic mean. |
| A11 | **C** | Unchanged — AUC depends only on ranking, and squaring is monotonic. |
| A11b | **A** | ECE rises. The ranking is preserved but the probabilities are now systematically too low. |
| A12 | **C** | `√(0.9×0.1/100) = √0.0009 = 0.03`. |

---

<a id="section-b"></a>
## Section B — Applied reasoning (12 marks, 2 each)

**B1 (2).** *"What is the base rate, and what does the majority-class baseline score?"* — 1 mark.
Because on an imbalanced problem, 94% may be **below** a do-nothing baseline, and accuracy cannot be
interpreted without one — 1 mark. Accept equivalent phrasings; do not accept "what model did you use?"

**B2 (2).** Report **0.72**, the grouped number — 1 mark. Say that the 0.99 measured performance on
customers the model had already seen, so it describes re-recognition rather than prediction, and that
the drop is a *correction*, not a regression — 1 mark. Full marks for adding: check what mechanism
made grouping matter, since a random split only leaks when the model can identify the group.

**B3 (2).** ROC-AUC's FPR denominator is the large negative population, so many false positives barely
move it — 1 mark. At a 0.5% base rate the flagged set is small, so the same false positives dominate
precision and the alerts are mostly wrong — 1 mark. Full marks for asking for PR-AUC and the base rate.

**B4 (2).** Duplicated minority rows land on both sides of the split, so the model is tested on rows it
memorised; 0.97 is fabricated — 1 mark. Correct order: **split first, then resample the training side
only** — 1 mark.

**B5 (2).** Class weighting shifts predicted probabilities away from observed frequencies, so an
expected-cost calculation built on them is wrong even though the ranking is fine — 1 mark. First
action: plot a reliability diagram / compute ECE on validation, then recalibrate (Platt or isotonic) —
1 mark. Accept "check calibration before trusting the numbers".

**B6 (2).** Established: the gradient is correct **for that input** — 1 mark. Not established: that it
is correct for inputs exercising other branches; a missing ReLU mask passes at 4.94e-11 when every
unit is active — 1 mark.

---

<a id="section-c"></a>
## Section C — Calculation (18 marks, 3 each)

### C1 (3 marks)

```
total = 30 + 20 + 70 + 880 = 1000
accuracy  = (30 + 880) / 1000 = 0.9100
precision = 30 / (30 + 20)    = 0.6000
recall    = 30 / (30 + 70)    = 0.3000
F1        = 2(0.6)(0.3)/(0.9) = 0.4000
```

Majority-class baseline: 900 negatives / 1000 = **0.9000**.

**Interpretation (1 of the 3 marks):** the model beats the do-nothing baseline by **1 point** while
missing **70 of 100** positives — so accuracy is measuring the majority class, and precision/recall
are the numbers that describe the task.

*Marking:* 1 mark for all four metrics correct to 4 dp; 1 for the baseline; 1 for the interpretation.
Deduct nothing for arithmetic that follows a correctly stated formula.

### C2 (3 marks)

```
a·b = 2 + 8 + 8 = 18       ‖a‖ = √9 = 3      ‖b‖ = √36 = 6
cos(a,b) = 18 / (3×6) = 18/18 = 1.0000

a·c = -1 + 0 + 2 = 1        ‖c‖ = √2 ≈ 1.4142
cos(a,c) = 1 / (3 × 1.4142) = 1/4.2426 = 0.2357
```

**`b` is more similar** — in fact identical in direction, since `b = 2a`. Magnitude did not decide it
because cosine divides both magnitudes out; `b` is twice as long as `a` and still scores exactly 1.0.

*Marking:* 1 mark per cosine; 1 for the magnitude explanation.

### C3 (3 marks)

**(a) Forward:**
```
z_h   = 0.5(2.0) + (-0.3)(1.0) + 0.2 = 1.0 - 0.3 + 0.2 = 0.9
h     = ReLU(0.9) = 0.9
z_out = 1.5(0.9) + (-0.1) = 1.35 - 0.1 = 1.25
p     = σ(1.25) = 1/(1 + e^-1.25) = 1/1.2865 = 0.7773
```

**(b)** `∂L/∂z_out = p − y = 0.7773 − 1 = **−0.2227**` (sigmoid + BCE, cancelled).

**(c)**
```
∂L/∂h    = -0.2227 × 1.5 = -0.3341
∂L/∂z_h  = -0.3341 × 1   = -0.3341     (z_h = 0.9 > 0, so ReLU passes it)
∂L/∂w[0] = x[0] × ∂L/∂z_h = 2.0 × (-0.3341) = **-0.6681**
```

*Marking:* 1 mark for (a) complete; 1 for (b) including the correct sign; 1 for (c) showing the ReLU
step explicitly. Award the (c) mark only if the ReLU mask is mentioned — a candidate who skips it
gets the right answer here by luck, since the unit happened to be active.

### C4 (3 marks)

```
SGD:  Δ = -0.1 × [0.8, 0.02] = [-0.0800, -0.0020]

Adam, t = 1, from m = v = 0:
  m  = 0.1 × [0.8, 0.02]          = [0.0800, 0.0020]
  v  = 0.001 × [0.64, 0.0004]     = [0.00064, 0.0000004]
  m̂ = m / (1 - 0.9¹)   = m/0.1    = [0.8000, 0.0200]
  v̂ = v / (1 - 0.999¹) = v/0.001  = [0.6400, 0.0004]
  √v̂                              = [0.8000, 0.0200]
  Δ  = -0.1 × [0.8/0.8, 0.02/0.02] = [-0.1000, -0.1000]
```

**Why equal:** on the first step `m̂/√v̂ = g/|g| = ±1` for every parameter, so the step size is the
learning rate regardless of gradient magnitude.

*Marking:* 1 for SGD; 1 for Adam including bias correction; 1 for the explanation. A candidate who
omits bias correction gets `[-0.3162, -0.3162]` — award the Adam mark at half if the working is
otherwise correct and they notice the values are still equal.

### C5 (3 marks)

**(a)** `4,000 × 0.005 = **20 positives**`.

**(b)** `SE = √(0.98 × 0.02 / 4000) = √(4.9e-6) = **0.0022**`.

**(c)** The difference is 0.003. The SE of a *difference* of two independent proportions is about
`0.0022 × √2 = 0.0031`, so a 0.003 gap is **within one standard error** — indistinguishable.

Full marks require the additional point: with only ~20 positives, accuracy is almost entirely
determined by the 3,980 negatives, so neither figure says anything about the positive class at all.
The right response is to report precision and recall with the positive count, not to pick a winner.

*Marking:* 1 mark each for (a), (b) and (c). Award (c) only if the candidate concludes
"indistinguishable" rather than naming a winner.

### C6 (3 marks)

**(a)** RMSE/MAE = **1.05** in the first case: errors are tightly clustered and of similar size.
RMSE/MAE = **4.75** in the second: a few very large errors dominate, even though the *average*
absolute error is identical. The ratio is a direct read-out of error skew.

**(b)** **RMSE.** MAE treats one 60-minute error as equal to six 10-minute errors (both total 60
minutes). RMSE squares them: `60² = 3,600` against `6 × 10² = 600` — a 6× heavier penalty on the
single large error, which is exactly the stated cost structure.

*Marking:* 1 mark per ratio interpretation; 1 for the RMSE choice **with** the numeric justification.
An unjustified "RMSE" scores 0 on that mark.

---

<a id="section-d"></a>
## Section D — Practical assignment (28 marks)

### D1 — Audit (8 marks, up to 2 per problem, best 4 scored)

Available problems, with the evidence to gather:

1. **`customer_avg_churn_rate` is target leakage.** "Historical churn propensity per account" is
   almost certainly a per-account mean of the label. *Evidence:* check whether it was computed over
   all 12 months; check its correlation with the label; retrain without it. *Expect:* a large drop.
   Project 3's section 7(b) measured **+0.0871 PR-AUC** from exactly this feature.
2. **Accuracy on a 3.1% problem is uninformative.** The always-negative baseline scores **96.9%** —
   *higher than the claimed 96.8%*. *Evidence:* compute the baseline. *Expect:* the model is worse
   than doing nothing, by the metric quoted.
3. **6,700 customers over 12 months means grouped rows.** *Evidence:* re-split by `account_id` and
   compare. *Expect:* a drop, whose size depends on whether the model can identify accounts — with
   `account_id` present as a feature, expect a large one.
4. **No temporal split.** Churn is time-dependent and the model will be used on future months.
   *Evidence:* re-split with the last months held out. *Expect:* a drop.
5. **Threshold 0.5 is arbitrary and contradicts the stated capacity.** 40 reviews a week against
   80,000 rows implies flagging well under 0.1%. *Evidence:* count how many rows clear 0.5.
   *Expect:* far more than 40.
6. **ROC-AUC 0.94 on a 3.1% problem may still be unusable.** *Evidence:* compute PR-AUC and the base
   rate; compute precision at the capacity-implied threshold.
7. **`region` and `plan_tier` may be proxies for protected characteristics.** *Evidence:* sliced
   metrics with support counts.
8. **No calibration statement**, and no statement of what the model is for.

*Marking:* 2 marks per problem correctly identified **with** appropriate evidence and a stated
expectation; 1 mark if the problem is named without evidence. Score the best four. A candidate who
finds problems 1 and 2 has found the two that matter most.

### D2 — Re-evaluate (8 marks)

| Element | Expected answer | Marks |
|---|---|---|
| Split | Grouped by `account_id`, **and** temporal with the latest months held out, with a gap if any feature uses a rolling window | 2 |
| Features | Drop `customer_avg_churn_rate`, or recompute it fold-safely from training months only | 2 |
| Metrics | Precision, recall, PR-AUC **with the base rate**, plus the always-negative baseline; not accuracy alone | 2 |
| Threshold | From the 40-per-week capacity, chosen on validation; report the precision and recall it yields | 2 |

Deduct 1 mark for any element chosen without a stated reason.

### D3 — Report (6 marks)

| Criterion | Marks |
|---|---|
| States what the model does in one plain sentence, no jargon | 1 |
| Gives the honest number **with its baseline** | 1 |
| States the capacity-implied operating point: at 40 reviews/week, N of them are real, catching X% of churn | 2 |
| Asks for a decision (accept this trade-off, fund more reviewers, or accept lower recall) rather than presenting a number to admire | 2 |

Deduct 2 marks for reporting accuracy as the headline. Deduct 1 for any unexplained term
("PR-AUC", "F1") without a plain-language gloss.

### D4 — Limitations (6 marks)

1 mark each for a limitation about: **the data** (grouping, imbalance, the leaky feature's history);
**the method** (correlational, not causal); **calibration** (probabilities not usable for
expected-cost decisions without recalibration); **the split** (what it does and does not simulate);
**the evaluation's silence** on subgroup performance; and an explicit statement that **no metric here
establishes legal or regulatory compliance**.

Award the last mark only if that final point is present. It is the one candidates skip, and it is the
one that matters when the model reaches a real review.

---

<a id="remediation"></a>
## Remediation

If you scored below 50/71, work through the rows matching the questions you missed **before**
starting Module 4. Modules 6, 7 and 8 assume this material fluently.

| Missed | Revisit | Then do |
|---|---|---|
| A1, C2 | [M3-L02](../modules/module-03-math-ml-essentials/M3-L02-dot-product-cosine.md) §5 | Lab `l02`, exercises 1–2. **This is the most-used single operation in Modules 6 and 7.** |
| A2, B3 | [M3-L04](../modules/module-03-math-ml-essentials/M3-L04-probability.md) §5.4 | Exercise 2, then M3-L14 §5.3 |
| A3 | [M3-L05](../modules/module-03-math-ml-essentials/M3-L05-logs-entropy.md) §5.3 | Lab `l05` |
| A4, A5 | [M3-L10](../modules/module-03-math-ml-essentials/M3-L10-neural-networks.md) §5.2, [M3-L11](../modules/module-03-math-ml-essentials/M3-L11-backpropagation.md) §5.1 | The M3-L10 collapse proof, then M3-L11 §6 by hand |
| A6, A7, C4 | [M3-L12](../modules/module-03-math-ml-essentials/M3-L12-optimizers.md) §5.2, §5.5 | Lab `l12` sections 1–4 |
| A8, B2, B4 | [M3-L13](../modules/module-03-math-ml-essentials/M3-L13-splits-imbalance.md) §5.3, §5.7 | Lab `l13`, then Project 3 exercise 3 |
| A9, A10, C1 | [M3-L14](../modules/module-03-math-ml-essentials/M3-L14-metrics.md) §5.1–5.2 | Write the metrics from scratch; check against `metrics.py` |
| A11, A11b, B5 | [M3-L14](../modules/module-03-math-ml-essentials/M3-L14-metrics.md) §5.5 | Lab `l14` sections 4–5 |
| A12, B1, C5 | [M3-L03](../modules/module-03-math-ml-essentials/M3-L03-statistics.md) §5.5, [M3-L13](../modules/module-03-math-ml-essentials/M3-L13-splits-imbalance.md) §5.4 | Lab `l13` section 1 |
| B6, C3 | [M3-L11](../modules/module-03-math-ml-essentials/M3-L11-backpropagation.md) §5.5, §6 | Lab `l11` sections 3–4 |
| C6 | [M3-L14](../modules/module-03-math-ml-essentials/M3-L14-metrics.md) §5.7 | Lab `l14` section 7 |
| Section D | [Project 3](../projects/project-03-classifier/README.md) | Its exercises 1 and 3 in full |

---

→ [Module 4 — Generative AI and LLM Internals](../modules/module-04-genai-llm-internals/)
