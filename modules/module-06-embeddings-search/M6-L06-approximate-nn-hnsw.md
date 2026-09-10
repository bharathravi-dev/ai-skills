# M6-L06 — Approximate Nearest Neighbours and HNSW Intuition

| | |
|---|---|
| **Lesson ID** | M6-L06 |
| **Difficulty** | 3 (Advanced) |
| **Estimated study time** | 2.0 hours |
| **Prerequisites** | [M6-L05](M6-L05-exact-nn-search.md) |

---

## 1. Learning objectives

1. **Build** a real clustering-based (IVF-style) approximate index and measure its recall against
   exact-search ground truth.
2. **Explain** and measure the recall-vs-speed trade-off a single tunable parameter (`nprobe`) controls.
3. **Trace by hand** a graph-based greedy search, HNSW's core mechanism, and identify when it can fail.
4. **Distinguish** the failure modes of clustering-based and graph-based approximate search.
5. **State** why exact search remains the reference standard every approximate method is measured
   against, not a discarded baseline.

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **Approximate nearest-neighbour (ANN) search** | A search method that does not compare against every vector, trading controlled accuracy for speed. |
| **Recall@k** | The fraction of the true top-k (from exact search) that an approximate method actually found. |
| **IVF (inverted file) index** | A clustering-based ANN method: partition the corpus, search only the nearest cluster(s) at query time. |
| **`nprobe`** | The number of clusters an IVF-style search checks before stopping. |
| **HNSW (Hierarchical Navigable Small World)** | A graph-based ANN method: a multi-layer proximity graph searched by greedy traversal. |
| **Greedy graph search** | Repeatedly moving to whichever neighbour is closest to the query, stopping when none improves. |
| **Local minimum (graph search)** | A node whose neighbours are all farther from the query, even though a closer node exists elsewhere, unreachable from the path taken. |
| **`ef` (search-width parameter)** | HNSW's parameter controlling how many candidates are explored before stopping — the graph-search analogue of `nprobe`. |

---

## 3. Plain-language explanation

### 3.1 Give up the guarantee, on purpose, for speed

M6-L05 measured exact search's cost precisely enough to compute exactly when it stops fitting a latency
budget. Approximate methods respond to that measurement directly: **deliberately avoid comparing against
every vector**, accepting some chance of missing the true best match, in exchange for query time that no
longer grows linearly with corpus size. This lesson builds one such method for real and measures exactly
what that trade costs and buys.

### 3.2 Cluster first, then search only what's nearby

The simplest real approximate method: partition the corpus into clusters ahead of time. At query time,
compare against the (much smaller) set of cluster centres first, then exact-search only inside the
nearest one or few clusters — never touching the rest of the corpus at all. §7.1–7.2 build and measure
exactly this.

### 3.3 One number controls the whole trade-off

How many clusters to check (`nprobe`) is a dial: check one, and you are fast but might miss a match that
landed in a neighbouring cluster; check many, and you approach exact search's accuracy — and, eventually,
its cost. §7.2 measures this dial precisely, including a genuinely surprising point where checking *more*
clusters becomes *slower* than skipping the index altogether.

### 3.4 A different mechanism, a different failure mode

HNSW does not cluster at all — it builds a graph where each vector is connected to a handful of nearby
vectors, and searches by **greedily walking** toward the query, one hop at a time, stopping when no
neighbour is closer than the current position. §7.3 traces this by hand on a graph small enough to
verify every distance. Its failure mode is not "wrong cluster" — it is a **local minimum**: reaching a
point that looks locally best while a genuinely closer point sits unreachable elsewhere in the graph.

---

## 4. Analogy

**Two ways to find the nearest coffee shop without a full map.** One approach: divide the city into
districts, and only look at shops in whichever district you're standing in (or its immediate
neighbours) — fast, but if a slightly closer shop happens to sit just across a district boundary, you
never see it. A second approach: ask someone standing nearby which way the nearest shop is, walk that
way, and keep asking — fast, and usually accurate, but if you ask in a spot from which every visible
direction happens to lead slightly *away* from the true nearest shop (it's just around an obstructing
corner), you stop too early, confident you've found the best one.

Neither failure is a bug in the strategy. Both are the specific, predictable cost of not checking every
single shop in the city — which is exactly what exact search does, at a cost M6-L05 measured precisely.

### Where the analogy breaks

- **A city's districts are usually drawn by humans with intent.** The clusters in §7.1 are found
  automatically by k-means from the data itself, with no guarantee any single cluster boundary is
  "correct" in any deeper sense.
- **Asking one person for directions is free.** Following a real graph edge in HNSW has a real, if
  small, computational cost — every hop is one more comparison, just far fewer than checking the whole
  corpus.
- **A human giving directions can course-correct if you explain you're stuck.** A greedy graph search
  has no such recovery within a single layer — real HNSW's multiple layers and multiple entry points
  (§5.4) exist specifically to reduce how often this happens, not shown in this lesson's single-layer
  example.

---

## 5. Detailed technical explanation

### 5.1 A real IVF index, built and measured

`[REAL]` §7.1 built a genuine clustering index: 50,000 vectors generated from 200 underlying "topics"
(clusters of related vectors, the way real document embeddings cluster by subject — not pure
unstructured noise, which has no structure for any clustering method to find), partitioned into 100
k-means clusters.

At query time: compare the query against the 100 centroids (cheap), then exact-search only inside the
nearest `nprobe` clusters.

### 5.2 The recall-speed dial, measured exactly

`[REAL]` §7.2 measured recall@10 against exact-search ground truth (M6-L05's method) across `nprobe`
values:

| `nprobe` | Recall@10 | Time/query | Speedup vs exact |
|---|---|---|---|
| **1** | **84.7%** | 0.09ms | **8.7×** |
| 2 | 87.7% | 0.14ms | 5.7× |
| 5 | 93.0% | 0.26ms | 3.1× |
| 10 | 94.7% | 0.82ms | 1.0× |
| 20 | 96.0% | 1.41ms | 0.6× |
| **50** | 98.3% | 5.24ms | **0.2×** |

**Checking just 1 of 100 clusters already recovers 84.7% of the true top-10** — most of a query's true
nearest neighbours are concentrated in its nearest cluster, because the underlying data genuinely has
topic structure. **Recall rises steadily as `nprobe` grows, approaching but never quite reaching 100%.**
And the last row is the sharpest, least intuitive result: **`nprobe=50` is measured as *slower* than
exact search itself** (0.2× — one fifth the speed) — checking half the clusters, plus the overhead of the
centroid comparison step, costs more than simply scanning the whole corpus directly. **An approximate
method configured too conservatively is not merely wasteful; it can be worse than the exact method it was
meant to speed up.**

### 5.3 A graph search, traced completely by hand

`[REAL]` §7.3 built an 8-node graph in 2D, with edges connecting each node to its true nearest
neighbours (computed exactly, then symmetrised), and traced a greedy search from a fixed entry point:

```
Start: A (distance to query: 6.000)
A -> C (4.177, closer)  ->  D (2.766, closer)  ->  E (1.000, closer)  ->  H (0.447, closer)
H's neighbours (E: 1.000, G: 2.302) -- neither closer than H (0.447) -- STOP
```

**Found: H. True nearest (checking all 8 nodes): H. Match.** Only **5 of 8 nodes** were ever compared to
the query — at real scale (millions of nodes, multiple layers, more edges per node) this is the exact
mechanism that makes HNSW's query time sub-linear: it never scans the graph, only a short greedy path
through it.

### 5.4 Two families, two different failure modes

| | IVF (clustering) | HNSW (graph) |
|---|---|---|
| Structure built | Partition corpus into clusters | Connect each vector to nearby neighbours |
| Query-time work | Compare to centroids, search nearest cluster(s) | Greedily walk the graph toward the query |
| Tunable trade-off knob | `nprobe` — how many clusters to check | `ef` — how many candidates to explore |
| Failure mode | Miss a match that landed in a **different cluster** | Reach a **local minimum**: no neighbour looks closer, but a closer node exists elsewhere |
| Real mitigation | Increase `nprobe`, or cluster more carefully | Multiple graph layers, multiple entry points (not shown in §7.3's single-layer example) |

**Neither failure mode is a defect to be embarrassed about — both are the direct, predictable cost of not
checking every vector**, which is precisely what exact search (M6-L05) guarantees and approximate methods
deliberately give up.

### 5.5 Assumptions and limitations

- §7.1–7.2's corpus is synthetic, generated with explicit topic structure to be *representative* of real
  embeddings' genuine clustering behaviour — not a measurement of any specific real embedding model or
  corpus. Recall numbers on your own data will differ; re-measure before choosing `nprobe`.
- §7.3's graph is 8 hand-verified nodes, illustrating the search *mechanism* only. Real HNSW builds its
  graph automatically at construction time, uses multiple hierarchical layers, and has its own
  construction parameters (`M`, `ef_construction`) not implemented here.
- This lesson does not cover how to choose between IVF-style and graph-based indexes for a real system —
  both are real, deployed families with different trade-offs (M6-L08 covers pgvector's actual support for
  these).

---

## 6. Worked example — the index tuned once, at launch, and never revisited

**The system.** A team deploys an IVF-style vector index for a document search feature, tunes `nprobe`
once during initial testing against a small, hand-picked set of queries, achieves what looks like
acceptable recall, and ships.

**What happened over the following year.** The corpus grew 10× as more documents were ingested, but
cluster count and `nprobe` were never revisited. Recall degraded gradually — each cluster now held far
more documents than it did at launch, so the same `nprobe` value now covered a much smaller *proportion*
of the corpus than it did originally, exactly as §5.2's table would predict if corpus size (and therefore
effective coverage per cluster) had shifted.

**Why nobody noticed immediately.** Recall degradation is not a crash or an error — it looks exactly like
"the search is a little less good than it used to be," easy to attribute to content growth, query
variety, or nothing in particular, rather than to a specific, measurable, fixable parameter.

**Three defects:**

| # | Defect | Consequence |
|---|---|---|
| 1 | `nprobe` tuned once, against a small query set, never re-measured | No process existed to catch drift as the corpus grew |
| 2 | Recall was never tracked as a monitored metric | The degradation had no alarm, only a vague, unattributed sense of declining quality |
| 3 | Cluster count was never revisited as corpus size changed | The index's structure itself became stale, not just its `nprobe` setting |

### The fix

**Track recall@k as an ongoing production metric**, not a one-time launch check — measured the same way
§7.2 measured it, periodically, against a stable set of exact-search ground-truth queries.

**Re-tune `nprobe` (and reconsider cluster count) as the corpus grows**, since §5.2's whole table shifts
as `N` changes — a value that was appropriate at launch is not guaranteed to remain appropriate
indefinitely.

**Treat index parameters as configuration that ages**, the same discipline M5-L12 established for
prompts and M6-L02 established for embedding models — a value chosen once, under one set of conditions,
needs periodic re-validation, not permanent trust.

**The general rule.** **An approximate index's accuracy is not a fact you establish once at launch — it
is a measurement that must be repeated as the data it indexes changes, because the index's own structure
was built for a corpus that no longer exists once the corpus has grown.**

---

## 7. Practical activity

**File:** [`labs/m6/l06_approximate_nn_hnsw.py`](../../labs/m6/l06_approximate_nn_hnsw.py)

**No API key, no network.** Expect the run to take roughly 10–30 seconds (real k-means clustering).

```bash
source .venv/bin/activate
python labs/m6/l06_approximate_nn_hnsw.py
```

Sections 1–2 build and query a real clustering-based index. Section 3 is a small, fully hand-verifiable
graph search.

### 7.2 Expected output

`[EXECUTED, machine-specific timings]` — 2026-09-09, Python 3.10.11, NumPy 2.2.6, scikit-learn 1.7.2.

```text
============================================================================
1. A REAL APPROXIMATE INDEX: CLUSTER FIRST, SEARCH ONLY THE NEAREST CLUSTERS
============================================================================
  50,000 vectors, 128 dimensions -- the same shape of problem M6-L05
  measured exact search's cost for. Generated with 200 genuine
  underlying topics (vectors scattered around 200 random centres),
  the way real document embeddings cluster by subject -- NOT pure
  unstructured noise, which has no exploitable structure for any
  clustering-based index to find.

  Building a real k-means index: 100 clusters over 50,000 vectors (this takes a few seconds)...
  Index built in 6.2s. Average cluster size: 500 vectors.

  The index: at query time, compare against the 100 CENTROIDS first
  (cheap), then exact-search only inside the closest cluster(s) --
  never touching the other clusters' vectors at all.

============================================================================
2. RECALL vs SPEED: A REAL, TUNABLE TRADE-OFF
============================================================================
  30 queries, drawn from the same topic structure as the corpus
  (a realistic query resembles the kind of content it searches for).
  For each, exact search gives the TRUE top-10 (M6-L05's method) --
  the ground truth every recall number below is measured against.

   nprobe  avg recall@10   time/query  speedup vs exact
        1          84.7%       0.09ms              8.7x
        2          87.7%       0.14ms              5.7x
        5          93.0%       0.26ms              3.1x
       10          94.7%       0.82ms              1.0x
       20          96.0%       1.41ms              0.6x
       50          98.3%       5.24ms              0.2x

  Exact search (M6-L05's method), for comparison: 0.79ms/query, 100% recall by definition.

  Read left to right: checking only 1 cluster is fast but misses real
  matches -- recall well under 100%. Checking more clusters (larger
  'nprobe') raises recall back toward exact search's, at the cost of
  approaching exact search's own time. THIS is the trade-off every
  approximate method makes, HNSW included -- nprobe here plays the
  same role as HNSW's 'ef' search-width parameter: how hard to look
  before stopping.

============================================================================
3. HNSW'S DIFFERENT MECHANISM: A GRAPH, TRACED BY HAND
============================================================================
  A different ANN family: instead of clusters, build a graph where
  each vector is a node connected to a few nearby neighbours, and
  search by GREEDILY walking toward the query, one hop at a time.

  8 nodes, each connected to its nearest neighbours (a symmetrised k-NN graph). Query point: (4.8, 3.6).

  node  coords      distance to query
  A     (0, 0)      6.000
  B     (1, 0.2)    5.099
  C     (2, 0.5)    4.177
  D     (3, 1.5)    2.766
  E     (4, 3.0)    1.000
  F     (1, 3.0)    3.847
  G     (2.5, 3.5)  2.302
  H     (5, 4.0)    0.447

  True nearest node (by checking all 8, i.e. exact search): 'H'

  Greedy graph search, starting at 'A': visits ['A', 'C', 'D', 'E', 'H'] (5 of 8 nodes),
  then stops because no neighbour of 'H' is closer than 'H' itself.
  Found: 'H'. True nearest: 'H'. Match: True.

  Only 5 of 8 nodes were ever compared to the
  query -- at real scale (millions of nodes, more layers, more edges
  per node) this is what makes HNSW sub-linear: it never scans the
  whole graph, only a short greedy path through it, layer by layer.

  The failure mode is different from clustering's. IVF search (sections 1-2)
  can miss the right answer by checking the wrong CLUSTER. A graph
  search can miss it by reaching a LOCAL MINIMUM -- a node with no
  closer neighbour, even though a closer node exists elsewhere in the
  graph, unreachable from the greedy path taken. Real HNSW mitigates
  this with multiple layers and multiple entry points, not shown in
  this single-layer, hand-traced example.

============================================================================
4. WHAT THIS LAB IS AND IS NOT
============================================================================
  REAL: sections 1-2 build and query an actual clustering-based
  approximate index (the same family as IVF-Flat in real vector
  databases) using real k-means and real brute-force sub-search, and
  measure real recall against real exact-search ground truth (M6-L05).

  HAND-TRACED, NOT A FULL IMPLEMENTATION: section 3's graph is 8
  nodes with manually assigned edges, illustrating HNSW's core greedy-
  search MECHANISM. Real HNSW builds its graph automatically, uses
  multiple hierarchical layers, and includes construction-time
  choices (M, ef_construction) this lab does not implement.

  ILLUSTRATIVE: exact recall/speed numbers depend on this specific
  corpus, cluster count, and hardware. Re-measure on your own data
  before choosing nprobe or any ANN parameter for a real system.

  NOT SHOWN: how to choose between IVF-style and graph-based (HNSW)
  indexes for a real system -- both are real, deployed families with
  different trade-offs, and pgvector (M6-L08) supports both.

Done.
```

### 7.3 Reading the result

**Section 2's `nprobe=1` row is the number worth remembering: 84.7% recall for an 8.7× speedup.** This is
why clustering-based ANN works in practice — real data has real structure, and a query's true neighbours
are disproportionately concentrated near the query's own cluster, not scattered evenly across all of
them.

**The `nprobe=50` row is the number worth remembering for a different reason.** More thoroughness is not
free, and past a point it is not even a good trade — 0.2× speedup means this "approximate" configuration
is *five times slower* than simply not using the index at all. Tuning an ANN parameter is not "more is
safer;" it has a real cost curve with a real optimum.

**Section 3's 5-of-8 result is small enough to feel almost trivial — and that is deliberate.** The
mechanism that saves 3 comparisons out of 8 here is the same mechanism that saves millions of comparisons
out of billions at real production scale. Verifying it by hand at a scale small enough to check every
number is what makes the larger claim trustworthy.

---

## 8. Common mistakes and troubleshooting

1. **Assuming more `nprobe` (or `ef`) is always safer.** §5.2 measured a configuration that was slower
   than exact search itself.
2. **Tuning an ANN parameter once and never revisiting it.** §6 — recall degrades silently as the corpus
   grows.
3. **Not tracking recall@k as an ongoing metric.** Without it, degradation looks like vague quality
   decline with no clear cause.
4. **Testing an ANN index against unstructured random data and concluding it "doesn't work well."** Real
   embeddings have real cluster structure (§5.1); the method's effectiveness depends on that structure
   existing.
5. **Treating IVF and HNSW's failure modes as interchangeable.** §5.4 — "wrong cluster" and "local
   minimum" are genuinely different failures with different mitigations.
6. **Discarding exact search once an approximate index is live.** It remains the only way to measure the
   approximate index's actual recall (M6-L05 §5.4).
7. **Assuming a hand-traced 8-node graph result generalises numerically.** The mechanism generalises; the
   specific ratio of nodes visited does not (§5.5).

| Symptom | Likely cause | Fix |
|---|---|---|
| Search quality degrades gradually over months | Corpus grew, index parameters never re-tuned | Re-measure recall@k periodically; re-tune `nprobe`/cluster count (§6) |
| An "approximate" search is barely faster, or slower, than exact | `nprobe`/`ef` set too high | Measure the recall-speed curve (§7.2) and pick a value with real headroom |
| Recall is surprisingly poor on a test corpus | Corpus lacks real structure (e.g. synthetic random noise) | Verify on data with genuine structure, or accept that unstructured data limits any clustering-based method |
| Approximate search occasionally returns a clearly wrong top result | Local minimum (graph) or wrong-cluster (IVF) miss | Increase `ef`/`nprobe`; consider multiple entry points or better clustering |

---

## 9. Security, privacy, reliability, cost

- **Reliability.** Track recall@k as an ongoing production metric, not a one-time launch check — an
  index's accuracy can degrade silently as the corpus grows (§6).
- **Cost.** An over-tuned `nprobe`/`ef` value can cost more than exact search itself (§5.2) — measure the
  actual curve rather than assuming "more thorough" means "better."
- **Reliability.** Keep exact search available as a ground-truth tool even after deploying an
  approximate index — it is the only way to measure whether the approximate index is still performing as
  expected (M6-L05 §5.4).
- **Reliability.** Know which failure mode your chosen method has (wrong cluster vs local minimum) —
  they call for different mitigations and different monitoring signals (§5.4).

---

## 10. Exercises

### Exercise 1 — Beginner (~20 min)

1. In one sentence, what does an approximate nearest-neighbour method give up, and what does it gain?
2. Why does `nprobe=1` still achieve high recall on realistic (topic-structured) data?
3. What does "recall@k" measure, and what is it measured against?
4. In your own words, what is a local minimum in graph-based search?
5. Why does exact search remain useful after an approximate index is deployed?

### Exercise 2 — Intermediate (~40 min)

1. Run the lab. Report your own machine's recall@10 and speedup at `nprobe=5`.
2. Change `N_CLUSTERS` to 25 and to 400, and report how the recall-vs-`nprobe` curve changes at each.
3. Change `N_TOPICS` to be much closer to `N_CLUSTERS` (e.g. 100) and explain how you expect recall at
   low `nprobe` to change, then verify by running it.
4. Trace the greedy graph search in §7.3 by hand starting from a different entry node (e.g. `F`), and
   report whether it still finds the true nearest neighbour.
5. Design a monitoring plan (metrics and thresholds) for recall@k in a production ANN index.

### Exercise 3 — Challenge (~50 min)

1. Implement `recall@k` as a reusable function and use it to compare two different clustering approaches
   (e.g. k-means vs random partitioning) on the same corpus.
2. Build a slightly larger hand-traceable graph (15–20 nodes) with at least one genuine local-minimum
   case, and demonstrate the greedy search failing to find the true nearest neighbour from some entry
   points but not others.
3. Implement a simple two-layer graph search (a small "upper layer" with fewer nodes for a fast initial
   approximate location, then a "lower layer" for refinement) and compare its accuracy and node-visit
   count to the single-layer version.
4. Research (conceptually) how real HNSW's construction parameters (`M`, `ef_construction`) affect the
   resulting graph's quality, and write up the trade-offs.
5. Write a decision memo comparing IVF-style and graph-based indexing for a specific real or hypothetical
   system, including which recall/latency target you would set and how you would monitor it in
   production.

---

## 11. Quiz

*(Answers: [`answer-keys/module-06-answers.md`](../../answer-keys/module-06-answers.md#m6-l06).)*

**Q1.** In §7.1–7.2, the corpus was generated from 200 underlying "topics" rather than pure random
noise, because:

- A. Random noise is computationally more expensive to generate.
- B. Pure random noise has no exploitable structure for a clustering-based index to find, unlike real document embeddings which genuinely cluster by subject.
- C. K-means cannot run on random data at all.
- D. The lab required exactly 200 vectors for technical reasons.

**Q2.** In §7.2, checking just `nprobe=1` of 100 clusters achieved 84.7% recall at an 8.7x speedup. This
shows:

- A. IVF indexes are always at least 84.7% accurate regardless of data.
- B. Recall does not depend on how many clusters are checked.
- C. The corpus contained exactly 84.7% duplicate vectors.
- D. Even a minimal search of the index found most of the true nearest neighbors, because they were concentrated in the query's nearest cluster.

**Q3.** In §7.2, `nprobe=50` was measured as slower than exact search (0.2x speedup) despite still being
approximate. This happened because:

- A. Checking half the clusters, plus the overhead of comparing against centroids first, cost more than just scanning the whole corpus directly.
- B. The k-means index became corrupted at high nprobe values.
- C. Exact search was run twice by mistake at that setting.
- D. Recall dropped to zero at nprobe=50.

**Q4.** The `nprobe` parameter in the lab's IVF-style index plays the same role as:

- A. BM25's `k1` parameter.
- B. The number of dimensions in an embedding.
- C. HNSW's "ef" search-width parameter — both control how hard the algorithm searches before stopping, trading speed for recall.
- D. The corpus size itself.

**Q5.** In §7.3, the greedy graph search started at node A and visited 5 of 8 nodes before stopping. It
stopped because:

- A. It ran out of allowed search time.
- B. It had visited exactly 5 nodes, a fixed limit.
- C. Node A's original neighbours were all removed from the graph.
- D. It reached a node (H) with no neighbor closer to the query than itself.

**Q6.** What is a "local minimum" failure in graph-based ANN search, per §5.3?

- A. A node with too many edges to search efficiently.
- B. The search reaches a node whose neighbors are all farther from the query than itself, even though a closer node exists elsewhere in the graph, unreachable from the path taken.
- C. A cluster with fewer than the average number of members.
- D. A query vector with unusually small magnitude.

**Q7.** How does the failure mode of clustering-based (IVF) search differ from graph-based (HNSW) search,
per §5.4?

- A. IVF never fails; only graph search can miss the true answer.
- B. Graph search never fails; only IVF can miss the true answer.
- C. IVF can miss the right answer by searching the wrong cluster; graph search can miss it by reaching a local minimum along the wrong path.
- D. Both methods fail in exactly the same way, for the same reason.

**Q8.** Section 3's graph example is described as:

- A. A small, hand-traced illustration of HNSW's core search mechanism, not a full implementation of how HNSW builds its graph or uses multiple layers.
- B. A complete, production-ready implementation of HNSW.
- C. Mathematically unrelated to how real HNSW works.
- D. A clustering-based method identical to section 1's IVF index.

**Q9.** Why did the corrected, topic-structured corpus produce dramatically higher recall than an
earlier, pure-random-noise version would have?

- A. Topic-structured data has fewer total vectors.
- B. True nearest neighbors were concentrated within a query's own topic, which closely aligned with a small number of k-means clusters.
- C. Random noise vectors are always closer together than structured vectors.
- D. The topic-structured corpus disabled the exact-search ground truth calculation.

**Q10.** The general trade-off this lesson establishes for approximate nearest-neighbor search is:

- A. Checking less of the corpus trades a small, measurable, tunable amount of accuracy for a potentially large speed gain.
- B. Approximate methods are always both faster and more accurate than exact search.
- C. There is no meaningful difference between exact and approximate search in practice.
- D. Accuracy is entirely unrelated to how much of the corpus is checked.

**Q11.** Per M6-L05's forward reference, exact search's role after an approximate index is deployed is:

- A. It becomes entirely unnecessary and should be removed.
- B. It is only used once, at initial index construction.
- C. Providing the ground-truth top-k that the approximate index's recall is measured against.
- D. It replaces the approximate index whenever nprobe is set below 10.

**Q12.** Why does the lesson caution against quoting this lab's specific recall/speed numbers for a
different, real system?

- A. The numbers are randomly generated and change on every run.
- B. Recall and speed cannot be measured in any system.
- C. Real systems never use clustering or graph-based indexes.
- D. The numbers depend on this specific synthetic corpus, cluster count, and hardware, and must be re-measured on real data before being used to choose parameters.

**Q13.** *(Written, rubric-graded.)* In under 150 words: a colleague proposes setting `nprobe` (or `ef`)
as high as possible "to be safe," reasoning that more thorough search can only help. State what this
lesson's lab found that contradicts that reasoning, and what you would propose instead.

---

## 12. Revision notes

- **Approximate search deliberately avoids comparing against every vector**, trading a controlled,
  measurable amount of accuracy for query time that does not scale linearly with corpus size.
- **A clustering-based (IVF) index is real and simple**: partition the corpus, compare to centroids first,
  search only the nearest cluster(s). Measured: 84.7% recall at `nprobe=1`, an 8.7× speedup, on
  realistic topic-structured data.
- **The recall-speed trade-off has a real, measurable curve — and a real optimum, not "more is always
  safer."** Measured: `nprobe=50` was five times *slower* than exact search itself.
- **Realistic (topic-structured) data is what makes clustering-based ANN work.** Pure unstructured
  random vectors give a clustering index nothing to exploit.
- **HNSW's graph search is a different mechanism with a different failure mode.** Measured, by hand: a
  greedy walk visiting 5 of 8 nodes correctly found the true nearest neighbour; its risk is a local
  minimum, not a wrong cluster.
- **Exact search does not retire once an approximate index exists.** It remains the ground truth every
  recall measurement in this lesson depends on.
- **Tune ANN parameters against your own data, and re-measure as that data changes.** A value that was
  correct at launch is not guaranteed to remain correct as the corpus grows (§6).

---

## 13. Completion checklist

- [ ] I can build and query a real clustering-based approximate index.
- [ ] I can measure recall@k against exact-search ground truth.
- [ ] I understand that more thorough search (`nprobe`/`ef`) has a real cost curve, not unlimited benefit.
- [ ] I can trace a greedy graph search by hand and identify its stopping condition.
- [ ] I can distinguish IVF's "wrong cluster" failure from HNSW's "local minimum" failure.
- [ ] I know why exact search remains necessary after deploying an approximate index.
- [ ] I would re-measure recall@k periodically, not just once at launch.
- [ ] I scored 10/13 on the quiz.

---

## 14. References

- Malkov, Y. A. and Yashunin, D. A. (2016), *Efficient and Robust Approximate Nearest Neighbor Search
  Using Hierarchical Navigable Small World Graphs*. <https://arxiv.org/abs/1603.09320> `[UNVERIFIED]`
- Jégou, H., Douze, M., and Schmid, C. (2011), *Product Quantization for Nearest Neighbor Search* (a
  related family of ANN methods, for context). <https://ieeexplore.ieee.org/document/5432202>
  `[UNVERIFIED]`
- scikit-learn documentation — `sklearn.cluster.KMeans` (used in this lab's real index).
  <https://scikit-learn.org/stable/modules/generated/sklearn.cluster.KMeans.html> `[UNVERIFIED]`

---

## 15. Next lesson

→ [M6-L07 — Vector Indexes vs Vector Databases](M6-L07-vector-indexes-vs-databases.md)

You now understand what approximate search buys and costs, at the level of the algorithm itself. Next:
where that algorithm actually lives in a real system — the difference between a library that builds an
index in memory and a database that manages one for you.
