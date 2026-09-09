"""M3-L01: shapes, indexing, broadcasting and axes.

Requires numpy:
    source .venv/bin/activate
    python labs/m3/l01_arrays.py
"""

from __future__ import annotations

import time

import numpy as np

LINE = "-" * 74

# The section 6 embedding matrix: 3 documents, 4 dimensions.
E = np.array([
    [0.9, 0.1, 0.0, 0.2],     # doc0 "refund policy"
    [0.8, 0.2, 0.1, 0.1],     # doc1 "refund process"
    [0.1, 0.0, 0.9, 0.3],     # doc2 "shipping times"
])
LABELS = ["refund policy", "refund process", "shipping times"]


def show_matrix(name: str, arr: np.ndarray, indent: str = "    ") -> None:
    """Print a matrix with every line indented (array2string only indents
    continuation lines, which breaks alignment)."""
    text = np.array2string(arr, precision=4, suppress_small=True)
    lines = text.splitlines()
    print(f"  {name} =")
    for line in lines:
        print(f"{indent}{line.strip()}")


def section(title: str) -> None:
    print()
    print(LINE)
    print(title)
    print(LINE)


def shapes() -> None:
    section("1. THE THREE QUESTIONS TO ASK OF ANY ARRAY")
    print(f"  E =")
    for row, label in zip(E, LABELS):
        print(f"    {np.array2string(row, precision=1):<28} {label}")
    print()
    print(f"  E.shape = {E.shape}   <- 3 documents, each 4 numbers")
    print(f"  E.ndim  = {E.ndim}        <- two axes: rows and columns")
    print(f"  E.size  = {E.size}       <- total elements")
    print(f"  E.dtype = {E.dtype}")
    print()
    print("  Read the shape OUTERMOST to INNERMOST. (3, 4) is 3 items of 4")
    print("  numbers - never 4 items of 3.")


def indexing() -> None:
    section("2. INDEXING - an integer removes an axis, a slice keeps it")
    cases = [
        ("E[0]", E[0], "row 0: one document's embedding"),
        ("E[0:1]", E[0:1], "rows 0 to 1: a MATRIX containing one row"),
        ("E[0, 2]", E[0, 2], "a single element -> scalar"),
        ("E[:, 2]", E[:, 2], "all rows, column 2: one dimension for every doc"),
        ("E[:, 1:3]", E[:, 1:3], "all rows, columns 1-2"),
        ("E[-1]", E[-1], "last row"),
    ]
    print(f"  {'expression':<12}{'shape':<10}{'ndim':<6}value")
    for expr, value, note in cases:
        arr = np.asarray(value)
        # Flatten to one line so the table stays aligned.
        printed = np.array2string(arr, precision=2, separator=", ",
                                  max_line_width=200).replace("\n", " ")
        print(f"  {expr:<12}{str(arr.shape):<10}{arr.ndim:<6}{printed}")
    print()
    print("  Compare E[0] shape (4,) with E[0:1] shape (1, 4). Same numbers,")
    print("  different ndim. A function expecting a 2-D input accepts the")
    print("  second and rejects the first.")


def axes() -> None:
    section("3. AXES - axis=n is the axis that DISAPPEARS")
    print(f"  E.shape = {E.shape}  (documents, dimensions)")
    print()
    total = E.sum()
    per_dim = E.mean(axis=0)
    per_doc = E.mean(axis=1)
    print(f"  E.sum()          -> {total:.2f}   shape {np.asarray(total).shape}   everything")
    print(f"  E.mean(axis=0)   -> {np.array2string(per_dim, precision=4)}  "
          f"shape {per_dim.shape}")
    print("                      the DOCUMENT axis collapsed: one value per DIMENSION")
    print(f"  E.mean(axis=1)   -> {np.array2string(per_doc, precision=4)}  "
          f"shape {per_doc.shape}")
    print("                      the DIMENSION axis collapsed: one value per DOCUMENT")
    print()
    print("  Hand-check of the centroid (axis=0), from section 6:")
    for i in range(E.shape[1]):
        column = E[:, i]
        total_col = column.sum()
        print(f"    d{i}: ({' + '.join(f'{v:.1f}' for v in column)}) / 3 "
              f"= {total_col:.1f} / 3 = {total_col / 3:.4f}")
    print(f"  numpy gives      {np.array2string(per_dim, precision=4)}  - matches.")


def broadcasting() -> None:
    section("4. BROADCASTING - alignment starts from the RIGHT")
    centroid = E.mean(axis=0)
    print(f"  E shape        {E.shape}")
    print(f"  centroid shape {centroid.shape}")
    print("  align from the right:  4 vs 4 ok,  3 vs (nothing -> 1) ok  => works")
    centred = E - centroid
    print()
    print("  E - centroid (centring the matrix):")
    for row, label in zip(centred, LABELS):
        print(f"    {np.array2string(row, precision=4, suppress_small=True):<38} {label}")
    print(f"  new column means: "
          f"{np.array2string(centred.mean(axis=0), precision=6, suppress_small=True)}")
    print("  ~zero, as expected after centring.")

    print()
    print("  NOW THE COMMON ERROR - subtracting a PER-DOCUMENT value:")
    doc_means = E.mean(axis=1)
    print(f"    doc_means shape {doc_means.shape}")
    print("    align from the right:  4 vs 3  => INCOMPATIBLE")
    try:
        E - doc_means
    except ValueError as exc:
        print(f"    ValueError: {exc}")
    print()
    print("  THE FIX - keepdims=True preserves the axis:")
    doc_means_kept = E.mean(axis=1, keepdims=True)
    print(f"    E.mean(axis=1, keepdims=True).shape = {doc_means_kept.shape}")
    print("    align from the right:  4 vs 1 ok,  3 vs 3 ok  => works")
    result = E - doc_means_kept
    print(f"    result shape {result.shape}")
    print(f"    row means now: "
          f"{np.array2string(result.mean(axis=1), precision=6, suppress_small=True)}")
    print()
    print("  Note the error message names SHAPES, not your variables. Learning")
    print("  to read '(3,4) (3,)' as 'aligned from the right, 4 vs 3' is the")
    print("  whole skill.")


def elementwise_vs_matmul() -> None:
    section("5. * IS NOT @  - the error that does not raise")
    a = np.array([[1.0, 2.0], [3.0, 4.0]])
    b = np.array([[5.0, 6.0], [7.0, 8.0]])
    show_matrix("a", a)
    show_matrix("b", b)
    print()
    show_matrix("a * b  (element-wise)", a * b)
    show_matrix("a @ b  (matrix mult) ", a @ b)
    print()
    print("  Both are (2, 2). Both are plausible. Only one is what you meant.")
    print("  There is no exception to catch - which is why you check the")
    print("  numbers, not just the shape.")


def views() -> None:
    section("6. SLICES ARE VIEWS, NOT COPIES")
    original = np.arange(6).reshape(2, 3)
    show_matrix("original", original)
    view = original[0]
    view[0] = 99
    print(f"  view = original[0]; view[0] = 99")
    show_matrix("original is now", original)
    print("    <- the original changed. Same memory.")
    print()
    original2 = np.arange(6).reshape(2, 3)
    copy = original2[0].copy()
    copy[0] = 99
    print("  With .copy():")
    show_matrix("original", original2)
    print("    <- unchanged. This is the M2-L03 aliasing lesson in NumPy form.")


def performance() -> None:
    section("7. WHY NUMPY AND NOT A PYTHON LOOP")
    rng = np.random.default_rng(42)
    n = 1_000_000
    a = rng.normal(size=n)
    b = rng.normal(size=n)
    list_a, list_b = a.tolist(), b.tolist()

    start = time.perf_counter()
    loop_result = sum(x * y for x, y in zip(list_a, list_b))
    loop_ms = (time.perf_counter() - start) * 1000

    start = time.perf_counter()
    numpy_result = float(np.dot(a, b))
    numpy_ms = (time.perf_counter() - start) * 1000

    print(f"  Dot product of two {n:,}-element vectors:")
    print(f"    pure Python loop : {loop_ms:>9.2f} ms")
    print(f"    numpy np.dot     : {numpy_ms:>9.2f} ms")
    print(f"    speed-up         : {loop_ms / numpy_ms:>9.0f}x")
    print(f"    same answer?     : {np.isclose(loop_result, numpy_result)}")
    print()
    print("  NumPy stores numbers in one contiguous block and operates on them")
    print("  in compiled code, avoiding Python's per-element overhead. At")
    print("  Module 6 scale this is the difference between feasible and not.")


def storage() -> None:
    section("8. STORAGE - the number that sizes your vector database")
    print(f"  {'documents':>12}{'dims':>8}{'float32':>14}{'float64':>14}")
    for docs, dims in ((10_000, 768), (100_000, 1536), (1_000_000, 1536)):
        f32 = docs * dims * 4 / 1e9
        f64 = docs * dims * 8 / 1e9
        print(f"  {docs:>12,}{dims:>8}{f32:>13.2f}G{f64:>13.2f}G")
    print()
    print("  1,000,000 x 1,536 x 4 bytes = 6.14 GB in float32.")
    print("  That single arithmetic drives your Module 6 instance sizing and")
    print("  your monthly bill. Do it before choosing a vector store.")


def main() -> None:
    print("=" * 74)
    print("SCALARS, VECTORS, MATRICES AND SHAPES")
    print("=" * 74)
    print(f"numpy {np.__version__}")
    shapes()
    indexing()
    axes()
    broadcasting()
    elementwise_vs_matmul()
    views()
    performance()
    storage()
    print()
    print("=" * 74)


if __name__ == "__main__":
    main()
