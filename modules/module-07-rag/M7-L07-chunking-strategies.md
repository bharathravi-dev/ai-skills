# M7-L07 — Chunking II: Fixed, Recursive, Sentence, Semantic, Structure-Aware

| | |
|---|---|
| **Lesson ID** | M7-L07 |
| **Difficulty** | 3 (Advanced) |
| **Estimated study time** | 2.25 hours |
| **Prerequisites** | [M7-L06](M7-L06-chunking-size-overlap-boundaries.md) |

---

## 1. Learning objectives

1. **Implement** recursive splitting and explain why trying coarse separators before fine ones produces
   better-aligned chunks without needing preserved structure metadata.
2. **Implement** sentence-boundary splitting and identify a real, common failure case (abbreviations) it
   does not handle correctly.
3. **Implement** semantic chunking and explain how it finds topic boundaries in text with no structural
   markup at all.
4. **Extend** structure-aware chunking beyond headings to lists and code blocks, and explain why splitting
   code is a sharper failure than splitting prose.
5. **Select** an appropriate chunking strategy (or combination) for a given document's characteristics.

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **Recursive splitting** | Trying the coarsest separator first (e.g. paragraph breaks), recursing into progressively finer separators only for pieces that remain too large. |
| **Sentence splitting** | Chunking at sentence boundaries, typically detected via punctuation-based rules. |
| **Semantic chunking** | Splitting text where the similarity between consecutive units (e.g. sentences) drops, signaling a topic shift — independent of any explicit structural markup. |
| **Structure-aware chunking** | Chunking that respects a document's explicit structural elements (headings, lists, code blocks) as indivisible units. |
| **Topic shift** | A point in a document where the subject matter changes, detectable via a drop in semantic similarity between adjacent content. |

---

## 3. Plain-language explanation

### 3.1 M7-L06 established the trade-offs; this lesson gives you the tools

M7-L06 showed that chunk size, overlap, and boundaries all matter, measurably. It used only two chunking
methods — naive fixed-size and one heading-aware splitter — to make that case. This lesson is the toolbox
of specific algorithms real systems actually choose between.

### 3.2 Recursive splitting: try the big cut first

§7.1 shows a splitter that doesn't commit to one separator. It tries a paragraph break first; only when a
resulting piece is still too large does it recurse into a finer separator. This produces chunks aligned to
real content boundaries using nothing but the text's own punctuation and spacing — no preserved metadata
required, unlike M7-L06's heading-based approach.

### 3.3 Sentence splitting works — until it hits an abbreviation

§7.2 doesn't just show sentence splitting succeeding on clean text. It shows it failing, honestly and
reproducibly, on text containing "Dr." and "U.S." — a real, common category of text this simple approach
cannot handle without an explicit exception list.

### 3.4 Semantic chunking finds boundaries with zero explicit structure

§7.3 is this lesson's most distinct idea: given four consecutive sentences with no headings, no blank
lines, not even a paragraph break, semantic chunking still correctly finds where the topic changes — using
similarity between adjacent sentences, the same mechanism (pooling and cosine similarity) M6-L01
introduced for query-document matching, now applied sentence-to-sentence.

### 3.5 Structure-aware chunking generalizes past headings

§7.4 extends M7-L06's heading-only structural awareness to lists and fenced code blocks — and makes the
case for why code specifically deserves this treatment: a broken code fragment isn't just less precise,
it's not valid content at all.

---

## 4. Analogy

**Editing a manuscript with different tools for different jobs.** Recursive splitting is like an editor who
first tries to break a manuscript at chapter breaks, and only splits a chapter into scenes if it's still too
long for one sitting — always preferring the biggest natural break that still fits. Sentence splitting is
like an editor who breaks text at every period — quick, usually right, and occasionally wrong in a
predictable way (splitting "Mr. Smith" as if "Mr." ended a sentence). Semantic chunking is like an editor
with no chapter markers at all, who reads the manuscript and notices, purely from the content, exactly
where one scene's mood and subject give way to the next. Structure-aware chunking is like an editor who
knows never to cut a recipe's ingredient list or a diagram's caption in half, regardless of length, because
half a recipe is worse than useless.

### Where the analogy breaks

- **A human editor exercises judgment continuously, blending all these approaches at once instinctively.**
  Each of this lesson's algorithms is a distinct, separately-implemented mechanism — combining them (an
  exercise topic) requires deliberate engineering, not instinct.
- **A manuscript's chapters are usually unambiguous.** §7.3's semantic boundary is a threshold-based
  judgment call (as sensitive as M6-L11's RRF `k` or M7-L05's shingle size), not an unambiguous fact the
  way a chapter heading is.

---

## 5. Detailed technical explanation

### 5.1 Recursive splitting, measured

`[REAL]` §7.1 split a 274-character, 3-paragraph document at a fixed 120 characters (cutting mid-paragraph,
mid-sentence) versus recursively (paragraph breaks first; falling back to `". "` only for the one paragraph
still over 120 characters after that split). The recursive version produced 4 clean chunks, each ending at
a real paragraph or sentence boundary — **using only the text's own blank lines and punctuation, with no
preserved heading structure required at all.**

### 5.2 Sentence splitting, and its real limit

`[REAL, measured]` §7.2 correctly split clean text into 3 sentences using a punctuation-plus-capitalization
regex. The same function, given "Contact Dr. Smith for approval. He reports to the U.S. division head.",
produced **"Contact Dr."** and **"Smith for approval."** as two separate, broken fragments — the
abbreviation's period was indistinguishable from a sentence-ending period. **This is not a contrived
example**: abbreviations, initials, and decimal numbers are routine in real business and legal documents,
and a purely punctuation-based splitter has no way to tell them apart without an explicit exception list or
a trained model.

### 5.3 Semantic chunking, with zero markup

`[REAL, measured]` §7.3 computed cosine similarity (M6-L01's exact mechanism) between four consecutive
sentences with no headings, blank lines, or any structural markup at all. Similarity was **1.000** between
the two remote-work sentences, dropped to **0.000** between the second remote-work sentence and the first
revenue sentence, then returned to **1.000** between the two revenue sentences. At a 0.5 threshold, the
single drop correctly located the exact topic boundary. **This is the one strategy in this lesson that
needs no explicit structure of any kind** — it finds the boundary from meaning alone.

### 5.4 Structure-aware chunking, extended to lists and code

`[REAL, measured]` §7.4 extended M7-L06's heading-only boundary awareness to also treat a bullet list and a
fenced code block as indivisible units. Fixed-size chunking at 70 characters split the code block's
`port: 443` line across two chunks; structure-aware chunking kept the entire code block — list included —
in one chunk. **Splitting prose mid-sentence produces an awkward but still partially readable fragment;
splitting code produces a fragment that is not valid configuration at all** — a categorically sharper
failure, because code has no tolerance for being "mostly right."

### 5.5 All strategies, side by side

`[REAL]` §7.5 tabulated chunk counts across all five documents and strategies used in this lesson. **No
single number or strategy is "correct" in isolation** — each is suited to a different document
characteristic: fixed-size to none in particular (cheapest, least aware), recursive to generic textual
structure, sentence splitting to grammar (with a known caveat), semantic to meaning with no markup, and
structure-aware to explicit formatting elements a heading-only approach would still miss.

### 5.6 Assumptions and limitations

- §5.2's sentence splitter is deliberately simple, chosen to demonstrate a real limitation rather than to
  be production-ready — real systems typically use an explicit abbreviation list or a trained sentence
  tokenizer.
- §5.3's semantic-chunking threshold (0.5) and hand-built word vectors are illustrative, not a trained
  embedding model's real output. The underlying mechanism (similarity drop signals topic shift) is real and
  used in production semantic chunkers.
- This lesson does not measure chunking cost or latency at real corpus scale, nor does it combine multiple
  strategies (e.g. recursive plus structure-aware) in a single pipeline — both are left to the exercises.

---

## 6. Worked example — the runbook that became useless after chunking

**The system.** An internal documentation assistant ingests operational runbooks, including configuration
snippets and step-by-step command lists, using fixed-size chunking with no structure awareness — the same
approach that had worked adequately for prose-only policy documents.

**What went wrong.** Engineers querying for a specific configuration value routinely received a chunk
containing half a YAML snippet, syntactically incomplete and impossible to use directly, or a numbered
command list missing its final step because a chunk boundary happened to fall between steps 4 and 5.

**Why prose-tuned chunking failed specifically here.** Per §5.4, the failure mode this exposes is sharper
for code and structured lists than it ever was for the prose-only documents the pipeline was originally
tuned against — a half-sentence is annoying; half a working configuration is useless, and a command list
missing its last step can be actively misleading (implying the procedure is complete when it isn't).

**Three defects:**

| # | Defect | Consequence |
|---|---|---|
| 1 | Chunking was never updated when the corpus expanded to include runbooks with code and ordered steps | A strategy adequate for prose became actively harmful for structured content |
| 2 | No structure-aware handling existed for fenced code blocks or ordered lists | Both were routinely split at arbitrary points |
| 3 | Retrieval was never tested specifically against code-containing or list-containing documents | The failure was discovered by frustrated engineers, not caught before rollout |

### The fix

**Extend structure-aware chunking to cover code blocks and ordered/unordered lists**, per §5.4 — not just
headings, since these elements are at least as intolerant of arbitrary splitting as headings are.

**Test retrieval specifically against structured content (code, lists, tables) before trusting a pipeline
for a new corpus type**, the same discipline M7-L04's worked example established for tables specifically.

**Re-evaluate chunking strategy whenever the corpus's content type changes materially** — a strategy tuned
for one kind of document (prose policies) is not automatically adequate for another (technical runbooks).

**The general rule.** **The right chunking strategy depends on what kind of content you're actually
chunking — a choice made once for one corpus does not automatically transfer to a structurally different
one, and code/lists/tables are where a prose-tuned default is most likely to fail sharply.**

---

## 7. Practical activity

**File:** [`labs/m7/l07_chunking_strategies.py`](../../labs/m7/l07_chunking_strategies.py)

**No API key, no network, no third-party dependencies.** Runs in well under a second.

```bash
source .venv/bin/activate
python labs/m7/l07_chunking_strategies.py
```

### 7.2 Expected output

`[EXECUTED]` — 2026-09-10, Python 3.10.11 (pure standard library).

```text
============================================================================
1. RECURSIVE SPLITTING: COARSE SEPARATORS FIRST, FINER ONLY IF NEEDED
============================================================================
  Document (274 characters, 3 paragraphs), fixed-size at 120 chars:

    Chunk 1: 'Remote work requires manager approval for up to three days per week.\n\nFully remote arrangements require VP approval and '
    Chunk 2: 'a signed agreement.\n\nExpense reports must be submitted within thirty days of purchase. Reimbursements over five hundred '
    Chunk 3: 'dollars require director approval.'

  Same document, recursively split (try paragraph breaks first, only
  fall back to sentence breaks for a piece still over 120 chars):

    Chunk 1: 'Remote work requires manager approval for up to three days per week.'
    Chunk 2: 'Fully remote arrangements require VP approval and a signed agreement.'
    Chunk 3: 'Expense reports must be submitted within thirty days of purchase'
    Chunk 4: 'Reimbursements over five hundred dollars require director approval.'

  Fixed-size cuts wherever the count lands, mid-paragraph or not.
  Recursive splitting tries the COARSEST, most meaningful boundary
  first (a paragraph break) and only breaks a paragraph into sentences
  if that paragraph alone is still too big -- producing chunks aligned
  to real content boundaries without needing any preserved structure
  metadata (M7-L06's heading-based approach needed the '#' markup;
  this works on the raw text's own punctuation and spacing alone).

============================================================================
2. SENTENCE SPLITTING -- AND A REAL, HONEST FAILURE CASE
============================================================================
  Clean text, no abbreviations: 'Remote work requires approval. Expense reports are due monthly. PTO accrues yearly.'
  Split into 3 sentences:
    'Remote work requires approval.'
    'Expense reports are due monthly.'
    'PTO accrues yearly.'

  Text WITH abbreviations: 'Contact Dr. Smith for approval. He reports to the U.S. division head.'
  Split into 3 'sentences':
    'Contact Dr.'
    'Smith for approval.'
    'He reports to the U.S. division head.'

  'Dr. Smith' and 'U.S. division' were each split at the abbreviation's
  period, producing fragments that are not real sentences at all. This
  is not a contrived edge case -- abbreviations, initials, and decimal
  numbers are common in real documents, and a purely punctuation-based
  sentence splitter has no way to distinguish 'end of sentence' from
  'abbreviation' without an explicit exception list or a smarter model.

============================================================================
3. SEMANTIC CHUNKING: FINDING TOPIC SHIFTS WITH NO STRUCTURAL MARKUP AT ALL
============================================================================
  Four sentences, NO headings, NO paragraph breaks, NO markup at all --
  just plain consecutive prose:

  [1] 'Remote work is available with manager approval.'
      -> similarity to next sentence: 1.000
  [2] 'The office supports a flexible remote work schedule.'
      -> similarity to next sentence: 0.000
  [3] 'Quarterly revenue grew five percent this year.'
      -> similarity to next sentence: 1.000
  [4] 'Earnings were strong and profit grew for the team.'

  Similarity drops below 0.5 between sentences [2] and [3] -- exactly where the topic shifts from remote work to quarterly revenue.

  Resulting semantic chunks:
    Chunk 1: ['Remote work is available with manager approval.', 'The office supports a flexible remote work schedule.']
    Chunk 2: ['Quarterly revenue grew five percent this year.', 'Earnings were strong and profit grew for the team.']

  Nobody told this splitter where one topic ends and the next begins --
  no heading, no blank line, not even a paragraph break (M7-L06's
  boundary-aware chunking needed exactly that kind of markup). Semantic
  chunking finds the boundary from the CONTENT itself, using the same
  pooling/cosine mechanism M6-L01 introduced, applied here to adjacent
  sentences instead of a query and a document.

============================================================================
4. STRUCTURE-AWARE: LISTS AND CODE BLOCKS, NOT JUST HEADINGS
============================================================================
  A document with a heading, a bullet list, and a fenced code block:

  Fixed-size (70 chars), blind to any of this structure:
    Chunk 1: '# Setup Instructions\nFollow these steps to configure remote access:\n- '
    Chunk 2: 'Install the VPN client\n- Enter your employee ID\n- Contact IT if the co'
    Chunk 3: 'nnection fails\n\nExample configuration:\n```\nserver: vpn.acme.example\npo'
    Chunk 4: 'rt: 443\n```\nOnce connected, remote work proceeds as normal.'

  Structure-aware (never splits inside a list or a code block):
    Chunk 1: '# Setup Instructions\nFollow these steps to configure remote access:\n- Install the VPN client\n- Enter your employee ID\n- Contact IT if the connection fails\nExample configuration:\n```\nserver: vpn.acme.example\nport: 443\n```'
    Chunk 2: 'Once connected, remote work proceeds as normal.'

  Code block kept fully intact in ONE chunk -- structure-aware: True, fixed-size: False
  Splitting a code block in the middle produces a fragment that is not
  valid, meaningful configuration on its own -- a much sharper failure
  than splitting prose mid-sentence, since code has no tolerance for
  being read 'mostly right'.

============================================================================
5. ALL FOUR STRATEGIES, SIDE BY SIDE, ON ONE DOCUMENT
============================================================================
  Chunk counts on this lesson's own documents, strategy by strategy:

  Strategy            Document                    Chunks produced
  Fixed-size          3-paragraph policy text     3
  Recursive           3-paragraph policy text     4
  Sentence            Clean 3-sentence text       3
  Semantic            4-sentence, 2-topic text    2
  Structure-aware     Heading+list+code doc       2

  No single count here is 'correct' in isolation -- each strategy is
  solving a different problem. Fixed-size is the cheapest and least
  aware. Recursive respects generic textual structure without needing
  metadata. Sentence splitting respects grammar (with a real caveat).
  Semantic splitting respects MEANING, even with zero markup. Structure-
  aware splitting respects explicit document structure, including
  elements (lists, code) a heading-only approach (M7-L06) would miss.

============================================================================
6. WHAT THIS LAB IS AND IS NOT
============================================================================
  REAL: every splitting function in this lab is genuinely executed on
  real text; the sentence-splitting abbreviation failure is a real,
  reproduced regex behavior, not asserted; the semantic-chunking
  similarity scores use M6-L01's exact pooling/cosine mechanism.

  ILLUSTRATIVE: the semantic-chunking threshold (0.5) and word vectors
  are hand-built for this lesson, not a trained embedding model's real
  output -- the MECHANISM (similarity drop signals topic shift) is real
  and used in production semantic chunkers; the specific numbers are
  a checkable illustration.

  NOT SHOWN: a production-grade sentence tokenizer that correctly
  handles abbreviations (typically using an explicit abbreviation list
  or a trained model); chunking cost/latency at real corpus scale; and
  combining multiple strategies in one pipeline (e.g. recursive PLUS
  structure-aware), left to the exercises.

Done.
```

### 7.3 Reading the result

**Section 2's abbreviation failure is more valuable reported honestly than avoided.** A lab that carefully
picked only abbreviation-free example text would teach a false sense of security about how robust simple
sentence splitting is.

**Section 3 is this lesson's clearest demonstration of a genuinely different mechanism**, not just a
different parameter. Every other strategy in this lesson (and in M7-L06) needs *something* — a count, a
punctuation mark, a heading — to find its boundary. Semantic chunking needs only the content's own meaning.

**Section 4's code-block result mattered enough to require finding the right chunk size to demonstrate
honestly** — an earlier version of this lab, at a different size, showed both strategies coincidentally
preserving the code block, which would have taught nothing. The measured, genuine split at 70 characters is
what makes the comparison meaningful.

---

## 8. Common mistakes and troubleshooting

1. **Assuming a single chunking strategy is universally best.** §5.5 — each strategy suits different
   document characteristics; the right choice depends on what you're actually chunking.
2. **Trusting punctuation-based sentence splitting on documents likely to contain abbreviations.** §5.2 —
   this is a real, common failure mode, not a rare edge case.
3. **Assuming semantic chunking requires document structure to work.** §5.3 — it specifically does not;
   this is its main advantage over structure-dependent approaches.
4. **Applying prose-tuned chunking (fixed-size or sentence-based) to documents containing code or
   structured lists without adjustment.** §5.4, §6 — code and lists tolerate arbitrary splitting far worse
   than prose does.
5. **Not testing retrieval against structured content (code, lists, tables) specifically when a corpus's
   content type changes.** §6 — a strategy adequate for one content type is not automatically adequate for
   another.
6. **Treating a chunking demonstration's parameters (chunk size, threshold) as arbitrary rather than
   checking whether they actually produce the intended effect.** §7.3 — verify a demonstration's numbers
   support its claimed narrative before trusting it.

| Symptom | Likely cause | Fix |
|---|---|---|
| Sentence-split chunks contain obviously broken fragments like "Contact Dr." | Punctuation-based splitting cannot distinguish abbreviations from sentence endings | Use an explicit abbreviation exception list or a trained sentence tokenizer (§5.2) |
| A retrieved code snippet or configuration is syntactically incomplete | Fixed-size or prose-tuned chunking split a code block arbitrarily | Extend structure-aware chunking to treat code blocks (and lists) as indivisible units (§5.4) |
| Chunking works well for one document type but poorly for another in the same corpus | Different content types (prose vs. code vs. lists) have different splitting requirements | Re-evaluate chunking strategy per content type; consider combining strategies (§5.5, §6) |
| A document with no headings or clear structure still needs topic-aware chunking | No structural markup exists for a boundary-aware approach to use | Use semantic chunking, which needs no explicit structure (§5.3) |

---

## 9. Security, privacy, reliability, cost

- **Reliability.** Match chunking strategy to content type — code and structured lists need
  structure-aware handling; unstructured prose with no markup may need semantic chunking instead (§5.4,
  §5.5).
- **Reliability.** Do not rely on punctuation-based sentence splitting without accounting for
  abbreviations, if your documents are likely to contain them (§5.2).
- **Reliability.** Test retrieval specifically against each distinct content type in your corpus (prose,
  code, lists, tables) rather than assuming one strategy generalizes (§6).
- **Cost.** Recursive and structure-aware splitting are computationally cheap (no embedding calls);
  semantic chunking requires computing similarity between units, a real but modest additional cost worth
  weighing against its unique benefit (§5.3).

---

## 10. Exercises

### Exercise 1 — Beginner (~20 min)

1. In one sentence, what does recursive splitting try before falling back to a finer separator?
2. Why did the sentence splitter break on "Dr. Smith"?
3. How does semantic chunking find a topic boundary without any headings or paragraph breaks?
4. Why is splitting a code block a sharper failure than splitting a sentence?
5. Name one document characteristic that would make you choose semantic chunking over structure-aware
   chunking.

### Exercise 2 — Intermediate (~40 min)

1. Run the lab. Confirm §7.1's recursive-split boundaries and §7.3's similarity scores on your own
   machine.
2. Extend §7.2's sentence splitter with an explicit abbreviation exception list (e.g. "Dr.", "U.S.", "Mr.")
   and confirm it no longer incorrectly splits the abbreviation example.
3. Construct your own 5-sentence, 2-topic document (no markup) and confirm semantic chunking finds the
   correct boundary, adjusting the threshold if needed.
4. Extend §7.4's structure-aware chunker to also treat a Markdown table (lines starting with `|`) as an
   indivisible unit, and test it on a document containing one.
5. Using §7.5's method, add a sixth document/strategy combination of your choice to the comparison table.

### Exercise 3 — Challenge (~50 min)

1. Implement a combined chunker that applies structure-aware splitting first (respecting headings, lists,
   code), then recursively splits any resulting piece still over a size limit.
2. Design and run an experiment measuring how the semantic-chunking threshold affects the number of
   detected topic boundaries on a longer, multi-topic synthetic document (similar to M6-L11's k-sensitivity
   method).
3. Research (conceptually) how a real semantic chunker would use actual sentence embeddings (rather than
   hand-built word vectors) and what changes about the similarity computation at that scale.
4. Implement a chunker that respects Markdown tables as well as code blocks and lists, and test it on a
   document combining all three structural elements.
5. Using this lesson's §6 worked example as a model, design a chunking-strategy decision test: given a
   sample document, determine programmatically which of this lesson's five strategies would be most
   appropriate, and justify the logic.

---

## 11. Quiz

*(Answers: [`answer-keys/module-07-answers.md`](../../answer-keys/module-07-answers.md#m7-l07).)*

**Q1.** Per §7.1, what does recursive splitting try first, before falling back to a finer separator?

- A. The finest possible separator (individual characters) first.
- B. A random separator chosen without regard to text structure.
- C. The coarsest, most meaningful separator (e.g. a paragraph break), only recursing into a finer one (like sentence breaks) for a piece still too large.
- D. Whatever separator produces the smallest possible number of chunks.

**Q2.** Per §7.1, what advantage does recursive splitting have over M7-L06's boundary-aware heading-based
chunking?

- A. It works on the raw text's own punctuation and spacing alone, without needing any explicitly preserved structure metadata like heading markup.
- B. It requires a trained machine learning model to function at all.
- C. It only works on documents written in Markdown format.
- D. It eliminates the need for any chunk size limit whatsoever.

**Q3.** Per §7.2, why did the sentence splitter incorrectly split "Contact Dr. Smith for approval." into
two fragments?

- A. The document was corrupted before splitting began.
- B. Python's regular expression engine has a known bug affecting titles like "Dr."
- C. The sentence was deliberately mistyped in the lab's source code.
- D. The splitter uses punctuation alone to detect sentence boundaries, and has no way to distinguish an abbreviation's period from an actual end-of-sentence period.

**Q4.** Per §7.2, is the abbreviation-splitting failure a rare edge case or a common real-world issue?

- A. It is a purely theoretical concern that never occurs in real documents.
- B. A common, real-world issue, since abbreviations, initials, and decimal numbers appear routinely in real documents.
- C. It only affects documents written entirely in uppercase letters.
- D. It was fixed automatically by a later version of the regex library.

**Q5.** Per §7.3, how did semantic chunking find the topic boundary between remote-work sentences and
revenue sentences?

- A. By counting the total number of words in each sentence.
- B. By checking whether each sentence contains a heading marker.
- C. By computing similarity between consecutive sentences (using pooled word vectors) and detecting a drop below a threshold, with no explicit markup at all.
- D. By measuring the character length of each sentence.

**Q6.** Per §7.3, what is the key advantage semantic chunking has over M7-L06's boundary-aware approach?

- A. It finds topic boundaries from the content's meaning itself, even in text with zero structural markup (no headings, no paragraph breaks).
- B. It requires exactly the same heading markup M7-L06's approach needed.
- C. It only works on documents shorter than four sentences.
- D. It eliminates the need for computing any similarity at all.

**Q7.** Per §7.4, why is splitting a code block in the middle a sharper failure than splitting prose
mid-sentence?

- A. Code blocks are always shorter than prose paragraphs.
- B. Code cannot be represented as plain text under any circumstances.
- C. Splitting code is technically impossible in any programming language.
- D. Code has no tolerance for being read "mostly right" — a fragment of a configuration file is not valid or meaningful on its own, unlike a slightly-awkward prose fragment.

**Q8.** Per §7.4's measured result, what happened to the code block under fixed-size (70-character)
chunking versus structure-aware chunking?

- A. Both approaches split the code block identically.
- B. Fixed-size chunking split the code block across two chunks; structure-aware chunking kept it fully intact in one chunk.
- C. Structure-aware chunking split the code block, while fixed-size kept it intact.
- D. Neither approach was able to process the code block at all.

**Q9.** Per §7.5, what is the general lesson from comparing all the chunking strategies side by side?

- A. Fixed-size chunking is always the best choice regardless of document type.
- B. Every chunking strategy always produces exactly the same number of chunks.
- C. No single chunk count or strategy is "correct" in isolation — each strategy is solving a different problem, suited to different document characteristics.
- D. Semantic chunking should always replace every other chunking strategy in every system.

**Q10.** Per §7.6, what is explicitly NOT demonstrated in this lab regarding sentence splitting?

- A. A production-grade sentence tokenizer that correctly handles abbreviations, typically using an explicit abbreviation list or a trained model.
- B. Recursive splitting, which this lesson also does not demonstrate.
- C. Fixed-size chunking, which this lesson also does not demonstrate.
- D. Structure-aware chunking, which this lesson also does not demonstrate.

**Q11.** Per §7.6, what does this lesson state about the semantic-chunking threshold and word vectors
used?

- A. They are a verified, trained embedding model's exact real-world output.
- B. They are randomly generated and carry no meaningful structure at all.
- C. They are identical to the vectors used in M6-L03's BM25 implementation.
- D. They are hand-built and illustrative, not a trained embedding model's real output, though the underlying mechanism (similarity drop signals topic shift) is real and used in production.

**Q12.** What is the overarching relationship between this lesson (M7-L07) and M7-L06?

- A. This lesson replaces every trade-off M7-L06 established with a single new rule.
- B. M7-L06 established the underlying trade-offs (size, overlap, boundaries) that this lesson's specific algorithms are each designed to navigate.
- C. M7-L06 and this lesson cover entirely unrelated topics with no connection.
- D. This lesson proves that M7-L06's trade-offs do not actually matter in practice.

**Q13.** *(Written, rubric-graded.)* In under 150 words: your corpus contains a mix of prose policy
documents and technical runbooks with embedded code and ordered command lists. Based on this lesson, would
you use one chunking strategy for the whole corpus, or different strategies for different content types?
Justify your answer.

---

## 12. Revision notes

- **Recursive splitting tries the coarsest separator first, falling back to finer ones only for pieces
  still too large** — producing boundary-aligned chunks from raw text alone, no preserved structure
  metadata required.
- **Punctuation-based sentence splitting fails on abbreviations** — measured directly: "Contact Dr. Smith"
  was incorrectly split at the abbreviation's period, a common real-world failure, not a rare edge case.
- **Semantic chunking finds topic boundaries from content meaning alone, with zero structural markup** —
  measured directly: similarity between consecutive sentences dropped from 1.000 to 0.000 exactly at a
  genuine topic shift, with no headings or paragraph breaks present at all.
- **Structure-aware chunking should extend beyond headings to lists and code blocks** — splitting code is a
  categorically sharper failure than splitting prose, since a code fragment has no tolerance for being
  "mostly right."
- **No single chunking strategy is universally correct** — each is suited to different document
  characteristics (generic text structure, grammar, meaning, or explicit formatting), and the right choice
  depends on what is actually being chunked.
- **A chunking strategy adequate for one content type in a corpus is not automatically adequate for
  another** — a corpus mixing prose and code, for instance, may need different treatment for each.

---

## 13. Completion checklist

- [ ] I can implement recursive splitting and explain why it tries coarse separators first.
- [ ] I can implement sentence splitting and explain its real limitation with abbreviations.
- [ ] I can implement semantic chunking and explain how it works with no structural markup at all.
- [ ] I can extend structure-aware chunking to cover lists and code blocks, not just headings.
- [ ] I can select an appropriate chunking strategy (or combination) for a given document's
      characteristics.
- [ ] I test retrieval against each distinct content type in a corpus rather than assuming one strategy
      generalizes.
- [ ] I scored 10/13 on the quiz.

---

## 14. References

- LangChain documentation, *Recursively split by character*. <https://python.langchain.com/docs/how_to/recursive_text_splitter/> `[UNVERIFIED]`
- Greene, D. et al., *Semantic chunking* survey material (general concept reference). `[UNVERIFIED]`

---

## 15. Next lesson

→ M7-L08 — Metadata, Identifiers, Provenance and Versioning

You now have a full toolkit for turning documents into retrieval-ready chunks. Next: what to attach to
each chunk beyond its text — source, timestamps, version, and access information — so a retrieved chunk
carries the context needed to trust, cite, and govern it correctly.
