# M7-L01 — RAG Architecture End to End

| | |
|---|---|
| **Lesson ID** | M7-L01 |
| **Difficulty** | 2 (Intermediate) |
| **Estimated study time** | 1.75 hours |
| **Prerequisites** | [M6-L13](../module-06-embeddings-search/M6-L13-retrieval-metrics.md), M5-L07 |

---

## 1. Learning objectives

1. **Explain** why a language model cannot correctly answer questions about private, company-specific
   information from its parametric knowledge alone.
2. **Trace** a query through a complete, minimal RAG pipeline: ingestion, chunking, indexing, retrieval,
   context assembly, and generation.
3. **Demonstrate** that a RAG system's answer quality has a hard ceiling set by its retrieval quality, not
   its generation step.
4. **Map** each stage of the full RAG architecture to the specific lesson (in Module 6 or Module 7) that
   covers it in depth.
5. **Distinguish**, in this lesson's own lab, what is genuinely executed from what stands in for a real
   language model call.

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **Parametric knowledge** | What a language model "knows" as a result of its training data, encoded in its weights — fixed at training time, and blind to anything not in that data. |
| **Retrieval-Augmented Generation (RAG)** | An architecture that retrieves relevant documents at answer time and supplies them to a model as context, rather than relying only on parametric knowledge. |
| **Closed-book** | A model answering a question with no supporting retrieved context — parametric knowledge only. |
| **Grounded answer** | An answer produced from, and traceable to, specific retrieved source content, typically with a citation. |
| **Retrieval ceiling** | The fact that a RAG system's answer can only be as good as the documents its retrieval stage actually found — no generation-side technique can recover information that was never retrieved. |

---

## 3. Plain-language explanation

### 3.1 Module 6 built retrieval; this lesson puts it in a full system

Every lesson in Module 6 — embeddings, BM25, ANN search, hybrid fusion, reranking, evaluation metrics —
built one piece of a larger machine. This lesson assembles a minimal, working version of that machine end
to end, and gives the whole architecture a name and a map before Module 7 spends the next nineteen lessons
on its individual stages.

### 3.2 Why bother retrieving anything at all?

§7.1 answers this directly, not abstractly: a question about one company's actual parental leave policy
cannot be answered correctly by a general-purpose model that was never shown that company's documents. No
clever prompt (Module 5) changes this — the information required simply does not exist in the model's
parameters. This is RAG's entire reason for existing.

### 3.3 The minimal pipeline, made concrete

§7.2 builds the smallest version of a RAG system that still does something real: split documents into
chunks, index them with BM25 (M6-L03, unchanged), retrieve the top matches for a query, assemble them into
a context block, and generate an answer that cites its source. Every step here is genuinely executed except
the very last one, which is explicitly a template standing in for a real model call (§7.5).

### 3.4 Retrieval sets the ceiling on everything downstream

§7.3 is this lesson's central argument. The same pipeline, given a question phrased with different
words than the source document, fails to retrieve the relevant chunk at all — and the generation step,
correctly, has nothing to work with. This is not a generation failure. It is a retrieval failure that looks
like a generation failure from the outside, and distinguishing the two is a skill this whole module builds.

### 3.5 A map for the rest of the module

§7.4 closes the lesson with a table connecting every pipeline stage — ingestion, chunking, metadata,
indexing, query rewriting, retrieval, reranking, context assembly, generation, abstention, evaluation — to
the specific lesson that covers it properly. This lesson is deliberately shallow everywhere except
retrieval, where Module 6 already did the work.

---

## 4. Analogy

**A research assistant answering questions using only what they memorized in school, versus one sent to
the actual filing cabinet first.** Ask the first assistant a question about your company's specific
internal policy, and they will confidently guess based on what's typical elsewhere — sometimes reasonable,
often wrong, and with no way for you to tell which. Ask the second assistant the same question, and they
first go find the actual policy document, read the relevant passage, and answer by quoting it, page number
included.

The second assistant isn't smarter. They didn't get better at reasoning. They just looked something up
before answering — and if the filing system is disorganized enough that they search under the wrong label
and find nothing, they come back with "I couldn't find anything about that," not a plausible-sounding
guess. Whether they succeed or fail depends entirely on the filing system, not on how good an assistant
they are.

### Where the analogy breaks

- **A human assistant can adapt their search strategy on the fly if a query fails.** §7.3's pipeline
  cannot, on its own — query rewriting to recover from exactly this situation is M7-L09's topic.
- **A human assistant reads with genuine comprehension.** This lesson's generation step (§7.5) is an
  explicit template, not comprehension — real generation quality and citation faithfulness is M7-L12's
  deeper topic.

---

## 5. Detailed technical explanation

### 5.1 The closed-book failure, precisely

`[MOCK, ILLUSTRATIVE]` §7.1 asked a question with one objectively correct, company-specific answer (twelve
weeks of paid parental leave) with no retrieved context available. The scripted closed-book response — "6
to 8 weeks, though this varies by employer" — is a plausible-sounding, generically-true-of-some-companies,
specifically-wrong-for-this-one answer. **This is not a transcript of any real model's actual output** —
it is a hand-written illustration of a well-known, general failure mode: a model asked about information
outside its training data can produce a confident, specific-sounding answer that happens to be incorrect,
precisely because "plausible" and "correct" are not the same property.

### 5.2 The pipeline, stage by stage

`[REAL]` §7.2 executed five stages on six synthetic company-policy documents:

1. **Ingestion + chunking** — 6 documents split into 15 sentence-level chunks (naive; M7-L06/M7-L07 cover
   real chunking strategy).
2. **Indexing** — BM25 (M6-L03's exact scoring formula) over all 15 chunks, with stopword removal added as
   realistic preprocessing (§5.5).
3. **Retrieval** — top-2 chunks by BM25 score for the query.
4. **Context assembly** — chunks scoring above a threshold concatenated into a context block (token
   budgeting is M7-L11's topic; this lesson uses a simple score cutoff).
5. **Generation** — `[MOCK]` a template function reads the **top-ranked retrieved chunk** and cites its
   source document.

The result: **the correct policy document (P5) was found, and the generated answer stated the real number
(twelve weeks) with a citation — not because generation "understood" anything, but because retrieval found
the right document and the template read directly from it.**

### 5.3 The same pipeline, a harder query, and a clean failure

`[REAL, measured]` §7.3 asked a question with the same intended meaning as P4 (the referral bonus policy)
but reworded with **no shared content word** at all after stopword removal. Every one of the 15 chunks
scored **exactly 0.000** — BM25 found nothing, because BM25 (M6-L03) can only match literal terms, and none
were shared. **The generation template correctly abstained** ("I don't have information about that in the
provided documents") rather than fabricating an answer.

**Read this precisely**: the generation step behaved exactly as it should, given what it was handed. The
failure happened one stage earlier, in retrieval — and from the outside, a user sees only "the system
didn't know the answer," with no way to tell, unqualified, whether that was a generation failure or a
retrieval failure. Diagnosing which one occurred is a recurring skill this module returns to (directly, in
M7-L20).

### 5.4 The full architecture, mapped to lessons

`[REAL]` §7.4 tabulated the complete pipeline:

| Stage | Covered in |
|---|---|
| Ingestion & parsing | M7-L03, M7-L04 |
| Cleaning & deduplication | M7-L05 |
| Chunking | M7-L06, M7-L07 |
| Metadata & provenance | M7-L08 |
| Embedding & indexing | M6-L01, M6-L02, M6-L05–M6-L08 |
| Query rewriting | M7-L09 |
| Retrieval & reranking | M6-L03, M6-L04, M6-L11, M6-L12, M7-L10 |
| Context assembly | M7-L11 |
| Generation & citations | M7-L12 |
| Abstention | M7-L13 |
| Evaluation | M6-L13, M7-L19 |

**Every stage after retrieval was a deliberate placeholder in this lesson's lab** — naive chunking, no
query rewriting, no reranking, a template instead of a model. This lesson's job was the shape of the whole
system and the specific claim that retrieval quality caps answer quality; each stage's own depth is a later
lesson's job.

### 5.5 Assumptions and limitations

- Stopword removal (§7.2's indexing step) was added as realistic preprocessing, not present in M6-L03's
  own lab — M6-L03 used a small, hand-picked corpus where this wasn't yet an issue; this lesson's more
  prose-like corpus needed it to avoid accidental stopword-driven matches on a small chunk set.
- The "generation" step throughout this lab is a hand-coded template (extract the top retrieved chunk,
  cite its source), not a real language model call — consistent with every lab in this course to date
  (COURSE_PLAN.md A4: an offline/mock path before any paid path).
- This lesson does not cover query rewriting, reranking integration, token-budgeted context assembly, or
  real citation-quality verification — each is a specific, later lesson in this module.

---

## 6. Worked example — the "the AI is wrong" ticket that was actually a retrieval bug

**The system.** A newly launched internal RAG assistant answers employee questions from company policy
documents. A support ticket comes in: "The AI told me PTO accrual is fifteen days a year regardless of
tenure — but I've been here four years and should get twenty." The on-call engineer opens the model
provider's console, checks recent prompt-engineering changes, and starts reviewing the generation prompt
for bugs.

**What was actually wrong.** After an hour of unproductive prompt review, the engineer instead logged what
context had actually been retrieved for that query — and found the retrieved chunk was the FIRST sentence
of the PTO policy ("full-time employees accrue fifteen days of PTO per year") without the SECOND sentence
("increasing to twenty days after three years of service"), because chunking had split the policy into
two separate chunks and only the first had been retrieved.

**Why the investigation started in the wrong place.** Per §5.3, a wrong answer that LOOKS like a reasoning
or generation failure is very often a retrieval or chunking failure wearing a generation-shaped costume.
The generation step did exactly what a template (or a real model) should: state what the provided context
said. The context itself was incomplete.

**Three defects:**

| # | Defect | Consequence |
|---|---|---|
| 1 | Chunking split a policy across a sentence boundary that separated a rule from its exception | Retrieval could return a factually incomplete, misleadingly confident answer |
| 2 | No logging captured what context was actually retrieved for a given answer | Debugging started at the generation step by default, wasting time |
| 3 | Nobody had tested the pipeline against multi-sentence, conditional policy language specifically | The failure mode wasn't caught before launch |

### The fix

**Always inspect the retrieved context first when a RAG answer is wrong**, per §5.3 — before assuming the
generation step is at fault, confirm what it was actually given to work with.

**Log retrieved chunks alongside every generated answer**, so a wrong answer can be traced back to its
actual source context rather than re-derived by guesswork after the fact.

**Test chunking against conditional and multi-clause source language specifically** (M7-L06/M7-L07's
topic) — a rule-and-exception pattern split across chunks is a realistic, recurring failure shape.

**The general rule.** **When a RAG system gives a wrong answer, check what was retrieved before you
suspect the model** — per §5.3's central finding, the generation step is frequently working correctly on
incomplete or incorrect input, not reasoning incorrectly on complete input.

---

## 7. Practical activity

**File:** [`labs/m7/l01_rag_pipeline_end_to_end.py`](../../labs/m7/l01_rag_pipeline_end_to_end.py)

**No API key, no network.** Runs in well under a second.

```bash
source .venv/bin/activate
python labs/m7/l01_rag_pipeline_end_to_end.py
```

### 7.2 Expected output

`[EXECUTED]` — 2026-09-10, Python 3.10.11 (pure standard library, no third-party dependencies).

```text
============================================================================
1. WHY RAG EXISTS: A MODEL CANNOT KNOW WHAT IT WAS NEVER SHOWN
============================================================================
  Query: 'How many weeks of paid parental leave do employees get?'
  No retrieval -- the model answers from parametric knowledge alone:

  [MOCK closed-book answer] 'Many companies offer around 6 to 8 weeks of paid parental leave, though this varies by employer.'

  This is a genuinely plausible-SOUNDING answer -- generically true of
  'many companies' -- and genuinely, specifically WRONG for whichever
  company this question was actually about, because no general-purpose
  model was ever trained on this company's internal policy documents.
  There is no amount of prompting skill (M5) that fixes this: the
  correct number simply is not in the model's parameters. RAG exists
  to solve exactly this -- not by making the model 'smarter', but by
  giving it the actual, relevant document at answer time.

============================================================================
2. THE PIPELINE, STAGE BY STAGE, ON REAL DOCUMENTS
============================================================================
  Step 1 -- INGESTION + CHUNKING: 6 documents split into 15 sentence-level chunks.
  Step 2 -- INDEXING: BM25 (M6-L03's exact formula, stopwords removed) over all 15 chunks.
  Step 3 -- RETRIEVAL: top 2 chunks for the query:
    P5#1  (score 5.535):  'Employees are eligible for twelve weeks of paid parental leave following the birth or adoption of a child, available to any employee with at least six months of tenure'
    P5#0  (score 5.312):  'Parental Leave Policy'

  Step 4 -- CONTEXT ASSEMBLY: 2 chunk(s) above threshold assembled into a context block (token budgeting is M7-L11's topic):
    '[P5#1] Employees are eligible for twelve weeks of paid parental leave following the birth or adoption of a child, available to any employee with at least six months of tenure\n[P5#0] Parental Leave Policy'

  Step 5 -- GENERATION: [MOCK grounded answer] 'Employees are eligible for twelve weeks of paid parental leave following the birth or adoption of a child, available to any employee with at least six months of tenure. (Source: P5)'

  Compare directly to section 1's closed-book answer: the closed-book
  mock invented a generic, wrong number. The retrieval-grounded pipeline
  found the ACTUAL policy document (P5) and answered with the real
  number (twelve weeks) plus a verifiable citation -- not because the
  generation step got smarter, but because it was given the right
  document to read from. This is RAG's entire value proposition in one
  side-by-side comparison.

============================================================================
3. RAG's QUALITY CEILING IS SET BY RETRIEVAL, NOT GENERATION
============================================================================
  Query: 'Do you pay staff a reward for suggesting people who then join the team?'
  This asks EXACTLY what P4 (Referral Bonus Policy) answers -- but using
  different words throughout: 'pay/reward' instead of 'bonus',
  'suggesting people' instead of 'refer', 'join the team' instead of
  'hire' -- no shared content word with P4's actual text at all.

    P1#0  (score 0.000):  'Remote Work Policy'
    P1#1  (score 0.000):  'Employees may work remotely up to three days per week with manager approval'

  Retrieved 0 chunk(s) above threshold.
  [MOCK generation output] "I don't have information about that in the provided documents."

  BM25 (M6-L03) scores by literal term overlap, and this query shares
  almost no literal terms with P4's actual wording -- exactly the
  vocabulary gap M6-L01 introduced and M6-L04/M6-L11 addressed with
  dense and hybrid retrieval. The generation step here did exactly what
  it should with no relevant context: it abstained (M7-L13's topic)
  rather than guessing. But notice what actually failed: not the
  generation template, and not the model's 'reasoning' -- the RETRIEVAL
  step never found the one document that had the real answer. Every
  technique in Module 6 (BM25, dense, hybrid, reranking) exists to make
  this specific failure less likely; no amount of generation-side
  cleverness (M5's prompting techniques) can answer a question from a
  document the pipeline never retrieved.

============================================================================
4. THE FULL ARCHITECTURE, AND WHERE EACH LESSON FITS
============================================================================
  This lab's five steps (ingest, chunk, index, retrieve, generate) are a
  minimal skeleton. The full pipeline this module builds toward:

  Stage                     Covered in
  Ingestion & parsing       M7-L03, M7-L04
  Cleaning & deduplication  M7-L05
  Chunking                  M7-L06, M7-L07
  Metadata & provenance     M7-L08
  Embedding & indexing      M6-L01, M6-L02, M6-L05-M6-L08
  Query rewriting           M7-L09
  Retrieval & reranking     M6-L03, M6-L04, M6-L11, M6-L12, M7-L10
  Context assembly          M7-L11
  Generation & citations    M7-L12
  Abstention                M7-L13
  Evaluation                M6-L13, M7-L19

  Every stage after 'retrieval' in this lab was a placeholder (naive
  chunking, a template generator, no reranking, no query rewriting).
  That is deliberate: this lesson's job is the shape of the whole
  pipeline and where retrieval quality caps answer quality, not the
  depth of any one stage -- each gets its own lesson from here.

============================================================================
5. WHAT THIS LAB IS AND IS NOT
============================================================================
  REAL: chunking is genuinely executed (naive, sentence-based); scoring
  is M6-L03's exact, unmodified BM25 formula, with standard stopword
  removal added as realistic preprocessing (this lesson's prose corpus
  is closer to real text than M6-L03's hand-picked one, where accidental
  stopword matches would otherwise dominate a small corpus); the
  vocabulary-mismatch retrieval failure in section 3 -- every score
  landing at exactly 0.000 -- is a real, measured BM25 outcome on this
  corpus, not scripted.

  MOCK: 'generation' in both sections 1 and 2 is a hand-coded
  template/extraction function, not a real LLM call. This matches
  every lab in this course to date -- none calls a real model API,
  consistent with this course's offline-first design (COURSE_PLAN.md A4).
  Section 1's closed-book answer is a scripted ILLUSTRATION of a
  plausible failure mode, not a transcript of any real model's output.

  NOT SHOWN: real chunking strategy (M7-L06/M7-L07), query rewriting
  (M7-L09), reranking integration (M7-L10, though M6-L12 built the
  mechanism), token-budgeted context assembly (M7-L11), and real
  citation-quality verification (M7-L12) -- each is this module's own
  upcoming lesson.

Done.
```

### 7.3 Reading the result

**Section 1 and Section 2 together are the entire pitch for RAG, made concrete rather than asserted.** The
same kind of question, closed-book versus retrieval-grounded, produces a wrong generic guess or a correct,
cited answer — and the only thing that changed between them is whether the right document was found first.

**Section 3 is the lesson's most important result, and it is deliberately not a success story.** A clean,
total retrieval miss (every score exactly 0.000) demonstrates, unambiguously, that the failure lives in
retrieval, not generation — the generation template did the right thing with what it was given.

**Section 4 is a map, not new content** — treat it as the syllabus for the rest of this module, and revisit
it after each subsequent lesson to place that lesson precisely within the whole system.

---

## 8. Common mistakes and troubleshooting

1. **Assuming a wrong RAG answer means the model "isn't smart enough."** §5.3, §6 — check what was
   retrieved first; the generation step is frequently correct given incomplete or wrong input.
2. **Expecting closed-book (no-retrieval) answers to be reliable for private or company-specific
   information.** §5.1 — this is architecturally impossible, not a prompting problem.
3. **Treating chunking, indexing, and retrieval as interchangeable "the search part."** §5.4 — each is
   its own lesson with its own failure modes; conflating them makes debugging harder, not easier.
4. **Not logging retrieved context alongside generated answers.** §6 — without this, every "wrong answer"
   investigation has to start by guessing where the fault lies.
5. **Assuming abstention ("I don't have that information") is itself a bug.** §5.3 — it is frequently the
   CORRECT behavior when retrieval genuinely found nothing relevant; the bug, if any, is upstream.
6. **Trying to fix a retrieval-caused failure by changing the generation prompt.** §6 — this cannot work if
   the relevant content was never in the context the model received.

| Symptom | Likely cause | Fix |
|---|---|---|
| A RAG answer is wrong or incomplete | The retrieved context was wrong, incomplete, or missing — not (necessarily) the generation step | Log and inspect retrieved chunks first, per §5.3, §6 |
| A closed-book (no-retrieval) answer is confidently wrong | The model has no access to the private information the question requires | This is expected; the fix is adding retrieval, not better prompting (§5.1) |
| A rephrased version of a working query suddenly fails | Vocabulary mismatch causing a literal-match retrieval method (BM25) to miss the relevant document | Apply Module 6's dense/hybrid retrieval (M6-L04, M6-L11) or query rewriting (M7-L09) |
| Debugging time is spent reviewing prompts with no result | The investigation started at generation instead of retrieval | Always check retrieved context first, per §6's worked example |

---

## 9. Security, privacy, reliability, cost

- **Reliability.** When a RAG answer is wrong, inspect the retrieved context before suspecting the
  generation step or the model itself — §5.3 and §6 both demonstrate the failure is frequently upstream.
- **Reliability.** Log the retrieved context alongside every generated answer in any real system — without
  this, debugging a wrong answer requires guesswork rather than inspection.
- **Reliability.** Treat abstention as a correct outcome when retrieval genuinely finds nothing relevant,
  not as a failure to be prompted away — forcing an answer without context reintroduces §5.1's closed-book
  risk deliberately.
- **Cost.** A minimal pipeline's cheapest stage (retrieval, largely already built in Module 6) is also the
  stage that determines whether the more expensive stage (a real generation call) has any chance of being
  correct — investing in retrieval quality has outsized leverage on overall system quality.

---

## 10. Exercises

### Exercise 1 — Beginner (~20 min)

1. In one sentence, why couldn't the closed-book mock in §7.1 give the correct parental leave figure?
2. List the five pipeline stages this lab implements, in order.
3. In one sentence, why did §7.3's query fail to retrieve anything relevant?
4. What did the generation step do correctly in §7.3, and why was that the right behavior?
5. Using §7.4's table, name which lesson covers "chunking" and which covers "reranking."

### Exercise 2 — Intermediate (~40 min)

1. Run the lab. Confirm §7.2's retrieval scores and §7.3's all-zero scores match your own run.
2. Write a third query (your own choice of policy and phrasing) against this lab's corpus and predict,
   before running it, whether BM25 will find the relevant chunk — then verify.
3. Add a seventh policy document of your own and a query that should retrieve it, and confirm the pipeline
   answers correctly with a citation.
4. Deliberately reword a working query (like §7.3 did) until retrieval fails, and record the smallest
   wording change that causes the failure.
5. Using §6's worked example as a model, write a one-paragraph incident report for a hypothetical RAG
   failure you design yourself, distinguishing what looked broken from what was actually broken.

### Exercise 3 — Challenge (~50 min)

1. Replace this lab's BM25 retrieval with cosine similarity over hand-built vectors (M6-L01 style) and
   compare which queries succeed or fail differently between the two retrieval methods.
2. Implement a simple logging structure that records, for every query, the retrieved chunk IDs and scores
   alongside the generated answer — the fix §6 recommends — and demonstrate using it to diagnose a
   deliberately introduced chunking bug.
3. Extend §7.4's stage table into a full architecture diagram (textual or drawn) showing data flowing
   through every stage, with this lesson's own five implemented stages highlighted against the full map.
4. Research (conceptually) at least one real, production RAG framework's default pipeline (e.g. its
   default chunking, retrieval, and generation stages) and compare its stage boundaries to this lesson's
   own.
5. Design an experiment that would distinguish, from the outside (without access to internal logs), whether
   a wrong RAG answer was a retrieval failure or a generation failure, using only the system's visible
   inputs and outputs.

---

## 11. Quiz

*(Answers: [`answer-keys/module-07-answers.md`](../../answer-keys/module-07-answers.md#m7-l01).)*

**Q1.** Why couldn't the closed-book mock answer in §7.1 give the correct, company-specific parental-leave
duration?

- A. The correct figure is private, company-specific information that was never part of any general-purpose model's training data — no amount of prompting skill can supply information the model was never given access to.
- B. The mock function had a bug that prevented it from accessing the number.
- C. The query was phrased ambiguously, confusing the model.
- D. Parental leave policies cannot be expressed as a specific number of weeks.

**Q2.** Per §7.1–§7.2's side-by-side comparison, RAG's fundamental value proposition is:

- A. Making the underlying language model itself more intelligent through better training.
- B. Replacing the need for any generation step at all.
- C. Guaranteeing that a model's answer is always grammatically correct.
- D. Giving the model access to the actual, relevant document at answer time, rather than relying on what happens to be in its parameters.

**Q3.** In §7.2, why was the parental-leave query answered correctly, with a citation?

- A. The mock generation step was specifically hard-coded to answer this one question correctly.
- B. BM25 retrieval found the actual policy chunk (P5) containing the real answer, and generation extracted from and cited that specific retrieved chunk.
- C. The model was fine-tuned on the company's policy documents in advance.
- D. The query happened to already contain the exact number "twelve".

**Q4.** In §7.3, why did BM25 retrieval fail to find P4 (the referral bonus policy) for the reworded
query?

- A. P4 had been accidentally deleted from the corpus before this query ran.
- B. BM25 has a hard limit of four documents it can search at once.
- C. The reworded query shared no literal content terms with P4's actual wording, and BM25 can only score documents by literal term overlap.
- D. The retrieval threshold was set impossibly high for any query to pass.

**Q5.** Per §7.5, why was stopword removal added to this lab's BM25 implementation?

- A. On a small corpus, a common word appearing by chance in only one chunk can get an artificially high IDF weight, creating accidental, meaningless matches — standard IR practice removes these first.
- B. To make the corpus smaller and the lab run faster.
- C. Because BM25 cannot process documents containing common words like "the" or "a" at all.
- D. To comply with a licensing requirement on the source documents.

**Q6.** In §7.3, when retrieval found no chunk above the relevance threshold, what did the mock generation
step do?

- A. It fabricated a plausible-sounding but incorrect number, the same as the closed-book mock in §7.1.
- B. It crashed with an unhandled error.
- C. It returned the single most frequently occurring sentence in the whole corpus regardless of relevance.
- D. It abstained, stating it didn't have the relevant information, rather than guessing or fabricating an answer.

**Q7.** Per §7.3's closing argument, the general lesson about RAG system failures is:

- A. Generation quality is always the limiting factor in a RAG system's overall answer quality.
- B. A RAG system's answer quality has a hard ceiling set by its retrieval quality — no amount of generation-side sophistication can answer from a document that was never retrieved.
- C. RAG systems never fail once retrieval has been implemented correctly.
- D. Abstaining is always a sign of a broken system that must be fixed immediately.

**Q8.** Per §7.4, the "retrieval & reranking" stage of the full RAG pipeline draws directly on which prior
lessons?

- A. M2-L09 and M3-L14 only.
- B. M4-L06 and M5-L11 only.
- C. M6-L03, M6-L04, M6-L11 and M6-L12, alongside this module's own M7-L10.
- D. M1-L01 through M1-L05 exclusively.

**Q9.** Why does this lesson's lab use a hand-coded template for "generation" instead of a real LLM API
call?

- A. This matches every lab in the course to date — none calls a real model API, consistent with the course's offline-first design.
- B. Real LLM APIs cannot be used for question-answering tasks.
- C. Generation is not actually part of a RAG pipeline.
- D. A template is always more accurate than a real language model.

**Q10.** What is the purpose of §7.4's stage-by-stage table mapping the RAG pipeline to specific lessons?

- A. To rank the lessons in this module by difficulty.
- B. To replace the need for reading any of the module's other lessons.
- C. To list every lesson in the entire course, not just this module.
- D. To provide an advance map of the whole pipeline, showing which upcoming lesson covers each stage in depth — this lesson's job is the overall shape, not depth in any one stage.

**Q11.** Section 7.1's closed-book mock answer ("many companies offer 6 to 8 weeks...") is best understood
as:

- A. A verified transcript of a real, specific language model's actual output on this exact query.
- B. A scripted illustration of a plausible, specific-sounding but incorrect failure mode, not a claim about any particular real model's behavior.
- C. Proof that all language models always fabricate incorrect numbers.
- D. The correct answer for every company's parental leave policy.

**Q12.** The single biggest risk this lesson identifies for a RAG system with excellent generation but weak
retrieval is:

- A. Higher cloud infrastructure costs from running two systems instead of one.
- B. It will always be slower than a closed-book model with no retrieval step at all.
- C. It will fail to answer correctly (or answer wrongly) on any question whose relevant document was not retrieved, no matter how good the generation step is.
- D. It cannot be combined with prompting techniques from Module 5 at all.

**Q13.** *(Written, rubric-graded.)* In under 150 words: your team is debugging a RAG system that gives a
wrong answer to a legitimate question. Based on this lesson, what is the first thing you would check, and
why, before assuming the generation step (the LLM) is at fault?

---

## 12. Revision notes

- **A model cannot correctly answer from private, company-specific information it was never shown** — no
  prompting technique changes this; it is an architectural limitation of parametric knowledge, not a
  skill gap. Demonstrated: a scripted closed-book answer produced a plausible but wrong, generic number.
- **RAG's value proposition is giving the model the right document at answer time**, not making the model
  itself smarter — demonstrated directly by the same kind of question succeeding once retrieval found the
  correct source and failing once it did not.
- **A RAG system's answer quality has a hard ceiling set by retrieval quality.** Measured: a reworded query
  sharing no literal terms with the correct source document produced a clean, total retrieval miss (every
  BM25 score exactly 0.000), and the generation step correctly abstained rather than guessing.
- **A wrong RAG answer is very often a retrieval or chunking failure wearing a generation-shaped costume**
  — always inspect what was actually retrieved before suspecting the model itself.
- **The full RAG architecture has eleven or so distinct stages**, each with its own dedicated lesson in
  Module 6 or Module 7 — this lesson's job was the shape of the whole system, not depth in any one part.
- **This lesson's "generation" step is a deterministic template, not a real model call** — consistent with
  every lab in this course, which stays offline-first by design.

---

## 13. Completion checklist

- [ ] I can explain why a model cannot answer correctly from private information it was never shown.
- [ ] I can trace a query through ingestion, chunking, indexing, retrieval, context assembly, and
      generation.
- [ ] I can explain why a RAG system's quality ceiling is set by retrieval, not generation.
- [ ] I check retrieved context first when a RAG answer is wrong, before suspecting the model.
- [ ] I can map each pipeline stage to the lesson (in Module 6 or Module 7) that covers it in depth.
- [ ] I can distinguish, in any RAG lab or system, what is genuinely executed from what stands in for a
      real model call.
- [ ] I scored 10/13 on the quiz.

---

## 14. References

- Lewis, P. et al., *Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks*, NeurIPS 2020 (the
  original RAG paper). `[UNVERIFIED]`
- Anthropic documentation, *Retrieval augmented generation*. <https://docs.anthropic.com/en/docs/build-with-claude/embeddings> `[UNVERIFIED]`

---

## 15. Next lesson

→ M7-L02 — RAG vs Fine-Tuning vs Long Context vs Plain Tools

You now have the whole RAG pipeline in view, and know precisely where its quality ceiling comes from. Next:
when RAG is the right architectural choice at all, versus fine-tuning, long-context prompting, or simpler
tool-based approaches — a decision this lesson's architecture map assumed but did not yet justify.
