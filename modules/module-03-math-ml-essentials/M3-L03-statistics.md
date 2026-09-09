# M3-L03 — Mean, Variance, Standard Deviation and Distributions

| | |
|---|---|
| **Lesson ID** | M3-L03 |
| **Difficulty** | 1 (Intro) |
| **Estimated study time** | 1.75 hours |
| **Prerequisites** | [M3-L01](M3-L01-vectors-matrices.md) |

---

## 1. Learning objectives

1. **Compute** mean, variance and standard deviation by hand and **state** what each describes.
2. **Explain** why the mean alone is misleading, and when to prefer the median.
3. **Read** a distribution's shape and **identify** skew from summary statistics.
4. **Compute** a percentile and **explain** why latency is reported as p95 rather than as an average.
5. **Decide** whether a measured difference is large enough to act on.

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **Population** | Every item you care about. |
| **Sample** | The subset you actually measured. |
| **Mean** (μ or x̄) | The arithmetic average: sum divided by count. |
| **Median** | The middle value when sorted. |
| **Mode** | The most frequent value. |
| **Variance** (σ²) | The average squared distance from the mean. |
| **Standard deviation** (σ) | The square root of variance; in the same units as the data. |
| **Range** | Maximum minus minimum. |
| **Percentile** | The value below which a given percentage of the data falls. |
| **Quartile** | The 25th, 50th and 75th percentiles. |
| **IQR** | Interquartile range: Q3 − Q1. |
| **Distribution** | How values are spread across their possible range. |
| **Normal (Gaussian)** | The symmetric bell-shaped distribution. |
| **Skew** | Asymmetry. Right-skewed means a long tail of high values. |
| **Outlier** | A value far from the rest. |
| **Standard error** | The standard deviation of a sample statistic; how much it would vary between samples. |

---

## 3. Plain-language explanation

You have a collection of numbers — response times, similarity scores, accuracy across runs — and you
need to describe them without listing every value.

Two questions cover most of it:

1. **Where is the middle?** → mean, median, mode
2. **How spread out is it?** → variance, standard deviation, range, IQR

**The mean is the average.** Add everything, divide by the count.

```
[2, 4, 4, 4, 5, 5, 7, 9]
mean = (2+4+4+4+5+5+7+9) / 8 = 40 / 8 = 5
```

**The standard deviation says how far values typically sit from the mean.** A small σ means the
values cluster; a large σ means they scatter.

**The critical practical point:** the mean alone is almost never enough. These two datasets have the
same mean:

```
A = [5, 5, 5, 5, 5]        mean 5, σ 0     - completely predictable
B = [1, 1, 5, 9, 9]        mean 5, σ ~3.6  - wildly variable
```

Reporting "mean 5" for both is technically true and practically useless. **Always report a measure of
spread alongside a measure of centre.** In this course that rule applies to every evaluation result
(M3-L14), every latency figure (M13-L11), and every similarity threshold (M6-L13).

---

## 4. Analogy

**Describing a class's exam results.** The mean is the class average. The standard deviation says
whether everyone scored similarly or whether there were both failures and top marks. The median is
the score of the middle student — unaffected by one person scoring zero.

### Where the analogy breaks

1. **Exam scores are bounded 0–100 and roughly symmetric. Latency is not.** It has no upper bound and
   is strongly right-skewed, which is why §5.5 says the mean is the wrong summary for it.
2. **A class is a complete population; your measurements are a sample.** A sample statistic is itself
   uncertain, and that uncertainty (§5.6) is what decides whether a difference is real.
3. **Every student's mark matters equally. In latency, the slow tail matters more** — those are the
   users who leave.
4. **The analogy suggests one number can summarise.** For skewed data you need several: median, p95,
   p99 and the maximum tell four different stories.

---

## 5. Detailed technical explanation

### 5.1 Mean, median, mode

$$\bar{x} = \frac{1}{n}\sum_{i=1}^{n} x_i$$

Every symbol: `x̄` ("x-bar") is the sample mean, `n` is the count, `xᵢ` is the *i*-th value, `Σ` means
add them all up.

```
data = [2, 4, 4, 4, 5, 5, 7, 9]
mean   = 40 / 8 = 5.0
median = (4 + 5) / 2 = 4.5      # even count: average the middle two
mode   = 4                       # appears three times
```

**When to use which:**

| Statistic | Use when | Weakness |
|---|---|---|
| Mean | Data is roughly symmetric | One outlier drags it |
| **Median** | Data is **skewed or has outliers** | Ignores magnitude of extremes |
| Mode | Categorical data | May not exist or be unique |

**One outlier demonstrates the difference:**

```
[1, 2, 3, 4, 5]        mean 3.0    median 3
[1, 2, 3, 4, 500]      mean 102.0  median 3
```

The mean moved by a factor of 34; the median did not move at all. **The median is robust; the mean is
not.**

### 5.2 Variance and standard deviation

Variance is the average squared distance from the mean:

$$\sigma^2 = \frac{1}{n}\sum_{i=1}^{n}(x_i - \bar{x})^2$$

Worked on `[2, 4, 4, 4, 5, 5, 7, 9]`, mean 5:

| xᵢ | xᵢ − x̄ | (xᵢ − x̄)² |
|---|---|---|
| 2 | −3 | 9 |
| 4 | −1 | 1 |
| 4 | −1 | 1 |
| 4 | −1 | 1 |
| 5 | 0 | 0 |
| 5 | 0 | 0 |
| 7 | 2 | 4 |
| 9 | 4 | 16 |
| | **Σ** | **32** |

`σ² = 32 / 8 = 4` and `σ = √4 = **2**`.

**Why squared?** Squaring makes every deviation positive (so they do not cancel) and weights large
deviations more heavily. The cost is that variance is in *squared units* — squared milliseconds means
nothing — which is why you take the square root and report **standard deviation**, in the original
units.

**Population versus sample.** Dividing by `n` gives the *population* variance. Dividing by `n − 1`
gives the *sample* variance, which corrects a systematic underestimate when you are estimating a
population from a sample.

```python
np.var(data)          # divides by n      (population, ddof=0 default)
np.var(data, ddof=1)  # divides by n - 1  (sample)
```

**NumPy defaults to `ddof=0`; pandas defaults to the sample version.** They will disagree on the same
data, which surprises people. For large `n` the difference is negligible; for `n = 8` it is 14%.

### 5.3 Distributions

A **normal distribution** is symmetric and bell-shaped, described entirely by μ and σ:

| Range | Contains |
|---|---|
| μ ± 1σ | ~68% |
| μ ± 2σ | ~95% |
| μ ± 3σ | ~99.7% |

This "68–95–99.7 rule" is worth memorising: it tells you at a glance whether a value is unusual.

**But most things you measure are not normal:**

| Quantity | Typical shape |
|---|---|
| Human heights | Normal |
| **API latency** | **Right-skewed with a long tail** |
| Document lengths | Right-skewed |
| Cosine similarities | Often narrow and clustered (M3-L02 §5.7) |
| Tokens per request | Right-skewed |

**Right-skewed** means most values are small with a few very large ones. The mean is dragged above
the median. If `mean > median`, suspect right skew — and reconsider whether the mean is the right
summary.

### 5.4 Percentiles

The *p*-th percentile is the value below which *p* percent of the data falls.

```
sorted: [10, 12, 13, 15, 18, 20, 25, 40, 80, 200]
p50 (median) = (18 + 20) / 2 = 19
p90 = 80
p99 ≈ 200
```

**For latency this is the standard reporting form**, and the reason is visible above: the mean of
that data is 43.3, which is larger than 8 of the 10 values. It describes almost nobody's experience.

| Statistic | Answers |
|---|---|
| Mean | Meaningless for skewed data |
| p50 (median) | "The typical user" |
| p95 | "Almost everyone" |
| **p99** | **"The unhappy few"** |
| Max | The worst case |

**p99 matters more than it looks.** At 1,000 requests per minute, p99 is 10 users per minute having a
bad time — and a single page view often makes several requests, so the proportion of *users* who hit
a p99 response is far higher than 1%.

### 5.5 Standard error — is a difference real?

You measure prompt A at 82% and prompt B at 85% on 100 examples. Is B better?

For a proportion, the standard error is:

$$SE = \sqrt{\frac{p(1-p)}{n}}$$

With `p = 0.82` and `n = 100`: `SE = √(0.82 × 0.18 / 100) = √0.001476 ≈ **0.038**`, so about
**3.8 percentage points**.

A rough 95% interval is `p ± 2 × SE` → 82% ± 7.7%, i.e. **74% to 90%**.

**The 3-point difference is well inside the noise.** You cannot distinguish these prompts with 100
examples.

**How many would you need?** SE shrinks with `√n`, so to halve it you need **four times** the data.
For a 3-point difference you want SE around 1 point, needing roughly `n ≈ 1,500`.

This single calculation prevents a large amount of wasted effort, and it is why M5-L18 insists on
eval-set size. Combined with the M1-L05 optimistic-bias result, it explains why small evaluation
sets produce confident nonsense.

### 5.6 Assumptions and limitations

- These summaries assume the values are comparable. Mixing latencies from two endpoints produces a
  meaningless average.
- The normal-distribution rules apply only to normal data. Applying "μ ± 2σ" to latency badly
  underestimates the tail.
- The standard-error formula assumes independent samples. Correlated examples (M1-L06 grouping) make
  it optimistic.
- Percentiles from small samples are unstable: p99 of 100 points is essentially the maximum.

---

## 6. Worked example — reading an evaluation result

Two prompts, each evaluated on 200 questions, with per-question latency recorded.

**Prompt A:** 164/200 correct. **Prompt B:** 172/200 correct.

**Step 1 — accuracy.** A: 164/200 = **82.0%**. B: 172/200 = **86.0%**. B looks 4 points better.

**Step 2 — is it real?**

`SE_A = √(0.82 × 0.18 / 200) = √0.000738 = **0.0272**` (2.72 points)
`SE_B = √(0.86 × 0.14 / 200) = √0.000602 = **0.0245**` (2.45 points)

For the *difference*, combine them: `SE_diff = √(0.0272² + 0.0245²) = √0.00134 ≈ **0.0366**`
(3.66 points).

The observed difference is 4.0 points; the standard error of that difference is 3.7 points. The
difference is roughly **1.1 standard errors** — well short of the ~2 conventionally needed for
confidence.

**Conclusion: not distinguishable.** B might be better; the data cannot show it. To resolve a
4-point difference you need roughly 800–1,000 examples per prompt.

**Step 3 — latency.** Prompt A's 200 latencies (ms), summarised:

```
mean 850    median 620    p95 2,100    p99 4,800    max 9,200    σ 780
```

**Read `mean 850` against `median 620`.** The mean is 37% higher, so the data is strongly
right-skewed. Reporting "average latency 850 ms" describes a user who does not exist: most
requests complete in about 620 ms, and a few take many seconds.

**Step 4 — what to report.** Not "82% accurate, 850 ms average", which is two misleading numbers.
Instead:

> Prompt A: 82.0% ± 2.7% accuracy (n=200). Latency p50 620 ms, p95 2.1 s, p99 4.8 s.
> Prompt B: 86.0% ± 2.5% accuracy (n=200). The 4-point difference is within noise
> (≈1.1 SE); ~900 examples per prompt would be needed to resolve it.

**Step 5 — the decision that follows.** Do not ship B claiming an improvement. Either collect more
evaluation data, or accept that the prompts are equivalent on this metric and choose on another basis
— cost, latency or maintainability.

---

## 7. Practical activity

**File:** [`labs/m3/l03_statistics.py`](../../labs/m3/l03_statistics.py)

**Requires the venv:**

```bash
source .venv/bin/activate
python labs/m3/l03_statistics.py
```

Reproduces every hand calculation, shows mean-versus-median under an outlier, generates a realistic
right-skewed latency distribution with an ASCII histogram, computes percentiles, demonstrates the
`ddof` discrepancy, and simulates how often a 4-point difference appears by chance at various sample
sizes.

### 7.1 Important lines

| Construct | Why |
|---|---|
| `np.var(x)` vs `np.var(x, ddof=1)` | Population vs sample variance. |
| `np.percentile(x, [50, 95, 99])` | The latency reporting form. |
| `rng.lognormal(...)` | Generates realistic right-skewed latency. |
| `np.sqrt(p * (1 - p) / n)` | Standard error of a proportion. |
| Simulation loop over sample sizes | Shows empirically how often noise produces a 4-point gap. |

### 7.2 Expected output

`[EXECUTED]` 2026-09-08 with numpy 2.5.3, Python 3.12.3. Seeded, so the figures reproduce:

```
==========================================================================
MEAN, VARIANCE, STANDARD DEVIATION AND DISTRIBUTIONS
==========================================================================

--------------------------------------------------------------------------
1. THE HAND CALCULATION, VERIFIED
--------------------------------------------------------------------------
  data = [2, 4, 4, 4, 5, 5, 7, 9]
  mean = 40 / 8 = 5.0

     x    x - mean    (x - mean)^2
     2        -3.0             9.0
     4        -1.0             1.0
     4        -1.0             1.0
     4        -1.0             1.0
     5         0.0             0.0
     5         0.0             0.0
     7         2.0             4.0
     9         4.0            16.0
               sum            32.0

  population variance = 32.0 / 8 = 4.0
  population std dev  = sqrt(4.0) = 2.0

  numpy np.var(data)          = 4.0
  numpy np.std(data)          = 2.0
  numpy np.var(data, ddof=1)  = 4.5714  <- sample form

  The two variances differ by 14.3% at n=8.
  NumPy defaults to ddof=0 (population); pandas defaults to ddof=1
  (sample). They will disagree on identical data.

--------------------------------------------------------------------------
2. MEAN IS FRAGILE, MEDIAN IS ROBUST
--------------------------------------------------------------------------
  data                            mean    median
  [1, 2, 3, 4, 5]                  3.0       3.0
  [1, 2, 3, 4, 500]              102.0       3.0

  One value changed. The mean moved 34x.
  The median did not move at all.

--------------------------------------------------------------------------
3. A REALISTIC LATENCY DISTRIBUTION
--------------------------------------------------------------------------
  5,000 simulated request latencies (ms)

    mean          786
    median        600
    std dev       684
    p50           600
    p90          1535
    p95          2023
    p99          3572
    max          8027

  mean / median = 1.31  -> RIGHT SKEWED
  requests FASTER than the mean: 64.7%
    For symmetric data this would be 50%. Here the mean sits above
    most of the data, so it describes almost nobody.

  Distribution (each # is ~2% of requests):
         <250 ######                                             12.4%
      250-500 ##############                                     28.0%
      500-750 ##########                                         21.7%  <- MEDIAN
       750-1k #######                                            14.3%  <- MEAN
      1k-1.5k ######                                             13.0%
      1.5k-2k ##                                                  5.3%
        2k-3k #                                                   3.6%  <- p95
        3k-5k                                                     1.3%
       5k-10k                                                     0.3%
         >10k                                                     0.0%

  The mean sits to the RIGHT of the bulk of the data. A status
  report saying 'average latency 786ms' describes a user who
  does not exist: 65% of requests are faster than that, and
  the ones that are slower are MUCH slower (p99 = 3572ms).

--------------------------------------------------------------------------
4. IS A DIFFERENCE REAL? THE STANDARD ERROR
--------------------------------------------------------------------------
  SE of a proportion = sqrt(p(1-p)/n)

         n     p=0.82 SE         ~95% interval   resolvable gap
        50         5.43%         71.1% - 92.9%            15.3%
       100         3.84%         74.3% - 89.7%            10.8%
       200         2.72%         76.6% - 87.4%             7.7%
       500         1.72%         78.6% - 85.4%             4.8%
      1000         1.21%         79.6% - 84.4%             3.4%
      2000         0.86%         80.3% - 83.7%             2.4%
      5000         0.54%         80.9% - 83.1%             1.5%

  Last column: roughly the smallest difference between two prompts
  you could distinguish at that sample size.

  Note SE shrinks with sqrt(n): going from 500 to 2000 examples
  (4x the data) halves it. There is no cheap way around this.

--------------------------------------------------------------------------
5. HOW OFTEN DOES NOISE ALONE PRODUCE A 'WIN'?
--------------------------------------------------------------------------
  Two prompts, BOTH genuinely 80% accurate.
  Simulating 20,000 head-to-head evaluations at each size.

    n per prompt   |diff| > 3pp   |diff| > 5pp   mean |diff|
              50         70.8%          53.2%         6.37pp
             100         61.1%          36.8%         4.47pp
             200         45.3%          20.1%         3.17pp
             500         22.9%           4.4%         2.01pp
            1000          9.1%           0.4%         1.42pp
            2000          2.0%           0.0%         1.01pp

  Read the n=100 row. Two IDENTICAL prompts differ by more than
  3 percentage points most of the time, and by more than 5 points
  often. Every one of those would look like an improvement.

  Combine this with the M1-L05 optimistic-bias result - where
  picking the best of N candidates inflates the winner's score -
  and a small evaluation set is dangerous in two ways at once:
  it manufactures differences, and then you select on them.

==========================================================================
```

### 7.3 Reading the result

**Section 1 confirms the hand calculation** — sum of squared deviations 32, variance 4.0, standard
deviation 2.0 — and quantifies the `ddof` discrepancy: **14.3% at n=8**. On a small evaluation set,
NumPy and pandas will report noticeably different variances for identical data, and neither is wrong.
Specify `ddof` explicitly.

**Section 3's histogram makes skew visible.** The mean sits in the `750–1k` bucket while the median
sits in `500–750`, and **64.7% of requests are faster than the mean**. For symmetric data that figure
would be 50%. The mean is being dragged rightward by the small number of very slow requests, so it
describes a user who does not exist.

Compare the summary numbers:

```
median  600 ms      p95  2,023 ms      p99  3,572 ms      max  8,027 ms
```

The p99 is **six times** the median. A dashboard showing "average 786 ms" would look healthy while
one request in a hundred takes over three and a half seconds.

**Section 4 tells you what your evaluation set can actually resolve:**

| n | SE at p=0.82 | Smallest resolvable difference |
|---|---|---|
| 50 | 5.43% | ~15 points |
| 100 | 3.84% | ~11 points |
| 200 | 2.72% | ~7.7 points |
| 1,000 | 1.21% | ~3.4 points |
| 5,000 | 0.54% | ~1.5 points |

**With 100 examples you cannot detect anything smaller than about an 11-point difference.** Most
prompt improvements are 2–5 points. So the common practice of iterating against a 50-question eval
set cannot, even in principle, measure what it is trying to measure.

**Section 5 is the most important table in this lesson**, because it simulates the situation directly.
Two prompts, **both genuinely 80% accurate** — there is no real difference to find:

| n per prompt | Differ by > 3pp | Differ by > 5pp |
|---|---|---|
| **50** | **70.8%** | **53.2%** |
| **100** | **61.1%** | **36.8%** |
| 200 | 45.3% | 20.1% |
| 500 | 22.9% | 4.4% |
| 1,000 | 9.1% | 0.4% |

At n=100, two **identical** prompts appear to differ by more than 3 points **61% of the time**, and by
more than 5 points **37% of the time**. Every one of those would be reported as an improvement.
Someone would write it in a changelog.

Now combine this with M1-L05: if you try twenty prompt variants and keep the best, you are
*selecting* on exactly this noise — first manufacturing a difference, then choosing the largest one.
The two effects compound.

**The practical rule:** before believing a difference, compute what your sample size can resolve. If
the difference is smaller than that, you have not measured anything, however carefully you ran the
experiment.

**Verification:** confirm variance 4.0 / std 2.0 in section 1, `mean / median = 1.31` in section 3,
and that the n=100 row of section 5 shows roughly 61% and 37%.

---

## 8. Common mistakes and troubleshooting

1. **Reporting a mean with no measure of spread.**
2. **Using the mean for skewed data.** Latency, document length, cost per request.
3. **Reporting average latency instead of percentiles.**
4. **Treating a small difference as an improvement** without checking the standard error.
5. **Mixing `ddof=0` and `ddof=1`** between tools and comparing the results.
6. **Computing p99 from 50 samples.** It is the maximum, not a percentile.
7. **Applying the 68–95–99.7 rule to non-normal data.**
8. **Averaging percentiles across servers.** The mean of two p95s is not the overall p95.

| Symptom | Cause | Fix |
|---|---|---|
| Mean far above median | Right skew | Report median and percentiles |
| Metrics differ between NumPy and pandas | `ddof` default differs | Specify it explicitly |
| "Improvement" vanishes next week | It was noise | Compute the standard error; enlarge the sample |
| p99 jumps wildly between runs | Too few samples | Need ≫100 points for a stable p99 |
| Average latency looks fine, users complain | The tail is what they experience | Report and alert on p95/p99 |

---

## 9. Security, privacy, reliability and cost

- **Reliability.** Service level objectives are stated in percentiles precisely because averages hide
  the failures users notice. "p95 < 2 s" is actionable; "average < 2 s" is satisfiable while a
  quarter of requests time out.
- **Cost.** Cost per request is right-skewed — a few long prompts dominate. Budget on the mean
  (because you pay the total) but investigate the tail (because that is where waste hides). Both
  numbers, for different purposes.
- **Privacy.** Aggregate statistics can leak information about individuals when groups are small. A
  mean over three users can identify one. Set minimum group sizes before publishing breakdowns
  (M10-L06, M10-L08).
- **Governance.** Any reported metric must carry its sample size and spread. A number without `n` is
  not evidence, and M10-L12 makes this a release-gate requirement.

---

## 10. Exercises

### Exercise 1 — Beginner (~20 min)

By hand for `[3, 7, 7, 2, 9, 4, 7, 1]`:

1. Mean, median, mode.
2. Each value's deviation from the mean, and the squared deviations.
3. Population variance and standard deviation.
4. Sample variance (`n − 1`) and how much it differs.
5. Now append `100`. Recompute mean and median. Which changed more, and why?

### Exercise 2 — Intermediate (~30 min)

Using the lab's latency data:

1. Report mean, median, p50, p90, p95, p99 and max.
2. State whether the distribution is skewed and give the evidence.
3. Explain what "average latency" would tell a stakeholder and why it is misleading here.
4. Compute the proportion of requests slower than the mean. (For right-skewed data this is well under
   half — explain why.)
5. Write the one-sentence latency claim you would put in a status report.

### Exercise 3 — Challenge (~30 min)

1. Two prompts score 78% and 83% on 150 examples each. Compute both standard errors and the standard
   error of the difference. State whether the difference is distinguishable, showing your working.
2. How many examples per prompt would be needed to resolve a 5-point difference at roughly 2 SE?
   Show the algebra.
3. Simulate it: generate 10,000 pairs of evaluations where **both prompts are genuinely equal** at
   80%, using n = 50, 200 and 1,000. Report how often the observed difference exceeds 5 points in
   each case.
4. Explain how this result combines with the M1-L05 optimistic-bias finding to make small evaluation
   sets doubly dangerous.
5. Take a set of latencies and compute p95 from 20, 100 and 5,000 samples of the same distribution.
   Report the variability of the estimate and state a minimum sample size you would require.

---

## 11. Quiz

**Q1.** `[1, 2, 3, 4, 500]`. What are the mean and median?

- A. mean 3, median 3  B. mean 102, median 3  C. mean 102, median 102  D. mean 3, median 500

**Q2.** Why is variance squared rather than using absolute deviations?

- A. It is easier to compute.
- B. Squaring makes deviations positive so they do not cancel, and weights large deviations more —
  at the cost of squared units, which is why you take the square root.
- C. Absolute values are undefined.
- D. It makes the result smaller.

**Q3.** `mean 850, median 620` for a set of latencies. What does this tell you?

- A. The data is symmetric.
- B. It is right-skewed — a few large values pull the mean above the median.
- C. There is an error in the calculation.
- D. The standard deviation is zero.

**Q4.** Why is latency reported as p95 rather than as a mean?

- A. p95 is easier to compute.
- B. Latency is right-skewed, so the mean describes almost nobody; percentiles describe what users
  actually experience, including the slow tail.
- C. Means cannot be computed for time values.
- D. It is a legal requirement.

**Q5.** Two prompts score 82% and 85% on 100 examples. The standard error is about 3.8 points. What
do you conclude?

- A. The second prompt is better; ship it.
- B. The 3-point difference is well within the noise, so the two are indistinguishable at this
  sample size.
- C. The first prompt is better.
- D. You need a different metric.

**Q6.** To halve a standard error, how much more data do you need?

- A. Twice as much  B. Four times as much  C. Ten times as much  D. The same amount

**Q7.** `np.var(x)` and pandas' `.var()` on the same data give different answers. Why?

- A. One is buggy.
- B. NumPy defaults to the population form (`ddof=0`) and pandas to the sample form (`ddof=1`).
- C. Different floating-point precision.
- D. pandas sorts the data first.

**Q8.** What is wrong with computing p99 from 50 measurements?

- A. Nothing.
- B. With 50 points, p99 is effectively the maximum — a single value, highly unstable between runs
  rather than a meaningful percentile.
- C. p99 requires exactly 100 points.
- D. Percentiles cannot be estimated from samples.

**Q9.** Which pair should always be reported together?

- A. Mean and mode.
- B. A measure of centre and a measure of spread, plus the sample size.
- C. Median and maximum only.
- D. Variance alone.

**Q10.** *(Written, rubric-graded.)* In under 80 words, explain to a product manager why "our new
prompt improved accuracy from 82% to 85%" may not be an improvement at all.

---

## 12. Revision notes

- **Centre:** mean (sensitive to outliers) · **median (robust)** · mode (categorical).
- **Spread:** variance `σ² = Σ(xᵢ − x̄)²/n` · **standard deviation σ = √variance**, in original units ·
  range · IQR.
- **Never report a centre without a spread and a sample size.**
- `ddof=0` (population) vs `ddof=1` (sample). **NumPy defaults to 0, pandas to 1.**
- Normal: μ±1σ ≈ 68%, ±2σ ≈ 95%, ±3σ ≈ 99.7%. **Most real data is not normal.**
- **`mean > median` ⇒ right skew.** Latency, document length and cost are all right-skewed.
- **Report latency as p50 / p95 / p99, never as a mean.** p99 at 1,000 rpm is 10 unhappy users a
  minute.
- **Standard error of a proportion:** `√(p(1−p)/n)`. A difference under ~2 SE is not distinguishable.
- **SE shrinks with √n — four times the data to halve it.**
- Percentiles from small samples are unstable; p99 of 50 points is the maximum.
- **Never average percentiles across servers.**

---

## 13. Completion checklist

- [ ] I computed mean, variance and standard deviation by hand.
- [ ] I saw the mean move and the median stay put under an outlier.
- [ ] I can identify right skew from `mean > median`.
- [ ] I can compute the standard error of a proportion.
- [ ] I checked whether a 3-point difference is distinguishable at n=100.
- [ ] I know why p95 is reported rather than an average.
- [ ] I know the `ddof` default difference.
- [ ] I scored 7/10 on the quiz.

---

## 14. References

- NumPy statistics routines.
  <https://numpy.org/doc/stable/reference/routines.statistics.html> `[UNVERIFIED]`
- Google SRE Book, "Service Level Objectives" — on percentiles rather than averages.
  <https://sre.google/sre-book/service-level-objectives/> `[UNVERIFIED]`

---

## 15. Next lesson

→ [M3-L04 — Probability and Conditional Probability](M3-L04-probability.md)

You can describe a set of numbers. Next: reasoning about uncertainty — the foundation for the Naive
Bayes you already used in M1-L02, and for understanding what a model's output probabilities mean.
