"""M6-L12 lab -- why a bi-encoder (independent pooled vectors, M6-L01 style)
is architecturally blind to negation and word order, why a cross-encoder-style
joint scorer can see it, and why that same "joint" property means a
cross-encoder's score can never be precomputed or indexed -- so it can only
ever rerank a small, already-retrieved shortlist, never search a full corpus.

Deterministic. No API key, no network, no real transformer model -- see
section 5 for exactly what is real and what is a hand-built illustration.
Run:  python labs/m6/l12_cross_encoder_reranking.py
"""

from __future__ import annotations

import time

import numpy as np

RNG = np.random.default_rng(12)


def rule(title: str) -> None:
    print(f"\n{'=' * 76}\n{title}\n{'=' * 76}")


# ============================================================ 1
rule("1. A BI-ENCODER POOLS QUERY AND DOCUMENT INDEPENDENTLY -- IT CANNOT SEE NEGATION")

# Hand-built vectors, M6-L01/M6-L11 style: interpretable axes, not a trained
# model. Function words ("not", "did", "the", ...) get an all-zero vector,
# matching how little topical signal such words carry in a real embedding
# space -- this is the choice that makes the blindness below fall out
# honestly from pooling, not from a rigged example.
WORD_VECTORS = {
    "damaged":  [3.0, 0.0, 0.0],
    "refund":   [0.0, 3.0, 0.0],
    "item":     [0.3, 0.0, 0.2],
    "arrived":  [0.2, 0.0, 0.1],
    "arrive":   [0.2, 0.0, 0.1],
    "track":    [0.0, 0.0, 2.5],
    "order":    [0.0, 0.0, 1.0],
    "not":      [0.0, 0.0, 0.0],
    "did":      [0.0, 0.0, 0.0],
    "was":      [0.0, 0.0, 0.0],
    "is":       [0.0, 0.0, 0.0],
    "at":       [0.0, 0.0, 0.0],
    "all":      [0.0, 0.0, 0.0],
    "the":      [0.0, 0.0, 0.0],
    "my":       [0.0, 0.0, 0.0],
    "it":       [0.0, 0.0, 0.0],
    "please":   [0.0, 0.0, 0.0],
    "how":      [0.0, 0.0, 0.0],
    "do":       [0.0, 0.0, 0.0],
    "i":        [0.0, 0.0, 0.0],
}

CORPUS = {
    "D1": "the item arrived damaged",
    "D2": "the item did not arrive damaged",
    "D3": "my item is damaged please refund it",
    "D4": "how do i track my order",
    "D5": "the item was not damaged at all",
}
TOKENIZED = {d: t.split() for d, t in CORPUS.items()}
QUERY = "damaged item"
QUERY_TOKENS = QUERY.split()


def pooled_vector(tokens: list[str]) -> np.ndarray:
    vecs = [WORD_VECTORS.get(t, [0.0, 0.0, 0.0]) for t in tokens]
    return np.mean(vecs, axis=0)


def cosine(a: np.ndarray, b: np.ndarray) -> float:
    na, nb = np.linalg.norm(a), np.linalg.norm(b)
    if na == 0.0 or nb == 0.0:
        return 0.0
    return float(np.dot(a, b) / (na * nb))


query_vec = pooled_vector(QUERY_TOKENS)
bi_encoder_scores = {d: cosine(query_vec, pooled_vector(toks)) for d, toks in TOKENIZED.items()}
bi_rank = sorted(CORPUS, key=lambda d: -bi_encoder_scores[d])

print(f"  Query: {QUERY!r}\n")
print("  doc    text                                    cosine score")
for d in CORPUS:
    print(f"  {d}     {CORPUS[d]:<38}  {bi_encoder_scores[d]:.4f}")
print(f"\n  Bi-encoder ranking (highest cosine first): {bi_rank}")

print("\n  D1 and D3 genuinely report damage. D2 and D5 explicitly report the")
print("  OPPOSITE -- the item was NOT damaged. A bi-encoder pools every word's")
print("  vector into ONE fixed vector per text, independently, before any")
print("  comparison happens at all. 'not' contributes an all-zero vector --")
print("  the same near-neutral contribution it would make in real embeddings")
print("  for a common function word -- so pooling 'not ... damaged' lands in")
print("  almost the same place as pooling 'damaged' alone.")
print(f"\n  Look at the RANKING, not just the scores: {bi_rank[0]} -- explicitly")
print("  NOT damaged -- comes out on TOP, ranked above both genuinely damaged")
print("  documents (D1, D3). This is not a near-miss or a close call the bi-")
print("  encoder mostly gets right; on this query it puts the single most")
print("  clearly-irrelevant-by-content document first. Pooling destroyed the")
print("  one piece of information (word order, and which word negation")
print("  attached to) that would have distinguished them.")


# ============================================================ 2
rule("2. A CROSS-ENCODER-STYLE JOINT SCORER SEES THE SAME TEXT DIFFERENTLY")

NEGATION_WORDS = {"not", "n't", "never", "without"}
WINDOW = 3


def cross_encoder_score(key_terms: list[str], tokens: list[str]) -> int:
    """Toy joint scorer: for each key term's occurrence in the document,
    look at the WINDOW tokens immediately before it. This only works because
    the scorer reads query term and document tokens together, in the
    document's actual order -- never as two independently-pooled vectors."""
    score = 0
    for i, tok in enumerate(tokens):
        if tok in key_terms:
            window = tokens[max(0, i - WINDOW):i]
            negated = any(w in NEGATION_WORDS for w in window)
            score += -1 if negated else 1
    return score


KEY_TERMS = ["damaged"]
cross_scores = {d: cross_encoder_score(KEY_TERMS, toks) for d, toks in TOKENIZED.items()}
cross_rank = sorted(CORPUS, key=lambda d: -cross_scores[d])

print("  Same query concept ('damaged'), scored by looking at the actual")
print(f"  token sequence instead of a pooled vector (negation window = {WINDOW} tokens):\n")
print("  doc    text                                    cross-encoder-style score")
for d in CORPUS:
    print(f"  {d}     {CORPUS[d]:<38}  {cross_scores[d]:+d}")
print(f"\n  Cross-encoder-style ranking: {cross_rank}")

print("\n  This scorer never builds a document vector at all. It reads the")
print("  document's tokens directly, in order, and checks what sits immediately")
print("  before each occurrence of the query's key term -- exactly the")
print("  information mean-pooling in section 1 threw away. D1 and D3 (genuinely")
print("  damaged) score positive; D2 and D5 (explicitly NOT damaged) score")
print("  negative; D4 (no mention of damage at all) scores zero. This is the")
print("  architectural reason real cross-encoders feed query and document")
print("  tokens jointly into one model (e.g. via self-attention over the")
print("  concatenated pair) instead of encoding each side separately: only a")
print("  scorer that sees both sequences together, in order, can represent an")
print("  interaction like negation at all.")


# ============================================================ 3
rule("3. THE SAME JOINT PROPERTY MEANS THIS SCORE CAN NEVER BE PRECOMPUTED")

print("  Section 1's document vectors are computed ONCE, independent of any")
print("  future query -- exactly what makes them INDEXABLE (M6-L06's ANN")
print("  structures are built over fixed vectors like these). Section 2's")
print("  score does not exist until a specific query and a specific document")
print("  are considered TOGETHER -- there is no per-document number to")
print("  precompute, cache, or hand to an index ahead of time.\n")

N_DOCS = 8_000
VOCAB = ["item", "damaged", "refund", "order", "track", "not", "arrived", "the", "my", "please"]
synthetic_docs = [
    list(RNG.choice(VOCAB, size=10))
    for _ in range(N_DOCS)
]

t0 = time.perf_counter()
doc_matrix = np.array([pooled_vector(toks) for toks in synthetic_docs])
bi_index_time = time.perf_counter() - t0

N_QUERIES = 20
t0 = time.perf_counter()
for _ in range(N_QUERIES):
    qv = pooled_vector(["damaged", "item"])
    _ = doc_matrix @ qv          # one fast, vectorized pass over the WHOLE precomputed index
bi_query_time = (time.perf_counter() - t0) / N_QUERIES

t0 = time.perf_counter()
for _ in range(N_QUERIES):
    _ = [cross_encoder_score(["damaged"], toks) for toks in synthetic_docs]   # redone in full, every query
cross_query_time = (time.perf_counter() - t0) / N_QUERIES

print(f"  {N_DOCS:,} synthetic documents, {N_QUERIES} queries, same machine:\n")
print(f"  Bi-encoder:  one-time indexing (pool all {N_DOCS:,} docs once): {bi_index_time * 1000:.1f}ms")
print(f"               average cost PER QUERY afterward (reuses the index): {bi_query_time * 1000:.2f}ms")
print(f"  Cross-encoder-style: average cost PER QUERY (must rescan all")
print(f"               {N_DOCS:,} raw documents fresh, every time -- no index exists): {cross_query_time * 1000:.2f}ms")

total_bi = bi_index_time + N_QUERIES * bi_query_time
total_cross = N_QUERIES * cross_query_time
print(f"\n  Total cost for {N_QUERIES} queries -- bi-encoder: {total_bi * 1000:.1f}ms "
      f"(one index build + {N_QUERIES} cheap reuses)")
print(f"  Total cost for {N_QUERIES} queries -- cross-encoder-style: {total_cross * 1000:.1f}ms "
      f"({N_QUERIES} full, independent rescans)")

print(f"\n  Each cross-encoder-style query alone ({cross_query_time * 1000:.2f}ms) already costs")
print(f"  a meaningful fraction of the ENTIRE one-time bi-encoder index build")
print(f"  ({bi_index_time * 1000:.1f}ms) -- and unlike that index build, it is never reused.")
print("  Extrapolating both measured per-query rates out to more queries")
print("  (`[REAL arithmetic, extending this run's own measured rates]`):\n")
print(f"  {'queries':>10}{'bi-encoder total':>22}{'cross-encoder-style total':>28}")
for q in (20, 100, 1_000, 10_000):
    bi_total = bi_index_time + q * bi_query_time
    cross_total = q * cross_query_time
    bi_str = f"{bi_total * 1000:.0f}ms" if bi_total < 1 else f"{bi_total:.2f}s"
    cross_str = f"{cross_total * 1000:.0f}ms" if cross_total < 1 else f"{cross_total:.2f}s"
    print(f"  {q:>10,}{bi_str:>22}{cross_str:>28}")

print("\n  Read the SHAPE of this, not just the numbers: the bi-encoder pays its")
print(f"  {N_DOCS:,}-document cost close to ONCE -- its total barely grows with more")
print("  queries -- and M6-L06 showed those same precomputed vectors can be")
print("  indexed for sub-linear query cost too, shrinking this further. The")
print("  cross-encoder-style scorer's total grows LINEARLY with every additional")
print("  query, because there is no fixed per-document representation to reuse")
print("  or index -- each query re-pays a cost of the same order as the entire")
print("  one-time bi-encoder index build. This is exactly why cross-encoders")
print("  rerank a small, already-retrieved SHORTLIST (tens of candidates, from")
print(f"  M6-L03/M6-L04/M6-L11), never the full corpus: rescanning {N_DOCS:,} candidates")
print("  on every single query does not stay cheap the way a bi-encoder's")
print("  reused, indexable representation does.")


# ============================================================ 4
rule("4. RERANKING A SHORTLIST: WHERE THIS ACTUALLY EARNS ITS COST")

print("  A realistic pipeline never runs the cross-encoder-style scorer over")
print("  the whole corpus. It retrieves a small shortlist cheaply first (bi-")
print("  encoder cosine here, standing in for M6-L03/M6-L04/M6-L11's retrieval),")
print("  then reranks ONLY that shortlist.\n")

SHORTLIST_K = 4
shortlist = bi_rank[:SHORTLIST_K]
print(f"  Bi-encoder retrieval shortlist (top {SHORTLIST_K}): {shortlist}")
print(f"  Bi-encoder order within the shortlist: "
      f"{sorted(shortlist, key=lambda d: -bi_encoder_scores[d])}")

reranked = sorted(shortlist, key=lambda d: -cross_scores[d])
print(f"  Cross-encoder-style rerank of the SAME shortlist: {reranked}")

print("\n  Read this against section 1's own numbers: bi-encoder retrieval alone")
print("  cannot reliably separate D1/D3 (genuinely damaged) from D2/D5 (explicitly")
print("  not damaged) -- all four are 'about damage' to a pooled vector. Reranking")
print("  that same shortlist with a scorer that reads token order fixes exactly")
print("  this, at a cost that stayed small specifically because the shortlist,")
print(f"  not the full {N_DOCS:,}-document corpus, is what got rescanned.")


# ============================================================ 5
rule("5. WHAT THIS LAB IS AND IS NOT")

print("  REAL: the pooling/cosine formulas are M6-L01's exact mechanism; the")
print("  negation-window rule's outputs are computed precisely as coded; the")
print("  section 3 timings are real, measured wall-clock costs on this machine.")
print("\n  ILLUSTRATIVE: the 'cross-encoder' here is a small, hand-coded rule")
print("  (scan for a negation word in a fixed window before a key term), not a")
print("  trained transformer. A real cross-encoder (e.g. a fine-tuned BERT")
print("  scoring the concatenated query+document pair) learns to detect far")
print("  more general interactions -- paraphrase, entailment, subtle relevance")
print("  -- from training data, rather than a hand-written rule. It shares the")
print("  exact ARCHITECTURAL property this lab demonstrates: score(query, doc)")
print("  is a single joint function of both texts together, not a comparison")
print("  of two independently-computed representations -- which is what makes")
print("  it powerful AND what makes it impossible to index.")
print("\n  NOT SHOWN: running an actual pretrained cross-encoder model, and how")
print("  much its learned interactions outperform hand-written rules like")
print("  negation detection on real, varied language -- both require a real")
print("  trained model, out of scope for this offline, from-scratch lab.")

print("\nDone.")
