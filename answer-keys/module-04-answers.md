# Module 4 — Answer Key

**Do not read this before attempting the questions.** Every answer carries a reason, and for multiple
choice, a reason each distractor fails.

> **Module 4 onward, quiz options are written to uniform length with a balanced answer distribution.**
> M1–M3 lesson quizzes were formative self-checks whose correct option was longer and more explanatory
> than the distractors; that is fixed from here. If you are revising M1–M3, treat those quizzes as
> prompts and the module assessments as the graded instruments.

| Lesson | Jump to |
|---|---|
| M4-L01 Foundation Models | [↓](#m4-l01) |
| M4-L02 Modalities | [↓](#m4-l02) |
| M4-L03 Tokens and Tokenizers | [↓](#m4-l03) |
| M4-L04 Embeddings | [↓](#m4-l04) |
| M4-L05 Next-Token Prediction | [↓](#m4-l05) |
| M4-L06 Context Windows | [↓](#m4-l06) |
| M4-L07 Attention | [↓](#m4-l07) |
| M4-L08 QKV Worked by Hand | [↓](#m4-l08) |
| M4-L09 Positional Information | [↓](#m4-l09) |
| M4-L10 Transformer Block | [↓](#m4-l10) |
| M4-L11 Architectures | [↓](#m4-l11) |
| M4-L12 Pretraining and Post-Training | [↓](#m4-l12) |
| M4-L13 Preference Optimization | [↓](#m4-l13) |
| M4-L14 Decoding | [↓](#m4-l14) |
| M4-L15 Stop Conditions | [↓](#m4-l15) |
| M4-L16 Knowledge vs Context | [↓](#m4-l16) |
| M4-L17 Serving Internals | [↓](#m4-l17) |
| M4-L18 Hosted vs Local | [↓](#m4-l18) |

---

<a id="m4-l01"></a>
## M4-L01 — Foundation Models and What "Generative" Really Means

**Answers: C · D · A · B · D · B · C · A · D · C**

| Q | Ans | Why, and why the distractors fail |
|---|---|---|
| 1 | **C** | Adaptability to tasks it was never trained for is the defining property. **A** — size alone does not make a foundation model; a very large single-task model is just a large model. **B** — most frontier models are closed, and most "open" ones are open weights, not open source (§5.7). **D** — larger models are generally *slower* per token. |
| 2 | **D** | It learns a distribution and samples from it. **A** — "creative" is a description of the output, not a mechanism, and the same mechanism produces boring output too. **B** — depth is unrelated; a deep classifier is still discriminative. **C** — data volume is unrelated to the kind of model. |
| 3 | **A** | The label is the next token, taken from the data itself, so unlabelled text at internet scale becomes training data with no annotation cost. **B** — self-supervised pretraining takes *more* steps, not fewer. **C** — it needs more parameters, not fewer. **D** — it depends on accelerators more heavily, not less. |
| 4 | **B** | A base model continues text plausibly; in its training data, questions are often followed by more questions. Answering rather than continuing is what post-training adds (§5.3, M4-L12). **A** — temperature changes variety, not whether the model answers. **C** — the model is working correctly. **D** — a five-word prompt exceeds nothing. |
| 5 | **D** | Prompting → RAG → tools → fine-tuning, cheapest and fastest-feedback first. **A** is exactly backwards and is the expensive mistake §5.4 warns about. **B** puts RAG before prompting, doing work before establishing it is needed. **C** — the order changes cost by orders of magnitude. |
| 6 | **B** | Behaviour, format and tone. **A** is the most common misconception: fine-tuning is poor at instilling facts, and facts belong in retrieval (M13-L02). **C** — fine-tuning does not reduce latency; distillation or a smaller model would. **D** — tool use is a prompting and scaffolding concern. |
| 7 | **C** | It generates text matching the *pattern* of a citation. It holds no records, so there is nothing to look up and nothing to fail. **A** — a plain model has no retrieval index at all. **B** — the citation need never have existed anywhere. **D** — this happens at temperature 0 too. |
| 8 | **A** | Weights downloadable, often under a restrictive custom licence, with training data usually undisclosed. **B**, **C** and **D** are each a specific thing people wrongly assume "open" implies — and each is a legal exposure if assumed (§5.7, M10-L14). |
| 9 | **D** | Very little about *your* task. Benchmarks vary by model, version, prompt and task. **A** is the assumption that causes disappointing pilots. **B** ignores that a benchmark measures one thing. **C** — no benchmark establishes production readiness. |
| 10 | **C** | Four of the five failures produce plausible-looking output — the invented category is the exception, being catchable by validating against the allowed set. **A** — none crash. **B** — they occur at any temperature. **D** — a larger model reduces frequency, not the failure class. |

**Q11 rubric (4 marks).** One mark each for: describing it as a system trained on a very large amount
of text to continue text plausibly; noting it can be pointed at many different jobs with written
instructions rather than rebuilt for each; naming one thing it should not be used for (looking up
facts, arithmetic, anything needing an audit trail); and doing all of the above without the banned
words. Deduct a mark for any answer implying the system "knows" or "understands" things, since that is
the framing the exercise exists to break.

---

<a id="m4-l02"></a>
## M4-L02 — Modalities: Text, Image, Audio, Video and Multimodal

**Answers: A · B · D · C · B · D · A · B · D · A**

| Q | Ans | Why, and why the distractors fail |
|---|---|---|
| 1 | **A** | Every modality becomes a sequence of vectors — one per token, patch or frame. **B** — a single pooled vector is what an *encoder* might output, not what a transformer consumes. **C** — a 2-D array is an intermediate (a spectrogram, an image), not the input format. **D** — transformers do not operate on characters; text is tokenised first (M4-L03). |
| 2 | **B** | `(224/14)² = 16² = **256**`. **A** (16) is the grid width, not the count — squaring is the step people miss. **C** (196) is `(224/16)²`, the answer for a 16-pixel patch. **D** is arbitrary. |
| 3 | **D** | Quadruples. Patch count is `(w/p)×(h/p)`, so halving `p` doubles *both* factors. Measured in §7.3: 256 → 1,024. **A** and **C** assume a linear relationship, which is the expensive mistake. **B** ignores that patch size is in the denominator. |
| 4 | **C** | Converted to a spectrogram and sliced along time — 32,000 samples became 198 frames in the lab, **162× fewer** sequence positions. **A** is computationally impossible at 16 kHz. **B** — compressed bytes carry no usable structure. **D** — models *can* process audio natively; ASR is a choice, not a requirement (§5.3). |
| 5 | **B** | Each sampled frame costs a full image's worth of tokens. Measured: 1 minute at 30 fps ≈ **1,350,000 tokens**. **A** — file size on disk is unrelated to token cost. **C** — decoding is cheap and happens before the model. **D** — the cost is in the sequence length, not the parameters. |
| 6 | **D** | It maps vision-encoder vectors into the language model's embedding space, so both modalities become one sequence. **A** — resizing happens before the encoder. **B** — the projection changes dimensionality, not sequence length. **C** — these models emit text, not pixels. |
| 7 | **A** | Diffusion starts from noise and denoises the whole image over ~20–50 steps. **B** — parameter count is not the distinction. **C** describes autoregressive text generation, which is exactly what diffusion is not. **D** — prompts, guidance scale and negative prompts all control it. |
| 8 | **B** | OCR to text: 39% of the tokens *and* inspectable at each step. **A** — layout handling is real but does not justify 2.6× the cost when OCR is clean. **C** — the measured gap is 61% of tokens plus a large debuggability difference. **D** — doubles the cost to solve a problem a confidence threshold solves (§7.3's hybrid). |
| 9 | **D** | You can read the intermediate text and immediately tell whether OCR failed or the model misread correct text. **A** and **B** are true but irrelevant — they concern the OCR engine's own diagnostics, not the extraction failure. **C** is an unsupported generalisation. |
| 10 | **A** | Prompt injection: text extracted from an image is untrusted input and must be treated exactly like text from a user (M10-L06). **B** and **C** are false. **D** is dangerously false — reading text in images is a core capability. |

**Q11 rubric (4 marks).** One mark each for: stating that patch count — and therefore cost — scales
with the *square* of resolution; giving a concrete multiplier (a 2048×2048 scan is 64× a 224×224
thumbnail); proposing a specific alternative (downscale to what the task needs, or OCR-then-text);
and naming what that alternative discards. An answer that only says "it is expensive" without the
quadratic relationship scores 1.

---

<a id="m4-l03"></a>
## M4-L03 — Tokens, Tokenizers, Vocabularies and Token IDs

**Answers: C · A · D · A · B · C · D · A · B · D**

| Q | Ans | Why, and why the distractors fail |
|---|---|---|
| 1 | **C** | Character-level sequences are ~5× longer, and attention cost is **quadratic** in length (M4-L07), so a 5× longer sequence is ~25× the attention compute. **A** — character models have *no* out-of-vocabulary problem at all; that is word-level models. **B** is backwards: subwords *hide* spelling, which is what causes §5.4's failures. **D** — characters embed perfectly well; the objection is cost, not possibility. |
| 2 | **A** | The most frequent adjacent pair in the *current* corpus state — which changes after every merge, as §7.3's trace shows. **B** describes only the tie-break. **C** and **D** are inventions; frequency is the entire criterion. |
| 3 | **D** | ~4 chars/token is the usual rule of thumb — **but note §5.3: it is conservative and dated.** The lab measured **5.54** for modern English prose with `cl100k_base`, so the rule overestimates cost by ~39%. The question asks for the rule; the lesson asks you to distrust it. **A** and **B** are off by 4–5×; **C** inverts the direction. |
| 4 | **A** | Non-Latin scripts. Measured: Devanagari **1.00** chars/token and Japanese **0.97** — 5.5× the cost of prose per character, and 6.5× for the same *sentence*. **B** is the trap: technical English measured **5.56**, statistically identical to ordinary prose (5.54), because a 100k vocabulary contains the jargon. **C** is the baseline. **D** — occasional proper nouns barely move the ratio. |
| 5 | **B** | It receives opaque integer IDs. `strawberry` is `[496, 675, 15717]`; the letters are simply not present in the input, so no computation over that input could count them. **A** — the word is common; rarity is not the issue. **C** — counting to three is not the hard part. **D** — the failure persists at temperature 0. |
| 6 | **C** | Different tokens with different IDs: measured **1820** vs **279**. Not variants — two unrelated integers with independently learned embeddings. **A** — tokenizers deliberately preserve whitespace. **B** — positional encodings are separate (M4-L09) and do not distinguish these. **D** is false; leading-space tokens are the common case. |
| 7 | **D** | Token boundaries. Measured: **21 of 87 byte positions (24%)** in the lesson's sample produce invalid UTF-8, and with `errors="replace"` the corruption is **silent**. **A** and **B** are exactly the failure. **C** is safer than bytes but can still split a token, and does not guarantee the model sees what you intended. |
| 8 | **A** | Unknown without measuring. Tokenizer efficiency changes the token count, so cost-per-document is price × efficiency, not price alone. **C** is the assumption that produces wrong procurement decisions. **B** is unfounded. **D** — tokenizers are emphatically not standardised (§5.6). |
| 9 | **B** | A user who can emit a role-marker token can forge a conversation turn, injecting an apparent system or assistant message (M10-L06). **A** is true but trivial next to the security issue. **C** — special tokens are billed identically. **D** — the danger is that it *succeeds*, not that it errors. |
| 10 | **D** | Retrieved context: 1,900 of 3,655 input tokens, **52%**. **A** is the second largest at 22% and the easiest to fix by caching (M5-L16) — a good answer to a different question. **B** is 2%. **C** is 25%, close but not the largest. |

**Q11 rubric (5 marks).** One mark each for: naming tokens as the unit of billing; explaining that
English-centric tokenizers encode Devanagari at roughly one token per character while English averages
5.5; giving the measured multiplier (**6.5×** for the same sentence); noting the knock-on effects
beyond cost (less history fits the context window, higher latency); and offering at least two concrete
options — measure and set per-language limits, budget per language, shorten prompts for affected
languages, or evaluate a model with a more balanced tokenizer. Deduct a mark for any answer implying
the difference is a property of the *language* rather than of the *tokenizer's training data*.

---

<a id="m4-l04"></a>
## M4-L04 — Embeddings and Contextual Representations

**Answers: A · C · A · B · D · D · C · C · C · D**

| Q | Ans | Why, and why the distractors fail |
|---|---|---|
| 1 | **A** | It retrieves one row by index: `E[675]`. §7.3 confirms `one_hot(675) @ E == E[675]` — identical results, **25.6M multiplications versus zero**. **B** — the ID is an index, never a multiplicand. **C** — no network runs; that is what the *layers* do afterwards. **D** — hashing is a different technique (the hashing trick) and is not how transformers embed. |
| 2 | **C** | One fixed vector per word, averaging all senses into a point representing neither. Measured: static `bank` scores **0.7320** to both `shore` and `account`, a difference of exactly 0. **A** — adding dimensions does not help; the averaging happens regardless. **B** — the tokenizer is deterministic and emits the same ID. **D** — corpus size is irrelevant to the structural limitation. |
| 3 | **A** | Each layer updates every token's vector using the other tokens (M4-L07). **B** — tokenization is context-free; the ID is identical. **C** — there is one table, and word senses are not enumerated anywhere. **D** — positional encodings (M4-L09) distinguish *positions*, not *meanings*; identical tokens at the same position in different sentences would still collide. |
| 4 | **B** | `100,000 × 4,096 = 409,600,000` — **409.6M parameters, 1.53 GB in float32**. **A** and **C** are the two factors, not the product. **D** is arbitrary. |
| 5 | **D** | Individual dimensions generally mean nothing in isolation; only relationships between vectors are interpretable. **A** is the intuitive and wrong answer — the toy in §6 assigns axis meanings *only* so the arithmetic is legible, and says so. **B** and **C** describe PCA-like decompositions, not learned embeddings. |
| 6 | **D** | Every vector is dragged toward the padding embedding, silently. Measured: two **unrelated** sentences went from −0.0531 masked to **0.9721** unmasked. **A** — shapes align fine; that is the problem. **C** is the trap: a *zero* pad vector is harmless under cosine (measured error 0.0000), but a real pad token is a learned, non-zero row. **B** — all vectors in the batch are affected. |
| 7 | **C** | Anisotropy. Measured: unrelated pairs averaged **0.7787** with **13.4%** above 0.8. **A** — this is normal behaviour for language-model embeddings, not a training defect. **B** — cosine is appropriate; the *absolute scale* is what is uninformative. **D** — cosine normalises internally, so unnormalised inputs give the same answer. |
| 8 | **C** | Re-encode every stored vector. The two spaces are unrelated coordinate systems, so old and new vectors cannot be compared even when the dimension matches. **A** is the assumption that breaks production search silently. **B** — no rescaling relates two independently learned spaces. **D** leaves a corpus split across two incompatible spaces, which is worse than either alone. |
| 9 | **C** | Embeddings capture association; negation is barely represented, so the two sentences share almost all their content and score highly (M7-L09). **A** — more negation data helps marginally; the limitation is representational. **B** — order is captured to a degree by contextual models. **D** — "not" is not removed by a subword tokenizer. |
| 10 | **D** | Sensitive. Inversion attacks reconstruct a recognisable amount of the source text, so an embedding store needs the same access control, retention and deletion as the text itself (M10-L11). **A**, **B** and **C** are the assumptions that cause the compliance failure — particularly the belief that a deletion request is satisfied without deleting the vectors. |

**Q11 rubric (4 marks).** One mark each for: identifying that the new model produces vectors in a
different, incomparable space; explaining that the *stored* index still holds old-model vectors, so
queries and documents are now being compared across two coordinate systems; noting the symptom is
degraded relevance with **no error raised**; and stating what should have happened — re-encode the
entire corpus, ideally building the new index alongside the old and cutting over after an offline
relevance comparison (M3-L14, M7-L16). Deduct a mark for any answer suggesting the vectors could be
converted or rescaled.

---

<a id="m4-l05"></a>
## M4-L05 — Language Modelling: Next-Token Prediction End to End

**Answers: A · C · A · D · B · C · B · A · B · C**

| Q | Ans | Why, and why the distractors fail |
|---|---|---|
| 1 | **A** | Five — one distribution per position, each predicting that position's next token. §7.3 shows both distributions for a two-token prompt. **B** is what *generation* uses, discarding the rest; the model still computed them. **C** — position 0 predicts position 1 perfectly well. **D** — no extra position is created. |
| 2 | **C** | The input token at `i+1`: `targets = tokens[1:]`. **A** is the reconstruction objective of an autoencoder, and here would make the task trivial. **B** — no annotator is involved; this is self-supervision (M1-L07). **D** is not an operation any language model performs. |
| 3 | **A** | Positions attending to later positions. Verified structurally in §7.3: with the mask, changing the last input token leaves earlier logits **bit-identical**. **B** is a *padding* mask — a different mask serving a different purpose. **C** — repetition is a decoding concern (M4-L14). **D** — gradients flow normally. |
| 4 | **D** | The loss collapses. Measured: **0.0006 against 0.2160 masked**, perplexity **1.0000** — mathematically impossible for genuine prediction. **A** is the intuitive guess and is backwards. **B** — shapes are unaffected. **C** is the dangerous belief: the mask matters *most* in training, because that is where the answer is present in the input. |
| 5 | **B** | Token `n` must exist before it can be conditioned on to produce token `n+1`. **A** — the architecture is identical. **C** — memory is not the constraint; the data dependency is. **D** — the mask is applied in both phases. |
| 6 | **C** | `exp(2.30) ≈ 10.0` — as uncertain as choosing uniformly among 10 options. **A** confuses loss with perplexity. **B** is `exp(−2.30)`. **D** is arbitrary. |
| 7 | **B** | Memory bandwidth: every parameter is read from memory to generate one token, for relatively little arithmetic. This is why batching helps throughput so much and why quantisation speeds up decode (M4-L17). **A** is what *prefill* is bound by. **C** and **D** are minor. |
| 8 | **A** | At generation the model conditions on its own output — a distribution it never saw in training. Measured: **0.4449 teacher-forced vs 12.5447 free-running, 28×**, with the divergence beginning at the first wrong token. **B** is test-set contamination (M1-L09). **C** is unrelated. **D** is memorisation (M10-L12). |
| 9 | **B** | `2,000 × 100,000 × 4 bytes = 800 MB` for a single forward pass. **A** is off by 100×; **C** by 4,000×; **D** by 100×. This is why implementations compute logits only where needed. |
| 10 | **C** | Only with identical tokenizers and identical evaluation data. A larger vocabulary lowers perplexity partly by construction, since each token carries more text (M3-L05 §5.6). **A** is the mistake that produces meaningless leaderboard comparisons. **B** — size is not the obstacle; the unit is. **D** — nats versus bits is a fixed conversion factor. |

**Q11 rubric (4 marks).** One mark each for: identifying that generation is **sequentially dependent**
— token `n+1` cannot start until token `n` exists — so adding GPUs cannot shorten a single generation;
distinguishing this from **prefill**, which *is* parallel and does benefit; naming at least two things
that genuinely help (batching many concurrent requests for throughput, quantisation and faster memory
for per-step latency, speculative decoding, or simply generating fewer tokens); and noting that
streaming improves *perceived* latency without changing total time. Deduct a mark for any answer
implying the limitation is an implementation defect that better engineering would remove.

---

<a id="m4-l06"></a>
## M4-L06 — Context Windows, Output Limits and Truncation

**Answers: A · B · C · D · D · D · B · C · A · C**

| Q | Ans | Why, and why the distractors fail |
|---|---|---|
| 1 | **A** | The output is drawn from the same budget. A 199k prompt in a 200k window leaves ~1,000 tokens to answer in. **C** is the assumption that produces answers cut off mid-sentence. **B** — the system prompt is part of the input, not counted separately. **D** — history occupies the window only because your application re-sends it, and it is input. |
| 2 | **B** | Attention compares every token pair, so cost grows as `T²`. Measured: **`T^2.06`**, with 4,096 tokens costing **1,015×** what 128 does. **A** — the limit is physical before it is commercial. **C** — tokenizers have no length limit. **D** — the embedding matrix is indexed by *vocabulary*, not position. |
| 3 | **C** | About 1,000 tokens remain, and the answer may be truncated. **A** — no provider extends a window. **B** — some providers error, some silently truncate; **never rely on which**. **D** — nothing is dropped for you. |
| 4 | **D** | Output only, and it reserves no input space. You must do that arithmetic yourself (§5.1). **A** is the common misreading that causes "context length exceeded" despite a low `max_tokens`. **B** — prompt length is limited by the window. **C** — the KV cache follows from context length, not from `max_tokens`. |
| 5 | **D** | Information placed mid-context is used less reliably than information at either end. **A** describes truncation. **B** is false — softmax always sums to 1. **C** is a retrieval concern, upstream of the window entirely. |
| 6 | **D** | At the end, after the context. This exploits the recency end of the U-shaped curve in §7.3, where simulated recall is 1.000 against 0.240 at mid-depth. **A** wastes the strongest position on a question the model must then hold while reading. **B** puts it exactly where recall is worst. **C** costs tokens for marginal benefit and can create ambiguity about which question to answer. |
| 7 | **B** | Send the top 8, then measure. Measured in §7.3: cost per unit of quality bottoms out around 4 documents, and 80 documents cost **33× more per quality point** while scoring *lower* than 16. **A** is the expensive misunderstanding this lesson exists to prevent. **C** is arbitrary. **D** discards the retrieval you already have. |
| 8 | **C** | The system prompt. Truncating it can remove a safety constraint while leaving the rest looking intact — a silent, serious failure. §7.3's budget **refuses** rather than truncating it. **A** and **B** are exactly what the drop order is for. **D** — the output reservation is not content and cannot be truncated. |
| 9 | **A** | Linearly — roughly 0.5 MB/token on a 32-layer model, measured at **64 GB for one request at 128k context**. **B** — attention *compute* is quadratic; the cache is not. **C** — it grows with every generated token. **D** — no compression is applied by default. |
| 10 | **C** | `finish_reason`. It tells you directly whether the model stopped because it finished, hit `max_tokens`, or hit a stop sequence (M4-L15). Checking it takes one line and removes all guessing. **A**, **B** and **D** are all downstream investigations you would only start after `finish_reason` failed to explain it. |

**Q11 rubric (4 marks).** One mark each for: distinguishing what the model *can accept* from what it
*uses well* (advertised vs effective context, §5.4); naming a cost consequence — attention is
quadratic and the KV cache is linear, so a 1M-token request is expensive in both compute and memory
(§7.3 measured 16 concurrent users at 8k dropping to 1 at 128k); noting that retrieval is about
sending *less and better*, which a larger window does not accomplish; and proposing a measurement
rather than an argument — run both configurations against an evaluation set and compare quality per
unit of cost. An answer that simply says "it will be expensive" without the effective-context point
scores 2.

---

<a id="m4-l07"></a>
## M4-L07 — Attention and Self-Attention: the Core Idea

**Answers: A · C · B · C · A · B · D · C · C · D**

| Q | Ans | Why, and why the distractors fail |
|---|---|---|
| 1 | **A** | A weighted average of values, weights computed from content. **B** describes hard selection — attention is soft, and *always* blends every position (that softness is what makes it differentiable, M3-L06 §5.6). **C** is a fixed positional mixing, which is precisely what attention replaces. **D** confuses the score computation with the output. |
| 2 | **C** | What a position seeks differs from what it offers. Measured in §7.3: a **shared** projection gives `qᵢ·qⱼ`, symmetric by construction, with asymmetry **exactly 0.0000** — it can never express "A attends to B but B does not". **A** is backwards; separate projections cost *more*. **B** — Q and K must share a dimension to be dotted. **D** — the scaling applies to the product. |
| 3 | **B** | Softmax saturation, and therefore gradient collapse. Measured: unscaled, the mean softmax gradient falls **483×** between `d_k` 8 and 1,024. **A** — rows sum to 1 regardless of scaling. **C** — softmax is implemented with a max-subtraction that prevents overflow anyway (M3-L09 §5.5). **D** — the `T²` cost is unaffected by the divisor. |
| 4 | **C** | The same set of outputs, merely reordered. Measured to **5.55e-17** — exactly zero in floating point. **A** — the causal mask encodes *ordering* but not distance, and encoder models have no mask at all. **B** — the embeddings are identical; only their order changed. **D** — the computation is perfectly well-defined without order. |
| 5 | **A** | Row `i` is a probability distribution over which positions token `i` draws from. **B** — value normalisation is unrelated and not performed. **C** — scaling changes the spread, not the normalisation. **D** — the mask *removes* mass, and softmax renormalises what remains. |
| 6 | **B** | About the same parameters: `d_head = d_model / n_heads`, so 8 heads of 64 cost what 1 head of 512 costs. Measured: 1, 2, 4, 8 and 16 heads all totalled **12,288** Q/K/V parameters at `d_model` 64. **A** and **D** are the intuitive and wrong answer. **C** — standard multi-head does not share projections (though multi-query attention does, M4-L17). |
| 7 | **D** | It dominated one weighted average, in one head, at one layer. **A** — a large weight on a near-zero value vector contributes nothing. **B** — residual connections carry information around attention, so removal effects do not track weights. **C** — attention maps are not a faithful causal account (Jain & Wallace 2019, and its rebuttal). |
| 8 | **C** | Keys and values come from a different sequence — the decoder queries the encoder's output (M4-L11). **A** — the equation is identical, softmax included. **B** — masking is an orthogonal choice; cross-attention is usually unmasked, but that is not what defines it. **D** — both operate on tokens. |
| 9 | **C** | Near-uniform, because the scores are close together. Measured in §6: weights spanned 0.2342–0.2785 for four tokens, against a uniform 0.25. **A** and **B** are patterns that *emerge* from training, not initial states. **D** — softmax of anything finite is strictly positive, so no weight is ever exactly zero. |
| 10 | **D** | Information bypasses attention through the residual path, so a low attention weight does not mean no influence. **A** — residuals are added after attention and do not touch the weights. **B** — softmax makes rows sum to 1. **C** — the quadratic cost is the `QKᵀ` product, unrelated to residuals. |

**Q11 rubric (5 marks).** One mark each for: describing it as each position building a **blend of the
other positions**, with the blend proportions computed from content; noting the proportions are
**learned and depend on the input**, not fixed; explaining that this lets a word draw on any other
word regardless of distance; naming one thing it cannot do — it has **no notion of order** (a
measured, not asserted, property), or it cannot select just one item since it always blends
everything; and doing all of it without equations. Deduct a mark for any answer implying attention
"decides what is important", which is the framing §5.6 exists to correct.

---

<a id="m4-l08"></a>
## M4-L08 — Queries, Keys, Values and Attention Scores, Worked by Hand

**Answers: A · D · B · A · B · C · C · C · D · C**

| Q | Ans | Why, and why the distractors fail |
|---|---|---|
| 1 | **A** | `d_head = d_model / n_heads = 512 / 8 = 64`. **C** is `d_model` itself — the value before splitting. **B** is `d_model × 8`, the answer you get by multiplying instead of dividing. **D** is `n_heads`. |
| 2 | **D** | `(d_model, d_model)` — full width, with the head split performed as a **reshape of the output**. This is why multi-head costs no extra parameters (M4-L07 §7.3 measured 12,288 for 1, 2, 4, 8 and 16 heads alike). **A** and **C** describe the mental model people carry, not the implementation. **B** confuses a weight matrix with an activation. |
| 3 | **B** | To the scores, before the softmax. **C** is the bug: masked entries genuinely become zero, but mass was removed *after* normalisation, so **rows no longer sum to 1** — and §7.3 shows that is which assertion catches it. **A** and **D** mask the wrong tensor entirely. |
| 4 | **A** | `[1, 0, 0]`. Position 0 may attend only to position 0, so after softmax the single live entry takes all the mass. Verified in both heads in §7.3. **B** ignores the mask. **C** would require every entry masked, which the causal mask never does on the diagonal. **D** — softmax of one element is exactly 1, and perfectly stable. |
| 5 | **B** | A fully-masked row gives `nan` with `−inf` (every term underflows, and the normalising sum is zero) but degrades to a uniform distribution with `−1e9`. This arises when padding and causal masks combine. **A** — the speed difference is irrelevant. **C** — `−inf` is representable in float16. **D** — `−1e9` produces marginally *softer* weights, not sharper. |
| 6 | **C** | Mixes the concatenated head outputs across all dimensions. Without it, head 0's contribution is confined to dimensions 0–1 permanently — a structural limitation, not a numerical one (§7.3). **A** — softmax normalises. **B** — the `√d_head` divisor rescales. **D** — that is what the head split does. |
| 7 | **C** | Their projections select different slices of the vectors, so each head computes different scores from the same input. **A** — all heads see identical data and train together. **B** — heads receive equal-sized slices. **D** — the same mask is applied to every head. |
| 8 | **C** | Its three scores were identical (all 0.3536), and softmax of equal inputs is uniform. **A** inverts cause and effect — uniformity is a *symptom* of undifferentiated scores. **B** is true but incidental; head 1's row 2 is also unmasked and is *not* uniform. **D** is false; head 1's final row was `[0.2920, 0.4159, 0.2920]`. |
| 9 | **D** | Omitting `W_o` and dividing by `√d_model`. Measured in §7.3: both **PASS** all three assertions and raise nothing. **A**, **B** and **C** each name at least one error that *is* caught — the wrong softmax axis and masking after softmax both fail "rows sum to 1", and a missing transpose produces a shape error. |
| 10 | **C** | `(T, d_model)` — identical to the input. That invariant is what allows blocks to stack (M4-L10) and is the fastest shape-bug check available. **A** and **B** describe intermediate states before concatenation. **D** is the attention weight matrix, not the block output. |

**Q11 rubric (4 marks).** One mark each for naming three assertions with the specific bug each catches:
**(1)** attention weight rows sum to 1 — catches a wrong softmax axis *and* masking applied after the
softmax; **(2)** masked entries are exactly zero — catches a mask that was never applied or applied to
the wrong triangle; **(3)** output shape equals input shape — catches a missing transpose in the head
split or a failure to concatenate. The fourth mark is for noting that **these three do not catch
everything**: omitting `W_o` and using the wrong divisor pass all of them, so a correctness argument
needs a reference implementation to compare against, not assertions alone.

---

<a id="m4-l09"></a>
## M4-L09 — Positional Information

**Answers: A · A · B · D · C · C · B · C · D · C**

| Q | Ans | Why, and why the distractors fail |
|---|---|---|
| 1 | **A** | Attention is permutation-invariant — measured at **5.55e-17** in M4-L07 §7.3. Shuffle the input and the outputs shuffle identically. **B** — tokenizers preserve order perfectly; the IDs come out in sequence. **C** — identical tokens *do* share an embedding, but that is what makes position a *separate* problem, not the cause. **D** — softmax normalises within a row and destroys nothing positional. |
| 2 | **A** | A fixed maximum length with no row beyond it. Position 1024 in a 512-row table simply does not exist. **B** is false — a learned table *can* encode distance, just inefficiently and without generalising. **C** — a table lookup is cheaper than computing sinusoids. **D** — the table is trained once, not recomputed. |
| 3 | **B** | Rotating queries and keys by an angle proportional to position. **A** describes sinusoidal encodings. **C** describes ALiBi. **D** would be a learned scheme with a hard length limit — the opposite of RoPE's design. |
| 4 | **D** | The relative distance `m − n`, and nothing else. Verified in §7.3 to **2.91e-14** across distances up to 5,000. **A** is what absolute encodings give. **B** is arbitrary. **C** — rotation preserves magnitude exactly; it changes only the angle, which is the whole point. |
| 5 | **C** | Fast frequencies distinguish neighbours, slow ones distinguish regions; together they encode position at several scales. **A** is false — a single frequency gives distinct values, just ambiguous ones once it wraps. **B** — the count follows from `d_model`, it is not a requirement. **D** — sinusoidal encodings have **zero** parameters at any frequency count. |
| 6 | **C** | A distance-based penalty added to the attention scores, with a different slope per head. Measured in §7.3: slope 1.0 puts 0.632 on the immediately preceding token; slope 0 attends uniformly. **A** describes a learned embedding. **B** would break RoPE's property (§7.3 demonstrates this). **D** — no extra head is involved. |
| 7 | **B** | Output degrades silently, with no error and no warning. **A** — a provider may cap the input, but that is a separate API limit, not the model telling you it has left its trained range. **C** — no truncation happens automatically. **D** — sinusoidal and RoPE are defined at any position and do not wrap; §7.3 measured adjacent-position similarity identical at 256 and 4,096. |
| 8 | **C** | Compressing positions into the trained range — position 8,000 presented as 2,000. Measured cost in §7.3: **adjacent positions become 15× harder to distinguish** at 4× compression. **A** applies to learned tables and requires training the new rows. **B** describes NTK-aware scaling, a different technique. **D** would remove position entirely. |
| 9 | **D** | `32,768 × 4,096 = 134,217,728` — **134M parameters**. **A** and **B** are the two factors. **C** is `d_model / d_head` for some other configuration. At 128k context the same table is **536.9M**, about 8% of a 7B model. |
| 10 | **C** | Queries and keys only, inside attention. **A** is the error §7.3 demonstrates: rotating V makes the output depend on absolute position and destroys the relative property. **B** would make it an input-side scheme like sinusoidal, losing the exact-relative guarantee. **D** describes ALiBi. |

**Q11 rubric (4 marks).** One mark each for: identifying that extending context (by interpolation or
retraining) is a **trade**, not a free upgrade; naming the specific mechanism — position interpolation
compresses positions so adjacent ones become harder to distinguish (§7.3 measured **15×** at 4×
compression), costing fine-grained resolution exactly where short documents need it; noting that this
is a **known and predictable** consequence rather than a mystery; and stating the fix — evaluate both
length ranges before shipping, and consider keeping the short-context model for short inputs. Deduct a
mark for any answer that treats the regression as a bug rather than as the expected cost of the
extension.

---

<a id="m4-l10"></a>
## M4-L10 — Inside a Transformer Block

**Answers: B · A · D · B · C · A · D · B · C · B**

| Q | Ans | Why, and why the distractors fail |
|---|---|---|
| 1 | **B** | Attention and a feed-forward network, each wrapped in a norm and a residual. **A** — one attention sublayer per block. **C** omits attention, leaving a network that cannot see other tokens. **D** — the vocabulary softmax is the LM head, applied once after the whole stack, not per block. |
| 2 | **A** | The FFN, at `8d²` against attention's `4d²`. Measured at **66.7% of every block** across configurations from 12M to 65B parameters. **C** reverses it — the intuitive answer, given the architecture's name. **B** — norms cost `~4d`, negligible. **D** — 4× expansion produces 2:1, not parity. |
| 3 | **D** | Processes each position independently; no positions interact. **A** is attention's job — the alternation between the two is the design. **B** is normalisation. **C** describes the attention weights. |
| 4 | **B** | `dy/dx = 1 + f'(x)` gives a path with derivative exactly 1 from the loss to every layer. Measured at 48 layers: **4.84e+09×** more gradient with residuals than without. **A** — that is normalisation. **C** — the gradient traverses the same number of layers; it simply has an extra route. **D** — clipping is a separate, explicit operation (M3-L12). |
| 5 | **C** | Inside the branch: `x + sublayer(norm(x))`, leaving the residual path untouched. **A** is post-norm, which breaks the identity path at every layer. **B** — every block has its own norms. **D** — norms apply to activations, not to attention weights. |
| 6 | **A** | RMSNorm omits the mean subtraction and the learned shift, normalising by root-mean-square alone. **D** describes BatchNorm, which is the thing both LayerNorm and RMSNorm exist to avoid in sequence models. **B** and **C** are inventions. |
| 7 | **D** | `32 × 12 × 4096² = 6,442,450,944` — about **6.4 billion**, verified exact in §7.3. Add 131M for the embedding and you have a "7B" model. **A** and **B** are off by an order of magnitude or more; **C** is a full order too large. |
| 8 | **B** | RMSNorm removes scale, and step 3 scaled the vector without rotating it — so the normalised result is unchanged (max difference 3.79e-07). **A** is false; the addition doubled the magnitude. **C** — RMSNorm is not idempotent in general. **D** — gamma affects the output but not this equality. |
| 9 | **C** | The residual adds to `x`, not to the FFN's output, so the component survives in the residual stream at −1.8165. **A** — ReLU zeroes every negative. **B** — the second matrix cannot recover information the activation destroyed. **D** — there is no final normalisation inside a block. |
| 10 | **B** | 4×. Parameters go as `d²`, so doubling width quadruples them — measured 6.44B → 25.77B. Doubling *depth* is the 2× answer. **Width is the expensive axis**, which is the practical point. |

**Q11 rubric (4 marks).** One mark each for: identifying **post-norm** as the likely cause and that its
instability scales with depth; explaining *why* — the residual passes through the normalisation, so the
`+1` identity gradient path is broken at every layer, and 60 broken paths compound where 12 did not;
recommending **pre-norm** (`x + sublayer(norm(x))`) plus a final norm after the last block; and naming
at least one supporting measure — learning-rate warmup (M3-L12 §5.6), gradient clipping, or verifying
the loss starts at `ln(vocab)`. Award full marks for an answer that also proposes *measuring* per-layer
gradient norms to confirm the diagnosis before changing the architecture.

---

<a id="m4-l11"></a>
## M4-L11 — Encoder, Decoder and Encoder-Decoder Architectures

**Answers: B · C · A · D · C · C · D · D · C · A**

| Q | Ans | Why, and why the distractors fail |
|---|---|---|
| 1 | **B** | Which positions may attend to which. §7.3 demonstrates it directly: the *same* block code and the *same* weights, differing only in the mask, produce completely different behaviour. **A**, **C** and **D** all vary freely within each architecture and distinguish nothing. |
| 2 | **C** | Bidirectional attention makes next-token prediction trivial — the answer is in the input, and M4-L05 §7.3 measured the loss collapsing to **0.0006** under exactly this condition. Hence MLM instead. **A**, **B** and **D** are all false; the limitation is structural, not a matter of size or components. |
| 3 | **A** | `1,000 × 0.15 = 150`. **B** (999) is what CLM supervises, which is the comparison the question sets up. **C** is the document length. **D** confuses 15% with 15 tokens. |
| 4 | **D** | Every position is a training example — measured at **6.7×** the supervised positions at every document length. **A** is false; both cost the same per forward pass. **B** — masking saves no memory. **C** is plainly false, since MLM is self-supervised too. |
| 5 | **C** | The encoder's output. Queries come from the decoder; keys and values from the encoder. **A** describes self-attention, which the decoder block also has — separately. **B** and **D** are inventions. |
| 6 | **C** | No — the source is fully known at every decoding step, so there is nothing to hide. §7.3 shows the unmasked cross-attention matrix with rows summing to 1.0000. **A** confuses cross-attention with the decoder's *self*-attention, which **is** masked. **B** mistakes consistency for correctness. **D** — masking must match between training and inference or the model breaks. |
| 7 | **D** | 21 of 36 = **58%**. **A** is the encoder. **B** is the fraction you would get by counting only the strict lower triangle and forgetting the diagonal. **C** is arbitrary. |
| 8 | **D** | Causal masking means early positions never see later context, and an embedding *is* a position's representation. Measured: encoder **0.6212** against decoder **0.5125** on positions that cannot see the evidence, with a baseline of 0.5200. **A** is false — decoders are trained on more data, not less. **B** — `[CLS]` is a training convention, and mean or last-token pooling works without it. **C** is false. |
| 9 | **C** | Benchmark both. With abundant labels, a fixed label set and 50,000 daily requests, a fine-tuned encoder is frequently cheaper, faster, locally runnable and more accurate — but "frequently" is not "always", so measure (M1-L11). **A** is the default-to-the-biggest-model instinct this lesson exists to interrupt. **B** — classification is not seq2seq. **D** — training from scratch discards all pretraining value. |
| 10 | **A** | Encoder-only. It maps input to a fixed label set and was never trained to follow instructions, so text in its input cannot redirect it. **B** — a decoder follows instructions *by design*, which is exactly the injection surface. **C** — an encoder-decoder still generates from instructions. **D** — the three are not equally exposed, and treating them as such loses a real architectural mitigation (M10-L06). |

**Q11 rubric (4 marks).** One mark each for: naming a concrete cost or scale difference (§7.3 measured
**636×** fewer parameters for a 110M encoder against a 70B hosted decoder); noting the task's shape
makes the small model viable — a **fixed label set** with **abundant labels**, which is what fine-tuning
needs; naming a non-cost advantage — it runs locally so sensitive data stays in-house, latency is far
lower, or it has **no prompt-injection surface**; and framing the recommendation as **benchmark both**
rather than "switch", since the accuracy question is empirical. Deduct a mark for any answer that
asserts the encoder will be more accurate without proposing to measure it.

---

<a id="m4-l12"></a>
## M4-L12 — Pretraining, Instruction Tuning and the Post-Training Stack

**Answers: A · C · D · C · A · D · A · B · B · C**

| Q | Ans | Why, and why the distractors fail |
|---|---|---|
| 1 | **A** | Questions are frequently followed by more questions in crawled text — quiz pages, exam papers, FAQ indexes. §7.3 reproduces this from a corpus built exactly that way. **B** inverts cause and effect: the model has not been *shown that answering is what follows*, which SFT fixes. **C** — the behaviour persists at temperature 0. **D** — a base model has no chat template to apply. |
| 2 | **C** | Which continuation is most probable. §7.3's SFT model starts from the base model's own weights with identical architecture and produces `paris` where the base produced `what is the`. **A** is the central misconception — post-training cannot add knowledge that pretraining did not create. **B** and **D** are unchanged by SFT. |
| 3 | **D** | `6 × parameters × tokens` — roughly two operations forward and four backward per parameter. **A** is the forward-only figure. **B** and **C** are dimensionally wrong. |
| 4 | **C** | ~20 tokens per parameter, so `7e9 × 20 = 140B`. **D** (20B) is the multiplier mistaken for the answer; **A** is one token per parameter; **B** is 100×. |
| 5 | **A** | Otherwise the model learns to generate user questions. Measured: **74%** of SFT tokens were prompt tokens, and the unmasked model produced a fluent user question from a stub. **B** is incidental. **C** — masking does not reduce backward memory. **D** is false. |
| 6 | **D** | A forged system turn, if special-token encoding is enabled for user text. §7.3 shows the resulting prompt containing **two system turns** where there should be one, the second overriding the first. **A** — encoding succeeds, which is the problem. **B** is irrelevant. **C** is exactly the assumption that causes the vulnerability; escaping is not automatic. |
| 7 | **A** | Pretraining, at ~99% of total compute and trillions of tokens. **B**, **C** and **D** together account for well under 1% of compute and change *behaviour*, not knowledge. |
| 8 | **B** | Serving many requests favours a smaller model over-trained on more data, since the objective is **lifetime** cost rather than training cost. **A** — precision is an orthogonal choice. **C** is false. **D** — scaling laws are not restricted to large models. |
| 9 | **B** | Low learning rates, few epochs, mixed general data. Measured: LR 1e-4 caused **no** degradation while LR 0.3 made general loss **9.52× worse**. **A** and **C** both make it worse. **D** removes a safeguard and does nothing for forgetting. |
| 10 | **C** | 3B tokens is **2.1%** of Chinchilla-optimal for 7B — you would train a badly undertrained model and get something worse than a free download. **A** is a real cost but not the *main* problem, and it can be answered by raising the budget; the data problem cannot. **B** is a separate legal question, not the technical one. **D** is false — 7B is ample for a domain. |

**Q11 rubric (5 marks).** One mark each for: agreeing that the data may well be a moat while separating
that from *pretraining* being the way to exploit it; giving the data arithmetic — compute-optimal for
7B is ~140B tokens, and an enterprise's entire document estate is typically **~3B, about 2%** (§7.3);
noting that pretraining cost is dominated by data cleaning, failed runs and salaries rather than the
~$8k of compute; naming the cheaper options in order — **retrieval** (days, keeps data updatable and
citable), **fine-tuning** (behaviour and format), **continued pretraining** (genuine domain
adaptation); and stating what pretraining *would* legitimately buy — an unusual modality, a hard
data-sovereignty requirement, or a business model built on selling models. Deduct a mark for a flat
refusal that offers no alternative path to using the data.

---

<a id="m4-l13"></a>
## M4-L13 — Preference Optimization: RLHF, DPO and What Alignment Buys You

**Answers: A · B · C · B · C · A · B · B · A · D**

| Q | Ans | Why, and why the distractors fail |
|---|---|---|
| 1 | **A** | Judging which of two responses is better is far easier and faster than authoring a good one — roughly an order of magnitude more signal per annotator-hour. **C** is false: comparisons need *more* annotators for reliability, not fewer, because agreement is only ~60–75%. **B** — rating scales are usable, just noisier and harder to calibrate across annotators. **D** — guidelines matter more for comparisons, not less. |
| 2 | **B** | Logistic regression on the score *difference*: `P(A ≻ B) = σ(r(A) − r(B))` (M3-L09 §5.1). **A** — the labels are binary, not continuous. **C** describes a listwise ranking loss, a different formulation. **D** is unrelated. |
| 3 | **C** | The policy drifting far from the reference to chase reward. Measured: at β = 0 the KL distance reached 0.729 and the policy moved **1.97× further on length than on correctness**; at β = 5 the distance was 0.088. **A** — reward-model overfitting is a separate problem addressed with more data. **B** — disagreement enters through the reward model regardless. **D** — the value network has its own clipping. |
| 4 | **B** | It optimises preferences directly, with no separate reward model and no RL loop — **2 models in memory instead of 4**. **A** — DPO trains *no* reward model. **C** — neither method needs human feedback during optimisation; both use a fixed preference dataset. **D** is false. |
| 5 | **C** | Nothing on its own. Only differences enter the Bradley–Terry likelihood, so the scale is arbitrary — §7.3 adds 1,000 to every reward and the ranking and all preference probabilities are **identical**. **A**, **B** and **D** all read meaning into an arbitrary offset, and **B** additionally treats an interval scale as a ratio scale. |
| 6 | **A** | Optimising a proxy hard enough finds where it diverges from the goal — Goodhart's law. **D** is the comforting answer and is wrong: §7.3's reward model fitted its data *correctly* and the hacking followed anyway. **B** — DPO has no RL and hacks too. **C** — no annotator in §7.3 was dishonest. |
| 7 | **B** | Agreement is rated better than correction in preference data. Measured: as annotators' ability to verify correctness fell from 100% to 10%, weight shifted from correctness (7.60 → 2.70) to agreement (0.00 → 4.90), with agreement overtaking between **70% and 40%** verification. **A** — pretraining is not where this is introduced. **C** — the KL penalty limits drift in *either* direction. **D** — no such instruction is needed; the effect emerges from what annotators *could see*. |
| 8 | **B** | Worsens it. Confident answers are rated higher than hedged ones, so expressed uncertainty is trained away — which is why a model's stated confidence is not a probability (M3-L14 §5.5). **A** confuses *preferred* with *correct*. **C** — post-training changes calibration substantially. **D** is unfounded. |
| 9 | **A** | Both responses are correct, so `w_cor(1 − 1) = 0` and the correctness term vanishes exactly — the pair constrains only `w_len`. **B** — the judgement was reliable; it simply carries no correctness information. **C** — Bradley–Terry handles any number of features. **D** confuses which feature is *informative* with which is *larger*. |
| 10 | **D** | A strong default, with your own guardrails still required. It does not guarantee refusals (jailbreaks work), does not encode your values, does not transfer to your domain rules, and establishes no compliance. **A**, **B** and **C** each treat a model property as a system control, which is the mistake M10-L05 and M10-L07 exist to prevent. |

**Q11 rubric (5 marks).** One mark each for: naming **length bias in preference data** as the likely
cause; explaining the mechanism — annotators rate longer answers better on average, the reward model
captures that faithfully, and the policy exploits it because length is **cheap** to increase (§7.3
measured a **1.97×** movement ratio); stating that this is expected behaviour rather than a bug, since
every component worked correctly; naming what you would check — response-length distribution before
and after, whether quality metrics moved at all, and the KL/β setting; and proposing both fixes in the
right order — **length-balance the preference pairs** (removes the incentive; measured to drive
`w_length` to exactly 0.0000) and raise β as the weaker fallback that only bounds the symptom.

---

<a id="m4-l14"></a>
## M4-L14 — Autoregressive Decoding

**Answers: A · C · B · D · C · D · A · C · B · C**

| Q | Ans | Why, and why the distractors fail |
|---|---|---|
| 1 | **A** | To the logits, before softmax: `exp(z/T) / Σexp(z/T)`. **C** would rescale probabilities without renormalising correctly and is not what temperature does. **B** — the token is already chosen. **D** confuses it with the `√d_k` scaling (M4-L07). |
| 2 | **C** | Flattens the distribution, raising low-probability tokens. Measured: `purple` went from 1 in 35,571 at `T=0.5` to **1 in 43** at `T=2.0`. **A** is the seductive error — temperature adds no information and creates no new candidates. **B** — accuracy does not improve; different wrong answers become reachable. **D** — length is governed by `max_tokens` and EOS. |
| 3 | **B** | The number kept **adapts** to the distribution. Measured: top-p 0.9 kept **1** token on a peaked distribution and **8** on a uniform one, while top-k=3 kept 3 in both. **A** — both apply after temperature. **C** — the proportion of *probability*, not of the vocabulary. **D** — both operate on probabilities. |
| 4 | **D** | Cumulative `0.42, 0.70, 0.84, 0.92` — reaches 0.9 at the **fourth** token. **A** stops at 0.84, short of 0.9; **B** and **C** overshoot. |
| 5 | **C** | Temperature 0, **then validate and retry**. Temperature 0 alone is not enough — validation catches malformed output from any cause (M2-L08), and §7.3 of M4-L15 shows truncation producing invalid JSON at temperature 0. **A**, **B** and **D** all introduce randomness into a task with one correct answer. |
| 6 | **D** | Floating-point reduction order varies with batching. Measured: with a median logit gap of 2.38e-07 in float32, **44.4% of near-ties flip** on summation order alone. **A** — providers do not add noise. **B** — most implementations do treat 0 as greedy. **C** — weights are static. |
| 7 | **A** | Loop. The most probable continuation of a repeated pattern is that pattern again. Measured in §7.3: identical output on both runs, cycling the same sentence. **B** is backwards. **C** and **D** do not happen. |
| 8 | **C** | Above a fraction of the **top token's** probability — relative to the model's own confidence. **A** is a fixed absolute threshold, which is what min-p avoids. **B** is top-k. **D** is top-p. |
| 9 | **B** | It made a nonsense token reachable, not the model creative. **A** is the common and expensive misreading — the model has no better answer hidden in its tail. **C** — the model was not under-confident. **D** — 1.65%→2.30% is once every 43 tokens, which is very meaningful in a long generation. |
| 10 | **C** | Unreliable — plausible-but-wrong tokens rank **inside** the nucleus. Measured: top-p 0.9 did hold to about `T=3.0` on an 8-token toy where the bad tokens ranked 7th and 8th, but a real vocabulary has thousands of plausible-but-wrong tokens ranked high. **A** overstates the protection; **B** is arbitrary; **D** is false — §7.3 measured `P(purple)` rising **3,348×**. |

**Q11 rubric (4 marks).** One mark each for: identifying temperature 0.7 as inappropriate for a task
with one correct output; explaining that sampling means the model occasionally selects a
lower-probability token, and JSON has no tolerance for a single wrong character; recommending
temperature 0; and noting that temperature 0 alone is insufficient — you must **still validate the
parsed output and retry**, because truncation and other causes produce invalid JSON regardless
(M4-L15). Deduct a mark for "the default is fine" reasoning of any kind.

---

<a id="m4-l15"></a>
## M4-L15 — Stop Conditions, Truncated Output and Finish Reasons

**Answers: A · B · B · D · C · B · C · A · A · C**

| Q | Ans | Why, and why the distractors fail |
|---|---|---|
| 1 | **A** | Inspect `finish_reason`. **C** is exactly the trap: §7.3 shows a completed response ending `' "price": 10.99}]}'` and a truncated one ending `'", "qty": 4, "pric'` — neither ending identifies which is which, and a truncation that lands on a full stop looks finished. **B** fails when the model legitimately used the full budget. **D** works only for structured output, and by then the error names the wrong thing. |
| 2 | **B** | Generation stopped at `max_tokens` before the model was finished. **A** — exceeding the *context* window is a different error, raised before generation. **C** likewise. **D** produces a different reason (or the same one, ambiguously — §5.3). |
| 3 | **B** | Do not parse; retry with a higher limit or a smaller request. **C** is the actively dangerous answer: §7.3 shows brace-repair turning a truncated `delete_records` call into valid JSON with `filter` and `dry_run` missing. **A** and **D** propagate partial data into systems that assume it is complete. |
| 4 | **D** | A repair step can make it valid while dropping a safety argument. Measured: at one cut point the repaired call was `{"action": "delete_records"}` — valid JSON, real action, **no filter**. **A** is the *safe* case and is what usually happens to raw truncations. **B** and **C** are false. |
| 5 | **C** | The model decided it was finished — a prediction like any other token, which can fire early. **A** conflates stopping with being correct. **B** is false on providers that share the reason value between EOS and stop sequences. **D** does not follow. |
| 6 | **B** | Will truncate again unless something changes. Nothing about the request differs, and at temperature 0 nothing about the output differs either. **A** — sampling variation rarely shortens a response enough. **C** and **D** are not automatic anywhere. |
| 7 | **C** | In the final chunk. **The trap is ignoring it**, which builds a system that structurally cannot detect truncation and will show users partial answers while logging success. **A**, **B** and **D** are false. |
| 8 | **A** | Usually excluded. Measured: stopping on ` ``` ` returned **one** fence where valid markdown needs two. **B** and **C** are wrong; **D** confuses stop matching with `max_tokens`. |
| 9 | **A** | `max_tokens = 200` sat at the **98.1st percentile** of the output-length distribution, so 1.92% of documents exceeded it. **B** — the model produced *valid* JSON and was cut off. **C** — the inputs were fine. **D** — temperature 0 was already set. |
| 10 | **C** | A measured percentile of your own output-length distribution. **A** wastes budget and permits runaway generation. **B** is the guess that produced the 2% bug. **D** ignores that you must reserve output space deliberately (M4-L06 §5.1). |

**Q11 rubric (4 marks).** One mark each for: stating the cause plainly — the model was cut off at
`max_tokens`, not producing invalid JSON; explaining **why the parser was the wrong place to look**
(the error names a character offset, nothing mentions token limits); giving the quantitative reason for
2% (the limit sat at the ~98th percentile of output length, and failures correlate with document
complexity, which a small test set lacks); and stating the three-part fix — **check `finish_reason`
before parsing**, raise the limit from measured data, and validate the schema anyway. An answer that
blames the model scores 0 on the first mark.

---

<a id="m4-l16"></a>
## M4-L16 — Training Knowledge vs Runtime Context

**Answers: A · A · C · B · D · D · D · B · C · A**

| Q | Ans | Why, and why the distractors fail |
|---|---|---|
| 1 | **A** | Your application re-sends the history. §7.3 demonstrates it: turn 2 sent *without* history has no idea turn 1 happened. **B** — providers do not hold conversation state for you (a "memory" feature is application-level storage, and you should know where it lives). **C** — weights are static at inference. **D** — the KV cache is per-request. |
| 2 | **A** | The weights, fixed at the end of training. **C** is in-context information — the other of the only two stores. **B** and **D** are neither. |
| 3 | **C** | `20 × 500 + 100 × (19×20/2) = 10,000 + 19,000 = 29,000`, ≈31,000 including the current turn's contribution. **A** counts only the history term; **B** counts one turn; **D** roughly doubles. |
| 4 | **B** | Quadratically: every turn re-sends all prior turns. Measured: **16× the turns costs 51× the tokens**. **A** is the assumption that breaks capacity planning. **C** and **D** are false. |
| 5 | **D** | It varies, and an explicit instruction is your strongest lever. **A** and **B** both state a rule where there is a contest. **C** — no model reports a conflict. And §7.3 adds a further caution: a small model may lack the *capability* to be overridden by context at all. |
| 6 | **D** | Far more reliably. Measured: a fact seen once reached P = 0.0008; seen 150 times, 0.2251. **B** is backwards. **A** and **C** deny the mechanism that makes models reliable on common facts and unreliable on rare ones. |
| 7 | **D** | Retrieval — the weights cannot cite. **A** is the most common misconception about fine-tuning (M4-L01 §5.4). **B** works for a handful of facts but does not scale and is not attributable. **C** is fine-tuning again. |
| 8 | **B** | Application-level storage re-injected into the prompt. That is a good design; it is not the model remembering. **A**, **C** and **D** all attribute persistence to the model or the provider's inference path, which would change the privacy analysis entirely. |
| 9 | **C** | You. It is your data store, subject to your retention, access-control and deletion obligations. **A** may be partly true under a processing agreement but does not discharge your responsibility. **B** and **D** are false and dangerous assumptions. |
| 10 | **A** | A large, stable prefix — the system prompt, which §7.3 measured at **25%** of a 40-turn conversation's tokens while never changing. **B** — output is generated, not cached. **C** and **D** change per request. |

**Q11 rubric (4 marks).** One mark each for: explaining that the model has no memory and the whole
history is re-sent every turn; stating that cost is therefore **quadratic** in turns (turn 40 cost
**6.1×** turn 1 in §6); giving two concrete controls — a sliding window, summarising older turns,
retrieving only relevant turns, or prompt-caching the system prompt; and naming what each control
costs (a window loses early context, including the original problem statement — a product decision, not
a technical one).

---

<a id="m4-l17"></a>
## M4-L17 — Serving Internals

**Answers: C · B · B · A · C · D · C · B · B · B**

| Q | Ans | Why, and why the distractors fail |
|---|---|---|
| 1 | **C** | `7e9 × 2 bytes = 14e9 bytes = 13.0 GiB`. **B** is fp32; **A** is int4; **D** confuses parameters with gigabytes. Add 10–20% for real deployment. |
| 2 | **B** | Tokens × concurrent requests. **C** is attention *compute*, which is quadratic; the cache is linear. **A** and **D** both omit the term that actually causes out-of-memory failures. |
| 3 | **B** | Memory bandwidth — every parameter is read to produce one token, for little arithmetic. **A** is what *prefill* is bound by. **C** and **D** are minor. |
| 4 | **A** | Batched requests share the same weight read. Measured in §7.3: per-request time falls sharply with batch size on real matrix operations. **B**, **C** and **D** are inventions. |
| 5 | **C** | **88%** — measured. The weights were 11%. **A**, **B** and **D** all understate it, and the understatement is what causes hardware to be sized from the weights alone. |
| 6 | **D** | GQA. It reduced the cache **70%**, where int8 weights reduced the total **5%**. **A** is the instinct and is nearly useless here; **B** and **C** each save 44% and still do not fit. |
| 7 | **C** | Decode is bandwidth-bound, so halving the bytes read roughly halves the time — regardless of whether int8 arithmetic is faster. **You are buying bandwidth, not FLOPs.** **A** is only sometimes true and is not the reason. **B** is false — the parameter count is unchanged. **D** is a secondary effect. |
| 8 | **B** | Time to first token, then the streaming rate. A response starting in 200 ms and streaming feels faster than one arriving complete at 1 s. **C** is what matters *without* streaming. **A** is your cost, not their experience. **D** is irrelevant to perceived speed. |
| 9 | **B** | Verifying several tokens costs about as much as generating one, because decode is bandwidth-bound. **A** is false — the draft model is worse, which is why verification exists. **C** — the same parameters are read. **D** — drafts are not cached across requests. |
| 10 | **B** | The KV cache at that context and concurrency — it is the term that scales with users and is the binding constraint in every realistic row of §7.3's checklist. **A** spends money before understanding the problem. **C** addresses the wrong term. **D** is worth knowing but secondary. |

**Q11 rubric (4 marks).** One mark each for: identifying that int4 addresses the **weights**, which are
typically a small share of the requirement at real concurrency (measured: **11%**); giving the KV-cache
arithmetic — `2 × layers × kv_heads × head_dim × tokens × bytes`, scaling with users **and** context;
proposing the levers that actually shrink the cache — **GQA** (measured **70%** saving), KV-cache
quantization, shorter maximum context, or fewer concurrent users; and asking for the missing inputs
(context length and target concurrency) before agreeing to anything. Full marks for also noting the
quality cost of int4 must be measured on the team's own evaluation set, not assumed from a benchmark.

---

<a id="m4-l18"></a>
## M4-L18 — Hosted vs Local Models

**Answers: C · C · A · B · D · C · C · D · D · B**

| Q | Ans | Why, and why the distractors fail |
|---|---|---|
| 1 | **C** | Utilisation. Self-hosted cost is **fixed** — measured, the self-hosted column does not move as volume changes. **A** is the intuition the lesson exists to correct: a million requests in one hour and a million over a month cost the same hosted and wildly differently self-hosted. **B** and **D** are secondary. |
| 2 | **C** | `1/0.20 = 5×`. **A** inverts it; **B** is the 50% figure; **D** is the utilisation itself. |
| 3 | **A** | Redundancy, peak provisioning and engineering time. Measured: these took the figure from \$1,460 to **\$8,340**. **C** is the naive comparison that makes self-hosting look cheap. **B** omits the two largest additions. **D** is a useful ratio but not the cost itself. |
| 4 | **B** | Weights downloadable, often under a restrictive custom licence, with training data usually undisclosed. **A**, **C** and **D** are each a specific wrong assumption that becomes a legal exposure (M4-L01 §5.7). |
| 5 | **D** | Data residency or exact version pinning — requirements money cannot buy from a provider. **A** is true only at high *and steady* volume. **B** is generally false; frontier models are hosted. **C** is backwards — self-hosting is far more effort. |
| 6 | **C** | Low utilisation, making self-hosting expensive. Measured: weekday office hours gave **19.6%** utilisation and a break-even of **53×** current volume. **A** confuses peak concentration with high average utilisation. **B** and **D** deny the mechanism. |
| 7 | **C** | Version deprecation forcing re-evaluation. A hosted provider can deprecate or alter the model version under you, changing your system's behaviour without a deploy on your side — and you must then re-run your evaluation set. **A** (building the serving stack), **B** (being on call for inference) and **D** (hardware procurement) are all **self-hosted** costs. |
| 8 | **D** | About 10× — measured at **10.4×**, or **53×** once the workload's real 19.6% utilisation is included. **A**, **B** and **C** are off by large factors in both directions. |
| 9 | **D** | Narrow tasks — classification, extraction, routing — where a small model suffices. M4-L11 §7.3 measured a 110M encoder at **636×** fewer parameters than a 70B decoder for exactly this. **A**, **B** and **C** describe fallback, scheduling and consent routing, which are different patterns. |
| 10 | **B** | Have a shutdown plan; an idle GPU bills like a busy one. **A** contains the dangerous half-truth: a billing alert **notifies, it does not cap**. **C** commits money before you know the requirement. **D** is capacity advice, not a spend control. |

**Q11 rubric (5 marks).** One mark each for: agreeing to do the arithmetic rather than dismissing the
idea; giving the honest self-hosted figure — **redundancy, peak provisioning and engineering time**,
which took \$1,460 to \$8,340 in §7.3; computing the break-even (**10.4×** current volume at perfect
utilisation); raising **utilisation** and, if the workload is bursty, the real break-even (**53×**);
and closing on the question that actually decides it — *is there a data-residency or version-pinning
requirement?* — because if there is, cost was never the deciding factor and if there is not, hosted
wins at this volume by 10×. Deduct a mark for a flat "no" that offers no arithmetic.

---

<a id="module-assessment"></a>
# Module 4 Assessment — Answer Key

## Section A — Recall (14 marks)

**Answers: B · A · A · C · D · C · B · C · D · C · B · D · B · C**

| Q | Ans | Reason, and why the distractors fail |
|---|---|---|
| A1 | **B** | Questions follow questions in crawled text. **A** — the behaviour persists at temperature 0. **C** — a base model has no chat template. **D** — the cutoff is irrelevant to a fact from the 19th century. |
| A2 | **A** | A sequence of vectors, whatever the modality. **B** is a pooled *output*. **C** — tokenisation happens before the model. **D** describes a bag-of-words representation. |
| A3 | **A** | Non-Latin scripts — measured at **1.00 chars/token** for Devanagari against 5.54 for prose. **B** is the trap: technical English measured **5.56**, statistically identical to ordinary prose. **C** measured 4.98. **D** is the baseline. |
| A4 | **C** | A weighted average of values, weights from content. **A** is hard selection; attention is soft, which is what makes it differentiable. **B** is what attention replaces. **D** confuses the score with the output. |
| A5 | **D** | Softmax saturation and gradient collapse — measured at **483×** between `d_k` 8 and 1,024. **B** — max-subtraction already prevents overflow. **A** and **C** are unaffected by the divisor. |
| A6 | **C** | The same outputs, reordered — measured to **5.55e-17**. **B** — the mask encodes ordering but not distance, and encoders have no mask. **D** — the embeddings are identical; only order changed. |
| A7 | **B** | The FFN, at `8d²` against attention's `4d²` — **66.7%** of every block, measured across configurations from 12M to 65B. **C** states the right number against the wrong component. **A** — norms cost `~4d`. |
| A8 | **C** | Encoder-only. Bidirectional attention makes next-token prediction trivial (M4-L05 measured the loss collapsing to 0.0006), so encoders are trained with MLM and have no generation procedure at all. **A**, **B** and **D** are false. |
| A9 | **D** | Which continuation is most probable. M4-L12 §7.3 showed an SFT model starting from the base model's own weights producing `paris` where the base produced `what is the`. **A** is the central misconception. |
| A10 | **C** | Goodhart: optimising a proxy finds where it diverges. **D** is the comforting and wrong answer — the reward model in M4-L13 §7.3 fitted its data *correctly* and the hacking followed. **A** — no annotator was dishonest. **B** — DPO has no RL and hacks too. |
| A11 | **B** | Flattens the distribution. Measured: `purple` went from 1 in 35,571 at `T=0.5` to 1 in 43 at `T=2.0`. **C** is the seductive error — no new candidates are created. **A** — different wrong answers, not better ones. |
| A12 | **D** | `finish_reason`. **A** fails when truncation lands on a full stop. **B** works only for structured output and names the wrong cause. **C** fails when the model legitimately used the budget. |
| A13 | **B** | Your application re-sends the history. **A** and **C** attribute persistence to the provider or the inference path, which would change the privacy analysis. **D** — no post-training confers memory. |
| A14 | **C** | The KV cache — measured at **88%** of a 13B/8k/32-user deployment, against 11% for weights. **A** is the number people size hardware from, and it is the smaller one. |

---

## Section B — Applied reasoning (12 marks, 2 each)

**B1 (2).** Fine-tuning teaches **behaviour, not facts** — 1 mark. Propose **retrieval**: the catalogue
changes, must be citable, and can be updated without retraining (M4-L16's heuristic: *if it can change
or must be attributable, it does not belong in the weights*) — 1 mark. Accept "fine-tune for format and
tone, retrieve for the catalogue" as a full-mark answer.

**B2 (2).** **Print `finish_reason`** — 1 mark. Because the parse error names the parser and a character
offset, not the token limit, and truncation produces valid JSON that has simply been cut off; M4-L15
§7.3 measured a 1.92% failure rate from `max_tokens` sitting at the 98.1st percentile — 1 mark. Deduct
for any answer that begins by changing the prompt.

**B3 (2).** **Lost in the middle** — models use the beginning and end of a long context more reliably
(M4-L06 §5.4) — 1 mark. Two fixes from: move the document to the start or end, put the question last,
retrieve fewer and better documents, or shorten the context — 1 mark.

**B4 (2).** int4 addresses the **weights**, which are ~11% of the requirement; the KV cache is ~88% —
1 mark. Give the arithmetic: KV per token `2×40×40×128×2 = 800 KiB`, times 8,192 times 32 ≈ **200 GiB**
against an 80 GiB device, so int4's ~12 GiB saving is irrelevant; **GQA** is the lever (measured 70%) —
1 mark.

**B5 (2).** **Length bias in the preference data** — annotators rate longer answers better, the reward
model captures it faithfully, and the policy exploits it because length is cheap (measured: **1.97×**
faster movement on length than correctness at β=0) — 1 mark. The better fix is **length-balancing the
preference pairs**, which drove `w_length` to exactly 0.0000 and stopped the behaviour with no KL
penalty at all; raising β only bounds the symptom — 1 mark.

**B6 (2).** If user text is tokenised **with special tokens enabled**, they can forge a system turn —
M4-L12 §7.3 produced a prompt with two system turns, the second overriding the first — 1 mark. The fix
is one flag: **never encode user content with special-token encoding on**; the text then appears as an
inert literal string — 1 mark. Deduct for "strip `<|system|>` from the input", which is the fragile fix.

---

## Section C — Calculation (18 marks, 3 each)

### C1
```
(a) 12 × 4096²  = 12 × 16,777,216 = 201,326,592 per block
(b) 32 × 201,326,592           = 6,442,450,944
    + 32,000 × 4,096           =   131,072,000
                               = 6,573,522,944  (≈ 6.57B)
(c) 6,573,522,944 × 2 bytes / 1024³ = 12.24 GiB
```
*1 mark each. Accept 13.1 GB if decimal units are used consistently and stated.*

### C2
```
(a) 2 × 32 × 32 × 128 × 2 bytes = 524,288 bytes = 512 KiB per token
(b) 524,288 × 8,192 × 16 / 1024³ = 64.0 GiB
(c) 12.24 + 64.0 + 4 = 80.24 GiB  against 80 GiB  ->  DOES NOT FIT
```
**Full marks for (c) require noticing it fails by only 0.3%** — a deployment this close to the limit
will OOM under fragmentation even if the arithmetic says it fits (M4-L17 §5.7 advises 15–25% headroom).

### C3
```
(a) T=1.0: exp = 7.3891, 2.7183, 1.6487, 0.3679; sum = 12.1240
    probs   = 0.6095, 0.2242, 0.1360, 0.0303
(b) T=0.5: exp(z/0.5) = 54.598, 7.389, 2.718, 0.135; sum = 64.840
    probs   = 0.8420, 0.1140, 0.0419, 0.0021
(c) cumulative at T=1.0: 0.6095, 0.8337, 0.9697 -> reaches 0.9 at the THIRD token
    top-p 0.9 keeps 3 tokens
```
*1 mark each. Note how sharply T=0.5 concentrates mass: the top token goes 0.61 → 0.84.*

### C4
```
(a) 900 + 29 × 150 = 5,250 tokens
(b) 30 × 900 + 150 × (29 × 30 / 2) = 27,000 + 65,250 = 92,250
(c) 30 independent turns = 30 × 1,050 = 31,500  ->  ratio 2.93x
```
*Full marks for (c) require stating that the ratio **grows with conversation length**, because the
history term is quadratic.*

### C5
```
(a) p95 = 310  ->  5% of responses exceed it  ->  5% failure rate
(b) p99.9 = 700, plus margin: set 800-900
(c) 800 / 120 (p50) ≈ 6.7x the median output length
```
**The third mark requires the reasoning, not just the number:** `max_tokens` is a *ceiling*, not a
target — you are billed for tokens generated, not for the limit, so a generous ceiling costs nothing
except in the rare runaway case. Setting it at p99.9 buys reliability essentially free.

### C6
```
(a) 300,000 × (1,500 × 0.60 + 350 × 2.00) / 1e6
    = 300,000 × 0.0016 = $480/month
(b) 4 × $2.20 × 730 = $6,424
    + 0.3 × $130,000/12 = $3,250
    = $9,674/month
(c) $9,674 / $0.0016 = 6,046,250 requests/month  ≈ 20x current volume
```
**Full marks require the observation that self-hosting is 20× more expensive here** — and a
distinction-level answer notes that 20× is the figure at *perfect utilisation*, which a real workload
will not achieve (M4-L18 §7.3 measured a bursty workload's true break-even at 53× rather than 10×).

---

## Section D — Practical assignment (32 marks)

### D1 — Audit (12 marks, up to 2 per problem, best 6 scored)

| # | Problem | Evidence | Expected |
|---|---|---|---|
| 1 | **`temperature=0.7` for JSON extraction** | Measure `json_valid_rate` across temperatures | Failures at 0.7, none at 0.0 (M4-L14 §5.5) |
| 2 | **`max_tokens=200` with no `finish_reason` check** | Log the reason and the output-length distribution | Truncation on complex invoices; a parse error naming the wrong cause (M4-L15) |
| 3 | **Fine-tuning to learn supplier names** | Try retrieval instead | Fine-tuning teaches behaviour, not facts (M4-L12 §5.4) |
| 4 | **13B at 8k for 32 users on 80 GiB** | Compute the KV cache | ~200 GiB — does not fit by ~2.9× (M4-L17 §6) |
| 5 | **Self-hosting "cheaper at our volume"** | Compute break-even with redundancy, peak and engineering | 40,000/month is far below break-even (M4-L18 §6) |
| 6 | **400-page contract as context** | Compute the token count and check effective context | Likely exceeds the window; and lost-in-the-middle degrades the middle regardless (M4-L06 §5.4) |
| 7 | **Vision model for invoices, unexamined** | Compare OCR-then-text on cost and debuggability | OCR ~39% of the tokens and inspectable at each step (M4-L02 §6) |
| 8 | **Invoice images may contain injected text** | Test with an image containing an instruction | Extracted text is untrusted input (M4-L02 §9, M10-L06) |
| 9 | **No schema validation mentioned** | — | Model output must be validated regardless of temperature (M2-L08) |

*2 marks for a problem named **with** evidence and an expectation; 1 mark for naming it alone.*

### D2 — Corrected design (10 marks)

| Element | Expected | Marks |
|---|---|---|
| Modality | OCR-then-text by default, vision fallback on low OCR confidence; justified on cost **and** debuggability | 2 |
| Decoding | `temperature=0.0`, no top-p needed | 1 |
| `max_tokens` | Set from a **measured percentile** (p99.9) of real invoice outputs, not a guess | 2 |
| Error handling | Check `finish_reason` **before** parsing; validate against a schema; retry with a raised limit | 2 |
| Supplier knowledge | **Retrieval**, not fine-tuning — it changes and must be attributable | 1 |
| Deployment | Hosted at this volume; revisit if volume grows 20× **and** becomes steady | 1 |
| Contract context | **Chunk and retrieve**, not stuff — and treat extracted text as untrusted | 1 |

### D3 — The numbers (6 marks)

| Required | Marks |
|---|---|
| KV cache: `2 × 40 × 40 × 128 × 2 = 800 KiB/token`; × 8,192 × 32 ≈ **200 GiB** | 2 |
| Verdict: 24.2 (weights) + 200 + ~4 = **228 GiB vs 80 GiB — 2.9× over**; GQA is the lever, not quantization | 2 |
| Hosted vs self-hosted at 40,000/month, **including redundancy, peak and engineering**, with the break-even stated and assumptions marked | 2 |

*Deduct 1 mark for any comparison omitting engineering time or redundancy.*

### D4 — The memo (4 marks)

| Criterion | Marks |
|---|---|
| Leads with the two changes that matter most (temperature 0 + `finish_reason`; and the deployment arithmetic) | 2 |
| One screen, no unexplained jargon, no lecture | 1 |
| Offers to pair on the fix rather than only listing faults | 1 |

---

<a id="remediation"></a>
## Remediation

If you scored below 54/76, work through the rows matching what you missed **before** starting Module 5.
Modules 5 through 9 assume this material fluently.

| Missed | Revisit | Then do |
|---|---|---|
| A1, A9, B1 | [M4-L01](../modules/module-04-genai-llm-internals/M4-L01-foundation-models.md) §5.4, [M4-L12](../modules/module-04-genai-llm-internals/M4-L12-pretraining-posttraining.md) §5.4 | The M4-L12 lab, sections 1–2 |
| A2, A3, C3 | [M4-L02](../modules/module-04-genai-llm-internals/M4-L02-modalities.md), [M4-L03](../modules/module-04-genai-llm-internals/M4-L03-tokens-tokenizers.md) §5.3 | Tokenize your own content and compare with `chars/4` |
| A4, A5, A6 | [M4-L07](../modules/module-04-genai-llm-internals/M4-L07-attention.md) | **Work M4-L08 §6 with a pencil** — there is no substitute |
| A7 | [M4-L10](../modules/module-04-genai-llm-internals/M4-L10-transformer-block.md) §5.5 | Count a real model's parameters |
| A8 | [M4-L11](../modules/module-04-genai-llm-internals/M4-L11-architectures.md) §3.2 | The M4-L11 lab, sections 1–2 |
| A10, B5 | [M4-L13](../modules/module-04-genai-llm-internals/M4-L13-preference-optimization.md) §5.5 | The M4-L13 lab, sections 3–4 |
| A11, C3, B2 | [M4-L14](../modules/module-04-genai-llm-internals/M4-L14-decoding.md) §5.1–5.5 | Project 4, exercise 1 |
| A12, C5 | [M4-L15](../modules/module-04-genai-llm-internals/M4-L15-stop-conditions.md) | The M4-L15 lab, section 4 |
| A13, C4 | [M4-L16](../modules/module-04-genai-llm-internals/M4-L16-knowledge-vs-context.md) §5.4 | Compute your own conversation costs |
| A14, C1, C2, B4 | [M4-L17](../modules/module-04-genai-llm-internals/M4-L17-serving.md) §5.1–5.2 | The M4-L17 lab, sections 3–4 |
| C6 | [M4-L18](../modules/module-04-genai-llm-internals/M4-L18-hosted-vs-local.md) §5.1 | The M4-L18 lab, sections 1–4 |
| B3 | [M4-L06](../modules/module-04-genai-llm-internals/M4-L06-context-windows.md) §5.4 | The M4-L06 lab, section 4 |
| B6 | [M4-L12](../modules/module-04-genai-llm-internals/M4-L12-pretraining-posttraining.md) §3.3 | The M4-L12 lab, section 4 |
| Section D | [Project 4](../projects/project-04-model-comparison/README.md) | Its exercises 1 and 2 in full |

---

→ [Module 5 — Prompting and LLM Application Engineering](../modules/module-05-prompting-llm-apps/)

