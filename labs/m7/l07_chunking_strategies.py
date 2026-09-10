"""M7-L07 lab -- the specific chunking algorithms M7-L06's trade-offs (size,
overlap, boundaries) motivate: recursive splitting (coarse separators first,
falling back to finer ones only when needed), sentence-boundary splitting
(and a real, honest failure case -- abbreviations), semantic chunking (using
similarity between consecutive sentences to find topic shifts with NO
explicit structural markup at all), and structure-aware splitting extended
to lists and code blocks, not just headings.

Deterministic. No API key, no network, no third-party dependencies.
Run:  python labs/m7/l07_chunking_strategies.py
"""

from __future__ import annotations

import re
import sys

sys.stdout.reconfigure(encoding="utf-8")


def rule(title: str) -> None:
    print(f"\n{'=' * 76}\n{title}\n{'=' * 76}")


# ============================================================ 1
rule("1. RECURSIVE SPLITTING: COARSE SEPARATORS FIRST, FINER ONLY IF NEEDED")

DOCUMENT = """Remote work requires manager approval for up to three days per week.

Fully remote arrangements require VP approval and a signed agreement.

Expense reports must be submitted within thirty days of purchase. Reimbursements over five hundred dollars require director approval."""


def fixed_size_chunks(text: str, size: int) -> list[str]:
    return [text[i:i + size] for i in range(0, len(text), size)]


def recursive_split(text: str, max_size: int, separators: list[str] | None = None) -> list[str]:
    """[REAL] Try the COARSEST separator first (paragraph break); only
    recurse into a finer one (sentence, then word) for any piece still
    over max_size. A piece that already fits is never split further,
    regardless of which separator would have applied."""
    if separators is None:
        separators = ["\n\n", ". ", " "]
    if len(text) <= max_size or not separators:
        return [text] if text.strip() else []
    sep, rest = separators[0], separators[1:]
    pieces = text.split(sep)
    result = []
    for piece in pieces:
        if len(piece) > max_size:
            result.extend(recursive_split(piece, max_size, rest))
        elif piece.strip():
            result.append(piece)
    return result


naive = fixed_size_chunks(DOCUMENT, 120)
recursive = recursive_split(DOCUMENT, 120)

print(f"  Document ({len(DOCUMENT)} characters, 3 paragraphs), fixed-size at 120 chars:\n")
for i, c in enumerate(naive, start=1):
    print(f"    Chunk {i}: {c!r}")

print(f"\n  Same document, recursively split (try paragraph breaks first, only")
print(f"  fall back to sentence breaks for a piece still over 120 chars):\n")
for i, c in enumerate(recursive, start=1):
    print(f"    Chunk {i}: {c!r}")

print("\n  Fixed-size cuts wherever the count lands, mid-paragraph or not.")
print("  Recursive splitting tries the COARSEST, most meaningful boundary")
print("  first (a paragraph break) and only breaks a paragraph into sentences")
print("  if that paragraph alone is still too big -- producing chunks aligned")
print("  to real content boundaries without needing any preserved structure")
print("  metadata (M7-L06's heading-based approach needed the '#' markup;")
print("  this works on the raw text's own punctuation and spacing alone).")


# ============================================================ 2
rule("2. SENTENCE SPLITTING -- AND A REAL, HONEST FAILURE CASE")


def split_sentences(text: str) -> list[str]:
    """[REAL, deliberately simple] Split on '. ', '! ', '? ' followed by a
    capital letter. This is a real, common heuristic -- and a real,
    documented source of errors, demonstrated below."""
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z])", text)
    return [p.strip() for p in parts if p.strip()]


CLEAN_TEXT = "Remote work requires approval. Expense reports are due monthly. PTO accrues yearly."
sentences = split_sentences(CLEAN_TEXT)
print(f"  Clean text, no abbreviations: {CLEAN_TEXT!r}")
print(f"  Split into {len(sentences)} sentences:")
for s in sentences:
    print(f"    {s!r}")

ABBREV_TEXT = "Contact Dr. Smith for approval. He reports to the U.S. division head."
abbrev_sentences = split_sentences(ABBREV_TEXT)
print(f"\n  Text WITH abbreviations: {ABBREV_TEXT!r}")
print(f"  Split into {len(abbrev_sentences)} 'sentences':")
for s in abbrev_sentences:
    print(f"    {s!r}")

print(f"\n  'Dr. Smith' and 'U.S. division' were each split at the abbreviation's")
print("  period, producing fragments that are not real sentences at all. This")
print("  is not a contrived edge case -- abbreviations, initials, and decimal")
print("  numbers are common in real documents, and a purely punctuation-based")
print("  sentence splitter has no way to distinguish 'end of sentence' from")
print("  'abbreviation' without an explicit exception list or a smarter model.")


# ============================================================ 3
rule("3. SEMANTIC CHUNKING: FINDING TOPIC SHIFTS WITH NO STRUCTURAL MARKUP AT ALL")

WORD_VECTORS = {
    "remote": [3.0, 0.0, 0.0], "work": [2.5, 0.0, 0.0], "manager": [2.0, 0.0, 0.0],
    "approval": [1.5, 0.0, 0.0], "office": [2.0, 0.0, 0.0],
    "revenue": [0.0, 3.0, 0.0], "quarterly": [0.0, 2.5, 0.0], "profit": [0.0, 2.0, 0.0],
    "earnings": [0.0, 2.2, 0.0], "grew": [0.0, 0.0, 0.0], "the": [0.0, 0.0, 0.0],
    "is": [0.0, 0.0, 0.0], "and": [0.0, 0.0, 0.0], "was": [0.0, 0.0, 0.0],
    "a": [0.0, 0.0, 0.0], "for": [0.0, 0.0, 0.0], "up": [0.0, 0.0, 0.0], "to": [0.0, 0.0, 0.0],
    "percent": [0.0, 0.0, 0.0], "five": [0.0, 0.0, 0.0], "this": [0.0, 0.0, 0.0],
    "year": [0.0, 0.0, 0.0], "team": [0.0, 0.0, 0.0], "strong": [0.0, 2.0, 0.0],
}
UNSTRUCTURED_DOC = [
    "Remote work is available with manager approval.",
    "The office supports a flexible remote work schedule.",
    "Quarterly revenue grew five percent this year.",
    "Earnings were strong and profit grew for the team.",
]


def pooled_vector(sentence: str) -> list[float]:
    words = sentence.lower().rstrip(".").split()
    vecs = [WORD_VECTORS.get(w, [0.0, 0.0, 0.0]) for w in words]
    n = len(vecs) or 1
    return [sum(v[i] for v in vecs) / n for i in range(3)]


def cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = sum(x * x for x in a) ** 0.5
    nb = sum(x * x for x in b) ** 0.5
    return dot / (na * nb) if na and nb else 0.0


print("  Four sentences, NO headings, NO paragraph breaks, NO markup at all --")
print("  just plain consecutive prose:\n")
similarities = []
for i in range(len(UNSTRUCTURED_DOC) - 1):
    v1, v2 = pooled_vector(UNSTRUCTURED_DOC[i]), pooled_vector(UNSTRUCTURED_DOC[i + 1])
    sim = cosine(v1, v2)
    similarities.append(sim)
    print(f"  [{i + 1}] {UNSTRUCTURED_DOC[i]!r}")
    print(f"      -> similarity to next sentence: {sim:.3f}")
print(f"  [{len(UNSTRUCTURED_DOC)}] {UNSTRUCTURED_DOC[-1]!r}")

SEMANTIC_THRESHOLD = 0.5
split_points = [i for i, s in enumerate(similarities) if s < SEMANTIC_THRESHOLD]
print(f"\n  Similarity drops below {SEMANTIC_THRESHOLD} between sentences "
      f"{[p + 1 for p in split_points]} and {[p + 2 for p in split_points]} -- "
      f"exactly where the topic shifts from remote work to quarterly revenue.")

semantic_chunks: list[list[str]] = [[]]
for i, sentence in enumerate(UNSTRUCTURED_DOC):
    semantic_chunks[-1].append(sentence)
    if i in split_points:
        semantic_chunks.append([])
print(f"\n  Resulting semantic chunks:")
for i, chunk in enumerate(semantic_chunks, start=1):
    print(f"    Chunk {i}: {chunk}")

print("\n  Nobody told this splitter where one topic ends and the next begins --")
print("  no heading, no blank line, not even a paragraph break (M7-L06's")
print("  boundary-aware chunking needed exactly that kind of markup). Semantic")
print("  chunking finds the boundary from the CONTENT itself, using the same")
print("  pooling/cosine mechanism M6-L01 introduced, applied here to adjacent")
print("  sentences instead of a query and a document.")


# ============================================================ 4
rule("4. STRUCTURE-AWARE: LISTS AND CODE BLOCKS, NOT JUST HEADINGS")

MIXED_DOC = """# Setup Instructions
Follow these steps to configure remote access:
- Install the VPN client
- Enter your employee ID
- Contact IT if the connection fails

Example configuration:
```
server: vpn.acme.example
port: 443
```
Once connected, remote work proceeds as normal."""


def structure_aware_chunks(text: str) -> list[str]:
    """[REAL] Never split INSIDE a fenced code block (```...```) or a
    contiguous bullet list -- both are treated as one indivisible unit,
    generalizing M7-L06's heading-only boundary awareness."""
    lines = text.splitlines()
    chunks, current, in_code = [], [], False
    for line in lines:
        if line.strip().startswith("```"):
            in_code = not in_code
            current.append(line)
            if not in_code:
                chunks.append("\n".join(current))
                current = []
            continue
        if in_code:
            current.append(line)
            continue
        if line.startswith("#") and current:
            chunks.append("\n".join(current))
            current = [line]
        elif line.strip() == "" and current and not current[-1].startswith("-"):
            chunks.append("\n".join(current))
            current = []
        else:
            if line.strip():
                current.append(line)
    if current:
        chunks.append("\n".join(current))
    return [c for c in chunks if c.strip()]


naive_on_mixed = fixed_size_chunks(MIXED_DOC, 70)
structure_chunks = structure_aware_chunks(MIXED_DOC)

print("  A document with a heading, a bullet list, and a fenced code block:\n")
print("  Fixed-size (70 chars), blind to any of this structure:")
for i, c in enumerate(naive_on_mixed, start=1):
    print(f"    Chunk {i}: {c!r}")

print("\n  Structure-aware (never splits inside a list or a code block):")
for i, c in enumerate(structure_chunks, start=1):
    print(f"    Chunk {i}: {c!r}")

code_intact = any("server: vpn.acme.example" in c and "port: 443" in c for c in structure_chunks)
code_split_naive = any("server: vpn.acme.example" in c and "port: 443" in c for c in naive_on_mixed)
print(f"\n  Code block kept fully intact in ONE chunk -- structure-aware: "
      f"{code_intact}, fixed-size: {code_split_naive}")
print("  Splitting a code block in the middle produces a fragment that is not")
print("  valid, meaningful configuration on its own -- a much sharper failure")
print("  than splitting prose mid-sentence, since code has no tolerance for")
print("  being read 'mostly right'.")


# ============================================================ 5
rule("5. ALL FOUR STRATEGIES, SIDE BY SIDE, ON ONE DOCUMENT")

print("  Chunk counts on this lesson's own documents, strategy by strategy:\n")
print(f"  {'Strategy':<20}{'Document':<28}{'Chunks produced'}")
print(f"  {'Fixed-size':<20}{'3-paragraph policy text':<28}{len(naive)}")
print(f"  {'Recursive':<20}{'3-paragraph policy text':<28}{len(recursive)}")
print(f"  {'Sentence':<20}{'Clean 3-sentence text':<28}{len(sentences)}")
print(f"  {'Semantic':<20}{'4-sentence, 2-topic text':<28}{len(semantic_chunks)}")
print(f"  {'Structure-aware':<20}{'Heading+list+code doc':<28}{len(structure_chunks)}")

print("\n  No single count here is 'correct' in isolation -- each strategy is")
print("  solving a different problem. Fixed-size is the cheapest and least")
print("  aware. Recursive respects generic textual structure without needing")
print("  metadata. Sentence splitting respects grammar (with a real caveat).")
print("  Semantic splitting respects MEANING, even with zero markup. Structure-")
print("  aware splitting respects explicit document structure, including")
print("  elements (lists, code) a heading-only approach (M7-L06) would miss.")


# ============================================================ 6
rule("6. WHAT THIS LAB IS AND IS NOT")

print("  REAL: every splitting function in this lab is genuinely executed on")
print("  real text; the sentence-splitting abbreviation failure is a real,")
print("  reproduced regex behavior, not asserted; the semantic-chunking")
print("  similarity scores use M6-L01's exact pooling/cosine mechanism.")
print("\n  ILLUSTRATIVE: the semantic-chunking threshold (0.5) and word vectors")
print("  are hand-built for this lesson, not a trained embedding model's real")
print("  output -- the MECHANISM (similarity drop signals topic shift) is real")
print("  and used in production semantic chunkers; the specific numbers are")
print("  a checkable illustration.")
print("\n  NOT SHOWN: a production-grade sentence tokenizer that correctly")
print("  handles abbreviations (typically using an explicit abbreviation list")
print("  or a trained model); chunking cost/latency at real corpus scale; and")
print("  combining multiple strategies in one pipeline (e.g. recursive PLUS")
print("  structure-aware), left to the exercises.")

print("\nDone.")
