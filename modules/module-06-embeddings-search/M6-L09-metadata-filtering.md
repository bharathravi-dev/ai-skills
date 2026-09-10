# M6-L09 — Metadata, Filtering and Filtered-ANN Pitfalls

| | |
|---|---|
| **Lesson ID** | M6-L09 |
| **Difficulty** | 2 (Intermediate) |
| **Estimated study time** | 1.75 hours |
| **Prerequisites** | [M6-L08](M6-L08-pgvector-hands-on.md) |

---

## 1. Learning objectives

1. **Measure** why post-filtering an approximate search can silently return far fewer results than
   requested.
2. **Measure** what pre-filtering before an exact search fixes, and what it costs as selectivity
   decreases.
3. **Diagnose** the actual bug behind a filtered-ANN shortfall — filtering at the wrong stage, not
   necessarily too small a search — and fix it correctly.
4. **Use** search-width (`nprobe`/`ef`) as a secondary lever once filtering happens at the correct stage.
5. **State** what this lesson leaves to a real system's own internal implementation.

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **Metadata filter** | A structured condition (e.g. `category = X`) combined with a vector similarity search. |
| **Post-filtering** | Running the similarity search first, then applying the metadata filter to the results. |
| **Pre-filtering** | Applying the metadata filter first, then searching only within the matching subset. |
| **Selectivity** | The fraction of the corpus a given filter condition matches. |
| **Filtered-ANN pitfall** | The class of bugs where combining an approximate index with a filter returns fewer or wrong results than expected. |
| **Candidate pool** | The set of vectors an approximate search examines before any final ranking or filtering is applied. |

---

## 3. Plain-language explanation

### 3.1 The `WHERE` clause M6-L08 previewed, in full

M6-L08 showed that adding `WHERE category = 'billing'` to a pgvector query is syntactically
unremarkable. **What that query actually does under the hood** — and where it can quietly go wrong — is
this lesson's subject.

### 3.2 Filtering after searching can throw away real matches

The most obvious way to combine a filter with approximate search: get the top-k by similarity, then
filter those k. §7.1 measures exactly why this fails for anything but the most common filter values — the
filter examines only the k candidates the search happened to surface, and if few of those k belong to the
category you wanted, you get back far fewer than k, even though the corpus contains plenty of genuine
matches elsewhere.

### 3.3 Filtering before searching fixes correctness, at a real cost

Filter the corpus down to the matching subset first, then search that subset exactly. §7.2 shows this
always returns the correct count — and shows precisely how its cost rises as the filter becomes less
selective, approaching the cost of exact search over the entire corpus.

### 3.4 The actual bug is usually about *stage*, not *size*

§7.3 finds something sharper than "search harder": the real fix for §7.1's shortfall is filtering the
**whole candidate pool** before truncating to the top-k — not necessarily searching a larger pool.
Widening the search (`nprobe`) helps only at the margin, once the filtering stage itself is correct.

---

## 4. Analogy

**A talent scout reviewing the top 10 resumes for a shortlist, then checking each one's location.** If
only 2 of the top-10-by-score candidates happen to live in the required city, the scout ends up with 2
shortlisted candidates, not 10 — even if 50 qualified, in-city candidates exist further down the pile.
The scout's mistake was not reviewing too few resumes overall; it was checking location **after**
deciding who made the top 10 by a different criterion entirely.

The fix is not necessarily to read more resumes (though it can help) — it is to check location **for
every resume in the batch actually reviewed**, before deciding who the top 10 are.

### Where the analogy breaks

- **A human scout can flexibly re-order their process.** An approximate search's internal ranking
  happens in a specific, fixed order dictated by the index structure — "filter first" and "rank first"
  are genuinely different code paths, not a matter of the scout deciding to be more careful.
- **A scout reading more resumes has a roughly linear cost.** An approximate index's cost for searching a
  wider pool follows the specific curve M6-L06 measured — not necessarily linear, and with its own
  optimum.

---

## 5. Detailed technical explanation

### 5.1 The post-filter shortfall, measured

`[REAL]` §7.1 requested 10 results across four categories of varying selectivity:

| Category | Corpus share | Avg. results returned (of 10 requested) |
|---|---|---|
| common | 50% | 4.7 |
| medium | 30% | 2.9 |
| rare | 15% | 1.9 |
| **very_rare** | **5%** | **0.5** |

**Requesting 10 and receiving 0.5 on average is not a malfunction.** It is the direct, arithmetic
consequence of applying the category filter *after* the search had already committed to a fixed set of
10 candidates, chosen purely by similarity score, with no awareness of the filter at all.

### 5.2 The pre-filter fix, and its real cost curve

`[REAL]` §7.2 filtered first, then ran exact search (M6-L05) only within the matching subset:

| Category | Subset size | Results returned | Time/query |
|---|---|---|---|
| common | 24,847 | **10.0** | 0.58ms |
| very_rare | 2,495 | **10.0** | 0.04ms |

**Every row returned the full requested count** — correctness is fully restored. But the `common` row's
cost (0.58ms) is roughly **half** of full exact search over the entire 50,000-vector corpus (0.82ms) —
proportional to the subset size, exactly M6-L05's linear-scaling result. **As a filter becomes less
selective, pre-filter-then-exact search approaches the cost of exact search over everything** — the
approximate index's entire speed advantage (M6-L06) erodes in direct proportion to how large the matching
subset is.

### 5.3 The actual bug: stage, not size

`[REAL]` §7.3 fixed §5.1's shortfall correctly — filtering the **entire candidate pool** before selecting
the top-k, rather than after:

| `nprobe` | Results returned (of 10 requested) |
|---|---|
| 1 | **9.9** |
| 2 | **10.0** |
| 50 | 10.0 |

**Even at `nprobe=1` — searching a single cluster — filtering at the correct stage recovered nearly all
10 requested results**, a dramatic improvement over §5.1's 0.5. **Widening the search (`nprobe`) only
closed a small remaining gap** — it is a real, secondary lever (and would matter far more for an even
rarer category, or a smaller per-cluster pool), but **the primary fix was never "search more"; it was
"filter before truncating."** This is the single most important, and most commonly misdiagnosed, insight
in filtered-ANN search: a shortfall that looks like "the index isn't finding enough" is very often "the
filter ran after the decision that mattered had already been made."

### 5.4 What this lesson does not implement

Real vector databases, including pgvector (M6-L08), can push a filter condition **into** the index
traversal itself — evaluating it as the search proceeds rather than as a separate pass before or after.
This can outperform either pure strategy shown here, and exactly how it works is product- and
version-specific. This lesson establishes the underlying problem and the two general strategies; a
specific system's internal optimization is worth checking directly before assuming its behaviour matches
either pure case.

### 5.5 Assumptions and limitations

- §7.1–7.3's category shares, corpus size, and timings are illustrative and machine-specific. Real
  selectivity in your own metadata, and your own hardware, will differ — measure your own before choosing
  a strategy.
- §7.3's small margin between `nprobe=1` and `nprobe=50` is specific to this lab's cluster size (~500
  members/cluster) and 5% selectivity; a rarer category or smaller clusters would show `nprobe` mattering
  more.
- This lesson does not implement or measure how any specific real vector database pushes filters into
  index traversal internally (§5.4) — that is product-specific engineering outside this lesson's scope.

---

## 6. Worked example — the "empty results" bug that wasn't the index's fault

**The system.** A document search feature lets users filter by department before searching. Most
departments are common; a few are small, specialist teams. Support tickets start arriving: "searching
within [a specific small department] returns almost nothing, even though I know there are dozens of
matching documents."

**The team's first hypothesis.** Someone suspects the approximate index itself is broken for this
department's documents — perhaps they clustered oddly, or the embeddings are somehow worse for this
content.

**What was actually happening.** The search implementation, written early and never revisited, requested
the top 10 results by similarity, *then* filtered by department — exactly §5.1's mechanism. For a small
department at low corpus share, the top 10 by raw similarity rarely contained more than one or two
documents from that department, regardless of how many true matches existed.

**How it was actually found.** Someone tried filtering *first* and searching only within the
department's documents (§5.2's approach) as a diagnostic, and it worked — full result counts came back
immediately, proving the documents and their embeddings were fine all along. The bug was never in the
index; it was in the order two operations happened to run in.

**Three defects:**

| # | Defect | Consequence |
|---|---|---|
| 1 | Filtering ran after truncation to top-k, not before | Correct results existed and were simply discarded before the filter ever examined them |
| 2 | The first hypothesis blamed the index/embeddings rather than the query logic | Debugging time was spent investigating a component that was never at fault |
| 3 | No test existed for a known query against a known small-selectivity filter | The shortfall shipped and was only caught by user reports |

### The fix

**Filter the whole candidate pool before truncating to the requested count** (§5.3), not the other way
around — the single highest-leverage fix, cheaper than any amount of extra search-width tuning.

**Diagnose a filtered-search shortfall by checking filter *order* first**, before suspecting the index,
the embeddings, or the underlying data — §5.3 showed this fixes the overwhelming majority of the gap on
its own.

**Test with a known query against a deliberately low-selectivity filter**, the same evaluation discipline
M5-L18 established generally, applied here specifically to catch this class of bug before it reaches
users.

**The general rule.** **When a filtered vector search returns too few results, check what got filtered
and when before assuming the search itself is inadequate.** The fix is very often a one-line reordering,
not a bigger index.

---

## 7. Practical activity

**File:** [`labs/m6/l09_filtered_ann.py`](../../labs/m6/l09_filtered_ann.py)

**No API key, no network.** Expect the run to take roughly 10–20 seconds (real k-means).

```bash
source .venv/bin/activate
python labs/m6/l09_filtered_ann.py
```

### 7.2 Expected output

`[EXECUTED, machine-specific timings]` — 2026-09-10, Python 3.10.11, NumPy 2.2.6, scikit-learn 1.7.2.

```text
Building the 100-cluster IVF index over 50,000 vectors (a few seconds)...
Index built in 6.2s.

============================================================================
1. THE POST-FILTER PROBLEM: FILTER AFTER SEARCHING, MEASURED
============================================================================
  Ask for the top-10 results, THEN filter by category --
  the naive, obvious way to combine vector search with a WHERE clause.

  category     true corpus share   avg results returned   requested
  common                     50%                    4.7         10
  medium                     30%                    2.9         10
  rare                       15%                    1.9         10
  very_rare                   5%                    0.5         10

  Read the 'very_rare' row: requesting 10 results and getting back a
  small fraction of that is not a bug in the index -- it is the
  direct, arithmetic consequence of filtering AFTER selecting only
  10 candidates from a corpus where this category is uncommon. Many
  genuinely matching documents exist elsewhere in the corpus; they
  were simply never among the 10 candidates ANN search happened to
  surface BEFORE the filter ran.

============================================================================
2. THE PRE-FILTER FIX: FILTER FIRST, THEN SEARCH EXACTLY -- AT A COST
============================================================================
  Filter the corpus to the matching category FIRST, then run EXACT
  search (M6-L05) only within that subset. This always returns the
  full requested count, when enough matching documents exist -- but
  it isn't free.

  category      subset size   avg results returned   avg time/query
  common             24,847                   10.0           0.58ms
  medium             14,943                   10.0           0.25ms
  rare                7,715                   10.0           0.14ms
  very_rare           2,495                   10.0           0.04ms

  For comparison, exact search over the FULL 50,000-vector corpus: 0.82ms/query.

  Pre-filtering fixes correctness completely -- every row above
  returned the full requested count. But look at the 'common' row's
  time: it costs roughly HALF of full exact search -- proportional
  to the subset size (M6-L05's linear scaling, exactly), not a small
  fraction of it. Even a 50%-selective filter still leaves you paying
  something close to a full linear scan, which is the exact cost the
  approximate index (M6-L06) exists to avoid. The less selective the
  filter, the closer 'filter first, then search exactly' gets to
  plain exact search over the whole corpus -- and at NO filter at
  all, that is precisely what it becomes.

============================================================================
3. OVER-FETCHING: FILTER THE WHOLE POOL, THEN TAKE THE TOP-K
============================================================================
  Section 1's flaw: it filtered the top-10-BY-SCORE, discarding
  matching candidates that happened to rank 11th or lower BEFORE the
  filter ever saw them. The fix: filter the WHOLE candidate pool by
  category first, THEN take the best k of what survives -- and
  search more clusters (nprobe) to make that pool bigger.

  Category: 'very_rare' (5% of the corpus). Requesting 10 results.

    nprobe   avg results returned   avg time/query
         1                    9.9           0.06ms
         2                   10.0           0.06ms
         5                   10.0           0.10ms
        10                   10.0           0.17ms
        20                   10.0           0.31ms
        50                   10.0           0.73ms

  Read this against section 1's 0.5-of-10 result. The real fix was
  never 'search harder' -- it was filtering the pool BEFORE cutting
  it down to k, which alone recovers nearly all 10 results
  even at nprobe=1 (9.9 of 10 here). nprobe still matters at the
  margin: it closes the small remaining gap, and would matter far
  more for a category rarer than 5%, or a smaller per-cluster pool --
  but it is a SECONDARY lever. The primary bug in section 1 was
  filtering at the wrong STAGE, not searching too small a POOL.

============================================================================
4. WHAT THIS LAB IS AND IS NOT
============================================================================
  REAL: every count and timing in this lab comes from actually
  running the search and filter operations on a real (if synthetic)
  corpus with real category labels -- nothing here is simulated.

  ILLUSTRATIVE: the specific category shares, corpus size, and
  timings are chosen for this lab and this machine. Real selectivity
  in your own metadata, and your own hardware, will give different
  numbers -- measure your own before choosing an overfetch factor or
  a pre-filter/post-filter strategy.

  NOT SHOWN: how real vector databases implement filtered search
  internally (some push the filter into the index traversal itself,
  which can do better than either pure strategy shown here -- product-
  and version-specific, and worth checking directly for any system
  you deploy, including pgvector, M6-L08).

Done.
```

### 7.3 Reading the result

**Section 1's 0.5-of-10 result is the entire motivation for this lesson.** It is not a corner case — 5%
selectivity is an entirely ordinary real-world filter (a smaller department, a less common language, a
niche product category), and the naive combination of filter-after-search fails exactly this often on
data shaped this way.

**Section 2 is correctness bought back at a precisely quantifiable price.** The `common` row's cost
(roughly half of full exact search) is the number to remember: pre-filtering is not free even when it
works, and its cost rises predictably as the filter matches more of the corpus.

**Section 3 is the result worth sitting with the longest.** The gap between 0.5 and 9.9 is not explained
by "the pool was too small" — it is explained by "the filter ran at the wrong point in the computation."
`nprobe`'s marginal effect here (9.9 → 10.0) is real but small; the stage of the filter was the dominant
variable by a wide margin.

---

## 8. Common mistakes and troubleshooting

1. **Filtering after truncating to the top-k by similarity score.** §5.1, §6 — the single most common
   filtered-ANN bug, and the one this lesson centres on.
2. **Assuming a shortfall means the index needs to search more (higher `nprobe`/`ef`).** §5.3 — check
   filter *stage* first; it is usually the larger effect.
3. **Assuming pre-filtering is free just because it's correct.** §5.2 — its cost scales with subset size,
   approaching full exact search as selectivity decreases.
4. **Blaming embeddings or the index for a shortfall that is actually a query-logic bug.** §6 — a
   diagnostic swap to pre-filtering isolates the cause quickly.
5. **Never testing a filtered search against a genuinely low-selectivity filter.** Common-category
   filters can look fine in testing while rare-category filters silently fail.
6. **Assuming a specific real vector database behaves like either pure strategy in this lab.** Many
   systems push filters into the index traversal itself (§5.4) — check the actual implementation.

| Symptom | Likely cause | Fix |
|---|---|---|
| A rare-category (or otherwise selective) filtered search returns far fewer results than requested | Filtering applied after truncation to top-k | Filter the whole candidate pool before truncating (§5.3) |
| A filtered search is correct but slower than expected | Pre-filter-then-exact on a low-selectivity filter | Expect and budget for cost approaching full exact search as selectivity decreases (§5.2) |
| Increasing `nprobe`/`ef` barely helps a filtered-search shortfall | The bug is filter stage, not pool size | Fix filtering order first; treat search-width as a secondary lever (§5.3) |
| A team suspects the index or embeddings are broken for one category | The actual bug is query-logic ordering | Diagnose with a pre-filter-then-exact comparison before investigating the index itself (§6) |

---

## 9. Security, privacy, reliability, cost

- **Reliability.** Filter the whole candidate pool before truncating to the requested count — the single
  highest-leverage fix for the most common filtered-ANN shortfall (§5.1, §5.3).
- **Reliability.** Test filtered search against a genuinely low-selectivity filter, not just common
  categories — a shortfall can hide in testing that only exercises common cases.
- **Cost.** Pre-filter-then-exact search's cost rises toward full exact search as filter selectivity
  decreases — budget for this explicitly rather than assuming filtering always makes search cheaper.
- **Reliability.** Diagnose a filtered-search shortfall by checking filter order before suspecting the
  underlying index or embeddings (§6) — it is a faster, usually correct, first hypothesis.
- **Privacy.** A metadata filter used for access control (e.g., tenant isolation, M7-L15) has correctness
  requirements stricter than ordinary relevance filtering — a filtered-ANN shortfall in that context is a
  security bug, not just a quality one; verify it enforces the boundary completely, not approximately.

---

## 10. Exercises

### Exercise 1 — Beginner (~20 min)

1. In one sentence, why does post-filtering return fewer results for a rare category?
2. What does pre-filtering fix, and what does it cost as a filter becomes less selective?
3. In §7.3, why did increasing `nprobe` only slightly improve the result count?
4. What is the actual bug behind most filtered-ANN shortfalls, per this lesson?
5. Name one thing this lesson explicitly leaves to a real system's own implementation.

### Exercise 2 — Intermediate (~40 min)

1. Run the lab. Confirm the "very_rare" category's post-filter shortfall and pre-filter fix.
2. Add a category at 1% selectivity and report how post-filtering, pre-filtering, and the corrected
   filter-then-topk approach each behave.
3. Measure the crossover selectivity at which pre-filter-then-exact search costs the same as the
   approximate (unfiltered) search — above what selectivity does pre-filtering stop being worthwhile?
4. Implement the "wrong stage" bug from scratch (filter after truncation) and the "right stage" fix
   (filter before truncation) as two clearly separated functions, and write a test that would catch the
   bug.
5. Design a monitoring check for a production filtered-search feature that would have caught §6's
   incident before users reported it.

### Exercise 3 — Challenge (~50 min)

1. Implement a hybrid strategy that chooses pre-filtering vs the corrected post-filter-pool approach
   automatically, based on measured or estimated filter selectivity, and justify the threshold you choose.
2. Research (conceptually) how pgvector or another real system exposes combined filtering and ANN search,
   and write up whether it appears to push the filter into the index traversal or use one of this lesson's
   two pure strategies.
3. Extend the lab to measure filtered search with TWO simultaneous metadata conditions (e.g., category AND
   a second field), and analyse how combined selectivity affects both strategies.
4. Build a small test suite covering: common filter, rare filter, filter matching zero documents, and
   filter with no matching documents in the initially searched pool — and verify the corrected
   implementation handles all four correctly.
5. Write the design note for a production filtered-search feature, stating your chosen strategy, your
   monitoring plan for shortfalls, and how you would decide whether to invest in an index that supports
   filtering natively.

---

## 11. Quiz

*(Answers: [`answer-keys/module-06-answers.md`](../../answer-keys/module-06-answers.md#m6-l09).)*

**Q1.** In §7.1, requesting 10 results for the "very_rare" (5%) category returned only 0.5 on average.
This happened because:

- A. The index was corrupted for that category's vectors.
- B. The corpus contained no matching documents at all.
- C. The embedding model failed to represent that category correctly.
- D. The search selected the top 10 candidates by similarity score first, then filtered by category, discarding matching candidates that scored below the cutoff before the filter ever examined them.

**Q2.** In §7.2, pre-filtering to the matching category before running exact search:

- A. Returned fewer results than post-filtering in every case.
- B. Always returned the full requested count (when enough matching documents existed), fixing correctness, at a real, measured time cost proportional to the filtered subset's size.
- C. Was faster than the approximate index in every case, regardless of selectivity.
- D. Required no computation at all.

**Q3.** In §7.2, filtering to the "common" category (50% of the corpus) and searching that subset exactly
cost roughly:

- A. Half of what searching the full corpus exactly cost, consistent with M6-L05's linear scaling.
- B. Exactly the same as searching a single cluster.
- C. Twice as much as searching the full corpus.
- D. A negligible, near-zero amount regardless of subset size.

**Q4.** Per §5.2, as a metadata filter becomes less selective (matches a larger share of the corpus),
pre-filter-then-exact search:

- A. Becomes faster than the approximate index in every case.
- B. Is unaffected, since filtering always costs the same regardless of subset size.
- C. Approaches the cost of exact search over the entire corpus, losing the approximate index's speed advantage.
- D. Stops returning correct results entirely.

**Q5.** In §7.3, the corrected approach filtered the WHOLE candidate pool by category before selecting
the top-k, rather than:

- A. Using a different distance metric entirely.
- B. Increasing the corpus size.
- C. Removing the category field from the schema.
- D. Selecting the top-k by similarity score first and only then applying the category filter, which was section 1's actual mistake.

**Q6.** In §7.3, increasing `nprobe` from 1 to 50 improved the average results returned only slightly
(9.9 to 10.0), because:

- A. Even a single cluster's pool already contained enough matching-category candidates once filtering happened at the correct stage, making nprobe a secondary, marginal lever here rather than the primary fix.
- B. nprobe has no effect on filtered search under any circumstances.
- C. The category field was ignored entirely at higher nprobe values.
- D. Higher nprobe values are always slower without any recall benefit.

**Q7.** The primary lesson of §7.3, per the lab's own conclusion, is that the bug in section 1 was:

- A. An unfixable limitation of all approximate search methods.
- B. Filtering at the wrong stage (after truncating to top-k by score), not an insufficiently large candidate pool.
- C. A missing database index on the category column.
- D. Caused entirely by using cosine similarity instead of Euclidean distance.

**Q8.** Why does this lesson describe both post-filtering and pre-filter-then-exact as having a real
cost, rather than declaring one strategy universally correct?

- A. Because neither strategy ever returns correct results.
- B. Because cost is unrelated to which strategy is chosen.
- C. Because post-filtering risks returning too few results for selective filters, while pre-filtering sacrifices the approximate index's speed advantage as selectivity decreases — each has a genuine trade-off.
- D. Because both strategies are mathematically identical.

**Q9.** What does this lesson explicitly leave unexplored, deferring to a real system's own
implementation?

- A. The definition of cosine similarity.
- B. How BM25 computes term frequency.
- C. The mathematics of k-means clustering.
- D. How real vector databases push metadata filters directly into index traversal, which can outperform either simple strategy shown in the lab.

**Q10.** The general principle connecting this lesson to M6-L05/M6-L06 is:

- A. Metadata filtering makes M6-L05 and M6-L06's findings irrelevant.
- B. Combining a metadata filter with approximate search does not create a new algorithm — it exposes exactly the same recall/speed trade-off those lessons already measured, applied at the wrong or right stage.
- C. Filtering requires an entirely different distance metric than M6-L05/M6-L06 used.
- D. M6-L05 and M6-L06's measurements do not apply once metadata is involved.

**Q11.** A category selectivity of 5% combined with a candidate pool from a single cluster (`nprobe=1`)
in §7.3 still recovered 9.9 of 10 requested results, PROVIDED that:

- A. The category field was removed from the query.
- B. Exact search was used instead of any approximate method.
- C. The filter was applied to the whole pool before truncating to the top-k, not after.
- D. The corpus contained no other categories at all.

**Q12.** The general practical rule this lesson establishes for combining metadata filters with vector
search is:

- A. Filter before truncating to the requested count, and treat both filter selectivity and index search-width as levers with real, measurable costs — never assume a naive combination of the two works correctly by default.
- B. Always use post-filtering regardless of selectivity.
- C. Always use pre-filtering regardless of selectivity.
- D. Metadata filtering should be avoided entirely in vector search systems.

**Q13.** *(Written, rubric-graded.)* In under 150 words: your team's filtered vector search returns too
few results for one specific, low-selectivity filter value, and a colleague proposes increasing `nprobe`
to fix it. Based on this lesson, what would you check first, and why?

---

## 12. Revision notes

- **Post-filtering (search, then filter) can silently return far fewer results than requested.**
  Measured: a 5%-selective category returned 0.5 of 10 requested results on average.
- **Pre-filtering (filter, then exact search) fixes correctness completely, at a cost proportional to
  subset size.** Measured: a 50%-selective filter cost roughly half of full exact search — approaching
  full cost as selectivity decreases, exactly M6-L05's linear scaling.
- **The actual bug behind most filtered-ANN shortfalls is filtering at the wrong stage, not an
  insufficiently large search.** Measured: filtering the whole candidate pool before truncating to top-k
  recovered 9.9 of 10 results even at the smallest possible search width (`nprobe=1`) — a dramatically
  larger fix than widening the search alone provided.
- **Search-width (`nprobe`/`ef`) is a real but secondary lever once filtering happens at the correct
  stage** — it closes a small remaining gap, not the primary shortfall.
- **Diagnose a filtered-search shortfall by checking filter order first**, before suspecting the index,
  the embeddings, or the underlying data.
- **Real vector databases can push filters into index traversal itself**, potentially outperforming
  either pure strategy — check your specific system's actual behaviour rather than assuming.

---

## 13. Completion checklist

- [ ] I can explain why post-filtering an approximate search can return far fewer results than requested.
- [ ] I can compute (or estimate) the cost of pre-filter-then-exact search at a given selectivity.
- [ ] I know that the primary fix for a filtered-ANN shortfall is usually filter *stage*, not search width.
- [ ] I filter the whole candidate pool before truncating to a requested count, in any system I build.
- [ ] I test filtered search against genuinely low-selectivity filters, not just common cases.
- [ ] I diagnose filtered-search shortfalls by checking filter order before suspecting the index itself.
- [ ] I scored 10/13 on the quiz.

---

## 14. References

- pgvector — GitHub repository and documentation, on combining filters with indexed search.
  <https://github.com/pgvector/pgvector> `[UNVERIFIED]`
- Pinecone — documentation on metadata filtering with approximate search (a managed alternative's
  approach, for comparison). <https://docs.pinecone.io/> `[UNVERIFIED]`

---

## 15. Next lesson

→ [M6-L10 — Indexing, Updates, Deletion and Re-embedding](M6-L10-indexing-updates.md)

You now know how metadata filtering interacts with approximate search, and where it silently breaks.
Next: the full lifecycle of a vector index over time — updates, deletions, and what happens when the
embedding model itself changes underneath already-indexed data.
