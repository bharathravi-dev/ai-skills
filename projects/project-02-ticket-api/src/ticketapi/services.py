"""Business logic. Raises domain errors, never HTTPException (M2-L15)."""

from __future__ import annotations

import logging
import sqlite3
import uuid
from datetime import datetime, timezone

from ticketapi import db
from ticketapi.config import Principal
from ticketapi.errors import NoChangesRequested, NotAuthorized, TicketNotFound
from ticketapi.models import Ticket, TicketCreate, TicketUpdate

logger = logging.getLogger(__name__)


def _new_ticket_id() -> str:
    return f"T-{uuid.uuid4().hex[:10]}"


def create_ticket(
    conn: sqlite3.Connection,
    payload: TicketCreate,
    principal: Principal,
    *,
    request_id: str,
) -> Ticket:
    ticket = Ticket.new(_new_ticket_id(), payload, owner_id=principal.user_id)
    db.insert(conn, ticket)
    # Log identifiers and metrics, never the ticket body (M2-L18).
    logger.info(
        "ticket_created",
        extra={"request_id": request_id, "ticket_id": ticket.ticket_id,
               "owner_id": principal.user_id, "priority": ticket.priority,
               "channel": ticket.channel, "chars": len(ticket.text)},
    )
    return ticket


def get_ticket(
    conn: sqlite3.Connection,
    ticket_id: str,
    principal: Principal,
    *,
    request_id: str,
) -> Ticket:
    ticket = db.get(conn, ticket_id)
    if ticket is None:
        raise TicketNotFound(ticket_id)
    if ticket.owner_id != principal.user_id and not principal.is_admin:
        # The web layer converts this to 404, not 403, so the response does
        # not confirm the ticket exists. The real reason is logged here.
        logger.warning(
            "ticket_access_denied",
            extra={"request_id": request_id, "ticket_id": ticket_id,
                   "actor": principal.user_id, "owner": ticket.owner_id},
        )
        raise NotAuthorized("read this ticket")
    return ticket


def list_tickets(
    conn: sqlite3.Connection,
    principal: Principal,
    *,
    status: str | None = None,
    sort: str = "created_at",
    limit: int = 20,
    offset: int = 0,
) -> list[Ticket]:
    # Admins see everything; everyone else sees only their own. This is
    # enforced HERE, not by a query parameter the client controls.
    owner_id = None if principal.is_admin else principal.user_id
    return db.list_for(conn, owner_id=owner_id, status=status,
                       sort=sort, limit=limit, offset=offset)


def update_ticket(
    conn: sqlite3.Connection,
    ticket_id: str,
    payload: TicketUpdate,
    principal: Principal,
    *,
    request_id: str,
) -> Ticket:
    if not payload.has_changes():
        raise NoChangesRequested()

    ticket = get_ticket(conn, ticket_id, principal, request_id=request_id)

    if payload.internal_notes is not None and not principal.is_admin:
        raise NotAuthorized("set internal notes")

    updated = ticket.model_copy(update={
        "priority": payload.priority if payload.priority is not None else ticket.priority,
        "status": payload.status if payload.status is not None else ticket.status,
        "internal_notes": (payload.internal_notes
                           if payload.internal_notes is not None
                           else ticket.internal_notes),
        "updated_at": datetime.now(timezone.utc),
    })
    db.update(conn, updated)
    logger.info(
        "ticket_updated",
        extra={"request_id": request_id, "ticket_id": ticket_id,
               "actor": principal.user_id, "status": updated.status,
               "priority": updated.priority},
    )
    return updated
