# M1-L05 — Parameters vs Hyperparameters

| | |
|---|---|
| **Lesson ID** | M1-L05 |
| **Difficulty** | 1 (Intro) |
| **Estimated study time** | 0.75 hour |
| **Prerequisites** | [M1-L04](M1-L04-data-vocabulary.md) |

---

## 1. Learning objectives

1. **Define** parameter and hyperparameter, and **state** the one test that separates them.
2. **Classify** a list of numbers from a real system into the correct category.
3. **Explain** why hyperparameters must be tuned on a validation set and never on the test set.
4. **Identify** the hyperparameters of an LLM application, including ones that are not obviously
   "model settings".
5. **Estimate** the cost of a hyperparameter search and explain why grid search scales badly.

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **Parameter** | A number **inside** the model that the training algorithm learned from data. |
| **Weight** | The most common kind of parameter: a multiplier applied to an input. |
| **Bias** (the parameter) | A learned constant added after multiplication. Nothing to do with fairness bias — an unfortunate name collision. |
| **Hyperparameter** | A number or choice **you** set *before* training, which controls how training happens or how the model is shaped. |
| **Parameter count** | How many learned numbers a model has. "8 billion parameters" means 8 × 10⁹ weights. |
| **Hyperparameter tuning** | Searching for hyperparameter values that produce the best validation performance. |
| **Grid search** | Trying every combination from a fixed list of candidate values. |
| **Random search** | Sampling combinations at random. Usually more efficient than grid search. |
| **Validation set** | Data held out to compare hyperparameter choices. Detailed in M1-L06. |
| **Learning rate** | A hyperparameter controlling how big a step training takes each update. M3-L12. |
| **Epoch** | One full pass over the training data. A hyperparameter. M3-L12. |

---

## 3. Plain-language explanation

A trained model contains a lot of numbers. They come from two completely different places, and
mixing them up leads to a specific, serious mistake.

- **Parameters are learned.** The training algorithm sets them. You never type them. A model with 8
  billion parameters has 8 billion numbers that were computed from data. Nobody chose them; nobody
  can meaningfully read them.
- **Hyperparameters are chosen.** You type them in before training starts. How fast should learning
  go? How many layers? How many trees? How long to train? These control the *process* and the
  *shape*, not the content.

**The one test:**

> Did a training algorithm compute this number from data (**parameter**), or did a human type it in
> before training began (**hyperparameter**)?

That is the whole distinction. Everything else follows.

Why it matters so much: **parameters are fitted on the training set, so the training set is
"used up" for them. Hyperparameters are chosen by comparing results, so whatever data you compare on
gets "used up" too.** If you compare hyperparameters on your test set, your test set is no longer an
honest estimate of future performance — you have fitted to it, just more slowly and by hand. This is
the reason a *third* dataset exists, and M1-L06 is entirely about it.

### Connecting to what you already know

| Web analogy | Category |
|---|---|
| Values in your database rows | Parameters — produced by the system running |
| Values in your config file / env vars | Hyperparameters — you set them before starting |
| Connection pool size, timeout, retry count | Hyperparameters |
| Cached query results | Parameters |

The config-file intuition is accurate and useful: **hyperparameters are the config of training.**
And like config, they belong in version control, they belong in your experiment log, and changing
one silently is how you lose reproducibility (M3-L14).

---

## 4. Analogy

**Baking bread.**

- **Hyperparameters** = oven temperature, baking time, tin size, flour type. You choose these before
  baking.
- **Parameters** = the actual internal structure of the finished loaf — crumb, crust thickness,
  moisture distribution. These emerge from the process; you cannot type them in.
- **Training** = the bake.
- **Hyperparameter tuning** = baking many loaves at different temperatures and picking the best.

### Where the analogy breaks

1. **You can taste a loaf directly; you cannot inspect parameters usefully.** You judge a model only
   through its behaviour on held-out data.
2. **Tasting the loaf you will serve to guests is fine. "Tasting" your test set is not.** Every time
   you look at test performance and change something, you leak information from the test set into
   your decisions. Do this twenty times and your test score is optimistic. This disanalogy is the
   single most important point in the lesson.
3. **Bread has a handful of settings; models can have dozens**, and they interact. The best learning
   rate depends on the batch size, which depends on the model size.
4. **A loaf is finished; a model can be trained further.** Fine-tuning (Module 13) resumes from
   existing parameters.

---

## 5. Detailed technical explanation

### 5.1 Side by side

| | Parameters | Hyperparameters |
|---|---|---|
| **Set by** | Training algorithm | Human (or a search procedure) |
| **When** | During training | Before training |
| **Count** | Thousands to trillions | Typically 3–30 |
| **Stored in** | The model file | Config, code, experiment log |
| **Examples** | Weights, biases, embedding tables | Learning rate, epochs, batch size, layer count, tree depth, regularisation strength |
| **Changing one** | Requires retraining | Requires retraining (they *cause* the parameters) |
| **Tuned on** | Training set | **Validation set** |
| **If you tune on the test set** | n/a | Your test estimate becomes dishonest |

### 5.2 Concrete examples across model families

| Model family | Parameters (learned) | Hyperparameters (chosen) |
|---|---|---|
| Linear regression | One coefficient per feature, plus intercept | Regularisation strength; which features to include |
| Logistic regression | Coefficients, intercept | Regularisation type (L1/L2) and strength; solver; max iterations |
| Decision tree | The split feature and threshold at each node | Max depth; min samples per leaf; splitting criterion |
| Random forest | Every tree's splits | Number of trees; max depth; features per split |
| Neural network | All weights and biases in every layer | Layer count; units per layer; learning rate; batch size; epochs; activation function; dropout rate; optimiser |
| Transformer / LLM | Attention and feed-forward weights, embedding table | Layer count; hidden size; number of attention heads; context length; vocabulary size; learning-rate schedule |
| k-means clustering | The cluster centre coordinates | **k**, the number of clusters |
| Naive Bayes (M1-L02) | The word probabilities you counted | The smoothing constant (we used 1) |

That last row is worth pausing on. In M1-L02 you added 1 to every count. **That 1 was a
hyperparameter** — a value chosen by a human, not learned. You could have used 0.5 or 2 and got
different behaviour. You chose it before "training" (counting) began.

### 5.3 The hyperparameters of an LLM application

This is the part that matters most for this course, because when you build LLM applications the
model's parameters are frozen and someone else's problem. **Your** hyperparameters are different, and
most teams never write them down.

| Your hyperparameter | Typical values | What it controls | Lesson |
|---|---|---|---|
| Model choice | sonnet / opus / haiku | Quality, latency, cost | M5-L16 |
| Temperature | 0.0 – 1.0 | Output randomness | M4-L14 |
| Top-p | 0.9 – 1.0 | Sampling breadth | M4-L14 |
| Max output tokens | 256 – 8192 | Length cap, cost cap | M4-L15 |
| System prompt text | prose | Behaviour — the biggest one | M5-L02 |
| Number of few-shot examples | 0 – 20 | Accuracy vs cost | M5-L03 |
| Chunk size | 200 – 1500 tokens | Retrieval granularity | M7-L06 |
| Chunk overlap | 0 – 200 tokens | Boundary loss | M7-L06 |
| `k` (chunks retrieved) | 3 – 20 | Recall vs noise vs cost | M7-L11 |
| Reranking on/off, rerank depth | boolean, 20–100 | Precision vs latency | M6-L12 |
| Similarity threshold for abstention | 0.0 – 1.0 | When to say "I don't know" | M7-L13 |
| Retry count, timeout | 1–3, 10–60 s | Reliability | M2-L14 |
| Agent step limit | 5 – 30 | Runaway prevention | M8-L15 |

**Two consequences you should internalise now:**

1. **Your prompt is a hyperparameter.** It is a value you chose before "running", it materially
   changes behaviour, and changing it invalidates previous measurements. Therefore it must be
   version-controlled and every evaluation result must record which prompt version produced it.
   That is the whole argument for M5-L12, and it follows directly from this lesson.
2. **You are tuning these.** Whether or not you call it tuning, every time you try `k=5` instead of
   `k=3` and check whether answers improved, you are doing hyperparameter search — and if you
   checked on your final test set, you just contaminated it.

### 5.4 Why tuning needs its own dataset

Suppose you try 20 combinations of chunk size and `k`, and pick whichever scored best on a 100-item
evaluation set. Even if all 20 were genuinely equal in quality, the best of 20 noisy measurements
will look better than the true average, purely by chance. That gap is **optimistic bias**, and it
grows with the number of things you tried.

So the reported score of the winner is **not** an unbiased estimate of its real performance. To get
an honest number you need data that played no part in the selection. Hence three splits:

| Split | Used for | Touched how often |
|---|---|---|
| **Training** | Fitting parameters | Constantly |
| **Validation** | Comparing hyperparameters | Many times |
| **Test** | Final honest estimate | **Once**, at the end |

M1-L06 covers the mechanics; M1-L09 covers what goes wrong when this is violated.

### 5.5 Search strategies and their cost

If you have 3 hyperparameters with 5 candidate values each, **grid search** tries 5 × 5 × 5 = **125**
combinations. Add a fourth: 625. This is combinatorial explosion, and with each run costing money
(LLM calls) or hours (training), it becomes unaffordable fast.

| Strategy | How | When to use | Cost |
|---|---|---|---|
| Manual | Change one thing, observe | Few hyperparameters, good intuition, expensive runs | Lowest |
| Grid search | Every combination | ≤ 3 hyperparameters, cheap runs | Exponential |
| Random search | Sample combinations randomly | > 3 hyperparameters | You choose the budget |
| Bayesian / model-based | Use past results to choose the next trial | Expensive runs, many hyperparameters | Efficient but complex |

**Random search usually beats grid search for the same budget.** The reason is not obvious and is
worth knowing: in most problems only a few hyperparameters actually matter. A grid with 5 values per
parameter tests only 5 distinct values of the important one, no matter how many total runs you do,
because the grid repeats the same values. Random search tries a different value of the important
parameter on every single run. This result is from Bergstra & Bengio (2012) and it is one of the more
useful practical findings in ML.

For LLM applications the practical advice is simpler: **change one thing at a time, record every
result, and keep the test set closed.** With runs costing real money, disciplined manual search beats
automated search almost every time at your scale.

### 5.6 Assumptions and limitations

- The parameter/hyperparameter line blurs slightly in advanced methods that learn their own learning
  rates. Ignore this until it is relevant.
- "Bias" is overloaded: the learned constant in `wx + b`, and unfair treatment of groups (M10-L08).
  Always say which you mean.
- Parameter count is a poor proxy for quality. A well-trained 8B model can beat a badly-trained 70B
  model. Never accept parameter count as evidence.

---

## 6. Worked example

A tiny linear model predicting SLA breach risk from two features:

$$\text{score} = w_1 x_1 + w_2 x_2 + b$$

Every symbol: `x₁` = body length (scaled), `x₂` = prior tickets, `w₁` and `w₂` = weights, `b` = bias.

**Before training**, you choose:

| Choice | Value | Category |
|---|---|---|
| Learning rate | 0.01 | Hyperparameter |
| Epochs | 100 | Hyperparameter |
| Which 2 features to use | body_len, prior | Hyperparameter |
| Initial `w₁`, `w₂`, `b` | 0.0, 0.0, 0.0 | Initialisation — a *hyperparameter choice*, but the values then become parameters |

**After training**, the algorithm has produced:

| Number | Value | Category |
|---|---|---|
| `w₁` | 0.0034 | **Parameter** |
| `w₂` | −0.21 | **Parameter** |
| `b` | 0.15 | **Parameter** |

You did not choose 0.0034. The algorithm computed it. You *did* choose 0.01 and 100.

**Now the tuning trap, with numbers.** You try three learning rates and measure on your test set:

| Learning rate | Test accuracy |
|---|---|
| 0.001 | 71% |
| 0.01 | 78% |
| 0.1 | 64% |

You report "78% accuracy". **This number is dishonest**, and here is precisely why: you selected
0.01 *because* it scored highest on those specific 100 test examples. Part of that 78% is genuine
skill and part is luck — 0.01 happened to suit the particular examples in that set. On fresh data the
true figure might be 74%.

The fix costs nothing: make the comparison on a **validation** set, then measure the winner **once**
on the untouched test set. Suppose that gives 75%. That 75% is honest and is what you report.

Notice the difference is only 3 points here, with 3 trials. Try 50 prompt variants against one
100-item set — which is exactly what LLM development feels like — and the gap becomes large enough to
make a system look production-ready when it is not.

---

## 7. Practical activity

**File:** [`labs/m1/l05_hyperparameter_sort.py`](../../labs/m1/l05_hyperparameter_sort.py)

```bash
python3 labs/m1/l05_hyperparameter_sort.py            # drill
python3 labs/m1/l05_hyperparameter_sort.py --show     # reference table
python3 labs/m1/l05_hyperparameter_sort.py --demo     # optimistic-bias simulation
```

The `--demo` flag is the important one. It simulates the §6 trap: it creates a number of *equally
good* candidate settings, scores each on a small random evaluation set, picks the winner, and then
scores that winner on fresh data — showing you the size of the optimistic gap as the number of trials
grows. No model, no libraries: just the statistics of picking a maximum.

### 7.1 Important lines

| Construct | Why |
|---|---|
| `random.Random(seed)` | A private random generator, so the demo is reproducible without disturbing global state. |
| `sum(rng.random() < true_rate for _ in range(n))` | Simulates `n` coin flips at a fixed true success rate. `True` counts as 1 in Python — a common idiom. |
| `max(results, key=lambda r: r.val_score)` | Picks the best candidate *by validation score*, exactly as a human tuner would. |
| `statistics.mean(...)` | Averages the gap over many repeats so you see the systematic effect, not one lucky run. |

### 7.2 Expected output

`[EXECUTED]` 2026-09-07. Deterministic (fixed seed):

```
================================================================
OPTIMISTIC BIAS: why you must not tune on the test set
================================================================
Setup: every candidate is EQUALLY GOOD - true success rate 0.70.
       Any difference we observe is pure luck.
       Eval set = 100 items. Repeated 2000 times.

 trials   best score on the set   true score of winner   optimism
--------------------------------------------------------------------
      1                  0.6995                 0.7000    -0.0005
      3                  0.7389                 0.7000    +0.0389
      5                  0.7523                 0.7000    +0.0523
     10                  0.7702                 0.7000    +0.0702
     20                  0.7832                 0.7000    +0.0832
     50                  0.7989                 0.7000    +0.0989
    100                  0.8106                 0.7000    +0.1106

Reading this table:
  Every candidate is identical - true rate 0.70 for all of them.
  Yet after trying 50, the winner APPEARS to score noticeably higher.
  That gap is entirely selection luck. There is no real gain.
  Report it and you have overstated your system by that much.

  The fix: pick the winner on a VALIDATION set, then measure it
  ONCE on a test set that played no part in the choice.
================================================================
```

Sit with these numbers for a moment, because they are worse than most engineers expect.

Every one of those candidates is **identical**. There is no better setting to find. Yet a tuner who
tries 20 options and keeps the best will report **78.3%** for a system whose real performance is
**70%**. At 100 options — roughly a fortnight of enthusiastic prompt iteration — the reported figure
reaches **81%**, an overstatement of eleven percentage points, produced entirely by choosing the
maximum of noisy measurements.

This is not a subtle statistical curiosity. It is the mechanism behind a large share of AI projects
that demo well and disappoint in production. Nobody lied; they measured a maximum and reported it as
an average.

Two properties of the effect are worth memorising:

- **It grows with the number of things you try.** Every variant you test inflates it further.
- **It shrinks as the evaluation set grows.** With 1,000 items instead of 100 the noise in each
  measurement is smaller, so the maximum sits closer to the truth. You will confirm this yourself in
  Exercise 3.

**Verification:** the `true score of winner` column must stay at 0.7000 throughout, while `best score`
climbs. That contrast is the lesson: the improvement is entirely illusory.

---

## 8. Common mistakes and troubleshooting

1. **Tuning on the test set.** The headline mistake. Includes informal versions: "I tried a few
   prompts and kept the one that scored best on our eval set" — if that set is also your final
   report number, it is contaminated.
2. **Not recording hyperparameters with results.** An experiment log without settings is not a
   result; it is an anecdote.
3. **Treating the prompt as not-a-hyperparameter.** It is the most influential one you have.
4. **Grid-searching everything.** Exponential cost for little benefit. Change one thing at a time.
5. **Confusing the two meanings of "bias".** Say "the intercept term" or "unfair outcomes".
6. **Quoting parameter count as evidence of quality.**
7. **Changing several things at once and not knowing which helped.**

| Symptom | Cause | Fix |
|---|---|---|
| Great eval score, disappointing in production | Tuned on the evaluation set | Hold out a fresh test set and re-measure once |
| Cannot reproduce last week's number | Hyperparameters not recorded | Log every setting, including prompt version and seed |
| Tuning takes forever | Grid search over many parameters | Random search, or reduce to the 2–3 that matter |
| Results swing wildly between runs | Seed not fixed; eval set too small | Fix seeds; enlarge the eval set (M5-L18) |

---

## 9. Security, privacy, reliability and cost

- **Cost.** Hyperparameter search multiplies cost by the number of trials. 50 prompt variants × 200
  eval items × 2 LLM calls each = 20,000 calls. Estimate before you start (M5-L15).
- **Reliability.** Undocumented hyperparameters are a leading cause of "it worked yesterday".
  Treat them as deployable configuration with the same review as code.
- **Governance.** Hyperparameters — especially the prompt and the abstention threshold — are part of
  the system's behaviour and must be versioned and auditable (M10-L13). A changed threshold can alter
  who gets an answer and who gets refused.
- **Security.** If hyperparameters are loaded from a mutable store, that store is an attack surface.
  Setting `temperature` high or replacing a system prompt changes behaviour without any code change,
  and would not appear in a code review.

---

## 10. Exercises

### Exercise 1 — Beginner (~8 min)

Classify each as parameter or hyperparameter:

1. The number of trees in a random forest.
2. The coefficient on `age` in a logistic regression.
3. The temperature you pass to an LLM API.
4. The values in an LLM's embedding table.
5. The number of clusters `k`.
6. The coordinates of a cluster centre.
7. Your system prompt.
8. The smoothing constant in Naive Bayes.

### Exercise 2 — Intermediate (~15 min)

You are tuning a RAG system with: chunk size ∈ {256, 512, 1024}, overlap ∈ {0, 50, 100},
k ∈ {3, 5, 10}, reranking ∈ {on, off}.

1. How many combinations in a full grid? Show the arithmetic.
2. Each evaluation runs 150 questions at roughly £0.004 per question. What does a full grid cost?
3. You have £50. Propose a strategy, saying what you would fix, what you would vary, and in what
   order. Justify your choices with reference to which hyperparameters likely matter most.
4. Which of these four is *not* independent of the others? Explain the interaction.

### Exercise 3 — Challenge (~20 min)

Run the demo with your own numbers: modify the lab so the true rate is 0.85 and the eval set is only
30 items, then run it.

1. Report the optimism at 20 trials, and compare with the 100-item result.
2. Explain the relationship between evaluation set size and optimistic bias.
3. A colleague says "we ran 40 prompt variants against our 40-question eval set and got 92%; we are
   ready to ship". Write a 100-word response using your numbers.
4. State one situation where accepting some optimistic bias is a reasonable engineering trade-off,
   and what you would do to bound the risk.

---

## 11. Quiz

**Q1.** The single test distinguishing a parameter from a hyperparameter is:

- A. Whether it is an integer or a float.
- B. Whether a training algorithm computed it from data, or a human set it before training.
- C. Whether it is stored in the model file.
- D. Whether it affects accuracy.

**Q2.** In `k`-means clustering, which is the hyperparameter?

- A. The coordinates of each cluster centre.  B. The value of `k`.
- C. The distance metric output.  D. The cluster assignment of each point.

**Q3.** Why must hyperparameters be compared on a validation set rather than the test set?

- A. The test set is usually too small.
- B. Selecting the best of several noisy measurements produces an optimistically biased estimate, so
  the test set must play no part in the choice to remain an honest estimate.
- C. Validation sets are larger.
- D. It is a convention with no practical consequence.

**Q4.** In the lab demo, all candidates had a true success rate of 0.70, yet after 50 trials the
winner appeared to score 0.78. What does the 0.08 represent?

- A. A genuine improvement from tuning.
- B. Selection luck — the maximum of 50 noisy measurements exceeds the true value, with no real gain.
- C. A bug in the simulation.
- D. Overfitting of model parameters.

**Q5.** Which of these is a hyperparameter of an *LLM application* you build?

- A. The attention weights in layer 12.
- B. The embedding table values.
- C. The number of retrieved chunks `k`.
- D. The learned token frequencies.

**Q6.** Why is your system prompt correctly described as a hyperparameter?

- A. Because it is stored as text.
- B. Because you set it before running, it materially changes behaviour, and changing it invalidates
  previous measurements — so it must be versioned and recorded with every result.
- C. Because the model learns it.
- D. It is not; prompts are inputs.

**Q7.** With 4 hyperparameters at 5 candidate values each, a full grid search requires how many runs?

- A. 20  B. 25  C. 625  D. 1024

**Q8.** Why does random search usually outperform grid search at equal budget?

- A. Random search uses better values.
- B. Only a few hyperparameters usually matter, and a grid repeatedly tests the same few values of
  the important one, whereas random search tries a new value of it on every run.
- C. Grid search cannot handle floats.
- D. Random search needs no validation set.

**Q9.** A team reports "our model has 70 billion parameters" as evidence of quality. The best
response is:

- A. Accept it; parameter count measures capability.
- B. Parameter count describes size, not quality — a well-trained smaller model can outperform a
  poorly-trained larger one. Ask for evaluation results on a held-out set instead.
- C. Ask them to reduce it.
- D. Ask which GPU it runs on.

**Q10.** *(Written, rubric-graded.)* In under 80 words, explain to a project manager why the team
cannot report the best score they have seen during development as the expected production accuracy.

---

## 12. Revision notes

- **Parameter** = learned by the algorithm from data (weights, biases, cluster centres, counted
  probabilities). **Hyperparameter** = chosen by you before training (learning rate, epochs, `k`,
  depth, smoothing constant, **your prompt**).
- One test: *did an algorithm compute it, or did a human type it?*
- Parameters number in the millions–trillions; hyperparameters in the tens.
- **Tune hyperparameters on validation. Touch the test set once.** Selecting the best of N noisy
  results is optimistically biased, and the bias grows with N and shrinks with eval-set size.
- In LLM apps *your* hyperparameters are: model, temperature, top-p, max tokens, prompt text,
  few-shot count, chunk size, overlap, `k`, reranking, thresholds, retries, step limits.
- Grid search is exponential; random search usually wins at equal budget because few
  hyperparameters matter.
- Parameter count is not evidence of quality.
- "Bias" means two different things. Disambiguate.

---

## 13. Completion checklist

- [ ] I can state the one distinguishing test.
- [ ] I classified all 8 items in Exercise 1 correctly.
- [ ] I ran `--demo` and can explain why the true-score column stays flat.
- [ ] I can list at least six hyperparameters of an LLM application.
- [ ] I completed Exercise 2's cost arithmetic.
- [ ] I scored 7/10 on the quiz.

---

## 14. References

`[STABLE]` concepts.

- Bergstra & Bengio, "Random Search for Hyper-Parameter Optimization", JMLR 2012 — the source of the
  §5.5 result. `[UNVERIFIED]`
- scikit-learn user guide, "Tuning the hyper-parameters of an estimator".
  <https://scikit-learn.org/stable/modules/grid_search.html> `[UNVERIFIED]`

---

## 15. Next lesson

→ [M1-L06 — Training, Validation, Testing, Inference](M1-L06-training-validation-testing-inference.md)

This lesson kept referring to a validation set and a test set. The next lesson defines them
precisely, shows the mechanics of splitting, and explains the four phases of a model's life.
