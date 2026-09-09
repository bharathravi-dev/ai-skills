"""M5-L07 lab -- validation errors, feedback, and the economics of retrying.

Sections 1-2 and 5 use NO model: they run real pydantic and real arithmetic.
Section 1 is the one to read twice -- what a ValidationError actually contains
determines both what you can feed back to the model and what you leak to your
logs, and pydantic 2.13.5 has a switch for exactly that.

Sections 3-4 use a mock to compare retry strategies. The rates are specified;
the convergence, the cost tails and the systematic-failure result are not.

Deterministic (zlib.crc32). No API key, no network.
Run:  python labs/m5/l07_validation_repair.py
"""

from __future__ import annotations

import json
import math
import zlib
from enum import Enum

import numpy as np
from pydantic import BaseModel, ConfigDict, Field, ValidationError


def rule(title: str) -> None:
    print(f"\n{'=' * 76}\n{title}\n{'=' * 76}")


def seeded(*p) -> np.random.Generator:
    return np.random.default_rng(zlib.crc32("|".join(map(str, p)).encode()))


class Category(str, Enum):
    billing = "billing"
    technical = "technical"
    account = "account"
    other = "other"


class Decision(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")
    category: Category
    refund: float = Field(ge=0, le=500)
    contact: str = Field(min_length=5, max_length=120)
    urgent: bool


BAD_OUTPUTS = [
    ("wrong enum",
     '{"category":"refunds","refund":10.0,"contact":"jo@example.com",'
     '"urgent":false}'),
    ("out of bounds",
     '{"category":"billing","refund":999999.0,"contact":"jo@example.com",'
     '"urgent":false}'),
    ("string number",
     '{"category":"billing","refund":"10.0","contact":"jo@example.com",'
     '"urgent":false}'),
    ("missing field",
     '{"category":"billing","refund":10.0,"contact":"jo@example.com"}'),
    ("extra field",
     '{"category":"billing","refund":10.0,"contact":"jo@example.com",'
     '"urgent":false,"approved":true}'),
    ("several at once",
     '{"category":"nope","refund":-5.0,"contact":"x","urgent":"maybe",'
     '"who":"me"}'),
]


# ================================================================= 1
rule("1. WHAT A VALIDATION ERROR ACTUALLY CONTAINS")

print("  Real pydantic. For each bad output: how many errors, do they name the")
print("  field, and -- the part nobody checks -- do they contain the VALUE?\n")

print(f"  {'bad output':<20}{'errors':>8}{'fields named':>34}"
      f"{'value included':>17}")
leaky = 0
for label, raw in BAD_OUTPUTS:
    try:
        Decision.model_validate_json(raw)
        print(f"  {label:<20}{'0':>8}{'(valid)':>34}{'-':>17}")
        continue
    except ValidationError as e:
        errs = e.errors()
        fields = ",".join(".".join(str(x) for x in er["loc"]) for er in errs)
        has_input = any("input" in er for er in errs)
        leaky += has_input
        print(f"  {label:<20}{len(errs):>8}{fields[:32]:>34}"
              f"{('YES' if has_input else 'no'):>17}")

print(f"\n  {leaky}/{len(BAD_OUTPUTS)} error sets carry the offending INPUT VALUE.")
try:
    Decision.model_validate_json(BAD_OUTPUTS[3][1])
except ValidationError as e:
    miss = e.errors()[0]
    print(f"\n  And note the 'missing field' case. Its error type is "
          f"'{miss['type']}', so there is")
    print("  no single offending value -- pydantic reports the WHOLE OBJECT as")
    print("  the input:")
    print(f"    input = {miss['input']}")
    print("  The one error you would expect to be harmless carries every field")
    print("  the model produced, customer contact details included.")
print("  That is excellent for feeding back to the model and a liability the")
print("  moment you log it: the invalid value is frequently the customer's")
print("  email address, name, or free text.\n")

demo = BAD_OUTPUTS[-1][1]
try:
    Decision.model_validate_json(demo)
except ValidationError as e:
    with_input = e.errors()
    without = e.errors(include_input=False, include_url=False)

print("  The same error, two ways:\n")
print(f"    e.errors()                       -> "
      f"{len(json.dumps(with_input, default=str))} chars, contains input values")
print(f"    e.errors(include_input=False,")
print(f"             include_url=False)      -> "
      f"{len(json.dumps(without, default=str))} chars, no values")
print(f"\n    contact field, with input   : "
      f"{[er for er in with_input if er['loc'] == ('contact',)][0]}")
print(f"    contact field, without input: "
      f"{[er for er in without if er['loc'] == ('contact',)][0]}")

print("\n  Rule: errors(include_input=True) to the MODEL, errors(include_input=")
print("  False) to your LOGS. They are different audiences with different")
print("  retention. Most codebases send the same string to both.")


# ================================================================= 2
rule("2. BUILDING THE FEEDBACK MESSAGE")

print("  Three ways to tell the model what was wrong, and what each costs.\n")


def feedback_dump(e: ValidationError) -> str:
    return str(e)


def feedback_json(e: ValidationError) -> str:
    return json.dumps(e.errors(include_url=False), default=str)


def feedback_terse(e: ValidationError) -> str:
    lines = []
    for er in e.errors(include_url=False):
        loc = ".".join(str(x) for x in er["loc"])
        lines.append(f"{loc}: {er['msg']}")
    return "; ".join(lines)


# the distinctive values the last bad output contained -- if any of these
# appear in a feedback string, that string carries model/customer data
VALUES_IN_BAD = ("nope", "maybe", '"me"', "'me'")

try:
    Decision.model_validate_json(BAD_OUTPUTS[-1][1])
except ValidationError as e:
    print(f"  {'style':<26}{'chars':>8}{'~tokens':>10}{'doc URLs':>10}"
          f"{'leaks values':>14}")
    for name, fn in (("str(e)", feedback_dump),
                     ("errors() as JSON", feedback_json),
                     ("terse loc: msg", feedback_terse)):
        t = fn(e)
        urls = "yes" if "errors.pydantic.dev" in t else "no"
        # the actual invalid values this output contained, in any quoting
        leaks = "YES" if any(v in t for v in VALUES_IN_BAD) else "no"
        print(f"  {name:<26}{len(t):>8}{len(t) // 4:>10}{urls:>10}{leaks:>14}")

    print("\n  The terse form, in full:\n")
    for line in feedback_terse(e).split("; "):
        print(f"    {line}")

print("\n  All three name every broken field and state every rule. They differ")
print("  in what else they carry: documentation URLs the model cannot use and")
print("  you pay for on every repair attempt, and input values you may not")
print("  want in a prompt you are about to log.")
print("\n  The terse form wins three ways at once: a quarter of the tokens,")
print("  no documentation URLs, and no values from the model's output.")
print("\n  The obvious objection: without the input value, does the model know")
print("  what it did wrong? Usually yes -- its own output is already in the")
print("  conversation, so repeating the value back spends tokens telling it")
print("  something it can read two messages up. Include the value only when")
print("  you have stripped the prior turn to save context (M5-L11).")
print("\n  A good feedback message is the FIELD and the RULE it broke. Not")
print("  'that was invalid, try again', which tells the model exactly what")
print("  it already knew.")


# ================================================================= 3
rule("3. DO REPAIR LOOPS CONVERGE?  [MOCK]")

print("  Three strategies against two kinds of failure.\n")
print("    transient  -- the model can produce a valid answer; this one missed")
print("    systematic -- the schema and the prompt disagree; no sample is valid")
print("\n  Rates are specified. Convergence and cost are consequences.\n")

P_OK = 0.72          # per-attempt success on a transient failure, no feedback
FEEDBACK_LIFT = 0.55  # feedback closes this share of the remaining gap


def attempt(strategy: str, n_prior: int, systematic: bool, trial: int) -> bool:
    if systematic:
        return False                      # nothing the loop can do
    p = P_OK
    if strategy == "feedback" and n_prior > 0:
        p = P_OK + (1 - P_OK) * FEEDBACK_LIFT
    rng = seeded("att", strategy, n_prior, trial)
    return bool(rng.random() < p)


N, MAX_ATT = 20_000, 4
print(f"  {'strategy':<22}{'kind':<13}{'solved':>9}{'mean calls':>12}"
      f"{'p99 calls':>11}{'wasted calls':>14}")
for strategy in ("no retry", "naive retry", "retry + feedback"):
    for systematic in (False, True):
        limit = 1 if strategy == "no retry" else MAX_ATT
        solved, calls = 0, []
        for t in range(N):
            used = 0
            for a in range(limit):
                used += 1
                if attempt("feedback" if strategy == "retry + feedback"
                           else "naive", a, systematic, t):
                    solved += 1
                    break
            calls.append(used)
        c = np.array(calls)
        wasted = int(c.sum() - solved)
        print(f"  {strategy:<22}{('systematic' if systematic else 'transient'):<13}"
              f"{solved / N:>9.1%}{c.mean():>12.2f}"
              f"{np.percentile(c, 99):>11.0f}{wasted:>14,}")

print("\n  Read the systematic rows. Every retry strategy solves 0%, and the")
print("  4-attempt loop burns four calls per request to do it. The loop is")
print("  not failing to help -- it cannot help, because the same prompt and")
print("  the same schema produce the same rejection.")
print("\n  A repair loop is a bet that the failure was transient. If you do not")
print("  measure which kind you have, you are paying 4x on the ones where the")
print("  answer is to change the schema or the prompt.")


# ================================================================= 4
rule("4. THE ARITHMETIC OF A RETRY BUDGET")

print("  Exact, not simulated. p = per-attempt success probability.\n")
print(f"  {'p':>6}{'1 attempt':>12}{'2':>10}{'3':>10}{'4':>10}"
      f"{'mean calls (max 4)':>21}")
for p in (0.99, 0.95, 0.90, 0.80, 0.72, 0.50):
    cum = [1 - (1 - p) ** k for k in (1, 2, 3, 4)]
    mean = sum((1 - p) ** i for i in range(4))
    print(f"  {p:>6.2f}" + "".join(f"{c:>10.2%}" if i else f"{c:>12.2%}"
                                   for i, c in enumerate(cum))
          + f"{mean:>21.2f}")

print("\n  Two things this table decides for you:\n")
print("  1. WHERE TO STOP. At p=0.90, three attempts reach 99.9% and a fourth")
print("     buys 0.09 points. Attempts 4+ are almost entirely spent on")
print("     requests that were never going to succeed.")
print("  2. THE TAIL. Mean calls at p=0.90 is 1.11 -- the average bill barely")
print("     moves. But the 1-in-1000 request takes 4 calls and 4x the latency,")
print("     and that is what your p99 shows and your users feel.")

print("\n  A retry loop must be bounded by all three:\n")
print(f"    {'bound':<22}{'why':<48}")
print(f"    {'attempts':<22}{'stops the infinite loop':<48}")
print(f"    {'deadline':<22}{'stops a slow provider becoming a slow you':<48}")
print(f"    {'cost':<22}{'stops a retry storm becoming an invoice':<48}")
print("\n  Attempts alone is not enough: 4 attempts at 30 s each is a 2-minute")
print("  request, and the user left after 10 s (M2-L14).")


# ================================================================= 5
rule("5. WHAT AN UNBOUNDED LOOP COSTS")

print("  A real, common bug: retry until valid, no cap.\n")

IN_TOK, OUT_TOK = 900, 120
IN_P, OUT_P = 0.50 / 1e6, 2.00 / 1e6     # ILLUSTRATIVE, dated 2026-09-09
per_call = IN_TOK * IN_P + OUT_TOK * OUT_P
REQ = 100_000

print(f"  {REQ:,} requests/month, {IN_TOK} in + {OUT_TOK} out tokens/call,")
print(f"  ${per_call:.6f} per call  [ILLUSTRATIVE]\n")
print(f"  {'scenario':<38}{'calls/req':>11}{'$/month':>12}{'vs baseline':>14}")
base = REQ * per_call
for name, calls in (
        ("no validation (1 call)", 1.0),
        ("bounded retry, p=0.90, max 3", 1.11),
        ("bounded retry, p=0.72, max 4", 1.63),
        ("SYSTEMATIC failure, max 4", 4.0),
        ("unbounded loop, 2% systematic", 0.98 * 1.11 + 0.02 * 60),
):
    cost = REQ * calls * per_call
    print(f"  {name:<38}{calls:>11.2f}{f'${cost:,.0f}':>12}"
          f"{cost / base:>13.1f}x")

good_share, bad_share, bad_calls = 0.98, 0.02, 60
cost_good = REQ * good_share * 1.11 * per_call
cost_bad = REQ * bad_share * bad_calls * per_call
print(f"\n  The last row is the one that reaches production. Split it:\n")
print(f"    {'traffic':<28}{'share':>8}{'calls/req':>11}{'$/month':>11}")
print(f"    {'behaves (bounded retry)':<28}{good_share:>8.0%}"
      f"{1.11:>11.2f}{f'${cost_good:,.0f}':>11}")
print(f"    {'systematic, spins to 60':<28}{bad_share:>8.0%}"
      f"{bad_calls:>11.0f}{f'${cost_bad:,.0f}':>11}")
print(f"\n  {bad_share:.0%} of requests account for "
      f"{cost_bad / (cost_good + cost_bad):.0%} of the bill "
      f"({cost_bad / cost_good:.1f}x what the")
print("  other 98% costs). It reaches 60 calls only because a timeout")
print("  elsewhere in the stack eventually kills it -- nothing in the loop")
print("  itself was ever going to stop.")
print("\n  And it will not look like a cost incident. It looks like a latency")
print("  incident, because the same 2% are also holding connections open.")


# ================================================================= 6
rule("6. WHAT THIS LAB IS AND IS NOT")

print("  REAL: section 1 (pydantic 2.13.5 error structure, including the")
print("  include_input switch), section 2 (message sizes), section 4 (exact")
print("  probability arithmetic) and section 5 (cost arithmetic).")
print("\n  MOCK: section 3's per-attempt success rates are specified. What is")
print("  NOT specified, and is the point: that no strategy moves a systematic")
print("  failure off 0%, and what the loop costs while failing to.")
print("\n  NOT SHOWN: whether feeding a real model its validation errors helps")
print("  as much as the mock assumes. Measure that on your model, on your")
print("  schema -- exercise 2.4.")

print("\nDone.")
