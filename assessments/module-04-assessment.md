# Module 4 Assessment — Generative AI and LLM Internals

| | |
|---|---|
| **Covers** | M4-L01 … M4-L18 and Project 4 |
| **Questions** | 24 (14 multiple choice, 6 calculation, 4 short answer) + 1 practical assignment |
| **Total marks** | 76 |
| **Pass mark** | 54 (70%) |
| **Time** | ~2.5 hours (90 min for Sections A–C, 60 min for Section D) |
| **Answer key** | [`answer-keys/module-04-answers.md`](../answer-keys/module-04-answers.md#module-assessment) |

**Conditions.** Sections A and B closed book. Section C may use a calculator. Section D uses a machine.

**Before you start**, read [the revision guide](module-04-revision.md).

---

## Section A — Recall and understanding (14 marks, 1 each)

**A1.** A base model asked "What is the capital of France?" replies with more questions. Why?

- A. Its sampling temperature has been set far too high.
- B. Questions are often followed by questions in its training text.
- C. It was not given a system prompt with the request.
- D. Its knowledge cutoff predates the information requested.

**A2.** What does a transformer actually receive as input?

- A. A sequence of vectors, one per token, patch or frame.
- B. A single vector summarising the whole input.
- C. A string of characters, tokenised internally.
- D. A sparse matrix of token-frequency counts.

**A3.** Which content type tokenizes **least** efficiently?

- A. Text in a non-Latin script such as Devanagari.
- B. Technical English containing domain jargon.
- C. Well-formatted Python source code.
- D. Ordinary English conversational prose.

**A4.** Attention computes each position's output as:

- A. The single highest-scoring value vector, selected by argmax.
- B. A fixed learned combination of the neighbouring positions.
- C. A weighted average of values, with weights from content.
- D. The element-wise product of the query and key vectors.

**A5.** Dividing attention scores by `√d_k` prevents:

- A. The attention weights failing to sum to one per row.
- B. Numerical overflow when exponentiating large scores.
- C. The score matrix growing quadratically with length.
- D. Softmax saturating, which collapses the gradient.

**A6.** Attention with no positional encoding treats "dog bites man" and "man bites dog" as:

- A. Invalid input, since word order is structurally required.
- B. Different, because the causal mask distinguishes them.
- C. The same set of outputs, merely in a different order.
- D. Different, because the token embeddings themselves differ.

**A7.** Within one transformer block, most parameters are in:

- A. The two normalisation layers and their learned scales.
- B. The feed-forward network, at roughly `8d²`.
- C. The attention projections, at roughly `8d²`.
- D. They are evenly divided between attention and the FFN.

**A8.** Which architecture cannot generate text?

- A. Decoder-only, which is trained only to classify.
- B. Encoder-decoder, which lacks an output head.
- C. Encoder-only, whose bidirectional attention makes it trivial.
- D. All three can generate; they differ only in speed.

**A9.** SFT primarily changes:

- A. The facts and world knowledge available to the model.
- B. The model's parameter count and layer structure.
- C. The tokenizer's vocabulary and special tokens.
- D. Which continuation is most probable, not what it knows.

**A10.** Reward hacking occurs because:

- A. Annotators deliberately supplied misleading preferences.
- B. Reinforcement learning is inherently unstable to optimise.
- C. Optimising a proxy finds where it diverges from the goal.
- D. The reward model was trained on insufficient data.

**A11.** Raising the sampling temperature:

- A. Improves the model's accuracy on difficult questions.
- B. Flattens the distribution, making rare tokens reachable.
- C. Adds candidate tokens the model had not considered.
- D. Reduces the total number of tokens generated.

**A12.** The only reliable way to detect a truncated response is:

- A. Checking whether the text ends with a full stop.
- B. Attempting to parse it and catching the exception.
- C. Comparing its length against the requested maximum.
- D. Inspecting the `finish_reason` field.

**A13.** A model appears to remember earlier conversation turns because:

- A. The provider stores the conversation on its servers.
- B. Your application re-sends the whole history each time.
- C. The KV cache persists between separate requests.
- D. Post-training taught it to retain recent interactions.

**A14.** At realistic concurrency, serving memory is usually dominated by:

- A. The model weights, which are the largest single allocation.
- B. Transient activations during the forward pass.
- C. The KV cache, which scales with tokens × users.
- D. The tokenizer's vocabulary and embedding tables.

---

## Section B — Applied reasoning (12 marks, 2 each)

**B1.** A colleague says "we'll fine-tune the model on our product documentation so it knows our
catalogue." What do you say, and what do you propose instead? *(2 marks)*

**B2.** Your JSON extraction pipeline fails about 2% of the time with a parse error. Temperature is
already 0. What is your first diagnostic step and why? *(2 marks)*

**B3.** A model gives an excellent answer using a document you placed in the middle of a 100,000-token
prompt — but usually ignores it. Explain and give two fixes. *(2 marks)*

**B4.** Your team wants to serve a 13B model at 8k context for 32 concurrent users on one 80 GiB
accelerator, and proposes int4 quantization. Respond with arithmetic. *(2 marks)*

**B5.** After an alignment update, the assistant's answers became noticeably longer with no quality
improvement. Explain the likely mechanism and give the better of the two fixes. *(2 marks)*

**B6.** A user's message contains the literal text `<|system|>`. What is the risk, and what is the
one-line fix? *(2 marks)*

---

## Section C — Calculation (18 marks, 3 each)

Show your working. Answers without working score at most 1 mark.

**C1.** A model has 32 layers, `d_model` 4,096, and a 32,000-token vocabulary with tied embeddings.

(a) Compute the parameters per block using the `12d²` shortcut.
(b) Compute the total parameters.
(c) State the fp16 weight memory in GiB. *(3 marks)*

**C2.** The same model has 32 KV heads and head_dim 128, served in fp16.

(a) Compute the KV cache per token.
(b) Compute the cache for 16 concurrent users at 8,192 context.
(c) With 80 GiB total and ~4 GiB of activations, does it fit? *(3 marks)*

**C3.** Logits over four tokens: `[2.0, 1.0, 0.5, -1.0]`.

(a) Compute the softmax at `T = 1.0` to 4 dp.
(b) Compute it at `T = 0.5`.
(c) State how many tokens top-p = 0.9 keeps at `T = 1.0`. *(3 marks)*

**C4.** A support assistant has a 900-token system prompt and adds 150 tokens per turn.

(a) Input tokens on turn 30.
(b) Total input tokens across 30 turns.
(c) The ratio to 30 independent single-turn requests. *(3 marks)*

**C5.** You measure output lengths and find p50 = 120, p95 = 310, p99 = 480, p99.9 = 700 tokens.

(a) What failure rate would `max_tokens = 310` produce?
(b) What value would you set, and why?
(c) What is the cost consequence of your choice relative to p50? *(3 marks)*

**C6.** Hosted inference costs \$0.60/M input and \$2.00/M output. Your workload is 300,000 requests a
month at 1,500 input and 350 output tokens. Self-hosting needs 4 instances at \$2.20/hour plus 0.3 FTE
at \$130,000/year.

(a) Monthly hosted cost.
(b) Monthly self-hosted cost (730 hours).
(c) The break-even request volume. *(3 marks)*

---

## Section D — Practical assignment (32 marks)

**You may use a machine, this course's material, and the Project 4 codebase.**

A colleague sends you this specification for a new feature:

> *"Extraction service. We send an invoice image to a vision model, get JSON back, and write it to the
> database. Using `temperature=0.7` (the default), `max_tokens=200`. About 40,000 invoices a month.
> We'll fine-tune on our historical invoices so it learns our supplier names. Planning to self-host a
> 13B model on one 80 GiB GPU at 8k context for 32 concurrent workers — should be cheaper than the API
> at our volume. Long-term we want to send the whole 400-page supplier contract as context so it can
> answer policy questions too."*

**D1. Audit (12 marks).** Identify every distinct problem, and for each state the evidence you would
gather and what you expect it to show. **At least eight are available.**

**D2. Corrected design (10 marks).** Specify what you would build instead. Cover: modality choice,
decoding settings, `max_tokens`, error handling, where the supplier knowledge lives, deployment, and
the context strategy for the contract. Justify each in one sentence.

**D3. The numbers (6 marks).** Produce the arithmetic that settles the deployment question: the KV
cache requirement, whether it fits, and the honest hosted-versus-self-hosted comparison at 40,000
requests a month. State your assumptions and mark any figure you would need to verify.

**D4. The memo (4 marks).** Write what you would actually send your colleague. One screen, no
unexplained jargon, leading with the two changes that matter most and why.

**Marking:** see the rubric in the [answer key](../answer-keys/module-04-answers.md#module-assessment).

---

## Marks summary

| Section | Marks |
|---|---|
| A — Recall | 14 |
| B — Applied reasoning | 12 |
| C — Calculation | 18 |
| D — Practical assignment | 32 |
| **Total** | **76** |

**Pass 54 (70%). Distinction 65 (85%).**

If you score below 54, the answer key's remediation table maps every question to the lesson and section
to revisit.
