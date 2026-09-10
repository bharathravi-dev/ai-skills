"""M6-L06 lab -- approximate nearest-neighbour search: real recall-vs-speed
measurements for a clustering-based (IVF-style) ANN method, using M6-L05's
exact brute-force search as the ground truth it is measured against, plus a
small, hand-traceable graph search illustrating HNSW's different mechanism.

Sections 1-2 are REAL: a genuine clustering-based approximate index (the
same family as IVF-Flat in real vector databases), built with real k-means,
measured for real recall@k against real exact-search ground truth, and real
wall-clock speedup. Section 3 is a small, hand-built graph -- HNSW's
"navigable small world" idea traced by hand, not a full HNSW implementation,
which is considerably more involved than fits a teaching lab.

Deterministic (seeded). No API key, no network, no model download.
Run:  python labs/m6/l06_approximate_nn_hnsw.py
"""

from __future__ import annotations

import time

import numpy as np
from sklearn.cluster import KMeans

RNG = np.random.default_rng(6)


def rule(title: str) -> None:
    print(f"\n{'=' * 76}\n{title}\n{'=' * 76}")


def exact_top_k(query, corpus, k):
    scores = corpus @ query
    top_idx = np.argpartition(-scores, k)[:k]
    return top_idx[np.argsort(-scores[top_idx])]


# ============================================================ 1
rule("1. A REAL APPROXIMATE INDEX: CLUSTER FIRST, SEARCH ONLY THE NEAREST CLUSTERS")

N, D, K = 50_000, 128, 10
N_CLUSTERS = 100
N_TOPICS = 200          # genuine underlying structure -- more, and finer-grained,
                        # than the index's own 100 clusters, so this is not a
                        # trivially easy 1:1 match between "topic" and "cluster"
TOPIC_SPREAD = 0.15

print(f"  {N:,} vectors, {D} dimensions -- the same shape of problem M6-L05")
print(f"  measured exact search's cost for. Generated with {N_TOPICS} genuine")
print(f"  underlying topics (vectors scattered around {N_TOPICS} random centres),")
print(f"  the way real document embeddings cluster by subject -- NOT pure")
print(f"  unstructured noise, which has no exploitable structure for any")
print(f"  clustering-based index to find.\n")

topic_centers = RNG.normal(size=(N_TOPICS, D)).astype(np.float32)
topic_centers /= np.linalg.norm(topic_centers, axis=1, keepdims=True)
topic_of = RNG.integers(0, N_TOPICS, size=N)
corpus = topic_centers[topic_of] + RNG.normal(scale=TOPIC_SPREAD, size=(N, D)).astype(np.float32)
corpus /= np.linalg.norm(corpus, axis=1, keepdims=True)

print(f"  Building a real k-means index: {N_CLUSTERS} clusters over "
      f"{N:,} vectors (this takes a few seconds)...")
t0 = time.perf_counter()
kmeans = KMeans(n_clusters=N_CLUSTERS, n_init=3, random_state=6).fit(corpus)
build_time = time.perf_counter() - t0
centroids = kmeans.cluster_centers_
centroids /= np.linalg.norm(centroids, axis=1, keepdims=True)
labels = kmeans.labels_
print(f"  Index built in {build_time:.1f}s. Average cluster size: "
      f"{N / N_CLUSTERS:.0f} vectors.\n")

CLUSTER_MEMBERS = {c: np.where(labels == c)[0] for c in range(N_CLUSTERS)}


def ivf_search(query, nprobe, k):
    """Approximate search: check the nprobe nearest CENTROIDS, then exact
    search only within those clusters' members."""
    centroid_scores = centroids @ query
    nearest_clusters = np.argpartition(-centroid_scores, nprobe)[:nprobe]
    candidate_idx = np.concatenate([CLUSTER_MEMBERS[c] for c in nearest_clusters])
    if len(candidate_idx) <= k:
        return candidate_idx
    sub_scores = corpus[candidate_idx] @ query
    top = np.argpartition(-sub_scores, k)[:k]
    return candidate_idx[top[np.argsort(-sub_scores[top])]]


print("  The index: at query time, compare against the 100 CENTROIDS first")
print("  (cheap), then exact-search only inside the closest cluster(s) --")
print("  never touching the other clusters' vectors at all.")


# ============================================================ 2
rule("2. RECALL vs SPEED: A REAL, TUNABLE TRADE-OFF")

N_QUERIES = 30
query_topics = RNG.integers(0, N_TOPICS, size=N_QUERIES)
queries = (topic_centers[query_topics]
           + RNG.normal(scale=TOPIC_SPREAD, size=(N_QUERIES, D)).astype(np.float32))
queries /= np.linalg.norm(queries, axis=1, keepdims=True)

print(f"  {N_QUERIES} queries, drawn from the same topic structure as the corpus")
print(f"  (a realistic query resembles the kind of content it searches for).")
print(f"  For each, exact search gives the TRUE top-{K} (M6-L05's method) --")
print(f"  the ground truth every recall number below is measured against.\n")

ground_truth = [set(exact_top_k(q, corpus, K)) for q in queries]

t0 = time.perf_counter()
for q in queries:
    exact_top_k(q, corpus, K)
exact_time_per_query = (time.perf_counter() - t0) / N_QUERIES

print(f"  {'nprobe':>7}{'avg recall@10':>15}{'time/query':>13}{'speedup vs exact':>18}")
for nprobe in (1, 2, 5, 10, 20, 50):
    t0 = time.perf_counter()
    recalls = []
    for q, truth in zip(queries, ground_truth):
        found = set(ivf_search(q, nprobe, K))
        recalls.append(len(found & truth) / K)
    elapsed = (time.perf_counter() - t0) / N_QUERIES
    avg_recall = sum(recalls) / len(recalls)
    speedup = exact_time_per_query / elapsed if elapsed > 0 else float("inf")
    print(f"  {nprobe:>7}{avg_recall:>15.1%}{elapsed * 1000:>11.2f}ms{speedup:>17.1f}x")

print(f"\n  Exact search (M6-L05's method), for comparison: "
      f"{exact_time_per_query * 1000:.2f}ms/query, 100% recall by definition.")
print("\n  Read left to right: checking only 1 cluster is fast but misses real")
print("  matches -- recall well under 100%. Checking more clusters (larger")
print("  'nprobe') raises recall back toward exact search's, at the cost of")
print("  approaching exact search's own time. THIS is the trade-off every")
print("  approximate method makes, HNSW included -- nprobe here plays the")
print("  same role as HNSW's 'ef' search-width parameter: how hard to look")
print("  before stopping.")


# ============================================================ 3
rule("3. HNSW'S DIFFERENT MECHANISM: A GRAPH, TRACED BY HAND")

print("  A different ANN family: instead of clusters, build a graph where")
print("  each vector is a node connected to a few nearby neighbours, and")
print("  search by GREEDILY walking toward the query, one hop at a time.\n")

# A tiny, hand-built 2D graph -- coordinates chosen so distances are easy to verify.
GRAPH_NODES = {
    "A": (0, 0), "B": (1, 0.2), "C": (2, 0.5), "D": (3, 1.5),
    "E": (4, 3.0), "F": (1, 3.0), "G": (2.5, 3.5), "H": (5, 4.0),
}
# Each node's edges: the symmetric closure of every node's true 2 nearest
# neighbours (computed exactly, then unioned so the graph is bidirectional --
# which is why a couple of nodes end up with a 3rd edge, same as real
# k-NN graphs).
GRAPH_EDGES = {
    "A": ["B", "C"], "B": ["A", "C"], "C": ["A", "B", "D"],
    "D": ["C", "E", "F"], "E": ["D", "H", "G"], "F": ["G", "D"],
    "G": ["E", "F", "H"], "H": ["E", "G"],
}
QUERY_POINT = (4.8, 3.6)   # closest to H


def dist(p, q):
    return ((p[0] - q[0]) ** 2 + (p[1] - q[1]) ** 2) ** 0.5


print(f"  8 nodes, each connected to its nearest neighbours (a symmetrised"
      f" k-NN graph). Query point: "
      f"{QUERY_POINT}.\n")
print(f"  {'node':<6}{'coords':<12}{'distance to query'}")
true_distances = {n: dist(c, QUERY_POINT) for n, c in GRAPH_NODES.items()}
for n in GRAPH_NODES:
    print(f"  {n:<6}{str(GRAPH_NODES[n]):<12}{true_distances[n]:.3f}")
true_nearest = min(true_distances, key=true_distances.get)
print(f"\n  True nearest node (by checking all 8, i.e. exact search): "
      f"{true_nearest!r}\n")

# Greedy graph walk from a fixed entry point.
entry = "A"
current = entry
visited = [current]
while True:
    neighbours = GRAPH_EDGES[current]
    best_neighbour = min(neighbours, key=lambda n: true_distances[n])
    if true_distances[best_neighbour] < true_distances[current]:
        current = best_neighbour
        visited.append(current)
    else:
        break

print(f"  Greedy graph search, starting at {entry!r}: visits "
      f"{visited} ({len(visited)} of 8 nodes),")
print(f"  then stops because no neighbour of {current!r} is closer than "
      f"{current!r} itself.")
print(f"  Found: {current!r}. True nearest: {true_nearest!r}. "
      f"Match: {current == true_nearest}.")
print(f"\n  Only {len(visited)} of {len(GRAPH_NODES)} nodes were ever compared to the")
print("  query -- at real scale (millions of nodes, more layers, more edges")
print("  per node) this is what makes HNSW sub-linear: it never scans the")
print("  whole graph, only a short greedy path through it, layer by layer.")
print("\n  The failure mode is different from clustering's. IVF search (sections 1-2)")
print("  can miss the right answer by checking the wrong CLUSTER. A graph")
print("  search can miss it by reaching a LOCAL MINIMUM -- a node with no")
print("  closer neighbour, even though a closer node exists elsewhere in the")
print("  graph, unreachable from the greedy path taken. Real HNSW mitigates")
print("  this with multiple layers and multiple entry points, not shown in")
print("  this single-layer, hand-traced example.")


# ============================================================ 4
rule("4. WHAT THIS LAB IS AND IS NOT")

print("  REAL: sections 1-2 build and query an actual clustering-based")
print("  approximate index (the same family as IVF-Flat in real vector")
print("  databases) using real k-means and real brute-force sub-search, and")
print("  measure real recall against real exact-search ground truth (M6-L05).")
print("\n  HAND-TRACED, NOT A FULL IMPLEMENTATION: section 3's graph is 8")
print("  nodes with manually assigned edges, illustrating HNSW's core greedy-")
print("  search MECHANISM. Real HNSW builds its graph automatically, uses")
print("  multiple hierarchical layers, and includes construction-time")
print("  choices (M, ef_construction) this lab does not implement.")
print("\n  ILLUSTRATIVE: exact recall/speed numbers depend on this specific")
print("  corpus, cluster count, and hardware. Re-measure on your own data")
print("  before choosing nprobe or any ANN parameter for a real system.")
print("\n  NOT SHOWN: how to choose between IVF-style and graph-based (HNSW)")
print("  indexes for a real system -- both are real, deployed families with")
print("  different trade-offs, and pgvector (M6-L08) supports both.")

print("\nDone.")
