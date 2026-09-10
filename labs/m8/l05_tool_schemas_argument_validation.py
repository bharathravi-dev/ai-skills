"""M8-L05 lab -- M8-L03's loop already catches an unrecognized tool name and
a tool call that raises. This lesson adds a THIRD category, positioned
earlier than either: a recognized tool called with ARGUMENTS that are the
wrong type, out of bounds, or contain a field the tool was never designed to
accept at all. M5-L06's schema principle ("an instruction asks, a schema
refuses") and M5-L08's "absent parameters" defense are both applied here to
tool-call arguments specifically, gating them BEFORE the tool function ever
runs -- not inside it, and not after the fact (M8-L02's own pattern, one
step earlier).

Deterministic. No API key, no network, no third-party dependencies -- a
small hand-written validator stands in for a real schema library (M5-L06
used pydantic; this lab reimplements just enough of the same idea to stay
dependency-free, see section 6).
Run:  python labs/m8/l05_tool_schemas_argument_validation.py
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from typing import Any, Callable

sys.stdout.reconfigure(encoding="utf-8")


def rule(title: str) -> None:
    print(f"\n{'=' * 76}\n{title}\n{'=' * 76}")


@dataclass
class Tool:
    name: str
    func: Callable[..., Any]
    description: str


class ArgValidationError(Exception):
    pass


@dataclass
class ArgSpec:
    """[REAL, minimal] Enough of M5-L06's Pydantic-style schema to
    demonstrate the same three catches: wrong type, out of bounds, and a
    field the schema never declared."""
    type_: type
    ge: float | None = None
    le: float | None = None
    min_length: int | None = None
    max_length: int | None = None
    prefix: str | None = None


def validate_args(schema: dict[str, ArgSpec], args: dict) -> dict:
    """[REAL] M5-L06's exact principle, applied to tool-call arguments:
    reject unknown fields (the absent-parameter defense, M5-L08), reject
    wrong types, reject out-of-bounds values -- all BEFORE the tool
    function runs, not inside it."""
    extra = set(args) - set(schema)
    if extra:
        raise ArgValidationError(f"unexpected argument(s) not in schema: {sorted(extra)}")
    validated = {}
    for name, spec in schema.items():
        if name not in args:
            raise ArgValidationError(f"missing required argument: {name!r}")
        value = args[name]
        if not isinstance(value, spec.type_):
            raise ArgValidationError(
                f"{name!r} must be {spec.type_.__name__}, got {type(value).__name__} ({value!r})")
        if spec.ge is not None and value < spec.ge:
            raise ArgValidationError(f"{name!r}={value} is below minimum {spec.ge}")
        if spec.le is not None and value > spec.le:
            raise ArgValidationError(f"{name!r}={value} exceeds maximum {spec.le}")
        if spec.min_length is not None and len(value) < spec.min_length:
            raise ArgValidationError(f"{name!r} is shorter than minimum length {spec.min_length}")
        if spec.max_length is not None and len(value) > spec.max_length:
            raise ArgValidationError(f"{name!r} exceeds maximum length {spec.max_length}")
        if spec.prefix is not None and not value.startswith(spec.prefix):
            raise ArgValidationError(f"{name!r}={value!r} must start with {spec.prefix!r}")
        validated[name] = value
    return validated


def run_tool_loop(
    tools: list[Tool],
    decide_next: Callable[[dict], tuple[str, dict]],
    schemas: dict[str, dict[str, ArgSpec]] | None = None,
    max_steps: int = 8,
) -> list[str]:
    """[REAL, M8-L03's loop, EXTENDED with one new step] Unlike M8-L04,
    which reused M8-L03's loop byte-for-byte, this lesson genuinely needs a
    new capability -- so the loop itself changes: before calling a tool, if
    a schema is registered for it, arguments are validated first. An
    ArgValidationError is caught the same way an unknown tool name or a
    raised exception already were -- fed back as an observation, loop
    continues -- adding a THIRD general failure category, not a special
    case."""
    tool_by_name = {t.name: t for t in tools}
    schemas = schemas or {}
    trace: list[str] = []
    observed: dict[str, Any] = {}
    for step in range(1, max_steps + 1):
        action_name, action_args = decide_next(observed)
        if action_name == "respond":
            trace.append(f"[step {step}] [STOP] respond -- loop stops")
            return trace
        if action_name not in tool_by_name:
            observed["last_error"] = f"unknown tool {action_name!r}"
            trace.append(f"[step {step}] unknown tool {action_name!r}")
            continue
        if action_name in schemas:
            try:
                action_args = validate_args(schemas[action_name], action_args)
            except ArgValidationError as exc:
                observed["last_error"] = str(exc)
                trace.append(f"[step {step}] [VALIDATE] {action_name}({action_args}) "
                             f"REJECTED: {exc}")
                continue
        try:
            result = tool_by_name[action_name].func(**action_args)
            observed[action_name] = result
            trace.append(f"[step {step}] [ACT] {action_name}({action_args}) "
                         f"-> [OBSERVE] {result!r}")
        except Exception as exc:
            observed["last_error"] = str(exc)
            trace.append(f"[step {step}] {action_name}({action_args}) RAISED {exc!r}")
    trace.append(f"[step {max_steps}] [STOP] max_steps reached")
    return trace


ORDERS = {"O-1001": {"item": "Wireless Mouse", "amount": 40.0}}


def issue_refund(order_id: str, amount: float, reason: str) -> str:
    return f"refund of ${amount:.2f} issued for {order_id} ({reason})"


REFUND_TOOLS = [Tool("issue_refund", issue_refund, "Issue a refund for an order")]

# [REAL] Note what is absent, on purpose: no "approved_by", no "user_id" --
# M5-L08's own defense, applied here. A field that does not exist in the
# schema cannot be set by anything the model proposes, no matter how it is
# argued for.
REFUND_SCHEMA = {
    "issue_refund": {
        "order_id": ArgSpec(str, min_length=1, prefix="O-"),
        "amount": ArgSpec(float, ge=0.01, le=500.0),
        "reason": ArgSpec(str, min_length=1, max_length=200),
    }
}


# ============================================================ 1
rule("1. THREE THINGS NO AMOUNT OF PROMPTING CAN GUARANTEE")

print("  M5-L06's own finding, restated for tool arguments specifically: an")
print("  instruction can ASK a model to pass a valid order id, a reasonable")
print("  amount, and nothing extra -- a schema REFUSES anything that")
print("  doesn't comply, regardless of how the model was asked. Section 2")
print("  runs this loop's schema against three malformed proposals directly.")


# ============================================================ 2
rule("2. THREE MALFORMED PROPOSALS, VALIDATED DIRECTLY")

BAD_PROPOSALS = [
    ("wrong type", {"order_id": "O-1001", "amount": "forty dollars", "reason": "damaged"}),
    ("out of bounds", {"order_id": "O-1001", "amount": 50_000.0, "reason": "damaged"}),
    ("undeclared field", {"order_id": "O-1001", "amount": 40.0, "reason": "damaged", "approved_by": "admin"}),
]
for label, args in BAD_PROPOSALS:
    try:
        validate_args(REFUND_SCHEMA["issue_refund"], args)
        print(f"  {label:<18} {args} -> ACCEPTED (unexpected)")
    except ArgValidationError as exc:
        print(f"  {label:<18} {args}\n    -> REJECTED: {exc}")

print("\n  Each rejection happened before issue_refund() was ever called --")
print("  the wrong-type amount never reached a float comparison inside the")
print("  function (which would have crashed or misbehaved); the out-of-")
print("  bounds amount never reached the business logic at all; and")
print("  'approved_by' was rejected NOT because its value looked suspicious,")
print("  but because the schema never declared such a field could exist --")
print("  M5-L08's exact absent-parameter defense, applied here to args.")


# ============================================================ 3
rule("3. THE SAME THREE CATCHES, NOW INSIDE THE LOOP")


def make_scripted_decider() -> Callable[[dict], tuple[str, dict]]:
    """[ILLUSTRATIVE, scripted] Proposes the same three malformed calls as
    section 2, then a fourth, genuinely valid one -- standing in for a
    model that needs several attempts (or several turns) to produce
    compliant arguments, each attempt's rejection visible to it as its next
    observation."""
    calls = {"n": 0}

    def decide_next(observed: dict) -> tuple[str, dict]:
        calls["n"] += 1
        n = calls["n"]
        if n == 1:
            return "issue_refund", {"order_id": "O-1001", "amount": "forty dollars", "reason": "damaged"}
        if n == 2:
            return "issue_refund", {"order_id": "O-1001", "amount": 50_000.0, "reason": "damaged"}
        if n == 3:
            return "issue_refund", {"order_id": "O-1001", "amount": 40.0, "reason": "damaged", "approved_by": "admin"}
        if n == 4:
            return "issue_refund", {"order_id": "O-1001", "amount": 40.0, "reason": "damaged"}
        return "respond", {}

    return decide_next


print("  Running the loop with REFUND_SCHEMA wired in:\n")
trace = run_tool_loop(REFUND_TOOLS, make_scripted_decider(), schemas=REFUND_SCHEMA)
for line in trace:
    print(f"  {line}")

print("\n  Three rejections, one success, zero crashes -- every rejection")
print("  used the SAME general [VALIDATE] branch in run_tool_loop(), not")
print("  three separate special cases. This is the loop's THIRD failure")
print("  category, alongside M8-L03's unknown-tool and raised-exception")
print("  handling: recognized tool, invalid arguments.")


# ============================================================ 4
rule("4. WHERE THE GATE SITS MATTERS: BEFORE THE CALL, NOT INSIDE IT")

print("  M8-L02's gated_refund() validated a COMPUTED amount from inside the")
print("  tool's own logic, after deciding what to charge. This lesson's")
print("  schema validates the PROPOSED arguments before the tool function")
print("  is invoked AT ALL -- a step earlier. For issue_refund() specifically,")
print("  that means a wrong-type amount never reaches a single line of the")
print("  function's own code, including any bounds-checking that function")
print("  might otherwise need to duplicate. The schema is where the")
print("  well-formedness check belongs; the tool's own logic is free to")
print("  assume its arguments are already valid by the time it runs.")


# ============================================================ 5
rule("5. WHAT THIS LAB IS AND IS NOT")

print("  REAL: validate_args() is a genuine, executed type/bounds/field")
print("  checker -- every rejection in sections 2 and 3 is a real raised")
print("  ArgValidationError, caught by real except blocks, not a scripted")
print("  narrative. The final successful refund in section 3 is a real")
print("  call to issue_refund() with validated arguments.")
print("\n  ILLUSTRATIVE: make_scripted_decider() stands in for a real model")
print("  across several attempts or turns -- a real system would show each")
print("  rejection's error message to the model as its next observation and")
print("  let it try again, not follow a fixed script. validate_args() is a")
print("  small, hand-written reimplementation of M5-L06's Pydantic-based")
print("  approach, built here to stay dependency-free -- a real system")
print("  should prefer a maintained schema library over a hand-rolled one.")
print("\n  NOT SHOWN: nested or cross-field validation (e.g., a rule spanning")
print("  two arguments together); coercion policy (M5-L06's lax-vs-strict")
print("  distinction, fully applicable here too); and retry/backoff")
print("  strategies for how many correction attempts a model gets before")
print("  the loop gives up (M8-L13's own topic).")

print("\nDone.")
