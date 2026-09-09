"""Ticket classification. Public API of the package."""

from __future__ import annotations

# Absolute import from within the same package. Explicit and unambiguous.
from ticketkit._rules import BILLING_WORDS, URGENT_WORDS, contains_any
from ticketkit.models import Ticket


def classify_ticket(ticket: Ticket) -> dict[str, object]:
    """Return a small classification record for a ticket."""
    return {
        "ticket_id": ticket.ticket_id,
        "urgent": contains_any(ticket.text, URGENT_WORDS),
        "billing": contains_any(ticket.text, BILLING_WORDS),
        "words": ticket.word_count(),
    }
