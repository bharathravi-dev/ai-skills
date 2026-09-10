"""M6-L05 lab -- exact nearest-neighbour search: the algorithm, and its real,
measured cost as corpus size and dimension count grow.

Section 1 is a real, hand-verifiable brute-force search on a tiny corpus.
Sections 2 and 3 are REAL WALL-CLOCK TIMING -- actual numpy brute-force
search run at increasing scale, not simulated or estimated. Timings are
specific to the machine that ran them and will differ on yours; the SHAPE
(linear in corpus size, linear in dimensions) is what transfers.

Deterministic corpus generation (seeded). No API key, no network.
Run:  python labs/m6/l05_exact_nn_search.py
"""

from __future__ import annotations

import time

import numpy as np

RNG = np.random.default_rng(6)


def rule(title: str) -> None:
    print(f"\n{'=' * 76}\n{title}\n{'=' * 76}")


def exact_top_k(query: np.ndarray, corpus: np.ndarray, k: int) -> np.ndarray:
    """Brute-force exact nearest neighbours by cosine similarity.
    corpus: (N, d) array, assumed unit-normalised (so dot product = cosine)."""
    scores = corpus @ query          # (N,) -- one dot product per row, vectorised
    top_idx = np.argpartition(-scores, k)[:k]
    return top_idx[np.argsort(-scores[top_idx])]


# ============================================================ 1
rule("1. EXACT NEAREST-NEIGHBOUR SEARCH: THE ALGORITHM")

toy_corpus = {
    "D1": [1.0, 0.0, 0.0],
    "D2": [0.9, 0.1, 0.0],
    "D3": [0.0, 1.0, 0.0],
    "D4": [0.0, 0.9, 0.1],
    "D5": [0.0, 0.0, 1.0],
}
query = np.array([1.0, 0.0, 0.0])
print("  A 3-dimensional toy corpus and a query. Exact search means:")
print("  compute similarity to EVERY vector, then keep the best k.\n")
print(f"  {'doc':<5}{'vector':<20}{'cosine to query'}")
scores = {}
for doc_id, vec in toy_corpus.items():
    v = np.array(vec)
    scores[doc_id] = float(np.dot(query, v) / (np.linalg.norm(query) * np.linalg.norm(v)))
    print(f"  {doc_id:<5}{str(vec):<20}{scores[doc_id]:.4f}")

ranked = sorted(scores, key=lambda d: -scores[d])
print(f"\n  Exact top-2: {ranked[:2]}")
print("\n  This is the ENTIRE algorithm: no shortcuts, no approximation. It")
print("  is also the definition of 'correct' -- every faster method in this")
print("  module (M6-L06 onward) is judged by how closely it matches what")
print("  this brute-force scan would have found.")


# ============================================================ 2
rule("2. REAL TIMING: HOW SEARCH TIME GROWS WITH CORPUS SIZE")

D_FIXED = 384          # a common real embedding dimension (M6-L02)
K = 10
CORPUS_SIZES = [1_000, 10_000, 100_000, 500_000, 1_000_000]

print(f"  Dimension fixed at {D_FIXED}, k={K}. Real corpora of random unit")
print(f"  vectors, real wall-clock time for ONE brute-force query "
      f"(averaged over 5 runs):\n")
print(f"  {'corpus size (N)':>16}{'time/query':>14}{'vs N=1,000':>13}{'time/query/vector':>20}")
base_time = None
for n in CORPUS_SIZES:
    corpus = RNG.normal(size=(n, D_FIXED)).astype(np.float32)
    corpus /= np.linalg.norm(corpus, axis=1, keepdims=True)
    q = RNG.normal(size=D_FIXED).astype(np.float32)
    q /= np.linalg.norm(q)

    times = []
    for _ in range(5):
        t0 = time.perf_counter()
        exact_top_k(q, corpus, K)
        times.append(time.perf_counter() - t0)
    avg = sum(times) / len(times)
    if base_time is None:
        base_time = avg
    per_vector_ns = (avg / n) * 1e9
    print(f"  {n:>16,}{avg * 1000:>11.2f}ms{avg / base_time:>12.1f}x"
          f"{per_vector_ns:>17.1f}ns")

print("\n  Time per query scales roughly LINEARLY with corpus size -- 1,000x")
print("  more vectors costs roughly 1,000x more time, because every single")
print("  vector must be compared against the query. There is no shortcut in")
print("  this algorithm; correctness REQUIRES checking everything.")
print("\n  [Timings are wall-clock on THIS machine, this run, and will differ")
print("  on yours -- the near-linear SHAPE is the result that transfers,")
print("  not the specific millisecond figures.]")


# ============================================================ 3
rule("3. REAL TIMING: HOW SEARCH TIME GROWS WITH DIMENSION COUNT")

N_FIXED = 200_000
DIMENSIONS = [128, 384, 768, 1536, 3072]

print(f"  Corpus size fixed at {N_FIXED:,}. Real timing as dimension count varies:\n")
print(f"  {'dimensions':>11}{'time/query':>14}{'vs 128 dims':>14}")
base_time_d = None
for d in DIMENSIONS:
    corpus = RNG.normal(size=(N_FIXED, d)).astype(np.float32)
    corpus /= np.linalg.norm(corpus, axis=1, keepdims=True)
    q = RNG.normal(size=d).astype(np.float32)
    q /= np.linalg.norm(q)

    times = []
    for _ in range(5):
        t0 = time.perf_counter()
        exact_top_k(q, corpus, K)
        times.append(time.perf_counter() - t0)
    avg = sum(times) / len(times)
    if base_time_d is None:
        base_time_d = avg
    print(f"  {d:>11}{avg * 1000:>11.2f}ms{avg / base_time_d:>13.1f}x")

print("\n  Time also scales roughly linearly with dimension count -- each")
print("  additional dimension is one more multiplication per vector, per")
print("  query. Combined with section 2: exact search cost is O(N x d) per")
print("  query. Both a bigger corpus AND a bigger embedding model make")
print("  every single query more expensive, independently.")


# ============================================================ 4
rule("4. EXTRAPOLATING TO PRODUCTION SCALE")

measured_ns_per_vector = per_vector_ns   # from section 2's last (largest) measurement
LATENCY_BUDGET_MS = 100

print(f"  Using this run's measured per-vector cost ({measured_ns_per_vector:.1f}ns) at "
      f"{D_FIXED} dimensions:\n")
print(f"  {'corpus size':>14}{'estimated time/query':>22}")
for n in (1_000_000, 10_000_000, 100_000_000, 1_000_000_000):
    est_ms = n * measured_ns_per_vector / 1e6
    print(f"  {n:>14,}{est_ms:>19.1f}ms")

crossover_n = LATENCY_BUDGET_MS * 1e6 / measured_ns_per_vector
print(f"\n  At a {LATENCY_BUDGET_MS}ms latency budget, this measured rate implies exact")
print(f"  search stops fitting the budget somewhere around "
      f"{crossover_n:,.0f} vectors.")
print("  A production system with tens or hundreds of millions of vectors")
print("  -- an entirely ordinary size for real search or RAG applications --")
print("  is, on these numbers, one to three orders of magnitude past where")
print("  exact search alone can meet a normal interactive latency budget.")
print("  This is the exact, quantified reason M6-L06's approximate methods")
print("  exist: not because exact search is 'wrong', but because it is the")
print("  one thing that cannot be made fast enough at this scale by")
print("  definition -- checking fewer than all N vectors is what makes a")
print("  method approximate in the first place.")


# ============================================================ 5
rule("5. WHAT THIS LAB IS AND IS NOT")

print("  REAL: every millisecond in sections 2-3 is an actual measured")
print("  wall-clock time from running real vectorised numpy search on real")
print("  random unit vectors, on the machine executing this script.")
print("\n  MACHINE-SPECIFIC: the exact timings will differ on different")
print("  hardware, numpy builds, and load conditions. Re-run this lab on")
print("  your own machine before quoting a specific number to anyone.")
print("\n  ILLUSTRATIVE: section 4's crossover point depends entirely on the")
print("  measured rate above and the chosen 100ms budget -- recompute both")
print("  for your own system's real embedding dimension and real latency")
print("  requirement.")
print("\n  NOT SHOWN: how approximate methods (M6-L06) actually achieve")
print("  sub-linear query time, and how exact search is used as the")
print("  ground-truth reference for measuring an approximate method's")
print("  recall -- both are M6-L06's job, building directly on the cost")
print("  measured here.")

print("\nDone.")
