# M4-L04 — Embeddings and Contextual Representations

| | |
|---|---|
| **Lesson ID** | M4-L04 |
| **Difficulty** | 2 (Intermediate) |
| **Estimated study time** | 2 hours |
| **Prerequisites** | [M4-L03](M4-L03-tokens-tokenizers.md), [M3-L02](../module-03-math-ml-essentials/M3-L02-dot-product-cosine.md) |

---

## 1. Learning objectives

1. **Explain** how a token ID becomes a vector, and what that vector means.
2. **Distinguish** static from contextual embeddings, and say why the distinction matters.
3. **Compute** the size of an embedding matrix and its share of a model's parameters.
4. **Explain** how pooling produces a sentence embedding, and the trade-offs between methods.
5. **State** what embeddings do and do not capture — the basis for everything in Modules 6 and 7.

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **Embedding** | A dense vector representing a token, sentence or document. |
| **Embedding matrix** | The lookup table: one row per vocabulary entry. |
| **Static embedding** | One fixed vector per word, regardless of context (word2vec, GloVe). |
| **Contextual embedding** | A vector that depends on the surrounding tokens. |
| **Polysemy** | One word form with several meanings. |
| **Dimension** (`d_model`) | The length of each embedding vector. |
| **Pooling** | Combining many token vectors into one. |
| **Mean pooling / CLS pooling** | Two common pooling strategies. |
| **Tied embeddings** | Reusing the input embedding matrix as the output layer. |
| **Anisotropy** | The tendency of embeddings to occupy a narrow cone, inflating similarities. |
| **Embedding model** | A model whose *purpose* is producing sentence embeddings (M6). |

---

## 3. Plain-language explanation

### 3.1 From integer to vector

M4-L03 left you with token IDs — integers like `[496, 675, 15717]`. An integer carries no useful
structure: token 675 is not "more" than token 674, and their numeric closeness means nothing.

So the first thing a model does is **look each ID up in a table**:

```
token ID 675  →  row 675 of the embedding matrix  →  [0.021, -0.114, 0.303, ..., 0.087]
                                                      (a vector of d_model numbers)
```

That is all an embedding lookup is: **indexing a row**. No computation, just a table read.

**The table is learned.** Its values start random and are adjusted by gradient descent (M3-L11) like
any other parameter. Nothing tells the model that `cat` and `dog` should be near each other; it
discovers that because they appear in similar contexts and that similarity helps it predict.

### 3.2 The problem with one vector per word

If `bank` has exactly one row in the table, then:

```
"I sat on the river bank"      → bank = [0.3, -0.1, 0.8, ...]
"I deposited it at the bank"   → bank = [0.3, -0.1, 0.8, ...]   ← identical
```

**Same vector, completely different meanings.** A static embedding must average all senses of a word
into one point — which lands it somewhere between the senses, representing neither.

This was the state of the art for years (word2vec, GloVe) and it worked surprisingly well. But it puts
a hard ceiling on understanding, and lifting that ceiling is exactly what transformers did.

### 3.3 Contextual embeddings

In a transformer, the table lookup is only the **starting point**. Each layer updates every token's
vector using the other tokens around it (M4-L07). By the output layers:

```
"river bank"    → bank = [0.9, 0.2, -0.4, ...]   ← near "shore", "water"
"savings bank"  → bank = [-0.2, 0.7, 0.5, ...]   ← near "money", "account"
```

**Same token ID, same starting row, different final vectors** — because the context differed.

> **The one-sentence summary:** the embedding table gives every token a *starting guess* at its
> meaning; the transformer's layers refine that guess using context. Everything in M4-L07 through
> M4-L10 is machinery for doing the refining.

---

## 4. Analogy

**An embedding is a location on a map where distance means similarity.** Nearby points are related;
far-apart points are not. A static embedding gives every word one permanent address. A contextual
embedding lets a word move depending on who it is standing with.

### Where the analogy breaks

1. **Maps have two dimensions; embeddings have hundreds to thousands.** Almost all high-dimensional
   intuition from 2-D is wrong — most notably, **random points in high dimensions are nearly all
   equidistant and nearly orthogonal** (M3-L02 §7.3).
2. **Map distance is one thing. Embedding "distance" depends on the metric** — cosine and Euclidean
   can rank differently.
3. **Map coordinates mean something individually** (latitude, longitude). **Individual embedding
   dimensions usually mean nothing.** Only relationships between vectors are interpretable.
4. **Maps are shared. Every model has its own incompatible space** — you cannot compare a vector from
   one model with a vector from another, ever. This causes real production incidents (M6-L11).

---

## 5. Detailed technical explanation

### 5.1 The embedding matrix, and how big it is

```
E : (vocab_size, d_model)
```

| Vocab | `d_model` | Parameters | float32 |
|---|---|---|---|
| 32,000 | 4,096 | 131.1M | 524 MB |
| 100,000 | 4,096 | 409.6M | 1.6 GB |
| 128,000 | 8,192 | 1.05B | 4.2 GB |

**On a small model this is a large fraction of all parameters.** A 7B model with a 128k vocabulary
and `d_model` 4,096 spends about **524M parameters — 7.5% of the total — on the input embedding
alone**, before any layer does any work. §7.3 computes this for several configurations.

**Tied embeddings** reuse `E` transposed as the output projection, halving that cost. Common in
smaller models; less so at frontier scale.

### 5.2 The lookup is not a matrix multiply

Conceptually, a one-hot vector times `E`:

```
one_hot(675) @ E    # (1, 100000) @ (100000, 4096) -> (1, 4096)
```

**In practice nobody does this** — it is 409 million multiplications, almost all by zero, to fetch one
row. Every real implementation does `E[675]`, an array index. The one-hot framing is a useful mental
model for the *backward* pass (only that row receives a gradient), and a terrible implementation.

### 5.3 What the learned space contains

Trained embeddings show real structure:

- **Similar words cluster.** `cat`, `dog`, `hamster` land near each other.
- **Some relationships are directions.** The famous `king − man + woman ≈ queen`. **Treat this with
  care** — it works for a curated handful of analogies and fails on most, and the demonstrations are
  usually cherry-picked. `[UNVERIFIED — the effect is real but far weaker than popular accounts
  suggest]`
- **Frequency structures the space.** Rare tokens often sit further from the centroid.
- **Individual dimensions are not interpretable.** Dimension 1,847 does not mean "animalness".

**A limitation that causes real problems: embeddings capture *association*, not *truth* or
*negation*.** `"the payment succeeded"` and `"the payment did not succeed"` are highly similar in
embedding space, because they share almost every word. **A retrieval system built on cosine similarity
will happily return the opposite of what was asked** (M7-L09). This is not a tuning problem; it is a
property of the representation.

### 5.4 Contextual embeddings, layer by layer

| Layer | What the vector encodes |
|---|---|
| Input (table lookup) | The token identity alone |
| Early layers | Local syntax, morphology, neighbouring words |
| Middle layers | Phrase and clause meaning, resolved references |
| Late layers | Task-relevant, prediction-oriented meaning |

**A practical consequence.** When extracting embeddings for retrieval, the **last** layer is often
*not* the best choice — it has specialised toward next-token prediction. Second-to-last, or an
average of several, frequently works better. `[UNVERIFIED — model-dependent; test on your data]`

### 5.5 From token vectors to one sentence vector

A sentence gives you `n` vectors and you usually want one. The options:

| Method | How | Notes |
|---|---|---|
| **Mean pooling** | Average all token vectors | Simple, strong, the common default |
| **CLS pooling** | Take a designated special token's vector | Requires the model to have been trained for it |
| **Max pooling** | Element-wise maximum | Rare; loses a great deal |
| **Weighted mean** | Weight by attention or by IDF | Often better; more work |
| **Last token** | Take the final token's vector | Used by decoder-only embedding models |

**Mean pooling must exclude padding tokens** — but *when* this bites is more subtle than it is usually
stated, and §7.3 measures both cases:

| Configuration | Effect of forgetting the mask |
|---|---|
| **Zero** pad vector, **equal** lengths | **None at all** — error exactly 0.0000 |
| **Learned** (non-zero) pad vector, equal lengths | Small: 0.0373 |
| Learned pad vector, **unequal** lengths (4 vs 56) | **Large: 0.8219** |
| Learned pad vector, **unrelated** texts, equal short lengths | **Catastrophic: −0.05 → 0.97** |

Averaging in *zeros* rescales a vector without changing its direction, and cosine similarity is
scale-invariant (M3-L02) — so with zero padding the bug is genuinely harmless. **But a real padding
token is a learned row of the embedding matrix, and after any transformer layer it is emphatically not
zero.** Then both vectors acquire a large shared component — the pad embedding — and **unrelated texts
are pushed together**, producing silent false positives in retrieval.

**Note which configuration is harmless: zero padding with equal lengths — exactly what a unit test
usually uses.** Mask the padding.

**Note that a general language model is not automatically a good embedding model.** Dedicated
embedding models are trained with a *contrastive* objective — explicitly pulling related texts
together and pushing unrelated ones apart. M6-L02 covers this properly, and it is why you should use
an embedding model for retrieval rather than pooling a chat model's hidden states.

### 5.6 Anisotropy — why raw cosine scores mislead

Embeddings from language models tend to occupy a **narrow cone** rather than spreading over the
sphere. Consequence: **random unrelated sentences can score 0.7–0.9 cosine similarity.**

§7.3 measures it on 4,000 vectors in 256 dimensions:

| Vector set | Mean similarity of *unrelated* pairs | % scoring above 0.8 |
|---|---|---|
| Isotropic (textbook assumption) | 0.0002 | 0.0% |
| **Anisotropic (realistic)** | **0.7787** | **13.4%** |
| Anisotropic, after centring | 0.0004 | 0.0% |

If you have ever set a similarity threshold of 0.8 because it "sounded high", this is why it did not
work. **What matters is the *relative* ranking and the distribution on your own data, not the absolute
number.** Always plot the distribution of similarities for known-unrelated pairs before choosing a
threshold (M3-L02 §5.6, M6-L08).

### 5.7 Assumptions and limitations

- Embedding spaces are **model-specific and incomparable**. Changing embedding model means re-encoding
  everything.
- Dimensions are not individually interpretable; do not build features from them.
- Embeddings encode training-data associations, including social biases (M10-L09).
- Similarity is not truth: negation, contradiction and numeric differences are poorly captured.

---

## 6. Worked example — why one vector per word is not enough

A tiny 4-dimensional space, hand-built so the arithmetic is checkable. Four dimensions with
deliberately assigned meanings — *real* embeddings have no such interpretable axes, but a toy needs
them to be legible.

Axes: `[water, money, structure, movement]`

| Token | Vector |
|---|---|
| `river` | `[0.9, 0.0, 0.1, 0.4]` |
| `money` | `[0.0, 0.9, 0.1, 0.1]` |
| `shore` | `[0.8, 0.0, 0.3, 0.0]` |
| `account` | `[0.0, 0.8, 0.3, 0.0]` |
| `bank` (static) | `[0.45, 0.45, 0.5, 0.1]` |

**The static `bank` is the average of both senses** — halfway between water and money, close to
neither.

**Cosine similarities** (M3-L02):

```
cos(bank_static, shore)   = 0.7320
cos(bank_static, account) = 0.7320
```

**Identical.** The static embedding cannot tell you which sense is meant, because it has thrown that
information away. Any downstream system relying on it inherits the ambiguity.

**Now make it contextual.** A crude rule — nudge `bank` toward the average of its neighbours:

```
context_vector = mean(neighbouring token vectors)
bank_ctx = 0.5 × bank_static + 0.5 × context_vector
```

**In "river bank":** neighbour is `river = [0.9, 0.0, 0.1, 0.4]`

```
bank_ctx = 0.5 × [0.45, 0.45, 0.5, 0.1] + 0.5 × [0.9, 0.0, 0.1, 0.4]
         = [0.675, 0.225, 0.30, 0.25]
```

**In "money bank":** neighbour is `money = [0.0, 0.9, 0.1, 0.1]`

```
bank_ctx = [0.225, 0.675, 0.30, 0.10]
```

**Recomputed similarities:**

| | `shore` | `account` |
|---|---|---|
| `bank` in "river bank" | **0.9085** | 0.3894 |
| `bank` in "money bank" | 0.4059 | **0.9470** |

**Same token, same starting row, opposite results.** The ambiguity is resolved, and nothing changed
except the neighbours.

**What this toy gets wrong**, and it is worth being precise about:

1. **Real attention is learned**, not a fixed 50/50 average — it decides *which* neighbours matter and
   by how much (M4-L07).
2. **Real models stack dozens of these updates**, each refining the last.
3. **Real dimensions carry no assigned meaning.** These four axes exist so you can follow the
   arithmetic; a real model's dimension 1,847 means nothing on its own.
4. **A fixed average would destroy information in longer sentences** — averaging in twenty irrelevant
   neighbours would wash out the signal. Attention solves exactly that, which is why it exists.

**But the core claim is exact and survives all four caveats:** contextual embeddings work by mixing
neighbouring vectors into each token's representation.

---

## 7. Practical activity

**File:** [`labs/m4/l04_embeddings.py`](../../labs/m4/l04_embeddings.py)

**No API key, no network, no downloads.** NumPy only.

```bash
source .venv/bin/activate
python labs/m4/l04_embeddings.py
```

Reproduces §6 exactly, trains a small embedding table so you can watch structure emerge from random
initialisation, sizes real embedding matrices, compares pooling strategies including the padding bug,
and demonstrates anisotropy inflating similarity scores.

### 7.2 Expected output

`[EXECUTED]` on Python 3.12.3, NumPy 2.5.3, 2026-09-08.

```text

============================================================================
1. THE WORKED EXAMPLE  (4 toy dimensions: water, money, structure, movement)
============================================================================
  token        water   money  struct    move
  river         0.90    0.00    0.10    0.40
  money         0.00    0.90    0.10    0.10
  shore         0.80    0.00    0.30    0.00
  account       0.00    0.80    0.30    0.00
  bank          0.45    0.45    0.50    0.10   <- the static average of both senses

  STATIC embedding:
    cos(bank, shore)   = 0.7320
    cos(bank, account) = 0.7320
    difference         = 0.0000  <- IDENTICAL
    One vector cannot say which sense is meant. The information was
    averaged away before the question was asked.

  CONTEXTUAL, mixing 50% of the neighbour's vector:
  phrase          bank vector                         cos(shore)  cos(account)
  river bank      [0.675 0.225 0.3   0.25 ]               0.9085        0.3894
  money bank      [0.225 0.675 0.3   0.1  ]               0.4059        0.9470

  Same token, same starting row, opposite results. Nothing changed
  except the neighbours.

  How the mixing weight controls disambiguation:
    weight   river: cos(shore)   money: cos(account)   separation
      0.00              0.7320                0.7320       0.0000
      0.10              0.7827                0.7870       0.1055
      0.20              0.8273                0.8378       0.2135
      0.35              0.8785                0.9019       0.3727
      0.50              0.9085                0.9470       0.5191
      0.70              0.9176                0.9754       0.6821
      0.90              0.9009                0.9730       0.8041
      1.00              0.8867                0.9635       0.8513

  'separation' is how much better the RIGHT sense scores than the
  wrong one. At weight 0 there is none. It grows with the weight --
  but at weight 1.0 the token's own identity is gone entirely, which
  is why real attention LEARNS the weight instead of fixing it.

============================================================================
2. WATCHING STRUCTURE EMERGE FROM RANDOM INITIALISATION
============================================================================
  corpus     : 720 sentences, 25 distinct words
  d_model    : 12
  'cat'/'dog' appear in the same contexts and never together;
  'invoice'/'receipt' likewise. Nothing tells the model they are alike.

      step   cos(cat,dog)   cos(inv,rec)   cos(cat,inv)
    random        -0.1381        -0.2017         0.3169
       200         0.0354        -0.0567         0.0183
       600         0.7881         0.8465        -0.0940
      1500         0.9898         0.9796        -0.1482
      3000         0.9973         0.9961        -0.0940

  Words used in the same contexts converged toward each other; words
  from different contexts did not. Nothing supervised this -- the
  structure fell out of predicting neighbours (M1-L07 self-supervision).

  nearest neighbours in the learned space:
    cat        -> dog (0.997), today (0.470), mat (0.370)
    invoice    -> receipt (0.996), please (0.593), amount (0.472)
    mat        -> sat (0.765), shows (0.440), amount (0.420)

============================================================================
3. HOW BIG IS THE EMBEDDING MATRIX?
============================================================================
       vocab   d_model        params       fp32      fp16   % of a 7B model
      32,000     4,096   131,072,000      0.49G     0.24G             1.9%
     100,000     4,096   409,600,000      1.53G     0.76G             5.9%
     128,000     4,096   524,288,000      1.95G     0.98G             7.5%
     128,000     8,192 1,048,576,000      3.91G     1.95G            15.0%
     256,000     8,192 2,097,152,000      7.81G     3.91G            30.0%

  A 128k vocabulary at d_model 4,096 is 524M parameters -- 7.5% of a
  7B model spent on a lookup table, before any layer does any work.
  Tied embeddings (reusing E as the output projection) halve this.

  and the lookup itself:
    one_hot(675) @ E  == E[675] ? True
    multiplications in the matmul : 25,600,000
    multiplications in the index  : 0
    Same answer. Nobody does it the first way.

============================================================================
4. POOLING, AND THE PADDING BUG  (which is subtler than it looks)
============================================================================
  FIRST, the case people usually imagine: a ZERO padding vector,
  both sentences the same real length.

    real  padded   pad %   cos WITH mask   cos WITHOUT    error
       8       8     0%          0.9707        0.9707   0.0000
       8      32    75%          0.9613        0.9613   0.0000
       4      64    94%          0.9239        0.9239   0.0000
       2      64    97%          0.8220        0.8220   0.0000

  ERROR IS EXACTLY ZERO -- and that is a real result, not a broken
  demo. Averaging in zeros divides the vector by a larger number but
  does not change its DIRECTION, and cosine similarity is scale-
  invariant (M3-L02). With a zero pad vector and cosine, the bug is
  genuinely harmless.

  NOW the realistic case: a LEARNED (non-zero) padding embedding,
  and sentences of DIFFERENT real lengths padded to the same width.

   len A len B  padded   cos WITH mask   cos WITHOUT    error
       8     8      64          0.9617        0.9990   0.0373
       8    40      64          0.9722        0.5667   0.4055
       4    56      64          0.9595        0.1376   0.8219
       2    60      64          0.9298        0.0448   0.8851
      30    34      64          0.9912        0.9864   0.0047

  Same topic every row. Unmasked, the short sentence is dragged far
  toward the pad embedding and the long one barely at all, so their
  similarity is distorted. Note the LAST row: when both lengths are
  similar, the error nearly vanishes -- both drift the same way.

  And the case that actually costs you money -- UNRELATED sentences
  of very different lengths, which SHOULD score near zero:

   len A len B  padded   cos WITH mask   cos WITHOUT  inflation
       8     8      64         -0.0531        0.9721    +1.0251
       4    56      64         -0.0966        0.1665    +0.2631
       2    60      64         -0.0886        0.0942    +0.1829
       2    62      64         -0.0619        0.0624    +0.1242

  UNRELATED sentences are pushed UP toward each other, because both
  now contain a large shared component: the padding embedding. That is
  the failure -- false positives in retrieval, arriving silently.

  THE RULE: mask padding. The bug is invisible with zero padding and
  equal lengths, which is exactly the configuration people test with.

  pooling strategies compared on the same sentence:
    mean           same topic  0.9770   other topic -0.0848   separation  1.0618
    max            same topic  0.7152   other topic -0.0353   separation  0.7506
    last token     same topic  0.8691   other topic -0.0985   separation  0.9676
    first token    same topic  0.8759   other topic -0.1542   separation  1.0302

  Mean pooling separates the topics best here because it averages away
  per-token noise. Single-token strategies inherit that token's noise --
  which is why they need a model TRAINED to put the meaning there.

============================================================================
5. ANISOTROPY: WHY A 0.8 THRESHOLD MEANS NOTHING
============================================================================
  cosine similarity of RANDOM UNRELATED pairs, 256 dimensions:

  vector set                       mean       sd        p5       p95  % above 0.8
  isotropic (textbook)           0.0002   0.0639   -0.1037    0.1054         0.0%
  anisotropic (realistic)        0.7787   0.0193    0.7454    0.8090        13.4%

  In the anisotropic set, UNRELATED pairs average 0.78 similarity and
  13% of them exceed 0.8. A threshold of 0.8 copied from a
  tutorial would admit essentially the entire corpus as a 'match'.

  shared-component norm 30 vs noise norm ~16:
  the shared direction dominates, so every vector points roughly the
  same way and cosine similarity measures almost nothing.

  The fix -- centre the vectors (subtract the mean), then re-measure:
  vector set                       mean       sd        p5       p95  % above 0.8
  anisotropic, centred           0.0004   0.0625   -0.1001    0.1053         0.0%

  Centring removes the shared component and restores a usable spread.
  But note what it did NOT do: it changed the NUMBERS, not the ranking
  of any pair. If you only need top-k, rank and ignore the absolute
  scores. If you need a threshold, measure YOUR distribution first.

Done.
```

### 7.3 Reading the result

**Section 1 confirms §6.** Static `bank` scores **0.7320** against both `shore` and `account` — the
difference is **exactly 0.0000**. The information needed to disambiguate was averaged away before the
question was asked, so no downstream cleverness can recover it.

Contextualising resolves it completely: in "river bank" the vector scores **0.9085** to `shore` and
0.3894 to `account`; in "money bank", 0.4059 and **0.9470**.

The mixing-weight sweep adds something the lesson's fixed 50/50 could not show. Separation between the
right and wrong sense grows steadily with the weight — 0.0000 at weight 0, 0.5191 at 0.5, **0.8513 at
1.0** — but at weight 1.0 the token's own identity is gone entirely: `bank` has become its neighbour.
**That is the tension attention resolves**, by learning how much of each neighbour to mix rather than
fixing it in advance (M4-L07).

**Section 2 shows the structure emerging, which is the part worth watching.** A 12-dimensional table
starts random and is trained only to predict neighbouring words:

| Step | cos(cat, dog) | cos(invoice, receipt) | cos(cat, invoice) |
|---|---|---|---|
| random | −0.1381 | −0.2017 | 0.3169 |
| 200 | 0.0354 | −0.0567 | 0.0183 |
| 600 | 0.7881 | 0.8465 | −0.0940 |
| **3,000** | **0.9973** | **0.9961** | **−0.0940** |

`cat` and `dog` **never once appear together** in the corpus. Nothing tells the model they are
related. They converge to 0.9973 similarity purely because they occur in the same contexts — and
`cat` and `invoice`, which occur in different contexts, stay apart. **This is M1-L07's self-supervision
producing semantic structure from nothing but next-word prediction**, and it is the mechanism behind
every embedding you will ever use.

The nearest-neighbour listing confirms it: `cat → dog (0.997)`, `invoice → receipt (0.996)`.

**Section 3 sizes the tables**, and the last two rows are the ones to notice: a 128k vocabulary at
`d_model` 8,192 is **1.05B parameters — 15% of a 7B model** — and a 256k vocabulary at the same width
is **30%**. On smaller models, a large vocabulary is a major architectural cost, not a detail.

It also confirms `one_hot(675) @ E == E[675]`: identical results, **25.6 million multiplications
versus zero**.

**Section 4 corrected this lesson.** The first version of the lab measured the padding bug with a
*zero* pad vector and equal lengths, and found **error exactly 0.0000** — no bug at all. That is not a
broken demo; averaging in zeros rescales a vector without rotating it, and cosine is scale-invariant.

With a **learned** (non-zero) pad embedding the picture changes completely:

| Case | Masked | Unmasked | Error |
|---|---|---|---|
| Same topic, lengths 30 and 34 | 0.9912 | 0.9864 | 0.0047 |
| Same topic, lengths 4 and 56 | 0.9595 | 0.1376 | **0.8219** |
| **Unrelated topics, both length 8, padded to 64** | **−0.0531** | **0.9721** | **+1.0251** |

**Two unrelated sentences score 0.97 similarity when the padding is not masked.** In a retrieval
system that is a false positive on essentially every query, and nothing raises an error.

The important part is *which* configuration was harmless: zero padding with equal lengths — **exactly
what a unit test tends to use**. This is a bug that passes its own test and fails in production.

**Section 5 reproduces anisotropy, and the effect is large.** Unrelated pairs in the anisotropic set
average **0.7787** similarity, with **13.4% scoring above 0.8**. A 0.8 threshold copied from a tutorial
would admit most of the corpus as a match. Centring drops the mean to **0.0004** and the above-0.8 rate
to zero.

But note the closing caution, which is the practically important half: **centring changed the numbers,
not the ranking of any pair.** If you need top-k, rank and ignore the absolute scores entirely. If you
genuinely need a threshold, measure the distribution on *your* data first. An absolute cosine score has
no meaning that transfers between models or corpora.

---

## 8. Common mistakes and troubleshooting

1. **Comparing vectors from different models.** Never valid. Re-encode everything on a model change.
2. **Including padding in mean pooling.** Silent quality loss.
3. **Interpreting individual dimensions.**
4. **Setting a similarity threshold from a tutorial.** Measure your own distribution.
5. **Assuming similar means true.** Negation is barely represented.
6. **Using a chat model's hidden states for retrieval** instead of an embedding model.
7. **Forgetting embeddings are a large share of a small model's parameters.**
8. **Assuming the last layer is best** for extracted representations.

| Symptom | Likely cause | Fix |
|---|---|---|
| Everything scores 0.8+ similar | Anisotropy | Rank rather than threshold; measure the distribution |
| Retrieval returns the opposite meaning | Negation is not captured | Rerank; add lexical matching (M7-L09) |
| Quality dropped after adding batching | Padding included in pooling | Mask padding before averaging |
| Search broke after a model upgrade | Old and new vectors are incomparable | Re-encode the whole index |
| Similarities all near zero | Vectors not normalised, or wrong metric | Check the metric; normalise |
| Embedding memory larger than expected | `vocab × d_model` is substantial | Compute it; consider tied embeddings |
| Analogy arithmetic fails | It only works on curated cases | Do not build on it |

---

## 9. Security, privacy, reliability, cost

- **Privacy.** **Embeddings are not anonymised text.** Inversion attacks can reconstruct a
  recognisable amount of the original from its vector. Treat an embedding store with the same
  controls as the source text — access control, retention, deletion. This surprises people, and it is
  the single most important line in this section. (M10-L11.)
- **Privacy.** Deleting a document must also delete its embeddings. A vector database is a copy of
  your data, and a deletion request that misses it is a compliance failure.
- **Reliability.** Pin the embedding model version. An upgrade silently invalidates every stored
  vector, and the symptom is degraded relevance, not an error.
- **Cost.** Storage is `n_vectors × d_model × bytes`. 10M documents at 1,536 dimensions in float32 is
  **61 GB** before indexes. Quantisation and dimension reduction are the levers (M6-L12).
- **Bias.** Embeddings encode the associations in their training data, including harmful ones.
  Measuring this is a prerequisite for governance work, and measuring it is not the same as fixing it
  (M10-L09).

---

## 10. Exercises

### Exercise 1 — Beginner (~20 min)

1. In one sentence, what does an embedding lookup actually do?
2. Why can a static embedding not distinguish the two senses of `bank`?
3. A model has a 50,000 vocabulary and `d_model` 2,048. How many embedding parameters? How many MB in
   float32?
4. Why are two vectors from different embedding models incomparable?
5. Give two things embeddings capture well and two they capture badly.

### Exercise 2 — Intermediate (~35 min)

1. Run the lab and reproduce §6's similarity table by hand for one row.
2. Change the contextual mixing weight from 0.5 to 0.2 and to 0.8. Report how disambiguation changes
   and explain the trade-off.
3. Implement mean pooling with and without a padding mask. Measure the similarity error introduced by
   omitting the mask, as a function of the padding fraction.
4. Compute the embedding-parameter share for three model configurations and comment on which is most
   affected.
5. Generate 1,000 random vectors, then 1,000 from an anisotropic cone. Plot both similarity
   distributions and state what threshold each would need.

### Exercise 3 — Challenge (~45 min)

1. Train a small embedding table by next-token prediction on a synthetic corpus where two words are
   deliberately interchangeable. Show they converge to similar vectors, and report how many steps it
   takes.
2. Implement CLS, mean, max and last-token pooling. Rank them on a synthetic retrieval task and state
   whether the ranking is stable across seeds.
3. Demonstrate the negation problem: construct sentence pairs differing only by "not" and measure
   their similarity. Propose and test one mitigation.
4. Implement centring and whitening of an embedding set, and measure the effect on the similarity
   distribution and on retrieval ranking. State whether ranking actually improved or only the numbers
   moved.
5. Measure storage for 1M, 10M and 100M vectors at 384, 768 and 1,536 dimensions in float32, float16
   and int8. Produce the table you would take to a budget discussion.

---

## 11. Quiz

*(Answers: [`answer-keys/module-04-answers.md`](../../answer-keys/module-04-answers.md#m4-l04).)*

**Q1.** What does an embedding lookup do computationally?

- A. Retrieves one row of a learned matrix by index.
- B. Multiplies the token ID by a learned scaling factor.
- C. Runs the token through a small feed-forward network.
- D. Computes a hash of the token string into a vector.

**Q2.** Why can a static embedding not disambiguate `bank`?

- A. Static embeddings have too few dimensions to store both senses.
- B. The tokenizer splits the word differently in each context.
- C. It has one fixed vector per word, averaging all senses together.
- D. Static embeddings are trained on smaller corpora than contextual ones.

**Q3.** In a transformer, what makes an embedding contextual?

- A. Each layer updates every token's vector using the other tokens.
- B. The tokenizer emits different IDs depending on the sentence.
- C. A separate lookup table is used for each possible word sense.
- D. Positional encodings assign a distinct vector to every position.

**Q4.** Vocabulary 100,000, `d_model` 4,096. Embedding parameters?

- A. 4,096  B. 409.6M  C. 100,000  D. 24.4M

**Q5.** Which statement about individual embedding dimensions is correct?

- A. Each dimension corresponds to one interpretable semantic feature.
- B. Dimensions are ordered by importance, most significant first.
- C. The first dimension encodes frequency and the rest encode meaning.
- D. Individual dimensions generally mean nothing in isolation.

**Q6.** You mean-pool token vectors without masking padding. What happens?

- A. An exception is raised because shapes do not align.
- B. Only the last vector in each batch is affected.
- C. Nothing; padding vectors are always zero by construction.
- D. Every vector is dragged toward the padding embedding, silently.

**Q7.** Unrelated sentences score 0.85 cosine similarity. Why?

- A. The embedding model has been trained incorrectly.
- B. Cosine similarity is the wrong metric for text.
- C. Anisotropy — embeddings occupy a narrow cone, inflating scores.
- D. The vectors have not been normalised to unit length.

**Q8.** You upgrade your embedding model. What must you do?

- A. Nothing, provided the vector dimension is unchanged.
- B. Rescale the stored vectors by the ratio of the two dimensions.
- C. Re-encode every stored vector, as the spaces are incomparable.
- D. Re-encode only documents added since the previous upgrade.

**Q9.** Why is "the payment succeeded" similar to "the payment did not succeed"?

- A. The model has not been trained on enough negation examples.
- B. Cosine similarity ignores word order entirely by definition.
- C. Embeddings capture association; negation is barely represented.
- D. The word "not" is a stop word and is removed before encoding.

**Q10.** What is the privacy status of a stored embedding?

- A. Anonymous, since the original text cannot be recovered from it.
- B. Anonymous, provided the vector has more than 256 dimensions.
- C. Pseudonymous, and therefore outside most data-protection regimes.
- D. Sensitive — inversion attacks can reconstruct much of the source.

**Q11.** *(Written, rubric-graded.)* In under 100 words, explain to a colleague why the search results
got worse after the team "upgraded to a better embedding model", and what should have happened.

---

## 12. Revision notes

- **An embedding lookup is a table read.** `E[token_id]` — one row of a learned `(vocab, d_model)`
  matrix. No computation.
- **The one-hot matrix multiply is a mental model, not an implementation.**
- **Static embedding = one vector per word**, averaging every sense. **Contextual = the vector depends
  on neighbours**, which is what transformer layers produce.
- **Embedding matrices are big**: 100k × 4,096 = **409.6M parameters, 1.6 GB in float32** — a
  substantial share of a small model.
- **Individual dimensions mean nothing.** Only relationships between vectors are meaningful.
- **Mean pooling must mask padding** — but note *when* it bites. Measured: with a **zero** pad vector
  and equal lengths the error is **exactly 0.0000** (cosine is scale-invariant); with a **learned** pad
  vector, two **unrelated** sentences went from −0.05 to **0.97**. The harmless configuration is the
  one unit tests use.
- **Anisotropy inflates cosine scores.** Measured: unrelated pairs averaged **0.7787**, with **13.4%**
  above 0.8; centring dropped the mean to 0.0004 **without changing any ranking**. **Rank, do not
  threshold**, until you have measured your own distribution.
- **Similarity is not truth.** Negation and contradiction are barely represented, so retrieval can
  return the opposite of what was asked.
- **Spaces from different models are incomparable.** Upgrading means re-encoding everything.
- **Embeddings are not anonymised text.** Inversion attacks work. Protect and delete them like the
  source.

---

## 13. Completion checklist

- [ ] I can explain the lookup in one sentence without saying "matrix multiplication".
- [ ] I reproduced §6's similarity table.
- [ ] I can compute an embedding matrix's parameter count and size.
- [ ] I know why padding must be masked — and the configuration in which it makes no difference.
- [ ] I can explain anisotropy and why a 0.8 threshold is meaningless without measurement.
- [ ] I know that embeddings must be re-encoded when the model changes.
- [ ] I know embeddings are not anonymous.
- [ ] I scored 8/11 on the quiz.

---

## 14. References

- Mikolov et al. (2013), *Efficient Estimation of Word Representations* (word2vec).
  <https://arxiv.org/abs/1301.3781> `[UNVERIFIED]`
- Peters et al. (2018), *Deep Contextualized Word Representations* (ELMo).
  <https://arxiv.org/abs/1802.05365> `[UNVERIFIED]`
- Ethayarajh (2019), *How Contextual are Contextualized Word Representations?* (anisotropy).
  <https://arxiv.org/abs/1909.00512> `[UNVERIFIED]`
- Morris et al. (2023), *Text Embeddings Reveal (Almost) As Much As Text* (inversion).
  <https://arxiv.org/abs/2310.06816> `[UNVERIFIED]`

---

## 15. Next lesson

→ [M4-L05 — Language Modelling: Next-Token Prediction End to End](M4-L05-next-token-prediction.md)

You can turn tokens into vectors and know why context changes them. Next: the complete path from a
prompt to a predicted token, with every step's shape written down.
