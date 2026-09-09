"""M5-L08 lab -- tool schemas, arguments, and blast radius.

Tool arguments are the only model output that DOES something. This lab treats
them the way M5-L06 treated any other output -- as untrusted input -- and then
shows the one defence that is different in kind: a parameter that is not in the
schema cannot be set by any prompt, however persuasive.

Sections 1-3 and 5 use NO model: real pydantic, a real side-effecting function,
and arithmetic. Section 4 uses a mock for tool selection.

Deterministic (zlib.crc32). No API key, no network.
Run:  python labs/m5/l08_tools.py
"""

from __future__ import annotations

import math
import zlib
from dataclasses import dataclass, field
from enum import Enum
from typing import Literal

import numpy as np
from pydantic import BaseModel, ConfigDict, Field, ValidationError


def rule(title: str) -> None:
    print(f"\n{'=' * 76}\n{title}\n{'=' * 76}")


def seeded(*p) -> np.random.Generator:
    return np.random.default_rng(zlib.crc32("|".join(map(str, p)).encode()))


# ============================================================ 1
rule("1. TOOL ARGUMENTS ARE UNTRUSTED INPUT")

class LooseRefund(BaseModel):
    """The schema you write first."""
    user_id: str
    amount: float
    reason: str
    currency: str = "GBP"


class TightRefund(BaseModel):
    """The same tool, designed."""
    model_config = ConfigDict(strict=True, extra="forbid")
    order_id: str = Field(pattern=r"^GB-\d{4}$")
    amount_pence: int = Field(ge=1, le=50_000)
    reason: Literal["duplicate_charge", "not_received", "damaged", "other"]
    currency: Literal["GBP"]


ARGS = [
    ("ordinary refund",
     {"user_id": "u-1001", "amount": 25.0, "reason": "damaged",
      "currency": "GBP"},
     {"order_id": "GB-4471", "amount_pence": 2500, "reason": "damaged",
      "currency": "GBP"}),
    ("someone else's account",
     {"user_id": "u-9999", "amount": 25.0, "reason": "damaged",
      "currency": "GBP"},
     None),
    ("a million",
     {"user_id": "u-1001", "amount": 1_000_000.0, "reason": "damaged",
      "currency": "GBP"},
     {"order_id": "GB-4471", "amount_pence": 100_000_000,
      "reason": "damaged", "currency": "GBP"}),
    ("negative (a charge)",
     {"user_id": "u-1001", "amount": -500.0, "reason": "damaged",
      "currency": "GBP"},
     {"order_id": "GB-4471", "amount_pence": -50_000, "reason": "damaged",
      "currency": "GBP"}),
    ("wildcard id",
     {"user_id": "*", "amount": 10.0, "reason": "damaged", "currency": "GBP"},
     {"order_id": "*", "amount_pence": 1000, "reason": "damaged",
      "currency": "GBP"}),
    ("sql-ish id",
     {"user_id": "u-1001' OR '1'='1", "amount": 10.0, "reason": "x",
      "currency": "GBP"},
     {"order_id": "GB-4471' OR '1'='1", "amount_pence": 1000,
      "reason": "other", "currency": "GBP"}),
    ("path traversal",
     {"user_id": "../../admin", "amount": 10.0, "reason": "x",
      "currency": "GBP"},
     {"order_id": "../../admin", "amount_pence": 1000, "reason": "other",
      "currency": "GBP"}),
    ("unhandled currency",
     {"user_id": "u-1001", "amount": 1000000.0, "reason": "x",
      "currency": "KRW"},
     {"order_id": "GB-4471", "amount_pence": 100_000_000,
      "reason": "other", "currency": "KRW"}),
    ("float money",
     {"user_id": "u-1001", "amount": 0.1 + 0.2, "reason": "x",
      "currency": "GBP"},
     None),
    ("invented field",
     {"user_id": "u-1001", "amount": 10.0, "reason": "x", "currency": "GBP",
      "approved_by": "system"},
     {"order_id": "GB-4471", "amount_pence": 1000, "reason": "other",
      "currency": "GBP", "approved_by": "system"}),
]

print("  Ten argument sets a model might emit -- some ordinary, some the")
print("  result of an injected instruction, some just wrong.\n")
print(f"  {'arguments':<24}{'loose schema':>16}{'tight schema':>16}")
loose_ok = tight_ok = 0
for label, loose_args, tight_args in ARGS:
    try:
        LooseRefund(**loose_args)
        a = "ACCEPTED"
        loose_ok += 1
    except ValidationError:
        a = "rejected"
    if tight_args is None:
        b = "n/a"
    else:
        try:
            TightRefund(**tight_args)
            b = "ACCEPTED"
            tight_ok += 1
        except ValidationError:
            b = "rejected"
    print(f"  {label:<24}{a:>16}{b:>16}")

bad_float = 0.1 + 0.2
print(f"\n  And the quiet one: 'float money' passed the loose schema carrying")
print(f"  {bad_float!r} -- which is not 30 pence, and never will be (M2-L02).")
print(f"  The tight schema has no float field at all; money is integer pence.")
print(f"\n  loose schema accepted {loose_ok}/{len(ARGS)}")
print(f"  tight schema accepted {tight_ok}/"
      f"{sum(1 for a in ARGS if a[2] is not None)} of those it was given")
print("\n  Every 'ACCEPTED' in the loose column is an action your system takes.")
print("  This is M5-L06's lesson with consequences: an unvalidated field in a")
print("  summary is a bad sentence; an unvalidated field in a TOOL CALL is a")
print("  refund, a delete, or an email to a customer.")


# ============================================================ 2
rule("2. THE DEFENCE THAT IS DIFFERENT IN KIND: DELETE THE PARAMETER")

print("  The tight schema still rejects 'someone else's account' only if you")
print("  remember to check it. Look at what happens when user_id is simply")
print("  NOT A PARAMETER.\n")


@dataclass
class Session:
    """Identity established by authentication, before any model was involved."""
    user_id: str


class RefundArgs(BaseModel):
    """No user_id. There is nowhere to put one."""
    model_config = ConfigDict(strict=True, extra="forbid")
    order_id: str = Field(pattern=r"^GB-\d{4}$")
    amount_pence: int = Field(ge=1, le=50_000)
    reason: Literal["duplicate_charge", "not_received", "damaged", "other"]


ORDERS = {"GB-4471": "u-1001", "GB-8802": "u-9999"}


def issue_refund(session: Session, args: RefundArgs) -> str:
    """Identity from the session; the model chooses the order, not the owner."""
    owner = ORDERS.get(args.order_id)
    if owner is None:
        return "REJECTED: unknown order"
    if owner != session.user_id:                     # M2-L15, again
        return "REJECTED: order does not belong to this session"
    return f"OK: refunded {args.amount_pence}p on {args.order_id}"


session = Session(user_id="u-1001")
ATTACKS = [
    ("normal request", {"order_id": "GB-4471", "amount_pence": 2500,
                        "reason": "damaged"}),
    ("another user's order", {"order_id": "GB-8802", "amount_pence": 2500,
                              "reason": "damaged"}),
    ("injected: set user_id", {"order_id": "GB-4471", "amount_pence": 2500,
                               "reason": "damaged", "user_id": "u-9999"}),
    ("injected: admin flag", {"order_id": "GB-4471", "amount_pence": 2500,
                              "reason": "damaged", "is_admin": True}),
    ("over the cap", {"order_id": "GB-4471", "amount_pence": 999_999,
                      "reason": "damaged"}),
]

print(f"  {'model emitted':<26}{'schema':>10}  {'result':<46}")
for label, raw in ATTACKS:
    try:
        args = RefundArgs(**raw)
    except ValidationError as e:
        print(f"  {label:<26}{'rejected':>10}  "
              f"{'schema: ' + e.errors()[0]['type']:<46}")
        continue
    print(f"  {label:<26}{'valid':>10}  {issue_refund(session, args):<46}")

print("\n  Rows 3 and 4 are the point. The model was TOLD to set user_id and")
print("  is_admin, by an injected instruction it found persuasive. It could")
print("  not: extra='forbid' rejects the field, and even if it did not, the")
print("  function never reads one -- identity comes from the session.")
print("\n  Row 2 is the other half. The model may name any order it likes; the")
print("  function checks ownership. The model chooses WHAT, your code decides")
print("  WHETHER.")
print("\n  This is the third appearance of one principle in this module:")
print("    M2-L16  parameterised SQL   -- values cannot become commands")
print("    M5-L05  nonce delimiters    -- content cannot forge a boundary")
print("    M5-L08  absent parameters   -- prompts cannot set what does not exist")
print("  Each removes a capability rather than policing its use.")


# ============================================================ 3
rule("3. TOOLS RUN TWICE: IDEMPOTENCY")

print("  A tool call times out. Your HTTP layer retries (M2-L12). The first")
print("  call had already succeeded. Real code, real counter.\n")

REFUNDS: list[tuple[str, int]] = []
SEEN_KEYS: set[str] = set()


def refund_naive(order_id: str, pence: int) -> None:
    REFUNDS.append((order_id, pence))


def refund_idempotent(order_id: str, pence: int, key: str) -> str:
    if key in SEEN_KEYS:
        return "duplicate ignored"
    SEEN_KEYS.add(key)
    REFUNDS.append((order_id, pence))
    return "applied"


TRIALS = 1000
rng = seeded("timeouts")
timeouts = rng.random(TRIALS) < 0.03          # 3% of calls time out after work

REFUNDS.clear()
for i in range(TRIALS):
    refund_naive("GB-4471", 2500)
    if timeouts[i]:
        refund_naive("GB-4471", 2500)          # the retry
naive_total = len(REFUNDS)

REFUNDS.clear()
SEEN_KEYS.clear()
for i in range(TRIALS):
    key = f"req-{i}"
    refund_idempotent("GB-4471", 2500, key)
    if timeouts[i]:
        refund_idempotent("GB-4471", 2500, key)
idem_total = len(REFUNDS)

print(f"  {TRIALS:,} logical refund requests, {int(timeouts.sum())} timeouts\n")
print(f"  {'approach':<32}{'refunds applied':>18}{'overpaid':>12}")
print(f"  {'no idempotency key':<32}{naive_total:>18,}"
      f"{f'{(naive_total - TRIALS) * 2500 / 100:,.0f} GBP':>12}")
print(f"  {'idempotency key per request':<32}{idem_total:>18,}"
      f"{f'{(idem_total - TRIALS) * 2500 / 100:,.0f} GBP':>12}")

print("\n  A 3% timeout rate paid out "
      f"{naive_total - TRIALS} extra refunds. Nothing was")
print("  wrong with the model, the schema, or the arguments.")
print("\n  Note where the key must come from: the LOGICAL REQUEST, not the")
print("  tool call. If the model generates the key, a retry that re-runs the")
print("  model generates a new one, and you are back to paying twice.")


# ============================================================ 4
rule("4. HOW MANY TOOLS BEFORE THE MODEL PICKS THE WRONG ONE?  [MOCK]")

print("  Rates specified. The shape -- and the effect of overlapping")
print("  descriptions -- is what to take away.\n")


def selects_correctly(n_tools: int, overlap: float, trial: int) -> bool:
    p = 0.985 ** (n_tools - 1) * (1 - 0.55 * overlap)
    rng = seeded("sel", n_tools, overlap, trial)
    return bool(rng.random() < p)


N = 6000
print(f"  {'tools':>7}{'distinct descriptions':>24}{'overlapping (40%)':>20}"
      f"{'cost of overlap':>18}")
sel = {}
for n in (1, 2, 3, 5, 10, 20, 40):
    a = sum(selects_correctly(n, 0.0, t) for t in range(N)) / N
    b = sum(selects_correctly(n, 0.4, t) for t in range(N)) / N
    sel[n] = (a, b)
    print(f"  {n:>7}{a:>24.1%}{b:>20.1%}{a - b:>17.1%}")

print(f"\n  TWO overlapping tools score {sel[2][1]:.1%}. TEN well-separated ones")
print(f"  score {sel[10][0]:.1%}. Two tools called 'search_orders' and")
print("  'find_orders' are worse than ten that cannot be confused -- the")
print("  clarity of the descriptions matters more here than the count.")
print("\n  The fix is not fewer tools. It is descriptions that cannot both be")
print("  right for the same request.")
print("\n  A tool description is a prompt. It is also the only thing standing")
print("  between a request and the wrong action, so write it as carefully as")
print("  the system prompt (M5-L01).")


# ============================================================ 5
rule("5. BLAST RADIUS: WHAT THE WORST CASE ACTUALLY IS")

print("  For each tool, the worst a single successful injected call could do.")
print("  This table is the deliverable of a tool design review.\n")


@dataclass
class Tool:
    name: str
    reversible: bool
    scope: str
    worst_case: str
    gate: str


TOOLS = [
    Tool("search_orders", True, "session user", "reads own orders", "none"),
    Tool("get_order", True, "session user", "reads one own order", "none"),
    Tool("draft_reply", True, "no side effect", "writes a draft", "none"),
    Tool("issue_refund", False, "one order, <= 500 GBP",
         "500 GBP to a real customer", "amount cap + ownership"),
    Tool("send_email", False, "one address", "one email to a customer",
         "template allow-list"),
    Tool("delete_account", False, "session user", "irreversible data loss",
         "HUMAN APPROVAL"),
    Tool("run_sql", False, "whole database", "anything at all", "NOT EXPOSED"),
]

print(f"  {'tool':<17}{'reversible':>11}   {'scope':<24}{'gate':<24}")
for t in TOOLS:
    print(f"  {t.name:<17}{('yes' if t.reversible else 'NO'):>11}   "
          f"{t.scope:<24}{t.gate:<24}")

irrev = [t for t in TOOLS if not t.reversible]
gated = [t for t in irrev if t.gate not in ("none",)]
print(f"\n  {len(irrev)} of {len(TOOLS)} tools are irreversible; "
      f"{len(gated)} of those carry a gate.")

print("\n  The design rules this table enforces:\n")
print("    * A read-only tool scoped to the session is nearly free. Add those.")
print("    * An irreversible tool needs a bound (a cap, an allow-list) or a")
print("      person. 'The model is usually careful' is not a bound.")
print("    * A tool whose worst case is 'anything at all' is not exposed to a")
print("      model. run_sql is the tool everyone wants and nobody should ship:")
print("      its blast radius is the union of every other tool's.")

print("\n  Now price the gates. Assume 1% of calls are injected:\n")
CALLS = 100_000
INJECT = 0.01
print(f"  {'tool':<17}{'injected calls/mo':>19}{'ungated loss':>16}"
      f"{'gated loss':>13}")
for name, per_event, gate_blocks in (
        ("issue_refund", 500.0, 0.999),
        ("send_email", 0.5, 0.98),
        ("delete_account", 5000.0, 1.0),
):
    n_inj = CALLS * INJECT / len(TOOLS)
    ungated = n_inj * per_event
    print(f"  {name:<17}{n_inj:>19,.0f}{f'{ungated:,.0f} GBP':>16}"
          f"{f'{ungated * (1 - gate_blocks):,.0f} GBP':>13}")

print("\n  The gate on delete_account is a person, and its residual is zero")
print("  because a person is not subject to the injected instruction. That is")
print("  the only row where the control is outside the system entirely, and")
print("  it is the only row where the worst case is not a number you accept.")


# ============================================================ 6
rule("6. WHAT THIS LAB IS AND IS NOT")

print("  REAL: sections 1, 2, 3 and 5 -- pydantic schemas, a working")
print("  authorisation check, a real double-execution counter, and arithmetic.")
print("  Section 2 in particular is not a simulation: the attack fails because")
print("  the field does not exist, and you can read the code that makes that")
print("  true.")
print("\n  MOCK: section 4's selection rates are specified. The shape -- more")
print("  tools and overlapping descriptions both cost accuracy -- is the part")
print("  that transfers.")
print("\n  NOT SHOWN: how often a real model emits malformed or malicious tool")
print("  arguments. That rate is model-, prompt- and traffic-specific, and")
print("  the design above is chosen so that the rate does not have to be low.")

print("\nDone.")
