"""Data shapes for the ticket toolkit."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Ticket:
    """One support ticket."""

    ticket_id: str
    text: str
    channel: str = "email"
    # A mutable default on a dataclass MUST use default_factory, for exactly
    # the reason M2-L05 gave: a bare [] would be shared by every instance.
    tags: list[str] = field(default_factory=list)

    def word_count(self) -> int:
        return len(self.text.split())
