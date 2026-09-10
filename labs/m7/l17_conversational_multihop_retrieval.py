"""M7-L17 lab -- retrieval that requires more than one pass: a real,
measured multi-hop case where a single flat query surfaces the WRONG
document (an intermediate fact, not the actual answer), while a two-hop
chain -- discover an entity, then query using that entity -- correctly
finds it; a three-turn conversation where a later turn depends on context
from two turns back, extending M7-L09's single-follow-up example; and a
real, honest look at when to stop hopping rather than loop indefinitely.

Deterministic. No API key, no network, no third-party dependencies.
Run:  python labs/m7/l17_conversational_multihop_retrieval.py
"""

from __future__ import annotations

import math
import sys

sys.stdout.reconfigure(encoding="utf-8")

K1, B = 1.5, 0.75    # M6-L03's exact BM25 constants
STOPWORDS = {
    "a", "an", "the", "is", "are", "do", "you", "who", "for", "to", "of",
    "in", "on", "at", "with", "and", "or", "then", "their", "this", "that",
    "my", "it", "can", "i", "does", "be", "she", "he", "his", "what", "about",
    "from", "without",
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
    "ORG1": "The Engineering team is managed by Priya Shah.",
    "ORG2": "Priya Shah allows staff to work from any location without restriction.",
    "ORG3": "The Sales team is managed by Tom Reyes.",
    "ORG4": "Tom Reyes requires staff to work from the central office without exception.",
}
CORPUS_TOKENS = {d: remove_stopwords(t.lower().replace(".", "").replace("'s", "").split())
                  for d, t in CORPUS.items()}


def clean_terms(query: str) -> list[str]:
    return remove_stopwords(query.lower().replace("?", "").replace("'s", "").split())


def retrieve(query_terms: list[str], candidates: dict | None = None) -> list[tuple[str, float]]:
    pool = candidates if candidates is not None else CORPUS_TOKENS
    scores = bm25_scores(pool, query_terms)
    return sorted(scores.items(), key=lambda item: -item[1])


# ============================================================ 1
rule("1. ONE FLAT QUERY: THE TOP RESULT IS THE WRONG DOCUMENT")

FLAT_QUERY = "Does the Engineering team's manager allow employees to be based from home?"
flat_ranking = retrieve(clean_terms(FLAT_QUERY))

print(f"  Question: {FLAT_QUERY!r}\n")
print("  Single flat retrieval pass over the whole corpus:")
for doc_id, score in flat_ranking:
    print(f"    {doc_id} (score {score:.3f}): {CORPUS[doc_id]!r}")

top1 = flat_ranking[0][0]
print(f"\n  Top-1 result: {top1} -- {CORPUS[top1]!r}")
print("  This document confirms WHO manages Engineering, but says NOTHING about")
print("  work-location policy at all -- it's a genuinely relevant-LOOKING match")
print("  (it shares 'Engineering team manager' with the query) that does not")
print("  actually answer the question asked. The real answer (ORG2) scores")
print("  exactly 0.000 here -- it never even enters the ranking on merit, because")
print("  its text never mentions 'Engineering' at all, only the entity's name.")


# ============================================================ 2
rule("2. TWO-HOP RETRIEVAL: DISCOVER THE ENTITY, THEN QUERY USING IT")

HOP1_QUERY = "who manages the Engineering team"
hop1_ranking = retrieve(clean_terms(HOP1_QUERY))
hop1_top = hop1_ranking[0][0]

print(f"  Hop 1 -- retrieve to find the entity itself: {HOP1_QUERY!r}")
for doc_id, score in hop1_ranking:
    print(f"    {doc_id} (score {score:.3f}): {CORPUS[doc_id]!r}")
print(f"  Hop 1 result: {hop1_top} -- extract the entity name from its text: 'Priya Shah'")

remaining = {d: t for d, t in CORPUS_TOKENS.items() if d != hop1_top}
HOP2_QUERY = "Priya Shah"
hop2_ranking = retrieve(clean_terms(HOP2_QUERY), candidates=remaining)
hop2_top = hop2_ranking[0][0]

print(f"\n  Hop 2 -- query using the DISCOVERED entity, over the REMAINING documents")
print(f"  (excluding {hop1_top}, already used to extract the entity): {HOP2_QUERY!r}")
for doc_id, score in hop2_ranking:
    print(f"    {doc_id} (score {score:.3f}): {CORPUS[doc_id]!r}")
print(f"  Hop 2 result: {hop2_top} -- {CORPUS[hop2_top]!r}")

print(f"\n  The entity needed to find the real answer ('Priya Shah') never")
print(f"  appeared anywhere in the ORIGINAL question -- it could only be")
print(f"  discovered by retrieving once, reading the result, and retrieving")
print(f"  AGAIN using what was just found. Neither hop alone answers the")
print(f"  question; the chain of two does.")


# ============================================================ 3
rule("3. A THREE-TURN CONVERSATION: CONTEXT FROM TWO TURNS BACK")

TURN_1 = "Who manages the Sales team?"
t1_result = retrieve(clean_terms(TURN_1))[0][0]
print(f"  Turn 1: {TURN_1!r}")
print(f"    Retrieved: {t1_result} -- {CORPUS[t1_result]!r}")
print(f"    Tracked context: manager='Tom Reyes', team='Sales'")

TURN_2_RAW = "What is his policy on staff work location?"
TURN_2_REWRITTEN = "What is Tom Reyes's policy on staff work location?"
t2_raw_ranking = retrieve(clean_terms(TURN_2_RAW))
t2_rewritten_ranking = retrieve(clean_terms(TURN_2_REWRITTEN))
print(f"\n  Turn 2 (raw): {TURN_2_RAW!r}")
print(f"    All scores WITHOUT rewriting: {[(d, round(s, 3)) for d, s in t2_raw_ranking]}")
print(f"    Top-1: {t2_raw_ranking[0][0]} -- WRONG, this isn't Tom Reyes's own policy at all.")
print(f"  Turn 2 (rewritten using turn 1's discovered entity, M7-L09's pattern): "
      f"{TURN_2_REWRITTEN!r}")
print(f"    All scores WITH rewriting: {[(d, round(s, 3)) for d, s in t2_rewritten_ranking]}")
print(f"    Top-1: {t2_rewritten_ranking[0][0]} -- correct.")
print(f"    Tracked context: manager='Tom Reyes', team='Sales', "
      f"topic='staff work-location policy'")

TURN_3_RAW = "What about the Engineering team?"
TURN_3_REWRITTEN = "What is Priya Shah's policy on staff work location?"
t3_raw_ranking = retrieve(clean_terms(TURN_3_RAW))
t3_rewritten_ranking = retrieve(clean_terms(TURN_3_REWRITTEN))
print(f"\n  Turn 3 (raw): {TURN_3_RAW!r}")
print(f"    All scores WITHOUT rewriting: {[(d, round(s, 3)) for d, s in t3_raw_ranking]}")
print(f"    Top-1: {t3_raw_ranking[0][0]} -- just re-finds WHO manages Engineering,")
print(f"    not any work-location policy at all; the topic from turn 2 is gone.")
print(f"  Turn 3 needs context from BOTH turn 1's pattern (which team -> now")
print(f"  Engineering) AND turn 2's topic (work-location policy) AND section 2's")
print(f"  own finding (the answer is findable only via the manager's NAME, not")
print(f"  the team name). Rewritten using all three: {TURN_3_REWRITTEN!r}")
print(f"    All scores WITH rewriting: {[(d, round(s, 3)) for d, s in t3_rewritten_ranking]}")
print(f"    Top-1: {t3_rewritten_ranking[0][0]} -- correct.")

print("\n  Turn 3's raw form has no topic of its own at all -- exactly M7-L09's")
print("  finding -- but the missing context here comes from TWO turns back (the")
print("  work-location topic from turn 2), not the immediately preceding turn,")
print("  and correctly resolving it ALSO requires section 2's multi-hop insight")
print("  (use the manager's name, not the team name). A rewriter that only")
print("  remembers the single most recent turn, or that never resolves the team")
print("  name to an entity, would fail this turn even while succeeding at turn 2.")


# ============================================================ 4
rule("4. WHEN TO STOP HOPPING")

print("  This lab's example needed exactly two hops (and, in turn 3, the same")
print("  hop reused inside a conversation). A real question could need three,")
print("  four, or an unbounded chain -- and each additional hop is another full")
print("  retrieval pass, at M7-L09's own measured cost (roughly linear in the")
print("  number of hops, the same shape as decomposition's cost curve).")
print("\n  Two real stopping conditions matter, connecting directly to prior")
print("  lessons:")
print("    1. A hop's result doesn't contain a new entity to chase -- there is")
print("       nowhere further to go, and the chain should stop and answer with")
print("       whatever has been found (or abstain, M7-L13, if that's not enough).")
print("    2. A hop count budget is reached before an answer is found -- an")
print("       unbounded hop chain is a real cost and latency risk, not just a")
print("       correctness one; a system should abstain rather than loop")
print("       indefinitely chasing an entity that never resolves.")
print("  `[UNVERIFIED -- a specific maximum hop count is task- and cost-")
print("  dependent; calibrate it against your own queries, the same discipline")
print("  applied to every other threshold in this course.]`")


# ============================================================ 5
rule("5. WHAT THIS LAB IS AND IS NOT")

print("  REAL: every BM25 score in this lab is computed with M6-L03's exact")
print("  formula; the flat-query failure (wrong top-1 result), the two-hop")
print("  chain's success, and every turn's raw-vs-rewritten comparison in")
print("  section 3 are genuinely measured outcomes, not scripted -- including")
print("  turn 2's raw form landing on the wrong document and turn 3's raw form")
print("  finding no policy content at all.")
print("\n  ILLUSTRATIVE: entity extraction ('read Priya Shah out of ORG1's")
print("  text') and query rewriting in this lab are hand-authored, standing")
print("  in for what a real system would do with an LLM call or a named-")
print("  entity-recognition step -- consistent with every lab in this course,")
print("  none of which calls a real model.")
print("\n  NOT SHOWN: automatic entity extraction from retrieved text; deciding")
print("  PROGRAMMATICALLY when a query needs multi-hop treatment versus a")
print("  single pass (a real, harder classification problem); and combining")
print("  multi-hop retrieval with reranking (M6-L12) at each hop, a natural")
print("  extension left to the exercises.")

print("\nDone.")
