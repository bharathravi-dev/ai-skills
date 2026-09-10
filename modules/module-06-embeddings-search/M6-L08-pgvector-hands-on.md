# M6-L08 — pgvector Hands-On (and How Alternatives Differ)

| | |
|---|---|
| **Lesson ID** | M6-L08 |
| **Difficulty** | 2 (Intermediate) |
| **Estimated study time** | 2.5 hours |
| **Prerequisites** | [M6-L07](M6-L07-vector-indexes-vs-databases.md), [M2-L16](../module-02-python-foundations/M2-L16-sql.md) |

---

> **A note on how to use this lesson.** The SQL in this lesson is the primary content — run it yourself
> against a real PostgreSQL instance with the pgvector extension installed. It is marked `[NOT EXECUTED]`
> throughout because no PostgreSQL instance was available in the environment that authored this course:
> the logic is reviewed and, to the author's knowledge, correct, but has not been run and checked the way
> every other lab in this course has been. This is exactly the situation COURSE_PLAN.md's design
> assumption A2 anticipates — pgvector as the primary store, with a pure-Python fallback for offline
> practice — and §7's lab is that fallback, fully executed and verified.

---

## 1. Learning objectives

1. **Set up** pgvector on PostgreSQL and create a table with a vector column.
2. **Write** similarity search SQL using pgvector's three distance operators, and know which to use
   when.
3. **Create** and tune both of pgvector's approximate index types, connecting them to M6-L06's measured
   algorithms.
4. **Compare** pgvector to alternative vector stores, and state the specific reasoning behind this
   course's choice.
5. **Use** a verified Python fallback to check the underlying behaviour when a live instance is not
   available.

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **pgvector** | A PostgreSQL extension adding a vector data type and similarity search operators. |
| **Distance operator (pgvector)** | The SQL operators `<->`, `<=>`, `<#>` for L2, cosine, and negative inner product distance. |
| **`vector(n)`** | pgvector's column type for a fixed-dimension vector. |
| **`ivfflat`** | pgvector's clustering-based approximate index type (M6-L06's IVF family). |
| **`hnsw`** | pgvector's graph-based approximate index type (M6-L06's HNSW family). |
| **Managed vector database** | A hosted service (e.g. Pinecone) handling infrastructure, versus a self-hosted extension like pgvector. |

---

## 3. Plain-language explanation

### 3.1 Everything from M6-L01 through M6-L07, now as SQL

Cosine similarity (M6-L02), the algorithms behind approximate search (M6-L06), and the index-vs-database
distinction (M6-L07) are not abstractions this lesson introduces something new to replace — pgvector is
where they become executable SQL, in a database you already know how to use (M2-L16). Nothing about the
underlying mathematics changes; only the interface does.

### 3.2 Three operators, one already-proven identity

pgvector exposes L2 distance, cosine distance, and negative inner product as three separate SQL
operators. §5.1 shows this is not three different ideas — it is M6-L02's identity, under pgvector's own
names, with a specific, actionable consequence for which operator to choose.

### 3.3 Two index types you have already built

`ivfflat` and `hnsw` are not new algorithms to learn — they are pgvector's names for exactly the two
families M6-L06 built from scratch and measured directly. Tuning them in SQL means adjusting the same
parameters, under pgvector's own names.

### 3.4 pgvector is a choice, made for stated reasons — not the only one

COURSE_PLAN.md's design assumptions name the reasoning directly: you already understand relational
databases; one system serves both rows and vectors; no new vendor account is required. Alternatives exist
for good reasons too, and §5.4 compares them honestly.

---

## 4. Detailed technical explanation

### 4.1 Setup

`[NOT EXECUTED — verify against your own PostgreSQL and pgvector installation]`

```sql
-- Requires PostgreSQL with the pgvector extension available.
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE documents (
    id bigserial PRIMARY KEY,
    content text NOT NULL,
    category text,
    embedding vector(384)          -- fixed dimension, chosen at table creation (M6-L02)
);
```

**The dimension is fixed at table creation and must match your embedding model exactly** — this is
M6-L02's model-compatibility warning, enforced structurally: pgvector will reject a vector of the wrong
dimension outright, which is a real, useful guardrail against the silent mismatch bug M6-L02 measured.

### 4.2 Inserting and querying

```sql
INSERT INTO documents (content, category, embedding)
VALUES ('Refund request for a damaged item', 'billing', '[0.12, -0.03, ...]');

-- Cosine distance, ascending (nearest first). Note: DISTANCE, not similarity --
-- smaller is better, the opposite direction from a similarity score.
SELECT id, content, embedding <=> '[0.11, -0.02, ...]' AS distance
FROM documents
ORDER BY embedding <=> '[0.11, -0.02, ...]'
LIMIT 10;
```

**`<=>` returns cosine *distance*** (`1 - cosine similarity`, M3-L02), so `ORDER BY ... ASC` — not
`DESC` — gives the nearest matches. This is a common, easy mistake: forgetting the operator returns a
distance, and sorting the wrong direction, silently returning the *worst* matches first with no error.

### 4.3 The three operators, and which to choose

`[REAL — verified in §7.1's Python fallback]`

| Operator | Measures | Requires normalization for cosine-equivalent ranking? |
|---|---|---|
| `<->` | L2 (Euclidean) distance | Not equivalent to cosine even when normalized (different formula) |
| `<=>` | Cosine distance | No — correct regardless of magnitude |
| `<#>` | Negative inner product | **Yes** — only cosine-equivalent if every vector is unit-normalized |

§7.1's Python fallback proved this exactly: on un-normalized vectors, all three operators disagreed on
the best match; after normalizing, all three agreed. **`<#>` is pgvector's fastest operator because it
skips the normalization division `<=>` performs internally** — but that speed is only safe if
normalization happened once, at insert time, rather than being computed per query. **Store normalized
vectors and use `<#>` for speed, or use `<=>` directly and accept the small extra cost — never use `<#>`
on un-normalized data expecting cosine-equivalent results.**

### 4.4 Approximate indexes: `ivfflat` and `hnsw`

`[NOT EXECUTED — verify against your own installation; exact syntax and defaults vary by pgvector
version]`

```sql
-- IVF-style clustering index (M6-L06 section 1's method, exactly)
CREATE INDEX ON documents USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);                    -- M6-L06's cluster count

-- Search-time tuning (M6-L06's nprobe, by another name):
SET ivfflat.probes = 5;

-- HNSW graph index (M6-L06 section 3's method, exactly)
CREATE INDEX ON documents USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);   -- graph connectivity at build time

-- Search-time tuning (M6-L06's search-width parameter, by another name):
SET hnsw.ef_search = 40;
```

**These are not new algorithms.** `lists` is M6-L06's cluster count; `ivfflat.probes` is M6-L06's
`nprobe`; `hnsw.ef_search` is M6-L06's search-width parameter. §7.2 reproduces M6-L06's own measured
recall/speed table with these exact SQL names substituted in, because — being the same algorithm — the
numbers are the same. **Tuning `probes` or `ef_search` upward trades speed for recall, with the same real
optimum M6-L06 measured, including the same risk of tuning so high that the index becomes slower than no
index at all.**

### 4.5 Combining with SQL you already know

```sql
-- Metadata filtering, previewed here, fully covered in M6-L09:
SELECT id, content, embedding <=> '[0.11, -0.02, ...]' AS distance
FROM documents
WHERE category = 'billing'
ORDER BY embedding <=> '[0.11, -0.02, ...]'
LIMIT 10;
```

**This single query does something a bare index library (M6-L07) does not do for free**: combine a
structured `WHERE` condition with an approximate similarity search, using the same SQL you already know
from M2-L16. Whether the filter runs before or after the approximate search — and what that choice costs
in recall — is M6-L09's full subject; this lesson only shows that the SQL to write it is unremarkable.

### 4.6 How alternatives differ

`[UNVERIFIED — feature sets and pricing change; check current documentation for any system you evaluate]`

| System | Hosting | Strength (per COURSE_PLAN.md's own comparison) |
|---|---|---|
| **pgvector** (this course's choice) | Self-hosted, on PostgreSQL you already run | One system for rows and vectors; no new vendor account |
| Chroma | Self-hosted or embedded | Easiest to start with for a small, standalone project |
| Qdrant / Weaviate | Self-hosted or managed | Strong purpose-built vector features |
| Pinecone / OpenSearch | Managed | Infrastructure handled for you, at a cost |

**The reasoning behind this course's choice is stated plainly in COURSE_PLAN.md**: you already understand
relational databases (M2-L16); pgvector lets vectors live alongside the rows they describe, in one
system; and it requires no new vendor account to start learning. **This is a defensible choice, not the
only correct one** — a system with no existing relational data, or one needing purpose-built vector
features pgvector does not offer, may reasonably choose differently.

### 4.7 Assumptions and limitations

- Every SQL block in this lesson is `[NOT EXECUTED]` in the strict sense this course uses that label —
  reviewed for correctness against training knowledge, not run and verified against a live instance. Run
  it yourself before trusting it in production.
- Exact pgvector syntax, default parameter values, and available operators change between versions.
  Confirm against your installed version's documentation before relying on any specific detail here.
- §4.6's comparison reflects COURSE_PLAN.md's own stated reasoning at course-design time, not a
  current, independently re-verified feature comparison across vendors.

---

## 5. Worked example — the query that silently returned the worst matches

**The system.** A team's first pgvector integration writes:

```sql
SELECT id, content FROM documents
ORDER BY embedding <=> '[...]' DESC
LIMIT 10;
```

**What happened.** The query ran without error and returned 10 results. Every deployment test passed —
"the search returns results" was the only check anyone wrote. In production, users reported that search
results seemed almost deliberately unrelated to their query, but the feature clearly "worked" in the
sense that it never crashed.

**Why, exactly.** `<=>` returns cosine **distance** — smaller means more similar. `ORDER BY ... DESC`
sorts largest-first, which for a distance means **least similar first**. The query was syntactically
valid, ran without error, and confidently returned the ten *worst* matches in the entire table, every
single time.

**Three defects:**

| # | Defect | Consequence |
|---|---|---|
| 1 | `DESC` used on a distance operator, an easy and common mix-up with similarity intuition | Every query silently inverted its own ranking |
| 2 | No test checked that a *known* query returned a *known-relevant* result | "Returns 10 rows without erroring" passed, despite being completely wrong |
| 3 | No one had internalized that pgvector's operators return distances, not similarities | The bug was invisible to code review, since the SQL "reads" correctly to someone expecting a similarity score |

### The fix

**Always sort distance operators ascending**, and say so explicitly in code review checklists for any
pgvector query — `ORDER BY embedding <=> query ASC` (or simply omit `DESC`, since ascending is the
default, but writing it explicitly prevents exactly this mistake).

**Test with a known query and a known-relevant result** (this is M5-L18's evaluation discipline, applied
to search) — "the query runs" is not the same claim as "the query is correct," the same lesson M6-L05
and M6-L06 established for search algorithms generally.

**The general rule.** **A distance operator returning valid, error-free results is not evidence it is
being used correctly.** The single most dangerous property of this bug is that it looks completely
correct at every layer except the one that matters.

---

## 6. Analogy

**A librarian who reports "how far this book is from what you asked for," not "how good a match it
is."** If you mishear "far" as "good" and ask for the ten *farthest* books first, the librarian will
hand them over exactly as asked, correctly, with a polite smile — because from the librarian's point of
view, nothing went wrong. You got exactly the ten answers to the question you actually asked, which is a
different question from the one you meant to ask.

### Where the analogy breaks

- **A human librarian would likely notice you seem confused and check.** SQL has no such courtesy — a
  syntactically valid query executes exactly as written, with no opportunity to catch an inverted intent
  (§5's incident, precisely).
- **A librarian's "distance" is intuitive and hard to invert by habit.** A programmer's intuition for
  "similarity" (bigger is better) collides directly with "distance" (smaller is better) in a way that is
  genuinely easy to get backwards, repeatedly, across a whole team.

---

## 7. Practical activity

**Primary activity — real pgvector SQL:** Work through §4.1–4.5 against a real PostgreSQL instance with
pgvector installed. This is the actual hands-on content this lesson's title promises.

**Fallback lab — verified Python, no database required:**
[`labs/m6/l08_pgvector_fallback.py`](../../labs/m6/l08_pgvector_fallback.py)

```bash
python labs/m6/l08_pgvector_fallback.py
```

### 7.2 Expected output (fallback lab)

`[EXECUTED]` — 2026-09-09, Python 3.10.11, NumPy 2.2.6.

```text
============================================================================
1. PGVECTOR'S THREE OPERATORS, MIRRORED: <->  <=>  <#>
============================================================================
  pgvector exposes three distance operators directly in SQL:
    <->   L2 (Euclidean) distance
    <=>   cosine distance  (1 - cosine similarity)
    <#>   negative inner product  (for max-inner-product search)
  [UNVERIFIED -- confirm exact operator names against your installed
  pgvector version's documentation before relying on this in SQL.]

  doc                  L2 (<->)   cosine (<=>)   neg-inner (<#>)
  doc_near               0.1414         0.0050           -2.0000
  doc_far_same_dir       2.8284         0.0000           -6.0000
  doc_other_dir          0.4243         0.0422           -2.0000

  Ranked by <->  : ['doc_near', 'doc_other_dir', 'doc_far_same_dir']
  Ranked by <=>  : ['doc_far_same_dir', 'doc_near', 'doc_other_dir']
  Ranked by <#>  : ['doc_far_same_dir', 'doc_near', 'doc_other_dir']

  On UN-normalised vectors, all three disagree on the best match --
  exactly M6-L02's finding, now against pgvector's own operator
  names rather than a generic 'cosine vs Euclidean' comparison.

  Normalise every vector to unit length first (M6-L02's proof):
    <->  ranking: ['doc_far_same_dir', 'doc_near', 'doc_other_dir']
    <=>  ranking: ['doc_far_same_dir', 'doc_near', 'doc_other_dir']
    <#>  ranking: ['doc_far_same_dir', 'doc_near', 'doc_other_dir']
    All three agree: True

  This is why pgvector documentation recommends <#> (inner product)
  for speed -- it skips the normalisation division entirely -- but
  ONLY gives cosine-equivalent rankings if every vector was
  normalised before insertion. Store un-normalised vectors and use
  <#> for speed, and you get a fast, wrong answer. [UNVERIFIED --
  confirm this guidance against current pgvector documentation.]

============================================================================
2. PGVECTOR'S TWO INDEX TYPES, MAPPED TO M6-L06's OWN MEASUREMENTS
============================================================================
  pgvector supports two approximate index types, matching the two
  families M6-L06 built and measured directly:

    CREATE INDEX ... USING ivfflat (embedding vector_cosine_ops)
      WITH (lists = 100);          -- M6-L06 section 1's clustering index
    SET ivfflat.probes = 5;        -- M6-L06's 'nprobe', by another name

    CREATE INDEX ... USING hnsw (embedding vector_cosine_ops)
      WITH (m = 16, ef_construction = 64);   -- M6-L06 section 3's graph
    SET hnsw.ef_search = 40;       -- M6-L06's search-width parameter
  [UNVERIFIED -- exact parameter names/defaults change between pgvector
  versions; confirm against your installed version's documentation.]

  Re-reading M6-L06's own measured table with pgvector's names substituted:

    ivfflat.probes  avg recall@10   time/query  speedup vs exact
                 1          84.7%        0.09ms             8.7x
                 2          87.7%        0.14ms             5.7x
                 5          93.0%        0.26ms             3.1x
                10          94.7%        0.82ms             1.0x
                20          96.0%        1.41ms             0.6x
                50          98.3%        5.24ms             0.2x

  (Reproduced from M6-L06's own measured run -- the same numbers,
  because it is the same algorithm. pgvector did not change the
  trade-off; it packaged it behind SQL, with persistence, filtering
  and concurrency added around it, exactly M6-L07's point.)

============================================================================
3. WHAT THIS LAB IS AND IS NOT
============================================================================
  REAL: section 1's operator arithmetic is exact, reproducible, and
  directly verifiable against pgvector's documented distance formulas.

  NOT A DATABASE: this file runs no SQL and touches no PostgreSQL
  instance. It mirrors pgvector's OPERATOR BEHAVIOUR in pure Python
  so you can verify the underlying arithmetic offline. The lesson's
  SQL blocks are the primary, real content -- run them yourself
  against an actual PostgreSQL + pgvector installation. This file is
  the fallback COURSE_PLAN.md's own design calls for, not a
  replacement for doing that.

  REUSED, NOT RE-MEASURED: section 2's recall/speed table is copied
  from M6-L06's own executed run, not re-measured here -- the point
  is the NAME MAPPING onto pgvector's actual parameters, not a new
  measurement.

Done.
```

### 7.3 Reading the result

**Section 1 is M6-L02's identity, now with names you will actually type into SQL.** The moment you
understand `<=>` is safe regardless of magnitude while `<#>` requires pre-normalization, a whole class of
"pgvector gives weird results" bug reports becomes diagnosable in seconds.

**Section 2 is the payoff of M6-L06 having been built from scratch rather than taken on faith.** Because
you measured `nprobe`'s real recall/speed curve yourself, `ivfflat.probes` in a real `SET` statement is
not a mysterious knob — it is a parameter whose behaviour you already know precisely, under a new name.

---

## 8. Common mistakes and troubleshooting

1. **Sorting a distance operator `DESC`.** §5 — silently returns the worst matches, with no error.
2. **Using `<#>` on un-normalized vectors expecting cosine-equivalent results.** §4.3 — fast and wrong.
3. **Mismatching embedding dimension between the model and the `vector(n)` column.** pgvector will
   reject this outright — a real guardrail against M6-L02's silent model-mismatch bug.
4. **Assuming `ivfflat`/`hnsw` parameters are pgvector-specific magic.** They are M6-L06's own measured
   parameters, under new names — reason about them the same way.
5. **Testing only that a query runs without error, never that it returns the right result.** §5 —
   "no error" and "correct" are different claims.
6. **Treating this lesson's SQL as verified simply because it appears in a course.** It is explicitly
   marked `[NOT EXECUTED]` — run and check it yourself.
7. **Choosing pgvector, or any alternative, without stating your own reasoning.** COURSE_PLAN.md's
   reasoning (§4.6) is specific to this course's context; yours may differ.

| Symptom | Likely cause | Fix |
|---|---|---|
| Search results seem inverted or nonsensical | `ORDER BY ... DESC` on a distance operator | Sort ascending; distance operators return smaller-is-better |
| `<#>`-based search gives inconsistent rankings | Vectors not normalized before insertion | Normalize at insert time, or switch to `<=>` |
| `INSERT` fails with a dimension error | Embedding dimension doesn't match `vector(n)` | Verify the model's actual output dimension (M6-L02) matches the column definition |
| An approximate index seems to add no speed benefit | `probes`/`ef_search` tuned too high (M6-L06's finding) | Measure the recall/speed curve for your own data; pick a value with headroom |

---

## 9. Security, privacy, reliability, cost

- **Reliability.** Always sort distance operators ascending, and test with a known query and a
  known-relevant result — "runs without error" is not evidence of correctness (§5).
- **Reliability.** Match the embedding column's dimension exactly to the producing model's actual output
  size — pgvector enforces this, closing one specific instance of M6-L02's model-compatibility bug.
- **Cost.** Choose `<#>` over `<=>` only when vectors are normalized at insert time — otherwise the speed
  gain comes with a correctness cost, not a genuine saving.
- **Cost.** `ivfflat`/`hnsw` parameters have the same real cost curve M6-L06 measured — tune them against
  your own data, not by assumption (M6-L06 §5.2).
- **Reliability.** State your own reasoning for choosing pgvector or an alternative, against your actual
  system's requirements (M6-L07's checklist) — this course's reasoning (§4.6) is a starting point, not a
  universal answer.

---

## 10. Exercises

### Exercise 1 — Beginner (~20 min)

1. Write the `CREATE TABLE` statement for a table storing 768-dimensional embeddings alongside a
   `title` column.
2. Which pgvector operator would you use for a general-purpose similarity search where vectors are not
   guaranteed to be normalized?
3. What SQL mistake produced the incident in §5, and how would you catch it in code review?
4. Name the two pgvector index types and the M6-L06 algorithm family each corresponds to.
5. State, in your own words, this course's stated reasoning for choosing pgvector.

### Exercise 2 — Intermediate (~40 min)

1. Set up PostgreSQL and pgvector on your own machine (or a container), and run §4.1–4.2's SQL for real.
2. Insert 20 real or synthetic documents with embeddings, and write a query combining a metadata filter
   with a similarity search (§4.5), even before formally covering M6-L09.
3. Run the Python fallback lab and confirm the operator-agreement result from §7.2 by hand for one
   document.
4. Create both an `ivfflat` and an `hnsw` index on the same table, and compare query plans
   (`EXPLAIN ANALYZE`) for a similarity search against each.
5. Write a test that would have caught §5's incident — a known query with a known most-relevant document.

### Exercise 3 — Challenge (~50 min)

1. Benchmark `ivfflat.probes` at several values against a real pgvector table you build, and compare your
   own measured recall/speed curve to M6-L06's.
2. Design a migration plan for re-embedding an existing pgvector table when the embedding model changes
   (tying to M6-L02's model-versioning discussion).
3. Research (conceptually) how one managed alternative (Pinecone, Weaviate, or Qdrant) handles the
   update/delete problem M6-L07 measured, and compare it to pgvector's approach.
4. Write a decision memo choosing between pgvector and one named alternative for a specific real or
   hypothetical system, using both COURSE_PLAN.md's reasoning and M6-L07's capability checklist.
5. Build a small Python client (using a real PostgreSQL driver) that performs the full pipeline: connect,
   create the extension and table, insert embeddings, query, and clean up — then run it against a real
   instance and report the actual results.

---

## 11. Quiz

*(Answers: [`answer-keys/module-06-answers.md`](../../answer-keys/module-06-answers.md#m6-l08).)*

**Q1.** In §7.1, ranking by `<->`, `<=>`, and `<#>` disagreed on un-normalised vectors but agreed exactly
once every vector was normalised. This is:

- A. A coincidence specific to the chosen example vectors.
- B. Evidence that pgvector's operators are unreliable.
- C. The same identity M6-L02 proved, now applied specifically to pgvector's three named distance operators.
- D. Only true for vectors with exactly two dimensions.

**Q2.** Why does pgvector documentation recommend `<#>` (inner product) for speed, per §5.1?

- A. It skips the normalisation division cosine similarity requires, making it computationally cheaper — but only gives correct cosine-equivalent rankings if vectors were normalized before insertion.
- B. It is the only operator that supports indexes.
- C. It always returns a value between 0 and 1.
- D. It is required by PostgreSQL for all vector columns.

**Q3.** pgvector's `ivfflat` and `hnsw` index types, per §5.2, correspond to:

- A. Two entirely unrelated algorithms never discussed elsewhere in this course.
- B. Two different distance metrics, not index structures.
- C. A single algorithm exposed under two different names.
- D. The same two ANN algorithm families (clustering-based and graph-based) measured directly in M6-L06, now exposed through SQL syntax.

**Q4.** The recall/speed table reproduced in §7.2 was:

- A. Measured fresh against a live pgvector instance for this lesson.
- B. Copied from M6-L06's own executed measurement, to show the parameter-name mapping onto pgvector, not re-measured as a new experiment.
- C. Entirely fabricated for illustrative purposes.
- D. Measured using a different corpus than M6-L06 used.

**Q5.** Why are this lesson's SQL blocks marked as requiring verification against a real PostgreSQL
instance, rather than being labeled EXECUTED?

- A. SQL cannot be verified under any circumstances.
- B. pgvector does not actually exist.
- C. No PostgreSQL/pgvector instance was available in the environment that authored this lesson, so the SQL could not actually be run and checked.
- D. The SQL is intentionally incorrect as a teaching exercise.

**Q6.** Per Design Assumption A2 (COURSE_PLAN.md), the course's stated reason for choosing pgvector as
the primary vector store is:

- A. It is the fastest vector database available under any circumstance.
- B. It was the first vector database ever created.
- C. It requires no SQL knowledge at all.
- D. It lets a learner who already understands relational databases use one system for both rows and vectors, without a new vendor account.

**Q7.** What does the Python fallback lab in this lesson actually verify?

- A. The underlying distance-operator arithmetic and the algorithm-parameter mapping, not SQL syntax or a running database.
- B. That PostgreSQL is correctly installed.
- C. The exact query performance of a real pgvector deployment.
- D. That the SQL statements in this lesson execute without syntax errors.

**Q8.** If vectors are stored un-normalized in a pgvector table and queried with the `<#>` operator for
speed, per §5.1, the result is:

- A. An error preventing the query from running.
- B. A fast query that returns a ranking inconsistent with true cosine similarity — a fast, wrong answer.
- C. Identical results to using `<=>`.
- D. The query automatically normalizes the vectors first.

**Q9.** The `ivfflat.probes` and `hnsw.ef_search` settings in pgvector, per §5.2, control:

- A. The dimension of stored vectors.
- B. Whether metadata filtering is enabled.
- C. The same recall-vs-speed trade-off as M6-L06's nprobe and search-width parameters, under pgvector's own naming.
- D. The number of rows returned by every query, regardless of LIMIT.

**Q10.** Why does this lesson reuse M6-L06's exact measured numbers rather than presenting new
pgvector-specific benchmarks?

- A. Because pgvector implements the same underlying algorithms; the trade-off is mathematically identical, and no live instance was available to re-benchmark in this environment.
- B. Because pgvector's algorithms are completely different from M6-L06's.
- C. Because benchmarking is not possible for vector databases.
- D. Because M6-L06's numbers are more accurate than any pgvector-specific measurement could be.

**Q11.** This lesson's approach to a missing database instance follows:

- A. An improvised workaround unique to this lesson.
- B. A decision to skip hands-on content entirely.
- C. Standard practice for every lesson in this course, regardless of resource availability.
- D. The course's own stated design principle of providing a pure-Python fallback for offline labs, not an improvised workaround.

**Q12.** The general relationship between this lesson and M6-L06/M6-L07 is:

- A. This lesson contradicts what M6-L06 and M6-L07 taught.
- B. M6-L08 shows that a real, specific system (pgvector) implements the exact algorithms and trade-offs those two lessons already taught and measured directly.
- C. M6-L08 is entirely unrelated to the previous two lessons.
- D. M6-L06 and M6-L07 will be superseded by this lesson's content.

**Q13.** *(Written, rubric-graded.)* In under 150 words: a colleague's pgvector-backed search feature
returns results without error, but users report the results seem unrelated to their queries. Based on
this lesson, what is the first thing you would check, and why?

---

## 12. Revision notes

- **pgvector puts M6-L01–M6-L07's concepts into real SQL** — nothing about the underlying mathematics or
  algorithms is new; only the interface is.
- **`<->`, `<=>`, and `<#>` are L2, cosine, and negative inner-product distance.** Verified: they
  disagree on un-normalised vectors and agree exactly once normalised — M6-L02's identity, under
  pgvector's own names.
- **`<#>` is fastest but only cosine-equivalent on pre-normalized vectors.** Using it on un-normalized
  data is a fast, wrong answer, not a genuine saving.
- **`ivfflat` and `hnsw` are M6-L06's own algorithms, renamed.** `lists`/`probes` and
  `m`/`ef_construction`/`ef_search` are the same parameters already measured directly — the same
  recall/speed trade-off, the same real optimum, the same risk of over-tuning into a slower-than-no-index
  configuration.
- **Distance operators sort ascending, not descending** — a genuinely easy, genuinely silent mistake that
  produces error-free, confidently wrong results.
- **This course's choice of pgvector is a stated, specific decision** (COURSE_PLAN.md A2), not a claim
  that it is universally best — evaluate alternatives against your own system's actual requirements
  (M6-L07's checklist).
- **This lesson's SQL is unverified in the strict sense** — reviewed, not executed against a live
  instance. Run it yourself before trusting it in production.

---

## 13. Completion checklist

- [ ] I have run (or will run) this lesson's SQL against a real PostgreSQL + pgvector instance.
- [ ] I know which distance operator to use, and why `<#>` requires pre-normalized vectors.
- [ ] I always sort distance operators ascending, and I know why sorting DESC is a silent bug.
- [ ] I can map pgvector's `ivfflat`/`hnsw` parameters onto M6-L06's own measured concepts.
- [ ] I test with a known query and known-relevant result, not just "the query runs without error."
- [ ] I can state this course's reasoning for choosing pgvector, and evaluate alternatives against my own requirements.
- [ ] I scored 10/13 on the quiz.

---

## 14. References

- pgvector — GitHub repository and README (operators, index types, syntax).
  <https://github.com/pgvector/pgvector> `[UNVERIFIED]`
- PostgreSQL documentation — `CREATE EXTENSION`, `CREATE INDEX`.
  <https://www.postgresql.org/docs/current/sql-createindex.html> `[UNVERIFIED]`
- COURSE_PLAN.md, this repository — Design assumption A2 (this course's stated reasoning for choosing
  pgvector). `[STABLE — internal course document]`

---

## 15. Next lesson

→ [M6-L09 — Metadata, Filtering and Filtered-ANN Pitfalls](M6-L09-metadata-filtering.md)

You can now write real similarity search SQL and tune a real approximate index. Next: the full treatment
of the `WHERE` clause this lesson only previewed — combining metadata filters with approximate search
correctly, and the specific ways doing it carelessly breaks recall.
