"""M6-L10 lab -- what happens to index quality as data is added without a
rebuild (measured, real), and what a full re-embedding migration costs
(arithmetic, extending M6-L06/M6-L07's own measured rebuild times).

M6-L07 already measured deletion's cost (tombstone vs rebuild). This lab
measures the other half of the lifecycle: ADDING data incrementally, and
what degrades if you never rebuild -- plus what re-embedding an entire
corpus under a new, incompatible model (M6-L02) actually costs at scale.

Deterministic (seeded). No API key, no network.
Run:  python labs/m6/l10_indexing_updates.py
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


# Same style of corpus as M6-L06/L07/L09, but with a deliberate, realistic
# twist: the vectors added LATER introduce genuinely NEW topics the original
# index never saw -- new content in a growing corpus is often about
# emerging subjects, not a random resample of the old ones.
N_TOTAL, D = 50_000, 128
N_INITIAL = 25_000          # what the index was originally built on
N_TOPICS_OLD, N_TOPICS_NEW = 150, 50    # 200 total, but 50 are unseen initially
TOPIC_SPREAD = 0.15
N_CLUSTERS = 100
K = 10
N_TOPICS = N_TOPICS_OLD + N_TOPICS_NEW

topic_centers = RNG.normal(size=(N_TOPICS, D)).astype(np.float32)
topic_centers /= np.linalg.norm(topic_centers, axis=1, keepdims=True)

# The initial corpus is drawn ONLY from the old topics.
topic_of_initial = RNG.integers(0, N_TOPICS_OLD, size=N_INITIAL)
initial_corpus = (topic_centers[topic_of_initial]
                   + RNG.normal(scale=TOPIC_SPREAD, size=(N_INITIAL, D)).astype(np.float32))
initial_corpus /= np.linalg.norm(initial_corpus, axis=1, keepdims=True)

# The added corpus is drawn from ALL topics, old and new -- realistic: new
# content keeps discussing old subjects too, plus genuinely new ones.
N_ADDED = N_TOTAL - N_INITIAL
topic_of_added = RNG.integers(0, N_TOPICS, size=N_ADDED)
added_corpus = (topic_centers[topic_of_added]
                + RNG.normal(scale=TOPIC_SPREAD, size=(N_ADDED, D)).astype(np.float32))
added_corpus /= np.linalg.norm(added_corpus, axis=1, keepdims=True)

corpus = np.concatenate([initial_corpus, added_corpus], axis=0)

# Queries are drawn from ALL topics -- representative of what the FINAL,
# grown corpus actually contains, including the topics the original index
# never saw.
N_QUERIES = 20
query_topics = RNG.integers(0, N_TOPICS, size=N_QUERIES)
queries = (topic_centers[query_topics]
           + RNG.normal(scale=TOPIC_SPREAD, size=(N_QUERIES, D)).astype(np.float32))
queries /= np.linalg.norm(queries, axis=1, keepdims=True)

ground_truth = [set(exact_top_k(q, corpus, K)) for q in queries]   # over the FULL, final corpus


def recall_at_k(found_idx, truth_set):
    return len(set(found_idx) & truth_set) / len(truth_set)


# ============================================================ 1
rule("1. THREE STATES OF THE SAME INDEX, MEASURED AGAINST THE SAME QUERIES")

print(f"  A corpus that grows from {N_INITIAL:,} to {N_TOTAL:,} vectors. Three")
print(f"  ways the index could reflect that growth, all measured against")
print(f"  the SAME {N_QUERIES} queries and the SAME ground truth (exact search")
print(f"  over the full, final {N_TOTAL:,}-vector corpus).\n")

print(f"  Building the ORIGINAL index on the first {N_INITIAL:,} vectors only...")
t0 = time.perf_counter()
km_initial = KMeans(n_clusters=N_CLUSTERS, n_init=3, random_state=6).fit(initial_corpus)
print(f"  Built in {time.perf_counter() - t0:.1f}s.")
initial_centroids = km_initial.cluster_centers_ / np.linalg.norm(
    km_initial.cluster_centers_, axis=1, keepdims=True)
initial_labels = km_initial.labels_
initial_members = {c: np.where(initial_labels == c)[0] for c in range(N_CLUSTERS)}


def ivf_search(query, centroids_, members_, corpus_, nprobe, k):
    centroid_scores = centroids_ @ query
    nearest = np.argpartition(-centroid_scores, nprobe)[:nprobe]
    pool = np.concatenate([members_[c] for c in nearest])
    sub_scores = corpus_[pool] @ query
    kk = min(k, len(pool))
    top = np.argpartition(-sub_scores, kk - 1)[:kk]
    return pool[top[np.argsort(-sub_scores[top])]]


NPROBE = 10

# State A: original index, never touched -- the added vectors are simply INVISIBLE.
recalls_a = []
for q, truth in zip(queries, ground_truth):
    found = ivf_search(q, initial_centroids, initial_members, initial_corpus, NPROBE, K)
    recalls_a.append(recall_at_k(found, truth))
print(f"\n  State A -- index never updated at all, {N_TOTAL - N_INITIAL:,} newer "
      f"vectors simply never added:")
print(f"    avg recall@{K}: {sum(recalls_a) / len(recalls_a):.1%}")

# State B: incrementally ADD the new vectors, assigning each to its nearest
# EXISTING centroid -- no re-fit of k-means at all.
t0 = time.perf_counter()
new_assignments = np.argmax(added_corpus @ initial_centroids.T, axis=1)
incremental_members = {c: list(initial_members[c]) for c in range(N_CLUSTERS)}
for local_i, cluster in enumerate(new_assignments):
    incremental_members[int(cluster)].append(N_INITIAL + local_i)
incremental_members = {c: np.array(v) for c, v in incremental_members.items()}
incremental_add_time = time.perf_counter() - t0
recalls_b = []
for q, truth in zip(queries, ground_truth):
    found = ivf_search(q, initial_centroids, incremental_members, corpus, NPROBE, K)
    recalls_b.append(recall_at_k(found, truth))
print(f"\n  State B -- {N_TOTAL - N_INITIAL:,} new vectors added incrementally "
      f"(assigned to nearest EXISTING centroid, {incremental_add_time * 1000:.1f}ms total, no rebuild):")
print(f"    avg recall@{K}: {sum(recalls_b) / len(recalls_b):.1%}")

# State C: full rebuild on all N_TOTAL vectors.
t0 = time.perf_counter()
km_full = KMeans(n_clusters=N_CLUSTERS, n_init=3, random_state=6).fit(corpus)
rebuild_time = time.perf_counter() - t0
full_centroids = km_full.cluster_centers_ / np.linalg.norm(
    km_full.cluster_centers_, axis=1, keepdims=True)
full_labels = km_full.labels_
full_members = {c: np.where(full_labels == c)[0] for c in range(N_CLUSTERS)}
recalls_c = []
for q, truth in zip(queries, ground_truth):
    found = ivf_search(q, full_centroids, full_members, corpus, NPROBE, K)
    recalls_c.append(recall_at_k(found, truth))
print(f"\n  State C -- full rebuild on all {N_TOTAL:,} vectors "
      f"({rebuild_time:.1f}s):")
print(f"    avg recall@{K}: {sum(recalls_c) / len(recalls_c):.1%}")

print("\n  Read all three together. State A is the cost of forgetting to add")
print("  new data at all -- half the corpus is searchable by NOBODY. State B")
print("  is cheap (milliseconds) and searchable, but its centroids were")
print("  computed on half the eventual data, so recall sits measurably below")
print("  a full rebuild's. State C is correct, and costs real, measured")
print("  seconds -- the same trade-off M6-L07 measured for deletion, now")
print("  measured for the addition side of the same lifecycle.")


# ============================================================ 2
rule("2. RE-EMBEDDING: WHY YOU CANNOT MIX MODELS, AND WHAT MIGRATING COSTS")

print("  M6-L02 measured that two embedding models -- or two versions of")
print("  'the same' model -- produce INCOMPATIBLE vector spaces, even at")
print("  identical dimensionality. Upgrading the embedding model therefore")
print("  means every vector must be recomputed AND the index rebuilt --")
print("  there is no partial or incremental version of this operation.\n")

print(f"  Using this run's measured rebuild time as a baseline "
      f"({rebuild_time:.1f}s for {N_TOTAL:,} vectors):\n")
print(f"  {'corpus size':>14}{'estimated re-embed+rebuild time':>34}")
per_vector_rebuild = rebuild_time / N_TOTAL
for n in (100_000, 1_000_000, 10_000_000):
    est_seconds = n * per_vector_rebuild
    if est_seconds < 3600:
        est_str = f"{est_seconds / 60:.1f} min"
    else:
        est_str = f"{est_seconds / 3600:.1f} hours"
    print(f"  {n:>14,}{est_str:>34}")

print("\n  (This scales the k-means REBUILD cost alone -- a real migration")
print("  also pays to re-embed every document through the new model, a")
print("  separate, often larger cost this lab does not measure.)")

print("\n  Because this takes real, non-trivial time -- and the service")
print("  cannot stop answering queries while it happens -- the standard")
print("  pattern is NOT to rebuild in place:\n")
print("    1. Build the NEW index (new embeddings, new model) alongside the")
print("       OLD one, which keeps serving every query throughout.")
print("    2. Validate the new index's recall against a held-out query set")
print("       (M5-L18's discipline, applied to a vector index) before")
print("       trusting it.")
print("    3. Cut traffic over to the new index atomically, only once step 2")
print("       passes -- never gradually, since a query landing on the OLD")
print("       index and one landing on the NEW index are answered from two")
print("       INCOMPATIBLE vector spaces (M6-L02), not two versions of one")
print("       answer.")
print("    4. Decommission the old index only after the cutover is confirmed")
print("       stable.")
print("\n  This is the vector-index-specific version of a blue-green")
print("  deployment -- necessary here specifically because M6-L02's")
print("  incompatibility means there is no safe partial or gradual state.")


# ============================================================ 3
rule("3. WHAT THIS LAB IS AND IS NOT")

print("  REAL: section 1's three recall measurements and all timings are")
print("  from actually building, updating, and querying real indexes over")
print("  a real (if synthetic) corpus -- nothing is simulated.")
print("\n  ILLUSTRATIVE: the specific recall percentages, corpus size, and")
print("  timings are tied to this lab's synthetic data and this machine.")
print("  Section 2's extrapolation reuses this run's measured rebuild rate;")
print("  re-embedding cost (calling the model itself) is separate and often")
print("  larger, and is not measured here at all.")
print("\n  NOT SHOWN: how a real vector database automates the blue-green")
print("  pattern internally, and how to detect, in production, that")
print("  incremental-only updates (state B) have degraded recall enough to")
print("  need a rebuild -- both are engineering choices specific to your")
print("  own monitoring and operational setup.")

print("\nDone.")
