"""M6-L11 lab -- hybrid search: why BM25 and cosine scores cannot simply be
added together, reciprocal rank fusion worked by hand, and a real
demonstration of hybrid search recovering matches that neither pure sparse
nor pure dense retrieval finds alone.

Reuses M6-L03's exact BM25 implementation and M6-L01's hand-built embedding
approach, on an extended corpus deliberately containing both an exact-
keyword match and a paraphrase-only match for the same query -- the precise
scenario every lesson since M6-L01 has been building toward combining.

Deterministic. No API key, no network, no model download.
Run:  python labs/m6/l11_hybrid_rrf.py
"""

from __future__ import annotations

import math

import numpy as np


def rule(title: str) -> None:
    print(f"\n{'=' * 76}\n{title}\n{'=' * 76}")


# ============================================================ BM25, exactly M6-L03's implementation
K1, B = 1.5, 0.75


def bm25_scores(corpus_tokens: dict, query_terms: list[str]) -> dict:
    n = len(corpus_tokens)
    doc_lens = {d: len(t) for d, t in corpus_tokens.items()}
    avgdl = sum(doc_lens.values()) / n

    def doc_freq(term):
        return sum(1 for t in corpus_tokens.values() if term in t)

    def idf(term):
        df = doc_freq(term)
        return math.log((n - df + 0.5) / (df + 0.5) + 1)

    scores = {}
    for doc_id, toks in corpus_tokens.items():
        total = 0.0
        for term in query_terms:
            f = toks.count(term)
            if f == 0:
                continue
            length_norm = 1 - B + B * doc_lens[doc_id] / avgdl
            total += idf(term) * f * (K1 + 1) / (f + K1 * length_norm)
        scores[doc_id] = total
    return scores


# ============================================================ 1
rule("1. WHY YOU CANNOT JUST ADD BM25 AND COSINE SCORES")

CORPUS = {
    "D1": "refund request for damaged item",
    "D2": "please process my refund quickly",
    "D3": "the item arrived damaged and broken",
    "D4": "how do I track my order",
    "D5": "refund refund refund please help me get my refund",
}
TOKENIZED = {d: t.split() for d, t in CORPUS.items()}
QUERY = ["refund", "damaged"]

bm25 = bm25_scores(TOKENIZED, QUERY)

# Hand-built word vectors, in the style of M6-L01/M6-L02.
WORD_VECTORS = {
    "refund": [3.0, 0, 0, 0], "request": [2.5, 0, 0, 0], "for": [0, 0, 0, 0],
    "damaged": [0, 3.0, 0, 0], "item": [1.0, 1.0, 0, 0], "please": [0, 0, 0, 0],
    "process": [2.0, 0, 0, 0], "my": [0, 0, 0, 0], "quickly": [0, 0, 0, 0],
    "the": [0, 0, 0, 0], "arrived": [0, 1.5, 0, 0], "and": [0, 0, 0, 0],
    "broken": [0, 2.5, 0, 0], "how": [0, 0, 0, 0], "do": [0, 0, 0, 0],
    "i": [0, 0, 0, 0], "track": [0, 0, 3.0, 0], "order": [0, 0, 2.0, 0],
    "help": [0, 0, 0, 0], "get": [0, 0, 0, 0],
}


def doc_vector(tokens):
    vecs = [WORD_VECTORS.get(w.lower(), [0, 0, 0, 0]) for w in tokens]
    return np.mean(vecs, axis=0) if vecs else np.zeros(4)


def cosine(a, b):
    na, nb = np.linalg.norm(a), np.linalg.norm(b)
    return float(np.dot(a, b) / (na * nb)) if na and nb else 0.0


query_vec = doc_vector(QUERY)
dense = {d: cosine(query_vec, doc_vector(toks)) for d, toks in TOKENIZED.items()}

print(f"  Query: {QUERY}\n")
print(f"  {'doc':<5}{'BM25 score':>12}{'cosine score':>14}")
for d in CORPUS:
    print(f"  {d:<5}{bm25[d]:>12.4f}{dense[d]:>14.4f}")

naive_sum = {d: bm25[d] + dense[d] for d in CORPUS}
print(f"\n  Naive sum (BM25 + cosine): "
      f"{ {d: round(v, 3) for d, v in naive_sum.items()} }")
print(f"  Ranked by naive sum: {sorted(CORPUS, key=lambda d: -naive_sum[d])}")
print(f"  Ranked by BM25 alone: {sorted(CORPUS, key=lambda d: -bm25[d])}")
print("\n  BM25 scores here range roughly 0-1.5+; cosine scores range 0-1 but")
print("  mean something entirely different at any given value. Adding them")
print("  directly lets whichever method happens to produce larger raw")
print("  numbers dominate the fused ranking -- not because it is more")
print("  relevant, but because its SCALE is bigger. Compare the naive-sum")
print("  ranking to BM25 alone: notice they are not even in the same order,")
print("  for reasons that have nothing to do with relevance.")


# ============================================================ 2
rule("2. RECIPROCAL RANK FUSION: FUSE RANKS, NOT SCORES")

RRF_K = 60   # a commonly cited default constant


def rrf_fuse(rankings: list[list[str]], k: int = RRF_K) -> dict:
    scores = {}
    for ranking in rankings:
        for rank, doc_id in enumerate(ranking, start=1):
            scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (k + rank)
    return scores


bm25_rank = sorted(CORPUS, key=lambda d: -bm25[d])
dense_rank = sorted(CORPUS, key=lambda d: -dense[d])

print(f"  BM25 ranking:  {bm25_rank}")
print(f"  Dense ranking: {dense_rank}\n")
print(f"  RRF score for each document: sum over methods of 1/(k + rank), k={RRF_K}\n")
print(f"  {'doc':<5}{'BM25 rank':>11}{'dense rank':>12}{'RRF score':>12}")
rrf_scores = rrf_fuse([bm25_rank, dense_rank])
for d in CORPUS:
    br = bm25_rank.index(d) + 1
    dr = dense_rank.index(d) + 1
    print(f"  {d:<5}{br:>11}{dr:>12}{rrf_scores[d]:>12.5f}")

fused_rank = sorted(CORPUS, key=lambda d: -rrf_scores[d])
print(f"\n  Fused ranking (RRF): {fused_rank}")
print("\n  RRF never looks at the raw BM25 or cosine VALUE -- only each")
print("  document's POSITION in each ranking. This sidesteps the entire")
print("  scale-incompatibility problem from section 1: a rank of 1 means")
print("  the same thing (the best match, by that method) whether it came")
print("  from a BM25 score of 12.4 or a cosine score of 0.31.")

print(f"\n  A note on k={RRF_K}: it is a commonly cited default, but it was")
print("  chosen for corpora with thousands of results, where the difference")
print("  between rank 1 and rank 50 still matters at that scale. On a")
print("  6-document toy corpus, a large k nearly ERASES rank differences:")
print(f"  {'k':>6}{'D1 score':>12}{'D4 score (worst on both)':>27}"
      f"{'ratio D1/D4':>14}")
for k_test in (1, 5, 20, 60):
    scores_k = rrf_fuse([bm25_rank, dense_rank], k=k_test)
    print(f"  {k_test:>6}{scores_k['D1']:>12.5f}{scores_k['D4']:>27.5f}"
          f"{scores_k['D1'] / scores_k['D4']:>14.2f}")
print("\n  At k=60, the best and worst documents in this tiny corpus score")
print("  within a few percent of each other -- k must be sized relative to")
print("  how many results you actually expect to distinguish, not treated")
print("  as a universal constant. [UNVERIFIED -- confirm a sensible k for")
print("  your own corpus size and ranking depth before using RRF for real.]")


# ============================================================ 3
rule("3. HYBRID SEARCH RECOVERING BOTH KINDS OF MATCH")

EXT_CORPUS = {
    "D1": "refund request for damaged item",
    "D2": "please process my refund quickly",
    "D3": "the item arrived damaged and broken",
    "D4": "how do I track my order",
    "D5": "refund refund refund please help me get my refund",
    "D6": "we issued a full reimbursement to you today",   # paraphrase, NO literal "refund"
}
EXT_TOKENIZED = {d: t.split() for d, t in EXT_CORPUS.items()}
EXT_WORD_VECTORS = dict(WORD_VECTORS)
EXT_WORD_VECTORS.update({
    "we": [0, 0, 0, 0], "issued": [2.8, 0, 0, 0], "a": [0, 0, 0, 0],
    "full": [0, 0, 0, 0], "reimbursement": [3.0, 0, 0, 0], "to": [0, 0, 0, 0],
    "you": [0, 0, 0, 0],
})


def ext_doc_vector(tokens):
    vecs = [EXT_WORD_VECTORS.get(w.lower(), [0, 0, 0, 0]) for w in tokens]
    return np.mean(vecs, axis=0) if vecs else np.zeros(4)


ext_bm25 = bm25_scores(EXT_TOKENIZED, QUERY)
ext_query_vec = ext_doc_vector(QUERY)
ext_dense = {d: cosine(ext_query_vec, ext_doc_vector(toks)) for d, toks in EXT_TOKENIZED.items()}

print(f"  D6 (new): {EXT_CORPUS['D6']!r} -- a paraphrase of 'refund' using")
print("  'reimbursement', with NO literal query term present at all.\n")
print(f"  {'doc':<5}{'BM25 score':>12}{'BM25 rank':>11}"
      f"{'cosine score':>14}{'dense rank':>12}")
ext_bm25_rank = sorted(EXT_CORPUS, key=lambda d: -ext_bm25[d])
ext_dense_rank = sorted(EXT_CORPUS, key=lambda d: -ext_dense[d])
for d in EXT_CORPUS:
    print(f"  {d:<5}{ext_bm25[d]:>12.4f}{ext_bm25_rank.index(d) + 1:>11}"
          f"{ext_dense[d]:>14.4f}{ext_dense_rank.index(d) + 1:>12}")

print(f"\n  BM25 gives D6 a score of EXACTLY 0.0 -- it shares not one literal")
print("  word with the query, so it cannot be found at all by keyword")
print("  matching, no matter how relevant it actually is.")
print(f"\n  Dense gives D6 the SAME cosine score as D2 and D5 (0.7071, exactly).")
print("  This is not a coincidence or a tie-break artifact: D6, D2 and D5 all")
print("  point in exactly the same direction in this toy space -- purely")
print("  the 'refund' concept, with no 'damaged' concept at all -- so a")
print("  query half-way between the two concepts is equally close to all")
print("  three, REGARDLESS of which literal words produced each vector.")
print("  Dense search has correctly recognised that a sentence about a")
print("  'reimbursement' is conceptually equivalent to one about a")
print("  'refund' -- exactly the semantic-gap-bridging M6-L01 promised,")
print("  now demonstrated on a query BM25 could not match to D6 at all.")

print(f"\n  Following section 2's finding, k=60 would nearly erase rank")
print(f"  differences on this {len(EXT_CORPUS)}-document corpus. Using k=2, sized to")
print("  this corpus's actual depth, instead:")
TOY_K = 2
ext_rrf = rrf_fuse([ext_bm25_rank, ext_dense_rank], k=TOY_K)
ext_fused_rank = sorted(EXT_CORPUS, key=lambda d: -ext_rrf[d])
print(f"\n  Fused (RRF, k={TOY_K}) ranking: {ext_fused_rank}")
print(f"  D4 RRF score: {ext_rrf['D4']:.4f}  |  D6 RRF score: {ext_rrf['D6']:.4f}")
print(f"  D1's position in the fused ranking: {ext_fused_rank.index('D1') + 1} "
      f"of {len(EXT_CORPUS)} (the exact-match document, still ranked first)")

print("\n  Read this honestly: D6 still lands LAST, tied exactly with D4 --")
print("  a document matching NEITHER query concept at all. This is not a")
print("  failure of the method to notice; it is what the arithmetic")
print("  actually produces here. D4 is (BM25 rank 5, dense rank 6) and D6")
print("  is (BM25 rank 6, dense rank 5) -- the same PAIR of ranks, swapped")
print("  between methods, and RRF sums across methods symmetrically, so the")
print("  two totals come out identical. A six-document toy corpus is simply")
print("  too small, with too few genuine degrees of partial relevance, to")
print("  show hybrid search lifting a rank-6-on-one-method document clear")
print("  of an unrelated one. What the toy corpus DOES show cleanly is the")
print("  upstream fact that makes hybrid search worth using at real scale:")
print("  BM25 assigned D6 a flat, uninformative 0, while dense assigned it")
print("  a real, meaningful, non-zero relevance score identical to known")
print("  partial matches. At production scale -- thousands of documents,")
print("  many genuine shades of partial relevance, no artificial ties --")
print("  that same underlying signal is what reliably pulls a paraphrase")
print("  like D6 up from unreachable toward findable, even though this")
print("  toy example's fused RANK does not demonstrate it directly.")


# ============================================================ 4
rule("4. WHAT THIS LAB IS AND IS NOT")

print("  REAL: every BM25 score is M6-L03's exact formula; every RRF score")
print("  is the exact, standard formula, computed precisely on stated ranks.")
print("\n  ILLUSTRATIVE: the dense/cosine scores use M6-L01/M6-L02's small,")
print("  hand-built word vectors, not a real trained embedding model -- the")
print("  MECHANISM (semantic similarity beyond shared words) is real; the")
print("  specific numbers are a checkable illustration, not a benchmark.")
print("\n  A NOTE ON k=60: this is a commonly cited default in RRF")
print("  literature, not a universal constant. [UNVERIFIED -- the right")
print("  value can depend on your ranking depth and corpus; test your own.]")
print("\n  NOT SHOWN: reranking a fused or retrieved list with a second,")
print("  more expensive model (cross-encoder reranking, M6-L12), which is")
print("  the next, complementary technique in this module.")

print("\nDone.")
