# M4-L07 — Attention and Self-Attention: the Core Idea

| | |
|---|---|
| **Lesson ID** | M4-L07 |
| **Difficulty** | 3 (Advanced) |
| **Estimated study time** | 2.5 hours |
| **Prerequisites** | [M4-L04](M4-L04-embeddings.md), [M3-L02](../module-03-math-ml-essentials/M3-L02-dot-product-cosine.md), [M3-L09](../module-03-math-ml-essentials/M3-L09-logistic-regression.md) |

---

> **This is the idea the whole architecture is named after.**
> This lesson builds the intuition and proves the key properties. [M4-L08](M4-L08-qkv-worked.md)
> computes every number by hand. Do them in order, and do not skip §6.

---

## 1. Learning objectives

1. **Explain** attention as a content-dependent weighted average, without using the word "attention".
2. **Describe** what queries, keys and values each do, and why three roles are needed.
3. **Prove** that attention is permutation-invariant, and explain what that forces.
4. **Explain** why multi-head attention exists and what a single head cannot do.
5. **State**, precisely, what attention weights do and do not tell you.

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **Attention** | Producing an output as a weighted average of values, where weights come from content. |
| **Query (Q)** | What a position is looking for. |
| **Key (K)** | What a position offers as a label for itself. |
| **Value (V)** | What a position contributes if attended to. |
| **Attention score** | The raw `q·k` compatibility between two positions. |
| **Attention weight** | The score after softmax — a probability over positions. |
| **Self-attention** | Q, K and V all come from the same sequence. |
| **Cross-attention** | Q from one sequence, K and V from another. |
| **Scaling factor** | The `1/√d_k` divisor applied before the softmax. |
| **Multi-head** | Several attention operations in parallel, each in a subspace. |
| **Head dimension** | `d_model / n_heads`. |
| **Permutation invariance** | Reordering the inputs permutes the outputs identically — no positional sense. |

---

## 3. Plain-language explanation

### 3.1 The problem

M4-L04 showed that a token's meaning depends on its neighbours: `bank` differs in "river bank" and
"savings bank". Something must mix information between positions.

The obvious approaches all fail:

| Approach | Why it fails |
|---|---|
| Average all tokens equally | `the` contributes as much as `bank`; signal is diluted |
| Fixed window (±3 tokens) | Misses long-range dependencies; the window is a guess |
| Fixed learned weights per position | Position 5 always weights position 3 the same, regardless of content |

**What is actually needed: weights that depend on the content**, so `bank` can look at `river` when
`river` is present and at `savings` when it is not — without knowing in advance where either sits.

### 3.2 The idea

For each position:

1. **Compare** it with every other position. How relevant is each one to me?
2. **Normalise** those comparisons into weights summing to 1 (softmax, M3-L09).
3. **Average** the other positions' contributions using those weights.

```
output[i] = Σⱼ weight[i,j] × value[j]        where Σⱼ weight[i,j] = 1
```

**That is the whole mechanism.** A weighted average whose weights are computed from the content, per
position, every time.

### 3.3 Why three roles and not one

You could compare embeddings directly, `x_i · x_j`. Three separate learned projections are used
instead, and the reason is worth understanding:

- **Query** — what this position is *looking for*.
- **Key** — what this position *advertises about itself*.
- **Value** — what this position *contributes* when selected.

**Query and key must be separate** because *what I am looking for* is a different thing from *what I
offer*. A verb might be looking for its subject; it does not advertise itself as a subject. With one
projection, matching would be forced to be symmetric — if A attends to B, B must attend equally to A —
and language is full of asymmetric relationships.

**Value must be separate from key** because *how I am found* is a different thing from *what I
contribute*. A pronoun might be found via grammatical features and contribute semantic content.

**§7.3 demonstrates the asymmetry directly**, which is the cleanest justification for the design.

---

## 4. Analogy

**A library search.** Your **query** is what you want. Each book's **key** is its catalogue entry. The
**value** is the book's contents. You match your query against every key, and take a blend of the
contents weighted by how well each matched.

### Where the analogy breaks

1. **A library search returns a few books. Attention always returns a blend of *all* of them**,
   weighted — including tiny weights on irrelevant ones. Nothing is excluded; things are only
   de-emphasised.
2. **Catalogue entries are written by librarians. Keys, queries and values are all learned**, and
   there is no guarantee they correspond to anything a person would name.
3. **You know what you are looking for. A query is a vector**, produced by a matrix, that no one
   designed to be interpretable.
4. **A library has one catalogue. Multi-head attention runs several searches at once** in different
   subspaces, and combines them.
5. **Library search is a lookup. This is differentiable**, which is the entire reason it can be
   learned (M3-L06 §5.6).

---

## 5. Detailed technical explanation

### 5.1 The equation

$$\\text{Attention}(Q, K, V) = \\text{softmax}\\!\\left(\\frac{QK^\\top}{\\sqrt{d_k}}\\right)V$$

Step by step, with shapes, for a sequence of `T` tokens:

```python
Q = X @ W_q        # (T, d_model) @ (d_model, d_k) -> (T, d_k)
K = X @ W_k        # (T, d_k)
V = X @ W_v        # (T, d_v)

scores = Q @ K.T / np.sqrt(d_k)     # (T, T)   every position vs every position
scores = scores + causal_mask       # -inf above the diagonal (M4-L05)
weights = softmax(scores, axis=-1)  # (T, T)   each ROW sums to 1
output  = weights @ V               # (T, d_v)
```

**The `(T, T)` scores matrix is the quadratic cost** measured in M4-L06 §7.3 at `T^2.06`.

**Each row of `weights` sums to 1** — row `i` is a probability distribution over which positions
token `i` draws from.

### 5.2 Why divide by `√d_k`

Without scaling, dot products grow with dimension. For random vectors with unit-variance components,
`q·k` has standard deviation `√d_k` — so at `d_k = 64` scores are typically ±8, and at `d_k = 128`,
±11.

**Large scores make softmax saturate**: one weight goes to ~1 and the rest to ~0, and the gradient
through softmax collapses (M3-L10 §5.3). Training stalls.

Dividing by `√d_k` returns the scores to roughly unit variance regardless of dimension. **§7.3
measures the saturation and the gradient collapse.**

### 5.3 Attention is permutation-invariant — and this is a problem

**Nothing in the equation refers to position.** Shuffle the input rows and the outputs are shuffled
identically; no output value changes.

```
attention(shuffle(X)) == shuffle(attention(X))
```

So `"dog bites man"` and `"man bites dog"` produce **the same set of output vectors**, differently
ordered. The mechanism cannot tell them apart.

**This is why positional information must be added explicitly** (M4-L09). It is not an enhancement;
without it the model is a bag of words. §7.3 proves the invariance numerically.

*(The causal mask breaks the invariance in decoder-only models by making the score matrix
position-dependent — but it only encodes ordering, not distance, so positional encodings are still
required.)*

### 5.4 Self-attention versus cross-attention

| | Q from | K, V from | Used in |
|---|---|---|---|
| **Self-attention** | The sequence | The same sequence | Every transformer block |
| **Cross-attention** | The decoder | The **encoder** | Translation, encoder-decoder models (M4-L11) |

Cross-attention is how a decoder consults a separate encoded input. It is the same equation; only the
source of K and V changes.

### 5.5 Multi-head attention

One attention operation produces **one** weighted average per position — so it can express one
relationship at a time. But a token often relates to several things at once: its subject, its
modifier, the entity it refers back to.

**Multi-head runs `h` attentions in parallel, each in a `d_model/h`-dimensional subspace:**

```python
d_head = d_model // n_heads
# each head has its own W_q, W_k, W_v of size (d_model, d_head)
heads = [attention(X @ Wq[i], X @ Wk[i], X @ Wv[i]) for i in range(n_heads)]
output = np.concatenate(heads, axis=-1) @ W_o     # (T, d_model)
```

**Note the parameter count does not increase.** 8 heads of 64 dimensions cost the same as 1 head of
512. You get several relationships for the price of one, at the cost of each being lower-dimensional.

Heads often specialise — some track syntax, some track position, some appear to do very little.
**§7.3 trains a model where two heads must learn different relationships, and shows them doing so.**

### 5.6 What attention weights do and do not tell you

Attention maps are appealing: they look like an explanation. **Treat them with care.**

**What they tell you:** which positions contributed to a weighted average at one layer, in one head.

**What they do not tell you:**

- **Not importance.** A large weight on a value vector near zero contributes nothing. The weight is
  half the story; the value is the other half.
- **Not causation.** Attention weights are not a faithful explanation of the output. Jain & Wallace
  (2019) showed that different attention distributions can produce identical predictions.
  `[UNVERIFIED — the finding is contested and the literature is worth reading before relying on it]`
- **Not the whole path.** Residual connections carry information *around* attention (M4-L10). A
  position can influence the output with near-zero attention weight.
- **Not aggregate.** Weights from one head in one layer say nothing about a 32-layer, 32-head model's
  behaviour.

**Use attention maps as a debugging hint, never as evidence.** If you need to explain a decision,
build an evaluation that measures behaviour (M3-L14, M10-L10), not a heatmap that looks persuasive.

### 5.7 Assumptions and limitations

- This describes standard scaled dot-product attention. Sparse, linear and sliding-window variants
  change the cost and the properties.
- Real implementations fuse operations and never materialise the `(T, T)` matrix.
- Grouped-query and multi-query attention share K and V across heads to shrink the KV cache
  (M4-L17); the equation is unchanged.

---

## 6. Worked example — attention resolving a reference, by hand

Four tokens, `d_k = d_v = 2`, so the arithmetic is checkable. **Do this with a pencil.**

**Sentence:** `the  cat  sat  it` — where `it` should attend to `cat`.

**Embeddings** (already including position, for simplicity):

```
x_the = [0.1, 0.0]
x_cat = [0.9, 0.2]
x_sat = [0.2, 0.8]
x_it  = [0.3, 0.1]
```

**Projections** — deliberately chosen so `it`'s query points toward "noun-like":

```
W_q = [[1.0, 0.0],     W_k = [[1.0, 0.0],     W_v = [[1.0, 0.0],
       [0.0, 0.5]]            [0.0, 0.5]]            [0.0, 1.0]]
```

**Step 1 — compute Q, K, V.** With these matrices, `q = [x₀, 0.5·x₁]`, same for `k`, and `v = x`.

| Token | q | k | v |
|---|---|---|---|
| the | `[0.10, 0.00]` | `[0.10, 0.00]` | `[0.1, 0.0]` |
| cat | `[0.90, 0.10]` | `[0.90, 0.10]` | `[0.9, 0.2]` |
| sat | `[0.20, 0.40]` | `[0.20, 0.40]` | `[0.2, 0.8]` |
| **it** | `[0.30, 0.05]` | `[0.30, 0.05]` | `[0.3, 0.1]` |

**Step 2 — scores for the query at `it`.** `q_it = [0.30, 0.05]`, and `√d_k = √2 = 1.4142`:

```
q_it · k_the = 0.30(0.10) + 0.05(0.00) = 0.0300   → /1.4142 = 0.0212
q_it · k_cat = 0.30(0.90) + 0.05(0.10) = 0.2750   → /1.4142 = 0.1944
q_it · k_sat = 0.30(0.20) + 0.05(0.40) = 0.0800   → /1.4142 = 0.0566
q_it · k_it  = 0.30(0.30) + 0.05(0.05) = 0.0925   → /1.4142 = 0.0654
```

**Step 3 — softmax.**

```
exp(0.0212)=1.0214   exp(0.1944)=1.2146   exp(0.0566)=1.0582   exp(0.0654)=1.0676
sum = 4.3618

weights = [0.2342, 0.2785, 0.2426, 0.2448]
```

**Step 4 — the weighted average.**

```
output_it = 0.2342[0.1,0.0] + 0.2785[0.9,0.2] + 0.2426[0.2,0.8] + 0.2448[0.3,0.1]
          = [0.0234, 0.0000] + [0.2507, 0.0557] + [0.0485, 0.1941] + [0.0734, 0.0245]
          = [0.3960, 0.2743]
```

**Step 5 — read the result honestly, because this is the important part.**

`cat` received the highest weight (**0.2785**) — correct. But look at the spread: **0.2342 to 0.2785**.
The distribution is nearly **uniform**. `it`'s output has barely moved toward `cat` at all.

**Why so flat?** The scores before softmax range from 0.021 to 0.194 — a spread of **0.17**, and
`exp` of numbers that close is nearly constant. **Softmax only produces sharp weights when the
scores are well separated**, and separating them is exactly what training the `W` matrices
accomplishes.

**This is what an untrained attention head looks like: an almost uniform average.** Training does not
teach the model to average; it teaches the projections to make the right scores *large*. §7.3 trains
this same head and shows the weight on `cat` rising from 0.28 toward 1.0.

**Step 6 — what would sharpen it?** Larger scores. Either larger `q`/`k` magnitudes (what training
produces) or removing the `√d_k` divisor (which would sharpen it *and* break the gradient, §5.2).
The scaling factor deliberately trades sharpness for trainability.

---

## 7. Practical activity

**File:** [`labs/m4/l07_attention.py`](../../labs/m4/l07_attention.py)

**No API key, no network.** NumPy only.

```bash
source .venv/bin/activate
python labs/m4/l07_attention.py
```

Reproduces §6 exactly, trains the same head and watches the weights sharpen, proves permutation
invariance numerically, measures softmax saturation with and without `√d_k` scaling, demonstrates the
query/key asymmetry, and trains a two-head model where the heads must specialise.

### 7.2 Expected output

`[EXECUTED]` on Python 3.12.3, NumPy 2.5.3, 2026-09-08.

```text

============================================================================
1. THE WORKED EXAMPLE, VERIFIED  (4 tokens, d_k = 2)
============================================================================
  token  x               q               k               v               
  the    [0.1 0. ]       [0.1 0. ]       [0.1 0. ]       [0.1 0. ]       
  cat    [0.9 0.2]       [0.9 0.1]       [0.9 0.1]       [0.9 0.2]       
  sat    [0.2 0.8]       [0.2 0.4]       [0.2 0.4]       [0.2 0.8]       
  it     [0.3 0.1]       [0.3  0.05]     [0.3  0.05]     [0.3 0.1]       

  scores for the query at 'it'  (sqrt(d_k) = 1.4142):
  vs            q.k    /sqrt(d_k)       exp    weight
  the        0.0300        0.0212    0.8409    0.2342
  cat        0.2750        0.1945    1.0000    0.2785
  sat        0.0800        0.0566    0.8712    0.2426
  it         0.0925        0.0654    0.8789    0.2448
  sum                                          1.0000

  output for 'it' = [0.396  0.2743]
  highest weight  : 'cat' (0.2785)  -- correct
  weight spread   : 0.2342 to 0.2785 = 0.0443
  score spread    : 0.0212 to 0.1945 = 0.1732

  NEARLY UNIFORM. The right token wins, but only just. exp() of numbers
  that close is nearly constant, so softmax cannot separate them.
  This is what an UNTRAINED attention head looks like.

  the full attention matrix (each ROW sums to 1):
               the      cat      sat       it      sum
      the   0.2451   0.2594   0.2469   0.2486   1.0000
      cat   0.2036   0.3412   0.2232   0.2321   1.0000
      sat   0.2309   0.2660   0.2622   0.2409   1.0000
       it   0.2342   0.2785   0.2426   0.2448   1.0000

============================================================================
2. TRAINING SHARPENS THE WEIGHTS  ('it' must attend to 'cat')
============================================================================
      step   weight on cat   profile
         0          0.2779   |###########
        10          0.3587   |##############
        50          0.9339   |#####################################
       200          0.9931   |#######################################
      1000          0.9991   |#######################################
      4000          0.9998   |#######################################

  final attention row for 'it':
                the       cat       sat        it
       it    0.0000    0.9998    0.0000    0.0002

  score spread went 0.1732 -> 11.6324
  weight on 'cat'  went 0.2779 -> 0.9998

  Training did NOT teach the model to average. It learned projections
  that SEPARATE the scores, and softmax turned that separation into a
  sharp weight. Sharpness is a consequence, not an objective.

============================================================================
3. ATTENTION IS PERMUTATION-INVARIANT  (why positional encoding exists)
============================================================================
  original order : ['the', 'cat', 'sat', 'it']
  permuted order : ['sat', 'the', 'it', 'cat']

  token   output (original)       output (permuted input)   
  sat     [0.387179 0.287072]     [0.387179 0.287072]       
  the     [0.381923 0.274232]     [0.381923 0.274232]       
  it      [0.395986 0.274251]     [0.395986 0.274251]       
  cat     [0.441652 0.269995]     [0.441652 0.269995]       

  attention(shuffle(X)) == shuffle(attention(X)) ? True
  max difference: 5.55e-17

  Every output vector is IDENTICAL, merely reordered. 'dog bites man'
  and 'man bites dog' are the same computation to this mechanism.

  now add positional encodings and repeat:
    invariance still holds? False
    max difference: 0.4010

  Broken, as required. Positional encoding is not an enhancement --
  without it the model is a bag of words (M4-L09).

============================================================================
4. WHY DIVIDE BY sqrt(d_k)  (saturation and the gradient)
============================================================================
  16 random tokens, unit-variance components

     d_k   score sd   max weight   entropy   mean softmax grad   scaled?
       8      1.846       0.8001    1.8003            4.59e-02        NO
       8      0.639       0.2483    2.5958            5.70e-02       yes
      64      7.596       0.9999    0.4276            1.43e-02        NO
      64      1.185       0.4837    2.3029            5.36e-02       yes
     256     15.344       1.0000    0.0668            2.50e-03        NO
     256      0.961       0.3729    2.4174            5.52e-02       yes
    1024     30.225       1.0000    0.0050            9.50e-05        NO
    1024      0.959       0.4810    2.4145            5.50e-02       yes

  uniform entropy for 16 positions = ln(16) = 2.7726

  gradient collapse, unscaled: 4.59e-02 at d_k=8 -> 9.50e-05 at d_k=1024
    a 483x reduction
  scaled                     : 5.70e-02 -> 5.50e-02
    a 1.04x change -- essentially constant

  Unscaled, score standard deviation grows with sqrt(d_k), so at large
  d_k one weight approaches 1.0, entropy collapses toward 0, and the
  mean softmax gradient w(1-w) goes to zero -- training stalls (M3-L10).
  Scaled, the statistics are roughly CONSTANT across four orders of
  magnitude in d_k. That is what the divisor buys.

============================================================================
5. WHY QUERY AND KEY MUST BE SEPARATE PROJECTIONS
============================================================================
  GOAL: 'verb' should attend strongly to 'noun', while 'noun' attends
  only weakly to 'verb'. An asymmetric relationship -- the normal case
  in language.

                        separate Q,K         shared projection
                -> verb      -> noun      -> verb      -> noun
      verb       0.0474       0.9526       0.9526       0.0474
      noun       0.5000       0.5000       0.0474       0.9526

  asymmetry |w(verb->noun) - w(noun->verb)|:
    separate Q,K      : 0.4526
    shared projection : 0.0000

  With a SHARED projection the score matrix is q_i . q_j, which is
  symmetric by construction: score(i,j) == score(j,i) ALWAYS. It can
  never express 'A looks at B but B does not look at A'. Separate Q and
  K make the score matrix asymmetric, which is why there are two.

============================================================================
6. MULTI-HEAD: SEVERAL RELATIONSHIPS FOR THE SAME PARAMETER BUDGET
============================================================================
  d_model = 64

    heads   d_head   params/head   total Q,K,V params
        1       64        12,288               12,288
        2       32         6,144               12,288
        4       16         3,072               12,288
        8        8         1,536               12,288
       16        4           768               12,288

  IDENTICAL total. 8 heads of 64 dims cost exactly what 1 head of 512
  costs. You get several relationships for the same price -- at the cost
  of each being lower-dimensional.

  training 2 heads on a task with TWO relationships:
    head must learn: 'attend to the PREVIOUS token'
    head must learn: 'attend to the FIRST token'

    head 0 (previous-token): mean weight on its target = 0.9999
      attention matrix (rows = query position):
        pos 0 |  1.000  0.000  0.000  0.000  0.000  0.000
        pos 1 |  1.000  0.000  0.000  0.000  0.000  0.000
        pos 2 |  0.000  1.000  0.000  0.000  0.000  0.000
        pos 3 |  0.000  0.000  1.000  0.000  0.000  0.000
        pos 4 |  0.000  0.000  0.000  1.000  0.000  0.000
        pos 5 |  0.000  0.000  0.000  0.000  1.000  0.000

    head 1 (first-token): mean weight on its target = 0.9999
      attention matrix (rows = query position):
        pos 0 |  1.000  0.000  0.000  0.000  0.000  0.000
        pos 1 |  1.000  0.000  0.000  0.000  0.000  0.000
        pos 2 |  1.000  0.000  0.000  0.000  0.000  0.000
        pos 3 |  1.000  0.000  0.000  0.000  0.000  0.000
        pos 4 |  1.000  0.000  0.000  0.000  0.000  0.000
        pos 5 |  1.000  0.000  0.000  0.000  0.000  0.000

  overlap between the two heads' attention: 0.3333
  The heads learned genuinely DIFFERENT patterns -- one a diagonal band,
  one a single column. A single head could express only one of them.
  That is what multi-head buys.

  A CAUTION on reading these matrices: they show which positions fed a
  weighted average in ONE head at ONE layer. They are not importance,
  not causation, and not the whole path -- residual connections carry
  information around attention entirely (M4-L07 section 5.6).

Done.
```

### 7.3 Reading the result

**Section 1 verifies §6 exactly** — weights `[0.2342, 0.2785, 0.2426, 0.2448]`, summing to 1.0000, with
`cat` correctly winning. The full matrix confirms **every row sums to 1.0000**.

The spread is the finding. Scores range 0.0212 to 0.1945 (a spread of **0.1732**) and weights range
0.2342 to 0.2785 (a spread of **0.0443**). `exp` of numbers that close is nearly constant, so softmax
cannot separate them. **This is what an untrained attention head looks like: an almost uniform
average.**

**Section 2 shows what training actually changes**, and it is not what most people assume:

| Step | Weight on `cat` |
|---|---|
| 0 | 0.2779 |
| 10 | 0.3587 |
| 50 | 0.9339 |
| 4,000 | **0.9998** |

**Score spread went 0.1732 → 11.6324; weight on `cat` went 0.2779 → 0.9998.** Training did not teach
the model "to attend"; it learned projections that make the *right* scores large, and softmax
converted that separation into a sharp weight. **Sharpness is a consequence of separation, not an
objective.** That is worth holding onto when you look at an attention map and see a peak.

**Section 3 proves permutation invariance to machine precision.** Shuffling the input rows produces
outputs identical to shuffling the outputs — **maximum difference 5.55e-17**, i.e. exactly zero in
floating point.

`"dog bites man"` and `"man bites dog"` are the *same computation* to this mechanism. Adding
positional encodings breaks the invariance immediately (max difference 0.4010). **Positional encoding
is not an enhancement; without it the model is a bag of words** (M4-L09).

**Section 4 measures why the `√d_k` divisor exists**, across four orders of magnitude:

| `d_k` | Scaled? | Score sd | Max weight | Entropy | Mean softmax gradient |
|---|---|---|---|---|---|
| 8 | no | 1.85 | 0.8001 | 1.80 | 4.59e-02 |
| 1024 | no | **30.23** | **1.0000** | **0.0050** | **9.50e-05** |
| 8 | yes | 0.64 | 0.2483 | 2.60 | 5.70e-02 |
| 1024 | yes | 0.96 | 0.4810 | 2.41 | 5.50e-02 |

**Unscaled, the mean softmax gradient collapses by 483× between `d_k` 8 and 1,024.** Entropy falls to
0.0050 against a uniform value of `ln(16) = 2.7726` — one weight has taken essentially all the mass,
and `w(1−w)` is therefore ~0 everywhere. **Training stalls, and the symptom is a loss curve that
flattens early for no visible reason** (M3-L10 §5.3).

**Scaled, the same statistics change by 1.04× across the whole range.** That constancy is precisely
what the divisor buys — the layer behaves the same whether `d_k` is 8 or 1,024.

*(A note on method: the first version of this lab reported the **maximum** of `w(1−w)` and showed no
effect at `d_k` 64 or 256 — a saturated row still contains a few mid-range entries, so the max hides
the collapse. The mean is the right statistic here, and choosing it deliberately is part of the work.)*

**Section 5 is the cleanest justification for having three projections rather than one:**

| | Separate Q, K | | Shared projection | |
|---|---|---|---|---|
| | → verb | → noun | → verb | → noun |
| **verb** | 0.0474 | **0.9526** | 0.9526 | 0.0474 |
| **noun** | 0.5000 | 0.5000 | 0.0474 | 0.9526 |

Asymmetry `|w(verb→noun) − w(noun→verb)|`: **0.4526** with separate projections, **exactly 0.0000**
with a shared one.

**With a shared projection the score matrix is `qᵢ·qⱼ`, which is symmetric by construction.** It can
*never* express "A attends to B but B does not attend to A" — not through better training, not with
more parameters. Language is full of asymmetric relationships, so the design needs two projections.
This is a structural argument, not an empirical preference.

**Section 6 confirms multi-head is free in parameters**: 1 head at 64 dimensions, 8 heads at 8
dimensions and 16 heads at 4 dimensions all cost **12,288** Q/K/V parameters.

Then two heads are trained on genuinely different relationships, and both reach **0.9999** mean weight
on their target. The learned matrices are visibly different structures — head 0 is a diagonal band
(each position attends to its predecessor), head 1 is a single column (every position attends to the
first token). **A single head produces one weighted average and can express only one of these.** That
is what multi-head buys: several relationships for the same parameter budget, each in a smaller
subspace.

**And the caution the lab ends on is the one to carry forward.** Those matrices look like
explanations. They show which positions fed a weighted average, in one head, at one layer. They are
not importance (the value vector may be near zero), not causation, and not the whole path — residual
connections carry information *around* attention entirely (§5.6). **Use them as a debugging hint,
never as evidence.**

---

## 8. Common mistakes and troubleshooting

1. **Forgetting the `√d_k` scaling.** Softmax saturates, gradients vanish, training stalls.
2. **Softmaxing over the wrong axis.** Rows must sum to 1, not columns.
3. **Adding the mask *after* the softmax.** It must be added to the scores, before.
4. **Assuming attention knows about order.** It does not (§5.3).
5. **Reading attention maps as explanations.**
6. **Assuming more heads is better.** Heads shrink as they multiply; `d_head` can become too small.
7. **Materialising the full `(T, T)` matrix** at long context.
8. **Expecting a single head to capture several relationships.**

| Symptom | Likely cause | Fix |
|---|---|---|
| Loss plateaus early | Softmax saturated | Check the `√d_k` scaling |
| Attention weights all ~1/T | Untrained, or scores too close | Expected at init; check it changes with training |
| One weight ~1.0, rest ~0 | Saturation | Verify scaling; check init magnitude |
| Word order does not matter | No positional encoding | Add it (M4-L09) |
| Rows do not sum to 1 | Wrong softmax axis | Softmax over the last axis |
| Model sees the future | Mask applied after softmax | Add `−inf` to scores first |
| OOM at long sequences | `(T, T)` materialised | Use a fused implementation |

---

## 9. Security, privacy, reliability, cost

- **Cost.** Attention is `O(T²)` in compute and, if materialised, in memory. Doubling context
  quadruples the work (M4-L06 §7.3 measured `T^2.06`). Model this before offering long context.
- **Security.** Every token in the window can influence every other. A malicious instruction in a
  retrieved document is *mechanically* able to affect the answer — attention is exactly the pathway
  (M10-L06).
- **Reliability.** Attention weights are not an audit trail. If you need to justify a decision, build
  a behavioural evaluation, not a heatmap.
- **Privacy.** Attention maps derived from user content are themselves derived data. Do not log them
  by default, and treat them like the content they came from.

---

## 10. Exercises

### Exercise 1 — Beginner (~25 min)

1. In one sentence, define attention without using the word "attention".
2. Why are query and key separate projections rather than one?
3. What does `√d_k` prevent, and what would happen without it?
4. Why does permutation invariance force positional encodings?
5. What do attention weights *not* tell you? Give two things.

### Exercise 2 — Intermediate (~40 min)

1. Run the lab. Reproduce §6's weight on `cat` by hand and confirm it.
2. Remove the `√d_k` divisor at `d_k` = 8, 64 and 512. Report the maximum weight in each case and
   explain the trend.
3. Prove permutation invariance yourself with an assertion, then add positional encodings and show
   the assertion now fails.
4. Implement multi-head attention and verify the output shape equals single-head with the same
   `d_model`.
5. Construct an input where query/key asymmetry matters: A should attend strongly to B while B
   attends weakly to A. Show a single shared projection cannot do this.

### Exercise 3 — Challenge (~50 min)

1. Train the §6 head on a task requiring `it` to attend to `cat`. Plot the weight on `cat` against
   training step.
2. Build a two-head model on a task with two distinct relationships and show the heads specialise.
   Report a measure of specialisation and justify your choice of measure.
3. Measure the gradient magnitude through softmax as a function of score spread, and identify where it
   collapses.
4. Implement attention with an explicit causal mask and assert that output `i` is unchanged when
   tokens after `i` are altered.
5. Implement a sliding-window attention variant and measure the cost curve against full attention.
   Report the exponent for each.
6. Construct a case where a token has near-zero attention weight yet materially affects the output via
   the residual path. Explain what this means for interpreting attention maps.

---

## 11. Quiz

*(Answers: [`answer-keys/module-04-answers.md`](../../answer-keys/module-04-answers.md#m4-l07).)*

**Q1.** Attention computes each output as:

- A. A weighted average of values, with weights from content.
- B. The single most similar value vector, selected by argmax.
- C. A fixed learned combination of neighbouring positions.
- D. The element-wise product of the query and key vectors.

**Q2.** Why are query and key separate projections?

- A. To halve the number of parameters the layer must learn.
- B. To let the two vectors have different dimensionalities.
- C. Because what a position seeks differs from what it offers.
- D. To allow the scaling factor to be applied to only one.

**Q3.** What does dividing by `√d_k` prevent?

- A. Attention weights failing to sum to one across a row.
- B. Softmax saturating, which collapses the gradient signal.
- C. Numerical overflow when exponentiating very large scores.
- D. The scores matrix growing quadratically with sequence length.

**Q4.** Attention without positional encoding treats "dog bites man" and "man bites dog" as:

- A. Different, because the causal mask distinguishes the orders.
- B. Different, because the embeddings themselves differ.
- C. The same set of outputs, merely reordered.
- D. Invalid input, since order is required for the computation.

**Q5.** In `weights = softmax(scores)`, each row sums to 1 because:

- A. Row `i` is a distribution over which positions `i` draws from.
- B. The values were normalised to unit length beforehand.
- C. The scaling factor guarantees the scores are bounded.
- D. The causal mask removes exactly the excess probability.

**Q6.** Multi-head attention with 8 heads at `d_model` 512 uses:

- A. Eight times the parameters of a single 512-dimensional head.
- B. About the same parameters, with each head at 64 dimensions.
- C. Fewer parameters, since the heads share their projections.
- D. Eight times the parameters, but only during training.

**Q7.** A token has an attention weight of 0.9. What does that establish?

- A. That token is the most important input to the prediction.
- B. Removing it would change the output proportionally.
- C. It caused the model's answer at this layer.
- D. It dominated one weighted average, in one head, at one layer.

**Q8.** Cross-attention differs from self-attention in that:

- A. It uses a different normalisation instead of softmax.
- B. It omits the causal mask and attends bidirectionally.
- C. Keys and values come from a different sequence than queries.
- D. It operates on characters rather than on tokens.

**Q9.** At initialisation, attention weights are typically:

- A. Sharply peaked on the token's own position.
- B. Concentrated entirely on the first token in the sequence.
- C. Near-uniform, because the scores are close together.
- D. Exactly zero, until the projections have been trained.

**Q10.** Why is a residual connection relevant to interpreting attention maps?

- A. Residuals rescale the attention weights before the softmax.
- B. Residuals are what make the weights sum to one per row.
- C. Residuals cause the quadratic cost attributed to attention.
- D. Information bypasses attention, so low weight is not no influence.

**Q11.** *(Written, rubric-graded.)* In under 120 words, explain attention to a competent engineer who
knows no machine learning, using no equations, and state one thing it cannot do.

---

## 12. Revision notes

- **Attention = a weighted average of values, where the weights are computed from the content**, per
  position, every time. `softmax(QKᵀ/√d_k)V`.
- **Three roles:** query = what I seek · key = what I advertise · value = what I contribute.
  **Q and K must differ** or matching would be forced symmetric, and language is asymmetric.
- **Each row of the weight matrix sums to 1** — a distribution over source positions.
- **`√d_k` prevents softmax saturation.** Measured: unscaled, the mean softmax gradient collapses
  **483×** between `d_k` 8 and 1,024 and entropy falls to 0.0050 (uniform is 2.7726); scaled, the same
  statistics change by **1.04×** across that range.
- **Attention is permutation-invariant.** Measured to **5.55e-17** — exactly zero in floating point.
  **This is why positional encodings are mandatory** (M4-L09), not optional.
- **A shared Q/K projection gives a symmetric score matrix by construction.** Measured asymmetry:
  0.4526 with separate projections, **exactly 0.0000** with a shared one. No amount of training fixes
  that.
- **Multi-head is several attentions in subspaces**, at *no extra parameter cost* — `d_head =
  d_model / n_heads`. One head expresses one relationship.
- **At initialisation the weights are near-uniform.** Measured: weight on the target went
  **0.2779 → 0.9998** while the score spread went **0.1732 → 11.6324**. Training learns projections
  that *separate the scores*; sharpness is the consequence, not the objective.
- **Attention weights are not explanations.** Not importance (the value may be ~0), not causation, and
  not the whole path (residuals bypass attention). **Debugging hint, never evidence.**
- **Cost is `O(T²)`** — measured at `T^2.06` in M4-L06.

---

## 13. Completion checklist

- [ ] I can define attention in one sentence without using the word.
- [ ] I worked §6 with a pencil before running the lab.
- [ ] I can explain why Q and K are separate projections.
- [ ] I can explain what `√d_k` prevents, mechanically.
- [ ] I proved permutation invariance to machine precision and understand what it forces.
- [ ] I saw that a shared Q/K projection cannot express an asymmetric relationship.
- [ ] I can explain multi-head's parameter cost.
- [ ] I can state two things attention weights do not tell me.
- [ ] I scored 8/11 on the quiz.

---

## 14. References

- Vaswani et al. (2017), *Attention Is All You Need*. <https://arxiv.org/abs/1706.03762> `[UNVERIFIED]`
- Bahdanau et al. (2014), *Neural Machine Translation by Jointly Learning to Align and Translate*.
  <https://arxiv.org/abs/1409.0473> `[UNVERIFIED]`
- Jain & Wallace (2019), *Attention is not Explanation*. <https://arxiv.org/abs/1902.10186>
  `[UNVERIFIED]`
- Wiegreffe & Pinter (2019), *Attention is not not Explanation* (the rebuttal).
  <https://arxiv.org/abs/1908.04626> `[UNVERIFIED]`

---

## 15. Next lesson

→ [M4-L08 — Queries, Keys, Values and Attention Scores, Worked by Hand](M4-L08-qkv-worked.md)

You have the idea and the properties. Next: a complete multi-head attention computation with every
number written out, so the mechanism stops being a formula and becomes arithmetic you can do.
