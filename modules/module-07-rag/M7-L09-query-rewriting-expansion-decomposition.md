# M7-L09 — Query Rewriting, Expansion and Decomposition

| | |
|---|---|
| **Lesson ID** | M7-L09 |
| **Difficulty** | 3 (Advanced) |
| **Estimated study time** | 2.0 hours |
| **Prerequisites** | [M7-L01](M7-L01-rag-architecture-end-to-end.md) |

---

## 1. Learning objectives

1. **Fix**, from the query side, a vocabulary-mismatch retrieval failure that M7-L01 documented and left
   unresolved.
2. **Implement** query rewriting to resolve a conversational follow-up that carries no retrievable topic
   of its own.
3. **Implement** query decomposition and explain why scoring a compound question's terms together can
   disadvantage a document that only answers half of it.
4. **Distinguish** query-side fixes (this lesson) from retrieval-method fixes (M6-L04, M6-L11) as
   complementary, not competing, approaches.
5. **Account** for the real, measurable cost each query-transformation technique adds.

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **Query expansion** | Adding related terms (synonyms, alternate phrasings) to a query before retrieval, to increase the chance of matching a document's actual vocabulary. |
| **Query rewriting** | Reformulating a query — often using conversation history — into a self-contained form retrieval can act on. |
| **Query decomposition** | Splitting a compound, multi-part question into separate sub-queries, retrieved independently. |
| **Context-free fragment** | A query (typically a conversational follow-up) that carries no retrievable topic of its own, depending entirely on prior context to be meaningful. |
| **Retrieval pass** | One execution of a retrieval method (e.g. one BM25 or vector search call) against the corpus. |

---

## 3. Plain-language explanation

### 3.1 M7-L01 found a retrieval failure and left it as an open problem

M7-L01 §7.3 documented, precisely and measurably, a query that shared no literal vocabulary with the one
document that actually answered it — a clean retrieval miss. That lesson framed the fix as "Module 6's
retrieval techniques." This lesson shows the other half of the fix: changing the query itself, before it
ever reaches retrieval.

### 3.2 The exact same failure, fixed from a different angle

§7.1–§7.2 don't invent a new example — they reproduce M7-L01's own documented failure, confirm it's still
zero, and then fix it with query expansion alone, touching neither the corpus nor the retrieval algorithm.

### 3.3 A follow-up question isn't always a complete question

§7.3 shows something query expansion can't fix: a follow-up ("What about the Mid tier?") that has no topic
at all in its own words — the actual subject only exists in the previous conversational turn. Rewriting,
not expanding, is the tool for this.

### 3.4 A compound question competes against itself

§7.4 shows a subtler problem: a question asking about two unrelated things, scored as one query, forces
two documents (each fully answering one half) to compete in a single ranking neither should have to share.
Decomposition removes the competition entirely, deliberately, by construction.

### 3.5 None of this is free

§7.5 closes with the trade-off this module keeps returning to (M7-L06's overlap, M7-L02's cost curves):
every technique here buys its fix with real, measurable extra work — mostly modest for expansion and
rewriting, linear and potentially significant for decomposition.

---

## 4. Analogy

**Asking a reference librarian a question, versus asking a search engine the same words.** A librarian
naturally expands "signing bonus for recommending someone" into the library's own catalog terms ("referral
incentive," "employee referral program") without being asked to — a search engine matching only literal
words does not, unless the query is expanded first. A librarian also naturally carries forward what you
asked five minutes ago — "and what about the other tier?" means something specific to them because they
remember your first question; a stateless search box treats it as five meaningless words. And if you ask a
librarian two unrelated things in one breath ("where's the tax section, and also do you have any cookbooks
by this author?"), a good librarian answers both, separately — not by trying to find one shelf that
satisfies both requests at once.

### Where the analogy breaks

- **A librarian's "expansion" and "rewriting" happen instantly and free, from expertise.** §7.5's cost
  section is the reminder that a computational system pays for each of these steps explicitly, in extra
  retrieval passes or model calls.
- **A librarian never mechanically fails on a follow-up the way §7.3's isolated retrieval does.** The
  contrast is closer to a phone directory (context-free lookup) suddenly being asked "the other one" with
  the actual name never stated.

---

## 5. Detailed technical explanation

### 5.1 Reproducing, then fixing, a documented failure

`[REAL, measured]` §7.1 re-ran M7-L01 §7.3's exact query ("Do you pay staff a reward for suggesting people
who then join the team?") against the same corpus and confirmed every document still scores **0.000** —
the failure is real and reproducible, not a one-off artifact. §7.2 then expanded the query's own terms
with synonyms (`reward → bonus`, `suggesting → refer`, `join → hire`, etc.) and re-scored: **P4 jumped from
0.000 to 9.948**, the only document with any genuine signal at all. **Nothing about the corpus or the
retrieval algorithm changed — only the query's own term set did.**

### 5.2 Query expansion is complementary to, not a replacement for, retrieval-side fixes

`[REAL]` M6-L04 (dense retrieval) and M6-L11 (hybrid fusion) address the same underlying vocabulary gap
from the retrieval-method side, by scoring semantic similarity rather than literal overlap. Query expansion
addresses it from the query side, by giving a purely lexical method (BM25) literal terms to match in the
first place. **A real system can use both together** — expansion does not make dense or hybrid retrieval
unnecessary, and vice versa.

### 5.3 Rewriting a context-free follow-up

`[REAL, measured]` §7.3 retrieved "What about the Mid tier?" in isolation and found **every document scores
exactly 0.000** — there is no meaningful top result, only an arbitrary tie among zero scores, because the
follow-up's own words ("what," "about," "mid," "tier," after stopword removal: "mid," "tier") carry no
topic at all. Rewriting it to explicitly restate the conversation's actual subject ("What is the PTO
accrual for Mid tier employees?") produced a clear top result: **P3 at 2.085**, far above every other
document. **The follow-up was never ambiguous to a human reading the whole conversation — it was
ambiguous specifically to a retrieval system seeing only that one turn's words.**

### 5.4 Decomposition removes cross-topic competition

`[REAL, measured]` §7.4 scored a compound question ("What is the remote work policy and how much is the
referral bonus?") as one query: **P1 (5.133) and P4 (3.924)** emerged as the top two, both genuinely
relevant. Decomposing into two sub-queries and retrieving each separately found the **same two documents**
(P1 for the remote-work half, P4 for the referral-bonus half) — **but for a structurally different, more
reliable reason**. In the single compound query, P1 and P4 (and every other document) are all scored
against the SAME combined term set, so a document answering only half the question is implicitly competing
against one answering the other half, within one ranking. Decomposition guarantees each half its own
dedicated retrieval, **regardless of how the two topics' documents happen to compare against each other**
— a guarantee the compound-query approach does not make, even when, as here, it happens to produce the
same result.

### 5.5 The real cost of each technique

`[REAL, arithmetic]` §7.5 states the cost shape plainly: expansion and rewriting keep the retrieval-pass
count at 1 (more or different query terms, same number of searches); a real rewriting step typically also
requires an LLM call to produce the rewritten query itself. Decomposition multiplies retrieval passes by
the number of sub-queries — 2 sub-queries, roughly 2x retrieval cost; N sub-queries, N times the cost —
**on top of whatever it costs, in a real system, to decide how to decompose the question in the first
place.**

### 5.6 Assumptions and limitations

- This lab's expansion synonyms and rewritten/decomposed queries are hand-authored, not produced by a real
  LLM call. The retrieval scores they produce are genuinely computed; the transformation step itself is
  illustrative of what a real system's model call would do.
- This lesson does not cover how a real system decides *when* to apply expansion, rewriting, or
  decomposition versus passing a query through unchanged, nor how to combine decomposed sub-query results
  into one coherent final answer (M7-L11, M7-L12).
- Multi-turn conversational retrieval at real depth (many turns, topic switches, references to much
  earlier context) is M7-L17's dedicated topic; this lesson shows the mechanism in miniature, for one
  follow-up turn.

---

## 6. Worked example — the support bot that couldn't handle "what about"

**The system.** A support chatbot answers policy questions using BM25 retrieval over the same kind of
policy corpus this lesson uses, with no query rewriting — each turn is retrieved using only its own literal
text.

**What went wrong.** Users asking a natural follow-up ("what about for contractors?" after asking about
full-time employee PTO) consistently received irrelevant or unhelpful answers, while the exact same
question asked as a single, fully-specified query ("what is the PTO policy for contractors?") worked fine.
Support tickets described the bot as "not able to follow a conversation," even though the underlying
retrieval and generation components were unchanged between the two phrasings.

**Why this was mistaken for a generation problem.** Per §5.3, the follow-up's own words carry no
retrievable topic — this is a retrieval-input problem, not a reasoning or generation problem. The team
initially reviewed the generation prompt and model behavior (following M7-L01 §6's general debugging
discipline of checking retrieval first would have redirected this immediately) before realizing the
retrieved context itself was already wrong for these specific turns.

**Three defects:**

| # | Defect | Consequence |
|---|---|---|
| 1 | No query rewriting step existed for conversational turns | Follow-up questions retrieved essentially at random, since their own words carried no topic |
| 2 | Conversation history was available to the generation step but not the retrieval step | The information needed to rewrite the follow-up existed, but was never used at the stage that needed it |
| 3 | The symptom was initially investigated as a generation/reasoning failure | Time was spent reviewing prompts before the actual, retrieval-input cause was identified |

### The fix

**Add a query rewriting step before retrieval for any conversational turn**, per §5.3 — using prior turns
to resolve pronouns, ellipsis, and implicit topics into an explicit, retrievable query.

**Make conversation history available to the retrieval stage, not only the generation stage** — per this
lesson's framing, rewriting needs exactly the context M5-L10 already tracks for conversation state.

**Check retrieval input first when a conversational answer seems wrong**, per M7-L01 §6's general
discipline, applied specifically to multi-turn conversations here.

**The general rule.** **A retrieval system has no memory of its own — every query is evaluated on its own
words alone, unless something upstream explicitly carries context forward into it.**

---

## 7. Practical activity

**File:** [`labs/m7/l09_query_rewriting_expansion_decomposition.py`](../../labs/m7/l09_query_rewriting_expansion_decomposition.py)

**No API key, no network, no third-party dependencies.** Runs in well under a second.

```bash
source .venv/bin/activate
python labs/m7/l09_query_rewriting_expansion_decomposition.py
```

### 7.2 Expected output

`[EXECUTED]` — 2026-09-10, Python 3.10.11 (pure standard library).

```text
============================================================================
1. THE PROBLEM: M7-L01's OWN DOCUMENTED RETRIEVAL MISS
============================================================================
  Query: 'Do you pay staff a reward for suggesting people who then join the team?'
  (M7-L01 section 3's own reworded referral-bonus query -- documented
  there as a clean retrieval MISS: every chunk scored 0.000.)

    P1: 0.000
    P2: 0.000
    P3: 0.000
    P4: 0.000
    P5: 0.000
    P6: 0.000

  All zero, confirmed again here -- BM25 has no literal term to match
  P4's actual wording ('refer', 'bonus', 'hire') against this query's
  actual wording ('reward', 'suggesting', 'join'). This lesson fixes
  this from the QUERY side, rather than the retrieval-method side
  (M6-L04/M6-L11's job).

============================================================================
2. QUERY EXPANSION: ADDING SYNONYMS TO BRIDGE THE GAP
============================================================================
  Original query terms (stopwords removed): ['pay', 'staff', 'reward', 'suggesting', 'people', 'join', 'team']
  Expanded query terms (synonyms added):    ['pay', 'staff', 'reward', 'suggesting', 'people', 'join', 'team', 'bonus', 'refer', 'referring', 'hire', 'hire', 'employment']

    P1: 0.000
    P2: 0.000
    P3: 0.000
    P4: 9.948  <-- was 0.000, now found
    P5: 0.000
    P6: 0.000

  Documents with any real (non-zero) match after expansion: ['P4'] -- every other document is still an untouched tie at 0.000, not a genuine second result.
  Adding synonyms for the query's OWN words -- not touching the corpus
  or the retrieval algorithm at all -- gave BM25 literal terms to match
  against P4's actual vocabulary. This is the same underlying gap M6-L04/
  M6-L11 address from the RETRIEVAL side (dense embeddings, hybrid fusion);
  query expansion is a complementary, often cheaper, query-side fix.

============================================================================
3. QUERY REWRITING: A FOLLOW-UP THAT NEEDS CONVERSATION CONTEXT
============================================================================
  Turn 1: 'How many days of PTO does a Junior employee get?'
  Turn 2 (follow-up): 'What about the Mid tier?'

  Retrieving turn 2 IN ISOLATION, terms: ['what', 'about', 'mid', 'tier']
    P1: 0.000
    P2: 0.000
    P3: 0.000
    P4: 0.000
    P5: 0.000
    P6: 0.000
  Every document scores exactly 0.000 -- there is no meaningful top result at all (all zero: True), only an arbitrary tie.

  Rewritten using turn 1's context: 'What is the PTO accrual for Mid tier employees?'
  Terms: ['what', 'pto', 'accrual', 'mid', 'tier', 'employees']
    P1: 0.072
    P2: 0.075
    P3: 2.085
    P4: 0.077
    P5: 0.077
    P6: 0.080
  Top-1: ['P3'] (score 2.085)

  'What about the Mid tier?' carries no topic of its own at all -- 'PTO'
  only exists in the CONVERSATION, not in this turn's own words. Rewriting
  the follow-up to explicitly restate the carried-over topic (M5-L10's
  conversation-state discipline, applied here to retrieval specifically)
  turns an unanswerable, context-free fragment into a query retrieval can
  actually work with. M7-L17 covers this in depth for longer, multi-turn
  conversations; this is the mechanism in miniature.

============================================================================
4. QUERY DECOMPOSITION: ONE COMPOUND QUESTION, TWO SEPARATE RETRIEVALS
============================================================================
  Compound query: 'What is the remote work policy and how much is the referral bonus?'
  Terms: ['what', 'remote', 'work', 'policy', 'how', 'much', 'referral', 'bonus']

    P1: 5.133
    P2: 0.075
    P3: 0.066
    P4: 3.924
    P5: 0.077
    P6: 0.080
  Top-2 as ONE query: ['P1', 'P4']

  Decomposed into two sub-queries, retrieved SEPARATELY:
    Sub-query 1: 'What is the remote work policy?' -> top-1: P1 (score 5.133)
    Sub-query 2: 'How much is the referral bonus?' -> top-1: P4 (score 3.847)

  Documents found -- one compound query: {'P4', 'P1'}; two decomposed sub-queries: {'P4', 'P1'}
  Both approaches happen to find the same two documents here, but for a
  DIFFERENT reason: the compound query's terms all get scored TOGETHER
  in one BM25 pass, so a document strongly matching only HALF the
  question competes, in the same ranking, against one matching the
  OTHER half -- decomposition instead guarantees each half gets its OWN
  dedicated top-1, regardless of how the two topics compare to each other.

============================================================================
5. THE COST OF QUERY TRANSFORMATION
============================================================================
  Every technique in this lesson buys its fix with extra retrieval work:

    Raw query:              1 retrieval pass
    Expanded query:         1 retrieval pass (more query terms, same pass count)
    Rewritten query:        1 retrieval pass (same count, but needs a rewriting
                             step first -- an extra LLM call in a real system)
    Decomposed (2 parts):   2 retrieval passes (roughly 2x retrieval cost)
    Decomposed (N parts):   N retrieval passes (cost scales with N)

  Expansion and rewriting change WHAT is searched for, at roughly the
  same retrieval cost as the original query. Decomposition changes HOW
  MANY searches happen -- a real, linear cost increase with the number
  of sub-questions, on top of whatever it costs (an LLM call, in a real
  system) to decide how to decompose the question in the first place.

============================================================================
6. WHAT THIS LAB IS AND IS NOT
============================================================================
  REAL: every BM25 score in this lab is computed with M6-L03's exact,
  unmodified formula; the expansion synonyms and rewritten/decomposed
  queries are hand-authored, but the retrieval scores they produce are
  genuinely computed, not asserted; the before/after fix in section 2
  reproduces M7-L01's own documented failure and then genuinely resolves it.

  MOCK / ILLUSTRATIVE: this lab's 'rewriting' and 'decomposition' are
  hand-authored strings, not generated by a real LLM call. A real system
  typically uses a model to perform expansion, rewriting, and
  decomposition dynamically -- this lab demonstrates that the RESULTING
  retrieval improvement is real, without claiming the transformation
  step itself was automated here.

  NOT SHOWN: how a real system decides WHEN to rewrite, expand, or
  decompose a query (versus passing it through unchanged); combining
  decomposed sub-query results into one coherent final answer (M7-L11's
  context assembly, M7-L12's generation); and multi-turn conversational
  retrieval at depth, which is M7-L17's dedicated topic.

Done.
```

### 7.3 Reading the result

**Section 1-2 together are this lesson's strongest argument, precisely because they are not a new
example.** Reproducing M7-L01's own documented failure and then genuinely resolving it (P4: 0.000 → 9.948)
demonstrates a real fix to a real, previously-identified problem, rather than a fix to a problem
constructed to be easy to solve.

**Section 3's "all zero, no meaningful top result" finding matters more than it might first appear.** It
would have been easy to report *some* top-1 result for the isolated follow-up and let a reader assume
retrieval "sort of" worked. Reporting the honest tie instead makes the failure — and the size of the fix —
unambiguous.

**Section 4 is a subtler point than sections 1-3, and worth re-reading.** The compound and decomposed
approaches found the *same* documents here — the lesson isn't that decomposition changes the outcome in
this specific case, but that it changes the *reliability* of getting that outcome, by removing a
competition that didn't need to exist.

---

## 8. Common mistakes and troubleshooting

1. **Assuming a retrieval miss must be fixed on the retrieval-method side (embeddings, hybrid search).**
   §5.1-§5.2 — the same failure can often be fixed more cheaply from the query side instead, or alongside.
2. **Retrieving a conversational follow-up using only its own words.** §5.3 — a follow-up's actual topic
   frequently lives in prior turns, not in the follow-up itself.
3. **Making conversation history available to generation but not to retrieval.** §6 — rewriting needs
   history at the retrieval stage, before the query is ever scored.
4. **Scoring a compound, multi-part question as a single query without considering decomposition.** §5.4 —
   this can create unnecessary competition between documents that each answer only part of the question.
5. **Treating query decomposition as free.** §5.5 — its cost scales linearly with the number of
   sub-queries, on top of the cost of deciding how to decompose in the first place.
6. **Debugging a conversational retrieval failure by reviewing the generation prompt first.** §6 — check
   what was actually retrieved (and with what query) before suspecting reasoning or generation.

| Symptom | Likely cause | Fix |
|---|---|---|
| A query using different wording than the source document returns no results | A literal-match retrieval method (BM25) has no term overlap to work with | Apply query expansion (§5.1-§5.2) or a semantic retrieval method (M6-L04, M6-L11) |
| A follow-up question in a conversation retrieves irrelevant or no results | The follow-up carries no topic of its own; retrieval saw only that turn's words | Rewrite the follow-up using conversation history before retrieval (§5.3, §6) |
| A compound question's answer is incomplete, missing one part of a multi-part query | The compound query's terms compete in one ranking, disadvantaging a document answering only part of it | Decompose into sub-queries and retrieve each separately (§5.4) |
| Retrieval latency or cost increased after adding query transformation | Decomposition (or an added rewriting/expansion model call) increases the number of retrieval passes or model calls | Confirm the accuracy gain justifies the added cost for your use case (§5.5) |

---

## 9. Security, privacy, reliability, cost

- **Reliability.** Apply query expansion when a retrieval miss is traced to a vocabulary gap between the
  query and the source documents' actual wording (§5.1-§5.2).
- **Reliability.** Make conversation history available to the retrieval stage, and rewrite follow-up
  queries before retrieval, not only before generation (§5.3, §6).
- **Reliability.** Decompose compound questions into sub-queries when a single query's terms might
  disadvantage a document that only answers part of it (§5.4).
- **Cost.** Account for decomposition's linear cost increase (one retrieval pass per sub-query) and any
  model-call cost for the rewriting/decomposition step itself before adopting it broadly (§5.5).

---

## 10. Exercises

### Exercise 1 — Beginner (~20 min)

1. In one sentence, why did the original referral-bonus query score 0.000 across the whole corpus?
2. How did query expansion fix that specific failure, without changing the corpus or the algorithm?
3. Why did the isolated follow-up "What about the Mid tier?" fail completely?
4. What does query decomposition guarantee that scoring a compound query as one pass does not?
5. Name one real cost query decomposition adds that expansion and rewriting do not.

### Exercise 2 — Intermediate (~40 min)

1. Run the lab. Confirm §7.2's score jump (0.000 → 9.948) and §7.4's compound vs. decomposed results on
   your own machine.
2. Add a new synonym mapping to §7.2's dictionary and construct a different mismatched query that it
   fixes.
3. Construct a three-turn conversation (not two) where the third turn needs context from both prior
   turns, and write the correctly rewritten query.
4. Construct a compound query with THREE parts (not two) and decompose it into three sub-queries,
   confirming each retrieves its intended document.
5. Using §7.5's method, compute the total retrieval-pass cost for a 4-part decomposed query compared to a
   single compound query, and state the multiplier.

### Exercise 3 — Challenge (~50 min)

1. Implement a simple rule-based query classifier that decides whether a query needs expansion,
   rewriting, decomposition, or no transformation at all, based on simple heuristics (e.g. presence of
   "and," pronoun references, very short queries).
2. Design and implement a synonym-expansion dictionary built automatically from a corpus (e.g. co-occurring
   terms), rather than hand-authored, and test it on a new mismatched query.
3. Extend §7.3's rewriting example to a three-turn conversation with a topic switch partway through, and
   design the rewriting logic needed to handle it correctly.
4. Research (conceptually) how a real system might use an LLM to perform query decomposition dynamically,
   and design the prompt you would use to decompose a compound question into sub-queries.
5. Using this lesson's §6 worked example as a model, design a test suite that would catch conversational
   retrieval failures (like the "what about" bug) before they reach users.

---

## 11. Quiz

*(Answers: [`answer-keys/module-07-answers.md`](../../answer-keys/module-07-answers.md#m7-l09).)*

**Q1.** Per §7.1, why did every document score 0.000 for the original reworded referral-bonus query?

- A. The lab's corpus was accidentally left empty.
- B. This reproduces M7-L01's own documented finding — the query shares no literal content terms with P4's actual wording after stopword removal, and BM25 can only match literal terms.
- C. BM25 cannot process queries longer than five words.
- D. The documents were deleted before the query ran.

**Q2.** Per §7.2, how did query expansion fix this specific retrieval miss?

- A. By deleting the documents that didn't match and re-running the query.
- B. By changing BM25's underlying mathematical formula for this specific query.
- C. By translating the query into a different language first.
- D. By adding synonyms for the query's own words (without touching the corpus or retrieval algorithm), giving BM25 literal terms that actually matched P4's vocabulary.

**Q3.** Per §7.2, is query expansion a fix on the retrieval side or the query side, and how does it relate
to M6-L04/M6-L11?

- A. It's a query-side fix, complementary to retrieval-side fixes like dense embeddings or hybrid fusion (M6-L04/M6-L11), which address the same underlying vocabulary gap differently.
- B. It replaces the need for BM25 or any retrieval algorithm entirely.
- C. It is identical to and interchangeable with hybrid search (M6-L11).
- D. It only works when the corpus contains fewer than ten documents.

**Q4.** Per §7.3, why did retrieving the follow-up "What about the Mid tier?" in isolation fail
completely?

- A. The retrieval system was not configured correctly for follow-up questions.
- B. BM25 cannot process questions phrased with "what about."
- C. The follow-up carries no topic of its own — "PTO" (the actual subject) only exists in the prior conversation turn, not in the follow-up's own words.
- D. The corpus does not contain any information about the Mid tier at all.

**Q5.** Per §7.3, how was the follow-up query fixed?

- A. By ignoring the follow-up entirely and re-answering turn 1 instead.
- B. By rewriting it to explicitly restate the carried-over topic from the conversation history, turning a context-free fragment into a self-contained, retrievable query.
- C. By translating the follow-up into a different language.
- D. By deleting turn 1 from the conversation history.

**Q6.** Per §7.4, why can a compound query's terms scored together in one BM25 pass create a problem a
decomposed query avoids?

- A. Compound queries can never be scored by BM25 under any circumstances.
- B. This problem only occurs when a compound query contains exactly two parts.
- C. BM25 refuses to process any query containing the word "and."
- D. A document strongly matching only half the question competes, in the same ranking, against a document matching the other half, whereas decomposition guarantees each half gets its own dedicated retrieval.

**Q7.** Per §7.4's measured result in this specific lab, did decomposition find different documents than
the single compound query?

- A. No — both approaches found the same two documents in this specific case, but decomposition guarantees this by construction rather than by how the topics happened to compare in one combined ranking.
- B. Yes, decomposition found two entirely different documents than the compound query did.
- C. Decomposition found zero documents, while the compound query found two.
- D. The compound query found four documents, while decomposition found only one.

**Q8.** Per §7.5, what is the real cost difference between query expansion/rewriting and query
decomposition?

- A. Both techniques always cost exactly the same amount, with no difference at all.
- B. Query decomposition always costs less than a single compound query.
- C. Expansion and rewriting keep retrieval cost roughly the same (one pass, with more or different terms); decomposition multiplies retrieval cost by the number of sub-queries.
- D. Query expansion always requires more retrieval passes than decomposition does.

**Q9.** Per §7.5, what additional real-system cost does query rewriting typically require beyond the
extra retrieval pass?

- A. A completely new corpus that must be re-ingested from scratch.
- B. An LLM call (or equivalent) to actually perform the rewriting itself, in a real (non-lab) system.
- C. A new BM25 index built specifically for rewritten queries.
- D. Additional storage space proportional to the size of the original corpus.

**Q10.** Per §7.6, what is explicitly mock/illustrative about this lab's rewriting and decomposition?

- A. The BM25 formula itself, which this lesson computes exactly as in M6-L03.
- B. The corpus documents, which are unchanged from M7-L01.
- C. The stopword-removal logic, which is identical to M7-L01's.
- D. The rewritten and decomposed queries, which are hand-authored strings, not generated by a real LLM call, though the retrieval scores they produce are genuinely computed.

**Q11.** Which topic does this lesson explicitly leave to M7-L17?

- A. Multi-turn conversational retrieval at depth — this lesson only shows the mechanism in miniature, for a single follow-up turn.
- B. The BM25 formula, which this lesson covers directly instead.
- C. Query expansion, which this lesson covers directly instead.
- D. Query decomposition, which this lesson covers directly instead.

**Q12.** What is the general lesson this lab demonstrates about fixing retrieval failures?

- A. Retrieval failures can only ever be fixed by changing the retrieval algorithm itself.
- B. Query-side fixes always make retrieval-method improvements (M6-L04, M6-L11) completely unnecessary.
- C. Some retrieval failures (vocabulary gaps, missing conversational context, compound questions) can be fixed on the query side, before retrieval ever runs, as a complement to fixing them on the retrieval-method side.
- D. Every retrieval failure has exactly one correct fix, and no two techniques can ever be combined.

**Q13.** *(Written, rubric-graded.)* In under 150 words: your RAG system handles single-turn questions
well but performs poorly on conversational follow-ups like "what about the other one?" Based on this
lesson, what is happening, and what would you implement to fix it?

---

## 12. Revision notes

- **A vocabulary-mismatch retrieval failure can be fixed from the query side, without touching the corpus
  or retrieval algorithm** — measured directly: M7-L01's own documented 0.000-score failure jumped to
  9.948 after query expansion alone.
- **Query expansion is complementary to, not a replacement for, retrieval-method fixes** (dense embeddings,
  hybrid fusion) — both address the same underlying gap from different sides of the pipeline.
- **A conversational follow-up can carry no retrievable topic of its own** — measured directly: every
  document scored exactly 0.000 for an isolated follow-up whose actual subject existed only in the prior
  turn; rewriting it using conversation history produced a clear, correct top result.
- **Scoring a compound question's terms together can create unnecessary competition between documents that
  each answer only part of it** — decomposition guarantees each sub-question its own dedicated retrieval,
  a structural improvement even when, as measured here, the outcome happens to match the compound query's.
- **Query expansion and rewriting cost roughly one retrieval pass, same as the original query; decomposition
  costs one pass per sub-query, a real linear cost increase.**
- **Some retrieval failures are best fixed on the query side, as a complement to (not a substitute for)
  retrieval-method improvements** — the two are not competing approaches.

---

## 13. Completion checklist

- [ ] I can fix a vocabulary-mismatch retrieval failure using query expansion.
- [ ] I can implement query rewriting to resolve a conversational follow-up.
- [ ] I can implement query decomposition and explain what it guarantees over a single compound query.
- [ ] I can distinguish query-side fixes from retrieval-method fixes as complementary approaches.
- [ ] I account for the real cost (extra retrieval passes, model calls) each technique adds.
- [ ] I check retrieval input (and the query that produced it) before suspecting generation when a
      conversational answer is wrong.
- [ ] I scored 10/13 on the quiz.

---

## 14. References

- Anthropic documentation, prompt engineering guidance relevant to query reformulation. `[UNVERIFIED]`
- Pinecone, *Query Transformations for RAG* (general survey of expansion/rewriting/decomposition
  techniques). `[UNVERIFIED]`

---

## 15. Next lesson

→ M7-L10 — Retrieval and Reranking in the RAG Loop

You now have query-side fixes for vocabulary gaps, missing context, and compound questions. Next: putting
retrieval and reranking (M6-L03, M6-L04, M6-L11, M6-L12) into the actual RAG loop end to end, with the
query-side techniques from this lesson feeding directly into it.
