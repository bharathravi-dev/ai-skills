"""M7-L08 lab -- metadata, identifiers, provenance and versioning: building a
real chunk-record schema on top of M7-L03's uniform document record; a real,
measured demonstration of a stale and a current policy chunk being equally
retrievable without version metadata, and version-aware filtering resolving
the ambiguity; why provenance metadata is what makes a citation verifiable at
all; and what happens to chunk identifiers when a document is re-chunked.

Deterministic. No API key, no network, no third-party dependencies.
Run:  python labs/m7/l08_metadata_provenance_versioning.py
"""

from __future__ import annotations

import hashlib
import sys
from dataclasses import dataclass, field

sys.stdout.reconfigure(encoding="utf-8")


def rule(title: str) -> None:
    print(f"\n{'=' * 76}\n{title}\n{'=' * 76}")


def content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:10]


# ============================================================ 1
rule("1. A CHUNK RECORD IS MORE THAN JUST TEXT")


@dataclass
class Chunk:
    chunk_id: str
    text: str
    source_uri: str
    source_document_id: str
    chunk_index: int
    document_version: int
    is_current: bool
    ingested_at: str
    metadata: dict = field(default_factory=dict)


def make_chunk(text, source_uri, doc_id, index, version, is_current, ts, **extra) -> Chunk:
    return Chunk(
        chunk_id=f"{doc_id}_v{version}_c{index}_{content_hash(text)}",
        text=text, source_uri=source_uri, source_document_id=doc_id,
        chunk_index=index, document_version=version, is_current=is_current,
        ingested_at=ts, metadata=extra,
    )


example = make_chunk(
    "Full time employees accrue fifteen days of PTO per year.",
    source_uri="hr-portal://policies/pto-policy", doc_id="pto-policy", index=0,
    version=1, is_current=False, ts="2026-01-15T09:00:00Z", department="HR",
)
print("  A chunk is not just its text -- it's text PLUS the context needed to")
print("  trust, cite, and manage it. One example record:\n")
for field_name in ["chunk_id", "text", "source_uri", "source_document_id",
                    "chunk_index", "document_version", "is_current", "ingested_at", "metadata"]:
    print(f"    {field_name}: {getattr(example, field_name)!r}")

print("\n  M7-L03 already established WHY a chunk needs a content-hash-based id")
print("  (idempotent re-ingestion, change detection). Everything else here --")
print("  source, version, currency, timestamp -- is what the rest of this")
print("  lesson demonstrates is load-bearing, not decorative.")


# ============================================================ 2
rule("2. WITHOUT VERSION METADATA, A STALE CHUNK IS INDISTINGUISHABLE FROM A CURRENT ONE")

POLICY_V1_TEXT = "Full time employees accrue fifteen days of PTO per year."
POLICY_V2_TEXT = "Full time employees accrue twenty days of PTO per year."

chunk_v1 = make_chunk(POLICY_V1_TEXT, "hr-portal://policies/pto-policy", "pto-policy",
                       0, version=1, is_current=False, ts="2026-01-15T09:00:00Z")
chunk_v2 = make_chunk(POLICY_V2_TEXT, "hr-portal://policies/pto-policy", "pto-policy",
                       0, version=2, is_current=True, ts="2026-06-01T09:00:00Z")

INDEX = [chunk_v1, chunk_v2]

WORD_VECTORS = {
    "full": [0.0, 0.0], "time": [0.0, 0.0], "employees": [0.0, 0.0], "accrue": [0.0, 0.0],
    "fifteen": [0.0, 0.0], "twenty": [0.0, 0.0], "days": [3.0, 0.0], "of": [0.0, 0.0],
    "pto": [3.0, 0.0], "per": [0.0, 0.0], "year": [0.0, 0.0], "how": [0.0, 0.0],
    "many": [0.0, 0.0], "do": [0.0, 0.0], "i": [0.0, 0.0], "get": [0.0, 0.0],
}


def pooled_vector(text: str) -> list[float]:
    words = text.lower().rstrip(".").split()
    vecs = [WORD_VECTORS.get(w, [0.0, 0.0]) for w in words]
    n = len(vecs) or 1
    return [sum(v[i] for v in vecs) / n for i in range(2)]


def cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = sum(x * x for x in a) ** 0.5
    nb = sum(x * x for x in b) ** 0.5
    return dot / (na * nb) if na and nb else 0.0


query = "how many PTO days do I get"
qv = pooled_vector(query)
scores = {c.chunk_id: cosine(qv, pooled_vector(c.text)) for c in INDEX}

print(f"  Query: {query!r}\n")
print("  Without filtering by version, BOTH chunks retrieve equally well:")
for c in INDEX:
    print(f"    {c.chunk_id}  (v{c.document_version}, current={c.is_current})  "
          f"score={scores[c.chunk_id]:.3f}  text={c.text!r}")

tie = scores[chunk_v1.chunk_id] == scores[chunk_v2.chunk_id]
print(f"\n  Scores are IDENTICAL: {tie}. Nothing about the TEXT or its SCORE")
print("  reveals which one is current -- 'fifteen' and 'twenty' are just words")
print("  to a retrieval system with no version awareness. A naive pipeline")
print("  could just as easily surface the STALE policy as the current one,")
print("  with no error, no warning, and a fully plausible-looking citation.")

current_only = [c for c in INDEX if c.is_current]
print(f"\n  Filtering to is_current=True BEFORE scoring/generation (M6-L09's")
print(f"  metadata-filtering pattern, applied to version currency):")
for c in current_only:
    print(f"    {c.chunk_id}  (v{c.document_version})  text={c.text!r}")
print(f"  Exactly {len(current_only)} chunk remains -- the ambiguity is resolved")
print("  structurally, by metadata, not by hoping retrieval happens to prefer")
print("  the right one.")


# ============================================================ 3
rule("3. PROVENANCE IS WHAT MAKES A CITATION VERIFIABLE")


def cite(chunk: Chunk) -> str:
    return (f'"{chunk.text}" (Source: {chunk.source_uri}, version {chunk.document_version}, '
            f"ingested {chunk.ingested_at})")


def cite_without_provenance(text: str) -> str:
    return f'"{text}" (source unknown)'


print("  The SAME retrieved text, cited two ways:\n")
print(f"  WITHOUT provenance metadata: {cite_without_provenance(chunk_v2.text)}")
print(f"  WITH provenance metadata:    {cite(chunk_v2)}")

print("\n  The first citation cannot be checked by a reader at all -- there is")
print("  no way to go verify it against the actual source, or to notice it")
print("  might be an old version. The second can be opened, checked against")
print("  the live document, and its version explicitly confirmed. M7-L12's")
print("  citation-quality lesson assumes metadata like this already exists;")
print("  this is where it has to come from.")


# ============================================================ 4
rule("4. IDENTIFIER STABILITY ACROSS RE-CHUNKING")

DOCUMENT = "Remote work requires manager approval. Expense reports are due within thirty days. PTO accrues yearly."


def position_based_chunks(text: str, size: int, doc_id: str) -> list[tuple[str, str]]:
    pieces = [text[i:i + size] for i in range(0, len(text), size)]
    return [(f"{doc_id}_pos{i}", p) for i, p in enumerate(pieces)]


def hash_based_chunks(text: str, size: int, doc_id: str) -> list[tuple[str, str]]:
    pieces = [text[i:i + size] for i in range(0, len(text), size)]
    return [(f"{doc_id}_{content_hash(p)}", p) for p in pieces]


ORIGINAL_SIZE, NEW_SIZE = 40, 35
pos_before = position_based_chunks(DOCUMENT, ORIGINAL_SIZE, "doc1")
pos_after = position_based_chunks(DOCUMENT, NEW_SIZE, "doc1")
hash_before = hash_based_chunks(DOCUMENT, ORIGINAL_SIZE, "doc1")
hash_after = hash_based_chunks(DOCUMENT, NEW_SIZE, "doc1")

print(f"  Re-chunking the SAME document after changing chunk size from "
      f"{ORIGINAL_SIZE} to {NEW_SIZE} characters (e.g. after adopting M7-L07's")
print("  recursive splitting instead of fixed-size):\n")

pos_before_map, pos_after_map = dict(pos_before), dict(pos_after)
print("  Position-based IDs:")
print(f"    Before: {pos_before}")
print(f"    After:  {pos_after}")
shared_pos_ids = set(pos_before_map) & set(pos_after_map)
silently_changed = [cid for cid in shared_pos_ids if pos_before_map[cid] != pos_after_map[cid]]
print(f"\n    {len(shared_pos_ids)} of {len(pos_before)} IDs are the SAME string before and after "
      f"({sorted(shared_pos_ids)}).")
print(f"    Of those, {len(silently_changed)} now point to DIFFERENT text than before:")
for cid in silently_changed:
    print(f"      {cid}:  before={pos_before_map[cid]!r}")
    print(f"      {' ' * len(cid)}   after ={pos_after_map[cid]!r}")
print("\n  This is the dangerous case: the ID looks stable (same string, both")
print("  times), but SILENTLY refers to different content after re-chunking --")
print("  a cache, a diff tool, or an incremental-update check keyed on this ID")
print("  (M7-L16's topic) could easily conclude 'nothing changed here' when")
print("  everything did. Position-based IDs encode WHERE a chunk was, not")
print("  WHAT it contains, so they cannot detect this at all.")

hash_before_map, hash_after_map = dict(hash_before), dict(hash_after)
shared_hash_ids = set(hash_before_map) & set(hash_after_map)
print(f"\n  Content-hash-based IDs: {len(shared_hash_ids)} shared between before and after.")
mismatched_hash = [cid for cid in shared_hash_ids if hash_before_map[cid] != hash_after_map[cid]]
print(f"  Of those, {len(mismatched_hash)} point to different text -- by construction, this can")
print("  never be more than 0: a hash-based ID is DERIVED from its text, so the")
print("  same ID appearing twice is a mathematical guarantee the text is")
print("  identical both times. Re-chunking at a different size changes almost")
print("  every chunk's exact boundaries, so most hash IDs churn here too -- but")
print("  unlike position-based IDs, a hash-based ID can NEVER silently point to")
print("  different content, which is the property M7-L16's incremental-update")
print("  and change-detection logic depends on.")


# ============================================================ 5
rule("5. METADATA FILTERING AT QUERY TIME")

CORPUS = [
    make_chunk("Remote work requires manager approval.", "hr://remote", "remote-policy",
               0, 1, True, "2026-02-01T00:00:00Z", department="HR"),
    make_chunk("Server maintenance windows are Tuesdays 2-4am.", "it://maintenance", "it-maintenance",
               0, 1, True, "2026-03-01T00:00:00Z", department="IT"),
    make_chunk("Expense reports are due within thirty days.", "hr://expenses", "expense-policy",
               0, 1, True, "2026-01-10T00:00:00Z", department="HR"),
]


def filter_by_department(chunks: list[Chunk], department: str) -> list[Chunk]:
    return [c for c in chunks if c.metadata.get("department") == department]


hr_only = filter_by_department(CORPUS, "HR")
print(f"  Full corpus: {len(CORPUS)} chunks across HR and IT.")
print(f"  Filtered to department=HR (M6-L09's metadata-filtering pattern, "
      f"reusing this lesson's schema): {len(hr_only)} chunks")
for c in hr_only:
    print(f"    {c.chunk_id}: {c.text!r}")
print("\n  None of this filtering logic is new -- M6-L09 already covered pre-")
print("  filtering vs. post-filtering mechanics in depth. What this lesson")
print("  adds is the SCHEMA (which fields exist, what they mean) that any of")
print("  M6-L09's filtering techniques actually filters ON.")


# ============================================================ 6
rule("6. WHAT THIS LAB IS AND IS NOT")

print("  REAL: every chunk record, hash, filter, and comparison in this lab")
print("  is genuinely constructed and computed; the version-ambiguity scores")
print("  (section 2) and the ID-stability comparison (section 4) are measured")
print("  on real, executed code, not asserted.")
print("\n  ILLUSTRATIVE: the chunk-record schema (chunk_id, source_uri, version,")
print("  is_current, etc.) is one reasonable design, not a universal standard --")
print("  real systems vary in exactly which fields they track.")
print("\n  NOT SHOWN: a real versioning workflow (how 'is_current' actually gets")
print("  flipped when a document changes -- M7-L16's topic); permission-aware")
print("  filtering specifically for access control (M7-L15's topic, distinct")
print("  from the department-tagging shown here); and citation rendering in")
print("  a real generated answer (M7-L12's topic).")

print("\nDone.")
