"""Pydantic schemas: the contract at the API boundary (M2-L08).

Three distinct models on purpose:
  TicketCreate - what a client may SEND (extra="forbid" blocks mass assignment)
  Ticket       - the full internal row, including fields clients never see
  TicketOut    - what a client RECEIVES (response_model filters to this)
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

Channel = Literal["email", "chat", "phone"]
Status = Literal["open", "pending", "resolved"]


class TicketCreate(BaseModel):
    """Client-supplied fields only.

    Note what is ABSENT: owner_id, status, internal_notes. A client cannot
    set them, because extra="forbid" rejects unknown fields outright.
    """

    model_config = ConfigDict(extra="forbid")

    subject: str = Field(min_length=1, max_length=200)
    text: str = Field(min_length=1, max_length=5000)
    priority: int = Field(default=3, ge=1, le=5)
    channel: Channel = "email"

    @field_validator("subject", "text", mode="before")
    @classmethod
    def strip_whitespace(cls, value: object) -> object:
        """Normalise before length checks, so "   " is rejected as empty."""
        return value.strip() if isinstance(value, str) else value


class TicketUpdate(BaseModel):
    """Partial update. Every field optional; at least one required."""

    model_config = ConfigDict(extra="forbid")

    priority: int | None = Field(default=None, ge=1, le=5)
    status: Status | None = None
    internal_notes: str | None = Field(default=None, max_length=2000)

    def has_changes(self) -> bool:
        return any(v is not None for v in self.model_dump().values())


class Ticket(BaseModel):
    """The full internal record."""

    ticket_id: str
    subject: str
    text: str
    priority: int
    channel: Channel
    status: Status
    owner_id: str
    internal_notes: str = ""
    created_at: datetime
    updated_at: datetime

    @classmethod
    def new(cls, ticket_id: str, payload: TicketCreate, owner_id: str) -> Ticket:
        now = datetime.now(timezone.utc)
        return cls(
            ticket_id=ticket_id,
            subject=payload.subject,
            text=payload.text,
            priority=payload.priority,
            channel=payload.channel,
            status="open",
            owner_id=owner_id,          # from the token, never the request body
            internal_notes="",
            created_at=now,
            updated_at=now,
        )


class TicketOut(BaseModel):
    """The public shape.

    owner_id and internal_notes are deliberately absent, so response_model
    strips them even though the handler returns a full Ticket (M2-L15).
    """

    ticket_id: str
    subject: str
    text: str
    priority: int
    channel: Channel
    status: Status
    created_at: datetime
    updated_at: datetime


class ErrorResponse(BaseModel):
    detail: str
    request_id: str
