# M2-L16 — SQL Fundamentals and Database Access from Python

| | |
|---|---|
| **Lesson ID** | M2-L16 |
| **Difficulty** | 2 (Core) |
| **Estimated study time** | 2.5 hours |
| **Prerequisites** | [M2-L09](M2-L09-files-json-env.md) |

---

> This lesson is a prerequisite for **M6-L08 (pgvector)** and **M7-L15 (permission-aware retrieval)**.
> The course deliberately teaches SQL before any vector-database abstraction, because a vector store
> is a database and the same rules about indexes, transactions and injection apply.

---

## 1. Learning objectives

1. **Write** SELECT queries with filtering, ordering, joining, grouping and limits.
2. **Use** parameterised queries and **explain** why string formatting is a vulnerability.
3. **Design** a small schema with keys, constraints and appropriate types.
4. **Explain** what an index does, and **measure** its effect.
5. **Use** transactions correctly, including rollback on failure.

---

## 2. Vocabulary

| Term | Definition |
|---|---|
| **Table / row / column** | The relational structure: entities, records, attributes. |
| **Primary key** | A column uniquely identifying each row. |
| **Foreign key** | A column referencing another table's primary key. |
| **Constraint** | A rule the database enforces: `NOT NULL`, `UNIQUE`, `CHECK`. |
| **Index** | A structure making lookups on a column fast. |
| **Full table scan** | Reading every row because no usable index exists. |
| **JOIN** | Combining rows from two tables on a matching condition. |
| **Aggregate** | A function over many rows: `COUNT`, `SUM`, `AVG`. |
| **Transaction** | A group of statements applied all-or-nothing. |
| **Commit / rollback** | Making a transaction permanent / undoing it. |
| **ACID** | Atomicity, Consistency, Isolation, Durability. |
| **Parameterised query** | A query with placeholders, values sent separately. |
| **SQL injection** | Attacker-supplied text changing the meaning of a query. |
| **Migration** | A versioned, repeatable schema change. |
| **N+1 query** | Fetching a list, then one query per item. A classic performance bug. |

---

## 3. Plain-language explanation

A relational database stores data in tables and lets you ask questions in SQL.

```sql
SELECT ticket_id, priority
FROM tickets
WHERE channel = 'email' AND priority <= 2
ORDER BY created_at DESC
LIMIT 10;
```

Read in the order it executes, which is *not* the order it is written:

1. `FROM tickets` — which table
2. `WHERE ...` — keep matching rows
3. `SELECT ...` — choose columns
4. `ORDER BY ...` — sort
5. `LIMIT ...` — take the first N

Understanding this order explains a common confusion: you cannot use a `SELECT` alias in a `WHERE`
clause, because `WHERE` runs first.

**The one rule that matters most:**

```python
# NEVER - SQL injection
cursor.execute(f"SELECT * FROM tickets WHERE id = '{ticket_id}'")

# ALWAYS - parameterised
cursor.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,))
```

This is the same shape as the f-string warning in M2-L02 §5.4, and it returns again in M5-L05 as
prompt injection. **Interpolating untrusted text into a command string is the general vulnerability;
SQL injection is one instance of it.**

### Why SQLite here

The labs use **SQLite** — a file-based database in the Python standard library, needing no server. It
is a genuine SQL database with real transactions, and everything you learn transfers.

Where it differs from PostgreSQL, the lesson says so. M6-L08 moves to PostgreSQL because pgvector
needs it.

---

## 4. Analogy

**A table is a spreadsheet; an index is its sorted lookup tab.**

Without a tab you read every row to find one. With one you jump straight there. Adding tabs costs
space and slows down insertion, because every new row must be filed.

### Where the analogy breaks

1. **A spreadsheet has no constraints.** A database *refuses* invalid data — a foreign key to a
   non-existent row is rejected, not merely wrong.
2. **Spreadsheets have no transactions.** Halfway through editing a spreadsheet you have a half-edited
   spreadsheet. Halfway through a transaction, other readers still see the original state, and a
   failure undoes everything.
3. **Indexes are not just sorted copies.** They are B-trees with their own cost model, and the query
   planner may ignore one it judges unhelpful.
4. **A spreadsheet is single-user.** Concurrency, locking and isolation have no spreadsheet analogue,
   and they are where database bugs actually live.

---

## 5. Detailed technical explanation

### 5.1 Creating a schema

```sql
CREATE TABLE customers (
    customer_id TEXT PRIMARY KEY,
    name        TEXT NOT NULL,
    tier        TEXT NOT NULL CHECK (tier IN ('free', 'pro', 'enterprise')),
    created_at  TEXT NOT NULL
);

CREATE TABLE tickets (
    ticket_id   TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL REFERENCES customers(customer_id),
    text        TEXT NOT NULL,
    priority    INTEGER NOT NULL CHECK (priority BETWEEN 1 AND 5),
    channel     TEXT NOT NULL,
    created_at  TEXT NOT NULL,
    resolved_at TEXT
);

CREATE INDEX idx_tickets_customer ON tickets(customer_id);
CREATE INDEX idx_tickets_created  ON tickets(created_at);
```

Note what the schema **enforces**: priority cannot be 99, tier cannot be `"platinum"`, and a ticket
cannot reference a customer that does not exist. These are the same constraints you wrote in Pydantic
(M2-L08) — and having them in **both** places is correct, not redundant. Pydantic gives a good error
message at the API boundary; the database guarantees the invariant even if a script, a migration or a
second service writes directly.

`resolved_at` is nullable: `NULL` means "not resolved". `NULL` is not zero and not empty string; it
means *unknown/absent*, and comparisons with it use `IS NULL`, never `= NULL`.

### 5.2 Querying

```sql
SELECT * FROM tickets WHERE priority <= 2;
SELECT ticket_id, priority FROM tickets ORDER BY created_at DESC LIMIT 10;
SELECT * FROM tickets WHERE channel IN ('email', 'chat');
SELECT * FROM tickets WHERE text LIKE '%refund%';
SELECT * FROM tickets WHERE resolved_at IS NULL;
```

**Aggregates and grouping:**

```sql
SELECT channel, COUNT(*) AS n, AVG(priority) AS avg_priority
FROM tickets
GROUP BY channel
HAVING COUNT(*) > 5
ORDER BY n DESC;
```

`WHERE` filters **rows before** grouping; `HAVING` filters **groups after**. Using `WHERE` on an
aggregate is an error, and this is the reason.

**Joins:**

```sql
SELECT t.ticket_id, t.priority, c.name, c.tier
FROM tickets t
JOIN customers c ON c.customer_id = t.customer_id
WHERE c.tier = 'enterprise';
```

| Join | Keeps |
|---|---|
| `INNER JOIN` (default) | Rows matching in both tables |
| `LEFT JOIN` | All left rows; `NULL` where no match |
| `CROSS JOIN` | Every combination — rarely intended |

**A `LEFT JOIN` followed by a `WHERE` on the right table silently becomes an inner join**, because
`NULL` fails the condition. Put such conditions in the `ON` clause instead. This is one of the most
common SQL mistakes.

### 5.3 Parameterised queries

```python
import sqlite3

conn = sqlite3.connect("course.db")
conn.row_factory = sqlite3.Row          # rows accessible by column name

cur = conn.execute(
    "SELECT * FROM tickets WHERE customer_id = ? AND priority <= ?",
    (customer_id, max_priority),
)
for row in cur:
    print(row["ticket_id"], row["priority"])
```

Placeholder styles differ by driver: SQLite uses `?`, psycopg uses `%s`, and named forms
(`:name`) exist for both. **The values are never part of the SQL text** — the driver sends them
separately, so no input can change the query's structure.

**What you cannot parameterise:** table and column names, and `ORDER BY` direction. If those must be
dynamic, validate against an allow-list:

```python
ALLOWED_SORT = {"created_at", "priority", "ticket_id"}
if sort_column not in ALLOWED_SORT:
    raise ValueError(f"invalid sort column: {sort_column}")
query = f"SELECT * FROM tickets ORDER BY {sort_column} DESC"   # safe: allow-listed
```

An allow-list, not an escape function. This exact pattern reappears in M9-L13 for MCP tools.

### 5.4 Transactions

```python
try:
    with conn:                                    # commits on success, rolls back on exception
        conn.execute("UPDATE accounts SET balance = balance - ? WHERE id = ?", (100, "a"))
        conn.execute("UPDATE accounts SET balance = balance + ? WHERE id = ?", (100, "b"))
except sqlite3.Error:
    ...                                            # both updates were undone
```

`with conn` is a transaction, not a connection context manager — a genuine confusion in the SQLite
API. It does **not** close the connection.

**Atomicity is the property that matters:** the debit and credit either both happen or neither does.
Without a transaction, a failure between them destroys money.

### 5.5 Indexes, measured

An index turns a full scan (O(n)) into a tree lookup (O(log n)).

```sql
CREATE INDEX idx_tickets_customer ON tickets(customer_id);
EXPLAIN QUERY PLAN SELECT * FROM tickets WHERE customer_id = 'C-042';
```

Without an index the plan says `SCAN tickets`; with one, `SEARCH tickets USING INDEX ...`. **Reading
the query plan is the skill** — it tells you what the database will actually do rather than what you
hoped.

Costs: extra storage, slower writes (every insert updates every index), and no benefit if the query
cannot use it — for example `WHERE lower(name) = 'x'` cannot use a plain index on `name`.

**Index the columns you filter and join on.** Do not index everything.

### 5.6 The N+1 problem

```python
tickets = conn.execute("SELECT * FROM tickets LIMIT 100").fetchall()
for t in tickets:                                    # 100 more queries!
    customer = conn.execute(
        "SELECT name FROM customers WHERE customer_id = ?", (t["customer_id"],)
    ).fetchone()
```

101 queries where 1 would do. Use a join, or fetch all the needed customers in one `IN` query. This is
invisible on 10 rows in development and catastrophic on 10,000 in production — and ORMs make it
especially easy to write by accident.

### 5.7 SQLite versus PostgreSQL

| | SQLite | PostgreSQL |
|---|---|---|
| Setup | A file; zero config | A server |
| Concurrency | One writer at a time | Many writers |
| Types | Dynamic, loosely enforced | Strict |
| Extensions | Limited | **pgvector**, full-text search, JSONB |
| Right for | Tests, local dev, embedded | Production, and Module 6 onward |

SQLite's loose typing is worth knowing: by default it will accept a string in an `INTEGER` column.
This course's labs use `CHECK` constraints to compensate, and it is a reminder that a permissive
database is not a substitute for validation.

### 5.8 Assumptions and limitations

- SQL dialects differ. `LIMIT` is standard; date functions and upserts are not.
- ORMs (SQLAlchemy) add mapping and migrations, but you must still read the SQL they emit — most ORM
  performance problems are N+1 or missing indexes.
- Schema changes need **migrations** (Alembic, or plain versioned SQL files), not hand-edits.
- Vector similarity search needs an extension (pgvector). SQLite cannot do it natively.

---

## 6. Worked example — a query, made correct

Requirement: "the 10 most recent unresolved high-priority tickets for enterprise customers, with the
customer name."

**v1 — string formatting.**

```python
q = f"SELECT * FROM tickets WHERE priority <= {priority} AND channel = '{channel}'"
```

**Injectable.** `channel = "email' OR '1'='1"` returns every row. Worse,
`channel = "x'; DROP TABLE tickets; --"` is the classic case. Never do this.

**v2 — parameterised.**

```python
q = "SELECT * FROM tickets WHERE priority <= ? AND channel = ?"
conn.execute(q, (priority, channel))
```

Safe. But it does not answer the question — no customer name, no unresolved filter, no limit.

**v3 — the join.**

```sql
SELECT t.ticket_id, t.priority, t.created_at, c.name, c.tier
FROM tickets t
JOIN customers c ON c.customer_id = t.customer_id
WHERE c.tier = 'enterprise'
  AND t.priority <= 2
  AND t.resolved_at IS NULL
ORDER BY t.created_at DESC
LIMIT 10;
```

Note `IS NULL`, not `= NULL` — the latter is never true, so it silently returns nothing.

**v4 — parameterised, with a validated sort column.**

```python
ALLOWED_SORT = {"created_at", "priority"}

def recent_urgent(conn, tier: str, max_priority: int, *,
                  sort: str = "created_at", limit: int = 10) -> list[sqlite3.Row]:
    if sort not in ALLOWED_SORT:
        raise ValueError(f"invalid sort column: {sort!r}")
    query = f"""
        SELECT t.ticket_id, t.priority, t.created_at, c.name, c.tier
        FROM tickets t
        JOIN customers c ON c.customer_id = t.customer_id
        WHERE c.tier = ? AND t.priority <= ? AND t.resolved_at IS NULL
        ORDER BY t.{sort} DESC
        LIMIT ?
    """
    return conn.execute(query, (tier, max_priority, limit)).fetchall()
```

Values are parameterised; the one thing that cannot be (a column name) is allow-listed. The f-string
is safe here **only because `sort` was checked against a fixed set first** — and that reasoning
should be written in a comment, because the next reader will see an f-string in SQL and worry.

**v5 — index it.** The query filters on `c.tier`, `t.priority` and `t.resolved_at`, and joins on
`customer_id`. Without indexes the database scans both tables. The lab measures the difference on
20,000 rows.

---

## 7. Practical activity

**File:** [`labs/m2/l16_sql.py`](../../labs/m2/l16_sql.py)

```bash
python3 labs/m2/l16_sql.py
```

Standard library only (`sqlite3`), writing to a temporary file. Builds a schema, inserts 20,000
synthetic rows, demonstrates a **real SQL injection** and its fix, measures indexed versus unindexed
queries with `EXPLAIN QUERY PLAN`, shows transaction rollback, demonstrates the N+1 problem, and
shows the `LEFT JOIN` + `WHERE` trap.

### 7.1 Important lines

| Construct | Why |
|---|---|
| `conn.row_factory = sqlite3.Row` | Access columns by name instead of index. |
| `conn.execute(sql, (a, b))` | Parameterised. The values never enter the SQL text. |
| `EXPLAIN QUERY PLAN` | Shows `SCAN` versus `SEARCH ... USING INDEX`. |
| `with conn:` | A transaction — commits on success, rolls back on exception. |
| `PRAGMA foreign_keys = ON` | SQLite does **not** enforce foreign keys by default. |

### 7.2 Expected output

`[EXECUTED]` 2026-09-08, Python 3.12.3, SQLite 3.50.4. Seeded, so counts reproduce; timings vary:

```
==========================================================================
SQL FUNDAMENTALS
==========================================================================
Building a database with 500 customers and 20,000 tickets...

--------------------------------------------------------------------------
1. QUERY BASICS
--------------------------------------------------------------------------
  total tickets: 20,000

  Tickets per channel (GROUP BY):
    chat      6,678  avg priority 3.0
    phone     6,665  avg priority 3.03
    email     6,657  avg priority 3.0

  IS NULL vs = NULL:
    WHERE resolved_at IS NULL -> 6,059 rows
    WHERE resolved_at =  NULL -> 0 rows   <-- always zero
    Comparison with NULL is never true. No error is raised.

  A join (enterprise customers, urgent unresolved tickets):
    T-000034  p1  Customer 129 (enterprise)
    T-000089  p1  Customer 461 (enterprise)
    T-000196  p1  Customer 365 (enterprise)
    T-000405  p1  Customer 50 (enterprise)
    T-000512  p1  Customer 87 (enterprise)

--------------------------------------------------------------------------
2. SQL INJECTION - a real one, then the fix
--------------------------------------------------------------------------
  vulnerable_search('email')          -> 6,657 rows (correct)
  vulnerable_search("email' OR '1'='1") -> 20,000 rows  <-- EVERY ROW

  The query the database actually received:
    SELECT ... WHERE channel = 'email' OR '1'='1'
    The attacker's quote closed the string and OR '1'='1' made the
    condition always true. The filter is gone.

  safe_search('email')                -> 6,657 rows (correct)
  safe_search("email' OR '1'='1")     -> 0 rows  <-- treated as a literal channel name

  Identifiers cannot be parameterised, so allow-list them:
    sort='priority' -> ok, 3 rows
    sort='priority; DROP TABLE tickets' -> ValueError: invalid sort column: 'priority; DROP TABLE tickets'

--------------------------------------------------------------------------
3. INDEXES - measured, with the query plan
--------------------------------------------------------------------------
  Table has 20,000 rows.

              plan                                                per query
  no index    SCAN tickets                                          0.950 ms
  indexed     SEARCH tickets USING COVERING INDEX idx_tickets_cu    0.007 ms
  speed-up: 145x

  SCAN means every row was read. SEARCH ... USING INDEX means the
  database jumped straight to the matching rows.

  When an index does NOT help - a function on the column:
    WHERE lower(customer_id) = ?  ->  SCAN tickets
    The index is on customer_id, not on lower(customer_id).

--------------------------------------------------------------------------
4. TRANSACTIONS - all or nothing
--------------------------------------------------------------------------
  before: C-0001=379  C-0002=125

  A transfer that fails halfway, INSIDE a transaction:
    caught: network failure between the two updates
    after : C-0001=379  C-0002=125   <-- UNCHANGED, rolled back

  The same failure WITHOUT a transaction:
    after : C-0001=279  C-0002=125   <-- 100 has VANISHED

--------------------------------------------------------------------------
5. THE N+1 PROBLEM
--------------------------------------------------------------------------
  Fetching 300 tickets with their customer names:
    N+1 version :  301 queries       3.2 ms
    JOIN version:    1 query         0.5 ms
    6x slower, same 300 rows of data

  On 10 rows in development this is invisible. On 10,000 rows in
  production it is an outage. ORMs make it especially easy to
  write by accident, because the extra queries are implicit.

--------------------------------------------------------------------------
6. THE LEFT JOIN + WHERE TRAP
--------------------------------------------------------------------------
  LEFT JOIN, no filter                     -> 501 customers
  LEFT JOIN + WHERE t.priority <= 2        -> 500 customers  <-- lost some
  LEFT JOIN ... ON ... AND t.priority <= 2 -> 501 customers  <-- correct

  'Silent Customer' has no tickets at all. In the middle query its
  joined columns are NULL, and NULL <= 2 is not true, so the row is
  filtered out. The LEFT JOIN silently became an INNER JOIN.
  Conditions on the right-hand table belong in ON, not WHERE.

--------------------------------------------------------------------------
7. SQLITE FOREIGN KEYS ARE OFF BY DEFAULT
--------------------------------------------------------------------------
  foreign_keys = OFF -> inserted an orphan ticket. Rows: 1
  foreign_keys = ON  -> IntegrityError: FOREIGN KEY constraint failed

  SQLite defaults foreign_keys to OFF for backwards compatibility.
  Every connection must enable it explicitly, or your referential
  integrity is decorative.

==========================================================================
```

### 7.3 Reading the result

**Section 2 is a working SQL injection, not a description of one:**

```
vulnerable_search('email')            ->  6,657 rows (correct)
vulnerable_search("email' OR '1'='1") -> 20,000 rows  <-- EVERY ROW
```

The attacker's apostrophe closed the string literal and `OR '1'='1'` made the condition
unconditionally true. **The filter disappeared entirely**, and the function returned the whole table.

Now look at the fix:

```
safe_search("email' OR '1'='1")       ->      0 rows
```

Zero — because the parameterised version treated the entire payload as a *literal channel name*, and
no channel is called `email' OR '1'='1`. The value never had the opportunity to be interpreted as
SQL. That is the whole mechanism: **the driver sends the statement and the values down separate
paths**, so no value can alter the statement's structure.

And the identifier case, which cannot be parameterised, is rejected by the allow-list rather than by
escaping:

```
sort='priority; DROP TABLE tickets' -> ValueError: invalid sort column
```

**Section 3 quantifies indexing on 20,000 rows:**

| | Query plan | Per query |
|---|---|---|
| No index | `SCAN tickets` | 0.866 ms |
| Indexed | `SEARCH tickets USING COVERING INDEX ...` | **0.006 ms** |

**134× faster.** And the plan text tells you *why*: `SCAN` means every one of the 20,000 rows was
read; `SEARCH ... USING INDEX` means the database went straight to the matches. Learning to read that
one line is more valuable than memorising indexing rules.

The final line of that section is the caveat people forget:

```
WHERE lower(customer_id) = ?  ->  SCAN tickets
```

The index is on `customer_id`, not on `lower(customer_id)`. Wrapping a column in a function makes the
index unusable, and nothing warns you — the query simply gets slow as the table grows.

**Section 4 shows atomicity destroying and preserving money:**

```
inside a transaction, failing halfway  -> C-0001=379   UNCHANGED, rolled back
without a transaction, failing halfway -> C-0001=279   100 has VANISHED
```

The second case debited an account and never credited the other. There is no error, no log, and no
way to detect it later except by reconciliation. **A multi-statement write without a transaction is a
data-corruption bug waiting for its first failure.**

**Section 5:** 301 queries versus 1, and 6× slower — on a local SQLite file with 300 rows. Across a
network to a real database, each of those 300 extra round trips costs a millisecond or more, and the
gap becomes hundreds of times rather than six.

**Section 6 catches the `LEFT JOIN` trap in the act.** 501 customers before the filter, **500**
after adding `WHERE t.priority <= 2`, 501 again once the condition moves into `ON`. "Silent Customer"
has no tickets, so its joined columns are `NULL`, and `NULL <= 2` is not true — the row is filtered
away. The `LEFT JOIN` silently became an `INNER JOIN`, and the only symptom is a slightly smaller
result set that looks entirely plausible.

**Section 7:** with `PRAGMA foreign_keys = OFF` — SQLite's **default** — a ticket referencing a
non-existent customer inserted happily. Turn it on and the same insert raises `IntegrityError`. Every
connection must enable it explicitly, or the `REFERENCES` clause in your schema is documentation
rather than a constraint.

**Verification:** confirm the injection returns 20,000 rows and the safe version returns 0, the index
plan changes from `SCAN` to `SEARCH`, the transaction rollback leaves both balances unchanged, and
the LEFT JOIN counts are 501 / 500 / 501.

---

## 8. Common mistakes and troubleshooting

1. **String formatting values into SQL.** The vulnerability.
2. **`= NULL` instead of `IS NULL`.** Always false.
3. **`SELECT *` in application code.** Breaks when columns change; fetches data you do not need.
4. **N+1 queries.**
5. **No transaction around multi-statement updates.**
6. **Missing indexes on filter and join columns.**
7. **`WHERE` on the right table of a `LEFT JOIN`** — silently becomes an inner join.
8. **Forgetting `PRAGMA foreign_keys = ON`** in SQLite.
9. **Not closing connections**, or sharing one across threads.

| Error / symptom | Cause | Fix |
|---|---|---|
| `sqlite3.OperationalError: no such column` | Typo or wrong alias | Check the schema and aliases |
| Query returns nothing with a NULL filter | `= NULL` | Use `IS NULL` |
| Query slow as data grows | Full table scan | Add an index; read `EXPLAIN QUERY PLAN` |
| `UNIQUE constraint failed` | Duplicate key | Use an upsert, or check first |
| `FOREIGN KEY constraint failed` | Referenced row missing | Insert the parent first |
| Partial update after an error | No transaction | Wrap in `with conn:` |
| `database is locked` | Concurrent writes in SQLite | One writer; use PostgreSQL for real concurrency |

---

## 9. Security, privacy, reliability and cost

- **Security.** SQL injection remains one of the most exploited vulnerability classes. Parameterise
  every value; allow-list every identifier. **This becomes acute in Module 8**, where an agent may
  construct queries — never let a model emit raw SQL that you execute.
- **Security.** Grant the application the least privilege it needs. A service that only reads should
  not hold DELETE or DDL rights.
- **Privacy.** Databases accumulate personal data. Deletion requests mean rows *and* backups *and*
  read replicas *and* any derived exports (M10-L06). Design for deletion.
- **Reliability.** Transactions are how you avoid half-applied changes. Multi-step writes without one
  are a data-corruption bug waiting for a failure.
- **Cost.** A missing index can multiply query time and cloud database cost by orders of magnitude.
  Reading query plans is a cost-control skill.

---

## 10. Exercises

### Exercise 1 — Beginner (~20 min)

Using the lab's database, write queries for:

1. All tickets with priority 1.
2. The 5 most recent tickets, newest first.
3. The count of tickets per channel.
4. Tickets that are not yet resolved.
5. Tickets for enterprise customers, with the customer name.
6. Channels with more than 100 tickets, ordered by count.

### Exercise 2 — Intermediate (~30 min)

1. Write `search_tickets(conn, *, channel=None, max_priority=None, unresolved_only=False,
   limit=20)` that builds a **parameterised** query with only the filters supplied. Prove no
   f-string interpolation of values occurs.
2. Add a `sort` parameter accepting only `created_at` or `priority`, rejecting anything else. Test it
   with `"priority; DROP TABLE tickets"`.
3. Measure the query with and without an index on `channel`. Report both times and both query plans.
4. Write an N+1 version and a joined version of "list 200 tickets with their customer names". Report
   the query count and the time for each.

### Exercise 3 — Challenge (~35 min)

1. Demonstrate a working SQL injection against a vulnerable function: extract all rows using an
   `OR '1'='1'` payload. Then fix it and prove the same payload is now treated as a literal string.
2. Implement a transfer between two customers' credit balances that debits one and credits the other.
   Show that an exception between the two statements leaves **both** balances unchanged.
3. Turn `PRAGMA foreign_keys` off and on. Insert a ticket referencing a non-existent customer in each
   case. Explain the difference and why SQLite's default is dangerous.
4. Construct the `LEFT JOIN` + `WHERE` trap: list all customers and their ticket counts including
   customers with zero tickets, then break it by adding `WHERE t.priority <= 2`, then fix it by
   moving that condition into the `ON` clause. Report all three row counts.
5. Using `EXPLAIN QUERY PLAN`, find one query in your solutions that still scans, and either fix it
   or explain why the scan is acceptable.

---

## 11. Quiz

**Q1.** Why is `f"SELECT * FROM t WHERE id = '{value}'"` dangerous?

- A. It is slow.
- B. Attacker-supplied text becomes part of the SQL statement, so it can change the query's meaning —
  SQL injection.
- C. f-strings cannot contain quotes.
- D. It is not dangerous if the value is a number.

**Q2.** What does a parameterised query do differently?

- A. Escapes quotes in the string.
- B. Sends the SQL text and the values separately, so no value can alter the statement's structure.
- C. Encrypts the values.
- D. Validates types.

**Q3.** Which cannot be parameterised, and what should you do instead?

- A. Nothing; everything can be.
- B. Table and column names (and sort direction) — validate them against an allow-list.
- C. Numbers; convert them to strings.
- D. NULL values.

**Q4.** `WHERE resolved_at = NULL` returns no rows even though many are NULL. Why?

- A. A syntax error.
- B. Comparison with `NULL` is never true; use `IS NULL`.
- C. The column is misspelled.
- D. NULL is stored as an empty string.

**Q5.** What is the difference between `WHERE` and `HAVING`?

- A. They are interchangeable.
- B. `WHERE` filters rows before grouping; `HAVING` filters groups after aggregation.
- C. `HAVING` is for joins.
- D. `WHERE` only works on indexed columns.

**Q6.** What is the N+1 problem?

- A. Off-by-one in a LIMIT.
- B. Fetching a list with one query, then issuing one additional query per item — 101 queries where a
  single join would do.
- C. Too many indexes.
- D. A transaction error.

**Q7.** What does `with conn:` do in `sqlite3`?

- A. Closes the connection afterwards.
- B. Opens a transaction, committing on success and rolling back if an exception is raised. It does
  **not** close the connection.
- C. Enables foreign keys.
- D. Nothing.

**Q8.** A `LEFT JOIN` followed by `WHERE right_table.column = 'x'` behaves how?

- A. As intended.
- B. It silently becomes an inner join, because `NULL` fails the `WHERE` condition — put the
  condition in the `ON` clause instead.
- C. It raises an error.
- D. It returns every row.

**Q9.** When does an index **not** help?

- A. Never; indexes always help.
- B. When the query cannot use it — for example a function applied to the column
  (`WHERE lower(name) = 'x'`), or a leading wildcard `LIKE '%x'`.
- C. Only on small tables.
- D. Only for text columns.

**Q10.** *(Written, rubric-graded.)* In under 80 words, explain why an application should validate
input with Pydantic **and** enforce constraints in the database, rather than choosing one.

---

## 12. Revision notes

- Execution order: **FROM → WHERE → GROUP BY → HAVING → SELECT → ORDER BY → LIMIT.**
- **Always parameterise values** (`?` / `%s`). Identifiers cannot be parameterised — **allow-list**
  them. Same shape as prompt injection (M5-L13).
- **`IS NULL`, never `= NULL`.** NULL means unknown.
- `WHERE` filters rows; `HAVING` filters groups.
- **`LEFT JOIN` + `WHERE` on the right table = inner join.** Move the condition into `ON`.
- **Indexes** turn scans into searches. Index filter and join columns; they cost storage and write
  speed. **Read `EXPLAIN QUERY PLAN`** — `SCAN` versus `SEARCH ... USING INDEX`.
- Indexes do not help through functions or leading-wildcard `LIKE`.
- **N+1**: one query then one per row. Join instead.
- **`with conn:`** is a transaction (commit/rollback), not connection cleanup.
- **Constraints in the database *and* Pydantic at the boundary** — different jobs, both needed.
- SQLite: single writer, loose typing, **foreign keys off by default** (`PRAGMA foreign_keys = ON`).

---

## 13. Completion checklist

- [ ] I can write SELECT with filter, join, group, order and limit.
- [ ] I always parameterise values and allow-list identifiers.
- [ ] I performed a working SQL injection and then fixed it.
- [ ] I read a query plan and saw SCAN become SEARCH.
- [ ] I measured the index speed-up myself.
- [ ] I demonstrated transaction rollback leaving data unchanged.
- [ ] I reproduced the N+1 problem and the LEFT JOIN trap.
- [ ] I scored 7/10 on the quiz.

---

## 14. References

- SQLite documentation. <https://www.sqlite.org/docs.html> `[UNVERIFIED]`
- Python docs, `sqlite3`. <https://docs.python.org/3/library/sqlite3.html> `[UNVERIFIED]`
- PostgreSQL tutorial. <https://www.postgresql.org/docs/current/tutorial.html> `[UNVERIFIED]`
- OWASP, SQL Injection Prevention Cheat Sheet.
  <https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html>
  `[UNVERIFIED]`

---

## 15. Next lesson

→ [M2-L17 — Git, Branches and Dependency Management](M2-L17-git-dependencies.md)

You can store and query data. Next: version control and dependency management — how the code and its
environment get reproduced on someone else's machine, and in CI.
