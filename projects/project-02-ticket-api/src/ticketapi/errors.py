"""Domain exceptions.

The service layer raises these; the web layer translates them into HTTP
responses (M2-L10, M2-L15). Keeping HTTPException out of services means the
same code can be used from a CLI or a worker.
"""

from __future__ import annotations


class TicketError(Exception):
    """Base for every error this application raises deliberately."""


class TicketNotFound(TicketError):
    def __init__(self, ticket_id: str) -> None:
        super().__init__(f"ticket {ticket_id} not found")
        self.ticket_id = ticket_id


class NotAuthorized(TicketError):
    """Raised when a principal may not perform an action.

    NOTE: the API deliberately reports this as 404 for read/modify of another
    user's ticket, so the response does not confirm the ticket exists
    (M2-L15 section 6).
    """

    def __init__(self, action: str) -> None:
        super().__init__(f"not authorized to {action}")
        self.action = action


class NoChangesRequested(TicketError):
    def __init__(self) -> None:
        super().__init__("update must contain at least one field")
