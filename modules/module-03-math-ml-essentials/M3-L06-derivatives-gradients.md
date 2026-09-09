# M3-L06 — Derivatives, Gradients and the Chain Rule

| | |
|---|---|
| **Lesson ID** | M3-L06 |
| **Difficulty** | 2 (Core) |
| **Estimated study time** | 2.0 hours |
| **Prerequisites** | [M3-L01](M3-L01-vectors-matrices.md) |

---

> **If you have never done calculus, start here anyway.** This lesson builds the derivative from
> arithmetic you already have — "how much does the output change when I nudge the input?" — and every
> value is computed numerically before any formula appears. You will not need to integrate anything.

---

## 1. Learning objectives

1. **Explain** what a derivative is, in terms of a small nudge to the input.
2. **Compute** a derivative numerically and **check** it against the analytic rule.
3. **Explain** what a gradient is and why it points uphill.
4. **Apply** the chain rule to a two-step function by hand.
5. **Explain** what backpropagation computes, and why the chain rule makes it possible.

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **Function** | A rule turning inputs into an output: `f(x) = x²`. |
| **Derivative** | The rate of change of a function's output with respect to one input. |
| **`f'(x)` / `df/dx`** | Notation for the derivative of `f` with respect to `x`. |
| **Slope** | The derivative's geometric meaning: rise over run. |
| **Nudge** (h) | A tiny change to the input, used to measure the derivative numerically. |
| **Numerical derivative** | `(f(x+h) − f(x)) / h` for small `h`. |
| **Analytic derivative** | The exact formula, from calculus rules. |
| **Partial derivative** (`∂f/∂x`) | The derivative with respect to one variable, holding others fixed. |
| **Gradient** (`∇f`) | The vector of all partial derivatives. Points in the direction of steepest increase. |
| **Chain rule** | The rule for differentiating a function of a function. |
| **Local minimum** | A point where the function is lower than everywhere nearby. |
| **Backpropagation** | Applying the chain rule backwards through a network to get every parameter's gradient. |
| **Computational graph** | The network of operations linking inputs to the final output. |

---

## 3. Plain-language explanation

**A derivative answers one question: if I nudge the input a tiny bit, how much does the output
change?**

Take `f(x) = x²`. At `x = 3`:

```
f(3)      = 9
f(3.001)  = 9.006001
change in output = 0.006001
change in input  = 0.001
rate = 0.006001 / 0.001 = 6.001
```

The derivative at `x = 3` is **6**. Our numerical estimate of 6.001 is off only because the nudge was
not infinitely small.

**That is the whole idea.** A derivative is a ratio: output change divided by input change, as the
input change shrinks toward zero.

**Why you care.** Training a model means finding parameter values that make the loss small. The
derivative tells you which way to move each parameter:

- Derivative **positive** → increasing this parameter increases the loss → **decrease** it.
- Derivative **negative** → increasing this parameter decreases the loss → **increase** it.
- Derivative **zero** → you are at a flat point; stop.

**A gradient is just all the derivatives at once** — one per parameter. For a model with 8 billion
parameters, the gradient is a vector of 8 billion numbers, each saying "nudge me this way".

---

## 4. Analogy

**Standing on a hillside in fog.** You cannot see the valley, but you can feel the slope under your
feet. The gradient is that felt slope: it points **uphill**, and steeply where the ground is steep.

To descend, you step in the **opposite** direction to the gradient — hence *gradient descent*.

### Where the analogy breaks

1. **A hillside is two-dimensional. A loss surface has millions of dimensions.** Intuitions about
   "walking downhill" mostly survive, but intuitions about "seeing the whole landscape" do not.
2. **A real hill has one bottom. A loss surface has many local minima**, and gradient descent finds
   *a* low point, not necessarily the lowest.
3. **You feel the true slope. A model estimates the slope from a mini-batch of data**, so it is noisy
   — this is the "stochastic" in stochastic gradient descent (M3-L12).
4. **Fog is a limitation. In high dimensions the difficulty is different** — most flat-looking points
   are saddle points (up in some directions, down in others) rather than minima.

---

## 5. Detailed technical explanation

### 5.1 The definition

$$f'(x) = \lim_{h \to 0} \frac{f(x+h) - f(x)}{h}$$

Every symbol: `h` is a small nudge, `f(x+h) − f(x)` is how much the output moved, dividing by `h`
gives the rate, and `lim h→0` means "as the nudge shrinks toward zero".

In code you cannot take a true limit, so you use a small `h`:

```python
def numerical_derivative(f, x, h=1e-5):
    return (f(x + h) - f(x)) / h
```

**A better version uses a symmetric nudge**, which is far more accurate for the same `h`:

```python
def numerical_derivative(f, x, h=1e-5):
    return (f(x + h) - f(x - h)) / (2 * h)     # central difference
```

The lab measures both. Note that `h` cannot be made arbitrarily small: below about `1e-8`,
floating-point cancellation makes the estimate *worse*, not better. There is an optimum, and the lab
finds it.

### 5.2 The rules you need

You only need a handful, and you can verify every one numerically.

| Function | Derivative | Check at x=3 |
|---|---|---|
| `f(x) = c` (constant) | `0` | 0 |
| `f(x) = x` | `1` | 1 |
| `f(x) = x²` | `2x` | 6 |
| `f(x) = xⁿ` | `n·xⁿ⁻¹` | — |
| `f(x) = eˣ` | `eˣ` | 20.09 |
| `f(x) = ln(x)` | `1/x` | 0.333 |
| `f(x) = c·g(x)` | `c·g'(x)` | — |
| `f(x) = g(x) + h(x)` | `g'(x) + h'(x)` | — |

**The power rule** (`xⁿ → n·xⁿ⁻¹`) covers most of what you meet. `x²` → `2x`. `x³` → `3x²`. `x` →
`1·x⁰` = 1.

You do not need to memorise these to use a framework — autodiff computes them for you. You need them
to *understand what the framework is doing* and to debug when a gradient is zero or explodes.

### 5.3 Partial derivatives and the gradient

With several inputs, differentiate with respect to one at a time, treating the others as constants.

$$f(x, y) = x^2 + 3y$$

- `∂f/∂x = 2x` (treat `3y` as a constant → derivative 0)
- `∂f/∂y = 3` (treat `x²` as a constant → derivative 0)

The **gradient** collects them:

$$\nabla f = \left[\frac{\partial f}{\partial x}, \frac{\partial f}{\partial y}\right] = [2x, 3]$$

At `(x, y) = (2, 5)`: `∇f = [4, 3]`.

**Interpretation:** from that point, increasing `x` raises `f` at 4 units per unit, and increasing `y`
raises it at 3. The gradient `[4, 3]` points in the direction of steepest increase, and its magnitude
`√(16+9) = 5` says how steep.

**To minimise, move against it:** `new_point = old_point − learning_rate × gradient` — which is
gradient descent, and M3-L07 develops it fully.

### 5.4 The chain rule

**This is the one that matters**, because it is what makes training deep networks possible.

If `y` depends on `u`, and `u` depends on `x`, then:

$$\frac{dy}{dx} = \frac{dy}{du} \times \frac{du}{dx}$$

**Rates multiply.** If `u` changes 3× as fast as `x`, and `y` changes 2× as fast as `u`, then `y`
changes 6× as fast as `x`.

**Worked example.** `y = (3x + 1)²` at `x = 2`.

Break it into steps:

1. `u = 3x + 1` → at x=2, `u = 7`
2. `y = u²` → `y = 49`

Now differentiate each step:

1. `du/dx = 3`
2. `dy/du = 2u = 14`

Chain them: `dy/dx = 14 × 3 = **42**`

**Check numerically:** `f(2) = 49`, `f(2.001) = (7.003)² = 49.042009`.
`(49.042009 − 49) / 0.001 = 42.009`. ✓

**Why this is the whole of backpropagation.** A neural network is a long chain:

```
input → layer1 → layer2 → layer3 → output → loss
```

To know how a weight in layer 1 affects the loss, you multiply the local derivatives along the path
from that weight to the loss. Backpropagation computes these **backwards from the loss**, reusing
shared intermediate results, so the cost of getting *every* parameter's gradient is roughly the same
as one forward pass — not one pass per parameter.

**That efficiency is why deep learning is feasible at all.** Computing 8 billion gradients naively,
one nudge at a time, would require 8 billion forward passes per training step. The chain rule reduces
it to about two.

### 5.5 Gradients that go wrong

Two failure modes worth recognising by name, both consequences of multiplying many terms:

| Problem | Cause | Symptom |
|---|---|---|
| **Vanishing gradient** | Many derivatives < 1 multiplied together | Early layers stop learning; loss plateaus |
| **Exploding gradient** | Many derivatives > 1 multiplied together | Loss becomes `nan`; weights blow up |

Multiply 50 numbers of size 0.5 and you get `0.5⁵⁰ ≈ 10⁻¹⁵` — effectively zero. Multiply 50 of size
1.5 and you get `1.5⁵⁰ ≈ 6 × 10⁸`.

**This is the same compounding arithmetic as M1-L11's `p^n` reliability and M3-L05's underflow.** The
mitigations — ReLU activations, residual connections, normalisation layers, gradient clipping —
exist to keep that product near 1, and M4-L10 shows where they sit in a transformer.

### 5.6 Automatic differentiation

You will rarely differentiate by hand. Frameworks build a **computational graph** as you compute,
then walk it backwards applying the chain rule.

```python
# PyTorch-style, illustrative
x = tensor(2.0, requires_grad=True)
y = (3 * x + 1) ** 2
y.backward()
x.grad          # 42.0
```

**What you still need this lesson for:**

- Reading `nan` losses (exploding gradients) and flat losses (vanishing, or a zero learning rate).
- Understanding why an operation is or is not differentiable — `argmax` and hard thresholds are not,
  which is why models output continuous probabilities rather than discrete decisions (M3-L09).
- Knowing that `.detach()` or `no_grad()` breaks the chain deliberately.

### 5.7 Assumptions and limitations

- Derivatives require the function to be smooth at that point. `|x|` has no derivative at 0; ReLU is
  handled by convention.
- Numerical derivatives are estimates. Too large an `h` is inaccurate; too small is dominated by
  floating-point error.
- The gradient is *local*. It says nothing about the landscape beyond the immediate neighbourhood.
- Zero gradient means a flat point — a minimum, a maximum, or a saddle.

---

## 6. Worked example — one step of gradient descent, by hand

Fit a single parameter. The model predicts `ŷ = w × x`, and we use squared error.

**Data:** one example, `x = 2`, true `y = 10`. So the ideal `w` is 5.
**Start:** `w = 1`.

**Step 1 — forward pass.**

- Prediction: `ŷ = w × x = 1 × 2 = 2`
- Error: `ŷ − y = 2 − 10 = −8`
- Loss: `L = (ŷ − y)² = 64`

**Step 2 — the derivative, by the chain rule.**

The chain is `w → ŷ → L`.

1. `dL/dŷ = 2(ŷ − y) = 2 × (−8) = **−16**`
2. `dŷ/dw = x = **2**`
3. `dL/dw = (dL/dŷ) × (dŷ/dw) = −16 × 2 = **−32**`

**Step 3 — read the sign.** The derivative is **negative**, meaning increasing `w` *decreases* the
loss. So we should increase `w` — which matches intuition, since 1 is well below the ideal 5.

**Step 4 — take a step.** With learning rate `α = 0.01`:

`w_new = w − α × (dL/dw) = 1 − 0.01 × (−32) = 1 + 0.32 = **1.32**`

**Step 5 — verify the loss fell.**

- `ŷ = 1.32 × 2 = 2.64`
- `L = (2.64 − 10)² = (−7.36)² = **54.17**`

Down from 64. The step worked.

**Step 6 — verify the derivative numerically.** Nudge `w` by `h = 0.0001`:

- `L(1) = (1×2 − 10)² = 64`
- `L(1.0001) = (1.0001×2 − 10)² = (−7.9998)² = 63.99680004`
- `(63.99680004 − 64) / 0.0001 = **−31.9996**`

Against the analytic `−32`. ✓ **Always check a hand-derived gradient this way** — it is the standard
technique (gradient checking) and it catches sign errors, which are the most common mistake.

**Step 7 — what happens if the learning rate is wrong.**

| α | `w` after one step | New loss | Outcome |
|---|---|---|---|
| 0.001 | 1.032 | 63.0 | Correct direction, very slow |
| 0.01 | 1.32 | 54.2 | Good progress |
| 0.1 | 4.2 | 2.56 | Fast, still short of w=5 |
| **0.125** | **5.0** | **0.0** | **Exactly optimal here** |
| 0.2 | 7.4 | 23.0 | Overshot past w=5, but still improving |
| 0.5 | 17.0 | 576 | **Diverging** — worse than we started |

The divergence threshold for this problem is exactly **0.25**, and the lab finds it by bisection.
Above it each step overshoots by more than it corrects, so the loss grows without bound. Note that
0.2 *overshoots* the minimum and is still fine — overshooting is not the same as diverging.

**The gradient tells you the direction; the learning rate decides how far to trust it.** Too small
and training crawls; too large and you overshoot or diverge. M3-L12 covers choosing it.

---

## 7. Practical activity

**File:** [`labs/m3/l06_derivatives.py`](../../labs/m3/l06_derivatives.py)

**Requires the venv:**

```bash
source .venv/bin/activate
python labs/m3/l06_derivatives.py
```

Computes derivatives numerically and checks them against the analytic rules, finds the optimal nudge
size empirically, verifies the chain rule, computes a gradient and shows it pointing uphill, runs the
§6 descent to convergence, demonstrates learning rates from too-small to diverging, and shows
gradients vanishing and exploding through a deep chain.

### 7.1 Important lines

| Construct | Why |
|---|---|
| `(f(x+h) - f(x-h)) / (2*h)` | Central difference — more accurate than the forward form. |
| Sweep over `h` | Shows the accuracy optimum and floating-point breakdown below it. |
| `dy_du * du_dx` | The chain rule, applied directly. |
| `w -= lr * grad` | One gradient-descent step. |
| `np.prod(derivatives)` over a deep chain | Vanishing and exploding gradients, measured. |

### 7.2 Expected output

`[EXECUTED]` 2026-09-08 with numpy 2.5.3, Python 3.12.3:

```
==========================================================================
DERIVATIVES, GRADIENTS AND THE CHAIN RULE
==========================================================================

--------------------------------------------------------------------------
1. A DERIVATIVE IS JUST A NUDGE RATIO
--------------------------------------------------------------------------
  f(x) = x^2, at x = 3.0

       nudge h        f(x)        f(x+h)      change      rate
           1.0      9.0000     16.000000    7.000000    7.0000
           0.1      9.0000      9.610000    0.610000    6.1000
          0.01      9.0000      9.060100    0.060100    6.0100
         0.001      9.0000      9.006001    0.006001    6.0010
        0.0001      9.0000      9.000600    0.000600    6.0001

  As the nudge shrinks, the rate converges on 6. The analytic
  derivative of x^2 is 2x, and 2 x 3 = 6. That is all a
  derivative is: the limit of that last column.

--------------------------------------------------------------------------
2. THE RULES, CHECKED NUMERICALLY
--------------------------------------------------------------------------
  function                        x    analytic    numerical       error
  f(x) = 7        (constant)      3    0.000000     0.000000    0.00e+00
  f(x) = x                        3    1.000000     1.000000    6.55e-12
  f(x) = x^2                      3    6.000000     6.000000    3.93e-11
  f(x) = x^3                      2   12.000000    12.000000    2.12e-10
  f(x) = 5x + 3                   3    5.000000     5.000000    1.66e-10
  f(x) = e^x                      1    2.718282     2.718282    5.86e-11
  f(x) = ln(x)                    4    0.250000     0.250000    9.46e-12

  Every rule verified against a numerical estimate. You can always
  check a derivative this way - it is how you catch sign errors.

--------------------------------------------------------------------------
3. HOW SMALL SHOULD h BE? (smaller is NOT better)
--------------------------------------------------------------------------
  f(x) = e^x at x = 1.0, true derivative = 2.7182818285

  (Using e^x rather than x^2: the central difference is EXACT for
   quadratics, because its error depends on the third derivative.
   A nice fact, and useless for showing the trade-off.)

           h    forward error    central error
       1e-01        1.406e-01        4.533e-03
       1e-02        1.364e-02        4.530e-05
       1e-03        1.360e-03        4.530e-07
       1e-04        1.359e-04        4.531e-09
       1e-05        1.359e-05        5.859e-11
       1e-06        1.359e-06        1.635e-10
       1e-07        1.399e-07        5.859e-11
       1e-08        6.603e-09        6.603e-09
       1e-09        2.154e-07        6.603e-09
       1e-10        1.548e-06        6.727e-07
       1e-11        3.263e-05        1.043e-05
       1e-12        4.323e-04        2.103e-04
       1e-13        4.559e-04        4.559e-04

  Best central-difference accuracy at h = 1e-05 (error 5.86e-11)

  TWO competing effects pull in opposite directions:
    large h -> the nudge is too coarse; you measure a chord across
               a curve, not the tangent. Error SHRINKS as h shrinks.
    tiny h  -> f(x+h) and f(x-h) agree in their leading digits, so
               subtracting them destroys precision. Error GROWS as
               h shrinks further.

  The minimum sits between them. Note the central difference beats
  the forward difference by several orders of magnitude in the
  useful range - which is why gradient checking uses it.

--------------------------------------------------------------------------
4. THE CHAIN RULE - rates multiply
--------------------------------------------------------------------------
  y = (3x + 1)^2  at x = 2.0

  Step 1: u = 3x + 1 = 7.0
  Step 2: y = u^2    = 49.0

  du/dx = 3           = 3.0
  dy/du = 2u = 2 x 7.0 = 14.0
  dy/dx = 14.0 x 3.0    = 42.0   <- rates multiply

  numerical check: 42.000000   error 8.97e-10

  A neural network is this same chain, thousands of links long.
  Backpropagation walks it backwards from the loss, multiplying
  local derivatives - which is why every parameter's gradient
  costs about one extra forward pass, not one pass each.

--------------------------------------------------------------------------
5. GRADIENTS - all the partial derivatives at once
--------------------------------------------------------------------------
  f(x, y) = x^2 + 3y   at (x, y) = (2.0, 5.0)
    df/dx = 2x = 4.0     (numerical 4.000000)
    df/dy = 3    = 3.0     (numerical 3.000000)
    gradient = [4. 3.], magnitude 5.0000

  The gradient points UPHILL. Proof - move a small step each way:
    f at the point              = 19.000000
    f after step ALONG gradient = 19.251600   (higher)
    f after step AGAINST it     = 18.751600   (lower)

  To minimise, always step AGAINST the gradient. That is the
  minus sign in  w <- w - alpha * grad.

--------------------------------------------------------------------------
6. THE SECTION 6 DESCENT, STEP BY STEP
--------------------------------------------------------------------------
  model: y_hat = w * x   with x = 2.0, true y = 10.0
  ideal w = 5.0

  Hand-derived gradient at w=1: -32.0
  numerical check             : -32.0000   error 7.46e-11

  Descending with learning rate 0.01:
    step           w          loss    gradient
       0    1.000000     64.000000    -32.0000
       1    1.320000     54.169600    -29.4400
       2    1.614400     45.849149    -27.0848
       3    1.885248     38.806720    -24.9180
       4    2.134428     32.846008    -22.9246
       5    2.363674     27.800861    -21.0906
       6    2.574580     23.530649    -19.4034
       7    2.768614     19.916341    -17.8511
       8    2.947125     16.857191    -16.4230
     ...
   final    5.000000   0.000000000

  Converged to w = 5, which is exactly y/x. The loss went to zero.

--------------------------------------------------------------------------
7. THE LEARNING RATE DECIDES HOW FAR TO TRUST THE GRADIENT
--------------------------------------------------------------------------
  Starting at w = 1 (loss 64.0). ONE step at each rate:

    learning rate       new w      new loss   outcome
            0.001      1.0320       62.9801   correct direction, but very slow
             0.01      1.3200       54.1696   good progress
              0.1      4.2000        2.5600   good progress
            0.125      5.0000        0.0000   EXACTLY optimal here
              0.2      7.4000       23.0400   overshot past the minimum, still improving
              0.5     17.0000      576.0000   DIVERGING - worse than we started

  Finding the divergence threshold empirically:
    diverges above a learning rate of about 0.2500

  For this quadratic the threshold is 2/(2*x^2) = 0.2500. Above it, each step
  overshoots further than it corrects, and the loss grows without
  bound. The gradient gave the direction; the rate was wrong.

--------------------------------------------------------------------------
8. VANISHING AND EXPLODING GRADIENTS
--------------------------------------------------------------------------
  A deep network multiplies one local derivative per layer.
  Same compounding arithmetic as M1-L11's p^n and M3-L05's underflow.

    per-layer derivative     10 layers       50 layers      100 layers
                     0.5     9.766e-04       8.882e-16       7.889e-31
                     0.9     3.487e-01       5.154e-03       2.656e-05
                     1.0     1.000e+00       1.000e+00       1.000e+00
                     1.1     2.594e+00       1.174e+02       1.378e+04
                     1.5     5.767e+01       6.376e+08       4.066e+17

  d = 0.5 over 100 layers -> 7.9e-31. The gradient reaching the
    first layer is effectively zero: it stops learning entirely.
    VANISHING GRADIENT.

  d = 1.5 over 100 layers -> 4.1e+17. The update is astronomically
    large, weights blow up, and the loss becomes nan.
    EXPLODING GRADIENT.

  Only d = 1.0 is stable at depth. ReLU activations, residual
  connections, normalisation layers and gradient clipping all
  exist to keep that product near 1 (M4-L10).

==========================================================================
```

### 7.3 Reading the result

**Section 3 contains a detail worth knowing.** The sweep deliberately uses `eˣ` rather than `x²`,
because **the central difference is exact for any quadratic** — its error term depends on the third
derivative, which is zero for `x²`. Run the sweep on `x²` and you get errors around `1e-15` at every
`h`, showing nothing.

With `eˣ` the real trade-off appears:

| h | Forward error | Central error |
|---|---|---|
| 1e-01 | 1.4e-01 | 4.5e-03 |
| 1e-05 | 1.4e-05 | **5.9e-11** ← best |
| 1e-10 | 1.5e-06 | 6.7e-07 |
| 1e-13 | 4.6e-04 | 4.6e-04 |

A clean U-shape with its minimum at **`h = 1e-5`**, exactly the value §5.1 recommends. Below that,
`f(x+h)` and `f(x−h)` agree in so many leading digits that subtracting them destroys precision, and
the estimate gets **worse** as `h` shrinks. Note also that the central difference beats the forward
difference by four to six orders of magnitude in the useful range — which is why gradient checking
uses it.

**Section 4** verifies the chain rule to within `9e-10`: `dy/du × du/dx = 14 × 3 = 42`, matching the
numerical estimate. Two local rates multiplied to give the end-to-end rate.

**Section 6** shows the descent converging from `w = 1` to **exactly 5.0** with the loss reaching
zero, and the hand-derived gradient of −32 confirmed numerically to `7e-11`. Watch the gradient
column shrink as `w` approaches the optimum — the steps get smaller automatically as the slope
flattens, which is why gradient descent slows down near a minimum without being told to.

**Section 7 is the learning-rate table, measured:**

| α | New loss | Outcome |
|---|---|---|
| 0.001 | 62.98 | Correct direction, very slow |
| 0.1 | 2.56 | Good progress |
| **0.125** | **0.00** | **Exactly optimal here** |
| 0.2 | 23.04 | Overshot past w=5, still improving |
| 0.5 | 576.00 | **Diverging** |

And the bisection search finds the divergence threshold at **exactly 0.25**, matching the analytic
`2/(2x²) = 0.25`. Note that 0.2 *overshoots* the minimum (landing at w=7.4 rather than 5) and is
still fine — overshooting and diverging are different things, and only the second is fatal.

**Section 8 is the same compounding arithmetic you have now met three times:**

| Per-layer derivative | 100 layers |
|---|---|
| 0.5 | **7.9e-31** — vanishing |
| 0.9 | 2.7e-05 |
| **1.0** | **1.0 — stable** |
| 1.1 | 1.4e+04 |
| 1.5 | **4.1e+17** — exploding |

Only `1.0` survives depth. At 0.5 the gradient arriving at the first layer is effectively zero and
that layer simply stops learning; at 1.5 the update is astronomically large and the loss becomes
`nan`.

This is the same product rule as M1-L11's `p^n` reliability and M3-L05's probability underflow. ReLU
activations, residual connections, normalisation layers and gradient clipping all exist for one
reason: **to keep that per-layer factor near 1.** You will see exactly where they sit in a
transformer in M4-L10.

**Verification:** confirm the central-difference optimum at `h = 1e-5`, the chain rule giving 42, the
descent reaching `w = 5.0` with zero loss, the divergence threshold at 0.25, and `0.5¹⁰⁰ ≈ 7.9e-31`.

---

## 8. Common mistakes and troubleshooting

1. **Getting the sign wrong.** Subtract the gradient to minimise; adding it maximises.
2. **Learning rate too large.** Loss increases or becomes `nan`.
3. **Learning rate too small.** Loss barely moves; it looks like nothing is learning.
4. **Numerical `h` too small.** Floating-point cancellation makes the estimate worse.
5. **Forgetting to zero gradients** between steps in a framework — they accumulate.
6. **Expecting a non-differentiable operation to have a gradient.** `argmax`, `round`, hard
   thresholds.
7. **Assuming zero gradient means a minimum.** It may be a saddle or a maximum.

| Symptom | Cause | Fix |
|---|---|---|
| Loss becomes `nan` | Exploding gradients, or `log(0)` | Lower the learning rate; clip gradients; clip probabilities |
| Loss flat from the start | Learning rate ~0, or vanishing gradients | Raise the rate; check activations; check the graph is connected |
| Loss oscillates wildly | Learning rate too high | Reduce it |
| Numerical and analytic gradients disagree | A derivation error, or a bad `h` | Use a central difference with `h ≈ 1e-5`; re-derive |
| Gradient is exactly zero everywhere | Graph disconnected, or a non-differentiable operation | Check for `argmax`/`detach`/`no_grad` |
| Loss decreases then increases | Overshooting near the minimum | Decay the learning rate |

---

## 9. Security, privacy, reliability and cost

- **Privacy.** Gradients leak information about the data that produced them. In federated learning,
  sharing gradients rather than data is **not** automatically private — training examples have been
  reconstructed from gradients. Treat gradients as sensitive as the data (M10-L06).
- **Reliability.** `nan` losses are almost always exploding gradients or `log(0)`. Gradient clipping
  and probability clipping are cheap insurance.
- **Cost.** Backpropagation costs roughly two forward passes, so a training step is ~3× the cost of
  inference on the same batch. That ratio is the basis of every fine-tuning cost estimate (M13-L05).
- **Reliability.** Gradient checking — comparing an analytic gradient to a numerical one — is the
  standard way to validate a custom operation before trusting it.

---

## 10. Exercises

### Exercise 1 — Beginner (~20 min)

Compute numerically with `h = 1e-5`, then verify against the analytic rule:

1. `f(x) = x²` at `x = 3`, `x = 0`, `x = −2`.
2. `f(x) = x³` at `x = 2`.
3. `f(x) = 5x + 3` at any `x`. Why is the answer the same everywhere?
4. `f(x) = ln(x)` at `x = 4`.
5. `f(x) = eˣ` at `x = 0` and `x = 1`. What is special about this function?

### Exercise 2 — Intermediate (~30 min)

1. For `f(x, y) = x² + 3xy + y²`, derive `∂f/∂x` and `∂f/∂y` by hand, then verify both numerically at
   `(1, 2)`.
2. State the gradient at that point and its magnitude.
3. Take one gradient-descent step with `α = 0.1` and confirm `f` decreased.
4. Repeat for 20 steps, printing the loss each time. Does it converge? To what?
5. Now use `α = 0.6` and report what happens. Explain the behaviour in terms of step size versus the
   local curvature.

### Exercise 3 — Challenge (~30 min)

1. Implement `gradient_check(f, grad_f, x)` comparing analytic and numerical gradients and returning
   the relative error. Test it on a correct gradient and on one with a deliberate sign error.
2. Sweep `h` from `1e-1` to `1e-12` for `f(x)=x²` at `x=3`. Plot or tabulate the error and identify
   the optimum. Explain both sides of the curve.
3. Build a chain of 50 multiplications with per-link derivative 0.5, then 1.5, then 1.0. Report the
   end-to-end gradient in each case and relate it to vanishing/exploding gradients.
4. Implement the §6 descent and run it to convergence from `w = 1`, `w = 100` and `w = −50`. Report
   the steps needed for each and whether they reach the same answer.
5. Find the learning rate at which the §6 problem diverges, to two decimal places, and explain why
   that threshold exists.

---

## 11. Quiz

**Q1.** What does a derivative measure?

- A. The value of the function.
- B. How much the output changes for a tiny change in the input.
- C. The area under the curve.
- D. The function's maximum.

**Q2.** `f(x) = x²`. What is `f'(3)`?

- A. 3  B. 6  C. 9  D. 2

**Q3.** The gradient of a loss with respect to a parameter is **negative**. What should you do?

- A. Decrease the parameter.
- B. Increase it — a negative gradient means increasing the parameter decreases the loss.
- C. Leave it; the gradient is invalid.
- D. Set it to zero.

**Q4.** What does the gradient vector point toward?

- A. The minimum.
- B. The direction of steepest increase — which is why you step in the opposite direction to
  minimise.
- C. The origin.
- D. The nearest data point.

**Q5.** `y = (3x + 1)²`. Using the chain rule, what is `dy/dx` at `x = 2`?

- A. 6  B. 14  C. 42  D. 49

**Q6.** Why does backpropagation make deep learning feasible?

- A. It makes the model smaller.
- B. The chain rule computed backwards gives every parameter's gradient for roughly the cost of
  one extra forward pass, instead of one pass per parameter.
- C. It removes the need for a loss function.
- D. It parallelises across GPUs.

**Q7.** A loss becomes `nan` during training. What is the most likely cause?

- A. Too little data.
- B. Exploding gradients, or a `log(0)` — the learning rate is likely too high.
- C. The model has converged.
- D. Vanishing gradients.

**Q8.** Why can `h` not be made arbitrarily small in a numerical derivative?

- A. It would take too long.
- B. Below roughly `1e-8`, floating-point cancellation in `f(x+h) − f(x)` dominates and the estimate
  gets worse.
- C. Small values are rounded up.
- D. It can be; smaller is always better.

**Q9.** Why do models output continuous probabilities rather than a discrete decision?

- A. Probabilities are easier to store.
- B. `argmax` and hard thresholds are not differentiable, so no gradient could flow back through
  them to train the model.
- C. Discrete outputs are less accurate.
- D. It is a convention.

**Q10.** *(Written, rubric-graded.)* In under 80 words, explain to a colleague what "the gradient" is
and why training subtracts it.

---

## 12. Revision notes

- **A derivative is a ratio: output change ÷ input change, as the change shrinks to zero.**
- Numerically: `(f(x+h) − f(x−h)) / (2h)`. **`h ≈ 1e-5`** — smaller is not better, because
  floating-point cancellation takes over below ~`1e-8`.
- Power rule: `xⁿ → n·xⁿ⁻¹`. `x² → 2x`. `eˣ → eˣ`. `ln(x) → 1/x`.
- **Partial derivative:** differentiate one variable, hold the rest constant. **Gradient** = the
  vector of all of them, pointing **uphill**.
- **To minimise, step against the gradient:** `w ← w − α·∇L`.
- **Chain rule: rates multiply.** `dy/dx = (dy/du)(du/dx)`. `(3x+1)²` at x=2 gives 14 × 3 = **42**.
- **Backpropagation is the chain rule applied backwards**, giving every gradient for ~2 forward
  passes rather than one per parameter. That is why deep learning is affordable.
- **Vanishing** (many terms < 1) and **exploding** (many > 1) gradients are the same compounding
  arithmetic as `p^n`.
- **Gradient checking** — compare analytic against numerical — catches sign errors.
- Non-differentiable operations (`argmax`, `round`, hard thresholds) block gradients. Hence
  continuous probabilities.
- **Zero gradient ≠ minimum.** It may be a saddle or a maximum.

---

## 13. Completion checklist

- [ ] I can explain a derivative as a nudge ratio.
- [ ] I computed derivatives numerically and matched the analytic rules.
- [ ] I found the optimal `h` empirically and can explain both sides of the curve.
- [ ] I applied the chain rule by hand and verified it numerically.
- [ ] I ran the §6 descent and saw the loss fall.
- [ ] I found the learning rate at which it diverges.
- [ ] I can explain why backprop is ~2 passes rather than one per parameter.
- [ ] I scored 7/10 on the quiz.

---

## 14. References

- 3Blue1Brown, "Essence of Calculus" — the clearest visual introduction.
  <https://www.3blue1brown.com/topics/calculus> `[UNVERIFIED]`
- Karpathy, "The spelled-out intro to neural networks and backpropagation" (micrograd).
  <https://karpathy.ai/zero-to-hero.html> `[UNVERIFIED]`

---

## 15. Next lesson

→ [M3-L07 — Loss Functions and Gradient Descent](M3-L07-loss-gradient-descent.md)

You can compute a gradient. Next: the full optimisation loop — which loss to choose, how the learning
rate behaves, and what a training curve is actually telling you.
