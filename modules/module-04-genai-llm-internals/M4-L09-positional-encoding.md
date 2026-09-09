# M4-L09 — Positional Information

| | |
|---|---|
| **Lesson ID** | M4-L09 |
| **Difficulty** | 3 (Advanced) |
| **Estimated study time** | 1.5 hours |
| **Prerequisites** | [M4-L08](M4-L08-qkv-worked.md), [M4-L07](M4-L07-attention.md) |

---

## 1. Learning objectives

1. **Explain** why positional information must be added, citing the property that forces it.
2. **Compare** learned, sinusoidal, relative and rotary encodings on the properties that matter.
3. **Compute** a sinusoidal encoding and a rotary rotation by hand.
4. **Explain** why RoPE became the standard, in terms of one specific property.
5. **Predict** what happens beyond the trained context length, and name the mitigations.

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **Positional encoding** | Information about a token's position, injected into the model. |
| **Absolute position** | "This is token 7." |
| **Relative position** | "This token is 3 before that one." |
| **Sinusoidal** | Fixed encodings built from sines and cosines at varied frequencies. |
| **Learned positional embedding** | A trained table with one row per position. |
| **RoPE** | Rotary Position Embedding — rotates Q and K by an angle proportional to position. |
| **ALiBi** | Attention with Linear Biases — a distance penalty added to scores. |
| **Extrapolation** | Working beyond the trained sequence length. |
| **Position interpolation** | Compressing positions to fit a longer sequence into the trained range. |
| **NTK-aware scaling** | Adjusting RoPE frequencies to extend context. |

---

## 3. Plain-language explanation

### 3.1 Why this lesson exists

M4-L07 §7.3 proved it numerically: **attention is permutation-invariant to machine precision**
(5.55e-17). Shuffle the input and the outputs shuffle identically. `"dog bites man"` and
`"man bites dog"` are the same computation.

**So position must be injected separately.** This is not a refinement — without it the model is a bag
of words, and the difference between a transformer and a very expensive averaging machine is entirely
this lesson.

### 3.2 The four approaches, in one table

| Approach | How | Where it acts |
|---|---|---|
| **Learned absolute** | A trained table, one row per position, added to embeddings | Input |
| **Sinusoidal** | Fixed sine/cosine values added to embeddings | Input |
| **RoPE** | Rotate Q and K by an angle proportional to position | Inside attention |
| **ALiBi** | Add a distance penalty to attention scores | Inside attention |

**The first two say "you are at position 7". The last two encode "you are 3 apart from that one".**
That distinction is the whole story of why the field moved from the first pair to the second.

### 3.3 Why relative beats absolute

Consider `"the cat sat"` appearing at positions 0–2 in one document and 500–502 in another. With
absolute encodings these get **completely different** vectors, and the model must learn the same
pattern separately at every position it might occur.

With relative encodings, what matters is that `cat` is one after `the` — the same in both cases.
**The pattern is learned once and applies everywhere**, which is more parameter-efficient and
generalises far better to positions the model saw rarely during training.

---

## 4. Analogy

**Absolute encoding is a seat number; relative encoding is "two seats to your left."** If the whole
audience moves back three rows, every seat number changes and every relative description stays
correct.

### Where the analogy breaks

1. **Seat numbers are discrete and exact. Positional encodings are continuous vectors** blended into
   the representation, not looked up as facts.
2. **You can always read your seat number. A model has no separate "position" field** to consult; the
   information is mixed into the same vector as the meaning.
3. **A theatre has a fixed size. Sequence length varies**, and behaviour beyond the trained range is
   the whole of §5.6.
4. **Seat numbers do not decay. RoPE and ALiBi both make distant tokens progressively harder to
   attend to** — a bias the analogy has no equivalent for.

---

## 5. Detailed technical explanation

### 5.1 Learned absolute embeddings

```python
positions = np.arange(T)
X = token_embeddings + position_embeddings[positions]
```

A `(max_len, d_model)` trained table. Simple, and used by early models including BERT and GPT-2.

**Two hard limits:**

- **A fixed maximum length.** Position `max_len` has no row. There is no answer beyond it, at all.
- **No generalisation between positions.** Row 500 and row 501 are independent parameters; nothing
  ties them together, so a pattern learned at one position is not available at another.

### 5.2 Sinusoidal encodings

$$PE_{(pos,\\,2i)} = \\sin\\!\\left(\\frac{pos}{10000^{2i/d}}\\right) \\qquad
PE_{(pos,\\,2i+1)} = \\cos\\!\\left(\\frac{pos}{10000^{2i/d}}\\right)$$

Each dimension pair oscillates at a different frequency — fast in early dimensions, extremely slow in
later ones. **Together they form a unique fingerprint per position**, rather like a binary counter
written in continuous values.

**Advantages:** no parameters, defined for any position, and `PE(pos+k)` is a fixed linear function
of `PE(pos)` — so relative offsets are *representable*.

**The catch:** representable is not the same as *used*. Nothing forces the model to exploit that
structure, and in practice sinusoidal encodings extrapolate poorly beyond the trained length. §7.3
measures the similarity decay that makes them look promising and the failure that follows anyway.

### 5.3 RoPE — the current standard

Instead of adding anything to the input, **rotate the query and key vectors** by an angle proportional
to position. Treat consecutive dimension pairs as 2-D coordinates and rotate each pair by `θ = pos ×
frequency`:

```python
def rope(x, pos, theta_base=10000.0):
    d = x.shape[-1]
    freqs = 1.0 / (theta_base ** (np.arange(0, d, 2) / d))
    angles = pos * freqs
    cos, sin = np.cos(angles), np.sin(angles)
    x_even, x_odd = x[..., 0::2], x[..., 1::2]
    out = np.empty_like(x)
    out[..., 0::2] = x_even * cos - x_odd * sin
    out[..., 1::2] = x_even * sin + x_odd * cos
    return out
```

**The property that made it standard.** Rotating `q` by angle `mθ` and `k` by `nθ` makes their dot
product depend on `(m − n)` **only** — the relative distance — and not on `m` or `n` individually.
This is not a heuristic that works well in practice; it is an algebraic identity, and §7.3 verifies it
numerically.

**Consequences:**

- Relative position, for free, with **no parameters**.
- Applied to Q and K inside attention, so it does not consume representation capacity in the residual
  stream.
- Compatible with KV caching (M4-L17): a cached key keeps its rotation.
- Extends more gracefully than absolute encodings, though **not indefinitely** (§5.6).

### 5.4 ALiBi

Add a linear penalty to attention scores based on distance:

```python
scores = scores - slope * distance_matrix
```

Different heads get different slopes, so some attend locally and some globally. **No positional vector
at all** — just a bias. Simple, and it extrapolates unusually well.

### 5.5 Comparison

| | Learned | Sinusoidal | RoPE | ALiBi |
|---|---|---|---|---|
| Parameters | `max_len × d` | 0 | 0 | 0 |
| Relative? | No | Representable | **Yes, exactly** | Yes |
| Hard length limit | **Yes** | No | No | No |
| Extrapolates | Not at all | Poorly | Moderately | Well |
| Where applied | Input | Input | Q and K | Scores |
| Current use | Older models | Original transformer | **Most modern LLMs** | Some models |

### 5.6 What happens beyond the trained length

**Nothing warns you.** The model produces output; it is simply worse — often much worse, and sometimes
degenerate.

| Encoding | Beyond the trained length |
|---|---|
| Learned absolute | **Impossible** — no embedding row exists |
| Sinusoidal | Defined, but quality degrades sharply |
| RoPE | Defined; degrades, with mitigations available |
| ALiBi | Degrades most gracefully |

**Mitigations for RoPE** `[UNVERIFIED — active research; check the current literature]`:

- **Position interpolation** — compress positions into the trained range (e.g. treat position 8,000 as
  2,000 when trained on 2,048). Cheap; costs some fine-grained resolution.
- **NTK-aware scaling** — adjust the frequency base rather than the positions, preserving
  high-frequency detail better.
- **Continued training at the longer length** — the most reliable and the most expensive.

**The practical rule: a model's advertised context is a claim about what it accepts, not what it
handles well.** M4-L06 §5.4 makes the same point from the other direction. **Test at the length you
will actually use.**

### 5.7 Assumptions and limitations

- Which encoding a given model uses is a model-specific fact; check its documentation or code.
- Extension techniques change quickly and are marked `[UNVERIFIED]` throughout.
- ALiBi's extrapolation advantage is well reported but comes with its own trade-offs; do not treat
  the comparison table as a ranking.

---

## 6. Worked example — sinusoidal and RoPE by hand

`d_model = 4`, so two frequency pairs.

### 6.1 Sinusoidal

Frequencies: `1/10000^(0/4) = 1.0` and `1/10000^(2/4) = 1/100 = 0.01`.

| Position | `sin(pos×1)` | `cos(pos×1)` | `sin(pos×0.01)` | `cos(pos×0.01)` |
|---|---|---|---|---|
| 0 | 0.0000 | 1.0000 | 0.0000 | 1.0000 |
| 1 | 0.8415 | 0.5403 | 0.0100 | 1.0000 |
| 2 | 0.9093 | −0.4161 | 0.0200 | 0.9998 |
| 3 | 0.1411 | −0.9900 | 0.0300 | 0.9996 |

**Read the columns.** The first pair swings wildly between adjacent positions — it distinguishes
neighbours. The second barely moves — it distinguishes *regions*. **Together they encode position at
several scales at once**, which is why several frequencies are used rather than one.

### 6.2 RoPE, and the property that matters

`q = [1.0, 0.0, 1.0, 0.0]` at position `m`, and `k = [1.0, 0.0, 1.0, 0.0]` at position `n`. **The same
vector at two positions**, so any difference in their dot product comes purely from position.

Rotate dimension pair 0 by `m × 1.0` and pair 1 by `m × 0.01`.

**At `m = 2`:**

```
pair 0: [1,0] rotated by 2.00 rad → [cos 2.00, sin 2.00] = [−0.4161,  0.9093]
pair 1: [1,0] rotated by 0.02 rad → [cos 0.02, sin 0.02] = [ 0.9998,  0.0200]
q_rot = [−0.4161, 0.9093, 0.9998, 0.0200]
```

**At `n = 5`:**

```
pair 0: [1,0] rotated by 5.00 rad → [ 0.2837, −0.9589]
pair 1: [1,0] rotated by 0.05 rad → [ 0.9988,  0.0500]
k_rot = [ 0.2837, −0.9589, 0.9988, 0.0500]
```

**Dot product, pair by pair:**

```
pair 0: (−0.4161)(0.2837) + (0.9093)(−0.9589) = −0.1181 − 0.8719 = −0.9900
pair 1: ( 0.9998)(0.9988) + (0.0200)( 0.0500) =  0.9986 + 0.0010 =  0.9996
                                                          total  =  0.0096
```

**Now look at what those two pair-totals actually are.**

```
−0.9900 = cos(−3.00) = cos((m − n) × 1.0)
 0.9996 = cos(−0.03) = cos((m − n) × 0.01)
```

**Each pair's contribution collapsed to a cosine of the *distance*.** The absolute positions 2 and 5
have vanished; only `m − n = −3` survives. This is not a coincidence of these numbers — it is the
rotation identity `cos(a)cos(b) + sin(a)sin(b) = cos(a − b)`, applied per pair.

**The test.** Repeat at `m = 12`, `n = 15` — completely different absolute positions, **same distance
of 3**:

```
pair 0: cos((12 − 15) × 1.0)  = cos(−3.00) = −0.9900
pair 1: cos((12 − 15) × 0.01) = cos(−0.03) =  0.9996
                                     total =  0.0096
```

**Identical.** And at `m = 500`, `n = 503`, it is 0.0096 again. §7.3 verifies this across 40 random
position pairs at each of six distances up to 5,000, with a worst deviation of **2.91e-14** —
floating-point noise.

**This algebraic identity is why RoPE became the standard.** Not "it works well empirically" — the dot
product provably depends on `m − n` and nothing else, giving exact relative position with **zero
parameters**, no learned table, and no maximum length. The rotation is applied to Q and K *inside*
attention, so it also costs nothing in the residual stream and survives KV caching.

**Why not V?** Because the identity is about the *dot product* `q·k`, which is the only place position
needs to enter. Rotating V would rotate the output itself, making the block's output depend on
absolute position — destroying the very property RoPE exists to provide. Exercise 3.5 asks you to
demonstrate this.

## 7. Practical activity

**File:** [`labs/m4/l09_positional.py`](../../labs/m4/l09_positional.py)

**No API key, no network.**

```bash
source .venv/bin/activate
python labs/m4/l09_positional.py
```

Builds sinusoidal encodings and plots their similarity decay, implements RoPE and **proves** the
relative-distance property numerically, compares all four schemes on extrapolation, and demonstrates
position interpolation.

### 7.2 Expected output

`[EXECUTED]` on Python 3.12.3, NumPy 2.5.3, 2026-09-08.

```text

============================================================================
1. SINUSOIDAL ENCODINGS  (verifying the lesson's table)
============================================================================
  d_model = 4, frequencies = ['1.0000', '0.0100']

    pos    sin(p*1)    cos(p*1)   sin(p*0.01)   cos(p*0.01)
      0      0.0000      1.0000        0.0000        1.0000
      1      0.8415      0.5403        0.0100        1.0000
      2      0.9093     -0.4161        0.0200        0.9998
      3      0.1411     -0.9900        0.0300        0.9996

  section 6.1 verified to 4 dp.

  The fast pair swings wildly between adjacent positions (it separates
  NEIGHBOURS); the slow pair barely moves (it separates REGIONS). That
  is why several frequencies are used rather than one.

  similarity between position encodings, as distance grows:
    distance     cos(PE[0], PE[d])   profile
           0                1.0000   |#######################################
           1                0.9662   |#######################################
           2                0.8845   |#####################################
           4                0.7479   |##################################
           8                0.7004   |##################################
          16                0.6054   |################################
          32                0.6111   |################################
          64                0.4346   |############################
         128                0.2839   |#########################
         256                0.3537   |###########################
         512                0.1854   |#######################

  Similarity decays with distance -- nearby positions look alike, distant
  ones do not. The model CAN exploit this. Nothing forces it to.

============================================================================
2. RoPE, AND THE PROPERTY THAT MADE IT STANDARD
============================================================================
  q = k = [1, 0, 1, 0] -- the SAME vector at two positions, so any
  difference in the dot product comes purely from position.

  m =   2, n =   5   (distance -3)
    q_rot = [-0.4161  0.9093  0.9998  0.02  ]
    k_rot = [ 0.2837 -0.9589  0.9988  0.05  ]
    pair 0 contribution:   -0.9900   = cos(-3.00) = -0.9900
    pair 1 contribution:    0.9996   = cos(-0.03) = 0.9996
    total              :    0.0096

  m =  12, n =  15   (distance -3)
    q_rot = [ 0.8439 -0.5366  0.9928  0.1197]
    k_rot = [-0.7597  0.6503  0.9888  0.1494]
    pair 0 contribution:   -0.9900   = cos(-3.00) = -0.9900
    pair 1 contribution:    0.9996   = cos(-0.03) = 0.9996
    total              :    0.0096

  Both distances are -3, and both totals are identical. The absolute
  positions vanished; only m - n survived.

  now verifying it exhaustively -- 40 position pairs at each distance:
    distance     mean dot   max deviation     verdict
           1     1.540252        1.11e-15    CONSTANT
           3     0.009558        2.92e-15    CONSTANT
           7     1.751453        4.88e-15    CONSTANT
          50     1.842549        6.66e-16    CONSTANT
         500    -0.600187        2.22e-16    CONSTANT
        5000     1.119634        2.91e-14    CONSTANT

  worst deviation across all distances: 2.91e-14
  The dot product depends on m - n and NOTHING else, to within floating-
  point noise. This is an algebraic identity, not an empirical finding.

  and the same test with RoPE wrongly applied to V as well:
    distance    mean output[0]   max deviation     verdict
           1         -0.093409        1.11e+00      VARIES
           3         -0.002285        8.94e-03      VARIES
          50         -0.128681        1.31e+00      VARIES

  Rotating V makes the OUTPUT depend on absolute position, destroying
  the property RoPE exists to provide. Apply it to Q and K only.

============================================================================
3. ALiBi: A DISTANCE PENALTY ON THE SCORES
============================================================================
  attention from the LAST position, flat scores, 8 tokens.
  Different heads get different slopes:

     slope      pos0    pos1    pos2    pos3    pos4    pos5    pos6    pos7   effective range
     0.000     0.125   0.125   0.125   0.125   0.125   0.125   0.125   0.125                 8
     0.125     0.077   0.088   0.099   0.113   0.128   0.145   0.164   0.186                 7
     0.250     0.044   0.057   0.073   0.094   0.121   0.155   0.199   0.256                 7
     0.500     0.012   0.020   0.033   0.054   0.089   0.147   0.243   0.401                 5
     1.000     0.001   0.002   0.004   0.012   0.031   0.086   0.233   0.632                 3

  slope 0 attends uniformly over the whole past; larger slopes
  concentrate on recent tokens. A model with a spread of slopes across
  heads gets local AND global views for free, with no parameters and no
  positional vector at all.

============================================================================
4. BEYOND THE TRAINED LENGTH  (what this CAN and CANNOT be measured)
============================================================================
  a model trained to length 512, then asked for longer.

  FIRST, what IS measurable without a trained model: are the encodings
  still well-defined and still distinguishable out there?

  scheme                      at 256      at 512     at 1024     at 4096
  learned absolute           defined     defined      NO ROW      NO ROW
  sinusoidal                  0.9662      0.9662      0.9662      0.9662
  RoPE                        0.9662      0.9662      0.9662      0.9662
                          <- similarity between ADJACENT positions

  Read that carefully. For a learned table, position 1024 has NO ROW --
  the failure is total and immediate. For sinusoidal and RoPE the
  adjacent-position similarity is IDENTICAL at every length, because
  both schemes are translation-invariant by construction. Positions
  100,000 apart are as distinguishable as positions 100 apart.

  So the encodings do not degrade. NOW THE HONEST LIMIT OF THIS LAB:
  that is not what extrapolation failure is. The encodings are fine; the
  MODEL has simply never seen them. Weights trained only on rotations up
  to angle 512*theta have no idea what to do with angle 4096*theta, and
  measuring that requires a trained model, which this lab does not have.

  What you can take from this section:
    * learned tables fail HARD and immediately (no row exists)
    * sinusoidal and RoPE fail SOFTLY and silently (defined, untrained)
    * and the second failure mode is the more dangerous one, because
      nothing errors -- see M4-L06 section 5.4 for the same point about
      effective context. TEST AT YOUR REAL LENGTH.

============================================================================
5. POSITION INTERPOLATION: THE TRADE IT MAKES
============================================================================
  trained context 512; extending to 4x by compressing positions
  (position p is presented to the model as p / 4)

                           adjacent sim   sim at dist 10    resolution
  original (no scaling)        0.966151         0.657863      0.033849
  interpolated (4x)            0.997776         0.839595      0.002224

  adjacent positions become 15x harder to tell apart.
  That is the cost of interpolation, and it is why an interpolated model
  can get WORSE at short sequences while getting better at long ones.
  Evaluate BOTH ranges before shipping (M4-L09 section 9).

============================================================================
6. THE PARAMETER COST OF EACH SCHEME
============================================================================
  scheme                        2k ctx       32k ctx      128k ctx
  learned absolute               8.4M       134.2M       536.9M
  sinusoidal                        0             0             0
  RoPE                              0             0             0
  ALiBi                             0             0             0

  A learned table at 128k context and d_model 4096 costs
  537M parameters -- about 8% of a 7B model,
  spent entirely on saying where each token is. RoPE and ALiBi do the
  same job for nothing, which is the other half of why the field moved.

Done.
```

### 7.3 Reading the result

**Section 1 verifies §6.1 to four decimal places** and then shows why several frequencies are used:
similarity between position encodings decays with distance — 0.9662 at distance 1, 0.4346 at 64,
0.1854 at 512. Nearby positions look alike; distant ones do not. **The model *can* exploit that
structure. Nothing forces it to**, which is the practical weakness of sinusoidal encodings.

**Section 2 is the result this lesson exists for.**

At `m=2, n=5` and again at `m=12, n=15` — completely different absolute positions, same distance of
−3 — the pair contributions are **identical**: −0.9900 and 0.9996, totalling **0.0096** both times.
And each pair's contribution is exactly `cos((m−n) × frequency)`, as the rotation identity predicts.

The exhaustive check makes it unambiguous. Forty random position pairs at each of six distances:

| Distance | Mean dot product | Max deviation |
|---|---|---|
| 1 | 1.540252 | 1.11e-15 |
| 3 | 0.009558 | 2.92e-15 |
| 50 | 1.842549 | 6.66e-16 |
| **5,000** | 1.119634 | **2.91e-14** |

**The dot product is constant across all positions at a given distance, to within floating-point
noise** — even at distance 5,000. This is an algebraic identity, not an empirical tendency, and it is
why RoPE displaced learned and sinusoidal encodings: exact relative position, **zero parameters**, no
maximum length.

The lab then applies RoPE to V as well, and the property **breaks immediately** — the output varies
with absolute position at every distance tested. Rotating V rotates the block's *output*, which is
precisely what RoPE exists to avoid. **Q and K only.**

**Section 3 shows ALiBi's slopes producing different attention ranges** from identical scores: slope 0
attends uniformly across all 8 positions, slope 1.0 puts **0.632** on the immediately preceding token
and effectively sees 3. A model with a spread of slopes across heads gets local and global views
simultaneously, with no positional vector at all.

**Section 4 required rewriting, and the correction is the useful part.**

The first version presented an "extrapolation" table showing sinusoidal and RoPE at 0.9662 for every
length — a constant, measuring nothing. That is not a broken experiment; **the metric is constant *by
construction*.** Both schemes are translation-invariant, so positions 100,000 apart are exactly as
distinguishable as positions 100 apart. The encodings do not degrade at long range.

**Which means the metric cannot measure extrapolation failure at all**, because that failure is not
about the encodings. It is that the *model* has never seen those rotations: weights trained only on
angles up to `512θ` have no learned behaviour for `4096θ`. Measuring it needs a trained long-context
model, which this lab does not have — and the lab now says so.

What the section *can* establish is the distinction that matters operationally:

- **Learned tables fail hard and immediately** — position 1024 has no row, and you get an index error.
- **Sinusoidal and RoPE fail softly and silently** — perfectly defined, entirely untrained.

**The second failure mode is the more dangerous one**, for exactly the reason M4-L06 §5.4 gives about
effective context: nothing errors.

**Section 5 prices position interpolation.** Compressing positions 4× makes adjacent positions
**15× harder to distinguish** (similarity 0.9662 → 0.9978). That is the trade, stated numerically —
and it is why an interpolated long-context model can get *worse* at short documents while getting
better at long ones. **Evaluate both ranges.**

**Section 6 gives the other half of why the field moved.** A learned positional table at 128k context
and `d_model` 4,096 costs **536.9M parameters — about 8% of a 7B model — spent entirely on saying
where each token is.** RoPE and ALiBi do the same job for **zero**.

---

## 8. Common mistakes and troubleshooting

1. **Forgetting positional encoding entirely.** The model becomes a bag of words.
2. **Exceeding a learned table's `max_len`.** Index error, or silently wrong.
3. **Applying RoPE to values as well as queries and keys.** It belongs on Q and K only.
4. **Assuming a model works well at its advertised length.**
5. **Adding positional encodings after attention** instead of before.
6. **Mixing rotation conventions** between training and inference.
7. **Interpolating positions without evaluating** the quality cost.

| Symptom | Likely cause | Fix |
|---|---|---|
| Word order does not affect output | No positional encoding | Add it |
| Index error at long input | Learned table exceeded | Truncate, or use a relative scheme |
| Quality collapses past a length | Extrapolation failure | Interpolation, NTK scaling, or continued training |
| Fine-tuned long-context model got worse at short | Interpolation hurt short sequences | Evaluate both ranges |
| RoPE gives absolute-looking behaviour | Applied to the wrong tensors | Q and K only |
| Cached keys mismatch after resume | Rotation applied twice | Rotate once, then cache |

---

## 9. Security, privacy, reliability, cost

- **Reliability.** Behaviour beyond the trained length degrades **silently**. Test at your real
  maximum length and set a hard input limit below it.
- **Reliability.** If you extend context by interpolation, **evaluate short sequences too** — the
  extension can cost quality at lengths that previously worked.
- **Cost.** RoPE and ALiBi cost no parameters and negligible compute. Learned tables cost
  `max_len × d_model` parameters — at 32,768 × 4,096 that is **134M parameters** spent on position
  alone.
- **Security.** A model that degrades past its effective length can produce incoherent or unsafe
  output on very long inputs. If untrusted users control input length, cap it explicitly rather than
  relying on the model.

---

## 10. Exercises

### Exercise 1 — Beginner (~20 min)

1. Why must positional information be added at all? Cite the property.
2. Give one advantage and one disadvantage of learned absolute embeddings.
3. What does RoPE's dot product depend on, and what does it *not* depend on?
4. Why does the sinusoidal scheme use several frequencies?
5. What happens beyond a learned table's maximum position?

### Exercise 2 — Intermediate (~35 min)

1. Implement sinusoidal encodings and verify §6.1's table.
2. Implement RoPE and verify that `rope(q,m)·rope(k,n)` depends only on `m−n`, for at least 20 pairs.
3. Plot similarity between positional encodings as a function of distance for both schemes.
4. Implement ALiBi and show that different slopes produce different attention ranges.
5. Compute the parameter cost of a learned table for `max_len` 2k, 32k and 128k at `d_model` 4,096.

### Exercise 3 — Challenge (~45 min)

1. Prove RoPE's relative property algebraically for a single 2-D pair, then confirm numerically.
2. Implement position interpolation and measure the resolution loss between adjacent positions.
3. Implement NTK-aware scaling and compare its adjacent-position resolution with plain interpolation.
4. Train a tiny model with each of the four schemes on a position-sensitive task. Report accuracy
   inside and beyond the trained length.
5. Show that applying RoPE to values as well as Q and K breaks the relative-distance property, and
   explain why.

---

## 11. Quiz

*(Answers: [`answer-keys/module-04-answers.md`](../../answer-keys/module-04-answers.md#m4-l09).)*

**Q1.** Why is positional encoding necessary?

- A. Attention is permutation-invariant and cannot distinguish order.
- B. Tokenizers discard word order during the encoding step.
- C. Embeddings are identical for every occurrence of a token.
- D. Softmax normalisation removes any sequence information.

**Q2.** A learned absolute positional table's main limitation is:

- A. It has a fixed maximum length with no row beyond it.
- B. It cannot represent distances between two positions at all.
- C. It requires far more compute than a sinusoidal scheme.
- D. It must be recomputed for every new input sequence.

**Q3.** RoPE works by:

- A. Adding a fixed sinusoidal vector to the input embeddings.
- B. Rotating queries and keys by an angle proportional to position.
- C. Subtracting a distance penalty from the attention scores.
- D. Learning one rotation matrix for each possible position.

**Q4.** After RoPE, the dot product of a query and key depends on:

- A. Both absolute positions, `m` and `n`, independently.
- B. The absolute position of the query only.
- C. Neither position; RoPE affects only the magnitudes.
- D. The relative distance `m − n`, and nothing else.

**Q5.** Sinusoidal encodings use several frequencies because:

- A. A single frequency would produce identical values at all positions.
- B. The transformer requires exactly `d_model / 2` distinct frequencies.
- C. Different frequencies distinguish neighbours and regions alike.
- D. Multiple frequencies reduce the parameter count of the encoding.

**Q6.** ALiBi adds:

- A. A learned vector to each token's input embedding.
- B. A rotation applied to the value vectors before weighting.
- C. A distance-based penalty to the attention scores.
- D. An extra attention head dedicated to positional information.

**Q7.** What happens when a model is given input beyond its trained length?

- A. The provider's API raises a clear length-exceeded error.
- B. Output degrades silently, with no error and no warning.
- C. The model automatically truncates to its trained length.
- D. Positional encodings wrap around to the start of the range.

**Q8.** Position interpolation extends context by:

- A. Adding new rows to the learned positional embedding table.
- B. Increasing the frequency base used by the encoding.
- C. Compressing positions into the model's trained range.
- D. Removing the positional encoding beyond the trained length.

**Q9.** A learned table at `max_len` 32,768 and `d_model` 4,096 costs:

- A. 32,768 parameters  B. 4,096 parameters  C. 8 parameters  D. 134M parameters

**Q10.** RoPE should be applied to:

- A. Queries, keys and values, for consistency across the block.
- B. The input embeddings, before any projection occurs.
- C. Queries and keys only, inside the attention computation.
- D. The attention scores, after the matrix product.

**Q11.** *(Written, rubric-graded.)* In under 100 words, explain to a colleague why the team's
fine-tuned 128k-context model performs worse on short documents than the 8k model it replaced.

---

## 12. Revision notes

- **Attention is permutation-invariant** (measured at 5.55e-17 in M4-L07). Position must be injected
  separately, or the model is a bag of words.
- **Learned absolute**: a trained table. Simple, but a **hard maximum length** and no generalisation
  between positions. Costs `max_len × d_model` — **134M parameters** at 32k × 4,096.
- **Sinusoidal**: fixed sines and cosines at many frequencies — fast pairs distinguish neighbours,
  slow pairs distinguish regions. No parameters. Relative offsets are *representable* but not
  *enforced*, and it extrapolates poorly.
- **RoPE**: rotate **Q and K only** by an angle proportional to position. **The dot product then
  depends on `m − n` and nothing else** — verified to **2.91e-14** across distances up to 5,000. An
  algebraic identity, not a heuristic. Zero parameters, KV-cache compatible, now the standard.
  Rotating V as well **destroys** the property.
- **ALiBi**: a linear distance penalty on scores, with a different slope per head. Extrapolates best.
- **Beyond the trained length: learned tables fail HARD (no row exists); sinusoidal and RoPE fail
  SOFTLY.** The encodings themselves are translation-invariant and do not degrade — measured identical
  at 256 and 4,096. **The model simply never saw those angles.** The silent failure is the dangerous
  one. Mitigations: position interpolation, NTK-aware scaling, continued training.
- **Position interpolation costs resolution.** Measured: 4× compression made adjacent positions
  **15× harder to distinguish** — which is why an interpolated model can get worse at short inputs.
- **Parameter cost measured:** a learned table at 128k × 4,096 is **536.9M parameters (~8% of a 7B
  model)**; RoPE and ALiBi are **zero**.
- **Advertised context is what the model accepts, not what it handles well.** Test at your real
  length.

---

## 13. Completion checklist

- [ ] I can state the property that forces positional encoding to exist.
- [ ] I computed §6.1's sinusoidal table by hand.
- [ ] I verified RoPE's relative-distance property to 2.91e-14.
- [ ] I can explain why RoPE goes on Q and K but not V.
- [ ] I can name the parameter cost of a learned table at 32k.
- [ ] I know what happens past the trained length, and three mitigations.
- [ ] I scored 8/11 on the quiz.

---

## 14. References

- Vaswani et al. (2017), *Attention Is All You Need*, §3.5 (sinusoidal).
  <https://arxiv.org/abs/1706.03762> `[UNVERIFIED]`
- Su et al. (2021), *RoFormer: Enhanced Transformer with Rotary Position Embedding*.
  <https://arxiv.org/abs/2104.09864> `[UNVERIFIED]`
- Press et al. (2021), *Train Short, Test Long* (ALiBi). <https://arxiv.org/abs/2108.12409>
  `[UNVERIFIED]`
- Chen et al. (2023), *Extending Context Window via Position Interpolation*.
  <https://arxiv.org/abs/2306.15595> `[UNVERIFIED]`

---

## 15. Next lesson

→ [M4-L10 — Inside a Transformer Block](M4-L10-transformer-block.md)

You have attention and position. Next: the rest of the block — the feed-forward network, residual
connections and normalisation — and why each one is load-bearing.
