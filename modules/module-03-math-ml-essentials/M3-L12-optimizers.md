# M3-L12 — Learning Rate, Epochs, Batches and Optimizers

| | |
|---|---|
| **Lesson ID** | M3-L12 |
| **Difficulty** | 2 (Intermediate) |
| **Estimated study time** | 2 hours |
| **Prerequisites** | [M3-L07](M3-L07-loss-gradient-descent.md), [M3-L11](M3-L11-backpropagation.md) |

---

## 1. Learning objectives

1. **Define** epoch, batch, step and iteration precisely, and convert between them.
2. **Explain** the learning rate's effect and diagnose a bad one from a loss curve.
3. **Compare** full-batch, stochastic and mini-batch gradient descent on cost and stability.
4. **Explain** momentum, RMSProp and Adam in terms of what each fixes.
5. **Choose** sensible starting hyperparameters and justify them.
6. **Recognise** which of these settings still matter when you are only calling an LLM API.

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **Epoch** | One complete pass over the training set. |
| **Batch (mini-batch)** | The subset of examples used to compute one gradient. |
| **Step / iteration** | One parameter update. `steps_per_epoch = ceil(n / batch_size)`. |
| **Learning rate** (α, `lr`) | The multiplier on the gradient when stepping. |
| **Schedule** | A rule that changes the learning rate over training. |
| **Warmup** | Starting at a tiny learning rate and ramping up. |
| **Momentum** | An exponentially decayed running average of past gradients. |
| **Adam** | Adaptive Moment Estimation — per-parameter learning rates. |
| **Weight decay** | Shrinking weights each step; regularisation (M3-L08). |
| **Gradient clipping** | Capping the gradient norm before stepping. |
| **Convergence** | The loss stops improving meaningfully. |
| **Divergence** | The loss increases without bound, usually to `nan`. |

---

## 3. Plain-language explanation

M3-L07 gave you the update rule:

```
new_parameter = old_parameter − learning_rate × gradient
```

Backprop (M3-L11) supplies the gradient. **This lesson is about everything else in that line.**

**Three questions, three answers:**

1. **How big a step?** → the learning rate. Too small and training takes forever; too large and it
   diverges. This is the single most important hyperparameter, by a wide margin.
2. **How much data per step?** → the batch size. All of it is accurate but slow; one example is fast
   but noisy; a few dozen to a few hundred is the practical compromise.
3. **How to use the *history* of gradients?** → the optimizer. Plain SGD forgets each gradient
   immediately. Momentum and Adam remember, and that memory is worth a lot.

**A quick note on why this matters to you.** You are not going to train a foundation model. But you
*will* fine-tune small models (M13), and — more immediately — these ideas explain a great deal of
what you will read in model cards, training logs and papers. "We used AdamW with a cosine schedule,
2,000 warmup steps and a peak LR of 3e-4" is a sentence you should be able to read completely by the
end of this lesson.

---

## 4. Analogy

**Descending a hill in fog** (M3-L07's analogy), now with the details filled in:

| Concept | In the analogy |
|---|---|
| Learning rate | Your stride length |
| Batch size | How many compass readings you average before stepping |
| Momentum | Continuing to roll in the direction you were already heading |
| Adam | Taking shorter strides on scree, longer on firm ground |
| Schedule | Long strides at the top, careful shuffles near the bottom |
| Warmup | Testing your footing before committing to full strides |

### Where the analogy breaks

1. **The hill has thousands of dimensions**, not two. Intuitions about local minima largely fail:
   in high dimensions, saddle points vastly outnumber local minima, and true local minima are rare.
2. **The terrain changes as you use different data.** Each mini-batch is a slightly different hill.
3. **You cannot see the ground truth.** The training loss is not the thing you care about
   (M3-L08) — a route to the lowest training loss can be the wrong route.
4. **Speed is not the goal.** Slower descent that generalises better is a *win*, which makes no
   sense for someone descending a real hill.

---

## 5. Detailed technical explanation

### 5.1 Epochs, batches and steps

With `n = 50,000` examples and `batch_size = 64`:

```
steps_per_epoch = ceil(50000 / 64) = 782
10 epochs       = 7,820 steps
```

**Steps, not epochs, are what actually drive learning.** Halving the batch size doubles the steps per
epoch, so "10 epochs" means twice as much updating. When comparing runs, compare steps.

**Modern LLM pretraining does not use epochs at all** — the corpus is so large that models see most
data once. You will see "trained on 2T tokens", never "trained for 3 epochs".

### 5.2 The learning rate

| Learning rate | Symptom |
|---|---|
| Far too large | Loss becomes `nan` or `inf` within a few steps |
| Too large | Loss oscillates or plateaus high; may spike |
| Slightly too large | Loss falls then flattens above where it should |
| Good | Smooth, fast decrease, then a gentle plateau |
| Too small | Smooth but very slow; still improving when you stop |

**Diagnosis is visual.** Plot the loss. The shapes are distinctive enough that you will identify a bad
learning rate in seconds once you have seen each one.

**Finding one — the LR range test:** train for a few hundred steps while increasing the learning rate
exponentially, and plot loss against LR. Pick roughly one order of magnitude below where the loss
starts rising. The lab implements this.

**Reasonable defaults `[STABLE]`:**

| Setting | Typical starting LR |
|---|---|
| SGD, small network | 0.01 – 0.1 |
| Adam, small network | 1e-3 |
| Adam, transformer pretraining | 1e-4 – 3e-4 |
| **Fine-tuning a pretrained model** | **1e-5 – 5e-5** |
| LoRA (M13-L06) | 1e-4 – 3e-4 |

**Note how much smaller fine-tuning rates are.** The model is already good; you are nudging it. A
pretraining learning rate applied to a fine-tune will destroy the pretrained behaviour — this is the
most common fine-tuning mistake, and M13 returns to it.

### 5.3 Batch size

| Batch size | Gradient quality | Speed per epoch | Notes |
|---|---|---|---|
| Full dataset | Exact | Slowest | Rarely fits in memory |
| 32 – 512 | Good estimate | Fast | The practical range |
| 1 (SGD) | Very noisy | Slow per epoch | Poor hardware utilisation |

The gradient's standard error falls as `1/√batch_size` (M3-L03 §5.5). **Quadrupling the batch halves
the noise** — diminishing returns, and the extra memory usually buys less than a larger learning rate
would.

**Some noise is beneficial.** It acts as regularisation, helping escape sharp minima. Very large
batches often generalise slightly *worse* unless the learning rate is scaled up to compensate — the
common heuristic is the **linear scaling rule**: multiply the LR by the same factor as the batch size,
with warmup. `[UNVERIFIED — from the literature; not measured in this course]`

**Gradient accumulation** simulates a large batch on small hardware: run `k` mini-batches, sum the
gradients, step once. Mathematically near-identical to a `k×` larger batch, at `k×` the time.

### 5.4 Momentum

Plain SGD has no memory. In a narrow valley it oscillates across the walls while creeping slowly
along the floor.

```python
velocity = beta * velocity + grad          # beta ~ 0.9
param   -= lr * velocity
```

The oscillating components alternate sign and cancel in the running average; the consistent downhill
component accumulates. **Momentum damps the oscillation and accelerates the useful direction.**

`beta = 0.9` averages roughly the last `1/(1−0.9) = 10` gradients.

### 5.5 Adam

Two ideas combined:

1. **Momentum** (first moment): a running average of the gradient.
2. **RMSProp** (second moment): a running average of the gradient *squared*, used to give each
   parameter its own effective learning rate.

```python
m = b1 * m + (1 - b1) * grad               # b1 = 0.9
v = b2 * v + (1 - b2) * grad**2            # b2 = 0.999
m_hat = m / (1 - b1**t)                    # bias correction
v_hat = v / (1 - b2**t)
param -= lr * m_hat / (np.sqrt(v_hat) + 1e-8)
```

**Why the second moment helps:** dividing by `√v` means a parameter with consistently large gradients
takes proportionally smaller steps, and one with small gradients takes larger ones. Parameters at very
different scales — which is normal in a deep network — all progress at a reasonable rate. This is why
Adam is far less sensitive to the learning rate than SGD, and why it is the default.

**Why bias correction:** `m` and `v` start at zero, so early estimates are biased toward zero. Dividing
by `(1 − β^t)` corrects this; the correction vanishes as `t` grows. Without it, the first steps are
much too small — the lab measures exactly how much.

**AdamW** is Adam with weight decay applied directly to the parameter rather than folded into the
gradient. It is the correct version and the current default for transformers.

**Cost:** Adam stores `m` and `v` per parameter — **2 extra copies**. With float32 parameters and
gradients too, training memory is roughly **4× the parameter memory** before activations. This is why
M3-L10's 8B-parameter model needed ~128 GB to train but 32 GB to serve.

### 5.6 Schedules

| Schedule | Behaviour | Used for |
|---|---|---|
| Constant | Never changes | Simple problems |
| Step decay | ×0.1 at fixed milestones | Classic vision training |
| **Cosine** | Smooth decay to ~0 | **The transformer default** |
| **Warmup + cosine** | Ramp up, then cosine down | **LLM pretraining and fine-tuning** |
| ReduceLROnPlateau | Cut when validation stalls | When you cannot plan the length |

**Why warmup?** At initialisation, Adam's `v` estimate is based on almost no data and is unreliable,
and the gradients themselves are large and uninformative. A large early step can push the model
somewhere it never recovers from. Warmup (typically 1–5% of total steps) avoids this.

**Why decay at the end?** Large steps near a minimum bounce around it. Decaying to near zero lets the
model settle. The cosine schedule's total step count is baked in, so stopping early leaves you at a
high learning rate and a worse model than the schedule promised.

**A caution the lab measures directly (§7.3):** on a short, easy problem a schedule may not lower the
final loss at all — the lab's constant LR beat cosine on final loss while cosine's last-50-step swing
was **30× smaller**. Schedules buy *stability*, and they pay off on long, hard, large-batch runs. Use
one because your run needs it, not because a paper used it.

### 5.7 Gradient clipping

```python
total_norm = np.sqrt(sum((g ** 2).sum() for g in grads))
if total_norm > max_norm:                  # max_norm typically 1.0
    grads = [g * (max_norm / total_norm) for g in grads]
```

Clip by **global norm**, not per-parameter — that preserves the gradient's *direction* and scales only
its magnitude. Nearly all LLM training uses it as a cheap insurance policy against a single bad batch
producing `nan`.

### 5.8 What survives into LLM work

You will not tune these when calling an API, but the concepts transfer directly:

- **Temperature** (M4-L14) is a different knob with the same character: one scalar, dramatic effect,
  found empirically.
- **Retry backoff** (M2-L14) is a schedule — increasing rather than decreasing.
- **Batch size** reappears as embedding batch size (M6) and as agent concurrency (M8).
- **Fine-tuning and LoRA** (M13) use every setting in this lesson directly.
- Reading a model card's training details is a routine part of evaluating whether a model suits your
  task.

### 5.9 Assumptions and limitations

- Defaults here are conventions, not laws. Always validate on your own data.
- Adam is not universally better; well-tuned SGD with momentum still wins on some vision tasks.
- These settings interact. Changing the batch size usually means changing the learning rate.
- No optimizer fixes a bad loss function, bad data, or a leak (M1-L09).

---

## 6. Worked example — one step, four optimizers

Two parameters. Gradient at this step: `g = [0.5, 0.02]`. Learning rate `α = 0.1`. This is the common
awkward case — one parameter with a large gradient, one with a small one.

**Plain SGD:**

```
Δ = −0.1 × [0.5, 0.02] = [−0.050, −0.002]
```

Parameter 2 moves **25× less**. If its gradient stays small it will take forever, and lowering α to
suit parameter 1 makes parameter 2 slower still. **This is the problem Adam solves.**

**Momentum (β = 0.9), with `v_prev = [0.4, 0.03]`:**

```
v = 0.9 × [0.4, 0.03] + [0.5, 0.02] = [0.860, 0.047]
Δ = −0.1 × [0.860, 0.047]           = [−0.0860, −0.0047]
```

Both moved further than plain SGD, because past gradients agreed with the current one. Momentum's step
can exceed `α × g` — that is the acceleration.

**Adam, step t = 1, from `m = v = 0`:**

```
m = 0.1 × [0.5, 0.02]     = [0.0500, 0.00200]
v = 0.001 × [0.25, 0.0004] = [0.000250, 0.0000004]

bias correction at t=1:  1 − 0.9¹ = 0.1     1 − 0.999¹ = 0.001
m̂ = [0.500, 0.0200]
v̂ = [0.250, 0.000400]

Δ = −0.1 × [0.500/(0.5+1e-8), 0.0200/(0.02+1e-8)]
  = −0.1 × [1.000, 1.000] = [−0.1000, −0.1000]
```

**Both parameters move by exactly the learning rate**, despite gradients differing 25-fold. On the
first step Adam's update is `±α` for every parameter, because `m̂/√v̂ = g/|g| = ±1`. Adam's step size
is set by the learning rate, not by the gradient's magnitude — and *that* is why Adam is so much less
sensitive to the learning rate than SGD.

**Adam without bias correction, same step:**

```
Δ = −0.1 × [0.0500/√0.000250, 0.00200/√0.0000004]
  = −0.1 × [0.0500/0.0158, 0.00200/0.000632]
  = −0.1 × [3.162, 3.162] = [−0.3162, −0.3162]
```

**3.16× too large** — not too small, as the naive intuition suggests. `m` is under-scaled by 10× and
`√v` by 31.6×, and the ratio `31.6/10 = 3.16` goes the wrong way. Bias correction fixes both at once.
The lab confirms this number.

---

## 7. Practical activity

**File:** [`labs/m3/l12_optimizers.py`](../../labs/m3/l12_optimizers.py)

```bash
source .venv/bin/activate
python labs/m3/l12_optimizers.py
```

Reproduces §6, runs an LR sweep to show every failure mode, compares batch sizes on gradient noise and
wall-clock, races SGD / momentum / Adam on a badly-scaled problem, measures bias correction's effect,
compares schedules, and shows clipping preventing `nan`.

### 7.2 Expected output

`[EXECUTED]` on Python 3.12.3, NumPy 2.5.3, 2026-09-08.

```text

========================================================================
1. ONE STEP, FOUR OPTIMIZERS  (g = [0.5, 0.02], lr = 0.1)
========================================================================
  SGD           delta = [-0.05  -0.002]
                ratio between the two = 25x  (same as the gradient ratio)

  Momentum      v     = [0.86  0.047]
                delta = [-0.086  -0.0047]
                |delta[0]| vs plain SGD: 1.72x larger

  Adam (t=1)    m     = [0.05  0.002]
                v     = [2.5e-04 4.0e-07]
                m_hat = [0.5  0.02]
                v_hat = [0.25   0.0004]
                delta = [-0.1 -0.1]
                BOTH parameters moved by exactly the learning rate (0.1), despite
                gradients differing 25x.

  Adam, NO bias correction:
                delta = [-0.316228 -0.316223]
                ratio to corrected = 3.1623x  -> TOO LARGE, not too small
                (m is under-scaled 10x, sqrt(v) 31.6x; 31.6/10 = 3.162)

========================================================================
2. LEARNING RATE SWEEP  (the M3-L11 network, 300 steps)
========================================================================
        lr   start loss   final loss    min loss   diagnosis
    0.0001       0.6586       0.6552      0.6552   FLAT AND HIGH (lr too low / stuck)
     0.001       0.6586       0.6271      0.6271   TOO SLOW (still falling at the end)
      0.01       0.6586       0.4710      0.4710   TOO SLOW (still falling at the end)
       0.1       0.6586       0.3190      0.3190   CONVERGED (good)
       1.0       0.6586       0.3087      0.3087   CONVERGED (good)
      10.0       0.6586       0.3923      0.3448   OSCILLATING (lr too high)
     100.0       0.6586       5.8592      0.6586   OSCILLATING (lr too high)

========================================================================
3. BATCH SIZE: GRADIENT NOISE AND WALL-CLOCK
========================================================================
     batch    grad norm sd   cosine to full   steps/epoch    ms/epoch
         1         0.49029           0.1974          4096        41.5
         8         0.17537           0.4577           512         5.5
        64         0.06058           0.8333            64         0.8
       512         0.02005           0.9763             8         0.3
      4096         0.00000           1.0000             1         0.3

  Noise falls as 1/sqrt(batch): quadrupling the batch should halve the sd.
  Batch 4096 is the full dataset, so its sd is exactly 0 (it IS the answer).

========================================================================
4. SGD vs MOMENTUM vs ADAM  (ill-conditioned bowl, curvature ratio 1000:1)
========================================================================
  optimizer         lr    steps to loss < 1e-6    final loss
  sgd           0.0019                   3,450     4.583e-34
  sgd           0.0021                DIVERGED     1.132e+12
  momentum      0.0005                   1,257     2.059e-92
  adam             0.1                     125     2.304e-07

  Adam is 28x fewer steps than the fastest
  STABLE SGD rate. SGD cannot simply use a larger rate: at lr = 0.021 it
  exceeds the stability limit 2/1000 = 0.002 and diverges. One learning
  rate must serve both directions, so it is capped by the STEEPEST one
  while the shallowest one crawls. Adam rescales each direction separately.

========================================================================
5. SCHEDULES  (300 steps, peak lr = 0.5)
========================================================================
  schedule                final loss    min loss   last-50 swing
  constant                    0.3123      0.3123         0.00091
  cosine                      0.3153      0.3153         0.00003
  warmup + cosine             0.3153      0.3153         0.00003

  LR profile for warmup + cosine (peak 0.5, 30 warmup steps of 300):
    step:       0      10      29      30      75     150     225     299
      lr:  0.0167  0.1833  0.5000  0.5000  0.4665  0.2934  0.0893  0.0000

========================================================================
6. GRADIENT CLIPPING  (one poisoned batch in an otherwise fine run)
========================================================================
  setting                       peak grad norm   MSE on clean rows  verdict
  no clipping                       4.096e+151                   nan  MODEL DESTROYED
    learned weights: [-1.97410359e+221  1.91968107e+221 -2.06369138e+221  1.82958873e+221]
  clip at global norm 1.0            6.243e+08                0.0156  usable model
    learned weights: [ 1.54  -2.032  0.535  2.963]

  true weights:      [ 1.5 -2.   0.5  3. ]

  One row out of 512 -- 0.2% of the data -- is enough to destroy the run
  without clipping. Clipping caps the damage that any single batch can do,
  which is why essentially all long training runs use it.

========================================================================
7. OPTIMIZER STATE MEMORY  (float32)
========================================================================
  optimizer        state copies    100k params      7B params    total w/ grads
  SGD                         0         0.0 MB         0.0 GB           52.2 GB
  Momentum                    1         0.4 MB        26.1 GB           78.2 GB
  Adam / AdamW                2         0.8 MB        52.2 GB          104.3 GB

  A 7B model needs ~26 GB to serve in float32 but ~104 GB to train with
  Adam, before activations. That gap is why 'it fits for inference' does
  not mean 'it fits for training'.

Done.
```

### 7.3 Reading the result

**Section 1 confirms §6 exactly**, including the bias-correction result: without it, Adam's first step
is **3.1623× too large**. Momentum's step is **1.72×** plain SGD's, because the stored velocity agreed
with the current gradient.

**Section 2 produces every failure mode from the §5.2 table on one problem.** At `lr = 1e-4` the loss
moves from 0.6586 to 0.6552 in 300 steps — flat. At 0.1 and 1.0 it converges to 0.319 and 0.309. At
10.0 it oscillates. At 100.0 the *final* loss is **5.86 — worse than the starting loss of 0.66**, and
its minimum over all 300 steps is 0.6586, meaning it never improved on step 0 even once. Note the
usable range spans **two orders of magnitude** here; that is typical, and it is why an LR sweep of six
values is a cheap and reliable procedure.

**Section 3 is the batch-size result, and one column deserves attention.** The `cosine to full` column
measures how well a mini-batch gradient's *direction* agrees with the true full-dataset gradient:

| Batch | Noise (sd) | Cosine to true gradient |
|---|---|---|
| 1 | 0.490 | **0.197** |
| 8 | 0.175 | 0.458 |
| 64 | 0.061 | 0.833 |
| 512 | 0.020 | 0.976 |
| 4096 (full) | 0.000 | 1.000 |

**A single-example gradient points in a direction only 0.197 cosine-similar to the true one** — barely
better than random, in the sense of M3-L02. It is *still* a descent direction on average, and SGD works
anyway; that is the surprising and important fact. The noise column follows `1/√batch` closely: 8× the
batch gives 0.490/0.175 = 2.80× less noise, against a predicted √8 = 2.83.

Wall-clock tells the other half of the story: batch 1 takes **41.1 ms/epoch**, batch 64 takes **0.8 ms**
— **50× faster** for a gradient that is *also* four times better aligned. Batch 1 is worse on both
axes. That is why nobody uses it.

**Section 4 is the clearest demonstration of what Adam actually buys.** On a bowl where one direction
is 1,000× steeper than the other:

| Optimizer | LR | Steps to loss < 1e-6 |
|---|---|---|
| SGD | 0.0019 | **3,450** |
| SGD | 0.0021 | **diverged** |
| Momentum | 0.0005 | 1,257 |
| **Adam** | 0.1 | **125** |

**Adam is 28× fewer steps than the fastest SGD rate that is stable at all.** And SGD cannot escape by
raising its rate: the stability limit is `2/curvature = 0.002`, and at 0.0021 — a 10% increase — it
diverges to 1.13e+12. A single learning rate must serve both directions, so it is **capped by the
steepest direction while the shallowest one crawls**. Adam's second moment rescales each direction
independently, which is exactly the constraint it removes. Real networks are far worse conditioned
than 1000:1, which is why Adam is the default.

**Section 5 did not go the way the schedule literature would suggest, and the honest result is more
instructive.** On this easy 300-step problem, the **constant** learning rate reached a *lower* final
loss (0.3123) than cosine (0.3153). What cosine bought was **stability**: the loss swing over the last
50 steps was **0.00003 versus 0.00091 — 30× smaller**. Warmup made no measurable difference at all
here.

That is the correct lesson. Schedules do not magically lower the loss; they stop the model bouncing
around the minimum, and they matter most on long, hard, large-batch runs where a bad early step is
unrecoverable — not on a 300-step run of a 2-feature problem. **Do not adopt warmup + cosine because a
paper used it; adopt it when your run is long enough for it to pay.** The LR profile printed underneath
confirms the schedule is implemented correctly: it ramps to exactly 0.5000 at step 29–30 and decays to
0.0000 at step 299.

**Section 6 shows why clipping is worth its trivial cost.** The dataset is 512 clean rows plus **one**
poisoned row (0.2% of the data) with features at 1e4 and a target of 1e6 — the sort of thing a broken
ETL job produces. That row lands in exactly one mini-batch:

- **Without clipping:** the peak gradient norm reaches **4.10e+151**, the weights reach **±2e+221**, and
  the loss is `nan`. The run is a total loss.
- **With clipping at global norm 1.0:** the same 6.24e+08 gradient is scaled down, and the model
  finishes at `[1.540, -2.032, 0.535, 2.963]` against true weights `[1.5, -2.0, 0.5, 3.0]` — MSE
  **0.0156** on the clean rows.

The clipped run did not merely survive; it learned essentially the right answer *despite* the poisoned
row. Clipping caps how much damage any single batch can do, and one bad row in five hundred is enough
to justify it.

**Section 7 quantifies §5.5's memory warning.** For a 7B-parameter model in float32: parameters and
gradients are 52.2 GB, and Adam's two moment buffers add another **52.2 GB**, for **104.3 GB before a
single activation is stored**. The same model serves in about 26 GB. **A model that fits comfortably
on your inference hardware can be a 4× miss for training** — a surprise that is much cheaper to have
now than after provisioning a GPU instance.

---

## 8. Common mistakes and troubleshooting

1. **Reaching for a fancier optimizer when the learning rate is wrong.** Fix the LR first.
2. **Reusing a pretraining LR for fine-tuning.** 1e-3 will destroy a pretrained model; use 1e-5–5e-5.
3. **Changing batch size without changing LR.**
4. **Comparing runs by epochs when the batch sizes differ.** Compare steps.
5. **Stopping a cosine schedule early**, leaving the LR high and the model unsettled.
6. **Adopting warmup + cosine on a short run** and assuming it helps. Measure it (§7.3).
7. **Forgetting bias correction** in a hand-rolled Adam — the first steps are 3× too large.
8. **Not clipping**, then losing a long run to one bad batch.
9. **Tuning on the test set** (M1-L06). Use validation.
10. **Assuming Adam always wins.** Benchmark.

| Symptom | Likely cause | Fix |
|---|---|---|
| Loss `nan` in a few steps | LR far too high; no clipping | ÷10; clip at 1.0 |
| Loss oscillates, no progress | LR too high | ÷3 and retry |
| Loss falls then flattens high | LR slightly high, or underfitting | Add decay; more capacity |
| Loss falls very slowly | LR too low | ×3 |
| Loss spikes mid-training | A bad batch | Clip; check the data |
| Fine-tune ruins the model | LR too high for fine-tuning | 1e-5 to 5e-5 |
| Train loss falls, validation rises | Overfitting (M3-L08) | Early stop; decay; more data |
| Adam much worse than SGD | Bias correction bug, or wrong β | Verify against a reference |

---

## 9. Security, privacy, reliability, cost

- **Cost.** Training cost is roughly linear in steps. A ×10 LR sweep of six values costs six runs —
  usually far cheaper than one badly-tuned long run.
- **Reliability.** Checkpoint regularly. A 20-hour run lost to `nan` at hour 19 with no checkpoint is
  a pure, avoidable loss. Log the LR, loss and gradient norm every N steps.
- **Reproducibility.** Record every hyperparameter with the checkpoint. "What LR did we use?" six
  weeks later is an unpleasant question without it.
- **Privacy.** Gradients carry information about training data; gradient inversion attacks can
  reconstruct inputs in federated settings. Do not treat gradients as anonymous. (M10-L11.)
- **Cost trap.** Adam's optimizer state is 2× the parameters. A model that fits in memory for
  inference may not fit for training — a common and expensive surprise on rented GPUs.

---

## 10. Exercises

### Exercise 1 — Beginner (~20 min)

1. `n = 12,000`, `batch_size = 32`. How many steps per epoch? How many in 15 epochs?
2. You halve the batch size and keep the epoch count. How do the steps change?
3. Match each loss curve description to its cause: (a) `nan` by step 5; (b) smooth but still falling
   at the end; (c) sawtooth around a high value; (d) falls fast then flat and high.
4. A colleague fine-tunes with LR 1e-3 and the model gets worse. What is your first suggestion?
5. Compute the SGD update for `g = [0.5, 0.02]` at α = 0.1 and explain the imbalance.

### Exercise 2 — Intermediate (~35 min)

1. Implement SGD, momentum and Adam as three functions with the same signature.
2. Reproduce every §6 number, including the 3.162× bias-correction result.
3. Sweep LR over `[1e-4, 1e-3, 1e-2, 0.1, 1.0, 10.0]` on the M3-L11 network. Record the final loss
   and classify each curve's failure mode.
4. Compare batch sizes 1, 8, 64 and full-batch: measure gradient-norm variance and wall-clock to a
   fixed loss.
5. Build a badly-scaled problem (one feature ×1000 the other) and show Adam converges in far fewer
   steps than SGD.

### Exercise 3 — Challenge (~40 min)

1. Implement warmup + cosine decay and plot the LR over 1,000 steps. Verify the peak lands exactly at
   the end of warmup.
2. Run the same problem with constant, cosine, and warmup+cosine. Report final losses.
3. Implement global-norm clipping. Initialise with large weights and show that clipping prevents `nan`
   where the unclipped run diverges.
4. Implement an LR range test and identify the recommended LR automatically.
5. Implement gradient accumulation and show that accumulating 4 micro-batches of 16 gives a gradient
   within floating-point tolerance of one batch of 64.
6. Measure optimizer state memory for SGD, momentum and Adam on a 100k-parameter model and confirm
   the 1× / 2× / 3× pattern.

---

## 11. Quiz

**Q1.** `n = 10,000`, `batch_size = 100`. How many steps in 5 epochs?

- A. 5  B. 100  C. 500  D. 50,000

**Q2.** Loss becomes `nan` after 3 steps. Most likely cause?

- A. Learning rate far too high.
- B. Too few epochs.
- C. Batch size too large.
- D. The model is too small.

**Q3.** What does Adam's second moment do?

- A. Adds momentum.
- B. Divides each parameter's step by a running estimate of its gradient magnitude, giving every
  parameter its own effective learning rate.
- C. Decays weights.
- D. Clips gradients.

**Q4.** Why warm up the learning rate?

- A. To make the GPU warm.
- B. Because early gradients are large and uninformative and Adam's variance estimate is unreliable
  at step 1, so a full-size early step can do lasting damage.
- C. It is required for convergence.
- D. To save memory.

**Q5.** Typical LR for fine-tuning a pretrained model?

- A. 0.1  B. 1e-3  C. 1e-5 to 5e-5  D. 10

**Q6.** Quadrupling the batch size does what to gradient noise?

- A. Quarters it.
- B. Halves it — the standard error falls as `1/√batch_size`.
- C. Leaves it unchanged.
- D. Doubles it.

**Q7.** How much extra memory does Adam need versus plain SGD?

- A. None.
- B. 2 extra copies of the parameters (first and second moments), which is why a model that fits
  for inference may not fit for training.
- C. 1 extra copy.
- D. 10 extra copies.

**Q8.** Why clip by global norm rather than per-parameter?

- A. It is faster.
- B. Scaling all gradients by one factor preserves the direction of the update and changes only its
  magnitude; per-parameter clipping distorts the direction.
- C. It uses less memory.
- D. There is no difference.

**Q9.** In §6, why do both parameters move by exactly α on Adam's first step despite gradients
differing 25-fold?

- A. A coincidence of the numbers chosen.
- B. Because `m̂/√v̂` equals `g/|g| = ±1` on the first step, so the step size is set by the learning
  rate rather than the gradient magnitude.
- C. Because bias correction was omitted.
- D. Because the learning rate was too high.

**Q10.** *(Written, rubric-graded.)* In under 100 words, explain to a colleague why the learning rate
is the first hyperparameter to tune, and how you would diagnose a bad one from a loss curve.

---

## 12. Revision notes

- `steps_per_epoch = ceil(n / batch_size)`. **Compare runs by steps, not epochs.**
- **Learning rate is the most important hyperparameter.** Diagnose it from the loss curve: `nan` =
  far too high · sawtooth = too high · flat-and-high = slightly high · slow = too low.
- Defaults: SGD 0.01–0.1 · Adam 1e-3 · transformer pretraining 1e-4–3e-4 · **fine-tuning 1e-5–5e-5**.
- Batch size 32–512 is the practical range. Noise falls as `1/√batch_size`; **some noise helps**.
- **Momentum** = running average of gradients; cancels oscillation, accelerates consistent descent.
- **Adam** = momentum + per-parameter scaling by `√(running mean of g²)`. Much less LR-sensitive.
- **Bias correction matters:** without it Adam's first step is **3.16× too large**, not too small.
- **Adam costs 2 extra parameter copies.** Training memory ≈ 4× parameter memory before activations.
- **Warmup + cosine** is the transformer default. Warmup protects the fragile start; decay lets the
  model settle. Stopping a cosine schedule early leaves the LR high.
- **Clip by global norm** (typically 1.0) — cheap insurance against one bad batch. Measured: **one
  poisoned row in 512** takes an unclipped run to `nan`; the clipped run recovers the true weights.
- Measured on a 1000:1 bowl: **Adam 125 steps, momentum 1,257, SGD 3,450** — and SGD diverges if its
  rate rises 10% above the stability limit. That constraint is what Adam removes.
- Measured: a **batch-1 gradient has cosine similarity 0.197** to the true gradient and is **50× slower
  per epoch** than batch 64. Worse on both axes.
- **Schedules buy stability, not necessarily a lower loss.** Measured: 30× smaller end-of-run swing,
  slightly *higher* final loss on an easy problem.
- Tune the learning rate before reaching for a better optimizer.

---

## 13. Completion checklist

- [ ] I can convert between epochs, batches and steps.
- [ ] I reproduced every §6 number, including 3.162×.
- [ ] I ran an LR sweep and saw each failure mode.
- [ ] I saw Adam take 28× fewer steps than stable SGD on the 1000:1 bowl.
- [ ] I saw one poisoned row destroy an unclipped run.
- [ ] I can explain what momentum and Adam's second moment each fix.
- [ ] I can explain warmup in one sentence.
- [ ] I know Adam's memory cost and why it matters.
- [ ] I scored 7/10 on the quiz.

---

## 14. References

- Kingma & Ba (2014), *Adam: A Method for Stochastic Optimization*.
  <https://arxiv.org/abs/1412.6980> `[UNVERIFIED]`
- Loshchilov & Hutter (2017), *Decoupled Weight Decay Regularization* (AdamW).
  <https://arxiv.org/abs/1711.05101> `[UNVERIFIED]`
- Smith (2015), *Cyclical Learning Rates* — the LR range test.
  <https://arxiv.org/abs/1506.01186> `[UNVERIFIED]`
- PyTorch optimizer docs. <https://pytorch.org/docs/stable/optim.html> `[UNVERIFIED]`

---

## 15. Next lesson

→ [M3-L13 — Splits, Class Imbalance and Stratification](M3-L13-splits-imbalance.md)

You can train a model. Next: making sure the number it reports means something.
