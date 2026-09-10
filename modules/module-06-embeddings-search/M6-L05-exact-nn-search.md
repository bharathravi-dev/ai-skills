# M6-L05 — Exact Nearest-Neighbour Search and Its Cost

| | |
|---|---|
| **Lesson ID** | M6-L05 |
| **Difficulty** | 2 (Intermediate) |
| **Estimated study time** | 1.75 hours |
| **Prerequisites** | [M6-L02](M6-L02-embedding-dimensions.md) |

---

## 1. Learning objectives

1. **Implement** exact nearest-neighbour search and explain why it must compare the query against every
   vector.
2. **Measure** real query time as corpus size grows, and confirm it scales linearly.
3. **Measure** real query time as dimension count grows, and combine both into one cost model.
4. **Extrapolate** measured costs to determine the corpus size at which exact search stops meeting a
   stated latency budget.
5. **Explain** why exact search remains necessary even after faster methods exist, as the reference
   standard M6-L06 measures against.

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **Exact nearest-neighbour (NN) search** | Computing similarity against every vector in the corpus and returning the true best matches. |
| **Brute-force search / linear scan** | The implementation of exact search — checking every vector, with no shortcuts. |
| **Query time / query latency** | The time taken to answer one search request. |
| **Linear scaling (O(N))** | Cost growing directly proportional to corpus size. |
| **Ground truth (retrieval)** | The true, exact top-k result, used as the reference for measuring an approximate method's accuracy. |
| **Latency budget** | The maximum acceptable time for a system to respond. |
| **Crossover point** | The scale at which one approach stops meeting a requirement that a different approach still meets. |

---

## 3. Plain-language explanation

### 3.1 The simplest correct algorithm there is

Given a query vector and a corpus, the only way to **guarantee** finding the true best matches is to
compare the query against **every single vector** and keep the top few. There is no shortcut that
preserves this guarantee — skipping even one vector means you might have skipped the best match. §7.1
shows the entire algorithm in a few lines, on a corpus small enough to check by eye.

### 3.2 "Simple" and "cheap" are not the same claim

Exact search is conceptually trivial and computationally expensive at scale. Every additional vector in
the corpus is one more comparison, for **every** query. §7.2 measures this directly, with real wall-clock
timing, not an estimate: a 1,000× larger corpus costs roughly 1,000× more time per query.

### 3.3 Dimension count is a second, independent cost

M6-L02 priced dimensions in storage. This lesson prices them in **query time**: each dimension adds one
more multiplication per vector comparison, and that cost is paid on every single vector, every single
query. §7.3 measures this as a second, separate scaling factor.

### 3.4 The two costs multiply, and that tells you exactly when to stop using exact search

Combine linear-in-corpus-size and linear-in-dimensions, and exact search's total cost is proportional to
`N × d`. That is not an abstract fact — §7.4 turns it into a specific number: the corpus size at which a
stated latency budget stops being achievable at all with exact search, on this lesson's measured
hardware.

---

## 4. Analogy

**Checking every locker in a building by hand versus consulting a directory.** If you must guarantee
finding a specific item and have no directory, opening every locker in sequence is the only method that
cannot miss it. It also gets slower, in direct proportion, with every locker the building adds — a
building twice the size takes twice as long to search completely, no matter how efficiently you open each
locker.

A directory (the subject of M6-L06) lets you skip almost every locker, at the cost of trusting that the
directory itself is accurate and complete — usually true, but not a guarantee the way opening every
locker is.

### Where the analogy breaks

- **A physical locker search's cost is obvious from watching it happen.** A software system's linear
  cost is invisible until specifically measured (§7.2) — nothing about a slow query "looks" like it is
  scaling badly until you plot several sizes against each other.
- **A directory for lockers is built once and rarely wrong.** An approximate search index (M6-L06) has an
  explicit, measurable, and tunable accuracy trade-off — it is not simply "a faster version of the same
  guarantee."
- **You would never build a directory for ten lockers.** Exact search is not just acceptable but
  *preferable* at small scale (§7.4's crossover point) — the faster method only starts paying for its
  added complexity above a specific, computable size.

---

## 5. Detailed technical explanation

### 5.1 The algorithm and its cost, in one formula

`[REAL]` Exact search, vectorised:

```python
def exact_top_k(query, corpus, k):
    scores = corpus @ query                      # one dot product per row
    top_idx = np.argpartition(-scores, k)[:k]
    return top_idx[np.argsort(-scores[top_idx])]
```

Every call touches every row of `corpus`. §7.2 measured this directly:

| Corpus size (N) | Query time | vs N=1,000 |
|---|---|---|
| 1,000 | 0.07ms | 1.0× |
| 100,000 | 5.55ms | 76.9× |
| **1,000,000** | **52.38ms** | **725.8×** |

**A 1,000× larger corpus costs roughly 726× more time** — close to exactly proportional, confirming the
algorithm's cost is **linear in corpus size**. Per-vector cost stayed close to constant (52–72
nanoseconds) across every corpus size tested, which is exactly what "linear" means in practice: the
*rate* doesn't change, only the *total*, proportional to how many vectors there are.

### 5.2 Dimension count multiplies the same cost

`[REAL]` §7.3 held corpus size fixed and varied dimension count:

| Dimensions | Query time | vs 128 dims |
|---|---|---|
| 128 | 4.82ms | 1.0× |
| 768 | 21.96ms | 4.6× |
| **3,072** | **100.90ms** | **20.9×** |

**More dimensions cost more time, roughly in proportion** — every additional dimension is one more
multiplication, repeated across every vector in the corpus. Combined with §5.1, **exact search's total
cost per query is proportional to `N × d`** — corpus size times dimension count. Doubling either one
roughly doubles query time; doubling both roughly quadruples it.

### 5.3 Turning the measurement into a decision

`[REAL, machine-specific]` §7.4 extrapolated this run's measured rate (52.4 nanoseconds per vector, at
384 dimensions) to real production scales:

| Corpus size | Estimated query time |
|---|---|
| 1,000,000 | 52.4ms |
| 10,000,000 | 523.8ms |
| **100,000,000** | **5,237.6ms** |

**At a 100ms latency budget, this run's measured rate implies exact search stops fitting somewhere
around 1.9 million vectors.** A production RAG or search system with tens or hundreds of millions of
vectors — an entirely ordinary scale — sits one to three orders of magnitude past that point. **This is
the exact, quantified argument for M6-L06's approximate methods**: not that exact search is incorrect,
but that guaranteeing correctness by checking every vector is, at this scale, mathematically
incompatible with a normal interactive latency budget.

### 5.4 Exact search does not retire once faster methods exist

Two roles survive every faster method M6-L06 introduces:

- **Small-scale search.** Below the crossover point in §5.3, exact search is not just acceptable — it is
  *preferable*, since it carries zero accuracy trade-off and no additional infrastructure.
- **Ground truth for evaluation.** An approximate method's whole value proposition is "close enough to
  exact, much faster." Measuring "close enough" requires knowing what exact search *would* have returned
  — exact search becomes the reference standard, not a discarded first draft (M6-L06's recall
  measurements depend on this directly).

### 5.5 Assumptions and limitations

- Every timing in this lesson is specific to the machine, numpy build, and load conditions present when
  it ran. `[EXECUTED, machine-specific — re-run on your own hardware before quoting a number elsewhere.]`
- §7.3's scaling was close to, but not perfectly, linear at small dimension counts — likely reflecting
  fixed per-call overhead and vectorisation efficiency effects rather than a violation of the underlying
  `O(d)` cost. The trend, not the exact ratios, is what should transfer.
- This lesson measures a single-query, single-threaded cost. Real systems often parallelise across
  queries or shard a corpus across machines — both change the *effective* cost profile without changing
  the fact that each shard still performs a linear scan internally.

---

## 6. Worked example — the search feature that worked in staging and crawled in production

**The system.** A team builds a document search feature. Staging tests use a corpus of 5,000 documents.
Query latency in staging: comfortably under 10ms, tested casually and never benchmarked formally.

**What happened at launch.** Production ingested the company's full document history — 40 million
documents. Query latency became several seconds per search. Users described the feature as "broken";
nothing had crashed.

**Why, exactly.** Staging's 5,000-document corpus was **8,000× smaller** than production's. Per §5.1's
measured linear scaling, an 8,000× larger corpus costs roughly 8,000× more query time — a query that took
a few milliseconds in staging was always going to take several seconds at production scale, using the
same exact-search code. **Nothing degraded or broke. The system did exactly what its algorithm's cost
model predicts, at a scale nobody had measured.**

**Three defects:**

| # | Defect | Consequence |
|---|---|---|
| 1 | Staging corpus was orders of magnitude smaller than production, with no scaling test | The linear cost relationship was never observed before launch |
| 2 | No stated latency budget existed anywhere in the project | There was no number to check the design against before committing to exact search |
| 3 | No crossover-point calculation was ever done (§5.3) | The team had no way to know in advance that production scale exceeded exact search's viable range |

### The fix

**Measure query time at more than one corpus size before launch**, per §7.2's method, and fit the
relationship rather than assuming staging behaviour holds at production scale.

**State a latency budget explicitly**, as a requirement, before choosing between exact and approximate
search — "fast enough" is not a specification until it has a number attached.

**Compute the crossover point (§5.3) for the actual target corpus size** before committing to an
architecture, the same way M6-L02 required computing storage cost before committing to a dimension count.

**The general rule.** **A cost that scales linearly is not a defect to discover in production — it is
predictable in advance, from a handful of measurements at smaller scale, exactly as this lesson's lab
does it.**

---

## 7. Practical activity

**File:** [`labs/m6/l05_exact_nn_search.py`](../../labs/m6/l05_exact_nn_search.py)

**No API key, no network.** Real timing, so results will vary by machine — expect the run to take
around 30 seconds.

```bash
source .venv/bin/activate
python labs/m6/l05_exact_nn_search.py
```

Sections 2–4 report actual measured wall-clock time on real vectorised numpy search, not simulated or
estimated figures.

### 7.2 Expected output

`[EXECUTED, machine-specific]` — 2026-09-09, Python 3.10.11, NumPy 2.2.6. **Timings are from the
machine that ran this; expect different numbers on yours — the shape is what to check, not the exact
milliseconds.**

```text
============================================================================
1. EXACT NEAREST-NEIGHBOUR SEARCH: THE ALGORITHM
============================================================================
  A 3-dimensional toy corpus and a query. Exact search means:
  compute similarity to EVERY vector, then keep the best k.

  doc  vector              cosine to query
  D1   [1.0, 0.0, 0.0]     1.0000
  D2   [0.9, 0.1, 0.0]     0.9939
  D3   [0.0, 1.0, 0.0]     0.0000
  D4   [0.0, 0.9, 0.1]     0.0000
  D5   [0.0, 0.0, 1.0]     0.0000

  Exact top-2: ['D1', 'D2']

  This is the ENTIRE algorithm: no shortcuts, no approximation. It
  is also the definition of 'correct' -- every faster method in this
  module (M6-L06 onward) is judged by how closely it matches what
  this brute-force scan would have found.

============================================================================
2. REAL TIMING: HOW SEARCH TIME GROWS WITH CORPUS SIZE
============================================================================
  Dimension fixed at 384, k=10. Real corpora of random unit
  vectors, real wall-clock time for ONE brute-force query (averaged over 5 runs):

   corpus size (N)    time/query   vs N=1,000   time/query/vector
             1,000       0.07ms         1.0x             72.2ns
            10,000       0.56ms         7.8x             56.1ns
           100,000       5.55ms        76.9x             55.5ns
           500,000      29.74ms       412.2x             59.5ns
         1,000,000      52.38ms       725.8x             52.4ns

  Time per query scales roughly LINEARLY with corpus size -- 1,000x
  more vectors costs roughly 1,000x more time, because every single
  vector must be compared against the query. There is no shortcut in
  this algorithm; correctness REQUIRES checking everything.

  [Timings are wall-clock on THIS machine, this run, and will differ
  on yours -- the near-linear SHAPE is the result that transfers,
  not the specific millisecond figures.]

============================================================================
3. REAL TIMING: HOW SEARCH TIME GROWS WITH DIMENSION COUNT
============================================================================
  Corpus size fixed at 200,000. Real timing as dimension count varies:

   dimensions    time/query   vs 128 dims
          128       4.82ms          1.0x
          384       9.61ms          2.0x
          768      21.96ms          4.6x
         1536      39.28ms          8.2x
         3072     100.90ms         20.9x

  Time also scales roughly linearly with dimension count -- each
  additional dimension is one more multiplication per vector, per
  query. Combined with section 2: exact search cost is O(N x d) per
  query. Both a bigger corpus AND a bigger embedding model make
  every single query more expensive, independently.

============================================================================
4. EXTRAPOLATING TO PRODUCTION SCALE
============================================================================
  Using this run's measured per-vector cost (52.4ns) at 384 dimensions:

     corpus size  estimated time/query
       1,000,000               52.4ms
      10,000,000              523.8ms
     100,000,000             5237.6ms
   1,000,000,000            52376.1ms

  At a 100ms latency budget, this measured rate implies exact
  search stops fitting the budget somewhere around 1,909,268 vectors.
  A production system with tens or hundreds of millions of vectors
  -- an entirely ordinary size for real search or RAG applications --
  is, on these numbers, one to three orders of magnitude past where
  exact search alone can meet a normal interactive latency budget.
  This is the exact, quantified reason M6-L06's approximate methods
  exist: not because exact search is 'wrong', but because it is the
  one thing that cannot be made fast enough at this scale by
  definition -- checking fewer than all N vectors is what makes a
  method approximate in the first place.

============================================================================
5. WHAT THIS LAB IS AND IS NOT
============================================================================
  REAL: every millisecond in sections 2-3 is an actual measured
  wall-clock time from running real vectorised numpy search on real
  random unit vectors, on the machine executing this script.

  MACHINE-SPECIFIC: the exact timings will differ on different
  hardware, numpy builds, and load conditions. Re-run this lab on
  your own machine before quoting a specific number to anyone.

  ILLUSTRATIVE: section 4's crossover point depends entirely on the
  measured rate above and the chosen 100ms budget -- recompute both
  for your own system's real embedding dimension and real latency
  requirement.

  NOT SHOWN: how approximate methods (M6-L06) actually achieve
  sub-linear query time, and how exact search is used as the
  ground-truth reference for measuring an approximate method's
  recall -- both are M6-L06's job, building directly on the cost
  measured here.

Done.
```

### 7.3 Reading the result

**Section 2's per-vector column is the number that proves linearity, not just suggests it.** It stays
within a narrow band (52–72 nanoseconds) across three orders of magnitude of corpus size — exactly what
"the rate is constant, only the total changes" looks like when measured directly.

**Section 3's slightly sub-proportional early scaling (4.6× time for 6× dimensions, at the 768 point) is
worth noting rather than smoothing over.** It likely reflects fixed per-call overhead and vectorisation
efficiency mattering more at smaller sizes — a real measurement detail, not a contradiction of the
underlying linear cost model, which the later, larger points confirm more closely.

**Section 4 is the entire point of the lesson, expressed as one number: 1.9 million.** Not "exact search
doesn't scale," which is vague — a specific corpus size, computed from a specific measured rate and a
specific latency budget, past which a specific architectural decision must change.

---

## 8. Common mistakes and troubleshooting

1. **Testing search latency only at a small development-scale corpus.** §6 — the exact failure that
   surprised a real launch.
2. **Assuming "it's slow" is a bug to fix rather than an expected consequence of scale.** Linear cost is
   not a defect; it is what §7.2 predicts and measures directly.
3. **Not stating a latency budget before choosing a search architecture.** Without one, there is no
   number to compute a crossover point against (§5.3).
4. **Assuming approximate methods are strictly "better."** They trade a small, measurable amount of
   accuracy for speed — appropriate above the crossover point, unnecessary complexity below it (§5.4).
5. **Discarding exact search once an approximate index is built.** It remains necessary as the ground
   truth for measuring that index's accuracy (§5.4, M6-L06).
6. **Quoting this lesson's specific millisecond figures as if they applied to your hardware.** Re-measure
   on your own machine (§5.5).
7. **Forgetting that both corpus size and dimension count independently affect cost.** A larger embedding
   model can push a system past its latency budget even at a constant corpus size (§5.2).

| Symptom | Likely cause | Fix |
|---|---|---|
| Search latency was fine in testing, unacceptable in production | Corpus size scaled up without re-measuring cost | Measure at multiple sizes; extrapolate per §7.4 before launch |
| Search got slower after upgrading the embedding model | Higher dimension count, same corpus size | Recompute the cost model with the new dimension count (§5.2) |
| No clear answer to "do we need approximate search yet" | No stated latency budget or crossover calculation | Compute the crossover point for your actual corpus size and budget (§5.3) |
| An approximate index's accuracy can't be assessed | No ground-truth exact-search results to compare against | Keep exact search available for evaluation, even after deploying ANN (§5.4) |

---

## 9. Security, privacy, reliability, cost

- **Reliability.** Measure query latency at more than one corpus size before launch, and extrapolate to
  the real production scale (§7.2, §6) — do not discover linear scaling in production.
- **Cost.** Exact search's `O(N×d)` cost means both corpus growth and embedding-model upgrades
  independently increase compute cost per query — budget for both (§5.2).
- **Reliability.** State a latency budget explicitly as a requirement before choosing a search
  architecture — it is the number the crossover calculation (§5.3) needs.
- **Reliability.** Retain exact search as a ground-truth evaluation tool even after deploying an
  approximate index — without it, an approximate method's accuracy cannot be measured (§5.4, M6-L06).

---

## 10. Exercises

### Exercise 1 — Beginner (~20 min)

1. In one sentence, why must exact search compare the query against every vector?
2. Why does exact search's cost scale linearly with corpus size?
3. Name the second factor, besides corpus size, that affects exact search's query cost.
4. What is a "crossover point," in your own words?
5. Why does exact search remain useful even after an approximate method is deployed?

### Exercise 2 — Intermediate (~40 min)

1. Run the lab. Report your own machine's measured time at 1,000,000 vectors, and compare it to this
   lesson's figure.
2. Recompute §7.4's crossover point using your own measured rate and a 50ms latency budget instead of
   100ms.
3. Modify the lab to measure query time for `k=1` versus `k=100`. Does `k` materially affect cost at
   this corpus size? Explain why or why not.
4. Using your own measured per-vector cost, estimate the corpus size at which a 10ms latency budget
   would be exceeded.
5. Design a simple pre-launch checklist item ("measure latency at N=X, N=10X, N=100X before shipping")
   for a team building a new search feature.

### Exercise 3 — Challenge (~50 min)

1. Implement exact search using a plain Python loop instead of vectorised numpy, and measure how much
   slower it is at the same corpus sizes — quantify the cost of not vectorising.
2. Extend the lab to measure memory usage (not just time) as corpus size grows, and compute the memory
   crossover point for a stated available RAM budget.
3. Implement a simple sharding scheme (split the corpus across multiple "shards," search each, merge
   results) and measure whether it changes per-query latency at a fixed total corpus size.
4. Research (conceptually) what BLAS/LAPACK libraries numpy relies on for matrix operations, and explain
   why vectorised operations are faster than an equivalent Python loop.
5. Write the capacity-planning memo for a real or hypothetical system: current corpus size, growth rate,
   measured cost model, and the date at which exact search will cross its latency budget if nothing
   changes.

---

## 11. Quiz

*(Answers: [`answer-keys/module-06-answers.md`](../../answer-keys/module-06-answers.md#m6-l05).)*

**Q1.** In §7.1, exact nearest-neighbour search means:

- A. Computing similarity between the query and every single vector in the corpus, then keeping the best k.
- B. Randomly sampling a subset of the corpus and returning the closest match found.
- C. Using a pre-built index to skip most of the corpus.
- D. Comparing only the first k vectors in the corpus.

**Q2.** In §7.2, going from 1,000 to 1,000,000 vectors (1,000x more) increased query time by roughly:

- A. 10x
- B. 100x
- C. 725x, close to proportionally, confirming the algorithm's cost scales linearly with corpus size.
- D. It stayed exactly the same regardless of corpus size.

**Q3.** Why does exact search cost scale linearly with corpus size, per §5.1?

- A. It does not; the cost is constant regardless of corpus size.
- B. The algorithm re-reads the query vector once per vector in the corpus.
- C. Larger corpora require more dimensions per vector.
- D. Correctness requires comparing the query against every vector; there is no way to skip any of them and still guarantee finding the true nearest neighbors.

**Q4.** In §7.3, query time also grew as dimension count increased, holding corpus size fixed. This is
because:

- A. Higher-dimension vectors require re-normalising the entire corpus every query.
- B. Each additional dimension adds one more multiplication per vector comparison, for every vector in the corpus.
- C. Dimension count affects only storage, never query time.
- D. The corpus size secretly changed between measurements.

**Q5.** Per §5.1/§5.2, exact search's total per-query cost is best described as:

- A. Proportional to the product of corpus size and dimension count (O(N×d)).
- B. Constant, regardless of corpus size or dimension count.
- C. Proportional only to dimension count, never corpus size.
- D. Proportional to the square of corpus size.

**Q6.** In §7.4, the measured crossover point (around 1.9 million vectors) represents:

- A. The maximum number of vectors any computer can store.
- B. The point at which exact search becomes mathematically incorrect.
- C. A fixed constant that applies to every system regardless of hardware.
- D. The corpus size beyond which, at this run's measured rate, exact search alone no longer fits a 100ms latency budget.

**Q7.** Why does the lesson describe exact search as neither "wrong" nor obsolete, despite its cost?

- A. It is the cheapest method at every possible corpus size.
- B. It is the only method that guarantees finding the true nearest neighbors, and it remains the reference standard other methods are measured against.
- C. Approximate methods have been shown to always be less accurate.
- D. It requires no computation at all.

**Q8.** What role does exact search play for approximate methods, per §5.3's forward reference?

- A. It replaces the need for approximate methods entirely.
- B. It has no relationship to approximate methods.
- C. It provides the ground-truth top-k that an approximate method's results are compared against, to measure how much accuracy was traded for speed.
- D. It is only used for training approximate methods, never for evaluation.

**Q9.** The lab explicitly cautions that its millisecond timings are:

- A. Specific to the machine that ran them, and should be re-measured on your own hardware before being quoted elsewhere.
- B. Guaranteed to be identical on any computer.
- C. Only valid for corpora smaller than 1,000 vectors.
- D. Independent of numpy version or hardware.

**Q10.** Why do faster, approximate search methods (M6-L06) necessarily risk missing the true nearest
neighbor sometimes?

- A. They always use a different similarity metric than exact search.
- B. They only work on sparse vectors, never dense ones.
- C. They require more memory than exact search.
- D. Any method that avoids comparing against every single vector, by definition, might skip the one vector that would have been the true best match.

**Q11.** A system with a 50ms latency budget and this lab's measured rate at 384 dimensions would hit its
exact-search limit at roughly:

- A. Twice the corpus size found for a 100ms budget.
- B. Half the corpus size found for a 100ms budget, since the relationship is linear.
- C. The same corpus size regardless of the budget.
- D. An unrelated, unpredictable corpus size.

**Q12.** The central practical lesson of this lab is:

- A. Exact search should never be used in any production system.
- B. Query cost cannot be predicted in advance and must always be discovered through incidents.
- C. Exact search's cost is measurable, predictable, and can be extrapolated to determine exactly when a system needs a faster method, rather than switching methods based on guesswork.
- D. Dimension count has no effect on search performance.

**Q13.** *(Written, rubric-graded.)* In under 150 words: your team's search feature was tested only
against a 10,000-document staging corpus and is about to launch against a 50-million-document production
corpus. State what you would measure before launch, referencing this lesson's method, and what decision
that measurement should drive.

---

## 12. Revision notes

- **Exact search compares the query against every vector — the only way to guarantee correctness, and
  the reason it cannot be made sub-linear.**
- **Query cost scales linearly with corpus size.** Measured: a 1,000× larger corpus cost roughly 726×
  more time, with per-vector cost staying nearly constant across three orders of magnitude.
- **Query cost also scales with dimension count, independently.** Measured: roughly 21× more time going
  from 128 to 3,072 dimensions at fixed corpus size.
- **Total cost is proportional to `N × d`.** Both corpus growth and embedding-model upgrades
  independently increase query cost.
- **A measured rate extrapolates to a specific, actionable crossover point.** Measured: roughly 1.9
  million vectors before a 100ms latency budget stops being achievable, on this run's hardware.
- **Exact search does not become useless once faster methods exist.** It remains preferable below the
  crossover point and necessary as the ground-truth standard approximate methods (M6-L06) are measured
  against.
- **Measure latency at more than one scale before launch.** A cost that scales linearly is predictable in
  advance from a handful of measurements — not something that should be discovered in production (§6).

---

## 13. Completion checklist

- [ ] I can implement exact nearest-neighbour search and explain why it checks every vector.
- [ ] I have measured (or can explain how to measure) query time at multiple corpus sizes.
- [ ] I can state exact search's cost model as proportional to corpus size times dimension count.
- [ ] I can compute a crossover point given a measured rate and a latency budget.
- [ ] I know why exact search remains necessary even after deploying an approximate method.
- [ ] I would never quote this lesson's specific timings as applying to a different machine.
- [ ] I scored 10/13 on the quiz.

---

## 14. References

- NumPy documentation — `numpy.argpartition` (used for the top-k selection in this lab's implementation).
  <https://numpy.org/doc/stable/reference/generated/numpy.argpartition.html> `[UNVERIFIED]`
- Malkov, Y. A. and Yashunin, D. A. (2016), *Efficient and robust approximate nearest neighbor search
  using Hierarchical Navigable Small World graphs* (the approximate method M6-L06 covers next, cited here
  for context on what exact search's cost motivates). <https://arxiv.org/abs/1603.09320> `[UNVERIFIED]`

---

## 15. Next lesson

→ [M6-L06 — Approximate Nearest Neighbours and HNSW Intuition](M6-L06-approximate-nn-hnsw.md)

You now know exactly what exact search costs, and exactly when that cost becomes a problem. Next: how
approximate methods buy sub-linear query time by deliberately not checking every vector — and what that
trade costs in accuracy, measured against the exact search this lesson just built.
