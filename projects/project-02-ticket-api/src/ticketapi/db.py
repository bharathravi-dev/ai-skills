"""SQLite persistence with parameterised queries only (M2-L16)."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from ticketapi.models import Ticket

SCHEMA = """
CREATE TABLE IF NOT EXISTS tickets (
    ticket_id      TEXT PRIMARY KEY,
    subject        TEXT NOT NULL,
    text           TEXT NOT NULL,
    priority       INTEGER NOT NULL CHECK (priority BETWEEN 1 AND 5),
    channel        TEXT NOT NULL CHECK (channel IN ('email','chat','phone')),
    status         TEXT NOT NULL CHECK (status IN ('open','pending','resolved')),
    owner_id       TEXT NOT NULL,
    internal_notes TEXT NOT NULL DEFAULT '',
    created_at     TEXT NOT NULL,
    updated_at     TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_tickets_owner ON tickets(owner_id);
CREATE INDEX IF NOT EXISTS idx_tickets_status ON tickets(status);
"""

# Identifiers cannot be parameterised, so they are allow-listed (M2-L16).
SORTABLE = {"created_at", "updated_at", "priority", "ticket_id"}


def connect(database_path: str) -> sqlite3.Connection:
    if database_path != ":memory:":
        Path(database_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(database_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")     # off by default in SQLite
    conn.executescript(SCHEMA)
    return conn


@contextmanager
def transaction(conn: sqlite3.Connection) -> Iterator[sqlite3.Connection]:
    """Commit on success, roll back on any exception (M2-L16)."""
    try:
        with conn:
            yield conn
    finally:
        pass


def _to_ticket(row: sqlite3.Row) -> Ticket:
    return Ticket.model_validate(dict(row))


def insert(conn: sqlite3.Connection, ticket: Ticket) -> Ticket:
    with transaction(conn):
        conn.execute(
            """INSERT INTO tickets (ticket_id, subject, text, priority, channel,
                                    status, owner_id, internal_notes,
                                    created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (ticket.ticket_id, ticket.subject, ticket.text, ticket.priority,
             ticket.channel, ticket.status, ticket.owner_id,
             ticket.internal_notes, ticket.created_at.isoformat(),
             ticket.updated_at.isoformat()),
        )
    return ticket


def get(conn: sqlite3.Connection, ticket_id: str) -> Ticket | None:
    row = conn.execute(
        "SELECT * FROM tickets WHERE ticket_id = ?", (ticket_id,)
    ).fetchone()
    return _to_ticket(row) if row else None


def update(conn: sqlite3.Connection, ticket: Ticket) -> Ticket:
    with transaction(conn):
        conn.execute(
            """UPDATE tickets
               SET priority = ?, status = ?, internal_notes = ?, updated_at = ?
               WHERE ticket_id = ?""",
            (ticket.priority, ticket.status, ticket.internal_notes,
             ticket.updated_at.isoformat(), ticket.ticket_id),
        )
    return ticket


def list_for(
    conn: sqlite3.Connection,
    *,
    owner_id: str | None,
    status: str | None = None,
    sort: str = "created_at",
    limit: int = 20,
    offset: int = 0,
) -> list[Ticket]:
    """owner_id=None means 'all tickets' and is only ever passed for admins."""
    if sort not in SORTABLE:
        raise ValueError(f"invalid sort column: {sort!r}")

    clauses: list[str] = []
    params: list[object] = []
    if owner_id is not None:
        clauses.append("owner_id = ?")
        params.append(owner_id)
    if status is not None:
        clauses.append("status = ?")
        params.append(status)

    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    # `sort` is interpolated only because it was allow-listed above.
    query = (f"SELECT * FROM tickets {where} "
             f"ORDER BY {sort} DESC LIMIT ? OFFSET ?")
    params.extend([limit, offset])
    return [_to_ticket(r) for r in conn.execute(query, params)]


def count_for(conn: sqlite3.Connection, *, owner_id: str | None) -> int:
    if owner_id is None:
        return conn.execute("SELECT COUNT(*) AS n FROM tickets").fetchone()["n"]
    return conn.execute(
        "SELECT COUNT(*) AS n FROM tickets WHERE owner_id = ?", (owner_id,)
    ).fetchone()["n"]
