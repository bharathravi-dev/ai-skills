# M1-L03 — The Four Task Shapes: Classification, Regression, Clustering, Generation

| | |
|---|---|
| **Lesson ID** | M1-L03 |
| **Module** | Module 1 — AI Foundations |
| **Difficulty** | 1 (Intro) |
| **Estimated study time** | 1.0 hour |
| **Prerequisites** | [M1-L01](M1-L01-what-ai-ml-dl-genai-mean.md) |

---

## 1. Learning objectives

1. **Name** the four task shapes and **state** the output type of each in one phrase.
2. **Convert** a vague business request into a specific task shape, and **justify** the choice by
   naming the output type required.
3. **Recognise** when a request is *two* tasks wearing one coat, and split it.
4. **Explain** why the task shape determines which evaluation metric is even meaningful.
5. **Identify** the three common mis-framings (ranking as classification, ordinal as regression,
   generation as retrieval) and state the correct framing for each.

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **Task shape** | The structural form of what the model outputs. Not the domain, not the algorithm — the output type. |
| **Classification** | Output is one label (or a set of labels) chosen from a fixed, finite list defined in advance. |
| **Binary classification** | Classification with exactly two possible labels. |
| **Multi-class classification** | One label chosen from three or more mutually exclusive options. |
| **Multi-label classification** | Zero or more labels from a list, applied simultaneously. |
| **Regression** | Output is a continuous number on a scale, such as a price, a duration or a temperature. |
| **Clustering** | Output is a grouping of items where the groups were **not** defined in advance. |
| **Generation** | Output is newly constructed content from an open-ended space (text, image, audio, code). |
| **Ranking** | Output is an *ordering* of items by relevance. A fifth shape, treated here as a variant. |
| **Ordinal** | Categories with a meaningful order but no meaningful arithmetic (e.g. small/medium/large). |
| **Label space** | The complete set of possible outputs, enumerated in advance. Exists for classification, not for generation. |
| **Continuous** | Able to take any value in a range, including fractions. |
| **Anomaly detection** | Identifying items unlike the rest. Usually framed as classification or clustering. |

---

## 3. Plain-language explanation

Before you can choose a model, a metric, a dataset or a budget, you must answer one question:

> **What shape is the output?**

There are four common answers, and they lead to completely different engineering.

1. **Classification — "which bucket?"** You have a fixed list of answers. Spam or not spam. Which of
   these 12 support categories. Approved, rejected or needs review. The list exists before you start
   and does not change at runtime.

2. **Regression — "how much?"** The answer is a number on a scale. What will this house sell for?
   How many minutes until delivery? How many tickets next Tuesday? Any value in a range is allowed,
   including 43.7.

3. **Clustering — "what natural groups exist?"** You do **not** have a list of answers. You have
   50,000 customers and want to know whether they fall into natural groups. Nobody defines the
   groups in advance; the algorithm proposes them and a human interprets them afterwards.

4. **Generation — "produce something new."** The answer is content, constructed piece by piece, from
   a space too large to enumerate. Write this summary. Draft this reply. Produce this image.

The critical difference between 1 and 4 is whether the list of possible outputs **exists**.
Classification chooses from a list. Generation builds something that was never on a list.

The critical difference between 1 and 3 is **who defines the groups**. In classification a human
defined the categories in advance and labelled examples. In clustering nobody did, which is why the
output needs human interpretation before it is useful.

### Connecting to what you already know

| Web concept | Task shape |
|---|---|
| A `<select>` with fixed `<option>`s | Classification |
| A numeric `<input type="number">` | Regression |
| Grouping log lines by similarity to find unknown error patterns | Clustering |
| A `<textarea>` the system fills in for you | Generation |
| Search results page ordering | Ranking |

If you can name the HTML form control that would hold the answer, you have found the task shape.
That is not a joke — it is a genuinely reliable heuristic and I use it in customer meetings.

---

## 4. Analogy

**A restaurant.**

- **Classification** = the waiter asking "table for 2, 4 or 6?" — a fixed menu of answers.
- **Regression** = the bill. A number, any number, on a continuous scale.
- **Clustering** = the manager reviewing a year of bookings and noticing three kinds of customer
  emerge (quick lunch, long dinner, big group) that nobody had defined before.
- **Generation** = the chef inventing a dish from what is in the kitchen.

### Where the analogy breaks

1. **The restaurant categories are obviously distinct; real tasks blur.** "Rate this review 1–5" is
   ordinal — categories with an order. Treating it as classification throws away the fact that
   predicting 4 when the truth is 5 is far better than predicting 1. Treating it as regression
   implies the gap from 1→2 equals 4→5, which is empirically false for star ratings. Neither shape
   is fully correct, and the right choice depends on your metric. This is a real judgement call
   covered in §5.4.
2. **The chef improvises within tradition; a generative model has no such grounding.** The chef
   knows a dish is bad. The model has no comparable check. That is why Module 7 exists.
3. **The manager can validate the three customer groups against reality; clustering output is
   frequently meaningless.** Give a clustering algorithm `k=3` and it will return 3 clusters whether
   or not 3 groups exist. **Clustering always produces output; that output is not evidence that
   structure exists.** This is the single biggest trap in unsupervised learning.

---

## 5. Detailed technical explanation

### 5.1 The four shapes side by side

| | Classification | Regression | Clustering | Generation |
|---|---|---|---|---|
| **Output** | A label from a fixed set | A number on a scale | A group assignment | Constructed content |
| **Label space known in advance?** | Yes | Range known, values continuous | **No** | No — effectively unbounded |
| **Needs labelled training data?** | Yes | Yes | **No** | Pretrained on raw text/images |
| **Learning paradigm** (M1-L07) | Supervised | Supervised | Unsupervised | Self-supervised |
| **Typical metrics** (M3-L14) | Accuracy, precision, recall, F1 | MAE, RMSE, R² | Silhouette, plus human judgement | No single metric; see M7-L19 |
| **"Is it correct?" is…** | Objectively checkable | Objectively checkable | **Not well defined** | Often subjective and multi-dimensional |
| **Classic example** | Spam detection | House price prediction | Customer segmentation | LLM writing an email |

Read the second-to-last row carefully. It explains why evaluation gets harder from left to right, and
why Modules 5, 7 and 13 spend so much effort on evaluation. For classification you compare to a
correct label. For generation there may be a thousand acceptable outputs and no list of them.

### 5.2 Classification varieties

Getting this sub-shape wrong is a common and expensive mistake.

| Variety | Rule | Example | Trap |
|---|---|---|---|
| **Binary** | Exactly 2 labels | spam / not spam | Choosing accuracy as the metric when classes are imbalanced (M3-L14) |
| **Multi-class** | 1 label from N, mutually exclusive | route ticket to Billing / Technical / Account / Sales | Assuming exclusivity when it does not hold |
| **Multi-label** | 0..N labels simultaneously | tag an article with `python`, `security`, `aws` | Modelling as multi-class, which forces a false single choice |
| **Ordinal** | Ordered categories | severity: low / medium / high / critical | Losing the ordering, so predicting `low` for `critical` costs the same as predicting `high` |

**The multi-class vs multi-label mistake is the one you will actually hit.** A support ticket saying
"I was double charged and cannot log in" is genuinely both Billing and Technical. If you built a
multi-class classifier, the model is forced to pick one and you will spend weeks blaming the model
for a modelling error you made. Ask early: *can two labels be true at once?*

### 5.3 Regression subtleties

- **A bounded range is still regression.** Predicting a probability from 0 to 1, or a percentage,
  is regression even though the range is bounded.
- **Counts are awkward.** "How many tickets tomorrow" cannot be 43.7 and cannot be negative.
  Treating counts as ordinary regression works acceptably at large values and badly near zero.
- **Regression can be converted to classification by bucketing** ("cheap / medium / expensive"), and
  this is sometimes the right call: it is easier to evaluate, easier to explain, and often all the
  business needs. You lose precision. Make the choice deliberately.

### 5.4 The ordinal problem, worked

You must predict severity from `{low, medium, high, critical}`. Truth for one ticket is `critical`.

| Framing | Prediction `high` | Prediction `low` | Problem |
|---|---|---|---|
| Multi-class | Wrong (0 credit) | Wrong (0 credit) | Treats both errors as identical, but one is nearly right and one is dangerous |
| Regression (low=1…critical=4) | Error = 1 | Error = 3 | Captures ordering ✓, but assumes the gap low→medium equals high→critical, which is business-false |
| **Ordinal-aware** | Small penalty | Large penalty | Correct, but needs a custom metric and more effort |

**Practical guidance:** start with multi-class plus a **confusion matrix** (M3-L14) so you can *see*
how far off the errors are, and add a distance-weighted metric only if the business genuinely cares
about near-misses. Do not silently pick regression for ordinal data without saying so.

### 5.5 Ranking: the fifth shape

Search and recommendation output an *ordering*, not a label or a number. It is usually implemented
as regression (score each item) followed by a sort — but its **metrics are different** (MRR, nDCG,
Precision@k) because only the top few positions matter. This is the entire subject of M6-L13, and
RAG retrieval (Module 7) is fundamentally a ranking problem. Recognising ranking as its own shape
saves you from the common error of measuring your retriever with accuracy.

### 5.6 Generation is often several tasks at once

"Summarise this ticket and assign a category and suggest a reply" is **three** tasks:

1. Generation (summary)
2. Classification (category)
3. Generation (reply draft)

Each has its own success criterion and its own failure mode. Bundling them into one prompt and one
quality score means you cannot tell which part is broken. **Split tasks for evaluation even when you
bundle them for execution.** You will build exactly this in Project 5.

### 5.7 Assumptions and limitations

- These shapes describe **output structure**, not difficulty. Binary classification can be harder
  than generation.
- Modern LLMs can perform all four shapes, which tempts people to stop distinguishing them. Do not.
  The shape still determines the metric, and the metric determines whether you know it works.
- Some tasks genuinely resist all four (e.g. "make the user happy"). Those need decomposition into
  measurable proxies — M14-L04.

---

## 6. Worked example — turning a vague request into task shapes

**The request, as received from a customer:**

> "We get 500 support emails a day. We want AI to handle them."

This is not a task. It is a wish. Here is how to decompose it, which is a core Forward Deployed
Engineer skill (Module 14).

**Step 1 — list the decisions a human currently makes.** Shadow the workflow and write down every
judgement:

1. Is this actually support, or spam/marketing?
2. Which team should it go to?
3. Is it urgent?
4. Which known issue does it match, if any?
5. What should the reply say?
6. How long will this take to resolve?

**Step 2 — assign a shape to each.**

| # | Decision | Shape | Output type | Label space |
|---|---|---|---|---|
| 1 | Support or not | Binary classification | one of 2 | `{support, not_support}` |
| 2 | Which team | Multi-class classification | one of N | `{billing, technical, account, sales}` |
| 3 | Urgent? | Ordinal classification | ordered category | `{low, medium, high, critical}` |
| 4 | Matches known issue | **Ranking / retrieval** | ordered list of candidate issues | not a fixed list — the issue database changes |
| 5 | Reply text | Generation | free text | unbounded |
| 6 | Resolution time | Regression | a number of hours | continuous, ≥ 0 |

**Step 3 — notice what this immediately tells you.**

- Decisions 1–3 need **labelled historical tickets**. Do they have them? If tickets were never
  tagged, this is a data problem, not a model problem, and it must be solved first (M14-L03).
- Decision 4 is **not classification**, even though it feels like it. The set of known issues changes
  weekly, so you cannot fix a label space. It is retrieval + ranking → Module 6 and 7.
- Decision 5 is the only one needing generation, and it is the one with the **weakest evaluation
  story**. It should probably draft for a human rather than send autonomously (M8-L10).
- Decision 6 is regression, and is probably the least valuable. Worth asking whether anyone will act
  on it. Do not build it just because it is possible.

**Step 4 — sequence by value and risk.**

| Priority | Task | Why first |
|---|---|---|
| 1 | #2 routing | Highest volume saving, objectively measurable, low risk if wrong (a human re-routes) |
| 2 | #3 urgency | Cheap once #2 works, directly affects SLA |
| 3 | #4 known-issue matching | High value, but needs retrieval infrastructure |
| 4 | #5 reply drafting | Highest visible "wow", **highest risk**, weakest evaluation. Do it last, with a human in the loop |
| — | #1, #6 | Defer. Low value or unclear action |

Notice the recommendation puts the impressive generative feature **last**. That ordering is the
professional judgement this course is training. The customer asked for #5 first. M14-L07 teaches you
how to have that conversation.

---

## 7. Practical activity

**File:** [`labs/m1/l03_task_shapes.py`](../../labs/m1/l03_task_shapes.py) — standard library only.

```bash
python3 labs/m1/l03_task_shapes.py            # interactive drill
python3 labs/m1/l03_task_shapes.py --show     # full answer table
```

The drill gives you 14 real-world requests, several of them deliberately ambiguous or
mis-framed, and asks you to pick the shape. It then explains the deciding property and flags the
three classic mis-framings.

### 7.1 Important lines

| Construct | Why it matters |
|---|---|
| `Shape = Literal["classification", ...]` | A `Literal` type restricts a value to an exact set of strings — the type-system equivalent of a label space. Fitting, given the lesson. M2-L08. |
| `dataclass(frozen=True)` | Makes records immutable, so the quiz data cannot be modified by accident. M2-L07. |
| `textwrap.fill(...)` | Wraps explanation text to the terminal width so long reasons stay readable. |
| `sorted(counts.items(), key=lambda kv: -kv[1])` | Sorts by count descending. `lambda` = an inline anonymous function, like a JS arrow function. M2-L05. |

### 7.2 Expected output

`[EXECUTED]` 2026-09-07. The `--show` output is deterministic:

```
TASK SHAPE REFERENCE TABLE
==================================================================================
Request                                            Shape           Note
----------------------------------------------------------------------------------
Is this email spam?                                classification  binary
Route ticket to one of 4 teams                     classification  multi-class
Tag article with any of 20 topics                  classification  multi-label
Severity: low/medium/high/critical                 classification  ordinal - watch
What will this house sell for?                     regression      continuous
Minutes until food delivery arrives                regression      continuous
How many support tickets tomorrow?                 regression      count - awkward
Probability the customer churns                    regression      bounded 0-1
Find natural customer groups (undefined)           clustering      no label space
Group log lines to discover error types            clustering      needs human read
Order search results by relevance                  ranking         NOT classification
Which known issue does this match?                 ranking         label space changes
Write a reply to this ticket                       generation      unbounded output
Summarise and categorise and reply                 generation      3 TASKS - split it
==================================================================================
Counts: classification=4  regression=4  clustering=2  ranking=2  generation=2
```

**Verification:** the last line must read `classification=4  regression=4  clustering=2  ranking=2
  generation=2`.

---

## 8. Common mistakes and troubleshooting

1. **Framing ranking as classification.** "Which known issue is this?" looks like multi-class until
   you notice the issue list changes weekly and has 4,000 entries. Ask: *is the label space fixed
   and small?* If not, it is retrieval/ranking.
2. **Framing multi-label as multi-class.** Forces one answer where several are true. Ask: *can two
   labels be simultaneously correct?*
3. **Silently treating ordinal as either extreme.** Say which you chose and why.
4. **Believing clustering output.** k-means with `k=5` returns 5 clusters from pure random noise. It
   always returns something. Validate against a held-out interpretation, or do not ship it.
5. **Bundling three tasks and one score.** You lose the ability to diagnose. Split for evaluation.
6. **Choosing the shape by the algorithm you want to use.** Decide the shape from the *output the
   business needs*, then choose the method.

| Symptom | Likely cause | Fix |
|---|---|---|
| Model "can't decide" between two categories | Task is multi-label, modelled as multi-class | Re-frame; allow multiple labels |
| Accuracy is high but users complain | Metric does not match shape (e.g. accuracy on a ranking task) | Use MRR/nDCG — M6-L13 |
| Clusters look arbitrary | There may be no cluster structure | Test stability across seeds/subsets |
| Errors are "technically wrong but close" and you have no credit for it | Ordinal treated as multi-class | Confusion matrix, then distance-weighted metric |

---

## 9. Security, privacy, reliability and cost

- **Reliability.** The shape determines whether "correct" is even checkable. Classification and
  regression have objective ground truth; generation frequently does not. Systems whose output
  cannot be checked need human oversight (M10-L09) or grounding (Module 7).
- **Cost.** Ascending sharply left to right. A classification can be a small model costing
  microseconds; generation is an LLM call costing money per request. **Do not use generation for a
  classification task.** If the output is one of four labels, constrain it to those four labels
  (M5-L06) — you will save money and gain the ability to measure accuracy.
- **Privacy.** Clustering on customer data can re-identify individuals even when no single field
  does, because a small cluster is effectively an identifier. M10-L06.

---

## 10. Exercises

### Exercise 1 — Beginner (~10 min)

Name the shape and the output type for each:

1. Predict tomorrow's electricity demand in megawatts.
2. Decide whether a transaction is fraudulent.
3. Discover which of your 200 API endpoints have similar usage patterns.
4. Write release notes from a list of merged pull requests.
5. Assign each bug report a priority of P0/P1/P2/P3.
6. Choose the 5 most relevant documents for a question.

### Exercise 2 — Intermediate (~20 min)

A retailer says: *"We want AI to reduce returns."*

Decompose it as in §6. Produce a table with at least five distinct decisions, each with its task
shape, output type, whether a fixed label space exists, and what data would be required. Then
sequence them by value and risk, and state which one you would **not** build, with a reason.

### Exercise 3 — Challenge (~25 min)

You are given this specification by a product manager:

> "Classify each customer review into: Positive, Negative, Complaint about shipping, Complaint about
> product quality, Request for refund, or Spam."

There are at least **three** distinct modelling problems with this specification. Identify them,
explain the consequence of each, and rewrite the specification correctly. Then state what you would
need to check in the existing labelled data before trusting it.

Rubric in the answer key.

---

## 11. Quiz

**Q1.** What single property defines a task's shape?

- A. The algorithm used. B. The structure of the output. C. The size of the dataset.
- D. Whether it runs in the cloud.

**Q2.** Which is the clearest sign that a task is **not** classification?

- A. It has more than 10 categories.
- B. The set of possible answers is not fixed in advance and changes at runtime.
- C. It uses text as input.
- D. The model is a neural network.

**Q3.** A ticket says "I was double charged and I cannot log in". Your router must send it somewhere.
The correct framing is:

- A. Multi-class classification, picking the more important issue.
- B. Regression on an importance score.
- C. Multi-label classification, since Billing and Technical can both be true.
- D. Clustering.

**Q4.** Predicting severity `{low, medium, high, critical}` as a regression on 1–4 has which specific
drawback?

- A. Regression cannot handle four values.
- B. It assumes equal spacing between adjacent levels, which is usually false for business severity.
- C. It cannot be evaluated.
- D. It requires unlabelled data.

**Q5.** Why is "which known issue does this ticket match?" usually ranking rather than classification?

- A. Because the answer is text.
- B. Because ranking models are more accurate.
- C. Because the set of known issues is large and changes over time, so no fixed label space can be
  defined, and the useful output is an ordered shortlist rather than one label.
- D. Because classification cannot handle more than 100 classes.

**Q6.** A colleague runs k-means with k=4 on random noise and gets four clusters. What does this
demonstrate?

- A. The data has four groups.
- B. Clustering always returns groups whether or not real structure exists, so its output requires
  independent validation.
- C. k-means is broken.
- D. Four is the wrong value of k.

**Q7.** Your feature summarises a ticket, categorises it, and drafts a reply, and you track one
"quality score". What is the main engineering problem?

- A. It costs too much.
- B. A single score over three different tasks cannot tell you which component is failing, so you
  cannot diagnose or improve it.
- C. Summarisation and classification cannot use the same model.
- D. Nothing; a single score is best practice.

**Q8.** You need to output one of exactly four category labels and you are using an LLM. From this
lesson's cost reasoning, what should you do?

- A. Let it write free text and parse it later.
- B. Constrain the output to the four labels so the task stays classification — cheaper, and
  accuracy becomes measurable.
- C. Use a larger model for safety.
- D. Use clustering to find the categories at runtime.

**Q9.** Which pairing of task shape and metric is **mismatched**?

- A. Binary classification → precision and recall.
- B. Regression → mean absolute error.
- C. Ranking → accuracy.
- D. Ranking → nDCG.

**Q10.** *(Written, rubric-graded.)* A customer asks for "an AI that understands our documents". In
under 80 words, name two different task shapes this could mean, and give the one question you would
ask to tell them apart.

---

## 12. Revision notes

- Four shapes, defined by **output structure**: classification (label from a fixed set), regression
  (a number), clustering (groups nobody defined), generation (constructed content). Ranking is a
  fifth, and RAG retrieval is ranking.
- Classification vs generation: **does the list of possible answers exist?**
- Classification vs clustering: **did a human define the groups in advance?**
- Sub-shapes matter: binary / multi-class / **multi-label** / ordinal. Ask *can two labels be true
  at once?* and *do the categories have an order?*
- Ordinal data: multi-class loses the ordering, regression assumes equal spacing. Start with a
  confusion matrix.
- Clustering **always** returns clusters. That is not evidence of structure.
- Bundled tasks must be **split for evaluation** even if bundled for execution.
- The shape determines the metric; the metric determines whether you know it works.
- Cost rises steeply toward generation. Never use generation for a classification task.

---

## 13. Completion checklist

- [ ] I can name the four shapes and each output type from memory.
- [ ] I can state the deciding question separating classification from clustering, and from generation.
- [ ] I decomposed the §6 support-email request without looking.
- [ ] I scored 12/14 or better on the drill.
- [ ] I completed Exercises 1 and 2.
- [ ] I found all three problems in Exercise 3.
- [ ] I scored 7/10 on the quiz.

---

## 14. References

`[STABLE]`.

- Hastie, Tibshirani & Friedman, *The Elements of Statistical Learning*, Ch. 1 — supervised vs
  unsupervised framing. Free at <https://hastie.su.domains/ElemStatLearn/> `[UNVERIFIED]`
- scikit-learn user guide, "Choosing the right estimator" — a practical map from task to method.
  <https://scikit-learn.org/stable/user_guide.html> `[UNVERIFIED]`

---

## 15. Next lesson

→ [M1-L04 — Data Vocabulary](M1-L04-data-vocabulary.md)

You now know what shape the output takes. Next: the precise vocabulary for the *inputs* — dataset,
feature, label, model, algorithm — which you need before any of Module 3 will make sense.
