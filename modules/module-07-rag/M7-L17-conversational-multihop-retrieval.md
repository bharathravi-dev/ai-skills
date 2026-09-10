# M7-L17 — Conversational and Multi-Hop Retrieval

| | |
|---|---|
| **Lesson ID** | M7-L17 |
| **Difficulty** | 3 (Advanced) |
| **Estimated study time** | 2.0 hours |
| **Prerequisites** | [M7-L09](M7-L09-query-rewriting-expansion-decomposition.md), M5-L10 |

---

## 1. Learning objectives

1. **Demonstrate** a real question that a single flat retrieval pass cannot answer, and explain why.
2. **Implement** a two-hop retrieval chain that discovers an entity in the first hop and uses it to find
   the real answer in the second.
3. **Implement** conversational query rewriting that carries context across more than one prior turn,
   extending M7-L09's single-follow-up example.
4. **Combine** multi-hop entity resolution with multi-turn context tracking in a single, realistic case.
5. **Explain** when a multi-hop retrieval chain should stop, and why an unbounded chain is a real risk.

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **Multi-hop retrieval** | Answering a question that requires more than one retrieval pass, where a later pass depends on what an earlier pass found. |
| **Hop** | One retrieval pass in a multi-hop chain. |
| **Entity discovery** | Identifying a specific name, term, or identifier from a retrieved document, to be used as input to a subsequent retrieval. |
| **Multi-turn context** | Information accumulated across more than one turn of a conversation, needed to correctly interpret a later turn. |
| **Hop budget** | A limit on how many retrieval passes a multi-hop chain may take before stopping or abstaining. |

---

## 3. Plain-language explanation

### 3.1 M7-L09 rewrote one follow-up; this lesson chains retrieval itself

M7-L09 showed a single conversational follow-up needing context from the immediately preceding turn.
This lesson covers two harder, related cases: a question that needs its own entity discovered through
retrieval before the real answer can even be searched for, and a conversation where the needed context
comes from further back than just one turn.

### 3.2 A relevant-looking answer can still be the wrong answer

§7.1 shows something subtler than a retrieval *miss* (M7-L01's or M7-L09's vocabulary-gap failures): a
single flat query's top result shares real, meaningful vocabulary with the question and still doesn't
answer it — because the question's real target (the manager's actual policy) is only reachable through an
entity that the question itself never states.

### 3.3 Retrieving twice, in sequence, closes the gap

§7.2 doesn't just claim multi-hop retrieval works — it retrieves once to find the missing entity, then
retrieves again using exactly what the first pass found, and confirms neither pass alone would have
worked.

### 3.4 A conversation's memory has to outlast one turn

§7.3 extends this to three turns, and its central finding is specific: the context a later turn needs can
come from two turns back, not just the last one — a rewriter that only remembers "the previous turn" would
succeed at turn 2 and still fail at turn 3.

### 3.5 Hopping has to stop somewhere

§7.4 closes with the same discipline this course applies to every open-ended cost (M7-L09's decomposition,
M7-L13's abstention): a chain that doesn't know when to stop is a real cost and reliability risk, not just
an elegant idea taken too far.

---

## 4. Analogy

**Tracing a rumor back to its source through a chain of people.** Someone tells you "ask Priya about the
new policy" — but you don't actually know the policy yet, only who to ask next. You go ask Priya, and
*then* you learn the actual policy. Neither step alone gave you the answer: the first person gave you a
name, not a policy; Priya gave you the policy, but only once you knew to ask her specifically. A
conversation where someone says "and what about the other team?" three exchanges later requires you to
still remember what "the other team's manager said" was actually about — not just who you're now asking,
but what you were originally asking them.

### Where the analogy breaks

- **A human naturally keeps a whole conversation's context without conscious effort.** §7.3's finding —
  that a rewriter needs deliberate, explicit tracking across turns — is a reminder that this doesn't happen
  automatically in a retrieval system the way it does in a person's memory.
- **A human knows when to stop chasing a lead.** §7.4's hop-budget discipline is a designed, explicit
  safeguard — there's no equivalent instinct in a retrieval pipeline that isn't built in on purpose.

---

## 5. Detailed technical explanation

### 5.1 A relevant-looking failure, measured

`[REAL, measured]` §7.1 ran a flat query asking whether Engineering's manager allows remote work. **The
top result (score 2.027) correctly identifies who manages Engineering — and says nothing about
work-location policy at all.** The actual answer scores **exactly 0.000**, because it never mentions
"Engineering" — only the manager's name. **A document can share real vocabulary with a question and still
fail to answer it**, when the actual answer is reachable only through information the question itself
doesn't state.

### 5.2 Two hops, each doing a distinct job

`[REAL, measured]` §7.2 retrieved twice. Hop 1 ("who manages the Engineering team") correctly found the
management-fact document and yielded an entity: "Priya Shah." Hop 2, querying with that name over the
*remaining* documents (deliberately excluding hop 1's own result, to avoid redundant re-discovery), found
the real answer with the only nonzero score in its pool (1.885). **Hop 1 found an entity, not an answer.
Hop 2 found an answer, but only because hop 1 supplied the term it needed.**

### 5.3 Context from two turns back, measured

`[REAL, measured]` §7.3 ran a three-turn conversation. Turn 2's raw form (no entity) **retrieved the wrong
person's policy document** (2.434 vs. the correct target's 1.303) — rewriting with the entity discovered
in turn 1 fixed it (2.605, correctly on top). **Turn 3's raw form found no policy content at all** — just
the same "who manages Engineering" fact turn 1's pattern would have found for a different team, with the
work-location topic from turn 2 completely absent. **Correctly rewriting turn 3 required combining two
things**: the topic carried forward from turn 2, and §5.2's own finding that the real answer needs the
manager's *name*, not the team name. The rewritten version scored correctly (3.736, clearly on top).
**A rewriter tracking only the single most recent turn would succeed at turn 2 and still fail at turn 3** —
multi-turn context needs to persist across the whole conversation, not just one step back.

### 5.4 When to stop

`[REAL reasoning]` §7.4 names two real stopping conditions: a hop that yields no new entity to chase (there
is nowhere further to go, and the chain should answer with what it has, or abstain per M7-L13 if that's
insufficient), and a hop-count budget being reached before an answer is found (an unbounded chain is a real
cost risk, at roughly M7-L09's own measured per-pass cost, multiplied by however many hops are attempted).
`[UNVERIFIED — a specific hop-count budget is task- and cost-dependent; calibrate it against your own
queries.]`

### 5.5 Assumptions and limitations

- Entity extraction ("read the name out of the retrieved text") and query rewriting throughout this lab
  are hand-authored, standing in for what a real system would do with an LLM call or a named-entity-
  recognition step — consistent with every lab in this course, none of which calls a real model.
- This lesson does not cover programmatically deciding *when* a query needs multi-hop treatment versus a
  single pass — a real, harder classification problem left unaddressed here.
- Combining multi-hop retrieval with reranking (M6-L12) at each hop is a natural extension not demonstrated
  in this lab.

---

## 6. Worked example — the assistant that answered a two-hop question with a one-hop guess

**The system.** An internal Q&A assistant retrieves once per query, with no multi-hop capability, and no
detection for when a question's answer might require it.

**What went wrong.** Employees asking questions in the shape "does [team]'s manager allow X" consistently
received confident, cited answers that were actually about a different, unrelated policy — the system's
single retrieval pass reliably surfaced *some* relevant-looking document (often just confirming who the
manager was) and generated a fluent answer from whatever it found, with no signal that the real information
required a second retrieval step the system never took.

**Why this looked like a hallucination problem at first.** The generated answers weren't inventing facts
from nothing — each one was grounded in a real, retrieved, cited document (M7-L12's groundedness check
would have passed every one of them). Per §5.1, the actual defect was upstream: the wrong document was
being treated as sufficient, when the question's structure required a second, dependent retrieval the
system had no mechanism to perform at all.

**Three defects:**

| # | Defect | Consequence |
|---|---|---|
| 1 | The system had no multi-hop retrieval capability at all | Questions whose answers required entity discovery could only ever be answered from whatever a single pass happened to surface |
| 2 | No detection existed for when a question's shape suggested multi-hop treatment | The system had no way to recognize it was in over its depth for this class of question |
| 3 | Citation and groundedness checks passed even on these wrong answers | The wrongness was invisible to every automated quality check already in place |

### The fix

**Implement multi-hop retrieval for question shapes that require it**, per §5.2 — discover the needed
entity first, then retrieve again using it, rather than trusting a single pass to find everything.

**Design (even simple, rule-based) detection for when a question likely needs multi-hop treatment** —
per §5.5, this is a real, unsolved-in-general problem, but even a partial heuristic (e.g. a question
referring to "X's manager's Y" pattern) is better than none.

**Recognize that groundedness checks alone cannot catch this failure class** — per §6, a wrong-but-grounded
answer passes every check M7-L12 introduced, since the problem is upstream of generation entirely.

**The general rule.** **A single retrieval pass answers only questions whose answer is directly reachable
from the question's own words — any question requiring an intermediate fact to be discovered first needs
a system that can actually retrieve more than once.**

---

## 7. Practical activity

**File:** [`labs/m7/l17_conversational_multihop_retrieval.py`](../../labs/m7/l17_conversational_multihop_retrieval.py)

**No API key, no network, no third-party dependencies.** Runs in well under a second.

```bash
source .venv/bin/activate
python labs/m7/l17_conversational_multihop_retrieval.py
```

### 7.2 Expected output

`[EXECUTED]` — 2026-09-10, Python 3.10.11 (pure standard library).

```text
============================================================================
1. ONE FLAT QUERY: THE TOP RESULT IS THE WRONG DOCUMENT
============================================================================
  Question: "Does the Engineering team's manager allow employees to be based from home?"

  Single flat retrieval pass over the whole corpus:
    ORG1 (score 2.027): 'The Engineering team is managed by Priya Shah.'
    ORG3 (score 0.741): 'The Sales team is managed by Tom Reyes.'
    ORG2 (score 0.000): 'Priya Shah allows staff to work from any location without restriction.'
    ORG4 (score 0.000): 'Tom Reyes requires staff to work from the central office without exception.'

  Top-1 result: ORG1 -- 'The Engineering team is managed by Priya Shah.'
  This document confirms WHO manages Engineering, but says NOTHING about
  work-location policy at all -- it's a genuinely relevant-LOOKING match
  (it shares 'Engineering team manager' with the query) that does not
  actually answer the question asked. The real answer (ORG2) scores
  exactly 0.000 here -- it never even enters the ranking on merit, because
  its text never mentions 'Engineering' at all, only the entity's name.

============================================================================
2. TWO-HOP RETRIEVAL: DISCOVER THE ENTITY, THEN QUERY USING IT
============================================================================
  Hop 1 -- retrieve to find the entity itself: 'who manages the Engineering team'
    ORG1 (score 2.027): 'The Engineering team is managed by Priya Shah.'
    ORG3 (score 0.741): 'The Sales team is managed by Tom Reyes.'
    ORG2 (score 0.000): 'Priya Shah allows staff to work from any location without restriction.'
    ORG4 (score 0.000): 'Tom Reyes requires staff to work from the central office without exception.'
  Hop 1 result: ORG1 -- extract the entity name from its text: 'Priya Shah'

  Hop 2 -- query using the DISCOVERED entity, over the REMAINING documents
  (excluding ORG1, already used to extract the entity): 'Priya Shah'
    ORG2 (score 1.885): 'Priya Shah allows staff to work from any location without restriction.'
    ORG3 (score 0.000): 'The Sales team is managed by Tom Reyes.'
    ORG4 (score 0.000): 'Tom Reyes requires staff to work from the central office without exception.'
  Hop 2 result: ORG2 -- 'Priya Shah allows staff to work from any location without restriction.'

  The entity needed to find the real answer ('Priya Shah') never
  appeared anywhere in the ORIGINAL question -- it could only be
  discovered by retrieving once, reading the result, and retrieving
  AGAIN using what was just found. Neither hop alone answers the
  question; the chain of two does.

============================================================================
3. A THREE-TURN CONVERSATION: CONTEXT FROM TWO TURNS BACK
============================================================================
  Turn 1: 'Who manages the Sales team?'
    Retrieved: ORG3 -- 'The Sales team is managed by Tom Reyes.'
    Tracked context: manager='Tom Reyes', team='Sales'

  Turn 2 (raw): 'What is his policy on staff work location?'
    All scores WITHOUT rewriting: [('ORG2', 2.434), ('ORG4', 1.303), ('ORG1', 0.0), ('ORG3', 0.0)]
    Top-1: ORG2 -- WRONG, this isn't Tom Reyes's own policy at all.
  Turn 2 (rewritten using turn 1's discovered entity, M7-L09's pattern): "What is Tom Reyes's policy on staff work location?"
    All scores WITH rewriting: [('ORG4', 2.605), ('ORG2', 2.434), ('ORG3', 1.482), ('ORG1', 0.0)]
    Top-1: ORG4 -- correct.
    Tracked context: manager='Tom Reyes', team='Sales', topic='staff work-location policy'

  Turn 3 (raw): 'What about the Engineering team?'
    All scores WITHOUT rewriting: [('ORG1', 2.027), ('ORG3', 0.741), ('ORG2', 0.0), ('ORG4', 0.0)]
    Top-1: ORG1 -- just re-finds WHO manages Engineering,
    not any work-location policy at all; the topic from turn 2 is gone.
  Turn 3 needs context from BOTH turn 1's pattern (which team -> now
  Engineering) AND turn 2's topic (work-location policy) AND section 2's
  own finding (the answer is findable only via the manager's NAME, not
  the team name). Rewritten using all three: "What is Priya Shah's policy on staff work location?"
    All scores WITH rewriting: [('ORG2', 3.736), ('ORG1', 1.482), ('ORG4', 1.303), ('ORG3', 0.0)]
    Top-1: ORG2 -- correct.

  Turn 3's raw form has no topic of its own at all -- exactly M7-L09's
  finding -- but the missing context here comes from TWO turns back (the
  work-location topic from turn 2), not the immediately preceding turn,
  and correctly resolving it ALSO requires section 2's multi-hop insight
  (use the manager's name, not the team name). A rewriter that only
  remembers the single most recent turn, or that never resolves the team
  name to an entity, would fail this turn even while succeeding at turn 2.

============================================================================
4. WHEN TO STOP HOPPING
============================================================================
  This lab's example needed exactly two hops (and, in turn 3, the same
  hop reused inside a conversation). A real question could need three,
  four, or an unbounded chain -- and each additional hop is another full
  retrieval pass, at M7-L09's own measured cost (roughly linear in the
  number of hops, the same shape as decomposition's cost curve).

  Two real stopping conditions matter, connecting directly to prior
  lessons:
    1. A hop's result doesn't contain a new entity to chase -- there is
       nowhere further to go, and the chain should stop and answer with
       whatever has been found (or abstain, M7-L13, if that's not enough).
    2. A hop count budget is reached before an answer is found -- an
       unbounded hop chain is a real cost and latency risk, not just a
       correctness one; a system should abstain rather than loop
       indefinitely chasing an entity that never resolves.
  `[UNVERIFIED -- a specific maximum hop count is task- and cost-
  dependent; calibrate it against your own queries, the same discipline
  applied to every other threshold in this course.]`

============================================================================
5. WHAT THIS LAB IS AND IS NOT
============================================================================
  REAL: every BM25 score in this lab is computed with M6-L03's exact
  formula; the flat-query failure (wrong top-1 result), the two-hop
  chain's success, and every turn's raw-vs-rewritten comparison in
  section 3 are genuinely measured outcomes, not scripted -- including
  turn 2's raw form landing on the wrong document and turn 3's raw form
  finding no policy content at all.

  ILLUSTRATIVE: entity extraction ('read Priya Shah out of ORG1's
  text') and query rewriting in this lab are hand-authored, standing
  in for what a real system would do with an LLM call or a named-
  entity-recognition step -- consistent with every lab in this course,
  none of which calls a real model.

  NOT SHOWN: automatic entity extraction from retrieved text; deciding
  PROGRAMMATICALLY when a query needs multi-hop treatment versus a
  single pass (a real, harder classification problem); and combining
  multi-hop retrieval with reranking (M6-L12) at each hop, a natural
  extension left to the exercises.

Done.
```

### 7.3 Reading the result

**Section 1's zero score for the real answer is worth sitting with.** It isn't a low-but-nonzero score
losing a close race — the correct document has *no* measurable connection to the flat query at all. The
only way to it is through information the question doesn't contain.

**Section 3's turn 2 result is a genuinely uncomfortable one, and reported honestly rather than smoothed
over.** The raw query didn't just fail to find anything — it confidently landed on a specific, wrong,
plausible-looking document (a different person's policy). This is a sharper failure than "no results," and
worth taking seriously as the realistic shape conversational retrieval bugs actually take.

**Section 3's turn 3 is this lesson's true integration point.** It isn't solvable by M7-L09's rewriting
alone (topic tracking) or by §5.2's multi-hop technique alone (entity resolution) — it genuinely needs
both, combined, which is the most realistic picture of what a production conversational RAG system
actually has to do.

---

## 8. Common mistakes and troubleshooting

1. **Assuming a retrieved document's topical relevance means it answers the question.** §5.1 — a document
   can share real vocabulary with a query and still not contain the actual answer.
2. **Treating a single retrieval pass as sufficient for every question shape.** §5.2, §6 — some questions
   require an intermediate entity to be discovered before the real answer is even searchable.
3. **Including an already-used document in a subsequent hop's candidate pool.** §5.2 — this risks
   redundant re-discovery instead of finding genuinely new information.
4. **Tracking only the single most recent conversational turn.** §5.3 — a later turn's needed context can
   come from further back, and a one-step memory will fail exactly when it matters most.
5. **Assuming citation and groundedness checks (M7-L12) catch multi-hop failures.** §6 — a wrong answer
   built from a genuinely retrieved, correctly cited document passes those checks; the defect is upstream.
6. **Allowing a multi-hop chain to continue indefinitely with no budget.** §5.4 — this is a real cost and
   latency risk; a hop budget with an abstention fallback (M7-L13) is a necessary safeguard.

| Symptom | Likely cause | Fix |
|---|---|---|
| A generated answer is fluent, cited, and grounded, but still factually wrong | The question required multi-hop retrieval, and only a single pass was performed | Detect and implement multi-hop retrieval for this question shape (§5.1-§5.2) |
| A conversational follow-up succeeds, but a LATER follow-up in the same conversation fails | Context tracking resets after each turn instead of persisting across the conversation | Track accumulated context across the whole conversation, not just the last turn (§5.3) |
| A multi-hop or multi-turn retrieval pipeline becomes slow or expensive on certain queries | No hop-count budget exists, allowing an unbounded chain | Add a hop budget with an abstention fallback when it's exceeded (§5.4) |
| Citation/groundedness monitoring shows no issues, but users report wrong answers | These checks validate individual claims against retrieved text, not whether retrieval found the RIGHT text | Check for multi-hop question shapes specifically as a separate failure class (§6) |

---

## 9. Security, privacy, reliability, cost

- **Reliability.** Implement multi-hop retrieval for question shapes that require discovering an
  intermediate entity before the real answer is searchable (§5.1-§5.2).
- **Reliability.** Track conversational context across the whole conversation, not only the most recent
  turn — a later turn's needed context can come from further back (§5.3).
- **Reliability.** Recognize that citation and groundedness checks (M7-L12) do not catch multi-hop
  failures — a wrong answer can still be genuinely grounded in a real, but insufficient, retrieved document
  (§6).
- **Cost.** Enforce a hop-count budget on multi-hop chains, with abstention (M7-L13) as the fallback when
  it's exceeded, since each additional hop is a real, measurable retrieval cost (§5.4).

---

## 10. Exercises

### Exercise 1 — Beginner (~20 min)

1. In one sentence, why did the flat query in §7.1 return the wrong top result?
2. What did hop 1 find, and what did it NOT find, in §7.2?
3. Why did turn 2's raw query in §7.3 retrieve the wrong document?
4. From how many turns back did turn 3 need context, and what does that imply?
5. Name the two real stopping conditions for a multi-hop chain, per §7.4.

### Exercise 2 — Intermediate (~40 min)

1. Run the lab. Confirm §7.1's zero score for the real answer and §7.3's turn-2/turn-3 raw-vs-rewritten
   results on your own machine.
2. Add a third team/manager/policy triple to the corpus and construct a new two-hop question that requires
   discovering that manager's name first.
3. Extend the three-turn conversation to a fourth turn that needs context from turn 2 specifically (not
   turn 3), and verify your rewriter correctly reaches back that far.
4. Construct a case where hop 1 finds an entity, but hop 2 (using that entity) ALSO fails to find a
   complete answer and would need a third hop — implement and test the third hop.
5. Using M7-L09's cost-accounting method, compute the total retrieval-pass cost of this lesson's full
   three-turn conversation (including both hops used for turn 3).

### Exercise 3 — Challenge (~50 min)

1. Implement a simple heuristic that detects, from a query's structure alone (e.g. a possessive chain like
   "X's Y's Z"), whether a question likely needs multi-hop treatment, and test it against both single-hop
   and multi-hop example questions.
2. Design and implement a hop-budget-enforcing multi-hop retriever that abstains (M7-L13's mechanism) when
   the budget is exceeded without finding a resolving entity.
3. Combine this lesson's multi-hop retrieval with M6-L12's cross-encoder-style reranking at each hop, and
   test whether reranking changes which entity gets extracted at hop 1.
4. Research (conceptually) how a real multi-hop QA system (e.g. one using an LLM to decide when and how to
   hop) might differ from this lab's fixed, two-hop, hand-authored approach.
5. Using this lesson's §6 worked example as a model, design a test suite specifically for multi-hop
   question shapes that citation/groundedness checks alone would not catch.

---

## 11. Quiz

*(Answers: [`answer-keys/module-07-answers.md`](../../answer-keys/module-07-answers.md#m7-l17).)*

**Q1.** Per §7.1, why did the flat single-hop query's top-1 result fail to answer the actual question?

- A. The retrieval algorithm crashed and returned no result at all.
- B. The corpus did not contain any document relevant to the question.
- C. BM25 cannot process questions phrased with "Does."
- D. It returned the document confirming who manages Engineering, but that document says nothing about work-location policy; the real answer never mentions "Engineering" at all, only the manager's name.

**Q2.** Per §7.1's measured result, what score did the real answer document receive from the flat query?

- A. Exactly 0.000 — it never entered the ranking on merit at all, since it shares no relevant vocabulary with the flat query.
- B. The highest score of any document in the corpus.
- C. A score that could not be computed due to a formatting error.
- D. A score identical to every other document in the corpus.

**Q3.** Per §7.2, what did hop 1 accomplish, and what did it NOT do?

- A. It answered the original question completely on its own.
- B. It found the entity (the manager's name) needed for the real answer, but did not itself answer the original question.
- C. It deleted the document containing the real answer from the corpus.
- D. It required no further retrieval steps of any kind.

**Q4.** Per §7.2, why was hop 1's own top result excluded from hop 2's candidate pool?

- A. It was excluded due to a random selection process with no underlying logic.
- B. It was excluded because it no longer existed in the corpus at all.
- C. It had already been used to extract the entity, so re-including it in hop 2 would be redundant re-discovery rather than finding new information.
- D. It was excluded because it scored a perfect, maximum possible score.

**Q5.** Per §7.3's measured result, why did turn 2's raw (unrewritten) query retrieve the wrong document?

- A. The retrieval system does not support queries about policies at all.
- B. The document store was empty at the time this query ran.
- C. The query contained no words that could be tokenized.
- D. Without the entity name, the query's remaining generic terms happened to match a different person's unrelated policy document more strongly than the intended target's.

**Q6.** Per §7.3's measured result, what happened to turn 3's raw (unrewritten) query?

- A. It found only the document confirming who manages Engineering, with no work-location policy content at all — the topic established in turn 2 was completely lost.
- B. It correctly found the exact same answer as the rewritten version.
- C. It returned every document in the corpus with an identical score.
- D. It caused the entire conversation to be discarded and restarted.

**Q7.** Per §7.3, what TWO things did turn 3's correct rewrite need to combine?

- A. Nothing beyond the exact words used in turn 1 alone.
- B. The topic carried forward from turn 2 (work-location policy) and the multi-hop insight from section 2 (resolving the team name to the manager's actual name, not just using the team name).
- C. A completely new topic unrelated to anything discussed in turns 1 or 2.
- D. Only the team name, with no reference to work-location policy at all.

**Q8.** Per §7.3, from how many turns back did turn 3 need context, and what does this imply about
conversational query rewriting?

- A. Zero turns back; turn 3 required no prior context at all.
- B. Only the single immediately preceding turn, the same as M7-L09's original example.
- C. Two turns back — implying a rewriter must track context across the whole conversation, not just the single immediately preceding turn.
- D. An unlimited, unspecified number of turns back with no practical bound.

**Q9.** Per §7.4, what are the two real stopping conditions for a multi-hop retrieval chain?

- A. The chain should always continue indefinitely regardless of any condition.
- B. The chain should stop only after exactly one hop, regardless of whether an entity was found.
- C. There are no real stopping conditions; a well-designed system never needs to stop hopping.
- D. A hop's result contains no new entity to chase (nowhere further to go), or a hop count budget is reached before an answer is found.

**Q10.** Per §7.4, what should a system do if a hop count budget is reached before an answer is found?

- A. Abstain (M7-L13's mechanism) rather than loop indefinitely chasing an entity that never resolves.
- B. Continue hopping indefinitely until the process is manually terminated by an administrator.
- C. Immediately delete the corpus and restart ingestion from scratch.
- D. Return a random document from the corpus regardless of relevance.

**Q11.** Per §7.5, what is illustrative rather than fully real about this lab's entity extraction and query
rewriting?

- A. The BM25 formula, which this lesson computes exactly as in M6-L03.
- B. They are hand-authored, standing in for what a real system would do with an LLM call or a named-entity-recognition step, consistent with every lab in this course not calling a real model.
- C. They are generated by a real, live language model call made during this lab's execution.
- D. They are retrieved from an external, internet-connected knowledge base.

**Q12.** What is the general lesson this lab demonstrates about conversational and multi-hop retrieval?

- A. Every question can always be answered correctly with exactly one retrieval pass, regardless of complexity.
- B. Multi-hop retrieval and conversational context tracking are entirely unrelated problems with no shared mechanism.
- C. Some questions cannot be answered by a single retrieval pass at all, and correctly resolving them may require both discovering an entity through an earlier hop and tracking conversational context across more than just the immediately preceding turn.
- D. Conversational retrieval never requires more than the single most recent turn's context, regardless of the question.

**Q13.** *(Written, rubric-graded.)* In under 150 words: your RAG system gives a fluent, cited, and
apparently well-grounded answer that is nonetheless factually wrong, for a question shaped like "does
[team]'s manager allow X?" Based on this lesson, what would you check, and why might M7-L12's groundedness
checks not have caught it?

---

## 12. Revision notes

- **A retrieved document can share real vocabulary with a question and still not answer it** — measured
  directly: a flat query's top result correctly identified a team's manager but said nothing about the
  actual policy asked about, while the real answer scored exactly 0.000, unreachable by that query's own
  words.
- **Multi-hop retrieval discovers an entity in one pass and uses it in the next** — measured directly: hop
  1 found a name, hop 2 used that name to find the real answer; neither pass alone succeeded.
- **Already-visited documents should be excluded from later hops' candidate pools**, to avoid redundant
  re-discovery rather than finding genuinely new information.
- **Conversational context can be needed from more than one turn back** — measured directly: a
  three-turn conversation's final turn required topic information from two turns prior, which a
  one-step-memory rewriter would have lost.
- **Multi-hop entity resolution and multi-turn context tracking can both be needed for the same question**
  — measured directly: turn 3's correct rewrite required combining both, not either alone.
- **An unbounded multi-hop chain is a real cost and reliability risk** — a hop budget with an abstention
  fallback (M7-L13) is a necessary safeguard, not an optional refinement.

---

## 13. Completion checklist

- [ ] I can demonstrate a real question a single flat retrieval pass cannot answer, and explain why.
- [ ] I can implement a two-hop retrieval chain that discovers and then uses an entity.
- [ ] I can implement conversational query rewriting that tracks context across more than one prior turn.
- [ ] I can combine multi-hop entity resolution with multi-turn context tracking in one case.
- [ ] I enforce a hop budget on multi-hop chains, with abstention as the fallback.
- [ ] I recognize that citation and groundedness checks alone do not catch multi-hop retrieval failures.
- [ ] I scored 10/13 on the quiz.

---

## 14. References

- Yang, Z. et al., *HotpotQA: A Dataset for Diverse, Explainable Multi-hop Question Answering*, EMNLP 2018
  (general reference on multi-hop QA). `[UNVERIFIED]`
- Anthropic documentation, guidance on multi-turn conversation handling where available. `[UNVERIFIED]`

---

## 15. Next lesson

→ M7-L18 — Agentic Retrieval and Graph RAG

You now have retrieval that can chain across hops and conversation turns using hand-authored rewriting.
Next: letting a model itself decide when and how to retrieve, and representing knowledge as an explicit
graph of connected entities rather than a flat, unstructured corpus.
