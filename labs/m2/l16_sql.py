"""M2-L16: SQL fundamentals, injection, indexes, transactions and N+1.

    python3 labs/m2/l16_sql.py

Standard library only (sqlite3). Writes to a temporary file.
"""

from __future__ import annotations

import random
import sqlite3
import tempfile
import time
from pathlib import Path

LINE = "-" * 74
N_CUSTOMERS = 500
N_TICKETS = 20_000
CHANNELS = ["email", "chat", "phone"]
TIERS = ["free", "pro", "enterprise"]


def section(title: str) -> None:
    print()
    print(LINE)
    print(title)
    print(LINE)


SCHEMA = """
CREATE TABLE customers (
    customer_id TEXT PRIMARY KEY,
    name        TEXT NOT NULL,
    tier        TEXT NOT NULL CHECK (tier IN ('free', 'pro', 'enterprise')),
    credit      INTEGER NOT NULL DEFAULT 0
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
"""


def build(path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")      # SQLite does NOT do this by default
    conn.executescript(SCHEMA)

    rng = random.Random(42)
    customers = [
        (f"C-{i:04d}", f"Customer {i}", rng.choice(TIERS), rng.randint(0, 500))
        for i in range(N_CUSTOMERS)
    ]
    conn.executemany("INSERT INTO customers VALUES (?, ?, ?, ?)", customers)

    tickets = []
    for i in range(N_TICKETS):
        resolved = None if rng.random() < 0.3 else f"2026-02-{rng.randint(1, 28):02d}"
        tickets.append((
            f"T-{i:06d}",
            f"C-{rng.randint(0, N_CUSTOMERS - 1):04d}",
            rng.choice(["refund request", "cannot log in", "invoice query",
                        "delivery late", "password reset"]),
            rng.randint(1, 5),
            rng.choice(CHANNELS),
            f"2026-01-{rng.randint(1, 28):02d}",
            resolved,
        ))
    conn.executemany("INSERT INTO tickets VALUES (?, ?, ?, ?, ?, ?, ?)", tickets)
    conn.commit()
    return conn


def basics(conn: sqlite3.Connection) -> None:
    section("1. QUERY BASICS")
    row = conn.execute("SELECT COUNT(*) AS n FROM tickets").fetchone()
    print(f"  total tickets: {row['n']:,}")

    print()
    print("  Tickets per channel (GROUP BY):")
    for r in conn.execute(
        "SELECT channel, COUNT(*) AS n, ROUND(AVG(priority), 2) AS avg_priority "
        "FROM tickets GROUP BY channel ORDER BY n DESC"
    ):
        print(f"    {r['channel']:<8}{r['n']:>7,}  avg priority {r['avg_priority']}")

    print()
    print("  IS NULL vs = NULL:")
    unresolved_correct = conn.execute(
        "SELECT COUNT(*) AS n FROM tickets WHERE resolved_at IS NULL").fetchone()["n"]
    unresolved_wrong = conn.execute(
        "SELECT COUNT(*) AS n FROM tickets WHERE resolved_at = NULL").fetchone()["n"]
    print(f"    WHERE resolved_at IS NULL -> {unresolved_correct:,} rows")
    print(f"    WHERE resolved_at =  NULL -> {unresolved_wrong:,} rows   <-- always zero")
    print("    Comparison with NULL is never true. No error is raised.")

    print()
    print("  A join (enterprise customers, urgent unresolved tickets):")
    for r in conn.execute("""
        SELECT t.ticket_id, t.priority, c.name, c.tier
        FROM tickets t
        JOIN customers c ON c.customer_id = t.customer_id
        WHERE c.tier = 'enterprise' AND t.priority = 1 AND t.resolved_at IS NULL
        ORDER BY t.created_at DESC
        LIMIT 5
    """):
        print(f"    {r['ticket_id']}  p{r['priority']}  {r['name']} ({r['tier']})")


# ---------------------------------------------------------------------------
def vulnerable_search(conn: sqlite3.Connection, channel: str) -> list[sqlite3.Row]:
    """NEVER WRITE THIS. Values interpolated straight into the SQL text."""
    query = f"SELECT ticket_id, channel FROM tickets WHERE channel = '{channel}'"
    return conn.execute(query).fetchall()


def safe_search(conn: sqlite3.Connection, channel: str) -> list[sqlite3.Row]:
    """Parameterised: the value never becomes part of the statement."""
    return conn.execute(
        "SELECT ticket_id, channel FROM tickets WHERE channel = ?", (channel,)
    ).fetchall()


ALLOWED_SORT = {"created_at", "priority", "ticket_id"}


def safe_sorted_search(conn: sqlite3.Connection, channel: str, sort: str) -> list[sqlite3.Row]:
    """Values parameterised; the identifier is ALLOW-LISTED, not escaped."""
    if sort not in ALLOWED_SORT:
        raise ValueError(f"invalid sort column: {sort!r}")
    query = f"""
        SELECT ticket_id, channel, priority FROM tickets
        WHERE channel = ? ORDER BY {sort} DESC LIMIT 3
    """
    return conn.execute(query, (channel,)).fetchall()


def injection_demo(conn: sqlite3.Connection) -> None:
    section("2. SQL INJECTION - a real one, then the fix")
    legitimate = "email"
    attack = "email' OR '1'='1"

    normal = vulnerable_search(conn, legitimate)
    print(f"  vulnerable_search('email')          -> {len(normal):,} rows (correct)")

    exploited = vulnerable_search(conn, attack)
    print(f"  vulnerable_search(\"email' OR '1'='1\") -> {len(exploited):,} rows  <-- EVERY ROW")
    print()
    print("  The query the database actually received:")
    print(f"    SELECT ... WHERE channel = '{attack}'")
    print("    The attacker's quote closed the string and OR '1'='1' made the")
    print("    condition always true. The filter is gone.")
    print()

    safe_normal = safe_search(conn, legitimate)
    safe_attack = safe_search(conn, attack)
    print(f"  safe_search('email')                -> {len(safe_normal):,} rows (correct)")
    print(f"  safe_search(\"email' OR '1'='1\")     -> {len(safe_attack):,} rows  <-- treated "
          f"as a literal channel name")
    print()
    print("  Identifiers cannot be parameterised, so allow-list them:")
    rows = safe_sorted_search(conn, "email", "priority")
    print(f"    sort='priority' -> ok, {len(rows)} rows")
    try:
        safe_sorted_search(conn, "email", "priority; DROP TABLE tickets")
    except ValueError as exc:
        print(f"    sort='priority; DROP TABLE tickets' -> ValueError: {exc}")


def index_demo(conn: sqlite3.Connection) -> None:
    section("3. INDEXES - measured, with the query plan")
    query = "SELECT COUNT(*) FROM tickets WHERE customer_id = ?"
    target = "C-0042"

    def timed(repeats: int = 200) -> float:
        start = time.perf_counter()
        for _ in range(repeats):
            conn.execute(query, (target,)).fetchone()
        return (time.perf_counter() - start) / repeats * 1000

    plan_before = conn.execute("EXPLAIN QUERY PLAN " + query, (target,)).fetchone()["detail"]
    before = timed()

    conn.execute("CREATE INDEX idx_tickets_customer ON tickets(customer_id)")
    conn.commit()

    plan_after = conn.execute("EXPLAIN QUERY PLAN " + query, (target,)).fetchone()["detail"]
    after = timed()

    print(f"  Table has {N_TICKETS:,} rows.")
    print()
    print(f"  {'':<12}{'plan':<52}{'per query'}")
    print(f"  {'no index':<12}{plan_before[:50]:<52}{before:>7.3f} ms")
    print(f"  {'indexed':<12}{plan_after[:50]:<52}{after:>7.3f} ms")
    print(f"  speed-up: {before / after:.0f}x")
    print()
    print("  SCAN means every row was read. SEARCH ... USING INDEX means the")
    print("  database jumped straight to the matching rows.")
    print()
    print("  When an index does NOT help - a function on the column:")
    plan = conn.execute(
        "EXPLAIN QUERY PLAN SELECT * FROM tickets WHERE lower(customer_id) = ?",
        ("c-0042",)).fetchone()["detail"]
    print(f"    WHERE lower(customer_id) = ?  ->  {plan[:60]}")
    print("    The index is on customer_id, not on lower(customer_id).")


def transaction_demo(conn: sqlite3.Connection) -> None:
    section("4. TRANSACTIONS - all or nothing")

    def credit(cid: str) -> int:
        return conn.execute(
            "SELECT credit FROM customers WHERE customer_id = ?", (cid,)
        ).fetchone()["credit"]

    a, b = "C-0001", "C-0002"
    print(f"  before: {a}={credit(a)}  {b}={credit(b)}")

    print()
    print("  A transfer that fails halfway, INSIDE a transaction:")
    try:
        with conn:                     # commits on success, rolls back on exception
            conn.execute("UPDATE customers SET credit = credit - 100 WHERE customer_id = ?", (a,))
            raise RuntimeError("network failure between the two updates")
            conn.execute("UPDATE customers SET credit = credit + 100 WHERE customer_id = ?", (b,))
    except RuntimeError as exc:
        print(f"    caught: {exc}")
    print(f"    after : {a}={credit(a)}  {b}={credit(b)}   <-- UNCHANGED, rolled back")

    print()
    print("  The same failure WITHOUT a transaction:")
    conn.execute("UPDATE customers SET credit = credit - 100 WHERE customer_id = ?", (a,))
    conn.commit()
    print(f"    after : {a}={credit(a)}  {b}={credit(b)}   <-- 100 has VANISHED")
    conn.execute("UPDATE customers SET credit = credit + 100 WHERE customer_id = ?", (a,))
    conn.commit()


def n_plus_one_demo(conn: sqlite3.Connection) -> None:
    section("5. THE N+1 PROBLEM")
    limit = 300

    start = time.perf_counter()
    tickets = conn.execute(
        "SELECT ticket_id, customer_id FROM tickets LIMIT ?", (limit,)).fetchall()
    queries = 1
    names_n1 = []
    for t in tickets:
        row = conn.execute(
            "SELECT name FROM customers WHERE customer_id = ?", (t["customer_id"],)
        ).fetchone()
        queries += 1
        names_n1.append(row["name"])
    n1_ms = (time.perf_counter() - start) * 1000

    start = time.perf_counter()
    joined = conn.execute("""
        SELECT t.ticket_id, c.name
        FROM tickets t JOIN customers c ON c.customer_id = t.customer_id
        LIMIT ?
    """, (limit,)).fetchall()
    join_ms = (time.perf_counter() - start) * 1000

    print(f"  Fetching {limit} tickets with their customer names:")
    print(f"    N+1 version : {queries:>4} queries   {n1_ms:>7.1f} ms")
    print(f"    JOIN version: {1:>4} query     {join_ms:>7.1f} ms")
    print(f"    {n1_ms / join_ms:.0f}x slower, same {len(joined)} rows of data")
    print()
    print("  On 10 rows in development this is invisible. On 10,000 rows in")
    print("  production it is an outage. ORMs make it especially easy to")
    print("  write by accident, because the extra queries are implicit.")


def left_join_demo(conn: sqlite3.Connection) -> None:
    section("6. THE LEFT JOIN + WHERE TRAP")
    conn.execute("INSERT INTO customers VALUES ('C-9999', 'Silent Customer', 'free', 0)")
    conn.commit()

    all_customers = conn.execute("""
        SELECT c.customer_id, COUNT(t.ticket_id) AS n
        FROM customers c LEFT JOIN tickets t ON t.customer_id = c.customer_id
        GROUP BY c.customer_id
    """).fetchall()

    broken = conn.execute("""
        SELECT c.customer_id, COUNT(t.ticket_id) AS n
        FROM customers c LEFT JOIN tickets t ON t.customer_id = c.customer_id
        WHERE t.priority <= 2
        GROUP BY c.customer_id
    """).fetchall()

    fixed = conn.execute("""
        SELECT c.customer_id, COUNT(t.ticket_id) AS n
        FROM customers c LEFT JOIN tickets t
             ON t.customer_id = c.customer_id AND t.priority <= 2
        GROUP BY c.customer_id
    """).fetchall()

    print(f"  LEFT JOIN, no filter                     -> {len(all_customers)} customers")
    print(f"  LEFT JOIN + WHERE t.priority <= 2        -> {len(broken)} customers  <-- lost some")
    print(f"  LEFT JOIN ... ON ... AND t.priority <= 2 -> {len(fixed)} customers  <-- correct")
    print()
    print("  'Silent Customer' has no tickets at all. In the middle query its")
    print("  joined columns are NULL, and NULL <= 2 is not true, so the row is")
    print("  filtered out. The LEFT JOIN silently became an INNER JOIN.")
    print("  Conditions on the right-hand table belong in ON, not WHERE.")


def foreign_key_demo(conn: sqlite3.Connection) -> None:
    section("7. SQLITE FOREIGN KEYS ARE OFF BY DEFAULT")
    bad = ("T-BAD", "C-DOES-NOT-EXIST", "x", 1, "email", "2026-01-01", None)

    conn.execute("PRAGMA foreign_keys = OFF")
    conn.execute("INSERT INTO tickets VALUES (?, ?, ?, ?, ?, ?, ?)", bad)
    conn.commit()
    orphan = conn.execute(
        "SELECT COUNT(*) AS n FROM tickets WHERE customer_id = 'C-DOES-NOT-EXIST'"
    ).fetchone()["n"]
    print(f"  foreign_keys = OFF -> inserted an orphan ticket. Rows: {orphan}")
    conn.execute("DELETE FROM tickets WHERE ticket_id = 'T-BAD'")
    conn.commit()

    conn.execute("PRAGMA foreign_keys = ON")
    try:
        conn.execute("INSERT INTO tickets VALUES (?, ?, ?, ?, ?, ?, ?)", bad)
        conn.commit()
    except sqlite3.IntegrityError as exc:
        print(f"  foreign_keys = ON  -> IntegrityError: {exc}")
    print()
    print("  SQLite defaults foreign_keys to OFF for backwards compatibility.")
    print("  Every connection must enable it explicitly, or your referential")
    print("  integrity is decorative.")


def main() -> None:
    with tempfile.TemporaryDirectory() as raw:
        path = Path(raw) / "course.db"
        print("=" * 74)
        print("SQL FUNDAMENTALS")
        print("=" * 74)
        print(f"Building a database with {N_CUSTOMERS} customers and "
              f"{N_TICKETS:,} tickets...")
        conn = build(path)
        try:
            basics(conn)
            injection_demo(conn)
            index_demo(conn)
            transaction_demo(conn)
            n_plus_one_demo(conn)
            left_join_demo(conn)
            foreign_key_demo(conn)
        finally:
            conn.close()
    print()
    print("=" * 74)


if __name__ == "__main__":
    main()
