"""M7-L09 lab -- fixing retrieval on the QUERY side: query expansion recovers
M7-L01's own documented vocabulary-mismatch failure (a real, measured before/
after fix, not a new example); query rewriting resolves a conversational
follow-up that is unanswerable in isolation; query decomposition retrieves a
compound, multi-part question more completely than the raw question can; and
the real, measured cost every one of these techniques adds in extra
retrieval operations.

Deterministic. No API key, no network, no third-party dependencies.
Run:  python labs/m7/l09_query_rewriting_expansion_decomposition.py
"""

from __future__ import annotations

import math
import sys

sys.stdout.reconfigure(encoding="utf-8")

K1, B = 1.5, 0.75    # M6-L03's exact BM25 constants
STOPWORDS = {
    "a", "an", "the", "is", "are", "do", "you", "who", "for", "to", "of",
    "in", "on", "at", "with", "and", "or", "then", "their", "this", "that",
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


# M7-L01's own knowledge base, unchanged, for direct continuity.
KB_DOCUMENTS = {
    "P1": "Remote Work Policy. Employees may work remotely up to three days per "
          "week with manager approval. Fully remote arrangements require VP "
          "approval and a signed remote work agreement.",
    "P2": "Expense Reimbursement Policy. Employees must submit expense reports "
          "within thirty days of purchase. Reimbursements over five hundred "
          "dollars require director approval before submission.",
    "P3": "Paid Time Off Policy. Full time employees accrue fifteen days of PTO "
          "per year, increasing to twenty days after three years of service. "
          "PTO requests must be submitted at least two weeks in advance.",
    "P4": "Referral Bonus Policy. Employees who refer a successful hire receive "
          "a two thousand dollar bonus, paid out after the new hire completes "
          "ninety days of employment.",
    "P5": "Parental Leave Policy. Employees are eligible for twelve weeks of "
          "paid parental leave following the birth or adoption of a child, "
          "available to any employee with at least six months of tenure.",
    "P6": "Equipment Policy. New employees receive a company laptop and a one "
          "time three hundred dollar home office stipend within their first "
          "thirty days.",
}
CHUNK_TOKENS = {d: remove_stopwords(t.lower().replace(",", "").replace(".", "").split())
                for d, t in KB_DOCUMENTS.items()}


# ============================================================ 1
rule("1. THE PROBLEM: M7-L01's OWN DOCUMENTED RETRIEVAL MISS")

ORIGINAL_QUERY = "Do you pay staff a reward for suggesting people who then join the team?"
original_terms = remove_stopwords(ORIGINAL_QUERY.lower().replace("?", "").split())
original_scores = bm25_scores(CHUNK_TOKENS, original_terms)

print(f"  Query: {ORIGINAL_QUERY!r}")
print(f"  (M7-L01 section 3's own reworded referral-bonus query -- documented")
print(f"  there as a clean retrieval MISS: every chunk scored 0.000.)\n")
for d in KB_DOCUMENTS:
    print(f"    {d}: {original_scores[d]:.3f}")
print(f"\n  All zero, confirmed again here -- BM25 has no literal term to match")
print("  P4's actual wording ('refer', 'bonus', 'hire') against this query's")
print("  actual wording ('reward', 'suggesting', 'join'). This lesson fixes")
print("  this from the QUERY side, rather than the retrieval-method side")
print("  (M6-L04/M6-L11's job).")


# ============================================================ 2
rule("2. QUERY EXPANSION: ADDING SYNONYMS TO BRIDGE THE GAP")

SYNONYMS = {
    "reward": ["bonus"], "suggesting": ["refer", "referring"], "people": ["hire"],
    "join": ["hire"], "team": ["employment"],
}


def expand_query(terms: list[str], synonyms: dict) -> list[str]:
    expanded = list(terms)
    for t in terms:
        expanded.extend(synonyms.get(t, []))
    return expanded


expanded_terms = expand_query(original_terms, SYNONYMS)
expanded_scores = bm25_scores(CHUNK_TOKENS, expanded_terms)

print(f"  Original query terms (stopwords removed): {original_terms}")
print(f"  Expanded query terms (synonyms added):    {expanded_terms}\n")
for d in KB_DOCUMENTS:
    marker = "  <-- was 0.000, now found" if original_scores[d] == 0 and expanded_scores[d] > 0 else ""
    print(f"    {d}: {expanded_scores[d]:.3f}{marker}")

nonzero_after_expansion = [d for d in KB_DOCUMENTS if expanded_scores[d] > 0]
print(f"\n  Documents with any real (non-zero) match after expansion: {nonzero_after_expansion} "
      f"-- every other document is still an untouched tie at 0.000, not a genuine second result.")
print("  Adding synonyms for the query's OWN words -- not touching the corpus")
print("  or the retrieval algorithm at all -- gave BM25 literal terms to match")
print("  against P4's actual vocabulary. This is the same underlying gap M6-L04/")
print("  M6-L11 address from the RETRIEVAL side (dense embeddings, hybrid fusion);")
print("  query expansion is a complementary, often cheaper, query-side fix.")


# ============================================================ 3
rule("3. QUERY REWRITING: A FOLLOW-UP THAT NEEDS CONVERSATION CONTEXT")

FIRST_TURN = "How many days of PTO does a Junior employee get?"
FOLLOW_UP = "What about the Mid tier?"

follow_up_terms = remove_stopwords(FOLLOW_UP.lower().replace("?", "").split())
follow_up_scores = bm25_scores(CHUNK_TOKENS, follow_up_terms)

print(f"  Turn 1: {FIRST_TURN!r}")
print(f"  Turn 2 (follow-up): {FOLLOW_UP!r}\n")
print(f"  Retrieving turn 2 IN ISOLATION, terms: {follow_up_terms}")
for d in KB_DOCUMENTS:
    print(f"    {d}: {follow_up_scores[d]:.3f}")
all_zero_isolated = all(s == 0 for s in follow_up_scores.values())
print(f"  Every document scores exactly 0.000 -- there is no meaningful top result "
      f"at all (all zero: {all_zero_isolated}), only an arbitrary tie.")

REWRITTEN = "What is the PTO accrual for Mid tier employees?"
rewritten_terms = remove_stopwords(REWRITTEN.lower().replace("?", "").split())
rewritten_scores = bm25_scores(CHUNK_TOKENS, rewritten_terms)
print(f"\n  Rewritten using turn 1's context: {REWRITTEN!r}")
print(f"  Terms: {rewritten_terms}")
for d in KB_DOCUMENTS:
    print(f"    {d}: {rewritten_scores[d]:.3f}")
top_rewritten = sorted(KB_DOCUMENTS, key=lambda d: -rewritten_scores[d])[:1]
print(f"  Top-1: {top_rewritten} (score {rewritten_scores[top_rewritten[0]]:.3f})")

print(f"\n  'What about the Mid tier?' carries no topic of its own at all -- 'PTO'")
print("  only exists in the CONVERSATION, not in this turn's own words. Rewriting")
print("  the follow-up to explicitly restate the carried-over topic (M5-L10's")
print("  conversation-state discipline, applied here to retrieval specifically)")
print("  turns an unanswerable, context-free fragment into a query retrieval can")
print("  actually work with. M7-L17 covers this in depth for longer, multi-turn")
print("  conversations; this is the mechanism in miniature.")


# ============================================================ 4
rule("4. QUERY DECOMPOSITION: ONE COMPOUND QUESTION, TWO SEPARATE RETRIEVALS")

COMPOUND_QUERY = "What is the remote work policy and how much is the referral bonus?"
compound_terms = remove_stopwords(COMPOUND_QUERY.lower().replace("?", "").split())
compound_scores = bm25_scores(CHUNK_TOKENS, compound_terms)

print(f"  Compound query: {COMPOUND_QUERY!r}")
print(f"  Terms: {compound_terms}\n")
top_2_compound = sorted(KB_DOCUMENTS, key=lambda d: -compound_scores[d])[:2]
for d in KB_DOCUMENTS:
    print(f"    {d}: {compound_scores[d]:.3f}")
print(f"  Top-2 as ONE query: {top_2_compound}")

SUB_QUERY_1 = "What is the remote work policy?"
SUB_QUERY_2 = "How much is the referral bonus?"
sub1_terms = remove_stopwords(SUB_QUERY_1.lower().replace("?", "").split())
sub2_terms = remove_stopwords(SUB_QUERY_2.lower().replace("?", "").split())
sub1_scores = bm25_scores(CHUNK_TOKENS, sub1_terms)
sub2_scores = bm25_scores(CHUNK_TOKENS, sub2_terms)
top1_sub1 = sorted(KB_DOCUMENTS, key=lambda d: -sub1_scores[d])[0]
top1_sub2 = sorted(KB_DOCUMENTS, key=lambda d: -sub2_scores[d])[0]

print(f"\n  Decomposed into two sub-queries, retrieved SEPARATELY:")
print(f"    Sub-query 1: {SUB_QUERY_1!r} -> top-1: {top1_sub1} (score {sub1_scores[top1_sub1]:.3f})")
print(f"    Sub-query 2: {SUB_QUERY_2!r} -> top-1: {top1_sub2} (score {sub2_scores[top1_sub2]:.3f})")

combined = {top1_sub1, top1_sub2}
compound_top2_set = set(top_2_compound)
print(f"\n  Documents found -- one compound query: {compound_top2_set}; "
      f"two decomposed sub-queries: {combined}")
print("  Both approaches happen to find the same two documents here, but for a")
print("  DIFFERENT reason: the compound query's terms all get scored TOGETHER")
print("  in one BM25 pass, so a document strongly matching only HALF the")
print("  question competes, in the same ranking, against one matching the")
print("  OTHER half -- decomposition instead guarantees each half gets its OWN")
print("  dedicated top-1, regardless of how the two topics compare to each other.")


# ============================================================ 5
rule("5. THE COST OF QUERY TRANSFORMATION")

print("  Every technique in this lesson buys its fix with extra retrieval work:\n")
print(f"    Raw query:              1 retrieval pass")
print(f"    Expanded query:         1 retrieval pass (more query terms, same pass count)")
print(f"    Rewritten query:        1 retrieval pass (same count, but needs a rewriting")
print(f"                             step first -- an extra LLM call in a real system)")
print(f"    Decomposed (2 parts):   2 retrieval passes (roughly 2x retrieval cost)")
print(f"    Decomposed (N parts):   N retrieval passes (cost scales with N)")

print("\n  Expansion and rewriting change WHAT is searched for, at roughly the")
print("  same retrieval cost as the original query. Decomposition changes HOW")
print("  MANY searches happen -- a real, linear cost increase with the number")
print("  of sub-questions, on top of whatever it costs (an LLM call, in a real")
print("  system) to decide how to decompose the question in the first place.")


# ============================================================ 6
rule("6. WHAT THIS LAB IS AND IS NOT")

print("  REAL: every BM25 score in this lab is computed with M6-L03's exact,")
print("  unmodified formula; the expansion synonyms and rewritten/decomposed")
print("  queries are hand-authored, but the retrieval scores they produce are")
print("  genuinely computed, not asserted; the before/after fix in section 2")
print("  reproduces M7-L01's own documented failure and then genuinely resolves it.")
print("\n  MOCK / ILLUSTRATIVE: this lab's 'rewriting' and 'decomposition' are")
print("  hand-authored strings, not generated by a real LLM call. A real system")
print("  typically uses a model to perform expansion, rewriting, and")
print("  decomposition dynamically -- this lab demonstrates that the RESULTING")
print("  retrieval improvement is real, without claiming the transformation")
print("  step itself was automated here.")
print("\n  NOT SHOWN: how a real system decides WHEN to rewrite, expand, or")
print("  decompose a query (versus passing it through unchanged); combining")
print("  decomposed sub-query results into one coherent final answer (M7-L11's")
print("  context assembly, M7-L12's generation); and multi-turn conversational")
print("  retrieval at depth, which is M7-L17's dedicated topic.")

print("\nDone.")
