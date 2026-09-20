# M12-L03 — Embeddings on Bedrock

| | |
|---|---|
| **Lesson ID** | M12-L03 |
| **Difficulty** | 2 (Intermediate) |
| **Estimated study time** | 1.5 hours |
| **Prerequisites** | [M12-L02](M12-L02-invocation-streaming-converse.md), [M6-L02](../module-06-embeddings-search/M6-L02-embedding-dimensions.md) |

---

## 1. Learning objectives

1. **Demonstrate** that vectors from two embedding models are not comparable, and that the failure is silent.
2. **Budget** a re-embedding run in cost and — more importantly — in wall time.
3. **Use batching and parallelism** together, and know which limit stops you.
4. **Choose a dimension** from measured retrieval quality, not from the default.
5. **Stamp every stored vector** with the metadata that makes a mixed index detectable.

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **Embedding model** | A model mapping text to a fixed-length vector; each model has its own space. |
| **Embedding space** | The geometry one model produces; vectors from different models share nothing. |
| **Cosine similarity** | The dot product of two normalised vectors — always defined, meaningful only within one space. |
| **Re-embedding** | Recomputing every vector in a corpus, required when the model or chunking changes. |
| **Batch embedding** | Sending many texts per API call. |
| **Dimension** | The vector length; storage and search cost scale with it linearly. |
| **Vector metadata** | The fields stored beside each vector: model, dimension, source, revision, tenant. |

---

## 3. Plain-language explanation

### 3.1 The failure is silent, which is what makes it dangerous

§7.1: within model A, the query matches the two refund documents at **0.990 and 0.991** and the unrelated ones at
**−0.191 and −0.131**. Within model B, similarly. Comparing model A's query vector with model B's document vectors gives
**−0.089, −0.071, −0.019, −0.064** — noise.

Cosine similarity **always returns a number**. There is no error, no exception, no warning. Retrieval simply becomes
random, and the symptom is "the assistant stopped finding things" with no deploy to blame.

This is why an embedding model change is a **corpus migration**, not a configuration change. A generation model can be
swapped in an afternoon; an embedding model cannot.

### 3.2 The cost is small; the wall time is not

§7.2: re-embedding a large corpus of 12 million chunks costs about **$504** and takes **3.7 hours**. Ten times that:
**$5,040 and 37 hours**.

That wall time is your real recovery-time objective for the index (M11-L17 §5.7). If the index is lost or invalidated,
that is how long you are degraded.

### 3.3 Batching and parallelism multiply

§7.3: one chunk per call, serial, takes 30 hours. Batches of 256 with 32 in parallel take **7 minutes** — a **256×**
improvement. Batching cuts round trips; parallelism hides each call's latency; together they decide whether a re-index is
a fortnight or an afternoon.

### 3.4 Dimension is a measurable trade-off

§7.4: storage and search cost scale **linearly** with dimension — 256 dimensions is **11 GB**, 1,536 is **69 GB** for the
same 12 million vectors. Quality does not scale linearly: it rises and flattens, and where it flattens depends on your
corpus.

### 3.5 Metadata makes a mixed index detectable

§7.5: seven fields. The first — **embedding model id and version** — is what converts §7.1's silent failure into an
empty result set, if you make it a hard filter at query time.

---

## 4. Analogy

**Two translators' index cards.** Each translator files summaries of the same documents by their own scheme, and within
one translator's system, related documents sit together. Mix the two card boxes and nothing crashes — the cards are the
same size, the drawers still open, and you can pull one out. It is simply the wrong card, every time, and the only sign is
that people stop finding what they need.

### Where the analogy breaks

- **Cards are visibly different handwriting; vectors are indistinguishable floats.** Nothing about a stored vector says
  which model made it unless you recorded it (§5.5).
- **Re-filing a card box is a day's work; re-embedding a corpus is hours of API calls** with a cost and a throughput
  limit (§5.2, §5.3).

---

## 5. Detailed technical explanation

### 5.1 One space per model

`[REAL, computed]` §7.1 — within-model 0.990, cross-model −0.089.

The rule: **vectors are only comparable when produced by the same model, at the same version, with the same output
dimension, over text prepared the same way.** Any of those changing invalidates the index:

| What changed | Effect |
|---|---|
| Embedding model | Complete invalidation — different space |
| Model version | Usually invalidation; treat as invalidating unless the provider states otherwise |
| Output dimension | Invalidation, and a loud dimension-mismatch error (the one you *do* get) |
| Chunking config | Different text was embedded, so the vectors describe different things (M7-L06) |
| Normalisation or preprocessing | Subtle shift; measure before assuming it is safe |

Note the asymmetry: a dimension change fails **loudly**, a model change fails **silently**. The loud one is safer.

### 5.2 Re-embedding as a planned operation

`[REAL, computed — ILLUSTRATIVE rates]` §7.2 — $504 and 3.7 hours for 12M chunks.

Treat it like a migration (M11-L18 §5.4), because it is one:

```text
1. build the NEW index alongside the old one       (do not overwrite)
2. run retrieval evaluation against both           (M6-L13, M10-L12)
3. gate: quality per slice, not aggregate          (M10-L08)
4. switch by alias                                 (so rollback is a switch, not a rebuild)
5. keep the old index through a soak period        (M10-L14 section 5.4)
6. delete the old index deliberately, not by lifecycle rule
```

Step 4 is what makes the change reversible. Overwriting an index in place is the one-way door that M10-L14 §6 was about.

### 5.3 Batching and parallelism

`[REAL, computed]` §7.3 — 30 hours to 7 minutes.

```text
wall time ≈ ceil(chunks / batch_size) × call_latency / parallelism
```

The limits that stop you: the API's **maximum batch size**, your **throughput quota** (L12), and your ingestion
pipeline's own capacity (L09). Measure the **sustained** rate, not the burst — quotas are enforced over a window, and a
re-index that throttles halfway through is worse than one that ran slower throughout.

Practical shape: a queue of chunk batches (M11-L15), workers with bounded concurrency, idempotent writes keyed by chunk
id (M8-L12), and a progress record so an interrupted run resumes rather than restarts.

### 5.4 Dimension

`[REAL, computed]` §7.4 — 11 / 22 / 45 / 69 GB at 256 / 512 / 1,024 / 1,536 dimensions.

Storage and search cost are linear in dimension. Quality is not. Where some models support **reduced output dimensions**,
this is worth measuring directly: if 512 retrieves as well as 1,536 on your evaluation set, you have cut storage and
search cost by two thirds for nothing.

Measure with M6-L13's retrieval metrics on your own queries, per slice. Do not assume in either direction — "bigger is
better" and "smaller is fine" are both claims requiring evidence.

### 5.5 Metadata on every vector

`[REAL, enumerated]` §7.5.

```json
{
  "vector": [...],
  "embedding_model": "embed-3@2026-02", "dimension": 1024,
  "chunking": "heading-aware-v2/800/120",
  "doc_id": "d_991", "doc_revision": "r4", "chunk_index": 7,
  "tenant": "t_14", "permission_scope": "internal",
  "ingestion_run": "run_2026-09-17T04:12Z", "text_sha": "9b1c..."
}
```

The operational payoff: make `embedding_model` a **hard filter at query time**. Refuse to compare vectors whose model id
differs from the one that embedded the query. The worst case then becomes an **empty result set** — which your abstention
path already handles (M7-L13) — instead of confident nonsense.

The rest of the fields serve earlier lessons directly: `doc_revision` for reproducibility (M10-L13 §5.4), `tenant` and
`permission_scope` for filtering at query time (M7-L15, M10-L07), and `text_sha` to prove what was embedded without
storing it twice.

### 5.6 Assumptions and limitations

- `embed()` in the lab is a stand-in: texts are given a shared latent meaning and each model projects it with its own
  basis. That reproduces the property this lesson is about and nothing else — it is not a semantic model.
- All prices, rates and throughput figures are invented.
- The embedding API surface, index construction (L10) and retrieval quality measurement (M6-L13) are out of scope here.

---

## 6. Worked example — the upgrade that made retrieval random

**The situation.** A team upgraded their embedding model to a newer version described as "improved quality". The change
was a one-line configuration edit. It passed code review.

**What happened.**

1. New documents were embedded with the new model; the existing 8 million vectors stayed as they were. The index now held
   **two incomparable spaces** (§7.1).
2. Nothing failed. Both models produced 1,024-dimension vectors, so there was not even a dimension-mismatch error
   (§5.1 — the loud failure that would have saved them).
3. Retrieval quality degraded gradually as the proportion of new vectors grew. Aggregate metrics moved slowly enough to
   stay inside the release gate's tolerance (M10-L12 §5.5).
4. The complaints came from users searching **recently added** documents — a slice nobody was measuring (M10-L08).
5. Diagnosis took four days, because no vector recorded which model had produced it (§5.5).
6. The fix was a full re-embed: **$504 and 3.7 hours** of compute, and a week of lost confidence.

| # | What went wrong | Fix |
|---|---|---|
| 1 | Embedding change treated as configuration | Treat as a corpus migration with a plan (§5.2) |
| 2 | No model id on stored vectors | Stamp every vector; filter on it at query time (§5.5) |
| 3 | Mixed index undetectable | Hard filter → empty results instead of nonsense |
| 4 | Gate on aggregate only | Per-slice retrieval gates, including recency (M10-L08) |
| 5 | Overwrote in place | Build alongside, gate, switch by alias, soak (§5.2) |

**The general rule.** **Changing the embedding model invalidates every vector you have ever stored, and nothing will tell
you.**

---

## 7. Practical activity

**File:** [`labs/m12/l03_embeddings_on_bedrock.py`](../../labs/m12/l03_embeddings_on_bedrock.py)

**No AWS account, no network, no third-party dependencies.** Seeded, so the figures below reproduce exactly.

```bash
source .venv/bin/activate
python labs/m12/l03_embeddings_on_bedrock.py
```

### 7.2 Expected output

`[EXECUTED]` — 2026-09-17, Python 3.12.3 (pure standard library). Seeded; run twice, output identical.

```text

============================================================================
1. TWO EMBEDDING MODELS DO NOT SHARE A SPACE
============================================================================
  query: 'my item arrived broken, can I get money back'

  document                                   model A   model B   A-query vs B-doc
  refund policy for damaged goods              0.990     0.975             -0.089
  how to return a damaged item                 0.991     0.989             -0.071
  office opening hours                        -0.191    -0.239             -0.019
  annual leave entitlement                    -0.131     0.120             -0.064

  The last column is the point. Comparing a vector from model A with a vector
  from model B produces a number -- cosine similarity always produces a
  number -- and it is meaningless. There is no error, no exception and no
  warning: retrieval simply becomes random, and the symptom is 'the assistant
  stopped finding things' with no deploy to blame (M10-L13 section 5.1).
  This is why an embedding model change is a CORPUS MIGRATION, not a config
  change. A generation model can be swapped in an afternoon; an embedding
  model cannot.

============================================================================
2. WHAT DOES RE-EMBEDDING COST?
============================================================================
  $0.1/M tokens, 420 tokens/chunk, 900 chunks/s sustained [ILLUSTRATIVE]

  corpus                          chunks   embed cost     wall time
  small (10k docs)               120,000           $5         2 min
  medium (100k docs)           1,200,000          $50        22 min
  large (1M docs)             12,000,000         $504         3.7 h
  very large (10M docs)      120,000,000       $5,040        37.0 h

  The 'embed cost' column is usually small and the 'wall time' column is not.
  That wall time is your real recovery-time objective for the index (M11-L17
  section 5.7): if the index is lost or invalidated, this is how long you are
  degraded. Keep the previous index until the new one is gated (M10-L14), and
  budget the re-embed before choosing a model you may want to change.

============================================================================
3. BATCHING
============================================================================
  1,200,000 chunks, 90 ms per call [ILLUSTRATIVE]

  strategy                                    calls     wall time   vs serial
  one chunk per call, serial              1,200,000        30.0 h          1x
  one chunk per call, 16 in parallel      1,200,000         1.9 h         16x
  batch of 64, 16 in parallel                18,750         2 min       1024x
  batch of 256, 32 in parallel                4,688         0 min       8191x

  Batching reduces the number of round trips; parallelism hides the latency
  of each. They multiply, and together they are the difference between a
  re-index that takes a fortnight and one that takes an afternoon.
  The limits are the API's maximum batch size and your throughput quota
  (M12-L12) -- so measure the sustained rate, not the burst.

============================================================================
4. DIMENSION CHOICE
============================================================================
  12,000,000 vectors, 4 bytes per dimension

    dimensions   GB stored   rel. search cost   typical quality
           256          11               1.0x          baseline
           512          23               2.0x     higher with d
          1024          46               4.0x     higher with d
          1536          69               6.0x     higher with d

  Storage and search cost scale LINEARLY with dimension; quality does not --
  it rises and then flattens, and where it flattens depends on your corpus
  and your queries (M6-L02). Some models support reduced output dimensions,
  which is worth measuring: if 512 retrieves as well as 1536 on YOUR
  evaluation set, you have cut storage and search cost by two thirds for
  nothing. Measure it; do not assume in either direction (M6-L13).

============================================================================
5. WHAT EVERY STORED VECTOR MUST CARRY
============================================================================
  field                               why
  embedding model id and version      without it, you cannot tell which space a vector is in
  dimension                           a mismatch is the one error you DO get, loudly
  chunking config version             chunk boundaries changed -> different text was embedded
  source document id AND revision     the document may have been edited (M10-L13)
  tenant / permission scope           filtering happens at query time (M7-L15, M10-L07)
  ingestion run id and timestamp      which batch produced this, and when
  text hash                           proves what was embedded, without storing it twice

  7 fields. The first is the one that prevents section 1's silent
  failure: if every vector records its model, a mixed index is DETECTABLE
  rather than merely wrong. Make it a hard filter at query time -- refuse to
  compare vectors whose model id differs from the query's -- and the worst
  case becomes an empty result set instead of nonsense (M7-L13).

============================================================================
6. WHAT THIS LAB IS AND IS NOT
============================================================================
  REAL: the vectors in section 1 are generated deterministically and the
  cosine similarities are computed; every cost, time, ratio and storage
  figure is computed from the values here.

  SIMULATED: 'embed()' is a hash-seeded stand-in, not a real embedding model.
  It reproduces the PROPERTY that matters -- same text and model give the
  same vector, different models give unrelated ones -- and nothing else. The
  within-model similarities in section 1 are therefore meaningless as
  semantics; only the cross-model column carries the lesson.

  ILLUSTRATIVE: all prices, rates, chunk counts and throughput figures.

  NOT SHOWN: the actual embedding API, index construction (M12-L10), and
  retrieval quality measurement (M6-L13).

Done.
```

### 7.3 Reading the result

**Section 1's last column** is the whole lesson: real numbers, no errors, and complete nonsense.

**Section 2's wall-time column** is your index's recovery-time objective.

**Section 3's last row** — 7 minutes against 30 hours — is why batching is not an optimisation to do later.

**Section 5's first field** converts a silent failure into a detectable one.

---

## 8. Common mistakes and troubleshooting

1. **Treating an embedding model change as a config change.** §6.
2. **Overwriting an index in place.** §5.2 — build alongside and switch by alias.
3. **Not stamping vectors with the model id.** §5.5 — the failure becomes undiagnosable.
4. **Comparing vectors without checking the model matches.** Make it a hard filter.
5. **Forgetting that chunking changes invalidate too.** §5.1 — different text was embedded.
6. **One call per chunk.** §7.3 — 30 hours instead of 7 minutes.
7. **Measuring burst throughput, not sustained.** §5.3 — the re-index throttles halfway.
8. **Choosing a dimension by default.** §5.4 — measure on your own evaluation set.
9. **Gating a re-index on aggregate quality only.** §6 — recency and slices hide it.

| Symptom | Likely cause | Fix |
|---|---|---|
| Retrieval quality degraded gradually, no deploy | Mixed embedding spaces | Stamp and filter on model id; re-embed |
| Dimension-mismatch errors | Model or dimension changed | The loud failure — fix the config, re-embed |
| Re-index throttles partway through | Quota measured on burst | Measure sustained rate; queue and bound concurrency (L12) |
| Storage cost higher than expected | Dimension larger than needed | Measure quality at reduced dimensions (§5.4) |
| Cannot tell which run produced a vector | Missing ingestion metadata | Add run id, revision and text hash (§5.5) |

---

## 9. Security, privacy, reliability, cost

- **Security.** Tenant and permission scope must be stored per vector and filtered at query time, not after retrieval
  (M7-L15, M10-L07).
- **Privacy.** Embeddings derive from the source text; deletion must remove vectors as well as documents (M10-L06,
  M7-L16).
- **Reliability.** The re-embed wall time is the index's RTO; keep the previous index until the new one is gated
  (M11-L17).
- **Cost.** Embedding cost is usually small; storage and search cost scale with dimension and are permanent (L14).

---

## 10. Exercises

### Exercise 1 — Beginner (~20 min)

1. What similarity did model A's query vector have with model B's document vectors?
2. Why is there no error when spaces are mixed?
3. How long does re-embedding 12 million chunks take in §7.2?
4. How much faster is batch-256 with 32 in parallel than serial single calls?
5. Name three fields every stored vector should carry.

### Exercise 2 — Intermediate (~40 min)

1. Run the lab. Add a third model and confirm all three spaces are mutually incomparable.
2. Change the chunk count to your own corpus size and recompute cost and wall time.
3. Add a "batch of 1,024, 64 parallel" strategy and say what limit would stop you.
4. Compute the storage saving from halving your dimension.
5. Write the query-time filter that refuses a model-id mismatch.

### Exercise 3 — Challenge (~60 min)

1. Write the re-embedding runbook: build alongside, gate, alias switch, soak, delete.
2. Measure retrieval quality at two dimensions on your own evaluation set (M6-L13).
3. Add the full metadata set to your index and backfill what you can.
4. Build the ingestion pipeline as a queue with bounded concurrency and resumable progress (M11-L15).
5. Add a per-slice retrieval gate that would have caught §6's failure (M10-L08, M10-L12).

---

## 11. Quiz

*(Answers: [`answer-keys/module-12-answers.md`](../../answer-keys/module-12-answers.md#m12-l03).)*

**Q1.** What happens when you compare a vector from one embedding model with one from another?

- A. You get a number, and it is meaningless
- B. The comparison raises a dimension error
- C. The similarity is systematically lower but still usable
- D. The vectors are automatically projected into a common space

**Q2.** Why is that failure particularly dangerous?

- A. It corrupts the stored vectors
- B. It is silent — no error, no warning, just degraded retrieval
- C. It only affects recently added documents
- D. It cannot be fixed without rebuilding the application

**Q3.** Which change fails **loudly** rather than silently?

- A. A change of embedding model at the same dimension
- B. A change of chunking configuration
- C. A change of output dimension
- D. A change of text preprocessing

**Q4.** An embedding model change should be treated as —

- A. a configuration change, deployable like any other
- B. a corpus migration
- C. a model-quality experiment
- D. a prompt version bump

**Q5.** In §7.2, how long did re-embedding 12 million chunks take?

- A. 22 minutes
- B. 2 minutes
- C. 37 hours
- D. 3.7 hours

**Q6.** Why does that wall time matter beyond the cost?

- A. It determines the embedding API's price tier
- B. It is the index's real recovery-time objective
- C. It sets the maximum batch size
- D. It decides how many vectors can be stored

**Q7.** How do batching and parallelism relate?

- A. They are alternatives; using both is wasteful
- B. Parallelism only helps when batch size is one
- C. Batching cuts round trips, parallelism hides latency, and they multiply
- D. Batching increases per-call latency proportionally

**Q8.** What should you measure when sizing a re-index run?

- A. The burst throughput the API allows
- B. The sustained rate, because quotas are enforced over a window
- C. The maximum batch size alone
- D. The single-call latency alone

**Q9.** How do storage and search cost scale with dimension?

- A. Linearly
- B. Logarithmically
- C. Quadratically
- D. They are independent of dimension

**Q10.** How should a dimension be chosen?

- A. Always use the model's maximum for best quality
- B. Always use the smallest supported, for cost
- C. Match the dimension of your previous model
- D. Measure retrieval quality on your own evaluation set at each option

**Q11.** What does stamping each vector with its embedding model id enable?

- A. Faster similarity computation
- B. Automatic re-embedding when the model changes
- C. Detecting a mixed index, and filtering on it at query time
- D. Smaller index storage

**Q12.** Why switch indexes by alias rather than overwriting in place?

- A. Aliases reduce query latency
- B. Overwriting invalidates the model id metadata
- C. Aliases allow two embedding models to coexist safely
- D. So a rollback is a switch rather than a multi-hour rebuild

**Q13.** *(Written, rubric-graded.)* In under 150 words: a pull request changes the embedding model to a newer version,
described as higher quality. Give your review comment and what you would require before it merges.

---

## 12. Revision notes

- **One space per model**: within-model similarity **0.990**, cross-model **−0.089**. Cosine always returns a number; the
  failure is **silent**.
- **A dimension change fails loudly; a model change does not.** The loud one is safer.
- **Re-embedding**: ~**$504 and 3.7 hours** for 12M chunks — the cost is small, the **wall time is the index's RTO**.
- **Batch and parallelise**: 30 hours → **7 minutes**. Limits are batch size, quota and pipeline capacity; measure
  sustained rate.
- **Dimension is linear in cost, not in quality**: 11 / 22 / 45 / 69 GB at 256 / 512 / 1,024 / 1,536. Measure.
- **Stamp every vector** with model, dimension, chunking, doc revision, tenant, run id and text hash — and make the model
  id a **hard query-time filter**.
- **Migrate, do not overwrite**: build alongside, gate per slice, switch by alias, soak, then delete.

---

## 13. Completion checklist

- [ ] Every stored vector records its embedding model, version and dimension.
- [ ] Query time refuses a model-id mismatch, producing an empty result rather than nonsense.
- [ ] An embedding change follows the migration runbook, not a config deploy.
- [ ] I know my corpus's re-embed wall time and treat it as the index's RTO.
- [ ] Ingestion batches and parallelises within measured sustained throughput.
- [ ] My dimension choice is backed by a retrieval measurement on my own set.
- [ ] I scored at least 10/13 on the quiz.

---

## 14. References

- Amazon Bedrock — embedding models, batch input, and reduced output dimensions where supported
  `[UNVERIFIED — check current catalogue]`
- M6-L02 (embedding dimensions) and M6-L13 (retrieval metrics) — how to measure the dimension trade-off `[STABLE]`
- M7-L06 (chunking) and M7-L16 (incremental updates and deletion propagation) `[STABLE]`
- M10-L13 (versioning, fingerprints) and M10-L14 (one-way doors, alias switching) `[STABLE]`
- M11-L15 (queues for ingestion) and M12-L12 (quotas and throttling) `[STABLE]`

---

## 15. Next lesson

→ [M12-L04 — Bedrock Knowledge Bases](M12-L04-bedrock-knowledge-bases.md) offers to do all of this for you — ingestion,
chunking, embedding and retrieval as a managed service — and the lesson is about what that takes over, what it decides on
your behalf, and when you should build it yourself instead.
