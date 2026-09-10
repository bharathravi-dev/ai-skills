# M6-L04 — Dense vs Sparse Retrieval

| | |
|---|---|
| **Lesson ID** | M6-L04 |
| **Difficulty** | 2 (Intermediate) |
| **Estimated study time** | 1.5 hours |
| **Prerequisites** | [M6-L03](M6-L03-bm25.md), [M6-L02](M6-L02-embedding-dimensions.md) |

---

## 1. Learning objectives

1. **Define** sparse and dense vectors precisely, by dimensionality and by how their values are
   determined — not merely as "keyword search" versus "AI search."
2. **Compute** cosine similarity over sparse (vocabulary-dimensioned) vectors and show it is the same
   mechanism M6-L02 used for dense embeddings.
3. **Demonstrate** that a sparse match can be explained dimension by dimension, while a dense match
   cannot.
4. **Compare** sparse cosine similarity against BM25 on the same corpus, and explain why they can
   disagree despite both being "sparse."
5. **State** the practical trade-off between dense and sparse retrieval, as the basis for combining them
   in M6-L11.

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **Sparse vector** | A vector with one dimension per vocabulary term, mostly zero for any given document. |
| **Dense vector** | A vector with far fewer dimensions, almost none zero, each a learned or hand-abstracted composite. |
| **Sparse retrieval** | Retrieval based on sparse (vocabulary-dimensioned) vectors — raw term counts, TF-IDF, or BM25. |
| **Dense retrieval** | Retrieval based on dense embedding vectors and cosine or dot-product similarity. |
| **Interpretability (retrieval)** | The ability to explain why a specific document matched a query, dimension by dimension. |
| **Weighting scheme** | The rule determining a sparse vector's dimension values — raw count, IDF-weighted, saturated, etc. |

---

## 3. Plain-language explanation

### 3.1 "Keyword vs AI" is the wrong distinction

M6-L01 through M6-L03 built two things that look completely different: cosine similarity over embeddings,
and BM25 over word counts. It is tempting to describe the difference as "keyword search versus AI
search." **That framing hides the actual distinction.** Both are vector similarity computations. What
differs is the **shape** of the vector and **how its values were decided**.

### 3.2 Sparse means "one dimension per word, mostly zero"

A **sparse vector** has one dimension for every word in the corpus's vocabulary — potentially tens of
thousands of dimensions — and almost all of them are zero for any single, short document. A **dense
vector** (M4-L04, M6-L02) has far fewer dimensions, learned by a model, and almost none of them are zero.
§7.1 builds real sparse vectors and computes real cosine similarity over them — the exact same formula
M6-L02 used for dense vectors, just applied to a very different shape of input.

### 3.3 Sparse vectors can be explained. Dense vectors cannot.

Every non-zero dimension in a sparse vector has a name: it is a specific word. When two sparse vectors
are similar, you can point at exactly which words they share. A dense vector's dimensions have no such
names — even in a small, hand-built toy model where a human chose the axes, a search system has nothing
meaningful to report back about "axis 0." §7.2 makes this concrete on both sides of the same comparison.

### 3.4 "Sparse" is a family, not one algorithm

BM25 (M6-L03) and raw term-count cosine similarity are **both** sparse retrieval — both build a
vocabulary-dimensioned vector and compute similarity over it. They can still rank the same corpus
**differently**, because they weight each dimension differently. §7.3 shows this directly: two "sparse"
methods disagreeing on the same query.

---

## 4. Analogy

**A fingerprint database versus a facial-recognition system.** A fingerprint match is explainable in the
most literal sense: an examiner can point at specific, named ridge points that correspond between two
prints — every element of the match has a label. A facial-recognition match is a similarity score between
two learned feature vectors; the system can report *how confident* it is, but there is no "ridge point 7"
to point to — the features a trained model uses to compare faces are not human-named categories at all.

Both are legitimate, useful matching systems, built on the same underlying idea (compare two
representations, produce a similarity score). They differ in whether the representation's parts have
names a person can inspect.

### Where the analogy breaks

- **A fingerprint's named ridge points are fixed by anatomy.** A sparse vector's "named dimensions" are
  fixed by whatever vocabulary the corpus happens to contain — a word never seen in training the corpus
  has no dimension at all (M6-L01's out-of-vocabulary case).
- **Facial recognition's features, while unnamed, are at least stable per system.** Two different dense
  embedding models can disagree about which features matter at all (M6-L02's model-compatibility problem)
  — there is no universal "facial feature space" the way there sort of is for fingerprints.
- **A forensic examiner is a genuinely independent check on a fingerprint match.** Nothing plays that
  role for a dense similarity score by default — its interpretability gap is structural, not a matter of
  needing a better examiner.

---

## 5. Detailed technical explanation

### 5.1 Sparse vectors, built and scored for real

`[REAL]` §7.1 built count vectors over the M6-L03 corpus's 21-word vocabulary and scored them against the
query `["refund", "damaged"]` by cosine similarity:

| Doc | Non-zero dimensions | Cosine similarity |
|---|---|---|
| D1 | `{refund:1, request:1, for:1, damaged:1, item:1}` | **0.6325** |
| D5 | `{refund:4, please:1, help:1, me:1, get:1, my:1}` | 0.6172 |
| D4 | `{how:1, do:1, I:1, track:1, my:1, order:1}` | **0.0000** |

**This is a complete, working retrieval method** — no model, no training, just counting and cosine
similarity, the identical mechanism M6-L02 applied to dense embeddings. The query vector itself has
non-zero values in only 2 of 21 dimensions; every other word in the vocabulary is implicitly zero — that
overwhelming zero-fraction is exactly what "sparse" names.

### 5.2 What you can and cannot explain

`[REAL]` §7.2 asked "why did D1 win?" of both a sparse and a dense comparison:

**Sparse (fully explainable):**
```
shared vocabulary words: ['damaged', 'refund']
  'damaged': query has 1, D1 has 1
  'refund': query has 1, D1 has 1
```

**Dense (not explainable the same way), using M6-L02's hand-built model:**
```
cosine('refund', 'invoice') = 0.9975
dimension-by-dimension: axis0=3.0*2.8, axis1=0.0*0.2, ...
```

**"Axis 0" has no name to report**, even in this tiny toy example where a human deliberately chose what
each axis would mean. A real, trained embedding model's dimensions carry no human-assigned meaning at
all. **You can see that two dense vectors are close. You generally cannot see why, term by term, the way
you just did for the sparse case.**

### 5.3 Two sparse methods can still disagree

`[REAL]` §7.3 ran sparse cosine and BM25 side by side on the same corpus and query:

| Doc | Sparse cosine | BM25 |
|---|---|---|
| D1 | 0.6325 | 1.5494 |
| D5 | 0.6172 | 0.8971 |
| D3 | 0.2887 | **0.8884** |
| D2 | **0.3162** | 0.5904 |

**Sparse cosine ranks D2 above D3. BM25 ranks D3 above D2 — the rankings do not match.** Both are sparse
methods; both build a vocabulary-dimensioned vector. The disagreement comes entirely from **weighting**:
raw cosine treats every word roughly equally except for how often it appears, while BM25 additionally
applies IDF (rewarding the rarer term "damaged" over the more common "refund") and caps term-frequency's
contribution (M6-L03). **The sparse-vs-dense distinction and the "which weighting scheme" question are
separate axes** — this is the single most common conceptual tangle this lesson exists to untangle.

### 5.4 The trade-off, stated plainly

| | Sparse (BM25, count vectors) | Dense (embeddings) |
|---|---|---|
| Captures shared wording | Yes, directly | Indirectly, via learned similarity |
| Captures synonymy/paraphrase | No (M6-L01's semantic gap) | Yes, when the model has learned it |
| Explainable per-match | Yes — named dimensions | No — uninterpretable dimensions |
| Requires training | No | Yes (a trained embedding model) |
| Storage/compute cost | Low, no vectors to store beyond counts | Higher (M6-L02's storage arithmetic) |
| Handles out-of-vocabulary exact strings (IDs, codes) | Yes | No (M6-L01 §5.3) |

**Neither column dominates.** This table is the direct setup for M6-L11's hybrid search, which combines
both rather than choosing one.

### 5.5 Assumptions and limitations

- §7.1's 21-word vocabulary is tiny for teaching purposes; real corpora have vocabularies in the tens or
  hundreds of thousands, making the "mostly zero" property far more extreme in practice.
- §7.2's dense model is M6-L02's small, hand-built illustration, not a real trained embedding model — a
  real model's interpretability gap is at least as large, not smaller.
- This lesson does not cover TF-IDF as a named, separate weighting scheme (a raw-count sparse vector and
  BM25 are the two points on the spectrum shown here); nor does it cover how sparse vectors are stored
  and searched efficiently at scale (an inverted index, mentioned but not built, M6-L03).

---

## 6. Worked example — the compliance team that needed to explain every match

**The system.** A compliance team builds a document search tool to find policy violations in internal
communications. Early prototypes used dense embeddings for their superior recall on paraphrased language.

**What went wrong.** When a match surfaced a document as "highly relevant" to a sensitive query, reviewers
asked, reasonably: *why?* The honest answer — "the embedding vectors were close in a 768-dimensional
space" — was not an answer a compliance process could act on, document, or defend under audit. Nothing in
the dense score named a specific word, phrase, or clause a human could point to.

**Why this mattered more here than in most search applications.** In many settings, "it's probably
relevant, here it is" is a perfectly acceptable search result. In a compliance or legal context, an
unexplainable match is close to useless — the whole point of the search is to produce something a
reviewer can cite and defend.

**The fix, and its own trade-off.** Switching to sparse retrieval (BM25) restored full explainability —
every match came with the specific overlapping terms attached — at the direct cost of §5.4's row:
paraphrased violations using different wording than the compliance keyword list went undetected, exactly
the semantic gap M6-L01 described.

**Three defects:**

| # | Defect | Consequence |
|---|---|---|
| 1 | Dense-only retrieval chosen for recall without weighing the explainability requirement | Matches could not be defended or documented in the compliance workflow |
| 2 | No stated requirement for "what must a match be able to justify" before choosing a retrieval method | The trade-off in §5.4 was discovered after building, not before |
| 3 | Switching to sparse-only traded one gap for the other, rather than combining both | Paraphrased violations became newly invisible |

### The fix

**State the explainability requirement explicitly, before choosing a method** — a compliance or audit
context usually needs §5.4's "explainable per-match" row satisfied, which sparse retrieval provides and
dense retrieval structurally cannot.

**Do not treat this as an all-or-nothing choice.** M6-L11's hybrid search lets sparse retrieval provide
an explainable primary signal while dense retrieval catches paraphrases sparse alone would miss — the
right answer to "dense or sparse" is usually "both, for different reasons," not a single winner.

**The general rule.** **Interpretability is not a nice-to-have layered on top of a retrieval method — it
is a structural property some methods have and others do not, and it belongs in the requirements before
the method is chosen, not discovered afterward.**

---

## 7. Practical activity

**File:** [`labs/m6/l04_dense_vs_sparse.py`](../../labs/m6/l04_dense_vs_sparse.py)

**No API key, no network, no model download.** Pure Python.

```bash
python labs/m6/l04_dense_vs_sparse.py
```

Every sparse vector, cosine similarity and BM25 score is exact, reproducible arithmetic.

### 7.2 Expected output

`[EXECUTED]` — 2026-09-09, Python 3.10.11.

```text
============================================================================
1. SPARSE VECTORS ARE VECTORS TOO -- JUST HUGE AND MOSTLY EMPTY
============================================================================
  Vocabulary size for this 5-document corpus: 21 words.
  A real corpus's vocabulary can run to tens of thousands of words --
  each document's sparse vector has ONE dimension per vocabulary word,
  almost all of them zero for any single short document.

  Query ['refund', 'damaged'] as a sparse vector (non-zero entries only): {'refund': 1, 'damaged': 1}
  (Every one of the other 19 vocabulary words is implicitly 0 in this vector.)

  D1  cosine=0.6325  non-zero dims: {'refund': 1, 'request': 1, 'for': 1, 'damaged': 1, 'item': 1}
  D2  cosine=0.3162  non-zero dims: {'please': 1, 'process': 1, 'my': 1, 'refund': 1, 'quickly': 1}
  D3  cosine=0.2887  non-zero dims: {'the': 1, 'item': 1, 'arrived': 1, 'damaged': 1, 'and': 1, 'broken': 1}
  D4  cosine=0.0000  non-zero dims: {'how': 1, 'do': 1, 'I': 1, 'track': 1, 'my': 1, 'order': 1}
  D5  cosine=0.6172  non-zero dims: {'refund': 4, 'please': 1, 'help': 1, 'me': 1, 'get': 1, 'my': 1}

  Ranked by sparse-vector cosine similarity: ['D1', 'D5', 'D2', 'D3', 'D4']

  This is a real, complete retrieval method: count how many times
  each vocabulary word appears, treat that as a vector, and compute
  cosine similarity exactly as M6-L02 did for dense embeddings. The
  only difference so far is dimensionality and how the vector was
  built -- counted directly from the text, versus learned by a model.

============================================================================
2. INTERPRETABILITY: A SPARSE MATCH CAN BE EXPLAINED. A DENSE ONE CANNOT.
============================================================================
  Why did 'D1' score highest against the query? Inspect the
  vector directly -- the shared, non-zero dimensions ARE the reason:

    shared vocabulary words: ['damaged', 'refund']
      'damaged': query has 1, D1 has 1
      'refund': query has 1, D1 has 1

  That is a complete, human-readable explanation. Compare this to a
  DENSE embedding (M6-L02's hand-built 4-axis toy model):

    cosine('refund', 'invoice') = 0.9975
    dimension-by-dimension: axis0=3.0*2.8, axis1=0.0*0.2, ...

  Even in this tiny, HAND-BUILT toy model, 'axis 0' has no name a
  system can report back to a user -- we know it because WE chose to
  call it 'animal-ness' or similar when we built it (M6-L01). In a
  real, trained embedding model, no axis has any human-assigned
  meaning at all. You can see THAT two vectors are close; you cannot,
  in general, see WHY, dimension by dimension, the way you just did
  for the sparse vector above.

============================================================================
3. HEAD-TO-HEAD: SPARSE COSINE vs BM25 vs A DENSE MODEL
============================================================================
  Query: ['refund', 'damaged']

  doc    sparse cosine      BM25
  D1            0.6325    1.5494
  D2            0.3162    0.5904
  D3            0.2887    0.8884
  D4            0.0000    0.0000
  D5            0.6172    0.8971

  Ranked by sparse cosine: ['D1', 'D5', 'D2', 'D3', 'D4']
  Ranked by BM25:          ['D1', 'D5', 'D3', 'D2', 'D4']
  Rankings match exactly: False

  Both methods are 'sparse retrieval' in this lesson's sense -- both
  represent documents as vectors over the vocabulary and both find
  D1 (matches both query terms) first. They differ in HOW they weight
  each dimension: raw sparse cosine treats every word equally except
  for how often it appears; BM25 additionally weights by rarity (IDF,
  M6-L03) and caps term-frequency's contribution (saturation,
  M6-L03). That difference in WEIGHTING, not the sparse-vs-dense
  distinction itself, is what usually separates 'naive keyword
  counting' from 'BM25' in practice.

============================================================================
4. WHAT THIS LAB IS AND IS NOT
============================================================================
  REAL: every sparse vector, cosine similarity and BM25 score here is
  exact, reproducible arithmetic on real corpus text.

  ILLUSTRATIVE: section 2's dense model reuses M6-L02's small,
  hand-built toy embedding to make the interpretability point
  concretely -- a real trained embedding model would be far higher-
  dimensional and its lack of per-axis meaning would be even less
  disputable, not more.

  NOT SHOWN: how a real vocabulary of tens of thousands of words is
  stored and searched efficiently for sparse vectors (an inverted
  index, M6-L03's forward reference), and how sparse and dense
  retrieval are actually COMBINED in one system -- that is M6-L11's
  reciprocal rank fusion, building directly on this lesson's
  side-by-side comparison.

Done.
```

### 7.3 Reading the result

**Section 1 is the reframe the whole lesson depends on.** Cosine similarity over sparse count vectors is
not a different kind of thing from cosine similarity over dense embeddings — it is the identical
computation, applied to a vector with a different shape and a different origin.

**Section 2's contrast is the sharpest, most portable takeaway.** "Shared vocabulary words:
`['damaged', 'refund']`" is a complete answer to "why did this match?" — `axis0=3.0*2.8, axis1=0.0*0.2,
...` is not, and cannot be made into one without inventing meaning the model itself never assigned.

**Section 3 is the result most people do not expect.** Two methods both correctly called "sparse
retrieval" disagreed on which of two documents should rank higher — D2 versus D3 — purely because of
*how* they weighted the vocabulary dimensions they share. Sparse-vs-dense and weighting-scheme are
independent design choices, and conflating them is the single most common confusion this topic produces.

---

## 8. Common mistakes and troubleshooting

1. **Equating "sparse" with "keyword search" and "dense" with "AI."** Both are vector similarity; the
   real distinction is dimensionality, sparsity, and how values are set (§3.1).
2. **Assuming all sparse methods produce the same ranking.** §7.3 shows two sparse methods disagreeing on
   the same corpus and query.
3. **Choosing dense retrieval without checking whether match explainability is a real requirement.** §6
   — this can be a hard blocker in compliance, legal, or audit contexts.
4. **Assuming a dense embedding's dimensions have interpretable meaning**, even a hand-built toy one.
   §5.2 shows this fails even in the most favourable, human-designed case.
5. **Treating BM25 and raw sparse cosine similarity as interchangeable.** They are both sparse, and they
   can rank documents differently (§5.3) — verify which your system actually uses.
6. **Picking dense or sparse as a permanent, exclusive choice** instead of recognising the trade-off table
   (§5.4) as the setup for combining both (M6-L11).

| Symptom | Likely cause | Fix |
|---|---|---|
| "Why did this document match?" has no good answer | Dense-only retrieval in a context requiring explainability | Add or switch to sparse retrieval where explainability is required (§6) |
| Two "keyword search" systems rank the same query differently | Different sparse weighting schemes (raw count vs BM25 vs TF-IDF) | Confirm which weighting scheme each system actually implements |
| Search misses paraphrased or synonymous queries | Sparse-only retrieval, no semantic component | Add dense retrieval (M6-L01's semantic gap, M6-L11's hybrid design) |
| Search misses exact codes/IDs after moving to embeddings | Dense-only retrieval, out-of-vocabulary query (M6-L01) | Keep or add sparse/exact match for identifiers |

---

## 9. Security, privacy, reliability, cost

- **Reliability.** Know whether your system needs explainable matches (compliance, legal, audit
  contexts) before choosing dense-only retrieval — the gap is structural, not fixable by better
  embeddings (§6).
- **Cost.** Sparse retrieval requires no trained model and generally less storage than dense embeddings
  at scale (M6-L02) — where explainability and exact term matching suffice, it is the cheaper default.
- **Reliability.** Verify which specific sparse weighting scheme a system implements (raw count, TF-IDF,
  BM25) rather than assuming "keyword search" means one specific thing — §7.3 shows they can disagree.
- **Privacy.** A sparse index is, in effect, a per-document word list — treat it with the same access
  controls as the underlying documents, since named dimensions can themselves reveal document content.

---

## 10. Exercises

### Exercise 1 — Beginner (~20 min)

1. In your own words, what makes a vector "sparse"?
2. Why can a sparse match be explained term by term, while a dense match generally cannot?
3. Name one thing sparse retrieval can do that dense retrieval cannot.
4. Name one thing dense retrieval can do that sparse retrieval cannot.
5. Give an example of two "sparse" methods that could disagree on a ranking, and why.

### Exercise 2 — Intermediate (~40 min)

1. Run the lab. Confirm D2's sparse cosine similarity by hand, using the printed non-zero dimensions.
2. Add a sixth document and a new query to the corpus, and compute both sparse cosine and BM25 rankings
   for it.
3. Implement a third weighting scheme — TF-IDF (term count × IDF, without BM25's saturation or length
   normalisation) — and compare its ranking to both raw sparse cosine and BM25 on the same query.
4. For a query and document pair of your choosing, write out the full "why did this match" explanation a
   sparse method would produce.
5. Design a short checklist for choosing between sparse, dense, or hybrid retrieval for a system of your
   choice, using §5.4's trade-off table.

### Exercise 3 — Challenge (~50 min)

1. Build a small function that, given a sparse match, automatically generates the kind of "shared terms"
   explanation shown in §7.2, formatted for a non-technical reviewer.
2. Research (conceptually) whether any technique exists for approximating an explanation for a dense
   match (e.g. nearest-neighbour example retrieval, attention visualisation) and write up its limitations
   compared to a sparse method's exact explanation.
3. Measure, on a larger synthetic corpus you construct, how often raw sparse cosine and BM25 disagree on
   the top-ranked document, and characterise what kind of documents cause the disagreement.
4. Design the compliance-search system from §6 properly: state the explainability requirement, propose a
   hybrid architecture, and justify which method handles which part of the requirement.
5. Write a one-page explainer, suitable for a non-technical stakeholder, of why "AI search" cannot always
   explain its own results the way "keyword search" can.

---

## 11. Quiz

*(Answers: [`answer-keys/module-06-answers.md`](../../answer-keys/module-06-answers.md#m6-l04).)*

**Q1.** In §7.1, the sparse vector for the query "refund damaged" has non-zero entries in only 2 of the
corpus's 21 vocabulary dimensions. The remaining 19 dimensions are:

- A. Undefined and cause an error if accessed.
- B. Implicitly zero, which is what makes the representation "sparse."
- C. Set to the average value across the corpus.
- D. Removed entirely from the vector.

**Q2.** Cosine similarity computed over sparse count vectors in §7.1 is:

- A. A theoretical exercise with no real retrieval application.
- B. Only valid when the corpus has fewer than 10 documents.
- C. A different mathematical operation from cosine similarity over dense embeddings.
- D. A real, complete retrieval method in its own right, using the same cosine-similarity mechanism M6-L02 used for dense embeddings.

**Q3.** In §7.2, why can a sparse match be explained by naming shared vocabulary words, while a dense
match cannot be explained the same way?

- A. Dense vectors are always longer than sparse vectors.
- B. Sparse vectors are computed faster.
- C. Each sparse dimension corresponds to a specific, named word, while a dense embedding's dimensions are learned or hand-abstracted composites with no individual meaning.
- D. Dense embeddings do not use cosine similarity.
**Q4.** The dense model used in §7.2 to demonstrate uninterpretability was:

- A. A small, hand-built toy embedding from M6-L02 — even here, where we assigned the axes ourselves, a system reporting results has no name for "axis 0" to give a user.
- B. A commercial embedding model accessed via an API.
- C. Randomly generated with no defined structure.
- D. Identical to the sparse vectors used elsewhere in the lab.

**Q5.** In §7.3, sparse cosine and BM25 produced different rankings for the same corpus and query despite
both being "sparse" methods, because:

- A. One of the two methods contains a bug.
- B. BM25 is not actually a sparse method.
- C. The corpus was different for each method.
- D. They weight vocabulary dimensions differently — raw cosine treats terms roughly equally by count, while BM25 additionally applies IDF weighting and term-frequency saturation.

**Q6.** Per §5.3, the actual distinction between "naive keyword counting" and "BM25" in practice is best
described as:

- A. Naive keyword counting is not a real retrieval method.
- B. A difference in weighting scheme within the sparse-retrieval family, not a difference between sparse and dense retrieval.
- C. BM25 is a form of dense retrieval.
- D. The two methods always produce identical rankings.

**Q7.** Both D1 and D5 in §7.3 ranked near the top under sparse cosine, but for different reasons. D1
ranked highly because:

- A. It matched both distinct query terms, "refund" and "damaged."
- B. It was the shortest document.
- C. It had the lowest word count.
- D. It repeated a single term the most times.

**Q8.** D5 ranked highly under sparse cosine mainly because:

- A. It matched both query terms.
- B. It had the highest IDF value.
- C. It repeated the term "refund" four times, which raw count-based cosine similarity does not discount the way BM25's saturation does.
- D. It was the longest document in words.

**Q9.** The general definition of "sparse" this lesson establishes is:

- A. Any retrieval method that does not use a neural network.
- B. A vector representation with one dimension per vocabulary term, mostly zero for any given short document — not merely "not using embeddings."
- C. Any vector with fewer than 100 dimensions.
- D. A vector that changes value every time it is queried.

**Q10.** This lesson's central practical distinction between dense and sparse retrieval is:

- A. Dense retrieval is always superior and should replace sparse retrieval entirely.
- B. Sparse retrieval is always superior and should replace dense retrieval entirely.
- C. The two methods are mathematically identical and differ only in name.
- D. Dense captures meaning beyond shared words but is not directly explainable per-dimension; sparse is explainable but limited to literal term overlap.

**Q11.** What does this lesson explicitly defer to M6-L11?

- A. How to compute cosine similarity.
- B. How BM25's IDF formula works.
- C. How to combine sparse and dense retrieval into one system (reciprocal rank fusion).
- D. How embedding models are trained.

**Q12.** Why does this lesson describe sparse retrieval as "a vector operation too," rather than treating
it as a fundamentally different approach from dense retrieval?

- A. Both represent documents as vectors and compute similarity between them; they differ mainly in dimensionality, sparsity, and how the vector values are determined.
- B. Sparse retrieval secretly uses embeddings internally.
- C. There is no actual difference between sparse and dense retrieval.
- D. Vector operations only apply to dense representations by definition.

**Q13.** *(Written, rubric-graded.)* In under 150 words: a colleague says "we should just use dense
embeddings for everything, since they're more advanced than keyword search." State one concrete scenario
from this lesson where that choice would cause a real problem, and what you would propose instead.

---

## 12. Revision notes

- **"Sparse vs dense" is a distinction about vector shape and origin, not about "keyword vs AI."** Both
  are cosine-similarity-style computations.
- **Sparse vectors have one dimension per vocabulary word, mostly zero.** Measured: a 2-term query is
  non-zero in only 2 of 21 corpus vocabulary dimensions.
- **Sparse matches are fully explainable; dense matches structurally are not.** Measured: a complete
  "shared words" explanation for a sparse match, versus an unnamed "axis0=3.0×2.8" for a dense one — even
  in a small, human-designed toy embedding.
- **"Sparse" is a family of methods, not one algorithm.** Measured: raw sparse cosine and BM25 disagreed
  on ranking D2 against D3 for the identical corpus and query, purely from differing weighting schemes
  (IDF, saturation).
- **Neither dense nor sparse dominates the other.** Each has a real, distinct set of strengths (§5.4's
  table) — the basis for combining both in hybrid search (M6-L11).
- **State an explainability requirement explicitly before choosing dense-only retrieval** — the gap is
  structural (§6), not something a better embedding model fixes.

---

## 13. Completion checklist

- [ ] I can define sparse and dense vectors precisely, not just by "keyword" vs "AI."
- [ ] I can compute cosine similarity over a sparse vector by hand.
- [ ] I can produce a "shared terms" explanation for a sparse match.
- [ ] I understand why a dense match cannot be explained the same way, even for a hand-built toy model.
- [ ] I know that different sparse weighting schemes (raw count, BM25) can disagree with each other.
- [ ] I check whether match explainability is a real requirement before choosing dense-only retrieval.
- [ ] I scored 10/13 on the quiz.

---

## 14. References

- Manning, C. D., Raghavan, P., and Schütze, H., *Introduction to Information Retrieval* — sparse
  (vector space model) retrieval, foundational treatment.
  <https://nlp.stanford.edu/IR-book/> `[UNVERIFIED]`
- Karpukhin, V., et al. (2020), *Dense Passage Retrieval for Open-Domain Question Answering* — a widely
  cited dense retrieval approach, for contrast. <https://arxiv.org/abs/2004.04906> `[UNVERIFIED]`

---

## 15. Next lesson

→ [M6-L05 — Exact Nearest-Neighbour Search and Its Cost](M6-L05-exact-nn-search.md)

You can now name and compare dense and sparse retrieval precisely. Next: what it actually costs to find
the best match by checking every single vector — the naive approach every faster method in this module
exists to avoid.
