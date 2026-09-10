"""M6-L01 lab -- semantic similarity vs exact matching, on hand-built
embeddings small enough to check by hand (course design choice: math by
hand with small numbers first, per COURSE_PLAN.md A9).

These are NOT real learned embeddings from any trained model. They are five
hand-assigned axes (animal, vehicle, emotion, finance, nature) chosen so the
example is checkable and honest about being illustrative -- a real
embedding model captures far richer, messier structure (M6-L02 onward).
Document vectors are built by MEAN POOLING word vectors, the same mechanic
M4-L04 taught for turning token vectors into one sentence vector.

Deterministic, pure arithmetic. No API key, no network, no model download.
Run:  python labs/m6/l01_semantic_vs_exact.py
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


# Axes, in order: [animal, vehicle, emotion, finance, nature]
WORD_VECTORS = {
    "dog":        [3.0, 0, 0, 0, 0],
    "puppy":      [2.8, 0, 0.5, 0, 0],
    "canine":     [3.0, 0, 0, 0, 0],
    "cat":        [2.5, 0, 0, 0, 0],
    "car":        [0, 3.0, 0, 0, 0],
    "automobile": [0, 3.0, 0, 0, 0],
    "vehicle":    [0, 3.0, 0, 0, 0],
    "truck":      [0, 2.7, 0, 0, 0],
    "joyful":     [0, 0, 2.9, 0, 0],
    "glad":       [0, 0, 2.8, 0, 0],
    "money":      [0, 0, 0, 2.8, 0],
    "loan":       [0, 0, 0, 2.6, 0],
    "river":      [0, 0, 0, 0, 3.0],
    "stream":     [0, 0, 0, 0, 2.8],
    "bank":       [0, 0, 0, 1.6, 1.6],   # ONE static vector, split between two senses
}

DOCUMENTS = {
    "D1": {"text": "My puppy is a loyal canine companion.",
           "words": ["puppy", "canine"]},
    "D2": {"text": "The automobile needs a new engine.",
           "words": ["automobile"]},
    "D3": {"text": "She felt so joyful and glad today.",
           "words": ["joyful", "glad"]},
    "D4": {"text": "I took out a loan from the bank.",
           "words": ["loan", "bank"]},
    "D5": {"text": "We walked along the river bank at sunset.",
           "words": ["river", "bank"]},
    "D6": {"text": "Your order GB-4471 has shipped.",
           "words": []},
}


def pool(words: list[str]) -> np.ndarray:
    vecs = [WORD_VECTORS[w] for w in words if w in WORD_VECTORS]
    return np.mean(vecs, axis=0) if vecs else np.zeros(5)


DOC_VECTORS = {doc_id: pool(d["words"]) for doc_id, d in DOCUMENTS.items()}


def exact_match(query_word: str) -> list[str]:
    q = query_word.lower()
    return [doc_id for doc_id, d in DOCUMENTS.items() if q in d["text"].lower()]


def semantic_rank(query_word: str) -> list[tuple[str, float]]:
    qv = WORD_VECTORS.get(query_word.lower())
    if qv is None:
        return []
    scored = [(doc_id, cosine(qv, dv)) for doc_id, dv in DOC_VECTORS.items()]
    return sorted(scored, key=lambda x: -x[1])


# ============================================================ 1
rule("1. EXACT MATCH MISSES SYNONYMS AND PARAPHRASES")

print("  Five documents, pooled from hand-built word vectors (mean pooling,")
print("  M4-L04's mechanic). Query for a word that never appears literally,")
print("  but whose MEANING is present in one document.\n")

for query in ("dog", "vehicle", "money"):
    exact = exact_match(query)
    ranked = semantic_rank(query)
    top_doc, top_score = ranked[0]
    print(f"  query {query!r:<12} exact match: {exact or '[] (MISS)'}")
    print(f"    semantic top match: {top_doc} (cosine={top_score:.2f}) "
          f"-- {DOCUMENTS[top_doc]['text']!r}")

print("\n  In all three cases, exact match finds NOTHING -- the literal word")
print("  never appears -- while cosine similarity over pooled vectors")
print("  correctly ranks the document whose MEANING matches highest. This is")
print("  the entire case for semantic search: it finds relevance that")
print("  shares no surface form with the query at all.")


# ============================================================ 2
rule("2. SEMANTIC SIMILARITY HAS ITS OWN BLIND SPOT: POLYSEMY")

query = "bank"
exact = exact_match(query)
ranked = semantic_rank(query)
print(f"  query {query!r} -- a word with two unrelated meanings.\n")
print(f"  exact match (literal substring 'bank'): {exact}")
print(f"    -- correct at the SURFACE level: both D4 and D5 do contain 'bank'.\n")
print(f"  semantic ranking (cosine similarity):")
for doc_id, score in ranked:
    print(f"    {doc_id}  cosine={score:.2f}  {DOCUMENTS[doc_id]['text']!r}")

d4_score = dict(ranked)["D4"]
d5_score = dict(ranked)["D5"]
print(f"\n  D4 (a loan, financial sense) and D5 (a river, natural sense) score")
print(f"  {d4_score:.2f} and {d5_score:.2f} -- nearly identical, because 'bank' has only")
print("  ONE static vector (M4-L04), sitting halfway between both meanings.")
print("  The embedding cannot tell 'river bank' from 'loan from the bank'")
print("  apart, because the query word alone carries no context. This is")
print("  exactly why CONTEXTUAL embeddings (M4-L04) exist -- a contextual")
print("  model reads the surrounding words and produces a DIFFERENT vector")
print("  for 'bank' in each sentence. A static, single-word query vector,")
print("  as used here, cannot do that by construction.")


# ============================================================ 3
rule("3. NEITHER WINS ALONE: A HEAD-TO-HEAD ON FIVE QUERIES")

QUERIES = ["dog", "vehicle", "money", "bank", "GB-4471"]
print("  The fifth query is an order code -- not a word with any meaning in")
print("  this vocabulary at all.\n")
print(f"  {'query':<12}{'exact match finds':<22}{'semantic top match':<30}{'winner'}")
for q in QUERIES:
    exact = exact_match(q)
    ranked = semantic_rank(q)
    if ranked:
        top_doc, top_score = ranked[0]
        sem_desc = f"{top_doc} (cosine={top_score:.2f})"
    else:
        sem_desc = "undefined (out of vocabulary)"
    if not exact and ranked:
        winner = "semantic"
    elif exact and not ranked:
        winner = "exact"
    elif exact and ranked and len(exact) > 1:
        winner = "neither alone (ambiguous)"
    else:
        winner = "both agree" if exact and ranked and exact[0] == ranked[0][0] else "-"
    exact_desc = ", ".join(exact) if exact else "[]"
    print(f"  {q:<12}{exact_desc:<22}{sem_desc:<30}{winner}")

print("\n  Read the last row. An order code has no place in a meaning-based")
print("  vector space at all -- cosine similarity is not just wrong here, it")
print("  is UNDEFINED, because the code was never assigned a vector.")
print("  Exact match finds it instantly and correctly. Neither approach")
print("  dominates the other across all five rows -- which is the argument")
print("  for HYBRID search (M6-L11), not for picking one and discarding the")
print("  other.")


# ============================================================ 4
rule("4. WHAT THIS LAB IS AND IS NOT")

print("  REAL: every cosine similarity and exact-match result here is exact,")
print("  reproducible arithmetic given the stated vectors -- nothing is")
print("  simulated or approximated.")
print("\n  ILLUSTRATIVE, NOT LEARNED: the word vectors themselves are hand-")
print("  assigned on five axes chosen to make the example checkable, not")
print("  vectors from any trained embedding model. A real model's vectors")
print("  have hundreds or thousands of dimensions, are learned from data,")
print("  and fail in messier, less predictable ways -- see M6-L02 onward,")
print("  where real embedding models are used directly.")
print("\n  NOT SHOWN: how an embedding MODEL actually produces these vectors")
print("  (M4-L04 covered the mechanism; this lab starts from vectors already")
print("  given), and any indexing or approximate search structure -- both")
print("  are M6-L05 onward.")

print("\nDone.")
