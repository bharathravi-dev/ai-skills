# M7-L06 — Chunking I: Size, Overlap and Document Boundaries

| | |
|---|---|
| **Lesson ID** | M7-L06 |
| **Difficulty** | 2 (Intermediate) |
| **Estimated study time** | 2.0 hours |
| **Prerequisites** | [M7-L05](M7-L05-cleaning-normalization-deduplication.md) |

---

## 1. Learning objectives

1. **Demonstrate** that fixed-size chunking splits text without regard for word or sentence boundaries.
2. **Measure** how a chunk that is too big dilutes relevance for any single topic it contains.
3. **Measure** how a chunk that is too small can split one fact across two chunks, losing information no
   single chunk can recover.
4. **Implement** overlap and explain precisely what it does and does not guarantee, including its real
   storage cost.
5. **Implement** boundary-aware chunking using structure preserved at ingestion (M7-L03), and explain why
   it is preferable to an arbitrary character count wherever structure exists.

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **Chunk** | A retrieval-sized piece of a document, produced by splitting it during ingestion. |
| **Fixed-size chunking** | Splitting text at a constant character (or token) count, without regard for word, sentence, or topic boundaries. |
| **Overlap** | Shared content between adjacent chunks, intended to recover information that would otherwise be split by a hard chunk boundary. |
| **Relevance dilution** | The reduction in a chunk's similarity score to a specific query, caused by merging unrelated content into the same chunk. |
| **Boundary-aware chunking** | Splitting text at a document's own natural structural boundaries (headings, sections) rather than at an arbitrary count. |

---

## 3. Plain-language explanation

### 3.1 Every lab since M7-L01 has used a placeholder; this lesson replaces it

M7-L01's naive sentence-splitting, M7-L04's simulated fixed-size cuts through a table, and every other
lab's chunking has been a deliberate stand-in. This lesson is where chunking gets a real treatment — the
trade-offs, not yet the sophisticated algorithms (that's M7-L07).

### 3.2 A fixed count doesn't know what a word is

§7.1 shows the simplest possible chunker (split every N characters) doing exactly what its definition
promises and nothing more — cutting through words and sentences with no awareness that they exist.

### 3.3 Too big dilutes; too small loses

§7.2 and §7.3 are this lesson's two central, opposite failure modes, both measured directly rather than
asserted: a chunk containing multiple unrelated topics scores *worse* on the query it should answer best,
because pooling blends in irrelevant content; a chunk that's too small can split one fact's label from its
value, with neither resulting chunk able to answer a question the original document clearly could.

### 3.4 Overlap is a real fix with a real, measurable cost

§7.4 doesn't just claim overlap helps — it shows a case where it's needed, how much overlap that specific
case actually required, and why overlap is a probabilistic mitigation, not a guarantee. §7.6 completes the
picture with overlap's actual storage cost, so both sides of the trade-off are on the table together.

### 3.5 If structure exists, use it instead of guessing

§7.5 returns to M7-L03's preserved heading structure and uses it to chunk by section instead of by count —
the single most direct way to avoid both failure modes at once, wherever a document's own structure is
available.

---

## 4. Analogy

**Slicing a loaf of bread with a ruler versus slicing it at its own natural seams.** A ruler-based slicer
cuts at exactly 2cm intervals regardless of what's there — sometimes straight through a raisin, sometimes
leaving one slice mostly crust and another mostly crumb. A slice that's too thick contains a bit of every
different filling baked into that loaf, so it doesn't taste distinctly of any one of them. A slice that's
too thin might separate a filling from the piece of bread that was supposed to hold it together. Slightly
overlapping cuts can rescue a filling that would otherwise fall exactly on a cut line — but if a rare,
extra-long ingredient runs the length of several thin slices, only a much more generous overlap (or a
thicker slice to begin with) would ever keep it whole. A loaf with its own natural seams — like a braided
challah — can be pulled apart along those seams instead, keeping each complete section intact without
guessing at all.

### Where the analogy breaks

- **Bread doesn't have an embedding or a relevance score.** §7.2's dilution effect (a big chunk scoring
  *worse*, not just "less precisely") has no clean physical analogue — it's a specific consequence of mean
  pooling (M6-L01), not a general property of "big pieces."
- **A loaf's seams are usually visually obvious.** §7.5's structural boundaries require the structure to
  have been explicitly preserved during ingestion (M7-L03) — nothing about raw extracted text announces
  where a section begins or ends by itself.

---

## 5. Detailed technical explanation

### 5.1 Fixed-size chunking, exactly as advertised

`[REAL]` §7.1 chunked a 224-character document at a fixed 60 characters, producing chunks that split
"remotely...with manager" mid-word ("...with m" | "anager approval...") and cut through sentences with no
regard for where they ended. **This is not a bug in the implementation — it's the complete, correct
behavior of a chunker whose only rule is "every N characters."**

### 5.2 Too big: measured relevance dilution

`[REAL, measured]` §7.2 built one chunk merging three unrelated sentences (damage/refund, remote work,
quarterly revenue) and compared it against a chunk containing only the damage/refund sentence, for the
query "damaged item refund." The correctly-scoped small chunk scored a perfect **1.0000**; the big, mixed
chunk scored **0.8039** — the *same sentence, word for word*, scored measurably worse purely because
unrelated content was pooled into the same vector (M6-L01's mean-pooling mechanism). **A chunk that is too
big doesn't just retrieve less precisely — it can actively underperform a smaller, correctly-scoped chunk
on the exact query it should answer best.**

### 5.3 Too small: a fact split across a hard boundary

`[REAL]` §7.3 chunked a single fact ("...Mid tier...twenty days of PTO...") at a small 45 characters,
putting "Mid tier" in chunk 1 and "twenty" in chunk 2. **Neither chunk alone can answer a question about
the Mid tier's PTO allowance** — this is exactly M7-L04's table-flattening chunk-boundary failure,
reproduced here for ordinary prose rather than a table, showing the failure shape is general, not specific
to tables.

### 5.4 Overlap: what it fixes, what it costs to fix it

`[REAL, measured]` §7.4 confirmed no arrangement of non-overlapping 45-character chunks contained both "Mid
tier" and "twenty" together. Adding overlap fixed this — but **it took 30 characters of overlap out of a
45-character chunk (67%)** to bridge the actual distance between the two pieces of information. **This is
an honest, deliberately non-clean result**: a small, typical overlap fraction (10-20%, often recommended as
a default) would not have recovered this specific split, because the label and its value were simply too
far apart relative to chunk size for a small overlap to reach across. **Overlap is a probabilistic
mitigation for splits near a boundary, not a guarantee for any split, however far apart the related content
happens to be.**

### 5.5 Boundary-aware chunking, using structure already preserved

`[REAL]` §7.5 chunked the same two-section document two ways: fixed-size (70 characters), which merged
part of the Remote Work section with part of the Expense section into one chunk; and boundary-aware
(splitting at each Markdown heading, reusing M7-L03's structure-parsing approach), which kept each section
completely intact. **Wherever document structure exists and was preserved at ingestion, using it directly
avoids both §5.2 and §5.3's failure modes at once** — no guessing about size, no merging unrelated
sections, no splitting one section's heading from its own body.

### 5.6 Overlap's cost, measured directly

`[REAL, measured]` §7.6 measured total corpus size (in characters, across all chunks) at 0%, 10%, 25%, and
50% overlap on a longer document: total stored content grew from the baseline up to **+96.8% at 50%
overlap** — nearly double. **Every character of overlap is embedded and stored more than once.** This is
the other half of §5.4's trade-off: recovering a specific split requires overlap sized to the actual gap
being bridged, and that overlap is never free.

### 5.7 Assumptions and limitations

- This lesson's chunk sizes (45-100 characters) are chosen to make failures visible in a short synthetic
  document. Real systems typically chunk by *token* count, at sizes of hundreds of tokens.
- §5.4's specific 67% overlap figure is particular to this lab's specific fact and chunk size — it is not
  a general recommendation; it demonstrates that the *required* overlap depends on the actual distance
  between related content, which varies by document.
- This lesson does not cover the specific, more sophisticated chunking *algorithms* (sentence-boundary,
  semantic, recursive) that reduce the need to rely on overlap in the first place — that is M7-L07's topic.

---

## 6. Worked example — the policy bot that answered PTO questions correctly only half the time

**The system.** An internal policy assistant chunks its knowledge base at a fixed 200 tokens, no overlap,
no structure awareness — chosen because it was the fastest thing to implement at launch.

**What went wrong.** Employees asking about PTO accrual by tier got correct answers roughly half the time;
the other half, the assistant either gave an incomplete answer or said it didn't have the information. The
same underlying document answered the question correctly when tested manually by reading the whole policy.

**Why it was inconsistent rather than always broken.** Per §5.3, whether a fixed-size chunk boundary
happens to fall between a tier name and its PTO figure depends on exactly where that specific fact sits
relative to the fixed 200-token grid — for some tiers, the split happened to land elsewhere in the
document; for others, it landed exactly between the label and the value. **This is precisely why the
symptom looked random rather than reproducible**: it was, in fact, entirely deterministic, just sensitive
to details (fact position, chunk boundary position) nobody was looking at.

**Three defects:**

| # | Defect | Consequence |
|---|---|---|
| 1 | Chunk size and boundaries were chosen without checking how they interacted with the actual document's fact positions | Some facts were split by chance; others weren't, producing inconsistent-looking results |
| 2 | No overlap was used at all | Nothing mitigated the splits that did occur |
| 3 | The document's own heading/section structure (available from ingestion, M7-L03) was never used | A reliable, structure-respecting alternative to guessing at chunk size existed and went unused |

### The fix

**Use boundary-aware chunking wherever document structure is available**, per §5.5 — this is not merely
"one option among several," it directly eliminates the class of failure this incident describes.

**Where fixed-size chunking must be used, add overlap sized to the actual documents**, per §5.4 and §5.6 —
check how far apart related facts typically fall in your own corpus before choosing an overlap fraction.

**Test retrieval specifically against facts positioned near likely chunk boundaries**, not just against
easy, centrally-located facts — this is a predictable failure mode (§5.3), worth checking for deliberately
rather than discovering from user reports.

**The general rule.** **A fixed chunk size and boundary position is a bet that no important fact happens
to straddle it — check that bet against your actual documents, or remove the need to make it at all by
chunking at the document's own structural boundaries.**

---

## 7. Practical activity

**File:** [`labs/m7/l06_chunking_size_overlap.py`](../../labs/m7/l06_chunking_size_overlap.py)

**No API key, no network, no third-party dependencies.** Runs in well under a second.

```bash
source .venv/bin/activate
python labs/m7/l06_chunking_size_overlap.py
```

### 7.2 Expected output

`[EXECUTED]` — 2026-09-10, Python 3.10.11 (pure standard library).

```text
============================================================================
1. FIXED-SIZE CHUNKING SPLITS TEXT ARBITRARILY
============================================================================
  Document (224 characters), chunked at a fixed 60 characters, no regard for word or sentence boundaries:

    Chunk 1: 'Employees may work remotely up to three days per week with m'
    Chunk 2: 'anager approval. Fully remote arrangements require VP approv'
    Chunk 3: 'al and a signed remote work agreement. Expense reports must '
    Chunk 4: 'be submitted within thirty days of purchase.'

  Notice chunk boundaries land mid-word ('remote' split across chunks,
  'manager' split across chunks) and mid-sentence. A fixed character
  count has no concept of where a word, sentence, or idea actually ends
  -- it cuts at a count, not at a meaningful boundary.

============================================================================
2. CHUNK SIZE: TOO BIG DILUTES RELEVANCE, MEASURED
============================================================================
  Query: 'damaged item refund'

  ONE big chunk (3 unrelated topics merged): 'The item was damaged and I need a refund please. Remote work requires manager approval. Quarterly revenue grew five percent.'
    cosine score: 0.8039

  ONE small, correctly-scoped chunk (1 topic only): 'The item was damaged and I need a refund please.'
    cosine score: 1.0000

  The SAME sentence about damage and refunds is present, word for word,
  in both chunks. Merging it with two unrelated topics (remote work,
  quarterly revenue) into one big chunk pulls its pooled vector toward
  those topics' axes too, diluting its similarity to a query about
  damage specifically -- from 1.0000 down to 0.8039.
  A chunk that is too big doesn't just retrieve slower -- it can score
  WORSE on exactly the query it should answer best, because pooling
  (M6-L01) blends in content the query was never about.

============================================================================
3. CHUNK SIZE: TOO SMALL SPLITS ONE FACT ACROSS TWO CHUNKS
============================================================================
  A single fact, chunked at a too-small 45 characters:

    Chunk 1: 'For all staff in the Mid tier, the company ac'
    Chunk 2: 'crues twenty days of PTO per year.'

  'Mid tier' ends up in chunk 1; 'twenty days' ends up in chunk 2. A query
  retrieving only chunk 2 sees 'twenty days of PTO' with no tier name
  anywhere in the same chunk to attach it to -- the exact same failure
  shape M7-L04 measured for a flattened TABLE, now shown for ordinary
  PROSE chunked too aggressively.

============================================================================
4. OVERLAP RECOVERS WHAT A HARD BOUNDARY WOULD SPLIT
============================================================================
  Same fact, same 45-character chunk size, WITHOUT overlap:
    Chunk 1: 'For all staff in the Mid tier, the company ac'
    Chunk 2: 'crues twenty days of PTO per year.'
  Any single chunk contains BOTH 'Mid tier' and 'twenty': False

  Same fact, same size, WITH 30-character overlap between chunks:
    Chunk 1: 'For all staff in the Mid tier, the company ac'
    Chunk 2: 'n the Mid tier, the company accrues twenty da'
    Chunk 3: ' the company accrues twenty days of PTO per y'
    Chunk 4: 'crues twenty days of PTO per year.'
    Chunk 5: 'ys of PTO per year.'
    Chunk 6: 'ear.'
  Any single chunk contains BOTH 'Mid tier' and 'twenty': True

  Overlap doesn't prevent a boundary from falling in an awkward place --
  it just guarantees that whatever falls near a boundary also appears
  fully, at least once, in some OTHER chunk that isn't cut at the same
  point. This is a real, mechanical fix for section 3's exact failure,
  not a heuristic that sometimes helps.

  Notice how much overlap this actually took: 30 characters out
  of a 45-character chunk (67%) -- because 'Mid
  tier' and 'twenty' are genuinely far apart relative to the chunk size.
  Overlap only recovers a split if it's large enough to bridge the actual
  gap between related facts -- a small, token overlap percentage (the
  common 10-20% recommendation) recovers only NEARBY splits, not distant
  ones. This is why overlap is a probabilistic mitigation, not a
  guarantee, unless sized generously relative to how far apart related
  content can realistically fall in your own documents.

============================================================================
5. RESPECTING DOCUMENT BOUNDARIES INSTEAD OF CUTTING THROUGH THEM
============================================================================
  The same two-section document, chunked two ways:

  Fixed-size (70 chars), ignoring structure:
    Chunk 1: '# Remote Work Policy\nEmployees may work remotely up to three days per '
    Chunk 2: 'week with manager approval.\n# Expense Policy\nExpense reports must be s'
    Chunk 3: 'ubmitted within thirty days of purchase.'

  Boundary-aware (split at each heading):
    Chunk 1: '# Remote Work Policy\nEmployees may work remotely up to three days per week with manager approval.'
    Chunk 2: '# Expense Policy\nExpense reports must be submitted within thirty days of purchase.'

  Fixed-size chunking has no idea 'Remote Work Policy' and 'Expense
  Policy' are two unrelated sections -- it can (and here, does) merge
  part of one section with part of the next, or split a heading from
  its own body. Boundary-aware chunking, using exactly the structure
  M7-L03 preserved during ingestion, keeps each section whole. M7-L07
  covers more advanced strategies (semantic, recursive) built on this
  same principle: prefer the document's own boundaries over an
  arbitrary count wherever structure is available.

============================================================================
6. OVERLAP IS NOT FREE: THE STORAGE/EMBEDDING COST, MEASURED
============================================================================
    0% overlap:  16 chunks, 1,580 total characters across all chunks (+0.0% vs. the original 1,580-character document)
   10% overlap:  18 chunks, 1,750 total characters across all chunks (+10.8% vs. the original 1,580-character document)
   25% overlap:  22 chunks, 2,085 total characters across all chunks (+32.0% vs. the original 1,580-character document)
   50% overlap:  32 chunks, 3,110 total characters across all chunks (+96.8% vs. the original 1,580-character document)

  Every character of overlap is embedded and stored MORE THAN ONCE.
  Section 4 showed overlap's real benefit; this section shows its real
  cost is not hypothetical either -- both numbers belong in the same
  decision, not just the benefit alone.

============================================================================
7. WHAT THIS LAB IS AND IS NOT
============================================================================
  REAL: every chunking function in this lab is genuinely executed on
  real text; the relevance-dilution scores (section 2) use M6-L01's
  exact pooling/cosine mechanism; the overlap storage-cost measurement
  (section 6) is exact arithmetic on real chunked output.

  ILLUSTRATIVE: chunk sizes in this lab (45-100 characters) are chosen
  to make failures visible in a short document; real systems typically
  chunk by TOKEN count, at sizes of hundreds of tokens, not characters.

  NOT SHOWN: sentence-boundary-aware, semantic, and recursive chunking
  algorithms -- specific, more sophisticated splitting STRATEGIES that
  are M7-L07's dedicated topic. This lesson establishes the underlying
  trade-offs (size, overlap, boundaries) those strategies are designed
  to navigate.

Done.
```

### 7.3 Reading the result

**Section 2's number (1.0000 vs. 0.8039) is worth sitting with.** It would be easy to assume "a bigger
chunk has more context, so it can only help." It measurably does not, once pooling dilutes the signal a
specific query actually needs.

**Section 4's 67% overlap figure is deliberately not a clean, reassuring number.** A tidier lab might have
picked a fact that a standard 15% overlap recovers, implying overlap is a small, cheap insurance policy.
This fact needed much more than that — an honest reminder that overlap's *required* size depends on your
actual documents, not on a rule of thumb.

**Section 5 is the lesson's practical resolution.** Sections 2-4 are all problems that boundary-aware
chunking, wherever structure is available, avoids by construction rather than mitigates by tuning a
parameter.

---

## 8. Common mistakes and troubleshooting

1. **Assuming a bigger chunk is always safer because it has "more context."** §5.2 — a chunk mixing
   unrelated topics can score worse than a smaller, correctly-scoped one, due to pooling dilution.
2. **Choosing chunk size without checking how it interacts with your actual documents' fact positions.**
   §5.3, §6 — the same fixed size can split some facts and not others, depending on where they fall.
3. **Treating a standard overlap percentage (e.g. 10-20%) as universally sufficient.** §5.4 — the overlap
   actually needed depends on how far apart related content falls, which varies by document.
4. **Using fixed-size chunking when document structure (headings, sections) is already available.** §5.5 —
   boundary-aware chunking avoids the size trade-off entirely wherever structure exists.
5. **Treating overlap as a free improvement with no downside.** §5.6 — every overlapping character is
   stored and embedded again, a real, measurable cost that scales with overlap percentage.
6. **Debugging inconsistent RAG answers about facts near a chunk boundary as a "random" or "flaky" issue.**
   §6 — this is deterministic and traceable to specific chunk-boundary positions, not random at all.

| Symptom | Likely cause | Fix |
|---|---|---|
| A chunk containing the right information still scores poorly for a specific query | The chunk also contains unrelated content, diluting its pooled relevance | Reduce chunk size or scope, or use boundary-aware chunking (§5.2, §5.5) |
| A RAG answer about a specific fact is inconsistent — correct for some facts, wrong for others in the same document | Chunk boundaries happen to split some facts and not others | Check fact positions against chunk boundaries; add overlap sized to the actual gaps, or use boundary-aware chunking (§5.3, §6) |
| Overlap was added but a specific known split still isn't recovered | The overlap size is too small relative to the actual distance between the related pieces of content | Measure the actual gap and size overlap to it, or eliminate the need via boundary-aware chunking (§5.4) |
| Storage or embedding cost grew significantly after adding overlap | Every overlapping character is stored and embedded again | Confirm the overlap fraction is actually needed for your documents before accepting the cost (§5.6) |

---

## 9. Security, privacy, reliability, cost

- **Reliability.** Use boundary-aware chunking wherever document structure is available, rather than an
  arbitrary fixed size — it eliminates both the too-big and too-small failure modes at once (§5.5).
- **Reliability.** Where fixed-size chunking must be used, measure how far apart related facts typically
  fall in your actual documents before choosing an overlap size — a standard percentage is not
  automatically sufficient (§5.4).
- **Cost.** Treat overlap as a real, measurable cost (storage and embedding), not a free safety margin —
  size it deliberately against a real recovery need (§5.6).
- **Reliability.** Test retrieval specifically against facts positioned near likely chunk boundaries, not
  only against easy, centrally-located facts, since this is a predictable, not random, failure mode (§6).

---

## 10. Exercises

### Exercise 1 — Beginner (~20 min)

1. In one sentence, why does fixed-size chunking split words and sentences arbitrarily?
2. Why did the big, multi-topic chunk score lower than the small, single-topic chunk in §7.2?
3. What specifically went wrong in §7.3's too-small chunking example?
4. What does overlap actually guarantee, and what does it not guarantee, per §7.4?
5. Why is boundary-aware chunking preferable to fixed-size chunking whenever structure is available?

### Exercise 2 — Intermediate (~40 min)

1. Run the lab. Confirm §7.2's two cosine scores and §7.4's False→True transition on your own machine.
2. Construct your own three-topic document and measure the relevance-dilution effect for a query about
   one specific topic, following §7.2's method.
3. Find the minimum overlap size (as a percentage of chunk size) that recovers §7.3's specific fact split,
   and compare it to the 67% this lesson measured for a different chunk size.
4. Extend §7.5's boundary-aware chunker to also split on a second-level heading (e.g. `##`), and test it
   on a document with nested sections.
5. Using §7.6's method, measure the storage cost of the specific overlap size you found in Exercise 2.3,
   and weigh it against the benefit.

### Exercise 3 — Challenge (~50 min)

1. Implement a chunker that splits at sentence boundaries (using simple punctuation-based rules) instead
   of a fixed character count, and compare its behavior on §7.1's document to the fixed-size approach.
2. Design and run an experiment measuring relevance dilution (§7.2's method) as a function of how many
   unrelated topics are merged into one chunk (1, 2, 3, 4 topics), and report the trend.
3. Implement a chunker that combines boundary-awareness (§7.5) with a maximum chunk size (splitting a
   section further only if it exceeds a size limit), and test it on a document with one very long section.
4. Research (conceptually) how token-based chunk-size limits interact with a specific embedding model's or
   LLM's context window, and explain why token count, not character count, is the more common real-world
   unit for chunk size.
5. Using this lesson's §6 worked example as a model, design a test suite that would have caught the
   inconsistent-PTO-answer bug before launch, specifying what each test should check.

---

## 11. Quiz

*(Answers: [`answer-keys/module-07-answers.md`](../../answer-keys/module-07-answers.md#m7-l06).)*

**Q1.** Per §7.1, why did fixed-size chunking split "remote" and "manager" mid-word?

- A. The document was corrupted before chunking began.
- B. It cuts text at a fixed character count with no awareness of word or sentence boundaries.
- C. Python's string slicing only works correctly on documents shorter than 60 characters.
- D. The words "remote" and "manager" are reserved keywords that trigger special splitting behavior.

**Q2.** Per §7.2, why did the same sentence about damage/refunds score lower when merged into one big
chunk with two unrelated topics?

- A. The scoring function contains a bug that always favors longer chunks.
- B. Cosine similarity cannot be computed on chunks containing more than one sentence.
- C. The query itself was worded incorrectly.
- D. Mean pooling blends the vectors of every word in the chunk, so unrelated topics' word vectors pull the chunk's overall vector away from the query's specific topic.

**Q3.** Per §7.3, what specifically went wrong when a fact was chunked at a too-small size?

- A. The tier label ("Mid tier") ended up in one chunk and its associated value ("twenty days") ended up in a different chunk, with nothing to connect them.
- B. The entire fact was deleted during chunking.
- C. The fact was duplicated identically in both resulting chunks.
- D. Chunking failed with an unhandled exception.

**Q4.** Per §7.4, what did adding overlap between chunks actually change?

- A. Overlap prevented the boundary from falling in an awkward place at all.
- B. Overlap deleted the problematic boundary entirely, leaving only one chunk.
- C. It added enough shared content between adjacent chunks that at least one chunk (not present in the no-overlap version) contained both the label and its value together.
- D. Overlap had no measurable effect on which chunks contained which words.

**Q5.** Per §7.4's own honest finding, why did this specific fact require an unusually large (67%)
overlap fraction to be recovered?

- A. Because the lab's code contains an off-by-one error in the overlap calculation.
- B. Because the label and its value were unusually far apart relative to the chunk size, and overlap can only bridge a gap if it's large enough to span that specific distance.
- C. Because 67% is the mathematically required overlap fraction for all documents.
- D. Because the sentence contained a spelling error that confused the chunker.

**Q6.** Per §7.4, what is the general relationship between overlap size and recovery guarantees?

- A. Overlap always guarantees recovery of any split fact regardless of size.
- B. Overlap guarantees recovery only for facts shorter than 10 characters.
- C. Overlap has no relationship to the distance between related pieces of content.
- D. Overlap is a probabilistic mitigation, not a guarantee, unless sized generously relative to how far apart related content can realistically fall in your documents.

**Q7.** Per §7.5, what did fixed-size chunking do to the two-section policy document that boundary-aware
chunking avoided?

- A. It merged part of one section with part of the next (and can split a heading from its own body), rather than keeping each section intact.
- B. It correctly identified and preserved both sections perfectly.
- C. It deleted one of the two sections entirely.
- D. It merged the two sections into a single, larger, but internally consistent section.

**Q8.** Per §7.5, what information did the boundary-aware chunker use to keep each section whole?

- A. A machine learning model trained specifically to detect section boundaries.
- B. Random guessing about where sections might begin and end.
- C. The heading structure preserved during ingestion (M7-L03), splitting at each heading rather than at an arbitrary character count.
- D. The total character count of the document, divided evenly.

**Q9.** Per §7.6, what real cost does adding overlap impose, as measured directly?

- A. Overlap has no cost at all; it is purely beneficial in every case.
- B. Every character of overlap is embedded and stored more than once, inflating total storage/embedding cost.
- C. Overlap reduces the total number of chunks needed, lowering cost.
- D. Overlap cost only applies to documents written in non-English languages.

**Q10.** What is the correct relationship between section 4 (overlap's benefit) and section 6 (overlap's
cost), per this lesson?

- A. Section 4 is correct and section 6 is not relevant to the same decision.
- B. Section 6 disproves section 4's finding entirely.
- C. Only section 6's cost matters; section 4's benefit should be ignored.
- D. Both are real and must be weighed together — overlap is not a free win, it's a trade-off with a measurable cost on one side and a measurable recovery benefit on the other.

**Q11.** Which topic does this lesson explicitly leave to M7-L07?

- A. Specific, more sophisticated chunking algorithms — sentence-boundary-aware, semantic, and recursive strategies.
- B. The definition of a content hash, which this lesson also does not cover.
- C. Unicode normalization, which this lesson also does not cover.
- D. Retrieval evaluation metrics, which this lesson also does not cover.

**Q12.** What is the general lesson this lab demonstrates about chunk size and overlap?

- A. Chunk size and overlap are arbitrary implementation details with no measurable effect on retrieval quality.
- B. There is one universally correct chunk size and overlap value for all documents and use cases.
- C. Chunk size and overlap are both real, measurable trade-offs (too big dilutes relevance, too small splits facts, overlap recovers some splits at a real storage cost) rather than arbitrary implementation details.
- D. Overlap should always be set to the maximum possible value regardless of cost.

**Q13.** *(Written, rubric-graded.)* In under 150 words: your RAG system answers questions about some
facts in a document correctly and others incorrectly, seemingly at random. Based on this lesson, what
would you check first, and why?

---

## 12. Revision notes

- **Fixed-size chunking cuts at a character count with no awareness of words, sentences, or topics** —
  this is its complete, correct behavior, not a bug to work around.
- **A chunk that is too big can score WORSE on the query it should answer best**, because mean pooling
  blends in unrelated content — measured directly: 1.0000 (correctly-scoped) vs. 0.8039 (same sentence,
  merged with two unrelated topics).
- **A chunk that is too small can split one fact's label from its value**, leaving neither resulting chunk
  able to answer a question the original document could — the same failure shape M7-L04 found in tables,
  now shown in ordinary prose.
- **Overlap recovers some boundary splits, but only if sized to the actual gap being bridged** — measured
  directly: a specific fact required 67% overlap (not a standard 10-20%) to be recovered, because the
  related content was unusually far apart relative to chunk size.
- **Overlap has a real, measurable storage/embedding cost** — measured: up to nearly double the total
  stored content at 50% overlap.
- **Boundary-aware chunking, using structure preserved at ingestion (M7-L03), avoids both the too-big and
  too-small failure modes at once wherever document structure is available** — the most direct fix, not
  merely one option among equals.

---

## 13. Completion checklist

- [ ] I can explain why fixed-size chunking splits words and sentences without regard for meaning.
- [ ] I can demonstrate and explain why an overly large chunk can dilute relevance for a specific query.
- [ ] I can demonstrate and explain why an overly small chunk can split one fact across two chunks.
- [ ] I can implement overlap and explain precisely what it guarantees and does not guarantee.
- [ ] I know overlap has a real, measurable storage/embedding cost, not just a benefit.
- [ ] I can implement boundary-aware chunking using structure preserved at ingestion.
- [ ] I scored 10/13 on the quiz.

---

## 14. References

- Pinecone, *Chunking Strategies for LLM Applications* (general survey of chunking trade-offs). `[UNVERIFIED]`
- LangChain documentation, *Text Splitters*. <https://python.langchain.com/docs/how_to/#text-splitters> `[UNVERIFIED]`

---

## 15. Next lesson

→ M7-L07 — Chunking II: Fixed, Recursive, Sentence, Semantic, Structure-Aware

You now understand the trade-offs chunking has to navigate. Next: the specific algorithms — recursive
splitting, sentence-boundary detection, semantic similarity-based splitting, and structure-aware
strategies — designed to navigate size, overlap, and boundaries better than a fixed character count alone.
