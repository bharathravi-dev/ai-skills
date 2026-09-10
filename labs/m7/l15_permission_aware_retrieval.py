"""M7-L15 lab -- retrieval that respects tenant boundaries and per-role
permissions: real tenant isolation (a query from one tenant must never see
another tenant's documents, even a textually better match); the
security-critical difference between pre-filtering and post-filtering
permissions (M6-L09's mechanics, now with real consequences for what a
post-filter approach exposes before it discards anything); role-based
filtering within one tenant; and a defense-in-depth second check that
catches a simulated pre-filter bug before results are ever returned.

Deterministic. No API key, no network, no third-party dependencies.
Run:  python labs/m7/l15_permission_aware_retrieval.py
"""

from __future__ import annotations

import math
import sys
from dataclasses import dataclass

sys.stdout.reconfigure(encoding="utf-8")

K1, B = 1.5, 0.75    # M6-L03's exact BM25 constants
STOPWORDS = {
    "a", "an", "the", "is", "are", "do", "you", "who", "for", "to", "of",
    "in", "on", "at", "with", "and", "or", "then", "their", "this", "that",
    "my", "it", "can", "i",
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


@dataclass
class Document:
    doc_id: str
    tenant: str
    required_role: str   # "employee" (any authenticated user), "hr", "executive"
    text: str


CORPUS = [
    Document("ACME-P1", "acme", "employee", "Remote work policy allows employees to work from home three days a week."),
    Document("ACME-P2", "acme", "hr", "Salary bands range from level 1 to level 8 with compensation review each year."),
    Document("ACME-P3", "acme", "executive", "The acquisition roadmap targets three companies for the next fiscal year."),
    Document("GLOBEX-P1", "globex", "employee", "Remote work policy allows employees to work from home three days a week."),
    Document("GLOBEX-P2", "globex", "hr", "Salary bands range from level 1 to level 6 with compensation review each year."),
]
CORPUS_TOKENS = {d.doc_id: remove_stopwords(d.text.lower().replace(".", "").split()) for d in CORPUS}


@dataclass
class CurrentUser:
    """[REAL pattern, ILLUSTRATIVE object] Mirrors what a FastAPI dependency
    (M2-L15's Depends()) would resolve from an auth token in a real service --
    this lab simulates the resolved user context directly, not the HTTP layer."""
    user_id: str
    tenant: str
    role: str   # "employee", "hr", or "executive"


ROLE_RANK = {"employee": 0, "hr": 1, "executive": 2}


def authorized(doc: Document, user: CurrentUser) -> bool:
    same_tenant = doc.tenant == user.tenant
    sufficient_role = ROLE_RANK[user.role] >= ROLE_RANK[doc.required_role]
    return same_tenant and sufficient_role


# ============================================================ 1
rule("1. TENANT ISOLATION: A QUERY MUST NEVER SEE ANOTHER TENANT'S DOCUMENTS")

acme_employee = CurrentUser("u1", tenant="acme", role="employee")
QUERY = "remote work policy"
query_terms = remove_stopwords(QUERY.lower().split())
all_scores = bm25_scores(CORPUS_TOKENS, query_terms)
full_ranking = sorted(CORPUS_TOKENS, key=lambda d: -all_scores[d])

print(f"  Query: {QUERY!r}, asked by {acme_employee.user_id} (tenant={acme_employee.tenant}, "
      f"role={acme_employee.role})\n")
print("  Full BM25 ranking, IGNORING tenant/role entirely:")
for d in full_ranking:
    doc = next(x for x in CORPUS if x.doc_id == d)
    print(f"    {d} (tenant={doc.tenant}, score={all_scores[d]:.3f}): {doc.text[:55]!r}...")

print(f"\n  ACME-P1 and GLOBEX-P1 are near-identical policy text -- ACME's own")
print(f"  employee must see ONLY ACME-P1. GLOBEX-P1 belongs to a different")
print(f"  tenant entirely and must never appear, no matter how well it scores.")


# ============================================================ 2
rule("2. PRE-FILTERING VS POST-FILTERING -- WHY THIS ISN'T JUST A PERFORMANCE CHOICE HERE")

TOP_K = 2


def post_filter(ranking: list[str], user: CurrentUser, k: int) -> tuple[list[str], list[str]]:
    """Retrieve top-k globally FIRST, filter permissions AFTER."""
    raw_candidates = ranking[:k]
    authorized_only = [d for d in raw_candidates
                        if authorized(next(x for x in CORPUS if x.doc_id == d), user)]
    return raw_candidates, authorized_only


def pre_filter(corpus: list[Document], corpus_tokens: dict, query_terms: list[str],
                user: CurrentUser, k: int) -> list[str]:
    """Filter to authorized documents FIRST, THEN retrieve top-k from that set only."""
    allowed_tokens = {d.doc_id: corpus_tokens[d.doc_id] for d in corpus if authorized(d, user)}
    scores = bm25_scores(allowed_tokens, query_terms)
    return sorted(allowed_tokens, key=lambda d: -scores[d])[:k]


raw, post_filtered = post_filter(full_ranking, acme_employee, TOP_K)
pre_filtered = pre_filter(CORPUS, CORPUS_TOKENS, query_terms, acme_employee, TOP_K)

print(f"  POST-filtering (retrieve top-{TOP_K} globally, filter after):")
print(f"    Raw candidate list BEFORE filtering: {raw}")
print(f"    Final result AFTER filtering: {post_filtered}")
globex_in_raw = "GLOBEX-P1" in raw
print(f"    GLOBEX-P1 present in the RAW candidate list at any point: {globex_in_raw}")

print(f"\n  PRE-filtering (filter to authorized documents FIRST, retrieve top-{TOP_K} "
      f"from only those):")
print(f"    Result: {pre_filtered}")
globex_ever_scored = "GLOBEX-P1" in {d.doc_id: None for d in CORPUS if authorized(d, acme_employee)}
print(f"    GLOBEX-P1 ever scored, ranked, or present in any intermediate list: {globex_ever_scored}")

print("\n  Both approaches produce the SAME final answer here -- but post-")
print("  filtering's raw candidate list genuinely CONTAINED a cross-tenant")
print("  document, even though it was later removed. In a real system, that")
print("  raw list is exactly what gets logged for debugging, cached for reuse,")
print("  handed to a reranker (M6-L12), or fused across methods (M6-L11) --")
print("  any one of which can leak the excluded document's presence, content,")
print("  or existence before the final filter ever runs. Pre-filtering never")
print("  lets an unauthorized document enter ANY intermediate structure at")
print("  all. For permissions specifically, this is a security property, not")
print("  a performance tuning choice -- unlike M6-L09's generic metadata")
print("  filtering, where pre- vs post- was mainly a recall/cost trade-off.")


# ============================================================ 3
rule("3. ROLE-BASED PERMISSIONS WITHIN ONE TENANT")

acme_hr = CurrentUser("u2", tenant="acme", role="hr")
SALARY_QUERY = "salary bands compensation"
salary_terms = remove_stopwords(SALARY_QUERY.lower().split())

for user in (acme_employee, acme_hr):
    result = pre_filter(CORPUS, CORPUS_TOKENS, salary_terms, user, TOP_K)
    print(f"  Query {SALARY_QUERY!r} as {user.user_id} (tenant={user.tenant}, role={user.role}): {result}")

print("\n  The employee sees nothing relevant -- ACME-P2 (salary bands) requires")
print("  the 'hr' role, which this user does not have, so it never entered")
print("  their authorized candidate set at all. The HR user, same tenant,")
print("  correctly retrieves it. Same tenant, same query, genuinely different")
print("  results -- role, not just tenant, has to gate what's retrievable.")


# ============================================================ 4
rule("4. DEFENSE IN DEPTH: A SECOND CHECK BEFORE RESULTS ARE EVER RETURNED")


def pre_filter_with_simulated_bug(corpus: list[Document], corpus_tokens: dict,
                                   query_terms: list[str], user: CurrentUser, k: int) -> list[str]:
    """Same as pre_filter, but with ONE deliberately reintroduced bug: role is
    checked, tenant is not -- simulating a real, plausible implementation
    mistake (e.g. a filter that checks role but forgets tenant scoping)."""
    allowed_tokens = {d.doc_id: corpus_tokens[d.doc_id] for d in corpus
                       if ROLE_RANK[user.role] >= ROLE_RANK[d.required_role]}   # tenant check MISSING
    scores = bm25_scores(allowed_tokens, query_terms)
    return sorted(allowed_tokens, key=lambda d: -scores[d])[:k]


def final_authorization_check(candidate_ids: list[str], corpus: list[Document], user: CurrentUser) -> list[str]:
    """A second, independent check applied to whatever the retrieval stage
    produced, regardless of how it was produced -- catches exactly the bug
    above."""
    return [cid for cid in candidate_ids
            if authorized(next(x for x in corpus if x.doc_id == cid), user)]


buggy_result = pre_filter_with_simulated_bug(CORPUS, CORPUS_TOKENS, query_terms, acme_employee, TOP_K)
print(f"  Simulating a real, plausible bug: the retrieval filter checks ROLE")
print(f"  but forgets to check TENANT.")
print(f"  Buggy pre-filter's result for {acme_employee.user_id} (tenant={acme_employee.tenant}): {buggy_result}")
leaked = "GLOBEX-P1" in buggy_result
print(f"  GLOBEX-P1 (wrong tenant) leaked through: {leaked}")

final_result = final_authorization_check(buggy_result, CORPUS, acme_employee)
print(f"\n  A SECOND, independent authorization check applied to whatever the")
print(f"  retrieval stage returns, regardless of how it was produced:")
print(f"  Final result after the second check: {final_result}")
print(f"  GLOBEX-P1 present in the FINAL result: {'GLOBEX-P1' in final_result}")

print("\n  The bug still exists in the retrieval stage -- it should be fixed")
print("  there too -- but the second, independent check caught its consequence")
print("  before anything leaked to the user. Relying on exactly one place in")
print("  the pipeline to enforce permissions means exactly one bug is enough")
print("  to leak data; a second, independent check is real insurance against")
print("  that single point of failure.")


# ============================================================ 5
rule("5. WHAT THIS LAB IS AND IS NOT")

print("  REAL: BM25 scoring is M6-L03's exact formula; every authorization,")
print("  pre-filter, post-filter, and defense-in-depth check in this lab is")
print("  genuinely computed against the stated tenant/role data, including")
print("  the deliberately reintroduced bug in section 4 and its real,")
print("  measured consequence.")
print("\n  ILLUSTRATIVE: CurrentUser stands in for what a real FastAPI")
print("  dependency (M2-L15's Depends()) would resolve from an authenticated")
print("  request -- this lab simulates the resolved user context directly,")
print("  not an actual HTTP request/response cycle or auth token validation.")
print("\n  NOT SHOWN: how a real vector database implements tenant-scoped")
print("  indexes (separate indexes per tenant vs. a shared index with a")
print("  mandatory filter, each with real trade-offs); actual authentication")
print("  and token validation; and enforcing permissions outside the model")
print("  entirely, at the infrastructure level, which is M9-L13's dedicated")
print("  topic.")

print("\nDone.")
