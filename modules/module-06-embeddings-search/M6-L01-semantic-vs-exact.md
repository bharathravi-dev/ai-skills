# M6-L01 — Semantic Similarity vs Exact Matching

| | |
|---|---|
| **Lesson ID** | M6-L01 |
| **Difficulty** | 1 (Intro) |
| **Estimated study time** | 1.25 hours |
| **Prerequisites** | [M4-L04](../module-04-genai-llm-internals/M4-L04-embeddings.md) |

---

## 1. Learning objectives

1. **Explain** why exact matching misses relevant content that shares no wording with the query.
2. **Explain** why semantic similarity has its own blind spot — polysemy — that exact matching does not
   share.
3. **Compute** cosine similarity over small, hand-built vectors and use it to rank documents by meaning.
4. **Recognise** query types where semantic search cannot help at all, and why.
5. **State** the case for combining both approaches, as the foundation for everything else in Module 6.

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **Semantic search** | Retrieval based on meaning similarity between vectors, typically cosine similarity. |
| **Exact match / keyword search** | Retrieval based on literal string or token presence. |
| **Semantic gap** | The mismatch between a query's wording and a relevant document's wording that exact match cannot bridge. |
| **Out-of-vocabulary (OOV) query** | A query term with no defined vector representation. |
| **Hybrid search** | Combining exact and semantic matching in one system (M6-L11). |
| **Query vector** | The embedding representing a search query. |
| **Document vector** | The embedding representing a document, often built by pooling (M4-L04). |
| **Relevance** | Whether a document actually satisfies what a query was asking for — formalised with metrics in M6-L13. |

---

## 3. Plain-language explanation

### 3.1 Two different questions a search system can ask

**Exact match** asks: *does this literal text appear?* **Semantic search** asks: *is this vector close to
that vector?* M4-L04 gave you the mechanism that makes the second question answerable — an embedding
turns words and sentences into vectors, and cosine similarity (M3-L02) turns "close" into a number. This
lesson asks which question you should actually be asking, and shows — with vectors small enough to check
by hand — that the honest answer is: **it depends on the query, and neither question is always right.**

### 3.2 Exact match cannot bridge the semantic gap

A document about a *puppy* is exactly what someone searching for *dog* wants. Exact match cannot find it
— the word "dog" is not in the document. §7.1 shows this concretely: three separate queries, three
literal misses, three correct semantic hits.

### 3.3 Semantic search cannot always tell meanings apart

A single word can mean two unrelated things — M4-L04 called this **polysemy**. A **static** embedding
(M4-L04) for "bank" has to be one vector, and that one vector ends up sitting between "financial
institution" and "edge of a river," because it was built with no idea which sense you meant. §7.2 measures
this directly: two documents about entirely different things score almost identically similar to the bare
query "bank."

### 3.4 Some queries have no meaning to search by

An order code, a product SKU, an exact error string — these are not concepts with a position in a
meaning-space at all. Semantic search does not do badly on them; it is **undefined** for them, because
nothing assigned them a vector. §7.3 makes this the sharpest row in the lesson's comparison table.

---

## 4. Analogy

**A librarian who only recognises exact titles, versus one who only recognises subjects.** Ask the first
for "the book about a boy wizard" and they find nothing unless you say the title. Ask the second for
"catalogue number 741.5-HP-07" and they shrug — a catalogue number is not a subject, and subject-matching
has nothing to offer it.

Neither librarian is doing their job badly. They are answering different questions. The best library desk
has both: someone who can find a title instantly *and* someone who can find "that book about a boy who
discovers he's magical" even if you cannot remember its name.

### Where the analogy breaks

- **A librarian resolves ambiguity by asking a follow-up question.** A bare static query vector cannot
  ask "did you mean the river or the loan?" — it commits to one compromise vector before your intent is
  ever clarified (§7.2).
- **A librarian never returns "undefined."** Semantic search genuinely can, for a query with no
  meaningful vector at all (§7.3) — a librarian would at least try, even if unhelpfully.
- **A human librarian's two skills live in one person.** In a real system, combining both is a deliberate
  design decision (hybrid search, M6-L11), not something that happens by default.

---

## 5. Detailed technical explanation

### 5.1 Exact match's blind spot, measured

`[REAL, hand-built vectors]` §7.1 pooled hand-assigned word vectors (M4-L04's mean-pooling mechanic) into
five document vectors, then queried with words that never appear literally in any document:

| Query | Exact match | Semantic top match |
|---|---|---|
| `dog` | `[]` (miss) | D1 — "My puppy is a loyal canine companion." (cosine 1.00) |
| `vehicle` | `[]` (miss) | D2 — "The automobile needs a new engine." (cosine 1.00) |
| `money` | `[]` (miss) | D4 — "I took out a loan from the bank." (cosine 0.93) |

**Every exact match failed. Every semantic match found the right document.** This is the complete,
uncomplicated case for semantic search, demonstrated with arithmetic you can redo by hand.

### 5.2 Semantic search's blind spot, measured

`[REAL, hand-built vectors]` §7.2 queried the ambiguous word "bank" against two unrelated documents:

| Document | Meaning | Cosine similarity to "bank" |
|---|---|---|
| D4 — "I took out a loan from the bank." | Financial | **0.91** |
| D5 — "We walked along the river bank at sunset." | Natural | **0.90** |

**A 0.01 gap between two completely unrelated meanings.** Exact match, for comparison, correctly found
both documents at the surface level — it does not need to understand meaning to know the string "bank"
is present in both. **Neither result is wrong; they are answers to different questions, and the semantic
one happens to be uninformative here specifically because "bank" has only one vector to give both senses.**

### 5.3 A query with no vector at all

`[REAL]` §7.3 extended the comparison to five queries, including an order code:

| Query | Exact match | Semantic | Winner |
|---|---|---|---|
| `dog` | miss | D1 (1.00) | semantic |
| `money` | miss | D4 (0.93) | semantic |
| `bank` | D4, D5 | D4 (0.91) | ambiguous — neither alone |
| **`GB-4471`** | **D6** | **undefined** | **exact** |

**The last row is not "semantic search scored low" — it is "semantic search had nothing to compute."** An
order code was never assigned a vector, so there is no similarity to measure. Exact match finds it
instantly, because finding it requires no understanding of meaning at all.

### 5.4 The conclusion this table is building toward

Across five representative queries, semantic search won two, exact match won one outright, and one
produced a genuine tie between unrelated meanings. **No single row supports "always use semantic search"
or "always use exact match."** This four-row table is the entire argument for hybrid search (M6-L11):
combine both, and let each cover the other's blind spot.

### 5.5 Assumptions and limitations

- The word vectors in this lesson's lab are **hand-assigned on five interpretable axes**, chosen to make
  the arithmetic checkable — they are not vectors from any trained embedding model. Real models produce
  vectors with hundreds or thousands of dimensions, learned from data, and fail in messier and less
  predictable ways.
- Document vectors were built by simple mean pooling. Real embedding models often use more sophisticated
  pooling or produce sentence vectors directly (M4-L04 §5.4).
- This lesson does not cover how an embedding model is actually trained (M4-L04's job) or how large-scale
  vector search is indexed and made fast (M6-L05 onward).

---

## 6. Worked example — the support search that couldn't find its own documentation

**The system.** A support search tool is built using only exact keyword matching against a knowledge base.

**What happened.** A customer searches "how do I get my money back." The knowledge base has an article
titled "Requesting a Refund," which never uses the word "money" and phrases the process as "refund," not
"get back." Exact match returns nothing. The customer, seeing no results, opens a support ticket for a
question the documentation already answered.

**What semantic search would have done.** A query embedding for "how do I get my money back" sits close,
in meaning-space, to a document embedding for "Requesting a Refund" — §5.1's exact mechanism — even
though the two share almost no words.

**But semantic search alone is not the fix either.** The same knowledge base has an article titled "Bank
Transfer Details" for adding a payout account. A later query, "how do I add my bank details," risks
scoring close to *both* the refund article (via "money"/financial-adjacent vocabulary) and the bank-
transfer article — §5.2's exact polysemy problem, now costing a real user a confusing result list. And a
query for an exact article ID a colleague shared, like `KB-0091`, has no meaning to search by at all —
§5.3's exact failure mode.

**Three defects:**

| # | Defect | Consequence |
|---|---|---|
| 1 | Exact-match-only search missed a paraphrased query for content that existed | Unnecessary support ticket for an already-documented answer |
| 2 | A hypothetical semantic-only replacement would blur unrelated senses of shared vocabulary | Ambiguous or wrong top results for legitimately different queries |
| 3 | Neither approach alone handles a literal ID a user already has | A trivial, exact lookup would fail or need special-casing |

### The fix

**Neither engine alone is sufficient — this is the argument for hybrid search (M6-L11),** covered in
full once M6-L04 (dense vs sparse retrieval) establishes the mechanics both engines are built from. For
now, the actionable takeaway is smaller and immediate: **know which failure mode your current search
system has**, by testing it against paraphrased queries (semantic gap), ambiguous shared vocabulary
(polysemy), and literal codes (OOV) — exactly the three query shapes this lesson's lab tested.

**The general rule.** **A search system's failure mode is a direct consequence of which question it
knows how to ask.** An exact-match system cannot answer "what does this mean." A semantic-only system
cannot answer "does this exact string exist." Know which question your users are actually asking before
choosing, or combining, the tools that answer it.

---

## 7. Practical activity

**File:** [`labs/m6/l01_semantic_vs_exact.py`](../../labs/m6/l01_semantic_vs_exact.py)

**No API key, no network, no model download.**

```bash
source .venv/bin/activate
python labs/m6/l01_semantic_vs_exact.py
```

Every number in this lab is exact, hand-checkable arithmetic on small, illustrative vectors — matching
COURSE_PLAN.md's design choice to teach the math by hand with small numbers before using real models.

### 7.2 Expected output

`[EXECUTED]` — 2026-09-09, Python 3.10.11, NumPy 2.2.6.

```text
============================================================================
1. EXACT MATCH MISSES SYNONYMS AND PARAPHRASES
============================================================================
  Five documents, pooled from hand-built word vectors (mean pooling,
  M4-L04's mechanic). Query for a word that never appears literally,
  but whose MEANING is present in one document.

  query 'dog'        exact match: [] (MISS)
    semantic top match: D1 (cosine=1.00) -- 'My puppy is a loyal canine companion.'
  query 'vehicle'    exact match: [] (MISS)
    semantic top match: D2 (cosine=1.00) -- 'The automobile needs a new engine.'
  query 'money'      exact match: [] (MISS)
    semantic top match: D4 (cosine=0.93) -- 'I took out a loan from the bank.'

  In all three cases, exact match finds NOTHING -- the literal word
  never appears -- while cosine similarity over pooled vectors
  correctly ranks the document whose MEANING matches highest. This is
  the entire case for semantic search: it finds relevance that
  shares no surface form with the query at all.

============================================================================
2. SEMANTIC SIMILARITY HAS ITS OWN BLIND SPOT: POLYSEMY
============================================================================
  query 'bank' -- a word with two unrelated meanings.

  exact match (literal substring 'bank'): ['D4', 'D5']
    -- correct at the SURFACE level: both D4 and D5 do contain 'bank'.

  semantic ranking (cosine similarity):
    D4  cosine=0.91  'I took out a loan from the bank.'
    D5  cosine=0.90  'We walked along the river bank at sunset.'
    D1  cosine=0.00  'My puppy is a loyal canine companion.'
    D2  cosine=0.00  'The automobile needs a new engine.'
    D3  cosine=0.00  'She felt so joyful and glad today.'
    D6  cosine=0.00  'Your order GB-4471 has shipped.'

  D4 (a loan, financial sense) and D5 (a river, natural sense) score
  0.91 and 0.90 -- nearly identical, because 'bank' has only
  ONE static vector (M4-L04), sitting halfway between both meanings.
  The embedding cannot tell 'river bank' from 'loan from the bank'
  apart, because the query word alone carries no context. This is
  exactly why CONTEXTUAL embeddings (M4-L04) exist -- a contextual
  model reads the surrounding words and produces a DIFFERENT vector
  for 'bank' in each sentence. A static, single-word query vector,
  as used here, cannot do that by construction.

============================================================================
3. NEITHER WINS ALONE: A HEAD-TO-HEAD ON FIVE QUERIES
============================================================================
  The fifth query is an order code -- not a word with any meaning in
  this vocabulary at all.

  query       exact match finds     semantic top match            winner
  dog         []                    D1 (cosine=1.00)              semantic
  vehicle     []                    D2 (cosine=1.00)              semantic
  money       []                    D4 (cosine=0.93)              semantic
  bank        D4, D5                D4 (cosine=0.91)              neither alone (ambiguous)
  GB-4471     D6                    undefined (out of vocabulary) exact

  Read the last row. An order code has no place in a meaning-based
  vector space at all -- cosine similarity is not just wrong here, it
  is UNDEFINED, because the code was never assigned a vector.
  Exact match finds it instantly and correctly. Neither approach
  dominates the other across all five rows -- which is the argument
  for HYBRID search (M6-L11), not for picking one and discarding the
  other.

============================================================================
4. WHAT THIS LAB IS AND IS NOT
============================================================================
  REAL: every cosine similarity and exact-match result here is exact,
  reproducible arithmetic given the stated vectors -- nothing is
  simulated or approximated.

  ILLUSTRATIVE, NOT LEARNED: the word vectors themselves are hand-
  assigned on five axes chosen to make the example checkable, not
  vectors from any trained embedding model. A real model's vectors
  have hundreds or thousands of dimensions, are learned from data,
  and fail in messier, less predictable ways -- see M6-L02 onward,
  where real embedding models are used directly.

  NOT SHOWN: how an embedding MODEL actually produces these vectors
  (M4-L04 covered the mechanism; this lab starts from vectors already
  given), and any indexing or approximate search structure -- both
  are M6-L05 onward.

Done.
```

### 7.3 Reading the result

**Section 1 is the uncomplicated case for semantic search** — three literal misses, three correct
semantic hits, using nothing more exotic than mean pooling and cosine similarity.

**Section 2 is the lesson's central, honest correction.** A 0.01-point gap between two completely
unrelated meanings is not a rounding error — it is the direct, predictable consequence of giving one word
exactly one vector. Anyone who assumes semantic search "understands" a query should sit with this number.

**Section 3's last row is the sharpest single result in the lab.** Semantic search is not merely weak on
an order code — it has nothing to compute at all, because the code was never assigned a position in the
vector space. Exact match, needing no such assignment, finds it immediately.

---

## 8. Common mistakes and troubleshooting

1. **Assuming semantic search "understands" queries the way a person does.** It measures vector
   closeness; polysemy shows the limits of that (§5.2).
2. **Assuming exact match is obsolete now that embeddings exist.** §5.1 and §5.3 both show cases it wins
   outright.
3. **Not testing a search system against paraphrased queries.** The single most common way exact-match
   gaps go unnoticed until a real user hits one (§6).
4. **Not testing a search system against literal codes, IDs or exact strings.** Semantic-only systems can
   fail here silently (§5.3).
5. **Treating a single word's static embedding as if it captured a specific sense.** It captures a
   compromise across all the word's senses (§5.2, M4-L04).
6. **Choosing one approach permanently instead of testing which failure mode matters more for your
   actual queries.**
7. **Assuming this lesson's hand-built vectors represent how real embedding models behave.** They are a
   checkable illustration, not a benchmark (§5.5).

| Symptom | Likely cause | Fix |
|---|---|---|
| Users report "I know it's in there, but search finds nothing" | Exact-match-only system, semantic gap | Add semantic search, or test with paraphrased queries first |
| Search returns unrelated results for an ambiguous term | Static embedding blending multiple senses | Consider contextual embeddings, or hybrid search with exact-match tiebreaks |
| A known ID or code returns nothing from "AI search" | Semantic-only system, OOV query | Keep or add exact match for identifiers and codes |
| Search quality varies wildly by query type with no clear pattern | No systematic test set covering all three failure modes | Build a small test set like §7.3's, covering paraphrase, polysemy and exact-ID queries |

---

## 9. Security, privacy, reliability, cost

- **Reliability.** Test any search system against all three query shapes in this lesson — paraphrase,
  ambiguous shared vocabulary, and exact codes — before assuming it is "working."
- **Reliability.** A semantic-only system silently returning irrelevant results for an out-of-vocabulary
  query (§5.3) can be harder to notice than an exact-match system returning nothing, because a plausible-
  looking wrong answer does not visibly signal failure.
- **Cost.** Semantic search requires computing and storing embeddings for every document; exact match
  does not. Knowing which query types actually need semantic search (M6-L11 onward) avoids paying for
  capability you do not use.
- **Privacy.** Query text sent to an embedding model is processed the same as any other model input —
  treat it with the same handling discipline as any user-provided content (M2-L18, M10-L06).

---

## 10. Exercises

### Exercise 1 — Beginner (~20 min)

1. Give one example query where exact match would fail but semantic search would succeed.
2. Give one example query where semantic search would fail but exact match would succeed.
3. Why did "bank" score almost identically against two unrelated documents in §7.2?
4. What does "undefined" mean for a semantic similarity score, and when does it happen?
5. In one sentence, why does neither approach dominate the other?

### Exercise 2 — Intermediate (~40 min)

1. Run the lab. Confirm the cosine similarity scores for all three §7.1 queries by hand, using the stated
   vectors.
2. Add two new words and one new document of your own design to the vocabulary, and add a query that
   demonstrates the semantic-gap case (§5.1) using your new content.
3. Add a second polysemous word (e.g. "spring," "bat," "crane") with its own hand-built ambiguous vector,
   and demonstrate the same near-tie effect as §7.2's "bank" example.
4. Extend §7.3's table to eight queries of your own design, covering paraphrase, polysemy, and OOV cases,
   and report the winner for each.
5. Write a short test plan (a table of query types and what "success" looks like for each) for evaluating
   a real search system's exact-vs-semantic behaviour.

### Exercise 3 — Challenge (~50 min)

1. Implement a simple hybrid scoring function that combines exact-match presence and cosine similarity
   into one score, and test it against all five of §7.3's queries.
2. Research (conceptually, no need to run code) how a real sentence-embedding model would handle the
   "bank" polysemy case differently from this lab's static word vectors, and write up the expected
   difference.
3. Design a small, hand-built embedding space (your own axes and vectors) for a domain of your choice
   (e.g. cooking, sports), and construct one example each of a semantic-gap win, a polysemy failure, and
   an OOV query.
4. Investigate what happens to cosine similarity when a document vector is the zero vector (as `D6` is in
   this lab) and explain why the `cosine()` function guards against dividing by zero.
5. Write the design note for Project 6, stating which query types you expect your search system to face
   and which of exact match, semantic search, or both you will use for each.

---

## 11. Quiz

*(Answers: [`answer-keys/module-06-answers.md`](../../answer-keys/module-06-answers.md#m6-l01).)*

**Q1.** In §7.1, querying "dog" against documents that never contain the literal word "dog" returns:

- A. Nothing from either exact match or semantic search.
- B. No results from exact match, but the correct document from cosine similarity over pooled word vectors.
- C. The correct document from exact match, but nothing from semantic search.
- D. An error, since "dog" is not in any document.

**Q2.** Document vectors in this lab are built by:

- A. Randomly assigning a vector to each document.
- B. Copying the query vector for the most similar document.
- C. Counting the number of words in each document.
- D. Mean pooling the vectors of the words each document contains, the same mechanic M4-L04 taught for sentence embeddings.

**Q3.** In §7.2, the query "bank" scored nearly identical cosine similarity (0.91 vs 0.90) against a
financial-sense document and a nature-sense document. The cause is:

- A. "Bank" has only one static vector, positioned as a compromise between both meanings, since a single-word query carries no surrounding context.
- B. A bug in the cosine similarity formula.
- C. The two documents are actually about the same topic.
- D. Exact match failed to distinguish the two documents.

**Q4.** What would fix the polysemy problem in §7.2, per the lesson?

- A. Using a larger vocabulary of unrelated words.
- B. Switching entirely to exact match.
- C. A contextual embedding, which produces a different vector for "bank" depending on its surrounding words, rather than one fixed vector for the word alone.
- D. Increasing the number of axes in the hand-built vector space.

**Q5.** In §7.3, the query "GB-4471" scored as "undefined" under semantic search because:

- A. The cosine similarity function crashed.
- B. GB-4471 is a stop word that was filtered out.
- C. The order code appeared in too many documents.
- D. The code was never assigned a vector at all — it is out of the hand-built vocabulary, not merely dissimilar.

**Q6.** Why does exact match correctly find the order code in §7.3 while semantic search cannot?

- A. Exact match uses a larger vocabulary than semantic search.
- B. Exact match only needs the literal string to appear, which requires no meaning-based representation of the query at all.
- C. Order codes are always excluded from semantic search by design.
- D. Exact match and semantic search use the same underlying vectors.

**Q7.** The general conclusion from §7.3's five-query comparison is:

- A. Semantic search should always be preferred over exact match.
- B. Exact match should always be preferred over semantic search.
- C. Neither exact match nor semantic search dominates the other across all query types, which motivates combining them (hybrid search).
- D. The two approaches always agree with each other.

**Q8.** Why are this lab's word vectors explicitly marked as illustrative rather than real embeddings?

- A. They are hand-assigned on a small number of interpretable axes chosen to make the example checkable, not learned from data by a trained model.
- B. They were generated by a real embedding model but then rounded.
- C. They are identical to a specific commercial embedding model's actual output.
- D. They are randomly generated and have no defined structure.

**Q9.** Exact match correctly found both D4 and D5 for the query "bank" in §7.2. This shows that exact
match:

- A. Also fails to distinguish the two meanings.
- B. Can be correct at the surface (string) level while still failing to distinguish the different meanings behind that surface form.
- C. Uses semantic understanding to find both documents.
- D. Is strictly better than semantic search for every query.

**Q10.** A real embedding model, compared to this lab's hand-built vectors, per §7.4:

- A. Produces identical results in every case.
- B. Cannot be used for semantic search at all.
- C. Only works for single words, never documents.
- D. Has far more dimensions, is learned from data, and fails in messier, less predictable ways than this illustrative example.

**Q11.** The document "I took out a loan from the bank" scored 0.93 cosine similarity to the query
"money" rather than 1.00. This is because:

- A. The document's pooled vector blends "loan" with the ambiguous "bank" vector, which is not purely on the finance axis.
- B. The cosine similarity formula has a built-in rounding error.
- C. "Money" and "loan" are considered completely unrelated in this vector space.
- D. The document contains no financial vocabulary at all.

**Q12.** This lesson's central practical lesson for building a search system is:

- A. Always default to whichever approach is cheaper to implement.
- B. Semantic search alone is sufficient for any production system.
- C. Choose between (or combine) exact and semantic matching based on the actual query types your system needs to support, not by assuming one is strictly superior.
- D. Exact match should be removed once an embedding model is available.

**Q13.** *(Written, rubric-graded.)* In under 150 words: a colleague proposes replacing your product's
keyword search entirely with semantic search, citing better handling of paraphrased queries. State one
concrete query type this would break, referencing this lesson's lab, and what you would propose instead.

---

## 12. Revision notes

- **Exact match and semantic search answer different questions**: "does this literal text appear" versus
  "is this vector close to that vector." Neither is a superset of the other.
- **Exact match cannot bridge the semantic gap.** Measured: three paraphrased queries, three exact-match
  misses, three correct semantic hits.
- **Semantic search cannot resolve polysemy from a bare query word.** Measured: "bank" scored 0.91 and
  0.90 against two completely unrelated documents — a static embedding is one compromise vector across
  all of a word's senses.
- **Some queries have no meaningful vector at all.** Measured: an order code scored as undefined under
  semantic search, while exact match found it instantly.
- **Neither approach dominates across query types** — the direct motivation for hybrid search (M6-L11).
- **This lesson's vectors are hand-built and illustrative**, chosen for checkability, not real learned
  embeddings — real models are higher-dimensional, learned from data, and fail differently.
- **Test any search system against paraphrase, polysemy, and exact-code queries** before trusting it.

---

## 13. Completion checklist

- [ ] I can explain, with an example, why exact match misses a paraphrased query.
- [ ] I can explain, with an example, why semantic search struggles with polysemy.
- [ ] I can compute cosine similarity by hand on small vectors.
- [ ] I know what "undefined" means for a semantic similarity score and when it happens.
- [ ] I have tested (or would test) a search system against all three query shapes from this lesson.
- [ ] I understand that this lesson's vectors are illustrative, not real learned embeddings.
- [ ] I can state the case for hybrid search in one sentence.
- [ ] I scored 10/13 on the quiz.

---

## 14. References

- Mikolov, T., et al. (2013), *Efficient Estimation of Word Representations in Vector Space* (word2vec —
  the original static embedding approach). <https://arxiv.org/abs/1301.3781> `[UNVERIFIED]`
- Manning, C. D., Raghavan, P., and Schütze, H., *Introduction to Information Retrieval* — foundational
  treatment of exact-match (keyword) search. <https://nlp.stanford.edu/IR-book/> `[UNVERIFIED]`

---

## 15. Next lesson

→ [M6-L02 — Embedding Dimensions, Model Compatibility and Normalization](M6-L02-embedding-dimensions.md)

You now know why semantic and exact search each miss things the other catches. Next: the practical
mechanics of the vectors semantic search depends on — how many dimensions they need, why two different
embedding models' vectors cannot be mixed, and why normalization matters before you compute a single
cosine similarity.
