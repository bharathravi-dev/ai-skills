# M4-L14 — Autoregressive Decoding: Temperature, Top-p, Top-k and Sampling

| | |
|---|---|
| **Lesson ID** | M4-L14 |
| **Difficulty** | 2 (Intermediate) |
| **Estimated study time** | 2 hours |
| **Prerequisites** | [M4-L05](M4-L05-next-token-prediction.md), [M3-L09](../module-03-math-ml-essentials/M3-L09-logistic-regression.md) |

---

> **Everything before this lesson was about how the model was built.**
> This lesson is about the handful of numbers *you* set on every request — the only part of the whole
> pipeline you control from a config file. They are also the settings most often copied from a tutorial
> and never examined.

---

## 1. Learning objectives

1. **Explain** what temperature does to a probability distribution, mechanically.
2. **Compare** greedy, top-k, top-p and min-p on what each removes and why.
3. **Choose** decoding settings from a task's requirements, and defend the choice.
4. **Explain** why temperature 0 does not guarantee identical output.
5. **Diagnose** repetition, incoherence and truncation from the settings that cause them.

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **Decoding** | Turning the model's probability distribution into actual tokens. |
| **Greedy decoding** | Always taking the highest-probability token. |
| **Temperature** | A divisor on logits before softmax. Reshapes the distribution. |
| **Top-k** | Keep only the `k` highest-probability tokens, then sample. |
| **Top-p (nucleus)** | Keep the smallest set whose probability sums to `p`. |
| **Min-p** | Keep tokens above a fraction of the top token's probability. |
| **Repetition penalty** | Reducing the probability of already-generated tokens. |
| **Beam search** | Keeping several candidate sequences and expanding the best. |
| **Logit bias** | A manual per-token adjustment to the logits. |
| **Seed** | A value initialising the sampler's randomness. |

---

## 3. Plain-language explanation

### 3.1 Where decoding sits

M4-L05 ended with a probability distribution over the vocabulary at the final position. **Decoding is
what you do with it.**

```
logits (vocab_size,)
   │
   ▼  ÷ temperature          ← reshapes the distribution
   │
   ▼  softmax
   │
   ▼  truncate: top-k / top-p / min-p    ← removes the tail
   │
   ▼  renormalise
   │
   ▼  sample                 ← one token
```

**Two separate operations, and conflating them causes most confusion:**

- **Temperature reshapes** the whole distribution — every token's probability changes.
- **Top-k / top-p truncate** it — some tokens are removed entirely, and the rest are renormalised.

You can use either alone or both together, and the order matters.

### 3.2 The core trade-off

**Every decoding setting trades repetition against incoherence.** There is no setting that avoids
both, and where you sit is a product decision:

```
   greedy ──────────────────────────────────► pure sampling
   deterministic                              maximally varied
   repetitive                                 incoherent
```

M4-L01 §7.3 measured the left end: greedy decoding produced
`'the are are are are are are are...'` — identical on every run, and looping forever. M3-L09 §5.6
measured the right end: at high temperature the output approaches uniform noise.

**Neither end is usable. Everything practical is a point in between**, chosen for the task.

---

## 4. Analogy

**A dial between a metronome and a jazz improviser.** Fully left: perfectly predictable, and it will
play the same bar forever. Fully right: never repeats, and stops making musical sense.

### Where the analogy breaks

1. **A musician knows when to be predictable.** The dial is fixed for a whole generation — the model
   cannot be conservative on a number and creative on a phrase within one response.
2. **Improvisation follows structure. Sampling follows probability**, with no notion of appropriateness.
3. **A metronome never drifts. Greedy decoding loops** — the most probable continuation of a repeated
   pattern is that pattern again, which is a failure mode a metronome does not have.
4. **You can ask a musician to try again differently.** The same seed and settings reproduce the same
   output exactly — which is a feature, not a limitation.

---

## 5. Detailed technical explanation

### 5.1 Temperature

$$p_i = \\frac{\\exp(z_i / T)}{\\sum_j \\exp(z_j / T)}$$

**Identical to the softmax temperature in M3-L09 §5.6.** Same formula, same effect.

| `T` | Effect |
|---|---|
| → 0 | Approaches greedy — the top token takes all the mass |
| 0.0–0.3 | Very focused; near-deterministic |
| 0.7–1.0 | Balanced; the usual default range |
| 1.0 | The model's own distribution, unmodified |
| > 1.5 | Flattened; low-probability tokens become plausible |
| → ∞ | Uniform over the vocabulary |

**Temperature does not add information.** It reshapes what is already there. A model that assigns the
correct answer 0.02 probability will not find it at `T = 2`; it will simply produce a *different*
wrong answer more often.

### 5.2 Top-k

Keep the `k` most probable tokens, zero the rest, renormalise.

**The weakness is that `k` is fixed while the distribution is not.** After `"The capital of France
is"` the distribution is sharply peaked and `k = 50` admits 49 irrelevant tokens. After `"She opened
the door and saw a"` thousands of continuations are reasonable and `k = 50` is too restrictive.

**One number cannot suit both**, which is exactly what top-p fixes.

### 5.3 Top-p (nucleus sampling)

Sort descending, take the smallest set whose cumulative probability reaches `p`, renormalise.

**The set size adapts to the distribution.** §7.3 measures this directly: on a peaked distribution
`top_p = 0.9` might keep 2 tokens; on a flat one, several hundred.

**This is why top-p is the usual default.** `p = 0.9` to `0.95` is the common range.

### 5.4 Min-p

Keep tokens whose probability is at least `min_p × p_max`.

```python
threshold = min_p * probs.max()
keep = probs >= threshold
```

**Directly relative to the model's own confidence.** When the model is certain, only near-equal
candidates survive; when uncertain, many do. Newer, well regarded, and increasingly available.
`[UNVERIFIED — support varies by provider]`

### 5.5 Choosing settings

| Task | Temperature | Top-p | Why |
|---|---|---|---|
| **Structured extraction / JSON** | **0.0** | — | You want the most probable valid output, every time |
| Classification | 0.0 | — | Same |
| Factual question answering | 0.0–0.3 | 0.9 | Minimise invention |
| **RAG answers** | **0.0–0.3** | 0.9 | The answer is in the context; do not improvise |
| Summarisation | 0.3–0.5 | 0.9 | Slight variation, high fidelity |
| Conversation | 0.7–0.9 | 0.95 | Natural, varied |
| Brainstorming | 0.9–1.2 | 0.95 | Variety is the goal |
| Creative writing | 1.0–1.3 | 0.95 | Variety is the goal |

**The most common production mistake is leaving temperature at a chat default for a structured task.**
If you need parseable JSON, there is no argument for randomness — you want the most probable valid
output, not a sample from a distribution over outputs.

### 5.6 Repetition penalties

| Mechanism | How |
|---|---|
| **Repetition penalty** | Divide the logits of already-seen tokens by a factor (~1.1) |
| **Frequency penalty** | Subtract proportionally to how often a token appeared |
| **Presence penalty** | Subtract a flat amount if a token appeared at all |
| **No-repeat n-gram** | Forbid any n-gram that has already occurred |

**Use these carefully.** They apply to *all* tokens, including ones that legitimately recur — a
technical document naming the same product forty times will be penalised for doing so. Prefer fixing
the prompt or the sampling settings first.

### 5.7 Why temperature 0 is not deterministic

**A genuinely surprising and frequently-hit fact.** Even at `T = 0`, repeated identical requests can
return different output. Causes:

| Cause | Explanation |
|---|---|
| **Floating-point non-associativity** | `(a+b)+c ≠ a+(b+c)` in floating point. GPU reduction order varies with batch composition |
| **Batching** | Your request is batched with others; the batch changes the arithmetic |
| **Mixture-of-experts routing** | Routing can depend on the batch |
| **Hardware and version differences** | Different accelerators, different kernels |
| **Ties** | Two tokens with equal top probability |

**The practical consequence: do not build anything that requires bit-identical model output.** Cache
by input, validate output, and test for behaviour rather than exact strings. A test asserting an exact
generated string will be flaky, and the flakiness is not a bug in your code.

### 5.8 Beam search

Keep `b` candidate sequences, expand each, retain the best `b` by total log-probability.

**Standard in translation, and largely abandoned for open-ended generation** — it produces bland,
high-probability text, because the highest-probability *sequence* is usually not the most interesting
one. It also costs `b×` the compute.

### 5.9 Assumptions and limitations

- Parameter names, ranges and availability differ by provider. Verify against current documentation.
- Some providers apply top-p before temperature, or expose only a subset of these controls.
- Recommended ranges are conventions, not derivations. Test on your task.

---

## 6. Worked example — one distribution, five decoding strategies

**Prompt:** `"The weather today is"`. The model produces these logits over a 8-token vocabulary:

| Token | Logit |
|---|---|
| sunny | 3.2 |
| cloudy | 2.8 |
| rainy | 2.1 |
| cold | 1.5 |
| warm | 1.2 |
| terrible | 0.3 |
| purple | −1.8 |
| Tuesday | −2.4 |

### 6.1 Softmax at `T = 1.0`

`exp(3.2) = 24.53`, `exp(2.8) = 16.44`, `exp(2.1) = 8.17`, `exp(1.5) = 4.48`, `exp(1.2) = 3.32`,
`exp(0.3) = 1.35`, `exp(−1.8) = 0.165`, `exp(−2.4) = 0.091`. Sum = **58.55**.

| Token | `T = 1.0` |
|---|---|
| sunny | 0.4190 |
| cloudy | 0.2809 |
| rainy | 0.1395 |
| cold | 0.0765 |
| warm | 0.0567 |
| terrible | 0.0231 |
| purple | 0.0028 |
| Tuesday | 0.0015 |

### 6.2 The same logits at three temperatures

| Token | `T = 0.5` | `T = 1.0` | `T = 2.0` |
|---|---|---|---|
| sunny | **0.6192** | 0.4190 | **0.2802** |
| cloudy | 0.2782 | 0.2809 | 0.2294 |
| rainy | 0.0686 | 0.1395 | 0.1617 |
| cold | 0.0207 | 0.0765 | 0.1198 |
| warm | 0.0113 | 0.0567 | 0.1031 |
| terrible | 0.0019 | 0.0231 | 0.0657 |
| purple | **0.0000** | 0.0028 | **0.0230** |
| Tuesday | 0.0000 | 0.0015 | 0.0170 |

*(All values verified in §7.3. An earlier draft of this table had the `T = 0.5` and `T = 2.0` columns
wrong — the lab's assertion caught it, which is the same argument M4-L08 §7.3 makes.)*

**Read the `purple` row.** At `T = 0.5` it is effectively impossible — about **1 in 35,571** tokens. At
`T = 2.0` it has a **2.30%** chance, or **1 in 43**. `"The weather today is purple"` is now a realistic
output.

**Temperature did not make the model creative. It made a nonsense token reachable.** That distinction
matters: high temperature does not unlock better answers, it lowers the bar for worse ones.

### 6.3 Top-k = 3

Keep `sunny`, `cloudy`, `rainy`; discard the rest; renormalise by their sum `0.4190 + 0.2808 + 0.1395
= 0.8393`:

| Token | Renormalised |
|---|---|
| sunny | 0.4992 |
| cloudy | 0.3346 |
| rainy | 0.1662 |

`purple` is now **impossible regardless of temperature** — truncation happens after temperature and
removes tokens outright.

### 6.4 Top-p = 0.9

Cumulative from the top: `0.4190`, `0.6999`, `0.8393`, `0.9159` ← reaches 0.9 at the **fourth** token.

**Keeps 4 tokens** (`sunny`, `cloudy`, `rainy`, `cold`).

**Now the point of top-p.** Suppose a different, much flatter distribution — say all eight tokens near
0.125. Cumulative: `0.125, 0.25, 0.375, 0.5, 0.625, 0.75, 0.875, 1.0` — reaching 0.9 requires **8
tokens**.

**Same setting, 4 tokens in one case and 8 in the other.** Top-k = 3 would have kept exactly 3 in both,
which is too many for the peaked case and far too few for the flat one. **The adaptation is the whole
value.**

### 6.5 Min-p = 0.1

Threshold = `0.1 × 0.4190 = 0.0419`. Keep tokens at or above it: `sunny` (0.4190), `cloudy` (0.2808),
`rainy` (0.1395), `cold` (0.0765), `warm` (0.0567). **5 tokens.**

**Relative to the model's own confidence.** If the top token had 0.95 probability, the threshold would
be 0.095 and almost nothing else would survive — which is the desired behaviour when the model is sure.

### 6.6 Choosing, for this prompt

| Setting | Kept | Sensible for |
|---|---|---|
| Greedy | 1 (`sunny`) | Extraction, classification — and it will loop on repetitive text |
| `T=0.5`, top-p 0.9 | 3 | A factual weather report |
| `T=1.0`, top-p 0.9 | 4 | Conversation |
| `T=2.0`, top-p 0.9 | 6 | Marginal — nonsense is close to the boundary |

**How far does top-p protect you as temperature rises?** §7.3 sweeps both rather than assuming, and the
honest answer is *further than an earlier draft of this lesson claimed*:

| | `p=0.9` | `p=0.95` | `p=0.98` |
|---|---|---|---|
| `T=1.0` | 4 | 5 | 6 |
| `T=2.0` | 6 | 6 | **7 ✗** |
| `T=3.0` | 6 | **7 ✗** | **8 ✗** |
| `T=5.0` | **7 ✗** | **8 ✗** | **8 ✗** |

*(✗ = a nonsense token survived truncation)*

**Top-p 0.9 does hold up to about `T = 3.0` here**, because `purple` and `Tuesday` stay ranked 7th and
8th and the nucleus never reaches them. But `P(purple)` before truncation rose from 0.000028 at
`T = 0.5` to **0.0941 at `T = 10` — a 3,348× increase** — and at looser top-p values the nonsense gets
through, earlier at higher temperature.

**The practical warning survives the correction, and is more important than the specific numbers.**
This toy has 8 tokens, two of which are *obviously* absurd and therefore ranked last. A real vocabulary
has ~100,000 tokens, and thousands of them are **plausible-but-wrong** rather than absurd — those sit
*high* in the ranking, well inside the nucleus, and top-p keeps every one of them. **Do not treat
top-p as a safety net for a high temperature.**

---

## 7. Practical activity

**File:** [`labs/m4/l14_decoding.py`](../../labs/m4/l14_decoding.py)

**No API key, no network.**

```bash
source .venv/bin/activate
python labs/m4/l14_decoding.py
```

Verifies every §6 number, measures how many tokens top-p keeps across distributions of different
shapes, generates from a trained model at each setting, demonstrates greedy looping, shows temperature
and top-p interacting, and demonstrates floating-point non-determinism.

### 7.2 Expected output

`[EXECUTED]` on Python 3.12.3, NumPy 2.5.3, 2026-09-09.

```text

============================================================================
1. THE WORKED EXAMPLE: ONE DISTRIBUTION, THREE TEMPERATURES
============================================================================
  prompt: 'The weather today is'

  token         logit    exp(z)     T=0.5     T=1.0     T=2.0
  sunny           3.2     24.53    0.6192    0.4190    0.2802
  cloudy          2.8     16.44    0.2782    0.2809    0.2294
  rainy           2.1      8.17    0.0686    0.1395    0.1617
  cold            1.5      4.48    0.0207    0.0765    0.1198
  warm            1.2      3.32    0.0113    0.0567    0.1031
  terrible        0.3      1.35    0.0019    0.0231    0.0657
  purple         -1.8      0.17    0.0000    0.0028    0.0230
  Tuesday        -2.4      0.09    0.0000    0.0015    0.0170
  sum                     58.55    1.0000    1.0000    1.0000

  section 6.1 and 6.2 verified to 4 dp.

  the 'purple' row is the one to read:
    T=0.5 : 0.000028  (1 in 35,571 tokens)
    T=1.0 : 0.002823  (1 in 354)
    T=2.0 : 0.023003  (1 in 43)

  At T=2.0 'The weather today is purple' appears about once every
  43 tokens. Temperature did not make the model creative --
  it made a nonsense token REACHABLE. Those are different things.

============================================================================
2. TOP-K, TOP-P AND MIN-P ON THE SAME DISTRIBUTION
============================================================================
  starting from T=1.0 probabilities

  strategy          kept   tokens kept
  greedy               1   sunny
  top-k = 3            3   sunny, cloudy, rainy
  top-p = 0.9          4   sunny, cloudy, rainy, cold
  min-p = 0.1          5   sunny, cloudy, rainy, cold, warm

  top-p = 0.9 cumulative sums:
    sunny         0.4190   cumulative  0.4190
    cloudy        0.2809   cumulative  0.6999
    rainy         0.1395   cumulative  0.8393
    cold          0.0765   cumulative  0.9159  <- reaches 0.9 here
    warm          0.0567   cumulative  0.9726
    terrible      0.0231   cumulative  0.9956
    purple        0.0028   cumulative  0.9985
    Tuesday       0.0015   cumulative  1.0000

  top-k = 3 renormalised:
    sunny         0.4992
    cloudy        0.3346
    rainy         0.1662
  section 6.3 verified.

  min-p = 0.1 threshold = 0.1 x 0.4190 = 0.0419
  kept: ['sunny', 'cloudy', 'rainy', 'cold', 'warm']

============================================================================
3. WHY TOP-P IS THE DEFAULT: IT ADAPTS, TOP-K DOES NOT
============================================================================
  distribution              top prob   top-p 0.9 keeps   top-k 3 keeps   min-p 0.1
  very peaked                 0.9950                 1               3           1
  peaked (the example)        0.4190                 4               3           5
  moderate                    0.2271                 7               3           8
  flat                        0.1479                 8               3           8
  uniform                     0.1250                 8               3           8

  Top-p keeps 2 tokens when the model is certain and 8 when it is not.
  Top-k keeps 3 EVERY TIME -- too many for the peaked case, far too few
  for the flat one. One fixed number cannot suit both distributions,
  and that is the whole argument for top-p.

============================================================================
4. TEMPERATURE AND TOP-P INTERACT  (finding the actual boundary)
============================================================================
  Does top-p protect you as temperature rises? Sweep BOTH and find out
  rather than assuming.

             p=0.9    p=0.95    p=0.98    p=0.99     <- top-p
       T      kept      kept      kept      kept
     0.5         3         3         4         5
     1.0         4         5         6         6
     2.0         6         6        7*        8*
     3.0         6        7*        8*        8*
     5.0        7*        8*        8*        8*
    10.0        7*        8*        8*        8*
     (* = at least one nonsense token survived truncation)

  probability mass reaching the two nonsense tokens BEFORE truncation:
       T    P(purple)   P(Tuesday)   tail total   rank of purple
     0.5       0.0000       0.0000       0.0000                7
     1.0       0.0028       0.0015       0.0044                7
     2.0       0.0230       0.0170       0.0400                7
     3.0       0.0432       0.0354       0.0786                7
     5.0       0.0686       0.0609       0.1295                7
    10.0       0.0941       0.0886       0.1827                7

  READ THIS HONESTLY. With only 8 tokens and this logit spread, top-p
  0.9 DOES keep the nonsense out at every temperature tested -- the two
  worst tokens stay ranked 7th and 8th, and 0.9 never reaches that far.
  My first draft of this lesson claimed otherwise; the measurement
  disagreed, so the lesson was corrected.

  But look at what temperature DID do: P(purple) before truncation went
  from 0.000028 at T=0.5 to 0.0941 at T=10 -- a 3,348x increase.
  And at looser top-p values the nonsense DOES get through, earlier at
  higher temperature. The interaction is real; it is just bounded by how
  far down the ranking the bad tokens sit.

  THE PRACTICAL POINT: top-p protects you only while the tokens you do
  not want stay OUTSIDE the nucleus. A real vocabulary has 100,000
  tokens, not 8, and thousands of them are plausible-but-wrong rather
  than obviously absurd -- those sit high in the ranking and top-p keeps
  them. Do not treat top-p as a safety net for a high temperature.

============================================================================
5. DECODING A REAL MODEL: GREEDY LOOPS, SAMPLING WANDERS
============================================================================
  vocabulary 15, trained on templated sentences

  greedy (T=0)
    'the cat sat on the mat . the dog ran to the park . the cat'
    'the cat sat on the mat . the dog ran to the park . the cat'
  T=0.3
    'the cat sat on the mat . the dog ran to the park . the cat'
    'the cat sat on the mat . the dog ran to the park . a bird'
  T=0.8
    'the cat sat on the mat . the dog ran to the park . the cat'
    'the cat sat on the mat . the dog ran to the park . a bird'
  T=0.8, top-p 0.9
    'the cat sat on the mat . the dog ran to the park . the cat'
    'the cat sat on the mat . the dog ran to the park . a bird'
  T=2.0
    'the cat sat on on mat . the dog ran to the park . the cat'
    'the cat sat on the park . the dog ran to ran to the park .'
  T=2.0, top-p 0.9
    'the cat sat on the dog sat on the mat . the dog ran to the'
    'the cat sat on the mat . the dog ran to the park . a bird'

  Greedy is identical on both runs and cycles the same sentence.
  T=0.8 with top-p 0.9 varies while staying grammatical.
  T=2.0 wanders into word salad, and top-p 0.9 only partly rescues it --
  the same interaction section 4 measured.

============================================================================
6. QUANTIFYING THE REPETITION / INCOHERENCE TRADE-OFF
============================================================================
  setting                 unique tokens  valid bigrams  repeated 4-grams
  greedy (T=0)                    0.556          1.000             0.067
  T=0.3                           0.622          1.000             0.036
  T=0.8                           0.641          1.000             0.031
  T=0.8, top-p 0.9                0.641          1.000             0.031
  T=1.5                           0.617          0.978             0.051
  T=2.5                           0.541          0.859             0.036

  Read the two ENDS, and note that 'unique tokens' is not the metric
  it looks like -- it peaks in the MIDDLE, because at very high
  temperature the model cycles through nonsense repetitively too.

  The two diagnostic columns are the outer ones:
    repeated 4-grams is HIGHEST at greedy (0.067) -- that is REPETITION
    valid bigrams is LOWEST at T=2.5 (0.859)     -- that is INCOHERENCE

  Both are near their best around T=0.8, which is why that region is
  the conventional default. There is no setting that maximises both, and
  the corpus here is deliberately simple -- on real text the incoherence
  arrives sooner and the usable window is narrower.

============================================================================
7. WHY TEMPERATURE 0 IS NOT DETERMINISTIC
============================================================================
  Floating-point addition is not associative: (a+b)+c != a+(b+c).
  GPU reductions sum in an order that depends on how requests are
  batched, so the SAME logits can come out microscopically different.

  a = 1e+16, b = -1e+16, c = 1.0
    (a + b) + c = 1.0
    a + (b + c) = 0.0
    equal? False

  now the case that matters -- two tokens whose logits are SO close
  that the summation order decides which wins. Real accelerators use
  float32 or bfloat16, where the reordering error is far larger than in
  the float64 NumPy defaults to, so this is done in float32:

    near-tied logit pairs tested : 4,000
    median logit gap             : 2.38e-07
    argmax flipped by sum order  : 1,774  (44.4%)

  Same numbers, same hardware, different summation ORDER -- and the
  chosen token changes in a measurable fraction of near-ties. On a real
  accelerator that order depends on how your request was batched with
  other users' requests, which is not under your control.

  When two tokens are near-tied, the order of summation decides which
  wins -- and that order is not under your control. It depends on how
  your request happened to be batched with other users' requests.

  THE RULE: never build anything requiring bit-identical model output.
  Cache by input, validate every response, and test for BEHAVIOUR
  rather than exact strings. A test asserting an exact generated string
  will be flaky, and the flakiness is not a bug in your code.

Done.
```

### 7.3 Reading the result

**Section 1 verified §6 and corrected it.** The `T = 1.0` column was right; the `T = 0.5` and
`T = 2.0` columns in an earlier draft were not, and the lab's assertion caught it. The corrected
`purple` row is the one that matters: **1 in 35,571 tokens at `T = 0.5`, 1 in 43 at `T = 2.0`**.

**Temperature made a nonsense token reachable. It did not make the model more creative.** Those are
different claims, and only the first one is true.

**Section 2 confirms every truncation strategy's behaviour** on the same distribution: greedy keeps 1,
top-k=3 keeps 3, top-p=0.9 keeps 4 (reaching cumulative 0.9159 at `cold`), min-p=0.1 keeps 5.

**Section 3 is the argument for top-p in one table:**

| Distribution | Top probability | top-p 0.9 keeps | top-k 3 keeps |
|---|---|---|---|
| Very peaked | 0.9950 | **1** | 3 |
| Peaked | 0.4190 | 4 | 3 |
| Moderate | 0.2271 | 7 | 3 |
| Uniform | 0.1250 | **8** | 3 |

**Top-p keeps 1 token when the model is certain and 8 when it is not. Top-k keeps 3 every time** — too
many when the answer is obvious, far too few when it is genuinely open. One fixed number cannot serve
both, which is the whole reason top-p became the default.

**Section 4 contradicted this lesson's draft**, and the correction is in §6.6. I had asserted that
top-p 0.9 fails to protect at `T = 2.0`. Measured, it holds to about `T = 3.0` — the two nonsense
tokens stay ranked 7th and 8th, and the 0.9 nucleus never reaches that far.

The interaction is nonetheless real and the sweep locates it precisely: at `p = 0.95` nonsense gets
through at `T = 3.0`; at `p = 0.9` it gets through at `T = 5.0`. And `P(purple)` before truncation rose
**3,348×** across the sweep.

**The generalisation is the important part.** Top-p protects you only while the tokens you do not want
sit *outside* the nucleus. In this toy the bad tokens are absurd and therefore last. In a real
vocabulary the dangerous tokens are **plausible-but-wrong**, they rank high, and top-p keeps them all.

**Section 5 shows the trade-off in actual generated text.** Greedy produces
`'the cat sat on the mat . the dog ran to the park . the cat'` — **identical on both runs**, cycling.
`T = 0.8` with top-p 0.9 varies while staying grammatical. `T = 2.0` produces
`'the cat sat on on mat'` and `'the dog ran to ran to the park'` — visibly degraded.

**Section 6 quantifies it, and one column behaves unexpectedly:**

| Setting | Unique tokens | Valid bigrams | Repeated 4-grams |
|---|---|---|---|
| Greedy | 0.556 | 1.000 | **0.067** |
| T=0.8 | 0.641 | 1.000 | 0.031 |
| T=2.5 | 0.541 | **0.859** | 0.036 |

**"Unique tokens" peaks in the middle, not at high temperature** — at `T = 2.5` the model cycles
through *nonsense* repetitively, so diversity falls again. The two diagnostic columns are the outer
ones: **repeated 4-grams is highest at greedy (repetition); valid bigrams is lowest at T=2.5
(incoherence)**. Both are near their best around `T = 0.8`, which is why that region is the
conventional default.

**Section 7 demonstrates the non-determinism, and the rate is high.** With two tokens whose logits
differ by a median of **2.38e-07** — summed in float32, as real accelerators do — **44.4% of near-ties
flip** when the same 4,000 contributions are summed in a different order.

Same numbers, same hardware, different summation order, different token. On a real accelerator that
order depends on how your request was batched with other users' requests.

**Hence the rule: never build anything requiring bit-identical model output.** Cache by input hash,
validate every response, and test for *behaviour* rather than exact strings. A test asserting an exact
generated string will be flaky, and the flakiness is not a bug in your code.

---

## 8. Common mistakes and troubleshooting

1. **Leaving temperature at a chat default for structured output.** Use 0.
2. **Assuming temperature 0 is deterministic.**
3. **Using top-k where top-p is appropriate.**
4. **Raising temperature to get better answers.** It gets *different* answers.
5. **Applying repetition penalties to technical text.**
6. **Using beam search for open-ended generation.**
7. **Copying settings from a tutorial** without testing on your task.
8. **Testing for exact output strings.** They will vary.

| Symptom | Likely cause | Fix |
|---|---|---|
| Output repeats a phrase forever | Greedy or very low temperature | Raise temperature; use top-p; add a repetition penalty |
| Output is incoherent | Temperature too high | Lower it; tighten top-p |
| JSON sometimes malformed | Temperature above 0 | Set temperature 0; validate anyway (M2-L08) |
| Answers vary between identical calls | Sampling, or float non-determinism | Lower temperature; do not require exactness |
| Answers still vary at temperature 0 | Batching and float non-associativity | Expected; design for it |
| Same word repeated in technical output | Repetition penalty too aggressive | Lower or remove it |
| Output bland and generic | Beam search, or temperature too low | Sample instead |

---

## 9. Security, privacy, reliability, cost

- **Reliability.** **Never assume identical output for identical input.** Cache by input hash if you
  need consistency; validate every response.
- **Reliability.** Temperature 0 plus schema validation plus a retry is the correct pattern for
  structured output — not temperature 0 alone.
- **Security.** Higher temperature widens the range of reachable outputs, including ones your safety
  testing did not see. **Test at the temperature you will deploy.**
- **Cost.** Decoding settings do not change token cost directly, but they change *length*: a repetition
  loop at low temperature can run to `max_tokens` every time. **Always set `max_tokens`** (M4-L06).
- **Reliability.** Sampling settings are part of your configuration and must be version-controlled and
  included in evaluation runs. A silent temperature change is a silent behaviour change.

---

## 10. Exercises

### Exercise 1 — Beginner (~20 min)

1. Compute the softmax of `[2.0, 1.0, 0.5]` at `T = 1.0` and at `T = 0.5`.
2. What does temperature do that top-p does not, and vice versa?
3. For `[0.5, 0.25, 0.15, 0.06, 0.04]`, how many tokens does top-p = 0.9 keep?
4. Name three tasks that should use temperature 0.
5. Why is temperature 0 not deterministic?

### Exercise 2 — Intermediate (~35 min)

1. Run the lab and verify §6.2's table.
2. Implement top-k, top-p and min-p, and confirm each keeps the expected tokens for §6's distribution.
3. Measure the number of tokens top-p = 0.9 keeps across five distributions from peaked to flat.
4. Generate 20 samples at temperatures 0, 0.5, 1.0 and 2.0 and quantify the diversity of each.
5. Show that top-p 0.9 at `T = 2.0` admits tokens that `T = 0.5` made unreachable.

### Exercise 3 — Challenge (~45 min)

1. Demonstrate greedy looping and find the shortest prompt that triggers it.
2. Implement all four repetition penalties and measure their effect on repeated 4-grams *and* on a
   technical text that legitimately repeats a term.
3. Implement beam search and compare its output diversity with sampling at matched compute.
4. Demonstrate floating-point non-associativity changing an argmax, and estimate how often it would
   flip a real token choice.
5. Build a decoding-settings recommender: given a task description and a required output format,
   output settings with justifications.

---

## 11. Quiz

*(Answers: [`answer-keys/module-04-answers.md`](../../answer-keys/module-04-answers.md#m4-l14).)*

**Q1.** Temperature is applied:

- A. To the logits, before the softmax is computed.
- B. To the sampled token, after it has been selected.
- C. To the probabilities, after softmax normalisation.
- D. To the attention scores inside the final block.

**Q2.** What does raising temperature do?

- A. Adds new candidate tokens the model had not considered.
- B. Increases the model's accuracy on difficult questions.
- C. Flattens the distribution, raising low-probability tokens.
- D. Reduces the number of tokens that will be generated.

**Q3.** Top-p differs from top-k in that:

- A. It applies before temperature rather than after it.
- B. The number of tokens kept adapts to the distribution.
- C. It keeps a fixed proportion of the vocabulary each time.
- D. It operates on logits rather than on probabilities.

**Q4.** For `[0.42, 0.28, 0.14, 0.08, 0.06, 0.02]`, top-p = 0.9 keeps:

- A. 3 tokens  B. 5 tokens  C. 6 tokens  D. 4 tokens

**Q5.** You need reliably parseable JSON. Set temperature to:

- A. 0.7, the common conversational default value.
- B. 1.0, the model's own unmodified distribution.
- C. 0.0, then validate the output and retry on failure.
- D. 0.3, to allow slight formatting variation.

**Q6.** Why is temperature 0 not deterministic?

- A. The provider adds noise to prevent output caching.
- B. Temperature 0 is internally converted to a small value.
- C. The model's weights are updated between requests.
- D. Floating-point reduction order varies with batching.

**Q7.** Greedy decoding on repetitive text tends to:

- A. Loop, repeating the same phrase indefinitely.
- B. Produce more varied output than sampling does.
- C. Terminate early before reaching the token limit.
- D. Raise an error when a token repeats too often.

**Q8.** Min-p keeps tokens whose probability is:

- A. Above a fixed absolute threshold you configure.
- B. Within the top `k` positions after sorting.
- C. Above a fraction of the top token's probability.
- D. Summing cumulatively to at least the min-p value.

**Q9.** In §6, `purple` has 1.65% probability at `T = 2.0`. This shows temperature:

- A. Unlocks creative answers the model could not otherwise give.
- B. Makes nonsense tokens reachable rather than improving answers.
- C. Corrects the model's under-confidence on rare vocabulary.
- D. Has no meaningful effect on tokens below 5% probability.

**Q10.** Raising temperature while relying on top-p to protect you:

- A. Works reliably, since top-p removes the tail afterwards.
- B. Works only when top-p is set below 0.9 exactly.
- C. Is unreliable — plausible-but-wrong tokens rank inside the nucleus.
- D. Has no effect, as the two settings are independent.

**Q11.** *(Written, rubric-graded.)* In under 100 words, explain to a colleague why their JSON extraction
pipeline fails about 2% of the time, given that they are using temperature 0.7 "because that is the
default".

---

## 12. Revision notes

- **Decoding = turning a distribution into tokens.** Temperature **reshapes**; top-k/top-p/min-p
  **truncate**. Truncation happens *after* temperature.
- **`p_i = exp(z_i/T) / Σ exp(z_j/T)`** — identical to M3-L09's softmax temperature.
- **Every setting trades repetition against incoherence.** No setting avoids both; you choose a point.
- **Temperature adds no information.** It makes low-probability tokens *reachable*, which is not the
  same as making better answers available.
- **Top-k keeps a fixed count; top-p keeps an adaptive set.** That adaptation is why top-p is the
  default. **Min-p** thresholds relative to the model's own confidence.
- **Structured output → temperature 0**, plus schema validation, plus a retry. Not temperature 0 alone.
- **Temperature 0 is not deterministic** — floating-point non-associativity, batching, MoE routing.
  Measured: with a median logit gap of 2.38e-07 in float32, **44.4% of near-ties flip** on summation
  order alone. **Never test for exact output strings.**
- **Beam search is largely abandoned for open-ended generation** — bland output at `b×` the cost.
- **Repetition penalties punish legitimate repetition too.** Fix the prompt first.
- **Temperature and top-p interact, but top-p is more robust than folklore suggests.** Measured:
  `p = 0.9` held to `T ≈ 3.0` on an 8-token vocabulary. **The real danger is not absurd tokens — it is
  plausible-but-wrong ones, which rank high and sit inside the nucleus at any top-p.** Do not treat
  top-p as a safety net for a high temperature.
- **Always set `max_tokens`** — a low-temperature loop will otherwise run to the limit every time.

---

## 13. Completion checklist

- [ ] I can write the temperature formula and say where it applies.
- [ ] I verified §6.2's table by hand for at least one column.
- [ ] I can explain why top-p adapts and top-k does not.
- [ ] I know which tasks demand temperature 0.
- [ ] I can explain why temperature 0 is not deterministic.
- [ ] I know how far top-p protects against temperature, and why real vocabularies are worse.
- [ ] I saw 44.4% of near-tied token choices flip on summation order.
- [ ] I scored 8/11 on the quiz.

---

## 14. References

- Holtzman et al. (2019), *The Curious Case of Neural Text Degeneration* (nucleus sampling).
  <https://arxiv.org/abs/1904.09751> `[UNVERIFIED]`
- Fan et al. (2018), *Hierarchical Neural Story Generation* (top-k).
  <https://arxiv.org/abs/1805.04833> `[UNVERIFIED]`
- Minh et al. (2024), *Turning Up the Heat: Min-p Sampling*.
  <https://arxiv.org/abs/2407.01082> `[UNVERIFIED]`

---

## 15. Next lesson

→ [M4-L15 — Stop Conditions, Truncated Output and Finish Reasons](M4-L15-stop-conditions.md)

You can control *how* tokens are chosen. Next: how generation ends — and how to tell the difference
between a finished answer and a truncated one.
