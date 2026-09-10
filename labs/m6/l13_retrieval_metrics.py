"""M6-L13 lab -- formalizing the "recall@k" this module has used informally
since M6-L06 into a full retrieval-metrics toolkit: Precision@k and Recall@k
(and why they diverge once the relevant set isn't forced to size k), MRR
(when only the first hit matters), nDCG (when relevance is graded and ORDER
within the top-k matters, not just membership), and why every one of these
numbers is only as meaningful as the relevance labels computed underneath it.

Deterministic. No API key, no network.
Run:  python labs/m6/l13_retrieval_metrics.py
"""

from __future__ import annotations

import math

import numpy as np

RNG = np.random.default_rng(13)


def rule(title: str) -> None:
    print(f"\n{'=' * 76}\n{title}\n{'=' * 76}")


# ============================================================ 1
rule("1. PRECISION@K VS RECALL@K -- THEY DIVERGE ONCE |RELEVANT| != K")

# Hand-built vectors, M6-L01 style: interpretable axes, not a trained model.
WORD_VECTORS = {
    "damaged": [3.0, 0.0, 0.0], "item": [0.3, 0.0, 0.0], "arrived": [0.2, 0.0, 0.0],
    "broken": [2.6, 0.0, 0.0], "refund": [0.0, 3.0, 0.0], "please": [0.0, 0.2, 0.0],
    "process": [0.0, 0.4, 0.0], "reimbursement": [0.0, 2.8, 0.0], "money": [0.0, 1.5, 0.0],
    "back": [0.0, 0.5, 0.0], "track": [0.0, 0.0, 2.5], "order": [0.0, 0.0, 1.0],
    "status": [0.0, 0.0, 0.8], "shipping": [0.0, 0.0, 1.2], "cancel": [0.0, 0.3, 0.5],
    "help": [0.0, 0.0, 0.0], "the": [0.0, 0.0, 0.0], "my": [0.0, 0.0, 0.0],
    "is": [0.0, 0.0, 0.0], "how": [0.0, 0.0, 0.0], "do": [0.0, 0.0, 0.0],
    "i": [0.0, 0.0, 0.0], "a": [0.0, 0.0, 0.0], "it": [0.0, 0.0, 0.0],
}

CORPUS = {
    "D1": "the item arrived damaged", "D2": "please process my refund",
    "D3": "the item is broken and damaged", "D4": "please refund my money back",
    "D5": "i need a reimbursement please", "D6": "how do i track my order status",
    "D7": "please cancel and refund my order", "D8": "shipping status update for my order",
    "D9": "refund please help", "D10": "my order refund is still pending",
    "D11": "please process my reimbursement", "D12": "how is my shipping order status",
}
TOKENIZED = {d: t.split() for d, t in CORPUS.items()}


def pooled_vector(tokens: list[str]) -> np.ndarray:
    vecs = [WORD_VECTORS.get(t, [0.0, 0.0, 0.0]) for t in tokens]
    return np.mean(vecs, axis=0)


def cosine(a: np.ndarray, b: np.ndarray) -> float:
    na, nb = np.linalg.norm(a), np.linalg.norm(b)
    return float(np.dot(a, b) / (na * nb)) if na and nb else 0.0


# Ground truth relevant sets, hand-labeled by what the query is ACTUALLY
# asking for -- not derived from the scores below, to keep labels independent
# of the system being measured (M5-L18's discipline, applied to retrieval).
QUERY_A = "damaged item"
RELEVANT_A = {"D1", "D3"}                                   # 2 relevant total
QUERY_B = "refund"
RELEVANT_B = {"D2", "D4", "D5", "D7", "D9", "D10", "D11"}    # 7 relevant total

K = 5


def rank_by_cosine(query: str, corpus_tokens: dict) -> list[str]:
    qv = pooled_vector(query.split())
    scores = {d: cosine(qv, pooled_vector(toks)) for d, toks in corpus_tokens.items()}
    return sorted(corpus_tokens, key=lambda d: -scores[d])


def precision_at_k(ranking: list[str], relevant: set, k: int) -> float:
    top_k = ranking[:k]
    return len(set(top_k) & relevant) / k


def recall_at_k(ranking: list[str], relevant: set, k: int) -> float:
    top_k = ranking[:k]
    return len(set(top_k) & relevant) / len(relevant)


rank_a = rank_by_cosine(QUERY_A, TOKENIZED)
rank_b = rank_by_cosine(QUERY_B, TOKENIZED)

print(f"  Query A: {QUERY_A!r} -- {len(RELEVANT_A)} relevant documents exist in the whole corpus: {sorted(RELEVANT_A)}")
print(f"  Top-{K} ranking: {rank_a[:K]}")
p_a, r_a = precision_at_k(rank_a, RELEVANT_A, K), recall_at_k(rank_a, RELEVANT_A, K)
print(f"  Precision@{K} = (relevant in top {K}) / {K} = {p_a:.2f}")
print(f"  Recall@{K}    = (relevant in top {K}) / {len(RELEVANT_A)} total relevant = {r_a:.2f}")

print(f"\n  Query B: {QUERY_B!r} -- {len(RELEVANT_B)} relevant documents exist in the whole corpus: {sorted(RELEVANT_B)}")
print(f"  Top-{K} ranking: {rank_b[:K]}")
p_b, r_b = precision_at_k(rank_b, RELEVANT_B, K), recall_at_k(rank_b, RELEVANT_B, K)
print(f"  Precision@{K} = (relevant in top {K}) / {K} = {p_b:.2f}")
print(f"  Recall@{K}    = (relevant in top {K}) / {len(RELEVANT_B)} total relevant = {r_b:.2f}")

print(f"\n  Both queries retrieved the SAME k={K}, and both found several relevant")
print("  documents in their top 5 -- but Recall@5 tells two very different")
print("  stories, because it divides by how many relevant documents EXIST, not")
print("  by k. M6-L06/M6-L09/M6-L10 always compared against an exact top-k")
print("  ground truth, which quietly forced |relevant| = k -- making Precision@k")
print("  and Recall@k numerically identical there. That equality was a special")
print("  case of this section's ground truth, not a general property of the two")
print("  metrics -- outside that special case, as here, they answer different")
print("  questions: 'how much of what I returned is good?' (precision) versus")
print("  'how much of what exists did I find?' (recall).")


# ============================================================ 2
rule("2. MEAN RECIPROCAL RANK -- WHEN ONLY THE FIRST HIT MATTERS")

K1, B = 1.5, 0.75    # M6-L03's exact BM25 constants


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


LOOKUP_CORPUS = {
    "T1": "order GB-4471 shipped yesterday",
    "T2": "please refund my order GB-9002 it was damaged",
    "T3": "GB-4471 tracking says delivered but i never got it",
    "T4": "how do i cancel order GB-1183",
    "T5": "damaged item order GB-9002 please refund GB-9002 today",
    "T6": "order GB-5567 refund status update",
    "T7": "GB-1183 GB-1183 order cancellation confirmed twice for GB-1183",
    "T8": "general help how do i track any order",
    "T9": "order GB-5567 please cancel GB-5567 immediately",
    "T10": "damaged package order GB-4471 refund needed",
}
LOOKUP_TOKENIZED = {d: t.lower().split() for d, t in LOOKUP_CORPUS.items()}

# Each query has exactly ONE correct target document -- an exact-lookup task,
# M6-L01-style, but now scored and ranked (not just found/not-found).
LOOKUP_QUERIES = [
    ("GB-4471", "T1"), ("GB-9002", "T2"), ("GB-1183", "T4"),
    ("GB-5567", "T6"), ("GB-9999", None),      # no document contains this code at all
]

print("  Five lookup queries, each with exactly one correct target document")
print("  (or none, for the last). Ranked by BM25 over this ticket corpus:\n")

reciprocal_ranks = []
for query_code, target in LOOKUP_QUERIES:
    term = query_code.lower()
    scores = bm25_scores(LOOKUP_TOKENIZED, [term])
    ranking = sorted(LOOKUP_TOKENIZED, key=lambda d: -scores[d])
    if target is not None and target in ranking:
        rank = ranking.index(target) + 1
        rr = 1.0 / rank
    else:
        rank, rr = None, 0.0
    reciprocal_ranks.append(rr)
    rank_str = f"rank {rank}" if rank is not None else "not the correct target / not found"
    print(f"  Query {query_code!r:>10}  target={str(target):>5}  ranking={ranking[:4]}...  "
          f"{rank_str}  RR={rr:.3f}")

mrr = sum(reciprocal_ranks) / len(reciprocal_ranks)
print(f"\n  MRR = mean of the {len(reciprocal_ranks)} reciprocal ranks above = {mrr:.3f}")

print("\n  Notice T5 and T10 (which mention GB-9002 and GB-4471 as SECONDARY")
print("  detail) and T7 (which repeats GB-1183 three times) compete with the")
print("  actual target tickets -- BM25's term-frequency term rewards exactly")
print("  this repetition, sometimes pushing the true target below rank 1. MRR")
print("  penalizes this smoothly (1/2, 1/3, ...) rather than treating 'not")
print("  rank 1' as a flat failure -- and the GB-9999 query, matching nothing,")
print("  contributes exactly 0, the same way a genuinely absent answer should.")


# ============================================================ 3
rule("3. nDCG -- GRADED RELEVANCE, AND ORDER WITHIN THE TOP-K")

# Same 5 documents, same graded relevance labels (0-3), in two different
# orders -- chosen so Precision@5 and Recall@5 come out IDENTICAL for both,
# isolating exactly what nDCG adds: sensitivity to ORDER, not just membership.
RANKING_X = [("d_a", 1), ("d_b", 3), ("d_c", 0), ("d_d", 2), ("d_e", 0)]   # buries the best doc at rank 2
RANKING_Y = [("d_b", 3), ("d_d", 2), ("d_a", 1), ("d_c", 0), ("d_e", 0)]   # best-to-worst order


def precision_recall_binary(ranking_with_grades: list[tuple], total_relevant: int, k: int) -> tuple[float, float]:
    top_k = ranking_with_grades[:k]
    n_relevant_found = sum(1 for _, grade in top_k if grade >= 1)
    return n_relevant_found / k, n_relevant_found / total_relevant


def dcg(ranking_with_grades: list[tuple], k: int) -> float:
    return sum(grade / math.log2(i + 1) for i, (_, grade) in enumerate(ranking_with_grades[:k], start=1))


TOTAL_RELEVANT = 3   # d_a, d_b, d_d have grade >= 1; d_c, d_e are grade 0 (irrelevant)

px, rx = precision_recall_binary(RANKING_X, TOTAL_RELEVANT, 5)
py, ry = precision_recall_binary(RANKING_Y, TOTAL_RELEVANT, 5)
print(f"  Ranking X (grades in order): {[g for _, g in RANKING_X]}")
print(f"  Ranking Y (grades in order): {[g for _, g in RANKING_Y]}")
print(f"\n  Precision@5:  X={px:.2f}   Y={py:.2f}   (IDENTICAL -- same 3 relevant docs present in top 5)")
print(f"  Recall@5:     X={rx:.2f}   Y={ry:.2f}   (IDENTICAL -- same reason)")

dcg_x, dcg_y = dcg(RANKING_X, 5), dcg(RANKING_Y, 5)
ideal_ranking = sorted(RANKING_X, key=lambda t: -t[1])   # sort by grade descending = the ideal order
idcg = dcg(ideal_ranking, 5)
ndcg_x, ndcg_y = dcg_x / idcg, dcg_y / idcg

print(f"\n  DCG@5  (discount 1/log2(rank+1) per position): X={dcg_x:.3f}   Y={dcg_y:.3f}")
print(f"  IDCG@5 (DCG of the ideal, grade-sorted order {[g for _, g in ideal_ranking]}): {idcg:.3f}")
print(f"  nDCG@5 = DCG / IDCG: X={ndcg_x:.3f}   Y={ndcg_y:.3f}")

print("\n  Precision@5 and Recall@5 are blind to WHERE within the top 5 a")
print("  relevant document sits -- only whether it is present at all. nDCG is")
print("  not: Ranking X buries its best (grade-3) document at rank 2 behind a")
print("  merely-okay (grade-1) document at rank 1, and its nDCG (below 1.0)")
print("  reflects that real quality loss, while Ranking Y -- the same relevant")
print("  documents, in best-to-worst order -- scores a perfect 1.000, because")
print("  Y IS its own ideal ordering.")


# ============================================================ 4
rule("4. EVERY METRIC ABOVE IS ONLY AS GOOD AS ITS RELEVANCE LABELS")

print("  Section 1's relevant sets were hand-labeled by what the query actually")
print("  asks for. In practice, 'relevant' is often defined by thresholding a")
print("  SCORE -- and the threshold chosen changes every metric computed from")
print("  it, with the ranking itself never changing at all.\n")

# Several new, genuinely MIXED documents -- damaged AND refund concepts
# together, in varying proportions -- added to section 1's corpus and
# re-scored for Query A. D1/D3 are purely on the "damaged" axis (orthogonal
# to every other document), so without additions every non-D1/D3 score is
# EXACTLY 0.0 and no threshold could ever distinguish "strict" from "loose".
# Mixed documents give a real score gradient for a threshold to actually cut
# through -- and with MORE positive-scoring documents than k, a loose
# threshold's relevant set is guaranteed to spill outside the top-k.
EXTRA_DOCS = {
    "D13": "my item was damaged so please refund the money",
    "D14": "damaged please refund",
    "D15": "please help with a refund the item may be damaged during shipping",
    "D16": "refund please the item was a little damaged i think",
}
extended_tokenized = dict(TOKENIZED, **{d: t.split() for d, t in EXTRA_DOCS.items()})
qv = pooled_vector(QUERY_A.split())
all_scores = {d: cosine(qv, pooled_vector(toks)) for d, toks in extended_tokenized.items()}
extended_ranking = sorted(extended_tokenized, key=lambda d: -all_scores[d])

print(f"  Four new mixed documents added, each combining 'damaged' and 'refund'")
print(f"  concepts in different proportions, scored for query {QUERY_A!r}:")
for d in EXTRA_DOCS:
    print(f"    {d} ({EXTRA_DOCS[d]!r}): {all_scores[d]:.3f}")
print(f"  (D1/D3 score {all_scores['D1']:.3f}; every purely-refund/tracking document scores "
      f"{all_scores['D2']:.3f})\n")

for label, threshold in [("strict (>= 0.90)", 0.90), ("loose (>= 0.25)", 0.25)]:
    relevant_by_threshold = {d for d, s in all_scores.items() if s >= threshold}
    r = recall_at_k(extended_ranking, relevant_by_threshold, K)
    print(f"  Threshold {label}: {sorted(relevant_by_threshold)} count as 'relevant' "
          f"({len(relevant_by_threshold)} docs) -> Recall@{K} = {r:.2f}")

print(f"\n  The retrieval system and its ranking did NOT change between these two")
print("  lines -- only the DEFINITION of 'relevant' changed. The strict threshold's")
print("  2 relevant documents are both comfortably inside the top 5, for perfect")
print("  recall. The loose threshold recognizes more documents as genuinely")
print("  on-topic, but that set is now LARGER than k=5 -- so by simple pigeonhole,")
print("  at least one loosely-relevant document must fall outside the top 5,")
print("  and recall drops below 1.00, even though retrieval itself never changed.")
print("  A metric reported without stating how its relevance labels were defined")
print("  is not yet a fully specified number (M5-L18's discipline: the evaluation")
print("  dataset -- here, the label definition -- is as load-bearing as the")
print("  system being evaluated).")


# ============================================================ 5
rule("5. ALL FOUR METRICS, SIDE BY SIDE, ON ONE RANKING")

# Six documents in the style of M6-L11's hybrid-search corpus, with graded
# relevance labels assigned by hand against the query "refund damaged item".
FUSED_RANKING = [
    ("F1", 3),   # exact match, both concepts
    ("F2", 2),   # damaged, clearly relevant
    ("F3", 2),   # refund, clearly relevant
    ("F4", 1),   # refund paraphrase, partially relevant
    ("F5", 0),   # tracking, irrelevant
    ("F6", 1),   # refund mention only, marginally relevant
]
TOTAL_RELEVANT_F = sum(1 for _, g in FUSED_RANKING if g >= 1)   # 5 of 6

print(f"  Ranking under evaluation (grades in order): {[g for _, g in FUSED_RANKING]}")
print(f"  ({TOTAL_RELEVANT_F} of 6 documents are relevant at grade >= 1)\n")

for k in (1, 3, 6):
    p, r = precision_recall_binary(FUSED_RANKING, TOTAL_RELEVANT_F, k)
    print(f"  Precision@{k} = {p:.2f}   Recall@{k} = {r:.2f}")

first_relevant_rank = next(i for i, (_, g) in enumerate(FUSED_RANKING, start=1) if g >= 1)
mrr_single = 1.0 / first_relevant_rank
print(f"\n  Reciprocal rank (this one ranking) = 1/{first_relevant_rank} = {mrr_single:.3f}")

dcg_f = dcg(FUSED_RANKING, 6)
ideal_f = sorted(FUSED_RANKING, key=lambda t: -t[1])
idcg_f = dcg(ideal_f, 6)
ndcg_f = dcg_f / idcg_f
print(f"  nDCG@6 = {dcg_f:.3f} / {idcg_f:.3f} = {ndcg_f:.3f}  (ideal order would be grades {[g for _, g in ideal_f]})")

print("\n  Read these together, not in isolation. Precision@1 and the reciprocal")
print("  rank agree that the very top result is strong. Recall climbs steadily")
print("  as k grows, showing most relevant documents are present SOMEWHERE in")
print("  the list. nDCG, just under 1.0, shows the order is good but not")
print("  perfectly sorted by relevance grade -- a distinction none of the other")
print("  three numbers can express on their own.")


# ============================================================ 6
rule("6. WHAT THIS LAB IS AND IS NOT")

print("  REAL: every Precision@k, Recall@k, MRR and DCG/nDCG value is computed")
print("  from its exact, standard formula against explicitly stated relevance")
print("  labels and rankings -- BM25 (section 2) and cosine (sections 1, 4) use")
print("  M6-L01/M6-L03's exact mechanisms.")
print("\n  ILLUSTRATIVE: all relevance labels (binary sets in sections 1/2,")
print("  graded 0-3 labels in sections 3/5) are hand-assigned for this lab,")
print("  not collected from real users or annotators -- M5-L18 covers building")
print("  a trustworthy evaluation dataset from real judgments in more depth.")
print("\n  NOT SHOWN: inter-annotator agreement measurement on real human labels,")
print("  and evaluating a full production ranking pipeline (M6-L11's hybrid")
print("  fusion, M6-L12's reranking) end-to-end against these metrics together")
print("  -- a natural next exercise, left to this lesson's own exercises.")

print("\nDone.")
