"""M7-L03 lab -- ingestion as its own pipeline stage: real files written to
disk and read back, a genuine encoding bug (wrong-charset assumption) shown
failing and then fixed, structure-preserving Markdown parsing, uniform
document records built from CSV and JSON sources, content-hash identity for
idempotent re-ingestion and change detection, and per-record error handling
so one bad file doesn't take down an entire ingestion run.

Deterministic. No API key, no network -- writes and reads real temporary
files on disk, cleaned up at the end.
Run:  python labs/m7/l03_ingestion_document_parsing.py
"""

from __future__ import annotations

import csv
import hashlib
import json
import shutil
import sys
import tempfile
from pathlib import Path

# This lesson is ABOUT encoding correctness -- fittingly, the fix for this
# console's own default codepage mangling non-ASCII characters (e.g. accented
# letters, em-dashes) in printed output is exactly the discipline the lesson
# teaches: don't rely on a default encoding, set one explicitly.
sys.stdout.reconfigure(encoding="utf-8")


def rule(title: str) -> None:
    print(f"\n{'=' * 76}\n{title}\n{'=' * 76}")


WORKDIR = Path(tempfile.mkdtemp(prefix="m7l03_"))


def cleanup() -> None:
    shutil.rmtree(WORKDIR, ignore_errors=True)


# ============================================================ 1
rule("1. THE CLASSIC INGESTION BUG: WRONG ENCODING, SILENT CORRUPTION")

# A real file written in cp1252 (Windows-1252) -- a plausible export format --
# containing characters outside plain ASCII.
CP1252_TEXT = "The café's naïve approach failed — client said “never again”."
cp1252_path = WORKDIR / "legacy_export.txt"
cp1252_path.write_bytes(CP1252_TEXT.encode("cp1252"))

print(f"  Wrote a real file ({cp1252_path.name}) encoded as cp1252, containing:")
print(f"    {CP1252_TEXT!r}\n")

print("  Reading it back ASSUMING utf-8 (a common, silent, wrong default):")
try:
    wrong = cp1252_path.read_text(encoding="utf-8")
    print(f"    Result: {wrong!r}")
except UnicodeDecodeError as e:
    print(f"    UnicodeDecodeError: {e}")

print("\n  Reading it back with a real fallback chain (try utf-8, then cp1252):")


def read_with_fallback(path: Path, encodings: tuple[str, ...] = ("utf-8", "cp1252", "latin-1")) -> tuple[str, str]:
    for enc in encodings:
        try:
            return path.read_bytes().decode(enc), enc
        except UnicodeDecodeError:
            continue
    raise ValueError(f"Could not decode {path} with any of {encodings}")


recovered, used_encoding = read_with_fallback(cp1252_path)
print(f"    Result (decoded as {used_encoding}): {recovered!r}")
print(f"    Matches original: {recovered == CP1252_TEXT}")

print("\n  Whether the wrong-encoding read above raised an exception or silently")
print("  produced garbled (but valid-looking) text depends on the SPECIFIC bytes")
print("  involved -- some byte sequences are invalid UTF-8 and raise immediately;")
print("  others happen to be valid UTF-8 by coincidence and decode into wrong,")
print("  silently corrupted characters. The second case is the dangerous one:")
print("  nothing crashes, so nothing alerts anyone that the content is wrong.")


# ============================================================ 2
rule("2. STRUCTURE-PRESERVING PARSING: PLAIN TEXT VS MARKDOWN")

PLAIN_TEXT = ("This is a flat support note with no structure at all. "
              "Everything is one block of prose with no headings to anchor on.")
plain_path = WORKDIR / "note.txt"
plain_path.write_text(PLAIN_TEXT, encoding="utf-8")

MARKDOWN_TEXT = """# Remote Work Policy

## Eligibility
Employees may work remotely up to three days per week with manager approval.

## Approval process
Fully remote arrangements require VP approval and a signed agreement.

# Expense Reimbursement Policy

## Deadlines
Expense reports must be submitted within thirty days of purchase.
"""
md_path = WORKDIR / "policies.md"
md_path.write_text(MARKDOWN_TEXT, encoding="utf-8")

print(f"  {plain_path.name}: {len(plain_path.read_text(encoding='utf-8'))} characters, "
      f"NO structure to parse -- ingestion can only record it as one opaque block.\n")


def parse_markdown_sections(text: str) -> list[dict]:
    """[REAL, deliberately simple] Track heading level via '#' count and group
    body text under the most recent heading at each level. Real Markdown has
    far more syntax (lists, code fences, links); this captures exactly the
    one structural signal chunking (M7-L06/M7-L07) most needs: heading
    boundaries and their nesting level."""
    sections = []
    current = None
    for line in text.splitlines():
        if line.startswith("#"):
            level = len(line) - len(line.lstrip("#"))
            heading = line.lstrip("#").strip()
            current = {"level": level, "heading": heading, "body": []}
            sections.append(current)
        elif current is not None and line.strip():
            current["body"].append(line.strip())
    for s in sections:
        s["body"] = " ".join(s["body"])
    return sections


md_sections = parse_markdown_sections(MARKDOWN_TEXT)
print(f"  {md_path.name}: parsed into {len(md_sections)} structured sections:")
for s in md_sections:
    print(f"    (level {s['level']}) {s['heading']!r}: {s['body'][:60]!r}"
          f"{'...' if len(s['body']) > 60 else ''}")

print("\n  This structure is exactly what naive, sentence-only chunking (M7-L01's")
print("  own placeholder) throws away. Preserving heading level and grouping")
print("  here is what lets M7-L06/M7-L07's real chunking strategies respect")
print("  document boundaries instead of splitting mid-topic.")


# ============================================================ 3
rule("3. CSV AND JSON AS DOCUMENT SOURCES -- ONE UNIFORM RECORD SHAPE")

csv_path = WORKDIR / "faq_export.csv"
with csv_path.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["question", "answer", "category"])
    writer.writeheader()
    writer.writerow({"question": "How do I reset my password?",
                      "answer": "Use the 'forgot password' link on the login page.",
                      "category": "account"})
    writer.writerow({"question": "What payment methods are accepted?",
                      "answer": "Visa, Mastercard, and bank transfer.",
                      "category": "billing"})

json_path = WORKDIR / "articles_export.json"
json_path.write_text(json.dumps([
    {"title": "Shipping Times", "content": "Standard shipping takes 5-7 business days.", "tags": ["shipping"]},
    {"title": "Return Policy", "content": "Items may be returned within 30 days of delivery.", "tags": ["returns"]},
]), encoding="utf-8")


def document_id(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]


def ingest_csv(path: Path) -> list[dict]:
    docs = []
    with path.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            text = f"{row['question']} {row['answer']}"
            docs.append({"id": document_id(text), "source": str(path.name),
                         "text": text, "metadata": {"category": row["category"]}})
    return docs


def ingest_json(path: Path) -> list[dict]:
    docs = []
    for item in json.loads(path.read_text(encoding="utf-8")):
        text = f"{item['title']}. {item['content']}"
        docs.append({"id": document_id(text), "source": str(path.name),
                     "text": text, "metadata": {"tags": item["tags"]}})
    return docs


csv_docs = ingest_csv(csv_path)
json_docs = ingest_json(json_path)
all_docs = csv_docs + json_docs

print(f"  Ingested {len(csv_docs)} records from {csv_path.name} and "
      f"{len(json_docs)} from {json_path.name} into ONE uniform shape:\n")
for d in all_docs:
    print(f"    id={d['id']}  source={d['source']}  metadata={d['metadata']}")
    print(f"      text={d['text']!r}")

print("\n  A CSV row and a JSON object have nothing in common as raw formats --")
print("  but downstream (chunking, embedding, indexing) needs to work with ONE")
print("  shape regardless of where a document came from. This uniform record")
print("  (id, source, text, metadata) is that shape.")


# ============================================================ 4
rule("4. CONTENT-HASH IDENTITY: IDEMPOTENT RE-INGESTION AND CHANGE DETECTION")

first_pass = ingest_csv(csv_path)
second_pass = ingest_csv(csv_path)   # re-ingesting the SAME file
ids_match = [a["id"] == b["id"] for a, b in zip(first_pass, second_pass)]
print(f"  Re-ingesting the SAME file twice: IDs identical both times? {all(ids_match)}")

with csv_path.open("a", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["question", "answer", "category"])
    writer.writerow({"question": "How do I reset my password?",
                      "answer": "Use the 'forgot password' link on the login page, or contact support.",
                      "category": "account"})
edited_pass = ingest_csv(csv_path)
print(f"  Original first record id: {first_pass[0]['id']}")
print(f"  A near-duplicate record with ONE clause added (same question, "
      f"slightly longer answer): {edited_pass[2]['id']}")
print(f"  These differ: {first_pass[0]['id'] != edited_pass[2]['id']}")

print("\n  A content hash gives ingestion a stable, deterministic identity with")
print("  no external ID-tracking database needed: the SAME text always produces")
print("  the SAME id (idempotent -- re-running ingestion doesn't create")
print("  duplicates), and ANY change to the text produces a DIFFERENT id (so a")
print("  changed document is detected as new/different, not silently skipped.")
print("  M7-L16 builds on exactly this property for incremental updates and")
print("  deletion propagation.")


# ============================================================ 5
rule("5. ONE BAD RECORD SHOULD NOT SINK THE WHOLE INGESTION RUN")

MALFORMED_JSON = '[{"title": "Valid Article", "content": "This one is fine.", "tags": []}, {"title": "Broken",]'
bad_json_path = WORKDIR / "broken_export.json"
bad_json_path.write_text(MALFORMED_JSON, encoding="utf-8")

BATCH = [json_path, bad_json_path, csv_path]
print(f"  Ingesting a batch of {len(BATCH)} sources, one of which is malformed JSON:\n")

succeeded, failed = [], []
for path in BATCH:
    try:
        if path.suffix == ".json":
            docs = ingest_json(path)
        else:
            docs = ingest_csv(path)
        succeeded.append((path.name, len(docs)))
    except json.JSONDecodeError as e:
        failed.append((path.name, str(e)))

print("  Succeeded:")
for name, count in succeeded:
    print(f"    {name}: {count} document(s) ingested")
print("  Failed (logged, batch continued):")
for name, err in failed:
    print(f"    {name}: {err}")

print(f"\n  {len(succeeded)} of {len(BATCH)} sources ingested successfully despite one")
print("  genuinely broken file. A pipeline that raises on the FIRST error and")
print("  aborts the entire batch turns one malformed source file into total")
print("  ingestion downtime for every OTHER, perfectly valid source in the same")
print("  run -- catching and logging per-record failures, then continuing, is")
print("  the difference between a partial, diagnosable problem and a full outage.")


# ============================================================ 6
rule("6. WHAT THIS LAB IS AND IS NOT")

print("  REAL: every file in this lab is genuinely written to disk and read")
print("  back; the encoding failure and its fix are real, measured decode")
print("  behavior; content hashes are computed with the real SHA-256 algorithm;")
print("  the malformed-JSON failure is a real, caught exception, not simulated.")
print("\n  NOT SHOWN: PDFs, HTML, scanned images and OCR, and tables embedded in")
print("  documents -- these 'hard formats' are M7-L04's dedicated topic. Text")
print("  cleaning (removing boilerplate, normalizing whitespace) and cross-")
print("  document deduplication are M7-L05's topic, not this one. Splitting a")
print("  document's text into retrieval-sized pieces is M7-L06/M7-L07's topic;")
print("  this lab stops at whole-document (or whole-record) ingestion.")

cleanup()
print(f"\n  (Temporary files cleaned up: {WORKDIR})")
print("\nDone.")
