# Coverage Matrix

Every item from the requested syllabus, mapped to the lesson that teaches it. This is the document to
check when asking "was X actually covered?"

**Status:** ✅ written · ⬜ planned (see [`COURSE_PLAN.md`](COURSE_PLAN.md) for the full inventory)

---

## Module 1 — AI Foundations ✅ COMPLETE

| Syllabus item | Lesson | Where | Status |
|---|---|---|---|
| AI, machine learning, deep learning, generative AI | M1-L01 | §3, §5.1 | ✅ |
| Rule-based systems versus learned systems | M1-L02 | §5.1–5.4 | ✅ |
| Classification | M1-L03 | §5.1, §5.2 | ✅ |
| Regression | M1-L03 | §5.1, §5.3 | ✅ |
| Clustering | M1-L03 | §5.1; M1-L07 §5.3 | ✅ |
| Generation | M1-L03 | §5.1, §5.6 | ✅ |
| Data, datasets | M1-L04 | §5.1 | ✅ |
| Features | M1-L04 | §5.2 | ✅ |
| Labels | M1-L04 | §5.4 | ✅ |
| Models | M1-L04 | §5.3 | ✅ |
| Algorithms | M1-L04 | §5.3 | ✅ |
| Parameters versus hyperparameters | M1-L05 | §5.1–5.3 | ✅ |
| Training | M1-L06 | §5.1 | ✅ |
| Validation | M1-L06 | §5.1–5.2 | ✅ |
| Testing | M1-L06 | §5.1, §5.5 | ✅ |
| Inference | M1-L06 | §5.1 | ✅ |
| Supervised learning | M1-L07 | §5.1 | ✅ |
| Unsupervised learning | M1-L07 | §5.1, §5.3 | ✅ |
| Self-supervised learning | M1-L07 | §5.2 | ✅ |
| Reinforcement learning | M1-L07 | §5.4 | ✅ |
| Generalization | M1-L08 | §3, §5.1 | ✅ |
| Overfitting | M1-L08 | §5.1–5.3 | ✅ |
| Underfitting | M1-L08 | §5.4 | ✅ |
| Data leakage | M1-L09 | §5.1 | ✅ |
| Evaluation contamination | M1-L09 | §5.2 | ✅ |
| Probabilistic behaviour and uncertainty | M1-L10 | §5.1, §5.4 | ✅ |
| Hallucination and unsupported claims | M1-L10 | §5.2 | ✅ |
| AI capability versus application reliability | M1-L11 | §3, §5.1 | ✅ |
| When ordinary code is preferable to AI | M1-L11 | §5.2–5.3 | ✅ |

**Added beyond the requested syllabus** (prerequisites the brief asked me to add where needed):

| Addition | Lesson | Why added |
|---|---|---|
| Ranking as a fifth task shape | M1-L03 §5.5 | RAG retrieval is a ranking problem; without this, Module 6 metrics make no sense |
| Multi-label vs multi-class vs ordinal | M1-L03 §5.2, §5.4 | The most common and costly task-framing error in practice |
| Calibration and reliability diagrams | M1-L10 §5.3 | Required before any confidence-threshold decision in M7-L13 |
| Compound error arithmetic (`p^n`) | M1-L11 §5.1 | Required to reason about agent step limits in M8-L15 |
| Optimistic bias from selection | M1-L05 §5.4 | Underpins every evaluation claim in Modules 5, 7 and 13 |
| Point-in-time feature reconstruction | M1-L09 §6 | The realistic form of temporal leakage |

---

## Module 2 — Python and Software Foundations ✅ COMPLETE

| Syllabus item | Lesson | Status |
|---|---|---|
| Installation, terminal basics, virtual environments, package management | M2-L01 | ✅ |
| Variables, primitive types, strings | M2-L02 | ✅ |
| Collections | M2-L03 | ✅ |
| Conditions, loops, comprehensions | M2-L04 | ✅ |
| Functions, scope | M2-L05 | ✅ |
| Modules, classes, composition | M2-L06, M2-L07 | ✅ |
| Type hints and validation | M2-L08 | ✅ |
| Files, paths, CSV, JSON, environment variables | M2-L09 | ✅ |
| Exceptions and debugging | M2-L10 | ✅ |
| HTTP, REST, headers, status codes, authentication | M2-L11 | ✅ |
| API clients and SDKs | M2-L12 | ✅ |
| Async programming and concurrency | M2-L13 | ✅ |
| Timeouts, retries, exponential backoff, rate limits | M2-L14 | ✅ |
| FastAPI and request/response schemas | M2-L15 | ✅ |
| SQL fundamentals and database access | M2-L16 | ✅ |
| Git and dependency management | M2-L17 | ✅ |
| Logging and testing | M2-L18 | ✅ |
| Secret handling | M2-L19 | ✅ |
| Docker fundamentals | M2-L20 | ✅ |
| **Project: validated support-ticket API with error handling** | `projects/project-02-ticket-api/` | ✅ 41 tests pass |

**Added beyond the requested syllabus:**

| Addition | Lesson | Why |
|---|---|---|
| Idempotency keys | M2-L11 §5.6 | Required before agent duplicate-prevention (M8-L12) |
| `MockTransport` testing | M2-L12 §5.6 | How every API-dependent test in this course avoids the network |
| Bounding concurrency with a semaphore | M2-L13 §5.6 | Unbounded `gather` measured as *slower* and unsafe |
| Thundering herd and jitter | M2-L14 §5.3 | Backoff without jitter can sustain an outage |
| Token bucket vs semaphore | M2-L14 §5.8 | Rate limits and concurrency limits are different constraints |
| `404` vs `403` for resource enumeration | M2-L15 §6 | A deliberate security/debuggability trade-off |
| Path traversal defence | M2-L09 §9 | Needed before MCP tools expose file access (M9-L13) |
| Asserting privacy properties in tests | M2-L18 §6 | Makes governance commitments executable (M10-L12) |

---

## Modules 2–15 — planned

Rows are filled in as each module is written. The full item list is in
[`COURSE_PLAN.md`](COURSE_PLAN.md) §4, and current build state is in
[`GENERATION_STATUS.md`](GENERATION_STATUS.md).

| Module | Syllabus items | Lessons planned | Status |
|---|---|---|---|
| M2 Python and Software Foundations | 17 | 20 + project | ✅ |
| M3 Mathematics and ML Essentials | 15 | 14 + project | ✅ |
| M4 Generative AI and LLM Internals | 23 | 18 + project | ✅ |
| M5 Prompting and LLM Applications | 18 | 18 + project | ⬜ |
| M6 Embeddings and Search | 15 | 13 + project | ⬜ |
| M7 Retrieval-Augmented Generation | 23 | 20 + project | ⬜ |
| M8 Agentic AI | 20 | 18 + project | ⬜ |
| M9 Model Context Protocol | 19 | 16 + project | ⬜ |
| M10 AI Governance and Security | 22 | 16 + project | ⬜ |
| M11 AWS Foundations | 20 | 18 + project | ⬜ |
| M12 AI on AWS | 15 | 14 + project | ⬜ |
| M13 Fine-Tuning and Production | 17 | 14 + project | ⬜ |
| M14 FDE and Delivery Skills | 15 | 12 + exercise | ⬜ |
| M15 Capstone | 13 capabilities, 14 deliverables | 8 units | ⬜ |

---

## Module 3 — Mathematics and ML Essentials

| Syllabus item | Covered in | Status |
|---|---|---|
| Vectors, matrices, shapes | M3-L01 §5.1–5.4 | ✅ |
| Broadcasting and axis semantics | M3-L01 §5.5–5.6 | ✅ |
| Dot product and norms | M3-L02 §5.1–5.2 | ✅ |
| Cosine similarity | M3-L02 §5.3–5.5 | ✅ |
| Descriptive statistics, percentiles | M3-L03 §5.1–5.4 | ✅ |
| Sampling variability, standard error | M3-L03 §5.5; M3-L13 §5.4 | ✅ |
| Probability, conditional probability | M3-L04 §5.1–5.3 | ✅ |
| Bayes' theorem and base rates | M3-L04 §5.4–5.5 | ✅ |
| Logarithms and log-space arithmetic | M3-L05 §5.1–5.2 | ✅ |
| Entropy, cross-entropy, perplexity | M3-L05 §5.3–5.6 | ✅ |
| Derivatives, gradients, chain rule | M3-L06 §5.1–5.5 | ✅ |
| Differentiability and why it matters | M3-L06 §5.6 | ✅ |
| Loss functions (MSE, MAE, cross-entropy) | M3-L07 §5.2–5.4 | ✅ |
| Gradient descent | M3-L07 §5.5–5.6 | ✅ |
| Linear regression | M3-L08 (whole lesson) | ✅ |
| Logistic regression, sigmoid, softmax | M3-L09 (whole lesson) | ✅ |
| Softmax temperature | M3-L09 §5.6 | ✅ |
| Neural network structure and activations | M3-L10 §5.1–5.4 | ✅ |
| Initialisation, dead units, parameter counting | M3-L10 §5.5–5.7 | ✅ |
| Backpropagation | M3-L11 §5.1–5.4, §6 | ✅ |
| Gradient checking | M3-L11 §5.5 | ✅ |
| Vanishing and exploding gradients | M3-L10 §5.3; M3-L11 §5.6 | ✅ |
| Learning rate, epochs, batches | M3-L12 §5.1–5.3 | ✅ |
| Momentum, Adam, schedules, clipping | M3-L12 §5.4–5.7 | ✅ |
| Train/validation/test splitting | M1-L06; M3-L13 §5.1 | ✅ |
| Stratification and grouped splits | M3-L13 §5.2–5.3 | ✅ |
| Cross-validation, temporal splits | M3-L13 §5.5–5.6 | ✅ |
| Class imbalance handling | M3-L13 §5.7 | ✅ |
| Confusion matrix, precision, recall, F1 | M3-L14 §5.1–5.2 | ✅ |
| ROC-AUC vs PR-AUC | M3-L14 §5.3 | ✅ |
| Threshold selection | M3-L14 §5.4 | ✅ |
| Calibration and ECE | M3-L14 §5.5 | ✅ |
| Baselines | M3-L14 §5.6 | ✅ |
| Regression metrics | M3-L14 §5.7 | ✅ |
| Macro/micro averaging | M3-L14 §5.8 | ✅ |
| Reproducibility and seeding | M3-L14 §5.9; Project 3 tests | ✅ |
| **End-to-end classifier build** | Project 3 (98 tests) | ✅ |

---

## Module 4 — Generative AI and LLM Internals

| Syllabus item | Covered in | Status |
|---|---|---|
| Foundation models, generative vs discriminative | M4-L01 §5.1–5.2 | ✅ |
| Pretrain-adapt pattern; the four adaptation methods | M4-L01 §5.3–5.4 | ✅ |
| Emergent capabilities; open weights vs open source | M4-L01 §5.5, §5.7 | ✅ |
| Modalities: text, image, audio, video | M4-L02 §5.1–5.4 | ✅ |
| Multimodal architectures; diffusion vs autoregressive | M4-L02 §5.5–5.6 | ✅ |
| Tokens, tokenizers, BPE, vocabularies, token IDs | M4-L03 §5.1–5.2 | ✅ |
| Token cost, tokenizer equity, special tokens | M4-L03 §5.3–5.7 | ✅ |
| Embeddings: static vs contextual, pooling, anisotropy | M4-L04 §5.1–5.6 | ✅ |
| Next-token prediction end to end; shapes | M4-L05 §5.1–5.2 | ✅ |
| Teacher forcing, causal mask, loss, perplexity | M4-L05 §5.3–5.5 | ✅ |
| Prefill vs decode | M4-L05 §5.6; M4-L17 §3.2 | ✅ |
| Context windows, budgets, truncation strategies | M4-L06 §5.1–5.3 | ✅ |
| Lost in the middle; `max_tokens`; KV cache growth | M4-L06 §5.4–5.6 | ✅ |
| Attention: the core idea, Q/K/V, scaling | M4-L07 §5.1–5.2 | ✅ |
| Permutation invariance; self vs cross-attention | M4-L07 §5.3–5.4 | ✅ |
| Multi-head attention; attention as (non-)explanation | M4-L07 §5.5–5.6 | ✅ |
| Full multi-head computation, worked by hand | M4-L08 §6 | ✅ |
| Positional encoding: learned, sinusoidal, RoPE, ALiBi | M4-L09 §5.1–5.5 | ✅ |
| Context extension and its cost | M4-L09 §5.6 | ✅ |
| Transformer block: FFN, residuals, normalisation | M4-L10 §5.1–5.3 | ✅ |
| Pre-norm vs post-norm; parameter counting | M4-L10 §5.4–5.5 | ✅ |
| Encoder / decoder / encoder-decoder | M4-L11 §5.1–5.4 | ✅ |
| Pretraining, data, scaling laws | M4-L12 §5.1–5.2 | ✅ |
| SFT, chat templates, catastrophic forgetting | M4-L12 §5.3–5.5 | ✅ |
| RLHF, reward models, DPO | M4-L13 §5.1–5.3 | ✅ |
| Reward hacking, sycophancy, what alignment guarantees | M4-L13 §5.5–5.6 | ✅ |
| Decoding: temperature, top-k, top-p, min-p | M4-L14 §5.1–5.4 | ✅ |
| Determinism, repetition penalties, beam search | M4-L14 §5.6–5.8 | ✅ |
| Stop conditions, `finish_reason`, truncation handling | M4-L15 §5.1–5.6 | ✅ |
| Training knowledge vs runtime context; statelessness | M4-L16 §5.1–5.4 | ✅ |
| Serving: quantization, KV cache, batching, metrics | M4-L17 §5.1–5.5 | ✅ |
| Speculative decoding; OOM diagnosis | M4-L17 §5.6–5.7 | ✅ |
| Hosted vs local: the seven axes, break-even, licensing | M4-L18 §5.1–5.5 | ✅ |
| **Reproducible behaviour comparison harness** | Project 4 (65 tests) | ✅ |

---

## Module 5 — Prompting and LLM Application Engineering (in progress)

| Item | Where | Status |
|---|---|---|
| Prompt anatomy: instruction, context, examples, input | M5-L01 §5.1–5.4 | ✅ |
| Prompt injection baseline measurement | M5-L01 §7.3 | ✅ |
| Message roles; instruction priority is learned, not enforced | M5-L02 §5.1–5.3 | ✅ |
| Special-token forgery and encoding defences | M5-L02 §7.3 | ✅ |
| System prompts are not secret | M5-L02 §5.4 | ✅ |
| Zero-shot vs few-shot; label coverage rule | M5-L03 §5.1 | ✅ |
| Example selection strategies at equal cost | M5-L03 §5.2, §7.3 | ✅ |
| Majority-label, recency, format lock-in, difficulty bias | M5-L03 §5.3 | ✅ |
| Few-shot cost per unit of quality; few-shot vs fine-tuning | M5-L03 §5.5–5.6 | ✅ |
| Error compounding across steps (`p^n`) | M5-L04 §5.1 | ✅ |
| Decomposition measured against a usability bar | M5-L04 §5.2 | ✅ |
| Error propagation; absence of self-correction | M5-L04 §5.3 | ✅ |
| Self-consistency and the error-independence assumption | M5-L04 §5.4 | ✅ |
| Verification of working vs answer | M5-L04 §5.5 | ✅ |
| One call vs several; chain-of-thought faithfulness | M5-L04 §5.6, §5.8 | ✅ |
| Untrusted content inventory | M5-L05 §3.2 | ✅ |
| Round-trip boundary test | M5-L05 §5.1 | ✅ |
| Nonce delimiters; escaping as data corruption | M5-L05 §5.2–5.3 | ✅ |
| Boundary confusion vs instruction compliance | M5-L05 §5.5 | ✅ |
| Parsing vs validation | M5-L06 §3.1 | ✅ |
| Real model output failure catalogue; safe repair | M5-L06 §5.1–5.2 | ✅ |
| Pydantic strict mode, coercion, `extra="forbid"` | M5-L06 §5.3 | ✅ |
| Schema as a control; JSON mode's actual guarantee | M5-L06 §5.4, §5.6 | ✅ |
| Schema complexity vs compliance | M5-L06 §5.5 | ✅ |
| Transient vs systematic failure classification | M5-L07 §3.1, §5.3 | ✅ |
| `ValidationError` contents and the `include_input` switch | M5-L07 §5.1 | ✅ |
| Feedback message design and cost | M5-L07 §5.2 | ✅ |
| Retry budgets: attempts, deadline, cost | M5-L07 §5.4–5.5 | ✅ |
| Degrade / escalate / fail | M5-L07 §5.6 | ✅ |
| M5-L08 … M5-L18 items | — | ⬜ TODO |

---

## Verification note

This matrix is only meaningful if it is honest. A row is marked ✅ **only** when the named lesson
contains a substantive explanation of that item — not a mention, not a forward reference. Where an
item is split across lessons, every location is listed.

The final completeness check described in the brief is performed against this file once all modules
are written, and the result recorded in [`GENERATION_STATUS.md`](GENERATION_STATUS.md).
