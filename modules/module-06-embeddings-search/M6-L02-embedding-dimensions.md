# M6-L02 — Embedding Dimensions, Model Compatibility and Normalization

| | |
|---|---|
| **Lesson ID** | M6-L02 |
| **Difficulty** | 2 (Intermediate) |
| **Estimated study time** | 1.75 hours |
| **Prerequisites** | [M3-L02](../module-03-math-ml-essentials/M3-L02-dot-product-cosine.md), [M6-L01](M6-L01-semantic-vs-exact.md) |

---

## 1. Learning objectives

1. **Compute** the storage cost of an embedding corpus from dimension count, precision, and document
   count.
2. **Explain** why two embedding models — even at identical dimension count — produce incompatible
   vector spaces, and demonstrate it concretely.
3. **Identify** the practical triggers for a model-compatibility bug, including a routine model upgrade.
4. **Prove**, with a verified identity, why cosine similarity and Euclidean distance agree on normalized
   vectors and can disagree sharply on unnormalized ones.
5. **Design** a vector-tagging discipline that catches model-compatibility bugs before they reach
   production.

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **Embedding dimensionality** | The number of values (axes) in an embedding vector — a design choice of the model. |
| **Vector precision** | The numeric representation (float32, float16, int8, …) used to store each dimension's value. |
| **Quantization** | Reducing a vector's numeric precision to save storage, independent of dimension count. |
| **Model-compatibility bug** | Comparing vectors from two different embedding models, or versions, as if they shared one coordinate system. |
| **Coordinate system (embedding space)** | The specific, learned arrangement of axes one trained model produces — not shared with any other model. |
| **Distance metric** | The function (cosine, Euclidean/L2, dot product) a search system uses to rank vectors. |
| **Magnitude sensitivity** | A distance metric's tendency to be affected by vector length, not just direction. |
| **Vector tagging** | Recording which model and version produced a stored vector, to detect incompatibility later. |

---

## 3. Plain-language explanation

### 3.1 Dimensions cost something, always

M4-L04 told you an embedding's dimension count is `d_model`, a design choice. This lesson prices that
choice: every additional dimension is more storage, more memory, and more arithmetic on every single
similarity computation, at every scale. §7.1 puts an exact number on it.

### 3.2 "Same dimension count" is not "same space"

Two embedding models can both produce, say, 768-dimensional vectors, and be **completely incompatible**
— dimension 47 means something different (or nothing coherent at all) between them, because each model
learned its own arrangement of axes from its own training. Comparing a query embedded by one model against
documents embedded by another produces numbers that are computed correctly and **mean nothing**. §7.2
demonstrates this with vectors small enough to inspect by eye.

### 3.3 Cosine and Euclidean distance are not interchangeable, until vectors are normalized

M3-L02 proved, with small numbers, that normalized vectors make dot product and cosine identical. This
lesson shows the practical consequence: **on un-normalized vectors, cosine similarity and Euclidean
distance can rank the same documents in opposite orders**, purely because of magnitude differences that
have nothing to do with meaning. §7.3 verifies, with an exact identity, exactly when that disagreement
disappears.

---

## 4. Analogy

**Two translators who each learned their own private shorthand.** Both write notes using exactly 40
symbols per sentence — the same "dimension count." But translator A's symbol 12 means "urgent," and
translator B's symbol 12 means "polite." Handing translator B's notes to someone trained only to read
translator A's shorthand produces a reading that is fluent, confident, and wrong — nothing about the notes
signals that they came from a different system.

Separately: imagine grading both translators' notes by literally measuring how much ink is on the page
(a stand-in for magnitude) rather than what the symbols actually say (direction/meaning). A translator who
wrote a longer, more detailed note about something completely irrelevant would out-rank a translator who
wrote a short, perfectly on-topic note — not because the content was better, but because there was more
of it.

### Where the analogy breaks

- **A human reader would eventually notice the shorthand doesn't parse.** A cosine similarity computation
  never "notices" anything — it returns a number for any two vectors of matching dimension, correct or
  not (§7.2).
- **Ink quantity is an obviously silly way to grade notes.** Magnitude-sensitive ranking on
  un-normalized embeddings is a real, common, non-obvious default in some systems (§7.3) — it does not
  announce itself as wrong.
- **Two translators' shorthand systems are visibly different documents.** Two embedding models' vector
  spaces are both just lists of numbers, identical in shape, with no visible marker separating them —
  which is exactly what makes §7.2's bug hard to catch by inspection.

---

## 5. Detailed technical explanation

### 5.1 Storage scales linearly with dimensions, and separately with precision

`[REAL]` §7.1 computed storage for a 1,000,000-document corpus:

| Dimensions | float32 | float16 | int8 (quantized) |
|---|---|---|---|
| 256 | 1.02 GB | 0.51 GB | 0.26 GB |
| 768 | 3.07 GB | 1.54 GB | 0.77 GB |
| 3,072 | **12.29 GB** | 6.14 GB | 3.07 GB |

**Going from 256 to 3,072 dimensions is a 12× storage multiplier**, at identical corpus size and
precision. **Quantization is a separate, independent lever** — dropping from float32 to int8 recovers a
4× saving at *any* dimension count, without discarding a single dimension. Neither lever is free:
lower precision and fewer dimensions each risk losing some of the nuance a larger, higher-precision
embedding would have captured. The right trade-off is empirical, not assumed (M6-L13 gives you the
metrics to measure it).

### 5.2 Same shape, different meaning

`[REAL, hand-built]` §7.2 built two 4-dimensional "embedding models" over the same six words, each
internally sensible but using genuinely different axes:

| Comparison | Cosine similarity |
|---|---|
| Model A query "refund" vs Model A doc "invoice" (correct pairing) | **1.00** |
| Model A query "refund" vs Model B doc "invoice" (**mixed**) | **0.07** |

**Both numbers are computed correctly.** The second one is meaningless — not low-quality, not
approximately right, simply **not a measurement of anything**, because Model A's axis 0 and Model B's
axis 0 do not represent the same concept. **The practical triggers for this bug are mundane**: querying an
index with the wrong model by a configuration error, or — more insidious — **upgrading to a newer version
of "the same" model**, whose retraining run can land on a different coordinate system even at identical
dimensionality and even with a similar-sounding name.

### 5.3 When cosine and Euclidean distance disagree, and when they must agree

`[REAL, exact identity verified]` §7.3 built three documents relative to one query, one of them sharing
the query's **exact direction** at a much larger magnitude:

| | Cosine similarity | Euclidean distance |
|---|---|---|
| Document in query's exact direction, large magnitude | **1.000** (ranked #1) | **2.828** (ranked #3 — last) |
| Document close to query's direction, small magnitude | 0.995 (ranked #2) | 0.141 (ranked #1) |

**The rankings disagree completely**, because Euclidean distance is sensitive to magnitude and cosine
similarity is not. After normalizing every vector to unit length:

| | Cosine (unit vectors) | Euclidean (unit vectors) |
|---|---|---|
| Same document | **1.000** (ranked #1) | **0.000** (ranked #1) |

**The rankings now agree exactly**, and this is provable, not coincidental: for unit vectors,
`‖a−b‖² = 2 − 2·cos(a,b)` — §7.3 verifies this identity numerically. **This is why normalizing vectors
once, at index time, and then using the cheaper, division-free dot product (M3-L02) is standard
practice**: it produces results identical to cosine similarity, and both then agree with Euclidean
distance too.

### 5.4 Guarding against the model-compatibility bug

Since §5.2's bug produces no error, the defence has to be structural, not reactive:

| Control | What it catches |
|---|---|
| Tag every stored vector with model name and version | A query embedded by a different model is a detectable mismatch, not a silent one |
| Fingerprint the embedding configuration (M5-L12's discipline, applied to embeddings) | A version bump is a version bump, not an invisible drift |
| Re-index rather than mix, on any model change | Never leaves old-model and new-model vectors compared against each other |

This is the same principle M5-L12 established for prompt artefacts, applied to a different kind of
artefact: **if changing it can change what a comparison means, it needs a version tag.**

### 5.5 Assumptions and limitations

- §7.1's dimension counts and precisions are real, common values; exact storage overhead (indexing
  structures, metadata) is not included and will add further cost — treat this as a floor, not a total.
- §7.2's two "models" are small and deliberately, visibly mismatched for teaching purposes. A real
  model-compatibility bug between two trained models would not be this obvious on inspection — that is
  precisely what makes it dangerous in practice.
- §7.3's identity is exact mathematics (M3-L02), not an approximation; it holds for any unit vectors in
  any number of dimensions, not just the two-dimensional example shown.

---

## 6. Worked example — the search quality drop nobody could explain

**The system.** A document search feature has run for months on embeddings from "Model V1." Search
quality is good and stable.

**The change.** The embedding provider releases "Model V2" — same name family, same 768 dimensions, faster
and cheaper. A team member updates the embedding calls to use V2 for new documents, planning to re-embed
the rest "later," expecting a routine, low-risk upgrade since the interface is identical and the
dimension count hasn't changed.

**What happened.** Search quality degraded sharply and unpredictably. Some queries returned excellent
results; others returned results that made no sense at all. Nothing crashed. No error appeared anywhere.
The team spent days suspecting the ranking logic, the query preprocessing, and the underlying documents
themselves.

**What was actually happening.** Every query embedded with V2 was being compared, via cosine similarity,
against a mix of V1-embedded documents (the old majority) and V2-embedded documents (the new minority) —
exactly §7.2's bug, produced by a routine model upgrade rather than a configuration mistake. The
comparisons against V1 documents were computing real numbers that meant nothing, exactly as
demonstrated in the lab, and — because some V1 and V2 vectors happened to be coincidentally similar in a
few cases — the failure was inconsistent enough to look like noise rather than a structural bug.

**Three defects:**

| # | Defect | Consequence |
|---|---|---|
| 1 | No version tag stored alongside each vector | Nothing distinguished a V1 vector from a V2 vector at query time |
| 2 | The upgrade mixed models in one index instead of re-indexing | Every cross-model comparison silently returned meaningless numbers |
| 3 | No test caught it before launch | The bug's inconsistent symptom (works sometimes) delayed diagnosis by days |

### The fix

**Tag every vector with its model and version** (§5.4), so a query's model can be checked against a
document's before any comparison is trusted.

**Treat a model version change as an artefact change requiring a full re-index** (M5-L12's discipline,
applied here) — never let two models' vectors coexist in one comparable index.

**Test with a query known to fail under a mismatch** (analogous to §7.2's "refund" query) as part of any
embedding-model upgrade process, so the failure is caught before launch, not discovered as unexplained
quality drift afterward.

**The general rule.** **A dimension count matching is not compatibility. Compatibility is a property of
the model that produced the vectors, and it must be tracked as explicitly as a prompt's version (M5-L12)
— because nothing about the vectors themselves will tell you when it has silently changed.**

---

## 7. Practical activity

**File:** [`labs/m6/l02_embedding_dimensions.py`](../../labs/m6/l02_embedding_dimensions.py)

**No API key, no network, no model download.**

```bash
source .venv/bin/activate
python labs/m6/l02_embedding_dimensions.py
```

Every number is exact, reproducible vector arithmetic.

### 7.2 Expected output

`[EXECUTED]` — 2026-09-09, Python 3.10.11, NumPy 2.2.6.

```text
============================================================================
1. STORAGE COST SCALES WITH DIMENSION COUNT
============================================================================
  A 1,000,000-document corpus. Storage = dimensions x bytes/value x count.

   dimensions             float32             float16    int8 (quantized)
          256             1.02 GB             0.51 GB             0.26 GB
          384             1.54 GB             0.77 GB             0.38 GB
          768             3.07 GB             1.54 GB             0.77 GB
         1536             6.14 GB             3.07 GB             1.54 GB
         3072            12.29 GB             6.14 GB             3.07 GB

  Going from 256 to 3072 dimensions is a 12x storage multiplier, at the SAME corpus
  size and the SAME numeric precision. More dimensions can capture
  more nuance, but it is never free -- storage, memory, and the cost
  of every downstream similarity computation all scale with it.
  int8 quantisation recovers most of the float32-vs-float16 saving
  again without dropping dimensions at all -- a separate lever.

============================================================================
2. SAME DIMENSION COUNT DOES NOT MEAN COMPATIBLE SPACES
============================================================================
  Two 4-dimensional embedding models over the SAME six words. Both
  are internally sensible -- 'refund' and 'invoice' are close within
  each model, 'delivery' and 'tracking' are close within each model.
  Neither model's axes correspond to the other's in any way.

  Query embedded with MODEL A: 'refund'
  comparison                             cosine similarity
  A query vs A doc 'invoice'                          1.00
  A query vs A doc 'delivery'                         0.00
  A query vs A doc 'login'                            0.00

  A query vs B doc 'invoice' (MIXED)                  0.07
  A query vs B doc 'delivery' (MIXED)                 0.00
  A query vs B doc 'login' (MIXED)                    0.00

  Read the two blocks. Comparing A's query against A's documents
  correctly ranks 'invoice' highest (same topic as 'refund'). Mixing
  A's query against B's documents produces DIFFERENT numbers -- not
  an error, not a crash, just numbers, computed correctly by
  `cosine()`, that mean nothing, because dimension 0 in model A and
  dimension 0 in model B are not the same concept. This is what
  happens, silently, if a document index built with one embedding
  model is ever queried with a DIFFERENT model -- including a new
  version of 'the same' model, whose training run landed on a
  different coordinate system even at identical dimensionality.

============================================================================
3. NORMALIZATION: WHEN COSINE AND EUCLIDEAN AGREE, AND WHEN THEY DON'T
============================================================================
  Un-normalised vectors. One document shares the query's exact
  direction but has a much larger magnitude (e.g. a longer, summed-
  not-averaged document embedding).

  document                cosine similarity  Euclidean distance
  doc_small_same_dir                  0.995               0.141
  doc_LARGE_same_dir                  1.000               2.828
  doc_different_dir                   0.958               0.424

  Ranked by cosine (best first):    ['doc_LARGE_same_dir', 'doc_small_same_dir', 'doc_different_dir']
  Ranked by Euclidean (best first): ['doc_small_same_dir', 'doc_different_dir', 'doc_LARGE_same_dir']

  The rankings DISAGREE. 'doc_LARGE_same_dir' points in EXACTLY the
  query's direction -- cosine similarity says it is the best match,
  correctly. Euclidean distance ranks it WORST, purely because of its
  magnitude, which has nothing to do with meaning here.

  Now normalise every vector to unit length first:
  document                cosine (unit vectors)  Euclidean (unit vectors)
  doc_small_same_dir                      0.995                     0.100
  doc_LARGE_same_dir                      1.000                     0.000
  doc_different_dir                       0.958                     0.290

  Ranked by cosine (unit vectors):    ['doc_LARGE_same_dir', 'doc_small_same_dir', 'doc_different_dir']
  Ranked by Euclidean (unit vectors): ['doc_LARGE_same_dir', 'doc_small_same_dir', 'doc_different_dir']
  Rankings now agree: True

  Identity check on 'doc_small_same_dir': ||a-b||^2 = 0.0099, 2 - 2*cos(a,b) = 0.0099 -- equal, exactly, for unit vectors.
  This is why normalising once at index time and then using the
  cheaper, division-free dot product (M3-L02) is standard practice:
  it gives IDENTICAL rankings to cosine similarity, and both agree
  with Euclidean distance too, once every vector has unit length.

============================================================================
4. WHAT THIS LAB IS AND IS NOT
============================================================================
  REAL: every number in this lab is exact, reproducible vector
  arithmetic -- no simulation, no approximation.

  ILLUSTRATIVE: section 2's two 'models' are small, hand-built
  stand-ins for the real phenomenon of two trained embedding models
  (or two versions of one model) landing on different coordinate
  systems. A real pair of incompatible models would not be this
  obviously mismatched to inspect by eye -- that is what makes the
  real version dangerous: it looks fine until you check.

  NOT SHOWN: how to detect a model-mismatch bug in a real running
  system (checking a model/version tag stored per vector is the
  practical fix, mirroring M5-L12's artefact-fingerprint discipline
  applied to embeddings instead of prompts), and how vector indexes
  actually implement these distance metrics at scale -- M6-L05
  onward.

Done.
```

### 7.3 Reading the result

**Section 1 turns "how many dimensions" into a budgeting question**, the same way M5-L15 turned token
counts into a cost question — a 12× spread across common real-world dimension counts, before even
considering precision.

**Section 2 is the lesson's most important warning.** `0.07` is not "a bit off" — it is a number
computed correctly by a correct function, describing a comparison that has no meaning. Nothing in the
output format distinguishes it from a legitimate low-similarity score. That indistinguishability is the
entire danger.

**Section 3 turns a common piece of engineering folklore — "normalize your vectors" — into something
provable.** The identity holds exactly, in any number of dimensions, which is why it is safe to rely on
as a design rule rather than a rule of thumb.

---

## 8. Common mistakes and troubleshooting

1. **Comparing vectors from two different embedding models or versions.** §5.2, §6 — produces silent,
   meaningless results.
2. **Assuming a model upgrade with the same dimension count is a safe, drop-in replacement.** §6 —
   dimension count says nothing about coordinate-system compatibility.
3. **Mixing normalized and un-normalized vectors in the same index.** Breaks the identity in §5.3;
   rankings become inconsistent in ways that are hard to diagnose.
4. **Using Euclidean/L2 distance on un-normalized vectors without checking whether magnitude carries
   meaning.** §7.3 shows this can invert a ranking entirely.
5. **Choosing dimension count without pricing the storage trade-off.** §5.1 — always compute it before
   committing to a model.
6. **Not tagging stored vectors with model/version.** The single control that would have caught §6's
   incident before launch.
7. **Assuming quantization and dimension reduction are the same lever.** They are independent (§5.1) and
   have different trade-offs.
8. **Treating a "same name" model family as automatically comparable across versions.** Verify, per §5.4,
   rather than assume.

| Symptom | Likely cause | Fix |
|---|---|---|
| Search quality degrades unpredictably after a model/provider change | Mixed-model comparison (§5.2) | Tag vectors by model/version; re-index rather than mix |
| Search results seem biased toward longer or shorter documents | Magnitude-sensitive distance metric on un-normalized vectors | Normalize vectors; use cosine or normalized dot product (§5.3) |
| Storage costs far exceed estimates | Dimension count or precision not budgeted in advance | Compute storage per §5.1 before choosing a model |
| Two similarity scores for the "same" comparison disagree between systems | One system normalizes, the other doesn't | Standardize on normalized vectors + dot product throughout |

---

## 9. Security, privacy, reliability, cost

- **Reliability.** Never compare vectors from different embedding models or versions without an explicit
  compatibility check — §5.2's bug produces no error, ever.
- **Reliability.** Tag every stored vector with the model and version that produced it (§5.4) — the
  single most effective, cheapest control against §6's failure mode.
- **Cost.** Price dimension count and precision together before choosing an embedding model — §5.1
  showed a 12× storage spread across common real dimension counts alone.
- **Reliability.** Standardize on normalized vectors and a consistent distance metric throughout a
  system, to avoid the ranking disagreements demonstrated in §5.3.
- **Cost.** Quantization (int8) is a largely-free way to cut storage further, independent of dimension
  count — evaluate it before defaulting to a smaller embedding model purely to save space.

---

## 10. Exercises

### Exercise 1 — Beginner (~20 min)

1. Compute the storage, in GB, for 500,000 documents at 1,536 dimensions in float32.
2. Why does "same dimension count" not imply "compatible embeddings"?
3. Name one realistic, non-obvious trigger for a model-compatibility bug.
4. In your own words, why do cosine similarity and Euclidean distance agree on normalized vectors?
5. What is the cheapest control against the model-compatibility bug?

### Exercise 2 — Intermediate (~40 min)

1. Run the lab. Confirm the storage figures for 768 dimensions at float16 by hand.
2. Extend section 2 with a third toy "Model C" and demonstrate that mixing it with Model A produces
   equally meaningless results.
3. Using section 3's setup, add a fourth document whose magnitude is even larger than
   `doc_LARGE_same_dir` but points in a slightly different direction, and report how the pre- and
   post-normalization rankings change.
4. Verify the identity `‖a−b‖² = 2 − 2·cos(a,b)` by hand on two simple unit vectors of your choosing.
5. Design a vector-tagging schema (fields and types) for a real or hypothetical vector store.

### Exercise 3 — Challenge (~50 min)

1. Build a small function that raises an error if two vectors being compared have mismatched
   model/version tags, and test that it catches a simulated mismatch.
2. Implement and time (roughly) dot product vs cosine similarity on normalized vectors at a larger scale
   (e.g. 10,000 random vectors) to observe the practical cost difference M3-L02 predicts.
3. Design an embedding-model upgrade runbook: the steps, checks and rollback plan for moving a production
   vector index from one model version to another without a §6-style incident.
4. Research (conceptually) how a real vector database exposes a choice of distance metric (cosine, L2,
   inner product) and write up which you would choose for a normalized vs an un-normalized embedding
   model.
5. Extend section 1's storage calculation to include a rough estimate of index overhead (e.g. HNSW graph
   structure, a preview of M6-L06) and discuss how much it changes the total.

---

## 11. Quiz

*(Answers: [`answer-keys/module-06-answers.md`](../../answer-keys/module-06-answers.md#m6-l02).)*

**Q1.** Going from 256 to 3,072 dimensions, at the same corpus size and precision, in §7.1, multiplied
storage by:

- A. 3x
- B. 6x
- C. 12x, exactly proportional to the dimension increase.
- D. It stayed the same, since precision did not change.

**Q2.** Why does int8 quantization reduce storage without reducing dimension count, per §5.1?

- A. It stores each value in fewer bytes, a separate lever from how many values (dimensions) each vector has.
- B. It removes the least important dimensions automatically.
- C. It compresses the entire corpus using a shared dictionary.
- D. It only applies to documents, never to queries.

**Q3.** In §7.2, comparing Model A's query vector against Model B's document vectors produced valid-
looking cosine similarity numbers that were nevertheless meaningless. The reason is:

- A. The `cosine()` function had a bug when given cross-model vectors.
- B. Model B's vectors were corrupted.
- C. The dimension counts did not actually match.
- D. The two models' dimensions do not correspond to the same concepts, even though both models have the same dimension count.

**Q4.** Per §5.2, which of the following is a realistic real-world trigger for the model-compatibility bug
demonstrated in §7.2?

- A. Adding a new document to an existing, single-model index.
- B. Upgrading to a new version of "the same" embedding model, whose training run can land on a different coordinate system.
- C. Increasing the number of documents returned by a search query.
- D. Switching from cosine similarity to Euclidean distance on the same vectors.

**Q5.** Why is the model-mismatch bug in §7.2 described as dangerous rather than merely wrong?

- A. It only affects small embedding models.
- B. It always causes a visible crash immediately.
- C. It produces no error or crash — just numbers that look valid but are meaningless, indistinguishable from a correct result without checking.
- D. It can only occur when using int8 quantization.

**Q6.** In §7.3, before normalization, cosine similarity ranked "doc_LARGE_same_dir" first while Euclidean
distance ranked it last. The cause was:

- A. A rounding error in the Euclidean distance formula.
- B. The document was actually about a different topic.
- C. Cosine similarity is always more accurate than Euclidean distance.
- D. The document's much larger magnitude, which Euclidean distance is sensitive to and cosine similarity is not.

**Q7.** After normalizing all vectors to unit length in §7.3, cosine and Euclidean rankings:

- A. Became identical, and the lab verified this follows from an exact mathematical identity, not coincidence.
- B. Remained different, since normalization only affects cosine similarity.
- C. Became undefined for all documents.
- D. Diverged even further than before.

**Q8.** The identity verified in §7.3 (`‖a−b‖² = 2 − 2·cos(a,b)` for unit vectors) explains why:

- A. Euclidean distance should never be used in vector search.
- B. Normalizing vectors once and then using the cheaper dot product gives results identical to cosine similarity.
- C. Dimension count must always be a power of two.
- D. Cosine similarity can exceed a value of 1.

**Q9.** Per §5.2's forward reference, the practical fix for the model-compatibility risk is best
summarized as:

- A. Always use the highest possible dimension count.
- B. Disable normalization to preserve magnitude information.
- C. Retrain the embedding model from scratch before every query.
- D. Tagging every stored vector with the model/version that produced it, the same artefact discipline M5-L12 applied to prompts.

**Q10.** The general lesson from comparing sections 1 and 2 of this lesson is:

- A. Higher dimension counts always guarantee model compatibility.
- B. Storage cost and model compatibility are the same concern.
- C. Dimension count alone describes storage cost, not whether two sets of vectors can be meaningfully compared.
- D. Model compatibility only matters above 1,536 dimensions.

**Q11.** A document embedding built by summing (not averaging) its word vectors would tend to have a
magnitude that:

- A. Stays constant regardless of document length.
- B. Grows with document length, which per §7.3 can bias an unnormalized Euclidean-distance search toward or against longer documents for reasons unrelated to relevance.
- C. Is always smaller than any individual word vector.
- D. Has no effect on any distance metric.

**Q12.** This lesson's central practical rule is:

- A. Verify both the numeric precision/dimension trade-off and model/version compatibility before trusting a vector similarity score.
- B. Always prefer the model with the most dimensions available.
- C. Normalization is optional and rarely matters in practice.
- D. Model compatibility issues are always caught automatically by the search system.

**Q13.** *(Written, rubric-graded.)* In under 150 words: your team plans to upgrade a production
embedding model to a newer version with the same dimension count, re-embedding only newly added documents
going forward to save cost. State the specific risk in this plan, referencing this lesson's lab, and what
you would require before approving it.

---

## 12. Revision notes

- **Dimension count and storage cost scale together, exactly.** Measured: a 12× storage multiplier from
  256 to 3,072 dimensions at fixed precision. Quantization is a separate, independent lever.
- **Same dimension count does not mean compatible vector spaces.** Measured: a cross-model comparison
  produced a valid-looking 0.07 cosine similarity that meant nothing, because the two models' axes do not
  correspond.
- **The model-compatibility bug is silent by construction** — no error, no crash, a plausible-looking
  wrong number. The realistic trigger is often a routine model version upgrade, not a configuration
  mistake.
- **Cosine similarity and Euclidean distance can rank identically-meaningful documents in opposite
  order** when magnitude varies and vectors are not normalized. Measured: a complete ranking reversal in
  §7.3.
- **Normalizing fixes this exactly, not approximately** — `‖a−b‖² = 2 − 2·cos(a,b)` for unit vectors,
  verified numerically. This is why normalize-once-then-dot-product is standard practice (M3-L02).
- **Tag every stored vector with its model and version.** The cheapest, most effective defence against
  the model-compatibility bug, mirroring M5-L12's artefact discipline.
- **Treat any embedding-model change as requiring a full re-index**, never a gradual mix of old and new
  vectors in one comparable index.

---

## 13. Completion checklist

- [ ] I can compute embedding storage cost from dimension count, precision, and corpus size.
- [ ] I can explain why identical dimension count does not imply compatible embedding spaces.
- [ ] I know at least one realistic, non-obvious trigger for a model-compatibility bug.
- [ ] I can state and verify the identity connecting cosine similarity and Euclidean distance for unit vectors.
- [ ] My vector storage design tags every vector with its producing model and version.
- [ ] I never mix vectors from different models/versions in one comparable index.
- [ ] I use normalized vectors and a consistent distance metric throughout any system I build.
- [ ] I scored 10/13 on the quiz.

---

## 14. References

- Amazon Web Services — pgvector distance operators and normalization guidance.
  <https://github.com/pgvector/pgvector> `[UNVERIFIED]`
- Reimers, N. and Gurevych, I. (2019), *Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks*
  (real sentence-embedding model behaviour, contrasted with this lesson's hand-built illustration).
  <https://arxiv.org/abs/1908.10084> `[UNVERIFIED]`

---

## 15. Next lesson

→ [M6-L03 — Keyword Search and BM25 — Computed by Hand](M6-L03-bm25.md)

You now know how to size, compare and safely combine embedding vectors. Next: the other half of hybrid
search — the keyword-ranking algorithm that exact match actually uses in practice, worked by hand the
same way cosine similarity was in M3-L02.
