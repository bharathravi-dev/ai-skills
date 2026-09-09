"""M2-L06 demo runner. Shows how imports resolve.

    cd labs/m2/l06_demo && python3 run_demo.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import ticketkit
from ticketkit import Ticket, classify_ticket


def main() -> None:
    print("=" * 70)
    print("PACKAGE IMPORTS")
    print("=" * 70)
    print()
    print(f"  ticketkit.__version__ : {ticketkit.__version__}")
    print(f"  ticketkit.__all__     : {ticketkit.__all__}")
    print(f"  ticketkit.__file__    : .../{Path(ticketkit.__file__).parent.name}/__init__.py")
    print()
    print("  sys.path[0] (where Python looks first):")
    print(f"    {sys.path[0] or '(current directory)'}")
    print()

    tickets = [
        Ticket("T-1", "Our checkout is down, this is urgent"),
        Ticket("T-2", "Question about the invoice from March", channel="chat"),
        Ticket("T-3", "How do I change my avatar?"),
    ]

    print(f"  {'id':<6}{'urgent':<9}{'billing':<10}{'words':<7}text")
    print("  " + "-" * 64)
    for ticket in tickets:
        result = classify_ticket(ticket)
        print(f"  {result['ticket_id']:<6}{str(result['urgent']):<9}"
              f"{str(result['billing']):<10}{result['words']:<7}{ticket.text[:30]}")

    print()
    print("  Note what the caller did NOT have to know:")
    print("    - that classify_ticket lives in ticketkit/classify.py")
    print("    - that the word lists live in ticketkit/_rules.py")
    print("  __init__.py re-exported them, so the internal layout can change")
    print("  without breaking any caller.")
    print()
    print("  The dataclass default_factory in action (M2-L05's bug, avoided):")
    a, b = Ticket("T-9", "one"), Ticket("T-10", "two")
    a.tags.append("escalated")
    print(f"    a.tags = {a.tags}")
    print(f"    b.tags = {b.tags}   <-- separate lists, thanks to default_factory")
    print("=" * 70)


if __name__ == "__main__":
    main()
