# Module 1 Assessment — AI Foundations

| | |
|---|---|
| **Covers** | M1-L01 … M1-L11 |
| **Questions** | 15 (10 multiple choice, 5 short answer) + 1 practical assignment |
| **Total marks** | 40 |
| **Pass mark** | 28 (70%) |
| **Time** | ~90 minutes (60 for Sections A–B, 30 for Section C) |
| **Answer key** | [`answer-keys/module-01-answers.md`](../answer-keys/module-01-answers.md#module-assessment) — do not open until finished |

**Conditions.** Closed book. Do not re-read the lessons while answering. If you find yourself
guessing on more than three questions in Section A, stop, revise, and return another day — the score
is only useful if it reflects what you actually retained.

---

## Section A — Recall and understanding (10 marks, 1 each)

**A1.** What single property most fundamentally separates a rule-based system from a learned one?

- A. Whether it runs on specialised hardware.
- B. Whether the output is text or a number.
- C. Where the decision logic came from — a human writing it, or a fitting procedure over data.
- D. Whether it is deployed as a service.

**A2.** A support system must answer "which of our 4,000 known issues does this ticket match?" The
issue list changes weekly. What task shape is this?

- A. Multi-class classification  B. Ranking / retrieval
- C. Clustering  D. Regression

**A3.** You set `k = 5` for the number of chunks your RAG system retrieves. What is `k`?

- A. A parameter, because it affects the output.
- B. Neither — it is an input.
- C. A hyperparameter, because you set it before running and it changes system behaviour.
- D. A parameter, because it is stored in configuration.

**A4.** How many times should a test set be used?

- A. Once per training run.
- B. Once, on data that played no part in any decision.
- C. As often as needed to tune the model.
- D. Never — validation is sufficient.

**A5.** A model is trained by hiding random words in a corpus and predicting them. Which paradigm is
this?

- A. Supervised  B. Self-supervised  C. Unsupervised  D. Reinforcement

**A6.** A model scores 97% on training data and 71% on validation data. This is:

- A. Underfitting  B. A good fit  C. Overfitting  D. Data leakage

**A7.** You are predicting whether a loan will default, and the feature list includes
`collections_agency_assigned`. What is the problem?

- A. The feature has too many categories.
- B. Target leakage — the field is populated as a consequence of the outcome being predicted.
- C. Temporal leakage from a future aggregate.
- D. There is no problem; it is highly predictive.

**A8.** An LLM outputs "I am 92% confident this is correct." What does that number tell you?

- A. Its internal probability for the answer is 0.92.
- B. It will be right 92% of the time on this class of question.
- C. Its calibration error is 8%.
- D. Nothing measurable — it is generated text, not a report of an internal probability.

**A9.** A pipeline has five required steps, each succeeding 90% of the time. What is the approximate
end-to-end success rate?

- A. 90%  B. 59%  C. 45%  D. 72%

**A10.** A model scores 64% on training data and 63% on validation data. What should you do?

- A. Add L2 regularisation to close the gap.
- B. Collect more training data to reduce overfitting.
- C. Increase model capacity, train longer, or improve the features.
- D. Stop training earlier.

---

## Section B — Short answers (15 marks, 3 each)

Answer in 3–5 sentences each. Marks are for precision, not length.

**B1.** Why is data leakage considered more dangerous than overfitting? *(3 marks)*

**B2.** A colleague's model scores 100% on training, validation and test data. What do you conclude,
and what specific check do you run first? *(3 marks)*

**B3.** Explain, starting from the training objective, why a language model produces confident false
statements. *(3 marks)*

**B4.** Your pipeline has six model steps, each succeeding 95% of the time. State the end-to-end
reliability with your working, and give two distinct ways to improve it. *(3 marks)*

**B5.** Name two categories of decision that should never be delegated to a model, and give the
underlying reason. *(3 marks)*

---

## Section C — Practical assignment (15 marks)

**Scenario.**

> A logistics company comes to you. "We want an AI system that predicts which deliveries will be
> late, so we can warn customers proactively. We have four years of delivery records."

You have not seen their data. Produce a **one-page design note** covering all seven items below.
Be specific: a note that could apply to any project scores poorly.

| # | Deliverable | Marks |
|---|---|---|
| 1 | **Task shape**, and the exact moment the prediction is made | 2 |
| 2 | **Label definition** — precise and computable, including how you handle records that are not yet resolved | 2 |
| 3 | **Feature list** of at least six candidates, each with the availability test applied; plus at least two candidate features you **reject as leakage**, with reasons | 3 |
| 4 | **Split strategy**, with justification | 2 |
| 5 | **Baseline** — the trivial alternative your model must beat, and what it would score | 2 |
| 6 | **Reliability target and failure handling** — acceptance criteria, the cost of a false positive versus a false negative, and the fallback | 2 |
| 7 | **One honest limitation** you would state to the customer before starting | 2 |

**Constraint.** Do not propose a model architecture. Nothing in this module was about choosing
algorithms, and a design note that leads with "we'll use gradient boosting" while leaving the label
undefined is exactly the failure mode this assessment tests for.

---

## Marking and next steps

| Score | Meaning | Action |
|---|---|---|
| 36–40 | Strong | Proceed to Module 2 |
| 28–35 | Pass | Proceed; skim the sections named in the remediation table |
| 24–27 | Borderline | Redo the weak lessons and re-sit Sections A–B |
| < 24 | Not yet | Re-work Module 1 from M1-L06 onward before continuing |

The remediation table mapping lost marks to specific lesson sections is in the
[answer key](../answer-keys/module-01-answers.md#module-assessment).

Module 1 has no coding project — Module 2 introduces Python, and Project 2 is the first build. The
practical skill assessed here is **design judgement before code**, which is the thing this module
actually taught.
