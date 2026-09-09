# M3-L09 — Logistic Regression and the Sigmoid

| | |
|---|---|
| **Lesson ID** | M3-L09 |
| **Difficulty** | 2 (Core) |
| **Estimated study time** | 2.0 hours |
| **Prerequisites** | [M3-L08](M3-L08-linear-regression.md), [M3-L05](M3-L05-logs-entropy.md) |

---

> **Why this lesson matters beyond classification.** The softmax you meet here is the *same function*
> that turns a language model's raw scores into next-token probabilities (M4-L14). Temperature,
> top-p and every sampling parameter operate on its output. Understanding softmax here means
> understanding LLM decoding later.

---

## 1. Learning objectives

1. **Explain** why a linear model cannot output a probability, and how the sigmoid fixes it.
2. **Compute** the sigmoid, softmax and their outputs by hand.
3. **Implement** logistic regression by gradient descent.
4. **Explain** the relationship between logits, odds, log-odds and probabilities.
5. **Choose** a decision threshold deliberately, rather than accepting 0.5.

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **Logistic regression** | A linear model whose output is squashed into (0, 1) and interpreted as a probability. |
| **Logit** (`z`) | The raw linear output `wx + b`, before squashing. Range −∞ to +∞. |
| **Sigmoid** (σ) | `1 / (1 + e⁻ᶻ)`. Maps any real number to (0, 1). |
| **Softmax** | The multi-class generalisation: turns a vector of logits into probabilities summing to 1. |
| **Odds** | `p / (1 − p)`. The ratio of "happens" to "does not". |
| **Log-odds** | `log(p / (1 − p))`. Equals the logit — hence the name. |
| **Decision threshold** | The probability above which you predict the positive class. |
| **Decision boundary** | The set of inputs where the model is exactly undecided. |
| **Saturation** | The flat region of the sigmoid where gradients vanish (M3-L07). |
| **One-vs-rest** | Training one binary classifier per class. |
| **Temperature** | A divisor applied to logits before softmax, controlling output sharpness. |

---

## 3. Plain-language explanation

Linear regression outputs any number. For classification you need a **probability**, between 0 and 1.

A linear model cannot promise that. `w·x + b` might be −4.7 or 12.3, and neither is a probability.

**The sigmoid squashes any real number into (0, 1):**

$$\sigma(z) = \frac{1}{1 + e^{-z}}$$

| z | σ(z) |
|---|---|
| −5 | 0.007 |
| −2 | 0.119 |
| **0** | **0.500** |
| 2 | 0.881 |
| 5 | 0.993 |

An S-shaped curve. Very negative → near 0. Zero → exactly 0.5. Very positive → near 1. It never
quite reaches either end, which matters: the model can be very confident but never *certain*.

**So logistic regression is two steps:**

1. Compute a linear score: `z = w·x + b` (exactly as in M3-L08).
2. Squash it: `p = σ(z)`.

That is the entire model. It is linear regression with a squashing function bolted on, trained with
cross-entropy (M3-L05) rather than MSE — and M3-L07 §5.2 showed you exactly why that loss choice is
not optional.

---

## 4. Analogy

**A dimmer switch with end stops.** The linear score is how far you turn the knob; the sigmoid is the
mechanism converting that into brightness between fully off and fully on. Turn it far enough either
way and further turning changes almost nothing.

### Where the analogy breaks

1. **A dimmer has real end stops. The sigmoid never reaches 0 or 1** — it only approaches them. A
   logistic model cannot express certainty, which is arguably a feature (M1-L10).
2. **"Almost off" on a dimmer is still light. p = 0.001 is a claim about frequency**, and whether it
   is trustworthy is the calibration question (M1-L10, M3-L04 §5.6).
3. **The flat regions of a dimmer are harmless. The sigmoid's flat regions kill gradients** —
   saturation is why cross-entropy is required and why initialisation matters (§5.6).
4. **A dimmer has one knob. Multi-class needs softmax**, where the outputs compete: raising one
   probability necessarily lowers the others.

---

## 5. Detailed technical explanation

### 5.1 The sigmoid and its derivative

$$\sigma(z) = \frac{1}{1 + e^{-z}}
\qquad
\sigma'(z) = \sigma(z)\bigl(1 - \sigma(z)\bigr)$$

That derivative form is unusually convenient — the derivative is expressible in terms of the output
itself, so no extra computation is needed during backpropagation.

**It is also the source of the saturation problem.** `σ'` is maximal at `z = 0` (value 0.25) and
approaches 0 at both extremes:

| z | σ(z) | σ'(z) |
|---|---|---|
| −6 | 0.0025 | **0.0025** |
| 0 | 0.5 | **0.25** |
| 6 | 0.9975 | **0.0025** |

At `z = ±6` the gradient is a hundredth of its peak. This is exactly the factor that made MSE fail in
M3-L07 §5.2 — and why cross-entropy, whose gradient is simply `σ(z) − y` with no `σ'` factor, is the
correct loss.

**Numerical stability.** `np.exp(-z)` overflows for large negative `z`. Real implementations branch:

```python
def sigmoid(z):
    return np.where(z >= 0,
                    1 / (1 + np.exp(-np.abs(z))),
                    np.exp(-np.abs(z)) / (1 + np.exp(-np.abs(z))))
```

Use your framework's version; know that the naive one warns or produces `nan` at the extremes.

### 5.2 Logits, odds and log-odds

These three describe the same thing on different scales, and moving between them is a genuinely
useful skill.

| Scale | Range | Formula |
|---|---|---|
| Probability | 0 to 1 | `p` |
| Odds | 0 to ∞ | `p / (1 − p)` |
| **Log-odds (logit)** | −∞ to ∞ | `log(p / (1 − p))` |

| p | Odds | Log-odds |
|---|---|---|
| 0.1 | 0.11 (1:9) | −2.20 |
| 0.5 | 1.00 (1:1) | **0.00** |
| 0.9 | 9.00 (9:1) | +2.20 |
| 0.99 | 99.0 | +4.60 |

**The sigmoid is exactly the inverse of the log-odds.** That is why `z` is called a logit: the linear
part of the model predicts log-odds, and the sigmoid converts them back to probability.

**This gives coefficients a clean interpretation.** A coefficient of 0.7 means: a one-unit increase in
that feature adds 0.7 to the log-odds, multiplying the **odds** by `e^0.7 ≈ 2.01`. So the odds
roughly double.

**It does not double the probability.** Odds and probability are not the same, and this is a very
common misreading. Doubling odds from 1:9 (p = 0.1) gives 2:9 (p = 0.18) — an 8-point rise. Doubling
odds from 9:1 (p = 0.9) gives 18:1 (p = 0.947) — under 5 points. **The same coefficient produces a
different probability change depending on where you start.**

### 5.3 Softmax for multiple classes

For `K` classes, the model produces `K` logits and softmax converts them to probabilities:

$$\text{softmax}(z)_i = \frac{e^{z_i}}{\sum_{j=1}^{K} e^{z_j}}$$

Each output is positive, and they sum to exactly 1.

**Worked by hand.** Logits `[2.0, 1.0, 0.1]`:

1. Exponentiate: `e² = 7.389`, `e¹ = 2.718`, `e^0.1 = 1.105`
2. Sum: `7.389 + 2.718 + 1.105 = 11.212`
3. Divide: `[0.659, 0.242, 0.099]`

Check: they sum to 1.000 ✓

**Two properties that matter:**

- **The outputs compete.** Raising one logit lowers every other probability. This is unlike
  independent sigmoids, and it is why softmax suits *mutually exclusive* classes (multi-class) while
  per-label sigmoids suit multi-label (M1-L03 §5.2).
- **Only differences matter.** Adding a constant to every logit leaves the output unchanged, because
  the constant cancels. This is used for numerical stability: subtract the maximum logit before
  exponentiating, or `e^1000` overflows.

```python
def softmax(z):
    z = z - z.max()          # numerically essential, mathematically a no-op
    e = np.exp(z)
    return e / e.sum()
```

**Softmax with temperature** — the same function you will meet in M4-L14:

$$\text{softmax}(z/T)_i$$

| T | Effect |
|---|---|
| → 0 | Approaches picking the maximum (deterministic) |
| 1 | The model's own distribution |
| > 1 | Flatter — more of the probability mass moves to lower-scoring options |

**When an LLM API takes a `temperature` parameter, this is what it divides.** The lab shows the same
logits producing very different distributions at different temperatures.

### 5.4 Training

Identical to M3-L08 except for the squashing and the loss.

$$L = -\frac{1}{n}\sum \bigl[y_i \log(p_i) + (1-y_i)\log(1-p_i)\bigr]$$

That is cross-entropy for two classes: when `y = 1` only the first term survives, giving `−log(p)`
(M3-L05 §5.4).

**The gradient is remarkably clean:**

$$\frac{\partial L}{\partial w} = \frac{1}{n}X^\top(p - y)$$

**Identical in form to linear regression's gradient**, with `p` in place of `ŷ`. The sigmoid's
derivative and cross-entropy's derivative cancel exactly — which is the mathematical reason those two
are always paired.

### 5.5 The decision threshold

The model outputs a probability. Turning it into a decision needs a **threshold**, and 0.5 is a
default, not a law.

| Threshold | Effect |
|---|---|
| Lower (0.3) | More positives predicted → higher recall, lower precision |
| 0.5 | The default |
| Higher (0.8) | Fewer positives → higher precision, lower recall |

**Choose it from the cost of each error type, not from convention.**

- Screening for a serious condition: false negatives are catastrophic → **low threshold**.
- Auto-blocking user content: false positives silence real users → **high threshold**.
- Rare events (M3-L04 §5.4): even a high threshold may yield poor precision, and that arithmetic
  should be done before building.

The M1-L10 lab already showed you how to choose this from measured data rather than by guessing.

### 5.6 What can go wrong

**Perfect separation.** If a feature separates the classes exactly, the optimal coefficient is
infinite — the model can always increase confidence by scaling up. Coefficients grow without bound
and the loss creeps toward zero. **Regularisation fixes it**, which is why scikit-learn's
`LogisticRegression` applies it by default.

**Saturation from bad initialisation.** Starting deep in the flat region gives near-zero gradients.
Small random initialisation and standardised features keep you near `z = 0`, where gradients are
largest.

**Confusing logits with probabilities.** Model outputs are often logits; applying a 0.5 threshold to a
logit means thresholding the probability at 0.5 too (since `σ(0) = 0.5`), but comparing a logit to
0.8 is meaningless.

**Assuming calibration.** Logistic regression is usually better calibrated than most models, but
"usually" is not "verified" (M1-L10, M3-L04 §5.6).

### 5.7 Assumptions and limitations

- Assumes the log-odds are linear in the features. Non-linear boundaries need engineered features.
- The decision boundary is a straight line (or hyperplane). It cannot separate a circle from its
  surroundings without a transformed feature.
- Sensitive to feature scaling, exactly as in M3-L08.
- Perfect separation makes the unregularised solution unbounded.

---

## 6. Worked example — will this ticket be escalated?

Two features, standardised. Weights `w = [1.2, 0.8]`, bias `b = −0.5`.

**Ticket A:** `body_length_std = 1.5`, `is_priority = 1`

**Step 1 — the logit.**
`z = 1.2 × 1.5 + 0.8 × 1 + (−0.5) = 1.8 + 0.8 − 0.5 = **2.1**`

**Step 2 — the sigmoid.**
`σ(2.1) = 1 / (1 + e^−2.1) = 1 / (1 + 0.1225) = 1 / 1.1225 = **0.891**`

An 89.1% probability of escalation.

**Step 3 — the odds.**
`odds = 0.891 / 0.109 = **8.17**` — about 8:1 on. And `log(8.17) = 2.10`, the logit. ✓

**Ticket B:** `body_length_std = −0.5`, `is_priority = 0`

- `z = 1.2 × (−0.5) + 0 − 0.5 = **−1.1**`
- `σ(−1.1) = 1 / (1 + e^1.1) = 1 / 4.004 = **0.250**`

**Step 4 — interpret the coefficients as odds ratios.**

- `body_length_std`: `e^1.2 = **3.32**`. Each standard deviation of extra length multiplies the odds
  of escalation by 3.32.
- `is_priority`: `e^0.8 = **2.23**`. High priority multiplies the odds by 2.23.

**Step 5 — the trap.** "Multiplying the odds by 3.32" is *not* "multiplying the probability by 3.32".
For ticket B (p = 0.250, odds 0.333), one extra standard deviation gives odds `0.333 × 3.32 = 1.106`,
so `p = 1.106/2.106 = **0.525**` — a rise of 27.5 points. For ticket A (p = 0.891, odds 8.17), the
same change gives odds 27.1, so `p = **0.964**` — a rise of only 7.4 points.

**The same coefficient, the same feature change, and a four-times-larger effect on probability at one
end than the other.** That is the sigmoid's shape, and it is why "each unit adds X% probability" is
always wrong for a logistic model.

**Step 6 — the decision boundary.** The model is exactly undecided where `z = 0`:

`1.2·x₁ + 0.8·x₂ − 0.5 = 0` → `x₂ = (0.5 − 1.2·x₁) / 0.8`

A straight line in feature space. Everything on one side is predicted positive, everything on the
other negative — and no logistic model can produce a boundary that is not a straight line in whatever
feature space you give it.

**Step 7 — the threshold.** At 0.5, ticket A (0.891) escalates and ticket B (0.250) does not. At a
threshold of 0.2, both would. Nothing about the model changed — only the decision rule bolted on top.

---

## 7. Practical activity

**File:** [`labs/m3/l09_logistic_regression.py`](../../labs/m3/l09_logistic_regression.py)

**Requires the venv:**

```bash
source .venv/bin/activate
python labs/m3/l09_logistic_regression.py
```

Plots the sigmoid and its derivative, verifies the §6 calculations, shows the logit/odds/probability
relationship, demonstrates the odds-ratio trap, implements logistic regression from scratch, shows
softmax with temperature, demonstrates numerical overflow and its fix, and sweeps decision thresholds.

### 7.1 Important lines

| Construct | Why |
|---|---|
| `1 / (1 + np.exp(-z))` | The sigmoid — and where it overflows. |
| `s * (1 - s)` | `σ'(z)` expressed via the output itself. |
| `z - z.max()` before `exp` | Softmax stability. Mathematically a no-op, numerically essential. |
| `(1/n) * X.T @ (p - y)` | The gradient — same form as linear regression. |
| `softmax(z / T)` | Temperature, the same operation an LLM applies. |

### 7.2 Expected output

`[EXECUTED]` 2026-09-08 with numpy 2.5.3, Python 3.12.3:

```
==========================================================================
LOGISTIC REGRESSION, THE SIGMOID AND SOFTMAX
==========================================================================

--------------------------------------------------------------------------
1. THE SIGMOID AND ITS DERIVATIVE
--------------------------------------------------------------------------
        z    sigma(z)   sigma_prime(z)   shape
       -6      0.0025           0.0025   
       -4      0.0180           0.0177   
       -2      0.1192           0.1050   ####
       -1      0.2689           0.1966   ##########
        0      0.5000           0.2500   ####################
        1      0.7311           0.1966   #############################
        2      0.8808           0.1050   ###################################
        4      0.9820           0.0177   #######################################
        6      0.9975           0.0025   #######################################

  sigma' peaks at z=0 with 0.25, and falls to 0.0025 at z=6
  a ratio of 101x

  THAT COLLAPSE IS SATURATION. It is the sigma'(z) factor that
  made MSE fail for classification in M3-L07: at z=+-6 the
  gradient is a hundredth of its peak. Cross-entropy's gradient
  is simply (p - y), with no sigma' factor at all.

--------------------------------------------------------------------------
2. PROBABILITY, ODDS AND LOG-ODDS - the same thing three ways
--------------------------------------------------------------------------
    probability          odds    log-odds (logit)   sigmoid(logit)
           0.01         0.010             -4.5951           0.0100
           0.10         0.111             -2.1972           0.1000
           0.25         0.333             -1.0986           0.2500
           0.50         1.000              0.0000           0.5000
           0.75         3.000              1.0986           0.7500
           0.90         9.000              2.1972           0.9000
           0.99        99.000              4.5951           0.9900

  The last column recovers the first exactly: the sigmoid IS the
  inverse of the log-odds. That is why z is called a 'logit' -
  the linear part of the model predicts log-odds.

--------------------------------------------------------------------------
3. THE SECTION 6 MODEL, VERIFIED
--------------------------------------------------------------------------
  w = [1.2, 0.8], b = -0.5

  ticket        body_std  priority        z        p     odds
  ticket A           1.5         1    2.100   0.8909    8.166
  ticket B          -0.5         0   -1.100   0.2497    0.333

  Check: log(odds) for ticket A = 2.1000, which is z = 2.1000

  Coefficients as ODDS RATIOS:
    body_length_std      e^1.2 = 3.320x the odds
    is_priority          e^0.8 = 2.226x the odds

--------------------------------------------------------------------------
4. THE ODDS-RATIO TRAP - why 'adds X% probability' is always wrong
--------------------------------------------------------------------------
  Coefficient 1.2 -> odds ratio 3.320
  Applying the SAME +1 standard deviation at different starting
  probabilities:

     start p   start odds    new odds     new p      change
        0.05        0.053       0.175    0.1487      +9.9%
        0.25        0.333       1.107    0.5253     +27.5%
        0.50        1.000       3.320    0.7685     +26.9%
        0.75        3.000       9.960    0.9088     +15.9%
        0.89        8.091      26.863    0.9641      +7.4%
        0.98       49.000     162.686    0.9939      +1.4%

  The SAME coefficient and the SAME feature change produce a
  27-point probability rise starting from 0.25 and under a
  2-point rise starting from 0.98.

  'Each unit adds X% probability' is therefore never a correct
  statement about a logistic model. The odds ratio is constant;
  the probability effect is not.

--------------------------------------------------------------------------
5. SOFTMAX
--------------------------------------------------------------------------
  logits = [2.0, 1.0, 0.1]
  exponentiate : [7.389 2.718 1.105]
  sum          : 11.213
  divide       : [0.659 0.242 0.099]
  sums to      : 1.000000

  ONLY DIFFERENCES MATTER - add 100 to every logit:
    [0.659 0.242 0.099]   identical? True

  OUTPUTS COMPETE - raise the first logit by 1:
    before [0.659 0.242 0.099]
    after  [0.84  0.114 0.046]
    The first rose; BOTH others fell. Softmax suits mutually
    exclusive classes. Independent per-label sigmoids suit
    multi-label problems (M1-L03).

--------------------------------------------------------------------------
6. NUMERICAL OVERFLOW - and the one-line fix
--------------------------------------------------------------------------
  logits = [1000.0, 999.0, 998.0]

  NAIVE softmax (no max subtraction):
    np.exp(1000) = inf
    result       = [nan nan nan]   <- nan, the distribution is destroyed

  STABLE softmax (subtract the max first):
    result       = [0.665241 0.244728 0.090031]
    sums to      = 1.000000

  Mathematically the two are identical - softmax is invariant to
  adding a constant. Numerically one produces nan and the other
  the right answer. This is why you use the library's version.

--------------------------------------------------------------------------
7. TEMPERATURE - the same knob an LLM exposes
--------------------------------------------------------------------------
  Next-token logits: {'Paris': 3.0, 'London': 1.0, 'Berlin': 0.5}

    temperature      Paris     London     Berlin   character
            0.1     1.0000     0.0000     0.0000   nearly deterministic
            0.5     0.9756     0.0179     0.0066   sharpened
            1.0     0.8214     0.1112     0.0674   the model's own distribution
            2.0     0.6045     0.2224     0.1732   flattened, more variety
            5.0     0.4392     0.2944     0.2664   approaching uniform
           20.0     0.3588     0.3246     0.3166   approaching uniform

  At T=0.1 the model picks 'Paris' essentially always. At T=20 it
  is close to choosing at random between all three.

  This IS the temperature parameter on an LLM API. 'temperature=0'
  is the limit of this table: always take the highest logit,
  which is greedy decoding (M1-L07, M4-L14).

--------------------------------------------------------------------------
8. LOGISTIC REGRESSION FROM SCRATCH
--------------------------------------------------------------------------
  400 samples, true w = [1.5, -2.0], true b = 0.3

     step        loss      w[0]      w[1]         b   accuracy
        0      0.6931    0.0000    0.0000    0.0000      0.482
      400      0.4207    1.4550   -2.1902    0.1080      0.800
      800      0.4207    1.4554   -2.1908    0.1080      0.800
     1200      0.4207    1.4554   -2.1908    0.1080      0.800
     1600      0.4207    1.4554   -2.1908    0.1080      0.800
     2000      0.4207    1.4554   -2.1908    0.1080      0.800

  recovered w = [1.455, -2.191], b = 0.108
  true      w = [1.5, -2.0], b = 0.3

  The gradient used was (1/n) X^T (p - y) - the SAME FORM as
  linear regression's, because the sigmoid's derivative and
  cross-entropy's derivative cancel exactly.

--------------------------------------------------------------------------
9. THE THRESHOLD IS A DECISION, NOT A DEFAULT
--------------------------------------------------------------------------
  2000 predictions, 7.7% genuinely positive

    threshold  predicted +   precision    recall       F1
          0.1         1658       0.093     1.000    0.170
          0.2         1198       0.126     0.981    0.223
          0.3          847       0.175     0.961    0.296
          0.5          379       0.351     0.864    0.499
          0.7          150       0.580     0.565    0.572
          0.9           31       0.935     0.188    0.314

  Nothing about the MODEL changed across those rows - only the
  decision rule bolted on top of it.

  Screening for something serious? Take a low threshold: catch
  more real cases, accept more false alarms.
  Auto-blocking user content? Take a high one: silencing a real
  user costs more than missing one bad post.
  0.5 is a default, not an answer.

==========================================================================
```

### 7.3 Reading the result

**Section 1 quantifies saturation.** `σ'` peaks at **0.25** when `z = 0` and falls to **0.0025** at
`z = 6` — a **100×** collapse. That factor is precisely what M3-L07 measured killing MSE's gradient,
and it is why cross-entropy (whose gradient is simply `p − y`, with no `σ'` term) is the correct
pairing rather than a stylistic preference.

**Section 4 is the table to show anyone who reports a logistic coefficient as a percentage:**

| Starting p | New p | Change |
|---|---|---|
| 0.05 | 0.149 | **+9.9 pts** |
| **0.25** | 0.525 | **+27.5 pts** |
| 0.75 | 0.909 | +15.9 pts |
| **0.98** | 0.994 | **+1.4 pts** |

**The same coefficient. The same feature change.** A 27.5-point effect starting from 0.25 and a
1.4-point effect starting from 0.98 — a twentyfold difference. The odds ratio (3.32×) is constant;
the probability effect is not, because the sigmoid is a curve.

So "each extra day increases escalation probability by 15%" is never a correct reading. The honest
sentence is *"each extra day multiplies the odds of escalation by 3.3"*.

**Section 6 shows why you use the library's softmax:**

```
NAIVE:  np.exp(1000) = inf  ->  result = [nan nan nan]
STABLE: result = [0.665241 0.244728 0.090031]
```

The naive version destroys the distribution entirely. The fix — subtracting the maximum logit — is
**mathematically a no-op**, because softmax is invariant to adding a constant. It changes nothing
about the answer and everything about whether you get one.

**Section 7 is the direct bridge to Module 4:**

| Temperature | Paris | London | Berlin |
|---|---|---|---|
| 0.1 | **1.0000** | 0.0000 | 0.0000 |
| 1.0 | 0.8214 | 0.1112 | 0.0674 |
| 5.0 | 0.4392 | 0.2944 | 0.2664 |
| 20.0 | 0.3588 | 0.3246 | 0.3166 |

Identical logits throughout — only the divisor changed. At T=0.1 the model is effectively
deterministic; at T=20 it is nearly picking at random among three tokens.

**This is exactly the `temperature` parameter on an LLM API**, applied to exactly this function.
`temperature=0` is the limit of the first row: always take the largest logit, which is the greedy
decoding whose repetition failure you already saw in the M1-L07 lab. When M4-L14 covers sampling, it
is this table with a 100,000-token vocabulary.

**Section 8** recovers `w = [1.455, −2.191]` against a true `[1.5, −2.0]` from 400 noisy samples,
using a gradient of `(1/n)Xᵀ(p − y)` — the *same form* as linear regression's, because σ' and
cross-entropy's derivative cancel. Note the loss reaching 0.4207 by step 400 and then not moving:
converged, and further training buys nothing (M13-L04).

**Section 9 is the threshold sweep, on a deliberately imbalanced problem (7.7% positive):**

| Threshold | Precision | Recall |
|---|---|---|
| 0.1 | 0.093 | **1.000** |
| 0.5 | 0.351 | 0.864 |
| 0.9 | **0.935** | 0.188 |

At 0.1 you catch **every** positive and 91% of your alerts are wrong. At 0.9 almost every alert is
right and you miss 81% of the cases. **The model is identical in every row.** Only the decision rule
changed.

This is the M3-L04 base-rate arithmetic in a different form, and it is why M3-L14 insists on
precision and recall rather than accuracy for imbalanced problems.

**Verification:** confirm `σ'` falling 100× from z=0 to z=6, the odds-ratio table showing +27.5 vs
+1.4 points, naive softmax producing `nan` at logit 1000, and temperature 0.1 giving essentially
1.0000 for the top token.

---

## 8. Common mistakes and troubleshooting

1. **Using MSE instead of cross-entropy.** M3-L07 §5.2 measured why.
2. **Reading a coefficient as a probability change.** It is a log-odds change; exponentiate for an
   odds ratio.
3. **Accepting 0.5 as the threshold** without considering error costs.
4. **Not standardising features.**
5. **Naive `exp` in softmax**, overflowing on large logits.
6. **Confusing logits with probabilities.**
7. **Assuming outputs are calibrated** without checking.
8. **Expecting a non-linear decision boundary** without engineered features.

| Symptom | Cause | Fix |
|---|---|---|
| `RuntimeWarning: overflow in exp` | Naive sigmoid/softmax on large values | Use the stable form; subtract the max |
| Coefficients grow without bound | Perfect separation | Add regularisation |
| Model stuck predicting one class | Class imbalance, or saturated initialisation | Weight the loss (M3-L13); standardise; init small |
| Probabilities all near 0.5 | Weights near zero — model has not learned | Check the learning rate and gradient flow |
| Good accuracy, poor precision on the rare class | Threshold and base rate (M3-L04) | Sweep the threshold; report precision/recall |
| Cannot separate the classes at all | The boundary is not linear in these features | Engineer features, or use a different model |

---

## 10. Exercises

### Exercise 1 — Beginner (~20 min)

By hand, then verify:

1. `σ(0)`, `σ(1)`, `σ(−1)`, `σ(3)`, `σ(−3)`.
2. `σ'(0)` and `σ'(4)`. What is the ratio, and what does it imply for training?
3. Convert p = 0.75 to odds and to log-odds.
4. Convert a logit of −1.5 to a probability.
5. Softmax of `[1.0, 2.0, 3.0]`. Confirm it sums to 1.

### Exercise 2 — Intermediate (~30 min)

Using the §6 model (`w = [1.2, 0.8]`, `b = −0.5`):

1. Compute `z` and `p` for four tickets of your choosing, including one deep in saturation.
2. Convert both coefficients to odds ratios and state them in plain English.
3. Reproduce the §5 trap: show the probability change from +1 standard deviation of body length at
   `p = 0.25` and at `p = 0.89`. Explain the difference.
4. Find the decision boundary line and plot or tabulate five points on it.
5. Sweep the threshold from 0.1 to 0.9 on 200 simulated tickets and report precision and recall at
   each. State which threshold you would ship and why.

### Exercise 3 — Challenge (~30 min)

1. Implement logistic regression by gradient descent. Train on separable and non-separable data.
   Report the coefficient magnitudes in both cases and explain the difference.
2. Add L2 regularisation and show it bounds the coefficients under perfect separation.
3. Demonstrate softmax overflow with logits of `[1000, 999, 998]`, then fix it with the max-subtract
   trick. Show that the outputs are identical after the fix.
4. Apply temperatures 0.1, 0.5, 1.0, 2.0 and 10.0 to logits `[3.0, 1.0, 0.5]`. Tabulate the
   distributions and explain what an LLM's `temperature=0` would mean.
5. Generate data where the classes form concentric circles. Fit logistic regression and report the
   accuracy. Then add `x² + y²` as a feature and refit. Explain both results using §5.7.

---

## 11. Quiz

**Q1.** Why can a plain linear model not output a probability?

- A. It is too slow.
- B. `w·x + b` can be any real number, including negative values and values above 1.
- C. It has no intercept.
- D. It can, with rounding.

**Q2.** What is `σ(0)`?

- A. 0  B. 0.5  C. 1  D. Undefined

**Q3.** A coefficient is 1.2. What does that mean?

- A. Each unit increase adds 1.2 to the probability.
- B. Each unit increase adds 1.2 to the log-odds, multiplying the odds by `e^1.2 ≈ 3.32`.
- C. The feature is 120% important.
- D. Each unit multiplies the probability by 1.2.

**Q4.** Why does the same coefficient produce different probability changes at different starting
points?

- A. A bug in the model.
- B. The sigmoid is non-linear — a fixed change in log-odds produces a large probability change near
  p = 0.5 and a small one near the extremes.
- C. The coefficient changes during inference.
- D. It does not; the change is constant.

**Q5.** What does subtracting the maximum logit before softmax achieve?

- A. It changes the probabilities to be more accurate.
- B. Nothing mathematically — softmax is invariant to adding a constant — but it prevents `exp`
  overflowing on large logits.
- C. It normalises the inputs.
- D. It applies temperature.

**Q6.** Softmax of `[2.0, 1.0, 0.1]` gives approximately:

- A. `[0.5, 0.3, 0.2]`  B. `[0.659, 0.242, 0.099]`  C. `[2.0, 1.0, 0.1]`  D. `[0.33, 0.33, 0.33]`

**Q7.** Why is cross-entropy paired with the sigmoid rather than MSE?

- A. It is faster.
- B. The sigmoid's derivative and cross-entropy's derivative cancel, leaving a gradient of simply
  `p − y` — whereas MSE retains a `σ'(z)` factor that vanishes when the model is confidently wrong.
- C. MSE cannot be computed for probabilities.
- D. Convention only.

**Q8.** What does a temperature above 1 do to a softmax distribution?

- A. Sharpens it toward the maximum.
- B. Flattens it, moving probability mass toward lower-scoring options.
- C. Nothing.
- D. Makes it sum to more than 1.

**Q9.** Your coefficients grow without bound during training. What is happening?

- A. The learning rate is too low.
- B. Perfect separation — the model can always reduce loss by scaling up, so the unregularised optimum
  is infinite. Add regularisation.
- C. The features are unscaled.
- D. The labels are wrong.

**Q10.** *(Written, rubric-graded.)* In under 80 words, explain to a colleague why "each extra day of
delay increases the escalation probability by 15%" is a wrong reading of a logistic coefficient.

---

## 12. Revision notes

- Logistic regression = **linear score, then squash**. `z = w·x + b`, then `p = σ(z)`.
- **`σ(z) = 1/(1+e⁻ᶻ)`**, S-shaped, `σ(0) = 0.5`, never reaches 0 or 1.
- **`σ'(z) = σ(z)(1−σ(z))`** — peaks at 0.25 when `z = 0`, collapses at both extremes. That is
  saturation, and why MSE fails here.
- **Logit = log-odds.** `p → odds = p/(1−p) → log-odds = z`. The sigmoid is the inverse.
- **A coefficient is a log-odds change.** `e^coefficient` is the **odds ratio**. It is *not* a
  probability change, and the same coefficient moves probability far more near 0.5 than near the ends.
- **Softmax:** `e^zᵢ / Σe^zⱼ`. Outputs compete and sum to 1. **Only differences matter** — subtract
  the max before `exp` for stability.
- **Temperature divides the logits** before softmax. Low = sharp, high = flat. This is exactly the
  LLM `temperature` parameter (M4-L14).
- **Gradient is `(1/n)Xᵀ(p − y)`** — same form as linear regression, because σ' and cross-entropy's
  derivative cancel.
- **0.5 is a default, not a law.** Choose the threshold from error costs.
- **Perfect separation ⇒ unbounded coefficients.** Regularise.
- The decision boundary is always **linear** in the features you supply.

---

## 13. Completion checklist

- [ ] I computed sigmoid and softmax values by hand.
- [ ] I converted between probability, odds and log-odds in both directions.
- [ ] I reproduced the §6 calculations and the odds-ratio trap.
- [ ] I implemented logistic regression from scratch.
- [ ] I demonstrated softmax overflow and fixed it.
- [ ] I applied temperature and can explain what `temperature=0` means.
- [ ] I swept a decision threshold and chose one deliberately.
- [ ] I scored 7/10 on the quiz.

---

## 14. References

- Hastie, Tibshirani & Friedman, *ESL*, Ch. 4.
  <https://hastie.su.domains/ElemStatLearn/> `[UNVERIFIED]`
- scikit-learn, Logistic Regression.
  <https://scikit-learn.org/stable/modules/linear_model.html#logistic-regression> `[UNVERIFIED]`

---

## 15. Next lesson

→ [M3-L10 — Neural Networks: Weights, Biases, Activations](M3-L10-neural-networks.md)

You have built a single-layer classifier. Next: stacking them — what an extra layer actually buys,
and why a non-linear activation is what makes depth mean anything.
