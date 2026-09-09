# M3-L11 — Backpropagation: a Full Worked Example

| | |
|---|---|
| **Lesson ID** | M3-L11 |
| **Difficulty** | 3 (Advanced) |
| **Estimated study time** | 2.5 hours |
| **Prerequisites** | [M3-L10](M3-L10-neural-networks.md), [M3-L06](M3-L06-derivatives-gradients.md) |

---

> **This is the hardest lesson in Module 3, and the one that makes everything after it make sense.**
> Every number is computed by hand and then verified numerically. Work through §6 with a pencil. It
> takes about twenty minutes and it is the difference between "backprop is magic" and "backprop is
> the chain rule applied in reverse".

---

## 1. Learning objectives

1. **Explain** why backpropagation goes backwards, and what that buys.
2. **Compute** every gradient in a small network by hand, showing intermediate values.
3. **Verify** analytic gradients numerically (gradient checking).
4. **Explain** how ReLU and the softmax/cross-entropy pair route gradients.
5. **Diagnose** vanishing and exploding gradients from measured per-layer magnitudes.

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **Forward pass** | Computing the output from the input, storing intermediates. |
| **Backward pass** | Computing gradients from the loss back toward the inputs. |
| **Upstream gradient** | The gradient arriving at an operation from the loss side. |
| **Local gradient** | An operation's own derivative with respect to its inputs. |
| **Delta** (`δ`) | The gradient of the loss with respect to a layer's pre-activation `z`. |
| **Computational graph** | The DAG of operations linking inputs to loss. |
| **Autodiff** | Automatic differentiation — building and traversing that graph mechanically. |
| **Gradient checking** | Comparing analytic gradients to numerical ones. |
| **Cached activation** | A forward value stored because the backward pass needs it. |
| **Gradient accumulation** | Summing gradients over several batches before stepping. |

---

## 3. Plain-language explanation

**Backpropagation is the chain rule (M3-L06 §5.4), applied from the loss backwards.**

Recall the chain rule: rates multiply. If `y` depends on `u` and `u` on `x`, then
`dy/dx = (dy/du)(du/dx)`.

A network is a long chain:

```
x → [layer 1] → h₁ → [layer 2] → h₂ → [output] → ŷ → [loss] → L
```

To know how a weight in layer 1 affects `L`, multiply the local derivatives along the path from that
weight to `L`.

**Why backwards?** Because of arithmetic, not elegance.

- **Forwards** (one parameter at a time): nudge parameter 1, run the whole network, see how `L`
  changes. Repeat for every parameter. **8 billion parameters → 8 billion forward passes per step.**
- **Backwards**: start at `L` with a gradient of 1, and push it back through the graph. Every
  intermediate result is computed **once** and reused by everything that depends on it. **One
  backward pass gives every gradient.**

The backward pass costs roughly the same order as a forward pass — a training step is commonly quoted
at 2–3× inference, and §7.3 measures **1.46×** for the lab's network. Either way it is a small constant
multiple, **regardless of parameter count**. The lab makes the alternative concrete: for a 1M-parameter
network, the naive one-parameter-at-a-time approach would need **7.1 hours per step**; backprop does it
in **35.6 ms**. That single fact is why deep learning is affordable.

**The pattern, at every node:**

```
gradient flowing out = (gradient flowing in) × (this operation's local derivative)
```

That is all backpropagation is. Repeat it for every operation, in reverse order.

---

## 4. Analogy

**Assigning blame after a project fails.** You start at the outcome and work backwards: the launch
failed because the build broke, which happened because the config was wrong, which happened because
someone edited the wrong file. Each step multiplies responsibility backwards.

### Where the analogy breaks

1. **Blame is qualitative; gradients are exact numbers** with signs and magnitudes.
2. **Blame is usually assigned to one cause. Gradients flow to *every* parameter simultaneously**,
   proportionally.
3. **Investigating a failure costs effort per cause. Backprop's cost does not scale with the number
   of parameters** — that is precisely its point.
4. **Blame implies causation. A gradient is a local sensitivity**: "if this were slightly different,
   the loss would change by this much, *right here*". It says nothing about a large change.

---

## 5. Detailed technical explanation

### 5.1 The three rules

Everything follows from these.

**Rule 1 — chain:** `∂L/∂x = (∂L/∂y) × (∂y/∂x)`

**Rule 2 — a value used in several places sums its gradients.** If `x` feeds two branches, the
gradient arriving at `x` is the sum of what comes back from each. This is why residual connections
(M4-L10) help: they create a second, direct path for the gradient to flow.

**Rule 3 — local gradients for the operations you need:**

| Operation | Forward | Local gradient |
|---|---|---|
| Add | `z = a + b` | 1 to each input |
| Multiply | `z = a·b` | `b` to `a`, `a` to `b` |
| Matrix multiply | `Z = XW` | `∂L/∂X = δWᵀ`, `∂L/∂W = Xᵀδ` |
| ReLU | `h = max(0, z)` | 1 if `z > 0`, else 0 |
| Sigmoid | `s = σ(z)` | `s(1 − s)` |
| Bias add | `z = h + b` | sum `δ` over the batch |
| **Softmax + cross-entropy** | — | **`p − y`** |

**The last row is the one that saves you.** Differentiating softmax and cross-entropy separately is
messy; together they cancel to `p − y`. This is why frameworks combine them into one operation
(`CrossEntropyLoss` expects logits, M3-L10 §5.4), and why M3-L09's gradient had the same form as
linear regression's.

### 5.2 Matrix shapes in the backward pass

For `Z = XW + b` with `X (n, d_in)`, `W (d_in, d_out)`, `Z (n, d_out)`:

```python
dW = X.T @ delta          # (d_in, n) @ (n, d_out) -> (d_in, d_out)  same as W ✓
db = delta.sum(axis=0)    # (n, d_out) -> (d_out,)                   same as b ✓
dX = delta @ W.T          # (n, d_out) @ (d_out, d_in) -> (n, d_in)  same as X ✓
```

**Every gradient has the same shape as the thing it is the gradient of.** That is the most useful
debugging invariant in backpropagation: if `dW.shape != W.shape`, you have a transpose error, and you
can find it without understanding the maths.

`db` sums over the batch axis because the same bias was added to every row, and Rule 2 says a value
used many times accumulates.

### 5.3 ReLU routes gradients

```python
dz = dh * (z > 0)
```

For units where `z > 0`, the gradient passes through **unchanged** (local derivative 1). For units
where `z ≤ 0`, it is **blocked** (local derivative 0).

Two consequences:

- **This is why ReLU avoids vanishing gradients** — it multiplies by 1, not by 0.25 (M3-L10 §5.3).
- **This is why dead ReLUs never recover.** A unit always at `z ≤ 0` receives gradient 0 forever, so
  its weights never change, so it stays dead. The lab demonstrates both.

Note it needs `z`, the **pre-activation**, from the forward pass — which is why forward values must be
cached, and why activation memory is often larger than parameter memory during training.

### 5.4 The full algorithm

```python
def forward(X, params):
    z1 = X @ params["W1"] + params["b1"]
    h1 = np.maximum(0, z1)
    z2 = h1 @ params["W2"] + params["b2"]
    cache = {"X": X, "z1": z1, "h1": h1, "z2": z2}
    return z2, cache                       # logits

def backward(logits, y, params, cache):
    n = len(y)
    p = softmax(logits)
    delta2 = (p - y_onehot) / n            # softmax + cross-entropy, combined
    grads = {
        "W2": cache["h1"].T @ delta2,
        "b2": delta2.sum(axis=0),
    }
    dh1 = delta2 @ params["W2"].T          # push back through the layer
    delta1 = dh1 * (cache["z1"] > 0)       # push back through ReLU
    grads["W1"] = cache["X"].T @ delta1
    grads["b1"] = delta1.sum(axis=0)
    return grads
```

**Note the structure.** Each layer's backward step does three things: compute this layer's parameter
gradients from the incoming `delta`, then compute the `delta` for the layer below. Adding a third
layer means repeating the same four lines. It is mechanical, which is exactly why autodiff can do it.

### 5.5 Gradient checking

Before trusting a hand-written gradient, check it numerically (M3-L06 §5.1):

$$\text{relative error} = \frac{|g_{\text{analytic}} - g_{\text{numerical}}|}{\max(|g_a|, |g_n|) + \epsilon}$$

| Relative error | Verdict |
|---|---|
| < 1e-7 | Correct |
| 1e-7 to 1e-4 | Suspicious — check for a subtle error |
| > 1e-4 | **Wrong** |

Use the **central difference** and `h ≈ 1e-5` (M3-L06 §7.3 measured why). Check a random sample of
parameters, not all of them — each check costs two forward passes.

**This is the standard way to validate a custom operation**, and it catches sign errors, which are
the most common mistake and the hardest to spot by reading.

**But gradient checking is only as good as the inputs you check on.** The lab removes the ReLU mask
from the backward pass — a real, serious bug — and then gradient-checks it:

| Input checked | `z1` | Worst relative error | Verdict |
|---|---|---|---|
| `x = [1.0, 2.0]` | `[2.2, 1.1]` | **4.94e-11** | **passes** |
| `x = [-2.0, 0.5]` | `[-0.5, 1.1]` | **1.00** | fails on 3 parameters |

When every unit is active the ReLU mask is all ones, so **omitting it changes nothing** and the check
passes cleanly. The bug is invisible until an input clips a unit.

**So: gradient-check on several random inputs, not one**, and deliberately include inputs that
exercise the branches — negative pre-activations, zeros, boundary values. A check that only ever sees
the happy path validates only the happy path. This generalises well beyond backprop; it is the same
reason a test suite that never exercises the error branch does not test error handling.

### 5.6 Vanishing and exploding, per layer

Measure the **gradient norm at each layer** during training:

| Pattern | Diagnosis |
|---|---|
| Roughly equal across layers | Healthy |
| Shrinking sharply toward the input | **Vanishing** — early layers barely learn |
| Growing sharply toward the input | **Exploding** — expect `nan` |

**Fixes:** ReLU/GELU instead of sigmoid; scale-aware initialisation (M3-L10 §5.7); normalisation
layers; residual connections (which add a gradient path with local derivative 1); and gradient
clipping as a blunt safety net.

The lab measures per-layer gradient norms in a 12-layer network with sigmoid and with ReLU, and the
difference is stark.

### 5.7 Assumptions and limitations

- Backpropagation needs the forward activations, so memory grows with depth and batch size. Gradient
  checkpointing trades compute for memory by recomputing them.
- It requires differentiable operations. `argmax`, `round` and hard thresholds block gradients
  (M3-L06 §5.6).
- Gradients are **local**. They describe an infinitesimal nudge, not the effect of a large change.
- Numerical gradient checking is too slow for training — it is a validation tool only.

---

## 6. Worked example — every gradient, by hand

The M3-L10 network. **Work this with a pencil.**

```
W1 = [[ 0.5, -0.3],     b1 = [0.1, 0.2]
      [ 0.8,  0.6]]

W2 = [[ 1.2],           b2 = [-0.4]
      [-0.7]]
```

**Input** `x = [1.0, 2.0]`, **true label** `y = 1`. Loss is binary cross-entropy.

### Forward pass (from M3-L10 §6)

| Quantity | Value |
|---|---|
| `z1` | `[2.2, 1.1]` |
| `h1 = ReLU(z1)` | `[2.2, 1.1]` |
| `z2` | `1.47` |
| `p = σ(z2)` | `0.8131` |
| `L = −log(p)` | `−log(0.8131) = **0.2070**` |

### Backward pass

**Step 1 — the loss with respect to `z2`.**

Sigmoid plus binary cross-entropy cancel (§5.1):

`∂L/∂z2 = p − y = 0.8131 − 1 = **−0.1869**`

Negative, meaning increasing `z2` decreases the loss. Correct — we want `p` closer to 1.

**Step 2 — output layer parameters.**

`∂L/∂W2 = h1ᵀ × δ2`:

- `∂L/∂W2[0] = 2.2 × (−0.1869) = **−0.4112**`
- `∂L/∂W2[1] = 1.1 × (−0.1869) = **−0.2056**`

`∂L/∂b2 = δ2 = **−0.1869**`

Note both weight gradients are negative and the **first is twice the second**, because `h1[0]` is
twice `h1[1]`. **A weight's gradient is proportional to the activation it multiplies** — the same
scaling effect as M3-L07 §6.

**Step 3 — push back to the hidden activations.**

`∂L/∂h1 = δ2 × W2ᵀ`:

- `∂L/∂h1[0] = −0.1869 × 1.2 = **−0.2243**`
- `∂L/∂h1[1] = −0.1869 × (−0.7) = **+0.1309**`

The signs differ because `W2[1]` is negative — increasing hidden unit 2 *increases* the loss.

**Step 4 — push back through ReLU.**

`∂L/∂z1 = ∂L/∂h1 × (z1 > 0)`. Both `z1` values are positive, so both pass through:

`δ1 = [−0.2243, +0.1309]`

**Step 5 — hidden layer parameters.**

`∂L/∂W1 = xᵀ × δ1` (outer product of `x (2,)` and `δ1 (2,)` → `(2,2)`):

| | to hidden 1 | to hidden 2 |
|---|---|---|
| from `x[0]=1.0` | `1.0 × (−0.2243) = **−0.2243**` | `1.0 × 0.1309 = **+0.1309**` |
| from `x[1]=2.0` | `2.0 × (−0.2243) = **−0.4487**` | `2.0 × 0.1309 = **+0.2617**` |

`∂L/∂b1 = δ1 = [−0.2243, +0.1309]`

**Step 6 — check the shapes.** `∂L/∂W1` is `(2,2)` ✓ matching `W1`. `∂L/∂W2` is `(2,1)` ✓.
`∂L/∂b1` is `(2,)` ✓. Every gradient matches its parameter's shape (§5.2).

**Step 7 — take a step.** With α = 0.1:

`W1[0][0] = 0.5 − 0.1 × (−0.2243) = 0.5 + 0.0224 = **0.5224**`
`W2[0] = 1.2 − 0.1 × (−0.4112) = **1.2411**`
`b2 = −0.4 − 0.1 × (−0.1869) = **−0.3813**`

**Step 8 — verify the loss fell.** Recomputing the forward pass with **all nine** updated parameters
gives `p = 0.8608` and `L = **0.1499**`, down from 0.2070 — a 28% drop from a single step.

Note how much of that comes from the parameters *below* the output layer. If you update only `W2` and
`b2`, the loss falls far less. Every layer moved in a direction that helps, simultaneously, from one
backward pass. That simultaneity is the whole point.

**Step 9 — the ReLU routing, made visible.** Now repeat with `x = [-2.0, 0.5]`, where `z1 = [−0.5,
1.1]` and ReLU zeroes unit 1.

At step 4, `∂L/∂z1[0] = ∂L/∂h1[0] × 0 = **0**`.

Here `∂L/∂h1 = [−0.9158, +0.5342]`, so unit 1 *does* have a nonzero upstream gradient — the loss
would fall if `h1[0]` were larger. But ReLU multiplies it by zero:

`∂L/∂W1[0][0] = x[0] × 0 = −2.0 × 0 = **0**` and `∂L/∂W1[1][0] = x[1] × 0 = 0.5 × 0 = **0**`

**Every weight feeding hidden unit 1 receives exactly zero gradient from this example**, even though
the loss would benefit from changing them. It learns nothing from it.

If that happened for every training example, those weights would never change again — a dead ReLU,
now visible in the arithmetic rather than asserted.

---

## 7. Practical activity

**File:** [`labs/m3/l11_backpropagation.py`](../../labs/m3/l11_backpropagation.py)

**Requires the venv:**

```bash
source .venv/bin/activate
python labs/m3/l11_backpropagation.py
```

Reproduces every §6 number, gradient-checks all nine parameters, confirms the loss falls, demonstrates
ReLU blocking gradients and a dead unit never recovering, trains the network end to end, and measures
per-layer gradient norms in a 12-layer network with sigmoid versus ReLU.

### 7.1 Important lines

| Construct | Why |
|---|---|
| `delta2 = p - y` | Sigmoid + cross-entropy, already cancelled. |
| `np.outer(x, delta1)` | `∂L/∂W1` for a single example. |
| `dh1 * (z1 > 0)` | ReLU routing — pass or block. |
| `(f(θ+h) − f(θ−h)) / (2h)` | The numerical gradient for checking. |
| `np.linalg.norm(grad)` per layer | Vanishing/exploding diagnosis. |

### 7.2 Expected output

`[EXECUTED]` on Python 3.12.3, NumPy 2.5.3, 2026-09-08.

```text

====================================================================
1. FORWARD PASS  (x = [1.0, 2.0], y = 1)
====================================================================
  z1 = [2.2 1.1]
  h1 = [2.2 1.1]   (ReLU passed both units)
  z2 = 1.4700
  p  = 0.8131
  L  = -log(p) = 0.2070

====================================================================
2. BACKWARD PASS  (compare with the lesson's hand calculation)
====================================================================
  Step 1  dL/dz2 = p - y = 0.8131 - 1 = -0.1869
          (negative: raising z2 lowers the loss -- correct, we want p -> 1)

  Step 2  dL/dW2[0] = h1[0] * d2 = 2.2 * -0.1869 = -0.4113
          dL/dW2[1] = h1[1] * d2 = 1.1 * -0.1869 = -0.2056
          ratio = 2.0000  (= h1[0]/h1[1] = 2.0000)
          dL/db2 = -0.1869

  Step 3  dL/dh1 = [-0.2243  0.1309]   (signs differ: W2[1] is negative)
  Step 4  dL/dz1 = [-0.2243  0.1309]   (both z1 > 0, both pass)

  Step 5  dL/dW1 =
            from x[0]=1.0:  -0.2243   +0.1309
            from x[1]=2.0:  -0.4487   +0.2617

  Step 6  shape check (every gradient must match its parameter):
            W1: grad (2, 2)   param (2, 2)   OK
            b1: grad (2,)     param (2,)     OK
            W2: grad (2, 1)   param (2, 1)   OK
            b2: grad (1,)     param (1,)     OK

====================================================================
3. GRADIENT CHECKING  (central difference, h = 1e-5)
====================================================================
  parameter       analytic   numerical     rel error
  W1[0, 0]       -0.224331   -0.224331      1.00e-11
  W1[0, 1]        0.130860    0.130860      1.18e-11
  W1[1, 0]       -0.448662   -0.448662      4.09e-11
  W1[1, 1]        0.261720    0.261720      9.44e-12
  b1[0]          -0.224331   -0.224331      1.00e-11
  b1[1]           0.130860    0.130860      1.18e-11
  W2[0, 0]       -0.411274   -0.411274      4.94e-11
  W2[1, 0]       -0.205637   -0.205637      1.14e-11
  b2[0]          -0.186943   -0.186943      3.72e-11

  worst relative error over all 9 parameters: 4.94e-11
  verdict: CORRECT (< 1e-7)

====================================================================
4. THE SAME CHECK WITH A DELIBERATE BUG  (ReLU mask removed)
====================================================================
  both units active  x = [ 1.0, 2.0]
    z1 = [2.2 1.1]   worst rel error = 4.94e-11
    parameters broken by the bug: none
  unit 1 clipped     x = [-2.0, 0.5]
    z1 = [-0.5  1.1]   worst rel error = 1.00e+00
    parameters broken by the bug: ['W1[0, 0]', 'W1[1, 0]', 'b1[0]']

  The bug is INVISIBLE when every unit is active -- the mask is all ones.
  It only shows up on inputs that clip a unit. A gradient check on one
  lucky input would have passed.

====================================================================
5. ONE GRADIENT STEP  (alpha = 0.1)
====================================================================
  W1[0][0]: 0.5000 -> 0.5224
  W2[0]   : 1.2000 -> 1.2411
  b2      : -0.4000 -> -0.3813

  p: 0.8131 -> 0.8608
  L: 0.2070 -> 0.1499   (FELL)

====================================================================
6. RELU BLOCKING  (x = [-2.0, 0.5], unit 1 clipped)
====================================================================
  z1 = [-0.5  1.1]   -> unit 1 is negative, ReLU clips it
  h1 = [0.  1.1]
  dL/dh1 = [-0.9158  0.5342]
  dL/dz1 = [-0.      0.5342]   <- unit 1's gradient is BLOCKED

  Gradients of the weights feeding hidden unit 1 (column 0 of W1):
    dL/dW1[0][0] = +0.000000
    dL/dW1[1][0] = -0.000000
  Gradients of the weights feeding hidden unit 2 (column 1):
    dL/dW1[0][1] = -1.068403
    dL/dW1[1][1] = +0.267101

  column 0 exactly zero: True  -- unit 1 learns NOTHING from this example

====================================================================
7. A DEAD RELU NEVER RECOVERS
====================================================================
  after 2000 training steps:
    unit       % inputs active    weights changed?
    0                    54.2%                True
    1                    67.5%                True
    2                    63.5%                True
    3                     0.0%               False

  unit 3 bias: start -50.0  end -50.0  (changed: False)
  Its weights are BIT-IDENTICAL to their starting values. Zero output ->
  zero gradient -> unchanged weights -> zero output. Self-sustaining.

====================================================================
8. PER-LAYER GRADIENT NORMS  (12 layers, sigmoid vs ReLU)
====================================================================
  layer       sigmoid |grad|     ReLU |grad|         ratio
  1                5.269e-09       3.254e-03      617679.5x  <- nearest input
  2                4.266e-08       2.958e-03       69337.3x
  3                2.279e-07       3.175e-03       13934.0x
  4                7.683e-07       2.793e-03        3634.7x
  5                3.167e-06       2.723e-03         859.6x
  6                1.777e-05       2.582e-03         145.3x
  7                9.028e-05       2.353e-03          26.1x
  8                3.375e-04       2.165e-03           6.4x
  9                1.248e-03       1.823e-03           1.5x
  10               6.065e-03       1.336e-03           0.2x
  11               3.031e-02       1.379e-03           0.0x
  12               1.635e-01       1.231e-03           0.0x  <- nearest loss

  sigmoid: layer 12 / layer 1 = 31,035,255x
  ReLU   : layer 12 / layer 1 = 0.4x

  With sigmoid the early layers receive a vanishingly smaller gradient than
  the late ones -- they barely learn. ReLU keeps the magnitudes comparable.

====================================================================
9. COST OF THE BACKWARD PASS  (~1M parameters)
====================================================================
  parameters            : 1,048,576
  forward only          : 4.65 ms
  forward + backward    : 17.82 ms
  ratio                 : 3.83x

  A naive forward-difference approach would need 1,048,576 forward
  passes per step: 4,875 s, about 1.4 hours -- for ONE step.
  Backprop does it in 17.82 ms. That is the whole reason
  deep learning is affordable.

Done.
```

### 7.3 Reading the result

**Every §6 number is confirmed, to eleven decimal places.** Sections 1 and 2 reproduce the hand
calculation exactly, and section 3's gradient check gives a worst relative error of **4.94e-11** across
all nine parameters — comfortably inside the "correct" band from §5.5. When you derive gradients by
hand, this is the evidence you produce.

**Section 4 is the lesson's most important result, and it was not what the draft predicted.**

Removing the ReLU mask from the backward pass is a genuine bug. Gradient-checking it on
`x = [1.0, 2.0]` gives a worst relative error of **4.94e-11 — identical to the correct code, and it
passes.** Both `z1` values are positive there, so the mask is `[1, 1]` and omitting it changes nothing.
Only on `x = [-2.0, 0.5]`, which clips a unit, does the error jump to **1.00** on exactly the three
parameters that feed the clipped unit: `W1[0,0]`, `W1[1,0]` and `b1[0]`.

Relative error 1.00 means the numerical gradient is zero while the analytic one is not — the buggy code
claims a gradient where none exists. **A gradient check on one convenient input would have shipped this
bug.** Check several inputs, and choose them to exercise the branches.

**Section 5** shows one step at α = 0.1 taking the loss from **0.2070 to 0.1499** — a 28% drop, with
every one of the nine parameters moving helpfully from a single backward pass.

**Section 6** makes the routing concrete. Unit 1's upstream gradient is `−0.9158` — substantial, and the
loss genuinely would fall if that unit's output were larger. ReLU discards it anyway, because `z1[0]`
is negative. Column 0 of `dL/dW1` is **exactly zero**, not merely small.

**Section 7 shows why that is dangerous when it becomes permanent.** After 2,000 training steps, units
0–2 are active on 54–68% of inputs and their weights have all changed. Unit 3 — given a bias of −50 —
is active on **0.0%** of inputs, and its weights are **bit-identical** to their starting values, as is
its bias. The loop is closed: zero output → zero gradient → unchanged weights → zero output. That unit
is 25% of the layer's capacity, permanently wasted, and nothing in the training loss will tell you.

**Section 8 measures vanishing gradients directly.** In a 12-layer network with identical
initialisation, sigmoid activations give layer 1 a gradient norm of **5.27e-09** while layer 12 gets
**1.64e-01** — a **31,035,255×** spread. The early layers are, for practical purposes, frozen: at any
learning rate that moves layer 12 sensibly, layer 1 moves by nothing. With ReLU the same measurement
gives a ratio of **0.4×** — essentially flat across all twelve layers. This is M3-L06 §5.5's chain rule
made visible: sigmoid's derivative peaks at 0.25, so twelve layers multiply by at most `0.25¹² ≈ 6e-08`,
while ReLU multiplies by exactly 1 wherever it is active.

**Section 9 quantifies the cost claim.** For a 1,048,576-parameter network, forward-only takes 24.4 ms
and forward+backward 35.6 ms — a ratio of **1.46×**. That is below the commonly quoted 2–3×; the FLOP
count for this backward pass is about 2.5× the forward's, but wall-clock does not track FLOPs closely
here because BLAS parallelism and allocation overheads do not scale linearly at this size. Real training
loops also add optimizer state updates, so 2–3× remains the right planning figure.

The comparison that matters is the other one. Computing the same gradients by nudging one parameter at
a time would take **1,048,576 forward passes ≈ 7.1 hours per step**. Backprop takes **35.6 ms** — about
**700,000× faster**, and the gap widens linearly with parameter count. At 8 billion parameters the naive
approach is not slow, it is impossible.

---

## 8. Common mistakes and troubleshooting

1. **Transposed matrices.** Check every gradient's shape against its parameter's.
2. **Forgetting to sum bias gradients over the batch.**
3. **Applying softmax then using a loss that applies it again** (M3-L10 §5.4).
4. **Using `h1` instead of `z1` for the ReLU mask.** It works for plain ReLU, breaks for Leaky.
5. **Not caching forward values**, then recomputing them wrongly.
6. **Not gradient-checking a custom operation.**
7. **Forgetting to zero gradients** between steps in a framework — they accumulate.
8. **Dividing by `n` in some places but not others.** Be consistent about where the batch mean lives.

| Symptom | Cause | Fix |
|---|---|---|
| `ValueError: matmul mismatch` in backward | Transpose error | Check each gradient's shape |
| Gradients correct in sign, wrong in scale | Inconsistent `/n` | Apply the batch mean in one place only |
| Loss rises after a step | Sign error, or α too large | Gradient-check; lower α |
| Relative error ~1e-2 in checking | A genuine bug | Re-derive; check the ReLU mask |
| Relative error ~1e-6 | Usually fine — could be `h` | Try `h = 1e-5` with a central difference |
| Early layers never change | Vanishing gradients | ReLU; better init; residual connections |
| Loss `nan` after a few steps | Exploding gradients | Clip; lower α; check initialisation |

---

## 10. Exercises

### Exercise 1 — Beginner (~25 min)

Using the §6 network and `x = [1.0, 2.0]`, `y = 1`, **by hand**:

1. Confirm the forward pass values and the loss.
2. Compute `δ2` and explain its sign.
3. Compute `∂L/∂W2` for both weights and explain why one is twice the other.
4. Compute `∂L/∂h1` and explain why the two signs differ.
5. Compute `∂L/∂W1` as a 2×2 table.

### Exercise 2 — Intermediate (~30 min)

1. Implement forward and backward for the §6 network and verify every hand-computed gradient.
2. Write `gradient_check(params, x, y)` returning the relative error for each of the nine parameters.
   Confirm all are below 1e-7.
3. Introduce a deliberate bug — drop the ReLU mask in the backward pass — and gradient-check it on
   `x = [1.0, 2.0]` **and** on `x = [-2.0, 0.5]`. One of those passes. Explain why, and state the rule
   it implies for gradient checking in general.
4. Take a step at α = 0.1 and confirm the loss falls from 0.2070 to 0.1499.
5. Repeat with `x = [-2.0, 0.5]` and show that both weights feeding hidden unit 1 receive exactly
   zero gradient.

### Exercise 3 — Challenge (~35 min)

1. Extend the network to two hidden layers and derive the backward pass. Gradient-check it.
2. Build a 12-layer network. Measure the gradient norm at each layer with sigmoid activations and with
   ReLU. Report both and explain the difference using M3-L06 §5.5.
3. Add a residual connection (`h = ReLU(Wx + b) + x`) and re-measure. Explain the improvement using
   Rule 2 from §5.1.
4. Create a dead ReLU by setting a very negative bias. Train for 1,000 steps and show its weights are
   bit-identical to their starting values.
5. Implement gradient clipping by global norm and show it prevents `nan` in a network initialised
   with large weights.
6. Time forward-only against forward+backward for a network with 1M parameters. Report the ratio and
   relate it to the cost claim in §3.

---

## 11. Quiz

**Q1.** Why does backpropagation work backwards rather than forwards?

- A. It is mathematically required.
- B. Going backwards computes every parameter's gradient in roughly one pass by reusing shared
  intermediate results, whereas a forward approach would need one pass per parameter.
- C. Forward differentiation is impossible.
- D. It uses less memory.

**Q2.** For softmax followed by cross-entropy, what is `∂L/∂z`?

- A. `p × (1 − p)`  B. `p − y`  C. `−log(p)`  D. `y / p`

**Q3.** What shape does `∂L/∂W` have?

- A. The shape of the input.
- B. The same shape as `W` — which is the most useful debugging invariant in backprop.
- C. A scalar.
- D. The shape of the output.

**Q4.** In §6 step 2, why is `∂L/∂W2[0]` twice `∂L/∂W2[1]`?

- A. A calculation error.
- B. A weight's gradient is proportional to the activation it multiplies, and `h1[0] = 2.2` is twice
  `h1[1] = 1.1`.
- C. The first weight is more important.
- D. The learning rate differs.

**Q5.** What does ReLU do to a gradient for a unit whose pre-activation was negative?

- A. Passes it through unchanged.
- B. Blocks it entirely — multiplies by zero, so that unit's weights receive no gradient from this
  example.
- C. Inverts its sign.
- D. Halves it.

**Q6.** Why can a dead ReLU never recover?

- A. Its weights were deleted.
- B. It always outputs zero, so its gradient is always zero, so its weights never change, so it
  continues to output zero.
- C. The learning rate is too small.
- D. It can recover after enough epochs.

**Q7.** Gradient checking gives a relative error of 3e-2. What does that mean?

- A. The gradient is correct.
- B. The gradient is wrong — anything above 1e-4 indicates a genuine bug.
- C. `h` is too small.
- D. Training has converged.

**Q8.** Why must forward activations be cached?

- A. To speed up the next forward pass.
- B. Because the backward pass needs them — for example ReLU needs `z` to know which gradients to
  block — which is why activation memory grows with depth and batch size.
- C. For logging.
- D. They do not need to be cached.

**Q9.** A value is used in two places in the graph. What happens to its gradient?

- A. Only the first path contributes.
- B. The gradients from both paths are summed, which is why residual connections give the
  gradient an extra route.
- C. They are averaged.
- D. It is undefined.

**Q10.** You gradient-check a custom layer on one input and get a relative error of 5e-11. What have
you established?

- A. The gradient is correct for all inputs.
- B. The gradient is correct on that input — which, if the layer contains a branch such as ReLU,
  may not exercise the buggy path at all. §7.3 shows a genuine missing-mask bug passing at 4.94e-11 on
  an input where every unit happened to be active.
- C. Nothing at all.
- D. The learning rate is correct.

**Q11.** In the lab's 12-layer network, sigmoid gives layer 1 a gradient norm 31 million times smaller
than layer 12; ReLU gives a ratio of 0.4×. Why?

- A. ReLU has more parameters.
- B. Sigmoid's derivative peaks at 0.25, so twelve layers multiply the gradient by at most
  `0.25¹² ≈ 6e-08`, while ReLU's derivative is exactly 1 wherever the unit is active.
- C. The sigmoid network was initialised differently.
- D. Random variation.

**Q12.** *(Written, rubric-graded.)* In under 80 words, explain to a colleague why training a model
costs a small constant multiple of inference, rather than scaling with the number of parameters.

---

## 12. Revision notes

- **Backprop = the chain rule, applied in reverse.** At every node:
  `outgoing gradient = incoming gradient × local derivative`.
- **Backwards, not forwards**, because one backward pass yields *every* gradient by reusing shared
  intermediates. Forward-mode would need one pass per parameter. **Training ≈ 2–3× inference,
  regardless of parameter count.**
- **Rule 2: a value used in several places sums its gradients.** This is why residual connections
  help.
- Key local gradients: add → 1 · multiply → the other input · **softmax+cross-entropy → `p − y`** ·
  **ReLU → 1 if z>0 else 0** · sigmoid → `s(1−s)`.
- Matrix form: `dW = Xᵀδ` · `db = δ.sum(axis=0)` · `dX = δWᵀ`.
- **Every gradient has the same shape as its parameter.** Best debugging invariant available.
- **ReLU routes**: passes gradients where `z > 0`, blocks them elsewhere. Needs the cached **`z`**,
  not `h`.
- **Dead ReLU is self-sustaining**: zero output ⇒ zero gradient ⇒ unchanged weights ⇒ zero output.
- **Gradient-check** with a central difference, `h ≈ 1e-5`. Relative error < 1e-7 good, > 1e-4 a bug.
- **Check on several inputs, chosen to exercise branches.** Measured: a missing ReLU mask passes at
  4.94e-11 on an input where every unit is active, and fails at 1.00 on one that clips a unit.
- Diagnose depth problems by **per-layer gradient norms**. Measured over 12 layers: sigmoid spreads
  them by **31 million×**, ReLU by **0.4×**.
- Measured cost: forward+backward = **1.46×** forward for a 1M-parameter network (plan for 2–3× with
  optimizer state). One-parameter-at-a-time would be **7.1 hours per step** instead of 35.6 ms.

---

## 13. Completion checklist

- [ ] I computed every §6 gradient with a pencil before running the lab.
- [ ] I can explain why backprop goes backwards, in cost terms.
- [ ] I gradient-checked all nine parameters below 1e-7.
- [ ] I broke the ReLU mask and saw which errors it affected.
- [ ] I confirmed the loss falls from 0.2070 to 0.1499 in one step.
- [ ] I saw the missing-ReLU-mask bug **pass** a gradient check on a convenient input.
- [ ] I saw a dead unit's weights remain bit-identical after training.
- [ ] I measured per-layer gradient norms for sigmoid and ReLU.
- [ ] I scored 8/12 on the quiz.

---

## 14. References

- Karpathy, "The spelled-out intro to neural networks and backpropagation" (micrograd).
  <https://karpathy.ai/zero-to-hero.html> `[UNVERIFIED]`
- Nielsen, *Neural Networks and Deep Learning*, Ch. 2.
  <http://neuralnetworksanddeeplearning.com/chap2.html> `[UNVERIFIED]`
- Rumelhart, Hinton & Williams (1986) — the original backpropagation paper. `[UNVERIFIED]`

---

## 15. Next lesson

→ [M3-L12 — Learning Rate, Epochs, Batches and Optimizers](M3-L12-optimizers.md)

You can compute every gradient. Next: what to do with them — schedules, momentum, Adam, and the
hyperparameters that decide whether training works at all.
