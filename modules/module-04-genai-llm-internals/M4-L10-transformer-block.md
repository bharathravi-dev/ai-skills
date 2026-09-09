# M4-L10 — Inside a Transformer Block

| | |
|---|---|
| **Lesson ID** | M4-L10 |
| **Difficulty** | 3 (Advanced) |
| **Estimated study time** | 2 hours |
| **Prerequisites** | [M4-L09](M4-L09-positional-encoding.md), [M3-L10](../module-03-math-ml-essentials/M3-L10-neural-networks.md) |

---

## 1. Learning objectives

1. **Name** every component of a transformer block and state what each contributes.
2. **Explain** why the feed-forward network holds most of the parameters, and what it does.
3. **Explain** residual connections in terms of the gradient path, not just "it helps".
4. **Compare** pre-norm and post-norm, and say which is used at depth and why.
5. **Count** a model's parameters from its architecture, and check the result.

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **Block / layer** | One attention sublayer plus one feed-forward sublayer, with norms and residuals. |
| **Sublayer** | Either the attention or the feed-forward half. |
| **FFN / MLP** | The position-wise feed-forward network. |
| **`d_ff`** | The FFN's hidden width, conventionally `4 × d_model`. |
| **Residual connection** | `x + sublayer(x)` — the input is added to the output. |
| **Residual stream** | The running `d_model`-wide representation each block reads from and writes to. |
| **LayerNorm** | Normalises each vector to zero mean and unit variance, then scales and shifts. |
| **RMSNorm** | Normalises by root-mean-square only; no mean subtraction. |
| **Pre-norm / post-norm** | Normalising before or after each sublayer. |
| **GELU / SwiGLU** | Activation functions used in modern FFNs. |

---

## 3. Plain-language explanation

### 3.1 The block, in one picture

```
        x  ──────────────────────────┐
        │                            │
   ┌────▼─────┐                      │
   │   norm   │                      │
   └────┬─────┘                      │
   ┌────▼─────────────┐              │
   │ multi-head       │              │
   │ attention        │              │
   └────┬─────────────┘              │
        │                            │
        ▼                            │
       (+)◄──────────────────────────┘     residual
        │
        ├────────────────────────────┐
   ┌────▼─────┐                      │
   │   norm   │                      │
   └────┬─────┘                      │
   ┌────▼─────────────┐              │
   │ feed-forward     │              │
   │ (d → 4d → d)     │              │
   └────┬─────────────┘              │
        │                            │
        ▼                            │
       (+)◄──────────────────────────┘     residual
        │
        ▼  out            (same shape as x)
```

**Two sublayers, each wrapped in a norm and a residual.** That is the entire block, repeated 32 to 80
times.

### 3.2 What each half does

**Attention mixes information *between* positions.** Each token gathers from other tokens (M4-L07).

**The feed-forward network processes each position *independently*.** No mixing at all — the same
two-layer network applied to every position separately.

**The alternation is the design.** Attention decides *what information a position should have*; the
FFN decides *what to do with it*. Neither alone is sufficient: attention with no FFN can only ever
produce weighted averages of value vectors, and an FFN with no attention cannot see other tokens.

### 3.3 The fact that surprises people

**The feed-forward network holds about twice as many parameters as attention.**

```
Attention:  4 × d² (the Q, K, V and O projections)
FFN:        8 × d² (d → 4d, then 4d → d)
```

**Two-thirds of every block is the FFN**, and §7.3 counts this exactly for real configurations. Given
that the architecture is named after attention, this is worth knowing — and there is evidence that
the FFN is where much of a model's factual knowledge is stored. `[UNVERIFIED — an active research
area; Geva et al. 2020 is the usual reference]`

---

## 4. Analogy

**An assembly line where every station passes the whole product along, plus its own additions.**
Each station (block) can consult other items on the line (attention) and then does its own work
(FFN). Crucially, nothing is thrown away: each station *adds* to what arrived rather than replacing
it.

### Where the analogy breaks

1. **A station replaces or transforms. A residual block *adds*** — the original is still present in
   the sum, which is exactly what makes deep stacks trainable.
2. **Stations have defined jobs. Blocks have no assigned roles**; any specialisation is emergent and
   often not interpretable.
3. **A line has a fixed order of operations. Every block has identical structure** — the same code
   with different weights, 32 to 80 times.
4. **A product is finished at the end. The residual stream is read from and written to throughout**,
   and later blocks can undo what earlier ones did.

---

## 5. Detailed technical explanation

### 5.1 The feed-forward network

```python
def ffn(x, W1, b1, W2, b2):
    return activation(x @ W1 + b1) @ W2 + b2     # (T,d) -> (T,4d) -> (T,d)
```

**Applied identically to every position, independently.** It is a `(d) → (d)` function broadcast over
the sequence — no positions interact.

**Why expand to `4d` and back?** The wide middle layer gives the non-linearity room to work. A direct
`d → d` layer with an activation is far less expressive; the expansion is where the capacity lives.
`4×` is convention rather than derivation, and modern models vary it.

**Activations:**

| Function | Character |
|---|---|
| ReLU | `max(0, x)`. Simple; dead units possible (M3-L10 §5.6) |
| GELU | Smooth, roughly ReLU-shaped. Common in older transformers |
| SwiGLU | A gated variant using **three** matrices, not two. Common in modern LLMs |

**SwiGLU changes the parameter count**, which matters when you are counting: it uses three matrices,
so implementations shrink `d_ff` (often to `8/3 × d_model`) to keep the total comparable. §7.3
computes both.

### 5.2 Residual connections — the gradient argument

```python
x = x + attention(norm(x))
x = x + ffn(norm(x))
```

**The intuition usually given is "it helps information flow".** The precise reason is about gradients
(M3-L11 §5.1, Rule 2):

Differentiating `y = x + f(x)` gives `dy/dx = 1 + f'(x)`.

**That `1` is the point.** It creates a gradient path with derivative exactly 1, straight from the
loss to every earlier layer. Without it, the gradient must pass through every layer's Jacobian, and
those products shrink or explode with depth — M3-L11 §7.3 measured a **31,035,255×** spread across 12
layers with sigmoid activations.

**With residuals the gradient always has a route home**, regardless of depth. This is what made
networks beyond about 20 layers trainable at all, and it is why the residual stream is the right
mental model: a `d_model`-wide bus that every block reads from and adds to.

### 5.3 Normalisation

**LayerNorm** normalises each vector across its features:

```python
def layer_norm(x, gamma, beta, eps=1e-5):
    mean = x.mean(axis=-1, keepdims=True)
    var = x.var(axis=-1, keepdims=True)
    return gamma * (x - mean) / np.sqrt(var + eps) + beta
```

**RMSNorm** drops the mean subtraction and the shift:

```python
def rms_norm(x, gamma, eps=1e-6):
    rms = np.sqrt((x ** 2).mean(axis=-1, keepdims=True) + eps)
    return gamma * x / rms
```

**RMSNorm is cheaper and works about as well**, and most current LLMs use it. `[UNVERIFIED as to any
specific model]`

**Note that normalisation is per-token, not per-batch.** Unlike BatchNorm, it behaves identically at
batch size 1 and batch size 512 — which is why it suits variable-length sequence models.

### 5.4 Pre-norm versus post-norm — a real difference

| | Formula | Behaviour |
|---|---|---|
| **Post-norm** (original) | `x = norm(x + sublayer(x))` | Needs learning-rate warmup; unstable when deep |
| **Pre-norm** (modern) | `x = x + sublayer(norm(x))` | Trains stably at depth; the standard now |

**Why pre-norm is stable:** in post-norm, the residual passes *through* the normalisation, so the
clean `+1` gradient path is broken at every layer. In pre-norm the residual path is untouched — the
norm sits inside the branch — so the identity path survives from the loss all the way to layer 1.

**§7.3 measures this at 48 layers**, and the difference in activation growth is large.

Most pre-norm models add a **final norm** after the last block, since the residual stream is never
normalised on its way out.

### 5.5 Counting parameters

Per block, with `d = d_model`:

| Component | Parameters |
|---|---|
| `W_q, W_k, W_v, W_o` | `4d²` |
| FFN (`d→4d`, `4d→d`) | `8d²` |
| Two norms | `~4d` (negligible) |
| **Per block** | **`≈12d²`** |

Whole model:

```
total ≈ n_layers × 12d² + vocab × d      (+ vocab × d again if untied)
```

**Worked check** — 32 layers, `d = 4096`, vocabulary 32,000:

```
blocks    = 32 × 12 × 4096²  = 6,442,450,944
embedding = 32,000 × 4,096   =   131,072,000
total     ≈ 6.57 billion
```

**A "7B" model.** §7.3 verifies this arithmetic and shows the FFN's share.

### 5.6 What each component actually contributes

Ablation results from §7.3, on a **single-block** model trained on a small templated corpus:

| Removed | Final loss | vs full block |
|---|---|---|
| — (full block) | 0.1991 | — |
| **Attention** | 0.5285 | **2.65× worse** |
| **Residuals** | 0.4156 | **2.09× worse** |
| FFN | 0.1924 | **0.97× — slightly better** |
| Normalisation | 0.1823 | **0.92× — slightly better** |

**Two components made the tiny model *worse* by being present**, and that is a real result rather than
a broken experiment. On 15 tokens of rigid templates solved by one attention head, the FFN's extra
`8d²` parameters have nothing useful to learn and add optimisation noise, while normalisation
constrains a model that was never going to destabilise in one layer.

**So the honest statement is not "every component is always load-bearing" — it is that components earn
their place at different scales:**

| Component | Load-bearing from |
|---|---|
| **Attention** | Immediately, at any size — without it positions cannot interact at all |
| **Residuals** | The first layer, and **decisive** with depth (§7.3 measures a **4.84e+09×** gradient difference at 48 layers) |
| **FFN** | Scale — it is **67% of a real model's parameters** and does nothing on a toy |
| **Normalisation** | Depth — §7.3 shows what it holds together at 48 layers |

**The transferable lesson: if a component looks useless in your ablation, check whether your
experiment is large enough for it to matter before concluding anything.** This is the same error as
M4-L07's `max`-versus-`mean` gradient metric, in a different costume.

### 5.7 Assumptions and limitations

- Architectures vary: some interleave differently, some use mixture-of-experts FFNs, some share
  parameters between blocks.
- Biases are frequently omitted in modern models; the counts above ignore them.
- The claim that FFNs store factual knowledge is an active research area, not settled fact.

---

## 6. Worked example — one block, by hand

`d_model = 4`, `d_ff = 8`, one attention head, RMSNorm, pre-norm.

**Input** (one token, to keep the arithmetic small):

```
x = [1.0, 2.0, -1.0, 0.0]
```

**Step 1 — RMSNorm.**

```
mean(x²) = (1 + 4 + 1 + 0) / 4 = 1.5
rms      = √1.5 = 1.2247
x_norm   = [1.0, 2.0, -1.0, 0.0] / 1.2247
         = [0.8165, 1.6330, -0.8165, 0.0000]
```

With `γ = [1, 1, 1, 1]`, that is the output.

**Step 2 — attention.** A single token attends only to itself, so the weight is 1.0 and the output is
its own value vector. With `W_v = I` and `W_o = I`:

```
attn_out = x_norm = [0.8165, 1.6330, -0.8165, 0.0000]
```

**Step 3 — first residual.**

```
x = [1.0, 2.0, -1.0, 0.0] + [0.8165, 1.6330, -0.8165, 0.0000]
  = [1.8165, 3.6330, -1.8165, 0.0000]
```

**Note the original `x` is still fully present in that sum.** That is the residual stream.

**Step 4 — RMSNorm again.**

```
mean(x²) = (3.2997 + 13.1987 + 3.2997 + 0) / 4 = 4.9495
rms      = 2.2247
x_norm   = [0.8165, 1.6330, -0.8165, 0.0000]
```

**The same values as step 1** — because RMSNorm removes scale, and step 3 scaled the vector without
rotating it. A worthwhile thing to notice: **normalisation discards magnitude information**, and here
it discarded everything the attention sublayer contributed.

**Step 5 — FFN, first layer** (`d → 2d` here, kept small):

```
W1 = [[1, 0, 0, 0, 0, 0, 0, 0],
      [0, 1, 0, 0, 0, 0, 0, 0],
      [0, 0, 1, 0, 0, 0, 0, 0],
      [0, 0, 0, 1, 0, 0, 0, 0]]
```

`h = x_norm @ W1 = [0.8165, 1.6330, -0.8165, 0.0000, 0, 0, 0, 0]`

**ReLU:** `[0.8165, 1.6330, 0.0000, 0.0000, 0, 0, 0, 0]`

**The −0.8165 became 0.** That information is gone from this sublayer's output — but **it survives in
the residual stream**, because step 6 adds to `x`, not to `h`. This is the residual connection doing
its second job: preserving what a sublayer discards.

**Step 6 — FFN, second layer** (`W2` selects the first four rows):

```
ffn_out = [0.8165, 1.6330, 0.0000, 0.0000]
```

**Step 7 — second residual.**

```
out = [1.8165, 3.6330, -1.8165, 0.0000] + [0.8165, 1.6330, 0.0000, 0.0000]
    = [2.6330, 5.2660, -1.8165, 0.0000]
```

**Step 8 — read the result.**

- **Shape is `(4,)`, unchanged.** The block is `(T, d) → (T, d)`, which is what lets 32 of these stack.
- **The third component is `−1.8165`, not 0**, even though ReLU zeroed it in the FFN branch. The
  residual preserved it. **Without the residual it would be permanently lost after one block** — and
  after 32 blocks, almost everything would be.
- **The first two components have grown** from `[1.0, 2.0]` to `[2.63, 5.27]`. Residual streams grow
  through depth, which is exactly why a final norm is needed before the LM head.

---

## 7. Practical activity

**File:** [`labs/m4/l10_transformer_block.py`](../../labs/m4/l10_transformer_block.py)

**No API key, no network.**

```bash
source .venv/bin/activate
python labs/m4/l10_transformer_block.py
```

Verifies §6, counts parameters for real configurations and checks the FFN share, ablates each
component on a trained model, and compares pre-norm against post-norm at 48 layers.

### 7.2 Expected output

`[EXECUTED]` on Python 3.12.3, NumPy 2.5.3, 2026-09-08.

```text

============================================================================
1. THE WORKED EXAMPLE, VERIFIED  (d_model 4, one token, pre-norm)
============================================================================
  input x = [ 1.  2. -1.  0.]

  step 1: RMSNorm
    mean(x^2) = 1.5000   rms = 1.2247
    x_norm    = [ 0.8165  1.633  -0.8165  0.    ]

  step 2: attention (single token, W_v = W_o = I)
    attn_out  = [ 0.8165  1.633  -0.8165  0.    ]

  step 3: first residual
    x = [ 1.  2. -1.  0.] + [ 0.8165  1.633  -0.8165  0.    ]
      = [ 1.8165  3.633  -1.8165  0.    ]
    NOTE the original x is still entirely present in that sum.

  step 4: RMSNorm again
    mean(x^2) = 4.9495   rms = 2.2247
    x_norm    = [ 0.8165  1.633  -0.8165  0.    ]
    identical to step 1? True   (max diff 3.79e-07)
    RMSNorm removes SCALE, and step 3 scaled without rotating. So the
    normalisation discarded everything attention contributed here.

  step 5: FFN first layer + ReLU
    h        = [ 0.8165  1.633  -0.8165  0.      0.      0.      0.      0.    ]
    ReLU(h)  = [0.8165 1.633  0.     0.     0.     0.     0.     0.    ]
    the -0.8165 became 0.0000. That information is gone
    from this sublayer's output.

  step 6: FFN second layer
    ffn_out  = [0.8165 1.633  0.     0.    ]

  step 7: second residual
    out = [ 1.8165  3.633  -1.8165  0.    ] + [0.8165 1.633  0.     0.    ]
        = [ 2.633   5.266  -1.8165  0.    ]

  step 8: reading the result
    shape (4,) == input shape (4,): True
    component 2 = -1.8165, NOT 0 -- ReLU zeroed it in the FFN
      branch, and the residual preserved it.
    components 0-1 grew from [1. 2.] to [2.633 5.266]
      -- residual streams grow with depth, hence the final norm.

  SECTION 6 FULLY VERIFIED.

============================================================================
2. PARAMETER COUNTING, AND THE FFN's SHARE
============================================================================
  config     layers  d_model    attn/blk     ffn/blk  ffn share        total
  small          12      768        2.4M        4.7M     66.7%        0.12B
  7B-ish         32     4096       67.1M      134.2M     66.7%        6.57B
  13B-ish        40     5120      104.9M      209.7M     66.7%       12.75B
  70B-ish        80     8192      268.4M      536.9M     66.7%       65.47B

  The FFN is 66.7% of every block, in every configuration --
  it is 8d^2 against attention's 4d^2, so the ratio is exactly 2:1
  regardless of size. The architecture is named after the smaller half.

  verifying the lesson's arithmetic (32 layers, d=4096, vocab=32k):
    blocks    = 32 x 12 x 4096^2 = 6,442,450,944
    computed  =                    6,442,450,944
    embedding = 32,000 x 4,096   = 131,072,000
    total     =                    6,573,522,944  (6.57B)
    the 12d^2-per-block shortcut is exact.

  SwiGLU uses THREE matrices, so d_ff shrinks to keep the count level:
  variant                        d_ff    ffn params   vs 2-matrix
  2 matrices, d_ff = 4d        16,384        134.2M            --
  SwiGLU, d_ff = 8d/3          10,922        134.2M         1.00x

  width vs depth -- which axis is expensive:
  change                          parameters    factor
  baseline (32L, d=4096)               6.44B     1.00x
  double d_model                      25.77B     4.00x
  double layers                       12.88B     2.00x

  Doubling width QUADRUPLES parameters; doubling depth doubles them.

============================================================================
3. PRE-NORM vs POST-NORM AT DEPTH
============================================================================
  48 blocks, d_model 64, random weights, tracking activation
  magnitude through the stack.

    layer      pre-norm     post-norm    no residual
        0        0.7842        0.7938        0.8118
        1        1.3800        0.7925        1.0155
        4        2.4355        0.8243        1.0569
       12        4.4683        0.8386        0.8952
       24        5.9402        0.8016        1.0053
       36        7.7703        0.7782        1.0816
       48        8.9167        0.7590        0.9881

  growth from layer 0 to layer 48:
    pre-norm      0.7842 -> 8.9167e+00   (1.14e+01x)
    post-norm     0.7938 -> 7.5901e-01   (9.56e-01x)
    no residual   0.8118 -> 9.8808e-01   (1.22e+00x)

  Pre-norm grows steadily and predictably -- the residual stream
  ACCUMULATES each block's contribution, which is why a FINAL norm is
  needed before the LM head. Post-norm re-normalises after every
  addition, so magnitude stays flat -- but the identity gradient path is
  broken at each layer, which is the cost that does not show up here.

  NOTE what the 'no residual' column does NOT show. Its magnitude also
  stays near 1.0, because each layer's own norm rescales it. Activation
  MAGNITUDE is simply the wrong metric for that failure: the problem is
  not that the signal shrinks, it is that each layer REPLACES the
  previous representation instead of adding to it, so nothing survives
  the stack and no gradient reaches the early layers. Section 4 measures
  that directly, and finds a 10^9 difference.

============================================================================
4. WHY RESIDUALS HELP: THE GRADIENT PATH, MEASURED
============================================================================
  Propagating a gradient back through 48 blocks. With residuals the
  Jacobian is (1 + f'); without, it is f' alone.

    depth     with residual    without residual         ratio
        0        1.0000e+00          1.0000e+00      1.00e+00
        4        2.1149e+00          3.4741e-01      6.09e+00
       12        1.4947e+01          4.7398e-02      3.15e+02
       24        2.9362e+02          3.8916e-03      7.54e+04
       36        6.6450e+03          3.1376e-04      2.12e+07
       48        9.2431e+04          1.9103e-05      4.84e+09

  after 48 layers the gradient is 4.84e+09x
  larger with residuals than without. Without them it has vanished
  entirely -- the early layers receive nothing and never learn.
  This is M3-L11 section 5.1 Rule 2: dy/dx = 1 + f'(x), and that 1 is
  a path with derivative exactly 1 from the loss to every layer.

============================================================================
5. ABLATION: WHAT EACH COMPONENT IS WORTH
============================================================================
  vocabulary 15, d_model 32, 5-token context, 900 steps
  loss at initialisation should be ln(15) = 2.7081

  variant                            final loss   perplexity    vs full
  full block                             0.1991         1.22         --
  no attention                           0.5285         1.70      2.65x
  no feed-forward network                0.1924         1.21      0.97x
  no residual connections                0.4156         1.52      2.09x
  no normalisation                       0.1823         1.20      0.92x

  READ THIS TABLE HONESTLY -- two components made the model WORSE by
  their presence, and that is a real result, not a broken experiment.

    attention   : 2.65x worse without it. Decisive. Positions cannot
                  interact at all, so no amount of per-token processing
                  can use context.
    residuals   : 2.09x worse without them, even at ONE block.
    FFN         : removing it made the model very slightly BETTER.
    normalisation: same -- slightly better without.

  Why? This task is 15 tokens of rigid templates solved by a single
  attention head. The FFN's 4d^2 extra parameters have nothing useful
  to learn and add optimisation noise; normalisation constrains a model
  that was never going to destabilise in one layer.

  The honest conclusion is NOT 'every component is always load-bearing'.
  It is that components earn their place at DIFFERENT SCALES:
    * attention is load-bearing immediately, at any size
    * residuals are load-bearing from the first layer and become
      decisive with depth (section 4: a 10^9 gradient difference at 48)
    * the FFN and normalisation are overhead on a toy and essential at
      scale -- the FFN is 67% of a real model's parameters, and section 3
      shows what normalisation is holding together at 48 layers

  If a component looks useless in your ablation, check whether your
  experiment is large enough for it to matter before concluding anything.

Done.
```

### 7.3 Reading the result

**Section 1 verifies §6 completely**, including the two observations that make the residual's role
concrete: step 4's RMSNorm reproduces step 1's values exactly (max difference 3.79e-07), and the
output's third component is **−1.8165 rather than 0** despite ReLU having zeroed it in the FFN branch.

**Section 2 confirms the FFN's share is exactly 66.7% in every configuration** — 12M to 65B
parameters, same ratio. It is `8d²` against attention's `4d²`, so 2:1 holds regardless of size. The
`12d²`-per-block shortcut is verified exact against the explicit count.

The SwiGLU row shows why the `8/3` convention exists: three matrices at `d_ff = 8d/3` gives **134.2M
parameters, identical** to two matrices at `d_ff = 4d`. The shrink is deliberate, and forgetting it is
a common counting error.

And the width-versus-depth comparison: **doubling `d_model` quadruples parameters (4.00×); doubling
layers doubles them (2.00×).** Width is the expensive axis.

**Section 3 shows pre-norm and post-norm behaving as predicted** — pre-norm's activations grow
steadily to 8.92 over 48 layers as the residual stream accumulates, post-norm stays flat at ~0.76
because it re-normalises after every addition.

**But note what this section cannot show.** The "no residual" column also stays near 1.0, because each
layer's own norm rescales it. **Activation magnitude is the wrong metric for that failure** — the
problem is not that the signal shrinks but that each layer *replaces* the representation instead of
adding to it. The lab says so rather than pretending the number means what it does not.

**Section 4 measures the residual's actual effect**, and it is enormous:

| Depth | With residual | Without | Ratio |
|---|---|---|---|
| 12 | 1.49e+01 | 4.74e-02 | 3.15e+02 |
| 24 | 2.94e+02 | 3.89e-03 | 7.54e+04 |
| **48** | **9.24e+04** | **1.91e-05** | **4.84e+09** |

**After 48 layers the gradient is 4.84 billion times larger with residuals than without.** Without
them it has vanished entirely — the early layers receive nothing and never learn. This is M3-L11
§5.1's Rule 2 made quantitative: `dy/dx = 1 + f'(x)`, and that `1` is a path with derivative exactly 1
from the loss to every layer.

**Section 5 contradicted this lesson's draft, and the correction is now in §5.6.**

I had written that every component is load-bearing. Measured on a single-block model: attention is
worth **2.65×** and residuals **2.09×**, but removing the **FFN made the model slightly better**
(0.1924 vs 0.1991) and so did removing **normalisation** (0.1823).

That is not a defect in the experiment. On 15 tokens of rigid templates solved by one attention head,
the FFN has nothing to learn and normalisation constrains a model that could not destabilise in one
layer. **Both are overhead at this scale and essential at production scale** — the FFN being
two-thirds of a real model's parameters, and normalisation being what §3 shows holding a 48-layer
stack together.

**The transferable point: an ablation that shows a component is useless may be telling you about the
component, or about the size of your experiment.** Distinguishing those two is the work.

---

## 8. Common mistakes and troubleshooting

1. **Post-norm at depth without warmup.** Use pre-norm.
2. **Forgetting the final norm** after the last block in a pre-norm model.
3. **Omitting a residual.** Deep training degrades and it is hard to attribute.
4. **Assuming attention holds most parameters.** The FFN holds twice as many.
5. **Using BatchNorm.** It behaves differently at different batch sizes.
6. **Forgetting SwiGLU uses three matrices** when counting parameters.
7. **Normalising the residual stream in place** rather than inside the branch.

| Symptom | Likely cause | Fix |
|---|---|---|
| Training diverges past ~20 layers | Post-norm | Switch to pre-norm |
| Loss spikes early then recovers | No warmup with post-norm | Add warmup, or pre-norm |
| Parameter count off by ~2× | FFN or tied embeddings miscounted | Recount with `12d²` per block |
| Activations grow through depth | No final norm | Add one |
| Deep model no better than shallow | Residuals missing or broken | Check `x + sublayer(x)` |
| Quality varies with batch size | BatchNorm somewhere | Use LayerNorm or RMSNorm |

---

## 9. Security, privacy, reliability, cost

- **Cost.** Parameters are roughly `n_layers × 12d²`. Doubling `d_model` **quadruples** the parameters
  and therefore the memory and the per-token cost. Doubling depth only doubles them. Width is the
  expensive axis.
- **Reliability.** Pre-norm versus post-norm is a genuine stability difference, not a style
  preference. A deep post-norm model can fail to train at all.
- **Privacy.** If FFN layers do store factual associations, a model trained on sensitive text may
  retain and emit it. Do not train on unsanitised data (M10-L12).
- **Cost.** Activation memory during training scales with `n_layers × T × d_ff`, which for a `4d` FFN
  is four times the residual stream's width. This is what gradient checkpointing trades away.

---

## 10. Exercises

### Exercise 1 — Beginner (~25 min)

1. Name the four components of a block and what each contributes.
2. Why does the FFN hold twice the parameters of attention? Show the arithmetic.
3. Write `dy/dx` for `y = x + f(x)` and explain why the `1` matters.
4. What is the difference between pre-norm and post-norm, in one line each?
5. Count the parameters of a 24-layer model at `d_model` 2,048 with a 50,000 vocabulary.

### Exercise 2 — Intermediate (~40 min)

1. Implement a full block and assert the output shape equals the input shape.
2. Verify §6 numerically, including that step 4 reproduces step 1's values.
3. Count parameters for three real configurations and check the FFN share is ~67%.
4. Remove the residual connections and measure the gradient magnitude at layer 1 in a 24-layer stack.
5. Implement both LayerNorm and RMSNorm and measure the speed difference over 10,000 calls.

### Exercise 3 — Challenge (~50 min)

1. Build 48-layer pre-norm and post-norm stacks. Measure activation magnitude per layer and report
   where each diverges.
2. Ablate attention, the FFN, residuals and norms one at a time on a trained model. Report the loss
   for each and rank them.
3. Implement SwiGLU and adjust `d_ff` so the parameter count matches a two-matrix FFN. Verify.
4. Measure how much of the residual stream's final magnitude comes from each layer's contribution.
5. Show that removing the final norm in a pre-norm model changes the logit scale, and quantify it.

---

## 11. Quiz

*(Answers: [`answer-keys/module-04-answers.md`](../../answer-keys/module-04-answers.md#m4-l10).)*

**Q1.** A transformer block consists of:

- A. Two attention sublayers with a shared normalisation between them.
- B. Attention and a feed-forward network, each with norm and residual.
- C. A feed-forward network wrapped in two residual connections.
- D. Attention followed by a softmax over the whole vocabulary.

**Q2.** Which holds more parameters in a standard block?

- A. The feed-forward network, at roughly twice attention's count.
- B. The normalisation layers, which scale with `d_model` squared.
- C. Attention, at roughly twice the feed-forward network's count.
- D. They are equal by construction at `d_ff = 4 × d_model`.

**Q3.** What does the feed-forward network do?

- A. Mixes information between positions in the sequence.
- B. Normalises each position's vector to unit variance.
- C. Selects which positions each token should attend to.
- D. Processes each position independently of all others.

**Q4.** Why do residual connections help gradients?

- A. They normalise the gradient magnitude at every layer boundary.
- B. `dy/dx = 1 + f'(x)`, giving a path with derivative exactly 1.
- C. They reduce the number of layers the gradient must traverse.
- D. They apply gradient clipping automatically at each sublayer.

**Q5.** Pre-norm differs from post-norm in that the norm is applied:

- A. After the residual addition, to the combined result.
- B. Only once, before the first block in the whole stack.
- C. Inside the branch, leaving the residual path untouched.
- D. To the attention weights rather than to the activations.

**Q6.** RMSNorm differs from LayerNorm by:

- A. Omitting the mean subtraction and the learned shift.
- B. Applying to attention scores instead of to activations.
- C. Using a learned scale per layer instead of per feature.
- D. Normalising across the batch instead of across features.

**Q7.** A 32-layer model at `d_model` 4,096 has roughly how many block parameters?

- A. 400 million  B. 130 million  C. 100 billion  D. 6.4 billion

**Q8.** In §6 step 4, RMSNorm produced the same values as step 1 because:

- A. The residual addition had no effect on the vector at all.
- B. RMSNorm removes scale, and step 3 only scaled the vector.
- C. RMSNorm is idempotent and always returns its first output.
- D. The gamma parameters were set to one in both cases.

**Q9.** In §6 step 5, ReLU zeroed a component. Why is it still present in the output?

- A. ReLU preserves negative values below a learned threshold.
- B. The second FFN matrix restored it from the wide layer.
- C. The residual adds to `x`, not to the FFN's own output.
- D. The final normalisation reintroduced the missing magnitude.

**Q10.** Doubling `d_model` changes the parameter count by a factor of:

- A. 2  B. 4  C. 8  D. It is unchanged

**Q11.** *(Written, rubric-graded.)* In under 100 words, explain to a colleague why their 60-layer
model diverges during training while their 12-layer version trained fine, and what you would change.

---

## 12. Revision notes

- **A block = attention sublayer + FFN sublayer**, each wrapped in a **norm** and a **residual**.
  Repeated 32–80 times. **Shape is `(T, d_model)` throughout.**
- **Attention mixes *between* positions; the FFN processes each position *independently*.** The
  alternation is the design — neither alone suffices.
- **The FFN holds ~2× attention's parameters:** `8d²` vs `4d²`, so **~67% of every block**. The
  architecture is named after the smaller half.
- **Residuals: `dy/dx = 1 + f'(x)`.** That `1` is a gradient path with derivative exactly 1 from the
  loss to every layer. Without it, products of Jacobians shrink or explode with depth (M3-L11
  measured a 31-million-fold spread over 12 layers).
- **Residuals also preserve what a sublayer discards** — §6 step 5's ReLU zeroed a component and the
  residual kept it. Measured gradient effect at 48 layers: **4.84e+09×**.
- **Components earn their place at different scales.** Measured on one block: attention **2.65×**,
  residuals **2.09×** — but removing the **FFN or normalisation made the toy model slightly better**.
  Both are essential at depth and overhead on a toy. **An ablation showing no effect may be telling
  you about your experiment's size, not about the component.**
- **Pre-norm (`x + sublayer(norm(x))`) is the modern standard** because the residual path is
  untouched. Post-norm breaks the identity path at every layer and needs warmup. **Add a final norm.**
- **RMSNorm** = no mean subtraction, no shift. Cheaper, works about as well. **Per-token, not
  per-batch** — behaviour is identical at any batch size.
- **Parameters ≈ `n_layers × 12d² + vocab × d`.** Verified exact: 32 layers at `d` 4,096 = 6.44B
  blocks + 131M embedding = **6.57B**. FFN share is **66.7% in every configuration**.
- **SwiGLU uses three matrices**, so `d_ff` shrinks to `8d/3` — measured identical at **134.2M**.
- **Width is the expensive axis:** doubling `d_model` **quadruples** parameters; doubling depth
  doubles them.

---

## 13. Completion checklist

- [ ] I can draw a block from memory with norms and residuals in the right places.
- [ ] I can explain why the FFN has twice attention's parameters.
- [ ] I can state the gradient argument for residuals precisely.
- [ ] I know why pre-norm is used at depth.
- [ ] I counted a real model's parameters and checked the total.
- [ ] I worked §6 and saw the residual preserve what ReLU discarded.
- [ ] I can explain why the FFN ablation made the toy model *better*.
- [ ] I scored 8/11 on the quiz.

---

## 14. References

- Vaswani et al. (2017), *Attention Is All You Need*. <https://arxiv.org/abs/1706.03762> `[UNVERIFIED]`
- Xiong et al. (2020), *On Layer Normalization in the Transformer Architecture* (pre vs post-norm).
  <https://arxiv.org/abs/2002.04745> `[UNVERIFIED]`
- Zhang & Sennrich (2019), *Root Mean Square Layer Normalization*.
  <https://arxiv.org/abs/1910.07467> `[UNVERIFIED]`
- Geva et al. (2020), *Transformer Feed-Forward Layers Are Key-Value Memories*.
  <https://arxiv.org/abs/2012.14913> `[UNVERIFIED]`

---

## 15. Next lesson

→ [M4-L11 — Encoder, Decoder and Encoder-Decoder Architectures](M4-L11-architectures.md)

You can build a block. Next: the three ways they are arranged, and why almost every model you will use
picks the same one.
