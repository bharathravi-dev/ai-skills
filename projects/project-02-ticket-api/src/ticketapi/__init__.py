"""ticketapi - Project 2 of the AI Engineering course.

Public surface only; internal layout can change without breaking callers
(M2-L06).
"""

from ticketapi.models import Ticket, TicketCreate, TicketOut, TicketUpdate

__all__ = ["Ticket", "TicketCreate", "TicketOut", "TicketUpdate"]
__version__ = "0.1.0"
