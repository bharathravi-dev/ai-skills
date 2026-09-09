"""M5-L06 lab -- structured output: parsing, repair, and silent coercion.

Sections 1-4 use NO model. They run the real json module and the real pydantic
against a catalogue of malformed outputs collected from the failure modes in
M2-L08 and M4-L15. The results are properties of those libraries on this
machine, not simulations -- which is what makes the coercion findings usable.

Section 5 adds a mock for the one thing real libraries cannot show: how schema
complexity affects a model's compliance.

Deterministic. No API key, no network.
Run:  python labs/m5/l06_structured_output.py
"""

from __future__ import annotations

import json
import math
import re
import zlib
from enum import Enum
from typing import Any

import numpy as np
from pydantic import BaseModel, ConfigDict, Field, ValidationError


def rule(title: str) -> None:
    print(f"\n{'=' * 76}\n{title}\n{'=' * 76}")


def seeded(*p) -> np.random.Generator:
    return np.random.default_rng(zlib.crc32("|".join(map(str, p)).encode()))


# ------------------------------------------------- the catalogue of failures
# Each entry: (label, raw text a model actually tends to emit)
RAW = [
    ("clean",            '{"category":"billing","refund":42.5,"urgent":false}'),
    ("fenced",           '```json\n{"category":"billing","refund":42.5,'
                         '"urgent":false}\n```'),
    ("preamble",         'Sure! Here is the JSON you asked for:\n'
                         '{"category":"billing","refund":42.5,"urgent":false}'),
    ("preamble+fence",   'Here you go:\n```json\n{"category":"billing",'
                         '"refund":42.5,"urgent":false}\n```\nLet me know!'),
    ("trailing comma",   '{"category":"billing","refund":42.5,"urgent":false,}'),
    ("single quotes",    "{'category':'billing','refund':42.5,'urgent':False}"),
    ("truncated",        '{"category":"billing","refund":42.5,"urg'),
    ("truncated deep",   '{"category":"billing","refund":42.5,"filters":'
                         '{"account":"A-1","region":'),
    ("nan",              '{"category":"billing","refund":NaN,"urgent":false}'),
    ("string numbers",   '{"category":"billing","refund":"42.5","urgent":"false"}'),
    ("extra field",      '{"category":"billing","refund":42.5,"urgent":false,'
                         '"approved_by":"system"}'),
    ("wrong enum",       '{"category":"Billing Dept","refund":42.5,'
                         '"urgent":false}'),
    ("null for number",  '{"category":"billing","refund":null,"urgent":false}'),
    ("two objects",      '{"category":"billing","refund":42.5,"urgent":false}\n'
                         '{"category":"other","refund":0,"urgent":true}'),
]

TRUTH = {"category": "billing", "refund": 42.5, "urgent": False}


# ================================================================= 1
rule("1. WHAT PLAIN json.loads DOES WITH REAL MODEL OUTPUT")

print("  No model, no mock: the stdlib json module against 14 outputs of the")
print("  kind models actually emit.\n")
print(f"  {'raw output':<20}{'json.loads':>14}{'error':>44}")
plain_ok = 0
for label, raw in RAW:
    try:
        json.loads(raw)
        plain_ok += 1
        print(f"  {label:<20}{'parses':>14}{'':>44}")
    except Exception as e:
        msg = str(e).split(":")[0][:42]
        print(f"  {label:<20}{'FAILS':>14}{msg:>44}")

print(f"\n  {plain_ok}/{len(RAW)} parse. The failures are not exotic -- a code")
print("  fence and a polite preamble are the two most common things a chat")
print("  model does, and neither is an error from its point of view.")
print("\n  Note 'nan' PARSED. Python's json accepts NaN and Infinity by default,")
print("  which is not valid JSON. It will parse here and explode in whatever")
print("  consumes it. Pass parse_constant to reject it.")


# ================================================================= 2
rule("2. REPAIR STRATEGIES -- AND THE ONES THAT SUCCEED DANGEROUSLY")

def strip_fence(t: str) -> str:
    m = re.search(r"```(?:json)?\s*(.*?)\s*```", t, re.S)
    return m.group(1) if m else t


def first_object(t: str) -> str:
    i = t.find("{")
    j = t.rfind("}")
    return t[i:j + 1] if i != -1 and j > i else t


def balance_braces(t: str) -> str:
    """The 'helpful' repair: close whatever is open. See M4-L15."""
    t = t.rstrip().rstrip(",")
    opens = t.count("{") - t.count("}")
    if opens > 0:
        t = re.sub(r',\s*"[^"]*$', "", t)      # drop a half-written key
        t = re.sub(r',\s*"[^"]*"\s*:\s*$', "", t)
        t += "}" * opens
    return t


PIPELINE = [
    ("json.loads only", lambda t: t),
    ("+ strip fences", strip_fence),
    ("+ first {...}", lambda t: first_object(strip_fence(t))),
    ("+ balance braces", lambda t: balance_braces(first_object(strip_fence(t)))),
]

print("  Each stage adds one repair. 'correct' means the parsed object equals")
print("  what the model meant. 'WRONG' means it parsed into something else.\n")
print(f"  {'strategy':<22}{'parsed':>9}{'correct':>10}{'WRONG':>8}"
      f"{'what silently changed':>36}")

for name, fn in PIPELINE:
    parsed = correct = wrong = 0
    damage = []
    for label, raw in RAW:
        try:
            obj = json.loads(fn(raw))
        except Exception:
            continue
        parsed += 1
        if isinstance(obj, dict) and obj.get("category") == "billing" and \
                obj.get("refund") == 42.5 and obj.get("urgent") is False:
            correct += 1
        else:
            wrong += 1
            damage.append(label)
    note = ",".join(damage[:2]) if damage else "--"
    print(f"  {name:<22}{parsed:>9}{correct:>10}{wrong:>8}{note:>36}")

print("\n  Now look at what brace-balancing actually produced:\n")
for label in ("truncated", "truncated deep"):
    raw = dict(RAW)[label]
    fixed = balance_braces(first_object(strip_fence(raw)))
    try:
        obj = json.loads(fixed)
        print(f"    {label}:")
        print(f"      raw    : {raw}")
        print(f"      repaired: {fixed}")
        print(f"      parsed  : {obj}")
        missing = [k for k in TRUTH if k not in obj]
        print(f"      MISSING KEYS: {missing or 'none'}")
    except Exception as e:
        print(f"    {label}: still unparseable ({type(e).__name__})")

print("\n  This is the failure that matters. The truncated output did not")
print("  fail -- it succeeded, as a DIFFERENT object. A repair that produces")
print("  valid JSON from an incomplete response has invented a complete")
print("  answer out of a partial one, and nothing downstream can tell.")
print("\n  If the missing key had been a filter on a delete, the repair would")
print("  have widened the operation to everything (M4-L15).")
print("\n  Rule: NEVER repair a truncated response. Check finish_reason first;")
print("  if it is not a natural stop, the response is not data, it is debris.")


# ================================================================= 3
rule("3. VALIDATION: WHAT PYDANTIC ACCEPTS WHEN YOU DO NOT ASK IT NOT TO")

class Category(str, Enum):
    billing = "billing"
    technical = "technical"
    account = "account"
    other = "other"


class Lax(BaseModel):
    category: Category
    refund: float
    urgent: bool


class Strict(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")
    category: Category
    refund: float = Field(ge=0, le=1000)
    urgent: bool


print("  Same JSON, two models. 'lax' is what you get by default.\n")
print(f"  {'raw output':<20}{'lax':>28}{'strict':>28}")


def show(model, raw):
    try:
        obj = model.model_validate_json(raw)
        d = obj.model_dump()
        return f"{d['category'].value if hasattr(d['category'], 'value') else d['category']}/" \
               f"{d['refund']}/{d['urgent']}"
    except ValidationError as e:
        return f"rejected ({e.error_count()})"
    except Exception as e:
        return f"unparseable"


coerced = []
for label, raw in RAW:
    body = first_object(strip_fence(raw))
    a, b = show(Lax, body), show(Strict, body)
    if a != b and not a.startswith("rejected") and not a.startswith("unpars"):
        coerced.append(label)
    print(f"  {label:<20}{a:>28}{b:>28}")

print(f"\n  Rows where lax ACCEPTED and strict rejected: "
      f"{', '.join(coerced) if coerced else 'none'}")
print("\n  Read the 'string numbers' row. Lax turned \"42.5\" into 42.5 and")
print("  \"false\" into False, and reported success. That is usually what you")
print("  wanted -- and it means your validator cannot tell you that the model")
print("  stopped emitting numbers as numbers, which is exactly the signal")
print("  you need after a model upgrade (M5-L17).")
print("\n  Read the 'extra field' row. Without extra='forbid', approved_by")
print("  passes straight through your validator and into your code, where")
print("  something may well read it (M2-L15, mass assignment).")


# ================================================================= 4
rule("4. WHAT A SCHEMA CATCHES THAT AN INSTRUCTION CANNOT")

print("  Four outputs that are valid JSON and wrong. Which layer stops them?\n")

BAD = [
    ("refund of 1e6",   '{"category":"billing","refund":1000000,"urgent":false}'),
    ("negative refund", '{"category":"billing","refund":-50,"urgent":false}'),
    ("invented label",  '{"category":"escalation","refund":10,"urgent":false}'),
    ("extra authority", '{"category":"billing","refund":10,"urgent":false,'
                        '"approved":true}'),
]
print(f"  {'output':<20}{'valid JSON':>12}{'lax model':>26}{'strict model':>16}")
for label, raw in BAD:
    try:
        json.loads(raw)
        vj = "yes"
    except Exception:
        vj = "no"
    print(f"  {label:<20}{vj:>12}{show(Lax, raw):>26}{show(Strict, raw):>16}")

print("\n  Every one of these is well-formed JSON. Parsing cannot help. The")
print("  bounds (ge/le), the enum and extra='forbid' are what reject them,")
print("  and each one is a line of schema rather than a sentence of prompt.")
print("\n  An instruction asks. A schema refuses. Only one of them is a control.")


# ================================================================= 5
rule("5. SCHEMA COMPLEXITY vs COMPLIANCE  [MOCK]")

print("  The one thing real libraries cannot show: whether the MODEL manages")
print("  to produce the shape. Rates below are specified, not measured.\n")

def compliance(fields: int, depth: int, enums: int, trial: int) -> bool:
    p = 0.985 ** fields * 0.90 ** (depth - 1) * (1.0 + 0.004 * enums)
    rng = seeded("comp", fields, depth, enums, trial)
    return bool(rng.random() < min(p, 0.999))


N = 5000
print(f"  {'schema':<34}{'fields':>8}{'depth':>7}{'compliance':>13}"
      f"{'per 100k requests':>20}")
rows5 = []
for name, f_, d_, e_ in (
        ("3 flat fields, 1 enum", 3, 1, 1),
        ("8 flat fields, 2 enums", 8, 1, 2),
        ("8 fields, 1 nested object", 8, 2, 2),
        ("15 fields, 3 levels deep", 15, 3, 3),
        ("25 fields, 4 levels deep", 25, 4, 4),
):
    ok = sum(compliance(f_, d_, e_, t) for t in range(N)) / N
    rows5.append((name, ok))
    print(f"  {name:<34}{f_:>8}{d_:>7}{ok:>13.1%}{int((1 - ok) * 100_000):>20,}")

best, worst = rows5[0], rows5[-1]
print(f"\n  The right-hand column is the one to design against. The simplest")
print(f"  schema here is {best[1]:.1%} -- which is "
      f"{int((1 - best[1]) * 100_000):,} failed requests per 100,000, a retry")
print("  budget and a support queue, not a rounding error.")
print(f"\n  The largest schema is {worst[1]:.1%}. Between the two rows nothing")
print("  changed about the task or the model: only the shape you asked for.")
print("\n  Flatten before you deepen: two calls with flat schemas beat one call")
print("  with a nested one, and each can be validated and retried alone.")


# ================================================================= 6
rule("6. WHAT THIS LAB IS AND IS NOT")

print("  REAL (sections 1-4): the stdlib json module and pydantic 2.13.5 on")
print("  this machine. Those rows are reproducible facts about the libraries")
print("  you will actually ship, including the coercion behaviour -- which is")
print("  the finding most likely to surprise you in production.")
print("\n  MOCK (section 5): compliance rates are specified. Only the shape")
print("  transfers -- more fields and more depth cost compliance.")
print("\n  NOT SHOWN: constrained decoding. Where a provider can guarantee the")
print("  grammar, section 5's problem largely disappears and sections 1-4 do")
print("  NOT -- a guaranteed-valid JSON object can still carry a refund of")
print("  1,000,000. Validation is not parsing, and neither is a substitute")
print("  for the other.")

print("\nDone.")
