# M6-L07 — Vector Indexes vs Vector Databases

| | |
|---|---|
| **Lesson ID** | M6-L07 |
| **Difficulty** | 2 (Intermediate) |
| **Estimated study time** | 1.5 hours |
| **Prerequisites** | [M6-L06](M6-L06-approximate-nn-hnsw.md) |

---

## 1. Learning objectives

1. **Measure** the real cost of two ways to "delete" from an approximate index, and explain why neither
   is both cheap and correct.
2. **Measure** what persisting an in-memory index to disk actually requires, beyond the algorithm
   itself.
3. **Distinguish** a bare vector index (a library) from a vector database (a system), by capability, not
   by vendor name.
4. **Decide**, for a given system, whether a bare index or a managed database is the right level of
   infrastructure.
5. **State** what this lesson explicitly defers to M6-L08 (a real system) and M6-L09 (filtering).

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **Vector index** | The algorithm and in-memory data structure for similarity search (M6-L06) — no persistence or management included. |
| **Vector database** | A system wrapping one or more indexes with persistence, metadata filtering, concurrency, and other operational capabilities. |
| **Tombstone (deletion)** | Marking a vector as deleted without removing it from the underlying index structure. |
| **Index rebuild** | Regenerating an index's structure from its (possibly changed) source vectors — often the only way to achieve true deletion. |
| **Persistence** | A system's ability to survive a process restart without losing its data or structure. |
| **Operational overhead** | The ongoing work — deployment, monitoring, scaling — required to run a system in production. |

---

## 3. Plain-language explanation

### 3.1 "Vector database" is doing a lot of hidden work in that phrase

M6-L05 and M6-L06 built and measured real search **algorithms**. Neither one persisted anything, handled
more than one query at a time safely, or supported removing a vector cleanly. Those gaps are not
oversights in the labs — they are exactly the gaps a **vector database** exists to fill. This lesson
measures the gaps directly, rather than asserting they exist.

### 3.2 Deleting from an approximate index is genuinely hard

An IVF index (M6-L06) assigns each vector to a cluster based on the full corpus at build time. Remove a
vector, and the cluster it belonged to is now slightly wrong — not broken, just stale. §7.1 measures the
two real options: mark it deleted and keep searching around it (fast, but the cost and the staleness
remain), or actually rebuild the index (correct, but real, measured compute). **There is no third option
that is both fast and fully correct.**

### 3.3 Persistence is not the algorithm's job

A vector index, as a library, does one thing: it answers similarity queries against whatever is currently
in memory. What happens when the process restarts is not its concern — and §7.2 shows exactly what has to
be added, deliberately, to change that.

### 3.4 The comparison is about capability, not vendor

"Index vs database" is not "library X vs product Y." It is a checklist of specific capabilities — §5.4
lays it out — and the honest answer to "which do I need" depends entirely on which rows on that checklist
are actual requirements for your system.

---

## 4. Analogy

**A calculator versus an accounting department.** A calculator computes correctly, instantly, and
disappears the moment you put it down — nothing it computed is retained, nobody else can use it while
you are, and if you need to correct an entry from last month, there is no record to correct. An
accounting department uses calculators constantly, but it also keeps ledgers, handles multiple people
working on the books at once, and has a defined process for correcting a past entry without losing the
audit trail.

Nobody would say the accounting department's process makes the calculator obsolete. The calculator is
still doing the actual arithmetic. The department exists because "get the right number" and "manage the
numbers reliably over time, for multiple people, with a history" are different problems.

### Where the analogy breaks

- **A calculator's output is either right or wrong, immediately checkable.** An approximate index's
  output has a *measured*, tunable accuracy (M6-L06), which a database does not change — it inherits
  whatever the underlying index provides.
- **Correcting a ledger entry is a well-understood, cheap accounting operation.** Correcting (deleting
  from) an approximate index is genuinely expensive by construction (§7.1) — this is not solved just by
  wrapping the index in more software; it has to be actively managed.
- **An accounting department is unambiguously "more" than a calculator.** A bare index is sometimes the
  *correct* choice, not a lesser one — when none of §5.4's extra rows are actual requirements, adding a
  database is pure overhead.

---

## 5. Detailed technical explanation

### 5.1 The delete problem, measured

`[REAL]` §7.1 built the same 50,000-vector IVF index from M6-L06, then removed 20% of it two ways:

| Approach | Time | What it actually achieves |
|---|---|---|
| **Tombstone** (mark deleted, filter results) | **~0ms** | Nothing freed; a search still compares against every "deleted" vector, then hides them from the result |
| **Rebuild** (regenerate the index) | **4.9 seconds** | Vectors genuinely gone: less memory, correct centroids, no wasted comparison time |

**A search after tombstoning cost the same 0.91ms it cost before** — the deleted vectors were still
fully present in memory and still fully part of every comparison; only the *displayed result* changed.
**Rebuilding is correct and measurably expensive**, at a corpus size far smaller than most production
systems. **There is no cheap option that is also correct.** A vector database's real job, in large part,
is managing this trade-off systematically — batching deletes, scheduling rebuilds in the background, or
choosing an index structure with genuinely cheaper true deletion — instead of leaving every delete as a
manual choice between "fake" and "expensive."

### 5.2 Persistence, measured

`[REAL]` §7.2 measured what turning the in-memory index from §7.1 into something that survives a restart
actually requires:

| Operation | Time | Size |
|---|---|---|
| Serialize to bytes | 0.01s | 25.9 MB |
| Deserialize back | 0.00s | — |

**This is the simplest possible version** — one file, one process, no concurrent access, no partial-write
recovery. A bare index library did not do any of this automatically; it had to be added, explicitly, as
separate code. A real production system additionally needs to survive a crash **mid-write**, remain
**readable while being written to**, and scale past what fits in **one process's memory** — none of which
this lab's simple version handles, and none of which a bare index library provides by default.

### 5.3 The comparison, as a checklist

| Capability | Bare index (e.g. a library like this lab's) | Vector database |
|---|---|---|
| Similarity search algorithm | Yes — its entire job | Yes, usually wrapping a library like this |
| Persistence across restarts | No, unless you build it | Yes, by default |
| True deletion without a full rebuild | No (§5.1) | Often yes, managed internally |
| Metadata filtering (M6-L09) | No, unless you build it | Usually built in |
| Concurrent reads/writes | No, unless you build it | Yes, by default |
| Backups, replication | No | Usually yes |
| Operational overhead | Low — it's a library | Higher — it's a service |

**Neither column is universally better.** A bare index embedded directly in an application is lighter and
has fewer moving parts when persistence, filtering, and concurrency genuinely are not required. A
database is the right choice the moment any row in the left column becomes a real requirement rather
than a hypothetical one — which, for most production systems handling real, changing, concurrently-
accessed data, is almost immediately.

### 5.4 What this lesson does not cover

**Metadata filtering** — combining a similarity search with a structured condition like `category = X` —
is listed in §5.3's table but not built here; it is M6-L09's complete subject, including the specific
pitfalls of combining filters with approximate search. **A real, specific vector database system** —
pgvector, running on real PostgreSQL — is M6-L08's hands-on subject, building directly on the concepts
this lesson names.

### 5.5 Assumptions and limitations

- §7.1 and §7.2's specific timings are tied to this lab's corpus size, this run's hardware, and Python's
  built-in `pickle` for serialization — a real system's numbers, and its choice of serialization format,
  will differ. The *shape* of the gap (tombstone is fast-but-incomplete, rebuild is correct-but-costly;
  a bare library persists nothing by default) is what transfers.
- Real vector databases implement more sophisticated incremental update strategies internally than this
  lesson's simple tombstone-or-rebuild choice — the specifics are product-dependent and not covered here.
- This lesson's comparison table describes typical capability differences, not a guarantee about any
  specific product; verify a given system's actual feature set before relying on any row.

---

## 6. Worked example — the prototype that "worked fine" until the process restarted

**The system.** A team prototypes a document-search feature using a bare vector-index library directly in
their application code — no database, just the index, built once at startup from a fixed set of
documents. It works well in every demo.

**What happened at the first deployment.** The application's hosting platform restarted the process
during a routine deployment — an entirely normal, expected event in any real hosting environment. The
in-memory index, having never been persisted, was gone. The application rebuilt it from source documents
on the next startup, which took long enough that the first several requests after every restart failed
or timed out.

**Why nobody caught this in the demo.** A demo environment is rarely restarted mid-session. The gap
between "works in a long-running demo" and "survives a normal production restart schedule" was invisible
until the first real deployment cycle.

**Three defects:**

| # | Defect | Consequence |
|---|---|---|
| 1 | No persistence was built for the in-memory index | Every restart lost the entire index, with no recovery path but a full rebuild |
| 2 | No measurement of rebuild time against realistic restart frequency | Nobody had a number to check "is this acceptable" against before it happened in production |
| 3 | The choice between a bare index and a database was never made deliberately | The team ended up needing database-like capability (persistence) without having chosen a database, or built the equivalent themselves |

### The fix

**Persist the index explicitly** (§5.2), or — more robustly — **use a system that persists by default**,
per §5.3's table, once persistence is a real requirement rather than an assumption.

**Measure rebuild time against your actual deployment/restart frequency** before deciding a bare,
non-persistent index is acceptable — the same "measure before you assume" discipline M6-L05 applied to
search latency.

**Make the index-vs-database choice deliberately**, using §5.3's checklist against your system's actual
requirements, rather than defaulting to whichever is simplest to start with and discovering the gap in
production.

**The general rule.** **A bare vector index gives you exactly the algorithm and nothing else. Every other
capability — surviving a restart, deleting cleanly, serving concurrent requests — is either something you
build yourself, deliberately, or something you get by choosing a system that already builds it for you.
There is no third option where it comes for free.**

---

## 7. Practical activity

**File:** [`labs/m6/l07_index_vs_database.py`](../../labs/m6/l07_index_vs_database.py)

**No API key, no network.** Expect the run to take roughly 10–15 seconds (real k-means, twice).

```bash
source .venv/bin/activate
python labs/m6/l07_index_vs_database.py
```

Sections 1–2 measure real operations on the same real index M6-L06 built.

### 7.2 Expected output

`[EXECUTED, machine-specific timings]` — 2026-09-09, Python 3.10.11, NumPy 2.2.6, scikit-learn 1.7.2.

```text
============================================================================
1. THE DELETE PROBLEM: TOMBSTONE VS REBUILD, MEASURED
============================================================================
  Building the same 50,000-vector, 100-cluster IVF index as M6-L06...
  Built in 6.1s.

  Deleting 10,000 vectors (20% of the corpus), scattered across clusters.

  Option A -- TOMBSTONE: mark 10,000 ids as deleted.
    time taken: 0.000ms (a set insert, essentially free)
    a search afterward still costs 0.91ms --
    the deleted vectors are still THERE, still compared against,
    still occupying every byte of memory they occupied before.
    Filtering happens AFTER the comparison, not instead of it.

  Option B -- REBUILD: actually remove the 10,000 vectors and rebuild the index for real.
    time taken: 4.9s -- the tombstone was, for
    practical purposes, instant; this is real, measured, whole
    seconds of compute, on a corpus far smaller than production.
    But the vectors are ACTUALLY gone: less memory, uncorrupted
    centroids, and a search no longer wastes time comparing against
    them at all.

  There is no cheap, correct delete for an approximate index. You
  choose: tombstone (instant, but the cost and the stale centroids
  remain until a rebuild) or rebuild (correct, but real, measured
  seconds of work at this corpus size -- and a production corpus is
  routinely orders of magnitude larger). A vector DATABASE exists
  partly to manage this trade-off for you -- batching deletes,
  scheduling background rebuilds, or using an index structure with
  cheaper true deletion -- instead of leaving you to choose between
  'fake' and 'expensive' by hand, every time something is deleted.

============================================================================
2. PERSISTENCE: WHAT A BARE INDEX DOES NOT GIVE YOU
============================================================================
  An in-memory index (like the one just built) exists only as long as
  the process holding it stays alive. Persisting it is extra work a
  library does not do for you automatically.

  Serializing the index to bytes: 0.01s, 25.9 MB.
  Deserializing it back: 0.00s.
  Restored correctly: True

  This lab does the simplest possible version (one file, one process,
  no concurrent access, no partial writes to worry about). A real
  production system needs this to survive a crash mid-write, be
  readable while still being written to by another process, and
  scale past what fits in one process's memory at all -- none of
  which a bare index library provides. That gap is exactly what a
  vector DATABASE is built to close.

============================================================================
3. INDEX vs DATABASE: WHAT EACH ACTUALLY PROVIDES
============================================================================
  Similarity search algorithm
    bare index:      Yes (its whole job)
    vector database: Yes (usually wraps a library like this)
  Persistence across restarts
    bare index:      No, unless you build it
    vector database: Yes, by default
  True deletion without a full rebuild
    bare index:      No (section 1: tombstone or rebuild)
    vector database: Often yes (managed internally)
  Metadata filtering (M6-L09)
    bare index:      No, unless you build it
    vector database: Usually built in
  Concurrent reads/writes
    bare index:      No, unless you build it
    vector database: Yes, by default
  Backups, replication
    bare index:      No
    vector database: Usually yes
  Operational overhead
    bare index:      Low (it's a library)
    vector database: Higher (it's a service)

  Neither column is 'better' in the abstract. A bare index embedded
  directly in your application is lighter-weight and has fewer moving
  parts when you genuinely do not need persistence, filtering, or
  concurrent access. A database is the right choice the moment any of
  sections 1-2's gaps become requirements rather than conveniences --
  which, for most production systems, is almost immediately.

============================================================================
4. WHAT THIS LAB IS AND IS NOT
============================================================================
  REAL: sections 1-2 measure actual operations -- a real k-means
  rebuild, a real tombstone set, real pickle serialisation -- on the
  same real index M6-L06 built. Every millisecond is measured, not
  estimated.

  ILLUSTRATIVE: the specific rebuild and serialisation times are
  specific to this corpus size and this machine. A real production
  index (larger, on real hardware, possibly with a more efficient
  serialisation format than pickle) will differ -- the SHAPE of the
  gap, not the specific seconds, is what transfers.

  NOT SHOWN: how a real vector database actually implements cheaper
  incremental updates internally (proprietary, and varies by
  product), and metadata filtering, which is M6-L09's full treatment.
  M6-L08 gets hands-on with one real system, pgvector, next.

Done.
```

### 7.3 Reading the result

**Section 1's most important number is the one that stays the same: 0.91ms.** The search cost after
"deleting" 20% of the corpus via tombstone was unchanged, because nothing about the search actually got
smaller. If the goal of deleting was to reclaim memory or speed, a tombstone alone delivers neither.

**The 4.9-second rebuild is small only because this lab's corpus is small.** M6-L05 already established
that this class of operation scales with corpus size — a production-scale rebuild is not a rounding
error.

**Section 3's table is the lesson's actual deliverable.** Read it as a requirements checklist for your
own system, not as an abstract comparison — every "no, unless you build it" row is a specific piece of
engineering work someone has to do, one way or another.

---

## 8. Common mistakes and troubleshooting

1. **Treating "delete" from an approximate index as a cheap, instant operation.** §7.1 — it is one or the
   other, never both.
2. **Assuming an in-memory index survives a process restart.** §6 — it does not, unless persistence is
   built deliberately.
3. **Choosing a bare index or a database based on familiarity rather than requirements.** Use §5.3's
   checklist against your actual needs.
4. **Adding a full database when none of §5.3's extra rows are actually required.** Unnecessary
   operational overhead is a real cost too.
5. **Not measuring rebuild time against your actual delete/update frequency.** A rebuild that's
   acceptable once a month may not be acceptable once an hour.
6. **Assuming a vector database's internal update mechanism is free or instant.** It manages the
   tombstone/rebuild trade-off better than doing it by hand, but the underlying cost (§5.1) does not
   disappear — it is engineered around, not eliminated.

| Symptom | Likely cause | Fix |
|---|---|---|
| Index is empty or missing after a deployment/restart | No persistence built for an in-memory index | Add explicit persistence, or use a system that persists by default (§5.2, §6) |
| Deletes don't seem to free memory or speed up search | Tombstoning only, no rebuild | Schedule periodic rebuilds, or use a system with real incremental deletion |
| Choosing between a library and a managed service feels arbitrary | No explicit requirements checklist | Use §5.3's table against actual system requirements |
| Unexpected latency spikes after bulk deletes | An unscheduled full rebuild triggered synchronously | Batch and schedule rebuilds; measure their cost against your traffic pattern |

---

## 9. Security, privacy, reliability, cost

- **Reliability.** Never assume an in-memory vector index survives a process restart — measure or
  explicitly build persistence before depending on it (§7.2, §6).
- **Reliability.** Understand that "delete" from an approximate index is either incomplete (tombstone) or
  expensive (rebuild) — plan for one or the other deliberately, not by accident.
- **Cost.** A full index rebuild has a real, measurable compute cost that scales with corpus size (M6-L05)
  — schedule and batch it rather than triggering it synchronously on every delete.
- **Privacy.** A "deleted" (tombstoned) vector remains fully present in memory and in any persisted copy
  of the index until a rebuild actually removes it — if deletion is required for compliance reasons
  (M10-L06), a tombstone alone does not satisfy that requirement.
- **Reliability.** Choose a bare index only when persistence, filtering, and concurrency are genuinely
  not required — the operational simplicity is real, but so is the gap if requirements change later.

---

## 10. Exercises

### Exercise 1 — Beginner (~20 min)

1. In one sentence, what does a bare vector index provide, and what does it not provide?
2. Why does tombstoning not reduce a search's query time?
3. Why is rebuilding an index the only way to achieve true deletion for the method built in this lab?
4. Name two things a bare index library does not give you that a vector database usually does.
5. When is a bare index the right choice, rather than a database?

### Exercise 2 — Intermediate (~40 min)

1. Run the lab. Report your own machine's rebuild time and compare it to this lesson's figure.
2. Change the delete fraction to 5% and to 50%, and report how rebuild time changes with each.
3. Measure how long it takes to persist and reload the index using a different serialization approach
   (e.g. `numpy.save` for the arrays instead of `pickle`) and compare the size and speed.
4. Design a "batched delete" policy (e.g. rebuild only after every 1,000 deletes, or once per hour) for a
   system with a stated delete rate, and justify the batching interval with arithmetic.
5. Using §5.3's checklist, evaluate whether a bare index or a database is the right choice for three
   different hypothetical systems you define (e.g. a single-user prototype, a multi-tenant SaaS product,
   an internal research tool).

### Exercise 3 — Challenge (~50 min)

1. Implement a simple background-rebuild scheduler: accumulate deletes, and trigger a real rebuild once a
   threshold is crossed, without blocking incoming search queries during the rebuild.
2. Measure memory usage (not just time) before and after a tombstone-only delete versus a full rebuild,
   and quantify the memory actually reclaimed by each.
3. Research (conceptually) how one real vector database product handles updates and deletes internally,
   and compare its approach to this lab's tombstone/rebuild choice.
4. Design a persistence format for a real system (fields, versioning, how to detect a partial write) more
   robust than this lab's single-file pickle approach.
5. Write the infrastructure decision document for a real or hypothetical system: which capabilities from
   §5.3's checklist are required, and whether that points to a bare index or a managed vector database.

---

## 11. Quiz

*(Answers: [`answer-keys/module-06-answers.md`](../../answer-keys/module-06-answers.md#m6-l07).)*

**Q1.** In §7.1, tombstoning 10,000 vectors took essentially zero measurable time, but a search afterward
still cost about the same as before deletion. This is because:

- A. The tombstone operation actually failed silently.
- B. Search time is unrelated to corpus size.
- C. The deleted vectors were moved to a faster storage tier.
- D. The deleted vectors are still stored and still compared against during search; only the results are filtered afterward.

**Q2.** In §7.1, rebuilding the index after removing the deleted vectors took several real, measured
seconds. This demonstrates:

- A. Rebuilding is always faster than tombstoning.
- B. True deletion from an approximate index requires substantial recomputation, unlike a tombstone, which is nearly free but does not actually reclaim anything.
- C. The k-means algorithm cannot handle reduced datasets.
- D. Deletion is impossible in any vector index.

**Q3.** Per §5.1, the fundamental problem with deleting from an approximate index is:

- A. Deletion is not supported by any real system.
- B. Only dense vectors can be deleted, never sparse ones.
- C. There is no cheap option that is also correct — tombstoning is fast but leaves stale data and cost behind; rebuilding is correct but computationally expensive.
- D. Deletion always corrupts the remaining data permanently.

**Q4.** In §7.2, what did serializing the index to disk actually require?

- A. Explicit code to convert the in-memory structures to bytes and back — nothing a bare index library provides automatically.
- B. No code at all; it happens automatically in any index library.
- C. A separate database server running at all times.
- D. Converting all vectors to sparse representations first.

**Q5.** Per §5.2, what happens to an in-memory vector index if the process holding it crashes, with no
persistence code written?

- A. The index automatically saves itself before the crash.
- B. Only the most recently added vectors are lost.
- C. The operating system preserves it in a temporary cache.
- D. The entire index is lost and must be rebuilt from scratch, since nothing was saved to survive the process ending.

**Q6.** According to §5.3's comparison table, which capability is typically NOT provided by a bare index
library like the one used in this lab?

- A. A similarity search algorithm.
- B. The ability to compute cosine similarity.
- C. Concurrent reads and writes from multiple processes.
- D. The ability to store vectors in memory.

**Q7.** The lesson states that neither a bare index nor a full vector database is "better" in the
abstract. This means:

- A. The two are functionally identical in every way.
- B. The right choice depends on whether persistence, filtering, and concurrent access are actual requirements or unnecessary overhead for a given system.
- C. Databases should always be preferred regardless of requirements.
- D. Bare indexes should always be preferred regardless of requirements.

**Q8.** Metadata filtering (e.g., "top-k similar documents WHERE category=X") is mentioned in this
lesson's comparison table but not covered in depth, because:

- A. It is the specific, full subject of a later lesson, M6-L09.
- B. It is impossible to implement in any real system.
- C. It has no relationship to vector search at all.
- D. It was fully covered in M6-L01.

**Q9.** The general lesson from combining sections 1 and 2 is:

- A. Vector indexes and vector databases are interchangeable terms for the same thing.
- B. Persistence is more important than deletion in every system.
- C. Rebuilding is always the wrong choice compared to tombstoning.
- D. A bare vector index provides the similarity-search algorithm itself, but essentially none of the operational capabilities (persistence, real deletion, concurrency) a production system typically needs.

**Q10.** Why does the lesson caution that this lab's specific rebuild and serialization times will differ
on other systems?

- A. The lab's code contains a randomised bug.
- B. They depend on this specific corpus size, this machine's hardware, and the specific libraries used (e.g., pickle), none of which are universal constants.
- C. Timing measurements are impossible to reproduce under any circumstances.
- D. Different programming languages always produce identical timings.

**Q11.** A vector database, per §5.3, typically wraps:

- A. An underlying similarity-search index (often a library similar to the one built in this lab), adding persistence, filtering, and concurrency around it.
- B. Nothing; it is built entirely independently of any indexing algorithm.
- C. Only sparse retrieval methods, never dense embeddings.
- D. A single, universally standardized algorithm used by every vendor.

**Q12.** What does this lesson explicitly defer to M6-L08?

- A. The mathematics of cosine similarity.
- B. How BM25 computes term frequency.
- C. Hands-on work with a real, specific vector database system, pgvector.
- D. The definition of a vector index.

**Q13.** *(Written, rubric-graded.)* In under 150 words: your team is building a prototype that embeds a
fixed, rarely-changing set of 500 documents and needs no concurrent access. A colleague insists on
standing up a full managed vector database "to be safe." State what this lesson's checklist would say
about that decision, and what you would propose instead.

---

## 12. Revision notes

- **A vector index provides the search algorithm. A vector database wraps an index with persistence,
  filtering, concurrency, and operational management.** Neither term implies the other.
- **Deleting from an approximate index has no cheap, correct option.** Measured: a tombstone cost
  approximately 0ms but left search cost unchanged (0.91ms, identical to before); a real rebuild cost
  4.9 measured seconds on a corpus far smaller than production scale.
- **Persistence is not automatic.** Measured: serializing and reloading a real index required explicit
  code and real, if small, time — nothing a bare library does for you by default.
- **The index-vs-database choice is a checklist against actual requirements**, not a judgment about which
  is generically superior — persistence, true deletion, filtering, and concurrency are each their own
  yes/no question for a given system.
- **A bare index is the right choice exactly when none of those requirements are real** — added
  operational overhead without a corresponding need is a real cost, not caution.
- **Metadata filtering and a specific real database system (pgvector) are deliberately deferred** to
  M6-L09 and M6-L08 respectively — this lesson establishes the concepts both will build on.

---

## 13. Completion checklist

- [ ] I can explain why tombstoning does not reduce search cost.
- [ ] I can explain why true deletion from an approximate index requires a rebuild.
- [ ] I know that persistence is not automatic for a bare vector index.
- [ ] I can use a capability checklist to decide between a bare index and a vector database for a given system.
- [ ] I understand that neither choice is universally correct — it depends on actual requirements.
- [ ] I know that metadata filtering and a specific real system are covered in M6-L09 and M6-L08.
- [ ] I scored 10/13 on the quiz.

---

## 14. References

- pgvector — GitHub repository and documentation (the specific system M6-L08 covers hands-on).
  <https://github.com/pgvector/pgvector> `[UNVERIFIED]`
- Facebook AI Research — FAISS documentation (a widely used bare vector-index library).
  <https://github.com/facebookresearch/faiss/wiki> `[UNVERIFIED]`
- Python documentation — `pickle` module (used for this lab's persistence measurement).
  <https://docs.python.org/3/library/pickle.html> `[UNVERIFIED]`

---

## 15. Next lesson

→ [M6-L08 — pgvector Hands-On (and How Alternatives Differ)](M6-L08-pgvector-hands-on.md)

You now know what a bare index does not give you. Next: getting hands-on with a real system that fills
those gaps — pgvector, running as an extension on PostgreSQL you already know how to use.
