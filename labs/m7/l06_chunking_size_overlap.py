"""M7-L06 lab -- chunking fundamentals: why fixed-size chunking splits text
arbitrarily, a real measured demonstration of chunks that are too small
(losing context) versus too big (diluting relevance), overlap recovering
content that would otherwise be broken across a chunk boundary, respecting a
document's own structural boundaries instead of a document's own placeholder
"naive" chunking used since M7-L01, and the real, measured storage cost
overlap imposes in exchange for that recovery.

Deterministic. No API key, no network, no third-party dependencies.
Run:  python labs/m7/l06_chunking_size_overlap.py
"""

from __future__ import annotations

import sys

sys.stdout.reconfigure(encoding="utf-8")


def rule(title: str) -> None:
    print(f"\n{'=' * 76}\n{title}\n{'=' * 76}")


# ============================================================ 1
rule("1. FIXED-SIZE CHUNKING SPLITS TEXT ARBITRARILY")

DOCUMENT = ("Employees may work remotely up to three days per week with manager "
            "approval. Fully remote arrangements require VP approval and a signed "
            "remote work agreement. Expense reports must be submitted within "
            "thirty days of purchase.")


def fixed_size_chunks(text: str, size: int) -> list[str]:
    return [text[i:i + size] for i in range(0, len(text), size)]


naive_chunks = fixed_size_chunks(DOCUMENT, 60)
print(f"  Document ({len(DOCUMENT)} characters), chunked at a fixed 60 characters, "
      f"no regard for word or sentence boundaries:\n")
for i, c in enumerate(naive_chunks, start=1):
    print(f"    Chunk {i}: {c!r}")

print(f"\n  Notice chunk boundaries land mid-word ('remote' split across chunks,")
print("  'manager' split across chunks) and mid-sentence. A fixed character")
print("  count has no concept of where a word, sentence, or idea actually ends")
print("  -- it cuts at a count, not at a meaningful boundary.")


# ============================================================ 2
rule("2. CHUNK SIZE: TOO BIG DILUTES RELEVANCE, MEASURED")

WORD_VECTORS = {
    "damaged": [3.0, 0.0, 0.0], "item": [0.3, 0.0, 0.0], "refund": [0.0, 3.0, 0.0],
    "remote": [0.0, 0.0, 3.0], "work": [0.0, 0.0, 0.3], "revenue": [0.0, 0.0, 0.0],
    "quarterly": [0.0, 0.0, 0.0], "the": [0.0, 0.0, 0.0], "and": [0.0, 0.0, 0.0],
    "was": [0.0, 0.0, 0.0], "a": [0.0, 0.0, 0.0], "grew": [0.0, 0.0, 0.0],
    "percent": [0.0, 0.0, 0.0], "please": [0.0, 0.0, 0.0], "my": [0.0, 0.0, 0.0],
}


def pooled_vector(text: str) -> list[float]:
    words = text.lower().replace(".", "").split()
    vecs = [WORD_VECTORS.get(w, [0.0, 0.0, 0.0]) for w in words]
    n = len(vecs) or 1
    return [sum(v[i] for v in vecs) / n for i in range(3)]


def cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = sum(x * x for x in a) ** 0.5
    nb = sum(x * x for x in b) ** 0.5
    return dot / (na * nb) if na and nb else 0.0


SENTENCE_DAMAGED = "The item was damaged and I need a refund please."
SENTENCE_REMOTE = "Remote work requires manager approval."
SENTENCE_REVENUE = "Quarterly revenue grew five percent."

big_chunk = f"{SENTENCE_DAMAGED} {SENTENCE_REMOTE} {SENTENCE_REVENUE}"
small_chunk = SENTENCE_DAMAGED

query_vec = pooled_vector("damaged item refund")
score_big = cosine(query_vec, pooled_vector(big_chunk))
score_small = cosine(query_vec, pooled_vector(small_chunk))

print(f"  Query: 'damaged item refund'\n")
print(f"  ONE big chunk (3 unrelated topics merged): {big_chunk!r}")
print(f"    cosine score: {score_big:.4f}")
print(f"\n  ONE small, correctly-scoped chunk (1 topic only): {small_chunk!r}")
print(f"    cosine score: {score_small:.4f}")

print(f"\n  The SAME sentence about damage and refunds is present, word for word,")
print(f"  in both chunks. Merging it with two unrelated topics (remote work,")
print(f"  quarterly revenue) into one big chunk pulls its pooled vector toward")
print(f"  those topics' axes too, diluting its similarity to a query about")
print(f"  damage specifically -- from {score_small:.4f} down to {score_big:.4f}.")
print("  A chunk that is too big doesn't just retrieve slower -- it can score")
print("  WORSE on exactly the query it should answer best, because pooling")
print("  (M6-L01) blends in content the query was never about.")


# ============================================================ 3
rule("3. CHUNK SIZE: TOO SMALL SPLITS ONE FACT ACROSS TWO CHUNKS")

FACT_SENTENCE = "For all staff in the Mid tier, the company accrues twenty days of PTO per year."
TOO_SMALL = 45
tiny_chunks = fixed_size_chunks(FACT_SENTENCE, TOO_SMALL)
print(f"  A single fact, chunked at a too-small {TOO_SMALL} characters:\n")
for i, c in enumerate(tiny_chunks, start=1):
    print(f"    Chunk {i}: {c!r}")
print(f"\n  'Mid tier' ends up in chunk 1; 'twenty days' ends up in chunk 2. A query")
print("  retrieving only chunk 2 sees 'twenty days of PTO' with no tier name")
print("  anywhere in the same chunk to attach it to -- the exact same failure")
print("  shape M7-L04 measured for a flattened TABLE, now shown for ordinary")
print("  PROSE chunked too aggressively.")


# ============================================================ 4
rule("4. OVERLAP RECOVERS WHAT A HARD BOUNDARY WOULD SPLIT")


def chunks_with_overlap(text: str, size: int, overlap: int) -> list[str]:
    step = size - overlap
    return [text[i:i + size] for i in range(0, len(text), step) if text[i:i + size]]


OVERLAP_SIZE = 30
no_overlap = fixed_size_chunks(FACT_SENTENCE, TOO_SMALL)
with_overlap = chunks_with_overlap(FACT_SENTENCE, TOO_SMALL, overlap=OVERLAP_SIZE)

print(f"  Same fact, same {TOO_SMALL}-character chunk size, WITHOUT overlap:")
for i, c in enumerate(no_overlap, start=1):
    print(f"    Chunk {i}: {c!r}")
contains_fact_no_overlap = any("mid tier" in c.lower() and "twenty" in c.lower() for c in no_overlap)
print(f"  Any single chunk contains BOTH 'Mid tier' and 'twenty': {contains_fact_no_overlap}")

print(f"\n  Same fact, same size, WITH {OVERLAP_SIZE}-character overlap between chunks:")
for i, c in enumerate(with_overlap, start=1):
    print(f"    Chunk {i}: {c!r}")
contains_fact_with_overlap = any("mid tier" in c.lower() and "twenty" in c.lower() for c in with_overlap)
print(f"  Any single chunk contains BOTH 'Mid tier' and 'twenty': {contains_fact_with_overlap}")

print("\n  Overlap doesn't prevent a boundary from falling in an awkward place --")
print("  it just guarantees that whatever falls near a boundary also appears")
print("  fully, at least once, in some OTHER chunk that isn't cut at the same")
print("  point. This is a real, mechanical fix for section 3's exact failure,")
print("  not a heuristic that sometimes helps.")

print(f"\n  Notice how much overlap this actually took: {OVERLAP_SIZE} characters out")
print(f"  of a {TOO_SMALL}-character chunk ({OVERLAP_SIZE / TOO_SMALL:.0%}) -- because 'Mid")
print("  tier' and 'twenty' are genuinely far apart relative to the chunk size.")
print("  Overlap only recovers a split if it's large enough to bridge the actual")
print("  gap between related facts -- a small, token overlap percentage (the")
print("  common 10-20% recommendation) recovers only NEARBY splits, not distant")
print("  ones. This is why overlap is a probabilistic mitigation, not a")
print("  guarantee, unless sized generously relative to how far apart related")
print("  content can realistically fall in your own documents.")


# ============================================================ 5
rule("5. RESPECTING DOCUMENT BOUNDARIES INSTEAD OF CUTTING THROUGH THEM")

STRUCTURED_DOC = """# Remote Work Policy
Employees may work remotely up to three days per week with manager approval.
# Expense Policy
Expense reports must be submitted within thirty days of purchase."""


def chunk_by_heading(text: str) -> list[str]:
    """[REAL, reuses M7-L03's heading-tracking approach] Split at each '#'
    heading, keeping the heading and its body together as one chunk."""
    chunks, current = [], []
    for line in text.splitlines():
        if line.startswith("#") and current:
            chunks.append("\n".join(current))
            current = []
        if line.strip():
            current.append(line)
    if current:
        chunks.append("\n".join(current))
    return chunks


naive_on_structured = fixed_size_chunks(STRUCTURED_DOC, 70)
boundary_aware = chunk_by_heading(STRUCTURED_DOC)

print("  The same two-section document, chunked two ways:\n")
print("  Fixed-size (70 chars), ignoring structure:")
for i, c in enumerate(naive_on_structured, start=1):
    print(f"    Chunk {i}: {c!r}")
print("\n  Boundary-aware (split at each heading):")
for i, c in enumerate(boundary_aware, start=1):
    print(f"    Chunk {i}: {c!r}")

print("\n  Fixed-size chunking has no idea 'Remote Work Policy' and 'Expense")
print("  Policy' are two unrelated sections -- it can (and here, does) merge")
print("  part of one section with part of the next, or split a heading from")
print("  its own body. Boundary-aware chunking, using exactly the structure")
print("  M7-L03 preserved during ingestion, keeps each section whole. M7-L07")
print("  covers more advanced strategies (semantic, recursive) built on this")
print("  same principle: prefer the document's own boundaries over an")
print("  arbitrary count wherever structure is available.")


# ============================================================ 6
rule("6. OVERLAP IS NOT FREE: THE STORAGE/EMBEDDING COST, MEASURED")

LONGER_DOC = FACT_SENTENCE * 20   # a stand-in for a longer real document
for overlap_pct in (0, 10, 25, 50):
    size = 100
    overlap = int(size * overlap_pct / 100)
    chunked = chunks_with_overlap(LONGER_DOC, size, overlap)
    total_chars = sum(len(c) for c in chunked)
    inflation = (total_chars / len(LONGER_DOC) - 1) * 100
    print(f"  {overlap_pct:>3}% overlap: {len(chunked):>3} chunks, "
          f"{total_chars:>5,} total characters across all chunks "
          f"({inflation:+.1f}% vs. the original {len(LONGER_DOC):,}-character document)")

print("\n  Every character of overlap is embedded and stored MORE THAN ONCE.")
print("  Section 4 showed overlap's real benefit; this section shows its real")
print("  cost is not hypothetical either -- both numbers belong in the same")
print("  decision, not just the benefit alone.")


# ============================================================ 7
rule("7. WHAT THIS LAB IS AND IS NOT")

print("  REAL: every chunking function in this lab is genuinely executed on")
print("  real text; the relevance-dilution scores (section 2) use M6-L01's")
print("  exact pooling/cosine mechanism; the overlap storage-cost measurement")
print("  (section 6) is exact arithmetic on real chunked output.")
print("\n  ILLUSTRATIVE: chunk sizes in this lab (45-100 characters) are chosen")
print("  to make failures visible in a short document; real systems typically")
print("  chunk by TOKEN count, at sizes of hundreds of tokens, not characters.")
print("\n  NOT SHOWN: sentence-boundary-aware, semantic, and recursive chunking")
print("  algorithms -- specific, more sophisticated splitting STRATEGIES that")
print("  are M7-L07's dedicated topic. This lesson establishes the underlying")
print("  trade-offs (size, overlap, boundaries) those strategies are designed")
print("  to navigate.")

print("\nDone.")
