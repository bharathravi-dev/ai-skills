# M4-L08 — Queries, Keys, Values and Attention Scores, Worked by Hand

| | |
|---|---|
| **Lesson ID** | M4-L08 |
| **Difficulty** | 3 (Advanced) |
| **Estimated study time** | 2.5 hours |
| **Prerequisites** | [M4-L07](M4-L07-attention.md) |

---

> **This lesson is one long worked example.**
> Every number in a complete masked multi-head attention pass, computed by hand and then verified.
> Set aside a clear 45 minutes, take a pencil and paper, and work §6 line by line. There is no
> substitute for this and no shortcut through it — but you only have to do it once, and afterwards
> the mechanism is permanently yours.

---

## 1. Learning objectives

1. **Compute** a complete multi-head attention pass by hand, including the mask.
2. **Track** every tensor shape through the computation without looking them up.
3. **Split and recombine** heads correctly, and state where the split happens.
4. **Verify** your arithmetic against a reference implementation.
5. **Diagnose** the four most common implementation errors from their symptoms.

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **`d_model`** | The model's working dimension; every block's input and output width. |
| **`n_heads`** | How many attention heads run in parallel. |
| **`d_head`** | `d_model / n_heads` — each head's working dimension. |
| **`W_q, W_k, W_v`** | Projections producing queries, keys and values. |
| **`W_o`** | The output projection applied after concatenating heads. |
| **Score matrix** | `(T, T)` — every position's compatibility with every other. |
| **Mask** | `−∞` added to disallowed score entries, before the softmax. |
| **Head split** | Reshaping `(T, d_model)` into `(n_heads, T, d_head)`. |
| **Concatenation** | Reassembling head outputs back into `(T, d_model)`. |

---

## 3. Plain-language explanation

M4-L07 gave you the equation. This lesson runs it once, completely, with numbers small enough to
check.

**The five steps, and where people go wrong at each:**

| Step | What happens | The common error |
|---|---|---|
| 1. Project | `X` → Q, K, V | Using the same matrix for Q and K |
| 2. Split heads | `(T, d_model)` → `(h, T, d_head)` | Splitting the wrong axis |
| 3. Score and mask | `QKᵀ/√d_head`, add `−∞` | Masking **after** the softmax |
| 4. Softmax and weight | `softmax(scores) @ V` | Softmax over the wrong axis |
| 5. Concatenate and project | heads → `(T, d_model)` → `@ W_o` | Forgetting `W_o` entirely |

**The single most important detail:** the projections produce the **full** `d_model` width, and the
split into heads is a **reshape of that output**, not a separate set of smaller projections. One
matrix multiply, then a view. Real implementations always do it this way, and it is why multi-head
costs no extra parameters (M4-L07 §7.3 measured this).

---

## 4. Analogy

**A committee reading one document.** Each member (head) reads with a different brief, forms an
opinion, and the chair (`W_o`) combines the opinions into one recommendation.

### Where the analogy breaks

1. **Committee members read the whole document. Each head sees only its own `d_head` slice** of every
   vector — a projection, not a perspective.
2. **A chair weighs opinions deliberately. `W_o` is a learned matrix** with no notion of trust.
3. **Members can abstain. Every head always produces a full output**, even when it has learned to do
   nothing useful.
4. **A committee is assembled for a purpose. Heads are not assigned roles**; any specialisation is
   emergent, and many heads specialise into nothing identifiable.

---

## 5. Detailed technical explanation

### 5.1 Shapes, once, completely

For `T` tokens, `d_model = 4`, `n_heads = 2`, so `d_head = 2`:

| Stage | Shape | Note |
|---|---|---|
| `X` | `(3, 4)` | Input |
| `W_q, W_k, W_v` | `(4, 4)` each | **Full width, not per-head** |
| `Q, K, V` | `(3, 4)` each | Before splitting |
| After head split | `(2, 3, 2)` | `(n_heads, T, d_head)` |
| Scores per head | `(2, 3, 3)` | `(n_heads, T, T)` |
| Weights per head | `(2, 3, 3)` | Each row sums to 1 |
| Head outputs | `(2, 3, 2)` | |
| After concatenation | `(3, 4)` | Back to `d_model` |
| `W_o` | `(4, 4)` | |
| **Final output** | **`(3, 4)`** | **Same as the input** |

**The block is a `(T, d_model) → (T, d_model)` function.** That invariant is what lets blocks stack
(M4-L10), and checking it is the fastest way to find a shape bug.

### 5.2 The head split, precisely

```python
Q = X @ W_q                                  # (T, d_model)
Q = Q.reshape(T, n_heads, d_head)            # (T, h, d_head)
Q = Q.transpose(1, 0, 2)                     # (h, T, d_head)
```

**Head `i` gets columns `i*d_head : (i+1)*d_head`** of the projected output. Head 0 takes columns 0–1,
head 1 takes columns 2–3.

**The transpose matters.** Without it, the subsequent matrix multiply batches over the wrong axis and
you get an answer that is wrongly shaped — or worse, correctly shaped and wrong.

### 5.3 Masking, precisely

```python
scores = Q @ K.transpose(0, 2, 1) / np.sqrt(d_head)
scores = np.where(mask, -np.inf, scores)      # BEFORE softmax
weights = softmax(scores, axis=-1)
```

The causal mask is upper-triangular, excluding the diagonal — position `i` may attend to `0…i`.

**Use `−1e9` rather than `−inf` in practice.** A row that is entirely `−inf` produces `nan` through
softmax; `−1e9` degrades to a uniform distribution instead, which is recoverable. This matters when
padding and causal masks combine and a row can end up fully masked.

### 5.4 Concatenation and `W_o`

```python
out = weights @ V                             # (h, T, d_head)
out = out.transpose(1, 0, 2)                  # (T, h, d_head)
out = out.reshape(T, d_model)                 # (T, d_model)
out = out @ W_o                               # (T, d_model)
```

**`W_o` is not optional.** Without it the heads' outputs are merely stacked side by side and never
mix — head 0's information can only ever occupy dimensions 0–1. `W_o` is what lets them combine.

### 5.5 The four errors and their symptoms

| Error | Symptom |
|---|---|
| Softmax over the wrong axis | Columns sum to 1 instead of rows; the model trains but poorly |
| Mask applied after softmax | Rows no longer sum to 1; the model sees the future; loss collapses |
| Missing transpose in the split | Shape error, or a silently wrong batching |
| `W_o` omitted | Trains, underperforms, no error |

**Two of these four produce no error at all.** That is why the assertions in §7 exist, and why
"it runs" is not evidence that an attention implementation is correct.

### 5.6 Assumptions and limitations

- Biases are omitted throughout for clarity; real implementations often include them.
- Dropout and layer normalisation belong to the surrounding block (M4-L10).
- Grouped-query attention shares K and V across heads (M4-L17); the arithmetic here is the standard
  form.

---

## 6. Worked example — a complete masked multi-head pass

**Setup:** `T = 3`, `d_model = 4`, `n_heads = 2`, `d_head = 2`. Causal masking.

**Tokens:** `the`, `cat`, `sat`.

### 6.1 Inputs

```
X = [[1.0, 0.0, 0.5, 0.0],     the
     [0.0, 1.0, 0.0, 0.5],     cat
     [0.5, 0.5, 1.0, 0.0]]     sat
```

### 6.2 Projection matrices

```
W_q = [[1, 0, 0, 0],      W_k = [[0, 1, 0, 0],      W_v = [[1, 0, 0, 0],
       [0, 1, 0, 0],             [1, 0, 0, 0],             [0, 1, 0, 0],
       [0, 0, 1, 0],             [0, 0, 0, 1],             [0, 0, 2, 0],
       [0, 0, 0, 1]]             [0, 0, 1, 0]]             [0, 0, 0, 2]]
```

`W_q` is the identity — queries equal inputs. `W_k` swaps columns in pairs. `W_v` doubles the last two
columns. **Chosen so the arithmetic is checkable, not because they mean anything.**

### 6.3 Compute Q, K, V

`Q = X @ W_q = X`:

```
Q = [[1.0, 0.0, 0.5, 0.0],
     [0.0, 1.0, 0.0, 0.5],
     [0.5, 0.5, 1.0, 0.0]]
```

`K = X @ W_k` — swap columns (0,1) and (2,3):

```
K = [[0.0, 1.0, 0.0, 0.5],
     [1.0, 0.0, 0.5, 0.0],
     [0.5, 0.5, 0.0, 1.0]]
```

`V = X @ W_v` — double columns 2 and 3:

```
V = [[1.0, 0.0, 1.0, 0.0],
     [0.0, 1.0, 0.0, 1.0],
     [0.5, 0.5, 2.0, 0.0]]
```

### 6.4 Split into 2 heads

Head 0 takes columns 0–1; head 1 takes columns 2–3.

**Head 0:**

```
Q₀ = [[1.0, 0.0],    K₀ = [[0.0, 1.0],    V₀ = [[1.0, 0.0],
      [0.0, 1.0],          [1.0, 0.0],          [0.0, 1.0],
      [0.5, 0.5]]          [0.5, 0.5]]          [0.5, 0.5]]
```

**Head 1:**

```
Q₁ = [[0.5, 0.0],    K₁ = [[0.0, 0.5],    V₁ = [[1.0, 0.0],
      [0.0, 0.5],          [0.5, 0.0],          [0.0, 1.0],
      [1.0, 0.0]]          [0.0, 1.0]]          [2.0, 0.0]]
```

### 6.5 Head 0 — scores

`√d_head = √2 = 1.4142`. Compute `Q₀K₀ᵀ`:

```
row 0 (the):  [1.0,0.0]·[0.0,1.0]=0.00   ·[1.0,0.0]=1.00   ·[0.5,0.5]=0.50
row 1 (cat):  [0.0,1.0]·[0.0,1.0]=1.00   ·[1.0,0.0]=0.00   ·[0.5,0.5]=0.50
row 2 (sat):  [0.5,0.5]·[0.0,1.0]=0.50   ·[1.0,0.0]=0.50   ·[0.5,0.5]=0.50
```

Divide by 1.4142:

```
scores₀ = [[0.0000, 0.7071, 0.3536],
           [0.7071, 0.0000, 0.3536],
           [0.3536, 0.3536, 0.3536]]
```

### 6.6 Head 0 — apply the causal mask

Position `i` may attend to `0…i`. Set everything above the diagonal to `−∞`:

```
masked₀ = [[0.0000,   −∞,      −∞   ],
           [0.7071, 0.0000,    −∞   ],
           [0.3536, 0.3536, 0.3536]]
```

### 6.7 Head 0 — softmax, row by row

**Row 0** — only one live entry, so the weight must be 1:

```
weights₀[0] = [1.0000, 0.0000, 0.0000]
```

**Row 1** — `exp(0.7071) = 2.0281`, `exp(0.0000) = 1.0000`, sum `3.0281`:

```
weights₀[1] = [0.6698, 0.3302, 0.0000]
```

**Row 2** — all three entries are equal, so the weights are uniform:

```
weights₀[2] = [0.3333, 0.3333, 0.3333]
```

**Check every row sums to 1.** Row 0: 1.0000 ✓ Row 1: 0.6698 + 0.3302 = 1.0000 ✓ Row 2: 1.0000 ✓

### 6.8 Head 0 — weighted values

```
out₀[0] = 1.0000 × [1.0, 0.0]                                  = [1.0000, 0.0000]

out₀[1] = 0.6698 × [1.0, 0.0] + 0.3302 × [0.0, 1.0]            = [0.6698, 0.3302]

out₀[2] = 0.3333 × [1.0,0.0] + 0.3333 × [0.0,1.0] + 0.3333 × [0.5,0.5]
        = [0.3333, 0.0000] + [0.0000, 0.3333] + [0.1667, 0.1667]
        = [0.5000, 0.5000]
```

### 6.9 Head 1 — the same procedure

`Q₁K₁ᵀ`:

```
row 0:  [0.5,0.0]·[0.0,0.5]=0.00   ·[0.5,0.0]=0.25   ·[0.0,1.0]=0.00
row 1:  [0.0,0.5]·[0.0,0.5]=0.25   ·[0.5,0.0]=0.00   ·[0.0,1.0]=0.50
row 2:  [1.0,0.0]·[0.0,0.5]=0.00   ·[0.5,0.0]=0.50   ·[0.0,1.0]=0.00
```

Divided by 1.4142 and masked:

```
masked₁ = [[0.0000,   −∞,      −∞   ],
           [0.1768, 0.0000,    −∞   ],
           [0.0000, 0.3536, 0.0000]]
```

Softmax:

```
weights₁[0] = [1.0000, 0.0000, 0.0000]
weights₁[1] = [0.5441, 0.4559, 0.0000]        exp(0.1768)=1.1934, exp(0)=1
weights₁[2] = [0.2920, 0.4159, 0.2920]        exp(0.3536)=1.4242, sum=3.4242
```

Weighted values:

```
out₁[0] = [1.0000, 0.0000]
out₁[1] = 0.5441 × [1.0,0.0] + 0.4559 × [0.0,1.0]              = [0.5441, 0.4559]
out₁[2] = 0.2920 × [1.0,0.0] + 0.4159 × [0.0,1.0] + 0.2920 × [2.0,0.0]
        = [0.2920 + 0.5841, 0.4159] = [0.8761, 0.4159]
```

*(An aside worth having: the first draft of this lesson had `0.2887` here — the value you get if you
mistakenly normalise by `1 + 1.4242 + 1` computed as `3.4642`. The lab's assertion caught it, which is
exactly the argument for §7's assertions. Check your arithmetic against a reference; do not trust a
number because it looks plausible.)*

### 6.10 Concatenate

Head 0's output supplies columns 0–1, head 1's supplies columns 2–3:

```
concat = [[1.0000, 0.0000, 1.0000, 0.0000],
          [0.6698, 0.3302, 0.5441, 0.4559],
          [0.5000, 0.5000, 0.8761, 0.4159]]
```

Shape `(3, 4)` — back to `d_model`. ✓

### 6.11 Output projection

```
W_o = [[1, 0, 0, 0],
       [0, 1, 0, 0],
       [0, 0, 1, 0],
       [0, 0, 0, 1]]
```

The identity, so `output = concat`. **In a real model `W_o` is learned and this is where the heads'
information actually mixes** — without it, head 0's contribution is stuck in dimensions 0–1 forever.

### 6.12 Read the result

**Three things to notice, and the third is the point of the whole lesson:**

1. **Row 0 attends only to itself**, in both heads, with weight exactly 1.0000. The first token has no
   past. This is the causal mask working, and it is why the first token's representation is never
   contextual.

2. **The two heads produced different weights for the same row.** For `cat`, head 0 gave
   `[0.6698, 0.3302]` and head 1 gave `[0.5441, 0.4559]`; for `sat`, head 0 gave a flat
   `[0.3333, 0.3333, 0.3333]` and head 1 gave `[0.2920, 0.4159, 0.2920]`. Same input, same positions,
   different relationships — at identical parameter cost. That is multi-head's entire justification.

3. **Row 2's head-0 weights are exactly uniform** — `[0.3333, 0.3333, 0.3333]`. Its three scores were
   all 0.3536, so softmax could not distinguish them. **An untrained head defaults to averaging**, as
   M4-L07 §7.3 measured. Training changes this by learning projections that separate the scores, not
   by teaching the model to be selective.

---

## 7. Practical activity

**File:** [`labs/m4/l08_qkv_worked.py`](../../labs/m4/l08_qkv_worked.py)

**No API key, no network.**

```bash
source .venv/bin/activate
python labs/m4/l08_qkv_worked.py
```

Recomputes every number in §6 and asserts it matches, then deliberately introduces each of §5.5's four
errors and shows exactly which invariant each one breaks.

### 7.2 Expected output

`[EXECUTED]` on Python 3.12.3, NumPy 2.5.3, 2026-09-08. **Every assertion passes.**

```text

============================================================================
1. RECOMPUTING EVERY NUMBER IN THE WORKED EXAMPLE
============================================================================
  X (input, one row per token):
    the  [1.  0.  0.5 0. ]
    cat  [0.  1.  0.  0.5]
    sat  [0.5 0.5 1.  0. ]

  Q = X @ W_q   (W_q is the identity, so Q == X)
    the  [1.  0.  0.5 0. ]
    cat  [0.  1.  0.  0.5]
    sat  [0.5 0.5 1.  0. ]

  K = X @ W_k   (columns swapped in pairs)
    the  [0.  1.  0.  0.5]
    cat  [1.  0.  0.5 0. ]
    sat  [0.5 0.5 0.  1. ]

  V = X @ W_v   (columns 2 and 3 doubled)
    the  [1. 0. 1. 0.]
    cat  [0. 1. 0. 1.]
    sat  [0.5 0.5 2.  0. ]

  section 6.3 verified: Q, K, V all match.

  head split: (T=3, d_model=4) -> (n_heads=2, T=3, d_head=2)

    head 0  (columns 0-1)
      Q0 = [[1.0, 0.0], [0.0, 1.0], [0.5, 0.5]]
      K0 = [[0.0, 1.0], [1.0, 0.0], [0.5, 0.5]]
      V0 = [[1.0, 0.0], [0.0, 1.0], [0.5, 0.5]]

    head 1  (columns 2-3)
      Q1 = [[0.5, 0.0], [0.0, 0.5], [1.0, 0.0]]
      K1 = [[0.0, 0.5], [0.5, 0.0], [0.0, 1.0]]
      V1 = [[1.0, 0.0], [0.0, 1.0], [2.0, 0.0]]

  section 6.4 verified: both heads' Q, K, V match.

  head 0: raw Q.K^T
    the  [0.  1.  0.5]
    cat  [1.  0.  0.5]
    sat  [0.5 0.5 0.5]
  head 0: scaled by sqrt(d_head) = 1.4142, then masked
    the  [ 0.0000   -inf    -inf ]
    cat  [ 0.7071  0.0000   -inf ]
    sat  [ 0.3536  0.3536  0.3536]
  head 0: after softmax
    the  [1. 0. 0.]   sum 1.0000
    cat  [0.6698 0.3302 0.    ]   sum 1.0000
    sat  [0.3333 0.3333 0.3333]   sum 1.0000

  head 1: raw Q.K^T
    the  [0.   0.25 0.  ]
    cat  [0.25 0.   0.5 ]
    sat  [0.  0.5 0. ]
  head 1: scaled by sqrt(d_head) = 1.4142, then masked
    the  [ 0.0000   -inf    -inf ]
    cat  [ 0.1768  0.0000   -inf ]
    sat  [ 0.0000  0.3536  0.0000]
  head 1: after softmax
    the  [1. 0. 0.]   sum 1.0000
    cat  [0.5441 0.4559 0.    ]   sum 1.0000
    sat  [0.292  0.4159 0.292 ]   sum 1.0000

  sections 6.7 and 6.9 verified: all weights match to 4 dp.

  weighted values per head:
    head 0  the  [1. 0.]
    head 0  cat  [0.6698 0.3302]
    head 0  sat  [0.5 0.5]
    head 1  the  [1. 0.]
    head 1  cat  [0.5441 0.4559]
    head 1  sat  [0.8761 0.4159]

  sections 6.8 and 6.9 verified: head outputs match.

  concatenated -> (3, 4):
    the  [1. 0. 1. 0.]
    cat  [0.6698 0.3302 0.5441 0.4559]
    sat  [0.5    0.5    0.8761 0.4159]

  after W_o (identity here) -> (3, 4):
    the  [1. 0. 1. 0.]
    cat  [0.6698 0.3302 0.5441 0.4559]
    sat  [0.5    0.5    0.8761 0.4159]

  SHAPE INVARIANT: input (3, 4) -> output (3, 4)  OK
  EVERY NUMBER IN SECTION 6 VERIFIED.

============================================================================
2. THE THREE ASSERTIONS EVERY IMPLEMENTATION NEEDS
============================================================================
  implementation                        rows sum 1  mask respected       shape
  correct                                   PASS            PASS        PASS
  ERROR: softmax over axis -2 (columns)     FAIL            PASS        PASS
  ERROR: mask applied AFTER softmax         FAIL            PASS        PASS
  ERROR: W_o omitted                        PASS            PASS        PASS
  ERROR: divided by sqrt(d_model)           PASS            PASS        PASS

  Read the FAIL columns carefully:
    * wrong softmax axis  -> 'rows sum 1' FAILS. Caught.
    * mask after softmax  -> 'rows sum 1' FAILS (mass was removed after
      normalisation, so the rows no longer sum to 1). Caught.
    * W_o omitted         -> ALL THREE PASS. NOT CAUGHT.
    * wrong divisor       -> ALL THREE PASS. NOT CAUGHT.

  Two of the four errors are invisible to these assertions AND produce
  no exception. They simply make the model worse. That is why 'it runs'
  is not evidence that an attention implementation is correct.

============================================================================
3. HOW THE INVISIBLE ERRORS ACTUALLY SHOW UP
============================================================================
  W_o omitted -- with the IDENTITY W_o used in the lesson there is no
  difference at all, which is why the lesson's example cannot reveal it.
    identity W_o, difference: 0.000000
    a LEARNED W_o, difference: 1.390710

  The consequence is structural, not numerical: without W_o, head 0's
  output can only ever occupy dimensions 0-1 of the block's output.
  Information cannot move between heads. The model trains, produces no
  error, and is permanently less expressive.

  wrong divisor -- sqrt(d_model)=2.0000 vs sqrt(d_head)=1.4142
    scores are 1.4142x too small,
    so the weights are too UNIFORM at initialisation:
      correct head-1 row 2 weights: [0.292  0.4159 0.292 ]
      wrong   head-1 row 2 weights: [0.3045 0.391  0.3045]
      entropy 1.0838 -> 1.0913  (uniform = 1.0986)
    The divisor grows with d_head, so at realistic sizes (d_head 64 vs
    d_model 4096) the error is an 8x scale mistake, not a 1.4x one.

============================================================================
4. THE MASK, PROVEN
============================================================================
  Change ONLY the last token, then check whether earlier positions'
  outputs moved. With correct causal masking they must not.

  position    original output               after change                     same?
  0 (the)     [1. 0. 1. 0.]                 [1. 0. 1. 0.]                     True
  1 (cat)     [0.6698 0.3302 0.5441 0.4559] [0.6698 0.3302 0.5441 0.4559]     True
  2 (sat)     [0.5    0.5    0.8761 0.4159] [0.5112 0.4888 0.4949 0.778 ]    False

  Positions 0 and 1 are bit-identical; position 2 changed, as it must.
  The past cannot see the future.

  the same test WITHOUT the mask:
    positions 0-1 identical? False
    max change at position 0: 0.5041
  Without the mask, changing the LAST token changes the FIRST token's
  output. In training that means the answer is visible in the input
  (M4-L05 measured the resulting loss collapse).

============================================================================
5. SHAPES AND MEMORY AT REALISTIC SIZES
============================================================================
         T  heads      score tensor        fp32       fp16
       512     32        32x512x512       0.03G      0.02G
      2048     32      32x2048x2048       0.50G      0.25G
      8192     32      32x8192x8192       8.00G      4.00G
     32768     32    32x32768x32768     128.00G     64.00G

  The score tensor is n_heads x T x T -- quadratic in T and linear in
  heads. At 32k context with 32 heads it is 128 GB in fp32 if
  materialised, which is why fused kernels that never form it exist.
  The COMPUTE is still quadratic (M4-L06 measured T^2.06).

Done.
```

### 7.3 Reading the result

**Section 1 asserts every value in §6** — Q, K, V, both heads' splits, both weight matrices, both head
outputs, and the shape invariant. All pass.

**It also caught an error in the first draft of this lesson.** I had written head 1's row-2 weights as
`[0.2887, 0.4226, 0.2887]`; the correct values are `[0.2920, 0.4159, 0.2920]`, and the head output was
`[0.8761, 0.4159]` rather than `[0.8661, 0.4226]`. The numbers looked entirely plausible — they summed
to 1, they had the right shape, the middle one was largest as expected. **Plausibility is not
correctness**, which is the case for §7's assertions stated as an anecdote rather than a principle.

**Section 2 is the result to take away from this lesson.**

| Implementation | Rows sum to 1 | Mask respected | Shape | Caught? |
|---|---|---|---|---|
| Correct | PASS | PASS | PASS | — |
| Softmax over the wrong axis | **FAIL** | PASS | PASS | ✅ |
| Mask applied after softmax | **FAIL** | PASS | PASS | ✅ |
| **`W_o` omitted** | PASS | PASS | PASS | ❌ |
| **Divided by `√d_model`** | PASS | PASS | PASS | ❌ |

**Two of the four errors pass every assertion and raise no exception.** They do not crash, they do not
produce warnings, and they do not violate any structural invariant. They simply make the model worse,
and you find out — if you ever find out — as a quality number that is lower than it should be, with no
indication why.

Note also *how* the mask-after-softmax bug is caught: not by the "mask respected" check (the masked
entries genuinely are zero — they were zeroed *after* normalisation) but by "rows sum to 1", because
probability mass was removed after the softmax had already normalised. **The assertion that catches a
bug is often not the one you would have predicted**, which is an argument for writing all three rather
than the one that seems relevant.

**Section 3 shows how the two invisible errors actually manifest.**

With the lesson's identity `W_o`, omitting it makes **no difference at all** (0.000000) — the lesson's
own example cannot reveal this bug. With a *learned* `W_o` the difference is **1.390710**. But the real
consequence is structural rather than numerical: **without `W_o`, head 0's output can only ever occupy
dimensions 0–1 of the block's output.** Information cannot move between heads, ever. The model trains
fine and is permanently less expressive.

The wrong-divisor error is small here — `√4 / √2 = 1.41×`, moving row-2 entropy from 1.0838 to 1.0913
against a uniform 1.0986. **At realistic sizes it is not small.** With `d_head` 64 and `d_model` 4,096
the divisor is wrong by `√4096/√64 = 8×`, which flattens the weights substantially at initialisation
and slows training for no visible reason.

**Section 4 proves the mask by construction.** Changing only the third token leaves positions 0 and 1
**bit-identical** and changes position 2, exactly as required. Without the mask, changing the *last*
token changes the *first* token's output by up to **0.5041** — which in training means the answer is
present in the input, and M4-L05 §7.3 measured the resulting loss collapse to 0.0006.

**Section 5 scales the shapes up.** The score tensor is `n_heads × T × T`:

| `T` | Heads | fp32 | fp16 |
|---|---|---|---|
| 512 | 32 | 0.03 GB | 0.02 GB |
| 8,192 | 32 | 8.00 GB | 4.00 GB |
| 32,768 | 32 | **128.00 GB** | 64.00 GB |

**128 GB for the score tensor alone at 32k context.** No accelerator holds that, which is why fused
implementations that never materialise the matrix exist. The *compute* remains quadratic regardless —
M4-L06 measured `T^2.06` — so long context is cheaper than this table suggests but never free.

---

## 8. Common mistakes and troubleshooting

1. **Softmax over the wrong axis.** Assert rows sum to 1.
2. **Masking after softmax.** Assert masked positions are exactly 0.
3. **Forgetting the transpose in the head split.**
4. **Omitting `W_o`.** No error; just a worse model.
5. **Using `−inf` where a row can be fully masked.** Use `−1e9`.
6. **Splitting heads before projecting** instead of after.
7. **Dividing by `√d_model` instead of `√d_head`.**

| Symptom | Likely cause | Check |
|---|---|---|
| Rows do not sum to 1 | Wrong softmax axis, or mask after softmax | `assert np.allclose(w.sum(-1), 1)` |
| Model sees the future | Mask after softmax | Assert the upper triangle is exactly 0 |
| Shape error at concatenation | Missing transpose | Print shapes at every step |
| `nan` in the weights | A fully-masked row with `−inf` | Use `−1e9` |
| Trains but underperforms | `W_o` missing | Check the parameter count |
| Weights too sharp at init | Divided by `√d_model` | Divide by `√d_head` |

---

## 9. Security, privacy, reliability, cost

- **Reliability.** Two of the four common errors produce **no error message**. Write the assertions —
  rows sum to 1, masked entries are exactly 0, output shape equals input shape — and run them in CI.
- **Security.** A mask bug that lets a position see later tokens is a correctness failure in training
  and a potential **information-leak** in a shared-context setting: if several users' content is
  batched, a masking error can let one position attend across a boundary. Assert masks, always.
- **Cost.** The `(T, T)` score matrix per head is what makes attention quadratic. `n_heads × T × T`
  floats materialised at once is the memory figure to check before raising context length.
- **Privacy.** Attention weights derived from user content are derived data. Do not log them by
  default (M4-L07 §9).

---

## 10. Exercises

### Exercise 1 — Beginner (~30 min)

1. Reproduce §6.5's `scores₀` matrix entirely by hand.
2. Reproduce `weights₀[1] = [0.6698, 0.3302, 0.0000]`, showing the exponentials.
3. Compute `out₀[2]` and confirm `[0.5000, 0.5000]`.
4. Write every shape from §5.1 from memory, then check.
5. Explain in one sentence why row 0's weights are `[1, 0, 0]` in both heads.

### Exercise 2 — Intermediate (~40 min)

1. Implement the pass and assert it matches every §6 value to 4 decimal places.
2. Add three assertions: rows sum to 1, masked entries are exactly 0, output shape equals input shape.
3. Break the softmax axis and report which assertion fires.
4. Move the mask after the softmax and report which assertion fires.
5. Remove `W_o` (set it to the identity) on a *randomly initialised* model and measure the difference
   in output. Explain why it is not zero in general.

### Exercise 3 — Challenge (~50 min)

1. Extend to 4 heads at `d_model = 8` and verify the shape invariant holds.
2. Implement both the reshape-based head split and an explicit per-head loop. Assert they agree
   bit-for-bit.
3. Add a padding mask alongside the causal mask and construct a case where a row is fully masked.
   Show `−inf` produces `nan` and `−1e9` does not.
4. Measure memory for the score tensor at `T` = 512, 4096, 32768 with 32 heads in float32 and
   float16. State which fit in 8 GB.
5. Implement grouped-query attention (K and V shared across pairs of heads) and report the KV memory
   saving and the output difference.
6. Write a property test: for random inputs, assert that output `i` is unchanged when tokens after
   `i` are altered. Show it failing when the mask is removed.

---

## 11. Quiz

*(Answers: [`answer-keys/module-04-answers.md`](../../answer-keys/module-04-answers.md#m4-l08).)*

**Q1.** With `d_model` 512 and 8 heads, `d_head` is:

- A. 64  B. 4096  C. 512  D. 8

**Q2.** The projections `W_q`, `W_k`, `W_v` have shape:

- A. `(d_head, d_head)`, one small matrix per head.
- B. `(T, d_model)`, matching the input sequence length.
- C. `(n_heads, d_model, d_head)`, one slice per head.
- D. `(d_model, d_model)`, split into heads afterwards.

**Q3.** The causal mask must be applied:

- A. To the values, before they are weighted and summed.
- B. To the scores, before the softmax is taken.
- C. To the weights, immediately after the softmax.
- D. To the input embeddings, before any projection.

**Q4.** After masking, row 0 of the weight matrix is:

- A. `[1, 0, 0]`, since the first token has no past to attend to.
- B. `[0.33, 0.33, 0.33]`, an average over the whole sequence.
- C. `[0, 0, 0]`, since everything is masked at position zero.
- D. Undefined, because softmax of a single element is unstable.

**Q5.** Why is `−1e9` preferred to `−inf` for masking?

- A. It is faster to compute on floating-point hardware.
- B. A fully-masked row gives `nan` with `−inf` but not `−1e9`.
- C. `−inf` is not representable in float16 arithmetic.
- D. It makes the resulting attention weights slightly sharper.

**Q6.** What does `W_o` do?

- A. Normalises the attention weights so each row sums to one.
- B. Rescales the scores before the softmax is applied.
- C. Mixes the concatenated head outputs across all dimensions.
- D. Projects the input down to the per-head dimension.

**Q7.** In §6, the two heads gave different weights for row 1 because:

- A. They were trained on different subsets of the data.
- B. Head 1 received a larger share of the input dimensions.
- C. Their projections select different slices of the vectors.
- D. The causal mask is applied differently to each head.

**Q8.** Row 2 of head 0 has uniform weights because:

- A. Uniform weights are the correct answer for that position.
- B. The mask allows all three positions equally at row 2.
- C. Its three scores were identical, so softmax cannot separate them.
- D. Softmax always returns uniform weights on the final row.

**Q9.** Which two errors produce **no** error message?

- A. Wrong softmax axis, and omitting `W_o`.
- B. Wrong softmax axis, and a missing transpose in the split.
- C. Masking after softmax, and dividing by `√d_model`.
- D. Omitting `W_o`, and dividing by `√d_model`.

**Q10.** The output shape of an attention block is:

- A. `(T, d_head)`, one vector per head per position.
- B. `(n_heads, T, d_head)`, kept split for the next block.
- C. `(T, d_model)` — identical to the input shape.
- D. `(T, T)`, matching the attention weight matrix.

**Q11.** *(Written, rubric-graded.)* In under 120 words, describe the three assertions you would add to
an attention implementation and what specific bug each one catches.

---

## 12. Revision notes

- **`d_head = d_model / n_heads`.** Projections are **full width** `(d_model, d_model)`; the head split
  is a **reshape of the output**, not separate small matrices. One matmul, then a view.
- **Shapes:** `X (T,d)` → Q,K,V `(T,d)` → split `(h,T,d_head)` → scores `(h,T,T)` → weights `(h,T,T)`
  → out `(h,T,d_head)` → concat `(T,d)` → `@W_o` → **`(T,d)`**.
- **The block is `(T,d) → (T,d)`.** That invariant is what lets blocks stack, and the fastest shape-bug
  check available.
- **Mask the scores, before the softmax.** Use **`−1e9`**, not `−inf`, so a fully-masked row degrades
  to uniform rather than `nan`.
- **Divide by `√d_head`, not `√d_model`.**
- **`W_o` is not optional** — without it, head 0's information is confined to dimensions 0–1 forever.
- **Row 0 always attends only to itself** under causal masking. The first token is never contextual.
- **Different heads give different weights for the same row.** Same input, different relationships,
  identical parameter cost.
- **Equal scores give uniform weights.** An untrained head averages; training separates the scores.
- **Two of the four common errors pass every assertion and raise nothing.** Measured: omitting `W_o`
  and dividing by `√d_model` both PASS "rows sum to 1", "mask respected" and "shape" — they only make
  the model worse. **"It runs" is not evidence.**
- Note *which* assertion catches the mask-after-softmax bug: **"rows sum to 1"**, not "mask
  respected" — the masked entries genuinely are zero, but mass was removed after normalisation. Write
  all three; the one that fires is often not the one you expect.

---

## 13. Completion checklist

- [ ] I worked §6 with a pencil, end to end, before running the lab.
- [ ] I reproduced `scores₀`, `weights₀[1]` and `out₀[2]` by hand.
- [ ] I can write every shape from memory.
- [ ] I can explain why the head split is a reshape, not separate matrices.
- [ ] I know why `−1e9` beats `−inf`.
- [ ] I wrote the three assertions and saw each one catch its bug.
- [ ] I can name the two errors that pass all three assertions.
- [ ] I saw that the score tensor is 128 GB at 32k context with 32 heads.
- [ ] I scored 8/11 on the quiz.

---

## 14. References

- Vaswani et al. (2017), *Attention Is All You Need*, §3.2.
  <https://arxiv.org/abs/1706.03762> `[UNVERIFIED]`
- Alammar, *The Illustrated Transformer*. <https://jalammar.github.io/illustrated-transformer/>
  `[UNVERIFIED]`
- Karpathy, *nanoGPT*. <https://github.com/karpathy/nanoGPT> `[UNVERIFIED]`

---

## 15. Next lesson

→ [M4-L09 — Positional Information](M4-L09-positional-encoding.md)

You can compute attention completely. Next: the piece M4-L07 proved was missing — how order gets into
a mechanism that is provably blind to it.
