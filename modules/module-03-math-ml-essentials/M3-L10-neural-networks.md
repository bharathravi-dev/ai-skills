# M3-L10 — Neural Networks: Weights, Biases, Activations

| | |
|---|---|
| **Lesson ID** | M3-L10 |
| **Difficulty** | 2 (Core) |
| **Estimated study time** | 2.0 hours |
| **Prerequisites** | [M3-L09](M3-L09-logistic-regression.md) |

---

## 1. Learning objectives

1. **Describe** a neural network as a stack of linear layers with non-linearities between them.
2. **Explain**, with proof, why stacking linear layers without activations gains nothing.
3. **Compute** a forward pass through a small network by hand.
4. **Compare** the common activation functions and state when each is appropriate.
5. **Count** a network's parameters and **estimate** its memory footprint.

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **Neuron / unit** | One weighted sum plus a bias, followed by an activation. |
| **Layer** | A group of units applied to the same input. |
| **Hidden layer** | Any layer between the input and the output. |
| **Weight matrix** `W` | All of a layer's weights, shape `(in_features, out_features)`. |
| **Bias vector** `b` | One bias per output unit. |
| **Activation function** | A non-linear function applied after the weighted sum. |
| **ReLU** | `max(0, x)`. The standard hidden activation. |
| **Forward pass** | Computing the output from the input. |
| **Feed-forward / MLP** | A network where data flows one way through stacked layers. |
| **Width** | Units per layer. **Depth** — number of layers. |
| **Representation** | The intermediate vector a hidden layer produces. |
| **Universal approximation** | The result that a wide enough one-hidden-layer network can approximate any continuous function. |
| **Dead ReLU** | A unit stuck outputting zero for every input, so it never learns. |

---

## 3. Plain-language explanation

A neural network is **logistic regression, stacked, with a non-linearity between each layer**.

One layer does exactly what M3-L09 did — a weighted sum plus a bias:

```
z = W·x + b
```

The only new idea is doing this several times, applying a non-linear function between each:

```
h₁ = ReLU(W₁·x  + b₁)      hidden layer 1
h₂ = ReLU(W₂·h₁ + b₂)      hidden layer 2
y  = softmax(W₃·h₂ + b₃)   output layer
```

That is the whole architecture. Everything in Module 4 is this pattern with specific choices about
what the layers do.

**Why the non-linearity is essential.** Without it, stacking gains you *nothing at all*:

```
W₂(W₁x + b₁) + b₂  =  (W₂W₁)x + (W₂b₁ + b₂)  =  W'x + b'
```

Two linear layers collapse into **one** linear layer. A hundred would too. Without an activation
function, a hundred-layer network has exactly the expressive power of logistic regression — and the
lab demonstrates this numerically.

**The activation is what makes depth mean something.** It breaks the collapse, so each layer can
build on the previous one's output rather than being absorbed into it.

---

## 4. Analogy

**An assembly line.** Each station (layer) transforms what it receives and passes it on. Early
stations produce simple parts; later ones assemble those into complex ones.

### Where the analogy breaks

1. **A factory's stations are designed by people. A network's are learned** — nobody specifies what
   hidden unit 47 detects, and usually nobody can say afterwards.
2. **Assembly stations are independent. Layers are trained jointly**, so a change in layer 1 alters
   what layer 3 should do. There is no "fix one station in isolation".
3. **The analogy implies interpretable intermediate parts.** Some are; most are not. Individual
   hidden units rarely correspond to anything nameable.
4. **A factory without a transformation step still moves goods along. A network without
   activations is literally equivalent to a single layer** — the stations do not just add less, they
   add *nothing*.

---

## 5. Detailed technical explanation

### 5.1 One layer, in matrix form

For a batch of `n` samples with `d_in` features producing `d_out` outputs:

$$H = XW + b$$

| Object | Shape |
|---|---|
| `X` | `(n, d_in)` |
| `W` | `(d_in, d_out)` |
| `b` | `(d_out,)` — broadcast across rows |
| `H` | `(n, d_out)` |

```python
H = X @ W + b                # (n, d_in) @ (d_in, d_out) -> (n, d_out)
```

**Shape errors here are almost always a transposed weight matrix.** Check `W.shape[0] == X.shape[1]`
before anything else — the M3-L01 rule applied to layers.

### 5.2 Why activations are mandatory

The collapse proof again, with attention to what it means:

$$W_2(W_1x + b_1) + b_2 = \underbrace{(W_2W_1)}_{\text{one matrix}}x + \underbrace{(W_2b_1 + b_2)}_{\text{one vector}}$$

The composition of two linear maps is a linear map. **No number of layers changes this.** The lab
constructs a 5-layer linear network, multiplies its weight matrices into a single equivalent matrix,
and shows the outputs match to floating-point precision.

The practical consequence: if you forget the activation function, your deep network trains to exactly
the performance of logistic regression, and nothing errors. It just quietly cannot learn anything a
straight line could not.

### 5.3 The activation functions

| Function | Formula | Range | Notes |
|---|---|---|---|
| **ReLU** | `max(0, x)` | [0, ∞) | The default for hidden layers. Cheap; no saturation for positive inputs |
| **Leaky ReLU** | `max(0.01x, x)` | (−∞, ∞) | Fixes dead units |
| **GELU** | smooth, ReLU-like | (−0.17, ∞) | Standard in transformers (M4-L10) |
| **Sigmoid** | `1/(1+e⁻ˣ)` | (0, 1) | **Output only**, for binary classification |
| **Tanh** | `(eˣ−e⁻ˣ)/(eˣ+e⁻ˣ)` | (−1, 1) | Zero-centred; largely superseded |
| **Softmax** | M3-L09 §5.3 | sums to 1 | **Output only**, multi-class |

**Why ReLU displaced sigmoid for hidden layers**, which is worth understanding rather than accepting:

| | Sigmoid | ReLU |
|---|---|---|
| Derivative | ≤ 0.25, → 0 at both extremes | **exactly 1** for x > 0 |
| Vanishing gradients | Severe at depth | Largely avoided |
| Cost | `exp` per unit | A comparison |

Recall M3-L06 §5.5: gradients multiply through layers. With sigmoid's maximum derivative of 0.25,
ten layers give at best `0.25¹⁰ ≈ 10⁻⁶` — the gradient reaching the first layer is effectively zero.
**ReLU's derivative is exactly 1 for positive inputs, so the product does not shrink.** That single
property is what made networks deeper than a few layers trainable.

**The cost: dead ReLUs.** If a unit's input is negative for every training example, its output is
always 0, its gradient is always 0, and it never recovers. It is permanently dead. Leaky ReLU
(`max(0.01x, x)`) keeps a small gradient alive to prevent this.

**Choosing:** ReLU (or GELU) for hidden layers; sigmoid for binary output; softmax for multi-class
output; **nothing** for a regression output — squashing it would cap your predictions.

### 5.4 A complete network

```python
def forward(X, W1, b1, W2, b2, W3, b3):
    h1 = np.maximum(0, X @ W1 + b1)     # hidden layer 1, ReLU
    h2 = np.maximum(0, h1 @ W2 + b2)    # hidden layer 2, ReLU
    logits = h2 @ W3 + b3               # output layer, NO activation
    return logits                        # softmax applied by the loss function
```

**Note the output layer has no activation.** Frameworks' cross-entropy losses expect *logits* and
apply softmax internally, for the numerical-stability reasons of M3-L09 §5.3. Applying softmax
yourself and then using such a loss applies it twice — a real and quiet bug that degrades training
without erroring.

### 5.5 Counting parameters

For a layer from `d_in` to `d_out`: `d_in × d_out` weights plus `d_out` biases.

A network 784 → 128 → 64 → 10:

| Layer | Weights | Biases | Total |
|---|---|---|---|
| 784 → 128 | 100,352 | 128 | 100,480 |
| 128 → 64 | 8,192 | 64 | 8,256 |
| 64 → 10 | 640 | 10 | 650 |
| | | **Total** | **109,386** |

At `float32` (4 bytes) that is 437,544 bytes — about **427 KiB**.

**This arithmetic scales directly to the models you will use.** An 8-billion-parameter model needs
8e9 × 4 = **32 GB** in `float32`, or **16 GB** in `float16`. That is the calculation behind
"will this model fit on this GPU?", and quantisation (M4-L17) is the technique for shrinking it.

**Training needs roughly 3–4× the parameter memory**, because you also store gradients and optimiser
state (M3-L12). This is why fine-tuning a model is far more memory-hungry than running it, and why
LoRA exists (M13-L05).

### 5.6 Width, depth and capacity

**Universal approximation** says a single hidden layer, made wide enough, can approximate any
continuous function to arbitrary precision. It is a real theorem and it is nearly useless in practice
— it says nothing about *how wide*, or whether training could ever find those weights.

**Depth is usually more efficient than width.** Some functions need exponentially many units in one
layer but only linearly many across several. Deep networks reuse intermediate representations;
shallow ones cannot.

**But more capacity is not better** (M1-L08). More parameters means more ability to memorise, and the
M1-L08 lab measured exactly what that does to validation error.

**Practical starting point:** 2–3 hidden layers, width comparable to the input dimension, then adjust
based on the training curve. Underfitting → wider or deeper. Overfitting → more data, or
regularisation, or smaller.

### 5.7 Initialisation

**Not all zeros.** Every unit would compute the same thing, receive the same gradient, and remain
identical forever — the network would have one effective unit per layer (M3-L07 §5.6).

**Not too large.** Activations grow through layers and saturate or explode.

**The standard is scale-aware.** He initialisation (for ReLU) draws from a normal distribution with
variance `2/d_in`, chosen so the activations' variance stays roughly constant through the layers.
Xavier/Glorot does the equivalent for tanh.

The point is the same one as M3-L06 §5.5: keep the per-layer factor near 1, so signals neither
vanish nor explode as depth grows.

### 5.8 Assumptions and limitations

- A network is only as good as its features and labels. It cannot recover information that is not
  there (M1-L08 §5.4).
- On tabular data, gradient-boosted trees frequently beat neural networks (M1-L01 §5.1).
- Individual hidden units are rarely interpretable.
- More layers means more compounding-gradient risk, which is what normalisation and residual
  connections address (M4-L10).

---

## 6. Worked example — a forward pass by hand

A tiny network: 2 inputs → 2 hidden units (ReLU) → 1 output (sigmoid).

**The parameters:**

```
W1 = [[ 0.5, -0.3],        b1 = [0.1, 0.2]
      [ 0.8,  0.6]]

W2 = [[1.2],               b2 = [-0.4]
      [-0.7]]
```

`W1` is `(2, 2)` — 2 inputs, 2 hidden units. `W2` is `(2, 1)` — 2 hidden units, 1 output.

**Input:** `x = [1.0, 2.0]`

**Step 1 — hidden layer pre-activation.** `z₁ = x·W1 + b1`

- Hidden unit 1: `1.0 × 0.5 + 2.0 × 0.8 + 0.1 = 0.5 + 1.6 + 0.1 = **2.2**`
- Hidden unit 2: `1.0 × (−0.3) + 2.0 × 0.6 + 0.2 = −0.3 + 1.2 + 0.2 = **1.1**`

`z₁ = [2.2, 1.1]`

**Step 2 — ReLU.** `h₁ = max(0, z₁) = [2.2, 1.1]` — both positive, so both pass through unchanged.

**Step 3 — output pre-activation.** `z₂ = h₁·W2 + b2`

`= 2.2 × 1.2 + 1.1 × (−0.7) + (−0.4) = 2.64 − 0.77 − 0.4 = **1.47**`

**Step 4 — sigmoid.** `σ(1.47) = 1 / (1 + e^−1.47) = 1 / (1 + 0.2299) = **0.813**`

An 81.3% probability.

**Step 5 — a second input, to see ReLU bite.** `x = [-2.0, 0.5]`

- Hidden 1: `−2.0 × 0.5 + 0.5 × 0.8 + 0.1 = −1.0 + 0.4 + 0.1 = **−0.5**`
- Hidden 2: `−2.0 × (−0.3) + 0.5 × 0.6 + 0.2 = 0.6 + 0.3 + 0.2 = **1.1**`

`z₁ = [−0.5, 1.1]` → **ReLU zeroes the first unit**: `h₁ = [0.0, 1.1]`

`z₂ = 0.0 × 1.2 + 1.1 × (−0.7) − 0.4 = **−1.17**` → `σ(−1.17) = **0.237**`

**Step 6 — what just happened, and why it matters.** For this input, hidden unit 1 contributed
*nothing*. Its weight `1.2` was multiplied by zero. **The network used a different subset of its
units for this input than for the last one.**

That is the non-linearity doing its work. A linear model applies the same fixed formula to every
input. A ReLU network effectively selects which units participate, per input — which is how it
represents different rules in different regions of the input space, and why it can separate things a
straight line cannot.

**Step 7 — and the gradient consequence.** Because hidden unit 1 output zero, its gradient for this
example is also zero: it learns nothing from it. If that happened for *every* training example, the
unit would be permanently dead (§5.3).

**Step 8 — parameter count.** `W1`: 4 weights + 2 biases = 6. `W2`: 2 weights + 1 bias = 3.
**Total: 9 parameters.** A model you can hold entirely in your head — and the exact same structure as
one with 8 billion.

---

## 7. Practical activity

**File:** [`labs/m3/l10_neural_network.py`](../../labs/m3/l10_neural_network.py)

**Requires the venv:**

```bash
source .venv/bin/activate
python labs/m3/l10_neural_network.py
```

Verifies the §6 forward pass, **proves numerically that stacked linear layers collapse to one**,
compares activations and their derivatives, trains a network on data that logistic regression cannot
separate, demonstrates dead ReLUs and the all-zeros initialisation failure, and computes parameter
counts and memory from a tiny network up to 8 billion parameters.

### 7.1 Important lines

| Construct | Why |
|---|---|
| `X @ W1 + b1` | One layer. Check `W.shape[0] == X.shape[1]`. |
| `np.maximum(0, z)` | ReLU. |
| `W1 @ W2 @ W3` | Collapsing a linear stack into one equivalent matrix. |
| `rng.normal(scale=np.sqrt(2/d_in))` | He initialisation. |
| `params * 4 / 1e9` | Memory in GB at `float32`. |

### 7.2 Expected output

`[EXECUTED]` 2026-09-08 with numpy 2.5.3, Python 3.12.3:

```
==========================================================================
NEURAL NETWORKS: WEIGHTS, BIASES, ACTIVATIONS
==========================================================================

--------------------------------------------------------------------------
1. THE SECTION 6 FORWARD PASS, VERIFIED
--------------------------------------------------------------------------
  input x = [1.0, 2.0]
    hidden pre-activation z1 = [2.2 1.1]
    after ReLU            h1 = [2.2 1.1]
    output pre-activation z2 = 1.4700
    sigmoid                  = 0.8131

  input x = [-2.0, 0.5]
    hidden pre-activation z1 = [-0.5  1.1]
    after ReLU            h1 = [0.  1.1]   <- unit 1 ZEROED
    output pre-activation z2 = -1.1700
    sigmoid                  = 0.2369

  For the second input, hidden unit 1 contributed NOTHING - its
  weight of 1.2 was multiplied by zero. The network used a
  DIFFERENT SUBSET of its units for the two inputs.

  That is the non-linearity working. A linear model applies one
  fixed formula to every input; a ReLU network selects which units
  participate, per input.

  Finding an input that zeroes BOTH units:
    x = [-5.0, -5.0]     z1 = [-6.4 -1.3]          BOTH zeroed, output 0.4013
    x = [-1.0, -1.0]     z1 = [-1.2 -0.1]          BOTH zeroed, output 0.4013
  When both are zeroed the output is always sigmoid(b2) = 0.4013,
  regardless of the input. The network has nothing left to say.

--------------------------------------------------------------------------
2. THE COLLAPSE PROOF - stacked linear layers ARE one layer
--------------------------------------------------------------------------
  A 5-layer network: 6 -> 32 -> 24 -> 16 -> 8 -> 3
  Total parameters: 1,579

  5-layer output (first row): [-2.830344 -3.396468 -7.915263]
  1-layer equivalent        : [-2.830344 -3.396468 -7.915263]
  identical? True   max difference 9.33e-15

  The collapsed layer is a single (6, 3) matrix plus a
  (3,) bias - 21 numbers replacing 1,579.

  NOW ADD ReLU between the layers:
  with ReLU (first row)     : [ 0.554406 -0.763544 -0.108675]
  same as the linear version? False

  Without activations the depth is DECORATION. It fails silently:
  no error, no warning, just a very expensive logistic regression.

--------------------------------------------------------------------------
3. ACTIVATIONS AND THEIR DERIVATIVES
--------------------------------------------------------------------------
        z     ReLU   ReLU_grad    sigmoid  sigmoid_grad      tanh
     -6.0     0.00        0.00     0.0025        0.0025   -1.0000
     -2.0     0.00        0.00     0.1192        0.1050   -0.9640
     -0.5     0.00        0.00     0.3775        0.2350   -0.4621
      0.0     0.00        0.00     0.5000        0.2500    0.0000
      0.5     0.50        1.00     0.6225        0.2350    0.4621
      2.0     2.00        1.00     0.8808        0.1050    0.9640
      6.0     6.00        1.00     0.9975        0.0025    1.0000

  THE DECISIVE COLUMN is ReLU_grad vs sigmoid_grad.

    layers     ReLU (grad=1)    sigmoid (grad<=0.25)
         1               1.0                2.50e-01
         5               1.0                9.77e-04
        10               1.0                9.54e-07
        20               1.0                9.09e-13
        50               1.0                7.89e-31

  Sigmoid's BEST case is 0.25 per layer. Ten layers gives 1e-6 -
  the gradient reaching the first layer is effectively zero and it
  stops learning. ReLU's derivative is exactly 1 for positive
  inputs, so the product does not shrink at all.

  That single property is what made networks deeper than a few
  layers trainable (M3-L06).

--------------------------------------------------------------------------
4. WHAT A HIDDEN LAYER BUYS: DATA A LINE CANNOT SPLIT
--------------------------------------------------------------------------
  800 points. Class = 1 when both coordinates share a sign
  (an XOR pattern: two opposite quadrants against two others).

  logistic regression (no hidden layer) : accuracy 0.451
  network with 8 hidden ReLU units       : accuracy 0.995

  Logistic regression scores near chance because NO straight line
  separates opposite quadrants. Its decision boundary is a line,
  and the problem is not linearly separable (M3-L09).

  The hidden layer builds intermediate features that ARE linearly
  separable in the space it constructs. That is what depth buys,
  and it is impossible without the non-linearity.

--------------------------------------------------------------------------
5. TWO FAILURES: ZERO INIT AND DEAD ReLUs
--------------------------------------------------------------------------
  A) ALL-ZERO INITIALISATION
    hidden weights after 500 steps:
      unit 1: [0. 0. 0.]
      unit 2: [0. 0. 0.]
      unit 3: [0. 0. 0.]
      unit 4: [0. 0. 0.]
    all units identical? True
    Every unit computed the same output, received the same
    gradient, and stayed identical. Four units, one effective unit.

  B) DEAD ReLU - a unit initialised with a very negative bias
    unit 1 active on 54.7% of inputs
    unit 2 active on 0.0% of inputs   <- DEAD
    unit 2 gradient is (z > 0) = 0.0% of the time, i.e. never.
    It outputs 0 for every input, receives no gradient, and can
    never recover. Leaky ReLU keeps a small gradient alive:
    with Leaky ReLU, unit 2 output range: [-0.521, -0.481] - non-zero, so
    a gradient still flows and the unit can recover.

--------------------------------------------------------------------------
6. PARAMETERS AND MEMORY - the arithmetic that sizes a GPU
--------------------------------------------------------------------------
  architecture                                  layers    parameters
  the section 6 toy                        2 -> 2 -> 1             9
  small MLP                     784 -> 128 -> 64 -> 10       109,386
  larger MLP            784 -> 512 -> 256 -> 128 -> 10       567,434

  Breakdown for 784 -> 128 -> 64 -> 10:
    layer              weights    biases       total
    784 -> 128         100,352       128     100,480
    128 -> 64            8,192        64       8,256
    64 -> 10               640        10         650
    TOTAL                                    109,386
    float32 memory: 427.3 KB

  Scaling the SAME arithmetic to real models:
      parameters     float32     float16      int8   training (~4x fp32)
       1,000,000        0.0G        0.0G      0.0G                  0.0G
     100,000,000        0.4G        0.2G      0.1G                  1.6G
   7,000,000,000       28.0G       14.0G      7.0G                112.0G
   8,000,000,000       32.0G       16.0G      8.0G                128.0G
  70,000,000,000      280.0G      140.0G     70.0G               1120.0G

  An 8B model needs 32 GB in float32 - more than a 24 GB GPU has.
  At float16 it is 16 GB and fits. That single calculation is why
  quantisation exists (M4-L17), and why FINE-TUNING an 8B model
  needs ~128 GB while running it needs 16 - hence LoRA (M13-L05).

==========================================================================
```

### 7.3 Reading the result

**Section 1 confirms every hand-computed value** — `z1 = [2.2, 1.1]`, output 0.8131; then
`z1 = [-0.5, 1.1]` with unit 1 zeroed and output 0.2369.

The search for an input zeroing *both* units is the interesting part: whenever both are dead, the
output is **0.4013 regardless of the input** — because it is just `σ(b₂)`. The network has literally
nothing left to say. That is what a fully saturated region looks like.

**Section 2 is the proof, executed:**

```
A 5-layer network: 6 -> 32 -> 24 -> 16 -> 8 -> 3
Total parameters: 1,579

5-layer output : [-2.830344 -3.396468 -7.915263]
1-layer equiv  : [-2.830344 -3.396468 -7.915263]
identical? True   max difference 9.33e-15
```

**1,579 parameters collapsed into 21** — a single `(6, 3)` matrix plus a `(3,)` bias — with
byte-identical outputs. Adding ReLU between the layers immediately produces something no single
linear layer can.

The warning matters: this failure is **completely silent**. No error, no warning, no shape mismatch.
A twenty-layer network missing its activations trains successfully to exactly the performance of
logistic regression, and the only symptom is that it never gets better than a straight line.

**Section 3 puts numbers on the ReLU argument:**

| Layers | ReLU (grad = 1) | Sigmoid (grad ≤ 0.25) |
|---|---|---|
| 10 | 1.0 | **9.54e-07** |
| 20 | 1.0 | 9.09e-13 |
| 50 | 1.0 | **7.89e-31** |

Sigmoid's *best possible* case is 0.25 per layer, and that is only at `z = 0`. Ten layers reduces the
gradient reaching the first layer to about **one in a million**; fifty layers to 1e-31. ReLU's
derivative is exactly 1 for positive inputs, so the product does not shrink at all.

This is the same table as M3-L06 §5.5, now attached to a specific design decision — and it is why
deep networks became trainable.

**Section 4 shows what depth actually buys:**

```
logistic regression (no hidden layer) : accuracy 0.451
network with 8 hidden ReLU units      : accuracy 0.995
```

Logistic regression scores **below chance** on the XOR pattern, because no straight line separates
opposite quadrants — its decision boundary is a line and the problem is not linearly separable. Eight
hidden units reach 99.5%.

The hidden layer constructs a representation in which the problem *is* linearly separable. That is
the entire value of depth, and it is impossible without the non-linearity from section 2.

**Section 5** shows all four units under zero initialisation remaining **exactly `[0, 0, 0]`** after
500 steps — identical forever, four units doing the work of one. And a unit with a −50 bias active on
**0.0% of inputs**: it outputs zero always, receives gradient never, and cannot recover. Leaky ReLU
keeps its output in `[-0.521, -0.481]`, non-zero, so a gradient still flows.

**Section 6 is the arithmetic that decides your hardware:**

| Parameters | float32 | float16 | int8 | Training (~4× fp32) |
|---|---|---|---|---|
| 8 billion | **32.0 GB** | **16.0 GB** | 8.0 GB | **128 GB** |
| 70 billion | 280 GB | 140 GB | 70 GB | 1,120 GB |

An 8B model does **not** fit on a 24 GB GPU in `float32`, and does fit in `float16`. Fine-tuning the
same model needs roughly **128 GB** — eight times what inference needs — because gradients and
optimiser state must be stored alongside the weights.

Those two facts are the entire motivation for quantisation (M4-L17) and for LoRA (M13-L05), and you
can now derive both from `parameters × bytes`.

**Verification:** confirm output 0.8131 for the first input, the collapse matching to ~1e-15, sigmoid
reaching 9.5e-07 at 10 layers, XOR accuracies of roughly 0.45 and 0.99, and 109,386 parameters for
784→128→64→10.

---

## 8. Common mistakes and troubleshooting

1. **Forgetting the activation.** Silently equivalent to logistic regression.
2. **Applying softmax then using a loss that also applies it.**
3. **Squashing a regression output**, capping predictions at the activation's range.
4. **All-zero initialisation.**
5. **Transposed weight matrices.** Check `W.shape[0] == X.shape[1]`.
6. **Assuming more layers is better.** More capacity means more overfitting (M1-L08).
7. **Not standardising inputs.** The M3-L07 ravine, per layer.
8. **Ignoring dead ReLUs** when a large fraction of units output zero for everything.

| Symptom | Cause | Fix |
|---|---|---|
| Deep network performs like logistic regression | Missing activations | Add them; check `forward` |
| Loss `nan` | Exploding activations or gradients | Scale-aware init; standardise inputs; lower α |
| Many units always output 0 | Dead ReLUs | Leaky ReLU; lower α; better init |
| All units learn identically | Zero initialisation | Random init |
| `ValueError: matmul mismatch` | Transposed weights | Check the layer shapes |
| Training loss falls, validation rises | Too much capacity | Fewer parameters; more data; regularise |
| Out of GPU memory | Parameter + gradient + optimiser state | Smaller batch; smaller model; quantise (M4-L17) |

---

## 10. Exercises

### Exercise 1 — Beginner (~20 min)

Using the §6 network, by hand:

1. Forward pass for `x = [0.0, 0.0]`. What is the output, and why is it not 0.5?
2. Forward pass for `x = [3.0, -1.0]`. Which hidden units survive ReLU?
3. Find an input for which **both** hidden units are zeroed. What does the network output then, and
   why is it the same for every such input?
4. Count the parameters and confirm 9.
5. Replace ReLU with the identity and compute the equivalent single-layer weights.

### Exercise 2 — Intermediate (~30 min)

1. Implement the §6 forward pass in NumPy and verify all the hand-computed values.
2. Build a 5-layer network with **no** activations. Multiply its weight matrices together and show
   the composite single layer produces identical outputs.
3. Add ReLU between the layers and show the outputs now differ from any single linear layer.
4. Count parameters for 784 → 256 → 128 → 10 and compute the `float32` memory.
5. Compute the memory for 8B parameters at `float32`, `float16` and `int8`, and state which fit on a
   24 GB GPU for inference.

### Exercise 3 — Challenge (~30 min)

1. Generate XOR-like data (two classes in opposite corners). Fit logistic regression and report the
   accuracy. Explain the result geometrically.
2. Train a 2-hidden-unit network on the same data and report the accuracy. Explain what the hidden
   layer bought you.
3. Initialise every weight to zero and train. Show that all hidden units remain identical, and
   demonstrate it by printing their weights.
4. Construct a dead ReLU deliberately: initialise a unit's bias very negative. Show it outputs zero
   for every input and never recovers. Then fix it with Leaky ReLU.
5. Sweep hidden width from 1 to 64 on a fixed dataset. Report training and validation accuracy at
   each and identify where overfitting begins (M1-L08).

---

## 11. Quiz

**Q1.** What happens if you stack linear layers with no activation between them?

- A. The network becomes more expressive with each layer.
- B. It collapses algebraically to a single linear layer — no number of layers adds any expressive
  power.
- C. Training fails with an error.
- D. Gradients explode.

**Q2.** Why did ReLU largely replace sigmoid in hidden layers?

- A. It is more accurate.
- B. Its derivative is exactly 1 for positive inputs, so gradients do not shrink through depth —
  whereas sigmoid's maximum derivative of 0.25 vanishes rapidly when multiplied across layers.
- C. It outputs probabilities.
- D. It is smoother.

**Q3.** In §6 step 5, ReLU zeroed hidden unit 1. What is the consequence for that example?

- A. The network errors.
- B. That unit contributes nothing to the output, and receives no gradient from that example.
- C. The output becomes 0.5.
- D. The other unit is also zeroed.

**Q4.** What is a dead ReLU?

- A. A unit with zero weight.
- B. A unit whose input is negative for every training example, so it always outputs 0, always has
  zero gradient, and can never recover.
- C. A unit that has converged.
- D. A removed layer.

**Q5.** A network is 784 → 128 → 64 → 10. How many parameters?

- A. 986  B. 109,386  C. 100,352  D. 8,192

**Q6.** Why does the output layer usually have no activation in the code?

- A. It is a bug.
- B. Framework cross-entropy losses expect logits and apply softmax internally for numerical
  stability — applying it yourself would apply it twice.
- C. Output layers cannot have activations.
- D. It saves memory.

**Q7.** How much memory does an 8-billion-parameter model need in `float32`?

- A. 8 GB  B. 16 GB  C. 32 GB  D. 4 GB

**Q8.** Why must weights not be initialised to zero?

- A. Zero is an invalid value.
- B. Every unit would compute the same output, receive the same gradient, and stay identical forever —
  the layer would have one effective unit.
- C. The loss would be zero.
- D. It causes overflow.

**Q9.** What does the universal approximation theorem actually tell you in practice?

- A. That one wide hidden layer is always the best choice.
- B. Very little — it guarantees such a network *exists* but says nothing about how wide, or whether
  training could find it.
- C. That deeper is always better.
- D. That neural networks always converge.

**Q10.** *(Written, rubric-graded.)* In under 80 words, explain to a colleague why their 20-layer
network performs no better than logistic regression, given that they forgot the activations.

---

## 12. Revision notes

- A network is **stacked linear layers with a non-linearity between them**. One layer is `XW + b`,
  exactly M3-L09.
- **Without activations, layers collapse:** `W₂(W₁x+b₁)+b₂ = W'x + b'`. A hundred layers = one layer.
  **This fails silently.**
- Shapes: `X (n, d_in)` · `W (d_in, d_out)` · `b (d_out,)` · `H (n, d_out)`. Check
  `W.shape[0] == X.shape[1]`.
- **ReLU for hidden layers** — derivative exactly 1 for x > 0, so gradients survive depth.
  Sigmoid's max derivative is 0.25, giving `0.25¹⁰ ≈ 1e-6`.
- **Dead ReLU:** always-negative input ⇒ always 0 output ⇒ zero gradient ⇒ never recovers. Leaky
  ReLU fixes it.
- Output activation: **sigmoid** (binary) · **softmax** (multi-class) · **none** (regression).
  In code, output logits and let the loss apply softmax.
- **Parameters** = `d_in × d_out + d_out` per layer. **Memory** = params × bytes. 8B × 4 = **32 GB**
  in float32; **training needs 3–4× that.**
- **Universal approximation is nearly useless in practice.** Depth is usually more efficient than
  width; more capacity means more overfitting.
- **Never initialise to zero.** Use scale-aware init (He for ReLU) to keep the per-layer factor near 1.

---

## 13. Completion checklist

- [ ] I computed the §6 forward pass by hand, both inputs.
- [ ] I can state the collapse proof and reproduced it numerically.
- [ ] I can explain ReLU's advantage in terms of gradient products.
- [ ] I found an input that zeroes both hidden units.
- [ ] I demonstrated a dead ReLU and the zero-initialisation failure.
- [ ] I counted parameters and computed memory up to 8B.
- [ ] I trained a network on data logistic regression cannot separate.
- [ ] I scored 7/10 on the quiz.

---

## 14. References

- Goodfellow, Bengio & Courville, *Deep Learning*, Ch. 6.
  <https://www.deeplearningbook.org/> `[UNVERIFIED]`
- He et al., "Delving Deep into Rectifiers" (2015) — He initialisation. `[UNVERIFIED]`

---

## 15. Next lesson

→ [M3-L11 — Backpropagation: a Full Worked Example](M3-L11-backpropagation.md)

You can run a network forward. Next: running it backwards — the complete gradient calculation for
this exact network, every number computed by hand.
