"""M3-L02: dot products, norms, cosine - and where each one fails.

Requires numpy:
    source .venv/bin/activate
    python labs/m3/l02_similarity.py
"""

from __future__ import annotations

import time

import numpy as np

LINE = "-" * 74

QUERY = np.array([0.8, 0.2, 0.1, 0.0])
CORPUS = np.array([
    [0.9, 0.1, 0.0, 0.2],      # doc0 refund policy details
    [0.1, 0.0, 0.9, 0.3],      # doc1 shipping times
    [1.6, 0.4, 0.2, 0.0],      # doc2 same direction as query, double length
])
NAMES = ["doc0 refund policy details", "doc1 shipping times",
         "doc2 refund policy (x2 length)"]


def section(title: str) -> None:
    print()
    print(LINE)
    print(title)
    print(LINE)


def cosine(a: np.ndarray, b: np.ndarray) -> float:
    denominator = np.linalg.norm(a) * np.linalg.norm(b)
    if denominator == 0:
        raise ValueError("cosine is undefined for a zero vector")
    return float(np.dot(a, b) / denominator)


def by_hand() -> None:
    section("1. THE HAND CALCULATION, VERIFIED")
    a = np.array([3.0, 4.0])
    b = np.array([2.0, 1.0])

    dot = float(np.dot(a, b))
    norm_a = float(np.linalg.norm(a))
    norm_b = float(np.linalg.norm(b))
    cos = dot / (norm_a * norm_b)

    print(f"  a = {a}, b = {b}")
    print(f"    a . b   = 3x2 + 4x1 = 6 + 4          = {dot}")
    print(f"    ||a||   = sqrt(9 + 16) = sqrt(25)    = {norm_a}")
    print(f"    ||b||   = sqrt(4 + 1)  = sqrt(5)     = {norm_b:.4f}")
    print(f"    cos     = {dot} / ({norm_a} x {norm_b:.4f}) = {cos:.4f}")
    print(f"    angle   = {np.degrees(np.arccos(np.clip(cos, -1, 1))):.1f} degrees")
    print()

    c = a * 2
    print(f"  SCALE INVARIANCE - c = a doubled = {c}")
    print(f"    c . b   = {float(np.dot(c, b))}    <- dot product DOUBLED")
    print(f"    ||c||   = {float(np.linalg.norm(c))}     <- norm doubled too")
    print(f"    cos     = {cosine(c, b):.4f}   <- IDENTICAL to cos(a, b)")
    print()
    print(f"  Euclidean distance between a and c: "
          f"{float(np.linalg.norm(a - c)):.4f}")
    print("    Cosine says 'identical direction'; Euclidean says '5 apart'.")
    print(f"    cos(a, c) = {cosine(a, c):.4f}")


def ranking() -> None:
    section("2. RANKING THE SECTION 6 CORPUS")
    dots = CORPUS @ QUERY
    norms = np.linalg.norm(CORPUS, axis=1)
    query_norm = np.linalg.norm(QUERY)
    cosines = dots / (norms * query_norm)

    print(f"  query = {QUERY}, ||query|| = {query_norm:.4f}")
    print()
    print(f"  {'document':<32}{'dot':>8}{'norm':>9}{'cosine':>10}")
    for name, d, n, c in zip(NAMES, dots, norms, cosines):
        print(f"  {name:<32}{d:>8.4f}{n:>9.4f}{c:>10.4f}")
    print()
    print(f"  ranking by dot product : "
          f"{[NAMES[i][:4] for i in np.argsort(-dots)]}")
    print(f"  ranking by cosine      : "
          f"{[NAMES[i][:4] for i in np.argsort(-cosines)]}")
    print()
    print("  Same ORDER here, but look at the ratios:")
    print(f"    by dot product, doc2 scores {dots[2] / dots[0]:.2f}x doc0")
    print(f"    by cosine,      doc2 scores {cosines[2] / cosines[0]:.2f}x doc0")
    print("  doc2 is literally the query direction doubled. Cosine correctly")
    print("  reports 1.0000 (perfect direction match). The dot product")
    print("  inflates it for being longer.")


def ranking_inverted() -> None:
    section("3. WHERE THE DOT PRODUCT ACTIVELY BREAKS THE RANKING")
    # A long, rambling, only-vaguely-related document with a large norm.
    rambling = np.array([1.2, 1.1, 1.3, 1.0])
    corpus = np.vstack([CORPUS[0], CORPUS[1], rambling])
    names = ["doc0 SHORT, highly relevant", "doc1 shipping times",
             "doc3 LONG, vaguely related"]

    dots = corpus @ QUERY
    norms = np.linalg.norm(corpus, axis=1)
    cosines = dots / (norms * np.linalg.norm(QUERY))

    print(f"  {'document':<32}{'dot':>8}{'norm':>9}{'cosine':>10}")
    for name, d, n, c in zip(names, dots, norms, cosines):
        print(f"  {name:<32}{d:>8.4f}{n:>9.4f}{c:>10.4f}")
    print()
    dot_order = [names[i][:5] for i in np.argsort(-dots)]
    cos_order = [names[i][:5] for i in np.argsort(-cosines)]
    print(f"  ranking by dot product : {dot_order}")
    print(f"  ranking by cosine      : {cos_order}")
    print()
    print("  THE RANKINGS DISAGREE. The long, vaguely-related document wins")
    print("  on raw dot product purely because its norm is larger. Cosine")
    print("  puts the short, highly relevant document first, correctly.")
    print()
    print("  This is what a user sees as 'search returns waffle'. No error")
    print("  is raised. The scores look reasonable. The order is wrong.")


def normalisation_shortcut() -> None:
    section("4. THE NORMALISATION SHORTCUT, VERIFIED")
    norms = np.linalg.norm(CORPUS, axis=1, keepdims=True)   # (3, 1) for broadcasting
    normalised = CORPUS / norms
    query_unit = QUERY / np.linalg.norm(QUERY)

    print(f"  corpus norms shape (keepdims=True): {norms.shape}")
    print(f"  norms after normalising: "
          f"{np.array2string(np.linalg.norm(normalised, axis=1), precision=6)}")
    print("    all 1.0, as required")
    print()

    full_cosine = (CORPUS @ QUERY) / (np.linalg.norm(CORPUS, axis=1)
                                      * np.linalg.norm(QUERY))
    plain_dot = normalised @ query_unit

    print(f"  {'document':<32}{'full cosine':>14}{'normalised dot':>16}")
    for name, c, d in zip(NAMES, full_cosine, plain_dot):
        print(f"  {name:<32}{c:>14.6f}{d:>16.6f}")
    print()
    print(f"  identical to floating-point precision? "
          f"{np.allclose(full_cosine, plain_dot)}")
    print()
    print("  So: normalise ONCE at index time, then a plain dot product at")
    print("  query time gives cosine similarity for free.")


def performance() -> None:
    section("5. WHY THAT SHORTCUT MATTERS AT SCALE")
    rng = np.random.default_rng(42)
    n_docs, dims = 100_000, 768
    corpus = rng.normal(size=(n_docs, dims))
    query = rng.normal(size=dims)

    normalised = corpus / np.linalg.norm(corpus, axis=1, keepdims=True)
    query_unit = query / np.linalg.norm(query)

    start = time.perf_counter()
    for _ in range(10):
        _ = (corpus @ query) / (np.linalg.norm(corpus, axis=1)
                                * np.linalg.norm(query))
    full_ms = (time.perf_counter() - start) / 10 * 1000

    start = time.perf_counter()
    for _ in range(10):
        _ = normalised @ query_unit
    dot_ms = (time.perf_counter() - start) / 10 * 1000

    print(f"  Scoring 1 query against {n_docs:,} documents of {dims} dimensions:")
    print(f"    full cosine (norms every time) : {full_ms:>8.2f} ms")
    print(f"    plain dot on pre-normalised    : {dot_ms:>8.2f} ms")
    print(f"    speed-up                       : {full_ms / dot_ms:>8.1f}x")
    print()
    print("  The norms were computed ONCE at index time instead of on every")
    print("  query. At production query rates that is the whole difference.")


def high_dimensions() -> None:
    section("6. HIGH DIMENSIONS - random vectors become orthogonal")
    rng = np.random.default_rng(42)
    pairs = 2000

    print(f"  Mean |cosine| between {pairs} random vector pairs:")
    print(f"  {'dimensions':>12}{'mean |cos|':>14}{'':>4}")
    for dims in (2, 8, 64, 256, 768, 1536):
        a = rng.normal(size=(pairs, dims))
        b = rng.normal(size=(pairs, dims))
        a /= np.linalg.norm(a, axis=1, keepdims=True)
        b /= np.linalg.norm(b, axis=1, keepdims=True)
        mean_abs = float(np.mean(np.abs(np.sum(a * b, axis=1))))
        bar = "#" * int(mean_abs * 60)
        print(f"  {dims:>12}{mean_abs:>14.4f}    {bar}")
    print()
    print("  In 2 dimensions two random vectors are quite often aligned by")
    print("  chance. By 1536 dimensions they are almost exactly orthogonal.")
    print()
    print("  THIS IS WHY EMBEDDING SEARCH WORKS: against a near-zero")
    print("  background, any genuine similarity stands out sharply.")


def main() -> None:
    print("=" * 74)
    print("DOT PRODUCTS, NORMS AND COSINE SIMILARITY")
    print("=" * 74)
    by_hand()
    ranking()
    ranking_inverted()
    normalisation_shortcut()
    performance()
    high_dimensions()
    print()
    print("=" * 74)


if __name__ == "__main__":
    main()
