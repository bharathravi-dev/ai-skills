"""M2-L15: a hardened FastAPI app, exercised entirely through TestClient.

Requires fastapi:
    source .venv/bin/activate
    python labs/m2/l15_fastapi.py

No server is started and no port is opened.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Literal

from fastapi import Depends, FastAPI, Header, HTTPException, Query
from fastapi.testclient import TestClient
from pydantic import BaseModel, ConfigDict, Field

LINE = "-" * 74


def section(title: str) -> None:
    print()
    print(LINE)
    print(title)
    print(LINE)


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------
class TicketIn(BaseModel):
    # Blocks mass assignment: a client cannot smuggle in owner_id or is_admin.
    model_config = ConfigDict(extra="forbid")

    text: str = Field(min_length=1, max_length=5000)
    priority: int = Field(default=3, ge=1, le=5)
    channel: Literal["email", "chat", "phone"] = "email"


class TicketOut(BaseModel):
    """The PUBLIC shape. Fields absent here are stripped from responses."""

    ticket_id: str
    text: str
    priority: int
    channel: str
    created_at: datetime
    # deliberately absent: owner_id, internal_notes, handling_cost


class User(BaseModel):
    id: str
    is_admin: bool = False


# ---------------------------------------------------------------------------
# A fake store. Rows carry MORE fields than TicketOut exposes.
# ---------------------------------------------------------------------------
TICKETS: dict[str, dict] = {
    "T-001": {
        "ticket_id": "T-001", "text": "Refund not received", "priority": 2,
        "channel": "email", "created_at": datetime(2026, 1, 5, tzinfo=timezone.utc),
        "owner_id": "u-alice", "internal_notes": "VIP customer, escalate fast",
        "handling_cost": 12.50,
    },
    "T-002": {
        "ticket_id": "T-002", "text": "Cannot log in", "priority": 1,
        "channel": "chat", "created_at": datetime(2026, 1, 6, tzinfo=timezone.utc),
        "owner_id": "u-bob", "internal_notes": "third report this week",
        "handling_cost": 3.00,
    },
}

TOKENS = {"tok-alice": User(id="u-alice"), "tok-bob": User(id="u-bob"),
          "tok-admin": User(id="u-admin", is_admin=True)}


# ---------------------------------------------------------------------------
# Dependencies: authentication and authorization, in deterministic code.
# ---------------------------------------------------------------------------
def current_user(authorization: str = Header(default="")) -> User:
    if not authorization.startswith("Bearer "):
        raise HTTPException(401, "missing bearer token")
    user = TOKENS.get(authorization[7:])
    if user is None:
        raise HTTPException(401, "invalid token")
    return user


def require_admin(user: User = Depends(current_user)) -> User:
    if not user.is_admin:
        raise HTTPException(403, "admin required")      # 403: known, not permitted
    return user


app = FastAPI(title="Ticket API")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/tickets", response_model=TicketOut, status_code=201)
def create_ticket(payload: TicketIn, user: User = Depends(current_user)) -> dict:
    ticket_id = f"T-{len(TICKETS) + 1:03d}"
    row = {
        "ticket_id": ticket_id,
        "text": payload.text,
        "priority": payload.priority,
        "channel": payload.channel,
        "created_at": datetime.now(timezone.utc),
        # owner_id comes from the VERIFIED TOKEN, never from the request body.
        "owner_id": user.id,
        "internal_notes": "",
        "handling_cost": 0.0,
    }
    TICKETS[ticket_id] = row
    return row


@app.get("/tickets/{ticket_id}", response_model=TicketOut)
def get_ticket(ticket_id: str, user: User = Depends(current_user)) -> dict:
    row = TICKETS.get(ticket_id)
    # 404 for BOTH "absent" and "not yours": a 403 would confirm it exists.
    if row is None or (row["owner_id"] != user.id and not user.is_admin):
        raise HTTPException(404, "ticket not found")
    return row


@app.get("/tickets", response_model=list[TicketOut])
def list_tickets(
    user: User = Depends(current_user),
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> list[dict]:
    owned = [r for r in TICKETS.values()
             if user.is_admin or r["owner_id"] == user.id]
    return owned[offset:offset + limit]


@app.delete("/tickets/{ticket_id}", status_code=204)
def delete_ticket(ticket_id: str, user: User = Depends(require_admin)) -> None:
    TICKETS.pop(ticket_id, None)


# ---------------------------------------------------------------------------
client = TestClient(app)


def show(label: str, response, *, body: bool = True) -> None:
    print(f"  {label}")
    print(f"    -> {response.status_code}", end="")
    if body and response.content:
        payload = response.json()
        text = json.dumps(payload)
        print(f"  {text[:110]}{'...' if len(text) > 110 else ''}")
    else:
        print()


def validation_demo() -> None:
    section("1. VALIDATION - what the framework rejects for you")
    auth = {"Authorization": "Bearer tok-alice"}

    show("valid ticket", client.post("/tickets", headers=auth,
         json={"text": "Printer on fire", "priority": 1}))

    show("priority out of range (99)", client.post("/tickets", headers=auth,
         json={"text": "x", "priority": 99}))

    show("empty text", client.post("/tickets", headers=auth,
         json={"text": "", "priority": 2}))

    show("invalid channel", client.post("/tickets", headers=auth,
         json={"text": "x", "channel": "carrier-pigeon"}))

    print()
    print("  MASS ASSIGNMENT ATTEMPT - client tries to own someone else's data:")
    response = client.post("/tickets", headers=auth,
                           json={"text": "x", "owner_id": "u-bob", "is_admin": True})
    show("  posts owner_id and is_admin", response)
    print("    extra='forbid' rejected both fields by name. Without it they")
    print("    would have been silently ignored - or worse, honoured.")

    print()
    print("  The 422 body is structured, not prose:")
    detail = client.post("/tickets", headers=auth,
                         json={"text": "", "priority": 99}).json()["detail"]
    for error in detail:
        print(f"    loc={error['loc']}  msg={error['msg']}")


def auth_demo() -> None:
    section("2. AUTHORIZATION - enforced before any handler logic runs")
    print(f"  {'request':<46}{'status':>8}")
    cases = [
        ("no Authorization header", {}, "/tickets/T-001"),
        ("invalid token", {"Authorization": "Bearer nope"}, "/tickets/T-001"),
        ("alice reads her own ticket", {"Authorization": "Bearer tok-alice"}, "/tickets/T-001"),
        ("alice reads BOB's ticket", {"Authorization": "Bearer tok-alice"}, "/tickets/T-002"),
        ("alice reads a ticket that does not exist", {"Authorization": "Bearer tok-alice"}, "/tickets/T-999"),
        ("admin reads bob's ticket", {"Authorization": "Bearer tok-admin"}, "/tickets/T-002"),
    ]
    for label, headers, path in cases:
        response = client.get(path, headers=headers)
        print(f"  {label:<46}{response.status_code:>8}")

    print()
    print("  Note rows 4 and 5 BOTH return 404.")
    print("  Bob's ticket exists; the non-existent one does not. Returning 403")
    print("  for the first would confirm its existence, letting an attacker")
    print("  enumerate valid ticket IDs. Identical responses reveal nothing.")

    print()
    print(f"  {'admin-only delete':<46}{'status':>8}")
    saved = dict(TICKETS["T-002"])
    for label, token in (("alice tries to delete", "tok-alice"),
                         ("admin deletes", "tok-admin")):
        response = client.delete("/tickets/T-002",
                                 headers={"Authorization": f"Bearer {token}"})
        print(f"  {label:<46}{response.status_code:>8}")
    print("    403 for alice: authenticated, but not permitted (M2-L11).")
    TICKETS["T-002"] = saved       # restore, so later demos are independent


def response_model_demo() -> None:
    section("3. response_model - a real data-leak control")
    stored = TICKETS["T-001"]
    print(f"  Fields stored in the row  : {sorted(stored.keys())}")
    response = client.get("/tickets/T-001",
                          headers={"Authorization": "Bearer tok-alice"})
    returned = response.json()
    print(f"  Fields returned to client : {sorted(returned.keys())}")
    print()
    hidden = sorted(set(stored) - set(returned))
    print(f"  STRIPPED by response_model: {hidden}")
    print()
    print("  The handler returned the whole row. FastAPI filtered it down to")
    print("  TicketOut. 'internal_notes' contained 'VIP customer, escalate")
    print("  fast' and 'handling_cost' was 12.5 - neither reached the client.")
    print()
    print("  Add a column to the table tomorrow and it is NOT exposed unless")
    print("  someone deliberately adds it to TicketOut. That default is the")
    print("  security property.")


def override_demo() -> None:
    section("4. DEPENDENCY OVERRIDES - testing auth with no real tokens")
    print("  Run the SAME endpoint as three different users, no tokens needed:")

    for user in (User(id="u-alice"), User(id="u-bob"), User(id="u-admin", is_admin=True)):
        app.dependency_overrides[current_user] = lambda u=user: u
        response = client.get("/tickets")
        ids = [t["ticket_id"] for t in response.json()]
        print(f"    as {user.id:<10} (admin={str(user.is_admin):<5}) -> sees {ids}")

    app.dependency_overrides.clear()
    print()
    print("  No patching, no mocking library, no fake HTTP server. The real")
    print("  route code ran - real validation, real response_model filtering -")
    print("  with one dependency swapped. This is M2-L07 composition, applied")
    print("  by the framework.")


def openapi_demo() -> None:
    section("5. THE GENERATED SCHEMA")
    schema = app.openapi()
    ticket_in = schema["components"]["schemas"]["TicketIn"]["properties"]
    print("  Your Field() constraints appear in the OpenAPI document:")
    for name, spec in ticket_in.items():
        limits = {k: v for k, v in spec.items()
                  if k in ("minimum", "maximum", "minLength", "maxLength", "enum", "default")}
        print(f"    {name:<12}{limits}")
    print()
    print(f"  Paths documented: {sorted(schema['paths'].keys())}")
    print("  This is generated from the code, so it cannot drift from it.")


def main() -> None:
    print("=" * 74)
    print("FASTAPI: VALIDATION, AUTHORIZATION AND TESTING")
    print("=" * 74)
    validation_demo()
    auth_demo()
    response_model_demo()
    override_demo()
    openapi_demo()
    print()
    print("=" * 74)


if __name__ == "__main__":
    main()
