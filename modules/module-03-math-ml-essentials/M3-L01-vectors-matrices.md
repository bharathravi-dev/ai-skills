# M3-L01 — Scalars, Vectors, Matrices, Shapes and Dimensions

| | |
|---|---|
| **Lesson ID** | M3-L01 |
| **Module** | Module 3 — Mathematics and Machine Learning Essentials |
| **Difficulty** | 1 (Intro) |
| **Estimated study time** | 1.75 hours |
| **Prerequisites** | [M2-L04](../module-02-python-foundations/M2-L04-control-flow-comprehensions.md) |

---

> **A note on the mathematics.** You said beginner, so this module starts from arithmetic you already
> know and adds one idea at a time. Every symbol is named before it is used, and every formula is
> worked with small numbers by hand before any code appears. Nothing here requires prior mathematics
> beyond secondary school.
>
> **Why this module matters practically:** an embedding is a vector. Similarity is a dot product.
> Retrieval scores are matrix multiplication. When Module 6 returns the wrong documents, the debugging
> happens at this level.

---

## 1. Learning objectives

1. **Define** scalar, vector and matrix, and **state** the shape of each.
2. **Read** a shape such as `(1000, 1536)` and say what each number means.
3. **Predict** whether two arrays can be added or multiplied, and **explain** broadcasting.
4. **Diagnose** a shape-mismatch error from its message.
5. **Represent** a batch of text embeddings as a matrix and index it correctly.

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **Scalar** | A single number. `5`, `0.91`, `-2.3`. |
| **Vector** | An ordered list of numbers. `[3, 4]`. |
| **Matrix** | A rectangular grid of numbers, arranged in rows and columns. |
| **Tensor** | The general term for an array of any number of dimensions. |
| **Dimension** (of an array) | How many indices you need to select one element. Also called *rank* or *axis count*. |
| **Dimension** (of a vector) | How many numbers it contains. **A different meaning — see §5.2.** |
| **Shape** | A tuple giving the size along each axis: `(3, 4)` is 3 rows by 4 columns. |
| **Axis** | One direction through an array. Axis 0 is rows, axis 1 is columns. |
| **Element** | One number inside an array. |
| **NumPy** | The Python library for numerical arrays. |
| **`ndarray`** | NumPy's array type. |
| **Broadcasting** | NumPy's rule for operating on arrays of different but compatible shapes. |
| **Row vector / column vector** | A matrix with one row, shape `(1, n)`, or one column, shape `(n, 1)`. |
| **Element-wise** | An operation applied independently to each corresponding pair of elements. |

---

## 3. Plain-language explanation

Three levels of structure, and one rule for reading them.

**A scalar** is one number: `0.91`. A similarity score is a scalar.

**A vector** is an ordered list: `[0.2, -0.1, 0.8]`. **An embedding is a vector.** When Module 4 says
a model turns text into a 1,536-number representation, it means a vector with 1,536 entries.

**A matrix** is a grid. **A collection of embeddings is a matrix**: one row per document, one column
per dimension.

```
       dim0   dim1   dim2
doc0 [  0.2,  -0.1,   0.8 ]
doc1 [ -0.5,   0.3,   0.1 ]
doc2 [  0.9,   0.0,  -0.4 ]
```

That is shape `(3, 3)` — three documents, three dimensions each. Real embeddings have hundreds or
thousands of columns, but the structure is identical.

**The rule for reading a shape: it is always `(outermost, ..., innermost)`.** For `(1000, 1536)`:
1,000 items, each of which is 1,536 numbers. So it is 1,000 embeddings of 1,536 dimensions — never
the other way round.

### Connecting to what you already know

| Python | Mathematics | Shape |
|---|---|---|
| `0.91` | Scalar | `()` |
| `[1, 2, 3]` | Vector | `(3,)` |
| `[[1,2,3],[4,5,6]]` | Matrix | `(2, 3)` |
| A list of dicts, one per row | A matrix with named columns | — |

A matrix is a list of lists where **every inner list has the same length**. That constraint is what
makes it a matrix rather than merely nested lists, and it is what NumPy enforces.

---

## 4. Analogy

**A spreadsheet.** A cell is a scalar, a row is a vector, the sheet is a matrix, and a workbook of
sheets is a 3-D array.

### Where the analogy breaks

1. **Spreadsheet columns have names and mixed types.** A matrix is positional and uniformly numeric —
   which is why the M1-L04 encoding step exists: text and categories must become numbers first.
2. **Spreadsheets are ragged; matrices are strictly rectangular.** Every row has the same length, and
   NumPy refuses otherwise.
3. **You read a spreadsheet by row.** Much matrix work operates on **columns** or on the whole array
   at once, which is where `axis=` comes in (§5.5).
4. **Spreadsheets stop at two dimensions.** Arrays keep going — a batch of token embeddings is
   `(batch, tokens, dimensions)`, three axes, and Module 4 uses exactly that.

---

## 5. Detailed technical explanation

### 5.1 NumPy basics

```python
import numpy as np

scalar = np.array(5.0)
vector = np.array([3.0, 4.0])
matrix = np.array([[1.0, 2.0, 3.0],
                   [4.0, 5.0, 6.0]])

scalar.shape    # ()      zero axes
vector.shape    # (2,)    one axis, length 2
matrix.shape    # (2, 3)  two axes: 2 rows, 3 columns
matrix.ndim     # 2       number of axes
matrix.size     # 6       total elements
matrix.dtype    # dtype('float64')
```

**Note the trailing comma in `(2,)`.** That is Python's one-element tuple syntax (M2-L03) — `(2)`
would just be the integer 2. It matters because `(2,)` and `(2, 1)` and `(1, 2)` are three different
shapes that behave differently.

Creating arrays:

```python
np.zeros((2, 3))            # 2x3 of zeros
np.ones(5)                  # length-5 of ones
np.arange(6)                # [0 1 2 3 4 5]
np.arange(6).reshape(2, 3)  # same data, 2x3
np.random.default_rng(42).normal(size=(3, 4))   # seeded random
```

Always seed random generation (M3-L14). `np.random.default_rng(seed)` is the modern form.

### 5.2 The word "dimension" means two things

This genuinely confuses people, and both meanings appear in the same sentence in real documentation.

| Phrase | Means | Example |
|---|---|---|
| "a 1,536-dimensional embedding" | The **vector's length** | shape `(1536,)` — one axis |
| "a 2-dimensional array" | The **number of axes** | shape `(1000, 1536)` — two axes |

So a matrix of 1,000 embeddings of 1,536 dimensions is a **2-dimensional array** whose second
**dimension** is 1,536. Both usages are correct. When it is ambiguous, say "shape `(1000, 1536)`" —
a shape is never ambiguous.

### 5.3 Indexing and slicing

```python
m = np.array([[1, 2, 3],
              [4, 5, 6],
              [7, 8, 9]])

m[0]          # array([1, 2, 3])   row 0 -> shape (3,)
m[0, 2]       # 3                  row 0, column 2 -> a scalar
m[:, 1]       # array([2, 5, 8])   ALL rows, column 1 -> shape (3,)
m[0:2]        # first two rows     -> shape (2, 3)
m[0:2, 1:]    # rows 0-1, columns 1+ -> shape (2, 2)
m[-1]         # last row
```

`m[:, 1]` — "every row, column 1" — is the idiom for extracting one feature across all examples, and
you will use it constantly.

**A single index reduces the number of axes; a slice preserves it:**

```python
m[0].shape      # (3,)    one axis - the row itself
m[0:1].shape    # (1, 3)  two axes - a matrix containing one row
```

That distinction causes real bugs when a function expects a 2-D input.

### 5.4 Element-wise operations and broadcasting

Arithmetic on same-shaped arrays is **element-wise**:

```python
a = np.array([1.0, 2.0, 3.0])
b = np.array([10.0, 20.0, 30.0])
a + b        # [11. 22. 33.]
a * b        # [10. 40. 90.]   NOT a dot product (M3-L02)
```

**`*` is element-wise multiplication, not matrix multiplication.** Matrix multiplication is `@` or
`np.matmul`. Confusing them is the single most common NumPy error, and it frequently produces a
*plausible wrong answer* rather than an exception.

**Broadcasting** lets differently-shaped arrays combine, by conceptually stretching the smaller one:

```python
matrix = np.array([[1.0, 2.0, 3.0],
                   [4.0, 5.0, 6.0]])        # (2, 3)
matrix + 10                                  # scalar broadcast to every element
matrix + np.array([100.0, 200.0, 300.0])     # (3,) broadcast across both rows
```

**The rule**, applied from the **right-hand end** of the shapes: two dimensions are compatible if
they are equal, or one of them is 1.

```
(2, 3) and (3,)     -> (3,) is treated as (1, 3) -> compatible -> result (2, 3)
(2, 3) and (2,)     -> compared as (1, 2) vs (2, 3) -> 2 vs 3 -> INCOMPATIBLE
(2, 3) and (2, 1)   -> compatible -> result (2, 3)
```

The second line surprises people: a length-2 array does **not** broadcast across the rows of a
`(2, 3)` matrix, because alignment starts from the right. To subtract a per-row value you need shape
`(2, 1)`:

```python
row_means = matrix.mean(axis=1, keepdims=True)   # (2, 1), not (2,)
centred = matrix - row_means
```

`keepdims=True` is what preserves the axis so broadcasting aligns correctly. Forgetting it is a
common and confusing bug.

### 5.5 Axes in reductions

```python
m = np.array([[1.0, 2.0, 3.0],
              [4.0, 5.0, 6.0]])

m.sum()            # 21.0        everything -> scalar
m.sum(axis=0)      # [5. 7. 9.]  collapse ROWS -> one value per column, shape (3,)
m.sum(axis=1)      # [6. 15.]    collapse COLUMNS -> one value per row, shape (2,)
```

**`axis=n` means "the axis that disappears".** `axis=0` removes the row axis, leaving column totals.
Reading it as "operate along" is where people go wrong; read it as "collapse this one".

For a `(n_documents, n_dimensions)` embedding matrix:

- `axis=0` → one value per **dimension**, across all documents.
- `axis=1` → one value per **document**, across all its dimensions. This is what you want for vector
  norms (M3-L02).

### 5.6 Shapes in this course

| Quantity | Shape | Meaning |
|---|---|---|
| One embedding | `(1536,)` | 1,536 numbers |
| A batch of embeddings | `(n_docs, 1536)` | One row per document |
| A feature matrix `X` | `(n_samples, n_features)` | M1-L04 |
| A label vector `y` | `(n_samples,)` | One label per sample |
| Similarity scores | `(n_docs,)` | One score per document |
| Token embeddings | `(batch, n_tokens, d_model)` | Module 4 |
| Attention scores | `(batch, heads, n_tokens, n_tokens)` | M4-L08 |

**`(n_samples, n_features)` — samples first — is the universal convention** in scikit-learn, NumPy
and almost every framework. Getting it backwards produces a model that trains on the wrong thing, or
a shape error naming numbers you do not recognise.

### 5.7 Why NumPy rather than lists

```python
python_sum = sum(a[i] * b[i] for i in range(len(a)))   # a Python loop
numpy_sum  = np.dot(a, b)                              # compiled, vectorised
```

NumPy stores numbers in a contiguous block of memory and operates on them in compiled code, so it
avoids Python's per-element overhead. The lab measures the difference; it is large enough to change
what is feasible.

### 5.8 Assumptions and limitations

- NumPy 2.5.3 `[VERIFIED 2026-09-08]` by installation and execution here.
- Arrays are **homogeneous**: one dtype for the whole array. Mixed types force `object` dtype and lose
  all speed benefits.
- `float64` is the default; deep-learning frameworks often use `float32` for memory and speed.
- Slices are **views**, not copies — modifying a slice modifies the original (the M2-L03 aliasing
  lesson, again).

---

## 6. Worked example — a tiny embedding matrix by hand

Three documents, each embedded into 4 dimensions. Small enough to do entirely on paper.

```
        d0     d1     d2     d3
doc0 [ 0.9,   0.1,   0.0,   0.2 ]     "refund policy"
doc1 [ 0.8,   0.2,   0.1,   0.1 ]     "refund process"
doc2 [ 0.1,   0.0,   0.9,   0.3 ]     "shipping times"
```

**Step 1 — the shape.** 3 rows, 4 columns → `(3, 4)`. Three documents, each a 4-dimensional
embedding. `ndim` is 2; `size` is 12.

**Step 2 — select one document.** `E[0]` → `[0.9, 0.1, 0.0, 0.2]`, shape `(4,)`. One axis, because a
single integer index removes an axis.

**Step 3 — select one dimension across all documents.** `E[:, 2]` → `[0.0, 0.1, 0.9]`, shape `(3,)`.
The third dimension for every document.

**Step 4 — the mean of each dimension.** Collapse the document axis, so `axis=0`:

- d0: (0.9 + 0.8 + 0.1) / 3 = 1.8 / 3 = **0.6**
- d1: (0.1 + 0.2 + 0.0) / 3 = 0.3 / 3 = **0.1**
- d2: (0.0 + 0.1 + 0.9) / 3 = 1.0 / 3 ≈ **0.3333**
- d3: (0.2 + 0.1 + 0.3) / 3 = 0.6 / 3 = **0.2**

Result `[0.6, 0.1, 0.3333, 0.2]`, shape `(4,)`. This is the **centroid** — the average embedding, and
a real technique for representing a cluster of documents (M6-L01).

**Step 5 — centre the matrix.** Subtract the centroid from every row. The centroid has shape `(4,)`
and the matrix `(3, 4)`; aligning from the right gives 4 vs 4 ✓ and 3 vs 1 ✓, so it broadcasts:

```
doc0 - centroid = [0.9-0.6, 0.1-0.1, 0.0-0.3333, 0.2-0.2] = [ 0.3, 0.0, -0.3333,  0.0]
doc1 - centroid = [0.8-0.6, 0.2-0.1, 0.1-0.3333, 0.1-0.2] = [ 0.2, 0.1, -0.2333, -0.1]
doc2 - centroid = [0.1-0.6, 0.0-0.1, 0.9-0.3333, 0.3-0.2] = [-0.5,-0.1,  0.5667,  0.1]
```

**Step 6 — the mistake to expect.** Now try to subtract a *per-document* value, say each document's
own mean:

```python
doc_means = E.mean(axis=1)          # shape (3,) - one per document
E - doc_means                       # ValueError!
```

Aligning `(3, 4)` with `(3,)` from the right compares 4 against 3 → incompatible. The fix is
`keepdims=True`, giving `(3, 1)`, which aligns as 4 vs 1 ✓ and 3 vs 3 ✓.

**This is the single most common NumPy error**, and the message names shapes rather than your
variables — so recognising the pattern is what saves you time.

---

## 7. Practical activity

**File:** [`labs/m3/l01_arrays.py`](../../labs/m3/l01_arrays.py)

**Requires the venv** (`numpy==2.5.3`):

```bash
source .venv/bin/activate
python labs/m3/l01_arrays.py
```

Works through the §6 example with real output, demonstrates every indexing form and its resulting
shape, walks the broadcasting rule including the failure, shows the axis convention, exposes the view
-versus-copy trap, and measures NumPy against a pure-Python loop.

### 7.1 Important lines

| Construct | Why |
|---|---|
| `E.shape`, `E.ndim`, `E.size` | The three questions to ask of any array you did not create. |
| `E[:, 2]` | All rows, one column — extracting a feature. |
| `E.mean(axis=0)` vs `axis=1` | `axis=n` is the axis that **disappears**. |
| `keepdims=True` | Preserves the axis so broadcasting aligns. |
| `arr[0:2] = 0` on a slice | Demonstrates that slices are **views**, not copies. |
| `time.perf_counter()` | Measures the NumPy speed-up. |

### 7.2 Expected output

`[EXECUTED]` 2026-09-08 with numpy 2.5.3, Python 3.12.3. Timings vary:

```
==========================================================================
SCALARS, VECTORS, MATRICES AND SHAPES
==========================================================================
numpy 2.5.3

--------------------------------------------------------------------------
1. THE THREE QUESTIONS TO ASK OF ANY ARRAY
--------------------------------------------------------------------------
  E =
    [0.9 0.1 0.  0.2]            refund policy
    [0.8 0.2 0.1 0.1]            refund process
    [0.1 0.  0.9 0.3]            shipping times

  E.shape = (3, 4)   <- 3 documents, each 4 numbers
  E.ndim  = 2        <- two axes: rows and columns
  E.size  = 12       <- total elements
  E.dtype = float64

  Read the shape OUTERMOST to INNERMOST. (3, 4) is 3 items of 4
  numbers - never 4 items of 3.

--------------------------------------------------------------------------
2. INDEXING - an integer removes an axis, a slice keeps it
--------------------------------------------------------------------------
  expression  shape     ndim  value
  E[0]        (4,)      1     [0.9, 0.1, 0. , 0.2]
  E[0:1]      (1, 4)    2     [[0.9, 0.1, 0. , 0.2]]
  E[0, 2]     ()        0     0.
  E[:, 2]     (3,)      1     [0. , 0.1, 0.9]
  E[:, 1:3]   (3, 2)    2     [[0.1, 0. ],  [0.2, 0.1],  [0. , 0.9]]
  E[-1]       (4,)      1     [0.1, 0. , 0.9, 0.3]

  Compare E[0] shape (4,) with E[0:1] shape (1, 4). Same numbers,
  different ndim. A function expecting a 2-D input accepts the
  second and rejects the first.

--------------------------------------------------------------------------
3. AXES - axis=n is the axis that DISAPPEARS
--------------------------------------------------------------------------
  E.shape = (3, 4)  (documents, dimensions)

  E.sum()          -> 3.70   shape ()   everything
  E.mean(axis=0)   -> [0.6    0.1    0.3333 0.2   ]  shape (4,)
                      the DOCUMENT axis collapsed: one value per DIMENSION
  E.mean(axis=1)   -> [0.3   0.3   0.325]  shape (3,)
                      the DIMENSION axis collapsed: one value per DOCUMENT

  Hand-check of the centroid (axis=0), from section 6:
    d0: (0.9 + 0.8 + 0.1) / 3 = 1.8 / 3 = 0.6000
    d1: (0.1 + 0.2 + 0.0) / 3 = 0.3 / 3 = 0.1000
    d2: (0.0 + 0.1 + 0.9) / 3 = 1.0 / 3 = 0.3333
    d3: (0.2 + 0.1 + 0.3) / 3 = 0.6 / 3 = 0.2000
  numpy gives      [0.6    0.1    0.3333 0.2   ]  - matches.

--------------------------------------------------------------------------
4. BROADCASTING - alignment starts from the RIGHT
--------------------------------------------------------------------------
  E shape        (3, 4)
  centroid shape (4,)
  align from the right:  4 vs 4 ok,  3 vs (nothing -> 1) ok  => works

  E - centroid (centring the matrix):
    [ 0.3    -0.     -0.3333 -0.    ]      refund policy
    [ 0.2     0.1    -0.2333 -0.1   ]      refund process
    [-0.5    -0.1     0.5667  0.1   ]      shipping times
  new column means: [-0. -0.  0. -0.]
  ~zero, as expected after centring.

  NOW THE COMMON ERROR - subtracting a PER-DOCUMENT value:
    doc_means shape (3,)
    align from the right:  4 vs 3  => INCOMPATIBLE
    ValueError: operands could not be broadcast together with shapes (3,4) (3,) 

  THE FIX - keepdims=True preserves the axis:
    E.mean(axis=1, keepdims=True).shape = (3, 1)
    align from the right:  4 vs 1 ok,  3 vs 3 ok  => works
    result shape (3, 4)
    row means now: [ 0. -0. -0.]

  Note the error message names SHAPES, not your variables. Learning
  to read '(3,4) (3,)' as 'aligned from the right, 4 vs 3' is the
  whole skill.

--------------------------------------------------------------------------
5. * IS NOT @  - the error that does not raise
--------------------------------------------------------------------------
  a =
    [[1. 2.]
    [3. 4.]]
  b =
    [[5. 6.]
    [7. 8.]]

  a * b  (element-wise) =
    [[ 5. 12.]
    [21. 32.]]
  a @ b  (matrix mult)  =
    [[19. 22.]
    [43. 50.]]

  Both are (2, 2). Both are plausible. Only one is what you meant.
  There is no exception to catch - which is why you check the
  numbers, not just the shape.

--------------------------------------------------------------------------
6. SLICES ARE VIEWS, NOT COPIES
--------------------------------------------------------------------------
  original =
    [[0 1 2]
    [3 4 5]]
  view = original[0]; view[0] = 99
  original is now =
    [[99  1  2]
    [ 3  4  5]]
    <- the original changed. Same memory.

  With .copy():
  original =
    [[0 1 2]
    [3 4 5]]
    <- unchanged. This is the M2-L03 aliasing lesson in NumPy form.

--------------------------------------------------------------------------
7. WHY NUMPY AND NOT A PYTHON LOOP
--------------------------------------------------------------------------
  Dot product of two 1,000,000-element vectors:
    pure Python loop :     52.01 ms
    numpy np.dot     :      4.06 ms
    speed-up         :        13x
    same answer?     : True

  NumPy stores numbers in one contiguous block and operates on them
  in compiled code, avoiding Python's per-element overhead. At
  Module 6 scale this is the difference between feasible and not.

--------------------------------------------------------------------------
8. STORAGE - the number that sizes your vector database
--------------------------------------------------------------------------
     documents    dims       float32       float64
        10,000     768         0.03G         0.06G
       100,000    1536         0.61G         1.23G
     1,000,000    1536         6.14G        12.29G

  1,000,000 x 1,536 x 4 bytes = 6.14 GB in float32.
  That single arithmetic drives your Module 6 instance sizing and
  your monthly bill. Do it before choosing a vector store.

==========================================================================
```

### 7.3 Reading the result

**Section 3 confirms the hand calculation.** The centroid computed on paper in §6 —
`[0.6, 0.1, 0.3333, 0.2]` — is exactly what `E.mean(axis=0)` returns. Do that check on every new
operation you learn: work it by hand on three numbers first, then trust the library.

Note the two means side by side:

```
E.mean(axis=0) -> [0.6, 0.1, 0.3333, 0.2]   shape (4,)   one per DIMENSION
E.mean(axis=1) -> [0.3, 0.3, 0.325]         shape (3,)   one per DOCUMENT
```

Same matrix, same method, different axis, completely different meaning. `axis=0` collapsed the three
documents; `axis=1` collapsed the four dimensions. **The axis you name is the axis that disappears.**

**Section 4 is the error you will actually hit:**

```
ValueError: operands could not be broadcast together with shapes (3,4) (3,)
```

Read it the way the lab does: align from the **right**. `4` against `3` — incompatible. The message
names shapes, not your variables, so the skill is translating `(3,4) (3,)` into "the last dimensions
disagree". With `keepdims=True` the shape becomes `(3, 1)`, which aligns as `4 vs 1` ✓ and `3 vs 3` ✓.

**Section 5 is the mistake that does not announce itself:**

| | Result |
|---|---|
| `a * b` (element-wise) | `[[5, 12], [21, 32]]` |
| `a @ b` (matrix multiply) | `[[19, 22], [43, 50]]` |

Both are `(2, 2)`. Both are plausible matrices of plausible numbers. **No exception is raised.** A
shape assertion would not catch it either. The only defence is knowing which one you meant and
checking a value by hand — which is why §6 of every maths lesson in this module works an example on
paper first.

**Section 7:** NumPy was **13× faster** than the equivalent Python loop for a million-element dot
product, with an identical answer. That gap widens with array size, and it is why every embedding
operation in Modules 6 and 7 is expressed as an array operation rather than a loop.

**Section 8 is the arithmetic to remember:**

| Documents | Dimensions | float32 | float64 |
|---|---|---|---|
| 10,000 | 768 | 0.03 GB | 0.06 GB |
| 100,000 | 1,536 | 0.61 GB | 1.23 GB |
| **1,000,000** | **1,536** | **6.14 GB** | **12.29 GB** |

One million documents at 1,536 dimensions needs **6.14 GB** in `float32` — and twice that if you
leave the default `float64`. That single calculation decides your vector-store instance size and your
monthly bill in Module 6. Do it before you choose a product, not after.

**Verification:** confirm the centroid is `[0.6, 0.1, 0.3333, 0.2]`, that `E - doc_means` raises with
shapes `(3,4) (3,)`, and that `a * b` and `a @ b` give different results.

---

## 8. Common mistakes and troubleshooting

1. **`*` when you meant `@`.** Element-wise versus matrix multiplication. Often silent.
2. **Forgetting `keepdims=True`** when subtracting a per-row value.
3. **Reversing `(n_samples, n_features)`.**
4. **Confusing `axis=0` and `axis=1`.** `axis=n` disappears.
5. **`m[0]` when a function needs 2-D.** Use `m[0:1]` or `m[0].reshape(1, -1)`.
6. **Assuming a slice is a copy.** It is a view; use `.copy()`.
7. **Confusing the two meanings of "dimension".**
8. **Mixed types** forcing `object` dtype and destroying performance.

| Error | Cause | Fix |
|---|---|---|
| `ValueError: operands could not be broadcast together with shapes (3,4) (3,)` | Right-aligned mismatch | `keepdims=True`, or `reshape(-1, 1)` |
| `ValueError: matmul: Input operand 1 has a mismatch...` | Inner dimensions differ | Check `A.shape[1] == B.shape[0]` (M3-L02) |
| Result has an unexpected extra axis | Sliced with `0:1` instead of `0` | Choose deliberately |
| Silently wrong numbers | `*` instead of `@` | Check the result's shape against what you expected |
| Original array changed unexpectedly | A slice is a view | `.copy()` |
| Very slow | `dtype=object`, or a Python loop | Keep one numeric dtype; vectorise |

---

## 9. Security, privacy, reliability and cost

- **Reliability.** Shape errors are the most common bug in numerical code. **Assert shapes at
  boundaries** — `assert X.shape[1] == 1536` costs nothing and turns a confusing downstream error
  into an immediate one, exactly as M2-L05 argued for validation.
- **Cost.** Embedding storage is `n_documents × dimensions × bytes_per_number`. One million documents
  at 1,536 dimensions in `float32` is 1e6 × 1536 × 4 ≈ **6.1 GB**. That number drives your vector
  database sizing and bill in Module 6.
- **Privacy.** Embeddings are derived from text and are not anonymous — the original content can
  often be partially reconstructed from them. Treat an embedding store with the same care as the
  source documents (M10-L06).
- **Reliability.** Always seed random generation. An unseeded initialisation makes a bug
  irreproducible.

---

## 10. Exercises

### Exercise 1 — Beginner (~15 min)

Predict the shape, then verify:

```python
np.zeros((4, 5)).shape
np.zeros((4, 5))[2].shape
np.zeros((4, 5))[2:3].shape
np.zeros((4, 5))[:, 1].shape
np.zeros((4, 5)).sum(axis=0).shape
np.zeros((4, 5)).sum(axis=1).shape
np.zeros((4, 5)).mean(axis=1, keepdims=True).shape
np.arange(12).reshape(3, 4)[:, ::2].shape
```

### Exercise 2 — Intermediate (~25 min)

Build the §6 embedding matrix in NumPy, then:

1. Print its shape, ndim, size and dtype.
2. Compute the centroid with `axis=0` and confirm it matches the hand calculation.
3. Centre the matrix by subtracting the centroid. Verify the new column means are ~0.
4. Compute each document's own mean and subtract it — **first without `keepdims`** (record the exact
   error), then with it.
5. Extract dimension 2 for all documents, and document 1's full embedding. State both shapes and
   explain why they differ in ndim.

### Exercise 3 — Challenge (~30 min)

1. Write `assert_shape(array, expected)` raising a clear error naming the array, the expected shape
   and the actual one. Allow `None` as a wildcard, so `(None, 1536)` means "any number of rows".
2. Generate a random `(1000, 128)` matrix with a fixed seed. Compute row norms two ways: a Python
   loop and `np.linalg.norm(..., axis=1)`. Confirm they agree with `np.allclose` and report both
   timings.
3. Demonstrate the view-versus-copy trap: take a slice, modify it, show the original changed, then
   fix it with `.copy()`.
4. Compute the storage in megabytes for 500,000 embeddings at 768 dimensions in `float32` and in
   `float64`. Show your arithmetic and state which you would choose and why.
5. Deliberately trigger three different shape errors and record each message. For each, say which
   part of the message identifies the problem.

---

## 11. Quiz

**Q1.** What does shape `(1000, 1536)` describe?

- A. 1,536 items of 1,000 numbers each.
- B. 1,000 items of 1,536 numbers each.
- C. A 1,000-dimensional vector.
- D. 1,536 documents.

**Q2.** In NumPy, what does `A * B` do for two same-shaped matrices?

- A. Matrix multiplication.
- B. Element-wise multiplication — matrix multiplication is `@`.
- C. A dot product returning a scalar.
- D. Raises an error.

**Q3.** `m` has shape `(2, 3)`. What is the shape of `m[0]`?

- A. `(2, 3)`  B. `(1, 3)`  C. `(3,)`  D. `(2,)`

**Q4.** `m.sum(axis=0)` on a `(2, 3)` matrix gives what shape, and what does it contain?

- A. `(2,)` — one total per row.
- B. `(3,)` — one total per column, because axis 0 (rows) is collapsed.
- C. `(2, 3)` — unchanged.
- D. `()` — a single total.

**Q5.** Why does `(2, 3) - (2,)` fail while `(2, 3) - (3,)` succeeds?

- A. Broadcasting only works with scalars.
- B. Shapes align from the right: `(3,)` matches the 3 columns, whereas `(2,)` is compared
  against 3 and does not match.
- C. `(2,)` is not a valid shape.
- D. Subtraction cannot broadcast.

**Q6.** What does `keepdims=True` do, and when do you need it?

- A. Keeps the dtype unchanged.
- B. Preserves the reduced axis with length 1, so the result still broadcasts against the original —
  needed when subtracting a per-row value.
- C. Prevents copying.
- D. Keeps the array sorted.

**Q7.** What is the shape of a feature matrix `X` by convention?

- A. `(n_features, n_samples)`  B. `(n_samples, n_features)`  C. `(n_features,)`
- D. It varies by library.

**Q8.** You modify a slice of an array and the original changes. Why?

- A. A bug in NumPy.
- B. Slices are views into the same memory, not copies — use `.copy()` for independence.
- C. The array was not sealed.
- D. Integers are immutable.

**Q9.** How much storage do 1,000,000 embeddings of 1,536 dimensions in `float32` require?

- A. ~1.5 MB  B. ~6.1 GB  C. ~1.5 GB  D. ~24 GB

**Q10.** *(Written, rubric-graded.)* In under 70 words, explain the two meanings of "dimension" in
this field and how to avoid ambiguity.

---

## 12. Revision notes

- **Scalar** `()` · **vector** `(n,)` · **matrix** `(rows, cols)` · **tensor** = any number of axes.
- **Read shapes outermost → innermost.** `(1000, 1536)` = 1,000 embeddings of 1,536 numbers.
- **"Dimension" means two things**: a vector's length, and an array's number of axes. Say the shape.
- Indexing with an **integer removes an axis**; a **slice preserves it**. `m[0]` is `(3,)`;
  `m[0:1]` is `(1, 3)`.
- **`*` is element-wise; `@` is matrix multiplication.** Confusing them often fails silently.
- **Broadcasting aligns from the RIGHT.** Compatible if equal or one is 1. `(2,3)` works with `(3,)`
  and with `(2,1)`, **not** with `(2,)`.
- **`keepdims=True`** to subtract a per-row value.
- **`axis=n` is the axis that disappears.** For `(docs, dims)`: `axis=0` → per dimension,
  `axis=1` → per document.
- Convention is **`(n_samples, n_features)`** everywhere.
- **Slices are views, not copies.**
- **Assert shapes at boundaries.** Seed random generation.
- Storage = `n × d × bytes`. 1M × 1536 × 4 bytes ≈ **6.1 GB**.

---

## 13. Completion checklist

- [ ] I can state the shape of a scalar, vector and matrix.
- [ ] I can read `(1000, 1536)` correctly without hesitating.
- [ ] I predicted all eight Exercise 1 shapes.
- [ ] I reproduced the §6 centroid by hand and in NumPy.
- [ ] I triggered the broadcasting error and fixed it with `keepdims`.
- [ ] I know `axis=n` is the axis that disappears.
- [ ] I demonstrated the view-versus-copy trap.
- [ ] I scored 7/10 on the quiz.

---

## 14. References

- NumPy, "The absolute basics for beginners".
  <https://numpy.org/doc/stable/user/absolute_beginners.html> `[UNVERIFIED]`; numpy 2.5.3
  `[VERIFIED 2026-09-08]` by installation and execution here.
- NumPy, Broadcasting.
  <https://numpy.org/doc/stable/user/basics.broadcasting.html> `[UNVERIFIED]`

---

## 15. Next lesson

→ [M3-L02 — Dot Products, Norms and Cosine Similarity by Hand](M3-L02-dot-product-cosine.md)

You can now represent embeddings as arrays. Next: the single most important calculation in this
course — how to measure whether two vectors point in the same direction, which is how every semantic
search in Modules 6 and 7 works.
