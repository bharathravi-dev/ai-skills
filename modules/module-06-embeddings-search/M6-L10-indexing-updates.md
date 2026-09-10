# M6-L10 — Indexing, Updates, Deletion and Re-embedding

| | |
|---|---|
| **Lesson ID** | M6-L10 |
| **Difficulty** | 2 (Intermediate) |
| **Estimated study time** | 1.75 hours |
| **Prerequisites** | [M6-L08](M6-L08-pgvector-hands-on.md) |

---

## 1. Learning objectives

1. **Measure** how index recall changes across three real states: never updated, incrementally updated,
   and fully rebuilt.
2. **Explain** why incremental addition is cheap but can leave an index's structure reflecting an
   outdated distribution.
3. **Explain** why an embedding-model upgrade requires a full, atomic index migration, not an
   incremental one.
4. **Design** a blue-green migration pattern for re-embedding a production corpus.
5. **Connect** this lesson to M6-L07's deletion cost, as two halves of one index lifecycle.

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **Incremental addition** | Adding new vectors to an existing index by assigning them to existing structure (e.g. nearest centroid), without a full rebuild. |
| **Cluster drift** | An index's cluster structure becoming a progressively worse fit for the corpus as new data is added without rebuilding. |
| **Re-embedding** | Recomputing every vector in a corpus under a new or upgraded embedding model. |
| **Blue-green index migration** | Building a new index fully alongside the old one and cutting over atomically, rather than updating in place. |
| **Atomic cutover** | Switching all traffic from one system to another at a single point in time, never gradually, to avoid a mixed, inconsistent state. |

---

## 3. Plain-language explanation

### 3.1 M6-L07 measured half of a lifecycle; this lesson measures the other half

M6-L07 measured what deleting from an approximate index actually costs — a choice between a fast,
incomplete tombstone and a correct, expensive rebuild. **Adding** data has the same shape of choice, and
**changing the embedding model entirely** is a third, distinct operation with its own requirements. This
lesson measures both.

### 3.2 Adding data cheaply is not the same as adding it correctly

An IVF index (M6-L06) can absorb a new vector almost instantly — just assign it to whichever existing
cluster centroid is closest. §7.1 measures exactly what this buys and what it costs: real, fast, and
searchable, but built on cluster boundaries that reflect the corpus as it existed *before* the new data
arrived.

### 3.3 New data is often not just "more of the same"

The gap between "cheap update" and "full rebuild" is easy to underestimate if you assume new content
closely resembles old content. §7.1's experiment is designed around the more realistic case: a growing
corpus often introduces genuinely new subjects, not merely more examples of subjects the index already
knew about — and that is exactly when stale cluster structure costs the most.

### 3.4 A model upgrade is not an update at all — it is a migration

M6-L02 already established that two embedding models produce incompatible vector spaces. There is no
"incremental" version of switching models: every vector must be recomputed, and the entire index rebuilt,
with an explicit plan for what serves traffic while that happens.

---

## 4. Analogy

**A library that keeps adding new books to existing shelves, versus one that occasionally
re-catalogues.** Slotting a new book onto the shelf nearest its rough subject is fast and keeps the
library open. Do this for long enough, especially as genuinely new subjects arrive that the original
shelving plan never anticipated, and the shelving stops reflecting the collection well — not broken, just
increasingly approximate. Periodically re-cataloguing the whole collection from scratch fixes this, at
the cost of closing the relevant section while it happens.

Now imagine the library switches to an entirely new classification system (Dewey Decimal to Library of
Congress, say). There is no way to have "half the books" under one system and "half" under the other on
the same shelves at once — a patron's call number means something different depending on which system
produced it. The only sane approach is to build the new catalogue completely, in parallel, and switch the
whole library over at a single point in time.

### Where the analogy breaks

- **A librarian can judge, by eye, when shelving has drifted too far.** An index's cluster drift is
  invisible without deliberately measuring recall (§7.1) — nothing about a degraded index looks wrong on
  inspection.
- **Re-cataloguing a physical library takes it offline.** A blue-green migration (§5.2) exists precisely
  to avoid this — the old system keeps serving every request throughout.

---

## 5. Detailed technical explanation

### 5.1 Three states of the same index, measured

`[REAL]` §7.1 grew a corpus from 25,000 to 50,000 vectors — with the added half genuinely introducing new
topics the original index never saw — and measured recall@10 against the same queries in three states:

| State | What happened | Recall@10 |
|---|---|---|
| **A** — never updated | The newer 25,000 vectors were simply never added | **49.0%** |
| **B** — incrementally added | New vectors assigned to the nearest *existing* centroid, no rebuild (19.5ms total) | **84.5%** |
| **C** — fully rebuilt | k-means re-fit on all 50,000 vectors (6.5s) | **86.5%** |

**Read State A first: roughly half the true answers are simply unreachable** — not a search-quality
problem, an availability one. **State B recovers the overwhelming majority of that loss for a
near-zero cost** — going from "half searchable" to "almost as good as a full rebuild" took milliseconds.
**State C's remaining 2-point gain came from correctly-placed cluster centroids that reflect the true,
final topic distribution** — a real, if comparatively modest, improvement over State B, at the cost of a
measured, non-trivial rebuild.

**The practical reading: adding data cheaply is far better than not adding it at all, and meaningfully
short of a full rebuild.** Neither extreme is free to ignore.

### 5.2 Re-embedding: not an update, a migration

`[REAL arithmetic, extending this run's own measured rebuild rate]` §7.2 extrapolated rebuild cost to
larger corpora:

| Corpus size | Estimated rebuild time |
|---|---|
| 100,000 | 0.2 min |
| 1,000,000 | 2.2 min |
| 10,000,000 | 21.5 min |

**This is the rebuild step alone** — a real migration also pays to re-embed every document through the
new model, a separate and often larger cost this lesson does not measure directly. Because this takes
real, non-trivial time, and the service cannot stop answering queries meanwhile, the standard pattern is:

1. **Build the new index fully, alongside the old one.** The old index keeps serving every query
   throughout.
2. **Validate the new index's recall against a held-out query set** (M5-L18's discipline, applied here)
   before trusting it.
3. **Cut traffic over atomically, only once validated** — never gradually, since a query answered by the
   old index and one answered by the new index come from two genuinely incompatible vector spaces
   (M6-L02), not two versions of the same answer.
4. **Decommission the old index only after the cutover is confirmed stable.**

**This is a blue-green deployment, applied to a vector index specifically because M6-L02's incompatibility
rules out any safe partial or gradual state.**

### 5.3 The full lifecycle, in one place

| Operation | Cheap option | Correct option | This lesson / M6-L07 |
|---|---|---|---|
| Delete | Tombstone (instant, incomplete) | Rebuild (correct, costly) | M6-L07 |
| Add | Nearest-centroid assignment (instant, approximate) | Rebuild (correct, costly) | This lesson §5.1 |
| Change model | *(no cheap option exists)* | Full re-embed + rebuild + atomic cutover | This lesson §5.2 |

**Delete and add share the same shape of trade-off** — a fast, approximate option and a correct,
expensive one. **Changing the embedding model has no cheap option at all** — it is categorically a
different kind of operation, requiring a migration process, not a maintenance task.

### 5.4 Assumptions and limitations

- §7.1's specific recall percentages depend on this lab's synthetic topic structure, corpus size, and
  the chosen split between "old" and "new" topics — real corpora and real drift patterns will differ.
  Measure your own before relying on any specific number here.
- §7.2's extrapolation scales only the k-means rebuild step measured directly; it does not include
  embedding-model inference cost, which is frequently the larger part of a real re-embedding migration.
- This lesson does not cover how to detect, in production, that incremental-only updates have degraded
  recall enough to justify a rebuild — that is a monitoring design choice specific to your own system.

---

## 6. Worked example — the search feature that quietly got worse for a year

**The system.** A document search feature launches with a well-tuned IVF index. New documents are added
daily via nearest-centroid assignment (§5.1's State B) — fast, simple, and it never breaks. The index is
never rebuilt after launch.

**What happened over the following year.** The organisation's focus shifted; entire new categories of
documents were added that barely existed at launch. Search quality for these newer categories was
consistently, quietly worse than for the original content — not absent, just noticeably less reliable —
while nobody could point to a specific incident, because nothing ever errored.

**Why it went unnoticed for so long.** Recall degradation from cluster drift looks exactly like "search is
a bit worse for this newer stuff," which is easy to attribute to the content itself, to user expectations,
or to nothing in particular — never to a specific, measurable, fixable cause, unless someone specifically
measures recall the way §7.1 did.

**Three defects:**

| # | Defect | Consequence |
|---|---|---|
| 1 | Only incremental addition was ever used, with no scheduled rebuild | Cluster structure kept drifting further from the corpus's true, evolving distribution |
| 2 | No recall metric was tracked over time | The gradual degradation had no signal to trigger investigation |
| 3 | Nobody had budgeted a periodic rebuild as a normal operational cost | The eventual full rebuild felt like an emergency fix rather than routine maintenance |

### The fix

**Schedule periodic full rebuilds**, not only reactive ones — treat this the same way M6-L07 argued for
deletion: batch and schedule the expensive-but-correct operation rather than deferring it indefinitely.

**Track recall@k over time as a production metric**, the same discipline M6-L06 established for
approximate-search quality generally, specifically watching for drift as new content categories emerge.

**Budget rebuild cost as routine operational overhead**, sized using §5.2's extrapolation method against
your own corpus growth rate, rather than discovering it unplanned.

**The general rule.** **Incremental addition is a maintenance convenience, not a substitute for
periodically re-deriving an index's structure from the data it actually contains now** — and the gap
between the two grows exactly when new content stops resembling old content, which is precisely when it
matters most.

---

## 7. Practical activity

**File:** [`labs/m6/l10_indexing_updates.py`](../../labs/m6/l10_indexing_updates.py)

**No API key, no network.** Expect the run to take roughly 10–20 seconds (real k-means, twice).

```bash
source .venv/bin/activate
python labs/m6/l10_indexing_updates.py
```

### 7.2 Expected output

`[EXECUTED, machine-specific timings]` — 2026-09-10, Python 3.10.11, NumPy 2.2.6, scikit-learn 1.7.2.

```text
============================================================================
1. THREE STATES OF THE SAME INDEX, MEASURED AGAINST THE SAME QUERIES
============================================================================
  A corpus that grows from 25,000 to 50,000 vectors. Three
  ways the index could reflect that growth, all measured against
  the SAME 20 queries and the SAME ground truth (exact search
  over the full, final 50,000-vector corpus).

  Building the ORIGINAL index on the first 25,000 vectors only...
  Built in 3.0s.

  State A -- index never updated at all, 25,000 newer vectors simply never added:
    avg recall@10: 49.0%

  State B -- 25,000 new vectors added incrementally (assigned to nearest EXISTING centroid, 19.5ms total, no rebuild):
    avg recall@10: 84.5%

  State C -- full rebuild on all 50,000 vectors (6.5s):
    avg recall@10: 86.5%

  Read all three together. State A is the cost of forgetting to add
  new data at all -- half the corpus is searchable by NOBODY. State B
  is cheap (milliseconds) and searchable, but its centroids were
  computed on half the eventual data, so recall sits measurably below
  a full rebuild's. State C is correct, and costs real, measured
  seconds -- the same trade-off M6-L07 measured for deletion, now
  measured for the addition side of the same lifecycle.

============================================================================
2. RE-EMBEDDING: WHY YOU CANNOT MIX MODELS, AND WHAT MIGRATING COSTS
============================================================================
  M6-L02 measured that two embedding models -- or two versions of
  'the same' model -- produce INCOMPATIBLE vector spaces, even at
  identical dimensionality. Upgrading the embedding model therefore
  means every vector must be recomputed AND the index rebuilt --
  there is no partial or incremental version of this operation.

  Using this run's measured rebuild time as a baseline (6.5s for 50,000 vectors):

     corpus size   estimated re-embed+rebuild time
         100,000                           0.2 min
       1,000,000                           2.2 min
      10,000,000                          21.5 min

  (This scales the k-means REBUILD cost alone -- a real migration
  also pays to re-embed every document through the new model, a
  separate, often larger cost this lab does not measure.)

  Because this takes real, non-trivial time -- and the service
  cannot stop answering queries while it happens -- the standard
  pattern is NOT to rebuild in place:

    1. Build the NEW index (new embeddings, new model) alongside the
       OLD one, which keeps serving every query throughout.
    2. Validate the new index's recall against a held-out query set
       (M5-L18's discipline, applied to a vector index) before
       trusting it.
    3. Cut traffic over to the new index atomically, only once step 2
       passes -- never gradually, since a query landing on the OLD
       index and one landing on the NEW index are answered from two
       INCOMPATIBLE vector spaces (M6-L02), not two versions of one
       answer.
    4. Decommission the old index only after the cutover is confirmed
       stable.

  This is the vector-index-specific version of a blue-green
  deployment -- necessary here specifically because M6-L02's
  incompatibility means there is no safe partial or gradual state.

============================================================================
3. WHAT THIS LAB IS AND IS NOT
============================================================================
  REAL: section 1's three recall measurements and all timings are
  from actually building, updating, and querying real indexes over
  a real (if synthetic) corpus -- nothing is simulated.

  ILLUSTRATIVE: the specific recall percentages, corpus size, and
  timings are tied to this lab's synthetic data and this machine.
  Section 2's extrapolation reuses this run's measured rebuild rate;
  re-embedding cost (calling the model itself) is separate and often
  larger, and is not measured here at all.

  NOT SHOWN: how a real vector database automates the blue-green
  pattern internally, and how to detect, in production, that
  incremental-only updates (state B) have degraded recall enough to
  need a rebuild -- both are engineering choices specific to your
  own monitoring and operational setup.

Done.
```

### 7.3 Reading the result

**State A's 49.0% is the cost of an obvious mistake stated precisely** — forgetting to add new data at
all is functionally "half the corpus doesn't exist," a much more severe failure than any recall tuning
question.

**States B and C together are the lesson's real payoff.** Going from A to B (49.0% → 84.5%) is an
enormous gain for a near-zero cost. Going from B to C (84.5% → 86.5%) is a real but far smaller gain, for
a cost that is orders of magnitude higher (milliseconds versus seconds, and that gap only grows with
corpus size). **Both comparisons matter, and they point in different operational directions**: always
add new data, cheaply, immediately — and still schedule periodic full rebuilds, because the second gain,
while smaller per rebuild, compounds as drift accumulates over many additions.

**Section 2's extrapolation is a reminder that "just rebuild it" stops being a casual sentence at real
scale.** Twenty minutes at 10 million vectors, for the clustering step alone, is exactly the kind of
number that needs to appear in a migration plan before it appears in an incident.

---

## 8. Common mistakes and troubleshooting

1. **Never adding new data to an index at all.** §7.1's State A — an availability failure, not a quality
   one.
2. **Relying on incremental addition forever, with no scheduled rebuild.** §6 — drift accumulates
   silently as new content diverges from what the index was originally built on.
3. **Assuming incremental addition is "basically as good as" a rebuild.** §7.1 measured a real, if
   modest, gap — and it grows as new content becomes less like old content.
4. **Attempting to migrate embedding models incrementally, mixing old and new vectors.** M6-L02's
   incompatibility makes this silently wrong, not just awkward.
5. **Rebuilding an index in place, with no fallback, during a model migration.** Use the blue-green
   pattern (§5.2) so the service never goes down mid-migration.
6. **Cutting over to a new, re-embedded index without validating its recall first.** §5.2, step 2 — this
   is exactly M5-L18's evaluation discipline, applied to a vector index.
7. **Not tracking recall over time as a production metric.** Without it, drift from incremental-only
   updates is invisible until users notice (§6).

| Symptom | Likely cause | Fix |
|---|---|---|
| Newer documents seem consistently less findable than older ones | Cluster drift from incremental-only updates | Schedule periodic full rebuilds; track recall over time (§5.1, §6) |
| A "quick embedding model upgrade" caused widespread search quality issues | Old and new vectors mixed in one index | Use the blue-green migration pattern (§5.2); never mix incompatible vector spaces |
| A migration plan has no clear cost estimate | Rebuild time never measured or extrapolated | Measure your own rebuild rate and extrapolate to your real corpus size (§5.2) |
| Search quality degradation has no clear cause | No recall metric tracked over time | Add recall@k monitoring, the same way M6-L06 established for approximate search generally |

---

## 9. Security, privacy, reliability, cost

- **Reliability.** Add new data to an index immediately, even cheaply — never adding it at all is a
  severe availability failure, far worse than any recall degradation from deferred rebuilding (§7.1).
- **Reliability.** Schedule periodic full rebuilds as routine maintenance, not only as a reactive fix —
  cluster drift compounds silently as new content diverges from the original distribution (§6).
- **Reliability.** Never mix vectors from different embedding models or versions in one index — use an
  atomic, validated cutover (§5.2), never a gradual migration.
- **Cost.** Budget rebuild time using your own measured rate extrapolated to your actual corpus size
  (§5.2) — this scales with corpus size and needs to appear in migration planning, not just incident
  response.
- **Reliability.** Validate a newly re-embedded index's recall against a held-out query set before
  cutting traffic over (M5-L18's discipline) — do not trust a migration's correctness by assumption.

---

## 10. Exercises

### Exercise 1 — Beginner (~20 min)

1. In one sentence, why did State A (never updated) recall only about half the true results?
2. Why is incremental addition cheap, and what does it not fix?
3. Why can't an embedding-model upgrade be done incrementally, mixing old and new vectors?
4. Name the four steps of the blue-green index migration pattern.
5. Why does this lesson connect directly to M6-L07?

### Exercise 2 — Intermediate (~40 min)

1. Run the lab. Confirm the three recall percentages and report your own machine's rebuild time.
2. Change the split between old and new topics (e.g. make 90% of topics "new" in the added data instead
   of 25%) and report how the State B vs State C gap changes.
3. Measure recall after adding the new data in smaller increments (e.g. 25%, 50%, 75%, 100% of the added
   batch) without ever rebuilding, and plot the drift curve.
4. Using §5.2's extrapolation method, estimate re-embedding time for a corpus size relevant to a real or
   hypothetical system you have in mind.
5. Design a recall-monitoring plan (metric, frequency, alert threshold) that would have caught §6's
   incident earlier.

### Exercise 3 — Challenge (~50 min)

1. Implement a full blue-green migration for a small synthetic corpus: build an "old" index, an
   incompatible "new" index, validate the new one's recall, and perform an atomic cutover in code.
2. Implement a scheduled-rebuild policy (e.g. rebuild after every N additions, or when estimated drift
   exceeds a threshold) and justify the schedule with the same kind of measurement §7.1 used.
3. Extend the lab to model deletions happening alongside additions (combining this lesson with M6-L07),
   and measure recall under a realistic mixed add/delete workload over time.
4. Research (conceptually) how a real vector database exposes an "add" operation for an HNSW-type index,
   and compare its cost profile to the IVF nearest-centroid approach used in this lab.
5. Write the migration runbook for upgrading a production embedding model: validation criteria, rollback
   plan, and the specific point at which the cutover becomes irreversible.

---

## 11. Quiz

*(Answers: [`answer-keys/module-06-answers.md`](../../answer-keys/module-06-answers.md#m6-l10).)*

**Q1.** In §7.1, State A (index never updated at all) recalled only 49.0% on average. This is because:

- A. Half the corpus's vectors were never added to the index at all, so any true top-10 result among them was structurally impossible to find, regardless of search quality.
- B. The similarity metric was configured incorrectly.
- C. The embedding model produced identical vectors for different documents.
- D. Recall was measured against the wrong set of queries.

**Q2.** In §7.1, State B (incremental addition, no rebuild) recalled 84.5% while State C (full rebuild)
recalled 86.5%. This gap exists because:

- A. State B used a different distance metric than State C.
- B. State B's index contained fewer total vectors than State C's.
- C. State B's cluster centroids were computed only from the original data's topic distribution, which did not represent the newly introduced topics as well as centroids fit on the full, final distribution.
- D. State C used exact search instead of an approximate index.

**Q3.** Why did the corpus generation for this lab deliberately draw the initially-indexed vectors from a
SUBSET of topics, with new topics introduced only in the added data?

- A. To reduce the total computation time required.
- B. To match a specific pgvector configuration requirement.
- C. Because random number generation requires it.
- D. To realistically model that new content in a growing corpus often discusses genuinely new subjects, not merely a random resample of existing ones — the first version of the experiment, without this, showed almost no degradation.

**Q4.** Per §5.1, incrementally adding new vectors to an existing IVF index by assigning them to the
nearest existing centroid is:

- A. Always exactly as accurate as a full rebuild, with no trade-off at all.
- B. Cheap (milliseconds, no re-fit required) but can leave the index's cluster structure reflecting an outdated distribution.
- C. More expensive than a full rebuild in every case.
- D. Only possible for graph-based (HNSW) indexes, never clustering-based ones.

**Q5.** Why can't upgrading an embedding model be done incrementally, mixing old and new vectors in one
index, per §5.2?

- A. M6-L02 established that two embedding models (or versions) produce incompatible vector spaces, so a query against a mixed index would be comparing vectors that were never meant to be compared.
- B. It is technically possible but simply not recommended for stylistic reasons.
- C. Embedding models never change once deployed.
- D. Mixing vectors is only a problem for sparse retrieval, not dense embeddings.

**Q6.** The "blue-green" migration pattern described in §5.2 exists specifically because:

- A. It is required by PostgreSQL for any index change.
- B. It reduces the total storage needed for the corpus.
- C. It is the only way to compute cosine similarity correctly.
- D. There is no safe partial or gradual state when switching embedding models — the old and new indexes must each be internally consistent, with an atomic cutover between them.

**Q7.** Per §5.2's pattern, what should happen before cutting traffic over to a newly re-embedded index?

- A. The old index should be deleted immediately.
- B. Nothing; cutover can happen as soon as the new index finishes building.
- C. Its recall should be validated against a held-out query set, the same evaluation discipline M5-L18 established generally.
- D. The corpus size must be reduced by half.

**Q8.** Section 2's re-embed+rebuild time estimates reuse:

- A. Numbers published by a specific vector database vendor.
- B. This run's own measured k-means rebuild rate, extrapolated to larger corpus sizes — and explicitly exclude the separate cost of calling the embedding model itself.
- C. A theoretical estimate with no basis in any actual measurement.
- D. M6-L05's exact search timing rather than any clustering measurement.

**Q9.** The general relationship between this lesson and M6-L07 is:

- A. M6-L07 measured the cost of deletion from an approximate index; this lesson measures the other half of the same lifecycle — addition and model migration.
- B. This lesson contradicts M6-L07's findings about deletion cost.
- C. M6-L07 and this lesson cover entirely unrelated topics.
- D. This lesson replaces the need for anything M6-L07 taught.

**Q10.** What does this lesson explicitly leave to a team's own operational setup, per §7.3?

- A. The definition of recall@k.
- B. How cosine similarity is computed.
- C. The mathematics of k-means clustering.
- D. Detecting, in production, when incremental-only updates have degraded recall enough to justify a rebuild.

**Q11.** State A's 49% recall and State B's 84.5% recall together show that:

- A. Incremental addition provides no benefit over never updating the index at all.
- B. Simply making new data searchable at all (State B) recovers most of the loss from never adding it (State A), even before considering the smaller additional gain from a full rebuild (State C).
- C. State A and State B always produce identical recall.
- D. Recall is unrelated to whether new data has been added to the index.

**Q12.** The general practical rule this lesson establishes is:

- A. Never perform incremental updates; always rebuild the entire index for any change.
- B. Incremental updates are always sufficient and full rebuilds are never necessary.
- C. Adding data cheaply (without a rebuild) is far better than not adding it at all, but is not equivalent to a full rebuild — and a model change requires a full, validated, atomically-switched rebuild with no safe partial state.
- D. Embedding model upgrades can always be performed gradually without any special migration process.

**Q13.** *(Written, rubric-graded.)* In under 150 words: your team has been adding new documents to a
vector index incrementally for a year, with no rebuild, and search quality for recently-added content
categories has been quietly declining. Based on this lesson, what would you check, and what would you
propose?

---

## 12. Revision notes

- **Never adding new data to an index is a severe availability failure**, not a subtle quality issue.
  Measured: recall dropped to 49% when half the corpus was simply never added.
- **Incremental addition is cheap and recovers most of the loss from not updating at all.** Measured:
  recall rose from 49% to 84.5% for a near-zero (millisecond) cost.
- **Incremental addition still falls measurably short of a full rebuild**, because cluster structure
  reflects the distribution at the time of the last rebuild, not the corpus as it exists now. Measured:
  an additional 2-point recall gain from a full rebuild, at a cost orders of magnitude higher.
- **The gap between incremental and rebuilt grows as new content diverges from old content** — a
  realistic growing corpus, not a random resample of what already existed.
- **An embedding-model change is a migration, not an update — there is no cheap option.** M6-L02's
  incompatibility rules out mixing old and new vectors in one index at any point.
- **Blue-green migration (build new, validate, cut over atomically, decommission old) is the standard
  pattern** for a model change, specifically because no safe partial state exists.
- **Delete (M6-L07) and add (this lesson) share the same fast-vs-correct trade-off shape; model change
  does not** — it is categorically different, requiring a full migration process every time.

---

## 13. Completion checklist

- [ ] I can explain why never adding new data is worse than adding it incrementally without a rebuild.
- [ ] I understand that incremental addition is cheap but leaves cluster structure reflecting outdated data.
- [ ] I schedule periodic full rebuilds as routine maintenance, not only reactively.
- [ ] I know why an embedding-model change requires a full migration, never an incremental update.
- [ ] I can describe the blue-green index migration pattern and why atomic cutover matters.
- [ ] I validate a new index's recall before cutting traffic over to it.
- [ ] I track recall@k over time to catch cluster drift before users notice.
- [ ] I scored 10/13 on the quiz.

---

## 14. References

- pgvector — GitHub repository, on index maintenance and rebuilding.
  <https://github.com/pgvector/pgvector> `[UNVERIFIED]`
- Fowler, M., *BlueGreenDeployment* (the general pattern this lesson applies to vector indexes).
  <https://martinfowler.com/bliki/BlueGreenDeployment.html> `[UNVERIFIED]`

---

## 15. Next lesson

→ [M6-L11 — Hybrid Search and Reciprocal Rank Fusion](M6-L11-hybrid-search-rrf.md)

You now understand a vector index's full lifecycle — additions, deletions, and model migrations. Next:
combining the sparse and dense retrieval methods from M6-L03/M6-L04 into one system, using the specific
technique — reciprocal rank fusion — that makes combining two rankings principled rather than ad hoc.
