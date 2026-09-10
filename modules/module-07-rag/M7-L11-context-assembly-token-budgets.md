# M7-L11 — Context Assembly and Token Budgets

| | |
|---|---|
| **Lesson ID** | M7-L11 |
| **Difficulty** | 2 (Intermediate) |
| **Estimated study time** | 2.0 hours |
| **Prerequisites** | M5-L11 |

---

## 1. Learning objectives

1. **Compute** how much of a total context window is actually available for retrieved chunks, after
   accounting for the system prompt, conversation history, and reserved output space.
2. **Compare** two truncation strategies for when reranked chunks exceed budget, and explain the real
   trade-off between them.
3. **Explain** why chunk order within an assembled context is not an afterthought, citing the "lost in the
   middle" effect as a documented (though model-specific) consideration.
4. **Deduplicate** near-identical retrieved chunks at assembly time, even when corpus-level deduplication
   has already run.
5. **Assemble** a complete, citable context block from reranked chunks under a real token budget.

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **Retrieval budget** | The portion of a context window actually available for retrieved chunks, after subtracting the system prompt, conversation history, and reserved output space. |
| **Drop-from-bottom truncation** | Keeping the highest-ranked chunks whole and discarding lower-ranked ones entirely when budget is exceeded. |
| **Proportional truncation** | Shortening every candidate chunk by the same proportion so all are represented, none complete. |
| **Lost in the middle** | A documented tendency for some models to use information less reliably when it sits in the middle of a long context, versus near the beginning or end. |
| **Assembly-time deduplication** | Removing near-identical chunks from the specific set retrieved for a given query, even when the source corpus has already been deduplicated (M7-L05). |

---

## 3. Plain-language explanation

### 3.1 M7-L10 finished the reranked list; this lesson finishes the prompt

Every lab since M7-L01 has treated "put the retrieved chunks in the prompt" as a simple concatenation. This
lesson is where that step gets the same rigor M5-L11 already applied to context engineering generally —
now aimed specifically at the retrieval-to-generation handoff.

### 3.2 The budget is what's left, not what's available

§7.1 makes concrete something easy to forget: retrieved context does not get the whole context window. It
gets whatever remains after the system prompt, conversation history, and reserved output space are
subtracted — often much less than the total window size suggests.

### 3.3 When chunks don't fit, something has to give

§7.2 compares two honest strategies for the same problem — reranked chunks whose total size exceeds the
budget — and shows neither is free: one guarantees completeness at the cost of coverage, the other
guarantees coverage at the cost of completeness, with a real risk M7-L06 already measured for chunking
itself now showing up again at assembly time.

### 3.4 Where you put things in the context can matter as much as what you put there

§7.3 covers a real, documented (if model-specific) phenomenon: content buried in the middle of a long
context can be used less reliably than content near either end — a consideration this lesson is honest
about not being able to measure directly, without inflating its practical importance.

### 3.5 Retrieval can still hand you near-duplicates

§7.4 shows that even a fully deduplicated corpus (M7-L05) can produce redundant retrieved chunks for a
specific query — most often from overlapping chunk windows (M7-L06) — and that catching this at assembly
time frees real budget for genuinely different content.

---

## 4. Analogy

**Packing a small suitcase for a trip, with items already sorted by priority.** The suitcase (context
window) doesn't only hold clothes (retrieved chunks) — it also has to fit toiletries (system prompt), gifts
you're already carrying (conversation history), and room left over so you can still close it and get
through security (reserved output). If everything you want doesn't fit, you can either pack fewer items
completely, or try to pack everything by squeezing each one — folding a coat so tightly it's unusable when
you arrive. And packing two nearly-identical shirts wastes space you could have used for something you
don't already have one of.

### Where the analogy breaks

- **A suitcase's items don't need to be read in a particular order to be useful.** §7.3's positional
  effect has no everyday-packing equivalent — it is specific to how some models attend across a long
  context.
- **A traveler can usually tell two shirts are near-identical at a glance.** §7.4's near-duplicate
  detection needs an explicit similarity check (Jaccard/shingling) precisely because two differently-worded
  chunks describing the same fact don't look identical at the text level.

---

## 5. Detailed technical explanation

### 5.1 The retrieval budget, computed

`[REAL]` §7.1 computed a retrieval budget of 6,200 tokens from a stated 8,000-token context window, after
subtracting 300 (system prompt), 500 (conversation history), and 1,000 (reserved output). **This is
M5-L11's own context-engineering discipline**, applied specifically to the slot retrieved chunks occupy —
never the full window, always whatever remains after every other consumer of that window is accounted for.

### 5.2 Two truncation strategies, measured

`[REAL, measured]` §7.2 took 5 reranked chunks totaling 220 estimated tokens against a deliberately tight
60-token budget. **Drop-from-bottom** kept only the single highest-ranked chunk, complete and coherent, at
48 tokens. **Proportional truncation** kept all 5 chunks, each cut to roughly 13 tokens and ending mid
sentence. **Neither is free**: drop-from-bottom discards four chunks' worth of information entirely;
proportional truncation risks the exact chunk-boundary failure M7-L06 measured for chunking itself —
severing a label from its value, or a fact from its qualifying detail, mid-cut. **The right choice depends
on the task**: a question with one precise answer likely needs a complete chunk (favor drop-from-bottom); a
task needing breadth across many partial signals may tolerate incompleteness better (favor proportional).

### 5.3 Order within the window, honestly framed

`[CONCEPTUAL, UNVERIFIED]` §7.3 does not run a real LLM call, and says so explicitly. It reports a
documented phenomenon — content in the middle of a long context sometimes used less reliably than content
near the beginning or end — as something to verify against your own model and task, not as a measured
result of this lab. **The actionable implication, if it applies**: preserve rank order when assembling
chunks, with the most relevant chunk placed first or last, not buried in an arbitrary middle position.

### 5.4 Assembly-time deduplication, measured

`[REAL, measured]` §7.4 computed Jaccard similarity (M7-L05's exact shingling method) between two
retrieved PTO chunks describing the same fact in slightly different words: **0.524, above a 0.5
threshold** — correctly flagged as near-duplicates, with one of the two dropped, freeing roughly 25 tokens.
A genuinely different chunk (parental leave) scored **0.000** against the same reference and was correctly
kept. **This catches redundancy M7-L05's corpus-level deduplication cannot**, because the redundancy here
arises from retrieval and chunking (overlapping windows, M7-L06) at query time, not from duplicate source
documents.

### 5.5 The assembled artifact

`[REAL]` §7.5 assembled the final context block: the retained chunk (from §5.2's drop-from-bottom
strategy), each prefixed with its source URI (M7-L08's provenance metadata) — 51 tokens, within the
60-token budget, and structured so M7-L12's citation step has exactly what it needs already attached.

### 5.6 Assumptions and limitations

- Section 1's context window and reserved-token amounts are round, illustrative numbers, not a specific
  real model's actual limits.
- Section 3's "lost in the middle" effect is reported from published, general research on some language
  models; it is model- and version-specific and was not measured in this lab.
- This lesson does not cover summarizing chunks that don't fit budget (as opposed to truncating or
  dropping them) — that is M5-L11's own topic, applicable here directly.

---

## 6. Worked example — the assembled context that quietly dropped the actual answer

**The system.** A support-ticket assistant retrieves and reranks the top 8 candidate chunks for each
query, then concatenates all 8 into the context, regardless of total size, relying on the model's large
context window to "just handle it."

**What went wrong.** For a subset of queries, the correct, highest-ranked chunk was present in the
assembled context, but positioned in the middle of a long, 8-chunk block — and the model's answers for
these specific queries were noticeably less reliable than for queries where the same chunk happened to
rank in a position placed near the start or end of the assembled text.

**Why the team didn't suspect assembly order at first.** Per M7-L01 §6's discipline, the team correctly
checked retrieval first — and confirmed the right chunk WAS being retrieved and reranked correctly every
time. The bug was neither a retrieval nor a reranking failure; it was in how the already-correct chunks
were subsequently arranged into the prompt.

**Three defects:**

| # | Defect | Consequence |
|---|---|---|
| 1 | All reranked chunks were concatenated in a fixed order unrelated to their actual position-sensitivity | The single most relevant chunk could land anywhere, including the middle of a long context |
| 2 | No token budget was actually enforced — "the model's context window is big enough" was treated as sufficient | Assembled contexts grew arbitrarily large with no accounting for what belonged in that space |
| 3 | Retrieved chunks were never checked for redundancy at assembly time | Budget was spent on near-duplicate content instead of on ordering the genuinely relevant chunk favorably |

### The fix

**Enforce an explicit retrieval budget**, per §5.1 — decide deliberately what belongs in that space rather
than assuming a large window makes the question moot.

**Place the highest-ranked chunk first or last in the assembled context**, per §5.3, as a low-cost
mitigation for the documented (if model-specific) positional effect.

**Deduplicate the retrieved set at assembly time**, per §5.4, freeing budget that a fixed-size,
redundancy-blind concatenation would otherwise waste.

**The general rule.** **A correct retrieval and reranking result can still be undermined by how it's
assembled into the final context — order and budget management are a distinct source of failure, not a
detail retrieval quality automatically takes care of.**

---

## 7. Practical activity

**File:** [`labs/m7/l11_context_assembly_token_budgets.py`](../../labs/m7/l11_context_assembly_token_budgets.py)

**No API key, no network, no third-party dependencies.** Runs in well under a second.

```bash
source .venv/bin/activate
python labs/m7/l11_context_assembly_token_budgets.py
```

### 7.2 Expected output

`[EXECUTED]` — 2026-09-10, Python 3.10.11 (pure standard library).

```text
============================================================================
1. THE RETRIEVAL CONTEXT BUDGET IS WHAT'S LEFT OVER, NOT THE WHOLE WINDOW
============================================================================
  Total context window:          8,000 tokens
  - System prompt:                 300 tokens
  - Conversation history:          500 tokens
  - Reserved for model output:   1,000 tokens
  =============================================
  = Budget actually available for retrieved context: 6,200 tokens

  This is M5-L11's context-engineering discipline, applied specifically
  to the retrieval slot: the context window is not one pool available
  to retrieved chunks -- it is shared with the system prompt, whatever
  conversation history is being carried (M7-L09's rewriting target),
  and space reserved so the model can actually finish its answer.

============================================================================
2. WHEN RERANKED CHUNKS EXCEED BUDGET: TWO STRATEGIES, MEASURED
============================================================================
  5 reranked chunks, most relevant first, estimated token counts:
    P3#1 (48 tok): 'Full time employees accrue fifteen days of PTO per year, increasing to'...
    P3#0 (44 tok): 'Paid Time Off Policy applies to all full time employees hired before t'...
    P5#1 (46 tok): 'Employees are eligible for twelve weeks of paid parental leave followi'...
    P1#0 (39 tok): 'Remote Work Policy allows employees to work remotely up to three days '...
    P4#0 (43 tok): 'Referral Bonus Policy pays employees a two thousand dollar bonus for a'...

  Total: 220 tokens vs. a budget of 60 tokens for this example (deliberately tight to force the trade-off).

  STRATEGY A -- drop from the bottom (keep highest-ranked chunks whole, drop the rest):
    P3#1 (complete, 48 tok): 'Full time employees accrue fifteen days of PTO per year, increasing to twenty days after three years of service, based on continuous employment without any unpaid leave gaps exceeding thirty consecutive days in a given calendar year.'
  Kept 1 of 5 chunks, each FULLY intact.

  STRATEGY B -- truncate every chunk proportionally (keep all 5, each shortened):
    P3#1 (partial, 13 tok): 'Full time employees accrue fifteen days of PTO per [...]'
    P3#0 (partial, 13 tok): 'Paid Time Off Policy applies to all full time [...]'
    P5#1 (partial, 13 tok): 'Employees are eligible for twelve weeks of paid parental [...]'
    P1#0 (partial, 13 tok): 'Remote Work Policy allows employees to work remotely up [...]'
    P4#0 (partial, 13 tok): 'Referral Bonus Policy pays employees a two thousand dollar [...]'
  Kept all 5 chunks, each CUT OFF mid-sentence.

  Strategy A guarantees every included chunk is complete and internally
  coherent, at the cost of dropping lower-ranked information entirely.
  Strategy B guarantees every chunk contributes SOMETHING, at the cost
  of each contribution being incomplete -- and, per M7-L06's own
  measured finding, an arbitrary mid-sentence or mid-fact cut can sever
  a label from its value just as easily inside a context-assembly
  truncation as inside chunking itself. Neither strategy is free; the
  right choice depends on whether partial information or missing
  information is more useful for the task at hand.

============================================================================
3. ORDER WITHIN THE CONTEXT WINDOW IS NOT AN AFTERTHOUGHT
============================================================================
  `[CONCEPTUAL -- not measured in this lab, which makes no real LLM call]`
  Published research on long-context LLM behavior has reported a
  'lost in the middle' effect: information placed in the MIDDLE of a
  long context is sometimes used less reliably by a model than
  information placed near the BEGINNING or END of the same context,
  even when all of it is technically present. `[UNVERIFIED -- this is
  model- and version-specific; verify against your own model and task
  before relying on it.]`

  If this effect applies to your model, the practical implication is
  direct: place the highest-reranked (most likely to matter) chunk at
  the START or END of the assembled context, not buried in an arbitrary
  middle position -- simply preserving M7-L10's rank order when
  concatenating chunks already does this correctly, provided the most
  relevant chunk is placed first (or last), not in the middle of the list.

============================================================================
4. DEDUPLICATING NEAR-IDENTICAL RETRIEVED CHUNKS AT ASSEMBLY TIME
============================================================================
  Retrieved chunks can overlap even after corpus-level dedup (M7-L05) --
  e.g. two chunks from OVERLAPPING windows (M7-L06) covering the same fact:

    P3#1a: 'Full time employees accrue fifteen days of PTO per year, increasing to twenty days after three years of service.'
    P3#1b: 'Full time employees accrue fifteen days of PTO each year, increasing to twenty days after three years of tenure.'
    P5#1: 'Employees are eligible for twelve weeks of paid parental leave following the birth or adoption of a child.'

  Jaccard(P3#1a, P3#1b) = 0.524  (near-duplicate PTO chunks)
  Jaccard(P3#1a, P5#1)  = 0.000  (genuinely different topic)

  After assembly-time dedup (threshold 0.5, M7-L05's shingling method): ['P3#1a', 'P5#1'] kept, ['P3#1b'] dropped as redundant.
  Roughly 25 tokens of budget freed up -- enough, in section 2's tight
  budget, to include an additional, genuinely different chunk instead of
  a second near-copy of information already present.

============================================================================
5. THE FINAL ASSEMBLED CONTEXT BLOCK, WITH CITATIONS METADATA
============================================================================
  The actual context block assembled for the model (M7-L08's provenance
  metadata attached per chunk, ready for M7-L12's citation step):

[Source: hr-portal://policies/pto-policy#v2]
Full time employees accrue fifteen days of PTO per year, increasing to twenty days after three years of service, based on continuous employment without any unpaid leave gaps exceeding thirty consecutive days in a given calendar year.

  Final assembled size: 51 tokens (budget was 60).

============================================================================
6. WHAT THIS LAB IS AND IS NOT
============================================================================
  REAL: token estimates use M7-L02's own stated word-to-token ratio,
  applied consistently; both truncation strategies and the assembly-
  time deduplication are genuinely computed, not scripted; the near-
  duplicate Jaccard scores use M7-L05's exact shingling method.

  ILLUSTRATIVE / CONCEPTUAL: the total context window and reserved
  token amounts in section 1 are round, chosen numbers, not a specific
  real model's limits. Section 3's 'lost in the middle' effect is
  reported as published, general research, not measured in this lab,
  which makes no real LLM call at all.

  NOT SHOWN: summarizing (rather than truncating or dropping) chunks
  that don't fit budget, which is M5-L11's own topic applied here; and
  how the assembled context block's citations get verified against the
  model's actual generated answer, which is M7-L12's topic next.

Done.
```

### 7.3 Reading the result

**Section 2's contrast is deliberately extreme (1 complete chunk vs. 5 mangled ones) to make the trade-off
undeniable.** A more generous budget would blur this distinction; the tight 60-token budget makes both
strategies' costs fully visible in one short output.

**Section 3 is the one section in this lesson that stays honest about its limits.** It would have been easy
to state the "lost in the middle" effect as settled fact — labeling it conceptual and model-specific, while
still explaining its practical implication, is the more defensible position for a lab that makes no real
model call at all.

**Section 4's freed-up 25 tokens connects directly back to section 2's tight budget** — in a system this
constrained, deduplication isn't a minor optimization, it's the difference between fitting one more
genuinely useful chunk or not.

---

## 8. Common mistakes and troubleshooting

1. **Assuming the full context window is available for retrieved chunks.** §5.1 — the system prompt,
   conversation history, and reserved output all compete for the same space.
2. **Truncating every candidate chunk proportionally without considering task shape.** §5.2 — this risks
   the same mid-fact split M7-L06 measured for chunking, now at assembly time.
3. **Assuming a model uses every part of a long context equally reliably.** §5.3 — treat this as a
   documented, model-specific risk to verify, not a settled universal fact, but don't ignore it either.
4. **Trusting corpus-level deduplication (M7-L05) to prevent all redundancy in retrieved results.** §5.4 —
   overlapping chunk windows can still produce near-duplicate retrieved chunks at query time.
5. **Concatenating chunks with no attached provenance metadata.** §5.5 — this leaves M7-L12's citation
   step with nothing to cite back to.
6. **Relying on "the context window is big enough" instead of enforcing an explicit budget.** §6 — this
   defers, rather than solves, the assembly decisions this lesson covers.

| Symptom | Likely cause | Fix |
|---|---|---|
| Model answers seem to ignore or underuse some retrieved information despite it being in the context | The relevant chunk may be positioned in the middle of a long assembled context | Place the highest-ranked chunk near the start or end of the assembled context (§5.3) |
| Assembled context regularly exceeds available budget | No explicit retrieval budget was computed or enforced | Compute the actual remaining budget after system prompt, history, and output reservation (§5.1) |
| Retrieved results feel redundant even though the corpus was deduplicated | Overlapping chunk windows or differently-worded chunks describe the same fact | Deduplicate the retrieved set at assembly time using shingling/Jaccard similarity (§5.4) |
| Generated answers cannot be traced back to a specific source | The assembled context lacks provenance metadata per chunk | Attach source/version metadata to each chunk before assembly (§5.5, building on M7-L08) |

---

## 9. Security, privacy, reliability, cost

- **Reliability.** Compute and enforce an explicit retrieval budget rather than assuming a large context
  window makes budgeting unnecessary (§5.1).
- **Reliability.** Choose a truncation strategy (drop-from-bottom vs. proportional) deliberately, based on
  whether the task needs complete information from fewer sources or partial information from more (§5.2).
- **Reliability.** Place the most relevant chunk near the start or end of the assembled context as a
  low-cost mitigation for the documented "lost in the middle" effect (§5.3).
- **Cost.** Deduplicate retrieved chunks at assembly time — redundant near-duplicate content wastes budget
  that could hold genuinely different information (§5.4).

---

## 10. Exercises

### Exercise 1 — Beginner (~20 min)

1. In one sentence, why is the retrieval budget smaller than the total context window?
2. What does "drop from the bottom" preserve that "truncate proportionally" does not, and vice versa?
3. Why is the "lost in the middle" effect discussed as conceptual rather than measured in this lab?
4. Why can retrieved chunks be near-duplicates even after corpus-level deduplication?
5. What does the final assembled context block include beyond the chunk text itself?

### Exercise 2 — Intermediate (~40 min)

1. Run the lab. Confirm §7.2's truncation results and §7.4's Jaccard scores on your own machine.
2. Recompute §7.1's retrieval budget for a different total context window and reserved-token allocation of
   your choice.
3. Design a third truncation strategy (e.g. drop from the bottom until one chunk remains, then truncate
   that one to fit exactly) and compare its output to both strategies in this lesson.
4. Construct a new pair of near-duplicate chunks (your own topic) and find the shingle size and threshold
   that correctly flags them as redundant.
5. Using §7.5's method, assemble a context block from three chunks with different source URIs, and write
   out the exact citation-ready format.

### Exercise 3 — Challenge (~50 min)

1. Implement a context assembler that tries drop-from-bottom first, and falls back to proportional
   truncation only for the lowest-ranked chunk that doesn't fully fit, combining both strategies.
2. Design and implement an assembly-time deduplication step that considers ALL pairs in a retrieved set
   (not just sequential ones), clustering near-duplicates before selecting one representative per cluster.
3. Research (conceptually) the "lost in the middle" phenomenon in published LLM literature, and summarize
   what conditions it was reported under (context length, task type, model family).
4. Design an experiment (conceptually, since this lab makes no real model call) that would test whether
   your own model exhibits a positional effect, specifying what you would measure and how.
5. Using this lesson's §6 worked example as a model, design a context-assembly test suite that would catch
   budget overruns, redundant chunks, and poor chunk ordering before they reach production.

---

## 11. Quiz

*(Answers: [`answer-keys/module-07-answers.md`](../../answer-keys/module-07-answers.md#m7-l11).)*

**Q1.** Per §7.1, why is the token budget available for retrieved context smaller than the total context
window?

- A. The total context window is always exactly zero tokens for any real model.
- B. Retrieved chunks are not allowed to use more than 100 tokens under any circumstances.
- C. Token budgets do not actually exist in real language models.
- D. The total window is shared with the system prompt, conversation history, and space reserved for the model's output, and the retrieval budget is only what's left after those are subtracted.

**Q2.** Per §7.2, what did "drop from the bottom" preserve that "truncate proportionally" did not?

- A. Neither strategy preserves any information at all.
- B. Complete, internally coherent chunks (though fewer of them), versus all chunks present but each cut off mid-sentence.
- C. Exactly the same result as the other strategy, with no meaningful difference.
- D. A guarantee that every chunk in the corpus is included regardless of budget.

**Q3.** Per §7.2, what real risk does the "truncate proportionally" strategy share with M7-L06's own
finding?

- A. An arbitrary cut can sever a label from its value (or cut mid-sentence/mid-fact) just as easily during context-assembly truncation as during chunking itself.
- B. Truncation always improves the clarity of every chunk it is applied to.
- C. This risk applies only to chunks written in languages other than English.
- D. M7-L06 found no risk at all associated with arbitrary text splitting.

**Q4.** Per §7.2, is one truncation strategy universally correct?

- A. Yes, "drop from the bottom" is always the objectively correct choice in every situation.
- B. Yes, "truncate proportionally" is always the objectively correct choice in every situation.
- C. No — the right choice depends on whether partial information across many chunks or complete information from fewer chunks is more useful for the specific task.
- D. Neither strategy can ever be implemented in a real system.

**Q5.** Per §7.3, what is the "lost in the middle" effect, as described in this lesson?

- A. A guarantee that models always ignore the first and last parts of any context.
- B. A technique for compressing a context window to half its original size.
- C. A bug specific to one particular vendor's language model that has since been fixed everywhere.
- D. Published research reporting that information placed in the middle of a long context can be used less reliably by a model than information near the beginning or end, even when technically present.

**Q6.** Per §7.3, why is the "lost in the middle" discussion explicitly labeled conceptual/unverified
rather than measured?

- A. Because the effect has been definitively proven false by this lesson's own lab.
- B. Because this lab makes no real LLM call, so the effect is reported from published research, not demonstrated directly.
- C. Because the effect only applies to context windows smaller than 100 tokens.
- D. Because measuring it would require a network connection this lab deliberately avoids for unrelated reasons.

**Q7.** Per §7.4, why can retrieved chunks be near-duplicates even after M7-L05's corpus-level
deduplication?

- A. Overlapping chunk windows (M7-L06) or differently-worded chunks describing the same fact can still be highly similar at query time, even when no two documents in the corpus are exact duplicates.
- B. M7-L05's deduplication only ever runs on documents, never on chunks, by definition.
- C. Retrieved chunks are always identical to each other regardless of any deduplication step.
- D. Query-time retrieval always introduces duplicate chunks intentionally, by design.

**Q8.** Per §7.4's measured result, what happened to the near-duplicate PTO chunk pair at the chosen
threshold?

- A. Both chunks were kept, since near-duplicates are always preserved regardless of threshold.
- B. Both chunks were dropped, leaving no PTO information in the final context at all.
- C. The near-duplicate pair scored above the 0.5 threshold (0.524) and one of the two was correctly dropped as redundant, freeing budget for other content.
- D. The threshold had no effect on which chunks were kept or dropped.

**Q9.** Per §7.5, what does the final assembled context block include beyond the retrieved chunk text
itself?

- A. A complete copy of the entire original source document for every chunk.
- B. A randomly generated identifier with no connection to the chunk's actual source.
- C. The full conversation history repeated for each individual chunk.
- D. Provenance/source metadata (M7-L08) attached per chunk, ready to support citations in the generated answer.

**Q10.** Which topic does this lesson explicitly leave to M5-L11, applied here rather than newly
introduced?

- A. Token budget accounting, which this lesson covers directly instead.
- B. Summarizing (rather than truncating or dropping) chunks that don't fit the budget.
- C. Assembly-time deduplication, which this lesson covers directly instead.
- D. Context window ordering, which this lesson covers directly instead.

**Q11.** Which topic does this lesson explicitly leave to M7-L12?

- A. How the assembled context block's citations get verified against the model's actual generated answer.
- B. Token budget accounting, which this lesson covers directly instead.
- C. Truncation strategies, which this lesson covers directly instead.
- D. The "lost in the middle" effect, which this lesson covers directly instead.

**Q12.** What is the general lesson this lab demonstrates about context assembly?

- A. Context assembly is a trivial concatenation step with no real trade-offs to consider.
- B. Retrieval and reranking are the only stages of a RAG pipeline that involve any meaningful trade-offs.
- C. Assembling retrieved chunks into a context window involves real, measurable trade-offs (budget accounting, truncation strategy, ordering, deduplication) that are as consequential as the retrieval and reranking stages that produced the chunks in the first place.
- D. Context assembly should always be skipped entirely in a production RAG system.

**Q13.** *(Written, rubric-graded.)* In under 150 words: your team retrieves and reranks chunks correctly,
but final answer quality is inconsistent for queries where the correct chunk lands in different positions
within a long assembled context. Based on this lesson, what would you check and what would you change?

---

## 12. Revision notes

- **The retrieval budget is what remains after the system prompt, conversation history, and reserved
  output are subtracted from the total context window** — measured: an 8,000-token window left only 6,200
  tokens for retrieved content.
- **When reranked chunks exceed budget, drop-from-bottom preserves complete chunks at the cost of coverage;
  proportional truncation preserves coverage at the cost of completeness (and risks the same mid-fact
  split M7-L06 measured for chunking)** — neither is universally correct.
- **Chunk order within the assembled context may matter** — a documented, model-specific "lost in the
  middle" effect suggests placing the most relevant chunk near the start or end, though this lesson
  reports it honestly as unmeasured here.
- **Retrieved chunks can be near-duplicates even after corpus-level deduplication**, due to overlapping
  chunk windows or differently-worded restatements of the same fact — measured directly: a near-duplicate
  pair scored 0.524 on M7-L05's shingling method and one was correctly dropped, freeing real budget.
- **The final assembled context block should carry provenance metadata (M7-L08) per chunk**, so the
  citation step (M7-L12) has what it needs already attached.
- **Context assembly is its own source of failure, distinct from retrieval and reranking quality** — a
  correctly retrieved and reranked chunk can still be undermined by poor budget management or ordering.

---

## 13. Completion checklist

- [ ] I can compute the actual retrieval budget available within a total context window.
- [ ] I can compare drop-from-bottom and proportional truncation and choose appropriately for a given task.
- [ ] I can explain the "lost in the middle" effect and its practical, honestly-scoped implication.
- [ ] I can deduplicate near-identical retrieved chunks at assembly time.
- [ ] I can assemble a complete, citable context block with provenance metadata attached.
- [ ] I check context assembly (budget, order, redundancy) as a distinct possible cause when a
      well-retrieved answer is still inconsistent.
- [ ] I scored 10/13 on the quiz.

---

## 14. References

- Liu, N. F. et al., *Lost in the Middle: How Language Models Use Long Contexts*, 2023 (the source of the
  positional effect discussed in §5.3). `[UNVERIFIED]`
- Anthropic documentation, prompt engineering guidance on context window usage. `[UNVERIFIED]`

---

## 15. Next lesson

→ M7-L12 — Citations and Evidence Verification

You now have a complete, budget-aware, citable context block. Next: making sure a generated answer's
citations actually correspond to what the retrieved evidence says, rather than merely looking plausible.
