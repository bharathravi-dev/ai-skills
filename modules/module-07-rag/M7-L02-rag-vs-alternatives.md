# M7-L02 — RAG vs Fine-Tuning vs Long Context vs Plain Tools

| | |
|---|---|
| **Lesson ID** | M7-L02 |
| **Difficulty** | 2 (Intermediate) |
| **Estimated study time** | 1.75 hours |
| **Prerequisites** | [M7-L01](M7-L01-rag-architecture-end-to-end.md) |

---

## 1. Learning objectives

1. **Compute** how RAG's and long context's per-query cost scale differently as a corpus grows, and
   explain why.
2. **Identify** the specific corpus and cost conditions under which long context is a legitimate,
   simpler choice rather than an inferior one.
3. **Distinguish** what fine-tuning is well suited for (style, format, behaviour) from what it is poorly
   suited for (precise, verbatim factual recall), and explain why.
4. **Recognize** task shapes where a plain, deterministic tool call is the correct answer, and neither RAG
   nor fine-tuning belongs in the picture at all.
5. **Apply** a decision framework to choose the right approach (or combination of approaches) for a given
   situation.

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **Long context** | Supplying an entire corpus (or a large portion of it) directly in the prompt on every query, with no retrieval or selection step. |
| **Fine-tuning** | Updating a model's own weights on task- or domain-specific data, so learned patterns are reflected in the model's parameters rather than supplied at inference time. |
| **Plain tool call** | Invoking a deterministic function (a calculator, a database lookup, a unit conversion) directly, bypassing the language model's "knowledge" entirely for tasks that don't need it. |
| **Cost scaling** | How a technique's resource cost (tokens, money, time) changes as an input — here, corpus size — grows. |
| **Verbatim recall** | Producing an answer by directly reproducing retrieved source text, as opposed to reconstructing an answer from a model's learned, compressed weights. |

---

## 3. Plain-language explanation

### 3.1 M7-L01 showed RAG works; this lesson asks when it's the right tool

M7-L01 built a working RAG pipeline and showed its value against a closed-book failure. It did not ask
whether RAG was the *best* available approach for that situation, or any situation. This lesson puts RAG
alongside its three real alternatives and gives each one a place it genuinely wins.

### 3.2 Long context is RAG with the retrieval step removed

§7.1–§7.2 compare RAG against the simplest possible alternative: instead of retrieving a relevant subset,
put the entire corpus in the prompt every time. This removes an entire failure mode (a retrieval miss,
M7-L01 §7.3) at the cost of paying for every document, every query, regardless of relevance — a cost that
§7.2 measures directly as the corpus grows.

### 3.3 Fine-tuning changes the model itself, not what it's shown

Fine-tuning takes a fundamentally different approach: instead of supplying information at answer time, it
adjusts the model's weights in advance. §7.4 makes the key practical distinction concrete: this is well
suited to teaching a model *how to behave*, and poorly suited to making it reliably *remember specific
facts* it can quote back verbatim.

### 3.4 Sometimes none of the three "knowledge" strategies are the point

§7.5 is a deliberate change of subject: for a task with one exact, computable answer, RAG, long context,
and fine-tuning are all the wrong shape of solution. A direct tool call — already covered in M5-L08 — is
correct, simpler, and cheaper.

### 3.5 A framework, not a single winner

§7.6 closes by mapping situations to approaches, and by stating plainly that real systems typically combine
more than one of these four — the question this lesson answers is not "which one is best" but "which one
fits this specific need."

---

## 4. Analogy

**Deciding how to answer questions in an open-book exam versus a closed-book one versus a calculator
allowed.** RAG is an open-book exam where you're handed exactly the relevant page of the textbook for each
question — fast to check, but only as good as the person handing you pages. Long context is being handed
the *entire textbook* for every single question — nothing is ever missing, but you're carrying the whole
book to answer even the simplest question. Fine-tuning is closer to genuinely *studying* the material in
advance, so you can answer from memory without any book at all — useful for developing a general skill or
style of answering, much less reliable for reciting a specific footnote word for word months later. A
plain tool is a calculator sitting on the desk: for "what's 15% of 340," you don't open any book at all,
you just compute it.

### Where the analogy breaks

- **A student's "memory" from studying and a model's weights from fine-tuning are not really the same kind
  of storage.** The analogy is meant to motivate the STYLE-vs-FACTS distinction in §5.3, not to claim
  fine-tuning works like human memorization mechanically.
- **A real exam doesn't let you combine strategies mid-question.** §5.5's decision framework explicitly
  expects real systems to combine several of these approaches together.

---

## 5. Detailed technical explanation

### 5.1 The cost-scaling argument, measured

`[REAL]` §7.2 measured this lab's own 6 documents at an average of 27.7 words each (an estimated 36.0
tokens/document, at a commonly cited ~1.3 tokens/word rule of thumb). Extrapolating:

| Corpus size | Long-context tokens/query | RAG tokens/query (top-3) |
|---|---|---|
| 6 | 216 | 108 |
| 500 | 17,983 | 108 |
| 50,000 | 1,798,333 | 108 |

**RAG's per-query cost is fixed by how many chunks it retrieves (top-*k*), never by total corpus size.**
Long context's cost scales linearly with corpus size, because it inserts everything, every time. At this
lab's own tiny corpus the gap is small (2x); at 50,000 documents — not an unusual size for a real
knowledge base — long context costs roughly 16,667x more per query for the identical question. **This ratio
is exactly corpus size ÷ top-*k*, and does not depend on the token-per-word estimate at all** — it is a
structural property of the two approaches, not an artifact of this lab's specific numbers.

### 5.2 Where long context genuinely wins

`[REAL reasoning, illustrative scale]` §7.3 states the honest boundary: at small, stable corpus sizes, long
context's cost penalty is modest, and it comes with two real advantages RAG does not have — no retrieval
step that can miss the relevant document (M7-L01 §7.3's vocabulary-mismatch failure structurally cannot
happen if nothing is ever excluded from the prompt), and no separate indexing pipeline to build or maintain
(M6-L05–M6-L08). **RAG's added complexity earns its keep specifically at the scale where §5.1's cost gap
becomes large, or where the corpus is too big to fit in any context window at all.**

### 5.3 Fine-tuning: behaviour over facts, and why

`[CONCEPTUAL]` §7.4 draws the lesson's second key distinction. Fine-tuning adjusts a model's weights toward
patterns in its training data — well suited to teaching a consistent *style, format, or behaviour* (always
respond in JSON, adopt a specific tone, follow a specific reasoning pattern). It is poorly suited to
reliably storing individual, precise *facts* for later exact recall, because weights are a lossy,
compressed summary of training data, not a lookup table. **RAG retrieves the actual source text verbatim
at answer time — precisely why M7-L01's grounded answer could state an exact figure with a citation,
something a fine-tuned model asked the same question has no verbatim source to point back to.**

### 5.4 The update-cost asymmetry

`[CONCEPTUAL, illustrative figures]` §7.4 also contrasts how each approach absorbs new or changed data: RAG
requires only re-indexing the new or changed documents (seconds to minutes, per M6-L10's own measured
lifecycle); fine-tuning requires retraining or re-running a tuning job, plus re-evaluation (hours to days).
**This asymmetry compounds with how often the underlying information changes** — a fast-changing policy
corpus favors RAG on update-cost grounds alone, independent of §5.1's per-query cost argument.

### 5.5 Plain tools, and the decision framework

`[REAL]` §7.5 computed `calculate_percentage(340, 15) = 51.0` and `hours_to_minutes(3.5) = 210.0` directly
— exact, cheap, and instantaneous, for a task neither RAG nor fine-tuning is shaped to solve well (RAG
would retrieve a document *about* percentages, not compute one; fine-tuning would try to make arithmetic
*generally* more reliable through weight updates, an expensive, probabilistic solution to a deterministic
problem). §7.6 assembles all four approaches into one framework:

| Situation | Favoured approach |
|---|---|
| One deterministic, computable answer | Plain tool (M5-L08) |
| Small, stable corpus; simplicity valued | Long context |
| Large or frequently-updated corpus; need citations | RAG |
| Need to shift style, format, or behaviour broadly | Fine-tuning |
| Need to recall specific facts precisely and verifiably | RAG |
| Corpus too large for any context window | RAG |

**These are not mutually exclusive.** A realistic production assistant might combine a fine-tuned tone,
direct tool calls for computation, and RAG for facts and policies, reserving long context for a small,
one-off document a user pastes directly into the conversation.

### 5.6 Assumptions and limitations

- The 1.3 tokens/word conversion is a commonly cited approximation, not a measurement from any specific
  tokenizer. `[UNVERIFIED]`
- §5.4's fine-tuning timescales are typical, illustrative figures — this lesson trains no model and
  measures no real fine-tuning job.
- This lesson compares cost and structural fit, not answer *accuracy*, between the four approaches on
  real, ambiguous queries — that comparison depends heavily on the specific model, task, and data involved.

---

## 6. Worked example — the migration that fixed the wrong problem

**The system.** A small internal tool answers employee questions by stuffing all 40 company policy
documents into every prompt (long context, no retrieval). It works fine at launch. Eighteen months later,
the policy corpus has grown to 600 documents, and the team is told the feature has become "too expensive
to run" and is asked to fine-tune a smaller model on the policies instead, to cut cost.

**What actually happened during the fine-tuning attempt.** The fine-tuned model became noticeably cheaper
per query, but started giving confidently wrong answers to specific numeric questions (exact PTO day
counts, specific dollar thresholds) that the original long-context version had answered correctly, because
those documents were always in its prompt.

**Why the fix was the wrong fix.** Per §5.3, fine-tuning is not well suited to storing precise, individual
facts for exact recall — the very thing this application depended on. The team's actual problem, per §5.1,
was that long context's cost scales with corpus size — the fix implied by that specific problem was RAG
(keeping the per-query cost bounded via retrieval), not fine-tuning (which solved a cost problem by
introducing an accuracy problem in exactly the facts the application existed to get right).

**Three defects:**

| # | Defect | Consequence |
|---|---|---|
| 1 | The cost problem (long context scaling with corpus size) was correctly diagnosed | — |
| 2 | The fix chosen (fine-tuning) was matched to the symptom (cost) rather than the underlying cause (no bounded retrieval step) | Cost went down, but factual accuracy on exact figures went down with it |
| 3 | No one applied §5.3's style-vs-facts distinction before choosing an approach | A fix that was right for a different kind of problem was applied to this one |

### The fix

**Diagnose which axis is actually the problem before picking an approach** — cost (§5.1), staleness
(§5.4), or a need for a different behaviour/style (§5.3) point toward different fixes, and treating them as
interchangeable is how a working system gets a wrong-shaped fix.

**Move to RAG when a long-context system's cost problem is really a lack of a bounded, relevant retrieval
step** — this preserves verbatim factual accuracy while fixing the actual scaling problem (§5.1).

**Reserve fine-tuning for behaviour and style changes**, and pair it with RAG (not instead of it) when
precise factual recall still matters (§5.3, §5.5's framework).

**The general rule.** **Match the fix to the axis that's actually failing — cost, staleness, or
behaviour — rather than reaching for whichever of the four approaches is most fashionable or most familiar.**

---

## 7. Practical activity

**File:** [`labs/m7/l02_rag_vs_alternatives.py`](../../labs/m7/l02_rag_vs_alternatives.py)

**No API key, no network.** Runs in well under a second.

```bash
source .venv/bin/activate
python labs/m7/l02_rag_vs_alternatives.py
```

### 7.2 Expected output

`[EXECUTED]` — 2026-09-10, Python 3.10.11 (pure standard library, no third-party dependencies).

```text
============================================================================
1. FOUR APPROACHES TO THE SAME QUESTION
============================================================================
  Query: 'How many weeks of paid parental leave do employees get?'

  APPROACH 1 -- RAG: retrieve only the relevant chunk(s), insert them
  into the prompt alongside the query. (M7-L01's own pipeline.)

  APPROACH 2 -- LONG CONTEXT: skip retrieval entirely; insert EVERY
  document into the prompt on EVERY query, and let the model find the
  relevant part itself.

  APPROACH 3 -- FINE-TUNING: retrain the model's weights on this
  company's policies in advance, so the answer comes from the model's
  own parameters at inference time, with no retrieved context at all.
  `[CONCEPTUAL -- this lab does not fine-tune a real model; no training
  infrastructure or cost is available in this environment.]`

  APPROACH 4 -- PLAIN TOOL: for a task with a deterministic, computable
  answer (not this one -- see section 5), call a function directly and
  skip the language model's 'knowledge' altogether.

============================================================================
2. TOKEN-COST SCALING: RAG VS LONG CONTEXT AS THE CORPUS GROWS
============================================================================
  Measured on this lab's 6 real documents: average 27.7 words/doc, an estimated 36.0 tokens/doc (at 1.3 tokens/word).

   corpus size   long-context tokens/query    RAG tokens/query   long-context $/1K queries    RAG $/1K queries
             6                         216                 108                       $0.11               $0.05
            50                       1,798                 108                       $0.90               $0.05
           500                      17,983                 108                       $8.99               $0.05
         5,000                     179,833                 108                      $89.92               $0.05
        50,000                   1,798,333                 108                     $899.17               $0.05

  RAG's per-query cost is FIXED at 3 chunks regardless of how
  large the underlying corpus grows -- retrieval selects a constant-size
  slice every time. Long context's per-query cost grows LINEARLY with
  total corpus size, because it inserts everything, every query. At this
  lab's actual 6-document corpus the two are close; by 50,000 documents
  (a realistic size for a real knowledge base), long context costs
  roughly 16,667x
  more per query than RAG, for the same question.

============================================================================
3. WHERE LONG CONTEXT IS ACTUALLY THE RIGHT CHOICE
============================================================================
  Section 2's table has a crossover, not a verdict. At this lab's OWN
  6-document corpus, long context costs only a few times
  more than RAG -- and it comes with real advantages RAG does not have:
  no retrieval step to get wrong (M7-L01 section 3's vocabulary-mismatch
  miss cannot happen if nothing is ever excluded from the prompt), and
  no separate indexing pipeline to build or maintain (M6-L05-M6-L08).

  The honest read: for a SMALL, STABLE corpus -- one that comfortably
  fits in a single prompt at a cost you're willing to pay every query --
  long context is a legitimate, simpler choice, not an inferior one.
  RAG earns its added complexity specifically at the scale where
  section 2's cost gap becomes large, or where the corpus is too big to
  fit in any single context window at all.

============================================================================
4. FINE-TUNING VS RAG: FACTS VS BEHAVIOUR, AND THE COST OF AN UPDATE
============================================================================
  `[CONCEPTUAL -- typical, illustrative figures below; not measured in
  this lab, which trains nothing]`

  RAG:
    Update mechanism:      re-index the new/changed documents
    Typical time to reflect new data:  seconds to minutes (M6-L10)
  Fine-tuning:
    Update mechanism:      retrain (or re-run a tuning job)
    Typical time to reflect new data:  hours to days, plus re-evaluation

  The deeper distinction is not just speed -- it's WHAT each approach is
  good at storing. Fine-tuning shifts a model's weights toward patterns
  in its training data; this is well suited to teaching a STYLE, FORMAT,
  or BEHAVIOUR (respond tersely, always structure answers as JSON, adopt
  a specific tone). It is poorly suited to reliably storing individual,
  precise FACTS for later exact recall -- weights are a lossy, compressed
  summary of training data, not a lookup table. RAG retrieves the actual
  source text VERBATIM at answer time, which is exactly why M7-L01's
  grounded answer could state an exact figure (twelve weeks) with a
  citation -- a fine-tuned model asked the same question has no verbatim
  source to point to, only a weighted tendency learned from examples.

============================================================================
5. PLAIN TOOLS: WHEN NEITHER RAG NOR FINE-TUNING IS THE RIGHT ANSWER
============================================================================
  Query: 'What is 15% of $340, and how many minutes is 3.5 hours?'

  [REAL, direct tool call] calculate_percentage(340, 15) = 51.0
  [REAL, direct tool call] hours_to_minutes(3.5) = 210.0

  Neither RAG nor fine-tuning belongs anywhere near this query. RAG
  would retrieve a document ABOUT how percentages work, which does not
  compute this specific answer. Fine-tuning would try to make the model
  BETTER AT ARITHMETIC IN GENERAL through weight updates -- expensive,
  slow, and still probabilistic, for a problem with one exact, correct,
  cheaply-computable answer. M5-L08 already covers calling a tool
  directly for exactly this task shape: deterministic, well-defined,
  and answerable without any of the three knowledge-access strategies
  this lesson otherwise compares.

============================================================================
6. A DECISION FRAMEWORK
============================================================================
  Task has one deterministic, computable answer
    -> Plain tool (M5-L08)
  Small, stable corpus; simplicity valued over cost
    -> Long context
  Large or frequently-updated corpus; need citations
    -> RAG
  Need to shift STYLE, FORMAT, or BEHAVIOUR broadly
    -> Fine-tuning
  Need to recall specific FACTS precisely and verifiably
    -> RAG
  Corpus too large to fit any context window at all
    -> RAG

  These four approaches are not mutually exclusive in a real system --
  a production assistant might use a fine-tuned model (for tone), that
  calls plain tools (for arithmetic and lookups), backed by RAG (for
  facts and policies), with long context reserved for the rare case of a
  small, one-off document a user pastes directly into a conversation.

============================================================================
7. WHAT THIS LAB IS AND IS NOT
============================================================================
  REAL: word counts are computed directly from this lab's actual
  document text; the token-cost and dollar-cost scaling in section 2 is
  real arithmetic on those measured counts, extended by explicit,
  labeled extrapolation to larger corpus sizes; section 5's tool calls
  are genuinely executed, exact computations.

  ILLUSTRATIVE / UNVERIFIED: the 1.3 tokens/word conversion is a commonly
  cited rule of thumb, not a measurement from any specific tokenizer;
  section 4's fine-tuning timescales are typical, illustrative figures,
  not measurements -- this lab trains no model at all.

  NOT SHOWN: an actual fine-tuning run, an actual long-context API call
  at scale, and the accuracy trade-offs (not just cost) between these
  approaches on real, ambiguous queries -- this lesson's job is the
  decision framework, not a benchmark of any one approach's quality.

Done.
```

### 7.3 Reading the result

**Section 2's table is the lesson's quantitative core.** The ratio between long context and RAG cost is
exactly corpus size divided by top-*k* — worth internalizing as a structural fact, not just a number in a
table, since it holds regardless of the specific token-counting approximation used to get there.

**Section 3 is the deliberate counterweight to section 2** — without it, this lesson would read as "RAG
always wins," which is not the claim being made. The crossover point, not a fixed verdict, is the takeaway.

**Section 5 is a genuine change of subject, and that's the point.** It would be easy to read a "RAG vs
alternatives" lesson as being only about the three knowledge-access strategies — section 5 exists
specifically to head off the mistake of routing a deterministic task through any of them.

---

## 8. Common mistakes and troubleshooting

1. **Treating RAG as universally superior to long context.** §5.2 — at small, stable corpus sizes, long
   context is a legitimate, simpler choice, not an inferior one.
2. **Using fine-tuning to try to teach a model new facts it must recall exactly.** §5.3 — this is a
   structural mismatch; RAG's verbatim retrieval is suited to this, fine-tuning's weight updates are not.
3. **Fixing a cost problem (long context scaling with corpus size) with fine-tuning instead of RAG.** §6 —
   this addresses the wrong axis and can introduce a factual-accuracy regression.
4. **Routing a deterministic, computable task through RAG or fine-tuning.** §5.5 — use a direct tool call
   (M5-L08) instead; neither knowledge-access strategy is the right shape for this task.
5. **Assuming these four approaches are mutually exclusive.** §5.5 — real systems commonly combine them,
   each solving a different part of the problem.
6. **Choosing an approach before diagnosing which axis (cost, staleness, behaviour, determinism) is
   actually the problem.** §6 — match the fix to the actual cause, not the most familiar tool.

| Symptom | Likely cause | Fix |
|---|---|---|
| A long-context system's cost keeps climbing as the corpus grows | Cost scales linearly with corpus size in this architecture | Move to RAG's bounded, retrieval-based cost model (§5.1) |
| A fine-tuned model confidently states wrong specific facts | Fine-tuning is not suited to precise, verbatim factual recall | Use RAG for facts; reserve fine-tuning for style/behaviour (§5.3) |
| An arithmetic or lookup feature is unreliable despite a capable model | The task was routed through RAG or fine-tuning instead of a direct tool call | Implement a plain, deterministic tool call (§5.5) |
| Data updates take hours or days to reflect in answers | Using fine-tuning for information that changes frequently | Use RAG, which only requires re-indexing changed documents (§5.4) |

---

## 9. Security, privacy, reliability, cost

- **Cost.** Model the token-cost scaling of long context against corpus size (§5.1) before committing to it
  at any scale beyond a small, stable corpus.
- **Reliability.** Do not rely on a fine-tuned model to recall precise, individual facts verbatim — use RAG
  for anything requiring exact, citable factual accuracy (§5.3).
- **Reliability.** Route deterministic, computable tasks through direct tool calls, not through RAG or
  fine-tuning, to avoid introducing unnecessary unreliability into an already-solved problem (§5.5).
- **Cost.** Account for update cost (§5.4), not just per-query cost, when choosing between RAG and
  fine-tuning for frequently-changing information.

---

## 10. Exercises

### Exercise 1 — Beginner (~20 min)

1. In one sentence, why does RAG's per-query cost stay flat as a corpus grows, while long context's does
   not?
2. Name one real advantage long context has over RAG, per §5.2.
3. Why is fine-tuning poorly suited to teaching a model new, precise facts for exact recall?
4. Why is neither RAG nor fine-tuning the right approach for computing 15% of $340?
5. Name one situation from §5.5's decision framework where fine-tuning, not RAG, is favoured.

### Exercise 2 — Intermediate (~40 min)

1. Run the lab. Confirm §7.2's token-cost table and the exact 16,667x ratio by hand.
2. Using your own estimate of a realistic corpus size and top-*k* for a system you have in mind, compute
   the long-context-to-RAG cost ratio using §5.1's method.
3. Write a one-paragraph justification for why a specific hypothetical company (your choice) should use
   long context rather than RAG, using §5.2's criteria explicitly.
4. Using §5.4's update-cost argument, estimate how a weekly-changing policy corpus should be handled
   differently from a once-a-year one.
5. Design one additional deterministic task (other than arithmetic) that should be routed to a plain tool
   rather than RAG or fine-tuning, and justify it using §5.5.

### Exercise 3 — Challenge (~50 min)

1. Extend the lab to compute the exact corpus size at which long context and RAG cost the same, as a
   function of top-*k* and average document token count, and verify it against the lab's own numbers.
2. Design a hybrid system (conceptually, or in code) that combines all four approaches for a single
   realistic application, specifying which task types route to which approach and why.
3. Research (conceptually) prompt caching as a way to reduce long context's per-query cost, and explain
   what it changes and does not change about §5.1's scaling argument.
4. Write a short decision memo (under 300 words) recommending an approach for a hypothetical scenario with
   specific numbers (corpus size, update frequency, budget, accuracy requirements) you define yourself.
5. Using §6's worked example as a model, design a second, different scenario where the wrong one of these
   four approaches was chosen, and explain both what axis was actually the problem and what the correct
   fix would have been.

---

## 11. Quiz

*(Answers: [`answer-keys/module-07-answers.md`](../../answer-keys/module-07-answers.md#m7-l02).)*

**Q1.** Per §7.1–§7.2, what is the key structural difference between RAG and "long context" as retrieval
strategies?

- A. RAG always produces longer prompts than long context.
- B. RAG selects only a small, relevant subset of the corpus per query, while long context inserts the entire corpus into every prompt regardless of relevance.
- C. Long context requires a vector database and RAG does not.
- D. RAG and long context are simply two names for the same underlying technique.

**Q2.** Per §7.2's measured scaling, why does RAG's per-query token cost stay constant as the corpus grows
from 6 to 50,000 documents?

- A. Because the corpus never actually grows in a real system.
- B. Because RAG always uses a cheaper pricing tier than long context.
- C. Because RAG always retrieves a fixed number of chunks (top-k), independent of how many documents exist in total.
- D. Because RAG compresses every document before inserting it into the prompt.

**Q3.** Per §7.2, why does long context's per-query cost grow linearly with corpus size?

- A. Because it inserts every document into every prompt, so total tokens per query scale directly with total corpus size.
- B. Because long context uses a slower, more expensive model by design.
- C. Because long context re-embeds the corpus on every single query.
- D. Because long context requires a separate retrieval step that RAG does not.

**Q4.** Per §7.3, under what condition is long context described as a legitimate, not inferior, choice?

- A. Whenever the corpus contains any documents about company policy.
- B. Only when fine-tuning is unavailable for technical reasons.
- C. Whenever the query is phrased as a question rather than a command.
- D. A small, stable corpus that comfortably fits in a single prompt at an acceptable cost.

**Q5.** Per §7.4, what is fine-tuning generally well suited for, according to this lesson?

- A. Reliably storing individual, precise facts for later exact recall.
- B. Shifting a model's style, format, or behaviour, rather than reliably storing individual facts for exact recall.
- C. Replacing the need for any retrieval or context at all, in every situation.
- D. Making a model's per-query token cost lower than RAG's.

**Q6.** Per §7.4, why can RAG state an exact number with a citation in a way a fine-tuned model generally
cannot?

- A. Fine-tuned models are not permitted to generate numbers.
- B. RAG always uses a larger context window than any fine-tuned model.
- C. RAG retrieves the actual source text verbatim at answer time, while fine-tuning's weights are a lossy, compressed summary of training data, not a lookup table.
- D. Fine-tuning deletes the original training data after training completes.

**Q7.** Per §7.4's update-cost comparison, why does RAG typically reflect new or changed data faster than
fine-tuning?

- A. RAG only requires re-indexing the new or changed documents, while fine-tuning requires retraining (or re-running a tuning job) and re-evaluation.
- B. Fine-tuning is always fully automated with no human review required.
- C. RAG does not support updates of any kind once deployed.
- D. Fine-tuning only needs to be done once for any company, ever.

**Q8.** Per §7.5, why is neither RAG nor fine-tuning the right approach for "What is 15% of $340?"

- A. Because language models are fundamentally incapable of ever producing correct numbers.
- B. Because RAG and fine-tuning are both more expensive than every possible alternative in all cases.
- C. Because arithmetic questions are outside the scope of any AI system entirely.
- D. Because the task has one deterministic, exactly computable answer, which a direct tool call solves cheaply and reliably without needing any retrieved document or model knowledge at all.

**Q9.** Per §7.5, what would happen if this arithmetic query were answered via RAG instead of a direct tool
call?

- A. RAG would compute the exact numeric answer just as reliably as a direct tool call.
- B. RAG would retrieve a document ABOUT percentages, which does not itself compute this specific numeric answer.
- C. RAG would automatically fall back to fine-tuning instead.
- D. RAG cannot process any query containing a number.

**Q10.** Per §7.6's decision framework, which situation specifically favors RAG over the other three
approaches?

- A. A task with one deterministic, computable answer.
- B. A small, stable corpus where simplicity is valued over cost.
- C. A large or frequently-updated corpus where citations to specific source facts are needed.
- D. A need to shift a model's style or tone broadly across all responses.

**Q11.** Per §7.6's closing point, how do these four approaches typically relate in a real production
system?

- A. They are not mutually exclusive — a real system commonly combines several of them, such as a fine-tuned tone, tool calls for computation, and RAG for facts.
- B. Only one of the four approaches may ever be used in a single production system.
- C. Long context always replaces the need for the other three approaches once context windows are large enough.
- D. Fine-tuning and RAG cannot coexist in the same application under any circumstances.

**Q12.** Per §7.7, what does this lesson's lab NOT measure or demonstrate?

- A. Real word counts computed from this lab's own document text.
- B. Real, executed tool-call computations in section 5.
- C. Real arithmetic scaling token and dollar cost against measured word counts.
- D. An actual fine-tuning run, an actual long-context API call at scale, or accuracy trade-offs between the four approaches.

**Q13.** *(Written, rubric-graded.)* In under 150 words: a colleague proposes fine-tuning a model on your
company's policy documents so it can "just know" the answers without needing retrieval. Based on this
lesson, what would you tell them, and what would you propose instead (or in addition)?

---

## 12. Revision notes

- **RAG's per-query cost is bounded by top-k, independent of corpus size; long context's cost scales
  linearly with corpus size.** Measured: at 50,000 documents, long context costs roughly 16,667x more per
  query than RAG for the same question — a ratio equal to corpus size ÷ top-k.
- **Long context is a legitimate choice, not an inferior one, for small, stable corpora** — it avoids
  retrieval misses and indexing overhead entirely, at a cost penalty that stays modest at small scale.
- **Fine-tuning is well suited to shifting style, format, or behaviour; poorly suited to storing precise
  facts for exact, verbatim recall** — its weights are a lossy, compressed summary of training data, not a
  lookup table, unlike RAG's verbatim retrieval.
- **RAG reflects data changes faster than fine-tuning** — re-indexing (seconds to minutes) versus
  retraining and re-evaluation (hours to days).
- **Deterministic, computable tasks belong to plain tool calls (M5-L08), not RAG or fine-tuning** — routing
  arithmetic or lookups through either knowledge-access strategy is a structural mismatch.
- **These four approaches are not mutually exclusive** — real systems typically combine them, and the
  right question is which approach fits which specific need, not which one approach wins overall.

---

## 13. Completion checklist

- [ ] I can compute and explain why RAG's and long context's per-query costs scale differently as a
      corpus grows.
- [ ] I can identify when long context is a legitimate, simpler choice rather than an inferior one.
- [ ] I can explain why fine-tuning suits style/behaviour changes better than precise factual recall.
- [ ] I recognize deterministic, computable tasks that belong to a plain tool call, not RAG or fine-tuning.
- [ ] I can apply a decision framework to choose (or combine) the right approach for a given situation.
- [ ] I diagnose which axis (cost, staleness, behaviour, determinism) is the actual problem before
      picking a fix.
- [ ] I scored 10/13 on the quiz.

---

## 14. References

- Anthropic documentation, *Contextual retrieval* and *long context prompting* guidance. <https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/long-context-tips> `[UNVERIFIED]`
- Anthropic documentation, *Fine-tuning* guidance (where available for the relevant model family). `[UNVERIFIED]`

---

## 15. Next lesson

→ M7-L03 — Ingestion and Document Parsing

You now have a framework for choosing RAG deliberately, not by default. Next: the first stage of a real RAG
pipeline that this lesson and M7-L01 both left as a placeholder — actually getting real-world documents
(PDFs, HTML, plain text, and worse) into a form a pipeline can use at all.
