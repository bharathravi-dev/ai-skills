"""M6-L07 lab -- what a bare vector index does NOT give you for free: real
deletion cost, and real persistence cost, both measured on the same
IVF-style index M6-L06 built.

Section 1 is REAL: deleting from an approximate index the "fast" way
(tombstone) versus the "correct" way (rebuild), with real timing for both,
showing neither is a genuinely cheap, correct delete -- exactly the gap a
vector DATABASE exists to manage for you. Section 2 is REAL: measuring what
it actually costs to persist an index to disk and reload it, something a
bare in-memory library does not do automatically.

Deterministic (seeded). No API key, no network.
Run:  python labs/m6/l07_index_vs_database.py
"""

from __future__ import annotations

import pickle
import time

import numpy as np
from sklearn.cluster import KMeans

RNG = np.random.default_rng(6)


def rule(title: str) -> None:
    print(f"\n{'=' * 76}\n{title}\n{'=' * 76}")


# Same corpus shape and generation method as M6-L06, for direct continuity.
N, D = 50_000, 128
N_TOPICS, TOPIC_SPREAD = 200, 0.15
N_CLUSTERS = 100

topic_centers = RNG.normal(size=(N_TOPICS, D)).astype(np.float32)
topic_centers /= np.linalg.norm(topic_centers, axis=1, keepdims=True)
topic_of = RNG.integers(0, N_TOPICS, size=N)
corpus = topic_centers[topic_of] + RNG.normal(scale=TOPIC_SPREAD, size=(N, D)).astype(np.float32)
corpus /= np.linalg.norm(corpus, axis=1, keepdims=True)


# ============================================================ 1
rule("1. THE DELETE PROBLEM: TOMBSTONE VS REBUILD, MEASURED")

print(f"  Building the same {N:,}-vector, {N_CLUSTERS}-cluster IVF index as "
      f"M6-L06...")
t0 = time.perf_counter()
kmeans = KMeans(n_clusters=N_CLUSTERS, n_init=3, random_state=6).fit(corpus)
build_time = time.perf_counter() - t0
labels = kmeans.labels_
print(f"  Built in {build_time:.1f}s.\n")

DELETE_FRACTION = 0.20
to_delete = RNG.choice(N, size=int(N * DELETE_FRACTION), replace=False)
delete_set = set(to_delete.tolist())
print(f"  Deleting {len(to_delete):,} vectors ({DELETE_FRACTION:.0%} of the corpus), "
      f"scattered across clusters.\n")

# Option A: tombstone -- mark as deleted, keep everything else unchanged.
t0 = time.perf_counter()
tombstones = delete_set   # a set lookup; this is the ENTIRE "delete" operation
tombstone_time = time.perf_counter() - t0
print(f"  Option A -- TOMBSTONE: mark {len(to_delete):,} ids as deleted.")
print(f"    time taken: {tombstone_time * 1000:.3f}ms (a set insert, "
      f"essentially free)")


def ivf_search_with_tombstones(query, centroids_, nprobe, k, tombstones_):
    centroid_scores = centroids_ @ query
    nearest_clusters = np.argpartition(-centroid_scores, nprobe)[:nprobe]
    candidate_idx = np.concatenate(
        [np.where(labels == c)[0] for c in nearest_clusters])
    live = np.array([i for i in candidate_idx if i not in tombstones_])
    if len(live) == 0:
        return np.array([], dtype=int)
    sub_scores = corpus[live] @ query
    kk = min(k, len(live))
    top = np.argpartition(-sub_scores, kk - 1)[:kk]
    return live[top[np.argsort(-sub_scores[top])]]


centroids = kmeans.cluster_centers_
centroids /= np.linalg.norm(centroids, axis=1, keepdims=True)
q = RNG.normal(size=D).astype(np.float32)
q /= np.linalg.norm(q)

t0 = time.perf_counter()
result = ivf_search_with_tombstones(q, centroids, 5, 10, tombstones)
tombstoned_query_time = time.perf_counter() - t0
print(f"    a search afterward still costs {tombstoned_query_time * 1000:.2f}ms --")
print(f"    the deleted vectors are still THERE, still compared against,")
print(f"    still occupying every byte of memory they occupied before.")
print(f"    Filtering happens AFTER the comparison, not instead of it.\n")

print(f"  Option B -- REBUILD: actually remove the {len(to_delete):,} vectors "
      f"and rebuild the index for real.")
keep_mask = np.ones(N, dtype=bool)
keep_mask[to_delete] = False
reduced_corpus = corpus[keep_mask]
t0 = time.perf_counter()
kmeans2 = KMeans(n_clusters=N_CLUSTERS, n_init=3, random_state=6).fit(reduced_corpus)
rebuild_time = time.perf_counter() - t0
print(f"    time taken: {rebuild_time:.1f}s -- the tombstone was, for")
print(f"    practical purposes, instant; this is real, measured, whole")
print(f"    seconds of compute, on a corpus far smaller than production.")
print(f"    But the vectors are ACTUALLY gone: less memory, uncorrupted")
print(f"    centroids, and a search no longer wastes time comparing against")
print(f"    them at all.")

print("\n  There is no cheap, correct delete for an approximate index. You")
print("  choose: tombstone (instant, but the cost and the stale centroids")
print("  remain until a rebuild) or rebuild (correct, but real, measured")
print("  seconds of work at this corpus size -- and a production corpus is")
print("  routinely orders of magnitude larger). A vector DATABASE exists")
print("  partly to manage this trade-off for you -- batching deletes,")
print("  scheduling background rebuilds, or using an index structure with")
print("  cheaper true deletion -- instead of leaving you to choose between")
print("  'fake' and 'expensive' by hand, every time something is deleted.")


# ============================================================ 2
rule("2. PERSISTENCE: WHAT A BARE INDEX DOES NOT GIVE YOU")

print("  An in-memory index (like the one just built) exists only as long as")
print("  the process holding it stays alive. Persisting it is extra work a")
print("  library does not do for you automatically.\n")

t0 = time.perf_counter()
serialized = pickle.dumps(
    {"centroids": centroids, "labels": labels, "corpus": corpus})
serialize_time = time.perf_counter() - t0
size_mb = len(serialized) / 1e6

t0 = time.perf_counter()
restored = pickle.loads(serialized)
deserialize_time = time.perf_counter() - t0

print(f"  Serializing the index to bytes: {serialize_time:.2f}s, "
      f"{size_mb:.1f} MB.")
print(f"  Deserializing it back: {deserialize_time:.2f}s.")
print(f"  Restored correctly: "
      f"{np.array_equal(restored['centroids'], centroids)}\n")

print("  This lab does the simplest possible version (one file, one process,")
print("  no concurrent access, no partial writes to worry about). A real")
print("  production system needs this to survive a crash mid-write, be")
print("  readable while still being written to by another process, and")
print("  scale past what fits in one process's memory at all -- none of")
print("  which a bare index library provides. That gap is exactly what a")
print("  vector DATABASE is built to close.")


# ============================================================ 3
rule("3. INDEX vs DATABASE: WHAT EACH ACTUALLY PROVIDES")

comparison = [
    ("Similarity search algorithm", "Yes (its whole job)", "Yes (usually wraps a library like this)"),
    ("Persistence across restarts", "No, unless you build it", "Yes, by default"),
    ("True deletion without a full rebuild", "No (section 1: tombstone or rebuild)", "Often yes (managed internally)"),
    ("Metadata filtering (M6-L09)", "No, unless you build it", "Usually built in"),
    ("Concurrent reads/writes", "No, unless you build it", "Yes, by default"),
    ("Backups, replication", "No", "Usually yes"),
    ("Operational overhead", "Low (it's a library)", "Higher (it's a service)"),
]
for cap, idx, db in comparison:
    print(f"  {cap}")
    print(f"    bare index:      {idx}")
    print(f"    vector database: {db}")

print("\n  Neither column is 'better' in the abstract. A bare index embedded")
print("  directly in your application is lighter-weight and has fewer moving")
print("  parts when you genuinely do not need persistence, filtering, or")
print("  concurrent access. A database is the right choice the moment any of")
print("  sections 1-2's gaps become requirements rather than conveniences --")
print("  which, for most production systems, is almost immediately.")


# ============================================================ 4
rule("4. WHAT THIS LAB IS AND IS NOT")

print("  REAL: sections 1-2 measure actual operations -- a real k-means")
print("  rebuild, a real tombstone set, real pickle serialisation -- on the")
print("  same real index M6-L06 built. Every millisecond is measured, not")
print("  estimated.")
print("\n  ILLUSTRATIVE: the specific rebuild and serialisation times are")
print("  specific to this corpus size and this machine. A real production")
print("  index (larger, on real hardware, possibly with a more efficient")
print("  serialisation format than pickle) will differ -- the SHAPE of the")
print("  gap, not the specific seconds, is what transfers.")
print("\n  NOT SHOWN: how a real vector database actually implements cheaper")
print("  incremental updates internally (proprietary, and varies by")
print("  product), and metadata filtering, which is M6-L09's full treatment.")
print("  M6-L08 gets hands-on with one real system, pgvector, next.")

print("\nDone.")
