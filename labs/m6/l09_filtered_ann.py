"""M6-L09 lab -- the filtered-ANN problem, measured: post-filtering an
approximate search can silently return far fewer results than requested,
pre-filtering-then-exact fixes correctness at a real, measurable cost, and
over-fetching is a real, tunable middle ground.

Reuses the same IVF-style index and topic-structured corpus as M6-L06/L07,
now with a metadata "category" field at varying selectivity, exactly the
kind of field a real WHERE clause (M6-L08) would filter on.

Deterministic (seeded). No API key, no network.
Run:  python labs/m6/l09_filtered_ann.py
"""

from __future__ import annotations

import time

import numpy as np
from sklearn.cluster import KMeans

RNG = np.random.default_rng(6)


def rule(title: str) -> None:
    print(f"\n{'=' * 76}\n{title}\n{'=' * 76}")


def exact_top_k(query, corpus_, k):
    scores = corpus_ @ query
    kk = min(k, len(scores))
    top_idx = np.argpartition(-scores, kk - 1)[:kk]
    return top_idx[np.argsort(-scores[top_idx])]


# Same corpus generation as M6-L06/L07, plus a metadata "category" field.
N, D = 50_000, 128
N_TOPICS, TOPIC_SPREAD = 200, 0.15
N_CLUSTERS = 100
K_REQUESTED = 10

topic_centers = RNG.normal(size=(N_TOPICS, D)).astype(np.float32)
topic_centers /= np.linalg.norm(topic_centers, axis=1, keepdims=True)
topic_of = RNG.integers(0, N_TOPICS, size=N)
corpus = topic_centers[topic_of] + RNG.normal(scale=TOPIC_SPREAD, size=(N, D)).astype(np.float32)
corpus /= np.linalg.norm(corpus, axis=1, keepdims=True)

# Category is independent of topic -- realistic: metadata like "region" or
# "department" often does not correlate with semantic content.
CATEGORY_SHARES = {"common": 0.50, "medium": 0.30, "rare": 0.15, "very_rare": 0.05}
cat_names = list(CATEGORY_SHARES.keys())
cat_probs = list(CATEGORY_SHARES.values())
categories = RNG.choice(cat_names, size=N, p=cat_probs)

print(f"Building the {N_CLUSTERS}-cluster IVF index over {N:,} vectors "
      f"(a few seconds)...")
t0 = time.perf_counter()
kmeans = KMeans(n_clusters=N_CLUSTERS, n_init=3, random_state=6).fit(corpus)
print(f"Index built in {time.perf_counter() - t0:.1f}s.")
labels = kmeans.labels_
centroids = kmeans.cluster_centers_
centroids /= np.linalg.norm(centroids, axis=1, keepdims=True)
CLUSTER_MEMBERS = {c: np.where(labels == c)[0] for c in range(N_CLUSTERS)}

N_QUERIES = 20
query_topics = RNG.integers(0, N_TOPICS, size=N_QUERIES)
queries = (topic_centers[query_topics]
           + RNG.normal(scale=TOPIC_SPREAD, size=(N_QUERIES, D)).astype(np.float32))
queries /= np.linalg.norm(queries, axis=1, keepdims=True)


def ivf_raw_candidates(query, nprobe, n_candidates):
    centroid_scores = centroids @ query
    nearest_clusters = np.argpartition(-centroid_scores, nprobe)[:nprobe]
    candidate_idx = np.concatenate([CLUSTER_MEMBERS[c] for c in nearest_clusters])
    if len(candidate_idx) <= n_candidates:
        return candidate_idx
    sub_scores = corpus[candidate_idx] @ query
    top = np.argpartition(-sub_scores, n_candidates - 1)[:n_candidates]
    return candidate_idx[top[np.argsort(-sub_scores[top])]]


NPROBE = 10


# ============================================================ 1
rule("1. THE POST-FILTER PROBLEM: FILTER AFTER SEARCHING, MEASURED")

print(f"  Ask for the top-{K_REQUESTED} results, THEN filter by category --")
print(f"  the naive, obvious way to combine vector search with a WHERE clause.\n")
print(f"  {'category':<12}{'true corpus share':>18}{'avg results returned':>23}"
      f"{'requested':>12}")
for cat in cat_names:
    counts = []
    for q in queries:
        raw = ivf_raw_candidates(q, NPROBE, K_REQUESTED)
        survivors = sum(1 for i in raw if categories[i] == cat)
        counts.append(survivors)
    avg = sum(counts) / len(counts)
    print(f"  {cat:<12}{CATEGORY_SHARES[cat]:>18.0%}{avg:>23.1f}{K_REQUESTED:>11}")

print("\n  Read the 'very_rare' row: requesting 10 results and getting back a")
print("  small fraction of that is not a bug in the index -- it is the")
print("  direct, arithmetic consequence of filtering AFTER selecting only")
print("  10 candidates from a corpus where this category is uncommon. Many")
print("  genuinely matching documents exist elsewhere in the corpus; they")
print("  were simply never among the 10 candidates ANN search happened to")
print("  surface BEFORE the filter ran.")


# ============================================================ 2
rule("2. THE PRE-FILTER FIX: FILTER FIRST, THEN SEARCH EXACTLY -- AT A COST")

print("  Filter the corpus to the matching category FIRST, then run EXACT")
print("  search (M6-L05) only within that subset. This always returns the")
print("  full requested count, when enough matching documents exist -- but")
print("  it isn't free.\n")
print(f"  {'category':<12}{'subset size':>13}{'avg results returned':>23}"
      f"{'avg time/query':>17}")
exact_full_time = None
for cat in cat_names:
    subset_idx = np.where(categories == cat)[0]
    subset = corpus[subset_idx]
    counts, times = [], []
    for q in queries:
        t0 = time.perf_counter()
        local_top = exact_top_k(q, subset, K_REQUESTED)
        times.append(time.perf_counter() - t0)
        counts.append(len(local_top))
    avg_count = sum(counts) / len(counts)
    avg_time = sum(times) / len(times)
    if cat == "common" and exact_full_time is None:
        exact_full_time = avg_time
    print(f"  {cat:<12}{len(subset_idx):>13,}{avg_count:>23.1f}"
          f"{avg_time * 1000:>15.2f}ms")

t0 = time.perf_counter()
for q in queries:
    exact_top_k(q, corpus, K_REQUESTED)
full_corpus_time = (time.perf_counter() - t0) / N_QUERIES
print(f"\n  For comparison, exact search over the FULL {N:,}-vector corpus: "
      f"{full_corpus_time * 1000:.2f}ms/query.")
print("\n  Pre-filtering fixes correctness completely -- every row above")
print("  returned the full requested count. But look at the 'common' row's")
print("  time: it costs roughly HALF of full exact search -- proportional")
print("  to the subset size (M6-L05's linear scaling, exactly), not a small")
print("  fraction of it. Even a 50%-selective filter still leaves you paying")
print("  something close to a full linear scan, which is the exact cost the")
print("  approximate index (M6-L06) exists to avoid. The less selective the")
print("  filter, the closer 'filter first, then search exactly' gets to")
print("  plain exact search over the whole corpus -- and at NO filter at")
print("  all, that is precisely what it becomes.")


# ============================================================ 3
rule("3. OVER-FETCHING: FILTER THE WHOLE POOL, THEN TAKE THE TOP-K")

print("  Section 1's flaw: it filtered the top-10-BY-SCORE, discarding")
print("  matching candidates that happened to rank 11th or lower BEFORE the")
print("  filter ever saw them. The fix: filter the WHOLE candidate pool by")
print("  category first, THEN take the best k of what survives -- and")
print("  search more clusters (nprobe) to make that pool bigger.\n")


def filter_pool_then_topk(query, nprobe, category, k):
    centroid_scores = centroids @ query
    nearest_clusters = np.argpartition(-centroid_scores, nprobe)[:nprobe]
    pool = np.concatenate([CLUSTER_MEMBERS[c] for c in nearest_clusters])
    matching = pool[categories[pool] == category]      # filter the WHOLE pool
    if len(matching) == 0:
        return np.array([], dtype=int)
    sub_scores = corpus[matching] @ query
    kk = min(k, len(matching))
    top = np.argpartition(-sub_scores, kk - 1)[:kk]
    return matching[top[np.argsort(-sub_scores[top])]]


cat = "very_rare"
print(f"  Category: {cat!r} ({CATEGORY_SHARES[cat]:.0%} of the corpus). "
      f"Requesting {K_REQUESTED} results.\n")
print(f"  {'nprobe':>8}{'avg results returned':>23}{'avg time/query':>17}")
for nprobe in (1, 2, 5, 10, 20, 50):
    counts, times = [], []
    for q in queries:
        t0 = time.perf_counter()
        result = filter_pool_then_topk(q, nprobe, cat, K_REQUESTED)
        times.append(time.perf_counter() - t0)
        counts.append(len(result))
    avg_count = sum(counts) / len(counts)
    avg_time = sum(times) / len(times)
    print(f"  {nprobe:>8}{avg_count:>23.1f}{avg_time * 1000:>15.2f}ms")

print("\n  Read this against section 1's 0.5-of-10 result. The real fix was")
print("  never 'search harder' -- it was filtering the pool BEFORE cutting")
print(f"  it down to k, which alone recovers nearly all {K_REQUESTED} results")
print("  even at nprobe=1 (9.9 of 10 here). nprobe still matters at the")
print("  margin: it closes the small remaining gap, and would matter far")
print("  more for a category rarer than 5%, or a smaller per-cluster pool --")
print("  but it is a SECONDARY lever. The primary bug in section 1 was")
print("  filtering at the wrong STAGE, not searching too small a POOL.")


# ============================================================ 4
rule("4. WHAT THIS LAB IS AND IS NOT")

print("  REAL: every count and timing in this lab comes from actually")
print("  running the search and filter operations on a real (if synthetic)")
print("  corpus with real category labels -- nothing here is simulated.")
print("\n  ILLUSTRATIVE: the specific category shares, corpus size, and")
print("  timings are chosen for this lab and this machine. Real selectivity")
print("  in your own metadata, and your own hardware, will give different")
print("  numbers -- measure your own before choosing an overfetch factor or")
print("  a pre-filter/post-filter strategy.")
print("\n  NOT SHOWN: how real vector databases implement filtered search")
print("  internally (some push the filter into the index traversal itself,")
print("  which can do better than either pure strategy shown here -- product-")
print("  and version-specific, and worth checking directly for any system")
print("  you deploy, including pgvector, M6-L08).")

print("\nDone.")
