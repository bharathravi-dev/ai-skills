# M7-L18 — Agentic Retrieval and Graph RAG

| | |
|---|---|
| **Lesson ID** | M7-L18 |
| **Difficulty** | 3 (Advanced) |
| **Estimated study time** | 2.0 hours |
| **Prerequisites** | [M7-L17](M7-L17-conversational-multihop-retrieval.md) |

---

## 1. Learning objectives

1. **Implement** a decision function that determines whether a query needs retrieval at all, connecting
   to M7-L02's tool-vs-retrieval framework.
2. **Implement** agentic multi-hop retrieval, where a second retrieval pass happens only when a
   sufficiency check on the first result fails.
3. **Represent** a small set of facts as an explicit knowledge graph, and implement direct edge traversal
   to answer a question M7-L17 needed two text-retrieval passes for.
4. **Explain** the real trade-off between graph RAG and text retrieval — precision and directness versus
   the upfront cost and completeness limits of graph construction.
5. **Distinguish**, in this lesson's own lab, hand-coded decision rules from what a real agentic system's
   model-driven judgment would do.

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **Agentic retrieval** | A retrieval pipeline where the decision to retrieve, and how many times, is made dynamically based on the model's own judgment rather than a fixed sequence of steps. |
| **Sufficiency check** | An evaluation of whether currently retrieved information is enough to answer a question, used to decide whether further retrieval is needed. |
| **Knowledge graph** | An explicit representation of entities and the relationships between them, typically as (subject, relation, object) triples. |
| **Edge traversal** | Following a relationship (edge) from one entity (node) to another in a graph, to answer a query directly rather than by searching text. |
| **Entity/relation extraction** | The process of reading unstructured text and producing structured (subject, relation, object) facts to populate a knowledge graph. |

---

## 3. Plain-language explanation

### 3.1 M7-L17 hard-coded a two-hop chain; this lesson makes the chain decide itself

M7-L17 always performed exactly two retrieval passes for its multi-hop example, whether or not two were
actually needed. This lesson replaces that fixed sequence with a decision made at each step — and
separately, replaces the underlying text search itself with something that doesn't need to search at all
for facts a graph already represents directly.

### 3.2 The first decision: retrieve or not?

§7.1 revisits M7-L02's tool-vs-retrieval question from the other direction: instead of a human designer
choosing the right approach per task type in advance, a decision function (standing in for a real agent's
judgment) makes the same call per query, at run time.

### 3.3 The second decision: is what I found enough?

§7.2 is this lesson's central mechanism: a real sufficiency check on the first retrieved result decides
whether a second pass happens at all. For a one-hop question, this same agent would stop after one pass —
the two-hop behavior isn't hard-coded, it's earned by the first result actually failing the check.

### 3.4 The same facts, represented so hops become lookups

§7.3 takes M7-L17's exact underlying facts and represents them as an explicit graph. The two-hop text
retrieval chain becomes two direct edge lookups — no scoring, no ranking, no reading text to extract an
entity by hand.

### 3.5 A graph is only as good as what built it

§7.4 is honest about graph RAG's real cost: someone (or some real extraction process) had to read the
original text and produce the graph's edges in the first place — and a fact never captured as an edge is
just as unreachable through the graph as a vocabulary-mismatched query makes a fact unreachable through
text search.

---

## 4. Analogy

**Asking a concierge who knows the building, versus wandering the halls reading every door label.** A
fixed retrieval pipeline is like reading every door label on every floor, every single time, regardless of
what you're looking for. An agentic pipeline is a concierge who first asks themselves "do I even need to
check the directory for this," and, if so, checks it, reads the result, and decides on the spot whether
that's enough or whether they need to check something else next. A knowledge graph is that concierge
having already memorized "reception is on floor 2, and floor 2's supervisor is Maria" — for exactly the
relationships they've memorized, no searching is needed at all; for anything outside what they've
memorized, they're back to reading door labels.

### Where the analogy breaks

- **A concierge's memory updates naturally as they learn the building.** §7.4's graph-completeness problem
  has no easy equivalent — a real knowledge graph does not update itself as new facts appear; it requires a
  deliberate extraction process.
- **A human concierge exercises genuine judgment about sufficiency.** §7.2's `is_sufficient()` is a small,
  hand-coded rule — a real agent's equivalent judgment comes from the model itself, not a fixed keyword
  check.

---

## 5. Detailed technical explanation

### 5.1 Deciding whether to retrieve at all

`[REAL mechanism, illustrative rule]` §7.1 ran two queries through a simple decision function. An
arithmetic question ("What is 15% of 200?") was correctly routed to skip retrieval entirely — computed
directly, no document needed, exactly M7-L02's plain-tool case. A policy question was correctly routed to
retrieve. **A fixed pipeline retrieves unconditionally; an agentic one makes this choice per query.**

### 5.2 Deciding whether to retrieve again

`[REAL, measured]` §7.2 ran M7-L17's own multi-hop question through an agent that checks sufficiency after
each pass. The first pass's top result (ORG1, "managed by Priya Shah") **failed the sufficiency check** —
it identifies the manager but says nothing about the actual policy. Only because of that failure did a
second pass run, using the entity extracted from the first result — and that second pass **passed the
sufficiency check**, so the agent stopped. **The critical difference from M7-L17's own lab**: that pipeline
always ran exactly two hops, correct or not; this agent's second hop is *earned*, triggered by an actual
failed check on the first result, and for a question answerable in one hop, the same agent would stop
after one pass.

### 5.3 The same facts, as a graph

`[REAL]` §7.3 represented M7-L17's exact underlying facts as four (subject, relation, object) edges. The
same question that needed two scored, ranked text-retrieval passes in M7-L17 was answered here by **two
direct edge lookups**: `Engineering --managed_by--> Priya Shah`, then `Priya Shah --has_policy--> flexible
location, no restriction`. **No scoring, no ranking, no reading retrieved text to manually extract an
entity** — provided the fact already exists as an edge.

### 5.4 What graph RAG costs, and where it fits

`[REAL reasoning]` §7.4 states the trade-off plainly: graph traversal's precision and speed for
already-represented relationships is real, but the graph itself required an upfront extraction step this
lab's hand-built `GRAPH_EDGES` skipped entirely. **A fact never captured as an edge is unreachable through
the graph** — the same shape of failure M7-L01 first demonstrated for vocabulary-mismatched text queries,
now recurring at the graph-construction level instead. **The practical pattern in real systems is usually
both together**: a graph for well-defined, known relationship types; text retrieval (M6-L03–M6-L12,
M7-L01–M7-L17) for everything else, open-ended and unanticipated.

### 5.5 Assumptions and limitations

- `needs_retrieval()` and `is_sufficient()` are small, hand-coded rules standing in for a real agent's
  judgment — in a real system (M5-L08's tool-calling pattern), an LLM itself decides whether and when to
  retrieve, not a fixed keyword check.
- `GRAPH_EDGES` was hand-built directly from M7-L17's already-known facts, not extracted from text by any
  real process — this lesson does not demonstrate entity/relation extraction itself.
- This lesson does not run a real agent loop where a model actually issues tool calls and reads their
  results (M5-L08 and Module 9's agentic-AI material cover this in depth), nor combine graph traversal
  with text retrieval in one hybrid pipeline.

---

## 6. Worked example — the knowledge graph that quietly went stale

**The system.** A company builds a knowledge graph from its HR documents to answer "who manages X" and
"what is Y's policy" questions precisely and instantly, extracted once during a project six months ago.

**What went wrong.** Several team reorganizations happened since the graph was built. The graph
confidently, instantly, and *incorrectly* answered "who manages Engineering" with the name of a manager
who had left the role months earlier — the underlying HR documents had been updated, but the graph, built
once and never re-extracted, had no mechanism to notice.

**Why this differs from a typical retrieval staleness bug.** Per M7-L16's propagation lesson, a text-based
index has a relatively direct path to staying current: re-chunk and re-embed the updated document. A graph
has an *extra* step in between — the updated text has to be *re-extracted* into updated edges, and if that
extraction step isn't triggered by the same update event, the graph can be stale even while the underlying
source documents are perfectly current.

**Three defects:**

| # | Defect | Consequence |
|---|---|---|
| 1 | Graph extraction ran once, as a one-time project, with no ongoing process | Every subsequent document update had no path to updating the graph at all |
| 2 | No mechanism linked document updates (M7-L16's propagation chain) to graph re-extraction | The graph's staleness was invisible until a wrong answer was reported |
| 3 | The graph was trusted as authoritative with no fallback to the underlying text | A stale edge produced a confident, instant, wrong answer with no signal anything was off |

### The fix

**Treat graph extraction as an ongoing process, triggered by the same document-update events M7-L16
covered**, not a one-time project — a graph is a derived artifact with the same propagation requirements as
any other index.

**Consider a fallback to text retrieval when graph confidence is uncertain**, rather than trusting the
graph as unconditionally authoritative.

**Monitor graph edges against their source documents periodically**, as a safety net for extraction gaps
that event-driven propagation alone might miss, the same discipline M7-L16 recommended for cached
citations.

**The general rule.** **A knowledge graph is a derived index like any other — it inherits the exact same
staleness and propagation risks M6-L10 and M7-L16 already established for text indexes and caches, and
needs the same ongoing maintenance, not a one-time build.**

---

## 7. Practical activity

**File:** [`labs/m7/l18_agentic_retrieval_graph_rag.py`](../../labs/m7/l18_agentic_retrieval_graph_rag.py)

**No API key, no network, no third-party dependencies.** Runs in well under a second.

```bash
source .venv/bin/activate
python labs/m7/l18_agentic_retrieval_graph_rag.py
```

### 7.2 Expected output

`[EXECUTED]` — 2026-09-10, Python 3.10.11 (pure standard library).

```text
============================================================================
1. AGENTIC RETRIEVAL: DECIDING WHETHER TO SEARCH AT ALL
============================================================================
  Query: 'What is 15% of 200?'
    Agent decision: SKIP RETRIEVAL -- use a tool instead (M7-L02)
    (15% of 200 = 30.0 -- computed directly, no document needed)

  Query: 'What is the PTO policy?'
    Agent decision: RETRIEVE

  A FIXED pipeline retrieves for every query, whether or not retrieval
  is actually the right tool for it (M7-L02's entire point). An agentic
  pipeline makes this decision per query -- here, with a simple rule;
  in a real system, with the model's own judgment about what it needs.

============================================================================
2. AGENTIC RETRIEVAL: DECIDING WHETHER TO RETRIEVE AGAIN
============================================================================
  Query: "Does the Engineering team's manager allow employees to be based from home?"
  First retrieval pass -- top result: ORG1 (score 2.138): 'The Engineering team is managed by Priya Shah.'
  Agent's sufficiency check: does this text actually address the policy question? False

  Agent decision: NOT sufficient -- this is a fact about WHO manages
  the team, not the policy itself. Retrieve AGAIN, using an entity
  extracted from what was just found (M7-L17's exact mechanism, now
  triggered by the agent's own judgment rather than a fixed, always-
  two-hop pipeline).
  Second retrieval pass (query='Priya Shah'): top result ORG2 (score 1.835): 'Priya Shah allows staff to work from any location without restriction.'
  Sufficiency check again: True -- agent stops here.

  The KEY difference from M7-L17's own two-hop lab: there, the pipeline
  ALWAYS performed exactly two hops, whether or not two were needed.
  Here, the SECOND retrieval only happens because the agent's own
  sufficiency check on the FIRST result came back negative -- for a
  query answerable in one hop, this same agent would stop after pass 1.

============================================================================
3. GRAPH RAG: THE SAME FACTS, REPRESENTED AS A GRAPH
============================================================================
  The exact same facts M7-L17's text corpus contained, represented as
  explicit (subject, relation, object) edges:

    (Engineering) --[managed_by]--> (Priya Shah)
    (Sales) --[managed_by]--> (Tom Reyes)
    (Priya Shah) --[has_policy]--> (flexible location, no restriction)
    (Tom Reyes) --[has_policy]--> (central office required, no exception)

  Query: "Does the Engineering team's manager allow employees to be based from home?"
  Graph traversal, following edges directly:
    Engineering --managed_by--> ['Priya Shah']
    Priya Shah --has_policy--> ['flexible location, no restriction']

  Answer, found by following two EDGES rather than two separate TEXT
  RETRIEVAL passes: 'flexible location, no restriction'

  M7-L17's version of this exact question needed two full retrieval
  passes -- score every document, extract an entity by reading text,
  score every document again. Here, the same two 'hops' are two
  dictionary/edge lookups -- exact, instant, and requiring no scoring
  or ranking at all, PROVIDED the fact is already represented as an
  edge in the graph.

============================================================================
4. WHEN GRAPH RAG WINS, AND WHAT IT COSTS TO GET THERE
============================================================================
  Graph traversal is exact and direct for relationship questions the
  graph already represents -- 'who manages X', 'what policy does Y
  have' become lookups, not searches. This is a real, structural
  advantage over M7-L17's text-based multi-hop chain for EXACTLY this
  class of question.

  But the graph didn't build itself. Someone (or some real extraction
  pipeline, using an LLM or a named-entity/relation-extraction model)
  had to read the ORIGINAL text and produce these exact (subject,
  relation, object) triples -- a real, upfront cost this lab's
  hand-built GRAPH_EDGES list skips entirely. A graph is also only as
  complete as its extraction: a fact never captured as an edge is as
  unreachable through the graph as it would be unreachable through a
  vocabulary-mismatched text query (M7-L01's original finding, in a
  new form).

  The practical shape: text retrieval (M6-L03-M6-L12, M7-L01-M7-L17)
  handles open-ended, unanticipated questions over raw documents with
  no extraction step; graph RAG handles a KNOWN set of relationship
  types precisely and cheaply, once built. Many real systems use both
  -- a graph for well-defined relationships, text retrieval for
  everything else.

============================================================================
5. WHAT THIS LAB IS AND IS NOT
============================================================================
  REAL: BM25 scoring is M6-L03's exact formula; the graph traversal in
  section 3 is genuine dictionary/edge lookup over real, stated data;
  the agent's two-pass decision in section 2 is genuinely computed,
  not scripted to always take two passes.

  ILLUSTRATIVE: needs_retrieval() and is_sufficient() are small,
  hand-coded rules standing in for a real agent's judgment -- in a
  real system (M5-L08's pattern), an LLM itself decides whether and
  when to call a retrieval tool, not a fixed keyword check. GRAPH_EDGES
  was hand-built directly from M7-L17's known facts, not extracted
  from text by any real process.

  NOT SHOWN: a real agent loop where a model actually issues tool
  calls and reads their results (M5-L08, M9's agentic-AI module covers
  this in depth); real entity/relation extraction from unstructured
  text to build a graph; and combining graph traversal with text
  retrieval in one hybrid pipeline, a natural extension left to the
  exercises.

Done.
```

### 7.3 Reading the result

**Section 2's `False` sufficiency check on the first pass is the entire mechanism in one boolean.** It
would be easy to build an agent that always does two passes "to be safe" — this lesson's version does the
harder, more honest thing: it does exactly as many passes as its own check on the results actually
justifies.

**Section 3's answer arriving with no BM25 score at all is worth noticing explicitly.** Nothing in the
graph traversal resembles retrieval the way this whole module has used the word — it's pure, deterministic
lookup, and that absence of scoring is exactly graph RAG's advantage for the specific questions it covers.

**Section 4 is the honest counterweight, and it matters as much as section 3's speed.** A lab that only
showed graph traversal's win would leave a false impression that graphs are simply better — the real
comparison requires weighing that speed against a real, non-trivial construction and maintenance cost.

---

## 8. Common mistakes and troubleshooting

1. **Retrieving unconditionally for every query, regardless of whether it needs retrieval at all.** §5.1 —
   an agentic decision (or, at minimum, a task-type router) avoids this, per M7-L02's original point.
2. **Hard-coding a fixed number of retrieval hops rather than checking sufficiency after each one.** §5.2 —
   this either wastes passes on questions that needed only one, or stops too early on questions that
   genuinely needed more.
3. **Treating a knowledge graph as complete simply because it exists.** §5.4 — a graph is only as complete
   as its extraction process; unrepresented facts are as unreachable as vocabulary-mismatched text queries.
4. **Building a knowledge graph once and never updating it.** §6 — graph extraction needs the same ongoing
   propagation discipline M7-L16 established for indexes and caches.
5. **Trusting graph traversal as unconditionally authoritative with no fallback.** §6 — a stale or
   incomplete graph can produce a confident, instant, wrong answer with no signal anything is off.
6. **Assuming graph RAG replaces text retrieval entirely.** §5.4 — the two are typically complementary,
   covering different classes of question in the same real system.

| Symptom | Likely cause | Fix |
|---|---|---|
| A retrieval pipeline performs unnecessary searches for queries answerable without any document | No decision step exists to route away from retrieval for tasks that don't need it | Add an agentic (or rule-based) decision step, per §5.1 and M7-L02 |
| A multi-hop pipeline always performs the same fixed number of retrieval passes | No sufficiency check exists to determine when enough information has been found | Add a sufficiency check after each pass, stopping as soon as it passes (§5.2) |
| A graph-based answer is confidently wrong despite the source documents being correct | The graph was extracted once and never updated as source documents changed | Trigger graph re-extraction from the same document-update events M7-L16 covers (§6) |
| A question the graph "should" be able to answer returns nothing | The relevant fact was never captured as an edge during extraction | Fall back to text retrieval, and treat the gap as an extraction-completeness issue (§5.4) |

---

## 9. Security, privacy, reliability, cost

- **Cost.** Route queries away from retrieval entirely when they don't need it (§5.1), avoiding unnecessary
  retrieval cost for tasks a plain tool or direct computation can handle (M7-L02).
- **Cost.** Use a sufficiency check to bound multi-hop retrieval to exactly as many passes as needed
  (§5.2), rather than a fixed count that may over- or under-retrieve.
- **Reliability.** Treat a knowledge graph as a derived index requiring the same ongoing propagation
  discipline as any other (M7-L16), not a one-time build (§6).
- **Reliability.** Maintain a fallback to text retrieval for questions a graph's extraction never captured,
  since graph completeness is never guaranteed (§5.4).

---

## 10. Exercises

### Exercise 1 — Beginner (~20 min)

1. In one sentence, what decision does §7.1's agentic pipeline make that a fixed pipeline does not?
2. What triggered the second retrieval pass in §7.2, specifically?
3. How many hops did the graph traversal in §7.3 need, and how does that compare to M7-L17's text-based
   approach?
4. What real cost does building a knowledge graph require that this lab's own graph skipped?
5. Name one situation where text retrieval is preferable to graph RAG, per §7.4.

### Exercise 2 — Intermediate (~40 min)

1. Run the lab. Confirm §7.2's sufficiency-check results and §7.3's graph traversal on your own machine.
2. Add a query that is answerable in exactly one hop, and confirm the agent from §7.2 correctly stops
   after a single pass.
3. Add a new entity, team, and policy to the graph, and construct a two-hop query that correctly traverses
   it.
4. Construct a query whose answer requires a fact NOT represented as an edge in the graph, and design a
   fallback that routes it to text retrieval instead.
5. Using M7-L16's propagation framework, design (conceptually) how graph edge updates should be triggered
   when a source document changes.

### Exercise 3 — Challenge (~50 min)

1. Implement a combined pipeline that tries graph traversal first and falls back to M7-L17's text-based
   multi-hop retrieval when the needed edge doesn't exist.
2. Design and implement a three-hop graph traversal example, and extend §7.4's stopping-condition
   discussion (from M7-L17) to graph traversal specifically.
3. Research (conceptually) how a real entity/relation extraction system might build a graph from
   unstructured text, and what error types (missed entities, wrong relations) it would need to handle.
4. Implement a simple graph-completeness checker that compares the graph's entities against the original
   corpus and reports any entity mentioned in text but absent from the graph.
5. Using this lesson's §6 worked example as a model, design a monitoring process that would catch a stale
   graph edge before it produces a wrong answer.

---

## 11. Quiz

*(Answers: [`answer-keys/module-07-answers.md`](../../answer-keys/module-07-answers.md#m7-l18).)*

**Q1.** Per §7.1, what decision does an agentic pipeline make that a fixed pipeline does not?

- A. Whether to display results in a different font or color.
- B. Whether retrieval is actually the right tool for a given query at all, rather than always retrieving regardless of whether the query needs it.
- C. Whether to delete the corpus after answering a query.
- D. Whether to translate the query into a different language before processing it.

**Q2.** Per §7.1's measured result, why did the arithmetic query skip retrieval entirely?

- A. Because the corpus was empty and no documents were available to retrieve.
- B. Because BM25 cannot process queries containing numbers.
- C. Because the retrieval system crashed before completing the query.
- D. It was recognized as answerable directly by computation (a plain tool, M7-L02's case), with no document needed at all.

**Q3.** Per §7.2, what triggered the second retrieval pass?

- A. The agent's own sufficiency check on the first result's text came back negative — it identified who manages the team but said nothing about the actual policy asked about.
- B. The first retrieval pass returned zero documents of any kind.
- C. The user explicitly requested a second retrieval pass.
- D. The corpus was updated with new documents between the first and second pass.

**Q4.** Per §7.2, what is the key difference between this lesson's agentic two-pass retrieval and
M7-L17's own two-hop pipeline?

- A. M7-L17's pipeline never performed more than one retrieval pass under any circumstances.
- B. This lesson's agent always performs exactly two passes, identical to M7-L17's pipeline.
- C. M7-L17's pipeline always performed exactly two hops regardless of whether two were needed; this lesson's agent only performs the second pass because its own sufficiency check on the first result failed.
- D. There is no difference at all between the two approaches.

**Q5.** Per §7.3, what does graph traversal replace, for a question the graph already represents?

- A. The need for a document store to exist at all.
- B. The two full text-retrieval passes (scoring, ranking, and reading text to extract an entity) that M7-L17 needed, with two direct, exact edge lookups instead.
- C. The need for any relationship between entities to exist in the underlying facts.
- D. The BM25 scoring formula, which graph traversal also depends on internally.

**Q6.** Per §7.3's measured result, how many "hops" did the graph traversal require to answer the same
question M7-L17 needed two retrieval passes for?

- A. Zero hops; the graph answered the question without any traversal at all.
- B. Four hops, twice as many as the text-based approach needed.
- C. An unlimited, unbounded number of hops with no defined stopping point.
- D. Two edge lookups — the same number of logical hops, but as exact dictionary/edge lookups rather than scored, ranked text retrieval passes.

**Q7.** Per §7.4, what real cost does building a knowledge graph require that this lab's hand-built graph
skipped?

- A. An upfront extraction step (using an LLM or a named-entity/relation-extraction process) to read the original text and produce the actual (subject, relation, object) triples.
- B. No cost at all; graphs build themselves automatically from any text corpus with no additional process.
- C. The cost of purchasing a specialized graph database license.
- D. The cost of translating the corpus into a different programming language.

**Q8.** Per §7.4, what happens to a fact that was never captured as an edge in the graph?

- A. It is automatically inferred and added to the graph without any human or model involvement.
- B. It becomes more findable than it would be through text retrieval, not less.
- C. It becomes unreachable through the graph, in the same way a vocabulary-mismatched query makes a fact unreachable through text retrieval — a graph is only as complete as its extraction.
- D. The entire graph becomes unusable and must be rebuilt from scratch.

**Q9.** Per §7.4, what is the described practical relationship between graph RAG and text retrieval in
real systems?

- A. Graph RAG always completely replaces text retrieval in any real system that adopts it.
- B. Many real systems use both together — a graph for well-defined, known relationship types, and text retrieval for open-ended, unanticipated questions.
- C. Text retrieval always completely replaces graph RAG in any real system that adopts it.
- D. The two approaches can never be used together in the same system under any circumstances.

**Q10.** Per §7.5, what do `needs_retrieval()` and `is_sufficient()` stand in for in a real agentic
system?

- A. A real, live database connection used to store the corpus itself.
- B. The BM25 scoring function, renamed for this specific lesson.
- C. An actual HTTP server that this lab starts and runs during execution.
- D. An LLM's own judgment about whether and when to call a retrieval tool, rather than a fixed keyword-based rule.

**Q11.** Per §7.5, what does this lesson explicitly NOT demonstrate?

- A. A real agent loop where a model actually issues tool calls and reads their results, and real entity/relation extraction from unstructured text to build a graph.
- B. BM25 scoring, which this lesson computes exactly as in M6-L03.
- C. Graph edge traversal, which this lesson performs directly and genuinely.
- D. The two-pass agentic decision process, which this lesson performs directly and genuinely.

**Q12.** What is the general lesson this lab demonstrates about agentic retrieval and Graph RAG?

- A. Agentic retrieval and Graph RAG are entirely unrelated techniques with no shared underlying purpose.
- B. A fixed, always-the-same retrieval pipeline is always superior to both agentic retrieval and Graph RAG in every case.
- C. Both are ways of moving past a fixed, always-the-same retrieval pipeline — agentic retrieval by deciding dynamically whether and how much to retrieve, and Graph RAG by replacing scored text search with exact traversal for relationships the graph already captures, each with its own real cost.
- D. Graph RAG eliminates the need for any retrieval decision-making of any kind, agentic or otherwise.

**Q13.** *(Written, rubric-graded.)* In under 150 words: your team built a knowledge graph six months ago
for "who manages X" queries, and it just gave a confidently wrong answer after a recent reorganization.
Based on this lesson, what happened, and what would you propose?

---

## 12. Revision notes

- **An agentic pipeline decides whether to retrieve at all**, rather than retrieving unconditionally —
  measured directly: an arithmetic query correctly skipped retrieval entirely, routed to direct
  computation instead (M7-L02).
- **An agentic pipeline decides whether to retrieve again, based on a sufficiency check on what it already
  found** — measured directly: the second pass in this lesson's lab ran only because the first result
  failed its sufficiency check, unlike M7-L17's fixed two-hop pipeline.
- **A knowledge graph represents facts as explicit (subject, relation, object) edges**, letting
  relationship questions be answered by direct traversal instead of scored, ranked text search — measured
  directly: the same question M7-L17 needed two retrieval passes for was answered here with two edge
  lookups and no scoring at all.
- **Graph construction has a real, upfront extraction cost this lesson's hand-built graph skipped** — a
  real graph requires reading source text and producing accurate edges, typically via an LLM or a
  relation-extraction process.
- **A fact never captured as an edge is unreachable through the graph** — the same shape of failure as a
  vocabulary-mismatched text query, now occurring at the graph-construction stage instead.
- **A knowledge graph is a derived index with the same staleness and propagation risks as any other** (M6-
  L10, M7-L16) — it requires ongoing maintenance triggered by source updates, not a one-time build.

---

## 13. Completion checklist

- [ ] I can implement a decision function for whether a query needs retrieval at all.
- [ ] I can implement agentic multi-hop retrieval, where a sufficiency check determines whether a second
      pass runs.
- [ ] I can represent a small set of facts as a knowledge graph and implement direct edge traversal.
- [ ] I can explain the real trade-off between graph RAG's precision and its construction/maintenance cost.
- [ ] I treat a knowledge graph as a derived index requiring ongoing propagation, not a one-time build.
- [ ] I distinguish, in any lab or system, hand-coded decision rules from real model-driven agentic
      judgment.
- [ ] I scored 10/13 on the quiz.

---

## 14. References

- Anthropic documentation, guidance on tool use and agentic patterns (M5-L08's foundation for this
  lesson's agentic decisions). `[UNVERIFIED]`
- Edge, D. et al., *From Local to Global: A Graph RAG Approach to Query-Focused Summarization*, 2024
  (general reference on Graph RAG). `[UNVERIFIED]`

---

## 15. Next lesson

→ M7-L19 — Evaluating RAG: Retrieval vs Answer, Groundedness, Correctness, Completeness

You now have two ways to move past a fixed retrieval pipeline. Next: measuring, rigorously, whether any of
Module 7's techniques — from ingestion through agentic retrieval — actually improved anything at all.
