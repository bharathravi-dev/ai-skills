# M3-L08 — Linear Regression from Scratch

| | |
|---|---|
| **Lesson ID** | M3-L08 |
| **Difficulty** | 2 (Core) |
| **Estimated study time** | 2.0 hours |
| **Prerequisites** | [M3-L07](M3-L07-loss-gradient-descent.md) |

---

## 1. Learning objectives

1. **Write** the linear model in both scalar and matrix form, and **state** every shape.
2. **Implement** linear regression by gradient descent, from scratch.
3. **Interpret** learned coefficients, and **state** what they do not mean.
4. **Compare** against a baseline and **evaluate** with R², MAE and RMSE.
5. **Diagnose** the three practical failures: unscaled features, multicollinearity, and extrapolation.

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **Linear model** | A prediction formed as a weighted sum of features plus a constant. |
| **Coefficient / weight** | The multiplier learned for one feature. |
| **Intercept / bias** | The constant term; the prediction when all features are zero. |
| **Design matrix** | The feature matrix `X`, shape `(n_samples, n_features)`. |
| **Residual** | `actual − predicted` for one example. |
| **RMSE** | Root Mean Squared Error — MSE's square root, in the target's units. |
| **R²** | Coefficient of determination: the fraction of variance the model explains. |
| **Baseline** | The trivial model — here, always predicting the mean. |
| **Normal equation** | The closed-form solution `w = (XᵀX)⁻¹Xᵀy`. |
| **Multicollinearity** | Two or more features carrying nearly the same information. |
| **Extrapolation** | Predicting outside the range of the training data. |
| **Standardisation** | Rescaling each feature to mean 0, standard deviation 1. |
| **Regularisation** | Penalising large coefficients to reduce overfitting (Ridge, Lasso). |

---

## 3. Plain-language explanation

A linear model predicts by taking a **weighted sum** of the inputs:

$$\hat{y} = w_1x_1 + w_2x_2 + \cdots + w_dx_d + b$$

Each `wᵢ` says how much feature `i` contributes. `b` is the value when every feature is zero.

For predicting a support ticket's resolution time:

```
hours = 0.004 × body_length
      + 2.1   × is_high_priority
      - 0.8   × is_enterprise_customer
      + 1.5   (intercept)
```

Read directly: each extra character adds 0.004 hours; high priority adds 2.1 hours; enterprise
customers resolve 0.8 hours faster.

**Why start here.** Linear regression is the smallest complete machine-learning system: features,
parameters, a loss, an optimiser, an evaluation and a baseline. Everything in Module 4 is this
structure with more layers. And it is genuinely useful — for many tabular problems it is competitive
with far more complex models, and it is the baseline you must beat before anything else is justified
(M1-L11).

---

## 4. Analogy

**A recipe with quantities.** Each ingredient (feature) contributes in proportion to how much you
add. The coefficient is the amount per unit; the intercept is what you get with nothing added.

### Where the analogy breaks

1. **Ingredients interact — sugar and heat together are not their sum. A linear model cannot express
   that.** It has no way to say "high priority matters *only* for enterprise customers"; you must
   create an interaction feature by hand.
2. **A recipe's quantities are causal. Coefficients are not.** A negative coefficient on
   "is_enterprise" does not mean being enterprise *causes* faster resolution — it may reflect that
   enterprise tickets go to a better-staffed queue. §5.5.
3. **Recipes are bounded — you cannot add −2 eggs. Linear models extrapolate freely** and confidently
   off the end of the data, which is a real failure mode (§5.6).
4. **A recipe's ingredients are independent. Features are frequently correlated**, which makes the
   individual coefficients unstable even when predictions are fine (§5.6).

---

## 5. Detailed technical explanation

### 5.1 Matrix form

For `n` samples and `d` features, prediction for all samples at once:

$$\hat{y} = Xw + b$$

| Object | Shape | Meaning |
|---|---|---|
| `X` | `(n, d)` | Design matrix — one row per sample |
| `w` | `(d,)` | One coefficient per feature |
| `b` | scalar | Intercept |
| `ŷ` | `(n,)` | One prediction per sample |

```python
predictions = X @ w + b       # (n, d) @ (d,) -> (n,), then broadcast b
```

Check the shapes against M3-L01: `(n, d) @ (d,)` gives `(n,)`, and adding a scalar broadcasts. If you
get a shape error here it is almost always `X` transposed — the `(n_samples, n_features)` convention
is not optional.

### 5.2 The gradients

With `MSE = (1/n)Σ(ŷᵢ − yᵢ)²` and `ŷ = Xw + b`, the chain rule (M3-L06) gives:

$$\frac{\partial L}{\partial w} = \frac{2}{n}X^\top(\hat{y} - y)
\qquad
\frac{\partial L}{\partial b} = \frac{2}{n}\sum(\hat{y}_i - y_i)$$

```python
error = predictions - y                  # (n,)
grad_w = (2 / n) * (X.T @ error)         # (d, n) @ (n,) -> (d,)
grad_b = (2 / n) * error.sum()           # scalar
```

`X.T @ error` is the whole gradient computation — one matrix multiply for every coefficient at once.
This is why models are expressed in matrix form: it is the same arithmetic as M3-L07 §6, vectorised.

### 5.3 The closed form, and why it is not always used

Linear regression has an exact solution:

$$w = (X^\top X)^{-1}X^\top y$$

```python
w = np.linalg.solve(X.T @ X, X.T @ y)     # never use np.linalg.inv here
```

| | Normal equation | Gradient descent |
|---|---|---|
| Exactness | Exact | Approximate |
| Cost | ~O(d³) for the solve | O(n·d) per step |
| Large `d` (10k+ features) | Impractical | Fine |
| Data too large for memory | Impossible | Fine (mini-batches) |
| Multicollinearity | `XᵀX` becomes near-singular | Degrades gracefully |
| Generalises to other models | **No** | **Yes** |

**Use `np.linalg.solve`, never `np.linalg.inv`.** Explicitly inverting is slower and numerically
worse. If `XᵀX` is singular, `solve` raises — which is information, not a nuisance.

The closed form is worth knowing because it gives you an exact answer to check your gradient descent
against, which the lab does.

### 5.4 Evaluating

| Metric | Formula | Units | Reading |
|---|---|---|---|
| **MAE** | mean(\|ŷ − y\|) | Target's | Typical error size |
| **RMSE** | √mean((ŷ − y)²) | Target's | Like MAE but outlier-sensitive |
| **R²** | 1 − SS_res/SS_tot | None | Fraction of variance explained |

**R² compares your model against the mean-prediction baseline:**

$$R^2 = 1 - \frac{\sum(y_i - \hat{y}_i)^2}{\sum(y_i - \bar{y})^2}$$

| R² | Meaning |
|---|---|
| 1.0 | Perfect |
| 0.7 | Explains 70% of the variance |
| **0.0** | **Exactly as good as always predicting the mean** |
| Negative | **Worse than the mean** — genuinely possible on held-out data |

**R² = 0 meaning "no better than the baseline" is the useful property.** It builds the M1-L11
baseline comparison directly into the metric — and a negative R² on your test set is an unambiguous
signal that the model has learned nothing transferable.

**Report RMSE alongside R².** R² says how much variance you explain; RMSE says how wrong you are in
real units, which is what anyone acting on the prediction needs.

### 5.5 Interpreting coefficients — carefully

A coefficient of 2.1 on `is_high_priority` means: **holding every other feature constant**, a
high-priority ticket takes 2.1 hours longer.

**Four cautions, all of which matter in practice:**

1. **Scale dependence.** A coefficient of 0.004 on `body_length` (range 0–5000) and 2.1 on a 0/1 flag
   are not comparable. To compare importance, **standardise the features first**, then the
   coefficients are directly comparable.
2. **Not causal.** The model found a correlation in your data. "Enterprise resolves faster" may
   entirely reflect routing, staffing or SLA policy.
3. **Unstable under collinearity.** With two nearly-identical features, the fit can put +50 on one
   and −48 on the other. Predictions stay fine; the individual coefficients are meaningless. Adding a
   handful of rows can flip their signs.
4. **"Holding everything else constant" is often impossible.** If body length and priority are
   correlated in reality, no intervention changes one alone, so the coefficient describes an
   arithmetic relationship rather than an achievable action.

### 5.6 The three practical failures

**Unscaled features** (M3-L07 §6). Standardise. It also makes coefficients comparable.

**Multicollinearity.** Detect it by computing feature correlations, or by noticing coefficients that
swing wildly on a re-fit with slightly different data. Fixes: drop one of the pair, combine them, or
use Ridge regression, which penalises large coefficients and stabilises the fit.

**Extrapolation.** A linear model happily predicts for inputs far outside anything it has seen, with
no warning. If your training tickets are 50–2,000 characters, a 50,000-character ticket produces a
confident and absurd prediction. **Record the training range and refuse or flag inputs outside it** —
this is the same "know when you do not know" problem as M1-L10, in a simpler setting.

### 5.7 When linear regression is the right choice

**Use it when:** the relationship is roughly linear; you need explainable coefficients; you have few
samples relative to features; you need a fast, cheap baseline; or you must justify a decision to a
regulator.

**Do not use it when:** the relationship is strongly non-linear (unless you engineer features);
interactions dominate; or the target is a category — that is logistic regression, M3-L09.

**Always fit it first.** It takes minutes, and it tells you whether the signal is there at all. If a
linear model gets R² = 0.75, a neural network must beat that meaningfully to justify its cost and
opacity. If linear regression gets R² = 0.02, the problem is usually your features, not your model.

### 5.8 Assumptions and limitations

- Assumes a roughly linear relationship, and errors of roughly constant spread.
- Sensitive to outliers because MSE is (M3-L07 §5.1).
- Cannot represent interactions unless you create them explicitly.
- Coefficients are correlational, not causal.
- With more features than samples the closed form is singular and the model overfits badly.

---

## 6. Worked example — predicting resolution time

Five tickets, two features. Small enough to verify entirely by hand.

| # | body_length | is_high_priority | hours |
|---|---|---|---|
| 1 | 100 | 0 | 2.0 |
| 2 | 500 | 0 | 4.0 |
| 3 | 200 | 1 | 5.0 |
| 4 | 800 | 1 | 8.0 |
| 5 | 300 | 0 | 3.0 |

**Step 1 — the baseline.** Mean hours = `(2+4+5+8+3)/5 = 22/5 = **4.4**`.

Baseline SSE = `(2−4.4)² + (4−4.4)² + (5−4.4)² + (8−4.4)² + (3−4.4)²`
= `5.76 + 0.16 + 0.36 + 12.96 + 1.96 = **21.2**`

**Any model must beat 21.2 to be worth anything.** This is `SS_tot`, the denominator of R².

**Step 2 — the shapes.** `X` is `(5, 2)`, `w` is `(2,)`, `b` is a scalar, `ŷ` is `(5,)`.

**Step 3 — why you must standardise.** `body_length` ranges 100–800; `is_high_priority` is 0 or 1.
Their gradients differ by a factor of several hundred (M3-L07 §6), so descent on the raw features
either diverges or crawls.

Standardising `body_length`: mean = `(100+500+200+800+300)/5 = 380`, standard deviation ≈ 253.0.

| # | raw | standardised |
|---|---|---|
| 1 | 100 | (100−380)/253 = **−1.107** |
| 2 | 500 | **+0.474** |
| 3 | 200 | **−0.711** |
| 4 | 800 | **+1.660** |
| 5 | 300 | **−0.316** |

**Step 4 — fit.** Descent on the standardised features converges to (the lab verifies this against
the exact closed-form solution):

```
hours = 1.241 × body_length_std + 1.225 × is_high_priority + 4.400
```

**Step 5 — interpret, on the standardised scale.** Because both features are now standardised, the
coefficients *are* comparable: a one-standard-deviation increase in body length adds 1.24 hours, and
being high priority adds 1.22. **They matter almost equally** — a conclusion you could not have drawn
from the raw coefficients (0.005 and 2.5), which differ by a factor of 500 purely because of scale.

**Step 6 — evaluate.**

| Metric | Value |
|---|---|
| SSE | **0.0000** |
| R² | **1.0000** |
| RMSE | **0.0000** |

**Step 7 — and this is exactly why it is worthless.** A *perfect* fit. Before celebrating, notice
what happened: these five rows were constructed to satisfy `hours = 0.005×length + 2.5×priority +
1.5` exactly, with no noise. Three parameters can always fit five points that genuinely lie on a
plane.

**R² = 1.000 here tells you about the data, not about the model.** With five samples you cannot even
hold out a meaningful test set, so there is no way for the number to be informative. This is M1-L08's
lesson arriving early: a training score is not evidence, and a *perfect* training score is a warning.

The lab therefore repeats the exercise on 200 noisy samples with a proper train/test split, where
train R² is **0.871** and test R² is **0.863** — close together, which is what a healthy fit actually
looks like.

**Step 8 — extrapolate, and watch it fail.** Predict for a 50,000-character ticket. Standardised,
that is `(50000−380)/253 ≈ 196`, giving roughly `1.24 × 196 + 4.40 ≈ **247 hours**` — over six
working weeks. The model states it confidently. Nothing in the arithmetic knows that no training ticket exceeded 800
characters.

---

## 7. Practical activity

**File:** [`labs/m3/l08_linear_regression.py`](../../labs/m3/l08_linear_regression.py)

**Requires the venv:**

```bash
source .venv/bin/activate
python labs/m3/l08_linear_regression.py
```

Implements linear regression from scratch, verifies gradient descent against the closed-form
solution, compares against the mean baseline, evaluates with R²/RMSE/MAE, shows raw versus
standardised coefficients, demonstrates multicollinearity destabilising coefficients while
predictions stay fine, and shows extrapolation failing confidently.

### 7.1 Important lines

| Construct | Why |
|---|---|
| `X @ w + b` | The whole forward pass. |
| `(2/n) * (X.T @ error)` | Every coefficient's gradient in one matrix multiply. |
| `np.linalg.solve(X.T @ X, X.T @ y)` | The exact solution, to check descent against. |
| `1 - ss_res / ss_tot` | R², computed directly from the definition. |
| `(X - X.mean(0)) / X.std(0)` | Standardisation. |

### 7.2 Expected output

`[EXECUTED]` 2026-09-08 with numpy 2.5.3, Python 3.12.3:

```
/home/bharathr/self/Learning/claude/ai/labs/m3/l08_linear_regression.py:44: RuntimeWarning: overflow encountered in square
  history.append(float((error ** 2).mean()))
/home/bharathr/self/Learning/claude/ai/labs/m3/l08_linear_regression.py:45: RuntimeWarning: overflow encountered in matmul
  w -= lr * (2 / n) * (x.T @ error)
/tmp/claude-1001/-home-bharathr-self-Learning-claude-ai/9c4512c5-c9dc-4273-a0a7-c085ab932aab/scratchpad/venvtest/lib/python3.12/site-packages/numpy/_core/_methods.py:49: RuntimeWarning: overflow encountered in reduce
  return umr_sum(a, axis, dtype, out, keepdims, initial, where)
/home/bharathr/self/Learning/claude/ai/labs/m3/l08_linear_regression.py:42: RuntimeWarning: invalid value encountered in matmul
  pred = x @ w + b
/tmp/claude-1001/-home-bharathr-self-Learning-claude-ai/9c4512c5-c9dc-4273-a0a7-c085ab932aab/scratchpad/venvtest/lib/python3.12/site-packages/numpy/_core/_methods.py:132: RuntimeWarning: overflow encountered in reduce
  ret = umr_sum(arr, axis, dtype, out, keepdims, where=where)
/home/bharathr/self/Learning/claude/ai/labs/m3/l08_linear_regression.py:45: RuntimeWarning: invalid value encountered in matmul
  w -= lr * (2 / n) * (x.T @ error)
/home/bharathr/self/Learning/claude/ai/labs/m3/l08_linear_regression.py:45: RuntimeWarning: invalid value encountered in subtract
  w -= lr * (2 / n) * (x.T @ error)
==========================================================================
LINEAR REGRESSION FROM SCRATCH
==========================================================================

--------------------------------------------------------------------------
1. THE BASELINE - what any model must beat
--------------------------------------------------------------------------
  hours = [2.0, 4.0, 5.0, 8.0, 3.0]
  mean  = 22 / 5 = 4.4

    actual    baseline    residual     squared
       2.0         4.4       -2.40      5.7600
       4.0         4.4       -0.40      0.1600
       5.0         4.4        0.60      0.3600
       8.0         4.4        3.60     12.9600
       3.0         4.4       -1.40      1.9600
                            SS_tot       21.20

  Baseline SSE = 21.20. Any model must beat this to be
  worth anything. It is also the DENOMINATOR of R2, which is why
  R2 = 0 means exactly 'no better than the mean'.
  Baseline R2  = 0.000000   (exactly zero, by construction)

--------------------------------------------------------------------------
2. WHY YOU MUST STANDARDISE
--------------------------------------------------------------------------
  feature                  min     max      mean       std
  body_length              100     800     380.0     248.2
  is_high_priority           0       1       0.4       0.5

  Scale ratio: 507x

  body_length standardised by hand:
    (100 - 380) / 248.2 = -1.128
    (500 - 380) / 248.2 = +0.483
    (200 - 380) / 248.2 = -0.725
    (800 - 380) / 248.2 = +1.692
    (300 - 380) / 248.2 = -0.322
  standardised mean = 0.0000000000, std = 1.0000

  Fitting on RAW features at several learning rates:
    alpha=1e-02    final MSE = DIVERGED
    alpha=1e-05    final MSE = DIVERGED
    alpha=1e-07    final MSE = 2.1917
  Fitting on STANDARDISED features at alpha=1e-01: final MSE = 0.000000

  On raw features no learning rate works well. On standardised
  features an ordinary one converges immediately.

--------------------------------------------------------------------------
3. GRADIENT DESCENT vs THE CLOSED FORM
--------------------------------------------------------------------------
                           w[body_len]   w[priority]   intercept
  gradient descent            1.240967      1.224745    4.400000
  closed form (exact)         1.240967      1.224745    4.400000
  difference                  1.11e-15      1.11e-15    1.78e-15

  Descent converged to the exact solution. Always check a from-
  scratch implementation against a known-correct one where you can.

  metric             value   reading
  SSE               0.0000   down from the baseline's 21.20
  R2                1.0000   explains 100.0% of the variance
  RMSE              0.0000   typically wrong by 0 minutes
  MAE               0.0000   hours

  A PERFECT fit. And that is precisely why it is worthless as
  evidence: these five points were constructed to lie exactly on
  a plane, and 3 parameters can always fit them. R2 = 1.000 here
  tells you about the data, not about the model (M1-L08).
  Section 5 fits 200 noisy samples with a held-out test set.

--------------------------------------------------------------------------
4. INTERPRETING COEFFICIENTS - raw vs standardised
--------------------------------------------------------------------------
  feature                raw coefficient    standardised
  body_length                   0.005000          1.2410
  is_high_priority              2.500000          1.2247
  intercept                     1.500000          4.4000

  The RAW coefficients cannot be compared: 0.0050 per
  character versus 2.50 per 0/1 flag says nothing about
  relative importance - the features are on wildly different scales.

  The STANDARDISED coefficients CAN be compared - both now mean
  'hours per one standard deviation of this feature':
    1. body_length            1.241
    2. is_high_priority       1.225

  Both models make IDENTICAL predictions. Standardisation changes
  the coefficients' units, not the fit.
  predictions identical? True

--------------------------------------------------------------------------
5. A REALISTIC FIT - 200 noisy samples
--------------------------------------------------------------------------
  200 samples, true relationship: hours = 0.003*body + 2.0*priority + 1.5 + noise
  split: 150 train / 50 test

                      R2      RMSE       MAE
  train           0.8706    0.7870    0.6218
  test            0.8633    0.7997    0.6293

  Train and test agree closely: a healthy fit, not overfitting
  (M1-L08). Compare with the 5-sample R2 of ~0.97 in section 3.

  coefficient               true   recovered
  body_length             0.0030      0.0031
  is_high_priority        2.0000      2.1954
  RMSE 0.800 vs the noise we injected (0.8) - the
  model has essentially recovered the truth and cannot do better
  than the noise floor.

--------------------------------------------------------------------------
6. MULTICOLLINEARITY - unstable coefficients, fine predictions
--------------------------------------------------------------------------
  correlation between feature 1 and feature 2: 0.999999

  fit on                              w1          w2        w3   test R2
  full data                       -15.11       18.10      1.99    0.9990
  bootstrap resample A            -17.90       20.89      1.97    0.9989
  bootstrap resample B            -17.83       20.83      1.97    0.9989
  bootstrap resample C            -16.35       19.35      1.98    0.9989

  w1 and w2 swing wildly between resamples - often large and of
  OPPOSITE sign - while R2 stays high and stable throughout.

  The model's PREDICTIONS are reliable. Its individual
  COEFFICIENTS are meaningless. Anyone reading 'feature 1 has a
  coefficient of +47' as an insight would be badly misled.

  Ridge regression (adding lambda*I to X'X) stabilises this:
    lambda=0.0    w1=  -15.11  w2=   18.10  w3=  1.99  R2=0.9990
    lambda=0.1    w1=    1.49  w2=    1.51  w3=  1.99  R2=0.9989
    lambda=1.0    w1=    1.49  w2=    1.49  w3=  1.97  R2=0.9989
    lambda=10.0   w1=    1.41  w2=    1.41  w3=  1.79  R2=0.9930
    As lambda grows the two collinear coefficients converge to a
    sensible shared value, at a small cost in training R2.

--------------------------------------------------------------------------
7. EXTRAPOLATION - confident and absurd
--------------------------------------------------------------------------
  Training body_length range: 100 to 800 characters

     body_length  standardised   predicted hours   status
             150         -0.93               2.3   in range
             400          0.08               3.5   in range
             800          1.69               5.5   in range
           5,000         18.61              26.5   EXTRAPOLATING
          50,000        199.92             251.5   EXTRAPOLATING

  A 50,000-character ticket gets a confident prediction of
  252 hours - over 6 working weeks. Nothing in the
  arithmetic knows that no training ticket exceeded 800 characters.

  Record the training range and flag inputs outside it. This is
  the same 'know when you do not know' problem as M1-L10, in a
  model simple enough to see it clearly.

==========================================================================
```

### 7.3 Reading the result

**Section 3 validates the implementation.** Gradient descent and the exact closed-form solution agree
to `1e-15` — floating-point identical. **Always check a from-scratch implementation against a
known-correct one where one exists**; it is how you distinguish "my maths is wrong" from "my data is
hard".

And then the perfect score, with its caveat: **R² = 1.0000, RMSE = 0.0000**. Not because the model is
good, but because the five rows were constructed to lie exactly on a plane and three parameters can
always fit them. Section 5 shows the realistic version — train R² **0.871**, test R² **0.863** — where
the two agreeing closely is what a healthy fit actually looks like.

**Section 4 is the coefficient-comparison trap:**

| Feature | Raw coefficient | Standardised |
|---|---|---|
| body_length | 0.005 | **1.241** |
| is_high_priority | 2.500 | **1.225** |

The raw coefficients differ by a factor of **500**, which invites the conclusion that priority
dominates. The standardised ones are **1.241 and 1.225** — the two features matter almost exactly
equally. The raw ratio was entirely an artefact of measuring one feature in characters and the other
in 0/1.

Note the closing check: both models make **identical predictions**. Standardisation changes the
coefficients' units, not the fit.

**Section 5 recovers the truth from noise.** The true relationship was
`0.003×body + 2.0×priority + 1.5`, and the fit recovered `0.0031` and `2.195`. Test RMSE is **0.800**
against the **0.8** noise we injected — the model has hit the noise floor and cannot do better,
which is the correct place for a well-specified model to stop.

**Section 6 is the most important demonstration in this lesson:**

```
fit on                    w1        w2      w3   test R2
full data             -15.11     18.10    1.99    0.9990
bootstrap resample A  -17.90     20.89    1.97    0.9989
```

Features 1 and 2 correlate at **0.999999**. The fit assigns **−15.11 and +18.10** — large values of
*opposite sign* to two features that are nearly the same thing — and these swing by several units
between resamples. Meanwhile **R² stays at 0.999** throughout.

**The predictions are excellent and the coefficients are meaningless.** Anyone reading "feature 1 has
a coefficient of −15, so it reduces the target" would be drawing a conclusion the data does not
support at all — the pair is jointly determined and individually arbitrary.

Ridge regression fixes it cleanly: at λ = 0.1 the two coefficients collapse to **1.49 and 1.51**, a
sensible shared value, at a cost of 0.0001 in R².

**Section 7 shows the confident absurdity.** Training body lengths ran 100–800 characters. A
50,000-character ticket is standardised to **199.9** — two hundred standard deviations out — and the
model returns **251 hours**, over six working weeks, with no hesitation.

Nothing in a linear model knows where its data ended. Recording the training range and flagging
inputs outside it is a three-line defence, and it is the same "know when you do not know" problem as
M1-L10 in a setting simple enough to see the whole mechanism.

**Verification:** confirm descent matches the closed form to ~1e-15, standardised coefficients of
1.241 and 1.225, test R² near 0.86 in section 5, opposite-signed collinear coefficients with R² near
0.999 in section 6, and a prediction over 200 hours for the 50,000-character input.

---

## 8. Common mistakes and troubleshooting

1. **Not standardising features.** Descent crawls or diverges.
2. **Comparing raw coefficients** as though they indicated importance.
3. **Reading coefficients as causal.**
4. **No baseline.** R² provides one; use it.
5. **Reporting R² without RMSE.** One is dimensionless, the other actionable.
6. **Extrapolating** beyond the training range.
7. **`np.linalg.inv`** instead of `solve`.
8. **Forgetting the intercept**, forcing the line through the origin.
9. **Trusting R² from very few samples.**

| Symptom | Cause | Fix |
|---|---|---|
| Loss diverges | Unscaled features, or α too high | Standardise; lower α |
| Coefficients swing wildly on re-fit | Multicollinearity | Drop or combine features; use Ridge |
| `LinAlgError: singular matrix` | Collinear features, or d > n | Remove redundancy; use descent or Ridge |
| Negative R² on test data | Worse than predicting the mean | The features carry no transferable signal |
| Great on training, poor on test | Overfitting (M1-L08) | More data; fewer features; regularise |
| Absurd prediction | Extrapolation | Check the input against the training range |

---

## 10. Exercises

### Exercise 1 — Beginner (~20 min)

Using the §6 data:

1. Compute the mean of `hours` and the baseline SSE by hand.
2. Standardise `body_length` by hand and verify the mean is 0.
3. For `w = [1.0, 2.0]`, `b = 4.0`, compute all five predictions and the MSE.
4. Compute `∂L/∂w` for both features and `∂L/∂b`.
5. Take one step at α = 0.1 and confirm the loss fell.

### Exercise 2 — Intermediate (~30 min)

1. Implement linear regression by gradient descent and fit the §6 data. Report `w`, `b`, R², RMSE.
2. Solve the same problem with the normal equation and confirm both agree to 4 decimal places.
3. Fit on **raw** features and on **standardised** features. Report the coefficients from both and
   explain why only one set is comparable.
4. Compute R² for the baseline model (always predict the mean) and confirm it is exactly 0.
5. Generate 200 noisy samples from a known linear relationship, fit, and report how close the
   recovered coefficients are to the truth.

### Exercise 3 — Challenge (~30 min)

1. Add a third feature that is `body_length × 1.001 + tiny noise`. Fit and report all three
   coefficients. Re-fit on a bootstrap resample and report them again. Explain what you observe.
2. Show that despite unstable coefficients, the model's **predictions** remain accurate. What does
   that tell you about interpreting coefficients?
3. Implement Ridge regression (add `λ·I` to `XᵀX`) and show it stabilises the coefficients. Sweep λ
   and report the trade-off against training R².
4. Write `predict_with_range_check(model, x, train_min, train_max)` that flags extrapolation. Test it
   on an in-range and a far-out-of-range input.
5. Fit a linear model to data generated from `y = x²`. Report R², then add `x²` as an explicit feature
   and refit. Explain both results in terms of §5.7.

---

## 11. Quiz

**Q1.** In `ŷ = Xw + b`, what are the shapes of `X`, `w` and `ŷ`?

- A. `(d, n)`, `(n,)`, `(d,)`  B. `(n, d)`, `(d,)`, `(n,)`  C. `(n, n)`, `(n,)`, `(n,)`
- D. `(d, d)`, `(d,)`, `(d,)`

**Q2.** What does R² = 0 mean?

- A. The model is perfect.
- B. The model is exactly as good as always predicting the mean.
- C. The model has no coefficients.
- D. All predictions are zero.

**Q3.** Can R² be negative?

- A. No, never.
- B. Yes — on held-out data a model can be worse than predicting the mean, which is an unambiguous
  signal it learned nothing transferable.
- C. Only for classification.
- D. Only with a bug.

**Q4.** Why must features be standardised before comparing coefficient magnitudes?

- A. To make training faster only.
- B. A coefficient's size depends on its feature's scale — 0.004 per character and 2.1 per 0/1 flag
  are not comparable until both features are on the same scale.
- C. Coefficients cannot be negative otherwise.
- D. It is not necessary.

**Q5.** Two nearly-identical features are included. What happens?

- A. Training fails immediately.
- B. Coefficients become unstable and can take large opposite values, while predictions stay
  accurate.
- C. R² becomes negative.
- D. The intercept disappears.

**Q6.** Why use `np.linalg.solve` rather than `np.linalg.inv`?

- A. `inv` does not exist.
- B. Explicitly inverting is slower and numerically less stable; `solve` also raises informatively on
  a singular matrix.
- C. `solve` gives a different answer.
- D. `inv` only works on square matrices.

**Q7.** Your model predicts 333 hours for a ticket far longer than any in training. What is this?

- A. A bug in the arithmetic.
- B. Extrapolation — the model applies its fitted slope confidently outside the range it has seen,
  with no mechanism to know it should not.
- C. Overfitting.
- D. Multicollinearity.

**Q8.** Why fit linear regression before trying anything more complex?

- A. It is required by convention.
- B. It is fast and explainable, and it establishes the baseline a complex model must meaningfully
  beat to justify its cost and opacity.
- C. Complex models cannot be trained without it.
- D. It always performs best.

**Q9.** A coefficient of −0.8 on `is_enterprise` means what?

- A. Being an enterprise customer causes 0.8 hours faster resolution.
- B. In this data, enterprise tickets are associated with 0.8 hours faster resolution, holding other
  features constant — which is correlation, not causation.
- C. Enterprise customers are 80% faster.
- D. The feature should be removed.

**Q10.** *(Written, rubric-graded.)* In under 80 words, explain why an R² of 0.97 on five samples is
not evidence that a model works.

---

## 12. Revision notes

- `ŷ = Xw + b`. Shapes: `X` **(n, d)**, `w` **(d,)**, `ŷ` **(n,)**. Samples first, always.
- Gradients: `∂L/∂w = (2/n)Xᵀ(ŷ−y)`, `∂L/∂b = (2/n)Σ(ŷ−y)`. One matrix multiply for all
  coefficients.
- **Closed form** `w = (XᵀX)⁻¹Xᵀy` — use `np.linalg.solve`, never `inv`. Exact, but O(d³) and does
  not generalise to other models.
- **R² = 0 means "no better than predicting the mean".** Negative R² on test data means worse than
  that. **Report RMSE alongside** — R² is dimensionless, RMSE is in real units.
- **Standardise before comparing coefficients.** Raw coefficient size reflects feature scale, not
  importance.
- **Coefficients are correlational, not causal**, and **unstable under multicollinearity** — large
  opposite values while predictions stay fine.
- **Linear models extrapolate confidently and absurdly.** Record the training range and flag inputs
  outside it.
- **Always fit linear regression first.** It is the baseline everything else must beat (M1-L11).
- High R² on very few samples is not evidence (M1-L08).

---

## 13. Completion checklist

- [ ] I can state the shape of every object in `ŷ = Xw + b`.
- [ ] I implemented gradient descent and matched the closed-form solution.
- [ ] I computed R² and confirmed the baseline scores exactly 0.
- [ ] I compared raw and standardised coefficients and can explain the difference.
- [ ] I destabilised coefficients with collinear features while predictions stayed accurate.
- [ ] I demonstrated extrapolation producing a confident absurdity.
- [ ] I scored 7/10 on the quiz.

---

## 14. References

- Hastie, Tibshirani & Friedman, *The Elements of Statistical Learning*, Ch. 3.
  <https://hastie.su.domains/ElemStatLearn/> `[UNVERIFIED]`
- scikit-learn, Linear Models.
  <https://scikit-learn.org/stable/modules/linear_model.html> `[UNVERIFIED]`

---

## 15. Next lesson

→ [M3-L09 — Logistic Regression and the Sigmoid](M3-L09-logistic-regression.md)

You can predict a number. Next: predicting a **class** — the sigmoid, the softmax, and why the output
of every classifier you meet is shaped the way it is.
