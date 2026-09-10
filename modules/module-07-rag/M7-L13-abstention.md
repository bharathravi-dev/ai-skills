# M7-L13 — Abstention: Teaching the System to Say "I Don't Know"

| | |
|---|---|
| **Lesson ID** | M7-L13 |
| **Difficulty** | 3 (Advanced) |
| **Estimated study time** | 2.0 hours |
| **Prerequisites** | [M7-L12](M7-L12-citations-evidence-verification.md) |

---

## 1. Learning objectives

1. **Explain** what failure shape abstention exists to prevent, connecting directly to M7-L01's and
   M7-L12's own documented failures.
2. **Implement** a threshold-based abstention decision from a retrieval score.
3. **Measure** abstention accuracy as a real confusion matrix, and explain why its two error types carry
   different real-world costs.
4. **Calibrate** an abstention threshold by measuring its trade-off across multiple values, rather than
   choosing one arbitrarily.
5. **Distinguish** a genuinely helpful abstention message from a merely terse refusal.

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **Abstention** | A system's deliberate decision to decline answering, rather than generating an unsupported or low-confidence response. |
| **Abstention threshold** | The score (retrieval, groundedness, or both) below which a system abstains rather than answers. |
| **False positive (abstention context)** | Answering when the system should have abstained — a confident but unsupported or wrong response. |
| **False negative (abstention context)** | Abstaining when the system could have answered correctly — an unnecessary refusal. |
| **Calibration** | Measuring a threshold's actual effect across representative cases, rather than setting it by guesswork. |

---

## 3. Plain-language explanation

### 3.1 M7-L01 and M7-L12 both found this failure; this lesson decides what to do about it

M7-L01 §7.1 showed a closed-book answer inventing a specific, wrong number. M7-L12 §7.3 showed a citation
that pointed to a real source while asserting something that source didn't say. Both are the same failure
shape wearing different clothes: confidence without support. This lesson is about deciding, deliberately
and measurably, when a system should say so instead.

### 3.2 Abstention is a decision, not just a detection

§7.2 builds an actual decision function — not a vague "if the model isn't sure," but a concrete threshold
applied to a real, computed score. §7.3 then asks the harder question a detection mechanism alone can't
answer: how good is this decision, actually?

### 3.3 The two ways to get it wrong are not equally bad

§7.3–§7.4 measure abstention as a genuine confusion matrix, and name the asymmetry directly: answering when
you shouldn't have is a confidently wrong output; abstaining when you shouldn't have is merely an
unnecessary refusal. Both are errors; only one of them actively misleads.

### 3.4 A threshold needs calibrating, not guessing

§7.4 sweeps the abstention threshold across three values and measures what actually happens at each — the
same discipline this course has applied to every other threshold parameter (RRF's k, shingle similarity
cutoffs), now applied to the decision that determines whether a system tells the truth about its own
limits.

### 3.5 Saying "I don't know" well is still a skill

§7.5 closes with something easy to treat as an afterthought: abstaining honestly is necessary but not
sufficient for being helpful — a terse refusal and a genuinely useful one are both honest, but only one of
them actually helps the user.

---

## 4. Analogy

**A reference librarian who knows the limits of their own collection.** A poor librarian, asked a question
their library's books don't cover, might guess an answer that sounds plausible rather than admit the gap —
exactly M7-L01's closed-book risk. A better librarian says "I don't have that here" — but a truly excellent
one says "I don't have that here, but here's what I do have that's related, and here's where you might find
it instead." All three responses are technically "the library doesn't cover this" — only the last one is
actually useful to the person asking.

### Where the analogy breaks

- **A librarian's judgment about "do I actually know this" is instant and intuitive.** §7.2's decision
  function is an explicit, calibrated threshold on a computed score — there is no equivalent intuition to
  fall back on in a system that must decide the same thing millions of times.
- **A librarian rarely produces a wrong answer with total confidence.** §7.3's false-positive risk — a
  system answering fluently and citing a real source while still being wrong — has no close everyday
  parallel; it is specific to how generation and retrieval interact.

---

## 5. Detailed technical explanation

### 5.1 A real, threshold-based abstention decision

`[REAL, measured]` §7.2 ran six queries — three genuinely answerable from a small policy corpus, three
genuinely not — through BM25 (M6-L03's exact formula) and a simple rule: abstain if the top retrieval score
falls below 2.0. The three answerable queries scored 2.21, 3.72, and 6.29 (all answered); the three
unanswerable queries scored 1.66, 1.66, and 0.00 (all abstained). **This is a real decision, computed from
a real signal, not a placeholder.**

### 5.2 Measuring the decision, not just making it

`[REAL, measured]` §7.3 scored this decision as a genuine confusion matrix: **3 true positives (correctly
answered), 3 true negatives (correctly abstained), 0 false positives, 0 false negatives** at threshold 2.0.
**The two error types are not symmetric in cost**: a false positive means the system would confidently
generate an answer from a document that doesn't actually address the question — the exact hallucination
risk M7-L01 demonstrated, now dressed with a citation that looks legitimate (M7-L12). A false negative means
a real, answerable question gets refused unnecessarily — frustrating, but not actively misleading. **This is
M3-L14's classification-cost asymmetry, applied to a new, specific decision.**

### 5.3 The threshold, swept and measured

`[REAL, measured]` §7.4 tested the same six queries at three thresholds:

| Threshold | TP | TN | FP (dangerous) | FN (annoying) |
|---|---|---|---|---|
| 1.0 (too permissive) | 3 | 1 | **2** | 0 |
| 2.0 | 3 | 3 | 0 | 0 |
| 3.0 (too strict) | 2 | 3 | 0 | **1** |

At threshold 1.0, two genuinely unanswerable queries (which happened to share a word — "office,"
"company" — with an unrelated policy) scored just high enough to pass, producing two dangerous false
positives. At threshold 3.0, a genuinely answerable PTO question (2.21) fell below the bar and was wrongly
refused. **Threshold 2.0's perfect separation is a real, measured result for this lab's specific six
queries — not a guarantee that this exact value transfers to a different corpus or query set.**
`[UNVERIFIED — calibrate against your own representative queries, exactly as M6-L11's RRF `k` and
M7-L05's shingle threshold required their own calibration.]`

### 5.4 Abstention quality is a separate question from abstention accuracy

`[MOCK, illustrative]` §7.5 compared two equally honest abstention messages — "I don't know" versus a
version stating what was actually searched and suggesting a next step. **Neither fabricates anything; only
one gives the user somewhere to go.** A system can have a perfectly calibrated abstention decision and
still deliver it in a way that's unhelpfully terse — accuracy and message quality are independent
dimensions, both worth getting right.

### 5.5 Assumptions and limitations

- This lab's answerable/unanswerable labels were assigned by hand for six small, illustrative queries — a
  real system needs this judgment established at meaningfully larger scale, following M5-L18's
  evaluation-dataset discipline.
- The abstention decision here uses retrieval score alone, evaluated before generation. M7-L12's
  groundedness check is a complementary signal, evaluated after generation — combining both into one
  decision is a natural extension not demonstrated in this lab.
- Section 5's abstention messages are hand-authored, not generated by a real model.

---

## 6. Worked example — the support bot that never said "I don't know"

**The system.** A support assistant is launched with no abstention mechanism at all — every query,
however loosely related to the corpus, receives a generated, cited answer, on the theory that "some answer
is better than a refusal."

**What went wrong.** For questions genuinely outside the corpus's coverage, the assistant reliably produced
fluent, confidently-worded, citation-backed answers built from whichever document happened to score highest
— even when that document had nothing to do with the actual question. Users trusted these answers at the
same rate as genuinely correct ones, because nothing in the response's tone or format distinguished a
well-supported answer from a confidently-presented guess.

**Why this went undetected until a serious incident.** Per §5.2, this is exactly the false-positive failure
mode this lesson measures — and without a calibrated abstention mechanism, EVERY out-of-scope query became
a guaranteed false positive, not an occasional one. Nothing in the system's own output signaled the
difference to a user, and no internal metric was tracking it either.

**Three defects:**

| # | Defect | Consequence |
|---|---|---|
| 1 | No abstention mechanism existed at all | Every out-of-scope query produced a confident, unsupported answer by default |
| 2 | No retrieval-score or groundedness threshold was ever established | There was no calibrated signal available to trigger abstention even after the gap was noticed |
| 3 | No confusion-matrix-style evaluation of answer quality vs. query scope was ever run | The scale of the problem (how often this happened) was unknown until a serious incident forced the question |

### The fix

**Implement a calibrated abstention threshold**, per §5.1–§5.3, rather than defaulting to "always answer."

**Measure abstention accuracy as a real confusion matrix against representative queries**, per §5.2, to
know the actual false-positive and false-negative rates before and after any threshold change.

**Design the abstention message to be genuinely helpful**, per §5.4, so declining to answer still gives the
user useful information about why and what to try instead.

**The general rule.** **"Always answer" is not a neutral default — it is a choice that turns every
out-of-scope query into a guaranteed false positive, and the fix is a calibrated, measured abstention
decision, not an assumption that more answers are always better.**

---

## 7. Practical activity

**File:** [`labs/m7/l13_abstention.py`](../../labs/m7/l13_abstention.py)

**No API key, no network, no third-party dependencies.** Runs in well under a second.

```bash
source .venv/bin/activate
python labs/m7/l13_abstention.py
```

### 7.2 Expected output

`[EXECUTED]` — 2026-09-10, Python 3.10.11 (pure standard library).

```text
============================================================================
1. WHY ABSTAIN AT ALL?
============================================================================
  M7-L01 section 1 showed a closed-book mock answer inventing a
  plausible-sounding, specific, WRONG number for a question the model
  had no real access to. M7-L12 showed a citation-backed claim can
  still be ungrounded. Both failures share one shape: the system
  produced a confident-sounding answer when it should have said so
  plainly instead -- 'I don't have enough information to answer that.'
  This lesson is about deciding WHEN to say that, deliberately, not
  leaving it to chance.

============================================================================
2. A REAL ABSTENTION DECISION FUNCTION
============================================================================
  Decision rule: abstain if the top BM25 retrieval score falls below 2.0.

  Query                                               Answerable?  Top score  Decision
  How many days of PTO do employees get?              True         2.210      ANSWER (from P3)
  What is the referral bonus amount?                  True         3.721      ANSWER (from P4)
  How many weeks of parental leave are available?     True         6.288      ANSWER (from P5)
  What is the company stock option vesting schedule?  False        1.656      ABSTAIN
  Can I bring my dog to the office?                   False        1.656      ABSTAIN
  What is the CEO name?                               False        0.000      ABSTAIN

============================================================================
3. MEASURING ABSTENTION ACCURACY -- A REAL CONFUSION MATRIX
============================================================================
  At threshold=2.0:
    Correctly answered (true positive):   3
    Correctly abstained (true negative):  3
    WRONGLY answered (false positive):    0  <- DANGEROUS: confident wrong/ungrounded answer
    WRONGLY abstained (false negative):   0  <- ANNOYING: refused an answerable question

  These two error types are not equally bad. A false positive here
  means the system would have generated an answer from a document
  (M7-L12's groundedness problem) that doesn't actually address the
  question -- exactly M7-L01 section 1's closed-book hallucination
  risk, now happening WITH a citation attached that looks legitimate.
  A false negative means a real, answerable question got an
  unnecessary refusal -- frustrating, but not actively misleading.
  This is the same asymmetry M3-L14 taught for classification generally,
  applied here to a specific, consequential decision.

============================================================================
4. THE THRESHOLD TRADE-OFF, MEASURED
============================================================================
   threshold   TP   TN   FP (dangerous)   FN (annoying)
         1.0    3    1                2               0
         2.0    3    3                0               0
         3.0    2    3                0               1

  At threshold=1.0 (too permissive), the two genuinely unanswerable
  queries that happened to share a word with the Equipment Policy
  ('office', 'company') score just high enough to pass -- the system
  would confidently answer from a document that has nothing to do
  with either question. At threshold=3.0 (too strict), a genuinely
  answerable PTO question (scoring 2.21) gets refused unnecessarily.
  Threshold=2.0 happens to separate this lab's specific 6 queries
  perfectly -- a real, measured result, not a guarantee that any fixed
  threshold generalizes to a different corpus or query set without
  its own calibration.
  `[UNVERIFIED -- calibrate this threshold against your own corpus and
  representative queries, the same discipline M6-L11/M7-L05 applied
  to their own threshold parameters.]`

============================================================================
5. WHAT A GOOD ABSTENTION MESSAGE LOOKS LIKE
============================================================================
  `[MOCK -- hand-authored, illustrating the difference, not generated]`

  Terse:   "I don't know."
  Helpful: "I couldn't find information about stock option vesting in the documents I have access to (company policies on remote work, expenses, PTO, referrals, parental leave, and equipment). This may be covered in a different system, or you may want to check with HR directly."

  Both are honest -- neither fabricates an answer. But the terse version
  gives a user nowhere to go next: is this a permanently unanswerable
  question, a wrong system to ask, or a temporary gap? The helpful
  version states what WAS searched, which narrows down why it failed,
  and suggests a concrete next step. Abstention done well is still a
  genuinely useful response, not merely the absence of a wrong one.

============================================================================
6. WHAT THIS LAB IS AND IS NOT
============================================================================
  REAL: every BM25 score is M6-L03's exact formula; the confusion
  matrix and threshold sweep are computed directly from those scores
  against the stated ground-truth labels, not scripted to fit.

  ILLUSTRATIVE: the answerable/unanswerable ground-truth labels for
  these 6 queries were assigned by hand, based on this lab's own small
  corpus -- a real system needs this labeled 'should the system be
  able to answer this' judgment at meaningfully larger scale (M5-L18's
  evaluation-dataset discipline, applied here). The abstention messages
  in section 5 are hand-authored, not generated by a real model.

  NOT SHOWN: combining retrieval-score-based abstention with M7-L12's
  groundedness-based abstention into one combined decision (a natural
  extension, left to the exercises); and abstention decisions made
  AFTER generation (checking groundedness) versus BEFORE it (checking
  retrieval alone, this lab's approach) as two different points in the
  pipeline where the same underlying decision can be made.

Done.
```

### 7.3 Reading the result

**Section 2's clean separation (all answerable queries above 2.0, all unanswerable below) is a genuinely
good outcome, and worth treating as one, not taking for granted.** It would have been easy for the two
"office"/"company" false-positive-prone queries in section 4 to land just as easily above 2.0 instead of
below it — the specific numbers came out favorably here, which is precisely why section 4's sensitivity
check matters.

**Section 4's table is the lesson's core argument, and it directly mirrors this course's other
threshold-sensitivity findings** (M6-L11's RRF k, M7-L05's shingle threshold). A single "correct" run at one
threshold value is not evidence the value is correct in general; sweeping it and watching what breaks is.

**Section 5 is a small section carrying a disproportionately important point.** It would be easy to treat
abstention as "solved" once the accuracy numbers look good — section 5 is a reminder that accuracy and
usefulness are two different things to get right.

---

## 8. Common mistakes and troubleshooting

1. **Having no abstention mechanism at all, on the theory that any answer beats a refusal.** §6 — this
   turns every out-of-scope query into a guaranteed false positive.
2. **Setting an abstention threshold by guesswork rather than measuring its effect.** §5.3 — a threshold
   that "feels right" can produce either dangerous false positives or excessive false negatives without
   ever being checked.
3. **Treating false positives and false negatives as equally acceptable errors.** §5.2 — a confidently
   wrong answer is a more serious failure than an unnecessary refusal.
4. **Assuming a threshold calibrated on one corpus or query set transfers automatically to another.** §5.3
   — recalibrate against your own representative queries.
5. **Delivering an abstention as a bare "I don't know" with no further information.** §5.4 — this is honest
   but not maximally useful; state what was searched and suggest a next step.
6. **Measuring only whether abstention happens, not whether it happens correctly.** §5.2 — track the full
   confusion matrix, not just an abstention rate in isolation.

| Symptom | Likely cause | Fix |
|---|---|---|
| The system confidently answers questions clearly outside its knowledge base | No abstention mechanism exists, or its threshold is too permissive | Implement and calibrate a threshold-based abstention decision (§5.1, §5.3) |
| Users report the system refuses to answer questions it should be able to answer | The abstention threshold is set too strictly | Lower the threshold and re-measure the confusion matrix (§5.3) |
| Abstention responses feel unhelpful even though they're honest | The abstention message is terse with no context or next step | Design the message to state what was searched and suggest an alternative (§5.4) |
| A threshold that worked well in testing performs poorly in production | The threshold was calibrated on an unrepresentative or too-small query set | Recalibrate against a larger, more representative set of real queries (§5.3, §5.5) |

---

## 9. Security, privacy, reliability, cost

- **Reliability.** Implement a calibrated abstention threshold rather than defaulting to always answering
  — an uncalibrated "always answer" system guarantees false positives on every out-of-scope query (§6).
- **Reliability.** Measure abstention as a full confusion matrix, tracking false positives and false
  negatives separately, since they carry different real-world costs (§5.2).
- **Reliability.** Recalibrate abstention thresholds against your own representative query set — a value
  that worked for one corpus or query mix is not guaranteed to transfer (§5.3).
- **Cost.** Design abstention messages to be genuinely useful, not just honest — a terse refusal that
  offers no next step increases support burden elsewhere even when it correctly avoids a wrong answer
  (§5.4).

---

## 10. Exercises

### Exercise 1 — Beginner (~20 min)

1. In one sentence, what failure shape does abstention exist to prevent?
2. Why is a false positive described as more dangerous than a false negative in this context?
3. What happened at threshold=1.0 in §7.4, and why?
4. What happened at threshold=3.0 in §7.4, and why?
5. What makes the "helpful" abstention message in §7.5 more useful than the terse one, given both are
   honest?

### Exercise 2 — Intermediate (~40 min)

1. Run the lab. Confirm §7.2's six scores and §7.4's threshold sweep on your own machine.
2. Add two new queries (one answerable, one not) to the test set, and confirm whether threshold=2.0 still
   correctly classifies them.
3. Find the threshold value (or range) that would produce zero false positives AND zero false negatives
   for your expanded query set from Exercise 2, if one exists.
4. Rewrite §7.5's helpful abstention message for a different unanswerable query from this lab's set, and
   justify what you included.
5. Using M3-L14's framework, compute precision and recall for the abstention decision at each of §7.4's
   three thresholds, treating "answer" as the positive class.

### Exercise 3 — Challenge (~50 min)

1. Implement a combined abstention decision using BOTH retrieval score (this lab) AND a groundedness check
   (M7-L12) — abstain if EITHER signal falls below its own threshold — and test it on a case where
   retrieval succeeds but groundedness would fail.
2. Design and run an experiment with a larger (15-20 query) test set, computing a full precision-recall
   curve for the abstention decision across a finer sweep of threshold values.
3. Implement an abstention message generator that dynamically lists which topics the corpus actually
   covers (rather than hand-authoring the message), based on the retrieved corpus's own document titles.
4. Research (conceptually) how a real production RAG system might combine multiple abstention signals
   (retrieval score, groundedness, query classification) into one decision, and design the combination
   logic.
5. Using this lesson's §6 worked example as a model, design a monitoring dashboard that would track
   abstention accuracy (the full confusion matrix) in production over time, specifying what to alert on.

---

## 11. Quiz

*(Answers: [`answer-keys/module-07-answers.md`](../../answer-keys/module-07-answers.md#m7-l13).)*

**Q1.** Per §7.1, what shape of failure does abstention exist to prevent?

- A. A system running out of available memory during a query.
- B. A user submitting a query in an unsupported language.
- C. A system producing a confident-sounding answer (whether fabricated, as in M7-L01, or ungrounded despite a citation, as in M7-L12) instead of plainly stating it lacks enough information.
- D. A retrieval system taking longer than expected to return results.

**Q2.** Per §7.2's measured result, why did the "CEO name" query score exactly 0.000?

- A. None of its query terms appear anywhere in the corpus at all, so BM25 has no literal match to score.
- B. The query contained a spelling error that crashed the scoring function.
- C. The corpus was empty at the time this specific query ran.
- D. BM25 always returns exactly 0.000 for questions about people.

**Q3.** Per §7.3, why is a false positive (wrongly answering) described as more dangerous than a false
negative (wrongly abstaining)?

- A. A false positive and a false negative are always equally costly in every system.
- B. A false negative is always more dangerous than a false positive in every system.
- C. Neither error type has any real consequence in a RAG system.
- D. A false positive means the system confidently presents an answer from a document that doesn't actually address the question, an actively misleading outcome, whereas a false negative is only an unnecessary refusal.

**Q4.** Per §7.3, what prior lesson's framework does this asymmetry directly connect to?

- A. M6-L03's BM25 formula, applied here for the first time to classification.
- B. M3-L14's classification-metrics framework, where different error types can carry different real-world costs.
- C. M7-L07's chunking-strategy comparison framework.
- D. M7-L04's hard-format extraction framework.

**Q5.** Per §7.4's measured result, what happened at threshold=1.0 (too permissive)?

- A. Every query in the test set was answered correctly with no errors at all.
- B. The system crashed and produced no output for any query.
- C. Two genuinely unanswerable queries scored just high enough to pass, producing dangerous false positives — the system would have confidently answered from an unrelated document.
- D. All six queries were incorrectly abstained on.

**Q6.** Per §7.4's measured result, what happened at threshold=3.0 (too strict)?

- A. A genuinely answerable PTO question, scoring 2.21, was wrongly abstained on — an unnecessary refusal.
- B. Every unanswerable query was correctly identified with no errors at all.
- C. The threshold had no effect on any query's outcome.
- D. All three answerable queries were wrongly abstained on.

**Q7.** Per §7.4, does the specific threshold (2.0) that worked perfectly for this lab's 6 queries
generalize automatically to a different corpus or query set?

- A. Yes, this exact threshold value is mathematically guaranteed to work for any corpus.
- B. Yes, because BM25 scores are always identical regardless of corpus content.
- C. No, because the threshold value can never be reused across different corpora under any circumstances.
- D. No — it is explicitly labeled unverified and stated to require its own calibration, the same discipline applied to other threshold parameters (RRF's k, shingle similarity thresholds) elsewhere in this course.

**Q8.** Per §7.5, what is the key difference between the terse and helpful abstention messages, given that
both are equally honest?

- A. There is no meaningful difference between the two messages at all.
- B. The helpful version states what was actually searched and suggests a concrete next step, giving the user somewhere to go, while the terse version leaves the user with no way to tell why it failed or what to do next.
- C. The terse version is always preferred because it uses fewer tokens.
- D. The helpful version fabricates an answer, while the terse version does not.

**Q9.** Per §7.5, is an unhelpful, terse abstention message still better than confidently generating a
wrong answer?

- A. No, a terse abstention is always worse than a confidently wrong answer.
- B. Terseness is explicitly stated as the primary goal of good abstention design.
- C. Yes, but that doesn't mean terseness is the goal — abstention done well is still a genuinely useful response, not merely the absence of a wrong one.
- D. The lesson takes no position on whether abstention is preferable to a wrong answer.

**Q10.** Per §7.6, what combination is explicitly named as a natural extension left to the exercises?

- A. Combining retrieval-score-based abstention (this lab's approach) with M7-L12's groundedness-based abstention into one combined decision.
- B. The BM25 formula, which this lesson covers directly instead.
- C. The confusion-matrix framework, which this lesson covers directly instead.
- D. Threshold calibration, which this lesson covers directly instead.

**Q11.** Per §7.6, what two different points in the pipeline can the same underlying abstention decision
be made at?

- A. Only before generation; abstention can never be decided after a claim has been generated.
- B. Only after generation; abstention can never be decided before retrieval runs.
- C. Only during ingestion, before any query is ever received.
- D. Before generation (checking retrieval score alone, this lab's approach) or after generation (checking groundedness, M7-L12's approach).

**Q12.** What is the general lesson this lab demonstrates about abstention?

- A. Abstention should always be triggered regardless of any measurement or calibration.
- B. Abstention is a deliberate, calibrated decision with a measurable accuracy and an asymmetric cost between its two error types, not simply "refuse when unsure."
- C. Abstention has no measurable accuracy and cannot be evaluated in any systematic way.
- D. Abstention and answering are equally safe choices in every situation, with no cost difference at all.

**Q13.** *(Written, rubric-graded.)* In under 150 words: a colleague proposes removing your RAG system's
abstention mechanism entirely, arguing "users would rather get some answer than nothing." Based on this
lesson, how would you respond?

---

## 12. Revision notes

- **Abstention exists to prevent the same failure shape M7-L01 and M7-L12 each demonstrated**: a system
  producing a confident-sounding answer instead of plainly stating it lacks enough support.
- **A real abstention decision is a computed threshold on a real signal** — measured directly: a BM25
  score threshold of 2.0 correctly separated three answerable from three unanswerable queries with zero
  errors.
- **Abstention's two error types are asymmetric in cost**: a false positive (wrongly answering) is
  actively misleading; a false negative (wrongly abstaining) is only an unnecessary refusal — the same
  cost asymmetry M3-L14 taught for classification generally.
- **A threshold needs calibration, not guesswork** — measured directly: threshold 1.0 produced 2 dangerous
  false positives, threshold 3.0 produced 1 annoying false negative, and only 2.0 achieved zero errors for
  this specific query set — a result that does not automatically generalize.
- **Abstention message quality is independent of abstention accuracy** — a system can decide correctly to
  abstain and still deliver that decision unhelpfully; stating what was searched and suggesting a next
  step makes real, measurable difference to usefulness.
- **"Always answer" is a choice, not a neutral default** — it guarantees a false positive on every
  out-of-scope query, exactly the incident this lesson's worked example describes.

---

## 13. Completion checklist

- [ ] I can explain what failure shape abstention exists to prevent.
- [ ] I can implement a threshold-based abstention decision from a retrieval score.
- [ ] I can measure abstention accuracy as a confusion matrix and explain its cost asymmetry.
- [ ] I calibrate an abstention threshold by sweeping and measuring, not by guessing.
- [ ] I design abstention messages to be genuinely helpful, not merely honest.
- [ ] I treat "always answer" as a deliberate choice with a real cost, not a safe default.
- [ ] I scored 10/13 on the quiz.

---

## 14. References

- Anthropic documentation, guidance on model refusals and honesty where available. `[UNVERIFIED]`
- Kamath, A. et al., *Selective Question Answering under Domain Shift*, ACL 2020 (general reference on
  calibrated abstention in QA systems). `[UNVERIFIED]`

---

## 15. Next lesson

→ M7-L14 — Conflicting, Duplicated and Outdated Sources

You now have a calibrated way to decide when NOT to answer. Next: what happens when the system SHOULD
answer, but the retrieved evidence itself disagrees with other evidence — conflicting, duplicated, or
outdated sources that abstention alone cannot resolve.
