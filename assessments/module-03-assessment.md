# Module 3 Assessment — Math and ML Essentials

| | |
|---|---|
| **Covers** | M3-L01 … M3-L14 and Project 3 |
| **Questions** | 23 (13 multiple choice, 6 calculation, 6 short answer) + 1 practical assignment |
| **Total marks** | 71 |
| **Pass mark** | 50 (70%) |
| **Time** | ~2.5 hours (90 min for Sections A–C, 60 min for Section D) |
| **Answer key** | [`answer-keys/module-03-answers.md`](../answer-keys/module-03-answers.md#module-assessment) |

**Conditions.** Sections A and B closed book, no calculator beyond arithmetic. Section C may use a
calculator. Section D uses a machine.

**Before you start**, read [the revision guide](module-03-revision.md).

---

## Section A — Recall and understanding (13 marks, 1 each)

**A1.** `a = [3, 4]`, `b = [30, 40]`. What is `cos(a, b)`?

- A. 0.0  B. 0.5  C. 10.0  D. 1.0

**A2.** A disease affects 1 in 10,000. A test is 99% accurate both ways. A random person tests
positive. Roughly what is the probability they have the disease?

- A. 99%  B. 50%  C. About 1%  D. 0.01%

**A3.** A model assigns probability 0.02 to the correct token. Its cross-entropy loss for that token
is:

- A. ≈ 3.91  B. −0.02  C. 0.02  D. 50

**A4.** You remove every activation function from a 20-layer network. What can it now represent?

- A. The same set of functions, but trained more slowly.
- B. Exactly the set a single linear layer represents.
- C. Nothing at all; the network stops producing output.
- D. Only classification tasks, not regression ones.

**A5.** In backpropagation, what is `∂L/∂z` for softmax followed by cross-entropy?

- A. `p(1−p)`  B. `y/p`  C. `−log p`  D. `p − y`

**A6.** Your loss becomes `nan` after four steps. The first thing to change is:

- A. The learning rate.  B. The number of epochs.
- C. The batch size.  D. The activation function.

**A7.** Adam stores how many extra copies of the parameters compared with plain SGD?

- A. 2  B. 1  C. 0  D. 4

**A8.** 3,000 X-ray images from 800 patients. Which split?

- A. Random over rows  B. Stratified over rows only
- C. Temporal by scan date  D. Grouped by patient

**A9.** Precision is:

- A. `TP/(TP+FP)`  B. `TP/(TP+FN)`  C. `TN/(TN+FP)`  D. `(TP+TN)/total`

**A10.** F1 for precision 1.0 and recall 0.01 is approximately:

- A. 0.505  B. 1.0  C. 0.99  D. 0.02

**A11.** You square every predicted probability. ROC-AUC:

- A. Rises  B. Falls  C. Is unchanged  D. Becomes undefined

**A11b.** And the model's expected calibration error:

- A. Rises  B. Falls  C. Is unchanged  D. Becomes undefined

**A12.** A test set of 100 rows gives 90% accuracy. The approximate standard error is:

- A. 0.003  B. 0.3  C. 0.03  D. 0

---

## Section B — Applied reasoning (12 marks, 2 each)

**B1.** A colleague reports 94% accuracy on a churn model. What is the first question you ask, and
why? *(2 marks)*

**B2.** You are told a random split gave 0.99 accuracy and a grouped split gave 0.72 on the same data
and model. Which number do you report, and what do you say about the other one? *(2 marks)*

**B3.** Your model's ROC-AUC is 0.96 on a 0.5%-positive problem, and the operations team says the
alerts are useless. Explain how both can be true. *(2 marks)*

**B4.** A teammate oversamples the minority class to balance the dataset and then splits it 80/20.
Their test accuracy is 0.97. State precisely what is wrong and what the correct order is. *(2 marks)*

**B5.** A model's predicted probabilities are used to compute expected cost. The model was trained
with class weights. What is the risk, and what would you do first? *(2 marks)*

**B6.** You gradient-check a custom layer on one input and get relative error 3e-11. State what you
have and have not established. *(2 marks)*

---

## Section C — Calculation (18 marks, 3 each)

Show your working. Answers without working score at most 1 mark.

**C1.** Confusion matrix: TP = 30, FP = 20, FN = 70, TN = 880.
Compute accuracy, precision, recall and F1 to 4 decimal places. State the majority-class baseline
accuracy and say in one sentence what the comparison tells you. *(3 marks)*

**C2.** `a = [1, 2, 2]`, `b = [2, 4, 4]`, `c = [-1, 0, 1]`.
Compute `cos(a, b)` and `cos(a, c)` exactly, and state which of `b` or `c` is more similar to `a` and
why magnitude did not decide it. *(3 marks)*

**C3.** A two-input neuron has `w = [0.5, -0.3]`, `b = 0.2`, ReLU activation, feeding an output unit
with weight `1.5` and bias `-0.1`, then a sigmoid. For `x = [2.0, 1.0]`:

(a) compute the hidden pre-activation, hidden activation, output pre-activation and final probability;
(b) with true label `y = 1`, compute `∂L/∂z_out` for binary cross-entropy;
(c) compute `∂L/∂w[0]`. *(3 marks)*

**C4.** Gradient `g = [0.8, 0.02]`, learning rate 0.1.
Compute the plain SGD update for both parameters, then Adam's update at step `t = 1` from
`m = v = 0` with `β₁ = 0.9`, `β₂ = 0.999`. Explain in one sentence why Adam's two components are
equal. *(3 marks)*

**C5.** A dataset has 40,000 rows and a 0.5% positive rate. You take a 10% test set.

(a) How many positives do you expect in it?
(b) What is the standard error of an accuracy of 0.98 on that test set?
(c) Your model scores 0.982 and a colleague's 0.979. What do you conclude, and why? *(3 marks)*

**C6.** Regression predictions on 100 rows give MAE 4.0 and RMSE 4.2. On a second dataset of the same
size, MAE 4.0 and RMSE 19.0.

(a) What does the RMSE/MAE ratio tell you in each case?
(b) Which metric would you report for a delivery-time model where being 60 minutes late is far worse
than six occasions of being 10 minutes late, and why? *(3 marks)*

---

## Section D — Practical assignment (28 marks)

**You may use a machine, this course's material, and the Project 3 codebase.**

You are handed a dataset and a model by a departing colleague, with a note:

> *"Churn model. 96.8% accurate on the test set, ROC-AUC 0.94. Ready to ship — just point it at the
> production table. Threshold is 0.5. The team can review about 40 accounts a week."*

The dataset has 80,000 rows: 12 months of monthly snapshots for 6,700 customers, 3.1% of snapshots
churned. Features include `account_id`, `region`, `plan_tier`, `tenure_months`,
`support_tickets_last_90d`, and `customer_avg_churn_rate` (described in the note as "historical churn
propensity per account").

**D1. Audit (8 marks).** List every specific problem you can identify with the claim as stated. For
each, say what evidence you would gather to confirm it and what you expect that evidence to show. At
least five distinct problems are available.

**D2. Re-evaluate (8 marks).** Using the Project 3 codebase as a starting point, describe — in code
or in precise prose — the evaluation you would run instead. Specify the split, the metrics, the
baselines, and how you would choose the threshold. Justify each choice in one sentence.

**D3. Report (6 marks).** Write the summary you would send to the product owner. It must fit on one
screen, contain no unexplained jargon, state what the model can and cannot do, and give them a
decision to make rather than a number to admire.

**D4. Limitations (6 marks).** Write the limitations section for the model card. Include at least one
limitation about the data, one about the method, one about calibration, and one about what the
evaluation does *not* establish.

**Marking:** see the rubric in the [answer key](../answer-keys/module-03-answers.md#module-assessment).

---

## Marks summary

| Section | Marks |
|---|---|
| A — Recall | 13 |
| B — Applied reasoning | 12 |
| C — Calculation | 18 |
| D — Practical assignment | 28 |
| **Total** | **71** |

**Pass 50 (70%). Distinction 61 (85%).**

If you score below 50, the answer key's remediation table maps every question to the lesson and
section to revisit.
