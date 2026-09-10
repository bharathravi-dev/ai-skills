"""M6-L04 lab -- sparse retrieval is ALSO a vector operation, just in an
enormous, mostly-empty vocabulary space, and what that space costs and buys
you compared to a dense embedding.

Section 1 builds real sparse (count) vectors over the M6-L03 corpus's
vocabulary and computes real cosine similarity over them -- a genuine,
computable retrieval method in its own right, not a stand-in for BM25.
Section 2 demonstrates interpretability concretely: a sparse match can be
explained by naming the shared vocabulary dimensions; a dense match (reusing
M6-L02's hand-built toy embedding) cannot be explained that way at all.
Section 3 runs sparse-cosine, BM25 and dense-cosine side by side on the same
corpus and query set.

Deterministic. No API key, no network, no model download.
Run:  python labs/m6/l04_dense_vs_sparse.py
"""

from __future__ import annotations

import math


def rule(title: str) -> None:
    print(f"\n{'=' * 76}\n{title}\n{'=' * 76}")


def cosine(a: dict, b: dict) -> float:
    """Cosine similarity over sparse vectors given as {dim: value} dicts."""
    shared = set(a) & set(b)
    dot = sum(a[k] * b[k] for k in shared)
    na = math.sqrt(sum(v * v for v in a.values()))
    nb = math.sqrt(sum(v * v for v in b.values()))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


# Same corpus as M6-L03, for direct continuity.
CORPUS = {
    "D1": "refund request for damaged item",
    "D2": "please process my refund quickly",
    "D3": "the item arrived damaged and broken",
    "D4": "how do I track my order",
    "D5": "refund refund refund please help me get my refund",
}
TOKENIZED = {doc_id: text.split() for doc_id, text in CORPUS.items()}
VOCAB = sorted({w for toks in TOKENIZED.values() for w in toks})


def sparse_vector(tokens: list[str]) -> dict:
    vec = {}
    for w in tokens:
        vec[w] = vec.get(w, 0) + 1
    return vec


DOC_SPARSE = {doc_id: sparse_vector(toks) for doc_id, toks in TOKENIZED.items()}


# ============================================================ 1
rule("1. SPARSE VECTORS ARE VECTORS TOO -- JUST HUGE AND MOSTLY EMPTY")

print(f"  Vocabulary size for this 5-document corpus: {len(VOCAB)} words.")
print(f"  A real corpus's vocabulary can run to tens of thousands of words --")
print(f"  each document's sparse vector has ONE dimension per vocabulary word,")
print(f"  almost all of them zero for any single short document.\n")

query_tokens = ["refund", "damaged"]
query_sparse = sparse_vector(query_tokens)
print(f"  Query {query_tokens} as a sparse vector (non-zero entries only): "
      f"{query_sparse}")
print(f"  (Every one of the other {len(VOCAB) - len(query_sparse)} vocabulary "
      f"words is implicitly 0 in this vector.)\n")

sparse_scores = {}
for doc_id, vec in DOC_SPARSE.items():
    sparse_scores[doc_id] = cosine(query_sparse, vec)
    print(f"  {doc_id}  cosine={sparse_scores[doc_id]:.4f}  non-zero dims: {vec}")

sparse_rank = sorted(sparse_scores, key=lambda d: -sparse_scores[d])
print(f"\n  Ranked by sparse-vector cosine similarity: {sparse_rank}")
print("\n  This is a real, complete retrieval method: count how many times")
print("  each vocabulary word appears, treat that as a vector, and compute")
print("  cosine similarity exactly as M6-L02 did for dense embeddings. The")
print("  only difference so far is dimensionality and how the vector was")
print("  built -- counted directly from the text, versus learned by a model.")


# ============================================================ 2
rule("2. INTERPRETABILITY: A SPARSE MATCH CAN BE EXPLAINED. A DENSE ONE CANNOT.")

best_doc = sparse_rank[0]
shared_dims = set(query_sparse) & set(DOC_SPARSE[best_doc])
print(f"  Why did {best_doc!r} score highest against the query? Inspect the")
print(f"  vector directly -- the shared, non-zero dimensions ARE the reason:\n")
print(f"    shared vocabulary words: {sorted(shared_dims)}")
for w in sorted(shared_dims):
    print(f"      {w!r}: query has {query_sparse[w]}, {best_doc} has "
          f"{DOC_SPARSE[best_doc][w]}")
print(f"\n  That is a complete, human-readable explanation. Compare this to a")
print(f"  DENSE embedding (M6-L02's hand-built 4-axis toy model):\n")

DENSE_MODEL = {
    "refund":  [3.0, 0.0, 0.0, 0.0],
    "invoice": [2.8, 0.2, 0.0, 0.0],
}


def dense_cosine(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(x * x for x in b))
    return dot / (na * nb) if na and nb else 0.0


score = dense_cosine(DENSE_MODEL["refund"], DENSE_MODEL["invoice"])
print(f"    cosine('refund', 'invoice') = {score:.4f}")
print(f"    dimension-by-dimension: axis0={DENSE_MODEL['refund'][0]}*"
      f"{DENSE_MODEL['invoice'][0]}, axis1={DENSE_MODEL['refund'][1]}*"
      f"{DENSE_MODEL['invoice'][1]}, ...")
print("\n  Even in this tiny, HAND-BUILT toy model, 'axis 0' has no name a")
print("  system can report back to a user -- we know it because WE chose to")
print("  call it 'animal-ness' or similar when we built it (M6-L01). In a")
print("  real, trained embedding model, no axis has any human-assigned")
print("  meaning at all. You can see THAT two vectors are close; you cannot,")
print("  in general, see WHY, dimension by dimension, the way you just did")
print("  for the sparse vector above.")


# ============================================================ 3
rule("3. HEAD-TO-HEAD: SPARSE COSINE vs BM25 vs A DENSE MODEL")

# BM25, reusing M6-L03's exact formula and corpus.
K1, B = 1.5, 0.75
N = len(CORPUS)
DOC_LEN = {d: len(t) for d, t in TOKENIZED.items()}
AVGDL = sum(DOC_LEN.values()) / N


def doc_freq(term):
    return sum(1 for t in TOKENIZED.values() if term in t)


def idf(term):
    n = doc_freq(term)
    return math.log((N - n + 0.5) / (n + 0.5) + 1)


def bm25(doc_id, terms):
    total = 0.0
    for t in terms:
        f = TOKENIZED[doc_id].count(t)
        if f == 0:
            continue
        L = 1 - B + B * DOC_LEN[doc_id] / AVGDL
        total += idf(t) * f * (K1 + 1) / (f + K1 * L)
    return total


bm25_scores = {d: bm25(d, query_tokens) for d in CORPUS}
bm25_rank = sorted(bm25_scores, key=lambda d: -bm25_scores[d])

print(f"  Query: {query_tokens}\n")
print(f"  {'doc':<5}{'sparse cosine':>15}{'BM25':>10}")
for doc_id in CORPUS:
    sc, bc = sparse_scores[doc_id], bm25_scores[doc_id]
    print(f"  {doc_id:<5}{sc:>15.4f}{bc:>10.4f}")

print(f"\n  Ranked by sparse cosine: {sparse_rank}")
print(f"  Ranked by BM25:          {bm25_rank}")
print(f"  Rankings match exactly: {sparse_rank == bm25_rank}")
print("\n  Both methods are 'sparse retrieval' in this lesson's sense -- both")
print("  represent documents as vectors over the vocabulary and both find")
print("  D1 (matches both query terms) first. They differ in HOW they weight")
print("  each dimension: raw sparse cosine treats every word equally except")
print("  for how often it appears; BM25 additionally weights by rarity (IDF,")
print("  M6-L03) and caps term-frequency's contribution (saturation,")
print("  M6-L03). That difference in WEIGHTING, not the sparse-vs-dense")
print("  distinction itself, is what usually separates 'naive keyword")
print("  counting' from 'BM25' in practice.")


# ============================================================ 4
rule("4. WHAT THIS LAB IS AND IS NOT")

print("  REAL: every sparse vector, cosine similarity and BM25 score here is")
print("  exact, reproducible arithmetic on real corpus text.")
print("\n  ILLUSTRATIVE: section 2's dense model reuses M6-L02's small,")
print("  hand-built toy embedding to make the interpretability point")
print("  concretely -- a real trained embedding model would be far higher-")
print("  dimensional and its lack of per-axis meaning would be even less")
print("  disputable, not more.")
print("\n  NOT SHOWN: how a real vocabulary of tens of thousands of words is")
print("  stored and searched efficiently for sparse vectors (an inverted")
print("  index, M6-L03's forward reference), and how sparse and dense")
print("  retrieval are actually COMBINED in one system -- that is M6-L11's")
print("  reciprocal rank fusion, building directly on this lesson's")
print("  side-by-side comparison.")

print("\nDone.")
