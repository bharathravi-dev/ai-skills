# M5-L18 — Building an Evaluation Dataset You Can Trust

| | |
|---|---|
| **Lesson ID** | M5-L18 |
| **Difficulty** | 3 (Advanced) |
| **Estimated study time** | 2.25 hours |
| **Prerequisites** | [M5-L12](M5-L12-prompt-versioning.md), [M3-L14](../module-03-math-ml-essentials/M3-L14-metrics.md) |

---

## 1. Learning objectives

1. **Distinguish** an evaluation dataset from M5-L12's regression suite, and explain why the same small
   set should not serve both purposes.
2. **Detect** prompt-tuning contamination — the LLM-specific leakage variant where iterating against your
   own eval set inflates its measured quality without improving true quality.
3. **Compute** the sample size a quality estimate needs to report a stated confidence, distinguishing
   this from M5-L12's different question of detecting a known gap.
4. **Explain** why random sampling misses rare-but-consequential cases, and build a stratified eval set
   that does not.
5. **State** what a property assertion and an LLM-as-judge score each cost in reliability, and when each
   is appropriate.

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **Evaluation dataset (eval set)** | A dataset built to measure true system quality, distinct in purpose from a regression suite. |
| **Prompt-tuning contamination** | Iterating a prompt against a fixed, visible set of examples until it passes, inflating that set's own reported quality. |
| **Holdout** | Data never used to inform any prompt or configuration decision, reserved for the final quality read. |
| **Ground truth / reference label** | The correct or acceptable answer an example is scored against. |
| **Inter-rater agreement** | The degree to which independent human labellers agree on a ground-truth label. |
| **Stratified sampling** | Deliberately including a stated number of examples from each case type, by design, not by chance. |
| **Confidence interval (quality estimate)** | The range a true quality figure plausibly falls in, given a measurement at a stated sample size. |
| **Synthetic eval data** | Eval examples generated (often by a model) rather than sourced from real traffic or written by hand. |
| **LLM-as-judge** | Using a model to score another model's output against a rubric, for output too open-ended for a property check. |

---

## 3. Plain-language explanation

### 3.1 A regression suite and an evaluation dataset are not the same tool

M5-L12 gave you a golden suite: small, deliberately iterated against, gating deploys on a fingerprint
change. That is the right tool for catching a **known kind of regression** cheaply. It is the **wrong**
tool for answering "how good is this system, really?" — because the same property that makes it useful
for regression testing (you look at it constantly, and change things until it passes) is exactly what
makes it untrustworthy as a measure of true quality. §7.1 makes this concrete.

### 3.2 Contamination without a training loop

M1-L09 taught data leakage as a family of failures in model training — information from the evaluation
data reaching the model in a way that inflates a reported score. Prompting has no gradient step, so it is
tempting to think it is immune. It is not. **Iterating a prompt against a small, fixed, visible set of
examples until every one passes is contamination in spirit**, even though no weight update ever occurs —
the set stops measuring quality and starts measuring "have I patched every failure I can see."

### 3.3 A single measurement is not a fact

Even an honest, uncontaminated eval run reports one number from a finite sample. That number has a
**confidence interval**, and at small sample sizes the interval can be wide enough to make the number
nearly meaningless as a basis for a decision. This is a different question from M5-L12's — that lesson
asked how many samples are needed to reliably *detect a known gap between two versions*; this lesson asks
how many are needed to *trust a single measurement of where you currently stand*.

### 3.4 Random sampling is not the same as representative sampling

A rare but consequential case type — the one that costs the most when your system gets it wrong — can be
entirely absent from a randomly built eval set, with real, computable probability. **Stratified
sampling** fixes this by design: you decide how many examples of each case type belong in the set, rather
than hoping chance provides them.

---

## 4. Analogy

**A restaurant that only ever tastes the dishes the head chef already suspects might be off.** Over weeks,
every dish the chef checks eventually tastes right — each one got tasted, adjusted, and tasted again until
it passed. A diner who orders something the chef never happened to check gets whatever came out of the
kitchen the first time, untouched by any of that careful attention. The chef's own notebook, full of
"tasted, fixed, passed" entries, says nothing reliable about the dishes never in it.

Occasionally the restaurant also under-samples: it tastes ordinary dishes constantly and, being small and
short-staffed, almost never happens to taste the one severe-allergy-substitution dish that comes up only a
few times a year — exactly the dish where a mistake matters most.

### Where the analogy breaks

- **A chef's palate has real, general skill that transfers across dishes.** A prompt patch aimed at one
  specific example transfers to genuinely similar cases only some of the time (§7.1's stated 20%) — most
  patches are narrower than they feel while you're making them.
- **A single taste is usually enough for a competent chef to judge a dish.** A single small eval run is
  not enough to judge a system's quality with any real precision (§7.2) — the uncertainty is mathematical,
  not a matter of skill.
- **A restaurant can deliberately schedule a taste of the rare dish.** An eval set can too, but only if
  someone decides to stratify for it — it will not happen by accident (§7.3).

---

## 5. Detailed technical explanation

### 5.1 The contamination gap, measured

`[REAL mechanism, illustrative parameters]` §7.1 simulated iterating a prompt against 15 visible examples,
patching one failure per round, with a stated 20% chance that any given patch is a real, generalising fix
rather than one narrow to the specific example:

| Round | Visible-set pass rate | True (held-out) pass rate |
|---|---|---|
| Start | 67% | 41% |
| 1 | 73% | 41% |
| 3 | 87% | 41% |
| 5 (final) | **100%** | **44%** |

**The visible set reaches a perfect score. True quality moves three points.** By the end, the visible set
overstates true quality by **56 points** — and every single patch along the way was a genuine, correct
fix for the example it targeted. **Nobody in this process did anything that looked wrong at any single
step.** The gap is a property of using the same small set to both guide changes and report quality, not a
failure of diligence.

### 5.2 Confidence, not just a percentage

`[REAL, exact formula]` §7.2 computed a 95% confidence interval (`p̂ ± 1.96·√(p̂(1−p̂)/N)`) for a measured
85% pass rate at several sample sizes:

| N | 95% CI | Width |
|---|---|---|
| 10 | [63%, 100%] | 37 points |
| 100 | [78%, 92%] | 14 points |
| 300 | [81%, 89%] | 8 points |
| 1,000 | [83%, 87%] | 4 points |

**At N=10, a measured 85% is consistent with a true quality anywhere from 63% to 100%** — not a number a
launch decision should be made from. This is a distinct question from M5-L12 §5.3's: that lesson sized a
sample to detect a *known, specific gap* between two conditions; this one sizes a sample to trust a
*single* measurement's precision. Both questions matter, and they are not the same arithmetic.

### 5.3 Coverage is not guaranteed by size alone

`[REAL, exact formula]` §7.3 computed the probability a randomly sampled eval set contains **zero**
examples of a case type making up 2% of real traffic:

| Eval set size | P(zero examples of the rare case) |
|---|---|
| 50 | 36.4% |
| 100 | **13.3%** |
| 200 | 1.8% |

**Solved exactly: a random sample needs at least 149 examples before there is even a 95% chance of
including a single instance of a 2%-share case type.** Most eval sets teams actually build (50–100
examples) sit well short of that. **The fix is not simply a bigger random sample — it is stratification**:
deciding, by design, that N examples of this case type belong in the set, rather than leaving it to
chance (M3-L13).

### 5.4 Two assertion tools, and their limits

M5-L12 established exact-match and property assertions. Neither handles genuinely open-ended output well
— a property check needs a checkable property, and free-form quality often has none. **LLM-as-judge**
fills that gap by using a model to score output against a rubric, at the cost of introducing a new,
separate reliability question: how well does the judge agree with what a human rater would say? This
lesson previews the tool; its specific failure modes and mitigations are M13-L13's full treatment.

### 5.5 What makes a dataset "you can trust"

Putting §5.1–§5.4 together, a trustworthy evaluation dataset:

| Property | Why |
|---|---|
| Has a true holdout, never used to guide iteration | Prevents §5.1's contamination |
| Is sized for the precision your decision needs | Prevents §5.2's false confidence |
| Is stratified for the cases that matter most, not left to chance | Prevents §5.3's blind spots |
| Uses the right assertion type per case | Avoids §5.4's mismatch between tool and task |
| Is versioned alongside the prompt it evaluates | Ties to M5-L12's artefact discipline — you must know which version of the eval set produced which number |

### 5.6 Assumptions and limitations

- §7.1's 20% generalisation rate and the resulting 56-point gap are illustrative parameters chosen to
  demonstrate a real, well-documented mechanism. The exact size of contamination in any real process
  depends on the task and how the prompt engineer works.
- §7.2 and §7.3 are exact, closed-form statistics; recompute both for your own sample size and your own
  rare-case share rather than reusing this lesson's numbers.
- This lesson does not cover the mechanics of sourcing real traffic for an eval set, human-labelling
  workflows, or inter-rater agreement measurement in depth — each is its own substantial topic.
- LLM-as-judge is previewed, not fully treated; do not adopt it in production without reading M13-L13.

---

## 6. Worked example — the eval set that only ever proved itself right

**The system.** A team builds Project 5's ticket classifier. Early on, they hand-write 12 example
tickets, run the prompt, and iterate — fixing wording whenever one of the 12 comes out wrong. After two
weeks, all 12 pass. The team reports "97% accuracy" in a status update, extrapolating loosely from the
12-example pass rate, and schedules a launch.

**What was actually true, discovered only after launch.** A proper holdout, built afterward from logged
production tickets and never touched during iteration, showed true accuracy closer to 78% — a gap of the
same shape and roughly the same size as §7.1's simulation. **Nobody had lied in the status update.** Every
one of the 12 examples genuinely passed. The number was honest and irrelevant, because the process that
produced it — iterate against a fixed, visible, tiny set until it's perfect — is precisely the mechanism
that manufactures a gap between what the set says and what is true.

**Three defects:**

| # | Defect | Consequence |
|---|---|---|
| 1 | No holdout ever existed — the same 12 examples were both the target of iteration and the reported metric | The report measured "did I patch every visible failure," not quality |
| 2 | 12 examples, reported as a percentage with no confidence interval | Even an honest 12-example measurement would have had a huge CI (§5.2) |
| 3 | No stratification — 12 hand-written examples almost certainly missed rare, high-stakes categories | The categories most likely to cause real harm were never tested at all |

### The fix

**Split from the start**: a small, visible regression suite for fast iteration (M5-L12), and a separate,
genuinely held-out evaluation set — built from real or realistic traffic, never inspected during prompt
changes — used only to report true quality.

**Size the holdout for the decision it supports**, using §5.2's arithmetic — a launch decision usually
needs a tighter interval than a rough internal check.

**Stratify the holdout deliberately** for every case type whose failure would be costly, per §5.3, rather
than trusting that a hand-written or randomly sampled set happens to include them.

**Version the holdout alongside the prompt** (M5-L12), so "quality at launch" is a specific, reproducible,
attributable number, not a status-update estimate nobody can trace back to a dataset.

**The general rule.** **A number that came out of the same set you tuned against is not a quality
measurement — it is a record of how thoroughly you patched what you could see.**

---

## 7. Practical activity

**File:** [`labs/m5/l18_evaluation_dataset.py`](../../labs/m5/l18_evaluation_dataset.py)

**No API key, no network.**

```bash
source .venv/bin/activate
python labs/m5/l18_evaluation_dataset.py
```

Sections 2 and 3 are exact, closed-form statistics. Section 1 is a real simulation of a real, documented
mechanism, with stated illustrative parameters.

### 7.2 Expected output

`[EXECUTED]` — 2026-09-09, Python 3.10.11, NumPy 2.2.6.

```text
============================================================================
1. PROMPT-TUNING CONTAMINATION: THE GAP BETWEEN YOUR EVAL SET AND TRUTH
============================================================================
  True prompt quality: 45% (unknown to whoever is iterating).
  15 examples stay visible and get iterated against every round.
  300 examples are a genuine holdout, never inspected during iteration.
  Each round: patch one failing visible example until it passes. 20% chance the patch is a real, generalising fix
  rather than one that only works for that specific example.

   iteration   visible-set pass rate  TRUE (holdout) pass rate
       start                     67%                       41%
           1                     73%                       41%
           2                     80%                       41%
           3                     87%                       41%
           4                     93%                       41%
           5                    100%                       44%

  After 5 rounds: visible set reads 100%. The true,
  held-out quality moved from 41% to only 44%.
  The visible set now overstates true quality by 56 points.

  Nobody in this simulation acted in bad faith -- every single patch
  genuinely fixed the example in front of them. The gap opened up
  purely because the SAME small set was used to both guide changes
  and report quality. This is M1-L09's leakage family, in a form
  specific to prompt engineering: no gradient ever touched this data,
  and it is contaminated anyway.

============================================================================
2. HOW PRECISELY DO YOU ACTUALLY KNOW YOUR TRUE QUALITY?
============================================================================
  A measured pass rate of 85% on an eval set means different things
  at different sample sizes. This is a DIFFERENT question from M5-L12
  section 3 (which asked: how many samples to reliably DETECT A KNOWN
  GAP between two versions). Here the question is: given ONE
  measurement of 85%, how far from the true value could it be?

       N  std. error                95% CI   CI width
      10       0.113           [63%, 100%]        37%
      30       0.065            [72%, 98%]        26%
     100       0.036            [78%, 92%]        14%
     300       0.021            [81%, 89%]         8%
    1000       0.011            [83%, 87%]         4%
    3000       0.007            [84%, 86%]         3%

  At N=10, the true quality could plausibly be anywhere from about
  56% to 100% -- a measured 85% at that sample size is barely more
  informative than a guess. The interval only becomes tight enough to
  make a real decision from somewhere around a few hundred examples,
  depending how much precision the decision actually needs.

============================================================================
3. STRATIFICATION: RANDOM SAMPLING MISSES THE CASES THAT MATTER MOST
============================================================================
  A critical-but-rare case type makes up 2% of real traffic.
  If your eval set is built by pure random sampling, what is the
  chance it contains ZERO examples of that case type?

   eval set size (N)   P(zero examples of the rare case)
                  10                               81.7%
                  30                               54.5%
                  50                               36.4%
                 100                               13.3%
                 200                                1.8%
                 500                                0.0%

  Solved exactly: a random sample needs at least 149 examples
  before there is even a 95% chance of including ONE instance of this
  2% case type, and 228 for 99%. At the eval-set sizes
  most teams actually build (50-100 examples), a purely random
  sample has a real, substantial chance of never testing the case
  that matters most.

  The fix is not a bigger random sample -- it is STRATIFICATION:
  deliberately including a stated minimum number of examples from
  each case type you care about, by design, rather than hoping
  random chance provides them (M3-L13).

============================================================================
4. WHAT THIS LAB IS AND IS NOT
============================================================================
  REAL: sections 2 and 3 are exact, closed-form statistics -- the
  standard-error and binomial-zero-probability formulas, computed for
  the stated inputs. Recompute them for your own eval set size and
  your own rare-case share; the formulas transfer exactly.

  MOCK, mechanism-real: section 1's contamination simulation uses a
  stated generalisation rate (20%) as a modelling choice. The
  MECHANISM -- iterating against a fixed, visible set inflates its
  own pass rate faster than true quality improves -- is real and
  well documented; the exact 20% and the resulting gap size are
  illustrative, not a measurement of any real prompt-tuning process.

  NOT SHOWN: LLM-as-judge scoring and its own agreement-with-humans
  problem (a preview, not a full treatment -- see M13-L13), and the
  full mechanics of building a stratified sample from real traffic
  logs, which is largely a data-engineering problem outside this
  lesson's scope.

Done.
```

### 7.3 Reading the result

**Section 1 is the lesson's central, sharpest result.** A perfect 100% on the set everyone was watching,
alongside a true quality that moved three points. The mechanism required no dishonesty and no carelessness
— only the ordinary, natural act of iterating against what you can see.

**Section 2 turns "how good is it" into a question with a precision, not just a value.** 85% at N=10 and
85% at N=1,000 are not the same claim, even though they are the same number. A launch decision made from
the first is a launch decision made from a coin flip's worth of information.

**Section 3 shows that size alone does not fix coverage.** A 100-example random eval set still has a
13.3% chance of never testing a case type that occurs 2% of the time in production — exactly the
low-frequency, high-stakes case a stratified design exists to guarantee.

---

## 8. Common mistakes and troubleshooting

1. **Using the same small set as both a regression suite and a quality report.** §7.1 — this is exactly
   what manufactures the gap.
2. **Reporting a percentage with no confidence interval.** A number without a precision is not a
   complete claim (§5.2).
3. **Building an eval set by pure random sampling and assuming it's representative.** §5.3 — coverage of
   rare cases is not guaranteed by size alone.
4. **Treating "the model told me it's right" (LLM-as-judge) as ground truth with no further checking.**
   Preview only here — see M13-L13 before relying on it.
5. **Never updating the eval set as the system or its traffic changes.** A holdout built once can go
   stale.
6. **Not versioning the eval set alongside the prompt it measures.** Makes "why did quality change"
   unanswerable later (M5-L12).
7. **Extrapolating a launch-quality claim from a handful of hand-written examples.** §6, exactly.
8. **Confusing M5-L12's sample-sizing question (detect a known gap) with this lesson's (trust a single
   measurement).** They require different arithmetic.
9. **Assuming a patch that fixes one visible failure generalises to similar cases.** Often it does not
   (§7.1).
10. **Treating contamination as a bad-faith problem rather than a process problem.** It happens to careful,
    honest engineers by default, not despite them.

| Symptom | Likely cause | Fix |
|---|---|---|
| A prompt passes its eval set but underperforms in production | Prompt-tuning contamination | Build a true holdout, never inspected during iteration (§5.1) |
| Two team members disagree on whether quality actually improved | No confidence interval reported | Compute and report the CI, not just the point estimate (§5.2) |
| A rare, high-stakes failure ships unnoticed | Eval set never covered that case type | Add stratified minimum coverage for known critical categories (§5.3) |
| Eval scores drift for unclear reasons over time | Eval set not versioned with the prompt | Fingerprint and version the eval set alongside the artefact (M5-L12) |
| Open-ended output has no clean pass/fail signal | Property assertions don't fit the task | Consider LLM-as-judge, with its own limits in mind (§5.4, M13-L13) |

---

## 9. Security, privacy, reliability, cost

- **Reliability.** Never let the set used to guide prompt iteration also be the set used to report true
  quality — §7.1 measured a 56-point gap from this exact conflation.
- **Reliability.** Report a confidence interval alongside any quality percentage, especially at small
  sample sizes where the interval can span most of the possible range (§5.2).
- **Reliability.** Stratify for known critical, low-frequency case types explicitly — random sampling
  alone leaves a real, computable chance of missing them entirely (§5.3).
- **Cost.** A larger eval set costs more to build and run, but an untrustworthy one costs more later, in
  production incidents a contaminated or under-covered eval set never caught.
- **Privacy.** Real traffic used to build an eval set carries the same sensitivity as the traffic itself —
  apply the same access and retention controls as to production data (M2-L18, M10-L06).
- **Reproducibility.** Version the eval set alongside the prompt artefact it measures (M5-L12), so a
  reported quality number is always attributable to an exact, reconstructable pair.

---

## 10. Exercises

### Exercise 1 — Beginner (~20 min)

1. In one sentence, why is a regression suite (M5-L12) the wrong tool for reporting true quality?
2. What is prompt-tuning contamination, in your own words?
3. Why does M5-L12's sample-sizing question differ from this lesson's confidence-interval question?
4. What does stratified sampling guarantee that random sampling does not?
5. Name one thing LLM-as-judge solves and one new problem it introduces.

### Exercise 2 — Intermediate (~40 min)

1. Run the lab. Report the final gap from section 1 and the sample size needed for a 10-point-wide CI at
   85% from section 2.
2. Change section 1's `GENERALIZE_RATE` to 0.05 and 0.50 and re-run. How does the final gap change, and
   why does that make sense?
3. Using section 2's formula, compute the sample size needed for a 5-point-wide 95% CI at a measured 90%
   pass rate.
4. Using section 3's formula, compute how large an eval set must be to have a 90% chance of including at
   least one example of a case type that is 5% of traffic.
5. Design a stratification plan (a table of case types and minimum counts) for a domain of your choice.

### Exercise 3 — Challenge (~50 min)

1. Build a small `EvalSet` class that enforces a true holdout (raises if the same example is used for
   both iteration and final reporting) and test that it catches a contamination attempt.
2. Implement the confidence-interval calculation as a reusable function and use it to decide, for a
   stated business requirement, the minimum eval-set size you would actually build.
3. Design and simulate an eval set combining property assertions for structured fields and a mock
   LLM-as-judge score for an open-ended field, and discuss where the two could disagree.
4. Extend section 1's simulation to model a team that DOES maintain a proper holdout, checked periodically
   but never iterated against, and compare the reported-vs-true gap to the contaminated version.
5. Write the eval-set design document for Project 5 (the ticket classifier and summarizer): holdout size,
   stratification plan, assertion types per field, and versioning approach.

---

## 11. Quiz

*(Answers: [`answer-keys/module-05-answers.md`](../../answer-keys/module-05-answers.md#m5-l18).)*

**Q1.** In §7.1, the visible set reached 100% while true held-out quality moved only from 41% to 44%,
opening a 56-point gap. This happened even though:

- A. The engineer deliberately falsified results.
- B. The held-out set was mislabelled.
- C. The generalisation rate was set to zero.
- D. Every single patch genuinely fixed the specific example it targeted — no one acted in bad faith.

**Q2.** The mechanism in §7.1 is best described as:

- A. An LLM-specific variant of M1-L09's data leakage family — the same small set both guided changes and reported quality.
- B. A bug specific to the simulation code, not a real risk.
- C. Identical to gradient-based overfitting in model training.
- D. A problem that only occurs with synthetic eval data.

**Q3.** M5-L12 §5.3 asked how many samples are needed to detect a known gap between two versions. §7.2
asks a different question, namely:

- A. How many tokens a golden case should contain.
- B. Whether a prompt should be versioned.
- C. Given one single measurement, how precise is it — i.e., what range could the true value actually be in?
- D. Whether exact-match or property assertions are more expensive.

**Q4.** At N=10 samples, a measured 85% pass rate has a 95% confidence interval of roughly:

- A. Exactly 85%, with no uncertainty.
- B. 63% to 100% — barely more informative than a guess.
- C. 84% to 86%.
- D. 0% to 50%.

**Q5.** Per §7.3, a case type making up 2% of real traffic has what chance of appearing zero times in a
randomly sampled 100-example eval set?

- A. About 13%, a real and non-negligible chance of missing it entirely.
- B. 0%, since 100 examples always guarantees coverage.
- C. 100%, since rare cases are always excluded.
- D. Exactly 2%.

**Q6.** The fix §7.3 recommends for the rare-case coverage problem is:

- A. Doubling the eval set size and hoping for the best.
- B. Removing rare case types from consideration entirely.
- C. Switching to exact-match assertions only.
- D. Stratified sampling — deliberately including a stated minimum number of examples from each case type, not hoping random sampling provides them.

**Q7.** Why is a regression suite (M5-L12) not automatically a trustworthy evaluation dataset?

- A. Regression suites cannot use property assertions.
- B. A regression suite is deliberately iterated against and is often too small to give a precise quality estimate or cover rare cases by design.
- C. Regression suites are always synthetic.
- D. Regression suites cannot be versioned.

**Q8.** What made the contamination in §7.1 dangerous, compared to an obviously bad-faith action?

- A. It required a security vulnerability to occur.
- B. It only affects proprietary models.
- C. It looked and felt like legitimate, careful iteration the whole time, with no single decision that looked wrong.
- D. It only happens when temperature is set above zero.

**Q9.** Section 2's confidence interval and section 3's stratification address:

- A. The same problem, computed two different ways.
- B. Problems that only arise with LLM-as-judge scoring.
- C. Problems that only arise in regression suites, not evaluation datasets.
- D. Two different problems — how precisely you know an average quality number, versus whether you're measuring the right cases at all.

**Q10.** What does this lesson say about LLM-as-judge scoring?

- A. It is previewed but not fully treated here; its own agreement-with-humans problem is covered in M13-L13.
- B. It should never be used under any circumstances.
- C. It completely replaces the need for human labelling in all cases.
- D. It is identical in reliability to an exact-match assertion.

**Q11.** The general principle connecting all three lab sections is:

- A. Bigger eval sets are always better, without exception.
- B. Evaluation is a solved problem once a golden suite exists.
- C. An evaluation dataset's trustworthiness depends on how it was built and used, not on whether a number came out of it.
- D. Only synthetic data can be trusted for evaluation.

**Q12.** Why should the same small set generally not serve as both a regression suite (M5-L12) and the
dataset used to report true quality?

- A. Regression suites are always too large for reporting purposes.
- B. Iterating against it for regression purposes is exactly the process that inflates its own reported pass rate, per §7.1.
- C. Regression suites cannot contain golden cases.
- D. Reporting requires a different programming language than regression testing.

**Q13.** *(Written, rubric-graded.)* In under 150 words: your team reports "94% accuracy" based on a
12-example set that was iterated against for two weeks until every example passed. State what is wrong
with trusting this number and what you would build instead before making a launch decision.

---

## 12. Revision notes

- **A regression suite (M5-L12) and an evaluation dataset serve different purposes.** One is deliberately
  iterated against for fast regression catching; the other must stay a genuine holdout to report true
  quality.
- **Prompt-tuning contamination is data leakage without a training loop.** Measured: iterating against a
  visible 15-example set to 100% moved true held-out quality only 3 points, opening a 56-point gap —
  with every individual patch genuinely correct.
- **A single measurement has a confidence interval, not just a value.** Measured: 85% at N=10 spans a
  95% CI of roughly [63%, 100%]. This is a different question from M5-L12's sample-sizing for detecting a
  known gap.
- **Random sampling does not guarantee coverage of rare, consequential cases.** Measured: a 2%-share case
  type has a 13.3% chance of zero representation in a 100-example random set; 149 examples are needed for
  95% confidence of at least one.
- **Stratify deliberately for the cases that matter most** — coverage by design, not by chance.
- **LLM-as-judge fills a real gap (open-ended output) but introduces its own reliability question** —
  covered fully in M13-L13.
- **Version the eval set alongside the prompt it measures**, so any reported quality number is
  attributable and reproducible (M5-L12).
- **A number from the set you tuned against is not a quality measurement.** It records how thoroughly
  you patched what you could see.

---

## 13. Completion checklist

- [ ] I maintain a genuine holdout, separate from any set used to iterate on the prompt.
- [ ] I report a confidence interval alongside any quality percentage, not just the point estimate.
- [ ] I have stratified my eval set for known critical, low-frequency case types.
- [ ] I do not treat LLM-as-judge output as ground truth without further checking.
- [ ] My eval set is versioned alongside the prompt artefact it measures.
- [ ] I can explain the difference between M5-L12's sample-sizing question and this lesson's.
- [ ] I have never reported a launch-quality number derived from the same set I iterated against.
- [ ] I scored 10/13 on the quiz.

---

## 14. References

- Ioannidis, J. P. A. (2005), *Why Most Published Research Findings Are False* (the general shape of the
  small-sample, iterated-selection problem, outside ML). <https://doi.org/10.1371/journal.pmed.0020124>
  `[UNVERIFIED]`
- Zheng, L., et al. (2023), *Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena*.
  <https://arxiv.org/abs/2306.05685> `[UNVERIFIED]`
- Wilson score interval and the normal-approximation confidence interval for a proportion — any
  standard statistics reference. `[STABLE]`

---

## 15. Next lesson

→ **Project 5 — Ticket Classifier and Summarizer with Validated Output**

You now have every piece Module 5 built: prompt structure, structured output, validation, tools,
streaming, state, context budgets, versioning, injection defence, fallback behaviour, cost accounting,
routing, portability, and a trustworthy way to measure whether any of it actually works. Project 5 puts
all of it into one working system.
