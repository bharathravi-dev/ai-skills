# GENERATION_STATUS.md

**Last updated:** 2026-09-09 (Modules 1–4 COMPLETE incl. Project 4; Module 5 IN PROGRESS — 7 of 18 lessons)
**Course root:** `/home/bharathr/self/Learning/claude/ai`

This file tracks what has actually been written. A file is only listed as **DONE** when it contains
complete teaching material — never when it is an outline, a heading skeleton, or a placeholder.

---

## Legend

| Status | Meaning |
|---|---|
| DONE | Complete lesson: all applicable template sections, worked example, code, exercises, quiz |
| IN PROGRESS | Currently being written |
| TODO | Not started |

---

## Scaffolding

| File | Status |
|---|---|
| README.md | DONE |
| COURSE_PLAN.md | DONE |
| GENERATION_STATUS.md | DONE (living file) |
| COVERAGE_MATRIX.md | DONE for M1–M3; rows added per module |
| PROGRESS_TRACKER.md | DONE for M1–M3; rows added per module |
| GLOSSARY.md | DONE for M1–M3 (180 terms, merged alphabetically); grows with each module |
| requirements.txt / .env.example / .gitignore | DONE |
| references/STUDY_SCHEDULE.md | **DONE** (492 course hours, 45 weeks at 11 h/wk) |

---

## Module completion summary

| Module | Lessons planned | Lessons DONE | Project | Assessment | Answer key |
|---|---|---|---|---|---|
| M1 AI Foundations | 11 | **11 ✅** | n/a | **DONE** | **DONE** |
| M2 Python and Software | 20 | **20 ✅** | **DONE** | **DONE** | **DONE** |
| M3 Math and ML Essentials | 14 | **14 ✅** | **DONE** (98 tests) | **DONE** | **DONE** |
| M4 GenAI and LLM Internals | 18 | **18 ✅** | **DONE** (65 tests) | **DONE** | **DONE** |
| M5 Prompting and LLM Apps | 18 | 0 | TODO | TODO | TODO |
| M6 Embeddings and Search | 13 | 0 | TODO | TODO | TODO |
| M7 RAG | 20 | 0 | TODO | TODO | TODO |
| M8 Agentic AI | 18 | 0 | TODO | TODO | TODO |
| M9 MCP | 16 | 0 | TODO | TODO | TODO |
| M10 Governance and Security | 16 | 0 | TODO | TODO | TODO |
| M11 AWS Foundations | 18 | 0 | TODO | TODO | TODO |
| M12 AI on AWS | 14 | 0 | TODO | TODO | TODO |
| M13 Fine-tuning and Production | 14 | 0 | TODO | TODO | TODO |
| M14 FDE Delivery | 12 | 0 | TODO | TODO | TODO |
| M15 Capstone | 8 units | 0 | — | TODO | TODO |
| **Total** | **214** | **37** | 1/14 | 2/15 | 2/15 |

---

## Module 1 — completed artefacts

11 lessons (53,725 words), 11 runnable labs, all **executed** in this environment with real output
pasted into the lessons. Assessment (15 questions + practical, 40 marks), revision guide, and a
12,000-word answer key with reasoning for every distractor and rubrics for every open question.

| Lesson | Words | Lab | Executed |
|---|---|---|---|
| M1-L01 | 4,960 | `labs/m1/l01_taxonomy_quiz.py` | ✅ |
| M1-L02 | 5,902 | `labs/m1/l02_rules_vs_learned.py` | ✅ |
| M1-L03 | 4,185 | `labs/m1/l03_task_shapes.py` | ✅ |
| M1-L04 | 4,862 | `labs/m1/l04_dataset_anatomy.py` | ✅ |
| M1-L05 | 4,409 | `labs/m1/l05_hyperparameter_sort.py` | ✅ |
| M1-L06 | 5,007 | `labs/m1/l06_splitting.py` | ✅ |
| M1-L07 | 5,034 | `labs/m1/l07_self_supervision.py` | ✅ |
| M1-L08 | 4,775 | `labs/m1/l08_overfitting.py` | ✅ |
| M1-L09 | 4,742 | `labs/m1/l09_leakage.py` | ✅ |
| M1-L10 | 4,963 | `labs/m1/l10_calibration.py` | ✅ |
| M1-L11 | 4,886 | `labs/m1/l11_reliability_calculator.py` | ✅ |

Every exercise whose answer depends on running modified code was itself verified by running that
modification (M1-L02 ex2, M1-L05 ex3, M1-L06 ex2.5, M1-L08 ex2.3/2.4, M1-L10 ex2.4). The answer key
quotes the real measured results.

---

## Module 2 — COMPLETE (20 lessons + project + assessment + answer key)

All 20 lessons written (~90,000 words), all 20 labs **executed** with real output pasted in.

| Lesson | Lab | Executed |
|---|---|---|
| L01 Terminal, Python, venv, pip | `l01_doctor.py` | ✅ 3 scenarios |
| L02 Variables, numbers, strings | `l02_types_and_strings.py` | ✅ |
| L03 Collections | `l03_collections.py` | ✅ |
| L04 Control flow, comprehensions | `l04_control_flow.py` | ✅ |
| L05 Functions, arguments, scope | `l05_functions.py` | ✅ |
| L06 Modules and project layout | `l06_demo/` (real package) | ✅ 3 scenarios |
| L07 Classes and dataclasses | `l07_classes.py` | ✅ |
| L08 Type hints and Pydantic v2 | `l08_pydantic.py` | ✅ venv |
| L09 Files, CSV, JSON, env vars | `l09_files.py` | ✅ venv |
| L10 Exceptions and debugging | `l10_exceptions.py` | ✅ |
| L11 HTTP and REST | `l11_http.py` (local server) | ✅ |
| L12 API clients with httpx | `l12_httpx.py` | ✅ venv |
| L13 Async and concurrency | `l13_async.py` | ✅ venv |
| L14 Retries, backoff, rate limits | `l14_retries.py` | ✅ venv |
| L15 FastAPI | `l15_fastapi.py` (TestClient) | ✅ venv |
| L16 SQL | `l16_sql.py` (20k rows) | ✅ |
| L17 Git and dependencies | `l17_git.sh` (real repo) | ✅ git 2.43.0 |
| L18 Logging and pytest | `l18_logging_testing.py` | ✅ venv |
| L19 Secret handling | `l19_secrets.py` | ✅ |
| L20 Docker | `l20_docker.sh` (real build) | ✅ Docker 29.2.1 |

**Project 2** — `projects/project-02-ticket-api/`, 17 files.
`[EXECUTED]` **41 tests pass**; the server was smoke-tested with real HTTP requests; the Docker image
was built, run as non-root, verified free of secrets in its history, and removed.

**Assessment** (20 questions + practical, 60 marks), **revision guide**, and a **6,500-word answer
key** with reasoning for every distractor and rubrics for every open question.

---

### Notable corrections made because execution contradicted the draft

These are recorded because the same discipline must continue:

- **M2-L02** — my claim that `257 is 257` is `False` was wrong: constant interning inside one code
  object makes it `True`. Rewritten to separate interning from the small-int cache using
  `int("257")`.
- **M2-L04** — the mutation-during-iteration demo on `[1,2,3,4]` produced the *correct* answer by
  luck, hiding the bug. Changed to `[2,4,6,8]`, which visibly leaves `[4, 8]`.
- **M2-L12** — pooling initially showed no benefit; the cause was Nagle's algorithm plus delayed ACKs
  adding ~40 ms per request on loopback. With `disable_nagle_algorithm` the real result is ~28×.
- **M2-L13** — unbounded `gather` turned out to be **3× slower** than `semaphore(10)` because it
  saturates the server. The lesson was rewritten around that measured finding.
- **M2-L14** — added a deadline check *before* sleeping, after observing the retry sleep 3 s only to
  then discover the deadline had passed.

---

## Module 3 — in progress (6 of 14)

| Lesson | Words | Lab | Executed |
|---|---|---|---|
| M3-L01 Scalars, vectors, matrices, shapes | 4,931 | `l01_arrays.py` | ✅ |
| M3-L02 Dot products, norms, cosine similarity | 4,870 | `l02_similarity.py` | ✅ |
| M3-L03 Mean, variance, distributions | 4,582 | `l03_statistics.py` | ✅ |
| M3-L04 Probability and conditional probability | 4,768 | `l04_probability.py` | ✅ |
| M3-L05 Logarithms, cross-entropy, perplexity | 5,041 | `l05_entropy.py` | ✅ |
| M3-L06 Derivatives, gradients, chain rule | 5,289 | `l06_derivatives.py` | ✅ |

### Notable findings from execution (Module 3)

- **M3-L02** — un-normalised dot product measurably **inverts** the correct ranking; normalising at
  index time then using a plain dot product is **40.6× faster** and gives identical results.
- **M3-L03** — simulated two *identical* 80%-accurate prompts: at n=100 they appear to differ by
  >3 points **61% of the time**. Small eval sets manufacture differences.
- **M3-L05** — probability products underflow to exactly 0.0 at **n=324** multiplications.
- **M3-L06** — the central difference is **exact for quadratics** (its error depends on the third
  derivative), so the h-sweep had to use `e^x` to show the real accuracy trade-off.

---

## ENVIRONMENT NOTE (important for resuming)

The scratchpad venv used to execute labs lives **outside** the course repo and was wiped once during
generation. If `$SCRATCH/venvtest/bin/python` is missing, rebuild it before running any lab:

```bash
python3 -m venv "$SCRATCH/venvtest"
"$SCRATCH/venvtest/bin/pip" install numpy==2.5.3 scikit-learn==1.9.0 pydantic==2.13.5 \
  fastapi==0.141.1 uvicorn==0.52.4 httpx==0.28.1 pytest==9.1.1 python-dotenv==1.2.3 \
  rank-bm25==0.2.2 tiktoken==0.14.0
```

These are the exact versions every `[EXECUTED]` output in the course was produced with.

---

---

## Module 3 completion record (2026-09-08)

**14 lessons, ~66,000 words. 14 labs, all `[EXECUTED]`. Project 3: 98 tests passing.**

| Artefact | Detail |
|---|---|
| Lessons | `modules/module-03-math-ml-essentials/M3-L01` … `M3-L14` |
| Labs | `labs/m3/l01_*.py` … `l14_metrics.py` — every one executed, output pasted into §7.2 |
| Project 3 | `projects/project-03-classifier/` — 7 source modules, 6 test modules, **98 tests** |
| Assessment | `assessments/module-03-assessment.md` — 71 marks |
| Revision guide | `assessments/module-03-revision.md` |
| Answer key | `answer-keys/module-03-answers.md` — ~6,900 words |

### Lessons rewritten because execution contradicted the draft

The discipline stated in the brief — verify before asserting — changed the following:

| Lesson | Draft claimed | Execution showed | Action |
|---|---|---|---|
| M3-L11 §6 | Loss falls 0.2069 → 0.1907 after one step | **0.2070 → 0.1499** | Corrected, and added why (all nine parameters move at once) |
| M3-L11 §5.5 | Gradient checking catches bugs | A missing ReLU mask **passed at 4.94e-11** on an input where every unit was active | Promoted to a new subsection; became the lesson's headline result and quiz Q10 |
| M3-L12 §3 | Training costs 2–3× inference | **1.46×** measured for 1M params | Reported the measurement, kept 2–3× as the planning figure with the reason for the gap |
| M3-L12 §5.6 | Warmup + cosine improves results | **Constant LR reached a lower final loss**; cosine's gain was 30× smaller end-of-run swing | Rewrote as "schedules buy stability, not necessarily a lower loss" |
| M3-L12 lab §4 | SGD/momentum/Adam on a logistic problem | Differences were negligible (0.3939 vs 0.3938 vs 0.3880) | Replaced with an ill-conditioned quadratic: **Adam 125 steps vs SGD 3,450**, SGD diverging 10% above the stability limit |
| M3-L12 lab §6 | Clipping prevents divergence | The original set-up never diverged | Replaced with one poisoned row in 512: unclipped → weights ±2e+221 and `nan`; clipped → recovers the true weights |
| M3-L13 §6 | Illustrative fraud numbers | Replaced entirely with measured ones | Now every figure in the worked example is from the lab |
| M3-L13 lab §3 | Grouped split would show a gap | Only 1.8 points with no identity feature | Redesigned with a customer-id feature → **16.7-point** gap |
| M3-L14 §6 | Illustrative threshold table | Replaced with the measured sweep | The highest-accuracy threshold catches **4 of 87** fraud cases |
| M3-L14 lab §3 | "FPR looks negligible" | FPR was 0.39 — not negligible at all | Reselected the threshold at FPR = 2%; precision there is **0.1777** |
| Project 3 §7 | A random split would inflate the score | **−0.023** — it did not | Kept the negative result, explained the missing mechanism, and **added** a target-encoding leak that does inflate it (+0.0871) |

### Defect found and fixed across the whole course

**Answer leakage in quizzes.** An audit found **44 option lines across 20 files** where the correct
option carried `**bold**` emphasis, marking the answer inline. All were stripped. The Module 3
assessment additionally had its Section A options rewritten to uniform length and its answer
distribution rebalanced (was A1/B5/C7/D0, now **A5/B1/C3/D4**).

**Known remaining limitation, stated in the answer key.** M1–M3 *lesson* quizzes still tend to place
the correct option at position B, and their correct options are longer and more explanatory than the
distractors. They are formative self-checks and are labelled as such; the **module assessments are the
graded instruments** and are clean. From Module 4 onward, lesson quiz options are written to uniform
length with a balanced answer distribution.

### Cost and safety compliance

- **£0.00 / $0.00 spent.** No cloud resource was provisioned at any point. Every M3 lab and Project 3
  runs on a local CPU.
- **No credentials anywhere.** Project 3 has a test (`test_no_secrets_or_credentials_in_the_package`)
  asserting no module mentions `api_key`, `secret`, `password` or `aws_access`.
- **All data synthetic**, deterministic from a seed, generated in-repo.

---

---

## Module 4 completion record (2026-09-09)

**18 lessons, ~93,000 words. 18 labs, all `[EXECUTED]`. Project 4: 65 tests passing.**

| Artefact | Detail |
|---|---|
| Lessons | `modules/module-04-genai-llm-internals/M4-L01` … `M4-L18` |
| Labs | `labs/m4/l01_*.py` … `l18_hosted_vs_local.py` — every one executed, output pasted into §7.2 |
| Project 4 | `projects/project-04-model-comparison/` — 6 source modules, 5 test modules, **65 tests** |
| Assessment | `assessments/module-04-assessment.md` — 76 marks |
| Revision guide | `assessments/module-04-revision.md` |
| Answer key | `answer-keys/module-04-answers.md` — ~14,400 words |

### Lessons corrected because execution contradicted the draft (18 cases)

| Lesson | Draft claimed | Measured | Action |
|---|---|---|---|
| L03 §5.3 | English ≈4.0–4.5 chars/token | **5.54** | Rule of thumb overestimates cost ~39% |
| L03 §5.3 | Technical English worse than prose | **5.56 — identical** | A 100k vocabulary contains the jargon |
| L03 §5.3 | Code ~2.5–3.5 chars/token | **4.98** | Modern tokenizers have absorbed code |
| L03 lab | Byte truncation corrupts text | No corruption — every cut was in ASCII | Rewrote to scan all cut points: **24% break** |
| L04 §5.5 | Unmasked padding always degrades | **Exactly 0.0000** with zero pad under cosine | Harmless with zero pad + equal lengths (what tests use); **−0.05 → 0.97** with a learned pad |
| L04 lab | Anisotropy inflates similarity | 0% above 0.8 — shared component too weak | Raised it; now **0.7787 mean, 13.4% above 0.8** |
| L05 lab | Causal-mask removal collapses loss | **5%** — attention weights were never trained | Added full backprop; now **0.2160 vs 0.0006** |
| L06 §5.3 | Head+tail truncation "keeps the most" | **All three tie at 3/9** | Strategies differ in *which* part, never *how much* |
| L07 lab | Scaling prevents gradient collapse | `max` of `w(1−w)` showed nothing | Switched to the **mean**; clean **483×** collapse |
| L08 §6.9 | head 1 row 2 = `[0.2887, 0.4226, 0.2887]` | **`[0.2920, 0.4159, 0.2920]`** | My hand arithmetic was wrong; the assertion caught it |
| L09 lab §4 | Table showing extrapolation degradation | Constant 0.9662 — **constant by construction** | Rewrote to state what it can and cannot measure |
| L10 §5.6 | "Every component is load-bearing" | Removing the **FFN and norm made the toy model better** | Rewrote: components earn their place at different **scales** |
| L11 lab §4 | Linear probe on representations | **No train/test split** — pure overfitting | Added held-out split (M3-L13); encoder 0.6212 vs decoder 0.5125 vs baseline 0.5200 |
| L13 lab §3 | KL sweep shows reward hacking | **Identical rows** — β never exceeded the reward gradient | Normalised reward to unit norm; real trade appeared |
| L14 §6.2 | `T=0.5` and `T=2.0` softmax columns | Both **wrong** | Assertion caught it; corrected against the lab |
| L14 §6.6 | top-p 0.9 fails to protect at `T=2.0` | **Holds to `T≈3.0`** | Corrected, and generalised: the danger is plausible-but-wrong tokens, which rank *inside* the nucleus |
| L15 §5.4 | Truncated tool calls "may still parse" | Raw truncations **almost never parse** | Rewrote around the real danger: the **brace-repair pattern**, which produces `{"action": "delete_records"}` with no filter |
| L16 §2 | Context overrides weak parametric belief | **Context never wins at any level** | Reported the negative result: in-context learning is a capability that emerges at scale, not an instruction |

**Six of these are cases where the experiment could not detect the effect rather than the effect being
absent** (L05, L07, L09, L11, L13, L16). Each is recorded in the lesson as a methodological point.
Two (L08, L14) were errors in my own hand arithmetic that a lab assertion caught — which is the
argument those lessons make, demonstrated on themselves.

### Cost and safety compliance

- **£0.00 / $0.00 spent.** No cloud resource, no API key, no network call in any M4 lab or in
  Project 4. Project 4 has **8 tests asserting it cannot** — no network library imported, no credential
  pattern in any source file, `.env.example` empty, `RealProvider` refuses without a key.
- **All prices in course material are labelled ILLUSTRATIVE and dated**, with the caveat that a billing
  alert notifies rather than caps.
- **All data synthetic.** No real customer, employer or learner data anywhere.

### Quiz answer distributions (uniform-length options, no inline explanations)

| Lesson | A | B | C | D | | Lesson | A | B | C | D |
|---|---|---|---|---|---|---|---|---|---|---|
| L01 | 2 | 2 | 3 | 3 | | L10 | 2 | 4 | 2 | 2 |
| L02 | 3 | 3 | 1 | 3 | | L11 | 2 | 1 | 4 | 3 |
| L03 | 3 | 2 | 2 | 3 | | L12 | 3 | 2 | 3 | 2 |
| L04 | 2 | 1 | 4 | 3 | | L13 | 3 | 4 | 2 | 1 |
| L05 | 3 | 3 | 3 | 1 | | L14 | 2 | 2 | 4 | 2 |
| L06 | 2 | 2 | 3 | 3 | | L15 | 3 | 3 | 3 | 1 |
| L07 | 2 | 2 | 4 | 2 | | L16 | 3 | 2 | 2 | 3 |
| L08 | 2 | 2 | 4 | 2 | | L17 | 1 | 5 | 3 | 1 |
| L09 | 2 | 2 | 4 | 2 | | L18 | 1 | 2 | 4 | 3 |

Module 4 assessment Section A: **A2 / B4 / C5 / D3**.

---

## Module 5 — Prompting and LLM Application Engineering (IN PROGRESS)

| Lesson | Title | Words | Lab | Answer key |
|---|---|---|---|---|
| M5-L01 | Anatomy of a Prompt | 5,138 | `labs/m5/l01_prompt_anatomy.py` | DONE |
| M5-L02 | Message Roles and Instruction Priority | 4,736 | `labs/m5/l02_message_roles.py` | DONE |
| M5-L03 | Zero-shot, Few-shot and Example Selection | 6,035 | `labs/m5/l03_few_shot.py` | DONE |
| M5-L04 | Task Decomposition and Reasoning Prompts | 6,584 | `labs/m5/l04_decomposition.py` | DONE |
| M5-L05 | Delimiters and Handling Untrusted Content | 5,921 | `labs/m5/l05_delimiters.py` | DONE |
| M5-L06 | Structured Outputs and JSON Schemas | 5,677 | `labs/m5/l06_structured_output.py` | DONE |
| M5-L07 | Output Validation and Repair Loops | 5,938 | `labs/m5/l07_validation_repair.py` | DONE |
| M5-L08 … M5-L18 | — | — | — | TODO |
| Project 5 | Ticket Classifier and Summarizer | — | — | TODO |
| Assessment + revision | 20 questions | — | — | TODO |

**Module 5 lessons written: 7 / 18.** All seven labs executed; all lesson numbers come from those
executions.

### Corrections made in Module 5 so far

| Lesson | What the draft claimed | What execution showed |
|---|---|---|
| M5-L01 | Reproducible lab | Seeded with Python `hash()` — randomised per process. Fixed to `zlib.crc32`. |
| M5-L01 | Injection rate 0% at n=20 | Re-measured at n=2,000: **5.1%, CI 4.1–6.1%** |
| M5-L03 | "Most benefit in the first 2–4 examples" | 1 and 2 examples scored **below zero-shot**; the cause is label coverage, not count (63.8% vs 77.7% at a fixed count of 4) |
| M5-L03 | Example-count sweep | Naive design confounded count with selection; rebuilt with nested sets over 8 draws |
| M5-L03 | Recency from forward-vs-reversed | Two orderings cannot establish an ordering effect; measured all 24 (**14.1-point spread**) |
| M5-L04 | Self-consistency helps | Only under independent errors: **+30.0 / +1.5 / +0.0** points; agreement is **highest where it helps least** |
| M5-L04 | Decomposition gain grows with length | True, and at an 80% usability bar **no** chain length changed verdict |
| M5-L05 | `---` delimiter comparison | My parser was broken (0/10 on clean input); fixed, and every strategy attacked with its own marker |
| M5-L05 | Round-trip ranking | "No delimiter" scored 94% — a warning about the metric, not an endorsement |
| M5-L06 | — | Brace-balancing added **0** correct results and **2** wrong ones |
| M5-L07 | — | 6/6 pydantic error sets carry the input value; a `missing` error carries the **whole object** |

---

## Exact next step

Continue Module 5 at `modules/module-05-prompting-llm-apps/M5-L08-tools.md`
(Tool Definitions and Tool-Call Arguments), following [`COURSE_PLAN.md`](COURSE_PLAN.md).

Every lesson must still run without an API key (design assumption A6). The strongest Module 5 labs so
far are the ones that measure **real libraries** rather than a mock — M5-L05 §1–3 (a real assembler and
parser), M5-L06 §1–4 (stdlib `json` and pydantic) and M5-L07 §1–2 (pydantic error structure). Prefer
that pattern where the subject allows it, and label mock sections explicitly.
