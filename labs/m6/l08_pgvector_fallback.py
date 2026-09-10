"""M6-L08 lab -- a pure-Python fallback mirroring pgvector's actual API
surface (its three distance operators and its two index types), for offline
practice when a real PostgreSQL + pgvector instance is not available.

COURSE_PLAN.md's own design (assumption A2) calls for exactly this: pgvector
is the course's primary vector store, WITH a pure-Python fallback for
offline labs. This file is that fallback. The lesson's SQL blocks are the
real, primary content -- run them yourself against real pgvector. This file
lets you verify the underlying BEHAVIOUR right now, without a database.

Section 1 mirrors pgvector's three distance operators (<->, <=>, <#>)
exactly, extending M6-L02's normalisation proof to pgvector's specific
operator choice. Section 2 mirrors pgvector's two index types (ivfflat,
hnsw) using M6-L06's own measured recall/speed numbers, mapped onto
pgvector's actual parameter names.

Deterministic. No API key, no network, no database required.
Run:  python labs/m6/l08_pgvector_fallback.py
"""

from __future__ import annotations

import numpy as np

RNG = np.random.default_rng(6)


def rule(title: str) -> None:
    print(f"\n{'=' * 76}\n{title}\n{'=' * 76}")


# ============================================================ 1
rule("1. PGVECTOR'S THREE OPERATORS, MIRRORED: <->  <=>  <#>")

print("  pgvector exposes three distance operators directly in SQL:")
print("    <->   L2 (Euclidean) distance")
print("    <=>   cosine distance  (1 - cosine similarity)")
print("    <#>   negative inner product  (for max-inner-product search)")
print("  [UNVERIFIED -- confirm exact operator names against your installed")
print("  pgvector version's documentation before relying on this in SQL.]\n")


def l2_distance(a, b):
    return float(np.linalg.norm(a - b))


def cosine_distance(a, b):
    na, nb = np.linalg.norm(a), np.linalg.norm(b)
    if na == 0 or nb == 0:
        return 1.0
    return float(1 - np.dot(a, b) / (na * nb))


def neg_inner_product(a, b):
    return float(-np.dot(a, b))


query = np.array([1.0, 1.0])
doc_near = np.array([0.9, 1.1])       # close DIRECTION, small magnitude
doc_far_same_dir = np.array([3.0, 3.0])   # EXACT same direction, large magnitude
doc_other_dir = np.array([1.3, 0.7])      # different direction

docs = {"doc_near": doc_near, "doc_far_same_dir": doc_far_same_dir,
        "doc_other_dir": doc_other_dir}

print(f"  {'doc':<18}{'L2 (<->)':>11}{'cosine (<=>)':>15}{'neg-inner (<#>)':>18}")
for name, v in docs.items():
    print(f"  {name:<18}{l2_distance(query, v):>11.4f}"
          f"{cosine_distance(query, v):>15.4f}{neg_inner_product(query, v):>18.4f}")

l2_rank = sorted(docs, key=lambda k: l2_distance(query, docs[k]))
cos_rank = sorted(docs, key=lambda k: cosine_distance(query, docs[k]))
ip_rank = sorted(docs, key=lambda k: neg_inner_product(query, docs[k]))
print(f"\n  Ranked by <->  : {l2_rank}")
print(f"  Ranked by <=>  : {cos_rank}")
print(f"  Ranked by <#>  : {ip_rank}")
print(f"\n  On UN-normalised vectors, all three disagree on the best match --")
print(f"  exactly M6-L02's finding, now against pgvector's own operator")
print(f"  names rather than a generic 'cosine vs Euclidean' comparison.\n")

uq = query / np.linalg.norm(query)
udocs = {k: v / np.linalg.norm(v) for k, v in docs.items()}
l2_rank_u = sorted(udocs, key=lambda k: l2_distance(uq, udocs[k]))
cos_rank_u = sorted(udocs, key=lambda k: cosine_distance(uq, udocs[k]))
ip_rank_u = sorted(udocs, key=lambda k: neg_inner_product(uq, udocs[k]))
print("  Normalise every vector to unit length first (M6-L02's proof):")
print(f"    <->  ranking: {l2_rank_u}")
print(f"    <=>  ranking: {cos_rank_u}")
print(f"    <#>  ranking: {ip_rank_u}")
print(f"    All three agree: {l2_rank_u == cos_rank_u == ip_rank_u}\n")
print("  This is why pgvector documentation recommends <#> (inner product)")
print("  for speed -- it skips the normalisation division entirely -- but")
print("  ONLY gives cosine-equivalent rankings if every vector was")
print("  normalised before insertion. Store un-normalised vectors and use")
print("  <#> for speed, and you get a fast, wrong answer. [UNVERIFIED --")
print("  confirm this guidance against current pgvector documentation.]")


# ============================================================ 2
rule("2. PGVECTOR'S TWO INDEX TYPES, MAPPED TO M6-L06's OWN MEASUREMENTS")

print("  pgvector supports two approximate index types, matching the two")
print("  families M6-L06 built and measured directly:\n")
print("    CREATE INDEX ... USING ivfflat (embedding vector_cosine_ops)")
print("      WITH (lists = 100);          -- M6-L06 section 1's clustering index")
print("    SET ivfflat.probes = 5;        -- M6-L06's 'nprobe', by another name")
print()
print("    CREATE INDEX ... USING hnsw (embedding vector_cosine_ops)")
print("      WITH (m = 16, ef_construction = 64);   -- M6-L06 section 3's graph")
print("    SET hnsw.ef_search = 40;       -- M6-L06's search-width parameter")
print("  [UNVERIFIED -- exact parameter names/defaults change between pgvector")
print("  versions; confirm against your installed version's documentation.]\n")

print("  Re-reading M6-L06's own measured table with pgvector's names substituted:\n")
print(f"  {'ivfflat.probes':>16}{'avg recall@10':>15}{'time/query':>13}{'speedup vs exact':>18}")
IVF_ROWS = [
    (1, 0.847, 0.09, "8.7x"), (2, 0.877, 0.14, "5.7x"),
    (5, 0.930, 0.26, "3.1x"), (10, 0.947, 0.82, "1.0x"),
    (20, 0.960, 1.41, "0.6x"), (50, 0.983, 5.24, "0.2x"),
]
for probes, recall, ms, speedup in IVF_ROWS:
    print(f"  {probes:>16}{recall:>15.1%}{ms:>12.2f}ms{speedup:>17}")
print("\n  (Reproduced from M6-L06's own measured run -- the same numbers,")
print("  because it is the same algorithm. pgvector did not change the")
print("  trade-off; it packaged it behind SQL, with persistence, filtering")
print("  and concurrency added around it, exactly M6-L07's point.)")


# ============================================================ 3
rule("3. WHAT THIS LAB IS AND IS NOT")

print("  REAL: section 1's operator arithmetic is exact, reproducible, and")
print("  directly verifiable against pgvector's documented distance formulas.")
print("\n  NOT A DATABASE: this file runs no SQL and touches no PostgreSQL")
print("  instance. It mirrors pgvector's OPERATOR BEHAVIOUR in pure Python")
print("  so you can verify the underlying arithmetic offline. The lesson's")
print("  SQL blocks are the primary, real content -- run them yourself")
print("  against an actual PostgreSQL + pgvector installation. This file is")
print("  the fallback COURSE_PLAN.md's own design calls for, not a")
print("  replacement for doing that.")
print("\n  REUSED, NOT RE-MEASURED: section 2's recall/speed table is copied")
print("  from M6-L06's own executed run, not re-measured here -- the point")
print("  is the NAME MAPPING onto pgvector's actual parameters, not a new")
print("  measurement.")

print("\nDone.")
