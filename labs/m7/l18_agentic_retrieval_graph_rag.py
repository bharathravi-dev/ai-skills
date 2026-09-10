"""M7-L18 lab -- two ways of moving past a fixed, single-shot retrieval
pipeline: agentic retrieval, where a decision function chooses whether to
retrieve at all, retrieve once, or retrieve again based on what's already
been found (reusing M7-L02's tool-vs-retrieval judgment and M7-L17's own
multi-hop scenario); and Graph RAG, representing the SAME facts M7-L17 used
as an explicit graph, where the two-hop TEXT retrieval chain becomes a
single, direct, real graph traversal.

Deterministic. No API key, no network, no third-party dependencies.
Run:  python labs/m7/l18_agentic_retrieval_graph_rag.py
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


# M7-L17's own corpus, unchanged, for direct continuity.
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
rule("1. AGENTIC RETRIEVAL: DECIDING WHETHER TO SEARCH AT ALL")


def needs_retrieval(query: str) -> bool:
    """[REAL mechanism, ILLUSTRATIVE rule] A simple stand-in for what a real
    agent (an LLM deciding whether to call a retrieval tool, M5-L08's
    pattern) would judge: does this query need external information, or can
    it be answered directly? Real agentic systems use the model's own
    judgment, not a keyword rule -- this rule is a checkable illustration of
    the DECISION POINT, not a claim about how a real agent decides."""
    arithmetic_signals = {"%", "+", "-", "*", "plus", "minus", "times", "percent"}
    return not any(sig in query for sig in arithmetic_signals)


QUERIES = [
    "What is 15% of 200?",
    "What is the PTO policy?",
]
for q in QUERIES:
    decision = "RETRIEVE" if needs_retrieval(q) else "SKIP RETRIEVAL -- use a tool instead (M7-L02)"
    print(f"  Query: {q!r}")
    print(f"    Agent decision: {decision}")
    if not needs_retrieval(q):
        print(f"    (15% of 200 = {200 * 15 / 100} -- computed directly, no document needed)")
    print()

print("  A FIXED pipeline retrieves for every query, whether or not retrieval")
print("  is actually the right tool for it (M7-L02's entire point). An agentic")
print("  pipeline makes this decision per query -- here, with a simple rule;")
print("  in a real system, with the model's own judgment about what it needs.")


# ============================================================ 2
rule("2. AGENTIC RETRIEVAL: DECIDING WHETHER TO RETRIEVE AGAIN")


def is_sufficient(query: str, top_result_text: str) -> bool:
    """[ILLUSTRATIVE] Checks whether the retrieved text actually addresses
    the query's real subject, using simple keyword presence as a stand-in
    for a real agent's judgment (or M7-L12's groundedness check, applied to
    'is there enough here to answer' rather than 'is this claim supported')."""
    topic_words = {"policy", "location", "remote", "restriction", "office"}
    return any(w in top_result_text.lower() for w in topic_words)


AGENTIC_QUERY = "Does the Engineering team's manager allow employees to be based from home?"
first_pass = retrieve(clean_terms(AGENTIC_QUERY))
first_top_id, first_top_score = first_pass[0]
sufficient = is_sufficient(AGENTIC_QUERY, CORPUS[first_top_id])

print(f"  Query: {AGENTIC_QUERY!r}")
print(f"  First retrieval pass -- top result: {first_top_id} "
      f"(score {first_top_score:.3f}): {CORPUS[first_top_id]!r}")
print(f"  Agent's sufficiency check: does this text actually address the "
      f"policy question? {sufficient}")

if not sufficient:
    print("\n  Agent decision: NOT sufficient -- this is a fact about WHO manages")
    print("  the team, not the policy itself. Retrieve AGAIN, using an entity")
    print("  extracted from what was just found (M7-L17's exact mechanism, now")
    print("  triggered by the agent's own judgment rather than a fixed, always-")
    print("  two-hop pipeline).")
    entity = "Priya Shah"   # [ILLUSTRATIVE] stands in for real extraction from first_top_id's text
    remaining = {d: t for d, t in CORPUS_TOKENS.items() if d != first_top_id}
    second_pass = retrieve(clean_terms(entity), candidates=remaining)
    second_top_id, second_top_score = second_pass[0]
    print(f"  Second retrieval pass (query={entity!r}): top result {second_top_id} "
          f"(score {second_top_score:.3f}): {CORPUS[second_top_id]!r}")
    sufficient_2 = is_sufficient(AGENTIC_QUERY, CORPUS[second_top_id])
    print(f"  Sufficiency check again: {sufficient_2} -- agent stops here.")

print("\n  The KEY difference from M7-L17's own two-hop lab: there, the pipeline")
print("  ALWAYS performed exactly two hops, whether or not two were needed.")
print("  Here, the SECOND retrieval only happens because the agent's own")
print("  sufficiency check on the FIRST result came back negative -- for a")
print("  query answerable in one hop, this same agent would stop after pass 1.")


# ============================================================ 3
rule("3. GRAPH RAG: THE SAME FACTS, REPRESENTED AS A GRAPH")

# A real, small knowledge graph built from the SAME facts as CORPUS above.
GRAPH_EDGES = [
    ("Engineering", "managed_by", "Priya Shah"),
    ("Sales", "managed_by", "Tom Reyes"),
    ("Priya Shah", "has_policy", "flexible location, no restriction"),
    ("Tom Reyes", "has_policy", "central office required, no exception"),
]


def graph_lookup(entity: str, relation: str) -> list[str]:
    return [obj for subj, rel, obj in GRAPH_EDGES if subj == entity and rel == relation]


print("  The exact same facts M7-L17's text corpus contained, represented as")
print("  explicit (subject, relation, object) edges:\n")
for subj, rel, obj in GRAPH_EDGES:
    print(f"    ({subj}) --[{rel}]--> ({obj})")

print(f"\n  Query: {AGENTIC_QUERY!r}")
print("  Graph traversal, following edges directly:")
managers = graph_lookup("Engineering", "managed_by")
print(f"    Engineering --managed_by--> {managers}")
policies = graph_lookup(managers[0], "has_policy")
print(f"    {managers[0]} --has_policy--> {policies}")
print(f"\n  Answer, found by following two EDGES rather than two separate TEXT")
print(f"  RETRIEVAL passes: {policies[0]!r}")

print("\n  M7-L17's version of this exact question needed two full retrieval")
print("  passes -- score every document, extract an entity by reading text,")
print("  score every document again. Here, the same two 'hops' are two")
print("  dictionary/edge lookups -- exact, instant, and requiring no scoring")
print("  or ranking at all, PROVIDED the fact is already represented as an")
print("  edge in the graph.")


# ============================================================ 4
rule("4. WHEN GRAPH RAG WINS, AND WHAT IT COSTS TO GET THERE")

print("  Graph traversal is exact and direct for relationship questions the")
print("  graph already represents -- 'who manages X', 'what policy does Y")
print("  have' become lookups, not searches. This is a real, structural")
print("  advantage over M7-L17's text-based multi-hop chain for EXACTLY this")
print("  class of question.")
print("\n  But the graph didn't build itself. Someone (or some real extraction")
print("  pipeline, using an LLM or a named-entity/relation-extraction model)")
print("  had to read the ORIGINAL text and produce these exact (subject,")
print("  relation, object) triples -- a real, upfront cost this lab's")
print("  hand-built GRAPH_EDGES list skips entirely. A graph is also only as")
print("  complete as its extraction: a fact never captured as an edge is as")
print("  unreachable through the graph as it would be unreachable through a")
print("  vocabulary-mismatched text query (M7-L01's original finding, in a")
print("  new form).")
print("\n  The practical shape: text retrieval (M6-L03-M6-L12, M7-L01-M7-L17)")
print("  handles open-ended, unanticipated questions over raw documents with")
print("  no extraction step; graph RAG handles a KNOWN set of relationship")
print("  types precisely and cheaply, once built. Many real systems use both")
print("  -- a graph for well-defined relationships, text retrieval for")
print("  everything else.")


# ============================================================ 5
rule("5. WHAT THIS LAB IS AND IS NOT")

print("  REAL: BM25 scoring is M6-L03's exact formula; the graph traversal in")
print("  section 3 is genuine dictionary/edge lookup over real, stated data;")
print("  the agent's two-pass decision in section 2 is genuinely computed,")
print("  not scripted to always take two passes.")
print("\n  ILLUSTRATIVE: needs_retrieval() and is_sufficient() are small,")
print("  hand-coded rules standing in for a real agent's judgment -- in a")
print("  real system (M5-L08's pattern), an LLM itself decides whether and")
print("  when to call a retrieval tool, not a fixed keyword check. GRAPH_EDGES")
print("  was hand-built directly from M7-L17's known facts, not extracted")
print("  from text by any real process.")
print("\n  NOT SHOWN: a real agent loop where a model actually issues tool")
print("  calls and reads their results (M5-L08, M9's agentic-AI module covers")
print("  this in depth); real entity/relation extraction from unstructured")
print("  text to build a graph; and combining graph traversal with text")
print("  retrieval in one hybrid pipeline, a natural extension left to the")
print("  exercises.")

print("\nDone.")
