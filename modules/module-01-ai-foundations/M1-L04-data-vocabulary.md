# M1-L04 — Data Vocabulary: Dataset, Feature, Label, Model, Algorithm

| | |
|---|---|
| **Lesson ID** | M1-L04 |
| **Difficulty** | 1 (Intro) |
| **Estimated study time** | 1.0 hour |
| **Prerequisites** | [M1-L03](M1-L03-task-shapes.md) |

---

## 1. Learning objectives

1. **Define** dataset, example, feature, label, model, algorithm and prediction, and **state** which
   of them exist at training time only, at inference time only, or both.
2. **Draw** the shape of a tabular dataset and **identify** rows, columns, feature matrix and label
   vector using the standard `X` / `y` notation.
3. **Distinguish** an algorithm from a model, using a concrete pair, and explain why conflating them
   causes real confusion when reading documentation.
4. **Identify** feature and label for an unstructured task (text, image) where the "columns" are not
   obvious.
5. **Explain** why labels are the expensive part of most ML projects.

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **Dataset** | A collection of examples used to train or evaluate a model. |
| **Example** (row, sample, instance, observation, data point) | One item: one email, one customer, one image. All five words mean the same thing; different books prefer different ones. |
| **Feature** (input, attribute, predictor, independent variable, column) | One measurable property of an example, used as input. |
| **Feature vector** | All of one example's features, arranged as a list of numbers. |
| **Feature matrix (`X`)** | All examples' feature vectors stacked: rows = examples, columns = features. |
| **Label** (target, ground truth, `y`, dependent variable, annotation) | The correct answer for an example. Exists only in supervised learning. |
| **Label vector (`y`)** | The labels for all examples, in the same row order as `X`. |
| **Algorithm** | A *procedure* for producing a model from data. A recipe. |
| **Model** | The *artefact* the algorithm produced: learned numbers plus the structure that uses them. |
| **Parameters** | The numbers inside a model that were learned from data. Detail in M1-L05. |
| **Prediction** (`ŷ`, "y-hat") | The model's output for an example. Compare with `y` to measure error. |
| **Feature engineering** | Deriving new, more useful features from raw data by hand. |
| **Annotation / labelling** | The human process of producing labels. |
| **Schema** | The definition of what columns exist and their types. |
| **Cardinality** | How many distinct values a feature takes. |

Note on notation: capital `X` for the matrix, lowercase `y` for the vector, is a near-universal
convention. Capital = 2-dimensional, lowercase = 1-dimensional. You will see it in every library and
every paper.

---

## 3. Plain-language explanation

Machine learning has a small vocabulary that is used with irritating inconsistency across books,
libraries and blog posts. Learning it once, precisely, removes a large amount of future confusion.

The core picture is a spreadsheet.

- Each **row** is one thing you want to make a decision about: one email, one customer, one photo.
  That is an **example**.
- Each **column** (except one) is a **feature**: something measurable about that thing.
- One special column is the **label**: the correct answer, which a human supplied.
- The **dataset** is the whole spreadsheet.
- An **algorithm** is the procedure you run over the spreadsheet.
- A **model** is what comes out of running it.

The last distinction is the one people get wrong. **"Logistic regression" is an algorithm. The thing
you saved to `model.pkl` after running it on your data is a model.** One algorithm run on ten
different datasets produces ten different models. Documentation frequently uses "model" for both,
which is why you should be precise in your own writing.

### Connecting to what you already know

| Software concept | ML term | Why the mapping works |
|---|---|---|
| Database table | Dataset | Rows and typed columns |
| Row / record | Example | One entity |
| Column | Feature | One attribute |
| The `is_fraud` column your ops team fills in | Label | Human-supplied ground truth |
| A compiler | Algorithm | A procedure that transforms input into an artefact |
| The compiled binary | Model | The artefact you deploy |
| Running the binary on new input | Inference | Using the artefact |
| The build script | Training pipeline | Reproducibly regenerates the artefact |

The compiler analogy is worth holding on to: **you version the source and the build, and you deploy
the artefact.** Every good ML system treats the model as a build output, not as something hand-made.
M10-L13 makes this a governance requirement.

---

## 4. Analogy

**A recruitment process.**

- **Dataset** = a stack of past applications.
- **Example** = one application.
- **Features** = years of experience, degree, previous role, interview score.
- **Label** = whether that hire actually worked out, judged 2 years later.
- **Algorithm** = the process of studying past applications to work out what predicted success.
- **Model** = the resulting mental checklist a hiring manager carries.
- **Prediction** = "this candidate will probably work out."

### Where the analogy breaks

1. **Labels arrive late and are themselves judgements.** "Worked out" is decided by a human who
   might be wrong or biased. In ML this is called **label noise**, and your model can never be more
   correct than your labels. If the labels encode past discrimination, the model learns it — this is
   the mechanism behind most real-world AI bias, and it is why M10-L08 exists.
2. **The manager knows which features they used; a model may use combinations no one intended.**
   A model can latch onto postcode as a proxy for something you would never legally use directly.
3. **A human updates continuously; a model is frozen at training.** (Same point as M1-L02.)
4. **The analogy hides the cost asymmetry.** Collecting applications is easy; establishing whether
   each hire worked out is slow and expensive. Same in ML: features are usually cheap, labels are
   usually the budget.

---

## 5. Detailed technical explanation

### 5.1 The shape of a dataset

A tabular dataset with `n` examples and `d` features:

```
                 features (d columns)
              ┌──────────────────────────────┐   label
              │  f1     f2     f3     f4     │     y
        ┌─────┼──────────────────────────────┼──────────┐
        │ e1  │ 2.0    1      0.5    "uk"    │   spam   │
examples│ e2  │ 7.5    0      0.1    "de"    │   ham    │  n rows
(n rows)│ e3  │ 1.2    1      0.9    "uk"    │   spam   │
        │ e4  │ 9.9    0      0.2    "fr"    │   ham    │
        └─────┴──────────────────────────────┴──────────┘
                        X  (n x d)                y (n)
```

- `X` is the **feature matrix**, shape `(n, d)` — read "n by d".
- `y` is the **label vector**, shape `(n,)` — one label per row, **in the same order**.
- Row order alignment between `X` and `y` is a hard requirement. Shuffling one without the other is a
  classic and silent bug: the code runs, accuracy collapses to chance, and nothing errors.

Every ML library expects this layout. When scikit-learn's docs say `fit(X, y)`, this is what they
mean. You will build these arrays by hand in M3-L01.

### 5.2 Features are not always columns

For a spreadsheet, features are obvious. For unstructured data they must be *constructed*, and this
is where the interesting work lives.

| Data type | What one example is | How features are obtained |
|---|---|---|
| Tabular | One row | Already columns. Perhaps engineered (ratios, dates → day-of-week) |
| Text | One document | Historically hand-made counts (word frequencies, length). Today: **embeddings** (Module 4/6) |
| Image | One picture | Raw pixel values, or learned convolutional features |
| Audio | One clip | Spectrogram values, or learned features |
| Time series | One window of time | Lagged values, rolling means, seasonality flags |

**The historical shift that created modern AI is exactly here.** Until roughly 2012, a human decided
what features to extract — this was called feature engineering and it was most of the job. Deep
learning *learns* the features from raw input. That is what "representation learning" means, and it
is why deep learning won on images, audio and text but not (yet, reliably) on tabular data, where
humans had already engineered good features.

For your work this matters concretely: when you use an embedding model in Module 6, you are using a
neural network as a **feature extractor**. The 1,536 numbers it returns are features. Nothing more
mysterious than that.

### 5.3 Algorithm vs model, precisely

| | Algorithm | Model |
|---|---|---|
| **What it is** | A procedure | An artefact |
| **Exists** | Before you have data | Only after training |
| **Examples** | Logistic regression, k-means, gradient descent, transformer training | `spam_clf_v3.pkl`, `claude-sonnet-5`, your fine-tuned checkpoint |
| **Analogy** | Recipe | The cake |
| **In code** | `LogisticRegression()` — the class | The fitted object after `.fit(X, y)` |
| **You version** | In git, as code | In a model registry, as a binary + metadata |
| **Changing it** | Changes how learning happens | Changes what is predicted |

```python
algorithm = LogisticRegression()   # the recipe: no knowledge yet
model = algorithm.fit(X, y)        # the cake: now contains learned numbers
prediction = model.predict(X_new)  # using it
```

In scikit-learn, `fit` mutates and returns the same object, so `algorithm` and `model` are the same
Python object — which is precisely why the distinction gets lost. Keep it clear in your head anyway:
before `fit` it knows nothing, after `fit` it encodes your data.

**Why this matters practically:** when a stakeholder asks "can we use the same model for the German
market?", the answer depends entirely on which they mean. Same *algorithm*: obviously yes. Same
*model*: only if German data resembles the training data. Those are completely different
conversations.

### 5.4 Labels: the expensive part

For a typical supervised project, effort splits roughly like this — the exact ratios vary, but the
*ordering* is remarkably consistent:

| Activity | Rough share of effort |
|---|---|
| Getting and cleaning data | large |
| **Defining and producing labels** | **largest** |
| Feature work | moderate |
| Choosing and training the model | small |
| Evaluation and deployment | moderate to large |

Choosing the algorithm — the part tutorials focus on — is one of the smallest slices.

Why labels are hard:

1. **Cost.** Human time. 10,000 labelled tickets at 30 seconds each is ~83 hours.
2. **Disagreement.** Two annotators labelling the same 100 items will disagree on some. If humans
   agree only 80% of the time, no model can exceed ~80% on that task, and you have just discovered
   your realistic ceiling. Measuring this (**inter-annotator agreement**) before building is one of
   the highest-value things you can do, and almost nobody does it. M14-L04.
3. **Definition drift.** "Urgent" means something different to two teams. Ambiguous label
   definitions produce noisy labels, which produce a model that looks broken.
4. **Ground truth may not exist.** For "is this summary good?", there is no single correct answer.
   This is why generation is hard to evaluate (M7-L19, M13-L13).

**The foundation-model shortcut:** LLMs let you skip labelling for many tasks — you describe the
categories in a prompt instead of labelling 10,000 examples. That is genuinely transformative and it
is why Module 5 comes before any training. But you still need labels for **evaluation**. You cannot
know whether your prompt works without a labelled test set. So the cost does not vanish; it shrinks
from ~10,000 labels to perhaps 200. Budget for those 200. They are not optional.

### 5.5 Assumptions and limitations

- This vocabulary assumes supervised learning. Clustering has no `y`; generation's "label" is the
  next token in the text itself (M1-L07).
- The tabular picture is a simplification for text and images, but the roles are unchanged.
- Terminology varies: statisticians say *independent/dependent variable*; ML says *feature/label*;
  databases say *column*. Same things.

---

## 6. Worked example — building a dataset by hand

Task: predict whether a support ticket will breach its 24-hour SLA.

**Step 1 — define one example.** One ticket. Sounds trivial; it is not. If a ticket can be reopened,
is a reopened ticket the same example or a new one? Decide and write it down. Ambiguity here causes
duplicate rows, which causes leakage (M1-L09).

**Step 2 — define the label.** "Breached SLA" = resolved more than 24 hours after creation.
Precisely: `y = 1 if (resolved_at - created_at) > 24h else 0`. Binary classification.

Two immediate problems, both real:

- Tickets **still open** have no label yet. Exclude them, or you will silently label them 0.
- The label uses `resolved_at`, which **does not exist when you need the prediction**. Any feature
  derived from it is leakage. Flag this now (M1-L09).

**Step 3 — choose features available at prediction time.** The test for every candidate feature:
*would this value be known at the moment I need the prediction?*

| Candidate | Available at creation? | Verdict |
|---|---|---|
| `channel` (email/chat/phone) | Yes | ✅ feature |
| `customer_tier` (free/pro/enterprise) | Yes | ✅ feature |
| `body_length` (characters) | Yes | ✅ feature |
| `hour_of_day` created | Yes | ✅ feature |
| `n_prior_tickets` by this customer | Yes | ✅ feature |
| `assigned_agent` | Usually not at creation | ⚠️ only if assignment is immediate |
| `n_replies` | No — accumulates over the ticket's life | ❌ **leakage** |
| `resolution_time_hours` | No — it *is* the label | ❌ **leakage** |

`n_replies` is the dangerous one. It looks like an innocent feature and it will give you 97%
accuracy in testing and useless predictions in production, because at creation time it is always 0.

**Step 4 — write out `X` and `y` for five examples.**

| # | channel | tier | body_len | hour | prior_tickets | **y** (breached) |
|---|---|---|---|---|---|---|
| 1 | email | free | 850 | 22 | 0 | 1 |
| 2 | chat | enterprise | 120 | 10 | 5 | 0 |
| 3 | email | pro | 430 | 14 | 2 | 0 |
| 4 | phone | free | 210 | 3 | 1 | 1 |
| 5 | chat | pro | 1500 | 16 | 0 | 1 |

Here `n = 5` examples and `d = 5` features. `X` has shape `(5, 5)`; `y` has shape `(5,)`.

**Step 5 — make it numeric.** `channel` and `tier` are text; most algorithms need numbers.

*One-hot encoding* creates one 0/1 column per category:

| # | ch_email | ch_chat | ch_phone | tier_free | tier_pro | tier_ent | body_len | hour | prior | y |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 1 | 0 | 0 | 1 | 0 | 0 | 850 | 22 | 0 | 1 |
| 2 | 0 | 1 | 0 | 0 | 0 | 1 | 120 | 10 | 5 | 0 |
| 3 | 1 | 0 | 0 | 0 | 1 | 0 | 430 | 14 | 2 | 0 |
| 4 | 0 | 0 | 1 | 1 | 0 | 0 | 210 | 3 | 1 | 1 |
| 5 | 0 | 1 | 0 | 0 | 1 | 0 | 1500 | 16 | 0 | 1 |

`d` has grown from 5 to 9. This is normal and it has a cost: **a high-cardinality column explodes
the matrix.** One-hot encoding a `customer_id` with 50,000 values adds 50,000 columns and is almost
always wrong. That is a decision point, not a mechanical step.

Two more subtleties worth noticing now:

- `tier` is **ordinal** (free < pro < enterprise). One-hot discards that ordering. Encoding it as
  1/2/3 preserves order but asserts equal spacing. Same trade-off as M1-L03 §5.4.
- `hour` is **cyclic**: hour 23 is adjacent to hour 0, but numerically they are 23 apart. A model
  will not know that unless you encode it (e.g. sine/cosine of the hour). This is feature
  engineering, and it is the kind of thing that quietly limits a model's accuracy.

---

## 7. Practical activity

**File:** [`labs/m1/l04_dataset_anatomy.py`](../../labs/m1/l04_dataset_anatomy.py) — standard library
only, no NumPy needed yet.

```bash
python3 labs/m1/l04_dataset_anatomy.py
```

It builds the exact ticket dataset from §6 as plain Python lists, prints `X` and `y` with their
shapes, one-hot encodes the categorical columns, and then **demonstrates the row-misalignment bug**
by shuffling `X` without `y` so you can see what a silent data bug looks like.

### 7.1 Important lines

| Construct | Why |
|---|---|
| `X: list[list[float]]` | A list of lists = a matrix. Rows are examples. |
| `sorted(set(values))` | Collects the distinct categories, in a **stable, sorted** order. If the order changed between training and inference, column meanings would shift — a real production bug. |
| `[1.0 if v == cat else 0.0 for cat in categories]` | One-hot encoding in one line. M2-L04 covers comprehensions. |
| `len(X)`, `len(X[0])` | `n` and `d` — the shape. |
| `random.Random(0).shuffle(X_only)` | Deliberately shuffles `X` and not `y` to create the misalignment bug. |

### 7.2 Expected output

`[EXECUTED]` 2026-09-07:

```
============================================================
DATASET ANATOMY - support ticket SLA breach
============================================================

Raw dataset (5 examples, 5 features + 1 label)
  #  channel  tier        body_len  hour  prior  | y
  1  email    free             850    22      0  | 1
  2  chat     enterprise       120    10      5  | 0
  3  email    pro              430    14      2  | 0
  4  phone    free             210     3      1  | 1
  5  chat     pro             1500    16      0  | 1

Categories discovered (sorted for stability):
  channel -> ['chat', 'email', 'phone']
  tier    -> ['enterprise', 'free', 'pro']

After one-hot encoding:
  X shape = (5, 9)   n=5 examples, d=9 features
  y shape = (5,)
  column names: ['ch_chat', 'ch_email', 'ch_phone', 'tier_enterprise', 'tier_free', 'tier_pro'],
                ['body_len', 'hour', 'prior']

  X[0] = [0.0, 1.0, 0.0, 0.0, 1.0, 0.0, 850.0, 22.0, 0.0]   y[0] = 1
  X[1] = [1.0, 0.0, 0.0, 1.0, 0.0, 0.0, 120.0, 10.0, 5.0]   y[1] = 0

------------------------------------------------------------
THE ALIGNMENT BUG
------------------------------------------------------------
Correct pairing:
  example 1: body_len=850  -> y=1
  example 2: body_len=120  -> y=0
  example 3: body_len=430  -> y=0

After shuffling X but NOT y:
  example 1: body_len=430  -> y=1   <-- wrong label
  example 2: body_len=120  -> y=0
  example 3: body_len=850  -> y=0   <-- wrong label

Nothing raised an exception. No type error. No warning.
The code runs perfectly and the model learns noise.
This is why X and y must always be shuffled together.
============================================================
```

Look closely at the alignment section. Example 2 kept its correct pairing purely by chance — the
shuffle happened to leave that row in place. Examples 1 and 3 are now paired with the wrong labels.

That partial corruption is what makes this bug so dangerous in practice. If *every* row were wrong,
accuracy would crater to chance and you would investigate immediately. Instead a fraction of rows
stay correct, accuracy lands somewhere mediocre-but-plausible, and the natural conclusion is "the
model needs tuning" or "we need more data". Teams have lost weeks to exactly this.

**Verification:** confirm `X shape = (5, 9)` and that the alignment section shows two mismatched
pairs with no error raised. That silence is the entire point.

---

## 8. Common mistakes and troubleshooting

1. **Using a feature unavailable at prediction time.** The single most common cause of "great in
   testing, useless in production". Always ask: *would I know this value at the moment I predict?*
2. **Shuffling `X` and `y` separately.** Silent. Always shuffle indices, or shuffle paired rows.
3. **Saying "model" when you mean "algorithm".** Causes real miscommunication about reuse.
4. **One-hot encoding high-cardinality columns.** 50,000 new columns. Use grouping, target encoding,
   or embeddings instead.
5. **Inconsistent category order between training and inference.** Column 3 means "chat" at training
   and "phone" at inference. Persist the encoder with the model, never rebuild it from live data.
6. **Assuming labels are correct.** Measure annotator agreement first. Your model cannot beat your
   labels.
7. **Ignoring that `hour` is cyclic** or that `tier` is ordinal. Free accuracy left on the table.

| Symptom | Likely cause | Fix |
|---|---|---|
| Accuracy ~99% in dev, poor in production | Leakage from a future feature | Audit every feature for time availability |
| Accuracy ≈ chance despite good data | `X`/`y` misalignment | Shuffle together; verify a few rows by hand |
| `ValueError: could not convert string to float` | Categorical column not encoded | One-hot or ordinal encode it |
| Works in training, `KeyError` on a new category at inference | Unseen category | Reserve an "unknown" bucket at training time |
| Feature matrix has 50k columns | One-hot on an ID column | Do not encode IDs |

---

## 9. Security, privacy, reliability and cost

- **Privacy.** Features are personal data. `customer_tier` and `postcode` may be innocuous alone and
  identifying together. Datasets need the same access control as production databases, plus a
  retention and deletion story (M10-L06). A model trained on personal data can also *leak* it.
- **Security.** Training data is an injection surface. If any user can add rows to a dataset you
  later train on, they can influence model behaviour — **data poisoning**. Treat dataset write
  access as privileged (M10-L05).
- **Reliability.** The training/serving pipelines must compute features **identically**. A subtle
  difference between them — training on a nightly batch, serving on live data — is called
  training/serving skew and is a leading cause of silent production degradation.
- **Cost.** Labels dominate. Before proposing a supervised project, estimate labelling hours
  explicitly. A model that needs 50,000 labels may be a worse business decision than a rule that
  needs none.

---

## 10. Exercises

### Exercise 1 — Beginner (~10 min)

For predicting whether a customer will renew a subscription, name:
(a) what one example is, (b) four plausible features, (c) the label and how you would compute it,
(d) one tempting feature that would be leakage, and why.

### Exercise 2 — Intermediate (~20 min)

Take this raw table:

| order_id | customer_id | country | items | order_total | placed_at | delivered_at | was_returned |
|---|---|---|---|---|---|---|---|
| 1001 | C7 | UK | 3 | 84.50 | 2026-01-04 09:12 | 2026-01-06 11:00 | no |
| 1002 | C7 | UK | 1 | 19.99 | 2026-01-09 17:40 | 2026-01-12 10:20 | yes |
| 1003 | C2 | DE | 7 | 210.00 | 2026-01-11 08:05 | 2026-01-13 14:30 | no |

You must predict `was_returned` **at the moment the order is placed**.

1. Which columns are usable features? Which are leakage? Justify each.
2. Derive two new features from `placed_at` that could plausibly matter.
3. `customer_id` has high cardinality. Give two ways to use it without one-hot encoding it, and a
   risk of each.
4. Write the shape of `X` and `y` after your encoding, showing your arithmetic.

### Exercise 3 — Challenge (~25 min)

Your company wants to predict which employees will leave within 12 months.

1. Define the example, the label, and the exact time window. State how you avoid including people
   who have not yet had 12 months of opportunity to leave.
2. List five features and, for each, state whether it is available at prediction time.
3. Identify **two** features that are legally or ethically problematic, and explain the proxy-variable
   risk even if you exclude the obvious one.
4. State the inter-annotator or ground-truth issue with this label. (There is one: "left" is not as
   crisp as it looks.)
5. Recommend whether to build this at all, with reasoning.

Rubric in the answer key. Part 5 is deliberately open — a defensible "no" scores full marks.

---

## 11. Quiz

**Q1.** In the standard notation, what do `X` and `y` refer to, and why is one capitalised?

- A. `X` is the algorithm, `y` the model; capitalisation is arbitrary.
- B. `X` is the feature matrix (2-D, hence capital), `y` is the label vector (1-D, hence lowercase).
- C. `X` is training data, `y` is test data.
- D. `X` is input at inference, `y` is input at training.

**Q2.** Which best distinguishes an algorithm from a model?

- A. An algorithm runs on a GPU; a model runs on a CPU.
- B. An algorithm is a procedure that exists before you have data; a model is the artefact produced
  by running it on a specific dataset.
- C. They are synonyms.
- D. A model is written in Python; an algorithm is mathematics.

**Q3.** You are predicting SLA breach at ticket creation. Which feature is leakage?

- A. `channel`  B. `customer_tier`  C. `number_of_replies_so_far`  D. `hour_of_day_created`

**Q4.** Why does the lab shuffle `X` without `y`?

- A. To improve model accuracy.
- B. To demonstrate that misalignment produces no error, no warning and no type failure — the model
  silently learns noise.
- C. Because labels should always be shuffled separately.
- D. To speed up training.

**Q5.** One-hot encoding `customer_id` with 50,000 distinct values is a bad idea mainly because:

- A. Customer IDs are private.
- B. It adds 50,000 columns, making the matrix enormous and sparse, and IDs carry no generalisable
  signal.
- C. One-hot encoding only supports 10 categories.
- D. It would make the model too accurate.

**Q6.** Two annotators agree on only 78% of items when labelling ticket urgency. What does this most
directly tell you?

- A. One annotator is incompetent.
- B. The model will reach 100% accuracy.
- C. The label definition is ambiguous, and roughly 78% is your realistic accuracy ceiling on this
  task as currently defined.
- D. You need a deeper neural network.

**Q7.** Using an LLM to classify tickets by prompt rather than training a classifier removes the need
for:

- A. All labelled data, including for evaluation.
- B. Large-scale training labels, but not the smaller labelled test set needed to know whether it
  works.
- C. Feature engineering only.
- D. Nothing; you still need 10,000 labels.

**Q8.** Which is the correct description of "training/serving skew"?

- A. The model drifts over time as the world changes.
- B. Features are computed differently in the training pipeline than in the serving pipeline, so the
  model sees inputs at inference that do not match what it learned from.
- C. The training set is larger than the test set.
- D. The GPU and CPU produce different floating-point results.

**Q9.** In the §6 example, `hour_of_day` is encoded as an integer 0–23. What limitation does this
introduce?

- A. None; integers are ideal.
- B. Hour is cyclic — 23 and 0 are adjacent in reality but 23 apart numerically — so the model cannot
  see that late night and early morning are neighbouring.
- C. Integers cannot be used as features.
- D. It causes leakage.

**Q10.** *(Written, rubric-graded.)* A stakeholder asks "can we reuse the same model for our new
Brazilian market?" In under 70 words, explain what you would need to clarify and what your answer
depends on. Use the algorithm/model distinction explicitly.

---

## 12. Revision notes

- Dataset = spreadsheet. Row = **example**. Column = **feature**. Answer column = **label**.
- `X` = feature matrix, shape `(n, d)`, capital because 2-D. `y` = label vector, shape `(n,)`.
  **Row order must stay aligned.**
- **Algorithm** = the recipe (exists before data). **Model** = the cake (exists only after training).
  Compiler vs binary.
- Features for text/images are *constructed*; deep learning learns them. An embedding model is a
  feature extractor.
- **The test for any feature: would I know this value at the moment I predict?** If no, it is
  leakage.
- One-hot encoding: one 0/1 column per category. Never on high-cardinality IDs. Persist the encoder
  with the model, keep category order stable.
- **Labels are the expensive part.** Measure annotator agreement first — it sets your ceiling.
- LLMs remove the need for *training* labels, not *evaluation* labels. Budget ~200.
- Watch for ordinal features (lost ordering) and cyclic features (hour, day-of-week).

---

## 13. Completion checklist

- [ ] I can define all 8 core terms without looking.
- [ ] I can draw the `X` / `y` diagram and state both shapes.
- [ ] I can explain algorithm vs model with a concrete pair.
- [ ] I ran the lab and saw the alignment bug produce no error.
- [ ] I completed Exercises 1 and 2.
- [ ] I attempted Exercise 3 including the ethics section.
- [ ] I scored 7/10 on the quiz.

---

## 14. References

`[STABLE]`.

- scikit-learn glossary of common terms — the closest thing to an authoritative shared vocabulary.
  <https://scikit-learn.org/stable/glossary.html> `[UNVERIFIED]`
- Google, *Rules of Machine Learning* — Rule #29 covers training/serving skew directly.
  <https://developers.google.com/machine-learning/guides/rules-of-ml> `[UNVERIFIED]`

---

## 15. Next lesson

→ [M1-L05 — Parameters vs Hyperparameters](M1-L05-parameters-vs-hyperparameters.md)

You now know that a model contains learned numbers. Next: the difference between the numbers the
model learns and the numbers **you** choose — and why only one kind can be tuned on test data
without invalidating your results.
