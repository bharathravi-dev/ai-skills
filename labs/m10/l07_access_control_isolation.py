"""M10-L07 lab -- access control is a governance control only when it is enforced
where the data is and proved by tests. This lab runs three tenants through a
retrieval assistant and measures:

  1. cache keys: answers reused across tenants,
  2. retrieval filters: pre-filter vs post-filter, for leaks AND for false denials,
  3. enforcement layer: checks at the API vs at the data layer, with a second
     endpoint added later,
  4. break-glass admin access: how much is reachable, and whether it is logged,
  5. evidence: which isolation controls have an automated test behind them.

Deterministic (seeded). No API key, no network, no third-party dependencies.
Run:  python labs/m10/l07_access_control_isolation.py
"""

from __future__ import annotations

import random
import sys
from collections import Counter

sys.stdout.reconfigure(encoding="utf-8")


def rule(title: str) -> None:
    print(f"\n{'=' * 76}\n{title}\n{'=' * 76}")


rng = random.Random(1007)
TENANTS = ["acme", "borealis", "cygnus"]
DOCS = [{"id": f"{t}-d{i}", "tenant": t, "text": f"{t} policy note {i}", "score": rng.random()}
        for t in TENANTS for i in range(40)]
COMMON_QUESTIONS = ["what is the refund window?", "how do I add a user?", "what is the SLA?"]


# ============================================================ 1
rule("1. CACHE KEYS: THE CHEAPEST WAY TO LEAK ACROSS TENANTS")

def answer_for(tenant: str, question: str) -> str:
    return f"[{tenant}] answer to {question!r}"


queries = []
for i in range(300):
    tenant = TENANTS[i % 3]
    # the shared questions are asked by every tenant, which is exactly when a
    # question-only cache key starts serving one tenant's answer to another
    question = COMMON_QUESTIONS[(i // 3) % 3] if i % 10 < 4 else f"tenant-specific question {i}"
    queries.append((tenant, question))

for label, key_fn in (("key = question", lambda t, q: q),
                      ("key = (tenant, question)", lambda t, q: (t, q))):
    cache, leaks, hits = {}, 0, 0
    for tenant, question in queries:
        key = key_fn(tenant, question)
        if key in cache:
            hits += 1
            served = cache[key]
            if not served.startswith(f"[{tenant}]"):
                leaks += 1
        else:
            cache[key] = answer_for(tenant, question)
    print(f"  {label:<28} cache hits: {hits:>3}   answers served to the WRONG tenant: {leaks:>3}")
print("\n  The leak is not in the retrieval code at all: it is one missing component")
print("  of a cache key. Every cache, memo and prompt-cache in the path needs the")
print("  tenant (or the authorization context) in its key (M9-L06's cacheScope).")


# ============================================================ 2
rule("2. RETRIEVAL FILTERS: PRE-FILTER, POST-FILTER, OR NONE")

K = 5


def search(tenant: str, mode: str) -> list[dict]:
    ranked = sorted(DOCS, key=lambda d: -d["score"])
    if mode == "none":
        return ranked[:K]
    if mode == "post-filter":                      # take top-K globally, then drop other tenants
        return [d for d in ranked[:K] if d["tenant"] == tenant]
    return [d for d in ranked if d["tenant"] == tenant][:K]     # pre-filter in the index


for mode in ("none", "post-filter", "pre-filter"):
    leaked = empty = returned = 0
    for tenant in TENANTS:
        for _ in range(20):
            hits = search(tenant, mode)
            leaked += sum(1 for d in hits if d["tenant"] != tenant)
            returned += len(hits)
            empty += not hits
    print(f"  {mode:<12} results returned: {returned:>4}   other tenants' documents: {leaked:>4}   "
          f"empty result sets: {empty:>3}/60")
print("\n  Post-filtering is safe but lossy: the tenant's own documents never reach the")
print("  top K, so correct queries return nothing (M6-L09). Pre-filtering inside the")
print("  index is both safe and useful -- and it is the only one that scales as one")
print("  tenant's corpus grows.")


# ============================================================ 3
rule("3. WHERE THE CHECK LIVES: API LAYER VS DATA LAYER")

RECORDS = [{"id": f"r{i}", "tenant": TENANTS[i % 3]} for i in range(90)]


def api_layer_check(tenant: str, endpoint: str) -> list[dict]:
    """Checks the caller's tenant in each handler -- and a new handler forgot."""
    if endpoint == "get_record":
        return [r for r in RECORDS if r["tenant"] == tenant][:1]
    if endpoint == "search":
        return [r for r in RECORDS if r["tenant"] == tenant][:5]
    return RECORDS                                   # bulk_export, added later, no check


def data_layer_check(tenant: str, endpoint: str) -> list[dict]:
    """Every query goes through one function that applies the tenant predicate."""
    rows = [r for r in RECORDS if r["tenant"] == tenant]
    return rows[:1] if endpoint == "get_record" else rows[:5] if endpoint == "search" else rows


for label, fn in (("checks in each handler", api_layer_check), ("one enforced data accessor", data_layer_check)):
    exposed = 0
    for endpoint in ("get_record", "search", "bulk_export"):
        for tenant in TENANTS:
            exposed += sum(1 for r in fn(tenant, endpoint) if r["tenant"] != tenant)
    print(f"  {label:<28} other tenants' records returned across 3 endpoints x 3 tenants: {exposed}")
print("\n  Nothing changed about the policy -- only where it is enforced. A handler")
print("  written six months later cannot forget a check it never had to write.")


# ============================================================ 4
rule("4. BREAK-GLASS ADMIN ACCESS")

ADMIN_MODES = {
    "support admin can read any tenant, no record": (len(RECORDS), False, False),
    "support admin, logged": (len(RECORDS), True, False),
    "support admin, logged + customer-visible + time-boxed": (len(RECORDS), True, True),
    "support admin scoped to one tenant on ticket": (len([r for r in RECORDS if r['tenant'] == 'acme']), True, True),
}
for label, (reach, logged, visible) in ADMIN_MODES.items():
    print(f"  {label:<56} reachable records: {reach:>3}  logged: {str(logged):<5} visible to customer: {visible}")
print("\n  Break-glass access is legitimate; unlogged, unbounded break-glass is not a")
print("  control, it is a second system with no governance. Scope it, log it, expire it,")
print("  and review the log with someone other than the person who used it.")


# ============================================================ 5
rule("5. EVIDENCE: WHICH CONTROLS HAVE A TEST BEHIND THEM?")

CONTROLS = {
    "Tenant predicate applied in the data accessor": "test_isolation_data_layer (CI, every commit)",
    "Cache keys include the tenant": "test_cache_key_contains_tenant (CI, every commit)",
    "Vector search pre-filters by tenant": None,
    "Bulk export requires tenant scope": "test_bulk_export_scoped (CI, added after incident)",
    "Admin access is logged and reviewed": "monthly access review (manual, last done 2026-06)",
    "Embeddings are stored per tenant namespace": None,
}
with_test = [c for c, e in CONTROLS.items() if e and "CI" in e]
manual = [c for c, e in CONTROLS.items() if e and "CI" not in e]
none = [c for c, e in CONTROLS.items() if not e]
for control, evidence in CONTROLS.items():
    print(f"  [{'CI  ' if control in with_test else 'manual' if control in manual else 'NONE'}] {control:<48} {evidence or '-'}")
print(f"\n  automated: {len(with_test)}/{len(CONTROLS)}   manual: {len(manual)}   no evidence: {len(none)}")
print("  In a governance review, the first three columns of the risk register come")
print("  from this table: control, evidence, last verified (M10-L04).")


rule("6. WHAT THIS LAB IS AND IS NOT")
print("  REAL: every leak count, empty-result count, exposure count and evidence")
print("  tally above is computed by running these implementations.")
print("\n  ILLUSTRATIVE: three tenants, 120 documents and a scoring function standing in")
print("  for a real index; the endpoints are functions rather than a service.")
print("\n  NOT SHOWN: identity federation, attribute-based policy engines, row-level")
print("  security in databases, and encryption per tenant -- all of which are ways to")
print("  implement the same rule closer to the data.")
print("\nDone.")
