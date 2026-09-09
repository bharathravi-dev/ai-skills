# M3-L05 — Logarithms, Cross-Entropy and Perplexity Intuition

| | |
|---|---|
| **Lesson ID** | M3-L05 |
| **Difficulty** | 2 (Core) |
| **Estimated study time** | 2.0 hours |
| **Prerequisites** | [M3-L04](M3-L04-probability.md) |

---

> **Why this lesson exists.** Cross-entropy is the loss function every language model is trained to
> minimise. Perplexity is how model quality is reported. Log probabilities are why the M1-L02 Naive
> Bayes lab added logs instead of multiplying. All three are the same idea.

---

## 1. Learning objectives

1. **Explain** what a logarithm is and **compute** simple ones by hand.
2. **Explain** why probabilities are handled as logs in every real implementation.
3. **Compute** cross-entropy loss for a small prediction by hand.
4. **Convert** between cross-entropy and perplexity, and **interpret** a perplexity value.
5. **Explain** what "the model was trained to minimise cross-entropy" actually means.

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **Logarithm** | The inverse of exponentiation. `log_b(x)` answers "b to what power gives x?" |
| **Natural log** (`ln`, `log`) | Logarithm base *e* ≈ 2.71828. NumPy's `np.log`. |
| **log₂** | Logarithm base 2. Answers "how many doublings?" Used for bits. |
| **Underflow** | A number too small for floating point, silently becoming 0.0. |
| **Log probability** | `log(p)`. Always ≤ 0, since probabilities are ≤ 1. |
| **Entropy** | The average surprise of a distribution. How uncertain it is. |
| **Cross-entropy** | The average surprise when you predict with distribution *q* but reality follows *p*. |
| **Negative log likelihood (NLL)** | Another name for cross-entropy loss on the true class. |
| **Perplexity** | `exp(cross-entropy)`. Interpretable as an effective number of choices. |
| **Surprisal** | `−log(p)` for a single event. Low probability ⇒ high surprise. |
| **Bit / nat** | Units of information: log₂ gives bits, natural log gives nats. |
| **One-hot** | A vector with 1 at the true class and 0 elsewhere. |

---

## 3. Plain-language explanation

**A logarithm answers "what power?"**

```
log₁₀(1000) = 3      because 10³ = 1000
log₂(8) = 3          because 2³ = 8
log₂(1024) = 10      because 2¹⁰ = 1024
```

Two properties do all the work:

| Property | Meaning |
|---|---|
| `log(a × b) = log(a) + log(b)` | **Multiplication becomes addition** |
| `log(aⁿ) = n × log(a)` | Powers become multiplication |

The first is the reason logs appear everywhere in machine learning.

**Why it matters.** Probabilities are between 0 and 1. Multiplying many of them produces a very small
number:

```
0.1 × 0.1 × 0.1 × ... (400 times) = 10⁻⁴⁰⁰
```

The smallest positive `float64` is about `5 × 10⁻³²⁴`. So that product **becomes exactly 0.0**, and
every distinction between "unlikely" and "impossible" is lost. Worse, `log(0)` is `−inf`, so the
error propagates.

In logs:

```
log(0.1) ≈ −2.303
400 × (−2.303) = −921.0
```

`−921` is a perfectly ordinary float. Nothing is lost.

**This is exactly what the M1-L02 lab did.** It summed `math.log(p)` instead of multiplying `p`, and
now you know why: a 30-word message multiplies 30 probabilities, and longer documents would underflow.

---

## 4. Analogy

**Logarithms measure "how many times bigger", not "how much bigger".**

Earthquake magnitude, decibels and pH are all logarithmic. A magnitude 7 quake is not 7/6 of a
magnitude 6 — it releases about 32 times more energy. Log scales let you write quantities spanning
many orders of magnitude on one axis.

### Where the analogy breaks

1. **Decibels compress a range for human readability. Logs in ML are a numerical necessity** — the
   alternative literally does not fit in a float.
2. **Earthquake magnitudes are positive. Log probabilities are always ≤ 0**, because probabilities are
   ≤ 1. A "score" of −921 is not an error.
3. **The analogy suggests logs are just a display convention.** They change the arithmetic: sums
   replace products, and gradients (M3-L06) become far better behaved.
4. **Decibel scales have a natural zero. Log probability has no floor** — as `p → 0`, `log(p) → −∞`,
   which is why a confidently wrong prediction produces an unbounded loss (§5.5).

---

## 5. Detailed technical explanation

### 5.1 Logs in practice

```python
import numpy as np
np.log(x)     # natural log, base e     - the default in ML
np.log2(x)    # base 2                  - gives bits
np.log10(x)   # base 10
np.exp(x)     # inverse of np.log
```

Values worth knowing by sight:

| x | ln(x) | log₂(x) |
|---|---|---|
| 1.0 | 0 | 0 |
| 0.5 | −0.693 | −1 |
| 0.1 | −2.303 | −3.32 |
| 0.01 | −4.605 | −6.64 |
| 0.001 | −6.908 | −9.97 |

**`ln(1) = 0`** — a probability of 1 costs nothing. **`ln(0.5) = −0.693`** — one bit of surprise, and
you will see 0.693 constantly in binary classification.

**Changing base:** `log_b(x) = ln(x) / ln(b)`. So `log₂(x) = ln(x) / 0.693`.

### 5.2 Surprisal

The **surprisal** of an event with probability *p* is `−log(p)`.

| p | −ln(p) | Interpretation |
|---|---|---|
| 1.0 | 0.00 | Certain — no surprise |
| 0.5 | 0.69 | A coin flip |
| 0.1 | 2.30 | Fairly surprising |
| 0.01 | 4.61 | Very surprising |
| 0.001 | 6.91 | Extremely surprising |

The negative sign makes it positive (since `log(p) ≤ 0` for `p ≤ 1`), so "more surprise" is a larger
number. **Surprisal is the loss for a single prediction.**

### 5.3 Entropy

**Entropy** is the *average* surprisal of a distribution — how uncertain it is overall:

$$H(p) = -\sum_i p_i \log(p_i)$$

Worked on three distributions over four outcomes:

**A fair four-way choice** `[0.25, 0.25, 0.25, 0.25]`:
`H = −4 × (0.25 × ln 0.25) = −4 × (0.25 × −1.386) = **1.386 nats**` = `log(4)`, or exactly **2 bits**.

**A confident distribution** `[0.97, 0.01, 0.01, 0.01]`:
`H = −(0.97 × ln0.97 + 3 × 0.01 × ln0.01) = −(0.97 × −0.0305 + 3 × 0.01 × −4.605)`
`= 0.0296 + 0.138 = **0.168 nats**`

**A certain distribution** `[1, 0, 0, 0]`: `H = **0**`.

**Entropy is maximised by uniformity and zero when certain.** A uniform distribution over *n*
outcomes has entropy `log(n)` — which is the anchor for interpreting perplexity in §5.6.

### 5.4 Cross-entropy — the loss function

Entropy measures one distribution's uncertainty. **Cross-entropy** measures how well a *predicted*
distribution *q* matches the *true* distribution *p*:

$$H(p, q) = -\sum_i p_i \log(q_i)$$

In classification the truth is **one-hot** — a single correct class, so `pᵢ` is 1 for the true class
and 0 for everything else. Every term vanishes except one:

$$\text{loss} = -\log(q_{\text{true}})$$

**Cross-entropy loss is just the negative log probability the model assigned to the correct answer.**
That is the whole thing.

**Worked example.** Four classes: billing, technical, account, sales. The true class is **billing**.

| Model | Predicted distribution | q(billing) | Loss `−ln(q)` |
|---|---|---|---|
| Confident and right | `[0.90, 0.05, 0.03, 0.02]` | 0.90 | **0.105** |
| Uncertain | `[0.40, 0.30, 0.20, 0.10]` | 0.40 | **0.916** |
| Uniform (no information) | `[0.25, 0.25, 0.25, 0.25]` | 0.25 | **1.386** |
| Confident and **wrong** | `[0.02, 0.90, 0.05, 0.03]` | 0.02 | **3.912** |

**Note the asymmetry.** Being confidently wrong costs 3.912; being confidently right saves only
0.105 relative to uniform's 1.386. **Cross-entropy punishes confident errors far more than it rewards
confident successes**, and that asymmetry is deliberate — it is what discourages a model from
asserting things it cannot support.

**The pathological case:** if the model assigns `q = 0` to the true class, the loss is `−ln(0) = ∞`.
Implementations clip probabilities away from 0 (e.g. to `1e-15`) to avoid this, which is the same
motivation as the Laplace smoothing in M1-L02.

### 5.5 What "trained to minimise cross-entropy" means

For a language model, the "classes" are the entire vocabulary — perhaps 100,000 tokens — and the task
at every position is: given the preceding text, which token comes next (M1-L07)?

1. The model outputs a probability distribution over all 100,000 tokens.
2. The actual next token in the training text is the "true class".
3. The loss is `−log(probability assigned to that actual token)`.
4. Training adjusts the weights to make that number smaller, averaged over trillions of positions.

**That is the entire training objective.** Not "be helpful", not "be true" — *assign high probability
to the token that actually came next*. Everything you know about hallucination (M1-L10 §5.2) follows
from that sentence being the literal objective.

### 5.6 Perplexity

Cross-entropy in nats is hard to interpret. **Perplexity** exponentiates it:

$$\text{perplexity} = e^{H(p,q)}$$

| Cross-entropy | Perplexity | Interpretation |
|---|---|---|
| 0.0 | 1.0 | Perfectly certain and correct |
| 0.693 | 2.0 | Effectively choosing between 2 options |
| 1.386 | 4.0 | Effectively choosing between 4 |
| 2.303 | 10.0 | Effectively choosing between 10 |
| 4.605 | 100.0 | Effectively choosing between 100 |

**Perplexity is the effective number of equally-likely choices the model is deciding between.** A
perplexity of 20 means the model is about as uncertain as if it were picking uniformly among 20
tokens.

Because a uniform distribution over *n* outcomes has entropy `log(n)`, its perplexity is exactly *n* —
which is what makes the interpretation exact rather than metaphorical.

**Interpreting values:**

| Perplexity | Meaning |
|---|---|
| ≈ vocabulary size | The model has learned nothing |
| 100+ | Weak |
| 10–50 | Reasonable for a small model |
| < 10 | Strong on that data |
| 1.0 | Memorised (or the data is trivial) |

**Three important cautions:**

1. **Perplexity is only comparable across models using the same tokenizer and the same evaluation
   data.** A model with a larger vocabulary is not automatically worse because its perplexity is
   higher.
2. **Low perplexity on the training data means memorisation**, not quality (M1-L08).
3. **Perplexity measures prediction of the *next token*, not usefulness.** A model can have excellent
   perplexity and be unhelpful, and this is exactly why instruction tuning and preference
   optimisation exist (M4-L12, M4-L13). It is a training diagnostic, not a product metric.

### 5.7 Assumptions and limitations

- Cross-entropy assumes the predicted values form a genuine probability distribution — non-negative
  and summing to 1. That is what the softmax function guarantees (M3-L09).
- Perplexity comparisons require identical tokenization and identical evaluation text.
- Minimising cross-entropy optimises calibration *on the training distribution*; it does not
  guarantee calibration on your data (M1-L10).
- Log-space arithmetic prevents underflow but introduces its own care: summing probabilities in log
  space requires `logsumexp`, not a naive `log(sum(exp(...)))`, which can overflow.

---

## 6. Worked example — evaluating a classifier with cross-entropy

Five support tickets. Four classes. The model's predicted probability for the **true** class:

| Ticket | True class | q(true) | Loss `−ln(q)` |
|---|---|---|---|
| 1 | billing | 0.85 | −ln(0.85) = **0.163** |
| 2 | technical | 0.60 | −ln(0.60) = **0.511** |
| 3 | billing | 0.95 | −ln(0.95) = **0.051** |
| 4 | sales | 0.10 | −ln(0.10) = **2.303** |
| 5 | account | 0.70 | −ln(0.70) = **0.357** |

**Step 1 — average cross-entropy.**

`(0.163 + 0.511 + 0.051 + 2.303 + 0.357) / 5 = 3.385 / 5 = **0.677 nats**`

**Step 2 — perplexity.** `e^0.677 = **1.97**`

The model is about as uncertain as choosing between 2 equally likely options — from 4 classes. It has
learned something substantial (a random model would score 4.0), but it is not confident.

**Step 3 — find where the loss lives.** Ticket 4 alone contributes 2.303 of the 3.385 total, which is
**68% of the entire loss from 20% of the data**.

**This is the most useful property of cross-entropy for debugging.** Accuracy would report this model
as "4 of 5 correct if we threshold at the argmax" and tell you nothing more. Cross-entropy points
straight at ticket 4 and says *this one is where your model is failing badly*.

**Step 4 — compare with accuracy.** Suppose all five were classified correctly by `argmax`. Accuracy
is **100%**. Cross-entropy is 0.677, and ticket 4 was correct with only 10% confidence — the model
scraped through. Accuracy cannot see that; cross-entropy can.

**Step 5 — the practical workflow.** Rank your evaluation examples by per-example loss and read the
worst ten. They are, reliably, either genuinely hard cases, mislabelled data (M1-L04 §5.4), or a
systematic gap in your prompt. This single technique finds more real problems than any aggregate
metric, and you will use it in M5-L18 and M7-L19.

---

## 7. Practical activity

**File:** [`labs/m3/l05_entropy.py`](../../labs/m3/l05_entropy.py)

**Requires the venv:**

```bash
source .venv/bin/activate
python labs/m3/l05_entropy.py
```

Demonstrates underflow with real floats, verifies the log-sum identity, computes entropy for several
distributions, reproduces the §6 table, shows the confident-wrong asymmetry, converts to perplexity,
and shows a language model's loss falling during simulated training.

### 7.1 Important lines

| Construct | Why |
|---|---|
| `np.prod(probs)` vs `np.log(probs).sum()` | Underflow, demonstrated with real floats. |
| `-np.sum(p * np.log(p))` | Entropy, directly from the formula. |
| `-np.log(q[true_index])` | Cross-entropy loss for a one-hot target. |
| `np.exp(mean_loss)` | Perplexity. |
| `np.clip(q, 1e-15, 1)` | Prevents `−log(0) = inf`. |

### 7.2 Expected output

`[EXECUTED]` 2026-09-08 with numpy 2.5.3, Python 3.12.3:

```
==========================================================================
LOGARITHMS, CROSS-ENTROPY AND PERPLEXITY
==========================================================================

--------------------------------------------------------------------------
1. UNDERFLOW - why nobody multiplies probabilities
--------------------------------------------------------------------------
  Multiplying 0.1 by itself, n times:
       n                   product     sum of logs
      10                 1.000e-10           -23.0
      50                 1.000e-50          -115.1
     100                1.000e-100          -230.3
     200                1.000e-200          -460.5
     300                1.000e-300          -690.8
     323                9.881e-324          -743.7
     324                 0.000e+00          -746.0   <-- UNDERFLOWED TO ZERO
     400                 0.000e+00          -921.0   <-- UNDERFLOWED TO ZERO

  Smallest positive float64: 4.941e-324

  Past ~324 multiplications the product is EXACTLY 0.0. Every
  distinction between 'unlikely' and 'impossible' is gone, and
  log(0) is -inf, so the damage propagates.

  The log column never leaves a comfortable numeric range. This
  is precisely why the M1-L02 Naive Bayes lab summed logs.

  The identity that makes it work:
    log(0.2 x 0.3)    = log(0.06) = -2.813411
    log(0.2) + log(0.3) = -1.609438 + -1.203973 = -2.813411
    identical? True

--------------------------------------------------------------------------
2. SURPRISAL AND ENTROPY
--------------------------------------------------------------------------
  Surprisal of a single event, -ln(p):
         p      -ln(p)    -log2(p)   interpretation
       1.0       0.000       0.000   certain, no surprise
       0.5       0.693       1.000   a coin flip
      0.25       1.386       2.000   one of four
       0.1       2.303       3.322   fairly surprising
      0.01       4.605       6.644   very surprising
     0.001       6.908       9.966   extremely surprising

  Entropy = average surprisal of a whole distribution:
  shape               distribution                      nats    bits
  uniform over 4      [0.25, 0.25, 0.25, 0.25]        1.3863  2.0000
  somewhat confident  [0.7, 0.1, 0.1, 0.1]            0.9404  1.3568
  very confident      [0.97, 0.01, 0.01, 0.01]        0.1677  0.2419
  certain             [1.0, 0.0, 0.0, 0.0]            0.0000  0.0000

  Uniform over 4 gives exactly ln(4) = 1.3863 nats = 2 bits.
  Entropy is maximised by uniformity and zero when certain.

--------------------------------------------------------------------------
3. CROSS-ENTROPY - the loss is just -log(q_true)
--------------------------------------------------------------------------
  True class: billing

  model                   predicted distribution          q(true)     loss
  confident and RIGHT     [0.9, 0.05, 0.03, 0.02]            0.90    0.105
  uncertain               [0.4, 0.3, 0.2, 0.1]               0.40    0.916
  uniform (no info)       [0.25, 0.25, 0.25, 0.25]           0.25    1.386
  confident and WRONG     [0.02, 0.9, 0.05, 0.03]            0.02    3.912

  THE ASYMMETRY:
    uniform baseline           : 1.386
    confident and right SAVES  : 1.281
    confident and wrong COSTS  : 2.526
    ratio                      : 2.0x

  Being confidently wrong is punished about 2x as hard as being
  confidently right is rewarded. That asymmetry is deliberate: it
  discourages asserting things the model cannot support.

  And the pathological case:
    q(true)=0.1      loss=2.303      clipped loss=2.303
    q(true)=0.01     loss=4.605      clipped loss=4.605
    q(true)=0.001    loss=6.908      clipped loss=6.908
    q(true)=1e-10    loss=23.026     clipped loss=23.026
    q(true)=0.0      loss=inf        clipped loss=34.539
    Implementations clip away from zero, for the same reason
    M1-L02 used Laplace smoothing.

--------------------------------------------------------------------------
4. THE SECTION 6 EVALUATION, VERIFIED
--------------------------------------------------------------------------
  ticket      true class      q(true)     loss  % of total
  ticket 1    billing            0.85    0.163        4.8%
  ticket 2    technical          0.60    0.511       15.1%
  ticket 3    billing            0.95    0.051        1.5%
  ticket 4    sales              0.10    2.303       68.0%
  ticket 5    account            0.70    0.357       10.5%
                                total    3.384

  mean cross-entropy = 3.384 / 5 = 0.677 nats
  perplexity         = exp(0.677) = 1.97

  With 4 classes, a model that had learned NOTHING would score
  perplexity 4.00. This model is at 1.97 - it has learned
  a lot, but it is far from confident.

  WHERE THE LOSS LIVES: ticket 4 contributes 68% of the total loss
  from 20% of the data.

  Accuracy cannot see this. If all five were correct by argmax,
  accuracy is 100% and tells you nothing. Cross-entropy points
  straight at ticket 4.

  Sensitivity check - fix ticket 4 from 0.10 to 0.50:
    mean loss  0.677 -> 0.355
    perplexity 1.97 -> 1.43
    One example out of five moved the metric substantially.

--------------------------------------------------------------------------
5. PERPLEXITY - the effective number of choices
--------------------------------------------------------------------------
    cross-entropy (nats)    perplexity   meaning
                   0.000          1.00   perfectly certain and correct
                   0.693          2.00   choosing between 2
                   1.386          4.00   choosing between 4
                   2.303         10.00   choosing between 10
                   3.912         50.00   choosing between 50
                   4.605        100.00   choosing between 100

  A uniform distribution over n outcomes has entropy ln(n), so its
  perplexity is exactly n. That is what makes the interpretation
  exact rather than a metaphor.

  Verifying it:
    uniform over   2: entropy 0.6931, perplexity 2.00
    uniform over   4: entropy 1.3863, perplexity 4.00
    uniform over  10: entropy 2.3026, perplexity 10.00
    uniform over  50: entropy 3.9120, perplexity 50.00
    uniform over 100: entropy 4.6052, perplexity 100.00

--------------------------------------------------------------------------
6. WHAT 'TRAINED TO MINIMISE CROSS-ENTROPY' LOOKS LIKE
--------------------------------------------------------------------------
  Simulated language-model training. Vocabulary 50,000 tokens.

        step   loss (nats)    perplexity   what it means
           0        10.820        50,000   uniform guess - knows nothing
         100         7.200         1,339   learning token frequencies
       1,000         5.400           221   learning common patterns
      10,000         4.100            60   learning grammar and context
     100,000         3.200            25   learning grammar and context
   1,000,000         2.600            13   strong next-token prediction

  Step 0 loss = ln(50,000) = 10.820, perplexity 50,000 - exactly the
  vocabulary size, because a uniform guess over the vocabulary is
  what 'knows nothing' means.

  IMPORTANT: this whole curve measures only NEXT-TOKEN PREDICTION.
  Not truth. Not helpfulness. A model at perplexity 13 predicts
  text well and may still be unhelpful, which is exactly why
  instruction tuning and preference optimisation exist (M4-L12,
  M4-L13). Perplexity is a training diagnostic, not a product
  metric.

==========================================================================
```

### 7.3 Reading the result

**Section 1 shows underflow happening at a precise point:**

```
n=323   product 9.881e-324   sum of logs -743.7
n=324   product 0.000e+00    sum of logs -746.0   <-- UNDERFLOWED TO ZERO
```

At 323 multiplications the product is still representable. At **324 it is exactly zero**. Not
"very small" — zero, indistinguishable from an impossible event, and `log(0)` is `−inf`, so the
damage spreads to everything downstream.

Meanwhile the log column reads −743.7 and −746.0: entirely ordinary numbers. A 400-word document has
400 word probabilities to combine, so this is not a theoretical concern — it is why the M1-L02 lab
summed `math.log(p)` rather than multiplying.

**Section 3 quantifies the asymmetry**, which is worth internalising because it explains model
behaviour you will observe later:

| | Loss | vs uniform |
|---|---|---|
| Uniform baseline (no information) | 1.386 | — |
| Confident and **right** (q=0.90) | 0.105 | **saves 1.281** |
| Confident and **wrong** (q=0.02) | 3.912 | **costs 2.526** |

**Being confidently wrong is punished exactly twice as hard as being confidently right is rewarded.**
A model trained on this objective learns that unsupported confidence is expensive — which is a
deliberate design property, not an accident.

And the pathological row: `q(true) = 0.0` gives `loss = inf`. Clipping to `1e-15` gives 34.539 —
a huge but finite penalty. Same motivation as Laplace smoothing in M1-L02.

**Section 4 reproduces §6 exactly**: mean cross-entropy **0.677 nats**, perplexity **1.97**, and
ticket 4 contributing **68% of the total loss from 20% of the data**.

That last figure is the practical payoff. Accuracy would report this model as perfect if all five
predictions won their `argmax`, and would tell you nothing else. Cross-entropy points at ticket 4 and
says *look here*. Sorting an evaluation set by per-example loss and reading the worst ten is the
single most productive debugging habit in this module.

The sensitivity check underneath makes the point again: fixing that one example moved the mean loss
from 0.677 to 0.355 and perplexity from 1.97 to 1.43 — **one example in five, roughly halving the
metric**.

**Section 5 verifies the perplexity interpretation is exact, not a metaphor:**

```
uniform over   4: entropy 1.3863, perplexity   4.00
uniform over 100: entropy 4.6052, perplexity 100.00
```

A uniform distribution over *n* outcomes has perplexity **exactly** *n*. So "perplexity 20" really
does mean "as uncertain as picking uniformly among 20 options".

**Section 6 puts the training objective on one screen:**

```
step 0        loss 10.820   perplexity 50,000   uniform guess - knows nothing
step 1,000    loss  5.400   perplexity    221   learning common patterns
step 1,000,000 loss 2.600   perplexity     13   strong next-token prediction
```

Step 0's loss is `ln(50,000) = 10.820`, and its perplexity is **exactly the vocabulary size** —
because "knows nothing" means "guesses uniformly over the vocabulary". That is a satisfying anchor:
the loss curve starts at a value you can derive from first principles.

**And the caution the lab ends on matters more than the curve.** Every number there measures
next-token prediction. Not truth, not helpfulness. A model at perplexity 13 predicts text very well
and may still refuse to follow instructions or assert confident falsehoods — which is precisely why
M4-L12 and M4-L13 exist, and why perplexity is a training diagnostic rather than a product metric.

**Verification:** confirm underflow at n=324, the asymmetry ratio of 2.0×, mean loss 0.677 with
perplexity 1.97, ticket 4 at 68%, and that uniform over *n* gives perplexity exactly *n*.

---

## 8. Common mistakes and troubleshooting

1. **Multiplying probabilities instead of summing logs.** Underflow to 0.0.
2. **Taking `log(0)`.** Clip first.
3. **Comparing perplexity across different tokenizers or datasets.** Meaningless.
4. **Treating low training perplexity as quality.** It is memorisation (M1-L08).
5. **Confusing nats and bits.** `ln` gives nats; `log₂` gives bits. A factor of 0.693.
6. **Using perplexity as a product metric.** It measures next-token prediction, not usefulness.
7. **Forgetting the predicted values must sum to 1.**

| Error / symptom | Cause | Fix |
|---|---|---|
| Loss is `inf` or `nan` | `log(0)`, or probabilities not normalised | `np.clip(q, 1e-15, 1)`; check the sum |
| Product of probabilities is exactly 0.0 | Underflow | Work in log space |
| Perplexity ≈ vocabulary size | The model has learned nothing | Check training actually ran |
| Perplexity 1.0 on training data | Memorisation | Evaluate on held-out data |
| Loss values differ from another framework | nats vs bits | Divide by `ln(2)` to convert |
| Accuracy high, loss high | Correct but unconfident predictions | Inspect the highest-loss examples |

---

## 9. Security, privacy, reliability and cost

- **Reliability.** Per-example loss is the best triage tool you have. Sorting an evaluation set by
  loss and reading the worst cases finds mislabelled data and systematic gaps faster than any
  aggregate.
- **Privacy.** A model's loss on a specific example is a **membership-inference signal** — unusually
  low loss suggests the example was in the training data. Exposing per-example log probabilities from
  a model trained on private data leaks information about that data (M10-L06, M13-L02).
- **Cost.** Perplexity is the standard metric for whether more training is paying off. A flat
  validation perplexity means further training is spending money for nothing (M13-L04).
- **Governance.** When reporting perplexity, record the tokenizer, the evaluation dataset and its
  version. Without those the number cannot be compared to anything (M10-L13).

---

## 10. Exercises

### Exercise 1 — Beginner (~20 min)

Compute by hand, then verify:

1. `log₂(16)`, `log₂(0.25)`, `ln(1)`, `ln(e)`.
2. The surprisal `−ln(p)` for p = 1.0, 0.5, 0.25, 0.1, 0.01.
3. `log(0.2 × 0.3)` two ways: multiply then log, and log then add. Confirm they agree.
4. Multiply 0.1 by itself 400 times in Python. What do you get, and why?
5. The same in log space. What do you get?

### Exercise 2 — Intermediate (~30 min)

1. Compute the entropy of `[0.25,0.25,0.25,0.25]`, `[0.7,0.1,0.1,0.1]`, `[0.97,0.01,0.01,0.01]` and
   `[1,0,0,0]`. Handle the `0 × log(0)` case and explain your choice.
2. Reproduce the §6 table and confirm the mean loss of 0.677 and perplexity of 1.97.
3. Compute what fraction of the total loss each ticket contributes. Confirm ticket 4 is ~68%.
4. Change ticket 4's `q(true)` from 0.10 to 0.50. Report the new mean loss and perplexity, and say
   what that tells you about the metric's sensitivity.
5. Build a model that is correct on all five by `argmax` but has high loss. Explain why accuracy and
   cross-entropy disagree.

### Exercise 3 — Challenge (~30 min)

1. Write `cross_entropy(true_indices, predicted_probs)` handling: unnormalised rows, zero
   probabilities, and mismatched shapes. Test all three.
2. For a 4-class problem, plot loss against `q(true)` from 0.01 to 1.0. Mark uniform (0.25) on it and
   describe the curve's shape near zero.
3. Take 200 simulated predictions, compute per-example loss, and print the 10 worst. Explain what you
   would do with that list in a real project.
4. Convert a cross-entropy of 2.5 nats to bits and to perplexity. Show both calculations.
5. A model reports perplexity 12 on its training set and 95 on held-out data. Diagnose it, referring
   to M1-L08, and say what you would do next.
6. Explain in three sentences why a model can have excellent perplexity and still be useless as a
   product, naming the module that addresses the gap.

---

## 11. Quiz

**Q1.** What is `log₂(8)`?

- A. 2  B. 3  C. 4  D. 8

**Q2.** Why are probabilities handled as logarithms in real implementations?

- A. Logs are faster to compute.
- B. Multiplying many probabilities underflows to exactly 0.0 in floating point, whereas adding their
  logs stays in a safe numeric range.
- C. Logs are more accurate.
- D. It is a convention with no practical effect.

**Q3.** What is cross-entropy loss when the true label is one-hot?

- A. The sum of all predicted probabilities.
- B. The negative log of the probability the model assigned to the correct class.
- C. The difference between predicted and true probabilities.
- D. The entropy of the prediction.

**Q4.** The true class is billing. The model predicts `[0.02, 0.90, 0.05, 0.03]`. What is the loss?

- A. 0.105  B. 0.916  C. 3.912  D. 0.02

**Q5.** Why does cross-entropy punish confident errors so heavily?

- A. It is a design flaw.
- B. `−log(p)` grows without bound as `p → 0`, so assigning near-zero probability to something that
  actually happened produces a very large loss — which discourages unsupported confidence.
- C. It does not; it treats all errors equally.
- D. Because probabilities are squared.

**Q6.** A model has cross-entropy 1.386 nats. What is its perplexity, and what does that mean?

- A. 1.386; it is 138% confident.
- B. 4.0; it is about as uncertain as choosing uniformly among 4 options.
- C. 0.25; it is 25% accurate.
- D. 2.0; it is choosing between 2 options.

**Q7.** When can two perplexity values be compared?

- A. Always.
- B. Only when the models use the same tokenizer and are evaluated on the same data.
- C. Only for models of the same size.
- D. Never.

**Q8.** What is a language model's training objective, stated precisely?

- A. To be helpful and accurate.
- B. To maximise the probability assigned to the token that actually came next in the training text —
  equivalently, to minimise the negative log of that probability.
- C. To minimise the number of errors.
- D. To match human preferences.

**Q9.** Your model has 100% accuracy but high cross-entropy. What does that indicate?

- A. A bug in the loss calculation.
- B. It is getting the right answers but with low confidence — the correct class wins the `argmax`
  narrowly, which accuracy cannot see but cross-entropy can.
- C. The labels are wrong.
- D. Cross-entropy is the wrong metric here.

**Q10.** *(Written, rubric-graded.)* In under 80 words, explain to a colleague why a model with
excellent perplexity might still be useless in your product.

---

## 12. Revision notes

- **`log(a×b) = log(a) + log(b)`.** This one identity is why logs are everywhere.
- **Multiplying many probabilities underflows to 0.0.** `0.1⁴⁰⁰` is exactly zero in float64. Work in
  log space — which is what the M1-L02 lab did.
- Log probabilities are **always ≤ 0**. `ln(1)=0`, `ln(0.5)=−0.693`, `ln(0.1)=−2.303`.
- **Surprisal** = `−log(p)`. **Entropy** = average surprisal = `−Σ pᵢ log(pᵢ)`; maximised by uniform
  (`log n`), zero when certain.
- **Cross-entropy with a one-hot target = `−log(q_true)`.** That is the whole loss function.
- **Confident errors are punished far more than confident successes are rewarded** — `−log(p) → ∞` as
  `p → 0`. Clip to avoid `inf`.
- **Perplexity = `e^(cross-entropy)`** = the effective number of equally-likely choices. Uniform over
  *n* gives exactly *n*.
- Perplexity is comparable **only** across the same tokenizer and the same data. Low *training*
  perplexity is memorisation.
- **A language model's objective is literally "predict the next token"** — not truth, not
  helpfulness (M1-L10, M4-L12).
- **Sort your evaluation set by per-example loss and read the worst ten.** Best debugging tool in
  this module.

---

## 13. Completion checklist

- [ ] I can compute simple logs by hand.
- [ ] I demonstrated underflow and the log-space fix myself.
- [ ] I computed entropy for uniform, confident and certain distributions.
- [ ] I reproduced the §6 table, mean loss 0.677 and perplexity 1.97.
- [ ] I can explain the confident-wrong asymmetry.
- [ ] I can convert between cross-entropy and perplexity in both directions.
- [ ] I can state a language model's training objective in one sentence.
- [ ] I scored 7/10 on the quiz.

---

## 14. References

- Goodfellow, Bengio & Courville, *Deep Learning*, Ch. 3 (information theory).
  <https://www.deeplearningbook.org/> `[UNVERIFIED]`
- Shannon, "A Mathematical Theory of Communication" (1948) — the origin of entropy.
  `[UNVERIFIED]`

---

## 15. Next lesson

→ [M3-L06 — Derivatives, Gradients and the Chain Rule](M3-L06-derivatives-gradients.md)

You now know what a model is trying to minimise. Next: how it knows which direction to move — the
calculus behind every training step, built from arithmetic you already have.
