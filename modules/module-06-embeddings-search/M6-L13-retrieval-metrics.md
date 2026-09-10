# M6-L13 — Retrieval Metrics: Precision@k, Recall@k, MRR, nDCG and Relevance Labels

| | |
|---|---|
| **Lesson ID** | M6-L13 |
| **Difficulty** | 3 (Advanced) |
| **Estimated study time** | 2.5 hours |
| **Prerequisites** | [M6-L11](M6-L11-hybrid-search-rrf.md), [M3-L14](../module-03-math-ml-essentials/M3-L14-metrics.md) |

---

## 1. Learning objectives

1. **Distinguish** Precision@k from Recall@k precisely, and explain why they are only forced to be equal
   in the special case this module's earlier labs quietly relied on.
2. **Compute** Mean Reciprocal Rank by hand, and identify the task shape it fits.
3. **Compute** DCG and nDCG by hand, and explain what they capture that Precision@k and Recall@k cannot.
4. **Explain** why every one of these metrics is only as meaningful as the relevance labels it is computed
   against.
5. **Select** an appropriate metric (or combination) for a given retrieval task shape.

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **Precision@k** | The fraction of the top-k retrieved documents that are relevant: (relevant in top k) / k. |
| **Recall@k** | The fraction of all relevant documents that were found in the top k: (relevant in top k) / (total relevant). |
| **Mean Reciprocal Rank (MRR)** | The average, across queries, of 1 / (rank of the first relevant result), used when only the first hit matters. |
| **Discounted Cumulative Gain (DCG)** | A sum of graded relevance values, each divided by a logarithmic discount based on rank position, rewarding relevant documents ranked higher. |
| **Normalized DCG (nDCG)** | DCG divided by the DCG of the ideal (relevance-sorted) ordering, producing a score in [0, 1] comparable across queries. |
| **Relevance label** | A judgment — binary or graded — of how well a document satisfies a query, underlying every metric in this lesson. |

---

## 3. Plain-language explanation

### 3.1 This module has used "recall" informally since M6-L06 — this lesson makes it precise

M6-L06, M6-L09, and M6-L10 all reported "recall@k" by comparing an approximate search's results against
an exact top-k ground truth. That setup quietly made Recall@k and Precision@k numerically identical,
because the number of "relevant" documents was always defined as exactly k. §7.1 shows this was a special
case, not a general rule, and gives both metrics their full, general definitions.

### 3.2 Precision and recall answer different questions

Precision@k answers "of what I gave you, how much was good?" Recall@k answers "of everything good that
exists, how much did I find?" These only have to agree when "everything good" happens to number exactly
k — outside that coincidence, as §7.1 shows with two realistic queries, they can move independently and
tell you different things about the same ranking.

### 3.3 Some tasks only care about the first right answer

Not every retrieval task is "return the k best results." An exact-lookup task — find the one ticket about
order GB-4471 — only cares how far down the list the right answer had to be searched for. §7.2 introduces
Mean Reciprocal Rank for exactly this task shape, building on this module's own BM25 (M6-L03).

### 3.4 Membership in the top-k isn't the whole story — order within it matters too

Precision@k and Recall@k only ask whether a relevant document appears somewhere in the top k — not where.
§7.3 shows two rankings with identical Precision@k and Recall@k that clearly differ in quality, because one
buries its best result behind a mediocre one. nDCG is built specifically to capture this difference.

### 3.5 None of these numbers means anything without stating what "relevant" means

§7.4 closes the loop on a theme this module has touched before (M6-L09's filtering, M5-L18's evaluation
discipline): every metric in this lesson is computed against a relevance judgment somebody made, and
changing that judgment's threshold changes the metric's value without the retrieval system changing at
all.

---

## 4. Analogy

**A fishing net compared against a lake's actual fish population.** Precision asks: of everything the net
just pulled up, how much of it was fish you actually wanted (not seaweed, not the wrong species)? Recall
asks: of every fish you wanted that was actually swimming in that lake, how many did this one haul catch?
A net can be extremely precise (everything in it is a keeper) while still missing most of the lake's
keepers entirely — precision and recall are simply not the same question, no matter how good the net is.

MRR is the specific case of fishing for one particular prize fish: you don't care about the rest of the
haul, only how far down the boat had to search before finding it. nDCG is grading the catch by quality, not
just species — and caring whether the best fish came up in the first scoop or the last one.

### Where the analogy breaks

- **A real net either catches a fish or it doesn't — no partial credit.** nDCG's graded relevance (§7.3)
  has no clean equivalent here; a document can be "somewhat" relevant in a way a fish cannot be "somewhat"
  caught.
- **The lake's fish population is fully known to the person grading the analogy, but not to a real search
  system.** §7.4's point — that "how many relevant documents exist" is itself a judgment call — has no
  tension in the fishing version, where the lake's contents are assumed given.

---

## 5. Detailed technical explanation

### 5.1 Precision@k and Recall@k, formally

$$\text{Precision@k} = \frac{|\{\text{relevant documents}\} \cap \{\text{top-}k\text{ results}\}|}{k}
\qquad
\text{Recall@k} = \frac{|\{\text{relevant documents}\} \cap \{\text{top-}k\text{ results}\}|}{|\{\text{relevant documents}\}|}$$

`[REAL]` §7.1 computed both for two queries retrieving the same k = 5 from the same 12-document corpus.
Query A had exactly 2 relevant documents total; both landed in the top 5, giving **Precision@5 = 0.40,
Recall@5 = 1.00**. Query B had 7 relevant documents total; 5 landed in the top 5, giving **Precision@5 =
1.00, Recall@5 = 0.71**. The two queries' Recall@5 values differ sharply for a reason that has nothing to
do with search quality — the size of the true relevant set differs.

**This directly reframes M6-L06/M6-L09/M6-L10's own "recall@k" figures**: those labs always measured
against an exact top-k ground truth, forcing $|\{\text{relevant}\}| = k$ by construction — the one
condition under which Precision@k and Recall@k become numerically identical. That was a deliberate
simplification for measuring index quality, not a general property of the two metrics.

### 5.2 Mean Reciprocal Rank

$$\text{RR} = \frac{1}{\text{rank of first relevant result}} \qquad \text{MRR} = \frac{1}{|Q|}\sum_{q \in Q} \text{RR}_q$$

`[REAL]` §7.2 ran five lookup-style queries (M6-L03's exact BM25) against a ticket corpus where competing
documents mention the target order code as secondary or repeated detail. Three of five queries found their
correct target below rank 1 (rank 2, each contributing RR = 0.5); one query's target matched nothing at
all in the corpus (RR = 0); the resulting **MRR = 0.500**.

**MRR fits tasks where only the first correct answer matters** — it does not evaluate the quality of an
entire top-k list the way Precision@k and Recall@k do, and a query with no correct answer at all
contributes exactly 0, not an error or an exclusion.

### 5.3 DCG and nDCG

$$\text{DCG@k} = \sum_{i=1}^{k} \frac{\text{rel}_i}{\log_2(i + 1)} \qquad \text{nDCG@k} = \frac{\text{DCG@k}}{\text{IDCG@k}}$$

where $\text{IDCG@k}$ is the DCG of the same relevance grades sorted into their ideal (best-first) order.

`[REAL]` §7.3 held the same five documents' relevance grades `[1, 3, 0, 2, 0]` fixed, and compared two
orderings. **Precision@5 and Recall@5 were identical for both (0.60 and 1.00)** — both orderings contain
the same relevant documents somewhere in the top 5. **nDCG was not identical**: burying the best (grade-3)
document at rank 2 behind a merely-okay document scored **nDCG = 0.788**, while the best-to-worst ordering
scored a perfect **nDCG = 1.000**. The logarithmic discount ($\log_2(i+1)$) means a relevant document
ranked 1st counts for more than the identical document ranked 5th — exactly the sensitivity Precision@k
and Recall@k lack. Dividing by IDCG normalizes the score to [0, 1] so it stays comparable across queries
with different numbers of relevant documents or grade distributions, the same purpose normalization served
throughout M6 (M6-L01's cosine, M6-L11's RRF).

### 5.4 Every metric here is a function of a relevance-label choice

`[REAL]` §7.4 added several documents genuinely mixing "damaged" and "refund" concepts and computed the
same query's cosine scores again. With a strict relevance threshold, 2 documents counted as relevant and
**Recall@5 = 1.00**; with a looser threshold, 6 documents counted as relevant, and because that set now
exceeded k = 5, at least one had to fall outside the top 5, giving **Recall@5 = 0.83** — **with the
retrieval system and its ranking completely unchanged between the two measurements.**

**The number moved because the definition of "relevant" moved, not because retrieval got worse.** Any
reported Precision@k, Recall@k, MRR, or nDCG value is only fully specified alongside a stated definition of
its relevance labels — M5-L18's evaluation-dataset discipline, applied here to what "relevant" means.

### 5.5 Assumptions and limitations

- All relevance labels in this lesson's lab are hand-assigned for illustration, not collected from real
  users or annotators — building a trustworthy, real evaluation dataset is M5-L18's deeper topic.
- §7.3's DCG uses linear gain ($\text{rel}_i$ directly), matching common reference implementations (e.g.
  scikit-learn's default). Some production systems use exponential gain ($2^{\text{rel}_i} - 1$) instead,
  which weights high grades more heavily. `[UNVERIFIED — confirm which convention a specific tool or paper
  uses before comparing numbers across systems.]`
- This lesson does not cover inter-annotator agreement measurement on real human relevance judgments, or
  evaluating a full production pipeline (M6-L11's hybrid fusion, M6-L12's reranking) end-to-end against
  these metrics together — both are natural extensions, left to the exercises.

---

## 6. Worked example — the dashboard metric nobody could act on

**The system.** A search team's dashboard reports a single weekly number: "Recall@10 = 0.91." Leadership
tracks it as the team's headline quality metric. One week it drops to 0.84, and the team is asked to
explain the regression.

**What went wrong.** Nobody could answer the question quickly, because the dashboard's documentation never
recorded how "relevant" was defined for the underlying labels, whether it was measured against a fixed or
a growing set of queries, or whether k = 10 was chosen to match a real product surface. The investigation
took days rather than minutes, because the team first had to reconstruct what the number actually meant
before they could investigate why it changed.

**Why it happened, precisely.** Per §5.4, Recall@k is a function of both the ranking AND the relevance
label definition. A change in either one moves the number. Without recording which had changed —or
whether the query set or corpus had grown, changing the denominator — the drop was equally consistent with
"the ranking got worse" and "the relevance labels or query mix changed," and nobody had the information to
tell which.

**Three defects:**

| # | Defect | Consequence |
|---|---|---|
| 1 | The relevance label definition was never documented alongside the metric | A metric change could not be attributed to ranking quality vs. label/query changes |
| 2 | Only one metric (Recall@10) was tracked, with no Precision@k, MRR, or nDCG alongside it | No way to tell whether the regression was about coverage, ordering, or something else |
| 3 | The query set and corpus composition over time were not version-controlled with the metric | A shift in "what's being measured" could masquerade as a shift in "how well it's measured" |

### The fix

**Record the relevance label definition alongside every reported metric**, per §5.4 — a number without
its label definition is not yet a fully specified measurement.

**Track more than one metric together**, per §7.5 — Precision@k, Recall@k, MRR, and nDCG each surface a
different kind of regression, and a single number cannot distinguish between them.

**Version the evaluation query set and corpus alongside the metric history**, the same discipline M5-L18
established for evaluation datasets generally, so a metric change can be traced to its actual cause.

**The general rule.** **A retrieval metric is a function of three things — the ranking, the relevance
labels, and the query/corpus it was measured against — and a metric reported without pinning down the
other two is not yet a diagnosable number.**

---

## 7. Practical activity

**File:** [`labs/m6/l13_retrieval_metrics.py`](../../labs/m6/l13_retrieval_metrics.py)

**No API key, no network.** Runs in under a second.

```bash
source .venv/bin/activate
python labs/m6/l13_retrieval_metrics.py
```

### 7.2 Expected output

`[EXECUTED]` — 2026-09-10, Python 3.10.11, NumPy 2.2.6.

```text
============================================================================
1. PRECISION@K VS RECALL@K -- THEY DIVERGE ONCE |RELEVANT| != K
============================================================================
  Query A: 'damaged item' -- 2 relevant documents exist in the whole corpus: ['D1', 'D3']
  Top-5 ranking: ['D1', 'D3', 'D2', 'D4', 'D5']
  Precision@5 = (relevant in top 5) / 5 = 0.40
  Recall@5    = (relevant in top 5) / 2 total relevant = 1.00

  Query B: 'refund' -- 7 relevant documents exist in the whole corpus: ['D10', 'D11', 'D2', 'D4', 'D5', 'D7', 'D9']
  Top-5 ranking: ['D2', 'D4', 'D5', 'D9', 'D11']
  Precision@5 = (relevant in top 5) / 5 = 1.00
  Recall@5    = (relevant in top 5) / 7 total relevant = 0.71

  Both queries retrieved the SAME k=5, and both found several relevant
  documents in their top 5 -- but Recall@5 tells two very different
  stories, because it divides by how many relevant documents EXIST, not
  by k. M6-L06/M6-L09/M6-L10 always compared against an exact top-k
  ground truth, which quietly forced |relevant| = k -- making Precision@k
  and Recall@k numerically identical there. That equality was a special
  case of this section's ground truth, not a general property of the two
  metrics -- outside that special case, as here, they answer different
  questions: 'how much of what I returned is good?' (precision) versus
  'how much of what exists did I find?' (recall).

============================================================================
2. MEAN RECIPROCAL RANK -- WHEN ONLY THE FIRST HIT MATTERS
============================================================================
  Five lookup queries, each with exactly one correct target document
  (or none, for the last). Ranked by BM25 over this ticket corpus:

  Query  'GB-4471'  target=   T1  ranking=['T1', 'T10', 'T3', 'T2']...  rank 1  RR=1.000
  Query  'GB-9002'  target=   T2  ranking=['T5', 'T2', 'T1', 'T3']...  rank 2  RR=0.500
  Query  'GB-1183'  target=   T4  ranking=['T7', 'T4', 'T1', 'T2']...  rank 2  RR=0.500
  Query  'GB-5567'  target=   T6  ranking=['T9', 'T6', 'T1', 'T2']...  rank 2  RR=0.500
  Query  'GB-9999'  target= None  ranking=['T1', 'T2', 'T3', 'T4']...  not the correct target / not found  RR=0.000

  MRR = mean of the 5 reciprocal ranks above = 0.500

  Notice T5 and T10 (which mention GB-9002 and GB-4471 as SECONDARY
  detail) and T7 (which repeats GB-1183 three times) compete with the
  actual target tickets -- BM25's term-frequency term rewards exactly
  this repetition, sometimes pushing the true target below rank 1. MRR
  penalizes this smoothly (1/2, 1/3, ...) rather than treating 'not
  rank 1' as a flat failure -- and the GB-9999 query, matching nothing,
  contributes exactly 0, the same way a genuinely absent answer should.

============================================================================
3. nDCG -- GRADED RELEVANCE, AND ORDER WITHIN THE TOP-K
============================================================================
  Ranking X (grades in order): [1, 3, 0, 2, 0]
  Ranking Y (grades in order): [3, 2, 1, 0, 0]

  Precision@5:  X=0.60   Y=0.60   (IDENTICAL -- same 3 relevant docs present in top 5)
  Recall@5:     X=1.00   Y=1.00   (IDENTICAL -- same reason)

  DCG@5  (discount 1/log2(rank+1) per position): X=3.754   Y=4.762
  IDCG@5 (DCG of the ideal, grade-sorted order [3, 2, 1, 0, 0]): 4.762
  nDCG@5 = DCG / IDCG: X=0.788   Y=1.000

  Precision@5 and Recall@5 are blind to WHERE within the top 5 a
  relevant document sits -- only whether it is present at all. nDCG is
  not: Ranking X buries its best (grade-3) document at rank 2 behind a
  merely-okay (grade-1) document at rank 1, and its nDCG (below 1.0)
  reflects that real quality loss, while Ranking Y -- the same relevant
  documents, in best-to-worst order -- scores a perfect 1.000, because
  Y IS its own ideal ordering.

============================================================================
4. EVERY METRIC ABOVE IS ONLY AS GOOD AS ITS RELEVANCE LABELS
============================================================================
  Section 1's relevant sets were hand-labeled by what the query actually
  asks for. In practice, 'relevant' is often defined by thresholding a
  SCORE -- and the threshold chosen changes every metric computed from
  it, with the ranking itself never changing at all.

  Four new mixed documents added, each combining 'damaged' and 'refund'
  concepts in different proportions, scored for query 'damaged item':
    D13 ('my item was damaged so please refund the money'): 0.575
    D14 ('damaged please refund'): 0.684
    D15 ('please help with a refund the item may be damaged during shipping'): 0.695
    D16 ('refund please the item was a little damaged i think'): 0.718
  (D1/D3 score 1.000; every purely-refund/tracking document scores 0.000)

  Threshold strict (>= 0.90): ['D1', 'D3'] count as 'relevant' (2 docs) -> Recall@5 = 1.00
  Threshold loose (>= 0.25): ['D1', 'D13', 'D14', 'D15', 'D16', 'D3'] count as 'relevant' (6 docs) -> Recall@5 = 0.83

  The retrieval system and its ranking did NOT change between these two
  lines -- only the DEFINITION of 'relevant' changed. The strict threshold's
  2 relevant documents are both comfortably inside the top 5, for perfect
  recall. The loose threshold recognizes more documents as genuinely
  on-topic, but that set is now LARGER than k=5 -- so by simple pigeonhole,
  at least one loosely-relevant document must fall outside the top 5,
  and recall drops below 1.00, even though retrieval itself never changed.
  A metric reported without stating how its relevance labels were defined
  is not yet a fully specified number (M5-L18's discipline: the evaluation
  dataset -- here, the label definition -- is as load-bearing as the
  system being evaluated).

============================================================================
5. ALL FOUR METRICS, SIDE BY SIDE, ON ONE RANKING
============================================================================
  Ranking under evaluation (grades in order): [3, 2, 2, 1, 0, 1]
  (5 of 6 documents are relevant at grade >= 1)

  Precision@1 = 1.00   Recall@1 = 0.20
  Precision@3 = 1.00   Recall@3 = 0.60
  Precision@6 = 0.83   Recall@6 = 1.00

  Reciprocal rank (this one ranking) = 1/1 = 1.000
  nDCG@6 = 6.049 / 6.079 = 0.995  (ideal order would be grades [3, 2, 2, 1, 1, 0])

  Read these together, not in isolation. Precision@1 and the reciprocal
  rank agree that the very top result is strong. Recall climbs steadily
  as k grows, showing most relevant documents are present SOMEWHERE in
  the list. nDCG, just under 1.0, shows the order is good but not
  perfectly sorted by relevance grade -- a distinction none of the other
  three numbers can express on their own.

============================================================================
6. WHAT THIS LAB IS AND IS NOT
============================================================================
  REAL: every Precision@k, Recall@k, MRR and DCG/nDCG value is computed
  from its exact, standard formula against explicitly stated relevance
  labels and rankings -- BM25 (section 2) and cosine (sections 1, 4) use
  M6-L01/M6-L03's exact mechanisms.

  ILLUSTRATIVE: all relevance labels (binary sets in sections 1/2,
  graded 0-3 labels in sections 3/5) are hand-assigned for this lab,
  not collected from real users or annotators -- M5-L18 covers building
  a trustworthy evaluation dataset from real judgments in more depth.

  NOT SHOWN: inter-annotator agreement measurement on real human labels,
  and evaluating a full production ranking pipeline (M6-L11's hybrid
  fusion, M6-L12's reranking) end-to-end against these metrics together
  -- a natural next exercise, left to this lesson's own exercises.

Done.
```

### 7.3 Reading the result

**Section 1 corrects a simplification the whole module has been quietly relying on.** It would have been
easy to let M6-L06's "recall@k" stand as if it were the general definition. It wasn't — it was the special
case where the ground truth's size happens to equal k. Seeing the two metrics diverge on realistic queries
is worth more than the formula alone.

**Section 3's paired rankings are the single clearest illustration in this lesson.** Identical Precision@5,
identical Recall@5, visibly different nDCG — proof, not just assertion, that these metrics measure
genuinely different things.

**Section 4 is the lesson's most consequential finding for real work.** A metric can move by a meaningful
amount with the retrieval system frozen solid, purely from a labeling decision. Anyone reading a retrieval
metric in a report should now ask what section 4 asks: relevant, according to what definition?

---

## 8. Common mistakes and troubleshooting

1. **Treating Precision@k and Recall@k as interchangeable, or assuming they're always equal.** §5.1 — they
   coincide only when the relevant-set size equals k, a special case, not the general rule.
2. **Using MRR to evaluate a task where the whole top-k list's quality matters, not just the first hit.**
   §5.2 — MRR discards all information past the first relevant result; use Precision@k/Recall@k or nDCG
   instead for whole-list quality.
3. **Reporting Recall@k without stating how "relevant" was defined.** §5.4 — the number is not fully
   specified without its label definition, and can move independent of the ranking.
4. **Assuming a high Precision@k or Recall@k means the ranking is well-ordered.** §5.3 — neither metric
   sees position within the top k; use nDCG to evaluate ordering quality specifically.
5. **Comparing nDCG values computed under different gain conventions (linear vs. exponential) as if they
   were the same metric.** §5.5 — confirm which convention a specific tool or paper uses first.
6. **Tracking only one retrieval metric in production.** §6 — different metrics surface different kinds of
   regression; one number alone cannot distinguish a coverage problem from an ordering problem.

| Symptom | Likely cause | Fix |
|---|---|---|
| Precision@k and Recall@k disagree sharply for the same query | The number of truly relevant documents does not equal k | Expected behavior — report both explicitly rather than picking one (§5.1) |
| Two rankings score identically on Precision@k and Recall@k but seem different in quality | Both metrics are blind to order within the top k | Compute nDCG to capture ordering quality (§5.3) |
| A reported retrieval metric changed and nobody can explain why | The relevance label definition, query set, or corpus changed alongside (or instead of) the ranking | Version and document all three alongside the metric (§6) |
| MRR seems like the wrong metric for a use case | The task actually requires evaluating a full top-k list, not just the first hit | Use Precision@k, Recall@k, or nDCG instead (§5.2) |

---

## 9. Security, privacy, reliability, cost

- **Reliability.** Always state the relevance label definition alongside any reported Precision@k,
  Recall@k, MRR, or nDCG value — the number is not diagnosable without it (§5.4, §6).
- **Reliability.** Track more than one retrieval metric together in production — each surfaces a different
  failure mode, and no single number distinguishes a coverage regression from an ordering regression (§6).
- **Reliability.** Version the evaluation query set and corpus alongside metric history, the same
  discipline M5-L18 established for evaluation datasets generally, so a metric shift can be traced to its
  real cause rather than guessed at.
- **Cost.** Choosing the right metric for a task shape (MRR for single-answer lookup vs. nDCG for graded,
  ordered relevance) avoids spending optimization effort chasing a metric that doesn't reflect the actual
  product goal.

---

## 10. Exercises

### Exercise 1 — Beginner (~20 min)

1. In one sentence, why are Precision@k and Recall@k not always equal?
2. Write the formula for MRR and explain, in your own words, what task shape it fits.
3. What does nDCG capture that Precision@k and Recall@k cannot?
4. Using this lesson's Section 4 finding, explain why "Recall@10 = 0.91" is not yet a fully specified
   claim on its own.
5. Name one metric from this lesson you would use for a "find the one right answer" chatbot lookup
   feature, and one you would use for a "show the 10 best results" search page — and justify each choice.

### Exercise 2 — Intermediate (~40 min)

1. Run the lab. Confirm section 1's Precision@5/Recall@5 values and section 3's DCG/nDCG values by hand
   for at least one case each.
2. Using section 2's lookup corpus, add a sixth query with its own target document and compute its
   reciprocal rank, then recompute the overall MRR.
3. Using section 3's grade list, construct a THIRD ranking (a different order of the same five grades)
   and compute its nDCG, placing it between Ranking X and Ranking Y in quality.
4. Using section 4's method, choose a third threshold value and report how Recall@5 changes yet again,
   with the ranking held fixed.
5. Explain, using section 5's combined output, a real product scenario where Precision@1 could be high
   while nDCG is comparatively low, and what that combination would tell a product team.

### Exercise 3 — Challenge (~50 min)

1. Implement the exponential-gain variant of DCG ($2^{\text{rel}_i}-1$ instead of $\text{rel}_i$) and
   compare its nDCG values against this lab's linear-gain results on section 3's two rankings.
2. Evaluate M6-L11's hybrid RRF-fused ranking and M6-L12's reranked shortlist against a hand-assigned set
   of graded relevance labels, computing all four metrics from this lesson on each, and compare them.
3. Design and implement a small experiment measuring how MRR changes as a systematic bias is introduced
   into a ranking (e.g. a specific document type consistently pushed one rank lower).
4. Research (conceptually) precision-recall curves and average precision (AP) as an alternative to
   picking a single k, and explain when they would be preferable to this lesson's fixed-k metrics.
5. Write a short retrieval-metrics reporting standard for a hypothetical team: which metrics to track,
   at what k, with what relevance-label definition documented, and why — directly addressing §6's
   incident.

---

## 11. Quiz

*(Answers: [`answer-keys/module-06-answers.md`](../../answer-keys/module-06-answers.md#m6-l13).)*

**Q1.** In §7.1, Query A had 2 total relevant documents and Query B had 7, and both retrieved k = 5. What
does this demonstrate about Precision@k and Recall@k in general?

- A. They are only numerically forced to be equal when the total number of relevant documents happens to equal k exactly; in general they answer different questions and can diverge, as the two queries' differing Recall@5 shows.
- B. Precision@k and Recall@k are mathematically identical formulas and will always produce the same number.
- C. Recall@k is only defined when k is larger than the corpus size.
- D. Precision@k cannot be computed unless every document in the corpus has been manually labeled.

**Q2.** Precision@k is defined as:

- A. (number of relevant documents in the top k) divided by k.
- B. (number of relevant documents in the top k) divided by the total number of relevant documents in the corpus.
- C. (total number of documents in the corpus) divided by k.
- D. (number of relevant documents anywhere in the corpus) divided by k.

**Q3.** Recall@k is defined as:

- A. (number of relevant documents in the top k) divided by k.
- B. (total number of documents in the corpus) divided by the number of relevant documents.
- C. (number of irrelevant documents in the top k) divided by k.
- D. (number of relevant documents in the top k) divided by the total number of relevant documents that exist for that query.

**Q4.** Mean Reciprocal Rank (MRR) is most appropriate for tasks where:

- A. Only the position of the first correct/relevant result matters, such as an exact-lookup task with one right answer.
- B. There is no way to define a "correct" document at all.
- C. Every document in the ranked list must be individually graded on a 0-3 scale.
- D. The total size of the corpus is unknown.

**Q5.** In §7.2, the query "GB-9002" found its correct target document (T2) at rank 2. What is the
reciprocal rank contribution for this query?

- A. 2.0
- B. 1/2 = 0.5
- C. 0.0
- D. 1.0

**Q6.** In §7.2, the query "GB-9999" matched no document containing that code at all. What did this query
contribute to the MRR calculation?

- A. It was excluded from the average entirely.
- B. It contributed a reciprocal rank of 1.0, treated as a trivial success.
- C. It caused the entire MRR calculation to fail with an error.
- D. It contributed a reciprocal rank of exactly 0, the same way a genuinely absent correct answer should be scored.

**Q7.** Per §7.3, what does nDCG capture that Precision@k and Recall@k cannot?

- A. The total number of documents in the corpus.
- B. Whether the query contains a negation.
- C. The ORDER in which relevant documents appear within the top k, not just whether they are present at all.
- D. Whether BM25 or cosine similarity was used to produce the ranking.

**Q8.** Per §7.3, DCG discounts each document's relevance grade using a factor based on:

- A. The alphabetical order of the document's ID.
- B. The total number of queries evaluated.
- C. The document's logarithmically-scaled rank position, so lower-ranked positions count for less.
- D. Whether the document's relevance grade is even or odd.

**Q9.** Per §7.3, dividing DCG by IDCG (the DCG of the ideal, relevance-sorted order) to get nDCG serves
to:

- A. Make the metric artificially larger than 1.0 for strong rankings.
- B. Normalize the score to a comparable [0, 1] range regardless of how many relevant documents or what grades a specific query happens to have.
- C. Remove the effect of relevance grades entirely, reducing nDCG to plain recall.
- D. Convert a graded relevance scale into a binary one before scoring.

**Q10.** Per §7.4, adding several documents with intermediate relevance and changing the "relevant"
threshold from strict to loose changed Recall@5 from 1.00 to 0.83 even though:

- A. The total number of documents in the corpus decreased.
- B. The value of k was changed from 5 to 6.
- C. The query itself was changed to a completely different topic.
- D. The retrieval system and its ranking never changed at all — only the definition of "relevant" changed.

**Q11.** Per §7.5, computing Precision@k, Recall@k, MRR, and nDCG together on the same ranking showed
that:

- A. All four metrics always produce identical values on any ranking.
- B. Only one of the four metrics is ever meaningful; the other three are redundant.
- C. Each metric captures a different aspect of ranking quality, and no single one of them tells the complete story on its own.
- D. nDCG is a replacement for Precision@k and Recall@k and should always be used instead of them.

**Q12.** How do Precision@k and Recall@k in this lesson relate to the "precision" and "recall" taught in
M3-L14?

- A. They are unrelated concepts that happen to share the same names by coincidence.
- B. M3-L14's precision and recall apply to a single classification decision over a whole dataset; this lesson applies the same underlying concept to the top-k truncation of a ranked list, computed per query and typically averaged across queries.
- C. M3-L14's metrics are strictly more general and make this lesson's Precision@k and Recall@k unnecessary.
- D. This lesson's metrics replace the confusion matrix entirely.

**Q13.** *(Written, rubric-graded.)* In under 150 words: your team reports "Recall@10 = 0.95" for a search
feature with no further detail given. Based on this lesson, what additional information would you need
before trusting or acting on this number, and why?

---

## 12. Revision notes

- **Precision@k and Recall@k are different questions that happen to coincide only when the true relevant
  set's size equals k** — a special case this module's earlier labs relied on (M6-L06, M6-L09, M6-L10),
  not a general property. Measured: two queries with the same k=5 produced Recall@5 of 1.00 and 0.71.
- **MRR fits exact-lookup, single-answer tasks** — it averages 1/rank of the first relevant result, and a
  query with no correct answer at all contributes exactly 0. Measured MRR = 0.500 across five queries where
  competing documents' repeated terms pushed several true targets to rank 2.
- **nDCG captures ordering quality within the top k that Precision@k and Recall@k cannot see.** Measured:
  two rankings with identical Precision@5 (0.60) and Recall@5 (1.00) scored nDCG 0.788 versus 1.000, purely
  from reordering the same relevant documents.
- **Every metric in this lesson is a function of its relevance-label definition, not just the ranking.**
  Measured: Recall@5 moved from 1.00 to 0.83 purely from loosening a relevance threshold, with the ranking
  completely unchanged.
- **A retrieval metric is fully specified only alongside its k, its relevance-label definition, and the
  query/corpus it was measured against** — reporting the number alone is not enough to diagnose a change
  in it.
- **No single metric tells the whole story** — Precision@k, Recall@k, MRR, and nDCG each surface a
  different aspect of ranking quality, and production systems should track more than one together.

---

## 13. Completion checklist

- [ ] I can state the formulas for Precision@k and Recall@k and explain when they coincide versus diverge.
- [ ] I can compute Mean Reciprocal Rank by hand from a small set of ranked queries.
- [ ] I can compute DCG and nDCG by hand and explain what the logarithmic discount and normalization do.
- [ ] I can explain why a retrieval metric is only as meaningful as its relevance-label definition.
- [ ] I can select an appropriate metric (or combination) for a given retrieval task shape.
- [ ] I track more than one retrieval metric together rather than relying on a single reported number.
- [ ] I scored 10/13 on the quiz.

---

## 14. References

- Järvelin, K., Kekäläinen, J., *Cumulated Gain-Based Evaluation of IR Techniques*, ACM TOIS 2002 (the
  original DCG/nDCG paper). `[UNVERIFIED]`
- scikit-learn documentation, `sklearn.metrics.ndcg_score` (linear-gain DCG convention referenced in
  §5.5). <https://scikit-learn.org/stable/modules/generated/sklearn.metrics.ndcg_score.html> `[UNVERIFIED]`

---

## 15. Next lesson

Module 6 is complete. You now have a full toolkit for building and evaluating a search system: semantic
and exact matching, embeddings and dimensionality, BM25 and dense retrieval, exact and approximate nearest-
neighbor search, vector databases and pgvector, metadata filtering, index lifecycle management, hybrid
search with RRF, cross-encoder reranking, and the metrics to measure all of it rigorously.

→ **Project 6: Semantic and Hybrid Search over Course Descriptions** applies this module end to end.
→ Module 7 (RAG) builds directly on this foundation: retrieval is the "R" in Retrieval-Augmented
Generation, and every technique in this module — from embeddings to reranking to evaluation — becomes a
component in a full RAG pipeline.
