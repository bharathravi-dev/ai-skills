"""Internal rules. The leading underscore signals 'not part of the API'.

Nothing enforces this. It is a convention, and Python relies on conventions
far more than on access modifiers.
"""

from __future__ import annotations

URGENT_WORDS = frozenset({"urgent", "asap", "immediately", "outage", "down"})
BILLING_WORDS = frozenset({"invoice", "refund", "charge", "payment", "billing"})


def contains_any(text: str, words: frozenset[str]) -> bool:
    return any(word in text.lower().split() for word in words)
