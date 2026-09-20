# M10-L12 — Release Evaluation Gates

| | |
|---|---|
| **Lesson ID** | M10-L12 |
| **Difficulty** | 3 (Advanced) |
| **Estimated study time** | 2.0 hours |
| **Prerequisites** | [M5-L18](../module-05-prompting-llm-apps/M5-L18-evaluation-dataset.md), [M7-L19](../module-07-rag/M7-L19-evaluating-rag.md), [M10-L08](M10-L08-bias-subgroup-evaluation.md) |

---

## 1. Learning objectives

1. **Write** a release gate as a decision rule stated before the measurement, not a number read after it.
2. **Distinguish** hard gates that block from budget gates a named owner can accept.
3. **Gate on a confidence bound** rather than a point estimate, and explain what each choice costs.
4. **Gate per slice**, so an aggregate improvement cannot hide a subgroup regression.
5. **Size** an evaluation set from the smallest difference you need to detect, and discount best-of-k selection.

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **Release gate** | A pre-registered rule that decides whether a change may ship. |
| **Hard gate** | A gate whose failure blocks the release; not tradeable against other results. |
| **Budget gate** | A threshold on cost, latency or another resource that a named owner may accept over. |
| **Point estimate** | The observed score on your evaluation set — one draw from a noisy process. |
| **Confidence bound** | An interval around that score; gating on the lower bound asks the release to prove itself. |
| **Slice gate** | A per-subgroup gate that no aggregate result can satisfy on a slice's behalf. |
| **Minimum detectable effect (MDE)** | The smallest difference your evaluation set can distinguish from noise. |
| **Best-of-k inflation** | The apparent gain produced purely by selecting the highest scorer among k candidates. |

---

## 3. Plain-language explanation

### 3.1 A gate is written before the number arrives

A gate is a rule you commit to while you still do not know the result. Once you have the number, any threshold you invent
is a description of that number. The artefact is three lines long: what is measured, on what set, and what happens at
which value — written into the change record before the run.

### 3.2 A point estimate near a threshold is a coin flip

§7.1 simulates a system whose **true** quality is 82% against an 80% gate. At n=100 the observed score clears the gate in
**73%** of runs — the same unchanged system fails a quarter of the time. Worse in the other direction: a system whose true
quality is **78%**, genuinely below the gate, passes in **37%** of runs at n=100 and still **19%** at n=400.

Gating on the lower confidence bound reverses the bias. The same 82% system passes only **8%** of the time at n=100 and
**16%** at n=400 — strict, and honest about the fact that a hundred examples cannot prove a two-point margin.

### 3.3 Aggregates hide the people the change hurts

§7.2: aggregate quality rises from **84.6% to 86.5%**, so an aggregate gate passes. Underneath, **3 of 5 slices** fail a
−2-point rule, including French billing at **−8.0** and screen-reader users at **−7.0**. Those slices are **12% of
volume** — small enough for the headline to improve while the people in them get a materially worse system.

### 3.4 Your evaluation set has a resolution

§7.3: at n=100 the smallest detectable difference is about **10.6 points**. A "5% improvement" claimed on a hundred
examples is noise with a name. At n=3000 it falls to **1.9 points**. Per-slice sets are a fraction of the total, so the
resolution on the slice that matters is usually the worst one you have.

### 3.5 Choosing the winner manufactures a gain

§7.5 scores k **identical** candidates. Picking the best of 20 on a 200-example set produces **+4.90 points** of pure
selection effect; at n=1000 it is still **+2.20**. Report the chosen candidate's score on a held-out confirmation set.

---

## 4. Analogy

**A driving test.** The examiner has a list of immediate failures — a dangerous manoeuvre ends the test regardless of how
the rest went — and a count of minor faults you may accumulate up to a limit. The list exists before you drive, the same
list for everyone, and no amount of excellent parking buys back a red light. A single twenty-minute drive is also a small
sample: passing does not prove you are safe, which is why new drivers carry extra restrictions.

### Where the analogy breaks

- **Driving faults are observed directly; model quality is estimated.** Every gate compares a noisy estimate to a
  threshold, which is why the bound matters (§5.3).
- **The examiner's list is fixed nationally; yours is yours to write** — and the honest work is choosing thresholds you
  will actually enforce when a launch is at stake (§5.2).

---

## 5. Detailed technical explanation

### 5.1 The shape of a gate

```text
gate:      answer_supported_by_retrieved_context
measured:  regression set v7 (n=1200), judge rubric v3, 3 runs, median
rule:      HARD. Wilson lower bound >= 0.90. Below -> blocked, no override.
owner:     retrieval team
recorded:  CR-4471, before the candidate was built
```

Five properties make a gate usable: it names the **metric**, the **set and version**, the **rule**, its **class** (hard or
budget), and an **owner**. A gate that lacks a set version is unauditable; a gate without a class invites negotiation at
the worst moment; a gate without an owner gets waived by whoever is most tired.

### 5.2 Hard gates and budget gates

`[REAL, measured]` §7.4 runs six candidates through five gates:

| Class | Gates in the lab | Failure means |
|---|---|---|
| **Hard** | no slice worse than −2 points; unsafe output rate ≤ 0.5% | Blocked. Not tradeable, no exceptions path in the tool |
| **Quality** | quality ≥ 84% | Review: an owner decides with a recorded reason |
| **Budget** | p95 latency ≤ 2500 ms; cost ≤ £1.50 / 1k | Review: a trade-off someone may accept |

Two candidates are **BLOCKED**, two go to **review**, two **ship**. The instructive row is `E: aggressive prompt` — the
**highest quality score in the table**, blocked by a 1.9% unsafe-output rate. That is the entire purpose of a hard gate:
the headline number does not get to buy its way past a safety result.

The other instructive row is `C: cheaper model`, which fails only the quality gate. It is not blocked — it goes to a
person, who may accept 82.8% for a 60% cost reduction and write down that they did.

### 5.3 Point estimates, bounds, and which error you prefer

`[REAL, simulated]` §7.1. Every gate chooses which mistake to make:

| Rule | Ships a worse system (false pass) | Blocks a fine system (false block) |
|---|---|---|
| Point estimate ≥ threshold | Common: **37%** at n=100 for a system two points below | Uncommon |
| Lower bound ≥ threshold | Rare | Common: **92%** at n=100 for a system two points above |

For a safety gate, prefer the lower bound and accept that small evaluation sets cannot pass it — that is the correct
message, not an obstacle. For a quality gate on a small set, a point estimate with a *stated* interval and a human
decision is more honest than either rule pretending to be automatic.

The bound also tells you what to do next: if the interval straddles the threshold, the answer is **more data**, not more
argument.

### 5.4 Slice gates

`[REAL, measured]` §7.2: 3 of 5 slices regress while the aggregate improves by 1.9 points.

An aggregate gate is a weighted average, and a weighted average is dominated by the largest slice. Gate per slice, with:

- a **tolerance** (−2 points here) set from what the slice's own n can detect (§5.5),
- a **floor** as well as a delta, so a slice that was already poor cannot stay poor by not getting worse,
- and slices chosen from L08's analysis — language, accessibility, tenant, document type, query length.

When a slice is too small to gate, say so explicitly and route it to human review rather than silently dropping it.

### 5.5 Sizing the set

`[REAL, computed]` §7.3, from `z · sqrt(2p(1−p)/n)`:

| n | Smallest detectable difference |
|---|---|
| 50 | ~15.1 points |
| 100 | ~10.6 points |
| 300 | ~6.1 points |
| 1000 | ~3.4 points |
| 3000 | ~1.9 points |

Read it in both directions. Forwards: with the set you have, do not set a tolerance finer than its resolution. Backwards:
if the decision needs 2 points, you need thousands of examples — per slice.

### 5.6 Best-of-k and the confirmation set

`[REAL, simulated]` §7.5: with **identical** candidates, best-of-5 at n=200 gains **+3.28 points** and best-of-20 gains
**+4.90**; at n=1000, **+1.40** and **+2.20**.

The discipline: iterate on a development set, then measure the **one** chosen candidate on a confirmation set it has never
influenced, and report that number in the release record. Selection is a form of leakage (M1-L09) — it just happens at the
decision layer rather than in the data.

### 5.7 Assumptions and limitations

- The lab's quality, safety, latency and cost figures are invented; the statistics are real.
- Simulations assume independent examples. Real evaluation sets cluster (many questions per document), so the effective n
  is smaller than the row count and the true MDE is worse than the table.
- Offline gates do not observe real users. They are necessary, not sufficient — canaries and online monitoring are
  M13-L12 and M13-L14.

---

## 6. Worked example — the gate that moved

**The situation.** A team gated a retrieval change on "answer supported by context ≥ 90%" measured on 150 questions. The
candidate scored **88.7%**.

**What happened.**

1. The author observed that 88.7% "rounds to 89, and the baseline was 89.4, so it is within noise" — true, and precisely
   why a 150-question set could not support a 90% gate at all (§5.5: MDE ≈ 8.7 points).
2. The threshold was lowered to 88% "for this release", in the same thread as the result (§5.1: the gate was written
   after the number).
3. The aggregate hid the change's actual behaviour: it had improved long English questions and broken short
   multilingual ones. No slice gate existed (§5.4).
4. It shipped. Two weeks later, support volume for French customers rose; the regression was 9 points on that slice.
5. The rollback was fast (L14). The review found the evaluation set had **21** French questions.

| # | What went wrong | Fix |
|---|---|---|
| 1 | Gate finer than the set's resolution | Size the set from the MDE, or widen the tolerance and say so |
| 2 | Threshold changed after seeing the result | Gates recorded in the change request before the run |
| 3 | No slice gates | Per-slice delta and floor from the L08 slice list |
| 4 | Slice too small to measure | 21 examples cannot gate; grow the set or route to human review |
| 5 | Point estimate treated as the truth | Report the interval; escalate when it straddles the threshold |

**The general rule.** **If the threshold can move after the measurement, it was never a gate — it was a preference.**

---

## 7. Practical activity

**File:** [`labs/m10/l12_release_gates.py`](../../labs/m10/l12_release_gates.py)

**No API key, no network, no third-party dependencies.** Seeded, so the figures below reproduce exactly.

```bash
source .venv/bin/activate
python labs/m10/l12_release_gates.py
```

### 7.2 Expected output

`[EXECUTED]` — 2026-09-16, Python 3.12.3 (pure standard library). Seeded with `random.Random(1012)`; run twice, output
identical.

```text

============================================================================
1. GATING ON A POINT ESTIMATE VS A CONFIDENCE BOUND
============================================================================
  n=100   true quality 82%, gate at 80%:   point estimate passes 73% of runs,   lower bound passes 8%
  n=400   true quality 82%, gate at 80%:   point estimate passes 87% of runs,   lower bound passes 16%
  n=100   true quality 78% (BELOW the gate):   point estimate passes 37% of runs,   lower bound passes 1%
  n=400   true quality 78% (BELOW the gate):   point estimate passes 19% of runs,   lower bound passes 0%

  A point estimate against a threshold is a coin flip when the true value is
  near it, and lets a genuinely worse system through in a third of runs at
  n=100. A lower confidence bound is strict: it asks the release to PROVE the
  quality, and needs a larger evaluation set to pass at all.

============================================================================
2. AN AGGREGATE IMPROVEMENT HIDING A SLICE REGRESSION
============================================================================
  aggregate: baseline 84.6% -> candidate 86.5% (+1.9%)   an aggregate gate at -0.0% PASSES

  slice                       n   baseline  candidate    change   per-slice gate (-2 points)
  english / billing        2400      86.0%      89.0%     +3.0%   pass
  english / delivery       1500      84.0%      87.0%     +3.0%   pass
  french / billing          260      79.0%      71.0%     -8.0%   FAIL
  french / delivery         140      80.0%      78.0%     -2.0%   FAIL
  screen-reader users       120      81.0%      74.0%     -7.0%   FAIL

  slices failing a -2 point rule: 3 (french / billing, french / delivery, screen-reader users)
  those slices are 12% of volume -- small enough for the
  aggregate to improve while the people in them get a materially worse system.

============================================================================
3. WHAT CAN AN EVALUATION SET OF THIS SIZE EVEN DETECT?
============================================================================
  n=50    smallest detectable difference ~= 15.1%   (so a '8% improvement' claim at this size is noise)
  n=100   smallest detectable difference ~= 10.6%   (so a '5% improvement' claim at this size is noise)
  n=300   smallest detectable difference ~=  6.1%   (so a '3% improvement' claim at this size is noise)
  n=1000  smallest detectable difference ~=  3.4%   (so a '2% improvement' claim at this size is noise)
  n=3000  smallest detectable difference ~=  1.9%   (so a '1% improvement' claim at this size is noise)

  Set the gate's tolerance from the evaluation set you actually have, and size
  the set from the difference you need to detect -- especially per slice, where
  n is a fraction of the total (M3-L14, M5-L18).

============================================================================
4. A GATE SUITE OVER SIX CANDIDATE RELEASES
============================================================================
  candidate                  quality      slices      unsafe         p95        cost   verdict
  A: prompt tweak               pass        pass        pass        pass        pass   ship
  B: new model                  pass        FAIL        pass        pass        pass   BLOCKED
  C: cheaper model              FAIL        pass        pass        pass        pass   review
  D: retrieval change           pass        pass        pass        pass        pass   ship
  E: aggressive prompt          pass        pass        FAIL        pass        pass   BLOCKED
  F: bigger context             pass        pass        pass        FAIL        FAIL   review

  Hard gates (a slice regression, unsafe output rate) block regardless of the
  headline number; budget gates are trade-offs a named owner can accept with a
  recorded reason. 'E: aggressive prompt' has the best quality in the table.

============================================================================
5. BEST-OF-K: HOW MUCH OF AN IMPROVEMENT IS JUST CHOOSING THE WINNER?
============================================================================
  k=1   candidates, n=200  : best observed score exceeds the true value by -0.18% on average
  k=1   candidates, n=1000 : best observed score exceeds the true value by +0.09% on average
  k=5   candidates, n=200  : best observed score exceeds the true value by +3.28% on average
  k=5   candidates, n=1000 : best observed score exceeds the true value by +1.40% on average
  k=20  candidates, n=200  : best observed score exceeds the true value by +4.90% on average
  k=20  candidates, n=1000 : best observed score exceeds the true value by +2.20% on average

  Every candidate here is identical. Picking the best of twenty on one
  evaluation set manufactures 2 to 5 points of 'improvement', and a smaller
  set manufactures more. Hold out a confirmation set for the chosen
  candidate, and report THAT number (M5-L18).

============================================================================
6. WHAT THIS LAB IS AND IS NOT
============================================================================
  REAL: every pass rate, slice figure, detectable difference and inflation
  number above is computed by simulation or by the stated formula.

  ILLUSTRATIVE: quality, safety, latency and cost figures for the six
  candidates are invented; real gates use your measured results.

  NOT SHOWN: online evaluation and canaries (M13-L14), human evaluation
  (M13-L13), and the content of the evaluation set itself (M5-L18).

Done.
```

### 7.3 Reading the result

**Section 1, row 3 is the number to remember**: a system genuinely *below* the gate passes 37% of the time at n=100. Most
teams' evaluation sets are that size.

**Section 2 is what a slice gate is for.** The aggregate row and the slice rows describe the same release.

**Section 4's `E` row** — best quality, blocked — is the test of whether your gates are real.

**Section 5 measures nothing but selection.** All candidates are identical; the gain is an artefact of choosing.

---

## 8. Common mistakes and troubleshooting

1. **Setting the threshold after seeing the score.** §5.1 — record gates in the change request.
2. **Gating on the aggregate only.** §5.4 — 3 slices regressed while the headline improved.
3. **A tolerance finer than the set's resolution.** §5.5 — ±2 points needs ~1000 examples.
4. **Treating every gate as negotiable.** §5.2 — safety results are hard gates or they are decoration.
5. **Treating every gate as hard.** Budget gates need an owner and a recorded trade-off, or releases stall.
6. **Reporting the best of many runs.** §5.6 — +4.90 points from selection alone.
7. **Re-using the development set as the confirmation set.** M1-L09, at the decision layer.
8. **No owner on the gate.** Waivers accrue to whoever is on call at 6pm on a Friday.

| Symptom | Likely cause | Fix |
|---|---|---|
| Gate results flip between runs on the same build | n too small; judge variance | Increase n; average runs; report the interval |
| Every release "passes" and quality still drifts | Aggregate-only gates | Per-slice deltas and floors |
| A gate blocks every candidate | Bound-based gate on a small set | Grow the set, or state the rule as point estimate + interval + human decision |
| Launch reviews become negotiations | No hard/budget classification | Classify gates, name owners, log waivers |
| Offline gains do not appear in production | Selection inflation; distribution shift | Confirmation set; canary and online metrics (M13-L12) |

---

## 9. Security, privacy, reliability, cost

- **Security.** Injection resistance and unsafe-output rate belong in the hard class; a quality gain cannot buy them
  (M10-L10).
- **Privacy.** Evaluation sets often contain real user text — they are personal data with a retention rule (L06), and
  their version is part of the audit record (L13).
- **Reliability.** Gate p95 and error rate, not just quality; F's latency failure in §7.4 is a real production risk
  (M13-L11).
- **Cost.** Large evaluation sets and 3-run medians cost money per release; budget them deliberately, and reserve the
  biggest sets for the gates that block.

---

## 10. Exercises

### Exercise 1 — Beginner (~20 min)

1. Write one gate in the §5.1 format for a system you know.
2. In §7.1, how often did a system two points *below* the gate pass at n=100?
3. Which candidate in §7.4 had the highest quality, and why was it blocked?
4. What is the MDE for n=300?
5. Classify as hard or budget: unsafe output rate; p95 latency; cost per 1k; slice regression.

### Exercise 2 — Intermediate (~40 min)

1. Run the lab. Change `THRESHOLD` to 0.82 and explain what happens to both rules.
2. Add a sixth slice with n=60 and a −5-point change; decide whether it should gate, and justify from §5.5.
3. Add a "citation accuracy ≥ 95%" hard gate to §7.4 with invented figures and re-run the verdicts.
4. Compute the n you would need to gate a slice at ±3 points.
5. Write the waiver record you would want for `C: cheaper model`.

### Exercise 3 — Challenge (~60 min)

1. Build the gate suite for your own system: metric, set version, rule, class, owner — and get it reviewed.
2. Implement it as a script that reads an evaluation run and exits non-zero on any hard-gate failure.
3. Add bootstrap confidence intervals and gate the safety metric on the lower bound.
4. Measure your selection inflation: score 10 prompt variants, pick the best, then re-score on a fresh set.
5. Write the policy for what happens when a gate fails at 5pm before a committed launch date.

---

## 11. Quiz

*(Answers: [`answer-keys/module-10-answers.md`](../../answer-keys/module-10-answers.md#m10-l12).)*

**Q1.** What makes a threshold a gate rather than a preference?

- A. It is computed from the baseline release
- B. It is recorded before the measurement is taken
- C. It applies to safety metrics rather than quality
- D. It is approved by a governance committee

**Q2.** In §7.1, how often did a system whose true quality was 78% pass an 80% point-estimate gate at n=100?

- A. 8% of runs
- B. 19% of runs
- C. 37% of runs
- D. 73% of runs

**Q3.** What does gating on a lower confidence bound ask of a release?

- A. To prove the quality, not merely observe it
- B. To match the baseline on every slice
- C. To use a fixed evaluation set across releases
- D. To reduce variance by averaging runs

**Q4.** In §7.2, what happened to the aggregate score?

- A. It fell, while three slices improved
- B. It stayed flat within noise
- C. It could not be computed without slice weights
- D. It rose 1.9 points while three slices regressed

**Q5.** Why can an aggregate gate miss a serious regression?

- A. Aggregates are computed after gates are applied
- B. Judges score aggregates less reliably
- C. A weighted average is dominated by the largest slices
- D. Aggregate metrics have wider confidence intervals

**Q6.** What is the smallest difference an evaluation set of 100 examples can distinguish from noise?

- A. About 10.6 points
- B. About 6.1 points
- C. About 3.4 points
- D. About 1.9 points

**Q7.** Candidate `E: aggressive prompt` had the best quality score. Why was it blocked?

- A. Its p95 latency exceeded the budget
- B. Its cost exceeded £1.50 per 1k requests
- C. A slice regressed by more than two points
- D. Its unsafe-output rate exceeded the hard gate

**Q8.** What distinguishes a budget gate from a hard gate?

- A. Budget gates are measured on a separate set
- B. A named owner may accept a budget failure with a recorded reason
- C. Budget gates apply only after launch
- D. Hard gates are evaluated first in the pipeline

**Q9.** In §7.5, every candidate had identical true quality. What did best-of-20 at n=200 produce?

- A. No systematic difference from the true value
- B. A gain only when the set was larger
- C. A loss, because selection compounds noise
- D. An apparent gain of about 4.9 points

**Q10.** What is the correct response to best-of-k selection?

- A. Re-measure the chosen candidate on a held-out confirmation set
- B. Increase k so the best candidate is found reliably
- C. Average all candidates' scores and report the mean
- D. Report the median candidate instead of the best

**Q11.** A gate's interval straddles the threshold. What does that indicate?

- A. The metric is the wrong one for this decision
- B. More evaluation data is needed to decide
- C. The threshold should be lowered to the observed value
- D. The candidate should ship with monitoring

**Q12.** Why is a slice with 21 examples unsuitable as a gate?

- A. Small slices are usually not representative of users
- B. Judges are less consistent on small sets
- C. Its resolution is far coarser than any useful tolerance
- D. Slice gates require at least one hundred examples by convention

**Q13.** *(Written, rubric-graded.)* In under 150 words: a candidate improves aggregate quality by 1.5 points on a
400-example set, and your gate is "no regression". Describe what you would check before shipping, and what would make you
block regardless of the aggregate.

---

## 12. Revision notes

- **A gate is pre-registered**: metric, set version, rule, class, owner — written before the run.
- **Point estimates are noisy**: a system 2 points *below* an 80% gate passed **37%** of the time at n=100; **19%** at
  n=400.
- **Bounds are strict**: the same 82% system passed only **8%** at n=100 — a message about your set, not an obstacle.
- **Gate per slice**: aggregate **+1.9** while **3 of 5** slices regressed (−8.0, −7.0, −2.0), covering 12% of volume.
- **MDE**: ~10.6 points at n=100, ~3.4 at n=1000, ~1.9 at n=3000 — set tolerances from this, per slice.
- **Hard vs budget**: the highest-quality candidate was blocked by a 1.9% unsafe rate; the cheap one went to review.
- **Best-of-k inflates**: **+4.90** points at k=20, n=200 with identical candidates. Confirm on held-out data.

---

## 13. Completion checklist

- [ ] I record gates — metric, set version, rule, class, owner — before the measurement.
- [ ] I classify every gate as hard or budget, and hard gates have no override path.
- [ ] I gate per slice with a delta and a floor, chosen from the L08 slice list.
- [ ] I size evaluation sets from the difference I need to detect.
- [ ] I report the chosen candidate's score on a confirmation set it did not influence.
- [ ] I scored at least 10/13 on the quiz.

---

## 14. References

- M5-L18 (evaluation datasets, held-out sets) and M7-L19 (RAG evaluation metrics) `[STABLE]`
- M3-L14 (metrics, confidence) and M1-L09 (leakage — here at the decision layer) `[STABLE]`
- M10-L08 (subgroup evaluation — where the slice list comes from) and M10-L04 (risk register rows for accepted budget failures) `[STABLE]`
- Wilson score interval for a binomial proportion — E. B. Wilson, 1927 `[STABLE]`
- M13-L06 (fine-tuning evaluation and rollback), M13-L12 (offline vs online), M13-L14 (canaries) `[STABLE]`

---

## 15. Next lesson

→ [M10-L13 — Versioning Datasets, Models, Prompts and Configuration; Auditability](M10-L13-versioning-auditability.md)
asks the question a failed gate always raises: exactly which version of which artefact produced this result, and can you
prove it six months later?
