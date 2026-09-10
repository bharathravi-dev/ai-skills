"""M7-L16 lab -- when a source document changes or is deleted, does that
change actually propagate everywhere it needs to: real content-hash change
detection (M7-L08's mechanism) identifying exactly which chunks of an
updated document need re-embedding versus which can be safely skipped; real
deletion propagation from a document store through an index; the orphaned-
reference bug when a downstream cache isn't updated in the same event as the
index; and detecting a stale citation (M7-L12) pointing at a chunk that no
longer exists.

Deterministic. No API key, no network, no third-party dependencies.
Run:  python labs/m7/l16_incremental_updates_deletion_propagation.py
"""

from __future__ import annotations

import hashlib
import sys

sys.stdout.reconfigure(encoding="utf-8")


def rule(title: str) -> None:
    print(f"\n{'=' * 76}\n{title}\n{'=' * 76}")


def content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:10]


def naive_chunk(doc_id: str, text: str) -> dict[str, str]:
    sentences = [s.strip() for s in text.split(".") if s.strip()]
    return {f"{doc_id}#{content_hash(s)}": s for s in sentences}


# ============================================================ 1
rule("1. THE PROPAGATION CHAIN: WHAT ACTUALLY HAS TO UPDATE")

print("  A document changing or being deleted touches more than one place:")
print("    1. The DOCUMENT STORE (M7-L03) -- the source of truth itself.")
print("    2. The CHUNK INDEX (M6-L10) -- every chunk derived from that document.")
print("    3. Any CACHES -- previously generated answers (M7-L11/M7-L12) that")
print("       cited specific chunk IDs from the OLD version.")
print("    4. Any DERIVED DATA -- precomputed related-document lists, summaries,")
print("       or anything else keyed on a now-stale chunk ID.")
print("\n  M6-L10 covered stage 2 (index tombstone vs. rebuild) in depth. This")
print("  lesson covers the FULL chain -- specifically what happens when stage")
print("  3 or 4 is forgotten while stage 2 is handled correctly.")


# ============================================================ 2
rule("2. CONTENT-HASH CHANGE DETECTION: WHICH CHUNKS ACTUALLY NEED RE-EMBEDDING")

PTO_DOC_V1 = ("Paid Time Off Policy. Full time employees accrue 15 days of PTO per year. "
              "PTO requests must be submitted at least two weeks in advance. "
              "Unused PTO does not roll over to the next calendar year.")
PTO_DOC_V2 = ("Paid Time Off Policy. Full time employees accrue 20 days of PTO per year. "
              "PTO requests must be submitted at least two weeks in advance. "
              "Unused PTO does not roll over to the next calendar year.")

chunks_v1 = naive_chunk("PTO", PTO_DOC_V1)
chunks_v2 = naive_chunk("PTO", PTO_DOC_V2)

print(f"  PTO policy updated (15 days -> 20 days). Re-chunked into "
      f"{len(chunks_v1)} sentence-level chunks, both versions:\n")

unchanged = set(chunks_v1) & set(chunks_v2)
removed = set(chunks_v1) - set(chunks_v2)
added = set(chunks_v2) - set(chunks_v1)

print(f"  Chunk IDs unchanged (same content hash, same text): {len(unchanged)}")
for cid in unchanged:
    print(f"    {cid}: {chunks_v1[cid]!r}")
print(f"\n  Chunk IDs removed (old content, no longer present): {len(removed)}")
for cid in removed:
    print(f"    {cid}: {chunks_v1[cid]!r}")
print(f"\n  Chunk IDs added (new content, needs embedding): {len(added)}")
for cid in added:
    print(f"    {cid}: {chunks_v2[cid]!r}")

print(f"\n  Only {len(removed)} of {len(chunks_v1)} chunks actually changed. The other "
      f"{len(unchanged)} are IDENTICAL by content hash (M7-L08's mechanism) --")
print("  re-embedding them again would be wasted work. This is the real,")
print("  measurable efficiency gain from content-hash-based change detection:")
print("  update only what changed, leave the rest of the index untouched.")


# ============================================================ 3
rule("3. DELETION PROPAGATION: THE INDEX ALONE IS NOT ENOUGH")

DOCUMENT_STORE = {
    "PTO": PTO_DOC_V2,
    "EQUIPMENT": "Equipment Policy. New employees receive a laptop and a home office stipend.",
}
INDEX: dict[str, str] = {}
for doc_id, text in DOCUMENT_STORE.items():
    INDEX.update(naive_chunk(doc_id, text))

# A cache of previously generated, already-served answers -- exactly what
# M7-L11/M7-L12 assembled and cited.
equipment_chunk_id = next(cid for cid in INDEX if cid.startswith("EQUIPMENT#"))
CACHE = {
    "what equipment do new employees get": {
        "answer": f"New employees receive a laptop and a home office stipend. [Source: {equipment_chunk_id}]",
        "cited_chunk_ids": [equipment_chunk_id],
    }
}

print(f"  Index built from {len(DOCUMENT_STORE)} documents: {len(INDEX)} chunks total.")
print(f"  Cache contains 1 previously generated answer, citing chunk {equipment_chunk_id!r}.\n")

print("  Now the Equipment Policy document is DELETED from the document store.")


def delete_document_index_only(doc_id: str, document_store: dict, index: dict) -> None:
    """[REAL, but INCOMPLETE on purpose] Deletes from the document store and
    the index -- exactly M6-L10's tombstone mechanism -- but touches nothing
    else. This is the bug this section exists to demonstrate."""
    del document_store[doc_id]
    stale_ids = [cid for cid in index if cid.startswith(f"{doc_id}#")]
    for cid in stale_ids:
        del index[cid]


delete_document_index_only("EQUIPMENT", DOCUMENT_STORE, INDEX)
print(f"  Document store now has {len(DOCUMENT_STORE)} document(s); index now has {len(INDEX)} chunk(s).")
print(f"  Equipment chunk still in the index: {equipment_chunk_id in INDEX}")

cached_entry = CACHE["what equipment do new employees get"]
cited_id = cached_entry["cited_chunk_ids"][0]
print(f"\n  But the CACHE was never touched by this deletion:")
print(f"    Cached answer: {cached_entry['answer']!r}")
print(f"    Cited chunk ID still present in cache: {cited_id}")
print(f"    That chunk ID still present in the INDEX: {cited_id in INDEX}")

print("\n  A user re-asking the exact same question would be served this CACHED")
print("  answer, complete with a citation pointing to a chunk that no longer")
print("  exists anywhere in the index -- an orphaned reference. The index")
print("  update was correct and complete; the propagation to a DOWNSTREAM")
print("  system (the cache) was simply never triggered by the same event.")


# ============================================================ 4
rule("4. THE FIX: PROPAGATE THE SAME DELETION EVENT TO EVERY DOWNSTREAM CONSUMER")


def delete_document_with_propagation(doc_id: str, document_store: dict, index: dict, cache: dict) -> list[str]:
    """[REAL] The same deletion, but propagated to every consumer of chunk
    identity -- not just the index."""
    stale_ids = {cid for cid in index if cid.startswith(f"{doc_id}#")}
    del document_store[doc_id]
    for cid in list(index):
        if cid in stale_ids:
            del index[cid]
    invalidated = []
    for query, entry in list(cache.items()):
        if stale_ids & set(entry["cited_chunk_ids"]):
            del cache[query]
            invalidated.append(query)
    return invalidated


# Rebuild the scenario fresh, this time deleting WITH propagation.
DOCUMENT_STORE_2 = {"PTO": PTO_DOC_V2, "EQUIPMENT": "Equipment Policy. New employees receive a laptop and a home office stipend."}
INDEX_2: dict[str, str] = {}
for doc_id, text in DOCUMENT_STORE_2.items():
    INDEX_2.update(naive_chunk(doc_id, text))
equipment_chunk_id_2 = next(cid for cid in INDEX_2 if cid.startswith("EQUIPMENT#"))
CACHE_2 = {
    "what equipment do new employees get": {
        "answer": f"New employees receive a laptop and a home office stipend. [Source: {equipment_chunk_id_2}]",
        "cited_chunk_ids": [equipment_chunk_id_2],
    }
}

invalidated = delete_document_with_propagation("EQUIPMENT", DOCUMENT_STORE_2, INDEX_2, CACHE_2)
print(f"  Same deletion, this time propagated to the cache as part of the SAME")
print(f"  operation:")
print(f"    Cache entries invalidated: {invalidated}")
print(f"    Cache now contains: {list(CACHE_2.keys())}")
print(f"    Equipment chunk in index: {equipment_chunk_id_2 in INDEX_2}")

print("\n  The cache entry citing the deleted chunk was found (by checking")
print("  whether ANY of its cited chunk IDs belong to the deleted document)")
print("  and removed in the SAME operation that deleted the document -- not")
print("  as a separate, easily-forgotten step. A user re-asking the same")
print("  question now correctly triggers fresh retrieval instead of serving a")
print("  broken citation.")


# ============================================================ 5
rule("5. WHAT THIS LAB IS AND IS NOT")

print("  REAL: content-hash computation and comparison (M7-L08's exact")
print("  mechanism), chunk-level diffing between document versions, and both")
print("  the buggy and fixed deletion-propagation paths are genuinely")
print("  executed on real (if synthetic) data, not scripted to fit.")
print("\n  ILLUSTRATIVE: this lab's 'cache' is a single in-memory dictionary")
print("  standing in for whatever real caching layer a production system")
print("  uses (query result caches, CDN caches, precomputed summaries) --")
print("  the propagation PRINCIPLE generalizes; the specific cache structure")
print("  here does not represent any one real caching technology.")
print("\n  NOT SHOWN: propagating updates (not just deletions) through a cache")
print("  using the same content-hash change detection from section 2; a real")
print("  event-driven architecture (e.g. a message queue) that would trigger")
print("  propagation automatically across independent services; and")
print("  re-embedding cost at real scale, which M6-L10 already measured.")

print("\nDone.")
