# Module 7 — Answer Key

**Do not read this before attempting the questions.** Every answer carries a reason, and for multiple
choice, a reason each distractor fails.

> Module 7 quiz options are uniform in length with a balanced answer distribution, and carry no inline
> explanation of the correct choice. All rationale lives here.

| Lesson | Jump to |
|---|---|
| M7-L01 RAG Architecture End to End | [↓](#m7-l01) |
| M7-L02 RAG vs Fine-Tuning vs Long Context vs Plain Tools | [↓](#m7-l02) |
| M7-L03 Ingestion and Document Parsing | [↓](#m7-l03) |
| M7-L04 Hard Formats: PDFs, HTML, Tables, Scans and OCR | [↓](#m7-l04) |
| M7-L05 Cleaning, Normalisation and Deduplication | [↓](#m7-l05) |
| M7-L06 Chunking I: Size, Overlap and Document Boundaries | [↓](#m7-l06) |
| M7-L07 Chunking II: Fixed, Recursive, Sentence, Semantic, Structure-Aware | [↓](#m7-l07) |
| M7-L08 Metadata, Identifiers, Provenance and Versioning | [↓](#m7-l08) |
| M7-L09 Query Rewriting, Expansion and Decomposition | [↓](#m7-l09) |
| M7-L10 Retrieval and Reranking in the RAG Loop | [↓](#m7-l10) |
| M7-L11 Context Assembly and Token Budgets | [↓](#m7-l11) |
| M7-L12 Citations and Evidence Verification | [↓](#m7-l12) |
| M7-L13 Abstention: Teaching the System to Say "I Don't Know" | [↓](#m7-l13) |
| M7-L14 Conflicting, Duplicated and Outdated Sources | [↓](#m7-l14) |
| M7-L15 Permission-Aware Retrieval and Tenant Isolation | [↓](#m7-l15) |
| M7-L16 Incremental Updates and Deletion Propagation | [↓](#m7-l16) |
| M7-L17 Conversational and Multi-Hop Retrieval | [↓](#m7-l17) |
| M7-L18 Agentic Retrieval and Graph RAG | [↓](#m7-l18) |
| M7-L19 Evaluating RAG: Retrieval vs Answer, Groundedness, Correctness, Completeness | [↓](#m7-l19) |
| M7-L20 Debugging RAG, Adversarial Documents, Latency and Cost | [↓](#m7-l20) |

---

<a id="m7-l01"></a>
## M7-L01 — RAG Architecture End to End

**Answers: A · D · B · C · A · D · B · C · A · D · B · C**

| Q | Ans | Why, and why the distractors fail |
|---|---|---|
| 1 | **A** | The correct figure is private, company-specific information no general-purpose model was ever trained on, an architectural limit no prompting can overcome. **B**, **C** and **D** invent causes unrelated to why closed-book answering fails here. |
| 2 | **D** | The lesson's own side-by-side comparison shows the model unchanged; only the presence of the right retrieved document changed the outcome. **A**, **B** and **C** misstate what RAG actually does. |
| 3 | **B** | Retrieval found the real policy chunk, and the template extracted from and cited it directly — the mechanism the lesson demonstrates, not a special case. **A**, **C** and **D** invent explanations the lab's code does not support. |
| 4 | **C** | After stopword removal, the reworded query shared no literal term with P4's text, and BM25 can only match literal terms — reflected in every chunk scoring exactly 0.000. **A**, **B** and **D** name causes unrelated to the actual, measured mechanism. |
| 5 | **A** | On a small, prose-like corpus, a rare stopword confined to one chunk can receive an inflated BM25 IDF weight purely by chance, exactly the artifact the lesson's own development process encountered and fixed. **B**, **C** and **D** misstate BM25's actual capabilities or the real reason for the change. |
| 6 | **D** | With nothing scoring above threshold, the template correctly reported it had no relevant information rather than fabricating one, foreshadowing M7-L13. **A**, **B** and **C** describe behavior the lab's code does not exhibit. |
| 7 | **B** | This is the lesson's central, explicitly stated argument: retrieval sets the ceiling, and no generation-side sophistication recovers a document that was never found. **A**, **C** and **D** contradict this stated argument directly. |
| 8 | **C** | The lesson's own table names exactly these lessons for the retrieval-and-reranking stage. **A**, **B** and **D** name unrelated lessons the table does not list for this stage. |
| 9 | **A** | This lab follows the same offline-first pattern as every other lab in the course, per COURSE_PLAN.md's A4 assumption. **B**, **C** and **D** state claims the lesson does not make and that are not accurate in general. |
| 10 | **D** | The lesson explicitly frames the table as an advance map for the rest of the module, with this lesson covering shape rather than depth. **A**, **B** and **C** misstate the table's stated purpose. |
| 11 | **B** | The lesson explicitly labels this a scripted illustration of a plausible failure mode, not a real model transcript. **A**, **C** and **D** claim a status for this text the lesson explicitly denies. |
| 12 | **C** | This is the direct, general consequence of §5.3's retrieval-ceiling finding, stated as the lesson's practical risk. **A**, **B** and **D** name concerns the lesson does not identify as the central risk. |

**Q13 rubric (5 marks).** One mark each for: **naming the first check** — inspecting what context was
actually retrieved for the failing query, before reviewing the generation prompt or model behavior;
**explaining why retrieval is checked first** — because, per §5.3 and §6, a wrong answer frequently reflects
correct generation over incomplete or incorrect retrieved context, not faulty reasoning; **connecting this
to the lesson's own demonstrated mechanism** — a clean retrieval miss (or a chunking split that separates a
rule from its exception, as in §6) can produce an answer that looks like a generation failure from the
outside; **describing what confirming this would look like in practice** — logging or reproducing the
retrieved chunks for the specific failing query and checking they actually contain the correct information;
and **stating the practical consequence** — that only after ruling out retrieval as the cause does
investigating the generation step or prompt become a productive next move. An answer that jumps straight to
"check the prompt" without first proposing to inspect retrieved context scores 2.

---

<a id="m7-l02"></a>
## M7-L02 — RAG vs Fine-Tuning vs Long Context vs Plain Tools

**Answers: B · C · A · D · B · C · A · D · B · C · A · D**

| Q | Ans | Why, and why the distractors fail |
|---|---|---|
| 1 | **B** | RAG's defining property is selecting a small, relevant subset per query; long context's defining property is inserting everything, every time. **A**, **C** and **D** misstate or invert this structural difference. |
| 2 | **C** | Retrieval always returns the same top-k count, which is what keeps RAG's per-query cost flat regardless of corpus size. **A**, **B** and **D** name mechanisms the lesson's measurement does not rely on. |
| 3 | **A** | Long context has no selection step, so every document's tokens are paid for on every query, scaling directly with corpus size. **B**, **C** and **D** invent unrelated causes. |
| 4 | **D** | The lesson states this condition explicitly as where long context is legitimate rather than inferior. **A**, **B** and **C** name conditions the lesson never ties to this recommendation. |
| 5 | **B** | The lesson explicitly contrasts this with reliable factual recall, naming style/format/behaviour as fine-tuning's suited use. **A** is the opposite of what the lesson states. **C** and **D** are not claims the lesson makes. |
| 6 | **C** | RAG's verbatim retrieval is directly contrasted with fine-tuning's lossy, weight-based storage — the lesson's central mechanism for this distinction. **A**, **B** and **D** invent unrelated or false mechanisms. |
| 7 | **A** | This is the lesson's stated update-mechanism comparison, tying RAG to M6-L10's re-indexing and fine-tuning to a full retraining/evaluation cycle. **B**, **C** and **D** state false or invented claims. |
| 8 | **D** | The lesson's own framing: a deterministic, exactly computable task is solved directly and cheaply by a tool call, with neither RAG nor fine-tuning being the right shape of solution. **A**, **B** and **C** overstate or misstate the actual reasoning. |
| 9 | **B** | The lesson states directly that RAG would retrieve a document about the general topic, not compute the specific numeric answer itself. **A**, **C** and **D** contradict this stated outcome. |
| 10 | **C** | This is the exact situation the lesson's decision framework maps to RAG specifically. **A**, **B** and **D** map to plain tools, long context, and fine-tuning respectively in the same framework. |
| 11 | **A** | The lesson's closing point is explicit: these approaches combine in real systems rather than being an exclusive choice. **B**, **C** and **D** all assert an exclusivity the lesson explicitly denies. |
| 12 | **D** | Section 7.7 states plainly that no real fine-tuning run or large-scale long-context call is performed, and accuracy trade-offs are not measured. **A**, **B** and **C** describe things the lab does genuinely execute. |

**Q13 rubric (5 marks).** One mark each for: **naming the structural mismatch** — fine-tuning shifts model
weights toward learned patterns and is not a reliable mechanism for exact, verbatim factual recall, per
§5.3; **connecting this to the specific risk** — that a fine-tuned model asked about a specific policy
figure has no verbatim source to check itself against, unlike RAG's retrieved and cited text; **proposing
RAG (or RAG plus fine-tuning) instead** — retrieval preserves the ability to cite and verify exact facts,
addressing the colleague's actual goal; **acknowledging where fine-tuning could still help** — for shaping
tone, format, or response style, combined with RAG rather than replacing it, per §5.5's framework; and
**tying the recommendation to update cost** — noting that policies change and RAG's re-indexing (§5.4)
handles this far faster than a retraining cycle would. An answer that rejects fine-tuning outright without
acknowledging any legitimate role for it scores 3; an answer that only says "fine-tuning is worse" without
the mechanism scores 2.

---

<a id="m7-l03"></a>
## M7-L03 — Ingestion and Document Parsing

**Answers: A · D · B · C · A · D · B · C · A · D · B · C**

| Q | Ans | Why, and why the distractors fail |
|---|---|---|
| 1 | **A** | The specific byte was not valid UTF-8 on its own, so the decoder rejected it immediately rather than silently misreading it. **B**, **C** and **D** invent unrelated or false causes. |
| 2 | **D** | With no exception raised, there is no signal at all that anything went wrong, which is exactly what makes this case dangerous. **A**, **B** and **C** describe behavior that does not match a silent failure. |
| 3 | **B** | This is the exact fallback chain implemented and demonstrated recovering the original text correctly. **A**, **C** and **D** describe strategies the lab does not use and that would not solve the problem. |
| 4 | **C** | The lesson states this connection directly: structure preserved now is what chunking needs later to avoid splitting mid-topic. **A**, **B** and **D** are false or irrelevant claims about Markdown. |
| 5 | **A** | This is the lesson's stated purpose for normalization: one consistent shape regardless of source format. **B**, **C** and **D** misstate what the normalization actually solves. |
| 6 | **D** | This is the exact pair of properties (idempotence, change detection) the lesson demonstrates and states explicitly. **A**, **B** and **C** are false or irrelevant claims about content hashes. |
| 7 | **B** | The lab's own measured result: re-ingesting the same file twice produced identical IDs both times. **A**, **C** and **D** contradict this measured, printed result directly. |
| 8 | **C** | The lab measured a different hash after the edit, confirming change detection works as intended. **A**, **B** and **D** contradict this measured, printed result directly. |
| 9 | **A** | The lab's own output shows exactly this: the malformed file's error was caught and logged, and the other two sources were still ingested successfully. **B**, **C** and **D** contradict the lab's own printed results. |
| 10 | **D** | This is the lesson's stated reasoning for why batch-level failure handling is a poor design choice. **A**, **B** and **C** assert benefits the lesson does not claim and that do not follow from batch-level failure. |
| 11 | **B** | This is exactly what section 7.6 states these two specific lessons cover instead. **A**, **C** and **D** misstate which topics go to which lesson. |
| 12 | **C** | This is the lesson's own stated general conclusion, tying together every section's specific finding. **A**, **B** and **D** contradict the lesson's central argument or state an absolute the lesson does not support. |

**Q13 rubric (5 marks).** One mark each for: **acknowledging the premise without accepting the conclusion**
— agreeing most files may indeed be UTF-8, while noting "almost all" still leaves some that aren't;
**explaining the real risk precisely** — that some wrong-encoding reads fail silently rather than raising an
exception, per §5.1, so "we'd notice if it broke" does not hold in general; **connecting this to actual
measured behavior** — this lesson's own lab showed a wrong-encoding assumption succeeding without error on
some byte sequences while producing corrupted text; **proposing the low-cost fix** — a fallback encoding
chain (or a detection library), which costs little and directly closes this gap; and **naming the downside
of skipping it** — per §6's worked example, an undetected encoding bug can silently corrupt a meaningful
fraction of ingested data for months before anyone notices. An answer that only asserts "encoding bugs are
possible" without the silent-failure mechanism specifically scores 2.

---

<a id="m7-l04"></a>
## M7-L04 — Hard Formats: PDFs, HTML, Tables, Scans and OCR

**Answers: B · D · A · C · B · D · A · C · B · D · A · C**

| Q | Ans | Why, and why the distractors fail |
|---|---|---|
| 1 | **B** | PDF extraction has no concept of "boilerplate" built in; every line on every page is returned with equal status, which is why the header appeared once per page. **A**, **C** and **D** invent unrelated causes. |
| 2 | **D** | The footer's embedded page number made each occurrence textually distinct, so exact-match repetition detection never fired for it. **A**, **B** and **C** name causes unrelated to the actual, demonstrated mechanism. |
| 3 | **A** | The extracted text is confirmed to be a flat sequence with no row/column markers at all. **B**, **C** and **D** contradict the lab's own printed extraction result. |
| 4 | **C** | This is exactly the printed simulation result: the value ended up isolated from its label once the arbitrary cut fell mid-table. **A**, **B** and **D** contradict the lab's own printed chunk contents. |
| 5 | **B** | The naive extractor's output visibly mixed navigation, footer, and aside text with the real article content. **A**, **C** and **D** misstate what the comparison actually shows. |
| 6 | **D** | These are exactly the tags named in the extractor's `SKIP_TAGS` set and confirmed in the lab's output. **A**, **B** and **C** mis-list the actual set of skipped or kept tags. |
| 7 | **A** | The page contained only a raster image with no text objects, so there was no text data present to extract at all. **B**, **C** and **D** invent unrelated or false causes. |
| 8 | **C** | This is OCR's defining role, stated directly as the gap this section's empty-extraction result demonstrates. **A**, **B** and **D** overstate or misstate what OCR actually does. |
| 9 | **B** | The lesson states this plainly as a real, measured negative result, not a hidden or glossed-over one. **A**, **C** and **D** contradict the lesson's own stated finding. |
| 10 | **D** | This is the lesson's own explicitly stated, careful conclusion, including the call to test one's own tools and documents. **A**, **B** and **C** overgeneralize far beyond what one test on one tool can support. |
| 11 | **A** | The lesson names this specifically as M7-L05's topic in its own "what this lab is and is not" section. **B**, **C** and **D** name topics covered elsewhere (M7-L03, M7-L06/L07, M6-L13) not M7-L05. |
| 12 | **C** | This is the lesson's own stated general conclusion, drawn from all four sections' distinct findings. **A**, **B** and **D** contradict this conclusion or the evidence presented throughout the lesson. |

**Q13 rubric (5 marks).** One mark each for: **naming the table-flattening risk specifically** — that a
pricing table's extracted text loses row/column structure, and a chunk boundary can separate a tier or
item label from its associated value, per §5.2 and §6's worked example; **proposing a concrete test** —
deliberately querying for a fact that lives in a table cell and checking whether the retrieved chunk still
contains its label, not just its value; **naming the boilerplate risk** — checking whether repeated
headers/footers (e.g. a running contract header) are being stripped, and specifically whether page-varying
patterns like page numbers are also being caught, per §5.1; **proposing a check for text-layer presence** —
confirming that none of the contracts are scanned images with no text layer at all (§5.4), which would
ingest as empty; and **connecting this to the general principle** — that different hard formats fail in
different specific ways, so each risk needs its own explicit test rather than one general "does it look
right" check. An answer that only says "check the extraction looks correct" without naming a specific,
testable failure mode scores 2.

---

<a id="m7-l05"></a>
## M7-L05 — Cleaning, Normalisation and Deduplication

**Answers: C · A · D · B · C · A · D · B · C · A · D · B**

| Q | Ans | Why, and why the distractors fail |
|---|---|---|
| 1 | **C** | Unicode allows a precomposed code point and a base-plus-combining-mark sequence to render the same visible glyph while being different data. **A**, **B** and **D** invent unrelated or false causes. |
| 2 | **A** | A hash computed over unnormalized text captures this representational difference, producing different hashes for visually identical content. **B**, **C** and **D** overstate or misstate the actual consequence. |
| 3 | **D** | This is stated directly: whitespace noise adds no meaning while inflating token counts and diluting embeddings. **A**, **B** and **C** are false claims about what normalization does or requires. |
| 4 | **B** | The lab's own printed result: two of five documents collapsed as exact duplicates of a third. **A**, **C** and **D** contradict this measured, printed result. |
| 5 | **C** | Two genuinely different words make the documents genuinely different byte sequences, which an exact hash correctly reports. **A**, **B** and **D** invent unrelated or false explanations. |
| 6 | **A** | This is the lab's own measured table: Jaccard fell from 0.586 at k=3 to 0.355 at k=5 for the identical edit. **B**, **C** and **D** contradict this measured, printed result directly. |
| 7 | **D** | This is the lesson's own stated conclusion from the k-sensitivity finding. **A**, **B** and **C** assert absolutes the finding does not support. |
| 8 | **B** | The lab's own printed result: all three top results were exact copies of one document. **A**, **C** and **D** contradict this measured, printed result. |
| 9 | **C** | This is the lesson's own stated conclusion, directly following from section 5's measured before/after comparison. **A**, **B** and **D** understate or deny an effect the lesson explicitly measures. |
| 10 | **A** | Section 7.6 names this specifically as the natural next step not demonstrated here. **B**, **C** and **D** name techniques this lesson does demonstrate. |
| 11 | **D** | The lesson states this relationship explicitly: the same content-hash mechanism, now applied corpus-wide. **A**, **B** and **C** deny or misstate a relationship the lesson draws directly. |
| 12 | **B** | This is the lesson's own stated general conclusion, tying together every section's specific finding. **A**, **C** and **D** contradict this conclusion or the evidence presented throughout the lesson. |

**Q13 rubric (5 marks).** One mark each for: **checking for exact duplicates first** — running content-hash
deduplication (after normalizing Unicode form and whitespace, per §5.1–§5.3) across all three sources
together, not per source; **checking for near-duplicates specifically** — since a mirror site's headers,
footers, or light rewording will likely survive exact hashing, per §5.4, requiring shingling or a similar
similarity check; **proposing a concrete similarity technique and threshold** — shingling with Jaccard
similarity (or LSH/MinHash if the corpus is large, per §5.6), explicitly noting the threshold and shingle
size need calibration against this specific corpus; **connecting this to the actual symptom** — that
duplicate/near-duplicate crowding directly explains why searches surface copies instead of distinct
answers, per §5.5; and **proposing an ongoing policy, not a one-time fix** — deduplication should run as
part of ongoing ingestion, since new overlapping content will keep arriving from the same three sources.
An answer that proposes only "remove duplicates" without distinguishing exact from near-duplicate handling
scores 2.

---

<a id="m7-l06"></a>
## M7-L06 — Chunking I: Size, Overlap and Document Boundaries

**Answers: B · D · A · C · B · D · A · C · B · D · A · C**

| Q | Ans | Why, and why the distractors fail |
|---|---|---|
| 1 | **B** | A fixed character count has no concept of word or sentence boundaries by definition, which is exactly what the printed chunks show. **A**, **C** and **D** invent unrelated or false causes. |
| 2 | **D** | Mean pooling (M6-L01) averages every word's vector in the chunk, so unrelated topics measurably pull the pooled vector away from the query's specific axis. **A**, **B** and **C** invent causes unrelated to the actual, demonstrated mechanism. |
| 3 | **A** | The lab's own printed chunks show exactly this split, with the label in one chunk and the value in the next. **B**, **C** and **D** contradict the lab's own printed output. |
| 4 | **C** | The lab's own measured result: the no-overlap case never contains both together, and the overlap case does. **A**, **B** and **D** overstate or contradict what overlap actually did. |
| 5 | **B** | The lesson states this explicitly: overlap can only bridge a gap as large as the distance it spans, and this specific gap was unusually large. **A**, **C** and **D** invent unrelated or false explanations. |
| 6 | **D** | This is the lesson's own stated general conclusion from the 67%-overlap finding. **A**, **B** and **C** overstate or misstate what overlap actually guarantees. |
| 7 | **A** | The lab's own printed chunks show the fixed-size version splitting across the section boundary. **B**, **C** and **D** contradict the lab's own printed output. |
| 8 | **C** | The boundary-aware chunker explicitly splits at each heading, reusing the structure preserved during ingestion in M7-L03. **A**, **B** and **D** describe mechanisms the lab's code does not use. |
| 9 | **B** | The lab measured total stored characters growing substantially (up to +96.8% at 50% overlap), confirming this directly. **A**, **C** and **D** contradict this measured, printed result. |
| 10 | **D** | The lesson explicitly presents both findings as two sides of one trade-off to be weighed together, not as competing or contradictory claims. **A**, **B** and **C** each discard one side of a trade-off the lesson insists on holding together. |
| 11 | **A** | Section 7.7 names this specifically as M7-L07's dedicated topic. **B**, **C** and **D** name topics covered in other, unrelated lessons (M7-L03/M7-L05, M6-L13), not M7-L07. |
| 12 | **C** | This is the lesson's own stated general conclusion, tying together every section's specific measured finding. **A**, **B** and **D** contradict this conclusion or the evidence presented throughout the lesson. |

**Q13 rubric (5 marks).** One mark each for: **naming the mechanism, not "randomness"** — recognizing that
inconsistent per-fact accuracy is very likely deterministic, tied to specific chunk-boundary positions
relative to specific facts, not a random or flaky failure, per §5.3 and §6; **proposing a concrete check** —
locating exactly which chunk(s) contain the facts that fail, and checking whether a chunk boundary falls
between a label and its value; **connecting this to chunk size and overlap** — checking whether the current
overlap (if any) is large enough to bridge the specific gaps found, per §5.4; **proposing the structural
fix** — chunking by the document's own section/heading boundaries where available, per §5.5, rather than
tuning size or overlap indefinitely; and **proposing a systematic test**, per §6 — testing retrieval
specifically against facts positioned near likely chunk boundaries, not just easy, centrally-located ones,
to catch this class of failure before it reaches users. An answer that proposes only "increase chunk size"
without diagnosing the boundary-position mechanism first scores 2.

---

<a id="m7-l07"></a>
## M7-L07 — Chunking II: Fixed, Recursive, Sentence, Semantic, Structure-Aware

**Answers: C · A · D · B · C · A · D · B · C · A · D · B**

| Q | Ans | Why, and why the distractors fail |
|---|---|---|
| 1 | **C** | Recursive splitting explicitly tries the coarsest separator (paragraph break) first, only recursing into a finer one for pieces still over the size limit. **A**, **B** and **D** describe strategies the lab's code does not implement. |
| 2 | **A** | Recursive splitting works directly on punctuation and spacing already present in the text, unlike heading-based chunking which needed preserved markup. **B**, **C** and **D** invent requirements or effects the lesson does not describe. |
| 3 | **D** | The splitter's regex only recognizes punctuation, with no mechanism to except known abbreviations. **A**, **B** and **C** invent unrelated or false causes. |
| 4 | **B** | The lesson states this explicitly, naming abbreviations, initials, and decimal numbers as routine in real documents. **A**, **C** and **D** contradict this stated framing. |
| 5 | **C** | This is exactly the lab's measured mechanism: pooled-vector cosine similarity between adjacent sentences, dropping at the real topic shift. **A**, **B** and **D** describe mechanisms the lab's code does not use. |
| 6 | **A** | This is the lesson's own stated key advantage — no structural markup of any kind is required. **B**, **C** and **D** state false or invented constraints. |
| 7 | **D** | The lesson states this distinction directly: a code fragment is not valid or usable on its own, unlike an awkward prose fragment. **A**, **B** and **C** are false or irrelevant claims about code. |
| 8 | **B** | The lab's own measured, printed result shows exactly this outcome. **A**, **C** and **D** contradict the lab's own printed output. |
| 9 | **C** | This is the lesson's own stated conclusion from comparing all five strategies side by side. **A**, **B** and **D** assert absolutes the comparison does not support. |
| 10 | **A** | Section 7.6 names this specifically as not demonstrated, alongside the caveat that real systems use an exception list or trained model. **B**, **C** and **D** name things this lesson does demonstrate. |
| 11 | **D** | Section 7.6 states this explicitly, distinguishing the illustrative parameters from the real, production-used underlying mechanism. **A**, **B** and **C** contradict this stated distinction. |
| 12 | **B** | This is the lesson's own stated framing of its relationship to M7-L06 in the opening explanation. **A**, **C** and **D** deny or misstate a relationship the lesson draws directly. |

**Q13 rubric (5 marks).** One mark each for: **recommending different strategies per content type, not one
strategy for everything** — since the lesson's own worked example (§6) shows a single prose-tuned strategy
failing sharply on code and structured lists; **justifying prose handling** — recursive or sentence-based
(or semantic, if headings are sparse) splitting suits policy prose, per §5.1-§5.3; **justifying structured
content handling** — structure-aware chunking treating code blocks and ordered lists as indivisible units,
per §5.4, since a broken code fragment or an incomplete step list is a sharper failure than awkward prose;
**connecting this to the general principle** — that no single strategy is universally correct, and the
right choice depends on what is actually being chunked, per §5.5; and **proposing verification** — testing
retrieval specifically against both content types before trusting the pipeline, per §6. An answer that
proposes one single strategy for the whole mixed corpus without addressing the code/list risk specifically
scores 2.

---

<a id="m7-l08"></a>
## M7-L08 — Metadata, Identifiers, Provenance and Versioning

**Answers: D · B · A · C · D · B · A · C · D · B · A · C**

| Q | Ans | Why, and why the distractors fail |
|---|---|---|
| 1 | **D** | The lesson's own chunk record includes exactly these fields, each shown load-bearing elsewhere in the lesson. **A**, **B** and **C** contradict the lesson's own stated schema. |
| 2 | **B** | The lab's own measured scores were identical (1.000 for both), directly demonstrating this. **A**, **C** and **D** contradict the lab's own printed output. |
| 3 | **A** | This is exactly the filtering step the lab performed, reducing the candidate set to one chunk. **B**, **C** and **D** describe approaches the lesson does not use. |
| 4 | **C** | The lesson states this distinction directly, contrasting a checkable citation against an unverifiable one. **A**, **B** and **D** invert or deny this stated distinction. |
| 5 | **D** | The lab's own measured result: all 3 position-based IDs stayed the same string while referring to different text. **A**, **B** and **C** contradict the lab's own printed output. |
| 6 | **B** | This is the lesson's own stated reasoning for why a silent mismatch is worse than an ID simply changing. **A**, **C** and **D** deny or misstate this reasoning. |
| 7 | **A** | This is the precise, stated mathematical guarantee a content hash provides. **B**, **C** and **D** invent false or irrelevant properties. |
| 8 | **C** | The lab's own measured result: 0 hash-based IDs were shared after re-chunking, since boundaries moved; the guarantee is narrower than blanket stability. **A**, **B** and **D** contradict this measured, printed result. |
| 9 | **D** | The lesson explicitly frames its contribution as the schema, distinct from M6-L09's already-covered filtering mechanics. **A**, **B** and **C** misstate this stated relationship. |
| 10 | **B** | Section 7.6 names this specifically as M7-L16's topic. **A**, **C** and **D** name topics this lesson covers directly, not defers. |
| 11 | **A** | Section 7.6 names this specifically as M7-L15's topic, distinct from the department-tagging shown here. **B**, **C** and **D** name topics this lesson covers directly, not defers. |
| 12 | **C** | This is the lesson's own stated general conclusion, tying together every section's specific measured finding. **A**, **B** and **D** contradict this conclusion or the evidence presented throughout the lesson. |

**Q13 rubric (5 marks).** One mark each for: **directly rebutting the premise** — explaining that lexical
overlap ("relevance," as a retrieval score) is not the same as authority, and a stale chunk's wording does
not reliably become less RETRIEVABLE just because it is outdated, per §5.2's measured finding that a stale
and current chunk scored identically; **citing the specific measured evidence** — the 1.000/1.000 tie
between the old and new PTO figures for the same query; **explaining the real risk** — that without an
explicit currency flag, a naive pipeline can surface either version with equal confidence and a fully
plausible citation, exactly as shown in §6's audit example; **proposing the concrete fix** — an is_current
field, enforced and filtered on at query time, per §5.2; and **connecting this to citation trust** — noting
that even a correct answer is not verifiable without provenance metadata (§5.3), which "will just become
less relevant" does nothing to provide. An answer that only asserts "we need version metadata" without
addressing why relevance decay does not solve the problem scores 2.

---

<a id="m7-l09"></a>
## M7-L09 — Query Rewriting, Expansion and Decomposition

**Answers: B · D · A · C · B · D · A · C · B · D · A · C**

| Q | Ans | Why, and why the distractors fail |
|---|---|---|
| 1 | **B** | This is a direct reproduction of M7-L01's own documented failure: no literal term overlap remains after stopword removal, and BM25 can only score literal matches. **A**, **C** and **D** invent unrelated or false causes. |
| 2 | **D** | The lab's own measured result: adding synonyms for the query's terms alone raised P4 from 0.000 to 9.948, with nothing else changed. **A**, **B** and **C** describe mechanisms the lab's code does not use. |
| 3 | **A** | The lesson explicitly frames expansion as a query-side complement to M6-L04/M6-L11's retrieval-side fixes for the same underlying gap. **B**, **C** and **D** overstate or misstate this stated relationship. |
| 4 | **C** | The lesson states this directly: the follow-up's own words carry no topic, since the actual subject exists only in the prior turn. **A**, **B** and **D** invent unrelated or false causes. |
| 5 | **B** | This is exactly the rewriting step the lab performed, restoring a clear top result (P3, 2.085) from an all-zero tie. **A**, **C** and **D** describe approaches the lesson does not use. |
| 6 | **D** | This is the lesson's own stated mechanism for why compound scoring can disadvantage a partial-match document. **A**, **B** and **C** invent false constraints on BM25. |
| 7 | **A** | The lab's own measured result: identical document sets, found for a structurally different, more reliable reason under decomposition. **B**, **C** and **D** contradict the lab's own printed output. |
| 8 | **C** | This is the lesson's own stated cost comparison, directly following from the retrieval-pass counts in section 7.5. **A**, **B** and **D** invert or flatten a real, stated cost difference. |
| 9 | **B** | The lesson states this directly as the typical additional real-system cost beyond the extra retrieval pass itself. **A**, **C** and **D** invent unrelated or false costs. |
| 10 | **D** | Section 7.6 names this specifically as hand-authored and illustrative, while the retrieval scores themselves are real. **A**, **B** and **C** name things the lesson states are genuinely reused or computed, not illustrative. |
| 11 | **A** | Section 7.6 names this specifically as M7-L17's dedicated topic, beyond this lesson's single-follow-up miniature. **B**, **C** and **D** name topics this lesson covers directly, not defers. |
| 12 | **C** | This is the lesson's own stated general conclusion, tying together every section's specific finding. **A**, **B** and **D** contradict this conclusion or overstate an absolute the lesson does not support. |

**Q13 rubric (5 marks).** One mark each for: **naming the actual mechanism** — that a bare follow-up like
"what about the other one?" carries no retrievable topic of its own, since the real subject exists only in
a prior conversational turn, per §5.3; **connecting this to the measured lab finding** — an isolated
follow-up scored exactly 0.000 across every document, an all-zero tie, not a partial or degraded result;
**distinguishing this from a generation problem** — noting, per §6, that the symptom can look like a
reasoning failure but is actually a retrieval-input problem, since retrieval sees only that turn's own
words; **proposing the concrete fix** — adding a query-rewriting step that uses conversation history to
restate the follow-up's actual topic explicitly before retrieval runs; and **noting the architectural
requirement** — that conversation history must be available to the retrieval stage specifically, not only
to generation, for this fix to work at all. An answer that proposes only "improve the retrieval algorithm"
without identifying the query-side, context-carrying root cause scores 2.

---

<a id="m7-l10"></a>
## M7-L10 — Retrieval and Reranking in the RAG Loop

**Answers: C · A · D · B · C · A · D · B · C · A · D · B**

| Q | Ans | Why, and why the distractors fail |
|---|---|---|
| 1 | **C** | D6 uses "poor condition" and "broken" instead of "damaged," giving BM25 no literal term to match, exactly as measured. **A**, **B** and **D** invent unrelated or false causes. |
| 2 | **A** | This is M6-L12's own cost argument, restated and applied directly to this pipeline's design. **B**, **C** and **D** invent false constraints unrelated to the actual reasoning. |
| 3 | **D** | The lab's own measured result: D6 is absent from the narrow candidate pool and thus absent from the reranked result too. **A**, **B** and **C** contradict the lab's own printed output. |
| 4 | **B** | The lab's own measured result shows exactly this promotion, from rank 3 in the pool to rank 2 in the final reranked list. **A**, **C** and **D** contradict the lab's own printed output. |
| 5 | **C** | This is the lesson's own stated general conclusion from the narrow-vs-wide comparison. **A**, **B** and **D** assert absolutes the measured comparison does not support. |
| 6 | **A** | The lab's own measured result: D6 rose to rank 1 using only the expanded query with the original retrieval method. **B**, **C** and **D** contradict the lab's own printed output. |
| 7 | **D** | This is the lesson's own stated conclusion, framing the two techniques as complementary rather than substitutable. **A**, **B** and **C** assert a false exclusivity the lesson explicitly denies. |
| 8 | **B** | Section 7.5 names this specifically as the illustrative component, distinguishing it from the real, unmodified BM25 formula. **A**, **C** and **D** name components the lesson treats as real or accurately described. |
| 9 | **C** | Section 7.5 states this scaling comparison explicitly. **A**, **B** and **D** assert claims the lesson does not make. |
| 10 | **A** | Section 7.6 names this specifically as M7-L11's next topic. **B**, **C** and **D** name topics this lesson covers directly, not defers. |
| 11 | **D** | Section 7.5 names this specific combination as a natural extension left to the exercises. **A**, **B** and **C** name things this lesson does perform directly. |
| 12 | **B** | This is the lesson's own stated general conclusion, tying together every section's specific measured finding. **A**, **C** and **D** contradict this conclusion or the evidence presented throughout the lesson. |

**Q13 rubric (5 marks).** One mark each for: **naming the retrieve-k dependency specifically** — checking
whether the initial retrieval stage's retrieve-k was widened when reranking was introduced, rather than
left at whatever value predates the reranking stage, per §5.3; **connecting this to the measured mechanism**
— that reranking can only reorder documents already present in the candidate pool, so a narrow retrieve-k
caps its benefit regardless of reranker quality; **proposing a concrete check** — inspecting whether
documents the reranker was specifically meant to recover (paraphrases, differently-worded matches) are
actually present in the candidate pool before reranking runs; **referencing the §6 worked example
directly** — noting this is a known, previously-documented failure pattern (a reranker validated only on
pools already containing the right answer looks fine until deployed against real pools); and **proposing
the fix** — widening retrieve-k and re-validating end to end, rather than assuming the reranker itself is
underperforming. An answer that jumps straight to "the reranker must be broken" without checking retrieve-k
first scores 2.

---

<a id="m7-l11"></a>
## M7-L11 — Context Assembly and Token Budgets

**Answers: D · B · A · C · D · B · A · C · D · B · A · C**

| Q | Ans | Why, and why the distractors fail |
|---|---|---|
| 1 | **D** | This is stated directly and computed in the lab: the budget is the window minus every other consumer of it. **A**, **B** and **C** are false or invented claims about token budgets. |
| 2 | **B** | The lab's own measured result contrasts exactly this: one complete chunk versus five incomplete ones. **A**, **C** and **D** contradict the lab's own printed output. |
| 3 | **A** | The lesson draws this connection explicitly, tying assembly-time truncation to M7-L06's own measured chunk-boundary risk. **B**, **C** and **D** are false or unrelated claims. |
| 4 | **C** | This is the lesson's own stated conclusion: the correct strategy depends on the task's need for completeness versus coverage. **A**, **B** and **D** assert an absolute the lesson does not support. |
| 5 | **D** | This is the lesson's own stated definition, framed as reported research rather than an assertion. **A**, **B** and **C** misstate or invent claims about the effect. |
| 6 | **B** | The lesson states this explicitly as the reason for the conceptual label. **A**, **C** and **D** invent false reasons. |
| 7 | **A** | The lesson states this directly: query-time chunk overlap and rewording can still produce redundancy corpus-level dedup never sees. **B**, **C** and **D** are false or invented claims. |
| 8 | **C** | The lab's own measured result: 0.524 exceeded the 0.5 threshold, and the near-duplicate was correctly dropped. **A**, **B** and **D** contradict the lab's own printed output. |
| 9 | **D** | The final assembled block explicitly carries source metadata per chunk, as shown in the lab's own output. **A**, **B** and **C** describe content the lab's assembled block does not include. |
| 10 | **B** | Section 7.6 names this specifically as M5-L11's own topic, applicable here but not newly covered. **A**, **C** and **D** name topics this lesson covers directly, not defers. |
| 11 | **A** | Section 7.6 names this specifically as M7-L12's next topic. **B**, **C** and **D** name topics this lesson covers directly, not defers. |
| 12 | **C** | This is the lesson's own stated general conclusion, tying together every section's specific measured finding. **A**, **B** and **D** contradict this conclusion or the evidence presented throughout the lesson. |

**Q13 rubric (5 marks).** One mark each for: **naming the actual suspect** — checking where the correct
chunk landed within the assembled context (start, middle, end) across the inconsistent cases specifically,
rather than re-examining retrieval or reranking, per §5.3 and M7-L01 §6's discipline of checking upstream
before suspecting the model; **connecting this to the documented effect** — the "lost in the middle"
phenomenon, correctly caveated as model- and version-specific rather than assumed as fact; **proposing a
concrete comparison** — checking whether inconsistent answers correlate with the correct chunk's position
in the assembled context across the failing queries; **proposing the fix** — placing the highest-ranked
chunk near the start or end of the assembled context, rather than leaving concatenation order arbitrary;
and **proposing verification** — testing this specific change against the previously inconsistent queries
to confirm position, not some other factor, was the actual cause. An answer that jumps to re-tuning
retrieval or reranking without first checking assembly order scores 2.

---

<a id="m7-l12"></a>
## M7-L12 — Citations and Evidence Verification

**Answers: B · D · A · C · B · D · A · C · B · D · A · C**

| Q | Ans | Why, and why the distractors fail |
|---|---|---|
| 1 | **B** | This is the lesson's own stated framing, directly tied to M7-L08's provenance concept. **A**, **C** and **D** invent unrelated or false claims about what a citation asserts. |
| 2 | **D** | This is precisely what the citation-existence function checks, independent of claim content. **A**, **B** and **C** describe checks the lesson's code does not perform. |
| 3 | **A** | The lab's own printed result: P9 is absent from RETRIEVED_CONTEXT entirely. **B**, **C** and **D** contradict the lab's own printed output. |
| 4 | **C** | Both claims cite P3, a real entry in the retrieved set — this is exactly the point the lesson uses to motivate a second, distinct check. **A**, **B** and **D** contradict the lab's own printed output. |
| 5 | **B** | The lab's own measured result: '25' does not appear among P3's numbers (15, 20, 3). **A**, **C** and **D** contradict the lab's own printed output. |
| 6 | **D** | This is the lesson's own stated conclusion, drawn directly from the two claims' matching citation status but differing groundedness. **A**, **B** and **C** contradict this stated conclusion. |
| 7 | **A** | The lesson states this directly: mixing supported and fabricated content defeats a binary verdict. **B**, **C** and **D** are false or invented claims about the example. |
| 8 | **C** | The lab's own measured result: 2 of 4 claimed numbers (20, 3) were found; 25 and 5 were not. **A**, **B** and **D** contradict the lab's own printed output. |
| 9 | **B** | Section 7.5 states this distinction directly. **A**, **C** and **D** misstate the lesson's own comparison. |
| 10 | **D** | Section 7.5 states this distinction explicitly: the principle is real, the scope is narrowed. **A**, **B** and **C** misstate this stated distinction. |
| 11 | **A** | Section 7.6 names this specifically as M7-L13's next topic. **B**, **C** and **D** name topics this lesson covers directly, not defers. |
| 12 | **C** | This is the lesson's own stated general conclusion, tying together every section's specific measured finding. **A**, **B** and **D** contradict this conclusion or the evidence presented throughout the lesson. |

**Q13 rubric (5 marks).** One mark each for: **naming the actual gap** — that "citation present" only
checks whether a cited source exists in the retrieved set, never whether the specific claim next to it is
actually supported by that source's text, per §5.2-§5.3; **citing the measured evidence** — that two claims
citing the identical real source scored differently (1.00 vs. 0.50) purely because one asserted an
unsupported number, proving citation existence and groundedness are separable; **connecting this to the
100% pass rate specifically** — explaining that a 100% "citation present" rate is fully consistent with a
meaningful fraction of answers containing ungrounded or partially-grounded claims, since the metric never
tests claim content at all; **proposing the concrete addition** — a groundedness check (even a narrow one,
like this lesson's numeric check) verifying claim content against the cited source's actual text; and
**proposing it as a graded, not binary, metric**, per §5.4, since partially grounded claims are a real,
distinct category the current yes/no metric cannot represent at all. An answer that proposes only "add more
citations" without addressing claim-level verification scores 2.

---

<a id="m7-l13"></a>
## M7-L13 — Abstention: Teaching the System to Say "I Don't Know"

**Answers: C · A · D · B · C · A · D · B · C · A · D · B**

| Q | Ans | Why, and why the distractors fail |
|---|---|---|
| 1 | **C** | This is the lesson's own stated framing, tying directly to both M7-L01's and M7-L12's documented failures. **A**, **B** and **D** invent unrelated causes. |
| 2 | **A** | No query term for this question appears anywhere in the corpus, so BM25's term-frequency sum has nothing to add. **B**, **C** and **D** invent false or unrelated causes. |
| 3 | **D** | This is the lesson's own stated asymmetry, distinguishing a misleading answer from a merely unhelpful refusal. **A**, **B** and **C** deny or invert this stated asymmetry. |
| 4 | **B** | The lesson explicitly names this connection to M3-L14's classification-cost framework. **A**, **C** and **D** name unrelated lessons. |
| 5 | **C** | The lab's own measured result at threshold=1.0 shows exactly two false positives from queries sharing incidental vocabulary with an unrelated policy. **A**, **B** and **D** contradict the lab's own printed output. |
| 6 | **A** | The lab's own measured result at threshold=3.0 shows exactly this: the PTO query's 2.21 score fell below the raised bar. **B**, **C** and **D** contradict the lab's own printed output. |
| 7 | **D** | The lesson states this caveat explicitly, drawing a direct parallel to other threshold parameters in this course. **A**, **B** and **C** overstate or invert this stated caveat. |
| 8 | **B** | This is the lesson's own stated distinction between the two example messages. **A**, **C** and **D** misstate or deny this distinction. |
| 9 | **C** | The lesson states this nuance explicitly: honest but terse is not the same as maximally helpful. **A**, **B** and **D** contradict this stated position. |
| 10 | **A** | Section 7.6 names this specific combination as a natural extension left to the exercises. **B**, **C** and **D** name things this lesson covers directly, not defers. |
| 11 | **D** | Section 7.6 states this distinction directly, contrasting this lab's pre-generation check with M7-L12's post-generation check. **A**, **B** and **C** each deny one of the two valid points named. |
| 12 | **B** | This is the lesson's own stated general conclusion, tying together every section's specific measured finding. **A**, **C** and **D** contradict this conclusion or the evidence presented throughout the lesson. |

**Q13 rubric (5 marks).** One mark each for: **naming the actual trade-off** — that removing abstention
does not remove the underlying uncertainty, it only removes the system's ability to signal it, per §5.2;
**connecting this to the asymmetric cost** — that "some answer" for an out-of-scope query is a guaranteed
false positive (a confidently wrong, citation-backed answer), which is more costly than an occasional
unnecessary refusal, per §5.2's stated asymmetry; **citing the measured evidence** — this lesson's own
threshold sweep showing exactly what happens at the permissive end (dangerous false positives) versus the
strict end (annoying false negatives), and that "no abstention" is the permissive extreme taken to its
limit; **proposing the actual fix** — a calibrated threshold and a genuinely helpful abstention message
(§5.4), which addresses the "users want an answer" concern better than removing the mechanism entirely;
and **referencing §6's incident** as a concrete illustration of what "always answer" produces in practice.
An answer that only asserts "abstention is important" without the false-positive cost argument scores 2.

---

<a id="m7-l14"></a>
## M7-L14 — Conflicting, Duplicated and Outdated Sources

**Answers: B · D · A · C · B · D · A · C · B · D · A · C**

| Q | Ans | Why, and why the distractors fail |
|---|---|---|
| 1 | **B** | This is exactly the two-part check the lab implements: topic similarity above threshold, plus a real numeric disagreement. **A**, **C** and **D** describe checks the lab's code does not perform. |
| 2 | **D** | The lesson states this directly: filtering to the current version alone makes the apparent conflict vanish, since it was never two independently valid sources. **A**, **B** and **C** contradict the lab's own printed setup. |
| 3 | **A** | M7-L08's own currency/versioning mechanism is exactly what the lab applies to resolve this case. **B**, **C** and **D** name unrelated lessons. |
| 4 | **C** | Both chunks are already marked current, so there is no stale version for a currency filter to remove. **A**, **B** and **D** contradict the lab's own stated setup. |
| 5 | **B** | This is exactly what Strategy 1's implementation does, as shown in the lab's own printed output. **A**, **C** and **D** contradict the lab's own printed output. |
| 6 | **D** | The lesson states this requirement explicitly, warning against an invented hierarchy. **A**, **B** and **C** misstate or invert this stated requirement. |
| 7 | **A** | The lesson states this condition explicitly, tying it directly to M7-L13's abstention cost asymmetry. **B**, **C** and **D** contradict this stated condition. |
| 8 | **C** | The lab's own measured similarity (0.636) exceeds the stated dedup threshold (0.5), confirmed directly in the printed output. **A**, **B** and **D** contradict the lab's own printed output. |
| 9 | **B** | This is the lesson's own stated mechanism for why wording-only similarity checks are risky. **A**, **C** and **D** are false or unrelated claims. |
| 10 | **D** | The lesson states this fix explicitly, naming number extraction or the section 1 conflict detector as the needed additional check. **A**, **B** and **C** name checks the lesson does not propose. |
| 11 | **A** | Section 7.6 states this reasoning explicitly, tying the k=2 choice directly to M7-L05's own finding. **B**, **C** and **D** are false or invented claims. |
| 12 | **C** | This is the lesson's own stated general conclusion, tying together every section's specific measured finding. **A**, **B** and **D** contradict this conclusion or the evidence presented throughout the lesson. |

**Q13 rubric (5 marks).** One mark each for: **proposing conflict detection as the first check** — running
a same-topic-different-facts comparison across the sources involved in the inconsistent answers, per §5.1;
**distinguishing false from genuine conflict** — checking whether the disagreeing sources are both marked
current (is_current), since a versioning gap (§5.2) has a completely different fix than a genuine,
simultaneous disagreement (§5.3); **naming the branching next step** — if it's a versioning gap, apply
M7-L08's currency filtering; if genuine, select among §5.4's three resolution strategies based on whether a
real authority signal exists; **connecting this to the §6 precedent** — that "different answers to the same
question" is not automatically a retrieval bug, and may correctly reflect a real, pre-existing
inconsistency between sources; and **proposing escalation where appropriate** — flagging a confirmed
genuine conflict to the source owners, not treating it purely as an engineering fix. An answer that jumps
straight to "there's a retrieval bug" without checking for genuine source conflict first scores 2.

---

<a id="m7-l15"></a>
## M7-L15 — Permission-Aware Retrieval and Tenant Isolation

**Answers: B · D · A · C · B · D · A · C · B · D · A · C**

| Q | Ans | Why, and why the distractors fail |
|---|---|---|
| 1 | **B** | Tenant membership, not relevance, is the deciding factor — the lab's own tied scores demonstrate this directly. **A**, **C** and **D** invent unrelated or false causes. |
| 2 | **D** | The lab's own measured result confirms GLOBEX-P1 was genuinely present in the raw candidate list before the final filter ran. **A**, **B** and **C** contradict the lab's own printed output. |
| 3 | **A** | This is the lesson's own stated mechanism for why the raw candidate list is a real exposure surface. **B**, **C** and **D** invent unrelated or false claims. |
| 4 | **C** | The lesson states this contrast explicitly, distinguishing M6-L09's cost/recall framing from this lesson's security framing. **A**, **B** and **D** misstate this stated relationship. |
| 5 | **B** | The lab's own measured result: ACME-P2 required the hr role and was excluded from the employee's authorized set entirely. **A**, **C** and **D** contradict the lab's own printed setup. |
| 6 | **D** | The lesson states this directly, distinguishing tenant isolation from role-based permission as two separate, necessary layers. **A**, **B** and **C** contradict this stated conclusion. |
| 7 | **A** | The lab's own code comment and printed narrative name exactly this simulated bug. **B**, **C** and **D** describe a different or nonexistent bug. |
| 8 | **C** | The lab's own measured result confirms this leak directly. **A**, **B** and **D** contradict the lab's own printed output. |
| 9 | **B** | The lab's own measured result shows the second check correctly removing the leaked document. **A**, **C** and **D** contradict the lab's own printed output. |
| 10 | **D** | The lesson states this explicitly: the second check is insurance, not a substitute for fixing the actual defect. **A**, **B** and **C** contradict this stated position. |
| 11 | **A** | Section 7.5 states this connection to M2-L15 explicitly. **B**, **C** and **D** misstate what CurrentUser represents. |
| 12 | **C** | This is the lesson's own stated general conclusion, tying together every section's specific measured finding. **A**, **B** and **D** contradict this conclusion or the evidence presented throughout the lesson. |

**Q13 rubric (5 marks).** One mark each for: **naming the specific risk** — that a final-step-only filter
still lets every earlier stage (retrieval scoring, reranking, logging, caching) handle unauthorized
candidate data, per §5.2; **citing the measured evidence** — that post-filtering's raw candidate list
genuinely contained a cross-tenant document in this lesson's own lab, even though the final answer was
correct; **connecting this to a real exposure path** — logs, caches, or a reranking/fusion stage that
touches the unfiltered candidate set before the final filter runs, per §6's worked incident; **proposing
pre-filtering instead** — restricting the candidate set to authorized documents before scoring/ranking
begins; and **proposing a second, independent check as additional insurance**, per §5.4, rather than relying
on the single final-step filter alone. An answer that only says "filtering at the end is risky" without
naming a concrete intermediate exposure path scores 2.

---

<a id="m7-l16"></a>
## M7-L16 — Incremental Updates and Deletion Propagation

**Answers: C · A · D · B · C · A · D · B · C · A · D · B**

| Q | Ans | Why, and why the distractors fail |
|---|---|---|
| 1 | **C** | The lesson states this framing directly in its opening section, distinguishing its own scope from M6-L10's. **A**, **B** and **D** name topics covered in earlier lessons, not this one's contribution. |
| 2 | **A** | The lab's own measured result: 3 of 4 chunks shared an identical content hash and needed no re-embedding. **B**, **C** and **D** contradict the lab's own printed output. |
| 3 | **D** | This is exactly the mechanism the lab implements and the lesson names explicitly. **A**, **B** and **C** describe methods the lab's code does not use. |
| 4 | **B** | The lab's own measured result confirms the cache was untouched and still cited the deleted chunk. **A**, **C** and **D** contradict the lab's own printed output. |
| 5 | **C** | This is the lesson's own stated reasoning for why the orphaned reference is a real, consequential bug. **A**, **B** and **D** deny or misstate this reasoning. |
| 6 | **A** | The lesson states this explicitly: the index itself was correct; the propagation to a separate system was the actual failure. **B**, **C** and **D** contradict this stated conclusion. |
| 7 | **D** | This is exactly the mechanism implemented in the lab's fixed deletion function. **A**, **B** and **C** describe methods the lab's code does not use. |
| 8 | **B** | The lab's own measured result confirms the affected cache entry was identified and removed. **A**, **C** and **D** contradict the lab's own printed output. |
| 9 | **C** | The lesson states this explicitly, contrasting it with a separate, easily-forgotten follow-up step. **A**, **B** and **D** contradict this stated design. |
| 10 | **A** | Section 7.5 states this explicitly, naming the propagation principle as what generalizes. **B**, **C** and **D** misstate what the lab's cache represents. |
| 11 | **D** | Section 7.5 names this specifically as not covered in this lesson. **A**, **B** and **C** name things this lesson does cover directly. |
| 12 | **B** | This is the lesson's own stated general conclusion, tying together every section's specific measured finding. **A**, **C** and **D** contradict this conclusion or the evidence presented throughout the lesson. |

**Q13 rubric (5 marks).** One mark each for: **naming the actual check** — inspecting whether any caches or
other derived data (not just the index) still reference the deleted content's chunk IDs, per §5.3;
**connecting this to the specific measured mechanism** — that an index deletion can be entirely correct
while a separate downstream cache was simply never told about the change, since nothing links the two
operations by default; **explaining why this is invisible without checking** — a stale cached citation
looks exactly like a valid one, so the bug surfaces only when a user notices or someone explicitly verifies
cited chunk IDs against the current index; **proposing the fix** — propagating the same deletion event
(the same computed set of affected chunk IDs) to every downstream consumer, per §5.4, rather than relying
on independent, easily-forgotten invalidation logic per system; and **proposing a safety net** — periodic
validation of cached citations against the current index, per §6, for any propagation path not yet fully
event-driven. An answer that only says "the cache is stale" without identifying the missing propagation
link scores 2.

---

<a id="m7-l17"></a>
## M7-L17 — Conversational and Multi-Hop Retrieval

**Answers: D · A · B · C · D · A · B · C · D · A · B · C**

| Q | Ans | Why, and why the distractors fail |
|---|---|---|
| 1 | **D** | The lab's own measured result: the top document confirms the manager's identity but contains no policy content, while the real answer never mentions "Engineering" at all. **A**, **B** and **C** contradict the lab's own printed setup and output. |
| 2 | **A** | The lab's own measured result confirms this score directly. **B**, **C** and **D** contradict the lab's own printed output. |
| 3 | **B** | This is exactly the division of labor the lesson states and the lab demonstrates: hop 1 finds the entity, not the answer. **A**, **C** and **D** contradict this stated and demonstrated mechanism. |
| 4 | **C** | The lesson states this reasoning explicitly, distinguishing genuine new information from redundant re-discovery. **A**, **B** and **D** invent unrelated or false causes. |
| 5 | **D** | The lab's own measured result: the raw query's generic terms favored a different, unrelated document over the correct target. **A**, **B** and **C** contradict the lab's own printed setup and output. |
| 6 | **A** | The lab's own measured result confirms exactly this outcome. **B**, **C** and **D** contradict the lab's own printed output. |
| 7 | **B** | This is the lesson's own stated combination required for turn 3's correct rewrite. **A**, **C** and **D** contradict this stated requirement. |
| 8 | **C** | The lab's own conversation structure confirms this distance, and the lesson draws the stated implication directly from it. **A**, **B** and **D** contradict the lab's own printed setup. |
| 9 | **D** | This is the lesson's own stated pair of stopping conditions. **A**, **B** and **C** contradict this stated guidance. |
| 10 | **A** | The lesson states this explicitly, tying the fallback directly to M7-L13's mechanism. **B**, **C** and **D** contradict this stated guidance. |
| 11 | **B** | Section 7.5 states this explicitly, consistent with every other lab in the course. **A**, **C** and **D** misstate what is real versus illustrative in this lab. |
| 12 | **C** | This is the lesson's own stated general conclusion, tying together every section's specific measured finding. **A**, **B** and **D** contradict this conclusion or the evidence presented throughout the lesson. |

**Q13 rubric (5 marks).** One mark each for: **naming the actual check** — inspecting whether the retrieved
document(s) behind the answer actually contain the specific policy content asked about, or only confirm an
intermediate fact like who the manager is, per §5.1; **connecting this to the multi-hop mechanism** — that
this question shape may require discovering the manager's identity first (hop 1) and querying again using
that identity (hop 2), per §5.2, rather than trusting a single retrieval pass; **explaining why groundedness
checks pass anyway** — per §6, a wrong answer built from a genuinely retrieved, correctly cited document
(e.g. the "who manages" fact) passes claim-level groundedness checks, since the checked claim IS supported
by ITS cited source — the defect is that the wrong source was retrieved as sufficient, not that the citation
is fake; **proposing the fix** — implementing multi-hop retrieval or detection for this question shape; and
**noting the general principle** — that citation/groundedness checks validate claims against their sources,
not whether retrieval found the right source in the first place. An answer that only says "the retrieval
was wrong" without explaining why groundedness checks specifically missed it scores 2.

---

<a id="m7-l18"></a>
## M7-L18 — Agentic Retrieval and Graph RAG

**Answers: B · D · A · C · B · D · A · C · B · D · A · C**

| Q | Ans | Why, and why the distractors fail |
|---|---|---|
| 1 | **B** | This is exactly the decision the lesson names and the lab demonstrates for the arithmetic query. **A**, **C** and **D** invent unrelated decisions. |
| 2 | **D** | The lab's own printed result confirms direct computation, tying it explicitly to M7-L02's plain-tool framing. **A**, **B** and **C** contradict the lab's own printed output. |
| 3 | **A** | The lab's own measured result: the sufficiency check on ORG1's text returned False, triggering the second pass. **B**, **C** and **D** contradict the lab's own printed setup and output. |
| 4 | **C** | This is the lesson's own stated distinction, contrasting a fixed two-hop pipeline with an earned, check-triggered second pass. **A**, **B** and **D** contradict this stated distinction. |
| 5 | **B** | This is exactly what section 7.3 demonstrates, contrasted directly against M7-L17's own approach. **A**, **C** and **D** misstate what graph traversal replaces. |
| 6 | **D** | The lab's own printed traversal shows exactly two edge lookups producing the answer. **A**, **B** and **C** contradict the lab's own printed output. |
| 7 | **A** | The lesson states this cost explicitly, naming the extraction step this lab's own graph skipped. **B**, **C** and **D** invent false or unrelated costs. |
| 8 | **C** | The lesson draws this parallel explicitly, connecting graph incompleteness to M7-L01's original vocabulary-mismatch finding. **A**, **B** and **D** contradict this stated consequence. |
| 9 | **B** | The lesson states this combination explicitly as the practical, real-system pattern. **A**, **C** and **D** assert an exclusivity the lesson does not support. |
| 10 | **D** | Section 7.5 states this explicitly, tying the illustrative rules back to a real agent's actual judgment. **A**, **B** and **C** misstate what these functions represent. |
| 11 | **A** | Section 7.5 names both of these specifically as not demonstrated in this lab. **B**, **C** and **D** name things this lesson does perform directly. |
| 12 | **C** | This is the lesson's own stated general conclusion, tying together every section's specific measured finding. **A**, **B** and **D** contradict this conclusion or the evidence presented throughout the lesson. |

**Q13 rubric (5 marks).** One mark each for: **naming the actual mechanism** — that the graph was extracted
once and never re-extracted as source documents changed, per §5.4 and §6; **connecting this to the specific
symptom** — a reorganization updated the underlying HR documents, but nothing triggered the graph's edges to
be regenerated, so the graph kept pointing to the old manager; **contrasting this with ordinary index
staleness** — noting, per §6, that a graph has an extra step compared to a text index (M7-L16): re-
extraction into edges, not just re-embedding, and that gap is what silently broke; **proposing the fix** —
triggering graph re-extraction from the same document-update events M7-L16 established for propagation,
rather than treating the graph as a one-time build; and **proposing a fallback or safety net** — either
falling back to text retrieval when graph confidence is uncertain, or periodically validating graph edges
against source documents. An answer that only says "the graph is out of date" without identifying the
missing re-extraction trigger scores 2.

---

<a id="m7-l19"></a>
## M7-L19 — Evaluating RAG: Retrieval vs Answer, Groundedness, Correctness, Completeness

**Answers: C · A · D · B · C · A · D · B · C · A · D · B**

| Q | Ans | Why, and why the distractors fail |
|---|---|---|
| 1 | **C** | Retrieval and answer quality are measured by entirely different checks on entirely different objects — a ranked list of chunk IDs versus generated text — so a perfect score on one says nothing about the other. **A**, **B** and **D** invent false or unrelated claims about how these metrics relate. |
| 2 | **A** | Groundedness checks faithfulness to the cited source; correctness checks faithfulness to real-world truth — a claim can accurately reflect a source that is itself stale or wrong. **B**, **C** and **D** deny or misstate a divergence the lab directly measures. |
| 3 | **D** | The cited source (P3) genuinely said "20 days," but that figure was stale — the real PTO policy had since changed to 25, the same propagation problem M7-L16 covered. **A**, **B** and **C** invent causes unrelated to the actual, measured mechanism. |
| 4 | **B** | A fact-check that only asks "is this number right" would pass this claim, while its citation is fabricated or misattributed to a source that never mentions the topic. **A**, **C** and **D** contradict the lesson's own stated framing of this case. |
| 5 | **C** | The lab's own printed source text: P3 is about PTO and never mentions referral bonuses at all. **A**, **B** and **D** contradict the lab's own printed output. |
| 6 | **A** | Completeness measures whether an answer covers everything a question asked, entirely independent of whether what it does say is supported or true. **B**, **C** and **D** describe what citation-existence, correctness, or an unrelated concern check instead. |
| 7 | **D** | The lab's own measured result: only "junior PTO" was covered, leaving "senior PTO" and "referral bonus" entirely unaddressed, out of three sub-topics. **A**, **B** and **C** contradict the lab's own printed output — the answer was in fact grounded and correct. |
| 8 | **B** | The lab's own measured result: 0.50, not 1.00, because the answer repeated the same stale senior-PTO figure from section 2, inherited from the same imperfect source. **A**, **C** and **D** contradict this measured, printed result directly. |
| 9 | **C** | This is the lesson's own stated conclusion from the finding: an answer can be fully complete and fully grounded while still carrying a correctness problem inherited from its source. **A**, **B** and **D** overstate or invert this stated conclusion. |
| 10 | **A** | A blended score would collapse three genuinely different, differently-fixable failure types (stale source, fabricated citation, incomplete coverage) into one indistinguishable number. **B**, **C** and **D** contradict the lesson's own stated reasoning. |
| 11 | **D** | Section 7.6 states this explicitly: Precision@k, Recall@k, MRR, and nDCG are M6-L13's territory, not repeated here. **A**, **B** and **C** name axes this lesson covers directly, not defers. |
| 12 | **B** | This is the lesson's own stated general conclusion, tying together every section's specific measured finding across all three axes. **A**, **C** and **D** contradict this conclusion or the evidence presented throughout the lesson. |

**Q13 rubric (5 marks).** One mark each for: **explaining why the single score hid the problem** — a
blended average can stay stable while several small, structurally different failure rates each grow
underneath it, since none of them individually moves the average enough to be noticed, per §5.5 and §6;
**naming the distinct failure categories a real audit would likely find** — mirroring this lesson's own
three: a grounded-but-stale-source problem, an ungrounded-but-correct (fabricated citation) problem, and an
incomplete-coverage problem, each a genuinely different defect; **proposing separate, visible metrics
instead** — tracking groundedness, correctness, and completeness independently rather than averaging them
into one headline number, per §5.5's central table; **routing each failure type to its actual owning fix**
— stale sources need M7-L16's propagation discipline, fabricated citations need M7-L12's verification,
incomplete answers need M7-L09's decomposition, per §6; and **stating the general principle** — that a
stable-looking overall score is not evidence that a system has no problems, only that no single problem is
yet large enough to move the average alone. An answer that proposes only "improve the score" without
separating it into distinct, independently-tracked axes scores 2.

---

<a id="m7-l20"></a>
## M7-L20 — Debugging RAG, Adversarial Documents, Latency and Cost

**Answers: C · A · D · B · C · A · D · B · C · A · D · B**

| Q | Ans | Why, and why the distractors fail |
|---|---|---|
| 1 | **C** | Retrieval, then groundedness, then correctness, then completeness — each later check only makes sense once the layer before it has already passed, per §5.1. **A**, **B** and **D** misstate the checklist's actual, stated order and logic. |
| 2 | **A** | Nothing scored above the retrieval threshold, so there was no retrieved content for a groundedness check to even examine. **B**, **C** and **D** invent false or unrelated reasons the lab's code does not reflect. |
| 3 | **D** | Report E genuinely passes every layer, proving the checklist can correctly recognize a real bug-free case rather than always reporting some failure. **A**, **B** and **C** contradict the lab's own printed output and stated purpose for report E. |
| 4 | **B** | P7's opening and closing sentences are genuine, on-topic reimbursement content, giving BM25 a real reason to retrieve it independent of the embedded payload. **A**, **C** and **D** contradict the lab's own printed retrieval ranking and corpus contents. |
| 5 | **C** | The injection-pattern scan flagged P7 before context assembly — the lab states directly that the scan, not P7's retrieval rank, is what kept it out. **A**, **B** and **D** contradict this stated mechanism. |
| 6 | **A** | The lesson states this honest limitation directly: literal keyword matching does not generalize to reworded, split, or encoded phrasing. **B**, **C** and **D** contradict this stated limitation or invent a false one. |
| 7 | **D** | The lab's own measured result: retrieval latency scaled with corpus size; reranking's added latency scaled with candidate pool size instead. **A**, **B** and **C** contradict this measured, printed result. |
| 8 | **B** | The lesson states this connection explicitly, tying the re-measured scaling pattern back to M6-L12's original joint-scorer finding. **A**, **C** and **D** name unrelated lessons and findings. |
| 9 | **C** | The lab's own measured result: generation cost was roughly 1,101x embedding cost for the same query. **A**, **B** and **D** contradict this measured, printed result directly. |
| 10 | **A** | This is the lesson's own stated reasoning: a leaner context reduces both retrieval-quality risk and dollar cost together, since generation pays for the whole assembled context every call. **B**, **C** and **D** contradict or deny this stated reasoning. |
| 11 | **D** | Section 7.5 states this explicitly: no live model call is made anywhere in this course, so the hijack consequence is described conceptually, not demonstrated. **A**, **B** and **C** name components the lesson treats as genuinely executed, not illustrative. |
| 12 | **B** | This is the lesson's own stated general conclusion, tying together all three parts of the lesson's scope. **A**, **C** and **D** contradict this conclusion or the evidence presented throughout the lesson. |

**Q13 rubric (5 marks).** One mark each for: **naming a specific security check** — scanning the retrieved
corpus for adversarial/injectable content (§5.2-§5.3), since a document can be genuinely, legitimately
relevant and still carry an embedded instruction; **explaining why correctness testing doesn't already cover
this** — typical test queries are unlikely to include a deliberately crafted adversarial document, so
"retrieval and generation test correctly" says nothing about whether retrieved content is safe to hand to
the model; **naming a specific latency/cost check** — measuring real latency and dollar cost at the
corpus size and query volume expected in production (§5.4-§5.5), not just correctness on a handful of test
queries; **explaining why this matters** — reranking latency scales with candidate pool size and generation
cost dominates the bill at real volume, neither of which is visible from small-scale correctness testing
alone; and **connecting both checks back to this lesson specifically** rather than offering generic
pre-launch advice unrelated to RAG's particular failure modes. An answer naming only one specific,
lesson-grounded check, or naming checks unrelated to security or latency/cost, scores 3 or fewer.

---

*Module 7 is complete: all 20 lessons (M7-L01 through M7-L20) are answered above.*
