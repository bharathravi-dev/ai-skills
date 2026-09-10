# M7-L04 — Hard Formats: PDFs, HTML, Tables, Scans and OCR

| | |
|---|---|
| **Lesson ID** | M7-L04 |
| **Difficulty** | 3 (Advanced) |
| **Estimated study time** | 2.25 hours |
| **Prerequisites** | [M7-L03](M7-L03-ingestion-document-parsing.md) |

---

## 1. Learning objectives

1. **Demonstrate** that PDF text extraction returns headers and footers with the same status as body
   text, and implement a heuristic to remove them.
2. **Demonstrate** that flattening a table to plain text destroys row/column structure, and explain the
   concrete downstream risk this creates for chunking.
3. **Implement** a boilerplate-aware HTML content extractor that separates real content from navigation,
   footers, and other non-content elements.
4. **Explain**, with a real measured example, why a scanned document has no text layer at all, and what
   gap OCR exists to close.
5. **Evaluate** a specific claimed extraction failure mode against your own tools, rather than assuming it
   applies universally.

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **Text layer** | The actual character data embedded in a PDF (or absent from a scanned image), as opposed to its visual appearance. |
| **Boilerplate** | Repeated, non-content material (navigation, headers, footers, legal text) that appears identically or near-identically across many pages or documents. |
| **Table flattening** | The loss of row/column structure that occurs when a table is extracted as a linear sequence of text. |
| **OCR (Optical Character Recognition)** | The process of reading text from an image's pixels and producing actual character data — required when a document has no text layer. |
| **Column-order scrambling** | A historically well-documented PDF extraction failure where multi-column text is read out of its intended order — this lesson tests, rather than assumes, whether it reproduces with a specific modern tool. |

---

## 3. Plain-language explanation

### 3.1 M7-L03 ingested cooperative formats; this lesson ingests the rest

Plain text, Markdown, CSV, and JSON all give you their content directly. PDFs, HTML pages, tables, and
scanned images each hide, scramble, or entirely lack the information a RAG pipeline needs — and each in a
genuinely different way, which is why this lesson treats them one at a time rather than with one fix.

### 3.2 A PDF page doesn't know what a header is

§7.1 generates a real, multi-page PDF and extracts its text with a real library. The output includes the
running header and footer on every single page, indistinguishable from body content, because nothing in a
PDF's text layer marks a line as "repeated boilerplate" versus "the actual content."

### 3.3 A table, once extracted, is just a list of words in a row

§7.2 is this lesson's sharpest demonstration: a real 3x3 table, extracted, becomes a flat sequence with
every trace of which value belonged to which row and column gone. The lesson doesn't stop there — it shows
exactly how this becomes a real retrieval failure once the flattened text gets cut by an ordinary chunker.

### 3.4 HTML pages are mostly not the content you want

§7.3 contrasts stripping every tag indiscriminately against explicitly skipping the elements that are
almost always boilerplate (`<nav>`, `<header>`, `<footer>`, `<aside>`, `<script>`, `<style>`) — a small,
real, stdlib-only piece of code with an outsized effect on what ends up in your corpus.

### 3.5 A scanned page has no text in it at all

§7.4 makes something concrete that's easy to state abstractly: a scanned document isn't hard to extract
text from — there is no text there to extract. It's a picture of words. OCR is the specific technique that
turns pixels back into characters, and this lesson shows the empty result it exists to fix, without
running OCR itself.

### 3.6 Not every well-known problem reproduces the same way twice

§7.5 tests, rather than assumes, whether a specific historically-documented PDF failure (scrambled column
order) still occurs with a current library version — and reports the honest result either way.

---

## 4. Analogy

**Photocopying a filing cabinet's contents versus actually reading them.** A PDF's header/footer problem is
like a photocopier that dutifully reproduces the letterhead and page-number stamp on every single page,
because it has no idea those are different from the letter's actual content. A flattened table is like
photocopying a spreadsheet and cutting it into single-word strips — you still have every word that was on
the page, but you've thrown away which row and column each one came from, and no amount of staring at the
strips in order fully recovers it once they're separated. A scanned document is not a filing cabinet at
all — it's a photograph of one: you can see it, but nothing in the photograph is actually text you can
select, search, or copy, until something (OCR) reads the picture and writes down what it says.

### Where the analogy breaks

- **A human glancing at photocopied strips can often still guess the original table from context.** §7.2's
  point is sharper than this: once a chunk boundary genuinely separates a label from its value, no context
  survives in that specific chunk to guess from at all.
- **Photocopiers don't improve version to version in ways that matter here.** §7.5's honest negative result
  — testing the column-order failure and not finding it — has no real analogue; the point there is
  specifically that software tooling does change, and assumptions need re-testing.

---

## 5. Detailed technical explanation

### 5.1 Headers and footers, measured

`[REAL]` §7.1 generated a genuine 3-page PDF (via `reportlab`) with a repeated header and a footer
containing a page number, then extracted its text with `pypdf`. The header appeared 3 times, verbatim. A
simple exact-line-match heuristic (a line appearing on ≥60% of pages is boilerplate) correctly identified
and removed the header — **and correctly failed to catch the footer**, because each footer line contained
a different page number ("Page 1 of 3" vs. "Page 2 of 3"), so no two footer lines were byte-for-byte
identical despite the obvious repeated *pattern*. **This is a genuine, useful finding, not an oversight**:
catching this class of boilerplate requires a pattern-based rule (e.g. a regex matching "Page \d+ of \d+"),
not exact-string matching — real boilerplate detection is harder than "find repeated lines."

### 5.2 Table flattening, and the chunk-boundary failure it causes

`[REAL, measured]` §7.2 drew a real 3-row, 3-column table at genuine (x, y) grid coordinates and extracted
it. The result: `Tier, Years of Service, PTO Days, Junior, 0-2, 15, Mid, 3-5, 20, Senior, 6+, 25` — every
row/column association gone, replaced by a flat, header-then-cells sequence. **The lesson doesn't stop at
"structure is lost"**: simulating a naive, fixed-size chunker (M7-L06) cutting this text after line 7 put
`Mid` in one chunk and its corresponding PTO value, `20`, in the next chunk with no label to anchor it.
**A retrieval system that returns only the second chunk for a question about the Mid tier has lost
information that existed in the original document but was severed by ingestion, not by retrieval.**

### 5.3 HTML: what to keep, and what to explicitly skip

`[REAL]` §7.3 compared two real, executed extractors on the same HTML page. A naive extractor (collect all
text, regardless of tag) kept navigation links, a footer's legal text, and an unrelated "related articles"
aside, all mixed with the genuine article content in one undifferentiated string. A second extractor,
explicitly skipping `nav`, `header`, `footer`, `aside`, `script`, and `style` tags, produced only the
article's title and body. **The difference is not subtle** — roughly half the naive extraction's text was
never part of the article at all.

### 5.4 Scanned documents have no text layer, measured directly

`[REAL, measured]` §7.4 built a genuine PDF page containing an embedded raster image (created with PIL) of
the sentence "Employees accrue 15 days of PTO per year," drawn as pixels with no PDF text objects on the
page at all. `extract_text()` returned an empty string, length 0. **This is not a weak extractor failing —
there is no text data on that page to extract.** `[NOT EXECUTED]` OCR is the technique that reads the
pixels and produces actual character data; no real OCR engine (e.g. Tesseract) is available in this
environment, so this lesson demonstrates the precise gap OCR closes without running it.

### 5.5 An honest test of a well-known failure mode

`[REAL, measured, honest negative result]` §7.5 also directly tested the classic "multi-column PDF text
gets scrambled" problem, using a simple two-column layout. **It did not reproduce** with this lab's
`pypdf` version — the library's layout heuristics handled the simple case correctly. This is reported as a
genuine finding, not omitted: it does **not** mean column-order problems are solved everywhere — denser
layouts, older tools, and more irregular real-world page designs remain documented risks. `[UNVERIFIED —
test your own specific documents and library version rather than assuming either outcome.]`

### 5.6 Assumptions and limitations

- This lesson requires `pypdf`, `reportlab`, and `Pillow` — the first lab in this course needing
  third-party dependencies beyond `numpy`/`scikit-learn`, because generating and parsing real PDFs and
  images genuinely requires them.
- §5.1's boilerplate heuristic and §5.3's HTML extractor are simple, illustrative implementations, not
  production-grade solutions — real systems typically use more robust, configurable tooling.
- §5.5's result is specific to one library version tested on simple layouts; it is not a general claim
  about all PDF extraction tools or all column layouts.
- This lesson does not cover cleaning or deduplicating extracted text once ingested (M7-L05), nor
  automatic table-structure reconstruction, which remains a genuinely hard, unsolved-in-general problem
  only briefly touched on here.

---

## 6. Worked example — the compliance search that missed the actual clause

**The system.** A legal team's document search tool ingests PDF contracts, including their tables of
payment terms and deadlines, using a standard PDF-to-text extraction step with naive fixed-size chunking.

**What went wrong.** A search for "late payment penalty for the Enterprise tier" returned no relevant
result, even though the correct contract contained exactly this information — in a table where "Enterprise"
was in one row and its penalty terms were several cells away, and a chunk boundary had split the table
between the tier name and its associated values, exactly as §7.2 demonstrated directly.

**Why standard debugging didn't find it quickly.** The extracted text, read in full, "contained" all the
right words — someone reading the raw extraction manually could reconstruct the answer by counting columns,
the same way a human can read photocopied strips. The chunked, retrieved fragment alone could not, and this
distinction wasn't obvious until someone specifically inspected which chunk retrieval had actually returned
for that query (M7-L01 §6's own debugging discipline, applied here).

**Three defects:**

| # | Defect | Consequence |
|---|---|---|
| 1 | Tables were extracted as flat text with no structure preserved | Row/column associations existed only implicitly, recoverable by a human but not guaranteed to survive chunking |
| 2 | Chunking was applied without any table-aware boundary logic | A table could be (and was) split at an arbitrary point, severing a label from its value |
| 3 | No one had tested retrieval specifically against table-derived content before launch | The failure mode was discovered by a user, not caught in testing |

### The fix

**Detect and handle tables specially during ingestion** — at minimum, keep a table's rows intact as single
units rather than allowing generic chunking to cut through them (M7-L06/M7-L07's chunking strategies
should be table-aware where tables are detected).

**Test retrieval specifically against table-derived content before launch**, not only against prose —
per §5.2, this is a distinct, predictable failure mode worth checking for deliberately.

**When a RAG answer is wrong on a document known to contain tables, check whether a table was involved and
whether it was split across a chunk boundary** — this is a specific, checkable instance of M7-L01 §6's
general "inspect what was retrieved" debugging discipline.

**The general rule.** **Table flattening is not a rare edge case — any real corpus containing structured
data (pricing tables, eligibility matrices, schedules) will hit this exact failure mode unless table
structure is explicitly preserved or handled during ingestion and chunking.**

---

## 7. Practical activity

**File:** [`labs/m7/l04_hard_formats.py`](../../labs/m7/l04_hard_formats.py)

**Requires `pypdf`, `reportlab`, and `Pillow`** — install them in your lab environment first. No API key,
no network beyond the one-time install.

```bash
source .venv/bin/activate
pip install pypdf reportlab pillow
python labs/m7/l04_hard_formats.py
```

### 7.2 Expected output

`[EXECUTED]` — 2026-09-10, Python 3.10.11, pypdf 6.18.0, reportlab 5.0.1, Pillow 12.3.0.

```text
============================================================================
1. PDF HEADERS AND FOOTERS REPEAT ON EVERY PAGE
============================================================================
  A real 3-page PDF, generated and text-extracted (pypdf 6.18.0):

  'ACME CORP -- INTERNAL POLICY HANDBOOK\nRemote work requires manager approval for up to three days per week.\nPage 1 of 3 -- Confidential -- Do not distribute\n\nACME CORP -- INTERNAL POLICY HANDBOOK\nExpense reports must be submitted within thirty days of purchase.\nPage 2 of 3 -- Confidential -- Do not distribute\n\nACME CORP -- INTERNAL POLICY HANDBOOK\nReferral bonuses are paid after ninety days of the new hire.\nPage 3 of 3 -- Confidential -- Do not distribute\n'

  Header line repeats: 3 times
  Footer pattern repeats: 3 times

  Lines identified as boilerplate (appear on >= 60% of pages): {'ACME CORP -- INTERNAL POLICY HANDBOOK'}
  Cleaned text: 'Remote work requires manager approval for up to three days per week.\nPage 1 of 3 -- Confidential -- Do not distribute\nExpense reports must be submitted within thirty days of purchase.\nPage 2 of 3 -- Confidential -- Do not distribute\nReferral bonuses are paid after ninety days of the new hire.\nPage 3 of 3 -- Confidential -- Do not distribute'

  Notice the FOOTER is still there -- this simple, exact-match heuristic
  only caught the header. Each footer line is technically DIFFERENT text
  ('Page 1 of 3...' vs 'Page 2 of 3...'), because the page number is
  embedded in it, so exact-string repetition never matches across pages
  even though the PATTERN clearly repeats. Catching this needs a fuzzier
  rule (e.g. a regex like 'Page \d+ of \d+ -- Confidential') -- real
  boilerplate detection is genuinely harder than 'find repeated lines',
  and this gap is left uncorrected here specifically to show that.

  Nothing about a PDF FLAGS a header or footer as such -- extraction
  returns every line of text on the page with equal status. Without
  explicit boilerplate removal, a header repeated on every page of a
  50-page document becomes 50 near-duplicate copies of the same six
  words polluting the corpus, diluting real content in both search
  results and any per-document token budget.

============================================================================
2. TABLES LOSE ALL ROW/COLUMN STRUCTURE WHEN FLATTENED TO TEXT
============================================================================
  A real 3-row, 3-column table, drawn at genuine (x, y) grid positions, then extracted:

  'Tier\nYears of Service\nPTO Days\nJunior\n0-2\n15\nMid\n3-5\n20\nSenior\n6+\n25\n'

  Every row/column boundary is gone. The extracted text is a FLAT
  sequence: headers, then every cell, top-to-bottom, left-to-right --
  with nothing marking which value belongs to which row. Reading it
  in order happens to look sensible ONLY because a human reader can
  count columns and re-pair values from memory.

  Simulating a naive, fixed-size chunker (M7-L06) cutting after line 7:
    Chunk A: ['Tier', 'Years of Service', 'PTO Days', 'Junior', '0-2', '15', 'Mid']
    Chunk B: ['3-5', '20', 'Senior', '6+', '25']

  Chunk B alone contains ['3-5', '20', 'Senior', '6+', '25'] -- '20' with no 'Mid' anywhere in
  the same chunk to pair it with. A query asking specifically about the
  Mid tier's PTO days, if it retrieves chunk B alone, has genuinely lost
  the information needed to answer correctly -- not because retrieval
  failed, but because ingestion flattened a 2D structure into a 1D
  sequence that an arbitrary cut can sever at exactly the wrong point.

============================================================================
3. HTML: BOILERPLATE VS REAL CONTENT
============================================================================
  Naive 'just strip the tags' extraction keeps EVERYTHING, in document
  order:
    'Support trackVisit(); Home | Products | Pricing | Contact Acme Support Center Return Policy Items may be returned within thirty days of delivery for a full refund. Original packaging is required for electronics returns. Related articles: Shipping Times, Warranty Information (c) 2026 Acme Corp | Privacy Policy | Terms of Service'

  Boilerplate-aware extraction (skipping nav/header/footer/aside/
  script/style):
    'Support Return Policy Items may be returned within thirty days of delivery for a full refund. Original packaging is required for electronics returns.'

  The nav bar, footer legal text, and 'related articles' aside never
  appear -- only the article's own title and body. Chunking and
  embedding THIS text, rather than the whole page, means retrieval
  scores reflect the actual policy content, not diluted by boilerplate
  every other page on the same site repeats verbatim.

============================================================================
4. SCANNED DOCUMENTS: NO TEXT LAYER AT ALL
============================================================================
  A real PDF page containing a genuine embedded RASTER IMAGE of text
  (pixels, drawn via PIL -- exactly what a scanner or a photographed
  document produces), with no PDF text objects on the page at all.

  extract_text() result: ''  (length: 0)

  This is not a bug or a weak extractor -- there is genuinely no text
  to extract. The page contains a picture of words, not the words
  themselves as data. `[NOT EXECUTED]` Optical Character Recognition
  (OCR) is the process that reads the PIXELS and produces actual text
  from them -- a real OCR engine (e.g. Tesseract) is not available in
  this environment, so this lab demonstrates the exact gap OCR exists
  to close, without running OCR itself.

============================================================================
5. WHAT THIS LAB IS AND IS NOT
============================================================================
  REAL: every PDF in this lab is genuinely generated (via reportlab)
  and genuinely text-extracted (via pypdf) -- the header/footer
  repetition, the total loss of table structure, and the scanned
  page's completely empty extraction are all measured, not scripted.
  The HTML boilerplate extractor is real, stdlib-only code.

  AN HONEST NEGATIVE RESULT: this lesson also tested the classic
  'multi-column text gets scrambled' failure mode directly, using a
  simple two-column layout. It did NOT reproduce with this lab's
  pypdf version -- modern extraction libraries have gotten materially
  better at simple column layouts than commonly assumed. This is a
  real, measured finding, not an oversight: it does not mean column-
  order problems never happen -- denser layouts, older tools, and
  more irregular page designs remain documented, real risks.
  `[UNVERIFIED -- test your own specific documents and extraction
  library version before assuming either outcome.]`

  NOT SHOWN: running a real OCR engine on the scanned page; detecting
  and reconstructing table structure automatically (a genuinely hard
  problem in general, briefly touched on but not solved here); and
  cleaning/deduplicating extracted text once ingested, which is
  M7-L05's topic.

Done.
```

### 7.3 Reading the result

**Section 1's footer finding is more valuable than a clean success would have been.** A heuristic that
caught both header and footer would have taught only "repeated lines are boilerplate." Catching the header
but missing the footer teaches the sharper, more useful lesson: *why* it missed it, and what a more capable
rule would need.

**Section 2 is this lesson's most important result.** It doesn't stop at "structure is lost" — it traces
that loss forward into an actual, concrete retrieval failure, which is the difference between an
interesting fact and an operationally useful one.

**Section 5's honest negative result is a deliberate methodological example**, not a throwaway note. It
would have been easy to simply assert "PDFs scramble column order" as received wisdom; testing it directly
and reporting what actually happened models exactly the discipline this whole course has tried to practice.

---

## 8. Common mistakes and troubleshooting

1. **Assuming PDF extraction distinguishes body text from headers/footers automatically.** §5.1 — it does
   not; explicit boilerplate detection is required, and even then may need pattern-based, not just
   exact-match, rules.
2. **Chunking table-derived text with the same fixed-size logic used for prose.** §5.2, §6 — this can
   sever a label from its value, producing chunks that are individually unanswerable for questions the
   original document could answer.
3. **Extracting HTML by stripping all tags without regard to which ones mark boilerplate.** §5.3 — this
   pollutes a corpus with navigation and footer text that should never be search-relevant content.
4. **Assuming a scanned document's extraction failure is a bug to debug.** §5.4 — there is no text layer
   to extract; the fix is OCR, not a "better" text-extraction library.
5. **Treating a well-known extraction failure mode as universally true without testing it against your own
   tools and documents.** §5.5 — behavior is version- and layout-dependent; verify before assuming.
6. **Not testing retrieval specifically against table-derived or scanned content before launch.** §6 — these
   are predictable, specific failure modes worth checking deliberately, not just discovering in production.

| Symptom | Likely cause | Fix |
|---|---|---|
| The same header/footer text appears repeatedly throughout a corpus derived from a multi-page document | PDF extraction returning boilerplate with the same status as body text | Detect and strip repeated lines/patterns per document (§5.1) |
| A RAG answer about a specific row of a table is wrong or missing, even though the table was ingested | Table structure was flattened and a chunk boundary split a label from its value | Keep table rows intact during chunking, or preserve structure explicitly (§5.2, §6) |
| Search results for site content are polluted by navigation links or footer legal text | HTML extraction did not distinguish boilerplate elements from real content | Use a boilerplate-aware extractor that skips nav/header/footer/aside/script/style (§5.3) |
| A document ingests as completely empty | The document is a scan or photograph with no text layer | Apply OCR before ingestion; this is expected behavior for scanned content, not a bug (§5.4) |

---

## 9. Security, privacy, reliability, cost

- **Reliability.** Explicitly detect and remove boilerplate (headers, footers, navigation) during
  ingestion — it is never automatically distinguished from real content by the source format itself (§5.1,
  §5.3).
- **Reliability.** Treat tables as a distinct, table-aware chunking concern — a table split across an
  ordinary chunk boundary produces individually unanswerable fragments (§5.2, §6).
- **Reliability.** Test retrieval specifically against table-derived and scanned/OCR'd content before
  launch — these are predictable, checkable failure modes, not rare edge cases (§6).
- **Cost.** Re-test known extraction failure modes against your own specific tools and document set rather
  than assuming a historically documented problem does or doesn't apply — behavior changes across library
  versions (§5.5).

---

## 10. Exercises

### Exercise 1 — Beginner (~20 min)

1. In one sentence, why did the header appear on every extracted page in §7.1?
2. Why did the boilerplate-removal heuristic catch the header but not the footer?
3. What specifically does a table lose when it is flattened to plain text?
4. Why did the scanned page's extraction return an empty string, and what fixes this?
5. What did this lesson find when it tested the "columns get scrambled" failure mode directly?

### Exercise 2 — Intermediate (~40 min)

1. Run the lab (after installing `pypdf`, `reportlab`, and `Pillow`). Confirm §7.1's repetition counts and
   §7.4's empty extraction result on your own machine.
2. Extend §7.1's boilerplate heuristic with a regex-based rule that also catches the page-numbered footer,
   and confirm it now removes both.
3. Design and generate a 4-column table (instead of 3) and confirm the same flattening and chunk-boundary
   failure occurs.
4. Extend §7.3's HTML extractor to also skip a `<div class="advertisement">` element, and test it on a
   page containing one.
5. Using §7.2's method, construct a case where a fixed-size chunker's boundary happens to fall exactly at
   a table's row boundary (not mid-row) and confirm whether the failure still occurs.

### Exercise 3 — Challenge (~50 min)

1. Implement a simple table detector (e.g. based on consistent x-coordinate alignment across multiple
   lines) that identifies table-like regions in extracted text and keeps their rows intact during
   chunking.
2. Test §7.5's column-order experiment with a denser, more realistic multi-column layout (e.g. wrapped
   paragraphs of uneven length per column) and report whether it reproduces this time.
3. Research (conceptually) how a real OCR engine like Tesseract works at a high level, and what kinds of
   scanned-document quality issues (skew, low resolution, handwriting) affect its accuracy.
4. Design an ingestion pipeline test suite covering this lesson's four hard-format failure modes
   (boilerplate, table flattening, HTML noise, no text layer), specifying what each test should assert.
5. Write a short technical note (under 300 words) for a team about to ingest a corpus of PDF contracts
   containing pricing tables, based on this lesson's §6 worked example, recommending specific safeguards.

---

## 11. Quiz

*(Answers: [`answer-keys/module-07-answers.md`](../../answer-keys/module-07-answers.md#m7-l04).)*

**Q1.** Per §7.1, why did the header "ACME CORP -- INTERNAL POLICY HANDBOOK" appear 3 times in the
extracted text of a 3-page PDF?

- A. The PDF file was accidentally saved three separate times.
- B. PDF text extraction returns every line of text found on every page with equal status; nothing marks a line as a repeated header versus real body content.
- C. pypdf has a known bug that triples every line of text.
- D. The header was manually typed three times by the document's author.

**Q2.** Per §7.1, why did the simple exact-match boilerplate-detection heuristic catch the header but NOT
the footer?

- A. The footer used a different font than the header.
- B. The footer was positioned outside the visible page area.
- C. The extraction heuristic only checks the first and last page of a document.
- D. Each footer line contained a different page number ("Page 1 of 3" vs "Page 2 of 3"), so the lines were not byte-for-byte identical across pages even though the pattern repeated.

**Q3.** Per §7.2, what specifically was lost when the 3x3 table was extracted to flat text?

- A. All row/column structure — the extracted text is a flat sequence of values with nothing marking which value belongs to which row.
- B. The numeric values in the table, which were silently dropped entirely.
- C. Only the table's header row, while every data row extracted correctly.
- D. Nothing was lost; the table extracted with its structure fully intact.

**Q4.** Per §7.2's chunking simulation, why did Chunk B alone become unable to correctly answer a question
about the "Mid" tier's PTO days?

- A. Chunk B was empty and contained no text at all.
- B. The chunker crashed when it reached the middle of the table.
- C. The value "20" ended up in Chunk B with no "Mid" label anywhere in the same chunk, because the arbitrary cut point fell in the middle of the flattened table.
- D. Chunk B contained the entire table, unmodified.

**Q5.** Per §7.3, what does the "naive" HTML extraction baseline demonstrate?

- A. That HTML cannot be parsed without a third-party library under any circumstances.
- B. Stripping tags without regard to which ones mark navigation/boilerplate keeps everything — real article text mixed indiscriminately with nav bar, footer legal text, and unrelated asides.
- C. That naive extraction always produces shorter text than boilerplate-aware extraction.
- D. That HTML pages never contain any boilerplate content at all.

**Q6.** Per §7.3, which HTML elements did the boilerplate-aware extractor explicitly skip?

- A. Only `<script>` and `<style>`.
- B. `<article>`, `<h1>`, and `<p>` exclusively.
- C. Every tag present anywhere in the document.
- D. `<nav>`, `<header>`, `<footer>`, `<aside>`, `<script>`, and `<style>`.

**Q7.** Per §7.4, why did `extract_text()` return an empty string for the "scanned" PDF page?

- A. The page contained a raster image of text (pixels) with no PDF text objects at all — there was genuinely no text data to extract, not a failure of the extraction library.
- B. The PDF file was corrupted during creation.
- C. pypdf does not support reading any image-containing PDF.
- D. The image was too large for the extraction library to process.

**Q8.** Per §7.4, what is OCR's role relative to this lab's finding?

- A. OCR replaces the need for any text extraction library entirely, even for text-layer PDFs.
- B. OCR is only relevant for HTML documents, not PDFs or images.
- C. OCR reads the pixels of an image and produces actual extractable text from them — exactly the gap a page with no text layer at all has.
- D. OCR guarantees perfect accuracy on any scanned document regardless of quality.

**Q9.** Per §7.5, what did this lesson find when it directly tested the classic "multi-column text gets
scrambled" failure mode with a simple two-column layout?

- A. It reproduced exactly as expected, confirming the classic failure mode.
- B. It did not reproduce with this lab's specific pypdf version — an honest, measured negative result, not proof the problem never occurs elsewhere.
- C. The test could not be run at all due to a missing dependency.
- D. The column text was scrambled into a completely different, unrelated order.

**Q10.** Per §7.5's honest reporting, what should a reader conclude from the column-order test not
reproducing?

- A. That column-order problems have been completely and permanently solved in all PDF tools.
- B. That this lesson's finding applies to every possible PDF layout without exception.
- C. That table extraction problems are also solved by the same fix.
- D. Modern tools may handle some simple cases better than assumed, but this does not guarantee correctness on denser layouts, older tools, or more irregular real documents — worth testing on your own documents specifically.

**Q11.** Which topic does this lesson explicitly leave to M7-L05?

- A. Cleaning and deduplicating extracted text once ingested.
- B. Assigning content-hash-based document identity.
- C. Splitting documents into retrieval-sized chunks.
- D. Computing retrieval evaluation metrics.

**Q12.** What is the general lesson this lab demonstrates about "hard" document formats?

- A. All hard document formats can be solved by a single universal extraction fix.
- B. Hard formats are rare enough in practice that they can safely be ignored.
- C. Different hard formats (PDFs, tables, HTML, scans) each lose or obscure different kinds of information during extraction, and each requires its own explicit handling rather than a single universal fix.
- D. Only scanned documents present any real extraction challenge; all other formats are fully reliable.

**Q13.** *(Written, rubric-graded.)* In under 150 words: your team is about to ingest a large batch of PDF
contracts, some containing pricing tables. Based on this lesson, what would you specifically test for
before trusting the ingested result, and why?

---

## 12. Revision notes

- **PDF extraction returns headers, footers, and body text with equal status** — boilerplate must be
  explicitly detected and removed, and exact-match heuristics can miss patterns that vary slightly (e.g. a
  footer's page number) even when the underlying pattern clearly repeats.
- **Flattening a table to plain text destroys row/column structure**, and this becomes a concrete retrieval
  failure once an ordinary chunk boundary splits a label from its value — measured directly by simulating a
  fixed-size chunker cutting through a real extracted table.
- **HTML boilerplate (navigation, footers, asides, scripts, styles) must be explicitly skipped during
  extraction** — a naive "strip all tags" approach keeps this material mixed indiscriminately with real
  content.
- **A scanned document has no text layer at all — this is not an extraction bug, it is the expected result
  of a page containing only pixels.** OCR is the distinct technique that produces text from such a page;
  this lesson demonstrates the gap without running OCR itself.
- **A well-known, historically documented extraction failure (column-order scrambling) did not reproduce
  with this lesson's specific tool and simple test case** — reported honestly as a measured finding, with
  the explicit caveat that this does not generalize to all tools, layouts, or documents.
- **Different hard formats fail in different, specific ways** — there is no single fix; each requires its
  own explicit handling (boilerplate detection, table-aware chunking, content-vs-boilerplate HTML parsing,
  OCR).

---

## 13. Completion checklist

- [ ] I can explain why PDF extraction includes headers and footers with the same status as body text.
- [ ] I can explain why flattening a table to text loses its row/column structure, and how this becomes a
      concrete retrieval failure at a chunk boundary.
- [ ] I can implement a boilerplate-aware HTML extractor that skips navigation and footer elements.
- [ ] I can explain why a scanned document has no text layer, and what OCR does to address this.
- [ ] I test claimed extraction failure modes against my own tools and documents rather than assuming they
      apply universally.
- [ ] I test retrieval specifically against table-derived and scanned content before trusting a pipeline.
- [ ] I scored 10/13 on the quiz.

---

## 14. References

- pypdf documentation. <https://pypdf.readthedocs.io/> `[UNVERIFIED]`
- reportlab documentation. <https://www.reportlab.com/docs/reportlab-userguide.pdf> `[UNVERIFIED]`
- Tesseract OCR — GitHub repository. <https://github.com/tesseract-ocr/tesseract> `[UNVERIFIED]`

---

## 15. Next lesson

→ M7-L05 — Cleaning, Normalisation and Deduplication

You now have real, ingested text from every format this course covers, including the hard ones. Next: what
to do with extracted text before it's ready to chunk and embed — removing residual noise, normalizing
whitespace and encoding artifacts, and catching duplicate or near-duplicate content across your corpus.
