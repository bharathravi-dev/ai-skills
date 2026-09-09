"""Business logic and authorization, tested without HTTP."""

from __future__ import annotations

import pytest

from ticketapi import services
from ticketapi.config import Principal
from ticketapi.errors import NoChangesRequested, NotAuthorized, TicketNotFound
from ticketapi.models import TicketCreate, TicketUpdate

ALICE = Principal(user_id="u-alice", role="agent")
BOB = Principal(user_id="u-bob", role="agent")
ADMIN = Principal(user_id="u-admin", role="admin")

PAYLOAD = TicketCreate(subject="Refund", text="Please refund my order")


def test_owner_comes_from_principal_not_payload(conn):
    ticket = services.create_ticket(conn, PAYLOAD, ALICE, request_id="r1")
    assert ticket.owner_id == "u-alice"
    assert ticket.status == "open"


def test_owner_can_read_own_ticket(conn):
    created = services.create_ticket(conn, PAYLOAD, ALICE, request_id="r1")
    fetched = services.get_ticket(conn, created.ticket_id, ALICE, request_id="r2")
    assert fetched.ticket_id == created.ticket_id


def test_other_user_cannot_read(conn):
    created = services.create_ticket(conn, PAYLOAD, ALICE, request_id="r1")
    with pytest.raises(NotAuthorized):
        services.get_ticket(conn, created.ticket_id, BOB, request_id="r2")


def test_admin_can_read_any_ticket(conn):
    created = services.create_ticket(conn, PAYLOAD, ALICE, request_id="r1")
    fetched = services.get_ticket(conn, created.ticket_id, ADMIN, request_id="r2")
    assert fetched.owner_id == "u-alice"


def test_missing_ticket_raises(conn):
    with pytest.raises(TicketNotFound):
        services.get_ticket(conn, "T-nope", ALICE, request_id="r1")


def test_list_is_scoped_to_owner(conn):
    services.create_ticket(conn, PAYLOAD, ALICE, request_id="r1")
    services.create_ticket(conn, PAYLOAD, BOB, request_id="r2")

    assert len(services.list_tickets(conn, ALICE)) == 1
    assert len(services.list_tickets(conn, BOB)) == 1
    assert len(services.list_tickets(conn, ADMIN)) == 2


def test_update_changes_status(conn):
    created = services.create_ticket(conn, PAYLOAD, ALICE, request_id="r1")
    updated = services.update_ticket(
        conn, created.ticket_id, TicketUpdate(status="resolved"), ALICE,
        request_id="r2",
    )
    assert updated.status == "resolved"
    assert updated.updated_at >= created.updated_at


def test_empty_update_rejected(conn):
    created = services.create_ticket(conn, PAYLOAD, ALICE, request_id="r1")
    with pytest.raises(NoChangesRequested):
        services.update_ticket(conn, created.ticket_id, TicketUpdate(), ALICE,
                               request_id="r2")


def test_only_admin_may_set_internal_notes(conn):
    created = services.create_ticket(conn, PAYLOAD, ALICE, request_id="r1")
    with pytest.raises(NotAuthorized):
        services.update_ticket(
            conn, created.ticket_id, TicketUpdate(internal_notes="VIP"), ALICE,
            request_id="r2",
        )
    updated = services.update_ticket(
        conn, created.ticket_id, TicketUpdate(internal_notes="VIP"), ADMIN,
        request_id="r3",
    )
    assert updated.internal_notes == "VIP"


def test_invalid_sort_column_rejected(conn):
    with pytest.raises(ValueError, match="invalid sort column"):
        services.list_tickets(conn, ALICE, sort="priority; DROP TABLE tickets")
