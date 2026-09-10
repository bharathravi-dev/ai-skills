"""M8-L12 lab -- M8-L11 showed that some state-changing actions happen to
tolerate a repeat by luck (SET semantics) and others never do (APPEND
semantics), leaving safety to chance. This lesson builds the actual
mechanism that makes a retry safe DELIBERATELY: an idempotency key,
generated once per logical attempt and reused across retries of that same
attempt, so a repeated call with the same key returns the cached result
instead of executing again. A genuinely new request gets a genuinely new
key and still executes for real -- and a specific, real pitfall is
demonstrated: generating a fresh key on every retry defeats the whole
mechanism.

Deterministic. No API key, no network, no third-party dependencies.
Run:  python labs/m8/l12_idempotency_duplicate_prevention.py
"""

from __future__ import annotations

import sys
import uuid

sys.stdout.reconfigure(encoding="utf-8")


def rule(title: str) -> None:
    print(f"\n{'=' * 76}\n{title}\n{'=' * 76}")


REFUND_LOG: list[tuple[str, float]] = []
IDEMPOTENCY_STORE: dict[str, str] = {}


def issue_refund(order_id: str, amount: float) -> str:
    """[REAL] The underlying action -- unchanged from M8-L11, still an
    APPEND-style action that adds a new entry every time it actually runs."""
    REFUND_LOG.append((order_id, amount))
    return f"refund of ${amount:.2f} issued for {order_id}"


def issue_refund_idempotent(idempotency_key: str, order_id: str, amount: float) -> str:
    """[REAL] The deliberate mechanism M8-L11 foreshadowed: a repeated call
    with a key already seen returns the CACHED result without touching
    issue_refund() again at all -- the underlying action's own repeat
    behavior (safe or not) no longer matters, because it is never invoked
    a second time for the same key."""
    if idempotency_key in IDEMPOTENCY_STORE:
        cached = IDEMPOTENCY_STORE[idempotency_key]
        return f"{cached} [returned from cache -- issue_refund() was NOT called again]"
    result = issue_refund(order_id, amount)
    IDEMPOTENCY_STORE[idempotency_key] = result
    return result


# ============================================================ 1
rule("1. THE SAME KEY, RETRIED THREE TIMES: EXACTLY ONE REAL REFUND")

RETRY_KEY = "req-a1b2c3"   # generated ONCE, by the caller, before its first attempt

print(f"  A caller generates one idempotency key ({RETRY_KEY!r}) before its")
print("  first attempt, and reuses the SAME key across all retries of that")
print("  SAME logical attempt -- exactly as a real client library would:\n")
for attempt in range(1, 4):
    result = issue_refund_idempotent(RETRY_KEY, "O-4001", 30.0)
    print(f"    attempt {attempt}: issue_refund_idempotent({RETRY_KEY!r}, 'O-4001', 30.0) -> {result!r}")

print(f"\n  REFUND_LOG after 3 retries with the SAME key: {REFUND_LOG}")
print(f"  Total refunded: ${sum(a for _, a in REFUND_LOG):.2f} -- exactly one $30.00 refund,")
print("  not three, despite three separate calls. Contrast this directly")
print("  with M8-L11's own retry demonstration, which produced $75.00 for a")
print("  single intended $25.00 refund using the SAME underlying action with")
print("  no idempotency key at all.")


# ============================================================ 2
rule("2. A GENUINELY NEW REQUEST STILL EXECUTES FOR REAL")

NEW_KEY = "req-d4e5f6"   # a DIFFERENT logical request, its own fresh key

result = issue_refund_idempotent(NEW_KEY, "O-4002", 55.0)
print(f"  A genuinely different request, its own key ({NEW_KEY!r}):")
print(f"    issue_refund_idempotent({NEW_KEY!r}, 'O-4002', 55.0) -> {result!r}")
print(f"\n  REFUND_LOG now: {REFUND_LOG}")
print("\n  The mechanism did not block this refund -- it only recognized and")
print("  short-circuited RETRIES of a request it had already seen under the")
print("  SAME key. A new key for a new request executes normally, exactly as")
print("  it should.")


# ============================================================ 3
rule("3. THE PITFALL: A FRESH KEY EVERY RETRY DEFEATS THE MECHANISM ENTIRELY")

REFUND_LOG.clear()
IDEMPOTENCY_STORE.clear()


def buggy_retry_with_fresh_key(order_id: str, amount: float, retries: int) -> None:
    """[REAL, deliberately wrong] Generates a NEW idempotency key on every
    attempt instead of reusing one key across all retries of the SAME
    logical request -- a real, easy-to-make mistake, not a contrived one."""
    for _ in range(retries):
        key = str(uuid.uuid4())
        issue_refund_idempotent(key, order_id, amount)


print("  The SAME retry scenario as section 1, but generating a brand-new")
print("  key on every attempt instead of reusing one:\n")
buggy_retry_with_fresh_key("O-4003", 20.0, retries=3)
print(f"  REFUND_LOG: {REFUND_LOG}")
print(f"  IDEMPOTENCY_STORE now has {len(IDEMPOTENCY_STORE)} distinct keys.")
print(f"  Total refunded: ${sum(a for _, a in REFUND_LOG):.2f} -- three $20.00 refunds, $60.00 total,")
print("  for what was meant to be a single $20.00 refund.")

print("\n  The idempotency mechanism itself is not broken -- it correctly")
print("  never saw the same key twice, because there NEVER WAS a repeated")
print("  key to recognize. Idempotency protection depends entirely on the")
print("  CALLER generating one key per logical attempt and reusing it across")
print("  retries -- a fresh key per call is indistinguishable, from the")
print("  mechanism's point of view, from three genuinely different requests.")


# ============================================================ 4
rule("4. IDEMPOTENCY KEYS VS. M8-L06'S BUSINESS-LEVEL SCOPING: DIFFERENT QUESTIONS")

print("  M8-L06's check_already_refunded(customer, order_id) answers: 'has")
print("  THIS REAL-WORLD ORDER already been refunded, ever, in any past")
print("  conversation?' -- a business-level fact, checked against history.")
print("\n  This lesson's idempotency key answers a narrower, different")
print("  question: 'is THIS SPECIFIC CALL ATTEMPT a retry of one already in")
print("  flight or already completed?' -- a request-level fact, checked")
print("  against a key the CALLER controls and must reuse correctly.")
print("\n  A real system typically needs BOTH: idempotency keys protect a")
print("  single logical request from being duplicated by network retries")
print("  within its own attempt; M8-L06's business-level check protects")
print("  against a genuinely NEW request (a new key, a new conversation)")
print("  asking for something that, at the business level, already")
print("  happened. Neither replaces the other.")


# ============================================================ 5
rule("5. WHAT THIS LAB IS AND IS NOT")

print("  REAL: every REFUND_LOG entry, every IDEMPOTENCY_STORE lookup, and")
print("  the three-way contrast (correct reuse, a new request, the fresh-key")
print("  pitfall) are genuinely computed by calling these functions -- not")
print("  scripted to produce a predetermined narrative.")
print("\n  ILLUSTRATIVE: this lab's IDEMPOTENCY_STORE is an in-memory dict --")
print("  a real system needs a persistent, durable store (surviving a crash")
print("  or restart between retries) for the guarantee to hold in practice,")
print("  which this lab does not model.")
print("\n  NOT SHOWN: how long an idempotency key should remain valid before")
print("  being safely forgotten; what happens if two genuinely concurrent")
print("  requests race on the same key (M8-L13's own concurrency territory);")
print("  and how a real client library generates and attaches idempotency")
print("  keys automatically rather than requiring each caller to manage them")
print("  by hand, as this lab's examples do explicitly for clarity.")

print("\nDone.")
