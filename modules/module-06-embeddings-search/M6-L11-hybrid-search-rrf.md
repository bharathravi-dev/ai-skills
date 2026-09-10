# M6-L11 — Hybrid Search and Reciprocal Rank Fusion

| | |
|---|---|
| **Lesson ID** | M6-L11 |
| **Difficulty** | 2 (Intermediate) |
| **Estimated study time** | 2.0 hours |
| **Prerequisites** | [M6-L04](M6-L04-dense-vs-sparse.md) |

---

## 1. Learning objectives

1. **Explain** why BM25 scores and cosine similarity scores cannot simply be added together to produce a
   combined ranking.
2. **Compute** a reciprocal rank fusion (RRF) score by hand from two rankings.
3. **Explain** why RRF fuses on rank position rather than on raw score, and what problem that choice
   solves.
4. **Evaluate** the effect of RRF's `k` parameter on how sharply it distinguishes ranked documents at a
   given corpus scale.
5. **Recognize**, from a genuine worked example, both what hybrid search reliably fixes and the limits of
   a small demonstration corpus in showing it.

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **Hybrid search** | Combining sparse (e.g. BM25) and dense (embedding) retrieval into a single ranking. |
| **Score-scale incompatibility** | The fact that two scoring methods' raw numbers are not comparable in range or meaning, making direct arithmetic combination unsound. |
| **Reciprocal rank fusion (RRF)** | A method for combining multiple rankings by summing `1 / (k + rank)` for each document across all rankings, using rank position only. |
| **RRF constant (k)** | A tunable constant in the RRF formula that controls how sharply differences between ranks are preserved or flattened. |
| **Rank-pair swap** | A case where two documents hold the same pair of ranks across two ranking methods, but with the methods exchanged — producing identical fused scores under RRF. |

---

## 3. Plain-language explanation

### 3.1 M6-L03 and M6-L04 built two separate rankers; this lesson combines them

M6-L03 built BM25, a sparse, exact-term ranker. M6-L04 compared it against dense, embedding-based
retrieval. Neither lesson combined the two into a single ranking — this lesson does, and specifically
addresses the one question that makes combining them non-trivial: *combining how, exactly?*

### 3.2 The obvious approach — add the scores — does not work

BM25 scores and cosine similarity scores are both "just numbers," which makes adding them together look
reasonable. §7.1 shows concretely why it isn't: the two scores occupy different ranges and mean different
things at any given value, so the sum is dominated by whichever method happens to produce larger raw
numbers for a given query — a fact about the method's scale, not about relevance.

### 3.3 The fix: fuse ranks, not scores

Reciprocal rank fusion sidesteps the entire scale problem by throwing away raw scores immediately and
working only with each document's rank position in each ranking. A rank of 1 means the same thing — "the
best match, by that method" — regardless of whether it came from a BM25 score of 12.4 or a cosine score of
0.31. §7.2 computes this by hand.

### 3.4 The `k` constant is a real tuning parameter, not a fixed rule

§7.2 also shows something easy to miss if you only ever see RRF's textbook default (`k = 60`) presented as
a constant: on a small ranking, a large `k` can nearly erase the difference between the best and worst
documents. `k` needs to be sized relative to how many results you actually expect to distinguish.

### 3.5 A genuine worked example, including its honest limits

§7.3 extends the corpus with a paraphrase document that shares no literal words with the query at all —
the exact case hybrid search is meant to help with. The result is real and instructive, but the lesson
does not overstate it: on this small, six-document corpus, the paraphrase document ties with an unrelated
one in the final fused ranking, for a specific, explainable reason. What the example does show cleanly is
the correct underlying mechanism — the reason hybrid search helps at real scale, even though this toy
corpus is too small to show the rank-lifting benefit directly.

---

## 4. Analogy

**Two judges scoring a competition on different scales.** One judge scores out of 10, giving mostly 6s,
7s, and 8s. The other scores out of 100, giving mostly 40s, 60s, and 90s. If you simply add their scores,
the second judge's opinion dominates every total — not because that judge is more discerning, but because
their numbers are bigger. The fix or ganizers actually use: ask each judge only for their *ranking* of the
competitors (1st, 2nd, 3rd...), then combine the rankings. A 1st-place vote means the same thing from
either judge, no matter how differently each of them scores internally.

### Where the analogy breaks

- **Human judges' rankings are already sensible on their own.** BM25 and dense rankings can each contain
  real, useful information even where they disagree sharply (§7.1) — the point of fusing them is to
  combine two different, partially-correct views, not to average out noise.
- **A panel of judges doesn't have a tunable "k" changing how much 1st place is worth versus 10th.** RRF's
  `k` constant is a real, corpus-size-dependent choice (§7.2), with no equivalent in the judging analogy.

---

## 5. Detailed technical explanation

### 5.1 Why raw scores cannot be added directly

`[REAL]` §7.1 computed BM25 and cosine scores for the same five-document corpus and query, then compared
three rankings: BM25 alone, cosine alone, and naive-sum. The naive-sum ranking did not match the
BM25-alone ranking, even though BM25 clearly identified the best match — because the sum let whichever
score had the larger typical magnitude quietly steer the result.

### 5.2 Reciprocal rank fusion, computed by hand

For a document with rank $r$ under some ranking method, RRF assigns it a contribution of:

$$\frac{1}{k + r}$$

summed across every ranking method the document appears in. A document ranked 1st under both BM25 and
dense search gets the largest possible combined score; a document missing from a ranking entirely
contributes nothing from that method.

`[REAL]` §7.2 computed this directly: rank 1 under a method with `k = 60` contributes `1/61 ≈ 0.0164`;
rank 5 contributes `1/65 ≈ 0.0154`. These numbers are close together — deliberately, as §5.3 explains.

### 5.3 The `k` constant controls how sharply rank matters

`[REAL]` §7.2's k-sensitivity table swept `k` across 1, 5, 20, and 60 on the same six-document corpus,
comparing the best-ranked document (D1) against the worst (D4):

| k | D1 score | D4 score | ratio D1 / D4 |
|---|---|---|---|
| 1 | 1.00000 | 0.33333 | 3.00 |
| 5 | 0.33333 | 0.20000 | 1.67 |
| 20 | 0.09524 | 0.08000 | 1.19 |
| 60 | 0.03279 | 0.03077 | 1.07 |

**A small `k` preserves large differences between top and bottom ranks; a large `k` compresses them.**
`k = 60` is a commonly cited default in RRF literature, but it was chosen with corpora of thousands of
results in mind, where the gap between rank 1 and rank 50 still matters at that scale. On six documents,
the same `k` leaves the best and worst results scoring within 7% of each other. `[UNVERIFIED — confirm a
sensible k for your own corpus size and ranking depth before using RRF for real.]`

### 5.4 A genuine hybrid-search demonstration, read honestly

`[REAL]` §7.3 added a sixth document — a paraphrase of "refund" using the word "reimbursement," sharing no
literal word with the query at all — and computed both rankings again:

| doc | BM25 score | BM25 rank | cosine score | dense rank |
|---|---|---|---|---|
| D6 (paraphrase) | 0.0000 | 6 | 0.7071 | 5 |

BM25 gives D6 a score of exactly zero: it cannot match a document with which it shares no literal term,
full stop. Dense search gives D6 a real, non-zero score — in fact, the *same* score as two other
genuinely relevant documents, because all three point in exactly the same direction in the (small,
hand-built) vector space. This is not a coincidence or a bug; it is dense retrieval correctly recognizing
that "reimbursement" and "refund" mean the same thing here.

Fusing both rankings with `k = 2` (sized to this corpus's depth, per §5.3) produced a fused ranking in
which **D6 ties exactly with D4, a fully irrelevant document** — because D4 is (BM25 rank 5, dense rank 6)
and D6 is (BM25 rank 6, dense rank 5): the same pair of ranks, swapped between methods, and RRF sums
symmetrically across methods, so the totals come out identical.

**Read this honestly, not as a clean win.** A six-document corpus is too small, with too few genuine
degrees of partial relevance, to show hybrid search lifting a document ranked last-by-one-method clear of
an unrelated document. What the corpus *does* show cleanly is the upstream cause that reliably produces
that lift at real scale: BM25 assigns paraphrases a flat, uninformative zero, while dense retrieval assigns
them a real, meaningful, non-zero score. At production scale — thousands of documents, many genuine shades
of partial relevance, no artificial ties — that signal difference is what pulls a paraphrase up from
unreachable toward findable, even though this toy example's final rank does not demonstrate the lift
directly.

### 5.5 Assumptions and limitations

- §7.1–§7.3's cosine scores use M6-L01/M6-L02's small, hand-built word vectors, not a real trained
  embedding model. The BM25 and RRF formulas are exact; the specific dense scores are an illustration.
- The `k = 2` used in §7.3 was chosen to fit this six-document toy corpus, following §5.3's own finding —
  it is not a value to reuse at production scale, where `k = 60` (or another value sized to that corpus)
  is the relevant starting point.
- This lesson does not cover reranking a fused or retrieved list with a second, more expensive model —
  that is M6-L12's topic, immediately following this one.

---

## 6. Worked example — the search team that tuned the wrong number

**The system.** A support-ticket search feature combines BM25 and dense retrieval. Early testing on a
handful of example queries showed the fused ranking working well, so the team shipped it with the textbook
default `k = 60` and moved on.

**What went wrong.** Months later, an internal review found that fused rankings for niche queries — ones
returning only a handful of plausible results from a small filtered subset of tickets — looked barely
different from BM25 alone. The dense signal seemed to be contributing almost nothing for exactly the
queries where combining both methods should have mattered most.

**Why it happened.** `k = 60` is sized for rankings with hundreds or thousands of candidates, where the
difference between rank 1 and rank 50 remains meaningful. On a filtered subset returning only five or six
plausible results — precisely the small-corpus regime §7.2 measured — a `k` that large compresses nearly
all rank differences into a narrow band, so the fusion step contributes little beyond whichever method
happened to rank the top result first.

**Three defects:**

| # | Defect | Consequence |
|---|---|---|
| 1 | `k` was copied from a textbook default without checking it against actual ranking depth | Fusion barely distinguished documents on small, filtered result sets |
| 2 | Testing only covered queries against the full, large corpus | The small-result-set regime was never observed during evaluation |
| 3 | No one measured RRF's own score spread at the depths the system actually served | The problem was invisible until someone happened to compare scores directly |

### The fix

**Size `k` to the ranking depth actually being fused**, per §5.3 — a single global `k` is not necessarily
correct across every query shape a system serves, especially when result sets vary widely in size.

**Test fusion behavior at the smallest realistic result-set size**, not only against the full corpus —
§7.2's finding that small corpora need a smaller `k` applies exactly as much to a filtered subset of a
large corpus as to a small corpus outright.

**Inspect RRF scores directly when a fusion result looks suspicious**, the same way §7.3 did — a fused
ranking that looks like "basically just BM25" is a legitimate signal to check whether `k` is silently
flattening the dense contribution.

**The general rule.** **RRF removes the scale-incompatibility problem (§5.1) but introduces its own
tunable parameter, and that parameter is not scale-free** — it must be checked against the actual depth of
the rankings being fused, not copied from a default chosen for a different scale.

---

## 7. Practical activity

**File:** [`labs/m6/l11_hybrid_rrf.py`](../../labs/m6/l11_hybrid_rrf.py)

**No API key, no network.** Runs in well under a second — every computation is by-hand-scale arithmetic.

```bash
source .venv/bin/activate
python labs/m6/l11_hybrid_rrf.py
```

### 7.2 Expected output

`[EXECUTED]` — 2026-09-10, Python 3.10.11, NumPy 2.2.6.

```text
============================================================================
1. WHY YOU CANNOT JUST ADD BM25 AND COSINE SCORES
============================================================================
  Query: ['refund', 'damaged']

  doc    BM25 score  cosine score
  D1         1.5494        0.9728
  D2         0.5904        0.7071
  D3         0.8884        0.7894
  D4         0.0000        0.0000
  D5         0.8971        0.7071

  Naive sum (BM25 + cosine): {'D1': 2.522, 'D2': 1.298, 'D3': 1.678, 'D4': 0.0, 'D5': 1.604}
  Ranked by naive sum: ['D1', 'D3', 'D5', 'D2', 'D4']
  Ranked by BM25 alone: ['D1', 'D5', 'D3', 'D2', 'D4']

  BM25 scores here range roughly 0-1.5+; cosine scores range 0-1 but
  mean something entirely different at any given value. Adding them
  directly lets whichever method happens to produce larger raw
  numbers dominate the fused ranking -- not because it is more
  relevant, but because its SCALE is bigger. Compare the naive-sum
  ranking to BM25 alone: notice they are not even in the same order,
  for reasons that have nothing to do with relevance.

============================================================================
2. RECIPROCAL RANK FUSION: FUSE RANKS, NOT SCORES
============================================================================
  BM25 ranking:  ['D1', 'D5', 'D3', 'D2', 'D4']
  Dense ranking: ['D1', 'D3', 'D2', 'D5', 'D4']

  RRF score for each document: sum over methods of 1/(k + rank), k=60

  doc    BM25 rank  dense rank   RRF score
  D1             1           1     0.03279
  D2             4           3     0.03150
  D3             3           2     0.03200
  D4             5           5     0.03077
  D5             2           4     0.03175

  Fused ranking (RRF): ['D1', 'D3', 'D5', 'D2', 'D4']

  RRF never looks at the raw BM25 or cosine VALUE -- only each
  document's POSITION in each ranking. This sidesteps the entire
  scale-incompatibility problem from section 1: a rank of 1 means
  the same thing (the best match, by that method) whether it came
  from a BM25 score of 12.4 or a cosine score of 0.31.

  A note on k=60: it is a commonly cited default, but it was
  chosen for corpora with thousands of results, where the difference
  between rank 1 and rank 50 still matters at that scale. On a
  6-document toy corpus, a large k nearly ERASES rank differences:
       k    D1 score   D4 score (worst on both)   ratio D1/D4
       1     1.00000                    0.33333          3.00
       5     0.33333                    0.20000          1.67
      20     0.09524                    0.08000          1.19
      60     0.03279                    0.03077          1.07

  At k=60, the best and worst documents in this tiny corpus score
  within a few percent of each other -- k must be sized relative to
  how many results you actually expect to distinguish, not treated
  as a universal constant. [UNVERIFIED -- confirm a sensible k for
  your own corpus size and ranking depth before using RRF for real.]

============================================================================
3. HYBRID SEARCH RECOVERING BOTH KINDS OF MATCH
============================================================================
  D6 (new): 'we issued a full reimbursement to you today' -- a paraphrase of 'refund' using
  'reimbursement', with NO literal query term present at all.

  doc    BM25 score  BM25 rank  cosine score  dense rank
  D1         1.9224          1        0.9728           1
  D2         0.7735          4        0.7071           3
  D3         1.0665          3        0.7894           2
  D4         0.0000          5        0.0000           6
  D5         1.1684          2        0.7071           4
  D6         0.0000          6        0.7071           5

  BM25 gives D6 a score of EXACTLY 0.0 -- it shares not one literal
  word with the query, so it cannot be found at all by keyword
  matching, no matter how relevant it actually is.

  Dense gives D6 the SAME cosine score as D2 and D5 (0.7071, exactly).
  This is not a coincidence or a tie-break artifact: D6, D2 and D5 all
  point in exactly the same direction in this toy space -- purely
  the 'refund' concept, with no 'damaged' concept at all -- so a
  query half-way between the two concepts is equally close to all
  three, REGARDLESS of which literal words produced each vector.
  Dense search has correctly recognised that a sentence about a
  'reimbursement' is conceptually equivalent to one about a
  'refund' -- exactly the semantic-gap-bridging M6-L01 promised,
  now demonstrated on a query BM25 could not match to D6 at all.

  Following section 2's finding, k=60 would nearly erase rank
  differences on this 6-document corpus. Using k=2, sized to
  this corpus's actual depth, instead:

  Fused (RRF, k=2) ranking: ['D1', 'D3', 'D5', 'D2', 'D4', 'D6']
  D4 RRF score: 0.2679  |  D6 RRF score: 0.2679
  D1's position in the fused ranking: 1 of 6 (the exact-match document, still ranked first)

  Read this honestly: D6 still lands LAST, tied exactly with D4 --
  a document matching NEITHER query concept at all. This is not a
  failure of the method to notice; it is what the arithmetic
  actually produces here. D4 is (BM25 rank 5, dense rank 6) and D6
  is (BM25 rank 6, dense rank 5) -- the same PAIR of ranks, swapped
  between methods, and RRF sums across methods symmetrically, so the
  two totals come out identical. A six-document toy corpus is simply
  too small, with too few genuine degrees of partial relevance, to
  show hybrid search lifting a rank-6-on-one-method document clear
  of an unrelated one. What the toy corpus DOES show cleanly is the
  upstream fact that makes hybrid search worth using at real scale:
  BM25 assigned D6 a flat, uninformative 0, while dense assigned it
  a real, meaningful, non-zero relevance score identical to known
  partial matches. At production scale -- thousands of documents,
  many genuine shades of partial relevance, no artificial ties --
  that same underlying signal is what reliably pulls a paraphrase
  like D6 up from unreachable toward findable, even though this
  toy example's fused RANK does not demonstrate it directly.

============================================================================
4. WHAT THIS LAB IS AND IS NOT
============================================================================
  REAL: every BM25 score is M6-L03's exact formula; every RRF score
  is the exact, standard formula, computed precisely on stated ranks.

  ILLUSTRATIVE: the dense/cosine scores use M6-L01/M6-L02's small,
  hand-built word vectors, not a real trained embedding model -- the
  MECHANISM (semantic similarity beyond shared words) is real; the
  specific numbers are a checkable illustration, not a benchmark.

  A NOTE ON k=60: this is a commonly cited default in RRF
  literature, not a universal constant. [UNVERIFIED -- the right
  value can depend on your ranking depth and corpus; test your own.]

  NOT SHOWN: reranking a fused or retrieved list with a second,
  more expensive model (cross-encoder reranking, M6-L12), which is
  the next, complementary technique in this module.

Done.
```

### 7.3 Reading the result

**Section 1 is the whole argument for RRF, before RRF ever appears.** The naive-sum ranking disagreeing
with BM25-alone is not a subtle effect — it is a direct, visible consequence of adding numbers that mean
different things at different scales.

**Section 2's k-sensitivity table is the lesson's most easily-missed finding.** It would be simple to
present RRF with `k = 60` as if it were parameter-free, the way the formula itself is often written. The
measured ratio dropping from 3.00 (`k=1`) to 1.07 (`k=60`) on this corpus makes concrete exactly how much a
"default" constant can flatten a ranking at the wrong scale.

**Section 3 is deliberately not a clean success story, and that is the point.** It would have been easy to
adjust the toy corpus further until D6 clearly outranked D4 in the final fusion — but the actual, honest
result (an exact tie, for an explainable structural reason) teaches something more durable: what hybrid
search *reliably* fixes is the upstream signal (a real score instead of a hard zero), not a guarantee that
any given small example will show a clean rank improvement. The mechanism is real; the toy scale's
particular outcome is a demonstration of the mechanism's cause, not of its full downstream effect.

---

## 8. Common mistakes and troubleshooting

1. **Adding BM25 and cosine scores directly.** §7.1 — the two scales are not comparable, and the sum is
   dominated by whichever method's raw numbers happen to be larger.
2. **Treating `k = 60` as a fixed, universal constant.** §7.2 — it is a default sized for large result
   sets; a small ranking needs a smaller `k`, or rank differences nearly vanish.
3. **Assuming a fused ranking's improvement will always be visible on a small or hand-picked example.**
   §7.3 — the underlying signal can be genuinely fixed (BM25's zero vs. dense's real score) without a tiny
   example's final rank order visibly showing it, for reasons specific to that example's scale.
4. **Concluding hybrid search "doesn't work" from a single small or synthetic test.** §7.3's honest
   reading — check the upstream per-method scores, not only the final fused rank, before drawing that
   conclusion.
5. **Forgetting that a document present in only one ranking still contributes to its RRF score.** A
   document entirely missing from BM25 (score 0, e.g. D6 in §7.3) still receives a real RRF contribution
   from its dense rank alone.
6. **Re-running RRF on raw scores instead of rank positions.** RRF's entire benefit depends on discarding
   raw scores immediately (§5.2) — feeding it scores instead of ranks reintroduces the exact problem it
   solves.

| Symptom | Likely cause | Fix |
|---|---|---|
| A fused ranking looks almost identical to one method alone | `k` too large for the actual ranking depth | Size `k` to the ranking depth actually being fused (§5.3, §6) |
| Combining two scoring methods produces a ranking that matches neither method well | Raw scores were added directly instead of fused by rank | Use RRF (or another rank-based fusion) instead of arithmetic combination (§5.1–§5.2) |
| A "hybrid search improvement" test shows no visible ranking change | Corpus or example too small to show the effect at the final-rank level | Inspect per-method scores directly (§7.3); verify the underlying signal, not only the final order |
| Two documents receive an identical RRF score | Their ranks form the same pair, swapped between methods — a real, explainable RRF property, not a bug | Confirm by checking each document's rank under each method directly (§5.4) |

---

## 9. Security, privacy, reliability, cost

- **Reliability.** Never combine BM25 and dense scores by direct arithmetic — use a rank-based fusion
  method (RRF or equivalent), since raw-score combination is dominated by scale, not relevance (§5.1).
- **Reliability.** Treat RRF's `k` as a parameter to check against your own ranking depth, not a constant
  to copy from a default — an unchecked default sized for a different scale can silently flatten a fused
  ranking (§5.3, §6).
- **Reliability.** When validating a hybrid-search change, inspect per-method scores directly on cases that
  matter, not only the final fused order — a genuinely fixed upstream signal can still produce a
  same-looking (or tied) final rank on a small enough test case (§5.4, §7.3).
- **Cost.** RRF itself adds negligible computational cost over running both retrieval methods
  independently — the fusion step is a simple weighted sum over rank positions, not an additional model
  call.

---

## 10. Exercises

### Exercise 1 — Beginner (~20 min)

1. In one sentence, why can't BM25 and cosine scores simply be added together?
2. What does RRF use instead of raw scores, and why does that solve the scale problem?
3. Using `k = 60`, what does a document ranked 3rd by one method contribute to its RRF score from that
   method? Show the arithmetic.
4. Why did a large `k` value nearly erase rank differences on the lab's six-document corpus?
5. In your own words, what did the D6 (paraphrase) example in §7.3 actually demonstrate, and what did it
   *not* demonstrate?

### Exercise 2 — Intermediate (~40 min)

1. Run the lab. Confirm section 1's naive-sum ranking mismatch and section 2's RRF scores by hand for at
   least two documents.
2. Reproduce the k-sensitivity table for a value of `k` not shown in the lab (e.g. `k = 10`) and confirm
   where it falls relative to the existing rows.
3. Add a seventh document to the corpus that is a closer paraphrase than D6 (sharing zero literal terms
   but pointing more directly along the query's exact direction) and report whether it breaks D6's tie
   with D4.
4. Using the lab's BM25 and dense scores for the five-document corpus (§7.1), compute the RRF-fused
   ranking by hand for `k = 10` and compare it to the lab's own `k = 60` result.
5. Explain, using §5.4's rank-pair argument, why two documents can receive an identical RRF score across
   exactly two ranking methods, and describe a general condition under which this happens.

### Exercise 3 — Challenge (~50 min)

1. Extend the lab to fuse three ranking methods at once (e.g. BM25, dense, and a random baseline) and
   verify the RRF formula still applies with a straightforward sum across all three.
2. Using the k-sensitivity method from §5.3, write a short function that recommends a reasonable `k` given
   a corpus's typical result-list depth, and justify the heuristic you choose.
3. Design and run an experiment on a larger, more realistic synthetic corpus (e.g. reusing M6-L06's
   topic-cluster generation approach) that demonstrates hybrid search producing a clean rank improvement
   for a paraphrase-style document — one not undermined by the small-corpus tie this lesson found.
4. Research (conceptually) at least one alternative to RRF for combining rankings, and compare its
   assumptions and trade-offs against RRF's rank-only approach.
5. Using this lesson's honest reporting of the D4/D6 tie as a model, write a short "what this experiment
   does and does not show" section for a hypothetical hybrid-search evaluation you might run at work.

---

## 11. Quiz

*(Answers: [`answer-keys/module-06-answers.md`](../../answer-keys/module-06-answers.md#m6-l11).)*

**Q1.** Why can't BM25 scores and cosine similarity scores simply be added together to produce a fused
ranking, per §7.1?

- A. BM25 cannot be computed on the same documents that cosine similarity is computed on.
- B. The two scores live on different scales and mean different things at any given value, so whichever one happens to produce larger raw numbers dominates the sum for reasons unrelated to relevance.
- C. Cosine similarity can only be computed once per query, never once per document.
- D. Adding scores together requires the corpus to contain an even number of documents.

**Q2.** Reciprocal rank fusion (RRF) fuses two rankings by:

- A. Using only each document's rank position in each ranking, ignoring the underlying raw scores entirely.
- B. Averaging the raw BM25 and cosine scores after rescaling both to [0, 1].
- C. Selecting whichever single method produced the higher top score.
- D. Re-running BM25 on the dense ranking's top result only.

**Q3.** Using RRF's formula `1 / (k + rank)` with `k = 60`, a document ranked #1 by a given method
contributes:

- A. 1.0 to its RRF score from that method.
- B. 0 to its RRF score from that method.
- C. 1/61 ≈ 0.0164 to its RRF score from that method.
- D. 60 to its RRF score from that method.

**Q4.** §7.2's k-sensitivity table (k = 1, 5, 20, 60) on the six-document toy corpus showed that:

- A. Changing k had no measurable effect on any RRF score.
- B. Only k = 60 produced a valid ranking; all other values of k were invalid.
- C. Smaller k values always produce a different final ranking order than larger k values.
- D. At k = 60, the best- and worst-scoring documents came out within a few percent of each other — a large k nearly erased rank differences on a corpus this small.

**Q5.** The practical lesson from the k-sensitivity finding (§7.2) is:

- A. k should be sized relative to how many results you actually expect to distinguish (ranking depth), not treated as a fixed, universal constant.
- B. k = 60 is mandatory and should never be changed regardless of corpus size.
- C. k only affects BM25 scores, never dense scores.
- D. k should always be set equal to the number of documents in the corpus.

**Q6.** In §7.3, BM25 assigned the paraphrase document D6 ("we issued a full reimbursement to you today")
a score of exactly 0.0 because:

- A. D6 was accidentally excluded from the corpus passed to the BM25 function.
- B. D6's document length exceeded BM25's length-normalization limit.
- C. D6 shares no literal term with the query ("refund", "damaged") at all, and BM25 can only score documents containing at least one query term.
- D. BM25 scores are always 0 for the sixth document added to any corpus.

**Q7.** In §7.3, dense/cosine search gave D6 the exact same score (0.7071) as D2 and D5. The lesson
explains this as:

- A. A floating-point rounding bug that should be fixed before trusting the result.
- B. A genuine mathematical property: D2, D5, and D6 all point in exactly the same direction in the toy vector space (the "refund" concept with no "damaged" component), so a query between the two concepts is equidistant from all three regardless of wording.
- C. An artifact of using cosine similarity instead of Euclidean distance.
- D. Proof that dense search cannot distinguish between any two documents in this lab.

**Q8.** In the final RRF-fused ranking (k = 2) over the extended six-document corpus, D4 (an irrelevant
document) and D6 (the paraphrase document) ended up:

- A. With D6 clearly ranked above D4, demonstrating hybrid search rescuing the paraphrase.
- B. With D4 clearly ranked above D6, showing hybrid search failed on this example.
- C. Both excluded from the fused ranking entirely.
- D. Exactly tied, because D4 and D6 have the same pair of ranks (one from each method) simply swapped between methods, and RRF sums contributions across methods symmetrically.

**Q9.** Given that D6 tied with an irrelevant document rather than clearly outranking it, the lesson's
honest conclusion is:

- A. This six-document toy corpus is too small to demonstrate rank-lifting directly, but the upstream signal difference it does show — BM25 scoring D6 a flat 0 versus dense assigning it a real, meaningful score — is the actual mechanism that reliably lifts such documents at real, production scale.
- B. The experiment failed and should be discarded because hybrid search did not work.
- C. RRF is a flawed technique that should never be used with k values below 60.
- D. Paraphrased documents can never be retrieved by any combination of BM25 and dense search.

**Q10.** This lesson's hybrid fusion approach relates to M6-L01/M6-L02 (dense embeddings) and M6-L03
(BM25) by:

- A. Replacing both prior methods with a single, simpler scoring formula.
- B. Showing that BM25 alone is always sufficient, making dense retrieval unnecessary.
- C. Combining both previously-established retrieval methods through a principled rank-based fusion, rather than an ad hoc combination of their raw scores.
- D. Proving that dense retrieval and BM25 always agree on document ranking.

**Q11.** Per §7.4 ("what this lab is and is not"), which part of this lab is explicitly labeled
illustrative rather than real?

- A. The RRF formula and its computed scores.
- B. The hand-built word vectors used to compute cosine similarity, standing in for a real trained embedding model.
- C. The BM25 formula and its computed scores.
- D. The document ranking order produced by sorting scores.

**Q12.** The general practical rule this lesson establishes for combining sparse and dense retrieval is:

- A. Always trust whichever method produces the higher raw score.
- B. Rescale both methods' raw scores to the same range and average them.
- C. Use BM25 alone whenever the query contains any literal keyword.
- D. Fuse rankings by rank position (e.g. via RRF), not by combining raw scores directly, since ranks are comparable across methods in a way raw scores are not.

**Q13.** *(Written, rubric-graded.)* In under 150 words: explain why hybrid search (BM25 fused with dense
retrieval via RRF) can recover documents that neither pure BM25 nor pure dense search would rank highly
alone — referencing the specific mechanism this lesson demonstrated, not just "it combines both."

---

## 12. Revision notes

- **BM25 and cosine scores cannot be added directly** — they occupy different, incompatible scales, and a
  naive sum is dominated by whichever method's raw numbers are larger, for reasons unrelated to relevance.
  Measured: the naive-sum ranking diverged from the BM25-alone ranking on the same five-document corpus.
- **Reciprocal rank fusion solves this by discarding raw scores and fusing only rank positions** — a rank
  of 1 means the same thing regardless of which method or scale produced it.
- **RRF's `k` constant is a real, scale-sensitive tuning parameter, not a fixed universal default.**
  Measured: the ratio between the best and worst document's RRF score shrank from 3.00 (`k=1`) to 1.07
  (`k=60`) on a six-document corpus — `k=60` is sized for corpora far larger than this lab's toy example.
- **A paraphrase document with zero literal query-term overlap scores exactly 0 under BM25**, but receives
  a real, non-zero, meaningful score under dense retrieval — the concrete signal difference hybrid search
  is built to exploit.
- **A small toy corpus can produce a genuine tie in the final fused ranking**, even when the underlying
  signal difference is real — reported honestly here rather than adjusted away, because the tie itself
  has an explainable, structural cause (a rank-pair swapped symmetrically between two methods).
- **The valid, general finding is the upstream signal difference, not a guarantee of visible rank-lift on
  any specific small example** — the mechanism that helps at production scale is real even where a toy
  corpus is too small to show its downstream effect on final rank order.

---

## 13. Completion checklist

- [ ] I can explain why BM25 and cosine scores cannot be combined by direct arithmetic.
- [ ] I can compute an RRF score by hand from two documents' ranks under two methods.
- [ ] I understand why RRF discards raw scores and works only with rank position.
- [ ] I can explain how the `k` constant affects how sharply RRF distinguishes ranks, and why it must be
      sized to ranking depth.
- [ ] I can describe what the paraphrase-document example in this lesson does and does not demonstrate.
- [ ] I know to inspect per-method scores directly, not just a final fused rank, when validating a hybrid
      search change.
- [ ] I scored 10/13 on the quiz.

---

## 14. References

- Cormack, G., Clarke, C., Buettcher, S., *Reciprocal Rank Fusion Outperforms Condorcet and Individual
  Rank Learning Methods*, SIGIR 2009 (the original RRF paper). `[UNVERIFIED]`
- Elasticsearch documentation, *Reciprocal rank fusion*. <https://www.elastic.co/guide/en/elasticsearch/reference/current/rrf.html> `[UNVERIFIED]`

---

## 15. Next lesson

→ [M6-L12 — Cross-Encoder Reranking](M6-L12-cross-encoder-reranking.md)

You now have a principled way to combine sparse and dense retrieval into one ranking. Next: a
complementary, more expensive technique — reranking a retrieved or fused shortlist with a cross-encoder
model that scores each query-document pair jointly, rather than comparing precomputed vectors.
