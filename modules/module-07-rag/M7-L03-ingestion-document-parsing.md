# M7-L03 — Ingestion and Document Parsing

| | |
|---|---|
| **Lesson ID** | M7-L03 |
| **Difficulty** | 2 (Intermediate) |
| **Estimated study time** | 2.0 hours |
| **Prerequisites** | M2-L09 |

---

## 1. Learning objectives

1. **Diagnose** and fix a wrong-encoding read, and explain why a silent, non-crashing failure is more
   dangerous than one that raises an exception.
2. **Parse** structured text (Markdown headings) into a form that preserves document structure for later
   use, rather than discarding it.
3. **Normalize** documents from heterogeneous raw formats (CSV, JSON) into one uniform internal record
   shape.
4. **Assign** stable, content-based document identity, and explain what idempotent re-ingestion and
   change detection buy a pipeline.
5. **Design** ingestion to fail per-record rather than per-batch, so one malformed source doesn't take
   down an entire run.

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **Ingestion** | The pipeline stage that reads raw source documents (files, exports, API responses) and produces a usable internal representation. |
| **Encoding** | The specific byte-to-character mapping (UTF-8, CP-1252, Latin-1, ...) used to store text; assuming the wrong one corrupts or fails to read the content. |
| **Mojibake** | Text that has been decoded with the wrong character encoding, producing garbled but sometimes still valid-looking characters. |
| **Uniform document record** | A single internal shape (e.g. id, source, text, metadata) that every ingested document is normalized into, regardless of its original raw format. |
| **Content hash** | A deterministic fingerprint (e.g. SHA-256) computed from a document's text, used as a stable identifier that changes if and only if the content changes. |

---

## 3. Plain-language explanation

### 3.1 M7-L01/M7-L02 treated ingestion as a given; this lesson builds it

Every lab so far in Module 7 started from documents already sitting in a Python dictionary. Real documents
arrive as files on disk, database exports, or API responses, in a mix of formats, encodings, and states of
correctness. This lesson is the first of the pipeline's actual first stage.

### 3.2 The encoding bug you don't see until it's already wrong

§7.1 demonstrates the single most common, most silent ingestion bug: assuming every source file is UTF-8
when some aren't. Sometimes this fails loudly (an exception). Sometimes it doesn't fail at all — it just
produces wrong text that looks plausible enough that nobody notices until much later.

### 3.3 Structure is information; discarding it early is a decision, not a default

§7.2 contrasts a flat text file (nothing to parse) with a Markdown file (real heading structure). Keeping
that structure through ingestion isn't extra work for its own sake — it's what later chunking (M7-L06,
M7-L07) needs to make good decisions about where a document can and can't be safely split.

### 3.4 Every format needs to end up looking the same

§7.3 takes a CSV export and a JSON export — two formats with nothing in common — and normalizes both into
one identical record shape. Nothing past this stage needs to know or care which format a document
originally came from.

### 3.5 Identity has to survive being ingested twice

§7.4 establishes something easy to skip past: a document needs an ID that is the same every time the same
content is ingested, and different the moment the content changes. A content hash gives you both
properties for free, with no external bookkeeping required.

### 3.6 A batch of documents is not one document

§7.5 shows the practical consequence of treating ingestion as one atomic operation instead of many
independent ones: a single malformed file can silently take down every other file's ingestion along with
it, unless failures are caught and handled per record.

---

## 4. Analogy

**A mailroom sorting incoming letters written in different languages, some in unfamiliar handwriting.** A
good mailroom clerk doesn't assume every letter is in the same language and handwriting style as the last
one — they check first, and have a fallback process for the ones that don't match the default assumption.
They don't discard the letterhead and signature just because the body text is what matters most today —
tomorrow, someone will need to know who sent it and file it correctly. And if one letter arrives torn and
unreadable, a competent mailroom sets it aside with a note and keeps processing the rest of the day's mail
— it doesn't stop delivering every other letter until that one is fixed.

### Where the analogy breaks

- **A human mailroom clerk exercises judgment on each letter individually.** §7.1's fallback-encoding
  chain and §7.5's per-record error handling are mechanical, deterministic rules — they need to be
  designed in advance, not applied ad hoc.
- **A torn letter is usually obviously torn.** §7.1's dangerous case is precisely the encoding failure that
  looks fine — the mailroom analogy's "obviously unreadable" letter doesn't capture mojibake's silent risk.

---

## 5. Detailed technical explanation

### 5.1 Encoding: fail loud, fail silent, or fall back

`[REAL, measured]` §7.1 wrote a real file encoded as CP-1252 containing accented characters and an em-dash,
then read it back three ways. Assuming UTF-8 raised `UnicodeDecodeError` immediately, because one specific
byte (`0xe9`) is not valid UTF-8 on its own. **This is the fortunate case** — the failure is loud and
immediate. A fallback chain (`try utf-8, then cp1252, then latin-1`, first success wins) recovered the
exact original text.

**The genuinely dangerous case is the one this lab's specific bytes happened not to trigger**: some invalid
CP-1252 byte sequences are, by coincidence, ALSO valid UTF-8 — decoding them under the wrong assumption
produces no exception at all, only wrong characters. Nothing alerts anyone. This is why a fallback chain
(or a proper encoding-detection library in a real system) matters more than it initially appears to.

### 5.2 Structure-preserving parsing

`[REAL]` §7.2 parsed a Markdown document by tracking `#` count as heading level and grouping subsequent
lines under the most recent heading, producing 5 structured sections with explicit level and heading text
preserved. **This is deliberately simple** — real Markdown has far more syntax — but it captures the one
signal that matters most for what comes next: **where a document's natural topic boundaries are**, so
M7-L06/M7-L07's chunking strategies can respect them instead of splitting mid-sentence or mid-topic through
sheer ignorance of structure.

### 5.3 One shape for every source format

`[REAL]` §7.3 ingested a CSV file (via Python's `csv.DictReader`) and a JSON file (via `json.loads`) — two
formats sharing no structural similarity — into one identical record shape: `{id, source, text, metadata}`.
**This normalization is what lets every later stage (chunking, embedding, indexing, retrieval) remain
completely agnostic to where a document originally came from.** Without it, every downstream stage would
need format-specific logic, multiplying complexity throughout the pipeline instead of concentrating it in
one place.

### 5.4 Content-hash identity

`[REAL, measured]` §7.4 computed each document's ID as a SHA-256 hash of its text (truncated for
readability). Re-ingesting the identical CSV file twice produced **identical IDs both times** — ingestion
is idempotent; running it again does not create duplicate records. Adding one clause to an existing
record's answer text produced a **different ID**, correctly signaling changed content.

**A randomly generated ID (e.g. a UUID assigned at ingestion time) would have neither property**: it would
differ across re-ingestions of unchanged content (creating spurious duplicates) and would give no signal
at all that content had changed. M7-L16 builds directly on this same content-hash property for incremental
updates and deletion propagation.

### 5.5 Per-record failure, not per-batch failure

`[REAL, measured]` §7.5 ingested a batch of three sources, one containing deliberately malformed JSON.
Catching the parse failure for that one file and continuing let **2 of 3 sources ingest successfully** in
the same run. The alternative — raising on the first error and aborting the whole batch — would have
turned one broken file into zero documents ingested from any source that run, including the two files with
nothing wrong with them at all.

### 5.6 Assumptions and limitations

- This lesson's Markdown parser is deliberately minimal (heading level and grouping only) — a real system
  would need to handle lists, code fences, links, and more.
- The CP-1252 fallback chain in §7.1 is a simple, small example; a real system typically uses a dedicated
  encoding-detection library for source files of unknown provenance. `[UNVERIFIED — confirm current
  best-practice tooling before relying on any specific library.]`
- This lesson does not cover "hard" formats (PDF, HTML, scanned images/OCR, embedded tables) — that is
  M7-L04's dedicated topic — nor text cleaning or cross-document deduplication, which is M7-L05's.

---

## 6. Worked example — the quarterly export that silently corrupted 40% of one region's data

**The system.** A company ingests customer feedback from several regional support systems as CSV exports,
merged into one knowledge base. The pipeline assumes UTF-8 for every file, since most exports have always
been UTF-8.

**What went wrong.** One region's support system exported files in CP-1252, and roughly 40% of that
region's records happened to contain byte sequences that were *coincidentally valid UTF-8* under the wrong
assumption — no exception was ever raised. For months, search results for anything containing an accented
name or an em-dash from that region returned mangled, barely-readable text, while every other region's
data looked completely normal.

**Why it went undetected for months.** Per §5.1, this is exactly the dangerous case: no crash, no error
log entry, no obvious signal — just wrong characters that a human skimming search results might mentally
"autocorrect" without registering as a bug, until enough of them accumulated in one place to look
suspicious.

**Three defects:**

| # | Defect | Consequence |
|---|---|---|
| 1 | Encoding was assumed (UTF-8) rather than detected or attempted via a fallback chain | Legitimately different-encoded regional exports were silently misread |
| 2 | No validation step checked ingested text for signs of mojibake (e.g. unusual replacement-character-adjacent patterns) | The corruption had no automated detection mechanism |
| 3 | Nothing logged which encoding was actually used per file | When the bug was finally noticed, there was no record to help diagnose which files were affected |

### The fix

**Use a fallback encoding chain (or a real detection library) for any file whose encoding isn't
guaranteed**, per §5.1 — never assume a single encoding across all sources without justification.

**Log which encoding was actually used for each ingested file**, so a later investigation can immediately
identify which files are suspect, rather than re-deriving this from scratch.

**Add a lightweight sanity check for mojibake patterns** as a safety net, catching what a fallback chain
alone might still miss on genuinely ambiguous byte sequences.

**The general rule.** **An encoding assumption that happens to be right most of the time is still a latent
bug, and the failure mode when it's wrong is frequently silent — treat encoding detection as a required
ingestion step, not an edge case worth skipping for convenience.**

---

## 7. Practical activity

**File:** [`labs/m7/l03_ingestion_document_parsing.py`](../../labs/m7/l03_ingestion_document_parsing.py)

**No API key, no network.** Writes and reads real temporary files, cleaned up automatically. Runs in well
under a second.

```bash
source .venv/bin/activate
python labs/m7/l03_ingestion_document_parsing.py
```

### 7.2 Expected output

`[EXECUTED]` — 2026-09-10, Python 3.10.11 (pure standard library, no third-party dependencies).

```text
============================================================================
1. THE CLASSIC INGESTION BUG: WRONG ENCODING, SILENT CORRUPTION
============================================================================
  Wrote a real file (legacy_export.txt) encoded as cp1252, containing:
    "The café's naïve approach failed — client said "never again"."

  Reading it back ASSUMING utf-8 (a common, silent, wrong default):
    UnicodeDecodeError: 'utf-8' codec can't decode byte 0xe9 in position 7: invalid continuation byte

  Reading it back with a real fallback chain (try utf-8, then cp1252):
    Result (decoded as cp1252): "The café's naïve approach failed — client said "never again"."
    Matches original: True

  Whether the wrong-encoding read above raised an exception or silently
  produced garbled (but valid-looking) text depends on the SPECIFIC bytes
  involved -- some byte sequences are invalid UTF-8 and raise immediately;
  others happen to be valid UTF-8 by coincidence and decode into wrong,
  silently corrupted characters. The second case is the dangerous one:
  nothing crashes, so nothing alerts anyone that the content is wrong.

============================================================================
2. STRUCTURE-PRESERVING PARSING: PLAIN TEXT VS MARKDOWN
============================================================================
  note.txt: 117 characters, NO structure to parse -- ingestion can only record it as one opaque block.

  policies.md: parsed into 5 structured sections:
    (level 1) 'Remote Work Policy': ''
    (level 2) 'Eligibility': 'Employees may work remotely up to three days per week with m'...
    (level 2) 'Approval process': 'Fully remote arrangements require VP approval and a signed a'...
    (level 1) 'Expense Reimbursement Policy': ''
    (level 2) 'Deadlines': 'Expense reports must be submitted within thirty days of purc'...

  This structure is exactly what naive, sentence-only chunking (M7-L01's
  own placeholder) throws away. Preserving heading level and grouping
  here is what lets M7-L06/M7-L07's real chunking strategies respect
  document boundaries instead of splitting mid-topic.

============================================================================
3. CSV AND JSON AS DOCUMENT SOURCES -- ONE UNIFORM RECORD SHAPE
============================================================================
  Ingested 2 records from faq_export.csv and 2 from articles_export.json into ONE uniform shape:

    id=dd41b7979c5e  source=faq_export.csv  metadata={'category': 'account'}
      text="How do I reset my password? Use the 'forgot password' link on the login page."
    id=3d6fa1ee8852  source=faq_export.csv  metadata={'category': 'billing'}
      text='What payment methods are accepted? Visa, Mastercard, and bank transfer.'
    id=932ef19f7689  source=articles_export.json  metadata={'tags': ['shipping']}
      text='Shipping Times. Standard shipping takes 5-7 business days.'
    id=679cdde89a3d  source=articles_export.json  metadata={'tags': ['returns']}
      text='Return Policy. Items may be returned within 30 days of delivery.'

  A CSV row and a JSON object have nothing in common as raw formats --
  but downstream (chunking, embedding, indexing) needs to work with ONE
  shape regardless of where a document came from. This uniform record
  (id, source, text, metadata) is that shape.

============================================================================
4. CONTENT-HASH IDENTITY: IDEMPOTENT RE-INGESTION AND CHANGE DETECTION
============================================================================
  Re-ingesting the SAME file twice: IDs identical both times? True
  Original first record id: dd41b7979c5e
  A near-duplicate record with ONE clause added (same question, slightly longer answer): 3675f5e8d7f5
  These differ: True

  A content hash gives ingestion a stable, deterministic identity with
  no external ID-tracking database needed: the SAME text always produces
  the SAME id (idempotent -- re-running ingestion doesn't create
  duplicates), and ANY change to the text produces a DIFFERENT id (so a
  changed document is detected as new/different, not silently skipped.
  M7-L16 builds on exactly this property for incremental updates and
  deletion propagation.

============================================================================
5. ONE BAD RECORD SHOULD NOT SINK THE WHOLE INGESTION RUN
============================================================================
  Ingesting a batch of 3 sources, one of which is malformed JSON:

  Succeeded:
    articles_export.json: 2 document(s) ingested
    faq_export.csv: 3 document(s) ingested
  Failed (logged, batch continued):
    broken_export.json: Expecting property name enclosed in double quotes: line 1 column 93 (char 92)

  2 of 3 sources ingested successfully despite one
  genuinely broken file. A pipeline that raises on the FIRST error and
  aborts the entire batch turns one malformed source file into total
  ingestion downtime for every OTHER, perfectly valid source in the same
  run -- catching and logging per-record failures, then continuing, is
  the difference between a partial, diagnosable problem and a full outage.

============================================================================
6. WHAT THIS LAB IS AND IS NOT
============================================================================
  REAL: every file in this lab is genuinely written to disk and read
  back; the encoding failure and its fix are real, measured decode
  behavior; content hashes are computed with the real SHA-256 algorithm;
  the malformed-JSON failure is a real, caught exception, not simulated.

  NOT SHOWN: PDFs, HTML, scanned images and OCR, and tables embedded in
  documents -- these 'hard formats' are M7-L04's dedicated topic. Text
  cleaning (removing boilerplate, normalizing whitespace) and cross-
  document deduplication are M7-L05's topic, not this one. Splitting a
  document's text into retrieval-sized pieces is M7-L06/M7-L07's topic;
  this lab stops at whole-document (or whole-record) ingestion.

  (Temporary files cleaned up automatically at the end of the run.)

Done.
```

*(Note: this lab explicitly reconfigures stdout to UTF-8 before printing — fittingly, since a console's own
default codepage mangling accented characters is the same class of encoding-assumption bug section 1 is
about. Your own terminal's exact temporary-directory path will differ between runs; this is expected.)*

### 7.3 Reading the result

**Section 1's two outcomes (loud failure vs. silent corruption) are the single most important idea in this
lesson.** It would be easy to think "my ingestion crashed, so I'll notice encoding bugs" — the point is
that you cannot rely on that; some wrong-encoding reads produce no signal at all.

**Section 4's two comparisons (same file twice; one clause added) are a minimal but complete proof of
content-hash identity's two required properties.** Both needed to be demonstrated, not just asserted,
because idempotence without change-detection (or vice versa) would be a much weaker, less useful property.

**Section 5's "2 of 3 succeeded" is more valuable than "3 of 3 succeeded would have been."** A lab where
every file happened to be valid would not demonstrate the actual point: that failure isolation, not
universal success, is what makes an ingestion pipeline operationally trustworthy.

---

## 8. Common mistakes and troubleshooting

1. **Assuming every source file uses the same encoding.** §5.1 — use a fallback chain or a real detection
   library; assuming wrong can fail loudly (recoverable) or silently (dangerous).
2. **Discarding document structure (headings, sections) during ingestion "to keep things simple."** §5.2 —
   this information is exactly what later chunking needs; it is much harder to recover than to preserve.
3. **Writing separate, format-specific logic all the way through the pipeline instead of normalizing
   early.** §5.3 — normalize to one uniform record shape at ingestion, not repeatedly downstream.
4. **Using a randomly generated ID instead of a content hash for document identity.** §5.4 — this loses
   both idempotent re-ingestion and change detection, which a content hash provides for free.
5. **Letting one malformed file abort an entire ingestion batch.** §5.5 — catch and log failures per
   record/file, and continue processing the rest of the batch.
6. **Not logging which encoding (or fallback) was actually used per file.** §6 — without this, diagnosing
   an encoding bug after the fact requires guesswork instead of a direct lookup.

| Symptom | Likely cause | Fix |
|---|---|---|
| Search results contain garbled or mangled characters for some documents but not others | A wrong-encoding read that happened to succeed without raising an exception | Use a fallback encoding chain or detection library; log the encoding used per file (§5.1, §6) |
| Chunking splits documents in ways that ignore obvious section boundaries | Document structure was discarded during ingestion | Preserve heading/section structure at ingestion time (§5.2) |
| Re-running ingestion creates duplicate documents | Using a non-deterministic ID (e.g. a fresh UUID) instead of a content hash | Switch to content-hash-based IDs (§5.4) |
| One broken source file causes an entire scheduled ingestion job to fail with zero documents processed | Batch-level error handling instead of per-record | Catch and log errors per file/record; continue the batch (§5.5) |

---

## 9. Security, privacy, reliability, cost

- **Reliability.** Never assume a single encoding across all source files without justification — use a
  fallback chain or detection library, and log which encoding was actually used per file (§5.1, §6).
- **Reliability.** Use content-based, deterministic document IDs, not randomly generated ones, so
  re-ingestion is idempotent and content changes are detectable (§5.4).
- **Reliability.** Handle ingestion failures per record or per file, not per batch, so one malformed source
  cannot silently or completely halt processing of every other valid source (§5.5).
- **Privacy.** Ingested metadata (source paths, categories, tags) can itself carry sensitive information —
  treat the uniform document record's metadata field with the same care as its text.

---

## 10. Exercises

### Exercise 1 — Beginner (~20 min)

1. In one sentence, why is a wrong-encoding read that raises an exception the "fortunate" case?
2. What structural information does §7.2's Markdown parser preserve that a flat-text reader cannot?
3. Why does converting CSV and JSON sources into one uniform record shape simplify the rest of the
   pipeline?
4. What two properties does a content-hash-based document ID have that a random ID would not?
5. Why did the lab's ingestion batch succeed for 2 of 3 sources instead of failing entirely?

### Exercise 2 — Intermediate (~40 min)

1. Run the lab. Confirm §7.1's exception message and §7.4's matching/differing IDs on your own machine.
2. Write a new source file encoded in a THIRD encoding (not UTF-8 or CP-1252) and extend the fallback
   chain to correctly recover it.
3. Extend §7.2's Markdown parser to also capture bullet-point lists as a structural element, and test it
   on a document containing both headings and lists.
4. Add a fourth source format (e.g. a simple `.txt` file with a custom delimiter) and write an ingestion
   function that normalizes it into the same uniform record shape as §7.3.
5. Deliberately introduce a second kind of malformed input (e.g. a CSV with a missing required column) and
   extend §7.5's error handling to catch and log it without aborting the batch.

### Exercise 3 — Challenge (~50 min)

1. Implement a simple mojibake-detection heuristic (e.g. flagging an unusual density of specific
   suspicious character patterns) and test it against both a correctly-decoded and an incorrectly-decoded
   version of §7.1's file.
2. Design and implement an ingestion manifest that logs, for every ingested file: source path, detected/
   used encoding, content hash, and ingestion timestamp — then use it to answer "which files were affected"
   for a hypothetical encoding bug.
3. Extend §7.4's change-detection property into a small incremental-ingestion function that, given a
   previous manifest and a re-scanned set of files, reports which are new, which are unchanged, and which
   have changed content.
4. Research (conceptually) how a real encoding-detection library (e.g. one commonly used in Python)
   decides which encoding to guess, and compare its approach to this lab's simple fixed-order fallback
   chain.
5. Write a short incident postmortem (under 300 words), modeled on §6, for a hypothetical ingestion bug
   you design yourself involving either encoding or malformed-batch handling.

---

## 11. Quiz

*(Answers: [`answer-keys/module-07-answers.md`](../../answer-keys/module-07-answers.md#m7-l03).)*

**Q1.** Why did reading the CP-1252-encoded file while assuming UTF-8 raise a `UnicodeDecodeError` in
§7.1's first case?

- A. The specific byte sequence involved (from an accented character) is not valid UTF-8 at all, so the decoder rejected it outright rather than misinterpreting it.
- B. The file was corrupted during writing and no longer exists on disk.
- C. Python cannot read files smaller than a fixed minimum size.
- D. UTF-8 cannot represent any character outside the ASCII range under any circumstance.

**Q2.** Per §7.1, why is a wrong-encoding read that succeeds WITHOUT raising an exception described as the
more dangerous case?

- A. Because it always crashes the entire ingestion pipeline immediately.
- B. Because it takes measurably longer to execute than a failing read.
- C. Because it only happens with files larger than a fixed size threshold.
- D. Because it produces silently corrupted (mojibake) text with no error signal at all, so nothing alerts anyone the content is wrong.

**Q3.** What is the fallback strategy demonstrated in §7.1 for handling unknown or mixed source encodings?

- A. Delete the file and skip it if the first encoding attempted fails.
- B. Try a sequence of encodings in order (e.g. utf-8, then cp1252, then latin-1), using the first one that decodes without error.
- C. Always assume every file is encoded in ASCII only.
- D. Convert every file to a JSON format before attempting to read it.

**Q4.** Per §7.2, why does parsing Markdown's heading structure matter for a RAG pipeline, even though this
lesson doesn't do any chunking itself?

- A. Because Markdown files cannot be ingested by any other means.
- B. Because heading structure determines a document's file size on disk.
- C. Because heading level and grouping is exactly the structural signal later chunking stages (M7-L06/M7-L07) need to avoid splitting a document mid-topic.
- D. Because plain text files are always preferred over Markdown for ingestion.

**Q5.** Per §7.3, what problem does converting both CSV rows and JSON objects into one uniform document
record (id, source, text, metadata) solve?

- A. Downstream stages (chunking, embedding, indexing) need to work with one consistent shape regardless of which raw format a document originally came from.
- B. CSV files cannot otherwise be read by any Python program.
- C. JSON objects are always converted into CSV rows before being usable.
- D. It removes the need for a source or metadata field on any document.

**Q6.** Per §7.4, why does this lab use a content hash (e.g. SHA-256 of the text) as a document's ID rather
than, say, a random UUID generated at ingestion time?

- A. A random UUID is always faster to compute than a content hash.
- B. Content hashes are required by law for any document processing system.
- C. A content hash guarantees a document's text can never be changed once ingested.
- D. A content hash is deterministic — the same text always produces the same ID (idempotent), while any change to the text produces a different ID (detectable) — properties a random ID would not have.

**Q7.** Per §7.4's measured result, what happened when the same CSV file was ingested twice without any
change?

- A. The second ingestion pass produced entirely different IDs from the first.
- B. Both ingestion passes produced identical document IDs for the same records.
- C. The second ingestion pass failed with an error.
- D. The file's content changed automatically between the two passes.

**Q8.** Per §7.4, what happened when one clause was added to an existing record's answer text?

- A. The record's ID stayed exactly the same as before the edit.
- B. The ingestion pipeline raised an exception and stopped.
- C. The record's content hash (ID) changed, correctly signaling that the content is different from before.
- D. The edit was silently ignored and never reflected in the ingested text.

**Q9.** Per §7.5, what did the lab's ingestion batch do when one of three source files contained malformed
JSON?

- A. It caught and logged the error for that one file specifically, while still successfully ingesting the other two valid sources in the same run.
- B. The entire batch failed immediately with no documents ingested at all.
- C. It silently skipped all three files without reporting anything.
- D. It automatically repaired the malformed JSON and ingested it anyway.

**Q10.** Per §7.5, why is "abort the entire batch on the first error" described as a poor ingestion design?

- A. Because it makes ingestion run faster overall.
- B. Because it is required by most file formats.
- C. Because it guarantees higher data quality than per-record error handling.
- D. Because it turns one malformed source file into total ingestion downtime for every other, perfectly valid source in the same run.

**Q11.** Per §7.6, which topics does this lesson explicitly leave to M7-L04 and M7-L05 respectively?

- A. Chunking strategy to M7-L06/M7-L07; retrieval metrics to M6-L13.
- B. "Hard formats" (PDFs, HTML, scans/OCR, tables) to M7-L04; text cleaning and cross-document deduplication to M7-L05.
- C. Encoding detection to M7-L04; content hashing to M7-L05.
- D. Everything covered in this lesson is also covered again in M7-L04 and M7-L05.

**Q12.** What is the general lesson this lab demonstrates about ingestion as a pipeline stage?

- A. Ingestion is not actually a necessary stage in a real RAG pipeline.
- B. Ingestion failures can always be fully prevented by using only one file format.
- C. Ingestion has its own real failure modes (encoding, malformed input, format heterogeneity) and its own responsibilities (structure preservation, stable identity) distinct from chunking, cleaning, or retrieval.
- D. Ingestion and chunking are the same operation performed twice for redundancy.

**Q13.** *(Written, rubric-graded.)* In under 150 words: a teammate proposes skipping encoding detection
entirely, since "almost all our files are UTF-8 anyway." Based on this lesson, how would you respond?

---

## 12. Revision notes

- **A wrong-encoding read either fails loudly (an exception) or fails silently (mojibake with no error
  signal)** — the silent case is the more dangerous one, since nothing alerts anyone the content is wrong.
  Demonstrated: the same wrong assumption raised an exception on one file's specific bytes, and the fix
  (a fallback encoding chain) recovered the correct text.
- **Preserving document structure (e.g. Markdown headings) during ingestion is what lets later chunking
  respect topic boundaries** — discarding it early is a real, avoidable information loss, not a
  simplification.
- **Normalizing every source format into one uniform record shape (id, source, text, metadata) at
  ingestion time keeps every downstream stage format-agnostic.**
- **A content hash gives a document ID two properties a random ID lacks**: idempotent re-ingestion (same
  content, same ID) and change detection (different content, different ID) — measured directly by
  re-ingesting an unchanged file and then an edited one.
- **Ingestion should fail per record, not per batch** — measured: 2 of 3 sources ingested successfully
  despite one genuinely malformed file, because the failure was caught and logged rather than allowed to
  abort the whole run.
- **Ingestion has its own real failure modes and responsibilities**, distinct from chunking (M7-L06/L07),
  cleaning and deduplication (M7-L05), and hard-format parsing (M7-L04) — each gets its own dedicated
  lesson.

---

## 13. Completion checklist

- [ ] I can explain why a silent wrong-encoding read is more dangerous than one that raises an exception.
- [ ] I can implement a fallback encoding chain for reading files of unknown or mixed encoding.
- [ ] I preserve document structure (e.g. headings) during ingestion rather than discarding it by default.
- [ ] I normalize documents from different raw formats into one uniform internal record shape.
- [ ] I use content-hash-based document IDs and can explain the two properties this gives me.
- [ ] I design ingestion to fail per record, not per batch, so one bad file doesn't halt an entire run.
- [ ] I scored 10/13 on the quiz.

---

## 14. References

- Python documentation, `codecs` — *Standard Encodings*. <https://docs.python.org/3/library/codecs.html#standard-encodings> `[UNVERIFIED]`
- Python documentation, `hashlib` — *Secure hashes and message digests*. <https://docs.python.org/3/library/hashlib.html> `[UNVERIFIED]`

---

## 15. Next lesson

→ M7-L04 — Hard Formats: PDFs, HTML, Tables, Scans and OCR

You now have a working ingestion stage for plain text, Markdown, CSV, and JSON. Next: the formats that
don't cooperate — PDFs with unreliable text extraction, HTML full of navigation and boilerplate, tables
that don't linearize cleanly into prose, and scanned documents that have no text layer at all.
