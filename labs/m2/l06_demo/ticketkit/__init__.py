"""ticketkit - a tiny package used by M2-L06 to demonstrate imports.

The presence of this file makes `ticketkit` a package. It is also the place
to define the package's PUBLIC surface, so callers can write

    from ticketkit import classify

instead of reaching into internal module paths.
"""

from ticketkit.classify import classify_ticket
from ticketkit.models import Ticket

# __all__ declares what `from ticketkit import *` exports, and documents
# intent to readers and linters.
__all__ = ["Ticket", "classify_ticket"]

__version__ = "0.1.0"
