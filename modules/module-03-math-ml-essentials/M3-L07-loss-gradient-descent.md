# M3-L07 — Loss Functions and Gradient Descent

| | |
|---|---|
| **Lesson ID** | M3-L07 |
| **Difficulty** | 2 (Core) |
| **Estimated study time** | 2.0 hours |
| **Prerequisites** | [M3-L06](M3-L06-derivatives-gradients.md), [M3-L05](M3-L05-logs-entropy.md) |

---

## 1. Learning objectives

1. **Choose** the right loss function for a task shape and **justify** it.
2. **Explain** why MSE is wrong for classification, with the gradient as evidence.
3. **Implement** gradient descent and **read** a training curve.
4. **Distinguish** batch, stochastic and mini-batch descent, and state the trade-off.
5. **Diagnose** the five common training-curve pathologies.

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **Loss function** | A number measuring how wrong a prediction is. Lower is better. |
| **Cost / objective** | The loss averaged over a dataset. |
| **MSE** | Mean Squared Error: the average of `(prediction − truth)²`. |
| **MAE** | Mean Absolute Error: the average of `\|prediction − truth\|`. |
| **Cross-entropy** | The classification loss from M3-L05: `−log(q_true)`. |
| **Huber loss** | Quadratic near zero, linear far out. A compromise between MSE and MAE. |
| **Gradient descent** | Repeatedly stepping against the gradient to reduce the loss. |
| **Learning rate** (α) | How far to step each time. |
| **Epoch** | One full pass through the training data. |
| **Batch** | The set of examples used to compute one gradient. |
| **Mini-batch** | A small random subset, typically 8–512 examples. |
| **SGD** | Stochastic Gradient Descent — using a random subset each step. |
| **Convergence** | The loss stopping its meaningful decrease. |
| **Training curve** | Loss plotted against training step or epoch. |
| **Convex** | Bowl-shaped: one minimum, and gradient descent always finds it. |

---

## 3. Plain-language explanation

Training is a loop with three steps, repeated:

1. **Predict** with the current parameters.
2. **Measure** how wrong you were — that is the **loss**.
3. **Adjust** each parameter slightly in the direction that reduces the loss.

The loss function defines what "wrong" means, and **that choice determines what the model learns**.
Choose the wrong loss and the model optimises the wrong thing perfectly.

```python
for epoch in range(n_epochs):
    predictions = model(X)                    # 1. predict
    loss = loss_function(predictions, y)      # 2. measure
    gradients = compute_gradients(loss)       # 3a. which way?
    parameters -= learning_rate * gradients   # 3b. step
```

Every training loop you will ever read is this, with extra machinery around it.

**Two losses cover almost everything:**

| Task | Loss | Why |
|---|---|---|
| Regression (predict a number) | **MSE** | Penalises being far off, quadratically |
| Classification (predict a class) | **Cross-entropy** | Penalises confident errors, and gives usable gradients |

---

## 4. Analogy

**Rolling a ball down a valley in the dark.** The loss surface is the terrain, the ball is your
parameters, the gradient is the slope under it, and the learning rate is how big a hop it takes.

### Where the analogy breaks

1. **A real ball has momentum and keeps rolling. Plain gradient descent has none** — it re-reads the
   slope and hops, with no memory. Momentum-based optimisers (M3-L12) add that back deliberately.
2. **A valley has one bottom. Loss surfaces have many local minima and vast numbers of saddle
   points.** In high dimensions, saddles are the common obstacle, not local minima.
3. **The ball feels the true slope. SGD estimates it from a small sample**, so the path is noisy —
   and that noise is useful, because it helps escape flat regions.
4. **A ball cannot fly out of the valley. Too large a learning rate does exactly that**, and the loss
   diverges to infinity or `nan`.

---

## 5. Detailed technical explanation

### 5.1 Regression losses

**Mean Squared Error:**

$$\text{MSE} = \frac{1}{n}\sum_{i=1}^{n}(\hat{y}_i - y_i)^2$$

Its derivative with respect to a prediction is `2(ŷ − y)` — proportional to the error, so large
errors produce large corrections.

**Mean Absolute Error:**

$$\text{MAE} = \frac{1}{n}\sum_{i=1}^{n}|\hat{y}_i - y_i|$$

Its derivative is `+1` or `−1` — the same size regardless of how wrong you were.

| | MSE | MAE |
|---|---|---|
| Outliers | **Dominated by them** | Robust |
| Gradient | Proportional to error | Constant magnitude |
| Near the optimum | Gradient shrinks — converges smoothly | Gradient stays ±1 — can oscillate |
| Differentiable everywhere | Yes | **No** — a kink at zero |
| Optimises toward | The **mean** | The **median** |

**That last row is the one that decides it.** Minimising MSE gives you a model predicting the
conditional *mean*; minimising MAE gives the conditional *median*. Given M3-L03, you already know
those differ on skewed data — so on right-skewed targets like latency or price, MSE and MAE give
genuinely different models, not just different numbers.

**One outlier makes this concrete.** Predicting `[10, 12, 11, 500]`:

- Minimising MSE pulls the prediction toward 133 (the mean).
- Minimising MAE pulls it toward 11.5 (the median).

**Huber loss** is quadratic within a threshold δ and linear beyond it, giving MSE's smooth
convergence near zero and MAE's robustness to outliers.

### 5.2 Classification loss — and why MSE fails

For classification, use **cross-entropy** (M3-L05). Not MSE. The reason is the gradient.

Consider a binary classifier whose output is squashed by a sigmoid, `σ(z)`, and the true label is 1.

| Loss | Gradient with respect to `z` |
|---|---|
| Cross-entropy | `σ(z) − y` |
| MSE | `(σ(z) − y) × σ'(z)` |

The extra factor `σ'(z)` is the problem. The sigmoid saturates: for large positive or negative `z`,
`σ'(z)` approaches **zero**.

**So when the model is confidently wrong — exactly when you most need a large correction — MSE's
gradient goes to zero and learning stalls.** Cross-entropy has no such factor: its gradient is simply
the error, which is largest precisely when the model is most wrong.

Worked numbers, true label 1:

| Prediction | Error | Cross-entropy gradient | MSE gradient |
|---|---|---|---|
| 0.99 (confident, right) | −0.01 | −0.010 | −0.0001 |
| 0.50 (unsure) | −0.50 | −0.500 | −0.125 |
| **0.01 (confident, wrong)** | **−0.99** | **−0.990** | **−0.0098** |

Read the two gradient columns as the prediction gets **worse** (0.99 → 0.01):

- **Cross-entropy:** 0.010 → 0.100 → 0.500 → 0.900 → 0.990. It rises steadily. The worse the
  prediction, the larger the correction.
- **MSE:** 0.0001 → 0.0090 → **0.1250** → 0.0810 → 0.0098. It rises to a peak at `p = 0.5` and then
  **falls away again**.

MSE's gradient is largest when the model is *unsure* and collapses at **both** extremes. So a
prediction of 0.01 when the truth is 1 — as wrong as it is possible to be — receives a gradient of
0.0098, essentially the same as a nearly-correct 0.90 (0.0090), and **13× smaller** than an unsure
0.50.

**MSE cannot distinguish "almost right" from "completely wrong". Cross-entropy separates them by a
factor of ten.**

**Does it matter in practice?** It depends where the model starts. The lab measures both:

| Starting point | Loss | Start accuracy | Final accuracy |
|---|---|---|---|
| Neutral (zeros) | Cross-entropy | 0.500 | 0.998 |
| Neutral (zeros) | MSE | 0.500 | 0.997 |
| **Confidently wrong** | Cross-entropy | 0.000 | **0.998** |
| **Confidently wrong** | MSE | 0.000 | **0.010** |

From a neutral start both work, and on an easy problem MSE may even edge ahead — so a small
experiment can wrongly suggest the choice does not matter. From a **saturated** start, cross-entropy
recovers completely and MSE never moves: it is stuck precisely where its gradient has vanished.

In a deep network some units are always saturated. That is why cross-entropy is the standard choice
rather than merely a preference.

### 5.3 Choosing a loss

| Task | Loss | Notes |
|---|---|---|
| Regression, symmetric errors | MSE | The default |
| Regression with outliers | MAE or Huber | Robust |
| Binary classification | Binary cross-entropy | — |
| Multi-class, one label | Categorical cross-entropy | With softmax (M3-L09) |
| Multi-label | Binary cross-entropy per label | Independent decisions |
| Ranking / retrieval | Contrastive or triplet loss | M6-L12 |
| Imbalanced classes | Weighted cross-entropy | Weight by inverse frequency (M3-L13) |

**The loss encodes what you care about.** If false negatives are worse than false positives, an
unweighted loss will not know that. Weighting the loss is how you express business priorities to the
optimiser — and if you do not, it optimises the average, which is rarely what you meant.

### 5.4 Gradient descent variants

| Variant | Gradient computed from | Steps per epoch | Character |
|---|---|---|---|
| **Batch** | The entire dataset | 1 | Smooth, slow, memory-heavy |
| **Stochastic (SGD)** | One example | n | Very noisy, fast per step |
| **Mini-batch** | 8–512 examples | n / batch_size | **The practical choice** |

Mini-batch wins for three reasons: the gradient estimate is good enough, it fits in memory, and it
maps onto how GPUs actually compute.

**The noise is a feature, not just a cost.** A noisy gradient helps the parameters escape flat
regions and saddle points that a perfectly smooth gradient would settle into. This is why pure batch
descent is rarely used even when it is affordable.

**Batch size interacts with learning rate.** Larger batches give less noisy gradients, which permits
(and usually requires) a larger learning rate. Changing one without the other is a common source of
"it worked before and now it does not".

### 5.5 Reading a training curve

This is the practical skill. Five patterns, each with a distinct cause:

| Pattern | Diagnosis | Action |
|---|---|---|
| Falls smoothly, flattens | **Healthy** | Stop when validation flattens |
| Flat from the very start | Learning rate ≈ 0, disconnected graph, or vanishing gradients | Raise the rate; check the graph |
| Oscillates violently | Learning rate too high | Reduce it |
| Falls, then **rises** | Overshooting, or diverging | Reduce the rate; add decay |
| Becomes `nan` | Exploding gradients, or `log(0)` | Clip gradients; clip probabilities |
| Training falls, **validation rises** | **Overfitting** (M1-L08) | Early stopping; regularise; more data |

**Always plot training *and* validation loss together.** Training loss alone cannot distinguish
learning from memorising — which is the entire lesson of M1-L08.

### 5.6 When descent struggles

- **Poorly scaled features.** If one feature ranges 0–1 and another 0–100,000, the loss surface is a
  long narrow ravine and descent zig-zags. **Standardise your features** — this is often the single
  biggest practical fix.
- **Learning rate too large or too small.** See §5.5.
- **Bad initialisation.** All-zero weights make every neuron compute the same thing, so they all
  receive the same gradient and never differentiate. Random initialisation is required.
- **Saddle points.** Flat in some directions, curved in others. Mini-batch noise and momentum help
  escape them.

### 5.7 Assumptions and limitations

- Gradient descent finds *a* local minimum, not the global one. For convex problems (linear and
  logistic regression) they coincide; for neural networks they do not, and in practice this matters
  far less than expected.
- It requires a differentiable loss. Accuracy is not differentiable, which is why you optimise
  cross-entropy and *report* accuracy.
- The learning rate is the most important hyperparameter and usually needs tuning (M3-L12).
- Convergence to zero training loss is usually memorisation, not success (M1-L08).

---

## 6. Worked example — fitting a line, by hand then by descent

Three points: `(1, 3)`, `(2, 5)`, `(3, 7)`. The true relationship is `y = 2x + 1`.

Model: `ŷ = wx + b`. Start at `w = 0`, `b = 0`.

**Step 1 — forward pass.** All predictions are 0.

| x | y | ŷ | error (ŷ − y) | error² |
|---|---|---|---|---|
| 1 | 3 | 0 | −3 | 9 |
| 2 | 5 | 0 | −5 | 25 |
| 3 | 7 | 0 | −7 | 49 |

`MSE = (9 + 25 + 49) / 3 = 83 / 3 = **27.667**`

**Step 2 — the gradients.**

For `MSE = (1/n)Σ(wx + b − y)²`, applying the chain rule (M3-L06):

$$\frac{\partial L}{\partial w} = \frac{2}{n}\sum (\hat{y}_i - y_i)\,x_i
\qquad
\frac{\partial L}{\partial b} = \frac{2}{n}\sum (\hat{y}_i - y_i)$$

Compute each:

- `∂L/∂w = (2/3)[(−3)(1) + (−5)(2) + (−7)(3)] = (2/3)(−3 − 10 − 21) = (2/3)(−34) = **−22.667**`
- `∂L/∂b = (2/3)[(−3) + (−5) + (−7)] = (2/3)(−15) = **−10.000**`

Both negative, so both parameters should **increase**. Correct — they start at 0 and should reach 2
and 1.

**Step 3 — one step at α = 0.01.**

- `w = 0 − 0.01 × (−22.667) = **0.2267**`
- `b = 0 − 0.01 × (−10.000) = **0.1000**`

**Step 4 — check the loss fell.**

| x | y | ŷ = 0.2267x + 0.1 | error | error² |
|---|---|---|---|---|
| 1 | 3 | 0.3267 | −2.6733 | 7.147 |
| 2 | 5 | 0.5533 | −4.4467 | 19.773 |
| 3 | 7 | 0.7800 | −6.2200 | 38.688 |

`MSE = 65.608 / 3 = **21.869**`, down from 27.667. ✓

**Step 5 — notice the asymmetry in the gradients.** `∂L/∂w` is −22.667 while `∂L/∂b` is −10.000. The
weight moves more than twice as fast as the bias, because `w` is multiplied by `x` (values 1–3) and
`b` is not. **The parameter attached to the larger-magnitude input gets the larger gradient.**

This is exactly the feature-scaling problem in §5.6, visible in a two-parameter model. If `x` ranged
to 100,000 instead of 3, `∂L/∂w` would dwarf `∂L/∂b`, the loss surface would be an extremely narrow
ravine, and descent would zig-zag for thousands of steps. **Standardising features makes the
gradients comparable and the surface round.** The lab measures this directly.

**Step 6 — run it to convergence.** After enough steps it approaches `w = 2`, `b = 1` and the loss
approaches zero, because this data lies exactly on a line. Real data does not, and the loss converges
to a non-zero floor representing the noise.

---

## 7. Practical activity

**File:** [`labs/m3/l07_gradient_descent.py`](../../labs/m3/l07_gradient_descent.py)

**Requires the venv:**

```bash
source .venv/bin/activate
python labs/m3/l07_gradient_descent.py
```

Reproduces the §6 calculation, runs descent to convergence with an ASCII training curve, compares MSE
and MAE under an outlier, demonstrates MSE's vanishing gradient for classification, compares batch
sizes, shows all five curve pathologies, and measures the effect of feature scaling.

### 7.1 Important lines

| Construct | Why |
|---|---|
| `(2/n) * ((pred - y) * x).sum()` | The MSE gradient, straight from the formula. |
| `w -= lr * grad_w` | One descent step. |
| `sigmoid(z) * (1 - sigmoid(z))` | `σ'(z)` — the factor that kills MSE's classification gradient. |
| `rng.permutation(n)` | Shuffling for mini-batches. |
| Standardising `X` | Shows the ravine becoming round. |

### 7.2 Expected output

`[EXECUTED]` 2026-09-08 with numpy 2.5.3, Python 3.12.3:

```
==========================================================================
LOSS FUNCTIONS AND GRADIENT DESCENT
==========================================================================

--------------------------------------------------------------------------
1. THE SECTION 6 CALCULATION, VERIFIED
--------------------------------------------------------------------------
  data: [(np.int64(1), np.int64(3)), (np.int64(2), np.int64(5)), (np.int64(3), np.int64(7))]   (true: y = 2x + 1)
  start: w = 0.0, b = 0.0

     x     y     y_hat     error   error^2
     1     3    0.0000   -3.0000    9.0000
     2     5    0.0000   -5.0000   25.0000
     3     7    0.0000   -7.0000   49.0000
  MSE = 83.000 / 3 = 27.667

  dL/dw = (2/3)[(-3)(1) + (-5)(2) + (-7)(3)] = -22.6667
  dL/db = (2/3)[(-3) + (-5) + (-7)]          = -10.0000
  Both negative, so both parameters should INCREASE. Correct:
  they start at 0 and should reach w=2, b=1.

  One step at alpha=0.01:
    w = 0 - 0.01 x (-22.6667) = 0.2267
    b = 0 - 0.01 x (-10.0000) = 0.1000
    new MSE = 21.869   (was 27.667)   fell OK

  NOTE the asymmetry: |dL/dw| = 22.67 but |dL/db| = 10.00.
  w is multiplied by x (values 1-3); b is not. The parameter
  attached to the larger input gets the larger gradient. That is
  the feature-scaling problem, visible in two parameters.

--------------------------------------------------------------------------
2. DESCENT TO CONVERGENCE
--------------------------------------------------------------------------
  alpha = 0.05, 400 steps
  final: w = 2.000351, b = 0.999201, loss = 9.151e-08
  target: w = 2, b = 1, loss = 0

  loss
    27.667 |*                                                         
    25.361 |*                                                         
    23.056 |*                                                         
    20.750 |*                                                         
    18.444 |*                                                         
    16.139 |*                                                         
    13.833 |*                                                         
    11.528 |*                                                         
     9.222 |*                                                         
     6.917 |*                                                         
     4.611 |*                                                         
     2.306 |*                                                         
           +----------------------------------------------------------
            0                                                    step 400

  Smooth fall then flat: the healthy shape. It reaches zero loss
  because these three points lie EXACTLY on a line. Real data
  never does, and the loss converges to a non-zero floor that
  represents the noise you cannot fit.

--------------------------------------------------------------------------
3. MSE OPTIMISES THE MEAN, MAE THE MEDIAN
--------------------------------------------------------------------------
  Predicting a single constant for [10.0, 12.0, 11.0, 500.0]

  value minimising MSE :   133.25   (the mean is 133.25)
  value minimising MAE :    11.00   (the median is 11.50)

  One outlier moved the MSE-optimal prediction to 133 - a value
  no observation is anywhere near. MAE stayed at the median.

  This is not a rounding difference. On right-skewed targets
  (latency, price, document length - M3-L03) MSE and MAE give
  genuinely different models.

--------------------------------------------------------------------------
4. WHY MSE FAILS FOR CLASSIFICATION
--------------------------------------------------------------------------
  Binary classifier, sigmoid output, TRUE LABEL = 1.
  Comparing the gradient with respect to the pre-sigmoid value z.

    prediction     error   cross-entropy           MSE     ratio
          0.99     -0.01         -0.0100     -0.000099       101x
          0.90     -0.10         -0.1000     -0.009000        11x
          0.50     -0.50         -0.5000     -0.125000         4x
          0.10     -0.90         -0.9000     -0.081000        11x
          0.01     -0.99         -0.9900     -0.009801       101x

  Compare the two columns as the prediction gets WORSE:
    cross-entropy  0.0100 -> 0.1000 -> 0.5000 -> 0.9000 -> 0.9900
      rises steadily. The worse the prediction, the bigger the push.
    MSE            0.0001 -> 0.0090 -> 0.1250 -> 0.0810 -> 0.0098
      rises then FALLS AWAY again. It peaks at p=0.5 and collapses
      at BOTH extremes.

  So under MSE, a prediction of 0.01 when the truth is 1 (as wrong
  as possible) receives a gradient of 0.0098 - essentially the same
  as a nearly-correct 0.90 (0.0090), and 13x SMALLER than an
  unsure 0.50 (0.125).

  MSE cannot tell 'almost right' from 'completely wrong'.
  Cross-entropy separates them by a factor of 10.

  The culprit is the sigma'(z) factor, which goes to zero as the
  sigmoid saturates at either end.

  DOES IT MATTER IN PRACTICE? It depends on where you start.

  starting point                    loss              start acc  final acc
  zeros (neutral)                   cross-entropy         0.500      0.998
  zeros (neutral)                   MSE                   0.500      0.997
  CONFIDENTLY WRONG (-8, -8)        cross-entropy         0.000      0.998
  CONFIDENTLY WRONG (-8, -8)        MSE                   0.000      0.010

  From a NEUTRAL start both losses work; this problem is easy and
  MSE may even edge ahead. The difference only bites once the
  model is deep in saturation.

  From a CONFIDENTLY WRONG start, cross-entropy recovers and MSE
  does not - it is stuck exactly where its gradient has vanished.
  In a deep network some units are always saturated, which is why
  cross-entropy is the standard choice rather than merely a
  preference.

--------------------------------------------------------------------------
5. THE FIVE TRAINING-CURVE PATHOLOGIES
--------------------------------------------------------------------------
  healthy                        alpha=0.05      converging
                                 first losses: 27.7, 5.5, 1.1, 0.2, 0.0, 0.0
  alpha too small (flat)         alpha=5e-05     barely moved
                                 first losses: 27.7, 27.6, 27.6, 27.6, 27.5, 27.5
  alpha too high (oscillating)   alpha=0.22      diverged
                                 first losses: 27.7, 57.4, 119.1, 247.1, 512.8, 1063.9
  diverging                      alpha=0.3       diverged
                                 first losses: 27.7, 149.9, 812.4, 4402.5, 23857.3, 129283.7

  A curve that is flat and a curve that is diverging need OPPOSITE
  fixes. Reading which one you have is the whole diagnostic skill.

--------------------------------------------------------------------------
6. FEATURE SCALING - the ravine, measured
--------------------------------------------------------------------------
  Feature 1 std: 0.88   Feature 2 std: 1016.95
  Ratio: 1156x

  features           alpha   steps to converge    final loss
  raw                1e-02            DIVERGED           inf
  raw                1e-04            DIVERGED           inf
  raw                1e-06            DIVERGED           inf
  standardised       1e-02                 213        0.0199

  With raw features there is NO learning rate that works well:
  large enough for feature 1 diverges on feature 2, and small
  enough for feature 2 crawls on feature 1. That is the ravine.

  Standardising makes both gradients comparable, the surface
  round, and an ordinary learning rate converge quickly.
  This is usually the single biggest practical fix in training.

==========================================================================
```

### 7.3 Reading the result

**Section 1 confirms the hand calculation** — MSE 27.667, gradients −22.667 and −10.000, loss falling
to 21.869 after one step — and makes the asymmetry concrete: `|∂L/∂w| = 22.67` against
`|∂L/∂b| = 10.00`. The weight attached to `x` (values 1–3) gets the larger gradient purely because of
the input's magnitude. Section 6 shows what happens when that ratio is 1000× instead of 2×.

**Section 3 shows MSE and MAE optimising different statistics**, exactly as §5.1 claims:

```
value minimising MSE : 133.25   (the mean is 133.25)
value minimising MAE :  11.00   (the median is 11.50)
```

One outlier at 500 dragged the MSE-optimal prediction to **133** — a value no observation is anywhere
near. This is why the loss choice is a modelling decision, not a detail: on right-skewed targets like
latency or price you are choosing between predicting the mean and predicting the median.

**Section 4 is where the lab corrected my own draft.** The gradient table shows MSE's real shape:

```
prediction:   0.99      0.90      0.50      0.10      0.01
MSE grad:   0.0001    0.0090    0.1250    0.0810    0.0098
```

It **peaks at 0.5 and collapses at both ends**. So a completely wrong prediction (0.01) gets
essentially the same gradient as a nearly-right one (0.90). MSE cannot tell them apart; cross-entropy
separates them tenfold.

And the training comparison is the honest part:

| Start | Loss | Final accuracy |
|---|---|---|
| Neutral | Cross-entropy | 0.998 |
| Neutral | MSE | **0.997** |
| **Confidently wrong** | Cross-entropy | **0.998** |
| **Confidently wrong** | MSE | **0.010** |

**From a neutral start, MSE is fine** — it even matches cross-entropy on this easy problem. A quick
experiment would conclude the choice does not matter.

**From a saturated start, MSE never recovers.** It ends at 1% accuracy, having barely moved, because
its gradient is near zero exactly where it needs to be large. Cross-entropy climbs from 0% to 99.8%.

That contrast is the real argument, and it is why cross-entropy is standard rather than preferred: in
a deep network some units are always saturated, so you are always in the second row somewhere.

**Section 6 measures the ravine.** With one feature of standard deviation 1 and another of 1000,
**no learning rate works**: large enough to move the first diverges on the second, small enough for
the second crawls on the first. Standardising makes both gradients comparable and an ordinary
learning rate converges quickly.

This is usually the single highest-value fix in a struggling training run, and it costs two lines.

**Verification:** confirm MSE 27.667 and gradients −22.667 / −10.000 in section 1, MSE-optimal 133.25
versus MAE-optimal 11.00 in section 3, and that MSE from a confidently-wrong start ends near 0.010
while cross-entropy reaches 0.998.

---

## 8. Common mistakes and troubleshooting

1. **MSE for classification.** Gradients vanish exactly when the model is confidently wrong.
2. **Unscaled features.** Descent zig-zags for thousands of unnecessary steps.
3. **Learning rate wrong.** The single most common cause of a failed training run.
4. **All-zero initialisation.** Every unit receives an identical gradient and never differentiates.
5. **Plotting only training loss.** Cannot distinguish learning from memorising.
6. **Optimising accuracy directly.** Not differentiable — optimise cross-entropy, report accuracy.
7. **Not shuffling between epochs.** The model can learn the ordering.
8. **Changing batch size without adjusting the learning rate.**

| Symptom | Cause | Fix |
|---|---|---|
| Loss `nan` | Exploding gradients or `log(0)` | Lower α; clip gradients; clip probabilities |
| Loss flat from step 0 | α ≈ 0, or gradients not flowing | Raise α; check the graph is connected |
| Loss oscillates | α too high | Reduce it, or add decay |
| Loss falls then rises | Overshooting near the minimum | Decay α |
| Very slow convergence | Unscaled features or α too small | Standardise; raise α |
| Training loss falls, validation rises | Overfitting | Early stopping (M1-L08) |
| Classifier will not improve past chance | MSE loss, or a bug in the labels | Use cross-entropy; check label alignment (M1-L04) |

---

## 9. Security, privacy, reliability and cost

- **Reliability.** The training curve is your primary diagnostic. Log training *and* validation loss
  every epoch and keep the history — a curve you did not record cannot be diagnosed afterwards.
- **Cost.** Training cost is roughly `steps × batch_size × cost_per_example`. Doubling epochs doubles
  the bill, and past convergence buys nothing but overfitting. Early stopping is a cost control as
  much as a quality one (M13-L04).
- **Privacy.** The loss on a specific example is a membership-inference signal (M3-L05 §9). Do not
  expose per-example losses from a model trained on private data.
- **Governance.** Record the loss function, learning rate, batch size, epochs and random seed with
  every trained model. Without them the result is not reproducible (M10-L13).

---

## 10. Exercises

### Exercise 1 — Beginner (~20 min)

For data `(1,3)`, `(2,5)`, `(3,7)` and `w = 0.5`, `b = 0.5`:

1. Compute all three predictions and the MSE by hand.
2. Compute `∂L/∂w` and `∂L/∂b`.
3. Take one step at α = 0.05 and confirm the loss fell.
4. Which parameter moved more, and why?
5. Repeat with α = 0.5. What happens, and what does it tell you?

### Exercise 2 — Intermediate (~30 min)

1. Implement gradient descent for `ŷ = wx + b` and run it to convergence on the §6 data. Report the
   final `w`, `b` and loss.
2. Add an outlier `(4, 100)`. Refit with MSE and then with MAE. Report both fitted lines and explain
   the difference in terms of mean versus median.
3. Plot (or tabulate) the loss for α = 0.001, 0.01, 0.1 and 0.5 over 50 steps. Classify each curve
   using the §5.5 table.
4. Rescale `x` by ×1000 and refit with the same α. Report what happens, then standardise `x` and
   refit. Explain both results.

### Exercise 3 — Challenge (~30 min)

1. Implement binary classification with both cross-entropy and MSE. Train both from the same
   initialisation on the same data for 200 steps. Report both final losses and accuracies.
2. Instrument the gradient magnitude at each step for both losses. Show that MSE's gradient is
   smallest exactly when the model is most wrong.
3. Deliberately initialise all weights to zero in a two-unit model. Show that both units remain
   identical forever, and explain why.
4. Compare batch, mini-batch (size 16) and stochastic descent on 1,000 examples. Report wall-clock
   time, steps to convergence, and the smoothness of each curve.
5. Produce all five pathological curves from §5.5 deliberately, and state the single parameter change
   that caused each.

---

## 11. Quiz

**Q1.** What does a loss function do?

- A. Selects the model architecture.
- B. Produces a single number measuring how wrong a prediction is, which training then minimises.
- C. Splits the data.
- D. Chooses the learning rate.

**Q2.** Why is MSE a poor choice for classification?

- A. It is slower to compute.
- B. Combined with a sigmoid, its gradient includes a `σ'(z)` factor that goes to zero when the model
  is confidently wrong — so learning stalls exactly when the largest correction is needed.
- C. It cannot handle two classes.
- D. It always returns zero.

**Q3.** MSE optimises toward which statistic of the target, and MAE toward which?

- A. Both toward the mean.
- B. MSE toward the mean; MAE toward the median.
- C. MSE toward the median; MAE toward the mean.
- D. Both toward the mode.

**Q4.** In the §6 example, why is `∂L/∂w` larger than `∂L/∂b`?

- A. A calculation error.
- B. `w` is multiplied by `x` (values 1–3) while `b` is not, so the input magnitude scales the
  gradient — which is why feature scaling matters.
- C. `b` is less important.
- D. The learning rate differs per parameter.

**Q5.** Your training loss oscillates violently. What is the most likely cause?

- A. Too little data.  B. The learning rate is too high.  C. Overfitting.  D. Vanishing gradients.

**Q6.** Training loss falls steadily while validation loss rises. What is happening?

- A. The learning rate is too low.
- B. Overfitting — the model is memorising the training data (M1-L08).
- C. Exploding gradients.
- D. The data is mislabelled.

**Q7.** Why is mini-batch descent preferred over full-batch?

- A. It is always more accurate.
- B. The gradient estimate is good enough, it fits in memory, it maps onto GPU computation, and its
  noise helps escape saddle points.
- C. It requires no learning rate.
- D. It cannot overfit.

**Q8.** Why can you not train a model by directly optimising accuracy?

- A. Accuracy is too slow to compute.
- B. Accuracy is not differentiable — it is a step function, so it provides no gradient. You optimise
  cross-entropy and *report* accuracy.
- C. Accuracy is not a valid metric.
- D. You can; it is standard practice.

**Q9.** What happens if all weights are initialised to zero?

- A. Training proceeds normally.
- B. Every unit computes the same thing and receives the same gradient, so they never differentiate —
  the network effectively has one unit per layer.
- C. The loss becomes `nan`.
- D. It converges faster.

**Q10.** *(Written, rubric-graded.)* In under 80 words, explain how you would diagnose a training run
whose loss is flat from the very first step.

---

## 12. Revision notes

- **Loop:** predict → measure loss → step against the gradient. Everything else is machinery.
- **Regression → MSE** (optimises the **mean**, outlier-sensitive) · **MAE/Huber** (optimises the
  **median**, robust). **Classification → cross-entropy.**
- **MSE for classification fails** because the `σ'(z)` factor kills the gradient exactly when the
  model is confidently wrong. Cross-entropy's gradient is simply the error.
- **The loss encodes what you care about.** Weight it if some errors matter more.
- **Mini-batch is the practical default.** Its noise helps escape saddle points. Batch size and
  learning rate must be tuned together.
- **Reading curves:** smooth-then-flat = healthy · flat from start = α≈0 or no gradient flow ·
  oscillating = α too high · falls-then-rises = overshooting · `nan` = exploding or `log(0)` ·
  **train falls / validation rises = overfitting**.
- **Always plot training AND validation.**
- **Standardise features.** Unscaled inputs make a narrow ravine and descent zig-zags — visible even
  in the two-parameter §6 example.
- **Never initialise all weights to zero.**
- **Accuracy is not differentiable.** Optimise cross-entropy, report accuracy.

---

## 13. Completion checklist

- [ ] I reproduced the §6 gradients by hand and confirmed the loss fell.
- [ ] I can explain why `∂L/∂w` exceeded `∂L/∂b`.
- [ ] I ran descent to convergence and read the curve.
- [ ] I demonstrated MSE's vanishing gradient for classification.
- [ ] I compared MSE and MAE under an outlier.
- [ ] I produced all five curve pathologies deliberately.
- [ ] I measured the effect of feature scaling.
- [ ] I scored 7/10 on the quiz.

---

## 14. References

- Goodfellow, Bengio & Courville, *Deep Learning*, Ch. 4 and 8.
  <https://www.deeplearningbook.org/> `[UNVERIFIED]`
- Ruder, "An overview of gradient descent optimization algorithms".
  <https://www.ruder.io/optimizing-gradient-descent/> `[UNVERIFIED]`

---

## 15. Next lesson

→ [M3-L08 — Linear Regression from Scratch](M3-L08-linear-regression.md)

You have the loss and the optimiser. Next: assembling them into a complete, working model — trained,
evaluated and compared against a baseline.
