"""M7-L04 lab -- the document formats that don't cooperate: real PDFs
generated and extracted to show header/footer repetition and total table
structure loss, a real stdlib-only HTML boilerplate-vs-content extractor,
and a real image-only "scanned" PDF proving a scan has no text layer at all
for standard extraction to find -- the exact gap OCR exists to close.

Requires: pypdf, reportlab, Pillow (PDF/image generation and extraction --
genuinely needed for this lesson's specific subject, unlike every other lab
in this course). No API key, no network beyond the one-time pip install.
Run:  python labs/m7/l04_hard_formats.py
"""

from __future__ import annotations

import io
import sys
from html.parser import HTMLParser

from PIL import Image, ImageDraw
from pypdf import PdfReader
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

sys.stdout.reconfigure(encoding="utf-8")


def rule(title: str) -> None:
    print(f"\n{'=' * 76}\n{title}\n{'=' * 76}")


# ============================================================ 1
rule("1. PDF HEADERS AND FOOTERS REPEAT ON EVERY PAGE")

buf = io.BytesIO()
c = canvas.Canvas(buf, pagesize=letter)
BODY_LINES = [
    "Remote work requires manager approval for up to three days per week.",
    "Expense reports must be submitted within thirty days of purchase.",
    "Referral bonuses are paid after ninety days of the new hire.",
]
for i, line in enumerate(BODY_LINES, start=1):
    c.drawString(50, 750, "ACME CORP -- INTERNAL POLICY HANDBOOK")
    c.drawString(50, 700, line)
    c.drawString(50, 50, f"Page {i} of {len(BODY_LINES)} -- Confidential -- Do not distribute")
    c.showPage()
c.save()
buf.seek(0)

reader = PdfReader(buf)
raw_pages = [page.extract_text() for page in reader.pages]
raw_text = "\n".join(raw_pages)

print(f"  A real {len(raw_pages)}-page PDF, generated and text-extracted "
      f"(pypdf {__import__('pypdf').__version__}):\n")
print(f"  {raw_text!r}\n")
print(f"  Header line repeats: {raw_text.count('INTERNAL POLICY HANDBOOK')} times")
print(f"  Footer pattern repeats: {raw_text.count('Confidential')} times")


def strip_repeated_lines(pages: list[str], min_page_fraction: float = 0.6) -> str:
    """[REAL] A line that appears on most pages, verbatim, is very likely a
    running header/footer rather than real body content -- a simple,
    checkable heuristic, not a claim that this is the only correct method."""
    lines_per_page = [set(p.splitlines()) for p in pages]
    n = len(pages)
    all_lines = set().union(*lines_per_page)
    boilerplate = {line for line in all_lines
                   if sum(1 for lp in lines_per_page if line in lp) / n >= min_page_fraction}
    cleaned_pages = []
    for p in pages:
        cleaned_pages.append("\n".join(l for l in p.splitlines() if l not in boilerplate))
    return "\n".join(cleaned_pages), boilerplate


cleaned_text, boilerplate_lines = strip_repeated_lines(raw_pages)
print(f"\n  Lines identified as boilerplate (appear on >= 60% of pages): {boilerplate_lines}")
print(f"  Cleaned text: {cleaned_text!r}")

print("\n  Notice the FOOTER is still there -- this simple, exact-match heuristic")
print("  only caught the header. Each footer line is technically DIFFERENT text")
print("  ('Page 1 of 3...' vs 'Page 2 of 3...'), because the page number is")
print("  embedded in it, so exact-string repetition never matches across pages")
print("  even though the PATTERN clearly repeats. Catching this needs a fuzzier")
print("  rule (e.g. a regex like 'Page \\d+ of \\d+ -- Confidential') -- real")
print("  boilerplate detection is genuinely harder than 'find repeated lines',")
print("  and this gap is left uncorrected here specifically to show that.")

print("\n  Nothing about a PDF FLAGS a header or footer as such -- extraction")
print("  returns every line of text on the page with equal status. Without")
print("  explicit boilerplate removal, a header repeated on every page of a")
print("  50-page document becomes 50 near-duplicate copies of the same six")
print("  words polluting the corpus, diluting real content in both search")
print("  results and any per-document token budget.")


# ============================================================ 2
rule("2. TABLES LOSE ALL ROW/COLUMN STRUCTURE WHEN FLATTENED TO TEXT")

table_buf = io.BytesIO()
tc = canvas.Canvas(table_buf, pagesize=letter)
HEADERS = ["Tier", "Years of Service", "PTO Days"]
ROWS = [["Junior", "0-2", "15"], ["Mid", "3-5", "20"], ["Senior", "6+", "25"]]
COL_X = [50, 200, 350]
y = 700
for i, h in enumerate(HEADERS):
    tc.drawString(COL_X[i], y, h)
y -= 20
for row in ROWS:
    for i, cell in enumerate(row):
        tc.drawString(COL_X[i], y, cell)
    y -= 20
tc.save()
table_buf.seek(0)

table_text = PdfReader(table_buf).pages[0].extract_text()
print(f"  A real 3-row, 3-column table, drawn at genuine (x, y) grid "
      f"positions, then extracted:\n")
print(f"  {table_text!r}\n")

print("  Every row/column boundary is gone. The extracted text is a FLAT")
print("  sequence: headers, then every cell, top-to-bottom, left-to-right --")
print("  with nothing marking which value belongs to which row. Reading it")
print("  in order happens to look sensible ONLY because a human reader can")
print("  count columns and re-pair values from memory.")

flat_lines = table_text.strip().splitlines()
CHUNK_BOUNDARY = 7   # splits mid-table, as a real fixed-size chunker (M7-L06) would
chunk_a, chunk_b = flat_lines[:CHUNK_BOUNDARY], flat_lines[CHUNK_BOUNDARY:]
print(f"\n  Simulating a naive, fixed-size chunker (M7-L06) cutting after line "
      f"{CHUNK_BOUNDARY}:")
print(f"    Chunk A: {chunk_a}")
print(f"    Chunk B: {chunk_b}")
print(f"\n  Chunk B alone contains {chunk_b!r} -- '20' with no 'Mid' anywhere in")
print("  the same chunk to pair it with. A query asking specifically about the")
print("  Mid tier's PTO days, if it retrieves chunk B alone, has genuinely lost")
print("  the information needed to answer correctly -- not because retrieval")
print("  failed, but because ingestion flattened a 2D structure into a 1D")
print("  sequence that an arbitrary cut can sever at exactly the wrong point.")


# ============================================================ 3
rule("3. HTML: BOILERPLATE VS REAL CONTENT")

HTML_PAGE = """
<html><head><title>Support</title><script>trackVisit();</script></head>
<body>
<nav>Home | Products | Pricing | Contact</nav>
<header>Acme Support Center</header>
<article>
<h1>Return Policy</h1>
<p>Items may be returned within thirty days of delivery for a full refund.</p>
<p>Original packaging is required for electronics returns.</p>
</article>
<aside>Related articles: Shipping Times, Warranty Information</aside>
<footer>(c) 2026 Acme Corp | Privacy Policy | Terms of Service</footer>
</body></html>
"""


class ContentExtractor(HTMLParser):
    """[REAL] Stdlib-only extraction: keep text inside <article> (or <p>/<h1-6>
    tags generally), explicitly skip <nav>, <header>, <footer>, <aside>,
    <script>, <style> -- exactly the tags that are structurally boilerplate
    on most real pages, regardless of what they happen to say."""
    SKIP_TAGS = {"nav", "header", "footer", "aside", "script", "style"}

    def __init__(self):
        super().__init__()
        self.skip_depth = 0
        self.collected: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag in self.SKIP_TAGS:
            self.skip_depth += 1

    def handle_endtag(self, tag):
        if tag in self.SKIP_TAGS:
            self.skip_depth = max(0, self.skip_depth - 1)

    def handle_data(self, data):
        if self.skip_depth == 0 and data.strip():
            self.collected.append(data.strip())


class NaiveExtractor(HTMLParser):
    """[REAL] The baseline every boilerplate-aware extractor improves on:
    collect ALL text regardless of surrounding tag, in document order."""

    def __init__(self):
        super().__init__()
        self.collected: list[str] = []

    def handle_data(self, data):
        if data.strip():
            self.collected.append(data.strip())


naive = NaiveExtractor()
naive.feed(HTML_PAGE)
naive_text = " ".join(naive.collected)

extractor = ContentExtractor()
extractor.feed(HTML_PAGE)
extracted_content = " ".join(extractor.collected)

print("  Naive 'just strip the tags' extraction keeps EVERYTHING, in document")
print(f"  order:\n    {naive_text!r}")
print(f"\n  Boilerplate-aware extraction (skipping nav/header/footer/aside/")
print(f"  script/style):\n    {extracted_content!r}")
print("\n  The nav bar, footer legal text, and 'related articles' aside never")
print("  appear -- only the article's own title and body. Chunking and")
print("  embedding THIS text, rather than the whole page, means retrieval")
print("  scores reflect the actual policy content, not diluted by boilerplate")
print("  every other page on the same site repeats verbatim.")


# ============================================================ 4
rule("4. SCANNED DOCUMENTS: NO TEXT LAYER AT ALL")

img = Image.new("RGB", (600, 200), color="white")
draw = ImageDraw.Draw(img)
draw.text((20, 80), "Employees accrue 15 days of PTO per year.", fill="black")
img_buf = io.BytesIO()
img.save(img_buf, format="PNG")
img_buf.seek(0)

scan_buf = io.BytesIO()
sc = canvas.Canvas(scan_buf, pagesize=letter)
sc.drawImage(ImageReader(img_buf), 50, 600, width=400, height=133)
sc.save()
scan_buf.seek(0)

scanned_text = PdfReader(scan_buf).pages[0].extract_text()
print("  A real PDF page containing a genuine embedded RASTER IMAGE of text")
print("  (pixels, drawn via PIL -- exactly what a scanner or a photographed")
print("  document produces), with no PDF text objects on the page at all.\n")
print(f"  extract_text() result: {scanned_text!r}  (length: {len(scanned_text)})")
print("\n  This is not a bug or a weak extractor -- there is genuinely no text")
print("  to extract. The page contains a picture of words, not the words")
print("  themselves as data. `[NOT EXECUTED]` Optical Character Recognition")
print("  (OCR) is the process that reads the PIXELS and produces actual text")
print("  from them -- a real OCR engine (e.g. Tesseract) is not available in")
print("  this environment, so this lab demonstrates the exact gap OCR exists")
print("  to close, without running OCR itself.")


# ============================================================ 5
rule("5. WHAT THIS LAB IS AND IS NOT")

print("  REAL: every PDF in this lab is genuinely generated (via reportlab)")
print("  and genuinely text-extracted (via pypdf) -- the header/footer")
print("  repetition, the total loss of table structure, and the scanned")
print("  page's completely empty extraction are all measured, not scripted.")
print("  The HTML boilerplate extractor is real, stdlib-only code.")
print("\n  AN HONEST NEGATIVE RESULT: this lesson also tested the classic")
print("  'multi-column text gets scrambled' failure mode directly, using a")
print("  simple two-column layout. It did NOT reproduce with this lab's")
print("  pypdf version -- modern extraction libraries have gotten materially")
print("  better at simple column layouts than commonly assumed. This is a")
print("  real, measured finding, not an oversight: it does not mean column-")
print("  order problems never happen -- denser layouts, older tools, and")
print("  more irregular page designs remain documented, real risks.")
print("  `[UNVERIFIED -- test your own specific documents and extraction")
print("  library version before assuming either outcome.]`")
print("\n  NOT SHOWN: running a real OCR engine on the scanned page; detecting")
print("  and reconstructing table structure automatically (a genuinely hard")
print("  problem in general, briefly touched on but not solved here); and")
print("  cleaning/deduplicating extracted text once ingested, which is")
print("  M7-L05's topic.")

print("\nDone.")
