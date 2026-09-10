"""M6-L02 lab -- storage cost by dimension, why "same dimension count" does
not mean "compatible embeddings", and when cosine and Euclidean distance
silently disagree.

Section 1 is real arithmetic on stated, real-world embedding dimension
counts. Section 2 hand-builds two small, deliberately DIFFERENT toy
embedding spaces at the SAME dimensionality, to make model-incompatibility
concrete rather than asserted. Section 3 is exact vector arithmetic
demonstrating a real, provable identity: for unit vectors, ranking by
Euclidean distance and ranking by cosine similarity are mathematically
equivalent -- and that equivalence breaks the moment magnitudes vary.

Deterministic. No API key, no network, no model download.
Run:  python labs/m6/l02_embedding_dimensions.py
"""

from __future__ import annotations

import numpy as np


def rule(title: str) -> None:
    print(f"\n{'=' * 76}\n{title}\n{'=' * 76}")


def cosine(a, b) -> float:
    a, b = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    na, nb = np.linalg.norm(a), np.linalg.norm(b)
    if na == 0 or nb == 0:
        return 0.0
    return float(np.dot(a, b) / (na * nb))


def euclidean(a, b) -> float:
    return float(np.linalg.norm(np.asarray(a, dtype=float) - np.asarray(b, dtype=float)))


# ============================================================ 1
rule("1. STORAGE COST SCALES WITH DIMENSION COUNT")

CORPUS_SIZE = 1_000_000
DIMENSIONS = [256, 384, 768, 1536, 3072]      # real, common real-world sizes
DTYPES = {"float32": 4, "float16": 2, "int8 (quantized)": 1}

print(f"  A {CORPUS_SIZE:,}-document corpus. Storage = dimensions x bytes/value x count.\n")
print(f"  {'dimensions':>11}", end="")
for dtype_name in DTYPES:
    print(f"{dtype_name:>20}", end="")
print()
for dims in DIMENSIONS:
    print(f"  {dims:>11}", end="")
    for dtype_name, nbytes in DTYPES.items():
        total_gb = dims * nbytes * CORPUS_SIZE / 1e9
        print(f"{total_gb:>17.2f} GB", end="")
    print()

ratio = DIMENSIONS[-1] / DIMENSIONS[0]
print(f"\n  Going from {DIMENSIONS[0]} to {DIMENSIONS[-1]} dimensions is a "
      f"{ratio:.0f}x storage multiplier, at the SAME corpus")
print("  size and the SAME numeric precision. More dimensions can capture")
print("  more nuance, but it is never free -- storage, memory, and the cost")
print("  of every downstream similarity computation all scale with it.")
print("  int8 quantisation recovers most of the float32-vs-float16 saving")
print("  again without dropping dimensions at all -- a separate lever.")


# ============================================================ 2
rule("2. SAME DIMENSION COUNT DOES NOT MEAN COMPATIBLE SPACES")

# Two toy "embedding models" -- same 4 axes in name, but MODEL B's training
# (here: hand assignment) landed on a genuinely different coordinate system.
# This is the point: nothing about the SHAPE of the vectors reveals this.
MODEL_A = {
    "refund":  [3.0, 0.0, 0.0, 0.0],
    "invoice": [2.8, 0.2, 0.0, 0.0],
    "delivery": [0.0, 3.0, 0.0, 0.0],
    "tracking": [0.0, 2.7, 0.3, 0.0],
    "login":    [0.0, 0.0, 3.0, 0.0],
    "password": [0.0, 0.0, 2.8, 0.2],
}
MODEL_B = {
    "refund":   [0.0, 3.0, 0.0, 0.0],   # what was axis 0 in A is axis 1 in B
    "invoice":  [0.2, 2.8, 0.0, 0.0],
    "delivery": [0.0, 0.0, 3.0, 0.0],
    "tracking": [0.3, 0.0, 2.7, 0.0],
    "login":    [0.0, 0.0, 0.0, 3.0],
    "password": [0.2, 0.0, 0.0, 2.8],
}

print("  Two 4-dimensional embedding models over the SAME six words. Both")
print("  are internally sensible -- 'refund' and 'invoice' are close within")
print("  each model, 'delivery' and 'tracking' are close within each model.")
print("  Neither model's axes correspond to the other's in any way.\n")

query_word = "refund"
doc_words = ["invoice", "delivery", "login"]

print(f"  Query embedded with MODEL A: {query_word!r}")
print(f"  {'comparison':<38}{'cosine similarity':>18}")
qa = MODEL_A[query_word]
for w in doc_words:
    print(f"  {'A query vs A doc ' + repr(w):<38}{cosine(qa, MODEL_A[w]):>18.2f}")

print()
qb_mixed = MODEL_B[query_word]   # the SAME word, but embedded with model B by mistake
for w in doc_words:
    print(f"  {'A query vs B doc ' + repr(w) + ' (MIXED)':<38}"
          f"{cosine(qa, MODEL_B[w]):>18.2f}")

print("\n  Read the two blocks. Comparing A's query against A's documents")
print("  correctly ranks 'invoice' highest (same topic as 'refund'). Mixing")
print("  A's query against B's documents produces DIFFERENT numbers -- not")
print("  an error, not a crash, just numbers, computed correctly by")
print("  `cosine()`, that mean nothing, because dimension 0 in model A and")
print("  dimension 0 in model B are not the same concept. This is what")
print("  happens, silently, if a document index built with one embedding")
print("  model is ever queried with a DIFFERENT model -- including a new")
print("  version of 'the same' model, whose training run landed on a")
print("  different coordinate system even at identical dimensionality.")


# ============================================================ 3
rule("3. NORMALIZATION: WHEN COSINE AND EUCLIDEAN AGREE, AND WHEN THEY DON'T")

query = np.array([1.0, 1.0])
doc_near_same_direction = np.array([0.9, 1.1])      # CLOSE to the query's direction, small magnitude
doc_far_same_direction = np.array([3.0, 3.0])        # query's EXACT direction, large magnitude
doc_different_direction = np.array([1.3, 0.7])       # different direction, mid magnitude

docs = {
    "doc_small_same_dir": doc_near_same_direction,
    "doc_LARGE_same_dir": doc_far_same_direction,
    "doc_different_dir":  doc_different_direction,
}

print("  Un-normalised vectors. One document shares the query's exact")
print("  direction but has a much larger magnitude (e.g. a longer, summed-")
print("  not-averaged document embedding).\n")
print(f"  {'document':<22}{'cosine similarity':>19}{'Euclidean distance':>20}")
for name, v in docs.items():
    print(f"  {name:<22}{cosine(query, v):>19.3f}{euclidean(query, v):>20.3f}")

cos_rank = sorted(docs, key=lambda k: -cosine(query, docs[k]))
euc_rank = sorted(docs, key=lambda k: euclidean(query, docs[k]))
print(f"\n  Ranked by cosine (best first):    {cos_rank}")
print(f"  Ranked by Euclidean (best first): {euc_rank}")
print("\n  The rankings DISAGREE. 'doc_LARGE_same_dir' points in EXACTLY the")
print("  query's direction -- cosine similarity says it is the best match,")
print("  correctly. Euclidean distance ranks it WORST, purely because of its")
print("  magnitude, which has nothing to do with meaning here.\n")

print("  Now normalise every vector to unit length first:")
uq = query / np.linalg.norm(query)
udocs = {name: v / np.linalg.norm(v) for name, v in docs.items()}
print(f"  {'document':<22}{'cosine (unit vectors)':>23}{'Euclidean (unit vectors)':>26}")
for name, v in udocs.items():
    print(f"  {name:<22}{cosine(uq, v):>23.3f}{euclidean(uq, v):>26.3f}")

cos_rank_u = sorted(udocs, key=lambda k: -cosine(uq, udocs[k]))
euc_rank_u = sorted(udocs, key=lambda k: euclidean(uq, udocs[k]))
print(f"\n  Ranked by cosine (unit vectors):    {cos_rank_u}")
print(f"  Ranked by Euclidean (unit vectors): {euc_rank_u}")
print(f"  Rankings now agree: {cos_rank_u == euc_rank_u}")

# Verify the exact identity: for unit vectors, ||a-b||^2 = 2 - 2*cos(a,b)
name0 = list(udocs)[0]
lhs = euclidean(uq, udocs[name0]) ** 2
rhs = 2 - 2 * cosine(uq, udocs[name0])
print(f"\n  Identity check on {name0!r}: ||a-b||^2 = {lhs:.4f}, "
      f"2 - 2*cos(a,b) = {rhs:.4f} -- equal, exactly, for unit vectors.")
print("  This is why normalising once at index time and then using the")
print("  cheaper, division-free dot product (M3-L02) is standard practice:")
print("  it gives IDENTICAL rankings to cosine similarity, and both agree")
print("  with Euclidean distance too, once every vector has unit length.")


# ============================================================ 4
rule("4. WHAT THIS LAB IS AND IS NOT")

print("  REAL: every number in this lab is exact, reproducible vector")
print("  arithmetic -- no simulation, no approximation.")
print("\n  ILLUSTRATIVE: section 2's two 'models' are small, hand-built")
print("  stand-ins for the real phenomenon of two trained embedding models")
print("  (or two versions of one model) landing on different coordinate")
print("  systems. A real pair of incompatible models would not be this")
print("  obviously mismatched to inspect by eye -- that is what makes the")
print("  real version dangerous: it looks fine until you check.")
print("\n  NOT SHOWN: how to detect a model-mismatch bug in a real running")
print("  system (checking a model/version tag stored per vector is the")
print("  practical fix, mirroring M5-L12's artefact-fingerprint discipline")
print("  applied to embeddings instead of prompts), and how vector indexes")
print("  actually implement these distance metrics at scale -- M6-L05")
print("  onward.")

print("\nDone.")
