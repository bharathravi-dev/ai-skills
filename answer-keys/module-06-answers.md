# Module 6 — Answer Key

**Do not read this before attempting the questions.** Every answer carries a reason, and for multiple
choice, a reason each distractor fails.

> Module 6 quiz options are uniform in length with a balanced answer distribution, and carry no inline
> explanation of the correct choice. All rationale lives here.

| Lesson | Jump to |
|---|---|
| M6-L01 Semantic Similarity vs Exact Matching | [↓](#m6-l01) |
| M6-L02 Embedding Dimensions and Compatibility | [↓](#m6-l02) |
| M6-L03 BM25 | [↓](#m6-l03) |
| M6-L04 Dense vs Sparse Retrieval | [↓](#m6-l04) |
| M6-L05 Exact Nearest-Neighbour Search | [↓](#m6-l05) |
| M6-L06 Approximate NN and HNSW | [↓](#m6-l06) |
| M6-L07 Indexes vs Databases | [↓](#m6-l07) |
| M6-L08 pgvector Hands-On | [↓](#m6-l08) |
| M6-L09 Metadata and Filtered-ANN | [↓](#m6-l09) |
| M6-L10 Indexing, Updates and Re-embedding | [↓](#m6-l10) |
| M6-L11 Hybrid Search and Reciprocal Rank Fusion | [↓](#m6-l11) |
| M6-L12 Cross-Encoder Reranking | [↓](#m6-l12) |
| M6-L13 Retrieval Metrics: Precision@k, Recall@k, MRR, nDCG | [↓](#m6-l13) |

---

<a id="m6-l01"></a>
## M6-L01 — Semantic Similarity vs Exact Matching

**Answers: B · D · A · C · D · B · C · A · B · D · A · C**

| Q | Ans | Why, and why the distractors fail |
|---|---|---|
| 1 | **B** | Exact match found nothing, because the literal word "dog" appears nowhere; cosine similarity over the pooled vectors correctly ranked the puppy/canine document highest. **A** and **C** contradict the lab's own printed result. **D** invents an error condition that does not occur — a miss is a normal, silent result, not an exception. |
| 2 | **D** | Document vectors are the mean of their constituent words' vectors — exactly M4-L04's pooling mechanic, applied here to hand-built vectors instead of a trained model's output. **A**, **B** and **C** describe mechanisms not used anywhere in the lab's code. |
| 3 | **A** | "Bank" has exactly one vector in this vocabulary, positioned as a blend of the finance and nature axes, because a bare query word carries no context to disambiguate it. **B** and **C** misattribute a real, structural property of static embeddings to an error or coincidence. **D** confuses semantic scoring with exact match, which is a separate, unrelated computation. |
| 4 | **C** | A contextual embedding reads the surrounding words and produces a different vector per sentence, which is precisely what a bare, static query word cannot do. **A** and **D** propose changes to the vocabulary size or dimensionality, neither of which addresses the underlying cause. **B** discards semantic search rather than fixing its blind spot. |
| 5 | **D** | The order code was never given an entry in `WORD_VECTORS`, so there is no vector to compare — "undefined," not "low similarity." **A**, **B** and **C** invent mechanisms (a crash, stop-word filtering, document-count effects) that play no role in the lab's actual logic. |
| 6 | **B** | Exact match only requires the literal string to be present in the text — no vector, meaning, or understanding is required at all. **A** and **D** misdescribe how the two mechanisms actually work. **C** invents a design rule that is not how semantic search behaves; it is not "excluded," it is simply undefined for unrepresented terms. |
| 7 | **C** | Across five queries, each mechanism won on different rows, and one row was genuinely ambiguous for both — the direct argument for combining them. **A** and **B** each overgeneralise from a subset of the table's rows. **D** is contradicted by the "bank" row, where the two approaches diverge sharply on which document to prefer. |
| 8 | **A** | The vectors are deliberately hand-assigned on five interpretable axes so every calculation can be checked by hand, explicitly not the output of any trained model. **B** and **C** claim a provenance the lesson explicitly denies. **D** is false — the vectors are structured by axis, not random. |
| 9 | **B** | Exact match correctly finds the literal string "bank" in both documents while having no way to represent that the two occurrences mean different things — surface-correct, meaning-blind. **A** conflates two different failure modes; exact match did not fail to find the string. **C** attributes understanding to a mechanism that has none. **D** is contradicted by §7.1, where exact match failed outright. |
| 10 | **D** | Real embedding models operate in far higher dimensions, are learned rather than assigned, and consequently fail in less predictable ways than this small, hand-built illustration. **A**, **B** and **C** overstate either the similarity or the limitations of real models relative to this lab's simplified stand-in. |
| 11 | **A** | The document's vector is the mean of "loan" and the ambiguous "bank" vector, and only "loan" sits purely on the finance axis — the blend pulls the result below a perfect 1.00. **B** invents a computational flaw that does not exist. **C** and **D** are contradicted by the document's actual content and score. |
| 12 | **C** | The lesson's throughline: choose or combine tools based on the query types a system actually needs to handle, not by assuming either is universally superior. **A**, **B** and **D** each assert exactly the kind of absolute claim the lesson's five-query table was built to refute. |

**Q13 rubric (5 marks).** One mark each for: **naming a concrete failure case** — a literal identifier,
code, or exact string query (as in §7.3's `GB-4471`) that a semantic-only system would either fail on
outright or return as undefined/irrelevant, since such a query was never assigned a meaningful vector;
**connecting it to the lab's evidence** — referencing the lab's own head-to-head table rather than
asserting the risk abstractly; **acknowledging the real benefit being proposed** — semantic search's
genuine advantage on paraphrased queries (§5.1) should not be dismissed, only balanced; **proposing hybrid
search** — combining exact and semantic matching (M6-L11) rather than replacing one wholesale with the
other; and **suggesting how to verify** — testing the proposed system against a small set of paraphrase,
polysemy, and exact-code queries before committing to the change, mirroring §7.3's own test design. An
answer that only says "semantic search isn't perfect" without naming a concrete failing query type scores
2.

---

<a id="m6-l02"></a>
## M6-L02 — Embedding Dimensions, Model Compatibility and Normalization

**Answers: C · A · D · B · C · D · A · B · D · C · B · A**

| Q | Ans | Why, and why the distractors fail |
|---|---|---|
| 1 | **C** | 3,072 / 256 = 12, and the lab's own table shows storage scaling exactly proportionally to dimension count at fixed precision. **A** and **B** misstate the ratio. **D** ignores that dimension count changed even though precision did not — the two are independent levers. |
| 2 | **A** | Quantisation changes how many bytes represent each value, entirely separate from how many values (dimensions) exist — the lab's own framing of it as "a separate lever." **B** describes a different technique (dimensionality reduction), not quantisation. **C** and **D** invent mechanisms not used in the lab. |
| 3 | **D** | Both models have four dimensions, but each learned its own arrangement of axes, so a dimension index carries no shared meaning between them — the entire point of the section. **A** and **B** misattribute a structural mismatch to a defect. **C** is false; the lab's whole point is that dimension counts DID match while meaning still did not transfer. |
| 4 | **B** | A version upgrade of the same-named model can retrain into a different coordinate system without any visible signal — the lesson's stated, realistic trigger, distinct from an obvious configuration mistake. **A**, **C** and **D** describe ordinary, safe operations within one consistent model and metric. |
| 5 | **C** | No error, no crash — a plausible number that requires deliberate checking to catch, which is exactly what makes it dangerous compared to a failure that announces itself. **A** and **D** invent scope limits not present in the lesson. **B** contradicts the lab's explicit point that nothing crashes. |
| 6 | **D** | Euclidean distance responds to vector length as well as direction; the large-magnitude document was penalised by distance despite being the best possible direction match. **A** and **B** invent causes unrelated to the demonstrated mechanism. **C** overgeneralises a claim the lesson does not make — neither metric is universally "more accurate." |
| 7 | **A** | The lab explicitly verifies the identity `‖a−b‖²=2−2·cos(a,b)` numerically for unit vectors, so the agreement is provable, not a coincidence of the chosen numbers. **B**, **C** and **D** all contradict the lab's printed "Rankings now agree: True" result. |
| 8 | **B** | Because unit-vector Euclidean distance is a direct, monotonic function of cosine similarity, ranking by the cheaper dot product (equal to cosine on unit vectors, M3-L02) gives the identical order. **A** overreaches into a blanket prohibition the identity does not support. **C** and **D** are unrelated claims the identity does not make. |
| 9 | **D** | Tagging vectors by model/version turns an invisible mismatch into a checkable fact before any comparison is trusted — the lesson's stated control, paralleling M5-L12's artefact fingerprint. **A**, **B** and **C** propose actions that do not address the actual failure mode (a coordinate-system mismatch), and **B** in particular would make magnitude-driven ranking errors (§5.3) worse, not better. |
| 10 | **C** | Section 1 prices a quantity (storage) that depends only on shape and precision; section 2 shows that shape alone says nothing about whether two vector sets can be meaningfully compared — genuinely separate concerns. **A** and **D** invent a relationship between the two that the lesson explicitly denies. **B** collapses two independent axes into one. |
| 11 | **B** | Summing rather than averaging accumulates magnitude with every additional word, so longer documents get systematically larger vectors — exactly the mechanism §7.3 shows biasing an unnormalised, magnitude-sensitive distance metric. **A**, **C** and **D** contradict how summation behaves. |
| 12 | **A** | Both the storage/precision trade-off (§5.1) and model/version compatibility (§5.2, §5.4) must be checked before trusting a similarity score — the lesson's synthesis. **B**, **C** and **D** each restate a specific mistake the lesson corrects. |

**Q13 rubric (5 marks).** One mark each for: **naming the specific risk** — comparing V2-embedded queries
against a mixed index of V1- and V2-embedded documents produces the exact silent, meaningless-number
failure demonstrated in §7.2, regardless of the two versions sharing a dimension count; **why it is
dangerous** — the failure produces no error and can look like inconsistent quality drift rather than a
structural bug, exactly as in §6's worked example; **what to require before approving** — either a full
re-index of existing documents to the new model version, or a verified, explicit compatibility bridge, not
a gradual mixed-model rollout; **a concrete verification step** — testing a known query against both
old-only and mixed indexes before launch, analogous to the "refund" query in §7.2, to catch the failure
pre-emptively; and **tagging as an ongoing control** — recommending every vector be tagged with its
producing model/version so a future mismatch is detectable rather than silent. An answer that only says
"re-embedding everything is safer" without naming why the partial plan specifically fails scores 2.

---

<a id="m6-l03"></a>
## M6-L03 — Keyword Search and BM25, Computed by Hand

**Answers: D · B · A · C · B · D · C · A · D · B · C · A**

| Q | Ans | Why, and why the distractors fail |
|---|---|---|
| 1 | **D** | D1 is the only document matching both "refund" and "damaged," and BM25 sums a separate contribution for each matched query term — matching two terms beats matching one at high frequency. **A** and **B** name factors that affect the score but are not what actually decided this particular ranking. **C** confuses a per-term property (IDF) with the document's total score. |
| 2 | **B** | The lab's own table shows n=5 (every document) producing IDF≈0.087, near zero, because a term present everywhere cannot distinguish any document from any other. **A** and **C** contradict the printed values directly. **D** overstates — this smoothed formula stays positive even at maximum document frequency (§5.2's own caveat). |
| 3 | **A** | Rarity is informative: finding a term that appears in only one document narrows down the match far more than finding one that appears everywhere, which is why weight rises as document frequency falls. **B** and **D** are not claims the lesson makes. **C** is false; the formula explicitly uses a logarithm (M3-L05). |
| 4 | **C** | The term-frequency component approaches a fixed ceiling as occurrences grow, so each additional occurrence contributes strictly less than the one before it — exactly what the marginal-gain column shows. **A** and **D** invent errors that did not occur. **B** describes a real but unrelated mechanism; IDF does not change as term frequency within one document changes. |
| 5 | **B** | Without a cap on term-frequency contribution, repeating a query word many times would let a document win purely through repetition — saturation removes that incentive by design. **A**, **C** and **D** name benefits or properties the mechanism does not provide. |
| 6 | **D** | At b=0, the length-normalisation term is fixed regardless of document length, so both documents scored identically for the same term frequency — the lab's own printed 1.00 ratio at b=0. **A**, **B** and **C** all contradict that printed result. |
| 7 | **C** | The penalty scales purely with the length ratio at b=1, with no way to distinguish padding from genuinely relevant additional content — both documents had identical term frequency and IDF, isolating length as the only variable that changed. **A**, **B** and **D** name factors that were held constant in this comparison. |
| 8 | **A** | `b` scales how much a document's length relative to the corpus average affects its score, from no effect (b=0) to full effect (b=1) — demonstrated directly in §7.4's table. **B**, **C** and **D** describe mechanisms BM25's `b` parameter does not control. |
| 9 | **D** | Once document frequency exceeds half the corpus, the unsmoothed ratio inside the logarithm drops below 1, making its logarithm negative — an explicit penalty rather than a small reward. **A** and **C** are contradicted by this same mechanism. **B** is false; the formula remains computable, just with a different sign for very common terms. |
| 10 | **B** | The lesson explicitly frames k1 and b as common, tunable defaults, not fixed requirements of the formula itself. **A** and **D** overstate them as immutable. **C** invents a dependency on corpus size that does not exist in the formula. |
| 11 | **C** | BM25 is a fixed, deterministic formula — there is no learned model whose behaviour must be approximated or simulated, unlike labs earlier in the course involving LLM outputs. **A**, **B** and **D** name properties unrelated to why this lab counts as fully real. |
| 12 | **A** | Each of the three mechanisms is an explicit, separately adjustable design choice with its own measurable effect on scores — the throughline connecting all three sections. **B**, **C** and **D** each deny a distinction the lesson's own measurements establish clearly. |

**Q13 rubric (5 marks).** One mark each for: **naming the conflation** — "more content" and "more words"
are not the same thing, and b=0 removes ALL length sensitivity, not just an unfair penalty on genuinely
long, relevant documents; **citing the lab's evidence** — referencing §7.4's exact result that b=0 makes
two documents of very different lengths score identically for the same term frequency; **the real risk**
— a long document containing a query term only incidentally, amid mostly unrelated content, is no longer
disadvantaged relative to a short, focused, on-topic document; **what to check before agreeing** — testing
the change against a small evaluation set of real queries with known best answers (M5-L18's discipline
applied to search) rather than reasoning from intuition alone; and **a middle-ground alternative** —
suggesting a nonzero but reduced b (§7.4 shows several intermediate values) rather than accepting the
all-or-nothing choice between 0 and the current default. An answer that only says "b=0 seems risky"
without naming the specific mechanism it disables scores 2.

---

<a id="m6-l04"></a>
## M6-L04 — Dense vs Sparse Retrieval

**Answers: B · D · C · A · D · B · A · C · B · D · C · A**

| Q | Ans | Why, and why the distractors fail |
|---|---|---|
| 1 | **B** | Sparsity means most dimensions are zero for any given document or query, since only a handful of vocabulary words actually appear — the lab's own printed count confirms 19 of 21 dimensions carry no value for this query. **A**, **C** and **D** describe behaviours the vector representation does not have. |
| 2 | **D** | Section 1 computes an actual ranking from actual cosine similarity over actual count vectors — no model, no training, and it works, using the identical formula M6-L02 applied to dense embeddings. **A** and **B** contradict a method the lab runs successfully at this exact corpus size. **C** denies that the same mathematical operation was used in both cases, which the code itself disproves. |
| 3 | **C** | A sparse dimension is literally a vocabulary word, so a shared non-zero dimension names itself; a dense dimension is a learned or hand-abstracted composite with no such individual meaning, even when a human assigned it. **A**, **B** and **D** are not the actual mechanism behind the explainability gap. |
| 4 | **A** | The lab explicitly reuses M6-L02's small, hand-built toy embedding to make the point in the most favourable possible case — even there, no per-axis explanation exists. **B**, **C** and **D** misdescribe what the lab actually used. |
| 5 | **D** | Both methods build a sparse vector over the same vocabulary but assign different values to its dimensions — raw counts versus IDF-weighted, saturated BM25 scores — which is sufficient on its own to produce different rankings. **A** and **C** invent explanations the lab's identical corpus and query rule out. **B** contradicts the lesson's own classification of BM25 as a sparse method. |
| 6 | **B** | Both are sparse-retrieval methods; they differ in how they weight vocabulary dimensions, not in whether they are sparse or dense. **A** dismisses a method the lab runs and scores successfully. **C** misclassifies BM25. **D** is directly contradicted by §7.3's disagreement between the two rankings. |
| 7 | **A** | D1 is the only document matching both distinct query terms, which the sparse cosine computation rewards directly. **B**, **C** and **D** name properties that did not drive D1's specific score in this comparison. |
| 8 | **C** | D5 repeats "refund" four times with no length or frequency discount under raw cosine similarity, unlike BM25's saturation (M6-L03), which is exactly why the two methods disagree on D5's relative rank. **A** is false — D5 does not contain "damaged." **B** and **D** name properties not actually driving this particular score. |
| 9 | **B** | The lesson's definition centres on dimensionality-per-vocabulary-term and sparsity, explicitly distinguishing this from a vague "not embeddings" definition. **A**, **C** and **D** invent criteria the lesson does not use. |
| 10 | **D** | This is the lesson's stated trade-off: dense captures meaning without shared wording but cannot be explained dimension by dimension; sparse is fully explainable but limited to literal overlap. **A** and **B** assert a universal winner the lesson explicitly avoids claiming. **C** contradicts §7.3's measured disagreement between two sparse methods, let alone sparse versus dense. |
| 11 | **C** | The lesson names reciprocal rank fusion and combining both retrieval families as M6-L11's job, explicitly out of scope here. **A**, **B** and **D** are all covered within this lesson or its prerequisites, not deferred. |
| 12 | **A** | Both families represent documents as vectors and score similarity between them; the real differences are dimensionality, sparsity, and how values are assigned — the lesson's organising idea from §3.1 onward. **B**, **C** and **D** contradict definitions and distinctions the lesson establishes explicitly. |

**Q13 rubric (5 marks).** One mark each for: **naming a concrete failing scenario** — a compliance, legal,
or audit context (as in §6) where a match must be explainable to a human reviewer, which dense-only
retrieval cannot structurally provide; **connecting it to the lesson's evidence** — citing §7.2's direct
contrast between a complete "shared words" explanation and an unexplainable "axis0=3.0×2.8" dense
comparison; **naming the OOV risk too** — dense embeddings also cannot handle literal codes or identifiers
that were never assigned a meaningful vector (M6-L01), a second concrete failure mode beyond
explainability; **proposing hybrid retrieval** — combining sparse and dense (M6-L11) rather than replacing
one wholesale with the other; and **not dismissing the real benefit of dense retrieval** — acknowledging
its genuine advantage on paraphrased or synonymous queries, so the pushback reads as a correction, not a
rejection. An answer that only says "dense embeddings aren't perfect" without naming a specific mechanism
or scenario scores 2.

---

<a id="m6-l05"></a>
## M6-L05 — Exact Nearest-Neighbour Search and Its Cost

**Answers: A · C · D · B · A · D · B · C · A · D · B · C**

| Q | Ans | Why, and why the distractors fail |
|---|---|---|
| 1 | **A** | Exact search's defining property is comparing the query against every vector before selecting the top k — the lab's own implementation does exactly this. **B**, **C** and **D** each describe a shortcut that would make the result approximate, not exact. |
| 2 | **C** | The lab measured roughly a 725.8× increase for a 1,000× larger corpus — close to proportional, not the small multiples in **A** or **B**, and directly contradicting **D**'s claim of no change. |
| 3 | **D** | Guaranteeing the true nearest neighbours requires ruling out every vector that isn't one, which requires checking all of them — there is no way to skip a vector and keep the guarantee. **A** contradicts the measured data. **B** and **C** invent mechanisms not present in the algorithm. |
| 4 | **B** | Each dimension is one more term in the dot product computed for every vector, so more dimensions means more work per comparison, multiplied across the whole corpus. **A** and **D** invent unrelated mechanisms. **C** is directly contradicted by §7.3's measured timing increase. |
| 5 | **A** | The two measured scaling factors — linear in N, linear in d — combine multiplicatively into a total cost proportional to N×d, exactly as §5.2 states. **B**, **C** and **D** all contradict measurements from earlier sections. |
| 6 | **D** | The crossover point is specifically the corpus size at which the measured per-vector rate, multiplied by N, exceeds the stated 100ms budget — a statement about this run's hardware and this budget, not a universal limit. **A** and **C** overstate it as a fixed law. **B** confuses a performance limit with a correctness one; exact search remains correct at any size, just slower. |
| 7 | **B** | Exact search's unique property — a correctness guarantee — and its role as the standard other methods are measured against are exactly why the lesson avoids calling it obsolete. **A** is false; it is often the most expensive method at large scale. **C** and **D** are not claims the lesson makes. |
| 8 | **C** | An approximate method's accuracy is defined relative to what exact search would have found — without that reference, "how much accuracy was traded for speed" has no baseline to measure against. **A**, **B** and **D** contradict this relationship directly. |
| 9 | **A** | The lab explicitly states timings are wall-clock on the executing machine and will differ elsewhere — the opposite of **B** and **D**'s universality claims. **C** invents a restriction not present in the lab. |
| 10 | **D** | Any method faster than checking every vector must, by construction, sometimes not check the one vector that would have been the true best match — this is the structural trade-off the lesson sets up for M6-L06. **A**, **B** and **C** name unrelated or unsupported claims. |
| 11 | **B** | Since cost scales linearly with N at a fixed rate, halving the allowed time roughly halves the corpus size that still fits within it. **A** inverts the relationship. **C** and **D** deny that the relationship is linear and predictable, which the lesson's entire measurement exists to establish. |
| 12 | **C** | The lesson's throughline: this cost is not mysterious or undiscoverable — it can be measured at small scale and extrapolated to a specific, actionable number before a launch. **A**, **B** and **D** each contradict a specific measured result from the lab. |

**Q13 rubric (5 marks).** One mark each for: **naming the specific measurement** — running the exact-
search timing method from §7.2 at the staging corpus size and at least one larger size, to establish the
actual per-vector rate on the team's own hardware rather than assuming staging behaviour holds; **stating
the extrapolation** — using that measured rate to estimate query time at the full 50-million-document
production scale, per §7.4's method; **naming the missing requirement** — pointing out that no latency
budget has apparently been stated, and that one is needed before the measurement can be judged pass or
fail; **the decision the measurement should drive** — if the extrapolated time exceeds the latency budget,
the launch should not proceed on exact search alone until an approximate method (M6-L06) or a smaller
effective corpus (filtering, sharding) is in place; and **not treating a single staging number as
sufficient evidence** — explicitly rejecting "it was fast in staging" as adequate proof of production
readiness. An answer that only says "test it at production scale" without naming the specific rate-then-
extrapolate method scores 2.

---

<a id="m6-l06"></a>
## M6-L06 — Approximate Nearest Neighbours and HNSW Intuition

**Answers: B · D · A · C · D · B · C · A · B · A · C · D**

| Q | Ans | Why, and why the distractors fail |
|---|---|---|
| 1 | **B** | Pure random noise gives a clustering method no genuine structure to discover, unlike real embeddings, which cluster by subject the way the lab's topic-based generation deliberately mimics. **A**, **C** and **D** invent constraints unrelated to why the corpus was built this way. |
| 2 | **D** | A query's true nearest neighbours are disproportionately concentrated near its own topic, which closely aligns with a small number of clusters — checking even one captures most of them. **A** overstates a specific measurement into a universal guarantee. **B** contradicts the entire measured trend across nprobe values. **C** invents a cause unrelated to the mechanism. |
| 3 | **A** | Checking half the clusters plus paying the centroid-comparison overhead exceeded the cost of simply scanning every vector directly — a real, measured cost crossover. **B**, **C** and **D** invent failures the lab's actual output does not show; recall in fact rose to 98.3% at this setting. |
| 4 | **C** | Both nprobe and ef control how much of the index is explored before the search stops, directly trading speed for recall — the lesson's explicit parallel. **A**, **B** and **D** name unrelated quantities from earlier lessons. |
| 5 | **D** | The stated stopping rule is exactly this: the walk halts once no neighbour of the current node is closer to the query than the current node itself, which occurred at H. **A**, **B** and **C** invent mechanisms not present in the algorithm as implemented. |
| 6 | **B** | A local minimum is precisely a position where every visible option looks worse, even though a better one exists somewhere the search never reached. **A**, **C** and **D** describe unrelated properties. |
| 7 | **C** | The two methods fail for structurally different reasons — one by cluster assignment, the other by path-dependent graph traversal — which is why their mitigations also differ. **A** and **B** falsely claim one method is infallible. **D** denies a distinction the lesson's comparison table exists to draw. |
| 8 | **A** | The lesson explicitly frames the graph as a small, hand-verified illustration of the search mechanism, distinct from HNSW's actual automated, multi-layer construction. **B**, **C** and **D** overstate or misstate what the example represents. |
| 9 | **B** | With genuine topic structure, a query's true neighbours cluster together and align well with a modest number of k-means clusters, which is exactly why low nprobe still recovers most of them. **A**, **C** and **D** are not supported by anything in the lab's design or output. |
| 10 | **A** | This is the lesson's central, repeatedly demonstrated trade-off: checking less costs some accuracy and buys speed, in a measurable, tunable relationship. **B** contradicts the nprobe=50 result directly. **C** and **D** deny a relationship the entire lab exists to quantify. |
| 11 | **C** | An approximate method's value proposition — "close enough, much faster" — is only measurable against what exact search would have found, which is why it remains the reference standard rather than being discarded. **A**, **B** and **D** all contradict this ongoing role. |
| 12 | **D** | Every number in the lab is tied to this specific synthetic corpus, cluster count, and the executing machine's hardware — re-measurement on real data is required before trusting a parameter choice elsewhere. **A**, **B** and **C** misstate what the lab's disclaimers actually say. |

**Q13 rubric (5 marks).** One mark each for: **naming the contradicting result** — nprobe=50 was measured
at 0.2x speedup, meaning that configuration was five times SLOWER than simply using exact search, directly
refuting "more thorough can only help"; **explaining why** — checking more clusters (or a wider ef) adds
real computational cost on top of the centroid/entry-point overhead, and past a point that cost exceeds
what exact search would have cost outright; **naming the actual trade-off** — recall rises with
nprobe/ef but with diminishing returns, while cost rises steadily, so there is a real optimum rather than
a monotonically "safer" direction; **proposing measurement over intuition** — recommending the team
measure their own recall-vs-speed curve (per §7.2's method) on real data and pick a value with a
justified margin, not a maximal one; and **connecting it to production risk** — noting that an
over-tuned parameter can silently cost more in latency or compute than it saves in accuracy, exactly the
kind of regression that would not be caught without ongoing measurement (§6). An answer that only says
"test it first" without naming the specific slower-than-exact result scores 2.

---

<a id="m6-l07"></a>
## M6-L07 — Vector Indexes vs Vector Databases

**Answers: D · B · C · A · D · C · B · A · D · B · A · C**

| Q | Ans | Why, and why the distractors fail |
|---|---|---|
| 1 | **D** | The tombstone only records that an id is deleted; nothing about the search computation changes, so the same comparisons run and the measured query time stayed the same. **A**, **B** and **C** invent mechanisms not present in the lab's actual implementation. |
| 2 | **B** | Rebuilding recomputes cluster assignments and centroids from the reduced data, which is genuinely expensive computation, unlike a tombstone's near-zero-cost set update. **A** contradicts the measured order of magnitude. **C** is false; k-means ran successfully on the reduced corpus. **D** is refuted by the rebuild succeeding. |
| 3 | **C** | Exactly the trade-off measured: fast-but-incomplete versus correct-but-costly, with nothing occupying a cheap-and-correct middle ground in this method. **A**, **B** and **D** overstate or misstate the actual limitation. |
| 4 | **A** | Serialization required explicit `pickle` calls the lab wrote itself — a library did not do this automatically. **B**, **C** and **D** invent behaviour the lab's code does not exhibit. |
| 5 | **D** | With no persistence code, nothing outlives the process; a crash means starting over from source data. **A**, **B** and **C** invent recovery mechanisms that do not exist by default. |
| 6 | **C** | The comparison table explicitly lists concurrent reads/writes as something a bare index does not provide by default. **A**, **B** and **D** are capabilities the index in this lab does provide. |
| 7 | **B** | The lesson's stated position is that the right choice is requirement-dependent, not a fixed ranking of one option over the other. **A** denies the real differences §5.3 lists. **C** and **D** both assert exactly the kind of universal preference the lesson argues against. |
| 8 | **A** | The lesson explicitly names M6-L09 as filtering's full treatment, keeping this lesson's table as a pointer rather than a duplicate. **B** and **C** are false claims the lesson does not make. **D** misattributes the topic to an earlier lesson that covered something different (exact vs semantic matching). |
| 9 | **D** | Both measured sections point to the same conclusion: the algorithm is present, but persistence, real deletion, and (by extension) concurrency are not, without deliberate extra work. **A** collapses a distinction the lesson insists on. **B** and **C** overstate a preference between the two operations that the lesson does not take. |
| 10 | **B** | The lesson states plainly that timings are tied to this corpus, this hardware, and the specific serialization library used — none of which generalise automatically. **A**, **C** and **D** invent unrelated or false claims. |
| 11 | **A** | A vector database's job, per the table, is adding persistence, filtering and concurrency around an underlying search algorithm — not replacing the algorithm itself. **B**, **C** and **D** contradict this framing. |
| 12 | **C** | The lesson's closing section explicitly names pgvector, hands-on, as M6-L08's job. **A**, **B** and **D** name topics covered elsewhere or already established. |

**Q13 rubric (5 marks).** One mark each for: **applying the checklist** — walking through §5.3's rows
(persistence, true deletion, filtering, concurrency, backups) against the stated system's actual
description (fixed, rarely-changing, single-user); **naming which rows are NOT required** — concurrent
access and frequent deletion are explicitly absent from the scenario, and persistence needs may be
satisfiable much more simply than a full managed service; **the cost of the colleague's proposal** —
operational overhead (§5.3's last row) is a real, ongoing cost, not a free safety margin, for a system
that does not need most of what a database provides; **a concrete alternative** — a bare index plus a
simple, explicit persistence step (§7.2's approach: serialize to a file on build, reload on startup) as
sufficient for a fixed, low-concurrency prototype; and **not dismissing "safety" entirely** — acknowledging
that if the prototype is expected to grow into a system with real concurrent access or frequent updates,
revisiting the decision later is reasonable, rather than ruling out a database forever. An answer that
only says "we don't need a database" without walking through specific checklist rows scores 2.

---

<a id="m6-l08"></a>
## M6-L08 — pgvector Hands-On (and How Alternatives Differ)

**Answers: C · A · D · B · C · D · A · B · C · A · D · B**

| Q | Ans | Why, and why the distractors fail |
|---|---|---|
| 1 | **C** | The three-operator agreement-after-normalisation result is the exact identity M6-L02 established generally, reproduced here under pgvector's specific operator names. **A** dismisses a result that follows from a proven mathematical identity, not chance. **B** misreads a normalisation requirement as unreliability. **D** invents a dimensionality restriction the identity does not have. |
| 2 | **A** | `<#>` omits the division by vector norms that `<=>` performs, which is cheaper — but that shortcut is only equivalent to cosine distance when every stored vector already has unit length. **B**, **C** and **D** state properties `<#>` does not have. |
| 3 | **D** | `ivfflat` is the clustering-based family and `hnsw` the graph-based family, both built and measured directly in M6-L06 — pgvector exposes the same algorithms through SQL. **A** and **C** misdescribe the relationship the lesson establishes explicitly. **B** confuses index type with distance operator, a different axis entirely. |
| 4 | **B** | The lesson states plainly that the table was reproduced from M6-L06's own executed run to show the parameter-name mapping, not measured fresh. **A** and **D** contradict this stated sourcing. **C** dismisses real, previously executed measurements as fabricated. |
| 5 | **C** | The lesson explicitly states no PostgreSQL/pgvector instance was available in the authoring environment, which is why the SQL is marked for the reader to verify rather than labelled executed. **A**, **B** and **D** are not true and not claimed anywhere in the lesson. |
| 6 | **D** | This is COURSE_PLAN.md's own stated reasoning, quoted directly in the lesson: one system for rows and vectors, building on relational knowledge already gained, no new vendor account. **A**, **B** and **C** are claims neither the course nor pgvector's own documentation makes. |
| 7 | **A** | The fallback lab computes real distance-operator arithmetic and reproduces M6-L06's parameter mapping — it explicitly runs no SQL and touches no database, as its own closing section states. **B**, **C** and **D** describe things the lab does not do. |
| 8 | **B** | Skipping normalisation-aware computation for speed on data that was never normalised produces a ranking that diverges from true cosine distance — fast, but wrong, exactly as measured in §7.1. **A**, **C** and **D** contradict the lesson's stated mechanism. |
| 9 | **C** | Both parameters control how much of the index is searched before stopping, the identical trade-off M6-L06 measured under different names (nprobe, search-width). **A**, **B** and **D** name unrelated settings. |
| 10 | **A** | Because the underlying algorithms are identical, the recall/speed relationship is mathematically the same regardless of which system exposes it, and no live pgvector instance existed to re-measure it independently here. **B**, **C** and **D** contradict this stated reasoning. |
| 11 | **D** | The lesson explicitly ties its approach back to COURSE_PLAN.md's own design assumption A2, naming it as a deliberate, stated principle rather than an ad hoc fix. **A**, **B** and **C** mischaracterise this as improvised, absent, or universal in a way the lesson does not claim. |
| 12 | **B** | M6-L08 is framed throughout as putting M6-L06 and M6-L07's already-taught concepts into real SQL, not introducing a competing or contradictory account. **A**, **C** and **D** misstate this relationship. |

**Q13 rubric (5 marks).** One mark each for: **naming the first, cheapest check** — verifying the `ORDER
BY` direction on the distance operator, since sorting a distance descending silently returns the worst
matches while producing no error, exactly as in §5's worked example; **explaining why this is the prime
suspect** — a query that "runs without error" but returns unrelated results, with no crash, is the
signature of this specific mistake rather than a broken index or a bad embedding model; **naming a second
check** — confirming vectors were normalised consistently at insert time if `<#>` is in use, since that is
the other way to get fast, wrong-looking results (§4.3); **proposing a concrete test** — running a known
query against a known-relevant document and confirming it is actually returned near the top, rather than
only checking that the query executes; and **not jumping to a bigger architectural change** — the answer
should treat this as a likely small, specific SQL bug to check first, not evidence the whole approach or
system needs replacing. An answer that proposes re-architecting the search feature without first checking
sort direction scores 2.

---

<a id="m6-l09"></a>
## M6-L09 — Metadata, Filtering and Filtered-ANN Pitfalls

**Answers: D · B · A · C · D · A · B · C · D · B · C · A**

| Q | Ans | Why, and why the distractors fail |
|---|---|---|
| 1 | **D** | The search committed to a fixed top-10 by score before the category filter ever ran, so any of the 10 not belonging to the requested category were simply discarded, with no chance for lower-ranked genuine matches to take their place. **A**, **B** and **C** invent faults in components the lab's design shows were never at issue. |
| 2 | **B** | Filtering first and searching only the matching subset exactly guarantees the true top-k within that subset is found, at a cost tied directly to the subset's size — exactly what §7.2 measured. **A** contradicts the measured results directly. **C** overclaims a universal speed advantage the lesson explicitly says erodes with lower selectivity. **D** ignores that exact search still has to run. |
| 3 | **A** | 24,847 of 50,000 vectors is almost exactly half, and the measured time was almost exactly half of full-corpus exact search — M6-L05's linear-scaling result applied directly. **B**, **C** and **D** do not match the measured proportional relationship. |
| 4 | **C** | As the matching subset grows toward the full corpus, exact search over that subset costs correspondingly more, approaching full-corpus exact search cost and erasing the approximate index's advantage. **A**, **B** and **D** contradict this measured, proportional relationship. |
| 5 | **D** | Section 1's actual mechanism was ranking first, by score, and filtering only the resulting fixed-size set afterward — exactly what the correction reverses. **A**, **B** and **C** name changes unrelated to the ordering bug the lesson identifies. |
| 6 | **A** | With roughly 500 members per cluster and 5% category selectivity, even one cluster already contains close to enough matches once filtering happens on the whole pool, so widening the search adds only a small margin. **B**, **C** and **D** contradict the measured, if modest, improvement from 9.9 to 10.0. |
| 7 | **B** | The lab's own conclusion states this explicitly: the fix was filtering at the correct stage, not needing a larger pool, which the small nprobe-driven improvement in section 3 confirms. **A**, **C** and **D** misattribute the cause to something the measurements do not support. |
| 8 | **C** | Each strategy trades one failure mode for a different, real cost — insufficient results versus rising computation — which is precisely why the lesson presents both rather than declaring a single winner. **A** and **D** deny real differences the sections measure directly. **B** contradicts §7.2's explicit cost figures. |
| 9 | **D** | The lesson names this directly as product- and version-specific engineering outside its scope, distinct from the two general strategies it does cover in full. **A**, **B** and **C** are topics covered in other lessons, not this one's stated gap. |
| 10 | **B** | Filtering does not introduce a new search algorithm — it changes what gets counted as a match within the same recall/speed mechanics M6-L05 and M6-L06 already measured, and the stage at which filtering happens determines whether those mechanics work in your favour. **A**, **C** and **D** overstate filtering as invalidating prior lessons, which the text explicitly does not claim. |
| 11 | **C** | This is the exact condition the lab's own narration attaches to the 9.9-of-10 result — filtering the pool before truncation, not after. **A**, **B** and **D** describe conditions not present in that specific measurement. |
| 12 | **A** | This is the lesson's stated synthesis: correct filter ordering first, with both selectivity and search-width treated as levers with measurable costs, rather than assuming any naive combination works. **B**, **C** and **D** each assert an absolute the lesson's own trade-off analysis rules out. |

**Q13 rubric (5 marks).** One mark each for: **naming the first check** — whether the filter is applied
before or after the search truncates to a fixed top-k, since that ordering bug produces exactly this
symptom for a low-selectivity value; **explaining why nprobe is not the first suspect** — §7.3 measured
that correcting filter order recovered nearly all results even at the smallest possible search width,
while widening the search alone (without fixing order) does not address the root cause; **proposing a
concrete diagnostic** — comparing the current (likely post-filter) implementation against a pre-filter-
then-exact-search version on the same query, to see whether correctness returns immediately per §5.2/§6;
**quantifying the cost trade-off** — noting that if the fix is pre-filtering, its cost will scale with
that filter's selectivity, which is worth measuring before committing to it broadly; and **not dismissing
nprobe entirely** — acknowledging it can still help at the margin once ordering is fixed, rather than
implying it is useless. An answer that jumps straight to "increase nprobe" without checking filter order
first scores 2.

---

<a id="m6-l10"></a>
## M6-L10 — Indexing, Updates, Deletion and Re-embedding

**Answers: A · C · D · B · A · D · C · B · A · D · B · C**

| Q | Ans | Why, and why the distractors fail |
|---|---|---|
| 1 | **A** | The unadded vectors have no representation in the index at all, so any true top-10 member among them cannot be returned regardless of search quality — an availability gap, not a ranking one. **B**, **C** and **D** invent faults unrelated to what the experiment actually varied. |
| 2 | **C** | State B's centroids were fit only on the original 25,000 vectors' topic distribution, which under-represents the topics introduced later, while State C's centroids were fit on the true, final distribution. **A** and **D** describe conditions that were held constant between the two states. **B** is false; State B's index does contain all 50,000 vectors, just organised around stale centroids. |
| 3 | **D** | The lesson states this explicitly, including that an earlier version of the experiment without this design choice showed almost no degradation, which is why the corpus generation was changed. **A**, **B** and **C** are not the stated reasons and do not match the lesson's own account. |
| 4 | **B** | This is exactly what section 1 measured: a near-instant operation that recovers most, but not all, of a full rebuild's recall. **A** contradicts the measured 2-point gap. **C** contradicts the measured near-zero cost. **D** is false; the technique shown applies to the clustering-based family specifically. |
| 5 | **A** | M6-L02's finding — that two models produce vector spaces with no shared meaning per dimension — makes comparing vectors from each equally invalid regardless of how the mixing happens. **B**, **C** and **D** invent reasons unrelated to the actual, structural incompatibility. |
| 6 | **D** | Because no intermediate mixed state is safe, the only sound approach is building a fully separate, internally consistent new index and switching to it at one moment. **A**, **B** and **C** name unrelated or false justifications. |
| 7 | **C** | The lesson names this step explicitly, tying it directly to M5-L18's evaluation discipline applied to a vector index instead of a prompt. **A**, **B** and **D** contradict the stated, ordered migration steps. |
| 8 | **B** | The lesson states plainly that the extrapolation reuses the lab's own measured rebuild rate and explicitly excludes embedding-inference cost as a separate, often larger expense. **A**, **C** and **D** misstate the actual source of the numbers. |
| 9 | **A** | The lesson frames itself directly as covering the addition and migration side of the lifecycle M6-L07 began by measuring deletion. **B**, **C** and **D** deny a relationship the lesson establishes in its own framing and cross-references. |
| 10 | **D** | The lesson's own "what this lab is and is not" section names this specifically as left to a team's own monitoring and operational choices. **A**, **B** and **C** are covered within this lesson or its prerequisites, not left open. |
| 11 | **B** | The large jump from A to B, followed by a much smaller jump from B to C, is exactly the shape the lesson highlights — most of the value is in adding data at all, with a real but secondary gain from a full rebuild. **A**, **C** and **D** contradict the measured percentages directly. |
| 12 | **C** | This is the lesson's stated synthesis across both halves of the lifecycle — a real, useful middle option for addition, and no middle option at all for a model change. **A**, **B** and **D** each assert an absolute the lesson's own measurements and reasoning rule out. |

**Q13 rubric (5 marks).** One mark each for: **naming the actual mechanism** — cluster drift, where
centroids fit on an earlier, smaller version of the corpus increasingly under-represent newly introduced
topics or categories, exactly as measured in §7.1; **connecting it to the specific pattern observed** —
noting that decline concentrated in recently-added categories is the expected signature of this mechanism,
not a sign of a broken index or bad embeddings; **proposing a concrete measurement** — computing recall@k
for queries representative of the newer content against the current index, to confirm and quantify the
drift before acting; **proposing the fix** — scheduling a full rebuild (and considering a recurring
schedule going forward, sized against corpus growth rate) rather than continuing incremental-only updates
indefinitely; and **adding an ongoing control** — recommending recall@k be tracked over time as a
production metric so the next instance of this drift is caught proactively rather than reported by users a
year later. An answer that proposes only "rebuild the index" without diagnosing cluster drift as the cause
scores 2.

---

<a id="m6-l11"></a>
## M6-L11 — Hybrid Search and Reciprocal Rank Fusion

**Answers: B · A · C · D · A · C · B · D · A · C · B · D**

| Q | Ans | Why, and why the distractors fail |
|---|---|---|
| 1 | **B** | BM25 and cosine occupy different ranges and mean different things at any given value, so a direct sum lets whichever method's numbers are larger dominate the ranking regardless of relevance. **A**, **C** and **D** invent constraints that play no role in why the sum is unsound. |
| 2 | **A** | RRF discards raw scores entirely and sums a function of rank position alone, which is exactly what sidesteps the scale problem section 1 demonstrated. **B**, **C** and **D** describe mechanisms RRF does not use. |
| 3 | **C** | `1 / (60 + 1) = 1/61 ≈ 0.0164`, direct arithmetic on the stated formula. **A**, **B** and **D** misapply the formula. |
| 4 | **D** | The measured ratio between the best and worst document's score fell to about 1.07 at k=60 on this six-document corpus — a large k relative to corpus size compresses rank differences nearly away. **A** contradicts the table's own changing numbers. **B** and **C** assert absolutes the table does not support. |
| 5 | **A** | This is the lesson's own stated takeaway from the k-sensitivity table — k must match how many results actually need distinguishing. **B**, **C** and **D** either contradict the demonstrated sensitivity or invent an unrelated rule. |
| 6 | **C** | BM25 has no mechanism to score a document containing none of the query's literal terms; D6 shares zero words with the query. **A**, **B** and **D** invent causes unrelated to BM25's actual mechanism. |
| 7 | **B** | D2, D5 and D6 all point along the same "refund-only" axis in this toy vector space, so a query centered between two concepts is mathematically equidistant from all three regardless of surface wording. **A**, **C** and **D** misread a genuine structural property as an error. |
| 8 | **D** | D4 is (BM25 rank 5, dense rank 6) and D6 is (BM25 rank 6, dense rank 5) — the same rank pair, swapped between methods — and RRF's symmetric sum across methods produces identical totals for such a swap. **A** and **B** assert an outcome the measured scores contradict. **C** is false; both remain in the ranking. |
| 9 | **A** | This is the lesson's own stated, honest reading: the toy scale cannot show rank-lift directly, but the real, general-purpose mechanism (a hard zero versus a real score) is validly demonstrated. **B**, **C** and **D** overreact to one small example's outcome with conclusions the lesson explicitly does not draw. |
| 10 | **C** | The lesson explicitly frames RRF as a principled way to combine the two previously-established methods by rank, not to replace or favor either one. **A**, **B** and **D** contradict the lesson's stated framing and its own measured disagreements between the two methods. |
| 11 | **B** | Section 4 states plainly that the hand-built word vectors stand in for a real trained embedding model, while the BM25 and RRF formulas themselves are exact. **A**, **C** and **D** name components the lesson labels as real, not illustrative. |
| 12 | **D** | This is the lesson's stated general rule, following directly from sections 1 and 2's findings taken together. **A**, **B** and **C** each reintroduce the raw-score combination problem section 1 exists to rule out. |

**Q13 rubric (5 marks).** One mark each for: **stating the core problem with combining raw scores** — that
BM25 and dense scores live on incompatible scales, so a document's fused rank should not depend on which
method happens to produce larger numbers; **naming the actual mechanism RRF uses** — fusing rank position
via `1/(k+rank)` rather than raw score, exactly as computed in §7.2; **identifying the specific signal
difference that lets hybrid search recover a paraphrase** — a document sharing no literal terms with the
query scores a hard, uninformative zero under BM25 but a real, meaningful score under dense retrieval,
exactly as measured for D6 in §7.3; **acknowledging that a real signal difference does not guarantee a
clean rank improvement on any given small example** — the honest reporting of D6's tie with an irrelevant
document; and **stating the practical implication** — that this signal difference is what reliably lifts
paraphrased or reworded content at real production scale, even where a small demonstration cannot show the
lift directly. An answer that says only "combining both methods works better" without naming the upstream
score-behavior difference scores 2.

---

<a id="m6-l12"></a>
## M6-L12 — Cross-Encoder Reranking

**Answers: A · D · A · D · D · C · B · B · A · C · C · B**

| Q | Ans | Why, and why the distractors fail |
|---|---|---|
| 1 | **A** | Mean pooling discards word order, and "not" contributes an all-zero vector like any other near-neutral function word, so the pooled vector for the negated sentence lands close to the pooled vector for the plain positive statement. **B**, **C** and **D** invent causes unrelated to how pooling actually works. |
| 2 | **D** | The document vector is fixed before any query or comparison happens, and pooling is order-independent, which is exactly what discards the signal negation depends on. **A**, **B** and **C** misattribute a structural, architectural property to training, vocabulary, or the similarity metric. |
| 3 | **A** | The scorer inspects the actual token sequence and the local context around a key term, which is only possible because it never collapses the document into one pooled vector first. **B**, **C** and **D** describe mechanisms the lab's code does not use. |
| 4 | **D** | A cross-encoder's output is defined only once both the query and the document are known together — there is no document-only quantity to compute in advance. **A**, **B** and **C** name unrelated or invented constraints. |
| 5 | **D** | ANN indexes are built over a fixed set of precomputed vectors that exist before any query arrives; a cross-encoder never produces such a vector for a document alone. **A**, **B** and **C** invent limitations unrelated to the actual, structural reason. |
| 6 | **C** | The extrapolation table shows the cross-encoder-style total reaching over 112 seconds against the bi-encoder's 268ms at 10,000 queries — a gap of more than two orders of magnitude, growing linearly with query count. **A**, **B** and **D** contradict the measured, extrapolated figures directly. |
| 7 | **B** | Because nothing about a cross-encoder's score can be reused across queries, its cost is paid in full for every candidate on every query, which is only affordable when the candidate count is kept small. **A**, **C** and **D** state claims the lesson does not make and that do not follow from the cost argument. |
| 8 | **B** | The shortlist's retrieval order put the negated document first; reranking that same short list corrected the order, and stayed cheap specifically because only four candidates were rescanned rather than the full corpus. **A** and **C** contradict the printed rankings directly. **D** ignores that reranking only had a shortlist to work with because retrieval produced one first. |
| 9 | **A** | Section 7.5 states explicitly that comparing a real trained model's learned scope against a hand-written rule requires an actual trained model, which this lab does not run. **B**, **C** and **D** are all things the lab does demonstrate, directly contradicting what the question asks for. |
| 10 | **C** | This is the lesson's stated general pattern, drawn directly from combining sections 5.3's cost argument and 5.4's demonstration. **A**, **B** and **D** each discard one of the two stages the lesson argues both stages are needed for. |
| 11 | **C** | The investigation traced the slowdown to the reranker running against an unbounded filtered pool rather than a small, fixed shortlist — exactly the cost structure section 5.3 measured. **A**, **B** and **D** name causes the worked example explicitly rules out. |
| 12 | **B** | Because cost is paid per candidate with no reuse, the candidate count passed to the reranker is the lever that determines total cost, more directly than any property of the model or corpus size alone. **A**, **C** and **D** name factors the lesson does not identify as the primary cost lever. |

**Q13 rubric (5 marks).** One mark each for: **naming the mechanism that lets a cross-encoder succeed** —
reading the query and document jointly (e.g. via attention over the concatenated pair), rather than
comparing two independently pooled vectors, letting it represent interactions like negation, exactly as
demonstrated in §7.1–§7.2; **connecting this to a bi-encoder's specific failure** — that pooling each side
separately, before any comparison, discards word order and the attachment of words like negation;
**identifying the cost consequence as arising from the SAME property** — that a score existing only once
query and document are known jointly cannot be precomputed, cached, or indexed per document, as measured in
§5.3/§7.3; **stating the practical result** — that this cost must be paid in full, per candidate, on every
query, which only stays affordable over a small shortlist; and **concluding with the design implication** —
that cross-encoders are therefore used to rerank a retrieval-produced shortlist, never to search a full
corpus directly. An answer that only says "cross-encoders are more accurate but slower" without connecting
both properties to the shared joint-scoring mechanism scores 2.

---

<a id="m6-l13"></a>
## M6-L13 — Retrieval Metrics: Precision@k, Recall@k, MRR, nDCG and Relevance Labels

**Answers: A · A · D · A · B · D · C · C · B · D · C · B**

| Q | Ans | Why, and why the distractors fail |
|---|---|---|
| 1 | **A** | The two queries shared k=5 but had different total relevant-document counts, producing different Recall@5 values purely from that difference — proof the two metrics only coincide in the special case where the relevant count equals k. **B**, **C** and **D** state false or invented constraints on the two metrics. |
| 2 | **A** | This is Precision@k's exact definition, matching the lesson's own formula. **B** is Recall@k's definition, not Precision@k's. **C** and **D** invent formulas the lesson never uses. |
| 3 | **D** | This is Recall@k's exact definition, matching the lesson's own formula. **A** is Precision@k's definition, not Recall@k's. **B** and **C** invent formulas the lesson never uses. |
| 4 | **A** | MRR is built around a single correct answer's position, exactly the exact-lookup task shape the lesson introduces it for. **B**, **C** and **D** describe conditions unrelated to what makes MRR the right metric. |
| 5 | **B** | Reciprocal rank is defined as 1/rank; rank 2 gives 1/2 = 0.5, matching the lab's printed value exactly. **A**, **C** and **D** misapply or invert the formula. |
| 6 | **D** | A query with no correct answer present contributes a reciprocal rank of exactly 0, which is what the lab computed and used in the MRR average. **A**, **B** and **C** describe handling the lab's code does not perform. |
| 7 | **C** | nDCG's discount is sensitive to WHERE in the ranking a relevant document sits, unlike Precision@k/Recall@k, which only check membership in the top k. **A**, **B** and **D** name factors unrelated to what nDCG measures. |
| 8 | **C** | DCG's discount term is `1/log2(rank+1)`, a function of rank position alone, shrinking as rank increases. **A**, **B** and **D** invent discount bases the formula does not use. |
| 9 | **B** | Dividing by IDCG rescales DCG into a [0, 1] range that stays comparable across queries with different numbers of relevant documents or different grade distributions. **A**, **C** and **D** misstate what normalization does. |
| 10 | **D** | Section 7.4 held the ranking completely fixed and varied only the relevance-label threshold, and Recall@5 still moved — direct evidence the ranking itself was not the cause. **A**, **B** and **C** name changes the lab's own code did not make. |
| 11 | **C** | Section 7.5 computed all four side by side specifically to show each highlights a different aspect (top-result strength, coverage, ordering) that the others do not capture alone. **A**, **B** and **D** all assert a false equivalence or replacement the section does not support. |
| 12 | **B** | This is the lesson's own stated bridge to M3-L14: the same underlying precision/recall concept, applied per-query to a ranked list's top-k truncation instead of to one classification decision over a whole dataset. **A**, **C** and **D** deny or misstate a relationship the lesson explicitly draws. |

**Q13 rubric (5 marks).** One mark each for: **naming the missing relevance-label definition** — asking how
"relevant" was defined (binary or graded, what threshold or judgment produced the label), exactly as
demonstrated moving Recall@5 from 1.00 to 0.83 in §7.4 with the ranking held fixed; **asking about k and
its relationship to the true relevant-set size** — since Recall@k's meaning depends on how many relevant
documents actually exist, per §5.1; **asking about the query set and corpus the number was measured
against** — since a metric change can come from either shifting, not just from the ranking, as illustrated
in §6; **connecting this to the general principle** — that a retrieval metric is a function of the ranking,
the relevance labels, and the query/corpus together, not the ranking alone; and **stating the practical
consequence** — that without this information the number cannot be trusted for a go/no-go decision or
diagnosed if it changes later. An answer that only says "we'd need more context" without naming at least
two of the three specific missing pieces (labels, k vs. relevant-set size, query/corpus stability) scores 2.

---

*Module 6 is complete: all 13 lessons (M6-L01 through M6-L13) are answered above.*
