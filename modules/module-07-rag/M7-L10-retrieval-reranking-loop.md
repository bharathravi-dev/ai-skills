# M7-L10 — Retrieval and Reranking in the RAG Loop

| | |
|---|---|
| **Lesson ID** | M7-L10 |
| **Difficulty** | 2 (Intermediate) |
| **Estimated study time** | 1.75 hours |
| **Prerequisites** | [M6-L12](../module-06-embeddings-search/M6-L12-cross-encoder-reranking.md) |

---

## 1. Learning objectives

1. **Assemble** BM25 retrieval (M6-L03) and cross-encoder-style reranking (M6-L12) into one working
   pipeline stage.
2. **Demonstrate** why reranking runs on a small candidate pool rather than the whole corpus, connecting
   directly to M6-L12's cost argument.
3. **Measure** why reranking's benefit is entirely conditional on the initial retrieval stage being wide
   enough to have found the document worth promoting.
4. **Demonstrate** that query-side fixes (M7-L09) and reranking are complementary paths to the same
   document, not competing techniques.
5. **Design** the retrieve-then-rerank stage of a RAG pipeline with an appropriate retrieve-k and final-k.

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **Candidate pool** | The set of documents an initial retrieval pass returns, before any reranking is applied. |
| **Retrieve-k** | The number of candidates pulled by the initial (cheap, indexable) retrieval stage. |
| **Final-k** | The number of top results kept after reranking, typically much smaller than retrieve-k. |
| **Retrieve wide, rerank narrow** | The standard pattern of pulling a generous candidate pool cheaply, then applying an expensive reranker only to that pool. |
| **Complementary fix** | A technique that reaches the same correct outcome as another by a different mechanism, such that using both is not redundant. |

---

## 3. Plain-language explanation

### 3.1 Module 6 built retrieval and reranking separately; this lesson wires them together

M6-L03 built BM25. M6-L11 built hybrid fusion. M6-L12 built cross-encoder reranking, establishing exactly
why it must run on a shortlist, never a full corpus. This lesson assembles the pieces into one real
pipeline stage — the "retrieval & reranking" box M7-L01's own architecture table left as a single line.

### 3.2 Reranking's superpower has a hard dependency

§7.1–§7.2 recap the setup: a genuine paraphrase scores low under BM25's literal matching, and a
cross-encoder-style reranker can recognize it as relevant — but only if that document is actually in the
candidate pool reranking receives. This lesson makes that dependency concrete and measured, not just
stated.

### 3.3 "Retrieve wide" is not a suggestion, it's a requirement

§7.3 is the central demonstration: the exact same reranker, given a too-narrow candidate pool, cannot
recover a genuinely relevant document — not because the reranker is weak, but because reranking can only
reorder what it's handed. Given a wide-enough pool, the same reranker succeeds completely.

### 3.4 Two fixes, one document, no competition

§7.4 closes the loop with M7-L09: expanding the query beforehand and reranking afterward are two different
mechanisms that can reach the same relevant document. Neither makes the other pointless — a system can, and
often should, use both.

---

## 4. Analogy

**A talent scout with a wide-net recruiter and a discerning interviewer.** A recruiter (initial retrieval)
quickly gathers a wide pool of resumes using cheap, simple keyword filters — fast, but crude. An
interviewer (the reranker) reads each resume in the pool carefully and correctly identifies the best
candidate, even one whose resume didn't happen to use the exact buzzwords the keyword filter searched for.
But the interviewer only ever sees the resumes the recruiter actually handed over — a brilliant candidate
whose resume the recruiter discarded before the interviewer ever saw it is lost, no matter how good the
interviewer is. The fix isn't a better interviewer; it's telling the recruiter to gather a wider pool in
the first place.

### Where the analogy breaks

- **A human recruiter can be told, informally, to "cast a wider net."** §7.3's retrieve-k is an explicit,
  numeric parameter with a direct, measured cost — no equivalent judgment call exists for a fixed BM25
  cutoff.
- **An interviewer and a recruiter are different people with different skills.** In a real system, the
  same underlying corpus and index serve both stages — the "recruiter" and "interviewer" are two different
  scoring functions applied to the same data, not two independent systems.

---

## 5. Detailed technical explanation

### 5.1 The gap reranking exists to close

`[REAL]` §7.1 ran BM25 (M6-L03's exact formula) over a 6-document corpus for the query "was my item
damaged." The literal match (D1: "the item arrived damaged") scored highest, as expected. **D6, a genuine
paraphrase ("poor condition," "contents appear broken," no literal "damaged" at all), scored 0.088 — third
of six, low despite being clearly relevant.** This reproduces the exact gap M6-L12 established
cross-encoder reranking to address.

### 5.2 Why reranking needs a shortlist, restated in this pipeline's terms

`[REAL reasoning]` §7.2 reconnects directly to M6-L12's measured finding: a cross-encoder-style score is a
joint function of query and document that cannot be precomputed or indexed. Running it against this lab's
tiny 6-document corpus is trivially cheap; M6-L12's own extrapolation showed the identical operation
becoming prohibitively expensive at thousands of documents. **The real pipeline shape is always retrieve
cheaply and narrowly first, then rerank only that narrow pool** — never the reverse.

### 5.3 Retrieve wide, rerank narrow — measured

`[REAL, measured]` §7.3 ran the identical reranker (recognizing "damaged," "broken," or "poor condition")
against two different candidate pools from the same BM25 ranking:

| Initial retrieve-k | Candidate pool | Reranked result | D6 present? |
|---|---|---|---|
| 2 (narrow) | `[D1, D4]` | `[D1, D4]` | **No** |
| 4 (wide) | `[D1, D4, D6, D2]` | `[D1, D6, D4, D2]` | **Yes**, promoted to rank 2 |

**With retrieve-k = 2, D6 never enters the pool reranking sees — the reranker cannot recover a document it
was never given.** With retrieve-k = 4, D6 enters at rank 3 within the pool and the reranker correctly
promotes it to rank 2, ahead of D4 (a color complaint that scored respectably under BM25 but isn't
genuinely about damage). **Reranking's entire benefit in this example is conditional on retrieve-k being
wide enough** — the reranker itself did not change between the two runs; only what it was given to work
with did.

### 5.4 Query expansion and reranking are complementary

`[REAL, measured]` §7.4 applied M7-L09's query expansion — adding "broken" and "condition" to the query
terms before retrieval — and re-ran BM25. **D6 jumped from rank 3 to rank 1**, using the original retrieval
method alone, with no reranking step involved at all. **This is a second, independent way of reaching the
same document**: expansion changes what retrieval looks for before it runs; reranking rescues a document
retrieval already found but under-ranked. **Neither technique makes the other redundant** — a real system
can combine query expansion, wide initial retrieval, and reranking together, each addressing the gap from
a different point in the pipeline.

### 5.5 Assumptions and limitations

- The reranker in this lab is a small, hand-coded rule (exact match vs. a fixed synonym list), standing in
  for a real trained cross-encoder — M6-L12 covers this distinction and the real model's greater
  generality in depth.
- This lab's "wide" retrieve-k (4 of 6 documents) is illustrative of the *principle*, not the *scale* —
  real systems typically retrieve tens to low hundreds of candidates out of a corpus many orders of
  magnitude larger.
- This lesson does not cover systematically choosing retrieve-k and final-k via evaluation (M6-L13), nor
  combining hybrid (BM25 + dense) initial retrieval with reranking, though both are natural extensions of
  what this lesson assembles.

---

## 6. Worked example — the reranking rollout that "didn't help"

**The system.** A search team adds cross-encoder reranking to an existing BM25-only pipeline, expecting a
measurable quality improvement, since M6-L12's own findings clearly showed reranking recovering paraphrase
matches BM25 alone misses. After rollout, measured quality barely changes.

**What was actually happening.** The existing pipeline retrieved only the top 3 BM25 results before
reranking was added — a retrieve-k chosen years earlier for a BM25-only system with no reranking step at
all. Reranking was faithfully reordering those same 3 candidates, but the documents reranking was actually
designed to rescue — paraphrases, differently-worded matches — were being excluded from the candidate pool
before reranking ever got a chance to see them, exactly as §5.3 measured directly.

**Why the team initially suspected the reranker itself.** The reranker had been validated in isolation
(on hand-picked candidate sets that already included the right answer) and looked correct. The actual gap
was upstream, in a retrieve-k value nobody had revisited when reranking was introduced.

**Three defects:**

| # | Defect | Consequence |
|---|---|---|
| 1 | Retrieve-k was left at a value chosen for the previous, reranking-free pipeline | The candidate pool reranking received was too narrow to contain the documents it was meant to rescue |
| 2 | The reranker was validated only on pools already known to contain the right answer | Its real-world dependency on retrieve-k was never tested before rollout |
| 3 | Nobody revisited retrieve-k specifically when reranking was added to the pipeline | A parameter that needed to change alongside a new pipeline stage was left unexamined |

### The fix

**Widen retrieve-k specifically when introducing a reranking stage**, per §5.3 — a retrieve-k tuned for a
reranking-free pipeline is very likely too narrow once reranking is added.

**Validate reranking against realistic candidate pools, including cases where the right answer is not
already guaranteed to be present**, not just curated pools that were pre-selected to already contain it.

**Treat retrieve-k and final-k as a pair to tune together whenever the pipeline changes**, not
independently or once and for all.

**The general rule.** **Reranking is not a drop-in addition to an existing retrieval pipeline — it changes
what retrieve-k should be, because reranking's entire value depends on retrieval having already found what
needs promoting.**

---

## 7. Practical activity

**File:** [`labs/m7/l10_retrieval_reranking_loop.py`](../../labs/m7/l10_retrieval_reranking_loop.py)

**No API key, no network, no third-party dependencies.** Runs in well under a second.

```bash
source .venv/bin/activate
python labs/m7/l10_retrieval_reranking_loop.py
```

### 7.2 Expected output

`[EXECUTED]` — 2026-09-10, Python 3.10.11 (pure standard library).

```text
============================================================================
1. THE FULL LOOP: BM25 RETRIEVAL FEEDING A CROSS-ENCODER-STYLE RERANKER
============================================================================
  Query: 'was my item damaged'

  Full BM25 ranking (M6-L03's exact formula) over the whole corpus:
    1. D1 (score 2.030): 'the item arrived damaged'
    2. D4 (score 1.683): 'the item arrived and it was the wrong color'
    3. D6 (score 0.088): 'the item package arrived in poor condition and the item contents appear broken'
    4. D2 (score 0.084): 'please process my refund for the item'
    5. D3 (score 0.071): 'my item arrived late but otherwise fine'
    6. D5 (score 0.071): 'can i return an item that arrived unopened'

  D6 is a genuine paraphrase -- 'poor condition', 'contents appear
  broken' -- with no literal 'damaged' at all, so it scores low under
  BM25 despite being clearly relevant. This is the exact shape of gap
  M6-L12's cross-encoder reranking exists to close.

============================================================================
2. WHY RERANKING RUNS ON A CANDIDATE POOL, NOT THE WHOLE CORPUS
============================================================================
  M6-L12 measured directly: a cross-encoder-style score cannot be
  precomputed or indexed, because it is a joint function of the query
  and the document together. Running it against all 6 documents
  here is cheap only because this corpus is tiny -- M6-L12's own
  extrapolation showed this cost growing linearly and becoming
  prohibitive at real corpus scale (thousands+ of documents). The real
  pipeline shape is always: retrieve a SMALL candidate pool cheaply
  first (BM25/dense/hybrid), THEN rerank only that pool.

============================================================================
3. RETRIEVE WIDE, RERANK NARROW -- MEASURED
============================================================================
  NARROW initial retrieval (top-2 by BM25): ['D1', 'D4']
  Reranked (cross-encoder-style, applied to just these 2): ['D1', 'D4']
  D6 in the final result: False

  WIDE initial retrieval (top-4 by BM25): ['D1', 'D4', 'D6', 'D2']
  Reranked (cross-encoder-style, applied to these 4): ['D1', 'D6', 'D4', 'D2']
  D6 in the final result: True

  With NARROW initial retrieval, D6 never enters the candidate pool at
  all -- no reranker, however good, can recover it, because reranking
  can only reorder what retrieval already found. With WIDE initial
  retrieval, D6 enters the pool at rank 3 and reranking correctly
  promotes it to rank 2 -- just behind the exact literal match (D1),
  and ahead of documents (D4, a color complaint) that scored
  RESPECTABLY under BM25 but are not actually about damage at all.
  Reranking's benefit is entirely conditional on retrieve_k being wide
  enough to have already found the document worth promoting.

============================================================================
4. COMPOSING WITH M7-L09's QUERY-SIDE FIXES
============================================================================
  M7-L09's query expansion, applied BEFORE retrieval this time: adding
  'broken' and 'condition' to the query terms.

    1. D6 (score 2.483): 'the item package arrived in poor condition and the item contents appear broken'
    2. D1 (score 2.030): 'the item arrived damaged'
    3. D4 (score 1.683): 'the item arrived and it was the wrong color'

  D6's rank with an EXPANDED query: 1 of 6 (was rank 3 with the original query).
  Query expansion (M7-L09) and reranking (M6-L12) are two different
  ways of reaching the same document: expansion changes what retrieval
  looks for BEFORE it runs; reranking rescues a document retrieval
  already found but under-ranked. Using expansion here means an even
  NARROW top-2 retrieval now includes D6 without reranking's help at
  all -- the two techniques compose, they don't compete for credit.

============================================================================
5. WHAT THIS LAB IS AND IS NOT
============================================================================
  REAL: BM25 scoring is M6-L03's exact, unmodified formula; every
  ranking and rerank-promotion shown is genuinely computed on real
  (if synthetic) text, not scripted to fit the narrative.

  ILLUSTRATIVE: the cross-encoder-style reranker is a small, hand-coded
  rule (exact match vs. a fixed synonym list), standing in for a real
  trained model -- M6-L12 covers this distinction and its limits in
  depth. The corpus is small enough that 'retrieve wide' here means
  top-4 of 6; at real scale this is typically top-50 to top-200 of
  millions.

  NOT SHOWN: choosing retrieve_k and final-k values systematically
  (e.g. via evaluation against held-out relevance judgments, M6-L13);
  hybrid (BM25 + dense) initial retrieval feeding the same reranking
  step, which combines M6-L11 and M6-L12 directly and is a natural
  extension left to the exercises; and assembling the final reranked
  chunks into a context window, which is M7-L11's topic next.

Done.
```

### 7.3 Reading the result

**Section 3's table is the entire lesson in one comparison.** The reranker is byte-for-byte identical in
both rows; only retrieve-k differs. That the outcome differs so completely (D6 recovered vs. not) makes
the dependency undeniable rather than merely plausible.

**Section 4 is worth reading against section 3 directly.** It would be easy to conclude from section 3
that "reranking is essential." Section 4 tempers this appropriately: the *specific* problem in this
example — a paraphrase scoring too low — has more than one valid fix, and a well-designed system does not
need to choose only one.

**The worked example in §6 is this lesson's practical punchline.** A team can implement M6-L12's reranker
correctly and still see no improvement, for a reason entirely outside the reranker itself — this is worth
checking first whenever a reranking rollout underperforms expectations.

---

## 8. Common mistakes and troubleshooting

1. **Adding reranking to an existing pipeline without revisiting retrieve-k.** §5.3, §6 — reranking's
   value is capped by what the existing retrieve-k already surfaces, which was likely tuned without
   reranking in mind.
2. **Validating a reranker only on candidate pools known to already contain the right answer.** §6 — this
   never tests the dependency on retrieve-k that matters most in production.
3. **Treating reranking as a complete fix for vocabulary-mismatch retrieval failures.** §5.3 — it is only a
   fix for documents retrieval has already found; a document excluded from the candidate pool is
   unrecoverable regardless of reranking quality.
4. **Assuming query expansion and reranking are redundant with each other.** §5.4 — they fix the same class
   of problem from different points in the pipeline and can be used together.
5. **Running reranking against the full corpus "to be safe."** §5.2 — this reproduces M6-L12's own
   measured cost blowup; reranking is specifically designed for a small candidate pool.
6. **Choosing retrieve-k once and never revisiting it as the pipeline evolves.** §6 — retrieve-k and
   final-k should be reconsidered whenever a new stage (like reranking) is added.

| Symptom | Likely cause | Fix |
|---|---|---|
| Reranking was added but measured quality barely improved | Retrieve-k was left too narrow for the new reranking stage to have anything worth promoting | Widen retrieve-k specifically when introducing reranking (§5.3, §6) |
| A known-relevant, differently-worded document never appears in final results, even with reranking enabled | The document is being excluded before reranking ever sees it | Check whether the document is in the initial candidate pool at all, before suspecting the reranker (§5.3) |
| Reranking latency or cost is much higher than expected | Reranking is being applied to too large a candidate pool (or the whole corpus) | Confirm retrieve-k is a small, bounded shortlist, not the full corpus (§5.2) |
| Two different fixes (query expansion and reranking) both seem to solve the same problem | This is expected — they are complementary, not mutually exclusive (§5.4) | Choose based on cost and latency trade-offs, or use both together |

---

## 9. Security, privacy, reliability, cost

- **Reliability.** Whenever adding a reranking stage to an existing pipeline, revisit and typically widen
  retrieve-k — reranking's value is capped by what retrieval already surfaces (§5.3, §6).
- **Reliability.** Validate a reranker against realistic candidate pools, not only ones pre-selected to
  already contain the correct answer (§6).
- **Cost.** Keep reranking's candidate pool small and bounded — it cannot be indexed and its cost is paid
  per candidate, per query, with no reuse (§5.2, inherited directly from M6-L12).
- **Reliability.** Consider query-side fixes (M7-L09) and reranking together, not as alternatives — they
  address the same class of failure from different points in the pipeline (§5.4).

---

## 10. Exercises

### Exercise 1 — Beginner (~20 min)

1. In one sentence, why did D6 score low under BM25 despite being relevant?
2. Why does reranking run on a small candidate pool instead of the whole corpus?
3. What happened to D6 with a narrow retrieve-k, and why couldn't reranking fix it?
4. What happened to D6 with a wide retrieve-k?
5. Name one way query expansion and reranking relate to each other, per this lesson.

### Exercise 2 — Intermediate (~40 min)

1. Run the lab. Confirm §7.3's narrow vs. wide reranking results and §7.4's expanded-query ranking on
   your own machine.
2. Find the minimum retrieve-k at which D6 first enters the candidate pool in this lab's corpus, and
   confirm reranking then promotes it correctly.
3. Add a new paraphrase document to the corpus (your own choice of wording) and determine the retrieve-k
   needed to recover it via reranking.
4. Combine query expansion AND reranking together (expand the query, retrieve narrow, then rerank) and
   compare the result to using either technique alone.
5. Using M6-L12's cost-extrapolation method, estimate the cost difference between reranking a retrieve-k
   of 4 versus a retrieve-k of 40 on a corpus of 10,000 documents.

### Exercise 3 — Challenge (~50 min)

1. Implement a hybrid (BM25 + dense, M6-L11-style RRF) initial retrieval stage feeding this lesson's
   reranker, and compare its candidate pool composition to BM25-only retrieval.
2. Design and run an experiment measuring reranking's recovery rate (how often a relevant but low-ranked
   document gets promoted) as a function of retrieve-k, across a range of values.
3. Implement a systematic way to choose retrieve-k and final-k using held-out relevance judgments (M6-L13's
   metrics), rather than a fixed, hand-chosen value.
4. Research (conceptually) how a real production RAG system typically sets retrieve-k and final-k in
   practice, and what trade-offs (latency, cost, quality) inform that choice.
5. Using this lesson's §6 worked example as a model, design a rollout checklist for adding a reranking
   stage to an existing retrieval pipeline, specifically addressing the retrieve-k dependency.

---

## 11. Quiz

*(Answers: [`answer-keys/module-07-answers.md`](../../answer-keys/module-07-answers.md#m7-l10).)*

**Q1.** Per §7.1, why did the genuine paraphrase D6 score low under BM25 despite being clearly relevant?

- A. BM25 has a hard-coded limit on how many documents it can score at once.
- B. The document was accidentally excluded from the corpus during retrieval.
- C. It shares no literal word like "damaged" with the query — it uses "poor condition" and "broken" instead, and BM25 can only match literal terms.
- D. The document was intentionally marked as irrelevant in its metadata.

**Q2.** Per §7.2, why does reranking run on a small candidate pool rather than the whole corpus?

- A. A cross-encoder-style score can't be precomputed or indexed (M6-L12), so its cost is paid in full per candidate; this only stays affordable at real scale if the pool is kept small.
- B. Reranking is only legally permitted to run on a limited number of documents.
- C. The whole corpus is always too large to fit in computer memory at once.
- D. BM25 refuses to hand off its results to any other scoring method.

**Q3.** Per §7.3's measured result, what happened when initial retrieval was too narrow (top-2)?

- A. Reranking automatically expanded the candidate pool to include D6 anyway.
- B. The narrow retrieval crashed with an error and produced no results at all.
- C. D6 was found and correctly promoted to the top of the reranked list.
- D. D6 never entered the candidate pool, so reranking — however good — had no way to recover or promote it.

**Q4.** Per §7.3's measured result, what happened when initial retrieval was wide enough (top-4)?

- A. D6 was excluded from the final result despite being in the candidate pool.
- B. D6 entered the candidate pool at rank 3, and reranking correctly promoted it to rank 2, ahead of a less-relevant document that had scored well under BM25 alone.
- C. Every document in the candidate pool received an identical rerank score.
- D. The wide retrieval produced the exact same final ranking as the narrow retrieval.

**Q5.** Per §7.3, what is the general principle this demonstrates about reranking?

- A. Reranking can recover any relevant document regardless of whether initial retrieval found it.
- B. Reranking should always be applied to the entire corpus, never a limited candidate pool.
- C. Reranking can only reorder what retrieval already found — its benefit is entirely conditional on the initial retrieve-k being wide enough to include the document worth promoting.
- D. The initial retrieval stage has no effect on reranking's final output.

**Q6.** Per §7.4, what did adding "broken" and "condition" to the query (query expansion, M7-L09) do to
D6's rank?

- A. It moved D6 from rank 3 to rank 1, using the original retrieval method alone, with no reranking involved at all.
- B. It had no effect on D6's rank whatsoever.
- C. It removed D6 from the corpus entirely.
- D. It caused every document to receive an identical score.

**Q7.** Per §7.4, what is the relationship between query expansion and reranking, per this lesson's
finding?

- A. Query expansion and reranking are mutually exclusive and can never be used together.
- B. Reranking always makes query expansion completely unnecessary.
- C. Query expansion always makes reranking completely unnecessary.
- D. They are two different, complementary ways of reaching the same document — expansion changes what retrieval looks for beforehand; reranking rescues an under-ranked document retrieval already found.

**Q8.** Per §7.5, what is illustrative rather than production-grade about this lab's reranker?

- A. The BM25 formula used in this lab, which is M6-L03's exact, unmodified implementation.
- B. The reranker itself: a small, hand-coded rule (exact match vs. a fixed synonym list) standing in for a real trained cross-encoder model.
- C. The corpus documents, which are drawn from a real, published dataset.
- D. The final ranking order, which is randomly generated rather than computed.

**Q9.** Per §7.5, how does "retrieve wide" scale from this lab's small corpus to real production systems?

- A. Retrieve-k should always be set to the total size of the corpus, regardless of scale.
- B. Real production systems never retrieve more than 2 candidates before reranking.
- C. This lab's "wide" means top-4 of 6 documents; at real scale, retrieve-k is typically in the tens to low hundreds out of a much larger corpus.
- D. Retrieve-k has no relationship to corpus size in any system, real or illustrative.

**Q10.** Which topic does this lesson explicitly leave to M7-L11?

- A. Assembling the final reranked chunks into a context window for generation.
- B. The BM25 formula, which this lesson covers directly instead.
- C. Cross-encoder reranking's cost structure, which this lesson covers directly instead.
- D. Query expansion, which this lesson covers directly instead.

**Q11.** Per §7.5, which combination is explicitly named as a natural extension left to the exercises, not
demonstrated in this lab?

- A. Choosing retrieve_k and final-k values systematically, which this lesson performs directly instead.
- B. The cross-encoder-style reranker itself, which this lesson performs directly instead.
- C. BM25 scoring, which this lesson performs directly instead.
- D. Hybrid (BM25 + dense) initial retrieval feeding the same reranking step, combining M6-L11 and M6-L12 directly.

**Q12.** What is the general lesson this lab demonstrates about assembling a real RAG retrieval stage?

- A. Reranking alone is always sufficient, regardless of what the initial retrieval stage does.
- B. Retrieval and reranking are complementary stages with a strict dependency — reranking's effectiveness is capped by what the initial retrieval stage actually surfaces, regardless of how good the reranker itself is.
- C. Initial retrieval alone is always sufficient, making reranking unnecessary in every case.
- D. Retrieval and reranking are entirely independent stages with no dependency between them at all.

**Q13.** *(Written, rubric-graded.)* In under 150 words: your team just added cross-encoder reranking to a
production RAG pipeline, expecting a quality improvement, but measured quality barely changed. Based on
this lesson, what would you check first, and why?

---

## 12. Revision notes

- **Reranking can only reorder what initial retrieval already found** — measured directly: an identical
  reranker recovered a genuine paraphrase (D6) when retrieve-k was wide enough (top-4), and could not
  recover it at all when retrieve-k was too narrow (top-2), because the document was never in the
  candidate pool in the first place.
- **This is why reranking runs on a small candidate pool, never the full corpus** — directly inherited
  from M6-L12's finding that a cross-encoder-style score cannot be precomputed or indexed.
- **Query-side fixes (M7-L09) and reranking are complementary, not competing** — measured directly: query
  expansion alone moved D6 from rank 3 to rank 1, a second, independent way of reaching the same document.
- **Introducing a reranking stage to an existing pipeline should prompt revisiting retrieve-k** — a
  retrieve-k tuned for a reranking-free pipeline is very likely too narrow once reranking is added.
- **Validating a reranker only on pools already known to contain the right answer misses its real
  dependency on retrieve-k**, which only shows up under realistic, unfiltered candidate pools.
- **The retrieve-then-rerank pattern assembles Module 6's separately-built pieces (M6-L03/M6-L11 retrieval,
  M6-L12 reranking) into one working stage** — this lesson's contribution is the assembly and its measured
  dependency, not new retrieval or reranking mechanics.

---

## 13. Completion checklist

- [ ] I can assemble BM25 retrieval and cross-encoder-style reranking into one working pipeline stage.
- [ ] I can explain and demonstrate why reranking runs on a small candidate pool, not the whole corpus.
- [ ] I can demonstrate and explain why reranking's benefit depends entirely on retrieve-k being wide
      enough.
- [ ] I can demonstrate that query-side fixes and reranking are complementary, not redundant.
- [ ] I revisit retrieve-k whenever a reranking stage is added to an existing pipeline.
- [ ] I validate a reranker against realistic, not pre-filtered, candidate pools.
- [ ] I scored 10/13 on the quiz.

---

## 14. References

- Pinecone, *Rerankers and Two-Stage Retrieval* (general survey of retrieve-then-rerank architecture).
  `[UNVERIFIED]`
- Anthropic documentation, guidance on retrieval pipeline design where available. `[UNVERIFIED]`

---

## 15. Next lesson

→ M7-L11 — Context Assembly and Token Budgets

You now have a complete retrieve-then-rerank pipeline stage. Next: what happens to the final, reranked
chunks before they reach the model — assembling them into a context window under a real token budget,
the stage every lab since M7-L01 has treated as a simple concatenation.
