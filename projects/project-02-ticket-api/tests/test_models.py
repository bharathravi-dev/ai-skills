"""Validation rules at the boundary (M2-L08)."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from ticketapi.models import TicketCreate, TicketUpdate


def test_minimal_valid_ticket():
    ticket = TicketCreate(subject="Refund", text="Please refund my order")
    assert ticket.priority == 3          # default
    assert ticket.channel == "email"     # default


@pytest.mark.parametrize("priority", [0, 6, -1, 99])
def test_priority_out_of_range_rejected(priority):
    with pytest.raises(ValidationError) as exc:
        TicketCreate(subject="s", text="t", priority=priority)
    assert exc.value.errors()[0]["loc"] == ("priority",)


def test_whitespace_only_text_rejected():
    """strip_whitespace runs BEFORE the length check, so '   ' is empty."""
    with pytest.raises(ValidationError) as exc:
        TicketCreate(subject="s", text="   ")
    assert "at least 1 character" in exc.value.errors()[0]["msg"]


def test_text_is_stripped():
    ticket = TicketCreate(subject="  Refund  ", text="  hello  ")
    assert ticket.subject == "Refund"
    assert ticket.text == "hello"


def test_invalid_channel_rejected():
    with pytest.raises(ValidationError):
        TicketCreate(subject="s", text="t", channel="carrier-pigeon")


def test_mass_assignment_blocked():
    """A client must not be able to set owner_id or status."""
    with pytest.raises(ValidationError) as exc:
        TicketCreate(subject="s", text="t", owner_id="u-bob", status="resolved")
    fields = {e["loc"][0] for e in exc.value.errors()}
    assert fields == {"owner_id", "status"}
    assert all(e["type"] == "extra_forbidden" for e in exc.value.errors())


def test_update_requires_at_least_one_field():
    assert TicketUpdate().has_changes() is False
    assert TicketUpdate(priority=2).has_changes() is True
