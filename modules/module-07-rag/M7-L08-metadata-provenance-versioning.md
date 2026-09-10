# M7-L08 — Metadata, Identifiers, Provenance and Versioning

| | |
|---|---|
| **Lesson ID** | M7-L08 |
| **Difficulty** | 2 (Intermediate) |
| **Estimated study time** | 1.75 hours |
| **Prerequisites** | [M7-L06](M7-L06-chunking-size-overlap-boundaries.md) |

---

## 1. Learning objectives

1. **Design** a chunk record schema that carries source, version, currency, and provenance alongside its
   text.
2. **Demonstrate** that a stale and a current chunk can be equally retrievable without version metadata,
   and resolve the ambiguity by filtering on it.
3. **Explain** why provenance metadata is what makes a citation verifiable at all.
4. **Demonstrate** why position-based chunk identifiers can silently point to different content after
   re-chunking, and why content-hash-based identifiers cannot.
5. **Apply** metadata filtering at query time using this lesson's schema, building on M6-L09's mechanics.

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **Provenance** | The traceable record of where a piece of content came from — source, version, and when it was captured. |
| **Currency (is_current)** | A flag indicating whether a specific version of a document is the authoritative, up-to-date one. |
| **Position-based identifier** | A chunk ID derived from where a chunk sits in a document (e.g. its index), rather than from its content. |
| **Content-hash-based identifier** | A chunk ID derived from a deterministic hash of the chunk's own text (M7-L03), guaranteeing identical text always produces the identical ID. |
| **Silent identity mismatch** | The specific failure where the same identifier refers to different content at two points in time, with nothing signaling the change. |

---

## 3. Plain-language explanation

### 3.1 M7-L07 finished the chunking toolkit; this lesson finishes the chunk itself

Every prior lesson in this module treated a chunk as text (plus, since M7-L03, a content-hash ID). This
lesson asks what else a chunk needs to carry to be trustworthy, citable, and safely manageable over time —
the metadata layer every later lesson (M7-L12's citations, M7-L15's permissions, M7-L16's updates) assumes
already exists.

### 3.2 Two equally-good-looking answers, only one of them current

§7.2 is this lesson's central demonstration: an old and a new version of the same policy, differing only in
one number, score identically against the same query. Nothing in the text or the retrieval score says
which one is authoritative — that information has to live in metadata, or it doesn't exist at all.

### 3.3 A citation is only as good as what it points to

§7.3 makes concrete something easy to take for granted: a citation is only useful if a reader can actually
go check it. That requires the retrieved chunk to carry its source, not just its words.

### 3.4 An identifier can lie about stability

§7.4 is the lesson's sharpest, least obvious finding: after changing chunk size, the *same ID string*
referred to *different text* in every single case for a position-based scheme — a failure mode worse than
an ID simply changing, because nothing signals that anything happened at all.

### 3.5 Filtering needs something to filter on

§7.5 closes the loop back to M6-L09: filtering mechanics were already covered there. This lesson supplies
the actual fields — department, version, currency — that any of those mechanics operate on.

---

## 4. Analogy

**A library card catalog versus a pile of loose photocopied pages.** A photocopied page has words on it,
and that's all — no way to tell which book it came from, what edition, or whether a newer edition has since
corrected it. A proper catalog card carries the book's call number, edition, and acquisition date alongside
its summary — which is what lets a librarian confidently tell a patron "this is the current edition," pull
the exact source to verify a quote, or notice that an older edition sitting on a back shelf has been
superseded. A catalog card's call number is assigned by content and subject, not by which drawer it happens
to sit in today — move the card to a different drawer, and the number still means the same book.

### Where the analogy breaks

- **A library's call number rarely gets reassigned to a different book.** §7.4's silent-mismatch danger —
  the same ID quietly pointing to different content — has no everyday library equivalent; it is a
  specifically digital failure mode.
- **A patron can visually flip through a photocopy and notice it looks old.** §7.2's stale-vs-current
  ambiguity is invisible by design — the text itself gives no visual or textual cue that it's outdated.

---

## 5. Detailed technical explanation

### 5.1 What a chunk record actually needs

`[REAL]` §7.1 built a chunk record carrying `chunk_id` (content-hash-based, per M7-L03), `text`,
`source_uri`, `source_document_id`, `chunk_index`, `document_version`, `is_current`, `ingested_at`, and an
open `metadata` dict for domain-specific fields (e.g. department). **None of this is decorative** — each
field is what a later section of this lesson demonstrates is load-bearing.

### 5.2 Version ambiguity, measured and resolved

`[REAL, measured]` §7.2 indexed two chunks — the same PTO policy sentence before and after a real change
(fifteen days → twenty days) — and scored both against "how many PTO days do I get." **Both scored exactly
1.000.** Nothing about the text or the score distinguishes the stale version from the current one; a naive
pipeline could surface either with equal confidence and an equally plausible-looking answer. Filtering the
candidate set to `is_current=True` **before** scoring left exactly one chunk — **the ambiguity resolved
structurally, by metadata, not by hoping the scoring function happens to prefer the right one** (it has no
way to, since nothing about "twenty" is inherently more relevant than "fifteen" to this query).

### 5.3 Provenance and verifiability

`[REAL]` §7.3 constructed the same retrieved text as two citations: one bare ("source unknown"), one
carrying source URI, version, and ingestion timestamp. **Only the second can actually be checked** — opened,
compared against the live document, confirmed current or flagged as historical. M7-L12's citation-quality
lesson assumes this metadata is already present on every chunk; this is where it has to originate.

### 5.4 The silent identity mismatch, measured

`[REAL, measured]` §7.4 re-chunked one document at two different sizes (40 vs. 35 characters) and compared
identifier schemes. **Position-based IDs (`doc1_pos0`, `doc1_pos1`, `doc1_pos2`) were identical strings
before and after — and every single one now pointed to genuinely different text.** This is a sharper
failure than IDs simply changing: **a cache, diff tool, or incremental-update check keyed on this ID (M7-L16's
topic) would see the same key and could conclude nothing had changed, when the entire chunk's content had.**

**Content-hash-based IDs cannot have this specific failure, by construction**: an ID derived from a hash of
its own text guarantees that if the same ID appears twice, the text is identical both times — there is no
mechanism by which it could be otherwise. This does **not** mean hash-based IDs stay stable across
re-chunking in general — in this lab's own measurement, 0 hash-based IDs were shared between the two
chunkings, because changing chunk size shifted nearly every boundary. **The guarantee is narrower and more
precise than "IDs don't change"**: it is "a shared ID can never silently mean different content."

### 5.5 Metadata filtering, using this lesson's schema

`[REAL]` §7.5 filtered a 3-chunk corpus down to 2 chunks tagged `department=HR`, reusing M6-L09's
filtering mechanics directly. **M6-L09 already covered how to filter (pre-filter vs. post-filter,
filtered-ANN); this lesson supplies what gets filtered on** — the schema itself.

### 5.6 Assumptions and limitations

- This lesson's specific schema (chunk_id, source_uri, version, is_current, etc.) is one reasonable
  design, not a universal standard — real systems vary in which fields they track.
- This lesson does not cover the actual workflow that flips `is_current` when a document changes (M7-L16),
  permission-aware access-control filtering specifically (M7-L15, distinct from the department-tagging
  shown here), or citation rendering in a real generated answer (M7-L12).

---

## 6. Worked example — the audit that found two contradictory policies, both "current"

**The system.** A compliance team audits a RAG assistant's answers against the company's actual policy
documents. They discover the assistant has, on different occasions, cited two different PTO accrual
figures for the same tier — both from chunks that appeared, from the assistant's own output, to be
legitimate.

**What was actually happening.** The corpus had been re-ingested after a policy update, but the old
chunk had never been marked superseded — both the old and new chunks sat in the index side by side, both
retrievable, both without any version field to distinguish them, exactly reproducing §5.2's measured
ambiguity at production scale.

**Why the audit, not routine monitoring, caught it.** Per §5.2, nothing about either individual answer
looked wrong — each was a fluent, confident, plausible statement of a specific policy figure. The
contradiction was only visible when someone compared two separate answers to the same underlying question,
asked at different times.

**Three defects:**

| # | Defect | Consequence |
|---|---|---|
| 1 | Re-ingestion added new chunks without marking prior versions as superseded | Old and new chunks coexisted indefinitely, both retrievable |
| 2 | No `is_current` (or equivalent) field existed in the chunk schema at all | There was no metadata field available to filter on, even after the problem was found |
| 3 | No provenance (version, ingestion date) was attached to citations | Individual wrong answers gave no signal, from their own citation, that they might be outdated |

### The fix

**Add a currency field to the chunk schema and enforce it at every re-ingestion**, per §5.1-§5.2 — a
superseded document's chunks should be explicitly marked, not left ambiguous alongside their replacement.

**Filter to current chunks before scoring/generation as a standing pipeline step**, not as a one-off fix —
per §5.2, this resolves the ambiguity structurally rather than relying on scoring to happen to prefer the
right version.

**Attach provenance (source, version, timestamp) to every citation a generated answer produces**, per
§5.3 — this is what would have let the audit (or an end user) catch the contradiction from a single
answer, rather than needing to compare two.

**The general rule.** **A corpus that is updated without an explicit currency mechanism will, eventually,
contain contradictory "current" answers to the same question — and nothing about any single answer's
fluency will reveal which one to trust without metadata that says so explicitly.**

---

## 7. Practical activity

**File:** [`labs/m7/l08_metadata_provenance_versioning.py`](../../labs/m7/l08_metadata_provenance_versioning.py)

**No API key, no network, no third-party dependencies.** Runs in well under a second.

```bash
source .venv/bin/activate
python labs/m7/l08_metadata_provenance_versioning.py
```

### 7.2 Expected output

`[EXECUTED]` — 2026-09-10, Python 3.10.11 (pure standard library).

```text
============================================================================
1. A CHUNK RECORD IS MORE THAN JUST TEXT
============================================================================
  A chunk is not just its text -- it's text PLUS the context needed to
  trust, cite, and manage it. One example record:

    chunk_id: 'pto-policy_v1_c0_f2a77f1881'
    text: 'Full time employees accrue fifteen days of PTO per year.'
    source_uri: 'hr-portal://policies/pto-policy'
    source_document_id: 'pto-policy'
    chunk_index: 0
    document_version: 1
    is_current: False
    ingested_at: '2026-01-15T09:00:00Z'
    metadata: {'department': 'HR'}

  M7-L03 already established WHY a chunk needs a content-hash-based id
  (idempotent re-ingestion, change detection). Everything else here --
  source, version, currency, timestamp -- is what the rest of this
  lesson demonstrates is load-bearing, not decorative.

============================================================================
2. WITHOUT VERSION METADATA, A STALE CHUNK IS INDISTINGUISHABLE FROM A CURRENT ONE
============================================================================
  Query: 'how many PTO days do I get'

  Without filtering by version, BOTH chunks retrieve equally well:
    pto-policy_v1_c0_f2a77f1881  (v1, current=False)  score=1.000  text='Full time employees accrue fifteen days of PTO per year.'
    pto-policy_v2_c0_d06dbddfa9  (v2, current=True)  score=1.000  text='Full time employees accrue twenty days of PTO per year.'

  Scores are IDENTICAL: True. Nothing about the TEXT or its SCORE
  reveals which one is current -- 'fifteen' and 'twenty' are just words
  to a retrieval system with no version awareness. A naive pipeline
  could just as easily surface the STALE policy as the current one,
  with no error, no warning, and a fully plausible-looking citation.

  Filtering to is_current=True BEFORE scoring/generation (M6-L09's
  metadata-filtering pattern, applied to version currency):
    pto-policy_v2_c0_d06dbddfa9  (v2)  text='Full time employees accrue twenty days of PTO per year.'
  Exactly 1 chunk remains -- the ambiguity is resolved
  structurally, by metadata, not by hoping retrieval happens to prefer
  the right one.

============================================================================
3. PROVENANCE IS WHAT MAKES A CITATION VERIFIABLE
============================================================================
  The SAME retrieved text, cited two ways:

  WITHOUT provenance metadata: "Full time employees accrue twenty days of PTO per year." (source unknown)
  WITH provenance metadata:    "Full time employees accrue twenty days of PTO per year." (Source: hr-portal://policies/pto-policy, version 2, ingested 2026-06-01T09:00:00Z)

  The first citation cannot be checked by a reader at all -- there is
  no way to go verify it against the actual source, or to notice it
  might be an old version. The second can be opened, checked against
  the live document, and its version explicitly confirmed. M7-L12's
  citation-quality lesson assumes metadata like this already exists;
  this is where it has to come from.

============================================================================
4. IDENTIFIER STABILITY ACROSS RE-CHUNKING
============================================================================
  Re-chunking the SAME document after changing chunk size from 40 to 35 characters (e.g. after adopting M7-L07's
  recursive splitting instead of fixed-size):

  Position-based IDs:
    Before: [('doc1_pos0', 'Remote work requires manager approval. E'), ('doc1_pos1', 'xpense reports are due within thirty day'), ('doc1_pos2', 's. PTO accrues yearly.')]
    After:  [('doc1_pos0', 'Remote work requires manager approv'), ('doc1_pos1', 'al. Expense reports are due within '), ('doc1_pos2', 'thirty days. PTO accrues yearly.')]

    3 of 3 IDs are the SAME string before and after (['doc1_pos0', 'doc1_pos1', 'doc1_pos2']).
    Of those, 3 now point to DIFFERENT text than before:
      doc1_pos1:  before='xpense reports are due within thirty day'
                  after ='al. Expense reports are due within '
      doc1_pos0:  before='Remote work requires manager approval. E'
                  after ='Remote work requires manager approv'
      doc1_pos2:  before='s. PTO accrues yearly.'
                  after ='thirty days. PTO accrues yearly.'

  This is the dangerous case: the ID looks stable (same string, both
  times), but SILENTLY refers to different content after re-chunking --
  a cache, a diff tool, or an incremental-update check keyed on this ID
  (M7-L16's topic) could easily conclude 'nothing changed here' when
  everything did. Position-based IDs encode WHERE a chunk was, not
  WHAT it contains, so they cannot detect this at all.

  Content-hash-based IDs: 0 shared between before and after.
  Of those, 0 point to different text -- by construction, this can
  never be more than 0: a hash-based ID is DERIVED from its text, so the
  same ID appearing twice is a mathematical guarantee the text is
  identical both times. Re-chunking at a different size changes almost
  every chunk's exact boundaries, so most hash IDs churn here too -- but
  unlike position-based IDs, a hash-based ID can NEVER silently point to
  different content, which is the property M7-L16's incremental-update
  and change-detection logic depends on.

============================================================================
5. METADATA FILTERING AT QUERY TIME
============================================================================
  Full corpus: 3 chunks across HR and IT.
  Filtered to department=HR (M6-L09's metadata-filtering pattern, reusing this lesson's schema): 2 chunks
    remote-policy_v1_c0_d67210ed9a: 'Remote work requires manager approval.'
    expense-policy_v1_c0_ea82b33302: 'Expense reports are due within thirty days.'

  None of this filtering logic is new -- M6-L09 already covered pre-
  filtering vs. post-filtering mechanics in depth. What this lesson
  adds is the SCHEMA (which fields exist, what they mean) that any of
  M6-L09's filtering techniques actually filters ON.

============================================================================
6. WHAT THIS LAB IS AND IS NOT
============================================================================
  REAL: every chunk record, hash, filter, and comparison in this lab
  is genuinely constructed and computed; the version-ambiguity scores
  (section 2) and the ID-stability comparison (section 4) are measured
  on real, executed code, not asserted.

  ILLUSTRATIVE: the chunk-record schema (chunk_id, source_uri, version,
  is_current, etc.) is one reasonable design, not a universal standard --
  real systems vary in exactly which fields they track.

  NOT SHOWN: a real versioning workflow (how 'is_current' actually gets
  flipped when a document changes -- M7-L16's topic); permission-aware
  filtering specifically for access control (M7-L15's topic, distinct
  from the department-tagging shown here); and citation rendering in
  a real generated answer (M7-L12's topic).

Done.
```

### 7.3 Reading the result

**Section 2's identical 1.000 scores are the whole argument in one pair of numbers.** It would be tempting
to assume retrieval "somehow" handles staleness — it measurably does not, and cannot, without an explicit
signal.

**Section 4 is this lesson's most surprising result, and it's worth re-reading carefully.** The initial,
intuitive expectation is "position-based IDs change when chunking changes" — the measured reality is worse:
the *IDs stayed the same* while the *content changed underneath them*, which is a silent failure rather
than a visible one.

**Section 3's two citation strings, side by side, make an abstract principle immediately concrete** — one
is checkable, one is not, and the only difference is what metadata rode along with the text.

---

## 8. Common mistakes and troubleshooting

1. **Treating chunk metadata as optional or decorative.** §5.1 — every field this lesson defines resolves
   a specific, measured failure mode elsewhere in the lesson.
2. **Assuming retrieval scoring will naturally prefer a current document version over a stale one.** §5.2 —
   it has no basis to, absent explicit version/currency metadata to filter on.
3. **Generating citations without source, version, or timestamp information.** §5.3 — such a citation
   cannot be verified by a reader at all.
4. **Using position-based (index-based) chunk identifiers across re-chunking or re-indexing events.** §5.4
   — the same ID can silently refer to different content, a failure worse than the ID simply changing.
5. **Assuming a shared content-hash ID guarantees stability across any operation.** §5.4 — it guarantees
   only that shared IDs never mean different content; it does not guarantee IDs won't change when chunking
   itself changes.
6. **Re-ingesting updated documents without explicitly marking prior versions as superseded.** §6 — old and
   new content can otherwise coexist indefinitely, both appearing equally "current."

| Symptom | Likely cause | Fix |
|---|---|---|
| A RAG system gives different answers to the same question at different times, both citing "policy" | Stale and current chunks coexist with no currency metadata to filter on | Add and enforce an is_current field; filter to it before scoring/generation (§5.2, §6) |
| A citation cannot be verified or traced back to its source | The chunk record lacks provenance metadata (source, version, timestamp) | Attach and surface provenance metadata with every citation (§5.3) |
| An incremental-update or caching system fails to detect that content has changed | Chunk identifiers are position-based and silently point to different content after re-chunking | Switch to content-hash-based identifiers (§5.4) |
| Metadata filtering fails or returns unexpected results | The chunk schema lacks the specific field being filtered on | Design the schema to include every field filtering will need (§5.5) |

---

## 9. Security, privacy, reliability, cost

- **Reliability.** Attach version and currency metadata to every chunk, and filter to current chunks before
  scoring or generation — retrieval alone cannot distinguish a stale answer from a current one (§5.2, §6).
- **Reliability.** Attach provenance metadata (source, version, timestamp) to every chunk so citations can
  be verified, not merely asserted (§5.3).
- **Reliability.** Use content-hash-based, not position-based, chunk identifiers wherever re-chunking or
  re-indexing might occur — position-based IDs can silently point to different content (§5.4).
- **Privacy.** Metadata fields (department, source, tags) can themselves carry sensitive information —
  apply the same access controls to metadata as to the underlying text (a preview of M7-L15).

---

## 10. Exercises

### Exercise 1 — Beginner (~20 min)

1. In one sentence, why is a chunk's text alone not sufficient for a trustworthy RAG system?
2. Why did the stale and current PTO chunks score identically in §7.2?
3. What makes a citation verifiable, per §7.3?
4. Why is a position-based ID silently pointing to different content worse than an ID simply changing?
5. Why can a content-hash-based ID never have the same silent-mismatch problem?

### Exercise 2 — Intermediate (~40 min)

1. Run the lab. Confirm §7.2's identical scores and §7.4's silent-mismatch count on your own machine.
2. Design and add a third version of the PTO policy chunk, mark the second version as no longer current,
   and confirm filtering to is_current=True returns only the third.
3. Extend §7.1's chunk record schema with a field for "approved_by" and explain what real risk it would
   help mitigate.
4. Using §7.4's method, test whether the silent-mismatch problem also occurs when only OVERLAP (not chunk
   size) changes between two chunkings.
5. Using §7.5's method, add a second metadata dimension (e.g. document type) and filter on both department
   and document type simultaneously.

### Exercise 3 — Challenge (~50 min)

1. Implement a function that, given an old and a new corpus of chunks (both content-hash-identified),
   determines which chunks are new, which are unchanged, and which have been removed — the core mechanism
   M7-L16 will build on.
2. Design a versioning workflow (conceptually or in code) that automatically marks a document's prior
   chunks as not current when a new version is ingested, using content-hash comparison to detect the
   change.
3. Extend this lesson's citation function (§7.3) to detect and flag when a cited chunk's is_current field
   is False, producing an explicit "this may be outdated" warning.
4. Research (conceptually) how a real vector database or RAG framework represents chunk metadata, and
   compare its schema to this lesson's own.
5. Using this lesson's §6 worked example as a model, design an audit process that would catch contradictory
   "current" answers before an external audit does, specifying what to check and how often.

---

## 11. Quiz

*(Answers: [`answer-keys/module-07-answers.md`](../../answer-keys/module-07-answers.md#m7-l08).)*

**Q1.** Per §7.1, what does a chunk record include beyond its text content?

- A. Only the raw text of the chunk, nothing else.
- B. A randomly generated number with no relationship to the chunk's content or origin.
- C. A copy of the entire original source document, duplicated in full.
- D. Source URI, document ID, chunk index, version, currency flag, and ingestion timestamp, among other fields needed to trust, cite, and manage it.

**Q2.** Per §7.2, what did the measured cosine scores reveal about the stale (v1) and current (v2) PTO
policy chunks?

- A. The stale chunk always scored measurably lower than the current chunk.
- B. The two chunks scored identically, meaning nothing about the text or its score alone reveals which version is current.
- C. The retrieval system automatically excluded the stale chunk without any explicit filtering.
- D. Only the current chunk was ever indexed in the first place.

**Q3.** Per §7.2, how was the version ambiguity actually resolved?

- A. By filtering candidate chunks to only those marked is_current=True before scoring/generation, resolving the ambiguity structurally via metadata.
- B. By manually reading every retrieved chunk and guessing which one seemed more recent.
- C. By deleting the stale chunk's text so it could never be retrieved again.
- D. By always preferring whichever chunk happened to be indexed first.

**Q4.** Per §7.3, what is the practical difference between a citation with and without provenance
metadata?

- A. There is no practical difference; both citations are equally verifiable.
- B. A citation without provenance is always more trustworthy, since it is simpler.
- C. A citation with provenance (source, version, timestamp) can be verified against the live document; one without cannot be checked at all.
- D. Provenance metadata makes a citation less accurate, not more.

**Q5.** Per §7.4's measured result, what happened to position-based chunk IDs after the document was
re-chunked at a different size?

- A. All position-based IDs became completely different strings after re-chunking.
- B. The document became impossible to re-chunk at a different size at all.
- C. Position-based IDs were automatically converted to content-hash-based IDs.
- D. The same ID strings appeared before and after, but silently referred to different underlying text in every case.

**Q6.** Per §7.4, why is this specifically dangerous, more so than IDs simply changing?

- A. It is not actually more dangerous than IDs simply changing.
- B. A cache, diff tool, or incremental-update check keyed on the ID could conclude nothing changed when the content actually did, since the ID itself gives no signal of the mismatch.
- C. It causes the entire chunking process to fail with an error.
- D. It only affects documents shorter than 50 characters.

**Q7.** Per §7.4, why can a content-hash-based ID never have this same silent-mismatch problem?

- A. The ID is mathematically derived from the text itself, so the same ID appearing twice guarantees the text is identical both times.
- B. Content-hash-based IDs are assigned randomly and never repeat under any circumstances.
- C. Content-hash-based IDs are manually verified by a human before each use.
- D. Content-hash-based IDs always stay exactly the same regardless of any change to the text.

**Q8.** Per §7.4, did content-hash-based IDs stay stable across the re-chunking in this lab's specific
example?

- A. Yes, every single hash-based ID remained exactly the same after re-chunking.
- B. Hash-based IDs cannot be computed at all after a document is re-chunked.
- C. No — most hash IDs still changed, since re-chunking altered nearly every chunk's exact boundaries; the guarantee is only that a shared ID can never point to mismatched text, not that IDs won't change at all.
- D. Hash-based IDs are only valid for the first chunk of any document.

**Q9.** Per §7.5, what does this lesson's chunk-record schema provide that M6-L09's metadata filtering did
not by itself?

- A. A complete replacement for M6-L09's pre-filtering and post-filtering mechanics.
- B. A guarantee that filtering always returns exactly one result.
- C. A new vector similarity metric distinct from cosine similarity.
- D. The actual fields (department, version, currency, etc.) that filtering techniques like M6-L09's operate on, rather than new filtering mechanics themselves.

**Q10.** Which topic does this lesson explicitly leave to M7-L16?

- A. The definition of a content hash, which this lesson covers directly instead.
- B. The real versioning workflow — how "is_current" actually gets flipped when a document changes.
- C. Metadata filtering mechanics, which this lesson covers directly instead.
- D. Provenance-based citation construction, which this lesson covers directly instead.

**Q11.** Which topic does this lesson explicitly leave to M7-L15?

- A. Permission-aware filtering specifically for access control, distinct from the department-tagging shown in this lesson.
- B. Chunk identifier stability, which this lesson covers directly instead.
- C. Version-ambiguity resolution, which this lesson covers directly instead.
- D. The chunk-record schema itself, which this lesson covers directly instead.

**Q12.** What is the general lesson this lab demonstrates about chunk metadata?

- A. Chunk metadata is a decorative extra that has no real effect on system correctness.
- B. All chunks in any corpus should always share the identical metadata values.
- C. Metadata like version, currency, source, and stable identity is load-bearing infrastructure that resolves real ambiguities (staleness, unverifiable citations, silent identity mismatches), not decorative extra fields.
- D. Metadata should be discarded as soon as a chunk has been embedded and indexed.

**Q13.** *(Written, rubric-graded.)* In under 150 words: a colleague says "we don't need version metadata
— if we re-ingest a policy document, the old chunks will just get less relevant over time as the wording
changes." Based on this lesson, how would you respond?

---

## 12. Revision notes

- **A chunk record needs more than text**: source URI, document ID, version, currency, and ingestion
  timestamp are each load-bearing, not decorative, fields.
- **Retrieval scoring cannot distinguish a stale document version from a current one on its own** —
  measured directly: a stale and current PTO policy chunk scored identically (1.000) against the same
  query; filtering to `is_current=True` resolved the ambiguity structurally.
- **A citation is only verifiable if it carries provenance** — source, version, and timestamp are what let
  a reader actually check a citation against the live document.
- **Position-based chunk IDs can silently point to different content after re-chunking** — measured
  directly: all 3 position-based IDs stayed the same string while their underlying text changed completely.
- **Content-hash-based IDs cannot have this silent-mismatch failure, by mathematical construction** — a
  shared hash ID guarantees identical text, though hash IDs still change when chunk boundaries move.
- **Metadata filtering (M6-L09) needs a schema to filter on** — this lesson supplies the fields; M6-L09
  supplied the mechanics.

---

## 13. Completion checklist

- [ ] I can design a chunk record schema carrying source, version, currency, and provenance.
- [ ] I can demonstrate and explain why retrieval scoring cannot distinguish stale from current content
      without explicit metadata.
- [ ] I can explain why provenance metadata is what makes a citation verifiable.
- [ ] I can demonstrate why position-based chunk IDs can silently mismatch content, and why
      content-hash-based IDs cannot.
- [ ] I can apply metadata filtering using a concrete schema, building on M6-L09's mechanics.
- [ ] I enforce currency metadata on re-ingestion so stale and current content don't coexist ambiguously.
- [ ] I scored 10/13 on the quiz.

---

## 14. References

- Python documentation, `dataclasses` — used for this lesson's chunk record. <https://docs.python.org/3/library/dataclasses.html> `[UNVERIFIED]`
- W3C, *PROV-O: The PROV Ontology* (a general provenance modeling standard, for further reading). `[UNVERIFIED]`

---

## 15. Next lesson

→ M7-L09 — Query Rewriting, Expansion and Decomposition

You now have well-formed, trustworthy chunks with the metadata to manage them. Next: the query side of the
pipeline — rewriting, expanding, and decomposing a user's question before it ever reaches retrieval, to
close gaps M7-L01 already showed retrieval alone cannot close.
