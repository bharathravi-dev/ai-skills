# M4-L05 — Language Modelling: Next-Token Prediction End to End

| | |
|---|---|
| **Lesson ID** | M4-L05 |
| **Difficulty** | 2 (Intermediate) |
| **Estimated study time** | 2 hours |
| **Prerequisites** | [M4-L04](M4-L04-embeddings.md), [M3-L05](../module-03-math-ml-essentials/M3-L05-logs-entropy.md), [M3-L09](../module-03-math-ml-essentials/M3-L09-logistic-regression.md) |

---

> **This lesson connects everything so far into one pipeline.** After it, you can trace a prompt from
> characters to a predicted token and state the shape of every intermediate. Modules 5 through 8 all
> assume this picture.

---

## 1. Learning objectives

1. **Trace** the complete path from prompt string to next-token probability, naming every shape.
2. **Explain** teacher forcing, and why training and generation differ so sharply in cost.
3. **Compute** cross-entropy loss and perplexity for a prediction, by hand.
4. **Explain** why generation is sequential and what that implies for latency.
5. **Describe** the causal mask and what breaks without it.

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **Autoregressive** | Generating one token at a time, each conditioned on all previous. |
| **Logits** | Raw unnormalised scores over the vocabulary, one per token. |
| **LM head** | The final linear layer mapping the hidden state to logits. |
| **Teacher forcing** | Training on the *true* previous tokens rather than the model's own. |
| **Causal mask** | A mask preventing a position from attending to later positions. |
| **Shifted labels** | The target at position `i` is the input token at position `i+1`. |
| **Prefill** | Processing the prompt — all positions in parallel. |
| **Decode** | Generating tokens — one at a time. |
| **KV cache** | Stored keys and values so prefill work is not repeated (M4-L17). |
| **Perplexity** | `exp(cross-entropy)` — the effective branching factor. |
| **Greedy decoding** | Always taking the highest-probability token. |

---

## 3. Plain-language explanation

### 3.1 The whole pipeline, in one place

```
"The capital of France is"
        │
        ▼  tokenizer (M4-L03)
   [791, 6864, 315, 9822, 374]                    5 token IDs
        │
        ▼  embedding lookup (M4-L04)
   (5, d_model)                                   5 vectors
        │
        ▼  + positional information (M4-L09)
   (5, d_model)
        │
        ▼  N transformer blocks (M4-L07 … M4-L10)
   (5, d_model)                                   refined by context
        │
        ▼  take the LAST position only
   (d_model,)
        │
        ▼  LM head: a linear layer to vocabulary size
   (vocab_size,)                                  logits
        │
        ▼  softmax (M3-L09)
   (vocab_size,)                                  probabilities summing to 1
        │
        ▼  sampling (M4-L14)
   " Paris"
```

**Every shape in that diagram matters, and being able to write them down is the objective.**

### 3.2 The two facts people find surprising

**Fact 1: the model predicts a next token at *every* position, not just the last.**

Given five input tokens, the model produces **five** probability distributions — a prediction after
"The", after "The capital", and so on. During generation you discard all but the last. During
training you use all of them, which is why training is enormously more efficient per unit of
compute.

**Fact 2: training is parallel, generation is sequential.**

In training the whole sequence is known in advance, so every position is processed at once. In
generation the model must produce token 1 before it can condition on it to produce token 2.

**This asymmetry is the single most important performance fact about LLMs.** It explains why prompt
processing is fast and output is slow, why output tokens cost more, why streaming exists, and why
latency scales with the number of tokens generated rather than with the length of the prompt.

---

## 4. Analogy

**Predicting the next word in a sentence someone is reading aloud.** You continuously form
expectations; each word confirms or surprises you; a surprising word carries more information. That
"surprise" is exactly cross-entropy loss (M3-L05).

### Where the analogy breaks

1. **You understand the sentence's meaning and intent.** The model computes a conditional
   distribution. The outputs often coincide; the processes do not.
2. **You can revise a misreading.** An autoregressive model cannot un-emit a token — errors compound
   forward, which is why a bad first sentence often ruins a whole response.
3. **You predict one continuation. The model computes a probability for the *entire vocabulary***,
   every time — 100,000 numbers per token.
4. **You bring knowledge of the world.** The model brings the statistics of its training corpus, and
   nothing more (M4-L16).

---

## 5. Detailed technical explanation

### 5.1 Every shape, written out

For a prompt of `T` tokens, `d_model` = 4,096, vocabulary 100,000:

| Stage | Shape | Notes |
|---|---|---|
| Token IDs | `(T,)` | Integers |
| Embeddings | `(T, 4096)` | One row lookup per token |
| + positional | `(T, 4096)` | Unchanged shape |
| After each block | `(T, 4096)` | **Shape never changes through the stack** |
| Final hidden state | `(T, 4096)` | |
| Logits | `(T, 100000)` | LM head: `(4096, 100000)` |
| Probabilities | `(T, 100000)` | Softmax over the last axis |
| Next token | scalar | Sampled from row `T−1` |

**The shape is constant through the whole transformer stack.** Every block is a `(T, d) → (T, d)`
function. That is what allows arbitrary depth.

**The logits tensor is enormous.** At `T` = 2,000 and a 100k vocabulary, that is 200M floats — **800
MB in float32 for a single forward pass**. This is why implementations compute logits only for the
positions they need, and why the LM head is often the largest single matrix in the model.

### 5.2 The LM head and tied weights

```python
logits = hidden @ W_lm.T          # (T, d) @ (d, V) -> (T, V)
```

`W_lm` has `d × V` parameters — 409.6M at 4,096 × 100,000, the same size as the input embedding
matrix (M4-L04 §5.1). **Weight tying** sets `W_lm = E`, halving the cost, on the reasoning that the
representation predicting a token and the representation *of* that token should be related.

### 5.3 Teacher forcing and shifted labels

Training on `"The capital of France is Paris"`:

| Position | Input | Target |
|---|---|---|
| 0 | `The` | `capital` |
| 1 | `capital` | `of` |
| 2 | `of` | `France` |
| 3 | `France` | `is` |
| 4 | `is` | `Paris` |

**The targets are the inputs shifted left by one.** No separate label file exists — this is what M1-L07
means by self-supervision, and it is why raw text is training data.

```python
inputs  = tokens[:-1]
targets = tokens[1:]
```

**Teacher forcing** means position 3 is fed the *true* token `France`, not whatever the model
predicted at position 2. Every position learns from correct context.

**The cost: exposure bias.** At generation time the model conditions on its *own* output, including
its mistakes — a distribution it never saw in training.

§7.3 measures it on a seven-token sentence: **mean teacher-forced loss 0.4449, mean free-running loss
12.5447 — a 28× gap.** The free-running model got position 1 wrong and *never recovered*; every
subsequent position was scored against a context the model had corrupted itself. **Training only ever
measures the first number. Users only ever experience the second.**

### 5.4 The causal mask

Teacher forcing requires that position `i` cannot see position `i+1` — otherwise predicting the next
token is trivial, because the answer is in the input.

```
        The  capital  of  France  is
The      ✓      ✗     ✗     ✗     ✗
capital  ✓      ✓     ✗     ✗     ✗
of       ✓      ✓     ✓     ✗     ✗
France   ✓      ✓     ✓     ✓     ✗
is       ✓      ✓     ✓     ✓     ✓
```

Implemented by setting the masked attention scores to `−inf` before the softmax, so they receive
probability zero.

**Without the mask, training loss collapses toward zero and the model is worthless** — it has learned
to copy the answer from its input. §7.3 measures exactly this: **0.2160 masked versus 0.0006
unmasked**, a perplexity of 1.0000 against 1.24.

**The symptom is a suspiciously good loss curve**, and nothing else. There is no error, no warning,
and the model will appear to be the best you have ever trained right up until you generate from it.

### 5.5 Loss and perplexity

Loss at one position is `−log(p_true)` (M3-L05). Sequence loss is the mean over positions, and
**perplexity is `exp(mean loss)`**.

| Mean loss (nats) | Perplexity | Interpretation |
|---|---|---|
| 0.0 | 1.0 | Certain and correct |
| 0.69 | 2.0 | As uncertain as a coin flip |
| 2.30 | 10.0 | Effectively choosing among 10 |
| 4.61 | 100.0 | Choosing among 100 |
| 11.5 | 100,000 | Uniform over a 100k vocabulary — no learning |

**Perplexity only compares across identical tokenizers and identical evaluation data** (M3-L05 §5.6).
A model with a larger vocabulary has lower perplexity partly by construction.

### 5.6 Prefill and decode

| Phase | What happens | Parallel? | Bound by |
|---|---|---|---|
| **Prefill** | Process the whole prompt | Yes, all at once | Compute |
| **Decode** | Generate one token | No, strictly sequential | **Memory bandwidth** |

**Decode is memory-bandwidth-bound, not compute-bound.** Generating one token requires reading every
model parameter from memory to perform relatively little arithmetic. This is why:

- Output tokens cost more than input tokens.
- Batching many requests improves throughput dramatically — the same parameter read serves them all.
- Quantisation speeds up decoding (fewer bytes to read), often more than it reduces compute.

M4-L17 covers this properly, along with the KV cache that makes decode tractable at all.

### 5.7 A worked cost of generation

Generating 500 tokens with a 1,000-token prompt:

```
Prefill: 1 forward pass over 1,000 positions   (parallel)
Decode:  500 forward passes, 1 new position each (sequential)
```

**500 sequential steps.** At 20 ms each that is 10 seconds, and no amount of hardware parallelism
removes the sequential dependency — only faster individual steps, or speculative decoding, help.

**This is why you should ask for concise output**, and why streaming exists: the user sees token 1
after ~20 ms rather than waiting 10 seconds.

### 5.8 Assumptions and limitations

- This describes decoder-only autoregressive models — the dominant design (M4-L11 covers others).
- Diffusion language models and non-autoregressive decoding exist and behave differently.
- Real implementations fuse operations and never materialise the full logits tensor.

---

## 6. Worked example — one forward pass, by hand

A tiny model. **Vocabulary of 6 tokens**, `d_model` = 4.

```
Vocabulary: 0="the"  1="cat"  2="sat"  3="dog"  4="ran"  5="."
```

**Prompt:** `"the cat"` → token IDs `[0, 1]`.

**Step 1 — embed.** Rows 0 and 1 of `E`:

```
E[0] = [ 0.2, -0.1,  0.4,  0.0]      "the"
E[1] = [ 0.5,  0.3, -0.2,  0.1]      "cat"

X = [[ 0.2, -0.1,  0.4,  0.0],
     [ 0.5,  0.3, -0.2,  0.1]]        shape (2, 4)
```

**Step 2 — the blocks.** Assume they produce this final hidden state (M4-L07 onward derives it):

```
H = [[ 0.3,  0.0,  0.5,  0.1],       position 0, having seen "the"
     [ 0.7,  0.4, -0.1,  0.3]]       position 1, having seen "the cat"
```

**Step 3 — LM head.** `W_lm` is `(6, 4)`; `logits = H @ W_lm.T` → `(2, 6)`.

Take **position 1** (the last), whose hidden state is `[0.7, 0.4, -0.1, 0.3]`. With

```
W_lm = [[ 0.1,  0.2, -0.1,  0.0],    "the"
        [ 0.3, -0.2,  0.1,  0.4],    "cat"
        [ 0.8,  0.5,  0.2,  0.1],    "sat"
        [ 0.2, -0.1,  0.3,  0.0],    "dog"
        [ 0.6,  0.4, -0.2,  0.3],    "ran"
        [-0.3,  0.1,  0.4, -0.2]]    "."
```

`logit("sat") = 0.7(0.8) + 0.4(0.5) + (−0.1)(0.2) + 0.3(0.1) = 0.56 + 0.20 − 0.02 + 0.03 = **0.77**`

All six:

| Token | Logit | Probability |
|---|---|---|
| the | 0.1600 | 0.1391 |
| cat | 0.2400 | 0.1507 |
| **sat** | **0.7700** | **0.2561** |
| dog | 0.0700 | 0.1272 |
| **ran** | **0.6900** | **0.2364** |
| . | −0.2700 | 0.0905 |

Softmax over six logits; they sum to exactly 1.0000. *(All values verified in §7.3.)*

**Step 4 — read the result.** `sat` (0.2561) and `ran` (0.2364) are nearly tied — the model finds both
plausible after "the cat", which is linguistically correct. `dog` is lowest of the content words,
which is also right: "the cat dog" is not English.

**Step 5 — loss.** If the true next token is `sat`:

```
loss = −ln(0.2561) = 1.3623 nats
perplexity = exp(1.3623) = 3.91
```

**Interpretation:** the model is about as uncertain as choosing uniformly among **4** of its 6 tokens.
For a model this small, on two tokens of context, that is respectable.

**If the true token had been `.`:** `loss = −ln(0.0905) = 2.4023`, **76% higher**. Cross-entropy
punishes confident wrongness, exactly as M3-L05 §5.4 describes.

**Step 6 — note what was discarded.** Position 0 also produced a full distribution. In generation we
throw it away. In training it is a sixth of the learning signal from this example, free.

---

## 7. Practical activity

**File:** [`labs/m4/l05_next_token.py`](../../labs/m4/l05_next_token.py)

**No API key, no network.** A complete miniature language model, trained in the script.

```bash
source .venv/bin/activate
python labs/m4/l05_next_token.py
```

Reproduces §6 exactly, trains a small autoregressive model and tracks loss and perplexity, removes the
causal mask to show the loss collapse, demonstrates teacher forcing versus free running, and measures
the prefill/decode asymmetry.

### 7.2 Expected output

`[EXECUTED]` on Python 3.12.3, NumPy 2.5.3, 2026-09-08.

```text

============================================================================
1. THE WORKED EXAMPLE, VERIFIED  (6-token vocabulary, d_model 4)
============================================================================
  hidden state at the last position: [ 0.7  0.4 -0.1  0.3]

  logit('sat') = 0.7(0.8) + 0.4(0.5) + (-0.1)(0.2) + 0.3(0.1)
               = 0.56 + 0.20 + -0.02 + 0.03 = 0.7700

  token       logit   probability
  the        0.1600        0.1391
  cat        0.2400        0.1507
  sat        0.7700        0.2561  <-
  dog        0.0700        0.1272
  ran        0.6900        0.2364  <-
  .         -0.2700        0.0905
  sum                      1.0000

  if the true next token is 'sat':
    loss       = -ln(0.2561) = 1.3623 nats
    perplexity = exp(1.3623)     = 3.91

  if the true next token is '.':
    loss       = -ln(0.0905) = 2.4023 nats
    perplexity = exp(2.4023)     = 11.05

  The wrong-but-plausible token costs 76% more loss.
  Cross-entropy punishes confident wrongness (M3-L05).

============================================================================
2. A COMPLETE MINIATURE LANGUAGE MODEL
============================================================================
  vocabulary : 15 tokens -> ['.', 'a', 'bird', 'cat', 'dog', 'flew', 'mat', 'on', 'over', 'park', 'ran', 'sat', 'the', 'to', 'tree']
  corpus     : 16,800 tokens
  d_model    : 24,  context: 6

  loss at initialisation should be about ln(V) = ln(15) = 2.7081
  (a uniform distribution over the vocabulary -- no knowledge at all)
  training windows: 16,794

  first window, showing the shift:
    input : ['the', 'cat', 'sat', 'on', 'the', 'mat']
    target: ['cat', 'sat', 'on', 'the', 'mat', '.']
    Target at position i is the input at position i+1. No labels exist;
    the text IS the supervision (M1-L07).

  training WITH the causal mask (the correct set-up):
        step      loss   perplexity
           0    2.7101        15.03
         100    0.5899         1.80
         300    0.3634         1.44
         600    0.2107         1.23
        1200    0.2160         1.24

    initial loss 2.7101 vs ln(V) = 2.7081  (difference 0.0020)
    Starting at ln(V) confirms the model begins with no knowledge.

============================================================================
3. REMOVING THE CAUSAL MASK  (the loss collapse)
============================================================================
      step    WITH mask   WITHOUT mask     ratio
         0       2.7101         2.7111      1.00x
       100       0.5899         0.5310      0.90x
       300       0.3634         0.1812      0.50x
       600       0.2107         0.0033      0.02x
      1200       0.2160         0.0006      0.00x

  final loss   with mask: 0.2160   (perplexity 1.24)
  final loss without mask: 0.0006   (perplexity 1.00)

  The unmasked model reaches a LOWER loss -- and it is worthless.
  Position i can attend to position i+1, which holds the answer, so it
  learns to copy rather than to predict. The only symptom is a
  suspiciously good loss curve.

  PROOF the mask works: change only the last input token, then check
  whether earlier positions' logits moved.
    earlier positions identical (masked)  : True
    earlier positions identical (unmasked): False
  With the mask, the past cannot see the future. Without it, it can.

============================================================================
4. GENERATION: EVERY POSITION PREDICTS, BUT WE KEEP ONE
============================================================================
  prompt: ['the', 'cat']   -> the model produced 2 distributions, one per position

    after 'the'            -> tree (0.351), park (0.273), mat (0.142)  (discarded)
    after 'the cat'        -> sat (0.577), ran (0.422), to (0.001)  <- KEPT

  In generation we discard all but the last. In TRAINING every one of
  them is a learning signal, which is why training is so much more
  efficient per forward pass.

  greedy generation from 'the cat':
    'the cat sat on the mat . the dog ran'

  sampled at temperature 0.8, three runs:
    'the cat sat on the mat . the dog ran'
    'the cat sat on the mat . the dog ran'
    'the cat ran to the mat . the dog sat'

============================================================================
5. TEACHER FORCING vs FREE RUNNING  (exposure bias)
============================================================================
  position  true token    teacher-forced   free-running    model said
  1         cat                   2.1123         2.1123          tree
  2         sat                   0.5506        12.1739             .
  3         on                    0.0004        11.2784           the
  4         the                   0.0000        25.4517           cat
  5         mat                   0.0062        15.4083           sat
  6         .                     0.0000         8.8438            on

  mean loss  teacher-forced: 0.4449
  mean loss  free-running   : 12.5447
  ratio                     : 28.19x

  Training only ever measures the teacher-forced number. Generation
  always experiences the free-running one. That gap is exposure bias,
  and it is why an early mistake propagates through a long response.

============================================================================
6. PREFILL vs DECODE  (the asymmetry that governs latency and price)
============================================================================
  one prefill pass over 6 positions : 0.033 ms

    tokens generated   total time   per token   vs 1 prefill
                   1        0.05ms      0.047ms           1.4x
                  10        0.38ms      0.038ms          11.5x
                  50        1.81ms      0.036ms          54.8x
                 100        3.61ms      0.036ms         109.2x

  Generating N tokens costs N sequential forward passes. The prompt,
  however long, costs ONE. That is why:
    * output tokens are priced higher than input tokens,
    * latency scales with output length, not prompt length,
    * streaming exists (the user sees token 1 immediately),
    * and no amount of parallel hardware makes a single generation
      faster -- the dependency is inherent, not an implementation
      limitation.

  Scaled to a realistic request -- 1,000-token prompt, 500 output
  tokens, at 20 ms per decode step:
    prefill : 1 pass          ~ 0.02 s
    decode  : 500 passes      ~ 10.0 s
    -> 500x the prompt's cost, from 500 tokens of output.

Done.
```

### 7.3 Reading the result

**Section 1 verifies §6 to four decimal places**, including that the probabilities sum to exactly
1.0000 and that the wrong-but-plausible token costs **76% more loss**.

**Section 2 builds a working language model** — embeddings, positional encoding, attention, an MLP,
residual connections and an LM head, all in NumPy, trained by hand-derived backpropagation.

The initialisation check is the one to notice: **loss starts at 2.7101 against a predicted
`ln(15) = 2.7081`** — a difference of 0.0020. A model that begins at `ln(vocab)` is one assigning
uniform probability, i.e. knowing nothing. **If your loss starts anywhere else, something is wrong
before training has begun**, and this is the cheapest sanity check available.

By step 1,200 the loss is 0.2160 (perplexity 1.24) and the model has learned the corpus's grammar —
§4's greedy generation produces `'the cat sat on the mat . the dog ran'`, which is valid in the toy
language and was never seen as a contiguous string.

**Section 3 is the causal-mask result, and the first version of this lab failed to produce it.**

That failure is worth recording. The original script trained only the embeddings, MLP and LM head,
leaving `Wq/Wk/Wv/Wo` at their random initialisation — and measured a difference of **5%** between
masked and unmasked training. The conclusion looked like "the mask barely matters", which is wrong.
**The model could not exploit the future because its attention was never trained to.** With full
backpropagation through the attention block:

| Step | With mask | Without mask | Ratio |
|---|---|---|---|
| 0 | 2.7101 | 2.7111 | 1.00× |
| 100 | 0.5899 | 0.5310 | 0.90× |
| 300 | 0.3634 | 0.1812 | 0.50× |
| 600 | 0.2107 | 0.0033 | **0.02×** |
| **1,200** | **0.2160** | **0.0006** | **0.003×** |

**Final perplexity: 1.24 masked, 1.0000 unmasked.** A perplexity of exactly 1 means the model is
*certain and correct on every token* — which is impossible for genuine prediction and is a
mathematical statement that it is reading the answer off its own input.

**The lesson within the lesson:** a demonstration that shows no effect may mean the effect is absent,
or that the experiment could not detect it. Here it was the second, and the difference between those
two conclusions was 360× in the measured number.

The structural probe confirms the mechanism directly: change only the **last** input token, and with
the mask, every earlier position's logits are **bit-identical**; without it, they change. The past
cannot see the future — that, and only that, is what the mask does.

**Section 4 makes the "predicts at every position" claim concrete.** A two-token prompt yields **two**
distributions: after `'the'` the model predicts `tree (0.351), park (0.273), mat (0.142)`; after
`'the cat'` it predicts `sat (0.577), ran (0.422)`. **Generation discards the first entirely.**
Training uses both. That is why a training step extracts far more signal per forward pass than a
generation step does.

**Section 5 quantifies exposure bias, and the shape of the failure is as instructive as the number.**

| Position | True token | Teacher-forced loss | Free-running loss | Model said |
|---|---|---|---|---|
| 1 | cat | 2.1123 | 2.1123 | **tree** |
| 2 | sat | 0.5506 | **12.1739** | . |
| 3 | on | 0.0004 | **11.2784** | the |
| 4 | the | 0.0000 | **25.4517** | cat |
| 5 | mat | 0.0062 | **15.4083** | sat |

**Mean 0.4449 teacher-forced against 12.5447 free-running — 28×.**

Position 1 is identical in both, because both had the same (true) context. From position 2 onward
they diverge completely: the model said `tree`, then conditioned on its own `tree`, and every
subsequent prediction was made from a context no training example ever contained. **One wrong token
destroyed the rest of the sequence.**

This is the mechanism behind long responses that start well and degrade, and behind the general rule
that a model's first sentence disproportionately determines its last.

**Section 6 measures the prefill/decode asymmetry.** One prefill pass costs 0.033 ms; generating 100
tokens costs 3.61 ms — **109× one prefill**, and the per-token cost stays flat at ~0.036 ms because
each token is its own sequential pass.

Scaled up: a 1,000-token prompt is **one** forward pass; 500 output tokens are **500** sequential ones.
At 20 ms each that is 10 seconds of generation against 0.02 s of prompt processing. **No quantity of
parallel hardware changes this** — token 2 cannot begin until token 1 exists. Faster individual steps
help; more GPUs on one request do not. This single fact explains output pricing, streaming, and why
"ask for shorter answers" is the most reliable latency optimisation available.

---

## 8. Common mistakes and troubleshooting

1. **Forgetting to shift labels.** The model learns to copy its input; loss looks wonderful.
2. **Omitting the causal mask.** Same symptom, same cause: the answer is visible.
3. **Comparing perplexity across tokenizers.**
4. **Expecting generation to parallelise.** It cannot; the dependency is inherent.
5. **Materialising full logits for a long sequence.** 800 MB for one pass at 2k tokens.
6. **Assuming input and output tokens cost the same.** Decode is bandwidth-bound.
7. **Ignoring exposure bias** when a long generation degrades.
8. **Computing loss over padding positions.** Mask them.

| Symptom | Likely cause | Fix |
|---|---|---|
| Training loss near zero immediately | No causal mask, or unshifted labels | Check both; loss should start near `ln(V)` |
| Loss starts far above `ln(vocab)` | Bad initialisation | Check init scale (M3-L10 §5.7) |
| Generation degrades as it lengthens | Exposure bias; repetition | Sampling settings (M4-L14) |
| Generation much slower than prompt processing | Decode is sequential | Expected; stream; ask for concise output |
| Out of memory computing loss | Full logits tensor | Compute logits only where needed |
| Perplexity differs from a paper's | Different tokenizer or data | Not comparable |
| Model repeats one phrase forever | Greedy decoding | Sample; use top-p (M4-L14) |

---

## 9. Security, privacy, reliability, cost

- **Privacy.** Language models can memorise and reproduce rare training strings verbatim — including
  secrets that were in the corpus. Never train on unsanitised logs or credential-bearing text, and
  treat any model trained on internal data as potentially disclosing it (M10-L12).
- **Cost.** Output tokens dominate latency and are priced higher. The cheapest reliable optimisation
  is asking for less output.
- **Cost.** Prefill is roughly linear in prompt length; decode is linear in output length but with a
  much larger constant. Model both separately.
- **Reliability.** Generation length is not known in advance. Always set a maximum-token limit, or a
  runaway generation will consume budget and time (M4-L15).
- **Reliability.** Because each token conditions on the previous ones, one bad early token can derail
  an entire response. Validate outputs; do not assume a good start implies a good finish.

---

## 10. Exercises

### Exercise 1 — Beginner (~25 min)

1. Write out every shape in the pipeline for a 12-token prompt, `d_model` 768, vocabulary 50,000.
2. For `"the cat sat"`, write the input/target pairs used in training.
3. A model assigns 0.15 to the true token. Compute the loss and the perplexity.
4. Why is generating 500 tokens slower than processing a 500-token prompt?
5. What happens to training loss if the causal mask is omitted? Why?

### Exercise 2 — Intermediate (~40 min)

1. Run the lab and reproduce §6's logit for `sat` by hand.
2. Train the lab's model and plot loss and perplexity. State the loss you would expect at
   initialisation and check it.
3. Remove the causal mask, retrain, and report the loss. Explain the number.
4. Implement greedy decoding and generate 20 tokens. Comment on what you see.
5. Measure the time for prefill on 200 tokens versus decode of 200 tokens. Report the ratio.

### Exercise 3 — Challenge (~45 min)

1. Implement the full forward pass with an explicit causal mask and verify with an assertion that
   position `i`'s output is unchanged when tokens after `i` are altered.
2. Measure exposure bias: compare teacher-forced loss with free-running loss over 50 generated
   tokens, and plot the divergence.
3. Compute the memory of the full logits tensor for `T` in {128, 1024, 8192} at vocabulary 100k in
   float32 and float16. State when you must avoid materialising it.
4. Implement weight tying and report the parameter reduction and any loss difference.
5. Implement a repetition penalty and measure its effect on the fraction of repeated 4-grams.
6. Show empirically that shuffling the tokens *after* position `i` leaves position `i`'s logits
   bit-identical when masking is correct, and changes them when it is not.

---

## 11. Quiz

*(Answers: [`answer-keys/module-04-answers.md`](../../answer-keys/module-04-answers.md#m4-l05).)*

**Q1.** Given a 5-token prompt, how many probability distributions does the model produce?

- A. Five, one predicting the next token at each position.
- B. One, for the position after the final token.
- C. Four, since the first token has no preceding context.
- D. Six, including one for the end-of-sequence marker.

**Q2.** In training, what is the target at position `i`?

- A. The input token at position `i`, reconstructed exactly.
- B. A separately labelled class provided by human annotators.
- C. The input token at position `i+1`, the labels shifted left.
- D. The average of all tokens appearing after position `i`.

**Q3.** What does the causal mask prevent?

- A. Positions from attending to tokens that come after them.
- B. Padding tokens from contributing to the attention scores.
- C. The model from producing the same token twice in a row.
- D. Gradients from flowing backwards through earlier layers.

**Q4.** You omit the causal mask during training. What do you observe?

- A. The loss rises sharply and training fails to converge at all.
- B. An exception, since the attention shapes no longer align.
- C. No change; the mask affects only generation, not training.
- D. The loss collapses toward zero, as the answer is visible.

**Q5.** Why is generation sequential when training is parallel?

- A. Generation uses a different model architecture internally.
- B. Each generated token must exist before the next conditions on it.
- C. Memory limits prevent processing several positions at once.
- D. The causal mask is only applied during the generation phase.

**Q6.** A model's mean loss is 2.30 nats. Its perplexity is about:

- A. 2.30  B. 0.10  C. 10.0  D. 230

**Q7.** Decode is bound primarily by:

- A. Arithmetic throughput on the matrix multiplications.
- B. Memory bandwidth, since all parameters are read per token.
- C. Network latency between the client and the server.
- D. The size of the vocabulary in the final projection.

**Q8.** What is exposure bias?

- A. Generation conditions on its own output, unlike in training.
- B. Overfitting caused by repeatedly evaluating on a test set.
- C. Longer prompts receiving disproportionate attention weight.
- D. Training data appearing verbatim in the model's output.

**Q9.** At `T`=2,000 and a 100k vocabulary, the float32 logits tensor is about:

- A. 8 MB  B. 800 MB  C. 200 KB  D. 80 GB

**Q10.** Why can perplexity not be compared between two models?

- A. It can be compared freely; it is a standardised benchmark.
- B. Perplexity depends on model size and is therefore unfair.
- C. Only if the tokenizer and evaluation data are identical.
- D. Because perplexity is measured in nats rather than bits.

**Q11.** *(Written, rubric-graded.)* In under 100 words, explain to a colleague why their request to
"just parallelise the generation across 8 GPUs to make it 8× faster" will not work as stated, and what
would actually help.

---

## 12. Revision notes

- **The pipeline:** text → tokens → embeddings → +position → N blocks → last hidden state → LM head →
  logits → softmax → sample. **Shape is `(T, d_model)` throughout the stack.**
- **The model predicts at every position**, not just the last. Generation discards all but the last;
  training uses them all — which is why training is efficient per unit of compute.
- **Targets are inputs shifted left by one.** `inputs = tokens[:-1]`, `targets = tokens[1:]`. No
  labels required — this is self-supervision.
- **Teacher forcing** feeds true previous tokens; the cost is **exposure bias**. Measured: mean loss
  **0.4449 teacher-forced vs 12.5447 free-running — 28×**. One wrong token at position 1 destroyed
  every position after it.
- **The causal mask** stops a position seeing the future. Measured: **loss 0.2160 masked vs 0.0006
  unmasked, perplexity 1.24 vs 1.0000.** A perplexity of exactly 1 is mathematically impossible for
  genuine prediction. **A suspiciously good loss curve is the only symptom.**
- **Loss should start at `ln(vocab)`.** Measured 2.7101 against a predicted 2.7081 — the cheapest
  sanity check there is.
- **Loss = `−log(p_true)`; perplexity = `exp(mean loss)`.** Comparable only across identical
  tokenizers and data.
- **Prefill is parallel and compute-bound. Decode is sequential and memory-bandwidth-bound.** This is
  the most important performance fact about LLMs.
- **500 output tokens = 500 sequential forward passes.** No hardware removes that dependency.
- Logits are huge: `(2000, 100000)` float32 = **800 MB** for one pass.
- **Always set a maximum output length.**

---

## 13. Completion checklist

- [ ] I can write every shape in the pipeline from memory.
- [ ] I reproduced §6's logit for `sat` by hand.
- [ ] I can explain teacher forcing and exposure bias.
- [ ] I saw the loss collapse to 0.0006 (perplexity 1.0000) with the mask removed.
- [ ] I checked that loss starts at ln(vocab).
- [ ] I can compute loss and perplexity from a probability.
- [ ] I can explain prefill versus decode and why output costs more.
- [ ] I scored 8/11 on the quiz.

---

## 14. References

- Vaswani et al. (2017), *Attention Is All You Need*. <https://arxiv.org/abs/1706.03762> `[UNVERIFIED]`
- Radford et al. (2018), *Improving Language Understanding by Generative Pre-Training* (GPT).
  `[UNVERIFIED]`
- Karpathy, *Let's build GPT: from scratch, in code, spelled out*.
  <https://karpathy.ai/zero-to-hero.html> `[UNVERIFIED]`
- Bengio et al. (2015), *Scheduled Sampling* (exposure bias).
  <https://arxiv.org/abs/1506.03099> `[UNVERIFIED]`

---

## 15. Next lesson

→ [M4-L06 — Context Windows, Output Limits and Truncation](M4-L06-context-windows.md)

You can trace one forward pass. Next: the limit on how much can go into it, what happens at the
boundary, and why "it worked in testing" is not evidence that it will fit.
