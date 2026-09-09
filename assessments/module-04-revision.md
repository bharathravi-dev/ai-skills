# Module 4 — Revision Guide

Read this before the assessment. Eighteen lessons condensed to what recurs — and in Module 4 almost
all of it recurs, because Modules 5 through 9 are applications of this material.

If a line reads as unfamiliar rather than merely terse, return to that lesson.

---

## 1. One line per lesson

| Lesson | The thing to retain |
|---|---|
| L01 | **Generative = learns the distribution and samples from it.** A language model *continues text*; the correct answer is often the most probable continuation. |
| L02 | Every modality becomes **a sequence of vectors**. Patch count is **quadratic**; convert to text when text preserves what you need. |
| L03 | **You are billed per token, and the ratio to characters varies 5×.** The model cannot see inside a token. Truncate on token boundaries. |
| L04 | An embedding lookup is **a table read**. Static = one vector per word; contextual = the vector depends on neighbours. **Spaces from different models are incomparable.** |
| L05 | Text → tokens → embeddings → +position → blocks → LM head → softmax → sample. **Shape is `(T, d_model)` throughout.** |
| L06 | The window holds **everything, including the output**. Attention is `T²`. **Advertised ≠ effective.** |
| L07 | **Attention = a weighted average whose weights come from content.** Permutation-invariant, hence positional encodings. |
| L08 | `d_head = d_model/n_heads`; projections are full width and the split is a **reshape**. Mask the scores, **before** softmax. |
| L09 | **RoPE rotates Q and K so the dot product depends only on `m − n`.** Zero parameters, no length limit. |
| L10 | Block = attention + FFN, each with a norm and a **residual**. **The FFN is 67% of the parameters.** |
| L11 | One property separates the three architectures: **who may attend to whom.** Decoder-only won on **training signal (6.7×)**, not representation quality. |
| L12 | Pretraining creates capability; **post-training makes it accessible**. The chat template is a **trust boundary**. |
| L13 | Preferences are cheaper than authoring. **Reward hacking is predicted, not surprising.** Alignment is a default, not a control. |
| L14 | Temperature **reshapes**; top-k/top-p **truncate**. **Temperature 0 is not deterministic.** |
| L15 | **`finish_reason` is the only reliable truncation signal**, and checking it is one line. |
| L16 | Two stores only: **the weights and the prompt**. The model has no memory; history is **quadratic** in turns. |
| L17 | **The KV cache decides how many users you serve**, not the weights. Decode is memory-bandwidth-bound. |
| L18 | **Utilisation, not volume, decides self-hosting cost.** The strongest case is residency or version pinning. |

---

## 2. The formulas and shapes worth memorising

| | |
|---|---|
| Softmax with temperature | `exp(z_i/T) / Σ exp(z_j/T)` |
| Attention | `softmax(QKᵀ / √d_head) V` |
| Attention backward shapes | `dW = Xᵀδ` · `db = δ.sum(0)` · `dX = δWᵀ` |
| Block parameters | `≈ 12 d²` per layer (attention `4d²`, FFN `8d²`) |
| Total parameters | `n_layers × 12d² + vocab × d` |
| Pretraining FLOPs | `6 × parameters × tokens` |
| Chinchilla-optimal | **~20 tokens per parameter** |
| Weight memory | `parameters × bytes_per_parameter` |
| KV cache | `2 × layers × **kv_heads** × head_dim × tokens × bytes` |
| Patch count | `(w/p) × (h/p)` — **quadratic** |
| Conversation tokens | `n × system + t × n(n−1)/2` — **quadratic in turns** |
| Bradley–Terry | `P(A ≻ B) = σ(r(A) − r(B))` |

---

## 3. Numbers this module measured

Every one produced by a lab in this module. Not rules of thumb.

| Measurement | Value | Lesson |
|---|---|---|
| English prose, `cl100k_base` | **5.54 chars/token** (not the folklore 4.0) | L03 |
| Technical English | **5.56 — identical to prose** | L03 |
| Hindi vs English, same sentence | **6.5×** more tokens | L03 |
| Byte cut points producing invalid UTF-8 | **24%** | L03 |
| `cat`/`dog` cosine, never co-occurring | **0.9973** | L04 |
| Unmasked learned padding, unrelated texts | **−0.05 → 0.97** | L04 |
| Anisotropic unrelated pairs above 0.8 | **13.4%** | L04 |
| Causal mask removed: loss / perplexity | **0.0006 / 1.0000** | L05 |
| Exposure bias, teacher-forced vs free-running | **28×** | L05 |
| Attention cost exponent | **`T^2.06`** | L06 |
| KV cache, 7B at 128k, one request | **64 GiB** | L06 |
| Permutation invariance | **5.55e-17** | L07 |
| Shared Q/K projection asymmetry | **exactly 0.0000** | L07 |
| Unscaled softmax gradient collapse, `d_k` 8→1024 | **483×** | L07 |
| Score tensor, 32k context, 32 heads | **128 GB fp32** | L08 |
| RoPE relative property, distances to 5,000 | **2.91e-14** | L09 |
| Residual gradient advantage at 48 layers | **4.84e+09×** | L10 |
| FFN share of every block | **66.7%** | L10 |
| Decoder view vs encoder | **58% of the cells** | L11 |
| CLM vs MLM training signal | **6.7×** | L11 |
| Enterprise corpus vs Chinchilla-optimal for 7B | **2.1%** | L12 |
| Catastrophic forgetting at LR 0.3 | **9.52× worse** general loss | L12 |
| Sycophancy: agreement overtakes correctness | between **70% and 40%** verification | L13 |
| Length-balanced preference data | `w_length` → **exactly 0.0000** | L13 |
| Near-tied logits flipping on summation order | **44.4%** | L14 |
| `max_tokens` at the 98.1st percentile | **1.92% failure rate** | L15 |
| 40-turn conversation vs 40 single turns | **3.5×** | L16 |
| KV cache share of a 13B/8k/32-user deployment | **88%** | L17 |
| GQA saving on that deployment | **70%** (int8 weights: 5%) | L17 |
| Self-hosting break-even at 19.6% utilisation | **53×** current volume | L18 |

---

## 4. Decision tables

### Decoding settings by task

| Task | Temperature | Top-p |
|---|---|---|
| **Structured output / JSON** | **0.0** | — |
| Classification, extraction | 0.0 | — |
| RAG answers, factual QA | 0.0–0.3 | 0.9 |
| Summarisation | 0.3–0.5 | 0.9 |
| Conversation | 0.7–0.9 | 0.95 |
| Brainstorming, creative | 0.9–1.3 | 0.95 |

### Where information should live

| Information | Put it in |
|---|---|
| General knowledge | Weights (already there) |
| **Your documents** | **Retrieval** |
| This user's details | Prompt |
| Output format and tone | Prompt, or fine-tune if very stable |
| Anything after the cutoff | **Retrieval or a tool** |
| Anything that must be cited | **Retrieval** |

**The heuristic that settles most of these: if it can change, or must be attributable, it does not
belong in the weights.**

### Diagnosing generation problems

| Symptom | Cause |
|---|---|
| Repeats a phrase forever | Greedy / very low temperature |
| Incoherent | Temperature too high |
| JSON malformed intermittently | Temperature > 0, **or truncation** |
| Answer stops mid-sentence | `max_tokens` — check `finish_reason` |
| Ignores a supplied document | Lost in the middle, or grounding capability absent |
| Contradicts the system prompt | Prompt truncated, or injection |
| Costs grow superlinearly | Quadratic conversation history |
| OOM at concurrency, fine alone | **KV cache** |

---

## 5. The six mistakes to actively guard against

1. **Not checking `finish_reason`.** One line; the most common omission in LLM code.
2. **Leaving temperature at a chat default for structured output.**
3. **Fine-tuning to add facts.** It teaches behaviour; retrieval supplies facts.
4. **Sizing hardware from the weights.** The KV cache usually dominates.
5. **Assuming the model remembers.** You re-send, and you pay quadratically.
6. **Testing for exact output strings.** Temperature 0 is not deterministic.

---

## 6. What carries forward

| From Module 4 | Where it returns |
|---|---|
| Tokenization and cost | M5 (prompt cost), M7 (chunking) |
| Context windows and budgets | M5-L14, M7-L11 |
| Lost in the middle | M7-L11 — retrieve fewer, better |
| Decoding settings | M5 throughout, M8 (agent determinism) |
| `finish_reason` discipline | M5-L07, M8-L05 (tool calls) |
| Chat template as a trust boundary | M10-L06 (prompt injection) |
| Embeddings and their limits | M6 entirely, M7-L09 (negation) |
| Grounding is a capability | M7-L18 |
| Reward hacking and sycophancy | M5-L15, M10-L09 |
| KV cache and serving arithmetic | M12 (Bedrock), M13 (production) |
| Hosted vs local | M12-L03, M13-L11 |

**The single most transferable idea:** a language model produces the most probable continuation of
its input. Every capability and every failure in the next five modules follows from that one
sentence.

---

→ [Module 4 assessment](module-04-assessment.md)
