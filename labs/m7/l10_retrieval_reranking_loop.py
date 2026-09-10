"""M7-L10 lab -- assembling Module 6's retrieval and reranking mechanisms
into one real RAG loop stage: BM25 initial retrieval (M6-L03) feeding a
cross-encoder-style reranker (M6-L12), measuring exactly why reranking must
receive a wide-enough candidate pool to work at all ("retrieve wide, rerank
narrow"), and showing this composes with M7-L09's query-side fixes rather
than competing with them.

Deterministic. No API key, no network, no third-party dependencies.
Run:  python labs/m7/l10_retrieval_reranking_loop.py
"""

from __future__ import annotations

import math
import sys

sys.stdout.reconfigure(encoding="utf-8")

K1, B = 1.5, 0.75    # M6-L03's exact BM25 constants
STOPWORDS = {
    "a", "an", "the", "is", "are", "do", "you", "who", "for", "to", "of",
    "in", "on", "at", "with", "and", "or", "then", "their", "this", "that",
    "my", "it",
}


def rule(title: str) -> None:
    print(f"\n{'=' * 76}\n{title}\n{'=' * 76}")


def remove_stopwords(tokens: list[str]) -> list[str]:
    return [t for t in tokens if t not in STOPWORDS]


def bm25_scores(corpus_tokens: dict, query_terms: list[str]) -> dict:
    n = len(corpus_tokens)
    doc_lens = {d: len(t) for d, t in corpus_tokens.items()}
    avgdl = sum(doc_lens.values()) / n
    df = {term: sum(1 for t in corpus_tokens.values() if term in t) for term in query_terms}
    idf = {term: math.log((n - df[term] + 0.5) / (df[term] + 0.5) + 1) for term in query_terms}
    scores = {}
    for d, tokens in corpus_tokens.items():
        score = 0.0
        for term in query_terms:
            f = tokens.count(term)
            if f == 0:
                continue
            numer = f * (K1 + 1)
            denom = f + K1 * (1 - B + B * doc_lens[d] / avgdl)
            score += idf[term] * numer / denom
        scores[d] = score
    return scores


CORPUS = {
    "D1": "the item arrived damaged",
    "D2": "please process my refund for the item",
    "D3": "my item arrived late but otherwise fine",
    "D4": "the item arrived and it was the wrong color",
    "D5": "can i return an item that arrived unopened",
    "D6": "the item package arrived in poor condition and the item contents appear broken",
}
CORPUS_TOKENS = {d: remove_stopwords(t.lower().split()) for d, t in CORPUS.items()}
QUERY = "was my item damaged"
QUERY_TERMS = remove_stopwords(QUERY.lower().split())


# ============================================================ 1
rule("1. THE FULL LOOP: BM25 RETRIEVAL FEEDING A CROSS-ENCODER-STYLE RERANKER")


def cross_encoder_style_score(text: str) -> float:
    """[REAL mechanism, ILLUSTRATIVE rule -- M6-L12's pattern] Reads the raw
    text jointly with the query CONCEPT (damage), not as independently pooled
    vectors -- exactly why this can recognize 'poor condition'/'broken' as
    equivalent to 'damaged', something BM25's literal matching cannot."""
    text = text.lower()
    if "damaged" in text:
        return 2.0
    if "broken" in text or "poor condition" in text:
        return 1.5
    return 0.0


initial_scores = bm25_scores(CORPUS_TOKENS, QUERY_TERMS)
full_ranking = sorted(CORPUS, key=lambda d: -initial_scores[d])

print(f"  Query: {QUERY!r}\n")
print("  Full BM25 ranking (M6-L03's exact formula) over the whole corpus:")
for i, d in enumerate(full_ranking, start=1):
    print(f"    {i}. {d} (score {initial_scores[d]:.3f}): {CORPUS[d]!r}")

print("\n  D6 is a genuine paraphrase -- 'poor condition', 'contents appear")
print("  broken' -- with no literal 'damaged' at all, so it scores low under")
print("  BM25 despite being clearly relevant. This is the exact shape of gap")
print("  M6-L12's cross-encoder reranking exists to close.")


# ============================================================ 2
rule("2. WHY RERANKING RUNS ON A CANDIDATE POOL, NOT THE WHOLE CORPUS")

print(f"  M6-L12 measured directly: a cross-encoder-style score cannot be")
print(f"  precomputed or indexed, because it is a joint function of the query")
print(f"  and the document together. Running it against all {len(CORPUS)} documents")
print(f"  here is cheap only because this corpus is tiny -- M6-L12's own")
print(f"  extrapolation showed this cost growing linearly and becoming")
print(f"  prohibitive at real corpus scale (thousands+ of documents). The real")
print(f"  pipeline shape is always: retrieve a SMALL candidate pool cheaply")
print(f"  first (BM25/dense/hybrid), THEN rerank only that pool.")


# ============================================================ 3
rule("3. RETRIEVE WIDE, RERANK NARROW -- MEASURED")


def retrieve_then_rerank(ranking: list[str], retrieve_k: int) -> tuple[list[str], list[str]]:
    candidates = ranking[:retrieve_k]
    reranked = sorted(candidates, key=lambda d: -cross_encoder_style_score(CORPUS[d]))
    return candidates, reranked


NARROW_K, WIDE_K = 2, 4

narrow_candidates, narrow_reranked = retrieve_then_rerank(full_ranking, NARROW_K)
print(f"  NARROW initial retrieval (top-{NARROW_K} by BM25): {narrow_candidates}")
print(f"  Reranked (cross-encoder-style, applied to just these {NARROW_K}): {narrow_reranked}")
print(f"  D6 in the final result: {'D6' in narrow_reranked}")

wide_candidates, wide_reranked = retrieve_then_rerank(full_ranking, WIDE_K)
print(f"\n  WIDE initial retrieval (top-{WIDE_K} by BM25): {wide_candidates}")
print(f"  Reranked (cross-encoder-style, applied to these {WIDE_K}): {wide_reranked}")
print(f"  D6 in the final result: {'D6' in wide_reranked}")

print("\n  With NARROW initial retrieval, D6 never enters the candidate pool at")
print("  all -- no reranker, however good, can recover it, because reranking")
print("  can only reorder what retrieval already found. With WIDE initial")
print("  retrieval, D6 enters the pool at rank 3 and reranking correctly")
print("  promotes it to rank 2 -- just behind the exact literal match (D1),")
print("  and ahead of documents (D4, a color complaint) that scored")
print("  RESPECTABLY under BM25 but are not actually about damage at all.")
print("  Reranking's benefit is entirely conditional on retrieve_k being wide")
print("  enough to have already found the document worth promoting.")


# ============================================================ 4
rule("4. COMPOSING WITH M7-L09's QUERY-SIDE FIXES")

EXPANDED_QUERY_TERMS = QUERY_TERMS + ["broken", "condition"]
expanded_scores = bm25_scores(CORPUS_TOKENS, EXPANDED_QUERY_TERMS)
expanded_ranking = sorted(CORPUS, key=lambda d: -expanded_scores[d])

print(f"  M7-L09's query expansion, applied BEFORE retrieval this time: adding")
print(f"  'broken' and 'condition' to the query terms.\n")
for i, d in enumerate(expanded_ranking[:NARROW_K + 1], start=1):
    print(f"    {i}. {d} (score {expanded_scores[d]:.3f}): {CORPUS[d]!r}")

d6_rank_expanded = expanded_ranking.index("D6") + 1
print(f"\n  D6's rank with an EXPANDED query: {d6_rank_expanded} of {len(CORPUS)} "
      f"(was rank {full_ranking.index('D6') + 1} with the original query).")
print("  Query expansion (M7-L09) and reranking (M6-L12) are two different")
print("  ways of reaching the same document: expansion changes what retrieval")
print("  looks for BEFORE it runs; reranking rescues a document retrieval")
print("  already found but under-ranked. Using expansion here means an even")
print(f"  NARROW top-{NARROW_K} retrieval now includes D6 without reranking's help at")
print("  all -- the two techniques compose, they don't compete for credit.")


# ============================================================ 5
rule("5. WHAT THIS LAB IS AND IS NOT")

print("  REAL: BM25 scoring is M6-L03's exact, unmodified formula; every")
print("  ranking and rerank-promotion shown is genuinely computed on real")
print("  (if synthetic) text, not scripted to fit the narrative.")
print("\n  ILLUSTRATIVE: the cross-encoder-style reranker is a small, hand-coded")
print("  rule (exact match vs. a fixed synonym list), standing in for a real")
print("  trained model -- M6-L12 covers this distinction and its limits in")
print("  depth. The corpus is small enough that 'retrieve wide' here means")
print("  top-4 of 6; at real scale this is typically top-50 to top-200 of")
print("  millions.")
print("\n  NOT SHOWN: choosing retrieve_k and final-k values systematically")
print("  (e.g. via evaluation against held-out relevance judgments, M6-L13);")
print("  hybrid (BM25 + dense) initial retrieval feeding the same reranking")
print("  step, which combines M6-L11 and M6-L12 directly and is a natural")
print("  extension left to the exercises; and assembling the final reranked")
print("  chunks into a context window, which is M7-L11's topic next.")

print("\nDone.")
