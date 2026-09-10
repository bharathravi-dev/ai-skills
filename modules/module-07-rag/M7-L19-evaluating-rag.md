# M7-L19 — Evaluating RAG: Retrieval vs Answer, Groundedness, Correctness, Completeness

| | |
|---|---|
| **Lesson ID** | M7-L19 |
| **Difficulty** | 3 (Advanced) |
| **Estimated study time** | 2.5 hours |
| **Prerequisites** | [M7-L12](M7-L12-citations-evidence-verification.md), M5-L18 |

---

## 1. Learning objectives

1. **Explain** why retrieval-quality metrics (M6-L13) and answer-quality metrics measure fundamentally
   different things, and why neither substitutes for the other.
2. **Distinguish** groundedness from correctness, and demonstrate a real case where a claim is fully
   grounded and fully incorrect at the same time.
3. **Identify** the dangerous case of an ungrounded but factually correct claim, and explain why
   correctness checks alone cannot catch it.
4. **Measure** completeness for a compound question, and explain why it is independent of both
   groundedness and correctness.
5. **Evaluate** a set of answers across all three axes simultaneously, and explain why a single blended
   score obscures which fix a specific failure actually needs.

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **Retrieval evaluation** | Measuring whether the right documents were found (M6-L13's Precision@k, Recall@k, MRR, nDCG). |
| **Answer evaluation** | Measuring the quality of the generated text itself, independent of how it was measured on the retrieval side. |
| **Groundedness** | Whether a claim is supported by the specific source it cites (M7-L12). |
| **Correctness** | Whether a claim matches real-world, independently-verified ground truth — a separate question from what any cited source says. |
| **Completeness** | Whether an answer addresses everything a (possibly compound) question actually asked. |

---

## 3. Plain-language explanation

### 3.1 Module 7 built many pieces; this lesson asks whether any of them worked

Every lesson since M7-L01 built or measured one piece of a RAG pipeline. This lesson is the capstone
question: given all of it working together, how do you actually know whether the system produces good
answers? The honest answer requires more than one number.

### 3.2 A perfect retrieval score proves less than it sounds like

§7.1 states plainly what M6-L13's metrics do and don't cover: they measure whether the right chunks were
found, in the right order. Nothing about that guarantees the text generated from those chunks is itself
correct, complete, or even genuinely grounded in what was found.

### 3.3 Grounded and correct are not the same claim

§7.2 is this lesson's central, most important distinction: a claim can perfectly, honestly reflect what
its cited source says, and still be wrong — because the source itself is wrong or outdated. M7-L12 already
built the tool for checking groundedness; this lesson shows exactly why it isn't enough on its own.

### 3.4 The reverse case is worse

§7.3 shows the more dangerous direction: a claim that happens to be factually correct, cited to a source
that says nothing of the kind. A correctness check alone would wave this through; only a groundedness
check catches it.

### 3.5 Right and grounded still isn't the whole answer

§7.4 adds a third, independent axis: an answer can be completely true and completely well-cited and still
leave out most of what was actually asked, especially for compound questions — M7-L09's decomposition risk,
now measured on the output side rather than the input side.

### 3.6 Four real answers, four different profiles

§7.5 doesn't just claim these axes are independent — it measures four real answers and finds four
genuinely different score combinations, including one honestly imperfect "ideal" case that reveals its own
inherited flaw.

---

## 4. Analogy

**Grading a research paper on citations, factual accuracy, and completeness separately.** A paper can cite
its sources perfectly, quoting them exactly and in context (groundedness) — and still be built on outdated
research that's since been superseded (a correctness failure the citations themselves cannot reveal). A
different paper might state a fact that happens to be true while attributing it to a source that never
said it (an ungrounded citation, plausible and dangerous exactly because the underlying fact checks out). A
third paper might answer only the first of three questions the assignment actually asked, technically
correct and fully cited for the part it did address, and still fail the assignment. A single letter grade
would tell you none of which problem, if any, a given paper actually has.

### Where the analogy breaks

- **A human grader intuitively separates these concerns without a formal rubric.** This lesson's point is
  precisely that an automated system needs the equivalent of an explicit rubric — nothing separates these
  axes automatically the way a careful reader's judgment does.
- **A paper's "ground truth" is often itself debatable.** §7.2's ground truth (a specific, verified PTO
  figure) is treated as a known, settled fact for this lesson's purposes — real correctness checking often
  has to grapple with ground truth that is itself uncertain or contested.

---

## 5. Detailed technical explanation

### 5.1 Two evaluation layers, two different objects

`[REAL reasoning]` §7.1 states the boundary this lesson works on top of: M6-L13 already covers measuring
whether retrieval found the right chunks (Precision@k, Recall@k, MRR, nDCG) — a perfect score there is
entirely possible while the generated answer itself is still wrong, incomplete, or ungrounded, because
retrieval evaluation and answer evaluation check fundamentally different objects: a ranked list of chunk
IDs, versus a piece of generated text.

### 5.2 Groundedness and correctness, diverging

`[REAL, measured]` §7.2 scored a claim stating "20 days" of senior PTO, citing a real source that genuinely
says exactly that. **Groundedness: 1.00.** Checked against independently-verified, current ground truth
(the real figure had since changed to 25 — M7-L16's exact propagation scenario), **correctness: 0.00.**
**A perfectly grounded claim can be completely wrong, whenever the evidence it's grounded in is itself
wrong.** Groundedness answers "does this match the source?"; correctness answers "does this match
reality?" — genuinely different questions with genuinely different failure modes.

### 5.3 The dangerous reverse case

`[REAL, measured]` §7.3 scored a claim stating the correct referral bonus figure, cited to a source that
never mentions referral bonuses at all. **Groundedness: 0.00. Correctness: 1.00.** **This is the case a
correctness-only check would miss entirely** — the number is right, so a fact-check alone passes it, while
the citation itself is fabricated or misattributed. A user attempting to verify this specific citation
would find a document saying nothing about what was claimed.

### 5.4 Completeness, measured against a decomposed question

`[REAL, measured]` §7.4 scored an answer addressing only the "junior PTO" portion of a three-part compound
question, using M7-L09's decomposition to define the sub-topics being checked. The answer was fully
grounded and fully correct **and scored only 0.33 completeness** — two of three things actually asked about
were never addressed. **Completeness measures coverage of what was asked, entirely independent of whether
what was said is true or supported.**

### 5.5 Four answers, four profiles — including one honest surprise

`[REAL, measured]` §7.5 scored four hand-authored answers across all three axes:

| Answer | Grounded | Correct | Complete |
|---|---|---|---|
| Covers all 3 sub-topics, cites real sources | 1.00 | **0.50** | 1.00 |
| States the stale PTO figure | 1.00 | 0.00 | 0.33 |
| States the correct bonus, wrong citation | 0.00 | 1.00 | 0.33 |
| Correctly answers only 1 of 3 sub-topics | 1.00 | 1.00 | 0.33 |

**The first row is the lesson's most valuable, least expected result.** It looks like the "ideal" answer —
fully grounded, fully complete — and still scores only 0.50 correctness, because it repeats the same stale
senior-PTO figure from §7.2, inherited simply by citing the same imperfect source. **Neither completeness
nor groundedness protects against a correctness problem sitting upstream in the index itself.** No two of
the four rows share the same profile — a single blended score would erase exactly the distinctions that
determine which fix (M7-L16's propagation discipline, citation verification, or M7-L09's decomposition)
each case actually needs.

### 5.6 Assumptions and limitations

- The four example answers in this lesson are hand-authored, standing in for real generated output — no
  real model call was made, consistent with this course's offline-first design.
- Correctness and completeness checks here are narrowed to number and keyword presence, the same
  deliberate simplification M7-L12 used for groundedness — real systems typically need more general
  methods for non-numeric, qualitative claims.
- This lesson does not cover building a real evaluation dataset with human-verified ground truth, which is
  M5-L18's dedicated topic, nor combining all these signals into one production monitoring dashboard.

---

## 6. Worked example — the dashboard that showed 95% quality and hid three different problems

**The system.** A RAG system's quality dashboard tracks a single blended "answer quality" score, averaged
across sampled queries, reported weekly to stakeholders as a single headline number.

**What went wrong.** The score sat around 95% for months, read by leadership as "the system works well."
A detailed audit — triggered by unrelated user complaints — found the sampled answers actually broke down
into three distinct failure categories, each affecting a small but real fraction of queries: some answers
cited stale sources correctly (groundedness fine, correctness compromised); a smaller number had fabricated
or misattributed citations for otherwise-correct facts; and a third group answered only part of
multi-part questions. None of these categories showed up distinctly in the single blended number, because
each individually small failure rate got averaged into an overall score that still looked high.

**Why a single number hid three actionable problems.** Per §5.5, three genuinely different fixes were
needed — reindexing (M7-L16), citation verification (M7-L12), and decomposition-aware answer generation
(M7-L09) — and a single blended score gave no signal about which of the three needed attention, or that
there were three distinct problems at all rather than one diffuse one.

**Three defects:**

| # | Defect | Consequence |
|---|---|---|
| 1 | Only one blended quality metric was tracked, averaging across all failure types | Three distinct, independently fixable problems were invisible as separate signals |
| 2 | No metric distinguished groundedness from correctness | A source-staleness problem (M7-L16's territory) looked identical to a citation-fabrication problem (M7-L12's territory) in the dashboard |
| 3 | Completeness was never measured at all | Partial answers to compound questions were scored as fully correct whenever the part they did answer was accurate |

### The fix

**Track groundedness, correctness, and completeness as separate, visible metrics**, per §5.5 — not
averaged into one number that cannot distinguish their different causes.

**Route each failure type to its actual owning fix**, per §5.5's table — a correctness problem needs
M7-L16's propagation discipline; an ungrounded-but-correct problem needs M7-L12's citation verification; an
incompleteness problem needs M7-L09's decomposition.

**Report all three metrics to stakeholders, not a single blended score**, so a change in any one of them
is visible and actionable rather than smoothed away by averaging.

**The general rule.** **A single "quality" number for a RAG system is a genuine loss of information — it
can stay stable while several independent, differently-caused problems each grow underneath it, invisible
until an unrelated investigation happens to surface them.**

---

## 7. Practical activity

**File:** [`labs/m7/l19_evaluating_rag.py`](../../labs/m7/l19_evaluating_rag.py)

**No API key, no network, no third-party dependencies.** Runs in well under a second.

```bash
source .venv/bin/activate
python labs/m7/l19_evaluating_rag.py
```

### 7.2 Expected output

`[EXECUTED]` — 2026-09-10, Python 3.10.11 (pure standard library).

```text
============================================================================
1. RETRIEVAL EVALUATION IS NOT ANSWER EVALUATION
============================================================================
  Retrieval for this lesson's query found exactly the two right chunks
  (P3 for PTO, P4 for referral bonus) -- by M6-L13's own metrics, this
  retrieval could score a PERFECT Precision@2, Recall@2, and nDCG@2.
  None of that guarantees the GENERATED ANSWER built from these chunks
  is itself correct, complete, or even actually grounded in them --
  retrieval quality and answer quality are measured by ENTIRELY
  different checks, on entirely different objects (a ranked list of
  chunk IDs, versus a generated string of text).

============================================================================
2. GROUNDEDNESS VS. CORRECTNESS: NOT THE SAME AXIS
============================================================================
  Claim: 'Senior employees (3+ years) get 20 days of PTO. [Source: P3]'
  Cited source (P3): 'Full time employees accrue 15 days of PTO per year, increasing to 20 days after 3 years of service.'
  Real-world ground truth (verified independently): senior PTO is actually 25 days now, updated last month.

  Groundedness (does the CITED SOURCE support this claim?): 1.00
  Correctness (does the claim match REAL-WORLD truth?): 0.00

  This claim is FULLY grounded -- P3 really does say '20 days,' so the
  citation is completely honest about what the source contains. It is
  simultaneously INCORRECT, because the source itself is stale (M7-L16's
  propagation problem: the real policy changed, but this chunk was
  never re-indexed). Groundedness measures faithfulness to the SOURCE;
  correctness measures faithfulness to REALITY. A perfectly grounded
  answer can still be wrong if the evidence it was grounded in is wrong.

============================================================================
3. THE DANGEROUS CASE: UNGROUNDED BUT CORRECT
============================================================================
  Claim: 'The referral bonus is 2000 dollars. [Source: P3]'
  Cited source (P3): 'Full time employees accrue 15 days of PTO per year, increasing to 20 days after 3 years of service.'  (says nothing about referral bonuses at all)

  Groundedness: 0.00
  Correctness: 1.00

  The number '2000' happens to be the REAL, correct referral bonus --
  but the CITED source (P3) is about PTO and never mentions it. This
  claim is CORRECT and UNGROUNDED simultaneously -- a genuinely
  dangerous combination, because a fact-check that only asks 'is this
  number right' would pass it, while the citation itself is fabricated
  or misattributed. A user clicking through to 'verify' this citation
  would find a document that says nothing about what was just claimed.
  Checking correctness ALONE, without groundedness, misses this entirely.

============================================================================
4. COMPLETENESS: DID THE ANSWER COVER WHAT WAS ASKED?
============================================================================
  Compound question: 'How many PTO days do junior and senior employees get, and what is the referral bonus?'
  Answer: 'Junior employees get 15 days of PTO. [Source: P3]'

  Sub-topics covered: ['junior PTO']
  Sub-topics MISSING: ['senior PTO', 'referral bonus']
  Completeness score: 0.33

  This answer is fully grounded (P3 really does say 15 days) and fully
  correct (15 IS the real junior PTO figure) -- and still only
  ONE-THIRD complete, because two of the three things the compound
  question actually asked about (senior PTO, referral bonus) are
  simply never addressed. A grounded, correct, INCOMPLETE answer can
  still leave a user with a materially wrong impression of what they
  asked -- exactly the compound-question risk M7-L09 introduced from
  the retrieval side, now measured from the answer side.

============================================================================
5. ALL THREE AXES, ON FOUR REAL ANSWERS
============================================================================
  Label                                       Grounded   Correct  Complete
  Grounded, complete, PARTLY stale                1.00      0.50      1.00
  Grounded, INCORRECT (stale ground truth)        1.00      0.00      0.33
  UNGROUNDED, correct                             0.00      1.00      0.33
  Grounded, correct, INCOMPLETE                   1.00      1.00      0.33

  Notice the first row is not a clean 1.00/1.00/1.00 baseline, and that
  is itself a real, honest finding, not a loose end: this answer covers
  all three sub-topics and is fully grounded in what was retrieved, but
  its correctness is only 0.50, because it repeats the SAME stale
  senior-PTO figure section 2 already found (20, not the real 25) --
  it inherited that error simply by citing the same imperfect source.
  Completeness and groundedness are real, worth measuring, and NEITHER
  one protects against a correctness problem sitting upstream in the
  index itself.

  No two of these four answers share the same three scores. A single
  blended 'quality score' would collapse genuinely different failure
  types into one number -- an ungrounded-but-correct answer and a
  grounded-but-incorrect answer are both 'wrong' in SOME sense, but
  wrong for completely different reasons, needing completely different
  fixes (M7-L16's propagation discipline for the stale case; citation
  verification for the ungrounded case; decomposition, M7-L09, for the
  incomplete case). Measuring all three separately is what makes each
  fix identifiable at all.

============================================================================
6. WHAT THIS LAB IS AND IS NOT
============================================================================
  REAL: every groundedness, correctness, and completeness score in
  this lab is genuinely computed from the stated claims, sources, and
  ground-truth values -- the divergence between axes (section 2's
  grounded-but-wrong case, section 3's ungrounded-but-right case) is a
  real, measured result of these independent checks, not asserted.

  ILLUSTRATIVE: the four example answers are hand-authored, standing
  in for real generated output -- no real model call was made,
  consistent with this course's offline-first design. The correctness
  and completeness checks are narrowed to number/keyword presence, the
  same deliberate simplification M7-L12 used for groundedness.

  NOT SHOWN: retrieval-side metrics themselves (M6-L13 already covers
  Precision@k, Recall@k, MRR, and nDCG in depth); building a real
  evaluation dataset with human-verified ground truth (M5-L18's
  topic); and combining all of Module 7's evaluation signals into one
  dashboard, a natural extension left to the exercises.

Done.
```

### 7.3 Reading the result

**Section 2 and section 3 are mirror images of each other, and reading them side by side is the fastest
way to internalize this lesson's core distinction.** One is grounded-but-wrong; the other is
right-but-ungrounded. Neither failure is visible to a check designed for the other.

**Section 5's first row is worth more than a clean baseline would have been.** A table where one row was
simply 1.00/1.00/1.00 would have implied these three axes are usually aligned. Finding that even the
"best" answer here carries a real, specific, traceable flaw is a more honest and more useful result.

**The worked example in §6 is this lesson's practical punchline.** A single blended score isn't merely
less informative than three separate ones — it can stay reassuringly stable while multiple distinct,
independently fixable problems grow underneath it.

---

## 8. Common mistakes and troubleshooting

1. **Treating a high retrieval score (M6-L13) as evidence the generated answer is good.** §5.1 — these are
   separate measurements of separate things.
2. **Assuming a grounded claim is automatically correct.** §5.2 — groundedness reflects the source, not
   reality; a stale or wrong source produces grounded, wrong claims.
3. **Checking correctness without checking groundedness.** §5.3 — this misses fabricated or misattributed
   citations attached to claims that happen to be factually true.
4. **Not measuring completeness for compound questions.** §5.4 — a fully grounded, fully correct partial
   answer can still fail to address most of what was actually asked.
5. **Reporting a single blended quality score instead of separate axis scores.** §5.5, §6 — this hides
   which of several genuinely different problems is actually present.
6. **Assuming a "best-looking" answer has no flaws without measuring each axis directly.** §5.5 — even a
   grounded, complete answer can carry an inherited correctness problem.

| Symptom | Likely cause | Fix |
|---|---|---|
| A RAG system's retrieval metrics look excellent, but users report wrong answers | Retrieval quality and answer quality were never measured separately | Add answer-level evaluation (groundedness, correctness, completeness) alongside retrieval metrics (§5.1) |
| An answer cites a real source correctly but states outdated information | The claim is grounded but the source itself is stale | Fix at the source with M7-L16's propagation discipline, not at the citation level |
| An answer's facts check out, but its citation doesn't actually support them | The claim is correct but ungrounded — a fabricated or misattributed citation | Add groundedness checking (M7-L12) alongside any correctness/fact-checking |
| An answer to a multi-part question feels incomplete despite being accurate | Completeness was never measured, only correctness of the parts addressed | Decompose the question (M7-L09) and measure sub-topic coverage explicitly |

---

## 9. Security, privacy, reliability, cost

- **Reliability.** Measure retrieval quality (M6-L13) and answer quality separately — a perfect score on
  one says nothing about the other (§5.1).
- **Reliability.** Track groundedness and correctness as distinct metrics — a grounded claim can still be
  wrong if its source is stale, and this distinction determines which team or process needs to act (§5.2,
  §6).
- **Reliability.** Never rely on correctness checks alone to catch citation problems — an ungrounded but
  factually correct claim passes a pure fact-check while still misattributing its source (§5.3).
- **Cost.** Report groundedness, correctness, and completeness as separate, visible metrics rather than a
  single blended score, so a real, specific problem doesn't hide behind an acceptable-looking average (§6).

---

## 10. Exercises

### Exercise 1 — Beginner (~20 min)

1. In one sentence, why doesn't a perfect retrieval score guarantee a correct answer?
2. What is the difference between groundedness and correctness, in your own words?
3. Why is an ungrounded-but-correct claim described as more dangerous than a grounded-but-incorrect one?
4. What does completeness measure that the other two axes do not?
5. Why did this lesson's "best" example answer still score only 0.50 on correctness?

### Exercise 2 — Intermediate (~40 min)

1. Run the lab. Confirm §7.2's and §7.3's diverging scores, and §7.5's four-row table, on your own
   machine.
2. Construct a fifth example answer that is ungrounded AND incorrect AND incomplete, and compute its
   scores on all three axes.
3. Update the stale P3 source to state the correct, current PTO figures, and re-run §7.2's and §7.5's
   examples to confirm correctness improves once the source itself is fixed.
4. Design a new compound question (your own topic) with three sub-topics, and construct answers scoring
   0.33, 0.67, and 1.00 completeness respectively.
5. Using M6-L13's metrics conceptually, describe what a "perfect retrieval, poor answer" scenario would
   look like end to end, combining that lesson's metrics with this one's.

### Exercise 3 — Challenge (~50 min)

1. Extend the correctness and completeness checks to handle non-numeric, qualitative claims (e.g. "allows"
   vs. "prohibits"), not just number/keyword presence.
2. Design and implement a combined evaluation report that scores a batch of answers on all three axes and
   flags each one with its specific failure category (stale source, fabricated citation, or incomplete
   coverage).
3. Research (conceptually) how a real RAG evaluation framework (e.g. one used in production) defines and
   measures groundedness, correctness, and completeness, and compare it to this lesson's approach.
4. Using M5-L18's evaluation-dataset discipline, design a process for building a real, human-verified
   ground-truth set suitable for correctness scoring at scale.
5. Using this lesson's §6 worked example as a model, design a monitoring dashboard specification that
   reports all three axes separately, with example alert thresholds for each.

---

## 11. Quiz

*(Answers: [`answer-keys/module-07-answers.md`](../../answer-keys/module-07-answers.md#m7-l19).)*

**Q1.** Per §7.1, why doesn't a perfect retrieval score guarantee a correct generated answer?

- A. Because retrieval metrics like Precision@k and Recall@k do not actually exist as real, computable measures.
- B. Because retrieval always fails whenever answer generation succeeds, and vice versa.
- C. Retrieval and answer quality are measured by entirely different checks on entirely different objects — a ranked list of chunk IDs versus generated text — and finding the right documents doesn't guarantee the answer built from them is itself correct, complete, or grounded.
- D. Because M6-L13's metrics can only be computed after the final answer has already been generated.

**Q2.** Per §7.2's measured result, how can a claim be fully grounded (1.00) and still incorrect (0.00) at
the same time?

- A. Groundedness measures whether the cited source supports the claim; correctness measures whether the claim matches real-world truth — a claim can accurately reflect a source that is itself stale or wrong.
- B. Groundedness and correctness are actually the same measurement performed twice, so this combination should be impossible.
- C. The claim was measured incorrectly due to a bug in the scoring function.
- D. A claim can never be grounded and incorrect at the same time under any circumstances.

**Q3.** Per §7.2, what specifically made the claim in that example incorrect despite being fully grounded?

- A. The claim contained a typo that the scoring function misread as a different number.
- B. The cited source was never actually retrieved in the first place.
- C. The real-world ground truth was measured incorrectly.
- D. The cited source (P3) was stale — the real-world PTO figure had since changed, but the indexed chunk was never updated, the same propagation problem M7-L16 covered.

**Q4.** Per §7.3's measured result, why is an ungrounded-but-correct claim described as "genuinely
dangerous"?

- A. It is not actually dangerous; the lesson treats this combination as fully acceptable.
- B. A fact-check that only verifies whether the claimed number is true would pass it, while the citation itself is fabricated or misattributed to a source that says nothing about the claim.
- C. It causes the retrieval system to crash immediately upon detection.
- D. It only occurs when a query contains no numbers at all.

**Q5.** Per §7.3, what would a user find if they tried to verify the ungrounded claim's citation?

- A. The exact same claim, restated verbatim, confirming it word for word.
- B. A different document containing an even more specific version of the same claim.
- C. A document that says nothing about what was just claimed — the cited source (P3) never mentions the topic the claim is about at all.
- D. An error message stating the source could not be found.

**Q6.** Per §7.4, what does completeness measure that groundedness and correctness do not?

- A. Whether the answer addresses all parts of what was actually asked, not just whether the parts it does address are supported or true.
- B. Whether the cited source exists in the retrieved context at all.
- C. Whether the claim's numbers match a real-world ground-truth value.
- D. Whether the answer was generated within an acceptable time limit.

**Q7.** Per §7.4's measured result, why was the example answer scored as only one-third complete despite
being fully grounded and fully correct?

- A. Because the answer contained factually incorrect information throughout.
- B. Because the cited source did not actually exist in the retrieved context.
- C. Because the answer's citation format was invalid.
- D. It only addressed one of the three sub-topics the compound question asked about, leaving the other two entirely unaddressed.

**Q8.** Per §7.5, what did the "ideal-looking" answer's actual measured correctness score reveal?

- A. A perfect 1.00 correctness score, confirming the answer was entirely accurate.
- B. Even though the answer was fully grounded and covered all three sub-topics, it scored only 0.50 correctness, because it repeated the same stale senior-PTO figure from the earlier example, inheriting an error from its source.
- C. A correctness score that could not be computed due to a formatting error.
- D. A correctness score of exactly 0.00, indicating the answer was entirely wrong.

**Q9.** Per §7.5, what does this finding demonstrate about completeness and groundedness as safeguards?

- A. Completeness and groundedness together always guarantee full correctness, with no exceptions.
- B. Only groundedness matters; completeness has no relationship to correctness at all.
- C. Neither completeness nor groundedness protects against a correctness problem sitting upstream in the index itself — an answer can be complete and grounded while still repeating a factually stale figure.
- D. Only completeness matters; groundedness has no relationship to correctness at all.

**Q10.** Per §7.5, why would a single blended "quality score" be a poor way to report these four example
answers?

- A. It would collapse genuinely different failure types (stale source, fabricated citation, incomplete coverage) into one number, obscuring which specific fix each case actually needs.
- B. A single blended score would always be more accurate than measuring each axis separately.
- C. Blended scores are impossible to compute for any RAG system, regardless of design.
- D. There is no real difference between the four example answers' underlying problems.

**Q11.** Per §7.6, what is explicitly deferred to M6-L13 rather than covered in this lesson?

- A. Groundedness scoring, which this lesson covers directly instead.
- B. Correctness scoring, which this lesson covers directly instead.
- C. Completeness scoring, which this lesson covers directly instead.
- D. Retrieval-side metrics themselves — Precision@k, Recall@k, MRR, and nDCG.

**Q12.** What is the general lesson this lab demonstrates about evaluating a RAG system?

- A. A single overall quality score is always sufficient for evaluating any RAG system, regardless of context.
- B. Answer quality has multiple genuinely independent axes (groundedness, correctness, completeness) that can each fail separately from the others and from retrieval quality itself, so a complete evaluation must measure all of them separately rather than relying on any single score.
- C. Groundedness, correctness, and completeness always move together and can never diverge from one another.
- D. Retrieval quality is the only thing worth measuring in a RAG system; answer-level evaluation is unnecessary.

**Q13.** *(Written, rubric-graded.)* In under 150 words: your team's RAG dashboard shows a stable 95%
"answer quality" score, but a recent audit found three different kinds of problems in sampled answers.
Based on this lesson, why might the single score have hidden this, and what would you propose instead?

---

## 12. Revision notes

- **Retrieval evaluation (M6-L13) and answer evaluation measure entirely different objects** — a perfect
  retrieval score does not guarantee a correct, complete, or grounded generated answer.
- **Groundedness and correctness are genuinely independent axes** — measured directly: a claim scored
  1.00 groundedness and 0.00 correctness simultaneously, because it accurately reflected a source that was
  itself stale.
- **An ungrounded-but-correct claim is a distinctly dangerous failure mode** — measured directly: a claim
  scored 0.00 groundedness and 1.00 correctness, passing any correctness-only check while citing a source
  that says nothing about the claim.
- **Completeness measures coverage of what was asked, independent of groundedness and correctness** —
  measured directly: a fully grounded, fully correct partial answer scored only 0.33 completeness against
  a three-part compound question.
- **Even a "best-looking" answer can carry an inherited correctness problem** — measured directly: an
  answer that was fully grounded and fully complete still scored only 0.50 correctness, because it repeated
  a stale figure from its source.
- **A single blended quality score hides which specific, differently-caused problem is present** — three
  genuinely different failure types (stale source, fabricated citation, incomplete coverage) each need a
  different fix, and averaging them into one number obscures which fix is actually needed.

---

## 13. Completion checklist

- [ ] I can explain why retrieval-quality and answer-quality metrics measure different things.
- [ ] I can distinguish groundedness from correctness and demonstrate a case where they diverge.
- [ ] I can identify why an ungrounded-but-correct claim is dangerous and why correctness checks alone
      miss it.
- [ ] I can measure completeness for a compound question, independent of groundedness and correctness.
- [ ] I can evaluate a set of answers across all three axes and explain why a blended score would obscure
      the results.
- [ ] I report groundedness, correctness, and completeness as separate metrics, not one blended score.
- [ ] I scored 10/13 on the quiz.

---

## 14. References

- Es, S. et al., *RAGAS: Automated Evaluation of Retrieval Augmented Generation*, 2023 (general reference
  for RAG answer-quality metrics, referenced earlier at M7-L12). `[UNVERIFIED]`
- Anthropic documentation, evaluation guidance for RAG systems where available. `[UNVERIFIED]`

---

## 15. Next lesson

→ M7-L20 — Debugging RAG, Adversarial Documents, Latency and Cost

You now have a complete framework for measuring whether a RAG system actually works. Next, and closing
Module 7: what to do when it doesn't — systematic debugging, documents deliberately crafted to mislead the
system, and the latency and cost accounting a production deployment actually needs.
