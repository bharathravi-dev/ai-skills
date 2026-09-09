# Module 1 — Revision Guide

Read this **before** the assessment. It is a condensed pass over all eleven lessons: the ideas that
carry into later modules, the numbers worth remembering, and the mistakes that recur.

If any line here reads as unfamiliar rather than merely terse, go back to that lesson.

---

## 1. The one-page summary

| Lesson | The single thing to retain |
|---|---|
| L01 | AI ⊃ ML ⊃ DL. "Generative" describes the **output shape**, not the method. Most deployed deep learning is *not* generative. |
| L02 | Two ways to get logic in: **you write it** or **you fit it from data**. Rules on the outside, model on the inside. |
| L03 | Four task shapes, defined by output structure. Ranking is a fifth, and RAG retrieval is ranking. |
| L04 | `X` (n×d) and `y` (n) must stay row-aligned. **Labels are the expensive part.** |
| L05 | Parameter = learned. Hyperparameter = you chose it. **Your prompt is a hyperparameter.** |
| L06 | Train fits parameters · validation compares choices · test is touched **once** · inference learns nothing. |
| L07 | Self-supervision = hide part of the data and predict it. **Truth was never the objective.** |
| L08 | Training error falls forever; validation error is U-shaped. Pick the validation minimum. |
| L09 | Leakage removes every warning sign. **Treat unexpectedly good results as bug reports.** |
| L10 | Confidence ≠ accuracy. Fluency is not evidence. Every mitigation has a residual failure mode. |
| L11 | Capability ≠ reliability. Steps multiply: `p^n`. Reshape the task so failure is cheap. |

---

## 2. Numbers worth remembering

| Number | Where it comes from | Why it matters |
|---|---|---|
| **0.90¹⁰ ≈ 35%** | M1-L11 | A 10-step agent at 90% per step fails two times in three |
| **0.95⁵ ≈ 77%** | M1-L11 | Five "excellent" steps is a mediocre pipeline |
| **+0.11 optimism at 100 trials** | M1-L05 lab | Selecting the best of 100 identical candidates inflates the score by 11 points |
| **0.003 vs 0.091** | M1-L06 lab | Random vs temporal split error for the *same* model — a 30× difference |
| **train 0.054 / val 15,715** | M1-L08 lab | The best training error was the worst model, by ~7,600× |
| **100% → 75% = baseline** | M1-L09 lab | A leaky model collapsing to the do-nothing baseline on production-shaped rows |
| **stated 0.953 / actual 0.814** | M1-L10 lab | Overconfidence is worst exactly where you planned to automate |

---

## 3. The diagnostic tables

### Overfitting vs underfitting (M1-L08)

| Training | Validation | Diagnosis | Action |
|---|---|---|---|
| High | High, similar | Underfitting | **Add** capacity, train longer, better features |
| Low | Low, similar | Good fit | Compare to a baseline, then ship |
| Low | High | Overfitting | **Reduce** capacity, more data, regularise, early stop |
| High | Low | **Bug** | Check dropout at eval, preprocessing consistency, split difficulty |
| Perfect | Perfect | **Leakage** | Audit features; rebuild test rows as they appear at prediction time |

The last row is the M1-L09 addition. The M1-L08 table assumes no leakage.

### The five leakage types (M1-L09)

| Type | One-line test |
|---|---|
| Target | Is this field populated *because of* the outcome? |
| Train–test contamination | Do any examples appear in two splits? |
| Temporal | Is any feature's as-of time later than the prediction time? |
| Group | Does the same entity appear on both sides? |
| Preprocessing | Does every `fit` happen **after** the split? |

### Choosing a split (M1-L06)

| Situation | Split |
|---|---|
| Independent examples, balanced | Random |
| Imbalanced classes | Stratified — and check the *count* of minority examples |
| Repeated entities (customer, patient, document) | Grouped |
| Predicting forward in time | **Temporal**, cut on a real boundary |

---

## 4. The decision questions

Memorise these five. They do most of the work in real conversations.

1. **Where did the logic come from?** → rule-based or learned (L02)
2. **What shape is the output?** → classification / regression / clustering / ranking / generation
   (L03)
3. **Would I know this value at the moment I predict?** → feature or leakage (L04, L09)
4. **Did an algorithm compute it, or did a human type it?** → parameter or hyperparameter (L05)
5. **Could a competent person write down the rule in an afternoon?** → if yes, write it down (L11)

---

## 5. Things that are never negotiable

- **Authorization is never delegated to a model.** You need proof, not evidence. (L02, L11)
- **Never compute money with a language model.** (L11)
- **Never learn what is published.** Tax bands, statutory rules, business policy → code. (L02)
- **Never assert exact model output in a test.** Assert schema, structure, properties. (L10)
- **Never report a training score as evidence.** (L08)
- **Never tune on the test set** — and if you did, say so. (L05, L06)

---

## 6. The eight recurring mistakes

1. Reporting training performance.
2. Tuning against the set you then report.
3. Using a feature unavailable at prediction time.
4. Random-splitting time-dependent data.
5. Believing a model's stated confidence without measuring calibration.
6. Bundling several tasks under one quality score.
7. Adding a model step where a regex would do.
8. Treating a demo as evidence of reliability.

---

## 7. Vocabulary self-test

Cover the right column. If you cannot produce the definition, revisit the lesson.

| Term | Lesson |
|---|---|
| Brittleness | L02 |
| Multi-label vs multi-class | L03 |
| Feature matrix, label vector | L04 |
| Training/serving skew | L04 |
| Optimistic bias | L05 |
| Stratified split | L06 |
| Pretext task | L07 |
| Reward hacking | L07 |
| Generalization gap | L08 |
| Point-in-time reconstruction | L09 |
| Calibration, ECE | L10 |
| Epistemic vs aleatoric | L10 |
| Compound error | L11 |

---

## 8. Run the labs once more

Each takes under a minute and each demonstrates one thing you will be asked about:

```bash
python3 labs/m1/l05_hyperparameter_sort.py --demo   # optimistic bias
python3 labs/m1/l06_splitting.py                    # split strategy changes the answer 30x
python3 labs/m1/l08_overfitting.py                  # the U-curve, and the cliff
python3 labs/m1/l09_leakage.py                      # 100% that means nothing
python3 labs/m1/l10_calibration.py                  # confidence vs accuracy
python3 labs/m1/l11_reliability_calculator.py       # p^n
```

---

## 9. What Module 1 was actually for

You cannot yet build anything. That is deliberate. What you can now do is **ask the questions that
determine whether a build is worth starting** — what shape is this, where do the labels come from,
what would leak, what reliability does it need, and would ordinary code be better.

Those questions are the difference between an engineer who ships AI features and one who ships AI
demos. Module 2 gives you the tools; this module gave you the judgement about when to reach for them.

→ Next: [`assessments/module-01-assessment.md`](module-01-assessment.md), then
[M2-L01](../modules/module-02-python-foundations/M2-L01-setup-terminal-venv-pip.md).
