# M7-L16 — Incremental Updates and Deletion Propagation

| | |
|---|---|
| **Lesson ID** | M7-L16 |
| **Difficulty** | 3 (Advanced) |
| **Estimated study time** | 1.75 hours |
| **Prerequisites** | [M6-L10](../module-06-embeddings-search/M6-L10-indexing-updates.md), [M7-L08](M7-L08-metadata-provenance-versioning.md) |

---

## 1. Learning objectives

1. **Use** content-hash-based chunk identity (M7-L08) to identify exactly which chunks of an updated
   document actually need re-embedding.
2. **Demonstrate** that updating an index correctly does not guarantee a deletion or update has fully
   propagated through a real system.
3. **Implement** and detect an orphaned-reference bug, where a cache still serves a citation to a chunk
   that no longer exists.
4. **Implement** deletion propagation that invalidates downstream caches as part of the same operation
   that updates the index.
5. **Map** the full propagation chain a document change must travel through, beyond the index alone.

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **Propagation chain** | Every system — document store, index, caches, derived data — that must be kept consistent when a source document changes or is deleted. |
| **Content-hash change detection** | Comparing content-hash-based chunk IDs between document versions to identify exactly which chunks changed, are new, or are unchanged. |
| **Deletion propagation** | Ensuring a document's removal is reflected in every downstream system that referenced it, not only the primary index. |
| **Orphaned reference** | A stored reference (e.g. a cached citation) to a chunk ID that no longer exists in the current index. |
| **Same-event propagation** | Invalidating all downstream consumers of a piece of data as part of the single operation that changes it, rather than as a separate, easily-forgotten step. |

---

## 3. Plain-language explanation

### 3.1 M6-L10 measured index updates; this lesson measures everything else

M6-L10 measured, precisely, what it costs to add, delete, and rebuild a vector index. This lesson assumes
the index itself is handled correctly and asks a different question: is the index the *only* place a
document's identity lives? For any real system, the answer is no — and this lesson is about what happens
when that's forgotten.

### 3.2 Content hashes tell you exactly what changed

§7.2 reuses M7-L08's content-hash mechanism for a genuinely useful purpose beyond deduplication: comparing
an updated document's chunks against its previous version identifies precisely which chunks are new,
which are gone, and which are byte-for-byte unchanged — and only the changed ones need to be re-embedded
at all.

### 3.3 A correct index update can still leave a real bug behind

§7.3 is this lesson's central demonstration: deleting a document from the document store and index,
correctly and completely, still leaves a stale, broken citation sitting in a cache that nothing told to
update. The index being right doesn't mean the system is right.

### 3.4 The fix is propagating one event, not adding a second manual step

§7.4 doesn't fix this by remembering to also clear the cache separately — it computes the same set of
affected chunk IDs once, and uses that one set to update both the index and the cache, so there's no
second step to forget.

---

## 4. Analogy

**A company's employee directory, and everything that copies from it.** When an employee leaves, updating
the main HR system correctly removes them from the authoritative directory — but if the office's
printed floor-plan directory, the internal wiki's "team contacts" page, and an old onboarding email template
were never told, all three keep pointing a visitor toward someone who no longer works there. The HR system
being correct doesn't mean any of the downstream copies are. Fixing the HR system alone will never fix this
— every place that consumed a copy of that data needs its own update, triggered by the same departure
event, not remembered separately by whoever happens to maintain each copy.

### Where the analogy breaks

- **A human can eventually notice a stale printed directory and update it manually.** §7.3's cached
  citation gives no visible sign of being wrong — it looks exactly as valid as a correct one until someone
  checks whether its cited chunk still exists.
- **An office directory rarely needs to distinguish "this person changed roles" from "this person left
  entirely."** §7.2's content-hash comparison is specifically about the update case (some chunks changed,
  most didn't) as distinct from full deletion (§7.3–§7.4) — the propagation logic differs for each.

---

## 5. Detailed technical explanation

### 5.1 The full chain, beyond the index

`[REAL]` §7.1 names four places a chunk's identity can live: the document store, the chunk index (M6-L10's
territory), caches of previously generated answers (M7-L11/M7-L12's output), and any other derived data
keyed on chunk IDs. **This lesson's job is stages 3 and 4 — what M6-L10 didn't cover.**

### 5.2 Content-hash change detection, measured

`[REAL, measured]` §7.2 updated a PTO policy document (15 days → 20 days) and re-chunked both versions.
Comparing content-hash-based chunk IDs directly: **3 of 4 chunks were byte-for-byte identical (unchanged
hash); exactly 1 chunk changed** (the sentence containing the actual number). **Only that one chunk needs
re-embedding — the other three can be left untouched in the index entirely**, a real, measurable
efficiency gain from identity that reflects content rather than position (M7-L03's original argument,
applied here to updates specifically).

### 5.3 A correct deletion that still leaves a bug

`[REAL, measured]` §7.3 deleted a document using a function that correctly removes it from both the
document store and the index (M6-L10's own tombstone mechanism) — confirmed directly: the deleted
document's chunk is genuinely gone from the index. **But a cache holding a previously generated,
already-served answer was never touched by this deletion.** That cached answer still cites the now-deleted
chunk's exact ID. **A user re-asking the identical question would be served this cached answer, complete
with a citation pointing at nothing** — an orphaned reference, invisible until specifically checked for.
**The index update itself was correct and complete; the bug is that propagation to a separate downstream
system was never triggered by the same event.**

### 5.4 Propagating one event to every consumer

`[REAL, measured]` §7.4 implemented the fix: compute the set of chunk IDs being deleted *once*, then use
that same set to update both the index and to check every cache entry for a citation to any of those IDs.
The affected cache entry was correctly identified and removed **in the same operation**, not a
separately-remembered follow-up step. **This is the general fix pattern**: propagation should be driven by
a single, shared computation of "what changed," fanned out to every consumer, rather than each consumer
independently trying to notice the change on its own.

### 5.5 Assumptions and limitations

- This lab's "cache" is a single in-memory dictionary, standing in for whatever real caching layer a
  production system uses (query caches, CDN caches, precomputed summaries). The propagation *principle*
  generalizes; the specific structure here represents no one real technology.
- This lesson does not cover propagating *updates* (not just deletions) through a cache using the same
  content-hash detection from §5.2, nor a real event-driven architecture (e.g. a message queue) that would
  trigger propagation automatically across genuinely independent services.
- Re-embedding cost at real scale was already measured directly in M6-L10; this lesson focuses on
  *correctness* of propagation, not its cost.

---

## 6. Worked example — the support answer that cited a policy that no longer existed

**The system.** A support assistant caches generated answers for frequently asked questions, refreshing
the underlying index whenever source documents change, with cache entries expiring only after 30 days for
performance reasons.

**What went wrong.** A company retired an old benefits policy entirely, correctly removing it from the
document store and search index the same day. For the following three weeks, employees asking about that
exact benefit continued to receive a fluent, confidently-cited answer from the stale cache — the citation
pointed at a policy chunk that, by then, existed nowhere in the actual system.

**Why it took so long to notice.** Per §5.3, a stale cache entry gives no visible signal of being wrong —
it reads exactly like a correct, well-supported answer, and the cache's 30-day expiration meant the problem
would eventually self-resolve, which is precisely why it went unmonitored for that long.

**Three defects:**

| # | Defect | Consequence |
|---|---|---|
| 1 | Cache invalidation was never linked to document deletion or update events | Deleted or changed content remained servable from cache for up to 30 days |
| 2 | The cache's only staleness safeguard was a fixed time-based expiration | A deletion that happened the day after a cache entry was created still took nearly 30 days to clear |
| 3 | No process checked cached citations against the current index for validity | The orphaned reference was discovered by a user complaint, not by any internal check |

### The fix

**Trigger cache invalidation from the same event that updates the document store and index**, per §5.4 —
not from a separate, time-based expiration alone.

**Compute the affected chunk ID set once per change, and propagate it to every consumer**, per §5.4's
pattern, rather than relying on each downstream system to notice independently.

**Periodically validate cached citations against the current index**, per §5.3, as a safety net for any
propagation path not yet covered by event-driven invalidation.

**The general rule.** **A correctly updated index does not guarantee a correctly updated system — every
downstream consumer of chunk identity needs to be part of the same propagation event, or it will serve
stale, orphaned references for as long as its own independent staleness safeguard allows.**

---

## 7. Practical activity

**File:** [`labs/m7/l16_incremental_updates_deletion_propagation.py`](../../labs/m7/l16_incremental_updates_deletion_propagation.py)

**No API key, no network, no third-party dependencies.** Runs in well under a second.

```bash
source .venv/bin/activate
python labs/m7/l16_incremental_updates_deletion_propagation.py
```

### 7.2 Expected output

`[EXECUTED]` — 2026-09-10, Python 3.10.11 (pure standard library).

```text
============================================================================
1. THE PROPAGATION CHAIN: WHAT ACTUALLY HAS TO UPDATE
============================================================================
  A document changing or being deleted touches more than one place:
    1. The DOCUMENT STORE (M7-L03) -- the source of truth itself.
    2. The CHUNK INDEX (M6-L10) -- every chunk derived from that document.
    3. Any CACHES -- previously generated answers (M7-L11/M7-L12) that
       cited specific chunk IDs from the OLD version.
    4. Any DERIVED DATA -- precomputed related-document lists, summaries,
       or anything else keyed on a now-stale chunk ID.

  M6-L10 covered stage 2 (index tombstone vs. rebuild) in depth. This
  lesson covers the FULL chain -- specifically what happens when stage
  3 or 4 is forgotten while stage 2 is handled correctly.

============================================================================
2. CONTENT-HASH CHANGE DETECTION: WHICH CHUNKS ACTUALLY NEED RE-EMBEDDING
============================================================================
  PTO policy updated (15 days -> 20 days). Re-chunked into 4 sentence-level chunks, both versions:

  Chunk IDs unchanged (same content hash, same text): 3
    PTO#57333b68f3: 'Unused PTO does not roll over to the next calendar year'
    PTO#72d588daf1: 'Paid Time Off Policy'
    PTO#7345dd6174: 'PTO requests must be submitted at least two weeks in advance'

  Chunk IDs removed (old content, no longer present): 1
    PTO#0ba52fd6d1: 'Full time employees accrue 15 days of PTO per year'

  Chunk IDs added (new content, needs embedding): 1
    PTO#8459eb0c5a: 'Full time employees accrue 20 days of PTO per year'

  Only 1 of 4 chunks actually changed. The other 3 are IDENTICAL by content hash (M7-L08's mechanism) --
  re-embedding them again would be wasted work. This is the real,
  measurable efficiency gain from content-hash-based change detection:
  update only what changed, leave the rest of the index untouched.

============================================================================
3. DELETION PROPAGATION: THE INDEX ALONE IS NOT ENOUGH
============================================================================
  Index built from 2 documents: 6 chunks total.
  Cache contains 1 previously generated answer, citing chunk 'EQUIPMENT#68fd7752cc'.

  Now the Equipment Policy document is DELETED from the document store.
  Document store now has 1 document(s); index now has 4 chunk(s).
  Equipment chunk still in the index: False

  But the CACHE was never touched by this deletion:
    Cached answer: 'New employees receive a laptop and a home office stipend. [Source: EQUIPMENT#68fd7752cc]'
    Cited chunk ID still present in cache: EQUIPMENT#68fd7752cc
    That chunk ID still present in the INDEX: False

  A user re-asking the exact same question would be served this CACHED
  answer, complete with a citation pointing to a chunk that no longer
  exists anywhere in the index -- an orphaned reference. The index
  update was correct and complete; the propagation to a DOWNSTREAM
  system (the cache) was simply never triggered by the same event.

============================================================================
4. THE FIX: PROPAGATE THE SAME DELETION EVENT TO EVERY DOWNSTREAM CONSUMER
============================================================================
  Same deletion, this time propagated to the cache as part of the SAME
  operation:
    Cache entries invalidated: ['what equipment do new employees get']
    Cache now contains: []
    Equipment chunk in index: False

  The cache entry citing the deleted chunk was found (by checking
  whether ANY of its cited chunk IDs belong to the deleted document)
  and removed in the SAME operation that deleted the document -- not
  as a separate, easily-forgotten step. A user re-asking the same
  question now correctly triggers fresh retrieval instead of serving a
  broken citation.

============================================================================
5. WHAT THIS LAB IS AND IS NOT
============================================================================
  REAL: content-hash computation and comparison (M7-L08's exact
  mechanism), chunk-level diffing between document versions, and both
  the buggy and fixed deletion-propagation paths are genuinely
  executed on real (if synthetic) data, not scripted to fit.

  ILLUSTRATIVE: this lab's 'cache' is a single in-memory dictionary
  standing in for whatever real caching layer a production system
  uses (query result caches, CDN caches, precomputed summaries) --
  the propagation PRINCIPLE generalizes; the specific cache structure
  here does not represent any one real caching technology.

  NOT SHOWN: propagating updates (not just deletions) through a cache
  using the same content-hash change detection from section 2; a real
  event-driven architecture (e.g. a message queue) that would trigger
  propagation automatically across independent services; and
  re-embedding cost at real scale, which M6-L10 already measured.

Done.
```

### 7.3 Reading the result

**Section 2's 3-of-4-unchanged result is a genuinely useful, not just illustrative, finding.** In a real
document with dozens of sentences, an edit to one fact might leave 95% of chunks completely unchanged —
content-hash comparison is what lets a real system skip re-embedding all of them.

**Section 3's bug is deliberately unglamorous — a dictionary that simply never got touched.** That's the
point: propagation failures rarely look like dramatic bugs. They look like one system being correctly
updated while a completely reasonable-looking second system quietly keeps serving old data.

**Section 4's fix is a pattern, not just a patch for this one cache.** Computing the affected ID set once
and fanning it out to every consumer is the general shape of a correct propagation design — adding a third
or fourth downstream consumer later means adding it to the same fan-out, not inventing a new mechanism.

---

## 8. Common mistakes and troubleshooting

1. **Re-embedding an entire updated document instead of only its changed chunks.** §5.2 — content-hash
   comparison identifies exactly what changed; re-embedding everything wastes real, measurable work.
2. **Treating a correct index update as proof the system is fully consistent.** §5.3 — downstream caches
   and derived data can still reference deleted or outdated chunk IDs.
3. **Relying on time-based cache expiration as the only staleness safeguard.** §6 — this can leave stale,
   orphaned references servable for as long as the expiration window allows.
4. **Implementing cache invalidation as a separate, manually-remembered step from index deletion.** §5.4 —
   this is exactly the kind of step that gets forgotten; compute the affected set once and propagate it.
5. **Assuming a caching layer is safe because "it's just a performance optimization."** §6 — a cache
   serving stale citations is a correctness bug, not merely a performance concern.
6. **Not checking cached citations against the current index periodically.** §6 — this is a useful safety
   net independent of whether event-driven propagation is fully implemented everywhere yet.

| Symptom | Likely cause | Fix |
|---|---|---|
| An updated document causes re-embedding of content that didn't actually change | No content-hash-based change detection is being used | Compare chunk-level content hashes between versions; re-embed only what changed (§5.2) |
| A generated answer cites a source that no longer exists in the index | A cache was not invalidated when its underlying document was deleted or updated | Propagate deletion/update events to all caches referencing the affected chunk IDs (§5.3–§5.4) |
| Stale answers persist for a predictable, fixed period after a document is deleted | Cache invalidation relies only on time-based expiration | Trigger cache invalidation from the same event that updates the index, not expiration alone (§6) |
| A new caching layer is added and the old orphaned-reference bug reappears | Propagation logic wasn't extended to the new consumer | Add every new downstream consumer to the same shared propagation fan-out (§5.4) |

---

## 9. Security, privacy, reliability, cost

- **Reliability.** Use content-hash-based change detection to update only the chunks that actually
  changed, rather than re-embedding an entire document on every edit (§5.2).
- **Reliability.** Treat a correct index update as necessary but not sufficient — verify downstream caches
  and derived data are also updated as part of the same change (§5.3–§5.4).
- **Reliability.** Trigger cache invalidation from the same event that updates the index or document
  store, computing the affected ID set once and propagating it to every consumer (§5.4).
- **Cost.** Content-hash-based change detection directly reduces re-embedding cost by skipping unchanged
  chunks — a real efficiency gain, not just a correctness one (§5.2).

---

## 10. Exercises

### Exercise 1 — Beginner (~20 min)

1. In one sentence, what does content-hash comparison let you determine about an updated document?
2. Why did the buggy deletion function leave a real bug behind, even though it updated the index
   correctly?
3. What specifically made the cached answer in §7.3 dangerous, rather than merely outdated?
4. How did the fixed deletion function find which cache entries to invalidate?
5. Name one downstream consumer of chunk identity, besides the index, that a real system might need to
   update.

### Exercise 2 — Intermediate (~40 min)

1. Run the lab. Confirm §7.2's 3-unchanged/1-changed result and §7.3's orphaned-reference demonstration on
   your own machine.
2. Update a document with TWO sentences changed (not one) and confirm content-hash comparison correctly
   identifies both changed chunks and leaves the rest untouched.
3. Add a second cache entry (for a different query) that also cites the Equipment Policy chunk, and
   confirm the fixed deletion function invalidates both entries correctly.
4. Design and implement update propagation (not just deletion) to the cache: when a chunk's content hash
   changes, invalidate any cache entry citing the OLD chunk ID.
5. Using M6-L10's own measured rebuild-cost method, estimate the cost savings from content-hash-based
   partial re-embedding versus full re-embedding, for a corpus where typically 10% of chunks change per
   update.

### Exercise 3 — Challenge (~50 min)

1. Implement a generalized propagation system that accepts an arbitrary list of "consumers" (index, cache,
   and any others), each with its own invalidation logic, all triggered from one shared change-detection
   step.
2. Design and implement a periodic validation job that checks all cached citations against the current
   index and reports (or auto-invalidates) any orphaned references found, as a safety net independent of
   event-driven propagation.
3. Research (conceptually) how a real event-driven architecture (e.g. a message queue or pub/sub system)
   would implement this lesson's propagation pattern across genuinely independent services.
4. Extend this lesson's content-hash change detection to also handle document moves/renames (same content,
   different document ID) without treating them as a delete-and-add.
5. Using this lesson's §6 worked example as a model, design a monitoring check that would have caught the
   three-week stale-cache incident within hours instead of weeks.

---

## 11. Quiz

*(Answers: [`answer-keys/module-07-answers.md`](../../answer-keys/module-07-answers.md#m7-l16).)*

**Q1.** Per §7.1, what does this lesson cover that M6-L10 did not already cover in depth?

- A. The exact BM25 formula used for retrieval scoring.
- B. How to compute a content hash for a piece of text.
- C. The full propagation chain beyond the index itself — specifically what happens when caches or other derived data are forgotten while the index is updated correctly.
- D. How to chunk a document into sentence-level pieces.

**Q2.** Per §7.2's measured result, how many of the PTO policy's 4 chunks actually needed re-embedding
after the update?

- A. Only 1 of 4 — the other 3 were identical by content hash and could be safely skipped.
- B. All 4 chunks needed re-embedding, since the document changed.
- C. None of the 4 chunks needed re-embedding at all.
- D. Exactly 2 of the 4 chunks needed re-embedding.

**Q3.** Per §7.2, what makes it possible to identify exactly which chunks changed?

- A. Manually reading both versions of the document side by side.
- B. Checking which chunks are longer than a fixed character count.
- C. Randomly selecting half of the chunks for re-embedding.
- D. Comparing content-hash-based chunk IDs (M7-L08's mechanism) between the old and new versions — an unchanged hash means identical text, a changed or new hash means new content.

**Q4.** Per §7.3's measured result, what happened to the cache after the Equipment document was deleted
using the index-only deletion function?

- A. The cache was automatically and correctly updated at the same time as the index.
- B. The cache was never touched — it still contained an answer citing a chunk ID that no longer existed anywhere in the index.
- C. The cache was completely emptied of all entries, including unrelated ones.
- D. The cache raised an error and stopped functioning entirely.

**Q5.** Per §7.3, why is this described as a real bug rather than a harmless inconsistency?

- A. It is not actually a bug; the lesson treats this as fully acceptable behavior.
- B. It only affects documents written in languages other than English.
- C. A user re-asking the same question would be served a cached answer with a citation pointing to a chunk that no longer exists — an orphaned, broken reference presented as if it were still valid.
- D. It causes the entire retrieval system to crash immediately.

**Q6.** Per §7.3, was the index update itself correct in this scenario?

- A. Yes — the index update was correct and complete; the failure was that propagation to a separate, downstream system (the cache) was never triggered by the same event.
- B. No, the index update itself was incorrect and left stale chunks behind.
- C. No, the index was never actually updated at all in this scenario.
- D. The lesson does not address whether the index update was correct.

**Q7.** Per §7.4, how did the fixed deletion function find which cache entries needed invalidating?

- A. By asking the user which cache entries should be removed.
- B. By deleting every cache entry regardless of its content, as a precaution.
- C. By comparing cache entry timestamps to the current date.
- D. It checked whether any of a cache entry's cited chunk IDs belonged to the deleted document, using the same stale-ID set computed for the index deletion.

**Q8.** Per §7.4's measured result, what happened to the cache after the propagated deletion?

- A. The cache remained completely unchanged, identical to before the deletion.
- B. The cache entry citing the deleted chunk was correctly identified and removed, leaving the cache empty of any reference to the deleted document.
- C. A new, unrelated cache entry was created as a side effect.
- D. The cache invalidation function raised an unhandled exception.

**Q9.** Per §7.4, was the cache invalidation implemented as a separate, follow-up step or as part of the
same deletion operation?

- A. As a completely separate operation, run manually by an administrator days later.
- B. It was not implemented at all in this lab.
- C. As part of the same deletion operation, using the same set of stale chunk IDs computed once.
- D. As a scheduled background job that runs independently of any deletion event.

**Q10.** Per §7.5, what does this lab's "cache" stand in for?

- A. Whatever real caching layer a production system uses (query result caches, CDN caches, precomputed summaries) — the propagation principle generalizes, though the specific structure here isn't any one real technology.
- B. A real, live connection to a specific commercial caching product.
- C. The document store itself, renamed for this section.
- D. The BM25 scoring function, reused from a different lesson.

**Q11.** Which topic does this lesson explicitly leave unexplored, per §7.5?

- A. Content-hash computation, which this lesson covers directly instead.
- B. Deletion propagation to a cache, which this lesson covers directly instead.
- C. Chunk-level diffing between document versions, which this lesson covers directly instead.
- D. Propagating updates (not just deletions) through a cache using the same content-hash change detection, and a real event-driven architecture that would trigger propagation automatically.

**Q12.** What is the general lesson this lab demonstrates about incremental updates and deletion?

- A. Updating the index correctly is always sufficient on its own, regardless of any other system.
- B. A change must propagate to every system that references chunk identity, not just the primary index — updating the index correctly is necessary but not sufficient if downstream caches or derived data are left untouched.
- C. Caches should never be used in any RAG system, to avoid this class of bug entirely.
- D. Deletion and update propagation are entirely unrelated problems with no common underlying mechanism.

**Q13.** *(Written, rubric-graded.)* In under 150 words: your team's index correctly reflects a recent
document deletion, but users report answers citing content that "doesn't exist anymore." Based on this
lesson, what would you check, and why?

---

## 12. Revision notes

- **Content-hash-based chunk IDs (M7-L08) identify exactly which chunks of an updated document actually
  changed** — measured directly: only 1 of 4 chunks needed re-embedding after a real update, with the
  other 3 identical by hash and safely skippable.
- **A correct index update does not guarantee the whole system is consistent** — measured directly: a
  deletion that correctly removed a document from the document store and index still left a cache serving
  a citation to that now-nonexistent chunk.
- **An orphaned reference is dangerous specifically because it's invisible** — a stale cached citation
  looks exactly as valid as a correct one until someone checks whether the cited chunk still exists.
- **The fix is propagating one shared computation of "what changed" to every consumer**, not adding a
  separate, easily-forgotten manual step per downstream system — measured directly: the same stale-ID set
  used for index deletion correctly identified and invalidated the affected cache entry.
- **Time-based cache expiration alone is an inadequate staleness safeguard** — it can leave orphaned
  references servable for as long as the expiration window allows, as this lesson's worked example showed
  directly (nearly 30 days).
- **Every new downstream consumer of chunk identity needs to be added to the same propagation fan-out** —
  the pattern generalizes to any number of consumers, not just the one cache demonstrated here.

---

## 13. Completion checklist

- [ ] I can use content-hash comparison to identify exactly which chunks of an updated document changed.
- [ ] I can demonstrate that a correct index update alone does not guarantee full system consistency.
- [ ] I can implement and detect an orphaned-reference bug in a downstream cache.
- [ ] I can implement deletion propagation that invalidates caches as part of the same operation that
      updates the index.
- [ ] I map the full propagation chain (document store, index, caches, derived data) for any system I
      build.
- [ ] I treat time-based cache expiration as a safety net, not a substitute for event-driven propagation.
- [ ] I scored 10/13 on the quiz.

---

## 14. References

- Martin Fowler, *Cache Invalidation* (general reference on cache consistency patterns). `[UNVERIFIED]`
- Anthropic documentation, guidance on RAG index maintenance where available. `[UNVERIFIED]`

---

## 15. Next lesson

→ M7-L17 — Conversational and Multi-Hop Retrieval

You now know how to keep a whole system consistent as documents change. Next: retrieval across multiple
turns of a conversation and multiple hops of reasoning — building directly on M7-L09's query rewriting for
a single follow-up, now extended to genuinely multi-step questions.
