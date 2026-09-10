# M6-L12 — Cross-Encoder Reranking

| | |
|---|---|
| **Lesson ID** | M6-L12 |
| **Difficulty** | 3 (Advanced) |
| **Estimated study time** | 2.0 hours |
| **Prerequisites** | [M6-L11](M6-L11-hybrid-search-rrf.md) |

---

## 1. Learning objectives

1. **Explain** why a bi-encoder (independently pooled query/document vectors) is architecturally blind to
   word order and negation, regardless of how it is trained.
2. **Explain** how a cross-encoder's joint scoring of a query-document pair lets it represent interactions
   a bi-encoder cannot.
3. **Derive** why a cross-encoder's score can never be precomputed or indexed, from the same joint
   property that makes it more expressive.
4. **Measure** the real cost consequence of that property, and state why it restricts cross-encoders to
   reranking a small shortlist.
5. **Design** a two-stage retrieve-then-rerank pipeline that uses each method where its cost profile
   actually fits.

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **Bi-encoder** | A model that encodes a query and a document independently into fixed vectors, compared afterward (e.g. by cosine similarity) — the architecture behind every dense retrieval method in this module so far. |
| **Cross-encoder** | A model that takes a query and a document together as one joint input and produces a single relevance score, without ever forming an independent vector for either side alone. |
| **Joint (non-factorizable) scoring** | A score that is a function of the query and document together, `score(q, d)`, and cannot be decomposed into separately-computed `f(q)` and `g(d)` pieces compared by a fast operation. |
| **Two-stage retrieve-then-rerank** | A pipeline that retrieves a cheap, indexable shortlist first (BM25, dense, or hybrid), then reranks only that shortlist with a more expensive, joint scorer. |
| **Negation blindness** | The specific, well-known failure of mean-pooled or bag-of-words representations to distinguish a term's presence from its explicit negation, because pooling discards word order. |

---

## 3. Plain-language explanation

### 3.1 Every retrieval method in this module so far has been a bi-encoder

M6-L01's hand-built vectors, M6-L02's model-compatibility discussion, and M6-L04/M6-L11's dense scoring all
share one architecture: encode the query, encode the document, compare the two fixed vectors afterward.
This lesson introduces the other architecture — one that never forms those two independent vectors at
all.

### 3.2 Independent encoding has a real, structural blind spot

§7.1 shows this concretely, not abstractly: pooling every word in a sentence into one vector, independent
of the other sentence being compared, throws away word order. A document that explicitly says something
did **not** happen can end up looking just as similar — or more similar — to a query as a document
reporting that it did happen, because the negation word contributes almost nothing to the pooled vector on
its own.

### 3.3 Reading query and document together fixes this — at a cost

§7.2 builds a small, hand-coded stand-in for a cross-encoder: instead of pooling each side separately, it
reads the document's actual token sequence and checks what comes immediately before a key term. This is
only possible because query and document are considered **together, in order** — and it is exactly this
joint reading that a real cross-encoder does at much larger scale, with a trained model instead of a
hand-written rule.

### 3.4 The same joint property that helps also removes any possibility of indexing

§7.3 is the lesson's central, load-bearing argument: a score that only exists once query and document are
considered together cannot be computed for a document in advance, cannot be cached, and cannot be handed
to an approximate-search index (M6-L06) the way a fixed vector can. This is measured directly, not asserted
— and it is the real reason cross-encoders are used the way §7.4 shows: to rerank a small shortlist, never
to search a full corpus.

---

## 4. Analogy

**A resume-screening keyword filter versus a hiring panel interview.** A keyword filter reads each resume
once, on its own, and produces a fixed score — "matches 6 of 10 required terms" — before any specific job
opening is even considered. That score can be computed once and reused for any future opening that wants
the same 10 terms. A hiring panel, by contrast, reads a resume **in light of a specific role**, weighing
how its specific details interact with that role's specific needs — a judgment that cannot be precomputed
before the role is known, and must be redone, in full, for every candidate, for every role.

The panel produces better judgments exactly because it considers both sides jointly — the same reason it
cannot be run against every resume in a filing cabinet for every vacancy. It is reserved for a short list of
finalists the keyword filter already narrowed down.

### Where the analogy breaks

- **A hiring panel's cost scales with human time, not machine operations.** §7.3's cost argument is about
  computational indexability, a purely structural property with no analogue in human review speed.
- **A keyword filter is much simpler than a real bi-encoder.** Bi-encoders (M6-L01–M6-L11) are learned,
  often very capable, representations — the analogy is chosen to illustrate the *independent-vs-joint*
  distinction, not to suggest bi-encoders are as crude as keyword counting.

---

## 5. Detailed technical explanation

### 5.1 Why independent pooling cannot represent negation

`[REAL]` §7.1 computed cosine similarity between the query "damaged item" and five documents using
M6-L01-style hand-built vectors, with function words (including "not") assigned an all-zero vector — the
same near-neutral role such words play in real embedding spaces. The result: **D5, a document explicitly
stating the item was *not* damaged, ranked #1** — ahead of both documents genuinely reporting damage.

This is not a tuning failure specific to this vocabulary. Mean pooling computes:

$$\vec{v}(\text{doc}) = \frac{1}{n}\sum_{i=1}^{n} \vec{w}_i$$

which is invariant to the **order** of the $\vec{w}_i$ terms — "not damaged" and "damaged not" pool to the
literal same vector. Any architecture that must produce its document representation before knowing what
question will be asked of it inherits this same blindness, regardless of training.

### 5.2 A joint scorer that reads order can represent it

`[REAL]` §7.2's scorer never builds a document vector. For each occurrence of a key query term in the raw
token sequence, it inspects a small window of preceding tokens for a negation word, flipping the
contribution's sign if one is found. This correctly separated the corpus: genuinely-damaged documents
scored positive, explicitly-not-damaged documents scored negative, and the irrelevant document scored
zero — using the same five documents section 1 could not separate correctly.

**The mechanism generalizes past this hand-written rule.** A real cross-encoder feeds the concatenated
query and document tokens through a single model (typically a transformer using self-attention across the
whole combined sequence), letting every query token directly attend to every document token. Negation is
one example of an interaction this makes representable; paraphrase, entailment, and subtler relevance
judgments are others a trained model can learn that a hand-written rule cannot.

### 5.3 Why the joint score cannot be precomputed or indexed

`[REAL, measured]` §7.3 is the technical core of this lesson. A bi-encoder's document vector is computed
**once**, independent of any future query — which is precisely what M6-L06's ANN indexes require: a fixed
set of vectors that exist before any query arrives. A cross-encoder's score is not a property of the
document alone; it is a property of the **pair**, and does not exist until both are known simultaneously.
There is therefore no per-document number to cache, no vector to hand to an index — every new query
requires redoing the joint computation against every candidate, from scratch.

§7.3 measured this on 8,000 synthetic documents: building the bi-encoder index once cost roughly 84ms,
after which each additional query cost about 0.02ms by reusing it. The cross-encoder-style scorer, with no
index to build, cost about 11ms **per query**, every query, with nothing carried forward. Extrapolating
both measured rates: at 10,000 queries, the bi-encoder's total stayed near 268ms, while the cross-encoder-
style total reached over 112 seconds. The bi-encoder's cost is front-loaded and amortized; the
cross-encoder-style cost is repeated in full, indefinitely.

### 5.4 The resulting design: retrieve cheaply, rerank a shortlist

`[REAL]` §7.4 retrieved a small shortlist using bi-encoder cosine (standing in for M6-L03/M6-L04/M6-L11's
retrieval methods), then reranked only that shortlist with the joint scorer — correctly promoting the
genuinely-damaged documents above the explicitly-not-damaged ones within the shortlist, at a cost that
stayed small precisely because only the shortlist, not the full corpus, was rescanned. **This two-stage
pattern — cheap, indexable retrieval first; expensive, joint reranking second, over a small candidate set
only — is the standard, practical use of cross-encoders in a real system.**

### 5.5 Assumptions and limitations

- The "cross-encoder" in this lab is a small, hand-coded negation-window rule, not a trained transformer.
  It shares the real architectural property (joint, non-factorizable scoring) that makes real
  cross-encoders both powerful and unindexable — but a trained model detects far more than negation.
- §7.3's specific timings are tied to this lab's synthetic corpus, vocabulary, and machine; the *shape* of
  the result (one-time indexable cost vs. per-query joint cost) is the durable, general finding, not the
  exact millisecond figures.
- This lesson does not measure or compare retrieval **quality** gains from a real, trained cross-encoder —
  that requires an actual trained model, out of scope for this offline lab (§7.5).

---

## 6. Worked example — the reranker that was applied to the wrong thing

**The system.** A support-ticket search feature adds a cross-encoder reranker to improve result quality,
following advice that reranking meaningfully helps distinguish subtly different documents. To "be
thorough," an engineer configures it to rerank the **entire** candidate pool returned by a broad initial
filter — several thousand tickets for common categories — rather than a short list.

**What happened.** Search latency for common categories became unacceptably slow, occasionally timing out,
while rare-category searches (which returned few candidates) stayed fast. The team initially suspected a
problem with the reranker's model itself.

**Why it happened.** The reranker was doing exactly what §5.3 predicts: its per-candidate cost is paid in
full, every query, with no possible reuse or indexing. Applying it to thousands of candidates reproduces
§7.3's extrapolation directly — a cost that was fine at the small shortlist sizes it was designed for
becomes enormous at the scale of a full filtered pool.

**Three defects:**

| # | Defect | Consequence |
|---|---|---|
| 1 | The reranker was applied to the full filtered candidate pool, not a short list | Latency scaled with the number of candidates in the broadest categories, exactly as §7.3 measured |
| 2 | No shortlist size limit was enforced before reranking | There was no bound on how expensive a single query could become |
| 3 | The team initially investigated the model rather than the pipeline shape | Time was spent tuning the wrong component before the architectural cause was identified |

### The fix

**Retrieve a small, fixed-size shortlist first** (tens of candidates, via BM25, dense, or hybrid — M6-L03,
M6-L04, M6-L11), and rerank only that shortlist, regardless of how large the initial filtered pool is.

**Treat shortlist size as an explicit, tuned parameter**, weighing §7.3's measured cost-per-candidate
against the quality benefit of considering more candidates — not defaulting to "as many as available."

**When latency looks wrong, check the pipeline shape before the model** — §7.3's cost profile is a
property of the *architecture*, and a reranker applied to too many candidates will look slow regardless of
which specific model is used.

**The general rule.** **A cross-encoder's cost is paid per candidate, per query, with no possible reuse —
so the candidate count it is asked to score is the single most important lever on its cost, more so than
any property of the model itself.**

---

## 7. Practical activity

**File:** [`labs/m6/l12_cross_encoder_reranking.py`](../../labs/m6/l12_cross_encoder_reranking.py)

**No API key, no network, no real transformer model.** Runs in under a second.

```bash
source .venv/bin/activate
python labs/m6/l12_cross_encoder_reranking.py
```

### 7.2 Expected output

`[EXECUTED, machine-specific timings]` — 2026-09-10, Python 3.10.11, NumPy 2.2.6.

```text
============================================================================
1. A BI-ENCODER POOLS QUERY AND DOCUMENT INDEPENDENTLY -- IT CANNOT SEE NEGATION
============================================================================
  Query: 'damaged item'

  doc    text                                    cosine score
  D1     the item arrived damaged                0.9997
  D2     the item did not arrive damaged         0.9997
  D3     my item is damaged please refund it     0.7406
  D4     how do i track my order                 0.0605
  D5     the item was not damaged at all         1.0000

  Bi-encoder ranking (highest cosine first): ['D5', 'D1', 'D2', 'D3', 'D4']

  D1 and D3 genuinely report damage. D2 and D5 explicitly report the
  OPPOSITE -- the item was NOT damaged. A bi-encoder pools every word's
  vector into ONE fixed vector per text, independently, before any
  comparison happens at all. 'not' contributes an all-zero vector --
  the same near-neutral contribution it would make in real embeddings
  for a common function word -- so pooling 'not ... damaged' lands in
  almost the same place as pooling 'damaged' alone.

  Look at the RANKING, not just the scores: D5 -- explicitly
  NOT damaged -- comes out on TOP, ranked above both genuinely damaged
  documents (D1, D3). This is not a near-miss or a close call the bi-
  encoder mostly gets right; on this query it puts the single most
  clearly-irrelevant-by-content document first. Pooling destroyed the
  one piece of information (word order, and which word negation
  attached to) that would have distinguished them.

============================================================================
2. A CROSS-ENCODER-STYLE JOINT SCORER SEES THE SAME TEXT DIFFERENTLY
============================================================================
  Same query concept ('damaged'), scored by looking at the actual
  token sequence instead of a pooled vector (negation window = 3 tokens):

  doc    text                                    cross-encoder-style score
  D1     the item arrived damaged                +1
  D2     the item did not arrive damaged         -1
  D3     my item is damaged please refund it     +1
  D4     how do i track my order                 +0
  D5     the item was not damaged at all         -1

  Cross-encoder-style ranking: ['D1', 'D3', 'D4', 'D2', 'D5']

  This scorer never builds a document vector at all. It reads the
  document's tokens directly, in order, and checks what sits immediately
  before each occurrence of the query's key term -- exactly the
  information mean-pooling in section 1 threw away. D1 and D3 (genuinely
  damaged) score positive; D2 and D5 (explicitly NOT damaged) score
  negative; D4 (no mention of damage at all) scores zero. This is the
  architectural reason real cross-encoders feed query and document
  tokens jointly into one model (e.g. via self-attention over the
  concatenated pair) instead of encoding each side separately: only a
  scorer that sees both sequences together, in order, can represent an
  interaction like negation at all.

============================================================================
3. THE SAME JOINT PROPERTY MEANS THIS SCORE CAN NEVER BE PRECOMPUTED
============================================================================
  Section 1's document vectors are computed ONCE, independent of any
  future query -- exactly what makes them INDEXABLE (M6-L06's ANN
  structures are built over fixed vectors like these). Section 2's
  score does not exist until a specific query and a specific document
  are considered TOGETHER -- there is no per-document number to
  precompute, cache, or hand to an index ahead of time.

  8,000 synthetic documents, 20 queries, same machine:

  Bi-encoder:  one-time indexing (pool all 8,000 docs once): 84.3ms
               average cost PER QUERY afterward (reuses the index): 0.02ms
  Cross-encoder-style: average cost PER QUERY (must rescan all
               8,000 raw documents fresh, every time -- no index exists): 11.25ms

  Total cost for 20 queries -- bi-encoder: 84.7ms (one index build + 20 cheap reuses)
  Total cost for 20 queries -- cross-encoder-style: 225.0ms (20 full, independent rescans)

  Each cross-encoder-style query alone (11.25ms) already costs
  a meaningful fraction of the ENTIRE one-time bi-encoder index build
  (84.3ms) -- and unlike that index build, it is never reused.
  Extrapolating both measured per-query rates out to more queries
  (`[REAL arithmetic, extending this run's own measured rates]`):

     queries      bi-encoder total   cross-encoder-style total
          20                  85ms                       225ms
         100                  86ms                       1.13s
       1,000                 103ms                      11.25s
      10,000                 268ms                     112.52s

  Read the SHAPE of this, not just the numbers: the bi-encoder pays its
  8,000-document cost close to ONCE -- its total barely grows with more
  queries -- and M6-L06 showed those same precomputed vectors can be
  indexed for sub-linear query cost too, shrinking this further. The
  cross-encoder-style scorer's total grows LINEARLY with every additional
  query, because there is no fixed per-document representation to reuse
  or index -- each query re-pays a cost of the same order as the entire
  one-time bi-encoder index build. This is exactly why cross-encoders
  rerank a small, already-retrieved SHORTLIST (tens of candidates, from
  M6-L03/M6-L04/M6-L11), never the full corpus: rescanning 8,000 candidates
  on every single query does not stay cheap the way a bi-encoder's
  reused, indexable representation does.

============================================================================
4. RERANKING A SHORTLIST: WHERE THIS ACTUALLY EARNS ITS COST
============================================================================
  A realistic pipeline never runs the cross-encoder-style scorer over
  the whole corpus. It retrieves a small shortlist cheaply first (bi-
  encoder cosine here, standing in for M6-L03/M6-L04/M6-L11's retrieval),
  then reranks ONLY that shortlist.

  Bi-encoder retrieval shortlist (top 4): ['D5', 'D1', 'D2', 'D3']
  Bi-encoder order within the shortlist: ['D5', 'D1', 'D2', 'D3']
  Cross-encoder-style rerank of the SAME shortlist: ['D1', 'D3', 'D5', 'D2']

  Read this against section 1's own numbers: bi-encoder retrieval alone
  cannot reliably separate D1/D3 (genuinely damaged) from D2/D5 (explicitly
  not damaged) -- all four are 'about damage' to a pooled vector. Reranking
  that same shortlist with a scorer that reads token order fixes exactly
  this, at a cost that stayed small specifically because the shortlist,
  not the full 8,000-document corpus, is what got rescanned.

============================================================================
5. WHAT THIS LAB IS AND IS NOT
============================================================================
  REAL: the pooling/cosine formulas are M6-L01's exact mechanism; the
  negation-window rule's outputs are computed precisely as coded; the
  section 3 timings are real, measured wall-clock costs on this machine.

  ILLUSTRATIVE: the 'cross-encoder' here is a small, hand-coded rule
  (scan for a negation word in a fixed window before a key term), not a
  trained transformer. A real cross-encoder (e.g. a fine-tuned BERT
  scoring the concatenated query+document pair) learns to detect far
  more general interactions -- paraphrase, entailment, subtle relevance
  -- from training data, rather than a hand-written rule. It shares the
  exact ARCHITECTURAL property this lab demonstrates: score(query, doc)
  is a single joint function of both texts together, not a comparison
  of two independently-computed representations -- which is what makes
  it powerful AND what makes it impossible to index.

  NOT SHOWN: running an actual pretrained cross-encoder model, and how
  much its learned interactions outperform hand-written rules like
  negation detection on real, varied language -- both require a real
  trained model, out of scope for this offline, from-scratch lab.

Done.
```

### 7.3 Reading the result

**Section 1's result is stronger than "the bi-encoder is a little confused."** D5 — the document stating
the opposite of what genuinely happened — ranked strictly first. This is worth sitting with: independent
pooling is not merely imprecise about negation, it can actively invert the intended ranking.

**Section 3 is the lesson's real payoff, and its shape matters more than its exact milliseconds.** The
bi-encoder's total cost curve is nearly flat as queries increase; the cross-encoder-style curve is a
straight line through the origin with a steep slope. Any two-stage system design follows directly from
which side of that shape each stage's cost sits on.

**Section 4 shows the two findings combined into the actual, practical pattern**: retrieval gets you a
short list cheaply (even when, as here, its internal order is wrong); reranking fixes the order, and stays
cheap only because it was confined to that short list.

---

## 8. Common mistakes and troubleshooting

1. **Assuming a bi-encoder's failure to handle negation is a training problem, fixable with more data.**
   §5.1 — it is architectural: mean pooling discards word order regardless of training.
2. **Applying a cross-encoder to a large candidate pool instead of a short list.** §6 — its cost is paid
   in full, per candidate, per query, with no possible reuse.
3. **Expecting a cross-encoder's score to be cacheable per document.** §5.3 — the score does not exist
   until a specific query is also known; there is nothing to precompute per document alone.
4. **Trying to build an ANN index over cross-encoder scores.** §5.3 — ANN indexes (M6-L06) require fixed,
   precomputed vectors; a joint score is not decomposable into one.
5. **Skipping retrieval and reranking the entire corpus directly.** §7.3's extrapolation shows this cost
   grows linearly and without bound — retrieval (M6-L03/M6-L04/M6-L11) exists specifically to avoid this.
6. **Treating this lab's hand-coded negation rule as equivalent to a real trained cross-encoder's
   capability.** §7.5 — the architecture is genuinely shared; the learned expressiveness is not.

| Symptom | Likely cause | Fix |
|---|---|---|
| Search results rank a document contradicting the query above one confirming it | Bi-encoder pooling discarding word order/negation | Add a reranking stage that reads token order jointly (§5.2, §7.2) |
| A reranking stage makes queries dramatically slower as result-pool size grows | Cross-encoder-style scorer applied to too many candidates | Retrieve a small shortlist first; rerank only that shortlist (§5.4, §6) |
| An attempt to "index" a reranker's scores for reuse fails or makes no sense | The score is a joint function of query and document, not a per-document property | Do not attempt to precompute or cache reranker scores independent of a query (§5.3) |
| Reranking quality seems limited to simple, rule-like distinctions | Using a hand-written rule instead of a trained model | A hand-written rule (as in this lab) only catches what it was written to catch; a trained cross-encoder generalizes further (§7.5) |

---

## 9. Security, privacy, reliability, cost

- **Reliability.** Never assume a bi-encoder correctly handles negation or word-order-dependent meaning —
  test explicitly for it, since the failure is structural, not a matter of degree (§5.1).
- **Cost.** Always bound the number of candidates passed to a cross-encoder reranker — its cost is paid in
  full per candidate, per query, and grows without bound if applied to an unbounded pool (§5.3, §6).
- **Reliability.** Use retrieval (BM25, dense, or hybrid) to produce a shortlist before reranking — never
  substitute a cross-encoder for the retrieval stage itself (§5.4).
- **Cost.** Size the shortlist explicitly as a tuned trade-off between reranking quality and measured
  per-candidate cost (§7.3's extrapolation method), rather than defaulting to the largest available pool.

---

## 10. Exercises

### Exercise 1 — Beginner (~20 min)

1. In one sentence, why can't a bi-encoder distinguish "damaged" from "not damaged" by construction?
2. What does a cross-encoder read that a bi-encoder never sees?
3. Why can a cross-encoder's score not be precomputed or cached per document?
4. What is the standard two-stage pattern for using a cross-encoder in a real search system?
5. Name one thing this lab's cross-encoder-style scorer does NOT demonstrate, per §7.5.

### Exercise 2 — Intermediate (~40 min)

1. Run the lab. Confirm section 1's ranking and section 2's scores by hand for at least two documents.
2. Add a document with a *double* negation (e.g. "the item was not undamaged") and report what the toy
   scorer does with it — does the rule's simplicity show through?
3. Extend the negation window size (e.g. from 3 to 6 tokens) and report whether any document's score
   changes, explaining why or why not given the specific sentences in the corpus.
4. Using §7.3's measured per-query rates, compute the query count at which cross-encoder-style total cost
   would exceed one minute, and compare it to a shortlist size you consider realistic for a production
   reranker.
5. Design a small experiment (conceptually, or in code) that would demonstrate a cross-encoder-style
   scorer correctly handling a case bi-encoder pooling gets wrong, other than negation.

### Exercise 3 — Challenge (~50 min)

1. Implement a full two-stage pipeline over a larger synthetic corpus: retrieve the top 50 by bi-encoder
   cosine, then rerank with the cross-encoder-style scorer, and measure end-to-end latency versus
   reranking the full corpus directly.
2. Extend the hand-coded scorer to detect a second interaction pattern beyond negation (e.g. an explicit
   comparison, "worse than" vs. "better than") and demonstrate it correcting a bi-encoder ranking mistake.
3. Research (conceptually) how a real cross-encoder like a fine-tuned BERT model is trained (typically on
   labeled query-document relevance pairs) and contrast this training signal with the hand-written rule
   used in this lab.
4. Design a monitoring plan for a production retrieve-then-rerank pipeline that would catch the §6
   incident (reranker applied to too large a pool) before it caused a latency incident.
5. Using this lesson's cost-shape argument (§5.3), explain in writing why no clever optimization can make
   a true cross-encoder's per-query cost independent of candidate count, tying your answer to the
   definition of joint, non-factorizable scoring.

---

## 11. Quiz

*(Answers: [`answer-keys/module-06-answers.md`](../../answer-keys/module-06-answers.md#m6-l12).)*

**Q1.** In §7.1, why did D5 ("the item was not damaged at all") rank #1 for the query "damaged item" under
the bi-encoder?

- A. Mean pooling combines every word's vector independent of order, and the negation word "not" contributed an all-zero vector, so pooling "not damaged" landed close to pooling "damaged" alone.
- B. The query was tokenized incorrectly.
- C. D5 was assigned a larger vector magnitude than the other documents by mistake.
- D. Cosine similarity cannot be computed correctly on documents shorter than six words.

**Q2.** A bi-encoder is architecturally unable to reliably distinguish "X happened" from "X did not
happen" because:

- A. It has not been trained on enough examples of negation.
- B. Cosine similarity itself cannot represent negative relationships between vectors.
- C. Negation words are always excluded from the vocabulary entirely.
- D. Its document vector is computed by pooling words independently of order, before any comparison with a query occurs, discarding the one signal (word order/attachment) that negation depends on.

**Q3.** The lab's cross-encoder-style scorer in §7.2 is able to detect negation because it:

- A. Reads the document's raw token sequence directly and checks for a negation word in a window immediately preceding a key query term, rather than comparing two independently pooled vectors.
- B. Computes cosine similarity twice instead of once.
- C. Uses a larger embedding dimensionality than the bi-encoder.
- D. Removes all function words from the document before scoring.

**Q4.** Per §5.3, a cross-encoder's relevance score cannot be precomputed or cached per document because:

- A. Cross-encoders are always too slow to run more than once.
- B. Document text changes too frequently in most applications.
- C. Precomputation is only unavailable for documents longer than a fixed length.
- D. The score is a joint function of the query and document together and does not exist as a property of the document alone until a specific query is also known.

**Q5.** Per §5.3, why can't a cross-encoder's scores be organized into an ANN index the way bi-encoder
vectors can (M6-L06)?

- A. ANN indexes only support cosine similarity, never other scoring functions.
- B. ANN indexes are limited to corpora smaller than a few thousand documents.
- C. Cross-encoder scores are always negative numbers, which ANN indexes cannot store.
- D. ANN indexes require a fixed, precomputed vector per item that exists independent of any query — which a cross-encoder, by construction, never produces.

**Q6.** §7.3 measured that the bi-encoder's one-time indexing cost was roughly 84ms for 8,000 documents,
after which each additional query cost about 0.02ms. The cross-encoder-style scorer's cost was roughly
11ms **per query**, with no reuse. Extrapolated to 10,000 queries, this means:

- A. Both approaches end up costing roughly the same total amount.
- B. The bi-encoder's total cost grows far faster than the cross-encoder-style total.
- C. The cross-encoder-style total cost grows linearly and becomes over a hundred times larger than the bi-encoder's, whose total stays close to its one-time indexing cost.
- D. Neither approach's total cost depends on the number of queries at all.

**Q7.** The general, practical reason cross-encoders are used to rerank a small shortlist rather than
search a full corpus is:

- A. Cross-encoders produce lower-quality rankings than bi-encoders on large corpora.
- B. Their per-candidate, per-query cost has no possible reuse or indexing, so it must be paid in full for every candidate scored, on every query — which only stays affordable at small candidate counts.
- C. Cross-encoders are only compatible with corpora smaller than a few hundred documents by design.
- D. Bi-encoders are always more accurate than cross-encoders, making reranking unnecessary.

**Q8.** In §7.4's shortlist rerank, the bi-encoder's retrieval order was `['D5', 'D1', 'D2', 'D3']` and the
cross-encoder-style rerank produced `['D1', 'D3', 'D5', 'D2']`. This demonstrates:

- A. The two methods always produce identical rankings.
- B. Reranking a small, already-retrieved shortlist can correct an ordering mistake retrieval made, at a cost that stays small because only the shortlist was rescanned.
- C. Reranking has no effect on ranking order in this lab.
- D. The bi-encoder's retrieval step was unnecessary and could have been skipped entirely.

**Q9.** Per §7.5, what does this lab's hand-coded negation-window scorer NOT demonstrate?

- A. How a real, trained cross-encoder's learned interactions compare in scope to a hand-written rule, since no trained model is run in this lab.
- B. That negation is one example of such an interaction.
- C. That a joint scorer can, in principle, represent interactions a bi-encoder cannot.
- D. That cross-encoder-style scores cannot be precomputed per document.

**Q10.** The general design pattern this lesson establishes for combining retrieval and reranking is:

- A. Always use a cross-encoder alone and skip retrieval entirely.
- B. Always use bi-encoder retrieval alone and skip reranking entirely.
- C. Retrieve a cheap, indexable shortlist first (BM25, dense, or hybrid), then rerank only that shortlist with a more expensive, joint scorer.
- D. Alternate randomly between bi-encoder and cross-encoder scoring for each query.

**Q11.** Per §6's worked example, what was the actual root cause of the latency incident, correctly
identified only after investigation?

- A. The cross-encoder model itself was defective.
- B. The database connection was misconfigured.
- C. The reranker was being applied to a large filtered candidate pool instead of a small, fixed-size shortlist.
- D. The bi-encoder's vectors were computed incorrectly.

**Q12.** The single most important lever on a cross-encoder reranker's cost, per §6's general rule, is:

- A. The specific programming language the scorer is implemented in.
- B. The number of candidates it is asked to score per query, since that cost is paid in full with no possible reuse.
- C. The number of dimensions used in the bi-encoder's retrieval vectors.
- D. The total size of the full corpus, regardless of shortlist size.

**Q13.** *(Written, rubric-graded.)* In under 150 words: explain why a cross-encoder can correctly handle
a case (such as negation) that a bi-encoder gets wrong, and why that same reason makes it unsuitable for
searching a full corpus directly.

---

## 12. Revision notes

- **Bi-encoders pool query and document independently before comparing them**, which discards word order —
  a structural limitation, not a training deficiency. Measured: a document explicitly denying what a query
  described ranked #1 for that query.
- **Cross-encoders score a query-document pair jointly**, reading both together rather than comparing two
  independently-computed vectors — which is what lets them represent interactions like negation at all.
- **The same joint property that makes cross-encoders more expressive makes their scores impossible to
  precompute, cache, or index** — a score that only exists once both query and document are known has no
  per-document representation to reuse.
- **This cost was measured directly**: a bi-encoder's one-time indexing cost is paid once and amortized
  over all future queries; a cross-encoder-style score is repaid in full on every query, with no reuse —
  extrapolated to 10,000 queries, a gap of milliseconds versus minutes.
- **The standard, practical pattern is retrieve-then-rerank**: use cheap, indexable retrieval (BM25, dense,
  or hybrid — M6-L03/M6-L04/M6-L11) to produce a small shortlist, then apply the more expensive joint
  scorer only to that shortlist.
- **This lab's hand-coded negation rule shares cross-encoders' architecture but not their learned
  generality** — a real, trained cross-encoder detects far more than one hand-written rule can.

---

## 13. Completion checklist

- [ ] I can explain why bi-encoders are structurally blind to word order and negation.
- [ ] I can explain how a cross-encoder's joint scoring represents interactions a bi-encoder cannot.
- [ ] I can derive why a cross-encoder's score cannot be precomputed or indexed, from its joint property.
- [ ] I understand the measured cost consequence: amortized one-time cost versus repeated full cost.
- [ ] I can design a retrieve-then-rerank pipeline and explain why each stage is used where it is.
- [ ] I know to bound shortlist size explicitly rather than reranking an unbounded candidate pool.
- [ ] I scored 10/13 on the quiz.

---

## 14. References

- Reimers, N., Gurevych, I., *Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks*, EMNLP 2019
  (contrasts bi-encoder and cross-encoder architectures directly). `[UNVERIFIED]`
- sentence-transformers documentation, *Cross-Encoders*. <https://www.sbert.net/examples/applications/cross-encoder/README.html> `[UNVERIFIED]`

---

## 15. Next lesson

→ [M6-L13 — Retrieval Metrics: Precision@k, Recall@k, MRR, nDCG and Relevance Labels](M6-L13-retrieval-metrics.md)

You now have two complementary tools — hybrid retrieval (M6-L11) and cross-encoder reranking — for
building a search pipeline. Next, and closing Module 6: the metrics that let you measure, rigorously,
whether any of it actually worked.
