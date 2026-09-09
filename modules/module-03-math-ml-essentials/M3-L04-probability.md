# M3-L04 — Probability and Conditional Probability

| | |
|---|---|
| **Lesson ID** | M3-L04 |
| **Difficulty** | 2 (Core) |
| **Estimated study time** | 2.0 hours |
| **Prerequisites** | [M3-L03](M3-L03-statistics.md) |

---

## 1. Learning objectives

1. **Compute** basic, joint and conditional probabilities from counts.
2. **Apply** Bayes' theorem and **explain** each of its four terms.
3. **Explain** why a highly accurate test can still be usually wrong, using base rates.
4. **State** what independence means and why Naive Bayes assumes it.
5. **Interpret** a model's output probability, and **state** what it does and does not mean.

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **Probability** | A number from 0 to 1 expressing how likely an event is. |
| **Event** | An outcome or set of outcomes. |
| **`P(A)`** | The probability of event A. |
| **Joint probability `P(A and B)`** | Both happen. |
| **Conditional probability `P(A\|B)`** | The probability of A **given that** B happened. |
| **Independent** | Knowing B tells you nothing about A: `P(A\|B) = P(A)`. |
| **Mutually exclusive** | Cannot both happen. |
| **Base rate / prior** | How common something is before you look at any evidence. |
| **Likelihood** | `P(evidence \| hypothesis)` — how expected the evidence is if the hypothesis holds. |
| **Posterior** | `P(hypothesis \| evidence)` — the updated belief after seeing evidence. |
| **Bayes' theorem** | The rule for computing the posterior from the prior and likelihood. |
| **Base-rate fallacy** | Ignoring how rare something is when interpreting a test result. |
| **Naive Bayes** | A classifier assuming all features are conditionally independent. |
| **Calibration** | Whether stated probabilities match observed frequencies (M1-L10). |

---

## 3. Plain-language explanation

Probability is counting, then dividing.

```
100 support tickets. 30 are about billing.
P(billing) = 30 / 100 = 0.3
```

**Conditional probability** narrows the pool before counting:

```
Of the 100 tickets, 40 arrived by email. Of those 40, 18 are about billing.
P(billing | email) = 18 / 40 = 0.45
```

Read `P(A|B)` as "the probability of A **given** B". The vertical bar means "given". You have
restricted attention to the cases where B is true, and asked how often A is true among those.

**The single most important idea in this lesson:** `P(A|B)` and `P(B|A)` are different numbers, and
confusing them causes serious, common errors.

- `P(spam | contains "free")` — of messages containing "free", how many are spam?
- `P(contains "free" | spam)` — of spam messages, how many contain "free"?

These can differ enormously. Almost all spam might contain "free" (`P(free|spam) = 0.9`) while most
messages containing "free" are legitimate, simply because legitimate mail is far more common.

**Bayes' theorem is the rule for converting between them**, and §5.3 shows why that conversion is
where intuition fails.

---

## 4. Analogy

**A jar of marbles.** Probability is "how many of this colour, divided by the total". Conditional
probability is "first take out only the large marbles, then ask what fraction are red".

### Where the analogy breaks

1. **Marbles are countable and fixed. Real probabilities are usually estimated from a sample**, so
   they carry the uncertainty of M3-L03 §5.5.
2. **Drawing marbles is genuinely random. Most events you model are not** — they are deterministic
   processes you cannot observe fully. Probability here expresses *your uncertainty*, not the world's
   randomness.
3. **Marble colours are independent of one another. Features usually are not**, which is exactly the
   assumption Naive Bayes makes and violates (§5.5).
4. **The jar's contents do not change as you look.** Base rates drift — spam patterns, fraud rates and
   user behaviour all shift, so a probability estimated last year may be wrong now (M1-L06
   distribution shift).

---

## 5. Detailed technical explanation

### 5.1 The rules

| Rule | Formula | Meaning |
|---|---|---|
| Range | `0 ≤ P(A) ≤ 1` | 0 impossible, 1 certain |
| Complement | `P(not A) = 1 − P(A)` | — |
| Joint (independent) | `P(A and B) = P(A) × P(B)` | **Only if independent** |
| Joint (general) | `P(A and B) = P(A\|B) × P(B)` | Always true |
| Conditional | `P(A\|B) = P(A and B) / P(B)` | Requires `P(B) > 0` |
| Union | `P(A or B) = P(A) + P(B) − P(A and B)` | Subtract the overlap |

**The multiplication rule for independent events explains the M1-L11 compound-error result.** Five
steps each succeeding with probability 0.95, independently, gives `0.95⁵ = 0.774`. It is the same
arithmetic.

### 5.2 Reading a contingency table

Everything conditional comes from a table of counts.

```
                 billing   not billing   TOTAL
email               18          22         40
chat                 9          21         30
phone                3          27         30
TOTAL               30          70        100
```

| Quantity | Calculation | Result |
|---|---|---|
| `P(billing)` | 30 / 100 | 0.30 |
| `P(email)` | 40 / 100 | 0.40 |
| `P(billing and email)` | 18 / 100 | 0.18 |
| `P(billing \| email)` | 18 / 40 | **0.45** |
| `P(email \| billing)` | 18 / 30 | **0.60** |

**Notice that `P(billing|email) = 0.45` and `P(email|billing) = 0.60` are different numbers from the
same cell.** The numerator is identical (18); only the denominator changes — which pool you
restricted to. That is the whole distinction, and seeing it as a division choice makes it much harder
to confuse.

**Are channel and topic independent?** If they were, `P(billing|email)` would equal `P(billing)`.
It is 0.45 versus 0.30, so **no** — email is more likely to be about billing. That is useful signal:
channel predicts topic.

### 5.3 Bayes' theorem

$$P(A|B) = \frac{P(B|A) \times P(A)}{P(B)}$$

Every term named:

| Term | Name | Meaning |
|---|---|---|
| `P(A\|B)` | **Posterior** | What you want: belief in A after seeing B |
| `P(B\|A)` | **Likelihood** | How expected B is when A is true |
| `P(A)` | **Prior** / base rate | How common A is before any evidence |
| `P(B)` | **Evidence** | How common B is overall |

`P(B)` is usually expanded as `P(B|A)P(A) + P(B|not A)P(not A)` — the two ways B can occur.

### 5.4 The base-rate fallacy, worked

**This is the most consequential calculation in the lesson.**

A fraud detector is **99% accurate**: it flags 99% of fraud, and correctly clears 99% of legitimate
transactions. Fraud occurs in **0.1%** of transactions.

**A transaction is flagged. What is the probability it is actually fraud?**

Most people answer "99%". The correct answer is about **9%**.

Work it with 100,000 transactions:

| | Fraud (100) | Legitimate (99,900) | Total |
|---|---|---|---|
| **Flagged** | 99 | 999 | 1,098 |
| Not flagged | 1 | 98,901 | 98,902 |

- Fraud: 0.1% of 100,000 = **100**. The detector catches 99% → **99 flagged**.
- Legitimate: **99,900**. The detector wrongly flags 1% → **999 flagged**.

So of **1,098** flagged transactions, only **99** are fraud:

$$P(\text{fraud} \mid \text{flagged}) = \frac{99}{1098} \approx 0.090$$

**About 9%.** Ten times more false alarms than real fraud.

Via Bayes directly:

- Prior `P(fraud) = 0.001`
- Likelihood `P(flag|fraud) = 0.99`
- `P(flag) = 0.99 × 0.001 + 0.01 × 0.999 = 0.00099 + 0.00999 = 0.01098`
- Posterior `= (0.99 × 0.001) / 0.01098 = 0.00099 / 0.01098 ≈ **0.090**`

**Why this matters to you.** It is not a puzzle — it is the central design constraint of any detector
for a rare event:

- Content moderation, security alerting, medical screening, fraud, anomaly detection.
- **When the base rate is low, even an excellent classifier produces mostly false positives.**
- Reporting "99% accurate" is technically true and completely misleading. The number that matters is
  **precision** — of the things you flagged, how many were real (M3-L14).
- It is why human review queues exist, and why alert fatigue is a predictable engineering outcome
  rather than a failure of diligence.

### 5.5 Independence and Naive Bayes

Two events are **independent** if `P(A|B) = P(A)`.

In M1-L02 you built a Naive Bayes classifier that multiplied per-word probabilities:

```
P(spam | "free money now") ∝ P(spam) × P(free|spam) × P(money|spam) × P(now|spam)
```

That multiplication is only valid if the words are **conditionally independent given the class** —
knowing a message contains "free" tells you nothing about whether it contains "money".

**That is obviously false.** "Free" and "money" co-occur constantly. Hence "naive".

**So why does it work?** Because the *ranking* is often right even when the *probabilities* are
wrong. Correlated features are double-counted, pushing the winning class's score to an extreme — you
get badly overconfident probabilities but frequently the correct class.

**The practical consequence:** trust a Naive Bayes *classification*, distrust its *probability*. Its
outputs are notoriously poorly calibrated (M1-L10), often near 0 or 1. If you plan to threshold on
that probability, measure the calibration first.

### 5.6 What a model's probability actually means

When a classifier outputs `0.87`, that is a number the model produced. Whether it means "87% of such
cases are positive" is an **empirical question about calibration**, not a definition.

| Model type | Typical calibration |
|---|---|
| Logistic regression | Usually reasonable |
| Naive Bayes | Poor — overconfident |
| Deep neural networks | Often overconfident |
| LLM verbal confidence | Not a probability at all (M1-L10) |

**The check is the M1-L10 reliability diagram**: bucket predictions by stated confidence and measure
the actual accuracy in each bucket. Until you have done that, a probability is a score to be ranked
on, not a quantity to be reasoned with.

### 5.7 Assumptions and limitations

- Probabilities estimated from small samples are uncertain (M3-L03 §5.5).
- Base rates drift; a prior from last year may be wrong now.
- Independence assumptions are usually violated; the question is whether it matters for your purpose.
- Bayes' theorem is exact arithmetic — errors come from wrong inputs, especially a guessed prior.

---

## 6. Worked example — should this alert page someone?

You are asked to page an on-call engineer when a model flags a possible security incident.

**Given:**

- Real incidents: **2 per 10,000 sessions** → prior `P(incident) = 0.0002`
- Detector catches 95% of real incidents → `P(flag|incident) = 0.95`
- Detector wrongly flags 2% of normal sessions → `P(flag|normal) = 0.02`
- Volume: **50,000 sessions per day**

**Step 1 — expected daily counts.**

- Real incidents: 50,000 × 0.0002 = **10**
- Caught: 10 × 0.95 = **9.5**
- Normal sessions: 49,990. Wrongly flagged: 49,990 × 0.02 = **999.8**

**Step 2 — the posterior.**

$$P(\text{incident} \mid \text{flag}) = \frac{9.5}{9.5 + 999.8} = \frac{9.5}{1009.3} \approx 0.0094$$

**About 0.94%.** Roughly **one in 106** pages is a real incident.

**Step 3 — what that means operationally.** 1,009 pages per day. An engineer paged a thousand times a
day will, correctly and inevitably, stop reading them. **The system's real output is not detection —
it is alert fatigue**, and the genuine incidents will be missed *because* of the alerts, not despite
them.

**Step 4 — the options, and their arithmetic.**

| Option | Effect | New precision |
|---|---|---|
| Reduce false positives to 0.1% | 50 false + 9.5 true | 9.5/59.5 ≈ **16%** |
| Reduce to 0.01% | 5 false + 9.5 true | 9.5/14.5 ≈ **66%** |
| Require two independent signals | Multiplies the false-positive rates | Large improvement |
| Raise the threshold | Fewer flags, catches fewer real ones | A trade-off, not a fix |
| Do not page; use a review queue | Same volume, no interrupts | Precision unchanged, harm reduced |

**Step 5 — the recommendation.** Do not page on this signal. Route it to a queue reviewed during
working hours, and page only on a much rarer, higher-precision combination. Then measure the actual
precision in production, because the 2% false-positive rate is itself an estimate.

**Step 6 — the general lesson.** Before building any detector for a rare event, do this arithmetic
**first**. It takes five minutes and frequently shows that the proposed design cannot work at any
achievable accuracy — which is far cheaper to learn now than after deployment. This is the M1-L11
reliability argument, with the numbers filled in.

---

## 7. Practical activity

**File:** [`labs/m3/l04_probability.py`](../../labs/m3/l04_probability.py)

**Requires the venv:**

```bash
source .venv/bin/activate
python labs/m3/l04_probability.py
```

Builds the contingency table and computes every conditional from it, works Bayes' theorem both by
counting and by formula, sweeps base rates to show precision collapsing, simulates the fraud detector
on 100,000 transactions, and demonstrates Naive Bayes ranking correctly while being badly
miscalibrated.

### 7.1 Important lines

| Construct | Why |
|---|---|
| `table[row].sum()` / `table[:, col].sum()` | Marginal totals — the denominators of every conditional. |
| `posterior = (likelihood * prior) / evidence` | Bayes, written directly. |
| `rng.random(n) < rate` | Simulating events at a given probability. |
| Base-rate sweep | Shows precision collapsing as the event gets rarer. |
| Calibration buckets | The M1-L10 reliability check applied to Naive Bayes. |

### 7.2 Expected output

`[EXECUTED]` 2026-09-08 with numpy 2.5.3, Python 3.12.3. Seeded, so figures reproduce:

```
==========================================================================
PROBABILITY AND CONDITIONAL PROBABILITY
==========================================================================

--------------------------------------------------------------------------
1. EVERY CONDITIONAL COMES FROM A TABLE OF COUNTS
--------------------------------------------------------------------------
             billing   not billing   TOTAL
     email        18            22      40
      chat         9            21      30
     phone         3            27      30
     TOTAL        30            70     100

  P(billing)            = 30/100 = 0.30
  P(email)              = 40/100 = 0.40
  P(billing and email)  = 18/100 = 0.18
  P(billing | email)    = 18/40 = 0.45   <- restricted to EMAIL
  P(email | billing)    = 18/30 = 0.60   <- restricted to BILLING

  Same numerator (18). Different denominator. That is the whole
  difference between P(A|B) and P(B|A).

  Independence check:
    P(billing)         = 0.30
    P(billing | email) = 0.45
    They differ, so channel and topic are NOT independent -
    knowing the channel changes what you expect the topic to be.

   channel    P(billing | channel)
     email                    0.45
      chat                    0.30
     phone                    0.10
    Email is far more likely to be billing than phone is.

--------------------------------------------------------------------------
2. THE BASE-RATE FALLACY, BY COUNTING
--------------------------------------------------------------------------
  100,000 transactions, fraud rate 0.1%
  Detector: catches 99% of fraud, clears 99% of legitimate

                     fraud    legitimate     TOTAL
         flagged        99           999      1098
     not flagged         1         98901     98902
           TOTAL       100         99900    100000

  P(fraud | flagged) = 99 / 1098 = 0.090

  A '99% accurate' detector is right about 9.0% of the time
  when it fires. There are 10x more false alarms
  than real fraud.

  Via Bayes directly:
    prior      P(fraud)          = 0.001
    likelihood P(flag | fraud)   = 0.99
    evidence   P(flag)           = 0.99 x 0.001 + 0.01 x 0.999 = 0.01098
    posterior  P(fraud | flag)   = 0.99 x 0.001 / 0.01098 = 0.0902
    matches the counting result (0.090)

--------------------------------------------------------------------------
3. PRECISION COLLAPSES AS THE EVENT GETS RARER
--------------------------------------------------------------------------
  Holding sensitivity at 95% and the false-positive
  rate at 1%, varying only how common the event is:

     base rate   precision      false alarms per true positive
      50.0000%       0.990    #######################################    0.01x
      20.0000%       0.960    ######################################     0.04x
       5.0000%       0.833    #################################          0.20x
       1.0000%       0.490    ###################                        1.04x
       0.5000%       0.323    ############                               2.09x
       0.1000%       0.087    ###                                          11x
       0.0500%       0.045    #                                            21x
       0.0100%       0.009                                                105x

  Nothing about the detector changed across those rows. Only the
  world did. This is why 'accuracy' is the wrong metric for rare
  events and precision is the right one (M3-L14).

  Precision falls below 50% once the base rate drops below 1.0417%.

--------------------------------------------------------------------------
4. THE SECTION 6 ALERT DECISION
--------------------------------------------------------------------------
  50,000 sessions/day, incident rate 0.02%
    real incidents        :       10.0
    caught (95%)         :        9.5
    false alarms (2%)     :      999.8
    total pages           :     1009.3
    P(incident | page)    :     0.0094  (0.94%)
    -> 1 real incident per 106 pages

  An engineer paged ~1,000 times a day will stop reading them.
  The system's real output is alert fatigue, and real incidents
  get missed BECAUSE of the alerts, not despite them.

  What would fix it:
     false-positive rate   pages/day   precision
                  2.00%        1009        0.9%
                  0.50%         259        3.7%
                  0.10%          59       16.0%
                  0.01%          14       65.5%

  Only at a 0.01% false-positive rate does paging become
  defensible - a 200x improvement on the current detector.

--------------------------------------------------------------------------
5. NAIVE BAYES: GOOD RANKING, BAD PROBABILITIES
--------------------------------------------------------------------------
  4000 samples, two HIGHLY CORRELATED features.
    accuracy using both (naive, double-counts) : 0.839
    accuracy using one feature                 : 0.836
    Ranking quality is essentially unaffected.

  But look at the CALIBRATION of the naive probabilities:
     stated confidence       n   actual accuracy      gap
             0.50-0.60     634             0.514   -0.036
             0.60-0.70     596             0.584   -0.066
             0.70-0.80     480             0.823   +0.072
             0.80-0.90     583             0.995   +0.138
             0.90-0.99    1079             1.000   +0.046
             0.99-1.00     628             1.000   +0.003

  Expected Calibration Error: 0.057
  Predictions above 0.99 or below 0.01: 15.7%

  Multiplying two copies of the same evidence pushes the
  probability toward the extremes. The CLASS is usually right;
  the CONFIDENCE is not. Rank with Naive Bayes. Do not threshold
  on its probability without calibrating first (M1-L10).

==========================================================================
```

### 7.3 Reading the result

**Section 1 makes the `P(A|B)` vs `P(B|A)` distinction concrete.** Both use the same cell (18). Only
the denominator differs: 40 email tickets, or 30 billing tickets. `0.45` versus `0.60`. Seeing it as
*a choice of denominator* rather than as two mysterious formulas is what makes it stick.

The per-channel table underneath is the useful part in practice: `P(billing | email) = 0.45` against
`P(billing | phone) = 0.10`. Channel genuinely predicts topic, which is why it is a feature worth
having.

**Section 2 confirms the calculation both ways** — counting gives 99/1098 = 0.090, Bayes gives
0.0902. A "99% accurate" detector is right **9% of the time** when it fires, with **10× more false
alarms than real fraud**.

**Section 3 is the table to keep.** Nothing about the detector changes across those rows — only how
common the event is:

| Base rate | Precision | False alarms per true positive |
|---|---|---|
| 50% | 0.990 | 0.01× |
| 5% | 0.833 | 0.20× |
| **1%** | **0.490** | **1×** |
| 0.1% | 0.087 | 11× |
| 0.01% | 0.009 | **105×** |

And the algebraic answer: **precision falls below 50% once the base rate drops below 1.04%.** That
single number is worth memorising — for a detector with 95% sensitivity and a 1% false-positive rate,
anything rarer than roughly one in a hundred produces mostly false alarms.

**Section 4 turns that into an operational decision:**

```
50,000 sessions/day  ->  9.5 real incidents caught, 999.8 false alarms
P(incident | page) = 0.94%   ->  1 real incident per 106 pages
```

And the fix table shows what would be required:

| False-positive rate | Pages/day | Precision |
|---|---|---|
| 2.00% (current) | 1,009 | 0.9% |
| 0.10% | 59 | 16.0% |
| **0.01%** | **14** | **65.5%** |

Paging only becomes defensible at a **0.01%** false-positive rate — a 200-fold improvement on the
current detector. That is not a tuning exercise; it is a different system. Knowing this before
building it is the entire point of doing the arithmetic first.

**Section 5 demonstrates the Naive Bayes trade-off with two deliberately correlated features:**

- Accuracy using both features (double-counting): **0.839**
- Accuracy using one feature: **0.836**

**The ranking barely changed** — the second feature added almost nothing, because it was a copy. But
look at the calibration:

```
stated 0.80-0.90  ->  actual accuracy 0.995   gap +0.138
predictions above 0.99 or below 0.01: 15.7%
```

Multiplying two copies of the same evidence drove **15.7% of predictions to near-certainty**, and the
0.80–0.90 bucket is actually right 99.5% of the time — badly *under*-confident there, having been
pushed around by the double-counting. The class is usually right; the probability is not trustworthy.

**The rule this gives you:** rank with Naive Bayes, do not threshold on its probability. And more
generally — a model's output probability is a claim to be checked against observed frequencies
(M1-L10), never a definition.

**Verification:** confirm `99 / 1098 = 0.090`, that precision crosses 50% at a base rate of ~1.04%,
that the alert precision is 0.94%, and that Naive Bayes shows a large positive calibration gap in the
0.80–0.90 bucket.

---

## 8. Common mistakes and troubleshooting

1. **Confusing `P(A|B)` with `P(B|A)`.** The most common and most costly error.
2. **Ignoring the base rate.** "99% accurate" says nothing about precision on a rare event.
3. **Multiplying probabilities of dependent events.**
4. **Treating a model's output as a calibrated probability** without checking.
5. **Reporting accuracy for a rare event.** Always report precision and recall (M3-L14).
6. **Assuming a prior is stable.** Base rates drift.
7. **Building a detector before doing the arithmetic.**

| Symptom | Cause | Fix |
|---|---|---|
| "99% accurate" but the alerts are useless | Base-rate fallacy | Compute precision from the prior |
| Naive Bayes probabilities are all ~0 or ~1 | Correlated features double-counted | Use it for ranking, not for probability |
| Threshold works in testing, floods in production | The production base rate differs | Estimate the prior from production data |
| Model probability of 0.9 is right 60% of the time | Miscalibrated | Reliability diagram; recalibrate (M1-L10) |
| `ZeroDivisionError` in a conditional | The condition never occurred | Check for a zero denominator; add smoothing |

---

## 9. Security, privacy, reliability and cost

- **Security.** Every intrusion detector faces this arithmetic. A rare-event detector with any
  meaningful false-positive rate generates overwhelmingly false alerts, and alert fatigue is the
  predictable result. Design the review workflow at the same time as the detector, not after.
- **Reliability.** Compound error (M1-L11) is the independence multiplication rule. Where steps are
  *correlated* — one bad input breaking several — real reliability is worse than the product suggests.
- **Cost.** A low-precision detector's cost is human review time, and it scales with false positives
  rather than with true ones. 1,000 alerts a day at five minutes each is an entire full-time role.
- **Governance.** State the base rate assumed when reporting any detector's performance. A precision
  figure without the prior it was measured at is not reproducible (M10-L12).

---

## 10. Exercises

### Exercise 1 — Beginner (~20 min)

From this table:

```
              resolved   unresolved   TOTAL
priority 1        40          10        50
priority 2        90          60       150
priority 3       200         100       300
TOTAL            330         170       500
```

Compute: `P(resolved)` · `P(priority 1)` · `P(resolved and priority 1)` ·
`P(resolved | priority 1)` · `P(priority 1 | resolved)` · and state whether priority and resolution
are independent, with your reasoning.

### Exercise 2 — Intermediate (~30 min)

A content classifier flags policy violations. It catches 92% of real violations and wrongly flags
3% of acceptable posts. Violations are 0.5% of posts. You process 200,000 posts a day.

1. Expected true positives and false positives per day.
2. `P(violation | flagged)`. Show the working both by counting and via Bayes.
3. How many moderator-hours per day at 30 seconds per review?
4. What false-positive rate would be needed for 50% precision? Show the algebra.
5. Write the three-sentence recommendation you would give the product owner.

### Exercise 3 — Challenge (~30 min)

1. Plot (or tabulate) `P(real | flagged)` as the base rate varies from 50% down to 0.01%, holding
   sensitivity at 95% and the false-positive rate at 1%. Describe the shape.
2. At what base rate does precision fall below 50%? Solve it algebraically and confirm numerically.
3. Simulate the M1-L02 spam classifier's output probabilities on 2,000 messages and build a
   reliability diagram. Report the Expected Calibration Error and state whether you would threshold
   on those probabilities.
4. Two detectors each with 1% false-positive rates are combined with AND. What is the combined rate
   if they are independent? What if they are perfectly correlated? Explain why the truth is usually
   between, and why assuming independence is dangerous.
5. Write `precision_from_base_rate(prior, sensitivity, fp_rate)` and use it to produce a table a
   product owner could read.

---

## 11. Quiz

**Q1.** `P(A|B)` means:

- A. The probability of A and B both occurring.
- B. The probability of A, given that B has occurred.
- C. The probability of B, given A.
- D. A divided by B.

**Q2.** From the §5.2 table, `P(billing | email) = 18/40 = 0.45` while `P(email | billing) = 18/30 =
0.60`. Why do they differ?

- A. One is calculated incorrectly.
- B. The numerator is the same cell, but the denominator differs — you are restricting to a different
  pool.
- C. Because the events are independent.
- D. Rounding.

**Q3.** A test is 99% accurate for a condition affecting 0.1% of people. Someone tests positive. The
probability they have it is about:

- A. 99%  B. 50%  C. 9%  D. 0.1%

**Q4.** Why is that number so low?

- A. The test is badly designed.
- B. The condition is so rare that the small percentage of false positives among the very large
  healthy population outnumbers the true positives.
- C. Bayes' theorem does not apply.
- D. 99% accuracy is not high enough to be useful for anything.

**Q5.** In Bayes' theorem, what is the **prior**?

- A. `P(B|A)`  B. `P(A|B)`  C. `P(A)` — the base rate before any evidence  D. `P(B)`

**Q6.** Why is Naive Bayes called "naive"?

- A. It is simple to implement.
- B. It assumes features are conditionally independent given the class, which is almost always false —
  "free" and "money" co-occur constantly.
- C. It was invented first.
- D. It only works on text.

**Q7.** Given that assumption is violated, why is Naive Bayes still useful?

- A. The violation does not matter mathematically.
- B. The class *ranking* is often correct even when the probabilities are badly wrong, because
  double-counting correlated features pushes the winner to an extreme without usually changing which
  class wins.
- C. It corrects itself with more data.
- D. It is not useful.

**Q8.** A model outputs `0.87`. What does that number mean?

- A. 87% of such cases are positive.
- B. Only that the model produced 0.87 — whether it corresponds to an 87% frequency is an empirical
  question about calibration that must be measured.
- C. The model is 87% accurate.
- D. There is an 87% chance the model is right about everything.

**Q9.** You are asked to build a detector for an event occurring in 0.02% of sessions. What should you
do **first**?

- A. Choose a model architecture.
- B. Compute the expected precision from the base rate and a realistic false-positive rate, and check
  whether the resulting alert volume is workable.
- C. Collect training data.
- D. Set a confidence threshold.

**Q10.** *(Written, rubric-graded.)* In under 80 words, explain to a stakeholder why a "99% accurate"
fraud detector will produce mostly false alarms.

---

## 12. Revision notes

- Probability = count / total. **Conditional = count / restricted total.**
- **`P(A|B) ≠ P(B|A)`.** Same numerator, different denominator. This confusion is the most costly
  error in the lesson.
- `P(A and B) = P(A|B)P(B)` always; `= P(A)P(B)` **only if independent**.
- **Bayes:** `P(A|B) = P(B|A)P(A) / P(B)`. Posterior = likelihood × prior / evidence.
- **Base-rate fallacy:** a 99%-accurate test for a 0.1% condition gives ~**9%** precision. With rare
  events, false positives from the huge negative population swamp the true positives.
- **Report precision, not accuracy, for rare events.**
- **Do the arithmetic before building the detector.** It often shows the design cannot work.
- **Naive Bayes** assumes conditional independence — false, but the *ranking* often survives while the
  *probabilities* do not. Rank with it; do not threshold on its probability without calibrating.
- A model's output probability is a **claim to be verified**, not a definition (M1-L10).
- Base rates drift; priors expire.

---

## 13. Completion checklist

- [ ] I can compute any conditional from a contingency table.
- [ ] I can state the four terms of Bayes' theorem.
- [ ] I worked the 99%-accurate / 0.1%-prevalence case and got ~9%.
- [ ] I did the §6 alert arithmetic and can explain the recommendation.
- [ ] I can explain why Naive Bayes ranks well but calibrates badly.
- [ ] I know to compute precision from the base rate before building a detector.
- [ ] I scored 7/10 on the quiz.

---

## 14. References

- Kahneman & Tversky's work on the base-rate fallacy, summarised in *Thinking, Fast and Slow*.
  `[UNVERIFIED]`
- Wikipedia, "Base rate fallacy" — includes the standard worked examples.
  <https://en.wikipedia.org/wiki/Base_rate_fallacy> `[UNVERIFIED]`

---

## 15. Next lesson

→ [M3-L05 — Logarithms, Cross-Entropy and Perplexity Intuition](M3-L05-logs-entropy.md)

You can now reason about probabilities. Next: why they are almost always handled as logarithms in
practice, and the loss function that every language model is trained to minimise.
