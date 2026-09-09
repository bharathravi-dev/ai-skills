# M3-L02 — Dot Products, Norms and Cosine Similarity by Hand

| | |
|---|---|
| **Lesson ID** | M3-L02 |
| **Difficulty** | 2 (Core) |
| **Estimated study time** | 2.0 hours |
| **Prerequisites** | [M3-L01](M3-L01-vectors-matrices.md) |

---

> **This is the most directly useful mathematics lesson in the course.** Every semantic search in
> Modules 6 and 7 is a cosine similarity. Every attention score in Module 4 is a dot product. When
> retrieval returns the wrong documents, this is the level at which you debug it.

---

## 1. Learning objectives

1. **Compute** a dot product by hand and **state** what it measures.
2. **Compute** a vector's magnitude (norm) by hand.
3. **Compute** cosine similarity by hand and **interpret** the result.
4. **Explain** why cosine is preferred to Euclidean distance for text embeddings.
5. **Explain** why normalised vectors make dot product and cosine identical, and why that matters for
   performance.

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **Dot product** | Multiply corresponding elements of two vectors and sum the results. Written `a · b`. |
| **Magnitude / norm** | A vector's length. Written `‖a‖`. |
| **L2 norm (Euclidean)** | The usual length: the square root of the sum of squared elements. |
| **L1 norm (Manhattan)** | The sum of absolute values. |
| **Unit vector** | A vector of length exactly 1. |
| **Normalisation** | Dividing a vector by its own norm to make it a unit vector. |
| **Cosine similarity** | The cosine of the angle between two vectors. Range −1 to 1. |
| **Cosine distance** | `1 − cosine similarity`. Range 0 to 2. |
| **Euclidean distance** | The straight-line distance between two points. |
| **Orthogonal** | At right angles; dot product zero. |
| **Inner product** | The general name for the dot product. |
| **Sigma notation** (Σ) | "Sum of". `Σᵢ aᵢbᵢ` means add up `aᵢbᵢ` for every `i`. |

---

## 3. Plain-language explanation

Two vectors. You want one number saying how similar they are.

**The dot product** multiplies matching positions and adds up the results:

```
a = [3, 4]
b = [2, 1]

a · b = (3 × 2) + (4 × 1) = 6 + 4 = 10
```

That is the whole operation. It is a measure of **how much the two vectors agree**: large and positive
when they point the same way, near zero when they are unrelated, negative when they oppose.

But the dot product has a problem: **it grows with the vectors' lengths**. Double one vector and the
dot product doubles, even though its *direction* is unchanged. For text embeddings that is wrong —
"refund" and "refunds" should be similar regardless of magnitude.

**The fix is to divide out the lengths**, and that is cosine similarity:

$$\cos(\theta) = \frac{a \cdot b}{\|a\| \times \|b\|}$$

Reading every symbol: `a · b` is the dot product from above. `‖a‖` is the length of `a`.
`θ` (theta) is the angle between the vectors. The result is between −1 and 1.

| Cosine | Angle | Meaning |
|---|---|---|
| 1.0 | 0° | Identical direction |
| 0.7 | ~45° | Similar |
| 0.0 | 90° | Unrelated (orthogonal) |
| −1.0 | 180° | Opposite |

**In practice, for text embeddings, cosine similarity is the number your vector database returns when
you search.** Everything in Module 6 rests on it.

---

## 4. Analogy

**Two people pushing a cart.** The dot product measures how much their effort combines. Pushing in
the same direction: large positive. At right angles: zero contribution to each other. Opposing: 
negative.

Cosine similarity asks only **"how aligned are they?"**, ignoring how strong each push is.

### Where the analogy breaks

1. **Physical directions are in 2 or 3 dimensions. Embeddings have hundreds.** You cannot picture
   1,536 dimensions, and intuitions built in 2-D mislead — see §5.6 on high-dimensional behaviour.
2. **Force has a real physical meaning; embedding dimensions have none individually.** No single
   dimension is "the refund dimension". Only the whole pattern carries meaning.
3. **The analogy suggests negative similarity is common.** For most modern text embeddings, values
   cluster in a narrow positive band, so 0.0 is not the practical midpoint (§5.7). This surprises
   people badly when they set thresholds.
4. **Carts exist in a space with a fixed origin. Embedding space has no meaningful origin**, which
   is exactly why angle beats distance.

---

## 5. Detailed technical explanation

### 5.1 The dot product

For vectors of length *n*:

$$a \cdot b = \sum_{i=1}^{n} a_i b_i = a_1b_1 + a_2b_2 + \cdots + a_nb_n$$

`Σ` means "add up over all `i`". `aᵢ` is the *i*-th element.

```python
a = np.array([3.0, 4.0])
b = np.array([2.0, 1.0])
np.dot(a, b)     # 10.0
a @ b            # 10.0  - same thing
(a * b).sum()    # 10.0  - element-wise then sum
```

**Both vectors must have the same length.** Different lengths is an error, and it is usually a bug in
how you built them (a model mismatch — M6-L02).

**Properties worth knowing:**

- Commutative: `a · b = b · a`.
- `a · a = ‖a‖²` — a vector dotted with itself gives its squared length. This is used constantly.
- If `a · b = 0` and neither is the zero vector, they are **orthogonal**.

### 5.2 The norm

The L2 norm is Pythagoras, extended to *n* dimensions:

$$\|a\| = \sqrt{\sum_{i=1}^{n} a_i^2} = \sqrt{a_1^2 + a_2^2 + \cdots + a_n^2}$$

```
a = [3, 4]
‖a‖ = √(3² + 4²) = √(9 + 16) = √25 = 5
```

The classic 3-4-5 triangle. In 1,536 dimensions the formula is identical — just more terms.

```python
np.linalg.norm(a)                  # 5.0
np.sqrt(np.dot(a, a))              # 5.0  - same, via a · a = ‖a‖²
np.linalg.norm(matrix, axis=1)     # one norm per ROW (M3-L01 axis rule)
```

`axis=1` for a `(n_docs, n_dims)` matrix gives one norm per document — the dimension axis collapses.

**Normalisation** divides a vector by its own norm:

```
â = a / ‖a‖ = [3/5, 4/5] = [0.6, 0.8]
‖â‖ = √(0.36 + 0.64) = √1 = 1  ✓
```

The hat (`â`) conventionally denotes a unit vector.

### 5.3 Cosine similarity, fully worked

$$\cos(\theta) = \frac{a \cdot b}{\|a\| \|b\|}$$

With `a = [3, 4]` and `b = [2, 1]`:

1. `a · b = 3×2 + 4×1 = 10`
2. `‖a‖ = √(9 + 16) = 5`
3. `‖b‖ = √(4 + 1) = √5 ≈ 2.2361`
4. `cos = 10 / (5 × 2.2361) = 10 / 11.1803 ≈ **0.8944**`

An angle of about 26.6°, so the vectors are fairly well aligned.

**The scale-invariance check.** Take `c = [6, 8]` — exactly `a` doubled:

- `c · b = 6×2 + 8×1 = 20` — the **dot product doubled**.
- `‖c‖ = √(36 + 64) = 10` — the norm doubled too.
- `cos = 20 / (10 × 2.2361) = 20 / 22.3607 = **0.8944**` — **identical**.

The dot product changed; the cosine did not. That is precisely the property you want when comparing
text.

### 5.4 Cosine versus Euclidean distance

Euclidean distance measures the gap between the *points*:

$$d(a,b) = \sqrt{\sum_i (a_i - b_i)^2}$$

For `a = [3,4]`, `c = [6,8]`: `d = √(9 + 16) = 5`. They are **5 apart** — yet cosine says they are
**identical in direction** (1.0).

| Measure | Sensitive to | Use for |
|---|---|---|
| **Cosine** | Direction only | **Text embeddings** — the default |
| **Euclidean** | Direction *and* magnitude | When magnitude is meaningful (physical measurements) |
| **Dot product** | Direction and both magnitudes | Normalised vectors; some ANN indexes |

**Why cosine for text:** embedding magnitude often correlates with things you do not care about —
document length, token frequency, how "confident" the encoder was. Two documents saying the same
thing at different lengths should be similar. Cosine ignores magnitude; Euclidean punishes it.

### 5.5 The optimisation that matters at scale

**If both vectors are already normalised, cosine similarity *is* the dot product**, because the
denominator is 1 × 1:

$$\cos(\theta) = \frac{a \cdot b}{1 \times 1} = a \cdot b$$

This is not a curiosity — it is how production systems are built:

1. **Normalise every embedding once, at indexing time.**
2. **At query time, use a plain dot product**, skipping two norms and a division per comparison.

For a million-document search that removes a million square roots per query. Most vector databases
expose this as an "inner product" or "dot product" metric and expect pre-normalised vectors —
**and if you feed them un-normalised vectors, the rankings are silently wrong**, because longer
documents score higher regardless of relevance. The lab demonstrates that failure.

### 5.6 High-dimensional behaviour

Two facts that break 2-D intuition:

**Random high-dimensional vectors are nearly orthogonal.** Pick two random 1,536-dimensional vectors
and their cosine will be very close to 0. In 2-D, two random vectors have a cosine averaging about
0.64 in absolute value; in 1,536 dimensions it collapses toward zero. The lab measures this.

**Consequence:** in high dimensions, *any* meaningful similarity stands out clearly against a
near-zero background. This is why embedding search works at all.

**Distances concentrate.** As dimensions grow, the distance between the nearest and farthest points
in a random set becomes proportionally smaller — the "curse of dimensionality". Real embeddings are
not uniformly random (they lie on a lower-dimensional manifold), which is why retrieval still works,
but it is why absolute thresholds transfer badly between models.

### 5.7 Interpreting scores in practice

**Do not assume 0.0 is the midpoint.** Many modern text embedding models produce similarities
clustered in a narrow band — often 0.6 to 0.9 for almost any pair of English sentences, because they
share language structure. A score of 0.75 may mean "unrelated" for one model and "highly relevant"
for another.

**Therefore:**

- **Never hard-code a similarity threshold** taken from a tutorial or another model.
- **Calibrate on your own data**: score known-relevant and known-irrelevant pairs and look at the
  distributions (M6-L13).
- **Relative ranking is more reliable than absolute score.** "Top 5" survives a model change;
  "score > 0.8" does not.

This matters directly for the abstention threshold in M7-L13.

### 5.8 Assumptions and limitations

- Cosine requires non-zero vectors; a zero vector has undefined direction and division by zero.
- Cosine similarity between embeddings from **different models** is meaningless, even if the
  dimensions match (M6-L02).
- Floating-point error can put a computed cosine marginally outside [−1, 1]; clip before `arccos`.
- Cosine ignores magnitude — which is a limitation when magnitude *is* informative.

---

## 6. Worked example — ranking documents by hand

Three 4-dimensional document embeddings and one query. Small enough to compute entirely on paper.

```
query = [0.8, 0.2, 0.1, 0.0]      "refund policy"

doc0  = [0.9, 0.1, 0.0, 0.2]      "refund policy details"
doc1  = [0.1, 0.0, 0.9, 0.3]      "shipping times"
doc2  = [1.6, 0.4, 0.2, 0.0]      "refund policy" repeated twice - same direction, double length
```

**Step 1 — dot products.**

- `q · doc0 = 0.8×0.9 + 0.2×0.1 + 0.1×0.0 + 0.0×0.2 = 0.72 + 0.02 + 0 + 0 = **0.74**`
- `q · doc1 = 0.8×0.1 + 0.2×0.0 + 0.1×0.9 + 0.0×0.3 = 0.08 + 0 + 0.09 + 0 = **0.17**`
- `q · doc2 = 0.8×1.6 + 0.2×0.4 + 0.1×0.2 + 0.0×0.0 = 1.28 + 0.08 + 0.02 + 0 = **1.38**`

**By raw dot product the ranking is doc2 (1.38) > doc0 (0.74) > doc1 (0.17).**

**Step 2 — norms.**

- `‖q‖ = √(0.64 + 0.04 + 0.01 + 0) = √0.69 ≈ **0.8307**`
- `‖doc0‖ = √(0.81 + 0.01 + 0 + 0.04) = √0.86 ≈ **0.9274**`
- `‖doc1‖ = √(0.01 + 0 + 0.81 + 0.09) = √0.91 ≈ **0.9539**`
- `‖doc2‖ = √(2.56 + 0.16 + 0.04 + 0) = √2.76 ≈ **1.6613**`

Note `doc2`'s norm is much larger — it is the same direction, twice the length.

**Step 3 — cosine similarities.**

- `doc0: 0.74 / (0.8307 × 0.9274) = 0.74 / 0.7704 ≈ **0.9605**`
- `doc1: 0.17 / (0.8307 × 0.9539) = 0.17 / 0.7924 ≈ **0.2145**`
- `doc2: 1.38 / (0.8307 × 1.6613) = 1.38 / 1.3800 ≈ **1.0000**`

**By cosine the ranking is doc2 (1.000) > doc0 (0.961) > doc1 (0.215).**

**Step 4 — what changed, and what did not.**

The *order* is the same here, but look at the **numbers**:

| | doc0 | doc1 | doc2 |
|---|---|---|---|
| Dot product | 0.74 | 0.17 | **1.38** |
| Cosine | 0.961 | 0.215 | **1.000** |

By dot product, doc2 scores **1.86× higher** than doc0. By cosine, it scores **1.04× higher**. The dot
product is rewarding doc2 mostly for being *longer*, not for being more relevant. `doc2` is literally
the query direction doubled, so cosine correctly reports 1.000 — a perfect direction match — while the
dot product inflates it.

**Step 5 — where it actually breaks the ranking.** Now consider a long, rambling, only-vaguely-related
document with a large norm. Its dot product with the query can exceed that of a short, perfectly
relevant one. **The ranking inverts**, and your search returns waffle. The lab constructs exactly this
case.

**Step 6 — the normalisation shortcut.** Normalise everything first:

- `q̂ = q / 0.8307 = [0.9631, 0.2408, 0.1204, 0.0]`
- `d̂0 = doc0 / 0.9274 = [0.9704, 0.1078, 0.0, 0.2157]`
- `q̂ · d̂0 = 0.9631×0.9704 + 0.2408×0.1078 + 0.1204×0 + 0×0.2157`
  `= 0.9346 + 0.0260 + 0 + 0 = **0.9606**`

Which matches the cosine from step 3 (0.9605, the difference being rounding). **A plain dot product on
normalised vectors gives cosine similarity** — the §5.5 optimisation, verified by hand.

---

## 7. Practical activity

**File:** [`labs/m3/l02_similarity.py`](../../labs/m3/l02_similarity.py)

**Requires the venv:**

```bash
source .venv/bin/activate
python labs/m3/l02_similarity.py
```

Reproduces every hand calculation above, demonstrates scale-invariance, constructs the case where an
un-normalised dot product **inverts the correct ranking**, verifies the normalisation shortcut,
measures its speed advantage at scale, and shows how near-orthogonality emerges as dimensions grow.

### 7.1 Important lines

| Construct | Why |
|---|---|
| `np.dot(a, b)` / `a @ b` | The dot product. |
| `np.linalg.norm(a)` | The L2 norm. |
| `np.linalg.norm(M, axis=1, keepdims=True)` | One norm per row, shaped for broadcasting (M3-L01). |
| `M / norms` | Normalising every row at once. |
| `normalised @ query` | Cosine for the whole corpus in one operation. |
| `np.argsort(-scores)` | Ranking, highest first. |

### 7.2 Expected output

`[EXECUTED]` 2026-09-08 with numpy 2.5.3, Python 3.12.3. Timings vary:

```
==========================================================================
DOT PRODUCTS, NORMS AND COSINE SIMILARITY
==========================================================================

--------------------------------------------------------------------------
1. THE HAND CALCULATION, VERIFIED
--------------------------------------------------------------------------
  a = [3. 4.], b = [2. 1.]
    a . b   = 3x2 + 4x1 = 6 + 4          = 10.0
    ||a||   = sqrt(9 + 16) = sqrt(25)    = 5.0
    ||b||   = sqrt(4 + 1)  = sqrt(5)     = 2.2361
    cos     = 10.0 / (5.0 x 2.2361) = 0.8944
    angle   = 26.6 degrees

  SCALE INVARIANCE - c = a doubled = [6. 8.]
    c . b   = 20.0    <- dot product DOUBLED
    ||c||   = 10.0     <- norm doubled too
    cos     = 0.8944   <- IDENTICAL to cos(a, b)

  Euclidean distance between a and c: 5.0000
    Cosine says 'identical direction'; Euclidean says '5 apart'.
    cos(a, c) = 1.0000

--------------------------------------------------------------------------
2. RANKING THE SECTION 6 CORPUS
--------------------------------------------------------------------------
  query = [0.8 0.2 0.1 0. ], ||query|| = 0.8307

  document                             dot     norm    cosine
  doc0 refund policy details        0.7400   0.9274    0.9606
  doc1 shipping times               0.1700   0.9539    0.2145
  doc2 refund policy (x2 length)    1.3800   1.6613    1.0000

  ranking by dot product : ['doc2', 'doc0', 'doc1']
  ranking by cosine      : ['doc2', 'doc0', 'doc1']

  Same ORDER here, but look at the ratios:
    by dot product, doc2 scores 1.86x doc0
    by cosine,      doc2 scores 1.04x doc0
  doc2 is literally the query direction doubled. Cosine correctly
  reports 1.0000 (perfect direction match). The dot product
  inflates it for being longer.

--------------------------------------------------------------------------
3. WHERE THE DOT PRODUCT ACTIVELY BREAKS THE RANKING
--------------------------------------------------------------------------
  document                             dot     norm    cosine
  doc0 SHORT, highly relevant       0.7400   0.9274    0.9606
  doc1 shipping times               0.1700   0.9539    0.2145
  doc3 LONG, vaguely related        1.3100   2.3108    0.6825

  ranking by dot product : ['doc3 ', 'doc0 ', 'doc1 ']
  ranking by cosine      : ['doc0 ', 'doc3 ', 'doc1 ']

  THE RANKINGS DISAGREE. The long, vaguely-related document wins
  on raw dot product purely because its norm is larger. Cosine
  puts the short, highly relevant document first, correctly.

  This is what a user sees as 'search returns waffle'. No error
  is raised. The scores look reasonable. The order is wrong.

--------------------------------------------------------------------------
4. THE NORMALISATION SHORTCUT, VERIFIED
--------------------------------------------------------------------------
  corpus norms shape (keepdims=True): (3, 1)
  norms after normalising: [1. 1. 1.]
    all 1.0, as required

  document                           full cosine  normalised dot
  doc0 refund policy details            0.960634        0.960634
  doc1 shipping times                   0.214538        0.214538
  doc2 refund policy (x2 length)        1.000000        1.000000

  identical to floating-point precision? True

  So: normalise ONCE at index time, then a plain dot product at
  query time gives cosine similarity for free.

--------------------------------------------------------------------------
5. WHY THAT SHORTCUT MATTERS AT SCALE
--------------------------------------------------------------------------
  Scoring 1 query against 100,000 documents of 768 dimensions:
    full cosine (norms every time) :   672.66 ms
    plain dot on pre-normalised    :    16.55 ms
    speed-up                       :     40.6x

  The norms were computed ONCE at index time instead of on every
  query. At production query rates that is the whole difference.

--------------------------------------------------------------------------
6. HIGH DIMENSIONS - random vectors become orthogonal
--------------------------------------------------------------------------
  Mean |cosine| between 2000 random vector pairs:
    dimensions    mean |cos|    
             2        0.6395    ######################################
             8        0.2911    #################
            64        0.0980    #####
           256        0.0497    ##
           768        0.0291    #
          1536        0.0201    #

  In 2 dimensions two random vectors are quite often aligned by
  chance. By 1536 dimensions they are almost exactly orthogonal.

  THIS IS WHY EMBEDDING SEARCH WORKS: against a near-zero
  background, any genuine similarity stands out sharply.

==========================================================================
```

### 7.3 Reading the result

**Section 1 confirms every hand calculation**: `a · b = 10`, `‖a‖ = 5`, `‖b‖ = 2.2361`,
`cos = 0.8944`, angle 26.6°. Doubling `a` doubled the dot product to 20 and the norm to 10 — and left
the cosine at **exactly 0.8944**. That is scale-invariance, measured rather than asserted.

**Section 3 is the one that matters**, because here the two measures actually disagree:

| Document | dot | norm | cosine |
|---|---|---|---|
| doc0 SHORT, highly relevant | 0.7400 | 0.9274 | **0.9606** |
| doc3 LONG, vaguely related | **1.3100** | 2.3108 | 0.6825 |

```
ranking by dot product : ['doc3', 'doc0', 'doc1']    <- wrong
ranking by cosine      : ['doc0', 'doc3', 'doc1']    <- correct
```

The long, vaguely-related document **wins on raw dot product**, purely because its norm is 2.31
against doc0's 0.93. Its cosine is much lower — it genuinely is less relevant — but the dot product
rewards it for size.

Nothing errors. The scores look entirely reasonable. The order is simply wrong. This is exactly what
a user experiences as *"search keeps returning long waffly pages instead of the short page that
answers my question"*, and it is one of the most common misconfigurations in vector search.

**Section 4** confirms the shortcut exactly: full cosine and normalised dot product agree to
floating-point precision (`np.allclose → True`), including doc2's perfect `1.000000`.

**Section 5 puts a number on why that matters:**

```
full cosine (norms computed every query) : 672.66 ms
plain dot on pre-normalised vectors      :  16.55 ms
speed-up                                 :  40.6x
```

**Forty times faster**, for one query against 100,000 documents — from moving the norm computation
from query time to index time. Nothing about the results changed. At production query rates this is
the difference between a search that feels instant and one that does not, and it is a one-line change
made once.

**Section 6 explains why any of this works at all:**

| Dimensions | Mean \|cosine\| between random vectors |
|---|---|
| 2 | **0.6395** |
| 8 | 0.2911 |
| 64 | 0.0980 |
| 768 | 0.0291 |
| 1,536 | **0.0201** |

In two dimensions, two random vectors are aligned by chance about 64% as much as two identical ones.
By 1,536 dimensions that collapses to **2%** — they are almost exactly orthogonal.

**This is the property that makes embedding search possible.** In high-dimensional space, unrelated
things score near zero, so anything genuinely related stands out sharply against an almost-silent
background. If random vectors were as correlated as they are in 2-D, retrieval would be swamped by
coincidence.

It is also the reason a raw score of 0.3 can mean "unrelated" in 1,536 dimensions while meaning
"somewhat similar" in 8 — and therefore why §5.7 says never to copy a threshold between models.

**Verification:** confirm `cos = 0.8944` and the doubled vector giving the same value, that section 3
produces two *different* rankings, that `np.allclose` is `True` in section 4, and that mean |cosine|
falls monotonically with dimension in section 6.

---

## 8. Common mistakes and troubleshooting

1. **Feeding un-normalised vectors to a dot-product index.** Rankings are silently biased toward long
   documents.
2. **Hard-coding a similarity threshold** from a tutorial or another model.
3. **Comparing embeddings from different models.** Meaningless even at matching dimensions.
4. **`np.linalg.norm(M)`** without `axis=1` — gives one number for the whole matrix.
5. **Forgetting `keepdims=True`** when dividing a matrix by its row norms.
6. **Dividing by a zero norm.**
7. **Using Euclidean distance for text embeddings** by default.
8. **Assuming 0.0 is the practical midpoint** of the score range.

| Error / symptom | Cause | Fix |
|---|---|---|
| `ValueError: shapes (4,) and (5,) not aligned` | Different embedding lengths | Same model both sides (M6-L02) |
| `ValueError: operands could not be broadcast (3,4) (3,)` | Norms without `keepdims` | `axis=1, keepdims=True` |
| Long documents always rank first | Un-normalised dot product | Normalise at index time |
| `nan` in the scores | Division by a zero norm | Filter empty/zero vectors |
| Cosine slightly above 1.0 | Floating-point error | `np.clip(x, -1, 1)` before `arccos` |
| Threshold works for one model, not another | Score distributions differ | Calibrate per model (M6-L13) |

---

## 9. Security, privacy, reliability and cost

- **Cost.** Normalising at index time removes two norms and a division per comparison at query time.
  Over a million documents per query, that is the difference between a fast search and an expensive
  one — and it is a one-line change made once.
- **Reliability.** A threshold calibrated on one model silently changes meaning when the model is
  upgraded. **Record the model ID alongside any threshold** (M10-L13), and re-calibrate on change.
- **Privacy.** Cosine similarity between embeddings can reveal that two documents are near-duplicates
  without either being readable — which is useful for deduplication and is also a re-identification
  vector. Access to an embedding index is access to information about the documents (M10-L06).
- **Reliability.** Assert that vectors are non-zero and correctly dimensioned before scoring. A `nan`
  propagating through a ranking produces silently empty results.

---

## 10. Exercises

### Exercise 1 — Beginner (~20 min)

By hand, showing every step. Then verify with NumPy.

```
a = [1, 2, 2]
b = [2, 0, 1]
```

1. `a · b`
2. `‖a‖` and `‖b‖`
3. `cos(a, b)`
4. The Euclidean distance between them.
5. Normalise `a`, then verify its norm is 1.
6. Compute `â · b̂` and confirm it equals your answer to (3).

### Exercise 2 — Intermediate (~30 min)

Using the §6 corpus:

1. Reproduce all three cosine similarities in NumPy and confirm they match the hand calculations to
   4 decimal places.
2. Build a `(3, 4)` matrix and compute all three similarities **in one operation**, without a loop.
3. Add a fourth document that is `doc1 × 5` (shipping times, five times longer). Show that it now
   ranks **first** by dot product and still **last** by cosine.
4. Normalise the corpus at index time and confirm the plain dot product reproduces the cosine scores.
5. Write `rank(query, corpus, k)` returning the top-k `(index, score)` pairs, with a deterministic
   tie-break (M2-L03).

### Exercise 3 — Challenge (~30 min)

1. Generate 10,000 random 768-dimensional vectors with a fixed seed. Compute the mean absolute cosine
   similarity between random pairs at dimensions 2, 8, 64, 256 and 768. Plot or tabulate it and
   explain the trend.
2. Measure the time to score one query against 100,000 normalised vectors using (a) a plain dot
   product and (b) full cosine with norms computed each time. Report both and the ratio.
3. Construct a corpus where the un-normalised dot product ranking is the **exact reverse** of the
   cosine ranking. Explain how you engineered it.
4. Write `safe_cosine(a, b)` handling: zero vectors, mismatched lengths, and results marginally
   outside [−1, 1]. Test all three.
5. Take the M1-L02 spam corpus, build simple word-count vectors for five messages, and compute the
   cosine similarity matrix. Explain one result that surprises you and why raw word counts behave
   differently from learned embeddings.

---

## 11. Quiz

**Q1.** What is `[3, 4] · [2, 1]`?

- A. `[6, 4]`  B. `10`  C. `5`  D. `24`

**Q2.** What is `‖[3, 4]‖`?

- A. `7`  B. `12`  C. `5`  D. `25`

**Q3.** Why is cosine similarity preferred to the raw dot product for text embeddings?

- A. It is faster to compute.
- B. It divides out both vectors' magnitudes, so it measures direction alone — a document is not
  scored higher merely for being longer.
- C. It always returns a positive number.
- D. It works with different embedding dimensions.

**Q4.** `a = [3, 4]` and `c = [6, 8]`. What is `cos(a, c)`?

- A. `0.5`  B. `2.0`  C. `1.0` — same direction, different magnitude  D. `0.0`

**Q5.** If both vectors are already normalised, cosine similarity equals:

- A. The Euclidean distance.  B. The dot product, because the denominator is 1.
- C. Zero.  D. The sum of the elements.

**Q6.** Why does normalising at index time matter at scale?

- A. It saves storage.
- B. Query-time scoring becomes a plain dot product, removing two norm computations and a division
  per document compared.
- C. It improves accuracy.
- D. It is required by NumPy.

**Q7.** You feed un-normalised vectors to a vector database configured for inner-product similarity.
What happens?

- A. An error is raised.
- B. Rankings are silently biased toward documents with larger magnitudes — typically longer ones —
  regardless of relevance.
- C. Scores are clipped to [0, 1].
- D. Nothing; it is equivalent.

**Q8.** Two random 1,536-dimensional vectors will have a cosine similarity close to:

- A. 1.0  B. 0.5  C. 0.0 — high-dimensional random vectors are nearly orthogonal  D. −1.0

**Q9.** Why should you not copy a similarity threshold of 0.8 from a tutorial?

- A. Thresholds must be integers.
- B. Score distributions differ substantially between embedding models, so the same number means
  different things — thresholds must be calibrated on your own data and model.
- C. 0.8 is always too high.
- D. Thresholds are not used in practice.

**Q10.** *(Written, rubric-graded.)* In under 80 words, explain to a colleague why their search
returns long, rambling documents at the top, given that they use a dot-product index.

---

## 12. Revision notes

- **Dot product:** `a · b = Σ aᵢbᵢ`. Multiply matching positions, add. Grows with magnitude.
- **L2 norm:** `‖a‖ = √(Σ aᵢ²)`. Pythagoras in *n* dimensions. `a · a = ‖a‖²`.
- **Cosine similarity:** `(a · b) / (‖a‖‖b‖)`. Range −1 to 1. **Direction only — magnitude divided
  out.**
- `[3,4] · [2,1] = 10` · `‖[3,4]‖ = 5` · `cos ≈ 0.894`. Doubling a vector leaves cosine unchanged.
- **Cosine for text embeddings**; Euclidean when magnitude is meaningful.
- **Normalised vectors ⇒ cosine = dot product.** Normalise once at index time; use a plain dot
  product at query time.
- **Un-normalised vectors in a dot-product index silently rank long documents first.**
- `np.linalg.norm(M, axis=1, keepdims=True)` — one norm per row, shaped for broadcasting.
- **Random high-dimensional vectors are nearly orthogonal** (cosine ≈ 0), which is why embedding
  search works.
- **Never hard-code a threshold.** Distributions differ by model; calibrate, and prefer top-k ranking
  to absolute cut-offs.
- Cosine across **different models** is meaningless.

---

## 13. Completion checklist

- [ ] I computed a dot product, a norm and a cosine by hand.
- [ ] I verified that doubling a vector leaves cosine unchanged.
- [ ] I reproduced all §6 numbers in NumPy.
- [ ] I built the case where an un-normalised dot product inverts the ranking.
- [ ] I verified that normalised dot product equals cosine.
- [ ] I measured the speed difference at scale.
- [ ] I can explain why thresholds must not be copied between models.
- [ ] I scored 7/10 on the quiz.

---

## 14. References

- 3Blue1Brown, "Essence of Linear Algebra" — chapter on dot products.
  <https://www.3blue1brown.com/topics/linear-algebra> `[UNVERIFIED]`
- NumPy, `linalg.norm`.
  <https://numpy.org/doc/stable/reference/generated/numpy.linalg.norm.html> `[UNVERIFIED]`

---

## 15. Next lesson

→ [M3-L03 — Mean, Variance, Standard Deviation and Distributions](M3-L03-statistics.md)

You can now measure similarity between two vectors. Next: describing a *collection* of numbers — which
is how you will read evaluation results, calibrate the thresholds this lesson warned you about, and
tell a real improvement from noise.
