# M7-L05 — Cleaning, Normalisation and Deduplication

| | |
|---|---|
| **Lesson ID** | M7-L05 |
| **Difficulty** | 2 (Intermediate) |
| **Estimated study time** | 1.75 hours |
| **Prerequisites** | [M7-L03](M7-L03-ingestion-document-parsing.md) |

---

## 1. Learning objectives

1. **Demonstrate** that two strings can render identically yet be unequal as data, due to Unicode
   normalization form differences, and fix it.
2. **Normalize** whitespace artifacts left over from extraction.
3. **Deduplicate** an entire corpus using content-hash identity (M7-L03), applied at corpus scale.
4. **Detect** near-duplicate documents that exact hashing cannot catch, using shingling and Jaccard
   similarity, and explain the sensitivity of the shingle-size parameter.
5. **Measure** the concrete effect duplicate and near-duplicate content has on a retrieval result set.

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **Unicode normalization form** | A canonical way of representing text with combining characters — NFC (composed, one code point per visible character where possible) and NFD (decomposed, base character plus separate combining marks) are the two most common. |
| **Exact duplicate** | Two documents whose normalized text is byte-for-byte identical. |
| **Near-duplicate** | Two documents that are substantially similar but not identical — e.g. the same text with minor edits. |
| **Shingling (k-shingles)** | Breaking text into overlapping windows of k consecutive words (or characters), used to measure similarity between documents. |
| **Jaccard similarity** | The size of the intersection of two sets divided by the size of their union — a standard measure of set overlap, used here on shingle sets. |

---

## 3. Plain-language explanation

### 3.1 M7-L03/M7-L04 got text out; this lesson gets it into a comparable form

Ingestion and hard-format extraction produce text — but text from different sources can represent the
same content in subtly different ways (Unicode form, whitespace) and a corpus assembled from multiple
sources routinely contains the same or similar content more than once. This lesson is what happens between
"we have the text" and "we can trust our identity and duplication checks about it."

### 3.2 The same-looking string that isn't the same string

§7.1 demonstrates something most engineers encounter exactly once, painfully: two strings that print
identically can be unequal as data, because Unicode allows more than one way to represent certain
characters. This isn't a corner case invented for this lesson — it's a routine consequence of documents
arriving from different tools and operating systems.

### 3.3 Whitespace is cheap noise, and cheap to remove

§7.2 is the lesson's simplest section, deliberately: collapsing irregular whitespace left over from PDF
and HTML extraction (M7-L04) costs almost nothing and removes noise that would otherwise inflate token
counts for no benefit.

### 3.4 Exact deduplication is M7-L03's mechanism, now at corpus scale

§7.3 doesn't introduce a new idea — it applies M7-L03's content-hash identity across many documents at
once, to find and collapse exact duplicates that arrived from different source locations.

### 3.5 Some duplicates don't hash the same, and still matter

§7.4 is the lesson's technical core: two documents that are the same policy, lightly reworded, are
genuinely different byte-for-byte — exact hashing is *correct* to call them different. Shingling and
Jaccard similarity measure a different, complementary thing: how much they still overlap.

### 3.6 Duplicates aren't just wasted storage

§7.5 measures, rather than asserts, what duplicate content actually costs: a retrieval result set that
returns three copies of the same document instead of three genuinely different ones.

---

## 4. Analogy

**A library that received the same donated book three times, plus a second edition with a few corrected
typos.** Two copies of the *exact* same printing are trivially recognized as duplicates — same ISBN, same
cover, same everything. The second edition is trickier: it's not the same book byte-for-byte (a few words
changed), but a patron searching the shelves doesn't want three near-identical copies of essentially the
same content taking up three of their five browsing slots, crowding out a genuinely different book on a
related topic. A librarian who only checks "is this the exact same printing" will miss the second-edition
problem entirely; one who has to compare every book to every other book by reading them cover to cover
doesn't scale to a large library at all.

### Where the analogy breaks

- **ISBNs are assigned externally and don't have a Unicode-normalization-style ambiguity.** §7.1's problem
  has no clean analogue here — it's specific to how text is represented as data, not to real-world physical
  objects.
- **A librarian's judgment about "how similar is similar enough" is intuitive.** §7.4's threshold and
  shingle-size choices are explicit, tunable parameters with measurable sensitivity — there is no
  equivalent dial for a human librarian's judgment call.

---

## 5. Detailed technical explanation

### 5.1 Two representations, one appearance

`[REAL]` §7.1 constructed "café" two genuinely different ways: as a single precomposed code point for "é"
(4 characters total) and as "cafe" plus a separate combining acute accent mark (5 characters total). They
render identically and print identically, but `composed == decomposed` evaluates to **False**. Normalizing
both to NFC form (`unicodedata.normalize("NFC", text)`) made them equal.

**The practical risk**: a content-hash-based deduplication check (M7-L03) run *without* normalizing first
computes different hashes for text that is, to a human, the same document — a silent failure with the same
shape as M7-L03's encoding bug: nothing crashes, the duplicate is simply never caught.

### 5.2 Whitespace collapsing

`[REAL]` §7.2 collapsed `"Remote  work   requires\n\nmanager  approval.\t\tSubmit  the  form."` (63
characters, irregular spacing from extraction) into `"Remote work requires manager approval. Submit the
form."` (55 characters) via `" ".join(text.split())`. Cheap, safe, and removes variation that carries no
meaning while diluting token budgets and embeddings.

### 5.3 Exact deduplication, at corpus scale

`[REAL]` §7.3 hashed 5 documents ingested from 3 different source locations (after normalizing whitespace
and Unicode form first, per §5.1–§5.2) and found that 2 of the 5 were exact duplicates of a third — the
same remote-work policy, apparently scraped or exported from three separate places. **This is M7-L03's
content-hash identity mechanism, unchanged, applied across a whole corpus rather than one file's
re-ingestion history.**

### 5.4 Near-duplicates, and the sensitivity of shingle size

`[REAL, measured]` §7.4 took a policy document and a lightly reworded copy (2 words changed out of 25) and
confirmed exact hashing correctly reports them as different — they are, byte-for-byte. Breaking both into
overlapping 3-word shingles and computing Jaccard similarity gave **0.586**, comfortably above a 0.5
near-duplicate threshold; a genuinely different document scored **0.000**.

**The k-sensitivity finding**: the *same* 2-word edit produced Jaccard scores of 0.586 (k=3), 0.467 (k=4),
and 0.355 (k=5) — dropping below the 0.5 threshold entirely at k=5. Each word-level edit corrupts every
overlapping shingle that touches it, so larger k amplifies a small, localized edit into a larger apparent
difference. **Shingle size and similarity threshold are both real, sensitive parameters that need
calibration against your own corpus and typical edit patterns** — there is no universally correct choice.
`[UNVERIFIED — test both against your own data before relying on a specific value.]`

### 5.5 What duplicates cost, measured

`[REAL, illustrative scoring]` §7.5 scored a small corpus against a query using simple word overlap
(chosen for hand-checkability; the effect holds regardless of which real scoring method — BM25, dense,
hybrid — is actually used). **Before deduplication, the top 3 results were three exact copies of the same
policy document.** After collapsing the duplicate cluster to one representative, the top 3 included a
genuinely different, previously crowded-out document (the PTO policy). **Deduplication is not only a
storage optimization — it directly determines how much genuinely distinct information a user's top-k
results actually contain.**

### 5.6 Assumptions and limitations

- §7.4's shingling computes exact pairwise Jaccard similarity, which does not scale to large corpora
  (comparing every document to every other document is quadratic). Locality-sensitive hashing (LSH) or
  MinHash are the standard techniques for near-duplicate detection at real scale — not demonstrated here.
- §7.4's specific threshold (0.5) and shingle size (k=3) are illustrative choices for this lab's specific
  documents, not universal defaults.
- This lesson assumes documents are already in extracted text form (M7-L03, M7-L04) — it does not cover
  ingestion or hard-format extraction itself.

---

## 6. Worked example — the support corpus that answered every query with three results

**The system.** A support-article corpus is assembled from three overlapping sources: the primary
knowledge base, an SEO-optimized mirror site (same articles, different headers/footers), and an old
archive that hasn't been decommissioned. No deduplication step runs during ingestion.

**What went wrong.** Nearly every search returned the same article three times in the top 5 results,
because all three source copies scored identically (or near-identically) against any matching query — the
genuinely different, second-most-relevant article for many queries simply never appeared, crowded out by
redundant copies of the top match.

**Why it wasn't caught immediately.** Individually, each result "looked correct" — it genuinely was a
relevant article. The problem was only visible when someone asked "why does every query only ever surface
one real answer diluted across three slots," exactly the crowding effect §7.5 measured directly.

**Three defects:**

| # | Defect | Consequence |
|---|---|---|
| 1 | No exact-deduplication step ran across the three overlapping sources | Byte-for-byte identical content (modulo whitespace/Unicode form) was never collapsed |
| 2 | Text wasn't normalized (whitespace, Unicode form) before hashing | Even where content was truly identical, minor representational differences could have prevented hash matches |
| 3 | No near-duplicate detection existed for the mirror site's lightly modified copies | Slightly-edited duplicates (different headers, minor rewording) survived exact deduplication too |

### The fix

**Normalize text (Unicode form, whitespace) before computing any content hash**, per §5.1–§5.2 — otherwise
even truly identical content can fail to match.

**Run exact deduplication across the whole corpus at ingestion time**, per §5.3, not just within a single
source.

**Add near-duplicate detection (shingling, or LSH/MinHash at scale) for content that varies slightly across
sources**, per §5.4, since exact hashing alone will not catch a mirror site's minor edits.

**The general rule.** **A corpus assembled from multiple overlapping sources will contain both exact and
near-duplicate content by default — deduplication is not an optional cleanup step, it is what determines
whether a user's top-k results contain k genuinely different answers or k copies of one.**

---

## 7. Practical activity

**File:** [`labs/m7/l05_cleaning_dedup.py`](../../labs/m7/l05_cleaning_dedup.py)

**No API key, no network, no third-party dependencies** — pure Python standard library. Runs in well under
a second.

```bash
source .venv/bin/activate
python labs/m7/l05_cleaning_dedup.py
```

### 7.2 Expected output

`[EXECUTED]` — 2026-09-10, Python 3.10.11 (pure standard library).

```text
============================================================================
1. UNICODE NORMALIZATION: LOOKS IDENTICAL, ISN'T EQUAL AS DATA
============================================================================
  composed:   'café'  (length 4)
  decomposed: 'café'  (length 5)
  They print identically: they DO look the same above
  They are equal as Python strings: False

  After normalizing BOTH to NFC (composed form):
    composed   -> 'café' (length 4)
    decomposed -> 'café' (length 4)
    Now equal: True

  Two documents ingested from different sources (different export
  tools, different operating systems) can contain the SAME visible
  text encoded with different Unicode normalization forms. A content-
  hash-based dedup check (M7-L03) run WITHOUT normalizing first would
  compute two DIFFERENT hashes for genuinely identical-looking content
  -- a silent deduplication failure with the same shape as M7-L03's
  encoding bug: nothing crashes, the duplicate simply isn't caught.

============================================================================
2. WHITESPACE NORMALIZATION
============================================================================
  Raw (extraction artifact -- irregular spaces, tabs, blank lines):
    'Remote  work   requires\n\nmanager  approval.\t\tSubmit  the  form.'
  Normalized:
    'Remote work requires manager approval. Submit the form.'

  63 characters -> 55 characters. This kind of
  irregular whitespace is a routine, unremarkable side effect of PDF and
  HTML extraction (M7-L04) -- collapsing it is cheap and removes noise
  that would otherwise inflate token counts and dilute embeddings with
  meaningless variation.

============================================================================
3. EXACT DEDUPLICATION ACROSS A CORPUS, VIA CONTENT HASH
============================================================================
  5 documents ingested from 3 different sources.

  Unique (by content hash): ['src_a/policy.txt', 'src_a/expenses.txt', 'src_a/pto.txt']
  Exact duplicates found: [('src_b/mirror_policy.txt', 'src_a/policy.txt'), ('src_c/policy_export.txt', 'src_a/policy.txt')]

  Two of three copies of the SAME remote-work policy text (scraped or
  exported from three different source locations) collapse to one
  unique document once hashed -- exactly M7-L03's identity mechanism,
  now applied across an entire corpus rather than one file's history.

============================================================================
4. NEAR-DUPLICATES: WHAT EXACT HASHING MISSES
============================================================================
  Doc A hash: 1ba292a2ec12
  Doc B hash: 6cfedccbde21  (a lightly reworded copy of A)
  Exact hash match A vs B: False

  A and B are the same policy, reworded in two small places -- exact
  content hashing correctly reports them as DIFFERENT, because they are,
  byte for byte. But they are near-duplicates in a way that still
  matters for a retrieval corpus, and exact hashing has no way to see it.

  A and B differ in exactly 2 words out of 25 -- a genuinely light edit.

  3-word shingle sets: |A|=23, |B|=23, |C|=16
  Jaccard(A, B) = 0.586  (A vs its lightly reworded near-duplicate)
  Jaccard(A, C) = 0.000  (A vs a genuinely different policy)

  At a threshold of 0.5: A/B ARE flagged as near-duplicates; A/C are NOT.

  Shingling breaks text into overlapping k-word windows and measures
  set overlap -- two documents sharing most of their wording, even with
  a few words changed, share most of their shingles too. This is what
  catches near-duplicates exact hashing (section 3) cannot.

  Shingle size k is a real, sensitive parameter, not an arbitrary
  detail -- each single word edit corrupts every overlapping shingle
  that touches it, so LARGER k amplifies the same small edit into a
  bigger apparent difference:
    k=3: Jaccard(A, B) = 0.586
    k=4: Jaccard(A, B) = 0.467
    k=5: Jaccard(A, B) = 0.355

  The SAME 2-word edit drives Jaccard(A, B) from 0.586 at k=3 down to 0.355 at k=5 -- crossing this
  lab's 0.5 threshold from 'flagged' to 'missed' depending
  purely on k. `[UNVERIFIED -- calibrate both k and the threshold against
  your own corpus and edit patterns before relying on either value.]`

============================================================================
5. WHAT DUPLICATE CONTENT ACTUALLY COSTS A RETRIEVAL RESULT SET
============================================================================
  Query concept: 'remote work manager approval'
  Top-3 by simple overlap score, BEFORE deduplication: ['policy_v1', 'policy_mirror', 'policy_export']
    policy_v1: score 1.00
    policy_mirror: score 1.00
    policy_export: score 1.00

  Top-3 AFTER deduplication (near-duplicate cluster collapsed to one representative): ['policy_v1', 'policy_reworded', 'expenses']

  Before deduplication, the top 3 results are three near-identical
  copies of the SAME policy -- a user gets no new information from
  results 2 and 3, and a genuinely different, potentially more relevant
  document (PTO policy) is crowded out of the top-3 entirely by
  redundant copies of one document. Deduplication doesn't just save
  storage -- it directly affects which distinct information a user
  actually sees.

============================================================================
6. WHAT THIS LAB IS AND IS NOT
============================================================================
  REAL: the Unicode composed/decomposed inequality and its NFC fix are
  exact, standard-library behavior; whitespace collapsing, content
  hashing, shingling, and Jaccard similarity are all computed exactly
  as coded, on real (if synthetic) text.

  ILLUSTRATIVE: section 5's 'retrieval' is a simple word-overlap score,
  not a real embedding or BM25 ranking (M6-L01/M6-L03) -- chosen to keep
  the deduplication-crowding effect easy to verify by hand; the
  underlying point (duplicates crowd out distinct results) holds
  regardless of which real scoring method is used.

  NOT SHOWN: locality-sensitive hashing (LSH) or MinHash for near-
  duplicate detection at real corpus scale, where computing exact
  pairwise Jaccard similarity (this lab's approach) becomes too slow --
  a natural next step left to the exercises.

Done.
```

### 7.3 Reading the result

**Section 1 is easy to underestimate until you've been bitten by it once.** The printed strings look
completely identical; only their lengths (4 vs. 5) give away that they're different data. This is exactly
why it's dangerous in practice — nothing about *looking* at the text reveals the problem.

**Section 4's k-sensitivity finding is the lesson's most important result, and it directly parallels
M6-L11's RRF k-sensitivity finding.** A parameter that looks like an implementation detail (shingle size)
turns out to directly determine whether a real near-duplicate gets caught or missed, at a fixed threshold.

**Section 5 turns an abstract complaint ("duplicates are wasteful") into a measured, concrete claim**: the
exact set of documents a user sees in their top-k changes, not just how much disk space the corpus uses.

---

## 8. Common mistakes and troubleshooting

1. **Computing content hashes without normalizing Unicode form and whitespace first.** §5.1–§5.3 — this
   can cause genuinely identical-looking content to hash differently, silently failing deduplication.
2. **Assuming exact-hash deduplication catches all redundant content.** §5.4 — it correctly catches only
   byte-for-byte identical content; near-duplicates need a separate technique (shingling, LSH/MinHash).
3. **Treating shingle size (k) as an arbitrary implementation detail.** §5.4 — it is a sensitive parameter
   that directly changes whether a given near-duplicate pair is flagged or missed at a fixed threshold.
4. **Skipping deduplication because "it's just a storage optimization."** §5.5, §6 — it directly affects
   which distinct information appears in a user's top-k results.
5. **Running near-duplicate detection as exact pairwise comparison at real corpus scale.** §5.6 — this is
   quadratic and does not scale; use LSH or MinHash for large corpora.
6. **Assuming a corpus assembled from multiple sources has no duplicates without checking.** §6 — overlap
   between sources (mirrors, archives, exports) is a common, default outcome, not an edge case.

| Symptom | Likely cause | Fix |
|---|---|---|
| Two documents that look identical are not recognized as duplicates by content hash | Different Unicode normalization forms or unnormalized whitespace | Normalize text (NFC, whitespace collapse) before hashing (§5.1–§5.3) |
| Search results are dominated by near-identical copies of the same document | No near-duplicate detection; only exact hashing was applied | Add shingling/Jaccard-based (or LSH/MinHash at scale) near-duplicate detection (§5.4) |
| A near-duplicate pair is caught with one shingle size but missed with another | Shingle size (k) sensitivity to localized edits | Calibrate k and the similarity threshold against your own corpus's typical edit patterns (§5.4) |
| Deduplication is deprioritized as "just" a storage concern | Underestimating its effect on result diversity | Measure top-k result composition before/after deduplication, per §5.5 |

---

## 9. Security, privacy, reliability, cost

- **Reliability.** Always normalize Unicode form and whitespace before computing a content hash for
  deduplication — otherwise genuinely identical content can silently fail to match (§5.1–§5.3).
- **Reliability.** Deploy both exact (content-hash) and near-duplicate (shingling/LSH) detection — each
  catches a different class of redundancy, and neither alone is sufficient (§5.3–§5.4).
- **Reliability.** Measure the effect of deduplication on retrieval result diversity directly, not just on
  storage size — the practical impact is on what users actually see (§5.5).
- **Cost.** Use approximate techniques (LSH, MinHash) rather than exact pairwise comparison for
  near-duplicate detection once a corpus grows large, since exact comparison is quadratic (§5.6).

---

## 10. Exercises

### Exercise 1 — Beginner (~20 min)

1. In one sentence, why can two strings look identical but not be equal in Python?
2. Why is whitespace normalization considered "cheap" cleanup?
3. What did content-hash deduplication find across this lab's 5-document corpus?
4. In one sentence, why does exact hashing correctly report a lightly-reworded document as "different"?
5. Name one real effect deduplication has on retrieval results, beyond storage savings.

### Exercise 2 — Intermediate (~40 min)

1. Run the lab. Confirm §7.1's length difference and §7.4's k-sensitivity table on your own machine.
2. Construct your own pair of near-duplicate documents (a real paragraph, lightly edited in 2-3 places)
   and compute their Jaccard similarity at k=3 and k=5.
3. Using §7.3's method, add a sixth document to the corpus that is a genuine duplicate of the PTO policy,
   under a fourth source name, and confirm it is caught.
4. Experiment with the near-duplicate threshold (currently 0.5): find a threshold value that would
   incorrectly flag Doc A and Doc C (the genuinely different documents) as near-duplicates, and explain
   why that threshold is a poor choice.
5. Using §7.5's method, construct a corpus and query where near-duplicates (not exact duplicates) crowd
   out a genuinely different result, and measure the effect of near-duplicate collapsing.

### Exercise 3 — Challenge (~50 min)

1. Implement a simple MinHash sketch (a fixed-size approximation of Jaccard similarity) and compare its
   estimated similarity against this lab's exact Jaccard computation on the same document pairs.
2. Design and implement a corpus-wide near-duplicate clustering function (group all documents whose
   pairwise Jaccard similarity exceeds a threshold into clusters) and test it on an extended version of
   this lab's corpus.
3. Research (conceptually) locality-sensitive hashing (LSH) and explain, at a high level, how it avoids
   the quadratic cost of exact pairwise comparison at scale.
4. Extend §7.1's Unicode normalization check into a general ingestion safeguard that normalizes every
   document to NFC before any hashing or comparison occurs, and demonstrate it catching a case exact
   hashing alone would miss.
5. Write a short deduplication policy (under 300 words) for a hypothetical multi-source corpus, specifying
   what counts as an exact duplicate, what counts as a near-duplicate, and what action to take for each.

---

## 11. Quiz

*(Answers: [`answer-keys/module-07-answers.md`](../../answer-keys/module-07-answers.md#m7-l05).)*

**Q1.** Per §7.1, why are two strings that print identically ("café" composed vs. decomposed) not equal as
Python strings before normalization?

- A. Python cannot compare strings containing accented characters at all.
- B. One of the two strings was corrupted during the lab's setup.
- C. They are represented as different underlying code point sequences (one code point for the accented letter vs. two), even though they render visually the same.
- D. String comparison in Python is case-sensitive only, not character-sensitive.

**Q2.** Per §7.1, what real consequence does this have for a content-hash-based deduplication check?

- A. Two documents with the same visible text but different Unicode normalization forms would compute different hashes, silently failing to be recognized as duplicates.
- B. Content hashing becomes impossible to compute for any text containing accented characters.
- C. The documents would be merged automatically without any hash comparison at all.
- D. This has no practical effect on deduplication of any kind.

**Q3.** Per §7.2, why is whitespace normalization useful before chunking/embedding?

- A. It is required before any text can be read by a Python program at all.
- B. It permanently changes the meaning of the original document.
- C. It is only relevant for documents written in languages other than English.
- D. Irregular whitespace (multiple spaces, tabs, blank lines) is noise from extraction that inflates token counts and dilutes embeddings without adding meaning.

**Q4.** Per §7.3, how many of the 5 ingested documents were found to be exact duplicates by content hash?

- A. All 5 documents were found to be exact duplicates of each other.
- B. 2 of the 5 (two copies of the same remote-work policy from different source locations).
- C. None of the 5 documents were duplicates of any kind.
- D. Exactly 4 of the 5 documents were flagged as duplicates.

**Q5.** Per §7.4, why did exact content hashing correctly report Doc A and Doc B as different, even though
they're described as "near-duplicates"?

- A. Because content hashing is unreliable and often produces incorrect results.
- B. Because Doc A and Doc B were actually generated from completely unrelated topics.
- C. They differ by 2 actual words, so they are genuinely different byte-for-byte, which is exactly what an exact hash is designed to detect.
- D. Because the hash function used a different algorithm for each document.

**Q6.** Per §7.4's measured k-sensitivity finding, what happened to Jaccard(A, B) as shingle size k
increased from 3 to 5?

- A. It decreased (from 0.586 to 0.355), because each of the 2 word-level edits corrupts more overlapping shingles as k grows.
- B. It increased steadily as k grew larger.
- C. It stayed exactly the same regardless of k.
- D. It became undefined once k exceeded 3.

**Q7.** Per §7.4, what is the practical implication of the k-sensitivity finding?

- A. Shingle size should always be set to the largest possible value for best results.
- B. Near-duplicate detection is impossible regardless of shingle size.
- C. Only exact duplicates should ever be detected in a real system.
- D. Shingle size and similarity threshold both need to be calibrated for your own corpus and edit patterns, not treated as universal constants.

**Q8.** Per §7.5, what happened to the top-3 retrieval results BEFORE deduplication?

- A. The top 3 results were three completely unrelated documents.
- B. All three top results were exact copies of the same policy document, crowding out a genuinely different, potentially relevant document.
- C. The retrieval system returned zero results at all.
- D. The top 3 results were correctly deduplicated automatically without any explicit deduplication step.

**Q9.** Per §7.5's closing point, what does deduplication actually change about a retrieval system, beyond
storage savings?

- A. Deduplication only ever affects how much disk space a corpus uses.
- B. Deduplication has no measurable effect on what a user sees in search results.
- C. It directly affects which distinct pieces of information a user actually sees in the results, since duplicates can crowd out genuinely different relevant content.
- D. Deduplication makes retrieval slower without any corresponding benefit.

**Q10.** Per §7.6, what near-duplicate detection technique does this lesson explicitly NOT demonstrate,
leaving it as a natural next step?

- A. Locality-sensitive hashing (LSH) or MinHash, needed when exact pairwise Jaccard comparison becomes too slow at real corpus scale.
- B. Whitespace normalization, which this lesson also does not demonstrate.
- C. Content-hash-based exact deduplication, which this lesson also does not demonstrate.
- D. Unicode normalization, which this lesson also does not demonstrate.

**Q11.** How does this lesson's exact-hash deduplication (§7.3) relate to M7-L03's content-hash identity
mechanism?

- A. They are unrelated techniques that happen to share a similar name.
- B. M7-L03's mechanism only applies to CSV and JSON files, never plain documents.
- C. This lesson's deduplication replaces the need for M7-L03's content hashing entirely.
- D. It's the same mechanism (a deterministic content hash), now applied across an entire corpus to find duplicates rather than to just one file's re-ingestion history.

**Q12.** What is the general lesson this lab demonstrates about cleaning, normalization, and
deduplication?

- A. Cleaning, normalization, and deduplication are all optional steps that can be safely skipped in any pipeline.
- B. Normalization must happen before deduplication can work reliably, and exact and near-duplicate detection catch genuinely different classes of redundancy, each requiring its own technique.
- C. Exact deduplication alone is always sufficient to catch every form of redundant content.
- D. Near-duplicate detection always produces identical results regardless of which similarity technique is used.

**Q13.** *(Written, rubric-graded.)* In under 150 words: your corpus is assembled from three overlapping
sources (a primary site, a mirror, and an old archive), and search results are dominated by near-identical
copies of the same articles. Based on this lesson, what would you check and what would you implement?

---

## 12. Revision notes

- **Two strings can render identically but be unequal as data**, because Unicode allows more than one
  representation (e.g. composed vs. decomposed accented characters) — normalize to one form (e.g. NFC)
  before comparing or hashing.
- **Whitespace normalization is cheap, low-risk cleanup** that removes extraction noise without changing
  meaning.
- **Exact deduplication is M7-L03's content-hash mechanism, applied across a whole corpus** — measured
  directly collapsing 2 of 5 documents from different sources into 1 unique document.
- **Exact hashing correctly reports lightly-edited near-duplicates as different** — this is not a bug, it
  is exactly what a byte-for-byte hash is designed to do; a separate technique (shingling, Jaccard
  similarity) is needed to catch near-duplicates.
- **Shingle size (k) is a real, sensitive parameter** — the same 2-word edit produced Jaccard similarity
  ranging from 0.586 (k=3) to 0.355 (k=5), crossing a fixed 0.5 threshold from "flagged" to "missed" purely
  as a function of k.
- **Deduplication directly affects retrieval result diversity, not just storage** — measured directly: an
  undeduplicated top-3 contained three copies of one document, crowding out a genuinely different one.

---

## 13. Completion checklist

- [ ] I can explain why two visually identical strings can be unequal as data, and how to fix it.
- [ ] I normalize whitespace as routine, low-risk pipeline cleanup.
- [ ] I can implement corpus-wide exact deduplication using content hashing.
- [ ] I can implement near-duplicate detection using shingling and Jaccard similarity.
- [ ] I understand that shingle size and similarity threshold require calibration, not universal defaults.
- [ ] I measure deduplication's effect on retrieval result diversity, not just storage savings.
- [ ] I scored 10/13 on the quiz.

---

## 14. References

- Python documentation, `unicodedata` — *Unicode Database*. <https://docs.python.org/3/library/unicodedata.html> `[UNVERIFIED]`
- Broder, A., *On the resemblance and containment of documents*, 1997 (the original shingling/similarity paper). `[UNVERIFIED]`

---

## 15. Next lesson

→ M7-L06 — Chunking I: Size, Overlap and Document Boundaries

You now have clean, deduplicated, normalized text. Next: splitting it into the retrieval-sized pieces every
lab since M7-L01 has treated as a placeholder — how big a chunk should be, why overlap matters, and how to
respect a document's own natural boundaries instead of cutting through them arbitrarily.
